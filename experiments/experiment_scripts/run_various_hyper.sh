embed_sizes=(1000 2100 3100 4100 8200)

hid_units_1000=(128 256 512)
batch_sizes_1000=(32 64 128)

hid_units_2100=(256 512 1024)
batch_sizes_2100=(64 128 256)

hid_units_3100=(512 1024 2048)
batch_sizes_3100=(128 256 512)

hid_units_4100=(512 1024 2048)
batch_sizes_4100=(128 256 512)

hid_units_8200=(1024 2048 4096)
batch_sizes_8200=(256 512 1024)

export BUCKETIZE_INPUT="separate"
#########################model size#########################
for SEED in 42; do
# for SEED in 42 43 44; do
  for WORKLOAD in "stats"; do
      # for model_name in "meta-llama/Llama-3.1-70B"; do
      for model_name in "meta-llama/Llama-3.2-3B" "meta-llama/Llama-3.1-8B" "meta-llama/Llama-3.1-70B"; do
          model_name1="${model_name//\//-}"
          for embed_size in "${embed_sizes[@]}"; do
            hid_units_arr="hid_units_${embed_size}[@]"
            batch_sizes_arr="batch_sizes_${embed_size}[@]"

            for hid_units in "${!hid_units_arr}"; do
              for batch_size in "${!batch_sizes_arr}"; do
                echo "Running: bash experiment_scripts/core_scripts/run_llm_various.sh $WORKLOAD $WORKLOAD 1.0 False $model_name $model_name1 $SEED $embed_size $hid_units $batch_size"
                if [[ $WORKLOAD == "stats" ]]; then
                  bash experiment_scripts/core_scripts/run_llm_card_various.sh "$WORKLOAD" "$WORKLOAD" 1.0 False "$model_name" "$model_name1" $SEED $embed_size $hid_units $batch_size
                fi
                bash experiment_scripts/core_scripts/run_llm_time_various.sh "$WORKLOAD" "$WORKLOAD" 1.0 False "$model_name" "$model_name1" $SEED $embed_size $hid_units $batch_size

              done
            done
          done
      done
  done
done

