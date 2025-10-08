# 1) split the first arg into an array of workloads:
IFS=' ' read -r -a TRAIN_WLS <<< "$1"
WORKLOAD_TEST=$2
train_ratio=$3
SEED=$4
# optional: feature mask for aimeetsai (default all on)
AIME_FEATURES=${5:-11111}
# optional: algorithm (default aimai)
ALGO=${6:-aimai}
# optional: task (default card)
TASK=${7:-card}

# 2) build the parallel array of dat_paths:
DAT_PATHS=()
for wl in "${TRAIN_WLS[@]}"; do
  if [[ "$wl" == "syn" || "$wl" == "job" || "$wl" == "job_full" ]]; then
    DAT_PATHS+=( "../queryPlans/imdb/postgres/" )
  else
    DAT_PATHS+=( "../queryPlans/$wl/postgres/" )
  fi
done

# one test path
if [[ "$WORKLOAD_TEST" == "syn" || "$WORKLOAD_TEST" == "job" || "$WORKLOAD_TEST" == "job_full" ]]; then
  DAT_PATH_TEST="../queryPlans/imdb/postgres/"
else
  DAT_PATH_TEST="../queryPlans/$WORKLOAD_TEST/postgres/"
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
echo "${ALGO} ${TASK}"

# Check workload constraints for card task
if [[ "$TASK" == "card" ]] && [[ "$WORKLOAD_TEST" != "job" && "$WORKLOAD_TEST" != "syn" && "$WORKLOAD_TEST" != "stats" ]]; then
    echo "Cardinality prediction only supported for job, syn, stats workloads"
    exit 1
fi

# Set up file names
base_name="${TASK}_${ALGO}_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_seed${SEED}"
if [[ "$ALGO" == "aimai" ]]; then
    base_name="${base_name}_f${AIME_FEATURES}"
fi

# Call train.py with appropriate arguments
if [[ "$TASK" == "card" ]]; then
    python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                    --output_dir_qerror results/results_Train_"${TRAIN_WLS[*]}"_Test_"$WORKLOAD_TEST"_ours/${base_name}.csv \
                                    --output_dir_abs results/results_Train_"${TRAIN_WLS[*]}"_Test_"$WORKLOAD_TEST"_ours/${base_name}_abs.txt \
                                    --log_file logs/logs_Train_"${TRAIN_WLS[*]}"_Test_"$WORKLOAD_TEST"_ours/${base_name}.log \
                                    --db postgres \
                                    --workloads_train "${TRAIN_WLS[@]}" \
                                    --workload_test ${WORKLOAD_TEST} \
                                    --algo ${ALGO} \
                                    --learning_rate $lr \
                                    --batch_size $batch_size \
                                    --train_ratio $train_ratio \
                                    --card \
                                    --seed $SEED \
                                    --aime_features ${AIME_FEATURES}
else
    python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                    --output_dir_qerror results/results_Train_"${TRAIN_WLS[*]}"_Test_"$WORKLOAD_TEST"_ours/${base_name}.csv \
                                    --output_dir_abs results/results_Train_"${TRAIN_WLS[*]}"_Test_"$WORKLOAD_TEST"_ours/${base_name}_abs.txt \
                                    --log_file logs/logs_Train_"${TRAIN_WLS[*]}"_Test_"$WORKLOAD_TEST"_ours/${base_name}.log \
                                    --db postgres \
                                    --workloads_train "${TRAIN_WLS[@]}" \
                                    --workload_test ${WORKLOAD_TEST} \
                                    --algo ${ALGO} \
                                    --learning_rate $lr \
                                    --batch_size $batch_size \
                                    --train_ratio $train_ratio \
                                    --seed $SEED \
                                    --aime_features ${AIME_FEATURES}
fi
