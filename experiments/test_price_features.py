#!/usr/bin/env python3
"""Test PRICE feature generation for a given workload."""
import sys
import os

# Must run from PRICE root for imports
os.chdir("/root/PRICE")
sys.path.insert(0, "/root/PRICE")
sys.path.insert(0, "/root/LLM4QPR/experiments")

from price_data_utils import (
    extract_raw_sql_from_queries_true,
    get_db_name_for_workload,
    get_sql_file_for_workload,
    generate_price_features,
)

workload = sys.argv[1] if len(sys.argv) > 1 else "imdb_job"
db_name = get_db_name_for_workload(workload)
sql_file = get_sql_file_for_workload(workload)

print(f"Workload: {workload}, db: {db_name}, sql_file: {sql_file}")

sql_list = extract_raw_sql_from_queries_true(sql_file)
print(f"{workload}: {len(sql_list)} queries")

result = generate_price_features(workload, sql_list, db_name)
