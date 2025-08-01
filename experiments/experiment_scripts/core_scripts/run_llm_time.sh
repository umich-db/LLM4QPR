
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
  if [[ "$wl" == "syn" || "$wl" == "job" ]]; then
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
if [[ "$WORKLOAD_TEST" == "syn" || "$WORKLOAD_TEST" == "job" ]]; then
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

if [ "$finetune" == "False" ]; then
  #########################inference: no pre-train#########################
  algo=llm
  embed_size=1000
  hid_units=2048
  lr=0.0001
  batch_size=64     

  echo "inference: no pre-train"
  python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                      --output_dir_qerror results/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-None_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}_seed${SEED}.csv \
                                      --output_dir_abs results/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-None_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}_seed${SEED}_abs.txt \
                                      --log_file logs/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-None_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}_seed${SEED}.log \
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
                                      --num_epoch 200 \
                                      --seed $SEED \
                                      # --embeddings_exist
fi

if [ "$finetune" == "True" ]; then
  #########################finetune#########################
  algo=llm_finetune
  hid_units=2048
  lr=0.0001
  batch_size=2     

  # llm_mode=last
  # echo "finetune: last"
  # python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
  #                                     --log_file logs/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_last_postgres_${lr}_b${batch_size}_h${hid_units}_${model_name1}.log \
  #                                     --db postgres \
  #                                     --workloads_train "${TRAIN_WLS[@]}" \
  #                                     --workload_test ${WORKLOAD_TEST} \
  #                                     --algo ${algo} \
  #                                     --learning_rate $lr \
  #                                     --batch_size $batch_size \
  #                                     --hid_units $hid_units \
  #                                     --model_name $model_name \
  #                                     --train_ratio $train_ratio \
  #                                     --llm_mode $llm_mode \
  #                                     --num_epoch 1


  llm_mode=lora
  echo "finetune: lora"
  python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                      --log_file logs/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_lora_postgres_${lr}_b${batch_size}_h${hid_units}_${model_name1}.log \
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
                                      --num_epoch 1

  #########################inference: pre-trained#########################
  algo=llm
  embed_size=1000
  hid_units=2048
  lr=0.0001
  batch_size=64     

  # llm_pretrained=last
  # echo "inference: pre-trained last"
  # python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
  #                                     --output_dir_qerror results/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-${llm_pretrained}_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}_seed${SEED}.csv \
  #                                     --output_dir_abs results/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-${llm_pretrained}_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}_seed${SEED}_abs.txt \
  #                                     --log_file logs/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-${llm_pretrained}_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}_seed${SEED}.log \
  #                                     --db postgres \
  #                                     --workloads_train "${TRAIN_WLS[@]}" \
  #                                     --workload_test ${WORKLOAD_TEST} \
  #                                     --algo ${algo} \
  #                                     --learning_rate $lr \
  #                                     --batch_size $batch_size \
  #                                     --hid_units $hid_units \
  #                                     --model_name $model_name \
  #                                     --embed_size $embed_size \
  #                                     --train_ratio 1.0 \
  #                                     --llm_mode inference \
  #                                     --num_epoch 200 \
  #                                     --llm_pretrained $llm_pretrained \
  #                                     --llm_pretrained_task $llm_pretrained_task \
  #                                     --seed $SEED \
  #                                     --embeddings_exist


  llm_pretrained=lora                              
  echo "inference: pre-trained lora"
  python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                      --output_dir_qerror results/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-${llm_pretrained}_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}_seed${SEED}.csv \
                                      --output_dir_abs results/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-${llm_pretrained}_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}_seed${SEED}_abs.txt \
                                      --log_file logs/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours/time_${algo}_pretrained-${llm_pretrained}_${train_ratio}_cdf_postgres_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}_seed${SEED}.log \
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
                                      --num_epoch 200 \
                                      --llm_pretrained $llm_pretrained \
                                      --llm_pretrained_task $llm_pretrained_task \
                                      --seed $SEED
fi