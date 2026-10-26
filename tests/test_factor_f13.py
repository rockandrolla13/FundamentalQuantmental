"""Tests for F13 realized bond illiquidity, level and shock (docs/factors/F13-realized-illiquidity.md)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from hy.factors import f13_realized_illiquidity as f13

AS_OF = pd.Timestamp("2015-06-30")
MONTHS = pd.date_range(end=AS_OF, periods=f13.HIST_MONTHS + 13, freq="ME")
DAY = pd.Timedelta(1, unit="D")
FAST = {"min_fit": 20, "min_cell": 2}


# ---------------------------------------------------------------- synthetic fixture


def panel_rows(cusips, months=MONTHS, gvkey=None):
    rows = []
    for i, c in enumerate(cusips):
        for k, m in enumerate(months):
            rows.append({"date": m, "cusip": c, "gvkey": gvkey or f"G{i}", "years": 5.0, "price": 95.0 + (k % 2),
                         "yield": 0.07, "g_spread": 0.04, "mod_dur": 4.0, "carried": False, "n_trades": 9,
                         "par_volume": 9e6, "bid_ask_pts": 0.5, "available_at": m + DAY})
    return pd.DataFrame(rows)


def month_trades(cusip, month, d, days=(3, 10, 17), per_day=3, par=1e6, base=95.0):
    """Trades 10 minutes apart that alternate between base and base (1 + d): each return is log(1 + d)."""
    rows, k = [], 0
    for day in days:
        t0 = pd.Timestamp(month.year, month.month, day) + pd.Timedelta(10, unit="h")
        for j in range(per_day):
            rows.append({"cusip": cusip, "trade_time": t0 + pd.Timedelta(10 * j, unit="min"),
                         "price": base * (1 + d) if k % 2 else base, "par": par,
                         "available_at": t0.normalize() + DAY})
            k += 1
    return rows


def trades_for(spec, months=MONTHS):
    """spec: cusip -> d, or cusip -> (d_history, d_last_month)."""
    rows = []
    for c, d in spec.items():
        for m in months:
            dm = d if np.isscalar(d) else (d[1] if m == months[-1] else d[0])
            rows += month_trades(c, m, dm)
    return pd.DataFrame(rows)


@pytest.fixture
def base():
    spec = {"A": 0.002, "B": 0.004, "C": 0.008, "D": 0.016}
    return {"bond_panel": panel_rows(list(spec)), "trace_trades": trades_for(spec)}


# ---------------------------------------------------------------- contract


def test_meta_and_columns(base):
    for k in ("rank", "name", "level", "horizon_months", "needs", "spec", "section"):
        assert k in f13.META
    assert f13.META["rank"] == 13 and "trace_trades" in f13.META["needs"]
    out = f13.compute(base, AS_OF, **FAST)
    assert list(out.columns) == f13.COLS
    assert out["cusip"].is_unique and len(out) == 4
    assert (out["date"] == AS_OF).all() and (out["available_at"] == AS_OF + DAY).all()
    assert (out["measure"] == "trace").all()


def test_no_lookahead(base):
    ref = f13.compute(base, AS_OF, **FAST)
    late = dict(base)
    july = pd.Timestamp("2015-07-31")
    extra = trades_for({"A": 0.05, "D": 0.0001}, months=pd.DatetimeIndex([july]))
    hidden = pd.DataFrame(month_trades("A", AS_OF, 0.09, days=(29,))).assign(available_at=july)
    late["trace_trades"] = pd.concat([base["trace_trades"], extra, hidden], ignore_index=True)
    late["bond_panel"] = pd.concat([base["bond_panel"], panel_rows(list("ABCD"), pd.DatetimeIndex([july]))])
    pd.testing.assert_frame_equal(ref, f13.compute(late, AS_OF, **FAST))


# ---------------------------------------------------------------- sign


def test_level_sign_more_illiquid_scores_higher(base):
    out = f13.compute(base, AS_OF, **FAST).set_index("cusip")
    assert list(out["score"].sort_values().index) == ["A", "B", "C", "D"]
    assert out["illiq"].is_monotonic_increasing


def test_shock_sign_jump_is_positive():
    spec = {"A": 0.004, "B": 0.004, "C": (0.004, 0.012), "D": 0.008}
    panels = {"bond_panel": panel_rows(list(spec)), "trace_trades": trades_for(spec)}
    out = f13.compute(panels, AS_OF, **FAST).set_index("cusip")
    assert (out["shock_source"] == "har").all()
    # A = 8 log(1 + d) / (0.95e6 (5 + 4 (1 + d))): 9 trades, 8 returns, 5 at the base price
    jump = np.log(np.log(1.012) / np.log(1.004)) + np.log((9 + 4 * 0.004) / (9 + 4 * 0.012))
    assert out.loc["C", "shock"] == pytest.approx(jump, rel=1e-6)
    assert out.loc[["A", "B", "D"], "shock"].abs().max() < 1e-8
    assert out["shock_z"].idxmax() == "C"
    assert out.loc["C", "illiq_change"] > 0
    # score is level only by default; a positive shock weight lifts the shocked bond further
    w = f13.compute(panels, AS_OF, shock_weight=1.0, **FAST).set_index("cusip")
    assert w.loc["C", "score"] - out.loc["C", "score"] == pytest.approx(out.loc["C", "shock_z"])


# ---------------------------------------------------------------- sparse trades and missing panels


def test_sparse_bond_extends_window_then_falls_back_to_panel(base):
    p = dict(base)
    t = base["trace_trades"]
    june = t["trade_time"] >= pd.Timestamp("2015-06-01")
    keep = ~(june & t["cusip"].eq("B")) & ~t["cusip"].eq("C")
    sparse = pd.DataFrame(month_trades("B", AS_OF, 0.004, days=(3,), per_day=3))   # 2 returns in June
    p["trace_trades"] = pd.concat([t[keep], sparse], ignore_index=True)
    out = f13.compute(p, AS_OF, **FAST).set_index("cusip")
    assert out.loc["B", "measure"] == "trace_3m" and out.loc["B", "n_returns"] >= f13.MIN_RETURNS
    assert out.loc["C", "measure"] == "panel" and np.isfinite(out.loc["C", "illiq"])
    assert out.loc["A", "measure"] == "trace"


def test_missing_trace_panel_uses_monthly_fallback(base):
    out = f13.compute({"bond_panel": base["bond_panel"]}, AS_OF, **FAST)
    assert len(out) == 4 and (out["measure"] == "panel").all()
    # identical bonds in the panel: every level ties, so the cell sd is zero and no bond scores
    assert out["score"].isna().all()
    assert out["illiq"].notna().all()


def test_missing_bond_panel_is_empty(base):
    out = f13.compute({"trace_trades": base["trace_trades"]}, AS_OF)
    assert out.empty and list(out.columns) == f13.COLS


def test_defaulted_issuer_has_no_score(base):
    ratings = pd.DataFrame({"gvkey": ["G0", "G1", "G2", "G3"], "datadate": AS_OF - pd.Timedelta(5, unit="D"),
                            "splticrm": ["B", "B", "B", "D"], "available_at": AS_OF - pd.Timedelta(4, unit="D")})
    p = dict(base, ratings=ratings)
    out = f13.compute(p, AS_OF, **FAST).set_index("cusip")
    assert np.isnan(out.loc["D", "score"]) and out.loc[["A", "B", "C"], "score"].notna().all()
    assert out.loc["A", "rclass"] == "B" and out.loc["A", "cell"].startswith("rm:")


def test_nan_and_tiny_trades_drop_in_builder():
    raw = pd.DataFrame({"cusip_id": ["X"] * 4, "trd_exctn_dt": ["2015-06-01"] * 4,
                        "trd_exctn_tm": ["10:00:00", "10:07:00", "10:20:00", "11:00:00"],
                        "rptd_pr": [100.0, np.nan, 101.0, 100.5], "ascii_rptd_vol_tx": ["500000", "1MM+", "50000",
                                                                                        "5MM+"]})
    t = f13.trades_from_trace(raw)
    assert list(t["price"]) == [100.0, 100.5]
    assert list(t["par"]) == [500000.0, 5_000_000.0]
    assert t["trade_time"].iloc[1] == pd.Timestamp("2015-06-01 11:00")
    assert (t["available_at"] == pd.Timestamp("2015-06-02")).all()


# ---------------------------------------------------------------- formula helpers, hand computations


def test_sample_prices_keeps_last_price_and_all_volume():
    t = pd.DataFrame({"cusip": "X", "trade_time": pd.to_datetime(["2015-06-01 10:00", "2015-06-01 10:03",
                                                                   "2015-06-01 10:06"]),
                      "price": [100.0, 102.0, 101.0], "par": [1e6, 2e6, 1e6]})
    s = f13.sample_prices(t, "5min")
    assert list(s["price"]) == [102.0, 101.0]
    assert s["dollar_volume"].iloc[0] == pytest.approx(1e6 + 2.04e6)
    assert list(s["n_trades"]) == [2, 1]


def test_realized_amihud_hand_value():
    t = pd.DataFrame({"cusip": "X", "trade_time": pd.to_datetime(["2015-06-01 10:00", "2015-06-01 10:10",
                                                                   "2015-06-02 10:00"]),
                      "price": [100.0, 101.0, 100.0], "par": [1e6, 1e6, 1e6]})
    s = f13.sample_prices(t)
    a = f13.realized_amihud(s, pd.Timestamp("2015-06-01"), pd.Timestamp("2015-06-30 23:59")).iloc[0]
    rpv = 2 * np.log(1.01)
    assert a["n_returns"] == 2
    assert a["illiq"] == pytest.approx(1e6 * rpv / 3.01e6)
    # the window cuts the first trade: one return, no link to a price before the start
    b = f13.realized_amihud(s, pd.Timestamp("2015-06-01 10:05"), pd.Timestamp("2015-06-30")).iloc[0]
    assert b["n_returns"] == 1 and b["illiq"] == pytest.approx(1e6 * np.log(1.01) / 2.01e6)


def test_panel_measure_hand_value():
    m0, m1 = pd.Timestamp("2015-05-31"), AS_OF
    p = pd.DataFrame({"date": [m0, m1, m0, m1], "cusip": ["X", "X", "Y", "Y"], "price": [90.0, 99.0, 90.0, 90.0],
                      "par_volume": [1e6, 2e6, 1e6, 2e6], "carried": False})
    out = f13.panel_measure(p, m1).set_index("cusip")
    assert out.loc["X", "illiq"] == pytest.approx(1e6 * np.log(99 / 90) / (2e6 * 0.99))
    assert "Y" not in out.index          # no price move: no measure


def test_har_terms_and_fit():
    idx = pd.date_range("2014-01-31", periods=14, freq="ME")
    wide = pd.DataFrame({"X": np.arange(14, dtype=float)}, index=idx)
    terms = f13.har_terms(wide)
    assert terms[1].loc[idx[5], "X"] == 4.0
    assert terms[3].loc[idx[5], "X"] == pytest.approx((2 + 3 + 4) / 3)
    assert terms[12].loc[idx[13], "X"] == pytest.approx(np.mean(np.arange(1, 13)))
    assert terms[12].loc[idx[6], "X"] == pytest.approx(np.mean(np.arange(0, 6)))   # 6 of 12 = MIN_LAG_OBS
    assert np.isnan(terms[12].loc[idx[5], "X"])                                     # 5 values: too few
    rng = np.random.default_rng(0)
    x = rng.normal(size=(200, 3))
    y = -0.2 + x @ np.array([0.15, 0.37, 0.42])
    assert f13.fit_har(y, x) == pytest.approx([-0.2, 0.15, 0.37, 0.42])


def test_own_mean_fallback_when_fit_is_too_small():
    idx = pd.date_range(end=AS_OF, periods=6, freq="ME")
    wide = pd.DataFrame({"X": [1.0, 1.0, 1.0, 1.0, 1.0, 2.0]}, index=idx)
    sh = f13.illiquidity_shock(wide, AS_OF, min_fit=1000)
    assert sh.loc["X", "shock_source"] == "own" and sh.loc["X", "shock"] == pytest.approx(1.0)


def test_peer_z_and_fallback():
    x = pd.Series([1.0, 2.0, 3.0, 10.0, np.nan], index=list("abcde"))
    keys = pd.DataFrame({"rm": ["k1", "k1", "k1", "k2", "k1"], "r": ["r", "r", "r", "r", "r"],
                         "all": "all"}, index=x.index)
    z, cell = f13.peer_z(x, keys, min_cell=2)
    assert z["a"] == pytest.approx(-1.0) and z["c"] == pytest.approx(1.0)
    assert cell["a"] == "rm:k1" and cell["d"] == "r:r"           # k2 has one bond: falls back to the class
    assert z["d"] == pytest.approx((10 - 4) / np.std([1, 2, 3, 10], ddof=1))
    assert np.isnan(z["e"])


def test_cost_gate_hand_value():
    illiq = pd.Series([0.5, 1.0, 2.0, 4.0, 8.0, np.nan], index=list("abcdef"))
    g = f13.cost_gate(illiq, pd.Series("trace", index=illiq.index), gate_pct=0.6)
    assert g.loc["a", "impact_bp"] == pytest.approx(0.5e-6 * 1e6 * 1e4)
    assert list(g["cost_gate_pass"]) == [True, True, True, False, False, False]


def test_cost_columns_in_output(base):
    out = f13.compute(base, AS_OF, **FAST).set_index("cusip")
    assert out["cost_rt"].iloc[0] == pytest.approx(0.5 / 95.0)
    assert out.loc["A", "cost_gate_pass"] and not out.loc["D", "cost_gate_pass"]
