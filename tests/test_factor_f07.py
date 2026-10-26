"""Tests for hy.factors.f07_merton_ml_forecast: contract, no look-ahead in features and labels, the Merton sign,
edge cases, and a hand check of each formula helper (spec docs/factors/F07-merton-ml-forecast.md, Tests)."""

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from hy.backtest import decision_time
from hy.data.pit import LookAheadError
from hy.factors import f07_merton_ml_forecast as f7

AS_OF = pd.Timestamp("2015-06-30")
N_FIRMS, N_PRIVATE = 30, 5
H_TRUE = np.linspace(0.1, 0.6, N_FIRMS)          # true hedge ratio per firm


def _synthetic(seed: int = 7, start: str = "2010-01-31", end: str = "2016-06-30") -> dict[str, pd.DataFrame]:
    """Two bonds per firm. RS is AR(1) (psi1 can learn it from mom1m). RB = h RS + small noise, so the true
    E_t[RB_t+1] = h * 0.5 * RS_t. The last N_PRIVATE firms have no stock."""
    rng = np.random.default_rng(seed)
    months = pd.date_range(start, end, freq="ME")
    rs = np.zeros((len(months), N_FIRMS))
    for m in range(1, len(months)):
        rs[m] = 0.5 * rs[m - 1] + rng.normal(0, 0.05, N_FIRMS)
    rb = H_TRUE * rs + rng.normal(0, 0.002, rs.shape)
    rows, eq = [], []
    for i in range(N_FIRMS):
        g = f"G{i:02d}"
        for b in range(2):
            px = 100.0 * np.cumprod(1.0 + rb[:, i] + rng.normal(0, 0.001, len(months)))
            for m, t in enumerate(months):
                rows.append({"date": t, "cusip": f"{g}B{b}", "gvkey": g, "years": 5.0, "g_spread": 0.04 + 0.001 * i,
                             "price": px[m], "yield": 0.07, "coupon": 0.0, "maturity": t + pd.DateOffset(years=5),
                             "mod_dur": 4.5, "tsy_yield": 0.0, "bid_ask_pts": 0.5, "n_trades": 5,
                             "par_volume": 1e6 * (1 + b), "carried": False, "accrue_to": t, "hedge_date": t,
                             "available_at": t + pd.Timedelta(1, unit="D")})
        if i < N_FIRMS - N_PRIVATE:
            for m, t in enumerate(months):
                eq.append({"gvkey": g, "datadate": t, "ret": rs[m, i], "available_at": t + pd.Timedelta(1, unit="D")})
    ratings = pd.DataFrame({"gvkey": [f"G{i:02d}" for i in range(N_FIRMS)], "splticrm": ["BB"] * 15 + ["B"] * 15,
                            "datadate": pd.Timestamp("2009-12-31"), "available_at": pd.Timestamp("2010-01-01")})
    ratings = pd.concat([ratings.assign(datadate=t, available_at=t + pd.Timedelta(1, unit="D")) for t in months])
    return {"bond_panel": pd.DataFrame(rows), "equity_monthly": pd.DataFrame(eq), "ratings": ratings}


@pytest.fixture(scope="module")
def panels():
    return _synthetic()


@pytest.fixture(scope="module")
def scored(panels):
    return f7.compute(panels, AS_OF)


# ---------------------------------------------------------------- contract


def test_meta_has_contract_keys():
    assert {"rank", "name", "level", "horizon_months", "needs", "spec", "section"} <= set(f7.META)
    assert f7.META["rank"] == 7 and f7.META["level"] == "issuer" and f7.META["horizon_months"] == 1
    assert {"bond_panel", "equity_monthly"} <= set(f7.META["needs"])


def test_compute_returns_contract_columns_one_row_per_issuer(scored):
    assert list(scored.columns[:4]) == ["date", "gvkey", "score", "available_at"]
    assert set(f7.OUT_COLS) <= set(scored.columns)
    assert scored["gvkey"].is_unique and len(scored) == N_FIRMS
    assert (scored["date"] == AS_OF).all()
    assert (scored["available_at"] <= decision_time(AS_OF)).all()
    assert scored["fit_date"].iloc[0] == pd.Timestamp("2014-12-31")
    assert np.isfinite(scored["score"]).all()


def test_compute_is_deterministic(panels, scored):
    pd.testing.assert_frame_equal(f7.compute(panels, AS_OF), scored)


# ---------------------------------------------------------------- no look-ahead


def test_training_set_holds_no_label_realised_after_fit_decision_time(panels):
    feats = f7.build_features(panels, AS_OF)
    f_at = f7.fit_date(AS_OF)
    assert (feats["bond"]["rb_label_at"] > decision_time(f_at)).any()        # later labels exist; the cut must bite
    st, b = f7.training_set(feats, f_at)
    assert st["label_at"].max() <= decision_time(f_at)
    assert b["label_at"].max() <= decision_time(f_at)
    assert (b["date"] + pd.offsets.MonthEnd(1)).max() <= f_at                 # the return month ends by the fit date
    model = f7.fit(panels, AS_OF)
    assert model.label_through <= decision_time(f_at)


def test_future_and_late_rows_do_not_change_the_score(panels, scored):
    p = {k: v.copy() for k, v in panels.items()}
    bp, eq = p["bond_panel"], p["equity_monthly"]
    later = bp["date"] > AS_OF
    bp.loc[later, "price"] *= 3.0                                             # rows after as_of
    eq.loc[eq["datadate"] > AS_OF, "ret"] = 0.9
    late = bp[bp["date"] == AS_OF].head(4).copy()                             # dated at as_of, published late
    late["price"], late["available_at"] = 1.0, AS_OF + pd.Timedelta(10, unit="D")
    late_eq = eq[eq["datadate"] == AS_OF].head(4).assign(ret=-0.8, available_at=AS_OF + pd.Timedelta(10, unit="D"))
    p["bond_panel"] = pd.concat([bp[bp["date"] != AS_OF], late, bp[bp["date"] == AS_OF]])
    p["equity_monthly"] = pd.concat([late_eq, eq])
    pd.testing.assert_frame_equal(f7.compute(p, AS_OF), scored)


def test_prefitted_model_with_later_labels_raises(panels):
    model = f7.fit(panels, pd.Timestamp("2016-01-31"))
    with pytest.raises(LookAheadError):
        f7.compute(panels, AS_OF, model=model)


def test_prefitted_model_matches_fit_inside_the_call(panels, scored):
    model = f7.fit(panels, AS_OF)
    pd.testing.assert_frame_equal(f7.compute(panels, AS_OF, model=model), scored)


def test_walk_forward_refits_once_a_year(panels):
    months = pd.date_range("2014-11-30", "2015-02-28", freq="ME")
    wf = f7.walk_forward(panels, months)
    assert sorted(wf["fit_date"].unique()) == [pd.Timestamp("2013-12-31"), pd.Timestamp("2014-12-31")]
    one = f7.compute(panels, pd.Timestamp("2015-02-28"))
    pd.testing.assert_frame_equal(wf[wf["date"] == "2015-02-28"].reset_index(drop=True), one)


# ---------------------------------------------------------------- sign


def test_sign_follows_hedge_ratio_times_forecast_stock_return(panels, scored):
    eq = panels["equity_monthly"]
    rs_t = eq[eq["datadate"] == AS_OF].set_index("gvkey")["ret"]
    s = scored[scored["has_equity"]].set_index("gvkey")
    truth = pd.Series(H_TRUE[: N_FIRMS - N_PRIVATE], index=[f"G{i:02d}" for i in range(N_FIRMS - N_PRIVATE)])
    truth = truth * 0.5 * rs_t
    rho = stats.spearmanr(s["score"], truth.reindex(s.index)).statistic
    assert rho > 0.5
    assert stats.spearmanr(s["h_hat"], pd.Series(H_TRUE, index=[f"G{i:02d}" for i in range(N_FIRMS)])
                           .reindex(s.index)).statistic > 0.9


# ---------------------------------------------------------------- edge cases


def test_missing_required_panel_gives_empty_frame(panels):
    for drop in ("equity_monthly", "bond_panel"):
        out = f7.compute({k: v for k, v in panels.items() if k != drop}, AS_OF)
        assert out.empty and list(out.columns) == f7.OUT_COLS


def test_short_history_gives_empty_frame(panels):
    assert f7.compute(panels, pd.Timestamp("2012-06-30")).empty


def test_private_issuer_has_no_hedge_and_scores_on_the_bond_leg(scored):
    priv = scored[scored["gvkey"].isin([f"G{i:02d}" for i in range(N_FIRMS - N_PRIVATE, N_FIRMS)])]
    assert (~priv["has_equity"]).all() and priv["h_hat"].isna().all()
    np.testing.assert_allclose(priv["score"], priv["psi2_bond"])


def test_missing_ratings_and_bond_only_benchmark(panels):
    out = f7.compute({k: v for k, v in panels.items() if k != "ratings"}, AS_OF, bond_only=True)
    assert len(out) == N_FIRMS and np.isfinite(out["f1_bond_only"]).all()


# ---------------------------------------------------------------- formula helpers


def test_hedge_ratio_matches_hand_ols_and_needs_min_obs():
    rng = np.random.default_rng(1)
    idx = pd.date_range("2010-01-31", periods=40, freq="ME")
    rs = pd.DataFrame({"A": rng.normal(0, 0.05, 40)}, index=idx)
    rb = 0.01 + 0.3 * rs + pd.DataFrame({"A": rng.normal(0, 0.01, 40)}, index=idx)
    rb.iloc[5, 0] = np.nan
    h = f7.hedge_ratio(rb, rs)
    w = slice(4, 40)                                                          # months t-35 .. t at t = index 39
    m = rb["A"].iloc[w].notna()
    hand = np.polyfit(rs["A"].iloc[w][m], rb["A"].iloc[w][m], 1)[0]
    assert h["A"].iloc[-1] == pytest.approx(hand, rel=1e-9)
    assert h["A"].iloc[:23].isna().all() and np.isfinite(h["A"].iloc[24])      # 24 pairs from index 24 (one NaN)


def test_rbmrs_and_merton_forecast():
    np.testing.assert_allclose(f7.rbmrs([0.02], [0.4], [0.03]), [0.02 - 0.012])
    np.testing.assert_allclose(f7.merton_forecast([0.4, 0.0], [0.01, 0.05], [0.002, 0.003]), [0.006, 0.003])


def test_downside_risk_hand_values():
    w = np.array([-0.05, -0.03, -0.02, -0.01] + [0.01] * 20)[:, None]
    d = f7.downside_risk(w)
    assert d["var5"][0] == pytest.approx(0.03) and d["var10"][0] == pytest.approx(0.01)
    assert d["es5"][0] == pytest.approx(0.04) and d["es10"][0] == pytest.approx(0.0275)
    assert np.isnan(f7.downside_risk(w[:10])["var5"][0])


def test_return_windows_hand_values():
    idx = pd.date_range("2010-01-31", periods=50, freq="ME")
    r = pd.DataFrame({"A": 0.01}, index=idx)
    r.iloc[-1, 0] = 0.05
    w = f7.return_windows(r)
    assert w["rev"]["A"].iloc[-1] == 0.05
    assert w["mom6"]["A"].iloc[-1] == pytest.approx(1.01 ** 6 - 1)
    assert w["mom12"]["A"].iloc[-1] == pytest.approx(1.01 ** 11 - 1)
    assert w["ltr"]["A"].iloc[-1] == pytest.approx(1.01 ** 36 - 1)
    assert w["ltr"]["A"].iloc[46] != w["ltr"]["A"].iloc[46] and np.isfinite(w["ltr"]["A"].iloc[47])


def test_moments_and_coskew_hand_values():
    rng = np.random.default_rng(3)
    m = rng.normal(0, 0.02, 36)
    y = 0.001 + 0.8 * m + 5.0 * m ** 2
    st = f7.window_stats(pd.DataFrame({"A": y}), pd.Series(m))
    assert st["coskew"]["A"].iloc[-1] == pytest.approx(5.0, rel=1e-6)
    assert st["vol"]["A"].iloc[-1] == pytest.approx(np.std(y, ddof=1))
    assert st["skew"]["A"].iloc[-1] == pytest.approx(np.mean((y - y.mean()) ** 3) / np.std(y, ddof=1) ** 3)
    assert st["vol"]["A"].iloc[:23].isna().all()


def test_rank_features_maps_to_unit_interval_and_missing_to_zero():
    df = pd.DataFrame({"date": [1, 1, 1, 1, 2], "x": [3.0, 1.0, np.nan, 2.0, 5.0]})
    np.testing.assert_allclose(f7.rank_features(df, ["x"])["x"], [1.0, -1.0, 0.0, 0.0, 0.0])


@pytest.mark.parametrize("as_of,refit,expect", [("2015-06-30", 12, "2014-12-31"), ("2015-12-31", 12, "2015-12-31"),
                                                ("2015-06-30", 6, "2015-06-30"), ("2015-06-30", None, "2015-06-30")])
def test_fit_date(as_of, refit, expect):
    assert f7.fit_date(pd.Timestamp(as_of), refit) == pd.Timestamp(expect)
