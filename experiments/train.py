import os
import re
import pandas as pd
import torch
import sys
import torch.nn as nn
import argparse
import torch.nn.init as init
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, TensorDataset
import utilsTrain
from huggingface_hub import HfApi, login
# Ensure experiments/ dir is on path (for models/ package and utilsTrain)
_this_dir = os.path.dirname(os.path.abspath(__file__))
if _this_dir not in sys.path:
    sys.path.insert(0, _this_dir)
sys.path.append('../evaluation/')
from dataset_utils import *
from time import time as timer
import numpy as np
import csv

argsP = utilsTrain.parse_args()
log_dir = os.path.dirname(argsP.log_file)
os.makedirs(log_dir, exist_ok=True)

# Only create inference logger for LLM algorithms
if "llm" in argsP.algo:
    main_logger, inference_logger = utilsTrain.setup_loggers(argsP.log_file, argsP.log_file.replace(".log", "_inference.log"))
    argsP.main_logger = main_logger
    argsP.inference_logger = inference_logger
else:
    main_logger, inference_logger = utilsTrain.setup_loggers(argsP.log_file)
    argsP.main_logger = main_logger
    argsP.inference_logger = None

# Get Hugging Face token from environment variable
token = os.getenv("HF_TOKEN")

if os.environ.get("SKIP_HF_AUTH") != "1":
    try:
        # Works if HF_TOKEN is set or you've previously run `hf auth login`
        HfApi().whoami()
    except Exception:
        if not argsP.embeddings_exist and argsP.algo != "price_finetune":
          if token:
              login(token=token)  # will also cache it locally
          else:
              raise RuntimeError(
                  "No Hugging Face token found. Set HF_TOKEN environment variable or run `hf auth login`."
              )


db = argsP.db
dat_path = argsP.dat_path_test
dat_paths_train_list, dat_path_test, dat_dict = utilsTrain.prepare_paths(argsP)

if argsP.algo not in ("llm_finetune", "llm_price_finetune", "price_finetune"):
    output_dir = os.path.dirname(argsP.output_dir_qerror)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
# ─── Early retrain_mlp cache check: skip LLM/data loading if embeddings cached ──
_retrain_mlp_cache_hit = False
if (argsP.algo == "llm_price" and getattr(argsP, 'retrain_mlp', False) and
    getattr(argsP, 'price_weights_source', 'pretrained') in ("cross_attn_joint", "bi_cross_attn_joint", "reverse_cross_attn_joint")):
    # Compute the cache path from args alone (same logic as the model construction section)
    _pws = argsP.price_weights_source
    _ft_bs = getattr(argsP, 'ft_batch_size', 16)
    _task_str = "card" if argsP.card else "time"
    _pm = "_priceM" if getattr(argsP, 'price_m', False) else ""
    _ps = "_priceS" if getattr(argsP, 'price_s', False) else ""
    _ri = "_randInit" if getattr(argsP, 'price_random_init', False) else ""
    _rp = "_refinedPool" if getattr(argsP, 'refined_pool', False) else ""
    _tc = "_tripleConcat" if getattr(argsP, 'triple_concat', False) else ""
    _ip = "_inflatePRICE" if getattr(argsP, 'inflate_price', False) else ""
    _nl = f"_pL{argsP.price_n_layers}" if getattr(argsP, 'price_n_layers', 6) != 6 else ""
    _fr = f"_ffn{argsP.price_ffn_ratio:g}" if getattr(argsP, 'price_ffn_ratio', 4.0) != 4.0 else ""
    _n_cross = getattr(argsP, 'n_cross_layers', 2)
    _nc = f"_cx{_n_cross}" if _n_cross != 2 else ""
    _ft_epochs = getattr(argsP, 'ft_num_epoch', 0)
    _es = f"_e{_ft_epochs}" if _ft_epochs > 0 else ""
    if _pws == "bi_cross_attn_joint":
        _attn = "_biCrossAttn"
    elif _pws == "reverse_cross_attn_joint":
        _attn = "_revCrossAttn"
    else:
        _attn = "_crossAttn"
    _weight_prefix = f"finetuned_models/{argsP.db}/{argsP.canonical_wl_prefix}_{_task_str}_{argsP.llm_pretrained}_{argsP.model_name.replace('/','-')}_b{_ft_bs}{_pm}{_ps}_llm_price{_attn}{_rp}{_tc}{_ip}{_ri}{_nl}{_fr}{_nc}{_es}"
    _test_tag = f"_test-{argsP.workload_test}" if getattr(argsP, 'workload_test', '') else ""
    _early_cache_path = f"{_weight_prefix}{_test_tag}_retrainMLP_embeddings.pt"
    if os.path.exists(_early_cache_path):
        print(f"[retrain_mlp] Embedding cache exists: {_early_cache_path}")
        print(f"[retrain_mlp] Skipping LLM loading, data loading, and model construction")
        _retrain_mlp_cache_hit = True

# Print CUDA availability (optional, for verification)
print(f"Cuda available? {torch.cuda.is_available()}")
if "llm" in argsP.algo and not _retrain_mlp_cache_hit:
  if not argsP.embeddings_exist:
    from utilsLLM import QueryPlanDataset, QueryPlanPredictor, get_llm_ds_from_csv
    
    LLM = QueryPlanPredictor(
        argsP.model_name,
        argsP.llm_mode,
        use_sliding_window=True,
        window_stride_ratio=0.8,
        quantification=argsP.quantification
    )
    device = LLM.model.device if hasattr(LLM.model, 'device') else torch.device("cuda" if torch.cuda.is_available() else "cpu")
    LLM.to(device)
    # Configure stats token injection settings (if enabled)
    LLM.stats_token_dim = int(getattr(argsP, "stats_token_dim", 5))
    LLM.stats_token_str = getattr(argsP, "stats_token_str", "[STAT]")
    if argsP.algo == "llm_price" and argsP.llm_pretrained:
      # Load finetuned LLM weights — source depends on price_weights_source
      task_str = "card" if argsP.card else "time"
      pws = getattr(argsP, 'price_weights_source', 'joint')
      ft_bs = getattr(argsP, 'ft_batch_size', 16)
      price_m_suffix = "_priceM" if getattr(argsP, 'price_m', False) else ""
      price_s_suffix = "_priceS" if getattr(argsP, 'price_s', False) else ""
      if pws in ("joint", "joint_frozen_init", "gated_joint", "cross_attn_joint", "bi_cross_attn_joint", "reverse_cross_attn_joint"):
        # Joint finetuning: LLM weights saved with _llm_price_llm suffix
        frozen_init_suffix = "_frozenInit" if pws == "joint_frozen_init" else ""
        gated_suffix = "_gated" if pws == "gated_joint" else ""
        cross_attn_suffix = "_crossAttn" if pws == "cross_attn_joint" else ""
        bi_cross_attn_suffix = "_biCrossAttn" if pws == "bi_cross_attn_joint" else ""
        rev_cross_attn_suffix = "_revCrossAttn" if pws == "reverse_cross_attn_joint" else ""
        refined_pool_suffix = "_refinedPool" if getattr(argsP, 'refined_pool', False) else ""
        triple_concat_suffix = "_tripleConcat" if getattr(argsP, 'triple_concat', False) else ""
        inflate_price_suffix = "_inflatePRICE" if getattr(argsP, 'inflate_price', False) else ""
        rand_init_suffix = "_randInit" if getattr(argsP, 'price_random_init', False) else ""
        n_layers_suffix = f"_pL{argsP.price_n_layers}" if getattr(argsP, 'price_n_layers', 6) != 6 else ""
        ffn_ratio_suffix = f"_ffn{argsP.price_ffn_ratio:g}" if getattr(argsP, 'price_ffn_ratio', 4.0) != 4.0 else ""
        n_cross_suffix = f"_cx{argsP.n_cross_layers}" if pws in ("cross_attn_joint", "bi_cross_attn_joint", "reverse_cross_attn_joint") and getattr(argsP, 'n_cross_layers', 2) != 2 else ""
        ft_epochs = getattr(argsP, 'ft_num_epoch', 0)
        epoch_suffix = f"_e{ft_epochs}" if ft_epochs > 0 else ""
        llm_path = f"finetuned_models/{argsP.db}/{argsP.canonical_wl_prefix}_{task_str}_{argsP.llm_pretrained}_{argsP.model_name.replace('/','-')}_b{ft_bs}{price_m_suffix}{price_s_suffix}_llm_price{frozen_init_suffix}{gated_suffix}{cross_attn_suffix}{bi_cross_attn_suffix}{rev_cross_attn_suffix}{refined_pool_suffix}{triple_concat_suffix}{inflate_price_suffix}{rand_init_suffix}{n_layers_suffix}{ffn_ratio_suffix}{n_cross_suffix}{epoch_suffix}_llm.pt"
      else:
        # Standalone LLM finetune: weights saved with _llm suffix
        llm_path = f"finetuned_models/{argsP.db}/{argsP.canonical_wl_prefix}_{task_str}_{argsP.llm_pretrained}_{argsP.model_name.replace('/','-')}_b{ft_bs}_llm.pt"
      state_dict = torch.load(llm_path, map_location=device)
      try:
        result = LLM.model.load_state_dict(state_dict, strict=False)
        # Diagnostic: detect silent failures from key mismatches
        n_loaded = len(state_dict) - len(result.unexpected_keys)
        print(f"[LLM weight load] Keys in state_dict: {len(state_dict)}, loaded: {n_loaded}, "
              f"missing: {len(result.missing_keys)}, unexpected: {len(result.unexpected_keys)}")
        if len(result.unexpected_keys) > 0:
          print(f"[LLM weight load] WARNING: {len(result.unexpected_keys)} unexpected keys (first 5): {result.unexpected_keys[:5]}")
        if n_loaded == 0:
          print(f"[LLM weight load] ERROR: No keys loaded! Model keys and state_dict keys may have different prefixes.")
          print(f"  Model key sample: {list(LLM.model.state_dict().keys())[:3]}")
          print(f"  State dict key sample: {list(state_dict.keys())[:3]}")
      except RuntimeError as e:
        raise
      print(f"Loaded LLM weights from {llm_path} (price_weights_source={pws})")
    elif argsP.algo == "llm" and argsP.llm_pretrained:
      stats_suffix = ""
      if getattr(argsP, "stats_token_inject", False):
        stats_mode = getattr(argsP, "stats_token_mode", "per_column")
        stats_suffix = f"_statTok-{stats_mode}"
      ft_bs = getattr(argsP, 'ft_batch_size', 16)
      llm_path = f"finetuned_models/{argsP.db}/{argsP.canonical_wl_prefix}_{argsP.llm_pretrained_task}_{argsP.llm_pretrained}_{argsP.model_name.replace('/','-')}_b{ft_bs}{stats_suffix}_llm.pt"
      state_dict = torch.load(llm_path, map_location=device)
      try:
        result = LLM.model.load_state_dict(state_dict, strict=False)
        n_loaded = len(state_dict) - len(result.unexpected_keys)
        print(f"[LLM weight load] Keys in state_dict: {len(state_dict)}, loaded: {n_loaded}, "
              f"missing: {len(result.missing_keys)}, unexpected: {len(result.unexpected_keys)}")
        if len(result.unexpected_keys) > 0:
          print(f"[LLM weight load] WARNING: {len(result.unexpected_keys)} unexpected keys (first 5): {result.unexpected_keys[:5]}")
        if n_loaded == 0:
          print(f"[LLM weight load] ERROR: No keys loaded! Model keys and state_dict keys may have different prefixes.")
          print(f"  Model key sample: {list(LLM.model.state_dict().keys())[:3]}")
          print(f"  State dict key sample: {list(state_dict.keys())[:3]}")
      except RuntimeError as e:
        # Common case: stats token added during finetune, tokenizer size mismatch
        if "size mismatch" in str(e) and "tok_embeddings.weight" in str(e):
          try:
            LLM._ensure_stats_token(getattr(argsP, "stats_token_str", "[STAT]"))
            LLM.model.load_state_dict(state_dict, strict=False)
          except Exception:
            raise
        else:
          raise
      print(f"Loaded LLM weights from {llm_path}")
  else:
    LLM = None


# Set up device and seed
device = 'cuda' if torch.cuda.is_available() else 'cpu'
argsP.device = device
torch.manual_seed(argsP.seed)
torch.cuda.manual_seed_all(argsP.seed)
torch.backends.cudnn.deterministic = True 
torch.backends.cudnn.benchmark = False

def llm_collate(batch):
    # batch is a list of tuples:
    # - (text, cost) OR (text, stats_vecs, cost)
    if len(batch[0]) == 3:
        texts, stats_vecs, costs = zip(*batch)
        costs_tensor = torch.tensor(
            costs, dtype=torch.float32, device=device
        ).unsqueeze(1)
        return (list(texts), list(stats_vecs)), costs_tensor
    texts, costs = zip(*batch)
    costs_tensor = torch.tensor(
        costs, dtype=torch.float32, device=device
    ).unsqueeze(1)
    return list(texts), costs_tensor

def llm_price_collate(batch):
    """Collate function for LLMPriceDataset.
    Each item: (text, price_feat, pad_mask, njc, nfo, ntb, nfc, label)
    Returns: ((texts, price_feats, pad_masks, njcs, nfos, ntbs, nfcs), labels_tensor)
    """
    texts, pf, pm, njc, nfo, ntb, nfc, labels = zip(*batch)
    labels_tensor = torch.tensor(labels, dtype=torch.float32, device=device).unsqueeze(1)
    price_feats = torch.stack([f if isinstance(f, torch.Tensor) else torch.tensor(f, dtype=torch.float32) for f in pf]).float().to(device)
    pad_masks = torch.stack([m if isinstance(m, torch.Tensor) else torch.tensor(m) for m in pm]).float().to(device)
    njcs = torch.tensor(njc, dtype=torch.float32, device=device).unsqueeze(1)
    nfos = torch.tensor(nfo, dtype=torch.float32, device=device).unsqueeze(1)
    ntbs = torch.tensor(ntb, dtype=torch.float32, device=device).unsqueeze(1)
    nfcs = torch.tensor(nfc, dtype=torch.float32, device=device).unsqueeze(1)
    return (list(texts), price_feats, pad_masks, njcs, nfos, ntbs, nfcs), labels_tensor

def price_only_collate(batch):
    """Collate function for PriceOnlyDataset.
    Each item: (price_feat, pg_est_card, pad_mask, njc, nfo, ntb, nfc, label)
    Returns: ((price_feats, pg_est_cards, pad_masks, njcs, nfos, ntbs, nfcs), labels_tensor)
    """
    pf, pgc, pm, njc, nfo, ntb, nfc, labels = zip(*batch)
    labels_tensor = torch.tensor(labels, dtype=torch.float32, device=device).unsqueeze(1)
    price_feats = torch.stack([f if isinstance(f, torch.Tensor) else torch.tensor(f, dtype=torch.float32) for f in pf]).float().to(device)
    # pg_est_card: apply log(pg_est_card+1)+1 normalization
    pgc_raw = torch.tensor(pgc, dtype=torch.float32, device=device).unsqueeze(1)
    pg_est_cards = torch.log(pgc_raw + 1) + 1
    pad_masks = torch.stack([m if isinstance(m, torch.Tensor) else torch.tensor(m) for m in pm]).float().to(device)
    njcs = torch.tensor(njc, dtype=torch.float32, device=device).unsqueeze(1)
    nfos = torch.tensor(nfo, dtype=torch.float32, device=device).unsqueeze(1)
    ntbs = torch.tensor(ntb, dtype=torch.float32, device=device).unsqueeze(1)
    nfcs = torch.tensor(nfc, dtype=torch.float32, device=device).unsqueeze(1)
    return (price_feats, pg_est_cards, pad_masks, njcs, nfos, ntbs, nfcs), labels_tensor

def frozen_llm_price_collate(batch):
    """Collate function for FrozenLLMPriceDataset.
    Each item: (llm_emb, price_feat, pad_mask, njc, nfo, ntb, nfc, label)
    Returns: ((llm_embs, price_feats, pad_masks, njcs, nfos, ntbs, nfcs), labels_tensor)
    """
    llm_embs, pf, pm, njc, nfo, ntb, nfc, labels = zip(*batch)
    labels_tensor = torch.tensor(labels, dtype=torch.float32, device=device).unsqueeze(1)
    llm_embs_tensor = torch.stack([e if isinstance(e, torch.Tensor) else torch.tensor(e, dtype=torch.float32) for e in llm_embs]).float().to(device)
    price_feats = torch.stack([f if isinstance(f, torch.Tensor) else torch.tensor(f, dtype=torch.float32) for f in pf]).float().to(device)
    pad_masks = torch.stack([m if isinstance(m, torch.Tensor) else torch.tensor(m) for m in pm]).float().to(device)
    njcs = torch.tensor(njc, dtype=torch.float32, device=device).unsqueeze(1)
    nfos = torch.tensor(nfo, dtype=torch.float32, device=device).unsqueeze(1)
    ntbs = torch.tensor(ntb, dtype=torch.float32, device=device).unsqueeze(1)
    nfcs = torch.tensor(nfc, dtype=torch.float32, device=device).unsqueeze(1)
    return (llm_embs_tensor, price_feats, pad_masks, njcs, nfos, ntbs, nfcs), labels_tensor

if _retrain_mlp_cache_hit:
  # Skip all data loading and model construction — go straight to retrain_mlp
  from trainer import *
  device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
  argsP.device = device
  torch.manual_seed(argsP.seed)
  torch.cuda.manual_seed_all(argsP.seed)
  torch.backends.cudnn.deterministic = True
  torch.backends.cudnn.benchmark = False

  # Load cached embeddings
  print(f"[retrain_mlp] Loading cached embeddings from {_early_cache_path}")
  _cached = torch.load(_early_cache_path, map_location="cpu")
  all_embeddings = _cached["embeddings"]
  all_labels = _cached["labels"]
  for split_name in ("train", "val", "test"):
      print(f"  {split_name}: {all_embeddings[split_name].shape[0]} samples, embed_dim={all_embeddings[split_name].shape[1]}")

  # Build fresh MLP and loaders
  combined_dim = all_embeddings["train"].shape[1]
  model_comb = Prediction(combined_dim, argsP.hid_units)
  print(f"[retrain_mlp] Fresh MLP: input_dim={combined_dim}, hid_units={argsP.hid_units}")

  ds = TensorDataset(all_embeddings["train"], all_labels["train"])
  val_ds = TensorDataset(all_embeddings["val"], all_labels["val"])
  test_ds = TensorDataset(all_embeddings["test"], all_labels["test"])

  train_loader = DataLoader(ds, batch_size=argsP.batch_size, shuffle=True,
                            generator=torch.Generator().manual_seed(argsP.seed))
  val_loader = DataLoader(val_ds, batch_size=argsP.batch_size, shuffle=False)
  test_loader = DataLoader(test_ds, batch_size=1, shuffle=False)

  argsP.algo = "llm_price"
  argsP.embed_size = combined_dim
  print(f"[retrain_mlp] Fast path: skipped LLM/data loading ({argsP.num_epoch} MLP epochs)")

  # Reconstruct ds_info with cost_norm from cache (or fall back to label range)
  ds_info = dat_dict['ds_info']
  from utils import Normalizer
  _cost_norm_data = _cached.get("cost_norm", None)
  if _cost_norm_data:
      ds_info.cost_norm = Normalizer(mini=_cost_norm_data["mini"], maxi=_cost_norm_data["maxi"])
      print(f"[retrain_mlp] Loaded cost_norm from cache: mini={ds_info.cost_norm.mini:.4f}, maxi={ds_info.cost_norm.maxi:.4f}")
  else:
      # Old cache without cost_norm — use label range as approximation
      _all_labels_np = all_labels["train"].numpy().flatten()
      ds_info.cost_norm = Normalizer(mini=float(_all_labels_np.min()), maxi=float(_all_labels_np.max()))
      print(f"[retrain_mlp] WARNING: Old cache without cost_norm, using label range: mini={ds_info.cost_norm.mini:.4f}, maxi={ds_info.cost_norm.maxi:.4f}")
  test_lengths = test_templates = None
  train_roots = train_js_nodes = train_costs = None
  val_roots = val_js_nodes = val_costs_raw = None
  test_roots = test_js_nodes = test_costs_raw = None
  crit = nn.MSELoss()
  price_finetune_optimizer = None
  price_finetune_scheduler = None
  _ckpt_prefix = None
  argsP.checkpoint_prefix = None
  start_epoch = 0

elif argsP.algo == "price_finetune":
  from utilsLLM import get_price_only_ds_from_csv
  ds, val_ds, test_ds, val_costs, test_costs = get_price_only_ds_from_csv(
      dat_paths_train_list, dat_path_test, dat_dict['ds_info'], argsP
  )
  ds_info = dat_dict['ds_info']
  train_loader = DataLoader(dataset=ds, batch_size=argsP.batch_size, shuffle=True,
                            collate_fn=price_only_collate,
                            generator=torch.Generator().manual_seed(argsP.seed))
  val_loader = DataLoader(dataset=val_ds, batch_size=argsP.batch_size, shuffle=False,
                          collate_fn=price_only_collate)
  test_loader = DataLoader(dataset=test_ds, batch_size=1, shuffle=False,
                           collate_fn=price_only_collate)
  # Set dummy values for variables expected later
  train_roots = train_js_nodes = train_costs = None
  val_roots = val_js_nodes = val_costs_raw = None
  test_roots = test_js_nodes = test_costs_raw = None
  test_lengths = test_templates = None
elif argsP.algo == "llm_price_finetune" and getattr(argsP, 'freeze_llm', False):
  # Frozen LLM path: use pre-computed LLM embeddings + PRICE features
  from utilsLLM import get_frozen_llm_price_ds_from_csv
  ds, val_ds, test_ds, val_costs, test_costs, test_lengths, test_templates = get_frozen_llm_price_ds_from_csv(
      LLM, dat_paths_train_list, dat_path_test, dat_dict['ds_info'], argsP
  )
  ds_info = dat_dict['ds_info']
  train_loader = DataLoader(dataset=ds, batch_size=argsP.batch_size, shuffle=True,
                            collate_fn=frozen_llm_price_collate,
                            generator=torch.Generator().manual_seed(argsP.seed))
  val_loader = DataLoader(dataset=val_ds, batch_size=argsP.batch_size, shuffle=False,
                          collate_fn=frozen_llm_price_collate)
  test_loader = DataLoader(dataset=test_ds, batch_size=1, shuffle=False,
                           collate_fn=frozen_llm_price_collate)
  train_roots = train_js_nodes = train_costs = None
  val_roots = val_js_nodes = None
  test_roots = test_js_nodes = None
elif "llm" in argsP.algo:
  # Cross-attention inference needs llm_price_finetune data loading (raw texts + PRICE features)
  _cross_attn_inf = (argsP.algo == "llm_price" and
                     getattr(argsP, 'price_weights_source', 'pretrained') in ("cross_attn_joint", "bi_cross_attn_joint", "reverse_cross_attn_joint"))
  if _cross_attn_inf:
    active_collate = llm_price_collate
    _saved_algo = argsP.algo
    argsP.algo = "llm_price_finetune"  # temporarily switch for correct data loading
  else:
    active_collate = llm_price_collate if argsP.algo == "llm_price_finetune" else llm_collate
  ds_info, train_roots, train_js_nodes, train_costs, \
            val_roots,   val_js_nodes,   val_costs,   \
            test_roots,  test_js_nodes,  test_costs,  \
            ds,  val_ds,  test_ds,  \
            train_loader,  val_loader,  test_loader,  \
            test_lengths, test_templates, _ = utilsTrain.load_data(argsP, dat_path, dat_paths_train_list, dat_path_test, dat_dict, LLM, active_collate)
  if _cross_attn_inf:
    argsP.algo = _saved_algo  # restore for model construction
else:
  ds_info, train_roots, train_js_nodes, train_costs, \
            val_roots,   val_js_nodes,   val_costs,   \
            test_roots,  test_js_nodes,  test_costs,  \
            ds,  val_ds,  test_ds,  \
            train_loader,  val_loader,  test_loader,  \
            test_lengths, test_templates, _ = utilsTrain.load_data(argsP, dat_path, dat_paths_train_list, dat_path_test, dat_dict)

from trainer import *

if argsP.algo == "bao":
  # Get total_roots and IDs for verbose output
  total_roots = dat_dict.get('total_roots', None)
  total_costs = dat_dict.get('total_costs', None)
  train_ids = dat_dict.get('train_ids', None)
  test_ids = dat_dict.get('test_ids', None)
  
  # Set test_original_indices only when train/val/test are from the same file
  same_file = (len(dat_paths_train_list) == 1 and dat_paths_train_list[0] == dat_path_test)
  if same_file and test_ids is not None:
    argsP.test_original_indices = test_ids
    print(f"  BAO: Set test_original_indices for index mapping (same file scenario)")
  else:
    # Don't set test_original_indices when train and test are from different files
    print(f"  BAO: Separate train/test files - no index mapping")
  
  # Set metadata for verbose output
  argsP.test_plan_file_path = dat_path_test
  
  results = train_and_test_bao(
      train_roots, train_costs, test_roots, test_costs, argsP, device,
      total_roots=total_roots, total_costs=total_costs,
      train_ids=train_ids, test_ids=test_ids,
      plan_file_path=dat_path_test,
      output_dir_qerror=argsP.output_dir_qerror,
      dat_paths_train_list=dat_paths_train_list
  )
  save_error_cdf(results['qerr_dist'], argsP.output_dir_qerror, error_type="Qerror")
  # save_error_cdf(results['abserr_dist'], argsP.output_dir_abs,   error_type="abs_error")
  sys.exit(0)
elif argsP.algo == "postgres":
  results = train_and_test_postgres(train_roots, train_costs, test_roots, test_costs, argsP,
                                    dat_paths_train_list=dat_paths_train_list)
  save_error_cdf(results['qerr_dist'], argsP.output_dir_qerror, error_type="Qerror")
  # save_error_cdf(results['abserr_dist'], argsP.output_dir_abs,   error_type="abs_error")
  sys.exit(0)



if argsP.algo == "aimai":
  input_dim = len(ds_info.nodeParallels) * 5
  MLP = Prediction(input_dim, argsP.hid_units)
  model_comb = MLP
elif argsP.algo == "qf":
  from algorithms.queryformer.model import *
  model = QueryFormer(emb_size=64, use_sample = True, use_hist = True)
  input_dim = 393
  MLP = Prediction(input_dim, argsP.hid_units)
  model_comb = nn.Sequential(model, MLP)
elif argsP.algo == "e2e_cost":
    from algorithms.e2e_cost.e2e_model import *
    input_dim = 32
    model = E2E_model(input_dim, 64, 64, ds_info)
    MLP = Prediction(input_dim, argsP.hid_units)
    model_comb = nn.Sequential(model, MLP)
elif argsP.algo == "llm":
  input_dim = argsP.embed_size
  downstream = getattr(argsP, "llm_downstream", "mlp")
  if downstream == "autogluon":
    try:
      from models.autogluon_wrapper import AutoGluonRegressor
      model_comb = AutoGluonRegressor(problem_type="regression")
      print("Using AutoGluon as downstream learner for LLM embeddings.")
    except Exception as e:
      print(f"Falling back to MLP due to AutoGluon error: {e}")
      MLP = Prediction(input_dim, argsP.hid_units)
      model_comb = MLP
  else:
    MLP = Prediction(input_dim, argsP.hid_units)
    model_comb = MLP
elif argsP.algo == "llm_stats":
  # Deprecated: stats fusion is disabled. Behave like plain LLM embeddings.
  input_dim = argsP.embed_size
  downstream = getattr(argsP, "llm_downstream", "mlp")
  if downstream == "autogluon":
    print("AutoGluon does not support llm_stats; using MLP instead.")
  MLP = Prediction(input_dim, argsP.hid_units)
  model_comb = MLP
elif argsP.algo == "llm_price" and not _retrain_mlp_cache_hit:
  pws = getattr(argsP, 'price_weights_source', 'pretrained')
  if pws in ("cross_attn_joint", "bi_cross_attn_joint", "reverse_cross_attn_joint"):
    # Cross-attention / bidirectional / reverse cross-attention inference: build full model, load weights, evaluate directly
    import sys as _sys, os as _os
    _experiments_dir = _os.path.dirname(_os.path.abspath(__file__))
    if _experiments_dir not in _sys.path:
        _sys.path.insert(0, _experiments_dir)
    _local_price = _os.path.join(_experiments_dir, "..", "PRICE")
    _price_root = _local_price if _os.path.isdir(_os.path.join(_local_price, "setup")) else "/root/PRICE"
    if _price_root not in _sys.path:
        _sys.path.insert(0, _price_root)
    from model.encoder import RegressionModel
    from models.llm_price_model import (CrossAttentionPRICEEmbedder, CrossAttentionLLMPriceModel,
                                         BiCrossAttentionPRICEEmbedder, BiCrossAttentionLLMPriceModel,
                                         ReverseCrossAttentionPRICEEmbedder, ReverseCrossAttentionLLMPriceModel,
                                         InflatedBiCrossAttentionPRICEEmbedder, InflatedBiCrossAttentionLLMPriceModel)

    # Build PRICE model
    max_njc = argsP.price_max_n_join_col
    max_nfo = argsP.price_max_n_fanout
    max_ntb = argsP.price_max_n_table
    max_nfc = argsP.price_max_n_filter_col
    bin_size = getattr(argsP, 'price_bin_size', 40)
    table_dim = 4
    filter_dim = (bin_size + 21) if getattr(argsP, 'price_m', False) else (bin_size + 3)
    n_cross = getattr(argsP, 'n_cross_layers', 2)

    _price_n_embd = getattr(argsP, 'price_n_embd', 256)
    _price_n_heads = getattr(argsP, 'price_n_heads', 8)
    _price_ffn_ratio = getattr(argsP, 'price_ffn_ratio', 4.0)
    price_model = RegressionModel(
        n_join_col=max_njc, n_fanout=max_nfo, n_table=max_ntb, n_filter_col=max_nfc,
        hist_dim=bin_size, table_dim=table_dim, filter_dim=filter_dim,
        query_hidden_dim=512, final_hidden_dim=1024, output_dim=1,
        n_embd=_price_n_embd, n_layers=getattr(argsP, 'price_n_layers', 6), n_heads=_price_n_heads,
        dropout_rate=0.1, ffn_ratio=_price_ffn_ratio
    )

    if pws == "bi_cross_attn_joint" and getattr(argsP, 'inflate_price', False):
      inf_price_embedder = InflatedBiCrossAttentionPRICEEmbedder(
          price_model, argsP.embed_size, n_cross_layers=n_cross,
          n_embd=256, n_heads=8, dropout_rate=0.1
      )
      model_comb = InflatedBiCrossAttentionLLMPriceModel(LLM, inf_price_embedder, argsP.embed_size, argsP.hid_units)
      attn_tag = "_biCrossAttn"
    elif pws == "bi_cross_attn_joint":
      bi_price_embedder = BiCrossAttentionPRICEEmbedder(
          price_model, argsP.embed_size, n_cross_layers=n_cross,
          n_embd=256, n_heads=8, dropout_rate=0.1
      )
      model_comb = BiCrossAttentionLLMPriceModel(LLM, bi_price_embedder, argsP.embed_size, 512, argsP.hid_units, triple_concat=getattr(argsP, "triple_concat", False))
      attn_tag = "_biCrossAttn"
    elif pws == "reverse_cross_attn_joint":
      rev_price_embedder = ReverseCrossAttentionPRICEEmbedder(
          price_model, argsP.embed_size, n_cross_layers=n_cross,
          n_embd=256, n_heads=8, dropout_rate=0.1
      )
      model_comb = ReverseCrossAttentionLLMPriceModel(LLM, rev_price_embedder, argsP.embed_size, 512, argsP.hid_units)
      attn_tag = "_revCrossAttn"
    else:
      cross_price_embedder = CrossAttentionPRICEEmbedder(
          price_model, argsP.embed_size, n_cross_layers=n_cross,
          n_embd=256, n_heads=8, dropout_rate=0.1
      )
      model_comb = CrossAttentionLLMPriceModel(LLM, cross_price_embedder, argsP.embed_size, 512, argsP.hid_units)
      attn_tag = "_crossAttn"

    # Load finetuned PRICE+cross-attn weights
    ft_bs = getattr(argsP, 'ft_batch_size', 16)
    task_str = "card" if argsP.card else "time"
    price_m_suffix = "_priceM" if getattr(argsP, 'price_m', False) else ""
    price_s_suffix = "_priceS" if getattr(argsP, 'price_s', False) else ""
    rand_init_suffix = "_randInit" if getattr(argsP, 'price_random_init', False) else ""
    refined_pool_suffix = "_refinedPool" if getattr(argsP, 'refined_pool', False) else ""
    triple_concat_suffix = "_tripleConcat" if getattr(argsP, 'triple_concat', False) else ""
    inflate_price_suffix = "_inflatePRICE" if getattr(argsP, 'inflate_price', False) else ""
    n_layers_suffix = f"_pL{argsP.price_n_layers}" if getattr(argsP, 'price_n_layers', 6) != 6 else ""
    ffn_ratio_suffix = f"_ffn{argsP.price_ffn_ratio:g}" if getattr(argsP, 'price_ffn_ratio', 4.0) != 4.0 else ""
    n_cross_suffix = f"_cx{n_cross}" if n_cross != 2 else ""
    ft_epochs = getattr(argsP, 'ft_num_epoch', 0)
    epoch_suffix = f"_e{ft_epochs}" if ft_epochs > 0 else ""
    weight_prefix = f"finetuned_models/{argsP.db}/{argsP.canonical_wl_prefix}_{task_str}_{argsP.llm_pretrained}_{argsP.model_name.replace('/','-')}_b{ft_bs}{price_m_suffix}{price_s_suffix}_llm_price{attn_tag}{refined_pool_suffix}{triple_concat_suffix}{inflate_price_suffix}{rand_init_suffix}{n_layers_suffix}{ffn_ratio_suffix}{n_cross_suffix}{epoch_suffix}"

    price_sd = torch.load(f"{weight_prefix}_price.pt", map_location=device)
    model_comb.price.load_state_dict(price_sd)
    print(f"Loaded {pws} PRICE weights from {weight_prefix}_price.pt")

    mlp_sd = torch.load(f"{weight_prefix}_mlp.pt", map_location=device)
    model_comb.mlp.load_state_dict(mlp_sd)
    print(f"Loaded MLP weights from {weight_prefix}_mlp.pt")

    # Load refined_llm_proj if it exists (BiCrossAttn with refined pooling)
    rlp_path = f"{weight_prefix}_refined_llm_proj.pt"
    if hasattr(model_comb, 'refined_llm_proj') and os.path.exists(rlp_path):
        rlp_sd = torch.load(rlp_path, map_location=device)
        model_comb.refined_llm_proj.load_state_dict(rlp_sd)
        print(f"Loaded refined_llm_proj weights from {rlp_path}")
    # LLM weights already loaded above in the llm_pretrained block

    # Override algo to use llm_price_finetune data loading path
    if getattr(argsP, 'retrain_mlp', False):
        argsP._retrain_mlp_active = True
    else:
        argsP._cross_attn_inference = True
    argsP.algo = "llm_price_finetune"
  else:
    # Standard: Inference on pre-computed LLM+PRICE embeddings — just an MLP
    input_dim = argsP.embed_size
    MLP = Prediction(input_dim, argsP.hid_units)
    model_comb = MLP
elif argsP.algo == "llm_finetune":
  input_dim = argsP.embed_size
  MLP = Prediction(input_dim, argsP.hid_units)
  model_comb = nn.Sequential(LLM, MLP)
elif argsP.algo == "llm_price_finetune":
  import sys as _sys, os as _os
  _experiments_dir = _os.path.dirname(_os.path.abspath(__file__))
  if _experiments_dir not in _sys.path:
      _sys.path.insert(0, _experiments_dir)
  _local_price = _os.path.join(_experiments_dir, "..", "PRICE")
  _price_root = _local_price if _os.path.isdir(_os.path.join(_local_price, "setup")) else "/root/PRICE"
  if _price_root not in _sys.path:
      _sys.path.insert(0, _price_root)
  from model.encoder import RegressionModel
  from models.llm_price_model import PRICEEmbedder, LLMPriceJointModel, GatedLLMPriceJointModel, FrozenLLMPriceModel, CrossAttentionPRICEEmbedder, CrossAttentionLLMPriceModel, BiCrossAttentionPRICEEmbedder, BiCrossAttentionLLMPriceModel, ReverseCrossAttentionPRICEEmbedder, ReverseCrossAttentionLLMPriceModel, InflatedBiCrossAttentionPRICEEmbedder, InflatedBiCrossAttentionLLMPriceModel

  # Load pretrained PRICE model (skip if random init)
  price_state_dict = None
  if not getattr(argsP, 'price_random_init', False):
    price_state_dict = torch.load(argsP.price_model_path, map_location=device)
    # Strip DataParallel 'module.' prefix
    price_state_dict = {k.replace('module.', ''): v for k, v in price_state_dict.items()}

  # Build PRICE RegressionModel with correct dimensions
  max_njc = argsP.price_max_n_join_col
  max_nfo = argsP.price_max_n_fanout
  max_ntb = argsP.price_max_n_table
  max_nfc = argsP.price_max_n_filter_col
  bin_size = getattr(argsP, 'price_bin_size', 40)
  table_dim = 4
  filter_dim = (bin_size + 21) if getattr(argsP, 'price_m', False) else (bin_size + 3)

  _price_n_embd = getattr(argsP, 'price_n_embd', 256)
  _price_n_heads = getattr(argsP, 'price_n_heads', 8)
  _price_ffn_ratio = getattr(argsP, 'price_ffn_ratio', 4.0)
  price_model = RegressionModel(
      n_join_col=max_njc, n_fanout=max_nfo, n_table=max_ntb, n_filter_col=max_nfc,
      hist_dim=bin_size, table_dim=table_dim, filter_dim=filter_dim,
      query_hidden_dim=512, final_hidden_dim=1024, output_dim=1,
      n_embd=_price_n_embd, n_layers=getattr(argsP, 'price_n_layers', 6), n_heads=_price_n_heads,
      dropout_rate=0.1, ffn_ratio=_price_ffn_ratio
  )
  # Load weights with partial init for PRICE_M (histogram bins shared, operator dims differ)
  def _load_price_sd(model, ckpt_sd, label=""):
      """Load checkpoint into PRICE model with partial init for size-mismatched weights.
      For filter_embeddings.weight [n_embd,43]->[n_embd,61], copies the first min(43,61)
      columns (histogram bins) and leaves the rest randomly initialized."""
      model_sd = model.state_dict()
      for k, v in ckpt_sd.items():
          if k not in model_sd:
              continue
          if model_sd[k].shape == v.shape:
              model_sd[k] = v
          elif model_sd[k].dim() == v.dim():
              slices = tuple(slice(0, min(ms, vs)) for ms, vs in zip(model_sd[k].shape, v.shape))
              model_sd[k][slices] = v[slices]
              print(f"  Partial init {k}: copied {[s.stop for s in slices]} of {list(model_sd[k].shape)} from checkpoint {list(v.shape)}")
      model.load_state_dict(model_sd)
      if label:
          print(label)

  if getattr(argsP, 'price_random_init', False):
    print("[PRICE] Random initialization (skipping pretrained weights)")
  elif getattr(argsP, 'price_init_frozen_joint', False):
    # Load frozen-joint PRICE weights instead of pretrained
    task_str = "card" if argsP.card else "time"
    price_m_suffix = "_priceM" if getattr(argsP, 'price_m', False) else ""
    price_s_suffix = "_priceS" if getattr(argsP, 'price_s', False) else ""
    frozen_price_path = f"finetuned_models/{argsP.db}/{argsP.canonical_wl_prefix}_{task_str}_inference_{argsP.model_name.replace('/','-')}_b{argsP.batch_size}{price_m_suffix}{price_s_suffix}_llm_price_price.pt"
    frozen_sd = torch.load(frozen_price_path, map_location=device)
    _load_price_sd(price_model, frozen_sd, f"Loaded frozen-joint PRICE weights from {frozen_price_path}")
  else:
    _load_price_sd(price_model, price_state_dict, f"Loaded PRICE weights from {argsP.price_model_path}")

  price_embedder = PRICEEmbedder(price_model)

  if getattr(argsP, 'freeze_llm', False):
    # Frozen LLM path: model has no LLM, uses pre-computed embeddings
    model_comb = FrozenLLMPriceModel(price_embedder, argsP.embed_size, 512, argsP.hid_units)
    n_trainable = sum(1 for p in model_comb.parameters() if p.requires_grad)
    print(f"[freeze_llm] Using FrozenLLMPriceModel with pre-computed LLM embeddings. {n_trainable} trainable parameter tensors (PRICE + MLP).")
  elif getattr(argsP, 'use_cross_attention', False):
    # Cross-attention path: PRICE tokens attend to LLM hidden states
    n_cross = getattr(argsP, 'n_cross_layers', 2)
    cross_price_embedder = CrossAttentionPRICEEmbedder(
        price_model, argsP.embed_size, n_cross_layers=n_cross,
        n_embd=256, n_heads=8, dropout_rate=0.1
    )
    # Copy PRICE weights that were loaded into price_embedder to cross_price_embedder
    # (the shared layers have the same names, cross-attention layers are new/random)
    if not getattr(argsP, 'price_random_init', False):
      shared_sd = {k: v for k, v in price_embedder.state_dict().items()
                   if k in cross_price_embedder.state_dict() and
                   cross_price_embedder.state_dict()[k].shape == v.shape}
      cross_price_embedder.load_state_dict(shared_sd, strict=False)
      print(f"[cross_attention] Copied {len(shared_sd)} shared PRICE weight tensors; "
            f"cross-attention layers randomly initialized")
    model_comb = CrossAttentionLLMPriceModel(LLM, cross_price_embedder, argsP.embed_size, 512, argsP.hid_units)
    n_cross_params = sum(p.numel() for n, p in cross_price_embedder.named_parameters()
                         if 'cross_attn' in n or 'llm_proj' in n)
    print(f"[cross_attention] {n_cross} cross-attention layers, {n_cross_params:,} new params")
  elif getattr(argsP, 'use_bi_cross_attention', False) and getattr(argsP, 'inflate_price', False):
    # Inflated BiCrossAttn: PRICE projected UP to LLM dim, both directions at LLM dim
    n_cross = getattr(argsP, 'n_cross_layers', 2)
    inf_price_embedder = InflatedBiCrossAttentionPRICEEmbedder(
        price_model, argsP.embed_size, n_cross_layers=n_cross,
        n_embd=256, n_heads=8, dropout_rate=0.1
    )
    if not getattr(argsP, 'price_random_init', False):
      shared_sd = {k: v for k, v in price_embedder.state_dict().items()
                   if k in inf_price_embedder.state_dict() and
                   inf_price_embedder.state_dict()[k].shape == v.shape}
      inf_price_embedder.load_state_dict(shared_sd, strict=False)
      print(f"[inflated_bi_cross] Copied {len(shared_sd)} shared PRICE weight tensors; "
            f"cross-attention layers randomly initialized")
    model_comb = InflatedBiCrossAttentionLLMPriceModel(LLM, inf_price_embedder, argsP.embed_size, argsP.hid_units)
    n_cross_params = sum(p.numel() for p in inf_price_embedder.cross_attn_parameters())
    print(f"[inflated_bi_cross] {n_cross} cross-attention layers at LLM dim ({argsP.embed_size}), {n_cross_params:,} new params")
    print(f"[inflated_bi_cross] MLP input dim = {argsP.embed_size * 2} (2 × LLM dim)")
  elif getattr(argsP, 'use_bi_cross_attention', False):
    # Standard BiCrossAttn: LLM projected DOWN to PRICE dim (256)
    n_cross = getattr(argsP, 'n_cross_layers', 2)
    bi_price_embedder = BiCrossAttentionPRICEEmbedder(
        price_model, argsP.embed_size, n_cross_layers=n_cross,
        n_embd=256, n_heads=8, dropout_rate=0.1
    )
    if not getattr(argsP, 'price_random_init', False):
      shared_sd = {k: v for k, v in price_embedder.state_dict().items()
                   if k in bi_price_embedder.state_dict() and
                   bi_price_embedder.state_dict()[k].shape == v.shape}
      bi_price_embedder.load_state_dict(shared_sd, strict=False)
      print(f"[bi_cross_attention] Copied {len(shared_sd)} shared PRICE weight tensors; "
            f"bi-cross-attention layers randomly initialized")
    model_comb = BiCrossAttentionLLMPriceModel(LLM, bi_price_embedder, argsP.embed_size, 512, argsP.hid_units, triple_concat=getattr(argsP, "triple_concat", False))
    n_cross_params = sum(p.numel() for n, p in bi_price_embedder.named_parameters()
                         if 'cross_attn' in n or 'llm_proj' in n)
    print(f"[bi_cross_attention] {n_cross} bidirectional cross-attention layers, {n_cross_params:,} new params")
  elif getattr(argsP, 'use_reverse_cross_attention', False):
    # Reverse cross-attention path: LLM tokens attend to PRICE tokens
    n_cross = getattr(argsP, 'n_cross_layers', 2)
    rev_price_embedder = ReverseCrossAttentionPRICEEmbedder(
        price_model, argsP.embed_size, n_cross_layers=n_cross,
        n_embd=256, n_heads=8, dropout_rate=0.1
    )
    # Copy PRICE weights that were loaded into price_embedder to rev_price_embedder
    if not getattr(argsP, 'price_random_init', False):
      shared_sd = {k: v for k, v in price_embedder.state_dict().items()
                   if k in rev_price_embedder.state_dict() and
                   rev_price_embedder.state_dict()[k].shape == v.shape}
      rev_price_embedder.load_state_dict(shared_sd, strict=False)
      print(f"[reverse_cross_attention] Copied {len(shared_sd)} shared PRICE weight tensors; "
            f"reverse cross-attention layers randomly initialized")
    model_comb = ReverseCrossAttentionLLMPriceModel(LLM, rev_price_embedder, argsP.embed_size, 512, argsP.hid_units)
    n_cross_params = sum(p.numel() for n, p in rev_price_embedder.named_parameters()
                         if 'cross_attn' in n or 'price_proj' in n)
    print(f"[reverse_cross_attention] {n_cross} reverse cross-attention layers, {n_cross_params:,} new params")
  else:
    if getattr(argsP, 'use_price_gate', False):
      model_comb = GatedLLMPriceJointModel(LLM, price_embedder, argsP.embed_size, 512, argsP.hid_units)
    else:
      model_comb = LLMPriceJointModel(LLM, price_embedder, argsP.embed_size, 512, argsP.hid_units)

  # Freeze PRICE parameters if requested
  if getattr(argsP, 'freeze_all_price', False):
    # Freeze ALL PRICE parameters (for LLMOnly control)
    n_frozen = 0
    for param in model_comb.price.parameters():
      param.requires_grad = False
      n_frozen += 1
    print(f"[freeze_all_price] Froze ALL {n_frozen} PRICE param tensors (0 trainable)")
  elif getattr(argsP, 'freeze_price_encoder', False):
    unfreeze_last_n = getattr(argsP, 'unfreeze_last_n_blocks', 0)
    n_frozen = 0
    for name, param in model_comb.price.named_parameters():
      # Check if this is an embedding layer (always freeze)
      if name.startswith(('scale_embedding', 'filter_embedding')):
        param.requires_grad = False
        n_frozen += 1
      # Check if this is an encoder block
      elif name.startswith(('scale_encoder.blocks.', 'filter_encoder.blocks.')):
        block_num = int(name.split('blocks.')[1].split('.')[0])
        if block_num < getattr(argsP, 'price_n_layers', 6) - unfreeze_last_n:
          param.requires_grad = False
          n_frozen += 1
    n_trainable_price = sum(1 for p in model_comb.price.parameters() if p.requires_grad)
    total_trainable = sum(p.numel() for p in model_comb.price.parameters() if p.requires_grad)
    print(f"[freeze_price_encoder] Froze {n_frozen} PRICE param tensors, {n_trainable_price} remain trainable ({total_trainable:,} params)"
          f" (unfreeze_last_n_blocks={unfreeze_last_n})")

elif argsP.algo == "price_finetune":
  import sys as _sys, os as _os
  _experiments_dir = _os.path.dirname(_os.path.abspath(__file__))
  if _experiments_dir not in _sys.path:
      _sys.path.insert(0, _experiments_dir)
  _local_price = _os.path.join(_experiments_dir, "..", "PRICE")
  _price_root = _local_price if _os.path.isdir(_os.path.join(_local_price, "setup")) else "/root/PRICE"
  if _price_root not in _sys.path:
      _sys.path.insert(0, _price_root)
  from model.encoder import RegressionModel
  from models.llm_price_model import PRICEFinetunWrapper

  # Load pretrained PRICE model
  price_state_dict = torch.load(argsP.price_model_path, map_location=device)
  price_state_dict = {k.replace('module.', ''): v for k, v in price_state_dict.items()}

  max_njc = argsP.price_max_n_join_col
  max_nfo = argsP.price_max_n_fanout
  max_ntb = argsP.price_max_n_table
  max_nfc = argsP.price_max_n_filter_col
  bin_size = getattr(argsP, 'price_bin_size', 40)
  table_dim = 4
  filter_dim = (bin_size + 21) if getattr(argsP, 'price_m', False) else (bin_size + 3)

  _price_n_embd = getattr(argsP, 'price_n_embd', 256)
  _price_n_heads = getattr(argsP, 'price_n_heads', 8)
  _price_ffn_ratio = getattr(argsP, 'price_ffn_ratio', 4.0)
  price_model = RegressionModel(
      n_join_col=max_njc, n_fanout=max_nfo, n_table=max_ntb, n_filter_col=max_nfc,
      hist_dim=bin_size, table_dim=table_dim, filter_dim=filter_dim,
      query_hidden_dim=512, final_hidden_dim=1024, output_dim=1,
      n_embd=_price_n_embd, n_layers=getattr(argsP, 'price_n_layers', 6), n_heads=_price_n_heads,
      dropout_rate=0.1, ffn_ratio=_price_ffn_ratio
  )
  # Load with partial init for PRICE_M (histogram bins shared, operator dims differ)
  def _load_price_sd_ft(model, ckpt_sd, label=""):
      model_sd = model.state_dict()
      for k, v in ckpt_sd.items():
          if k not in model_sd:
              continue
          if model_sd[k].shape == v.shape:
              model_sd[k] = v
          elif model_sd[k].dim() == v.dim():
              slices = tuple(slice(0, min(ms, vs)) for ms, vs in zip(model_sd[k].shape, v.shape))
              model_sd[k][slices] = v[slices]
              print(f"  Partial init {k}: copied {[s.stop for s in slices]} of {list(model_sd[k].shape)} from checkpoint {list(v.shape)}")
      model.load_state_dict(model_sd)
      if label:
          print(label)
  if getattr(argsP, 'price_random_init', False):
    print("[PRICE] Random initialization (skipping pretrained weights)")
  else:
    _load_price_sd_ft(price_model, price_state_dict, f"Loaded pretrained PRICE weights from {argsP.price_model_path}")

  model_comb = PRICEFinetunWrapper(price_model)


# ─── Retrain MLP: pre-compute frozen cross-attn embeddings ─────────────
if getattr(argsP, '_retrain_mlp_active', False):
    # Cache path derived from the finetuned weight prefix (set during cross-attn model construction)
    _test_tag = f"_test-{argsP.workload_test}" if getattr(argsP, 'workload_test', '') else ""
    _retrain_cache_path = f"{weight_prefix}{_test_tag}_retrainMLP_embeddings.pt"
    _cache_hit = os.path.exists(_retrain_cache_path)

    if _cache_hit:
        print(f"[retrain_mlp] Loading cached embeddings from {_retrain_cache_path}")
        _cached = torch.load(_retrain_cache_path, map_location="cpu")
        all_embeddings = _cached["embeddings"]
        all_labels = _cached["labels"]
        for split_name in ("train", "val", "test"):
            print(f"  {split_name}: {all_embeddings[split_name].shape[0]} samples, embed_dim={all_embeddings[split_name].shape[1]}")
        # No need for the full model
        model_comb.cpu()
        del model_comb
        torch.cuda.empty_cache()
    else:
        print("[retrain_mlp] Pre-computing frozen cross-attention embeddings...")
        model_comb.to(device)
        model_comb.eval()

        all_embeddings = {}
        all_labels = {}
        for split_name, loader in [("train", train_loader), ("val", val_loader), ("test", test_loader)]:
            emb_list, lab_list = [], []
            n_batches = len(loader)
            with torch.no_grad():
                for bi, (batch_x, batch_y) in enumerate(loader):
                    emb = model_comb.forward_embeddings(batch_x)
                    emb_list.append(emb.cpu())
                    lab_list.append(batch_y.cpu())
                    if (bi + 1) % max(1, n_batches // 10) == 0 or bi + 1 == n_batches:
                        print(f"  [{split_name}] {bi+1}/{n_batches} batches", flush=True)
            all_embeddings[split_name] = torch.cat(emb_list, dim=0)
            all_labels[split_name] = torch.cat(lab_list, dim=0)
            print(f"  {split_name}: {all_embeddings[split_name].shape[0]} samples, embed_dim={all_embeddings[split_name].shape[1]}")

        # Save cache (include cost_norm for fast-path reconstruction)
        _cost_norm_data = {"mini": ds_info.cost_norm.mini, "maxi": ds_info.cost_norm.maxi} if ds_info.cost_norm else None
        torch.save({"embeddings": all_embeddings, "labels": all_labels, "cost_norm": _cost_norm_data}, _retrain_cache_path)
        print(f"[retrain_mlp] Cached embeddings to {_retrain_cache_path}")

        # Free the full model from GPU
        model_comb.cpu()
        del model_comb
        torch.cuda.empty_cache()

    # Build fresh MLP and new loaders
    combined_dim = all_embeddings["train"].shape[1]
    model_comb = Prediction(combined_dim, argsP.hid_units)
    print(f"[retrain_mlp] Fresh MLP: input_dim={combined_dim}, hid_units={argsP.hid_units}")

    ds = TensorDataset(all_embeddings["train"], all_labels["train"])
    val_ds = TensorDataset(all_embeddings["val"], all_labels["val"])
    test_ds = TensorDataset(all_embeddings["test"], all_labels["test"])

    train_loader = DataLoader(ds, batch_size=argsP.batch_size, shuffle=True,
                              generator=torch.Generator().manual_seed(argsP.seed))
    val_loader = DataLoader(val_ds, batch_size=argsP.batch_size, shuffle=False)
    test_loader = DataLoader(test_ds, batch_size=1, shuffle=False)

    # Switch algo so training loop uses standard MLP path (StepLR scheduler)
    argsP.algo = "llm_price"
    argsP.embed_size = combined_dim
    print(f"[retrain_mlp] Switched to algo=llm_price for MLP-only training ({argsP.num_epoch} epochs)")


crit = nn.MSELoss()

# Custom optimizer/scheduler for price_finetune or freeze_llm
price_finetune_optimizer = None
price_finetune_scheduler = None
if argsP.algo == "llm_price_finetune" and getattr(argsP, 'freeze_llm', False):
    # Only optimize PRICE + MLP params (LLM is frozen)
    _raw_price_lr = getattr(argsP, 'price_lr', None)
    price_lr = _raw_price_lr if _raw_price_lr is not None else (1e-3 if getattr(argsP, 'price_random_init', False) else 2.85e-5)
    lr = argsP.learning_rate
    param_groups = [
        {'params': list(model_comb.price.parameters()), 'lr': price_lr},
        {'params': list(model_comb.mlp.parameters()), 'lr': lr},
    ]
    price_finetune_optimizer = torch.optim.Adam(param_groups)
    if getattr(argsP, 'price_random_init', False):
        _finetune_lr = 2e-5
        _price_warmup = getattr(argsP, 'price_warmup_epochs', 10)
        def _random_init_schedule_frozen(epoch, _price_lr=price_lr, _ft_lr=_finetune_lr, _pw=_price_warmup):
            if epoch < _pw:
                return 1.0
            else:
                return _ft_lr / _price_lr
        price_finetune_scheduler = torch.optim.lr_scheduler.LambdaLR(
            price_finetune_optimizer, _random_init_schedule_frozen)
        print(f"[freeze_llm] Custom optimizer: PRICE lr={price_lr} (random init, drop to {_finetune_lr} at epoch {_price_warmup}), MLP lr={lr}")
    else:
        price_finetune_scheduler = torch.optim.lr_scheduler.OneCycleLR(
            price_finetune_optimizer, max_lr=[price_lr, lr],
            steps_per_epoch=len(train_loader), epochs=argsP.num_epoch
        )
        print(f"[freeze_llm] Custom optimizer: PRICE lr={price_lr}, MLP lr={lr}")
elif argsP.algo == "price_finetune":
    _raw_price_lr = getattr(argsP, 'price_lr', None)
    price_lr = _raw_price_lr if _raw_price_lr is not None else (1e-3 if getattr(argsP, 'price_random_init', False) else 2.85e-5)
    price_finetune_optimizer = torch.optim.Adam(model_comb.parameters(), lr=price_lr)
    if getattr(argsP, 'price_random_init', False):
        _finetune_lr = 2e-5
        _price_warmup = getattr(argsP, 'price_warmup_epochs', 10)
        def _random_init_schedule_ft(epoch, _price_lr=price_lr, _ft_lr=_finetune_lr, _pw=_price_warmup):
            if epoch < _pw:
                return 1.0
            else:
                return _ft_lr / _price_lr
        price_finetune_scheduler = torch.optim.lr_scheduler.LambdaLR(
            price_finetune_optimizer, _random_init_schedule_ft)
        print(f"[price_finetune] Random init LR schedule: {price_lr} for epochs 0-{_price_warmup-1}, {_finetune_lr} for epochs {_price_warmup}+")
    else:
        price_finetune_scheduler = torch.optim.lr_scheduler.OneCycleLR(
            price_finetune_optimizer, max_lr=price_lr,
            steps_per_epoch=len(train_loader), epochs=argsP.num_epoch
        )

# Compute experiment-specific checkpoint prefix for PRICE finetuning
_ckpt_prefix = None
if argsP.algo == "llm_price_finetune":
    _task = "card" if argsP.card else "time"
    _fi = "_frozenInit" if getattr(argsP, 'price_init_frozen_joint', False) else ""
    _ga = "_gated" if getattr(argsP, 'use_price_gate', False) else ""
    _ca = "_crossAttn" if getattr(argsP, 'use_cross_attention', False) else ""
    _bca = "_biCrossAttn" if getattr(argsP, 'use_bi_cross_attention', False) else ""
    _rca = "_revCrossAttn" if getattr(argsP, 'use_reverse_cross_attention', False) else ""
    _rp = "_refinedPool" if getattr(argsP, 'refined_pool', False) else ""
    _tc = "_tripleConcat" if getattr(argsP, 'triple_concat', False) else ""
    _ip = "_inflatePRICE" if getattr(argsP, 'inflate_price', False) else ""
    _pm = "_priceM" if getattr(argsP, 'price_m', False) else ""
    _ps = "_priceS" if getattr(argsP, 'price_s', False) else ""
    _ri = "_randInit" if getattr(argsP, 'price_random_init', False) else ""
    _nl = f"_pL{argsP.price_n_layers}" if getattr(argsP, 'price_n_layers', 6) != 6 else ""
    _fr = f"_ffn{argsP.price_ffn_ratio:g}" if getattr(argsP, 'price_ffn_ratio', 4.0) != 4.0 else ""
    _nc = f"_cx{argsP.n_cross_layers}" if (getattr(argsP, 'use_cross_attention', False) or getattr(argsP, 'use_bi_cross_attention', False) or getattr(argsP, 'use_reverse_cross_attention', False)) and getattr(argsP, 'n_cross_layers', 2) != 2 else ""
    _ckpt_prefix = f"{argsP.canonical_wl_prefix}_{_task}_{argsP.llm_mode}_{argsP.model_name.replace('/','-')}_b{argsP.batch_size}{_pm}{_ps}_llm_price{_fi}{_ga}{_ca}{_bca}{_rca}{_rp}{_tc}{_ip}{_ri}{_nl}{_fr}{_nc}"
elif argsP.algo == "price_finetune":
    _pm = "_priceM" if getattr(argsP, 'price_m', False) else ""
    _ps = "_priceS" if getattr(argsP, 'price_s', False) else ""
    _ri = "_randInit" if getattr(argsP, 'price_random_init', False) else ""
    _ckpt_prefix = f"{argsP.canonical_wl_prefix}_card_b{argsP.batch_size}{_pm}{_ps}{_ri}_price_separate"
elif argsP.algo == "llm_finetune":
    _task = "card" if argsP.card else "time"
    _ckpt_prefix = f"{argsP.canonical_wl_prefix}_{_task}_{argsP.llm_mode}_{argsP.model_name.replace('/','-')}_b{argsP.batch_size}"
argsP.checkpoint_prefix = _ckpt_prefix

# Resume from checkpoint if specified (or auto-detect latest)
resume_ckpt = getattr(argsP, 'resume_checkpoint', '')
start_epoch = 0
_resumed_from_weights = False
if not resume_ckpt and _ckpt_prefix and getattr(argsP, 'checkpoint_interval', 0) > 0:
    import glob as _glob
    _ckpt_dir = f"finetuned_models/{argsP.db}/checkpoints"
    _pattern = os.path.join(_ckpt_dir, f"{_ckpt_prefix}_epoch*.pt")
    _ckpts = sorted(_glob.glob(_pattern), key=lambda p: int(re.search(r'_epoch(\d+)', p).group(1)))
    if _ckpts:
        resume_ckpt = _ckpts[-1]
        print(f"[Checkpoint] Auto-detected: {resume_ckpt}")
    else:
        # Fallback: look for final weight files from a previous epoch count
        # These are separate files (llm.pt, price.pt, mlp.pt) saved after training
        _weight_dir = f"finetuned_models/{argsP.db}"
        _weight_pattern = os.path.join(_weight_dir, f"{_ckpt_prefix}_e*_llm.pt")
        _weight_files = _glob.glob(_weight_pattern)
        if _weight_files:
            # Find the highest epoch among available weight files
            _epochs_found = []
            for wf in _weight_files:
                m = re.search(r'_e(\d+)_llm\.pt$', wf)
                if m:
                    ep = int(m.group(1))
                    if ep < argsP.num_epoch:  # Only resume from earlier epochs
                        _epochs_found.append(ep)
            if _epochs_found:
                _best_ep = max(_epochs_found)
                _weight_prefix = os.path.join(_weight_dir, f"{_ckpt_prefix}_e{_best_ep}")
                _llm_f = f"{_weight_prefix}_llm.pt"
                _price_f = f"{_weight_prefix}_price.pt"
                _mlp_f = f"{_weight_prefix}_mlp.pt"
                _gate_f = f"{_weight_prefix}_gate.pt"
                if os.path.exists(_llm_f) and os.path.exists(_price_f):
                    print(f"[Resume] Loading separate weight files from epoch {_best_ep}")
                    # Load PRICE weights
                    _price_sd = torch.load(_price_f, map_location=argsP.device, weights_only=True)
                    model_comb.price.load_state_dict(_price_sd)
                    print(f"[Resume] Loaded PRICE weights from {_price_f}")
                    # Load MLP weights
                    if os.path.exists(_mlp_f):
                        _mlp_sd = torch.load(_mlp_f, map_location=argsP.device, weights_only=True)
                        model_comb.mlp.load_state_dict(_mlp_sd)
                        print(f"[Resume] Loaded MLP weights from {_mlp_f}")
                    # Load LLM LoRA weights (filter to only LoRA keys)
                    _llm_sd = torch.load(_llm_f, map_location=argsP.device, weights_only=True)
                    _lora_keys = {k: v for k, v in _llm_sd.items() if 'lora_' in k}
                    if _lora_keys:
                        _current_sd = model_comb.llm.model.state_dict()
                        _current_sd.update(_lora_keys)
                        model_comb.llm.model.load_state_dict(_current_sd, strict=False)
                        print(f"[Resume] Loaded {len(_lora_keys)} LoRA weight tensors from {_llm_f}")
                    # Load gate weights if applicable
                    if os.path.exists(_gate_f) and hasattr(model_comb, 'gate'):
                        _gate_sd = torch.load(_gate_f, map_location=argsP.device, weights_only=True)
                        model_comb.gate.load_state_dict(_gate_sd)
                        print(f"[Resume] Loaded gate weights from {_gate_f}")
                    start_epoch = _best_ep
                    _resumed_from_weights = True
                    print(f"[Resume] Will start training from epoch {start_epoch}")
if resume_ckpt and os.path.exists(resume_ckpt) and not _resumed_from_weights:
    print(f"[Checkpoint] Resuming from {resume_ckpt}")
    ckpt = torch.load(resume_ckpt, map_location=argsP.device, weights_only=False)
    _load_result = model_comb.load_state_dict(ckpt['model_state_dict'], strict=False)
    if _load_result.unexpected_keys:
        print(f"[Checkpoint] Ignored {len(_load_result.unexpected_keys)} unexpected keys (e.g. bitsandbytes metadata)")
    if _load_result.missing_keys:
        print(f"[Checkpoint] WARNING: {len(_load_result.missing_keys)} missing keys: {_load_result.missing_keys[:5]}")
    start_epoch = ckpt['epoch']
    # Optimizer/scheduler will be loaded inside train() if we pass them
    if price_finetune_optimizer and ckpt.get('optimizer_state_dict'):
        price_finetune_optimizer.load_state_dict(ckpt['optimizer_state_dict'])
    if price_finetune_scheduler and ckpt.get('scheduler_state_dict'):
        price_finetune_scheduler.load_state_dict(ckpt['scheduler_state_dict'])
    print(f"[Checkpoint] Resuming from epoch {start_epoch}")

# Check for cached baseline model
_baseline_cached = False
if argsP.algo in ("aimai", "qf", "e2e_cost"):
    _cache_dir = f"finetuned_models/{argsP.db}/"
    _task_str = "card" if argsP.card else "time"
    _prefix = f"long_raw_{argsP.db}_"
    _data_names = []
    for _p in sorted(set(dat_paths_train_list)):
        _stem = os.path.splitext(os.path.basename(_p))[0]
        _data_names.append(_stem[len(_prefix):] if _stem.startswith(_prefix) else _stem)
    _data_str = '-'.join(_data_names)
    _cache_name = f"{_data_str}_{_task_str}_{argsP.algo}_d{input_dim}_{argsP.train_ratio}_b{argsP.batch_size}_h{argsP.hid_units}_seed{argsP.seed}_model.pt"
    _cache_path = os.path.join(_cache_dir, _cache_name)
    if os.path.exists(_cache_path):
        model_comb.load_state_dict(torch.load(_cache_path, map_location=argsP.device))
        model_comb.to(argsP.device)
        print(f"Loaded cached {argsP.algo} model from {_cache_path}")
        trained_model = model_comb
        _baseline_cached = True

if getattr(argsP, '_cross_attn_inference', False):
    # Cross-attention inference: model already has loaded weights, skip training
    trained_model = model_comb
    trained_model.to(argsP.device)
    training_time = 0.0
    argsP.main_logger.info(f"[Train] Skipped training (cross-attention inference with pre-loaded weights)")
elif _baseline_cached:
    training_time = 0.0
    argsP.main_logger.info(f"[Train] Skipped training (loaded from cache)")
else:
    training_start = timer()
    trained_model = train(model_comb, train_loader, val_loader, ds_info, argsP, crit=crit,
                          optimizer=price_finetune_optimizer, scheduler=price_finetune_scheduler,
                          start_epoch=start_epoch)
    training_time = timer() - training_start
    argsP.main_logger.info(f"[Train] Training took {training_time*1000:.2f} ms")

if argsP.algo == "llm_finetune":
    # Create save directory
    save_path = f"finetuned_models/{argsP.db}/"
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    save_dir = os.path.dirname(save_path)
    if save_dir and not os.path.exists(save_dir):
        os.makedirs(save_dir, exist_ok=True)

    llm_sd = LLM.model.state_dict()

    stats_suffix = ""
    if getattr(argsP, "stats_token_inject", False):
        stats_mode = getattr(argsP, "stats_token_mode", "per_column")
        stats_suffix = f"_statTok-{stats_mode}"
    if argsP.card:
        llm_out = os.path.join(save_dir, f"{argsP.canonical_wl_prefix}_card_{argsP.llm_mode}_{argsP.model_name.replace('/','-')}_b{argsP.batch_size}{stats_suffix}_llm.pt")
    else:
        llm_out = os.path.join(save_dir, f"{argsP.canonical_wl_prefix}_time_{argsP.llm_mode}_{argsP.model_name.replace('/','-')}_b{argsP.batch_size}{stats_suffix}_llm.pt")
    torch.save(llm_sd, llm_out)
    print(f"🔖  Saved LLM weights to {llm_out}")
elif argsP.algo == "llm_price_finetune" and not getattr(argsP, '_cross_attn_inference', False):
    # Save components: LLM (if not frozen), PRICE, MLP
    save_path = f"finetuned_models/{argsP.db}/"
    os.makedirs(save_path, exist_ok=True)

    task_str = "card" if argsP.card else "time"
    frozen_init_suffix = "_frozenInit" if getattr(argsP, 'price_init_frozen_joint', False) else ""
    gated_suffix = "_gated" if getattr(argsP, 'use_price_gate', False) else ""
    cross_attn_suffix = "_crossAttn" if getattr(argsP, 'use_cross_attention', False) else ""
    bi_cross_attn_suffix = "_biCrossAttn" if getattr(argsP, 'use_bi_cross_attention', False) else ""
    rev_cross_attn_suffix = "_revCrossAttn" if getattr(argsP, 'use_reverse_cross_attention', False) else ""
    refined_pool_suffix = "_refinedPool" if getattr(argsP, 'refined_pool', False) else ""
    triple_concat_suffix = "_tripleConcat" if getattr(argsP, 'triple_concat', False) else ""
    inflate_price_suffix = "_inflatePRICE" if getattr(argsP, 'inflate_price', False) else ""
    price_m_suffix = "_priceM" if getattr(argsP, 'price_m', False) else ""
    price_s_suffix = "_priceS" if getattr(argsP, 'price_s', False) else ""
    rand_init_suffix = "_randInit" if getattr(argsP, 'price_random_init', False) else ""
    n_layers_suffix = f"_pL{argsP.price_n_layers}" if getattr(argsP, 'price_n_layers', 6) != 6 else ""
    ffn_ratio_suffix = f"_ffn{argsP.price_ffn_ratio:g}" if getattr(argsP, 'price_ffn_ratio', 4.0) != 4.0 else ""
    n_cross_suffix = f"_cx{argsP.n_cross_layers}" if (getattr(argsP, 'use_cross_attention', False) or getattr(argsP, 'use_bi_cross_attention', False) or getattr(argsP, 'use_reverse_cross_attention', False)) and getattr(argsP, 'n_cross_layers', 2) != 2 else ""
    epoch_suffix = f"_e{argsP.num_epoch}"
    prefix = f"{argsP.canonical_wl_prefix}_{task_str}_{argsP.llm_mode}_{argsP.model_name.replace('/','-')}_b{argsP.batch_size}{price_m_suffix}{price_s_suffix}_llm_price{frozen_init_suffix}{gated_suffix}{cross_attn_suffix}{bi_cross_attn_suffix}{rev_cross_attn_suffix}{refined_pool_suffix}{triple_concat_suffix}{inflate_price_suffix}{rand_init_suffix}{n_layers_suffix}{ffn_ratio_suffix}{n_cross_suffix}{epoch_suffix}"

    if not getattr(argsP, 'freeze_llm', False):
        llm_sd = trained_model.llm.model.state_dict()
        llm_out = os.path.join(save_path, f"{prefix}_llm.pt")
        torch.save(llm_sd, llm_out)
        print(f"Saved LLM weights to {llm_out}")
    else:
        print(f"[freeze_llm] Skipping LLM weight save (unchanged)")

    price_sd = trained_model.price.state_dict()
    price_out = os.path.join(save_path, f"{prefix}_price.pt")
    torch.save(price_sd, price_out)
    print(f"Saved PRICE weights to {price_out}")

    mlp_sd = trained_model.mlp.state_dict()
    mlp_out = os.path.join(save_path, f"{prefix}_mlp.pt")
    torch.save(mlp_sd, mlp_out)
    print(f"Saved MLP weights to {mlp_out}")

    if hasattr(trained_model, 'gate'):
        gate_sd = trained_model.gate.state_dict()
        gate_out = os.path.join(save_path, f"{prefix}_gate.pt")
        torch.save(gate_sd, gate_out)
        print(f"Saved gate weights to {gate_out}")

    if hasattr(trained_model, 'refined_llm_proj'):
        rlp_sd = trained_model.refined_llm_proj.state_dict()
        rlp_out = os.path.join(save_path, f"{prefix}_refined_llm_proj.pt")
        torch.save(rlp_sd, rlp_out)
        print(f"Saved refined_llm_proj weights to {rlp_out}")
elif argsP.algo == "price_finetune":
    # Save finetuned PRICE model (the inner RegressionModel state_dict)
    save_path = f"finetuned_models/{argsP.db}/"
    os.makedirs(save_path, exist_ok=True)

    price_m_suffix = "_priceM" if getattr(argsP, 'price_m', False) else ""
    price_s_suffix = "_priceS" if getattr(argsP, 'price_s', False) else ""
    rand_init_suffix = "_randInit" if getattr(argsP, 'price_random_init', False) else ""
    n_layers_suffix = f"_pL{argsP.price_n_layers}" if getattr(argsP, 'price_n_layers', 6) != 6 else ""
    ffn_ratio_suffix = f"_ffn{argsP.price_ffn_ratio:g}" if getattr(argsP, 'price_ffn_ratio', 4.0) != 4.0 else ""
    epoch_suffix = f"_e{argsP.num_epoch}"
    price_out = os.path.join(save_path, f"{argsP.canonical_wl_prefix}_card_b{argsP.batch_size}{price_m_suffix}{price_s_suffix}{rand_init_suffix}{n_layers_suffix}{ffn_ratio_suffix}{epoch_suffix}_price_separate.pt")
    torch.save(trained_model.model.state_dict(), price_out)
    print(f"Saved separately finetuned PRICE weights to {price_out}")
else:
  # Save cached baseline model after training
  if argsP.algo in ("aimai", "qf", "e2e_cost") and not _baseline_cached:
    os.makedirs(_cache_dir, exist_ok=True)
    torch.save(trained_model.state_dict(), _cache_path)
    print(f"Saved {argsP.algo} model to {_cache_path}")

  # Save MLP weights for llm / llm_price inference (seed in filename)
  if argsP.algo in ("llm", "llm_price") and isinstance(trained_model, nn.Module):
    save_path = f"finetuned_models/{argsP.db}/"
    os.makedirs(save_path, exist_ok=True)
    task_str = "card" if argsP.card else "time"
    pretrained_str = argsP.llm_pretrained or "None"
    model_str = argsP.model_name.replace('/', '-')
    wl_str = '-'.join(argsP.workloads_train)
    # Truncate long workload strings to avoid exceeding filesystem filename limits (255 chars)
    if len(wl_str) > 80:
        import hashlib
        wl_hash = hashlib.md5(wl_str.encode()).hexdigest()[:8]
        wl_str = f"{len(argsP.workloads_train)}dbs_{wl_hash}"
    # Note: this path is only used for the non-joint-price MLP save (line 767+).
    # The joint-price path uses argsP.canonical_wl_prefix which is already truncated.
    ftb_str = f"_ftb{argsP.ft_batch_size}" if pretrained_str != "None" else ""
    price_str = ""
    price_m_str = "_priceM" if getattr(argsP, 'price_m', False) else ""
    price_s_str = "_priceS" if getattr(argsP, 'price_s', False) else ""
    if argsP.algo == "llm_price":
        price_source = getattr(argsP, 'price_weights_source', 'pretrained')
        price_str = f"_price-{price_source}"
    test_str = f"_test-{argsP.workload_test}" if argsP.workload_test else ""
    mlp_name = f"{wl_str}{test_str}_{task_str}_{argsP.algo}_pretrained-{pretrained_str}{price_str}{price_m_str}{price_s_str}_{model_str}_emb{argsP.embed_size}_h{argsP.hid_units}{ftb_str}_seed{argsP.seed}_mlp.pt"
    mlp_out = os.path.join(save_path, mlp_name)
    torch.save(trained_model.state_dict(), mlp_out)
    print(f"Saved MLP weights to {mlp_out}")

  # Log testing time for all other algorithms
  test_start = timer()
  
  # Prepare embeddings and metadata for verbose output
  train_embeddings_verbose = None
  
  if argsP.verbose_info:
    print("Preparing data for verbose output...")
    
    if argsP.algo in ("llm", "llm_price"):
      # For LLM/LLM+PRICE algorithm, get training embeddings for KNN calculation
      train_embeddings_verbose = ds.tensors[0].cpu().numpy()
    
    elif argsP.algo in ['aimai', 'qf', 'e2e_cost']:
      # For non-LLM algorithms with Sequential models
      train_embeddings_verbose = utilsTrain.prepare_non_llm_verbose_embeddings(
          argsP, trained_model, device, ds_info, dat_dict,
          dat_paths_train_list, dat_path_test, dat_path
      )
  
  if not argsP.card:
    q_errors, abs_errors, q_errors_dist, abs_errors_dist = evaluate(trained_model, argsP, test_loader, ds_info.cost_norm, device, data_sec="test",
                                                                    save_embeddings=False,
                                                                    # save_embeddings=(argsP.workload_test in ["tpch", "tpcds"] and test_templates is not None),
                                                                    test_embeddings=(test_ds.tensors[0].cpu().numpy() if argsP.algo in ("llm", "llm_price") and hasattr(test_ds, 'tensors') else None),
                                                                    test_templates=test_templates,
                                                                    output_dir_qerror=argsP.output_dir_qerror,
                                                                    workload_test=argsP.workload_test,
                                                                    verbose_info=argsP.verbose_info,
                                                                    train_embeddings=train_embeddings_verbose,
                                                                    test_texts=None)
  else:
    q_errors, abs_errors, q_errors_dist, abs_errors_dist = evaluate(trained_model, argsP, test_loader, ds_info.card_norm, device, data_sec="test",
                                                                    save_embeddings=False,
                                                                    test_embeddings=(test_ds.tensors[0].cpu().numpy() if argsP.algo in ("llm", "llm_price") and hasattr(test_ds, 'tensors') else None),
                                                                    test_templates=test_templates,
                                                                    output_dir_qerror=argsP.output_dir_qerror,
                                                                    workload_test=argsP.workload_test,
                                                                    verbose_info=argsP.verbose_info,
                                                                    train_embeddings=train_embeddings_verbose,
                                                                    test_texts=None)
  test_time = timer() - test_start
  argsP.main_logger.info(f"[Test] Testing took {test_time*1000:.2f} ms")

  save_error_cdf(q_errors_dist, argsP.output_dir_qerror, error_type="Qerror")
  # save_error_cdf(abs_errors_dist, argsP.output_dir_abs, error_type="abs_error")

  if argsP.algo in ("llm", "llm_price"):
    output_dir_lvq = argsP.output_dir_qerror.replace("cdf", "length_vs_qerror")
    with open(output_dir_lvq, "w") as f:
        w = csv.writer(f)
        w.writerow(["plan_length", "q_error"])
        for L, Q in zip(test_lengths, q_errors_dist):
            w.writerow([L, Q])

  print("\nTest Results:")
  print("Q Errors:", q_errors)
  # print("Absolute Errors:", abs_errors)
