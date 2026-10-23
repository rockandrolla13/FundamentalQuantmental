"""The whole analyst on made-up data (review finding AR-TST-001; design: data module).

Two made-up issuers, AAA (a hospital operator, archetype A2) and BBB (a cruise line, archetype A4), with quarters,
filing facts, balance sheets, bonds, daily quotes, Treasury curves, the HY index, macro forecasts and the peer
panels, all in a `FakeSource`. `process.run` runs every step through `DataView(fake, t)` with the network blocked.
The test passes with no data/raw folder at all: any read that reaches past the view is a side door, and it fails here.
"""

from __future__ import annotations

import json
import socket
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from hy.data import config as data_config
from hy.data import records as R
from hy.data.sources import FakeSource
from hy.data.view import DataView
from hy.forecasts import ForecastRow

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import process  # noqa: E402

END = "2026-09-17"                       # last trade day; filings as known the next day
DECISION = datetime(2026, 9, 18)
TENORS = (1 / 12, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 20.0, 30.0)
DAY = timedelta(days=1)

ISSUERS = {  # ticker: gvkey, cik, name, archetype, sector, revenue per quarter, EBITDA margin, debt, bond yield
    "AAA": ("900001", "9000001", "AAA Health", "A2", "35", 5000.0, 0.15, 9000.0, 0.070),
    "BBB": ("900002", "9000002", "BBB Cruises", "A4", "25", 4000.0, 0.25, 15000.0, 0.085),
}


# ------------------------------------------------------------------------------------------- the made-up world


def _quarter_ends(n: int, last: str = "2026-06-30") -> list[datetime]:
    return [d.to_pydatetime() for d in pd.date_range(end=last, periods=n, freq="QE")]


def _financials(t: str) -> list[R.IssuerFinancials]:
    gv, _, _, _, _, rev0, m, debt, _ = ISSUERS[t]
    out = []
    for i, q in enumerate(_quarter_ends(12)):
        rev = rev0 * (1 + 0.01 * i)
        eb = rev * m
        out.append(R.IssuerFinancials(
            gv, q, q + timedelta(days=40), revenue=rev, ebitda_reported=eb * 0.97, ebitda_adj_company=eb,
            nonrecurring_items=(R.NonRecurringItem("restructuring", -0.03 * eb, False, True),),
            ebitda_covenant=eb, cash_interest=debt * 0.065 / 4, cash_taxes=0.02 * rev, capex_total=0.06 * rev,
            capex_maintenance=0.04 * rev, inventory=0.05 * rev, receivables=0.5 * rev, payables=0.3 * rev,
            cogs=0.6 * rev, cash=0.15 * rev, debt_current=0.05 * debt, debt_long_term=0.95 * debt,
            depreciation=0.05 * rev, operating_cash_flow=0.8 * eb - debt * 0.065 / 4, source="fake"))
    return out


def _facts(t: str) -> R.IssuerFacts:
    gv, cik, name, arch, _, rev0, m, debt, _ = ISSUERS[t]
    acc = datetime(2026, 8, 5, 16)
    ltm_rev = sum(rev0 * (1 + 0.01 * i) for i in range(8, 12))
    v = {"ticker": (t, "input"), "name": (name, "fake"), "cik": (cik, "fake"), "gvkey": (gv, "fake"),
         "decision_time": (str(DECISION), "input"), "q": (f"{t}-Q2", "fake 10-Q"), "k": (f"{t}-K", "fake 10-K"),
         "q_acceptance": (str(acc), "fake"), "k_acceptance": ("2026-02-20 16:00:00", "fake"),
         "balance_sheet_date": ("2026-06-30", "fake"), "ltm_ebitda": (ltm_rev * m, "fake LTM"),
         "ltm_revenue": (ltm_rev, "fake LTM"), "run_rate_revenue": (rev0 * 1.11 * 4, "fake"),
         "interest_rate": (0.065, "fake"), "annual_lease_cost": (0.02 * ltm_rev, "fake"),
         "lease_wavg_term": (8.0, "fake"), "uncommenced_window": (None, "fake"), "uncommenced_term": (None, "fake"),
         "debt_tail_years": (5.0, "default assumption"), "rpo_windows": ([], "fake"), "rpo_total": (None, "fake"),
         "rpo_tail_years": (2.0, "default assumption"), "purchase": (None, "fake"),
         "scenario_extra_lease": (None, "analyst only"), "recourse": (None, "analyst only"),
         "rating": (None, "analyst only"), "archetype": (arch, "analyst input"), "available_at": (str(acc), "fake")}
    return R.IssuerFacts(t, acc, acc, issuer_ticker=t, values=v)


def _sheet(t: str, acc: str, as_of: datetime, accepted: datetime) -> R.BalanceSheet:
    _, _, _, _, _, rev0, _, debt, _ = ISSUERS[t]
    lad = [0.05 * debt, 0.10 * debt, 0.15 * debt, 0.20 * debt, 0.20 * debt, 0.30 * debt]
    lease = [0.08 * rev0] * 5 + [0.3 * rev0]
    return R.BalanceSheet(
        acc, as_of, accepted, issuer_ticker=t, accession=acc, debt=debt, debt_source="fake tag LongTermDebt",
        operating_lease_liability=sum(lease) * 0.8, finance_lease_liability=float("nan"), cash=0.6 * rev0,
        revolver_capacity=0.3 * rev0,
        ladders={"operating_lease": R.Ladder("operating_lease", lease, 0.5, sum(lease), True),
                 "finance_lease": None, "purchase": None, "debt": R.Ladder("debt", lad, 0.5, debt, True)},
        customer_shares={})


def _text(t: str, acc: str, when: datetime) -> R.FilingText:
    name = ISSUERS[t][2]
    body = (f"Item 1. Business. Overview {name} runs a large made-up business in the United States. "
            f"It earns fees from customers under contracts. The credit agreement requires a maximum consolidated "
            f"net leverage ratio of 6.00 to 1.00.")
    return R.FilingText(acc, when, when, issuer_ticker=t, accession=acc, text=body)


def _bonds(t: str) -> list[R.Bond]:
    return [R.Bond(f"{t}00{i}", t, 0.05 + 0.005 * i, datetime(2026 + y, 6, 15), "senior_unsecured", True, False, "H")
            for i, y in enumerate((3, 5, 8), start=1)]


def _observations() -> pd.DataFrame:
    days = pd.bdate_range("2026-03-20", END)
    rows = []
    for t in ISSUERS:
        y0 = ISSUERS[t][8]
        for k, b in enumerate(_bonds(t)):
            for j, d in enumerate(days):
                y = y0 + 0.002 * k + 0.0005 * np.sin(j / 9.0)
                rows.append({"cusip": b.cusip, "date": d, "price": 100.0 - 4.0 * (y - b.coupon) / 0.01 * 0.1,
                             "yield": y, "n_trades": 3, "par_volume": 2e6, "available_at": d + DAY})
    return pd.DataFrame(rows, columns=list(R.BOND_OBS_COLUMNS))


def _curves() -> list[R.Curve]:
    out = []
    for j, d in enumerate(pd.bdate_range("2025-12-01", END)):
        lvl = 0.040 + 0.002 * np.sin(j / 40.0)
        ys = tuple(lvl + 0.003 * np.log1p(x) for x in TENORS)
        out.append(R.Curve("UST", d.to_pydatetime(), (d + DAY).to_pydatetime(), tenors=TENORS, yields=ys))
    return out


def _index_levels() -> list[R.IndexLevel]:
    days = list(pd.date_range("2021-01-31", "2026-08-31", freq="ME")) + [pd.Timestamp(END)]
    return [R.IndexLevel("HY", d.to_pydatetime(), (d + DAY).to_pydatetime(), spread=0.035 - 0.0002 * i % 0.01,
                         distress=0.05) for i, d in enumerate(days)]


def _forecasts() -> list[ForecastRow]:
    v, a = datetime(2026, 8, 15), datetime(2026, 8, 16)
    rows = []
    for h in range(9):
        for var, mid in (("gdp_growth", 0.019), ("cpi", 0.026), ("unemployment", 0.045)):
            rows.append(ForecastRow("spf", var, h, v, a, mid))
            rows.append(ForecastRow("spf_prob", var, h, v, a, mid, q10=mid - 0.012, q50=mid, q90=mid + 0.012,
                                    method="survey_quantiles"))
        rows.append(ForecastRow("fomc_sep", "policy_rate", h, v, a, 0.0375 - 0.001 * h))
        rows.append(ForecastRow("ust_forward", "policy_rate", h, v, a, 0.037, method="market_implied"))
        rows.append(ForecastRow("ust_forward", "y2", h, v, a, 0.036 + 0.0005 * h, method="market_implied"))
        rows.append(ForecastRow("ust_forward", "y10", h, v, a, 0.042 + 0.0004 * h, method="market_implied"))
    for i, rel in enumerate((datetime(2026, 2, 2), datetime(2026, 5, 4), datetime(2026, 8, 3))):
        rows.append(ForecastRow("sloos", "sloos_tightening", 0, rel - timedelta(days=30), rel, 0.05 * i))
    rows.append(ForecastRow("trace_hy_benchmark", "hy_spread", 0, datetime(2026, 9, 17), DECISION, 0.033,
                            method="market_implied"))
    rows.append(ForecastRow("trace_hy_benchmark", "distress_ratio", 0, datetime(2026, 9, 17), DECISION, 0.05,
                            method="market_implied"))
    return rows


def _panels() -> dict[str, pd.DataFrame]:
    """Peer panels: 160 made-up issuers over 12 month ends, plus the two live issuers' own leverage rows."""
    rng = np.random.default_rng(20261023)
    months = pd.date_range(end="2026-08-31", periods=12, freq="ME")
    peers = [f"8{i:05d}" for i in range(160)]
    lev0 = dict(zip(peers, np.exp(rng.normal(np.log(4.0), 0.5, len(peers)))))
    sector = {g: ("35" if i % 2 else "25") for i, g in enumerate(peers)}
    lev, bonds, rat, eq = [], [], [], []
    for m in months:
        for g in peers:
            lv = lev0[g] * float(np.exp(rng.normal(0, 0.03)))
            lev.append({"date": m, "gvkey": g, "ltm_ebitda": 500.0, "debt": 500.0 * lv, "leverage": lv,
                        "available_at": m + DAY})
            cls = "BBB-" if lv < 2.5 else "BB" if lv < 3.8 else "B" if lv < 5.5 else "CCC+"
            rat.append({"gvkey": g, "datadate": m, "splticrm": cls, "available_at": m + DAY})
            eq.append({"gvkey": g, "datadate": m, "ret": float(rng.normal(0.005, 0.05)), "available_at": m + DAY})
            for k, yrs in enumerate((3.0, 6.0)):
                bonds.append({"date": m, "cusip": f"{g}{k}", "gvkey": g, "years": yrs,
                              "g_spread": 0.006 * lv * float(np.exp(rng.normal(0, 0.15))), "available_at": m + DAY})
        for t, (gv, *_rest) in ISSUERS.items():
            debt, rev0, mg = ISSUERS[t][7], ISSUERS[t][5], ISSUERS[t][6]
            lev.append({"date": m, "gvkey": gv, "ltm_ebitda": 4 * rev0 * mg, "debt": debt,
                        "leverage": debt / (4 * rev0 * mg), "available_at": m + DAY})
    gics = pd.DataFrame([{"gvkey": g, "gsector": s, "indfrom": pd.Timestamp("2000-01-31"), "indthru": pd.NaT,
                          "available_at": pd.Timestamp("2000-01-31")} for g, s in
                         list(sector.items()) + [(v[0], v[4]) for v in ISSUERS.values()]])
    annual = pd.DataFrame([{"gvkey": g, "datadate": pd.Timestamp(f"{y}-12-31"), "fyear": float(y), "oibdp": 2000.0,
                            "debt": 2000.0 * lev0[g], "available_at": pd.Timestamp(f"{y + 1}-03-01")}
                           for g in peers for y in range(2015, 2026)])
    return {"bond_panel": pd.DataFrame(bonds), "leverage": pd.DataFrame(lev), "gics": gics,
            "ratings": pd.DataFrame(rat), "annual_ebitda": annual, "equity_monthly": pd.DataFrame(eq)}


def fake_world() -> FakeSource:
    issuers, fin, facts, sheets, texts, filings, mvs = [], [], [], [], [], [], []
    for t, (gv, cik, name, *_rest) in ISSUERS.items():
        issuers.append(R.Issuer(t, gvkey=gv, cik=cik, name=name))
        fin += _financials(t)
        facts.append(_facts(t))
        q_acc, k_acc = datetime(2026, 8, 5, 16), datetime(2026, 2, 20, 16)
        sheets += [_sheet(t, f"{t}-Q2", datetime(2026, 6, 30), q_acc), _sheet(t, f"{t}-K", datetime(2025, 12, 31), k_acc)]
        texts += [_text(t, f"{t}-Q2", q_acc), _text(t, f"{t}-K", k_acc)]
        filings += [R.Filing(f"{t}-Q2", q_acc, q_acc, issuer_ticker=t, form="10-Q", accession=f"{t}-Q2"),
                    R.Filing(f"{t}-K", k_acc, k_acc, issuer_ticker=t, form="10-K", accession=f"{t}-K")]
        mvs.append(R.MarketValue(t, datetime(2026, 6, 30), q_acc, issuer_ticker=t, value=0.8 * ISSUERS[t][7],
                                 source="fake price x shares"))
    return FakeSource(issuers=issuers, financials=fin, facts=facts, filings=filings,
                      bonds=[b for t in ISSUERS for b in _bonds(t)], observations=_observations(), curves=_curves(),
                      index_levels=_index_levels(), forecasts=_forecasts(), panels=_panels(), market_values=mvs,
                      balance_sheets=sheets, texts=texts)


# ------------------------------------------------------------------------------------------- the test


@pytest.fixture
def offline(monkeypatch, tmp_path):
    """No network and no warehouse: sockets refuse to connect, WRDS refuses to open, derived artefacts are absent."""
    def refuse(*_a, **_k):
        raise OSError("network blocked in the fake-source test")
    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(data_config, "CONFIG", data_config.DataConfig(root=tmp_path / "no_raw", allow_network=False))
    monkeypatch.setattr(data_config, "_open_wrds", refuse)
    monkeypatch.setattr(process, "BACKTEST", tmp_path / "no_raw" / "backtest")
    return tmp_path


def test_every_step_runs_on_made_up_data(offline):
    out = offline / "process"
    steps = process.run(list(ISSUERS), END, [("AAA", "BBB")], out_dir=out, figures=False,
                        view=DataView(fake_world(), DECISION))
    expected = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "9b", "10", "11", "12", "13", "14", "14b", "15"]
    assert set(steps) == set(ISSUERS)
    for t, st in steps.items():
        assert sorted(st, key=expected.index) == expected, t
        for k, s in st.items():
            assert s.status in ("done", "partial", "blocked"), (t, k)
            if k not in ("9b",):
                assert s.outputs, (t, k, s.open_questions)
        assert st["9"].outputs["peers"]["n_peers"] > 0          # the peer step used the fake panels
        assert st["5"].outputs["covenants"]                       # the covenant level came from the fake text
        assert st["2"].outputs["sells"].startswith(ISSUERS[t][2])  # the business line too
        assert st["8"].outputs["market_cap_bn"] == pytest.approx(0.8 * ISSUERS[t][7] / 1e3, abs=0.05)
    assert steps["AAA"]["9b"].outputs["pairs"][0]["b"] == "BBB"
    for t in ISSUERS:
        dump = json.loads((out / f"{t}.json").read_text())
        assert dump["ticker"] == t and dump["macro"]["decision"] == "2026-09-18"
        assert {r["source"] for r in dump["macro"]["forecast_sources"]} >= {"spf", "ust_forward"}
    run = json.loads((out / "_run.json").read_text())
    assert run["tickers"] == list(ISSUERS) and run["macro"]["s_index_now"] == pytest.approx(0.035 - 0.0002 * 68 % 0.01)


def test_an_issuer_without_financials_is_blocked_not_fatal(offline):
    # One issuer has no quarters at all (a new filer, or a gap in the work machine's data). The run must finish for
    # the others and mark that issuer's later steps as blocked with the reason, not stop with an IndexError.
    world = fake_world()
    gone = ISSUERS["BBB"][0]
    world._financials = [r for r in world._financials if r.key != gone]
    steps = process.run(list(ISSUERS), END, [("AAA", "BBB")], out_dir=offline / "process", figures=False,
                        view=DataView(world, DECISION))
    assert set(steps) == set(ISSUERS)
    assert steps["AAA"]["15"].outputs                        # the others still run to the end
    b = steps["BBB"]
    blocked = [k for k, s in b.items() if s.status == "blocked"]
    assert blocked, "the issuer without financials must show blocked steps"
    assert any("financial" in q.lower() for k in blocked for q in b[k].open_questions)
