"""
Joint LLM + PRICE model for query cost/cardinality prediction.

Architecture:
  Query Plan Text --> LLM (LoRA) --> D_llm embedding --+
                                                        +--> Concat --> MLP --> Prediction
  SQL + Stats ------> PRICE (full) --> 512-dim embedding-+
"""

import sys
import torch
import torch.nn as nn
import torch.nn.functional as F

PRICE_ROOT = "/root/PRICE"
if PRICE_ROOT not in sys.path:
    sys.path.insert(0, PRICE_ROOT)


class PRICEEmbedder(nn.Module):
    """
    Wraps PRICE's RegressionModel layers up to and including the ELU activation.
    Returns 512-dim query_output embedding (query_hidden_dim).

    Copies these layers from a loaded RegressionModel:
      scale_embedding, filter_embedding, scale_encoder, filter_encoder,
      len_net, linear, elu
    """

    def __init__(self, regression_model):
        """
        Args:
            regression_model: A loaded PRICE RegressionModel instance.
        """
        super().__init__()
        self.n_join_col = regression_model.n_join_col
        self.n_fanout = regression_model.n_fanout
        self.n_table = regression_model.n_table
        self.n_filter_col = regression_model.n_filter_col
        self.hist_dim = regression_model.hist_dim
        self.table_dim = regression_model.table_dim
        self.dropout_rate = regression_model.dropout_rate

        # Copy the embedding layers
        self.scale_embedding = regression_model.scale_embedding
        self.filter_embedding = regression_model.filter_embedding
        self.scale_encoder = regression_model.scale_encoder
        self.filter_encoder = regression_model.filter_encoder
        self.len_net = regression_model.len_net
        self.linear = regression_model.linear
        self.elu = regression_model.elu

    def forward(self, x, padding_mask, n_join_col, n_fanout, n_table, n_filter_col):
        """
        Args:
            x: [B, feature_dim] padded PRICE features
            padding_mask: [B, max_n_feature+1]
            n_join_col: [B, 1]
            n_fanout: [B, 1]
            n_table: [B, 1]
            n_filter_col: [B, 1]

        Returns:
            query_output: [B, query_hidden_dim] (512-dim embedding)
        """
        # Scaling stage
        scale_features = self.scale_embedding(x)
        masks1 = padding_mask[:, :1 + self.n_join_col + self.n_fanout] if padding_mask is not None else None
        scaling_output = self.scale_encoder(scale_features, masks1)

        # Filtering stage
        filter_features = self.filter_embedding(scaling_output, x)
        masks2 = padding_mask[:, :] if padding_mask is not None else None
        filtering_output = self.filter_encoder(filter_features, masks2)
        query_output = filtering_output[:, 0, :]

        # Length features
        len_features = torch.cat([n_join_col, n_fanout, n_table, n_filter_col], dim=1)
        len_features = self.len_net(len_features)

        # Linear + ELU
        query_output = self.linear(torch.cat([query_output, len_features], dim=1))
        query_output = self.elu(query_output)
        query_output = F.dropout(query_output, p=self.dropout_rate, training=self.training)

        return query_output  # [B, 512]


class LLMPriceJointModel(nn.Module):
    """
    Joint model: LLM embeddings + PRICE embeddings --> MLP --> prediction.

    The forward method receives a tuple:
      (texts, price_features, padding_mask, n_join_col, n_fanout, n_table, n_filter_col)
    """

    def __init__(self, llm, price_embedder, llm_embed_size, price_embed_size, hid_units):
        """
        Args:
            llm: QueryPlanPredictor (with LoRA) that takes text and returns embeddings
            price_embedder: PRICEEmbedder instance
            llm_embed_size: LLM hidden dim
            price_embed_size: PRICE embedding dim (512)
            hid_units: MLP hidden dimension
        """
        super().__init__()
        self.llm = llm
        self.price = price_embedder
        combined_dim = llm_embed_size + price_embed_size
        # Import Prediction from trainer
        from trainer import Prediction
        self.mlp = Prediction(combined_dim, hid_units)

    def forward(self, x):
        """
        Args:
            x: tuple of (texts, price_features, padding_mask, n_join_col, n_fanout, n_table, n_filter_col)

        Returns:
            prediction: [B, 1]
        """
        texts, price_features, padding_mask, n_join_col, n_fanout, n_table, n_filter_col = x

        # LLM embedding
        llm_emb = self.llm(texts)  # [B, D_llm]
        if llm_emb.dtype != torch.float32:
            llm_emb = llm_emb.float()

        # PRICE embedding
        price_emb = self.price(price_features, padding_mask, n_join_col, n_fanout, n_table, n_filter_col)  # [B, 512]

        # Concatenate and predict
        combined = torch.cat([llm_emb, price_emb], dim=1)
        return self.mlp(combined)


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
        price_emb = self.price(price_features, padding_mask, n_join_col, n_fanout, n_table, n_filter_col)
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

        # PRICE embedding
        price_emb = self.price(price_features, padding_mask, n_join_col, n_fanout, n_table, n_filter_col)

        # Concatenate and predict
        combined = torch.cat([llm_emb, price_emb], dim=1)
        return self.mlp(combined)


class PRICEFinetunWrapper(nn.Module):
    """
    Wrapper for finetuning PRICE's RegressionModel on cardinality estimation.

    Accepts a tuple (price_feats, pg_est_cards, pad_masks, njcs, nfos, ntbs, nfcs)
    and unpacks it for RegressionModel.forward().
    """

    def __init__(self, regression_model):
        super().__init__()
        self.model = regression_model

    def forward(self, x):
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
    """Pre-norm cross-attention + pre-norm FFN with residual connections."""

    def __init__(self, n_embd, n_heads, dropout_rate):
        super().__init__()
        self.norm1 = nn.LayerNorm(n_embd)
        self.cross_attn = MultiHeadCrossAttention(
            n_heads, n_embd // n_heads, n_embd, dropout_rate
        )
        self.norm2 = nn.LayerNorm(n_embd)
        self.feed_forward = FeedForward(n_embd)
        self.dropout_rate = dropout_rate

    def forward(self, query_tokens, kv_tokens, kv_mask=None):
        # Pre-norm cross-attention with residual
        normed = self.norm1(query_tokens)
        attn_out = self.cross_attn(normed, kv_tokens, kv_mask)
        attn_out = F.dropout(attn_out, p=self.dropout_rate, training=self.training)
        x = query_tokens + attn_out

        # Pre-norm FFN with residual
        normed = self.norm2(x)
        ff_out = self.feed_forward(normed)
        ff_out = F.dropout(ff_out, p=self.dropout_rate, training=self.training)
        return x + ff_out


class CrossAttentionPRICEEmbedder(nn.Module):
    """
    Like PRICEEmbedder but adds cross-attention layers that let PRICE tokens
    attend to LLM hidden states after the filter encoder, before CLS extraction.
    """

    def __init__(self, regression_model, llm_hidden_dim, n_cross_layers=2,
                 n_embd=256, n_heads=8, dropout_rate=0.1):
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
            CrossAttentionBlock(n_embd, n_heads, dropout_rate)
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
                 n_embd=256, n_heads=8, dropout_rate=0.1):
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
            CrossAttentionBlock(n_embd, n_heads, dropout_rate)
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


class BiCrossAttentionLLMPriceModel(nn.Module):
    """
    Joint model with bidirectional cross-attention fusion (Mode 12).
    PRICE tokens attend to LLM hidden states AND LLM tokens attend to PRICE tokens.
    The refined LLM tokens are mean-pooled and projected to replace the original
    LLM pooled embedding, then concatenated with the enriched PRICE embedding
    for the MLP head.
    """

    def __init__(self, llm, price_embedder, llm_embed_size, price_embed_size, hid_units):
        super().__init__()
        self.llm = llm
        self.price = price_embedder  # BiCrossAttentionPRICEEmbedder
        # Project mean-pooled refined LLM tokens (n_embd=256) → llm_embed_size
        n_embd = price_embedder.cross_attn_blocks[0].norm1.normalized_shape[0]  # 256
        self.refined_llm_proj = nn.Linear(n_embd, llm_embed_size)
        combined_dim = llm_embed_size + price_embed_size
        from trainer import Prediction
        self.mlp = Prediction(combined_dim, hid_units)

    def _pool_refined_llm(self, refined_llm, attn_mask):
        """Mean-pool refined LLM tokens with attention mask."""
        # refined_llm: [B, T, 256], attn_mask: [B, T]
        mask = attn_mask.unsqueeze(-1).float()  # [B, T, 1]
        pooled = (refined_llm * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1)  # [B, 256]
        return self.refined_llm_proj(pooled)  # [B, llm_embed_size]

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

        # Use refined LLM embedding if available, otherwise fall back to original
        if refined_llm is not None:
            llm_emb = self._pool_refined_llm(refined_llm, refined_mask)
        else:
            llm_emb = pooled_emb

        # Concatenate and predict
        combined = torch.cat([llm_emb, price_emb], dim=1)
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
        if refined_llm is not None:
            llm_emb = self._pool_refined_llm(refined_llm, refined_mask)
        else:
            llm_emb = pooled_emb
        return torch.cat([llm_emb, price_emb], dim=1)
