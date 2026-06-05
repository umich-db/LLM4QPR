"""Build mode-7's cx=0 PRICEEmbedder. Extracted from train.py so the LLM path
and the baselines (--baseline_price_concat) construct the identical embedder."""
import os
import sys

import torch

# train.py runs from the experiments/ dir and adds ../PRICE (or /root/PRICE) to
# sys.path so that `from model.encoder import RegressionModel` resolves. Replicate
# that path setup here so this module can be imported/used from either the LLM
# path or the baseline path without depending on train.py's import-time side
# effects (importing train.py would run the whole training script).
_experiments_dir = os.path.dirname(os.path.abspath(__file__))
if _experiments_dir not in sys.path:
    sys.path.insert(0, _experiments_dir)
_local_price = os.path.join(_experiments_dir, "..", "PRICE")
_price_root = _local_price if os.path.isdir(os.path.join(_local_price, "setup")) else "/root/PRICE"
if _price_root not in sys.path:
    sys.path.insert(0, _price_root)

from model.encoder import RegressionModel
from models.llm_price_model import PRICEEmbedder


def _price_dims(argsP, bin_size):
    """Return (filter_dim, fanout_dim, pairwise_intra_dim) per active flags.

    NOTE: Sql2FeatureN always emits 75-dim filter and 42-dim fanout tokens
    regardless of which PRICE_N sub-flag is set. So if any PRICE_N flag is
    on, both dims must use Sql2FeatureN's shape — the sub-flags only gate
    which atoms are populated, not the token shape.

    (Copy of train.py:_price_dims, kept here to avoid importing train.py — which
    runs the whole training script at import time. Must stay logic-identical.)
    """
    use_price_n = any([
        getattr(argsP, "price_n_filter", False),
        getattr(argsP, "price_n_fanout", False),
        getattr(argsP, "price_n_pairwise", False),
        getattr(argsP, "price_n_parsing", False),
    ])
    if use_price_n:
        filter_dim = bin_size + 3 * 11 + 2          # 75
        fanout_dim = bin_size + 2                   # 42
    elif getattr(argsP, "price_m", False):
        filter_dim = bin_size + 21                  # 61
        fanout_dim = bin_size                       # 40
    else:
        filter_dim = bin_size + 3                   # 43 (PRICE_S or base PRICE)
        fanout_dim = bin_size                       # 40

    pairwise_intra_dim = (64 + 2 * 3) if getattr(argsP, "price_n_pairwise", False) else 0   # 70
    return filter_dim, fanout_dim, pairwise_intra_dim


def _price_path_suffix(argsP):
    """PRICE-mode suffix: priceB / priceS / priceM / priceN_*, plus DNF flags.

    (Copy of train.py:_price_path_suffix, kept here to avoid importing train.py.
    Must stay logic-identical.)
    """
    parts = []
    if getattr(argsP, 'price_b', False):           parts.append("priceB")
    if getattr(argsP, 'price_s', False):           parts.append("priceS")
    if getattr(argsP, 'price_m', False):           parts.append("priceM")
    # PRICE_N sub-flags: collapse to a single "priceN" token when all four are
    # set (the common case after the --price_n shorthand) — keeps filenames
    # under the ext4 255-byte limit. Otherwise emit only the active subset.
    _pn = (getattr(argsP, 'price_n_filter', False),
           getattr(argsP, 'price_n_fanout', False),
           getattr(argsP, 'price_n_pairwise', False),
           getattr(argsP, 'price_n_parsing', False))
    if all(_pn):
        parts.append("priceN")
    else:
        if _pn[0]: parts.append("priceNflt")
        if _pn[1]: parts.append("priceNfan")
        if _pn[2]: parts.append("priceNpw")
        if _pn[3]: parts.append("priceNprs")
    if getattr(argsP, 'price_n_or', False):        parts.append("priceNor")
    # Default for max_clauses is 16 — only emit if non-default
    mc = getattr(argsP, 'price_n_or_max_clauses', 16)
    if mc != 16:
        parts.append(f"mc{mc}")
    return ("_" + "_".join(parts)) if parts else ""


def build_price_embedder(argsP, device, return_price_model=False):
    """Return (price_embedder, price_output_dim). cx=0 -> price_output_dim == 512
    (or argsP.price_output_dim override). Reuses --price_model_path /
    --price_bin_size / --price_n* / --price_random_init exactly like mode 7.

    With return_price_model=True, returns (price_embedder, price_output_dim,
    price_model) instead. train.py's llm_price_finetune block needs the same
    RegressionModel instance to seed its cross-attn embedders, so it uses this
    form; the byte-identical (price_model, price_embedder) pair it gets is the
    same one the original inline code produced."""
    # Global subdir component: inserted into every finetuned_models/{db}/<_GSUB>/... path
    # when --subdir_tag is set (e.g. "model_selection"). Empty string otherwise.
    _GSUB = f"/{argsP.subdir_tag}" if getattr(argsP, 'subdir_tag', '') else ""

    # Load pretrained PRICE model (skip if random init)
    price_state_dict = None
    if not getattr(argsP, 'price_random_init', False):
      price_state_dict = torch.load(argsP.price_model_path, map_location=device)
      # Strip DataParallel 'module.' prefix
      price_state_dict = {k.replace('module.', ''): v for k, v in price_state_dict.items()}

    # Build PRICE RegressionModel with correct dimensions
    max_njc = argsP.price_max_n_join_col
    max_nfo = argsP.price_max_n_fanout
    max_ntb = argsP.price_max_n_table
    max_nfc = argsP.price_max_n_filter_col
    bin_size = getattr(argsP, 'price_bin_size', 40)
    table_dim = 4
    filter_dim, fanout_dim, pairwise_intra_dim = _price_dims(argsP, bin_size)

    _price_n_embd = getattr(argsP, 'price_n_embd', 256)
    _price_n_heads = getattr(argsP, 'price_n_heads', 8)
    _price_ffn_ratio = getattr(argsP, 'price_ffn_ratio', 4.0)
    _use_or_transformer = any([
        getattr(argsP, "price_n_pairwise", False),
        getattr(argsP, "price_n_filter", False),
        getattr(argsP, "price_n_fanout", False),
        getattr(argsP, "price_n_parsing", False),
    ]) and not getattr(argsP, "no_or_transformer", False)
    # Pick query_hidden_dim so PRICEEmbedder can always reuse regression_model.linear
    # (no spurious nn.Linear in PRICEEmbedder.__init__, which would shift RNG state).
    _pod = int(getattr(argsP, 'price_output_dim', 0) or 0)
    if _pod > 0:
        _query_hidden_dim = _pod
    elif (getattr(argsP, 'use_bi_cross_attention', False)
          and getattr(argsP, 'inflate_price', False)
          and (getattr(argsP, 'n_cross_layers', 0) > 0 or getattr(argsP, 'force_inflate', False))):
        _query_hidden_dim = argsP.embed_size
    else:
        _query_hidden_dim = 512
    price_model = RegressionModel(
        n_join_col=max_njc, n_fanout=max_nfo, n_table=max_ntb, n_filter_col=max_nfc,
        n_pairwise_intra=getattr(argsP, "price_max_n_pairwise_intra", 8)
                          if getattr(argsP, "price_n_pairwise", False) else 0,
        hist_dim=bin_size, table_dim=table_dim, filter_dim=filter_dim,
        fanout_dim=fanout_dim, pairwise_intra_dim=pairwise_intra_dim,
        query_hidden_dim=_query_hidden_dim, final_hidden_dim=1024, output_dim=1,
        n_embd=_price_n_embd, n_layers=getattr(argsP, 'price_n_layers', 6), n_heads=_price_n_heads,
        dropout_rate=0.1, ffn_ratio=_price_ffn_ratio,
        use_or_transformer=_use_or_transformer,
        or_n_layers=getattr(argsP, "or_n_layers", 1),
        or_n_heads=getattr(argsP, "or_n_heads", 4),
        or_ffn_ratio=getattr(argsP, "or_ffn_ratio", 1.0),
    )
    # Load weights with partial init for PRICE_M (histogram bins shared, operator dims differ)
    def _load_price_sd(model, ckpt_sd, label=""):
        """Load checkpoint into PRICE model with partial init for size-mismatched weights.
        For filter_embeddings.weight [n_embd,43]->[n_embd,61], copies the first min(43,61)
        columns (histogram bins) and leaves the rest randomly initialized."""
        model_sd = model.state_dict()
        for k, v in ckpt_sd.items():
            if k not in model_sd:
                continue
            if model_sd[k].shape == v.shape:
                model_sd[k] = v
            elif model_sd[k].dim() == v.dim():
                slices = tuple(slice(0, min(ms, vs)) for ms, vs in zip(model_sd[k].shape, v.shape))
                model_sd[k][slices] = v[slices]
                print(f"  Partial init {k}: copied {[s.stop for s in slices]} of {list(model_sd[k].shape)} from checkpoint {list(v.shape)}")
        model.load_state_dict(model_sd)
        if label:
            print(label)

    if getattr(argsP, 'price_random_init', False):
      print("[PRICE] Random initialization (skipping pretrained weights)")
    elif getattr(argsP, 'price_init_frozen_joint', False):
      # Load frozen-joint PRICE weights instead of pretrained
      task_str = "card" if argsP.card else "time"
      _price_suffix = _price_path_suffix(argsP)
      frozen_price_path = f"finetuned_models/{argsP.db}{_GSUB}/{argsP.canonical_wl_prefix}_{task_str}_inference_{argsP.model_name.replace('/','-')}_b{argsP.batch_size}{_price_suffix}_llm_price_price.pt"
      frozen_sd = torch.load(frozen_price_path, map_location=device)
      _load_price_sd(price_model, frozen_sd, f"Loaded frozen-joint PRICE weights from {frozen_price_path}")
    else:
      _load_price_sd(price_model, price_state_dict, f"Loaded PRICE weights from {argsP.price_model_path}")

    price_embedder = PRICEEmbedder(price_model,
                                   price_output_dim_override=getattr(argsP, 'price_output_dim', 0))
    price_embedder.to(device)
    price_output_dim = getattr(price_embedder, 'price_output_dim', 512)
    if return_price_model:
        return price_embedder, price_output_dim, price_model
    return price_embedder, price_output_dim
