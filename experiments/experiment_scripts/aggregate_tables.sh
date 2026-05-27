#!/bin/bash
# Driver for to_table_seeds.py + to_table_relative.py across (db, workload)
# cells. Lets you pick model family, anchor quantile, MLP variant, db subset,
# and workload subset via env vars / CLI flags. Defaults match the
# previously-manual invocation: sentBert, anchor 90, all dbs, all workloads,
# both jointMLP and retrainMLP.
#
# Usage examples:
#
#   bash experiment_scripts/aggregate_tables.sh
#       # all dbs × all workloads, sentBert, anchor=90, both MLP variants
#
#   MODEL=bert2 ANCHOR=95 MLP=retrainMLP \
#     bash experiment_scripts/aggregate_tables.sh
#       # bert_uncased_L-2_H-256, anchor=95, retrainMLP only
#
#   DBS="spark" WORKLOADS="stats job_full" \
#     bash experiment_scripts/aggregate_tables.sh
#       # spark on just stats + job_full (the imdb-family job_full goes
#       #  through train=job test=job_full automatically)
#
# Flags (all overridable via env or --flag value):
#   MODEL    sentbert | bert2 | bert4          (default: sentbert)
#   ANCHOR   50 | 90 | 95 | max                 (default: 90)
#   MLP      both | jointMLP | retrainMLP       (default: both)
#   DBS      space-separated list of dbs        (default: "postgres duckdb spark")
#   WORKLOADS space-separated workload tokens   (default: "stats syn job job_full tpcds tpch")
#                                                Each token TS resolves to
#                                                  train=imdb-canonical(TS) Test=TS
#                                                (syn/job/job_full → train=job)
#   TASK     time | card                        (default: time)

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# ─── Defaults / env ─────────────────────────────────────────────────────────
MODEL="${MODEL:-sentbert}"
ANCHOR="${ANCHOR:-90}"
MLP="${MLP:-both}"
DBS="${DBS:-postgres duckdb spark}"
WORKLOADS="${WORKLOADS:-stats syn job job_full tpcds tpch}"
TASK="${TASK:-time}"

# ─── CLI overrides ──────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --model)     MODEL="$2";     shift 2 ;;
        --anchor)    ANCHOR="$2";    shift 2 ;;
        --mlp)       MLP="$2";       shift 2 ;;
        --dbs)       DBS="$2";       shift 2 ;;
        --workloads) WORKLOADS="$2"; shift 2 ;;
        --task)      TASK="$2";      shift 2 ;;
        -h|--help)
            head -36 "$0" | sed 's/^# \?//'
            exit 0 ;;
        *) echo "Unknown flag: $1" >&2; exit 1 ;;
    esac
done

# ─── Translate MODEL → to_table flag ────────────────────────────────────────
case "$MODEL" in
    sentbert) MODEL_FLAG="--sentbert_only" ;;
    bert2)    MODEL_FLAG="--bert2_only" ;;
    bert4)    MODEL_FLAG="--bert_only" ;;
    *) echo "MODEL must be one of: sentbert, bert2, bert4 (got: $MODEL)" >&2; exit 1 ;;
esac

# ─── Translate MLP → to_table flag ──────────────────────────────────────────
case "$MLP" in
    both)        MLP_FLAG="" ;;
    jointMLP)    MLP_FLAG="--exclude_retrain_mlp" ;;
    retrainMLP)  MLP_FLAG="--retrain_mlp_only" ;;
    *) echo "MLP must be one of: both, jointMLP, retrainMLP (got: $MLP)" >&2; exit 1 ;;
esac

# ─── Translate workload test-name → (train, test) pair ──────────────────────
# train workload is the imdb-canonical:  syn|job|job_full → job, others → self.
canonical_train_for() {
    case "$1" in
        syn|job|job_full|jobm) echo "job" ;;
        *) echo "$1" ;;
    esac
}

echo "============================================================"
echo "  MODEL=$MODEL  ANCHOR=$ANCHOR  MLP=$MLP  TASK=$TASK"
echo "  DBS:       $DBS"
echo "  WORKLOADS: $WORKLOADS"
echo "============================================================"

# ─── Main loop ──────────────────────────────────────────────────────────────
for db in $DBS; do
    echo
    echo "─── $db ──────────────────────────────────────────────────────────────"
    rel_dirs=()
    for wl in $WORKLOADS; do
        tr=$(canonical_train_for "$wl")
        d="results/$db/results_Train_${tr}_Test_${wl}_ours"
        if [[ ! -d "$d" ]]; then
            echo "  [skip] no dir: $d"
            continue
        fi
        echo "  ─ seeds: $d"
        python to_table_seeds.py --dir "$d" --task "$TASK" "$MODEL_FLAG" $MLP_FLAG
        rel_dirs+=("$d")
    done
    if [[ ${#rel_dirs[@]} -gt 0 ]]; then
        echo "  ─ relative ($db): ${#rel_dirs[@]} dirs"
        python to_table_relative.py --task "$TASK" --anchor "$ANCHOR" "$MODEL_FLAG" $MLP_FLAG \
            --dirs "${rel_dirs[@]}"
    fi
done

echo
echo "Done."
