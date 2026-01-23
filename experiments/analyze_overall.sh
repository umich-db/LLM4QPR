# bash compare_results.sh
# python analysis_scripts/summarize_inference_logs.py --log_dir logs_results_embeddings_10.11/logs
# python analysis_scripts/summarize_train_eval_logs.py --log_dir logs_results_embeddings_10.11/logs_train_eval
# python analysis_scripts/combine_timing_accuracy.py --base_dir logs_results_embeddings_10.11
# python analysis_scripts/plot_timing_accuracy.py --group_by task_dataset --input logs_results_embeddings_10.11/combined_timing_accuracy_report.csv --output_dir logs_results_embeddings_10.11/graphs
# python analysis_scripts/plot_timing_accuracy.py --group_by task --input logs_results_embeddings_10.11/combined_timing_accuracy_report.csv --output_dir logs_results_embeddings_10.11/graphs --outlier_nth 10
# python analysis_scripts/analyze_best_models.py --dir logs_results_embeddings_10.11 --threshold 3


# bash compare_results.sh
python analysis_scripts/summarize_inference_logs.py --log_dir logs
python analysis_scripts/summarize_train_eval_logs.py --log_dir logs_results_embeddings_10.11/logs_train_eval
python analysis_scripts/combine_timing_accuracy.py --base_dir .
# python analysis_scripts/plot_timing_accuracy.py --group_by task_dataset --input combined_timing_accuracy_report.csv --output_dir graphs --relative
python analysis_scripts/plot_timing_accuracy.py --group_by task --input combined_timing_accuracy_report.csv --output_dir graphs --outlier_nth 12 --relative min
# python analysis_scripts/plot_timing_accuracy.py --group_by task --input combined_timing_accuracy_report.csv --output_dir graphs --outlier_nth 12 --relative pg
# python analysis_scripts/analyze_best_models.py --dir . --threshold 2 --relative min
# python analysis_scripts/analyze_best_models.py --dir . --threshold 2 --relative pg
# python analysis_scripts/plot_timing_accuracy.py --group_by task_dataset --input combined_timing_accuracy_report.csv --output_dir graphs
# python analysis_scripts/plot_timing_accuracy.py --group_by task --input combined_timing_accuracy_report.csv --output_dir graphs --outlier_nth 15
# python analysis_scripts/analyze_best_models.py --dir . --threshold 2





# python analysis_scripts/card_rm_analysis.py --datasets job stats --average_by dataset
# python analysis_scripts/card_rm_analysis.py --datasets job stats --average_by model dataset
# python analysis_scripts/card_rm_analysis.py --datasets job stats --models h2048_google-gemma-3-1b-pt --average_by model dataset
# python analysis_scripts/card_rm_analysis.py --datasets job stats --models h2048_Qwen-Qwen3-Embedding-8B --average_by model dataset
# python analysis_scripts/card_rm_analysis.py --datasets job stats --models h2048_meta-llama-Llama-3.1-8B --average_by model dataset

# python analysis_scripts/check_missing_seeds.py --results_root results

# python analysis_scripts/verbose_analysis.py \
#   --algo llm \
#   --model google-gemma-3-1b-pt \
#   --dataset stats \
#   --task card \
#   --seed 42 \
#   --analysis_type top_q_error \
#   --topk 10

# python analysis_scripts/verbose_analysis.py \
#   --algo llm \
#   --model meta-llama-Llama-3.1-8B \
#   --dataset stats \
#   --task card \
#   --seed 42 \
#   --analysis_type top_q_error \
#   --topk 10

# python analysis_scripts/verbose_analysis.py \
#   --algo llm \
#   --model Qwen-Qwen3-Embedding-8B \
#   --dataset stats \
#   --task card \
#   --seed 42 \
#   --analysis_type top_q_error \
#   --topk 10

# python analysis_scripts/verbose_analysis.py \
#   --algo llm \
#   --model meta-llama-Llama-3.1-8B \
#   --dataset job_full \
#   --task time \
#   --seed 42 \
#   --analysis_type top_q_error \
#   --topk 10

# python analysis_scripts/verbose_analysis.py \
#   --algo e2e_cost \
#   --dataset job_full \
#   --task time \
#   --seed 42 \
#   --analysis_type top_q_error \
#   --topk 10



# python analysis_scripts/verbose_analysis.py \
#   --algo llm \
#   --model meta-llama-Llama-3.1-8B \
#   --dataset job_full \
#   --task time \
#   --seed 42 \
#   --analysis_type embedding_geometry \
#   --geometry_metric all \
#   --geometry_num_pairs 50000 \
#   --geometry_knn_k 15

# python analysis_scripts/verbose_analysis.py \
#   --algo e2e_cost \
#   --dataset job_full \
#   --task time \
#   --seed 42 \
#   --analysis_type embedding_geometry \
#   --geometry_metric all \
#   --geometry_num_pairs 50000 \
#   --geometry_knn_k 15

# python analysis_scripts/verbose_analysis.py \
#   --dataset job_full \
#   --task time \
#   --seed 42 \
#   --analysis_type embedding_geometry \
#   --geometry_metric all \
#   --geometry_num_pairs 50000 \
#   --geometry_knn_k 15

# python analysis_scripts/verbose_analysis.py \
#   --seed 42 \
#   --analysis_type embedding_geometry \
#   --geometry_metric all \
#   --geometry_num_pairs 50000 \
#   --geometry_knn_k 15

# python analysis_scripts/insights/plot_geometry_tables.py \
#   --input_dir analysis_scripts/insights/geometry_results

# python add_baseline_quantiles.py
# python plot_all_quantile_tables.py
# python3 analyze_geometry_error_correlation.py

# Use defaults (stats dataset, card task, Llama-3.1-8B)
python shapley_field_removal.py --dataset results_Train_stats_Test_stats_ours --task card --model Llama-3.1-8B

# Test only cost, card, cond, meta (keep ops always present)
python shapley_field_removal.py --dataset results_Train_stats_Test_stats_ours --task card --model Llama-3.1-8B --test-categories cost card cond meta

Use defaults (stats dataset, card task, Llama-3.1-8B)
python shapley_field_removal.py --dataset results_Train_job_full_Test_job_full_ours --task time --model Llama-3.1-8B

# Combine with specific categories to test
python shapley_field_removal.py --dataset results_Train_job_full_Test_job_full_ours --task time --model Llama-3.1-8B --test-categories cost card cond meta

# python analysis_scripts/insights/test_embedding_similarity.py --dataset job --task card --seed 42


# python analysis_scripts/insights/plot_geometry_tables.py \
#     --result_type alignment \
#     --pattern "metric_alignment_job_full_time_seed42.csv"


# python analysis_scripts/insights/metric_alignment.py \
#   --dataset job_full --task time --seed 42


# python analysis_scripts/insights/qerror_structure_alignment.py \
#   --dataset job_full --task time --seed 42

# python analysis_scripts/insights/caseStudy.py \
#   --dataset job_full --task time --seed 42 \
#   --algo e2e_cost --pc_drop_k 1

# python analysis_scripts/insights/caseStudy.py \
#   --dataset job_full --task time --seed 42 \
#   --algo llm --model meta-llama-Llama-3.1-8B --pc_drop_k 1

# python analysis_scripts/insights/caseStudy.py \
#   --dataset job_full --task time --seed 42 \
#   --algo llm --model Qwen-Qwen3-Embedding-8B --pc_drop_k 1

# python analysis_scripts/insights/caseStudy.py \
#   --dataset job_full --task time --seed 42 \
#   --algo llm --model google-gemma-3-1b-pt --pc_drop_k 1

# python analysis_scripts/insights/caseStudy.py \
#   --dataset job_full --task time --seed 42 \
#   --pc_drop_k 1  --study_type spearman

# python analysis_scripts/insights/caseStudy.py \
#   --dataset job_full --task time --seed 42 \
#   --algo llm --model meta-llama-Llama-3.1-8B \
#   --study_type counts

# python analysis_scripts/insights/caseStudy.py \
#   --dataset job_full --task time --seed 42 \
#   --algo llm --model Qwen-Qwen3-Embedding-8B \
#   --study_type counts

# python analysis_scripts/insights/caseStudy.py \
#   --dataset job_full --task time --seed 42 \
#   --algo llm --model google-gemma-3-1b-pt \
#   --study_type counts

# python analysis_scripts/insights/grand_analysis.py --dataset job_full --task time --seed 42
# python analysis_scripts/insights/grand_analysis.py --dataset job --task time --seed 42
# python analysis_scripts/insights/grand_analysis.py --dataset job --task card --seed 42
# python analysis_scripts/insights/grand_analysis.py --dataset syn --task time --seed 42
# python analysis_scripts/insights/grand_analysis.py --dataset syn --task card --seed 42
# python analysis_scripts/insights/grand_analysis.py --dataset stats --task time --seed 42
# python analysis_scripts/insights/grand_analysis.py --dataset stats --task card --seed 42
# python analysis_scripts/insights/grand_analysis.py --dataset tpch --task time --seed 42
# python analysis_scripts/insights/grand_analysis.py --dataset tpcds --task time --seed 42


# python analysis_scripts/insights/analyze_error_coefficients.py
python analysis_scripts/insights/metric_bucket_analysis.py --num_buckets 5 --target llm
# python analysis_scripts/insights/metric_bucket_analysis.py --num_buckets 5 --target baseline


python analysis_scripts/insights/generate_slim_plots.py

python analysis_scripts/insights/analyze_error_ranges.py


# Process only stats/card
# python analysis_scripts/insights/metric_bucket_analysis.py --dataset stats --task card --num_buckets 5

# Process all datasets for card task
python analysis_scripts/insights/metric_bucket_analysis.py --task card --num_buckets 5





python tables/generate_overleaf_table.py --datasets tpch,tpcds,syn --task time --output tables/overleaf_table_time.tex --results_dir results
python tables/generate_overleaf_table.py --datasets job,job_full,stats --task time --output tables/overleaf_table_time_p2.tex --results_dir results
python tables/generate_overleaf_table.py --datasets syn,job,stats --task card --output tables/overleaf_table_card.tex --results_dir results

python tables/generate_finetune_comparison_table.py
python tables/generate_training_ratio_table.py 


python add_baseline_quantiles_from_csv.py



# Absolute error analysis
python analysis_scripts/analyze_llm_size_vs_error.py --input combined_timing_accuracy_report.csv

# Relative error (min baseline)
python analysis_scripts/analyze_llm_size_vs_error.py --input combined_timing_accuracy_report.csv --relative min

# Relative error (postgres baseline)
python analysis_scripts/analyze_llm_size_vs_error.py --input combined_timing_accuracy_report.csv --relative pg

# Save results to CSV
python analysis_scripts/analyze_llm_size_vs_error.py --input combined_timing_accuracy_report.csv --relative min --output llm_size_analysis.csv

python analysis_scripts/analyze_llm_size_vs_error.py --input combined_timing_accuracy_report.csv --relative min --output llm_size_analysis.csv --plot_dir graphs/llm_size_analysis

# Default: use model rank on x-axis
python analysis_scripts/analyze_llm_size_vs_error.py --input combined_timing_accuracy_report.csv --plot_dir output/

# Use inference time on x-axis
python analysis_scripts/analyze_llm_size_vs_error.py --input combined_timing_accuracy_report.csv --relative min --output llm_size_analysis.csv --plot_dir graphs/llm_size_analysis --x_axis inference_time



# Run analysis
python3 analysis_scripts/find_zero_columns_bao.py

# Save results to CSV
python3 analysis_scripts/find_zero_columns_bao.py --output bao_zero_analysis.csv

python3 analysis_scripts/find_nonzero_last_column_bao.py embeddings/non-llm/bao_Train_tpcds_Test_tpcds_seed44_tpcds.csv --show-values




python tables/generate_training_time_table.py --input combined_timing_accuracy_report.csv --output tables/training_time_table.tex


python tables/generate_shapley_table.py \
  --time_file shapley_field_removal_results_results_Train_job_full_Test_job_full_ours_time_Llama-3.1-8B.csv \
  --card_file shapley_field_removal_results_results_Train_stats_Test_stats_ours_card_Llama-3.1-8B.csv \
  --output tables/shapley_table.tex



python analysis_scripts/compare_finetune_time.py


python analysis_scripts/analyze_specific_queries.py --verbose_dir verbose/verbose_Train_job_full_Test_job_full_ours --indices 35 36 --task time --models google-gemma-3-4b-pt meta-llama-Llama-3.1-8B Qwen-Qwen3-Embedding-8B