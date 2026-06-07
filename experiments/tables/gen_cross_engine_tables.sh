#!/usr/bin/env bash
set -euo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # -> experiments/
source ~/venvs/py312/bin/activate 2>/dev/null || source ~/venvs/tmpenv/bin/activate 2>/dev/null || true
for m in bert2 bert4 sentbert; do
    python generate_cross_engine_table.py --model "$m" --anchor 90 \
        --output "tables/cross_engine_table_time_${m}.tex"
done
echo "Done: 3 cross-engine tables in tables/"
