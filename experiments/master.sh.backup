# #########################cmp with baseline#########################
# model_name=meta-llama/Llama-3.1-8B
# model_name1="${model_name//\//-}"
# for SEED in 42; do
#   for WORKLOAD in "tpch" "tpcds" "job" "syn" "stats"; do
#         bash scripts/run_baseline.sh $WORKLOAD $WORKLOAD 1.0 $SEED
#         bash scripts/run_llm_time.sh $WORKLOAD $WORKLOAD $train_ratio False $model_name $model_name1 $SEED
#   done
# done

# #########################train ratio#########################
# model_name=meta-llama/Llama-3.1-8B
# model_name1="${model_name//\//-}"
# for SEED in 42 43 44; do
#   for WORKLOAD in "tpch" "tpcds" "job" "syn" "stats"; do
#       for train_ratio in 0.2 0.4 0.6 0.8 1.0; do
#           bash scripts/run_llm_time.sh $WORKLOAD $WORKLOAD $train_ratio False $model_name $model_name1 $SEED
#           if [[ $WORKLOAD == "job" || $WORKLOAD == "syn" || $WORKLOAD == "stats" ]]; then
#               bash scripts/run_llm_card.sh $WORKLOAD $WORKLOAD $train_ratio False $model_name $model_name1 $SEED
#           fi
#       done
#   done
# done

#########################model size#########################
for SEED in 42 43 44; do
  for WORKLOAD in "tpch" "tpcds" "stats"; do
      # for model_name in "meta-llama/Llama-3.2-1B" "meta-llama/Llama-3.2-3B"; do
      for model_name in "meta-llama/Llama-3.2-1B" "meta-llama/Llama-3.2-3B" "meta-llama/Llama-3.1-8B" "meta-llama/Llama-3.1-70B"; do
          model_name1="${model_name//\//-}"
          if [[ $WORKLOAD == "stats" ]]; then
            bash scripts/run_llm_card.sh $WORKLOAD $WORKLOAD 1.0 False $model_name $model_name1 $SEED
          fi
          bash scripts/run_llm_time.sh $WORKLOAD $WORKLOAD 1.0 False $model_name $model_name1 $SEED
      done
  done
done

# #########################finetune#########################
# model_name=meta-llama/Llama-3.1-8B
# model_name1="${model_name//\//-}"
# for SEED in 42 43 44; do
#   for WORKLOAD in "tpch" "tpcds" "stats"; do        
#       if [[ $WORKLOAD == "stats" ]]; then
#           bash scripts/run_llm_card.sh $WORKLOAD $WORKLOAD 0.1 True $model_name $model_name1 $SEED
#       fi
#       bash scripts/run_llm_time.sh $WORKLOAD $WORKLOAD 0.1 True $model_name $model_name1 $SEED
#   done
# done

# #########################across workloads#########################
# model_name=meta-llama/Llama-3.1-8B
# model_name1="${model_name//\//-}"
# ALL_WORKLOADS="genome financial movielens geneea seznam tpc_h walmart airline carcinogenesis baseball imdb accidents ssb basketball employee fhnk consumer tournament credit hepatitis"
# WORKLOAD_TEST_OPTIONS="tpc_h synthetic job-light"

# for SEED in 42 43 44; do
#   for WORKLOAD_TEST in $WORKLOAD_TEST_OPTIONS; do
#     # build a string of "the WORKLOADS_TRAIN"
#     WORKLOADS_TRAIN=""
#     for o in $ALL_WORKLOADS; do
#       if [[ $o != $WORKLOAD_TEST ]]; then
#         # Remove imdb from training if testing on synthetic or job-light
#         if [[ ($WORKLOAD_TEST == "synthetic" || $WORKLOAD_TEST == "job-light") && $o == "imdb" ]]; then
#           continue
#         fi
#         WORKLOADS_TRAIN="$WORKLOADS_TRAIN $o"
#       fi
#     done
#     # strip leading space
#     WORKLOADS_TRAIN=${WORKLOADS_TRAIN# }

#     echo "Testing on: $WORKLOAD_TEST"
#     echo "Training on: $WORKLOADS_TRAIN"
#     bash scripts/run_llm_time.sh "$WORKLOADS_TRAIN" "$WORKLOAD_TEST" 1.0 False $model_name $model_name1 $SEED
#   done
# done

# #########################finetune across workloads#########################
# model_name=meta-llama/Llama-3.1-8B
# model_name1="${model_name//\//-}"
# ALL_WORKLOADS="genome financial movielens geneea seznam tpc_h walmart airline carcinogenesis baseball imdb accidents ssb basketball employee fhnk consumer tournament credit hepatitis"
# # WORKLOAD_TEST_OPTIONS="tpc_h synthetic job-light"
# WORKLOAD_TEST_OPTIONS="tpc_h synthetic"

# for SEED in 42; do
# # for SEED in 42 43 44; do
#   for WORKLOAD_TEST in $WORKLOAD_TEST_OPTIONS; do
#     # build a string of "the WORKLOADS_TRAIN"
#     WORKLOADS_TRAIN=""
#     for o in $ALL_WORKLOADS; do
#       if [[ $o != $WORKLOAD_TEST ]]; then
#         # Remove imdb from training if testing on synthetic or job-light
#         if [[ ($WORKLOAD_TEST == "synthetic" || $WORKLOAD_TEST == "job-light") && $o == "imdb" ]]; then
#           continue
#         fi
#         WORKLOADS_TRAIN="$WORKLOADS_TRAIN $o"
#       fi
#     done
#     # strip leading space
#     WORKLOADS_TRAIN=${WORKLOADS_TRAIN# }

#     echo "Testing on: $WORKLOAD_TEST"
#     echo "Training on: $WORKLOADS_TRAIN"
#     bash scripts/run_llm_time.sh "$WORKLOADS_TRAIN" "$WORKLOAD_TEST" 0.1 True $model_name $model_name1 $SEED
#   done
# done