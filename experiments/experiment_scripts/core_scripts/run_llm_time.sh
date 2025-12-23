
# 1) split the first arg into an array of workloads:
IFS=' ' read -r -a TRAIN_WLS <<< "$1"
WORKLOAD_TEST=$2
train_ratio=$3
finetune=$4
model_name=$5
model_name1=$6
SEED=$7

# 2) build the parallel array of dat_paths:
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

# one test path
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

llm_pretrained_task=time

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
  
  # Determine directory names based on whether _rm- is in the filename
  RESULTS_DIR="results"
  LOGS_DIR="logs"
  if [[ "$REMOVED_FIELDS_SUFFIX" == *_rm-* ]]; then
    RESULTS_DIR="results_rm"
    LOGS_DIR="logs_rm"
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
                                      --output_dir_qerror ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-None_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${DOWNSTREAM_SUFFIX}${REMOVED_FIELDS_SUFFIX}_seed${SEED}.csv \
                                      --output_dir_abs ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-None_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${DOWNSTREAM_SUFFIX}${REMOVED_FIELDS_SUFFIX}_seed${SEED}_abs.txt \
                                      --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-None_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${DOWNSTREAM_SUFFIX}${REMOVED_FIELDS_SUFFIX}_seed${SEED}.log \
                                      --db postgres \
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
                                      $REMOVED_FIELDS_ARG
fi

if [ "$finetune" == "True" ]; then
  #########################finetune#########################
  algo=llm_finetune
  hid_units=2048
  lr=0.0001
  batch_size=1     

  # Check which finetuning modes to run (default to both if not set)
  RUN_LAST=${FINETUNE_RUN_LAST:-true}
  RUN_LORA=${FINETUNE_RUN_LORA:-true}
  
  # Helper function to check if finetuned model exists
  check_model_exists() {
    local mode=$1
    local model_file="finetuned_models/${TRAIN_WLS_HYPHEN}_time_${mode}_${model_name1}_llm.pt"
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
                                          --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_last_postgres_${lr}_b${batch_size}_h${hid_units}_${model_name1}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}.log \
                                          --db postgres \
                                          --workloads_train "${TRAIN_WLS[@]}" \
                                          --workload_test ${WORKLOAD_TEST} \
                                          --algo ${algo} \
                                          --learning_rate $lr \
                                          --batch_size $batch_size \
                                          --hid_units $hid_units \
                                          --model_name $model_name \
                                          --train_ratio $train_ratio \
                                          --llm_mode $llm_mode \
                                          --num_epoch 1 \
                                          --seed $SEED \
                                          $BUCKETIZE_ARG \
                                          $QUANTIFICATION_ARG \
                                          $REMOVED_FIELDS_ARG
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
                                          --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_lora_postgres_${lr}_b${batch_size}_h${hid_units}_${model_name1}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}.log \
                                          --db postgres \
                                          --workloads_train "${TRAIN_WLS[@]}" \
                                          --workload_test ${WORKLOAD_TEST} \
                                          --algo ${algo} \
                                          --learning_rate $lr \
                                          --batch_size $batch_size \
                                          --hid_units $hid_units \
                                          --model_name $model_name \
                                          --train_ratio $train_ratio \
                                          --llm_mode $llm_mode \
                                          --num_epoch 1 \
                                          --seed $SEED \
                                          $BUCKETIZE_ARG \
                                          $QUANTIFICATION_ARG \
                                          $REMOVED_FIELDS_ARG
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
                                        --output_dir_qerror ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-${llm_pretrained}_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${DOWNSTREAM_SUFFIX}${REMOVED_FIELDS_SUFFIX}_seed${SEED}.csv \
                                        --output_dir_abs ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-${llm_pretrained}_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${DOWNSTREAM_SUFFIX}${REMOVED_FIELDS_SUFFIX}_seed${SEED}_abs.txt \
                                        --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-${llm_pretrained}_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${DOWNSTREAM_SUFFIX}${REMOVED_FIELDS_SUFFIX}_seed${SEED}.log \
                                        --db postgres \
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
                                        --num_epoch 200 \
                                        --llm_pretrained $llm_pretrained \
                                        --llm_pretrained_task $llm_pretrained_task \
                                        --seed $SEED \
                                        $BUCKETIZE_ARG \
                                        $QUANTIFICATION_ARG \
                                        $EMBEDDINGS_ARG \
                                        $VERBOSE_ARG \
                                        $DOWNSTREAM_ARG \
                                        $REMOVED_FIELDS_ARG
  fi

  if [[ "$RUN_LORA" == "true" ]]; then
    llm_pretrained=lora                              
    echo "inference: pre-trained lora"
    
    setup_args_and_suffixes
    
    python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                        --output_dir_qerror ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-${llm_pretrained}_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${DOWNSTREAM_SUFFIX}${REMOVED_FIELDS_SUFFIX}_seed${SEED}.csv \
                                        --output_dir_abs ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-${llm_pretrained}_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${DOWNSTREAM_SUFFIX}${REMOVED_FIELDS_SUFFIX}_seed${SEED}_abs.txt \
                                        --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-${llm_pretrained}_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${DOWNSTREAM_SUFFIX}${REMOVED_FIELDS_SUFFIX}_seed${SEED}.log \
                                        --db postgres \
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
                                        --num_epoch 200 \
                                        --llm_pretrained $llm_pretrained \
                                        --llm_pretrained_task $llm_pretrained_task \
                                        --seed $SEED \
                                        $BUCKETIZE_ARG \
                                        $QUANTIFICATION_ARG \
                                        $EMBEDDINGS_ARG \
                                        $VERBOSE_ARG \
                                        $DOWNSTREAM_ARG \
                                        $REMOVED_FIELDS_ARG
  fi
fi
