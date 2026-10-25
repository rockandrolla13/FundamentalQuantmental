"""Plugging in another data source (docs/production_wiring.md): the source switch, the composite source, the tables
source, the panel builders and the contract check.

The main test exports the made-up world of `test_pipeline_fake_source` into tables, selects them with `HY_SOURCE`
only (no view passed in, no patch of the source), and requires the same outputs as the run on the made-up world.
"""

from __future__ import annotations

import json
import re
import sys
import types
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from hy.data import config as data_config
from hy.data import contract, factory, panels
from hy.data import records as R
from hy.data.pit import DataUnavailable
from hy.data.source import FACT_KEYS, PANEL_COLUMNS, PROTOCOLS, SOURCE_METHODS
from hy.data.sources import CompositeSource, FakeSource, PublicSource, WarehouseSource
from hy.data.tables import TableSource, make_source, write_tables
from hy.data.view import DataView

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_pipeline_fake_source as world  # noqa: E402

from test_pipeline_fake_source import DECISION, END, ISSUERS, offline  # noqa: E402,F401 - the fixture

START = datetime(2020, 1, 1)


# ------------------------------------------------------------------------------------------- the source switch


def test_source_methods_match_the_protocols():
    names = [n for p in PROTOCOLS for n, v in vars(p).items() if not n.startswith("_") and callable(v)]
    assert names == list(SOURCE_METHODS)


def test_open_source_defaults_to_the_warehouse(monkeypatch):
    monkeypatch.delenv(factory.SOURCE_ENV, raising=False)
    assert isinstance(factory.open_source(data_config.DataConfig(allow_network=False)), WarehouseSource)


def test_open_source_builds_the_named_factory(monkeypatch):
    mod = types.ModuleType("my_hy_source")
    mod.make = lambda cfg: ("made", cfg.root)
    monkeypatch.setitem(sys.modules, "my_hy_source", mod)
    monkeypatch.setenv(factory.SOURCE_ENV, "my_hy_source:make")
    cfg = data_config.DataConfig(root=Path("/somewhere"), allow_network=False)
    assert factory.open_source(cfg) == ("made", Path("/somewhere"))
    with pytest.raises(ValueError):
        factory.open_source(cfg, spec="no_colon")


# ------------------------------------------------------------------------------------------- the composite source


class _Only:
    def __init__(self, curve=None, fail=False):
        self._curve, self._fail = curve, fail

    def curve(self, on):
        if self._fail:
            raise DataUnavailable("curve", str(on), "not here")
        return self._curve


def test_composite_asks_parts_in_order_and_passes_gaps_on():
    c = R.Curve("UST", datetime(2026, 1, 2), datetime(2026, 1, 3), tenors=(1.0,), yields=(0.04,))
    assert CompositeSource(_Only(fail=True), _Only(curve=c)).curve(datetime(2026, 1, 5)) is c
    assert CompositeSource(_Only(curve=c), _Only(fail=True)).curve(datetime(2026, 1, 5)) is c
    with pytest.raises(DataUnavailable):
        CompositeSource(_Only(fail=True)).curve(datetime(2026, 1, 5))
    with pytest.raises(DataUnavailable):                       # no part serves bonds
        CompositeSource(_Only(curve=c)).bonds(R.Issuer("X"))
    with pytest.raises(AttributeError):
        CompositeSource(_Only(curve=c)).not_a_kind


def test_composite_shows_its_wiring():
    wiring = CompositeSource(_Only(), world.fake_world()).served_by()
    assert wiring["curve"] == "_Only then FakeSource" and wiring["bonds"] == "FakeSource"
    assert set(wiring) == set(SOURCE_METHODS)


def test_public_source_takes_the_hy_level_from_the_market_part():
    pub = PublicSource(data_config.DataConfig(allow_network=False), fundamentals=None, market=world.fake_world())
    rows, status = pub._hy_rows(DECISION)  # noqa: SLF001 - the forecast rows without the network loaders
    assert {r.variable for r in rows} == {"hy_spread", "distress_ratio"} and status["status"] == "live"
    assert all(r.available_at <= DECISION for r in rows)
    assert PublicSource(data_config.DataConfig(), None)._hy_rows(DECISION)[1]["status"].startswith("stubbed")  # noqa: SLF001


def test_public_facts_need_a_cik():
    from hy.data.adapters import edgar_filings
    with pytest.raises(DataUnavailable, match="CIK"):
        edgar_filings.facts_from_financials(R.Issuer("X", gvkey="1"), DECISION, data_config.DataConfig(), [])


# ------------------------------------------------------------------------------------------- the tables source


@pytest.fixture
def tables(tmp_path):
    folder = tmp_path / "tables"
    counts = write_tables(world.fake_world(), list(ISSUERS), START, datetime(2026, 9, 18), folder)
    assert counts["financials"] == 24 and counts["bonds"] == 6 and counts["panels/bond_panel"] > 0
    return folder


def test_tables_read_back_what_was_written(tables):
    fake, tab = world.fake_world(), TableSource(data_config.DataConfig(), folder=tables)
    iss = tab.issuers(["AAA"])[0]
    assert (iss.gvkey, iss.cik, iss.name) == ("900001", "9000001", "AAA Health")
    a, b = fake.financials(fake.issuers(["AAA"])[0]), tab.financials(iss)
    assert [r.as_of for r in a] == [r.as_of for r in b]
    assert [r.ebitda_adj_company for r in a] == pytest.approx([r.ebitda_adj_company for r in b])
    assert b[0].nonrecurring_items[0].amount == pytest.approx(a[0].nonrecurring_items[0].amount)
    assert tab.bonds(iss) == fake.bonds(iss)
    pd.testing.assert_frame_equal(tab.observations(tab.bonds(iss), START, DECISION),
                                  fake.observations(fake.bonds(iss), START, DECISION), check_dtype=False)
    assert tab.curve(DECISION).yields == pytest.approx(fake.curve(DECISION).yields)
    assert tab.hy_index(DECISION).spread == pytest.approx(fake.hy_index(DECISION).spread)
    assert tab.market_value(iss, DECISION).value == pytest.approx(fake.market_value(iss, DECISION).value)


def test_tables_reject_a_table_without_its_columns(tmp_path):
    (tmp_path / "t").mkdir()
    pd.DataFrame({"ticker": ["AAA"]}).to_csv(tmp_path / "t" / "issuers.csv", index=False)
    with pytest.raises(ValueError, match="issuer_id"):
        TableSource(data_config.DataConfig(), folder=tmp_path / "t").issuers(["AAA"])
    with pytest.raises(DataUnavailable):
        TableSource(data_config.DataConfig(), folder=tmp_path / "t").bonds(R.Issuer("AAA"))


def _strip(d):
    """A run's JSON without the fields that name the source or the output folder, and with the memo's source names
    ("bond observations (TableSource then FakeSource)") made one word."""
    if isinstance(d, dict):
        return {k: _strip(v) for k, v in d.items() if k not in ("out_dir", "source", "data_root")}
    if isinstance(d, list):
        return [_strip(x) for x in d]
    if isinstance(d, str):
        return re.sub(r"\(\w+Source( then \w+Source)*\)", "(source)", d)
    return d


def test_a_run_on_tables_selected_by_hy_source_equals_the_run_on_the_source(offline, tables, monkeypatch):
    import process  # scripts/ is on the path through the fake-source test module

    fake = world.fake_world()
    tab = TableSource(data_config.DataConfig(root=offline / "no_raw", allow_network=False), folder=tables)
    # The filing kinds and the forecasts stay with the made-up world (the public SEC and Fed loaders need the
    # network); the tables serve every vendor kind. The reference run reads the same financials records.
    filing_part = FakeSource(facts=[world._facts(t) for t in ISSUERS], forecasts=world._forecasts(),
                             filings=fake._filings, balance_sheets=list(fake._sheets.values()),
                             texts=list(fake._texts.values()))
    mod = types.ModuleType("hy_tables_test_source")
    mod.make = lambda cfg: CompositeSource(tab, filing_part)
    monkeypatch.setitem(sys.modules, "hy_tables_test_source", mod)

    reference = world.fake_world()
    reference._financials = [r for t in ISSUERS for r in tab.financials(tab.issuers([t])[0])]
    process.run(list(ISSUERS), END, [("AAA", "BBB")], out_dir=offline / "ref", figures=False,
                view=DataView(reference, DECISION))
    monkeypatch.setenv(factory.SOURCE_ENV, "hy_tables_test_source:make")
    steps = process.run(list(ISSUERS), END, [("AAA", "BBB")], out_dir=offline / "tab", figures=False)
    assert steps["AAA"]["9"].outputs["peers"]["n_peers"] > 0
    memo = (offline / "tab" / "AAA.json").read_text()
    assert "TRACE via WRDS" not in memo and "Compustat spiq" not in memo   # the memo names the data it read
    assert "bond observations (TableSource then FakeSource)" in memo
    files = sorted((offline / "ref").glob("*.json"))
    assert {f.name for f in files} >= {"AAA.json", "BBB.json", "_run.json"}
    for f in files:
        a, b = json.loads(f.read_text()), json.loads((offline / "tab" / f.name).read_text())
        assert _strip(a) == _strip(b), f.name


# ------------------------------------------------------------------------------------------- the panel builders


def test_bond_panel_from_records():
    fake = world.fake_world()
    iss = fake.issuers(list(ISSUERS))
    bonds = [b for i in iss for b in fake.bonds(i)]
    obs = fake.observations(bonds, START, DECISION)
    months = panels.month_ends("2026-04-30", "2026-08-31")
    p = panels.bond_panel(iss, bonds, obs, months, lambda t: fake.curve(t + pd.Timedelta(1, unit="D")).as_row())
    live = p[~p["carried"]]
    assert set(PANEL_COLUMNS["bond_panel"]) <= set(p.columns)
    assert len(live) == 6 * len(months) and set(live["gvkey"]) == {"900001", "900002"}
    r = live.iloc[0]
    curve = fake.curve(r["date"] + pd.Timedelta(1, unit="D")).as_row()
    from hy.sources import treasury as tr
    assert r["g_spread"] == pytest.approx(r["yield"] - tr.interpolate(curve, r["years"]))
    assert (live["available_at"] > live["date"] - pd.Timedelta(7, unit="D")).all()
    assert (live["available_at"] <= live["date"] + pd.Timedelta(1, unit="D")).all()


def test_bond_panel_uses_a_quoted_bid_ask():
    fake = world.fake_world()
    iss = fake.issuers(["AAA"])
    bonds = fake.bonds(iss[0])
    obs = fake.observations(bonds, START, DECISION).assign(bid_ask_pts=0.75)
    p = panels.bond_panel(iss, bonds, obs, [pd.Timestamp("2026-08-31")],
                          lambda t: fake.curve(t + pd.Timedelta(1, unit="D")).as_row())
    assert (p["bid_ask_pts"] == 0.75).all() and (p["bid_ask_source"] == "side").all()


def test_leverage_panel_from_records():
    fake = world.fake_world()
    fin = [r for i in fake.issuers(list(ISSUERS)) for r in fake.financials(i)]
    lev = panels.leverage_panel(fin, [pd.Timestamp("2026-08-31")])
    gv, rev0, m, debt = ISSUERS["AAA"][0], ISSUERS["AAA"][5], ISSUERS["AAA"][6], ISSUERS["AAA"][7]
    row = lev[lev["gvkey"] == gv].iloc[0]
    ltm = sum(rev0 * (1 + 0.01 * i) * m for i in range(8, 12))     # the four quarters public by 2026-09-01
    assert row["ltm_ebitda"] == pytest.approx(ltm) and row["leverage"] == pytest.approx(debt / ltm)
    assert set(PANEL_COLUMNS["leverage"]) <= set(lev.columns)


# ------------------------------------------------------------------------------------------- the contract check


def test_check_source_passes_the_made_up_world():
    rep = contract.check_source(world.fake_world(), list(ISSUERS), DECISION)
    assert contract.failures(rep).empty, contract.failures(rep).to_string()
    assert set(rep["kind"]) >= {"issuer", "financials", "facts", "bonds", "observations", "curve", "hy_index"}


def test_check_source_names_wrong_units_and_missing_keys():
    fake = world.fake_world()
    fake._obs = fake._obs.assign(**{"yield": fake._obs["yield"] * 100})           # percent, not decimal
    fake._facts = [R.IssuerFacts(f.key, f.as_of, f.available_at, issuer_ticker=f.issuer_ticker,
                                 values={k: v for k, v in f.values.items() if k != "ltm_ebitda"}) for f in fake._facts]
    bad = contract.failures(contract.check_source(fake, ["AAA"], DECISION))
    assert set(bad["kind"]) == {"observations", "facts"}
    assert "decimal" in bad.set_index("kind").loc["observations", "detail"]
    assert "ltm_ebitda" in bad.set_index("kind").loc["facts", "detail"]


def test_check_source_reports_look_ahead():
    fake = world.fake_world()
    f = fake._facts[0]
    late = datetime(2026, 9, 30)
    fake._facts = [R.IssuerFacts(f.key, late, late, issuer_ticker=f.issuer_ticker, values=f.values)]
    # A source that hands back a record public after the decision time is a defect the view refuses.
    fake.facts = lambda issuer, t: fake._facts[0]
    bad = contract.failures(contract.check_source(fake, ["AAA"], DECISION))
    assert "look-ahead" in bad.set_index("kind").loc["facts", "detail"]


def test_fact_keys_are_the_keys_the_made_up_world_supplies():
    assert set(FACT_KEYS) <= set(world._facts("AAA").values)


def test_a_left_out_financials_column_takes_the_warehouse_value(tmp_path):
    folder = tmp_path / "t"
    folder.mkdir()
    pd.DataFrame([{"ticker": "AAA", "issuer_id": "1"}]).to_csv(folder / "issuers.csv", index=False)
    pd.DataFrame([{"issuer_id": "1", "period_end": "2026-03-31", "available_at": "2026-05-10", "revenue": 100.0,
                   "ebitda_reported": 20.0, "ebitda_adj_company": float("nan")}]).to_csv(folder / "financials.csv",
                                                                                      index=False)
    tab = TableSource(data_config.DataConfig(), folder=folder)
    r = tab.financials(tab.issuers(["AAA"])[0])[0]
    assert (r.revolver_commitment, r.rent_expense, r.borrowing_base) == (0.0, 0.0, float("inf"))  # warehouse values
    assert np.isnan(r.capex_total) and np.isnan(r.ebitda_adj_company)  # a supplied field stays NaN when missing
    assert r.maturity_schedule == (0.0,) * 5 and r.nonrecurring_items == ()
