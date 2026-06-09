import os, re, glob, csv, shutil
ZIP="/root/tmp/logsResults_extract/logs/postgres/logs_Train_tpcds_Test_tpcds_ours/model_selection"
CSV="logs/postgres/logs_Train_tpcds_Test_tpcds_ours/all_models/all_models_full_e16.csv"

def parse(log):
    """Return dict of pool cells from an H100 e16 finetune log (per-epoch val/test
    [QError] blocks + [Train] Epoch N total + [Test] Total evaluation time)."""
    cur_ep=-1; sect=None
    train_ms={}; val={}; test={}; test_total={}; ntest=0
    pend=None  # (epoch, section) awaiting QError numbers
    for line in open(log):
        m=re.search(r"\[Train\] Epoch (\d+) total — ([\d.]+) ms", line)
        if m: cur_ep=int(m.group(1)); train_ms[cur_ep]=float(m.group(2)); continue
        m=re.search(r"\[QError\] Data section: (\w+)", line)
        if m: pend=(cur_ep, m.group(1)); continue
        m=re.search(r"\[Test\] Total evaluation time — ([\d.]+) ms", line)
        if m:
            test_total[cur_ep]=float(m.group(1)); continue
        m=re.search(r"\[Test\] Batch (\d+) —", line)
        if m: ntest=max(ntest,int(m.group(1))); continue
        if pend is not None:
            ep,s=pend; tgt = val if s=="val" else (test if s=="test" else None)
            if tgt is None: pend=None; continue
            for key,pat in (("median",r"Median: ([\d.]+)"),("p90",r"90th percentile: ([\d.]+)"),
                            ("p95",r"95th percentile: ([\d.]+)"),("max",r"Max: ([\d.]+)"),
                            ("mean",r"Mean: ([\d.]+)")):
                mm=re.search(r"\[QError\] "+pat, line)
                if mm and ep not in tgt.setdefault('_seen',set()) or (mm and ep in tgt and key not in tgt.get(ep,{})):
                    pass
            # simpler: capture the 5-line QError block on first occurrence per (ep,s)
        # fallthrough handled below
    return None  # replaced below

# Simpler robust parse: collect blocks
def parse2(log):
    txt=open(log).read().splitlines()
    cur=-1; out={'train':{}, 'val':{}, 'test':{}, 'ttot':{}, 'ntest':0}
    i=0
    while i < len(txt):
        L=txt[i]
        m=re.search(r"\[Train\] Epoch (\d+) total — ([\d.]+) ms", L)
        if m: cur=int(m.group(1)); out['train'][cur]=float(m.group(2)); i+=1; continue
        m=re.search(r"\[Test\] Total evaluation time — ([\d.]+) ms", L)
        if m: out['ttot'][cur]=float(m.group(1)); i+=1; continue
        m=re.search(r"\[Test\] Batch (\d+) —", L)
        if m: out['ntest']=max(out['ntest'],int(m.group(1))); i+=1; continue
        m=re.search(r"\[QError\] Data section: (val|test)", L)
        if m:
            s=m.group(1); blk={}
            for j in range(i+1, min(i+7,len(txt))):
                for key,pat in (("median","Median: ([\\d.]+)"),("p90","90th percentile: ([\\d.]+)"),
                                ("p95","95th percentile: ([\\d.]+)"),("max","Max: ([\\d.]+)"),("mean","Mean: ([\\d.]+)")):
                    mm=re.search(r"\[QError\] "+pat, txt[j])
                    if mm: blk[key]=float(mm.group(1))
            if cur not in out[s]:   # first occurrence per (epoch, section)
                out[s][cur]=blk
            i+=1; continue
        i+=1
    return out

def cells(log):
    d=parse2(log)
    def chunk(a,b): return sum(d['train'].get(e,0) for e in range(a,b))
    t14,t58,t912,t1316 = chunk(0,4),chunk(4,8),chunk(8,12),chunk(12,16)
    v=d['val']; te=d['test']; nt=d['ntest'] or 90
    def vg(ep,k): return v.get(ep,{}).get(k)
    e16=max(d['test']) if d['test'] else 15
    e16v=max(d['val']) if d['val'] else 15
    tq = (d['ttot'].get(e16) or list(d['ttot'].values() or [0])[-1])/nt if d['ttot'] else None
    T=te.get(e16,{})
    return dict(
        time_e1_4=t14,time_e5_8=t58,time_e9_12=t912,time_e13_16=t1316,
        val_median_e4=vg(3,'median'),val_median_e8=vg(7,'median'),val_median_e12=vg(11,'median'),val_median_e16=vg(e16v,'median'),
        val_p90_e4=vg(3,'p90'),val_p90_e8=vg(7,'p90'),val_p90_e12=vg(11,'p90'),val_p90_e16=vg(e16v,'p90'),
        test_median_e16=T.get('median'),test_p90_e16=T.get('p90'),test_p95_e16=T.get('p95'),
        test_max_e16=T.get('max'),test_mean_e16=T.get('mean'),test_per_query_ms=tq)

# model token from a log path
def tok(p): return re.search(r"h2048_(.+?)_quant-4-bit", p).group(1)
logs={}
for p in glob.glob(f"{ZIP}/*finetune*_quant-4-bit_priceS_inflatePRICE_randInit_cx4_frzLLM4_pwm4_e16_seed42.log"):
    if "inference" in p: continue
    t=tok(p); mx=max(parse2(p)["train"] or [-1])
    if t not in logs or mx > logs[t][0]: logs[t]=(mx,p)
logs={t:p for t,(mx,p) in logs.items()}
print("model logs found:", len(logs))

rows=list(csv.reader(open(CSV))); hdr=rows[0]; idx={h:i for i,h in enumerate(hdr)}
def keytok(key):
    m=re.search(r"h2048_(.+?)_quant-4-bit", key); return m.group(1) if m else None
filled=0
for r in rows[1:]:
    kt=keytok(r[idx['key']])
    if kt in logs and 'cx4' in r[idx['key']]:
        _maxep=max(parse2(logs[kt])['test'] or [-1])
        if _maxep < 15:
            print(f"  SKIP {kt}: incomplete run (only reached epoch {_maxep} of 15) -> left blank")
            continue
        c=cells(logs[kt])
        def setc(col,val):
            if val is not None: r[idx[col]]=f"{val:.4f}" if isinstance(val,float) else str(val)
        for ch in ('time_e1_4','time_e5_8','time_e9_12','time_e13_16'):
            setc(ch+'_ms', c[ch]); setc(ch+'_h100_ms', c[ch])
        for col in ('val_median_e4','val_median_e8','val_median_e12','val_median_e16',
                    'val_p90_e4','val_p90_e8','val_p90_e12','val_p90_e16',
                    'test_median_e16','test_p90_e16','test_p95_e16','test_max_e16','test_mean_e16'):
            setc(col, c[col])
        setc('test_per_query_ms', c['test_per_query_ms']); setc('test_testing_took_ms', c['test_per_query_ms'])
        r[idx['pieces_gpu_e1_e5_e9_e13']]="e0:H100|e4:H100|e8:H100|e12:H100"
        filled+=1
        _f=lambda x:'NA' if x is None else f'{x:.2f}'
        print(f"  filled {kt}: test p50/p90/p95 = {_f(c['test_median_e16'])}/{_f(c['test_p90_e16'])}/{_f(c['test_p95_e16'])} | per_q {_f(c['test_per_query_ms'])}ms | train_e1_4 {(c['time_e1_4'] or 0)/1000:.0f}s (e16=epoch{max(parse2(logs[kt])['test'] or [0])})")
print("rows filled:", filled)
shutil.copy(CSV, CSV+".bak")
with open(CSV,"w",newline="") as f: csv.writer(f).writerows(rows)
print("wrote", CSV, "(backup .bak)")
