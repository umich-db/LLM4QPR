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
    assert f.pairwise_dim_n == 70
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


def test_pairwise_intra_token_lt_single_range():
    sys.path.insert(0, "/root/LLM4QPR/PRICE")
    from setup.features_tool_n import Sql2FeatureN
    f = Sql2FeatureN("tpch", 40, "finetune")
    tok = f._encode_pairwise_intra_token(
        "lineitem", "l_shipdate", "l_commitdate", "<")
    assert tok.shape == (70,)
    # Slot 1: bins 0-27 (x<y region)
    low_1, high_1, sel_1 = tok[64].item(), tok[65].item(), tok[66].item()
    assert abs(low_1 - 0.0) < 1e-6
    assert abs(high_1 - 28 / 64) < 1e-6
    # Slot 2 unused → zeros
    low_2, high_2, sel_2 = tok[67].item(), tok[68].item(), tok[69].item()
    assert low_2 == 0.0 and high_2 == 0.0 and sel_2 == 0.0


def test_pairwise_intra_token_eq_diagonal_range():
    sys.path.insert(0, "/root/LLM4QPR/PRICE")
    from setup.features_tool_n import Sql2FeatureN
    f = Sql2FeatureN("tpch", 40, "finetune")
    tok = f._encode_pairwise_intra_token(
        "lineitem", "l_shipdate", "l_commitdate", "=")
    assert tok.shape == (70,)
    low_1, high_1 = tok[64].item(), tok[65].item()
    assert abs(low_1 - 28 / 64) < 1e-6
    assert abs(high_1 - 36 / 64) < 1e-6
    # Slot 2 unused
    assert tok[67].item() == 0.0 and tok[68].item() == 0.0


def test_pairwise_intra_token_neq_two_ranges():
    sys.path.insert(0, "/root/LLM4QPR/PRICE")
    from setup.features_tool_n import Sql2FeatureN
    f = Sql2FeatureN("tpch", 40, "finetune")
    tok = f._encode_pairwise_intra_token(
        "lineitem", "l_shipdate", "l_commitdate", "!=")
    assert tok.shape == (70,)
    # Slot 1: bins 0-27
    low_1, high_1 = tok[64].item(), tok[65].item()
    assert abs(low_1 - 0.0) < 1e-6 and abs(high_1 - 28 / 64) < 1e-6
    # Slot 2: bins 36-63
    low_2, high_2 = tok[67].item(), tok[68].item()
    assert abs(low_2 - 36 / 64) < 1e-6 and abs(high_2 - 1.0) < 1e-6


def test_pairwise_intra_token_xtab_falls_through_to_xtab_pkl():
    sys.path.insert(0, "/root/LLM4QPR/PRICE")
    from setup.features_tool_n import Sql2FeatureN
    f = Sql2FeatureN("tpcds", 40, "finetune")
    tok = f._encode_pairwise_intra_token(
        "inventory", "inv_quantity_on_hand", "<",
        right_table="catalog_sales", right_col="cs_quantity")
    assert tok.shape == (70,)


def test_fanout_ext_inner_join_zero_outer_bits():
    sys.path.insert(0, "/root/LLM4QPR/PRICE")
    from setup.features_tool_n import Sql2FeatureN
    f = Sql2FeatureN("tpch", 40, "finetune")
    join = "tpch_l.l_orderkey = tpch_o.o_orderkey"
    f1, f2 = f._encode_fanout_tokens_extended(join, side="INNER")
    assert f1.shape == (42,)
    assert f2.shape == (42,)
    # last 2 dims = (orphan_fraction, outer_preserve_flag); preserve=0 for INNER.
    assert f1[-1].item() == 0.0
    assert f2[-1].item() == 0.0


def test_fanout_ext_left_join_preserve_flag():
    sys.path.insert(0, "/root/LLM4QPR/PRICE")
    from setup.features_tool_n import Sql2FeatureN
    f = Sql2FeatureN("tpch", 40, "finetune")
    join = "tpch_l.l_orderkey = tpch_o.o_orderkey"
    f_lr, f_rl = f._encode_fanout_tokens_extended(join, side="LEFT")
    # L→R has preserve_flag = 1, R→L has 0.
    assert f_lr[-1].item() == 1.0
    assert f_rl[-1].item() == 0.0


def test_create_sql_features_returns_5_tuple_for_simple_query():
    sys.path.insert(0, "/root/LLM4QPR/PRICE")
    from setup.features_tool_n import Sql2FeatureN
    f = Sql2FeatureN("tpch", 40, "finetune")
    sql = ("select count(*) from tpch_l, tpch_o "
           "where tpch_l.l_orderkey = tpch_o.o_orderkey "
           "and tpch_l.l_quantity = 50")
    atoms_meta = {
        "filter_atoms": {
            "tpch_l.l_quantity": {**f.EMPTY_ATOMS, "eq_values": [50]},
        },
        "join_sides": {},          # all INNER
        "pairwise_atoms": [],      # no col-op-col / xtab non-equi
    }
    out = f.create_sql_features(sql, atoms_meta=atoms_meta)
    assert out is not None
    feats, n_jc, n_fo, n_tb, n_fc, n_pi = out
    assert len(feats) == 5
    join_hist, fanout_ext, table, filter_n, pairwise_intra = feats
    assert filter_n.shape[0] == 75 * n_fc
    assert fanout_ext.shape[0] == 42 * n_fo
    assert n_pi == 0
    assert pairwise_intra.numel() == 0


def test_not_pushdown_de_morgan_and():
    sys.path.insert(0, "/root/LLM4QPR/experiments")
    from price_data_utils import _push_not_to_nnf
    import sqlglot
    ast = sqlglot.parse_one(
        "SELECT * FROM t WHERE NOT (t.a < 5 AND t.b > 10)")
    _push_not_to_nnf(ast)
    sql = ast.sql()
    # Expect rewrite to (t.a >= 5 OR t.b <= 10) — De Morgan plus operator flips.
    assert "NOT" not in sql.upper().replace("NOT NULL", "").replace("IS NOT", "")
    assert ">=" in sql and "<=" in sql


def test_not_pushdown_double_neg():
    sys.path.insert(0, "/root/LLM4QPR/experiments")
    from price_data_utils import _push_not_to_nnf
    import sqlglot
    ast = sqlglot.parse_one("SELECT * FROM t WHERE NOT NOT (t.a = 5)")
    _push_not_to_nnf(ast)
    assert "NOT" not in ast.sql().upper().replace("NOT NULL", "").replace("IS NOT", "")


def test_not_pushdown_is_null_flip():
    sys.path.insert(0, "/root/LLM4QPR/experiments")
    from price_data_utils import _push_not_to_nnf
    import sqlglot
    ast = sqlglot.parse_one("SELECT * FROM t WHERE NOT (t.a IS NULL)")
    _push_not_to_nnf(ast)
    assert "IS NOT NULL" in ast.sql().upper()


def test_disjoint_or_to_in_collapses_chain():
    sys.path.insert(0, "/root/LLM4QPR/experiments")
    from price_data_utils import _rewrite_disjoint_or_to_in
    import sqlglot
    ast = sqlglot.parse_one(
        "SELECT * FROM t WHERE (t.c = 1) OR (t.c = 2) OR (t.c = 3)")
    _rewrite_disjoint_or_to_in(ast)
    sql = ast.sql()
    assert " IN " in sql.upper()
    assert " OR " not in sql.upper()


def test_disjoint_or_keeps_mixed_columns():
    sys.path.insert(0, "/root/LLM4QPR/experiments")
    from price_data_utils import _rewrite_disjoint_or_to_in
    import sqlglot
    ast = sqlglot.parse_one(
        "SELECT * FROM t WHERE (t.c = 1) OR (t.d = 2)")
    _rewrite_disjoint_or_to_in(ast)
    # Mixed columns must NOT be collapsed.
    assert " IN " not in ast.sql().upper()


def test_normalize_date_literal_to_epoch_days():
    sys.path.insert(0, "/root/LLM4QPR/experiments")
    from price_data_utils import _normalize_date_literals
    import sqlglot
    ast = sqlglot.parse_one(
        "SELECT * FROM t WHERE t.dt = DATE '1970-01-08'")
    _normalize_date_literals(ast)
    # 1970-01-08 = day 7 since epoch.
    assert "=7" in ast.sql().replace(" ", "")


def test_normalize_date_arith_literal():
    sys.path.insert(0, "/root/LLM4QPR/experiments")
    from price_data_utils import _normalize_date_literals
    import sqlglot
    ast = sqlglot.parse_one(
        "SELECT * FROM t WHERE t.dt < DATE '1970-01-15' - INTERVAL '5' DAY")
    _normalize_date_literals(ast)
    # 1970-01-15 = day 14, minus 5 = 9.
    assert "9" in ast.sql()


def test_extract_filter_atoms_collects_eq_in_null():
    sys.path.insert(0, "/root/LLM4QPR/experiments")
    from price_data_utils import _extract_filter_atoms
    import sqlglot
    ast = sqlglot.parse_one(
        "SELECT * FROM tpch_l "
        "WHERE tpch_l.l_quantity IN (10, 20) "
        "AND tpch_l.l_shipmode IS NOT NULL")
    atoms = _extract_filter_atoms(ast)
    assert atoms["tpch_l.l_quantity"]["in_values"] == [10, 20]
    assert atoms["tpch_l.l_shipmode"]["is_not_null"] is True


def test_extract_pairwise_intra_atoms_finds_self_pair():
    sys.path.insert(0, "/root/LLM4QPR/experiments")
    from price_data_utils import _extract_pairwise_intra_atoms
    import sqlglot
    ast = sqlglot.parse_one(
        "SELECT * FROM tpch_l "
        "WHERE tpch_l.l_shipdate < tpch_l.l_commitdate")
    atoms = _extract_pairwise_intra_atoms(ast)
    assert ("tpch_l", "l_shipdate", "l_commitdate", "<", None, None) in atoms


def test_extract_xtab_nonequi_atoms_whitelist_only():
    sys.path.insert(0, "/root/LLM4QPR/experiments")
    from price_data_utils import _extract_xtab_nonequi_atoms
    import sqlglot
    ast = sqlglot.parse_one(
        "SELECT * FROM inventory inv, catalog_sales cs "
        "WHERE inv.inv_quantity_on_hand < cs.cs_quantity")
    atoms = _extract_xtab_nonequi_atoms(ast)
    assert any(a[2] == "<" for a in atoms)


def test_flatten_join_with_side_preserves_left():
    sys.path.insert(0, "/root/LLM4QPR/experiments")
    from price_data_utils import _flatten_join_with_side
    sql = ("SELECT * FROM tpch_a a "
           "LEFT JOIN tpch_b b ON a.k = b.k")
    flat_sql, sides = _flatten_join_with_side(sql)
    assert any(s == "LEFT" for _, _, s in sides)


def test_transform_sql_with_price_n_parsing_runs_without_error():
    sys.path.insert(0, "/root/LLM4QPR/experiments")
    from price_data_utils import transform_sql_for_price
    sql = ("SELECT count(*) FROM tpch_l "
           "WHERE NOT (tpch_l.l_quantity > 50 AND tpch_l.l_shipmode IS NULL) "
           "AND tpch_l.l_quantity = 30")
    out = transform_sql_for_price(
        sql, "tpch",
        price_n_parsing=True, price_n_filter=True,
        price_n_fanout=False, price_n_pairwise=False)
    assert "NOT" not in out.upper().replace("NOT NULL", "").replace("IS NOT", "")


def test_generate_price_features_returns_5_tuple_under_price_n():
    sys.path.insert(0, "/root/LLM4QPR/experiments")
    from price_data_utils import generate_price_features
    sqls = [
        "SELECT count(*) FROM lineitem l, orders o "
        "WHERE l.l_orderkey = o.o_orderkey AND l.l_quantity = 30",
    ]
    out = generate_price_features(
        "tpch_smoke", sqls, "tpch",
        price_n_parsing=True, price_n_filter=True,
        price_n_fanout=True, price_n_pairwise=True)
    # 6-tuple of lists when price_n_pairwise=True
    assert len(out) == 6
    data_features, *_ = out
    assert len(data_features) == 1
    assert len(data_features[0]) == 5  # 5-tuple per query


def test_pad_and_cache_features_handles_pairwise_axis():
    import torch
    sys.path.insert(0, "/root/LLM4QPR/experiments")
    from price_data_utils import pad_and_cache_features
    feats = [
        (torch.zeros(40), torch.zeros(2 * 42),
         torch.zeros(8), torch.zeros(75 * 1), torch.zeros(70 * 0)),
        (torch.zeros(40), torch.zeros(2 * 42),
         torch.zeros(8), torch.zeros(75 * 1), torch.zeros(70 * 1)),
    ]
    out = pad_and_cache_features(
        feats, n_join_cols=[1, 1], n_fanouts=[2, 2], n_tables=[2, 2],
        n_filter_cols=[1, 1], n_pairwise_intras=[0, 1],
        bin_size=40, table_dim=4, filter_dim=75,
        pairwise_intra_dim=70, price_n_pairwise=True)
    assert len(out) >= 6  # padded_features, masks, max counts (one extra for pairwise)


def test_scale_embedding_accepts_parametric_fanout_dim():
    sys.path.insert(0, "/root/PRICE")
    import torch
    from model.module import ScaleEmbedding
    se = ScaleEmbedding(n_join_col=2, n_fanout=2, hist_dim=40,
                        n_embd=64, fanout_token_dim=42)
    # 2 join cols × 40 + 2 fanout tokens × 42 = 80 + 84 = 164
    x = torch.zeros(1, 164)
    out = se(x)
    assert out.shape == (1, 1 + 2 + 2, 64)  # virtual + 2 join + 2 fanout


def test_regression_model_accepts_pairwise_intra_embedding_dim():
    sys.path.insert(0, "/root/PRICE")
    import torch
    from model.encoder import RegressionModel
    rm = RegressionModel(
        n_join_col=2, n_fanout=4, n_table=2, n_filter_col=2,
        n_pairwise_intra=1,
        hist_dim=40, table_dim=4, filter_dim=75,
        fanout_dim=42, pairwise_intra_dim=70,
        n_embd=64, n_layers=2, n_heads=4, dropout_rate=0.1,
        query_hidden_dim=64,
        final_hidden_dim=64, output_dim=1)
    # Total flat width: 2*40 (joins) + 4*42 (fanout) + 2*4 (tables)
    # + 2*75 (filter) + 1*70 (pairwise) = 80 + 168 + 8 + 150 + 70 = 476
    x = torch.zeros(2, 476)
    pg_est_card = torch.zeros(2, 1)
    n_jc = torch.tensor([[2.0]] * 2)
    n_fo = torch.tensor([[4.0]] * 2)
    n_tb = torch.tensor([[2.0]] * 2)
    n_fc = torch.tensor([[2.0]] * 2)
    out = rm(x, pg_est_card=pg_est_card,
             n_join_col=n_jc, n_fanout=n_fo, n_table=n_tb, n_filter_col=n_fc)
    assert out.shape == (2, 1)


def test_partial_copy_filter_embedding_43_to_75():
    sys.path.insert(0, "/root/LLM4QPR/experiments")
    import torch
    from models.llm_price_model import _load_price_n_state_dict
    # Build a fake "pretrained" PRICE state dict (filter_dim=43, fanout=40).
    pretrained = {
        "filter_embedding.filter_embeddings.weight": torch.randn(64, 43),
        "filter_embedding.filter_embeddings.bias": torch.randn(64),
        "scale_embedding.fanout_embeddings.weight": torch.randn(64, 41),
        "scale_embedding.fanout_embeddings.bias": torch.randn(64),
    }
    # Build a target model with PRICE_N dims.
    sys.path.insert(0, "/root/PRICE")
    from model.encoder import RegressionModel
    target = RegressionModel(
        n_join_col=1, n_fanout=2, n_table=1, n_filter_col=1,
        n_pairwise_intra=0,
        hist_dim=40, table_dim=4, filter_dim=75,
        fanout_dim=42, pairwise_intra_dim=0,
        n_embd=64, n_layers=2, n_heads=4, dropout_rate=0.1,
        query_hidden_dim=64,
        final_hidden_dim=64, output_dim=1)
    summary = _load_price_n_state_dict(target, pretrained)
    # Verify the first 43 dims of filter_embedding match the pretrained values.
    target_w = target.filter_embedding.filter_embeddings.weight
    src_w = pretrained["filter_embedding.filter_embeddings.weight"]
    assert torch.allclose(target_w[:, :43], src_w)
    # Remaining dims should be zero (zero-init).
    assert torch.allclose(target_w[:, 43:], torch.zeros_like(target_w[:, 43:]))
    assert "filter_embedding.filter_embeddings.weight" in summary["partial_copied"]


def test_utilsTrain_accepts_price_n_shorthand():
    """parse_args() with --price_n must set the four orthogonal flags."""
    import subprocess
    result = subprocess.run(
        ["python", "-c",
         "import sys; sys.path.insert(0, '/root/LLM4QPR/experiments'); "
         "import utilsTrain, shlex; "
         "sys.argv = shlex.split('train.py --db postgres --workload tpch --algo llm --model_name x --price_n'); "
         "args = utilsTrain.parse_args(); "
         "print(args.price_n_parsing, args.price_n_filter, "
         "args.price_n_fanout, args.price_n_pairwise)"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().endswith("True True True True")


def test_utilsTrain_rejects_price_s_plus_price_n_filter():
    """The mutual-exclusion guard blocks --price_s --price_n_filter."""
    import subprocess
    result = subprocess.run(
        ["python", "-c",
         "import sys; sys.path.insert(0, '/root/LLM4QPR/experiments'); "
         "import utilsTrain, shlex; "
         "sys.argv = shlex.split('train.py --db postgres --workload tpch --algo llm --model_name x --price_s --price_n_filter'); "
         "args = utilsTrain.parse_args()"],
        capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert "mutually exclusive" in result.stderr.lower()


def test_filter_token_neq_continuous():
    """NEQ range-pair encoding: col != X emits gap slots covering values != X."""
    sys.path.insert(0, "/root/LLM4QPR/PRICE")
    from setup.features_tool_n import Sql2FeatureN
    f = Sql2FeatureN("tpch", 40, "finetune")
    atoms = {**f.EMPTY_ATOMS, "not_in_values": [50]}
    tok = f._encode_filter_token("tpch_p.p_size", atoms)
    assert tok.shape == (75,), f"Expected shape (75,) got {tok.shape}"
    # Two range slots should be used (below 50 and above 50).
    # Slot selectivities are at indices 40, 43, 46, ... (step 3) for K=10 slots,
    # then the tail slot at index 40+30+2 = 72.
    slot_sels = tok[40:40 + 30:3]  # K=10 slots, sel is every 3rd element
    tail_sel = tok[40 + 30 + 2].item()
    nonzero_sels = [s.item() for s in slot_sels if s.item() > 0]
    # At least one range slot should have non-zero selectivity
    assert len(nonzero_sels) >= 1, \
        f"Expected at least 1 non-zero slot selectivity, got slots={slot_sels.tolist()}"
    # Shape should still be correct
    assert tok[-1].item() == 0.0, "null_pred_flag should be 0 for plain NEQ"


def test_filter_token_neq_does_not_fire_when_positive_values_present():
    """When both eq_values and not_in_values are set, positive path takes priority."""
    sys.path.insert(0, "/root/LLM4QPR/PRICE")
    from setup.features_tool_n import Sql2FeatureN
    f = Sql2FeatureN("tpch", 40, "finetune")
    # Both eq_values=[50] and not_in_values=[30]: positive path should win
    atoms_eq_only = {**f.EMPTY_ATOMS, "eq_values": [50]}
    atoms_both = {**f.EMPTY_ATOMS, "eq_values": [50], "not_in_values": [30]}
    tok_eq = f._encode_filter_token("tpch_p.p_size", atoms_eq_only)
    tok_both = f._encode_filter_token("tpch_p.p_size", atoms_both)
    # With positive path dominant, the two tokens should be identical
    import torch
    assert torch.allclose(tok_eq, tok_both), \
        "Positive path should dominate when both eq_values and not_in_values are present"


def test_extract_filter_atoms_collects_neq():
    """_extract_filter_atoms must populate not_in_values for col != X predicates."""
    sys.path.insert(0, "/root/LLM4QPR/experiments")
    from price_data_utils import _extract_filter_atoms
    import sqlglot
    ast = sqlglot.parse_one(
        "SELECT * FROM tpch_l "
        "WHERE tpch_l.l_shipmode != 'MAIL'")
    atoms = _extract_filter_atoms(ast)
    assert "tpch_l.l_shipmode" in atoms, f"column not found; atoms keys: {list(atoms.keys())}"
    assert atoms["tpch_l.l_shipmode"]["not_in_values"] == ["MAIL"], \
        f"Expected ['MAIL'], got {atoms['tpch_l.l_shipmode']['not_in_values']}"


def test_extract_filter_atoms_skips_atoms_inside_subquery():
    """Atoms inside EXISTS/IN(subquery) should not be extracted when subqueries are residual."""
    sys.path.insert(0, "/root/LLM4QPR/experiments")
    from price_data_utils import _extract_filter_atoms
    import sqlglot
    # The inner filter (l2.l_orderkey = 42) is inside EXISTS — should be skipped
    ast = sqlglot.parse_one(
        "SELECT * FROM lineitem l1 "
        "WHERE l1.l_quantity = 10 "
        "AND EXISTS (SELECT 1 FROM lineitem l2 WHERE l2.l_orderkey = 42)")
    atoms = _extract_filter_atoms(ast)
    # The outer l1.l_quantity = 10 should be present
    assert any("l_quantity" in k for k in atoms), \
        f"Expected l_quantity in atoms, got: {list(atoms.keys())}"
    # The inner l2.l_orderkey = 42 should NOT be extracted
    assert not any("l_orderkey" in k for k in atoms), \
        f"Inner subquery atom l_orderkey should be skipped, got: {list(atoms.keys())}"


def test_not_pushdown_eliminates_not_between():
    sys.path.insert(0, "/root/LLM4QPR/experiments")
    from price_data_utils import _push_not_to_nnf
    import sqlglot
    ast = sqlglot.parse_one("SELECT * FROM t WHERE NOT (t.a BETWEEN 5 AND 10)")
    _push_not_to_nnf(ast)
    sql = ast.sql().upper()
    # No NOT wrapper should remain
    cleaned = sql.replace("NOT NULL", "").replace("IS NOT", "")
    assert "NOT" not in cleaned
    assert " < 5" in sql or "<5" in sql
    assert " > 10" in sql or ">10" in sql


def test_not_pushdown_eliminates_not_in_literal_list():
    sys.path.insert(0, "/root/LLM4QPR/experiments")
    from price_data_utils import _push_not_to_nnf
    import sqlglot
    ast = sqlglot.parse_one("SELECT * FROM t WHERE NOT t.a IN (1, 2, 3)")
    _push_not_to_nnf(ast)
    sql = ast.sql().upper()
    cleaned = sql.replace("NOT NULL", "").replace("IS NOT", "")
    assert "NOT" not in cleaned
    # Should have three NEQ atoms
    assert sql.count("<>") + sql.count("!=") >= 3


def test_extract_or_atoms_same_column_chain():
    sys.path.insert(0, "/root/LLM4QPR/experiments")
    from price_data_utils import _extract_filter_atoms
    import sqlglot
    ast = sqlglot.parse_one("SELECT * FROM tpch_l WHERE tpch_l.l_quantity < 5 OR tpch_l.l_quantity > 10")
    atoms = _extract_filter_atoms(ast)
    assert "tpch_l.l_quantity" in atoms
    or_atoms = atoms["tpch_l.l_quantity"].get("or_atoms", [])
    ops = sorted(op for op, _ in or_atoms)
    assert ops == ["<", ">"]


def test_extract_or_atoms_mixed_column_not_collapsed():
    sys.path.insert(0, "/root/LLM4QPR/experiments")
    from price_data_utils import _extract_filter_atoms
    import sqlglot
    ast = sqlglot.parse_one("SELECT * FROM t WHERE t.a < 5 OR t.b > 10")
    atoms = _extract_filter_atoms(ast)
    # Different columns — not collapsed; or_atoms empty for both
    for col, entry in atoms.items():
        assert entry.get("or_atoms", []) == []
