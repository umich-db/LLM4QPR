# 1) split the first arg into an array of workloads:
IFS=' ' read -r -a TRAIN_WLS <<< "$1"
WORKLOAD_TEST=$2
train_ratio=$3
SEED=$4

# 2) build the parallel array of dat_paths:
DAT_PATHS=()
for wl in "${TRAIN_WLS[@]}"; do
  if [[ "$wl" == "syn" || "$wl" == "job" ]]; then
    DAT_PATHS+=( "../queryPlans/imdb/postgres/" )
  else
    DAT_PATHS+=( "../queryPlans/$wl/postgres/" )
  fi
done

# one test path
if [[ "$WORKLOAD_TEST" == "syn" || "$WORKLOAD_TEST" == "job" ]]; then
  DAT_PATH_TEST="../queryPlans/imdb/postgres/"
else
  DAT_PATH_TEST="../queryPlans/$WORKLOAD_TEST/postgres/"
fi


algo=postgres
hid_units=99999999
lr=-1
batch_size=99999999
#time
echo "${algo} time"
python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                    --output_dir_qerror results/results_Train_"${TRAIN_WLS[*]}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_seed${SEED}.csv \
                                    --output_dir_abs results/results_Train_"${TRAIN_WLS[*]}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_seed${SEED}_abs.txt \
                                    --log_file logs/logs_Train_"${TRAIN_WLS[*]}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_seed${SEED}.log \
                                    --db postgres \
                                    --workloads_train "${TRAIN_WLS[@]}" \
                                    --workload_test ${WORKLOAD_TEST} \
                                    --algo ${algo} \
                                    --learning_rate $lr \
                                    --batch_size $batch_size \
                                    --hid_units $hid_units \
                                    --train_ratio $train_ratio \
                                    --seed $SEED

#card
if [[ "$WORKLOAD_TEST" == "job" || "$WORKLOAD_TEST" == "syn" || "$WORKLOAD_TEST" == "stats" ]]; then
    echo "${algo} card"
    python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                        --output_dir_qerror results/results_Train_"${TRAIN_WLS[*]}"_Test_"$WORKLOAD_TEST"_ours/card_${algo}_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_seed${SEED}.csv \
                                        --output_dir_abs results/results_Train_"${TRAIN_WLS[*]}"_Test_"$WORKLOAD_TEST"_ours/card_${algo}_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_seed${SEED}_abs.txt \
                                        --log_file logs/logs_Train_"${TRAIN_WLS[*]}"_Test_"$WORKLOAD_TEST"_ours/card_${algo}_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_seed${SEED}.log \
                                        --db postgres \
                                        --workloads_train "${TRAIN_WLS[@]}" \
                                        --workload_test ${WORKLOAD_TEST} \
                                        --algo ${algo} \
                                        --learning_rate $lr \
                                        --batch_size $batch_size \
                                        --train_ratio $train_ratio \
                                        --card \
                                        --seed $SEED
fi


algo=bao
hid_units=256
lr=0.001
batch_size=16
#time
echo "${algo} time"
python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                    --output_dir_qerror results/results_Train_"${TRAIN_WLS[*]}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_seed${SEED}.csv \
                                    --output_dir_abs results/results_Train_"${TRAIN_WLS[*]}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_seed${SEED}_abs.txt \
                                    --log_file logs/logs_Train_"${TRAIN_WLS[*]}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_seed${SEED}.log \
                                    --db postgres \
                                    --workloads_train "${TRAIN_WLS[@]}" \
                                    --workload_test ${WORKLOAD_TEST} \
                                    --algo ${algo} \
                                    --learning_rate $lr \
                                    --batch_size $batch_size \
                                    --train_ratio $train_ratio \
                                    --seed $SEED
#card
if [[ "$WORKLOAD_TEST" == "job" || "$WORKLOAD_TEST" == "syn" || "$WORKLOAD_TEST" == "stats" ]]; then
    echo "${algo} card"
    python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                        --output_dir_qerror results/results_Train_"${TRAIN_WLS[*]}"_Test_"$WORKLOAD_TEST"_ours/card_${algo}_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_seed${SEED}.csv \
                                        --output_dir_abs results/results_Train_"${TRAIN_WLS[*]}"_Test_"$WORKLOAD_TEST"_ours/card_${algo}_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_seed${SEED}_abs.txt \
                                        --log_file logs/logs_Train_"${TRAIN_WLS[*]}"_Test_"$WORKLOAD_TEST"_ours/card_${algo}_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_seed${SEED}.log \
                                        --db postgres \
                                        --workloads_train "${TRAIN_WLS[@]}" \
                                        --workload_test ${WORKLOAD_TEST} \
                                        --algo ${algo} \
                                        --learning_rate $lr \
                                        --batch_size $batch_size \
                                        --train_ratio $train_ratio \
                                        --card \
                                        --seed $SEED
fi


algo=aimai
hid_units=256
lr=0.0001
batch_size=64
#time
echo "${algo} time"
python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                    --output_dir_qerror results/results_Train_"${TRAIN_WLS[*]}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_seed${SEED}.csv \
                                    --output_dir_abs results/results_Train_"${TRAIN_WLS[*]}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_seed${SEED}_abs.txt \
                                    --log_file logs/logs_Train_"${TRAIN_WLS[*]}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_seed${SEED}.log \
                                    --db postgres \
                                    --workloads_train "${TRAIN_WLS[@]}" \
                                    --workload_test ${WORKLOAD_TEST} \
                                    --algo ${algo} \
                                    --learning_rate $lr \
                                    --batch_size $batch_size \
                                    --hid_units $hid_units \
                                    --train_ratio $train_ratio \
                                    --seed $SEED

# card
if [[ "$WORKLOAD_TEST" == "job" || "$WORKLOAD_TEST" == "syn" || "$WORKLOAD_TEST" == "stats" ]]; then
    echo "${algo} card"
    python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                        --output_dir_qerror results/results_Train_"${TRAIN_WLS[*]}"_Test_"$WORKLOAD_TEST"_ours/card_${algo}_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_seed${SEED}.csv \
                                        --output_dir_abs results/results_Train_"${TRAIN_WLS[*]}"_Test_"$WORKLOAD_TEST"_ours/card_${algo}_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_seed${SEED}_abs.txt \
                                        --log_file logs/logs_Train_"${TRAIN_WLS[*]}"_Test_"$WORKLOAD_TEST"_ours/card_${algo}_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_seed${SEED}.log \
                                        --db postgres \
                                        --workloads_train "${TRAIN_WLS[@]}" \
                                        --workload_test ${WORKLOAD_TEST} \
                                        --algo ${algo} \
                                        --learning_rate $lr \
                                        --batch_size $batch_size \
                                        --train_ratio $train_ratio \
                                        --card \
                                        --seed $SEED
fi



algo=qf
hid_units=256
lr=0.001
batch_size=64
#time
echo "${algo} time"
python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                    --output_dir_qerror results/results_Train_"${TRAIN_WLS[*]}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_seed${SEED}.csv \
                                    --output_dir_abs results/results_Train_"${TRAIN_WLS[*]}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_seed${SEED}_abs.txt \
                                    --log_file logs/logs_Train_"${TRAIN_WLS[*]}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_seed${SEED}.log \
                                    --db postgres \
                                    --workloads_train "${TRAIN_WLS[@]}" \
                                    --workload_test ${WORKLOAD_TEST} \
                                    --algo ${algo} \
                                    --learning_rate $lr \
                                    --batch_size $batch_size \
                                    --train_ratio $train_ratio \
                                    --seed $SEED

#card
if [[ "$WORKLOAD_TEST" == "job" || "$WORKLOAD_TEST" == "syn" || "$WORKLOAD_TEST" == "stats" ]]; then
    echo "${algo} card"
    python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                        --output_dir_qerror results/results_Train_"${TRAIN_WLS[*]}"_Test_"$WORKLOAD_TEST"_ours/card_${algo}_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_seed${SEED}.csv \
                                        --output_dir_abs results/results_Train_"${TRAIN_WLS[*]}"_Test_"$WORKLOAD_TEST"_ours/card_${algo}_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_seed${SEED}_abs.txt \
                                        --log_file logs/logs_Train_"${TRAIN_WLS[*]}"_Test_"$WORKLOAD_TEST"_ours/card_${algo}_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_seed${SEED}.log \
                                        --db postgres \
                                        --workloads_train "${TRAIN_WLS[@]}" \
                                        --workload_test ${WORKLOAD_TEST} \
                                        --algo ${algo} \
                                        --learning_rate $lr \
                                        --batch_size $batch_size \
                                        --train_ratio $train_ratio \
                                        --card \
                                        --seed $SEED
fi
