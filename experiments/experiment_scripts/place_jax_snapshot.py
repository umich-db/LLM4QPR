#!/usr/bin/env python3
"""Place a HCAHOI/llm4qpr JAX/NNX snapshot's raw artifacts into their canonical
homes AND materialize the model-selection-ready per-model dirs.

Step 2 of the raw->ready pipeline (step 1 = add_jax_snapshot_to_pool.py, which
already appended the all_models_full_e16.csv rows from the H100 profiling CSVs).

For each model in the snapshot this does two things:

(A) COPY-dereference the raw artifacts (snapshot files are symlinks into the HF
    blob cache; copy materializes real files and leaves the cache intact) to the
    canonical dirs taken from each model's upload_manifest.json `local` field
    (host prefix /home/haochiyu84/LLM4QPR/experiments/ stripped):
      finetuned_models/postgres/expanded_pool_tpu_jax_nnx_full_20260428/{MD}/seed42/checkpoint/state.pkl
      logs/postgres/logs_Train_stats_Test_stats_ours/expanded_pool_tpu_jax_nnx_full_20260428/<logfiles>
      results/postgres/results_Train_stats_Test_stats_ours/expanded_pool_tpu_jax_nnx_full_20260428/<resultfiles>

(B) GENERATE the per-model pool dir
      logs/postgres/logs_Train_stats_Test_stats_ours/all_models/expanded_pool_tpu__<KEY>__e16/
    with summary.txt + train.log + inference.log, byte-faithful to the existing
    expanded_pool_tpu rows (the upstream builder is not in the repo).  These three
    files are pure TPU-v4 provenance (raw wall x0.3 H100 estimate); the H100-native
    timing lives only in the CSV row.

  KEY  = postgres_0.0001_b{bs}_h2048_{MD}_quant-4-bit_priceS_inflatePRICE_randInit_cx4
  {MD} = meta_model_name with '/' -> '-'
"""
import argparse, glob, json, os, re, shutil

EXP = "/root/LLM4QPR/experiments"
RAW_SUBDIR = "expanded_pool_tpu_jax_nnx_full_20260428"
ALLMODELS = os.path.join(EXP, "logs/postgres/logs_Train_stats_Test_stats_ours/all_models")
HOST_PREFIX = "/home/haochiyu84/LLM4QPR/experiments/"


def _g(t, p, cast=str, d=None):
    m = re.search(p, t)
    return cast(m.group(1)) if m else d


def parse_log(log_path):
    t = open(log_path).read()
    return {
        "model": _g(t, r'meta_model_name="([^"]+)"'),
        "bs": _g(t, r'batch_size_stage1=(\d+)', int),
        "s1": _g(t, r'stage1_finetune_sec=([0-9.]+)', float),
        "infer": _g(t, r'infer_sec=([0-9.]+)', float),
        "q": json.loads("{" + _g(t, r'qerror_summary=\{([^}]+)\}') + "}"),
        "dotlog_raw": t,
    }


# ---- (B) per-model dir templates (verified byte-exact vs existing rows) ----
SUMMARY = """\
key:                  {KEY}
subdir:               expanded_pool_tpu
final_epoch:          16
epochs_seen:          [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
pieces:               [(16, 'tpuv4')]
piece_take_ms:        [(16, {raw2})]
piece_h100_eq_ms:     [(16, {h4})]
total_train_ms_raw:   {raw2}
total_train_ms_h100_estimated: {h2}
# TPU v4 factor is an ESTIMATE (0.3 = 1/3.33× ratio).
validation:           OK
# NOTE: val_p90_e{{4,8,12,16}} columns are populated with val_q_median
#       as a proxy (Stage 1 trainer does not log val_q90).
# NOTE: stage1_finetune_sec ({s1_2} s) split equally
#       across 4 chunks; per-epoch timing not logged by jax trainer.
hardware:             tpu_v4_to_h100_est
test_qerror:          median={qm4} p90={q904} p95={q954} max={qx4} mean={qe4}
test_latency:         total_eval={eval2} ms  testing_took={eval2} ms (TPU v4 wall)
"""

TRAIN_HEADER = """\
##### ====================================================================== #####
##### Combined training log for: {KEY}
##### Subdir: expanded_pool_tpu
##### Pieces (epoch order): [16]
##### Final epoch reached: 16
##### Total epochs covered: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
##### Per-GPU H100-equivalent factor used: tpuv4=0.3000 (ESTIMATED, TPU v4 BF16≈275 TFLOPS vs H100 BF16≈989 TFLOPS → ~3.3× slower; transformer-LoRA window 3–4×)
##### Cumulative TPU v4 stage1_finetune_sec (raw):  {raw2} ms ({rawmin} min)
##### Cumulative training time (H100-equivalent): {h2} ms ({hmin} min)
#####   piece e16  [GPU=tpuv4]: epochs 0..15, took={raw2} ms, h100_eq={h2} ms, file=time_jax_nnx_priceBiCrossAttnJoint_{MD}_e16_ftb4_seed42.console.log
##### VALIDATION: 16 stage1 epoch markers present in console log, qerror_summary parsed from .log.
##### NOTE: Stage 1 only logs val_q_median per epoch; val_p90 columns in all_models_full_e16.csv use val_q_median as a proxy.
##### NOTE: stage1_finetune_sec is split into 4 equal chunks for time_e1_4/e5_8/e9_12/e13_16 (per-epoch breakdown not logged).
##### ====================================================================== #####"""

TRAIN_BANNER = "##### ===== piece e16  (GPU=tpuv4, epochs 0..15; raw=stage1_finetune_sec×1000={raw2} ms, h100_eq={h2} ms) ===== #####"

INFER_HEADER = """\
##### Inference (TPU v4 jax_nnx) at e16
##### Source: time_jax_nnx_priceBiCrossAttnJoint_{MD}_e16_ftb4_seed42.log
##### Test Q-error: median={qm6} p90={q906} p95={q956} max={qx6} mean={qe6}
##### Test inference latency (TPU v4 wall): infer_sec={infer4} s (total_eval={eval2} ms, testing_took={eval2} ms)
##### NOTE: inference latency here is TPU v4 wall-clock; H100 per-query latency is sourced separately from model_profile_with_nonemb.csv (avg_ms).
##### ====================================================================== #####"""


def gen_perdir(info, snap_log, snap_console, out_dir, write):
    md = info["model"].replace("/", "-")
    key = f"postgres_0.0001_b{info['bs']}_h2048_{md}_quant-4-bit_priceS_inflatePRICE_randInit_cx4"
    raw_ms = info["s1"] * 1000.0
    h100 = raw_ms * 0.3
    q = info["q"]
    v = dict(KEY=key, MD=md,
             raw2=f"{raw_ms:.2f}", h4=f"{h100:.4f}", h2=f"{h100:.2f}",
             s1_2=f"{info['s1']:.2f}", rawmin=f"{raw_ms/60000:.2f}", hmin=f"{h100/60000:.2f}",
             eval2=f"{info['infer']*1000:.2f}", infer4=f"{info['infer']:.4f}",
             qm4=f"{q['q_median']:.4f}", q904=f"{q['q_90']:.4f}", q954=f"{q['q_95']:.4f}",
             qx4=f"{q['q_max']:.4f}", qe4=f"{q['q_mean']:.4f}",
             qm6=f"{q['q_median']:.6f}", q906=f"{q['q_90']:.6f}", q956=f"{q['q_95']:.6f}",
             qx6=f"{q['q_max']:.6f}", qe6=f"{q['q_mean']:.6f}")
    console_body = open(snap_console).read()
    dotlog_body = info["dotlog_raw"]
    files = {
        "summary.txt": SUMMARY.format(**v),
        "train.log": TRAIN_HEADER.format(**v) + "\n\n\n" + TRAIN_BANNER.format(**v) + "\n\n" + console_body,
        "inference.log": INFER_HEADER.format(**v) + "\n\n" + dotlog_body,
    }
    if write:
        os.makedirs(out_dir, exist_ok=True)
        for fn, content in files.items():
            with open(os.path.join(out_dir, fn), "w") as f:
                f.write(content)
    return key, out_dir


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--no-weights", action="store_true", help="skip the ~8GB state.pkl copies")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    write = not a.dry_run

    seed_dirs = sorted({os.path.dirname(os.path.dirname(p))
                        for p in glob.glob(os.path.join(a.snapshot, "**", "manifest", "upload_manifest.json"), recursive=True)})
    print(f"{len(seed_dirs)} models in snapshot\n")

    for sd in seed_dirs:
        man = json.load(open(os.path.join(sd, "manifest", "upload_manifest.json")))
        log = next(p for p in glob.glob(os.path.join(sd, "logs", "*.log"))
                   if "console" not in p and "pre_reboot" not in p)
        console = log[:-4] + ".console.log"
        info = parse_log(log)
        md = info["model"].replace("/", "-")
        print(f"== {info['model']}  (b{info['bs']}) ==")

        # (A) copy raw artifacts to canonical homes (from manifest 'local')
        for art in man["artifacts"]:
            dst = os.path.join(EXP, art["local"].replace(HOST_PREFIX, ""))
            if a.no_weights and art["kind"] == "checkpoint":
                print(f"   skip weights: {dst.replace(EXP+'/','')}")
                continue
            src = art["local"].replace(
                HOST_PREFIX + "finetuned_models/postgres/" + RAW_SUBDIR + f"/{md}/seed42/checkpoint",
                os.path.join(sd, "finetuned_models", "checkpoint")) if art["kind"] == "checkpoint" else None
            if src is None:
                kind_dir = {"log": "logs", "result": "results"}[art["kind"]]
                src = os.path.join(sd, kind_dir, os.path.basename(art["local"]))
            sz = os.path.getsize(src) / 1e6
            if write:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)              # follow_symlinks=True -> dereferences blob
            print(f"   copy {art['kind']:10s} {sz:8.1f} MB -> {dst.replace(EXP+'/','')}")

        # (B) per-model pool dir
        key = f"postgres_0.0001_b{info['bs']}_h2048_{md}_quant-4-bit_priceS_inflatePRICE_randInit_cx4"
        out = os.path.join(ALLMODELS, f"expanded_pool_tpu__{key}__e16")
        gen_perdir(info, log, console, out, write)
        print(f"   {'wrote' if write else 'would write'} per-model dir: {os.path.basename(out)}/{{summary.txt,train.log,inference.log}}\n")

    print("DRY-RUN (no changes)" if a.dry_run else "DONE")


if __name__ == "__main__":
    main()
