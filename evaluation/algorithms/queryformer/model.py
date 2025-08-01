import torch
from torch.utils.data import Dataset
import json
import pandas as pd
import torch.nn as nn
import torch.nn.functional as F

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
        # print(f"In model.py Prediction(), Shape of features: {features.shape}")
        
        if torch.isnan(features).any():
            print("NaN detected in features")
        
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
        if torch.isnan(out).any():
            print("NaN detected at output")

        return out


       
class FeatureEmbed(nn.Module):
    # max_filters = 10,3,or 23
    def __init__(self, embed_size=32, tables = 40, types=30, joins = 220, columns= 550, \
                 ops=10, use_sample = True, use_hist = True, bin_number = 50, max_filters = 23):
        super(FeatureEmbed, self).__init__()
        
        self.max_filters = max_filters

        self.use_sample = use_sample
        self.embed_size = embed_size        
        
        self.use_hist = use_hist
        self.bin_number = bin_number
        
        self.typeEmbed = nn.Embedding(types, embed_size)
        self.tableEmbed = nn.Embedding(tables, embed_size)
        
        self.columnEmbed = nn.Embedding(columns, embed_size)
        self.opEmbed = nn.Embedding(ops, embed_size//8)

        self.linearFilter2 = nn.Linear(embed_size+embed_size//8+1, embed_size+embed_size//8+1)
        self.linearFilter = nn.Linear(embed_size+embed_size//8+1, embed_size+embed_size//8+1)

        self.linearType = nn.Linear(embed_size, embed_size)
        
        self.linearJoin = nn.Linear(embed_size, embed_size)
        
        self.use_sample = use_sample
        self.use_hist = use_hist
        
        if use_sample:
            self.linearSample = nn.Linear(1000, embed_size)
        if use_hist:
            self.linearHist = nn.Linear(bin_number, embed_size)

        # self.joinEmbed = nn.Embedding(joins, embed_size)
        self.joinEmbed = nn.Embedding(300, embed_size)

        
        concat_size = embed_size*4 + embed_size//8 + 1 + \
            int(use_sample) * embed_size + int(use_hist) * embed_size
        self.project = nn.Linear(concat_size, concat_size)
#         if use_hist:
#             self.project = nn.Linear(embed_size*5 + embed_size//8+1, embed_size*5 + embed_size//8+1)
#         else:
#             self.project = nn.Linear(embed_size*4 + embed_size//8+1, embed_size*4 + embed_size//8+1)        
#         self.output_size = embed_size*4 + embed_size//8+1, embed_size*4 + embed_size//8+1
        self.output_size = concat_size
    
    # input: B by 14 (type, join, f1, f2, f3, mask1, mask2, mask3)
    def forward(self, feature):
#         print(feature.size())
        if self.use_hist and self.use_sample:
            typeId, joinId, filtersId, filtersMask, table, hists, sample = \
                torch.split(feature,(1,1,self.max_filters*3,self.max_filters, \
                                1, self.bin_number*self.max_filters,1000), dim = -1)
        elif self.use_hist:
            typeId, joinId, filtersId, filtersMask, table, hists = \
                torch.split(feature,(1,1,self.max_filters*3,self.max_filters, \
                                     1, self.bin_number*self.max_filters), dim = -1)
        elif self.use_sample:
            typeId, joinId, filtersId, filtersMask, table, sample = \
                torch.split(feature,(1,1,self.max_filters*3,self.max_filters, \
                                     1, 1000), dim = -1)        
        else:
            typeId, joinId, filtersId, filtersMask, table = \
                torch.split(feature,(1,1,self.max_filters*3,self.max_filters,1), dim = -1)
        
        
        typeEmb = self.getType(typeId)
        joinEmb = self.getJoin(joinId)
        filterEmbed = self.getFilter(filtersId, filtersMask)
        
        if self.use_hist:
            histEmb = self.getHist(hists, filtersMask)
        if self.use_sample:
            sampleEmb = self.linearSample(sample)
            
        tableEmb = self.getTable(table)
    
        if self.use_hist and self.use_sample:
            final = torch.cat((typeEmb, filterEmbed, joinEmb, tableEmb, histEmb, sampleEmb), dim = 1)
        elif self.use_hist:
            final = torch.cat((typeEmb, filterEmbed, joinEmb, tableEmb, histEmb), dim = 1)
        elif self.use_sample:
            final = torch.cat((typeEmb, filterEmbed, joinEmb, tableEmb, sampleEmb), dim = 1)
        else:
            final = torch.cat((typeEmb, filterEmbed, joinEmb, tableEmb), dim = 1)    
        final = F.leaky_relu(self.project(final))
        
        return final
    
    def getType(self, typeId):
        emb = self.typeEmbed(typeId.long())

        return emb.squeeze(1)
    
    def getTable(self, table_sample):
        # table, sample = torch.split(table_sample,(1,1000), dim = -1)
        emb = self.tableEmbed(table_sample.long()).squeeze(1)
        
        # if self.use_sample:
        #     emb += self.linearSample(sample)
        return emb
    
    def getJoin(self, joinId):
        # print("joinId before embedding:", joinId)

        # Check if joinId values exceed the embedding range
        max_index = self.joinEmbed.weight.size(0) - 1
        if joinId.max().item() > max_index:
            print(f"joinId.max().item(): {joinId.max().item()}")
            print(f"Warning: joinId contains values exceeding the embedding size. Max allowed index: {max_index}")

        emb = self.joinEmbed(joinId.long())

        return emb.squeeze(1)

    def getHist(self, hists, filtersMask):
        # batch * 50 * 3
        histExpand = hists.view(-1,self.bin_number,self.max_filters).transpose(1,2)
        
        emb = self.linearHist(histExpand)
        emb[~filtersMask.bool()] = 0.  # mask out space holder
        
        ## avg by # of filters
        num_filters = torch.sum(filtersMask,dim = 1)
        total = torch.sum(emb, dim = 1)
        avg = total / num_filters.view(-1,1)
        
        return avg
        
    def getFilter(self, filtersId, filtersMask):
        ## get Filters, then apply mask
        filterExpand = filtersId.view(-1,3, self.max_filters).transpose(1,2)
        colsId = filterExpand[:,:,0].long()
        opsId = filterExpand[:,:,1].long()
        vals = filterExpand[:,:,2].unsqueeze(-1) # b by 3 by 1
        
        # b by 3 by embed_dim
        
        col = self.columnEmbed(colsId)
        op = self.opEmbed(opsId)
        
        concat = torch.cat((col, op, vals), dim = -1)
        concat = F.leaky_relu(self.linearFilter(concat))
        concat = F.leaky_relu(self.linearFilter2(concat))
        
        ## apply mask
        concat[~filtersMask.bool()] = 0.
        
        ## avg by # of filters
        num_filters = torch.sum(filtersMask,dim = 1)
        total = torch.sum(concat, dim = 1)
        avg = total / num_filters.view(-1,1)
                
        return avg
    
#     def get_output_size(self):
#         size = self.embed_size * 5 + self.embed_size // 8 + 1
#         return size



class QueryFormer(nn.Module):
    def __init__(self, emb_size = 32 ,ffn_dim = 32, head_size = 8, \
                 dropout = 0.1, attention_dropout_rate = 0.1, n_layers = 8, \
                 use_sample = False, use_hist = False, bin_number = 50, \
                 pred_hid = 256, max_filters = 23, use_additional_feature=False):
        
        super(QueryFormer,self).__init__()

        self.max_filters = max_filters
        self.use_additional_feature = use_additional_feature

#         if use_hist:
#             hidden_dim = emb_size * 5 + emb_size //8 + 1
#         else:
#             hidden_dim = emb_size * 4 + emb_size //8 + 1

        hidden_dim = emb_size*4 + emb_size//8 + 1 + \
            int(use_sample) * emb_size + int(use_hist) * emb_size
    
        # if self.use_additional_feature:
        #     hidden_dim += 1  # Add this dimension for Top Model

        self.hidden_dim = hidden_dim
        self.head_size = head_size
        self.use_sample = use_sample
        self.use_hist = use_hist

        self.rel_pos_encoder = nn.Embedding(64, head_size, padding_idx=0)
        self.height_encoder = nn.Embedding(64, hidden_dim, padding_idx=0)
        
        self.input_dropout = nn.Dropout(dropout)
        
        # Pad hidden_dim by 1 for Top Model
        if self.use_additional_feature:
            encoders = [EncoderLayer(hidden_dim + 1, ffn_dim, dropout, attention_dropout_rate, head_size)
                        for _ in range(n_layers)]
            self.layers = nn.ModuleList(encoders)
            self.final_ln = nn.LayerNorm(hidden_dim + 1)
        else:
            encoders = [EncoderLayer(hidden_dim, ffn_dim, dropout, attention_dropout_rate, head_size)
                        for _ in range(n_layers)]
            self.layers = nn.ModuleList(encoders)
            self.final_ln = nn.LayerNorm(hidden_dim)

        self.super_token = nn.Embedding(1, hidden_dim)

        self.super_token_virtual_distance = nn.Embedding(1, head_size)
        
        self.embbed_layer = FeatureEmbed(emb_size, use_sample = use_sample, \
            use_hist = use_hist, bin_number = bin_number, max_filters = max_filters)

    # original forward
    def forward(self, batched_data):
        attn_bias, rel_pos, x = batched_data.attn_bias, batched_data.rel_pos, batched_data.x
        heights = batched_data.heights  
        additional_feature = batched_data.additional_feature  # Access additional_feature from the batch
        # print("x_size",x.size())
        n_batch, n_node = x.size()[:2]
        # print(f"Initial n_batch: {n_batch}, n_node: {n_node}")

        tree_attn_bias = attn_bias.clone()
        tree_attn_bias = tree_attn_bias.unsqueeze(1).repeat(1, self.head_size, 1, 1) 
        
        # rel pos
        rel_pos_bias = self.rel_pos_encoder(rel_pos).permute(0, 3, 1, 2) # [n_batch, n_node, n_node, n_head] -> [n_batch, n_head, n_node, n_node]
        tree_attn_bias[:, :, 1:, 1:] = tree_attn_bias[:, :, 1:, 1:] + rel_pos_bias

        # reset rel pos here
        t = self.super_token_virtual_distance.weight.view(1, self.head_size, 1)
        tree_attn_bias[:, :, 1:, 0] = tree_attn_bias[:, :, 1:, 0] + t
        tree_attn_bias[:, :, 0, :] = tree_attn_bias[:, :, 0, :] + t
        
        enc_dim = 3+self.max_filters*4+\
            50*self.max_filters*int(self.use_hist)+\
            int(self.use_sample)*1000
        # enc_dim = 3+self.max_filters*3+\
        #     50*self.max_filters*int(self.use_hist)+\
        #     int(self.use_sample)*1000
        
        # print(f"self.hidden_dim: {self.hidden_dim}")
        # print(f"n_batch: {n_batch}")

        # n = x.numel()
        # remainder = n % enc_dim
        # if remainder != 0:
        #     pad_length = enc_dim - remainder
        #     # Create a padding tensor with the same type and device as x.
        #     pad_tensor = torch.zeros(pad_length, dtype=x.dtype, device=x.device)
        #     # Flatten x (if it's not already flat), concatenate the padding,
        #     # and then reshape.
        #     x = torch.cat([x.view(-1), pad_tensor])

        x_view = x.view(-1, enc_dim)

        node_feature = self.embbed_layer(x_view)
        node_feature = node_feature.view(n_batch, -1, self.hidden_dim)
        node_feature = node_feature + self.height_encoder(heights)
        # print(f"node_feature with height:{node_feature[:3]}")
        super_token_feature = self.super_token.weight.unsqueeze(0).repeat(n_batch, 1, 1)
        # print(f"super_token_feature.shape: {super_token_feature.shape}")

        if self.use_additional_feature:
            # print(f"With additional feature")
            # node_feature: [88,-1,393], additional_feature_size: [88,1,1]
            # print("Shape of additional_feature before unsqueeze:", additional_feature.shape)
            additional_feature_expanded = additional_feature.unsqueeze(1)
            # print("Shape of additional_feature_expanded (before concatenation):", additional_feature_expanded.shape)
            
            # super_token_feature size: [88,1,393] -> [88,1,394]
            # print("Shape of super_token_feature before concatenation:", super_token_feature.shape)
            super_token_feature = torch.cat([super_token_feature, additional_feature_expanded], dim=-1)
            # print("Shape of super_token_feature after concatenation:", super_token_feature.shape)

            # node_feature size: [88,26,393] -> [88,26,394]
            padding = torch.zeros(n_batch, n_node, 1, device=node_feature.device)
            node_feature = torch.cat([node_feature, padding], dim=2)
            # print(f"node_feature shape: {node_feature.shape}")

        super_node_feature = torch.cat([super_token_feature, node_feature], dim=1)        
        
        output = self.input_dropout(super_node_feature)
        for enc_layer in self.layers:
            output = enc_layer(output, tree_attn_bias)
        output = self.final_ln(output)

        return output[:,0,:]



class FeedForwardNetwork(nn.Module):
    def __init__(self, hidden_size, ffn_size, dropout_rate):
        super(FeedForwardNetwork, self).__init__()

        self.layer1 = nn.Linear(hidden_size, ffn_size)
        self.gelu = nn.GELU()
        self.layer2 = nn.Linear(ffn_size, hidden_size)

    def forward(self, x):
        x = self.layer1(x)
        x = self.gelu(x)
        x = self.layer2(x)
        return x


class MultiHeadAttention(nn.Module):
    def __init__(self, hidden_size, attention_dropout_rate, head_size):
        super(MultiHeadAttention, self).__init__()

        self.head_size = head_size

        self.att_size = att_size = hidden_size // head_size
        self.scale = att_size ** -0.5

        self.linear_q = nn.Linear(hidden_size, head_size * att_size)
        self.linear_k = nn.Linear(hidden_size, head_size * att_size)
        self.linear_v = nn.Linear(hidden_size, head_size * att_size)
        self.att_dropout = nn.Dropout(attention_dropout_rate)

        self.output_layer = nn.Linear(head_size * att_size, hidden_size)

    def forward(self, q, k, v, attn_bias=None):
        orig_q_size = q.size()

        d_k = self.att_size
        d_v = self.att_size
        batch_size = q.size(0)

        # head_i = Attention(Q(W^Q)_i, K(W^K)_i, V(W^V)_i)
        q = self.linear_q(q).view(batch_size, -1, self.head_size, d_k)
        k = self.linear_k(k).view(batch_size, -1, self.head_size, d_k)
        v = self.linear_v(v).view(batch_size, -1, self.head_size, d_v)

        q = q.transpose(1, 2)                  # [b, h, q_len, d_k]
        v = v.transpose(1, 2)                  # [b, h, v_len, d_v]
        k = k.transpose(1, 2).transpose(2, 3)  # [b, h, d_k, k_len]

        # Scaled Dot-Product Attention.
        # Attention(Q, K, V) = softmax((QK^T)/sqrt(d_k))V
        q = q * self.scale
        x = torch.matmul(q, k)  # [b, h, q_len, k_len]
        if attn_bias is not None:
            x = x + attn_bias

        x = torch.softmax(x, dim=3)
        x = self.att_dropout(x)
        x = x.matmul(v)  # [b, h, q_len, attn]

        x = x.transpose(1, 2).contiguous()  # [b, q_len, h, attn]
        x = x.view(batch_size, -1, self.head_size * d_v)

        x = self.output_layer(x)

        assert x.size() == orig_q_size
        return x


class EncoderLayer(nn.Module):
    def __init__(self, hidden_size, ffn_size, dropout_rate, attention_dropout_rate, head_size):
        super(EncoderLayer, self).__init__()

        self.self_attention_norm = nn.LayerNorm(hidden_size)
        self.self_attention = MultiHeadAttention(hidden_size, attention_dropout_rate, head_size)
        self.self_attention_dropout = nn.Dropout(dropout_rate)

        self.ffn_norm = nn.LayerNorm(hidden_size)
        self.ffn = FeedForwardNetwork(hidden_size, ffn_size, dropout_rate)
        self.ffn_dropout = nn.Dropout(dropout_rate)

    def forward(self, x, attn_bias=None):
        y = self.self_attention_norm(x)
        y = self.self_attention(y, y, y, attn_bias)
        y = self.self_attention_dropout(y)
        x = x + y

        y = self.ffn_norm(x)
        y = self.ffn(y)
        y = self.ffn_dropout(y)
        x = x + y
        return x























