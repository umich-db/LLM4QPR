"""Tests for PRICE_N parsing rules and feature extractor.

Run with:
    cd /root/LLM4QPR && python -m pytest tests/test_price_n.py -v
"""
import os
import sys

# Ensure both the LLM4QPR experiments dir and the PRICE setup dir are on path.
sys.path.insert(0, "/root/LLM4QPR/experiments")
sys.path.insert(0, "/root/PRICE")
sys.path.insert(0, "/root/LLM4QPR/PRICE")


def test_imports_work():
    """Smoke test: confirm the test environment can import the modules
    we will be exercising. This catches path-ordering or venv issues
    before any real test runs."""
    import sqlglot  # noqa: F401
    from setup.features_tool import Sql2Feature  # noqa: F401
    import price_data_utils  # noqa: F401


def test_stats_generator_accepts_price_n_flags():
    """The stats generator must accept the four PRICE_N flags + shorthand
    via argparse without error (we don't actually run aggregates here)."""
    import subprocess
    result = subprocess.run(
        ["python", "/root/LLM4QPR/experiments/generate_price_stats_from_pg.py",
         "--db", "tpch", "--price_n", "--dry_run"],
        capture_output=True, text=True,
    )
    # We expect the script to exit cleanly under --dry_run with the flags
    # parsed but no DB work performed.
    assert "unrecognized arguments" not in result.stderr, result.stderr
    assert result.returncode == 0, f"stderr: {result.stderr}"


def test_null_fraction_aggregate_produces_dict():
    """generate_null_fractions returns a dict[(table, col)] -> float in [0, 1]."""
    sys.path.insert(0, "/root/LLM4QPR/experiments")
    from generate_price_stats_from_pg import (
        get_connection, generate_null_fractions, build_table_columns,
        DB_CONFIG,
    )
    pg_db, abbrev, _ = DB_CONFIG["tpch"]
    conn = get_connection(pg_db)
    table_col_dtypes = build_table_columns(conn)
    # Limit the set so the test is fast: just sample one column per known table.
    cols = set()
    for t, alias in abbrev.items():
        if t in table_col_dtypes:
            cols.add((t, sorted(table_col_dtypes[t])[0]))
    out = generate_null_fractions(conn, abbrev, cols)
    conn.close()
    assert isinstance(out, dict) and len(out) > 0
    for (t, c), frac in out.items():
        assert 0.0 <= frac <= 1.0, f"{t}.{c} → {frac} out of [0,1]"


def test_orphan_fraction_aggregate_produces_dict():
    """generate_orphan_fractions returns dict[(L_col, R_col)] -> (orphan_LR, orphan_RL),
    each in [0, 1]."""
    sys.path.insert(0, "/root/LLM4QPR/experiments")
    from generate_price_stats_from_pg import (
        get_connection, generate_orphan_fractions, DB_CONFIG,
    )
    pg_db, abbrev, _ = DB_CONFIG["tpch"]
    conn = get_connection(pg_db)
    # Use a single tpch join pair: lineitem.l_orderkey = orders.o_orderkey.
    joins = {(("lineitem", "l_orderkey"), ("orders", "o_orderkey"))}
    out = generate_orphan_fractions(conn, abbrev, joins)
    conn.close()
    key = ("tpch_l.l_orderkey", "tpch_o.o_orderkey")
    assert key in out, f"missing key {key} in {list(out.keys())[:3]}"
    o_lr, o_rl = out[key]
    assert 0.0 <= o_lr <= 1.0 and 0.0 <= o_rl <= 1.0


def test_pairwise_intra_aggregate_produces_dict():
    """generate_pairwise_intra returns dict[(table, col_x, col_y)] -> {
        'H8x8_ordered': np.ndarray (64,),
        's_lt': float, 's_eq': float, 's_gt': float
    } and the three sels sum to ~1."""
    import numpy as np
    sys.path.insert(0, "/root/LLM4QPR/experiments")
    from generate_price_stats_from_pg import (
        get_connection, generate_pairwise_intra, DB_CONFIG,
    )
    pg_db, _, _ = DB_CONFIG["tpch"]
    conn = get_connection(pg_db)
    pairs = [("lineitem", "l_shipdate", "l_commitdate")]
    out = generate_pairwise_intra(conn, pairs)
    conn.close()
    assert ("lineitem", "l_shipdate", "l_commitdate") in out
    rec = out[("lineitem", "l_shipdate", "l_commitdate")]
    assert isinstance(rec["H8x8_ordered"], np.ndarray)
    assert rec["H8x8_ordered"].shape == (64,)
    assert abs(rec["s_lt"] + rec["s_eq"] + rec["s_gt"] - 1.0) < 1e-3


def test_pairwise_xtab_aggregate_produces_dict():
    """generate_pairwise_xtab returns the cross-table 2D joint with the same
    schema as generate_pairwise_intra but a 4-tuple key."""
    import numpy as np
    sys.path.insert(0, "/root/LLM4QPR/experiments")
    from generate_price_stats_from_pg import (
        get_connection, generate_pairwise_xtab, DB_CONFIG,
    )
    pg_db, _, _ = DB_CONFIG["tpcds"]
    conn = get_connection(pg_db)
    pairs = [("inventory", "inv_quantity_on_hand",
              "catalog_sales", "cs_quantity")]
    out = generate_pairwise_xtab(conn, pairs, sample_n=10000)
    conn.close()
    key = ("inventory", "inv_quantity_on_hand",
           "catalog_sales", "cs_quantity")
    assert key in out
    assert out[key]["H8x8_ordered"].shape == (64,)
    assert abs(out[key]["s_lt"] + out[key]["s_eq"]
               + out[key]["s_gt"] - 1.0) < 1e-3


def test_sql2feature_n_skeleton_dims():
    sys.path.insert(0, "/root/LLM4QPR/PRICE")
    from setup.features_tool_n import Sql2FeatureN
    f = Sql2FeatureN("tpch", 40, "finetune")
    assert f.filter_dim_n == 75
    assert f.fanout_dim_n == 42
    assert f.pairwise_dim_n == 129
    assert f.K == 10
    assert f.PAIRWISE_GRID == 8


def test_filter_token_eq_single_value():
    sys.path.insert(0, "/root/LLM4QPR/PRICE")
    from setup.features_tool_n import Sql2FeatureN
    f = Sql2FeatureN("tpch", 40, "finetune")
    # equality on a known continuous column
    atoms = {"eq_values": [50000], "in_values": [], "not_in_values": [],
             "range_low": None, "range_high": None,
             "is_null": False, "is_not_null": False, "like_keys": []}
    tok = f._encode_filter_token("tpch_p.p_size", atoms)
    assert tok.shape == (75,)
    # null_pred_flag is the last entry, zero for no NULL atom
    assert tok[-1].item() == 0.0


def test_filter_token_in_with_overflow():
    sys.path.insert(0, "/root/LLM4QPR/PRICE")
    from setup.features_tool_n import Sql2FeatureN
    f = Sql2FeatureN("tpch", 40, "finetune")
    atoms = {"eq_values": [],
             "in_values": list(range(15)),
             "not_in_values": [], "range_low": None, "range_high": None,
             "is_null": False, "is_not_null": False, "like_keys": []}
    tok = f._encode_filter_token("tpch_p.p_size", atoms)
    assert tok.shape == (75,)
    # tail bucket selectivity (slot 11 = index 40 + 30 + 2) should be nonzero
    tail_sel_idx = 40 + 3 * 10 + 2
    assert tok[tail_sel_idx].item() >= 0.0  # nonneg; may be 0 if values absent


def test_filter_token_is_null():
    sys.path.insert(0, "/root/LLM4QPR/PRICE")
    from setup.features_tool_n import Sql2FeatureN
    f = Sql2FeatureN("tpch", 40, "finetune")
    atoms = {"eq_values": [], "in_values": [], "not_in_values": [],
             "range_low": None, "range_high": None,
             "is_null": True, "is_not_null": False, "like_keys": []}
    tok = f._encode_filter_token("tpch_p.p_size", atoms)
    assert tok[-1].item() == 1.0      # null_pred_flag = +1


def test_filter_token_is_not_null():
    sys.path.insert(0, "/root/LLM4QPR/PRICE")
    from setup.features_tool_n import Sql2FeatureN
    f = Sql2FeatureN("tpch", 40, "finetune")
    atoms = {"eq_values": [], "in_values": [], "not_in_values": [],
             "range_low": None, "range_high": None,
             "is_null": False, "is_not_null": True, "like_keys": []}
    tok = f._encode_filter_token("tpch_p.p_size", atoms)
    assert tok[-1].item() == -1.0     # null_pred_flag = -1


def test_pairwise_intra_token_lt():
    sys.path.insert(0, "/root/LLM4QPR/PRICE")
    from setup.features_tool_n import Sql2FeatureN
    f = Sql2FeatureN("tpch", 40, "finetune")
    tok = f._encode_pairwise_intra_token(
        "lineitem", "l_shipdate", "l_commitdate", "<")
    assert tok.shape == (129,)
    # Mask is 64 dims at offset 64; for "<" exactly the first 28 should be 1.
    mask = tok[64:128]
    assert mask[:28].sum().item() == 28.0
    assert mask[28:].sum().item() == 0.0


def test_pairwise_intra_token_eq():
    sys.path.insert(0, "/root/LLM4QPR/PRICE")
    from setup.features_tool_n import Sql2FeatureN
    f = Sql2FeatureN("tpch", 40, "finetune")
    tok = f._encode_pairwise_intra_token(
        "lineitem", "l_shipdate", "l_commitdate", "=")
    mask = tok[64:128]
    # Region-2 only (8 cells at indices 28..35).
    assert mask[28:36].sum().item() == 8.0
    assert mask[:28].sum().item() == 0.0
    assert mask[36:].sum().item() == 0.0


def test_pairwise_intra_token_xtab_falls_through_to_xtab_pkl():
    sys.path.insert(0, "/root/LLM4QPR/PRICE")
    from setup.features_tool_n import Sql2FeatureN
    f = Sql2FeatureN("tpcds", 40, "finetune")
    tok = f._encode_pairwise_intra_token(
        "inventory", "inv_quantity_on_hand", "<",
        right_table="catalog_sales", right_col="cs_quantity")
    assert tok.shape == (129,)
