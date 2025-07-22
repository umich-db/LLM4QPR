import os
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
sys.path.append('../evaluation/')
from dataset_utils import *
from time import time as timer
import numpy as np
import csv

argsP = utilsTrain.parse_args()
log_dir = os.path.dirname(argsP.log_file)
os.makedirs(log_dir, exist_ok=True)
main_logger, inference_logger = utilsTrain.setup_loggers(argsP.log_file, argsP.log_file.replace(".log", "_inference.log"))
argsP.inference_logger = inference_logger

hf_token = "XXX"
try:
    # Avoid logging in again if already authenticated
    HfApi().whoami()
except:
    login(hf_token)


db = argsP.db
dat_path = argsP.dat_path_test
dat_paths_train_list, dat_path_test, dat_dict = utilsTrain.prepare_paths(argsP)

if argsP.algo != "llm_finetune":
    output_dir = os.path.dirname(argsP.output_dir_qerror)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
# Print CUDA availability (optional, for verification)
print(f"Cuda available? {torch.cuda.is_available()}")
if "llm" in argsP.algo:
  if not argsP.embeddings_exist:
    from utilsLLM import QueryPlanDataset, QueryPlanPredictor, get_llm_ds_from_csv
    
    LLM = QueryPlanPredictor(argsP.model_name,argsP.llm_mode)
    device = LLM.model.device if hasattr(LLM.model, 'device') else torch.device("cuda" if torch.cuda.is_available() else "cpu")
    LLM.to(device)
    if argsP.algo == "llm" and argsP.llm_pretrained:
      llm_path = f"best_model/{'-'.join(argsP.workloads_train)}_{argsP.llm_pretrained_task}_{argsP.llm_pretrained}_{argsP.model_name.replace('/','-')}_llm.pt"
      state_dict = torch.load(llm_path, map_location=device)
      LLM.model.load_state_dict(state_dict, strict=False)
      print(f"✅  Loaded LLM weights from {llm_path}")
  else:
    LLM = None


# seed = 0
seed = argsP.seed
torch.manual_seed(seed)
torch.cuda.manual_seed_all(seed)
torch.backends.cudnn.deterministic = True 
torch.backends.cudnn.benchmark = False
class Args:
    #device = 'cuda:0'
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    bs = argsP.batch_size
    epochs = argsP.num_epoch # 200
    lr = argsP.learning_rate # Originally 1e-3
    save_path = "best_model/"
    hid_units = argsP.hid_units
    algo = argsP.algo
    log_file = argsP.log_file
    card = argsP.card
    main_logger = main_logger
    seed = argsP.seed

args = Args()
import os
save_path = args.save_path 
if not os.path.exists(save_path):
    os.makedirs(save_path)

device = args.device
def llm_collate(batch):
    # batch is a list of tuples: [(text1, cost1), (text2, cost2), …]
    texts, costs = zip(*batch)                      # two tuples of length B
    # turn costs into a FloatTensor of shape (B,1)
    costs_tensor = torch.tensor(costs, 
                                dtype=torch.float32,
                                device=device).unsqueeze(1)
    # leave texts as a plain Python list of str
    return list(texts), costs_tensor

if "llm" in argsP.algo:
  ds_info, train_roots, train_js_nodes, train_costs, \
            val_roots,   val_js_nodes,   val_costs,   \
            test_roots,  test_js_nodes,  test_costs,  \
            ds,  val_ds,  test_ds,  \
            train_loader,  val_loader,  test_loader,  \
            test_lengths, test_templates = utilsTrain.load_data(argsP, args, dat_path, dat_paths_train_list, dat_path_test, dat_dict, LLM, llm_collate)
else:
  ds_info, train_roots, train_js_nodes, train_costs, \
            val_roots,   val_js_nodes,   val_costs,   \
            test_roots,  test_js_nodes,  test_costs,  \
            ds,  val_ds,  test_ds,  \
            train_loader,  val_loader,  test_loader,  \
            test_lengths, test_templates = utilsTrain.load_data(argsP, args, dat_path, dat_paths_train_list, dat_path_test, dat_dict)

from trainer import *

if argsP.algo == "bao":
  results = train_and_test_bao(train_roots, train_costs, test_roots, test_costs, argsP, device)
  save_error_cdf(results['qerr_dist'], argsP.output_dir_qerror, error_type="Qerror")
  save_error_cdf(results['abserr_dist'], argsP.output_dir_abs,   error_type="abs_error")
  sys.exit(0)
elif argsP.algo == "postgres":
  results = train_and_test_postgres(train_roots, train_costs, test_roots, test_costs, argsP)
  save_error_cdf(results['qerr_dist'], argsP.output_dir_qerror, error_type="Qerror")
  save_error_cdf(results['abserr_dist'], argsP.output_dir_abs,   error_type="abs_error")
  sys.exit(0)



if argsP.algo == "aimai":
  input_dim = len(ds_info.nodeParallels) * 5
  MLP = Prediction(input_dim, args.hid_units)
  model_comb = MLP
elif argsP.algo == "qf":
  from algorithms.queryformer.model import *
  model = QueryFormer(emb_size=64, use_sample = True, use_hist = True)
  input_dim = 393
  MLP = Prediction(input_dim, args.hid_units)
  model_comb = nn.Sequential(model, MLP)
elif argsP.algo == "llm":
  print(f"embedding size: {argsP.embed_size}")
  input_dim = argsP.embed_size
  MLP = Prediction(input_dim, args.hid_units)
  model_comb = MLP
elif argsP.algo == "llm_finetune":
  print(f"embedding size: {argsP.embed_size}")
  input_dim = argsP.embed_size
  MLP = Prediction(input_dim, args.hid_units)
  model_comb = nn.Sequential(LLM, MLP)
# originally 64
# prediction = Prediction(393) #197, 393
# model_comb = nn.Sequential(model, prediction)


crit = nn.MSELoss()
training_start = timer()
best_model, best_model_path = train(model_comb, train_loader, val_loader, ds_info, args, crit=crit)
training_time = timer() - training_start
args.main_logger.info(f"[Final] Training total — {training_time*1000:.2f} ms")

if argsP.algo == "llm_finetune":
    save_dir = os.path.dirname(args.save_path)
    if save_dir and not os.path.exists(save_dir):
        os.makedirs(save_dir, exist_ok=True)

    llm_sd = LLM.model.state_dict()

    if argsP.card:
        llm_out = os.path.join(save_dir, f"{'-'.join(argsP.workloads_train)}_card_{argsP.llm_mode}_{argsP.model_name.replace('/','-')}_llm.pt")
    else:
        llm_out = os.path.join(save_dir, f"{'-'.join(argsP.workloads_train)}_time_{argsP.llm_mode}_{argsP.model_name.replace('/','-')}_llm.pt")
    torch.save(llm_sd, llm_out)
    print(f"🔖  Saved LLM weights to {llm_out}")
else:
  # Log testing time for all other algorithms
  test_start = timer()
  if not argsP.card:
    q_errors, abs_errors, q_errors_dist, abs_errors_dist = evaluate(best_model, args, test_loader, ds_info.cost_norm, args.device, data_sec="test",
                                                                    save_embeddings=(argsP.workload_test in ["tpch", "tpcds"] and test_templates is not None),
                                                                    test_embeddings=(test_ds.tensors[0].cpu().numpy() if argsP.algo == "llm" and hasattr(test_ds, 'tensors') else None),
                                                                    test_templates=test_templates,
                                                                    output_dir_qerror=argsP.output_dir_qerror,
                                                                    workload_test=argsP.workload_test)
  else:
    q_errors, abs_errors, q_errors_dist, abs_errors_dist = evaluate(best_model, args, test_loader, ds_info.card_norm, args.device, data_sec="test",
                                                                    save_embeddings=(argsP.workload_test in ["tpch", "tpcds"] and test_templates is not None),
                                                                    test_embeddings=(test_ds.tensors[0].cpu().numpy() if argsP.algo == "llm" and hasattr(test_ds, 'tensors') else None),
                                                                    test_templates=test_templates,
                                                                    output_dir_qerror=argsP.output_dir_qerror,
                                                                    workload_test=argsP.workload_test)
  test_time = timer() - test_start
  args.main_logger.info(f"[Test] Testing took {test_time*1000:.2f} ms")

  save_error_cdf(q_errors_dist, argsP.output_dir_qerror, error_type="Qerror")
  save_error_cdf(abs_errors_dist, argsP.output_dir_abs, error_type="abs_error")

  if argsP.algo == "llm":
    output_dir_lvq = argsP.output_dir_qerror.replace("cdf", "length_vs_qerror")
    with open(output_dir_lvq, "w") as f:
        w = csv.writer(f)
        w.writerow(["plan_length", "q_error"])
        for L, Q in zip(test_lengths, q_errors_dist):
            w.writerow([L, Q])

  print("\nTest Results:")
  print("Q Errors:", q_errors)
  print("Absolute Errors:", abs_errors)

