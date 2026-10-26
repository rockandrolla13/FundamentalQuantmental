"""Tests for hy.factors.f02_spread_to_d2d: contract, no look-ahead, sign, edge cases and each formula helper."""

import numpy as np
import pandas as pd
import pytest
from scipy.special import ndtr
from scipy.stats import multivariate_normal

from hy.factors import f02_spread_to_d2d as f02

AS_OF = pd.Timestamp("2015-06-30")
DT = AS_OF + pd.Timedelta(1, unit="D")
DAY = pd.Timedelta(1, unit="D")


def _panels(spreads=(0.03, 0.06, 0.04, 0.05), debt_lt=(100.0, 100.0, 300.0, 50.0), daily=False):
    """One bond per issuer. Issuer gN has 100 of equity (via market value), the given long-term debt, rating BB."""
    n = len(spreads)
    gv = [f"g{i}" for i in range(n)]
    bond = pd.DataFrame({"date": AS_OF, "cusip": [f"c{i}" for i in range(n)], "gvkey": gv, "years": 5.0,
                         "g_spread": spreads, "mod_dur": 4.0, "price": 100.0, "yield": 0.07, "carried": False,
                         "available_at": DT})
    fin = pd.DataFrame({"gvkey": gv, "period_end": pd.Timestamp("2015-03-31"), "debt_current": 10.0,
                        "debt_long_term": debt_lt, "available_at": pd.Timestamp("2015-05-10")})
    ends = pd.date_range(end=AS_OF, periods=36, freq="ME")
    eqm = pd.DataFrame([(g, d, 0.05 * (-1) ** k) for g in gv for k, d in enumerate(ends)],
                       columns=["gvkey", "datadate", "ret"]).assign(available_at=lambda x: x["datadate"] + DAY)
    mv = pd.DataFrame({"gvkey": gv, "period_end": AS_OF, "value": 100.0, "available_at": DT})
    rat = pd.DataFrame({"gvkey": gv, "datadate": pd.Timestamp("2015-05-31"), "splticrm": "BB",
                        "available_at": pd.Timestamp("2015-06-01")})
    p = {"bond_panel": bond, "financials": fin, "equity_monthly": eqm, "market_value": mv, "ratings": rat}
    if daily:
        days = pd.bdate_range(end=AS_OF, periods=300)
        p["equity_daily"] = pd.DataFrame([(g, d, 10.0, 10_000.0, 0.01 * (-1) ** k) for g in gv
                                          for k, d in enumerate(days)],
                                         columns=["gvkey", "date", "prc", "shrout", "ret"]).assign(
            available_at=lambda x: x["date"] + DAY)
    return p


# ---------------------------------------------------------------- contract


def test_meta_keys():
    assert set(f02.META) == {"rank", "name", "level", "horizon_months", "needs", "spec", "section"}
    assert f02.META["rank"] == 2 and f02.META["level"] == "bond"
    assert {"bond_panel", "financials", "equity_daily", "bond_daily"} <= set(f02.META["needs"])


def test_compute_columns_and_one_row_per_bond():
    out = f02.compute(_panels(), AS_OF)
    assert list(out.columns[:4]) == ["date", "cusip", "score", "available_at"]
    assert out["cusip"].is_unique and len(out) == 4
    assert (out["date"] == AS_OF).all() and (out["available_at"] <= DT).all()
    assert out["score"].between(-0.5, 0.5).all()
    assert (out["vol_source"] == "monthly").all() and (out["e_source"] == "market_value").all()


# ---------------------------------------------------------------- no look-ahead


def test_no_lookahead_rows_after_decision_time_change_nothing():
    p = _panels()
    base = f02.compute(p, AS_OF)
    q = {k: v.copy() for k, v in p.items()}
    late = q["bond_panel"].assign(date=AS_OF + pd.offsets.MonthEnd(1), g_spread=0.15,
                                  available_at=AS_OF + pd.offsets.MonthEnd(1) + DAY)
    q["bond_panel"] = pd.concat([q["bond_panel"], late])
    # A 10-Q accepted on day t + 2 with ten times the debt: it must not enter the month-end t score.
    q["financials"] = pd.concat([q["financials"], q["financials"].assign(
        period_end=AS_OF, debt_long_term=5000.0, available_at=AS_OF + 2 * DAY)])
    q["equity_monthly"] = pd.concat([q["equity_monthly"], q["equity_monthly"].tail(4).assign(
        datadate=AS_OF + pd.offsets.MonthEnd(1), ret=-0.9, available_at=AS_OF + pd.offsets.MonthEnd(1) + DAY)])
    q["market_value"] = pd.concat([q["market_value"], q["market_value"].assign(value=1.0, available_at=DT + DAY)])
    pd.testing.assert_frame_equal(base, f02.compute(q, AS_OF))


# ---------------------------------------------------------------- sign


def test_wider_spread_same_dd_ranks_higher():
    out = f02.compute(_panels(spreads=(0.03, 0.06), debt_lt=(100.0, 100.0)), AS_OF).set_index("cusip")
    assert out.loc["c0", "dd_equity"] == pytest.approx(out.loc["c1", "dd_equity"])
    assert out.loc["c1", "score"] > out.loc["c0", "score"]


def test_higher_dd_same_spread_ranks_higher():
    out = f02.compute(_panels(spreads=(0.05, 0.05), debt_lt=(50.0, 300.0)), AS_OF).set_index("cusip")
    assert out.loc["c0", "dd_equity"] > out.loc["c1", "dd_equity"]
    assert out.loc["c0", "score"] > out.loc["c1", "score"]


def test_dd_falls_with_debt_and_with_vol():
    dd = f02.naive_dd(100.0, np.array([20.0, 50.0, 100.0]), 0.4, 0.1)
    assert np.all(np.diff(dd) < 0)
    dd = f02.naive_dd(100.0, 50.0, np.array([0.2, 0.4, 0.8]), 0.1)
    assert np.all(np.diff(dd) < 0)


# ---------------------------------------------------------------- edge cases


def test_missing_required_panel_gives_empty_frame():
    p = _panels()
    del p["financials"]
    out = f02.compute(p, AS_OF)
    assert out.empty and list(out.columns) == f02.COLUMNS


def test_market_value_grows_with_later_monthly_returns():
    eqm = pd.DataFrame({"gvkey": "g0", "datadate": pd.to_datetime(["2015-03-31", "2015-04-30", "2015-05-31"]),
                        "ret": [0.5, 0.1, -0.2], "available_at": DT})
    mv = pd.DataFrame({"gvkey": ["g0", "g1"], "period_end": pd.Timestamp("2015-03-31"), "value": 100.0,
                       "available_at": DT})
    e = f02._market_value(mv, eqm, AS_OF)["E"]
    assert e["g0"] == pytest.approx(100.0 * 1.1 * 0.8) and e["g1"] == pytest.approx(100.0)


def test_no_equity_gives_nan_not_zero():
    p = _panels()
    p["market_value"] = p["market_value"][p["market_value"]["gvkey"] != "g0"]
    out = f02.compute(p, AS_OF).set_index("cusip")
    assert np.isnan(out.loc["c0", "score"]) and np.isnan(out.loc["c0", "dd_equity"])
    assert out.drop("c0")["score"].notna().all()


def test_short_daily_history_falls_back_to_monthly_with_flag():
    p = _panels(daily=True)
    e = p["equity_daily"]
    p["equity_daily"] = e[(e["gvkey"] != "g0") | (e["date"] > AS_OF - pd.Timedelta(150, unit="D"))]  # ~107 days
    out = f02.compute(p, AS_OF).set_index("cusip")
    assert out.loc["c0", "vol_source"] == "monthly" and out.loc["c0", "e_source"] == "market_value"
    assert (out.drop("c0")["vol_source"] == "daily").all() and (out.drop("c0")["e_source"] == "daily").all()
    assert out["score"].notna().all()


def test_distressed_spread_and_carried_rows_are_excluded():
    p = _panels(spreads=(0.03, 0.25, 0.04, 0.05))
    p["bond_panel"].loc[2, "carried"] = True      # no trade in the last 7 days: the panel carries the row
    out = f02.compute(p, AS_OF)
    assert set(out["cusip"]) == {"c0", "c3"}


def test_ig_bond_gets_no_bucket_score_but_a_pool_rank():
    p = _panels()
    p["ratings"].loc[0, "splticrm"] = "BBB"
    out = f02.compute(p, AS_OF).set_index("cusip")
    assert np.isnan(out.loc["c0", "score"]) and np.isfinite(out.loc["c0", "s2d_rank"])


def test_no_bond_daily_gives_nan_cg_score():
    out = f02.compute(_panels(daily=True), AS_OF)
    assert out["score_cg"].isna().all() and (out["cg_flag"] == 0).all() and out["score"].notna().all()


def _variant_b_panels(n_days=300):
    p = _panels(spreads=(0.05, 0.05), debt_lt=(100.0, 100.0), daily=True)
    old = p["financials"].assign(period_end=pd.Timestamp("2013-12-31"), available_at=pd.Timestamp("2014-03-01"))
    p["financials"] = pd.concat([old, p["financials"]], ignore_index=True)   # D known on every daily row
    days = pd.bdate_range(end=AS_OF, periods=n_days)
    rng = np.random.default_rng(1)
    rows = []
    for c in ("c0", "c1"):
        s = 0.05 * np.exp(rng.normal(0.0, 0.02, len(days)))
        if c == "c1":
            s[-1] = 0.08                           # a jump wider on the last day: cheap against the model
        rows += [(c, d, v) for d, v in zip(days, s)]
    p["bond_daily"] = pd.DataFrame(rows, columns=["cusip", "date", "g_spread"]).assign(
        available_at=lambda x: x["date"] + DAY)
    return p


def test_variant_b_wide_jump_scores_high_and_flags():
    out = f02.compute(_variant_b_panels(), AS_OF).set_index("cusip")
    assert out.loc["c1", "cg_gap"] > out.loc["c0", "cg_gap"]
    assert out.loc["c1", "score_cg"] > f02.CG_TRIGGER and out.loc["c1", "cg_flag"] == 1
    assert abs(out.loc["c0", "score_cg"]) < f02.CG_TRIGGER and out.loc["c0", "cg_flag"] == 0
    assert out["cg_spread"].gt(0).all() and out["cg_spread_kv"].gt(0).all()


def test_variant_b_short_history_gives_nan():
    p = _variant_b_panels()
    p["bond_daily"] = p["bond_daily"][p["bond_daily"]["date"] > AS_OF - pd.Timedelta(200, unit="D")]  # < 126 days
    out = f02.compute(p, AS_OF)
    assert out["score_cg"].isna().all()


# ---------------------------------------------------------------- formula helpers


def test_default_point_hand():
    assert f02.default_point(10.0, 100.0) == pytest.approx(60.0)
    assert f02.default_point(np.nan, 100.0) == pytest.approx(50.0)
    assert np.isnan(f02.default_point(np.nan, np.nan))


def test_naive_dd_hand():
    # E = 100, F = 50, sig_E = 0.4, mu = 0.1. sig_V = (2/3) 0.4 + (1/3)(0.05 + 0.10) = 0.316667.
    sv = 2 / 3 * 0.4 + 1 / 3 * 0.15
    assert f02.naive_sigma_v(100.0, 50.0, 0.4) == pytest.approx(sv)
    assert f02.naive_dd(100.0, 50.0, 0.4, 0.1) == pytest.approx((np.log(3.0) + 0.1 - 0.5 * sv ** 2) / sv)
    assert f02.naive_dd(100.0, 50.0, 0.4, 0.1) == pytest.approx(3.62676, abs=1e-5)
    assert np.isnan(f02.naive_dd(100.0, 0.0, 0.4, 0.1))


def test_spread_to_dd_hand():
    # log 0.05 - log Phi(-1) = -2.995732 + 1.841022.
    assert f02.spread_to_dd(0.05, 1.0) == pytest.approx(-1.154710, abs=1e-6)
    assert np.isfinite(f02.spread_to_dd(0.05, 40.0))          # log_ndtr: no PD floor needed


def test_centred_rank_and_winsorise():
    r = f02.centred_rank(pd.Series([3.0, 1.0, 2.0, np.nan]))
    assert r.iloc[:3].tolist() == [0.5, -0.5, 0.0] and np.isnan(r.iloc[3])
    assert f02.centred_rank(pd.Series([7.0])).iloc[0] == 0.0
    w = f02.winsorise(pd.Series(np.arange(101.0)))
    assert w.min() == 1.0 and w.max() == 99.0


def test_vol_and_compound_hand():
    assert f02.annual_vol(np.array([0.1, -0.1]), 12) == pytest.approx(np.sqrt(0.02) * np.sqrt(12))
    assert f02.compound([0.1, 0.1]) == pytest.approx(0.21)


def test_cg_debt_hand():
    # FD = 100, other liabilities 100, minority interest 80 capped at 50: 100 + 50 - 50.
    assert f02.cg_debt(10.0, 90.0, 200.0, 80.0) == pytest.approx(100.0)
    assert f02.cg_debt(10.0, 90.0) == pytest.approx(100.0)


def test_bvn_cdf_against_scipy():
    rng = np.random.default_rng(0)
    for h, k, r in zip(rng.normal(0, 2, 50), rng.normal(0, 2, 50), rng.uniform(-0.99, 0.99, 50)):
        ref = multivariate_normal([0.0, 0.0], [[1.0, r], [r, 1.0]]).cdf([h, k])
        assert f02.bvn_cdf(h, k, r) == pytest.approx(ref, abs=1e-6)
    assert f02.bvn_cdf(0.0, 0.0, 0.5) == pytest.approx(0.25 + np.arcsin(0.5) / (2 * np.pi), abs=1e-9)


def test_creditgrades_finger_hand():
    # S = 1, D = 1: d = 3 e^0.09. A = sqrt(0.25^2 + 0.09) at t = 1.
    d, A = 3.0 * np.exp(0.09), np.sqrt(0.0625 + 0.09)
    hand = ndtr(-A / 2 + np.log(d) / A) - d * ndtr(-A / 2 - np.log(d) / A)
    assert f02.creditgrades_survival(1.0, 1.0, 0.25, 1.0, exact=False) == pytest.approx(hand, abs=1e-12)


def test_kiesel_veraart_against_finger_and_bounds():
    for t in (1.0, 5.0):   # share-to-debt ratio 2: the two forms agree within 1e-3
        assert abs(f02.creditgrades_survival(2.0, 1.0, 0.25, t, exact=True)
                   - f02.creditgrades_survival(2.0, 1.0, 0.25, t, exact=False)) < 1e-3
    # Ratio 0.5, below the 0.796 of Kiesel and Veraart (Alber PDF p. 24 fn. 15): the forms differ.
    assert abs(f02.creditgrades_survival(0.5, 1.0, 0.25, 1.0, exact=True)
               - f02.creditgrades_survival(0.5, 1.0, 0.25, 1.0, exact=False)) > 1e-3
    S, sig, t = np.meshgrid([0.05, 0.2, 0.5, 1.0, 3.0], [0.05, 0.3, 1.0], [0.25, 1.0, 10.0])
    p = f02.creditgrades_survival(S, 1.0, sig, t, exact=True)
    assert np.all((p >= 0.0) & (p <= 1.0))


def test_kiesel_veraart_hand_values():
    # S = 0.5, D = 1, sig_A = 0.25, t = 1: ln d = ln 2 + 0.09, A = sqrt(0.1525), rho = 0.3/A.
    ln_d, A, lam = np.log(2.0) + 0.09, np.sqrt(0.1525), 0.3
    c1 = [[1.0, lam / A], [lam / A, 1.0]]
    c2 = [[1.0, -lam / A], [-lam / A, 1.0]]
    hand = (multivariate_normal([0, 0], c1).cdf([-lam / 2 + ln_d / lam, -A / 2 + ln_d / A])
            - np.exp(ln_d) * multivariate_normal([0, 0], c2).cdf([lam / 2 + ln_d / lam, -A / 2 - ln_d / A]))
    assert f02.creditgrades_survival(0.5, 1.0, 0.25, 1.0, exact=True) == pytest.approx(hand, abs=1e-6)
    # As t -> 0 only the barrier jump is left: P = Phi(-lam/2 + ln d/lam).
    assert f02.creditgrades_survival(0.5, 1.0, 0.25, 1e-10, exact=True) == pytest.approx(
        ndtr(-lam / 2 + ln_d / lam), abs=1e-6)


def test_creditgrades_spread_and_implied_sigma():
    assert f02.creditgrades_spread(0.9, 2.0) == pytest.approx(-0.7 * np.log(0.9) / 2.0)
    s = f02.creditgrades_spread(f02.creditgrades_survival(0.5, 1.0, 0.3, 4.0), 4.0)
    assert f02.implied_sigma_a(s, 0.5, 1.0, 4.0) == pytest.approx(0.3, rel=1e-8)
    assert np.isnan(f02.implied_sigma_a(1e-9, 0.5, 1.0, 4.0))   # below the model floor


def test_cg_gap_score_hand():
    # 20 prior days alternate 0.1 and -0.1: mean |gap| = 0.1, sd = 0.1 sqrt(20/19). Last day 0.5.
    gap = pd.Series([0.1, -0.1] * 10 + [0.5])
    hand = (0.5 - 0.1) / (0.1 * np.sqrt(20 / 19))
    g, flag = f02.cg_gap_score(gap)
    assert g == pytest.approx(hand) and hand < 4.0 and flag == 0
    g, flag = f02.cg_gap_score(pd.Series([0.1, -0.1] * 10 + [-0.9]))
    assert g == pytest.approx(-(0.9 - 0.1) / (0.1 * np.sqrt(20 / 19))) and flag == -1
    assert np.isnan(f02.cg_gap_score(gap.iloc[-20:])[0])        # 19 prior days only
