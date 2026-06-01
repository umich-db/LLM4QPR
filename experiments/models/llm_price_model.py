"""
Joint LLM + PRICE model for query cost/cardinality prediction.

Architecture:
  Query Plan Text --> LLM (LoRA) --> D_llm embedding --+
                                                        +--> Concat --> MLP --> Prediction
  SQL + Stats ------> PRICE (full) --> 512-dim embedding-+
"""

import os
import sys
import torch
import torch.nn as nn
import torch.nn.functional as F

PRICE_ROOT = "/root/PRICE"
if PRICE_ROOT not in sys.path:
    sys.path.insert(0, PRICE_ROOT)


def _segment_mean(rows, win_owner, B):
    """Mean of rows [Nw, D] grouped by win_owner [Nw] (text id per window) → [B, D].
    Used by the unified per-window pooling: averages each text's window rows. Equals
    a plain .mean() over each text's windows (index_add_ visits win_owner in its given
    non-decreasing order)."""
    D = rows.size(1)
    sums = torch.zeros(B, D, device=rows.device, dtype=rows.dtype)
    sums.index_add_(0, win_owner, rows)
    counts = torch.zeros(B, device=rows.device, dtype=rows.dtype)
    counts.index_add_(0, win_owner, torch.ones(win_owner.size(0), device=rows.device, dtype=rows.dtype))
    return sums / counts.clamp(min=1).unsqueeze(1)


def _load_price_n_state_dict(model, ckpt_sd):
    """Load a PRICE pretrained state dict into a PRICE_N-shaped RegressionModel.

    Performs:
      1. Best-effort load_state_dict(strict=False) for matching keys.
         Keys with shape mismatches are excluded from this call to avoid
         RuntimeError (PyTorch 2.7+ raises even under strict=False for shape
         mismatches on the same key).
      2. Partial-copy of filter_embedding.weight[:, :ckpt_dim] when target is wider.
      3. Partial-copy of fanout_embeddings.weight[:, :ckpt_dim] when target is wider.
      4. type_embed first 4 rows copied if target has 5.
      5. pairwise_intra_embedding fully random-init (no copy).

    Returns a dict {loaded, partial_copied, missing} for logging.
    """
    summary = {"loaded": [], "partial_copied": [], "missing": []}
    target_sd = model.state_dict()

    # Build a filtered checkpoint that only contains keys whose shapes match
    # the target model — load_state_dict(strict=False) in PyTorch 2.7 still
    # raises RuntimeError for shape mismatches, so we exclude them here and
    # handle them manually in the partial-copy step below.
    shape_matched = {
        k: v for k, v in ckpt_sd.items()
        if k in target_sd and v.shape == target_sd[k].shape
    }
    shape_mismatched = {k for k in ckpt_sd if k in target_sd and ckpt_sd[k].shape != target_sd[k].shape}

    # Step 1: load matching shapes with strict=False (handles truly missing keys gracefully)
    missing, unexpected = model.load_state_dict(shape_matched, strict=False)
    summary["loaded"] = list(shape_matched.keys())

    # Step 2 + 3: partial-copy mismatched 2-D Linear weights/biases.
    for key in [
        "filter_embedding.filter_embeddings.weight",
        "filter_embedding.filter_embeddings.bias",
        "scale_embedding.fanout_embeddings.weight",
        "scale_embedding.fanout_embeddings.bias",
    ]:
        if key not in ckpt_sd or key not in target_sd:
            continue
        src = ckpt_sd[key]
        tgt = target_sd[key]
        if src.shape == tgt.shape:
            continue                          # already loaded by strict=False
        if src.dim() == 2 and src.shape[0] == tgt.shape[0] and src.shape[1] < tgt.shape[1]:
            with torch.no_grad():
                tgt.zero_()
                tgt[:, :src.shape[1]].copy_(src)
            summary["partial_copied"].append(key)
        elif src.dim() == 1 and src.shape[0] <= tgt.shape[0]:
            with torch.no_grad():
                tgt.zero_()
                tgt[:src.shape[0]].copy_(src)
            summary["partial_copied"].append(key)

    summary["missing"] = list(missing)
    return summary


class PRICEEmbedder(nn.Module):
    """
    Mode 7's PRICE embedder, optionally enriched with cross-attention.

    Base pipeline (always runs):
      scale_emb -> filter_emb -> CLS(256) -> +len(16) -> linear(272→512) -> ELU -> dropout

    With n_cross_layers > 0:
      Adds an inflate Linear(512 -> llm_hidden_dim) and N cross-attention blocks.
      The PRICE summary is treated as a length-1 token sequence; LLM tokens
      cross-attend to it (and vice versa for odd-indexed blocks).

    Returns:
      (price_emb, updated_llm, llm_attention_mask)
        - price_emb: [B, query_hidden_dim] at cx=0, [B, llm_hidden_dim] at cx>0
        - updated_llm: None at cx=0; cross-attn-refined LLM tokens when cx>0 has odd blocks
        - llm_attention_mask: passed through (None at cx=0)
    """

    def __init__(self, regression_model, n_cross_layers=0, llm_hidden_dim=None,
                 n_heads=8, dropout_rate=0.1, cross_attn_noop=False, force_inflate=False,
                 price_output_dim_override=0, zero_init_all_blocks=False,
                 zero_init_even_blocks=False, defer_cross_attn=False,
                 unified_window_pool=False):
        super().__init__()
        self.cross_attn_noop = bool(cross_attn_noop)
        self.force_inflate = bool(force_inflate)
        # Unified per-window cross-attn pooling: PRICE token cross-attends each
        # sliding window separately, then segment-mean over the text's windows
        # (pooled_emb is the cx=0 special case). Set from --unified_window_pool.
        self.unified_window_pool = bool(unified_window_pool)
        self.price_output_dim_override = int(price_output_dim_override)
        self.n_join_col = regression_model.n_join_col
        self.n_fanout = regression_model.n_fanout
        self.n_table = regression_model.n_table
        self.n_filter_col = regression_model.n_filter_col
        self.hist_dim = regression_model.hist_dim
        self.table_dim = regression_model.table_dim
        self.dropout_rate = regression_model.dropout_rate

        # Mode-7-shared layers (scale/filter encoders, len_net, elu).
        self.scale_embedding = regression_model.scale_embedding
        self.filter_embedding = regression_model.filter_embedding
        self.scale_encoder = regression_model.scale_encoder
        self.filter_encoder = regression_model.filter_encoder
        self.len_net = regression_model.len_net
        self.elu = regression_model.elu
        # OR-Transformer: aggregates per-AND-clause CLS tokens for multi-clause DNF.
        # Constructed by RegressionModel when any PRICE_N flag is on (`use_or_transformer=True`),
        # left as None otherwise. PRICEEmbedder.forward calls it when `num_clauses` is provided
        # (i.e., the dataset emitted per-clause features under --price_n_or). For K=1
        # (single-clause), the OR-Transformer runs degenerately on a length-1 sequence.
        self.or_transformer = getattr(regression_model, 'or_transformer', None)

        self.n_cross_layers = int(n_cross_layers)
        # Always reuse regression_model.linear — never create a new nn.Linear here.
        # Output dim (272 → query_hidden_dim) is configured at RegressionModel
        # construction time in train.py, based on --price_output_dim / force_inflate
        # / cross-attn flags. This keeps the PRICEEmbedder.__init__ deterministic in
        # RNG consumption regardless of dim/architecture choice.
        self.linear = regression_model.linear
        self.inflate = None
        self.price_output_dim = self.linear.out_features
        if self.n_cross_layers > 0:
            # cx>0: cross-attn blocks require PRICE token at LLM hidden dim
            assert llm_hidden_dim is not None, "llm_hidden_dim required for cross-attn"
            assert self.price_output_dim == llm_hidden_dim, (
                f"With cx>0, price_output_dim ({self.price_output_dim}) must equal "
                f"llm_hidden_dim ({llm_hidden_dim}); set --price_output_dim or use the "
                f"force_inflate-driven path so RegressionModel is built with matching dim."
            )

        # Cross-attn block config is stashed so construction can be DEFERRED until
        # after the joint MLP is built (--mlp_before_cross_attn / defer_cross_attn).
        # Building the N blocks (~28M params) advances the global torch RNG; deferring
        # keeps the MLP's random init independent of the cross-attn block count, so
        # mode-7 (cx0) and mode-12 (cxN) get the SAME MLP init for a clean comparison.
        self._ca_llm_hidden_dim = llm_hidden_dim
        self._ca_n_heads = n_heads
        self._ca_dropout = dropout_rate
        self._ca_zero_all = bool(zero_init_all_blocks)
        self._ca_zero_even = bool(zero_init_even_blocks)
        self.cross_attn_blocks = nn.ModuleList([])
        self._cross_attn_deferred = bool(defer_cross_attn) and self.n_cross_layers > 0
        if self.n_cross_layers > 0 and not self._cross_attn_deferred:
            self._build_cross_attn_blocks()

    def _build_cross_attn_blocks(self):
        """Construct (and zero-init) the N cross-attn blocks. Separated from
        __init__ so it can be deferred until AFTER the joint MLP is built."""
        self.cross_attn_blocks = nn.ModuleList([
            ReverseCrossAttentionBlock(self._ca_llm_hidden_dim, self._ca_n_heads,
                                       self._ca_dropout, use_gate=False)
            for _ in range(self.n_cross_layers)
        ])
        for i, block in enumerate(self.cross_attn_blocks):
            # Default: only odd blocks (LLM←PRICE) are zero-initialised; even
            # blocks (PRICE←LLM) start normally so PRICE immediately reads LLM.
            # zero_init_all_blocks=True: also zero-init the even-block residual
            # injection (paired with --freeze_all_blocks_until_epoch → identity blocks).
            if i % 2 == 1 or self._ca_zero_all or (i % 2 == 0 and self._ca_zero_even):
                nn.init.zeros_(block.cross_attn.projection.weight)
                nn.init.zeros_(block.cross_attn.projection.bias)
                nn.init.zeros_(block.feed_forward[-1].weight)
                nn.init.zeros_(block.feed_forward[-1].bias)
        self._cross_attn_deferred = False

    def maybe_build_deferred_cross_attn(self):
        """Build deferred cross-attn blocks (no-op if not deferred / already built).
        Called by LLMPriceJointModel.__init__ AFTER the MLP so the MLP's random init
        is independent of cross-attn block count (init-matched mode-7 vs mode-12)."""
        if getattr(self, '_cross_attn_deferred', False):
            self._build_cross_attn_blocks()

    def forward(self, x, padding_mask, n_join_col, n_fanout, n_table, n_filter_col,
                llm_hidden_states=None, llm_attention_mask=None, num_clauses=None,
                qrt_block=None, r_qry=None, r_mask=None, per_window=None):
        # Mode 7's pipeline (always). When num_clauses is provided, x has shape
        # (batch * max_clauses, flat_features); we run scale+filter per clause,
        # then OR-Transformer aggregates the per-clause CLS tokens into a single
        # query-level embedding. When num_clauses is None, behavior is unchanged
        # (single-clause path, OR-Transformer not invoked).
        scale_features = self.scale_embedding(x)
        masks1 = padding_mask[:, :1 + self.n_join_col + self.n_fanout] if padding_mask is not None else None
        scaling_output = self.scale_encoder(scale_features, masks1)
        filter_features = self.filter_embedding(scaling_output, x)
        masks2 = padding_mask[:, :] if padding_mask is not None else None
        filtering_output = self.filter_encoder(filter_features, masks2)
        per_clause_emb = filtering_output[:, 0, :]

        if num_clauses is not None and self.or_transformer is not None:
            # Multi-clause: reshape to (batch, max_clauses, n_embd), build clause
            # padding mask, run OR-Transformer, take CLS-only output.
            bsz = num_clauses.size(0)
            # max_c is the GLOBAL padding count baked into the input tensor by
            # pad_and_cache_features, NOT the batch-local max of num_clauses.
            # Using num_clauses.max() here was a bug: when the dataset was
            # padded to a larger global max (e.g. 16 clauses for tpch q18) but
            # the current batch happened to contain only short queries (max
            # 2 clauses), reshape(bsz, batch_max, -1) smeared the extra rows
            # into the last dim (256 * 8 = 2048 instead of 256), surfacing as
            # "Expected size 256 but got 2048" inside the OR-Transformer's
            # torch.cat([cls, clause_embs]).
            max_c = per_clause_emb.size(0) // bsz
            # `.reshape` instead of `.view`: per_clause_emb is a slice of
            # filtering_output and may be non-contiguous (seen on tpch under
            # --price_n_or where filter_encoder returns non-contiguous output
            # due to attention's permutation pattern). .reshape() copies when
            # needed; .view() would raise the "view size is not compatible
            # with input tensor's size and stride" error.
            per_clause_emb = per_clause_emb.reshape(bsz, max_c, -1)
            clause_mask = (
                torch.arange(max_c, device=per_clause_emb.device).unsqueeze(0)
                >= num_clauses.unsqueeze(1)   # True where padded
            )
            query_output = self.or_transformer(per_clause_emb, clause_mask)
        else:
            query_output = per_clause_emb

        len_features = torch.cat([n_join_col, n_fanout, n_table, n_filter_col], dim=1)
        len_features = self.len_net(len_features)

        query_output = self.linear(torch.cat([query_output, len_features], dim=1))
        query_output = self.elu(query_output)
        query_output = F.dropout(query_output, p=self.dropout_rate, training=self.training)

        # query_output is already at the right dim:
        #   - cx=0 (no force_inflate): 512-d (mode 7's query_hidden_dim)
        #   - cx>0 OR force_inflate: llm_hidden_dim (direct projection in self.linear)
        # --use_qrt_cross_attn: enrich stat_core with Query Residual Tokens
        # BEFORE biCross runs. qrt_block projects D_stat→D_llm and returns the
        # refined [B, 1, D_llm] CLS, so biCross input shape stays the same.
        if qrt_block is not None:
            assert r_qry is not None, "qrt_block provided but r_qry is None"
            stat = query_output.unsqueeze(1)              # [B, 1, D_stat]
            refined = qrt_block(stat, r_qry, r_mask)      # [B, 1, D_llm]
            query_output = refined.squeeze(1)             # [B, D_llm]

        if self.n_cross_layers == 0:
            return query_output, None, None

        # cx>0: query_output is at LLM dim; treat as length-1 token for cross-attn
        price_tokens = query_output.unsqueeze(1)   # [B, 1, llm_hidden_dim]
        price_mask = torch.ones(price_tokens.size(0), 1, device=price_tokens.device, dtype=torch.long)

        # UNIFIED per-window cross-attn: the PRICE token cross-attends EACH sliding
        # window separately (batched over windows), then we segment-mean over each
        # text's windows. pooled_emb is the cx=0 special case (identity blocks →
        # refined CLS == raw per-window CLS → normalize+mean == today's pooled_emb;
        # refined PRICE == query_output → mean == today's price_output). The returned
        # "updated_llm" is the already-pooled [B,D] llm_emb (dim==2) — _select_llm_emb
        # detects that and uses it directly. per_window = (all_hs, all_masks, win_owner, B).
        if self.unified_window_pool and per_window is not None:
            all_hs, all_masks, win_owner, B = per_window
            price_w = price_tokens[win_owner]                 # [Nw, 1, D]
            if self.cross_attn_noop:
                refined_cls_w = all_hs[:, 0, :].float()
                refined_price_w = price_w[:, 0, :]
            else:
                llm_w = all_hs.float()                        # [Nw, T_pad, D]
                pmask_w = torch.ones(price_w.size(0), 1, device=price_w.device, dtype=torch.long)
                for i, block in enumerate(self.cross_attn_blocks):
                    if i % 2 == 0:   # PRICE(Q, this window's copy) attends to its window's LLM K/V
                        price_w = block(price_w, llm_w, all_masks)
                    else:            # this window's LLM tokens attend to its PRICE copy
                        llm_w = block(llm_w, price_w, pmask_w)
                refined_cls_w = llm_w[:, 0, :]                # [Nw, D]
                refined_price_w = price_w[:, 0, :]            # [Nw, D]
            # llm half: F.normalize per window (matches BERT pooled = F.normalize(CLS))
            # BEFORE the mean, so cx=0 reduces to all_pooled[win].mean == pooled_emb.
            llm_emb = _segment_mean(F.normalize(refined_cls_w, p=2, dim=1), win_owner, B)
            # price half: NOT normalized (today's price_output is unnormalized).
            price_emb = _segment_mean(refined_price_w, win_owner, B)
            return price_emb, llm_emb, None

        updated_llm = None
        any_llm_cross_attn = False
        if llm_hidden_states is not None and not self.cross_attn_noop:
            llm_tokens = llm_hidden_states.float()
            for i, block in enumerate(self.cross_attn_blocks):
                if i % 2 == 0:
                    # PRICE (Q) attends to LLM (K/V)
                    price_tokens = block(price_tokens, llm_tokens, llm_attention_mask)
                else:
                    # LLM (Q) attends to PRICE (K/V, length 1)
                    llm_tokens = block(llm_tokens, price_tokens, price_mask)
                    any_llm_cross_attn = True
            if any_llm_cross_attn:
                updated_llm = llm_tokens
        # cross_attn_noop: cross_attn_blocks are CONSTRUCTED (so optimizer sees
        # the params) but their forward is skipped. price_tokens stays at the
        # initial inflate(price_emb_512), updated_llm stays None. This is
        # architecturally equivalent to cx=0 — useful to confirm that the
        # cx>0 code path itself is bug-free (any divergence from cx=0 baseline
        # would come from the cross-attn blocks, not surrounding glue code).

        price_output = price_tokens[:, 0, :]
        return price_output, updated_llm, llm_attention_mask

    def cross_attn_parameters(self):
        if self.inflate is not None:
            yield from self.inflate.parameters()
        yield from self.cross_attn_blocks.parameters()

    def odd_layer_parameters(self):
        """Parameters of odd-indexed cross-attn blocks (i.e. the LLM←PRICE
        direction). These have their output projection + last FF zero-initialised
        on construction (lines 152-157); freezing them keeps the LLM tokens
        strictly unchanged through every odd block during the freeze window,
        as opposed to the default "soft warmup via zero-init" where the residual
        injection learns to grow from 0. Used by trainer.py's staged-unfreeze
        path when --freeze_odd_blocks_until_epoch > 0."""
        for i, block in enumerate(self.cross_attn_blocks):
            if i % 2 == 1:
                yield from block.parameters()

    def even_layer_parameters(self):
        """Parameters of even-indexed cross-attn blocks (the PRICE←LLM direction,
        i.e. PRICE attends to LLM). Mirror of odd_layer_parameters(). Paired with
        zero_init_even_blocks=True at construction, freezing them keeps the PRICE
        token strictly unchanged by the LLM during the freeze window, so only the
        LLM←PRICE (odd) direction is active. Used by trainer.py's staged-unfreeze
        path when --freeze_even_blocks_until_epoch > 0."""
        for i, block in enumerate(self.cross_attn_blocks):
            if i % 2 == 0:
                yield from block.parameters()

    def price_core_parameters(self):
        cross_attn_ids = {id(p) for p in self.cross_attn_parameters()}
        for p in self.parameters():
            if id(p) not in cross_attn_ids:
                yield p


class LLMPriceJointModel(nn.Module):
    """
    Joint model: LLM embeddings + PRICE embeddings --> MLP --> prediction.

    The forward method receives a tuple:
      (texts, price_features, padding_mask, n_join_col, n_fanout, n_table, n_filter_col)
    """

    def __init__(self, llm, price_embedder, llm_embed_size, price_embed_size, hid_units,
                 residual_pred=False, delta_bound=0.0, use_qrt_cross_attn=False,
                 qrt_max_tokens=128):
        """
        Args:
            llm: QueryPlanPredictor (with LoRA) that takes text and returns embeddings
            price_embedder: PRICEEmbedder instance (may have cross-attn enabled)
            llm_embed_size: LLM hidden dim
            price_embed_size: legacy default; ignored if price_embedder.price_output_dim is set
            hid_units: MLP hidden dimension
            residual_pred: ResNet-style bypass for cross-attn. When True:
                pred = sigmoid( base_mlp(pooled_emb) + delta_mlp(concat(llm_emb, price_emb)) )
                where pooled_emb is the PRE-cross-attn LLM output (pure LLM)
                and concat(...) is the POST-cross-attn fused embedding. The
                delta head's final layer (out_mlp2) is zero-init, so at step 0
                delta_logit = 0 and the joint model's prediction is *exactly*
                base_mlp(pooled_emb) — i.e., LLM-only. Training opens up the
                delta only if cross-attn helps; if it never helps, gradients
                through cross-attn vanish and the model degrades to pure LLM.
            delta_bound: Bound the residual delta_logit via
                delta_logit ← tanh(delta_logit) * delta_bound. 0 = unbounded.
                Caps how much the cross-attn branch can perturb the LLM-only
                prediction.
            use_qrt_cross_attn: enable Stat-core ↔ QRT bidirectional cross-attn
                before the Plan↔Query (biCross) block. When True, the model
                tokenizes the per-sample residual SQL text via self.llm.tokenizer,
                embeds via self.llm.model.get_input_embeddings(), and runs a
                single Transformer-style self-attention layer over
                [stat_proj || r_qry], returning only the refined stat_core CLS
                at D_llm. The biCross input shape (and downstream price_emb dim
                = D_llm) is preserved. For cx=0 (Mode 7) this changes the
                returned price_emb dim from D_stat to D_llm, so combined_dim
                in the MLP grows to 2*D_llm.
            qrt_max_tokens: max tokenizer length for residual texts.
        """
        super().__init__()
        self.llm = llm
        self.price = price_embedder
        # Read PRICE output dim from embedder; fall back to legacy arg.
        _pod = getattr(price_embedder, 'price_output_dim', price_embed_size)
        # When --use_qrt_cross_attn is on, QRT projects price_emb to D_llm.
        # The cx>0 path is already at D_llm; cx=0 path goes D_stat → D_llm.
        self.use_qrt_cross_attn = bool(use_qrt_cross_attn)
        self.qrt_max_tokens = int(qrt_max_tokens)
        if self.use_qrt_cross_attn:
            self.stat_qrt = StatQrtCrossAttn(
                d_stat=_pod, d_llm=llm_embed_size,
                n_heads=4, dropout_rate=0.1,
            )
            effective_price_dim = llm_embed_size
        else:
            self.stat_qrt = None
            effective_price_dim = _pod
        combined_dim = llm_embed_size + effective_price_dim
        from trainer import Prediction
        self.residual_pred = bool(residual_pred)
        self.delta_bound = float(delta_bound)
        if self.residual_pred:
            # delta head returns pre-sigmoid logit; out_mlp2 zero-init so
            # delta_logit = 0 at step 0.
            self.mlp = Prediction(combined_dim, hid_units, no_sigmoid=True)
            self.base_mlp = Prediction(llm_embed_size, hid_units, no_sigmoid=True)
            nn.init.zeros_(self.mlp.out_mlp2.weight)
            nn.init.zeros_(self.mlp.out_mlp2.bias)
        else:
            self.mlp = Prediction(combined_dim, hid_units)
        # Build deferred cross-attn blocks (when --mlp_before_cross_attn): the MLP
        # above is now constructed BEFORE the blocks, so its random init is
        # independent of the cross-attn block count (init-matched mode-7 vs mode-12).
        # No-op for the default (eager) construction.
        if hasattr(self.price, 'maybe_build_deferred_cross_attn'):
            self.price.maybe_build_deferred_cross_attn()
        # Convenience flag: does the embedder do cross-attention (need LLM hidden states)?
        self.uses_cross_attn = getattr(price_embedder, 'n_cross_layers', 0) > 0

    def _embed_residual_texts(self, residual_texts, device):
        """Tokenize residual SQL fragments and embed them via the LLM's input
        embedding layer. Returns (r_qry, r_mask) at LLM hidden dim, or (None, None)
        when use_qrt_cross_attn is off or residual_texts is missing/all-empty."""
        if not self.use_qrt_cross_attn or residual_texts is None:
            return None, None
        # Use a non-empty placeholder for blank residuals so the tokenizer
        # never produces zero-length sequences (would break stacking and the
        # cross-attn op). Single pad token suffices — its mask will mark it
        # as a real (but information-less) token.
        pad_tok = self.llm.tokenizer.pad_token or self.llm.tokenizer.eos_token or " "
        texts = [t if (t and t.strip()) else pad_tok for t in residual_texts]
        enc = self.llm.tokenizer(
            texts, return_tensors="pt", padding=True, truncation=True,
            max_length=self.qrt_max_tokens, add_special_tokens=False,
        )
        input_ids = enc["input_ids"].to(device)
        attn_mask = enc["attention_mask"].to(device)
        embed_layer = self.llm.model.get_input_embeddings()
        r_qry = embed_layer(input_ids).float()
        return r_qry, attn_mask.float()

    def _select_llm_emb(self, pooled_emb, updated_llm):
        """LLM half fed to the joint MLP. Shared by forward() and forward_embeddings()
        so both stay consistent.

        Legacy cross-attn behaviour (updated_llm is not None) used window-0's CLS only
        — `F.normalize(updated_llm[:,0,:])` — which TRUNCATES multi-window (long) plans
        to their first ~512 tokens, whereas the cx=0 path mean-pools ALL windows
        (utilsLLM._process_with_sliding_window_batch). That systematic truncation made
        the cross-attn path strictly information-poorer on long-plan workloads.

        With LLM_POOL_ALL_WINDOWS=1 the cross-attn path reuses the already-computed
        mean-over-windows `pooled_emb` (byte-identical to the cx=0 LLM half), so no plan
        content is discarded. NOTE: for ACTIVE cross-attn this means the LLM-side
        (odd-block) refinement no longer reaches llm_emb — a follow-up would mean-pool
        the *refined* updated_llm across windows; for frozen/identity blocks the two are
        the same and cx4 becomes exactly cx0.

        --unified_window_pool (the principled version) does that refined-and-meaned
        aggregation inside PRICEEmbedder.forward and returns the already-pooled [B,D]
        llm_emb as `updated_llm` (dim==2) — detected here and used directly."""
        if updated_llm is None:
            return pooled_emb
        if updated_llm.dim() == 2:
            # unified per-window path already returns the segment-mean-pooled [B,D] llm_emb
            return updated_llm
        if os.environ.get('LLM_POOL_ALL_WINDOWS') == '1':
            return pooled_emb
        return F.normalize(updated_llm[:, 0, :], p=2, dim=1)

    def _llm_forward(self, texts):
        """Run the LLM. Returns (pooled_emb, hidden_states, attn_mask, per_window).
        Shared by forward() and forward_embeddings() so they stay consistent.
        - unified per-window: per_window=(all_hs, all_masks, win_owner, B); pooled_emb =
          segment-mean of per-window pooled (== legacy pooled_emb, for the residual base).
        - legacy cross-attn: stitched hidden_states/attn_mask (per_window=None).
        - cx=0 / mode-7: cheap pooled forward."""
        if self.uses_cross_attn and getattr(self.price, 'unified_window_pool', False):
            all_pooled, all_hs, all_masks, win_owner, B = self.llm.forward_per_window(texts)
            pooled_emb = _segment_mean(all_pooled, win_owner, B)
            return pooled_emb, None, None, (all_hs, all_masks, win_owner, B)
        if self.uses_cross_attn:
            pooled_emb, hidden_states, attn_mask = self.llm.forward_with_sequence(texts)
            return pooled_emb, hidden_states, attn_mask, None
        return self.llm(texts), None, None, None

    def forward(self, x):
        # Unpack. The collate emits, in order:
        #   base 7-tuple (texts, pf, pm, njc, nfo, ntb, nfc),
        #   + optional num_clauses (under --price_n_or),
        #   + optional residual_texts (under --use_qrt_cross_attn).
        # We detect each optional tail element by type so the unpack stays
        # backward-compatible with the legacy 7/8-tuples.
        residual_texts = None
        num_clauses = None
        x = list(x)
        # residual_texts (list[str]) is always last when present.
        if len(x) > 7 and isinstance(x[-1], (list, tuple)) and (
            len(x[-1]) == 0 or isinstance(x[-1][0], str)
        ):
            residual_texts = x.pop()
        # num_clauses (torch.LongTensor) is the next-to-last when present.
        if len(x) == 8:
            num_clauses = x.pop()
        texts, price_features, padding_mask, n_join_col, n_fanout, n_table, n_filter_col = x

        # When cross-attn is enabled, the embedder needs LLM hidden states.
        # Otherwise (mode 7 / cx=0), use the cheaper LLM forward.
        pooled_emb, hidden_states, attn_mask, per_window = self._llm_forward(texts)
        if pooled_emb.dtype != torch.float32:
            pooled_emb = pooled_emb.float()

        # QRT: tokenize+embed residual SQL fragments per-batch; pass the
        # StatQrtCrossAttn block into PRICEEmbedder.forward so it can refine
        # stat_core before biCross.
        r_qry, r_mask = (None, None)
        if self.use_qrt_cross_attn:
            r_qry, r_mask = self._embed_residual_texts(residual_texts, price_features.device)

        price_emb, updated_llm, _ = self.price(
            price_features, padding_mask, n_join_col, n_fanout, n_table, n_filter_col,
            llm_hidden_states=hidden_states, llm_attention_mask=attn_mask,
            num_clauses=num_clauses,
            qrt_block=self.stat_qrt, r_qry=r_qry, r_mask=r_mask, per_window=per_window,
        )

        llm_emb = self._select_llm_emb(pooled_emb, updated_llm)

        combined = torch.cat([llm_emb, price_emb], dim=1)
        if self.residual_pred:
            # True ResNet-style bypass: base_mlp eats pooled_emb (PRE-cross-attn
            # LLM output), so the base path is independent of cross-attn. delta
            # head sees the cross-attn-fused (post-cross-attn LLM ⊕ post-cross-
            # attn PRICE) features. At step 0, delta_mlp.out_mlp2 is zero-init
            # so delta_logit ≡ 0 and the model is *exactly* an LLM-only
            # predictor. Training opens up delta only if cross-attn helps; if
            # it never does, gradients flowing through cross-attn vanish and
            # the model degrades gracefully to pure LLM.
            base_logit = self.base_mlp(pooled_emb)
            delta_logit = self.mlp(combined)
            if self.delta_bound > 0:
                delta_logit = torch.tanh(delta_logit) * self.delta_bound
            out = torch.sigmoid(base_logit + delta_logit)
        else:
            out = self.mlp(combined)
        if self.training:
            _c = getattr(self, '_dbg_count', 0)
            if _c < 5:
                self._dbg_count = _c + 1
                _ncx = getattr(self.price, 'n_cross_layers', 0)
                print(f"[Mode7-fwd b{_c} cx={_ncx}] llm_emb mean={llm_emb.mean().item():.8f} std={llm_emb.std().item():.8f} norm={llm_emb.norm().item():.6f}")
                print(f"[Mode7-fwd b{_c} cx={_ncx}] price_emb mean={price_emb.mean().item():.8f} std={price_emb.std().item():.8f} norm={price_emb.norm().item():.6f}")
                print(f"[Mode7-fwd b{_c} cx={_ncx}] out mean={out.mean().item():.8f} samples={out[:, 0].detach().cpu().tolist()[:3]}")
        return out

    @torch.no_grad()
    def forward_embeddings(self, x):
        """Return concat([llm_emb, price_emb]) without the final MLP head.
        Used by retrain_mlp inference flow to cache features."""
        residual_texts = None
        num_clauses = None
        x = list(x)
        if len(x) > 7 and isinstance(x[-1], (list, tuple)) and (
            len(x[-1]) == 0 or isinstance(x[-1][0], str)
        ):
            residual_texts = x.pop()
        if len(x) == 8:
            num_clauses = x.pop()
        texts, price_features, padding_mask, n_join_col, n_fanout, n_table, n_filter_col = x
        pooled_emb, hidden_states, attn_mask, per_window = self._llm_forward(texts)
        if pooled_emb.dtype != torch.float32:
            pooled_emb = pooled_emb.float()
        r_qry, r_mask = (None, None)
        if self.use_qrt_cross_attn:
            r_qry, r_mask = self._embed_residual_texts(residual_texts, price_features.device)
        price_emb, updated_llm, _ = self.price(
            price_features, padding_mask, n_join_col, n_fanout, n_table, n_filter_col,
            llm_hidden_states=hidden_states, llm_attention_mask=attn_mask,
            num_clauses=num_clauses,
            qrt_block=self.stat_qrt, r_qry=r_qry, r_mask=r_mask, per_window=per_window,
        )
        llm_emb = self._select_llm_emb(pooled_emb, updated_llm)
        return torch.cat([llm_emb, price_emb], dim=1)


class GatedLLMPriceJointModel(nn.Module):
    """
    Joint model with learned gating on PRICE embeddings.
    gate = sigmoid(Linear(D_llm -> D_price)), applied element-wise to price_emb.
    When gate->0, recovers pure LLM performance.
    """

    def __init__(self, llm, price_embedder, llm_embed_size, price_embed_size, hid_units):
        super().__init__()
        self.llm = llm
        self.price = price_embedder
        self.gate = nn.Sequential(
            nn.Linear(llm_embed_size, price_embed_size),
            nn.Sigmoid()
        )
        combined_dim = llm_embed_size + price_embed_size
        from trainer import Prediction
        self.mlp = Prediction(combined_dim, hid_units)

    def forward(self, x):
        texts, price_features, padding_mask, n_join_col, n_fanout, n_table, n_filter_col = x
        llm_emb = self.llm(texts)
        if llm_emb.dtype != torch.float32:
            llm_emb = llm_emb.float()
        # PRICEEmbedder now always returns 3-tuple; first element is the price embedding.
        price_emb, _, _ = self.price(
            price_features, padding_mask, n_join_col, n_fanout, n_table, n_filter_col
        )
        gated_price_emb = self.gate(llm_emb) * price_emb
        combined = torch.cat([llm_emb, gated_price_emb], dim=1)
        return self.mlp(combined)


class FrozenLLMPriceModel(nn.Module):
    """
    Model for finetuning PRICE+MLP with pre-computed (frozen) LLM embeddings.

    Unlike LLMPriceJointModel, this model does NOT contain the LLM.
    The forward method receives pre-computed LLM embeddings as tensors
    instead of raw text, so no LLM forward pass occurs during training.

    The forward method receives a tuple:
      (llm_embeddings, price_features, padding_mask, n_join_col, n_fanout, n_table, n_filter_col)
    """

    def __init__(self, price_embedder, llm_embed_size, price_embed_size, hid_units):
        """
        Args:
            price_embedder: PRICEEmbedder instance
            llm_embed_size: LLM hidden dim (must match pre-computed embeddings)
            price_embed_size: PRICE embedding dim (512)
            hid_units: MLP hidden dimension
        """
        super().__init__()
        self.price = price_embedder
        combined_dim = llm_embed_size + price_embed_size
        from trainer import Prediction
        self.mlp = Prediction(combined_dim, hid_units)

    def forward(self, x):
        """
        Args:
            x: tuple of (llm_emb, price_features, padding_mask, n_join_col, n_fanout, n_table, n_filter_col)
               llm_emb: [B, D_llm] pre-computed LLM embeddings (tensor)

        Returns:
            prediction: [B, 1]
        """
        llm_emb, price_features, padding_mask, n_join_col, n_fanout, n_table, n_filter_col = x

        if llm_emb.dtype != torch.float32:
            llm_emb = llm_emb.float()

        # PRICE embedding (PRICEEmbedder now always returns 3-tuple).
        price_emb, _, _ = self.price(
            price_features, padding_mask, n_join_col, n_fanout, n_table, n_filter_col
        )

        # Concatenate and predict
        combined = torch.cat([llm_emb, price_emb], dim=1)
        return self.mlp(combined)


class PRICEFinetunWrapper(nn.Module):
    """
    Wrapper for finetuning PRICE's RegressionModel on cardinality estimation.

    Accepts a tuple (price_feats, pg_est_cards, pad_masks, njcs, nfos, ntbs, nfcs)
    or (price_feats, pg_est_cards, pad_masks, njcs, nfos, ntbs, nfcs, num_clauses)
    and unpacks it for RegressionModel.forward().
    """

    def __init__(self, regression_model):
        super().__init__()
        self.model = regression_model

    def forward(self, x):
        if len(x) == 8:
            price_feats, pg_est_cards, pad_masks, njcs, nfos, ntbs, nfcs, num_clauses = x
            return self.model(price_feats, pg_est_cards, pad_masks, njcs, nfos, ntbs, nfcs,
                              num_clauses=num_clauses)
        price_feats, pg_est_cards, pad_masks, njcs, nfos, ntbs, nfcs = x
        return self.model(price_feats, pg_est_cards, pad_masks, njcs, nfos, ntbs, nfcs)


# ─── Cross-Attention Fusion (Mode 11) ────────────────────────────────────

import math
from model.module import FeedForward


class CrossAttentionHead(nn.Module):
    """Single cross-attention head: Q from query_tokens, K/V from kv_tokens."""

    def __init__(self, head_size, n_embd, dropout_rate):
        super().__init__()
        self.Query = nn.Linear(n_embd, head_size)
        self.Key = nn.Linear(n_embd, head_size)
        self.Value = nn.Linear(n_embd, head_size)
        self.dropout_rate = dropout_rate

    def forward(self, query_tokens, kv_tokens, kv_mask=None):
        """
        Args:
            query_tokens: [B, T_q, D]  (PRICE tokens)
            kv_tokens:    [B, T_kv, D] (projected LLM hidden states)
            kv_mask:      [B, T_kv] attention mask (1=attend, 0=pad)
        Returns:
            out: [B, T_q, head_size]
        """
        q = self.Query(query_tokens)   # [B, T_q, head_size]
        k = self.Key(kv_tokens)        # [B, T_kv, head_size]
        v = self.Value(kv_tokens)      # [B, T_kv, head_size]

        scores = torch.matmul(q, k.transpose(-1, -2)) / math.sqrt(k.size(-1))  # [B, T_q, T_kv]

        if kv_mask is not None:
            # kv_mask: [B, T_kv] -> [B, 1, T_kv] for broadcasting over T_q
            scores = scores.masked_fill(kv_mask.unsqueeze(1) == 0, -1e9)

        weights = F.softmax(scores, dim=-1)
        weights = F.dropout(weights, p=self.dropout_rate, training=self.training)
        return torch.matmul(weights, v)


class MultiHeadCrossAttention(nn.Module):
    """Multi-head cross-attention with linear projection."""

    def __init__(self, n_heads, head_size, n_embd, dropout_rate):
        super().__init__()
        self.heads = nn.ModuleList([
            CrossAttentionHead(head_size, n_embd, dropout_rate) for _ in range(n_heads)
        ])
        self.projection = nn.Linear(n_heads * head_size, n_embd)

    def forward(self, query_tokens, kv_tokens, kv_mask=None):
        head_outputs = [h(query_tokens, kv_tokens, kv_mask) for h in self.heads]
        return self.projection(torch.cat(head_outputs, dim=-1))


class CrossAttentionBlock(nn.Module):
    """Pre-norm cross-attention + pre-norm FFN with residual connections.

    Optional ReZero-style learnable gates (`use_gate=True`) scale the attn and
    FFN deltas by a per-block scalar, both initialized to 0 — so at init the
    block is a pure pass-through (output = query). Training opens the gates
    only when cross-attn actually reduces the loss; if it never helps, gates
    stay near 0 and the model degrades gracefully to LLM-only.
    """

    def __init__(self, n_embd, n_heads, dropout_rate, use_gate=False):
        super().__init__()
        self.norm1 = nn.LayerNorm(n_embd)
        self.cross_attn = MultiHeadCrossAttention(
            n_heads, n_embd // n_heads, n_embd, dropout_rate
        )
        self.norm2 = nn.LayerNorm(n_embd)
        self.feed_forward = FeedForward(n_embd)
        self.dropout_rate = dropout_rate
        self.use_gate = use_gate
        if use_gate:
            self.attn_gate = nn.Parameter(torch.zeros(1))
            self.ffn_gate = nn.Parameter(torch.zeros(1))

    def forward(self, query_tokens, kv_tokens, kv_mask=None):
        # Pre-norm cross-attention with residual (gated when use_gate=True)
        normed = self.norm1(query_tokens)
        attn_out = self.cross_attn(normed, kv_tokens, kv_mask)
        attn_out = F.dropout(attn_out, p=self.dropout_rate, training=self.training)
        if self.use_gate:
            attn_out = self.attn_gate * attn_out
        x = query_tokens + attn_out

        # Pre-norm FFN with residual (gated when use_gate=True)
        normed = self.norm2(x)
        ff_out = self.feed_forward(normed)
        ff_out = F.dropout(ff_out, p=self.dropout_rate, training=self.training)
        if self.use_gate:
            ff_out = self.ffn_gate * ff_out
        return x + ff_out


class StatQrtCrossAttn(nn.Module):
    """Single-layer bidirectional self-attention over [stat_core || QRT],
    returning only the refined stat_core CLS (length-1).

    Wired in by --use_qrt_cross_attn. Per the PRICE_N design doc §10:
      - stat_core comes from the OR-Transformer (or filter_encoder CLS when
        --price_n_or is off / single-clause). Shape [B, 1, D_stat].
      - r_qry comes from LLM.embed_tokens(tokenizer(residual_text)), where
        residual_text concatenates SQL fragments the stat-core can't encode
        (LIKE / ILIKE / EXISTS / IN-subq / scalar subq / opaque). Shape
        [B, T_r, D_llm], with r_mask [B, T_r] (1 = real token, 0 = pad).

    The block concatenates [stat_proj || r_qry] and runs one Transformer-
    style self-attention layer (pre-norm cross-attn block with Q=KV=the
    concatenated sequence — equivalent to a single self-attn layer). The
    stat_core position attends over all QRT tokens AND vice versa, so the
    bidirectional information flow happens inside one layer. Only the
    refined stat_core CLS is returned (shape [B, 1, D_llm]), so the
    downstream Plan↔Query cross-attn block sees the same length-1 PRICE
    summary shape as before — no other model code needs to change.
    """

    def __init__(self, d_stat: int, d_llm: int, n_heads: int = 4,
                 dropout_rate: float = 0.1):
        super().__init__()
        # Per design decision (2026-05-11): project stat_core to D_llm so the
        # cross-attn ops are dim-matched. No-op when D_stat == D_llm.
        self.stat_to_llm = (nn.Linear(d_stat, d_llm)
                             if d_stat != d_llm else nn.Identity())
        # One bidirectional layer over [stat || qrt]: reuse the existing
        # CrossAttentionBlock with Q=KV to get pre-norm self-attn + FFN.
        self.layer = CrossAttentionBlock(d_llm, n_heads, dropout_rate)

    def forward(self, stat_core, r_qry, r_mask=None):
        """
        Args:
            stat_core: [B, 1, D_stat] — PRICE stat_core CLS.
            r_qry:     [B, T_r, D_llm] — QRT token embeddings.
            r_mask:    [B, T_r] (optional) — 1 for real tokens, 0 for pads.
        Returns:
            stat_refined: [B, 1, D_llm] — stat_core CLS enriched by QRT
                information. Same shape as the original stat_core (in D_llm),
                so the downstream biCross block input shape is unchanged.
        """
        stat_proj = self.stat_to_llm(stat_core)              # [B, 1, D_llm]
        x = torch.cat([stat_proj, r_qry], dim=1)              # [B, 1+T_r, D_llm]
        # Build KV mask: stat position is always valid (1); pad QRT tokens
        # get the r_mask value. CrossAttentionBlock expects a mask where 1 =
        # real token, 0 = pad (it converts internally for the attention op).
        if r_mask is not None:
            stat_valid = torch.ones(r_mask.size(0), 1,
                                     dtype=r_mask.dtype, device=r_mask.device)
            kv_mask = torch.cat([stat_valid, r_mask], dim=1)  # [B, 1+T_r]
        else:
            kv_mask = None
        x_refined = self.layer(x, x, kv_mask)                 # self-attn (Q=KV)
        return x_refined[:, :1, :]                            # [B, 1, D_llm]


class CrossAttentionPRICEEmbedder(nn.Module):
    """
    Like PRICEEmbedder but adds cross-attention layers that let PRICE tokens
    attend to LLM hidden states after the filter encoder, before CLS extraction.
    """

    def __init__(self, regression_model, llm_hidden_dim, n_cross_layers=2,
                 n_embd=256, n_heads=8, dropout_rate=0.1, use_gate=False):
        super().__init__()
        # Copy PRICE layers (same as PRICEEmbedder)
        self.n_join_col = regression_model.n_join_col
        self.n_fanout = regression_model.n_fanout
        self.n_table = regression_model.n_table
        self.n_filter_col = regression_model.n_filter_col
        self.hist_dim = regression_model.hist_dim
        self.table_dim = regression_model.table_dim
        self.dropout_rate = regression_model.dropout_rate

        self.scale_embedding = regression_model.scale_embedding
        self.filter_embedding = regression_model.filter_embedding
        self.scale_encoder = regression_model.scale_encoder
        self.filter_encoder = regression_model.filter_encoder
        self.len_net = regression_model.len_net
        self.linear = regression_model.linear
        self.elu = regression_model.elu

        # NEW: project LLM hidden states to PRICE embedding dim
        self.llm_proj = nn.Linear(llm_hidden_dim, n_embd)

        # NEW: cross-attention blocks
        self.cross_attn_blocks = nn.ModuleList([
            CrossAttentionBlock(n_embd, n_heads, dropout_rate, use_gate=use_gate)
            for _ in range(n_cross_layers)
        ])

    def cross_attn_parameters(self):
        """Return parameters belonging to cross-attention layers (llm_proj + blocks)."""
        yield from self.llm_proj.parameters()
        yield from self.cross_attn_blocks.parameters()

    def price_core_parameters(self):
        """Return PRICE-core parameters (everything except cross-attention)."""
        cross_attn_ids = {id(p) for p in self.cross_attn_parameters()}
        for p in self.parameters():
            if id(p) not in cross_attn_ids:
                yield p

    def forward(self, x, padding_mask, n_join_col, n_fanout, n_table, n_filter_col,
                llm_hidden_states=None, llm_attention_mask=None):
        """
        Args:
            x, padding_mask, n_join_col, n_fanout, n_table, n_filter_col: same as PRICEEmbedder
            llm_hidden_states: [B, T_plan, D_llm] from LLM encoder
            llm_attention_mask: [B, T_plan] (1=real token, 0=pad)

        Returns:
            query_output: [B, 512]
        """
        # Scaling stage
        scale_features = self.scale_embedding(x)
        masks1 = padding_mask[:, :1 + self.n_join_col + self.n_fanout] if padding_mask is not None else None
        scaling_output = self.scale_encoder(scale_features, masks1)

        # Filtering stage
        filter_features = self.filter_embedding(scaling_output, x)
        masks2 = padding_mask[:, :] if padding_mask is not None else None
        filtering_output = self.filter_encoder(filter_features, masks2)
        # filtering_output: [B, T_stats, 256]

        # Cross-attention: PRICE tokens attend to LLM hidden states
        if llm_hidden_states is not None:
            llm_proj = self.llm_proj(llm_hidden_states.float())  # [B, T_plan, 256]
            for block in self.cross_attn_blocks:
                filtering_output = block(filtering_output, llm_proj, llm_attention_mask)

        # CLS token extraction
        query_output = filtering_output[:, 0, :]

        # Length features
        len_features = torch.cat([n_join_col, n_fanout, n_table, n_filter_col], dim=1)
        len_features = self.len_net(len_features)

        # Linear + ELU
        query_output = self.linear(torch.cat([query_output, len_features], dim=1))
        query_output = self.elu(query_output)
        query_output = F.dropout(query_output, p=self.dropout_rate, training=self.training)

        return query_output  # [B, 512]


class CrossAttentionLLMPriceModel(nn.Module):
    """
    Joint model with late cross-attention fusion (Mode 11).
    PRICE tokens attend to LLM hidden states via one-way cross-attention,
    then the enriched PRICE embedding is concatenated with LLM pooled embedding
    for the MLP head.
    """

    def __init__(self, llm, price_embedder, llm_embed_size, price_embed_size, hid_units):
        super().__init__()
        self.llm = llm
        self.price = price_embedder  # CrossAttentionPRICEEmbedder
        combined_dim = llm_embed_size + price_embed_size
        from trainer import Prediction
        self.mlp = Prediction(combined_dim, hid_units)

    def forward(self, x):
        """
        Args:
            x: tuple of (texts, price_features, padding_mask, n_join_col, n_fanout, n_table, n_filter_col)
        """
        texts, price_features, padding_mask, n_join_col, n_fanout, n_table, n_filter_col = x

        # LLM: get both pooled embedding and hidden states
        pooled_emb, hidden_states, attn_mask = self.llm.forward_with_sequence(texts)
        if pooled_emb.dtype != torch.float32:
            pooled_emb = pooled_emb.float()

        # PRICE embedding with cross-attention to LLM hidden states
        price_emb = self.price(
            price_features, padding_mask, n_join_col, n_fanout, n_table, n_filter_col,
            llm_hidden_states=hidden_states, llm_attention_mask=attn_mask
        )

        # Concatenate and predict
        combined = torch.cat([pooled_emb, price_emb], dim=1)
        return self.mlp(combined)

    @torch.no_grad()
    def forward_embeddings(self, x):
        """Return combined [pooled_emb, price_emb] before MLP."""
        texts, price_features, padding_mask, n_join_col, n_fanout, n_table, n_filter_col = x
        pooled_emb, hidden_states, attn_mask = self.llm.forward_with_sequence(texts)
        if pooled_emb.dtype != torch.float32:
            pooled_emb = pooled_emb.float()
        price_emb = self.price(
            price_features, padding_mask, n_join_col, n_fanout, n_table, n_filter_col,
            llm_hidden_states=hidden_states, llm_attention_mask=attn_mask
        )
        return torch.cat([pooled_emb, price_emb], dim=1)


# ─── Bidirectional Cross-Attention Fusion (Mode 12) ──────────────────────
#
# Alternating single-direction layers: reuses CrossAttentionBlock and swaps
# which tokens are Q vs K/V on each layer.
#   Layer 0 (even): PRICE tokens (Q) attend to LLM tokens (K/V)
#   Layer 1 (odd):  LLM tokens (Q) attend to PRICE tokens (K/V)
#   Layer 2 (even): PRICE → LLM  ...
# Same params-per-layer as Mode 11, but LLM representations get refined too.


class BiCrossAttentionPRICEEmbedder(nn.Module):
    """
    Like CrossAttentionPRICEEmbedder but uses alternating bidirectional
    cross-attention: even layers let PRICE attend to LLM, odd layers let
    LLM attend to PRICE.  Each layer is a standard CrossAttentionBlock.
    """

    def __init__(self, regression_model, llm_hidden_dim, n_cross_layers=2,
                 n_embd=256, n_heads=8, dropout_rate=0.1, use_gate=False):
        super().__init__()
        # Copy PRICE layers (same as PRICEEmbedder)
        self.n_join_col = regression_model.n_join_col
        self.n_fanout = regression_model.n_fanout
        self.n_table = regression_model.n_table
        self.n_filter_col = regression_model.n_filter_col
        self.hist_dim = regression_model.hist_dim
        self.table_dim = regression_model.table_dim
        self.dropout_rate = regression_model.dropout_rate

        self.scale_embedding = regression_model.scale_embedding
        self.filter_embedding = regression_model.filter_embedding
        self.scale_encoder = regression_model.scale_encoder
        self.filter_encoder = regression_model.filter_encoder
        self.len_net = regression_model.len_net
        self.linear = regression_model.linear
        self.elu = regression_model.elu

        # Project LLM hidden states to PRICE embedding dim
        self.llm_proj = nn.Linear(llm_hidden_dim, n_embd)

        # Alternating cross-attention blocks (same class, direction chosen at runtime)
        self.cross_attn_blocks = nn.ModuleList([
            CrossAttentionBlock(n_embd, n_heads, dropout_rate, use_gate=use_gate)
            for _ in range(n_cross_layers)
        ])

    def cross_attn_parameters(self):
        """Return parameters belonging to cross-attention layers (llm_proj + blocks)."""
        yield from self.llm_proj.parameters()
        yield from self.cross_attn_blocks.parameters()

    def price_core_parameters(self):
        """Return PRICE-core parameters (everything except cross-attention)."""
        cross_attn_ids = {id(p) for p in self.cross_attn_parameters()}
        for p in self.parameters():
            if id(p) not in cross_attn_ids:
                yield p

    def forward(self, x, padding_mask, n_join_col, n_fanout, n_table, n_filter_col,
                llm_hidden_states=None, llm_attention_mask=None):
        """
        Args:
            x, padding_mask, n_join_col, n_fanout, n_table, n_filter_col: same as PRICEEmbedder
            llm_hidden_states: [B, T_plan, D_llm] from LLM encoder
            llm_attention_mask: [B, T_plan] (1=real token, 0=pad)

        Returns:
            query_output: [B, 512]
            refined_llm: [B, T_plan, n_embd] or None — refined LLM tokens after cross-attention
            llm_attention_mask: passed through for masked pooling
        """
        # Scaling stage
        scale_features = self.scale_embedding(x)
        masks1 = padding_mask[:, :1 + self.n_join_col + self.n_fanout] if padding_mask is not None else None
        scaling_output = self.scale_encoder(scale_features, masks1)

        # Filtering stage
        filter_features = self.filter_embedding(scaling_output, x)
        masks2 = padding_mask[:, :] if padding_mask is not None else None
        filtering_output = self.filter_encoder(filter_features, masks2)
        # filtering_output: [B, T_stats, 256]

        # Alternating bidirectional cross-attention
        refined_llm = None
        if llm_hidden_states is not None:
            llm_proj = self.llm_proj(llm_hidden_states.float())  # [B, T_plan, 256]
            price_mask = masks2  # same convention: 1=attend, 0=pad

            for i, block in enumerate(self.cross_attn_blocks):
                if i % 2 == 0:
                    # Even layer: PRICE (Q) attends to LLM (K/V)
                    filtering_output = block(filtering_output, llm_proj, llm_attention_mask)
                else:
                    # Odd layer: LLM (Q) attends to PRICE (K/V)
                    llm_proj = block(llm_proj, filtering_output, price_mask)

            refined_llm = llm_proj  # [B, T_plan, n_embd]

        # CLS token extraction
        query_output = filtering_output[:, 0, :]

        # Length features
        len_features = torch.cat([n_join_col, n_fanout, n_table, n_filter_col], dim=1)
        len_features = self.len_net(len_features)

        # Linear + ELU
        query_output = self.linear(torch.cat([query_output, len_features], dim=1))
        query_output = self.elu(query_output)
        query_output = F.dropout(query_output, p=self.dropout_rate, training=self.training)

        return query_output, refined_llm, llm_attention_mask  # [B, 512], [B, T, 256], [B, T]


# ─── Reverse Cross-Attention Fusion (Mode 13) ──────────────────────────
#
# LLM tokens attend to PRICE tokens (reverse of Mode 11).
# PRICE tokens are projected UP to LLM hidden dim so cross-attention
# operates in LLM space.  Output: concat(mean_pooled_updated_LLM, PRICE_512).


class ReverseCrossAttentionBlock(nn.Module):
    """Pre-norm cross-attention + pre-norm FFN at LLM hidden dim.

    Optional ReZero-style learnable gates (`use_gate=True`) — see
    CrossAttentionBlock for rationale. At init both gates are 0 → block is a
    pure pass-through, so adding biCross can never make things worse than
    LLM-only at start.
    """

    def __init__(self, llm_dim, n_heads, dropout_rate, use_gate=False):
        super().__init__()
        self.norm1 = nn.LayerNorm(llm_dim)
        self.cross_attn = MultiHeadCrossAttention(
            n_heads, llm_dim // n_heads, llm_dim, dropout_rate
        )
        self.norm2 = nn.LayerNorm(llm_dim)
        self.feed_forward = nn.Sequential(
            nn.Linear(llm_dim, llm_dim * 4),
            nn.GELU(),
            nn.Linear(llm_dim * 4, llm_dim),
        )
        self.dropout_rate = dropout_rate
        self.use_gate = use_gate
        if use_gate:
            self.attn_gate = nn.Parameter(torch.zeros(1))
            self.ffn_gate = nn.Parameter(torch.zeros(1))

    def forward(self, query_tokens, kv_tokens, kv_mask=None):
        # Pre-norm cross-attention with residual (gated when use_gate=True)
        normed = self.norm1(query_tokens)
        attn_out = self.cross_attn(normed, kv_tokens, kv_mask)
        attn_out = F.dropout(attn_out, p=self.dropout_rate, training=self.training)
        if self.use_gate:
            attn_out = self.attn_gate * attn_out
        x = query_tokens + attn_out

        # Pre-norm FFN with residual (gated when use_gate=True)
        normed = self.norm2(x)
        ff_out = self.feed_forward(normed)
        ff_out = F.dropout(ff_out, p=self.dropout_rate, training=self.training)
        if self.use_gate:
            ff_out = self.ffn_gate * ff_out
        return x + ff_out


class ReverseCrossAttentionPRICEEmbedder(nn.Module):
    """
    Dual-direction cross-attention embedder (Mode 13).

    Warmup phase (warmup_mode=True):
      PRICE tokens (Q) attend to LLM tokens (K/V) at PRICE dim (n_embd=256).
      This lets PRICE learn from frozen LLM, same direction as Mode 11.
      Returns: (updated_PRICE_512, None, mask)

    Normal phase (warmup_mode=False):
      LLM tokens (Q) attend to PRICE tokens (K/V) at LLM dim.
      This lets LLM learn from trained PRICE.
      Returns: (PRICE_512, updated_LLM, mask)
    """

    def __init__(self, regression_model, llm_hidden_dim, n_cross_layers=2,
                 n_embd=256, n_heads=8, dropout_rate=0.1, use_gate=False):
        super().__init__()
        # Copy PRICE layers (same as PRICEEmbedder)
        self.n_join_col = regression_model.n_join_col
        self.n_fanout = regression_model.n_fanout
        self.n_table = regression_model.n_table
        self.n_filter_col = regression_model.n_filter_col
        self.hist_dim = regression_model.hist_dim
        self.table_dim = regression_model.table_dim
        self.dropout_rate = regression_model.dropout_rate

        self.scale_embedding = regression_model.scale_embedding
        self.filter_embedding = regression_model.filter_embedding
        self.scale_encoder = regression_model.scale_encoder
        self.filter_encoder = regression_model.filter_encoder
        self.len_net = regression_model.len_net
        self.linear = regression_model.linear
        self.elu = regression_model.elu

        # ── Warmup direction: PRICE (Q) attends to LLM (K/V) at n_embd ──
        self.llm_proj_down = nn.Linear(llm_hidden_dim, n_embd)
        self.warmup_cross_attn_blocks = nn.ModuleList([
            CrossAttentionBlock(n_embd, n_heads, dropout_rate, use_gate=use_gate)
            for _ in range(n_cross_layers)
        ])

        # ── Normal direction: LLM (Q) attends to PRICE (K/V) at llm_dim ──
        self.price_proj_up = nn.Linear(n_embd, llm_hidden_dim)
        self.cross_attn_blocks = nn.ModuleList([
            ReverseCrossAttentionBlock(llm_hidden_dim, n_heads, dropout_rate, use_gate=use_gate)
            for _ in range(n_cross_layers)
        ])

        self.warmup_mode = False

    def cross_attn_parameters(self):
        """Return parameters belonging to ALL cross-attention layers."""
        yield from self.llm_proj_down.parameters()
        yield from self.warmup_cross_attn_blocks.parameters()
        yield from self.price_proj_up.parameters()
        yield from self.cross_attn_blocks.parameters()

    def price_core_parameters(self):
        """Return PRICE-core parameters (everything except cross-attention)."""
        cross_attn_ids = {id(p) for p in self.cross_attn_parameters()}
        for p in self.parameters():
            if id(p) not in cross_attn_ids:
                yield p

    def forward(self, x, padding_mask, n_join_col, n_fanout, n_table, n_filter_col,
                llm_hidden_states=None, llm_attention_mask=None):
        """
        Args:
            x, padding_mask, n_join_col, n_fanout, n_table, n_filter_col: same as PRICEEmbedder
            llm_hidden_states: [B, T_plan, D_llm] from LLM encoder
            llm_attention_mask: [B, T_plan] (1=real token, 0=pad)

        Returns:
            query_output: [B, 512] — PRICE embedding (updated during warmup, unmodified otherwise)
            updated_llm: [B, T_plan, D_llm] or None — updated LLM (only in normal mode)
            llm_attention_mask: passed through for masked pooling
        """
        # Scaling stage
        scale_features = self.scale_embedding(x)
        masks1 = padding_mask[:, :1 + self.n_join_col + self.n_fanout] if padding_mask is not None else None
        scaling_output = self.scale_encoder(scale_features, masks1)

        # Filtering stage
        filter_features = self.filter_embedding(scaling_output, x)
        masks2 = padding_mask[:, :] if padding_mask is not None else None
        filtering_output = self.filter_encoder(filter_features, masks2)
        # filtering_output: [B, T_stats, n_embd]

        updated_llm = None
        if llm_hidden_states is not None:
            if self.warmup_mode:
                # Warmup: PRICE (Q) attends to LLM (K/V) at n_embd dim
                llm_proj = self.llm_proj_down(llm_hidden_states.float())  # [B, T_plan, n_embd]
                for block in self.warmup_cross_attn_blocks:
                    filtering_output = block(filtering_output, llm_proj, llm_attention_mask)
                # filtering_output is updated; LLM unchanged → updated_llm stays None
            else:
                # Normal: LLM (Q) attends to PRICE (K/V) at LLM dim
                price_proj = self.price_proj_up(filtering_output.float())  # [B, T_stats, D_llm]
                price_mask = masks2

                llm_tokens = llm_hidden_states.float()  # [B, T_plan, D_llm]
                for block in self.cross_attn_blocks:
                    llm_tokens = block(llm_tokens, price_proj, price_mask)

                updated_llm = llm_tokens  # [B, T_plan, D_llm]

        # CLS token extraction
        query_output = filtering_output[:, 0, :]

        # Length features
        len_features = torch.cat([n_join_col, n_fanout, n_table, n_filter_col], dim=1)
        len_features = self.len_net(len_features)

        # Linear + ELU
        query_output = self.linear(torch.cat([query_output, len_features], dim=1))
        query_output = self.elu(query_output)
        query_output = F.dropout(query_output, p=self.dropout_rate, training=self.training)

        return query_output, updated_llm, llm_attention_mask


class ReverseCrossAttentionLLMPriceModel(nn.Module):
    """
    Joint model with reverse cross-attention fusion (Mode 13).
    LLM tokens attend to PRICE tokens via cross-attention.
    The updated LLM tokens are mean-pooled, then concatenated with
    the PRICE 512-dim embedding for the MLP head.
    Output: concat(mean_pooled_updated_LLM, PRICE_512)
    """

    def __init__(self, llm, price_embedder, llm_embed_size, price_embed_size, hid_units):
        super().__init__()
        self.llm = llm
        self.price = price_embedder  # ReverseCrossAttentionPRICEEmbedder
        combined_dim = llm_embed_size + price_embed_size
        from trainer import Prediction
        self.mlp = Prediction(combined_dim, hid_units)

    def _pool_llm(self, llm_tokens, attn_mask):
        """Mean-pool LLM tokens with attention mask."""
        mask = attn_mask.unsqueeze(-1).float()  # [B, T, 1]
        pooled = (llm_tokens * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1)
        return pooled  # [B, D_llm]

    def forward(self, x):
        texts, price_features, padding_mask, n_join_col, n_fanout, n_table, n_filter_col = x

        # LLM: get both pooled embedding and hidden states
        pooled_emb, hidden_states, attn_mask = self.llm.forward_with_sequence(texts)
        if pooled_emb.dtype != torch.float32:
            pooled_emb = pooled_emb.float()

        # PRICE embedding + reverse cross-attention (LLM attends to PRICE)
        price_emb, updated_llm, updated_mask = self.price(
            price_features, padding_mask, n_join_col, n_fanout, n_table, n_filter_col,
            llm_hidden_states=hidden_states, llm_attention_mask=attn_mask
        )

        # Use updated LLM if available, otherwise fall back to original pooled
        if updated_llm is not None:
            llm_emb = self._pool_llm(updated_llm, updated_mask)
        else:
            llm_emb = pooled_emb

        combined = torch.cat([llm_emb, price_emb], dim=1)
        return self.mlp(combined)

    @torch.no_grad()
    def forward_embeddings(self, x):
        """Return combined [updated_llm_pooled, price_emb] before MLP."""
        texts, price_features, padding_mask, n_join_col, n_fanout, n_table, n_filter_col = x
        pooled_emb, hidden_states, attn_mask = self.llm.forward_with_sequence(texts)
        if pooled_emb.dtype != torch.float32:
            pooled_emb = pooled_emb.float()
        price_emb, updated_llm, updated_mask = self.price(
            price_features, padding_mask, n_join_col, n_fanout, n_table, n_filter_col,
            llm_hidden_states=hidden_states, llm_attention_mask=attn_mask
        )
        if updated_llm is not None:
            llm_emb = self._pool_llm(updated_llm, updated_mask)
        else:
            llm_emb = pooled_emb
        return torch.cat([llm_emb, price_emb], dim=1)


# ─── Inflated BiCrossAttn (Mode 12 + inflate_price) ─────────────────────
#
# Like BiCrossAttn but projects PRICE UP to LLM dim instead of LLM down to 256.
# Both directions of cross-attention operate at LLM hidden dim.
# Output: concat(updated_LLM_pooled, updated_PRICE_pooled), both at LLM dim.
# During warmup: only even layers (PRICE→LLM) + PRICE core train.
#   Odd layers (LLM→PRICE) and LLM LoRA are frozen.


class InflatedBiCrossAttentionPRICEEmbedder(nn.Module):
    """
    BiCrossAttn at LLM dim: PRICE tokens projected UP to LLM hidden dim.
    Even layers: PRICE(Q) → LLM(K/V).  Odd layers: LLM(Q) → PRICE(K/V).
    Returns both updated PRICE embedding (at LLM dim) and updated LLM tokens.
    """

    def __init__(self, regression_model, llm_hidden_dim, n_cross_layers=2,
                 n_embd=256, n_heads=8, dropout_rate=0.1, use_gate=False):
        super().__init__()
        self.n_join_col = regression_model.n_join_col
        self.n_fanout = regression_model.n_fanout
        self.n_table = regression_model.n_table
        self.n_filter_col = regression_model.n_filter_col
        self.hist_dim = regression_model.hist_dim
        self.table_dim = regression_model.table_dim
        self.dropout_rate = regression_model.dropout_rate
        self.llm_hidden_dim = llm_hidden_dim

        # Mode-7-aligned PRICE pipeline: keep mode 7's CLS-then-linear path so
        # the (optionally pretrained) regression_model.linear weights and the
        # 512-dim representation are preserved. Then a single inflate Linear
        # projects to LLM dim. At cx=0 this path equals mode 7 + final inflate;
        # at cx>0, the inflated PRICE summary is treated as a length-1 token
        # for cross-attention against the LLM token sequence.
        self.scale_embedding = regression_model.scale_embedding
        self.filter_embedding = regression_model.filter_embedding
        self.scale_encoder = regression_model.scale_encoder
        self.filter_encoder = regression_model.filter_encoder
        self.len_net = regression_model.len_net
        self.linear = regression_model.linear  # mode 7's (n_embd+16) → query_hidden_dim (e.g. 272→512)
        self.elu = regression_model.elu

        # At cx=0 there is no cross-attn, so no need to inflate to LLM dim.
        # Output stays at query_hidden_dim (512), making this path EXACTLY
        # mode 7's PRICE pipeline. At cx>0 we inflate to LLM dim so the
        # PRICE summary can be cross-attended against LLM tokens.
        _query_hidden_dim = self.linear.out_features
        if n_cross_layers > 0:
            self.inflate = nn.Linear(_query_hidden_dim, llm_hidden_dim)
            self.price_output_dim = llm_hidden_dim
        else:
            self.inflate = None
            self.price_output_dim = _query_hidden_dim  # 512, matches mode 7

        # Cross-attention blocks at LLM dim. Operate on a length-1 PRICE
        # token (the inflated summary) and the LLM token sequence.
        self.cross_attn_blocks = nn.ModuleList([
            ReverseCrossAttentionBlock(llm_hidden_dim, n_heads, dropout_rate, use_gate=use_gate)
            for _ in range(n_cross_layers)
        ])

        # Zero-init the residual-output projections of ODD (LLM→PRICE) layers so
        # that when they activate post-warmup, their output is 0 → residual pass-through.
        for i, block in enumerate(self.cross_attn_blocks):
            if i % 2 == 1:
                nn.init.zeros_(block.cross_attn.projection.weight)
                nn.init.zeros_(block.cross_attn.projection.bias)
                nn.init.zeros_(block.feed_forward[-1].weight)
                nn.init.zeros_(block.feed_forward[-1].bias)

        self.warmup_mode = False  # skip odd layers during warmup

    def cross_attn_parameters(self):
        """Return parameters belonging to cross-attention layers."""
        if self.inflate is not None:
            yield from self.inflate.parameters()
        yield from self.cross_attn_blocks.parameters()

    def even_layer_parameters(self):
        """Even-layer (PRICE→LLM) cross-attn params + projection."""
        if self.inflate is not None:
            yield from self.inflate.parameters()
        for i, block in enumerate(self.cross_attn_blocks):
            if i % 2 == 0:
                yield from block.parameters()

    def odd_layer_parameters(self):
        """Odd-layer (LLM→PRICE) cross-attn params."""
        for i, block in enumerate(self.cross_attn_blocks):
            if i % 2 == 1:
                yield from block.parameters()

    def price_core_parameters(self):
        """Return PRICE-core parameters (everything except cross-attention)."""
        cross_attn_ids = {id(p) for p in self.cross_attn_parameters()}
        for p in self.parameters():
            if id(p) not in cross_attn_ids:
                yield p

    def forward(self, x, padding_mask, n_join_col, n_fanout, n_table, n_filter_col,
                llm_hidden_states=None, llm_attention_mask=None):
        """
        Returns:
            price_output: [B, llm_hidden_dim] — updated PRICE embedding at LLM dim
            updated_llm: [B, T_plan, llm_hidden_dim] — updated LLM tokens
            llm_attention_mask: passed through
        """
        # Scaling stage
        scale_features = self.scale_embedding(x)
        masks1 = padding_mask[:, :1 + self.n_join_col + self.n_fanout] if padding_mask is not None else None
        scaling_output = self.scale_encoder(scale_features, masks1)

        # Filtering stage
        filter_features = self.filter_embedding(scaling_output, x)
        masks2 = padding_mask[:, :] if padding_mask is not None else None
        filtering_output = self.filter_encoder(filter_features, masks2)
        # filtering_output: [B, T_stats, n_embd=256]

        # Mode-7-aligned PRICE pipeline:
        # CLS(256) → cat(+len 16) → linear(272→512) → ELU → dropout → inflate(512→llm_dim)
        # When --price_random_init is False, self.linear/self.elu/self.len_net carry the
        # pretrained PRICE weights, preserving mode 7's representation exactly.
        price_cls_256 = filtering_output[:, 0, :].float()  # [B, n_embd=256]

        len_features = torch.cat([n_join_col, n_fanout, n_table, n_filter_col], dim=1)
        len_features = self.len_net(len_features)

        price_emb_512 = self.linear(torch.cat([price_cls_256, len_features], dim=1))  # [B, query_hidden_dim]
        price_emb_512 = self.elu(price_emb_512)
        price_emb_512 = F.dropout(price_emb_512, p=self.dropout_rate, training=self.training)

        updated_llm = None
        if self.inflate is None:
            # cx=0: no cross-attn, no inflate. Output stays at query_hidden_dim.
            # This path is exactly mode 7's PRICE pipeline.
            price_output = price_emb_512  # [B, query_hidden_dim]
        else:
            # cx>0: inflate to LLM dim, cross-attend PRICE summary as length-1 token.
            price_emb = self.inflate(price_emb_512)  # [B, llm_hidden_dim]
            price_tokens = price_emb.unsqueeze(1)  # [B, 1, llm_hidden_dim]
            price_mask = torch.ones(price_tokens.size(0), 1, device=price_tokens.device, dtype=torch.long)

            any_llm_cross_attn = False
            if llm_hidden_states is not None:
                llm_tokens = llm_hidden_states.float()  # [B, T_plan, llm_dim]
                for i, block in enumerate(self.cross_attn_blocks):
                    if i % 2 == 0:
                        # Even: PRICE (Q) attends to LLM (K/V); price_tokens stays length-1
                        price_tokens = block(price_tokens, llm_tokens, llm_attention_mask)
                    elif not self.warmup_mode:
                        # Odd: LLM (Q) attends to PRICE summary (K/V, length 1)
                        llm_tokens = block(llm_tokens, price_tokens, price_mask)
                        any_llm_cross_attn = True

                if any_llm_cross_attn:
                    updated_llm = llm_tokens  # [B, T_plan, llm_dim]

            price_output = price_tokens[:, 0, :]  # [B, llm_hidden_dim] — refined PRICE summary

        return price_output, updated_llm, llm_attention_mask


class InflatedBiCrossAttentionLLMPriceModel(nn.Module):
    """
    Mode 12 + inflate_price: both embeddings at LLM dim.
    Output: concat(updated_LLM_pooled, updated_PRICE) at 2*LLM_dim → MLP.
    """

    def __init__(self, llm, price_embedder, llm_embed_size, hid_units,
                 branch_gate=False, residual_pred=False, delta_bound=0.0,
                 price_emb_dropout=0.0):
        super().__init__()
        self.llm = llm
        self.price = price_embedder  # InflatedBiCrossAttentionPRICEEmbedder
        # Read PRICE output dim from the embedder. At cx=0 it's query_hidden_dim
        # (e.g. 512); at cx>0 it's llm_hidden_dim (e.g. 384) since cross-attn
        # operates at LLM dim. This makes cx=0 produce the same MLP input as mode 7.
        price_output_dim = getattr(price_embedder, 'price_output_dim', llm_embed_size)
        combined_dim = llm_embed_size + price_output_dim
        from trainer import Prediction
        self.mlp = Prediction(combined_dim, hid_units)
        # Branch-level gate: scalar that scales the PRICE-side embedding
        # before concat. Init at 0 so the model starts equivalent to
        # `concat(LLM_pooled, zeros)`.
        self.branch_gate_enabled = branch_gate
        if branch_gate:
            self.price_branch_gate = nn.Parameter(torch.zeros(1))
        self.delta_bound = float(delta_bound)
        # Element-wise dropout on price_emb at training time. Forces the model
        # to predict from LLM alone with prob p, breaking template-specific
        # reliance on PRICE features.
        self.price_emb_drop = nn.Dropout(float(price_emb_dropout)) if price_emb_dropout > 0 else None
        # ResNet-style additive prediction:
        #   pred = base_mlp(LLM_pooled) + delta_mlp(concat(LLM, PRICE))
        # delta_mlp's final 1-d linear is zero-initialized so at init
        # delta_mlp output = 0 and the joint model's prediction is
        # *exactly* the LLM-only prediction (mode 2 equivalent). Training
        # opens up the delta only if it reduces loss; if PRICE never helps,
        # delta_mlp.out_mlp2 stays near 0 and biCross degrades gracefully.
        self.residual_pred = residual_pred
        if residual_pred:
            # Both MLPs return pre-sigmoid logits; we sum them and sigmoid at
            # the end. delta_mlp = self.mlp (over the concat input) has its
            # final linear zero-init, so at init delta_logit = 0 and the joint
            # model's prediction is exactly sigmoid(base_logit) — i.e., the
            # LLM-only prediction (mode 2 equivalent).
            self.mlp = Prediction(combined_dim, hid_units, no_sigmoid=True)
            self.base_mlp = Prediction(llm_embed_size, hid_units, no_sigmoid=True)
            nn.init.zeros_(self.mlp.out_mlp2.weight)
            nn.init.zeros_(self.mlp.out_mlp2.bias)

    def _pool_llm(self, llm_tokens, attn_mask):
        """Mean-pool LLM tokens with attention mask."""
        mask = attn_mask.unsqueeze(-1).float()
        pooled = (llm_tokens * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1)
        return pooled  # [B, llm_dim]

    def forward(self, x):
        texts, price_features, padding_mask, n_join_col, n_fanout, n_table, n_filter_col = x

        # When cx=0 (no cross-attn), use the same `self.llm(texts)` path as
        # mode 7 to get a byte-identical pooled embedding. forward_with_sequence
        # also returns hidden_states for cross-attn, but its sliding-window
        # logic differs slightly from forward()'s (different sub-batching),
        # which produces tiny numerical drift that compounds over 30 epochs.
        # At cx>0 we still need hidden_states, so use forward_with_sequence.
        _n_cx = len(self.price.cross_attn_blocks) if hasattr(self.price, 'cross_attn_blocks') else 0
        if _n_cx == 0:
            pooled_emb = self.llm(texts)
            hidden_states = None
            attn_mask = None
        else:
            pooled_emb, hidden_states, attn_mask = self.llm.forward_with_sequence(texts)
        if pooled_emb.dtype != torch.float32:
            pooled_emb = pooled_emb.float()

        price_emb, updated_llm, updated_mask = self.price(
            price_features, padding_mask, n_join_col, n_fanout, n_table, n_filter_col,
            llm_hidden_states=hidden_states, llm_attention_mask=attn_mask
        )

        if updated_llm is not None:
            # Match mode 7's pooling: CLS token + L2 normalize. The LLM forward
            # (utilsLLM.py:1486-1494 BERT branch) returns
            # F.normalize(hidden_states[:,0], p=2, dim=1) as pooled_emb. Using
            # mean-pool would put the embedding in a different space than mode 7.
            llm_emb = F.normalize(updated_llm[:, 0, :], p=2, dim=1)
        else:
            llm_emb = pooled_emb

        if self.branch_gate_enabled:
            price_emb = self.price_branch_gate * price_emb
        if self.price_emb_drop is not None:
            price_emb = self.price_emb_drop(price_emb)

        combined = torch.cat([llm_emb, price_emb], dim=1)
        if self.residual_pred:
            # base_mlp uses biCross-refined llm_emb (NOT pooled_emb). Empirically,
            # using pooled_emb causes the LLM to be pulled in two directions —
            # base wants pure-LLM features, delta wants biCross-fused features —
            # and test error degrades from ~1.7 to ~5.6. Sharing llm_emb keeps
            # both paths' gradients aligned through the same input.
            base_logit = self.base_mlp(llm_emb)
            delta_logit = self.mlp(combined)
            if self.delta_bound > 0:
                delta_logit = torch.tanh(delta_logit) * self.delta_bound
            return torch.sigmoid(base_logit + delta_logit)
        out = self.mlp(combined)
        # ─── Diagnostic: print first 5 batches' tensor stats (only in training mode) ─
        if self.training:
            _c = getattr(self, '_dbg_count', 0)
            if _c < 5:
                self._dbg_count = _c + 1
                _n_cx = len(self.price.cross_attn_blocks) if hasattr(self.price, 'cross_attn_blocks') else -1
                print(f"[Mode12-fwd b{_c} cx={_n_cx}] llm_emb mean={llm_emb.mean().item():.8f} std={llm_emb.std().item():.8f} norm={llm_emb.norm().item():.6f}")
                print(f"[Mode12-fwd b{_c} cx={_n_cx}] price_emb mean={price_emb.mean().item():.8f} std={price_emb.std().item():.8f} norm={price_emb.norm().item():.6f}")
                print(f"[Mode12-fwd b{_c} cx={_n_cx}] out mean={out.mean().item():.8f} samples={out[:, 0].detach().cpu().tolist()[:3]}")
        return out

    @torch.no_grad()
    def forward_embeddings(self, x):
        """Return combined [updated_llm_pooled, price_emb] before MLP."""
        texts, price_features, padding_mask, n_join_col, n_fanout, n_table, n_filter_col = x
        # Mirror forward(): at cx=0 use the standard llm forward (no need for
        # hidden_states); at cx>0 use forward_with_sequence to provide them.
        _n_cx = len(self.price.cross_attn_blocks) if hasattr(self.price, 'cross_attn_blocks') else 0
        if _n_cx == 0:
            pooled_emb = self.llm(texts)
            hidden_states = None
            attn_mask = None
        else:
            pooled_emb, hidden_states, attn_mask = self.llm.forward_with_sequence(texts)
        if pooled_emb.dtype != torch.float32:
            pooled_emb = pooled_emb.float()
        price_emb, updated_llm, updated_mask = self.price(
            price_features, padding_mask, n_join_col, n_fanout, n_table, n_filter_col,
            llm_hidden_states=hidden_states, llm_attention_mask=attn_mask
        )
        if updated_llm is not None:
            llm_emb = F.normalize(updated_llm[:, 0, :], p=2, dim=1)
        else:
            llm_emb = pooled_emb
        if self.branch_gate_enabled:
            price_emb = self.price_branch_gate * price_emb
        return torch.cat([llm_emb, price_emb], dim=1)


class BiCrossAttentionLLMPriceModel(nn.Module):
    """
    Joint model with bidirectional cross-attention fusion (Mode 12).
    PRICE tokens attend to LLM hidden states AND LLM tokens attend to PRICE tokens.
    The refined LLM tokens are mean-pooled and projected to replace the original
    LLM pooled embedding, then concatenated with the enriched PRICE embedding
    for the MLP head.
    """

    def __init__(self, llm, price_embedder, llm_embed_size, price_embed_size, hid_units,
                 triple_concat=False, branch_gate=False, residual_pred=False, delta_bound=0.0,
                 price_emb_dropout=0.0):
        super().__init__()
        self.llm = llm
        self.price = price_embedder  # BiCrossAttentionPRICEEmbedder
        self.triple_concat = triple_concat
        self.n_embd = price_embedder.cross_attn_blocks[0].norm1.normalized_shape[0]  # 256

        if triple_concat:
            # Concatenate: original LLM + refined LLM (256) + PRICE
            self.refined_llm_proj = None
            combined_dim = llm_embed_size + self.n_embd + price_embed_size
        else:
            # Original: project refined LLM to llm_embed_size, concat with PRICE
            self.refined_llm_proj = nn.Linear(self.n_embd, llm_embed_size)
            combined_dim = llm_embed_size + price_embed_size

        from trainer import Prediction
        self.mlp = Prediction(combined_dim, hid_units)
        self.branch_gate_enabled = branch_gate
        if branch_gate:
            self.price_branch_gate = nn.Parameter(torch.zeros(1))
        # ResNet additive prediction (see InflatedBiCrossAttentionLLMPriceModel)
        self.residual_pred = residual_pred
        if residual_pred:
            self.mlp = Prediction(combined_dim, hid_units, no_sigmoid=True)
            self.base_mlp = Prediction(llm_embed_size, hid_units, no_sigmoid=True)
            nn.init.zeros_(self.mlp.out_mlp2.weight)
            nn.init.zeros_(self.mlp.out_mlp2.bias)
        self.delta_bound = float(delta_bound)
        self.price_emb_drop = nn.Dropout(float(price_emb_dropout)) if price_emb_dropout > 0 else None

    def _pool_refined_llm(self, refined_llm, attn_mask):
        """Mean-pool refined LLM tokens with attention mask."""
        # refined_llm: [B, T, 256], attn_mask: [B, T]
        mask = attn_mask.unsqueeze(-1).float()  # [B, T, 1]
        pooled = (refined_llm * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1)  # [B, 256]
        if self.refined_llm_proj is not None:
            return self.refined_llm_proj(pooled)  # [B, llm_embed_size]
        return pooled  # [B, 256]

    def forward(self, x):
        """
        Args:
            x: tuple of (texts, price_features, padding_mask, n_join_col, n_fanout, n_table, n_filter_col)
        """
        texts, price_features, padding_mask, n_join_col, n_fanout, n_table, n_filter_col = x

        # LLM: get both pooled embedding and hidden states
        pooled_emb, hidden_states, attn_mask = self.llm.forward_with_sequence(texts)
        if pooled_emb.dtype != torch.float32:
            pooled_emb = pooled_emb.float()

        # PRICE embedding with bidirectional cross-attention to LLM hidden states
        price_emb, refined_llm, refined_mask = self.price(
            price_features, padding_mask, n_join_col, n_fanout, n_table, n_filter_col,
            llm_hidden_states=hidden_states, llm_attention_mask=attn_mask
        )

        # Apply PRICE-branch gate if enabled
        if self.branch_gate_enabled:
            price_emb = self.price_branch_gate * price_emb
        if self.price_emb_drop is not None:
            price_emb = self.price_emb_drop(price_emb)

        # Combine LLM + PRICE embeddings
        if self.triple_concat:
            # Triple: original LLM + refined LLM (256) + PRICE
            if refined_llm is not None:
                refined_llm_emb = self._pool_refined_llm(refined_llm, refined_mask)
                combined = torch.cat([pooled_emb, refined_llm_emb, price_emb], dim=1)
            else:
                zeros = torch.zeros(pooled_emb.size(0), self.n_embd, device=pooled_emb.device)
                combined = torch.cat([pooled_emb, zeros, price_emb], dim=1)
        else:
            # Original: refined LLM (projected to llm_size) + PRICE
            if refined_llm is not None:
                llm_emb = self._pool_refined_llm(refined_llm, refined_mask)
            else:
                llm_emb = pooled_emb
            combined = torch.cat([llm_emb, price_emb], dim=1)
        if self.residual_pred:
            base_logit = self.base_mlp(pooled_emb)
            delta_logit = self.mlp(combined)
            if self.delta_bound > 0:
                delta_logit = torch.tanh(delta_logit) * self.delta_bound
            return torch.sigmoid(base_logit + delta_logit)
        return self.mlp(combined)

    @torch.no_grad()
    def forward_embeddings(self, x):
        """Return combined [refined_llm_emb, price_emb] before MLP."""
        texts, price_features, padding_mask, n_join_col, n_fanout, n_table, n_filter_col = x
        pooled_emb, hidden_states, attn_mask = self.llm.forward_with_sequence(texts)
        if pooled_emb.dtype != torch.float32:
            pooled_emb = pooled_emb.float()
        price_emb, refined_llm, refined_mask = self.price(
            price_features, padding_mask, n_join_col, n_fanout, n_table, n_filter_col,
            llm_hidden_states=hidden_states, llm_attention_mask=attn_mask
        )
        if self.triple_concat:
            if refined_llm is not None:
                refined_llm_emb = self._pool_refined_llm(refined_llm, refined_mask)
                return torch.cat([pooled_emb, refined_llm_emb, price_emb], dim=1)
            else:
                zeros = torch.zeros(pooled_emb.size(0), self.n_embd, device=pooled_emb.device)
                return torch.cat([pooled_emb, zeros, price_emb], dim=1)
        else:
            if refined_llm is not None:
                llm_emb = self._pool_refined_llm(refined_llm, refined_mask)
            else:
                llm_emb = pooled_emb
            return torch.cat([llm_emb, price_emb], dim=1)
