
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

# PRICE model path: prefer bundled copy inside LLM4QPR, fall back to /root/PRICE
SCRIPT_DIR_LLM="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
if [[ -z "${PRICE_MODEL_PATH:-}" ]]; then
  if [[ -f "$SCRIPT_DIR_LLM/experiments/price_statistics/model/model_params.pth" ]]; then
    PRICE_MODEL_PATH="$SCRIPT_DIR_LLM/experiments/price_statistics/model/model_params.pth"
  else
    PRICE_MODEL_PATH="/root/PRICE/results/model_params.pth"
  fi
fi

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
# IMDB-based workloads (job, syn, job_full, jobm) map to 'imdb' so finetuned
# model files match the prefix produced by utilsTrain.py's _CANONICAL_MAP.
_canonical_wl() {
  case "$1" in
    job|syn|job_full|jobm) echo "imdb" ;;
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

# PRICE_B (original PRICE: equi-join + col-op-literal only) — set once
PRICE_B_ARG=""
PRICE_B_SUFFIX=""
if [[ "$PRICE_B" == "true" || "$PRICE_B" == "True" ]]; then
  PRICE_B_ARG="--price_b"
  PRICE_B_SUFFIX="_priceB"
fi

# PRICE_N family (parsing / filter / fanout / pairwise + shorthand --price_n)
# Suffix order mirrors train._price_path_suffix to keep filenames consistent.
PRICE_N_ARGS=""
PRICE_N_SUFFIX=""
if [[ "${PRICE_N:-}" == "true" || "${PRICE_N:-}" == "True" ]]; then
  PRICE_N_ARGS="$PRICE_N_ARGS --price_n"
  # --price_n shorthand sets all four sub-flags; train._price_path_suffix
  # collapses that into a single "priceN" token (filename length).
  PRICE_N_SUFFIX="${PRICE_N_SUFFIX}_priceN"
else
  if [[ "${PRICE_N_FILTER:-}" == "true" || "${PRICE_N_FILTER:-}" == "True" ]]; then
    PRICE_N_ARGS="$PRICE_N_ARGS --price_n_filter"
    PRICE_N_SUFFIX="${PRICE_N_SUFFIX}_priceNflt"
  fi
  if [[ "${PRICE_N_FANOUT:-}" == "true" || "${PRICE_N_FANOUT:-}" == "True" ]]; then
    PRICE_N_ARGS="$PRICE_N_ARGS --price_n_fanout"
    PRICE_N_SUFFIX="${PRICE_N_SUFFIX}_priceNfan"
  fi
  if [[ "${PRICE_N_PAIRWISE:-}" == "true" || "${PRICE_N_PAIRWISE:-}" == "True" ]]; then
    PRICE_N_ARGS="$PRICE_N_ARGS --price_n_pairwise"
    PRICE_N_SUFFIX="${PRICE_N_SUFFIX}_priceNpw"
  fi
  if [[ "${PRICE_N_PARSING:-}" == "true" || "${PRICE_N_PARSING:-}" == "True" ]]; then
    PRICE_N_ARGS="$PRICE_N_ARGS --price_n_parsing"
    PRICE_N_SUFFIX="${PRICE_N_SUFFIX}_priceNprs"
  fi
fi
if [[ "${PRICE_N_OR:-}" == "true" || "${PRICE_N_OR:-}" == "True" ]]; then
  PRICE_N_ARGS="$PRICE_N_ARGS --price_n_or"
  PRICE_N_SUFFIX="${PRICE_N_SUFFIX}_priceNor"
fi
if [[ -n "${PRICE_N_OR_MAX_CLAUSES:-}" ]] && [[ "$PRICE_N_OR_MAX_CLAUSES" -ne 16 ]]; then
  PRICE_N_ARGS="$PRICE_N_ARGS --price_n_or_max_clauses $PRICE_N_OR_MAX_CLAUSES"
  PRICE_N_SUFFIX="${PRICE_N_SUFFIX}_mc${PRICE_N_OR_MAX_CLAUSES}"
fi
# Stat-core ↔ QRT cross-attn (--use_qrt_cross_attn). Env var passthrough.
if [[ "${USE_QRT_CROSS_ATTN:-}" == "true" || "${USE_QRT_CROSS_ATTN:-}" == "True" ]]; then
  PRICE_N_ARGS="$PRICE_N_ARGS --use_qrt_cross_attn"
  PRICE_N_SUFFIX="${PRICE_N_SUFFIX}_qrt"
fi

# --no_llm_residual: PRICE-only model; suffix lives on the architecture side.
NO_LLM_RESIDUAL_ARG=""
NO_LLM_RESIDUAL_SUFFIX=""
if [[ "${NO_LLM_RESIDUAL:-}" == "true" || "${NO_LLM_RESIDUAL:-}" == "True" ]]; then
  NO_LLM_RESIDUAL_ARG="--no_llm_residual"
  NO_LLM_RESIDUAL_SUFFIX="_noLLMres"
fi

# --no_or_transformer: ablate the OR Transformer (3rd encoder stage) while
# keeping PRICE_N's other components.  Used to isolate the OR Transformer's
# contribution from the new token shapes.
NO_OR_TRANSFORMER_ARG=""
NO_OR_TRANSFORMER_SUFFIX=""
if [[ "${NO_OR_TRANSFORMER:-}" == "true" || "${NO_OR_TRANSFORMER:-}" == "True" ]]; then
  NO_OR_TRANSFORMER_ARG="--no_or_transformer"
  NO_OR_TRANSFORMER_SUFFIX="_noORt"
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
# PRICE ffn_ratio — set once, used by all PRICE sections
PRICE_FFN_RATIO_ARG=""
PRICE_FFN_RATIO_SUFFIX=""
if [[ -n "${PRICE_FFN_RATIO:-}" ]] && [[ "$PRICE_FFN_RATIO" != "4" ]]; then
  PRICE_FFN_RATIO_ARG="--price_ffn_ratio $PRICE_FFN_RATIO"
  PRICE_FFN_RATIO_SUFFIX="_ffn${PRICE_FFN_RATIO}"
fi

# OR-Transformer config (only meaningful under --price_n_or). Env var → CLI
# flag passthrough; defaults are set in utilsTrain.py (n_layers=1, n_heads=4,
# ffn_ratio=1.0). Set OR_N_LAYERS / OR_N_HEADS / OR_FFN_RATIO to override.
OR_N_LAYERS_ARG=""
if [[ -n "${OR_N_LAYERS:-}" ]]; then
  OR_N_LAYERS_ARG="--or_n_layers $OR_N_LAYERS"
fi
OR_N_HEADS_ARG=""
if [[ -n "${OR_N_HEADS:-}" ]]; then
  OR_N_HEADS_ARG="--or_n_heads $OR_N_HEADS"
fi
OR_FFN_RATIO_ARG=""
if [[ -n "${OR_FFN_RATIO:-}" ]]; then
  OR_FFN_RATIO_ARG="--or_ffn_ratio $OR_FFN_RATIO"
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
# Reverse cross-attention — set once, used by ReverseCrossAttentionJoint section
REV_CROSS_ATTN_ARG=""
REV_CROSS_ATTN_SUFFIX=""
if [[ "$finetune" == "ReverseCrossAttentionJoint" ]]; then
  REV_CROSS_ATTN_ARG="--use_reverse_cross_attention"
  REV_CROSS_ATTN_SUFFIX="_revCrossAttn"
fi
if [[ -n "${N_CROSS_LAYERS:-}" ]] && [[ "$N_CROSS_LAYERS" -ne 2 ]]; then
  N_CROSS_LAYERS_ARG="--n_cross_layers $N_CROSS_LAYERS"
  N_CROSS_LAYERS_SUFFIX="_cx${N_CROSS_LAYERS}"
fi
CROSS_ATTN_LR_ARG=""
if [[ -n "${CROSS_ATTN_LR:-}" ]]; then
  CROSS_ATTN_LR_ARG="--cross_attn_lr $CROSS_ATTN_LR"
fi

# --cross_attn_dropout: dropout inside CrossAttentionBlock / ReverseCrossAttentionBlock.
# Default 0.1; raise to 0.3-0.5 to fight cross-attn overfitting on small data.
# Suffix _drop{X.X} only emits when non-default (matches train._arch_path_suffix).
CROSS_ATTN_DROPOUT_ARG=""
CROSS_ATTN_DROPOUT_SUFFIX=""
if [[ -n "${CROSS_ATTN_DROPOUT:-}" ]] && [[ "$CROSS_ATTN_DROPOUT" != "0.1" ]]; then
  CROSS_ATTN_DROPOUT_ARG="--cross_attn_dropout $CROSS_ATTN_DROPOUT"
  CROSS_ATTN_DROPOUT_SUFFIX="_drop${CROSS_ATTN_DROPOUT}"
fi

# --cross_attn_gate: ReZero-style learnable scalar gates around each cross-attn
# sub-layer, init at 0 → block is identity at start; training only opens gates
# when cross-attn helps. Adds ~2N scalar params per N cross-attn layers.
CROSS_ATTN_GATE_ARG=""
CROSS_ATTN_GATE_SUFFIX=""
if [[ "${CROSS_ATTN_GATE:-}" == "true" || "${CROSS_ATTN_GATE:-}" == "True" ]]; then
  CROSS_ATTN_GATE_ARG="--cross_attn_gate"
  CROSS_ATTN_GATE_SUFFIX="_gate"
fi

# --residual_pred: ResNet additive prediction. pred = base_mlp(LLM) + delta_mlp(concat).
# delta_mlp's final layer is zero-init so init pred = LLM-only prediction (mode 2).
RESIDUAL_PRED_ARG=""
RESIDUAL_PRED_SUFFIX=""
if [[ "${RESIDUAL_PRED:-}" == "true" || "${RESIDUAL_PRED:-}" == "True" ]]; then
  RESIDUAL_PRED_ARG="--residual_pred"
  RESIDUAL_PRED_SUFFIX="_resPred"
fi

# --delta_bound: tanh-bounded delta when residual_pred is on. 0 = unbounded.
DELTA_BOUND_ARG=""
DELTA_BOUND_SUFFIX=""
if [[ -n "${DELTA_BOUND:-}" && "${DELTA_BOUND}" != "0" && "${DELTA_BOUND}" != "0.0" ]]; then
  DELTA_BOUND_ARG="--delta_bound ${DELTA_BOUND}"
  DELTA_BOUND_SUFFIX="_db${DELTA_BOUND}"
fi

# --price_emb_dropout: element-wise dropout on price_emb at training time.
PRICE_EMB_DROPOUT_ARG=""
PRICE_EMB_DROPOUT_SUFFIX=""
if [[ -n "${PRICE_EMB_DROPOUT:-}" && "${PRICE_EMB_DROPOUT}" != "0" && "${PRICE_EMB_DROPOUT}" != "0.0" ]]; then
  PRICE_EMB_DROPOUT_ARG="--price_emb_dropout ${PRICE_EMB_DROPOUT}"
  PRICE_EMB_DROPOUT_SUFFIX="_peDrop${PRICE_EMB_DROPOUT}"
fi

INIT_LLM_FROM_ARG=""
INIT_LLM_FROM_SUFFIX=""
if [[ -n "${INIT_LLM_FROM:-}" ]]; then
  INIT_LLM_FROM_ARG="--init_llm_from ${INIT_LLM_FROM}"
  INIT_LLM_FROM_SUFFIX="_initLLM"
fi

DETERMINISTIC_ARG=""
DETERMINISTIC_SUFFIX=""
if [[ "${DETERMINISTIC:-}" == "true" ]]; then
  DETERMINISTIC_ARG="--deterministic_algorithms"
  DETERMINISTIC_SUFFIX="_det"
fi

NO_RETRAIN_MLP_ARG=""
if [[ "${NO_RETRAIN_MLP:-}" == "true" ]]; then
  NO_RETRAIN_MLP_ARG="--no_retrain_mlp_at_inference"
fi

CROSS_ATTN_NOOP_ARG=""
CROSS_ATTN_NOOP_SUFFIX=""
if [[ "${CROSS_ATTN_NOOP:-}" == "true" ]]; then
  CROSS_ATTN_NOOP_ARG="--cross_attn_noop"
  CROSS_ATTN_NOOP_SUFFIX="_noop"
fi

FORCE_INFLATE_ARG=""
FORCE_INFLATE_SUFFIX=""
if [[ "${FORCE_INFLATE:-}" == "true" ]]; then
  FORCE_INFLATE_ARG="--force_inflate"
  FORCE_INFLATE_SUFFIX="_finfl"
fi

PRICE_OUTPUT_DIM_ARG=""
PRICE_OUTPUT_DIM_SUFFIX=""
if [[ -n "${PRICE_OUTPUT_DIM:-}" && "${PRICE_OUTPUT_DIM}" != "0" ]]; then
  PRICE_OUTPUT_DIM_ARG="--price_output_dim ${PRICE_OUTPUT_DIM}"
  PRICE_OUTPUT_DIM_SUFFIX="_pod${PRICE_OUTPUT_DIM}"
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
INFLATE_PRICE_FLAG=""
INFLATE_PRICE_SUFFIX=""
if [[ "${INFLATE_PRICE:-}" == "true" ]]; then
  INFLATE_PRICE_FLAG="--inflate_price"
  INFLATE_PRICE_SUFFIX="_inflatePRICE"
fi

EARLY_STOP_ARG=""
if [[ -n "${EARLY_STOP_PATIENCE:-}" ]] && [[ "$EARLY_STOP_PATIENCE" -gt 0 ]]; then
  EARLY_STOP_ARG="--early_stop_patience $EARLY_STOP_PATIENCE"
  if [[ -n "${EARLY_STOP_AFTER_EPOCH:-}" ]] && [[ "$EARLY_STOP_AFTER_EPOCH" -gt 0 ]]; then
    EARLY_STOP_ARG="$EARLY_STOP_ARG --early_stop_after_epoch $EARLY_STOP_AFTER_EPOCH"
  fi
fi

EMBED_BS_ARG=""
if [[ -n "${EMBED_BATCH_SIZE:-}" ]]; then
  EMBED_BS_ARG="--embed_batch_size $EMBED_BATCH_SIZE"
fi
FREEZE_LLM_ARG=""
FREEZE_LLM_SUFFIX=""
if [[ -n "${FREEZE_LLM_UNTIL_EPOCH:-}" ]] && [[ "$FREEZE_LLM_UNTIL_EPOCH" -gt 0 ]]; then
  FREEZE_LLM_ARG="--freeze_llm_until_epoch $FREEZE_LLM_UNTIL_EPOCH"
  FREEZE_LLM_SUFFIX="_frzLLM${FREEZE_LLM_UNTIL_EPOCH}"
fi
FREEZE_ODD_ARG=""
FREEZE_ODD_SUFFIX=""
if [[ -n "${FREEZE_ODD_BLOCKS_UNTIL_EPOCH:-}" ]] && [[ "$FREEZE_ODD_BLOCKS_UNTIL_EPOCH" -gt 0 ]]; then
  FREEZE_ODD_ARG="--freeze_odd_blocks_until_epoch $FREEZE_ODD_BLOCKS_UNTIL_EPOCH"
  FREEZE_ODD_SUFFIX="_frzOdd${FREEZE_ODD_BLOCKS_UNTIL_EPOCH}"
fi
FREEZE_ALL_ARG=""
FREEZE_ALL_SUFFIX=""
if [[ -n "${FREEZE_ALL_BLOCKS_UNTIL_EPOCH:-}" ]] && [[ "$FREEZE_ALL_BLOCKS_UNTIL_EPOCH" -gt 0 ]]; then
  FREEZE_ALL_ARG="--freeze_all_blocks_until_epoch $FREEZE_ALL_BLOCKS_UNTIL_EPOCH"
  FREEZE_ALL_SUFFIX="_frzAll${FREEZE_ALL_BLOCKS_UNTIL_EPOCH}"
fi
FREEZE_EVEN_ARG=""
FREEZE_EVEN_SUFFIX=""
if [[ -n "${FREEZE_EVEN_BLOCKS_UNTIL_EPOCH:-}" ]] && [[ "$FREEZE_EVEN_BLOCKS_UNTIL_EPOCH" -gt 0 ]]; then
  FREEZE_EVEN_ARG="--freeze_even_blocks_until_epoch $FREEZE_EVEN_BLOCKS_UNTIL_EPOCH"
  FREEZE_EVEN_SUFFIX="_frzEven${FREEZE_EVEN_BLOCKS_UNTIL_EPOCH}"
fi
MLP_BEFORE_CA_ARG=""
MLP_BEFORE_CA_SUFFIX=""
if [[ "${MLP_BEFORE_CROSS_ATTN:-}" == "true" ]]; then
  MLP_BEFORE_CA_ARG="--mlp_before_cross_attn"
  MLP_BEFORE_CA_SUFFIX="_mlpFirst"
fi
# EVAL_FROZEN_BLOCKS env is read directly by trainer.py (no train.py flag); this
# only adds a filename suffix so the eval-frozen verification run is distinct.
EVAL_FRZ_SUFFIX=""
if [[ "${EVAL_FROZEN_BLOCKS:-}" == "1" ]]; then
  EVAL_FRZ_SUFFIX="_evalFrz"
fi
# RESEED_BEFORE_TRAIN env is read directly by trainer.py; suffix only for a distinct file.
RESEED_SUFFIX=""
if [[ "${RESEED_BEFORE_TRAIN:-}" == "1" ]]; then
  RESEED_SUFFIX="_reseed"
fi
# LLM_POOL_ALL_WINDOWS env read directly by the model; suffix marks the bug-fix run.
POOL_ALL_SUFFIX=""
if [[ "${LLM_POOL_ALL_WINDOWS:-}" == "1" ]]; then
  POOL_ALL_SUFFIX="_poolAll"
fi
# --unified_window_pool (also via UNIFIED_WINDOW_POOL=1 env); suffix for a distinct file.
UNIF_POOL_SUFFIX=""
if [[ "${UNIFIED_WINDOW_POOL:-}" == "1" ]]; then
  UNIF_POOL_SUFFIX="_unifPool"
fi
PRICE_WARMUP_ARG=""
PRICE_WARMUP_SUFFIX=""
if [[ -n "${PRICE_WARMUP_EPOCHS:-}" ]] && [[ "$PRICE_WARMUP_EPOCHS" -ne 0 ]]; then
  PRICE_WARMUP_ARG="--price_warmup_epochs $PRICE_WARMUP_EPOCHS"
  if [[ "${PRICE_RANDOM_INIT:-}" == "true" ]]; then
    PRICE_WARMUP_SUFFIX="_pwm${PRICE_WARMUP_EPOCHS}"
  fi
fi
# Pass --price_lr through to inference invocations too. Finetune blocks already
# inline `--price_lr $price_lr` from $PRICE_LR_DEFAULT, so they don't need this
# variable; inference blocks (which never had a price_lr fallback) do.
PRICE_LR_ARG=""
PRICE_LR_SUFFIX=""
if [[ -n "${PRICE_LR:-}" ]]; then
  PRICE_LR_ARG="--price_lr $PRICE_LR"
  # Mirror python's _arch_path_suffix: pLR{X:g} only when random_init is on
  # AND price_lr differs from the random-init default 1e-3.
  if [[ "${PRICE_RANDOM_INIT:-}" == "true" ]] && \
     ! awk -v v="$PRICE_LR" 'BEGIN { exit !(v+0 == 0.001) }'; then
    _plr_g="$(awk -v v="$PRICE_LR" 'BEGIN{printf "%g", v+0}')"
    PRICE_LR_SUFFIX="_pLR${_plr_g}"
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
        statsOutput) SUFFIX_PARTS+=("stOut") ;;  # spark-only: strips the planner row/byte estimates block
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

# Subdir tag (e.g. "model_selection") inserted into log/result/weight paths.
# When set, files go under .../<existing_path>/${SUBDIR_TAG}/
SUBDIR_PART=""
SUBDIR_ARG=""
if [[ -n "${SUBDIR_TAG:-}" ]]; then
  SUBDIR_PART="/${SUBDIR_TAG}"
  SUBDIR_ARG="--subdir_tag ${SUBDIR_TAG}"
fi

if [ "$finetune" == "False" ]; then
  #########################inference: no pre-train#########################
  algo=llm
  embed_size=${EMBED_SIZE:-1000}
  hid_units=2048
  lr=${LLM_LR:-0.0001}
  batch_size=64     

  echo "inference: no pre-train"
  
  setup_args_and_suffixes
  
  python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                      --output_dir_qerror ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_pretrained-None_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${DOWNSTREAM_SUFFIX}${REMOVED_FIELDS_SUFFIX}${CONCAT_TRUE_SUFFIX}${STATS_SUFFIX}${MAX_QUERIES_SUFFIX}_seed${SEED}.csv \
                                      --output_dir_abs ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_pretrained-None_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${DOWNSTREAM_SUFFIX}${REMOVED_FIELDS_SUFFIX}${CONCAT_TRUE_SUFFIX}${STATS_SUFFIX}${MAX_QUERIES_SUFFIX}_seed${SEED}_abs.txt \
                                      --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_pretrained-None_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${DOWNSTREAM_SUFFIX}${REMOVED_FIELDS_SUFFIX}${CONCAT_TRUE_SUFFIX}${STATS_SUFFIX}${MAX_QUERIES_SUFFIX}_seed${SEED}.log \
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
                                      $PRICE_M_ARG $PRICE_S_ARG $PRICE_B_ARG $PRICE_N_ARGS $NO_LLM_RESIDUAL_ARG $NO_OR_TRANSFORMER_ARG \
                                      $MAX_QUERIES_ARG \
                                      $EMBED_BS_ARG
fi

if [ "$finetune" == "True" ]; then
  #########################finetune#########################
  algo=llm_finetune
  hid_units=2048
  lr=${LLM_LR:-0.0001}
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
    local model_file="finetuned_models/${DB_ENGINE}${SUBDIR_PART}/${CANONICAL_TRAIN_HYPHEN}_time_${mode}_${model_name1}_b${FT_BATCH_SIZE}${stats_suffix}_llm.pt"
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
                                          --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_last_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${CONCAT_TRUE_SUFFIX}${STATS_SUFFIX}.log \
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
                                          $PRICE_M_ARG $PRICE_S_ARG $PRICE_B_ARG $PRICE_N_ARGS $NO_LLM_RESIDUAL_ARG $NO_OR_TRANSFORMER_ARG \
                                          $MAX_QUERIES_ARG \
                                          $EARLY_STOP_ARG
    fi
  fi

  if [[ "$RUN_LORA" == "true" ]]; then
    llm_mode=lora
    echo "finetune: lora"

    # ALWAYS invoke train.py for mode 2 so the jointMLP test eval CSV gets
    # emitted on every (db, workload) cell. When the canonical-prefix LLM
    # weights already exist (e.g. {syn, job, job_full} all canonicalise to
    # 'imdb', so the second and third runs in the imdb family hit a cached
    # weight file), pass --skip_train_load_finetuned_weights — train.py's
    # mode-2 branch then loads the saved LLM+MLP and runs the test eval
    # without retraining.
    SKIP_TRAIN_ARG_FT=""
    if check_model_exists "lora"; then
      echo "    Loading cached weights + emitting jointMLP test-eval CSV..."
      SKIP_TRAIN_ARG_FT="--skip_train_load_finetuned_weights"
    else
      echo "    Model not found, starting finetuning..."
    fi
    setup_args_and_suffixes

    python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                        --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_lora_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${CONCAT_TRUE_SUFFIX}${STATS_SUFFIX}_seed${SEED}.log \
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
                                        $PRICE_M_ARG $PRICE_S_ARG $PRICE_B_ARG $PRICE_N_ARGS $NO_LLM_RESIDUAL_ARG $NO_OR_TRANSFORMER_ARG \
                                        $MAX_QUERIES_ARG \
                                        $EARLY_STOP_ARG \
                                        $SKIP_TRAIN_ARG_FT
  fi

  #########################inference: pre-trained#########################
  algo=llm
  embed_size=${EMBED_SIZE:-1000}
  hid_units=2048
  lr=${LLM_LR:-0.0001}
  batch_size=64     

  if [[ "$RUN_LAST" == "true" ]]; then
    llm_pretrained=last
    echo "inference: pre-trained last"
    
    setup_args_and_suffixes
    
    python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                        --output_dir_qerror ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_pretrained-${llm_pretrained}_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${DOWNSTREAM_SUFFIX}${REMOVED_FIELDS_SUFFIX}${CONCAT_TRUE_SUFFIX}${STATS_SUFFIX}_ftb${FT_BATCH_SIZE}_seed${SEED}.csv \
                                        --output_dir_abs ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_pretrained-${llm_pretrained}_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${DOWNSTREAM_SUFFIX}${REMOVED_FIELDS_SUFFIX}${CONCAT_TRUE_SUFFIX}${STATS_SUFFIX}_ftb${FT_BATCH_SIZE}_seed${SEED}_abs.txt \
                                        --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_pretrained-${llm_pretrained}_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${DOWNSTREAM_SUFFIX}${REMOVED_FIELDS_SUFFIX}${CONCAT_TRUE_SUFFIX}${STATS_SUFFIX}_ftb${FT_BATCH_SIZE}_seed${SEED}.log \
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
                                        $PRICE_M_ARG $PRICE_S_ARG $PRICE_B_ARG $PRICE_N_ARGS $NO_LLM_RESIDUAL_ARG $NO_OR_TRANSFORMER_ARG \
                                        $EARLY_STOP_ARG
  fi

  if [[ "$RUN_LORA" == "true" ]]; then
    llm_pretrained=lora
    echo "inference: pre-trained lora"

    setup_args_and_suffixes

    python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                        --output_dir_qerror ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_pretrained-${llm_pretrained}_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${DOWNSTREAM_SUFFIX}${REMOVED_FIELDS_SUFFIX}${CONCAT_TRUE_SUFFIX}${STATS_SUFFIX}_ftb${FT_BATCH_SIZE}_seed${SEED}.csv \
                                        --output_dir_abs ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_pretrained-${llm_pretrained}_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${DOWNSTREAM_SUFFIX}${REMOVED_FIELDS_SUFFIX}${CONCAT_TRUE_SUFFIX}${STATS_SUFFIX}_ftb${FT_BATCH_SIZE}_seed${SEED}_abs.txt \
                                        --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_pretrained-${llm_pretrained}_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${DOWNSTREAM_SUFFIX}${REMOVED_FIELDS_SUFFIX}${CONCAT_TRUE_SUFFIX}${STATS_SUFFIX}_ftb${FT_BATCH_SIZE}_seed${SEED}.log \
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
                                        $PRICE_M_ARG $PRICE_S_ARG $PRICE_B_ARG $PRICE_N_ARGS $NO_LLM_RESIDUAL_ARG $NO_OR_TRANSFORMER_ARG \
                                        $EARLY_STOP_ARG
  fi
fi

if [ "$finetune" == "JointPrice" ]; then
  PRICE_MODEL_PATH=${PRICE_MODEL_PATH:-"$SCRIPT_DIR_LLM/experiments/price_statistics/model/model_params.pth"}
  PRICE_BIN_SIZE=${PRICE_BIN_SIZE:-40}

  # Check if finetuned JointPrice weights already exist
  # Seedless joint-finetune weight prefix — must match train.py:1273.
  # Per-seed JointPrice weights — distinct SEED → distinct finetune artifact
  # (matches train.py per-seed save). Different seeds re-finetune from scratch.
  JOINT_PRICE_PREFIX="finetuned_models/${DB_ENGINE}${SUBDIR_PART}/${CANONICAL_TRAIN_HYPHEN}_time_lora_${model_name1}_b${FT_BATCH_SIZE}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_N_SUFFIX}_llm_price${NO_LLM_RESIDUAL_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${PRICE_FFN_RATIO_SUFFIX}${EPOCH_SUFFIX}_seed${SEED}"
  algo=llm_price_finetune
  hid_units=2048
  lr=${LLM_LR:-0.0001}
  price_lr=${PRICE_LR:-$PRICE_LR_DEFAULT}
  batch_size=$FT_BATCH_SIZE
  grad_accum_steps=${GRAD_ACCUM_STEPS:-1}

  GRAD_ACCUM_ARG=""
  if [[ "$grad_accum_steps" -gt 1 ]]; then
    GRAD_ACCUM_ARG="--grad_accum_steps $grad_accum_steps"
  fi

  if [ -f "${JOINT_PRICE_PREFIX}_llm.pt" ] && [ -f "${JOINT_PRICE_PREFIX}_price.pt" ]; then
    echo "Finetuned JointPrice weights already exist; loading + emitting finetune-phase eval CSV:"
    echo "  LLM:   ${JOINT_PRICE_PREFIX}_llm.pt"
    echo "  PRICE: ${JOINT_PRICE_PREFIX}_price.pt"
    SKIP_TRAIN_ARG="--skip_train_load_finetuned_weights"
  else
    echo "Joint LLM+PRICE finetune"
    SKIP_TRAIN_ARG=""
    if [[ "$grad_accum_steps" -gt 1 ]]; then
      echo "  Gradient accumulation: ${grad_accum_steps} steps (effective batch = ${batch_size} * ${grad_accum_steps})"
    fi
  fi

  setup_args_and_suffixes

  python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                      --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_lora_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_N_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${PRICE_FFN_RATIO_SUFFIX}${EPOCH_SUFFIX}_seed${SEED}.log \
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
                                      $PRICE_M_ARG $PRICE_S_ARG $PRICE_B_ARG $PRICE_N_ARGS $NO_LLM_RESIDUAL_ARG $NO_OR_TRANSFORMER_ARG \
                                      $PRICE_RANDOM_INIT_FLAG \
                                      $CHECKPOINT_INTERVAL_ARG \
                                      $GRAD_ACCUM_ARG \
                                      $PRICE_N_LAYERS_ARG \
                                      $PRICE_FFN_RATIO_ARG $OR_N_LAYERS_ARG $OR_N_HEADS_ARG $OR_FFN_RATIO_ARG \
                                      $EARLY_STOP_ARG \
                                      $FREEZE_LLM_ARG $FREEZE_ODD_ARG $FREEZE_ALL_ARG $FREEZE_EVEN_ARG $MLP_BEFORE_CA_ARG \
                                      $PRICE_WARMUP_ARG \
                                      $PRICE_LR_ARG \
                                      $SUBDIR_ARG \
                                      $SKIP_TRAIN_ARG

  #########################inference: pre-trained JointPrice#########################
  algo=llm_price
  embed_size=${EMBED_SIZE:-1000}
  hid_units=2048
  lr=${LLM_LR:-0.0001}
  batch_size=64

  echo "inference: pre-trained JointPrice"

  setup_args_and_suffixes

  python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                      --output_dir_qerror ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_pretrained-lora_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_N_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${PRICE_FFN_RATIO_SUFFIX}${FREEZE_LLM_SUFFIX}${FREEZE_ODD_SUFFIX}${FREEZE_ALL_SUFFIX}${FREEZE_EVEN_SUFFIX}${MLP_BEFORE_CA_SUFFIX}${EVAL_FRZ_SUFFIX}${RESEED_SUFFIX}${POOL_ALL_SUFFIX}${UNIF_POOL_SUFFIX}${PRICE_WARMUP_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}_seed${SEED}.csv \
                                      --output_dir_abs ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_pretrained-lora_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_N_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${PRICE_FFN_RATIO_SUFFIX}${FREEZE_LLM_SUFFIX}${FREEZE_ODD_SUFFIX}${FREEZE_ALL_SUFFIX}${FREEZE_EVEN_SUFFIX}${MLP_BEFORE_CA_SUFFIX}${EVAL_FRZ_SUFFIX}${RESEED_SUFFIX}${POOL_ALL_SUFFIX}${UNIF_POOL_SUFFIX}${PRICE_WARMUP_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}_seed${SEED}_abs.txt \
                                      --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_pretrained-lora_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_N_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${PRICE_FFN_RATIO_SUFFIX}${FREEZE_LLM_SUFFIX}${FREEZE_ODD_SUFFIX}${FREEZE_ALL_SUFFIX}${FREEZE_EVEN_SUFFIX}${MLP_BEFORE_CA_SUFFIX}${EVAL_FRZ_SUFFIX}${RESEED_SUFFIX}${POOL_ALL_SUFFIX}${UNIF_POOL_SUFFIX}${PRICE_WARMUP_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}_seed${SEED}.log \
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
                                      $PRICE_M_ARG $PRICE_S_ARG $PRICE_B_ARG $PRICE_N_ARGS $NO_LLM_RESIDUAL_ARG $NO_OR_TRANSFORMER_ARG \
                                      $PRICE_RANDOM_INIT_FLAG \
                                      $PRICE_N_LAYERS_ARG \
                                      $PRICE_FFN_RATIO_ARG $OR_N_LAYERS_ARG $OR_N_HEADS_ARG $OR_FFN_RATIO_ARG \
                                      $EARLY_STOP_ARG \
                                      $FREEZE_LLM_ARG $FREEZE_ODD_ARG $FREEZE_ALL_ARG $FREEZE_EVEN_ARG $MLP_BEFORE_CA_ARG \
                                      $PRICE_WARMUP_ARG \
                                      $PRICE_LR_ARG \
                                      $SUBDIR_ARG
fi

if [ "$finetune" == "PriceNoFT" ]; then
  #########################Case 1: LLM+PRICE, no finetune#########################
  PRICE_MODEL_PATH=${PRICE_MODEL_PATH:-"$SCRIPT_DIR_LLM/experiments/price_statistics/model/model_params.pth"}
  PRICE_BIN_SIZE=${PRICE_BIN_SIZE:-40}

  algo=llm_price
  embed_size=${EMBED_SIZE:-1000}
  hid_units=2048
  lr=${LLM_LR:-0.0001}
  batch_size=64

  echo "LLM+PRICE inference: no finetune (PriceNoFT)"

  setup_args_and_suffixes

  python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                      --output_dir_qerror ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_pretrained-None_priceNoFT_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${PRICE_FFN_RATIO_SUFFIX}_seed${SEED}.csv \
                                      --output_dir_abs ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_pretrained-None_priceNoFT_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${PRICE_FFN_RATIO_SUFFIX}_seed${SEED}_abs.txt \
                                      --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_pretrained-None_priceNoFT_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${PRICE_FFN_RATIO_SUFFIX}_seed${SEED}.log \
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
                                      $PRICE_M_ARG $PRICE_S_ARG $PRICE_B_ARG $PRICE_N_ARGS $NO_LLM_RESIDUAL_ARG $NO_OR_TRANSFORMER_ARG \
                                      $PRICE_N_LAYERS_ARG \
                                      $PRICE_FFN_RATIO_ARG $OR_N_LAYERS_ARG $OR_N_HEADS_ARG $OR_FFN_RATIO_ARG \
                                      $PRICE_FFN_RATIO_ARG
fi

if [ "$finetune" == "PriceLLMOnly" ]; then
  #########################Case 2: LLM finetuned, PRICE frozen#########################
  PRICE_MODEL_PATH=${PRICE_MODEL_PATH:-"$SCRIPT_DIR_LLM/experiments/price_statistics/model/model_params.pth"}
  PRICE_BIN_SIZE=${PRICE_BIN_SIZE:-40}

  # Step 1: Finetune LLM (reuse existing llm_finetune logic)
  algo=llm_finetune
  hid_units=2048
  lr=${LLM_LR:-0.0001}
  batch_size=$FT_BATCH_SIZE

  check_model_exists_llm() {
    local mode=$1
    local model_file="finetuned_models/${DB_ENGINE}${SUBDIR_PART}/${CANONICAL_TRAIN_HYPHEN}_time_${mode}_${model_name1}_b${FT_BATCH_SIZE}_llm.pt"
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
                                        --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_lora_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}.log \
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
                                        $PRICE_M_ARG $PRICE_S_ARG $PRICE_B_ARG $PRICE_N_ARGS $NO_LLM_RESIDUAL_ARG $NO_OR_TRANSFORMER_ARG
  fi

  # Step 2: Inference with finetuned LLM + pretrained PRICE
  algo=llm_price
  embed_size=${EMBED_SIZE:-1000}
  hid_units=2048
  lr=${LLM_LR:-0.0001}
  batch_size=64

  echo "PriceLLMOnly: inference with finetuned LLM + pretrained PRICE"

  setup_args_and_suffixes

  python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                      --output_dir_qerror ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_pretrained-lora_priceLLMOnly_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${PRICE_FFN_RATIO_SUFFIX}_ftb${FT_BATCH_SIZE}_seed${SEED}.csv \
                                      --output_dir_abs ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_pretrained-lora_priceLLMOnly_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${PRICE_FFN_RATIO_SUFFIX}_ftb${FT_BATCH_SIZE}_seed${SEED}_abs.txt \
                                      --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_pretrained-lora_priceLLMOnly_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${PRICE_FFN_RATIO_SUFFIX}_ftb${FT_BATCH_SIZE}_seed${SEED}.log \
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
                                      $PRICE_M_ARG $PRICE_S_ARG $PRICE_B_ARG $PRICE_N_ARGS $NO_LLM_RESIDUAL_ARG $NO_OR_TRANSFORMER_ARG \
                                      $PRICE_N_LAYERS_ARG \
                                      $PRICE_FFN_RATIO_ARG $OR_N_LAYERS_ARG $OR_N_HEADS_ARG $OR_FFN_RATIO_ARG \
                                      $PRICE_FFN_RATIO_ARG
fi

if [ "$finetune" == "PricePRICEOnly" ]; then
  #########################Case 3: LLM frozen, PRICE finetuned on card#########################
  PRICE_MODEL_PATH=${PRICE_MODEL_PATH:-"$SCRIPT_DIR_LLM/experiments/price_statistics/model/model_params.pth"}
  PRICE_BIN_SIZE=${PRICE_BIN_SIZE:-40}

  # Step 1: Finetune PRICE on cardinality
  PRICE_SEPARATE_FILE="finetuned_models/${DB_ENGINE}${SUBDIR_PART}/${CANONICAL_TRAIN_HYPHEN}_card_b${FT_BATCH_SIZE}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${EPOCH_SUFFIX}_price_separate.pt"
  if [ -f "$PRICE_SEPARATE_FILE" ]; then
    echo "Separately finetuned PRICE weights already exist: $PRICE_SEPARATE_FILE"
  else
    algo=price_finetune
    price_lr=${PRICE_LR:-$PRICE_LR_DEFAULT}
    batch_size=$FT_BATCH_SIZE

    echo "PricePRICEOnly: finetune PRICE on cardinality"

    setup_args_and_suffixes

    python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                        --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_${DB_ENGINE}_${price_lr}_b${batch_size}_${model_name1}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${EPOCH_SUFFIX}.log \
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
                                        $PRICE_M_ARG $PRICE_S_ARG $PRICE_B_ARG $PRICE_N_ARGS $NO_LLM_RESIDUAL_ARG $NO_OR_TRANSFORMER_ARG \
                                        $PRICE_RANDOM_INIT_FLAG \
                                        $CHECKPOINT_INTERVAL_ARG
  fi

  # Step 2: Inference with frozen LLM + finetuned PRICE
  algo=llm_price
  embed_size=${EMBED_SIZE:-1000}
  hid_units=2048
  lr=${LLM_LR:-0.0001}
  batch_size=64

  echo "PricePRICEOnly: inference with frozen LLM + finetuned PRICE"

  setup_args_and_suffixes

  python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                      --output_dir_qerror ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_pretrained-None_pricePRICEOnly_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${FREEZE_LLM_SUFFIX}${FREEZE_ODD_SUFFIX}${FREEZE_ALL_SUFFIX}${FREEZE_EVEN_SUFFIX}${MLP_BEFORE_CA_SUFFIX}${EVAL_FRZ_SUFFIX}${RESEED_SUFFIX}${POOL_ALL_SUFFIX}${UNIF_POOL_SUFFIX}${PRICE_WARMUP_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}_seed${SEED}.csv \
                                      --output_dir_abs ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_pretrained-None_pricePRICEOnly_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${FREEZE_LLM_SUFFIX}${FREEZE_ODD_SUFFIX}${FREEZE_ALL_SUFFIX}${FREEZE_EVEN_SUFFIX}${MLP_BEFORE_CA_SUFFIX}${EVAL_FRZ_SUFFIX}${RESEED_SUFFIX}${POOL_ALL_SUFFIX}${UNIF_POOL_SUFFIX}${PRICE_WARMUP_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}_seed${SEED}_abs.txt \
                                      --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_pretrained-None_pricePRICEOnly_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${FREEZE_LLM_SUFFIX}${FREEZE_ODD_SUFFIX}${FREEZE_ALL_SUFFIX}${FREEZE_EVEN_SUFFIX}${MLP_BEFORE_CA_SUFFIX}${EVAL_FRZ_SUFFIX}${RESEED_SUFFIX}${POOL_ALL_SUFFIX}${UNIF_POOL_SUFFIX}${PRICE_WARMUP_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}_seed${SEED}.log \
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
                                      $PRICE_M_ARG $PRICE_S_ARG $PRICE_B_ARG $PRICE_N_ARGS $NO_LLM_RESIDUAL_ARG $NO_OR_TRANSFORMER_ARG \
                                      $PRICE_RANDOM_INIT_FLAG
fi

if [ "$finetune" == "PriceBothSep" ]; then
  #########################Case 4: Both finetuned separately#########################
  PRICE_MODEL_PATH=${PRICE_MODEL_PATH:-"$SCRIPT_DIR_LLM/experiments/price_statistics/model/model_params.pth"}
  PRICE_BIN_SIZE=${PRICE_BIN_SIZE:-40}

  # Step 1: Finetune LLM
  algo=llm_finetune
  hid_units=2048
  lr=${LLM_LR:-0.0001}
  batch_size=$FT_BATCH_SIZE

  check_model_exists_llm() {
    local mode=$1
    local model_file="finetuned_models/${DB_ENGINE}${SUBDIR_PART}/${CANONICAL_TRAIN_HYPHEN}_time_${mode}_${model_name1}_b${FT_BATCH_SIZE}_llm.pt"
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
                                        --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_lora_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}.log \
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
                                        $PRICE_M_ARG $PRICE_S_ARG $PRICE_B_ARG $PRICE_N_ARGS $NO_LLM_RESIDUAL_ARG $NO_OR_TRANSFORMER_ARG
  fi

  # Step 2: Finetune PRICE on cardinality
  PRICE_SEPARATE_FILE="finetuned_models/${DB_ENGINE}${SUBDIR_PART}/${CANONICAL_TRAIN_HYPHEN}_card_b${FT_BATCH_SIZE}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${EPOCH_SUFFIX}_price_separate.pt"
  if [ -f "$PRICE_SEPARATE_FILE" ]; then
    echo "Separately finetuned PRICE weights already exist: $PRICE_SEPARATE_FILE"
  else
    algo=price_finetune
    price_lr=${PRICE_LR:-$PRICE_LR_DEFAULT}
    batch_size=$FT_BATCH_SIZE

    echo "PriceBothSep: finetune PRICE on cardinality"

    setup_args_and_suffixes

    python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                        --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_${DB_ENGINE}_${price_lr}_b${batch_size}_${model_name1}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${EPOCH_SUFFIX}.log \
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
                                        $PRICE_M_ARG $PRICE_S_ARG $PRICE_B_ARG $PRICE_N_ARGS $NO_LLM_RESIDUAL_ARG $NO_OR_TRANSFORMER_ARG \
                                        $PRICE_RANDOM_INIT_FLAG \
                                        $CHECKPOINT_INTERVAL_ARG
  fi

  # Step 3: Inference with both finetuned weights
  algo=llm_price
  embed_size=${EMBED_SIZE:-1000}
  hid_units=2048
  lr=${LLM_LR:-0.0001}
  batch_size=64

  echo "PriceBothSep: inference with finetuned LLM + finetuned PRICE"

  setup_args_and_suffixes

  python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                      --output_dir_qerror ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_pretrained-lora_priceBothSep_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${FREEZE_LLM_SUFFIX}${FREEZE_ODD_SUFFIX}${FREEZE_ALL_SUFFIX}${FREEZE_EVEN_SUFFIX}${MLP_BEFORE_CA_SUFFIX}${EVAL_FRZ_SUFFIX}${RESEED_SUFFIX}${POOL_ALL_SUFFIX}${UNIF_POOL_SUFFIX}${PRICE_WARMUP_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}_seed${SEED}.csv \
                                      --output_dir_abs ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_pretrained-lora_priceBothSep_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${FREEZE_LLM_SUFFIX}${FREEZE_ODD_SUFFIX}${FREEZE_ALL_SUFFIX}${FREEZE_EVEN_SUFFIX}${MLP_BEFORE_CA_SUFFIX}${EVAL_FRZ_SUFFIX}${RESEED_SUFFIX}${POOL_ALL_SUFFIX}${UNIF_POOL_SUFFIX}${PRICE_WARMUP_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}_seed${SEED}_abs.txt \
                                      --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_pretrained-lora_priceBothSep_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${FREEZE_LLM_SUFFIX}${FREEZE_ODD_SUFFIX}${FREEZE_ALL_SUFFIX}${FREEZE_EVEN_SUFFIX}${MLP_BEFORE_CA_SUFFIX}${EVAL_FRZ_SUFFIX}${RESEED_SUFFIX}${POOL_ALL_SUFFIX}${UNIF_POOL_SUFFIX}${PRICE_WARMUP_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}_seed${SEED}.log \
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
                                      $PRICE_M_ARG $PRICE_S_ARG $PRICE_B_ARG $PRICE_N_ARGS $NO_LLM_RESIDUAL_ARG $NO_OR_TRANSFORMER_ARG \
                                      $PRICE_RANDOM_INIT_FLAG
fi

if [ "$finetune" == "PriceFTwithLLM" ]; then
  #########################Case 5: PRICE finetuned with frozen LLM embeddings#########################
  PRICE_MODEL_PATH=${PRICE_MODEL_PATH:-"$SCRIPT_DIR_LLM/experiments/price_statistics/model/model_params.pth"}
  PRICE_BIN_SIZE=${PRICE_BIN_SIZE:-40}

  # Step 1: Finetune PRICE+MLP with frozen LLM (no LLM forward per batch —
  # train.py's --freeze_llm path trains FrozenLLMPriceModel on pre-computed
  # pooled LLM embeddings, loaded from / saved to the SAME embedding cache as a
  # mode-1 pretrained-inference run: pretrained-None, algo=llm).
  # Weight prefix must match train.py's llm_price_finetune save (llm_mode=inference).
  FROZEN_JOINT_PREFIX="finetuned_models/${DB_ENGINE}${SUBDIR_PART}/${CANONICAL_TRAIN_HYPHEN}_time_inference_${model_name1}_b${FT_BATCH_SIZE}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_N_SUFFIX}_llm_price${NO_LLM_RESIDUAL_SUFFIX}_freezeLLM${PRICE_RAND_INIT_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${PRICE_FFN_RATIO_SUFFIX}${EPOCH_SUFFIX}_seed${SEED}"
  SKIP_TRAIN_ARG=""
  if [ -f "${FROZEN_JOINT_PREFIX}_price.pt" ] && [ -f "${FROZEN_JOINT_PREFIX}_mlp.pt" ]; then
    echo "Frozen-joint finetuned PRICE weights already exist: ${FROZEN_JOINT_PREFIX}_price.pt"
    SKIP_TRAIN_ARG="--skip_train_load_finetuned_weights"
  fi
  algo=llm_price_finetune
  hid_units=2048
  lr=${LLM_LR:-0.0001}
  price_lr=${PRICE_LR:-$PRICE_LR_DEFAULT}
  batch_size=$FT_BATCH_SIZE
  grad_accum_steps=${GRAD_ACCUM_STEPS:-1}

  GRAD_ACCUM_ARG=""
  if [[ "$grad_accum_steps" -gt 1 ]]; then
    GRAD_ACCUM_ARG="--grad_accum_steps $grad_accum_steps"
    echo "  Gradient accumulation: ${grad_accum_steps} steps (effective batch = ${batch_size} * ${grad_accum_steps})"
  fi

  echo "PriceFTwithLLM: finetune PRICE+MLP with frozen LLM (time)"

  setup_args_and_suffixes

  python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                      --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_frozen_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_N_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${PRICE_FFN_RATIO_SUFFIX}${EPOCH_SUFFIX}_seed${SEED}.log \
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
                                      $PRICE_M_ARG $PRICE_S_ARG $PRICE_B_ARG $PRICE_N_ARGS $NO_LLM_RESIDUAL_ARG $NO_OR_TRANSFORMER_ARG \
                                      $PRICE_RANDOM_INIT_FLAG \
                                      $CHECKPOINT_INTERVAL_ARG \
                                      $GRAD_ACCUM_ARG \
                                      $PRICE_N_LAYERS_ARG \
                                      $PRICE_FFN_RATIO_ARG $OR_N_LAYERS_ARG $OR_N_HEADS_ARG $OR_FFN_RATIO_ARG \
                                      $EARLY_STOP_ARG \
                                      $PRICE_WARMUP_ARG \
                                      $PRICE_LR_ARG \
                                      $SUBDIR_ARG \
                                      $SKIP_TRAIN_ARG

  # Step 2: Inference with frozen LLM + frozen-joint finetuned PRICE
  algo=llm_price
  embed_size=${EMBED_SIZE:-1000}
  hid_units=2048
  lr=${LLM_LR:-0.0001}
  batch_size=64

  echo "PriceFTwithLLM: inference with frozen LLM + frozen-joint finetuned PRICE (time)"

  setup_args_and_suffixes

  python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                      --output_dir_qerror ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_pretrained-None_priceFTwithLLM_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_N_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${PRICE_FFN_RATIO_SUFFIX}${FREEZE_LLM_SUFFIX}${FREEZE_ODD_SUFFIX}${FREEZE_ALL_SUFFIX}${FREEZE_EVEN_SUFFIX}${MLP_BEFORE_CA_SUFFIX}${EVAL_FRZ_SUFFIX}${RESEED_SUFFIX}${POOL_ALL_SUFFIX}${UNIF_POOL_SUFFIX}${PRICE_WARMUP_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}_seed${SEED}.csv \
                                      --output_dir_abs ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_pretrained-None_priceFTwithLLM_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_N_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${PRICE_FFN_RATIO_SUFFIX}${FREEZE_LLM_SUFFIX}${FREEZE_ODD_SUFFIX}${FREEZE_ALL_SUFFIX}${FREEZE_EVEN_SUFFIX}${MLP_BEFORE_CA_SUFFIX}${EVAL_FRZ_SUFFIX}${RESEED_SUFFIX}${POOL_ALL_SUFFIX}${UNIF_POOL_SUFFIX}${PRICE_WARMUP_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}_seed${SEED}_abs.txt \
                                      --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_pretrained-None_priceFTwithLLM_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_N_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${PRICE_FFN_RATIO_SUFFIX}${FREEZE_LLM_SUFFIX}${FREEZE_ODD_SUFFIX}${FREEZE_ALL_SUFFIX}${FREEZE_EVEN_SUFFIX}${MLP_BEFORE_CA_SUFFIX}${EVAL_FRZ_SUFFIX}${RESEED_SUFFIX}${POOL_ALL_SUFFIX}${UNIF_POOL_SUFFIX}${PRICE_WARMUP_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}_seed${SEED}.log \
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
                                      $PRICE_M_ARG $PRICE_S_ARG $PRICE_B_ARG $PRICE_N_ARGS $NO_LLM_RESIDUAL_ARG $NO_OR_TRANSFORMER_ARG \
                                      $PRICE_RANDOM_INIT_FLAG \
                                      $PRICE_N_LAYERS_ARG \
                                      $PRICE_FFN_RATIO_ARG $OR_N_LAYERS_ARG $OR_N_HEADS_ARG $OR_FFN_RATIO_ARG \
                                      $SUBDIR_ARG
fi

if [ "$finetune" == "GatedJointPrice" ]; then
  PRICE_MODEL_PATH=${PRICE_MODEL_PATH:-"$SCRIPT_DIR_LLM/experiments/price_statistics/model/model_params.pth"}
  PRICE_BIN_SIZE=${PRICE_BIN_SIZE:-40}

  # Check if finetuned GatedJointPrice weights already exist
  GATED_JOINT_PREFIX="finetuned_models/${DB_ENGINE}${SUBDIR_PART}/${CANONICAL_TRAIN_HYPHEN}_time_lora_${model_name1}_b${FT_BATCH_SIZE}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_N_SUFFIX}_llm_price${NO_LLM_RESIDUAL_SUFFIX}_gated${PRICE_RAND_INIT_SUFFIX}${EPOCH_SUFFIX}"
  if [ -f "${GATED_JOINT_PREFIX}_llm.pt" ] && [ -f "${GATED_JOINT_PREFIX}_price.pt" ] && [ -f "${GATED_JOINT_PREFIX}_gate.pt" ]; then
    echo "Finetuned GatedJointPrice weights already exist, skipping finetune:"
    echo "  LLM:   ${GATED_JOINT_PREFIX}_llm.pt"
    echo "  PRICE: ${GATED_JOINT_PREFIX}_price.pt"
    echo "  Gate:  ${GATED_JOINT_PREFIX}_gate.pt"
  else
    #########################Gated Joint LLM+PRICE finetune#########################
    algo=llm_price_finetune
    hid_units=2048
    lr=${LLM_LR:-0.0001}
    price_lr=${PRICE_LR:-$PRICE_LR_DEFAULT}
    batch_size=$FT_BATCH_SIZE

    echo "Gated Joint LLM+PRICE finetune"

    setup_args_and_suffixes

    python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                        --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_lora_gated_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${EPOCH_SUFFIX}.log \
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
                                        $PRICE_M_ARG $PRICE_S_ARG $PRICE_B_ARG $PRICE_N_ARGS $NO_LLM_RESIDUAL_ARG $NO_OR_TRANSFORMER_ARG \
                                        $PRICE_RANDOM_INIT_FLAG \
                                        $CHECKPOINT_INTERVAL_ARG
  fi

  #########################inference: pre-trained GatedJointPrice#########################
  algo=llm_price
  embed_size=${EMBED_SIZE:-1000}
  hid_units=2048
  lr=${LLM_LR:-0.0001}
  batch_size=64

  echo "inference: pre-trained GatedJointPrice"

  setup_args_and_suffixes

  python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                      --output_dir_qerror ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_pretrained-lora_priceGatedJoint_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${FREEZE_LLM_SUFFIX}${FREEZE_ODD_SUFFIX}${FREEZE_ALL_SUFFIX}${FREEZE_EVEN_SUFFIX}${MLP_BEFORE_CA_SUFFIX}${EVAL_FRZ_SUFFIX}${RESEED_SUFFIX}${POOL_ALL_SUFFIX}${UNIF_POOL_SUFFIX}${PRICE_WARMUP_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}_seed${SEED}.csv \
                                      --output_dir_abs ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_pretrained-lora_priceGatedJoint_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${FREEZE_LLM_SUFFIX}${FREEZE_ODD_SUFFIX}${FREEZE_ALL_SUFFIX}${FREEZE_EVEN_SUFFIX}${MLP_BEFORE_CA_SUFFIX}${EVAL_FRZ_SUFFIX}${RESEED_SUFFIX}${POOL_ALL_SUFFIX}${UNIF_POOL_SUFFIX}${PRICE_WARMUP_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}_seed${SEED}_abs.txt \
                                      --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_pretrained-lora_priceGatedJoint_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${FREEZE_LLM_SUFFIX}${FREEZE_ODD_SUFFIX}${FREEZE_ALL_SUFFIX}${FREEZE_EVEN_SUFFIX}${MLP_BEFORE_CA_SUFFIX}${EVAL_FRZ_SUFFIX}${RESEED_SUFFIX}${POOL_ALL_SUFFIX}${UNIF_POOL_SUFFIX}${PRICE_WARMUP_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}_seed${SEED}.log \
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
                                      $PRICE_M_ARG $PRICE_S_ARG $PRICE_B_ARG $PRICE_N_ARGS $NO_LLM_RESIDUAL_ARG $NO_OR_TRANSFORMER_ARG \
                                      $PRICE_RANDOM_INIT_FLAG
fi

if [ "$finetune" == "CrossAttentionJoint" ]; then
  PRICE_MODEL_PATH=${PRICE_MODEL_PATH:-"$SCRIPT_DIR_LLM/experiments/price_statistics/model/model_params.pth"}
  PRICE_BIN_SIZE=${PRICE_BIN_SIZE:-40}

  # Check if finetuned CrossAttentionJoint weights already exist
  CROSS_ATTN_JOINT_PREFIX="finetuned_models/${DB_ENGINE}${SUBDIR_PART}/${CANONICAL_TRAIN_HYPHEN}_time_lora_${model_name1}_b${FT_BATCH_SIZE}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_N_SUFFIX}_llm_price${NO_LLM_RESIDUAL_SUFFIX}${CROSS_ATTN_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${PRICE_FFN_RATIO_SUFFIX}${N_CROSS_LAYERS_SUFFIX}${CROSS_ATTN_DROPOUT_SUFFIX}${CROSS_ATTN_GATE_SUFFIX}${RESIDUAL_PRED_SUFFIX}${DELTA_BOUND_SUFFIX}${PRICE_EMB_DROPOUT_SUFFIX}${INIT_LLM_FROM_SUFFIX}${DETERMINISTIC_SUFFIX}${CROSS_ATTN_NOOP_SUFFIX}${FORCE_INFLATE_SUFFIX}${PRICE_OUTPUT_DIM_SUFFIX}${FREEZE_LLM_SUFFIX}${FREEZE_ODD_SUFFIX}${FREEZE_ALL_SUFFIX}${FREEZE_EVEN_SUFFIX}${MLP_BEFORE_CA_SUFFIX}${EVAL_FRZ_SUFFIX}${RESEED_SUFFIX}${POOL_ALL_SUFFIX}${UNIF_POOL_SUFFIX}${PRICE_WARMUP_SUFFIX}${PRICE_LR_SUFFIX}${EPOCH_SUFFIX}"
  if [ -f "${CROSS_ATTN_JOINT_PREFIX}_llm.pt" ] && [ -f "${CROSS_ATTN_JOINT_PREFIX}_price.pt" ]; then
    echo "Finetuned CrossAttentionJoint weights already exist, skipping finetune:"
    echo "  LLM:   ${CROSS_ATTN_JOINT_PREFIX}_llm.pt"
    echo "  PRICE: ${CROSS_ATTN_JOINT_PREFIX}_price.pt"
  else
    #########################Cross-Attention Joint LLM+PRICE finetune#########################
    algo=llm_price_finetune
    hid_units=2048
    lr=${LLM_LR:-0.0001}
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
                                        --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_lora_crossAttn_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${PRICE_FFN_RATIO_SUFFIX}${N_CROSS_LAYERS_SUFFIX}${CROSS_ATTN_DROPOUT_SUFFIX}${CROSS_ATTN_GATE_SUFFIX}${RESIDUAL_PRED_SUFFIX}${DELTA_BOUND_SUFFIX}${PRICE_EMB_DROPOUT_SUFFIX}${INIT_LLM_FROM_SUFFIX}${DETERMINISTIC_SUFFIX}${CROSS_ATTN_NOOP_SUFFIX}${FORCE_INFLATE_SUFFIX}${PRICE_OUTPUT_DIM_SUFFIX}${FREEZE_LLM_SUFFIX}${FREEZE_ODD_SUFFIX}${FREEZE_ALL_SUFFIX}${FREEZE_EVEN_SUFFIX}${MLP_BEFORE_CA_SUFFIX}${EVAL_FRZ_SUFFIX}${RESEED_SUFFIX}${POOL_ALL_SUFFIX}${UNIF_POOL_SUFFIX}${PRICE_WARMUP_SUFFIX}${PRICE_LR_SUFFIX}${EPOCH_SUFFIX}.log \
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
                                        $PRICE_M_ARG $PRICE_S_ARG $PRICE_B_ARG $PRICE_N_ARGS $NO_LLM_RESIDUAL_ARG $NO_OR_TRANSFORMER_ARG \
                                        $PRICE_RANDOM_INIT_FLAG \
                                        $CHECKPOINT_INTERVAL_ARG \
                                        $GRAD_ACCUM_ARG \
                                        $PRICE_N_LAYERS_ARG \
                                        $PRICE_FFN_RATIO_ARG $OR_N_LAYERS_ARG $OR_N_HEADS_ARG $OR_FFN_RATIO_ARG \
                                        $N_CROSS_LAYERS_ARG \
                                        $CROSS_ATTN_LR_ARG
  fi

  #########################inference: pre-trained CrossAttentionJoint#########################
  # Cross-attention requires the full model (LLM+PRICE+cross-attn) — uses llm_price with cross_attn_joint source
  algo=llm_price
  embed_size=${EMBED_SIZE:-1000}
  hid_units=2048
  lr=${LLM_LR:-0.0001}
  batch_size=64

  echo "inference: pre-trained CrossAttentionJoint"

  setup_args_and_suffixes

  python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                      --output_dir_qerror ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_pretrained-lora_priceCrossAttnJoint_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${REFINED_POOL_SUFFIX}${TRIPLE_CONCAT_SUFFIX}${INFLATE_PRICE_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${PRICE_FFN_RATIO_SUFFIX}${N_CROSS_LAYERS_SUFFIX}${FREEZE_LLM_SUFFIX}${FREEZE_ODD_SUFFIX}${FREEZE_ALL_SUFFIX}${FREEZE_EVEN_SUFFIX}${MLP_BEFORE_CA_SUFFIX}${EVAL_FRZ_SUFFIX}${RESEED_SUFFIX}${POOL_ALL_SUFFIX}${UNIF_POOL_SUFFIX}${PRICE_WARMUP_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}${RETRAIN_MLP_SUFFIX}_seed${SEED}.csv \
                                      --output_dir_abs ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_pretrained-lora_priceCrossAttnJoint_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${REFINED_POOL_SUFFIX}${TRIPLE_CONCAT_SUFFIX}${INFLATE_PRICE_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${PRICE_FFN_RATIO_SUFFIX}${N_CROSS_LAYERS_SUFFIX}${FREEZE_LLM_SUFFIX}${FREEZE_ODD_SUFFIX}${FREEZE_ALL_SUFFIX}${FREEZE_EVEN_SUFFIX}${MLP_BEFORE_CA_SUFFIX}${EVAL_FRZ_SUFFIX}${RESEED_SUFFIX}${POOL_ALL_SUFFIX}${UNIF_POOL_SUFFIX}${PRICE_WARMUP_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}${RETRAIN_MLP_SUFFIX}_seed${SEED}_abs.txt \
                                      --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_pretrained-lora_priceCrossAttnJoint_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${REFINED_POOL_SUFFIX}${TRIPLE_CONCAT_SUFFIX}${INFLATE_PRICE_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${PRICE_FFN_RATIO_SUFFIX}${N_CROSS_LAYERS_SUFFIX}${FREEZE_LLM_SUFFIX}${FREEZE_ODD_SUFFIX}${FREEZE_ALL_SUFFIX}${FREEZE_EVEN_SUFFIX}${MLP_BEFORE_CA_SUFFIX}${EVAL_FRZ_SUFFIX}${RESEED_SUFFIX}${POOL_ALL_SUFFIX}${UNIF_POOL_SUFFIX}${PRICE_WARMUP_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}${RETRAIN_MLP_SUFFIX}_seed${SEED}.log \
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
                                      $PRICE_M_ARG $PRICE_S_ARG $PRICE_B_ARG $PRICE_N_ARGS $NO_LLM_RESIDUAL_ARG $NO_OR_TRANSFORMER_ARG \
                                      $PRICE_RANDOM_INIT_FLAG \
                                      $PRICE_N_LAYERS_ARG \
                                      $PRICE_FFN_RATIO_ARG $OR_N_LAYERS_ARG $OR_N_HEADS_ARG $OR_FFN_RATIO_ARG \
                                      $N_CROSS_LAYERS_ARG \
                                      $CROSS_ATTN_DROPOUT_ARG \
                                        $CROSS_ATTN_GATE_ARG \
                                        $RESIDUAL_PRED_ARG \
                                        $DELTA_BOUND_ARG \
                                        $PRICE_EMB_DROPOUT_ARG \
                                        $INIT_LLM_FROM_ARG \
                                        $DETERMINISTIC_ARG \
                                        $NO_RETRAIN_MLP_ARG \
                                        $CROSS_ATTN_NOOP_ARG \
                                        $FORCE_INFLATE_ARG \
                                        $PRICE_OUTPUT_DIM_ARG \
                                      $RETRAIN_MLP_FLAG \
                                      $REFINED_POOL_FLAG \
                                      $TRIPLE_CONCAT_FLAG \
                                      $INFLATE_PRICE_FLAG \
                                      $EARLY_STOP_ARG \
                                      $SUBDIR_ARG
fi

if [ "$finetune" == "BiCrossAttentionJoint" ]; then
  PRICE_MODEL_PATH=${PRICE_MODEL_PATH:-"$SCRIPT_DIR_LLM/experiments/price_statistics/model/model_params.pth"}
  PRICE_BIN_SIZE=${PRICE_BIN_SIZE:-40}

  # Check if finetuned BiCrossAttentionJoint weights already exist.
  # IMPORTANT: this MUST reproduce train.py's saved name (train.py:1286 ->
  # _arch_path_suffix order, then _randInit, _e{epoch}, _seed{seed}). The old
  # version scattered randInit/cx/frzLLM in the wrong order and omitted _seed,
  # so it never matched the saved weights and biCrossAttn runs ALWAYS retrained
  # instead of loading existing weights. Order below mirrors _arch_path_suffix:
  #   ...biCrossAttn, refinedPool, tripleConcat, inflatePRICE, frzLLM, frzOdd,
  #   frzAll, cx, drop, gate, resPred, db, peDrop, noop, finfl, pod, nl, fr,
  #   pwm, pLR  -> then randInit, epoch, seed.
  BI_CROSS_ATTN_JOINT_PREFIX="finetuned_models/${DB_ENGINE}${SUBDIR_PART}/${CANONICAL_TRAIN_HYPHEN}_time_lora_${model_name1}_b${FT_BATCH_SIZE}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_N_SUFFIX}_llm_price${NO_LLM_RESIDUAL_SUFFIX}${BI_CROSS_ATTN_SUFFIX}${REFINED_POOL_SUFFIX}${TRIPLE_CONCAT_SUFFIX}${INFLATE_PRICE_SUFFIX}${FREEZE_LLM_SUFFIX}${FREEZE_ODD_SUFFIX}${FREEZE_ALL_SUFFIX}${FREEZE_EVEN_SUFFIX}${MLP_BEFORE_CA_SUFFIX}${EVAL_FRZ_SUFFIX}${RESEED_SUFFIX}${POOL_ALL_SUFFIX}${UNIF_POOL_SUFFIX}${N_CROSS_LAYERS_SUFFIX}${CROSS_ATTN_DROPOUT_SUFFIX}${CROSS_ATTN_GATE_SUFFIX}${RESIDUAL_PRED_SUFFIX}${DELTA_BOUND_SUFFIX}${PRICE_EMB_DROPOUT_SUFFIX}${CROSS_ATTN_NOOP_SUFFIX}${FORCE_INFLATE_SUFFIX}${PRICE_OUTPUT_DIM_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${PRICE_FFN_RATIO_SUFFIX}${PRICE_WARMUP_SUFFIX}${PRICE_LR_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${EPOCH_SUFFIX}_seed${SEED}"
  algo=llm_price_finetune
  hid_units=2048
  lr=${LLM_LR:-0.0001}
  price_lr=${PRICE_LR:-$PRICE_LR_DEFAULT}
  batch_size=$FT_BATCH_SIZE
  grad_accum_steps=${GRAD_ACCUM_STEPS:-1}

  if [ -f "${BI_CROSS_ATTN_JOINT_PREFIX}_llm.pt" ] && [ -f "${BI_CROSS_ATTN_JOINT_PREFIX}_price.pt" ]; then
    # Weights exist: skip-train-LOAD them and re-emit the finetune-phase
    # (jointMLP) eval CSV via the live joint forward — do NOT skip the finetune
    # step entirely (that left the jointMLP CDF stale on inference-only refreshes).
    echo "Finetuned BiCrossAttentionJoint weights already exist; loading + emitting finetune-phase eval CSV (jointMLP):"
    echo "  LLM:   ${BI_CROSS_ATTN_JOINT_PREFIX}_llm.pt"
    echo "  PRICE: ${BI_CROSS_ATTN_JOINT_PREFIX}_price.pt"
    SKIP_TRAIN_ARG="--skip_train_load_finetuned_weights"
  else
    #########################Bidirectional Cross-Attention Joint LLM+PRICE finetune#########################
    echo "Bidirectional Cross-Attention Joint LLM+PRICE finetune"
    SKIP_TRAIN_ARG=""
  fi

  # Build grad_accum arg
  GRAD_ACCUM_ARG=""
  if [[ "$grad_accum_steps" -gt 1 ]]; then
    GRAD_ACCUM_ARG="--grad_accum_steps $grad_accum_steps"
    echo "  Gradient accumulation: ${grad_accum_steps} steps (effective batch = ${batch_size} * ${grad_accum_steps})"
  fi

  setup_args_and_suffixes

    # When --no_llm_residual is set the training step is also the only
    # evaluation step (the LLM-side inference below is skipped).  Pass an
    # --output_dir_qerror so train.py emits the test-set CSV.  The path
    # mirrors the BiCrossAttnJoint inference filename with `_noLLMres` and
    # the PRICE_N suffix tags so multi-mode/multi-seed runs don't collide.
    NO_LLM_RES_QERROR_ARG=""
    if [[ -n "$NO_LLM_RESIDUAL_ARG" ]]; then
      NO_LLM_RES_QERROR_ARG="--output_dir_qerror ${RESULTS_DIR}/results_Train_${TRAIN_WLS_HYPHEN}_Test_${WORKLOAD_TEST}_ours${SUBDIR_PART}/time_${algo}_priceBiCrossAttnJoint_noLLMres_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_N_SUFFIX}${REFINED_POOL_SUFFIX}${TRIPLE_CONCAT_SUFFIX}${INFLATE_PRICE_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${PRICE_FFN_RATIO_SUFFIX}${N_CROSS_LAYERS_SUFFIX}${CROSS_ATTN_DROPOUT_SUFFIX}${CROSS_ATTN_GATE_SUFFIX}${RESIDUAL_PRED_SUFFIX}${DELTA_BOUND_SUFFIX}${PRICE_EMB_DROPOUT_SUFFIX}${INIT_LLM_FROM_SUFFIX}${DETERMINISTIC_SUFFIX}${CROSS_ATTN_NOOP_SUFFIX}${FORCE_INFLATE_SUFFIX}${PRICE_OUTPUT_DIM_SUFFIX}${FREEZE_LLM_SUFFIX}${FREEZE_ODD_SUFFIX}${FREEZE_ALL_SUFFIX}${FREEZE_EVEN_SUFFIX}${MLP_BEFORE_CA_SUFFIX}${EVAL_FRZ_SUFFIX}${RESEED_SUFFIX}${POOL_ALL_SUFFIX}${UNIF_POOL_SUFFIX}${PRICE_WARMUP_SUFFIX}${PRICE_LR_SUFFIX}${EPOCH_SUFFIX}_seed${SEED}.csv"
      mkdir -p "${RESULTS_DIR}/results_Train_${TRAIN_WLS_HYPHEN}_Test_${WORKLOAD_TEST}_ours${SUBDIR_PART}"
    fi

    python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                        --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_lora_biCrossAttn_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_N_SUFFIX}${NO_LLM_RESIDUAL_SUFFIX}${REFINED_POOL_SUFFIX}${TRIPLE_CONCAT_SUFFIX}${INFLATE_PRICE_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${PRICE_FFN_RATIO_SUFFIX}${N_CROSS_LAYERS_SUFFIX}${CROSS_ATTN_DROPOUT_SUFFIX}${CROSS_ATTN_GATE_SUFFIX}${RESIDUAL_PRED_SUFFIX}${DELTA_BOUND_SUFFIX}${PRICE_EMB_DROPOUT_SUFFIX}${INIT_LLM_FROM_SUFFIX}${DETERMINISTIC_SUFFIX}${CROSS_ATTN_NOOP_SUFFIX}${FORCE_INFLATE_SUFFIX}${PRICE_OUTPUT_DIM_SUFFIX}${FREEZE_LLM_SUFFIX}${FREEZE_ODD_SUFFIX}${FREEZE_ALL_SUFFIX}${FREEZE_EVEN_SUFFIX}${MLP_BEFORE_CA_SUFFIX}${EVAL_FRZ_SUFFIX}${RESEED_SUFFIX}${POOL_ALL_SUFFIX}${UNIF_POOL_SUFFIX}${PRICE_WARMUP_SUFFIX}${PRICE_LR_SUFFIX}${EPOCH_SUFFIX}_seed${SEED}.log \
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
                                        $NO_LLM_RES_QERROR_ARG \
                                        $BUCKETIZE_ARG \
                                        $QUANTIFICATION_ARG \
                                        $REMOVED_FIELDS_ARG \
                                        $PRICE_M_ARG $PRICE_S_ARG $PRICE_B_ARG $PRICE_N_ARGS $NO_LLM_RESIDUAL_ARG $NO_OR_TRANSFORMER_ARG \
                                        $PRICE_RANDOM_INIT_FLAG \
                                        $CHECKPOINT_INTERVAL_ARG \
                                        $GRAD_ACCUM_ARG \
                                        $PRICE_N_LAYERS_ARG \
                                        $PRICE_FFN_RATIO_ARG $OR_N_LAYERS_ARG $OR_N_HEADS_ARG $OR_FFN_RATIO_ARG \
                                        $N_CROSS_LAYERS_ARG \
                                        $CROSS_ATTN_LR_ARG \
                                        $CROSS_ATTN_DROPOUT_ARG \
                                        $CROSS_ATTN_GATE_ARG \
                                        $RESIDUAL_PRED_ARG \
                                        $DELTA_BOUND_ARG \
                                        $PRICE_EMB_DROPOUT_ARG \
                                        $INIT_LLM_FROM_ARG \
                                        $DETERMINISTIC_ARG \
                                        $NO_RETRAIN_MLP_ARG \
                                        $CROSS_ATTN_NOOP_ARG \
                                        $FORCE_INFLATE_ARG \
                                        $PRICE_OUTPUT_DIM_ARG \
                                        $REFINED_POOL_FLAG \
                                      $TRIPLE_CONCAT_FLAG \
                                      $INFLATE_PRICE_FLAG \
                                      $EARLY_STOP_ARG \
                                      $FREEZE_LLM_ARG $FREEZE_ODD_ARG $FREEZE_ALL_ARG $FREEZE_EVEN_ARG $MLP_BEFORE_CA_ARG \
                                      $PRICE_WARMUP_ARG \
                                      $PRICE_LR_ARG \
                                      $SUBDIR_ARG \
                                      $SKIP_TRAIN_ARG

  #########################inference: pre-trained BiCrossAttentionJoint#########################
  # Bidirectional cross-attention requires the full model (LLM+PRICE+bi-cross-attn).
  # Skip when --no_llm_residual is set: training uses the price_finetune algo
  # branch, which doesn't save _llm.pt. The downstream inference path here
  # would then fail trying to load a non-existent LLM checkpoint.
  if [[ -n "$NO_LLM_RESIDUAL_ARG" ]]; then
    echo "[no_llm_residual] Skipping LLM+PRICE inference step — PRICE-only training already evaluated."
  else
  algo=llm_price
  embed_size=${EMBED_SIZE:-1000}
  hid_units=2048
  lr=${LLM_LR:-0.0001}
  batch_size=64

  echo "inference: pre-trained BiCrossAttentionJoint"

  setup_args_and_suffixes

  python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                      --output_dir_qerror ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_pretrained-lora_priceBiCrossAttnJoint_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_N_SUFFIX}${REFINED_POOL_SUFFIX}${TRIPLE_CONCAT_SUFFIX}${INFLATE_PRICE_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${PRICE_FFN_RATIO_SUFFIX}${N_CROSS_LAYERS_SUFFIX}${FREEZE_LLM_SUFFIX}${FREEZE_ODD_SUFFIX}${FREEZE_ALL_SUFFIX}${FREEZE_EVEN_SUFFIX}${MLP_BEFORE_CA_SUFFIX}${EVAL_FRZ_SUFFIX}${RESEED_SUFFIX}${POOL_ALL_SUFFIX}${UNIF_POOL_SUFFIX}${PRICE_WARMUP_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}${RETRAIN_MLP_SUFFIX}_seed${SEED}.csv \
                                      --output_dir_abs ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_pretrained-lora_priceBiCrossAttnJoint_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_N_SUFFIX}${REFINED_POOL_SUFFIX}${TRIPLE_CONCAT_SUFFIX}${INFLATE_PRICE_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${PRICE_FFN_RATIO_SUFFIX}${N_CROSS_LAYERS_SUFFIX}${FREEZE_LLM_SUFFIX}${FREEZE_ODD_SUFFIX}${FREEZE_ALL_SUFFIX}${FREEZE_EVEN_SUFFIX}${MLP_BEFORE_CA_SUFFIX}${EVAL_FRZ_SUFFIX}${RESEED_SUFFIX}${POOL_ALL_SUFFIX}${UNIF_POOL_SUFFIX}${PRICE_WARMUP_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}${RETRAIN_MLP_SUFFIX}_seed${SEED}_abs.txt \
                                      --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_pretrained-lora_priceBiCrossAttnJoint_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_N_SUFFIX}${REFINED_POOL_SUFFIX}${TRIPLE_CONCAT_SUFFIX}${INFLATE_PRICE_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${PRICE_FFN_RATIO_SUFFIX}${N_CROSS_LAYERS_SUFFIX}${FREEZE_LLM_SUFFIX}${FREEZE_ODD_SUFFIX}${FREEZE_ALL_SUFFIX}${FREEZE_EVEN_SUFFIX}${MLP_BEFORE_CA_SUFFIX}${EVAL_FRZ_SUFFIX}${RESEED_SUFFIX}${POOL_ALL_SUFFIX}${UNIF_POOL_SUFFIX}${PRICE_WARMUP_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}${RETRAIN_MLP_SUFFIX}_seed${SEED}.log \
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
                                      $PRICE_M_ARG $PRICE_S_ARG $PRICE_B_ARG $PRICE_N_ARGS $NO_LLM_RESIDUAL_ARG $NO_OR_TRANSFORMER_ARG \
                                      $PRICE_RANDOM_INIT_FLAG \
                                      $PRICE_N_LAYERS_ARG \
                                      $PRICE_FFN_RATIO_ARG $OR_N_LAYERS_ARG $OR_N_HEADS_ARG $OR_FFN_RATIO_ARG \
                                      $N_CROSS_LAYERS_ARG \
                                      $CROSS_ATTN_DROPOUT_ARG \
                                        $CROSS_ATTN_GATE_ARG \
                                        $RESIDUAL_PRED_ARG \
                                        $DELTA_BOUND_ARG \
                                        $PRICE_EMB_DROPOUT_ARG \
                                        $INIT_LLM_FROM_ARG \
                                        $DETERMINISTIC_ARG \
                                        $NO_RETRAIN_MLP_ARG \
                                        $CROSS_ATTN_NOOP_ARG \
                                        $FORCE_INFLATE_ARG \
                                        $PRICE_OUTPUT_DIM_ARG \
                                      $RETRAIN_MLP_FLAG \
                                      $REFINED_POOL_FLAG \
                                      $TRIPLE_CONCAT_FLAG \
                                      $INFLATE_PRICE_FLAG \
                                      $EARLY_STOP_ARG \
                                      $FREEZE_LLM_ARG $FREEZE_ODD_ARG $FREEZE_ALL_ARG $FREEZE_EVEN_ARG $MLP_BEFORE_CA_ARG \
                                      $PRICE_WARMUP_ARG \
                                      $PRICE_LR_ARG \
                                      $SUBDIR_ARG
  fi  # close --no_llm_residual guard
fi

if [ "$finetune" == "ReverseCrossAttentionJoint" ]; then
  PRICE_MODEL_PATH=${PRICE_MODEL_PATH:-"$SCRIPT_DIR_LLM/experiments/price_statistics/model/model_params.pth"}
  PRICE_BIN_SIZE=${PRICE_BIN_SIZE:-40}

  # Check if finetuned ReverseCrossAttentionJoint weights already exist
  REV_CROSS_ATTN_JOINT_PREFIX="finetuned_models/${DB_ENGINE}${SUBDIR_PART}/${CANONICAL_TRAIN_HYPHEN}_time_lora_${model_name1}_b${FT_BATCH_SIZE}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_N_SUFFIX}_llm_price${NO_LLM_RESIDUAL_SUFFIX}${REV_CROSS_ATTN_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${PRICE_FFN_RATIO_SUFFIX}${N_CROSS_LAYERS_SUFFIX}${CROSS_ATTN_DROPOUT_SUFFIX}${CROSS_ATTN_GATE_SUFFIX}${RESIDUAL_PRED_SUFFIX}${DELTA_BOUND_SUFFIX}${PRICE_EMB_DROPOUT_SUFFIX}${INIT_LLM_FROM_SUFFIX}${DETERMINISTIC_SUFFIX}${CROSS_ATTN_NOOP_SUFFIX}${FORCE_INFLATE_SUFFIX}${PRICE_OUTPUT_DIM_SUFFIX}${FREEZE_LLM_SUFFIX}${FREEZE_ODD_SUFFIX}${FREEZE_ALL_SUFFIX}${FREEZE_EVEN_SUFFIX}${MLP_BEFORE_CA_SUFFIX}${EVAL_FRZ_SUFFIX}${RESEED_SUFFIX}${POOL_ALL_SUFFIX}${UNIF_POOL_SUFFIX}${PRICE_WARMUP_SUFFIX}${PRICE_LR_SUFFIX}${EPOCH_SUFFIX}"
  if [ -f "${REV_CROSS_ATTN_JOINT_PREFIX}_llm.pt" ] && [ -f "${REV_CROSS_ATTN_JOINT_PREFIX}_price.pt" ]; then
    echo "Finetuned ReverseCrossAttentionJoint weights already exist, skipping finetune:"
    echo "  LLM:   ${REV_CROSS_ATTN_JOINT_PREFIX}_llm.pt"
    echo "  PRICE: ${REV_CROSS_ATTN_JOINT_PREFIX}_price.pt"
  else
    #########################Reverse Cross-Attention Joint LLM+PRICE finetune#########################
    algo=llm_price_finetune
    hid_units=2048
    lr=${LLM_LR:-0.0001}
    price_lr=${PRICE_LR:-$PRICE_LR_DEFAULT}
    batch_size=$FT_BATCH_SIZE
    grad_accum_steps=${GRAD_ACCUM_STEPS:-1}

    echo "finetuning: ReverseCrossAttentionJoint LLM+PRICE (time)"

    setup_args_and_suffixes

    python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                        --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_revCrossAttn_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${PRICE_FFN_RATIO_SUFFIX}${N_CROSS_LAYERS_SUFFIX}${CROSS_ATTN_DROPOUT_SUFFIX}${CROSS_ATTN_GATE_SUFFIX}${RESIDUAL_PRED_SUFFIX}${DELTA_BOUND_SUFFIX}${PRICE_EMB_DROPOUT_SUFFIX}${INIT_LLM_FROM_SUFFIX}${DETERMINISTIC_SUFFIX}${CROSS_ATTN_NOOP_SUFFIX}${FORCE_INFLATE_SUFFIX}${PRICE_OUTPUT_DIM_SUFFIX}${FREEZE_LLM_SUFFIX}${FREEZE_ODD_SUFFIX}${FREEZE_ALL_SUFFIX}${FREEZE_EVEN_SUFFIX}${MLP_BEFORE_CA_SUFFIX}${EVAL_FRZ_SUFFIX}${RESEED_SUFFIX}${POOL_ALL_SUFFIX}${UNIF_POOL_SUFFIX}${PRICE_WARMUP_SUFFIX}${PRICE_LR_SUFFIX}${EPOCH_SUFFIX}.log \
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
                                        --use_reverse_cross_attention \
                                        --num_epoch $FT_NUM_EPOCH \
                                        --seed $SEED \
                                        --price_model_path $PRICE_MODEL_PATH \
                                        --price_bin_size $PRICE_BIN_SIZE \
                                        $BUCKETIZE_ARG \
                                        $QUANTIFICATION_ARG \
                                        $REMOVED_FIELDS_ARG \
                                        $PRICE_M_ARG $PRICE_S_ARG $PRICE_B_ARG $PRICE_N_ARGS $NO_LLM_RESIDUAL_ARG $NO_OR_TRANSFORMER_ARG \
                                        $PRICE_RANDOM_INIT_FLAG \
                                        $CHECKPOINT_INTERVAL_ARG \
                                        $GRAD_ACCUM_ARG \
                                        $PRICE_N_LAYERS_ARG \
                                        $PRICE_FFN_RATIO_ARG $OR_N_LAYERS_ARG $OR_N_HEADS_ARG $OR_FFN_RATIO_ARG \
                                        $N_CROSS_LAYERS_ARG \
                                        $CROSS_ATTN_LR_ARG \
                                        $CROSS_ATTN_DROPOUT_ARG \
                                        $CROSS_ATTN_GATE_ARG \
                                        $RESIDUAL_PRED_ARG \
                                        $DELTA_BOUND_ARG \
                                        $PRICE_EMB_DROPOUT_ARG \
                                        $INIT_LLM_FROM_ARG \
                                        $DETERMINISTIC_ARG \
                                        $NO_RETRAIN_MLP_ARG \
                                        $CROSS_ATTN_NOOP_ARG \
                                        $FORCE_INFLATE_ARG \
                                        $PRICE_OUTPUT_DIM_ARG \
                                        $EARLY_STOP_ARG \
                                        $FREEZE_LLM_ARG $FREEZE_ODD_ARG $FREEZE_ALL_ARG $FREEZE_EVEN_ARG $MLP_BEFORE_CA_ARG \
                                      $PRICE_WARMUP_ARG \
                                      $PRICE_LR_ARG \
                                      $SUBDIR_ARG
  fi

  #########################inference: pre-trained ReverseCrossAttentionJoint#########################
  algo=llm_price
  embed_size=${EMBED_SIZE:-1000}
  hid_units=2048
  lr=${LLM_LR:-0.0001}
  batch_size=64

  echo "inference: pre-trained ReverseCrossAttentionJoint"

  setup_args_and_suffixes

  python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                      --output_dir_qerror ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_pretrained-lora_priceRevCrossAttnJoint_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${PRICE_FFN_RATIO_SUFFIX}${N_CROSS_LAYERS_SUFFIX}${FREEZE_LLM_SUFFIX}${FREEZE_ODD_SUFFIX}${FREEZE_ALL_SUFFIX}${FREEZE_EVEN_SUFFIX}${MLP_BEFORE_CA_SUFFIX}${EVAL_FRZ_SUFFIX}${RESEED_SUFFIX}${POOL_ALL_SUFFIX}${UNIF_POOL_SUFFIX}${PRICE_WARMUP_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}${RETRAIN_MLP_SUFFIX}_seed${SEED}.csv \
                                      --output_dir_abs ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_pretrained-lora_priceRevCrossAttnJoint_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${PRICE_FFN_RATIO_SUFFIX}${N_CROSS_LAYERS_SUFFIX}${FREEZE_LLM_SUFFIX}${FREEZE_ODD_SUFFIX}${FREEZE_ALL_SUFFIX}${FREEZE_EVEN_SUFFIX}${MLP_BEFORE_CA_SUFFIX}${EVAL_FRZ_SUFFIX}${RESEED_SUFFIX}${POOL_ALL_SUFFIX}${UNIF_POOL_SUFFIX}${PRICE_WARMUP_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}${RETRAIN_MLP_SUFFIX}_seed${SEED}_abs.txt \
                                      --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_pretrained-lora_priceRevCrossAttnJoint_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${PRICE_N_LAYERS_SUFFIX}${PRICE_FFN_RATIO_SUFFIX}${N_CROSS_LAYERS_SUFFIX}${FREEZE_LLM_SUFFIX}${FREEZE_ODD_SUFFIX}${FREEZE_ALL_SUFFIX}${FREEZE_EVEN_SUFFIX}${MLP_BEFORE_CA_SUFFIX}${EVAL_FRZ_SUFFIX}${RESEED_SUFFIX}${POOL_ALL_SUFFIX}${UNIF_POOL_SUFFIX}${PRICE_WARMUP_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}${RETRAIN_MLP_SUFFIX}_seed${SEED}.log \
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
                                      --price_weights_source reverse_cross_attn_joint \
                                      --use_reverse_cross_attention \
                                      --seed $SEED \
                                      --ft_batch_size $FT_BATCH_SIZE \
                                      --ft_num_epoch $FT_NUM_EPOCH \
                                      $BUCKETIZE_ARG \
                                      $QUANTIFICATION_ARG \
                                      $EMBEDDINGS_ARG \
                                      $REMOVED_FIELDS_ARG \
                                      $PRICE_M_ARG $PRICE_S_ARG $PRICE_B_ARG $PRICE_N_ARGS $NO_LLM_RESIDUAL_ARG $NO_OR_TRANSFORMER_ARG \
                                      $PRICE_RANDOM_INIT_FLAG \
                                      $PRICE_N_LAYERS_ARG \
                                      $PRICE_FFN_RATIO_ARG $OR_N_LAYERS_ARG $OR_N_HEADS_ARG $OR_FFN_RATIO_ARG \
                                      $N_CROSS_LAYERS_ARG \
                                      $RETRAIN_MLP_FLAG \
                                      $EARLY_STOP_ARG \
                                      $SUBDIR_ARG
fi

if [ "$finetune" == "PriceFTthenJoint" ]; then
  #########################Case 6: Frozen-init then joint (PriceFTthenJoint)#########################
  PRICE_MODEL_PATH=${PRICE_MODEL_PATH:-"$SCRIPT_DIR_LLM/experiments/price_statistics/model/model_params.pth"}
  PRICE_BIN_SIZE=${PRICE_BIN_SIZE:-40}

  # Step 1: Finetune PRICE+MLP with frozen LLM (reuse PriceFTwithLLM step 1)
  FROZEN_JOINT_FILE="finetuned_models/${DB_ENGINE}${SUBDIR_PART}/${CANONICAL_TRAIN_HYPHEN}_time_inference_${model_name1}_b${FT_BATCH_SIZE}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}_llm_price${PRICE_RAND_INIT_SUFFIX}${EPOCH_SUFFIX}_price.pt"
  if [ -f "$FROZEN_JOINT_FILE" ]; then
    echo "Frozen-joint finetuned PRICE weights already exist: $FROZEN_JOINT_FILE"
  else
    algo=llm_price_finetune
    hid_units=2048
    lr=${LLM_LR:-0.0001}
    price_lr=${PRICE_LR:-$PRICE_LR_DEFAULT}
    batch_size=$FT_BATCH_SIZE

    echo "PriceFTthenJoint Step 1: finetune PRICE+MLP with frozen LLM (time)"

    setup_args_and_suffixes

    python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                        --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_frozen_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${EPOCH_SUFFIX}.log \
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
                                        $PRICE_M_ARG $PRICE_S_ARG $PRICE_B_ARG $PRICE_N_ARGS $NO_LLM_RESIDUAL_ARG $NO_OR_TRANSFORMER_ARG \
                                        $PRICE_RANDOM_INIT_FLAG \
                                        $CHECKPOINT_INTERVAL_ARG
  fi

  # Step 2: Joint finetune with frozen-init PRICE
  FROZEN_INIT_PREFIX="finetuned_models/${DB_ENGINE}${SUBDIR_PART}/${CANONICAL_TRAIN_HYPHEN}_time_lora_${model_name1}_b${FT_BATCH_SIZE}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_N_SUFFIX}_llm_price${NO_LLM_RESIDUAL_SUFFIX}_frozenInit${PRICE_RAND_INIT_SUFFIX}${EPOCH_SUFFIX}"
  if [ -f "${FROZEN_INIT_PREFIX}_llm.pt" ] && [ -f "${FROZEN_INIT_PREFIX}_price.pt" ]; then
    echo "Frozen-init joint weights already exist, skipping finetune:"
    echo "  LLM:   ${FROZEN_INIT_PREFIX}_llm.pt"
    echo "  PRICE: ${FROZEN_INIT_PREFIX}_price.pt"
  else
    algo=llm_price_finetune
    hid_units=2048
    lr=${LLM_LR:-0.0001}
    price_lr=${PRICE_LR:-$PRICE_LR_DEFAULT}
    batch_size=$FT_BATCH_SIZE

    echo "PriceFTthenJoint Step 2: joint LLM+PRICE finetune with frozen-init PRICE (time)"

    setup_args_and_suffixes

    python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                        --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_lora_frozenInit_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${EPOCH_SUFFIX}.log \
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
                                        $PRICE_M_ARG $PRICE_S_ARG $PRICE_B_ARG $PRICE_N_ARGS $NO_LLM_RESIDUAL_ARG $NO_OR_TRANSFORMER_ARG \
                                        $PRICE_RANDOM_INIT_FLAG \
                                        $CHECKPOINT_INTERVAL_ARG
  fi

  # Step 3: Inference with frozen-init joint weights
  algo=llm_price
  embed_size=${EMBED_SIZE:-1000}
  hid_units=2048
  lr=${LLM_LR:-0.0001}
  batch_size=64

  echo "PriceFTthenJoint Step 3: inference with frozen-init joint weights (time)"

  setup_args_and_suffixes

  python train.py --dat_paths_train "${DAT_PATHS[@]}" --dat_path_test $DAT_PATH_TEST \
                                      --output_dir_qerror ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_pretrained-lora_priceFTthenJoint_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${FREEZE_LLM_SUFFIX}${FREEZE_ODD_SUFFIX}${FREEZE_ALL_SUFFIX}${FREEZE_EVEN_SUFFIX}${MLP_BEFORE_CA_SUFFIX}${EVAL_FRZ_SUFFIX}${RESEED_SUFFIX}${POOL_ALL_SUFFIX}${UNIF_POOL_SUFFIX}${PRICE_WARMUP_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}_seed${SEED}.csv \
                                      --output_dir_abs ${RESULTS_DIR}/results_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_pretrained-lora_priceFTthenJoint_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${FREEZE_LLM_SUFFIX}${FREEZE_ODD_SUFFIX}${FREEZE_ALL_SUFFIX}${FREEZE_EVEN_SUFFIX}${MLP_BEFORE_CA_SUFFIX}${EVAL_FRZ_SUFFIX}${RESEED_SUFFIX}${POOL_ALL_SUFFIX}${UNIF_POOL_SUFFIX}${PRICE_WARMUP_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}_seed${SEED}_abs.txt \
                                      --log_file ${LOGS_DIR}/logs_Train_"${TRAIN_WLS_HYPHEN}"_Test_"$WORKLOAD_TEST"_ours${SUBDIR_PART}/time_${algo}_pretrained-lora_priceFTthenJoint_${train_ratio}_cdf_${DB_ENGINE}_${lr}_b${batch_size}_h${hid_units}_${model_name1}_emb${embed_size}${BUCKETIZE_SUFFIX}${QUANTIFICATION_SUFFIX}${REMOVED_FIELDS_SUFFIX}${PRICE_M_SUFFIX}${PRICE_S_SUFFIX}${PRICE_B_SUFFIX}${PRICE_RAND_INIT_SUFFIX}${FREEZE_LLM_SUFFIX}${FREEZE_ODD_SUFFIX}${FREEZE_ALL_SUFFIX}${FREEZE_EVEN_SUFFIX}${MLP_BEFORE_CA_SUFFIX}${EVAL_FRZ_SUFFIX}${RESEED_SUFFIX}${POOL_ALL_SUFFIX}${UNIF_POOL_SUFFIX}${PRICE_WARMUP_SUFFIX}_e${FT_NUM_EPOCH}_ftb${FT_BATCH_SIZE}_seed${SEED}.log \
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
                                      $PRICE_M_ARG $PRICE_S_ARG $PRICE_B_ARG $PRICE_N_ARGS $NO_LLM_RESIDUAL_ARG $NO_OR_TRANSFORMER_ARG \
                                      $PRICE_RANDOM_INIT_FLAG
fi
