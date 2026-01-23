"""
Test script to compare embeddings from different LLM models.

This script:
1. Loads embeddings from different LLM models for a given dataset/task
2. Compares them pairwise using CKA
3. Checks if sample-wise norms are identical (which would be suspicious)
4. Reports findings about embedding similarity

Usage:
    python test_embedding_similarity.py --dataset job --task card --seed 42
"""

import argparse
import pandas as pd
import numpy as np
from pathlib import Path


def linear_cka(Z: np.ndarray, M: np.ndarray) -> float:
    """
    Linear CKA between two representations Z and M.

    Z: (n_samples, d_z)  – e.g., LLM embeddings
    M: (n_samples, d_m)  – e.g., metric vectors or other embeddings

    Returns:
        scalar in [0, 1]-ish range (higher = more similar structure).
    """
    assert Z.shape[0] == M.shape[0], f"Z and M must have same number of samples: {Z.shape[0]} vs {M.shape[0]}"
    Zc = Z - Z.mean(axis=0, keepdims=True)
    Mc = M - M.mean(axis=0, keepdims=True)
    ZtM = Zc.T @ Mc
    numerator = np.linalg.norm(ZtM, ord="fro") ** 2
    denom = (np.linalg.norm(Zc.T @ Zc, ord="fro") * np.linalg.norm(Mc.T @ Mc, ord="fro"))
    if denom == 0:
        return 0.0
    return numerator / denom


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare embeddings from different LLM models"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="job",
        help="Dataset name (e.g., 'job', 'stats', 'syn')",
    )
    parser.add_argument(
        "--task",
        type=str,
        default="card",
        choices=["card", "time"],
        help="Task type ('card' or 'time')",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Seed to filter verbose CSVs",
    )
    parser.add_argument(
        "--verbose_root",
        type=Path,
        default=None,
        help="Verbose root directory (default: experiments/verbose)",
    )
    parser.add_argument(
        "--max_models",
        type=int,
        default=5,
        help="Maximum number of models to compare (default: 5)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    
    # Set up paths
    if args.verbose_root is None:
        verbose_root = Path(__file__).resolve().parents[2] / "verbose"
    else:
        verbose_root = args.verbose_root
    
    verbose_dir = verbose_root / f"verbose_Train_{args.dataset}_Test_{args.dataset}_ours"
    if not verbose_dir.exists():
        print(f"Error: Directory not found: {verbose_dir}")
        return
    
    # Find LLM model verbose files
    pattern = f"{args.task}_llm_*seed{args.seed}*.csv"
    llm_files = []
    for f in sorted(verbose_dir.glob(pattern)):
        if "_rm-" not in f.name and "downstream" not in f.name:
            llm_files.append(f)
    
    if len(llm_files) == 0:
        print(f"Error: No LLM model files found matching pattern '{pattern}' in {verbose_dir}")
        return
    
    print(f"Found {len(llm_files)} LLM model files")
    print(f"Will compare up to {args.max_models} models\n")
    
    # Load embeddings from models
    embeddings_data = {}
    for f in llm_files[:args.max_models]:
        try:
            vdf = pd.read_csv(f)
            if "embedding_file" not in vdf.columns:
                print(f"  {f.name}: No embedding_file column")
                continue
            
            embed_path = vdf["embedding_file"].dropna().iloc[0] if not vdf["embedding_file"].dropna().empty else None
            if embed_path is None:
                print(f"  {f.name}: No embedding file path")
                continue
            
            embed_path = Path(embed_path)
            if not embed_path.is_absolute():
                embed_path = (verbose_root.parent / embed_path).resolve()
            
            if not embed_path.exists():
                print(f"  {f.name}: Embedding file not found: {embed_path}")
                continue
            
            # Extract model name
            model_name = f.stem.replace(f"{args.task}_llm_pretrained-None_1.0_postgres_0.0001_b64_h2048_", "").replace("_emb1000_quant-4-bit_seed42", "")
            
            # Load embeddings
            embed_df = pd.read_csv(embed_path)
            if "idx" in embed_df.columns:
                embed_df = embed_df.set_index("idx")
            
            # Get embedding columns: columns with integer names (string representation of integer)
            # Exclude known non-embedding columns: costs, cards, lengths, idx
            excluded_cols = {"costs", "cards", "lengths", "idx"}
            embedding_cols = []
            for col in embed_df.columns:
                if col in excluded_cols:
                    continue
                # Check if column name is an integer (string representation of integer)
                if str(col).isdigit():
                    embedding_cols.append(col)
            
            if not embedding_cols:
                print(f"  {model_name}: Warning - no embedding columns found (only excluded columns)")
                continue
            
            Z = embed_df[embedding_cols].to_numpy(dtype=float)
            
            embeddings_data[model_name] = {
                'Z': Z,
                'embed_path': str(embed_path),
                'shape': Z.shape
            }
            print(f"  {model_name[:50]:<50}: shape={Z.shape}, file={Path(embed_path).name[:60]}")
        except Exception as e:
            print(f"  {f.name}: Error loading - {e}")
            continue
    
    if len(embeddings_data) < 2:
        print(f"\nError: Need at least 2 models to compare, but only found {len(embeddings_data)}")
        return
    
    print(f"\nLoaded {len(embeddings_data)} embedding files\n")
    
    # Compare embeddings pairwise
    models = list(embeddings_data.keys())
    print("=" * 100)
    print("PAIRWISE COMPARISON OF EMBEDDINGS")
    print("=" * 100)
    
    for i, model1 in enumerate(models):
        for model2 in models[i+1:]:
            Z1 = embeddings_data[model1]['Z']
            Z2 = embeddings_data[model2]['Z']
            
            # Align by number of samples
            min_samples = min(Z1.shape[0], Z2.shape[0])
            Z1_aligned = Z1[:min_samples]
            Z2_aligned = Z2[:min_samples]
            
            print(f"\n{model1[:40]:<40} vs {model2[:40]:<40}")
            print(f"  Shapes: {Z1_aligned.shape} vs {Z2_aligned.shape}")
            
            # Compute CKA between the two embeddings
            cka = linear_cka(Z1_aligned, Z2_aligned)
            print(f"  CKA: {cka:.15f}")
            
            # Compute sample-wise norms
            norms1 = np.linalg.norm(Z1_aligned, axis=1)
            norms2 = np.linalg.norm(Z2_aligned, axis=1)
            
            norm_diff = np.abs(norms1 - norms2)
            print(f"  Sample-wise norms:")
            print(f"    Model1: mean={norms1.mean():.10f}, std={norms1.std():.10f}")
            print(f"    Model2: mean={norms2.mean():.10f}, std={norms2.std():.10f}")
            print(f"    Difference: mean={norm_diff.mean():.15f}, max={norm_diff.max():.15f}")
            print(f"    Are norms identical? {np.allclose(norms1, norms2, atol=1e-10)}")
            
            # Compare embedding statistics
            print(f"  Embedding statistics:")
            print(f"    Model1: mean={Z1_aligned.mean():.6f}, std={Z1_aligned.std():.6f}, min={Z1_aligned.min():.6f}, max={Z1_aligned.max():.6f}")
            print(f"    Model2: mean={Z2_aligned.mean():.6f}, std={Z2_aligned.std():.6f}, min={Z2_aligned.min():.6f}, max={Z2_aligned.max():.6f}")
            
            # Check first few samples
            print(f"  First 3 sample norms:")
            for j in range(min(3, len(norms1))):
                print(f"    Sample {j}: Model1={norms1[j]:.10f}, Model2={norms2[j]:.10f}, Diff={abs(norms1[j] - norms2[j]):.15f}")
    
    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print("If CKA ≈ 1.0 between different embeddings, they have very similar structure.")
    print("If sample-wise norms are identical, this suggests:")
    print("  - Embeddings might be normalized to have the same per-sample norm")
    print("  - Or there's a bug in embedding generation/normalization")
    print("  - Or embeddings are computed from the same underlying representation")


if __name__ == "__main__":
    main()

