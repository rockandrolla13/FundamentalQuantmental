"""Offline tests of the alpha backtest (Sections 7.5 and 11): realised alpha arithmetic, HAC inference, IC,
Mincer-Zarnowitz calibration, decile long-short, PIT, the fair-line predictor, and the look-ahead guard."""

import numpy as np
import pandas as pd
import pytest

from hy import backtest as bt
from hy.fairspread import fit_ar1


def _row(cusip, date, price, tsy, coupon=0.06, mat="2026-01-31", dur=4.0, g=0.04, carried=False,
         accrue_to=None, hedge_date=None, gvkey=None, ba=0.5):
    d = pd.Timestamp(date)
    return dict(cusip=cusip, date=d, price=price, coupon=coupon, maturity=pd.Timestamp(mat),
                years=(pd.Timestamp(mat) - d).days / 365.25, **{"yield": tsy + g}, g_spread=g, tsy_yield=tsy,
                mod_dur=dur, carried=carried, accrue_to=pd.Timestamp(accrue_to or d), hedge_date=pd.Timestamp(hedge_date or d),
                available_at=d + pd.Timedelta(days=1), bid_ask_pts=ba, gvkey=gvkey)


def test_realised_excess_return_by_hand():
    panel = pd.DataFrame([_row("A", "2020-01-31", 100.0, 0.020), _row("A", "2020-04-30", 101.0, 0.025)])
    bench = pd.Series({pd.Timestamp("2020-01-31"): 0.040, pd.Timestamp("2020-04-30"): 0.045})
    r = bt.realised_excess_return(panel, 3, as_of=pd.Timestamp("2020-05-01"), bench=bench).iloc[0]
    tau = 90 / 365.25
    total = (101.0 - 100.0 + 100 * 0.06 * tau) / 100.0
    tsy = 0.020 * tau - 4.0 * 0.005
    hedge = 0.040 * tau - 4.0 * 0.005
    assert r["total"] == pytest.approx(total)
    assert r["tsy_ret"] == pytest.approx(tsy)
    assert r["bench_ret"] == pytest.approx(hedge)
    assert r["realised"] == pytest.approx(total - tsy - hedge)
    assert r["h_eff_months"] == 3


def test_realised_stops_at_last_price_for_a_bond_that_stops_trading():
    panel = pd.DataFrame([
        _row("A", "2020-01-31", 100.0, 0.02),
        _row("A", "2020-02-29", 90.0, 0.02),
        _row("A", "2020-03-31", 90.0, 0.02, carried=True, accrue_to="2020-02-27", hedge_date="2020-02-29"),
    ])
    bench = pd.Series({pd.Timestamp(d): 0.04 for d in ["2020-01-31", "2020-02-29", "2020-03-31"]})
    r = bt.realised_excess_return(panel, 3, as_of=pd.Timestamp("2020-04-01"), bench=bench).set_index("date")
    first = r.loc[pd.Timestamp("2020-01-31")]
    assert first["end_carried"] and first["h_eff_months"] == 1
    tau_acc, tau = 27 / 365.25, 29 / 365.25
    total = (90.0 - 100.0 + 6.0 * tau_acc) / 100.0
    assert first["total"] == pytest.approx(total)
    assert first["realised"] == pytest.approx(total - 0.02 * tau - 0.04 * tau)
    assert len(r) == 2   # the carried row is never a start


def test_flat_trading_bond_earns_no_coupon():
    panel = pd.DataFrame([_row("A", "2020-01-31", 40.0, 0.02, g=0.3), _row("A", "2020-02-29", 42.0, 0.02, g=0.3)])
    bench = pd.Series({pd.Timestamp("2020-01-31"): 0.04, pd.Timestamp("2020-02-29"): 0.04})
    r = bt.realised_excess_return(panel, 1, as_of=pd.Timestamp("2020-03-01"), bench=bench).iloc[0]
    assert r["total"] == pytest.approx(2.0 / 40.0)


def test_newey_west_matches_long_run_variance_of_ar1(rng):
    phi, n = 0.5, 40_000
    e = rng.standard_normal(n)
    x = np.empty(n)
    x[0] = e[0]
    for i in range(1, n):
        x[i] = phi * x[i - 1] + e[i]
    true_se = np.sqrt(1.0 / (1 - phi) ** 2 / n)
    assert bt.newey_west_se(x, 60) == pytest.approx(true_se, rel=0.10)
    assert bt.newey_west_se(x, 0) < 0.65 * true_se          # ignoring overlap overstates t


def test_newey_west_lag_zero_is_the_iid_standard_error(rng):
    x = rng.standard_normal(500)
    assert bt.newey_west_se(x, 0) == pytest.approx(x.std() / np.sqrt(500))


def _cross_section(rng, n_dates=36, n=120, noise=1.0, scale=1.0):
    dates = pd.date_range("2019-01-31", periods=n_dates, freq="ME")
    rows = []
    for d in dates:
        truth = rng.normal(0, 0.02, n)
        rows.append(pd.DataFrame({"date": d, "truth": truth, "pred_oc": scale * truth,
                                  "realised": truth + rng.normal(0, 0.02 * noise, n),
                                  "noise": rng.standard_normal(n), "cost_rt": 0.002}))
    return pd.concat(rows, ignore_index=True)


def test_ic_is_one_for_a_perfect_predictor_and_near_zero_for_noise(rng):
    df = _cross_section(rng)
    df["perfect"] = df["realised"]
    assert bt.ic_series(df, "perfect", "realised").min() == pytest.approx(1.0)
    ic = bt.hac_mean(bt.ic_series(df, "noise", "realised"), 0)
    assert abs(ic["mean"]) < 3 * ic["se"]
    assert abs(ic["t"]) < 3


def test_mincer_zarnowitz_recovers_truth_and_flags_overconfidence(rng):
    df = _cross_section(rng)
    mz = bt.mincer_zarnowitz(df, "truth", "realised", lags=2)
    assert mz["b"] == pytest.approx(1.0, abs=0.08) and abs(mz["a"]) < 3 * mz["se_a"]
    df["pred_oc"] = 3.0 * df["truth"]
    oc = bt.mincer_zarnowitz(df, "pred_oc", "realised", lags=2)
    assert oc["b"] == pytest.approx(1 / 3, abs=0.04) and oc["t_b_eq_1"] < -5


def test_decile_long_short_sign_and_cost(rng):
    df = _cross_section(rng, noise=0.5)
    ls = bt.long_short(df, "truth", "realised", "cost_rt")
    assert (ls["gross"] > 0).mean() > 0.95
    assert ls["net"].to_numpy() == pytest.approx((ls["gross"] - 0.004).to_numpy())
    df["anti"] = -df["truth"]
    assert bt.long_short(df, "anti", "realised", None)["gross"].mean() < 0
    cal = bt.decile_calibration(df, "truth", "realised")
    assert len(cal) == 10 and cal["real_mean"].is_monotonic_increasing


def test_max_drawdown_and_summary():
    assert bt.max_drawdown(pd.Series([1.0, 1.2, 0.9, 1.3])) == pytest.approx(0.9 / 1.2 - 1)
    s = bt.long_short_summary(pd.Series([0.01, -0.02, 0.03, 0.01, 0.02, 0.0]), 3)
    assert s["ann_mean"] == pytest.approx(np.mean([0.01, -0.02, 0.03, 0.01, 0.02, 0.0]) * 4)
    assert s["cum_return"] == pytest.approx(1.01 * 1.01 - 1)
    assert s["cagr"] == pytest.approx((1.01 * 1.01) ** (12 / 6) - 1)


def test_pit_is_uniform_when_the_spread_is_right(rng):
    df = _cross_section(rng, n_dates=48)
    pit = bt.pit_values(df, "truth", "realised", 3, min_errors=500)
    summ = bt.pit_summary(pit)
    assert summ["n"] > 3000 and summ["ks"] < 0.03
    first_dates = df["date"].drop_duplicates().iloc[:4]
    assert pit[df["date"].isin(first_dates)].isna().all()    # no completed past errors yet


def test_cycle_test_counts_windows_and_missing_cycles_fail():
    idx = pd.date_range("2019-01-31", "2023-12-31", freq="ME")
    ic = pd.Series(0.05, index=idx)
    ic[(ic.index.year == 2022)] = -0.02
    out = bt.cycle_test(ic)
    assert out["by_cycle"][2020] == pytest.approx(0.05) and out["by_cycle"][2022] == pytest.approx(-0.02)
    assert np.isnan(out["by_cycle"][2008]) and out["cycles_positive"] == 1 and not out["passes"]


# ---------------------------------------------------------------- fair line and look-ahead


def _synthetic_market(rng, n_iss=60, months=30, rho=0.8, a=-4.5, b=0.25):
    """Issuers with leverage and an AR(1) log residual; two bonds each; returns panel and fundamentals history."""
    dates = pd.date_range("2018-01-31", periods=months, freq="ME")
    lev = rng.uniform(1, 8, n_iss)
    eps = np.zeros((months, n_iss))
    eps[0] = rng.normal(0, 0.3, n_iss)
    for t in range(1, months):
        eps[t] = rho * eps[t - 1] + rng.normal(0, 0.3 * np.sqrt(1 - rho ** 2), n_iss)
    rows, fund = [], []
    for t, d in enumerate(dates):
        for i in range(n_iss):
            s = np.exp(a + b * lev[i] + eps[t, i])
            for j, mat in enumerate([3.0, 7.0]):
                rows.append(_row(f"C{i:03d}{j}", d, 100.0, 0.02, g=s, mat=d + pd.DateOffset(years=int(mat)),
                                 gvkey=f"G{i:03d}"))
            fund.append(dict(date=d, gvkey=f"G{i:03d}", leverage=lev[i], available_at=d + pd.Timedelta(days=1)))
    panel = pd.DataFrame(rows)
    panel["years"] = (panel["maturity"] - panel["date"]).dt.days / 365.25
    return panel, pd.DataFrame(fund), eps, dates


def test_fair_line_residuals_and_pooled_rho_recover_the_truth(rng):
    panel, fund, eps, dates = _synthetic_market(rng)
    t = dates[-1]
    p = panel[panel["date"] == t]
    e, fit = bt.fair_line_residuals(p, fund[fund["date"] == t])
    assert fit["b"] == pytest.approx(0.25, abs=0.06)
    truth = pd.Series(eps[-1], index=[f"G{i:03d}" for i in range(eps.shape[1])])
    assert np.corrcoef(e.sort_index(), truth.sort_index())[0, 1] > 0.9
    fl = bt.FairLine(mode="conv", min_pairs=500)
    fl(panel[panel["date"] <= t], fund[fund["date"] <= t], bt.decision_time(t), 3)
    rho, src = fl.rho(t)
    assert bt.FairLine(mode="conv").rho(dates[1]) == (bt.RHO_PRIOR_M, "prior")   # no history: the prior
    assert src == "fitted" and rho == pytest.approx(0.8, abs=0.06)


def test_pooled_rho_equals_fit_ar1_on_one_issuer():
    s = pd.Series([0.5, 0.4, 0.35, 0.2, 0.25, 0.1])
    hist = {d: pd.Series({"G1": v}) for d, v in zip(pd.date_range("2020-01-31", periods=6, freq="ME"), s)}
    assert bt.pooled_rho(hist)[0] == pytest.approx(fit_ar1(s.to_numpy()))


def test_fair_line_alpha_sign_and_formula(rng):
    panel, fund, eps, dates = _synthetic_market(rng)
    t = dates[-1]
    fl = bt.FairLine(mode="conv")
    a = fl(panel[panel["date"] <= t], fund[fund["date"] <= t], bt.decision_time(t), 6)
    rho = fl.rho_log[t][0]
    resid = fl.memo[t]
    bond = panel[(panel["date"] == t)].set_index("cusip")
    c = a.index[0]
    s = bond.loc[c, "g_spread"]
    expect = bond.loc[c, "mod_dur"] * (1 - rho ** 6) * (s - s * np.exp(-resid[bond.loc[c, "gvkey"]]))
    assert a[c] == pytest.approx(expect)
    by_issuer = a.groupby(a.index.str[:4]).mean()
    assert np.corrcoef(by_issuer.sort_index(), eps[-1])[0, 1] > 0.8   # cheap issuers get positive alpha
    net = bt.FairLine(mode="net")(panel[panel["date"] <= t], fund[fund["date"] <= t], bt.decision_time(t), 6)
    gross = bt.FairLine(mode="gross")(panel[panel["date"] <= t], fund[fund["date"] <= t], bt.decision_time(t), 6)
    assert (gross - net).to_numpy() == pytest.approx(0.5 / 100.0)   # round trip = bid-ask points / price


def test_lookahead_fixture_fails(rng):
    panel, fund, _, dates = _synthetic_market(rng, n_iss=20, months=6)
    t = dates[3]
    p_t = panel[panel["date"] <= t].copy()
    f_t = fund[fund["date"] <= t].copy()
    as_of = bt.decision_time(t)
    bt.predict_widest(p_t, f_t, as_of, 3)                     # clean inputs pass
    leak = p_t.copy()
    leak.loc[leak.index[0], "available_at"] = as_of + pd.Timedelta(days=1)
    with pytest.raises(bt.LookAheadError):
        bt.predict_widest(leak, f_t, as_of, 3)
    with pytest.raises(bt.LookAheadError):
        bt.FairLine()(leak, f_t, as_of, 3)
    f_leak = f_t.copy()
    f_leak.loc[f_leak.index[-1], "available_at"] = as_of + pd.Timedelta(days=30)
    with pytest.raises(bt.LookAheadError):
        bt.FairLine()(p_t, f_leak, as_of, 3)
    with pytest.raises(bt.LookAheadError):
        bt.predict_widest(p_t, f_t.drop(columns="available_at"), as_of, 3)
    with pytest.raises(bt.LookAheadError):
        bt.realised_excess_return(panel, 3, as_of=as_of)      # the whole panel is not known at t


def test_replay_sees_only_the_past(rng):
    panel, fund, _, dates = _synthetic_market(rng, n_iss=20, months=8)
    seen = []

    def spy(p, f, as_of, h):
        seen.append((as_of, p["date"].max(), f["date"].max()))
        return bt.predict_widest(p, f, as_of, h)

    out = bt.run_predictions(panel, fund, {"spy": spy, "fair": bt.FairLine()}, 3)
    assert all(pmax < as_of and fmax < as_of for as_of, pmax, fmax in seen)
    assert set(out["predictor"]) == {"spy", "fair"} and out["date"].nunique() == 8
