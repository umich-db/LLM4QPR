# 1) split the first arg into an array of workloads:
IFS=' ' read -r -a TRAIN_WLS <<< "$1"
WORKLOAD_TEST=$2
train_ratio=$3
SEED=$4
# optional: algorithm (default aimai)
ALGO=${5:-aimai}
# optional: task (default card)
TASK=${6:-card}
# optional: database engine (default postgres, can be set via DB_ENGINE env var)
DB_ENGINE=${DB_ENGINE:-postgres}

# 2) build the parallel array of dat_paths:
DAT_PATHS=()
for wl in "${TRAIN_WLS[@]}"; do
  if [[ "$wl" == "syn" || "$wl" == "job" || "$wl" == "job_full" ]]; then
    DAT_PATHS+=( "../queryPlans/imdb/${DB_ENGINE}/" )
  else
    DAT_PATHS+=( "../queryPlans/$wl/${DB_ENGINE}/" )
  fi
done

# one test path
if [[ "$WORKLOAD_TEST" == "syn" || "$WORKLOAD_TEST" == "job" || "$WORKLOAD_TEST" == "job_full" ]]; then
  DAT_PATH_TEST="../queryPlans/imdb/${DB_ENGINE}/"
else
  DAT_PATH_TEST="../queryPlans/$WORKLOAD_TEST/${DB_ENGINE}/"
fi


# Set algorithm-specific parameters
case $ALGO in
    "postgres")
        hid_units=99999999
        lr=-1
        batch_size=99999999
        ;;
    "bao")
        hid_units=256
        lr=0.001
        batch_size=16
        ;;
    "aimai")
        hid_units=256
        lr=0.0001
        batch_size=64
        ;;
    "qf")
        hid_units=256
        lr=0.001
        batch_size=64
        ;;
    "e2e_cost")
        hid_units=256
        lr=0.001
        batch_size=64
        ;;
    *)
        echo "Unknown algorithm: $ALGO. Supported: postgres, bao, aimai, qf, e2e_cost"
        exit 1
        ;;
esac

# Run experiments based on algorithm and task
echo "${ALGO} ${TASK} (db=${DB_ENGINE})"

# Check workload constraints for card task
if [[ "$TASK" == "card" ]] && [[ "$WORKLOAD_TEST" != "job" && "$WORKLOAD_TEST" != "syn" && "$WORKLOAD_TEST" != "stats" ]]; then
    echo "Cardinality prediction only supported for job, syn, stats workloads"
    exit 1
fi

# Get verbose_info setting from environment variable
VERBOSE_ARG=""
if [[ "$VERBOSE_INFO" == "true" || "$VERBOSE_INFO" == "True" ]]; then
  VERBOSE_ARG="--verbose_info"
fi

# Output directories namespaced by database engine (matches run_llm_time.sh)
RESULTS_DIR="results/${DB_ENGINE}"
LOGS_DIR="logs/${DB_ENGINE}"

# Set up file names
base_name="${TASK}_${ALGO}_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_seed${SEED}"

# Call train.py with appropriate arguments
if [[ "$TASK" == "card" ]]; then
    python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                    --output_dir_qerror ${RESULTS_DIR}/results_Train_"${TRAIN_WLS[*]}"_Test_"$WORKLOAD_TEST"_ours/${base_name}.csv \
                                    --output_dir_abs ${RESULTS_DIR}/results_Train_"${TRAIN_WLS[*]}"_Test_"$WORKLOAD_TEST"_ours/${base_name}_abs.txt \
                                    --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS[*]}"_Test_"$WORKLOAD_TEST"_ours/${base_name}.log \
                                    --db ${DB_ENGINE} \
                                    --workloads_train "${TRAIN_WLS[@]}" \
                                    --workload_test ${WORKLOAD_TEST} \
                                    --algo ${ALGO} \
                                    --num_epoch 100 \
                                    --learning_rate $lr \
                                    --batch_size $batch_size \
                                    --train_ratio $train_ratio \
                                    --card \
                                    --seed $SEED \
                                    $VERBOSE_ARG
else
    python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                    --output_dir_qerror ${RESULTS_DIR}/results_Train_"${TRAIN_WLS[*]}"_Test_"$WORKLOAD_TEST"_ours/${base_name}.csv \
                                    --output_dir_abs ${RESULTS_DIR}/results_Train_"${TRAIN_WLS[*]}"_Test_"$WORKLOAD_TEST"_ours/${base_name}_abs.txt \
                                    --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS[*]}"_Test_"$WORKLOAD_TEST"_ours/${base_name}.log \
                                    --db ${DB_ENGINE} \
                                    --workloads_train "${TRAIN_WLS[@]}" \
                                    --workload_test ${WORKLOAD_TEST} \
                                    --algo ${ALGO} \
                                    --num_epoch 100 \
                                    --learning_rate $lr \
                                    --batch_size $batch_size \
                                    --train_ratio $train_ratio \
                                    --seed $SEED \
                                    $VERBOSE_ARG
fi
