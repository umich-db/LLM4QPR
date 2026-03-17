#!/usr/bin/env python3
"""
Create combined SQL files for TPC-H and TPC-DS in queries_true_sql/ directory.

Reads individual query files from queries/tpch/ and queries/tpcds/,
parses EXPLAIN blocks, flattens multi-line SQL to single lines,
and writes them in the format expected by extract_raw_sql_from_queries_true():

    EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
    <single-line SQL>;

    (blank line)

Special handling:
- TPC-H query 15 has CREATE VIEW / DROP VIEW lines that are skipped
  (only EXPLAIN + SQL blocks are kept)
- All multi-line SQL is collapsed to a single line with normalized whitespace
"""

import os
import re

QUERIES_DIR = "/root/LLM4QPR/queries"
OUTPUT_DIR = "/root/LLM4QPR/queries_true_sql"

EXPLAIN_PREFIX = "EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)"


def parse_explain_blocks(file_path):
    """
    Parse a .sql file and extract EXPLAIN blocks.

    Returns a list of SQL strings (without the EXPLAIN prefix).
    Handles multi-line SQL that ends with a semicolon.
    Skips non-EXPLAIN lines (e.g., CREATE VIEW, DROP VIEW).
    """
    with open(file_path, "r") as f:
        lines = f.readlines()

    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if line == EXPLAIN_PREFIX:
            # Collect SQL lines until we find one ending with ;
            i += 1
            sql_parts = []
            while i < len(lines):
                sql_line = lines[i].rstrip("\n")
                stripped = sql_line.strip()

                if stripped == "":
                    # Blank line inside SQL block - skip but keep going
                    # (shouldn't normally happen, but be safe)
                    i += 1
                    continue

                sql_parts.append(stripped)
                if stripped.endswith(";"):
                    break
                i += 1
            i += 1

            if sql_parts:
                # Flatten to single line: join parts with space, normalize whitespace
                flat_sql = " ".join(sql_parts)
                # Normalize multiple spaces to single space
                flat_sql = re.sub(r"\s+", " ", flat_sql).strip()
                blocks.append(flat_sql)
        else:
            # Skip non-EXPLAIN lines (CREATE VIEW, DROP VIEW, blank lines, etc.)
            i += 1

    return blocks


def create_combined_sql(workload_name):
    """
    Create a combined SQL file for the given workload (tpch or tpcds).

    Reads all .sql files from queries/{workload_name}/ sorted numerically,
    parses EXPLAIN blocks from each, and writes them to
    queries_true_sql/{workload_name}.sql.
    """
    input_dir = os.path.join(QUERIES_DIR, workload_name)
    output_file = os.path.join(OUTPUT_DIR, f"{workload_name}.sql")

    # Get sorted list of .sql files
    sql_files = [f for f in os.listdir(input_dir) if f.endswith(".sql")]
    sql_files.sort(key=lambda x: int(x.replace(".sql", "")))

    print(f"\n{'='*60}")
    print(f"Processing {workload_name}: {len(sql_files)} query files")
    print(f"Input dir:  {input_dir}")
    print(f"Output file: {output_file}")
    print(f"{'='*60}")

    total_queries = 0
    all_blocks = []

    for fname in sql_files:
        fpath = os.path.join(input_dir, fname)
        blocks = parse_explain_blocks(fpath)
        query_num = int(fname.replace(".sql", ""))
        print(f"  Query {query_num:3d}: {len(blocks)} variants")
        total_queries += len(blocks)
        all_blocks.extend(blocks)

    # Write output file
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(output_file, "w") as f:
        for sql in all_blocks:
            f.write(f"{EXPLAIN_PREFIX}\n")
            f.write(f"{sql}\n")
            f.write("\n")

    print(f"\nTotal queries written: {total_queries}")
    print(f"Output: {output_file}")

    # Verify the output by re-reading
    verify_combined_sql(output_file, total_queries)

    return total_queries


def verify_combined_sql(sql_file, expected_count):
    """Verify the combined SQL file has the correct format."""
    with open(sql_file, "r") as f:
        lines = f.readlines()

    explain_count = 0
    issues = []

    i = 0
    while i < len(lines):
        line = lines[i].rstrip("\n")
        if line == EXPLAIN_PREFIX:
            explain_count += 1
            # Next line should be single-line SQL ending with ;
            if i + 1 < len(lines):
                sql_line = lines[i + 1].rstrip("\n")
                if not sql_line.endswith(";"):
                    issues.append(f"Line {i+2}: SQL does not end with semicolon: ...{sql_line[-50:]}")
                if "\n" in sql_line:
                    issues.append(f"Line {i+2}: SQL contains newline (not flattened)")
            # Line after SQL should be blank
            if i + 2 < len(lines):
                blank = lines[i + 2].rstrip("\n")
                if blank != "":
                    issues.append(f"Line {i+3}: Expected blank line, got: {blank[:50]}")
            i += 3
        elif line == "":
            i += 1
        else:
            issues.append(f"Line {i+1}: Unexpected content: {line[:80]}")
            i += 1

    print(f"\nVerification of {sql_file}:")
    print(f"  EXPLAIN blocks found: {explain_count}")
    print(f"  Expected: {expected_count}")
    print(f"  Match: {'YES' if explain_count == expected_count else 'NO'}")
    print(f"  Format issues: {len(issues)}")
    for issue in issues[:10]:
        print(f"    {issue}")
    if len(issues) > 10:
        print(f"    ... and {len(issues) - 10} more")

    if issues:
        raise ValueError(f"Verification failed with {len(issues)} issues")


def main():
    # Create TPC-H combined SQL file
    tpch_count = create_combined_sql("tpch")

    # Create TPC-DS combined SQL file
    tpcds_count = create_combined_sql("tpcds")

    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"TPC-H:  {tpch_count} queries -> queries_true_sql/tpch.sql")
    print(f"TPC-DS: {tpcds_count} queries -> queries_true_sql/tpcds.sql")


if __name__ == "__main__":
    main()
