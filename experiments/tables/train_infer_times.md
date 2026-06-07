# Training & inference time (H100) — averaged across workloads

- **full train (s)** = LLM: per-epoch (e1,tr0.1) x10 (->full data) x16 epochs; baselines: measured full training (tr1.0). Averaged over 4 training workloads {stats, tpch, tpcds, imdb}; imdb represents job/job_full/syn.
- **infer (ms/query)** = total test-set inference / #test queries (batch=1 for all), averaged over 6 test workloads {stats, tpch, tpcds, job, job_full, syn}.
- LLMs = mode-12 (biCrossAttn + inflatePRICE, cx4). Dagger = baseline reused from postgres (per-db profiling not collected yet -> run profile_baselines_duckdb_spark.sh).


## postgres

| method | full train (s) | infer (ms/query) |
|---|--:|--:|
| qf | 71.2 | 15.24 |
| aimai | 7.7 | 1.60 |
| bao | 30.7 | NA |
| e2e_cost | 63.0 | 6.56 |
| bert2 | 6,844.6 | 29.85 |
| bert4 | 11,016.6 | 33.14 |
| sentBert | 10,512.4 | 39.92 |

## duckdb

| method | full train (s) | infer (ms/query) |
|---|--:|--:|
| qf (dagger) | 71.2 | 15.24 |
| aimai (dagger) | 7.7 | 1.60 |
| bao (dagger) | 30.7 | NA |
| e2e_cost (dagger) | 63.0 | 6.56 |
| bert2 | 6,198.2 | 28.15 |
| bert4 | 8,398.9 | 30.34 |
| sentBert | 8,825.3 | 37.95 |

## spark

| method | full train (s) | infer (ms/query) |
|---|--:|--:|
| qf (dagger) | 71.2 | 15.24 |
| aimai (dagger) | 7.7 | 1.60 |
| bao (dagger) | 30.7 | NA |
| e2e_cost (dagger) | 63.0 | 6.56 |
| bert2 | 6,445.0 | 28.21 |
| bert4 | 7,569.4 | 30.72 |
| sentBert | 8,558.1 | 39.04 |
