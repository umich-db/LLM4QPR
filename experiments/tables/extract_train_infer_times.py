import os, re, glob, csv
ROOT="/root/tmp/logsH100_extract/logs"; RES="/root/LLM4QPR/experiments/results"
BASE_CSV="/root/h100_profile_runs_2026-05-18/csvs/profile_baselines_train_infer.csv"
SYSTEMS=["postgres","duckdb","spark"]
MODELS={"bert2":"google-bert_uncased_L-2_H-256_A-4","bert4":"google-bert_uncased_L-4_H-768_A-12",
        "sentBert":"sentence-transformers-all-MiniLM-L12-v2"}
TESTDIR={"stats":"logs_Train_stats_Test_stats_ours","tpch":"logs_Train_tpch_Test_tpch_ours",
         "tpcds":"logs_Train_tpcds_Test_tpcds_ours","job":"logs_Train_job_Test_job_ours",
         "job_full":"logs_Train_job_Test_job_full_ours","syn":"logs_Train_job_Test_syn_ours"}
TRAINWL={"stats":"logs_Train_stats_Test_stats_ours","tpch":"logs_Train_tpch_Test_tpch_ours",
         "tpcds":"logs_Train_tpcds_Test_tpcds_ours","imdb":"logs_Train_job_Test_job_ours"}
TEST_WLS=["stats","tpch","tpcds","job","job_full","syn"]; TRAIN_WLS=["stats","tpch","tpcds","imdb"]
NUM_EPOCHS=16; DATA_SCALE=10.0

def find_log(db,subdir,token,mode="mode12"):
    pat=f"{ROOT}/{db}/{subdir}/ablation_e1_profile/time_ablation_{mode}_{db}_*_{token}_quant-4-bit_e1_tr0.1_seed42.log"
    fs=[f for f in glob.glob(pat) if not f.endswith(("_inference.log",".stdout"))]; return fs[0] if fs else None
def epoch0_ms(f):
    m=re.findall(r"\[Train\] Epoch 0 total — ([\d.]+) ms",open(f).read()); return float(m[-1]) if m else None
def test_total_ms(f):
    m=re.findall(r"\[Test\] Total evaluation time — ([\d.]+) ms",open(f).read()); return float(m[-1]) if m else None
def test_ntest(f):  # batch=1 eval -> n_test = max [Test] batch index
    idx=[int(x) for x in re.findall(r"\[Test\] Batch (\d+) —",open(f).read())]; return max(idx) if idx else None
def base_ntest(w):  # full test set from pretrained-None CDF
    for d in [f"{RES}/postgres/results_Train_{w}_Test_{w}_ours",f"{RES}/postgres/results_Train_job_Test_{w}_ours"]:
        for f in glob.glob(f"{d}/time_llm_pretrained-None_*L-2_H-256*seed42.csv"):
            return sum(1 for _ in open(f))-1
    return None
NT_BASE={w:base_ntest(w) for w in TEST_WLS}

# LLMs
llm={}
for db in SYSTEMS:
    for mk,tok in MODELS.items():
        tr=[]
        for w in TRAIN_WLS:
            f=find_log(db,TRAINWL[w],tok); e=epoch0_ms(f) if f else None
            if e: tr.append(e*DATA_SCALE*NUM_EPOCHS/1000.0)
        inf=[]
        for w in TEST_WLS:
            f=find_log(db,TESTDIR[w],tok); t=test_total_ms(f) if f else None; n=test_ntest(f) if f else None
            if t and n: inf.append(t/n)
        llm[(db,mk)]=(sum(tr)/len(tr) if tr else None, sum(inf)/len(inf) if inf else None)
# baselines (postgres)
rows=list(csv.DictReader(open(BASE_CSV)))
def bval(a,w,c):
    for r in rows:
        if r["algo"]==a and r["workload"]==w: return None if r[c]=="NA" else float(r[c])
    return None
base={}
for algo in ["aimai","bao","e2e_cost"]:
    tr=[bval(algo,"syn" if w=="imdb" else w,"train_ms") for w in TRAIN_WLS]; tr=[v/1000 for v in tr if v is not None]
    inf=[]
    for w in TEST_WLS:
        v=bval(algo,w,"infer_ms"); n=NT_BASE[w]
        if v is not None and n: inf.append(v/n)
    base[algo]=(sum(tr)/len(tr) if tr else None, sum(inf)/len(inf) if inf else None)

print("LLM n_test (max [Test] idx, postgres bert2):",{w:test_ntest(find_log("postgres",TESTDIR[w],MODELS["bert2"])) for w in TEST_WLS})
print("Baseline n_test (full CDF):",NT_BASE)
def f2(v,w=8): return (" "*(w-2)+"NA") if v is None else f"{v:{w}.2f}"
for db in SYSTEMS:
    print(f"\n===== SYSTEM: {db} =====   (train avg: stats/tpch/tpcds/imdb ; infer avg: 6 test wls)")
    print(f"  {'method':<10}{'full_train(s)':>15}{'infer(ms/q)':>14}")
    for a in ["aimai","bao","e2e_cost"]:
        t,i=base[a]; print(f"  {a:<10}{f2(t,15)}{f2(i,14)}{'' if db=='postgres' else '  *pg-only'}")
    for mk in MODELS:
        t,i=llm[(db,mk)]; print(f"  {mk:<10}{f2(t,15)}{f2(i,14)}")
# stash for table gen
import json; json.dump({"llm":{f"{k[0]}|{k[1]}":v for k,v in llm.items()},"base":base,
   "NT_BASE":NT_BASE}, open("/tmp/time_results.json","w"),indent=1)
