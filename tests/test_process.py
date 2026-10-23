"""Tests for scripts/process.py helpers that the walk-forward depends on."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import process  # noqa: E402


def test_ltm_ready_is_false_without_four_consecutive_quarters():
    # OPI at 2024-06-30: 43 quarters on file but no four consecutive ones, so ltm_figures returns no ebitda_adj.
    # The old guard `x == x` read None == None as True and step 3 raised KeyError: 'ebitda_rep_q'.
    ltm = process.ltm_figures([])
    assert "ebitda_adj" not in ltm
    assert not process.ltm_ready(ltm)
    assert not process.ltm_ready({"ebitda_adj": float("nan")})
    assert process.ltm_ready({"ebitda_adj": 120.0})
