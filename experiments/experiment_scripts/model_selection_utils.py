"""Shared model-selection helpers.

Small, dependency-light utilities used by the top-level ``model_selection/``
research package (pareto_frontier_search.py + its analysis/plot scripts) to
load the model-profile pool and read Q-error CDF CSVs.

These were originally defined in ``model_selection_v2.py``. That prototype was
archived to ``experiments/_archive/model_selection_v2/`` (superseded by the
Pareto/round-based framework in ``analyze_overall.sh`` → ``compare_round_pareto.py``),
so the still-live ``model_selection/`` scripts now import these helpers from
here instead of from the archived file.
"""
from __future__ import annotations

import glob
import os
from typing import Dict, Optional

import pandas as pd

# Workload -> training workload mapping (matches run_model_selection.sh / the
# canonical-imdb mapping: syn and job_full both train on the job workload).
TRAIN_WORKLOAD_MAP = {
    "syn": "job",
    "job_full": "job",
}


def find_cdf_file(model: str, args) -> Optional[str]:
    """Locate the CDF CSV produced by run_different_llms.sh mode 1.

    `args` must expose: workload, db, embed_size.
    """
    model_safe = model.replace("/", "-")
    train_wl = TRAIN_WORKLOAD_MAP.get(args.workload, args.workload)
    results_base = (
        f"results/{args.db}/results_Train_{train_wl}_Test_{args.workload}_ours"
    )
    pattern = (
        f"{results_base}/time_llm_pretrained-None_1.0_cdf_{args.db}_*"
        f"_{model_safe}_emb{args.embed_size}*_seed42.csv"
    )
    matches = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
    return matches[0] if matches else None


def parse_qerror(csv_path: str) -> Dict[str, float]:
    """Parse Q-error percentiles {p50, p90, p95, max} from a CDF CSV."""
    df = pd.read_csv(csv_path).sort_values("percentage")
    result = {}
    for q in [50, 90, 95]:
        sub = df[df["percentage"] >= q]
        if not sub.empty:
            result[f"p{q}"] = float(sub.iloc[0]["Qerror"])
        else:
            result[f"p{q}"] = float(df["Qerror"].max())
    result["max"] = float(df["Qerror"].max())
    return result


def load_candidates(csv_path: str) -> pd.DataFrame:
    """Load the model profile CSV and prepare features (status=ok rows only)."""
    df = pd.read_csv(csv_path)

    # Filter to status=ok only
    if "status" in df.columns:
        df = df[df["status"] == "ok"].copy()

    # Convert boolean strings to 0/1
    bool_cols = [
        "is_embedding_tuned", "is_instruction_tuned", "is_multilingual",
        "is_cased", "deduped_variant",
    ]
    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].map({"True": 1, "False": 0, True: 1, False: 0}).fillna(0).astype(int)

    # Ensure numeric columns are numeric
    numeric_cols = [
        "non_embedding_params", "embedding_params", "total_params",
        "num_layers", "hidden_size", "attention_heads", "ffn_width",
        "context_length", "embedding_dimension", "avg_ms",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop rows with missing essential fields
    df = df.dropna(subset=["model", "avg_ms", "non_embedding_params"])

    return df.reset_index(drop=True)
