"""F03 residual equity momentum: contract, no look-ahead, window, lag, compounding, sign, weights, DEF hedge."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from hy.backtest import decision_time
from hy.factors import f03_residual_equity_momentum as f03

AS_OF = pd.Timestamp("2012-06-30")
MONTHS = pd.date_range(end=AS_OF, periods=48, freq="ME")
WIN = f03.window_months(AS_OF)          # 2009-06 .. 2012-05


def _ff(seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    return pd.DataFrame({"date": MONTHS, "mktrf": rng.normal(0.006, 0.045, len(MONTHS)), "rf": 0.001,
                         "available_at": MONTHS + pd.Timedelta(1, unit="D")})


def _equity(ff: pd.DataFrame, betas: dict[str, float], seed: int = 1, shock: dict[str, float] | None = None,
            noise: float = 0.05):
    """ret = rf + beta mktrf + noise; `shock` adds a residual to each of the 6 formation months t-6 .. t-1."""
    rng = np.random.default_rng(seed)
    rows = []
    for g, b in betas.items():
        eps = rng.normal(0.0, noise, len(MONTHS))
        if shock and g in shock:
            eps[(MONTHS >= WIN[-6]) & (MONTHS <= WIN[-1])] += shock[g]
        rows.append(pd.DataFrame({"gvkey": g, "datadate": MONTHS, "ret": ff["rf"] + b * ff["mktrf"] + eps}))
    e = pd.concat(rows, ignore_index=True)
    e["available_at"] = e["datadate"] + pd.Timedelta(1, unit="D")
    return e


def _bonds(gvkeys, per: int = 2, amt: bool = False) -> pd.DataFrame:
    rows = [{"date": AS_OF, "cusip": f"{g}{k}", "gvkey": g, "years": 5.0, "g_spread": 0.04, "price": 95.0 + k,
             "yield": 0.08, "mod_dur": 4.0, "carried": False, "available_at": AS_OF + pd.Timedelta(1, unit="D")}
            for g in gvkeys for k in range(per)]
    b = pd.DataFrame(rows)
    if amt:
        b["amt_out"] = [100.0 * (k + 1) for g in gvkeys for k in range(per)]
    return b


def _panels(betas=None, shock=None):
    betas = betas or {"A": 0.8, "B": 1.2, "C": 1.0}
    ff = _ff()
    return {"ff_factors": ff, "equity_monthly": _equity(ff, betas, shock=shock), "bond_panel": _bonds(betas)}


def _rm(panels, **kw) -> pd.Series:
    s = f03.issuer_scores(panels["equity_monthly"], panels["ff_factors"], AS_OF, **kw)
    return s.set_index("gvkey")["score"]


# ---------------------------------------------------------------- contract


def test_meta_and_columns():
    for k in ("rank", "name", "level", "horizon_months", "needs", "spec", "section"):
        assert k in f03.META
    assert f03.META["rank"] == 3 and "ff_factors" in f03.META["needs"]
    out = f03.compute(_panels(), AS_OF)
    assert list(out.columns[:4]) == ["date", "cusip", "score", "available_at"]
    assert out["cusip"].is_unique and len(out) == 6
    assert (out["date"] == AS_OF).all() and (out["available_at"] == decision_time(AS_OF)).all()
    assert out["score"].notna().all()
    # the issuer score is copied to every bond of the issuer
    assert out.groupby("gvkey")["score"].nunique().eq(1).all()


def test_missing_ff_panel_gives_empty_frame():
    p = _panels()
    for drop in ("ff_factors", "equity_monthly"):
        q = {k: v for k, v in p.items() if k != drop}
        out = f03.compute(q, AS_OF)
        assert out.empty and list(out.columns) == f03.BOND_COLS


# ---------------------------------------------------------------- no look-ahead, window, lag


def test_no_lookahead():
    p = _panels()
    base = f03.compute(p, AS_OF)
    q = dict(p)
    late = p["equity_monthly"].copy()
    late["datadate"] = late["datadate"] + pd.offsets.MonthEnd(3)          # returns dated after as_of
    late["available_at"] = late["datadate"] + pd.Timedelta(1, unit="D")
    # a restatement of a window return, published after the decision time
    restate = p["equity_monthly"][p["equity_monthly"]["datadate"] == WIN[-1]].assign(
        ret=9.0, available_at=AS_OF + pd.Timedelta(30, unit="D"))
    q["equity_monthly"] = pd.concat([p["equity_monthly"], late[late["datadate"] > AS_OF], restate])
    ff_late = p["ff_factors"].assign(mktrf=5.0, available_at=AS_OF + pd.Timedelta(10, unit="D"))
    q["ff_factors"] = pd.concat([p["ff_factors"], ff_late])
    pd.testing.assert_frame_equal(base, f03.compute(q, AS_OF))


def _bump(p, month, g="A", by=0.3):
    e = p["equity_monthly"].copy()
    e.loc[(e["gvkey"] == g) & (e["datadate"] == month), "ret"] += by
    return {**p, "equity_monthly": e}


def test_window_is_36_months():
    p = _panels()
    base = _rm(p)
    assert len(WIN) == 36 and WIN[0] == pd.Timestamp("2009-06-30") and WIN[-1] == pd.Timestamp("2012-05-31")
    assert _rm(_bump(p, WIN[0] - pd.offsets.MonthEnd(1)))["A"] == pytest.approx(base["A"])   # t-37: outside
    assert _rm(_bump(p, WIN[0]))["A"] != pytest.approx(base["A"])                             # t-36: inside


def test_one_month_lag():
    p = _panels()
    base = _rm(p)
    assert _rm(_bump(p, AS_OF))["A"] == pytest.approx(base["A"])         # month t is skipped
    assert _rm(_bump(p, AS_OF), skip=0)["A"] != pytest.approx(base["A"])  # the 0-skip check reads month t
    assert _rm(_bump(p, WIN[-1]))["A"] > base["A"]                       # t-1 is the last formation month


def test_minimum_observations():
    p = _panels()
    e = p["equity_monthly"]
    gap = e[~((e["gvkey"] == "A") & (e["datadate"] == WIN[10]))]       # one missing return inside the window
    q = {**p, "equity_monthly": gap}
    rm = _rm(q)
    assert "A" not in rm.index and {"B", "C"} <= set(rm.index)
    out = f03.compute(q, AS_OF)
    assert out.loc[out["gvkey"] == "A", "score"].isna().all()           # bonds stay, with no score
    assert out.loc[out["gvkey"] != "A", "score"].notna().all()
    assert "A" in _rm(q, min_obs=35).index                               # a looser floor fits on 35 months
    # a missing RMRF month leaves 35 months: nobody reaches 36
    ff = p["ff_factors"][p["ff_factors"]["date"] != WIN[3]]
    assert _rm({**p, "ff_factors": ff}).empty
    # a missing formation month of RMRF stops every score
    ff = p["ff_factors"][p["ff_factors"]["date"] != WIN[-1]]
    assert _rm({**p, "ff_factors": ff}, min_obs=30).empty


# ---------------------------------------------------------------- formula helpers


def test_market_residuals_match_ols():
    p = _panels()
    ff = p["ff_factors"].set_index("date").loc[WIN]
    e = p["equity_monthly"].pivot(index="datadate", columns="gvkey", values="ret").loc[WIN].sub(ff["rf"], axis=0)
    resid, beta = f03.market_residuals(e, ff["mktrf"])
    for g in e.columns:
        b, a = np.polyfit(ff["mktrf"], e[g], 1)
        assert beta[g] == pytest.approx(b)
        np.testing.assert_allclose(resid[g], e[g] - a - b * ff["mktrf"], atol=1e-12)
    assert beta["B"] > beta["A"]                                         # true betas 1.2 and 0.8


def test_residuals_compound_not_sum():
    eps = np.array([-0.1, 0.1] * 15 + [0.1] * 6)
    rm, sd = f03.residual_momentum(pd.DataFrame({"x": eps}))
    sd_hand = np.std(eps, ddof=1)
    assert sd["x"] == pytest.approx(sd_hand)
    assert rm["x"] == pytest.approx((1.1 ** 6 - 1) / sd_hand)            # 0.771561 / sd
    assert rm["x"] != pytest.approx(0.6 / sd_hand)                       # the sum would give 0.6 / sd


# ---------------------------------------------------------------- sign and neutrality


def test_sign_positive_residual_shock_ranks_top():
    betas = {f"G{i:02d}": 0.5 + i * 0.05 for i in range(20)}
    ff = _ff()
    e = _equity(ff, betas, shock={"G05": 0.06, "G12": -0.06}, noise=0.02)
    rm = f03.issuer_scores(e, ff, AS_OF).set_index("gvkey")["score"]
    top, bottom = rm.nlargest(2).index, rm.nsmallest(2).index            # top and bottom decile of 20 issuers
    assert "G05" in top and "G12" in bottom


def test_market_neutral():
    betas = {f"G{i:03d}": b for i, b in enumerate(np.linspace(0.2, 2.0, 200))}
    ff = _ff()
    s = f03.issuer_scores(_equity(ff, betas), ff, AS_OF).set_index("gvkey")["score"]
    assert abs(np.corrcoef(s, pd.Series(betas)[s.index])[0, 1]) < 0.2


# ---------------------------------------------------------------- weights inside a company


def test_company_weights():
    b = _bonds(["A", "B"], per=2, amt=True)
    w = f03.company_weights(b)
    mv = b["price"] * b["amt_out"]
    assert w.loc[0, "weight"] == pytest.approx(mv[0] / (mv[0] + mv[1]))   # 9500 / 29700
    assert (w["weight_basis"] == "mv").all()
    b.loc[3, "amt_out"] = np.nan                                           # B lacks one amount: equal weights
    w = f03.company_weights(b)
    assert list(w["weight_basis"]) == ["mv", "mv", "equal", "equal"] and w.loc[2, "weight"] == 0.5
    w = f03.company_weights(_bonds(["A"], per=4))                          # no amt_out column
    assert (w["weight"] == 0.25).all() and (w["weight_basis"] == "equal").all()
    out = f03.compute(_panels(), AS_OF)
    assert out.groupby("gvkey")["weight"].sum().eq(1.0).all()


# ---------------------------------------------------------------- DEF hedge


def test_def_hedge_rolling_past_window():
    rng = np.random.default_rng(3)
    idx = pd.date_range("2005-01-31", periods=60, freq="ME")
    d = pd.Series(rng.normal(0.004, 0.03, 60), idx)
    ls = -0.5 * d + rng.normal(0.0, 0.005, 60)
    h = f03.def_hedge(ls, d)
    assert h["def_beta"].iloc[:36].isna().all() and h["def_beta"].iloc[36:].notna().all()
    k = 40
    past_ls, past_d = ls.iloc[k - 36:k], d.iloc[k - 36:k]                  # months t-36 .. t-1 only
    b = np.cov(past_ls, past_d)[0, 1] / np.var(past_d, ddof=1)
    assert h["def_beta"].iloc[k] == pytest.approx(b)
    assert h["ls_hedged"].iloc[k] == pytest.approx(ls.iloc[k] - b * d.iloc[k])
    assert h["def_beta"].iloc[36:].between(-0.6, -0.4).all()
    # month t's own return does not enter beta_t
    ls2 = ls.copy()
    ls2.iloc[k] += 1.0
    assert f03.def_hedge(ls2, d)["def_beta"].iloc[k] == pytest.approx(b)


def test_default_factor_is_equal_weight_mean():
    dates = pd.date_range("2012-01-31", periods=3, freq="ME")
    rows = []
    for c, px in (("X", [100.0, 101.0, 102.0]), ("Y", [90.0, 89.0, 91.0])):
        for d, p in zip(dates, px):
            rows.append({"cusip": c, "date": d, "gvkey": c, "years": 5.0, "price": p, "coupon": 0.06,
                         "yield": 0.07, "tsy_yield": 0.02, "mod_dur": 4.0, "g_spread": 0.05, "carried": False,
                         "accrue_to": d, "hedge_date": d, "bid_ask_pts": 0.5,
                         "available_at": d + pd.Timedelta(1, unit="D")})
    panel = pd.DataFrame(rows)
    as_of = dates[-1] + pd.Timedelta(1, unit="D")
    d = f03.default_factor(panel, as_of)
    tau = (dates[1] - dates[0]).days / 365.25
    x = (101.0 - 100.0 + 100 * 0.06 * tau) / 100.0 - 0.02 * tau
    y = (89.0 - 90.0 + 100 * 0.06 * tau) / 90.0 - 0.02 * tau
    assert d.name == "def_xr" and d[dates[0]] == pytest.approx((x + y) / 2)


def test_no_usable_rows_gives_nan_scores():
    p = _panels()
    early = pd.Timestamp("2007-12-31")                                   # before any equity or factor row
    e = p["equity_monthly"].assign(available_at=AS_OF + pd.Timedelta(90, unit="D"))
    out = f03.compute({**p, "equity_monthly": e}, AS_OF)
    assert len(out) == 6 and out["score"].isna().all()
    assert f03.issuer_scores(p["equity_monthly"], p["ff_factors"], early).empty
