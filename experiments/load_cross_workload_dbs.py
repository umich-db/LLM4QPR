#!/usr/bin/env python3
"""
Load cross-workload databases into PostgreSQL from CSV files.

Reads schema DDL from zero-shot-cost-estimation/cross_db_benchmark/datasets/{db}/schema_sql/postgres.sql
and loads CSV data using COPY with kwargs from schema.json.

Usage:
    python load_cross_workload_dbs.py --data_dir /root/zero-shot-data/datasets
    python load_cross_workload_dbs.py --data_dir /root/zero-shot-data/datasets --db financial
    python load_cross_workload_dbs.py --data_dir /root/zero-shot-data/datasets --db all --force
"""

import os
import sys
import json
import argparse
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

SCHEMA_BASE = "/root/zero-shot-cost-estimation/cross_db_benchmark/datasets"

# Database definitions: db_name -> (source_dataset, data_folder, scale)
# source_dataset: directory name under SCHEMA_BASE for schema files
# data_folder: directory name under data_dir for CSV files
DATABASES = {
    # Unscaled (scale=1)
    "airline":       ("airline",       "airline",               1),
    "ssb":           ("ssb",           "ssb",                   1),
    "walmart":       ("walmart",       "walmart",               1),
    "accidents":     ("accidents",     "accidents",             1),
    # Scaled
    "financial":     ("financial",     "scaled_financial",      4),
    "basketball":    ("basketball",    "scaled_basketball",     200),
    "movielens":     ("movielens",     "scaled_movielens",      8),
    "baseball":      ("baseball",      "scaled_baseball",       10),
    "hepatitis":     ("hepatitis",     "scaled_hepatitis",      2000),
    "tournament":    ("tournament",    "scaled_tournament",     50),
    "credit":        ("credit",        "scaled_credit",         5),
    "employee":      ("employee",      "scaled_employee",       3),
    "consumer":      ("consumer",      "scaled_consumer",       6),
    "geneea":        ("geneea",        "scaled_geneea",         23),
    "genome":        ("genome",        "scaled_genome",         6),
    "carcinogenesis":("carcinogenesis","scaled_carcinogenesis",  674),
    "seznam":        ("seznam",        "scaled_seznam",         2),
    "fhnk":          ("fhnk",          "scaled_fhnk",           2),
}


def get_admin_conn():
    """Connect to the default postgres database for admin operations."""
    conn = psycopg2.connect(dbname="postgres", user="root", host="/var/run/postgresql")
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    return conn


def get_db_conn(db_name):
    """Connect to a specific database."""
    conn = psycopg2.connect(dbname=db_name, user="root", host="/var/run/postgresql")
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    return conn


def db_exists(db_name):
    """Check if a database already exists."""
    conn = get_admin_conn()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
    exists = cur.fetchone() is not None
    cur.close()
    conn.close()
    return exists


def load_database(db_name, data_dir, force=False):
    """Load a single database into PostgreSQL."""
    source_dataset, data_folder, scale = DATABASES[db_name]

    schema_sql_path = os.path.join(SCHEMA_BASE, source_dataset, "schema_sql", "postgres.sql")
    schema_json_path = os.path.join(SCHEMA_BASE, source_dataset, "schema.json")
    csv_dir = os.path.join(data_dir, data_folder)

    # For unscaled databases, try the source dataset name if scaled dir doesn't exist
    if not os.path.isdir(csv_dir) and scale == 1:
        csv_dir = os.path.join(data_dir, source_dataset)

    if not os.path.isfile(schema_sql_path):
        print(f"  ERROR: Schema SQL not found: {schema_sql_path}")
        return False
    if not os.path.isfile(schema_json_path):
        print(f"  ERROR: Schema JSON not found: {schema_json_path}")
        return False
    if not os.path.isdir(csv_dir):
        print(f"  ERROR: CSV directory not found: {csv_dir}")
        return False

    # Check if DB exists
    if db_exists(db_name):
        if not force:
            print(f"  Database '{db_name}' already exists (use --force to recreate)")
            return True
        print(f"  Dropping existing database '{db_name}'...")
        conn = get_admin_conn()
        cur = conn.cursor()
        cur.execute(f'DROP DATABASE IF EXISTS "{db_name}"')
        cur.close()
        conn.close()

    # Create database
    print(f"  Creating database '{db_name}'...")
    conn = get_admin_conn()
    cur = conn.cursor()
    cur.execute(f'CREATE DATABASE "{db_name}"')
    cur.close()
    conn.close()

    # Load schema
    print(f"  Loading schema from {schema_sql_path}...")
    with open(schema_sql_path, "r") as f:
        schema_sql = f.read()

    conn = get_db_conn(db_name)
    cur = conn.cursor()
    cur.execute(schema_sql)
    cur.close()
    conn.close()

    # Load data
    with open(schema_json_path, "r") as f:
        schema = json.load(f)

    tables = schema["tables"]
    copy_kwargs = schema.get("db_load_kwargs", {}).get("postgres", "CSV HEADER;")
    # Ensure it ends with semicolon
    if not copy_kwargs.strip().endswith(";"):
        copy_kwargs = copy_kwargs.strip() + ";"

    conn = get_db_conn(db_name)
    cur = conn.cursor()

    for table in tables:
        csv_path = os.path.join(csv_dir, f"{table}.csv")
        if not os.path.isfile(csv_path):
            print(f"    WARNING: CSV not found: {csv_path}, skipping")
            continue

        file_size = os.path.getsize(csv_path)
        print(f"    Loading {table} ({file_size / 1024 / 1024:.1f} MB)...")

        copy_sql = f'COPY "{table}" FROM \'{csv_path}\' {copy_kwargs}'
        try:
            cur.execute(copy_sql)
        except Exception as e:
            print(f"      ERROR loading {table}: {e}")
            # Try to continue with remaining tables
            conn.close()
            conn = get_db_conn(db_name)
            cur = conn.cursor()
            continue

    # Vacuum analyze
    print(f"  Running VACUUM ANALYZE...")
    cur.execute("VACUUM ANALYZE")

    # Report row counts
    for table in tables:
        try:
            cur.execute(f'SELECT count(*) FROM "{table}"')
            count = cur.fetchone()[0]
            print(f"    {table}: {count:,} rows")
        except Exception:
            pass

    cur.close()
    conn.close()
    return True


def main():
    parser = argparse.ArgumentParser(description="Load cross-workload databases into PostgreSQL")
    parser.add_argument("--data_dir", required=True, help="Root data directory containing CSV folders")
    parser.add_argument("--db", default="all", help="Database to load (or 'all')")
    parser.add_argument("--force", action="store_true", help="Recreate existing databases")
    args = parser.parse_args()

    if args.db == "all":
        dbs = list(DATABASES.keys())
    else:
        if args.db not in DATABASES:
            print(f"Unknown database: {args.db}. Valid: {list(DATABASES.keys())}")
            sys.exit(1)
        dbs = [args.db]

    success = 0
    failed = 0
    for db_name in dbs:
        print(f"\n{'='*60}")
        print(f"Loading: {db_name}")
        print(f"{'='*60}")
        if load_database(db_name, args.data_dir, args.force):
            success += 1
        else:
            failed += 1

    print(f"\n{'='*60}")
    print(f"Done: {success} loaded, {failed} failed")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
