"""
PRICE data pipeline utilities for Joint LLM+PRICE finetuning.

Handles:
- Extracting raw SQL from queries_true_sql files
- Transforming SQL to PRICE-compatible alias format
- Flattening CTEs, VIEWs, and subqueries for PRICE compatibility
- Extracting pg_est_card from query plan JSON
- Generating PRICE features (Sql2Feature)
- Padding and caching features
"""

import os
import re
import sys
import json
import pickle
import logging
import numpy as np
import torch

try:
    import sqlglot
    from sqlglot import exp as sqlglot_exp
    HAS_SQLGLOT = True
except ImportError:
    HAS_SQLGLOT = False

# Add PRICE to path — prefer local bundled copy, fall back to /root/PRICE
_LOCAL_PRICE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "PRICE")
PRICE_ROOT = _LOCAL_PRICE if os.path.isdir(os.path.join(_LOCAL_PRICE, "setup")) else "/root/PRICE"
if PRICE_ROOT not in sys.path:
    sys.path.insert(0, PRICE_ROOT)

# Local PRICE statistics bundled with LLM4QPR (preferred over PRICE_ROOT)
_LLM4QPR_STATS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "price_statistics")

def _get_stats_dir(db_name: str) -> str:
    """Return the statistics directory for a given database, preferring local copy."""
    local = os.path.join(_LLM4QPR_STATS_DIR, db_name)
    if os.path.isdir(local):
        return local
    return os.path.join(PRICE_ROOT, "datas", "statistics", "finetune", db_name)

logger = logging.getLogger("main_logger")

# Column prefix → table name for bare column resolution in TPC-H/DS queries
# Sorted by prefix length (longest first) to avoid partial matches
_TPCH_COL_PREFIX = [
    ('ps_', 'partsupp'),
    ('c_', 'customer'),
    ('o_', 'orders'),
    ('l_', 'lineitem'),
    ('p_', 'part'),
    ('s_', 'supplier'),
    ('n_', 'nation'),
    ('r_', 'region'),
]

_TPCDS_COL_PREFIX = [
    ('inv_', 'inventory'),
    ('web_', 'web_site'),
    ('ss_', 'store_sales'),
    ('sr_', 'store_returns'),
    ('cs_', 'catalog_sales'),
    ('cr_', 'catalog_returns'),
    ('ws_', 'web_sales'),
    ('wr_', 'web_returns'),
    ('ca_', 'customer_address'),
    ('cd_', 'customer_demographics'),
    ('hd_', 'household_demographics'),
    ('wp_', 'web_page'),
    ('cp_', 'catalog_page'),
    ('cc_', 'call_center'),
    ('ib_', 'income_band'),
    ('sm_', 'ship_mode'),
    ('c_', 'customer'),
    ('d_', 'date_dim'),
    ('t_', 'time_dim'),
    ('i_', 'item'),
    ('s_', 'store'),
    ('w_', 'warehouse'),
    ('p_', 'promotion'),
    ('r_', 'reason'),
]


def extract_raw_sql_from_queries_true(sql_file):
    """
    Parse queries_true_sql/{workload}.sql and extract raw SQL strings.

    Handles three formats:
      Format A (2-line): EXPLAIN ... \\n SELECT ... ;  -- label: <value>
      Format B (1-line): EXPLAIN ... SELECT ... ;
      Format C (multiline): EXPLAIN ... \\n select\\n  col,\\n  ...\\nfrom\\n  ...;

    Returns list of raw SQL strings (without EXPLAIN prefix).
    """
    EXPLAIN_PREFIX = "EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)"

    with open(sql_file, "r") as f:
        content = f.read()

    # Extract CREATE VIEW revenue0 definitions with date filters (TPC-H Q15).
    # Each Q15 instance has: drop view revenue0; create or replace view revenue0 ...
    #   l_shipdate >= date 'YYYY-MM-DD' ... ; EXPLAIN (...) select ... from supplier, revenue0 ...
    # We capture the start date from each CREATE VIEW to attach to the following query.
    revenue0_views = []  # list of (position_in_content, start_date_str)
    for vm in re.finditer(
        r"create\s+or\s+replace\s+view\s+revenue0\b[^;]*?"
        r"l_shipdate\s*>=\s*date\s+'(\d{4}-\d{2}-\d{2})'",
        content, re.IGNORECASE
    ):
        revenue0_views.append((vm.start(), vm.group(1)))

    # Split on EXPLAIN prefix to get each query block
    parts = re.split(r'(?=EXPLAIN\s*\(FORMAT\s+JSON)', content, flags=re.IGNORECASE)

    # Track character positions of each part for matching to CREATE VIEW positions
    part_starts = []
    pos = 0
    for part in parts:
        part_starts.append(pos)
        pos += len(part)

    sql_list = []
    for i, part in enumerate(parts):
        part = part.strip()
        if not part.upper().startswith("EXPLAIN"):
            continue

        # Remove EXPLAIN prefix
        m = re.match(r'EXPLAIN\s*\(FORMAT\s+JSON[^)]*\)\s*', part, re.IGNORECASE)
        if not m:
            continue
        sql_text = part[m.end():]

        # Find end of SQL: first semicolon at a non-quoted position
        depth = 0
        in_quote = False
        end_pos = len(sql_text)
        for j, ch in enumerate(sql_text):
            if in_quote:
                if ch == "'":
                    in_quote = False
            else:
                if ch == "'":
                    in_quote = True
                elif ch == ';':
                    end_pos = j
                    break

        sql_text = sql_text[:end_pos].strip()

        # Remove trailing comment "-- label: ..."
        # Only strip if it's at the end (not inside the SQL)
        lines = sql_text.split('\n')
        if lines and '--' in lines[-1]:
            lines[-1] = lines[-1][:lines[-1].rfind('--')].strip()
        sql_text = ' '.join(l.strip() for l in lines if l.strip())

        # Attach revenue0 date filters from preceding CREATE VIEW (Q15)
        if sql_text and 'revenue0' in sql_text.lower() and revenue0_views:
            cur_pos = part_starts[i]
            # Find the latest CREATE VIEW before this EXPLAIN
            best_date = None
            for vpos, vdate in revenue0_views:
                if vpos < cur_pos:
                    best_date = vdate
            if best_date:
                # Compute end date = start + 3 months
                y, mo, d = int(best_date[:4]), int(best_date[5:7]), int(best_date[8:10])
                mo += 3
                if mo > 12:
                    mo -= 12
                    y += 1
                end_date = f"{y:04d}-{mo:02d}-{d:02d}"
                sql_text = f"-- REVENUE0_DATES: {best_date} {end_date}\n{sql_text}"

        if sql_text:
            sql_list.append(sql_text)

    return sql_list


def _load_abbrev_mapping(db_name, bin_size=40):
    """
    Load the abbreviation mapping from PRICE statistics.
    Returns dict: {full_table_name: price_alias} e.g. {'title': 'imdb_t'}
    """
    stats_dir = _get_stats_dir(db_name)
    abbrev_path = os.path.join(stats_dir, "abbrev_col_type.pkl")
    with open(abbrev_path, "rb") as f:
        data = pickle.load(f)
    return data["abbrev"]  # e.g. {'title': 'imdb_t', 'movie_info': 'imdb_mi', ...}


# --- Statistics cache for scalar subquery estimation ---
_histogram_cache = {}


def _load_histogram_stats(db_name):
    """Load histogram statistics for aggregate estimation."""
    if db_name in _histogram_cache:
        return _histogram_cache[db_name]
    stats_dir = _get_stats_dir(db_name)
    hist_path = os.path.join(stats_dir, "histogram40.pkl")
    if os.path.exists(hist_path):
        with open(hist_path, "rb") as f:
            hist = pickle.load(f)
        _histogram_cache[db_name] = hist
        return hist
    _histogram_cache[db_name] = {}
    return {}


def _estimate_aggregate_value(db_name, col_name, agg_func):
    """
    Estimate the result of an aggregate function using histogram statistics.

    For SUM, estimates per-group value (suitable for correlated subqueries)
    using histogram mean * estimated group size.

    Returns estimated float value, or None if column not found.
    """
    hist = _load_histogram_stats(db_name)
    col_lower = col_name.lower()

    # Search all tables for this column
    for table_alias, cols in hist.items():
        if col_lower in cols:
            col_stats = cols[col_lower]
            min_val = float(col_stats.get('min_value', 0))
            max_val = float(col_stats.get('max_value', 0))
            total_rows = float(col_stats.get('len', 1))

            # Compute mean from histogram if available
            hist_arr = col_stats.get('hist', None)
            edges = col_stats.get('bin_edges', None)
            if hist_arr is not None and edges is not None and len(hist_arr) > 0 and len(edges) > 1:
                bin_centers = [(float(edges[i]) + float(edges[i+1])) / 2 for i in range(len(hist_arr))]
                hist_total = sum(hist_arr)
                mean = sum(c * h for c, h in zip(bin_centers, hist_arr)) / hist_total if hist_total > 0 else (min_val + max_val) / 2.0
            else:
                mean = (min_val + max_val) / 2.0

            if agg_func == 'MIN':
                return min_val
            elif agg_func == 'MAX':
                return max_val
            elif agg_func == 'AVG':
                return mean
            elif agg_func == 'COUNT':
                return total_rows
            elif agg_func == 'SUM':
                # Estimate per-group SUM for correlated subqueries
                # group_size heuristic: total_rows^0.25 (geometric mean of 1 and sqrt)
                group_size = max(1.0, total_rows ** 0.25)
                return mean * group_size
    return None


def _convert_timestamps_to_epoch(sql):
    """
    Convert PostgreSQL timestamp/date literals to epoch seconds so PRICE can parse them as floats.

    Handles formats like:
    - '2014-09-04 23:10:09'::timestamp
    - CAST('2014-09-04 23:10:09' AS TIMESTAMP)
    - date '1995-03-17'
    - date '1993-01-01' + interval '1 year'
    - date '1998-12-01' - interval '68 days'
    """
    from datetime import datetime, timedelta
    import calendar

    def _ts_to_epoch(match):
        ts_str = match.group(1)
        try:
            dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
            return str(int(dt.timestamp()))
        except ValueError:
            try:
                dt = datetime.strptime(ts_str, "%Y-%m-%d")
                return str(int(dt.timestamp()))
            except ValueError:
                return match.group(0)  # Can't parse, keep original

    def _add_interval(dt, num, unit):
        """Add an interval to a datetime, handling months/years."""
        unit = unit.lower().rstrip('s')
        if unit == 'day':
            return dt + timedelta(days=num)
        elif unit == 'month':
            month = dt.month + num
            year = dt.year + (month - 1) // 12
            month = (month - 1) % 12 + 1
            max_day = calendar.monthrange(year, month)[1]
            return dt.replace(year=year, month=month, day=min(dt.day, max_day))
        elif unit == 'year':
            try:
                return dt.replace(year=dt.year + num)
            except ValueError:
                return dt.replace(year=dt.year + num, day=28)
        return dt

    def _date_interval_to_epoch(match):
        date_str = match.group(1)
        op = match.group(2)
        num = int(match.group(3))
        unit = match.group(4)
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            if op == '-':
                num = -num
            result = _add_interval(dt, num, unit)
            return str(int(result.timestamp()))
        except (ValueError, OverflowError):
            return match.group(0)

    # Match '...'::timestamp (PostgreSQL cast syntax)
    sql = re.sub(r"'(\d{4}-\d{2}-\d{2}[\s\d:]*)'::timestamp", _ts_to_epoch, sql, flags=re.IGNORECASE)
    # Match CAST('...' AS TIMESTAMP)
    sql = re.sub(r"CAST\('(\d{4}-\d{2}-\d{2}[\s\d:]*)'\s+AS\s+TIMESTAMP\)", _ts_to_epoch, sql, flags=re.IGNORECASE)
    # Match date '...' +/- interval '...' (MUST be before standalone date pattern)
    sql = re.sub(
        r"date\s+'(\d{4}-\d{2}-\d{2})'\s*([+-])\s*interval\s+'(\d+)\s+(\w+)'",
        _date_interval_to_epoch, sql, flags=re.IGNORECASE
    )

    # Match CAST('...' AS DATE) +/- N (TPC-DS pattern: integer days added to date)
    def _cast_date_plus_int(match):
        date_str = match.group(1)
        op = match.group(2)
        days = int(match.group(3))
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            if op == '-':
                days = -days
            result = dt + timedelta(days=days)
            return str(int(result.timestamp()))
        except (ValueError, OverflowError):
            return match.group(0)

    sql = re.sub(
        r"\(?cast\s*\(\s*'(\d{4}-\d{1,2}-\d{1,2})'\s+as\s+date\s*\)\s*\)?\s*([+-])\s*(\d+)",
        _cast_date_plus_int, sql, flags=re.IGNORECASE
    )

    # Match standalone CAST('...' AS DATE) without arithmetic
    def _cast_date_to_epoch(match):
        date_str = match.group(1)
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return str(int(dt.timestamp()))
        except ValueError:
            return match.group(0)

    sql = re.sub(
        r"cast\s*\(\s*'(\d{4}-\d{1,2}-\d{1,2})'\s+as\s+date\s*\)",
        _cast_date_to_epoch, sql, flags=re.IGNORECASE
    )

    # Match standalone date '...' (TPC-H/DS style date literals)
    sql = re.sub(r"\bdate\s+'(\d{4}-\d{2}-\d{2})'", _ts_to_epoch, sql, flags=re.IGNORECASE)
    return sql


def _strip_trailing_clauses(where_clause):
    """Strip GROUP BY, ORDER BY, LIMIT, HAVING from end of WHERE clause (top-level only)."""
    keywords = ['group by', 'order by', 'limit ', 'having ']
    lower = where_clause.lower()
    depth = 0
    for i, char in enumerate(where_clause):
        if char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
        elif depth == 0:
            for kw in keywords:
                if lower[i:i + len(kw)] == kw:
                    # Check word boundary: not preceded by alphanumeric
                    if i > 0 and lower[i - 1].isalnum():
                        continue
                    return where_clause[:i].strip()
    return where_clause


# ============================================================================
# SQL FLATTENING: CTEs, VIEWs, subqueries-in-FROM → flat PRICE SQL
# ============================================================================

# TPC-H Q15: VIEW revenue0 reference body (for documentation only).
# Dates are now extracted from CREATE VIEW statements by extract_raw_sql_from_queries_true()
# and attached as -- REVENUE0_DATES comments, then used by _flatten_revenue0_query().


def _flatten_and(node, results):
    """Recursively flatten nested AND / Paren nodes into a flat list."""
    if isinstance(node, sqlglot_exp.Paren):
        _flatten_and(node.this, results)
    elif isinstance(node, sqlglot_exp.And):
        _flatten_and(node.left, results)
        _flatten_and(node.right, results)
    else:
        results.append(node)


def _is_constant(node):
    """Check if expression has no Column or Subquery refs (is a literal/constant)."""
    if isinstance(node, sqlglot_exp.Column):
        return False
    if isinstance(node, sqlglot_exp.Subquery):
        return False
    for child in node.iter_expressions():
        if not _is_constant(child):
            return False
    return True


def _get_from_sources(select_node):
    """Get (source_node, alias_or_name) pairs from a SELECT's FROM + JOINs."""
    sources = []
    from_clause = select_node.args.get('from_')
    if from_clause:
        src = from_clause.this
        alias = src.alias or (src.name if isinstance(src, sqlglot_exp.Table) else '')
        sources.append((src, alias))
    for join in select_node.args.get('joins') or []:
        src = join.this
        alias = src.alias or (src.name if isinstance(src, sqlglot_exp.Table) else '')
        sources.append((src, alias))
        # Also collect ON conditions as part of the WHERE (for JOIN...ON syntax)
        on_cond = join.args.get('on')
        if on_cond:
            sources.append(('__on__', on_cond.this))
    return sources


_SIMPLE_OPS = (
    sqlglot_exp.EQ, sqlglot_exp.NEQ,
    sqlglot_exp.GT, sqlglot_exp.GTE,
    sqlglot_exp.LT, sqlglot_exp.LTE,
)
_OP_STR = {
    sqlglot_exp.EQ: '=', sqlglot_exp.NEQ: '!=',
    sqlglot_exp.GT: '>', sqlglot_exp.GTE: '>=',
    sqlglot_exp.LT: '<', sqlglot_exp.LTE: '<=',
}


def _classify_condition(cond):
    """
    Classify a single WHERE condition.

    Returns:
      ('join', left_col_sql, right_col_sql)          - equi-join
      ('filter', col_sql, op_str, value_sql)          - simple comparison filter
      ('skip', reason)                                 - unsupported (OR, LIKE, IN, subquery, etc.)
    """
    if isinstance(cond, sqlglot_exp.Paren):
        return _classify_condition(cond.this)

    # OR → unsupported
    if isinstance(cond, sqlglot_exp.Or):
        return ('skip', 'OR')

    # Column = Column → equi-join
    if isinstance(cond, sqlglot_exp.EQ):
        left, right = cond.left, cond.right
        if isinstance(left, sqlglot_exp.Column) and isinstance(right, sqlglot_exp.Column):
            return ('join', left.sql(), right.sql())

    # Simple comparison: Column op constant
    if type(cond) in _SIMPLE_OPS:
        left, right = cond.left, cond.right
        op_str = _OP_STR[type(cond)]
        if isinstance(left, sqlglot_exp.Column) and _is_constant(right):
            return ('filter', left.sql(), op_str, right.sql())
        if isinstance(right, sqlglot_exp.Column) and _is_constant(left):
            # Flip: constant op column → column op' constant
            flip = {'=': '=', '!=': '!=', '>': '<', '>=': '<=', '<': '>', '<=': '>='}
            return ('filter', right.sql(), flip[op_str], left.sql())

    # BETWEEN → two filters
    if isinstance(cond, sqlglot_exp.Between):
        col = cond.this
        if isinstance(col, sqlglot_exp.Column):
            low = cond.args['low'].sql()
            high = cond.args['high'].sql()
            return ('between', col.sql(), low, high)

    # IN (value list) → range envelope (numeric) or representative equality (string)
    if isinstance(cond, sqlglot_exp.In):
        col = cond.this
        values = cond.expressions  # empty for IN-subquery
        if isinstance(col, sqlglot_exp.Column) and values:
            # Check if all values are numeric literals
            nums = []
            for v in values:
                if isinstance(v, sqlglot_exp.Literal) and not v.is_string:
                    try:
                        nums.append(float(v.this))
                    except (ValueError, TypeError):
                        break
                elif isinstance(v, sqlglot_exp.Neg) and isinstance(v.this, sqlglot_exp.Literal):
                    try:
                        nums.append(-float(v.this.this))
                    except (ValueError, TypeError):
                        break
                else:
                    break
            if len(nums) == len(values) and nums:
                # All numeric → range envelope
                return ('between', col.sql(), str(min(nums)), str(max(nums)))
            # Check if all values are string literals
            strs = []
            for v in values:
                if isinstance(v, sqlglot_exp.Literal) and v.is_string:
                    strs.append(v.sql())  # includes quotes
                else:
                    break
            if len(strs) == len(values) and strs:
                # All strings → use first as representative equality
                return ('filter', col.sql(), '=', strs[0])

    # Everything else (LIKE, NOT, EXISTS, subquery comparisons) → skip
    return ('skip', type(cond).__name__)


def _collect_union_branches(node, branches):
    """Recursively collect all SELECT branches from a UNION ALL chain."""
    if isinstance(node, sqlglot_exp.Union):
        _collect_union_branches(node.left, branches)
        _collect_union_branches(node.right, branches)
    elif isinstance(node, sqlglot_exp.Subquery):
        _collect_union_branches(node.this, branches)
    elif isinstance(node, sqlglot_exp.Select):
        branches.append(node)


def _extract_branch_info(branch_sel):
    """Extract alias_map, tables, tbl_aliases, joins, filters from a single SELECT branch."""
    alias_map = {}
    for sel_expr in branch_sel.expressions:
        if isinstance(sel_expr, sqlglot_exp.Alias):
            underlying = sel_expr.this
            if isinstance(underlying, sqlglot_exp.Column):
                alias_map[sel_expr.alias.lower()] = underlying.name.lower()
            else:
                alias_map[sel_expr.alias.lower()] = None  # aggregate/expr
        elif isinstance(sel_expr, sqlglot_exp.Column):
            alias_map[sel_expr.name.lower()] = sel_expr.name.lower()

    tables = set()
    tbl_aliases = {}
    for src, alias in _get_from_sources(branch_sel):
        if src == '__on__':
            continue
        if isinstance(src, sqlglot_exp.Table):
            tables.add(src.name.lower())
            a = (src.alias or src.name).lower()
            tbl_aliases[a] = src.name.lower()

    joins, filters = [], []
    where = branch_sel.args.get('where')
    if where:
        conditions = []
        _flatten_and(where.this, conditions)
        for c in conditions:
            cl = _classify_condition(c)
            if cl[0] == 'join':
                joins.append((cl[1], cl[2]))
            elif cl[0] == 'filter':
                filters.append((cl[1], cl[2], cl[3]))
            elif cl[0] == 'between':
                filters.append((cl[1], '>=', cl[2]))
                filters.append((cl[1], '<=', cl[3]))

    for src, alias in _get_from_sources(branch_sel):
        if src == '__on__' and alias is not None:
            on_conds = []
            _flatten_and(alias, on_conds)
            for c in on_conds:
                cl = _classify_condition(c)
                if cl[0] == 'join':
                    joins.append((cl[1], cl[2]))
                elif cl[0] == 'filter':
                    filters.append((cl[1], cl[2], cl[3]))

    return alias_map, tables, tbl_aliases, joins, filters


def _build_cte_info(ast):
    """Extract CTE metadata: alias maps, base tables, joins, filters."""
    info = {
        'names': set(),
        'alias_maps': {},          # cte_name → {cte_col: base_col_name} (first branch)
        'all_branch_maps': {},     # cte_name → [{cte_col: base_col}, ...] (all branches)
        'base_tables': {},         # cte_name → set of base table names
        'table_aliases': {},       # cte_name → {alias_in_cte: real_table_name}
        'joins': {},               # cte_name → [(left_sql, right_sql), ...]
        'filters': {},             # cte_name → [(col_sql, op, val), ...]
    }
    with_clause = ast.args.get('with_')
    if not with_clause:
        return info

    for cte in with_clause.find_all(sqlglot_exp.CTE):
        name = cte.alias
        info['names'].add(name)
        inner_sel = cte.this

        if isinstance(inner_sel, sqlglot_exp.Union):
            # UNION ALL CTE: process ALL branches
            branches = []
            _collect_union_branches(inner_sel, branches)

            all_alias_maps = []
            all_tables = set()
            all_tbl_aliases = {}
            all_joins = []
            all_filters = []

            for branch in branches:
                alias_map, tables, tbl_aliases, joins, filters = _extract_branch_info(branch)
                all_alias_maps.append(alias_map)
                all_tables.update(tables)
                all_tbl_aliases.update(tbl_aliases)
                all_joins.extend(joins)
                all_filters.extend(filters)

            info['alias_maps'][name] = all_alias_maps[0] if all_alias_maps else {}
            info['all_branch_maps'][name] = all_alias_maps
            info['base_tables'][name] = all_tables
            info['table_aliases'][name] = all_tbl_aliases
            info['joins'][name] = all_joins
            info['filters'][name] = all_filters
        else:
            # Normal CTE: single SELECT
            alias_map, tables, tbl_aliases, joins, filters = _extract_branch_info(inner_sel)
            info['alias_maps'][name] = alias_map
            info['all_branch_maps'][name] = [alias_map]
            info['base_tables'][name] = tables
            info['table_aliases'][name] = tbl_aliases
            info['joins'][name] = joins
            info['filters'][name] = filters

    return info


def _resolve_col_through_cte(col_sql, alias_to_cte, cte_info):
    """
    Resolve a column reference that goes through a CTE alias.

    Returns a list of resolved column names (one per UNION branch).
    For non-CTE columns, returns [col_sql].
    For unresolvable (aggregate) columns, returns [None].

    e.g. 'ctr1.ctr_store_sk' where ctr1 → CTE 'customer_total_return'
    and ctr_store_sk → sr_store_sk → returns ['sr_store_sk']

    For UNION ALL CTEs: 'wscs.sold_date_sk' → ['ws_sold_date_sk', 'cs_sold_date_sk']
    """
    parts = col_sql.split('.')
    if len(parts) == 2:
        table_alias, col_name = parts[0].lower(), parts[1].lower()
        if table_alias not in alias_to_cte:
            return [col_sql]  # Not a CTE reference

        cte_name = alias_to_cte[table_alias]
        # Check multi-branch maps (UNION ALL CTEs)
        all_maps = cte_info.get('all_branch_maps', {}).get(cte_name, [])
        if len(all_maps) > 1:
            results = []
            for branch_map in all_maps:
                base_col = branch_map.get(col_name)
                if base_col is not None:
                    results.append(base_col)
            return results if results else [None]
        # Single branch
        amap = cte_info['alias_maps'].get(cte_name, {})
        base_col = amap.get(col_name)
        return [base_col] if base_col is not None else [None]

    # Unqualified column: check if it matches any CTE's alias map
    col_name = parts[0].lower()
    for cte_alias, cte_name in alias_to_cte.items():
        all_maps = cte_info.get('all_branch_maps', {}).get(cte_name, [])
        if len(all_maps) > 1:
            results = []
            for branch_map in all_maps:
                base_col = branch_map.get(col_name)
                if base_col is not None:
                    results.append(base_col)
            if results:
                return results
        else:
            amap = cte_info['alias_maps'].get(cte_name, {})
            base_col = amap.get(col_name)
            if base_col is not None:
                return [base_col]

    return [col_sql]  # Can't resolve through CTE, return as-is


def _unwrap_from_subquery(sel):
    """If the FROM clause is a subquery, recurse to get the inner SELECT."""
    from_clause = sel.args.get('from_')
    if from_clause and isinstance(from_clause.this, sqlglot_exp.Subquery):
        inner = from_clause.this.this
        if isinstance(inner, sqlglot_exp.Select):
            return _unwrap_from_subquery(inner)
    return sel


def flatten_sql_for_price(sql, db_name):
    """
    Flatten complex SQL (CTEs, subqueries-in-FROM, VIEWs) into a simple
    SELECT COUNT(*) FROM t1, t2, ... WHERE join1 AND join2 AND filter1 ...

    Returns flattened SQL string, or None if flattening fails.

    PRICE requires:
    - Comma-separated FROM (no JOIN...ON)
    - WHERE clause with equi-joins and simple comparison filters
    - N-1 equi-joins for N tables (tree topology)
    - All columns as table.column format
    """
    if not HAS_SQLGLOT:
        return None

    # --- Extract revenue0 date filters from comment (injected by extract_raw_sql) ---
    revenue0_start, revenue0_end = None, None
    clean_sql = sql
    date_m = re.match(r'--\s*REVENUE0_DATES:\s*(\S+)\s+(\S+)\s*\n?', sql)
    if date_m:
        revenue0_start, revenue0_end = date_m.group(1), date_m.group(2)
        clean_sql = sql[date_m.end():]

    try:
        ast = sqlglot.parse_one(clean_sql)
    except Exception:
        return None

    # --- Handle TPC-H Q15 VIEW: expand revenue0 inline ---
    if db_name == 'tpch':
        has_revenue0 = False
        for t in ast.find_all(sqlglot_exp.Table):
            if t.name.lower() == 'revenue0':
                has_revenue0 = True
                break
        if has_revenue0:
            return _flatten_revenue0_query(revenue0_start, revenue0_end)

    # --- Build CTE info ---
    cte_info = _build_cte_info(ast)

    # --- Unwrap subquery-in-FROM ---
    main_sel = _unwrap_from_subquery(ast)

    # --- Collect base tables ---
    base_tables = set()          # set of real table names
    table_aliases = {}           # alias → real_table_name (for non-CTE tables)
    alias_to_cte = {}            # alias → CTE name (for CTE references in main query)

    for src, alias in _get_from_sources(main_sel):
        if src == '__on__':
            continue
        if isinstance(src, sqlglot_exp.Table):
            tname = src.name.lower()
            a = alias.lower() if alias else tname
            if tname in cte_info['names']:
                alias_to_cte[a] = tname
                base_tables.update(cte_info['base_tables'].get(tname, set()))
            else:
                base_tables.add(tname)
                table_aliases[a] = tname

    if not base_tables:
        return None

    # --- Collect conditions from main SELECT ---
    main_joins = []
    main_filters = []
    where = main_sel.args.get('where')
    if where:
        conditions = []
        _flatten_and(where.this, conditions)
        for c in conditions:
            cl = _classify_condition(c)
            if cl[0] == 'join':
                main_joins.append((cl[1], cl[2]))
            elif cl[0] == 'filter':
                main_filters.append((cl[1], cl[2], cl[3]))
            elif cl[0] == 'between':
                main_filters.append((cl[1], '>=', cl[2]))
                main_filters.append((cl[1], '<=', cl[3]))

    # Also collect ON conditions from JOINs in main query
    for src, alias in _get_from_sources(main_sel):
        if src == '__on__' and alias is not None:
            on_conds = []
            _flatten_and(alias, on_conds)
            for c in on_conds:
                cl = _classify_condition(c)
                if cl[0] == 'join':
                    main_joins.append((cl[1], cl[2]))
                elif cl[0] == 'filter':
                    main_filters.append((cl[1], cl[2], cl[3]))

    # --- Helper: strip table alias prefix, leaving bare column name ---
    # Build combined alias→table mapping from main query + all CTE internals
    all_tbl_aliases = dict(table_aliases)  # alias→real_table from main query
    for cte_name in cte_info.get('table_aliases', {}):
        all_tbl_aliases.update(cte_info['table_aliases'][cte_name])

    def _strip_alias(col_sql):
        """Strip table alias prefix, returning bare column name.
        'n1.n_nationkey' → 'n_nationkey', 'sr_store_sk' → 'sr_store_sk'"""
        if '.' in col_sql:
            parts = col_sql.split('.', 1)
            return parts[1]
        return col_sql

    # --- Merge CTE joins/filters ---
    all_joins = []
    all_filters = []

    # Add CTE-internal conditions for referenced CTEs
    referenced_ctes = set(alias_to_cte.values())
    for cte_name in referenced_ctes:
        for left, right in cte_info['joins'].get(cte_name, []):
            all_joins.append((_strip_alias(left), _strip_alias(right)))
        for col, op, val in cte_info['filters'].get(cte_name, []):
            all_filters.append((_strip_alias(col), op, val))

    # Resolve CTE column aliases in main-level conditions
    # _resolve_col_through_cte returns a list (one per UNION branch)
    for left_sql, right_sql in main_joins:
        resolved_lefts = _resolve_col_through_cte(left_sql, alias_to_cte, cte_info)
        resolved_rights = _resolve_col_through_cte(right_sql, alias_to_cte, cte_info)
        for rl in resolved_lefts:
            for rr in resolved_rights:
                if rl is not None and rr is not None:
                    all_joins.append((_strip_alias(rl), _strip_alias(rr)))

    for col_sql, op, val in main_filters:
        resolveds = _resolve_col_through_cte(col_sql, alias_to_cte, cte_info)
        for resolved in resolveds:
            if resolved is not None:
                all_filters.append((_strip_alias(resolved), op, val))

    if not all_joins and not all_filters:
        return None  # Nothing useful extracted

    # --- Deduplicate joins (same pair can come from CTE + main) ---
    seen_joins = set()
    deduped_joins = []
    for left, right in all_joins:
        key = (left.lower(), right.lower())
        rev_key = (right.lower(), left.lower())
        if key not in seen_joins and rev_key not in seen_joins:
            seen_joins.add(key)
            deduped_joins.append((left, right))
    all_joins = deduped_joins

    # --- Reconstruct flat SQL ---
    from_parts = sorted(base_tables)
    where_parts = []
    for left, right in all_joins:
        where_parts.append(f"{left} = {right}")
    for col, op, val in all_filters:
        where_parts.append(f"{col} {op} {val}")

    if not where_parts:
        return None

    flat_sql = f"SELECT COUNT(*) FROM {', '.join(from_parts)} WHERE {' AND '.join(where_parts)}"
    return flat_sql


def _flatten_revenue0_query(start_date=None, end_date=None):
    """
    Flatten TPC-H Q15 which references the VIEW revenue0.

    Expands to: SELECT COUNT(*) FROM supplier, lineitem
                WHERE s_suppkey = l_suppkey AND l_shipdate >= ... AND l_shipdate < ...

    The date filters come from the CREATE VIEW statement that precedes each Q15
    instance in tpch.sql, extracted by extract_raw_sql_from_queries_true().
    """
    flat = "SELECT COUNT(*) FROM supplier, lineitem WHERE s_suppkey = l_suppkey"
    if start_date and end_date:
        flat += f" AND l_shipdate >= date '{start_date}' AND l_shipdate < date '{end_date}'"
    return flat


# --- Subquery handling helpers ---


def _inline_exists_subqueries(ast, new_from_tables, tautology):
    """Inline EXISTS/NOT EXISTS subqueries: add inner tables to FROM, replace with join conditions."""

    def _process_exists(exists_node):
        """Extract tables and conditions from EXISTS subquery, return replacement expression."""
        inner_sel = exists_node.this
        if isinstance(inner_sel, sqlglot_exp.Subquery):
            inner_sel = inner_sel.this
        if not isinstance(inner_sel, sqlglot_exp.Select):
            return tautology.copy()

        # Collect inner FROM tables
        for tbl in inner_sel.find_all(sqlglot_exp.Table):
            new_from_tables.append(tbl.sql())

        # Collect conditions from inner WHERE
        inner_where = inner_sel.args.get('where')
        if not inner_where:
            return tautology.copy()

        conditions = []
        _flatten_and(inner_where.this, conditions)

        # Keep equi-join conditions and simple filters, drop non-equi (NEQ, LIKE, etc.)
        keep = []
        for cond in conditions:
            if isinstance(cond, sqlglot_exp.EQ):
                keep.append(cond.copy())
            elif isinstance(cond, (sqlglot_exp.GT, sqlglot_exp.GTE,
                                   sqlglot_exp.LT, sqlglot_exp.LTE)):
                keep.append(cond.copy())
            # Drop NEQ, LIKE, NOT, complex expressions

        if not keep:
            return tautology.copy()

        result = keep[0]
        for c in keep[1:]:
            result = sqlglot_exp.And(this=result, expression=c)
        return sqlglot_exp.Paren(this=result) if len(keep) > 1 else result

    # Handle NOT EXISTS: Not(Exists(...))
    for not_node in list(ast.find_all(sqlglot_exp.Not)):
        if isinstance(not_node.this, sqlglot_exp.Exists):
            replacement = _process_exists(not_node.this)
            not_node.replace(replacement)

    # Handle EXISTS
    for exists_node in list(ast.find_all(sqlglot_exp.Exists)):
        replacement = _process_exists(exists_node)
        exists_node.replace(replacement)


def _inline_in_subqueries(ast, new_from_tables, tautology):
    """Inline IN/NOT IN (subquery): add inner tables to FROM, replace with join condition."""

    def _process_in_subquery(in_node):
        """Process an IN node with a subquery. Returns replacement expression, or None if not a subquery IN."""
        subquery = in_node.args.get('query')
        if subquery is None:
            return None  # Value list IN, not subquery — skip

        col = in_node.this  # The outer column
        inner_sel = subquery.this if isinstance(subquery, sqlglot_exp.Subquery) else subquery
        if not isinstance(inner_sel, sqlglot_exp.Select):
            return tautology.copy()

        # Get the column returned by the subquery
        inner_exprs = inner_sel.expressions
        if not inner_exprs:
            return tautology.copy()

        inner_col_expr = inner_exprs[0]
        if isinstance(inner_col_expr, sqlglot_exp.Alias):
            inner_col_expr = inner_col_expr.this

        # Add inner tables to FROM
        for tbl in inner_sel.find_all(sqlglot_exp.Table):
            new_from_tables.append(tbl.sql())

        # Create equi-join: outer_col = inner_col
        join_cond = sqlglot_exp.EQ(this=col.copy(), expression=inner_col_expr.copy())

        # Collect inner WHERE conditions
        keep = [join_cond]
        inner_where = inner_sel.args.get('where')
        if inner_where:
            conditions = []
            _flatten_and(inner_where.this, conditions)
            for cond in conditions:
                if isinstance(cond, (sqlglot_exp.EQ, sqlglot_exp.GT, sqlglot_exp.GTE,
                                     sqlglot_exp.LT, sqlglot_exp.LTE)):
                    keep.append(cond.copy())

        result = keep[0]
        for c in keep[1:]:
            result = sqlglot_exp.And(this=result, expression=c)
        return sqlglot_exp.Paren(this=result) if len(keep) > 1 else result

    # Handle NOT IN (subquery): Not(In(...))
    for not_node in list(ast.find_all(sqlglot_exp.Not)):
        if isinstance(not_node.this, sqlglot_exp.In):
            replacement = _process_in_subquery(not_node.this)
            if replacement is not None:
                not_node.replace(replacement)

    # Handle IN (subquery)
    for in_node in list(ast.find_all(sqlglot_exp.In)):
        replacement = _process_in_subquery(in_node)
        if replacement is not None:
            in_node.replace(replacement)


def _estimate_scalar_subqueries(ast, db_name, tautology, new_from_tables=None, new_conditions=None):
    """Replace scalar subqueries in comparisons with estimated values from statistics.

    If new_from_tables/new_conditions are provided, also inlines the subquery's
    tables and correlated join conditions into the outer query.
    """

    def _extract_agg_info(select_node):
        """Extract (multiplier, agg_func_name, col_name) from a scalar subquery SELECT."""
        exprs = select_node.expressions
        if len(exprs) != 1:
            return None

        expr = exprs[0]
        if isinstance(expr, sqlglot_exp.Alias):
            expr = expr.this

        multiplier = 1.0

        # Handle multiplier: 0.2 * AGG(col) or AGG(col) * 0.2
        if isinstance(expr, sqlglot_exp.Mul):
            left, right = expr.this, expr.expression
            if isinstance(left, sqlglot_exp.Literal) and left.is_number:
                multiplier = float(left.this)
                expr = right
            elif isinstance(right, sqlglot_exp.Literal) and right.is_number:
                multiplier = float(right.this)
                expr = left

        # Check for aggregate function
        agg_map = {
            sqlglot_exp.Min: 'MIN',
            sqlglot_exp.Max: 'MAX',
            sqlglot_exp.Avg: 'AVG',
            sqlglot_exp.Sum: 'SUM',
            sqlglot_exp.Count: 'COUNT',
        }

        for agg_type, agg_name in agg_map.items():
            if isinstance(expr, agg_type):
                inner = expr.this
                if isinstance(inner, sqlglot_exp.Column):
                    return (multiplier, agg_name, inner.name.lower())
                return None

        return None

    # Find comparisons with subqueries
    for cmp_type in (sqlglot_exp.EQ, sqlglot_exp.LT, sqlglot_exp.GT,
                     sqlglot_exp.LTE, sqlglot_exp.GTE, sqlglot_exp.NEQ):
        for node in list(ast.find_all(cmp_type)):
            left = node.args.get('this')
            right = node.args.get('expression')

            subquery = None
            if isinstance(right, sqlglot_exp.Subquery):
                subquery = right
            elif isinstance(left, sqlglot_exp.Subquery):
                subquery = left

            if subquery is None:
                continue

            inner_sel = subquery.this
            if not isinstance(inner_sel, sqlglot_exp.Select):
                node.replace(tautology.copy())
                continue

            info = _extract_agg_info(inner_sel)
            if info is None:
                # Can't estimate aggregate, drop the filter
                node.replace(tautology.copy())
                continue

            multiplier, agg_func, col_name = info
            estimated = _estimate_aggregate_value(db_name, col_name, agg_func)
            if estimated is None:
                node.replace(tautology.copy())
                continue

            result_val = multiplier * estimated
            # Replace the subquery with the estimated literal
            if result_val == int(result_val):
                replacement_literal = sqlglot_exp.Literal.number(int(result_val))
            else:
                replacement_literal = sqlglot_exp.Literal.number(round(result_val, 4))
            subquery.replace(replacement_literal)

            # Inline subquery's tables and correlated conditions into outer query
            if new_from_tables is not None:
                for tbl in inner_sel.find_all(sqlglot_exp.Table):
                    tbl_sql = tbl.sql()
                    if tbl_sql:
                        new_from_tables.append(tbl_sql)

            if new_conditions is not None:
                inner_where = inner_sel.args.get('where')
                if inner_where:
                    inner_conds = []
                    _flatten_and(inner_where.this, inner_conds)
                    for cond in inner_conds:
                        if isinstance(cond, (sqlglot_exp.EQ, sqlglot_exp.GT, sqlglot_exp.GTE,
                                             sqlglot_exp.LT, sqlglot_exp.LTE,
                                             sqlglot_exp.Between)):
                            new_conditions.append(cond.sql())


def _eval_constant_arithmetic(ast):
    """Evaluate constant arithmetic expressions: 6 + 10 → 16, 1220 + 11 → 1231."""
    changed = True
    while changed:
        changed = False
        for node in list(ast.walk()):
            if not isinstance(node, (sqlglot_exp.Add, sqlglot_exp.Sub,
                                     sqlglot_exp.Mul, sqlglot_exp.Div)):
                continue
            left = node.this
            right = node.expression
            if not (isinstance(left, sqlglot_exp.Literal) and left.is_number and
                    isinstance(right, sqlglot_exp.Literal) and right.is_number):
                continue
            l_val = float(left.this)
            r_val = float(right.this)
            if isinstance(node, sqlglot_exp.Add):
                result = l_val + r_val
            elif isinstance(node, sqlglot_exp.Sub):
                result = l_val - r_val
            elif isinstance(node, sqlglot_exp.Mul):
                result = l_val * r_val
            elif isinstance(node, sqlglot_exp.Div):
                if r_val == 0:
                    continue
                result = l_val / r_val
            else:
                continue
            if result == int(result):
                node.replace(sqlglot_exp.Literal.number(int(result)))
            else:
                node.replace(sqlglot_exp.Literal.number(round(result, 6)))
            changed = True


def _add_tables_to_from(sql, new_tables):
    """Add tables to the FROM clause of a SQL query via string insertion."""
    from_match = re.search(r'\bFROM\b\s+', sql, re.IGNORECASE)
    if from_match:
        insert_pos = from_match.end()
        new_tables_str = ', '.join(new_tables) + ', '
        sql = sql[:insert_pos] + new_tables_str + sql[insert_pos:]
    return sql


def _add_conditions_to_where(sql, conditions):
    """Add extra AND conditions to the WHERE clause of a SQL query."""
    where_match = re.search(r'\bWHERE\b\s+', sql, re.IGNORECASE)
    if where_match:
        insert_pos = where_match.end()
        conditions_str = ' AND '.join(conditions) + ' AND '
        sql = sql[:insert_pos] + conditions_str + sql[insert_pos:]
    return sql


def _preprocess_predicates(sql, db_name=None, price_m=False, price_s=False):
    """
    Preprocess SQL predicates before PRICE transformation.

    Phase 1 — Subquery handling:
      - EXISTS/NOT EXISTS → inline inner tables and correlated join conditions
      - IN/NOT IN (subquery) → inline inner tables and join condition
      - Scalar subqueries (col op (SELECT AGG(...))) → estimate value from statistics

    Phase 2 — Predicate simplification:
      - BETWEEN → >= AND <=
      - IN (value list) → OR equalities  [skipped when price_m/price_s=True]
      - Drop LIKE / NOT LIKE             [skipped when price_m/price_s=True]
      - Drop non-EQ string comparisons

    Phase 3 — Arithmetic evaluation:
      - Constant expressions like 6 + 10 → 16

    Args:
        price_m: When True, preserve IN and LIKE predicates for PRICE_M encoding.
        price_s: When True, preserve IN and LIKE predicates for PRICE_S encoding.
    """
    if not HAS_SQLGLOT:
        return sql

    try:
        ast = sqlglot.parse_one(sql)
    except Exception:
        return sql

    new_from_tables = []  # tables to add to FROM clause
    new_conditions = []   # conditions to add to WHERE clause (from scalar subquery inlining)
    tautology = sqlglot_exp.EQ(
        this=sqlglot_exp.Literal.number(1),
        expression=sqlglot_exp.Literal.number(1)
    )

    # --- Phase 1: Subquery handling ---
    _inline_exists_subqueries(ast, new_from_tables, tautology)
    _inline_in_subqueries(ast, new_from_tables, tautology)
    if db_name:
        _estimate_scalar_subqueries(ast, db_name, tautology, new_from_tables, new_conditions)

    # --- Phase 2: Predicate simplification ---

    # BETWEEN → >= AND <=
    for node in list(ast.find_all(sqlglot_exp.Between)):
        col = node.this
        low = node.args.get('low')
        high = node.args.get('high')
        if col and low and high:
            gte = sqlglot_exp.GTE(this=col.copy(), expression=low.copy())
            lte = sqlglot_exp.LTE(this=col.copy(), expression=high.copy())
            and_expr = sqlglot_exp.And(this=gte, expression=lte)
            node.replace(sqlglot_exp.Paren(this=and_expr))

    # IN (value list) → OR equalities (subquery INs already handled in Phase 1)
    # PRICE_M/PRICE_S: preserve IN as-is for SpaceSaving encoding
    if not (price_m or price_s):
        for node in list(ast.find_all(sqlglot_exp.In)):
            col = node.this
            values = node.expressions
            if col and values:
                or_expr = None
                for val in values:
                    eq = sqlglot_exp.EQ(this=col.copy(), expression=val.copy())
                    if or_expr is None:
                        or_expr = eq
                    else:
                        or_expr = sqlglot_exp.Or(this=or_expr, expression=eq)
                if or_expr is not None:
                    node.replace(sqlglot_exp.Paren(this=or_expr))

    # Drop LIKE / NOT LIKE → 1 = 1
    # PRICE_M/PRICE_S: preserve LIKE, ILIKE, NOT LIKE, NOT ILIKE for SpaceSaving encoding
    if not (price_m or price_s):
        for node in list(ast.find_all(sqlglot_exp.Like)):
            node.replace(tautology.copy())
        for node in list(ast.find_all(sqlglot_exp.ILike)):
            node.replace(tautology.copy())
    if not (price_m or price_s):
        for node in list(ast.find_all(sqlglot_exp.Not)):
            child = node.this
            if isinstance(child, (sqlglot_exp.Like, sqlglot_exp.ILike)):
                node.replace(tautology.copy())

    # Drop non-EQ comparisons on string literals
    for cmp_type in (sqlglot_exp.GT, sqlglot_exp.GTE, sqlglot_exp.LT,
                     sqlglot_exp.LTE, sqlglot_exp.NEQ):
        for node in list(ast.find_all(cmp_type)):
            rhs = node.args.get("expression")
            if rhs and isinstance(rhs, sqlglot_exp.Literal) and rhs.is_string:
                node.replace(tautology.copy())
    for node in list(ast.find_all(sqlglot_exp.Not)):
        child = node.this
        if isinstance(child, sqlglot_exp.EQ):
            rhs = child.args.get("expression")
            if rhs and isinstance(rhs, sqlglot_exp.Literal) and rhs.is_string:
                node.replace(tautology.copy())

    # --- Phase 3: Arithmetic evaluation ---
    _eval_constant_arithmetic(ast)

    # Generate result
    result = ast.sql()

    # Add inlined tables to FROM clause
    if new_from_tables:
        result = _add_tables_to_from(result, new_from_tables)

    # Add inlined conditions to WHERE clause (from scalar subquery inlining)
    if new_conditions:
        result = _add_conditions_to_where(result, new_conditions)

    return result


def _add_missing_from_tables(sql, db_name):
    """
    If WHERE references aliases not in FROM that map to known PRICE tables,
    add those tables to the FROM clause.

    Example: FROM item tpcds_i, store tpcds_s WHERE tpcds_ss.ss_store_sk = ...
    → adds "store_sales tpcds_ss" to FROM.
    """
    from_match = re.search(
        r'\bSELECT\s+COUNT\(\*\)\s+FROM\s+(.*?)\s+WHERE\s+(.*)',
        sql, re.IGNORECASE | re.DOTALL
    )
    if not from_match:
        return sql

    from_str = from_match.group(1)
    where_str = from_match.group(2)

    # Parse existing FROM aliases
    from_aliases = set()
    for part in from_str.split(','):
        tokens = part.strip().split()
        if len(tokens) >= 2:
            from_aliases.add(tokens[-1].lower())
        elif tokens:
            from_aliases.add(tokens[0].lower())

    # Find all aliases referenced in WHERE
    where_aliases = set()
    for m in re.finditer(r'(\w+)\.\w+', where_str):
        where_aliases.add(m.group(1).lower())

    missing = where_aliases - from_aliases
    if not missing:
        return sql

    # Build reverse mapping: PRICE alias → table name
    abbrev = _load_abbrev_mapping(db_name)
    alias_to_table = {v: k for k, v in abbrev.items()}

    additions = []
    for alias in sorted(missing):
        if alias in alias_to_table:
            table_name = alias_to_table[alias]
            additions.append(f"{table_name} {alias}")

    if not additions:
        return sql

    new_from = from_str + ", " + ", ".join(additions)
    return f"SELECT COUNT(*) FROM {new_from} WHERE {where_str}"


def _convert_between_to_range(sql):
    """Convert BETWEEN conditions to >= AND <= range comparisons.

    Clean numeric BETWEENs (col BETWEEN N1 AND N2) become col >= N1 AND col <= N2.
    Mixed BETWEENs (col BETWEEN 'str' AND N) become col <= N (keep numeric bound).
    BETWEENs with arithmetic (col BETWEEN N AND N + M) are stripped (can't convert).
    String-only BETWEENs are stripped (PRICE can't use string comparisons).

    Must run BEFORE _split_where_on_and is called, since BETWEEN's internal AND
    confuses the AND-splitter.
    """
    # Helper: evaluate simple constant arithmetic like "22 + 30" → 52
    def _eval_arith(expr):
        """Safely evaluate numeric arithmetic (only +, -, *, / with numeric literals)."""
        expr = expr.strip()
        if not re.match(r'^[\d\.\s+\-*/]+$', expr):
            return None  # Not pure numeric arithmetic
        try:
            val = float(eval(expr))  # Safe: validated to only contain digits and operators
            return str(int(val)) if val == int(val) else str(val)
        except Exception:
            return None

    # 1. Numeric BETWEEN (possibly with arithmetic in bounds):
    #    col between 22 and 22 + 30 → col >= 22 AND col <= 52
    #    col between 100 and 500 → col >= 100 AND col <= 500
    def _numeric_between_replacer(m):
        col = m.group(1)
        lo_expr = m.group(2)
        hi_expr = m.group(3)
        lo = _eval_arith(lo_expr)
        hi = _eval_arith(hi_expr)
        if lo is None or hi is None:
            return ''  # Can't evaluate — strip
        return f"{col} >= {lo} AND {col} <= {hi}"

    sql = re.sub(
        r"\b(\w+(?:\.\w+)?)\s+between\s+(\d+(?:\.\d+)?(?:\s*[+\-*/]\s*\d+(?:\.\d+)?)*)\s+and\s+"
        r"(\d+(?:\.\d+)?(?:\s*[+\-*/]\s*\d+(?:\.\d+)?)*)",
        _numeric_between_replacer,
        sql, flags=re.IGNORECASE
    )
    # 2. String-first BETWEEN with numeric upper bound (possibly arithmetic):
    #    col between 'str' and 123 + 30 → col <= 153
    def _string_first_between_replacer(m):
        col = m.group(1)
        hi_expr = m.group(2)
        hi = _eval_arith(hi_expr)
        if hi is None:
            return ''  # Can't evaluate — strip
        return f"{col} <= {hi} "

    sql = re.sub(
        r"\b(\w+(?:\.\w+)?)\s+between\s+'[^']*'\s+and\s+"
        r"(\d+(?:\.\d+)?(?:\s*[+\-*/]\s*\d+(?:\.\d+)?)*)\s*\)?\s*",
        _string_first_between_replacer,
        sql, flags=re.IGNORECASE
    )
    # 3. String-only BETWEEN: col between 'str1' and 'str2' → strip
    sql = re.sub(
        r"\b\w+(?:\.\w+)?\s+between\s+'[^']*'\s+and\s+'[^']*'\s*\)?\s*",
        '', sql, flags=re.IGNORECASE
    )
    # 4. Any remaining BETWEEN (edge cases) — strip as safety net
    sql = re.sub(
        r"\b\w+(?:\.\w+)?\s+between\s+'[^']*'\s+and\s+\S+\s*\)?\s*",
        '', sql, flags=re.IGNORECASE
    )
    # Clean up AND artifacts from stripping
    sql = re.sub(r'\bWHERE\s+AND\s+', 'WHERE ', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\s+AND\s+AND\s+', ' AND ', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\s+AND\s*$', '', sql, flags=re.IGNORECASE)
    return sql


def _strip_same_table_conditions(sql):
    """
    Remove WHERE conditions where both sides reference the same table alias.

    After self-join collapse (e.g., tpcds_dd2 → tpcds_dd), join conditions like
    tpcds_dd.d_week_seq = tpcds_dd.d_week_seq become tautological same-table
    conditions. PRICE's parse_sql counts these as joins, violating the tree
    constraint. Strip them here.

    Also strips dangling references: conditions referencing aliases not in FROM.
    """
    from_match = re.search(
        r'\bSELECT\s+COUNT\(\*\)\s+FROM\s+(.*?)\s+WHERE\s+(.*)',
        sql, re.IGNORECASE | re.DOTALL
    )
    if not from_match:
        return sql

    from_str = from_match.group(1)
    where_str = from_match.group(2)

    # Note: BETWEEN patterns are already converted to >= / <= by _convert_between_to_range
    # which runs before this function in the pipeline.

    # Parse FROM aliases
    from_aliases = set()
    for part in from_str.split(','):
        tokens = part.strip().split()
        if tokens:
            from_aliases.add(tokens[-1].lower())

    raw_conditions = _split_where_on_and(where_str)

    # Unwrap parenthesized compound conditions: "(A and B)" → "A", "B"
    conditions = []
    for cond in raw_conditions:
        stripped = cond.strip()
        # Check if entire condition is wrapped in outer parens with AND inside
        if stripped.startswith('(') and stripped.endswith(')'):
            inner = stripped[1:-1].strip()
            # Only unwrap if inner has balanced parens and contains AND
            depth = 0
            balanced = True
            for ch in inner:
                if ch == '(':
                    depth += 1
                elif ch == ')':
                    depth -= 1
                    if depth < 0:
                        balanced = False
                        break
            if balanced and depth == 0 and ' and ' in inner.lower():
                sub_parts = _split_where_on_and(inner)
                conditions.extend(sub_parts)
                continue
        conditions.append(cond)

    new_conditions = []
    for cond in conditions:
        cond_stripped = cond.strip()

        # Strip tautologies: "1 = 1", "1 = 1 = 1", etc.
        if re.match(r'^1\s*=\s*1(\s*=\s*1)*$', cond_stripped):
            continue

        # Check for same-table conditions: alias.col = alias.col
        m = re.match(r'\s*(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)\s*$', cond_stripped)
        if m:
            lt, rt = m.group(1).lower(), m.group(3).lower()
            if lt == rt:
                continue  # Skip tautological same-table condition

        # Check for equi-join with bare (unqualified) column on one side
        # e.g., "sold_item_sk = tpcds_i.i_item_sk" — bare column from UNION alias
        # But NOT filter conditions like "tpcds_i.i_manager_id = 1"
        eq_match = re.match(r'\s*(\S+)\s*=\s*(\S+)\s*$', cond_stripped)
        if eq_match:
            lhs, rhs = eq_match.group(1), eq_match.group(2)
            if ('.' in lhs) != ('.' in rhs):
                # Check that the unqualified side looks like a column name, not a literal
                bare_side = lhs if '.' not in lhs else rhs
                if re.match(r'^[a-z_]\w*$', bare_side, re.IGNORECASE):
                    continue  # Bare column join — strip

        # Check for bare column in non-join condition (e.g., "ranking <= 5")
        # If no table qualifier at all in condition, strip it
        if not re.search(r'\w+\.\w+', cond_stripped):
            # No qualified column reference — this is a bare expression
            # Only strip if it looks like a comparison (has an operator)
            if re.search(r'[<>=!]', cond_stripped):
                continue

        # Check for dangling references (aliases in condition not in FROM)
        cond_aliases = set()
        for alias_match in re.finditer(r'(\w+)\.\w+', cond):
            cond_aliases.add(alias_match.group(1).lower())
        if cond_aliases and not cond_aliases.issubset(from_aliases):
            continue  # Skip condition with dangling references

        new_conditions.append(cond)

    if not new_conditions:
        return sql  # Don't remove everything

    return f"SELECT COUNT(*) FROM {from_str} WHERE {' AND '.join(new_conditions)}"


def _hoist_joins_from_or_blocks(sql):
    """
    Handle WHERE clauses that are entirely OR blocks (no top-level AND joins).

    TPC-H Q19 has: WHERE (join AND filters) OR (join AND filters) OR ...
    PRICE needs the join at top level. This function:
    1. Detects when WHERE is a single OR expression (no top-level ANDs)
    2. Scans inside each OR branch for equi-join conditions (alias.col = alias.col)
    3. Hoists the join to top level and keeps the simplest filter conditions
    """
    from_match = re.search(
        r'\bSELECT\s+COUNT\(\*\)\s+FROM\s+(.*?)\s+WHERE\s+(.*)',
        sql, re.IGNORECASE | re.DOTALL
    )
    if not from_match:
        return sql

    from_str = from_match.group(1)
    where_str = from_match.group(2)

    # Check if there are top-level ANDs — if so, this function doesn't apply
    top_level_conditions = _split_where_on_and(where_str)
    if len(top_level_conditions) > 1:
        return sql  # Already has top-level ANDs

    # Check for top-level OR pattern
    if ' or ' not in where_str.lower():
        return sql

    # Parse FROM aliases to identify join patterns
    from_aliases = set()
    for part in from_str.split(','):
        tokens = part.strip().split()
        if len(tokens) >= 2:
            from_aliases.add(tokens[-1].lower())

    # Scan entire WHERE for equi-join conditions (alias.col = alias.col)
    found_joins = []
    for m in re.finditer(r'(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)', where_str):
        lt, lc = m.group(1).lower(), m.group(2).lower()
        rt, rc = m.group(3).lower(), m.group(4).lower()
        if lt in from_aliases and rt in from_aliases and lt != rt:
            join_str = f"{lt}.{lc} = {rt}.{rc}"
            if join_str not in found_joins:
                found_joins.append(join_str)

    if not found_joins:
        return sql  # No joins found inside OR blocks

    # Scan for simple filter conditions (alias.col op literal)
    # Collect all, then deduplicate by keeping the envelope (widest range)
    # since OR semantics mean any row matching ANY branch is included.
    raw_filters = []
    for m in re.finditer(r'(\w+\.\w+)\s*(>=|<=|>|<|=)\s*(\d+(?:\.\d+)?)\b', where_str):
        col, op, val = m.group(1).lower(), m.group(2), float(m.group(3))
        raw_filters.append((col, op, val))

    # Deduplicate: OR envelope = widest range covering all branches
    #   For <=/<: keep LARGEST value (widest upper bound)
    #   For >=/> : keep SMALLEST value (widest lower bound)
    best = {}  # (col, op) → envelope value
    for col, op, val in raw_filters:
        key = (col, op)
        if key not in best:
            best[key] = val
        elif op in ('<=', '<'):
            best[key] = max(best[key], val)  # Widest upper bound
        elif op in ('>=', '>'):
            best[key] = min(best[key], val)  # Widest lower bound
        # For '=', keep first occurrence

    found_filters = []
    for (col, op), val in sorted(best.items()):
        val_str = str(int(val)) if val == int(val) else str(val)
        found_filters.append(f"{col} {op} {val_str}")

    # Build new WHERE: joins AND deduplicated filters
    new_parts = list(found_joins)

    # Add deduplicated filters (limited to avoid selectivity issues)
    for filt in found_filters:
        new_parts.append(filt)
        if len(new_parts) >= len(found_joins) + 4:
            break  # Limit filter count to avoid selectivity issues

    return f"SELECT COUNT(*) FROM {from_str} WHERE {' AND '.join(new_parts)}"


def _clean_sql_artifacts(sql):
    """
    Clean up SQL artifacts left by incomplete CTE/subquery flattening.

    Handles:
    - Trailing GROUP BY, ORDER BY, LIMIT, HAVING after WHERE clause
    - Excess closing parentheses from partial subquery removal
    - CASE/WHEN/END fragments (e.g., ") else (select ..." or "end as ...")
    - substring() function calls → strip entire condition
    """
    # Only process SELECT COUNT(*) FROM ... WHERE ... queries
    from_match = re.search(
        r'\bSELECT\s+COUNT\(\*\)\s+FROM\s+(.*?)\s+WHERE\s+(.*)',
        sql, re.IGNORECASE | re.DOTALL
    )
    if not from_match:
        return sql

    from_str = from_match.group(1)
    where_str = from_match.group(2)

    # Strip trailing GROUP BY / ORDER BY / LIMIT / HAVING at any paren depth
    # Find the earliest top-level or near-top-level occurrence
    lower = where_str.lower()
    depth = 0
    cut_pos = len(where_str)
    for i, ch in enumerate(where_str):
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
            # Excess closing paren (depth < 0) → cut here
            if depth < 0:
                # Check if everything before this is meaningful
                before = where_str[:i].strip()
                if before:
                    cut_pos = i
                    break
                depth = 0  # Reset and continue
        elif depth <= 0:
            for kw in ['group by', 'order by', 'limit ', 'having ']:
                if lower[i:i+len(kw)] == kw:
                    if i > 0 and not lower[i-1].isalnum():
                        cut_pos = i
                        break
            if cut_pos != len(where_str):
                break

    where_str = where_str[:cut_pos].strip()

    # Remove trailing excess closing parens
    while where_str.endswith(')'):
        depth = 0
        for ch in where_str:
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
        if depth < 0:
            where_str = where_str[:-1].strip()
        else:
            break

    # Strip CASE/WHEN/END fragments: ") else ..." or "end as ..."
    # These come from partially extracted CASE expressions
    for pattern in [r'\)\s*else\s*\(.*', r'\bend\s+as\s+\w+.*']:
        where_str = re.sub(pattern, '', where_str, flags=re.IGNORECASE | re.DOTALL).strip()

    # Note: BETWEEN patterns are already converted to >= / <= by _convert_between_to_range
    # which runs before this function in the pipeline.

    # Strip conditions PRICE can't handle
    conditions = _split_where_on_and(where_str)
    cleaned_conditions = []
    for cond in conditions:
        cond_lower = cond.lower().strip()
        if 'substring(' in cond_lower:
            continue  # Drop substring conditions
        if ' between ' in cond_lower:
            continue  # Drop BETWEEN (mixed type dates, etc.)
        if 'exists' in cond_lower:
            continue  # Drop EXISTS subqueries
        cleaned_conditions.append(cond)

    if cleaned_conditions:
        where_str = ' AND '.join(cleaned_conditions)
    else:
        where_str = where_str  # Keep original if all stripped

    # Clean up trailing AND
    where_str = re.sub(r'\s+AND\s*$', '', where_str, flags=re.IGNORECASE).strip()

    if not where_str:
        return sql  # Don't produce empty WHERE

    return f"SELECT COUNT(*) FROM {from_str} WHERE {where_str}"


def _prune_redundant_joins(sql):
    """
    Remove redundant join conditions to satisfy PRICE's tree constraint:
    len(tables) == len(joins) + 1.

    Job_full queries often have cyclic joins (e.g., t.id = ci.movie_id AND
    t.id = mc.movie_id AND ci.movie_id = mc.movie_id). We keep a spanning
    tree of joins using union-find to detect cycles.

    Uses sqlglot AST manipulation to remove redundant EQ nodes from WHERE.
    """
    if not HAS_SQLGLOT:
        return sql

    try:
        ast = sqlglot.parse_one(sql)
    except Exception:
        return sql

    where = ast.args.get("where")
    if where is None:
        return sql

    # Collect all EQ nodes that are joins (both sides are Column references)
    join_eqs = []
    filter_eqs = []
    for eq in where.find_all(sqlglot_exp.EQ):
        left = eq.args.get("this")
        right = eq.args.get("expression")
        if isinstance(left, sqlglot_exp.Column) and isinstance(right, sqlglot_exp.Column):
            # Extract table alias from column reference
            left_table = left.table if left.table else ""
            right_table = right.table if right.table else ""
            if left_table and right_table and left_table != right_table:
                join_eqs.append((eq, left_table, right_table))

    if not join_eqs:
        return sql

    # Count tables from FROM clause
    tables = set()
    for table in ast.find_all(sqlglot_exp.Table):
        tables.add(table.alias_or_name)

    n_tables = len(tables)
    n_needed = n_tables - 1

    if len(join_eqs) <= n_needed:
        return sql  # Already satisfies or under constraint

    # Union-Find to build spanning tree
    parent = {}

    def find(x):
        while parent.get(x, x) != x:
            parent[x] = parent.get(parent[x], parent[x])
            x = parent[x]
        return x

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx == ry:
            return False  # Cycle detected
        parent[rx] = ry
        return True

    # Keep joins that don't create cycles
    keep = []
    remove = []
    for eq, lt, rt in join_eqs:
        if union(lt, rt):
            keep.append(eq)
        else:
            remove.append(eq)

    if not remove:
        return sql

    # Remove redundant join EQ nodes from the WHERE clause
    # Replace them with TRUE (1 = 1) to avoid breaking AND chains
    tautology = sqlglot_exp.EQ(
        this=sqlglot_exp.Literal.number(1),
        expression=sqlglot_exp.Literal.number(1)
    )
    for eq in remove:
        eq.replace(tautology.copy())

    return ast.sql()


def _strip_tautologies(sql):
    """Remove 1 = 1 tautologies from WHERE clause.

    _prune_redundant_joins replaces cyclic joins with 1 = 1 tautologies.
    This function cleans them up afterward.
    """
    from_match = re.search(
        r'\bSELECT\s+COUNT\(\*\)\s+FROM\s+(.*?)\s+WHERE\s+(.*)',
        sql, re.IGNORECASE | re.DOTALL
    )
    if not from_match:
        return sql

    from_str = from_match.group(1)
    where_str = from_match.group(2)
    conditions = _split_where_on_and(where_str)
    filtered = [c for c in conditions
                if not re.match(r'^\s*1\s*=\s*1(\s*=\s*1)*\s*$', c.strip())]

    if not filtered:
        return sql  # Don't remove everything

    return f"SELECT COUNT(*) FROM {from_str} WHERE {' AND '.join(filtered)}"


def _split_where_on_and(where_str):
    """Split WHERE clause string on top-level AND, respecting parentheses."""
    parts = []
    depth = 0
    current = []
    i = 0
    where_lower = where_str.lower()
    while i < len(where_str):
        if where_str[i] == '(':
            depth += 1
            current.append(where_str[i])
        elif where_str[i] == ')':
            depth -= 1
            current.append(where_str[i])
        elif depth == 0 and where_lower[i:i+5] == ' and ' and i > 0:
            parts.append(''.join(current).strip())
            current = []
            i += 5
            continue
        else:
            current.append(where_str[i])
        i += 1
    if current:
        parts.append(''.join(current).strip())
    return [p for p in parts if p]


def _collapse_self_joins(sql):
    """
    Collapse numbered self-join aliases (e.g., tpcds_dd2 → tpcds_dd) when the
    numbered alias only joins to its base alias via tautological self-joins.

    After collapsing, the tautological join (tpcds_dd.col = tpcds_dd.col) will
    be cleaned up by _prune_redundant_joins.
    """
    from_match = re.search(
        r'\bSELECT\s+COUNT\(\*\)\s+FROM\s+(.*?)\s+WHERE\s+(.*)',
        sql, re.IGNORECASE | re.DOTALL
    )
    if not from_match:
        return sql

    from_str = from_match.group(1)
    where_str = from_match.group(2)

    # Parse tables: "table alias, table alias, ..."
    table_entries = []
    for part in from_str.split(','):
        part = part.strip()
        if not part:
            continue
        tokens = part.split()
        alias = tokens[-1].lower() if len(tokens) >= 2 else tokens[0].lower()
        table_entries.append((alias, part))

    alias_set = {e[0] for e in table_entries}
    if len(alias_set) <= 1:
        return sql

    # Identify numbered aliases: match pattern base_alias + digit(s)
    numbered_aliases = {}  # numbered_alias → base_alias
    for alias in sorted(alias_set):
        m = re.match(r'^(.+?)(\d+)$', alias)
        if m and m.group(1) in alias_set:
            numbered_aliases[alias] = m.group(1)

    if not numbered_aliases:
        return sql

    # Check which numbered aliases can be collapsed:
    # Collapse if ALL join partners are the base alias (or no joins at all)
    can_collapse = {}
    for numbered, base in numbered_aliases.items():
        join_partners = set()
        for m_join in re.finditer(r'(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)', where_str, re.IGNORECASE):
            lt, rt = m_join.group(1).lower(), m_join.group(3).lower()
            if lt == numbered:
                join_partners.add(rt)
            elif rt == numbered:
                join_partners.add(lt)
        if join_partners <= {base}:
            can_collapse[numbered] = base

    if not can_collapse:
        return sql

    # Perform collapse: replace numbered alias → base in WHERE, remove from FROM
    new_from_parts = [entry for alias, entry in table_entries if alias not in can_collapse]
    new_where = where_str
    for numbered, base in sorted(can_collapse.items(), key=lambda x: -len(x[0])):
        new_where = re.sub(r'\b' + re.escape(numbered) + r'\.', base + '.', new_where)

    return f"SELECT COUNT(*) FROM {', '.join(new_from_parts)} WHERE {new_where}"


def _prune_disconnected_tables(sql):
    """
    Remove tables from FROM that have no join conditions linking them to
    any other table. Keeps the largest connected component.
    """
    from_match = re.search(
        r'\bSELECT\s+COUNT\(\*\)\s+FROM\s+(.*?)\s+WHERE\s+(.*)',
        sql, re.IGNORECASE | re.DOTALL
    )
    if not from_match:
        return sql

    from_str = from_match.group(1)
    where_str = from_match.group(2)

    # Parse tables
    table_entries = []
    for part in from_str.split(','):
        part = part.strip()
        if not part:
            continue
        tokens = part.split()
        alias = tokens[-1].lower() if len(tokens) >= 2 else tokens[0].lower()
        table_entries.append((alias, part))

    aliases = {e[0] for e in table_entries}
    if len(aliases) <= 1:
        return sql

    # Build adjacency from join conditions
    adj = {a: set() for a in aliases}
    for m_join in re.finditer(r'(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)', where_str, re.IGNORECASE):
        lt = m_join.group(1).lower()
        rt = m_join.group(3).lower()
        if lt in aliases and rt in aliases and lt != rt:
            adj[lt].add(rt)
            adj[rt].add(lt)

    # Find largest connected component via BFS
    visited = set()
    components = []
    for start in sorted(aliases):
        if start in visited:
            continue
        component = set()
        queue = [start]
        while queue:
            node = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)
            component.add(node)
            for neighbor in adj.get(node, set()):
                if neighbor not in visited:
                    queue.append(neighbor)
        components.append(component)

    if not components:
        return sql

    # If multiple components have same size, prefer the one with more filter conditions
    def _component_score(comp):
        # Primary: size. Secondary: number of filter conditions referencing this component
        filter_count = 0
        for cond in _split_where_on_and(where_str):
            for alias in comp:
                if re.search(r'\b' + re.escape(alias) + r'\.', cond, re.IGNORECASE):
                    filter_count += 1
                    break
        return (len(comp), filter_count)

    largest = max(components, key=_component_score)

    if len(largest) == len(aliases):
        return sql  # All connected

    removed = aliases - largest

    # Filter FROM entries
    new_from_parts = [entry for alias, entry in table_entries if alias in largest]

    # Filter WHERE conditions: remove any referencing removed aliases
    conditions = _split_where_on_and(where_str)
    new_conditions = []
    for cond in conditions:
        cond_lower = cond.lower()
        references_removed = False
        for removed_alias in removed:
            if re.search(r'\b' + re.escape(removed_alias) + r'\.', cond_lower):
                references_removed = True
                break
        if not references_removed:
            new_conditions.append(cond)

    if not new_conditions:
        return sql  # Don't remove everything

    return f"SELECT COUNT(*) FROM {', '.join(new_from_parts)} WHERE {' AND '.join(new_conditions)}"


def _ast_collect_predicates(sql, db_name):
    """
    Last-resort predicate collection: walk entire SQL AST to extract all tables,
    equi-joins, and filters from every level (CTEs, UNION branches, subqueries).

    Used when CTE flattening fails. Builds the largest connected component and
    constructs a synthetic flat SQL for PRICE.

    Returns flat SQL string, or None if extraction fails.
    """
    if not HAS_SQLGLOT:
        return None

    try:
        ast = sqlglot.parse_one(sql)
    except Exception:
        return None

    # Identify CTE names (to exclude from table list)
    cte_names = set()
    with_clause = ast.args.get('with_')
    if with_clause:
        for cte in with_clause.find_all(sqlglot_exp.CTE):
            cte_names.add(cte.alias.lower())

    # Collect ALL real tables from every level
    tables = set()
    for tbl in ast.find_all(sqlglot_exp.Table):
        name = tbl.name.lower()
        if name and name not in cte_names:
            tables.add(name)

    if not tables:
        return None

    # Collect ALL equi-join conditions (Column = Column) from every level
    joins = []
    for eq in ast.find_all(sqlglot_exp.EQ):
        left = eq.args.get("this")
        right = eq.args.get("expression")
        if isinstance(left, sqlglot_exp.Column) and isinstance(right, sqlglot_exp.Column):
            left_col = left.name.lower()
            right_col = right.name.lower()
            if left_col != right_col:  # Skip tautological self-joins
                joins.append((left_col, right_col))

    # Collect simple filter conditions from every level
    filters = []
    for cmp_type, op_str in [(sqlglot_exp.GT, '>'), (sqlglot_exp.GTE, '>='),
                              (sqlglot_exp.LT, '<'), (sqlglot_exp.LTE, '<='),
                              (sqlglot_exp.EQ, '=')]:
        for node in ast.find_all(cmp_type):
            left = node.args.get("this")
            right = node.args.get("expression")
            if isinstance(left, sqlglot_exp.Column) and not isinstance(right, sqlglot_exp.Column):
                if isinstance(right, (sqlglot_exp.Literal, sqlglot_exp.Neg)):
                    filters.append((left.name.lower(), op_str, right.sql()))
            elif isinstance(right, sqlglot_exp.Column) and not isinstance(left, sqlglot_exp.Column):
                if isinstance(left, (sqlglot_exp.Literal, sqlglot_exp.Neg)):
                    flip = {'=': '=', '>': '<', '>=': '<=', '<': '>', '<=': '>='}
                    filters.append((right.name.lower(), flip[op_str], left.sql()))

    # Collect BETWEEN conditions
    for node in ast.find_all(sqlglot_exp.Between):
        col = node.this
        if isinstance(col, sqlglot_exp.Column):
            low = node.args.get('low')
            high = node.args.get('high')
            if low and high:
                filters.append((col.name.lower(), '>=', low.sql()))
                filters.append((col.name.lower(), '<=', high.sql()))

    # Deduplicate joins
    seen = set()
    unique_joins = []
    for left, right in joins:
        key = tuple(sorted([left, right]))
        if key not in seen:
            seen.add(key)
            unique_joins.append((left, right))

    # Build adjacency graph for tables using column prefix mapping
    col_prefixes = _TPCH_COL_PREFIX if db_name == 'tpch' else _TPCDS_COL_PREFIX if db_name == 'tpcds' else []

    def _col_to_table(col_name):
        for prefix, tbl in col_prefixes:
            if col_name.startswith(prefix):
                return tbl
        return None

    # Collect IN (value list) conditions
    for node in ast.find_all(sqlglot_exp.In):
        col = node.this
        values = node.expressions
        if isinstance(col, sqlglot_exp.Column) and values:
            col_name = col.name.lower()
            ct = _col_to_table(col_name)
            if not ct:
                continue
            # Numeric values → range
            nums = []
            for v in values:
                if isinstance(v, sqlglot_exp.Literal) and not v.is_string:
                    try:
                        nums.append(float(v.this))
                    except (ValueError, TypeError):
                        break
                elif isinstance(v, sqlglot_exp.Neg) and isinstance(v.this, sqlglot_exp.Literal):
                    try:
                        nums.append(-float(v.this.this))
                    except (ValueError, TypeError):
                        break
                else:
                    break
            if len(nums) == len(values) and nums:
                filters.append((col_name, '>=', str(min(nums))))
                filters.append((col_name, '<=', str(max(nums))))
                continue
            # String values → representative equality
            if values and isinstance(values[0], sqlglot_exp.Literal) and values[0].is_string:
                filters.append((col_name, '=', values[0].sql()))

    # Find connected component: map joins to table pairs
    table_adj = {t: set() for t in tables}
    valid_joins = []
    for left, right in unique_joins:
        lt = _col_to_table(left)
        rt = _col_to_table(right)
        if lt and rt and lt != rt and lt in tables and rt in tables:
            table_adj[lt].add(rt)
            table_adj[rt].add(lt)
            valid_joins.append((left, right))

    # Find largest connected component via BFS
    visited = set()
    components = []
    for start in sorted(tables):
        if start in visited:
            continue
        component = set()
        queue = [start]
        while queue:
            node = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)
            component.add(node)
            for neighbor in table_adj.get(node, set()):
                if neighbor not in visited:
                    queue.append(neighbor)
        components.append(component)

    if not components:
        return None
    largest = max(components, key=len)

    # Build flat SQL with tables in largest component
    from_parts = sorted(largest)
    where_parts = []

    for left, right in valid_joins:
        lt = _col_to_table(left)
        rt = _col_to_table(right)
        if lt in largest and rt in largest:
            where_parts.append(f"{left} = {right}")

    for col, op, val in filters:
        ct = _col_to_table(col)
        if ct and ct in largest:
            where_parts.append(f"{col} {op} {val}")

    if not where_parts:
        return None

    return f"SELECT COUNT(*) FROM {', '.join(from_parts)} WHERE {' AND '.join(where_parts)}"


def _regex_collect_predicates(sql, db_name):
    """
    Regex-based fallback predicate collector for when sqlglot can't parse the SQL.

    Scans the raw SQL text for:
    - Known table names (from abbrev mapping)
    - Equi-join conditions (col = col where columns belong to different tables)
    - Simple filter conditions (col op literal)

    Returns flat SQL string, or None if insufficient predicates found.
    """
    col_prefixes = _TPCH_COL_PREFIX if db_name == 'tpch' else _TPCDS_COL_PREFIX if db_name == 'tpcds' else []
    abbrev = _load_abbrev_mapping(db_name)

    def _col_to_table(col_name):
        for prefix, tbl in col_prefixes:
            if col_name.startswith(prefix):
                return tbl
        return None

    sql_lower = sql.lower()

    # Find all table names from the abbreviation mapping that appear in the SQL
    tables = set()
    for table_name in abbrev:
        if re.search(r'\b' + re.escape(table_name) + r'\b', sql_lower):
            tables.add(table_name)

    if not tables:
        return None

    # Find all equi-join conditions: col1 = col2 (both are column-like identifiers)
    joins = []
    seen_joins = set()
    for m in re.finditer(r'(\w+)\s*=\s*(\w+)', sql_lower):
        left, right = m.group(1), m.group(2)
        lt = _col_to_table(left)
        rt = _col_to_table(right)
        if lt and rt and lt != rt and lt in tables and rt in tables:
            key = tuple(sorted([left, right]))
            if key not in seen_joins:
                seen_joins.add(key)
                joins.append((left, right))

    # Also check alias.col = alias.col patterns
    for m in re.finditer(r'(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)', sql_lower):
        left_col, right_col = m.group(2), m.group(4)
        lt = _col_to_table(left_col)
        rt = _col_to_table(right_col)
        if lt and rt and lt != rt and lt in tables and rt in tables:
            key = tuple(sorted([left_col, right_col]))
            if key not in seen_joins:
                seen_joins.add(key)
                joins.append((left_col, right_col))

    # Find simple filter conditions: col op literal
    filters = []
    for m in re.finditer(r'(\w+)\s*(>=|<=|>|<|=)\s*(\d+(?:\.\d+)?)\b', sql_lower):
        col, op, val = m.group(1), m.group(2), m.group(3)
        ct = _col_to_table(col)
        if ct and ct in tables:
            filters.append((col, op, val))

    # Also find alias.col op literal
    for m in re.finditer(r'(\w+)\.(\w+)\s*(>=|<=|>|<|=)\s*(\d+(?:\.\d+)?)\b', sql_lower):
        col, op, val = m.group(2), m.group(3), m.group(4)
        ct = _col_to_table(col)
        if ct and ct in tables:
            filters.append((col, op, val))

    # String literal filters: col = 'value'
    for m in re.finditer(r"(\w+)\.(\w+)\s*(>=|<=|>|<|=)\s*'([^']*)'", sql_lower):
        col, op, val = m.group(2), m.group(3), f"'{m.group(4)}'"
        ct = _col_to_table(col)
        if ct and ct in tables:
            filters.append((col, op, val))

    # IN-list filters: alias.col IN (val1, val2, ...)
    for m in re.finditer(r'(\w+)\.(\w+)\s+in\s*\(([^)]+)\)', sql_lower):
        col = m.group(2)
        ct = _col_to_table(col)
        if ct and ct in tables:
            vals_str = m.group(3)
            # Try numeric (no quotes present)
            nums = []
            for v in re.findall(r'-?\d+(?:\.\d+)?', vals_str):
                try:
                    nums.append(float(v))
                except ValueError:
                    pass
            if nums and len(re.findall(r"'", vals_str)) == 0:
                filters.append((col, '>=', str(min(nums))))
                filters.append((col, '<=', str(max(nums))))
            else:
                # String IN-list: pick first quoted value
                str_match = re.search(r"'([^']*)'", vals_str)
                if str_match:
                    filters.append((col, '=', f"'{str_match.group(1)}'"))

    # Also bare column IN-lists (no table prefix)
    seen_in_filters = set()
    for m in re.finditer(r'\b(\w+)\s+in\s*\(([^)]+)\)', sql_lower):
        col = m.group(1)
        ct = _col_to_table(col)
        if ct and ct in tables:
            vals_str = m.group(2)
            nums = []
            for v in re.findall(r'-?\d+(?:\.\d+)?', vals_str):
                try:
                    nums.append(float(v))
                except ValueError:
                    pass
            if nums and len(re.findall(r"'", vals_str)) == 0:
                key = (col, '>=', str(min(nums)))
                if key not in seen_in_filters:
                    seen_in_filters.add(key)
                    filters.append(key)
                key2 = (col, '<=', str(max(nums)))
                if key2 not in seen_in_filters:
                    seen_in_filters.add(key2)
                    filters.append(key2)
            else:
                str_match = re.search(r"'([^']*)'", vals_str)
                if str_match:
                    key = (col, '=', f"'{str_match.group(1)}'")
                    if key not in seen_in_filters:
                        seen_in_filters.add(key)
                        filters.append(key)

    if not joins:
        return None

    # Build adjacency graph for connected component
    table_adj = {t: set() for t in tables}
    valid_joins = []
    for left, right in joins:
        lt = _col_to_table(left)
        rt = _col_to_table(right)
        table_adj[lt].add(rt)
        table_adj[rt].add(lt)
        valid_joins.append((left, right))

    # Find largest connected component
    visited = set()
    components = []
    for start in sorted(tables):
        if start in visited:
            continue
        component = set()
        queue = [start]
        while queue:
            node = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)
            component.add(node)
            for neighbor in table_adj.get(node, set()):
                if neighbor not in visited:
                    queue.append(neighbor)
        components.append(component)

    largest = max(components, key=len) if components else set()

    # Build flat SQL
    from_parts = sorted(largest)
    where_parts = []

    for left, right in valid_joins:
        lt = _col_to_table(left)
        rt = _col_to_table(right)
        if lt in largest and rt in largest:
            where_parts.append(f"{left} = {right}")

    # Deduplicate filters
    seen_filters = set()
    for col, op, val in filters:
        ct = _col_to_table(col)
        if ct and ct in largest:
            filt = f"{col} {op} {val}"
            if filt not in seen_filters:
                seen_filters.add(filt)
                where_parts.append(filt)

    if not where_parts:
        return None

    return f"SELECT COUNT(*) FROM {', '.join(from_parts)} WHERE {' AND '.join(where_parts)}"


def transform_sql_for_price(sql, db_name, price_m=False, price_s=False):
    """
    Transform a standard SQL query into PRICE-compatible format.

    PRICE expects:
    - Table aliases in the format `database_abbreviation` (e.g., `imdb_t` for `title`)
    - Column references use these aliases (e.g., `imdb_t.id`)
    - SELECT COUNT(*) FROM ... WHERE ... (no GROUP BY/ORDER BY/LIMIT)

    For TPC-H/DS, also handles:
    - Bare column names (c_custkey → tpch_c.c_custkey) via prefix mapping
    - Self-joins (nation n1, nation n2 → nation tpch_n, nation tpch_n2)
    - CTE/VIEW/subquery-in-FROM flattening via sqlglot
    - Date literal conversion (date '...' + interval '...')

    Args:
        price_m: When True, preserve IN and LIKE predicates for PRICE_M encoding.
        price_s: When True, preserve IN and LIKE predicates for PRICE_S encoding.
    """
    # Convert timestamps/dates to epoch before any other transformation
    sql = _convert_timestamps_to_epoch(sql)

    is_tpc = db_name in ('tpch', 'tpcds')

    # For TPC-H/DS: try sqlglot-based flattening for complex SQL
    # (CTEs, subqueries-in-FROM, VIEWs, queries with no top-level WHERE)
    needs_flattening = False
    if is_tpc:
        sql_lower = sql.strip().lower()
        if sql_lower.startswith('with '):
            needs_flattening = True
        elif 'revenue0' in sql_lower:
            needs_flattening = True
        else:
            # Check if there's a top-level FROM...WHERE or just FROM (subquery)
            from_match_check = re.search(r'\bfrom\b\s+(.*?)\s+\bwhere\b', sql, re.IGNORECASE | re.DOTALL)
            if not from_match_check:
                needs_flattening = True
            elif '(' in (from_match_check.group(1) if from_match_check else ''):
                # FROM clause contains subquery
                needs_flattening = True

    if needs_flattening:
        flattened = flatten_sql_for_price(sql, db_name)
        use_flattened = False
        if flattened is not None:
            # Verify flattened SQL has real table names (not CTE names like v1, wscs)
            _abbrev = _load_abbrev_mapping(db_name)
            fm = re.search(r'\bfrom\b\s+(.*?)\s+\bwhere\b', flattened, re.IGNORECASE | re.DOTALL)
            if fm:
                from_tables = [t.strip().split()[0].lower() for t in fm.group(1).split(',') if t.strip()]
                all_real = all(t in _abbrev for t in from_tables) if from_tables else False
                use_flattened = all_real
            else:
                use_flattened = False

        if use_flattened:
            sql = flattened
        else:
            # Try AST-based predicate collection from entire query tree
            collected = _ast_collect_predicates(sql, db_name)
            if collected is not None:
                sql = collected
            else:
                # Last resort: regex-based predicate collection (no sqlglot)
                regex_collected = _regex_collect_predicates(sql, db_name)
                if regex_collected is not None:
                    sql = regex_collected
                elif flattened is not None:
                    sql = flattened  # Use partial flattening as fallback
                else:
                    return sql  # Can't process at all

    # Preprocess predicates AFTER flattening: subquery inlining, IN → OR, BETWEEN → range,
    # LIKE → drop, scalar subquery estimation, arithmetic evaluation.
    # Must be after CTE flattening because sqlglot round-trip can alter CTE format.
    # PRICE_M/PRICE_S: preserves IN and LIKE for SpaceSaving encoding.
    sql = _preprocess_predicates(sql, db_name, price_m=price_m, price_s=price_s)

    abbrev = _load_abbrev_mapping(db_name)

    # Extract FROM clause content (between FROM and WHERE)
    from_match = re.search(r'\bfrom\b\s+(.*?)\s+\bwhere\b', sql, re.IGNORECASE | re.DOTALL)
    if not from_match:
        return sql  # Can't parse, return as-is

    from_clause = from_match.group(1)
    where_and_after = sql[from_match.end():]

    # Parse table references from FROM clause
    alias_to_price = {}  # old_alias -> price_alias
    table_parts = []
    table_count = {}  # table_name -> occurrence count (for self-join numbering)

    for part in from_clause.split(","):
        part = part.strip()
        if not part:
            continue
        # Match: table_name [AS] alias
        m = re.match(r'(\w+)\s+(?:AS\s+)?(\w+)', part, re.IGNORECASE)
        if m:
            table_name = m.group(1).lower()
            old_alias = m.group(2)
            if table_name in abbrev:
                base_alias = abbrev[table_name]
                count = table_count.get(table_name, 0) + 1
                table_count[table_name] = count
                if count == 1:
                    price_alias = base_alias
                else:
                    # Self-join: use numbered alias (tpch_l2, tpch_l3, etc.)
                    price_alias = f"{base_alias}{count}"
                alias_to_price[old_alias] = price_alias
                table_parts.append(f"{table_name} {price_alias}")
            else:
                table_parts.append(part)
        else:
            # Just a table name without alias — collapse duplicates
            # (bare column names can only reference one instance via prefix mapping)
            table_name = part.strip().lower()
            if table_name in abbrev:
                base_alias = abbrev[table_name]
                if table_name not in table_count:
                    table_count[table_name] = 1
                    alias_to_price[table_name] = base_alias
                    table_parts.append(f"{table_name} {base_alias}")
                # else: duplicate bare table, collapse to first instance
            else:
                table_parts.append(part)

    if not alias_to_price:
        return sql  # No mappings found, return as-is

    new_from = ", ".join(table_parts)

    # Replace alias references in WHERE clause (and subqueries)
    # Sort aliases by length (longest first) to avoid partial replacements
    new_where = where_and_after
    for old_alias, price_alias in sorted(alias_to_price.items(), key=lambda x: -len(x[0])):
        new_where = re.sub(
            r'\b' + re.escape(old_alias) + r'\.',
            price_alias + '.',
            new_where
        )

    # For TPC-H/DS: also replace bare table names in subquery FROM clauses
    # (e.g., "from lineitem where" → "from lineitem tpch_l where")
    # BUT NOT when already aliased (e.g., "from lineitem l2" should keep l2)
    if is_tpc:
        for table_name, price_alias in sorted(abbrev.items(), key=lambda x: -len(x[0])):
            # Only match table name followed by WHERE or comma (i.e., no existing alias)
            new_where = re.sub(
                r'(\bfrom\b\s+)' + re.escape(table_name) + r'(?=\s+(?:where\b|,))',
                r'\g<1>' + table_name + ' ' + price_alias,
                new_where,
                flags=re.IGNORECASE
            )
            # Also handle: "from table_name)" at end of subquery
            new_where = re.sub(
                r'(\bfrom\b\s+)' + re.escape(table_name) + r'(?=\s*\))',
                r'\g<1>' + table_name + ' ' + price_alias,
                new_where,
                flags=re.IGNORECASE
            )

    # For TPC-H/DS: prefix bare column names with PRICE aliases using column prefix mapping
    if is_tpc:
        col_prefixes = _TPCH_COL_PREFIX if db_name == 'tpch' else _TPCDS_COL_PREFIX
        # Build prefix → price_alias mapping
        prefix_to_price = []
        for prefix, table_name in col_prefixes:
            if table_name in abbrev:
                prefix_to_price.append((prefix, abbrev[table_name]))

        for prefix, price_alias in prefix_to_price:
            # Match bare column name starting with this prefix,
            # NOT preceded by a dot or word char (already qualified)
            new_where = re.sub(
                r'(?<!\w)(?<!\.)(' + re.escape(prefix) + r'\w+)\b',
                price_alias + r'.\1',
                new_where
            )

        # Strip GROUP BY, ORDER BY, LIMIT, HAVING
        new_where = _strip_trailing_clauses(new_where)

    # Rebuild full SQL with SELECT COUNT(*)
    # Always use SELECT COUNT(*) to avoid column refs with old aliases in SELECT
    select_part = 'SELECT COUNT(*)'

    result = f"{select_part} FROM {new_from} WHERE {new_where}"
    return result


def extract_pg_est_card_from_plan(plan_json):
    """
    Extract root node's 'Plan Rows' from query plan JSON.
    plan_json can be a dict or a JSON string.
    """
    if isinstance(plan_json, str):
        plan_json = json.loads(plan_json)

    # Navigate to root Plan node
    if isinstance(plan_json, list):
        plan_json = plan_json[0]
    if "Plan" in plan_json:
        root = plan_json["Plan"]
    elif "plan" in plan_json:
        root = plan_json["plan"]
    else:
        root = plan_json

    return float(root.get("Plan Rows", 1.0))


def _is_single_table_query(sql):
    """Check if SQL is a single-table query (no joins in FROM clause)."""
    from_match = re.search(r'\bfrom\b\s+(.*?)\s+\bwhere\b', sql, re.IGNORECASE | re.DOTALL)
    if not from_match:
        return False
    from_clause = from_match.group(1)
    return "," not in from_clause and " join " not in from_clause.lower()


def _create_single_table_features(sql2feat, sql, bin_size):
    """
    Generate PRICE-style features for single-table queries.

    PRICE doesn't support single-table queries (no joins → empty torch.cat crash).
    We generate features using PRICE's internal methods:
    - join_hist: 1 placeholder of zeros (padded later)
    - fanout: 2 placeholders of zeros (padded later)
    - table: proper table features (log_size, avi, minsel, ebo)
    - filter: proper filter features from histogram/summary
    """
    columns, tables, joins, ref_to_tables = sql2feat.parse_sql(sql)

    if len(tables) != 1 or len(joins) != 0:
        return None  # Not actually single-table, let normal path handle it

    table = tables[0]

    # All columns are filter columns (no joins)
    filter_columns = columns

    # Compute filter features and selectivities
    table_sels = []
    filter_column_features = []
    for filter_column in filter_columns:
        col_name = filter_column.split('.')[-1]
        col_table = filter_column.split('.')[0]
        if col_name in sql2feat.information_coltype['col_type'][col_table]['dsct']:
            keys, values = sql2feat.space_saving_summary(filter_column)
            filter_column_histogram = torch.tensor(values) / sql2feat.get_table_size(col_table)
            summary = sql2feat.get_summary_ranges(sql, filter_column, keys)
            if summary is not None:
                filter_column_ranges = torch.tensor(summary)
                location = sql2feat.get_summary_location(sql, filter_column)
                selectivity = torch.tensor([sql2feat.calculate_summary_selectivity(keys, values, location) / sql2feat.get_table_size(col_table)])
                table_sels.append(selectivity.item())
            else:
                filter_column_histogram = torch.tensor(sql2feat.get_column_histograms(filter_column))
                filter_column_ranges = torch.tensor(sql2feat.get_filter_norm_range(sql, filter_column, sql2feat.columns_bin_edges[filter_column]))
                range_low, range_high = sql2feat.get_filter_ranges(sql, filter_column)
                distribution = sql2feat.columns_distributions[filter_column]
                bin_edges = sql2feat.columns_bin_edges[filter_column]
                selectivity = torch.tensor([sql2feat.calculate_hist_selectivity(distribution, bin_edges, range_low, range_high) / sql2feat.get_table_size(col_table)])
                table_sels.append(selectivity.item())
        else:
            filter_column_histogram = torch.tensor(sql2feat.get_column_histograms(filter_column))
            filter_column_ranges = torch.tensor(sql2feat.get_filter_norm_range(sql, filter_column, sql2feat.columns_bin_edges[filter_column]))
            range_low, range_high = sql2feat.get_filter_ranges(sql, filter_column)
            distribution = sql2feat.columns_distributions[filter_column]
            bin_edges = sql2feat.columns_bin_edges[filter_column]
            selectivity = torch.tensor([sql2feat.calculate_hist_selectivity(distribution, bin_edges, range_low, range_high) / sql2feat.get_table_size(col_table)])
            table_sels.append(selectivity.item())

        filter_column_features.append(torch.cat([filter_column_histogram, filter_column_ranges, selectivity]))

    # Table features: log_size, avi, minsel, ebo
    table_size = sql2feat.get_table_size(table)
    if len(table_sels) == 0:
        avi, minsel, ebo = 1.0, 1.0, 1.0
    else:
        avi = float(torch.prod(torch.tensor(table_sels)).item())
        minsel = float(torch.min(torch.tensor(table_sels)).item())
        sorted_sels = sorted(table_sels, reverse=True)
        ebo = 1.0
        for i in range(min(len(sorted_sels), 4)):
            ebo *= sorted_sels[i] ** (1 / (2 ** i))
    table_feat = torch.tensor([np.log(table_size), avi, minsel, ebo])

    # For single-table: use 1 zero join col and 2 zero fanout as placeholders
    # These will be padded by features_padding anyway
    zero_join = torch.zeros(bin_size)
    zero_fanout = torch.zeros(bin_size * 2)

    if len(filter_column_features) > 0:
        filter_feat = torch.cat(filter_column_features)
    else:
        filter_feat = torch.zeros(bin_size + 3)

    n_jc = 1  # placeholder
    n_fo = 2  # placeholder
    n_tb = 1
    n_fc = max(len(filter_columns), 1)

    return (zero_join, zero_fanout, table_feat, filter_feat), n_jc, n_fo, n_tb, n_fc


def _patch_self_join_stats(sql2feat, max_copies=4):
    """
    Add self-join alias entries (e.g., tpch_l2, tpch_l3) to PRICE statistics.

    When self-joins appear (lineitem l1, lineitem l2), transform_sql_for_price
    creates distinct aliases (tpch_l, tpch_l2). PRICE needs statistics for each
    alias. We copy base alias stats to numbered variants.
    """
    base_aliases = list(sql2feat.information_size.keys())

    for base in base_aliases:
        for i in range(2, 2 + max_copies):
            new_alias = f"{base}{i}"
            # Copy histogram
            if base in sql2feat.information_histogram:
                sql2feat.information_histogram[new_alias] = sql2feat.information_histogram[base]
            # Copy summary
            if base in sql2feat.information_summary:
                sql2feat.information_summary[new_alias] = sql2feat.information_summary[base]
            # Copy size
            sql2feat.information_size[new_alias] = sql2feat.information_size[base]
            # Copy col_type
            col_type = sql2feat.information_coltype.get('col_type', {})
            if base in col_type:
                col_type[new_alias] = col_type[base]

    # Add fanout entries for numbered aliases
    existing_keys = list(sql2feat.information_fanout.keys())
    for key in existing_keys:
        # Skip PRICE_N sentinel keys (e.g., "__orphan__") that aren't (col, col) tuples.
        if not isinstance(key, tuple) or len(key) != 2:
            continue
        left_col, right_col = key
        lt = left_col.split('.')[0]
        lc = left_col.split('.')[1]
        rt = right_col.split('.')[0]
        rc = right_col.split('.')[1]

        for i in range(2, 2 + max_copies):
            # numbered_left.col ↔ right.col
            nk = (f"{lt}{i}.{lc}", right_col)
            if nk not in sql2feat.information_fanout:
                sql2feat.information_fanout[nk] = sql2feat.information_fanout[key]
            nk_rev = (right_col, f"{lt}{i}.{lc}")
            if nk_rev not in sql2feat.information_fanout:
                # Reverse the fanout arrays
                sql2feat.information_fanout[nk_rev] = [sql2feat.information_fanout[key][1], sql2feat.information_fanout[key][0]]

            # left.col ↔ numbered_right.col
            nk = (left_col, f"{rt}{i}.{rc}")
            if nk not in sql2feat.information_fanout:
                sql2feat.information_fanout[nk] = sql2feat.information_fanout[key]
            nk_rev = (f"{rt}{i}.{rc}", left_col)
            if nk_rev not in sql2feat.information_fanout:
                sql2feat.information_fanout[nk_rev] = [sql2feat.information_fanout[key][1], sql2feat.information_fanout[key][0]]

    # Add self-join fanout (base.col ↔ baseN.col on same column)
    for base in base_aliases:
        if base not in sql2feat.information_histogram:
            continue
        for col_name in sql2feat.information_histogram[base]:
            # Estimate self-join fanout: use uniform array of 1.0
            # (each row matches ~1 row on average — reasonable for PRICE features)
            uniform_fanout = list(np.ones(sql2feat.bin_size))
            for i in range(2, 2 + max_copies):
                new_alias = f"{base}{i}"
                self_key = (f"{base}.{col_name}", f"{new_alias}.{col_name}")
                rev_key = (f"{new_alias}.{col_name}", f"{base}.{col_name}")
                if self_key not in sql2feat.information_fanout:
                    sql2feat.information_fanout[self_key] = [uniform_fanout, uniform_fanout]
                if rev_key not in sql2feat.information_fanout:
                    sql2feat.information_fanout[rev_key] = [uniform_fanout, uniform_fanout]

            # Cross-numbered-alias fanout (baseN ↔ baseM, e.g., tpch_l2 ↔ tpch_l3)
            for i in range(2, 2 + max_copies):
                for j in range(i + 1, 2 + max_copies):
                    key_ij = (f"{base}{i}.{col_name}", f"{base}{j}.{col_name}")
                    key_ji = (f"{base}{j}.{col_name}", f"{base}{i}.{col_name}")
                    if key_ij not in sql2feat.information_fanout:
                        sql2feat.information_fanout[key_ij] = [uniform_fanout, uniform_fanout]
                    if key_ji not in sql2feat.information_fanout:
                        sql2feat.information_fanout[key_ji] = [uniform_fanout, uniform_fanout]


def _try_create_features(sql2feat, sql):
    """
    Try to create PRICE features. On selectivity=0 error, strip filter conditions
    one at a time and retry. On missing column KeyError, strip that column's
    conditions and retry.
    """
    try:
        return sql2feat.create_sql_features(sql)
    except (AssertionError, ValueError) as e:
        if 'selectivity should not be 0' not in str(e):
            raise
    except (KeyError, IndexError):
        pass  # Missing column or unqualified column — fall through to retry

    # Retry: strip filter conditions one at a time
    from_match = re.search(
        r'\bselect\s+count\(\*\)\s+from\s+(.*?)\s+where\s+(.*)',
        sql, re.IGNORECASE | re.DOTALL
    )
    if not from_match:
        return None

    from_str = from_match.group(1)
    where_str = from_match.group(2)
    conditions = _split_where_on_and(where_str)

    # Separate joins from filters
    joins = []
    filters = []
    for cond in conditions:
        m = re.match(r'\s*(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)\s*$', cond.strip())
        if m:
            joins.append(cond)
        else:
            filters.append(cond)

    # Try dropping filters one at a time (from end, typically the problematic ones)
    for i in range(len(filters)):
        remaining = joins + filters[:len(filters) - 1 - i]
        if not remaining:
            break
        retry_sql = f"select count(*) from {from_str} where {' and '.join(remaining)}"
        try:
            result = sql2feat.create_sql_features(retry_sql)
            if result is not None:
                return result
        except (AssertionError, ValueError, KeyError, IndexError):
            continue

    return None


def generate_price_features(workload, sql_list, db_name, bin_size=40, price_m=False, price_s=False, already_price_format=False):
    """
    Generate PRICE features for each SQL query using Sql2Feature (or Sql2FeatureM/S).

    Transforms SQL to PRICE-compatible format before feature extraction.
    Handles single-table queries (no joins) with a dedicated feature generator.

    Args:
        workload: Workload name (for logging)
        sql_list: List of raw SQL strings
        db_name: Database name for PRICE statistics (e.g., 'imdb', 'stats')
        bin_size: Histogram bin size (default 40)
        price_m: When True, use PRICE_M encoding (61-dim filters with IN/LIKE support)
        price_s: When True, use PRICE_S encoding (43-dim filters with IN/LIKE via bounding-box range)
        already_price_format: When True, SQL is already in PRICE alias format
            (from cross-workload plan reconstruction). Skip transform_sql_for_price()
            and most cleanup functions.

    Returns:
        data_features: list of tuples (join_hist, fanout, table, filter) per query
        n_join_cols: list of int
        n_fanouts: list of int
        n_tables: list of int
        n_filter_cols: list of int
    """
    mode_tag = "_m" if price_m else ("_s" if price_s else "")
    xwl_tag = "_xwl" if already_price_format else ""
    cache_dir = os.path.join(os.path.dirname(__file__), "price_feature_cache")
    cache_key = f"{db_name}_bin{bin_size}{mode_tag}{xwl_tag}_{workload}_n{len(sql_list)}.pkl"
    cache_path = os.path.join(cache_dir, cache_key)

    if os.path.exists(cache_path):
        print(f"[PRICE{mode_tag.upper()}] Loading cached raw features from {cache_path} ({len(sql_list)} queries)")
        with open(cache_path, "rb") as f:
            cached = pickle.load(f)
        return (cached["data_features"], cached["n_join_cols"],
                cached["n_fanouts"], cached["n_tables"], cached["n_filter_cols"])

    if price_m:
        from setup.features_tool_m import Sql2FeatureM
        sql2feat = Sql2FeatureM(db_name, bin_size, "finetune")
    elif price_s:
        from setup.features_tool_s import Sql2FeatureS
        sql2feat = Sql2FeatureS(db_name, bin_size, "finetune")
    else:
        from setup.features_tool import Sql2Feature
        sql2feat = Sql2Feature(db_name, bin_size, "finetune")
    _patch_self_join_stats(sql2feat)

    data_features = []
    n_join_cols = []
    n_fanouts = []
    n_tables = []
    n_filter_cols = []
    success_count = 0
    single_table_count = 0
    fail_count = 0

    total = len(sql_list)
    log_interval = max(1, total // 20)  # ~5% increments

    filter_dim = (bin_size + 21) if price_m else (bin_size + 3)

    for idx, sql in enumerate(sql_list):
        if idx % log_interval == 0:
            print(f"[PRICE{mode_tag.upper()}] Generating features: {idx}/{total} ({100*idx//total}%)", flush=True)
        try:
            if already_price_format:
                # SQL is already in PRICE alias format (from cross-workload reconstruction)
                # Just apply lowercasing for safety
                transformed_sql = _lower_except_quotes(sql)
            else:
                # Transform SQL to PRICE format (PRICE_M/S preserves IN and LIKE)
                transformed_sql = transform_sql_for_price(sql, db_name, price_m=price_m, price_s=price_s)
                # PRICE expects lowercase (except inside quotes)
                transformed_sql = _lower_except_quotes(transformed_sql)
                # Collapse self-join aliases (tpcds_dd2 → tpcds_dd) where only tautological joins
                transformed_sql = _collapse_self_joins(transformed_sql)
                # Add missing tables to FROM when WHERE references known aliases not in FROM
                transformed_sql = _add_missing_from_tables(transformed_sql, db_name)
                # Convert BETWEEN to >= / <= range comparisons (before any AND-splitting)
                transformed_sql = _convert_between_to_range(transformed_sql)
                # Strip same-table conditions and dangling references
                transformed_sql = _strip_same_table_conditions(transformed_sql)
                # Clean trailing SQL artifacts (GROUP BY, unbalanced parens, CASE, substring)
                transformed_sql = _clean_sql_artifacts(transformed_sql)
                # Hoist joins from inside OR blocks to top level (e.g., TPC-H Q19)
                transformed_sql = _hoist_joins_from_or_blocks(transformed_sql)
                # Remove disconnected tables (islands from subquery inlining)
                transformed_sql = _prune_disconnected_tables(transformed_sql)
                # Prune redundant joins to satisfy PRICE's tree constraint
                transformed_sql = _prune_redundant_joins(transformed_sql)
                # Clean up 1 = 1 tautologies left by _prune_redundant_joins
                transformed_sql = _strip_tautologies(transformed_sql)

            # Handle single-table queries specially (PRICE doesn't support them)
            # PRICE_M/S handle single-table internally
            if _is_single_table_query(transformed_sql) and not price_m and not price_s:
                result = _create_single_table_features(sql2feat, transformed_sql, bin_size)
                if result is None:
                    raise ValueError("single-table feature generation returned None")
                feats, n_jc, n_fo, n_tb, n_fc = result
                data_features.append(feats)
                n_join_cols.append(n_jc)
                n_fanouts.append(n_fo)
                n_tables.append(n_tb)
                n_filter_cols.append(n_fc)
                single_table_count += 1
                success_count += 1
                continue

            result = _try_create_features(sql2feat, transformed_sql)
            if result is None:
                raise ValueError(f"create_sql_features returned None for query {idx}")
            feats, n_jc, n_fo, n_tb, n_fc = result
            data_features.append(feats)
            n_join_cols.append(n_jc)
            n_fanouts.append(n_fo)
            n_tables.append(n_tb)
            n_filter_cols.append(n_fc)
            success_count += 1
        except Exception as e:
            if fail_count < 5:
                print(f"[PRICE{mode_tag.upper()}] Warning: Failed to generate features for query {idx}: {e}")
            elif fail_count == 5:
                print(f"[PRICE{mode_tag.upper()}] Suppressing further warnings...")
            fail_count += 1
            # Use zero-feature placeholder with proper empty tensors
            zero_join = torch.zeros(bin_size)  # 1 join col placeholder
            zero_fanout = torch.zeros(bin_size * 2)  # 2 fanout placeholder
            zero_table = torch.zeros(4)  # 1 table with 4 features
            zero_filter = torch.zeros(filter_dim)  # 1 filter placeholder
            data_features.append((zero_join, zero_fanout, zero_table, zero_filter))
            n_join_cols.append(1)
            n_fanouts.append(2)
            n_tables.append(1)
            n_filter_cols.append(1)

    print(f"[PRICE{mode_tag.upper()}] Feature generation: {success_count} succeeded ({single_table_count} single-table), {fail_count} failed out of {len(sql_list)}")

    os.makedirs(cache_dir, exist_ok=True)
    with open(cache_path, "wb") as f:
        pickle.dump({
            "data_features": data_features,
            "n_join_cols": n_join_cols,
            "n_fanouts": n_fanouts,
            "n_tables": n_tables,
            "n_filter_cols": n_filter_cols,
        }, f)
    print(f"[PRICE{mode_tag.upper()}] Cached raw features to {cache_path}")

    return data_features, n_join_cols, n_fanouts, n_tables, n_filter_cols


def _lower_except_quotes(sql):
    """Lowercase SQL except for text inside quotes (matching PRICE's preprocessing)."""
    result = []
    in_quote = False
    quote_char = None
    for char in sql:
        if in_quote:
            result.append(char)
            if char == quote_char:
                in_quote = False
        else:
            if char in ("'", '"'):
                in_quote = True
                quote_char = char
                result.append(char)
            else:
                result.append(char.lower())
    return ''.join(result)


def pad_and_cache_features(data_features, n_join_cols, n_fanouts, n_tables, n_filter_cols,
                           bin_size=40, table_dim=4, filter_dim=43,
                           cache_path=None, price_m=False):
    """
    Pad variable-length features to uniform size and optionally cache.

    Args:
        data_features: list of tuples from generate_price_features
        n_join_cols, n_fanouts, n_tables, n_filter_cols: per-query counts
        bin_size: histogram bin size
        table_dim: table feature dimension (default 4: log_size, avi, minsel, ebo)
        filter_dim: filter feature dimension (default bin_size+3 = 43, or bin_size+21 for PRICE_M)
        cache_path: if set, save/load from this pickle path

    Returns:
        padded_features: list of tensors, each of uniform length
        padding_masks: list of tensors
        max_n_join_col, max_n_fanout, max_n_table, max_n_filter_col
    """
    if cache_path and os.path.exists(cache_path):
        print(f"[PRICE] Loading cached features from {cache_path}")
        with open(cache_path, "rb") as f:
            cached = pickle.load(f)
        return (cached["padded_features"], cached["padding_masks"],
                cached["max_n_join_col"], cached["max_n_fanout"],
                cached["max_n_table"], cached["max_n_filter_col"])

    # Compute filter_dim: use PRICE_M (bin_size+21) if price_m flag is set
    if price_m:
        filter_dim = bin_size + 21
    # Import from PRICE's utils.model.padding (avoid name conflict with other 'utils' packages)
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location("price_padding", os.path.join(PRICE_ROOT, "utils", "model", "padding.py"))
    _padding_mod = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_padding_mod)
    features_padding = _padding_mod.features_padding

    padded_features, padding_masks = features_padding(
        bin_size, table_dim, filter_dim,
        list(data_features),  # make a copy since padding modifies in-place
        n_join_cols, n_fanouts, n_tables, n_filter_cols
    )

    max_n_join_col = max(n_join_cols) if n_join_cols else 0
    max_n_fanout = max(n_fanouts) if n_fanouts else 0
    max_n_table = max(n_tables) if n_tables else 0
    max_n_filter_col = max(n_filter_cols) if n_filter_cols else 0

    if cache_path:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        print(f"[PRICE] Caching features to {cache_path}")
        with open(cache_path, "wb") as f:
            pickle.dump({
                "padded_features": padded_features,
                "padding_masks": padding_masks,
                "max_n_join_col": max_n_join_col,
                "max_n_fanout": max_n_fanout,
                "max_n_table": max_n_table,
                "max_n_filter_col": max_n_filter_col,
            }, f)

    return (padded_features, padding_masks,
            max_n_join_col, max_n_fanout, max_n_table, max_n_filter_col)


def get_db_name_for_workload(workload):
    """Map LLM4QPR workload name to PRICE database name."""
    if workload in ("syn", "job", "job_full", "jobm", "imdb", "imdb_job", "imdb_jobm"):
        return "imdb"
    elif workload == "stats":
        return "stats"
    elif workload == "tpch":
        return "tpch"
    elif workload == "tpcds":
        return "tpcds"
    else:
        return workload


# Cross-workload database names (matches cross_workload_price_config.py)
_CROSS_WORKLOAD_DBS = {
    "accidents", "airline", "baseball", "basketball", "carcinogenesis",
    "consumer", "credit", "employee", "fhnk", "financial",
    "geneea", "genome", "hepatitis", "imdb", "movielens",
    "seznam", "ssb", "tournament", "tpc_h", "walmart",
}


def is_cross_workload_db(db_name):
    """Check if a database is one of the 20 cross-workload databases."""
    return db_name in _CROSS_WORKLOAD_DBS


def get_sql_for_cross_workload_plans(json_path, db_name):
    """Reconstruct PRICE-format SQL from a deepdb_augmented JSON plan file.

    Returns a list of SQL strings (one per plan, None if reconstruction fails).
    """
    from reconstruct_sql_from_plans import reconstruct_all_sql
    from cross_workload_price_config import get_abbrev_for_db
    abbrev = get_abbrev_for_db(db_name)
    return reconstruct_all_sql(json_path, db_name, abbrev)


def get_db_name_from_json_path(json_path):
    """Extract cross-workload database name from a deepdb_augmented JSON path.

    E.g., '../deepdb_augmented/financial/workload_100k_s1_c8220.json' -> 'financial'
    """
    return os.path.basename(os.path.dirname(json_path))


def get_sql_file_for_workload(workload, card=False, for_training=False):
    """
    Get the path to the queries_true_sql file for a given workload.
    Must match the CSV file used for query plans.

    Args:
        workload: Workload name (e.g., 'job', 'syn', 'stats')
        card: If True, return the cardinality sub-plan SQL file
        for_training: If True, return the SQL file matching the *training* CSV
                      (e.g., full imdb.sql for job/syn, full stats.sql for stats).
                      If False, return the SQL file matching the *test* CSV.
    """
    base_dir = os.path.join(os.path.dirname(__file__), "..", "queries_true_sql")
    base_dir = os.path.abspath(base_dir)

    if card:
        # Cardinality uses _sub variants (match *_sub.csv plans)
        if workload == "syn":
            return os.path.join(base_dir, "imdb_syn_sub.sql")
        elif workload == "job":
            return os.path.join(base_dir, "imdb_job_sub.sql")
        elif workload == "job_full":
            return os.path.join(base_dir, "imdb_job_sub.sql")
        elif workload == "stats":
            return os.path.join(base_dir, "stats_statsCEB_sub.sql")
    elif for_training:
        # Training CSV: long_raw_postgres_imdb.csv (syn/job/job_full)
        #               long_raw_postgres_stats.csv (stats)
        if workload in ("syn", "job", "job_full", "jobm"):
            return os.path.join(base_dir, "imdb.sql")           # 100k queries → 100k plans
        elif workload == "stats":
            return os.path.join(base_dir, "stats.sql")          # 67962 queries → 67962 plans
        elif workload == "tpch":
            return os.path.join(base_dir, "tpch.sql")           # 2200 queries
        elif workload == "tpcds":
            return os.path.join(base_dir, "tpcds.sql")          # 9900 queries
    else:
        # Test CSV: long_raw_postgres_imdb_{workload}.csv
        if workload == "syn":
            return os.path.join(base_dir, "imdb_syn.sql")       # 5000 queries → 5000 plans
        elif workload in ("job", "imdb_job"):
            return os.path.join(base_dir, "imdb_job.sql")       # 69 queries → 69 plans
        elif workload == "job_full":
            return os.path.join(base_dir, "imdb_job.sql")       # same JOB queries
        elif workload in ("jobm", "imdb_jobm"):
            return os.path.join(base_dir, "imdb_jobm.sql")      # 113 queries → 113 plans
        elif workload == "stats":
            return os.path.join(base_dir, "stats_statsCEB.sql") # 141 queries → 141 plans
        elif workload == "tpch":
            return os.path.join(base_dir, "tpch.sql")
        elif workload == "tpcds":
            return os.path.join(base_dir, "tpcds.sql")

    # Fallback
    return os.path.join(base_dir, f"{workload}.sql")
