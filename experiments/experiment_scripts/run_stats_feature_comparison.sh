#!/bin/bash
# Compare LLM performance with and without stats token injection (llm only)
#
# Usage:
#   bash experiment_scripts/run_stats_feature_comparison.sh "tpch" tpch "meta-llama/Llama-3.1-8B" "meta-llama-Llama-3.1-8B" 42 time
#
# Args:
#   1) TRAIN_WORKLOADS (space-separated)
#   2) WORKLOAD_TEST
#   3) MODEL_NAME
#   4) MODEL_NAME1 (sanitized for filenames)
#   5) SEED
#   6) TASK: time | card | both
#
# Optional env:
#   TRAIN_RATIO, EMBED_SIZE, BUCKETIZE_INPUT, QUANTIFICATION, REMOVED_FIELDS,
#   LLM_DOWNSTREAM, VERBOSE_INFO, STATS_PG_STATS_PATH, STATS_TABLE_SIZES_PATH, STATS_TOKEN_MODE,
#   CONCAT_TRUE_EMBEDDINGS, QUERIES_TRUE_DIR

IFS=' ' read -r -a TRAIN_WLS <<< "$1"
WORKLOAD_TEST=$2
MODEL_NAME=$3
MODEL_NAME1=$4
SEED=$5
TASK=$6

TRAIN_RATIO=${TRAIN_RATIO:-1.0}
EMBED_SIZE=${EMBED_SIZE:-1000}
HID_UNITS=${HID_UNITS:-2048}
LR=${LR:-0.0001}
BATCH_SIZE=${BATCH_SIZE:-64}

BUCKETIZE_ARG=""
BUCKETIZE_SUFFIX=""
QUANTIFICATION_ARG=""
QUANTIFICATION_SUFFIX=""
VERBOSE_ARG=""
DOWNSTREAM_ARG=""
DOWNSTREAM_SUFFIX=""
REMOVED_FIELDS_ARG=""
REMOVED_FIELDS_SUFFIX=""

if [[ "$BUCKETIZE_INPUT" != "None" && "$BUCKETIZE_INPUT" != "" ]]; then
  BUCKETIZE_ARG="--bucketize_input $BUCKETIZE_INPUT"
  BUCKETIZE_SUFFIX="_bucketize-${BUCKETIZE_INPUT}"
fi

if [[ "$QUANTIFICATION" != "None" && "$QUANTIFICATION" != "" ]]; then
  QUANTIFICATION_ARG="--quantification $QUANTIFICATION"
  QUANTIFICATION_SUFFIX="_quant-${QUANTIFICATION}"
fi

if [[ "$VERBOSE_INFO" == "true" || "$VERBOSE_INFO" == "True" ]]; then
  VERBOSE_ARG="--verbose_info"
fi

if [[ -n "$LLM_DOWNSTREAM" && "$LLM_DOWNSTREAM" != "" ]]; then
  DOWNSTREAM_ARG="--llm_downstream $LLM_DOWNSTREAM"
  if [[ "$LLM_DOWNSTREAM" != "mlp" ]]; then
    DOWNSTREAM_SUFFIX="_downstream-${LLM_DOWNSTREAM}"
  fi
fi

if [[ -n "$REMOVED_FIELDS" && "$REMOVED_FIELDS" != "" ]]; then
  REMOVED_FIELDS_ARG="--removed_fields $REMOVED_FIELDS"
  IFS=',' read -ra FIELD_CATS <<< "$REMOVED_FIELDS"
  SUFFIX_PARTS=()
  for cat in "${FIELD_CATS[@]}"; do
    cat_trimmed=$(echo "$cat" | tr -d ' ')
    case "$cat_trimmed" in
      operator_structure_and_config) SUFFIX_PARTS+=("ops") ;;
      cost) SUFFIX_PARTS+=("cost") ;;
      cardinality) SUFFIX_PARTS+=("card") ;;
      conditions_and_filters) SUFFIX_PARTS+=("cond") ;;
      metadata_and_config) SUFFIX_PARTS+=("meta") ;;
      *) echo "Warning: Unknown category '$cat_trimmed' ignored" ;;
    esac
  done
  if [ ${#SUFFIX_PARTS[@]} -gt 0 ]; then
    REMOVED_FIELDS_SUFFIX="_rm-$(IFS=-; echo "${SUFFIX_PARTS[*]}")"
  fi
fi

RESULTS_DIR="results"
LOGS_DIR="logs"
if [[ "$REMOVED_FIELDS_SUFFIX" == *_rm-* ]]; then
  RESULTS_DIR="results_rm"
  LOGS_DIR="logs_rm"
fi

STATS_ARGS=""
STATS_SUFFIX=""
if [[ -n "$STATS_PG_STATS_PATH" ]]; then
  STATS_ARGS="$STATS_ARGS --stats_pg_stats_path $STATS_PG_STATS_PATH"
fi
if [[ -n "$STATS_TABLE_SIZES_PATH" ]]; then
  STATS_ARGS="$STATS_ARGS --stats_table_sizes_path $STATS_TABLE_SIZES_PATH"
fi
if [[ -n "$STATS_TOKEN_MODE" ]]; then
  STATS_ARGS="$STATS_ARGS --stats_token_mode $STATS_TOKEN_MODE"
  STATS_SUFFIX="_statTok-${STATS_TOKEN_MODE}"
fi

CONCAT_TRUE_ARG=""
CONCAT_TRUE_SUFFIX=""
if [[ "$CONCAT_TRUE_EMBEDDINGS" == "true" || "$CONCAT_TRUE_EMBEDDINGS" == "True" ]]; then
  CONCAT_TRUE_ARG="--concat_true_embeddings"
  CONCAT_TRUE_SUFFIX="_trueEmb"
  if [[ -n "$QUERIES_TRUE_DIR" ]]; then
    CONCAT_TRUE_ARG="$CONCAT_TRUE_ARG --queries_true_dir $QUERIES_TRUE_DIR"
  fi
fi

# build the parallel array of dat_paths
DAT_PATHS=()
for wl in "${TRAIN_WLS[@]}"; do
  if [[ "$wl" == "syn" || "$wl" == "job" || "$wl" == "job_full" ]]; then
    DAT_PATHS+=( "../queryPlans/imdb/postgres/" )
  elif [[ "$wl" == "genome" || "$wl" == "financial" || "$wl" == "movielens" || \
          "$wl" == "geneea" || "$wl" == "seznam" || "$wl" == "tpc_h" || \
          "$wl" == "walmart" || "$wl" == "airline" || "$wl" == "carcinogenesis" || \
          "$wl" == "baseball" || "$wl" == "imdb" || "$wl" == "accidents" || \
          "$wl" == "ssb" || "$wl" == "basketball" || "$wl" == "employee" || \
          "$wl" == "fhnk" || "$wl" == "consumer" || "$wl" == "tournament" || \
          "$wl" == "credit" || "$wl" == "hepatitis" ]]; then
    DAT_PATHS+=( "../deepdb_augmented/$wl/" )
  else
    DAT_PATHS+=( "../queryPlans/$wl/postgres/" )
  fi
done

if [[ "$WORKLOAD_TEST" == "syn" || "$WORKLOAD_TEST" == "job" || "$WORKLOAD_TEST" == "job_full" ]]; then
  DAT_PATH_TEST="../queryPlans/imdb/postgres/"
elif [[ "$WORKLOAD_TEST" == "synthetic" || "$WORKLOAD_TEST" == "job-light" ]]; then
  DAT_PATH_TEST="../deepdb_augmented/imdb/"
elif [[ "$WORKLOAD_TEST" == "genome" || "$WORKLOAD_TEST" == "financial" || "$WORKLOAD_TEST" == "movielens" || \
        "$WORKLOAD_TEST" == "geneea" || "$WORKLOAD_TEST" == "seznam" || "$WORKLOAD_TEST" == "tpc_h" || \
        "$WORKLOAD_TEST" == "walmart" || "$WORKLOAD_TEST" == "airline" || "$WORKLOAD_TEST" == "carcinogenesis" || \
        "$WORKLOAD_TEST" == "baseball" || "$WORKLOAD_TEST" == "imdb" || "$WORKLOAD_TEST" == "accidents" || \
        "$WORKLOAD_TEST" == "ssb" || "$WORKLOAD_TEST" == "basketball" || "$WORKLOAD_TEST" == "employee" || \
        "$WORKLOAD_TEST" == "fhnk" || "$WORKLOAD_TEST" == "consumer" || "$WORKLOAD_TEST" == "tournament" || \
        "$WORKLOAD_TEST" == "credit" || "$WORKLOAD_TEST" == "hepatitis" ]]; then
  DAT_PATH_TEST="../deepdb_augmented/$WORKLOAD_TEST/"
else
  DAT_PATH_TEST="../queryPlans/$WORKLOAD_TEST/postgres/"
fi

TRAIN_WLS_HYPHEN="${TRAIN_WLS[0]}"
for elt in "${TRAIN_WLS[@]:1}"; do
  TRAIN_WLS_HYPHEN+="-$elt"
done

run_task() {
  local task_label=$1
  local card_flag=$2
  local inject_flag=$3
  local inject_suffix=$4

  python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
    --output_dir_qerror ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/${task_label}_llm_${TRAIN_RATIO}_cdf_postgres_${LR}_b${BATCH_SIZE}_h${HID_UNITS}_${MODEL_NAME1}_emb${EMBED_SIZE}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${DOWNSTREAM_SUFFIX}${REMOVED_FIELDS_SUFFIX}${inject_suffix}${STATS_SUFFIX}_seed${SEED}.csv \
    --output_dir_abs ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/${task_label}_llm_${TRAIN_RATIO}_cdf_postgres_${LR}_b${BATCH_SIZE}_h${HID_UNITS}_${MODEL_NAME1}_emb${EMBED_SIZE}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${DOWNSTREAM_SUFFIX}${REMOVED_FIELDS_SUFFIX}${inject_suffix}${STATS_SUFFIX}_seed${SEED}_abs.txt \
    --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/${task_label}_llm_${TRAIN_RATIO}_cdf_postgres_${LR}_b${BATCH_SIZE}_h${HID_UNITS}_${MODEL_NAME1}_emb${EMBED_SIZE}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${DOWNSTREAM_SUFFIX}${REMOVED_FIELDS_SUFFIX}${inject_suffix}${STATS_SUFFIX}_seed${SEED}.log \
    --db postgres \
    --workloads_train "${TRAIN_WLS[@]}" \
    --workload_test ${WORKLOAD_TEST} \
    --algo llm \
    --learning_rate $LR \
    --batch_size $BATCH_SIZE \
    --hid_units $HID_UNITS \
    --model_name $MODEL_NAME \
    --embed_size $EMBED_SIZE \
    --train_ratio $TRAIN_RATIO \
    --llm_mode inference \
    --seed $SEED \
    $BUCKETIZE_ARG \
    $QUANTIFICATION_ARG \
    $VERBOSE_ARG \
    $DOWNSTREAM_ARG \
    $REMOVED_FIELDS_ARG \
    $card_flag \
    $inject_flag \
    $CONCAT_TRUE_ARG \
    $STATS_ARGS
}

if [[ "$TASK" == "time" || "$TASK" == "both" ]]; then
  run_task "time" "" "" ""
  run_task "time" "" "--stats_token_inject" "_statTok"
fi

if [[ "$TASK" == "card" || "$TASK" == "both" ]]; then
  run_task "card" "--card" "" ""
  run_task "card" "--card" "--stats_token_inject" "_statTok"
fi
