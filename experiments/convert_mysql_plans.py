#!/usr/bin/env python3
"""
Convert MySQL EXPLAIN ANALYZE .txt files to long_raw CSV format.

Self-contained parser — no external 'parsers' module dependency.
Produces PostgreSQL-style JSON plans compatible with the LLM4QPR pipeline.

Usage:
    python convert_mysql_plans.py \
        --input_folder ~/mysql_and_spark/mysql/results \
        --output_csv  queryPlans/stats/mysql/long_raw_mysql_stats.csv
"""

import argparse
import csv
import json
import os
import re
import sys
from collections import defaultdict

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------
# Matches: (cost=23631 rows=871)
_COST_RE = re.compile(
    r'\(cost=([\d.eE+\-]+)\s+rows=([\d.eE+\-]+)\)'
)
# Matches: (actual time=1.19..203 rows=65927 loops=1)
_ACTUAL_RE = re.compile(
    r'\(actual\s+time=([\d.eE+\-]+)\.\.([\d.eE+\-]+)\s+rows=([\d.eE+\-]+)\s+loops=([\d.eE+\-]+)\)'
)
# Matches: (never executed)
_NEVER_EXEC_RE = re.compile(r'\(never executed\)')

# Table name from "on <table>"
_TABLE_RE = re.compile(r'\bon\s+(\w+)')
# Index name from "using <index>"
_INDEX_RE = re.compile(r'\busing\s+(\w+)')

# Join condition from operators like "Inner hash join (t.col = t2.col)"
_JOIN_COND_RE = re.compile(r'^(Inner hash join|Nested loop \w+ join)\s*\((.+?)\)\s*$')


# ---------------------------------------------------------------------------
# MySQL line parser
# ---------------------------------------------------------------------------
def _parse_mysql_line(line):
    """Parse one line of MySQL EXPLAIN ANALYZE output.

    Returns dict with keys:
        operator, filter, table, index, join_cond,
        est_cost, est_rows, actual_time_start, actual_time_end,
        actual_rows, actual_loops
    """
    info = {
        'operator': None,
        'filter': None,
        'table': None,
        'index': None,
        'join_cond': None,
        'est_cost': 0.0,
        'est_rows': 0.0,
        'actual_time_start': 0.0,
        'actual_time_end': 0.0,
        'actual_rows': 0.0,
        'actual_loops': 1.0,
    }

    # Extract cost and actual metrics
    cost_m = _COST_RE.search(line)
    if cost_m:
        info['est_cost'] = float(cost_m.group(1))
        info['est_rows'] = float(cost_m.group(2))

    actual_m = _ACTUAL_RE.search(line)
    if actual_m:
        info['actual_time_start'] = float(actual_m.group(1))
        info['actual_time_end'] = float(actual_m.group(2))
        info['actual_rows'] = float(actual_m.group(3))
        info['actual_loops'] = float(actual_m.group(4))
    elif _NEVER_EXEC_RE.search(line):
        # never executed node
        pass

    # Strip metric parentheticals for operator parsing
    op_text = _COST_RE.sub('', line)
    op_text = _ACTUAL_RE.sub('', op_text)
    op_text = _NEVER_EXEC_RE.sub('', op_text)
    op_text = op_text.strip()

    # Extract filter condition from "Filter: (...)"
    filter_match = re.match(r'^Filter:\s*(.+)', op_text)
    if filter_match:
        info['operator'] = 'Filter'
        info['filter'] = filter_match.group(1).strip()
        return info

    # Extract table name from "on <table>"
    table_m = _TABLE_RE.search(op_text)
    if table_m:
        info['table'] = table_m.group(1)

    # Extract index name from "using <index>"
    idx_m = _INDEX_RE.search(op_text)
    if idx_m:
        info['index'] = idx_m.group(1)

    # Extract join condition from "Inner hash join (cond)"
    join_m = _JOIN_COND_RE.match(op_text)
    if join_m:
        info['join_cond'] = join_m.group(2).strip()

    # Operator name: everything before "on", "using", parenthetical cond, ":"
    op_name = re.sub(r'\s+on\s+\w+.*', '', op_text)
    op_name = re.sub(r'\s+using\s+\w+.*', '', op_name)
    op_name = re.sub(r'\s*\(.*\)', '', op_name)
    op_name = re.sub(r':.*', '', op_name)
    op_name = op_name.strip()
    if not op_name:
        op_name = 'Unknown'
    info['operator'] = op_name

    return info


# ---------------------------------------------------------------------------
# Tree builder
# ---------------------------------------------------------------------------
def _build_tree(plan_text):
    """Parse MySQL EXPLAIN ANALYZE text into a nested dict tree.

    The raw file has literal '\\n' characters; we replace them with real
    newlines, then use leading-space indentation + '-> ' prefix to determine
    parent-child relationships.
    """
    text = plan_text.replace('\\n', '\n')
    lines = text.splitlines()

    nodes = []  # list of (indent_level, parsed_info_dict, children_list)

    for line in lines:
        stripped = line.rstrip()
        if not stripped or 'EXPLAIN' in stripped:
            continue

        # Count indentation
        leading = len(stripped) - len(stripped.lstrip(' '))

        # Remove '-> ' prefix
        content = stripped.lstrip()
        if content.startswith('-> '):
            content = content[3:]

        parsed = _parse_mysql_line(content)
        nodes.append((leading, parsed, []))

    if not nodes:
        return None

    # Build tree using a stack of (indent_level, node_dict, children_ref)
    stack = []
    for indent, info, children in nodes:
        node = info
        node['children'] = children

        # Pop items from stack that are at >= current indent (siblings or deeper)
        while stack and stack[-1][0] >= indent:
            stack.pop()

        if stack:
            # Append as child of the top-of-stack
            stack[-1][2].append(node)
        else:
            # Root node
            pass

        stack.append((indent, node, node['children']))

    # The root is the first node
    return nodes[0][1]


# ---------------------------------------------------------------------------
# Post-processing
# ---------------------------------------------------------------------------
def _multiply_by_loops(node):
    """Multiply actual_rows and est_rows by loops (MySQL reports per-loop values)."""
    loops = node.get('actual_loops', 1.0)
    node['actual_rows'] = node.get('actual_rows', 0) * loops
    node['est_rows'] = node.get('est_rows', 0) * loops
    # Timing: actual_time_end already reflects per-loop time; multiply for total
    node['actual_time_start'] = node.get('actual_time_start', 0) * loops
    node['actual_time_end'] = node.get('actual_time_end', 0) * loops
    for child in node.get('children', []):
        _multiply_by_loops(child)


def _compute_operator_time(node):
    """Post-order: operator_time = own total time - sum of children total times."""
    child_time = 0.0
    for child in node.get('children', []):
        _compute_operator_time(child)
        child_time += child.get('actual_time_end', 0.0)
    node['operator_time'] = max(0.0, node.get('actual_time_end', 0.0) - child_time)


def _merge_filter_into_scan(node):
    """Merge a Filter node into its scan/join child, moving the filter condition down.

    This matches PostgreSQL behaviour where filters are attached to scan nodes.
    """
    children = node.get('children', [])

    # Recursively process children first
    for child in children:
        _merge_filter_into_scan(child)

    if node.get('operator') == 'Filter' and len(children) == 1:
        child = children[0]
        scan_types = {
            'Table scan', 'Index lookup', 'Single-row index lookup',
            'Covering index lookup', 'Index range scan',
        }
        join_types = {
            'Nested loop inner join', 'Nested loop left join',
            'Inner hash join', 'Hash join', 'Merge join',
        }
        if child.get('operator') in scan_types:
            # Merge: child inherits filter's timing and rows
            child['filter'] = node.get('filter')
            child['actual_time_end'] = node.get('actual_time_end', child.get('actual_time_end', 0))
            child['actual_rows'] = node.get('actual_rows', child.get('actual_rows', 0))
            child['actual_loops'] = node.get('actual_loops', child.get('actual_loops', 1))
            # Replace self with child
            node.update(child)
        elif child.get('operator') in join_types:
            # Attach filter to join node
            existing = child.get('filter', '')
            new_filter = node.get('filter', '')
            if existing and new_filter:
                child['filter'] = f"({existing}) AND ({new_filter})"
            else:
                child['filter'] = existing or new_filter
            child['actual_time_end'] = node.get('actual_time_end', child.get('actual_time_end', 0))
            child['actual_rows'] = node.get('actual_rows', child.get('actual_rows', 0))
            node.update(child)


def _infer_table_from_filter(filter_text):
    """Try to extract a single table alias from filter like '(c.Score = 0)'."""
    if not filter_text:
        return None
    matches = re.findall(r'\b(\w+)\.\w+', filter_text)
    unique = set(matches)
    if len(unique) == 1:
        return unique.pop()
    return None


def _fill_missing(node):
    """Fill missing relation names and plan rows by inference."""
    if not node.get('table') and node.get('filter'):
        inferred = _infer_table_from_filter(node['filter'])
        if inferred:
            node['table'] = inferred

    if node.get('est_rows') in (None, 0.0) and node.get('children'):
        total = sum(c.get('est_rows', 0) or 0 for c in node['children'])
        node['est_rows'] = total if total > 0 else 1.0

    if node.get('est_cost') in (None, 0.0) and node.get('children'):
        total = sum(c.get('est_cost', 0) or 0 for c in node['children'])
        node['est_cost'] = total

    for child in node.get('children', []):
        _fill_missing(child)


def _remove_angle_brackets(node):
    """Remove <...> wrappers from filter text (MySQL artefact like <cache>(...)).

    Only removes angle-bracket expressions that start with a letter (e.g. <cache>,
    <in_optimizer>), NOT comparison operators like <= or >=.
    """
    if node.get('filter'):
        node['filter'] = re.sub(r'<[a-zA-Z][^>]*>', '', node['filter']).strip()
    for child in node.get('children', []):
        _remove_angle_brackets(child)


# ---------------------------------------------------------------------------
# Convert to PostgreSQL-style JSON
# ---------------------------------------------------------------------------
def _to_pg_json(node):
    """Convert parsed tree node to PostgreSQL-style JSON dict."""
    d = {
        'Node Type': node.get('operator', 'Unknown'),
        'Actual Startup Time': node.get('actual_time_start', 0.0),
        'Actual Total Time': node.get('actual_time_end', 0.0),
        'Actual Rows': node.get('actual_rows', 0.0),
        'Actual Loops': node.get('actual_loops', 1.0),
        'Total Cost': node.get('est_cost', 0.0),
        'Plan Rows': node.get('est_rows', 0.0),
    }

    if node.get('filter'):
        if node.get('operator') == 'Sort':
            d['Sort Key'] = node['filter']
        else:
            d['Filter'] = node['filter']

    if node.get('table'):
        d['Relation Name'] = node['table']

    if node.get('index'):
        d['Index Name'] = node['index']

    if node.get('join_cond'):
        cond = node['join_cond']
        # Wrap in parens for condPipeline compatibility (uses nestedExpr)
        if not cond.startswith('('):
            cond = f'({cond})'
        d['Hash Cond'] = cond

    children = node.get('children', [])
    if children:
        d['Plans'] = [_to_pg_json(c) for c in children]

    return d


def _replace_none(obj):
    """Recursively replace None with 0.0."""
    if isinstance(obj, dict):
        return {k: _replace_none(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_replace_none(e) for e in obj]
    elif obj is None:
        return 0.0
    return obj


# ---------------------------------------------------------------------------
# Main conversion
# ---------------------------------------------------------------------------
def convert_one_file(filepath):
    """Convert a single MySQL EXPLAIN ANALYZE .txt file to a list of PG-style JSON plans."""
    with open(filepath, 'r') as f:
        content = f.read()

    if not content.strip():
        return []

    # Find all EXPLAIN blocks; use the last one (some files have two)
    explain_positions = [m.start() for m in re.finditer(r'EXPLAIN', content)]
    if not explain_positions:
        return []

    # Use the last EXPLAIN block
    plan_text = content[explain_positions[-1]:]

    tree = _build_tree(plan_text)
    if tree is None:
        return []

    _multiply_by_loops(tree)
    _compute_operator_time(tree)
    _merge_filter_into_scan(tree)
    _fill_missing(tree)
    _remove_angle_brackets(tree)

    pg = _to_pg_json(tree)
    pg = _replace_none(pg)

    return [pg]


def process_files(input_folder, output_csv, file_pattern=r'stats_(\d+)_run0\.txt'):
    """Process all matching .txt files and write CSV."""
    os.makedirs(os.path.dirname(output_csv) or '.', exist_ok=True)

    # Collect matching files sorted by numeric ID
    files = []
    for fname in os.listdir(input_folder):
        m = re.match(file_pattern, fname)
        if m:
            files.append((int(m.group(1)), fname))
    files.sort()

    id_counter = 1
    errors = 0
    empty = 0

    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['id', 'json'])

        for file_id, fname in files:
            fpath = os.path.join(input_folder, fname)
            try:
                plans = convert_one_file(fpath)
                if not plans:
                    empty += 1
                    continue
                for plan in plans:
                    writer.writerow([id_counter, json.dumps(plan)])
                    id_counter += 1
            except Exception as e:
                errors += 1
                print(f"Error processing {fname}: {e}")

    total = id_counter - 1
    print(f"\nMySQL conversion complete:")
    print(f"  Output: {output_csv}")
    print(f"  Plans written: {total}")
    print(f"  Empty/skipped files: {empty}")
    print(f"  Errors: {errors}")

    return total


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert MySQL EXPLAIN ANALYZE .txt to CSV')
    parser.add_argument('--input_folder', type=str, required=True,
                        help='Directory with stats_*_run0.txt files')
    parser.add_argument('--output_csv', type=str, required=True,
                        help='Output CSV path (e.g. queryPlans/stats/mysql/long_raw_mysql_stats.csv)')
    parser.add_argument('--file_pattern', type=str, default=r'stats_(\d+)_run0\.txt',
                        help='Regex pattern for input filenames (must have one capture group for numeric ID)')
    args = parser.parse_args()

    process_files(args.input_folder, args.output_csv, args.file_pattern)
