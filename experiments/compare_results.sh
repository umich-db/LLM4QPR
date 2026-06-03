MODEL=bert2 ANCHOR=90 MLP=jointMLP bash experiment_scripts/aggregate_tables.sh --no-priceb-equiv 
MODEL=bert4 ANCHOR=90 MLP=jointMLP bash experiment_scripts/aggregate_tables.sh --no-priceb-equiv
MODEL=sentbert ANCHOR=90 MLP=jointMLP bash experiment_scripts/aggregate_tables.sh --no-priceb-equiv

python cross_engine_aggregate.py --anchor 90            # also accepts 50 / 95 / max
python cross_engine_aggregate.py --anchor 90 --jointmlp_only   # heatmaps restricted to _jointMLP cols
python cross_engine_aggregate.py --anchor 90 --jointmlp_only --frzeven_retrainMLP_cells bert2:duckdb:tpcds sentbert:spark:tpcds

python to_table_seeds.py --dir results/postgres/results_Train_job_Test_syn_ours --task time --sentbert_only
python to_table_seeds.py --dir results/postgres/results_Train_job_Test_job_ours --task time --sentbert_only
python to_table_seeds.py --dir results/postgres/results_Train_job_Test_job_full_ours --task time --sentbert_only
python to_table_seeds.py --dir results/postgres/results_Train_stats_Test_stats_ours --task time --sentbert_only
python to_table_seeds.py --dir results/postgres/results_Train_tpcds_Test_tpcds_ours --task time --sentbert_only
python to_table_seeds.py --dir results/postgres/results_Train_tpch_Test_tpch_ours --task time --sentbert_only

python to_table_relative.py --task time --dirs results/postgres/results_Train_stats_Test_stats_ours results/postgres/results_Train_job_Test_syn_ours results/postgres/results_Train_job_Test_job_ours results/postgres/results_Train_job_Test_job_full_ours results/postgres/results_Train_tpcds_Test_tpcds_ours results/postgres/results_Train_tpch_Test_tpch_ours --sentbert_only


python to_table_seeds.py --dir results/duckdb/results_Train_job_Test_syn_ours --task time --sentbert_only
python to_table_seeds.py --dir results/duckdb/results_Train_job_Test_job_ours --task time --sentbert_only
python to_table_seeds.py --dir results/duckdb/results_Train_job_Test_job_full_ours --task time --sentbert_only
python to_table_seeds.py --dir results/duckdb/results_Train_stats_Test_stats_ours --task time --sentbert_only
python to_table_seeds.py --dir results/duckdb/results_Train_tpcds_Test_tpcds_ours --task time --sentbert_only
python to_table_seeds.py --dir results/duckdb/results_Train_tpch_Test_tpch_ours --task time --sentbert_only

python to_table_relative.py --task time --dirs results/duckdb/results_Train_stats_Test_stats_ours results/duckdb/results_Train_job_Test_syn_ours results/duckdb/results_Train_job_Test_job_ours results/duckdb/results_Train_job_Test_job_full_ours results/duckdb/results_Train_tpcds_Test_tpcds_ours results/duckdb/results_Train_tpch_Test_tpch_ours --sentbert_only


python to_table_seeds.py --dir results/spark/results_Train_job_Test_syn_ours --task time --sentbert_only
python to_table_seeds.py --dir results/spark/results_Train_job_Test_job_ours --task time --sentbert_only
python to_table_seeds.py --dir results/spark/results_Train_job_Test_job_full_ours --task time --sentbert_only
python to_table_seeds.py --dir results/spark/results_Train_stats_Test_stats_ours --task time --sentbert_only
python to_table_seeds.py --dir results/spark/results_Train_tpcds_Test_tpcds_ours --task time --sentbert_only
python to_table_seeds.py --dir results/spark/results_Train_tpch_Test_tpch_ours --task time --sentbert_only

python to_table_relative.py --task time --dirs results/spark/results_Train_stats_Test_stats_ours results/spark/results_Train_job_Test_syn_ours results/spark/results_Train_job_Test_job_ours results/spark/results_Train_job_Test_job_full_ours results/spark/results_Train_tpcds_Test_tpcds_ours results/spark/results_Train_tpch_Test_tpch_ours --sentbert_only







python to_table_seeds.py --dir results/duckdb/results_Train_job_Test_job_ours --task time --sentbert_only --special_set1
python to_table_seeds.py --dir results/duckdb/results_Train_jobm_Test_jobm_ours --task time --sentbert_only --special_set1
python to_table_seeds.py --dir results/duckdb/results_Train_stats_Test_stats_ours --task time --sentbert_only --special_set1

python to_table_relative.py --task time --dirs results/duckdb/results_Train_stats_Test_stats_ours results/duckdb/results_Train_job_Test_job_ours results/duckdb/results_Train_jobm_Test_jobm_ours --sentbert_only --special_set1


python to_table_seeds.py --dir results/spark/results_Train_job_Test_job_ours --task time --sentbert_only --special_set1
python to_table_seeds.py --dir results/spark/results_Train_jobm_Test_jobm_ours --task time --sentbert_only --special_set1
python to_table_seeds.py --dir results/spark/results_Train_stats_Test_stats_ours --task time --sentbert_only --special_set1

python to_table_relative.py --task time --dirs results/spark/results_Train_stats_Test_stats_ours results/spark/results_Train_job_Test_job_ours results/spark/results_Train_jobm_Test_jobm_ours --sentbert_only --special_set1



# python to_table_seeds.py --dir results/postgres/results_Train_tpch_Test_tpch_ours --task time
# python to_table_seeds.py --dir results/postgres/results_Train_tpcds_Test_tpcds_ours --task time
# python to_table_seeds.py --dir results/postgres/results_Train_syn_Test_syn_ours --task time
# python to_table_seeds.py --dir results/postgres/results_Train_syn_Test_syn_ours --task card
python to_table_seeds.py --dir results/postgres/results_Train_job_Test_job_ours --task time
# python to_table_seeds.py --dir results/postgres/results_Train_job_Test_job_ours --task card
# python to_table_seeds.py --dir results/postgres/results_Train_job_full_Test_job_full_ours --task time
python to_table_seeds.py --dir results/postgres/results_Train_jobm_Test_jobm_ours --task time
python to_table_seeds.py --dir results/postgres/results_Train_stats_Test_stats_ours --task time
# python to_table_seeds.py --dir results/postgres/results_Train_stats_Test_stats_ours --task card

python to_table_seeds.py --dir results/duckdb/results_Train_job_Test_job_ours --task time
python to_table_seeds.py --dir results/duckdb/results_Train_jobm_Test_jobm_ours --task time
python to_table_seeds.py --dir results/duckdb/results_Train_stats_Test_stats_ours --task time


# python to_table_seeds.py --dir results/postgres/results_Train_genome-financial-movielens-geneea-seznam-tpc_h-walmart-airline-carcinogenesis-baseball-accidents-ssb-basketball-employee-fhnk-consumer-tournament-credit-hepatitis_Test_job-light_ours --task time
# python to_table_seeds.py --dir results/postgres/results_Train_genome-financial-movielens-geneea-seznam-tpc_h-walmart-airline-carcinogenesis-baseball-accidents-ssb-basketball-employee-fhnk-consumer-tournament-credit-hepatitis_Test_synthetic_ours --task time
# python to_table_seeds.py --dir results/postgres/results_Train_genome-financial-movielens-geneea-seznam-walmart-airline-carcinogenesis-baseball-imdb-accidents-ssb-basketball-employee-fhnk-consumer-tournament-credit-hepatitis_Test_tpc_h_ours --task time


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

# python compare_llama_pretrained.py --dataset stats --task card
# python compare_llama_pretrained.py --dataset stats --task time
# python compare_llama_pretrained.py --dataset tpch --task time
# python compare_llama_pretrained.py --dataset tpcds --task time