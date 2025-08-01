#!/bin/bash
# Main Experiment Runner
# Run different experiment configurations

echo "LLM4QPR Experiment Runner"
echo "========================="
echo ""

# Check if HF_TOKEN is set
if [ -z "$HF_TOKEN" ]; then
    echo "❌ Error: HF_TOKEN environment variable is not set."
    echo "Please set your Hugging Face token:"
    echo "  export HF_TOKEN=\"your_token_here\""
    exit 1
fi

echo "✅ HF_TOKEN is set"
echo ""

# Function to run experiments
run_experiment() {
    local script_name=$1
    local description=$2
    
    echo "🚀 Running: $description"
    echo "Script: $script_name"
    echo "---"
    
    if [ -f "experiment_scripts/$script_name" ]; then
        bash "experiment_scripts/$script_name"
        echo "✅ Completed: $description"
    else
        echo "❌ Error: Script $script_name not found"
    fi
    echo ""
}

# Available experiments
echo "Available experiments:"
echo "1. Comparison with Prior SOTA"
echo "2. Model Size Comparison"
echo "3. Training Ratio Analysis"
echo "4. Finetuning Experiments"
echo "5. Cross-Workload Experiments"
echo "6. All Experiments (in order)"
echo ""

# Get user choice
read -p "Enter experiment number (1-6): " choice

case $choice in
    1)
        run_experiment "run_baseline_comparison.sh" "Comparison with Prior SOTA"
        ;;
    2)
        run_experiment "run_model_size_comparison.sh" "Model Size Comparison"
        ;;
    3)
        run_experiment "run_training_ratio_analysis.sh" "Training Ratio Analysis"
        ;;
    4)
        run_experiment "run_finetuning_experiments.sh" "Finetuning Experiments"
        ;;
    5)
        run_experiment "run_cross_workload_experiments.sh" "Cross-Workload Experiments"
        ;;
    6)
        echo "🔄 Running all experiments in sequence..."
        echo ""
        run_experiment "run_baseline_comparison.sh" "Comparison with Prior SOTA"
        run_experiment "run_model_size_comparison.sh" "Model Size Comparison"
        run_experiment "run_training_ratio_analysis.sh" "Training Ratio Analysis"
        run_experiment "run_finetuning_experiments.sh" "Finetuning Experiments"
        run_experiment "run_cross_workload_experiments.sh" "Cross-Workload Experiments"
        echo "🎉 All experiments completed!"
        ;;
    *)
        echo "❌ Invalid choice. Please run the script again and select 1-6."
        exit 1
        ;;
esac

echo "🏁 Experiment runner finished!" 