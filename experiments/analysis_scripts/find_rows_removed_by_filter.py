#!/usr/bin/env python3
"""
Find which Node Types have the "Rows Removed by Filter" field in query plans.

Scans all query plan CSV files under queryPlans/ and identifies node types
that contain the "Rows Removed by Filter" field.
"""

import json
import pandas as pd
from pathlib import Path
from collections import defaultdict
import sys


def extract_node_types_with_field(plan_dict, field_name, node_types_set):
    """
    Recursively traverse a query plan tree and collect node types that have the specified field.
    
    Args:
        plan_dict: Dictionary representing a node in the query plan
        field_name: Name of the field to search for (e.g., "Rows Removed by Filter")
        node_types_set: Set to store node types that have this field
    """
    if not isinstance(plan_dict, dict):
        return
    
    # Check if this node has the field
    if field_name in plan_dict:
        node_type = plan_dict.get("Node Type", "Unknown")
        node_types_set.add(node_type)
    
    # Recursively check child plans
    if "Plans" in plan_dict:
        for child_plan in plan_dict["Plans"]:
            extract_node_types_with_field(child_plan, field_name, node_types_set)


def process_csv_file(csv_path, field_name):
    """
    Process a single CSV file containing query plans.
    
    Returns:
        Set of node types that have the specified field
    """
    node_types = set()
    
    try:
        df = pd.read_csv(csv_path)
        
        # Check if the CSV has the expected structure
        if 'json' not in df.columns:
            print(f"Warning: {csv_path} does not have a 'json' column. Skipping.")
            return node_types
        
        # Process each row
        for idx, row in df.iterrows():
            try:
                json_str = row['json']
                # Parse the JSON string (it's double-encoded)
                plan_data = json.loads(json_str)
                
                # Extract the Plan from the parsed data
                if "Plan" in plan_data:
                    extract_node_types_with_field(plan_data["Plan"], field_name, node_types)
                else:
                    # Sometimes the JSON might be the plan directly
                    extract_node_types_with_field(plan_data, field_name, node_types)
                    
            except json.JSONDecodeError as e:
                print(f"Warning: Failed to parse JSON in {csv_path} row {idx}: {e}")
                continue
            except Exception as e:
                print(f"Warning: Error processing {csv_path} row {idx}: {e}")
                continue
                
    except Exception as e:
        print(f"Error reading {csv_path}: {e}")
    
    return node_types


def main():
    # Base directory for query plans
    base_dir = Path("/home/jovyan/workspace/LLM4QPR/queryPlans")
    
    if not base_dir.exists():
        print(f"Error: Directory {base_dir} does not exist")
        sys.exit(1)
    
    # Field name to search for
    field_name = "Rows Removed by Filter"
    
    # Find all CSV files with "long_raw_postgres" in the name
    csv_files = list(base_dir.rglob("long_raw_postgres*.csv"))
    
    if not csv_files:
        print(f"No CSV files found in {base_dir}")
        sys.exit(1)
    
    print(f"Found {len(csv_files)} CSV files to process")
    print("=" * 80)
    
    # Process each CSV file
    all_node_types = set()
    file_node_types = defaultdict(set)
    
    for csv_file in sorted(csv_files):
        print(f"Processing: {csv_file.relative_to(base_dir)}")
        node_types = process_csv_file(csv_file, field_name)
        file_node_types[csv_file.name] = node_types
        all_node_types.update(node_types)
        if node_types:
            print(f"  Found node types: {sorted(node_types)}")
        else:
            print(f"  No node types with '{field_name}' found")
        print()
    
    # Print summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\nAll Node Types that have '{field_name}':")
    for node_type in sorted(all_node_types):
        print(f"  - {node_type}")
    
    print(f"\nTotal: {len(all_node_types)} unique node type(s)")
    
    # Show which files contain which node types
    print("\n" + "=" * 80)
    print("BREAKDOWN BY FILE")
    print("=" * 80)
    for csv_name, node_types in sorted(file_node_types.items()):
        if node_types:
            print(f"\n{csv_name}:")
            for node_type in sorted(node_types):
                print(f"  - {node_type}")


if __name__ == "__main__":
    main()



