import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from scipy.stats import pearsonr
import time
import os
import csv
import time
import logging

# main_logger = logging.getLogger(__name__)

# perf_counter gives you sub-microsecond resolution
timer = time.perf_counter



## cost prediction MLP model
class Prediction(nn.Module):
    def __init__(self, in_feature = 69, hid_units = 256, contract = 1, mid_layers = True, res_con = True):
        super(Prediction, self).__init__()
        self.mid_layers = mid_layers
        self.res_con = res_con
        
        self.out_mlp1 = nn.Linear(in_feature, hid_units)
        self.mid_mlp1 = nn.Linear(hid_units, hid_units//contract)
        self.mid_mlp2 = nn.Linear(hid_units//contract, hid_units)

        self.out_mlp2 = nn.Linear(hid_units, 1)

    def forward(self, features):
        # print(f"In trainer.py Prediction(), Shape of features: {features.shape}")

        if torch.isnan(features).any():
            print("NaN detected in trainer.py Prediction.features")
            for i, feature in enumerate(features):
                print(f"Feature entry {i}: {feature}")
            print(f"features: {features}")
            # To further isolate NaN values, print only the specific positions where NaNs are located
            nan_positions = torch.isnan(features)
            print(f"NaN detected at positions: {nan_positions.nonzero()}")

        hid = F.relu(self.out_mlp1(features))
        if torch.isnan(hid).any():
            print("NaN detected after first ReLU")

        if self.mid_layers:
            mid = F.relu(self.mid_mlp1(hid))
            if torch.isnan(mid).any():
                print("NaN detected after second ReLU")

            mid = F.relu(self.mid_mlp2(mid))
            if torch.isnan(mid).any():
                print("NaN detected after third ReLU")

            if self.res_con:
                hid = hid + mid
            else:
                hid = mid

        out = torch.sigmoid(self.out_mlp2(hid))
        # out = self.out_mlp2(hid)
        # out = torch.clamp(out, min=0.001, max=1.0)
        if torch.isnan(out).any():
            print("NaN detected at output")

        return out


def print_qerror(ps, ls, prints=True,data_sec = "unknown"):
    ps = np.array(ps, dtype=float)
    ls = np.array(ls, dtype=float)

    # mask out any zeroes in ground truth or predictions
    mask = (ls != 0) & (ps != 0)
    p = ps[mask]
    l = ls[mask]

    # Q-error is max(p/l, l/p)
    q = np.maximum(p / l, l / p)

    # compute your stats
    e50   = np.median(q)
    e90   = np.percentile(q, 90)
    e99   = np.percentile(q, 99)
    emax  = np.max(q)
    emean = np.mean(q)

    if prints:
        print(f"Data section:       {data_sec}")
        print(f"Median:             {e50}")
        print(f"90th percentile:    {e90}")
        print(f"99th percentile:    {e99}")
        print(f"Max:                {emax}")
        print(f"Mean:               {emean}")

    return {
        'q_median': e50,
        'q_90':     e90,
        'q_99':     e99,
        'q_max':    emax,
        'q_mean':   emean,
    }



def get_abs_errors(ps, ls):
    # ensure NumPy arrays of floats
    ps = np.array(ps, dtype=float)
    ls = np.array(ls, dtype=float)

    # absolute differences for all points
    abs_diff = np.abs(ps - ls)

    # build mask: finite & nonzero
    finite_mask = np.isfinite(ps) & np.isfinite(ls)
    nonzero_mask = (ps != 0) & (ls != 0)
    mask = finite_mask & nonzero_mask

    # default fallbacks
    corr = log_corr = mre = np.nan

    # only compute these if we have at least 2 valid points
    if mask.sum() >= 2:
        p = ps[mask]
        l = ls[mask]

        # Pearson on raw values
        corr, _ = pearsonr(p, l)

        # Pearson on log-values
        log_corr, _ = pearsonr(np.log(p), np.log(l))

        # mean relative error
        relative_errors = np.abs(p - l) / np.abs(l)
        mre = np.mean(relative_errors)

    # assemble results
    res = {
        'rmse'      : np.sqrt((abs_diff**2).mean()),
        'corr'      : corr,
        'log_corr'  : log_corr,
        'mre'       : mre,
        'abs_median': np.median(abs_diff),
        'abs_90'    : np.percentile(abs_diff, 90),
        'abs_95'    : np.percentile(abs_diff, 95),
        'abs_99'    : np.percentile(abs_diff, 99),
        'abs_max'   : np.max(abs_diff),
    }
    return res

def get_qerror_distribution(ps, ls, save_path=None, drop_zeros=False):
    """
    Compute per-example Q-error: max(p/l, l/p).

    If drop_zeros=False, any pair where p==0 or l==0 becomes np.inf.
    If drop_zeros=True, those pairs are simply omitted from the returned array.
    """
    ps = np.asarray(ps, dtype=float)
    ls = np.asarray(ls, dtype=float)

    # mask non-finite inputs
    finite_mask = np.isfinite(ps) & np.isfinite(ls)
    p = ps[finite_mask]
    l = ls[finite_mask]

    # mask zeros
    zero_mask = (p == 0) | (l == 0)
    nonzero_mask = ~zero_mask

    # prepare an array to hold all q-errors
    if drop_zeros:
        # only non-zero, non-finite pairs
        p = p[nonzero_mask]
        l = l[nonzero_mask]
        q = np.maximum(p / l, l / p)
    else:
        # keep original order, zeros → inf
        q = np.empty_like(p)
        # fill zeros with inf
        q[zero_mask] = np.inf
        # compute on the rest
        q[nonzero_mask] = np.maximum(p[nonzero_mask] / l[nonzero_mask],
                                      l[nonzero_mask] / p[nonzero_mask])

    # optionally save
    if save_path:
        pd.DataFrame({'qerror': q}).to_csv(save_path, index=False)

    return q


def get_abs_error_distribution(ps, ls, save_path=None, drop_nonfinite=False):
    """
    Compute per-example absolute error: |p − l|.

    By default returns errors for all finite inputs. If drop_nonfinite=True,
    then any p or l that is NaN/Inf is dropped.
    """
    ps = np.asarray(ps, dtype=float)
    ls = np.asarray(ls, dtype=float)

    # compute raw abs diff
    abs_diff = np.abs(ps - ls)

    if drop_nonfinite:
        # only keep entries where both p and l are finite
        mask = np.isfinite(ps) & np.isfinite(ls)
        abs_diff = abs_diff[mask]

    # optionally save
    if save_path:
        pd.DataFrame({'abs_error': abs_diff}).to_csv(save_path, index=False)

    return abs_diff


def evaluate(model, args, loader, norm, device, prints=True, data_sec="unknown", 
            save_embeddings=False, test_embeddings=None, test_templates=None, 
            output_dir_qerror=None, workload_test=None):  
    """
    Run inference on `loader` and compute Q-error and absolute-error metrics.

    - `model`: a PyTorch model
    - `args.algo`: algorithm name, special-case 'llm_finetune' for input handling
    - `loader`: DataLoader yielding (x, y) pairs; y are normalized labels
    - `norm`: normalization object with unnormalize_labels()
    - `device`: torch device
    - `prints`: whether to print Q-error summary
    - `data_sec`: an optional label for reporting
    - `save_embeddings`: whether to save embeddings and labels
    - `test_embeddings`: embeddings for the test set (if available)
    - `test_templates`: templates for the test set (if available)
    - `output_dir_qerror`: output directory for saving files
    - `workload_test`: test workload name
    """
    print("evaluating")
    model.to(device)
    model.eval()

    preds_list = []
    labels_list = []
    embeddings_list = []

    with torch.no_grad():
        for x, y in loader:
            # Move inputs to device if not LLM finetuning
            if args.algo != "llm_finetune":
                x = x.to(device)
            
            # Store embeddings if requested
            if save_embeddings and test_embeddings is None:
                embeddings_list.append(x.cpu().numpy())
            
            # Forward pass
            preds = model(x).squeeze()
            # Collect predictions
            if isinstance(preds, torch.Tensor):
                preds_np = preds.cpu().numpy()
                preds_list_value = preds_np.tolist()
                if isinstance(preds_list_value, float):
                    preds_list.append(preds_list_value)
                else:
                    preds_list.extend(preds_list_value)
            else:
                preds_list.append(float(preds))
            # Collect true labels (assumed already on CPU)
            y_squeezed = y.squeeze()
            if isinstance(y_squeezed, torch.Tensor):
                y_np = y_squeezed.cpu().numpy()
                y_list_value = y_np.tolist()
                if isinstance(y_list_value, float):
                    labels_list.append(y_list_value)
                else:
                    labels_list.extend(y_list_value)
            else:
                labels_list.append(float(y_squeezed))

    # Convert to numpy arrays
    predss = np.array(preds_list, dtype=float).flatten()
    labelss = np.array(labels_list, dtype=float).flatten()

    # Un-normalize both predictions and labels
    preds_true = norm.unnormalize_labels(predss)
    labels_true = norm.unnormalize_labels(labelss)

    # Compute metrics
    q_errors      = print_qerror(preds_true, labels_true, prints, data_sec=data_sec)
    abs_errors    = get_abs_errors(preds_true, labels_true)
    q_errors_dist = get_qerror_distribution(preds_true, labels_true)
    abs_errors_dist = get_abs_error_distribution(preds_true, labels_true)

    print("evaluated")
    return q_errors, abs_errors, q_errors_dist, abs_errors_dist



def get_record(model, loader, labels, bs, norm, device):
    model.to(device)
    model.eval()
    predss = np.empty(0)

    with torch.no_grad():
        for x,y in loader:
            x = x.to(device)           
            preds = model(x).squeeze()
            predss = np.append(predss, preds.cpu().detach().numpy())
    predss = norm.unnormalize_labels(predss)
    predss = predss.tolist()
    return predss, labels

def collate_record(predss, labels, method, save_file):
    if os.path.isfile(save_file):
        df = pd.read_csv(save_file)
    else:
        df = pd.DataFrame(data={'label':labels})
    df[method] = predss
    df.to_csv(save_file,index=False)
    return df

def eval_record(model, loader, labels, bs, norm, device, save_path, method, dataset):
    model.to(device)
    model.eval()
    predss = np.empty(0)

    with torch.no_grad():
        for x,y in loader:
            x = x.to(device)           
            preds = model(x).squeeze()
            predss = np.append(predss, preds.cpu().detach().numpy())
    predss = norm.unnormalize_labels(predss)
    predss = predss.tolist()
    title = [method, dataset]
    title += predss
    file = open('results/cost/test_log.csv', 'a+', newline ='')
    with file:   
        write = csv.writer(file)
        write.writerow(title)
    file.close()



def Logging(args, epoch, qscores, absscores, time, filename = None, save_model = False, model = None):
    arg_keys = [attr for attr in dir(args) if not attr.startswith('__')]
    arg_vals = [getattr(args, attr) for attr in arg_keys]
    
    res = dict(zip(arg_keys, arg_vals))
    model_checkpoint = str(hash(tuple(arg_vals))) + '.pt'

    res['epoch'] = epoch
    res['model'] = model_checkpoint 


    res = {**res, **qscores, **absscores}
    
    res['time'] = time

    filename = args.save_path + filename
    model_checkpoint = args.save_path + model_checkpoint
    
    if filename is not None: ## append if exists
        if os.path.isfile(filename):
            df = pd.read_csv(filename)
            df = df._append(res, ignore_index=True)
            df.to_csv(filename, index=False)
        else:
            df = pd.DataFrame(res, index=[0])
            df.to_csv(filename, index=False)
    if save_model:
        torch.save({
            'model': model.state_dict(),
            'args' : args
        }, model_checkpoint)
    
    return res['model']  

def train(model, train_loader, val_loader, \
    ds_info, args, crit=None, optimizer=None, scheduler=None, prints=True, record=True):

    # Set random seeds for reproducibility
    if hasattr(args, 'seed'):
        np.random.seed(args.seed)

    bs, device, epochs = \
        args.batch_size, args.device, args.num_epoch
    lr = args.learning_rate

    if not optimizer:
        optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    if not scheduler:
        scheduler = torch.optim.lr_scheduler.StepLR(optimizer, 20, 0.9)
    if not crit:
        crit = torch.nn.MSELoss()

    t0 = time.time()

    best_prev = 999999

    model.to(device)
    
    for epoch in range(epochs):
        epoch_start = timer()
        model.train()
        losses = 0
        predss = np.empty(0)
        labels = np.empty(0)

        print(">", end="", flush=True)
        for batch_idx, (x, y) in enumerate(train_loader, start=1):
            print(".", end="", flush=True)
            batch_start = timer()
            if args.algo=='llm_finetune':
                y = y.to(device)
                print(batch_idx, end="", flush=True)
            else:
                x, y = x.to(device), y.to(device)
            optimizer.zero_grad()

            preds = model(x)
            loss = crit(preds, y)

            loss.backward()
            # loss.backward(retain_graph=True)

            torch.nn.utils.clip_grad_norm_(model.parameters(), 5)

            optimizer.step()
            losses += loss.item()
            predss = np.append(predss, preds.detach().cpu().numpy())

            labels = np.append(labels, y.detach().cpu().numpy())
            
            if torch.cuda.is_available():
                torch.cuda.synchronize()
            batch_time = timer() - batch_start
            args.main_logger.info(f"[Train] Epoch {epoch} Batch {batch_idx} — {batch_time*1000:.2f} ms")
        epoch_time = timer() - epoch_start
        args.main_logger.info(f"[Train] Epoch {epoch} total — {epoch_time*1000:.2f} ms")
        print("")

        if epoch % 20 == 0 and prints:
            print('Epoch: {}  Avg Loss: {}, Time: {}'.format(epoch,losses/len(predss), time.time()-t0))
            if not args.card:
                print_qerror(ds_info.cost_norm.unnormalize_labels(predss), ds_info.cost_norm.unnormalize_labels(labels),data_sec = "train")
            else:
                print_qerror(ds_info.card_norm.unnormalize_labels(predss), ds_info.card_norm.unnormalize_labels(labels),data_sec = "train")
        ##############
        if record:
            if epoch > 20:
                if not args.card:
                    _, _, _, _ = evaluate(model, args, val_loader, ds_info.cost_norm, device, prints=True,data_sec = "val")
                else:
                    _, _, _, _ = evaluate(model, args, val_loader, ds_info.card_norm, device, prints=True,data_sec = "val")

        ##############
        scheduler.step()   

    return model


import torch.nn.init as init
def initialize_weights(m):
    if isinstance(m, nn.Linear):
        # Initialize Linear layers with Glorot/Xavier initialization
        init.xavier_uniform_(m.weight)
        if m.bias is not None:
            init.constant_(m.bias, 0)
    elif isinstance(m, nn.Embedding):
        # Initialize embeddings differently based on their role
        if m.padding_idx is None:
            # Non-padded embedding initialization
            init.uniform_(m.weight, -0.1, 0.1)
        else:
            # Padded embeddings might need zero for the padding index
            init.uniform_(m.weight, -0.1, 0.1)
            if m.padding_idx is not None:
                m.weight.data[m.padding_idx].zero_()
    elif isinstance(m, nn.LayerNorm):
        # Initialize Layer Normalization with constant weights and biases
        init.constant_(m.weight, 1)
        init.constant_(m.bias, 0)
    elif isinstance(m, nn.Dropout):
        # Dropout layers do not have weights and do not require initialization
        pass
    # Check if EncoderLayer or similar structures have parameters and initialize them
    elif hasattr(m, 'parameters'):
        for p in m.parameters():
            if p.dim() > 1: # Assume it's a weight matrix and not a bias vector
                init.xavier_uniform_(p)
    else:
        print("unknown model type")

# For checking NaN in model weights
def print_weights_and_check_nan(model, name="Model"):
    print(f"--- {name} Weights ---")
    for param_name, param in model.named_parameters():
        if param.requires_grad:
            print(f"{param_name}: Mean of weights = {param.data.mean().item()}")
            if torch.isnan(param.data).any():
                print(f"Warning: NaN values detected in {param_name}")
                return True
            else:
                print(f"{param_name} has no NaN values.")
                return False

# For checking NaN in data
def check_data_for_nans(loader, name):
    for i, (batch_data, labels) in enumerate(loader):
        if torch.isnan(batch_data.x).any():
            print(f"NaN detected in input features of {name} loader, batch {i}")
        if torch.isnan(labels).any():
            print(f"NaN detected in labels of {name} loader, batch {i}")

def check_batch_for_nans(batch):
    has_nan = False
    for attr in ['x', 'attn_bias', 'rel_pos', 'heights']:
        if hasattr(batch, attr):
            tensor = getattr(batch, attr)
            if torch.isnan(tensor).any():
                print(f"NaN detected in {attr}")
                has_nan = True
    return has_nan

def train_and_test_bao(train_roots, train_costs, test_roots, test_costs, args, device):
    """
    Train and test the BaoRegression model. Returns metrics and predictions.
    """
    from algorithms.bao.model import BaoRegression
    from algorithms.bao.featurize import collate as bao_collate
    import time

    bao = BaoRegression(have_cache_data=True, verbose=True)
    # Training
    training_start = time.time()
    bao.fit(train_roots, train_costs, args)
    training_time = time.time() - training_start
    args.main_logger.info(f"[Train] Training took {training_time*1000:.2f} ms")

    # Testing
    test_start = time.time()
    preds_test = []
    for root in test_roots:
        featurized = bao._BaoRegression__tree_transform.transform([root])
        batch, _ = bao_collate(list(zip(featurized, [0.0])))
        batch = batch.to(device)
        with torch.no_grad():
            raw_pred = bao._BaoRegression__net(batch)
            raw_np   = raw_pred.cpu().numpy()
        final_pred = bao._BaoRegression__pipeline.inverse_transform(raw_np)
        preds_test.append(final_pred[0,0])
    test_time = time.time() - test_start
    args.main_logger.info(f"[Test] Testing took {test_time*1000:.2f} ms")

    qerr = print_qerror(preds_test, test_costs)
    abserr = get_abs_errors(preds_test, test_costs)
    qerr_dist = get_qerror_distribution(preds_test, test_costs)
    abserr_dist = get_abs_error_distribution(preds_test, test_costs)
    return {
        'qerr': qerr,
        'abserr': abserr,
        'qerr_dist': qerr_dist,
        'abserr_dist': abserr_dist,
        'preds_test': preds_test,
        'training_time': training_time,
        'test_time': test_time,
    }

def train_and_test_postgres(train_roots, train_costs, test_roots, test_costs, args):
    """
    Train and test the PostgresEstimator model. Returns metrics and predictions.
    """
    from algorithms.postgres import PostgresEstimator
    import time

    pg = PostgresEstimator()
    if args.card:
        preds = pg.predict_card(test_roots)
        true_vals = test_costs
        label_name = "cardinality"
    else:
        pg.fit(train_roots, train_costs)
        preds = pg.predict_time(test_roots)
        true_vals = test_costs
        label_name = "time"

    qerr = print_qerror(preds, true_vals, True, data_sec=f"test")
    abserr = get_abs_errors(preds, true_vals)
    qerr_dist = get_qerror_distribution(preds, true_vals)
    abserr_dist = get_abs_error_distribution(preds, true_vals)
    return {
        'qerr': qerr,
        'abserr': abserr,
        'qerr_dist': qerr_dist,
        'abserr_dist': abserr_dist,
        'preds': preds,
    }