"""
Add 6 missing columns and 1 missing fanout pair to TPC-DS PRICE statistics files.

Updates the following pkl files in-place:
  - abbrev_col_type.pkl  (col_type entries for 6 new columns)
  - histogram40.pkl      (histograms for 4 continuous columns)
  - summary40.pkl        (summaries for 2 discrete columns)
  - fanout40.pkl         (fanout for cs_bill_customer_sk <-> ss_customer_sk)

Columns added:
  1. cs_ship_customer_sk  -> tpcds_cs, continuous
  2. p_channel_event      -> tpcds_pr, discrete
  3. cs_sales_price       -> tpcds_cs, continuous
  4. s_market_id          -> tpcds_s, discrete
  5. cr_return_amount     -> tpcds_cr, continuous
  6. cs_sold_time_sk      -> tpcds_cs, continuous

Fanout added:
  - (tpcds_cs.cs_bill_customer_sk, tpcds_ss.ss_customer_sk) and reverse
"""

import pickle
import numpy as np
import psycopg2

STATS_DIR = "/root/PRICE/datas/statistics/finetune/tpcds/"
DB_PARAMS = dict(dbname="tpcds", user="root", host="/var/run/postgresql")

# Column definitions: (col_name, table_abbrev, pg_table, pg_col)
CONTINUOUS_COLS = [
    ("cs_ship_customer_sk", "tpcds_cs", "catalog_sales", "cs_ship_customer_sk"),
    ("cs_sales_price",      "tpcds_cs", "catalog_sales", "cs_sales_price"),
    ("cr_return_amount",    "tpcds_cr", "catalog_returns", "cr_return_amount"),
    ("cs_sold_time_sk",     "tpcds_cs", "catalog_sales", "cs_sold_time_sk"),
]

DISCRETE_COLS = [
    ("p_channel_event", "tpcds_pr", "promotion",  "p_channel_event"),
    ("s_market_id",     "tpcds_s",  "store",      "s_market_id"),
]

NUM_BINS = 40


def load_pkl(name):
    path = STATS_DIR + name
    with open(path, "rb") as f:
        return pickle.load(f)


def save_pkl(name, data):
    path = STATS_DIR + name
    with open(path, "wb") as f:
        pickle.dump(data, f)
    print(f"  Saved {path}")


def build_histogram(cur, pg_table, pg_col):
    """Build a 40-bin equi-width histogram by querying PostgreSQL."""
    cur.execute(f"SELECT MIN({pg_col}::float8), MAX({pg_col}::float8), COUNT(*) FROM {pg_table} WHERE {pg_col} IS NOT NULL")
    min_val, max_val, total_rows = cur.fetchone()
    min_val = float(min_val)
    max_val = float(max_val)
    total_rows = int(total_rows)

    print(f"    {pg_table}.{pg_col}: min={min_val}, max={max_val}, rows={total_rows}")

    bin_edges = np.linspace(min_val, max_val, NUM_BINS + 1)

    cur.execute(f"""
        SELECT width_bucket({pg_col}::float8, {min_val}, {max_val}, {NUM_BINS}) AS bucket,
               COUNT(*) AS cnt
        FROM {pg_table}
        WHERE {pg_col} IS NOT NULL
        GROUP BY bucket
        ORDER BY bucket
    """)
    bucket_counts = dict(cur.fetchall())

    hist = np.zeros(NUM_BINS, dtype=np.float64)
    for b in range(1, NUM_BINS + 1):
        hist[b - 1] = float(bucket_counts.get(b, 0))

    # Bucket 0 (below min) goes to first bin; bucket NUM_BINS+1 (above max) goes to last bin
    if 0 in bucket_counts:
        hist[0] += float(bucket_counts[0])
    if (NUM_BINS + 1) in bucket_counts:
        hist[NUM_BINS - 1] += float(bucket_counts[NUM_BINS + 1])

    return {
        "hist": hist,
        "bin_edges": bin_edges,
        "len": total_rows,
        "min_value": min_val,
        "max_value": max_val,
    }


def build_summary(cur, pg_table, pg_col):
    """Build a discrete summary (value frequencies) by querying PostgreSQL."""
    cur.execute(f"""
        SELECT {pg_col}, COUNT(*) AS cnt
        FROM {pg_table}
        WHERE {pg_col} IS NOT NULL
        GROUP BY {pg_col}
        ORDER BY cnt DESC
    """)
    rows = cur.fetchall()
    keys = [r[0] for r in rows]
    values = [int(r[1]) for r in rows]
    print(f"    {pg_table}.{pg_col}: {len(keys)} distinct values, top={keys[:5]}")
    return {"keys": keys, "values": values}


def build_fanout(cur, left_table, left_col, right_table, right_col, left_bin_edges, right_bin_edges):
    """
    Build fanout arrays for a join pair.

    For left->right direction:
      For each of 40 bins of left_col, compute avg number of matching rows
      in right_table via right_col.

    For right->left direction:
      For each of 40 bins of right_col, compute avg number of matching rows
      in left_table via left_col.

    Returns: [left_fanout_40, right_fanout_40] (list of two lists, each len 40)
    """
    num_bins = NUM_BINS

    # Left fanout: for each bin of left_col, avg matching right rows
    print(f"    Computing left fanout: {left_table}.{left_col} -> {right_table}.{right_col}")
    left_fanout = []
    for i in range(num_bins):
        lo = left_bin_edges[i]
        hi = left_bin_edges[i + 1]
        if i == num_bins - 1:
            where_clause = f"L.{left_col} >= {lo} AND L.{left_col} <= {hi}"
        else:
            where_clause = f"L.{left_col} >= {lo} AND L.{left_col} < {hi}"
        cur.execute(f"""
            SELECT COALESCE(AVG(cnt), 0) FROM (
                SELECT L.{left_col}, COUNT(R.{right_col}) as cnt
                FROM {left_table} L
                LEFT JOIN {right_table} R ON L.{left_col} = R.{right_col}
                WHERE {where_clause}
                GROUP BY L.{left_col}
            ) sub
        """)
        avg_fanout = float(cur.fetchone()[0])
        left_fanout.append(avg_fanout)
        if (i + 1) % 10 == 0:
            print(f"      Bin {i+1}/{num_bins} done, avg_fanout={avg_fanout:.2f}")

    # Right fanout: for each bin of right_col, avg matching left rows
    print(f"    Computing right fanout: {right_table}.{right_col} -> {left_table}.{left_col}")
    right_fanout = []
    for i in range(num_bins):
        lo = right_bin_edges[i]
        hi = right_bin_edges[i + 1]
        if i == num_bins - 1:
            where_clause = f"R.{right_col} >= {lo} AND R.{right_col} <= {hi}"
        else:
            where_clause = f"R.{right_col} >= {lo} AND R.{right_col} < {hi}"
        cur.execute(f"""
            SELECT COALESCE(AVG(cnt), 0) FROM (
                SELECT R.{right_col}, COUNT(L.{left_col}) as cnt
                FROM {right_table} R
                LEFT JOIN {left_table} L ON R.{right_col} = L.{left_col}
                WHERE {where_clause}
                GROUP BY R.{right_col}
            ) sub
        """)
        avg_fanout = float(cur.fetchone()[0])
        right_fanout.append(avg_fanout)
        if (i + 1) % 10 == 0:
            print(f"      Bin {i+1}/{num_bins} done, avg_fanout={avg_fanout:.2f}")

    return [left_fanout, right_fanout]


def main():
    print("Connecting to PostgreSQL...")
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()

    # Load all pkl files
    print("Loading existing pkl files...")
    abbrev_col_type = load_pkl("abbrev_col_type.pkl")
    histogram = load_pkl("histogram40.pkl")
    summary = load_pkl("summary40.pkl")
    fanout = load_pkl("fanout40.pkl")

    # -------------------------------------------------------------------------
    # 1. Add columns to abbrev_col_type.pkl
    # -------------------------------------------------------------------------
    print("\n=== Step 1: Update abbrev_col_type.pkl ===")
    col_type = abbrev_col_type["col_type"]

    for col_name, table_abbrev, _, _ in CONTINUOUS_COLS:
        if col_name not in col_type[table_abbrev]["ctn"]:
            col_type[table_abbrev]["ctn"].append(col_name)
            print(f"  Added {col_name} to {table_abbrev}/ctn")
        else:
            print(f"  {col_name} already in {table_abbrev}/ctn, skipping")

    for col_name, table_abbrev, _, _ in DISCRETE_COLS:
        if col_name not in col_type[table_abbrev]["dsct"]:
            col_type[table_abbrev]["dsct"].append(col_name)
            print(f"  Added {col_name} to {table_abbrev}/dsct")
        else:
            print(f"  {col_name} already in {table_abbrev}/dsct, skipping")

    save_pkl("abbrev_col_type.pkl", abbrev_col_type)

    # -------------------------------------------------------------------------
    # 2. Add histogram entries for continuous columns
    # -------------------------------------------------------------------------
    print("\n=== Step 2: Update histogram40.pkl ===")
    for col_name, table_abbrev, pg_table, pg_col in CONTINUOUS_COLS:
        if col_name in histogram.get(table_abbrev, {}):
            print(f"  {table_abbrev}.{col_name} already has histogram, skipping")
            continue
        print(f"  Building histogram for {table_abbrev}.{col_name}...")
        if table_abbrev not in histogram:
            histogram[table_abbrev] = {}
        histogram[table_abbrev][col_name] = build_histogram(cur, pg_table, pg_col)

    save_pkl("histogram40.pkl", histogram)

    # -------------------------------------------------------------------------
    # 3. Add summary entries for discrete columns
    # -------------------------------------------------------------------------
    print("\n=== Step 3: Update summary40.pkl ===")
    for col_name, table_abbrev, pg_table, pg_col in DISCRETE_COLS:
        if col_name in summary.get(table_abbrev, {}):
            print(f"  {table_abbrev}.{col_name} already has summary, skipping")
            continue
        print(f"  Building summary for {table_abbrev}.{col_name}...")
        if table_abbrev not in summary:
            summary[table_abbrev] = {}
        summary[table_abbrev][col_name] = build_summary(cur, pg_table, pg_col)

    save_pkl("summary40.pkl", summary)

    # -------------------------------------------------------------------------
    # 4. Add fanout pair: cs_bill_customer_sk <-> ss_customer_sk
    # -------------------------------------------------------------------------
    print("\n=== Step 4: Update fanout40.pkl ===")

    fwd_key = ("tpcds_cs.cs_bill_customer_sk", "tpcds_ss.ss_customer_sk")
    rev_key = ("tpcds_ss.ss_customer_sk", "tpcds_cs.cs_bill_customer_sk")

    if fwd_key in fanout:
        print(f"  Fanout {fwd_key} already exists, skipping")
    else:
        # Get bin edges from existing histograms
        cs_bins = histogram["tpcds_cs"]["cs_bill_customer_sk"]["bin_edges"]
        ss_bins = histogram["tpcds_ss"]["ss_customer_sk"]["bin_edges"]

        print(f"  Building fanout for {fwd_key}...")
        fanout_data = build_fanout(
            cur,
            left_table="catalog_sales", left_col="cs_bill_customer_sk",
            right_table="store_sales", right_col="ss_customer_sk",
            left_bin_edges=cs_bins, right_bin_edges=ss_bins,
        )

        # Forward direction: [left_fanout, right_fanout]
        fanout[fwd_key] = fanout_data
        # Reverse direction: swap the two arrays
        fanout[rev_key] = [fanout_data[1], fanout_data[0]]
        print(f"  Added fanout for both directions")

    save_pkl("fanout40.pkl", fanout)

    cur.close()
    conn.close()
    print("\nDone! All statistics files updated successfully.")


if __name__ == "__main__":
    main()
