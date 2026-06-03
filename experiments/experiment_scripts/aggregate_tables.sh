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
#   PRICEB_EQUIV_WORKLOADS  workloads where mode-7b priceB reuses priceN's cdf
#            (default: "syn job job_full stats"). Set to "" (or pass
#            --no-priceb-equiv) to turn the priceB<-priceN aliasing OFF; or pass
#            --priceb-equiv-workloads "<list>" to customize the set.

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SELF="$SCRIPT_DIR/$(basename "${BASH_SOURCE[0]}")"  # absolute path for --help (cd below)
cd "$SCRIPT_DIR/.."

# ─── Defaults / env ─────────────────────────────────────────────────────────
MODEL="${MODEL:-sentbert}"
ANCHOR="${ANCHOR:-90}"
MLP="${MLP:-both}"
DBS="${DBS:-postgres duckdb spark}"
WORKLOADS="${WORKLOADS:-stats syn job job_full tpcds tpch}"
TASK="${TASK:-time}"
# Workloads where mode-7b priceB borrows the matching mode-7 priceN cdf (the two
# are feature-equivalent there). `-` (not `:-`) so an explicitly-empty env value
# disables it; a CLI flag below can override either way.
PRICEB_EQUIV_WORKLOADS="${PRICEB_EQUIV_WORKLOADS-syn job job_full stats}"

# ─── CLI overrides ──────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --model)     MODEL="$2";     shift 2 ;;
        --anchor)    ANCHOR="$2";    shift 2 ;;
        --mlp)       MLP="$2";       shift 2 ;;
        --dbs)       DBS="$2";       shift 2 ;;
        --workloads) WORKLOADS="$2"; shift 2 ;;
        --task)      TASK="$2";      shift 2 ;;
        --priceb-equiv-workloads) PRICEB_EQUIV_WORKLOADS="$2"; shift 2 ;;
        --no-priceb-equiv)        PRICEB_EQUIV_WORKLOADS="";   shift   ;;
        -h|--help)
            head -35 "$SELF" | sed 's/^# \?//'
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

# ─── PRICE_B ≡ PRICE_N on imdb-family + stats workloads ──────────────────────
# On syn / job / job_full / stats the original-PRICE design (priceB, mode 7b) and
# PRICE_N (priceN, mode 7) feature sets are equivalent, so the separately-trained
# priceB runs there differ from priceN only by training noise. For those
# workloads we feed to_table_relative a *staged* copy of the result dir in which
# each mode-7b priceB cdf is replaced by the matching mode-7 priceN cdf (both
# jointMLP and retrainMLP, all model families). Real result files are NEVER
# modified — the staging dir is a temp tree of symlinks under the same
# results/<db>/ parent (so to_table_relative's output path + db tag stay
# correct) and is removed on exit. tpch / tpcds keep their own priceB.
# Disable with --no-priceb-equiv (or PRICEB_EQUIV_WORKLOADS=""); customize with
# --priceb-equiv-workloads "<list>". PRICEB_EQUIV_WORKLOADS is resolved above
# (defaults + CLI), so it is intentionally not reassigned here.
_STAGED_DIRS=()
_cleanup_staged() { local t; for t in "${_STAGED_DIRS[@]:-}"; do [[ -n "$t" && -d "$t" ]] && rm -rf "$t"; done; }
trap _cleanup_staged EXIT

_is_priceb_equiv() { case " $PRICEB_EQUIV_WORKLOADS " in *" $1 "*) return 0 ;; *) return 1 ;; esac; }

# stage_priceb_from_pricen <result_dir> <workload> → sets global STAGED_DIR.
# For an equiv workload, STAGED_DIR is a temp dir with priceB cdfs aliased to
# priceN; otherwise it is <result_dir> unchanged.
stage_priceb_from_pricen() {
    local d="$1" wl="$2"
    STAGED_DIR="$d"
    _is_priceb_equiv "$wl" || return 0
    local tmp
    tmp="$(mktemp -d "$(dirname "$d")/.aggtmp_priceb_${wl}_XXXXXX")" || return 0
    _STAGED_DIRS+=("$tmp")
    local f bn pb swapped=0
    # read-only mirror of the real dir's cdfs
    for f in "$d"/*cdf*seed*.csv; do
        [[ -e "$f" ]] && ln -s "$(readlink -f "$f")" "$tmp/$(basename "$f")"
    done
    # replace each plain mode-7 priceN cdf's priceB twin with a copy of priceN
    # (skip mode-12 / 12w cross-attn variants, which also carry priceN tokens)
    for f in "$d"/*cdf*seed*.csv; do
        [[ -e "$f" ]] || continue
        bn="$(basename "$f")"
        case "$bn" in *priceN_priceNor*) ;; *) continue ;; esac
        case "$bn" in *biCrossAttn*|*priceBiCrossAttnJoint*|*inflatePRICE*|*_cx[0-9]*) continue ;; esac
        pb="${bn/priceN_priceNor/priceB}"
        [[ "$pb" == "$bn" ]] && continue
        rm -f "$tmp/$pb"
        cp "$f" "$tmp/$pb"
        swapped=$((swapped + 1))
    done
    echo "    [priceB<-priceN] $wl: aliased $swapped priceN cdf(s) as priceB (real files untouched)"
    STAGED_DIR="$tmp"
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
        stage_priceb_from_pricen "$d" "$wl"   # priceB ← priceN for equiv workloads (sets STAGED_DIR)
        rel_dirs+=("$STAGED_DIR")
    done
    if [[ ${#rel_dirs[@]} -gt 0 ]]; then
        echo "  ─ relative ($db): ${#rel_dirs[@]} dirs"
        python to_table_relative.py --task "$TASK" --anchor "$ANCHOR" "$MODEL_FLAG" $MLP_FLAG \
            --dirs "${rel_dirs[@]}"
    fi
done

echo
echo "Done."
