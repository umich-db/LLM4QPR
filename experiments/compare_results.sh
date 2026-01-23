python to_table_seeds.py --dir results/results_Train_tpch_Test_tpch_ours --task time
python to_table_seeds.py --dir results/results_Train_tpcds_Test_tpcds_ours --task time
python to_table_seeds.py --dir results/results_Train_syn_Test_syn_ours --task time
python to_table_seeds.py --dir results/results_Train_syn_Test_syn_ours --task card
python to_table_seeds.py --dir results/results_Train_job_Test_job_ours --task time
python to_table_seeds.py --dir results/results_Train_job_Test_job_ours --task card
python to_table_seeds.py --dir results/results_Train_job_full_Test_job_full_ours --task time
python to_table_seeds.py --dir results/results_Train_stats_Test_stats_ours --task time
python to_table_seeds.py --dir results/results_Train_stats_Test_stats_ours --task card

python to_table_seeds.py --dir results/results_Train_genome-financial-movielens-geneea-seznam-tpc_h-walmart-airline-carcinogenesis-baseball-accidents-ssb-basketball-employee-fhnk-consumer-tournament-credit-hepatitis_Test_job-light_ours --task time
python to_table_seeds.py --dir results/results_Train_genome-financial-movielens-geneea-seznam-tpc_h-walmart-airline-carcinogenesis-baseball-accidents-ssb-basketball-employee-fhnk-consumer-tournament-credit-hepatitis_Test_synthetic_ours --task time
python to_table_seeds.py --dir results/results_Train_genome-financial-movielens-geneea-seznam-walmart-airline-carcinogenesis-baseball-imdb-accidents-ssb-basketball-employee-fhnk-consumer-tournament-credit-hepatitis_Test_tpc_h_ours --task time


# python to_table_seeds.py --dir logs_results_embeddings_10.11/results/results_Train_tpch_Test_tpch_ours --task time --heatmap
# python to_table_seeds.py --dir logs_results_embeddings_10.11/results/results_Train_tpcds_Test_tpcds_ours --task time --heatmap
# python to_table_seeds.py --dir logs_results_embeddings_10.11/results/results_Train_syn_Test_syn_ours --task time --heatmap
# python to_table_seeds.py --dir logs_results_embeddings_10.11/results/results_Train_syn_Test_syn_ours --task card --heatmap
# python to_table_seeds.py --dir logs_results_embeddings_10.11/results/results_Train_job_Test_job_ours --task time --heatmap
# python to_table_seeds.py --dir logs_results_embeddings_10.11/results/results_Train_job_Test_job_ours --task card --heatmap
# python to_table_seeds.py --dir logs_results_embeddings_10.11/results/results_Train_job_full_Test_job_full_ours --task time --heatmap
# # python to_table_seeds.py --dir logs_results_embeddings_10.11/results/results_Train_job_full_Test_job_full_ours --task card --heatmap
# python to_table_seeds.py --dir logs_results_embeddings_10.11/results/results_Train_stats_Test_stats_ours --task time --heatmap
# python to_table_seeds.py --dir logs_results_embeddings_10.11/results/results_Train_stats_Test_stats_ours --task card --heatmap

python compare_llama_pretrained.py --dataset stats --task card
python compare_llama_pretrained.py --dataset stats --task time
python compare_llama_pretrained.py --dataset tpch --task time
python compare_llama_pretrained.py --dataset tpcds --task time