"""The TRACE master version in force at a date (Sections 3.1, 11; `trace_bonds.master_in_force_sql`).

TRACE keeps a stale first version open after a correction replaces it. Apple 037833AJ9 reads grade H from 2013-04-30
to 2018-06-21 and grade I from 2013-05-01 to 2018-05-07. The rule must read Apple as I while the correction is open.
The SQL runs on DuckDB here, so the test checks the same text that WRDS runs.
"""

import pandas as pd
import pytest

from hy.sources import trace_bonds as tb
from hy.sources import trace_panel as tp


def _master():
    rows = [
        # stale first version outlives its correction (Apple 037833AJ9, as in the master file)
        ("037833AJ9", "H", "2013-04-30", "2018-06-21"),
        ("037833AJ9", "I", "2013-05-01", "2018-05-07"),
        # ordinary successor: the old version ends the day before the new one starts
        ("21873SAB4", "I", "2025-05-21", "2025-05-21"),
        ("21873SAB4", "H", "2025-05-22", "2026-09-17"),
        # a version that starts after the date is not yet known
        ("999999AA1", "H", "2015-01-01", "2026-09-17"),
        ("999999AA1", "I", "2015-07-15", "2026-09-17"),
    ]
    df = pd.DataFrame(rows, columns=["cusip_id", "grade", "stdt", "enddt"])
    df["stdt"] = pd.to_datetime(df["stdt"]).dt.date
    df["enddt"] = pd.to_datetime(df["enddt"]).dt.date
    return df


def _run_sql(ss, es):
    duckdb = pytest.importorskip("duckdb")
    con = duckdb.connect()
    con.execute("create schema trace")
    con.register("m", _master())
    con.execute("create table trace.camasterfile as select * from m")
    sql = tb.master_in_force_sql(["cusip_id", "grade"], ss, es)
    return con.execute(sql).df().set_index("cusip_id")["grade"].to_dict()


@pytest.mark.parametrize("pick", ["sql", "python"])
def test_correction_wins_over_stale_first_version(pick):
    ss, es = "2015-06-24", "2015-06-30"
    got = _run_sql(ss, es) if pick == "sql" else tb.master_in_force(_master(), ss, es).set_index("cusip_id")["grade"].to_dict()
    assert got["037833AJ9"] == "I"
    assert got["999999AA1"] == "H"          # the 2015-07-15 version did not exist yet
    assert "21873SAB4" not in got           # no version had started


@pytest.mark.parametrize("pick", ["sql", "python"])
def test_superseded_version_does_not_come_back_after_its_successor_ends(pick):
    ss, es = "2018-05-25", "2018-05-31"
    got = _run_sql(ss, es) if pick == "sql" else tb.master_in_force(_master(), ss, es).set_index("cusip_id")["grade"].to_dict()
    assert "037833AJ9" not in got


@pytest.mark.parametrize("pick", ["sql", "python"])
def test_ordinary_successor(pick):
    ss, es = "2025-06-24", "2025-06-30"
    got = _run_sql(ss, es) if pick == "sql" else tb.master_in_force(_master(), ss, es).set_index("cusip_id")["grade"].to_dict()
    assert got["21873SAB4"] == "H"


def test_current_version_takes_the_latest_correction():
    cur = tb.current_version(_master()).set_index("cusip_id")["grade"]
    assert cur["037833AJ9"] == "I"
    assert cur["21873SAB4"] == "H"
    assert cur["999999AA1"] == "I"


def test_month_sql_and_hy_benchmark_use_the_in_force_rule():
    sql = tp.month_sql("2015-06-30")
    assert "lead(stdt)" in sql and "enddt desc, stdt desc" not in sql


def test_month_cache_name_carries_the_rule_tag(tmp_path):
    # a month pulled under the old rule must not be served
    assert tb.MASTER_RULE in tp.month_cache_path(tmp_path, "2015-06-30").name
