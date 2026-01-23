"""
Utilities for extracting structural statistics and lightweight distances from
PostgreSQL query plans that are stored as JSON blobs inside the plan CSVs.

The helpers focus on:
  * Counting tables, columns, joins, and filters.
  * Building operator histograms (bags of operators).
  * Building path n-gram inventories for local-structure comparisons.
  * Computing operator-multiset (L1/L2) distances.
  * Computing path n-gram cosine distances (TF or TF-IDF).

Example usage:

    from pathlib import Path
    from plan_structural_metrics import (
        load_plan_json,
        summarise_plan_structure,
        operator_multiset_distance,
        path_ngram_distance,
    )

    plan = load_plan_json("queryPlans/imdb/postgres/long_raw_postgres_imdb_job_full.csv", plan_id=100070)
    summary = summarise_plan_structure(plan)
    print(summary.num_tables, summary.num_columns, summary.num_joins, summary.num_filters)

"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from math import sqrt
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

import pandas as pd


@dataclass
class PlanStructuralSummary:
    # Original metrics (kept for backward compatibility)
    num_tables: int
    num_columns: int
    num_joins: int
    num_filters: int
    operator_histogram: Counter[str]
    path_ngrams: Counter[Tuple[str, ...]]
    longest_path_len: int
    # New enriched metrics (15 total)
    num_nodes: int
    join_tree_diameter: int
    num_blocking_ops: int
    num_nested_loop: int
    max_est_join_input_rows: float
    sum_est_join_input_rows: float
    num_highly_selective_filters: int
    log_filter_selectivity_product: float
    optimizer_est_cost_root: float
    log_max_est_rows: float
    log_sum_est_rows: float
    max_log_card_error: float


# ---------------------------------------------------------------------------
# Loading and traversal helpers
# ---------------------------------------------------------------------------


def load_plan_json(plan_csv: str | Path, plan_id: int | None = None) -> Dict:
    """
    Load a single plan (JSON dict) from a long_* CSV file.

    Args:
        plan_csv: Path to the CSV file containing columns ["id", "json"].
        plan_id: Optional integer id. If omitted, the first row is used.
    """
    plan_csv = Path(plan_csv)
    df = pd.read_csv(plan_csv)
    if plan_id is None:
        if len(df) != 1:
            raise ValueError(
                f"plan_id not provided and CSV has {len(df)} rows. "
                "Supply plan_id to disambiguate."
            )
        payload = df.iloc[0]["json"]
    else:
        subset = df[df["id"] == plan_id]
        if subset.empty:
            raise KeyError(f"Plan id {plan_id} not found in {plan_csv}")
        payload = subset.iloc[0]["json"]
    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to parse JSON for plan {plan_id}: {exc}") from exc


def _iter_nodes(plan: Dict) -> Iterator[Dict]:
    """Depth-first traversal of a Postgres plan tree. Yields every node dict in the plan."""
    stack = [plan]
    while stack:
        node = stack.pop()
        yield node
        for child in node.get("Plans", []) or []:
            stack.append(child)


def is_scan_node(node_type: str) -> bool:
    """
    Node types that represent base relations (tables/CTEs).
    """
    return node_type in {
        "Seq Scan", "Index Scan", "Index Only Scan",
        "Bitmap Heap Scan", "Bitmap Index Scan", "Tid Scan",
        "CTE Scan", "Subquery Scan", "Function Scan", "Values Scan",
        "Foreign Scan", "Custom Scan"
    }


def is_join_node(node_type: str) -> bool:
    """Check if node type is a join operator."""
    return node_type in {"Hash Join", "Merge Join", "Nested Loop"}


def is_blocking_node(node_type: str) -> bool:
    """
    Operators that typically block the pipeline / materialize.
    """
    return node_type in {
        "Sort", "Aggregate", "GroupAggregate", "HashAggregate",
        "Unique", "Materialize"
    }


def operator_type_counts(plan_root: Dict) -> Dict[str, int]:
    """
    Count occurrences of each Node Type in the plan.
    Returns: dict {node_type: count}
    """
    counts = defaultdict(int)
    for node in _iter_nodes(plan_root):
        nt = node.get("Node Type", "")
        counts[nt] += 1
    return dict(counts)


def _collect_paths(plan: Dict) -> List[List[str]]:
    paths: List[List[str]] = []

    def dfs(node: Dict, prefix: List[str]) -> None:
        token = node.get("Node Type", "Unknown")
        new_prefix = prefix + [token]
        children = node.get("Plans", []) or []
        if not children:
            paths.append(new_prefix)
        else:
            for child in children:
                dfs(child, new_prefix)

    dfs(plan, [])
    return paths


# ---------------------------------------------------------------------------
# Metric computation functions (15 metrics)
# ---------------------------------------------------------------------------


def num_nodes(plan_root: Dict) -> int:
    """Total number of operators (nodes) in the plan tree."""
    return sum(1 for _ in _iter_nodes(plan_root))


def longest_path(plan_root: Dict) -> int:
    """
    Height of the plan tree: length (in nodes) of the longest root→leaf path.
    """
    def depth(node: Dict) -> int:
        children = node.get("Plans", []) or []
        if not children:
            return 1
        return 1 + max(depth(child) for child in children)
    return depth(plan_root)


def tables_in_subtree(node: Dict) -> set[str]:
    """Set of base relation names reachable under this node."""
    tables = set()
    for n in _iter_nodes(node):
        if is_scan_node(n.get("Node Type", "")):
            rel = n.get("Relation Name") or n.get("Alias")
            if rel:
                tables.add(rel)
    return tables


def join_graph(plan_root: Dict) -> Dict[str, set[str]]:
    """
    Build an undirected join graph: nodes = tables, edges = join relationships.
    """
    adj = defaultdict(set)
    for node in _iter_nodes(plan_root):
        if is_join_node(node.get("Node Type", "")):
            children = node.get("Plans", []) or []
            if len(children) == 2:
                left_tables = tables_in_subtree(children[0])
                right_tables = tables_in_subtree(children[1])
                for lt in left_tables:
                    for rt in right_tables:
                        if lt != rt:
                            adj[lt].add(rt)
                            adj[rt].add(lt)
    return adj


def join_tree_diameter(plan_root: Dict) -> int:
    """
    Approximate diameter of the join graph (max shortest-path distance
    between any pair of tables).
    """
    adj = join_graph(plan_root)
    if not adj:
        return 0
    diameter = 0
    for start in adj.keys():
        dist = {start: 0}
        dq = deque([start])
        while dq:
            u = dq.popleft()
            for v in adj[u]:
                if v not in dist:
                    dist[v] = dist[u] + 1
                    dq.append(v)
        if dist:
            diameter = max(diameter, max(dist.values()))
    return diameter


def num_blocking_ops(plan_root: Dict) -> int:
    """Number of blocking operators (Sort, Aggregate, HashAggregate, Unique, Materialize)."""
    count = 0
    for node in _iter_nodes(plan_root):
        if is_blocking_node(node.get("Node Type", "")):
            count += 1
    return count


def num_nested_loop(plan_root: Dict) -> int:
    """Count of Nested Loop join operators."""
    return operator_type_counts(plan_root).get("Nested Loop", 0)


def join_input_rows(plan_root: Dict) -> List[float]:
    """Collect estimated child row counts for all join nodes."""
    rows = []
    for node in _iter_nodes(plan_root):
        if is_join_node(node.get("Node Type", "")):
            for child in node.get("Plans", []) or []:
                est = child.get("Plan Rows")
                if isinstance(est, (int, float)):
                    rows.append(float(est))
    return rows


def max_est_join_input_rows(plan_root: Dict) -> float:
    """Maximum estimated input rows across all join children."""
    rows = join_input_rows(plan_root)
    return max(rows) if rows else 0.0


def sum_est_join_input_rows(plan_root: Dict) -> float:
    """Sum of estimated join-input rows across all join nodes."""
    return sum(join_input_rows(plan_root))


def filter_selectivities(plan_root: Dict) -> List[float]:
    """
    Approximate actual selectivity for nodes with 'Rows Removed by Filter'.
    selectivity ≈ actual_rows / (actual_rows + rows_removed).
    """
    sels = []
    for node in _iter_nodes(plan_root):
        if "Rows Removed by Filter" in node:
            kept = node.get("Actual Rows")
            removed = node.get("Rows Removed by Filter")
            if isinstance(kept, (int, float)) and isinstance(removed, (int, float)):
                denom = kept + removed
                if denom > 0:
                    sels.append(kept / denom)
    return sels


def num_highly_selective_filters(plan_root: Dict, threshold: float = 0.01) -> int:
    """
    Number of filters whose observed selectivity is below `threshold`.
    Default threshold = 1%.
    """
    sels = filter_selectivities(plan_root)
    return sum(1 for s in sels if s < threshold)


def log_filter_selectivity_product(plan_root: Dict) -> float:
    """
    Sum of log(selectivity) across filter nodes.
    More negative ⇒ many strong filters (overall 'filter strength').
    """
    sels = filter_selectivities(plan_root)
    if not sels:
        return 0.0
    return sum(math.log(max(s, 1e-12)) for s in sels)


def optimizer_est_cost_root(plan_root: Dict) -> float:
    """Optimizer's estimated total cost at the root node (Total Cost)."""
    return float(plan_root.get("Total Cost", 0.0))


def max_est_rows_node(plan_root: Dict) -> float:
    """Maximum estimated number of rows over all nodes."""
    max_rows = 0.0
    for node in _iter_nodes(plan_root):
        r = node.get("Plan Rows")
        if isinstance(r, (int, float)):
            max_rows = max(max_rows, float(r))
    return max_rows


def log_max_est_rows(plan_root: Dict) -> float:
    """log(1 + max estimated rows at any node)."""
    return math.log1p(max_est_rows_node(plan_root))


def sum_est_rows_node(plan_root: Dict) -> float:
    """Sum of estimated rows across all nodes."""
    total = 0.0
    for node in _iter_nodes(plan_root):
        r = node.get("Plan Rows")
        if isinstance(r, (int, float)):
            total += float(r)
    return total


def log_sum_est_rows(plan_root: Dict) -> float:
    """log(1 + sum of estimated rows across all operators)."""
    return math.log1p(sum_est_rows_node(plan_root))


def card_errors_log(plan_root: Dict) -> List[float]:
    """
    Per-node absolute log-cardinality error:
    |log1p(Plan Rows) - log1p(Actual Rows)|.
    Only defined for EXPLAIN ANALYZE.
    """
    errs = []
    for node in _iter_nodes(plan_root):
        est = node.get("Plan Rows")
        act = node.get("Actual Rows")
        if isinstance(est, (int, float)) and isinstance(act, (int, float)):
            le = math.log1p(max(est, 0.0))
            la = math.log1p(max(act, 0.0))
            errs.append(abs(le - la))
    return errs


def max_log_card_error(plan_root: Dict) -> float:
    """Maximum log-cardinality error over all nodes."""
    errs = card_errors_log(plan_root)
    return max(errs) if errs else 0.0


# ---------------------------------------------------------------------------
# Structural summaries
# ---------------------------------------------------------------------------


def extract_top15_metrics(plan_root: Dict) -> Dict[str, float | int]:
    """
    Extract all 15 structural metrics as a dictionary.
    Convenience function for quick metric extraction.
    """
    # Compute num_tables properly (only from scan nodes)
    tables = set()
    for node in _iter_nodes(plan_root):
        node_type = node.get("Node Type", "")
        if is_scan_node(node_type):
            rel = node.get("Relation Name") or node.get("Alias")
            if rel:
                tables.add(rel)
    
    feats = {}
    feats["num_tables"] = len(tables)
    feats["num_nodes"] = num_nodes(plan_root)
    feats["num_joins"] = sum(1 for n in _iter_nodes(plan_root) if is_join_node(n.get("Node Type", "")))
    feats["longest_path"] = longest_path(plan_root)
    feats["join_tree_diameter"] = join_tree_diameter(plan_root)
    feats["num_blocking_ops"] = num_blocking_ops(plan_root)
    feats["num_nested_loop"] = num_nested_loop(plan_root)
    feats["max_est_join_input_rows"] = max_est_join_input_rows(plan_root)
    feats["sum_est_join_input_rows"] = sum_est_join_input_rows(plan_root)
    feats["num_highly_selective_filters"] = num_highly_selective_filters(plan_root)
    feats["log_filter_selectivity_product"] = log_filter_selectivity_product(plan_root)
    feats["optimizer_est_cost_root"] = optimizer_est_cost_root(plan_root)
    feats["log_max_est_rows"] = log_max_est_rows(plan_root)
    feats["log_sum_est_rows"] = log_sum_est_rows(plan_root)
    feats["max_log_card_error"] = max_log_card_error(plan_root)
    return feats


def summarise_plan_structure(plan: Dict, ngram_n: int = 3) -> PlanStructuralSummary:
    # Original metrics computation
    tables = set()
    columns = set()
    joins = 0
    filters = 0
    operator_hist = Counter()

    for node in _iter_nodes(plan):
        node_type = node.get("Node Type", "Unknown")
        operator_hist[node_type] += 1

        # Only count relations from scan nodes (base relations)
        if is_scan_node(node_type):
            relation = node.get("Relation Name") or node.get("Alias")
            if relation:
                tables.add(relation)

        for output in node.get("Output", []) or []:
            columns.add(output)

        if is_join_node(node_type):
            joins += 1

        if node.get("Filter"):
            filters += 1
        if node.get("Join Filter"):
            filters += 1

    paths = _collect_paths(plan)
    longest_path_len = max((len(p) for p in paths), default=0)

    # Compute new enriched metrics
    return PlanStructuralSummary(
        # Original metrics
        num_tables=len(tables),
        num_columns=len(columns),
        num_joins=joins,
        num_filters=filters,
        operator_histogram=operator_hist,
        path_ngrams=_make_ngram_counter(paths, ngram_n),
        longest_path_len=longest_path_len,
        # New enriched metrics
        num_nodes=num_nodes(plan),
        join_tree_diameter=join_tree_diameter(plan),
        num_blocking_ops=num_blocking_ops(plan),
        num_nested_loop=num_nested_loop(plan),
        max_est_join_input_rows=max_est_join_input_rows(plan),
        sum_est_join_input_rows=sum_est_join_input_rows(plan),
        num_highly_selective_filters=num_highly_selective_filters(plan),
        log_filter_selectivity_product=log_filter_selectivity_product(plan),
        optimizer_est_cost_root=optimizer_est_cost_root(plan),
        log_max_est_rows=log_max_est_rows(plan),
        log_sum_est_rows=log_sum_est_rows(plan),
        max_log_card_error=max_log_card_error(plan),
    )


def _enumerate_ngrams(path: Sequence[str], n: int) -> Iterable[Tuple[str, ...]]:
    if n <= 0:
        raise ValueError("n must be positive for n-grams")
    if len(path) < n:
        return []
    return [tuple(path[i : i + n]) for i in range(len(path) - n + 1)]


def _make_ngram_counter(paths: Iterable[Sequence[str]], n: int) -> Counter[Tuple[str, ...]]:
    counter: Counter[Tuple[str, ...]] = Counter()
    for path in paths:
        for ngram in _enumerate_ngrams(path, n):
            counter[ngram] += 1
    return counter


# ---------------------------------------------------------------------------
# Operator multiset distance
# ---------------------------------------------------------------------------


def _normalise_counter(counter: Counter[str]) -> Dict[str, float]:
    total = sum(counter.values())
    if total == 0:
        return {}
    return {key: value / total for key, value in counter.items()}


def operator_multiset_distance(
    hist_a: Counter[str],
    hist_b: Counter[str],
    norm: str = "l1",
) -> float:
    """
    Compute the L1 or L2 distance between normalised operator histograms.
    """
    if norm not in {"l1", "l2"}:
        raise ValueError("norm must be 'l1' or 'l2'")

    vec_a = _normalise_counter(hist_a)
    vec_b = _normalise_counter(hist_b)
    all_ops = set(vec_a) | set(vec_b)

    if norm == "l1":
        return sum(abs(vec_a.get(op, 0.0) - vec_b.get(op, 0.0)) for op in all_ops)

    # L2
    return sqrt(sum((vec_a.get(op, 0.0) - vec_b.get(op, 0.0)) ** 2 for op in all_ops))


# ---------------------------------------------------------------------------
# Path n-gram cosine distance
# ---------------------------------------------------------------------------


def _tfidf_vector(
    ngram_counts: Counter[Tuple[str, ...]],
    idf: Optional[Dict[Tuple[str, ...], float]] = None,
) -> Dict[Tuple[str, ...], float]:
    total = sum(ngram_counts.values())
    if total == 0:
        return {}
    vec: Dict[Tuple[str, ...], float] = {}
    for ngram, freq in ngram_counts.items():
        tf = freq / total
        weight = tf * (idf.get(ngram, 1.0) if idf else 1.0)
        vec[ngram] = weight
    return vec


def _cosine_distance(
    vec_a: Dict[Tuple[str, ...], float], vec_b: Dict[Tuple[str, ...], float]
) -> float:
    if not vec_a or not vec_b:
        return 1.0

    dot = 0.0
    for key, val in vec_a.items():
        dot += val * vec_b.get(key, 0.0)
    norm_a = sqrt(sum(value * value for value in vec_a.values()))
    norm_b = sqrt(sum(value * value for value in vec_b.values()))
    if norm_a == 0.0 or norm_b == 0.0:
        return 1.0
    cosine = dot / (norm_a * norm_b)
    return max(0.0, 1.0 - cosine)


def path_ngram_distance(
    ngrams_a: Counter[Tuple[str, ...]],
    ngrams_b: Counter[Tuple[str, ...]],
    idf: Optional[Dict[Tuple[str, ...], float]] = None,
) -> float:
    """
    Cosine distance between TF (or TF-IDF) vectors built from n-grams.
    """
    vec_a = _tfidf_vector(ngrams_a, idf=idf)
    vec_b = _tfidf_vector(ngrams_b, idf=idf)
    return _cosine_distance(vec_a, vec_b)


# ---------------------------------------------------------------------------
# CLI for quick inspection
# ---------------------------------------------------------------------------


def _format_counter(counter: Counter, top_k: int = 10) -> str:
    items = counter.most_common(top_k)
    return ", ".join(f"{key}:{value}" for key, value in items)


def _cli() -> None:
    parser = argparse.ArgumentParser(description="Inspect structural plan metrics.")
    parser.add_argument("--plan_csv", required=True, help="Path to long_raw CSV file.")
    parser.add_argument("--plan_id", type=int, required=False, help="Plan id inside the CSV.")
    parser.add_argument("--ngram_n", type=int, default=3, help="n for path n-grams (default: 3).")
    args = parser.parse_args()

    plan = load_plan_json(args.plan_csv, plan_id=args.plan_id)
    summary = summarise_plan_structure(plan, ngram_n=args.ngram_n)
    print("=== Original Metrics ===")
    print(f"Tables: {summary.num_tables}")
    print(f"Columns: {summary.num_columns}")
    print(f"Joins: {summary.num_joins}")
    print(f"Filters: {summary.num_filters}")
    print(f"Longest path: {summary.longest_path_len}")
    print("\n=== Enriched Metrics ===")
    print(f"Number of nodes: {summary.num_nodes}")
    print(f"Join tree diameter: {summary.join_tree_diameter}")
    print(f"Blocking operations: {summary.num_blocking_ops}")
    print(f"Nested loop joins: {summary.num_nested_loop}")
    print(f"Max estimated join input rows: {summary.max_est_join_input_rows:.2f}")
    print(f"Sum estimated join input rows: {summary.sum_est_join_input_rows:.2f}")
    print(f"Highly selective filters (<1%): {summary.num_highly_selective_filters}")
    print(f"Log filter selectivity product: {summary.log_filter_selectivity_product:.4f}")
    print(f"Optimizer estimated cost (root): {summary.optimizer_est_cost_root:.2f}")
    print(f"Log max estimated rows: {summary.log_max_est_rows:.4f}")
    print(f"Log sum estimated rows: {summary.log_sum_est_rows:.4f}")
    print(f"Max log cardinality error: {summary.max_log_card_error:.4f}")
    print("\n=== Operator Histogram (top 10) ===")
    print(_format_counter(summary.operator_histogram))
    print("\n=== Path N-grams (top 10) ===")
    print(_format_counter(summary.path_ngrams))


if __name__ == "__main__":
    _cli()

