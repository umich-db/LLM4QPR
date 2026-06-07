#!/usr/bin/env python3
"""
Full training time + per-query inference time, per (system, method), averaged
across workloads, for the 6 methods in generate_overleaf_table_time.py:
qf, aimai, bao, e2e_cost (baselines) + bert2, bert4, sentBert (mode-12 LLMs).

LLMs (mode 12, biCrossAttn+inflatePRICE cx4) -- from the H100 ablation_e1_profile
logs (1 epoch @ tr0.1) under ZIP_ROOT:
  full training   = [Train] Epoch 0 total (ms) x10 (tr0.1->full) x16 epochs
  infer / query   = final [Test] Total evaluation time (ms) / n_test  (batch=1)

Baselines -- from the REAL multi-epoch training logs under LOGS/<db>/...
(the runs that produced the accuracy CDFs; the old profile_baselines CSV was a
single-epoch probe and is NOT used for training):
  per-epoch       = (last) [Train] Training took (ms) / epochs-of-that-run
  full training   = per-epoch x min(epochs, 30)         # cap epochs at 30
                    (equivalently Training_took x min(1, 30/epochs))
  infer / query   = (last) [Test] Total evaluation time (ms) / n_test  (batch=1)
  bao logs no epoch count -> training shown as-measured (uncapped), flagged.

Averaging: training over {stats,tpch,tpcds,imdb} (imdb=Train_job, represents
job/job_full/syn); inference over the 6 test workloads.
"""
import os, re, glob, csv

ZIP_ROOT = "/root/tmp/logsH100_extract/logs"
RES      = "/root/LLM4QPR/experiments/results"
LOGS     = "/root/LLM4QPR/experiments/logs"

SYSTEMS = ["postgres", "duckdb", "spark"]
MODELS  = {"bert2": "google-bert_uncased_L-2_H-256_A-4",
           "bert4": "google-bert_uncased_L-4_H-768_A-12",
           "sentBert": "sentence-transformers-all-MiniLM-L12-v2"}
BASELINES = ["qf", "aimai", "bao", "e2e_cost"]
ORDER = ["qf", "aimai", "bao", "e2e_cost", "bert2", "bert4", "sentBert"]
EPOCH_CAP = 30

# Train-workload -> log dir (imdb = Train_job_Test_job). Test-workload -> log dir.
TRAIN_DIR = {"stats": "logs_Train_stats_Test_stats_ours", "tpch": "logs_Train_tpch_Test_tpch_ours",
             "tpcds": "logs_Train_tpcds_Test_tpcds_ours", "imdb": "logs_Train_job_Test_job_ours"}
TEST_DIR  = {"stats": "logs_Train_stats_Test_stats_ours", "tpch": "logs_Train_tpch_Test_tpch_ours",
             "tpcds": "logs_Train_tpcds_Test_tpcds_ours", "job": "logs_Train_job_Test_job_ours",
             "job_full": "logs_Train_job_Test_job_full_ours", "syn": "logs_Train_job_Test_syn_ours"}
# LLM ablation dirs (same layout under ZIP_ROOT)
TRAIN_WLS = ["stats", "tpch", "tpcds", "imdb"]
TEST_WLS  = ["stats", "tpch", "tpcds", "job", "job_full", "syn"]
NUM_EPOCHS_LLM = 16
DATA_SCALE = 10.0


# ---------------- LLM (ablation logs) ----------------
def llm_log(db, subdir, token):
    pat = (f"{ZIP_ROOT}/{db}/{subdir}/ablation_e1_profile/"
           f"time_ablation_mode12_{db}_*_{token}_quant-4-bit_e1_tr0.1_seed42.log")
    fs = [f for f in glob.glob(pat) if not f.endswith(("_inference.log", ".stdout"))]
    return fs[0] if fs else None

def _last_float(pat, f):
    m = re.findall(pat, open(f).read());  return float(m[-1]) if m else None

def llm_epoch0(f):     return _last_float(r"\[Train\] Epoch 0 total — ([\d.]+) ms", f)
def test_total(f):
    # per-test-set inference time: prefer "Total evaluation time", else "Testing took"
    # (identical timer; older bao logs only have the latter). Both are batch=1.
    return (_last_float(r"\[Test\] Total evaluation time — ([\d.]+) ms", f)
            or _last_float(r"\[Test\] Testing took ([\d.]+) ms", f))
def llm_ntest(f):
    idx = [int(x) for x in re.findall(r"\[Test\] Batch (\d+) —", open(f).read())]
    return max(idx) if idx else None


# ---------------- baseline real logs ----------------
def base_log(db, subdir, algo):
    fs = glob.glob(f"{LOGS}/{db}/{subdir}/time_{algo}_1.0_cdf_{db}_*seed42.log")
    fs = [f for f in fs if not f.endswith((".stdout", ".console.log"))]
    return fs[0] if fs else None

def train_took_and_epochs(f):
    """(last Training-took ms, epochs of that run). Pairs each 'Training took'
    with the max 'Epoch N' seen since the previous one. epochs=None if unlogged (bao)."""
    last_took, last_ep = None, None
    cur_ep = None
    for line in open(f):
        m = re.search(r"\[Train\].*?Epoch (\d+)", line) or re.search(r"^.*?Epoch (\d+) training loss", line)
        if m:
            e = int(m.group(1)); cur_ep = e if cur_ep is None else max(cur_ep, e)
        t = re.search(r"\[Train\] Training took ([\d.]+) ms", line)
        if t:
            last_took = float(t.group(1))
            last_ep = (cur_ep + 1) if cur_ep is not None else None   # epochs are 0-indexed
            cur_ep = None
    return last_took, last_ep

def base_ntest(w):  # full test-set size from the pretrained-None CDF (db-independent)
    for d in (f"{RES}/postgres/results_Train_{w}_Test_{w}_ours",
              f"{RES}/postgres/results_Train_job_Test_{w}_ours"):
        for f in glob.glob(f"{d}/time_llm_pretrained-None_*L-2_H-256*seed42.csv"):
            return sum(1 for _ in open(f)) - 1
    return None


def compute():
    NT = {w: base_ntest(w) for w in TEST_WLS}

    llm = {}
    for db in SYSTEMS:
        for mk, tok in MODELS.items():
            tr = [llm_epoch0(llm_log(db, TRAIN_DIR[w], tok)) for w in TRAIN_WLS
                  if llm_log(db, TRAIN_DIR[w], tok)]
            tr = [e * DATA_SCALE * NUM_EPOCHS_LLM / 1000.0 for e in tr if e]
            inf = []
            for w in TEST_WLS:
                f = llm_log(db, TEST_DIR[w], tok)
                t = test_total(f) if f else None; n = llm_ntest(f) if f else None
                if t and n: inf.append(t / n)
            llm[(db, mk)] = (sum(tr)/len(tr) if tr else None, sum(inf)/len(inf) if inf else None)

    base, base_flag = {}, {}
    for db in SYSTEMS:
        for algo in BASELINES:
            tr, uncapped = [], False
            for w in TRAIN_WLS:
                f = base_log(db, TRAIN_DIR[w], algo)
                if not f: continue
                took, ep = train_took_and_epochs(f)
                if took is None: continue
                if ep is None:                       # bao: epochs not logged -> as-measured
                    tr.append(took / 1000.0); uncapped = True
                else:
                    tr.append(took * min(1.0, EPOCH_CAP / ep) / 1000.0)
            inf = []
            for w in TEST_WLS:
                f = base_log(db, TEST_DIR[w], algo)
                t = test_total(f) if f else None; n = NT[w]
                if t and n: inf.append(t / n)
            base[(db, algo)] = (sum(tr)/len(tr) if tr else None, sum(inf)/len(inf) if inf else None)
            base_flag[(db, algo)] = uncapped
    return llm, base, base_flag


def main():
    llm, base, base_flag = compute()
    def get(db, m): return base[(db, m)] if m in BASELINES else llm[(db, m)]
    here = os.path.dirname(os.path.abspath(__file__))
    out_csv, out_md = os.path.join(here, "train_infer_times.csv"), os.path.join(here, "train_infer_times.md")

    with open(out_csv, "w", newline="") as fo:
        w = csv.writer(fo)
        w.writerow(["system", "method", "full_train_s", "infer_ms_per_query", "bao_uncapped"])
        for db in SYSTEMS:
            for m in ORDER:
                t, i = get(db, m)
                w.writerow([db, m, "" if t is None else f"{t:.2f}",
                            "" if i is None else f"{i:.3f}",
                            1 if (m in BASELINES and base_flag[(db, m)]) else 0])

    def ft(v): return "NA" if v is None else f"{v:,.1f}"
    def fi(v): return "NA" if v is None else f"{v:.2f}"
    lines = ["# Training & inference time (H100) — averaged across workloads\n",
             "- **full train (s)** = LLM: per-epoch (e1,tr0.1) x10 (->full data) x16 epochs; "
             "baselines: real per-epoch x min(real-epochs, 30) from the actual multi-epoch logs. "
             "Averaged over 4 training workloads {stats,tpch,tpcds,imdb}; imdb=Train_job represents "
             "job/job_full/syn.",
             "- **infer (ms/query)** = total test-set inference / #test queries (batch=1 for all), "
             "averaged over 6 test workloads {stats,tpch,tpcds,job,job_full,syn}.",
             "- LLMs = mode-12 (biCrossAttn + inflatePRICE, cx4). 'bao*' = bao epoch count is not "
             "logged, so its training is shown as-measured (NOT epoch-capped at 30).\n"]
    for db in SYSTEMS:
        lines += [f"\n## {db}\n", "| method | full train (s) | infer (ms/query) |", "|---|--:|--:|"]
        for m in ORDER:
            t, i = get(db, m)
            star = "*" if (m in BASELINES and base_flag[(db, m)]) else ""
            lines.append(f"| {m}{star} | {ft(t)} | {fi(i)} |")
    open(out_md, "w").write("\n".join(lines) + "\n")
    print(f"wrote {out_csv}\nwrote {out_md}\n")
    print(open(out_md).read())


if __name__ == "__main__":
    main()
