"""
generate_query_analyses.py
--------------------------
Driver that generates per-template PRICE_N analysis markdown files.

Iterates:
  queries/tpch/*.sql   (22 templates, q1–q22)
  queries/tpcds/*.sql  (99 templates, q1–q99)

For each template takes the FIRST query instantiation and calls analyze_query().

Output tree:
  docs/price_n_query_analysis/
  ├── INDEX.md
  ├── tpch/
  │   └── q1.md ... q22.md
  └── tpcds/
      └── q1.md ... q99.md
"""

import os
import sys
import re
import textwrap

_EXPERIMENTS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_EXPERIMENTS_DIR)

if _EXPERIMENTS_DIR not in sys.path:
    sys.path.insert(0, _EXPERIMENTS_DIR)

from analyze_query_for_price_n import analyze_query

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

QUERIES_DIR = os.path.join(_REPO_ROOT, "queries")
DOCS_DIR = os.path.join(_REPO_ROOT, "docs", "price_n_query_analysis")

WORKLOADS = [
    ("tpch", "TPC-H", range(1, 23)),
    ("tpcds", "TPC-DS", range(1, 100)),
]


# ---------------------------------------------------------------------------
# SQL extraction helper
# ---------------------------------------------------------------------------

def extract_first_sql(filepath):
    """
    Read a query file and return the FIRST SQL statement.

    File format:
        EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
        select ... ;
        EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
        select ... ;
        ...

    Returns the SQL string (stripped of trailing semicolons and whitespace),
    or None if the file can't be parsed.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return None

    # Split on EXPLAIN lines
    parts = re.split(r'(?=EXPLAIN\s*\(FORMAT\s+JSON)', content, flags=re.IGNORECASE)
    for part in parts:
        part = part.strip()
        if not part.upper().startswith("EXPLAIN"):
            continue
        # Strip the EXPLAIN header
        m = re.match(r'EXPLAIN\s*\([^)]*\)\s*', part, re.IGNORECASE)
        if not m:
            continue
        sql_text = part[m.end():]
        # Find end at first unquoted semicolon
        in_quote = False
        end_pos = len(sql_text)
        for j, ch in enumerate(sql_text):
            if in_quote:
                if ch == "'":
                    in_quote = False
            else:
                if ch == "'":
                    in_quote = True
                elif ch == ";":
                    end_pos = j
                    break
        sql_text = sql_text[:end_pos].strip()
        # Join lines
        lines = [l.strip() for l in sql_text.split("\n") if l.strip()]
        sql_text = " ".join(lines)
        if sql_text:
            return sql_text
    return None


# ---------------------------------------------------------------------------
# Markdown renderer
# ---------------------------------------------------------------------------

_MAX_SQL_LINES = 35   # truncate raw SQL after this many "virtual" lines
_WRAP_WIDTH = 100     # word-wrap width for SQL display


def _format_sql_block(sql, max_chars=3000):
    """Format SQL for a markdown fenced block, with optional truncation."""
    if not sql:
        return "(none)"
    # Normalize: collapse multiple spaces but keep it readable
    # For display, just wrap lines at _WRAP_WIDTH
    if len(sql) > max_chars:
        sql = sql[:max_chars] + "\n..."
    return sql


def _render_markdown(workload_upper, qnum, analysis):
    """Render the full markdown document for one template."""
    lines = []

    title = f"# {workload_upper} Query {qnum} — PRICE_N Analysis"
    lines.append(title)
    lines.append("")

    # ---- Raw SQL ----
    lines.append("## Raw SQL")
    lines.append("")
    lines.append("```sql")
    raw = _format_sql_block(analysis["raw_sql"])
    lines.append(raw)
    lines.append("```")
    lines.append("")

    # ---- Transformed SQL ----
    lines.append("## Transformed SQL (input to PRICE)")
    lines.append("")
    tsql = analysis.get("transformed_sql", "")
    if tsql:
        lines.append("```sql")
        lines.append(_format_sql_block(tsql))
        lines.append("```")
    else:
        lines.append("*(transformation failed or produced empty result)*")
    lines.append("")

    # ---- What goes into PRICE ----
    lines.append("## What goes into PRICE")
    lines.append("")

    tables = analysis.get("tables", [])
    if tables:
        tbl_str = ", ".join(f"`{alias}` ({phys})" for alias, phys in tables)
        lines.append(f"**Tables**: {tbl_str}")
    else:
        lines.append("**Tables**: (none detected)")
    lines.append("")

    joins = analysis.get("joins", [])
    if joins:
        lines.append("**Joins**:")
        for l, r in joins:
            lines.append(f"- `{l}` = `{r}`")
    else:
        lines.append("**Joins**: (none — single-table query)")
    lines.append("")

    join_sides = analysis.get("join_sides", [])
    if join_sides:
        lines.append("**Join sides** (ANSI type):")
        for lc, rc, side in join_sides:
            lines.append(f"- `{lc}` = `{rc}` — **{side}**")
        lines.append("")

    filter_atoms = analysis.get("filter_atoms", {})
    if filter_atoms:
        lines.append("**Filter atoms**:")
        for col, atom in sorted(filter_atoms.items()):
            parts = []
            if atom.get("eq_values"):
                parts.append(f"eq={atom['eq_values']}")
            if atom.get("in_values"):
                vals = atom["in_values"]
                if len(vals) > 8:
                    vals = vals[:8] + ["..."]
                parts.append(f"in={vals}")
            if atom.get("not_in_values"):
                parts.append(f"not_in={atom['not_in_values']}")
            if atom.get("range_low") is not None:
                parts.append(f"range_low={atom['range_low']}")
            if atom.get("range_high") is not None:
                parts.append(f"range_high={atom['range_high']}")
            if atom.get("is_null"):
                parts.append("IS NULL")
            if atom.get("is_not_null"):
                parts.append("IS NOT NULL")
            if atom.get("like_keys"):
                parts.append(f"like={atom['like_keys'][:3]}")
            detail = "; ".join(parts) if parts else "(no detail)"
            lines.append(f"- `{col}`: {detail}")
    else:
        lines.append("**Filter atoms**: (none)")
    lines.append("")

    pairwise = analysis.get("pairwise_atoms", [])
    if pairwise:
        lines.append("**Pairwise atoms (same-table col-op-col)**:")
        for atom in pairwise:
            tbl, cx, cy, op, _, _ = atom
            lines.append(f"- `{tbl}.{cx}` {op} `{tbl}.{cy}`")
    else:
        lines.append("**Pairwise atoms (col-op-col)**: (none)")
    lines.append("")

    xtab = analysis.get("xtab_atoms", [])
    if xtab:
        lines.append("**Cross-table non-equi atoms**:")
        for atom in xtab:
            lt, lc, op, rt, rc, _ = atom
            lines.append(f"- `{lt}.{lc}` {op} `{rt}.{rc}`")
    else:
        lines.append("**Cross-table non-equi atoms**: (none)")
    lines.append("")

    # ---- LLM residual constructs ----
    lines.append("## LLM Residual Constructs")
    lines.append("")
    residuals = analysis.get("llm_residual_constructs", [])
    if residuals:
        for r in residuals:
            kind = r["kind"]
            detail = r["detail"]
            snippet = r.get("snippet", "")
            lines.append(f"- **{kind}**: {detail}")
            if snippet and snippet not in detail:
                lines.append(f"  ```sql")
                # Truncate long snippets
                sn = snippet[:200] + ("..." if len(snippet) > 200 else "")
                lines.append(f"  {sn}")
                lines.append(f"  ```")
    else:
        lines.append("*(none — query is within PRICE scope)*")
    lines.append("")

    # ---- Predicate reordering ----
    lines.append("## Predicate Reordering")
    lines.append("")
    reorder = analysis.get("reordering_log", [])
    if reorder:
        for entry in reorder:
            phase = entry["phase"]
            before = entry.get("before", "")
            after = entry.get("after", "")
            lines.append(f"- **{phase}**")
            if before:
                lines.append(f"  - Before: `{before[:120]}`")
            if after:
                lines.append(f"  - After:  `{after[:120]}`")
    else:
        lines.append("*(no transformations fired — no NOT push-down, no OR→IN, no date literals)*")
    lines.append("")

    # ---- DNF ----
    lines.append("## DNF (WHERE clause, post-NNF)")
    lines.append("")
    dnf = analysis.get("dnf_clauses", [])
    if not dnf:
        lines.append("*(no WHERE clause or transformation failed)*")
    elif len(dnf) == 1:
        clause = dnf[0]
        if len(clause) <= 1:
            pred = clause[0] if clause else "(empty)"
            lines.append("Single atom:")
            lines.append(f"```")
            lines.append(pred[:300])
            lines.append(f"```")
        else:
            lines.append("Single conjunctive clause:")
            lines.append(f"```")
            # Truncate very long DNF clauses
            shown = clause[:20]
            for pred in shown:
                lines.append(pred[:200])
            if len(clause) > 20:
                lines.append(f"... ({len(clause) - 20} more atoms)")
            lines.append(f"```")
    else:
        lines.append(f"DNF with {len(dnf)} disjunctive branch(es):")
        for i, clause in enumerate(dnf[:4]):
            lines.append(f"```")
            lines.append(f"-- Branch {i+1}")
            for pred in clause[:10]:
                lines.append(pred[:200])
            if len(clause) > 10:
                lines.append(f"... ({len(clause) - 10} more)")
            lines.append(f"```")
        if len(dnf) > 4:
            lines.append(f"*... {len(dnf) - 4} more branch(es) omitted*")
    lines.append("")

    # ---- Errors ----
    errors = analysis.get("errors", [])
    if errors:
        lines.append("## Pipeline Errors")
        lines.append("")
        for err in errors:
            lines.append(f"- `{err}`")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main driver
# ---------------------------------------------------------------------------

def run(verbose=True):
    """Generate all markdown files and the INDEX.md."""

    # Create output directories
    os.makedirs(DOCS_DIR, exist_ok=True)
    for wl, _, _ in WORKLOADS:
        os.makedirs(os.path.join(DOCS_DIR, wl), exist_ok=True)

    stats = {
        "tpch": {"total": 0, "ok": 0, "errors": 0},
        "tpcds": {"total": 0, "ok": 0, "errors": 0},
    }
    index_entries = []

    for wl, wl_upper, qrange in WORKLOADS:
        queries_dir = os.path.join(QUERIES_DIR, wl)
        for qnum in qrange:
            sql_file = os.path.join(queries_dir, f"{qnum}.sql")
            if not os.path.exists(sql_file):
                if verbose:
                    print(f"  [SKIP] {wl}/q{qnum}: file not found")
                continue

            stats[wl]["total"] += 1

            sql = extract_first_sql(sql_file)
            if not sql:
                if verbose:
                    print(f"  [FAIL] {wl}/q{qnum}: could not extract SQL")
                stats[wl]["errors"] += 1
                continue

            if verbose:
                print(f"  Analyzing {wl}/q{qnum} ...", end="", flush=True)

            try:
                analysis = analyze_query(sql, wl)
                had_errors = bool(analysis.get("errors"))
            except Exception as exc:
                analysis = {
                    "raw_sql": sql,
                    "transformed_sql": "",
                    "tables": [], "joins": [], "join_sides": [],
                    "filter_atoms": {}, "pairwise_atoms": [], "xtab_atoms": [],
                    "llm_residual_constructs": [], "reordering_log": [],
                    "dnf_clauses": [],
                    "errors": [f"analyze_query raised: {exc}"],
                }
                had_errors = True

            md_text = _render_markdown(wl_upper, qnum, analysis)

            out_path = os.path.join(DOCS_DIR, wl, f"q{qnum}.md")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(md_text)

            n_tables = len(analysis.get("tables", []))
            n_filters = len(analysis.get("filter_atoms", {}))
            n_residuals = len(analysis.get("llm_residual_constructs", []))
            n_joins = len(analysis.get("joins", []))

            status = "ERR" if had_errors else "OK"
            if verbose:
                print(f" {status} | {n_tables}T {n_joins}J {n_filters}F {n_residuals}R")

            if had_errors:
                stats[wl]["errors"] += 1
            else:
                stats[wl]["ok"] += 1

            index_entries.append({
                "workload": wl_upper,
                "qnum": qnum,
                "path": f"{wl}/q{qnum}.md",
                "tables": n_tables,
                "joins": n_joins,
                "filters": n_filters,
                "residuals": n_residuals,
                "status": status,
            })

    # Write INDEX.md
    _write_index(index_entries, stats)

    total_files = sum(s["total"] for s in stats.values())
    total_ok = sum(s["ok"] for s in stats.values())
    total_err = sum(s["errors"] for s in stats.values())
    print(f"\nDone. {total_files} templates processed: {total_ok} OK, {total_err} with errors.")
    print(f"Output: {DOCS_DIR}")

    return stats


def _write_index(entries, stats):
    """Write the INDEX.md file."""
    lines = []
    lines.append("# PRICE_N Query Analysis — Index")
    lines.append("")
    lines.append("Per-template analysis of TPC-H (22 queries) and TPC-DS (99 queries).")
    lines.append("Shows what PRICE can handle vs. what falls to the LLM residual encoder.")
    lines.append("")
    lines.append("## Statistics")
    lines.append("")
    for wl, _, _ in WORKLOADS:
        s = stats.get(wl, {})
        lines.append(f"- **{wl.upper()}**: {s.get('total', 0)} templates, "
                     f"{s.get('ok', 0)} fully analyzed, "
                     f"{s.get('errors', 0)} with pipeline errors")
    lines.append("")
    lines.append("## TPC-H Queries")
    lines.append("")
    lines.append("| Query | Tables | Joins | Filter cols | Residuals | Status |")
    lines.append("|-------|--------|-------|-------------|-----------|--------|")
    for e in entries:
        if e["workload"] != "TPC-H":
            continue
        link = f"[q{e['qnum']}]({e['path']})"
        lines.append(f"| {link} | {e['tables']} | {e['joins']} | "
                     f"{e['filters']} | {e['residuals']} | {e['status']} |")
    lines.append("")
    lines.append("## TPC-DS Queries")
    lines.append("")
    lines.append("| Query | Tables | Joins | Filter cols | Residuals | Status |")
    lines.append("|-------|--------|-------|-------------|-----------|--------|")
    for e in entries:
        if e["workload"] != "TPC-DS":
            continue
        link = f"[q{e['qnum']}]({e['path']})"
        lines.append(f"| {link} | {e['tables']} | {e['joins']} | "
                     f"{e['filters']} | {e['residuals']} | {e['status']} |")
    lines.append("")

    index_path = os.path.join(DOCS_DIR, "INDEX.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Wrote {index_path}")


if __name__ == "__main__":
    run(verbose=True)
