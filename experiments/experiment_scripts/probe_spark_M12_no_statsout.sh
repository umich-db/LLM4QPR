#!/bin/bash
# Single-cell probe: spark × train=job × test=job_full × mode 12 cx=4 with
# --removed_fields statsOutput.
#
# Spark plans currently fed to the LLM include a trailing block of planner
# estimates:
#
#     query plan:
#     <tree>
#
#     statsOutput:
#     Join estimated row count: ..., size in bytes: ...
#     Filter estimated row count: ..., size in bytes: ...
#     LogicalRelation estimated row count: ..., size in bytes: ...
#     ...
#
# Those estimates leak the planner's cardinality model directly into the LLM,
# competing with the PRICE branch (which produces the same kind of estimate
# from query stats). This probe strips the statsOutput section so the LLM sees
# only the operator tree and the PRICE branch carries the stats signal alone.
#
# Hypothesis: removing the duplicate signal lets PRICE differentiate itself,
# closing the mode 12 vs mode 7 gap on spark.
#
# Target cell: spark train=job test=job_full (worst-case for true mode 12).
# Baseline (no removal):
#   L-4 M12/M7 p90 ratio = 2.061
#   sentBert M12/M7 p90 ratio = 1.360
#
# Output CSV filename: contains `_rm-stOut` (from REMOVED_FIELDS_SUFFIX in
# run_llm_time.sh and the matching category_abbrev in utilsLLM.py).
# Embeddings cache will live in embeddings_rm/spark/ rather than
# embeddings/spark/ — see utilsLLM.py:3226-3227.

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."
source "$SCRIPT_DIR/_compare_modes_lib.sh"

export MODEL="${MODEL:-sentence-transformers/all-MiniLM-L12-v2}"
export REMOVED_FIELDS="statsOutput"   # lib's build_shared forwards as --removed_fields
DB_ENGINES=(spark)
WORKLOADS_ARR=(job_full)
MODES_ARR=(12)

# Keep cx=4 default; we want to test the removal in isolation, not stack it
# with capacity reduction.
run_ablation
