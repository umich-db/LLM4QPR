#!/usr/bin/env python3
"""Append JAX/NNX expanded-pool snapshot models to all_models_full_e16.csv.

ACCURACY comes from the HCAHOI/llm4qpr HF snapshot (full TPU v4 e16 mode-12 runs);
TIMING comes from the H100 profiling runs in /root/h100_profile_runs_2026-05-18
(this is the convention the existing `expanded_pool_tpu` rows already follow).

Snapshot per model (accuracy + fallback timing):
  seed42/logs/...e16_ftb{bs}_seed42.log          stage1_finetune_sec, infer_sec, qerror_summary
  seed42/logs/...e16_ftb{bs}_seed42.console.log  per-epoch stage1 val_q_median (e4/8/12/16)

H100 profiling (timing), in csvs/:
  profile_model_db_warmup_e2.csv   model,warmup_ms,after_warmup_ms,infer_ms,exit_code,log
        -- e2 run on tr0.1 (10% data): 1 warmup(frozen) epoch + 1 post-warmup(unfrozen) epoch
  profile_model_db_h100_per_query_ms.csv  model,model_dashed,n_batches,mean_per_query_ms,first_batch_ms

Column derivation (verified to the cent against existing pool rows):
  time_e1_4_{ms,h100_ms}                 = warmup_ms       * 40   (x10 for 0.1->full data, x4 epochs/chunk)
  time_{e5_8,e9_12,e13_16}_{ms,h100_ms}  = after_warmup_ms * 40   (3 identical post-warmup chunks)
  pieces_gpu_e1_e5_e9_e13                = e0:H100|e4:H100|e8:H100|e12:H100   (raw == h100, ratio 1)
  test_per_query_ms = test_testing_took_ms = mean_per_query_ms (H100 per-query)

  FALLBACK when the H100 warmup_e2 profiling FAILED (exit!=0 / NA), exactly like the
  existing albert-large-v1/v2 rows: TPU v4 wall split equally x 0.3 (H100-equiv estimate):
      time_*_ms      = stage1_finetune_sec*1000 / 4
      time_*_h100_ms = that * 0.3
      pieces         = e0:tpuv4|e4:tpuv4|e8:tpuv4|e12:tpuv4
  eval_ms still uses H100 mean_per_query_ms when that probe succeeded (it is independent
  of the training probe); only if BOTH failed is eval_ms left blank.

  val_median_e{4,8,12,16} = stage1 val_q_median at those epochs (from snapshot)
  val_p90_e{4,8,12,16}    = same as val_median (stage1 logs no q90; documented proxy)
  test_*_e16              = snapshot final qerror_summary
"""
import argparse, csv, glob, json, os, re, shutil

CHUNK_FACTOR = 40.0       # (1/0.1 data) * (4 epochs/chunk)
TPU_TO_H100 = 0.3
SUBDIR = "expanded_pool_tpu"
HEADER = ["subdir","key","time_e1_4_ms","time_e5_8_ms","time_e9_12_ms","time_e13_16_ms",
          "time_e1_4_h100_ms","time_e5_8_h100_ms","time_e9_12_h100_ms","time_e13_16_h100_ms",
          "val_median_e4","val_median_e8","val_median_e12","val_median_e16",
          "val_p90_e4","val_p90_e8","val_p90_e12","val_p90_e16",
          "test_median_e16","test_p90_e16","test_p95_e16","test_max_e16","test_mean_e16",
          "test_per_query_ms","test_testing_took_ms","pieces_gpu_e1_e5_e9_e13"]


def _g(text, pat, cast=str, default=None):
    m = re.search(pat, text)
    return cast(m.group(1)) if m else default


def _is_num(s):
    try:
        float(s); return True
    except (TypeError, ValueError):
        return False


def load_profile(csv_dir):
    warm, perq = {}, {}
    with open(os.path.join(csv_dir, "profile_model_db_warmup_e2.csv")) as f:
        for r in csv.DictReader(f):
            warm[r["model"]] = r
    with open(os.path.join(csv_dir, "profile_model_db_h100_per_query_ms.csv")) as f:
        for r in csv.DictReader(f):
            perq[r["model"]] = r
    return warm, perq


def build_row(log_path, warm, perq):
    txt = open(log_path).read()
    con = log_path[:-4] + ".console.log"
    con = open(con).read() if os.path.exists(con) else ""

    model = _g(txt, r'meta_model_name="([^"]+)"')
    bs = _g(txt, r'batch_size_stage1=(\d+)', int)
    s1 = _g(txt, r'stage1_finetune_sec=([0-9.]+)', float)
    q = json.loads("{" + _g(txt, r'qerror_summary=\{([^}]+)\}') + "}")
    vals = []
    for e in (4, 8, 12, 16):
        m = re.search(rf'\[stage1 epoch={e}/16\] .*?val_q_median=([0-9.]+)', con)
        vals.append(f"{float(m.group(1)):.6f}" if m else "")

    w = warm.get(model, {})
    warmup_ok = w.get("exit_code") == "0" and _is_num(w.get("warmup_ms")) and _is_num(w.get("after_warmup_ms"))
    note = ""
    if warmup_ok:                                   # H100-native timing
        e1_4 = float(w["warmup_ms"]) * CHUNK_FACTOR
        post = float(w["after_warmup_ms"]) * CHUNK_FACTOR
        raw = [e1_4, post, post, post]
        h100 = list(raw)
        pieces = "e0:H100|e4:H100|e8:H100|e12:H100"
    else:                                           # TPU v4 wall x0.3 fallback (albert-large precedent)
        chunk = s1 * 1000.0 / 4.0
        raw = [chunk] * 4
        h100 = [chunk * TPU_TO_H100] * 4
        pieces = "e0:tpuv4|e4:tpuv4|e8:tpuv4|e12:tpuv4"
        note = "TPU-est (H100 warmup_e2 profiling failed)"

    pq = perq.get(model, {})
    eval_ms = f"{float(pq['mean_per_query_ms']):.4f}" if _is_num(pq.get("mean_per_query_ms")) else ""
    if not eval_ms:
        note = (note + "; " if note else "") + "no H100 per-query eval"

    key = (f"postgres_0.0001_b{bs}_h2048_{model.replace('/', '-')}"
           f"_quant-4-bit_priceS_inflatePRICE_randInit_cx4")
    row = [SUBDIR, key,
           *[f"{x:.2f}" for x in raw], *[f"{x:.2f}" for x in h100],
           *vals, *vals,
           f"{q['q_median']:.6f}", f"{q['q_90']:.6f}", f"{q['q_95']:.6f}",
           f"{q['q_max']:.6f}", f"{q['q_mean']:.6f}",
           eval_ms, eval_ms, pieces]
    return key, row, note


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--profile_csv_dir", required=True)
    ap.add_argument("--pool", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    warm, perq = load_profile(a.profile_csv_dir)
    logs = sorted(p for p in glob.glob(os.path.join(a.snapshot, "**", "*.log"), recursive=True)
                  if "console" not in p and "pre_reboot" not in p)
    built = [build_row(p, warm, perq) for p in logs]

    with open(a.pool) as f:
        rdr = csv.reader(f); header = next(rdr)
        existing = {r[1] for r in rdr if r}
    assert header == HEADER, "pool header mismatch"

    new = [(k, r, n) for k, r, n in built if k not in existing]
    print(f"parsed {len(built)} models; {len(new)} new")
    for k, r, n in built:
        tag = "NEW " if k in {x[0] for x in new} else "skip"
        flag = f"   [{n}]" if n else ""
        print(f"  {tag} e1_4_h100={r[6]:>14} eval={r[23]:>9}  {k.split('h2048_')[1].split('_quant')[0]}{flag}")

    if a.dry_run or not new:
        print("(dry-run / nothing to write)"); return
    bak = a.pool.replace(".csv", ".backup_2026-05-30_pre_jax_expand.csv")
    shutil.copy2(a.pool, bak); print("backup ->", bak)
    with open(a.pool, "a", newline="") as f:
        w = csv.writer(f)
        for _, r, _ in new:
            w.writerow(r)
    print(f"appended {len(new)} rows -> {a.pool}")


if __name__ == "__main__":
    main()
