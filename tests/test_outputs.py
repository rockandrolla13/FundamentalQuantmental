"""Tests for hy.outputs (methodology Section 10)."""

import json
from datetime import datetime

import pandas as pd
import pytest

from hy import outputs as out
from hy.inputs import LookAheadError


def _frame(table, n=2):
    cols = out.TABLES[table].columns
    df = pd.DataFrame({c: [None] * n for c in cols})
    df["date"] = [datetime(2026, 10, 21)] * n
    df["available_at"] = [datetime(2026, 10, 20)] * n
    return df


@pytest.mark.parametrize("table", list(out.TABLES))
def test_valid_frame_passes(table):
    df = _frame(table)
    assert out.validate_frame(df, table) is df


def test_validate_catches_look_ahead_row():
    df = _frame("bond_daily", 3)
    df.loc[1, "available_at"] = datetime(2026, 10, 22)
    with pytest.raises(LookAheadError, match=r"\[1\]"):
        out.validate_frame(df, "bond_daily")


def test_validate_catches_missing_column():
    with pytest.raises(out.SchemaError, match="replaces_position"):
        out.validate_frame(_frame("bond_daily").drop(columns="replaces_position"), "bond_daily")


def test_section_10_names_present():
    assert {"s1", "s7", "composite", "force_rank", "replaces_position", "event_var_alpha"} <= set(out.BOND_DAILY.columns)
    assert {"p_path", "p_outcome_given_path", "features_delta"} <= set(out.EVENT_MATRIX.columns)
    assert {"jtd_by_issuer", "band_gate_scale", "cycle_phase"} <= set(out.PORTFOLIO_RISK.columns)
    for t in out.TABLES.values():
        assert {"date", "available_at"} <= set(t.columns)
        assert len(t.columns) == len(set(t.columns))


def test_write_json_schemas(tmp_path):
    paths = out.write_json_schemas(tmp_path)
    assert {p.stem for p in paths} == set(out.TABLES)
    s = json.loads((tmp_path / "issuer_state.json").read_text())
    assert s["properties"]["q_vector"]["maxItems"] == 10
    assert set(s["required"]) == set(out.ISSUER_STATE.columns)
    # The committed copies exist and match the code.
    for name in out.TABLES:
        assert json.loads((out.SCHEMA_DIR / f"{name}.json").read_text()) == out.json_schema(name)
