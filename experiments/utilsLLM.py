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
        if "gpt2" in model_name:
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
        elif "bert" in model_name.lower():
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
        elif "google/" in model_name.lower() or "gemma" in model_name.lower():
            return self._load_google_model(model_name, quantification, offload_folder,
                                         use_lora, lora_r, lora_alpha, lora_dropout, target_modules)
        else:
            raise ValueError(f"Unsupported model type: {model_name}")

    def _infer_hidden_dim(self, model) -> int:
        """
        Robustly infer the model's hidden/embedding dimension across different architectures.
        Tries common config fields, then input embedding size, then text_config fallback.
        """
        cfg = getattr(model, 'config', None)
        # Try common config attributes
        for attr in [
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
        
        # Report max input length
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
                torch_dtype=torch.float16,
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
                torch_dtype=torch.float16,
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
            target_modules=target_modules or ["query", "value"],
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
            self.model.gradient_checkpointing_enable()
            print("Gradient checkpointing enabled")
        if mode == "lora":
            # Only prepare for kbit training if quantization is used
            if quantification != "None":
                self.model = prepare_model_for_kbit_training(self.model)
            # LoRA configuration for sentence-transformers models (typically BERT-based)
            lora_config = LoraConfig(
                r=lora_r,
                lora_alpha=lora_alpha,
                target_modules=target_modules or ["query", "value"],
                lora_dropout=lora_dropout,
                bias="none",
                task_type=TaskType.FEATURE_EXTRACTION,
            )
            self.model = get_peft_model(self.model, lora_config)
        return self.model
    
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
        
        # Only apply LoRA if requested and not in inference mode
        if use_lora and self.mode != "inference":
            # Only prepare for kbit training if quantization is used
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
        else:
            return model
    
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
        
        # 批量处理所有窗口
        if all_windows:
            embeddings = self._process_batch_optimized(all_windows, max_length)
            
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

    def _process_batch_optimized(self, windows: list, max_length: int) -> torch.Tensor:
        """批量处理函数，直接处理token ids或文本"""
        # Handle DDP models by accessing the underlying model
        model_to_check = self.model.module if hasattr(self.model, 'module') else self.model
        
        is_qwen = "qwen" in model_to_check.config.model_type.lower() if hasattr(model_to_check.config, 'model_type') else False
        is_bert = "bert" in model_to_check.config.model_type.lower() if hasattr(model_to_check.config, 'model_type') else False
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
        
        # 批量前向传播
        if is_gpt_oss:
            outputs = self.model(**inputs, output_hidden_states=True)
            hs = outputs.hidden_states[-1]
        elif is_qwen:
            outputs = self.model(**inputs)
        elif is_google:
            with torch.amp.autocast('cuda', enabled=True, dtype=torch.float16):
                outputs = self.model(**inputs, output_hidden_states=True)
                hs = outputs.hidden_states[-1]
                # f = open("log.txt", "a")
                # print(f"hs: {hs}", file=f)
                # f.close()
        else:
            with torch.amp.autocast('cuda', enabled=True):
                outputs = self.model(**inputs, output_hidden_states=True)
                if (is_qwen or is_bert) and hasattr(outputs, 'last_hidden_state'):
                    hs = outputs.last_hidden_state
                else:
                    hs = outputs.hidden_states[-1]
        
        # 批量池化
        if is_qwen:
            embs = self.last_token_pool(outputs.last_hidden_state, inputs['attention_mask'])
            embs = torch.nn.functional.normalize(embs, p=2, dim=1)
            return embs
        elif is_bert:
            embs = []
            for i in range(hs.shape[0]):
                emb = self.get_cls_token(hs[i:i+1])
                emb = torch.nn.functional.normalize(emb, p=2, dim=1)
                embs.append(emb.squeeze(0))
            return torch.stack(embs, dim=0)
        elif is_google:
            # For Google Gemma models, use mean pooling similar to other transformer models
            mask = inputs["attention_mask"].unsqueeze(-1)
            hs_masked = hs * mask
            sum_hs = hs_masked.sum(dim=1)
            lens = mask.sum(dim=1).clamp(min=1)
            embs = sum_hs / lens
            return embs
        else:
            # 批量mean pooling
            mask = inputs["attention_mask"].unsqueeze(-1)
            hs_masked = hs * mask
            sum_hs = hs_masked.sum(dim=1)
            lens = mask.sum(dim=1).clamp(min=1)
            embs = sum_hs / lens
            return embs

    def forward(self, texts: list[str]):
        """
        Forward pass using optimized implementation from BasePredictor.
        """
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
            generated = self.model(**inputs, output_hidden_states=True)
            hs = generated.hidden_states[-1]
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
        return self._process_batch_optimized(texts, max_length)
    
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

def _find_actual_total_time(root_node):
    if "Actual Total Time" not in root_node:
        raise KeyError("'Actual Total Time' not found in root")
    return float(root_node["Actual Total Time"])


def _find_actual_rows(root_node):
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


def _clean_node(obj, fields_to_remove=None):
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
    
    Returns:
        Cleaned object
    """
    if fields_to_remove is None:
        fields_to_remove = set()
    
    # Always remove runtime category fields
    runtime_fields = FIELD_CATEGORIES['runtime']
    all_fields_to_remove = fields_to_remove | runtime_fields
    
    if isinstance(obj, dict):
        cleaned = {}
        for k, v in obj.items():
            # Remove fields based on category selection (including runtime)
            if k in all_fields_to_remove:
                continue
            # Recursively clean the value
            cleaned[k] = _clean_node(v, fields_to_remove)
        return cleaned
    elif isinstance(obj, list):
        return [_clean_node(item, fields_to_remove) for item in obj]
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

def _collect_column_ids_and_replace(node, stats, replace_type="all"):
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
    cleaned_texts = []
    costs = []
    cards = []
    lengths = []
    templates = []
    
    # Parse removed_fields for ablation studies
    fields_to_remove = set()
    if hasattr(argsP, 'removed_fields') and argsP.removed_fields:
        removed_categories = [cat.strip() for cat in argsP.removed_fields.split(',')]
        fields_to_remove = get_fields_to_remove(removed_categories)
        if fields_to_remove:
            print(f"  Removing {len(fields_to_remove)} fields from categories: {removed_categories}")
    
    # Check if template column exists (only for tpch and tpcds)
    has_template = 'template' in df.columns

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
        costs.append(_find_actual_total_time(orig_root))
        cards.append(_find_actual_rows(orig_root))
        cleaned_root = _clean_node(root, fields_to_remove)
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

        used_column_ids = _collect_column_ids_and_replace(cleaned_plan, original_data["database_stats"]["column_stats"])
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
    cache_dir = "embeddings"
    if "_rm-" in removed_fields_suffix:
        cache_dir = "embeddings_rm"
    
    cache_file = f"embeddings_{argsP.model_name}_bucketize-{argsP.bucketize_input}_quant-{argsP.quantification}_pretrained-{argsP.llm_pretrained}_pretrainedTask-{argsP.llm_pretrained_task}{target_suffix}{seed_suffix}{removed_fields_suffix}_{dat_path}".replace("json", "csv") 
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

    if normalize_feats:
        feat_norm = FeatureNormalizer()
        features = feat_norm.fit_transform(features)

    # Return: always return 4 values
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
        embeddings_test, costs_test, lengths_test, templates_test = get_embeddings(predictor, ds_info, dat_path_test, argsP, 1, False, collect_test_info=argsP.verbose_info)
        
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
                embeddings, costs, lengths, templates = get_embeddings(predictor, ds_info, dat_path_train, argsP, 1, False, collect_test_info=False)
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