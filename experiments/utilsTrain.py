import os
import pandas as pd
import torch
import sys
import torch.nn as nn
import argparse
import torch.nn.init as init
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, TensorDataset
import logging
from pathlib import Path

# Ensure absolute paths are available on sys.path for sibling modules
_CURRENT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _CURRENT_DIR.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
_EVALUATION_DIR = _PROJECT_ROOT / "evaluation"
if str(_EVALUATION_DIR) not in sys.path:
    sys.path.insert(0, str(_EVALUATION_DIR))

from feature_extractor import DatasetInfo
from dataset_utils import *
from algorithms.aimeetsai import *

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', type=str, choices=['mysql', 'postgres', 'duckdb', 'spark'], required=True, help='Target database type')
    parser.add_argument("--workload", type=str)
    parser.add_argument("--algo", type=str)
    parser.add_argument("--dat_path", type=str)
    parser.add_argument("--file_name", type=str)
    parser.add_argument("--output_dir_qerror", type=str)
    parser.add_argument("--output_dir_abs", type=str)
    parser.add_argument("--LLM_path", type=str,
                            help="Path to the saved LLM model state_dict (QueryPlanPredictor).")
    parser.add_argument("--use_binary", action="store_true", default=False,
                            help="If set, incorporate the binary vector extracted from file names.")
    parser.add_argument("--binary_length", type=int, default=8,
                            help="Fixed length for binary representation (padding/truncating as needed)")
    parser.add_argument("--model_name", type=str, default="NousResearch/Hermes-3-Llama-3.2-3B", help="Pretrained LLM model name")
    parser.add_argument("--mlp_hidden_dim", type=int, default=128, help="MLP hidden dimension")
    parser.add_argument("--mlp_init_weight", type=int, default=5000, help="Initial weight for the last layer of MLP")
    parser.add_argument("--learning_rate", type=float, default=1e-4)
    parser.add_argument("--batch_size", type=int, default=102)
    parser.add_argument("--hid_units", type=int, default=256)
    # parser.add_argument("--num_epoch", type=int, default=2)
    parser.add_argument("--num_epoch", type=int, default=200)
    parser.add_argument("--embed_size", type=int, default=999999999)
    parser.add_argument("--card", action="store_true", default=False)
    parser.add_argument("--llm_pretrained", type=str, default=None)
    parser.add_argument("--llm_pretrained_task", type=str, default=None)
    parser.add_argument("--log_file", type=str, default=None)
    parser.add_argument("--workload_test",  type=str, default=None,
                        help="If set, override test workload (otherwise use --workload)")
    parser.add_argument("--dat_path_test", type=str, default=None,
                        help="If set, override test dat_path (otherwise use --dat_path)")
    parser.add_argument("--train_ratio", type=float, default=-1)
    parser.add_argument("--max_queries", type=int, default=-1,
                        help="Limit total queries loaded from CSV (default: -1 = no limit). "
                             "Truncates BEFORE embedding generation, speeding up model selection.")
    parser.add_argument("--llm_mode", type=str, default="inference")
    parser.add_argument("--llm_downstream", type=str, choices=['mlp', 'autogluon'], default='mlp',
                        help="Downstream learner for LLM embeddings (default: mlp)")
    parser.add_argument("--workloads_train", nargs="+", default=["tpcds", "tpch", "syn", "job", "job_full", "stats"], help="one or more workloads to train on")
    parser.add_argument("--dat_paths_train", nargs="+", default=["../data/imdb/postgres/"], help="one or more data paths to train on")

    # added bucketize_input flag
    parser.add_argument("--bucketize_input", type=str, choices=['separate', 'unified'], default=None,
                        help="Bucketize strategy: separate (bucketize_plans), unified (bucketize_plans_unified), None (no bucketizing)")
    parser.add_argument("--embeddings_exist", action="store_true", default=False)
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility')
    
    # sliding window arguments
    parser.add_argument("--use_sliding_window", action="store_true", default=False,
                        help="Enable sliding window for long texts")
    parser.add_argument("--window_stride_ratio", type=float, default=0.8,
                        help="Sliding window stride ratio (default 0.8)")
    
    # verbose output arguments
    parser.add_argument("--verbose_info", action="store_true", default=False,
                        help="Enable verbose output with query plans, embeddings, labels, and KNN information")
    parser.add_argument("--knn_k", type=int, default=5,
                        help="Number of nearest neighbors to find for verbose output (default 5)")
    
    # quantization arguments
    parser.add_argument("--quantification", type=str, choices=['4-bit', '8-bit', 'None'], default='None',
                        help="Quantization type: 4-bit (default), 8-bit, or None (no quantization)")
    # stats token injection arguments (distribution stats in LLM)
    parser.add_argument("--stats_token_inject", action="store_true", default=False,
                        help="Enable [STAT] token injection with per-predicate stats vectors")
    parser.add_argument("--stats_token_str", type=str, default="[STAT]",
                        help="Special token string used for stats injection (default [STAT])")
    parser.add_argument("--stats_token_dim", type=int, default=5,
                        help="Dimension of per-[STAT] vector (default 5)")
    parser.add_argument("--stats_token_mode", type=str, choices=["avg", "per_column"], default="per_column",
                        help="Stats token mode: avg (one token per predicate) or per_column (one per column)")
    parser.add_argument("--stats_pg_stats_path", type=str, default=None,
                        help="Path to pg_stats.csv (optional override)")
    parser.add_argument("--stats_table_sizes_path", type=str, default=None,
                        help="Path to table_sizes.csv (optional override)")
    parser.add_argument("--concat_true_embeddings", action="store_true", default=False,
                        help="Concatenate queries_true embeddings to LLM embeddings (in inference mode)")
    parser.add_argument("--queries_true_dir", type=str, default="../queries_true",
                        help="Directory containing queries_true embedding CSVs")
    # Joint LLM+PRICE finetuning arguments
    _default_price_model = os.path.join(os.path.dirname(os.path.abspath(__file__)), "price_statistics", "model", "model_params.pth")
    if not os.path.exists(_default_price_model):
        _default_price_model = "/root/PRICE/results/model_params.pth"
    parser.add_argument("--price_model_path", type=str, default=_default_price_model,
                        help="Path to pretrained PRICE model weights")
    parser.add_argument("--price_bin_size", type=int, default=40,
                        help="PRICE histogram bin size (default 40)")
    parser.add_argument("--price_statistics_dir", type=str, default=None,
                        help="Path to PRICE statistics directory (default: auto-detect)")
    parser.add_argument("--price_pretrained", action="store_true", default=False,
                        help="(Deprecated) Load finetuned PRICE weights for inference. Use --price_weights_source instead.")
    parser.add_argument("--price_weights_source", type=str, choices=["pretrained", "separate", "joint", "frozen_joint", "joint_frozen_init", "gated_joint", "cross_attn_joint", "bi_cross_attn_joint", "reverse_cross_attn_joint"],
                        default="pretrained",
                        help="Source of PRICE weights: pretrained (original), separate (finetuned on card), joint (jointly finetuned), frozen_joint (finetuned with frozen LLM), joint_frozen_init (jointly finetuned from frozen-joint init), gated_joint (jointly finetuned with learned gate), cross_attn_joint (jointly finetuned with cross-attention), bi_cross_attn_joint (jointly finetuned with bidirectional cross-attention), reverse_cross_attn_joint (jointly finetuned with reverse cross-attention)")
    parser.add_argument("--price_lr", type=float, default=None,
                        help="Learning rate for PRICE model parameters (default: 1e-3 with --price_random_init, else 2.85e-5)")
    parser.add_argument("--freeze_llm", action="store_true", default=False,
                        help="Freeze LLM parameters during llm_price_finetune (only train PRICE + MLP)")
    parser.add_argument("--price_init_frozen_joint", action="store_true", default=False,
                        help="Initialize PRICE from frozen-joint weights instead of pretrained (for PriceFTthenJoint mode)")
    parser.add_argument("--use_price_gate", action="store_true", default=False,
                        help="Use learned gate on PRICE embeddings (GatedJointPrice mode)")
    parser.add_argument("--price_m", action="store_true", default=False,
                        help="Use PRICE_M encoding (61-dim filters with IN/LIKE support via multi-value SpaceSaving)")
    parser.add_argument("--price_s", action="store_true", default=False,
                        help="Use PRICE_S encoding (43-dim, IN/LIKE via bounding-box range)")
    parser.add_argument("--price_n_parsing", action="store_true", default=False,
                        help="PRICE_N: enable parser rules (NOT push-down, "
                             "disjoint-OR→IN, date literals, atom tagging).")
    parser.add_argument("--price_n_filter", action="store_true", default=False,
                        help="PRICE_N: 75-dim filter token (10 IN slots + tail "
                             "+ null bits). Mutually exclusive with --price_s, --price_m.")
    parser.add_argument("--price_n_fanout", action="store_true", default=False,
                        help="PRICE_N: 42-dim fanout token (orphan_fraction "
                             "+ outer_preserve_flag).")
    parser.add_argument("--price_n_pairwise", action="store_true", default=False,
                        help="PRICE_N: enable 129-dim pairwise intra-table "
                             "filter token (5th token type).")
    parser.add_argument("--price_n", action="store_true", default=False,
                        help="PRICE_N shorthand: equivalent to "
                             "--price_n_parsing --price_n_filter "
                             "--price_n_fanout --price_n_pairwise.")
    parser.add_argument("--no_llm_residual", action="store_true", default=False,
                        help="Disable the LLM-residual fusion path. When set, "
                             "the PRICE statistics-core embedding (from the OR "
                             "Transformer in PRICE_N, or the filter_encoder CLS "
                             "for base/S/M) goes directly to the prediction MLP "
                             "or cross-attention with query plan embeddings, "
                             "without merging with LLM-residual embeddings. "
                             "Default: LLM residual fusion is active (current behavior).")
    parser.add_argument("--price_n_or", action="store_true", default=False,
                        help="PRICE_N DNF expansion: expand mixed-column OR blocks into "
                             "multiple DNF clauses (up to --price_n_or_max_clauses), each "
                             "encoded independently by scale_encoder + filter_encoder, then "
                             "aggregated by the OR Transformer. When off (default), "
                             "mixed-column ORs are routed to LLM residual. The OR Transformer "
                             "module is always present in the model when any PRICE_N structural "
                             "flag is enabled; this flag controls only the parser-side expansion.")
    parser.add_argument("--price_n_or_max_clauses", type=int, default=16,
                        help="Maximum DNF clauses per query for OR Transformer batching "
                             "(default 16). Queries that would exceed this are sent to LLM residual.")
    parser.add_argument("--price_max_n_pairwise_intra", type=int, default=8,
                        help="Pad pairwise intra-table tokens to this count.")
    parser.add_argument("--price_random_init", action="store_true", default=False,
                        help="Initialize PRICE with random weights instead of pretrained")
    parser.add_argument("--price_n_layers", type=int, default=6,
                        help="Number of transformer blocks per PRICE encoder (default 6, pretrained uses 6)")
    parser.add_argument("--price_n_embd", type=int, default=256,
                        help="PRICE embedding dimension (default 256, pretrained uses 256)")
    parser.add_argument("--price_n_heads", type=int, default=8,
                        help="PRICE attention heads (default 8, must divide n_embd evenly)")
    parser.add_argument("--price_ffn_ratio", type=float, default=4.0,
                        help="PRICE FFN expansion ratio (default 4.0, pretrained uses 4)")
    parser.add_argument("--freeze_all_price", action="store_true", default=False,
                        help="Freeze ALL PRICE parameters during joint finetuning (LLMOnly control)")
    parser.add_argument("--freeze_price_encoder", action="store_true", default=False,
                        help="Freeze PRICE encoder blocks during joint finetuning (only train len_net, linear, elu)")
    parser.add_argument("--unfreeze_last_n_blocks", type=int, default=0,
                        help="When freeze_price_encoder is set, unfreeze the last N encoder blocks (0=freeze all encoder blocks)")
    parser.add_argument("--early_stop_patience", type=int, default=0,
                        help="Stop training if val p90 Q-error doesn't improve for N epochs (0=disabled)")
    parser.add_argument("--early_stop_after_epoch", type=int, default=0,
                        help="Only start early stopping check after this epoch (e.g., 10 to skip warmup)")
    parser.add_argument("--freeze_llm_until_epoch", type=int, default=0,
                        help="Freeze LLM LoRA params for the first N epochs, only train PRICE/cross-attn (0=disabled)")
    parser.add_argument("--checkpoint_interval", type=int, default=0,
                        help="Save checkpoint every N epochs during finetuning (0=no checkpoints)")
    parser.add_argument("--subdir_tag", type=str, default="",
                        help="When set, route weights/checkpoints into this subdir under the usual location "
                             "(e.g. 'model_selection' → finetuned_models/{db}/model_selection/... and "
                             "finetuned_models/{db}/checkpoints/model_selection/...).")
    parser.add_argument("--resume_checkpoint", type=str, default="",
                        help="Path to checkpoint file to resume finetuning from")
    parser.add_argument("--lr_schedule", type=str, default="step", choices=["step", "cosine", "warmup_cosine"],
                        help="Learning rate schedule: step (StepLR), cosine (CosineAnnealingLR), or warmup_cosine (linear warmup + cosine)")
    parser.add_argument("--warmup_epochs", type=int, default=3,
                        help="Number of warmup epochs for warmup_cosine schedule (default 3)")
    parser.add_argument("--price_warmup_epochs", type=int, default=10,
                        help="Number of PRICE warmup epochs at high LR before dropping to finetune LR (default 10)")
    parser.add_argument("--price_lr_schedule", type=str, default=None, choices=["step", "cosine", "warmup_cosine"],
                        help="Separate LR schedule for PRICE optimizer (default: same as --lr_schedule)")
    parser.add_argument("--ft_batch_size", type=int, default=16,
                        help="Batch size used during finetuning (for locating weight files during inference)")
    parser.add_argument("--ft_num_epoch", type=int, default=0,
                        help="Finetuning epoch count (used by inference to locate weight files)")
    # Field removal arguments for query plan ablation studies
    parser.add_argument("--removed_fields", type=str, default=None,
                        help="Comma-separated list of field categories to remove from query plans. "
                             "Valid options: operator_structure_and_config, cost, cardinality, "
                             "conditions_and_filters, metadata_and_config. "
                             "Note: 'runtime' fields are ALWAYS removed automatically.")
    parser.add_argument("--grad_accum_steps", type=int, default=1,
                        help="Gradient accumulation steps. Effective batch = batch_size * grad_accum_steps. "
                             "Reduces GPU memory by processing smaller micro-batches (default: 1 = no accumulation)")
    # Cross-attention fusion arguments (Mode 11)
    parser.add_argument("--use_cross_attention", action="store_true", default=False,
                        help="Use cross-attention fusion: PRICE tokens attend to LLM hidden states")
    # Bidirectional cross-attention fusion arguments (Mode 12)
    parser.add_argument("--use_bi_cross_attention", action="store_true", default=False,
                        help="Use bidirectional cross-attention fusion: PRICE<->LLM attend to each other")
    # Reverse cross-attention fusion arguments (Mode 13)
    parser.add_argument("--use_reverse_cross_attention", action="store_true", default=False,
                        help="Use reverse cross-attention fusion: LLM tokens attend to PRICE tokens")
    parser.add_argument("--n_cross_layers", type=int, default=2,
                        help="Number of cross-attention layers (default 2)")
    parser.add_argument("--cross_attn_lr", type=float, default=None,
                        help="Learning rate for cross-attention layers (default: same as main learning_rate)")
    parser.add_argument("--retrain_mlp", action="store_true", default=False,
                        help="Pre-compute cross-attn embeddings, then train fresh MLP from scratch")
    parser.add_argument("--refined_pool", action="store_true", default=False,
                        help="Use refined (cross-attn enriched) LLM pooled embedding instead of original")
    parser.add_argument("--triple_concat", action="store_true", default=False,
                        help="Concatenate original LLM + refined LLM + PRICE embeddings (BiCross only)")
    parser.add_argument("--inflate_price", action="store_true", default=False,
                        help="Project PRICE up to LLM dim for BiCross; output = concat(updated_LLM, updated_PRICE) at 2*LLM_dim")

    args = parser.parse_args()

    # PRICE_N shorthand: --price_n sets all four orthogonal flags.
    if args.price_n:
        args.price_n_parsing = True
        args.price_n_filter = True
        args.price_n_fanout = True
        args.price_n_pairwise = True

    # Mutual exclusion: --price_s, --price_m, --price_n_filter all change filter_dim.
    if sum([args.price_s, args.price_m, args.price_n_filter]) > 1:
        parser.error(
            "--price_s, --price_m, --price_n_filter are mutually exclusive "
            "(they all change filter_dim).")

    # Backward compat: --price_pretrained maps to price_weights_source="joint"
    if args.price_pretrained and args.price_weights_source == "pretrained":
        args.price_weights_source = "joint"

    # Validation: price_finetune requires --card
    if args.algo == "price_finetune" and not args.card:
        parser.error("--algo price_finetune requires --card")

    # Canonical workload prefix for shared model files.
    # IMDB-based workloads (syn, job_full, jobm) share the same training data
    # as 'job', so finetuned models are identical and should use the same name.
    _CANONICAL_MAP = {'syn': 'job', 'job_full': 'job', 'jobm': 'job'}
    canonical_wls = []
    seen = set()
    for wl in args.workloads_train:
        cwl = _CANONICAL_MAP.get(wl, wl)
        if cwl not in seen:
            seen.add(cwl)
            canonical_wls.append(cwl)
    wl_joined = '-'.join(canonical_wls)
    # Truncate long workload strings to avoid exceeding filesystem filename limits (255 chars)
    if len(wl_joined) > 80:
        import hashlib
        wl_hash = hashlib.md5(wl_joined.encode()).hexdigest()[:8]
        test_tag = f"_test-{args.workload_test}" if args.workload_test else ""
        wl_joined = f"{len(canonical_wls)}dbs_{wl_hash}{test_tag}"
    args.canonical_wl_prefix = wl_joined

    return args


def setup_loggers(main_log_path, inf_log_path=None):
    # 1) Main logger (always needed)
    main_logger = logging.getLogger("main_logger")
    main_logger.setLevel(logging.INFO)
    main_logger.propagate = False
    main_handler = logging.FileHandler(main_log_path, mode="a")  # append each run
    main_fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    main_handler.setFormatter(main_fmt)
    main_logger.addHandler(main_handler)

    # 2) Inference logger (only for LLM algorithms)
    inference_logger = None
    if inf_log_path:
        inference_logger = logging.getLogger("inference_logger")
        inference_logger.setLevel(logging.INFO)
        inference_logger.propagate = False
        inf_handler = logging.FileHandler(inf_log_path, mode="a")  # append mode
        inf_fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        inf_handler.setFormatter(inf_fmt)
        inference_logger.addHandler(inf_handler)

    return main_logger, inference_logger


def prepare_paths(argsP):
    """ Compute wl_train, wl_test, dp_train, dp_test, dat_path_train, dat_path_test. """
    wl_train_list = argsP.workloads_train
    dp_train_list = argsP.dat_paths_train
    wl_test  = argsP.workload_test
    dp_test  = argsP.dat_path_test

    dat_paths_train_list = []
    for wl_train, dp_train in zip(wl_train_list, dp_train_list):
        is_json = False
        if wl_train == "syn" or wl_train == "job" or wl_train == "job_full" or wl_train == "jobm":
            dat_path_train = f"{dp_train}long_raw_{argsP.db}_imdb.csv"
        elif wl_train == "stats":
            dat_path_train = f"{dp_train}long_raw_{argsP.db}_{wl_train}.csv"

        elif wl_train in ["genome", "financial", "movielens", "geneea", "seznam", "tpc_h",
                          "walmart", "airline", "carcinogenesis", "baseball", "imdb", "accidents",
                          "ssb", "basketball", "employee", "fhnk", "consumer", "tournament", "credit",
                          "hepatitis"]:
            is_json = True

            dat_paths_train_list.extend([
                f"{dp_train}workload_100k_s1_c8220.json",
                f"{dp_train}index_workload_100k_s2_c8220.json"
            ])
        else:
            dat_path_train = f"{dp_train}long_raw_{argsP.db}_{wl_train}.csv"
        if not is_json:
            dat_paths_train_list.append(dat_path_train)
    dat_paths_train_list = list(set(dat_paths_train_list))

    # skipped below
    if not argsP.card:
        if wl_test == "syn" or wl_test == "job" or wl_test == "job_full" or wl_test == "jobm":
            dat_path_test = f"{dp_test}long_raw_{argsP.db}_imdb_{wl_test}.csv"
        elif wl_test == "stats":
            dat_path_test = f"{dp_test}long_raw_{argsP.db}_{wl_test}_statsCEB.csv"
        elif wl_test in ["genome", "financial", "movielens", "geneea", "seznam", "tpc_h",
                          "walmart", "airline", "carcinogenesis", "baseball", "imdb", "accidents",
                          "ssb", "basketball", "employee", "fhnk", "consumer", "tournament", "credit",
                          "hepatitis"]:
            dat_path_test = f"{dp_test}workload_100k_s1_c8220.json"
        elif wl_test in ["synthetic", "job-light"]:
            dat_path_test = f"{dp_test}{wl_test}_c8220.json"
        else:
            dat_path_test = f"{dp_test}long_raw_{argsP.db}_{wl_test}.csv"
    else:
        if wl_test == "syn" or wl_test == "job":
            dat_path_test = f"{dp_test}long_raw_{argsP.db}_imdb_{wl_test}_sub.csv"
        elif wl_test == "job_full":
            dat_path_test = f"{dp_test}long_raw_{argsP.db}_imdb_{wl_test}_sub_selected.csv"
        elif wl_test == "stats":
            dat_path_test = f"{dp_test}long_raw_{argsP.db}_{wl_test}_statsCEB_sub.csv"
        else:
            print("Only syn/job/stats workloads are supported for card")
            exit(1)
    # skipped above
    if "llm" in argsP.algo or argsP.algo == "price_finetune":
        dat_dict = {"ds_info": DatasetInfo({}), "train_js_nodes": None, "train_roots": None, "train_costs": None, "val_js_nodes": None, "val_roots": None, "val_costs": None, "test_js_nodes": None, "test_roots": None, "test_costs": None, "test_ids": None, "val_ids": None, "train_ids": None}
    else:
        print("running get_new")
        dat_dict = get_new(argsP, dp_test ,dat_paths_train_list, dat_path_test)
        print("done running get_new")
    return dat_paths_train_list, dat_path_test, dat_dict

def prepare_non_llm_verbose_embeddings(argsP, trained_model, device, ds_info, dat_dict, 
                                        dat_paths_train_list, dat_path_test, dat_path):
    """
    Prepare embeddings for verbose output for non-LLM algorithms (aimai, qf, e2e_cost).
    Handles both same-file and separate-file scenarios, matching LLM behavior.
    
    Args:
        argsP: Arguments object
        trained_model: Trained model
        device: torch device
        ds_info: Dataset info object
        dat_dict: Dictionary containing roots, costs, and IDs
        dat_paths_train_list: List of training data paths
        dat_path_test: Test data path
        dat_path: Base data path (for histogram/table sample)
    
    Returns:
        train_embeddings_verbose: numpy array of training embeddings for KNN
    """
    from trainer import generate_and_save_embeddings_for_dataset, get_embedding_file_path
    import numpy as np
    
    print(f"  Generating embeddings for {argsP.algo}...")
    
    # Check if train and test come from the same file
    same_file = (len(dat_paths_train_list) == 1 and dat_paths_train_list[0] == dat_path_test)
    
    if same_file:
        # Case 1: Train/Val/Test all from same file - cache once and split
        print(f"  Train/Val/Test from same file: {dat_path_test}")
        
        total_roots = dat_dict.get('total_roots', None)
        total_costs = dat_dict.get('total_costs', None)
        
        if total_roots is not None and total_costs is not None:
            # Generate embedding file path for the single file
            removed_fields = getattr(argsP, 'removed_fields', None)
            embedding_file_path = get_embedding_file_path(
                argsP.algo, dat_path_test, argsP.workloads_train, argsP.workload_test, argsP.seed, removed_fields
            )
            
            # Create dataset for all data
            print(f"  Creating dataset for all {len(total_roots)} samples...")
            full_ds = create_dataset_for_algo(
                argsP.algo, ds_info, total_roots, total_costs, argsP, dat_path
            )
            
            # Generate embeddings for all data (overwrites existing cache)
            all_embeddings = generate_and_save_embeddings_for_dataset(
                trained_model, full_ds, embedding_file_path, device, argsP.algo
            )
            
            # Extract training embeddings for KNN
            train_ids = dat_dict.get('train_ids', None)
            test_ids = dat_dict.get('test_ids', None)
            
            if train_ids is not None:
                train_embeddings_verbose = all_embeddings[train_ids]
                print(f"  Training embeddings for KNN shape: {train_embeddings_verbose.shape}")
            else:
                print("  Warning: train_ids not found")
                train_embeddings_verbose = None
            
            # Store metadata for verbose output
            argsP.test_plan_file_path = dat_path_test
            argsP.test_embedding_cache_path = embedding_file_path
            
            # Set test_original_indices for index mapping (same as LLM logic)
            if test_ids is not None:
                argsP.test_original_indices = test_ids
                print(f"  Set test_original_indices for index mapping")
            
            return train_embeddings_verbose
        else:
            print("  Warning: total_roots not available - skipping embedding generation")
            return None
    
    else:
        # Case 2: Separate train and test files - cache each separately
        print(f"  Separate train files and test file")
        print(f"  Train files: {dat_paths_train_list}")
        print(f"  Test file: {dat_path_test}")
        
        # Generate embeddings for each training file and collect train embeddings
        train_embeddings_list = []
        for dat_path_train in dat_paths_train_list:
            print(f"    Processing train file: {dat_path_train}")
            
            # Read the training file to get roots and costs
            if dat_path_train.endswith('.json'):
                df_train = pd.read_json(dat_path_train)
            else:
                df_train = pd.read_csv(dat_path_train)
            
            # Get roots and costs for this training file
            from evaluation.dataset_utils import df2nodes, get_costs
            train_roots, train_js_nodes, train_idxs = df2nodes(df_train, db=argsP.db)
            train_costs = get_costs(train_js_nodes, argsP.card, db=argsP.db)
            
            # Generate embedding file path for this training file
            removed_fields = getattr(argsP, 'removed_fields', None)
            embedding_file_path_train = get_embedding_file_path(
                argsP.algo, dat_path_train, argsP.workloads_train, argsP.workload_test, argsP.seed, removed_fields
            )
            
            # Create dataset for this training file
            train_ds = create_dataset_for_algo(
                argsP.algo, ds_info, train_roots, train_costs, argsP, dat_path_train
            )
            
            # Generate embeddings (overwrites existing cache)
            train_embeddings = generate_and_save_embeddings_for_dataset(
                trained_model, train_ds, embedding_file_path_train, device, argsP.algo
            )
            
            train_embeddings_list.append(train_embeddings)
        
        # Concatenate all training embeddings
        if train_embeddings_list:
            train_embeddings_verbose = np.concatenate(train_embeddings_list, axis=0)
            print(f"  Combined training embeddings shape: {train_embeddings_verbose.shape}")
        else:
            train_embeddings_verbose = None
        
        # Generate embeddings for test file separately
        print(f"    Processing test file: {dat_path_test}")
        
        # Read test file to get roots and costs
        if dat_path_test.endswith('.json'):
            df_test = pd.read_json(dat_path_test)
        else:
            df_test = pd.read_csv(dat_path_test)
        
        from evaluation.dataset_utils import df2nodes, get_costs
        test_roots, test_js_nodes, test_idxs = df2nodes(df_test, db=argsP.db)
        test_costs = get_costs(test_js_nodes, argsP.card, db=argsP.db)
        
        # Generate embedding file path for test file
        removed_fields = getattr(argsP, 'removed_fields', None)
        embedding_file_path_test = get_embedding_file_path(
            argsP.algo, dat_path_test, argsP.workloads_train, argsP.workload_test, argsP.seed, removed_fields
        )
        
        # Create dataset for test file
        test_ds_full = create_dataset_for_algo(
            argsP.algo, ds_info, test_roots, test_costs, argsP, dat_path_test
        )
        
        # Generate embeddings for test (overwrites existing cache)
        test_embeddings_full = generate_and_save_embeddings_for_dataset(
            trained_model, test_ds_full, embedding_file_path_test, device, argsP.algo
        )
        
        # Store metadata for verbose output
        argsP.test_plan_file_path = dat_path_test
        argsP.test_embedding_cache_path = embedding_file_path_test
        
        # Do NOT set test_original_indices in this case (same as LLM logic)
        
        return train_embeddings_verbose


def create_dataset_for_algo(algo, ds_info, roots, costs, argsP, dat_path, query_ids=None):
    """
    Helper function to create a dataset for a specific algorithm and set of roots/costs.
    This avoids code duplication when creating datasets for different splits or full data.
    
    Args:
        algo: Algorithm name ('aimai', 'qf', 'e2e_cost')
        ds_info: Dataset info object
        roots: List of tree roots
        costs: List of costs/cardinalities
        argsP: Arguments object
        dat_path: Data path (for qf histogram and table sample)
        query_ids: Optional query IDs
    
    Returns:
        PyTorch Dataset
    """
    if algo == "aimai":
        return get_aimeetsai_ds(ds_info, roots, costs, argsP)
    
    elif algo == "qf":
        from algorithms.queryformer.dataset_utils import Encoding, get_hist_file, get_job_table_sample, QueryFormerDataset
        encoding = Encoding(ds_info)
        data_path = Path(dat_path)
        data_dir = data_path.parent if data_path.suffix == ".csv" else data_path
        # Metadata lives one level above the engine directory (shared by postgres/ and duckdb/)
        metadata_dir = data_dir.parent
        hist_file = get_hist_file(str(metadata_dir / 'histogram_string.csv'))
        table_sample = get_job_table_sample(str(metadata_dir / 'long_df'))
        
        if argsP.workload_test in ["syn", "job", "job_full", "jobm", "tpch", "stats"]:
            max_node = 35
        elif argsP.workload_test == "tpcds":
            max_node = 120
        else:
            max_node = 35
        
        return QueryFormerDataset(
            hist_file=hist_file,
            table_sample=table_sample,
            nodes=roots,
            encoding=encoding,
            labels=costs,
            ds_info=ds_info,
            max_node=max_node,
            query_ids=query_ids,
            args=argsP
        )
    
    elif algo == "e2e_cost":
        from algorithms.e2e_cost.e2e_dataset import E2E_Dataset, Encoding, Constants
        encoding = Encoding(ds_info)
        if not hasattr(ds_info, 'constants'):
            ds_info.constants = Constants(ds_info)
        
        if argsP.workload_test in ["syn", "job", "job_full", "jobm", "tpch", "stats"]:
            max_node = 35
        elif argsP.workload_test == "tpcds":
            max_node = 120
        else:
            max_node = 35
        
        return E2E_Dataset(
            nodes=roots,
            labels=costs,
            encoding=encoding,
            max_node=max_node,
            ds_info=ds_info,
            args=argsP
        )
    
    else:
        raise ValueError(f"create_dataset_for_algo not implemented for algo: {algo}")


def load_data(argsP, dat_path, dat_paths_train_list, dat_path_test, dat_dict, predictor=None, llm_collate=None):
    ds_info = dat_dict['ds_info']

    train_js_nodes = dat_dict['train_js_nodes']
    train_roots = dat_dict['train_roots']
    train_costs = dat_dict['train_costs']
    train_query_ids = dat_dict.get('train_query_ids', None)

    val_js_nodes = dat_dict['val_js_nodes']
    val_roots = dat_dict['val_roots']
    val_costs = dat_dict['val_costs']
    val_query_ids = dat_dict.get('val_query_ids', None)

    test_js_nodes = dat_dict['test_js_nodes']
    test_roots = dat_dict['test_roots']
    test_costs = dat_dict['test_costs']
    test_query_ids = dat_dict.get('test_query_ids', None)

    if argsP.algo == "qf":
        from algorithms.queryformer.dataset_utils import collator
        # Use helper function to create datasets
        ds = create_dataset_for_algo('qf', ds_info, train_roots, train_costs, argsP, dat_path, train_query_ids)
        val_ds = create_dataset_for_algo('qf', ds_info, val_roots, val_costs, argsP, dat_path, val_query_ids)
        test_ds = create_dataset_for_algo('qf', ds_info, test_roots, test_costs, argsP, dat_path, test_query_ids)

        train_loader = DataLoader(dataset=ds,
                                batch_size = argsP.batch_size,
                                collate_fn=collator,
                                shuffle=True,
                                generator=torch.Generator().manual_seed(argsP.seed if hasattr(argsP, 'seed') else 42))
        val_loader = DataLoader(dataset=val_ds,
                                batch_size = argsP.batch_size,
                                collate_fn=collator,
                                shuffle=False)
        test_loader = DataLoader(dataset=test_ds,
                                batch_size = 1,
                                # batch_size = argsP.batch_size,
                                collate_fn=collator,
                                shuffle=False)
    elif argsP.algo == "e2e_cost":
        from algorithms.e2e_cost.e2e_dataset import collator, Constants
        # Ensure constants are set
        if not hasattr(ds_info, 'constants'):
            ds_info.constants = Constants(ds_info)
        
        # Use helper function to create datasets
        ds = create_dataset_for_algo('e2e_cost', ds_info, train_roots, train_costs, argsP, dat_path)
        val_ds = create_dataset_for_algo('e2e_cost', ds_info, val_roots, val_costs, argsP, dat_path)
        test_ds = create_dataset_for_algo('e2e_cost', ds_info, test_roots, test_costs, argsP, dat_path)

        train_loader = DataLoader(dataset=ds,
                                batch_size = argsP.batch_size,
                                collate_fn=collator,
                                shuffle=True,
                                generator=torch.Generator().manual_seed(argsP.seed if hasattr(argsP, 'seed') else 42))
        val_loader = DataLoader(dataset=val_ds,
                                batch_size = argsP.batch_size,
                                collate_fn=collator,
                                shuffle=False)
        test_loader = DataLoader(dataset=test_ds,
                                batch_size = 1,
                                # batch_size = argsP.batch_size,
                                collate_fn=collator,
                                shuffle=False)
    elif argsP.algo in ("aimai", "llm", "llm_stats", "llm_price"):
        if argsP.algo == "aimai":
            # Use helper function to create datasets
            ds = create_dataset_for_algo('aimai', ds_info, train_roots, train_costs, argsP, dat_path)
            val_ds = create_dataset_for_algo('aimai', ds_info, val_roots, val_costs, argsP, dat_path)
            test_ds = create_dataset_for_algo('aimai', ds_info, test_roots, test_costs, argsP, dat_path)
        elif argsP.algo in ("llm", "llm_stats", "llm_price"):
            from utilsLLM import QueryPlanDataset, QueryPlanPredictor, get_llm_ds_from_csv
            ds, val_ds, test_ds, val_costs, test_costs, test_lengths, test_templates = get_llm_ds_from_csv(predictor, dat_paths_train_list, dat_path_test, ds_info, argsP)
            if not argsP.embeddings_exist:
                predictor.to("cpu")
            torch.cuda.empty_cache()

        train_loader = DataLoader(dataset=ds,
                                batch_size = argsP.batch_size,
                                shuffle=True,
                                generator=torch.Generator().manual_seed(argsP.seed if hasattr(argsP, 'seed') else 42))
        val_loader = DataLoader(dataset=val_ds,
                                batch_size = argsP.batch_size,
                                shuffle=False)
        test_loader = DataLoader(dataset=test_ds,
                                batch_size = 1,
                                shuffle=False)
    elif argsP.algo == "llm_finetune":
        from utilsLLM import QueryPlanDataset, QueryPlanPredictor, get_llm_ds_from_csv
        ds, val_ds, test_ds, val_costs, test_costs, test_lengths, test_templates = get_llm_ds_from_csv(predictor, dat_paths_train_list, dat_path_test, ds_info, argsP)
        train_loader = DataLoader(dataset=ds,
                                batch_size = argsP.batch_size,
                                shuffle=True,
                                collate_fn=llm_collate,
                                generator=torch.Generator().manual_seed(argsP.seed if hasattr(argsP, 'seed') else 42))
        val_loader = DataLoader(dataset=val_ds,
                                batch_size = argsP.batch_size,
                                shuffle=False,
                                collate_fn=llm_collate)
        test_loader = DataLoader(dataset=test_ds,
                                batch_size = 1,
                                shuffle=False,
                                collate_fn=llm_collate)
    elif argsP.algo == "llm_price_finetune":
        from utilsLLM import get_llm_price_ds_from_csv
        ds, val_ds, test_ds, val_costs, test_costs, test_lengths, test_templates = get_llm_price_ds_from_csv(predictor, dat_paths_train_list, dat_path_test, ds_info, argsP)
        train_loader = DataLoader(dataset=ds,
                                batch_size = argsP.batch_size,
                                shuffle=True,
                                collate_fn=llm_collate,
                                generator=torch.Generator().manual_seed(argsP.seed if hasattr(argsP, 'seed') else 42))
        val_loader = DataLoader(dataset=val_ds,
                                batch_size = argsP.batch_size,
                                shuffle=False,
                                collate_fn=llm_collate)
        test_loader = DataLoader(dataset=test_ds,
                                batch_size = 1,
                                shuffle=False,
                                collate_fn=llm_collate)
    elif argsP.algo == "bao" or argsP.algo == "postgres":
        return ds_info, train_roots, train_js_nodes, train_costs, \
           val_roots,   val_js_nodes,   val_costs,   \
           test_roots,  test_js_nodes,  test_costs,  \
           None,  None,  None,  \
           None,  None,  None,  \
           (test_lengths if "llm" in argsP.algo else None), \
           (test_templates if "llm" in argsP.algo else None), \
           None  # test_texts (matching the main return statement)    
    

    return ds_info, train_roots, train_js_nodes, train_costs, \
           val_roots,   val_js_nodes,   val_costs,   \
           test_roots,  test_js_nodes,  test_costs,  \
           ds,  val_ds,  test_ds,  \
           train_loader,  val_loader,  test_loader,  \
           (test_lengths if "llm" in argsP.algo else None), \
           (test_templates if "llm" in argsP.algo else None), \
           None  # test_texts no longer collected since we don't save test_texts when getting verbose information