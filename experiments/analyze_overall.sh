# bash compare_results.sh
# python analysis_scripts/summarize_inference_logs.py --log_dir logs_results_embeddings_10.11/logs
# python analysis_scripts/summarize_train_eval_logs.py --log_dir logs_results_embeddings_10.11/logs_train_eval
# python analysis_scripts/combine_timing_accuracy.py --base_dir logs_results_embeddings_10.11
# python analysis_scripts/plot_timing_accuracy.py --group_by task_dataset --input logs_results_embeddings_10.11/combined_timing_accuracy_report.csv --output_dir logs_results_embeddings_10.11/graphs
# python analysis_scripts/plot_timing_accuracy.py --group_by task --input logs_results_embeddings_10.11/combined_timing_accuracy_report.csv --output_dir logs_results_embeddings_10.11/graphs --outlier_nth 10
# python analysis_scripts/analyze_best_models.py --dir logs_results_embeddings_10.11 --threshold 3


# bash compare_results.sh
# python analysis_scripts/summarize_inference_logs.py --log_dir logs
# python analysis_scripts/summarize_train_eval_logs.py --log_dir logs_results_embeddings_10.11/logs_train_eval
# python analysis_scripts/combine_timing_accuracy.py --base_dir .
# python analysis_scripts/plot_timing_accuracy.py --group_by task_dataset --input combined_timing_accuracy_report.csv --output_dir graphs --relative
# python analysis_scripts/plot_timing_accuracy.py --group_by task --input combined_timing_accuracy_report.csv --output_dir graphs --outlier_nth 12 --relative
python analysis_scripts/analyze_best_models.py --dir . --threshold 2 --relative
# python analysis_scripts/plot_timing_accuracy.py --group_by task_dataset --input combined_timing_accuracy_report.csv --output_dir graphs
# python analysis_scripts/plot_timing_accuracy.py --group_by task --input combined_timing_accuracy_report.csv --output_dir graphs --outlier_nth 15
# python analysis_scripts/analyze_best_models.py --dir . --threshold 2