#!/usr/bin/env python3
"""
Regenerate train_infer_times.{csv,md} with the LLM rows at cx=2.

cx2 = cx4 x (same-hardware cx2/cx4 ratio), applied to the existing old-H100 cx4
LLM numbers from extract_train_infer_times.compute(). The ratio is measured on
bert2/stats (the one cx4 reference run on the new H100, logsResults_6.8_H100-1.zip):
    new-HW cx2 b24 vs new-HW cx4 b24, batch=1 inference / Epoch-0 training:
        infer 39.85/45.73 = 0.871 ;  train 69814/76040 = 0.918
This isolates the cx-effect (the ~1.56x new-vs-old hardware factor cancels in the
same-HW ratio). One ratio is applied across all 3 models/systems. Baselines unchanged.
"""
import os, csv
import extract_train_infer_times as base

RATIO_TRAIN = 0.918   # same-HW cx2/cx4, Epoch-0 training (bert2/stats)
RATIO_INFER = 0.871   # same-HW cx2/cx4, batch=1 inference (bert2/stats)

llm_cx4, base_vals, base_flag = base.compute()[:3]
SYS, ORDER, BASELINES, MODELS = base.SYSTEMS, base.ORDER, base.BASELINES, base.MODELS

llm_cx2 = {}
for db in SYS:
    for mk in MODELS:
        t4, i4 = llm_cx4[(db, mk)]
        llm_cx2[(db, mk)] = (t4 * RATIO_TRAIN if t4 else None,
                             i4 * RATIO_INFER if i4 else None)

def get(db, m): return base_vals[(db, m)] if m in BASELINES else llm_cx2[(db, m)]
here = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(here, "train_infer_times.csv"), "w", newline="") as fo:
    w = csv.writer(fo); w.writerow(["system", "method", "full_train_s", "infer_ms_per_query", "note"])
    for db in SYS:
        for m in ORDER:
            t, i = get(db, m)
            note = ("baseline_pg_fallback" if (m in BASELINES and base_flag[(db, m)])
                    else f"llm_cx2=cx4x{RATIO_TRAIN}tr/{RATIO_INFER}inf" if m not in BASELINES else "")
            w.writerow([db, m, "" if t is None else f"{t:.2f}", "" if i is None else f"{i:.3f}", note])

def ft(v): return "NA" if v is None else f"{v:,.1f}"
def fi(v): return "NA" if v is None else f"{v:.2f}"
L = ["# Training & inference time (H100) — averaged across workloads | **LLMs at cx=2**\n",
     "- **full train (s)** = LLM: per-epoch (e1,tr0.1) x10 x16; baselines: real per-epoch x min(epochs,30). "
     "Averaged over 4 training workloads {stats,tpch,tpcds,imdb}.",
     "- **infer (ms/query)** = total test-set inference / #test queries (batch=1), avg over 6 test wls.",
     "- LLMs = mode-12 **cx2** (2 cross-attn blocks) = cx4 x same-hardware cx2/cx4 ratio "
     f"(train {RATIO_TRAIN}, infer {RATIO_INFER}; measured bert2/stats, new-H100 cx2-vs-cx4). The ~1.56x "
     "new-vs-old hardware factor cancels in the ratio, so these are old-H100-equivalent. "
     "Baselines unchanged (qf/aimai/bao/e2e_cost).\n"]
for db in SYS:
    L += [f"\n## {db}\n", "| method | full train (s) | infer (ms/query) |", "|---|--:|--:|"]
    for m in ORDER:
        t, i = get(db, m)
        L.append(f"| {m} | {ft(t)} | {fi(i)} |")
open(os.path.join(here, "train_infer_times.md"), "w").write("\n".join(L) + "\n")
print("wrote train_infer_times.{csv,md}\n")
print(open(os.path.join(here, "train_infer_times.md")).read())
