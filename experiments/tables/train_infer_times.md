# Training & inference time (H100) — averaged across workloads

- **full_train (s)** = per-epoch train time (e1, tr0.1) × 10 (→full data) × 16 epochs, averaged over **4 training workloads** {stats, tpch, tpcds, imdb}; imdb represents job/job_full/syn (shared training). Baselines: measured full training time (tr1.0), averaged over the same 4.
- **infer (ms/query)** = total test-set inference time ÷ #test queries (batch=1 for all methods), averaged over the **6 test workloads** {stats, tpch, tpcds, job, job_full, syn}.
- LLMs = mode-12 (biCrossAttn + inflatePRICE, cx4) — the variant in generate_overleaf_table_time.py. Baselines profiled on **postgres only** (reused in the duckdb/spark tables — marked †). bao inference not logged (NA).


## postgres

| method | full train (s) | infer (ms/query) |
|---|--:|--:|
| aimai | 7.7 | 1.60 |
| bao | 30.7 | NA |
| e2e_cost | 63.0 | 6.56 |
| bert2 | 6,844.6 | 29.85 |
| bert4 | 11,016.6 | 33.14 |
| sentBert | 10,512.4 | 39.92 |

## duckdb

| method | full train (s) | infer (ms/query) |
|---|--:|--:|
| aimai † | 7.7 | 1.60 |
| bao † | 30.7 | NA |
| e2e_cost † | 63.0 | 6.56 |
| bert2 | 6,198.2 | 28.15 |
| bert4 | 8,398.9 | 30.34 |
| sentBert | 8,825.3 | 37.95 |

## spark

| method | full train (s) | infer (ms/query) |
|---|--:|--:|
| aimai † | 7.7 | 1.60 |
| bao † | 30.7 | NA |
| e2e_cost † | 63.0 | 6.56 |
| bert2 | 6,445.0 | 28.21 |
| bert4 | 7,569.4 | 30.72 |
| sentBert | 8,558.1 | 39.04 |
