"""F19 owner cash flow to debt: contract, no look-ahead, sign, growth capex, annual fallback, edges, helpers.

Synthetic universe: one sector of six firms. Each firm has steady quarterly CFO c, capex 20 per quarter and debt 1000.
The firm's CFO rises with its index, so OCF / debt and the score must rise with it.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from hy.backtest import decision_time
from hy.factors import f19_owner_cash_flow as f19

AS_OF = pd.Timestamp("2024-03-31")
DT = decision_time(AS_OF)
QUARTERS = pd.date_range(end="2023-12-31", periods=12, freq="QE")
FIRMS = [f"g{i}" for i in range(6)]


def _firm(g: str, cfo_q: float, capx=None, quarters=QUARTERS, **extra) -> pd.DataFrame:
    """Twelve quarters, oldest first (USD millions). Interest 10 per quarter, no acquisitions, debt 1000."""
    n = len(quarters)
    capx = np.full(n, 20.0) if capx is None else np.asarray(capx, float)
    df = pd.DataFrame({"gvkey": g, "datadate": quarters, "available_at": quarters + pd.Timedelta(45, unit="D"),
                       "dlcq": 100.0, "dlttq": 900.0, "oancf": cfo_q, "capx": capx, "intpn": 10.0,
                       "xintq": 12.0, "aqc": 0.0, "dpq": 15.0})
    for k, v in extra.items():
        df[k] = v
    return df


def _gics(sectors: dict[str, str]) -> pd.DataFrame:
    return pd.DataFrame([{"gvkey": g, "gsector": s, "indfrom": pd.Timestamp("1990-01-01"), "indthru": pd.NaT,
                          "available_at": pd.Timestamp("1990-01-02")} for g, s in sectors.items()])


def _bonds(gvkeys, per: int = 2) -> pd.DataFrame:
    return pd.DataFrame([{"date": AS_OF, "cusip": f"{g}c{k}", "gvkey": g, "years": 5.0, "g_spread": 0.04,
                          "price": 95.0, "yield": 0.08, "mod_dur": 4.0, "carried": False, "available_at": DT}
                         for g in gvkeys for k in range(per)])


def _panels(cq=None, sectors=None) -> dict[str, pd.DataFrame]:
    cq = cq if cq is not None else pd.concat([_firm(g, 30.0 + 10.0 * i) for i, g in enumerate(FIRMS)],
                                             ignore_index=True)
    keys = sorted(cq["gvkey"].unique())
    return {"compustat_quarterly": cq, "gics": _gics(sectors or {g: "20" for g in keys}), "bond_panel": _bonds(keys)}


def _issuer(out: pd.DataFrame) -> pd.DataFrame:
    return out.drop_duplicates("gvkey").set_index("gvkey")


# ---------------------------------------------------------------- contract


def test_meta_and_columns():
    for k in ("rank", "name", "level", "horizon_months", "needs", "spec", "section"):
        assert k in f19.META
    assert f19.META["rank"] == 19 and f19.META["spec"] == "docs/factors/F19-owner-cash-flow.md"
    out = f19.compute(_panels(), AS_OF)
    assert list(out.columns) == f19.BOND_COLS
    assert out["cusip"].is_unique and len(out) == 12
    assert (out["date"] == AS_OF).all() and (out["available_at"] == DT).all()
    assert out["score"].notna().all() and out.groupby("gvkey")["score"].nunique().eq(1).all()
    assert (out["fin_source"] == "quarterly").all()


@pytest.mark.parametrize("drop", [["bond_panel"], ["gics"], ["compustat_quarterly"]])
def test_missing_panel_gives_empty_frame(drop):
    p = {k: v for k, v in _panels().items() if k not in drop}
    out = f19.compute(p, AS_OF)
    assert out.empty and list(out.columns) == f19.BOND_COLS


# ---------------------------------------------------------------- no look-ahead


def test_no_lookahead():
    base = f19.compute(_panels(), AS_OF)
    p = _panels()
    cq = p["compustat_quarterly"]
    newq = _firm("g0", 999.0, quarters=pd.DatetimeIndex([pd.Timestamp("2024-03-31")]))   # filed after DT
    restate = cq[cq["gvkey"] == "g5"].assign(oancf=-500.0, available_at=DT + pd.Timedelta(1, unit="D"))
    p["compustat_quarterly"] = pd.concat([cq, newq, restate], ignore_index=True)
    late_bond = _bonds(["g0"]).assign(cusip="late", available_at=DT + pd.Timedelta(1, unit="D"))
    p["bond_panel"] = pd.concat([p["bond_panel"], late_bond], ignore_index=True)
    out = f19.compute(p, AS_OF)
    pd.testing.assert_frame_equal(out, base)


# ---------------------------------------------------------------- sign and economics


def test_sign_higher_cash_flow_scores_higher():
    s = _issuer(f19.compute(_panels(), AS_OF))
    assert s.loc[FIRMS, "score"].is_monotonic_increasing
    assert s.loc[FIRMS, "ocf_debt"].is_monotonic_increasing
    assert s["score"].max() == pytest.approx(0.5) and s["score"].min() > -0.5


def test_growth_capex_spike_is_not_charged():
    """Capex 20 per quarter for two years, then 50: plain FCF falls by 120, OCF only by the rise in the 3-year mean."""
    capx = np.r_[[20.0] * 8, [50.0] * 4]
    cq = pd.concat([_firm("spike", 50.0, capx=capx)] + [_firm(g, 50.0) for g in FIRMS[:5]], ignore_index=True)
    s = _issuer(f19.compute(_panels(cq), AS_OF))
    mean3 = (200.0 + 80.0 + 80.0) / 3.0
    assert s.at["spike", "maint_capex"] == pytest.approx(mean3)
    assert s.at["spike", "growth_capex"] == pytest.approx(200.0 - mean3)
    assert s.at["spike", "fcf_debt"] == pytest.approx((200.0 - 200.0) / 1000.0)
    assert s.at["spike", "ocf_debt"] == pytest.approx((200.0 + 40.0 - mean3) / 1000.0)
    assert s.at["spike", "ocf_debt"] < s.at["g0", "ocf_debt"]


def test_capex_cut_is_capped_at_current():
    capx = np.r_[[50.0] * 8, [20.0] * 4]
    cq = pd.concat([_firm("cut", 50.0, capx=capx)] + [_firm(g, 50.0) for g in FIRMS[:5]], ignore_index=True)
    s = _issuer(f19.compute(_panels(cq), AS_OF))
    assert s.at["cut", "maint_capex"] == pytest.approx(80.0) and s.at["cut", "growth_capex"] == pytest.approx(0.0)


def test_rank_is_within_sector():
    """Two sectors with different cash flow levels: the best firm of each sector scores the same."""
    cq = pd.concat([_firm(f"a{i}", 30.0 + 10.0 * i) for i in range(5)]
                   + [_firm(f"b{i}", 300.0 + 10.0 * i) for i in range(5)], ignore_index=True)
    sectors = {**{f"a{i}": "20" for i in range(5)}, **{f"b{i}": "45" for i in range(5)}}
    s = _issuer(f19.compute(_panels(cq, sectors), AS_OF))
    assert s.at["a4", "score"] == pytest.approx(s.at["b4", "score"])
    assert s.at["a0", "score"] == pytest.approx(s.at["b0", "score"])


# ---------------------------------------------------------------- options


def test_interest_and_maint_options():
    p = _panels()
    base = _issuer(f19.compute(p, AS_OF))
    lev = _issuer(f19.compute(p, AS_OF, interest=False))
    dp = _issuer(f19.compute(p, AS_OF, maint="dp"))
    assert (base["owner_cf"] - lev["owner_cf"]).to_numpy() == pytest.approx(np.full(6, 40.0))
    assert (dp["maint_capex"] == 60.0).all()
    with pytest.raises(ValueError):
        f19.compute(p, AS_OF, maint="sales")


def test_interest_falls_back_to_expense():
    p = _panels()
    p["compustat_quarterly"] = p["compustat_quarterly"].assign(intpn=np.nan)
    assert (_issuer(f19.compute(p, AS_OF))["interest"] == 48.0).all()


def test_acquisitions_follow_the_min_rule_and_missing_counts_as_zero():
    aqc = np.r_[[0.0] * 8, [30.0, 0.0, 0.0, 0.0]]
    cq = pd.concat([_firm("deal", 50.0, aqc=aqc), _firm("none", 50.0).drop(columns="aqc")]
                   + [_firm(g, 50.0) for g in FIRMS[:4]], ignore_index=True)
    s = _issuer(f19.compute(_panels(cq), AS_OF))
    assert s.at["deal", "maint_acq"] == pytest.approx(10.0)
    assert s.at["none", "maint_acq"] == pytest.approx(0.0)


# ---------------------------------------------------------------- edge cases


def test_short_gap_stale_history_gives_nan():
    short = _firm("short", 50.0, quarters=QUARTERS[1:])                       # 11 quarters
    gap = _firm("gap", 50.0)
    gap = gap[gap["datadate"] != QUARTERS[5]]
    gap = pd.concat([gap, _firm("gap", 50.0, quarters=pd.DatetimeIndex([QUARTERS[0] - pd.offsets.QuarterEnd(1)]))])
    stale = _firm("stale", 50.0, quarters=QUARTERS - pd.offsets.QuarterEnd(4))
    cq = pd.concat([short, gap, stale] + [_firm(g, 30.0 + i) for i, g in enumerate(FIRMS)], ignore_index=True)
    s = _issuer(f19.compute(_panels(cq), AS_OF))
    assert s.loc[["short", "gap", "stale"], "score"].isna().all()
    assert s.loc[FIRMS, "score"].notna().all()


def test_zero_debt_financial_and_small_sector_give_nan():
    cq = pd.concat([_firm("nodebt", 50.0, dlcq=0.0, dlttq=0.0), _firm("bank", 50.0)]
                   + [_firm(g, 30.0 + i) for i, g in enumerate(FIRMS)]
                   + [_firm(f"t{i}", 40.0) for i in range(4)], ignore_index=True)
    sectors = {"nodebt": "20", "bank": "40", **{g: "20" for g in FIRMS}, **{f"t{i}": "45" for i in range(4)}}
    s = _issuer(f19.compute(_panels(cq, sectors), AS_OF))
    assert s.loc[["nodebt", "bank", "t0", "t3"], "score"].isna().all()
    assert np.isnan(s.at["nodebt", "ocf_debt"]) and np.isfinite(s.at["bank", "ocf_debt"])
    assert s.loc[FIRMS, "score"].notna().all()


def test_bond_without_fundamentals_gets_nan_row():
    p = _panels()
    p["bond_panel"] = pd.concat([p["bond_panel"], _bonds(["orphan"], per=1)], ignore_index=True)
    out = f19.compute(p, AS_OF)
    assert len(out) == 13 and np.isnan(out.loc[out["gvkey"] == "orphan", "score"]).all()


# ---------------------------------------------------------------- annual fallback


def _annual(g: str, cfo: float, capx=(80.0, 80.0, 80.0), years=(2020, 2021, 2022)) -> pd.DataFrame:
    rows = []
    for fy, cx in zip(years, capx):
        d = pd.Timestamp(f"{fy}-12-31")
        rows.append({"gvkey": g, "datadate": d, "fyear": fy, "oancf": cfo, "capx": cx, "aqc": np.nan,
                     "intpn": 40.0, "xint": 45.0, "dp": 60.0, "dlc": 100.0, "dltt": 900.0,
                     "available_at": d + pd.Timedelta(90, unit="D")})
    return pd.DataFrame(rows)


def test_annual_fallback_and_quarterly_precedence():
    p = _panels()
    ann = pd.concat([_annual("ann", 500.0, capx=(60.0, 90.0, 120.0)), _annual("g0", 9999.0)], ignore_index=True)
    p["compustat_annual"] = ann
    p["gics"] = _gics({**{g: "20" for g in FIRMS}, "ann": "20"})
    p["bond_panel"] = _bonds(FIRMS + ["ann"])
    s = _issuer(f19.compute(p, AS_OF))
    assert s.at["ann", "fin_source"] == "annual" and s.at["g0", "fin_source"] == "quarterly"
    assert s.at["ann", "maint_capex"] == pytest.approx(90.0)
    assert s.at["ann", "ocf_debt"] == pytest.approx((500.0 + 40.0 - 90.0 - 0.0) / 1000.0)
    assert s.at["ann", "score"] == pytest.approx(0.5)
    only_annual = {k: v for k, v in p.items() if k != "compustat_quarterly"}
    alone = _issuer(f19.compute(only_annual, AS_OF))
    assert alone["score"].isna().all()                        # two scored issuers: the sector is below MIN_SECTOR
    assert alone.loc[["ann", "g0"], "fin_source"].eq("annual").all() and alone.loc[FIRMS[1:], "ocf_debt"].isna().all()


def test_annual_needs_two_prior_years():
    p = _panels()
    p["compustat_annual"] = _annual("ann", 500.0, capx=(80.0, 80.0), years=(2021, 2022))
    p["gics"] = _gics({**{g: "20" for g in FIRMS}, "ann": "20"})
    p["bond_panel"] = _bonds(FIRMS + ["ann"])
    s = _issuer(f19.compute(p, AS_OF))
    assert np.isnan(s.at["ann", "score"]) and np.isnan(s.at["ann", "maint_capex"])


# ---------------------------------------------------------------- helpers


def test_maintenance_hand_numbers():
    cur, l1, l2 = pd.Series([120.0, 30.0, 50.0]), pd.Series([60.0, 60.0, np.nan]), pd.Series([30.0, 90.0, 50.0])
    got = f19.maintenance(cur, l1, l2)
    assert got.iloc[0] == pytest.approx(70.0)      # spike: mean 70 below current 120
    assert got.iloc[1] == pytest.approx(30.0)      # cut: capped at current 30 (p. 13)
    assert np.isnan(got.iloc[2])


def test_owner_cash_flow_to_debt_and_sector_score():
    ocf = f19.owner_cash_flow(pd.Series([200.0]), pd.Series([40.0]), pd.Series([70.0]), pd.Series([10.0]))
    assert ocf.iloc[0] == pytest.approx(160.0)
    x = f19.to_debt(pd.Series([160.0, 10.0, 10.0]), pd.Series([800.0, 0.0, -5.0]))
    assert x.iloc[0] == pytest.approx(0.2) and x.iloc[1:].isna().all()
    sc = f19.sector_score(pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, 9.0]), pd.Series(["20"] * 5 + ["45"]))
    assert sc.iloc[:5].to_numpy() == pytest.approx([-0.3, -0.1, 0.1, 0.3, 0.5])
    assert np.isnan(sc.iloc[5])
