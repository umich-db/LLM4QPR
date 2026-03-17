#!/usr/bin/env python3
"""
Latency probe: measures per-query LLM embedding latency for a given model.

Usage:
    python latency_probe.py \
        --model_name "sentence-transformers/all-MiniLM-L6-v2" \
        --workload stats \
        --db postgres \
        --num_queries 100 \
        --quantification 4-bit

Outputs JSON to stdout:
    {"model": "...", "avg_ms": 12.3, "p50_ms": 11.5, "p95_ms": 15.2, "num_queries": 100}
"""

import argparse
import json
import os
import sys
import time

import numpy as np
import pandas as pd
import torch

# Add experiments/ to path so we can import utilsLLM
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXPERIMENTS_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, EXPERIMENTS_DIR)
sys.path.insert(0, os.path.join(EXPERIMENTS_DIR, '..', 'evaluation'))


def get_workload_csv_path(workload, db):
    """Resolve the CSV path for a given workload and database engine."""
    base = os.path.join(EXPERIMENTS_DIR, '..', 'queryPlans')
    if workload in ('job', 'syn', 'job_full', 'jobm'):
        return os.path.join(base, 'imdb', db, f'long_raw_{db}_imdb.csv')
    else:
        return os.path.join(base, workload, db, f'long_raw_{db}_{workload}.csv')


def load_query_texts(csv_path, num_queries):
    """Load and clean query plan texts from the workload CSV."""
    df = pd.read_csv(csv_path)
    raw_jsons = df['json'].tolist()

    texts = []
    for raw in raw_jsons[:num_queries]:
        plan = json.loads(raw)
        # Extract root plan node
        if isinstance(plan, dict):
            if 'Plan' in plan:
                root = plan['Plan']
            elif isinstance(plan, list) and len(plan) > 0:
                root = plan[0].get('Plan', plan[0])
            else:
                root = plan
        else:
            root = plan

        # Remove "Actual..." keys to match training-time cleaning
        def clean_node(node):
            if isinstance(node, dict):
                cleaned = {}
                for k, v in node.items():
                    if k.startswith('Actual'):
                        continue
                    cleaned[k] = clean_node(v)
                return cleaned
            elif isinstance(node, list):
                return [clean_node(item) for item in node]
            return node

        cleaned = clean_node(root)
        texts.append(json.dumps(cleaned))

    return texts


def get_effective_max_length(predictor):
    """Determine the real max token length for a model, handling absurd tokenizer defaults."""
    tok_max = predictor.tokenizer.model_max_length

    # Many models report tokenizer.model_max_length as 1e30; use config instead
    model_cfg = getattr(predictor.model, 'config', None)
    if model_cfg is None and hasattr(predictor.model, 'base_model'):
        model_cfg = getattr(predictor.model.base_model, 'config', None)
    if model_cfg is None and hasattr(predictor.model, 'model'):
        model_cfg = getattr(predictor.model.model, 'config', None)

    pos_max = None
    if model_cfg is not None:
        pos_max = getattr(model_cfg, 'max_position_embeddings', None)

    candidates = []
    if tok_max is not None and tok_max < 1_000_000:
        candidates.append(tok_max)
    if pos_max is not None and pos_max < 1_000_000:
        candidates.append(pos_max)

    if candidates:
        return min(candidates)
    # Fallback for unknown models
    return 512


def truncate_texts(predictor, texts):
    """Truncate texts to the model's max token length to avoid index errors."""
    max_length = get_effective_max_length(predictor)
    print(f"[latency_probe] Effective max token length: {max_length}", file=sys.stderr)

    truncated = []
    for text in texts:
        tokens = predictor.tokenizer.encode(text, add_special_tokens=True)
        if len(tokens) > max_length:
            tokens = tokens[:max_length]
            text = predictor.tokenizer.decode(tokens, skip_special_tokens=True)
        truncated.append(text)
    return truncated


def measure_latency(predictor, texts):
    """Measure per-query latency in milliseconds, batch_size=1."""
    predictor.eval()
    latencies = []
    use_cuda = torch.cuda.is_available()

    # Truncate to model max length to avoid index-out-of-range errors
    texts = truncate_texts(predictor, texts)

    # Warmup: run 3 queries to avoid cold-start effects
    warmup_count = min(3, len(texts))
    with torch.no_grad():
        for i in range(warmup_count):
            _ = predictor([texts[i]])
            if use_cuda:
                torch.cuda.synchronize()

    with torch.no_grad():
        for text in texts:
            if use_cuda:
                torch.cuda.synchronize()
            t0 = time.perf_counter()
            _ = predictor([text])
            if use_cuda:
                torch.cuda.synchronize()
            t1 = time.perf_counter()
            latencies.append((t1 - t0) * 1000.0)  # ms

    return latencies


def main():
    parser = argparse.ArgumentParser(description='Measure per-query LLM embedding latency')
    parser.add_argument('--model_name', type=str, required=True, help='HuggingFace model name')
    parser.add_argument('--workload', type=str, default='stats', help='Workload name (stats, job, tpch, etc.)')
    parser.add_argument('--db', type=str, default='postgres', help='Database engine')
    parser.add_argument('--num_queries', type=int, default=100, help='Number of queries to probe')
    parser.add_argument('--quantification', type=str, default='4-bit', choices=['4-bit', '8-bit', 'None'],
                        help='Quantization level')
    args = parser.parse_args()

    # Suppress model loading verbosity — redirect stderr temporarily
    csv_path = get_workload_csv_path(args.workload, args.db)
    if not os.path.exists(csv_path):
        print(json.dumps({"error": f"Workload CSV not found: {csv_path}"}), file=sys.stdout)
        sys.exit(1)

    texts = load_query_texts(csv_path, args.num_queries)
    if len(texts) == 0:
        print(json.dumps({"error": "No query texts loaded"}), file=sys.stdout)
        sys.exit(1)

    # Print status to stderr so stdout stays clean for JSON
    print(f"[latency_probe] Loading model: {args.model_name} (quant={args.quantification})", file=sys.stderr)

    # Redirect stdout during model loading to stderr, since QueryPlanPredictor
    # prints initialization details to stdout which would pollute our JSON output.
    original_stdout = sys.stdout
    sys.stdout = sys.stderr
    try:
        from utilsLLM import QueryPlanPredictor
        predictor = QueryPlanPredictor(
            model_name=args.model_name,
            mode="inference",
            quantification=args.quantification,
        )
    except Exception as e:
        sys.stdout = original_stdout
        print(json.dumps({"error": f"Model loading failed: {e}"}))
        sys.exit(1)
    finally:
        sys.stdout = original_stdout

    # Fix absurd tokenizer.model_max_length (some models report 1e30).
    # Cap it to max_position_embeddings from config, or 512 as fallback.
    effective_max = get_effective_max_length(predictor)
    if predictor.tokenizer.model_max_length > 1_000_000:
        predictor.tokenizer.model_max_length = effective_max
        print(f"[latency_probe] Capped tokenizer.model_max_length to {effective_max}", file=sys.stderr)

    print(f"[latency_probe] Measuring latency on {len(texts)} queries...", file=sys.stderr)
    try:
        latencies = measure_latency(predictor, texts)
    except Exception as e:
        print(json.dumps({"error": f"Latency measurement failed: {e}"}))
        sys.exit(1)

    arr = np.array(latencies)
    result = {
        "model": args.model_name,
        "avg_ms": round(float(np.mean(arr)), 2),
        "p50_ms": round(float(np.percentile(arr, 50)), 2),
        "p95_ms": round(float(np.percentile(arr, 95)), 2),
        "num_queries": len(latencies),
    }

    # Output JSON to stdout (the only stdout line)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
