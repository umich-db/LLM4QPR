import os
import time
import json
import torch
import torch.nn as nn
import torch.nn.init as init
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, TensorDataset
from transformers import AutoTokenizer, AutoModelForCausalLM, LlamaForCausalLM, LlamaModel, AutoModel, BitsAndBytesConfig
import bitsandbytes, flash_attn
import random
import pandas as pd

# QLoRA and PEFT imports
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training, TaskType
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
from field_categories import FIELD_CATEGORIES, get_fields_to_remove
from field_categories_duckdb import (
    FIELD_CATEGORIES as DUCKDB_FIELD_CATEGORIES,
    get_fields_to_remove as duckdb_get_fields_to_remove,
)


def _get_field_categories(db):
    """Return the appropriate FIELD_CATEGORIES dict for the given database."""
    if db == 'duckdb':
        return DUCKDB_FIELD_CATEGORIES
    return FIELD_CATEGORIES


def _get_fields_to_remove_fn(db):
    """Return the appropriate get_fields_to_remove function for the given database."""
    if db == 'duckdb':
        return duckdb_get_fields_to_remove
    return get_fields_to_remove
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


class QueryPlanDatasetWithStatsTokens(Dataset):
    """Dataset that returns (text, stats_vecs, label).

    stats_vecs: list of numpy arrays (each dim stats_token_dim) corresponding to [STAT] tokens
    inserted into the text.
    """
    def __init__(self, texts, stats_vecs_list, labels):
        assert len(texts) == len(labels) == len(stats_vecs_list)
        self.texts = texts
        self.stats_vecs_list = stats_vecs_list
        self.labels = labels

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return self.texts[idx], self.stats_vecs_list[idx], self.labels[idx]

#########################################
#    QueryPlanPredictor Model Class
#########################################

class QueryPlanPredictor(nn.Module):
    """
    QueryPlanPredictor implementation using BasePredictor functionality.
    This class provides the same interface as the original QueryPlanPredictor but uses
    the more advanced BasePredictor implementation underneath.
    """
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
        window_stride_ratio: float = 0.8,
        use_sliding_window: bool = False,
        quantification: str = "4-bit",
    ):
        """
        Initialize QueryPlanPredictor using BasePredictor functionality.
        
        Args:
            model_name: HuggingFace model name or path
            mode: Model mode ('inference', 'lora', 'last')
            lora_r: LoRA rank
            lora_alpha: LoRA alpha
            lora_dropout: LoRA dropout
            target_modules: Target modules for LoRA
            enable_checkpointing: Whether to enable gradient checkpointing
            offload_folder: Folder for model offloading
            window_stride_ratio: Sliding window stride ratio (default 0.8)
            use_sliding_window: Whether to use sliding window for long texts (default False)
            quantification: Quantization type ('4-bit', '8-bit', 'None')
        """
        super().__init__()
        
        # Store model name for compatibility
        self.model_name = model_name
        
        # Initialize with BasePredictor functionality
        self.mode = mode
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.window_stride_ratio = window_stride_ratio
        self.use_sliding_window = use_sliding_window
        
        print(f"Initializing QueryPlanPredictor with model {model_name}")
        print(f"Mode: {mode}, enable_checkpointing: {enable_checkpointing}, window_stride_ratio: {window_stride_ratio}, use_sliding_window: {use_sliding_window}")
        
        # Initialize tokenizer
        self.tokenizer = self._load_tokenizer(model_name)
        
        # Load model using BasePredictor logic
        self.model = self._load_model(
            model_name, quantification, enable_checkpointing, offload_folder,
            True, lora_r, lora_alpha, lora_dropout, target_modules, mode
        )
        
        # Get hidden dimension
        self.hidden_dim = self._infer_hidden_dim(self.model)
        
        # Handle parameter freezing based on mode (same as original)
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
                # For PEFT models, structure is: base_model.model.model.layers.{layer_idx}.{rest}
                # So layer index is at split index 4, not 3
                parts = name.split(".")
                layer_ok = (
                    name.startswith("base_model.model.model.layers")
                    and len(parts) > 4
                    and parts[4] == str(self.model.config.num_hidden_layers - 1)
                )
                if p.dtype.is_floating_point or p.dtype.is_complex:
                    p.requires_grad = layer_ok
                else:
                    # All bitsandbytes-quantized (int/4-bit) tensors or buffers get frozen
                    p.requires_grad = False
                print(name, parts[4] if len(parts) > 4 else "N/A", p.requires_grad)
        else:
            raise ValueError(f"Unknown mode {mode!r}")

    def _load_tokenizer(self, model_name: str):
        """Load and configure tokenizer for the model."""
        try:
            if "gpt2" in model_name.lower():
                from transformers import GPT2TokenizerFast
                tokenizer = GPT2TokenizerFast.from_pretrained(model_name)
            elif "qwen" in model_name.lower() or "qwen3" in model_name.lower():
                tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
            elif "modernbert" in model_name.lower():
                tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
            elif "bert" in model_name.lower():
                tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
            elif "google/" in model_name.lower() or "gemma" in model_name.lower():
                tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
            else:
                tokenizer = AutoTokenizer.from_pretrained(model_name)
        except Exception:
            # Fallback to slow tokenizer if fast conversion fails (e.g. DeBERTa-v3)
            print(f"Fast tokenizer failed for {model_name}, falling back to slow tokenizer")
            tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False, trust_remote_code=True)
        
        # Set pad token if not present
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            
        return tokenizer
    
    def _load_model(self, model_name, quantification, enable_checkpointing, offload_folder, 
                   use_lora, lora_r, lora_alpha, lora_dropout, target_modules, mode):
        """
        Unified model loading function supporting multiple model types.
        """
        if "llama" in model_name.lower():
            return self._load_llama_model(model_name, quantification, offload_folder, 
                                        use_lora, lora_r, lora_alpha, lora_dropout, target_modules, enable_checkpointing)
        elif "modernbert" in model_name.lower():
            return self._load_modernbert_model(model_name, quantification, enable_checkpointing, offload_folder,
                                             use_lora, lora_r, lora_alpha, lora_dropout, target_modules, mode)
        elif "bert" in model_name.lower() or "electra" in model_name.lower():
            # distilgpt2 has "bert" in publisher name but is a GPT-2 model
            if "gpt2" in model_name.lower():
                return self._load_gpt2_model(model_name, quantification, enable_checkpointing, offload_folder,
                                            use_lora, lora_r, lora_alpha, lora_dropout, target_modules, mode)
            return self._load_bert_model(model_name, quantification, enable_checkpointing, offload_folder,
                                       use_lora, lora_r, lora_alpha, lora_dropout, target_modules, mode)
        elif "gpt2" in model_name:
            return self._load_gpt2_model(model_name, quantification, enable_checkpointing, offload_folder,
                                       use_lora, lora_r, lora_alpha, lora_dropout, target_modules, mode)
        elif "gpt-oss-20b" in model_name.lower() or "openai/gpt-oss-20b" in model_name.lower():
            return self._load_gpt_oss_model(model_name)
        elif "qwen" in model_name.lower() or "qwen3" in model_name.lower():
            return self._load_qwen_model(model_name, quantification, offload_folder,
                                       use_lora, lora_r, lora_alpha, lora_dropout, target_modules)
        elif "sentence-transformers" in model_name or "all-MiniLM-L6-v2" in model_name:
            return self._load_sentence_transformers_model(model_name, quantification, enable_checkpointing, offload_folder,
                                                        use_lora, lora_r, lora_alpha, lora_dropout, target_modules, mode)
        elif "intfloat" in model_name.lower() or "e5-" in model_name.lower():
            return self._load_sentence_transformers_model(model_name, quantification, enable_checkpointing, offload_folder,
                                                        use_lora, lora_r, lora_alpha, lora_dropout, target_modules, mode)
        elif "nomic" in model_name.lower():
            return self._load_sentence_transformers_model(model_name, quantification, enable_checkpointing, offload_folder,
                                                        use_lora, lora_r, lora_alpha, lora_dropout, target_modules, mode)
        elif "google/" in model_name.lower() or "gemma" in model_name.lower():
            return self._load_google_model(model_name, quantification, offload_folder,
                                         use_lora, lora_r, lora_alpha, lora_dropout, target_modules)
        else:
            # Generic fallback: AutoModel for any HuggingFace model
            return self._load_generic_model(model_name, quantification, enable_checkpointing, offload_folder,
                                           use_lora, lora_r, lora_alpha, lora_dropout, target_modules, mode)

    def _infer_hidden_dim(self, model) -> int:
        """
        Robustly infer the model's hidden/embedding dimension across different architectures.
        Tries common config fields, then input embedding size, then text_config fallback.
        """
        cfg = getattr(model, 'config', None)
        # Try common config attributes
        # word_embed_proj_dim (OPT models) takes priority — it's the actual output dim
        # when different from hidden_size
        for attr in [
            'word_embed_proj_dim',
            'hidden_size', 'd_model', 'n_embd', 'model_dim', 'hidden_dim', 'embed_dim', 'transformer_dim'
        ]:
            if cfg is not None and hasattr(cfg, attr):
                val = getattr(cfg, attr)
                try:
                    iv = int(val)
                    if iv > 0:
                        return iv
                except Exception:
                    pass
        # Try input embedding module
        try:
            emb = model.get_input_embeddings()
            if hasattr(emb, 'embedding_dim'):
                return int(emb.embedding_dim)
            if hasattr(emb, 'weight') and hasattr(emb.weight, 'shape'):
                return int(emb.weight.shape[1])
        except Exception:
            pass
        # Try text_config (used by some models)
        try:
            if cfg is not None and hasattr(cfg, 'text_config') and hasattr(cfg.text_config, 'hidden_size'):
                return int(cfg.text_config.hidden_size)
        except Exception:
            pass
        raise ValueError("Unable to infer model hidden dimension from config or embeddings.")
    
    def _load_llama_model(self, model_name, quantification, offload_folder, 
                         use_lora, lora_r, lora_alpha, lora_dropout, target_modules, enable_checkpointing=True):
        """Load Llama model."""
        print(f"Loading Llama model: {model_name}")
        print(f"Tokenizer max length: {self.tokenizer.model_max_length}")
        
        # Report max input length
        try:
            from transformers import AutoConfig
            config = AutoConfig.from_pretrained(model_name, trust_remote_code=True)
            max_position_embeddings = getattr(config, 'max_position_embeddings', None)
            n_positions = getattr(config, 'n_positions', None)
            max_seq_length = getattr(config, 'max_seq_length', None)
            
            print(f"=== Llama Model Max Input Length ===")
            if max_position_embeddings:
                print(f"Max position embeddings: {max_position_embeddings}")
            if n_positions:
                print(f"N positions: {n_positions}")
            if max_seq_length:
                print(f"Max sequence length: {max_seq_length}")
            print(f"Effective max input length: {self.tokenizer.model_max_length}")
            
        except Exception as e:
            print(f"Could not load model config: {e}")
            print(f"Using tokenizer max length: {self.tokenizer.model_max_length}")
        
        
        # OLD CODE - COMMENTED OUT
        # # Determine device map based on available GPUs
        # if torch.cuda.device_count() > 1 and hasattr(self, 'use_model_parallelism') and self.use_model_parallelism:
        #     # Use auto device map for multi-GPU
        #     device_map = "auto"
        # else:
        #     # Use specific device for single GPU
        #     device_map = self.device if hasattr(self, 'device') else "cuda:0"
        # 
        # if use_4bit:
        #     bnb_config = BitsAndBytesConfig(
        #         load_in_4bit=True,
        #         bnb_4bit_use_double_quant=True,
        #         bnb_4bit_quant_type="nf4",
        #         bnb_4bit_compute_dtype=torch.float16
        #     )
        #     model = AutoModelForCausalLM.from_pretrained(
        #         model_name,
        #         quantization_config=bnb_config,
        #         device_map=device_map,
        #         attn_implementation="flash_attention_2",
        #         trust_remote_code=True,
        #         offload_folder=offload_folder
        #     )
        # else:
        #     model = AutoModelForCausalLM.from_pretrained(
        #         model_name,
        #         device_map=device_map,
        #         torch_dtype=torch.float16,
        #         attn_implementation="flash_attention_2",
        #         trust_remote_code=True,
        #         offload_folder=offload_folder
        #     )
        # 
        # model = prepare_model_for_kbit_training(model)
        # 
        # lora_config = LoraConfig(
        #     r=lora_r,
        #     lora_alpha=lora_alpha,
        #     target_modules=target_modules or ["q_proj", "v_proj"],
        #     lora_dropout=lora_dropout,
        #     bias="none",
        #     task_type=TaskType.CAUSAL_LM,
        # )
        # return get_peft_model(model, lora_config)

        # NEW CODE - COMMENTED OUT
        # # NEW CODE - 4-bit loading with QLoRA setup
        # # 2) Load the LLM backbone in 4-bit, with optional offloading
        # #     - torch_dtype=torch.float16: internal compute in fp16
        # #     - load_in_4bit=True: quantize weights to 4-bit
        # #     - device_map="auto": HF/Accelerate will assign layers to GPU/CPU
        # #     - offload_folder=...: if set, accelerate will spill weights to disk/CPU
        # load_kwargs = {
        #     "pretrained_model_name_or_path": model_name,
        #     "torch_dtype": torch.float16,
        #     "load_in_4bit": True,
        #     "device_map": "auto",
        #     # "use_flash_attention_2": False,
        # }
        # if offload_folder:
        #     # If you want to offload weights to CPU/disk:
        #     load_kwargs["offload_folder"] = offload_folder
        #     load_kwargs["offload_state_dict"] = True
        # 
        # self.model = LlamaForCausalLM.from_pretrained(**load_kwargs)
        # # self.model = LlamaModel.from_pretrained(**load_kwargs)
        # 
        # # 3) (Optional) enable gradient checkpointing on the backbone
        # if enable_checkpointing:
        #     # This tells HF to checkpoint inner layers during forward
        #     # so they are recomputed in backward.
        #     self.model.gradient_checkpointing_enable()
        # 
        # # 4) Prepare for QLoRA (freeze 4-bit weights + enable adapter injection)
        # self.model = prepare_model_for_kbit_training(self.model)
        # 
        # # 5) Inject LoRA adapters
        # if target_modules is None:
        #     target_modules = ["q_proj", "v_proj"]
        # lora_cfg = LoraConfig(
        #     r=lora_r,
        #     lora_alpha=lora_alpha,
        #     target_modules=target_modules,
        #     lora_dropout=lora_dropout,
        #     bias="none",
        #     task_type="CAUSAL_LM",
        #     # bnb_4bit_compute_dtype=torch.float16,  # do 4-bit matmuls in fp16
        # )
        # self.model = get_peft_model(self.model, lora_cfg)
        # 
        # return self.model

        # THIRD CODE - Old format with default quantization settings
        # Determine device map based on available GPUs
        if torch.cuda.device_count() > 1 and hasattr(self, 'use_model_parallelism') and self.use_model_parallelism:
            # Use auto device map for multi-GPU
            device_map = "auto"
        else:
            # Use specific device for single GPU
            device_map = self.device if hasattr(self, 'device') else "cuda:0"
        
        if quantification == "4-bit":
            # Use 4-bit quantization settings
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=False,     # Default: False
                bnb_4bit_quant_type="fp4",          # Default: fp4
                bnb_4bit_compute_dtype=torch.float16  # Default: float32
            )
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                quantization_config=bnb_config,
                device_map=device_map,
                attn_implementation="flash_attention_2",
                trust_remote_code=True,
                offload_folder=offload_folder
            )
        elif quantification == "8-bit":
            # Use 8-bit quantization settings
            bnb_config = BitsAndBytesConfig(
                load_in_8bit=True,
                llm_int8_threshold=6.0,
                llm_int8_has_fp16_weight=False,
                llm_int8_skip_modules=None
            )
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                quantization_config=bnb_config,
                device_map=device_map,
                attn_implementation="flash_attention_2",
                trust_remote_code=True,
                offload_folder=offload_folder
            )
        else:  # quantification == "None"
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map=device_map,
                torch_dtype=torch.float16,
                attn_implementation="flash_attention_2",
                trust_remote_code=True,
                offload_folder=offload_folder
            )

        # Only prepare for kbit training if quantization is used
        if quantification != "None":
            model = prepare_model_for_kbit_training(model)

        lora_config = LoraConfig(
            r=lora_r,
            lora_alpha=lora_alpha,
            target_modules=target_modules or ["q_proj", "v_proj"],
            lora_dropout=lora_dropout,
            bias="none",
            task_type=TaskType.CAUSAL_LM,
        )
        return get_peft_model(model, lora_config)
    
    def _load_modernbert_model(self, model_name, quantification, enable_checkpointing, offload_folder,
                              use_lora, lora_r, lora_alpha, lora_dropout, target_modules, mode):
        """Load ModernBERT model."""
        print(f"Loading ModernBERT model: {model_name}")
        print(f"Tokenizer max length: {self.tokenizer.model_max_length}")
        
        # Report max input length and fix absurd tokenizer defaults
        try:
            from transformers import AutoConfig
            config = AutoConfig.from_pretrained(model_name, trust_remote_code=True)
            max_position_embeddings = getattr(config, 'max_position_embeddings', None)
            max_seq_length = getattr(config, 'max_seq_length', None)

            print(f"=== ModernBERT Model Max Input Length ===")
            if max_position_embeddings:
                print(f"Max position embeddings: {max_position_embeddings}")
            if max_seq_length:
                print(f"Max sequence length: {max_seq_length}")

            # Some ModernBERT tokenizers report model_max_length as ~1e30;
            # cap it to max_position_embeddings to avoid integer overflow.
            if self.tokenizer.model_max_length > 1_000_000 and max_position_embeddings:
                self.tokenizer.model_max_length = max_position_embeddings
                print(f"Capped tokenizer.model_max_length to {max_position_embeddings}")

            print(f"Effective max input length: {self.tokenizer.model_max_length}")
        except Exception as e:
            print(f"Could not load model config: {e}")
            if self.tokenizer.model_max_length > 1_000_000:
                self.tokenizer.model_max_length = 8192
                print(f"Capped tokenizer.model_max_length to 8192 (fallback)")
            print(f"Using tokenizer max length: {self.tokenizer.model_max_length}")


        # Determine device map based on available GPUs
        if torch.cuda.device_count() > 1 and hasattr(self, 'use_model_parallelism') and self.use_model_parallelism:
            # Use auto device map for multi-GPU
            device_map = "auto"
        else:
            # Use specific device for single GPU
            device_map = self.device if hasattr(self, 'device') else "cuda:0"
        
        if quantification == "4-bit":
            # Use 4-bit quantization settings
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=False,     # Match Llama: Default False
                bnb_4bit_quant_type="fp4",          # Match Llama: Default fp4
                bnb_4bit_compute_dtype=torch.float16  # Match Llama: Default float32
            )
            model = AutoModel.from_pretrained(
                model_name,
                quantization_config=bnb_config,
                device_map=device_map,
                trust_remote_code=True,
                offload_folder=offload_folder
            )
        elif quantification == "8-bit":
            # Use 8-bit quantization settings
            bnb_config = BitsAndBytesConfig(
                load_in_8bit=True,
                llm_int8_threshold=6.0,
                llm_int8_has_fp16_weight=False,
                llm_int8_skip_modules=None
            )
            model = AutoModel.from_pretrained(
                model_name,
                quantization_config=bnb_config,
                device_map=device_map,
                trust_remote_code=True,
                offload_folder=offload_folder
            )
        else:  # quantification == "None"
            model = AutoModel.from_pretrained(
                model_name,
                device_map=device_map,
                torch_dtype=torch.float16,
                trust_remote_code=True,
                offload_folder=offload_folder
            )
        
        if enable_checkpointing and mode != "inference":
            model.gradient_checkpointing_enable()
            print("Gradient checkpointing enabled")
        
        # Only prepare for kbit training if quantization is used
        if quantification != "None":
            model = prepare_model_for_kbit_training(model)
        
        lora_config = LoraConfig(
            r=lora_r,
            lora_alpha=lora_alpha,
            target_modules=target_modules or ["Wqkv"],
            lora_dropout=lora_dropout,
            bias="none",
            task_type=TaskType.FEATURE_EXTRACTION,
        )
        return get_peft_model(model, lora_config)
    
    def _load_bert_model(self, model_name, quantification, enable_checkpointing, offload_folder,
                        use_lora, lora_r, lora_alpha, lora_dropout, target_modules, mode):
        """Load BERT model."""
        print(f"Loading BERT model: {model_name}")
        print(f"Tokenizer max length: {self.tokenizer.model_max_length}")
        
        # Report max input length
        try:
            from transformers import AutoConfig
            config = AutoConfig.from_pretrained(model_name, trust_remote_code=True)
            max_position_embeddings = getattr(config, 'max_position_embeddings', None)
            max_seq_length = getattr(config, 'max_seq_length', None)
            
            print(f"=== BERT Model Max Input Length ===")
            if max_position_embeddings:
                print(f"Max position embeddings: {max_position_embeddings}")
            if max_seq_length:
                print(f"Max sequence length: {max_seq_length}")
            # Cap absurd tokenizer.model_max_length (some models report ~1e30)
            if self.tokenizer.model_max_length > 1_000_000 and max_position_embeddings:
                self.tokenizer.model_max_length = max_position_embeddings
                print(f"Capped tokenizer.model_max_length to {max_position_embeddings}")
            print(f"Effective max input length: {self.tokenizer.model_max_length}")
        except Exception as e:
            print(f"Could not load model config: {e}")
            print(f"Using tokenizer max length: {self.tokenizer.model_max_length}")
        
        
        # Determine device map based on available GPUs
        if torch.cuda.device_count() > 1 and hasattr(self, 'use_model_parallelism') and self.use_model_parallelism:
            # Use auto device map for multi-GPU
            device_map = "auto"
        else:
            # Use specific device for single GPU
            device_map = self.device if hasattr(self, 'device') else "cuda:0"
        
        # DeBERTa-v3 overflows with float16/bfloat16; use float32
        dtype = torch.float32 if "deberta" in model_name.lower() else torch.float16

        if quantification == "4-bit":
            # Use 4-bit quantization settings
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=False,     # Match Llama: Default False
                bnb_4bit_quant_type="fp4",          # Match Llama: Default fp4
                bnb_4bit_compute_dtype=dtype
            )
            model = AutoModel.from_pretrained(
                model_name,
                quantization_config=bnb_config,
                device_map=device_map,
                torch_dtype=dtype,
                trust_remote_code=True,
                offload_folder=offload_folder
            )
        elif quantification == "8-bit":
            # Use 8-bit quantization settings
            bnb_config = BitsAndBytesConfig(
                load_in_8bit=True,
                llm_int8_threshold=6.0,
                llm_int8_has_fp16_weight=False,
                llm_int8_skip_modules=None
            )
            model = AutoModel.from_pretrained(
                model_name,
                quantization_config=bnb_config,
                device_map=device_map,
                torch_dtype=dtype,
                trust_remote_code=True,
                offload_folder=offload_folder
            )
        else:  # quantification == "None"
            model = AutoModel.from_pretrained(
                model_name,
                device_map=device_map,
                torch_dtype=dtype,
                trust_remote_code=True,
                offload_folder=offload_folder
            )
        
        if enable_checkpointing and mode != "inference":
            model.gradient_checkpointing_enable()
            print("Gradient checkpointing enabled")

        # Only prepare for kbit training if quantization is used
        if quantification != "None":
            supports_gc = getattr(model, "supports_gradient_checkpointing", True)
            model = prepare_model_for_kbit_training(
                model, use_gradient_checkpointing=supports_gc
            )

        # Auto-detect LoRA target modules if not specified
        if target_modules:
            default_targets = target_modules
        else:
            module_names = {n.split('.')[-1] for n, m in model.named_modules() if isinstance(m, nn.Linear)}
            if {"query", "value"} <= module_names:
                default_targets = ["query", "value"]
            elif {"query_proj", "value_proj"} <= module_names:
                default_targets = ["query_proj", "value_proj"]
            elif {"q_lin", "v_lin"} <= module_names:
                default_targets = ["q_lin", "v_lin"]
            elif {"q", "v"} <= module_names:
                default_targets = ["q", "v"]
            elif {"q_proj", "v_proj"} <= module_names:
                default_targets = ["q_proj", "v_proj"]
            elif {"Wqkv"} <= module_names:
                default_targets = ["Wqkv"]
            else:
                default_targets = ["query", "value"]
            print(f"[bert] LoRA target modules: {default_targets}")
        lora_config = LoraConfig(
            r=lora_r,
            lora_alpha=lora_alpha,
            target_modules=default_targets,
            lora_dropout=lora_dropout,
            bias="none",
            task_type=TaskType.FEATURE_EXTRACTION,
        )
        return get_peft_model(model, lora_config)
    
    def _load_gpt2_model(self, model_name, quantification, enable_checkpointing, offload_folder,
                        use_lora, lora_r, lora_alpha, lora_dropout, target_modules, mode):
        """Load GPT2 model."""
        print(f"Loading GPT-2 model: {model_name}")
        print(f"Tokenizer max length: {self.tokenizer.model_max_length}")
        
        # Report max input length
        try:
            from transformers import AutoConfig
            config = AutoConfig.from_pretrained(model_name, trust_remote_code=True)
            max_position_embeddings = getattr(config, 'max_position_embeddings', None)
            n_positions = getattr(config, 'n_positions', None)
            max_seq_length = getattr(config, 'max_seq_length', None)
            
            print(f"=== GPT-2 Model Max Input Length ===")
            if max_position_embeddings:
                print(f"Max position embeddings: {max_position_embeddings}")
            if n_positions:
                print(f"N positions: {n_positions}")
            if max_seq_length:
                print(f"Max sequence length: {max_seq_length}")
            print(f"Effective max input length: {self.tokenizer.model_max_length}")
        except Exception as e:
            print(f"Could not load model config: {e}")
            print(f"Using tokenizer max length: {self.tokenizer.model_max_length}")
        
        
        from transformers import GPT2Model
        
        if quantification == "4-bit":
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=False,     # Match Llama: Default False
                bnb_4bit_quant_type="fp4",          # Match Llama: Default fp4
                bnb_4bit_compute_dtype=torch.float16  # Match Llama: Default float32
            )
            model = GPT2Model.from_pretrained(
                model_name,
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=True,
                offload_folder=offload_folder
            )
        elif quantification == "8-bit":
            bnb_config = BitsAndBytesConfig(
                load_in_8bit=True,
                llm_int8_threshold=6.0,
                llm_int8_has_fp16_weight=False,
                llm_int8_skip_modules=None
            )
            model = GPT2Model.from_pretrained(
                model_name,
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=True,
                offload_folder=offload_folder
            )
        else:  # quantification == "None"
            model = GPT2Model.from_pretrained(
                model_name,
                device_map="auto",
                torch_dtype=torch.float16,
                trust_remote_code=True,
                offload_folder=offload_folder
            )
        
        if enable_checkpointing and mode != "inference":
            model.gradient_checkpointing_enable()
            print("Gradient checkpointing enabled")
        
        # Only prepare for kbit training if quantization is used
        if quantification != "None":
            model = prepare_model_for_kbit_training(model)
        
        lora_config = LoraConfig(
            r=lora_r,
            lora_alpha=lora_alpha,
            target_modules=target_modules or ["c_attn", "c_proj"],
            lora_dropout=lora_dropout,
            bias="none",
            task_type=TaskType.FEATURE_EXTRACTION,
        )
        return get_peft_model(model, lora_config)
    
    def _load_gpt_oss_model(self, model_name):
        """Load GPT-OSS-20B model."""
        print(f"Loading GPT-OSS model: {model_name}")
        print(f"Tokenizer max length: {self.tokenizer.model_max_length}")
        
        from transformers import AutoConfig
        config = AutoConfig.from_pretrained(model_name)
        
        # Report max input length
        try:
            max_position_embeddings = getattr(config, 'max_position_embeddings', None)
            n_positions = getattr(config, 'n_positions', None)
            max_seq_length = getattr(config, 'max_seq_length', None)
            
            print(f"=== GPT-OSS Model Max Input Length ===")
            if max_position_embeddings:
                print(f"Max position embeddings: {max_position_embeddings}")
            if n_positions:
                print(f"N positions: {n_positions}")
            if max_seq_length:
                print(f"Max sequence length: {max_seq_length}")
            print(f"Effective max input length: {self.tokenizer.model_max_length}")
        except Exception as e:
            print(f"Could not load model config: {e}")
            print(f"Using tokenizer max length: {self.tokenizer.model_max_length}")
        
        
        try:
            from transformers import Mxfp4Config
            quantization_config = Mxfp4Config.from_dict(config.quantization_config)
        except ImportError:
            print("Warning: Mxfp4Config not available, using default quantization")
            quantization_config = None

        return AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=quantization_config,
            torch_dtype="auto",
            device_map="cuda",
        )
    
    def _load_qwen_model(self, model_name, quantification, offload_folder,
                        use_lora, lora_r, lora_alpha, lora_dropout, target_modules):
        """Load Qwen model."""
        print(f"Loading Qwen model: {model_name}")
        print(f"Tokenizer max length: {self.tokenizer.model_max_length}")
        
        # Report max input length
        try:
            from transformers import AutoConfig
            config = AutoConfig.from_pretrained(model_name, trust_remote_code=True)
            max_position_embeddings = getattr(config, 'max_position_embeddings', None)
            n_positions = getattr(config, 'n_positions', None)
            max_seq_length = getattr(config, 'max_seq_length', None)
            
            print(f"=== Qwen Model Max Input Length ===")
            if max_position_embeddings:
                print(f"Max position embeddings: {max_position_embeddings}")
            if n_positions:
                print(f"N positions: {n_positions}")
            if max_seq_length:
                print(f"Max sequence length: {max_seq_length}")
            print(f"Effective max input length: {self.tokenizer.model_max_length}")
        except Exception as e:
            print(f"Could not load model config: {e}")
            print(f"Using tokenizer max length: {self.tokenizer.model_max_length}")
        
        if quantification == "4-bit":
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=False,     # Match Llama: Default False
                bnb_4bit_quant_type="fp4",          # Match Llama: Default fp4
                bnb_4bit_compute_dtype=torch.float16  # Match Llama: Default float32
            )
            model = AutoModel.from_pretrained(
                model_name,
                quantization_config=bnb_config,
                device_map="auto",
                torch_dtype=torch.float16,
                attn_implementation="flash_attention_2",
                trust_remote_code=True,
                offload_folder=offload_folder
            )
        elif quantification == "8-bit":
            bnb_config = BitsAndBytesConfig(
                load_in_8bit=True,
                llm_int8_threshold=6.0,
                llm_int8_has_fp16_weight=False,
                llm_int8_skip_modules=None
            )
            model = AutoModel.from_pretrained(
                model_name,
                quantization_config=bnb_config,
                device_map="auto",
                torch_dtype=torch.float16,
                attn_implementation="flash_attention_2",
                trust_remote_code=True,
                offload_folder=offload_folder
            )
        else:  # quantification == "None"
            model = AutoModel.from_pretrained(
                model_name,
                device_map="auto",
                torch_dtype=torch.float16,
                attn_implementation="flash_attention_2",
                trust_remote_code=True,
                offload_folder=offload_folder
            )
        
        # Only prepare for kbit training if quantization is used
        if quantification != "None":
            model = prepare_model_for_kbit_training(model)
        
        lora_config = LoraConfig(
            r=lora_r,
            lora_alpha=lora_alpha,
            target_modules=target_modules or ["q_proj", "v_proj"],
            lora_dropout=lora_dropout,
            bias="none",
            task_type=TaskType.FEATURE_EXTRACTION,
        )
        return get_peft_model(model, lora_config)
    
    def _load_sentence_transformers_model(self, model_name, quantification, enable_checkpointing, offload_folder,
                                        use_lora, lora_r, lora_alpha, lora_dropout, target_modules, mode):
        """Load sentence-transformers model."""
        print(f"Loading Sentence Transformers model: {model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        print(f"Tokenizer max length: {self.tokenizer.model_max_length}")
        
        # Report max input length
        try:
            from transformers import AutoConfig
            config = AutoConfig.from_pretrained(model_name, trust_remote_code=True)
            max_position_embeddings = getattr(config, 'max_position_embeddings', None)
            max_seq_length = getattr(config, 'max_seq_length', None)
            
            print(f"=== Sentence Transformers Model Max Input Length ===")
            if max_position_embeddings:
                print(f"Max position embeddings: {max_position_embeddings}")
            if max_seq_length:
                print(f"Max sequence length: {max_seq_length}")
            # Cap absurd tokenizer.model_max_length (some models report ~1e30)
            if self.tokenizer.model_max_length > 1_000_000 and max_position_embeddings:
                self.tokenizer.model_max_length = max_position_embeddings
                print(f"Capped tokenizer.model_max_length to {max_position_embeddings}")
            print(f"Effective max input length: {self.tokenizer.model_max_length}")
        except Exception as e:
            print(f"Could not load model config: {e}")
            print(f"Using tokenizer max length: {self.tokenizer.model_max_length}")
        
        if quantification == "4-bit":
            from transformers import BitsAndBytesConfig
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=False,     # Match Llama: Default False
                bnb_4bit_quant_type="fp4",          # Match Llama: Default fp4
                bnb_4bit_compute_dtype=torch.float16  # Match Llama: Default float32
            )
            self.model = AutoModel.from_pretrained(
                model_name,
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=True,
                offload_folder=offload_folder
            )
        elif quantification == "8-bit":
            from transformers import BitsAndBytesConfig
            bnb_config = BitsAndBytesConfig(
                load_in_8bit=True,
                llm_int8_threshold=6.0,
                llm_int8_has_fp16_weight=False,
                llm_int8_skip_modules=None
            )
            self.model = AutoModel.from_pretrained(
                model_name,
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=True,
                offload_folder=offload_folder
            )
        else:  # quantification == "None"
            self.model = AutoModel.from_pretrained(
                model_name,
                device_map="auto",
                torch_dtype=torch.float16,
                trust_remote_code=True,
                offload_folder=offload_folder
            )
        if enable_checkpointing and mode != "inference":
            if getattr(self.model, "supports_gradient_checkpointing", True):
                self.model.gradient_checkpointing_enable()
                print("Gradient checkpointing enabled")
            else:
                print(f"Skipping gradient checkpointing (not supported by {type(self.model).__name__})")
        # Always apply LoRA (even in inference mode) so that state_dict keys match
        # when loading finetuned weights saved from a PeftModel
        if quantification != "None":
            supports_gc = getattr(self.model, "supports_gradient_checkpointing", True)
            self.model = prepare_model_for_kbit_training(
                self.model, use_gradient_checkpointing=supports_gc
            )
        # LoRA configuration for sentence-transformers models (typically BERT-based)
        # Auto-detect target modules from model architecture
        if target_modules:
            default_targets = target_modules
        elif "nomic" in model_name.lower():
            default_targets = ["Wqkv", "out_proj"]
        else:
            module_names = {n.split('.')[-1] for n, m in self.model.named_modules() if isinstance(m, nn.Linear)}
            if {"query", "value"} <= module_names:
                default_targets = ["query", "value"]
            elif {"query_proj", "value_proj"} <= module_names:
                default_targets = ["query_proj", "value_proj"]
            elif {"q_lin", "v_lin"} <= module_names:
                default_targets = ["q_lin", "v_lin"]
            elif {"q", "v"} <= module_names:
                default_targets = ["q", "v"]
            elif {"q_proj", "v_proj"} <= module_names:
                default_targets = ["q_proj", "v_proj"]
            else:
                default_targets = ["query", "value"]
            print(f"[sentence-transformers] LoRA target modules: {default_targets}")
        lora_config = LoraConfig(
            r=lora_r,
            lora_alpha=lora_alpha,
            target_modules=default_targets,
            lora_dropout=lora_dropout,
            bias="none",
            task_type=TaskType.FEATURE_EXTRACTION,
        )
        self.model = get_peft_model(self.model, lora_config)

        # NomicBertModel.forward() does not accept output_attentions/output_hidden_states
        # but PEFT injects them. Patch the underlying forward to strip unsupported kwargs.
        if "nomic" in model_name.lower() and not "modernbert" in model_name.lower():
            base_model = self.model.base_model.model
            _original_nomic_forward = base_model.forward
            def _patched_nomic_forward(*args, **kwargs):
                kwargs.pop('output_attentions', None)
                kwargs.pop('output_hidden_states', None)
                return _original_nomic_forward(*args, **kwargs)
            base_model.forward = _patched_nomic_forward

        return self.model

    def _load_generic_model(self, model_name, quantification, enable_checkpointing, offload_folder,
                            use_lora, lora_r, lora_alpha, lora_dropout, target_modules, mode):
        """Generic fallback loader using AutoModel for any HuggingFace model.
        Handles SmolLM, Pythia, OPT, GPT-Neo, MiniLM, and other unseen models."""
        print(f"Loading model (generic AutoModel): {model_name}")

        # Report max input length
        try:
            from transformers import AutoConfig
            config = AutoConfig.from_pretrained(model_name, trust_remote_code=True)
            max_pos = getattr(config, 'max_position_embeddings', None)
            print(f"=== Generic Model Max Input Length ===")
            if max_pos:
                print(f"Max position embeddings: {max_pos}")
            if self.tokenizer.model_max_length > 1_000_000 and max_pos:
                self.tokenizer.model_max_length = max_pos
                print(f"Capped tokenizer.model_max_length to {max_pos}")
            print(f"Effective max input length: {self.tokenizer.model_max_length}")
        except Exception as e:
            print(f"Could not load model config: {e}")

        if quantification == "4-bit":
            from transformers import BitsAndBytesConfig
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=False,
                bnb_4bit_quant_type="fp4",
                bnb_4bit_compute_dtype=torch.float16
            )
            model = AutoModel.from_pretrained(
                model_name,
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=True,
                offload_folder=offload_folder
            )
        elif quantification == "8-bit":
            from transformers import BitsAndBytesConfig
            bnb_config = BitsAndBytesConfig(
                load_in_8bit=True,
                llm_int8_threshold=6.0,
                llm_int8_has_fp16_weight=False,
            )
            model = AutoModel.from_pretrained(
                model_name,
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=True,
                offload_folder=offload_folder
            )
        else:
            model = AutoModel.from_pretrained(
                model_name,
                device_map="auto",
                torch_dtype=torch.float16,
                trust_remote_code=True,
                offload_folder=offload_folder
            )

        if enable_checkpointing and mode != "inference":
            if hasattr(model, 'gradient_checkpointing_enable'):
                model.gradient_checkpointing_enable()
                print("Gradient checkpointing enabled")

        if use_lora:
            if quantification != "None":
                supports_gc = getattr(model, "supports_gradient_checkpointing", True)
                model = prepare_model_for_kbit_training(
                    model, use_gradient_checkpointing=supports_gc
                )
            # Auto-detect LoRA target modules
            if target_modules:
                default_targets = target_modules
            else:
                # Try common target module names
                module_names = {n.split('.')[-1] for n, _ in model.named_modules() if isinstance(_, nn.Linear)}
                if {"q_proj", "v_proj"} <= module_names:
                    default_targets = ["q_proj", "v_proj"]
                elif {"query", "value"} <= module_names:
                    default_targets = ["query", "value"]
                elif {"Wqkv"} <= module_names:
                    default_targets = ["Wqkv"]
                else:
                    # Fallback: target all linear layers
                    default_targets = list(module_names)[:4] if module_names else ["query", "value"]
                print(f"[generic] LoRA target modules: {default_targets}")
            lora_config = LoraConfig(
                r=lora_r,
                lora_alpha=lora_alpha,
                target_modules=default_targets,
                lora_dropout=lora_dropout,
                bias="none",
                task_type=TaskType.FEATURE_EXTRACTION,
            )
            model = get_peft_model(model, lora_config)

        return model

    def _load_google_model(self, model_name, quantification, offload_folder,
                           use_lora, lora_r, lora_alpha, lora_dropout, target_modules):
        """Load Google Gemma model."""
        print(f"Loading Google Gemma model: {model_name}")
        print(f"Tokenizer max length: {self.tokenizer.model_max_length}")
        
        
        # Report max input length for Google Gemma models
        print("=== Google Gemma Model Max Input Length ===")
        print(f"Tokenizer type: {type(self.tokenizer).__name__}")
        print(f"Tokenizer vocab size: {self.tokenizer.vocab_size}")
        print(f"Tokenizer model max length: {self.tokenizer.model_max_length}")
        print(f"Tokenizer max length source: {getattr(self.tokenizer, '_model_max_length', 'Not set')}")
        
        # Check if there's a config file that might have the correct max length
        try:
            from transformers import AutoConfig
            config = AutoConfig.from_pretrained(model_name, trust_remote_code=True)
            max_position_embeddings = getattr(config, 'max_position_embeddings', None)
            n_positions = getattr(config, 'n_positions', None)
            max_seq_length = getattr(config, 'max_seq_length', None)
            
            if max_position_embeddings:
                print(f"Max position embeddings: {max_position_embeddings}")
            if n_positions:
                print(f"N positions: {n_positions}")
            if max_seq_length:
                print(f"Max sequence length: {max_seq_length}")
                
            # Comprehensive handling of abnormally long tokenizer max length
            if self.tokenizer.model_max_length > 128000:
                print(f"⚠️  Tokenizer max length ({self.tokenizer.model_max_length}) is abnormally long")
                
                # Try different config fields in order of preference
                effective_max_length = None
                
                # 1. Try max_position_embeddings if reasonable
                if max_position_embeddings and max_position_embeddings < 128000:
                    effective_max_length = max_position_embeddings
                    print(f"   Using max_position_embeddings ({max_position_embeddings}) as effective max length")
                
                # 2. Try n_positions if reasonable
                elif n_positions and n_positions < 128000:
                    effective_max_length = n_positions
                    print(f"   Using n_positions ({n_positions}) as effective max length")
                
                # 3. Try max_seq_length if reasonable
                elif max_seq_length and max_seq_length < 128000:
                    effective_max_length = max_seq_length
                    print(f"   Using max_seq_length ({max_seq_length}) as effective max length")
                
                # 5. Fallback to a reasonable default based on model size
                if effective_max_length is None:
                    # For large Gemma models, use 128k as default
                    if "gemma" in model_name.lower() and ("4b" in model_name.lower() or "12b" in model_name.lower() or "27b" in model_name.lower()):
                        effective_max_length = 128000  # Large context for big Gemma models
                    else:
                        effective_max_length = 8192  # Default for smaller models
                    print(f"   No reasonable config found, using fallback max length: {effective_max_length}")
                
                if effective_max_length:
                    self.tokenizer.model_max_length = effective_max_length
                
        except Exception as e:
            print(f"Could not load model config: {e}")
            # Fallback for when config loading fails
            if self.tokenizer.model_max_length > 128000:
                print(f"⚠️  Tokenizer max length ({self.tokenizer.model_max_length}) is abnormally long")
                # Use same logic as main fallback
                if "gemma" in model_name.lower() and ("4b" in model_name.lower() or "12b" in model_name.lower() or "27b" in model_name.lower()):
                    fallback_length = 128000  # Large context for big Gemma models
                else:
                    fallback_length = 8192  # Default for smaller models
                print(f"   Using fallback max length: {fallback_length}")
                self.tokenizer.model_max_length = fallback_length
        
        
        print(f"Effective max input length: {self.tokenizer.model_max_length}")
        
        # Determine device map based on available GPUs
        if torch.cuda.device_count() > 1 and hasattr(self, 'use_model_parallelism') and self.use_model_parallelism:
            # Use auto device map for multi-GPU
            device_map = "auto"
        else:
            # Use specific device for single GPU
            device_map = self.device if hasattr(self, 'device') else "cuda:0"
        
        # For embedding models, disable quantization due to compatibility issues
        if "embedding" in model_name.lower() and quantification != "None":
            print("Warning: Quantization is not compatible with embedding models. Loading without quantization.")
            quantification = "None"
        
        if quantification == "4-bit":
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=False,     # Match Llama: Default False
                bnb_4bit_quant_type="fp4",          # Match Llama: Default fp4
                bnb_4bit_compute_dtype=torch.float16  # Match Llama: Default float32
            )
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                quantization_config=bnb_config,
                device_map=device_map,
                torch_dtype=torch.bfloat16,
                attn_implementation="flash_attention_2",
                trust_remote_code=True,
                offload_folder=offload_folder
            )
        elif quantification == "8-bit":
            bnb_config = BitsAndBytesConfig(
                load_in_8bit=True,
                llm_int8_threshold=6.0,
                llm_int8_has_fp16_weight=False,
                llm_int8_skip_modules=None
            )
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                quantization_config=bnb_config,
                device_map=device_map,
                torch_dtype=torch.bfloat16,
                attn_implementation="flash_attention_2",
                trust_remote_code=True,
                offload_folder=offload_folder
            )
        else:  # quantification == "None"
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map=device_map,
                torch_dtype=torch.bfloat16,
                attn_implementation="flash_attention_2",
                trust_remote_code=True,
                offload_folder=offload_folder
            )
        
        # Always apply LoRA (even in inference mode) so that state_dict keys match
        # when loading finetuned weights saved from a PeftModel
        if quantification != "None":
            model = prepare_model_for_kbit_training(model)

        # Use Gemma-specific target modules
        gemma_target_modules = target_modules or ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]

        lora_config = LoraConfig(
            r=lora_r,
            lora_alpha=lora_alpha,
            target_modules=gemma_target_modules,
            lora_dropout=lora_dropout,
            bias="none",
            task_type=TaskType.CAUSAL_LM,  # Use CAUSAL_LM for Gemma models
        )
        return get_peft_model(model, lora_config)
    
    def last_token_pool(self, last_hidden_states: torch.Tensor, 
                        attention_mask: torch.Tensor) -> torch.Tensor:
        """Last token pooling for Qwen3-Embedding models"""
        left_padding = (attention_mask[:, -1].sum() == attention_mask.shape[0])
        if left_padding:
            return last_hidden_states[:, -1]
        else:
            sequence_lengths = attention_mask.sum(dim=1) - 1
            batch_size = last_hidden_states.shape[0]
            return last_hidden_states[torch.arange(batch_size, device=last_hidden_states.device), sequence_lengths]
    
    def get_cls_token(self, last_hidden_states: torch.Tensor) -> torch.Tensor:
        """For non-autoregressive models such as bert, get the cls token"""
        return last_hidden_states[:, 0]

    def _process_with_sliding_window_batch(self, texts: list[str], max_length: int) -> torch.Tensor:
        """Process texts with sliding window approach"""
        all_windows = []
        window_counts = []  # 记录每个文本产生了多少个窗口
        
        for text in texts:
            tokens = self.tokenizer.encode(text, add_special_tokens=True)
            
            if len(tokens) <= max_length:
                # 短文本直接加入
                all_windows.append(tokens)
                window_counts.append(1)
            else:
                # 长文本创建窗口
                stride = int(max_length * self.window_stride_ratio)
                text_windows = []
                start = 0
                
                while start < len(tokens):
                    end = min(start + max_length, len(tokens))
                    window_tokens = tokens[start:end]
                    
                    # 直接使用token ids而不是decode再encode
                    text_windows.append(window_tokens)
                    
                    if end == len(tokens):
                        break
                    start += stride
                
                all_windows.extend(text_windows)
                window_counts.append(len(text_windows))
        
        # Process windows in sub-batches to avoid OOM on long sequences
        if all_windows:
            window_batch_size = max(1, int(os.environ.get("WINDOW_BATCH_SIZE", "1")))
            emb_parts = []
            for i in range(0, len(all_windows), window_batch_size):
                chunk = all_windows[i : i + window_batch_size]
                emb_parts.append(self._process_batch_optimized(chunk, max_length))
                if window_batch_size == 1:
                    torch.cuda.empty_cache()
            embeddings = torch.cat(emb_parts, dim=0)
            
            # 按原始文本分组并平均
            result_embeddings = []
            start_idx = 0
            
            for count in window_counts:
                end_idx = start_idx + count
                if count == 1:
                    result_embeddings.append(embeddings[start_idx])
                else:
                    # 平均多个窗口的embedding
                    window_embs = embeddings[start_idx:end_idx]
                    avg_emb = window_embs.mean(dim=0)
                    result_embeddings.append(avg_emb)
                start_idx = end_idx
            
            return torch.stack(result_embeddings, dim=0)
        
        return torch.empty(0, self.hidden_dim, device=self.model.device)

    def _process_batch_optimized(self, windows: list, max_length: int, stats_vecs_batch=None, return_hidden_states=False) -> torch.Tensor:
        """批量处理函数，直接处理token ids或文本"""
        # Handle DDP models by accessing the underlying model
        model_to_check = self.model.module if hasattr(self.model, 'module') else self.model
        
        is_qwen = "qwen" in model_to_check.config.model_type.lower() if hasattr(model_to_check.config, 'model_type') else False
        is_nomic = "nomic_bert" == getattr(getattr(model_to_check, 'config', None), 'model_type', '').lower()
        is_bert = ("bert" in model_to_check.config.model_type.lower() and not is_nomic) if hasattr(model_to_check.config, 'model_type') else False
        is_gpt_oss = "gpt-oss-20b" in str(model_to_check.config).lower()
        is_google = "gemma" in model_to_check.config.model_type.lower() if hasattr(model_to_check.config, 'model_type') else False
        
        # Get device from the underlying model
        if hasattr(self.model, 'module'):
            model_device = self.model.module.device
        elif hasattr(self.model, 'device'):
            model_device = self.model.device
        else:
            # For models without direct device attribute, get from first parameter
            model_device = next(self.model.parameters()).device
        
        # 处理输入：可能是token ids列表或文本列表
        if isinstance(windows[0], list):  # token ids
            # 直接构建张量，避免重复tokenization
            max_len = max(len(w) for w in windows)
            padded_windows = []
            attention_masks = []
            
            for window_tokens in windows:
                padding_length = max_len - len(window_tokens)
                padded_tokens = window_tokens + [self.tokenizer.pad_token_id] * padding_length
                mask = [1] * len(window_tokens) + [0] * padding_length
                padded_windows.append(padded_tokens)
                attention_masks.append(mask)
            
            inputs = {
                'input_ids': torch.tensor(padded_windows, device=model_device),
                'attention_mask': torch.tensor(attention_masks, device=model_device)
            }
        else:  # 文本列表
            # 批量tokenize with proper length handling
            # First check if any text is too long and truncate if needed
            processed_windows = []
            for text in windows:
                # Pre-tokenize to check length
                tokens = self.tokenizer.encode(text, add_special_tokens=True)
                if len(tokens) > max_length:
                    # Truncate text to avoid overflow
                    truncated_tokens = tokens[:max_length]
                    truncated_text = self.tokenizer.decode(truncated_tokens, skip_special_tokens=True)
                    processed_windows.append(truncated_text)
                else:
                    processed_windows.append(text)
            
            inputs = self.tokenizer(
                processed_windows,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=max_length,
            )
            # Ensure inputs are on the same device as the model
            if hasattr(self.model, 'module'):
                target_device = self.model.module.device
            elif hasattr(self.model, 'device'):
                target_device = self.model.device
            else:
                # For models without direct device attribute, get from first parameter
                target_device = next(self.model.parameters()).device
            inputs = {k: v.to(target_device) for k, v in inputs.items()}
        
        # If stats token injection is enabled, replace [STAT] token embeddings with projected stats vectors
        if stats_vecs_batch is not None:
            try:
                inputs = self._inject_stats_token_embeddings(inputs, stats_vecs_batch)
            except Exception as e:
                print(f"[stats_token_inject] WARNING: injection failed: {e}")

        # 批量前向传播
        if is_gpt_oss:
            outputs = self.model(**inputs, output_hidden_states=True)
            hs = outputs.hidden_states[-1]
        elif is_nomic:
            # NomicBertModel.forward() does not accept output_hidden_states/output_attentions
            outputs = self.model(**inputs)
            hs = outputs.last_hidden_state
        elif is_qwen:
            outputs = self.model(**inputs)
        elif is_google:
            with torch.amp.autocast('cuda', enabled=True, dtype=torch.float16):
                outputs = self.model(**inputs)
                hs = outputs.last_hidden_state
        else:
            # DeBERTa-v3 overflows with float16/bfloat16; disable autocast
            use_amp = "deberta" not in self.model_name.lower()
            with torch.amp.autocast('cuda', enabled=use_amp):
                outputs = self.model(**inputs)
                if hasattr(outputs, 'last_hidden_state'):
                    hs = outputs.last_hidden_state
                else:
                    # Fallback for models without last_hidden_state
                    outputs = self.model(**inputs, output_hidden_states=True)
                    hs = outputs.hidden_states[-1]
        
        # 批量池化
        if is_qwen:
            embs = self.last_token_pool(outputs.last_hidden_state, inputs['attention_mask'])
            embs = torch.nn.functional.normalize(embs, p=2, dim=1)
            if return_hidden_states:
                return embs, outputs.last_hidden_state, inputs['attention_mask']
            return embs
        elif is_bert or is_nomic:
            embs = []
            for i in range(hs.shape[0]):
                emb = self.get_cls_token(hs[i:i+1])
                emb = torch.nn.functional.normalize(emb, p=2, dim=1)
                embs.append(emb.squeeze(0))
            pooled = torch.stack(embs, dim=0)
            if return_hidden_states:
                return pooled, hs, inputs['attention_mask']
            return pooled
        elif is_google:
            # For Google Gemma models, use mean pooling similar to other transformer models
            mask = inputs["attention_mask"].unsqueeze(-1)
            hs_masked = hs * mask
            sum_hs = hs_masked.sum(dim=1)
            lens = mask.sum(dim=1).clamp(min=1)
            embs = sum_hs / lens
            if return_hidden_states:
                return embs, hs, inputs['attention_mask']
            return embs
        else:
            # 批量mean pooling
            mask = inputs["attention_mask"].unsqueeze(-1)
            hs_masked = hs * mask
            sum_hs = hs_masked.sum(dim=1)
            lens = mask.sum(dim=1).clamp(min=1)
            embs = sum_hs / lens
            if return_hidden_states:
                return embs, hs, inputs['attention_mask']
            return embs

    def _ensure_stats_token(self, stats_token_str: str = "[STAT]"):
        # Add [STAT] to tokenizer/model vocab if needed; create projection layer.
        if getattr(self, "_stats_token_ready", False):
            return
        if stats_token_str not in self.tokenizer.get_vocab():
            self.tokenizer.add_special_tokens({"additional_special_tokens": [stats_token_str]})
            try:
                self.model.resize_token_embeddings(len(self.tokenizer))
            except Exception:
                try:
                    self.model.base_model.resize_token_embeddings(len(self.tokenizer))
                except Exception:
                    pass
        self.stats_token_str = stats_token_str
        self.stats_token_id = self.tokenizer.convert_tokens_to_ids(stats_token_str)
        stats_dim = int(getattr(self, "stats_token_dim", 5))
        self.stats_proj = nn.Linear(stats_dim, self.hidden_dim, bias=False)
        self.stats_ln = nn.LayerNorm(self.hidden_dim)
        # keep projection on same device as model embeddings
        try:
            self.stats_proj = self.stats_proj.to(self.model.get_input_embeddings().weight.device)
            self.stats_ln = self.stats_ln.to(self.model.get_input_embeddings().weight.device)
        except Exception:
            pass
        self._stats_token_ready = True

    def _inject_stats_token_embeddings(self, inputs: dict, stats_vecs_batch):
        # Replace embeddings at [STAT] token positions with projected stats vectors.
        self._ensure_stats_token(getattr(self, "stats_token_str", "[STAT]"))
        input_ids = inputs.get("input_ids")
        attention_mask = inputs.get("attention_mask")
        emb_layer = self.model.get_input_embeddings()
        inputs_embeds = emb_layer(input_ids)
        # Avoid in-place writes on a leaf view with grad
        inputs_embeds = inputs_embeds.clone()
        # ensure stats_proj matches the current device (important under CUDA_VISIBLE_DEVICES)
        try:
            self.stats_proj = self.stats_proj.to(device=inputs_embeds.device, dtype=inputs_embeds.dtype)
            self.stats_ln = self.stats_ln.to(device=inputs_embeds.device, dtype=inputs_embeds.dtype)
        except Exception:
            pass

        import torch
        for b in range(input_ids.shape[0]):
            pos = (input_ids[b] == self.stats_token_id).nonzero(as_tuple=False).flatten()
            if pos.numel() == 0:
                continue
            vecs = stats_vecs_batch[b] if stats_vecs_batch is not None else []
            if vecs is None:
                vecs = []
            k = min(len(vecs), int(pos.numel()))
            if k <= 0:
                continue
            sv = torch.tensor(vecs[:k], dtype=inputs_embeds.dtype, device=inputs_embeds.device)
            pv = self.stats_proj(sv)
            pv = self.stats_ln(pv)
            inputs_embeds[b, pos[:k], :] = pv
        return {"inputs_embeds": inputs_embeds, "attention_mask": attention_mask}

    def forward(self, texts: list[str]):
        """
        Forward pass using optimized implementation from BasePredictor.
        """
        stats_vecs_batch = None
        if isinstance(texts, tuple) and len(texts) == 2:
            texts, stats_vecs_batch = texts
        self.stats_token_dim = int(getattr(self, "stats_token_dim", 5))
        self.stats_token_str = getattr(self, "stats_token_str", "[STAT]")
        # 判断模型类型和最大长度
        is_qwen = "qwen" in self.model_name.lower()
        is_gpt_oss = "gpt-oss-20b" in self.model_name.lower() or "openai/gpt-oss-20b" in self.model_name.lower()
        
        if is_gpt_oss:
            # GPT-OSS保持原有逻辑
            if len(texts) != 1:
                raise ValueError("GPT-OSS model expects a single input text.")
            messages = [{"role": "user", "content": f"Generate a database physical query plan embedding: {texts[0]}"}]
            inputs = self.tokenizer.apply_chat_template(
                messages,
                add_generation_prompt=True,
                return_tensors="pt",
                return_dict=True,
            )
            # Get device from the underlying model for DDP compatibility
            if hasattr(self.model, 'module'):
                model_device = self.model.module.device
            elif hasattr(self.model, 'device'):
                model_device = self.model.device
            else:
                # For models without direct device attribute, get from first parameter
                model_device = next(self.model.parameters()).device
            # Ensure inputs are on the same device as the model
            if hasattr(self.model, 'module'):
                target_device = self.model.module.device
            elif hasattr(self.model, 'device'):
                target_device = self.model.device
            else:
                # For models without direct device attribute, get from first parameter
                target_device = next(self.model.parameters()).device
            inputs = {k: v.to(target_device) for k, v in inputs.items()}
            generated = self.model(**inputs)
            hs = generated.last_hidden_state if hasattr(generated, 'last_hidden_state') else self.model(**inputs, output_hidden_states=True).hidden_states[-1]
            mask = inputs["attention_mask"].unsqueeze(-1)
            hs_masked = hs * mask
            sum_hs = hs_masked.sum(dim=1)
            lens = mask.sum(dim=1).clamp(min=1)
            emb = sum_hs / lens
            if torch.isnan(emb).any():
                print("Warning: NaN values found in embeddings!")
            return emb
        
        max_length = self.tokenizer.model_max_length
        
        # 如果启用滑动窗口，使用优化的批量处理
        if self.use_sliding_window:
            # 先检查是否有需要滑动窗口的长文本
            needs_window = []
            for text in texts:
                tokens = self.tokenizer.encode(text, add_special_tokens=True)
                needs_window.append(len(tokens) > max_length)
            
            if any(needs_window):
                # 使用优化的批量滑动窗口处理
                return self._process_with_sliding_window_batch(texts, max_length)
        
        # 不需要滑动窗口或禁用滑动窗口，批量处理所有文本
        return self._process_batch_optimized(texts, max_length, stats_vecs_batch=stats_vecs_batch)
    
    def forward_with_sequence(self, texts: list[str]):
        """
        Like forward(), but also returns hidden states and attention mask
        for cross-attention fusion.  Uses sliding windows when texts exceed
        model_max_length, concatenating per-window hidden states (keeping
        only the non-overlapping stride portion from each subsequent window)
        into a single sequence per text.

        Returns:
            pooled_emb:     [B, D_llm]
            hidden_states:  [B, T_total, D_llm]
            attention_mask: [B, T_total]
        """
        max_length = self.tokenizer.model_max_length

        if not self.use_sliding_window:
            return self._process_batch_optimized(texts, max_length, return_hidden_states=True)

        # Tokenize once to check lengths
        tokenized = [self.tokenizer.encode(t, add_special_tokens=True) for t in texts]

        if not any(len(t) > max_length for t in tokenized):
            return self._process_batch_optimized(texts, max_length, return_hidden_states=True)

        # Build sliding windows per text
        stride = int(max_length * self.window_stride_ratio)
        overlap = max_length - stride
        all_windows = []          # flat list of token-id lists
        # Per text: list of (window_idx_in_all_windows, keep_start, keep_end)
        text_window_info = []

        for tokens in tokenized:
            info = []
            if len(tokens) <= max_length:
                info.append((len(all_windows), 0, len(tokens)))
                all_windows.append(tokens)
            else:
                start = 0
                is_first = True
                while start < len(tokens):
                    end = min(start + max_length, len(tokens))
                    win_tokens = tokens[start:end]
                    win_len = len(win_tokens)
                    win_idx = len(all_windows)
                    all_windows.append(win_tokens)

                    if is_first:
                        # First window: keep all real tokens
                        info.append((win_idx, 0, win_len))
                        is_first = False
                    else:
                        # Later windows: skip the overlapping prefix,
                        # keep only the new stride portion.
                        # If this is a short final window (win_len <= overlap),
                        # all its tokens were already covered — skip it entirely.
                        ks = min(overlap, win_len)
                        if ks < win_len:
                            info.append((win_idx, ks, win_len))

                    if end >= len(tokens):
                        break
                    start += stride
            text_window_info.append(info)

        # Process all windows in one batch
        all_pooled, all_hs, all_masks = self._process_batch_optimized(
            all_windows, max_length, return_hidden_states=True
        )
        # all_hs: [N_windows, T_padded, D], all_masks: [N_windows, T_padded]

        # Assemble per-text hidden states from non-overlapping slices
        per_text_hs = []
        per_text_mask = []
        pooled_list = []

        for info in text_window_info:
            hs_parts = []
            mask_parts = []
            for win_idx, ks, ke in info:
                hs_parts.append(all_hs[win_idx, ks:ke, :])
                mask_parts.append(all_masks[win_idx, ks:ke])
            per_text_hs.append(torch.cat(hs_parts, dim=0))
            per_text_mask.append(torch.cat(mask_parts, dim=0))
            # Pooled embedding: average of per-window pooled embeddings
            win_indices = [wi for wi, _, _ in info]
            pooled_list.append(all_pooled[win_indices].mean(dim=0))

        # Pad to uniform length across the batch
        max_seq = max(h.size(0) for h in per_text_hs)
        D = all_hs.size(-1)
        device = all_hs.device

        batch_hs = torch.zeros(len(texts), max_seq, D, device=device, dtype=all_hs.dtype)
        batch_mask = torch.zeros(len(texts), max_seq, device=device, dtype=all_masks.dtype)

        for i, (h, m) in enumerate(zip(per_text_hs, per_text_mask)):
            batch_hs[i, :h.size(0), :] = h
            batch_mask[i, :m.size(0)] = m

        pooled_emb = torch.stack(pooled_list, dim=0)
        return pooled_emb, batch_hs, batch_mask

    def to(self, device):
        """
        Move the model to the specified device.
        """
        self.model = self.model.to(device)
        return self

    

    

class FeatureNormalizer:
    def __init__(self, eps=1e-6, debug: bool = False):
        self.vmin = None
        self.vmax = None
        self.eps = eps
        self.debug = debug

    def fit(self, features: torch.Tensor):
        """
        features: [N, D] tensor of training embeddings
        """
        # compute per‐dimension minima & maxima, ignoring non-finite values
        finite_mask = torch.isfinite(features)
        if not finite_mask.all():
            print(f"[FeatureNormalizer.fit] WARNING: found non-finite values; excluding from min/max computation")
        # For min: set non-finite entries to +inf so they don't affect min
        safe_for_min = torch.where(
            finite_mask, features, torch.tensor(float('inf'), device=features.device, dtype=features.dtype)
        )
        # For max: set non-finite entries to -inf so they don't affect max
        safe_for_max = torch.where(
            finite_mask, features, torch.tensor(float('-inf'), device=features.device, dtype=features.dtype)
        )
        vmin_vals = safe_for_min.min(dim=0, keepdim=True).values
        vmax_vals = safe_for_max.max(dim=0, keepdim=True).values
        # If an entire dimension is non-finite, fall back to [0,1] range
        all_nonfinite_dims = (~finite_mask).all(dim=0, keepdim=True)
        if all_nonfinite_dims.any():
            bad_idxs = all_nonfinite_dims.nonzero(as_tuple=False)[:, 1].tolist()
            print(f"[FeatureNormalizer.fit] WARNING: dimensions with all non-finite values: {bad_idxs}")
            vmin_vals = torch.where(all_nonfinite_dims, torch.zeros_like(vmin_vals), vmin_vals)
            vmax_vals = torch.where(all_nonfinite_dims, torch.ones_like(vmax_vals), vmax_vals)
        self.vmin = vmin_vals
        self.vmax = vmax_vals
        
        # Debug: Check for problematic normalization cases
        if self.debug:
            print(f"[FeatureNormalizer.fit] Input features shape: {features.shape}")
            print(f"[FeatureNormalizer.fit] Input has NaN: {torch.isnan(features).any()}")
            print(f"[FeatureNormalizer.fit] Input has Inf: {torch.isinf(features).any()}")
            print(f"[FeatureNormalizer.fit] vmin shape: {self.vmin.shape}")
            print(f"[FeatureNormalizer.fit] vmax shape: {self.vmax.shape}")
            print(f"[FeatureNormalizer.fit] vmin has NaN: {torch.isnan(self.vmin).any()}")
            print(f"[FeatureNormalizer.fit] vmax has NaN: {torch.isnan(self.vmax).any()}")
        
        # Check for dimensions where min == max (would cause division by near-zero)
        equal_mask = (self.vmax - self.vmin).abs() <= 1e-8
        if equal_mask.any() and self.debug:
            equal_indices = equal_mask.nonzero(as_tuple=False)[:, 1]
            print(f"[FeatureNormalizer.fit] WARNING: {len(equal_indices)} dimensions have min==max at indices: {equal_indices.tolist()}")
            print(f"[FeatureNormalizer.fit] Problematic vmin values: {self.vmin[0, equal_indices]}")
            print(f"[FeatureNormalizer.fit] Problematic vmax values: {self.vmax[0, equal_indices]}")

    def transform(self, features: torch.Tensor) -> torch.Tensor:
        """
        Apply (x - min)/(max - min + eps), clipping into [0,1].
        """
        assert self.vmin is not None, "must call fit() first"
        
        # Replace non-finite inputs with vmin for stability
        if not torch.isfinite(features).all():
            print("[FeatureNormalizer.transform] WARNING: non-finite inputs detected; replacing with vmin per-dimension")
            features = torch.where(
                torch.isfinite(features),
                features,
                self.vmin.expand_as(features)
            )
        
        # Debug: Check inputs to transform
        if self.debug:
            print(f"[FeatureNormalizer.transform] Input features shape: {features.shape}")
            print(f"[FeatureNormalizer.transform] Input has NaN: {torch.isnan(features).any()}")
            print(f"[FeatureNormalizer.transform] Input has Inf: {torch.isinf(features).any()}")
        
        # broadcast sub & div
        denominator = self.vmax - self.vmin + self.eps
        if self.debug:
            print(f"[FeatureNormalizer.transform] Denominator shape: {denominator.shape}")
            print(f"[FeatureNormalizer.transform] Denominator has NaN: {torch.isnan(denominator).any()}")
            print(f"[FeatureNormalizer.transform] Denominator has zero: {(denominator == 0).any()}")
            print(f"[FeatureNormalizer.transform] Denominator min: {denominator.min()}")
            print(f"[FeatureNormalizer.transform] Denominator max: {denominator.max()}")
        
        normed = (features - self.vmin) / denominator
        if self.debug:
            print(f"[FeatureNormalizer.transform] After division - has NaN: {torch.isnan(normed).any()}")
            print(f"[FeatureNormalizer.transform] After division - has Inf: {torch.isinf(normed).any()}")
        
        result = normed.clamp(0.0, 1.0)
        if self.debug:
            print(f"[FeatureNormalizer.transform] After clamp - has NaN: {torch.isnan(result).any()}")
            print(f"[FeatureNormalizer.transform] After clamp - has Inf: {torch.isinf(result).any()}")
        
        return result

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


def sanitize_nonfinite_features(features: torch.Tensor) -> torch.Tensor:
    """
    Replace non-finite values (NaN, +Inf, -Inf) per-dimension with
    the mean of finite values along that dimension. If an entire
    dimension is non-finite, fall back to zeros for that dimension.
    """
    finite_mask = torch.isfinite(features)
    if finite_mask.all():
        return features
    finite_only = torch.where(
        finite_mask,
        features,
        torch.tensor(0.0, device=features.device, dtype=features.dtype)
    )
    counts = finite_mask.sum(dim=0, keepdim=True)
    # Avoid division by zero: set zero counts to 1 temporarily
    safe_counts = counts.clone().clamp(min=1)
    sums = finite_only.sum(dim=0, keepdim=True)
    means = sums / safe_counts
    # For columns with zero finite entries, use zeros as fallback
    means = torch.where((counts == 0), torch.zeros_like(means), means)
    return torch.where(finite_mask, features, means.expand_as(features))

def debug_embeddings_info(embeddings: torch.Tensor, prefix: str = ""):
    """
    Print debug information about embeddings only if they contain non-finite values.
    """
    has_nan = torch.isnan(embeddings).any()
    has_inf = torch.isinf(embeddings).any()
    
    if has_nan or has_inf:
        print(f"[DEBUG] {prefix}embeddings shape: {embeddings.shape}")
        print(f"[DEBUG] {prefix}embeddings min: {embeddings.min()}")
        print(f"[DEBUG] {prefix}embeddings max: {embeddings.max()}")
        print(f"[DEBUG] {prefix}embeddings has NaN: {has_nan}")
        print(f"[DEBUG] {prefix}embeddings has Inf: {has_inf}")

def debug_normalizer_info(feat_norm: 'FeatureNormalizer', prefix: str = ""):
    """
    Print debug information about FeatureNormalizer only if there are issues.
    """
    has_nan_vmin = torch.isnan(feat_norm.vmin).any()
    has_nan_vmax = torch.isnan(feat_norm.vmax).any()
    vmin_equals_vmax = torch.allclose(feat_norm.vmin, feat_norm.vmax)
    
    if has_nan_vmin or has_nan_vmax or vmin_equals_vmax:
        print(f"[DEBUG] {prefix}feat_norm.vmin: {feat_norm.vmin}")
        print(f"[DEBUG] {prefix}feat_norm.vmax: {feat_norm.vmax}")
        print(f"[DEBUG] {prefix}feat_norm.eps: {feat_norm.eps}")
        print(f"[DEBUG] {prefix}vmin has NaN: {has_nan_vmin}")
        print(f"[DEBUG] {prefix}vmax has NaN: {has_nan_vmax}")
        print(f"[DEBUG] {prefix}vmin == vmax: {vmin_equals_vmax}")

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

def _find_actual_total_time(root_node, db='postgres'):
    if db == 'duckdb':
        # DuckDB: latency in seconds at root level
        if "latency" not in root_node:
            raise KeyError("'latency' not found in root (DuckDB)")
        return float(root_node["latency"])
    # Postgres: Actual Total Time in milliseconds
    if "Actual Total Time" not in root_node:
        raise KeyError("'Actual Total Time' not found in root")
    return float(root_node["Actual Total Time"])


def _find_actual_rows(root_node, db='postgres'):
    if db == 'duckdb':
        # DuckDB: rows_returned at root level
        if "rows_returned" not in root_node:
            raise KeyError("'rows_returned' not found in root (DuckDB)")
        return float(root_node["rows_returned"])
    # Postgres: Actual Rows
    if "Actual Rows" not in root_node:
        raise KeyError("'Actual Rows' not found in root")
    return float(root_node["Actual Rows"])


def _truncate_text_to_max_tokens(tokenizer, text, max_tokens):
    """
    Truncate text to a maximum number of tokens by decoding tokens back to text.
    
    Args:
        tokenizer: The tokenizer to use
        text: The text to truncate
        max_tokens: Maximum number of tokens
        
    Returns:
        Truncated text
    """
    # Tokenize the text
    tokens = tokenizer.encode(text, add_special_tokens=False)
    
    # If already within limit, return as is
    if len(tokens) <= max_tokens:
        return text
    
    # Truncate tokens
    truncated_tokens = tokens[:max_tokens]
    
    # Decode back to text
    truncated_text = tokenizer.decode(truncated_tokens, skip_special_tokens=True)
    
    return truncated_text


def _should_truncate_for_llama70b_tpcds(predictor, argsP):
    """
    Check if truncation should be applied: llama-70b model + tpcds workload.
    
    Args:
        predictor: The QueryPlanPredictor model
        argsP: Arguments object
        
    Returns:
        True if truncation should be applied, False otherwise
    """
    # Check if model is llama-70b (case insensitive)
    model_name_lower = predictor.model_name.lower() if hasattr(predictor, 'model_name') else ""
    is_llama70b = "llama" in model_name_lower and ("70b" in model_name_lower or "70-b" in model_name_lower)
    
    # Check if test workload is tpcds
    workload_test = getattr(argsP, 'workload_test', None) or getattr(argsP, 'workload', None)
    is_tpcds = workload_test == "tpcds" if workload_test else False
    
    return is_llama70b and is_tpcds


def _clean_node(obj, fields_to_remove=None, field_categories=None):
    """
    Recursively clean a query plan node by removing runtime fields and optionally
    removing fields from specified categories.

    Note: We extract "Actual Total Time" and "Actual Rows" BEFORE calling this function
    for use as training labels. Runtime fields (from the 'runtime' category) are ALWAYS
    removed automatically. The fields_to_remove parameter controls removal of the other
    5 categories for ablation studies.

    Args:
        obj: The object to clean (dict, list, or primitive)
        fields_to_remove: Optional set of field names to remove (for ablation studies)
                         Should only contain fields from non-runtime categories
        field_categories: Optional dict of field categories (defaults to postgres FIELD_CATEGORIES)

    Returns:
        Cleaned object
    """
    if fields_to_remove is None:
        fields_to_remove = set()
    if field_categories is None:
        field_categories = FIELD_CATEGORIES

    # Always remove runtime category fields
    runtime_fields = field_categories['runtime']
    all_fields_to_remove = fields_to_remove | runtime_fields
    
    if isinstance(obj, dict):
        cleaned = {}
        for k, v in obj.items():
            # Remove fields based on category selection (including runtime)
            if k in all_fields_to_remove:
                continue
            # Recursively clean the value
            cleaned[k] = _clean_node(v, fields_to_remove, field_categories)
        return cleaned
    elif isinstance(obj, list):
        return [_clean_node(item, fields_to_remove, field_categories) for item in obj]
    else:
        return obj


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

def bucketize(value, initial_range=500, num_linear_buckets=50, num_log_buckets=50, max_value=None):
    """
    Use linear bucketization in [0, initial_range] to preserve precision for small values,
    and logarithmic bucketization in [initial_range, max] to handle large values.
    Args:
        value: The value to bucketize
        initial_range: The maximum value range for linear bucketization (default 500)
        num_linear_buckets: Number of linear buckets (default 50)
        num_log_buckets: Number of logarithmic buckets (default 50)
        max_value: Maximum value in the dataset, used to determine the upper bound for logarithmic bucketization (optional)
    Returns:
        int: The bucket index
    """
    import math
    # Handle special cases
    if value < 0:
        return 0
    # Linear bucketization range [0, initial_range]
    if value <= initial_range:
        # Linear bucketization: divide [0, initial_range] evenly into num_linear_buckets buckets
        linear_bucket_width = initial_range / num_linear_buckets
        bucket_idx = int(value / linear_bucket_width)
        # Prevent boundary case (value == initial_range)
        return min(bucket_idx, num_linear_buckets - 1)
    # Logarithmic bucketization range (initial_range, max_value]
    else:
        # If max_value is not provided, use a reasonable default
        if max_value is None:
            max_value = value * 10  # Use 10x the current value as the upper bound
        # Ensure max_value is greater than initial_range
        max_value = max(max_value, initial_range * 10)
        # Mathematical basis of logarithmic bucketization:
        # Use exponentially growing bucket widths to handle heavy-tailed distributions
        # Bucket boundaries follow: boundary_i = initial_range * base^i
        # where base is the growth factor
        # Compute log-space range
        log_min = math.log(initial_range)
        log_max = math.log(max_value)
        # Map value to log-space
        log_value = math.log(value)
        # Linearly map [log_min, log_max] to bucket index [0, num_log_buckets]
        normalized_log = (log_value - log_min) / (log_max - log_min)
        log_bucket_idx = int(normalized_log * num_log_buckets)
        # Prevent boundary cases
        log_bucket_idx = min(log_bucket_idx, num_log_buckets - 1)
        # Return overall bucket index (linear bucket count + logarithmic bucket index)
        return num_linear_buckets + log_bucket_idx

def bucketize_plans_unified(jsons, initial_range=500, num_linear_buckets=50, num_log_buckets=50):
    """
    Batch process query plan JSONs using unified bucketize parameters for all values.
    Args:
        jsons: Query plan JSON list or a single JSON
        initial_range: Maximum value range for linear bucketization
        num_linear_buckets: Number of linear buckets
        num_log_buckets: Number of logarithmic buckets
    Returns:
        Processed JSON (list or single), where values are replaced with bucket indices
    """
    import copy
    # If input is a single JSON, convert to list
    single_input = not isinstance(jsons, list)
    if single_input:
        jsons = [jsons]
    # Step 1: Collect global maximum value across all numbers
    global_max_value = 0
    def collect_all_values(obj):
        """Recursively collect the global maximum value"""
        nonlocal global_max_value
        if isinstance(obj, dict):
            for value in obj.values():
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    global_max_value = max(global_max_value, value)
                elif isinstance(value, (dict, list)):
                    collect_all_values(value)
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, (int, float)) and not isinstance(item, bool):
                    global_max_value = max(global_max_value, item)
                elif isinstance(item, (dict, list)):
                    collect_all_values(item)
    # Collect maximum value from all JSONs
    for json_data in jsons:
        collect_all_values(json_data)
    # Step 2: Apply bucketize (using unified max value)
    def apply_bucketize(obj):
        """Recursively apply bucketize"""
        if isinstance(obj, dict):
            result = {}
            for key, value in obj.items():
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    # Use global maximum value
                    result[key] = bucketize(value, initial_range, num_linear_buckets,
                                          num_log_buckets, global_max_value)
                elif isinstance(value, (dict, list)):
                    result[key] = apply_bucketize(value)
                else:
                    result[key] = value
            return result
        elif isinstance(obj, list):
            result = []
            for item in obj:
                if isinstance(item, (dict, list)):
                    result.append(apply_bucketize(item))
                elif isinstance(item, (int, float)) and not isinstance(item, bool):
                    # Use global maximum value
                    result.append(bucketize(item, initial_range, num_linear_buckets,
                                          num_log_buckets, global_max_value))
                else:
                    result.append(item)
            return result
        else:
            return obj
    # Process all JSONs
    results = []
    for json_data in jsons:
        # Deep copy to avoid modifying original
        processed = apply_bucketize(copy.deepcopy(json_data))
        results.append(processed)
    # If input is a single JSON, return a single result
    if single_input:
        return results[0]
    return results

def bucketize_plans(jsons, initial_range=500, num_linear_buckets=50, num_log_buckets=50):
    """
    Batch process query plan JSONs, ensuring values with the same key use the same bucketize parameters.
    Args:
        jsons: Query plan JSON list or a single JSON
        initial_range: Maximum value range for linear bucketization
        num_linear_buckets: Number of linear buckets
        num_log_buckets: Number of logarithmic buckets
    Returns:
        Processed JSON (list or single), where values are replaced with bucket indices
    """
    import copy
    # If input is a single JSON, convert to list
    single_input = not isinstance(jsons, list)
    if single_input:
        jsons = [jsons]
    # Step 1: Collect maximum value for each numeric field
    # Used to determine bucketize upper bound per field
    field_max_values = {}
    def collect_max_values(obj, path=""):
        """Recursively collect maximum value per numeric field"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    if current_path not in field_max_values:
                        field_max_values[current_path] = value
                    else:
                        field_max_values[current_path] = max(field_max_values[current_path], value)
                elif isinstance(value, (dict, list)):
                    collect_max_values(value, current_path)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                collect_max_values(item, f"{path}[{i}]")
    # Collect max values from all JSONs
    for json_data in jsons:
        collect_max_values(json_data)
    # Step 2: Apply bucketize
    def apply_bucketize(obj, path=""):
        """Recursively apply bucketize"""
        if isinstance(obj, dict):
            result = {}
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    # Get max value for this field
                    max_val = field_max_values.get(current_path, None)
                    # Apply bucketize
                    result[key] = bucketize(value, initial_range, num_linear_buckets,
                                          num_log_buckets, max_val)
                elif isinstance(value, (dict, list)):
                    result[key] = apply_bucketize(value, current_path)
                else:
                    result[key] = value
            return result
        elif isinstance(obj, list):
            result = []
            for i, item in enumerate(obj):
                if isinstance(item, (dict, list)):
                    result.append(apply_bucketize(item, f"{path}[{i}]"))
                elif isinstance(item, (int, float)) and not isinstance(item, bool):
                    # Apply bucketize for numeric values in list
                    # Use parent path max value
                    max_val = field_max_values.get(path, None)
                    result.append(bucketize(item, initial_range, num_linear_buckets,
                                          num_log_buckets, max_val))
                else:
                    result.append(item)
            return result
        else:
            return obj
    # Process all JSONs
    results = []
    for json_data in jsons:
        # Deep copy to avoid modifying original
        processed = apply_bucketize(copy.deepcopy(json_data))
        results.append(processed)
    # If input is a single JSON, return a single result
    if single_input:
        return results[0]
    return results

def _remove_act_fields(obj, fields_to_remove=None):
    """
    Recursively remove 'act_' prefixed fields, plan_runtime, and runtime category fields
    from query plans, and optionally remove fields from specified categories.
    
    Note: Runtime fields are ALWAYS removed automatically. The fields_to_remove parameter
    controls removal of the other 5 categories for ablation studies.
    
    Args:
        obj: The object to clean (dict, list, or primitive)
        fields_to_remove: Optional set of field names to remove (for ablation studies)
                         Should only contain fields from non-runtime categories
    
    Returns:
        Cleaned object
    """
    if fields_to_remove is None:
        fields_to_remove = set()
    
    # Always remove runtime category fields
    runtime_fields = FIELD_CATEGORIES['runtime']
    all_fields_to_remove = fields_to_remove | runtime_fields
    
    if isinstance(obj, dict):
        return {
            k: _remove_act_fields(v, fields_to_remove)
            for k, v in obj.items()
            if not k.startswith("act_") and k != "plan_runtime" and k not in all_fields_to_remove
        }
    elif isinstance(obj, list):
        return [_remove_act_fields(item, fields_to_remove) for item in obj]
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

def _collect_column_ids_and_replace(node, stats, replace_type="name"):
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
        replace_type (str): Type of replacement to perform.
            - "all": Replace with the entire stats[col_id] value (default, current behavior)
            - "name": Extract "tablename" and "attname" from stats[col_id], and create
              a dict with "tablename" and "columnname" (where "columnname" is the value
              from "attname")

    Returns:
        set[int]: All unique column‐IDs encountered (before replacement).
    """
    used_cols = set()

    def _get_replacement_value(col_id):
        """Helper function to get the replacement value based on replace_type."""
        if replace_type == "name":
            # Extract tablename and attname, rename attname to columnname
            col_stat = stats[col_id]
            if isinstance(col_stat, dict):
                return {
                    "tablename": col_stat.get("tablename"),
                    "columnname": col_stat.get("attname")
                }
            else:
                # Fallback to original behavior if not a dict
                return stats[col_id]
        else:  # replace_type == "all" (default)
            return stats[col_id]

    # 1) Handle "output_columns", which is a list of dicts each containing a "columns" list
    plan_params = node.get("plan_parameters", {})
    output_list = plan_params.get("output_columns", [])
    for out_entry in output_list:
        # out_entry might look like {"columns": [0, 3, 5], ...}
        cols = out_entry.get("columns", [])
        for idx, col_id in enumerate(cols):
            # Collect the original integer ID
            used_cols.add(col_id)

            # Replace it in‐place based on replace_type
            # (Assumes stats[col_id] exists; if not, you might check bounds first)
            out_entry["columns"][idx] = _get_replacement_value(col_id)

    # 2) Handle "filter_columns", which might be a dict {"column": 7, ...}
    filter_col = plan_params.get("filter_columns", {})
    if isinstance(filter_col, dict) and "column" in filter_col:
        col_id = filter_col["column"]
        if isinstance(col_id, int):
            used_cols.add(col_id)

            # Replace with value based on replace_type
            filter_col["column"] = _get_replacement_value(col_id)

    # 3) Recurse into children
    for child in node.get("children", []):
        used_cols.update(_collect_column_ids_and_replace(child, stats, replace_type))

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
    # Limit total queries if --max_queries is set (speeds up model selection)
    max_q = getattr(argsP, 'max_queries', -1)
    if max_q > 0 and len(df) > max_q:
        print(f"  Limiting to {max_q} queries (out of {len(df)})")
        df = df.head(max_q)
    cleaned_texts = []
    costs = []
    cards = []
    lengths = []
    templates = []
    stats_vecs_list = []  # per-plan list of per-[STAT] vectors (only when argsP.stats_token_inject)

    # Select field categories based on database type
    db = getattr(argsP, 'db', 'postgres')
    field_cats = _get_field_categories(db)
    _get_fields_fn = _get_fields_to_remove_fn(db)

    # Parse removed_fields for ablation studies
    fields_to_remove = set()
    if hasattr(argsP, 'removed_fields') and argsP.removed_fields:
        removed_categories = [cat.strip() for cat in argsP.removed_fields.split(',')]
        fields_to_remove = _get_fields_fn(removed_categories)
        if fields_to_remove:
            print(f"  Removing {len(fields_to_remove)} fields from categories: {removed_categories}")

    # Check if template column exists (only for tpch and tpcds)
    has_template = 'template' in df.columns

    # Stats-token injection support
    stats_mem = None
    token_str = getattr(argsP, "stats_token_str", "[STAT]")
    inject_stat_tokens_into_cleaned_plan = None
    if getattr(argsP, "stats_token_inject", False):
        from stats_features import load_stats_memory_for_args, inject_stat_tokens_into_cleaned_plan as _inject
        stats_mem = load_stats_memory_for_args(argsP)
        inject_stat_tokens_into_cleaned_plan = _inject

    raw_jsons = df["json"]
    plan_jsons = [json.loads(raw) for raw in raw_jsons]

    # Cache original roots for costs/cards before any bucketization
    original_roots = [
        _extract_root(p) if isinstance(p, dict) else p
        for p in plan_jsons
    ]

    if argsP.bucketize_input == "separate":
        plan_jsons = bucketize_plans(plan_jsons)
    elif argsP.bucketize_input == "unified":
        plan_jsons = bucketize_plans_unified(plan_jsons)
    # If bucketize_input is None, no bucketizing is applied

    # Set up token logging file if truncation will be needed
    token_log_file = None
    if _should_truncate_for_llama70b_tpcds(predictor, argsP):
        token_log_path = dat_path.replace(".csv", "_token_counts_before_truncation.txt")
        token_log_file = open(token_log_path, 'w')
        token_log_file.write(f"Token counts before truncation (llama-70b + tpcds, max=8000 tokens)\n")
        token_log_file.write(f"Index\tToken_Count\n")

    for idx, plan_json in enumerate(plan_jsons):
        if "failed" in plan_json:
            continue
        print("*", end='', flush=True)
        root = _extract_root(plan_json)
        # Use pre-bucketized root for costs/cards
        orig_root = original_roots[idx]
        costs.append(_find_actual_total_time(orig_root, db))
        cards.append(_find_actual_rows(orig_root, db))
        cleaned_root = _clean_node(root, fields_to_remove, field_cats)
        if getattr(argsP, "stats_token_inject", False) and stats_mem is not None:
            token_mode = getattr(argsP, "stats_token_mode", "per_column")
            cleaned_root, stat_vecs = inject_stat_tokens_into_cleaned_plan(
                cleaned_root,
                ds_info,
                stats_mem,
                token_str=token_str,
                token_mode=token_mode,
            )
            stats_vecs_list.append(stat_vecs)
        else:
            stats_vecs_list.append([])
        txt = json.dumps(cleaned_root)
        
        # Log token count before truncation if needed
        if token_log_file is not None:
            token_count = len(predictor.tokenizer(txt, add_special_tokens=False)["input_ids"])
            token_log_file.write(f"{idx + 1}\t{token_count}\n")
        
        # Truncate if llama-70b + tpcds
        if _should_truncate_for_llama70b_tpcds(predictor, argsP):
            txt = _truncate_text_to_max_tokens(predictor.tokenizer, txt, 8000)
        
        cleaned_texts.append(txt)
        tok = predictor.tokenizer(txt, add_special_tokens=False)
        lengths.append(len(tok["input_ids"]))
        
        # Extract template if available
        if has_template:
            templates.append(df.iloc[idx]['template'])
        else:
            templates.append(None)

    print(f"Read {len(cleaned_texts)} plans")
    
    # Close token log file if it was opened
    if token_log_file is not None:
        token_log_path = token_log_file.name
        token_log_file.close()
        print(f"  Logged token counts to {token_log_path}")

    update_ds_info_minmax(ds_info, costs, cards)

    if all:
        return cleaned_texts, costs, cards, lengths, templates
    else:
        if argsP.card:
            if getattr(argsP, "stats_token_inject", False):
                return cleaned_texts, cards, lengths, templates, stats_vecs_list
            return cleaned_texts, cards, lengths, templates
        else:
            if getattr(argsP, "stats_token_inject", False):
                return cleaned_texts, costs, lengths, templates, stats_vecs_list
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

    # Limit total queries if --max_queries is set (speeds up model selection)
    max_q = getattr(argsP, 'max_queries', -1)
    if max_q > 0 and len(original_data["parsed_plans"]) > max_q:
        print(f"  Limiting to {max_q} queries (out of {len(original_data['parsed_plans'])})")
        original_data["parsed_plans"] = original_data["parsed_plans"][:max_q]

    costs = []
    cards = []
    templates = []

    # Parse removed_fields for ablation studies
    fields_to_remove = set()
    if hasattr(argsP, 'removed_fields') and argsP.removed_fields:
        removed_categories = [cat.strip() for cat in argsP.removed_fields.split(',')]
        fields_to_remove = get_fields_to_remove(removed_categories)
        if fields_to_remove:
            print(f"  Removing {len(fields_to_remove)} fields from categories: {removed_categories}")

    # Cache original plans for costs/cards before any bucketization
    original_plans = original_data["parsed_plans"].copy()

    # Apply bucketization if specified
    if argsP.bucketize_input == "separate":
        original_data["parsed_plans"] = bucketize_plans(original_data["parsed_plans"])
    elif argsP.bucketize_input == "unified":
        original_data["parsed_plans"] = bucketize_plans_unified(original_data["parsed_plans"])
    # If bucketize_input is None, no bucketizing is applied

    cleaned = _remove_act_fields(original_data, fields_to_remove)

    for idx, (raw, cleaned_plan) in enumerate(zip(original_data["parsed_plans"], cleaned["parsed_plans"])):
        print("*", end='', flush=True)
        # Use pre-bucketized plan for costs/cards
        orig_plan = original_plans[idx]
        plan_param = orig_plan.get("plan_parameters", {})
        costs.append(plan_param.get("act_time", None))
        cards.append(plan_param.get("act_card", None))
        
        # Extract template if available
        template = orig_plan.get("template", None)
        templates.append(template)

        # used_column_ids = _collect_column_ids_and_replace(cleaned_plan, original_data["database_stats"]["column_stats"])
        # stats = [
        #     original_data["database_stats"]["column_stats"][cid]
        #     for cid in used_column_ids
        #     if isinstance(cid, int) and cid < len(original_data["database_stats"]["column_stats"])
        # ]
        # cleaned_plan["used_column_stats"] = stats

    txts = [json.dumps(cleaned_plan, indent=2) for cleaned_plan in cleaned["parsed_plans"]]
    
    # Truncate if llama-70b + tpcds
    if _should_truncate_for_llama70b_tpcds(predictor, argsP):
        # Log token counts before truncation
        token_log_path = dat_path.replace(".json", "_token_counts_before_truncation.txt")
        with open(token_log_path, 'w') as f:
            f.write(f"Token counts before truncation (llama-70b + tpcds, max=8000 tokens)\n")
            f.write(f"Index\tToken_Count\n")
            for idx, txt in enumerate(txts):
                token_count = len(predictor.tokenizer(txt, add_special_tokens=False)["input_ids"])
                f.write(f"{idx + 1}\t{token_count}\n")
        print(f"  Logged token counts to {token_log_path}")
        
        txts = [_truncate_text_to_max_tokens(predictor.tokenizer, txt, 8000) for txt in txts]
    
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


def _load_queries_true_embeddings(dat_path: str, argsP):
    """Load queries_true embeddings and return as FloatTensor [N, D]."""
    try:
        from pathlib import Path
        qt_dir = Path(getattr(argsP, "queries_true_dir", "../queries_true")).resolve()
        if not qt_dir.exists():
            print(f"[queries_true] Directory not found: {qt_dir}")
            return None
        base = Path(dat_path).name
        if base.endswith(".csv"):
            base = base[:-4]
        if base.startswith("long_raw_postgres_"):
            base = base[len("long_raw_postgres_"):]
        elif base.startswith("long_raw_duckdb_"):
            base = base[len("long_raw_duckdb_"):]
        elif base.startswith("long_raw_mysql_"):
            base = base[len("long_raw_mysql_"):]
        elif base.startswith("long_raw_spark_"):
            base = base[len("long_raw_spark_"):]

        candidates = []
        candidates.append(f"{base}_embeddings.csv")
        if base.startswith("imdb_"):
            candidates.append(f"{base.replace('imdb_','')}_embeddings.csv")
        if base.startswith("stats_"):
            candidates.append(f"{base.replace('stats_','')}_embeddings.csv")
        if base in ("imdb_job_full", "job_full"):
            candidates.append("job_full_train_embeddings.csv")

        emb_path = None
        for name in candidates:
            p = qt_dir / name
            if p.exists():
                emb_path = p
                break
        if emb_path is None:
            print(f"[queries_true] No embedding file found for {dat_path}. Tried: {candidates}")
            return None

        df = pd.read_csv(emb_path)
        # Support changed formats: select numeric columns only (drop ids/strings)
        num_df = df.select_dtypes(include=["number"])
        if num_df.shape[1] == 0:
            raise ValueError(f"[queries_true] No numeric columns found in {emb_path}")
        if num_df.shape[1] != df.shape[1]:
            dropped = [c for c in df.columns if c not in num_df.columns]
            print(f"[queries_true] Dropping non-numeric columns: {dropped}")
        feats = torch.from_numpy(num_df.values).float()
        print(f"[queries_true] Loaded embeddings from {emb_path} with shape {feats.shape}")
        return feats
    except Exception as e:
        print(f"[queries_true] Failed to load embeddings for {dat_path}: {e}")
        return None


def get_embeddings(predictor, ds_info, dat_path, argsP, batch_size=1, normalize_feats=True, collect_test_info=False):
    # Add target workload info to filename when conditions are met
    target_suffix = ""
    if hasattr(argsP, 'workload_test') and argsP.workload_test in ["synthetic", "job-light", "tpc_h"] and argsP.llm_pretrained is not None:
        target_suffix = f"_target_{argsP.workload_test}"
    
    # Append seed in cache filename when seed > 44
    seed_suffix = ""
    if hasattr(argsP, 'seed') and isinstance(getattr(argsP, 'seed'), (int, float)) and argsP.seed > 44:
        seed_suffix = f"_seed{int(argsP.seed)}"
    
    # Append removed fields suffix when field categories are removed
    removed_fields_suffix = ""
    if hasattr(argsP, 'removed_fields') and argsP.removed_fields:
        # Convert category names to abbreviations (matching shell script logic)
        category_abbrev = {
            'operator_structure_and_config': 'ops',
            'cost': 'cost',
            'cardinality': 'card',
            'conditions_and_filters': 'cond',
            'metadata_and_config': 'meta'
        }
        categories = [cat.strip() for cat in argsP.removed_fields.split(',')]
        abbrevs = [category_abbrev.get(cat, cat) for cat in categories if cat in category_abbrev]
        if abbrevs:
            removed_fields_suffix = f"_rm-{'-'.join(abbrevs)}"
    
    # Determine cache directory based on whether _rm- is in the filename
    db = getattr(argsP, 'db', 'postgres')
    cache_dir = f"embeddings/{db}"
    if "_rm-" in removed_fields_suffix:
        cache_dir = f"embeddings_rm/{db}"
    
    stats_suffix = ""
    if getattr(argsP, "stats_token_inject", False):
        stats_mode = getattr(argsP, "stats_token_mode", "per_column")
        stats_suffix = f"_statTok-{stats_mode}"
    # Include algo in cache filename to distinguish embeddings from different finetune sources
    # (e.g. llm_price uses JointPrice-finetuned LLM weights, different from llm's weights)
    algo_suffix = f"_algo-{argsP.algo}" if argsP.algo not in ("llm", "llm_stats") else ""
    # Include max_queries in cache filename to avoid conflicts between subset and full embeddings
    maxq_suffix = ""
    max_q = getattr(argsP, 'max_queries', -1)
    if max_q > 0:
        maxq_suffix = f"_maxq-{max_q}"
    ft_epoch_suffix = ""
    ft_ep = getattr(argsP, 'ft_num_epoch', 0)
    if argsP.llm_pretrained and argsP.llm_pretrained != "None" and ft_ep > 0:
        ft_epoch_suffix = f"_ftEp{ft_ep}"
    triple_concat_suffix = "_tripleConcat" if getattr(argsP, 'triple_concat', False) else ""
    cache_file = f"embeddings_{argsP.model_name}_bucketize-{argsP.bucketize_input}_quant-{argsP.quantification}_pretrained-{argsP.llm_pretrained}_pretrainedTask-{argsP.llm_pretrained_task}{algo_suffix}{target_suffix}{seed_suffix}{removed_fields_suffix}{stats_suffix}{maxq_suffix}{ft_epoch_suffix}{triple_concat_suffix}_{dat_path}".replace("json", "csv")
    cache_file = cache_file.replace("/","-")
    cache_path = os.path.join(cache_dir, cache_file)
    
    # Record test paths only when collecting test info
    try:
        if collect_test_info and not hasattr(argsP, 'test_embedding_cache_path') and not hasattr(argsP, 'test_plan_file_path'):
            argsP.test_embedding_cache_path = cache_path
            argsP.test_plan_file_path = dat_path
    except Exception:
        pass
    
    # Track max query plan token length for this workload
    max_plan_tokens = 0
    texts = None
    
    if os.path.exists(cache_path):
        # Load cached embeddings
        df        = pd.read_csv(cache_path)
        cards     = df['cards'].tolist()
        costs     = df['costs'].tolist()
        lengths   = df['lengths'].tolist()
        templates = df['templates'].tolist() if 'templates' in df.columns else [None] * len(cards)
        features  = torch.from_numpy(df.drop(columns=['costs', 'cards', 'lengths'] + (['templates'] if 'templates' in df.columns else [])).values).float()
        print(f"Loaded embeddings from {cache_path}")
        update_ds_info_minmax(ds_info, costs, cards)
        # Always sanitize cached features after loading
        if torch.isnan(features).any() or torch.isinf(features).any():
            nan_rows = torch.isnan(features).any(dim=1).nonzero(as_tuple=False).flatten().tolist()
            inf_rows = torch.isinf(features).any(dim=1).nonzero(as_tuple=False).flatten().tolist()
            print(f"[get_embeddings] Non-finite in cached features. NaN rows (up to 20): {nan_rows[:20]} | Inf rows (up to 20): {inf_rows[:20]}")
            features = sanitize_nonfinite_features(features)
            print("[get_embeddings] Replaced non-finite values in cached features with per-dimension means.")
        
        # Convert to float32 for MLP compatibility (BFloat16 causes dtype mismatch)
        if features.dtype == torch.bfloat16:
            features = features.float()
        
    else:
        print(f"embedding file {cache_path} not found, creating a new one")
        argsP.inference_logger.info(f"Creating new embedding file for dat_path: {dat_path}")
        if dat_path.endswith("c8220.json"):
            texts, costs, cards, lengths, templates = read_json_and_clean_v2(predictor, ds_info, dat_path, argsP, all=True)
        else:
            texts, costs, cards, lengths, templates = read_json_and_clean(predictor, ds_info, dat_path, argsP, all=True)
        
        # Track max query plan token length for this workload
        # Note: Truncation for llama-70b + tpcds is already handled in read_json_and_clean() and read_json_and_clean_v2()
        for text in texts:
            token_length = len(predictor.tokenizer.encode(text, add_special_tokens=True))
            if token_length > max_plan_tokens:
                max_plan_tokens = token_length
        print(f"Max query plan token length for {dat_path}: {max_plan_tokens} tokens")
        argsP.inference_logger.info(f"Max query plan token length for {dat_path}: {max_plan_tokens} tokens")
        
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
        
        # Store original embeddings before sanitization
        original_features = features.clone()
        
        # Non-finite check: raw features before any saving
        if torch.isnan(features).any() or torch.isinf(features).any():
            nan_rows = torch.isnan(features).any(dim=1).nonzero(as_tuple=False).flatten().tolist()
            inf_rows = torch.isinf(features).any(dim=1).nonzero(as_tuple=False).flatten().tolist()
            print(f"[get_embeddings] Non-finite in raw features. NaN rows (up to 20): {nan_rows[:20]} | Inf rows (up to 20): {inf_rows[:20]}")
            features = sanitize_nonfinite_features(features)
            print("[get_embeddings] Replaced non-finite values with per-dimension means for stability.")
        
        # Convert to float32 for MLP compatibility (BFloat16 causes dtype mismatch)
        if features.dtype == torch.bfloat16:
            features = features.float()

        # save original un-sanitized embeddings to CSV for next time
        output_dir = os.path.dirname(cache_path)
        os.makedirs(output_dir, exist_ok=True)
        df = pd.DataFrame(original_features.float().numpy())
        df['costs'] = costs
        df['cards'] = cards
        df['lengths'] = lengths
        if templates and any(t is not None for t in templates):
            df['templates'] = templates
        df.to_csv(cache_path, index=False)
        print(f"Saved original embeddings to {cache_path}")
    

    features = downsample_block_mean(features, argsP)
    # NaN check: after downsampling
    if torch.isnan(features).any() or torch.isinf(features).any():
        print("[get_embeddings] Non-finite after downsample_block_mean")
        exit(0)

    if getattr(argsP, "concat_true_embeddings", False) and getattr(argsP, "llm_mode", "inference") == "inference":
        true_emb = _load_queries_true_embeddings(dat_path, argsP)
        if true_emb is not None:
            if true_emb.shape[0] != features.shape[0]:
                raise ValueError(
                    f"queries_true embeddings rows ({true_emb.shape[0]}) do not match LLM embeddings rows ({features.shape[0]}) "
                    f"for {dat_path}"
                )
            features = torch.cat([features, true_emb.to(features.device)], dim=1)
            argsP.embed_size = int(features.shape[1])
    
    if normalize_feats:
        feat_norm = FeatureNormalizer()
        features = feat_norm.fit_transform(features)

    # Return: always return 4 values
    if argsP.card:
        return features, cards, lengths, templates
    else:
        return features, costs, lengths, templates


def generate_price_embeddings(price_embedder, workload, sql_list, db_name, bin_size, device, batch_size=64):
    """
    Generate PRICE embeddings for a list of SQL queries.

    Args:
        price_embedder: PRICEEmbedder instance (already on device)
        workload: workload name (e.g. 'job', 'tpcds')
        sql_list: list of raw SQL strings
        db_name: PRICE database name
        bin_size: histogram bin size
        device: torch device
        batch_size: batch size for inference

    Returns:
        embeddings: [N, 512] tensor of PRICE embeddings
    """
    import price_data_utils as pdu

    # Generate raw features
    data_features, n_join_cols, n_fanouts, n_tables, n_filter_cols = pdu.generate_price_features(
        workload, sql_list, db_name, bin_size,
        price_m=getattr(argsP, 'price_m', False),
        price_s=getattr(argsP, 'price_s', False)
    )

    # Pad features
    padded_features, padding_masks, max_njc, max_nfo, max_ntb, max_nfc = pdu.pad_and_cache_features(
        data_features, n_join_cols, n_fanouts, n_tables, n_filter_cols,
        bin_size=bin_size,
        price_m=getattr(argsP, 'price_m', False),
    )

    # Run through PRICEEmbedder in batches with no_grad
    price_embedder.eval()
    all_embs = []
    with torch.no_grad():
        for i in range(0, len(padded_features), batch_size):
            pf_batch = torch.stack([f if isinstance(f, torch.Tensor) else torch.tensor(f, dtype=torch.float32)
                                    for f in padded_features[i:i+batch_size]]).float().to(device)
            pm_batch = torch.stack([m if isinstance(m, torch.Tensor) else torch.tensor(m)
                                    for m in padding_masks[i:i+batch_size]]).float().to(device)
            njc_batch = torch.tensor(n_join_cols[i:i+batch_size], dtype=torch.float32, device=device).unsqueeze(1)
            nfo_batch = torch.tensor(n_fanouts[i:i+batch_size], dtype=torch.float32, device=device).unsqueeze(1)
            ntb_batch = torch.tensor(n_tables[i:i+batch_size], dtype=torch.float32, device=device).unsqueeze(1)
            nfc_batch = torch.tensor(n_filter_cols[i:i+batch_size], dtype=torch.float32, device=device).unsqueeze(1)

            emb = price_embedder(pf_batch, pm_batch, njc_batch, nfo_batch, ntb_batch, nfc_batch)
            all_embs.append(emb.cpu())

    return torch.cat(all_embs, dim=0)  # [N, 512]


def _load_price_embedder(argsP, max_njc, max_nfo, max_ntb, max_nfc, device):
    """
    Build a PRICEEmbedder and load weights based on argsP.price_weights_source.

    Args:
        argsP: parsed arguments (needs price_weights_source, price_bin_size,
               price_model_path, workloads_train, card, llm_pretrained, model_name)
        max_njc, max_nfo, max_ntb, max_nfc: PRICE model dimensions
        device: torch device

    Returns:
        price_embedder: PRICEEmbedder with loaded weights, on device
    """
    import sys as _sys, os as _os
    _local_price = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "PRICE")
    _price_root = _local_price if _os.path.isdir(_os.path.join(_local_price, "setup")) else "/root/PRICE"
    if _price_root not in _sys.path:
        _sys.path.insert(0, _price_root)
    from model.encoder import RegressionModel
    from models.llm_price_model import PRICEEmbedder

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
    price_embedder = PRICEEmbedder(price_model)

    source = getattr(argsP, 'price_weights_source', 'pretrained')
    ft_bs = getattr(argsP, 'ft_batch_size', 16)
    price_m_suffix = "_priceM" if getattr(argsP, 'price_m', False) else ""
    price_s_suffix = "_priceS" if getattr(argsP, 'price_s', False) else ""
    rand_init_suffix = "_randInit" if getattr(argsP, 'price_random_init', False) else ""
    n_layers_suffix = f"_pL{argsP.price_n_layers}" if getattr(argsP, 'price_n_layers', 6) != 6 else ""
    ft_epochs = getattr(argsP, 'ft_num_epoch', 0)
    epoch_suffix = f"_e{ft_epochs}" if ft_epochs > 0 else ""
    # Helper: load checkpoint into model with partial init for size-mismatched weights.
    # For PRICE_M, filter_embeddings.weight changes from [n_embd,43] to [n_embd,61];
    # copies the overlapping columns (histogram bins) and leaves the rest randomly initialized.
    def _partial_init_load(target, ckpt_sd, label=""):
        tsd = target.state_dict()
        for k, v in ckpt_sd.items():
            if k not in tsd:
                continue
            if tsd[k].shape == v.shape:
                tsd[k] = v
            elif tsd[k].dim() == v.dim():
                slices = tuple(slice(0, min(ms, vs)) for ms, vs in zip(tsd[k].shape, v.shape))
                tsd[k][slices] = v[slices]
                print(f"  Partial init {k}: copied {[s.stop for s in slices]} of {list(tsd[k].shape)} from checkpoint {list(v.shape)}")
        target.load_state_dict(tsd)
        if label:
            print(label)

    if source == "pretrained":
        # Load original pretrained PRICE weights
        price_sd = torch.load(argsP.price_model_path, map_location=device)
        price_sd = {k.replace('module.', ''): v for k, v in price_sd.items()}
        _partial_init_load(price_embedder, price_sd, f"Loaded pretrained PRICE weights from {argsP.price_model_path}")
    elif source == "separate":
        # Load PRICE weights finetuned separately on cardinality
        price_weight_path = f"finetuned_models/{argsP.db}/{argsP.canonical_wl_prefix}_card_b{ft_bs}{price_m_suffix}{price_s_suffix}{rand_init_suffix}{n_layers_suffix}{epoch_suffix}_price_separate.pt"
        price_sd = torch.load(price_weight_path, map_location=device)
        _partial_init_load(price_embedder, price_sd, f"Loaded separately finetuned PRICE weights from {price_weight_path}")
    elif source == "joint":
        # Load PRICE weights from joint LLM+PRICE finetuning
        task_str = "card" if argsP.card else "time"
        price_weight_path = f"finetuned_models/{argsP.db}/{argsP.canonical_wl_prefix}_{task_str}_{argsP.llm_pretrained}_{argsP.model_name.replace('/','-')}_b{ft_bs}{price_m_suffix}{price_s_suffix}_llm_price{rand_init_suffix}{n_layers_suffix}{epoch_suffix}_price.pt"
        price_sd = torch.load(price_weight_path, map_location=device)
        _partial_init_load(price_embedder, price_sd, f"Loaded jointly finetuned PRICE weights from {price_weight_path}")
    elif source == "frozen_joint":
        # Load PRICE weights finetuned with frozen LLM (llm_mode=inference)
        task_str = "card" if argsP.card else "time"
        price_weight_path = f"finetuned_models/{argsP.db}/{argsP.canonical_wl_prefix}_{task_str}_inference_{argsP.model_name.replace('/','-')}_b{ft_bs}{price_m_suffix}{price_s_suffix}_llm_price{rand_init_suffix}{n_layers_suffix}{epoch_suffix}_price.pt"
        price_sd = torch.load(price_weight_path, map_location=device)
        _partial_init_load(price_embedder, price_sd, f"Loaded frozen-joint finetuned PRICE weights from {price_weight_path}")
    elif source == "joint_frozen_init":
        # Load PRICE weights from joint finetuning that started from frozen-joint init
        task_str = "card" if argsP.card else "time"
        price_weight_path = f"finetuned_models/{argsP.db}/{argsP.canonical_wl_prefix}_{task_str}_{argsP.llm_pretrained}_{argsP.model_name.replace('/','-')}_b{ft_bs}{price_m_suffix}{price_s_suffix}_llm_price_frozenInit{rand_init_suffix}{n_layers_suffix}{epoch_suffix}_price.pt"
        price_sd = torch.load(price_weight_path, map_location=device)
        _partial_init_load(price_embedder, price_sd, f"Loaded frozen-init jointly finetuned PRICE weights from {price_weight_path}")
    elif source == "gated_joint":
        # Load PRICE weights from gated joint finetuning
        task_str = "card" if argsP.card else "time"
        price_weight_path = f"finetuned_models/{argsP.db}/{argsP.canonical_wl_prefix}_{task_str}_{argsP.llm_pretrained}_{argsP.model_name.replace('/','-')}_b{ft_bs}{price_m_suffix}{price_s_suffix}_llm_price_gated{rand_init_suffix}{n_layers_suffix}{epoch_suffix}_price.pt"
        price_sd = torch.load(price_weight_path, map_location=device)
        _partial_init_load(price_embedder, price_sd, f"Loaded gated jointly finetuned PRICE weights from {price_weight_path}")
    elif source == "cross_attn_joint":
        # Load PRICE weights from cross-attention joint finetuning
        # These are CrossAttentionPRICEEmbedder weights (includes llm_proj + cross_attn_blocks)
        task_str = "card" if argsP.card else "time"
        cross_attn_suffix = "_crossAttn"
        n_cross_suffix = f"_cx{argsP.n_cross_layers}" if getattr(argsP, 'n_cross_layers', 2) != 2 else ""
        price_weight_path = f"finetuned_models/{argsP.db}/{argsP.canonical_wl_prefix}_{task_str}_{argsP.llm_pretrained}_{argsP.model_name.replace('/','-')}_b{ft_bs}{price_m_suffix}{price_s_suffix}_llm_price{cross_attn_suffix}{rand_init_suffix}{n_layers_suffix}{n_cross_suffix}{epoch_suffix}_price.pt"
        price_sd = torch.load(price_weight_path, map_location=device)
        # Build a CrossAttentionPRICEEmbedder instead of plain PRICEEmbedder
        from models.llm_price_model import CrossAttentionPRICEEmbedder
        n_cross = getattr(argsP, 'n_cross_layers', 2)
        llm_hidden_dim = getattr(argsP, 'embed_size', 256)
        price_embedder = CrossAttentionPRICEEmbedder(
            price_model, llm_hidden_dim, n_cross_layers=n_cross,
            n_embd=256, n_heads=8, dropout_rate=0.1
        )
        _partial_init_load(price_embedder, price_sd, f"Loaded cross-attn jointly finetuned PRICE weights from {price_weight_path}")
    else:
        raise ValueError(f"Unknown price_weights_source: {source}")

    price_embedder.to(device)
    return price_embedder


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
            stats_vecs_test_full = None
            if getattr(argsP, "stats_token_inject", False):
                stats_vecs_test_full = [[] for _ in cleaned_texts_test]
        else:
            tmp = read_json_and_clean(predictor, ds_info, dat_path_test, argsP)
            if getattr(argsP, "stats_token_inject", False):
                cleaned_texts_test, costs_test, lengths_test, templates_test, stats_vecs_test_full = tmp
            else:
                cleaned_texts_test, costs_test, lengths_test, templates_test = tmp
                stats_vecs_test_full = None
        if len(dat_path_train_list)==1 and dat_path_train_list[0]==dat_path_test:
            train_ids, val_ids, test_ids = train_val_test(len(cleaned_texts_test), argsP)
            cleaned_texts_train = [cleaned_texts_test[idx] for idx in train_ids]
            cleaned_texts_val   = [cleaned_texts_test[idx] for idx in val_ids  ]
            cleaned_texts_test  = [cleaned_texts_test[idx] for idx in test_ids ]
            costs_train = [costs_test[idx] for idx in train_ids]
            if getattr(argsP, "stats_token_inject", False):
                stats_vecs_train = [stats_vecs_test_full[idx] for idx in train_ids]
                stats_vecs_val   = [stats_vecs_test_full[idx] for idx in val_ids]
                stats_vecs_test  = [stats_vecs_test_full[idx] for idx in test_ids]
            else:
                stats_vecs_train = stats_vecs_val = stats_vecs_test = None
            costs_val   = [costs_test[idx] for idx in val_ids  ]
            costs_test  = [costs_test[idx] for idx in test_ids ]
            lengths_test  = [lengths_test[idx] for idx in test_ids ]
            templates_test = [templates_test[idx] for idx in test_ids ]
        else:
            cleaned_texts_train, costs_train = [], []
            stats_vecs_train_list = []
            for dat_path_train in dat_path_train_list:
                if dat_path_train.endswith("c8220.json"):
                    # for the 100k workload, we use the v2 version
                    cleaned_texts, costs, lengths, templates = read_json_and_clean_v2(predictor, ds_info, dat_path_train, argsP)
                else:
                    tmp2 = read_json_and_clean(predictor, ds_info, dat_path_train, argsP)
                    if getattr(argsP, "stats_token_inject", False):
                        cleaned_texts, costs, lengths, templates, stats_vecs_part = tmp2
                    else:
                        cleaned_texts, costs, lengths, templates = tmp2
                cleaned_texts_train.extend(cleaned_texts)
                costs_train.extend(costs)
                if getattr(argsP, "stats_token_inject", False):
                    stats_vecs_train_list.extend(stats_vecs_part)
            train_ids, val_ids= train_val(len(cleaned_texts_train), argsP)
            cleaned_texts_val   = [cleaned_texts_train[idx] for idx in val_ids  ]
            cleaned_texts_train = [cleaned_texts_train[idx] for idx in train_ids]
            if getattr(argsP, "stats_token_inject", False):
                stats_vecs_val   = [stats_vecs_train_list[idx] for idx in val_ids]
                stats_vecs_train = [stats_vecs_train_list[idx] for idx in train_ids]
                stats_vecs_test  = stats_vecs_test_full
            else:
                stats_vecs_train = stats_vecs_val = stats_vecs_test = None
            costs_val   = [costs_train[idx] for idx in val_ids  ]
            costs_train = [costs_train[idx] for idx in train_ids]

        if hasattr(argsP, 'train_ratio') and 0.0 < argsP.train_ratio < 1.0:
            cleaned_texts_train, costs_train = sample_train(cleaned_texts_train, costs_train, argsP.train_ratio, features_is_list=True)

        if getattr(argsP, "stats_token_inject", False):
            from stats_features import normalize_stats_vecs
            stats_vecs_train, stats_vecs_val, stats_vecs_test = normalize_stats_vecs(
                stats_vecs_train, stats_vecs_val, stats_vecs_test
            )

    elif argsP.algo=="llm" or argsP.algo=="llm_stats":
        embeddings_test, costs_test, lengths_test, templates_test = get_embeddings(predictor, ds_info, dat_path_test, argsP, 16, False, collect_test_info=argsP.verbose_info)
        
        if len(dat_path_train_list)==1 and dat_path_train_list[0]==dat_path_test:
            # Debug: Check embeddings before normalization
            debug_embeddings_info(embeddings_test, "embeddings_test ")
            
            feat_norm = FeatureNormalizer()
            feat_norm.fit(embeddings_test)
            
            # Debug: Check normalization parameters
            debug_normalizer_info(feat_norm, "feat_norm.")
            
            embeddings_test = feat_norm.transform(embeddings_test)
            
            # Debug: Check embeddings after normalization
            debug_embeddings_info(embeddings_test, "After transform - embeddings_test ")
            
            # NaN check: after normalization on test-only
            if torch.isnan(embeddings_test).any():
                print("[get_llm_ds_from_csv] NaNs after FeatureNormalizer on test set")
                exit(0)
            train_ids, val_ids, test_ids = train_val_test(len(embeddings_test), argsP)
            embeddings_train = embeddings_test[train_ids]
            embeddings_val   = embeddings_test[val_ids]
            embeddings_test  = embeddings_test[test_ids]
            costs_train = [costs_test[idx] for idx in train_ids]
            costs_val   = [costs_test[idx] for idx in val_ids  ]
            costs_test  = [costs_test[idx] for idx in test_ids ]
            lengths_test  = [lengths_test[idx] for idx in test_ids ]
            templates_test = [templates_test[idx] for idx in test_ids ]
            
            # Record mapping from test dataset row to original index in the file
            try:
                argsP.test_original_indices = test_ids
            except Exception:
                pass
            
            # Note: texts_test is no longer collected since we don't save test_texts when getting verbose information
        else:
            embeddings_train_list, costs_train = [], []
            for dat_path_train in dat_path_train_list:
                embeddings, costs, lengths, templates = get_embeddings(predictor, ds_info, dat_path_train, argsP, 16, False, collect_test_info=False)
                embeddings_train_list.append(embeddings)
                costs_train.extend(costs)
            embeddings_train = torch.cat(embeddings_train_list, dim=0)
            all_embeddings = torch.cat([embeddings_train, embeddings_test], dim=0)       # [N_train+N_test, D]
            
            # Debug: Check combined embeddings before normalization
            debug_embeddings_info(all_embeddings, "all_embeddings ")
            
            feat_norm = FeatureNormalizer()
            all_embeddings = feat_norm.fit_transform(all_embeddings)
            
            # Debug: Check combined embeddings after normalization
            debug_embeddings_info(all_embeddings, "After fit_transform - all_embeddings ")
            
            # NaN check: after normalization on combined train+test
            if torch.isnan(all_embeddings).any():
                print("[get_llm_ds_from_csv] NaNs after FeatureNormalizer on train+test")
                exit(0)
            Ntr = embeddings_train.size(0)
            embeddings_train = all_embeddings[:Ntr]
            embeddings_test  = all_embeddings[Ntr:]

            train_ids, val_ids= train_val(Ntr, argsP)
            embeddings_val   = embeddings_train[val_ids]
            embeddings_train = embeddings_train[train_ids]
            costs_val   = [costs_train[idx] for idx in val_ids  ]
            costs_train = [costs_train[idx] for idx in train_ids]
            
            # Note: texts_test is no longer collected since we don't save test_texts when getting verbose information

        if hasattr(argsP, 'train_ratio') and 0.0 < argsP.train_ratio < 1.0:
            embeddings_train, costs_train = sample_train(embeddings_train, costs_train, argsP.train_ratio, features_is_list=False)

    elif argsP.algo == "llm_price":
        # ---- Phase 1: Get LLM embeddings (cached, uses torch.no_grad()) ----
        embeddings_test, costs_test, lengths_test, templates_test = get_embeddings(
            predictor, ds_info, dat_path_test, argsP, 16, False, collect_test_info=argsP.verbose_info
        )

        # ---- Phase 2: Build PRICEEmbedder and generate PRICE embeddings ----
        import price_data_utils as pdu

        workload = argsP.workload_test
        db_name = pdu.get_db_name_for_workload(workload)
        bin_size = getattr(argsP, 'price_bin_size', 40)
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Get SQL for test workload
        is_cross_wl_test = dat_path_test.endswith("c8220.json")
        if is_cross_wl_test:
            test_db = pdu.get_db_name_from_json_path(dat_path_test)
            sql_list_test = pdu.get_sql_for_cross_workload_plans(dat_path_test, test_db)
            sql_list_test = [s if s is not None else "select count(*) from _dummy" for s in sql_list_test]
            db_name = test_db
        else:
            sql_file = pdu.get_sql_file_for_workload(workload, card=argsP.card)
            sql_list_test = pdu.extract_raw_sql_from_queries_true(sql_file)
        # Align SQL and embeddings count
        min_len = min(len(sql_list_test), embeddings_test.size(0))
        sql_list_test = sql_list_test[:min_len]
        embeddings_test = embeddings_test[:min_len]
        costs_test = costs_test[:min_len]
        lengths_test = lengths_test[:min_len]
        templates_test = templates_test[:min_len]

        if len(dat_path_train_list) == 1 and dat_path_train_list[0] == dat_path_test:
            # Same file — generate PRICE embeddings for all, then split
            # First generate raw features to determine dims for model construction
            data_features, n_join_cols, n_fanouts, n_tables, n_filter_cols = pdu.generate_price_features(
                workload, sql_list_test, db_name, bin_size,
                price_m=getattr(argsP, 'price_m', False),
                price_s=getattr(argsP, 'price_s', False),
                already_price_format=is_cross_wl_test,
            )
            padded_features, padding_masks, max_njc, max_nfo, max_ntb, max_nfc = pdu.pad_and_cache_features(
                data_features, n_join_cols, n_fanouts, n_tables, n_filter_cols, bin_size=bin_size,
                price_m=getattr(argsP, 'price_m', False),
            )

            # Build PRICE model and load weights based on price_weights_source
            price_embedder = _load_price_embedder(argsP, max_njc, max_nfo, max_ntb, max_nfc, device)

            # Generate PRICE embeddings in batches
            price_embedder.eval()
            price_embs = []
            with torch.no_grad():
                for i in range(0, len(padded_features), 64):
                    pf_batch = torch.stack([f if isinstance(f, torch.Tensor) else torch.tensor(f, dtype=torch.float32) for f in padded_features[i:i+64]]).float().to(device)
                    pm_batch = torch.stack([m if isinstance(m, torch.Tensor) else torch.tensor(m) for m in padding_masks[i:i+64]]).float().to(device)
                    njc_batch = torch.tensor(n_join_cols[i:i+64], dtype=torch.float32, device=device).unsqueeze(1)
                    nfo_batch = torch.tensor(n_fanouts[i:i+64], dtype=torch.float32, device=device).unsqueeze(1)
                    ntb_batch = torch.tensor(n_tables[i:i+64], dtype=torch.float32, device=device).unsqueeze(1)
                    nfc_batch = torch.tensor(n_filter_cols[i:i+64], dtype=torch.float32, device=device).unsqueeze(1)
                    emb = price_embedder(pf_batch, pm_batch, njc_batch, nfo_batch, ntb_batch, nfc_batch)
                    price_embs.append(emb.cpu())
            price_embeddings = torch.cat(price_embs, dim=0)  # [N, 512]
            price_embedder.to("cpu")
            torch.cuda.empty_cache()
            print(f"Generated PRICE embeddings: {price_embeddings.shape}")

            # Apply learned gate if gated_joint
            if getattr(argsP, 'price_weights_source', 'pretrained') == "gated_joint":
                task_str = "card" if argsP.card else "time"
                ft_bs_gate = getattr(argsP, 'ft_batch_size', 16)
                price_m_suffix = "_priceM" if getattr(argsP, 'price_m', False) else ""
                price_s_suffix = "_priceS" if getattr(argsP, 'price_s', False) else ""
                rand_init_suffix_gate = "_randInit" if getattr(argsP, 'price_random_init', False) else ""
                ft_epochs_gate = getattr(argsP, 'ft_num_epoch', 0)
                epoch_suffix_gate = f"_e{ft_epochs_gate}" if ft_epochs_gate > 0 else ""
                gate_path = f"finetuned_models/{argsP.db}/{argsP.canonical_wl_prefix}_{task_str}_{argsP.llm_pretrained}_{argsP.model_name.replace('/','-')}_b{ft_bs_gate}{price_m_suffix}{price_s_suffix}_llm_price_gated{rand_init_suffix_gate}{epoch_suffix_gate}_gate.pt"
                gate_module = nn.Sequential(nn.Linear(embeddings_test.shape[1], 512), nn.Sigmoid())
                gate_module.load_state_dict(torch.load(gate_path, map_location="cpu"))
                gate_module.eval()
                with torch.no_grad():
                    gate_values = gate_module(embeddings_test)
                price_embeddings = gate_values * price_embeddings
                print(f"Applied learned gate from {gate_path}")

            # Concatenate LLM + PRICE embeddings
            combined = torch.cat([embeddings_test, price_embeddings], dim=1)  # [N, D_llm + 512]

            # Normalize combined embeddings
            feat_norm = FeatureNormalizer()
            feat_norm.fit(combined)
            combined = feat_norm.transform(combined)
            if torch.isnan(combined).any():
                print("[llm_price] NaNs after FeatureNormalizer on combined embeddings")
                exit(0)

            train_ids, val_ids, test_ids = train_val_test(len(combined), argsP)
            embeddings_train = combined[train_ids]
            embeddings_val = combined[val_ids]
            embeddings_test = combined[test_ids]
            costs_train = [costs_test[idx] for idx in train_ids]
            costs_val = [costs_test[idx] for idx in val_ids]
            costs_test = [costs_test[idx] for idx in test_ids]
            lengths_test = [lengths_test[idx] for idx in test_ids]
            templates_test = [templates_test[idx] for idx in test_ids]
        else:
            # Separate train/test files
            embeddings_train_list, costs_train = [], []
            price_train_list = []
            for idx_dp, dat_path_train in enumerate(dat_path_train_list):
                embs, costs, lengths, templates = get_embeddings(
                    predictor, ds_info, dat_path_train, argsP, 16, False, collect_test_info=False
                )
                embeddings_train_list.append(embs)
                costs_train.extend(costs)

                # Get SQL and PRICE embeddings for training workload
                is_cross_wl_train = dat_path_train.endswith("c8220.json")
                if is_cross_wl_train:
                    train_db = pdu.get_db_name_from_json_path(dat_path_train)
                    train_wl = train_db
                    train_sqls = pdu.get_sql_for_cross_workload_plans(dat_path_train, train_db)
                    train_sqls = [s if s is not None else "select count(*) from _dummy" for s in train_sqls]
                else:
                    train_wl = argsP.workloads_train[idx_dp] if idx_dp < len(argsP.workloads_train) else workload
                    train_db = pdu.get_db_name_for_workload(train_wl)
                    train_sql_file = pdu.get_sql_file_for_workload(train_wl, card=argsP.card, for_training=True)
                    train_sqls = pdu.extract_raw_sql_from_queries_true(train_sql_file)
                min_tr = min(len(train_sqls), embs.size(0))
                train_sqls = train_sqls[:min_tr]

                # Generate raw features for this train split
                df_tr, njc_tr, nfo_tr, ntb_tr, nfc_tr = pdu.generate_price_features(train_wl, train_sqls, train_db, bin_size, price_m=getattr(argsP, 'price_m', False), price_s=getattr(argsP, 'price_s', False), already_price_format=is_cross_wl_train)
                price_train_list.append((df_tr[:min_tr], njc_tr[:min_tr], nfo_tr[:min_tr], ntb_tr[:min_tr], nfc_tr[:min_tr]))

            embeddings_train_llm = torch.cat(embeddings_train_list, dim=0)

            # Collect all raw PRICE features for unified padding
            all_raw_feats, all_njc, all_nfo, all_ntb, all_nfc = [], [], [], [], []
            for df_tr, njc_tr, nfo_tr, ntb_tr, nfc_tr in price_train_list:
                all_raw_feats.extend(df_tr)
                all_njc.extend(njc_tr)
                all_nfo.extend(nfo_tr)
                all_ntb.extend(ntb_tr)
                all_nfc.extend(nfc_tr)

            # Test PRICE features
            data_features_test, njc_test, nfo_test, ntb_test, nfc_test = pdu.generate_price_features(
                workload, sql_list_test, db_name, bin_size,
                price_m=getattr(argsP, 'price_m', False),
                price_s=getattr(argsP, 'price_s', False),
                already_price_format=is_cross_wl_test,
            )
            n_train_price = len(all_raw_feats)
            all_raw_feats.extend(data_features_test)
            all_njc.extend(njc_test)
            all_nfo.extend(nfo_test)
            all_ntb.extend(ntb_test)
            all_nfc.extend(nfc_test)

            # Unified padding
            all_padded, all_masks, max_njc, max_nfo, max_ntb, max_nfc = pdu.pad_and_cache_features(
                all_raw_feats, all_njc, all_nfo, all_ntb, all_nfc, bin_size=bin_size,
                price_m=getattr(argsP, 'price_m', False),
            )

            # Build PRICE model and load weights based on price_weights_source
            price_embedder = _load_price_embedder(argsP, max_njc, max_nfo, max_ntb, max_nfc, device)

            # Generate ALL PRICE embeddings (train + test) in batches
            price_embedder.eval()
            price_embs_all = []
            with torch.no_grad():
                for i in range(0, len(all_padded), 64):
                    pf_batch = torch.stack([f if isinstance(f, torch.Tensor) else torch.tensor(f, dtype=torch.float32) for f in all_padded[i:i+64]]).float().to(device)
                    pm_batch = torch.stack([m if isinstance(m, torch.Tensor) else torch.tensor(m) for m in all_masks[i:i+64]]).float().to(device)
                    njc_batch = torch.tensor(all_njc[i:i+64], dtype=torch.float32, device=device).unsqueeze(1)
                    nfo_batch = torch.tensor(all_nfo[i:i+64], dtype=torch.float32, device=device).unsqueeze(1)
                    ntb_batch = torch.tensor(all_ntb[i:i+64], dtype=torch.float32, device=device).unsqueeze(1)
                    nfc_batch = torch.tensor(all_nfc[i:i+64], dtype=torch.float32, device=device).unsqueeze(1)
                    emb = price_embedder(pf_batch, pm_batch, njc_batch, nfo_batch, ntb_batch, nfc_batch)
                    price_embs_all.append(emb.cpu())
            price_embeddings_all = torch.cat(price_embs_all, dim=0)
            price_embedder.to("cpu")
            torch.cuda.empty_cache()

            price_embeddings_train = price_embeddings_all[:n_train_price]
            price_embeddings_test = price_embeddings_all[n_train_price:]
            print(f"Generated PRICE embeddings: train={price_embeddings_train.shape}, test={price_embeddings_test.shape}")

            # Apply learned gate if gated_joint
            if getattr(argsP, 'price_weights_source', 'pretrained') == "gated_joint":
                task_str = "card" if argsP.card else "time"
                ft_bs_gate = getattr(argsP, 'ft_batch_size', 16)
                price_m_suffix = "_priceM" if getattr(argsP, 'price_m', False) else ""
                price_s_suffix = "_priceS" if getattr(argsP, 'price_s', False) else ""
                rand_init_suffix_gate = "_randInit" if getattr(argsP, 'price_random_init', False) else ""
                ft_epochs_gate = getattr(argsP, 'ft_num_epoch', 0)
                epoch_suffix_gate = f"_e{ft_epochs_gate}" if ft_epochs_gate > 0 else ""
                gate_path = f"finetuned_models/{argsP.db}/{argsP.canonical_wl_prefix}_{task_str}_{argsP.llm_pretrained}_{argsP.model_name.replace('/','-')}_b{ft_bs_gate}{price_m_suffix}{price_s_suffix}_llm_price_gated{rand_init_suffix_gate}{epoch_suffix_gate}_gate.pt"
                gate_module = nn.Sequential(nn.Linear(embeddings_train_llm.shape[1], 512), nn.Sigmoid())
                gate_module.load_state_dict(torch.load(gate_path, map_location="cpu"))
                gate_module.eval()
                with torch.no_grad():
                    gate_values_train = gate_module(embeddings_train_llm)
                    gate_values_test = gate_module(embeddings_test)
                price_embeddings_train = gate_values_train * price_embeddings_train
                price_embeddings_test = gate_values_test * price_embeddings_test
                print(f"Applied learned gate from {gate_path}")

            # Concatenate LLM + PRICE
            combined_train = torch.cat([embeddings_train_llm, price_embeddings_train], dim=1)
            combined_test = torch.cat([embeddings_test, price_embeddings_test], dim=1)
            all_combined = torch.cat([combined_train, combined_test], dim=0)

            # Normalize
            feat_norm = FeatureNormalizer()
            all_combined = feat_norm.fit_transform(all_combined)
            if torch.isnan(all_combined).any():
                print("[llm_price] NaNs after FeatureNormalizer on combined train+test")
                exit(0)

            Ntr = combined_train.size(0)
            combined_train = all_combined[:Ntr]
            combined_test = all_combined[Ntr:]

            train_ids, val_ids = train_val(Ntr, argsP)
            embeddings_val = combined_train[val_ids]
            embeddings_train = combined_train[train_ids]
            embeddings_test = combined_test
            costs_val = [costs_train[idx] for idx in val_ids]
            costs_train = [costs_train[idx] for idx in train_ids]

        if hasattr(argsP, 'train_ratio') and 0.0 < argsP.train_ratio < 1.0:
            embeddings_train, costs_train = sample_train(embeddings_train, costs_train, argsP.train_ratio, features_is_list=False)

        argsP.embed_size = embeddings_train.size(1)
        print(f"[llm_price] Combined embed_size = {argsP.embed_size}")

    prepare_ds_info_norm(ds_info)
    # 3) Finally, create the TensorDataset
    if argsP.algo=="llm_finetune":
        if not argsP.card:
            ytr = ds_info.cost_norm.normalize_labels(costs_train)
            yva = ds_info.cost_norm.normalize_labels(costs_val)
            yte = ds_info.cost_norm.normalize_labels(costs_test)
        else:
            ytr = ds_info.card_norm.normalize_labels(costs_train)
            yva = ds_info.card_norm.normalize_labels(costs_val)
            yte = ds_info.card_norm.normalize_labels(costs_test)

        if getattr(argsP, "stats_token_inject", False):
            ds_train = QueryPlanDatasetWithStatsTokens(cleaned_texts_train, stats_vecs_train, ytr)
            ds_val   = QueryPlanDatasetWithStatsTokens(cleaned_texts_val,   stats_vecs_val,   yva)
            ds_test  = QueryPlanDatasetWithStatsTokens(cleaned_texts_test,  stats_vecs_test,  yte)
        else:
            ds_train = QueryPlanDataset(cleaned_texts_train, ytr)
            ds_val   = QueryPlanDataset(cleaned_texts_val,   yva)
            ds_test  = QueryPlanDataset(cleaned_texts_test,  yte)
        argsP.embed_size = predictor.hidden_dim
        return ds_train, ds_val, ds_test, costs_val, costs_test, lengths_test, templates_test
    else:
        # Labels
        if not argsP.card:
            y_train = torch.FloatTensor(ds_info.cost_norm.normalize_labels(costs_train)).view(-1, 1)
            y_val   = torch.FloatTensor(ds_info.cost_norm.normalize_labels(costs_val)).view(-1, 1)
            y_test  = torch.FloatTensor(ds_info.cost_norm.normalize_labels(costs_test)).view(-1, 1)
        else:
            y_train = torch.FloatTensor(ds_info.card_norm.normalize_labels(costs_train)).view(-1, 1)
            y_val   = torch.FloatTensor(ds_info.card_norm.normalize_labels(costs_val)).view(-1, 1)
            y_test  = torch.FloatTensor(ds_info.card_norm.normalize_labels(costs_test)).view(-1, 1)

        # Dataset (stats fusion disabled)
        ds_train = TensorDataset(embeddings_train, y_train)
        ds_val   = TensorDataset(embeddings_val,   y_val)
        ds_test  = TensorDataset(embeddings_test,  y_test)

        return ds_train, ds_val, ds_test, costs_val, costs_test, lengths_test, templates_test


#########################################
#  Joint LLM+PRICE Dataset & Loading
#########################################

class LLMPriceDataset(Dataset):
    """
    Dataset for joint LLM+PRICE finetuning.
    Each item returns (text, price_feat_tensor, padding_mask,
                       n_join_col, n_fanout, n_table, n_filter_col, label).
    """
    def __init__(self, texts, price_features, padding_masks,
                 n_join_cols, n_fanouts, n_tables, n_filter_cols, labels):
        assert len(texts) == len(labels)
        self.texts = texts
        self.price_features = price_features
        self.padding_masks = padding_masks
        self.n_join_cols = n_join_cols
        self.n_fanouts = n_fanouts
        self.n_tables = n_tables
        self.n_filter_cols = n_filter_cols
        self.labels = labels

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return (self.texts[idx],
                self.price_features[idx],
                self.padding_masks[idx],
                self.n_join_cols[idx],
                self.n_fanouts[idx],
                self.n_tables[idx],
                self.n_filter_cols[idx],
                self.labels[idx])


class FrozenLLMPriceDataset(Dataset):
    """
    Dataset for PRICE+MLP finetuning with pre-computed (frozen) LLM embeddings.
    Each item returns (llm_embedding, price_feat_tensor, padding_mask,
                       n_join_col, n_fanout, n_table, n_filter_col, label).
    Unlike LLMPriceDataset, stores LLM embeddings as tensors instead of text.
    """
    def __init__(self, llm_embeddings, price_features, padding_masks,
                 n_join_cols, n_fanouts, n_tables, n_filter_cols, labels):
        assert len(llm_embeddings) == len(labels)
        self.llm_embeddings = llm_embeddings
        self.price_features = price_features
        self.padding_masks = padding_masks
        self.n_join_cols = n_join_cols
        self.n_fanouts = n_fanouts
        self.n_tables = n_tables
        self.n_filter_cols = n_filter_cols
        self.labels = labels

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return (self.llm_embeddings[idx],
                self.price_features[idx],
                self.padding_masks[idx],
                self.n_join_cols[idx],
                self.n_fanouts[idx],
                self.n_tables[idx],
                self.n_filter_cols[idx],
                self.labels[idx])


class PriceOnlyDataset(Dataset):
    """
    Dataset for standalone PRICE finetuning on cardinality estimation.
    Each item returns (price_feat, pg_est_card, pad_mask, njc, nfo, ntb, nfc, label).
    """
    def __init__(self, price_features, pg_est_cards, padding_masks,
                 n_join_cols, n_fanouts, n_tables, n_filter_cols, labels):
        assert len(price_features) == len(labels)
        self.price_features = price_features
        self.pg_est_cards = pg_est_cards
        self.padding_masks = padding_masks
        self.n_join_cols = n_join_cols
        self.n_fanouts = n_fanouts
        self.n_tables = n_tables
        self.n_filter_cols = n_filter_cols
        self.labels = labels

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return (self.price_features[idx],
                self.pg_est_cards[idx],
                self.padding_masks[idx],
                self.n_join_cols[idx],
                self.n_fanouts[idx],
                self.n_tables[idx],
                self.n_filter_cols[idx],
                self.labels[idx])


def get_price_only_ds_from_csv(dat_path_train_list, dat_path_test, ds_info, argsP):
    """
    Build datasets for standalone PRICE finetuning on cardinality estimation.

    1) Read _sub.csv cardinality data
    2) Parse SQL from queries_true_sql for PRICE features
    3) Generate/load cached PRICE features
    4) Extract pg_est_card from plan JSONs
    5) Split train/val/test
    6) Normalize with log(card+1)+1 and return PriceOnlyDataset instances

    Returns: ds_train, ds_val, ds_test, costs_val, costs_test
    """
    import price_data_utils as pdu

    workload = argsP.workload_test
    db_name = pdu.get_db_name_for_workload(workload)
    bin_size = getattr(argsP, 'price_bin_size', 40)

    # ---- Step 1: Read cardinality data ----
    print(f"[PRICE finetune] Step 1: Reading cardinality data from {dat_path_test}...", flush=True)
    df_test = pd.read_csv(dat_path_test)
    # Extract true cardinalities from the CSV
    costs_all = []
    for raw_json in df_test["json"]:
        try:
            plan = json.loads(raw_json) if isinstance(raw_json, str) else raw_json
            if isinstance(plan, list):
                plan = plan[0]
            root = plan.get("Plan", plan)
            card = root.get("Actual Rows", root.get("Plan Rows", 1.0))
            costs_all.append(float(card))
        except Exception:
            costs_all.append(1.0)

    # ---- Step 2: Parse SQL for PRICE ----
    sql_file = pdu.get_sql_file_for_workload(workload, card=True)
    print(f"[PRICE finetune] Step 2: Loading SQL from {sql_file}", flush=True)
    sql_list = pdu.extract_raw_sql_from_queries_true(sql_file)

    # Align
    min_len = min(len(sql_list), len(costs_all))
    sql_list = sql_list[:min_len]
    costs_all = costs_all[:min_len]

    # ---- Step 3: Generate PRICE features ----
    print(f"[PRICE finetune] Step 3: Generating PRICE features for {len(sql_list)} queries...", flush=True)
    data_features, n_join_cols, n_fanouts, n_tables, n_filter_cols = pdu.generate_price_features(
        workload, sql_list, db_name, bin_size,
        price_m=getattr(argsP, 'price_m', False),
        price_s=getattr(argsP, 'price_s', False)
    )

    # ---- Step 4: Extract pg_est_card ----
    print(f"[PRICE finetune] Step 4: Extracting pg_est_card from plan JSONs...", flush=True)
    pg_est_cards = []
    for raw_json in df_test["json"][:min_len]:
        try:
            pg_est_cards.append(pdu.extract_pg_est_card_from_plan(raw_json))
        except Exception:
            pg_est_cards.append(1.0)

    # ---- Step 5: Pad features and split ----
    print(f"[PRICE finetune] Step 5: Padding features and splitting...", flush=True)
    if len(dat_path_train_list) == 1 and dat_path_train_list[0] == dat_path_test:
        # Same file — pad all, then split
        padded_features, padding_masks, max_njc, max_nfo, max_ntb, max_nfc = pdu.pad_and_cache_features(
            data_features, n_join_cols, n_fanouts, n_tables, n_filter_cols, bin_size=bin_size,
            price_m=getattr(argsP, 'price_m', False),
        )
        train_ids, val_ids, test_ids = train_val_test(len(costs_all), argsP)

        def _subset(lst, ids):
            return [lst[i] for i in ids]

        pf_train = _subset(padded_features, train_ids)
        pf_val = _subset(padded_features, val_ids)
        pf_test = _subset(padded_features, test_ids)
        pm_train = _subset(padding_masks, train_ids)
        pm_val = _subset(padding_masks, val_ids)
        pm_test = _subset(padding_masks, test_ids)
        njc_train = _subset(n_join_cols, train_ids)
        njc_val = _subset(n_join_cols, val_ids)
        njc_test = _subset(n_join_cols, test_ids)
        nfo_train = _subset(n_fanouts, train_ids)
        nfo_val = _subset(n_fanouts, val_ids)
        nfo_test = _subset(n_fanouts, test_ids)
        ntb_train = _subset(n_tables, train_ids)
        ntb_val = _subset(n_tables, val_ids)
        ntb_test = _subset(n_tables, test_ids)
        nfc_train = _subset(n_filter_cols, train_ids)
        nfc_val = _subset(n_filter_cols, val_ids)
        nfc_test = _subset(n_filter_cols, test_ids)
        pgc_train = _subset(pg_est_cards, train_ids)
        pgc_val = _subset(pg_est_cards, val_ids)
        pgc_test = _subset(pg_est_cards, test_ids)
        costs_train = _subset(costs_all, train_ids)
        costs_val = _subset(costs_all, val_ids)
        costs_test = _subset(costs_all, test_ids)
    else:
        # Separate train/test files — collect all features, pad together
        raw_feats_train, njc_train_all, nfo_train_all, ntb_train_all, nfc_train_all = [], [], [], [], []
        pgc_train_all, costs_train_all = [], []

        for idx_dp, dat_path_train in enumerate(dat_path_train_list):
            train_wl = argsP.workloads_train[idx_dp] if idx_dp < len(argsP.workloads_train) else workload
            train_db = pdu.get_db_name_for_workload(train_wl)
            train_sql_file = pdu.get_sql_file_for_workload(train_wl, card=True, for_training=True)
            train_sqls = pdu.extract_raw_sql_from_queries_true(train_sql_file)

            df_train = pd.read_csv(dat_path_train)
            min_tr = min(len(train_sqls), len(df_train))
            train_sqls = train_sqls[:min_tr]

            df_feats, njc, nfo, ntb, nfc = pdu.generate_price_features(train_wl, train_sqls, train_db, bin_size, price_m=getattr(argsP, 'price_m', False), price_s=getattr(argsP, 'price_s', False))
            raw_feats_train.extend(df_feats[:min_tr])
            njc_train_all.extend(njc[:min_tr])
            nfo_train_all.extend(nfo[:min_tr])
            ntb_train_all.extend(ntb[:min_tr])
            nfc_train_all.extend(nfc[:min_tr])

            for raw_json in df_train["json"][:min_tr]:
                try:
                    pgc_train_all.append(pdu.extract_pg_est_card_from_plan(raw_json))
                except Exception:
                    pgc_train_all.append(1.0)

            for raw_json in df_train["json"][:min_tr]:
                try:
                    plan = json.loads(raw_json) if isinstance(raw_json, str) else raw_json
                    if isinstance(plan, list):
                        plan = plan[0]
                    root = plan.get("Plan", plan)
                    costs_train_all.append(float(root.get("Actual Rows", root.get("Plan Rows", 1.0))))
                except Exception:
                    costs_train_all.append(1.0)

        # Unified padding across train + test
        all_raw_feats = raw_feats_train + list(data_features)
        all_njc = njc_train_all + n_join_cols
        all_nfo = nfo_train_all + n_fanouts
        all_ntb = ntb_train_all + n_tables
        all_nfc = nfc_train_all + n_filter_cols

        all_padded, all_masks, max_njc, max_nfo, max_ntb, max_nfc = pdu.pad_and_cache_features(
            all_raw_feats, all_njc, all_nfo, all_ntb, all_nfc, bin_size=bin_size,
            price_m=getattr(argsP, 'price_m', False),
        )

        n_train = len(raw_feats_train)
        pf_train_all = all_padded[:n_train]
        pm_train_all = all_masks[:n_train]
        padded_features = all_padded[n_train:]
        padding_masks = all_masks[n_train:]

        train_ids, val_ids = train_val(n_train, argsP)

        def _subset(lst, ids):
            return [lst[i] for i in ids]

        pf_train = _subset(pf_train_all, train_ids)
        pf_val = _subset(pf_train_all, val_ids)
        pf_test = padded_features
        pm_train = _subset(pm_train_all, train_ids)
        pm_val = _subset(pm_train_all, val_ids)
        pm_test = padding_masks
        njc_train = _subset(njc_train_all, train_ids)
        njc_val = _subset(njc_train_all, val_ids)
        njc_test = n_join_cols
        nfo_train = _subset(nfo_train_all, train_ids)
        nfo_val = _subset(nfo_train_all, val_ids)
        nfo_test = n_fanouts
        ntb_train = _subset(ntb_train_all, train_ids)
        ntb_val = _subset(ntb_train_all, val_ids)
        ntb_test = n_tables
        nfc_train = _subset(nfc_train_all, train_ids)
        nfc_val = _subset(nfc_train_all, val_ids)
        nfc_test = n_filter_cols
        pgc_train = _subset(pgc_train_all, train_ids)
        pgc_val = _subset(pgc_train_all, val_ids)
        pgc_test = pg_est_cards
        costs_train = _subset(costs_train_all, train_ids)
        costs_val = _subset(costs_train_all, val_ids)
        costs_test = costs_all

    # Store max dims on argsP for model construction
    argsP.price_max_n_join_col = max_njc
    argsP.price_max_n_fanout = max_nfo
    argsP.price_max_n_table = max_ntb
    argsP.price_max_n_filter_col = max_nfc

    # ---- Step 6: Normalize labels with log(card+1)+1 and create datasets ----
    print(f"[PRICE finetune] Step 6: Normalizing and creating datasets (train={len(costs_train)}, val={len(costs_val)}, test={len(costs_test)})...", flush=True)

    # Update ds_info normalizer
    all_costs = costs_train + costs_val + costs_test
    update_ds_info_minmax(ds_info, all_costs, all_costs)
    prepare_ds_info_norm(ds_info)

    ytr = ds_info.card_norm.normalize_labels(costs_train)
    yva = ds_info.card_norm.normalize_labels(costs_val)
    yte = ds_info.card_norm.normalize_labels(costs_test)

    ds_train = PriceOnlyDataset(pf_train, pgc_train, pm_train,
                                njc_train, nfo_train, ntb_train, nfc_train, ytr)
    ds_val = PriceOnlyDataset(pf_val, pgc_val, pm_val,
                              njc_val, nfo_val, ntb_val, nfc_val, yva)
    ds_test = PriceOnlyDataset(pf_test, pgc_test, pm_test,
                               njc_test, nfo_test, ntb_test, nfc_test, yte)

    return ds_train, ds_val, ds_test, costs_val, costs_test


def get_llm_price_ds_from_csv(predictor, dat_path_train_list, dat_path_test, ds_info, argsP):
    """
    Build datasets for joint LLM+PRICE finetuning.

    1) Read query plans via read_json_and_clean() for LLM text + labels
    2) Parse SQL from queries_true_sql for PRICE features
    3) Generate/load cached PRICE features
    4) Extract pg_est_card from plan JSONs
    5) Split train/val/test
    6) Return LLMPriceDataset instances

    Returns same signature as get_llm_ds_from_csv:
        ds_train, ds_val, ds_test, costs_val, costs_test, lengths_test, templates_test
    """
    import price_data_utils as pdu

    argsP.inference_logger.info(f"Getting LLM+PRICE dataset from {dat_path_train_list} and {dat_path_test}")

    workload = argsP.workload_test
    db_name = pdu.get_db_name_for_workload(workload)
    bin_size = getattr(argsP, 'price_bin_size', 40)

    # ---- Step 1: Read query plans (texts + labels) ----
    print(f"[LLM+PRICE] Step 1/6: Reading test query plans from {dat_path_test}...", flush=True)
    is_cross_wl_test = dat_path_test.endswith("c8220.json")
    if is_cross_wl_test:
        cleaned_texts_test, costs_test, lengths_test, templates_test = read_json_and_clean_v2(
            predictor, ds_info, dat_path_test, argsP
        )
    else:
        cleaned_texts_test, costs_test, lengths_test, templates_test = read_json_and_clean(
            predictor, ds_info, dat_path_test, argsP
        )
    print(f"[LLM+PRICE] Step 1/6 done: {len(cleaned_texts_test)} test plans read.", flush=True)

    # ---- Step 2: Parse SQL for PRICE ----
    if is_cross_wl_test:
        # Cross-workload: reconstruct SQL from plan trees
        test_db = pdu.get_db_name_from_json_path(dat_path_test)
        print(f"[LLM+PRICE] Step 2/6: Reconstructing SQL from {dat_path_test} (db={test_db})", flush=True)
        sql_list_test = pdu.get_sql_for_cross_workload_plans(dat_path_test, test_db)
        # Replace None entries with empty queries (will get zero-fill in feature generation)
        sql_list_test = [s if s is not None else "select count(*) from _dummy" for s in sql_list_test]
        # Override db_name to use per-database stats
        db_name = test_db
    else:
        sql_file = pdu.get_sql_file_for_workload(workload, card=argsP.card)
        print(f"[LLM+PRICE] Step 2/6: Loading SQL from {sql_file}", flush=True)
        sql_list_test = pdu.extract_raw_sql_from_queries_true(sql_file)

    # Verify alignment
    if len(sql_list_test) != len(cleaned_texts_test):
        print(f"[LLM+PRICE] Warning: SQL count ({len(sql_list_test)}) != plan count ({len(cleaned_texts_test)}). Using min.")
        min_len = min(len(sql_list_test), len(cleaned_texts_test))
        sql_list_test = sql_list_test[:min_len]
        cleaned_texts_test = cleaned_texts_test[:min_len]
        costs_test = costs_test[:min_len]
        lengths_test = lengths_test[:min_len]
        templates_test = templates_test[:min_len]

    # ---- Step 3: Generate raw PRICE features (unpadded) ----
    print(f"[LLM+PRICE] Step 3/6: Generating PRICE features for {len(sql_list_test)} test queries...", flush=True)
    db = getattr(argsP, 'db', 'postgres')
    cache_dir = os.path.join(os.path.dirname(__file__), "price_feature_cache", db)
    task_str = "card" if argsP.card else "time"

    data_features_test, n_join_cols_test, n_fanouts_test, n_tables_test, n_filter_cols_test = pdu.generate_price_features(
        workload, sql_list_test, db_name, bin_size,
        price_m=getattr(argsP, 'price_m', False),
        price_s=getattr(argsP, 'price_s', False),
        already_price_format=is_cross_wl_test,
    )

    # ---- Step 4: Extract pg_est_card (only for CSV-format data) ----
    if not is_cross_wl_test:
        print(f"[LLM+PRICE] Step 4/6: Extracting pg_est_card from plan JSONs...", flush=True)
        df_test = pd.read_csv(dat_path_test)
        pg_est_cards = []
        for raw_json in df_test["json"]:
            try:
                pg_est_cards.append(pdu.extract_pg_est_card_from_plan(raw_json))
            except Exception:
                pg_est_cards.append(1.0)
    else:
        print(f"[LLM+PRICE] Step 4/6: Skipping pg_est_card (cross-workload JSON)...", flush=True)

    # ---- Step 5: Split train/val/test and pad with unified max dims ----
    print(f"[LLM+PRICE] Step 5/6: Splitting train/val/test...", flush=True)
    if len(dat_path_train_list) == 1 and dat_path_train_list[0] == dat_path_test:
        # Same file for train/test — pad all together
        padded_features, padding_masks, max_njc, max_nfo, max_ntb, max_nfc = pdu.pad_and_cache_features(
            data_features_test, n_join_cols_test, n_fanouts_test, n_tables_test, n_filter_cols_test,
            bin_size=bin_size,
            price_m=getattr(argsP, 'price_m', False),
        )
        n_join_cols = n_join_cols_test
        n_fanouts = n_fanouts_test
        n_tables = n_tables_test
        n_filter_cols = n_filter_cols_test

        train_ids, val_ids, test_ids = train_val_test(len(cleaned_texts_test), argsP)

        def _subset(lst, ids):
            return [lst[i] for i in ids]

        texts_train = _subset(cleaned_texts_test, train_ids)
        texts_val = _subset(cleaned_texts_test, val_ids)
        texts_test_split = _subset(cleaned_texts_test, test_ids)

        costs_train = _subset(costs_test, train_ids)
        costs_val = _subset(costs_test, val_ids)
        costs_test_split = _subset(costs_test, test_ids)

        lengths_test = _subset(lengths_test, test_ids)
        templates_test = _subset(templates_test, test_ids)

        pf_train = _subset(padded_features, train_ids)
        pf_val = _subset(padded_features, val_ids)
        pf_test = _subset(padded_features, test_ids)

        pm_train = _subset(padding_masks, train_ids)
        pm_val = _subset(padding_masks, val_ids)
        pm_test = _subset(padding_masks, test_ids)

        njc_train = _subset(n_join_cols, train_ids)
        njc_val = _subset(n_join_cols, val_ids)
        njc_test = _subset(n_join_cols, test_ids)

        nfo_train = _subset(n_fanouts, train_ids)
        nfo_val = _subset(n_fanouts, val_ids)
        nfo_test = _subset(n_fanouts, test_ids)

        ntb_train = _subset(n_tables, train_ids)
        ntb_val = _subset(n_tables, val_ids)
        ntb_test = _subset(n_tables, test_ids)

        nfc_train = _subset(n_filter_cols, train_ids)
        nfc_val = _subset(n_filter_cols, val_ids)
        nfc_test = _subset(n_filter_cols, test_ids)

        costs_test = costs_test_split
        cleaned_texts_test = texts_test_split
    else:
        # Separate train / test files — collect all raw features first, then pad together
        cleaned_texts_train_all, costs_train_all = [], []
        raw_feats_train_all = []
        njc_train_all, nfo_train_all, ntb_train_all, nfc_train_all = [], [], [], []

        for idx_dp, dat_path_train in enumerate(dat_path_train_list):
            print(f"[LLM+PRICE] Step 5/6: Reading training plans from {dat_path_train}...", flush=True)
            is_cross_wl_train = dat_path_train.endswith("c8220.json")
            if is_cross_wl_train:
                ct, co, ln, tp = read_json_and_clean_v2(predictor, ds_info, dat_path_train, argsP)
            else:
                ct, co, ln, tp = read_json_and_clean(predictor, ds_info, dat_path_train, argsP)
            cleaned_texts_train_all.extend(ct)
            costs_train_all.extend(co)
            print(f"[LLM+PRICE] Step 5/6: {len(ct)} training plans read.", flush=True)

            # Get SQL for this training workload
            if is_cross_wl_train:
                # Cross-workload: reconstruct SQL from plan trees
                train_db = pdu.get_db_name_from_json_path(dat_path_train)
                train_wl = train_db
                print(f"[LLM+PRICE] Step 5/6: Reconstructing SQL from {dat_path_train} (db={train_db})", flush=True)
                train_sqls = pdu.get_sql_for_cross_workload_plans(dat_path_train, train_db)
                train_sqls = [s if s is not None else "select count(*) from _dummy" for s in train_sqls]
            else:
                train_wl = argsP.workloads_train[idx_dp] if idx_dp < len(argsP.workloads_train) else workload
                train_db = pdu.get_db_name_for_workload(train_wl)
                train_sql_file = pdu.get_sql_file_for_workload(train_wl, card=argsP.card, for_training=True)
                train_sqls = pdu.extract_raw_sql_from_queries_true(train_sql_file)

            min_len = min(len(train_sqls), len(ct))
            train_sqls = train_sqls[:min_len]

            print(f"[LLM+PRICE] Step 5/6: Generating PRICE features for {min_len} training queries...", flush=True)
            df_feats, njc, nfo, ntb, nfc = pdu.generate_price_features(train_wl, train_sqls, train_db, bin_size, price_m=getattr(argsP, 'price_m', False), price_s=getattr(argsP, 'price_s', False), already_price_format=is_cross_wl_train)
            raw_feats_train_all.extend(df_feats[:min_len])
            njc_train_all.extend(njc[:min_len])
            nfo_train_all.extend(nfo[:min_len])
            ntb_train_all.extend(ntb[:min_len])
            nfc_train_all.extend(nfc[:min_len])

        # Compute unified max dims across train AND test
        all_njc = njc_train_all + n_join_cols_test
        all_nfo = nfo_train_all + n_fanouts_test
        all_ntb = ntb_train_all + n_tables_test
        all_nfc = nfc_train_all + n_filter_cols_test
        max_njc = max(all_njc)
        max_nfo = max(all_nfo)
        max_ntb = max(all_ntb)
        max_nfc = max(all_nfc)
        print(f"[LLM+PRICE] Unified max dims: n_join_col={max_njc}, n_fanout={max_nfo}, n_table={max_ntb}, n_filter_col={max_nfc}", flush=True)

        # Pad ALL features (train + test) with the unified max dims
        all_raw_feats = raw_feats_train_all + list(data_features_test)
        all_njc_list = njc_train_all + n_join_cols_test
        all_nfo_list = nfo_train_all + n_fanouts_test
        all_ntb_list = ntb_train_all + n_tables_test
        all_nfc_list = nfc_train_all + n_filter_cols_test

        print(f"[LLM+PRICE] Step 5/6: Padding {len(all_raw_feats)} features with unified dims...", flush=True)
        all_padded, all_masks, _, _, _, _ = pdu.pad_and_cache_features(
            all_raw_feats, all_njc_list, all_nfo_list, all_ntb_list, all_nfc_list,
            bin_size=bin_size,
            price_m=getattr(argsP, 'price_m', False),
            # Pass max dims explicitly to ensure consistency
        )

        # Split back into train and test portions
        n_train = len(raw_feats_train_all)
        pf_train_all = all_padded[:n_train]
        pm_train_all = all_masks[:n_train]
        padded_features = all_padded[n_train:]
        padding_masks = all_masks[n_train:]
        n_join_cols = n_join_cols_test
        n_fanouts = n_fanouts_test
        n_tables = n_tables_test
        n_filter_cols = n_filter_cols_test

        train_ids, val_ids = train_val(len(cleaned_texts_train_all), argsP)

        def _subset(lst, ids):
            return [lst[i] for i in ids]

        texts_val = _subset(cleaned_texts_train_all, val_ids)
        texts_train = _subset(cleaned_texts_train_all, train_ids)

        costs_val = _subset(costs_train_all, val_ids)
        costs_train = _subset(costs_train_all, train_ids)

        pf_val = _subset(pf_train_all, val_ids)
        pf_train = _subset(pf_train_all, train_ids)

        pm_val = _subset(pm_train_all, val_ids)
        pm_train = _subset(pm_train_all, train_ids)

        njc_val = _subset(njc_train_all, val_ids)
        njc_train = _subset(njc_train_all, train_ids)

        nfo_val = _subset(nfo_train_all, val_ids)
        nfo_train = _subset(nfo_train_all, train_ids)

        ntb_val = _subset(ntb_train_all, val_ids)
        ntb_train = _subset(ntb_train_all, train_ids)

        nfc_val = _subset(nfc_train_all, val_ids)
        nfc_train = _subset(nfc_train_all, train_ids)

        # Apply train_ratio subsampling (consistent with llm_finetune path)
        if hasattr(argsP, 'train_ratio') and 0.0 < argsP.train_ratio < 1.0:
            n_before = len(texts_train)
            sample_ids, _ = train_test_split(
                list(range(n_before)), train_size=argsP.train_ratio, random_state=42
            )
            texts_train = [texts_train[i] for i in sample_ids]
            costs_train = [costs_train[i] for i in sample_ids]
            pf_train = [pf_train[i] for i in sample_ids]
            pm_train = [pm_train[i] for i in sample_ids]
            njc_train = [njc_train[i] for i in sample_ids]
            nfo_train = [nfo_train[i] for i in sample_ids]
            ntb_train = [ntb_train[i] for i in sample_ids]
            nfc_train = [nfc_train[i] for i in sample_ids]
            print(f"[LLM+PRICE] Subsampled training set: {n_before} -> {len(texts_train)} (train_ratio={argsP.train_ratio})", flush=True)

        texts_test_split = cleaned_texts_test
        pf_test = padded_features
        pm_test = padding_masks
        njc_test = n_join_cols
        nfo_test = n_fanouts
        ntb_test = n_tables
        nfc_test = n_filter_cols

    # Store max dims on argsP for model construction
    argsP.price_max_n_join_col = max_njc
    argsP.price_max_n_fanout = max_nfo
    argsP.price_max_n_table = max_ntb
    argsP.price_max_n_filter_col = max_nfc
    print(f"[LLM+PRICE] Model dims: n_join_col={max_njc}, n_fanout={max_nfo}, n_table={max_ntb}, n_filter_col={max_nfc}", flush=True)

    # ---- Step 6: Normalize labels and create datasets ----
    print(f"[LLM+PRICE] Step 6/6: Creating datasets (train={len(texts_train)}, val={len(texts_val)}, test={len(texts_test_split)})...", flush=True)
    update_ds_info_minmax(ds_info, costs_train + costs_val + costs_test,
                          costs_train + costs_val + costs_test)
    prepare_ds_info_norm(ds_info)

    if not argsP.card:
        ytr = ds_info.cost_norm.normalize_labels(costs_train)
        yva = ds_info.cost_norm.normalize_labels(costs_val)
        yte = ds_info.cost_norm.normalize_labels(costs_test)
    else:
        ytr = ds_info.card_norm.normalize_labels(costs_train)
        yva = ds_info.card_norm.normalize_labels(costs_val)
        yte = ds_info.card_norm.normalize_labels(costs_test)

    ds_train = LLMPriceDataset(texts_train, pf_train, pm_train,
                               njc_train, nfo_train, ntb_train, nfc_train, ytr)
    ds_val = LLMPriceDataset(texts_val, pf_val, pm_val,
                             njc_val, nfo_val, ntb_val, nfc_val, yva)
    ds_test = LLMPriceDataset(texts_test_split, pf_test, pm_test,
                              njc_test, nfo_test, ntb_test, nfc_test, yte)

    argsP.embed_size = predictor.hidden_dim

    return ds_train, ds_val, ds_test, costs_val, costs_test, lengths_test, templates_test


def get_frozen_llm_price_ds_from_csv(predictor, dat_path_train_list, dat_path_test, ds_info, argsP):
    """
    Build datasets for PRICE+MLP finetuning with pre-computed (frozen) LLM embeddings.

    Instead of storing raw text (which requires a live LLM forward pass each batch),
    this calls get_embeddings() to load cached LLM embeddings and stores them as tensors.
    The cached embeddings are reused from prior LLM inference runs (algo=llm).

    Returns same signature as get_llm_price_ds_from_csv:
        ds_train, ds_val, ds_test, costs_val, costs_test, lengths_test, templates_test
    """
    import price_data_utils as pdu

    argsP.inference_logger.info(f"Getting frozen-LLM+PRICE dataset from {dat_path_train_list} and {dat_path_test}")

    workload = argsP.workload_test
    db_name = pdu.get_db_name_for_workload(workload)
    bin_size = getattr(argsP, 'price_bin_size', 40)

    # ---- Step 1: Get LLM embeddings via get_embeddings() (cached) ----
    # Temporarily override algo so cache key matches prior "llm" inference runs
    orig_algo = argsP.algo
    argsP.algo = "llm"
    print(f"[FrozenLLM+PRICE] Step 1: Loading cached LLM embeddings for test...", flush=True)
    embeddings_test, costs_test, lengths_test, templates_test = get_embeddings(
        predictor, ds_info, dat_path_test, argsP, batch_size=16, normalize_feats=False
    )
    argsP.algo = orig_algo

    llm_embed_size = embeddings_test.shape[1]
    print(f"[FrozenLLM+PRICE] Step 1 done: {embeddings_test.shape[0]} embeddings, dim={llm_embed_size}", flush=True)

    # ---- Step 2: Parse SQL for PRICE ----
    is_cross_wl_test = dat_path_test.endswith("c8220.json")
    if is_cross_wl_test:
        test_db = pdu.get_db_name_from_json_path(dat_path_test)
        print(f"[FrozenLLM+PRICE] Step 2: Reconstructing SQL from {dat_path_test} (db={test_db})", flush=True)
        sql_list_test = pdu.get_sql_for_cross_workload_plans(dat_path_test, test_db)
        sql_list_test = [s if s is not None else "select count(*) from _dummy" for s in sql_list_test]
        db_name = test_db
    else:
        sql_file = pdu.get_sql_file_for_workload(workload, card=argsP.card)
        print(f"[FrozenLLM+PRICE] Step 2: Loading SQL from {sql_file}", flush=True)
        sql_list_test = pdu.extract_raw_sql_from_queries_true(sql_file)

    # Verify alignment
    n_emb = embeddings_test.shape[0]
    if len(sql_list_test) != n_emb:
        print(f"[FrozenLLM+PRICE] Warning: SQL count ({len(sql_list_test)}) != embedding count ({n_emb}). Using min.")
        min_len = min(len(sql_list_test), n_emb)
        sql_list_test = sql_list_test[:min_len]
        embeddings_test = embeddings_test[:min_len]
        costs_test = costs_test[:min_len]
        lengths_test = lengths_test[:min_len]
        templates_test = templates_test[:min_len]

    # ---- Step 3: Generate PRICE features ----
    print(f"[FrozenLLM+PRICE] Step 3: Generating PRICE features for {len(sql_list_test)} test queries...", flush=True)
    data_features_test, n_join_cols_test, n_fanouts_test, n_tables_test, n_filter_cols_test = pdu.generate_price_features(
        workload, sql_list_test, db_name, bin_size,
        price_m=getattr(argsP, 'price_m', False),
        price_s=getattr(argsP, 'price_s', False),
        already_price_format=is_cross_wl_test,
    )

    # ---- Step 4: Split train/val/test and pad ----
    print(f"[FrozenLLM+PRICE] Step 4: Splitting train/val/test...", flush=True)
    if len(dat_path_train_list) == 1 and dat_path_train_list[0] == dat_path_test:
        # Same file for train/test
        padded_features, padding_masks, max_njc, max_nfo, max_ntb, max_nfc = pdu.pad_and_cache_features(
            data_features_test, n_join_cols_test, n_fanouts_test, n_tables_test, n_filter_cols_test,
            bin_size=bin_size,
            price_m=getattr(argsP, 'price_m', False),
        )

        train_ids, val_ids, test_ids = train_val_test(n_emb, argsP)

        def _subset(lst, ids):
            return [lst[i] for i in ids]

        def _subset_tensor(t, ids):
            return t[ids]

        emb_train = _subset_tensor(embeddings_test, train_ids)
        emb_val = _subset_tensor(embeddings_test, val_ids)
        emb_test = _subset_tensor(embeddings_test, test_ids)

        costs_train = _subset(costs_test, train_ids)
        costs_val = _subset(costs_test, val_ids)
        costs_test = _subset(costs_test, test_ids)

        lengths_test = _subset(lengths_test, test_ids)
        templates_test = _subset(templates_test, test_ids)

        pf_train = _subset(padded_features, train_ids)
        pf_val = _subset(padded_features, val_ids)
        pf_test = _subset(padded_features, test_ids)

        pm_train = _subset(padding_masks, train_ids)
        pm_val = _subset(padding_masks, val_ids)
        pm_test = _subset(padding_masks, test_ids)

        njc_train = _subset(n_join_cols_test, train_ids)
        njc_val = _subset(n_join_cols_test, val_ids)
        njc_test = _subset(n_join_cols_test, test_ids)

        nfo_train = _subset(n_fanouts_test, train_ids)
        nfo_val = _subset(n_fanouts_test, val_ids)
        nfo_test = _subset(n_fanouts_test, test_ids)

        ntb_train = _subset(n_tables_test, train_ids)
        ntb_val = _subset(n_tables_test, val_ids)
        ntb_test = _subset(n_tables_test, test_ids)

        nfc_train = _subset(n_filter_cols_test, train_ids)
        nfc_val = _subset(n_filter_cols_test, val_ids)
        nfc_test = _subset(n_filter_cols_test, test_ids)
    else:
        # Separate train / test files
        emb_train_all, costs_train_all = [], []
        raw_feats_train_all = []
        njc_train_all, nfo_train_all, ntb_train_all, nfc_train_all = [], [], [], []

        for idx_dp, dat_path_train in enumerate(dat_path_train_list):
            print(f"[FrozenLLM+PRICE] Loading cached LLM embeddings for train: {dat_path_train}...", flush=True)
            orig_algo2 = argsP.algo
            argsP.algo = "llm"
            emb_part, costs_part, _, _ = get_embeddings(
                predictor, ds_info, dat_path_train, argsP, batch_size=16, normalize_feats=False
            )
            argsP.algo = orig_algo2
            emb_train_all.append(emb_part)
            costs_train_all.extend(costs_part)

            is_cross_wl_train = dat_path_train.endswith("c8220.json")
            if is_cross_wl_train:
                train_db = pdu.get_db_name_from_json_path(dat_path_train)
                train_wl = train_db
                print(f"[FrozenLLM+PRICE] Reconstructing SQL from {dat_path_train} (db={train_db})", flush=True)
                train_sqls = pdu.get_sql_for_cross_workload_plans(dat_path_train, train_db)
                train_sqls = [s if s is not None else "select count(*) from _dummy" for s in train_sqls]
            else:
                train_wl = argsP.workloads_train[idx_dp] if idx_dp < len(argsP.workloads_train) else workload
                train_db = pdu.get_db_name_for_workload(train_wl)
                train_sql_file = pdu.get_sql_file_for_workload(train_wl, card=argsP.card, for_training=True)
                train_sqls = pdu.extract_raw_sql_from_queries_true(train_sql_file)

            min_len = min(len(train_sqls), emb_part.shape[0])
            train_sqls = train_sqls[:min_len]

            df_feats, njc, nfo, ntb, nfc = pdu.generate_price_features(train_wl, train_sqls, train_db, bin_size, price_m=getattr(argsP, 'price_m', False), price_s=getattr(argsP, 'price_s', False), already_price_format=is_cross_wl_train)
            raw_feats_train_all.extend(df_feats[:min_len])
            njc_train_all.extend(njc[:min_len])
            nfo_train_all.extend(nfo[:min_len])
            ntb_train_all.extend(ntb[:min_len])
            nfc_train_all.extend(nfc[:min_len])

        emb_train_cat = torch.cat(emb_train_all, dim=0)

        # Pad all features with unified max dims
        all_raw_feats = raw_feats_train_all + list(data_features_test)
        all_njc_list = njc_train_all + n_join_cols_test
        all_nfo_list = nfo_train_all + n_fanouts_test
        all_ntb_list = ntb_train_all + n_tables_test
        all_nfc_list = nfc_train_all + n_filter_cols_test

        all_padded, all_masks, max_njc, max_nfo, max_ntb, max_nfc = pdu.pad_and_cache_features(
            all_raw_feats, all_njc_list, all_nfo_list, all_ntb_list, all_nfc_list,
            bin_size=bin_size,
            price_m=getattr(argsP, 'price_m', False),
        )

        n_train = len(raw_feats_train_all)
        pf_train_all = all_padded[:n_train]
        pm_train_all = all_masks[:n_train]
        pf_test = all_padded[n_train:]
        pm_test = all_masks[n_train:]

        train_ids, val_ids = train_val(n_train, argsP)

        def _subset(lst, ids):
            return [lst[i] for i in ids]

        def _subset_tensor(t, ids):
            return t[ids]

        emb_val = _subset_tensor(emb_train_cat, val_ids)
        emb_train = _subset_tensor(emb_train_cat, train_ids)

        costs_val = _subset(costs_train_all, val_ids)
        costs_train = _subset(costs_train_all, train_ids)

        pf_val = _subset(pf_train_all, val_ids)
        pf_train = _subset(pf_train_all, train_ids)

        pm_val = _subset(pm_train_all, val_ids)
        pm_train = _subset(pm_train_all, train_ids)

        njc_val = _subset(njc_train_all, val_ids)
        njc_train = _subset(njc_train_all, train_ids)

        nfo_val = _subset(nfo_train_all, val_ids)
        nfo_train = _subset(nfo_train_all, train_ids)

        ntb_val = _subset(ntb_train_all, val_ids)
        ntb_train = _subset(ntb_train_all, train_ids)

        nfc_val = _subset(nfc_train_all, val_ids)
        nfc_train = _subset(nfc_train_all, train_ids)

        njc_test = n_join_cols_test
        nfo_test = n_fanouts_test
        ntb_test = n_tables_test
        nfc_test = n_filter_cols_test
        emb_test = embeddings_test

    # Store max dims on argsP for model construction
    argsP.price_max_n_join_col = max_njc
    argsP.price_max_n_fanout = max_nfo
    argsP.price_max_n_table = max_ntb
    argsP.price_max_n_filter_col = max_nfc
    argsP.embed_size = llm_embed_size
    print(f"[FrozenLLM+PRICE] Model dims: n_join_col={max_njc}, n_fanout={max_nfo}, n_table={max_ntb}, n_filter_col={max_nfc}, llm_dim={llm_embed_size}", flush=True)

    # ---- Step 5: Normalize labels and create datasets ----
    print(f"[FrozenLLM+PRICE] Step 5: Creating datasets (train={len(emb_train)}, val={len(emb_val)}, test={len(emb_test)})...", flush=True)
    update_ds_info_minmax(ds_info, costs_train + costs_val + costs_test,
                          costs_train + costs_val + costs_test)
    prepare_ds_info_norm(ds_info)

    if not argsP.card:
        ytr = ds_info.cost_norm.normalize_labels(costs_train)
        yva = ds_info.cost_norm.normalize_labels(costs_val)
        yte = ds_info.cost_norm.normalize_labels(costs_test)
    else:
        ytr = ds_info.card_norm.normalize_labels(costs_train)
        yva = ds_info.card_norm.normalize_labels(costs_val)
        yte = ds_info.card_norm.normalize_labels(costs_test)

    ds_train = FrozenLLMPriceDataset(emb_train, pf_train, pm_train,
                                     njc_train, nfo_train, ntb_train, nfc_train, ytr)
    ds_val = FrozenLLMPriceDataset(emb_val, pf_val, pm_val,
                                   njc_val, nfo_val, ntb_val, nfc_val, yva)
    ds_test = FrozenLLMPriceDataset(emb_test, pf_test, pm_test,
                                    njc_test, nfo_test, ntb_test, nfc_test, yte)

    return ds_train, ds_val, ds_test, costs_val, costs_test, lengths_test, templates_test