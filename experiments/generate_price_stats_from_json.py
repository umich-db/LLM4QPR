"""
Generate synthetic PRICE statistics from deepdb_augmented JSON metadata.

For the 18 non-PostgreSQL databases, generates the 5 PRICE .pkl files using:
  - table_stats for sizes
  - column_stats for types and cardinality info
  - Literal mining from filter_columns across all plans for real histogram data

Usage:
    python generate_price_stats_from_json.py --db financial
    python generate_price_stats_from_json.py --db all
    python generate_price_stats_from_json.py --db all --exclude imdb stats
"""

import os
import sys
import json
import pickle
import argparse
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from cross_workload_price_config import (
    CROSS_WORKLOAD_ABBREV,
    ALL_CROSS_WORKLOAD_DBS,
    get_json_paths_for_db,
)
from reconstruct_sql_from_plans import reconstruct_all_sql

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BIN_SIZE = 40
PRICE_STATS_BASE = "/root/PRICE/datas/statistics/finetune"

STRING_TYPES = {"character varying", "character", "text", "char", "varchar"}
DATE_TYPES = {"date", "timestamp without time zone", "timestamp with time zone"}


# ---------------------------------------------------------------------------
# Literal mining from plan filter_columns
# ---------------------------------------------------------------------------
def mine_literals_from_plans(plans, column_stats):
    """Scan all plans' filter_columns to collect observed literal values per column index.

    Only mines from SCAN nodes (nodes with a 'table' field).

    Returns:
        dict: {col_idx: [literal_value, ...]} — raw literal values
    """
    literals = defaultdict(list)

    def _mine_from_filter(fc):
        if fc is None:
            return
        op = fc.get("operator")
        col_idx = fc.get("column")

        if op in ("AND", "OR") and fc.get("children"):
            for child in fc["children"]:
                _mine_from_filter(child)
            return

        if col_idx is not None and fc.get("literal") is not None:
            # Only collect from actual filter predicates (not join conditions)
            literal = fc["literal"]
            if isinstance(literal, str):
                # Skip join-condition literals like "table.col  "
                if "." in literal and literal.strip().endswith(""):
                    # Check if it looks like a join ref (e.g., "account.account_id  ")
                    parts = literal.strip().split(".")
                    if len(parts) == 2 and all(p.strip().replace("_", "").isalnum() for p in parts):
                        return
            literals[col_idx].append(literal)

    def _traverse_scan_only(node):
        pp = node.get("plan_parameters", {})
        # Only mine from scan nodes
        if pp.get("table") is not None and pp.get("filter_columns") is not None:
            _mine_from_filter(pp["filter_columns"])
        for child in node.get("children", []):
            _traverse_scan_only(child)

    for plan in plans:
        _traverse_scan_only(plan)

    return dict(literals)


def _discover_joins_from_plans(plans, table_stats, column_stats, abbrev):
    """Discover join column pairs from plan trees.

    Returns:
        set of ((alias1, col1), (alias2, col2)) pairs
    """
    import re
    joins = set()

    for plan in plans:
        for jc in plan.get("join_conds", []):
            parts = re.split(r"\s+AND\s+", jc)
            for part in parts:
                m = re.match(
                    r'"([^"]+)"\.?"([^"]+)"\s*=\s*"([^"]+)"\.?"([^"]+)"',
                    part.strip()
                )
                if m:
                    t1, c1, t2, c2 = m.groups()
                    a1 = abbrev.get(t1) or abbrev.get(t1.lower())
                    a2 = abbrev.get(t2) or abbrev.get(t2.lower())
                    if a1 and a2:
                        pair = tuple(sorted([
                            (a1, c1.lower()), (a2, c2.lower())
                        ]))
                        joins.add(pair)

    return joins


def _discover_filter_cols_from_plans(plans, column_stats, abbrev):
    """Discover which columns appear as filter predicates in scan nodes.

    Returns:
        set of (alias, col_name) tuples
    """
    filter_cols = set()

    def _extract(fc):
        if fc is None:
            return
        op = fc.get("operator")
        if op in ("AND", "OR") and fc.get("children"):
            for child in fc["children"]:
                _extract(child)
            return
        col_idx = fc.get("column")
        if col_idx is not None and col_idx < len(column_stats):
            cs = column_stats[col_idx]
            table_name = cs["tablename"]
            alias = abbrev.get(table_name)
            if alias:
                filter_cols.add((alias, cs["attname"].lower()))

    def _traverse(node):
        pp = node.get("plan_parameters", {})
        if pp.get("table") is not None and pp.get("filter_columns") is not None:
            _extract(pp["filter_columns"])
        for child in node.get("children", []):
            _traverse(child)

    for plan in plans:
        _traverse(plan)

    return filter_cols


# ---------------------------------------------------------------------------
# Classify columns
# ---------------------------------------------------------------------------
def classify_columns_from_stats(column_stats, tracked_cols, abbrev):
    """Classify columns as continuous or discrete using column_stats metadata.

    tracked_cols: set of (alias, col_name) to classify
    Returns: {(alias, col_name): 'ctn' | 'dsct'}
    """
    # Build reverse: alias -> table_name
    alias_to_table = {}
    for tname, alias in abbrev.items():
        alias_to_table[alias] = tname

    # Build column_stats lookup: (table, col_lower) -> stats
    cs_lookup = {}
    for cs in column_stats:
        cs_lookup[(cs["tablename"], cs["attname"].lower())] = cs

    col_types = {}
    for alias, col in tracked_cols:
        table = alias_to_table.get(alias)
        if not table:
            col_types[(alias, col)] = "ctn"
            continue

        stats = cs_lookup.get((table, col))
        if not stats:
            col_types[(alias, col)] = "ctn"
            continue

        dtype = stats.get("data_type", "")

        if dtype in STRING_TYPES:
            col_types[(alias, col)] = "dsct"
            continue

        if dtype in DATE_TYPES:
            col_types[(alias, col)] = "ctn"
            continue

        # Numeric: use n_distinct
        n_distinct = stats.get("n_distinct", -1)
        if n_distinct is None:
            n_distinct = -1

        n_distinct = float(n_distinct)
        if n_distinct < 0:
            # Negative = fraction of rows
            if abs(n_distinct) > 0.01:
                col_types[(alias, col)] = "ctn"
            else:
                col_types[(alias, col)] = "dsct"
        else:
            if n_distinct > 50:
                col_types[(alias, col)] = "ctn"
            else:
                col_types[(alias, col)] = "dsct"

    return col_types


# ---------------------------------------------------------------------------
# Generate size.pkl
# ---------------------------------------------------------------------------
def generate_size_from_json(table_stats_list, abbrev):
    """Generate size.pkl from table_stats."""
    # Build column counts per table from column_stats
    size_data = {}
    # Count unique tables in table_stats
    table_tuples = {}
    for ts in table_stats_list:
        name = ts["relname"]
        if name in abbrev:
            table_tuples[name] = ts["reltuples"]

    for table_name, alias in abbrev.items():
        tuples = table_tuples.get(table_name, 0)
        size_data[alias] = {
            "size": int(tuples),
            "num_cols": 0,  # Will be filled from column_stats
            "num_rows": int(tuples),
        }

    return size_data


def _fill_num_cols(size_data, column_stats, abbrev):
    """Fill in num_cols from column_stats."""
    col_counts = defaultdict(int)
    for cs in column_stats:
        table = cs["tablename"]
        if table in abbrev:
            col_counts[abbrev[table]] += 1

    for alias in size_data:
        if alias in col_counts:
            size_data[alias]["num_cols"] = col_counts[alias]


# ---------------------------------------------------------------------------
# Generate histogram40.pkl
# ---------------------------------------------------------------------------
def generate_histograms_from_literals(mined_literals, column_stats, abbrev,
                                       col_types, bin_size=BIN_SIZE):
    """Generate histograms from mined literal values.

    For columns with observed literals: build histogram from literal distribution.
    For columns without literals: build uniform synthetic histogram using
    n_distinct and table_size metadata.
    """
    histogram_data = {}
    for alias in abbrev.values():
        histogram_data[alias] = {}

    # Build col_idx -> (alias, col_name_lower, stats) mapping
    col_map = {}
    for idx, cs in enumerate(column_stats):
        table = cs["tablename"]
        if table in abbrev:
            col_map[idx] = (abbrev[table], cs["attname"].lower(), cs)

    # Collect all tracked columns
    tracked = set()
    for alias, col in col_types:
        tracked.add((alias, col))

    # Process each tracked column
    for (alias, col) in tracked:
        # Find the column index
        col_idx = None
        col_stats = None
        for idx, (a, c, cs) in col_map.items():
            if a == alias and c == col:
                col_idx = idx
                col_stats = cs
                break

        if col_stats is None:
            continue

        dtype = col_stats.get("data_type", "")
        table_size = float(col_stats.get("table_size", 1))
        n_distinct = float(col_stats.get("n_distinct", -1) or -1)

        # Resolve absolute n_distinct
        if n_distinct < 0:
            abs_distinct = abs(n_distinct) * table_size
        else:
            abs_distinct = n_distinct

        abs_distinct = max(1, int(abs_distinct))

        lits = mined_literals.get(col_idx, []) if col_idx is not None else []

        if dtype in STRING_TYPES:
            _build_string_histogram(
                alias, col, lits, abs_distinct, table_size,
                histogram_data, bin_size
            )
        else:
            _build_numeric_histogram(
                alias, col, lits, abs_distinct, table_size,
                histogram_data, bin_size
            )

    return histogram_data


def _build_numeric_histogram(alias, col, literals, abs_distinct, table_size,
                               histogram_data, bin_size):
    """Build histogram for numeric column from mined literals or synthetically."""
    # Filter numeric literals
    nums = []
    for lit in literals:
        if isinstance(lit, (int, float)):
            nums.append(float(lit))
        elif isinstance(lit, str):
            try:
                nums.append(float(lit))
            except (ValueError, TypeError):
                pass

    if nums:
        min_val = min(nums)
        max_val = max(nums)
        # Expand range slightly to cover the full domain
        if min_val == max_val:
            max_val = min_val + 1.0
    else:
        # No observed literals — synthetic range
        min_val = 0.0
        max_val = float(max(abs_distinct - 1, 1))

    bin_edges = np.linspace(min_val, max_val, bin_size + 1)

    if nums:
        hist, _ = np.histogram(nums, bins=bin_edges)
        hist = hist.astype(float)
        # Scale histogram to approximate table_size
        total = hist.sum()
        if total > 0:
            hist = hist * (table_size / total)
    else:
        # Uniform distribution
        hist = np.full(bin_size, table_size / bin_size, dtype=float)

    histogram_data[alias][col] = {
        "hist": hist,
        "bin_edges": bin_edges,
        "len": int(table_size),
        "min_value": min_val,
        "max_value": max_val,
    }


def _build_string_histogram(alias, col, literals, abs_distinct, table_size,
                               histogram_data, bin_size):
    """Build histogram for string column (encoded as integer indices)."""
    # Count unique string literals
    str_lits = [str(l).strip() for l in literals if isinstance(l, str)]

    if str_lits:
        # Build frequency ranking
        from collections import Counter
        freq = Counter(str_lits)
        ranked = sorted(freq.keys(), key=lambda x: -freq[x])
        n_distinct = max(abs_distinct, len(ranked))
    else:
        n_distinct = max(abs_distinct, 1)
        ranked = []

    min_val = 0.0
    max_val = float(n_distinct - 1) if n_distinct > 1 else 1.0

    bin_edges = np.linspace(min_val, max_val, bin_size + 1)

    if ranked:
        from collections import Counter
        freq = Counter(str_lits)
        hist = np.zeros(bin_size, dtype=float)
        bin_width = (max_val - min_val) / bin_size if max_val > min_val else 1.0
        for idx, val in enumerate(ranked):
            bucket = min(int((idx - min_val) / bin_width), bin_size - 1) if max_val > min_val else 0
            hist[bucket] += freq[val]
        # Scale to table_size
        total = hist.sum()
        if total > 0:
            hist = hist * (table_size / total)
    else:
        hist = np.full(bin_size, table_size / bin_size, dtype=float)

    histogram_data[alias][col] = {
        "hist": hist,
        "bin_edges": bin_edges,
        "len": int(table_size),
        "min_value": min_val,
        "max_value": max_val,
    }


# ---------------------------------------------------------------------------
# Generate summary40.pkl
# ---------------------------------------------------------------------------
def generate_summaries_from_literals(mined_literals, column_stats, abbrev,
                                       col_types):
    """Generate summary for discrete columns using mined literals."""
    summary_data = {}
    for alias in abbrev.values():
        summary_data[alias] = {}

    # Build col_idx -> (alias, col_name_lower, stats) mapping
    col_map = {}
    for idx, cs in enumerate(column_stats):
        table = cs["tablename"]
        if table in abbrev:
            col_map[idx] = (abbrev[table], cs["attname"].lower(), cs)

    for (alias, col), cls in col_types.items():
        if cls != "dsct":
            continue

        # Find column index
        col_idx = None
        col_stats = None
        for idx, (a, c, cs) in col_map.items():
            if a == alias and c == col:
                col_idx = idx
                col_stats = cs
                break

        if col_stats is None:
            continue

        table_size = float(col_stats.get("table_size", 1))
        lits = mined_literals.get(col_idx, []) if col_idx is not None else []

        if lits:
            from collections import Counter
            freq = Counter()
            for lit in lits:
                if isinstance(lit, (int, float)):
                    # Check if it's a whole number
                    if isinstance(lit, float) and lit == int(lit):
                        freq[int(lit)] += 1
                    else:
                        freq[lit] += 1
                else:
                    freq[str(lit).strip()] += 1

            # Sort by frequency (most frequent first), like PRICE expects
            sorted_items = sorted(freq.items(), key=lambda x: -x[1])
            keys = [k for k, _ in sorted_items]
            values = [v for _, v in sorted_items]

            # Scale values to approximate table_size
            total = sum(values)
            if total > 0:
                scale = table_size / total
                values = [int(v * scale) for v in values]
        else:
            # No literals — create synthetic entries
            n_distinct = float(col_stats.get("n_distinct", -1) or -1)
            if n_distinct < 0:
                abs_distinct = max(1, int(abs(n_distinct) * table_size))
            else:
                abs_distinct = max(1, int(n_distinct))

            keys = list(range(abs_distinct))
            per_key = max(1, int(table_size / abs_distinct))
            values = [per_key] * abs_distinct

        summary_data[alias][col] = {
            "keys": keys,
            "values": values,
        }

    return summary_data


# ---------------------------------------------------------------------------
# Generate fanout40.pkl
# ---------------------------------------------------------------------------
def generate_fanouts_from_metadata(joins, histogram_data, column_stats,
                                     abbrev, bin_size=BIN_SIZE):
    """Generate fanout estimates from metadata (n_distinct and table_size).

    For each join pair (a1.c1, a2.c2), estimates fanout using:
      fanout(left->right) ≈ table_size_right / n_distinct_right
    This is the expected number of matching right rows per distinct join value.
    """
    fanout_data = {}

    # Build alias.col -> (table, n_distinct, table_size) lookup
    alias_to_table = {v: k for k, v in abbrev.items()}
    col_info = {}
    for cs in column_stats:
        table = cs["tablename"]
        if table in abbrev:
            alias = abbrev[table]
            col_name = cs["attname"].lower()
            n_distinct = float(cs.get("n_distinct", -1) or -1)
            table_size = float(cs.get("table_size", 1))
            if n_distinct < 0:
                abs_distinct = max(1, abs(n_distinct) * table_size)
            else:
                abs_distinct = max(1, n_distinct)
            col_info[(alias, col_name)] = {
                "n_distinct": abs_distinct,
                "table_size": table_size,
            }

    for (a1, c1), (a2, c2) in joins:
        left_key = f"{a1}.{c1}"
        right_key = f"{a2}.{c2}"

        info1 = col_info.get((a1, c1))
        info2 = col_info.get((a2, c2))

        if info1 is None or info2 is None:
            continue

        # Check histograms exist for both sides
        if c1 not in histogram_data.get(a1, {}):
            continue
        if c2 not in histogram_data.get(a2, {}):
            continue

        # Estimate: avg fanout left->right = table_size_right / n_distinct_right
        avg_fanout_lr = info2["table_size"] / info2["n_distinct"]
        avg_fanout_rl = info1["table_size"] / info1["n_distinct"]

        # Create uniform fanout across bins
        left_fanout = [avg_fanout_lr] * bin_size
        right_fanout = [avg_fanout_rl] * bin_size

        fanout_data[(left_key, right_key)] = [left_fanout, right_fanout]
        fanout_data[(right_key, left_key)] = [right_fanout, left_fanout]

    return fanout_data


# ---------------------------------------------------------------------------
# Main generation
# ---------------------------------------------------------------------------
def generate_stats_for_db(db_name, extra_json_paths=None):
    """Generate all 5 PRICE statistics files for a cross-workload database."""
    print(f"\n{'='*60}")
    print(f"Generating synthetic PRICE statistics for: {db_name}")
    print(f"{'='*60}")

    abbrev = CROSS_WORKLOAD_ABBREV[db_name]

    # Load all JSON files for this database
    json_paths = extra_json_paths or get_json_paths_for_db(db_name)
    if not json_paths:
        print(f"  ERROR: No JSON files found for {db_name}")
        return

    all_plans = []
    table_stats = None
    column_stats = None

    for jp in json_paths:
        print(f"  Loading {os.path.basename(jp)} ...")
        with open(jp) as f:
            data = json.load(f)
        if table_stats is None:
            table_stats = data["database_stats"]["table_stats"]
            column_stats = data["database_stats"]["column_stats"]
        all_plans.extend(data["parsed_plans"])

    print(f"  Total plans: {len(all_plans)}")
    print(f"  Tables: {len(abbrev)}")

    # 1. Mine literals
    print(f"\n[1] Mining literals from filter_columns ...")
    mined = mine_literals_from_plans(all_plans, column_stats)
    total_lits = sum(len(v) for v in mined.values())
    print(f"    Mined {total_lits} literals across {len(mined)} columns")

    # 2. Discover joins and filter columns
    print(f"\n[2] Discovering joins and filter columns ...")
    joins = _discover_joins_from_plans(all_plans, table_stats, column_stats, abbrev)
    filter_cols = _discover_filter_cols_from_plans(all_plans, column_stats, abbrev)
    print(f"    Join pairs: {len(joins)}")
    print(f"    Filter columns: {len(filter_cols)}")

    # 3. Collect all tracked columns
    all_cols = set()
    for (a1, c1), (a2, c2) in joins:
        all_cols.add((a1, c1))
        all_cols.add((a2, c2))
    all_cols.update(filter_cols)
    print(f"    Total tracked columns: {len(all_cols)}")

    # 4. Classify columns
    print(f"\n[3] Classifying columns ...")
    col_types = classify_columns_from_stats(column_stats, all_cols, abbrev)
    ctn = sum(1 for v in col_types.values() if v == "ctn")
    dsct = sum(1 for v in col_types.values() if v == "dsct")
    print(f"    Continuous: {ctn}, Discrete: {dsct}")

    # 5. Generate statistics
    print(f"\n[4] Generating statistics ...")

    # size.pkl
    size_data = generate_size_from_json(table_stats, abbrev)
    _fill_num_cols(size_data, column_stats, abbrev)
    print(f"  size.pkl: {len(size_data)} tables")
    for alias, info in sorted(size_data.items()):
        print(f"    {alias}: {info['num_rows']:,} rows, {info['num_cols']} cols")

    # histogram40.pkl
    histogram_data = generate_histograms_from_literals(
        mined, column_stats, abbrev, col_types
    )
    n_hist = sum(len(v) for v in histogram_data.values())
    print(f"  histogram40.pkl: {n_hist} columns")

    # Ensure join columns have histograms too
    for (a1, c1), (a2, c2) in joins:
        if c1 not in histogram_data.get(a1, {}):
            # Find column stats and add a synthetic histogram
            for cs in column_stats:
                if cs["tablename"] in abbrev and abbrev[cs["tablename"]] == a1 and cs["attname"].lower() == c1:
                    ts = float(cs.get("table_size", 1))
                    nd = float(cs.get("n_distinct", -1) or -1)
                    if nd < 0:
                        nd = max(1, abs(nd) * ts)
                    else:
                        nd = max(1, nd)
                    min_v, max_v = 0.0, float(max(nd - 1, 1))
                    be = np.linspace(min_v, max_v, BIN_SIZE + 1)
                    h = np.full(BIN_SIZE, ts / BIN_SIZE, dtype=float)
                    if a1 not in histogram_data:
                        histogram_data[a1] = {}
                    histogram_data[a1][c1] = {
                        "hist": h, "bin_edges": be,
                        "len": int(ts), "min_value": min_v, "max_value": max_v,
                    }
                    break
        if c2 not in histogram_data.get(a2, {}):
            for cs in column_stats:
                if cs["tablename"] in abbrev and abbrev[cs["tablename"]] == a2 and cs["attname"].lower() == c2:
                    ts = float(cs.get("table_size", 1))
                    nd = float(cs.get("n_distinct", -1) or -1)
                    if nd < 0:
                        nd = max(1, abs(nd) * ts)
                    else:
                        nd = max(1, nd)
                    min_v, max_v = 0.0, float(max(nd - 1, 1))
                    be = np.linspace(min_v, max_v, BIN_SIZE + 1)
                    h = np.full(BIN_SIZE, ts / BIN_SIZE, dtype=float)
                    if a2 not in histogram_data:
                        histogram_data[a2] = {}
                    histogram_data[a2][c2] = {
                        "hist": h, "bin_edges": be,
                        "len": int(ts), "min_value": min_v, "max_value": max_v,
                    }
                    break

    n_hist = sum(len(v) for v in histogram_data.values())
    print(f"  histogram40.pkl (after join cols): {n_hist} columns")

    # summary40.pkl
    summary_data = generate_summaries_from_literals(
        mined, column_stats, abbrev, col_types
    )
    n_summ = sum(len(v) for v in summary_data.values())
    print(f"  summary40.pkl: {n_summ} discrete columns")

    # fanout40.pkl
    fanout_data = generate_fanouts_from_metadata(
        joins, histogram_data, column_stats, abbrev
    )
    print(f"  fanout40.pkl: {len(fanout_data)} entries")

    # Build col_type dict
    col_type_dict = {}
    for alias in abbrev.values():
        col_type_dict[alias] = {"ctn": [], "dsct": []}
    for (alias, col), cls in col_types.items():
        if alias in col_type_dict:
            col_type_dict[alias][cls].append(col)

    # Save all files
    output_dir = os.path.join(PRICE_STATS_BASE, db_name)
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n[5] Saving files to {output_dir}/ ...")
    files = {
        "abbrev_col_type.pkl": {"abbrev": abbrev, "col_type": col_type_dict},
        "size.pkl": size_data,
        "histogram40.pkl": histogram_data,
        "summary40.pkl": summary_data,
        "fanout40.pkl": fanout_data,
    }
    for fname, data_obj in files.items():
        fpath = os.path.join(output_dir, fname)
        with open(fpath, "wb") as f:
            pickle.dump(data_obj, f)
        print(f"    Saved {fname}")

    print(f"\n{'='*60}")
    print(f"DONE: {db_name}")
    print(f"  Tables: {len(abbrev)}, Join pairs: {len(joins)}")
    print(f"  Histogram cols: {n_hist}, Summary cols: {n_summ}")
    print(f"  Fanout entries: {len(fanout_data)}")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic PRICE statistics from deepdb_augmented JSON"
    )
    parser.add_argument(
        "--db", type=str, required=True,
        help="Database name or 'all' for all databases"
    )
    parser.add_argument(
        "--exclude", type=str, nargs="*", default=[],
        help="Databases to exclude when using --db all"
    )
    args = parser.parse_args()

    if args.db == "all":
        for db_name in ALL_CROSS_WORKLOAD_DBS:
            if db_name in args.exclude:
                print(f"Skipping {db_name} (excluded)")
                continue
            generate_stats_for_db(db_name)
    else:
        if args.db not in CROSS_WORKLOAD_ABBREV:
            print(f"Unknown database: {args.db}")
            print(f"Available: {ALL_CROSS_WORKLOAD_DBS}")
            sys.exit(1)
        generate_stats_for_db(args.db)


if __name__ == "__main__":
    main()
