"""F08 LEVER event-risk score and corner trade: contract, no look-ahead, sign, edge cases, helper arithmetic.

Synthetic universe: one latent attractiveness a in [0, 1] per firm drives all seven inputs in the LBO-friendly
direction (high B/M, low EV/EBITDA, high FCF yield, low capex growth, low FCF variability, high cash, small size).
The Firm LEVER-Score must then rise with a.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from hy.factors import f08_lever_event_risk as f8

AS_OF = pd.Timestamp("2024-03-31")
N_FIRMS = 40
QUARTERS = pd.date_range(end="2023-12-31", periods=8, freq="QE")
DEBT = 500.0


def _firm_quarters(g: str, a: float, quarters=QUARTERS) -> pd.DataFrame:
    """Eight quarters for one firm with attractiveness a (USD millions)."""
    mkcap = 1000.0 * (2.0 - a)
    cash = (0.02 + 0.2 * a) * mkcap
    ev = mkcap + DEBT - cash
    ebitda_q = ev / (14.0 - 8.0 * a) / 4.0
    fcf_mean = (0.02 + 0.1 * a) * mkcap / 4.0
    amp = (0.3 - 0.25 * a) * DEBT / np.sqrt(8.0 / 7.0)
    fcf = fcf_mean + amp * np.array([1, -1] * 4, float)
    capx = np.r_[[50.0] * 4, [50.0 * (1.3 - 0.5 * a)] * 4]
    n = len(quarters)
    return pd.DataFrame({
        "gvkey": g, "datadate": quarters, "available_at": quarters + pd.Timedelta(45, unit="D"),
        "ceqq": (0.2 + 0.8 * a) * mkcap, "prccq": mkcap / 100.0, "cshoq": 100.0, "cheq": cash,
        "dlcq": 100.0, "dlttq": DEBT - 100.0, "oibdpq": ebitda_q, "oancf": (fcf + capx)[-n:], "capx": capx[-n:]})


def _panels(n: int = N_FIRMS) -> tuple[dict[str, pd.DataFrame], pd.Series]:
    rng = np.random.default_rng(0)
    a = pd.Series(np.linspace(0.0, 1.0, n), index=[f"g{i:02d}" for i in range(n)])
    cq = pd.concat([_firm_quarters(g, v) for g, v in a.items()], ignore_index=True)
    gics = pd.DataFrame({"gvkey": a.index, "gsector": ["20" if i % 2 else "25" for i in range(n)],
                         "indfrom": pd.Timestamp("1990-01-01"), "indthru": pd.NaT,
                         "available_at": pd.Timestamp("1990-01-02")})
    bp = pd.DataFrame({
        "date": AS_OF, "cusip": [f"C{i:02d}" for i in range(n)], "gvkey": a.index, "years": 5.0,
        "g_spread": rng.uniform(0.02, 0.06, n), "available_at": AS_OF + pd.Timedelta(1, unit="D"),
        "price": 95.0, "yield": 0.08, "mod_dur": 4.0, "carried": False})
    return {"bond_panel": bp, "compustat_quarterly": cq, "gics": gics}, a


# ---------------------------------------------------------------- contract


def test_meta_keys():
    assert set(f8.META) == {"rank", "name", "level", "horizon_months", "needs", "spec", "section"}
    assert f8.META["rank"] == 8 and f8.META["level"] == "bond" and f8.META["horizon_months"] == 3
    assert "compustat_quarterly" in f8.META["needs"]


def test_compute_contract():
    panels, _ = _panels()
    out = f8.compute(panels, AS_OF)
    assert list(out.columns) == f8.OUT_COLS
    assert out["cusip"].is_unique and len(out) == N_FIRMS
    assert (out["date"] == AS_OF).all()
    assert (out["available_at"] <= f8.decision_time(AS_OF)).all()
    assert out["score"].notna().all() and out["lever"].between(0, 10).all()


# ---------------------------------------------------------------- no look-ahead


def test_no_lookahead():
    panels, a = _panels()
    base = f8.compute(panels, AS_OF)
    late = dict(panels)
    dt = f8.decision_time(AS_OF)
    # A new quarter and a restatement, both public after the decision time, with absurd values.
    newq = _firm_quarters("g00", 1.0, pd.DatetimeIndex(["2024-03-31"])).assign(available_at=dt + pd.Timedelta(1, "D"))
    restate = panels["compustat_quarterly"].iloc[:8].assign(ceqq=1e6, available_at=dt + pd.Timedelta(2, "D"))
    late["compustat_quarterly"] = pd.concat([panels["compustat_quarterly"], newq, restate], ignore_index=True)
    future = panels["bond_panel"].assign(date=pd.Timestamp("2024-04-30"), g_spread=0.5,
                                         available_at=pd.Timestamp("2024-05-01"))
    late_bp = panels["bond_panel"].iloc[:5].assign(g_spread=0.09, available_at=dt + pd.Timedelta(1, "D"))
    late["bond_panel"] = pd.concat([panels["bond_panel"], future, late_bp], ignore_index=True)
    late["macro_lever"] = pd.DataFrame({"date": [AS_OF], "macro_lever": [9.0], "available_at": [dt + pd.Timedelta(1, "D")]})
    pd.testing.assert_frame_equal(base, f8.compute(late, AS_OF))


# ---------------------------------------------------------------- sign


def test_lever_rises_with_attractiveness():
    panels, a = _panels()
    out = f8.compute(panels, AS_OF).set_index("gvkey")
    rho = stats.spearmanr(out["lever"], a.reindex(out.index)).statistic
    assert rho > 0.95
    assert out.loc["g39", "lever"] > 7.5 and out.loc["g00", "lever"] < 2.5   # 2007 p. 32: above 7.5 is high risk


def test_corner_sign_low_lever_wide_is_long():
    panels, a = _panels()
    bp = panels["bond_panel"].copy()
    # Within each LEVER tail (8 bonds each), give the safest firms the widest spreads.
    bp["g_spread"] = 0.02 + 0.03 * (1.0 - a.reindex(bp["gvkey"]).to_numpy())
    panels["bond_panel"] = bp
    out = f8.compute(panels, AS_OF).set_index("gvkey")
    assert out.loc["g00", "corner"] == "LH" and out.loc["g00", "score"] == 1.0     # low LEVER, wide: core long
    assert out.loc["g39", "corner"] == "HL" and out.loc["g39", "score"] == -1.0    # high LEVER, tight: core short
    assert (out.loc[out["lever_grp"] == "M", "score"] == 0.0).all()


# ---------------------------------------------------------------- edge cases


@pytest.mark.parametrize("missing", ["compustat_quarterly", "gics", "bond_panel"])
def test_missing_panel_gives_empty_frame(missing):
    panels, _ = _panels()
    del panels[missing]
    out = f8.compute(panels, AS_OF)
    assert out.empty and list(out.columns) == f8.OUT_COLS


def test_put_bond_short_history_and_financial_get_nan():
    panels, _ = _panels()
    cq = panels["compustat_quarterly"]
    panels["compustat_quarterly"] = cq[~((cq["gvkey"] == "g05") & (cq["datadate"] == QUARTERS[0]))]  # 7 quarters
    gics = panels["gics"].copy()
    gics.loc[gics["gvkey"] == "g06", "gsector"] = "40"                                            # financial
    panels["gics"] = gics
    panels["bond_terms"] = pd.DataFrame({"cusip": ["C07", "C08"], "coc_put_price": [101.0, np.nan],
                                         "available_at": pd.Timestamp("2020-01-01")})
    out = f8.compute(panels, AS_OF).set_index("gvkey")
    assert out.loc[["g05", "g06", "g07"], "score"].isna().all()
    assert out.loc[["g05", "g06"], "lever"].isna().all()
    assert out.loc["g08", "score"] == out.loc["g08", "score"]                      # no put: still scored


def test_stale_and_gapped_quarters_drop_out():
    q = _firm_quarters("gx", 0.5)
    dt = f8.decision_time(AS_OF)
    assert "gx" in f8.firm_inputs(q, dt).index
    assert f8.firm_inputs(q, dt + pd.Timedelta(400, unit="D")).empty              # latest quarter too old
    gap = _firm_quarters("gy", 0.5, pd.DatetimeIndex(list(QUARTERS[:4]) + list(QUARTERS[4:] + pd.offsets.QuarterEnd(1))))
    assert f8.firm_inputs(gap, dt).empty


def test_macro_weight_and_missing_macro():
    panels, _ = _panels()
    out = f8.compute(panels, AS_OF)
    assert (out["w"] == 0.0).all() and out["macro_lever"].isna().all()
    # Source example: Macro LEVER-Score 8 in January 2006 (2006 PDF p. 16); w = 0.1 x 8 (2007 p. 39).
    panels["macro_lever"] = pd.DataFrame({"date": [pd.Timestamp("2024-01-31")], "macro_lever": [8.0],
                                          "available_at": [pd.Timestamp("2024-02-01")]})
    out = f8.compute(panels, AS_OF)
    assert np.allclose(out["w"], 0.8)
    assert np.allclose(out.loc[out["corner"] == "LL", "score"], 0.8)
    assert np.allclose(out.loc[out["corner"] == "HH", "score"], -0.8)


def test_nan_spread_is_not_scored():
    panels, _ = _panels()
    bp = panels["bond_panel"].copy()
    bp.loc[0, "g_spread"] = np.nan
    panels["bond_panel"] = bp
    out = f8.compute(panels, AS_OF)
    assert "C00" not in set(out["cusip"]) or out.loc[out["cusip"] == "C00", "score"].isna().all()


def test_missing_equity_price_gives_nan_inputs():
    q = _firm_quarters("gz", 0.5)
    q.loc[q.index[-1], "prccq"] = np.nan
    x = f8.quarter_inputs(q)
    assert x[["bm", "fcf_yield", "cash_mcap", "size"]].isna().all()


# ---------------------------------------------------------------- helpers


def test_quarter_inputs_by_hand():
    q = pd.DataFrame({"ceqq": 400.0, "prccq": 10.0, "cshoq": 100.0, "cheq": 100.0, "dlcq": 50.0, "dlttq": 150.0,
                      "oibdpq": 25.0, "oancf": [30.0, 10.0] * 4, "capx": [10.0] * 4 + [12.0] * 4}, index=range(8))
    x = f8.quarter_inputs(q)
    fcf = np.array([20.0, 0.0, 20.0, 0.0, 18.0, -2.0, 18.0, -2.0])
    assert x["bm"] == pytest.approx(0.4)
    assert x["ev_ebitda"] == pytest.approx((1000 + 200 - 100) / 100)
    assert x["fcf_yield"] == pytest.approx(32.0 / 1000)
    assert x["capex_growth"] == pytest.approx(48.0 / 40.0 - 1.0)
    assert x["fcf_var"] == pytest.approx(np.std(fcf, ddof=1) / 200.0)
    assert x["cash_mcap"] == pytest.approx(0.1) and x["size"] == pytest.approx(1000.0)


def test_quarter_inputs_bad_denominators():
    q = pd.DataFrame({"ceqq": 400.0, "prccq": 10.0, "cshoq": 100.0, "cheq": 100.0, "dlcq": 0.0, "dlttq": 0.0,
                      "oibdpq": -5.0, "oancf": 10.0, "capx": [0.0] * 4 + [5.0] * 4}, index=range(8))
    x = f8.quarter_inputs(q)
    assert np.isnan(x["ev_ebitda"]) and np.isnan(x["fcf_var"]) and np.isnan(x["capex_growth"])


def test_normalise_by_hand():
    v, w = pd.Series([1.0, 2.0, 3.0]), pd.Series([1.0, 1.0, 2.0])
    m = (1 + 2 + 6) / 4
    assert np.allclose(f8.normalise(v, w, +1), [1 / m - 1, 2 / m - 1, 3 / m - 1])
    assert np.allclose(f8.normalise(v, w, -1), [-(1 / m - 1), -(2 / m - 1), -(3 / m - 1)])
    neg = f8.normalise(pd.Series([-1.0, -2.0]), pd.Series([1.0, 1.0]), +1)
    assert neg[0] > neg[1]                                                         # |mean| keeps the order


def test_normalise_sector_and_fallback():
    idx = [f"s{i}" for i in range(7)]
    v = pd.Series([1.0, 1.0, 1.0, 1.0, 1.0, 4.0, 4.0], index=idx)
    w = pd.Series(1.0, index=idx)
    sec = pd.Series(["A"] * 5 + ["B"] * 2, index=idx)
    out = f8.normalise(v, w, +1, sec)
    assert np.allclose(out[:5], 0.0)                                               # sector A mean 1
    assert np.allclose(out[5:], 4.0 / (13.0 / 7.0) - 1.0)                          # B too small: universe mean


def test_uniform_by_hand():
    assert list(f8.uniform(pd.Series([3.0, 1.0, 2.0]))) == [10.0, 0.0, 5.0]
    assert list(f8.uniform(pd.Series([7.0]))) == [5.0]


def test_tech_before_2001_excluded():
    panels, _ = _panels(10)
    x = f8.firm_inputs(panels["compustat_quarterly"], f8.decision_time(AS_OF))
    sec = pd.Series("45", index=x.index)
    sec.iloc[:5] = "20"
    assert len(f8.firm_lever(x, sec, pd.Timestamp("2000-06-30"))) == 5
    assert len(f8.firm_lever(x, sec, pd.Timestamp("2001-06-30"))) == 10


def test_corner_groups_and_score_by_hand():
    df = pd.DataFrame({"bucket": "b", "lever": np.arange(1.0, 16.0), "s": [3.0, 1.0, 2.0] + [1.0] * 9 + [1.0, 3.0, 2.0]})
    g = f8.corner_groups(df, "s")
    assert list(g["lever_grp"]) == ["L"] * 3 + ["M"] * 9 + ["H"] * 3              # 20% / 60% / 20% of 15
    cell = (g["lever_grp"] + g["spread_grp"]).tolist()
    assert cell[:3] == ["LH", "LL", "LM"] and cell[-3:] == ["HL", "HH", "HM"]
    sc = f8.corner_score(g["lever_grp"], g["spread_grp"], 0.5)
    assert list(sc[:3]) == [1.0, 0.5, 0.0] and list(sc[-3:]) == [-1.0, -0.5, 0.0]


def test_assign_buckets_fallback():
    rc = pd.Series(["BB"] * 16 + ["B"] * 4)
    yrs = pd.Series([2.0] * 15 + [9.0] + [5.0] * 4)
    b = f8.assign_buckets(rc, yrs)
    assert (b[:16] == "BB").all()                                                  # lone 9-year bond: pool the class
    full = f8.assign_buckets(pd.Series(["BB"] * 30), pd.Series([2.0] * 15 + [9.0] * 15))
    assert set(full) == {"BB|0", "BB|2"}
    assert b[16:].isna().all()                                                     # 4 B bonds: too few


def test_rating_classes_actual_then_nr():
    g = pd.Series(["g1", "g2"])
    ratings = pd.DataFrame({"gvkey": ["g1"], "datadate": [pd.Timestamp("2024-03-31")], "splticrm": ["BB+"],
                            "available_at": [pd.Timestamp("2024-03-31")]})
    out = f8.rating_classes(g, ratings, None, f8.decision_time(AS_OF))
    assert list(out) == ["BB", "NR"]


def test_macro_lever_score():
    years = np.arange(2000, 2016)
    x = np.arange(len(years), dtype=float)
    d = pd.DataFrame({"year": years, "pe": x, "available_at": pd.to_datetime([f"{y + 1}-01-31" for y in years])})
    n = pd.DataFrame({"year": years[1:], "n_lbo": 2.0 * x[:-1] + 1.0,
                      "available_at": pd.to_datetime([f"{y + 1}-01-31" for y in years[1:]])})
    as_of = pd.Timestamp("2017-03-31")
    assert f8.macro_lever_score(d, n, as_of) == pytest.approx(10.0)                # forecast above every fitted year
    assert f8.macro_lever_score(d.assign(pe=-x), n.assign(n_lbo=-2.0 * x[:-1] + 1.0), as_of) == pytest.approx(0.0)
    assert np.isnan(f8.macro_lever_score(d, n, pd.Timestamp("2010-03-31")))       # too few years public
