import os
import json
import re
from pathlib import Path
import pandas as pd
import numpy as np
import torch

# NOTE: train.py / utilsLLM.py add ../evaluation to sys.path, so import directly
from feature_extractor import traversePlan


def _default_stats_paths_for_workload(workload: str):
    """Pick stats source based on workload.

    - For IMDB-like workloads (job/job_full/syn/tpch/tpcds etc.), use imdb pg_stats.
    - For workload == 'stats', use stats pg_stats.

    Paths are relative to this repo checkout inside Doug's workspace.
    """
    here = Path(__file__).resolve()
    repo_root = here.parents[1]
    base = (repo_root / "dbresearch2_distributions").resolve()
    if workload == "stats":
        return base / "stats" / "pg_stats.csv", base / "stats" / "table_sizes.csv"
    return base / "imdb" / "pg_stats.csv", base / "imdb" / "table_sizes.csv"


class StatsMemory:
    """Lightweight wrapper around Postgres pg_stats dumps.

    We only use portable, read-only features:
    - null_frac
    - n_distinct (ndv proxy)
    - most_common_freqs (for top-k mass/skew proxy)
    - histogram_bounds (for rough range/shape proxy)

    Notes:
    - pg_stats is sampled + capped by stats target; treat as noisy.
    - For n_distinct: negative values are Postgres heuristics (fraction of rows).
    """

    def __init__(self, pg_stats_csv: str, table_sizes_csv: str | None = None):
        self.pg_stats_csv = str(pg_stats_csv)
        self.table_sizes_csv = str(table_sizes_csv) if table_sizes_csv else None

        df = pd.read_csv(self.pg_stats_csv)
        # normalize column names
        df.columns = [c.strip() for c in df.columns]
        self.df = df

        # Build lookup: (table, col) -> row
        self._idx = {}
        for _, r in df.iterrows():
            t = str(r.get("tablename"))
            a = str(r.get("attname"))
            self._idx[(t, a)] = r

        self.table_sizes = None
        if self.table_sizes_csv and os.path.exists(self.table_sizes_csv):
            ts = pd.read_csv(self.table_sizes_csv)
            ts.columns = [c.strip() for c in ts.columns]
            self.table_sizes = {str(r["table"]): (float(r["est_rows"]), float(r["bytes_total"])) for _, r in ts.iterrows()}

    @staticmethod
    def _parse_pg_array(arr_str: str):
        if not isinstance(arr_str, str) or len(arr_str) < 2:
            return []
        # simplest: strip { } and split by comma; frequencies are numeric, histogram bounds can be quoted
        s = arr_str.strip()
        if not (s.startswith("{") and s.endswith("}")):
            return []
        inner = s[1:-1]
        if inner == "":
            return []
        out = []
        cur = ""
        in_quotes = False
        i = 0
        while i < len(inner):
            ch = inner[i]
            if ch == '"':
                in_quotes = not in_quotes
                i += 1
                continue
            if ch == "," and not in_quotes:
                out.append(cur)
                cur = ""
                i += 1
                continue
            cur += ch
            i += 1
        out.append(cur)
        return out

    def col_features(self, table: str, col: str, est_rows_for_table: float | None = None):
        """Return a small numeric feature vector for one column.

        Vector (float32):
        - log1p(ndv_proxy)
        - null_frac
        - top1_freq
        - top5_mass
        - hist_len_norm

        ndv_proxy:
        - if n_distinct < 0 and est_rows known: ndv = -n_distinct * est_rows
        - else ndv = n_distinct (clipped)
        """
        r = self._idx.get((table, col))
        if r is None:
            return None

        null_frac = float(r.get("null_frac", 0.0))
        n_distinct = float(r.get("n_distinct", 0.0))

        # NDV proxy handling
        if n_distinct < 0 and est_rows_for_table is not None:
            ndv = (-n_distinct) * float(est_rows_for_table)
        else:
            ndv = n_distinct
        ndv = max(0.0, float(ndv))

        mcf = r.get("most_common_freqs", None)
        freqs = []
        if isinstance(mcf, str):
            try:
                freqs = [float(x) for x in self._parse_pg_array(mcf) if x != ""]
            except Exception:
                freqs = []
        top1 = freqs[0] if len(freqs) >= 1 else 0.0
        top5 = float(sum(freqs[:5])) if len(freqs) else 0.0

        hb = r.get("histogram_bounds", None)
        hist_len = 0.0
        if isinstance(hb, str):
            try:
                hist_len = float(len(self._parse_pg_array(hb)))
            except Exception:
                hist_len = 0.0
        hist_len_norm = hist_len / 100.0  # rough scale

        return np.array([
            np.log1p(ndv),
            null_frac,
            top1,
            top5,
            hist_len_norm,
        ], dtype=np.float32)


def extract_referenced_columns_from_plan_json(plan_json: dict):
    """Extract referenced column strings from a plan JSON.

    Returns a set of strings like:
    - alias.col (from filters)
    - alias.col (from join equality)

    The feature_extractor already formats filters as ["alias.col", op, value].
    Joins are strings like "a.x = b.y".
    """
    root = traversePlan(plan_json)
    cols = set()
    q = [root]
    while q:
        n = q.pop(0)
        q.extend(getattr(n, "children", []) or [])
        # filters: list of [col, op, val]
        if getattr(n, "filters", None):
            for f in n.filters:
                if isinstance(f, (list, tuple)) and len(f) >= 1:
                    c = f[0]
                    if isinstance(c, str) and "." in c:
                        cols.add(c)
        # join: string "a.x = b.y"
        j = getattr(n, "join", None)
        if isinstance(j, str) and "=" in j:
            parts = [p.strip() for p in j.split("=")]
            for p in parts:
                if "." in p:
                    cols.add(p)
    return cols


def build_query_stats_vector(plan_json: dict, ds_info, stats_mem: StatsMemory, max_cols: int = 16):
    """Aggregate per-column features into a fixed-length vector.

    Strategy (best-effort, robust):
    - collect referenced columns from filters+joins
    - map alias -> table via ds_info.alias2table when possible
    - compute per-column feature vectors
    - aggregate with (mean, max) over columns

    Output dim: 2 * feat_dim (mean + max). If no cols resolved, zeros.
    """
    feat_dim = 5
    cols = extract_referenced_columns_from_plan_json(plan_json)

    feats = []
    for ac in sorted(cols):
        try:
            alias, col = ac.split(".", 1)
        except Exception:
            continue
        table = ds_info.alias2table.get(alias, alias) if hasattr(ds_info, "alias2table") else alias
        est_rows = None
        if stats_mem.table_sizes is not None and table in stats_mem.table_sizes:
            est_rows = stats_mem.table_sizes[table][0]
        f = stats_mem.col_features(table, col, est_rows_for_table=est_rows)
        if f is not None:
            feats.append(f)
        if len(feats) >= max_cols:
            break

    if not feats:
        return np.zeros((feat_dim * 2,), dtype=np.float32)

    M = np.stack(feats, axis=0)  # [k, feat_dim]
    mean = M.mean(axis=0)
    mx = M.max(axis=0)
    return np.concatenate([mean, mx], axis=0).astype(np.float32)


def build_stats_matrix_from_csv(dat_path: str, ds_info, stats_mem: StatsMemory, argsP=None):
    """Read a plan CSV and return stats feature matrix aligned to rows.

    Expects columns:
    - 'json' or 'Plan_dump'

    Returns: torch.FloatTensor [N, S]
    """
    df = pd.read_csv(dat_path)
    col = "json" if "json" in df.columns else "Plan_dump"
    stats_vecs = []
    for _, row in df.iterrows():
        js_str = row.get(col)
        if not isinstance(js_str, str) or js_str == "failed":
            # keep alignment by emitting zeros
            stats_vecs.append(np.zeros((10,), dtype=np.float32))
            continue
        try:
            plan_json = json.loads(js_str)
        except Exception:
            stats_vecs.append(np.zeros((10,), dtype=np.float32))
            continue
        v = build_query_stats_vector(plan_json, ds_info, stats_mem)
        stats_vecs.append(v)

    X = np.stack(stats_vecs, axis=0)
    return torch.from_numpy(X).float()


def load_stats_memory_for_args(argsP):
    pg_stats_path = getattr(argsP, "stats_pg_stats_path", None)
    table_sizes_path = getattr(argsP, "stats_table_sizes_path", None)
    if pg_stats_path is None:
        pg_stats_path, table_sizes_path = _default_stats_paths_for_workload(getattr(argsP, "workload_test", "imdb"))
    return StatsMemory(pg_stats_path, table_sizes_path)


def inject_stat_tokens_into_cleaned_plan(
    cleaned_root: dict,
    ds_info,
    stats_mem: StatsMemory,
    token_str: str = "[STAT]",
    token_mode: str = "per_column",
):
    """Attach [STAT] tokens next to predicate strings inside the cleaned Postgres plan JSON.

    The cleaned plan JSON uses keys like "Filter", "Index Cond", "Hash Cond", "Merge Cond", etc.
    We do NOT concatenate stats into the text; instead we insert a literal token string
    and separately return a list of numeric vectors (one per inserted token).

    token_mode:
      - "per_column": insert up to K tokens (currently 8), one per referenced column.
      - "avg": insert a single token per predicate with mean-pooled vector.

    At model time, the [STAT] token's embedding is replaced with a projection of the
    corresponding numeric stats vector.

    Returns:
      (augmented_root, stats_vecs)
        - augmented_root: JSON-serializable dict with extra sibling keys containing [STAT] tokens
        - stats_vecs: list[np.ndarray], each shape [5]
    """
    stats_vecs = []

    PRED_KEYS = {
        "Filter",
        "Index Cond",
        "Recheck Cond",
        "Hash Cond",
        "Merge Cond",
        "Join Filter",
    }

    # Best-effort alias->table resolution from the plan itself.
    def _collect_alias_map(obj, amap: dict):
        if isinstance(obj, dict):
            alias = obj.get("Alias", None)
            rel = obj.get("Relation Name", None) or obj.get("Relation", None) or obj.get("Table Name", None)
            if isinstance(alias, str) and isinstance(rel, str) and alias and rel:
                amap[alias] = rel
            for v in obj.values():
                _collect_alias_map(v, amap)
        elif isinstance(obj, list):
            for x in obj:
                _collect_alias_map(x, amap)

    alias_map = {}
    _collect_alias_map(cleaned_root, alias_map)

    def _alias_to_table(alias: str) -> str:
        if alias in alias_map:
            return alias_map[alias]
        if hasattr(ds_info, "alias2table") and isinstance(ds_info.alias2table, dict):
            return ds_info.alias2table.get(alias, alias)
        return alias

    def _col_vec(alias: str, col: str):
        table = _alias_to_table(alias)
        est_rows = None
        if stats_mem.table_sizes is not None and table in stats_mem.table_sizes:
            est_rows = stats_mem.table_sizes[table][0]
        return stats_mem.col_features(table, col, est_rows_for_table=est_rows)

    _alias_col_re = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)")

    def _predicate_vecs(pred_str: str):
        if not isinstance(pred_str, str):
            return None
        matches = _alias_col_re.findall(pred_str)
        if not matches:
            return None
        vecs = []
        for alias, col in matches[:8]:
            v = _col_vec(alias, col)
            if v is not None:
                vecs.append((alias, col, v))
        if not vecs:
            return None
        return vecs

    def _recurse(obj):
        if isinstance(obj, dict):
            new = {}
            for k, v in obj.items():
                new[k] = _recurse(v)
                # After we copy the predicate string, append a sibling token key so JSON dump places it nearby.
                if k in PRED_KEYS and isinstance(v, str):
                    vecs = _predicate_vecs(v)
                    if vecs is not None:
                        if token_mode == "avg":
                            mean_vec = np.stack([vec for _, _, vec in vecs], axis=0).mean(axis=0).astype(np.float32)
                            new[f"{k}__stat_token"] = token_str
                            stats_vecs.append(mean_vec)
                        else:
                            for idx, (alias, col, vec) in enumerate(vecs):
                                new[f"{k}__statistics_token_{idx}_{alias}.{col}"] = token_str
                                stats_vecs.append(vec)
            return new
        elif isinstance(obj, list):
            return [_recurse(x) for x in obj]
        else:
            return obj

    return _recurse(cleaned_root), stats_vecs


class StatsVecNormalizer:
    """Simple per-dimension z-score normalization for stats vectors."""
    def __init__(self, eps: float = 1e-6):
        self.eps = eps
        self.mean = None
        self.std = None

    def fit(self, vecs: list[np.ndarray]):
        if not vecs:
            self.mean = None
            self.std = None
            return
        X = np.stack(vecs, axis=0).astype(np.float32)
        self.mean = X.mean(axis=0)
        self.std = X.std(axis=0)

    def transform(self, vecs: list[np.ndarray]) -> list[np.ndarray]:
        if self.mean is None or self.std is None:
            return vecs
        out = []
        denom = self.std + self.eps
        for v in vecs:
            out.append(((v - self.mean) / denom).astype(np.float32))
        return out


def normalize_stats_vecs(train_list, val_list, test_list):
    """Fit normalizer on train stats vectors; apply to train/val/test."""
    # Flatten per-plan lists
    train_flat = [v for per in train_list for v in per] if train_list else []
    val_flat = [v for per in val_list for v in per] if val_list else []
    test_flat = [v for per in test_list for v in per] if test_list else []

    norm = StatsVecNormalizer()
    norm.fit(train_flat)

    def _apply(per_plan_list):
        if not per_plan_list:
            return per_plan_list
        return [norm.transform(per) for per in per_plan_list]

    return _apply(train_list), _apply(val_list), _apply(test_list)
