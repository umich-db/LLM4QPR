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
sys.path.append('../evaluation/')
from feature_extractor import DatasetInfo
from dataset_utils import *
from algorithms.queryformer import *
from algorithms.queryformer.dataset_utils import *
from algorithms.queryformer.model import *
from algorithms.aimeetsai import *
from time import time as timer

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', type=str, choices=['mysql', 'postgres'], required=True, help='Target database type')
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
    parser.add_argument("--llm_mode", type=str, default="inference")
    parser.add_argument("--workloads_train", nargs="+", default=["tpcds", "tpch", "syn", "job", "stats"], help="one or more workloads to train on")
    parser.add_argument("--dat_paths_train", nargs="+", default=["../data/imdb/postgres/"], help="one or more data paths to train on")

    # added bucketize_input flag
    parser.add_argument("--bucketize_input", action="store_true", default=False,
                        help="If set, bucketize the input data.")
    parser.add_argument("--embeddings_exist", action="store_true", default=False)
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility')
    return parser.parse_args()


def setup_loggers(main_log_path, inf_log_path):
    # 1) Inference‐only logger
    inference_logger = logging.getLogger("inference_logger")
    inference_logger.setLevel(logging.INFO)
    inference_logger.propagate = False
    inf_handler = logging.FileHandler(inf_log_path, mode="a")  # append mode
    inf_fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    inf_handler.setFormatter(inf_fmt)
    inference_logger.addHandler(inf_handler)

    # 2) Main‐only logger
    main_logger = logging.getLogger("main_logger")
    main_logger.setLevel(logging.INFO)
    main_logger.propagate = False
    main_handler = logging.FileHandler(main_log_path, mode="w")  # overwrite each run
    main_fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    main_handler.setFormatter(main_fmt)
    main_logger.addHandler(main_handler)

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
        if wl_train == "syn" or wl_train == "job":
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
        if wl_test == "syn" or wl_test == "job":
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
        elif wl_test == "stats":
            dat_path_test = f"{dp_test}long_raw_{argsP.db}_{wl_test}_statsCEB_sub.csv"
        else:
            print("Only syn/job/stats workloads are supported for card")
            exit(1)
    # skipped above
    if "llm" in argsP.algo:
        dat_dict = {"ds_info": DatasetInfo({}), "train_js_nodes": None, "train_roots": None, "train_costs": None, "val_js_nodes": None, "val_roots": None, "val_costs": None, "test_js_nodes": None, "test_roots": None, "test_costs": None, "test_ids": None, "val_ids": None, "train_ids": None}
    else:
        print("running get_new")
        dat_dict = get_new(argsP, dp_test ,dat_paths_train_list, dat_path_test)
        print("done running get_new")
    return dat_paths_train_list, dat_path_test, dat_dict

def load_data(argsP, args, dat_path, dat_paths_train_list, dat_path_test, dat_dict, predictor=None, llm_collate=None):
    ds_info = dat_dict['ds_info']

    train_js_nodes = dat_dict['train_js_nodes']
    train_roots = dat_dict['train_roots']
    train_costs = dat_dict['train_costs']

    val_js_nodes = dat_dict['val_js_nodes']
    val_roots = dat_dict['val_roots']
    val_costs = dat_dict['val_costs']

    test_js_nodes = dat_dict['test_js_nodes']
    test_roots = dat_dict['test_roots']
    test_costs = dat_dict['test_costs']

    if argsP.algo == "qf":
        encoding = Encoding(ds_info)
        hist_file = get_hist_file(dat_path + 'histogram_string.csv')
        table_sample = get_job_table_sample(dat_path + 'long_df')
        
        if argsP.workload_test == "syn" or argsP.workload_test == "job" or argsP.workload_test == "tpch" or argsP.workload_test == "stats":
            max_node = 35
        elif argsP.workload_test == "tpcds":
            max_node = 120
        transform_start = timer()
        ds = QueryFormerDataset(hist_file = hist_file, table_sample = table_sample, \
                                nodes=train_roots, encoding=encoding, labels=train_costs, ds_info=ds_info, max_node=max_node, argsP=argsP)
        transform_time = timer() - transform_start
        argsP.inference_logger.info(f"[Transform] QueryFormer training dataset creation took {transform_time*1000:.2f} ms")

        val_ds = QueryFormerDataset(hist_file = hist_file, table_sample = table_sample, \
                                    nodes=val_roots, encoding=encoding, labels=val_costs, ds_info=ds_info, max_node=max_node, argsP=argsP)
        
        transform_start = timer()
        test_ds = QueryFormerDataset(hist_file = hist_file, table_sample = table_sample, \
                                    nodes=test_roots, encoding=encoding, labels=test_costs, ds_info=ds_info, max_node=max_node, argsP=argsP)
        transform_time = timer() - transform_start
        argsP.inference_logger.info(f"[Transform] QueryFormer testing dataset creation took {transform_time*1000:.2f} ms")

        train_loader = DataLoader(dataset=ds,
                                batch_size = args.bs,
                                collate_fn=collator,
                                shuffle=True,
                                generator=torch.Generator().manual_seed(argsP.seed if hasattr(argsP, 'seed') else 42))
        val_loader = DataLoader(dataset=val_ds,
                                batch_size = args.bs,
                                collate_fn=collator,
                                shuffle=False)
        test_loader = DataLoader(dataset=test_ds,
                                batch_size = 1,
                                # batch_size = args.bs,
                                collate_fn=collator,
                                shuffle=False)
    elif argsP.algo == "aimai" or argsP.algo == "llm":
        if argsP.algo == "aimai":
            transform_start = timer()
            ds = get_aimeetsai_ds(ds_info, train_roots, train_costs, argsP)
            transform_time = timer() - transform_start
            argsP.inference_logger.info(f"[Transform] AiMeetsAi training dataset creation took {transform_time*1000:.2f} ms")
            
            val_ds = get_aimeetsai_ds(ds_info, val_roots, val_costs, argsP)
            
            transform_start = timer()
            test_ds = get_aimeetsai_ds(ds_info, test_roots, test_costs, argsP)
            transform_time = timer() - transform_start
            argsP.inference_logger.info(f"[Transform] AiMeetsAi testing dataset creation took {transform_time*1000:.2f} ms")
        elif argsP.algo == "llm":
            from utilsLLM import QueryPlanDataset, QueryPlanPredictor, get_llm_ds_from_csv
            ds, val_ds, test_ds, val_costs, test_costs, test_lengths, test_templates = get_llm_ds_from_csv(predictor, dat_paths_train_list, dat_path_test, ds_info, argsP)
            if not argsP.embeddings_exist:
                predictor.to("cpu")
            torch.cuda.empty_cache()

        train_loader = DataLoader(dataset=ds,
                                batch_size = args.bs,
                                shuffle=True,
                                generator=torch.Generator().manual_seed(argsP.seed if hasattr(argsP, 'seed') else 42))
        val_loader = DataLoader(dataset=val_ds,
                                batch_size = args.bs,
                                shuffle=False)
        test_loader = DataLoader(dataset=test_ds,
                                batch_size = 1,
                                shuffle=False)
    elif argsP.algo == "llm_finetune":
        from utilsLLM import QueryPlanDataset, QueryPlanPredictor, get_llm_ds_from_csv
        ds, val_ds, test_ds, val_costs, test_costs, test_lengths, test_templates = get_llm_ds_from_csv(predictor, dat_paths_train_list, dat_path_test, ds_info, argsP)
        train_loader = DataLoader(dataset=ds,
                                batch_size = args.bs,
                                shuffle=True,
                                collate_fn=llm_collate,
                                generator=torch.Generator().manual_seed(argsP.seed if hasattr(argsP, 'seed') else 42))
        val_loader = DataLoader(dataset=val_ds,
                                batch_size = args.bs,
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
           (test_templates if "llm" in argsP.algo else None)    
    

    return ds_info, train_roots, train_js_nodes, train_costs, \
           val_roots,   val_js_nodes,   val_costs,   \
           test_roots,  test_js_nodes,  test_costs,  \
           ds,  val_ds,  test_ds,  \
           train_loader,  val_loader,  test_loader,  \
           (test_lengths if "llm" in argsP.algo else None), \
           (test_templates if "llm" in argsP.algo else None)