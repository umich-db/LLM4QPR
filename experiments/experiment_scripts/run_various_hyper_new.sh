# Check if required arguments are provided
if [ $# -lt 3 ]; then
    echo "Usage: $0 <embed_size> <seed> <model_name>"
    echo "Available embed_size options: 1000, 2100, 3100, 4100, 8200"
    echo "Example: $0 1000 42 \"meta-llama/Llama-3.1-8B\""
    exit 1
fi

embed_size=$1
SEED=$2
model_name=$3

# Validate embed_size
valid_sizes=(1000 2100 3100 4100 8200)
if [[ ! " ${valid_sizes[@]} " =~ " ${embed_size} " ]]; then
    echo "Error: Invalid embed_size. Available options: 1000, 2100, 3100, 4100, 8200"
    exit 1
fi

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
model_name1="${model_name//\//-}"
hid_units_arr="hid_units_${embed_size}[@]"
batch_sizes_arr="batch_sizes_${embed_size}[@]"

for WORKLOAD in "stats"; do
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

