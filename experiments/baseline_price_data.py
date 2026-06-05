"""Per-query PRICE features for baselines, aligned 1:1 to the baseline queries
(same workload files the LLM path uses).

This module is the Task-3 PRICE-feature provider for the baseline-concat feature
(qf / aimai / e2e_cost / bao).  It wraps PRICE feature extraction exactly the way
mode 7 (`--algo llm_price_finetune` / `price_finetune`) does, so the batched
``price_batch`` tuple this module produces is interchangeable with what mode 7
feeds ``PRICEEmbedder.forward(x, padding_mask, n_join_col, n_fanout, n_table,
n_filter_col, ..., num_clauses=...)``.

Two reproduction anchors (both in ``experiments/train.py``):

  * single-clause (``--price_n`` without ``--price_n_or``): the per-item tuple
    and the batch stacking mirror ``price_only_collate`` (train.py ~474-490) and
    the LLM-path ``llm_price_collate`` (train.py ~408-433).  The ``pg_est_card``
    that ``price_only_collate`` additionally carries is **not** consumed by
    ``PRICEEmbedder.forward`` (it feeds the standalone PriceOnly regression head),
    so it is intentionally omitted here.

  * multi-clause DNF (``--price_n_or``): the per-item packed tensors and the
    batch stacking + reshape mirror ``price_or_collate`` (train.py ~493-510) and
    the LLM-path ``llm_price_or_collate`` (train.py ~436-472).  Because
    ``PRICEEmbedder.forward`` expects ``x`` already flattened to
    ``(batch * max_clauses, flat_size)`` (it re-derives ``max_c`` from
    ``per_clause_emb.size(0) // bsz``), we reproduce the
    ``llm_price_or_collate`` 3D->2D reshape (train.py ~463-468) here, so the
    returned ``price_batch`` is directly forward-ready.

Alignment contract: ``load_price_feats`` returns a list indexed ``0..N-1`` in
the SAME order as ``sql_list``.  The caller (Task 5/7) MUST pass ``sql_list`` in
the same order as the baseline ``roots`` / ``query_ids`` so that
``PriceAugmentedDataset`` can zip the two by index.
"""
import os
import sys

import torch

# train.py runs from experiments/ and prepends ../PRICE (or /root/PRICE) to
# sys.path so PRICE's feature tooling (setup.features_tool_n, etc.) resolves.
# price_data_utils relies on that bootstrap; replicate it here so this module can
# be imported from the baseline path without importing train.py (which would run
# the whole training script at import time).  Mirrors price_embedder_factory.py.
_experiments_dir = os.path.dirname(os.path.abspath(__file__))
if _experiments_dir not in sys.path:
    sys.path.insert(0, _experiments_dir)
_local_price = os.path.join(_experiments_dir, "..", "PRICE")
_price_root = _local_price if os.path.isdir(os.path.join(_local_price, "setup")) else "/root/PRICE"
if _price_root not in sys.path:
    sys.path.insert(0, _price_root)

from torch.utils.data import Dataset

import price_data_utils as pdu
from price_data_utils import generate_price_features  # noqa: F401 (public re-export per spec)


# ---------------------------------------------------------------------------
# Per-query feature construction
# ---------------------------------------------------------------------------
def load_price_feats(workload, sql_list, db_name, bin_size, price_n_or):
    """Build per-query PRICE features for ``sql_list``.

    Returns a list indexed by query position (0..N-1, same order as
    ``sql_list``).  Each entry is the per-query PRICE feature tuple that
    ``PRICEEmbedder.forward`` consumes (after batch stacking by
    ``_stack_price``):

      * single-clause (``price_n_or=False``):
            (price_feat, pad_mask, n_join_col, n_fanout, n_table, n_filter_col)
        where ``price_feat`` is a 1-D float tensor (flat_size,) and ``pad_mask``
        is a 1-D tensor (mask_size,).

      * multi-clause DNF (``price_n_or=True``):
            (price_feat, pad_mask, n_join_col, n_fanout, n_table, n_filter_col,
             num_clauses_i)
        where ``price_feat`` is (max_clauses, flat_size) and ``pad_mask`` is
        (max_clauses, mask_size) — all clauses of one query packed, exactly as
        the mode-7 LLMPriceDataset stores them under ``--price_n_or``.

    This wraps ``generate_price_features`` + ``pad_and_cache_features`` with the
    SAME PRICE_N configuration mode 7 uses (``--price_n`` => all four PRICE_N
    sub-flags on => 75-dim filter / 42-dim fanout tokens), honoring
    ``price_n_or`` for the DNF multi-clause path.  No train/val/test split is
    applied: features are produced for the whole ``sql_list`` in order so the
    caller can align them 1:1 to the baseline ``roots``.
    """
    # Mode 7's PRICE_N config: the `--price_n` shorthand turns on all four
    # PRICE_N sub-flags (see CLAUDE.md PRICE_N_FLAGS). Sql2FeatureN always emits
    # 75-dim filter / 42-dim fanout tokens; the sub-flags only gate which atoms
    # are populated, not the token shape — so we enable all four to match the
    # embedder dims produced by price_embedder_factory._price_dims.
    pn_parsing = pn_filter = pn_fanout = pn_pairwise = True
    or_max_clauses = 16  # default --price_n_or_max_clauses

    gpf_out = generate_price_features(
        workload, sql_list, db_name, bin_size,
        price_n_parsing=pn_parsing,
        price_n_filter=pn_filter,
        price_n_fanout=pn_fanout,
        price_n_pairwise=pn_pairwise,
        price_n_or=price_n_or,
        price_n_or_max_clauses=or_max_clauses,
    )

    if price_n_or:
        # multi_clause_data: list[list[6-tuple]] (per-query list of per-clause
        # feature tuples).  Pad via the multi_clause path, then pack each query's
        # rows into (max_clauses, flat_size) — mirrors get_llm_price_ds_from_csv's
        # _pad_and_unpack / _pack_multi_clause (utilsLLM.py ~4794-4839).
        multi_clause_data = gpf_out[0]
        n_join_cols = gpf_out[1]
        n_fanouts = gpf_out[2]
        n_tables = gpf_out[3]
        n_filter_cols = gpf_out[4]

        out = pdu.pad_and_cache_features(
            [], [], [], [], [],
            bin_size=bin_size,
            filter_dim=75,
            price_n_pairwise=pn_pairwise,
            fanout_dim=42,
            pairwise_intra_dim=70,
            multi_clause_data=multi_clause_data,
        )
        flat_pf = out["padded_features"]          # (n_queries * max_clauses) tensors
        flat_pm = out["padding_masks"]
        max_n_clauses = int(out["max_n_clauses"])
        num_clauses = out["num_clauses"].tolist()  # per-query valid clause count
        n_queries = len(multi_clause_data)

        feats = []
        for qi in range(n_queries):
            slc = flat_pf[qi * max_n_clauses:(qi + 1) * max_n_clauses]
            pf_q = torch.stack([
                f if isinstance(f, torch.Tensor) else torch.tensor(f, dtype=torch.float32)
                for f in slc])
            ms = flat_pm[qi * max_n_clauses:(qi + 1) * max_n_clauses]
            pm_q = torch.stack([
                m if isinstance(m, torch.Tensor) else torch.tensor(m)
                for m in ms])
            # n_*_col in OR mode are per-query counts (max over the query's
            # clauses, as PRICEEmbedder expects a single count per query).
            feats.append((pf_q, pm_q,
                          n_join_cols[qi], n_fanouts[qi],
                          n_tables[qi], n_filter_cols[qi],
                          int(num_clauses[qi])))
        return feats

    # Single-clause path: data_features is list of 5-tuples (Sql2FeatureN always
    # emits 5-tuples). pad_and_cache_features auto-detects the 5-tuple shape and
    # returns one flat (flat_size,) tensor + (mask_size,) mask per query.
    #
    # Because ``--price_n`` sets price_n_pairwise=True (utilsTrain.py ~386-390),
    # generate_price_features returns a 6-tuple here — an EXTRA trailing
    # ``n_pairwise_intras`` (per-query pairwise-token counts) beyond the usual
    # five (price_data_utils.py return ~4774-4775). We MUST thread that count
    # into pad_and_cache_features exactly as mode 7 does
    # (get_price_only_ds_from_csv, utilsLLM.py ~4449-4453 + the single-clause
    # call ~4486-4491): without ``price_n_pairwise=True`` /
    # ``pairwise_intra_dim=70`` / ``n_pairwise_intras=...`` the pairwise token
    # axis is silently dropped, so when a workload has column-vs-column
    # predicates (pairwise>0) our flat width would be (B,525) while mode 7
    # yields (B, 525 + 70*max_pi) — a wrong-width tensor fed to the shared
    # PRICEEmbedder. (Coincides only because standard benchmarks have pairwise=0.)
    data_features = gpf_out[0]
    n_join_cols = gpf_out[1]
    n_fanouts = gpf_out[2]
    n_tables = gpf_out[3]
    n_filter_cols = gpf_out[4]
    n_pairwise_intras = gpf_out[5]  # 6-tuple under price_n_pairwise=True

    padded_features, padding_masks, _max_njc, _max_nfo, _max_ntb, _max_nfc, _max_npi = \
        pdu.pad_and_cache_features(
            data_features, n_join_cols, n_fanouts, n_tables, n_filter_cols,
            bin_size=bin_size,
            filter_dim=75,
            price_n_pairwise=pn_pairwise,
            fanout_dim=42,
            pairwise_intra_dim=70,
            n_pairwise_intras=n_pairwise_intras,
        )

    feats = []
    for i in range(len(padded_features)):
        feats.append((padded_features[i], padding_masks[i],
                      n_join_cols[i], n_fanouts[i],
                      n_tables[i], n_filter_cols[i]))
    return feats


# ---------------------------------------------------------------------------
# Batch stacking — mirrors price_only_collate / price_or_collate
# ---------------------------------------------------------------------------
def _stack_price(price_items):
    """Stack a list of per-query PRICE feature tuples into the batched tuple
    ``PRICEEmbedder.forward`` consumes.

    Detects the OR (multi-clause) variant by item length (7 vs 6).

    Single-clause -> (price_feats, pad_masks, njcs, nfos, ntbs, nfcs)
      Mirrors price_only_collate (train.py ~479-490), minus pg_est_card (the
      embedder does not consume it), and the LLM-path llm_price_collate
      (train.py ~424-429): stack the per-query flat tensors, stack the masks,
      and make each count an (N, 1) float column.

    Multi-clause (OR) -> (price_feats, pad_masks, njcs, nfos, ntbs, nfcs, num_clauses)
      Mirrors price_or_collate (train.py ~501-510) for the stacking + the
      num_clauses long tensor, then applies the llm_price_or_collate 3D->2D
      reshape (train.py ~463-468) so price_feats is
      (batch * max_clauses, flat_size) and pad_masks is
      (batch * max_clauses, mask_len) — the layout PRICEEmbedder.forward expects
      when num_clauses is provided.
    """
    is_or = len(price_items[0]) == 7
    if is_or:
        pf, pm, njc, nfo, ntb, nfc, nc = zip(*price_items)
    else:
        pf, pm, njc, nfo, ntb, nfc = zip(*price_items)

    # Stack price feats / masks (identical to *_collate).
    price_feats = torch.stack([
        f if isinstance(f, torch.Tensor) else torch.tensor(f, dtype=torch.float32)
        for f in pf]).float()
    pad_masks = torch.stack([
        m if isinstance(m, torch.Tensor) else torch.tensor(m)
        for m in pm]).float()
    njcs = torch.tensor(njc, dtype=torch.float32).unsqueeze(1)
    nfos = torch.tensor(nfo, dtype=torch.float32).unsqueeze(1)
    ntbs = torch.tensor(ntb, dtype=torch.float32).unsqueeze(1)
    nfcs = torch.tensor(nfc, dtype=torch.float32).unsqueeze(1)

    if not is_or:
        return (price_feats, pad_masks, njcs, nfos, ntbs, nfcs)

    num_clauses = torch.tensor(nc, dtype=torch.long)
    # 3D (batch, max_clauses, *) -> 2D (batch * max_clauses, *), exactly as
    # llm_price_or_collate does before handing x to PRICEEmbedder.forward.
    if price_feats.dim() == 3:
        bsz, max_c, flat_size = price_feats.shape
        price_feats = price_feats.view(bsz * max_c, flat_size)
    if pad_masks.dim() == 3:
        bsz, max_c, mask_len = pad_masks.shape
        pad_masks = pad_masks.view(bsz * max_c, mask_len)
    return (price_feats, pad_masks, njcs, nfos, ntbs, nfcs, num_clauses)


# ---------------------------------------------------------------------------
# Augmented dataset + collate
# ---------------------------------------------------------------------------
class PriceAugmentedDataset(Dataset):
    """Wrap a baseline Dataset so __getitem__ -> (base_item, price_feat_tuple).

    ``price_feats`` must be aligned to ``base_ds`` order (index i of price_feats
    corresponds to index i of base_ds) — see the alignment contract in
    ``load_price_feats``.
    """
    def __init__(self, base_ds, price_feats):
        assert len(base_ds) == len(price_feats), (
            f"base_ds ({len(base_ds)}) and price_feats ({len(price_feats)}) "
            f"length mismatch — they must be index-aligned")
        self.base_ds = base_ds
        self.price_feats = price_feats   # aligned to base_ds order

    def __len__(self):
        return len(self.base_ds)

    def __getitem__(self, i):
        return self.base_ds[i], self.price_feats[i]


def baseline_price_collate(batch, base_collate):
    """Collate (base_item, price_feat) pairs.

    The base half goes through the baseline's own collate; the price half is
    stacked into the PRICEEmbedder tuple of batched tensors via ``_stack_price``.
    """
    base_items = [b for b, _ in batch]
    price_items = [p for _, p in batch]
    base_batch = base_collate(base_items)    # the baseline's existing collate
    price_batch = _stack_price(price_items)  # -> (x, padding_mask, n_join_col, ...)
    return base_batch, price_batch


# ---------------------------------------------------------------------------
# CPU verification (feature extraction is CPU-only; no GPU required)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from functools import partial
    from torch.utils.data import DataLoader

    workload = "stats"
    db_name = "stats"          # get_db_name_for_workload("stats") == "stats"
    bin_size = 40

    # Read the SAME source file mode 7 uses for the stats cardinality workload:
    #   get_price_only_ds_from_csv -> get_sql_file_for_workload("stats", card=True)
    #   -> queries_true_sql/stats_statsCEB_sub.sql, parsed by
    #      extract_raw_sql_from_queries_true.
    sql_file = pdu.get_sql_file_for_workload(workload, card=True)
    print(f"[verify] SQL source (mode-7 stats card file): {sql_file}")
    all_sqls = pdu.extract_raw_sql_from_queries_true(sql_file)
    N = min(8, len(all_sqls))
    sql_list = all_sqls[:N]
    print(f"[verify] using {N} stats SQLs")

    for price_n_or in (False, True):
        print(f"\n========== price_n_or={price_n_or} ==========")
        feats = load_price_feats(workload, sql_list, db_name, bin_size, price_n_or)
        print(f"[verify] load_price_feats -> {len(feats)} per-query entries; "
              f"each entry length = {len(feats[0])}")

        base_ds = list(range(N))                 # trivial dummy baseline dataset
        aug = PriceAugmentedDataset(base_ds, feats)

        loader = DataLoader(
            aug, batch_size=4, shuffle=False,
            collate_fn=partial(baseline_price_collate,
                               base_collate=lambda xs: torch.tensor(xs)),
        )
        base_batch, price_batch = next(iter(loader))
        print(f"[verify] base_batch: shape={tuple(base_batch.shape)} dtype={base_batch.dtype}")
        names = (["price_feats", "pad_masks", "njcs", "nfos", "ntbs", "nfcs"]
                 + (["num_clauses"] if price_n_or else []))
        print(f"[verify] price_batch tuple length = {len(price_batch)}")
        for nm, t in zip(names, price_batch):
            print(f"    {nm:12s} shape={tuple(t.shape)} dtype={t.dtype}")

        if not price_n_or:
            # Strengthened single-clause cross-check: instead of re-stacking the
            # SAME `feats` (which can't catch a pairwise-arg divergence — it just
            # re-collates what load_price_feats already produced), independently
            # re-run generate_price_features + pad_and_cache_features with mode
            # 7's EXACT single-clause kwargs (get_price_only_ds_from_csv,
            # utilsLLM.py ~4449-4453 + the call ~4486-4491: price_n_pairwise=True,
            # filter_dim=75, fanout_dim=42, pairwise_intra_dim=70,
            # n_pairwise_intras=<from the 6-tuple return>). The per-query flat
            # tensor + mask WIDTHS from that mode-7 reproduction must equal what
            # load_price_feats produces; if the single-clause path ever dropped
            # the pairwise args, the widths would diverge whenever pairwise>0.
            _gpf = generate_price_features(
                workload, sql_list, db_name, bin_size,
                price_n_parsing=True, price_n_filter=True,
                price_n_fanout=True, price_n_pairwise=True,
                price_n_or=False,
            )
            assert len(_gpf) == 6, (
                f"generate_price_features(price_n_pairwise=True) arity "
                f"{len(_gpf)} != 6 (expected the extra n_pairwise_intras)")
            _df, _njc, _nfo, _ntb, _nfc, _npi = _gpf
            ref_pf_list, ref_pm_list, *_ = pdu.pad_and_cache_features(
                _df, _njc, _nfo, _ntb, _nfc,
                bin_size=bin_size,
                filter_dim=75,
                price_n_pairwise=True,
                fanout_dim=42,
                pairwise_intra_dim=70,
                n_pairwise_intras=_npi,
            )
            ref_flat_w = ref_pf_list[0].shape[-1]
            ref_mask_w = ref_pm_list[0].shape[-1]
            got_flat_w = price_batch[0].shape[-1]
            got_mask_w = price_batch[1].shape[-1]
            max_npi = max(_npi) if _npi else 0
            print(f"[verify] mode-7 single-clause widths: flat={ref_flat_w} "
                  f"mask={ref_mask_w} (max pairwise-intra tokens={max_npi})")
            ok = (got_flat_w == ref_flat_w and got_mask_w == ref_mask_w and
                  price_batch[2].shape == (4, 1) and price_batch[5].shape == (4, 1))
            print(f"[verify] single-clause widths match mode-7 "
                  f"pad_and_cache_features: {ok} "
                  f"(load_price_feats flat={got_flat_w} mask={got_mask_w})")
            assert ok, (
                "single-clause price_batch widths diverge from mode-7 "
                "pad_and_cache_features — pairwise token axis mismatch!")
        else:
            # OR (multi-clause) path already threads multi_clause_data (whose
            # padding includes the pairwise axis); re-stack the per-query `feats`
            # and confirm the embedder-relevant shapes survive _stack_price's
            # 3D->2D reshape (mirrors llm_price_or_collate).
            collate_items = [(pf, 1.0, pm, njc, nfo, ntb, nfc, nc, 0.0)
                             for (pf, pm, njc, nfo, ntb, nfc, nc) in feats[:4]]
            pf_, pgc_, pm_, njc_, nfo_, ntb_, nfc_, nc_, _lab = zip(*collate_items)
            ref_pf = torch.stack([f for f in pf_]).float()
            ref_pm = torch.stack([m for m in pm_]).float()
            ref_njc = torch.tensor(njc_, dtype=torch.float32).unsqueeze(1)
            ref_nfc = torch.tensor(nfc_, dtype=torch.float32).unsqueeze(1)
            if ref_pf.dim() == 3:
                b_, c_, f_ = ref_pf.shape
                ref_pf_cmp = ref_pf.view(b_ * c_, f_)
                ref_pm_cmp = ref_pm.view(b_ * c_, ref_pm.shape[-1])
            else:
                ref_pf_cmp, ref_pm_cmp = ref_pf, ref_pm
            ok = (price_batch[0].shape == ref_pf_cmp.shape and
                  price_batch[1].shape == ref_pm_cmp.shape and
                  price_batch[2].shape == ref_njc.shape and
                  price_batch[5].shape == ref_nfc.shape)
            print(f"[verify] shapes match mode-7 collate "
                  f"(price_feats/pad_masks/njc/nfc): {ok}")
            assert ok, "price_batch shapes diverge from mode-7 collate!"

    print("\n[verify] OK — price_batch is interchangeable with mode-7's PRICEEmbedder input.")
