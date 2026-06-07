#!/bin/bash
# Wait for a tpcds-pool tmux session to finish, then re-run every model that OOM'd
# during it at a smaller batch (2), escalating to batch 1 for any that still OOM.
# Self-contained so it can be launched once and left to run.
#
# Usage (in its own tmux session, on the same machine as the pool run):
#   SESSION=tpcds_poolC LOG=/tmp/tpcds_poolC.log \
#     bash .../tpcds_retry_oom_after_pass.sh
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Activate the GPU venv — run_different_llms.sh does NOT source one itself, so
# without this the retry's train.py crashes at "import torch" (ModuleNotFound).
source ~/venvs/py312/bin/activate 2>/dev/null || source ~/venvs/tmpenv/bin/activate 2>/dev/null || true
: "${SESSION:?set SESSION (the pool tmux session to wait on)}"
: "${LOG:?set LOG (the pool run log to scan for OOMs)}"

oom_from () {  # extract distinct model names that OOM'd in a log
    awk '/Running: Model=/{m=$0; sub(/.*Model=/,"",m); sub(/,.*/,"",m)}
         /out of memory|OutOfMemory|CUDA error/{print m}' "$1" 2>/dev/null | sort -u | paste -sd,
}
run_retry () {  # $1=batch  $2=models_csv  $3=logfile
    echo "[retry] ft_batch_size=$1 models: $2"
    MODELS_CSV="$2" FT_BATCH="$1" \
        bash "$SCRIPT_DIR/master_tpcds_inflatePRICE_e16_retry.sh" 2>&1 | tee "$3"
}

echo "[retry-wait] waiting for tmux session '$SESSION' to finish..."
while tmux has-session -t "$SESSION" 2>/dev/null; do sleep 120; done
echo "[retry-wait] '$SESSION' done. Scanning $LOG ..."

OOM=$(oom_from "$LOG")
if [ -z "$OOM" ]; then echo "[retry-wait] no OOM models; nothing to do."; exit 0; fi

B2_LOG="/tmp/${SESSION}_retry_b2.log"
run_retry 2 "$OOM" "$B2_LOG"

STILL=$(oom_from "$B2_LOG")
if [ -n "$STILL" ]; then
    echo "[retry-wait] still OOM at batch 2 -> retrying at batch 1: $STILL"
    run_retry 1 "$STILL" "/tmp/${SESSION}_retry_b1.log"
fi
echo "[retry-wait] retry pass complete for $SESSION."
