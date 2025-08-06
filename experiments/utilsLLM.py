import os
import time
import json
import torch
import torch.nn as nn
import torch.nn.init as init
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, TensorDataset
from transformers import AutoTokenizer, AutoModelForCausalLM, LlamaForCausalLM, LlamaModel
import bitsandbytes, flash_attn
import random
import pandas as pd

# QLoRA and PEFT imports
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
import argparse
import numpy as np
import re
import sys
from sklearn.model_selection import train_test_split
import time
import logging

sys.path.append('../evaluation/')
from dataset_utils import *
from utils import Normalizer
#########################################
#       Custom Dataset Class
#########################################

# perf_counter gives you sub-microsecond resolution
timer = time.perf_counter
# infer_logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO)


class QueryPlanDataset(Dataset):
    """
    Assumes each .txt file in the given directory has the following format:
      - First line: the query plan (text)
      - Second line: the ground truth cost (a float)
    """
    def __init__(self, texts, costs):
        assert len(texts) == len(costs), "texts and costs length mismatch"
        self.texts = texts
        self.costs = costs
        self.generator = torch.Generator()
        self.set_seed(42)  # Default seed
    
    def set_seed(self, seed):
        self.generator.manual_seed(seed)
    
    def __len__(self):
        return len(self.costs)
    
    def __getitem__(self, idx):
        return self.texts[idx], self.costs[idx]

#########################################
#    QueryPlanPredictor Model Class
#########################################

class QueryPlanPredictor(nn.Module):
    def __init__(
        self,
        model_name: str,
        mode: str = "inference",           # one of ['inference','lora','last']
        lora_r: int = 8,
        lora_alpha: int = 32,
        lora_dropout: float = 0.1,
        target_modules: list = None,
        *,
        enable_checkpointing: bool = False,
        offload_folder: str | None = None,
    ):
        """
        - enable_checkpointing=True  → turn on gradient checkpointing in the LLM.
        - offload_folder="some/path" → page weights/optimizer state to CPU/disk.
        """
        super().__init__()

        # 1) Tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # 2) Load the LLM backbone in 4-bit, with optional offloading
        #     - torch_dtype=torch.float16: internal compute in fp16
        #     - load_in_4bit=True: quantize weights to 4-bit
        #     - device_map="auto": HF/Accelerate will assign layers to GPU/CPU
        #     - offload_folder=...: if set, accelerate will spill weights to disk/CPU
        load_kwargs = {
            "pretrained_model_name_or_path": model_name,
            "torch_dtype": torch.float16,
            "load_in_4bit": True,
            "device_map": "auto",
            "use_flash_attention_2": False,
        }
        if offload_folder:
            # If you want to offload weights to CPU/disk:
            load_kwargs["offload_folder"] = offload_folder
            load_kwargs["offload_state_dict"] = True

        # self.model = LlamaForCausalLM.from_pretrained(**load_kwargs)
        self.model = LlamaModel.from_pretrained(**load_kwargs)

        # 3) (Optional) enable gradient checkpointing on the backbone
        if enable_checkpointing:
            # This tells HF to checkpoint inner layers during forward
            # so they are recomputed in backward.
            self.model.gradient_checkpointing_enable()

        # 4) Prepare for QLoRA (freeze 4-bit weights + enable adapter injection)
        self.model = prepare_model_for_kbit_training(self.model)

        # 5) Inject LoRA adapters
        if target_modules is None:
            target_modules = ["q_proj", "v_proj"]
        lora_cfg = LoraConfig(
            r=lora_r,
            lora_alpha=lora_alpha,
            target_modules=target_modules,
            lora_dropout=lora_dropout,
            bias="none",
            task_type="CAUSAL_LM",
            # bnb_4bit_compute_dtype=torch.float16,  # do 4-bit matmuls in fp16
        )
        self.model = get_peft_model(self.model, lora_cfg)

        # 6) Hidden-dimension of the pooled embedding
        self.hidden_dim = self.model.config.hidden_size

        # 7) Freeze/unfreeze parameters based on mode
        if mode == "inference":
            # Freeze absolutely everything
            for p in self.model.parameters():
                p.requires_grad = False

        elif mode == "lora":
            # QLoRA default: base in 4-bit is frozen, adapters are trainable
            # (no extra action needed)
            pass

        elif mode == "last":
            # Freeze everything except the last layer's weights
            for name, p in self.model.named_parameters():
                layer_ok = (
                    name.startswith("base_model.model.layers")
                    and name.split(".")[3]
                    == str(self.model.config.num_hidden_layers - 1)
                )
                # p.requires_grad = layer_ok
                if p.dtype.is_floating_point or p.dtype.is_complex:
                    p.requires_grad = layer_ok
                else:
                    # All bitsandbytes-quantized (int/4-bit) tensors or buffers get frozen
                    p.requires_grad = False

        else:
            raise ValueError(f"Unknown mode {mode!r}")

    def forward(self, texts: list[str]):
        # 1) Tokenize + move to device
        inputs = self.tokenizer(
            texts,
            return_tensors="pt",
            padding=True,
            truncation=True,
        )
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}

        # 2) Forward through LLM → get hidden states
        outputs = self.model(**inputs, output_hidden_states=True)
        hs = getattr(outputs, "last_hidden_state", outputs.hidden_states[-1])

        # 3) Mean‐pool over tokens (masking padded positions)
        mask = inputs["attention_mask"].unsqueeze(-1)  # [B, T, 1]
        hs_masked = hs * mask                          # zeros out padding tokens
        sum_hs = hs_masked.sum(dim=1)                  # [B, H]
        lens = mask.sum(dim=1).clamp(min=1)             # avoid div0
        emb = sum_hs / lens                             # [B, H]

        return emb
    

class FeatureNormalizer:
    def __init__(self, eps=1e-6):
        self.vmin = None
        self.vmax = None
        self.eps = eps

    def fit(self, features: torch.Tensor):
        """
        features: [N, D] tensor of training embeddings
        """
        # compute per‐dimension minima & maxima
        self.vmin = features.min(dim=0, keepdim=True).values
        self.vmax = features.max(dim=0, keepdim=True).values

    def transform(self, features: torch.Tensor) -> torch.Tensor:
        """
        Apply (x - min)/(max - min + eps), clipping into [0,1].
        """
        assert self.vmin is not None, "must call fit() first"
        # broadcast sub & div
        normed = (features - self.vmin) / (self.vmax - self.vmin + self.eps)
        return normed.clamp(0.0, 1.0)

    def fit_transform(self, features: torch.Tensor) -> torch.Tensor:
        self.fit(features)
        return self.transform(features)

def sample_train(features, labels, train_ratio, features_is_list=False):
    """
    Randomly sample a fraction of the training set.
    """
    total_rows = len(features)
    indices = list(range(total_rows))
    train_ids, _ = train_test_split(
        indices,
        train_size=train_ratio,
        random_state=42
    )
    if features_is_list:
        features = [features[idx] for idx in train_ids]
    else:
        features = features[train_ids]
    # labels   = labels[train_ids]
    labels   = [labels[idx] for idx in train_ids ]
    return features, labels

def downsample_block_mean(features: torch.Tensor, argsP) -> torch.Tensor:
    """
    Deterministically down‐samples a [B, H] tensor to [B, K] by averaging
    H//K‐sized blocks along the feature dimension.
    If K >= H, returns features unchanged.
    """
    K = argsP.embed_size
    B, H = features.shape
    if K >= H:
        argsP.embed_size = H
        return features

    block_size = H // K
    # drop the trailing dims so H is a multiple of K
    truncated = features[:, : block_size * K]        # [B, block_size*K]
    # reshape to [B, K, block_size] and average over the last axis
    return truncated.view(B, K, block_size).mean(dim=2)  # [B, K]


def _extract_root(plan_json):
    """
    Given the loaded JSON (either a list with one dict or a dict),
    pull out the actual root‐node dict.
    """
    if isinstance(plan_json, list) and plan_json:
        plan_obj = plan_json[0]
    else:
        plan_obj = plan_json
    # Postgres style: top‐level key "Plan"
    if "Plan" in plan_obj:
        return plan_obj["Plan"]
    else:
        # raise ValueError("no 'Plan' key at top level")
        return plan_obj

def _find_actual_total_time(root_node):
    if "Actual Total Time" not in root_node:
        raise KeyError("'Actual Total Time' not found in root")
    return float(root_node["Actual Total Time"])


def _find_actual_rows(root_node):
    if "Actual Rows" not in root_node:
        raise KeyError("'Actual Rows' not found in root")
    return float(root_node["Actual Rows"])

def _clean_node(node):
    """
    Recursively copy everything except keys starting with 'Actual',
    and recurse into children under key 'Plans' (if present).
    """
    cleaned = {}
    for k, v in node.items():
        if k.startswith("Actual"):
            continue
        if k == "Plans" and isinstance(v, list):
            # each child is itself a dict
            cleaned["Plans"] = [ _clean_node(child) for child in v ]
        else:
            cleaned[k] = v
    return cleaned

def _bucketize_input(node, ds_info, argsP):
    """
    Recursively bucketize keys (Startup Cost, Total Cost, Plan Rows, Plan Width)
    and recurse into children under key 'Plans' (if present).
    """
    cleaned = {}
    for k, v in node.items():
        # if k not in ["Startup Cost", "Total Cost", "Plan Rows", "Plan Width"]:
        #     continue
        if k == "Plans" and isinstance(v, list):
            # each child is itself a dict
            cleaned["Plans"] = [ _bucketize_input(child, ds_info, argsP) for child in v ]
        else:
            if k == "Startup Cost":
                cleaned[k] = ds_info.startup_cost_bucketizer.bucketize_label(v)
                print(f"Startup Cost: {v} => {cleaned[k]}")
            elif k == "Total Cost":
                cleaned[k] = ds_info.total_cost_bucketizer.bucketize_label(v)
                print(f"Total Cost: {v} => {cleaned[k]}")
            elif k == "Plan Rows":
                cleaned[k] = ds_info.plan_rows_bucketizer.bucketize_label(v)
                print(f"Plan Rows: {v} => {cleaned[k]}")
            elif k == "Plan Width":
                cleaned[k] = ds_info.plan_width_bucketizer.bucketize_label(v)
                print(f"Plan Width: {v} => {cleaned[k]}")
            else:
                cleaned[k] = v
    return cleaned

def _remove_act_fields(obj):
    if isinstance(obj, dict):
        return {
            k: _remove_act_fields(v)
            for k, v in obj.items()
            if not k.startswith("act_")
        }
    elif isinstance(obj, list):
        return [_remove_act_fields(item) for item in obj]
    else:
        return obj
    
def _collect_column_ids(node):
    used_cols = set()

    # output_columns
    output = node.get("plan_parameters", {}).get("output_columns", [])
    for out_entry in output:
        used_cols.update(out_entry.get("columns", []))

    # filter_columns
    filter_col = node.get("plan_parameters", {}).get("filter_columns", {})
    if isinstance(filter_col, dict) and "column" in filter_col:
        used_cols.add(filter_col["column"])

    for child in node.get("children", []):
        used_cols.update(_collect_column_ids(child))

    return used_cols

def _collect_column_ids_and_replace(node, stats):
    """
    Recursively traverse `node` (a dict representing one plan‐node), collect all integer
    column‐IDs into a set, and ALSO replace each occurrence of a column‐ID i with stats[i].
    Returns the set of all original IDs found.

    Args:
        node (dict): A single query‐plan node, e.g.
            {
              "plan_parameters": {
                "output_columns": [
                  {"columns": [0, 3, 5]},
                  {"columns": [2]}
                ],
                "filter_columns": {"column": 7, ...}
              },
              "children": [ ...sub‐nodes... ]
            }
        stats (list or dict): A sequence or mapping such that stats[i] is the value
            you want to substitute for column‐ID i.

    Returns:
        set[int]: All unique column‐IDs encountered (before replacement).
    """
    used_cols = set()

    # 1) Handle "output_columns", which is a list of dicts each containing a "columns" list
    plan_params = node.get("plan_parameters", {})
    output_list = plan_params.get("output_columns", [])
    for out_entry in output_list:
        # out_entry might look like {"columns": [0, 3, 5], ...}
        cols = out_entry.get("columns", [])
        for idx, col_id in enumerate(cols):
            # Collect the original integer ID
            used_cols.add(col_id)

            # Replace it in‐place with stats[col_id]
            # (Assumes stats[col_id] exists; if not, you might check bounds first)
            out_entry["columns"][idx] = stats[col_id]

    # 2) Handle "filter_columns", which might be a dict {"column": 7, ...}
    filter_col = plan_params.get("filter_columns", {})
    if isinstance(filter_col, dict) and "column" in filter_col:
        col_id = filter_col["column"]
        if isinstance(col_id, int):
            used_cols.add(col_id)

            # Replace with stats[col_id]
            filter_col["column"] = stats[col_id]

    # 3) Recurse into children
    for child in node.get("children", []):
        used_cols.update(_collect_column_ids_and_replace(child, stats))

    return used_cols

def train_val_test(num_rows, argsP):
    """
    Randomly sample a fraction of the training set.
    """
    total_rows = num_rows
    indices = list(range(total_rows))
    # train 0.7, val 0.15, test 0.15
    train_ids, temp_ids = train_test_split(indices, test_size=0.33, random_state=42)
    val_ids, test_ids = train_test_split(temp_ids, test_size=0.5, random_state=42)
    # train_ids, temp_ids = train_test_split(indices, test_size=0.9, random_state=42)
    # val_ids, test_ids = train_test_split(temp_ids, test_size=0.9, random_state=42)
    return train_ids, val_ids, test_ids

def train_val(num_rows, argsP):
    """
    Randomly sample a fraction of the training set.
    """
    total_rows = num_rows
    indices = list(range(total_rows))
    # train 0.7, val 0.15, test 0.15
    train_ids, val_ids = train_test_split(indices, test_size=0.1, random_state=42)
    return train_ids, val_ids

def prepare_ds_info_norm(ds_info):
    ds_info.cost_norm = Normalizer(np.log(float(ds_info.min_cost) + 0.001), np.log(float(ds_info.max_cost) + 0.001))
    ds_info.card_norm = Normalizer(np.log(float(ds_info.min_card) + 0.001), np.log(float(ds_info.max_card) + 0.001))

def update_ds_info_minmax(ds_info,costs=None, cards=None):
    
    ds_info.min_cost = min(ds_info.min_cost, min(costs))
    ds_info.max_cost = max(ds_info.max_cost, max(costs))
    ds_info.min_card = min(ds_info.min_card, min(cards))
    ds_info.max_card = max(ds_info.max_card, max(cards))

def read_json_and_clean(predictor, ds_info, dat_path, argsP, all=False):
    """
    Reads a CSV with columns ['id','json'] where 'json' is
    a tree‐structured plan.
    For each row, parses JSON, extracts root, grabs its
    Actual Total Time, then cleans away all "Actual..." keys,
    re‐dumps to a string.
    Returns cleaned_texts, costs, lengths, templates (if available)
    """
    print(f"Reading {dat_path}")
    df = pd.read_csv(dat_path)
    cleaned_texts = []
    costs = []
    cards = []
    lengths = []
    templates = []
    
    # Check if template column exists (only for tpch and tpcds)
    has_template = 'template' in df.columns
    
    for idx, raw in enumerate(df["json"]):
        if "failed" in raw:
            continue
        print("*", end='', flush=True)
        plan_json = json.loads(raw)
        root = _extract_root(plan_json)
        costs.append(_find_actual_total_time(root))
        cards.append(_find_actual_rows(root))
        cleaned_root = _clean_node(root)
        if argsP.bucketize_input:
            cleaned_root = _bucketize_input(cleaned_root, ds_info, argsP)
        txt = json.dumps(cleaned_root)
        cleaned_texts.append(txt)
        tok = predictor.tokenizer(txt, add_special_tokens=False)
        lengths.append(len(tok["input_ids"]))
        
        # Extract template if available
        if has_template:
            templates.append(df.iloc[idx]['template'])
        else:
            templates.append(None)

    print(f"Read {len(cleaned_texts)} plans")

    update_ds_info_minmax(ds_info, costs, cards)

    if all:
        return cleaned_texts, costs, cards, lengths, templates
    else:
        if argsP.card:
            return cleaned_texts, cards, lengths, templates
        else:
            return cleaned_texts, costs, lengths, templates


def read_json_and_clean_v2(predictor, ds_info, dat_path, argsP, all=False):
    """
    Reads a json with {"parsed_plans", "database_stats"} where 'parsed_plans' is
    a tree‐structured plan.
    clean: recursively remove the 'act_' keys from the parsed_plans.
    Append used column stats to the cleaned plan for each plan.
    re‐dumps to a string.
    Returns cleaned_texts, costs, lengths, templates (if available)
    """
    print(f"Reading {dat_path}")
    with open(dat_path, 'r') as f:
        original_data = json.load(f)

    costs = []
    cards = []
    templates = []

    cleaned = _remove_act_fields(original_data)

    for raw, cleaned_plan in zip(original_data["parsed_plans"], cleaned["parsed_plans"]):
        print("*", end='', flush=True)
        plan_param = raw.get("plan_parameters", {})
        costs.append(plan_param.get("act_time", None))
        cards.append(plan_param.get("act_card", None))
        
        # Extract template if available
        template = raw.get("template", None)
        templates.append(template)

        used_column_ids = _collect_column_ids_and_replace(cleaned_plan, original_data["database_stats"]["column_stats"])
        # stats = [
        #     original_data["database_stats"]["column_stats"][cid]
        #     for cid in used_column_ids
        #     if isinstance(cid, int) and cid < len(original_data["database_stats"]["column_stats"])
        # ]
        # cleaned_plan["used_column_stats"] = stats

    txts = [json.dumps(cleaned_plan, indent=2) for cleaned_plan in cleaned["parsed_plans"]]
    lengths = [len(predictor.tokenizer(txt, add_special_tokens=False)["input_ids"]) for txt in txts]

    print(f"Read {len(cleaned['parsed_plans'])} plans")
    # print("costs",costs)
    # print("cards",cards)

    update_ds_info_minmax(ds_info, costs, cards)

    if all:
        return txts, costs, cards, lengths, templates
    else:
        if argsP.card:
            return txts, cards, lengths, templates
        else:
            return txts, costs, lengths, templates



def get_embeddings(predictor, ds_info, dat_path, argsP, batch_size=1, normalize_feats=True):
    cache_dir  = "embeddings"
    cache_file = f"embeddings_{argsP.model_name}_bucketize-{argsP.bucketize_input}_pretrained-{argsP.llm_pretrained}_pretrainedTask-{argsP.llm_pretrained_task}_{dat_path}".replace("json", "csv") 
    cache_file = cache_file.replace("/","-")
    cache_path = os.path.join(cache_dir, cache_file)
    if os.path.exists(cache_path):
        # 1) if it has cache, directly use ut
        df        = pd.read_csv(cache_path)
        cards     = df['cards'].tolist()
        costs     = df['costs'].tolist()
        lengths   = df['lengths'].tolist()
        templates = df['templates'].tolist() if 'templates' in df.columns else [None] * len(cards)
        features  = torch.from_numpy(df.drop(columns=['costs', 'cards', 'lengths'] + (['templates'] if 'templates' in df.columns else [])).values).float()
        print(f"Loaded embeddings from {cache_path}")
        update_ds_info_minmax(ds_info, costs, cards)
    else:
        print(f"embedding file {cache_path} not found, creating a new one")
        argsP.inference_logger.info(f"Creating new embedding file for dat_path: {dat_path}")
        if dat_path.endswith("c8220.json"):
            texts, costs, cards, lengths, templates = read_json_and_clean_v2(predictor, ds_info, dat_path, argsP, all=True)
        else:
            texts, costs, cards, lengths, templates = read_json_and_clean(predictor, ds_info, dat_path, argsP, all=True)
        # 2) Otherwise, firstly collect texts and costs of the query plans
        # run through the predictor, collect, then save
        predictor.eval()
        all_embs = []
        with torch.no_grad():
            for i in range(0, len(texts), batch_size):
                print(i, end=' ', flush=True)
                batch_start = timer()
                batch_texts = texts[i : i + batch_size]
                emb      = predictor(batch_texts)      
                all_embs.append(emb.cpu())
                # if using GPU, make sure all kernels are done
                if torch.cuda.is_available():
                    torch.cuda.synchronize()
                batch_end = timer()
                batch_time = batch_end - batch_start
                argsP.inference_logger.info(f"[Infer] Prompt {i} took {batch_time*1000:.2f} ms")
        features = torch.cat(all_embs, dim=0)  # [N, hidden_dim]

        # save to CSV for next time
        output_dir = os.path.dirname(cache_path)
        os.makedirs(output_dir, exist_ok=True)
        df = pd.DataFrame(features.numpy())
        df['costs'] = costs
        df['cards'] = cards
        df['lengths'] = lengths
        if templates and any(t is not None for t in templates):
            df['templates'] = templates
        df.to_csv(cache_path, index=False)
        print(f"Saved embeddings to {cache_path}")              # [N, hidden_dim]
    

    features = downsample_block_mean(features, argsP)

    if normalize_feats:
        feat_norm = FeatureNormalizer()
        features = feat_norm.fit_transform(features)

    # labels = torch.FloatTensor(costs).view(-1, 1)     # [N, 1]
    if argsP.card:
        return features, cards, lengths, templates
    else:
        return features, costs, lengths, templates

def get_llm_ds_from_csv(predictor, dat_path_train_list, dat_path_test, ds_info, argsP):
    """
    1) Reads a CSV with columns ['id','json'] where 'json' is
       a tree‐structured plan.
    2) For each row, parses JSON, extracts root, grabs its
       Actual Total Time, then cleans away all "Actual..." keys,
       re‐dumps to a string.
    3) Calls your existing get_llm_ds(cleaned_texts, costs)
       and returns its TensorDataset.
    """

    argsP.inference_logger.info(f"Getting LLM dataset from {dat_path_train_list} and {dat_path_test}")

    if argsP.algo=="llm_finetune":
        if dat_path_test.endswith("c8220.json"):
            cleaned_texts_test, costs_test, lengths_test, templates_test = read_json_and_clean_v2(predictor, ds_info, dat_path_test, argsP)
        else:
            cleaned_texts_test, costs_test, lengths_test, templates_test = read_json_and_clean(predictor, ds_info, dat_path_test, argsP)
        if len(dat_path_train_list)==1 and dat_path_train_list[0]==dat_path_test:
            train_ids, val_ids, test_ids = train_val_test(len(cleaned_texts_test), argsP)
            cleaned_texts_train = [cleaned_texts_test[idx] for idx in train_ids]
            cleaned_texts_val   = [cleaned_texts_test[idx] for idx in val_ids  ]
            cleaned_texts_test  = [cleaned_texts_test[idx] for idx in test_ids ]
            costs_train = [costs_test[idx] for idx in train_ids]
            costs_val   = [costs_test[idx] for idx in val_ids  ]
            costs_test  = [costs_test[idx] for idx in test_ids ]
            lengths_test  = [lengths_test[idx] for idx in test_ids ]
            templates_test = [templates_test[idx] for idx in test_ids ]
        else:
            cleaned_texts_train, costs_train = [], []
            for dat_path_train in dat_path_train_list:
                if dat_path_train.endswith("c8220.json"):
                    # for the 100k workload, we use the v2 version
                    cleaned_texts, costs, lengths, templates = read_json_and_clean_v2(predictor, ds_info, dat_path_train, argsP)
                else:
                    cleaned_texts, costs, lengths, templates = read_json_and_clean(predictor, ds_info, dat_path_train, argsP)
                cleaned_texts_train.extend(cleaned_texts)
                costs_train.extend(costs)
            train_ids, val_ids= train_val(len(cleaned_texts_train), argsP)
            cleaned_texts_val   = [cleaned_texts_train[idx] for idx in val_ids  ]
            cleaned_texts_train = [cleaned_texts_train[idx] for idx in train_ids]
            costs_val   = [costs_train[idx] for idx in val_ids  ]
            costs_train = [costs_train[idx] for idx in train_ids]

        if hasattr(argsP, 'train_ratio') and 0.0 < argsP.train_ratio < 1.0:
            cleaned_texts_train, costs_train = sample_train(cleaned_texts_train, costs_train, argsP.train_ratio, features_is_list=True)

    elif argsP.algo=="llm":
        embeddings_test, costs_test, lengths_test, templates_test = get_embeddings(predictor, ds_info, dat_path_test, argsP, 1, False) 
        if len(dat_path_train_list)==1 and dat_path_train_list[0]==dat_path_test:
            train_ids, val_ids, test_ids = train_val_test(len(embeddings_test), argsP)
            embeddings_train = embeddings_test[train_ids]
            embeddings_val   = embeddings_test[val_ids]
            embeddings_test  = embeddings_test[test_ids]
            costs_train = [costs_test[idx] for idx in train_ids]
            costs_val   = [costs_test[idx] for idx in val_ids  ]
            costs_test  = [costs_test[idx] for idx in test_ids ]
            lengths_test  = [lengths_test[idx] for idx in test_ids ]
            templates_test = [templates_test[idx] for idx in test_ids ]
        else:
            embeddings_train_list, costs_train = [], []
            for dat_path_train in dat_path_train_list:
                embeddings, costs, lengths, templates = get_embeddings(predictor, ds_info, dat_path_train, argsP, 1, False)
                embeddings_train_list.append(embeddings)
                costs_train.extend(costs)
            embeddings_train = torch.cat(embeddings_train_list, dim=0)
            all_embeddings = torch.cat([embeddings_train, embeddings_test], dim=0)       # [N_train+N_test, D]
            feat_norm     = FeatureNormalizer()
            all_embeddings = feat_norm.fit_transform(all_embeddings)
            Ntr = embeddings_train.size(0)
            embeddings_train = all_embeddings[:Ntr]
            embeddings_test  = all_embeddings[Ntr:]

            train_ids, val_ids= train_val(Ntr, argsP)
            embeddings_val   = embeddings_train[val_ids]
            embeddings_train = embeddings_train[train_ids]
            costs_val   = [costs_train[idx] for idx in val_ids  ]
            costs_train = [costs_train[idx] for idx in train_ids]

        if hasattr(argsP, 'train_ratio') and 0.0 < argsP.train_ratio < 1.0:
            embeddings_train, costs_train = sample_train(embeddings_train, costs_train, argsP.train_ratio, features_is_list=False)

    prepare_ds_info_norm(ds_info)
    # 3) Finally, create the TensorDataset
    if argsP.algo=="llm_finetune":
        if not argsP.card:
            ds_train = QueryPlanDataset(cleaned_texts_train, ds_info.cost_norm.normalize_labels(costs_train))
            ds_val   = QueryPlanDataset(cleaned_texts_val,   ds_info.cost_norm.normalize_labels(costs_val))
            ds_test  = QueryPlanDataset(cleaned_texts_test,  ds_info.cost_norm.normalize_labels(costs_test))
        else:
            ds_train = QueryPlanDataset(cleaned_texts_train, ds_info.card_norm.normalize_labels(costs_train))
            ds_val   = QueryPlanDataset(cleaned_texts_val,   ds_info.card_norm.normalize_labels(costs_val))
            ds_test  = QueryPlanDataset(cleaned_texts_test,  ds_info.card_norm.normalize_labels(costs_test))
        argsP.embed_size = predictor.hidden_dim
        return ds_train, ds_val, ds_test, costs_val, costs_test, lengths_test, templates_test
    else:
        if not argsP.card:
            ds_train = TensorDataset(embeddings_train, torch.FloatTensor(ds_info.cost_norm.normalize_labels(costs_train)).view(-1, 1))
            ds_val   = TensorDataset(embeddings_val,   torch.FloatTensor(ds_info.cost_norm.normalize_labels(costs_val)).view(-1, 1))
            ds_test  = TensorDataset(embeddings_test,  torch.FloatTensor(ds_info.cost_norm.normalize_labels(costs_test)).view(-1, 1))
        else:
            ds_train = TensorDataset(embeddings_train, torch.FloatTensor(ds_info.card_norm.normalize_labels(costs_train)).view(-1, 1))
            ds_val   = TensorDataset(embeddings_val,   torch.FloatTensor(ds_info.card_norm.normalize_labels(costs_val)).view(-1, 1))
            ds_test  = TensorDataset(embeddings_test,  torch.FloatTensor(ds_info.card_norm.normalize_labels(costs_test)).view(-1, 1))
        return ds_train, ds_val, ds_test, costs_val, costs_test, lengths_test, templates_test