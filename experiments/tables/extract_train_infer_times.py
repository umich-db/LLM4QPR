#!/usr/bin/env python3
"""
Extract full training time + per-query inference time, per (system, method),
averaged across workloads, for the 6 methods in generate_overleaf_table_time.py:
qf, aimai, bao, e2e_cost (baselines) + bert2, bert4, sentBert (mode-12 LLMs).

Sources:
  - LLM (mode 12, biCrossAttn+inflatePRICE cx4): the H100 ablation_e1_profile logs
    (1 epoch @ tr0.1) unpacked from logsH100_time_6.4.zip -> ZIP_ROOT below.
      full training = [Train] Epoch 0 total (ms) x10 (tr0.1 -> full data) x16 epochs
      inference/query = final [Test] Total evaluation time (ms) / n_test
                        (test_loader is batch=1, so n_test = max [Test] batch index)
  - Baselines: profile_baselines_train_infer[_<db>].csv (train_ms full, infer_ms
    total over the batch=1 test set). bao infer now logged (trainer.py patch).
      Per-db CSV used if present; else postgres CSV reused (flagged pg_fallback).

Averaging:
  - training: over 4 TRAINING workloads {stats, tpch, tpcds, imdb}; imdb represents
    job/job_full/syn (shared training set). Baseline imdb training = the syn row
    (job/job_full reuse the cache -> train_ms NA).
  - inference: over the 6 TEST workloads {stats, tpch, tpcds, job, job_full, syn}.
"""
import os, re, glob, csv

ZIP_ROOT = "/root/tmp/logsH100_extract/logs"
RES      = "/root/LLM4QPR/experiments/results"
ANALYSIS = "/root/LLM4QPR/experiments/analysis_scripts"
H100_PG  = "/root/h100_profile_runs_2026-05-18/csvs/profile_baselines_train_infer.csv"

SYSTEMS = ["postgres", "duckdb", "spark"]
MODELS  = {"bert2": "google-bert_uncased_L-2_H-256_A-4",
           "bert4": "google-bert_uncased_L-4_H-768_A-12",
           "sentBert": "sentence-transformers-all-MiniLM-L12-v2"}
BASELINES = ["qf", "aimai", "bao", "e2e_cost"]
ORDER = ["qf", "aimai", "bao", "e2e_cost", "bert2", "bert4", "sentBert"]

TESTDIR = {"stats": "logs_Train_stats_Test_stats_ours", "tpch": "logs_Train_tpch_Test_tpch_ours",
           "tpcds": "logs_Train_tpcds_Test_tpcds_ours", "job": "logs_Train_job_Test_job_ours",
           "job_full": "logs_Train_job_Test_job_full_ours", "syn": "logs_Train_job_Test_syn_ours"}
TRAINWL = {"stats": "logs_Train_stats_Test_stats_ours", "tpch": "logs_Train_tpch_Test_tpch_ours",
           "tpcds": "logs_Train_tpcds_Test_tpcds_ours", "imdb": "logs_Train_job_Test_job_ours"}
TEST_WLS  = ["stats", "tpch", "tpcds", "job", "job_full", "syn"]
TRAIN_WLS = ["stats", "tpch", "tpcds", "imdb"]
NUM_EPOCHS = 16
DATA_SCALE = 10.0   # tr0.1 -> full data


def find_log(db, subdir, token, mode="mode12"):
    pat = (f"{ZIP_ROOT}/{db}/{subdir}/ablation_e1_profile/"
           f"time_ablation_{mode}_{db}_*_{token}_quant-4-bit_e1_tr0.1_seed42.log")
    fs = [f for f in glob.glob(pat) if not f.endswith(("_inference.log", ".stdout"))]
    return fs[0] if fs else None


def _last(pat, f):
    m = re.findall(pat, open(f).read())
    return float(m[-1]) if m else None


def epoch0_ms(f):     return _last(r"\[Train\] Epoch 0 total — ([\d.]+) ms", f)
def test_total_ms(f): return _last(r"\[Test\] Total evaluation time — ([\d.]+) ms", f)
def test_ntest(f):
    idx = [int(x) for x in re.findall(r"\[Test\] Batch (\d+) —", open(f).read())]
    return max(idx) if idx else None


def base_ntest(w):  # full test set size from the pretrained-None CDF (db-independent)
    for d in (f"{RES}/postgres/results_Train_{w}_Test_{w}_ours",
              f"{RES}/postgres/results_Train_job_Test_{w}_ours"):
        for f in glob.glob(f"{d}/time_llm_pretrained-None_*L-2_H-256*seed42.csv"):
            return sum(1 for _ in open(f)) - 1
    return None


def baseline_csv(db):
    """Return (path, is_pg_fallback) for a system's baseline profile CSV."""
    if db == "postgres":
        for p in (f"{ANALYSIS}/profile_baselines_train_infer.csv", H100_PG):
            if os.path.exists(p):
                return p, False
        return None, False
    p = f"{ANALYSIS}/profile_baselines_train_infer_{db}.csv"
    if os.path.exists(p):
        return p, False
    for p in (f"{ANALYSIS}/profile_baselines_train_infer.csv", H100_PG):  # reuse postgres, flagged
        if os.path.exists(p):
            return p, True
    return None, True


def compute():
    NT_BASE = {w: base_ntest(w) for w in TEST_WLS}

    llm = {}
    for db in SYSTEMS:
        for mk, tok in MODELS.items():
            tr = []
            for w in TRAIN_WLS:
                f = find_log(db, TRAINWL[w], tok)
                e = epoch0_ms(f) if f else None
                if e:
                    tr.append(e * DATA_SCALE * NUM_EPOCHS / 1000.0)  # seconds
            inf = []
            for w in TEST_WLS:
                f = find_log(db, TESTDIR[w], tok)
                t = test_total_ms(f) if f else None
                n = test_ntest(f) if f else None
                if t and n:
                    inf.append(t / n)
            llm[(db, mk)] = (sum(tr) / len(tr) if tr else None,
                             sum(inf) / len(inf) if inf else None)

    base, pg_only = {}, {}
    for db in SYSTEMS:
        path, fallback = baseline_csv(db)
        rows = list(csv.DictReader(open(path))) if path else []

        def bval(a, w, c):
            for r in rows:
                if r["algo"] == a and r["workload"] == w:
                    return None if r[c] in ("NA", "") else float(r[c])
            return None

        for algo in BASELINES:
            tr = [bval(algo, "syn" if w == "imdb" else w, "train_ms") for w in TRAIN_WLS]
            tr = [v / 1000.0 for v in tr if v is not None]
            inf = []
            for w in TEST_WLS:
                v = bval(algo, w, "infer_ms")
                n = NT_BASE[w]
                if v is not None and n:
                    inf.append(v / n)
            base[(db, algo)] = (sum(tr) / len(tr) if tr else None,
                                sum(inf) / len(inf) if inf else None)
            pg_only[(db, algo)] = fallback
    return llm, base, pg_only, NT_BASE


def main():
    llm, base, pg_only, _ = compute()

    def get(db, m):
        return base[(db, m)] if m in BASELINES else llm[(db, m)]

    here = os.path.dirname(os.path.abspath(__file__))
    out_csv, out_md = os.path.join(here, "train_infer_times.csv"), os.path.join(here, "train_infer_times.md")

    with open(out_csv, "w", newline="") as fo:
        w = csv.writer(fo)
        w.writerow(["system", "method", "full_train_s", "infer_ms_per_query", "baseline_pg_fallback"])
        for db in SYSTEMS:
            for m in ORDER:
                t, i = get(db, m)
                flag = 1 if (m in BASELINES and pg_only[(db, m)]) else 0
                w.writerow([db, m, "" if t is None else f"{t:.2f}",
                            "" if i is None else f"{i:.3f}", flag])

    def ft(v): return "NA" if v is None else f"{v:,.1f}"
    def fi(v): return "NA" if v is None else f"{v:.2f}"
    lines = ["# Training & inference time (H100) — averaged across workloads\n",
             "- **full train (s)** = LLM: per-epoch (e1,tr0.1) x10 (->full data) x16 epochs; "
             "baselines: measured full training (tr1.0). Averaged over 4 training workloads "
             "{stats, tpch, tpcds, imdb}; imdb represents job/job_full/syn.",
             "- **infer (ms/query)** = total test-set inference / #test queries (batch=1 for all), "
             "averaged over 6 test workloads {stats, tpch, tpcds, job, job_full, syn}.",
             "- LLMs = mode-12 (biCrossAttn + inflatePRICE, cx4). Dagger = baseline reused from "
             "postgres (per-db profiling not collected yet -> run profile_baselines_duckdb_spark.sh).\n"]
    for db in SYSTEMS:
        lines += [f"\n## {db}\n", "| method | full train (s) | infer (ms/query) |", "|---|--:|--:|"]
        for m in ORDER:
            t, i = get(db, m)
            dag = " (dagger)" if (m in BASELINES and pg_only[(db, m)]) else ""
            lines.append(f"| {m}{dag} | {ft(t)} | {fi(i)} |")
    open(out_md, "w").write("\n".join(lines) + "\n")
    print(f"wrote {out_csv}\nwrote {out_md}\n")
    print(open(out_md).read())


if __name__ == "__main__":
    main()
