import pandas as pd
import numpy as np
import torch
from torch.utils.data import TensorDataset



def get_aimeetsai_feature(root, ds_info, node2id, dim, feature_mask=None):
#     final_feature = {}
#     dim = len(ds_info.nodeParallels)
    feature_mat = np.zeros((dim,5))
    
    # Prepare mask
    if feature_mask is None:
        mask_vec = np.ones(5)
    else:
        # Ensure mask is length 5 of 0/1 floats
        mask_vec = np.array(feature_mask, dtype=float)
        if mask_vec.shape[0] != 5:
            mask_vec = np.ones(5)

    def dfs(node):
        node_type = node.nodeParallel
        node_feat = np.zeros(5) ## numpy array so that can do +=
        
        cost = ds_info.cost_est_norm.normalize_label(node.cost_est)
        card = ds_info.card_norm.normalize_label(node.card_est)
        byte = cost * node.width
        
        node_feat[0] = cost     
        node_feat[1] = card
        node_feat[3] = byte
        
        wei_costs = 0
        wei_rows = 0
        
        if node.children:
            height = 9999
            for child in node.children:
                ch_height, leaf_wei_rows, leaf_wei_costs = dfs(child)
                height = min(height, ch_height)
                
                wei_rows += leaf_wei_rows
                wei_costs += leaf_wei_costs
                
            height += 1
        else:
            height = 1
#         print(height)
        wei_rows += height * card
        node_feat[2] = wei_rows
        
        wei_costs += height * cost
        node_feat[4] = wei_costs
        
        # apply mask before aggregating
        feature_mat[node2id[node_type]] += (node_feat * mask_vec)
#         if node_type not in final_feature:
#             final_feature[node_type] = node_feat
#         else:
#             final_feature[node_type] += node_feat
            
            
        return height, wei_rows, wei_costs
    
    dfs(root)
    return feature_mat.reshape(-1)


def get_aimeetsai_ds(ds_info, roots, costs, args):
    node2id = dict(zip(ds_info.nodeParallels,range(len(ds_info.nodeParallels))))
    dim = len(ds_info.nodeParallels)
    features = []
    # parse mask from args.aime_features (string like "10110")
    mask = None
    if hasattr(args, 'aime_features') and isinstance(args.aime_features, str):
        s = args.aime_features.strip()
        if len(s) == 5 and set(s).issubset({'0', '1'}):
            mask = [int(ch) for ch in s]
    for root in roots:
        features.append(get_aimeetsai_feature(root, ds_info, node2id, dim, feature_mask=mask))
    features = torch.FloatTensor(features)
    if not args.card:
        costs = torch.FloatTensor(ds_info.cost_norm.normalize_labels(costs)).view(-1,1)
    else:
        costs = torch.FloatTensor(ds_info.card_norm.normalize_labels(costs)).view(-1,1)
    return TensorDataset(features, costs)