# Baseline stats-embedding concatenation (`--baseline_price_concat`)

Date: 2026-06-05

## 1. Goal

Let the non-LLM baselines — **qf, aimai, e2e_cost, bao** — concatenate a PRICE
(statistics) embedding with their own plan embedding before the downstream MLP,
**exactly like mode 7 of the LLM path** (`LLMPriceJointModel`): the stats embedder is
the same `PRICEEmbedder`, run with no cross-attention (cx=0 → 512-dim), and **trained
jointly** end-to-end with the baseline encoder and the prediction head.

Purpose: measure whether the PRICE stats embedding improves baseline accuracy, the same
way it does for the LLM (mode 1 → mode 7).

## 2. Background (existing code)

- **Mode 7** = `LLMPriceJointModel(llm, price_embedder, llm_embed_size, price_embed_size,
  hid_units)` (`experiments/models/llm_price_model.py`): `Prediction(concat(llm_emb,
  price_emb))`. `PRICEEmbedder` at cx=0 outputs **512-dim**; built on a PRICE regression
  model loaded from `--price_model_path` (or random-init via `--price_random_init`).
  `PRICEEmbedder.forward(x, padding_mask, n_join_col, n_fanout, n_table, n_filter_col, …)`.
- **PRICE features** per query come from
  `price_data_utils.generate_price_features(workload, sql_list, db_name, bin_size, …)` →
  `(data_features, n_join_cols, n_fanouts, n_tables, n_filter_cols)` (and `multi_clause_data`
  under `--price_n_or`). This is the *same* function mode 7 uses; it is cached on disk.
- **Baselines** (`experiments/train.py`):
  - `aimai`: `Prediction(input_dim = len(ds_info.nodeParallels)*5)` on a feature vector (no separate encoder).
  - `qf`: `nn.Sequential(QueryFormer→393, Prediction(393))`.
  - `e2e_cost`: `nn.Sequential(E2E_model→32, Prediction(32))`.
  - `bao`: SEPARATE path — `evaluation/algorithms/bao/model.py::BaoRegression` with its own
    `fit`/`predict` and `BaoNet` (`tree_conv` ending in `DynamicPooling` → pooled embedding;
    final `Linear` commented out, prediction = column 0). Driven by
    `evaluation/trainer.py::train_and_test_bao` (which `sys.exit(0)`s).
- Baseline datasets are built by `utilsTrain.create_dataset_for_algo(algo, ds_info, roots,
  costs, argsP, dat_path, query_ids)`: `get_aimeetsai_ds`, `QueryFormerDataset`, `E2E_Dataset`.

## 3. Architecture

```
plan/features ─► baseline encoder (qf/aimai/e2e/bao) ─► base_emb ─┐
                                                                  ├─► concat ─► Prediction MLP ─► ŷ
SQL + stats   ─► PRICEEmbedder (cx=0, 512-dim, trained jointly) ──┘
```

Two integration mechanisms under **one flag** (different because of bao's separate path):

| baselines | mechanism |
|-----------|-----------|
| qf, aimai, e2e_cost | new `BaselinePriceJointModel` (wraps the `nn.Sequential` encoder) |
| bao | `price_embedder` + a real head MLP inside `BaoRegression` (replaces the column-0 readout) |

Both use the identical `PRICEEmbedder` (cx=0, 512), the identical
`generate_price_features` source, and join by concatenation before a `Prediction` MLP.

## 4. Components

### 4.1 `BaselinePriceJointModel` (new — `experiments/models/baseline_price_model.py`)
```
__init__(base_encoder, price_embedder, base_emb_dim, hid_units, price_emb_dim=512)
forward(plan_input, price_feats) -> Prediction(concat(base_encoder(plan_input),
                                                      price_embedder(price_feats)[0]))
```
- `base_encoder`: the baseline's encoder module (QueryFormer / E2E_model). For **aimai**
  (no encoder — the input vector *is* the embedding), `base_encoder = nn.Identity()` and
  `base_emb_dim = len(nodeParallels)*5`.
- Downstream MLP `input_dim = base_emb_dim + 512` (qf 905, e2e 544, aimai `nodeParallels*5+512`).
- `price_embedder(price_feats)` returns `(price_emb, _, _)`; take `price_emb` (cx=0 → 512).

### 4.2 Price-augmented baseline dataset (`utilsTrain`)
A thin wrapper over each baseline `Dataset` so each item also yields that query's PRICE
feature tensors, plus a collate that batches the baseline input and the PRICE features
together. PRICE features are computed once per workload via `generate_price_features(...)`
and **aligned to the baseline's queries by `query_ids`/index** (the baselines and the PRICE
pipeline process the same workload queries; alignment uses the existing `query_ids` already
passed to `create_dataset_for_algo`). Honors `--price_n_or` (multi-clause) exactly as mode 7.

### 4.3 `BaoRegression` joint path (`evaluation/algorithms/bao/model.py`)
- `BaoRegression` gains an optional `price_embedder` and, when present, a head MLP
  `Prediction(bao_emb_dim + 512, hid_units)` that replaces the column-0 readout.
  `bao_emb_dim` = `BaoNet.tree_conv` (DynamicPooling) output width.
- `fit(X, y, args, val_X=None, val_y=None, price_feats=None, val_price_feats=None)` and
  `predict(X, price_feats=None)` gain the PRICE args. When `price_feats` is given, the
  internal `DataLoader` yields `(tree_batch, price_feats_batch, y)`; forward is
  `head(concat(tree_conv(trees), price_embedder(price_feats)[0]))`; BaoNet + price_embedder +
  head train jointly (the existing val-p90 early-stop loop is reused — its val forward is
  updated to pass `val_price_feats`).
- `train_and_test_bao` (trainer.py) builds `price_embedder` (from the PRICE flags), computes
  `generate_price_features` for train+test (aligned by query index), and threads them into
  `fit`/`predict`.

### 4.4 `train.py` wiring + the flag
- New arg **`--baseline_price_concat`** (store_true). Valid only with `--algo ∈
  {qf, aimai, e2e_cost, bao}`; errors otherwise (and on `--card`, since mode 7 is time-only —
  see Open Questions).
- It **reuses the existing PRICE flags** for the embedder: `--price_model_path`,
  `--price_bin_size`, `--price_n`, `--price_n_or`, `--price_random_init` (same as a mode-7 LLM
  run, minus the LLM flags). The `PRICEEmbedder` is constructed with the same helper mode 7
  uses (cx=0; `n_cross_layers=0`).
- For qf/aimai/e2e_cost: build the augmented dataset + `BaselinePriceJointModel`; train via the
  generic `train()` loop. For bao: route through the augmented `train_and_test_bao`.

### 4.5 Cache + result naming
- The baseline model cache key (`train.py`) and `BaoRegression`'s cache key gain a
  `_priceConcat` segment so the joint model never collides with the plain-baseline cache.
  (The arch-mismatch try/except added earlier remains as a safety net.)
- The result cdf / log filenames gain a `_priceConcat` tag (or the run script passes a distinct
  `--output_dir_qerror`) so a joint run never overwrites the plain-baseline cell.

## 5. Data flow

1. `train.py` loads roots/costs/query_ids for the workload (unchanged).
2. PRICE features for the workload are produced once via `generate_price_features(workload,
   sql_list, db, bin_size)` and indexed by query.
3. The augmented dataset yields, per query, `(baseline_input, price_feature_tensors)`; collate
   batches both.
4. Joint model: `base_emb = encoder(baseline_input)`; `price_emb = PRICEEmbedder(price_feats)`;
   `ŷ = Prediction(concat(base_emb, price_emb))`. End-to-end backprop trains encoder +
   PRICEEmbedder + MLP (bao: + head).
5. Eval/inference uses the same forward; result cdf written with the `_priceConcat` tag.

## 6. Out of scope (this cut)

- Cross-attention PRICE variants (mode 12). cx=0 only, like mode 7.
- New PRICE feature semantics — reuse `generate_price_features` verbatim.
- `postgres` native baseline (no learned embedding to concat into).

## 7. Resolved decisions / assumptions

- **`sql_list` source for alignment (RESOLVED):** the baselines consume the **exact same
  workload files the LLM path uses**, so the per-query SQL fed to `generate_price_features`
  is obtained the same way mode 7 obtains it and aligns to the baseline queries 1:1 (same
  order / `query_ids`, including the syn/job/job_full → imdb canonical training files). The
  implementation reuses mode 7's SQL-loading path verbatim.
- **`--card`:** **time-only** for the first cut (matches mode 7's usage); error on
  `--card + --baseline_price_concat` unless we later confirm card works.

## 8. Testing

- **Smoke per mechanism:** `duckdb/stats` with `--algo qf --baseline_price_concat` (sequential
  path) and `--algo bao --baseline_price_concat` (bao path): builds, trains ≥1 epoch end-to-end,
  MLP `input_dim == base_emb_dim + 512`, writes a `_priceConcat` cdf without OOM/shape errors.
  Use a throwaway `--output_dir_qerror` so no real cell is touched.
- **Guard tests:** `--baseline_price_concat` with `--algo postgres` (or `--card`) errors clearly.
- **Sanity:** the joint cdf differs from the plain-baseline cdf for the same cell (concat is
  actually wired in, not silently ignored).
