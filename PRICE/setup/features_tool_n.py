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
        # Build reverse mapping: price_alias -> raw_table_name
        # (used to look up null_fraction keys which use raw table names)
        abbrev = self.information_coltype.get("abbrev", {})
        self._alias_to_table = {v: k for k, v in abbrev.items()}

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

    # ---- filter token (rules a, b) ----

    EMPTY_ATOMS = {
        "eq_values": [], "in_values": [], "not_in_values": [],
        "range_low": None, "range_high": None,
        "is_null": False, "is_not_null": False, "like_keys": [],
    }

    def _value_selectivity_continuous(self, column: str, value) -> Tuple[float, float, float]:
        """For a continuous column, map a single value to (low_norm, high_norm, sel)."""
        bin_edges = self.columns_bin_edges[column]
        try:
            v = float(value)
        except (TypeError, ValueError):
            return 0.0, 0.0, 0.0
        rng = bin_edges[-1] - bin_edges[0]
        rng = rng or 1.0
        low_norm = (v - bin_edges[0]) / rng
        high_norm = (v + 1e-5 - bin_edges[0]) / rng
        low_norm = max(0.0, min(1.0, low_norm))
        high_norm = max(0.0, min(1.0, high_norm))
        dist = self.columns_distributions[column]
        sel = self.calculate_hist_selectivity(dist, bin_edges, v, v + 1e-5)
        sel = sel / max(1.0, dist.sum())
        return low_norm, high_norm, max(0.0, min(1.0, float(sel)))

    def _value_selectivity_discrete(self, column: str, value,
                                    keys, vals, table_size: int) -> Tuple[float, float, float]:
        """For a discrete column, map a value to (low_norm, high_norm, sel)
        via the SpaceSaving summary."""
        try:
            idx = keys.index(value)
            freq = vals[idx]
        except ValueError:
            idx = len(keys) - 1   # OtHeRs
            freq = vals[-1]
        low = idx / self.bin_size
        high = (idx + 1) / self.bin_size
        sel = float(freq) / max(1.0, table_size)
        return low, high, max(0.0, min(1.0, sel))

    def _populate_in_slots(self, column: str, values: Sequence,
                           is_discrete: bool, keys, vals, table_size: int):
        """Sort by selectivity, take top K, fold remainder into tail."""
        triples = []
        for v in values:
            if is_discrete:
                triples.append(self._value_selectivity_discrete(
                    column, v, keys, vals, table_size))
            else:
                triples.append(self._value_selectivity_continuous(column, v))
        triples.sort(key=lambda t: t[2], reverse=True)
        top = triples[: self.K]
        tail = triples[self.K:]
        slots = []
        for low, high, sel in top:
            slots.extend([low, high, sel])
        while len(slots) < self.K * 3:
            slots.extend([0.0, 0.0, 0.0])
        if tail:
            tail_low = min(t[0] for t in tail)
            tail_high = max(t[1] for t in tail)
            tail_sel = sum(t[2] for t in tail)
            slots.extend([tail_low, tail_high, min(1.0, tail_sel)])
        else:
            slots.extend([0.0, 0.0, 0.0])
        return slots  # 3*(K+1) = 33 floats

    def _encode_filter_token(self, filter_column: str, atoms: dict) -> torch.Tensor:
        """Build a 75-dim filter token from the atoms dict produced by the
        AST tag pass.

        atoms keys:
          eq_values    : list  — single-equality literal(s)
          in_values    : list  — IN-list literals
          not_in_values: list  — NOT IN literals (selectivity 1 - matched)
          range_low    : float | None
          range_high   : float | None
          is_null      : bool
          is_not_null  : bool
          like_keys    : list  — SpaceSaving keys matched by LIKE/NOT LIKE
        """
        col_table = filter_column.split(".")[0]
        col_name = filter_column.split(".")[-1]
        table_size = self.get_table_size(col_table)
        is_discrete = col_name in self.information_coltype['col_type'][col_table]['dsct']

        if is_discrete:
            keys, vals = self.space_saving_summary(filter_column)
            histogram = (torch.tensor(vals, dtype=torch.float32) / max(1.0, table_size))
        else:
            histogram = torch.tensor(
                self.get_column_histograms(filter_column), dtype=torch.float32)

        # Combine all multi-valued atoms (eq + in + like_keys minus not_in/not_like)
        # We treat eq + in + like as a positive list to populate the K slots.
        positive_values = list(atoms.get("eq_values", [])) + \
                          list(atoms.get("in_values", [])) + \
                          list(atoms.get("like_keys", []))

        if positive_values:
            slot_floats = self._populate_in_slots(
                filter_column, positive_values, is_discrete,
                keys=keys if is_discrete else None,
                vals=vals if is_discrete else None,
                table_size=table_size)
        elif atoms.get("range_low") is not None or atoms.get("range_high") is not None:
            # Range predicate: fill slot 1 only.
            bin_edges = self.columns_bin_edges.get(filter_column)
            slot_floats = [0.0] * (3 * (self.K + 1))
            if bin_edges is not None:
                lo = atoms.get("range_low")
                hi = atoms.get("range_high")
                lo_v = float(lo) if lo is not None else float(bin_edges[0])
                hi_v = float(hi) if hi is not None else float(bin_edges[-1])
                rng = max(1e-9, bin_edges[-1] - bin_edges[0])
                lo_n = max(0.0, min(1.0, (lo_v - bin_edges[0]) / rng))
                hi_n = max(0.0, min(1.0, (hi_v - bin_edges[0]) / rng))
                if lo_n > hi_n: lo_n = hi_n
                dist = self.columns_distributions[filter_column]
                sel = self.calculate_hist_selectivity(dist, bin_edges, lo_v, hi_v)
                sel = float(sel) / max(1.0, dist.sum())
                slot_floats[0:3] = [lo_n, hi_n, max(0.0, min(1.0, sel))]
        else:
            # Pure NULL or empty atoms: all slots zero.
            slot_floats = [0.0] * (3 * (self.K + 1))

        # NULL bits (rule b)
        # null_fraction keys use raw table names; resolve alias via _alias_to_table
        raw_table = self._alias_to_table.get(col_table, col_table)
        null_fraction = float(self._null_fraction.get((raw_table, col_name), 0.0))
        if atoms.get("is_null"):
            null_pred_flag = 1.0
        elif atoms.get("is_not_null"):
            null_pred_flag = -1.0
        else:
            null_pred_flag = 0.0

        feature = torch.cat([
            histogram,
            torch.tensor(slot_floats, dtype=torch.float32),
            torch.tensor([null_fraction, null_pred_flag], dtype=torch.float32),
        ])
        assert feature.shape[0] == self.filter_dim_n, \
            f"filter token shape {feature.shape[0]} != {self.filter_dim_n}"
        return feature
