
# 1) split the first arg into an array of workloads:
IFS=' ' read -r -a TRAIN_WLS <<< "$1"
WORKLOAD_TEST=$2
train_ratio=$3
finetune=$4
model_name=$5
model_name1=$6
SEED=$7

# Database engine (default: postgres, can be set to duckdb via DB_ENGINE env var)
DB_ENGINE=${DB_ENGINE:-postgres}

# 2) build the parallel array of dat_paths:
DAT_PATHS=()
for wl in "${TRAIN_WLS[@]}"; do
  if [[ "$wl" == "syn" || "$wl" == "job" || "$wl" == "job_full" || "$wl" == "jobm" ]]; then
    DAT_PATHS+=( "../queryPlans/imdb/${DB_ENGINE}/" )
  elif [[ "$wl" == "genome" || "$wl" == "financial" || "$wl" == "movielens" || \
          "$wl" == "geneea" || "$wl" == "seznam" || "$wl" == "tpc_h" || \
          "$wl" == "walmart" || "$wl" == "airline" || "$wl" == "carcinogenesis" || \
          "$wl" == "baseball" || "$wl" == "imdb" || "$wl" == "accidents" || \
          "$wl" == "ssb" || "$wl" == "basketball" || "$wl" == "employee" || \
          "$wl" == "fhnk" || "$wl" == "consumer" || "$wl" == "tournament" || \
          "$wl" == "credit" || "$wl" == "hepatitis" ]]; then
    DAT_PATHS+=( "../deepdb_augmented/$wl/" )
  else
    DAT_PATHS+=( "../queryPlans/$wl/${DB_ENGINE}/" )
  fi
done

# one test path
if [[ "$WORKLOAD_TEST" == "syn" || "$WORKLOAD_TEST" == "job" || "$WORKLOAD_TEST" == "job_full" || "$WORKLOAD_TEST" == "jobm" ]]; then
  DAT_PATH_TEST="../queryPlans/imdb/${DB_ENGINE}/"
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
  DAT_PATH_TEST="../queryPlans/$WORKLOAD_TEST/${DB_ENGINE}/"
fi

TRAIN_WLS_HYPHEN="${TRAIN_WLS[0]}"
for elt in "${TRAIN_WLS[@]:1}"; do
  TRAIN_WLS_HYPHEN+="-$elt"
done

# Canonical training workload for shared model files.
# IMDB-based workloads (syn, job_full, jobm) map to 'job' so finetuned models are shared.
_canonical_wl() {
  case "$1" in
    syn|job_full|jobm) echo "job" ;;
    *) echo "$1" ;;
  esac
}
declare -A _seen_canonical=()
CANONICAL_TRAIN_HYPHEN=""
_n_canonical=0
for wl in "${TRAIN_WLS[@]}"; do
  cwl=$(_canonical_wl "$wl")
  if [[ -z "${_seen_canonical[$cwl]+x}" ]]; then
    _seen_canonical[$cwl]=1
    _n_canonical=$((_n_canonical + 1))
    if [[ -n "$CANONICAL_TRAIN_HYPHEN" ]]; then
      CANONICAL_TRAIN_HYPHEN+="-$cwl"
    else
      CANONICAL_TRAIN_HYPHEN="$cwl"
    fi
  fi
done
# Truncate long workload strings to match Python's utilsTrain.py (md5 hash)
if [[ ${#CANONICAL_TRAIN_HYPHEN} -gt 80 ]]; then
  _wl_hash=$(echo -n "$CANONICAL_TRAIN_HYPHEN" | md5sum | cut -c1-8)
  _test_tag=""
  if [[ -n "$WORKLOAD_TEST" ]]; then
    _test_tag="_test-${WORKLOAD_TEST}"
  fi
  CANONICAL_TRAIN_HYPHEN="${_n_canonical}dbs_${_wl_hash}${_test_tag}"
fi

llm_pretrained_task=time
FT_BATCH_SIZE=${FT_BATCH_SIZE:-16}
FT_NUM_EPOCH=${FT_NUM_EPOCH:-$FT_BATCH_SIZE}

# PRICE_M (extended filter encoding) — set once, used by all sections
PRICE_M_ARG=""
PRICE_M_SUFFIX=""
if [[ "$PRICE_M" == "true" || "$PRICE_M" == "True" ]]; then
  PRICE_M_ARG="--price_m"
  PRICE_M_SUFFIX="_priceM"
fi

# PRICE_S (bounding-box range encoding) — set once, used by all sections
PRICE_S_ARG=""
PRICE_S_SUFFIX=""
if [[ "$PRICE_S" == "true" || "$PRICE_S" == "True" ]]; then
  PRICE_S_ARG="--price_s"
  PRICE_S_SUFFIX="_priceS"
fi

# PRICE random init — set once, used by all PRICE finetuning sections
PRICE_RANDOM_INIT_FLAG=""
PRICE_LR_DEFAULT=0.0000285
PRICE_RAND_INIT_SUFFIX=""
if [[ "${PRICE_RANDOM_INIT:-}" == "true" ]]; then
  PRICE_RANDOM_INIT_FLAG="--price_random_init"
  PRICE_LR_DEFAULT=0.001
  PRICE_RAND_INIT_SUFFIX="_randInit"
fi

# PRICE n_layers — set once, used by all PRICE sections
PRICE_N_LAYERS_ARG=""
PRICE_N_LAYERS_SUFFIX=""
if [[ -n "${PRICE_N_LAYERS:-}" ]] && [[ "$PRICE_N_LAYERS" -ne 6 ]]; then
  PRICE_N_LAYERS_ARG="--price_n_layers $PRICE_N_LAYERS"
  PRICE_N_LAYERS_SUFFIX="_pL${PRICE_N_LAYERS}"
fi

# Cross-attention — set once, used by CrossAttentionJoint section
CROSS_ATTN_ARG=""
CROSS_ATTN_SUFFIX=""
N_CROSS_LAYERS_ARG=""
N_CROSS_LAYERS_SUFFIX=""
if [[ "${USE_CROSS_ATTENTION:-}" == "true" ]] || [[ "$finetune" == "CrossAttentionJoint" ]]; then
  CROSS_ATTN_ARG="--use_cross_attention"
  CROSS_ATTN_SUFFIX="_crossAttn"
fi
# Bidirectional cross-attention — set once, used by BiCrossAttentionJoint section
BI_CROSS_ATTN_ARG=""
BI_CROSS_ATTN_SUFFIX=""
if [[ "$finetune" == "BiCrossAttentionJoint" ]]; then
  BI_CROSS_ATTN_ARG="--use_bi_cross_attention"
  BI_CROSS_ATTN_SUFFIX="_biCrossAttn"
fi
if [[ -n "${N_CROSS_LAYERS:-}" ]] && [[ "$N_CROSS_LAYERS" -ne 2 ]]; then
  N_CROSS_LAYERS_ARG="--n_cross_layers $N_CROSS_LAYERS"
  N_CROSS_LAYERS_SUFFIX="_cx${N_CROSS_LAYERS}"
fi
CROSS_ATTN_LR_ARG=""
if [[ -n "${CROSS_ATTN_LR:-}" ]]; then
  CROSS_ATTN_LR_ARG="--cross_attn_lr $CROSS_ATTN_LR"
fi

# Retrain MLP passthrough
RETRAIN_MLP_FLAG=""
RETRAIN_MLP_SUFFIX=""
if [[ "${RETRAIN_MLP:-}" == "true" ]]; then
  RETRAIN_MLP_FLAG="--retrain_mlp"
  RETRAIN_MLP_SUFFIX="_retrainMLP"
fi

# Refined pool passthrough
REFINED_POOL_FLAG=""
REFINED_POOL_SUFFIX=""
if [[ "${REFINED_POOL:-}" == "true" ]]; then
  REFINED_POOL_FLAG="--refined_pool"
  REFINED_POOL_SUFFIX="_refinedPool"
fi

TRIPLE_CONCAT_FLAG=""
TRIPLE_CONCAT_SUFFIX=""
if [[ "${TRIPLE_CONCAT:-}" == "true" ]]; then
  TRIPLE_CONCAT_FLAG="--triple_concat"
  TRIPLE_CONCAT_SUFFIX="_tripleConcat"
fi

EARLY_STOP_ARG=""
if [[ -n "${EARLY_STOP_PATIENCE:-}" ]] && [[ "$EARLY_STOP_PATIENCE" -gt 0 ]]; then
  EARLY_STOP_ARG="--early_stop_patience $EARLY_STOP_PATIENCE"
  if [[ -n "${EARLY_STOP_AFTER_EPOCH:-}" ]] && [[ "$EARLY_STOP_AFTER_EPOCH" -gt 0 ]]; then
    EARLY_STOP_ARG="$EARLY_STOP_ARG --early_stop_after_epoch $EARLY_STOP_AFTER_EPOCH"
  fi
fi

# Epoch suffix for finetuned weight files
EPOCH_SUFFIX="_e${FT_NUM_EPOCH}"

# Checkpoint interval passthrough
CHECKPOINT_INTERVAL_ARG=""
if [[ -n "${CHECKPOINT_INTERVAL:-}" ]] && [[ "$CHECKPOINT_INTERVAL" -gt 0 ]]; then
  CHECKPOINT_INTERVAL_ARG="--checkpoint_interval $CHECKPOINT_INTERVAL"
fi

# Max queries passthrough (limits data before embedding generation)
MAX_QUERIES_ARG=""
MAX_QUERIES_SUFFIX=""
if [[ -n "${MAX_QUERIES:-}" ]] && [[ "$MAX_QUERIES" -gt 0 ]]; then
  MAX_QUERIES_ARG="--max_queries $MAX_QUERIES"
  MAX_QUERIES_SUFFIX="_maxq-${MAX_QUERIES}"
fi

# Helper function to set up all arguments and suffixes
setup_args_and_suffixes() {
  # Initialize all variables
  BUCKETIZE_ARG=""
  BUCKETIZE_SUFFIX=""
  QUANTIFICATION_ARG=""
  QUANTIFICATION_SUFFIX=""
  EMBEDDINGS_ARG=""
  VERBOSE_ARG=""
  DOWNSTREAM_ARG=""
  DOWNSTREAM_SUFFIX=""
  REMOVED_FIELDS_ARG=""
  REMOVED_FIELDS_SUFFIX=""
  STATS_ARGS=""
  STATS_SUFFIX=""
  
  # Bucketize
  if [[ "$BUCKETIZE_INPUT" != "None" && "$BUCKETIZE_INPUT" != "" ]]; then
    BUCKETIZE_ARG="--bucketize_input $BUCKETIZE_INPUT"
    BUCKETIZE_SUFFIX="_bucketize-${BUCKETIZE_INPUT}"
  fi
  
  # Quantification
  if [[ "$QUANTIFICATION" != "None" && "$QUANTIFICATION" != "" ]]; then
    QUANTIFICATION_ARG="--quantification $QUANTIFICATION"
    QUANTIFICATION_SUFFIX="_quant-${QUANTIFICATION}"
  fi
  
  # Embeddings exist
  if [[ "$EMBEDDINGS_EXIST" == "True" || "$EMBEDDINGS_EXIST" == "true" ]]; then
    EMBEDDINGS_ARG="--embeddings_exist"
  fi
  
  # Verbose info
  if [[ "$VERBOSE_INFO" == "true" || "$VERBOSE_INFO" == "True" ]]; then
    VERBOSE_ARG="--verbose_info"
  fi
  
  # Downstream learner
  if [[ -n "$LLM_DOWNSTREAM" && "$LLM_DOWNSTREAM" != "" ]]; then
    DOWNSTREAM_ARG="--llm_downstream $LLM_DOWNSTREAM"
    if [[ "$LLM_DOWNSTREAM" != "mlp" ]]; then
      DOWNSTREAM_SUFFIX="_downstream-${LLM_DOWNSTREAM}"
    fi
  fi
  
  # Removed fields
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

  # queries_true embeddings concatenation
  if [[ "$CONCAT_TRUE_EMBEDDINGS" == "true" || "$CONCAT_TRUE_EMBEDDINGS" == "True" ]]; then
    CONCAT_TRUE_ARG="--concat_true_embeddings"
    CONCAT_TRUE_SUFFIX="_trueEmb"
    if [[ -n "$QUERIES_TRUE_DIR" ]]; then
      CONCAT_TRUE_ARG="$CONCAT_TRUE_ARG --queries_true_dir $QUERIES_TRUE_DIR"
    fi
  else
    CONCAT_TRUE_ARG=""
    CONCAT_TRUE_SUFFIX=""
  fi

  # Stats token injection
  if [[ "$STATS_TOKEN_INJECT" == "true" || "$STATS_TOKEN_INJECT" == "True" ]]; then
    STATS_ARGS="--stats_token_inject"
    STATS_SUFFIX="_statTok"
    if [[ -n "$STATS_TOKEN_MODE" ]]; then
      STATS_ARGS="$STATS_ARGS --stats_token_mode $STATS_TOKEN_MODE"
      STATS_SUFFIX="${STATS_SUFFIX}-${STATS_TOKEN_MODE}"
    fi
    if [[ -n "$STATS_TOKEN_STR" ]]; then
      STATS_ARGS="$STATS_ARGS --stats_token_str $STATS_TOKEN_STR"
    fi
    if [[ -n "$STATS_TOKEN_DIM" ]]; then
      STATS_ARGS="$STATS_ARGS --stats_token_dim $STATS_TOKEN_DIM"
    fi
    if [[ -n "$STATS_PG_STATS_PATH" ]]; then
      STATS_ARGS="$STATS_ARGS --stats_pg_stats_path $STATS_PG_STATS_PATH"
    fi
    if [[ -n "$STATS_TABLE_SIZES_PATH" ]]; then
      STATS_ARGS="$STATS_ARGS --stats_table_sizes_path $STATS_TABLE_SIZES_PATH"
    fi
  fi
  
  # Determine directory names based on whether _rm- is in the filename
  RESULTS_DIR="results/${DB_ENGINE}"
  LOGS_DIR="logs/${DB_ENGINE}"
  if [[ "$REMOVED_FIELDS_SUFFIX" == *_rm-* ]]; then
    RESULTS_DIR="results_rm/${DB_ENGINE}"
    LOGS_DIR="logs_rm/${DB_ENGINE}"
  fi
}

if [ "$finetune" == "False" ]; then
  #########################inference: no pre-train#########################
  algo=llm
  embed_size=${EMBED_SIZE:-1000}
  hid_units=2048
  lr=0.0001
  batch_size=64     

  echo "inference: no pre-train"
  
  setup_args_and_suffixes
  
  python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                      --output_dir_qerror ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-None_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${DOWNSTREAM_SUFFIX}${REMOVED_FIELDS_SUFFIX}${CONCAT_TRUE_SUFFIX}${STATS_SUFFIX}${MAX_QUERIES_SUFFIX}_seed${SEED}.csv \
                                      --output_dir_abs ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-None_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${DOWNSTREAM_SUFFIX}${REMOVED_FIELDS_SUFFIX}${CONCAT_TRUE_SUFFIX}${STATS_SUFFIX}${MAX_QUERIES_SUFFIX}_seed${SEED}_abs.txt \
                                      --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-None_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${DOWNSTREAM_SUFFIX}${REMOVED_FIELDS_SUFFIX}${CONCAT_TRUE_SUFFIX}${STATS_SUFFIX}${MAX_QUERIES_SUFFIX}_seed${SEED}.log \
                                      --db $DB_ENGINE \
                                      --workloads_train "${TRAIN_WLS[@]}" \
                                      --workload_test ${WORKLOAD_TEST} \
                                      --algo ${algo} \
                                      --learning_rate $lr \
                                      --batch_size $batch_size \
                                      --hid_units $hid_units \
                                      --model_name $model_name \
                                      --embed_size $embed_size \
                                      --train_ratio $train_ratio \
                                      --llm_mode inference \
                                      --seed $SEED \
                                      $BUCKETIZE_ARG \
                                      $QUANTIFICATION_ARG \
                                      $EMBEDDINGS_ARG \
                                      $VERBOSE_ARG \
                                      $DOWNSTREAM_ARG \
                                      $REMOVED_FIELDS_ARG \
                                      $CONCAT_TRUE_ARG \
                                      $STATS_ARGS \
                                      $PRICE_M_ARG $PRICE_S_ARG \
                                      $MAX_QUERIES_ARG
fi

if [ "$finetune" == "True" ]; then
  #########################finetune#########################
  algo=llm_finetune
  hid_units=2048
  lr=0.0001
  batch_size=$FT_BATCH_SIZE

  # Check which finetuning modes to run (default to both if not set)
  RUN_LAST=${FINETUNE_RUN_LAST:-true}
  RUN_LORA=${FINETUNE_RUN_LORA:-true}
  
  # Helper function to check if finetuned model exists
  check_model_exists() {
    local mode=$1
    local stats_suffix=""
    if [[ "$STATS_TOKEN_INJECT" == "true" || "$STATS_TOKEN_INJECT" == "True" ]]; then
      stats_suffix="_statTok"
      if [[ -n "$STATS_TOKEN_MODE" ]]; then
        stats_suffix="${stats_suffix}-${STATS_TOKEN_MODE}"
      fi
    fi
    local model_file="finetuned_models/${DB_ENGINE}/${CANONICAL_TRAIN_HYPHEN}_time_${mode}_${model_name1}_b${FT_BATCH_SIZE}${stats_suffix}_llm.pt"
    if [ -f "$model_file" ]; then
      echo "✅  Finetuned model already exists: $model_file"
      echo "    Skipping finetuning step for mode: $mode"
      return 0  # Model exists
    else
      return 1  # Model does not exist
    fi
  }

  if [[ "$RUN_LAST" == "true" ]]; then
    llm_mode=last
    echo "finetune: last"
    
    # Check if model already exists
    if check_model_exists "last"; then
      echo "    Continuing to inference step..."
    else
      echo "    Model not found, starting finetuning..."
      setup_args_and_suffixes
      
      python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                          --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_last_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${CONCAT_TRUE_SUFFIX}${STATS_SUFFIX}.log \
                                          --db $DB_ENGINE \
                                          --workloads_train "${TRAIN_WLS[@]}" \
                                          --workload_test ${WORKLOAD_TEST} \
                                          --algo ${algo} \
                                          --learning_rate $lr \
                                          --batch_size $batch_size \
                                          --hid_units $hid_units \
                                          --model_name $model_name \
                                          --train_ratio $train_ratio \
                                          --llm_mode $llm_mode \
                                          --num_epoch $FT_NUM_EPOCH \
                                          --seed $SEED \
                                          $BUCKETIZE_ARG \
                                          $QUANTIFICATION_ARG \
                                          $REMOVED_FIELDS_ARG \
                                          $CONCAT_TRUE_ARG \
                                          $STATS_ARGS \
                                          $PRICE_M_ARG $PRICE_S_ARG \
                                          $MAX_QUERIES_ARG
    fi
  fi

  if [[ "$RUN_LORA" == "true" ]]; then
    llm_mode=lora
    echo "finetune: lora"
    
    # Check if model already exists
    if check_model_exists "lora"; then
      echo "    Continuing to inference step..."
    else
      echo "    Model not found, starting finetuning..."
      setup_args_and_suffixes
      
      python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                          --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_lora_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${CONCAT_TRUE_SUFFIX}${STATS_SUFFIX}.log \
                                          --db $DB_ENGINE \
                                          --workloads_train "${TRAIN_WLS[@]}" \
                                          --workload_test ${WORKLOAD_TEST} \
                                          --algo ${algo} \
                                          --learning_rate $lr \
                                          --batch_size $batch_size \
                                          --hid_units $hid_units \
                                          --model_name $model_name \
                                          --train_ratio $train_ratio \
                                          --llm_mode $llm_mode \
                                          --num_epoch $FT_NUM_EPOCH \
                                          --seed $SEED \
                                          $BUCKETIZE_ARG \
                                          $QUANTIFICATION_ARG \
                                          $REMOVED_FIELDS_ARG \
                                          $CONCAT_TRUE_ARG \
                                          $STATS_ARGS \
                                          $PRICE_M_ARG $PRICE_S_ARG \
                                          $MAX_QUERIES_ARG
    fi
  fi

  #########################inference: pre-trained#########################
  algo=llm
  embed_size=${EMBED_SIZE:-1000}
  hid_units=2048
  lr=0.0001
  batch_size=64     

  if [[ "$RUN_LAST" == "true" ]]; then
    llm_pretrained=last
    echo "inference: pre-trained last"
    
    setup_args_and_suffixes
    
    python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                        --output_dir_qerror ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-${llm_pretrained}_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${DOWNSTREAM_SUFFIX}${REMOVED_FIELDS_SUFFIX}${CONCAT_TRUE_SUFFIX}${STATS_SUFFIX}_ftb${FT_BATCH_SIZE}_seed${SEED}.csv \
                                        --output_dir_abs ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-${llm_pretrained}_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${DOWNSTREAM_SUFFIX}${REMOVED_FIELDS_SUFFIX}${CONCAT_TRUE_SUFFIX}${STATS_SUFFIX}_ftb${FT_BATCH_SIZE}_seed${SEED}_abs.txt \
                                        --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-${llm_pretrained}_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${DOWNSTREAM_SUFFIX}${REMOVED_FIELDS_SUFFIX}${CONCAT_TRUE_SUFFIX}${STATS_SUFFIX}_ftb${FT_BATCH_SIZE}_seed${SEED}.log \
                                        --db $DB_ENGINE \
                                        --workloads_train "${TRAIN_WLS[@]}" \
                                        --workload_test ${WORKLOAD_TEST} \
                                        --algo ${algo} \
                                        --learning_rate $lr \
                                        --batch_size $batch_size \
                                        --hid_units $hid_units \
                                        --model_name $model_name \
                                        --embed_size $embed_size \
                                        --train_ratio 1.0 \
                                        --llm_mode inference \
                                        --num_epoch 100 \
                                        --llm_pretrained $llm_pretrained \
                                        --llm_pretrained_task $llm_pretrained_task \
                                        --seed $SEED \
                                        --ft_batch_size $FT_BATCH_SIZE \
                                        $BUCKETIZE_ARG \
                                        $QUANTIFICATION_ARG \
                                        $EMBEDDINGS_ARG \
                                        $VERBOSE_ARG \
                                        $DOWNSTREAM_ARG \
                                        $REMOVED_FIELDS_ARG \
                                        $CONCAT_TRUE_ARG \
                                        $STATS_ARGS \
                                        $PRICE_M_ARG $PRICE_S_ARG
  fi

  if [[ "$RUN_LORA" == "true" ]]; then
    llm_pretrained=lora
    echo "inference: pre-trained lora"

    setup_args_and_suffixes

    python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                        --output_dir_qerror ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-${llm_pretrained}_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${DOWNSTREAM_SUFFIX}${REMOVED_FIELDS_SUFFIX}${CONCAT_TRUE_SUFFIX}${STATS_SUFFIX}_ftb${FT_BATCH_SIZE}_seed${SEED}.csv \
                                        --output_dir_abs ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-${llm_pretrained}_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${DOWNSTREAM_SUFFIX}${REMOVED_FIELDS_SUFFIX}${CONCAT_TRUE_SUFFIX}${STATS_SUFFIX}_ftb${FT_BATCH_SIZE}_seed${SEED}_abs.txt \
                                        --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-${llm_pretrained}_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${DOWNSTREAM_SUFFIX}${REMOVED_FIELDS_SUFFIX}${CONCAT_TRUE_SUFFIX}${STATS_SUFFIX}_ftb${FT_BATCH_SIZE}_seed${SEED}.log \
                                        --db $DB_ENGINE \
                                        --workloads_train "${TRAIN_WLS[@]}" \
                                        --workload_test ${WORKLOAD_TEST} \
                                        --algo ${algo} \
                                        --learning_rate $lr \
                                        --batch_size $batch_size \
                                        --hid_units $hid_units \
                                        --model_name $model_name \
                                        --embed_size $embed_size \
                                        --train_ratio 1.0 \
                                        --llm_mode inference \
                                        --num_epoch 100 \
                                        --llm_pretrained $llm_pretrained \
                                        --llm_pretrained_task $llm_pretrained_task \
                                        --seed $SEED \
                                        --ft_batch_size $FT_BATCH_SIZE \
                                        $BUCKETIZE_ARG \
                                        $QUANTIFICATION_ARG \
                                        $EMBEDDINGS_ARG \
                                        $VERBOSE_ARG \
                                        $DOWNSTREAM_ARG \
                                        $REMOVED_FIELDS_ARG \
                                        $CONCAT_TRUE_ARG \
                                        $STATS_ARGS \
                                        $PRICE_M_ARG $PRICE_S_ARG
  fi
fi

if [ "$finetune" == "JointPrice" ]; then
  PRICE_MODEL_PATH=${PRICE_MODEL_PATH:-"/root/PRICE/results/model_params.pth"}
  PRICE_BIN_SIZE=${PRICE_BIN_SIZE:-40}

  # Check if finetuned JointPrice weights already exist
  JOINT_PRICE_PREFIX="finetuned_models/${DB_ENGINE}/${CANONICAL_TRAIN_HYPHEN}_time_lora_${model_name1}_b${FT_BATCH_SIZE}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}_llm_price${PRICE_RAND_INIT_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${EPOCH_SUFFIX}"
  if [ -f "${JOINT_PRICE_PREFIX}_llm.pt" ] && [ -f "${JOINT_PRICE_PREFIX}_price.pt" ]; then
    echo "Finetuned JointPrice weights already exist, skipping finetune:"
    echo "  LLM:   ${JOINT_PRICE_PREFIX}_llm.pt"
    echo "  PRICE: ${JOINT_PRICE_PREFIX}_price.pt"
  else
    #########################Joint LLM+PRICE finetune#########################
    algo=llm_price_finetune
    hid_units=2048
    lr=0.0001
    price_lr=${PRICE_LR:-$PRICE_LR_DEFAULT}
    batch_size=$FT_BATCH_SIZE
    grad_accum_steps=${GRAD_ACCUM_STEPS:-1}

    echo "Joint LLM+PRICE finetune"

    # Build grad_accum arg
    GRAD_ACCUM_ARG=""
    if [[ "$grad_accum_steps" -gt 1 ]]; then
      GRAD_ACCUM_ARG="--grad_accum_steps $grad_accum_steps"
      echo "  Gradient accumulation: ${grad_accum_steps} steps (effective batch = ${batch_size} * ${grad_accum_steps})"
    fi

    setup_args_and_suffixes

    python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                        --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_lora_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${EPOCH_SUFFIX}.log \
                                        --db $DB_ENGINE \
                                        --workloads_train "${TRAIN_WLS[@]}" \
                                        --workload_test ${WORKLOAD_TEST} \
                                        --algo ${algo} \
                                        --learning_rate $lr \
                                        --price_lr $price_lr \
                                        --batch_size $batch_size \
                                        --hid_units $hid_units \
                                        --model_name $model_name \
                                        --train_ratio $train_ratio \
                                        --llm_mode lora \
                                        --num_epoch $FT_NUM_EPOCH \
                                        --seed $SEED \
                                        --price_model_path $PRICE_MODEL_PATH \
                                        --price_bin_size $PRICE_BIN_SIZE \
                                        $BUCKETIZE_ARG \
                                        $QUANTIFICATION_ARG \
                                        $REMOVED_FIELDS_ARG \
                                        $PRICE_M_ARG $PRICE_S_ARG \
                                        $PRICE_RANDOM_INIT_FLAG \
                                        $CHECKPOINT_INTERVAL_ARG \
                                        $GRAD_ACCUM_ARG \
                                        $PRICE_N_LAYERS_ARG
  fi

  #########################inference: pre-trained JointPrice#########################
  algo=llm_price
  embed_size=${EMBED_SIZE:-1000}
  hid_units=2048
  lr=0.0001
  batch_size=64

  echo "inference: pre-trained JointPrice"

  setup_args_and_suffixes

  python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                      --output_dir_qerror ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-lora_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${PRICE_N_LAYERS_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}_seed${SEED}.csv \
                                      --output_dir_abs ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-lora_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${PRICE_N_LAYERS_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}_seed${SEED}_abs.txt \
                                      --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-lora_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${PRICE_N_LAYERS_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}_seed${SEED}.log \
                                      --db $DB_ENGINE \
                                      --workloads_train "${TRAIN_WLS[@]}" \
                                      --workload_test ${WORKLOAD_TEST} \
                                      --algo ${algo} \
                                      --learning_rate $lr \
                                      --batch_size $batch_size \
                                      --hid_units $hid_units \
                                      --model_name $model_name \
                                      --embed_size $embed_size \
                                      --train_ratio 1.0 \
                                      --llm_mode inference \
                                      --num_epoch 100 \
                                      --llm_pretrained lora \
                                      --llm_pretrained_task $llm_pretrained_task \
                                      --price_model_path $PRICE_MODEL_PATH \
                                      --price_bin_size $PRICE_BIN_SIZE \
                                      --price_pretrained \
                                      --seed $SEED \
                                      --ft_batch_size $FT_BATCH_SIZE \
                                      --ft_num_epoch $FT_NUM_EPOCH \
                                      $BUCKETIZE_ARG \
                                      $QUANTIFICATION_ARG \
                                      $EMBEDDINGS_ARG \
                                      $REMOVED_FIELDS_ARG \
                                      $PRICE_M_ARG $PRICE_S_ARG \
                                      $PRICE_RANDOM_INIT_FLAG \
                                      $PRICE_N_LAYERS_ARG
fi

if [ "$finetune" == "PriceNoFT" ]; then
  #########################Case 1: LLM+PRICE, no finetune#########################
  PRICE_MODEL_PATH=${PRICE_MODEL_PATH:-"/root/PRICE/results/model_params.pth"}
  PRICE_BIN_SIZE=${PRICE_BIN_SIZE:-40}

  algo=llm_price
  embed_size=${EMBED_SIZE:-1000}
  hid_units=2048
  lr=0.0001
  batch_size=64

  echo "LLM+PRICE inference: no finetune (PriceNoFT)"

  setup_args_and_suffixes

  python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                      --output_dir_qerror ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-None_priceNoFT_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_N_LAYERS_SUFFIX}_seed${SEED}.csv \
                                      --output_dir_abs ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-None_priceNoFT_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_N_LAYERS_SUFFIX}_seed${SEED}_abs.txt \
                                      --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-None_priceNoFT_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_N_LAYERS_SUFFIX}_seed${SEED}.log \
                                      --db $DB_ENGINE \
                                      --workloads_train "${TRAIN_WLS[@]}" \
                                      --workload_test ${WORKLOAD_TEST} \
                                      --algo ${algo} \
                                      --learning_rate $lr \
                                      --batch_size $batch_size \
                                      --hid_units $hid_units \
                                      --model_name $model_name \
                                      --embed_size $embed_size \
                                      --train_ratio $train_ratio \
                                      --llm_mode inference \
                                      --num_epoch 100 \
                                      --price_model_path $PRICE_MODEL_PATH \
                                      --price_bin_size $PRICE_BIN_SIZE \
                                      --price_weights_source pretrained \
                                      --seed $SEED \
                                      $BUCKETIZE_ARG \
                                      $QUANTIFICATION_ARG \
                                      $EMBEDDINGS_ARG \
                                      $REMOVED_FIELDS_ARG \
                                      $PRICE_M_ARG $PRICE_S_ARG \
                                      $PRICE_N_LAYERS_ARG
fi

if [ "$finetune" == "PriceLLMOnly" ]; then
  #########################Case 2: LLM finetuned, PRICE frozen#########################
  PRICE_MODEL_PATH=${PRICE_MODEL_PATH:-"/root/PRICE/results/model_params.pth"}
  PRICE_BIN_SIZE=${PRICE_BIN_SIZE:-40}

  # Step 1: Finetune LLM (reuse existing llm_finetune logic)
  algo=llm_finetune
  hid_units=2048
  lr=0.0001
  batch_size=$FT_BATCH_SIZE

  check_model_exists_llm() {
    local mode=$1
    local model_file="finetuned_models/${DB_ENGINE}/${CANONICAL_TRAIN_HYPHEN}_time_${mode}_${model_name1}_b${FT_BATCH_SIZE}_llm.pt"
    if [ -f "$model_file" ]; then
      echo "Finetuned LLM model already exists: $model_file"
      return 0
    else
      return 1
    fi
  }

  llm_mode=lora
  echo "PriceLLMOnly: finetune LLM (lora)"

  if check_model_exists_llm "lora"; then
    echo "    Continuing to inference step..."
  else
    setup_args_and_suffixes

    python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                        --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_lora_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}.log \
                                        --db $DB_ENGINE \
                                        --workloads_train "${TRAIN_WLS[@]}" \
                                        --workload_test ${WORKLOAD_TEST} \
                                        --algo ${algo} \
                                        --learning_rate $lr \
                                        --batch_size $batch_size \
                                        --hid_units $hid_units \
                                        --model_name $model_name \
                                        --train_ratio $train_ratio \
                                        --llm_mode $llm_mode \
                                        --num_epoch $FT_NUM_EPOCH \
                                        --seed $SEED \
                                        $BUCKETIZE_ARG \
                                        $QUANTIFICATION_ARG \
                                        $REMOVED_FIELDS_ARG \
                                        $PRICE_M_ARG $PRICE_S_ARG
  fi

  # Step 2: Inference with finetuned LLM + pretrained PRICE
  algo=llm_price
  embed_size=${EMBED_SIZE:-1000}
  hid_units=2048
  lr=0.0001
  batch_size=64

  echo "PriceLLMOnly: inference with finetuned LLM + pretrained PRICE"

  setup_args_and_suffixes

  python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                      --output_dir_qerror ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-lora_priceLLMOnly_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_N_LAYERS_SUFFIX}_ftb${FT_BATCH_SIZE}_seed${SEED}.csv \
                                      --output_dir_abs ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-lora_priceLLMOnly_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_N_LAYERS_SUFFIX}_ftb${FT_BATCH_SIZE}_seed${SEED}_abs.txt \
                                      --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-lora_priceLLMOnly_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_N_LAYERS_SUFFIX}_ftb${FT_BATCH_SIZE}_seed${SEED}.log \
                                      --db $DB_ENGINE \
                                      --workloads_train "${TRAIN_WLS[@]}" \
                                      --workload_test ${WORKLOAD_TEST} \
                                      --algo ${algo} \
                                      --learning_rate $lr \
                                      --batch_size $batch_size \
                                      --hid_units $hid_units \
                                      --model_name $model_name \
                                      --embed_size $embed_size \
                                      --train_ratio 1.0 \
                                      --llm_mode inference \
                                      --num_epoch 100 \
                                      --llm_pretrained lora \
                                      --llm_pretrained_task $llm_pretrained_task \
                                      --price_model_path $PRICE_MODEL_PATH \
                                      --price_bin_size $PRICE_BIN_SIZE \
                                      --price_weights_source pretrained \
                                      --seed $SEED \
                                      --ft_batch_size $FT_BATCH_SIZE \
                                      $BUCKETIZE_ARG \
                                      $QUANTIFICATION_ARG \
                                      $EMBEDDINGS_ARG \
                                      $REMOVED_FIELDS_ARG \
                                      $PRICE_M_ARG $PRICE_S_ARG \
                                      $PRICE_N_LAYERS_ARG
fi

if [ "$finetune" == "PricePRICEOnly" ]; then
  #########################Case 3: LLM frozen, PRICE finetuned on card#########################
  PRICE_MODEL_PATH=${PRICE_MODEL_PATH:-"/root/PRICE/results/model_params.pth"}
  PRICE_BIN_SIZE=${PRICE_BIN_SIZE:-40}

  # Step 1: Finetune PRICE on cardinality
  PRICE_SEPARATE_FILE="finetuned_models/${DB_ENGINE}/${CANONICAL_TRAIN_HYPHEN}_card_b${FT_BATCH_SIZE}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${EPOCH_SUFFIX}_price_separate.pt"
  if [ -f "$PRICE_SEPARATE_FILE" ]; then
    echo "Separately finetuned PRICE weights already exist: $PRICE_SEPARATE_FILE"
  else
    algo=price_finetune
    price_lr=${PRICE_LR:-$PRICE_LR_DEFAULT}
    batch_size=$FT_BATCH_SIZE

    echo "PricePRICEOnly: finetune PRICE on cardinality"

    setup_args_and_suffixes

    python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                        --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_${DB_ENGINE}_${price_lr}_b${batch_size}_${model_name1}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${EPOCH_SUFFIX}.log \
                                        --db $DB_ENGINE \
                                        --workloads_train "${TRAIN_WLS[@]}" \
                                        --workload_test ${WORKLOAD_TEST} \
                                        --algo ${algo} \
                                        --price_lr $price_lr \
                                        --batch_size $batch_size \
                                        --model_name $model_name \
                                        --train_ratio $train_ratio \
                                        --num_epoch $FT_NUM_EPOCH \
                                        --card \
                                        --seed $SEED \
                                        --price_model_path $PRICE_MODEL_PATH \
                                        --price_bin_size $PRICE_BIN_SIZE \
                                        $REMOVED_FIELDS_ARG \
                                        $PRICE_M_ARG $PRICE_S_ARG \
                                        $PRICE_RANDOM_INIT_FLAG \
                                        $CHECKPOINT_INTERVAL_ARG
  fi

  # Step 2: Inference with frozen LLM + finetuned PRICE
  algo=llm_price
  embed_size=${EMBED_SIZE:-1000}
  hid_units=2048
  lr=0.0001
  batch_size=64

  echo "PricePRICEOnly: inference with frozen LLM + finetuned PRICE"

  setup_args_and_suffixes

  python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                      --output_dir_qerror ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-None_pricePRICEOnly_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_RAND_INIT_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}_seed${SEED}.csv \
                                      --output_dir_abs ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-None_pricePRICEOnly_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_RAND_INIT_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}_seed${SEED}_abs.txt \
                                      --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-None_pricePRICEOnly_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_RAND_INIT_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}_seed${SEED}.log \
                                      --db $DB_ENGINE \
                                      --workloads_train "${TRAIN_WLS[@]}" \
                                      --workload_test ${WORKLOAD_TEST} \
                                      --algo ${algo} \
                                      --learning_rate $lr \
                                      --batch_size $batch_size \
                                      --hid_units $hid_units \
                                      --model_name $model_name \
                                      --embed_size $embed_size \
                                      --train_ratio $train_ratio \
                                      --llm_mode inference \
                                      --num_epoch 100 \
                                      --price_model_path $PRICE_MODEL_PATH \
                                      --price_bin_size $PRICE_BIN_SIZE \
                                      --price_weights_source separate \
                                      --seed $SEED \
                                      --ft_batch_size $FT_BATCH_SIZE \
                                      --ft_num_epoch $FT_NUM_EPOCH \
                                      $BUCKETIZE_ARG \
                                      $QUANTIFICATION_ARG \
                                      $EMBEDDINGS_ARG \
                                      $REMOVED_FIELDS_ARG \
                                      $PRICE_M_ARG $PRICE_S_ARG \
                                      $PRICE_RANDOM_INIT_FLAG
fi

if [ "$finetune" == "PriceBothSep" ]; then
  #########################Case 4: Both finetuned separately#########################
  PRICE_MODEL_PATH=${PRICE_MODEL_PATH:-"/root/PRICE/results/model_params.pth"}
  PRICE_BIN_SIZE=${PRICE_BIN_SIZE:-40}

  # Step 1: Finetune LLM
  algo=llm_finetune
  hid_units=2048
  lr=0.0001
  batch_size=$FT_BATCH_SIZE

  check_model_exists_llm() {
    local mode=$1
    local model_file="finetuned_models/${DB_ENGINE}/${CANONICAL_TRAIN_HYPHEN}_time_${mode}_${model_name1}_b${FT_BATCH_SIZE}_llm.pt"
    if [ -f "$model_file" ]; then
      echo "Finetuned LLM model already exists: $model_file"
      return 0
    else
      return 1
    fi
  }

  llm_mode=lora
  echo "PriceBothSep: finetune LLM (lora)"

  if check_model_exists_llm "lora"; then
    echo "    Continuing to next step..."
  else
    setup_args_and_suffixes

    python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                        --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_lora_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}.log \
                                        --db $DB_ENGINE \
                                        --workloads_train "${TRAIN_WLS[@]}" \
                                        --workload_test ${WORKLOAD_TEST} \
                                        --algo ${algo} \
                                        --learning_rate $lr \
                                        --batch_size $batch_size \
                                        --hid_units $hid_units \
                                        --model_name $model_name \
                                        --train_ratio $train_ratio \
                                        --llm_mode $llm_mode \
                                        --num_epoch $FT_NUM_EPOCH \
                                        --seed $SEED \
                                        $BUCKETIZE_ARG \
                                        $QUANTIFICATION_ARG \
                                        $REMOVED_FIELDS_ARG \
                                        $PRICE_M_ARG $PRICE_S_ARG
  fi

  # Step 2: Finetune PRICE on cardinality
  PRICE_SEPARATE_FILE="finetuned_models/${DB_ENGINE}/${CANONICAL_TRAIN_HYPHEN}_card_b${FT_BATCH_SIZE}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${EPOCH_SUFFIX}_price_separate.pt"
  if [ -f "$PRICE_SEPARATE_FILE" ]; then
    echo "Separately finetuned PRICE weights already exist: $PRICE_SEPARATE_FILE"
  else
    algo=price_finetune
    price_lr=${PRICE_LR:-$PRICE_LR_DEFAULT}
    batch_size=$FT_BATCH_SIZE

    echo "PriceBothSep: finetune PRICE on cardinality"

    setup_args_and_suffixes

    python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                        --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_${DB_ENGINE}_${price_lr}_b${batch_size}_${model_name1}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${EPOCH_SUFFIX}.log \
                                        --db $DB_ENGINE \
                                        --workloads_train "${TRAIN_WLS[@]}" \
                                        --workload_test ${WORKLOAD_TEST} \
                                        --algo ${algo} \
                                        --price_lr $price_lr \
                                        --batch_size $batch_size \
                                        --model_name $model_name \
                                        --train_ratio $train_ratio \
                                        --num_epoch $FT_NUM_EPOCH \
                                        --card \
                                        --seed $SEED \
                                        --price_model_path $PRICE_MODEL_PATH \
                                        --price_bin_size $PRICE_BIN_SIZE \
                                        $REMOVED_FIELDS_ARG \
                                        $PRICE_M_ARG $PRICE_S_ARG \
                                        $PRICE_RANDOM_INIT_FLAG \
                                        $CHECKPOINT_INTERVAL_ARG
  fi

  # Step 3: Inference with both finetuned weights
  algo=llm_price
  embed_size=${EMBED_SIZE:-1000}
  hid_units=2048
  lr=0.0001
  batch_size=64

  echo "PriceBothSep: inference with finetuned LLM + finetuned PRICE"

  setup_args_and_suffixes

  python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                      --output_dir_qerror ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-lora_priceBothSep_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_RAND_INIT_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}_seed${SEED}.csv \
                                      --output_dir_abs ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-lora_priceBothSep_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_RAND_INIT_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}_seed${SEED}_abs.txt \
                                      --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-lora_priceBothSep_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_RAND_INIT_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}_seed${SEED}.log \
                                      --db $DB_ENGINE \
                                      --workloads_train "${TRAIN_WLS[@]}" \
                                      --workload_test ${WORKLOAD_TEST} \
                                      --algo ${algo} \
                                      --learning_rate $lr \
                                      --batch_size $batch_size \
                                      --hid_units $hid_units \
                                      --model_name $model_name \
                                      --embed_size $embed_size \
                                      --train_ratio 1.0 \
                                      --llm_mode inference \
                                      --num_epoch 100 \
                                      --llm_pretrained lora \
                                      --llm_pretrained_task $llm_pretrained_task \
                                      --price_model_path $PRICE_MODEL_PATH \
                                      --price_bin_size $PRICE_BIN_SIZE \
                                      --price_weights_source separate \
                                      --seed $SEED \
                                      --ft_batch_size $FT_BATCH_SIZE \
                                      --ft_num_epoch $FT_NUM_EPOCH \
                                      $BUCKETIZE_ARG \
                                      $QUANTIFICATION_ARG \
                                      $EMBEDDINGS_ARG \
                                      $REMOVED_FIELDS_ARG \
                                      $PRICE_M_ARG $PRICE_S_ARG \
                                      $PRICE_RANDOM_INIT_FLAG
fi

if [ "$finetune" == "PriceFTwithLLM" ]; then
  #########################Case 5: PRICE finetuned with frozen LLM embeddings#########################
  PRICE_MODEL_PATH=${PRICE_MODEL_PATH:-"/root/PRICE/results/model_params.pth"}
  PRICE_BIN_SIZE=${PRICE_BIN_SIZE:-40}

  # Step 1: Finetune PRICE+MLP with frozen LLM
  FROZEN_JOINT_FILE="finetuned_models/${DB_ENGINE}/${CANONICAL_TRAIN_HYPHEN}_time_inference_${model_name1}_b${FT_BATCH_SIZE}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}_llm_price${PRICE_RAND_INIT_SUFFIX}${EPOCH_SUFFIX}_price.pt"
  if [ -f "$FROZEN_JOINT_FILE" ]; then
    echo "Frozen-joint finetuned PRICE weights already exist: $FROZEN_JOINT_FILE"
  else
    algo=llm_price_finetune
    hid_units=2048
    lr=0.0001
    price_lr=${PRICE_LR:-$PRICE_LR_DEFAULT}
    batch_size=$FT_BATCH_SIZE

    echo "PriceFTwithLLM: finetune PRICE+MLP with frozen LLM (time)"

    setup_args_and_suffixes

    python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                        --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_frozen_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${EPOCH_SUFFIX}.log \
                                        --db $DB_ENGINE \
                                        --workloads_train "${TRAIN_WLS[@]}" \
                                        --workload_test ${WORKLOAD_TEST} \
                                        --algo ${algo} \
                                        --learning_rate $lr \
                                        --price_lr $price_lr \
                                        --batch_size $batch_size \
                                        --hid_units $hid_units \
                                        --model_name $model_name \
                                        --train_ratio $train_ratio \
                                        --llm_mode inference \
                                        --freeze_llm \
                                        --num_epoch $FT_NUM_EPOCH \
                                        --seed $SEED \
                                        --price_model_path $PRICE_MODEL_PATH \
                                        --price_bin_size $PRICE_BIN_SIZE \
                                        $BUCKETIZE_ARG \
                                        $QUANTIFICATION_ARG \
                                        $REMOVED_FIELDS_ARG \
                                        $PRICE_M_ARG $PRICE_S_ARG \
                                        $PRICE_RANDOM_INIT_FLAG \
                                        $CHECKPOINT_INTERVAL_ARG
  fi

  # Step 2: Inference with frozen LLM + frozen-joint finetuned PRICE
  algo=llm_price
  embed_size=${EMBED_SIZE:-1000}
  hid_units=2048
  lr=0.0001
  batch_size=64

  echo "PriceFTwithLLM: inference with frozen LLM + frozen-joint finetuned PRICE (time)"

  setup_args_and_suffixes

  python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                      --output_dir_qerror ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-None_priceFTwithLLM_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_RAND_INIT_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}_seed${SEED}.csv \
                                      --output_dir_abs ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-None_priceFTwithLLM_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_RAND_INIT_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}_seed${SEED}_abs.txt \
                                      --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-None_priceFTwithLLM_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_RAND_INIT_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}_seed${SEED}.log \
                                      --db $DB_ENGINE \
                                      --workloads_train "${TRAIN_WLS[@]}" \
                                      --workload_test ${WORKLOAD_TEST} \
                                      --algo ${algo} \
                                      --learning_rate $lr \
                                      --batch_size $batch_size \
                                      --hid_units $hid_units \
                                      --model_name $model_name \
                                      --embed_size $embed_size \
                                      --train_ratio $train_ratio \
                                      --llm_mode inference \
                                      --num_epoch 100 \
                                      --price_model_path $PRICE_MODEL_PATH \
                                      --price_bin_size $PRICE_BIN_SIZE \
                                      --price_weights_source frozen_joint \
                                      --seed $SEED \
                                      --ft_batch_size $FT_BATCH_SIZE \
                                      --ft_num_epoch $FT_NUM_EPOCH \
                                      $BUCKETIZE_ARG \
                                      $QUANTIFICATION_ARG \
                                      $EMBEDDINGS_ARG \
                                      $REMOVED_FIELDS_ARG \
                                      $PRICE_M_ARG $PRICE_S_ARG \
                                      $PRICE_RANDOM_INIT_FLAG
fi

if [ "$finetune" == "GatedJointPrice" ]; then
  PRICE_MODEL_PATH=${PRICE_MODEL_PATH:-"/root/PRICE/results/model_params.pth"}
  PRICE_BIN_SIZE=${PRICE_BIN_SIZE:-40}

  # Check if finetuned GatedJointPrice weights already exist
  GATED_JOINT_PREFIX="finetuned_models/${DB_ENGINE}/${CANONICAL_TRAIN_HYPHEN}_time_lora_${model_name1}_b${FT_BATCH_SIZE}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}_llm_price_gated${PRICE_RAND_INIT_SUFFIX}${EPOCH_SUFFIX}"
  if [ -f "${GATED_JOINT_PREFIX}_llm.pt" ] && [ -f "${GATED_JOINT_PREFIX}_price.pt" ] && [ -f "${GATED_JOINT_PREFIX}_gate.pt" ]; then
    echo "Finetuned GatedJointPrice weights already exist, skipping finetune:"
    echo "  LLM:   ${GATED_JOINT_PREFIX}_llm.pt"
    echo "  PRICE: ${GATED_JOINT_PREFIX}_price.pt"
    echo "  Gate:  ${GATED_JOINT_PREFIX}_gate.pt"
  else
    #########################Gated Joint LLM+PRICE finetune#########################
    algo=llm_price_finetune
    hid_units=2048
    lr=0.0001
    price_lr=${PRICE_LR:-$PRICE_LR_DEFAULT}
    batch_size=$FT_BATCH_SIZE

    echo "Gated Joint LLM+PRICE finetune"

    setup_args_and_suffixes

    python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                        --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_lora_gated_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${EPOCH_SUFFIX}.log \
                                        --db $DB_ENGINE \
                                        --workloads_train "${TRAIN_WLS[@]}" \
                                        --workload_test ${WORKLOAD_TEST} \
                                        --algo ${algo} \
                                        --learning_rate $lr \
                                        --price_lr $price_lr \
                                        --batch_size $batch_size \
                                        --hid_units $hid_units \
                                        --model_name $model_name \
                                        --train_ratio $train_ratio \
                                        --llm_mode lora \
                                        --use_price_gate \
                                        --num_epoch $FT_NUM_EPOCH \
                                        --seed $SEED \
                                        --price_model_path $PRICE_MODEL_PATH \
                                        --price_bin_size $PRICE_BIN_SIZE \
                                        $BUCKETIZE_ARG \
                                        $QUANTIFICATION_ARG \
                                        $REMOVED_FIELDS_ARG \
                                        $PRICE_M_ARG $PRICE_S_ARG \
                                        $PRICE_RANDOM_INIT_FLAG \
                                        $CHECKPOINT_INTERVAL_ARG
  fi

  #########################inference: pre-trained GatedJointPrice#########################
  algo=llm_price
  embed_size=${EMBED_SIZE:-1000}
  hid_units=2048
  lr=0.0001
  batch_size=64

  echo "inference: pre-trained GatedJointPrice"

  setup_args_and_suffixes

  python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                      --output_dir_qerror ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-lora_priceGatedJoint_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_RAND_INIT_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}_seed${SEED}.csv \
                                      --output_dir_abs ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-lora_priceGatedJoint_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_RAND_INIT_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}_seed${SEED}_abs.txt \
                                      --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-lora_priceGatedJoint_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_RAND_INIT_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}_seed${SEED}.log \
                                      --db $DB_ENGINE \
                                      --workloads_train "${TRAIN_WLS[@]}" \
                                      --workload_test ${WORKLOAD_TEST} \
                                      --algo ${algo} \
                                      --learning_rate $lr \
                                      --batch_size $batch_size \
                                      --hid_units $hid_units \
                                      --model_name $model_name \
                                      --embed_size $embed_size \
                                      --train_ratio 1.0 \
                                      --llm_mode inference \
                                      --num_epoch 100 \
                                      --llm_pretrained lora \
                                      --llm_pretrained_task $llm_pretrained_task \
                                      --price_model_path $PRICE_MODEL_PATH \
                                      --price_bin_size $PRICE_BIN_SIZE \
                                      --price_weights_source gated_joint \
                                      --seed $SEED \
                                      --ft_batch_size $FT_BATCH_SIZE \
                                      --ft_num_epoch $FT_NUM_EPOCH \
                                      $BUCKETIZE_ARG \
                                      $QUANTIFICATION_ARG \
                                      $EMBEDDINGS_ARG \
                                      $REMOVED_FIELDS_ARG \
                                      $PRICE_M_ARG $PRICE_S_ARG \
                                      $PRICE_RANDOM_INIT_FLAG
fi

if [ "$finetune" == "CrossAttentionJoint" ]; then
  PRICE_MODEL_PATH=${PRICE_MODEL_PATH:-"/root/PRICE/results/model_params.pth"}
  PRICE_BIN_SIZE=${PRICE_BIN_SIZE:-40}

  # Check if finetuned CrossAttentionJoint weights already exist
  CROSS_ATTN_JOINT_PREFIX="finetuned_models/${DB_ENGINE}/${CANONICAL_TRAIN_HYPHEN}_time_lora_${model_name1}_b${FT_BATCH_SIZE}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}_llm_price${CROSS_ATTN_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${N_CROSS_LAYERS_SUFFIX}${EPOCH_SUFFIX}"
  if [ -f "${CROSS_ATTN_JOINT_PREFIX}_llm.pt" ] && [ -f "${CROSS_ATTN_JOINT_PREFIX}_price.pt" ]; then
    echo "Finetuned CrossAttentionJoint weights already exist, skipping finetune:"
    echo "  LLM:   ${CROSS_ATTN_JOINT_PREFIX}_llm.pt"
    echo "  PRICE: ${CROSS_ATTN_JOINT_PREFIX}_price.pt"
  else
    #########################Cross-Attention Joint LLM+PRICE finetune#########################
    algo=llm_price_finetune
    hid_units=2048
    lr=0.0001
    price_lr=${PRICE_LR:-$PRICE_LR_DEFAULT}
    batch_size=$FT_BATCH_SIZE
    grad_accum_steps=${GRAD_ACCUM_STEPS:-1}

    echo "Cross-Attention Joint LLM+PRICE finetune"

    # Build grad_accum arg
    GRAD_ACCUM_ARG=""
    if [[ "$grad_accum_steps" -gt 1 ]]; then
      GRAD_ACCUM_ARG="--grad_accum_steps $grad_accum_steps"
      echo "  Gradient accumulation: ${grad_accum_steps} steps (effective batch = ${batch_size} * ${grad_accum_steps})"
    fi

    setup_args_and_suffixes

    python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                        --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_lora_crossAttn_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${N_CROSS_LAYERS_SUFFIX}${EPOCH_SUFFIX}.log \
                                        --db $DB_ENGINE \
                                        --workloads_train "${TRAIN_WLS[@]}" \
                                        --workload_test ${WORKLOAD_TEST} \
                                        --algo ${algo} \
                                        --learning_rate $lr \
                                        --price_lr $price_lr \
                                        --batch_size $batch_size \
                                        --hid_units $hid_units \
                                        --model_name $model_name \
                                        --train_ratio $train_ratio \
                                        --llm_mode lora \
                                        --use_cross_attention \
                                        --num_epoch $FT_NUM_EPOCH \
                                        --seed $SEED \
                                        --price_model_path $PRICE_MODEL_PATH \
                                        --price_bin_size $PRICE_BIN_SIZE \
                                        $BUCKETIZE_ARG \
                                        $QUANTIFICATION_ARG \
                                        $REMOVED_FIELDS_ARG \
                                        $PRICE_M_ARG $PRICE_S_ARG \
                                        $PRICE_RANDOM_INIT_FLAG \
                                        $CHECKPOINT_INTERVAL_ARG \
                                        $GRAD_ACCUM_ARG \
                                        $PRICE_N_LAYERS_ARG \
                                        $N_CROSS_LAYERS_ARG \
                                        $CROSS_ATTN_LR_ARG
  fi

  #########################inference: pre-trained CrossAttentionJoint#########################
  # Cross-attention requires the full model (LLM+PRICE+cross-attn) — uses llm_price with cross_attn_joint source
  algo=llm_price
  embed_size=${EMBED_SIZE:-1000}
  hid_units=2048
  lr=0.0001
  batch_size=64

  echo "inference: pre-trained CrossAttentionJoint"

  setup_args_and_suffixes

  python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                      --output_dir_qerror ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-lora_priceCrossAttnJoint_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${REFINED_POOL_SUFFIX}${TRIPLE_CONCAT_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${N_CROSS_LAYERS_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}${RETRAIN_MLP_SUFFIX}_seed${SEED}.csv \
                                      --output_dir_abs ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-lora_priceCrossAttnJoint_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${REFINED_POOL_SUFFIX}${TRIPLE_CONCAT_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${N_CROSS_LAYERS_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}${RETRAIN_MLP_SUFFIX}_seed${SEED}_abs.txt \
                                      --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-lora_priceCrossAttnJoint_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${REFINED_POOL_SUFFIX}${TRIPLE_CONCAT_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${N_CROSS_LAYERS_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}${RETRAIN_MLP_SUFFIX}_seed${SEED}.log \
                                      --db $DB_ENGINE \
                                      --workloads_train "${TRAIN_WLS[@]}" \
                                      --workload_test ${WORKLOAD_TEST} \
                                      --algo ${algo} \
                                      --learning_rate $lr \
                                      --batch_size $batch_size \
                                      --hid_units $hid_units \
                                      --model_name $model_name \
                                      --embed_size $embed_size \
                                      --train_ratio 1.0 \
                                      --llm_mode inference \
                                      --num_epoch 100 \
                                      --llm_pretrained lora \
                                      --llm_pretrained_task $llm_pretrained_task \
                                      --price_model_path $PRICE_MODEL_PATH \
                                      --price_bin_size $PRICE_BIN_SIZE \
                                      --price_weights_source cross_attn_joint \
                                      --use_cross_attention \
                                      --seed $SEED \
                                      --ft_batch_size $FT_BATCH_SIZE \
                                      --ft_num_epoch $FT_NUM_EPOCH \
                                      $BUCKETIZE_ARG \
                                      $QUANTIFICATION_ARG \
                                      $EMBEDDINGS_ARG \
                                      $REMOVED_FIELDS_ARG \
                                      $PRICE_M_ARG $PRICE_S_ARG \
                                      $PRICE_RANDOM_INIT_FLAG \
                                      $PRICE_N_LAYERS_ARG \
                                      $N_CROSS_LAYERS_ARG \
                                      $RETRAIN_MLP_FLAG \
                                      $REFINED_POOL_FLAG \
                                      $TRIPLE_CONCAT_FLAG \
                                      $EARLY_STOP_ARG
fi

if [ "$finetune" == "BiCrossAttentionJoint" ]; then
  PRICE_MODEL_PATH=${PRICE_MODEL_PATH:-"/root/PRICE/results/model_params.pth"}
  PRICE_BIN_SIZE=${PRICE_BIN_SIZE:-40}

  # Check if finetuned BiCrossAttentionJoint weights already exist
  BI_CROSS_ATTN_JOINT_PREFIX="finetuned_models/${DB_ENGINE}/${CANONICAL_TRAIN_HYPHEN}_time_lora_${model_name1}_b${FT_BATCH_SIZE}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}_llm_price${BI_CROSS_ATTN_SUFFIX}${REFINED_POOL_SUFFIX}${TRIPLE_CONCAT_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${N_CROSS_LAYERS_SUFFIX}${EPOCH_SUFFIX}"
  if [ -f "${BI_CROSS_ATTN_JOINT_PREFIX}_llm.pt" ] && [ -f "${BI_CROSS_ATTN_JOINT_PREFIX}_price.pt" ]; then
    echo "Finetuned BiCrossAttentionJoint weights already exist, skipping finetune:"
    echo "  LLM:   ${BI_CROSS_ATTN_JOINT_PREFIX}_llm.pt"
    echo "  PRICE: ${BI_CROSS_ATTN_JOINT_PREFIX}_price.pt"
  else
    #########################Bidirectional Cross-Attention Joint LLM+PRICE finetune#########################
    algo=llm_price_finetune
    hid_units=2048
    lr=0.0001
    price_lr=${PRICE_LR:-$PRICE_LR_DEFAULT}
    batch_size=$FT_BATCH_SIZE
    grad_accum_steps=${GRAD_ACCUM_STEPS:-1}

    echo "Bidirectional Cross-Attention Joint LLM+PRICE finetune"

    # Build grad_accum arg
    GRAD_ACCUM_ARG=""
    if [[ "$grad_accum_steps" -gt 1 ]]; then
      GRAD_ACCUM_ARG="--grad_accum_steps $grad_accum_steps"
      echo "  Gradient accumulation: ${grad_accum_steps} steps (effective batch = ${batch_size} * ${grad_accum_steps})"
    fi

    setup_args_and_suffixes

    python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                        --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_lora_biCrossAttn_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${REFINED_POOL_SUFFIX}${TRIPLE_CONCAT_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${N_CROSS_LAYERS_SUFFIX}${EPOCH_SUFFIX}.log \
                                        --db $DB_ENGINE \
                                        --workloads_train "${TRAIN_WLS[@]}" \
                                        --workload_test ${WORKLOAD_TEST} \
                                        --algo ${algo} \
                                        --learning_rate $lr \
                                        --price_lr $price_lr \
                                        --batch_size $batch_size \
                                        --hid_units $hid_units \
                                        --model_name $model_name \
                                        --train_ratio $train_ratio \
                                        --llm_mode lora \
                                        --use_bi_cross_attention \
                                        --num_epoch $FT_NUM_EPOCH \
                                        --seed $SEED \
                                        --price_model_path $PRICE_MODEL_PATH \
                                        --price_bin_size $PRICE_BIN_SIZE \
                                        $BUCKETIZE_ARG \
                                        $QUANTIFICATION_ARG \
                                        $REMOVED_FIELDS_ARG \
                                        $PRICE_M_ARG $PRICE_S_ARG \
                                        $PRICE_RANDOM_INIT_FLAG \
                                        $CHECKPOINT_INTERVAL_ARG \
                                        $GRAD_ACCUM_ARG \
                                        $PRICE_N_LAYERS_ARG \
                                        $N_CROSS_LAYERS_ARG \
                                        $CROSS_ATTN_LR_ARG \
                                        $REFINED_POOL_FLAG \
                                      $TRIPLE_CONCAT_FLAG \
                                      $EARLY_STOP_ARG
  fi

  #########################inference: pre-trained BiCrossAttentionJoint#########################
  # Bidirectional cross-attention requires the full model (LLM+PRICE+bi-cross-attn)
  algo=llm_price
  embed_size=${EMBED_SIZE:-1000}
  hid_units=2048
  lr=0.0001
  batch_size=64

  echo "inference: pre-trained BiCrossAttentionJoint"

  setup_args_and_suffixes

  python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                      --output_dir_qerror ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-lora_priceBiCrossAttnJoint_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${REFINED_POOL_SUFFIX}${TRIPLE_CONCAT_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${N_CROSS_LAYERS_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}${RETRAIN_MLP_SUFFIX}_seed${SEED}.csv \
                                      --output_dir_abs ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-lora_priceBiCrossAttnJoint_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${REFINED_POOL_SUFFIX}${TRIPLE_CONCAT_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${N_CROSS_LAYERS_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}${RETRAIN_MLP_SUFFIX}_seed${SEED}_abs.txt \
                                      --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-lora_priceBiCrossAttnJoint_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${REFINED_POOL_SUFFIX}${TRIPLE_CONCAT_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${N_CROSS_LAYERS_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}${RETRAIN_MLP_SUFFIX}_seed${SEED}.log \
                                      --db $DB_ENGINE \
                                      --workloads_train "${TRAIN_WLS[@]}" \
                                      --workload_test ${WORKLOAD_TEST} \
                                      --algo ${algo} \
                                      --learning_rate $lr \
                                      --batch_size $batch_size \
                                      --hid_units $hid_units \
                                      --model_name $model_name \
                                      --embed_size $embed_size \
                                      --train_ratio 1.0 \
                                      --llm_mode inference \
                                      --num_epoch 100 \
                                      --llm_pretrained lora \
                                      --llm_pretrained_task $llm_pretrained_task \
                                      --price_model_path $PRICE_MODEL_PATH \
                                      --price_bin_size $PRICE_BIN_SIZE \
                                      --price_weights_source bi_cross_attn_joint \
                                      --use_bi_cross_attention \
                                      --seed $SEED \
                                      --ft_batch_size $FT_BATCH_SIZE \
                                      --ft_num_epoch $FT_NUM_EPOCH \
                                      $BUCKETIZE_ARG \
                                      $QUANTIFICATION_ARG \
                                      $EMBEDDINGS_ARG \
                                      $REMOVED_FIELDS_ARG \
                                      $PRICE_M_ARG $PRICE_S_ARG \
                                      $PRICE_RANDOM_INIT_FLAG \
                                      $PRICE_N_LAYERS_ARG \
                                      $N_CROSS_LAYERS_ARG \
                                      $RETRAIN_MLP_FLAG \
                                      $REFINED_POOL_FLAG \
                                      $TRIPLE_CONCAT_FLAG \
                                      $EARLY_STOP_ARG
fi

if [ "$finetune" == "PriceFTthenJoint" ]; then
  #########################Case 6: Frozen-init then joint (PriceFTthenJoint)#########################
  PRICE_MODEL_PATH=${PRICE_MODEL_PATH:-"/root/PRICE/results/model_params.pth"}
  PRICE_BIN_SIZE=${PRICE_BIN_SIZE:-40}

  # Step 1: Finetune PRICE+MLP with frozen LLM (reuse PriceFTwithLLM step 1)
  FROZEN_JOINT_FILE="finetuned_models/${DB_ENGINE}/${CANONICAL_TRAIN_HYPHEN}_time_inference_${model_name1}_b${FT_BATCH_SIZE}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}_llm_price${PRICE_RAND_INIT_SUFFIX}${EPOCH_SUFFIX}_price.pt"
  if [ -f "$FROZEN_JOINT_FILE" ]; then
    echo "Frozen-joint finetuned PRICE weights already exist: $FROZEN_JOINT_FILE"
  else
    algo=llm_price_finetune
    hid_units=2048
    lr=0.0001
    price_lr=${PRICE_LR:-$PRICE_LR_DEFAULT}
    batch_size=$FT_BATCH_SIZE

    echo "PriceFTthenJoint Step 1: finetune PRICE+MLP with frozen LLM (time)"

    setup_args_and_suffixes

    python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                        --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_frozen_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${EPOCH_SUFFIX}.log \
                                        --db $DB_ENGINE \
                                        --workloads_train "${TRAIN_WLS[@]}" \
                                        --workload_test ${WORKLOAD_TEST} \
                                        --algo ${algo} \
                                        --learning_rate $lr \
                                        --price_lr $price_lr \
                                        --batch_size $batch_size \
                                        --hid_units $hid_units \
                                        --model_name $model_name \
                                        --train_ratio $train_ratio \
                                        --llm_mode inference \
                                        --freeze_llm \
                                        --num_epoch $FT_NUM_EPOCH \
                                        --seed $SEED \
                                        --price_model_path $PRICE_MODEL_PATH \
                                        --price_bin_size $PRICE_BIN_SIZE \
                                        $BUCKETIZE_ARG \
                                        $QUANTIFICATION_ARG \
                                        $REMOVED_FIELDS_ARG \
                                        $PRICE_M_ARG $PRICE_S_ARG \
                                        $PRICE_RANDOM_INIT_FLAG \
                                        $CHECKPOINT_INTERVAL_ARG
  fi

  # Step 2: Joint finetune with frozen-init PRICE
  FROZEN_INIT_PREFIX="finetuned_models/${DB_ENGINE}/${CANONICAL_TRAIN_HYPHEN}_time_lora_${model_name1}_b${FT_BATCH_SIZE}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}_llm_price_frozenInit${PRICE_RAND_INIT_SUFFIX}${EPOCH_SUFFIX}"
  if [ -f "${FROZEN_INIT_PREFIX}_llm.pt" ] && [ -f "${FROZEN_INIT_PREFIX}_price.pt" ]; then
    echo "Frozen-init joint weights already exist, skipping finetune:"
    echo "  LLM:   ${FROZEN_INIT_PREFIX}_llm.pt"
    echo "  PRICE: ${FROZEN_INIT_PREFIX}_price.pt"
  else
    algo=llm_price_finetune
    hid_units=2048
    lr=0.0001
    price_lr=${PRICE_LR:-$PRICE_LR_DEFAULT}
    batch_size=$FT_BATCH_SIZE

    echo "PriceFTthenJoint Step 2: joint LLM+PRICE finetune with frozen-init PRICE (time)"

    setup_args_and_suffixes

    python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                        --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_lora_frozenInit_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${EPOCH_SUFFIX}.log \
                                        --db $DB_ENGINE \
                                        --workloads_train "${TRAIN_WLS[@]}" \
                                        --workload_test ${WORKLOAD_TEST} \
                                        --algo ${algo} \
                                        --learning_rate $lr \
                                        --price_lr $price_lr \
                                        --batch_size $batch_size \
                                        --hid_units $hid_units \
                                        --model_name $model_name \
                                        --train_ratio $train_ratio \
                                        --llm_mode lora \
                                        --price_init_frozen_joint \
                                        --num_epoch $FT_NUM_EPOCH \
                                        --seed $SEED \
                                        --price_model_path $PRICE_MODEL_PATH \
                                        --price_bin_size $PRICE_BIN_SIZE \
                                        $BUCKETIZE_ARG \
                                        $QUANTIFICATION_ARG \
                                        $REMOVED_FIELDS_ARG \
                                        $PRICE_M_ARG $PRICE_S_ARG \
                                        $PRICE_RANDOM_INIT_FLAG \
                                        $CHECKPOINT_INTERVAL_ARG
  fi

  # Step 3: Inference with frozen-init joint weights
  algo=llm_price
  embed_size=${EMBED_SIZE:-1000}
  hid_units=2048
  lr=0.0001
  batch_size=64

  echo "PriceFTthenJoint Step 3: inference with frozen-init joint weights (time)"

  setup_args_and_suffixes

  python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                      --output_dir_qerror ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-lora_priceFTthenJoint_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_RAND_INIT_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}_seed${SEED}.csv \
                                      --output_dir_abs ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-lora_priceFTthenJoint_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_RAND_INIT_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}_seed${SEED}_abs.txt \
                                      --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-lora_priceFTthenJoint_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_RAND_INIT_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}_seed${SEED}.log \
                                      --db $DB_ENGINE \
                                      --workloads_train "${TRAIN_WLS[@]}" \
                                      --workload_test ${WORKLOAD_TEST} \
                                      --algo ${algo} \
                                      --learning_rate $lr \
                                      --batch_size $batch_size \
                                      --hid_units $hid_units \
                                      --model_name $model_name \
                                      --embed_size $embed_size \
                                      --train_ratio 1.0 \
                                      --llm_mode inference \
                                      --num_epoch 100 \
                                      --llm_pretrained lora \
                                      --llm_pretrained_task $llm_pretrained_task \
                                      --price_model_path $PRICE_MODEL_PATH \
                                      --price_bin_size $PRICE_BIN_SIZE \
                                      --price_weights_source joint_frozen_init \
                                      --seed $SEED \
                                      --ft_batch_size $FT_BATCH_SIZE \
                                      --ft_num_epoch $FT_NUM_EPOCH \
                                      $BUCKETIZE_ARG \
                                      $QUANTIFICATION_ARG \
                                      $EMBEDDINGS_ARG \
                                      $REMOVED_FIELDS_ARG \
                                      $PRICE_M_ARG $PRICE_S_ARG \
                                      $PRICE_RANDOM_INIT_FLAG
fi
