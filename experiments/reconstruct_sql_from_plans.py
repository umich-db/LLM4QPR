"""
Reconstruct PRICE-format flat SQL from deepdb_augmented plan trees.

Each plan tree contains:
  - Root-level join_conds: list of SQL join condition strings
  - Scan nodes: plan_parameters.table (index into table_stats) and
    plan_parameters.filter_columns (predicate tree)
  - Hash Join / Nested Loop / Merge Join nodes: filter_columns with join
    conditions (literal looks like 'table.col  ') — NOT filter predicates

Output SQL format:
  select count(*) from alias1, alias2, ... where join1 and join2 and filter1 ...

Usage:
    from reconstruct_sql_from_plans import reconstruct_all_sql
    sqls = reconstruct_all_sql(json_path, db_name, abbrev)
"""

import json
import os
import re

# Characters that are safe in SQL identifiers without quoting
_SAFE_IDENT_RE = re.compile(r'^[a-z_][a-z0-9_]*$')


def _quote_col(col_name):
    """Quote a column name if it contains special characters (e.g., '/' in Month/Year).

    PRICE statistics store column names as-is (e.g., 'month/year'), so the quoted
    SQL must still produce a column reference that PRICE's parse_sql can resolve to
    the same 'alias.col_name' key used in the statistics.
    """
    if _SAFE_IDENT_RE.match(col_name):
        return col_name
    return f'"{col_name}"'


def _collect_scan_tables(node, table_indices):
    """Recursively collect table indices from scan nodes."""
    pp = node.get("plan_parameters", {})
    table_idx = pp.get("table")
    if table_idx is not None:
        table_indices.add(table_idx)
    for child in node.get("children", []):
        _collect_scan_tables(child, table_indices)


def _collect_scan_filters(node, filters, column_stats, table_stats, abbrev):
    """Collect filter predicates from scan nodes only (not join nodes).

    Scan nodes are identified by having a 'table' field in plan_parameters.
    Join nodes (Hash Join, Nested Loop, Merge Join) have filter_columns that
    represent join conditions, not WHERE predicates.
    """
    pp = node.get("plan_parameters", {})
    table_idx = pp.get("table")

    if table_idx is not None and pp.get("filter_columns") is not None:
        # This is a scan node with filters
        _extract_filter_predicates(
            pp["filter_columns"], column_stats, table_stats, abbrev, filters
        )

    for child in node.get("children", []):
        _collect_scan_filters(child, filters, column_stats, table_stats, abbrev)


def _extract_filter_predicates(fc, column_stats, table_stats, abbrev, filters):
    """Recursively extract filter predicates from a filter_columns tree.

    Handles:
      - Simple: {column: N, operator: '<=', literal: 42.0, children: []}
      - Compound AND: {column: null, operator: 'AND', children: [...]}
    """
    if fc is None:
        return

    op = fc.get("operator")
    col_idx = fc.get("column")

    if op == "AND" and fc.get("children"):
        for child in fc["children"]:
            _extract_filter_predicates(
                child, column_stats, table_stats, abbrev, filters
            )
        return

    if op == "OR" and fc.get("children"):
        # OR predicates: reconstruct as (p1 or p2 or ...)
        or_parts = []
        for child in fc["children"]:
            sub_filters = []
            _extract_filter_predicates(
                child, column_stats, table_stats, abbrev, sub_filters
            )
            or_parts.extend(sub_filters)
        if or_parts:
            filters.append("(" + " or ".join(or_parts) + ")")
        return

    if col_idx is None:
        return

    if col_idx >= len(column_stats):
        return

    cs = column_stats[col_idx]
    table_name = cs["tablename"]
    col_name = cs["attname"]

    if table_name not in abbrev:
        return

    alias = abbrev[table_name]
    col_name_lower = col_name.lower()
    literal = fc.get("literal")

    if literal is None:
        return

    # Format the literal
    literal_str = _format_literal(literal, cs.get("data_type", ""), operator=op)

    if literal_str is None:
        # Skip this filter (e.g., string != that PRICE can't handle)
        return

    if op in ("=", "!=", ">=", "<=", ">", "<"):
        filters.append(f"{alias}.{_quote_col(col_name_lower)} {op} {literal_str}")


def _try_date_to_epoch(s):
    """Try to convert a date/datetime string to epoch seconds.
    Returns float epoch or None if not a recognizable date format.
    """
    from datetime import datetime
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s.strip(), fmt)
            return int(dt.timestamp())
        except ValueError:
            continue
    return None


def _format_literal(literal, data_type="", operator="="):
    """Format a literal value for SQL output.

    For string literals:
      - Date-like strings ('2024-01-15') are converted to epoch seconds
        so PRICE can treat them as continuous numeric values.
      - Other strings are wrapped in quotes for discrete column handling.
      - For != operator on non-date strings, returns None (skip filter)
        because PRICE can't handle string != in continuous fallback.
    """
    if isinstance(literal, str):
        # Try date conversion first
        epoch = _try_date_to_epoch(literal)
        if epoch is not None:
            return str(epoch)

        # Non-date string: only emit for = operator (PRICE handles dsct =)
        # For != on string values, PRICE's fallback tries float conversion
        # which fails. Skip these filters.
        if operator == "!=":
            return None

        escaped = literal.replace("'", "''")
        return f"'{escaped}'"

    if isinstance(literal, float):
        # If it's a whole number, emit as integer
        if literal == int(literal) and abs(literal) < 1e15:
            return str(int(literal))
        return str(literal)

    if isinstance(literal, int):
        return str(literal)

    return str(literal)


def _parse_join_conds(join_conds, abbrev):
    """Parse root-level join_conds strings into PRICE-format join predicates.

    Handles two formats:
      Quoted:   '"table1"."col1" = "table2"."col2"'
      Unquoted: 'table1.col1 = table2.col2'
    Composite ones have AND:
      '"t1"."c1" = "t2"."c2" AND "t1"."c3" = "t2"."c4"'
    """
    # Quoted: "table"."col";? = "table"."col"
    _RE_QUOTED = re.compile(
        r'"([^"]+)"\.?"([^"]+)";?\s*=\s*"([^"]+)"\.?"([^"]+)"'
    )
    # Unquoted: table.col = table.col
    _RE_UNQUOTED = re.compile(
        r'(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)'
    )

    join_clauses = []

    for jc in join_conds:
        # Split composite joins on AND
        parts = re.split(r"\s+AND\s+", jc)
        for part in parts:
            part = part.strip()
            # Try quoted first, then unquoted
            m = _RE_QUOTED.match(part) or _RE_UNQUOTED.match(part)
            if m:
                t1, c1, t2, c2 = m.group(1), m.group(2), m.group(3), m.group(4)
                t1_lower = t1.lower()
                t2_lower = t2.lower()

                # Look up aliases (try both original case and lowercase)
                a1 = abbrev.get(t1) or abbrev.get(t1_lower)
                a2 = abbrev.get(t2) or abbrev.get(t2_lower)

                if a1 and a2:
                    join_clauses.append(f"{a1}.{_quote_col(c1.lower())} = {a2}.{_quote_col(c2.lower())}")
                else:
                    # Unknown table — skip this join condition
                    pass

    return join_clauses


def _prune_joins_to_spanning_tree(join_clauses, n_needed):
    """Prune join conditions to form a spanning tree using union-find.

    PRICE requires exactly (n_tables - 1) join conditions.
    When composite joins exist (e.g., two columns joining the same table pair),
    keep only enough joins to connect all tables.

    Args:
        join_clauses: list of "alias1.col1 = alias2.col2" strings
        n_needed: number of joins to keep (n_tables - 1)

    Returns:
        Pruned list of join clause strings
    """
    parent = {}

    def find(x):
        while parent.get(x, x) != x:
            parent[x] = parent.get(parent[x], parent[x])
            x = parent[x]
        return x

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx == ry:
            return False  # Cycle
        parent[rx] = ry
        return True

    kept = []
    for jc in join_clauses:
        parts = jc.split("=")
        if len(parts) != 2:
            kept.append(jc)
            continue
        left_table = parts[0].strip().split(".")[0]
        right_table = parts[1].strip().split(".")[0]
        if union(left_table, right_table):
            kept.append(jc)
            if len(kept) >= n_needed:
                break
        else:
            # Redundant join (cycle) — skip
            pass

    return kept


def reconstruct_sql_from_plan(plan, table_stats, column_stats, abbrev):
    """Reconstruct a single PRICE-format SQL from a plan tree.

    Args:
        plan: dict with 'plan_parameters', 'children', 'join_conds'
        table_stats: list of {relname, reltuples, ...}
        column_stats: list of {tablename, attname, data_type, ...}
        abbrev: {table_name: price_alias}

    Returns:
        SQL string or None if reconstruction fails
    """
    try:
        # 1. Collect tables from scan nodes
        table_indices = set()
        _collect_scan_tables(plan, table_indices)

        if not table_indices:
            return None

        # Map indices to table names and then to aliases
        from_tables = []
        seen_aliases = set()
        for idx in sorted(table_indices):
            if idx >= len(table_stats):
                continue
            table_name = table_stats[idx]["relname"]
            alias = abbrev.get(table_name)
            if alias and alias not in seen_aliases:
                from_tables.append(alias)
                seen_aliases.add(alias)

        if not from_tables:
            return None

        # 2. Parse join conditions
        join_conds = plan.get("join_conds", [])
        join_clauses = _parse_join_conds(join_conds, abbrev)

        # 2b. Prune redundant joins to satisfy PRICE's tree constraint:
        #     len(tables) == len(joins) + 1
        #     Use union-find to keep a spanning tree of join conditions.
        n_needed = len(from_tables) - 1
        if len(join_clauses) > n_needed and n_needed >= 0:
            join_clauses = _prune_joins_to_spanning_tree(join_clauses, n_needed)

        # 3. Collect filter predicates from scan nodes
        filters = []
        _collect_scan_filters(plan, filters, column_stats, table_stats, abbrev)

        # 4. Build the SQL
        from_clause = ", ".join(from_tables)

        where_parts = join_clauses + filters
        if where_parts:
            where_clause = " and ".join(where_parts)
            sql = f"select count(*) from {from_clause} where {where_clause}"
        else:
            sql = f"select count(*) from {from_clause}"

        return sql

    except Exception:
        return None


def reconstruct_all_sql(json_path, db_name, abbrev):
    """Reconstruct PRICE-format SQL for all plans in a JSON file.

    Args:
        json_path: path to deepdb_augmented JSON file
        db_name: database name (for logging)
        abbrev: {table_name: price_alias} mapping

    Returns:
        list of (sql_string | None) — one per plan
    """
    with open(json_path) as f:
        data = json.load(f)

    table_stats = data["database_stats"]["table_stats"]
    column_stats = data["database_stats"]["column_stats"]
    plans = data["parsed_plans"]

    results = []
    for plan in plans:
        sql = reconstruct_sql_from_plan(plan, table_stats, column_stats, abbrev)
        results.append(sql)

    return results


def reconstruct_all_sql_from_data(data, db_name, abbrev):
    """Same as reconstruct_all_sql but accepts pre-loaded JSON data.

    Args:
        data: parsed JSON dict with 'parsed_plans', 'database_stats'
        db_name: database name (for logging)
        abbrev: {table_name: price_alias} mapping

    Returns:
        list of (sql_string | None) — one per plan
    """
    table_stats = data["database_stats"]["table_stats"]
    column_stats = data["database_stats"]["column_stats"]
    plans = data["parsed_plans"]

    results = []
    for plan in plans:
        sql = reconstruct_sql_from_plan(plan, table_stats, column_stats, abbrev)
        results.append(sql)

    return results


def save_all_sql(output_dir, db_names=None):
    """Reconstruct and save SQL for cross-workload databases.

    For each database and each JSON file, writes one .sql file with one query
    per line.  Failed reconstructions are written as empty lines so that line
    numbers stay aligned with the plan indices.

    Args:
        output_dir: directory to write .sql files into
        db_names: list of database names, or None for all 20
    """
    from cross_workload_price_config import CROSS_WORKLOAD_ABBREV

    deepdb = os.path.join(os.path.dirname(__file__), "..", "deepdb_augmented")
    deepdb = os.path.normpath(deepdb)

    if db_names is None:
        db_names = sorted(
            d for d in os.listdir(deepdb)
            if os.path.isdir(os.path.join(deepdb, d))
        )

    os.makedirs(output_dir, exist_ok=True)

    for db_name in db_names:
        abbrev = CROSS_WORKLOAD_ABBREV.get(db_name, {})
        db_dir = os.path.join(deepdb, db_name)
        json_files = sorted(
            f for f in os.listdir(db_dir) if f.endswith(".json")
        )

        for jf in json_files:
            json_path = os.path.join(db_dir, jf)
            sqls = reconstruct_all_sql(json_path, db_name, abbrev)

            # Name: {db}_{workload_stem}.sql  e.g. financial_workload_100k_s1_c8220.sql
            stem = jf.replace(".json", "")
            out_name = f"{db_name}_{stem}.sql"
            out_path = os.path.join(output_dir, out_name)

            total = len(sqls)
            success = sum(1 for s in sqls if s is not None)

            with open(out_path, "w") as f:
                for sql in sqls:
                    f.write((sql or "") + "\n")

            print(f"{out_name}: {success}/{total} ({100*success/total:.1f}%)")


if __name__ == "__main__":
    import argparse
    import sys
    sys.path.insert(0, os.path.dirname(__file__))

    parser = argparse.ArgumentParser(
        description="Reconstruct PRICE-format SQL from deepdb_augmented plan trees"
    )
    parser.add_argument(
        "--output_dir", "-o",
        default=os.path.join(
            os.path.dirname(__file__), "..", "queries_true_sql", "cross_workload"
        ),
        help="Directory to write .sql files (default: queries_true_sql/cross_workload/)",
    )
    parser.add_argument(
        "--db", nargs="*", default=None,
        help="Database name(s) to process (default: all 20)",
    )
    args = parser.parse_args()

    save_all_sql(args.output_dir, args.db)
