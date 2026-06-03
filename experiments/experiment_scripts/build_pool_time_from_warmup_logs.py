#!/usr/bin/env python3
"""Build a per-workload all_models_full_e16.csv with ONLY the time columns filled
(accuracy columns left blank), from warmup_e2 profiling logs.

Time derivation mirrors /root/h100_profile_runs_2026-05-18 + add_jax_snapshot_to_pool.py:
  warmup_ms        = "[Train] Epoch 0 total — X ms"   (frozen warmup epoch, 0.1 data)
  after_warmup_ms  = "[Train] Epoch 1 total — X ms"   (post-warmup epoch,  0.1 data)
  CHUNK_FACTOR = 40 = x10 (0.1 -> full data) * x4 (epochs/chunk)
  time_e1_4_{ms,h100_ms}                 = warmup_ms       * 40
  time_{e5_8,e9_12,e13_16}_{ms,h100_ms}  = after_warmup_ms * 40
  (H100-native profiling -> raw == h100, pieces = e0:H100|e4:H100|e8:H100|e12:H100)
Inference (per user choice): MEAN PER-BATCH ms = mean of the first [Test] pass's
  "[Test] Batch N — X ms" lines, EXCLUDING batch 1 (cold start). Stored in BOTH
  test_total_eval_ms and test_testing_took_ms. (NB: batched at the profiling batch
  size, not the single-query latency the stats per-query profiler produced.)
Accuracy columns (val_*, test_{median,p90,p95,max,mean}_e16) are left BLANK.

Rows (subdir,key) are copied verbatim from the stats CSV so the pool is identical;
each model is matched to its warmup log by the dashed model name in the key.
"""
import argparse, csv, glob, os, re, sys

CHUNK_FACTOR = 40.0
TIME_COLS_RAW = ["time_e1_4_ms", "time_e5_8_ms", "time_e9_12_ms", "time_e13_16_ms"]
TIME_COLS_H100 = ["time_e1_4_h100_ms", "time_e5_8_h100_ms", "time_e9_12_h100_ms", "time_e13_16_h100_ms"]
ACC_COLS = ["val_median_e4", "val_median_e8", "val_median_e12", "val_median_e16",
            "val_p90_e4", "val_p90_e8", "val_p90_e12", "val_p90_e16",
            "test_median_e16", "test_p90_e16", "test_p95_e16", "test_max_e16", "test_mean_e16"]
PIECES_H100 = "e0:H100|e4:H100|e8:H100|e12:H100"


def model_of_key(key):
    m = re.search(r"_h2048_(.+?)_quant-4-bit", key)
    return m.group(1) if m else None


def parse_log(log_path):
    """-> (warmup_ms, after_warmup_ms, mean_per_batch_ms) or (None,...) on miss."""
    txt = open(log_path).read()
    def epoch_total(n):
        m = re.search(rf"\[Train\] Epoch {n} total — ([0-9.]+) ms", txt)
        return float(m.group(1)) if m else None
    warmup = epoch_total(0)
    after = epoch_total(1)
    # mean per-batch over the FIRST [Test] pass, excluding batch 1 (cold start).
    batch_ms = []
    for line in txt.splitlines():
        mb = re.search(r"\[Test\] Batch (\d+) — ([0-9.]+) ms", line)
        if mb:
            n = int(mb.group(1))
            if n == 1 and batch_ms:        # start of a NEW pass -> stop at first pass end
                break
            batch_ms.append((n, float(mb.group(2))))
    body = [v for (n, v) in batch_ms if n != 1]   # drop cold-start batch 1
    mean_pb = (sum(body) / len(body)) if body else None
    return warmup, after, mean_pb


def find_logs(prof_dir, model_dashed):
    """All training logs matching this model (could be >1 batch-size variant)."""
    return sorted(f for f in glob.glob(os.path.join(
            prof_dir, f"time_*_h2048_{model_dashed}_quant-4-bit_*_e2_tr0.1_seed42.log"))
        if not f.endswith(".stdout") and "_inference.log" not in os.path.basename(f))


def best_parse(logs):
    """Among candidate logs, return the parse of the first COMPLETE one (both epoch
    totals); else the first partial parse; (None,None,None) if no logs."""
    partial = None
    for lp in logs:
        w, aw, mpb = parse_log(lp)
        if w is not None and aw is not None:
            return w, aw, mpb, lp
        if partial is None:
            partial = (w, aw, mpb, lp)
    return partial if partial else (None, None, None, None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats_csv", required=True, help="template stats all_models_full_e16.csv")
    ap.add_argument("--prof_dir", required=True, help="warmup_e2_profile dir for the workload")
    ap.add_argument("--out", required=True)
    ap.add_argument("--write", action="store_true", help="actually write --out (else validate-only)")
    a = ap.parse_args()

    with open(a.stats_csv) as f:
        rdr = csv.DictReader(f); header = rdr.fieldnames; rows = list(rdr)
    out_rows, miss, ok = [], [], 0
    for r in rows:
        md = model_of_key(r["key"])
        logs = find_logs(a.prof_dir, md)
        nr = {c: "" for c in header}
        nr["subdir"] = r["subdir"]; nr["key"] = r["key"]
        if not logs:
            miss.append((md, "no-log")); out_rows.append(nr); continue
        w, aw, mpb, _lp = best_parse(logs)
        if w is None or aw is None:
            # incomplete (post-warmup OOM/truncated) -> leave ENTIRE row blank
            miss.append((md, "incomplete-epoch1" if w is not None else "incomplete-epoch0")); out_rows.append(nr); continue
        for c in TIME_COLS_RAW + TIME_COLS_H100:
            nr[c] = f"{(w if c.startswith('time_e1_4') else aw) * CHUNK_FACTOR:.2f}"
        if mpb is not None:
            nr["test_total_eval_ms"] = f"{mpb:.4f}"
            nr["test_testing_took_ms"] = f"{mpb:.4f}"
        nr["pieces_gpu_e1_e5_e9_e13"] = PIECES_H100
        out_rows.append(nr); ok += 1

    print(f"[{os.path.basename(os.path.dirname(a.prof_dir))}] rows={len(rows)} filled={ok} missing={len(miss)}")
    for md, why in miss:
        print(f"    MISS {why}: {md}")
    # sample
    for nr in out_rows[:2] + out_rows[-1:]:
        print(f"    e.g. {model_of_key(nr['key']):28} e1_4={nr['time_e1_4_ms']:>12} "
              f"e5_8={nr['time_e5_8_ms']:>12} infer={nr['test_total_eval_ms']:>10}")
    if a.write:
        os.makedirs(os.path.dirname(a.out), exist_ok=True)
        with open(a.out, "w", newline="") as f:
            wtr = csv.DictWriter(f, fieldnames=header); wtr.writeheader(); wtr.writerows(out_rows)
        print(f"    WROTE {a.out}")


if __name__ == "__main__":
    main()
