# Training & inference time (H100) — averaged across workloads

- **full train (s)** = LLM: per-epoch (e1,tr0.1) x10 (->full data) x16 epochs; baselines: real per-epoch x min(real-epochs, 30) from the actual multi-epoch logs. Averaged over 4 training workloads {stats,tpch,tpcds,imdb}; imdb=Train_job represents job/job_full/syn.
- **infer (ms/query)** = total test-set inference / #test queries (batch=1 for all), averaged over 6 test workloads {stats,tpch,tpcds,job,job_full,syn}.
- LLMs = mode-12 (biCrossAttn + inflatePRICE, cx4). 'bao*' = bao epoch count is not logged, so its training is shown as-measured (NOT epoch-capped at 30).


## postgres

| method | full train (s) | infer (ms/query) |
|---|--:|--:|
| qf | 1,116.1 | 11.93 |
| aimai | 16.5 | 0.83 |
| bao* | 123.0 | 0.72 |
| e2e_cost | 692.4 | 4.49 |
| bert2 | 6,844.6 | 29.85 |
| bert4 | 11,016.6 | 33.14 |
| sentBert | 10,512.4 | 39.92 |

## duckdb

| method | full train (s) | infer (ms/query) |
|---|--:|--:|
| qf | 3,244.6 | 13.42 |
| aimai | 28.9 | 0.35 |
| bao* | 113.6 | 0.54 |
| e2e_cost | 1,298.1 | 4.92 |
| bert2 | 6,198.2 | 28.15 |
| bert4 | 8,398.9 | 30.34 |
| sentBert | 8,825.3 | 37.95 |

## spark

| method | full train (s) | infer (ms/query) |
|---|--:|--:|
| qf | 2,344.3 | 27.66 |
| aimai | 28.3 | 0.51 |
| bao* | 707.3 | 1.47 |
| e2e_cost | 1,082.7 | 4.96 |
| bert2 | 6,445.0 | 28.21 |
| bert4 | 7,569.4 | 30.72 |
| sentBert | 8,558.1 | 39.04 |
