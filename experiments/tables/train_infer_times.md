# Training & inference time (H100) — averaged across workloads | **LLMs at cx=2**

- **full train (s)** = LLM: per-epoch (e1,tr0.1) x10 x16; baselines: real per-epoch x min(epochs,30). Averaged over 4 training workloads {stats,tpch,tpcds,imdb}.
- **infer (ms/query)** = total test-set inference / #test queries (batch=1), avg over 6 test wls.
- LLMs = mode-12 **cx2** (2 cross-attn blocks) = cx4 x same-hardware cx2/cx4 ratio (train 0.918, infer 0.871; measured bert2/stats, new-H100 cx2-vs-cx4). The ~1.56x new-vs-old hardware factor cancels in the ratio, so these are old-H100-equivalent. Baselines unchanged (qf/aimai/bao/e2e_cost).


## postgres

| method | full train (s) | infer (ms/query) |
|---|--:|--:|
| qf | 1,116.1 | 11.93 |
| aimai | 16.5 | 0.83 |
| bao | 123.0 | 0.72 |
| e2e_cost | 692.4 | 4.49 |
| bert2 | 6,283.4 | 26.00 |
| bert4 | 10,113.3 | 28.87 |
| sentBert | 9,650.3 | 34.77 |

## duckdb

| method | full train (s) | infer (ms/query) |
|---|--:|--:|
| qf | 3,244.6 | 13.42 |
| aimai | 28.9 | 0.35 |
| bao | 113.6 | 0.54 |
| e2e_cost | 1,298.1 | 4.92 |
| bert2 | 5,690.0 | 24.52 |
| bert4 | 7,710.2 | 26.42 |
| sentBert | 8,101.6 | 33.05 |

## spark

| method | full train (s) | infer (ms/query) |
|---|--:|--:|
| qf | 2,344.3 | 27.66 |
| aimai | 28.3 | 0.51 |
| bao | 707.3 | 1.47 |
| e2e_cost | 1,082.7 | 4.96 |
| bert2 | 5,916.5 | 24.57 |
| bert4 | 6,948.7 | 26.76 |
| sentBert | 7,856.3 | 34.00 |
