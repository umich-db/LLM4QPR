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
