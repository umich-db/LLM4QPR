"""PRICE_N: full hybrid PRICE-LLM SQL feature extractor.

filter_dim         = bin_size + 3*(K+1) + 2 = 75   (K = 10)
fanout_dim         = bin_size + 2          = 42
pairwise_intra_dim = 64 + 2*3              = 70  (anti-diagonal range-slot format)

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
        # 64-dim anti-diagonal H_xy + 2 range slots × (low, high, sel) = 70
        return 64 + 2 * 3

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
        "is_null": False, "is_not_null": False,
        "or_atoms": [],   # list of (op, value) tuples for same-column disjunctions
        # Note: LIKE/NOT LIKE/ILIKE go to LLM residual under PRICE_N (rule a
        # extension does not encode them).
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

    def _atom_to_slot(self, op: str, value, column: str,
                      is_discrete: bool, keys, vals, table_size: int
                      ) -> Tuple[float, float, float]:
        """Convert a single (op, value) atom to a (low, high, sel) range slot.

        Used to encode same-column OR chains from the or_atoms field.
        """
        if is_discrete:
            try:
                idx = keys.index(value)
                freq = vals[idx]
            except ValueError:
                idx = len(keys) - 1
                freq = vals[-1]
            bin_lo = idx / self.bin_size
            bin_hi = (idx + 1) / self.bin_size
            sel_unit = float(freq) / max(1.0, table_size)
            if op == "=":
                return bin_lo, bin_hi, max(0.0, min(1.0, sel_unit))
            elif op in ("<", "<="):
                # Everything before this bin
                lo_norm = 0.0
                hi_norm = bin_hi if op == "<=" else bin_lo
                gap_sel = sum(float(vals[b]) for b in range(0, idx + (1 if op == "<=" else 0))
                              if b < len(vals)) / max(1.0, table_size)
                return lo_norm, hi_norm, max(0.0, min(1.0, gap_sel))
            elif op in (">", ">="):
                lo_norm = bin_lo if op == ">=" else bin_hi
                hi_norm = 1.0
                start = idx if op == ">=" else idx + 1
                gap_sel = sum(float(vals[b]) for b in range(start, len(vals))) / max(1.0, table_size)
                return lo_norm, hi_norm, max(0.0, min(1.0, gap_sel))
            else:
                return 0.0, 0.0, 0.0
        else:
            bin_edges = self.columns_bin_edges.get(column)
            if bin_edges is None:
                return 0.0, 0.0, 0.0
            try:
                v = float(value)
            except (TypeError, ValueError):
                return 0.0, 0.0, 0.0
            lo_edge = float(bin_edges[0])
            hi_edge = float(bin_edges[-1])
            rng = max(1e-9, hi_edge - lo_edge)
            dist = self.columns_distributions.get(column)
            if dist is None:
                return 0.0, 0.0, 0.0
            dist_sum = max(1.0, float(dist.sum()))
            v_norm = max(0.0, min(1.0, (v - lo_edge) / rng))

            if op == "=":
                lo_n = v_norm
                hi_n = min(1.0, v_norm + 1e-5)
                sel = self.calculate_hist_selectivity(dist, bin_edges, v, v + 1e-5)
                sel = float(sel) / dist_sum
            elif op == "<":
                lo_n, hi_n = 0.0, v_norm
                sel = self.calculate_hist_selectivity(dist, bin_edges, lo_edge, v)
                sel = float(sel) / dist_sum
            elif op == "<=":
                lo_n, hi_n = 0.0, min(1.0, v_norm + 1e-5)
                sel = self.calculate_hist_selectivity(dist, bin_edges, lo_edge, v + 1e-5)
                sel = float(sel) / dist_sum
            elif op == ">":
                lo_n, hi_n = min(1.0, v_norm + 1e-5), 1.0
                sel = self.calculate_hist_selectivity(dist, bin_edges, v + 1e-5, hi_edge)
                sel = float(sel) / dist_sum
            elif op == ">=":
                lo_n, hi_n = v_norm, 1.0
                sel = self.calculate_hist_selectivity(dist, bin_edges, v, hi_edge)
                sel = float(sel) / dist_sum
            else:
                return 0.0, 0.0, 0.0
            return lo_n, hi_n, max(0.0, min(1.0, sel))

    def _populate_range_pair_slots(self, column: str, not_in_values: Sequence,
                                   is_discrete: bool, keys, vals,
                                   table_size: int):
        """Build N+1 range slots for `col != X` (and multi-NEQ) predicates.

        For continuous columns, sorts the excluded values numerically and emits
        slots covering the gaps between them (below first, between each pair,
        above last).

        For discrete columns, uses SpaceSaving bin indices as positions.

        Returns a list of 3*(K+1) = 33 floats, same layout as _populate_in_slots.
        """
        eps = 1e-6
        slots: list = []

        if is_discrete:
            # Map each excluded value to its SpaceSaving bin index.
            excluded_bins = []
            for v in not_in_values:
                try:
                    idx = keys.index(v)
                except ValueError:
                    idx = len(keys) - 1  # OtHeRs bin
                excluded_bins.append(idx)
            excluded_bins = sorted(set(excluded_bins))
            n_bins = self.bin_size  # typically 40

            # Build gap ranges: (lo_bin_incl, hi_bin_excl)
            boundaries = [-1] + excluded_bins + [n_bins]
            for i in range(len(boundaries) - 1):
                lo_bin = boundaries[i] + 1
                hi_bin = boundaries[i + 1]  # exclusive
                if lo_bin > hi_bin:
                    continue
                lo_norm = lo_bin / n_bins
                hi_norm = hi_bin / n_bins
                # Selectivity: sum of freq for bins [lo_bin, hi_bin)
                gap_sel = 0.0
                for b in range(lo_bin, hi_bin):
                    if b < len(vals):
                        gap_sel += float(vals[b]) / max(1.0, table_size)
                slots.append((lo_norm, hi_norm, min(1.0, gap_sel)))
        else:
            # Continuous: sort excluded values numerically.
            try:
                excl_sorted = sorted(float(v) for v in not_in_values)
            except (TypeError, ValueError):
                return [0.0] * (3 * (self.K + 1))
            bin_edges = self.columns_bin_edges.get(column)
            if bin_edges is None:
                return [0.0] * (3 * (self.K + 1))
            lo_edge = float(bin_edges[0])
            hi_edge = float(bin_edges[-1])
            rng = max(1e-9, hi_edge - lo_edge)
            dist = self.columns_distributions[column]
            dist_sum = max(1.0, dist.sum())

            # Boundaries including sentinel min/max
            boundaries = [lo_edge] + excl_sorted + [hi_edge]
            for i in range(len(boundaries) - 1):
                lo_v = boundaries[i] + (eps if i > 0 else 0.0)
                hi_v = boundaries[i + 1] - (eps if i < len(boundaries) - 2 else 0.0)
                if lo_v > hi_v:
                    continue
                lo_norm = max(0.0, min(1.0, (lo_v - lo_edge) / rng))
                hi_norm = max(0.0, min(1.0, (hi_v - lo_edge) / rng))
                sel = self.calculate_hist_selectivity(dist, bin_edges, lo_v, hi_v)
                sel = float(sel) / dist_sum
                slots.append((lo_norm, hi_norm, max(0.0, min(1.0, sel))))

        # Fill top K slots sorted by selectivity descending, remainder goes to tail.
        slots.sort(key=lambda t: t[2], reverse=True)
        top = slots[: self.K]
        tail = slots[self.K:]
        result = []
        for lo, hi, sel in top:
            result.extend([lo, hi, sel])
        while len(result) < self.K * 3:
            result.extend([0.0, 0.0, 0.0])
        if tail:
            tail_lo = min(t[0] for t in tail)
            tail_hi = max(t[1] for t in tail)
            tail_sel = sum(t[2] for t in tail)
            result.extend([tail_lo, tail_hi, min(1.0, tail_sel)])
        else:
            result.extend([0.0, 0.0, 0.0])
        return result  # 3*(K+1) = 33 floats

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
                          list(atoms.get("in_values", []))
        not_in_values = list(atoms.get("not_in_values", []))

        if positive_values:
            # Positive path dominates: EQ/IN is more selective than NEQ.
            # If both positive and NEQ are present, prefer positive (degenerate case).
            slot_floats = self._populate_in_slots(
                filter_column, positive_values, is_discrete,
                keys=keys if is_discrete else None,
                vals=vals if is_discrete else None,
                table_size=table_size)
        elif not_in_values:
            # NEQ range-pair encoding: col != X (rule a extension).
            slot_floats = self._populate_range_pair_slots(
                filter_column, not_in_values, is_discrete,
                keys=keys if is_discrete else None,
                vals=vals if is_discrete else None,
                table_size=table_size)
        elif atoms.get("or_atoms"):
            # Same-column OR chain: each (op, value) pair becomes one slot.
            # Used for NOT BETWEEN expansions and mixed-op same-column ORs.
            or_atom_list = atoms["or_atoms"]
            triples = []
            for op, val in or_atom_list:
                lo, hi, sel = self._atom_to_slot(
                    op, val, filter_column, is_discrete,
                    keys if is_discrete else None,
                    vals if is_discrete else None,
                    table_size)
                triples.append((lo, hi, sel))
            # Sort by selectivity descending; top K go to explicit slots.
            triples.sort(key=lambda t: t[2], reverse=True)
            top = triples[: self.K]
            tail = triples[self.K:]
            slot_floats = []
            for lo, hi, sel in top:
                slot_floats.extend([lo, hi, sel])
            while len(slot_floats) < self.K * 3:
                slot_floats.extend([0.0, 0.0, 0.0])
            if tail:
                slot_floats.extend([min(t[0] for t in tail),
                                    max(t[1] for t in tail),
                                    min(1.0, sum(t[2] for t in tail))])
            else:
                slot_floats.extend([0.0, 0.0, 0.0])
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

    # ---- extended fanout token (rule g) ----

    _PRESERVE_TABLE = {
        # side -> (preserve_LR, preserve_RL)
        "INNER": (0.0, 0.0),
        "LEFT":  (1.0, 0.0),
        "RIGHT": (0.0, 1.0),
        "FULL":  (1.0, 1.0),
    }

    def _encode_fanout_tokens_extended(self, join: str, side: str = "INNER"
                                       ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Return (fanout_LR, fanout_RL) each a 42-dim tensor.

        Layout: [raw_fanout_hist[0:40], orphan_fraction, outer_preserve_flag].

        Pretrained PRICE consumes only the 40-dim raw histogram; the 2 new
        dims are zero-filled when the orphan stats are missing or for INNER
        joins.
        """
        ff1, ff2 = self.get_fanout_features(join)
        ff1_t = torch.tensor(ff1, dtype=torch.float32)
        ff2_t = torch.tensor(ff2, dtype=torch.float32)
        if ff1_t.shape[0] != self.bin_size:
            ff1_t = torch.nn.functional.pad(
                ff1_t[:self.bin_size], (0, self.bin_size - ff1_t.shape[0]))
        if ff2_t.shape[0] != self.bin_size:
            ff2_t = torch.nn.functional.pad(
                ff2_t[:self.bin_size], (0, self.bin_size - ff2_t.shape[0]))

        left_join, right_join = join.split(" = ")[0], join.split(" = ")[1]
        orph_lr, orph_rl = self._orphan_fraction.get(
            (left_join, right_join), (0.0, 0.0))
        preserve_lr, preserve_rl = self._PRESERVE_TABLE.get(
            side.upper(), (0.0, 0.0))

        f_lr = torch.cat([ff1_t,
                          torch.tensor([orph_lr, preserve_lr],
                                       dtype=torch.float32)])
        f_rl = torch.cat([ff2_t,
                          torch.tensor([orph_rl, preserve_rl],
                                       dtype=torch.float32)])
        return f_lr, f_rl

    # ---- pairwise intra/cross-table filter token (rules h, j) ----

    # Operator → range slots in the anti-diagonal-ordered 64-vector.
    # Format: list of (lo_bin, hi_bin) inclusive bounds.
    _OP_RANGES = {
        "<":  [(0, 27)],
        "<=": [(0, 35)],
        "=":  [(28, 35)],
        "!=": [(0, 27), (36, 63)],
        ">":  [(36, 63)],
        ">=": [(28, 63)],
    }

    def _encode_pairwise_intra_token(self, left_table: str, col_x: str,
                                     col_y: str, op: Optional[str] = None,
                                     right_table: Optional[str] = None,
                                     right_col: Optional[str] = None) -> torch.Tensor:
        """Build a 70-dim pairwise filter token using anti-diagonal range slots.

        Format: H_xy[64] + 2 range slots (low, high, sel) = 70 dims.
        For self-pairs (right_table is None or == left_table), draws H from
        pairwise_intra40.pkl. For cross-table pairs (rule h), draws from
        nonequi_pair_xtab.pkl.

        The H_xy vector uses anti-diagonal ordering (see
        _order_8x8_anti_diagonal in generate_price_stats_from_pg.py).
        Operators map to 1 or 2 contiguous bin ranges via _OP_RANGES.
        """
        # Auto-detect xtab calling convention (op passed as 3rd positional)
        if right_table is not None and right_table != left_table and op is None:
            op = col_y
            col_y = None

        if right_table is None or right_table == left_table:
            rec = self._pairwise_intra.get((left_table, col_x, col_y))
        else:
            rec = self._pairwise_xtab.get(
                (left_table, col_x, right_table, right_col))

        if rec is None:
            return torch.zeros(self.pairwise_dim_n, dtype=torch.float32)

        H = torch.tensor(rec["H8x8_ordered"], dtype=torch.float32)
        if H.shape != (64,):
            H = H.flatten()[:64]

        total_mass = float(H.sum().item()) or 1.0
        ranges = self._OP_RANGES.get(op, [])

        slots = []
        for slot_idx in range(2):
            if slot_idx < len(ranges):
                lo_bin, hi_bin = ranges[slot_idx]
                low = lo_bin / 64.0
                high = (hi_bin + 1) / 64.0
                sel = float(H[lo_bin:hi_bin + 1].sum().item()) / total_mass
            else:
                low, high, sel = 0.0, 0.0, 0.0
            slots.extend([low, high, sel])

        feature = torch.cat([H, torch.tensor(slots, dtype=torch.float32)])
        assert feature.shape[0] == self.pairwise_dim_n
        return feature

    def create_sql_features(self, sql: str, atoms_meta: Optional[dict] = None):
        """PRICE_N feature builder. Returns
            (feats_5tuple, n_join_col, n_fanout, n_table, n_filter_col,
             n_pairwise_intra)
        or None on failure.

        atoms_meta is the dict produced by the price_data_utils Phase 2-9
        helpers (see spec §3 / §7.1). When None, defaults are used so the
        builder can still be exercised in isolation.
        """
        if atoms_meta is None:
            atoms_meta = {"filter_atoms": {}, "join_sides": {}, "pairwise_atoms": []}
        filter_atoms = atoms_meta.get("filter_atoms", {})
        join_sides = atoms_meta.get("join_sides", {})
        pairwise_atoms = atoms_meta.get("pairwise_atoms", [])

        columns, tables, joins, _ = self.parse_sql(sql)
        # Rule f: skip the cyclic-join check entirely (cyclic graphs are now legal).

        table_join_cols, table_filter_cols = {}, {}
        for t in tables:
            table_join_cols[t] = []
            table_filter_cols[t] = []
        for col in columns:
            tbl = col.split(".")[0]
            is_join_col = any(col == j.split("=")[0].strip()
                              or col == j.split("=")[1].strip()
                              for j in joins)
            if is_join_col:
                table_join_cols[tbl].append(col)
            else:
                table_filter_cols[tbl].append(col)

        join_columns = self.flatten_list(list(table_join_cols.values()))
        filter_columns = self.flatten_list(list(table_filter_cols.values()))

        # Join-column histograms (existing PRICE machinery)
        join_column_histograms = []
        for jc in join_columns:
            join_column_histograms.append(
                torch.tensor(self.get_column_histograms(jc), dtype=torch.float32))

        # Extended fanout tokens (rule g)
        fanout_tokens = []
        for j in joins:
            side = join_sides.get(j, "INNER")
            f_lr, f_rl = self._encode_fanout_tokens_extended(j, side=side)
            fanout_tokens.append(f_lr)
            fanout_tokens.append(f_rl)

        # Filter tokens (75 dim each)
        filter_tokens = []
        table_sels = {t: [] for t in tables}
        for fc in filter_columns:
            atoms = filter_atoms.get(fc, dict(self.EMPTY_ATOMS))
            tok = self._encode_filter_token(fc, atoms)
            filter_tokens.append(tok)
            # token layout: hist[40] + (10×3) slots + tail(3) + (null_fraction, null_pred_flag)
            # selectivity for the AVI/EBO/MinSel needs the strongest matched slot's sel.
            slot_sels = tok[40:40 + 30:3]
            tail_sel = tok[40 + 30 + 2].item()
            sel_pos = max(slot_sels.tolist() + [tail_sel])
            null_pred = tok[-1].item()
            null_frac = tok[-2].item()
            if null_pred == 1.0:
                effective = max(null_frac, 1e-6)
            elif null_pred == -1.0:
                effective = max(1.0 - null_frac, 1e-6)
            elif sel_pos > 0:
                effective = sel_pos
            else:
                effective = 1e-6
            table_sels[fc.split(".")[0]].append(effective)

        # Pairwise intra-table tokens (rules h, j)
        pairwise_tokens = []
        for atom in pairwise_atoms:
            # atom: (left_table, col_x, col_y, op, right_table, right_col)
            l_t, cx, cy, op, r_t, r_c = atom
            pairwise_tokens.append(self._encode_pairwise_intra_token(
                l_t, cx, cy, op, right_table=r_t, right_col=r_c))

        # Table tokens (existing PRICE machinery)
        table_features = []
        for t in tables:
            sels = table_sels[t]
            if not sels:
                avi = torch.tensor([1.0]); minsel = torch.tensor([1.0]); ebo = torch.tensor([1.0])
            else:
                avi = torch.prod(torch.tensor(sels))
                minsel = torch.min(torch.tensor(sels))
                sorted_sels = sorted(sels, reverse=True)
                ebo_v = 1.0
                for i, s in enumerate(sorted_sels):
                    if i > 3: break
                    ebo_v *= s ** (1 / (2 ** i))
                ebo = torch.tensor([ebo_v])
            table_size = self.get_table_size(t)
            table_features.append(torch.cat([
                torch.tensor([np.log(table_size)], dtype=torch.float32),
                torch.tensor([avi.item()], dtype=torch.float32),
                torch.tensor([minsel.item()], dtype=torch.float32),
                torch.tensor([ebo.item()], dtype=torch.float32),
            ]))

        # Single-table fall-through: zero-pad join_hist + fanout (PRICE_M precedent)
        if len(join_columns) == 0:
            join_hist = torch.zeros(self.bin_size)
            fanout_feat = torch.zeros(self.fanout_dim_n * 2)
            n_jc, n_fo = 1, 2
        else:
            join_hist = torch.cat(join_column_histograms)
            fanout_feat = torch.cat(fanout_tokens)
            n_jc, n_fo = len(join_columns), len(joins) * 2

        if filter_tokens:
            filter_feat = torch.cat(filter_tokens)
        else:
            filter_feat = torch.zeros(self.filter_dim_n)
        n_fc = max(len(filter_columns), 1)

        if pairwise_tokens:
            pairwise_feat = torch.cat(pairwise_tokens)
            n_pi = len(pairwise_tokens)
        else:
            pairwise_feat = torch.zeros(0)
            n_pi = 0

        feats = (join_hist, fanout_feat,
                 torch.cat(table_features),
                 filter_feat, pairwise_feat)
        return feats, n_jc, n_fo, len(tables), n_fc, n_pi
