# Baseline stats-embedding concatenation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let baselines `qf`, `aimai`, `e2e_cost`, `bao` concatenate a mode-7-style, jointly-trained PRICE (stats) embedding with their plan embedding before the downstream MLP, via a new `--baseline_price_concat` flag.

**Architecture:** Reuse mode 7's `PRICEEmbedder` (cx=0 → 512-dim). For the three `nn.Sequential` baselines, a new `BaselinePriceJointModel` wraps `concat(base_encoder(x), price_embedder(price_feats)) → Prediction`. For `bao`, add a `price_embedder` + head MLP inside `BaoRegression`. Per-query PRICE features come from `generate_price_features(...)` over the **same workload files the LLM path uses**, aligned to baseline queries by index/`query_ids`.

**Tech stack:** PyTorch, the existing `experiments/models/llm_price_model.py` (`PRICEEmbedder`), `experiments/price_data_utils.generate_price_features`, baseline encoders under `evaluation/algorithms/`.

**Testing reality:** this repo has no pytest suite for this path; "tests" are **smoke runs of `train.py`** with a throwaway `--output_dir_qerror` (so no real result cell is touched), asserting the run builds, trains ≥1 epoch, and prints the expected `input_dim`. Each task ends by running the relevant smoke + committing.

---

## File structure

| File | Responsibility |
|------|----------------|
| `experiments/price_embedder_factory.py` (new) | `build_price_embedder(argsP, device, ds_info) -> (price_embedder, price_feat_dim)` — extract mode 7's PRICE construction once, reuse it for LLM + baselines |
| `experiments/models/baseline_price_model.py` (new) | `BaselinePriceJointModel` (concat wrapper for qf/aimai/e2e_cost) |
| `experiments/baseline_price_data.py` (new) | `attach_price_features(base_ds, price_feats_by_idx)` wrapper + `baseline_price_collate` |
| `experiments/train.py` (modify) | `--baseline_price_concat` flag, build joint model + augmented dataset; refactor PRICE block to call the factory; cache/result `_priceConcat` tag |
| `experiments/utilsTrain.py` (modify) | parse `--baseline_price_concat`; pass through PRICE-feature plumbing |
| `evaluation/algorithms/bao/model.py` (modify) | optional `price_embedder` + head in `BaoRegression.fit/predict` |
| `evaluation/trainer.py` (modify) | `train_and_test_bao` builds price_embedder + price feats, threads them in |

---

## Task 1: Extract PRICEEmbedder construction into a reusable factory

**Files:**
- Create: `experiments/price_embedder_factory.py`
- Modify: `experiments/train.py` (the `if argsP.algo == "llm_price_finetune":` block, ~760–855)

- [ ] **Step 1 — Read the current block.** Read `experiments/train.py:700–960`. Identify the self-contained span that: loads the PRICE state dict (`--price_random_init` gate), computes dims via `_price_dims`, builds the PRICE `RegressionModel`, loads weights, and constructs `price_embedder = PRICEEmbedder(price_model, price_output_dim_override=…)`. Note every `argsP.*` it reads and the `device`.

- [ ] **Step 2 — Move it verbatim into a function.** In `experiments/price_embedder_factory.py`:

```python
"""Build mode-7's cx=0 PRICEEmbedder. Extracted from train.py so the LLM path
and the baselines (--baseline_price_concat) construct the identical embedder."""
import torch
from models.llm_price_model import PRICEEmbedder

def build_price_embedder(argsP, device):
    """Return (price_embedder, price_output_dim). cx=0 -> price_output_dim == 512
    (or argsP.price_output_dim override). Reuses --price_model_path /
    --price_bin_size / --price_n* / --price_random_init exactly like mode 7."""
    # <PASTE the dim setup + RegressionModel build + weight load from train.py here,
    #  unchanged except: take argsP/device as params; do NOT reference LLM vars.>
    price_embedder = PRICEEmbedder(price_model,
                                   price_output_dim_override=getattr(argsP, 'price_output_dim', 0))
    price_embedder.to(device)
    price_output_dim = getattr(price_embedder, 'price_output_dim', 512)
    return price_embedder, price_output_dim
```
Keep the `_price_dims` helper import (or move it alongside). Do NOT change behavior.

- [ ] **Step 3 — Call the factory from train.py.** Replace the moved span in the `llm_price_finetune` block with `price_embedder, _ = build_price_embedder(argsP, device)` (only for the cx=0 / mode-7 path; leave the cross-attn branches as-is).

- [ ] **Step 4 — Smoke: mode 7 still works (regression guard).**
Run (throwaway output):
```bash
cd experiments && source ~/venvs/tmpenv/bin/activate
python train.py --dat_paths_train ../queryPlans/stats/postgres/ --dat_path_test ../queryPlans/stats/postgres/ \
  --output_dir_qerror /tmp/m7_smoke.csv --log_file /tmp/m7_smoke.log --db postgres \
  --workloads_train stats --workload_test stats --algo llm_price_finetune --llm_mode lora \
  --model_name google/bert_uncased_L-2_H-256_A-4 --quantification 4-bit --batch_size 4 --hid_units 2048 \
  --train_ratio 0.05 --num_epoch 1 --seed 42 --price_n --price_n_or --price_random_init \
  --price_model_path price_statistics/model/model_params.pth --price_bin_size 40
```
Expected: builds + trains 1 epoch, no import/shape error (proves the extraction is behavior-preserving).

- [ ] **Step 5 — Commit.** `git add experiments/price_embedder_factory.py experiments/train.py && git commit -m "refactor: extract mode-7 PRICEEmbedder construction into build_price_embedder"`

---

## Task 2: `BaselinePriceJointModel`

**Files:**
- Create: `experiments/models/baseline_price_model.py`

- [ ] **Step 1 — Write the module.**

```python
"""Baseline (qf/aimai/e2e_cost) + PRICE concat, analogous to mode 7's
LLMPriceJointModel: concat(base_encoder(x), price_embedder(price_feats)) -> MLP."""
import torch
import torch.nn as nn

class BaselinePriceJointModel(nn.Module):
    def __init__(self, base_encoder, price_embedder, base_emb_dim, hid_units,
                 price_emb_dim=512):
        super().__init__()
        from trainer import Prediction
        self.base_encoder = base_encoder        # nn.Identity() for aimai
        self.price = price_embedder
        self.mlp = Prediction(base_emb_dim + price_emb_dim, hid_units)

    def forward(self, base_input, price_feats):
        base_emb = self.base_encoder(base_input)
        # PRICEEmbedder.forward(x, padding_mask, n_join_col, n_fanout, n_table, n_filter_col)
        price_emb, _, _ = self.price(*price_feats)
        return self.mlp(torch.cat([base_emb, price_emb], dim=1))
```

- [ ] **Step 2 — Sanity import.** `cd experiments && python -c "import sys; sys.path.insert(0,'../evaluation'); from models.baseline_price_model import BaselinePriceJointModel; print('ok')"`
Expected: `ok`.

- [ ] **Step 3 — Commit.** `git add experiments/models/baseline_price_model.py && git commit -m "feat: BaselinePriceJointModel (baseline + PRICE concat)"`

---

## Task 3: PRICE-feature provider + augmented baseline dataset

**Files:**
- Create: `experiments/baseline_price_data.py`
- Read first: `experiments/train.py:530–536` (how mode 7 builds price feats via `get_price_only_ds_from_csv` and the `price_only_collate` / `price_or_collate`), and `price_data_utils.generate_price_features`.

- [ ] **Step 1 — Determine the per-query PRICE feature tensors.** Read `price_only_collate` (`train.py:475`) and `price_or_collate` (`train.py:494`) to learn the exact tuple `PRICEEmbedder.forward` consumes: `(x, padding_mask, n_join_col, n_fanout, n_table, n_filter_col)`. Confirm the `--price_n_or` (multi-clause) shape.

- [ ] **Step 2 — Write the provider.** In `experiments/baseline_price_data.py`:

```python
"""Per-query PRICE features for baselines, aligned 1:1 to the baseline queries
(same workload files the LLM path uses)."""
import torch
from torch.utils.data import Dataset
from price_data_utils import generate_price_features

def load_price_feats(workload, sql_list, db_name, bin_size, price_n_or):
    """-> list indexed by query position; each entry = the per-query PRICE
    feature tuple PRICEEmbedder.forward consumes. Wraps generate_price_features
    exactly as mode 7 does (honoring price_n_or)."""
    # <build per-query feature tuples from generate_price_features(...) output,
    #  matching what price_only_collate/price_or_collate produce per item>
    ...

class PriceAugmentedDataset(Dataset):
    """Wrap a baseline Dataset so __getitem__ -> (base_item, price_feat_tuple)."""
    def __init__(self, base_ds, price_feats):
        self.base_ds = base_ds
        self.price_feats = price_feats   # aligned to base_ds order
    def __len__(self): return len(self.base_ds)
    def __getitem__(self, i): return self.base_ds[i], self.price_feats[i]

def baseline_price_collate(batch, base_collate):
    """Collate (base_item, price_feat) pairs: base via the baseline's own collate,
    price via stacking into the PRICEEmbedder tuple of batched tensors."""
    base_items = [b for b, _ in batch]
    price_items = [p for _, p in batch]
    base_batch = base_collate(base_items)   # the baseline's existing collate
    price_batch = _stack_price(price_items)  # -> (x, padding_mask, n_join_col, ...)
    return base_batch, price_batch
```
Implement `load_price_feats` / `_stack_price` to mirror `price_only_collate`/`price_or_collate` output exactly (read those two functions and reproduce their stacking).

- [ ] **Step 3 — Smoke the provider in isolation.** Add a `if __name__ == "__main__":` block that loads features for `stats/postgres` (small) and prints the first tuple's tensor shapes; run it. Expected: shapes match `price_only_collate`'s output for one batch.

- [ ] **Step 4 — Commit.** `git add experiments/baseline_price_data.py && git commit -m "feat: per-query PRICE features + augmented baseline dataset"`

---

## Task 4: `--baseline_price_concat` flag + guards

**Files:**
- Modify: `experiments/utilsTrain.py` (the `parse_args()` argparser)
- Modify: `experiments/train.py` (early validation)

- [ ] **Step 1 — Add the flag.** In `utilsTrain.py` parser:
```python
parser.add_argument("--baseline_price_concat", action="store_true",
    help="Concatenate a mode-7 PRICE/stats embedding before the baseline MLP "
         "(algos qf/aimai/e2e_cost/bao). Reuses --price_model_path/--price_bin_size/"
         "--price_n[_or]/--price_random_init.")
```

- [ ] **Step 2 — Guard in train.py** (near the top arg checks):
```python
if getattr(argsP, 'baseline_price_concat', False):
    if argsP.algo not in ("qf", "aimai", "e2e_cost", "bao"):
        raise SystemExit("--baseline_price_concat requires --algo qf|aimai|e2e_cost|bao")
    if argsP.card:
        raise SystemExit("--baseline_price_concat is time-only for now (no --card)")
```

- [ ] **Step 3 — Smoke the guard.** Run train.py with `--baseline_price_concat --algo postgres` → expect the clear error; with `--algo qf --card` → expect the card error.

- [ ] **Step 4 — Commit.** `git add experiments/utilsTrain.py experiments/train.py && git commit -m "feat: --baseline_price_concat flag + guards"`

---

## Task 5: Wire qf/aimai/e2e_cost joint path in train.py

**Files:**
- Modify: `experiments/train.py` (the `aimai`/`qf`/`e2e_cost` model-build block ~637–655; the dataset build via `create_dataset_for_algo`; the cache key block ~1276–1300; the result naming)

- [ ] **Step 1 — Build the joint model** when `baseline_price_concat` and algo ∈ {qf,aimai,e2e_cost}:
```python
if getattr(argsP, 'baseline_price_concat', False) and argsP.algo in ("qf","aimai","e2e_cost"):
    from price_embedder_factory import build_price_embedder
    from models.baseline_price_model import BaselinePriceJointModel
    price_embedder, price_dim = build_price_embedder(argsP, device)
    if argsP.algo == "aimai":
        base_encoder, base_emb_dim = nn.Identity(), len(ds_info.nodeParallels) * 5
    elif argsP.algo == "qf":
        from algorithms.queryformer.model import QueryFormer
        base_encoder, base_emb_dim = QueryFormer(emb_size=64, use_sample=True, use_hist=True), 393
    else:  # e2e_cost
        from algorithms.e2e_cost.e2e_model import E2E_model
        base_encoder, base_emb_dim = E2E_model(32, 64, 64, ds_info), 32
    model_comb = BaselinePriceJointModel(base_encoder, price_embedder, base_emb_dim,
                                         argsP.hid_units, price_emb_dim=price_dim)
```

- [ ] **Step 2 — Build the augmented dataset.** After `create_dataset_for_algo(...)` for these algos, wrap with `PriceAugmentedDataset` and set the DataLoader `collate_fn` to `partial(baseline_price_collate, base_collate=<the algo's existing collate>)`. Load `price_feats` via `load_price_feats(workload, sql_list, db, bin_size, price_n_or)` using the **same `sql_list` the LLM path uses** for this workload (read how mode 7 obtains it and reuse).

- [ ] **Step 3 — Forward unpack.** In the generic `train()`/`evaluate()` calls for these algos, the batch is now `(base_batch, price_batch)`; ensure the model forward receives both (the joint model's `forward(base_input, price_feats)`); the `train()` loop must pass the tuple through. If `train()` assumes a single input tensor, branch on `baseline_price_concat` to call `model(base_batch, price_batch)`.

- [ ] **Step 4 — Cache + result tag.** Append `_priceConcat` to the baseline `_cache_name` (train.py:1287) and to the result/log filename stems when `baseline_price_concat` is set.

- [ ] **Step 5 — Smoke qf.**
```bash
cd experiments && source ~/venvs/tmpenv/bin/activate
python train.py --dat_paths_train ../queryPlans/stats/postgres/ --dat_path_test ../queryPlans/stats/postgres/ \
  --output_dir_qerror /tmp/qf_pc.csv --log_file /tmp/qf_pc.log --db postgres \
  --workloads_train stats --workload_test stats --algo qf --baseline_price_concat \
  --batch_size 16 --hid_units 256 --train_ratio 0.1 --num_epoch 1 --seed 42 \
  --price_n --price_n_or --price_random_init --price_model_path price_statistics/model/model_params.pth --price_bin_size 40
```
Expected: builds, trains 1 epoch; the Prediction MLP input_dim == 393+512 == 905 (add a debug print to confirm); `/tmp/qf_pc.csv` written.

- [ ] **Step 6 — Commit.** `git add -A && git commit -m "feat: wire qf/aimai/e2e_cost --baseline_price_concat joint training"`

---

## Task 6: bao joint path inside `BaoRegression`

**Files:**
- Modify: `evaluation/algorithms/bao/model.py` (`BaoRegression.__init__`, `fit`, `predict`)

- [ ] **Step 1 — Add optional price_embedder + head.** In `BaoRegression.__init__`, accept `price_embedder=None, hid_units=256`. After `self.__net = net.BaoNet(in_channels)` in `fit`, when `price_embedder` is set, build `self.__head = Prediction(bao_emb_dim + 512, hid_units)` where `bao_emb_dim` = the `tree_conv`/DynamicPooling output width (probe one batch: `bao_emb_dim = self.__net(first_batch).shape[1]`).

- [ ] **Step 2 — Thread price feats through fit.** Change `fit(self, X, y, args, val_X=None, val_y=None, price_feats=None, val_price_feats=None)`. When `price_feats` is set: the training `DataLoader` zips `(featurized_tree, price_feat, y)`; the forward becomes `pred = self.__head(torch.cat([self.__net(tree_batch), price_embedder(price_feat_batch)[0]], dim=1))`; optimizer trains `BaoNet + price_embedder + head`. The existing val-p90 early-stop loop's val forward also passes `val_price_feats`.

- [ ] **Step 3 — predict.** `predict(self, X, price_feats=None)`: when set, `pred = self.__head(cat(net(trees), price_embedder(price_feats)[0]))` instead of the column-0 readout.

- [ ] **Step 4 — Smoke (deferred to Task 7's end-to-end run).** Commit the module change.
`git add evaluation/algorithms/bao/model.py && git commit -m "feat: optional PRICE concat + head in BaoRegression"`

---

## Task 7: Wire bao via `train_and_test_bao`

**Files:**
- Modify: `evaluation/trainer.py` (`train_and_test_bao`)
- Modify: `experiments/train.py` (the `bao` branch ~598–627 passes `baseline_price_concat` + price feats)

- [ ] **Step 1 — Build embedder + feats.** In `train_and_test_bao`, when `getattr(args,'baseline_price_concat',False)`: `price_embedder,_ = build_price_embedder(args, device)`; load `price_feats` (train) and `test_price_feats` via `load_price_feats(...)` aligned to `train_roots`/`test_roots`; construct `BaoRegression(have_cache_data=True, price_embedder=price_embedder, hid_units=args.hid_units)`; call `bao.fit(train_roots, train_costs, args, val_X=val_roots, val_y=val_costs, price_feats=price_feats, val_price_feats=val_price_feats)` and `bao.predict(test_roots, price_feats=test_price_feats)`. Append `_priceConcat` to the bao cache key.

- [ ] **Step 2 — Smoke bao end-to-end (throwaway output).**
```bash
cd experiments && source ~/venvs/tmpenv/bin/activate
python train.py --dat_paths_train ../queryPlans/stats/postgres/ --dat_path_test ../queryPlans/stats/postgres/ \
  --output_dir_qerror /tmp/bao_pc.csv --log_file /tmp/bao_pc.log --db postgres \
  --workloads_train stats --workload_test stats --algo bao --baseline_price_concat \
  --batch_size 16 --hid_units 256 --train_ratio 0.1 --num_epoch 2 --seed 42 \
  --price_n --price_n_or --price_random_init --price_model_path price_statistics/model/model_params.pth --price_bin_size 40
```
Expected: trains, the head input dim == bao_emb_dim+512, `/tmp/bao_pc.csv` written, no shape error in the joint forward.

- [ ] **Step 3 — Commit.** `git add -A && git commit -m "feat: wire bao --baseline_price_concat via train_and_test_bao"`

---

## Task 8: Sanity + docs

- [ ] **Step 1 — Concat-actually-wired check.** Diff `/tmp/qf_pc.csv` vs a plain `qf` run on the same cell (throwaway outputs) — they must differ (proves PRICE is feeding the prediction, not silently dropped).
- [ ] **Step 2 — Update CLAUDE.md Baselines section** with a one-line note on `--baseline_price_concat` (reuses `--price_*`; two mechanisms; `_priceConcat` tag).
- [ ] **Step 3 — Commit.** `git add CLAUDE.md && git commit -m "docs: --baseline_price_concat in CLAUDE.md Baselines"`

---

## Self-review notes
- Spec §4.1–4.5 → Tasks 2/3/5/6/7/4 (model, dataset, wiring, bao, cache/naming, flag). §5 data flow → Tasks 3+5+7. §8 testing → smokes in Tasks 1/5/7/8.
- The two big "paste/reproduce" steps (Task 1 PRICE block, Task 3 collate stacking) are reuse-of-existing-code, not new logic — the executor copies from the cited line ranges rather than inventing.
- Interfaces consistent: `build_price_embedder(argsP, device) -> (price_embedder, dim)`; `BaselinePriceJointModel(base_encoder, price_embedder, base_emb_dim, hid_units, price_emb_dim)`; `load_price_feats(workload, sql_list, db, bin_size, price_n_or)`; `BaoRegression(..., price_embedder, hid_units)` + `fit(..., price_feats, val_price_feats)` / `predict(X, price_feats)`.
