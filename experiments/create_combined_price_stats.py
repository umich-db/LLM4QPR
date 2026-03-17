"""
Create combined PRICE statistics for multi-database cross-workload training.

Merges PRICE .pkl files from multiple databases into one combined set.
Since all PRICE aliases are globally unique (e.g., fin_a vs imdb_t),
merging is conflict-free.

Usage:
    python create_combined_price_stats.py --exclude tpc_h --output cross_train_tpc_h
    python create_combined_price_stats.py --exclude imdb --output cross_train_imdb
    python create_combined_price_stats.py --dbs financial genome accidents --output small_test
"""

import os
import sys
import pickle
import argparse

sys.path.insert(0, os.path.dirname(__file__))
from cross_workload_price_config import ALL_CROSS_WORKLOAD_DBS

PRICE_STATS_BASE = "/root/PRICE/datas/statistics/finetune"


def load_pkl(db_name, fname):
    """Load a single .pkl file for a database."""
    fpath = os.path.join(PRICE_STATS_BASE, db_name, fname)
    if not os.path.exists(fpath):
        return None
    with open(fpath, "rb") as f:
        return pickle.load(f)


def create_combined_stats(db_names, output_name):
    """Merge PRICE stats from multiple databases into one combined directory.

    Args:
        db_names: list of database names to merge
        output_name: name for the combined output directory
    """
    print(f"Creating combined stats: {output_name}")
    print(f"  Databases: {db_names}")

    # Merged data structures
    merged_abbrev = {}
    merged_col_type = {}
    merged_size = {}
    merged_histogram = {}
    merged_summary = {}
    merged_fanout = {}

    for db_name in db_names:
        print(f"\n  Loading {db_name} ...")

        # abbrev_col_type.pkl
        act = load_pkl(db_name, "abbrev_col_type.pkl")
        if act is None:
            print(f"    WARNING: No stats for {db_name}, skipping")
            continue

        merged_abbrev.update(act["abbrev"])
        merged_col_type.update(act["col_type"])

        # size.pkl
        sz = load_pkl(db_name, "size.pkl")
        if sz:
            merged_size.update(sz)

        # histogram40.pkl
        hist = load_pkl(db_name, "histogram40.pkl")
        if hist:
            merged_histogram.update(hist)

        # summary40.pkl
        summ = load_pkl(db_name, "summary40.pkl")
        if summ:
            merged_summary.update(summ)

        # fanout40.pkl
        fan = load_pkl(db_name, "fanout40.pkl")
        if fan:
            merged_fanout.update(fan)

        print(f"    Tables: {len(act['abbrev'])}, "
              f"Size: {len(sz) if sz else 0}, "
              f"Hist: {sum(len(v) for v in hist.values()) if hist else 0}, "
              f"Summ: {sum(len(v) for v in summ.values()) if summ else 0}, "
              f"Fanout: {len(fan) if fan else 0}")

    # Save combined files
    output_dir = os.path.join(PRICE_STATS_BASE, output_name)
    os.makedirs(output_dir, exist_ok=True)

    files = {
        "abbrev_col_type.pkl": {"abbrev": merged_abbrev, "col_type": merged_col_type},
        "size.pkl": merged_size,
        "histogram40.pkl": merged_histogram,
        "summary40.pkl": merged_summary,
        "fanout40.pkl": merged_fanout,
    }

    print(f"\n  Saving to {output_dir}/ ...")
    for fname, data in files.items():
        fpath = os.path.join(output_dir, fname)
        with open(fpath, "wb") as f:
            pickle.dump(data, f)
        print(f"    {fname}")

    n_tables = len(merged_abbrev)
    n_hist = sum(len(v) for v in merged_histogram.values())
    n_summ = sum(len(v) for v in merged_summary.values())
    n_fan = len(merged_fanout)
    print(f"\n  Combined stats: {n_tables} tables, "
          f"{n_hist} histogram cols, {n_summ} summary cols, "
          f"{n_fan} fanout entries")
    print(f"  DONE: {output_name}")


def main():
    parser = argparse.ArgumentParser(
        description="Create combined PRICE statistics for cross-workload training"
    )
    parser.add_argument(
        "--dbs", type=str, nargs="*", default=None,
        help="Specific databases to include (default: all)"
    )
    parser.add_argument(
        "--exclude", type=str, nargs="*", default=[],
        help="Databases to exclude"
    )
    parser.add_argument(
        "--output", type=str, required=True,
        help="Output directory name under PRICE_STATS_BASE"
    )
    args = parser.parse_args()

    if args.dbs:
        db_names = args.dbs
    else:
        db_names = [d for d in ALL_CROSS_WORKLOAD_DBS if d not in args.exclude]

    if not db_names:
        print("No databases selected!")
        sys.exit(1)

    create_combined_stats(db_names, args.output)


if __name__ == "__main__":
    main()
