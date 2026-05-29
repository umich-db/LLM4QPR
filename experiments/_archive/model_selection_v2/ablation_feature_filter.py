#!/usr/bin/env python3
"""Ablation study: does feature filtering help in model selection?

Tests different (feature_filter_after, keep_top_k_features) settings
across 10 random seeds. Reports rank of best found model vs oracle.
Uses real cached CDF results for ground-truth ranking.
"""
import sys, os, glob, io, contextlib
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import pandas as pd
from model_selection_v2 import (
    SearchConfig, ConstrainedModelSearch, load_candidates,
    make_evaluator, find_cdf_file, parse_qerror,
    CONTINUOUS_COLS, CATEGORICAL_COLS,
)
from argparse import Namespace


def build_oracle_ranking(candidates, evaluator_args, latency_limit):
    """Build ground-truth ranking from cached CDF results for all feasible models."""
    oracle = []
    for _, row in candidates.iterrows():
        lat = float(row["avg_ms"])
        if lat > latency_limit:
            continue
        cached = find_cdf_file(row["model"], evaluator_args)
        if cached is None:
            continue
        qerror = parse_qerror(cached)
        oracle.append({
            "model": row["model"],
            "latency": lat,
            "accuracy": -qerror["p90"],  # higher = better
        })
    oracle_df = pd.DataFrame(oracle).sort_values("accuracy", ascending=False).reset_index(drop=True)
    oracle_df["rank"] = range(1, len(oracle_df) + 1)
    return oracle_df


def run_one(candidates, available_cont, available_cat, evaluator_args,
            oracle_df, seed, enable_ff, filter_after, top_k):
    config = SearchConfig(
        latency_limit=20.0,
        init_budget=8,
        batch_size=4,
        max_evals=20,
        random_state=seed,
        enable_feature_filtering=enable_ff,
        feature_filter_after=filter_after,
        keep_top_k_features=top_k,
    )

    evaluator = make_evaluator(evaluator_args)
    with contextlib.redirect_stdout(io.StringIO()):
        search = ConstrainedModelSearch(
            candidates=candidates.copy(),
            evaluator=evaluator,
            config=config,
            candidate_id_col="model",
            continuous_cols=available_cont + ["log_non_embedding_params"],
            categorical_cols=available_cat,
        )
        result = search.run()

    selected_model = None
    selected_rank = None
    selected_accuracy = None
    if result.best_feasible_row is not None:
        selected_model = result.best_feasible_row["model"]
        selected_accuracy = result.best_feasible_row["_accuracy"]
        match = oracle_df[oracle_df["model"] == selected_model]
        if not match.empty:
            selected_rank = int(match.iloc[0]["rank"])

    return {
        "seed": seed,
        "enable_ff": enable_ff,
        "filter_after": filter_after,
        "top_k": top_k,
        "selected_model": selected_model,
        "selected_rank": selected_rank,
        "oracle_model": oracle_df.iloc[0]["model"],
        "n_feasible": len(oracle_df),
        "num_evaluated": len(result.evaluated),
        "selected_accuracy": selected_accuracy,
        "selected_features": result.selected_feature_names,
    }


def main():
    csv_path = os.path.join(os.path.dirname(__file__), "model_profile_with_nonemb.csv")
    candidates = load_candidates(csv_path)

    available_cont = [c for c in CONTINUOUS_COLS if c in candidates.columns]
    available_cat = [c for c in CATEGORICAL_COLS if c in candidates.columns]

    evaluator_args = Namespace(
        dry_run=False,
        workload="stats",
        task="time",
        db="postgres",
        quantification="4-bit",
        embed_size=1000,
        price_s=True,
        max_eval_queries=200,
        csv=csv_path,
    )

    # Build ground-truth oracle ranking from cached CDF results
    print("Building oracle ranking from cached CDF results...")
    oracle_df = build_oracle_ranking(candidates, evaluator_args, 20.0)
    print(f"Oracle: {len(oracle_df)} feasible models with cached results")
    print(f"Oracle best: {oracle_df.iloc[0]['model']} (p90={-oracle_df.iloc[0]['accuracy']:.2f})")
    print(f"Top 5:")
    for i in range(min(5, len(oracle_df))):
        r = oracle_df.iloc[i]
        print(f"  #{i+1}: {r['model']} (p90={-r['accuracy']:.2f})")

    seeds = [42, 123, 7, 99, 256, 314, 500, 777, 1000, 2024]

    # Configurations to test:
    # (enable_feature_filtering, feature_filter_after, keep_top_k_features)
    configs = [
        # Baseline: no filtering
        (False, 999, None, "No filtering"),
        # filter_after=8 (right after init)
        (True, 8, None, "after=8, k=auto"),
        (True, 8, 3, "after=8, k=3"),
        (True, 8, 5, "after=8, k=5"),
        (True, 8, 7, "after=8, k=7"),
        (True, 8, 10, "after=8, k=10"),
        # filter_after=12
        (True, 12, None, "after=12, k=auto"),
        (True, 12, 3, "after=12, k=3"),
        (True, 12, 5, "after=12, k=5"),
        (True, 12, 7, "after=12, k=7"),
        (True, 12, 10, "after=12, k=10"),
        # filter_after=16
        (True, 16, None, "after=16, k=auto"),
        (True, 16, 5, "after=16, k=5"),
        (True, 16, 7, "after=16, k=7"),
    ]

    results = []
    for enable_ff, filter_after, top_k, label in configs:
        print(f"\n{'='*60}")
        print(f"  Config: {label}")
        print(f"{'='*60}")
        ranks = []
        for seed in seeds:
            r = run_one(candidates, available_cont, available_cat,
                        evaluator_args, oracle_df,
                        seed, enable_ff, filter_after, top_k)
            r["label"] = label
            results.append(r)
            ranks.append(r["selected_rank"])
            print(f"  seed={seed:>4d}  rank={r['selected_rank']:>2d}/65  "
                  f"model={r['selected_model']}", flush=True)

        ranks = np.array(ranks)
        print(f"  => mean={ranks.mean():.1f}  median={np.median(ranks):.1f}  "
              f"best={ranks.min()}  worst={ranks.max()}  "
              f"top5={np.sum(ranks<=5)}/10  oracle={np.sum(ranks==1)}/10")

    # Summary table
    print(f"\n\n{'='*80}")
    print(f"  SUMMARY")
    print(f"{'='*80}")
    print(f"{'Config':<22s} {'Mean':>5s} {'Med':>4s} {'Best':>4s} {'Worst':>5s} {'Top5':>4s} {'#1':>3s}")
    print("-" * 55)

    df = pd.DataFrame(results)
    for label in df["label"].unique():
        sub = df[df["label"] == label]
        ranks = sub["selected_rank"].values
        print(f"{label:<22s} {ranks.mean():>5.1f} {np.median(ranks):>4.1f} "
              f"{ranks.min():>4d} {ranks.max():>5d} "
              f"{np.sum(ranks<=5):>4d} {np.sum(ranks==1):>3d}")

    # Save raw results
    out_path = os.path.join(os.path.dirname(__file__), "ablation_feature_filter_results.csv")
    df.to_csv(out_path, index=False)
    print(f"\nRaw results saved to {out_path}")


if __name__ == "__main__":
    main()
