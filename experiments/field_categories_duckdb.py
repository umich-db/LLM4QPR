"""
Field category definitions for DuckDB query plan ablation studies.

This module defines how DuckDB query plan fields are classified into 6 categories:
- 5 user-selectable categories (for ablation studies)
- 1 runtime category (always removed automatically)

DuckDB plan structure:
  Root: query-level metadata (latency, rows_returned, ...) + children (operator tree)
  Nodes: operator_name, operator_type, extra_info{...}, children[...], timing/cardinality fields
  extra_info: nested dict with Estimated Cardinality, Join Type, Conditions, Filters, Table, Projections, etc.
"""

# Field category definitions for DuckDB query plans
FIELD_CATEGORIES = {
    'operator_structure_and_config': {
        # Core operator identification
        'operator_name',
        'operator_type',
        # Join configuration (inside extra_info)
        'Join Type',
        # Scan configuration (inside extra_info)
        'Table',
        'Type',
        # Output projection (inside extra_info)
        'Projections',
        # Expressions (inside extra_info)
        'Expression',
    },
    'cost': {
        # DuckDB does not expose separate startup/total cost fields.
        # Estimated Cardinality is the planner's row estimate (closest to cost info).
        # Kept empty so cardinality category holds the estimate instead.
    },
    'cardinality': {
        # Planner's row count estimate (inside extra_info)
        'Estimated Cardinality',
    },
    'conditions_and_filters': {
        # Join and filter conditions (inside extra_info)
        'Conditions',
        'Filters',
    },
    'metadata_and_config': {
        # Query-level metadata
        'query_name',
        # extra_info container itself is structural, not removed
    },
    'runtime': {
        # === QUERY-LEVEL RUNTIME STATISTICS (root) ===
        'latency',
        'rows_returned',
        'result_set_size',
        'cpu_time',
        'blocked_thread_time',
        'system_peak_buffer_memory',
        'system_peak_temp_dir_size',
        'total_bytes_read',
        'total_bytes_written',

        # === OPERATOR-LEVEL RUNTIME STATISTICS (nodes) ===
        'operator_timing',
        'operator_cardinality',
        'operator_rows_scanned',
        'cumulative_cardinality',
        'cumulative_rows_scanned',
        # result_set_size, cpu_time, total_bytes_read, total_bytes_written
        # also appear at node level — already listed above
    }
}


def get_fields_to_remove(removed_categories):
    """
    Given a list of category names, return the set of all fields to remove.

    Note: The 'runtime' category is ALWAYS removed automatically and should not be
    specified in removed_categories. Only the other 5 categories are valid options.

    Args:
        removed_categories: List of category names (e.g., ['cost', 'cardinality'])
                           Valid: operator_structure_and_config, cost, cardinality,
                                  conditions_and_filters, metadata_and_config
                           Invalid: runtime (always removed automatically)

    Returns:
        Set of field names to remove (excluding runtime fields, which are handled separately)
    """
    if not removed_categories:
        return set()

    valid_categories = {
        'operator_structure_and_config',
        'cost',
        'cardinality',
        'conditions_and_filters',
        'metadata_and_config'
    }

    fields_to_remove = set()
    for category in removed_categories:
        if category == 'runtime':
            print(f"Warning: 'runtime' category is always removed by default. No need to specify it.")
            continue
        if category in valid_categories:
            fields_to_remove.update(FIELD_CATEGORIES[category])
        else:
            print(f"Warning: Unknown field category '{category}'. Valid categories: {sorted(valid_categories)}")

    return fields_to_remove


def get_category_summary():
    """
    Return a summary of field categories for documentation/debugging.

    Returns:
        Dictionary with category statistics
    """
    summary = {}
    for category, fields in FIELD_CATEGORIES.items():
        summary[category] = {
            'count': len(fields),
            'user_selectable': category != 'runtime',
            'fields': sorted(fields)
        }
    return summary
