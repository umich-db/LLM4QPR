"""PRICE_N: full hybrid PRICE-LLM SQL feature extractor.

filter_dim         = bin_size + 3*(K+1) + 2 = 75   (K = 10)
fanout_dim         = bin_size + 2          = 42
pairwise_intra_dim = 8*8 + 8*8 + 1         = 129

See /root/LLM4QPR/docs/superpowers/specs/2026-05-02-price-n-parsing-rules-design.md
for the full design.
"""
import os
import pickle
import re
from typing import Optional, Sequence, Tuple

import numpy as np
import torch
import sqlglot

from setup.features_tool import Sql2Feature


class Sql2FeatureN(Sql2Feature):
    """PRICE_N feature extractor.

    Subclass of Sql2Feature that does NOT inherit from Sql2FeatureM (PRICE_N's
    IN-list slot rule differs fundamentally from PRICE_M's frequency-ordered
    encoding).
    """

    K = 10
    PAIRWISE_GRID = 8

    def __init__(self, database: str, bin_size: int, usage: str):
        super().__init__(database, bin_size, usage)
        self._null_fraction = self._safe_load_pkl("null_fraction.pkl") or {}
        # Fanout file already loaded by parent into self.information_fanout.
        # The orphan dict (added by Task 4) is nested under '__orphan__'.
        self._orphan_fraction = self.information_fanout.get("__orphan__", {})
        self._pairwise_intra = self._safe_load_pkl("pairwise_intra40.pkl") or {}
        self._pairwise_xtab = self._safe_load_pkl("nonequi_pair_xtab.pkl") or {}
        self._nonequi_fanout_op = self._safe_load_pkl(
            "nonequi_fanout_op40.pkl") or {}

    @property
    def filter_dim_n(self) -> int:
        return self.bin_size + 3 * (self.K + 1) + 2

    @property
    def fanout_dim_n(self) -> int:
        return self.bin_size + 2

    @property
    def pairwise_dim_n(self) -> int:
        return self.PAIRWISE_GRID ** 2 * 2 + 1

    def _safe_load_pkl(self, fname: str):
        """Load a stats pkl if present; return None if missing (lets pre-stats
        environments still construct the class for unit tests)."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        path = (f'{current_dir}/../datas/statistics/{self.usage}/'
                f'{self.database}/{fname}')
        if not os.path.exists(path):
            return None
        with open(path, 'rb') as f:
            return pickle.load(f)
