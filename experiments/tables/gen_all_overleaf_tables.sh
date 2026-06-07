#!/usr/bin/env bash
# Generate all 6 overleaf time-task tables (3 systems x 2 dataset groups) with the
# canonical retrainMLP cell substitution applied:
#   bert2:duckdb:tpcds  +  sentbert:spark:tpcds
# (the flag is global; each per-db table only applies its matching cells).
#
# Output: experiments/tables/overleaf_table_time_<db>_g{1,2}.tex
set -euo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # -> experiments/
source ~/venvs/tmpenv/bin/activate 2>/dev/null || true

CELLS="bert2:duckdb:tpcds sentbert:spark:tpcds"
G1="tpch,tpcds,syn"
G2="job,job_full,stats"
mkdir -p tables

for db in postgres duckdb spark; do
    python generate_overleaf_table_time.py --db "$db" --datasets "$G1" --task time \
        --frzeven_retrainMLP_cells $CELLS \
        --output "tables/overleaf_table_time_${db}_g1.tex"
    python generate_overleaf_table_time.py --db "$db" --datasets "$G2" --task time \
        --frzeven_retrainMLP_cells $CELLS \
        --output "tables/overleaf_table_time_${db}_g2.tex"
done

echo "Done: 6 tables written to tables/overleaf_table_time_{postgres,duckdb,spark}_g{1,2}.tex"
