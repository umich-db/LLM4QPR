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
