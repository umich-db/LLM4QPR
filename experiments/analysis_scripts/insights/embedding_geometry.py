"""
Geometry diagnostics for embedding spaces (G1–G5).

All functions accept a 2D numpy array ``Z`` with shape (n_samples, dim).
By default the vectors are mean-centered and L2-normalised before computing
metrics, matching the analysis recipe shared by the user.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np

try:
    import torch

    _TORCH_AVAILABLE = torch.cuda.is_available()
    _TORCH_DEVICE = torch.device("cuda") if _TORCH_AVAILABLE else None
except ImportError:  # pragma: no cover - torch optional
    torch = None
    _TORCH_AVAILABLE = False
    _TORCH_DEVICE = None


def _center_l2_numpy(
    Z: np.ndarray, center: bool = True, l2: bool = True
) -> Tuple[np.ndarray, Dict[str, float]]:
    """
    Mean-center and L2-normalise row vectors.

    Returns the processed matrix and simple norm statistics.
    """
    Z = np.asarray(Z, dtype=float)
    if Z.ndim != 2:
        raise ValueError("Embeddings must have shape (n_samples, dim)")

    n, _ = Z.shape
    pre_norms = np.linalg.norm(Z, axis=1) + 1e-12
    Zc = Z - Z.mean(axis=0, keepdims=True) if center else Z.copy()
    norms = np.linalg.norm(Zc, axis=1) + 1e-12
    Zp = Zc / norms[:, None] if l2 else Zc

    stats = {
        "pre_norm_mean": float(pre_norms.mean()),
        "pre_norm_std": float(pre_norms.std(ddof=1)) if n > 1 else 0.0,
        "post_norm_mean": float(np.linalg.norm(Zp, axis=1).mean()),
        "post_norm_std": float(np.linalg.norm(Zp, axis=1).std(ddof=1))
        if n > 1
        else 0.0,
    }
    return Zp, stats


def _center_l2_torch(
    Z: np.ndarray, center: bool = True, l2: bool = True
) -> Tuple["torch.Tensor", Dict[str, float]]:
    if not _TORCH_AVAILABLE:
        raise RuntimeError("Torch with CUDA is not available for GPU acceleration.")

    Z_tensor = torch.as_tensor(Z, dtype=torch.float32, device=_TORCH_DEVICE)
    if Z_tensor.ndim != 2:
        raise ValueError("Embeddings must have shape (n_samples, dim)")

    n = Z_tensor.shape[0]
    pre_norms = torch.linalg.norm(Z_tensor, dim=1) + 1e-12
    if center:
        mean = torch.mean(Z_tensor, dim=0, keepdim=True)
        Zc = Z_tensor - mean
    else:
        Zc = Z_tensor.clone()

    norms = torch.linalg.norm(Zc, dim=1) + 1e-12
    Zp = Zc / norms.unsqueeze(1) if l2 else Zc

    post_norms = torch.linalg.norm(Zp, dim=1)
    stats = {
        "pre_norm_mean": float(pre_norms.mean().item()),
        "pre_norm_std": float(torch.std(pre_norms, unbiased=True).item()) if n > 1 else 0.0,
        "post_norm_mean": float(post_norms.mean().item()),
        "post_norm_std": float(torch.std(post_norms, unbiased=True).item()) if n > 1 else 0.0,
    }
    return Zp, stats


def _use_torch_backend() -> bool:
    return _TORCH_AVAILABLE


def _center_l2(
    Z: np.ndarray, center: bool = True, l2: bool = True
) -> Tuple[np.ndarray | "torch.Tensor", Dict[str, float]]:
    if _use_torch_backend():
        return _center_l2_torch(Z, center=center, l2=l2)
    return _center_l2_numpy(Z, center=center, l2=l2)


def _sample_pairs(n: int, num_pairs: int, rng: np.random.Generator) -> np.ndarray:
    """Uniformly sample ``num_pairs`` index pairs (i, j) with i != j."""
    if num_pairs <= 0:
        raise ValueError("num_pairs must be positive")
    if n < 2:
        raise ValueError("Need at least two samples to form pairs")

    i = rng.integers(0, n, size=num_pairs)
    j = rng.integers(0, n - 1, size=num_pairs)
    j = j + (j >= i)  # skip diagonal entries
    return np.stack([i, j], axis=1)


def _eigs_from_cov(X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Eigen-decompose C = X^T X / (n-1).

    Returns eigenvalues (descending) and eigenvectors (columns).
    """
    n = X.shape[0]
    if n <= 1:
        raise ValueError("Need at least two samples to compute covariance")

    # Handle NaN values: replace with 0
    X = np.where(np.isnan(X), 0.0, X)
    
    # Remove constant columns (zero variance) to avoid ill-conditioned covariance matrix
    col_stds = np.std(X, axis=0)
    non_constant_mask = col_stds > 1e-10
    if non_constant_mask.sum() == 0:
        # All columns are constant, return dummy eigenvalues/eigenvectors
        return np.array([1.0]), np.ones((X.shape[1], 1))
    
    X = X[:, non_constant_mask]

    C = (X.T @ X) / max(n - 1, 1)
    
    # Use try-except to handle potential convergence issues
    try:
        w, V = np.linalg.eigh(C)  # ascending order
    except np.linalg.LinAlgError as e:
        if "singular" in str(e).lower() or "ill-conditioned" in str(e).lower():
            # If eigenvalue decomposition fails, try with regularization
            C_reg = C + np.eye(C.shape[0]) * 1e-6
            w, V = np.linalg.eigh(C_reg)
        else:
            raise
    
    idx = np.argsort(w)[::-1]
    return w[idx], V[:, idx]


def _g1_mean_cosine_numpy(
    Z: np.ndarray,
    num_pairs: int = 200_000,
    seed: int = 0,
    center: bool = True,
    l2: bool = True,
) -> Dict[str, float]:
    """
    G1: Mean pairwise cosine (and std) over sampled pairs.
    After centering + L2, healthy spaces tend to have mean cosine close to 0.
    """
    # Handle NaN values: replace with 0
    Z = np.where(np.isnan(Z), 0.0, Z)
    
    Zp, _ = _center_l2(Z, center=center, l2=l2)
    n = Zp.shape[0]
    max_pairs = max(n * (n - 1) // 2, 1)
    num_pairs = int(min(num_pairs, max_pairs))

    rng = np.random.default_rng(seed)
    pairs = _sample_pairs(n, num_pairs, rng)
    cos = np.sum(Zp[pairs[:, 0]] * Zp[pairs[:, 1]], axis=1)

    return {
        "metric": "G1",
        "mean_cosine": float(cos.mean()),
        "std_cosine": float(cos.std(ddof=1)) if cos.size > 1 else 0.0,
        "num_pairs": int(cos.size),
    }


def _g1_mean_cosine_torch(
    Z: np.ndarray,
    num_pairs: int = 200_000,
    seed: int = 0,
    center: bool = True,
    l2: bool = True,
) -> Dict[str, float]:
    # Handle NaN values: replace with 0
    Z = np.where(np.isnan(Z), 0.0, Z)
    
    Zp, _ = _center_l2_torch(Z, center=center, l2=l2)
    n = Zp.shape[0]
    max_pairs = max(n * (n - 1) // 2, 1)
    num_pairs = int(min(num_pairs, max_pairs))

    rng = np.random.default_rng(seed)
    pairs = _sample_pairs(n, num_pairs, rng)
    idx_i = torch.as_tensor(pairs[:, 0], device=Zp.device, dtype=torch.long)
    idx_j = torch.as_tensor(pairs[:, 1], device=Zp.device, dtype=torch.long)
    cos = torch.sum(Zp[idx_i] * Zp[idx_j], dim=1)
    mean_cos = float(cos.mean().item())
    std_cos = float(torch.std(cos, unbiased=True).item()) if cos.numel() > 1 else 0.0

    return {
        "metric": "G1",
        "mean_cosine": mean_cos,
        "std_cosine": std_cos,
        "num_pairs": int(cos.numel()),
    }


def g1_mean_cosine(
    Z: np.ndarray,
    num_pairs: int = 200_000,
    seed: int = 0,
    center: bool = True,
    l2: bool = True,
) -> Dict[str, float]:
    if _use_torch_backend():
        return _g1_mean_cosine_torch(Z, num_pairs=num_pairs, seed=seed, center=center, l2=l2)
    return _g1_mean_cosine_numpy(Z, num_pairs=num_pairs, seed=seed, center=center, l2=l2)


def _g2_mcc_evr1_erank_numpy(
    Z: np.ndarray, center: bool = True, l2: bool = True
) -> Dict[str, float]:
    Zp, _ = _center_l2_numpy(Z, center=center, l2=l2)
    
    # Handle NaN values: replace with 0
    Zp = np.where(np.isnan(Zp), 0.0, Zp)
    
    Zc = Zp - Zp.mean(axis=0, keepdims=True) if center else Zp.copy()

    w, V = _eigs_from_cov(Zc)
    
    # If all columns were constant, _eigs_from_cov returns dummy values
    # Check if we have valid eigenvalues
    if len(w) == 0 or np.all(w <= 1e-10):
        return {"metric": "G2", "MCC": 0.0, "EVR1": 1.0, "effective_rank": 1.0}
    
    total = float(np.sum(w)) + 1e-12
    evr1 = float(w[0] / total) if total > 0 else 0.0
    p = w / total if total > 0 else np.ones_like(w) / len(w)
    p = np.clip(p, 1e-12, 1.0)
    erank = float(np.exp(-np.sum(p * np.log(p))))

    v1 = V[:, 0]
    mcc = float(np.mean(np.abs(Zp @ v1)))

    return {"metric": "G2", "MCC": mcc, "EVR1": evr1, "effective_rank": erank}


def _g2_mcc_evr1_erank_torch(
    Z: np.ndarray, center: bool = True, l2: bool = True
) -> Dict[str, float]:
    Zp, _ = _center_l2_torch(Z, center=center, l2=l2)
    
    # Handle NaN values: replace with 0
    Zp = torch.where(torch.isnan(Zp), torch.zeros_like(Zp), Zp)
    
    if center:
        mean = torch.mean(Zp, dim=0, keepdim=True)
        Zc = Zp - mean
    else:
        Zc = Zp.clone()

    n = Zc.shape[0]
    if n <= 1:
        raise ValueError("Need at least two samples to compute covariance")

    # Remove constant columns (zero variance) to avoid ill-conditioned covariance matrix
    col_stds = torch.std(Zc, dim=0)
    non_constant_mask = col_stds > 1e-10
    if non_constant_mask.sum() == 0:
        # All columns are constant, return default values
        return {"metric": "G2", "MCC": 0.0, "EVR1": 1.0, "effective_rank": 1.0}
    
    Zc = Zc[:, non_constant_mask]
    Zp = Zp[:, non_constant_mask]

    C = torch.matmul(Zc.T, Zc) / max(n - 1, 1)
    
    # Use try-except to handle potential convergence issues
    try:
        w, V = torch.linalg.eigh(C)
    except RuntimeError as e:
        if "converge" in str(e) or "ill-conditioned" in str(e).lower():
            # If eigenvalue decomposition fails, try with regularization
            C_reg = C + torch.eye(C.shape[0], device=C.device, dtype=C.dtype) * 1e-6
            w, V = torch.linalg.eigh(C_reg)
        else:
            raise
    idx = torch.argsort(w, descending=True)
    w = w[idx]
    V = V[:, idx]
    total = torch.sum(w) + 1e-12
    evr1 = float((w[0] / total).item()) if total > 0 else 0.0
    if total > 0:
        p = w / total
    else:
        p = torch.full_like(w, 1.0 / w.numel())
    p = torch.clamp(p, 1e-12, 1.0)
    erank = float(torch.exp(-torch.sum(p * torch.log(p))).item())
    v1 = V[:, 0]
    projections = torch.abs(torch.matmul(Zp, v1))
    mcc = float(projections.mean().item())
    return {"metric": "G2", "MCC": mcc, "EVR1": evr1, "effective_rank": erank}


def g2_mcc_evr1_erank(
    Z: np.ndarray, center: bool = True, l2: bool = True
) -> Dict[str, float]:
    """
    G2: Top-component dominance.
      - MCC: mean |projection on PC1|.
      - EVR1: explained variance ratio of PC1.
      - Effective rank: exp(entropy(eigvals / sum)).
    """
    if _use_torch_backend():
        return _g2_mcc_evr1_erank_torch(Z, center=center, l2=l2)
    return _g2_mcc_evr1_erank_numpy(Z, center=center, l2=l2)


def _g3_uniformity_numpy(
    Z: np.ndarray,
    t: float = 2.0,
    num_pairs: int = 200_000,
    seed: int = 0,
    center: bool = True,
    l2: bool = True,
) -> Dict[str, float]:
    """
    G3: Uniformity (Wang & Isola, 2020).
    uniformity = log E[ exp( - t * ||zi - zj||^2 ) ] for sampled pairs.
    Lower is better (more evenly spread representations).
    """
    Zp, _ = _center_l2(Z, center=center, l2=l2)
    n = Zp.shape[0]
    max_pairs = max(n * (n - 1) // 2, 1)
    num_pairs = int(min(num_pairs, max_pairs))

    rng = np.random.default_rng(seed)
    pairs = _sample_pairs(n, num_pairs, rng)
    cos = np.sum(Zp[pairs[:, 0]] * Zp[pairs[:, 1]], axis=1)
    dist2 = 2.0 - 2.0 * cos  # because vectors are L2-normalised

    vals = -t * dist2
    a = np.max(vals)
    uniformity = float(a + np.log(np.mean(np.exp(vals - a))))

    return {"metric": "G3", "uniformity": uniformity, "t": float(t), "num_pairs": int(num_pairs)}


def _g3_uniformity_torch(
    Z: np.ndarray,
    t: float = 2.0,
    num_pairs: int = 200_000,
    seed: int = 0,
    center: bool = True,
    l2: bool = True,
) -> Dict[str, float]:
    Zp, _ = _center_l2_torch(Z, center=center, l2=l2)
    n = Zp.shape[0]
    max_pairs = max(n * (n - 1) // 2, 1)
    num_pairs = int(min(num_pairs, max_pairs))

    rng = np.random.default_rng(seed)
    pairs = _sample_pairs(n, num_pairs, rng)
    idx_i = torch.as_tensor(pairs[:, 0], device=Zp.device, dtype=torch.long)
    idx_j = torch.as_tensor(pairs[:, 1], device=Zp.device, dtype=torch.long)
    cos = torch.sum(Zp[idx_i] * Zp[idx_j], dim=1)
    dist2 = 2.0 - 2.0 * cos
    vals = -t * dist2
    a = torch.max(vals)
    uniformity = float((a + torch.log(torch.mean(torch.exp(vals - a)))).item())
    return {"metric": "G3", "uniformity": uniformity, "t": float(t), "num_pairs": int(num_pairs)}


def g3_uniformity(
    Z: np.ndarray,
    t: float = 2.0,
    num_pairs: int = 200_000,
    seed: int = 0,
    center: bool = True,
    l2: bool = True,
) -> Dict[str, float]:
    if _use_torch_backend():
        return _g3_uniformity_torch(Z, t=t, num_pairs=num_pairs, seed=seed, center=center, l2=l2)
    return _g3_uniformity_numpy(Z, t=t, num_pairs=num_pairs, seed=seed, center=center, l2=l2)


def _gini(x: np.ndarray) -> float:
    """Gini coefficient in [0, 1]; 0 == perfectly equal."""
    x = np.asarray(x, dtype=float).ravel()
    if x.size == 0 or np.all(x == 0):
        return 0.0
    x = np.sort(x)
    n = x.size
    cumx = np.cumsum(x)
    return float((n + 1 - 2 * (cumx.sum() / cumx[-1])) / n)


def _g4_hubness_numpy(
    Z: np.ndarray,
    k: int = 10,
    max_samples: int = 5000,
    seed: int = 0,
    center: bool = True,
    l2: bool = True,
) -> Dict[str, float]:
    Zp, _ = _center_l2_numpy(Z, center=center, l2=l2)
    rng = np.random.default_rng(seed)
    n = Zp.shape[0]
    if n == 0:
        raise ValueError("No embeddings available for hubness computation")

    if n > max_samples:
        idx = rng.choice(n, size=max_samples, replace=False)
        Zp = Zp[idx]
        n = Zp.shape[0]

    if n < 2:
        raise ValueError("Need at least two embeddings for hubness")

    S = Zp @ Zp.T
    np.fill_diagonal(S, -np.inf)
    k_eff = int(min(max(k, 1), n - 1))

    nn_idx = np.argpartition(S, -k_eff, axis=1)[:, -k_eff:]
    counts = np.zeros(n, dtype=int)
    for row in nn_idx:
        counts[row] += 1

    return {
        "metric": "G4",
        "hubness_gini": float(_gini(counts)),
        "k": k_eff,
        "n_eval": int(n),
        "counts_mean": float(counts.mean()),
        "counts_std": float(counts.std(ddof=1)) if n > 1 else 0.0,
        "counts_min": int(counts.min()) if n > 0 else 0,
        "counts_max": int(counts.max()) if n > 0 else 0,
    }


def _g4_hubness_torch(
    Z: np.ndarray,
    k: int = 10,
    max_samples: int = 5000,
    seed: int = 0,
    center: bool = True,
    l2: bool = True,
) -> Dict[str, float]:
    Zp, _ = _center_l2_torch(Z, center=center, l2=l2)
    n = Zp.shape[0]
    if n == 0:
        raise ValueError("No embeddings available for hubness computation")

    if n > max_samples:
        if seed is not None:
            torch.manual_seed(seed)
        perm = torch.randperm(n, device=Zp.device)
        idx = perm[: max_samples]
        Zp = Zp[idx]
        n = Zp.shape[0]

    if n < 2:
        raise ValueError("Need at least two embeddings for hubness")

    S = torch.matmul(Zp, Zp.T)
    S.fill_diagonal_(-float("inf"))
    k_eff = int(min(max(k, 1), n - 1))
    _, nn_idx = torch.topk(S, k_eff, dim=1)
    counts = torch.bincount(nn_idx.reshape(-1), minlength=n)
    counts_cpu = counts.to("cpu").numpy()

    return {
        "metric": "G4",
        "hubness_gini": float(_gini(counts_cpu)),
        "k": k_eff,
        "n_eval": int(n),
        "counts_mean": float(counts_cpu.mean()),
        "counts_std": float(counts_cpu.std(ddof=1)) if counts_cpu.size > 1 else 0.0,
        "counts_min": int(counts_cpu.min()) if counts_cpu.size > 0 else 0,
        "counts_max": int(counts_cpu.max()) if counts_cpu.size > 0 else 0,
    }


def g4_hubness(
    Z: np.ndarray,
    k: int = 10,
    max_samples: int = 5000,
    seed: int = 0,
    center: bool = True,
    l2: bool = True,
) -> Dict[str, float]:
    """
    G4: Hubness via kNN neighbour occurrence counts (cosine similarity).
    Subsamples up to ``max_samples`` points for tractability.
    """
    if _use_torch_backend():
        return _g4_hubness_torch(
            Z, k=k, max_samples=max_samples, seed=seed, center=center, l2=l2
        )
    return _g4_hubness_numpy(
        Z, k=k, max_samples=max_samples, seed=seed, center=center, l2=l2
    )


def _g5_norm_stats_numpy(Z: np.ndarray, center: bool = True, l2: bool = True) -> Dict[str, float]:
    Z = np.asarray(Z, dtype=float)
    if Z.ndim != 2:
        raise ValueError("Embeddings must have shape (n_samples, dim)")

    pre = np.linalg.norm(Z, axis=1) + 1e-12
    Zp, _ = _center_l2_numpy(Z, center=center, l2=l2)
    post = np.linalg.norm(Zp, axis=1) + 1e-12

    return {
        "metric": "G5",
        "pre_norm_mean": float(pre.mean()),
        "pre_norm_std": float(pre.std(ddof=1)) if Z.shape[0] > 1 else 0.0,
        "pre_norm_min": float(pre.min()),
        "pre_norm_max": float(pre.max()),
        "post_norm_mean": float(post.mean()),
        "post_norm_std": float(post.std(ddof=1)) if Z.shape[0] > 1 else 0.0,
        "post_norm_min": float(post.min()),
        "post_norm_max": float(post.max()),
    }


def _g5_norm_stats_torch(Z: np.ndarray, center: bool = True, l2: bool = True) -> Dict[str, float]:
    if not _TORCH_AVAILABLE:
        raise RuntimeError("Torch with CUDA support is required for GPU execution.")

    Z_tensor = torch.as_tensor(Z, dtype=torch.float32, device=_TORCH_DEVICE)
    if Z_tensor.ndim != 2:
        raise ValueError("Embeddings must have shape (n_samples, dim)")

    pre = torch.linalg.norm(Z_tensor, dim=1) + 1e-12
    Zp, _ = _center_l2_torch(Z, center=center, l2=l2)
    post = torch.linalg.norm(Zp, dim=1) + 1e-12

    def _torch_stat(vec, fn, default=0.0):
        if vec.numel() <= 1 and fn is torch.std:
            return default
        return float(fn(vec).item())

    return {
        "metric": "G5",
        "pre_norm_mean": float(pre.mean().item()),
        "pre_norm_std": float(torch.std(pre, unbiased=True).item()) if pre.numel() > 1 else 0.0,
        "pre_norm_min": float(pre.min().item()),
        "pre_norm_max": float(pre.max().item()),
        "post_norm_mean": float(post.mean().item()),
        "post_norm_std": float(torch.std(post, unbiased=True).item()) if post.numel() > 1 else 0.0,
        "post_norm_min": float(post.min().item()),
        "post_norm_max": float(post.max().item()),
    }


def g5_norm_stats(Z: np.ndarray, center: bool = True, l2: bool = True) -> Dict[str, float]:
    """
    G5: Norm sanity (before/after processing). Spectrum sanity is covered by G2.
    """
    if _use_torch_backend():
        return _g5_norm_stats_torch(Z, center=center, l2=l2)
    return _g5_norm_stats_numpy(Z, center=center, l2=l2)


def all_geometry_metrics(
    Z: np.ndarray,
    num_pairs: int = 200_000,
    uniformity_t: float = 2.0,
    knn_k: int = 10,
    max_samples_for_knn: int = 5000,
    seed: int = 0,
    center: bool = True,
    l2: bool = True,
) -> Dict[str, float]:
    """
    Convenience wrapper to compute G1–G5 in a single call.
    """
    out: Dict[str, float] = {}
    out.update(
        g1_mean_cosine(
            Z, num_pairs=num_pairs, seed=seed, center=center, l2=l2
        )
    )
    out.update(g2_mcc_evr1_erank(Z, center=center, l2=l2))
    out.update(
        g3_uniformity(
            Z,
            t=uniformity_t,
            num_pairs=num_pairs,
            seed=seed,
            center=center,
            l2=l2,
        )
    )
    out.update(
        g4_hubness(
            Z,
            k=knn_k,
            max_samples=max_samples_for_knn,
            seed=seed,
            center=center,
            l2=l2,
        )
    )
    out.update(g5_norm_stats(Z, center=center, l2=l2))
    return out


GEOMETRY_FUNCTIONS = {
    "g1": g1_mean_cosine,
    "g2": g2_mcc_evr1_erank,
    "g3": g3_uniformity,
    "g4": g4_hubness,
    "g5": g5_norm_stats,
    "all": all_geometry_metrics,
}


@dataclass
class GeometryConfig:
    num_pairs: int = 200_000
    uniformity_t: float = 2.0
    knn_k: int = 10
    max_samples_for_knn: int = 5000
    seed: int = 0
    center: bool = True
    l2: bool = True


def run_geometry_metric(Z: np.ndarray, metric: str, cfg: GeometryConfig) -> Dict[str, float]:
    """
    Execute one of the registered geometry metrics with the provided config.
    """
    metric = metric.lower()
    if metric not in GEOMETRY_FUNCTIONS:
        raise ValueError(f"Unsupported geometry metric '{metric}'")

    fn = GEOMETRY_FUNCTIONS[metric]
    kwargs = {}
    if metric in {"g1", "g3"}:
        kwargs["num_pairs"] = cfg.num_pairs
    if metric == "g3":
        kwargs["t"] = cfg.uniformity_t
    if metric in {"g1", "g3", "g4"}:
        kwargs["seed"] = cfg.seed
    if metric == "g4":
        kwargs["k"] = cfg.knn_k
        kwargs["max_samples"] = cfg.max_samples_for_knn
    if metric == "all":
        kwargs["num_pairs"] = cfg.num_pairs
        kwargs["uniformity_t"] = cfg.uniformity_t
        kwargs["knn_k"] = cfg.knn_k
        kwargs["max_samples_for_knn"] = cfg.max_samples_for_knn
        kwargs["seed"] = cfg.seed

    kwargs["center"] = cfg.center
    kwargs["l2"] = cfg.l2

    return fn(Z, **kwargs)

