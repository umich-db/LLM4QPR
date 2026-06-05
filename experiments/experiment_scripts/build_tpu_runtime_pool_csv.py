#!/usr/bin/env python3
"""Generate a TPU-runtime version of all_models_full_e16.csv for plot_true_frontier.py.

The canonical all_models_full_e16.csv records H100 timing for the expanded_pool_tpu
rows. This script instead takes the TPU-v4 runtime recorded in the per-model
  all_models/expanded_pool_tpu__<KEY>__e16/{summary.txt,inference.log}
folders, keeping the ACCURACY columns (val_*, test_*_e16) from the CSV:

  TRAINING:  total_train_ms_raw (e16 TPU-v4 raw wall = stage1_finetune_sec*1000, from
             summary.txt) split equally over the 4 chunk columns (the TPU trainer logs
             only the aggregate). raw == h100 here (pure-TPU csv);
             pieces = e0:tpuv4|e4:tpuv4|e8:tpuv4|e12:tpuv4.

  INFERENCE: FULL-forward PER-QUERY latency (ms) reconstructed from the TPU timing
             breakdown in inference.log, because the bare `infer_sec` measures only the
             stage-2 head on PRE-CACHED embeddings (it excludes the LLM forward — it is
             smaller than the time to even embed the test set). The LLM-forward cost is
             recovered from `embedding_gen_sec` (the LLM forward over all data):

               test_per_query_ms = embedding_gen_sec / (train_size+val_size+test_size)   # LLM fwd / query
                                 + infer_sec        /  test_size                         # head / query
               (× 1000 for ms)

             -> comparable IN KIND to the H100 deployed per-query latency (still on a
             different test split / JAX stack / batched-throughput, so indicative only).

Only models with both an expanded_pool_tpu CSV row AND the needed log fields are emitted.
Output: all_models_full_e16_tpu.csv (same schema), runnable via
  plot_true_frontier.py --all_models_csv <out>
"""
import csv, glob, os, re, argparse

ALLMODELS_DIR = "/root/LLM4QPR/experiments/logs/postgres/logs_Train_stats_Test_stats_ours/all_models"
TIME_RAW = ["time_e1_4_ms", "time_e5_8_ms", "time_e9_12_ms", "time_e13_16_ms"]
TIME_H100 = ["time_e1_4_h100_ms", "time_e5_8_h100_ms", "time_e9_12_h100_ms", "time_e13_16_h100_ms"]
PIECES = "e0:tpuv4|e4:tpuv4|e8:tpuv4|e12:tpuv4"


def _g(text, pat, cast=float):
    m = re.search(pat, text, re.MULTILINE)
    return cast(m.group(1)) if m else None


def parse_folder(d):
    summ = open(os.path.join(d, "summary.txt")).read()
    inf_path = os.path.join(d, "inference.log")
    inf = open(inf_path).read() if os.path.exists(inf_path) else ""
    return {
        "key": _g(summ, r"^key:\s*(\S+)", str),
        "train_raw": _g(summ, r"total_train_ms_raw:\s*([0-9.]+)"),   # = stage1_finetune_sec*1000
        "embedding_gen_sec": _g(inf, r"^embedding_gen_sec=([0-9.]+)"),  # LLM forward over all data
        "infer_sec": _g(inf, r"^infer_sec=([0-9.]+)"),                  # stage-2 head on cached embs
        "train_size": _g(inf, r"^train_size=(\d+)", int),
        "val_size": _g(inf, r"^val_size=(\d+)", int),
        "test_size": _g(inf, r"^test_size=(\d+)", int),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=ALLMODELS_DIR)
    ap.add_argument("--csv", default=None, help="input H100 CSV (default <dir>/all_models_full_e16.csv)")
    ap.add_argument("--out", default=None, help="output TPU CSV (default <dir>/all_models_full_e16_tpu.csv)")
    a = ap.parse_args()
    csv_in = a.csv or os.path.join(a.dir, "all_models_full_e16.csv")
    out = a.out or os.path.join(a.dir, "all_models_full_e16_tpu.csv")

    folders = {}
    for d in glob.glob(os.path.join(a.dir, "expanded_pool_tpu__*__e16")):
        if os.path.exists(os.path.join(d, "summary.txt")):
            info = parse_folder(d)
            if info["key"]:
                folders[info["key"]] = info

    with open(csv_in) as f:
        rdr = csv.DictReader(f); header = rdr.fieldnames; rows = list(rdr)

    needed = ("train_raw", "embedding_gen_sec", "infer_sec", "train_size", "val_size", "test_size")
    out_rows, missing = [], []
    for r in rows:
        if r["subdir"] != "expanded_pool_tpu":
            continue
        info = folders.get(r["key"])
        if not info or any(info[k] is None for k in needed) or info["test_size"] <= 0:
            missing.append((r["key"], info)); continue
        nr = dict(r)  # preserve accuracy (val_*, test_*_e16), key, subdir
        chunk = info["train_raw"] / 4.0
        for c in TIME_RAW + TIME_H100:
            nr[c] = f"{chunk:.2f}"
        N = info["train_size"] + info["val_size"] + info["test_size"]
        # full-forward per-query latency (ms) = LLM forward/query + head/query
        per_query_ms = (info["embedding_gen_sec"] / N + info["infer_sec"] / info["test_size"]) * 1000.0
        nr["test_per_query_ms"] = f"{per_query_ms:.4f}"
        nr["test_testing_took_ms"] = f"{per_query_ms:.4f}"
        nr["pieces_gpu_e1_e5_e9_e13"] = PIECES
        out_rows.append(nr)

    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header); w.writeheader(); w.writerows(out_rows)
    print(f"wrote {out}")
    print(f"  TPU models: {len(out_rows)}   (skipped: {len(missing)})")
    for k, info in missing:
        print(f"    MISSING: {k}  (info={info})")


if __name__ == "__main__":
    main()
