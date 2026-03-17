#!/usr/bin/env python3
"""
Update IMDB PRICE statistics (.pkl) to cover all tables/columns/joins
used in job_full.sql queries.

The existing stats only cover 6 core tables (title, cast_info, movie_companies,
movie_info, movie_info_idx, movie_keyword). This script adds:
  - 35 missing join pairs (fanout40.pkl)
  - 21 missing filter columns (histogram40.pkl + summary40.pkl)
  - Updated col_type entries (abbrev_col_type.pkl)

Usage:
    python update_imdb_stats_for_job_full.py
"""

import os
import sys
import re
import pickle
from collections import defaultdict

import numpy as np
import psycopg2

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BIN_SIZE = 40
STATS_DIR = "/root/PRICE/datas/statistics/finetune/imdb"

# IMDB alias mapping (same as in abbrev_col_type.pkl)
IMDB_ABBREV = {
    "title": "imdb_t",
    "cast_info": "imdb_ci",
    "movie_companies": "imdb_mc",
    "movie_info": "imdb_mi",
    "movie_info_idx": "imdb_mii",
    "movie_keyword": "imdb_mk",
    "name": "imdb_n",
    "company_name": "imdb_cpn",
    "company_type": "imdb_ct",
    "keyword": "imdb_kw",
    "kind_type": "imdb_kt",
    "info_type": "imdb_it",
    "role_type": "imdb_rt",
    "link_type": "imdb_lt",
    "movie_link": "imdb_ml",
    "complete_cast": "imdb_cc",
    "comp_cast_type": "imdb_cct",
    "char_name": "imdb_chn",
    "aka_name": "imdb_an",
    "aka_title": "imdb_at",
    "person_info": "imdb_pi",
}

# JOB query alias -> real table name
JOB_ALIAS_TO_TABLE = {
    't': 'title', 't1': 'title', 't2': 'title',
    'ci': 'cast_info', 'mc': 'movie_companies', 'mi': 'movie_info',
    'mi_idx': 'movie_info_idx', 'mk': 'movie_keyword',
    'n': 'name', 'n1': 'name',
    'cn': 'company_name', 'cn1': 'company_name', 'cn2': 'company_name',
    'k': 'keyword', 'it': 'info_type', 'it1': 'info_type',
    'it2': 'info_type', 'it3': 'info_type',
    'kt': 'kind_type', 'kt1': 'kind_type', 'kt2': 'kind_type',
    'rt': 'role_type', 'ct': 'company_type',
    'lt': 'link_type', 'ml': 'movie_link',
    'cc': 'complete_cast', 'cct1': 'comp_cast_type', 'cct2': 'comp_cast_type',
    'chn': 'char_name', 'an': 'aka_name', 'an1': 'aka_name',
    'at': 'aka_title', 'pi': 'person_info',
}

# String types (for classification)
STRING_TYPES = {"character varying", "character", "text", "char", "varchar"}
DATE_TYPES = {"date", "timestamp without time zone", "timestamp with time zone"}


# ---------------------------------------------------------------------------
# PostgreSQL helpers
# ---------------------------------------------------------------------------
def get_connection():
    return psycopg2.connect(dbname="imdb", user="root", host="/var/run/postgresql")


def query_one(conn, sql):
    cur = conn.cursor()
    cur.execute(sql)
    row = cur.fetchone()
    cur.close()
    return row


def query_all(conn, sql):
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    cur.close()
    return rows


# ---------------------------------------------------------------------------
# Parse job_full queries to find all joins and filter columns
# ---------------------------------------------------------------------------
def parse_job_full():
    """Parse job_full.sql to extract joins and filter columns."""
    with open("/root/LLM4QPR/queries/imdb/job_full.sql") as f:
        lines = f.readlines()

    all_joins = set()
    all_filter_cols = set()

    for line in lines:
        line = line.strip()
        if not line or not line.upper().startswith("EXPLAIN"):
            continue

        # Extract equi-joins: alias.col = alias.col
        join_matches = re.findall(r'(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)', line)
        for a1, c1, a2, c2 in join_matches:
            if a1 in JOB_ALIAS_TO_TABLE and a2 in JOB_ALIAS_TO_TABLE:
                t1 = JOB_ALIAS_TO_TABLE[a1]
                t2 = JOB_ALIAS_TO_TABLE[a2]
                if t1 != t2 or c1 != c2:
                    pair = tuple(sorted([(t1, c1), (t2, c2)]))
                    all_joins.add(pair)

        # Extract filter columns (col op literal)
        filter_matches = re.findall(
            r'(\w+)\.(\w+)\s*(?:=|!=|<>|>=|<=|>|<|BETWEEN|IN|LIKE|NOT LIKE)\s*[\'"\d(]',
            line, re.IGNORECASE
        )
        for alias, col in filter_matches:
            if alias in JOB_ALIAS_TO_TABLE:
                table = JOB_ALIAS_TO_TABLE[alias]
                all_filter_cols.add((table, col))

    return all_joins, all_filter_cols


# ---------------------------------------------------------------------------
# Load existing statistics
# ---------------------------------------------------------------------------
def load_pkl(name):
    path = os.path.join(STATS_DIR, name)
    with open(path, "rb") as f:
        return pickle.load(f)


def save_pkl(name, data):
    path = os.path.join(STATS_DIR, name)
    with open(path, "wb") as f:
        pickle.dump(data, f)
    print(f"  Saved {path}")


# ---------------------------------------------------------------------------
# Column classification
# ---------------------------------------------------------------------------
def get_col_dtype(conn, table, col):
    row = query_one(conn, f"""
        SELECT data_type FROM information_schema.columns
        WHERE table_schema='public' AND table_name='{table}' AND column_name='{col}'
    """)
    return row[0] if row else ""


def classify_col(conn, table, col, dtype):
    if dtype in STRING_TYPES:
        return "dsct"
    if dtype in DATE_TYPES:
        return "ctn"
    # Check cardinality
    row = query_one(conn, f"""
        SELECT n_distinct FROM pg_stats
        WHERE schemaname='public' AND tablename='{table}' AND attname='{col}'
    """)
    if row is None or row[0] is None:
        return "ctn"
    n_distinct = float(row[0])
    if n_distinct < 0:
        return "ctn" if abs(n_distinct) > 0.01 else "dsct"
    return "ctn" if n_distinct > 50 else "dsct"


# ---------------------------------------------------------------------------
# Histogram generation
# ---------------------------------------------------------------------------
def _col_expr(col, dtype):
    if dtype in DATE_TYPES:
        return f"EXTRACT(EPOCH FROM {col})::float8"
    return f"{col}::float8"


def generate_histogram_numeric(conn, table, col, dtype):
    expr = _col_expr(col, dtype)
    row = query_one(conn, f"""
        SELECT min({expr}), max({expr}), count(*)
        FROM {table} WHERE {col} IS NOT NULL
    """)
    len_col = query_one(conn, f"SELECT count(*) FROM {table}")[0]

    if row is None or row[0] is None:
        return {
            "hist": np.zeros(BIN_SIZE),
            "bin_edges": np.zeros(BIN_SIZE + 1),
            "len": len_col, "min_value": 0, "max_value": 0,
        }

    min_val, max_val, total = float(row[0]), float(row[1]), int(row[2])

    if min_val == max_val:
        bin_edges = np.linspace(min_val, min_val + 1.0, BIN_SIZE + 1)
        hist = np.zeros(BIN_SIZE, dtype=float)
        hist[0] = float(total)
    else:
        bin_edges = np.linspace(min_val, max_val, BIN_SIZE + 1)
        eps = (max_val - min_val) * 1e-10 + 1e-10
        rows = query_all(conn, f"""
            SELECT width_bucket({expr}, {min_val}, {max_val + eps}, {BIN_SIZE}) AS bucket,
                   count(*) AS cnt
            FROM {table} WHERE {col} IS NOT NULL
            GROUP BY bucket ORDER BY bucket
        """)
        hist = np.zeros(BIN_SIZE, dtype=float)
        for bucket, cnt in rows:
            if bucket is None:
                continue
            if 1 <= bucket <= BIN_SIZE:
                hist[bucket - 1] = float(cnt)
            elif bucket == 0:
                hist[0] += float(cnt)
            elif bucket == BIN_SIZE + 1:
                hist[BIN_SIZE - 1] += float(cnt)

    return {
        "hist": hist, "bin_edges": bin_edges,
        "len": len_col, "min_value": min_val, "max_value": max_val,
    }


def generate_histogram_string(conn, table, col):
    rows = query_all(conn, f"""
        SELECT {col}, count(*) AS cnt FROM {table}
        WHERE {col} IS NOT NULL GROUP BY {col} ORDER BY cnt DESC
    """)
    len_col = query_one(conn, f"SELECT count(*) FROM {table}")[0]
    if not rows:
        return {
            "hist": np.zeros(BIN_SIZE),
            "bin_edges": np.zeros(BIN_SIZE + 1),
            "len": len_col, "min_value": 0, "max_value": 0,
        }

    n_distinct = len(rows)
    total = sum(cnt for _, cnt in rows)
    min_val = 0.0
    max_val = float(n_distinct - 1) if n_distinct > 1 else 1.0

    if n_distinct == 1:
        bin_edges = np.linspace(0.0, 1.0, BIN_SIZE + 1)
        hist = np.zeros(BIN_SIZE, dtype=float)
        hist[0] = float(total)
    else:
        bin_edges = np.linspace(min_val, max_val, BIN_SIZE + 1)
        hist = np.zeros(BIN_SIZE, dtype=float)
        bin_width = (max_val - min_val) / BIN_SIZE
        for idx, (val, cnt) in enumerate(rows):
            bucket = min(int((idx - min_val) / bin_width), BIN_SIZE - 1)
            hist[bucket] += float(cnt)

    return {
        "hist": hist, "bin_edges": bin_edges,
        "len": len_col, "min_value": min_val, "max_value": max_val,
    }


# ---------------------------------------------------------------------------
# Summary generation
# ---------------------------------------------------------------------------
def generate_summary(conn, table, col):
    rows = query_all(conn, f"""
        SELECT {col}, count(*) AS cnt FROM {table}
        WHERE {col} IS NOT NULL GROUP BY {col} ORDER BY cnt DESC
    """)
    keys = []
    values = []
    for val, cnt in rows:
        if isinstance(val, (int, float)):
            keys.append(val)
        else:
            keys.append(str(val).strip())
        values.append(int(cnt))
    return {"keys": keys, "values": values}


# ---------------------------------------------------------------------------
# Fanout generation
# ---------------------------------------------------------------------------
def compute_fanout_direction(conn, left_table, left_col, right_table, right_col,
                              bin_edges, left_dtype, right_dtype):
    """Compute per-bin average fanout from left to right."""
    if left_dtype in STRING_TYPES:
        return compute_fanout_direction_string(
            conn, left_table, left_col, right_table, right_col, bin_edges)

    left_expr = _col_expr(left_col, left_dtype)
    right_expr = _col_expr(right_col, right_dtype)
    min_val = float(bin_edges[0])
    max_val = float(bin_edges[-1])

    if min_val == max_val:
        lc = query_one(conn, f"SELECT count(*) FROM {left_table} WHERE {left_col} IS NOT NULL")[0]
        rc = query_one(conn, f"""
            SELECT count(*) FROM {right_table}
            WHERE {right_col} IS NOT NULL AND {right_expr} = {min_val}
        """)[0]
        fanout = [0.0] * BIN_SIZE
        if lc > 0:
            fanout[0] = float(rc)
        return fanout

    eps = (max_val - min_val) * 1e-10 + 1e-10
    sql = f"""
        WITH left_counts AS (
            SELECT {left_expr} AS val, count(*) AS lcnt
            FROM {left_table} WHERE {left_col} IS NOT NULL
            GROUP BY {left_expr}
        ),
        right_counts AS (
            SELECT {right_expr} AS val, count(*) AS rcnt
            FROM {right_table} WHERE {right_col} IS NOT NULL
            GROUP BY {right_expr}
        ),
        merged AS (
            SELECT lc.val, lc.lcnt, COALESCE(rc.rcnt, 0) AS rcnt
            FROM left_counts lc
            LEFT JOIN right_counts rc ON lc.val = rc.val
        )
        SELECT
            width_bucket(val, {min_val}, {max_val + eps}, {BIN_SIZE}) AS bucket,
            CASE WHEN SUM(lcnt) = 0 THEN 0
                 ELSE SUM(lcnt::float8 * rcnt) / SUM(lcnt)
            END AS avg_fanout
        FROM merged GROUP BY bucket ORDER BY bucket
    """
    rows = query_all(conn, sql)
    fanout = [0.0] * BIN_SIZE
    for bucket, avg_fo in rows:
        if bucket is None:
            continue
        idx = bucket - 1
        if 0 <= idx < BIN_SIZE:
            fanout[idx] = float(avg_fo) if avg_fo else 0.0
        elif bucket == 0:
            fanout[0] += float(avg_fo) if avg_fo else 0.0
        elif bucket == BIN_SIZE + 1:
            fanout[BIN_SIZE - 1] += float(avg_fo) if avg_fo else 0.0
    return fanout


def compute_fanout_direction_string(conn, left_table, left_col, right_table, right_col,
                                     bin_edges):
    """Compute per-bin fanout for string-type join columns."""
    left_rows = query_all(conn, f"""
        SELECT {left_col}, count(*) AS cnt FROM {left_table}
        WHERE {left_col} IS NOT NULL GROUP BY {left_col} ORDER BY cnt DESC
    """)
    if not left_rows:
        return [0.0] * BIN_SIZE

    right_rows = query_all(conn, f"""
        SELECT {right_col}, count(*) AS cnt FROM {right_table}
        WHERE {right_col} IS NOT NULL GROUP BY {right_col}
    """)
    right_counts = {val: cnt for val, cnt in right_rows}

    n_distinct = len(left_rows)
    min_val = 0.0
    max_val = float(n_distinct - 1) if n_distinct > 1 else 1.0
    bin_width = (max_val - min_val) / BIN_SIZE if max_val > min_val else 1.0

    bin_lc_sum = [0.0] * BIN_SIZE
    bin_lc_rc_sum = [0.0] * BIN_SIZE
    for idx, (val, lcnt) in enumerate(left_rows):
        rcnt = right_counts.get(val, 0)
        bucket = min(int((idx - min_val) / bin_width), BIN_SIZE - 1) if max_val > min_val else 0
        bin_lc_sum[bucket] += float(lcnt)
        bin_lc_rc_sum[bucket] += float(lcnt) * float(rcnt)

    fanout = [0.0] * BIN_SIZE
    for i in range(BIN_SIZE):
        if bin_lc_sum[i] > 0:
            fanout[i] = bin_lc_rc_sum[i] / bin_lc_sum[i]
    return fanout


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=== Updating IMDB PRICE statistics for job_full ===\n")

    # Parse queries
    print("Step 1: Parsing job_full.sql ...")
    all_joins, all_filter_cols = parse_job_full()
    print(f"  Found {len(all_joins)} unique join pairs, {len(all_filter_cols)} filter columns\n")

    # Load existing stats
    print("Step 2: Loading existing statistics ...")
    act = load_pkl("abbrev_col_type.pkl")
    fanout = load_pkl("fanout40.pkl")
    hist = load_pkl("histogram40.pkl")
    summary = load_pkl("summary40.pkl")
    size = load_pkl("size.pkl")
    print(f"  Existing fanout keys: {len(fanout)}")
    print(f"  Existing histogram tables: {len(hist)}")
    print(f"  Existing summary tables: {len(summary)}\n")

    # Connect to PostgreSQL
    conn = get_connection()

    # Determine which joins and filters are missing
    missing_joins = []
    for pair in all_joins:
        (t1, c1), (t2, c2) = pair
        a1 = IMDB_ABBREV.get(t1)
        a2 = IMDB_ABBREV.get(t2)
        if not a1 or not a2:
            continue
        key1 = (f"{a1}.{c1}", f"{a2}.{c2}")
        key2 = (f"{a2}.{c2}", f"{a1}.{c1}")
        if key1 not in fanout and key2 not in fanout:
            missing_joins.append(pair)

    missing_filters = []
    for table, col in all_filter_cols:
        abbrev = IMDB_ABBREV.get(table)
        if not abbrev:
            continue
        has_hist = abbrev in hist and col in hist[abbrev]
        has_summ = abbrev in summary and col in summary[abbrev]
        if not has_hist and not has_summ:
            missing_filters.append((table, col))

    print(f"  Missing joins: {len(missing_joins)}")
    print(f"  Missing filters: {len(missing_filters)}\n")

    # Collect all columns that need statistics (join cols + filter cols)
    all_cols_needed = set()
    for (t1, c1), (t2, c2) in missing_joins:
        all_cols_needed.add((t1, c1))
        all_cols_needed.add((t2, c2))
    for table, col in missing_filters:
        all_cols_needed.add((table, col))

    # Also include existing join columns that need histograms for fanout computation
    for (t1, c1), (t2, c2) in missing_joins:
        a1 = IMDB_ABBREV[t1]
        a2 = IMDB_ABBREV[t2]
        if a1 in hist and c1 in hist[a1]:
            pass  # already has histogram
        else:
            all_cols_needed.add((t1, c1))
        if a2 in hist and c2 in hist[a2]:
            pass  # already has histogram
        else:
            all_cols_needed.add((t2, c2))

    # Step 3: Classify all needed columns and get dtypes
    print("Step 3: Classifying columns ...")
    col_dtypes = {}
    col_classes = {}
    for table, col in sorted(all_cols_needed):
        dtype = get_col_dtype(conn, table, col)
        col_dtypes[(table, col)] = dtype
        cls = classify_col(conn, table, col, dtype)
        col_classes[(table, col)] = cls
        abbrev = IMDB_ABBREV[table]
        print(f"  {abbrev}.{col}: dtype={dtype}, class={cls}")

    # Step 4: Update abbrev_col_type.pkl
    print("\nStep 4: Updating abbrev_col_type.pkl ...")
    if 'col_type' not in act:
        act['col_type'] = {}
    for (table, col), cls in col_classes.items():
        abbrev = IMDB_ABBREV[table]
        if abbrev not in act['col_type']:
            act['col_type'][abbrev] = {}
        if col not in act['col_type'][abbrev]:
            act['col_type'][abbrev][col] = cls
            print(f"  Added {abbrev}.{col} = {cls}")

    # Step 5: Update size.pkl for any new tables
    print("\nStep 5: Updating size.pkl ...")
    for table, abbrev in IMDB_ABBREV.items():
        if abbrev not in size:
            row_count = query_one(conn, f"SELECT count(*) FROM {table}")[0]
            col_count = query_one(conn, f"""
                SELECT count(*) FROM information_schema.columns
                WHERE table_schema='public' AND table_name='{table}'
            """)[0]
            size[abbrev] = {"size": row_count, "num_cols": col_count, "num_rows": row_count}
            print(f"  Added {abbrev}: {row_count:,} rows, {col_count} cols")

    # Step 6: Generate missing histograms
    print("\nStep 6: Generating missing histograms ...")
    for (table, col) in sorted(all_cols_needed):
        abbrev = IMDB_ABBREV[table]
        if abbrev not in hist:
            hist[abbrev] = {}
        if col in hist[abbrev]:
            continue  # already exists
        dtype = col_dtypes[(table, col)]
        if dtype in STRING_TYPES:
            h = generate_histogram_string(conn, table, col)
        else:
            h = generate_histogram_numeric(conn, table, col, dtype)
        hist[abbrev][col] = h
        print(f"  {abbrev}.{col}: min={h['min_value']:.2f}, max={h['max_value']:.2f}, "
              f"len={h['len']:,}, bins_nz={int(np.count_nonzero(h['hist']))}")

    # Step 7: Generate missing summaries (for discrete columns)
    print("\nStep 7: Generating missing summaries ...")
    for (table, col), cls in sorted(col_classes.items()):
        if cls != "dsct":
            continue
        abbrev = IMDB_ABBREV[table]
        if abbrev not in summary:
            summary[abbrev] = {}
        if col in summary[abbrev]:
            continue  # already exists
        s = generate_summary(conn, table, col)
        summary[abbrev][col] = s
        print(f"  {abbrev}.{col}: {len(s['keys'])} distinct values")

    # Step 8: Generate missing fanouts
    print("\nStep 8: Generating missing fanouts ...")
    for (t1, c1), (t2, c2) in sorted(missing_joins):
        a1 = IMDB_ABBREV[t1]
        a2 = IMDB_ABBREV[t2]
        left_key = f"{a1}.{c1}"
        right_key = f"{a2}.{c2}"

        # Ensure both sides have histograms for binning
        if c1 not in hist.get(a1, {}):
            print(f"  WARNING: No histogram for {a1}.{c1}, skipping")
            continue
        if c2 not in hist.get(a2, {}):
            print(f"  WARNING: No histogram for {a2}.{c2}, skipping")
            continue

        print(f"  Computing: {left_key} <-> {right_key}")

        d1 = col_dtypes.get((t1, c1), "")
        d2 = col_dtypes.get((t2, c2), "")
        # If dtype missing, look it up
        if not d1:
            d1 = get_col_dtype(conn, t1, c1)
        if not d2:
            d2 = get_col_dtype(conn, t2, c2)

        left_fanout = compute_fanout_direction(
            conn, t1, c1, t2, c2,
            hist[a1][c1]["bin_edges"], d1, d2
        )
        right_fanout = compute_fanout_direction(
            conn, t2, c2, t1, c1,
            hist[a2][c2]["bin_edges"], d2, d1
        )

        fanout[(left_key, right_key)] = [left_fanout, right_fanout]
        fanout[(right_key, left_key)] = [right_fanout, left_fanout]

    conn.close()

    # Step 9: Save all updated files
    print("\nStep 9: Saving updated statistics ...")
    save_pkl("abbrev_col_type.pkl", act)
    save_pkl("fanout40.pkl", fanout)
    save_pkl("histogram40.pkl", hist)
    save_pkl("summary40.pkl", summary)
    save_pkl("size.pkl", size)

    # Summary
    print(f"\n=== Done ===")
    print(f"  Total fanout keys: {len(fanout)}")
    print(f"  Total histogram tables with data: {sum(1 for t in hist.values() if t)}")
    print(f"  Total summary tables with data: {sum(1 for t in summary.values() if t)}")


if __name__ == "__main__":
    main()
