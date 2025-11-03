"""
Field category definitions for PostgreSQL query plan ablation studies.

This module defines how query plan fields are classified into 6 categories:
- 5 user-selectable categories (for ablation studies)
- 1 runtime category (always removed automatically)
"""

# Field category definitions for PostgreSQL query plans
FIELD_CATEGORIES = {
    'operator_structure_and_config': {
        # Core operator information and node-specific configurations
        'Node Type',
        'Parent Relationship',
        # Scan node configurations
        'Relation Name',
        'Schema',
        'Alias',
        'Index Name',
        'Scan Direction',
        # CTE Scan node configurations
        'CTE Name',
        # Function Scan node configurations
        'Function Name',
        'Table Function Name',
        # Subplan node configurations
        'Subplan Name',
        # Join node configurations
        'Join Type',
        'Inner Unique',
        # Sort node configurations
        'Sort Key',
        'Presorted Key',
        # Hash node configurations (Hash Join, Hash Aggregate)
        'Hash Keys',
        # Insert node configurations
        'Conflict Resolution',
        'Conflict Arbiter Indexes',
        'Tuples Inserted',
        # Output projection (applies to most nodes)
        'Output',
        # Other node-specific configurations
        'Strategy',
        'Partial Mode',
    },
    'cost': {
        # Cost estimates (planned)
        'Startup Cost',
        'Total Cost',
        'Plan Width',  # Moved from cardinality - width is related to cost calculation
    },
    'cardinality': {
        # Row count estimates (planned)
        'Plan Rows',  # Only this field - the actual row count estimate
    },
    'conditions_and_filters': {
        # Query conditions and filters that affect cardinality
        'Filter',
        'Join Filter',
        'Index Cond',
        'Recheck Cond',
        'Hash Cond',
        'Merge Cond',
        'One-Time Filter',
        'TID Cond',
        'Group Key',
    },
    'metadata_and_config': {
        # Query-level and execution-level metadata (not node-specific)
        # Query-level metadata
        'Command',
        'Triggers',
        'Planning Time',
        # Execution capability and parallelism configuration
        'Parallel Aware',
        'Async Capable',
        'Workers Planned',
        'Single Copy',
    },
    'runtime': {
        # === ACTUAL EXECUTION STATISTICS ===
        # Timing and row counts
        'Actual Startup Time',
        'Actual Total Time',
        'Actual Rows',
        'Actual Loops',
        
        # === ROWS REMOVED / SELECTIVITY ===
        'Rows Removed by Filter',
        'Rows Removed by Index Recheck',
        'Rows Removed by Join Filter',
        
        # === MEMORY & DISK USAGE ===
        'Peak Memory Usage',
        'Sort Space Used',
        'Sort Space Type',
        'Work Mem Used',
        
        # === CACHE/BUFFER STATISTICS ===
        # Shared buffer statistics
        'Shared Hit Blocks',
        'Shared Read Blocks',
        'Shared Dirtied Blocks',
        'Shared Written Blocks',
        # Local buffer statistics
        'Local Hit Blocks',
        'Local Read Blocks',
        'Local Dirtied Blocks',
        'Local Written Blocks',
        # Temporary file statistics
        'Temp Read Blocks',
        'Temp Written Blocks',
        
        # === STORAGE ACCESS STATISTICS ===
        'I/O Read Time',
        'I/O Write Time',
        'Exact Heap Blocks',
        'Lossy Heap Blocks',
        'Heap Fetches',
        
        # === HASH EXECUTION DETAILS ===
        'Hash Buckets',
        'Hash Batches',
        'Original Hash Batches',
        
        # === PARALLELISM EXECUTION ===
        'Workers Launched',
        'Workers',
        'Worker Number',
        
        # === SORT EXECUTION DETAILS ===
        'Sort Method',
        
        # === INCREMENTAL SORT STATISTICS ===
        'Full-sort Groups',
        'Sort Groups Count',
        'Sort Methods Used',
        
        # === OTHER RUNTIME STATISTICS ===
        'Execution Time',
        'Subplan Calls',
        'WAL Records',
        'WAL FPI',
        'WAL Bytes',
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
    
    # Valid categories for user selection (runtime is always removed, not user-selectable)
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

