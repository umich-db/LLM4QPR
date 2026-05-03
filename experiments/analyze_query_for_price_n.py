"""
analyze_query_for_price_n.py
----------------------------
Standalone PRICE_N per-query parse-and-input analyzer.

Exports:
    analyze_query(sql: str, db_name: str) -> dict

The returned dict contains:
    raw_sql, transformed_sql, tables, joins, join_sides,
    filter_atoms, pairwise_atoms, xtab_atoms,
    llm_residual_constructs, reordering_log, dnf_clauses, errors
"""

import sys
import os
import re
import textwrap

# Ensure the experiments directory is on the path so price_data_utils is importable
_EXPERIMENTS_DIR = os.path.dirname(os.path.abspath(__file__))
if _EXPERIMENTS_DIR not in sys.path:
    sys.path.insert(0, _EXPERIMENTS_DIR)

try:
    import sqlglot
    from sqlglot import exp as _exp
    HAS_SQLGLOT = True
except ImportError:
    HAS_SQLGLOT = False

# Import the helpers from price_data_utils
from price_data_utils import (
    transform_sql_for_price,
    _push_not_to_nnf,
    _rewrite_disjoint_or_to_in,
    _normalize_date_literals,
    _extract_filter_atoms,
    _extract_pairwise_intra_atoms,
    _extract_xtab_nonequi_atoms,
    _flatten_join_with_side,
    _preprocess_predicates,
    flatten_sql_for_price,
    _check_cte_body_simple,
    _is_inside_subquery,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_sql(ast):
    """Return ast.sql() or '' on error."""
    try:
        return ast.sql()
    except Exception:
        return ""


def _col_str(node):
    """'table.column' for a Column node."""
    if hasattr(node, "table") and node.table:
        return f"{node.table}.{node.name}"
    return str(node)


def _eval_epoch_interval_arithmetic(ast):
    """
    Evaluate remaining `integer_epoch_seconds +/- INTERVAL 'N' DAYS` expressions
    that weren't fully resolved by the standard pipeline.

    This arises when _flatten_join_with_side converts DATE '...' → CAST('...' AS DATE)
    and the epoch conversion only partially applies.

    Mutates ast in place.
    """
    if not HAS_SQLGLOT:
        return
    cmp_classes = (_exp.EQ, _exp.NEQ, _exp.LT, _exp.LTE, _exp.GT, _exp.GTE)
    for cmp_cls in cmp_classes:
        for cmp in list(ast.find_all(cmp_cls)):
            rhs = cmp.expression
            if not isinstance(rhs, (_exp.Sub, _exp.Add)):
                continue
            base = rhs.this
            interval = rhs.expression
            if not (isinstance(base, _exp.Literal) and base.is_number
                    and isinstance(interval, _exp.Interval)):
                continue
            try:
                n_str = str(interval.this.name) if hasattr(interval.this, "name") else str(interval.this)
                n = int(n_str)
                unit = str(interval.unit).upper() if interval.unit else ""
                base_val = int(float(base.this))
                if unit.startswith("DAY"):
                    result = base_val + (n if isinstance(rhs, _exp.Add) else -n) * 86400
                    cmp.set("expression", _exp.Literal.number(result))
            except Exception:
                continue


# ---------------------------------------------------------------------------
# LLM residual constructs detector
# ---------------------------------------------------------------------------

def _cte_simplicity_failure_reason(body):
    """Return a human-readable reason why a CTE body fails the simple-body check."""
    if isinstance(body, (_exp.Union, _exp.Intersect, _exp.Except)):
        return "multi-branch (UNION/INTERSECT/EXCEPT)"
    if not isinstance(body, _exp.Select):
        return "not a SELECT node"
    reasons = []
    if body.args.get("group"):
        reasons.append("has GROUP BY")
    if body.args.get("having"):
        reasons.append("has HAVING")
    if body.args.get("distinct"):
        reasons.append("has DISTINCT")
    if body.args.get("limit") and body.args.get("order"):
        reasons.append("has ORDER BY + LIMIT")
    if any(body.find_all(_exp.Window)):
        reasons.append("has window functions")
    AGGS = (_exp.Sum, _exp.Avg, _exp.Min, _exp.Max, _exp.Count)
    for expr in body.expressions:
        e = expr.this if isinstance(expr, _exp.Alias) else expr
        if isinstance(e, AGGS) or any(e.find_all(AGGS)):
            reasons.append("has aggregates in projection")
            break
    return "; ".join(reasons) if reasons else "unknown"


def _collect_llm_residuals(ast, sql):
    """
    Walk the original AST to find constructs outside PRICE's scope.

    Returns a list of dict items:
        {"kind": str, "detail": str, "snippet": str}

    Under PRICE_N policy:
    - EXISTS / NOT EXISTS subqueries → Exists / NotExists residuals
    - IN(subquery) / NOT IN(subquery) → InSubquery / NotInSubquery residuals
    - Scalar subqueries (col op (SELECT AGG ...)) → ScalarSubquery residuals
    - CTEs whose body fails _check_cte_body_simple → NonSimpleCTE residuals
    - Simple CTEs → still reported as CTE (informational)
    """
    if not HAS_SQLGLOT:
        return [{"kind": "sqlglot_unavailable", "detail": "sqlglot not installed", "snippet": ""}]

    residuals = []

    # --- EXISTS / NOT EXISTS ---
    # NOT EXISTS: Not(Exists(...))
    for not_node in list(ast.find_all(_exp.Not)):
        if isinstance(not_node.this, _exp.Exists):
            exists_node = not_node.this
            inner = exists_node.this
            if isinstance(inner, _exp.Subquery):
                inner = inner.this
            inner_sql = inner.sql()[:100] if hasattr(inner, "sql") else ""
            residuals.append({
                "kind": "NotExists",
                "detail": f"NOT EXISTS subquery — goes to LLM residual under PRICE_N",
                "snippet": f"NOT EXISTS ({inner_sql}{'...' if len(inner_sql) >= 100 else ''})",
            })
    # EXISTS (not wrapped in Not)
    for exists_node in list(ast.find_all(_exp.Exists)):
        # Skip if parent is Not (already handled above)
        parent = exists_node.parent
        if isinstance(parent, _exp.Not):
            continue
        inner = exists_node.this
        if isinstance(inner, _exp.Subquery):
            inner = inner.this
        inner_sql = inner.sql()[:100] if hasattr(inner, "sql") else ""
        residuals.append({
            "kind": "Exists",
            "detail": f"EXISTS subquery — goes to LLM residual under PRICE_N",
            "snippet": f"EXISTS ({inner_sql}{'...' if len(inner_sql) >= 100 else ''})",
        })

    # --- IN(subquery) / NOT IN(subquery) ---
    # NOT IN: Not(In(...))
    for not_node in list(ast.find_all(_exp.Not)):
        if isinstance(not_node.this, _exp.In):
            in_node = not_node.this
            subq = in_node.args.get("query")
            if subq is not None:
                col = in_node.this
                col_str = col.sql()[:60] if hasattr(col, "sql") else str(col)
                inner_sql = subq.sql()[:80]
                residuals.append({
                    "kind": "NotInSubquery",
                    "detail": f"NOT IN (subquery) on `{col_str}` — goes to LLM residual under PRICE_N",
                    "snippet": f"{col_str} NOT IN ({inner_sql}{'...' if len(inner_sql) >= 80 else ''})",
                })
    # IN(subquery)
    for in_node in list(ast.find_all(_exp.In)):
        subq = in_node.args.get("query")
        if subq is None:
            continue  # value-list IN, not a subquery
        # Skip if parent is Not (already handled)
        if isinstance(in_node.parent, _exp.Not):
            continue
        col = in_node.this
        col_str = col.sql()[:60] if hasattr(col, "sql") else str(col)
        inner_sql = subq.sql()[:80]
        residuals.append({
            "kind": "InSubquery",
            "detail": f"IN (subquery) on `{col_str}` — goes to LLM residual under PRICE_N",
            "snippet": f"{col_str} IN ({inner_sql}{'...' if len(inner_sql) >= 80 else ''})",
        })

    # --- Scalar subqueries (col op (SELECT AGG ...)) ---
    cmp_classes = (_exp.EQ, _exp.NEQ, _exp.LT, _exp.LTE, _exp.GT, _exp.GTE)
    for cmp_cls in cmp_classes:
        for cmp in list(ast.find_all(cmp_cls)):
            rhs = cmp.expression
            # Unwrap Subquery wrapper if present
            inner = rhs
            if isinstance(inner, _exp.Subquery):
                inner = inner.this
            if not isinstance(inner, _exp.Select):
                continue
            # Check it looks like a scalar subquery (single aggregate expression)
            AGGS = (_exp.Sum, _exp.Avg, _exp.Min, _exp.Max, _exp.Count)
            has_agg = any(isinstance(e, AGGS) or any(e.find_all(AGGS))
                         for e in inner.expressions)
            if has_agg:
                col_str = cmp.this.sql()[:60] if hasattr(cmp.this, "sql") else str(cmp.this)
                inner_sql = rhs.sql()[:80]
                residuals.append({
                    "kind": "ScalarSubquery",
                    "detail": f"Scalar subquery `{col_str} {cmp_cls.__name__} (SELECT AGG ...)` — goes to LLM residual under PRICE_N",
                    "snippet": f"{col_str} ... ({inner_sql}{'...' if len(inner_sql) >= 80 else ''})",
                })

    # CTEs: WITH ... AS (...)
    # Under PRICE_N: non-simple bodies are NonSimpleCTE residuals; simple ones still reported as CTE.
    with_node = ast.args.get("with")
    is_recursive = bool(with_node and with_node.args.get("recursive")) if with_node else False
    ctes_found = list(ast.find_all(_exp.CTE))
    for cte in ctes_found:
        name = cte.alias or "(unnamed)"
        inner = cte.this
        if isinstance(inner, _exp.Subquery):
            inner = inner.this

        # Classify as simple or non-simple
        is_simple = _check_cte_body_simple(inner) and not is_recursive

        # Get SELECT list from first branch
        if isinstance(inner, _exp.Union):
            branches = list(inner.find_all(_exp.Select))
            branch_count = len(branches)
            projections = [e.sql() for e in (branches[0].expressions if branches else [])]
        else:
            branches = list(inner.find_all(_exp.Select)) if isinstance(inner, _exp.Select) else []
            branch_count = 1
            projections = [e.sql() for e in (inner.expressions if isinstance(inner, _exp.Select) else [])]

        proj_str = ", ".join(projections[:5])
        if len(projections) > 5:
            proj_str += ", ..."

        # WHERE filters
        where_nodes = list(inner.find_all(_exp.Where))
        where_str = where_nodes[0].sql() if where_nodes else ""

        # GROUP BY
        gb_nodes = list(inner.find_all(_exp.Group))
        gb_str = gb_nodes[0].sql() if gb_nodes else ""

        if is_simple:
            detail = f"CTE `{name}` (simple body — eligible for inlining)"
            kind = "CTE"
        else:
            if is_recursive:
                failure_reason = "WITH RECURSIVE"
            else:
                failure_reason = _cte_simplicity_failure_reason(inner)
            detail = f"CTE `{name}` (non-simple: {failure_reason}) — goes to LLM residual under PRICE_N"
            kind = "NonSimpleCTE"

        if branch_count > 1:
            detail += f" ({branch_count} UNION branches)"
        if proj_str:
            detail += f"; projects: {proj_str}"
        if where_str:
            detail += f"; filters: {where_str[:120]}"
        if gb_str:
            detail += f"; {gb_str[:60]}"

        residuals.append({
            "kind": kind,
            "detail": detail,
            "snippet": f"WITH {name} AS ({inner.sql()[:120]}...)" if len(inner.sql()) > 120
                       else f"WITH {name} AS ({inner.sql()})",
        })

    # Derived tables: subqueries in FROM position
    for subq in ast.find_all(_exp.Subquery):
        # Only care about subqueries that are in a FROM-like position (not EXISTS/IN)
        parent = subq.parent
        if parent is None:
            continue
        # Subquery in FROM (derived table) — its parent should be From or Join
        if isinstance(parent, (_exp.From, _exp.Join)):
            alias = subq.alias or "(unnamed)"
            inner_sql = subq.sql()[:120]
            residuals.append({
                "kind": "DerivedTable",
                "detail": f"Derived table alias `{alias}`",
                "snippet": f"FROM ({inner_sql}...) AS {alias}",
            })

    # Set operations: UNION / INTERSECT / EXCEPT
    for union_node in ast.find_all(_exp.Union):
        kind = type(union_node).__name__  # Union, Intersect, Except
        residuals.append({
            "kind": kind,
            "detail": f"{kind} operator — only first SELECT branch flows to PRICE",
            "snippet": union_node.sql()[:120] + ("..." if len(union_node.sql()) > 120 else ""),
        })
        break  # Only report once per query

    # CASE expressions in SELECT projection (not in WHERE)
    sel_node = None
    for sel in ast.find_all(_exp.Select):
        sel_node = sel
        break
    if sel_node is not None:
        for expr in sel_node.expressions:
            for case in expr.find_all(_exp.Case):
                residuals.append({
                    "kind": "CASE_in_SELECT",
                    "detail": f"CASE expression in SELECT: {case.sql()[:80]}",
                    "snippet": case.sql()[:100],
                })
                break  # one example per query

    # Function-call predicates in WHERE (Anonymous = unknown functions)
    where_node = ast.args.get("where")
    if where_node:
        for anon in where_node.find_all(_exp.Anonymous):
            residuals.append({
                "kind": "FunctionPredicate",
                "detail": f"Function call `{anon.this}(...)` in WHERE",
                "snippet": anon.sql()[:80],
            })

    # Window functions
    for win in ast.find_all(_exp.Window):
        residuals.append({
            "kind": "WindowFunction",
            "detail": f"Window function: {win.sql()[:60]}",
            "snippet": win.sql()[:80],
        })
        break  # one example

    # GROUP BY
    for gb in ast.find_all(_exp.Group):
        gb_cols = gb.sql()
        residuals.append({
            "kind": "GroupBy",
            "detail": f"GROUP BY: {gb_cols[:80]}",
            "snippet": gb_cols[:100],
        })
        break  # one example

    # Aggregates in SELECT
    agg_types = (_exp.Sum, _exp.Avg, _exp.Min, _exp.Max, _exp.Count)
    agg_examples = []
    if sel_node is not None:
        for expr in sel_node.expressions:
            for agg_t in agg_types:
                for agg in expr.find_all(agg_t):
                    agg_examples.append(agg.sql())
                    break
    if agg_examples:
        residuals.append({
            "kind": "Aggregates",
            "detail": f"Aggregates in SELECT: {', '.join(agg_examples[:4])}",
            "snippet": ", ".join(agg_examples[:4]),
        })

    # ORDER BY
    for ob in ast.find_all(_exp.Order):
        residuals.append({
            "kind": "OrderBy",
            "detail": f"ORDER BY: {ob.sql()[:80]}",
            "snippet": ob.sql()[:80],
        })
        break

    # HAVING
    for hav in ast.find_all(_exp.Having):
        residuals.append({
            "kind": "Having",
            "detail": f"HAVING: {hav.sql()[:80]}",
            "snippet": hav.sql()[:80],
        })
        break

    # LIMIT
    for lim in ast.find_all(_exp.Limit):
        residuals.append({
            "kind": "Limit",
            "detail": f"LIMIT: {lim.sql()[:40]}",
            "snippet": lim.sql()[:40],
        })
        break

    # LIKE / NOT LIKE / ILIKE / NOT ILIKE — always residual under PRICE_N
    # Walk all Like and ILike nodes; if the parent is a Not, classify as
    # Not*Predicate (and don't also emit a plain *Predicate for the inner node).
    seen_like_parents = set()
    for like_node in list(ast.find_all((_exp.Like, _exp.ILike))):
        if _is_inside_subquery(like_node):
            continue  # already counted under the parent CTE/Exists/InSubquery residual
        parent = like_node.parent
        is_negated = isinstance(parent, _exp.Not)
        if is_negated:
            node_id = id(parent)
            if node_id in seen_like_parents:
                continue  # avoid double-counting when both Like and ILike are children
            seen_like_parents.add(node_id)
            kind = ("NotILikePredicate" if isinstance(like_node, _exp.ILike)
                    else "NotLikePredicate")
            snippet = parent.sql()
        else:
            kind = "ILikePredicate" if isinstance(like_node, _exp.ILike) else "LikePredicate"
            snippet = like_node.sql()
        residuals.append({
            "kind": kind,
            "detail": f"{kind} predicate (always LLM residual under PRICE_N): {snippet[:120]}",
            "snippet": snippet[:200],
        })

    return residuals


# ---------------------------------------------------------------------------
# Reordering / transformation log
# ---------------------------------------------------------------------------

def _compute_reordering_log(sql):
    """
    Apply each PRICE_N pre-processing phase in sequence, recording
    before/after snippets whenever something changes.

    Returns list of {"phase": str, "before": str, "after": str}.
    """
    if not HAS_SQLGLOT:
        return []

    log = []

    try:
        ast = sqlglot.parse_one(sql)
    except Exception as exc:
        return [{"phase": "parse", "before": sql[:100], "after": f"ERROR: {exc}"}]

    def _snapshot(a):
        try:
            return a.sql()
        except Exception:
            return ""

    # Phase 1.5a: NOT → NNF
    before = _snapshot(ast)
    _push_not_to_nnf(ast)
    after = _snapshot(ast)
    if before != after:
        log.append({
            "phase": "NOT push-down → NNF",
            "before": _diff_snippet(before, after, "NOT"),
            "after": _diff_snippet(after, before, "NOT"),
        })

    # Phase 1.5b: disjoint OR → IN
    before = _snapshot(ast)
    _rewrite_disjoint_or_to_in(ast)
    after = _snapshot(ast)
    if before != after:
        log.append({
            "phase": "OR → IN rewrite",
            "before": _diff_snippet(before, after, " OR "),
            "after": _diff_snippet(after, before, " IN "),
        })

    # Phase 1.5c: date literals → epoch days
    before = _snapshot(ast)
    _normalize_date_literals(ast)
    after = _snapshot(ast)
    if before != after:
        # Find specific date conversions
        date_pattern = re.compile(r"DATE\s+'(\d{4}-\d{2}-\d{2})'", re.IGNORECASE)
        dates_found = date_pattern.findall(before)
        epoch_nums = re.findall(r'\b(\d{4,6})\b', after)
        detail = ""
        if dates_found:
            detail = f"e.g. DATE '{dates_found[0]}' → epoch days integer"
        log.append({
            "phase": "Date literals → epoch days",
            "before": _diff_snippet(before, after, "DATE"),
            "after": detail or _diff_snippet(after, before, ""),
        })

    # Phase 2: BETWEEN → range (happens in _preprocess_predicates via the main pipeline)
    # Check original SQL for BETWEEN
    if re.search(r'\bBETWEEN\b', sql, re.IGNORECASE):
        log.append({
            "phase": "BETWEEN → AND-of-comparisons",
            "before": "col BETWEEN low AND high",
            "after": "col >= low AND col <= high",
        })

    # LIKE → drop (if present in original)
    if re.search(r'\bLIKE\b', sql, re.IGNORECASE):
        log.append({
            "phase": "LIKE → dropped (1 = 1)",
            "before": "col LIKE 'pattern'",
            "after": "1 = 1 (tautology, filtered out)",
        })

    return log


def _diff_snippet(full_sql, other_sql, keyword):
    """Extract a meaningful snippet showing the changed part."""
    # Try to find a line/segment containing the keyword
    if keyword:
        idx = full_sql.lower().find(keyword.lower())
        if idx >= 0:
            start = max(0, idx - 30)
            end = min(len(full_sql), idx + 80)
            snippet = full_sql[start:end].strip()
            if start > 0:
                snippet = "..." + snippet
            if end < len(full_sql):
                snippet = snippet + "..."
            return snippet
    # Fallback: first 120 chars
    return full_sql[:120] + ("..." if len(full_sql) > 120 else "")


# ---------------------------------------------------------------------------
# DNF computation
# ---------------------------------------------------------------------------

def _compute_dnf(ast):
    """
    Compute the DNF of the WHERE clause (post-NNF, post-OR-rewrite).

    Returns a list of conjunctive clauses:
        [[pred_str, ...], [pred_str, ...], ...]
    Each inner list is a conjunction. Multiple outer lists = disjunction.

    Returns [] if no WHERE clause.
    """
    if not HAS_SQLGLOT:
        return []

    where = ast.args.get("where")
    if where is None:
        return []

    def _to_dnf(node):
        """Recursively convert node to DNF: list of conjunctions."""
        # Unwrap Paren
        while isinstance(node, _exp.Paren):
            node = node.this
        if isinstance(node, _exp.And):
            left_dnf = _to_dnf(node.left if hasattr(node, "left") else node.this)
            right_dnf = _to_dnf(node.right if hasattr(node, "right") else node.expression)
            # AND: cartesian product of clauses
            result = []
            for l_clause in left_dnf:
                for r_clause in right_dnf:
                    result.append(l_clause + r_clause)
            return result
        if isinstance(node, _exp.Or):
            left_dnf = _to_dnf(node.left if hasattr(node, "left") else node.this)
            right_dnf = _to_dnf(node.right if hasattr(node, "right") else node.expression)
            # OR: concatenate branches
            return left_dnf + right_dnf
        # Leaf node
        try:
            leaf_str = node.sql()
        except Exception:
            leaf_str = str(node)
        return [[leaf_str]]

    try:
        return _to_dnf(where.this if hasattr(where, "this") else where)
    except Exception as exc:
        return [[f"<DNF error: {exc}>"]]


# ---------------------------------------------------------------------------
# Main analysis function
# ---------------------------------------------------------------------------

def analyze_query(sql: str, db_name: str) -> dict:
    """
    Analyze a single SQL query for PRICE_N input decomposition.

    Returns a dict with:
        raw_sql          - the original SQL string
        transformed_sql  - SQL after transform_sql_for_price
        tables           - list of (alias, physical_name) tuples
        joins            - list of (left_col, right_col) string pairs
        join_sides       - list of (left_col, right_col, side) triples
        filter_atoms     - dict[col -> atom_dict]
        pairwise_atoms   - list of 6-tuples (same-table col-op-col)
        xtab_atoms       - list of 6-tuples (cross-table non-equi)
        llm_residual_constructs - list of residual dicts
        reordering_log   - list of transformation log entries
        dnf_clauses      - list of conjunctions (list of lists)
        errors           - list of error strings (if any)
    """
    result = {
        "raw_sql": sql,
        "transformed_sql": "",
        "tables": [],
        "joins": [],
        "join_sides": [],
        "filter_atoms": {},
        "pairwise_atoms": [],
        "xtab_atoms": [],
        "llm_residual_constructs": [],
        "reordering_log": [],
        "dnf_clauses": [],
        "errors": [],
    }

    if not HAS_SQLGLOT:
        result["errors"].append("sqlglot not available")
        return result

    # --- Step 1: Parse original AST for residual analysis ---
    try:
        orig_ast = sqlglot.parse_one(sql)
    except Exception as exc:
        result["errors"].append(f"parse_one(original): {exc}")
        orig_ast = None

    # --- Step 2: Collect LLM residuals from original AST ---
    if orig_ast is not None:
        try:
            result["llm_residual_constructs"] = _collect_llm_residuals(orig_ast, sql)
        except Exception as exc:
            result["errors"].append(f"collect_llm_residuals: {exc}")

    # --- Step 3: Compute reordering log ---
    try:
        result["reordering_log"] = _compute_reordering_log(sql)
    except Exception as exc:
        result["errors"].append(f"compute_reordering_log: {exc}")

    # --- Step 4: Transform SQL for PRICE ---
    try:
        transformed = transform_sql_for_price(
            sql, db_name,
            price_n_parsing=True,
            price_n_filter=True,
            price_n_fanout=True,
            price_n_pairwise=True,
        )
        result["transformed_sql"] = transformed or ""
    except Exception as exc:
        result["errors"].append(f"transform_sql_for_price: {exc}")
        result["transformed_sql"] = ""
        transformed = ""

    # --- Step 5: Parse transformed SQL and extract atoms ---
    if transformed:
        # Strip trailing unmatched ')' artifacts left by the flattening pipeline
        transformed_clean = transformed
        try:
            # Count paren balance; strip trailing unmatched closes
            depth = 0
            for ch in transformed_clean:
                if ch == '(':
                    depth += 1
                elif ch == ')':
                    depth -= 1
            # If more closes than opens, strip them from the right
            while depth < 0:
                idx = transformed_clean.rfind(')')
                if idx < 0:
                    break
                transformed_clean = transformed_clean[:idx] + transformed_clean[idx+1:]
                depth += 1
        except Exception:
            pass

        try:
            trans_ast = sqlglot.parse_one(transformed_clean)
        except Exception as exc:
            # Last attempt: try stripping trailing parens more aggressively
            try:
                trans_ast = sqlglot.parse_one(transformed_clean.rstrip(') \t\n'))
            except Exception:
                result["errors"].append(f"parse_one(transformed): {exc}")
                trans_ast = None

        if trans_ast is not None:
            # Evaluate any residual epoch-interval arithmetic before extraction
            try:
                _eval_epoch_interval_arithmetic(trans_ast)
            except Exception:
                pass

            # Filter atoms
            try:
                result["filter_atoms"] = _extract_filter_atoms(trans_ast)
            except Exception as exc:
                result["errors"].append(f"_extract_filter_atoms: {exc}")

            # Pairwise intra-table atoms (same-table col-op-col):
            # Try transformed SQL first; fall back to original if empty.
            # Pairwise predicates may be lost during EXISTS-inlining in the
            # transform pipeline, so we also scan the pre-processed original.
            try:
                pairwise_trans = _extract_pairwise_intra_atoms(trans_ast)
            except Exception:
                pairwise_trans = []

            if not pairwise_trans and orig_ast is not None:
                try:
                    # Apply NNF on a copy of the original AST
                    orig_pp = sqlglot.parse_one(sql)
                    _push_not_to_nnf(orig_pp)
                    pairwise_orig = _extract_pairwise_intra_atoms(orig_pp)
                    result["pairwise_atoms"] = pairwise_orig
                except Exception as exc:
                    result["errors"].append(f"_extract_pairwise_intra_atoms(orig): {exc}")
            else:
                result["pairwise_atoms"] = pairwise_trans

            # Cross-table non-equi atoms
            try:
                result["xtab_atoms"] = _extract_xtab_nonequi_atoms(trans_ast)
            except Exception as exc:
                result["errors"].append(f"_extract_xtab_nonequi_atoms: {exc}")

            # Tables and joins from transformed AST
            try:
                result["tables"] = _extract_tables(trans_ast, db_name)
                result["joins"] = _extract_joins(trans_ast)
            except Exception as exc:
                result["errors"].append(f"_extract_tables/joins: {exc}")

            # DNF of WHERE in transformed SQL
            try:
                # Re-apply NNF + OR→IN on transformed AST for DNF computation
                dnf_ast = sqlglot.parse_one(transformed_clean)
                _push_not_to_nnf(dnf_ast)
                _rewrite_disjoint_or_to_in(dnf_ast)
                _eval_epoch_interval_arithmetic(dnf_ast)
                result["dnf_clauses"] = _compute_dnf(dnf_ast)
            except Exception as exc:
                result["errors"].append(f"compute_dnf: {exc}")

    # --- Step 6: Join sides from _flatten_join_with_side ---
    try:
        _, sides = _flatten_join_with_side(sql)
        result["join_sides"] = sides
    except Exception as exc:
        result["errors"].append(f"_flatten_join_with_side: {exc}")

    return result


def _extract_tables(ast, db_name):
    """Extract (price_alias, physical_name) pairs from FROM clause."""
    if not HAS_SQLGLOT:
        return []
    tables = []
    from_clause = ast.args.get("from_")
    if from_clause is None:
        return []

    # Try loading abbreviation mapping for physical name lookup
    abbrev_rev = {}
    try:
        from price_data_utils import _load_abbrev_mapping
        abbrev = _load_abbrev_mapping(db_name)
        abbrev_rev = {v: k for k, v in abbrev.items()}
    except Exception:
        pass

    for tbl in ast.find_all(_exp.Table):
        alias = tbl.alias or tbl.name
        phys = abbrev_rev.get(alias, tbl.name)
        entry = (alias, phys)
        if entry not in tables:
            tables.append(entry)

    return tables


def _extract_joins(ast):
    """Extract equi-join pairs from WHERE clause."""
    if not HAS_SQLGLOT:
        return []
    where = ast.args.get("where")
    if where is None:
        return []
    joins = []
    for eq in where.find_all(_exp.EQ):
        lhs, rhs = eq.this, eq.expression
        if isinstance(lhs, _exp.Column) and isinstance(rhs, _exp.Column):
            pair = (_col_str(lhs), _col_str(rhs))
            if pair not in joins:
                joins.append(pair)
    return joins
