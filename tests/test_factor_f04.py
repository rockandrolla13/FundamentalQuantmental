"""F04 bond momentum: contract, no look-ahead, volatility adjustment, DTS residual, TRACE gaps, stale and carried
rows, defaulted bonds, missing panels, formula helpers, evaluation grid and the four-branch decision rule."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from hy.backtest import decision_time, realised_excess_return
from hy.data.pit import LookAheadError
from hy.factors import f04_bond_momentum as f04

AS_OF = pd.Timestamp("2012-12-31")
MONTHS = pd.date_range(end=AS_OF, periods=20, freq="ME")      # 2011-05 .. 2012-12
FORM_M = pd.date_range(end="2012-11-30", periods=6, freq="ME")  # 2012-06 .. 2012-11
DAY = pd.Timedelta(1, unit="D")


def _bond(cusip: str, gvkey: str, rets, mod_dur: float = 4.0, g_spread: float = 0.05, drop=(), n_trades: int = 5,
          price0: float = 100.0) -> pd.DataFrame:
    """Rows per month end. Coupon 0 and Treasury yield 0, so r_ex is the price return: P_m = P_m-1 (1 + r_m)."""
    rets = np.asarray(rets, float)
    price = price0 * np.cumprod(1.0 + np.r_[0.0, rets[1:]])
    df = pd.DataFrame({"date": MONTHS, "cusip": cusip, "gvkey": gvkey, "years": 5.0, "g_spread": g_spread,
                       "price": price, "yield": 0.08, "coupon": 0.0, "maturity": AS_OF + pd.DateOffset(years=5),
                       "mod_dur": mod_dur, "tsy_yield": 0.0, "bid_ask_pts": 0.5, "n_trades": n_trades,
                       "par_volume": 1e6, "carried": False, "accrue_to": MONTHS, "hedge_date": MONTHS,
                       "available_at": MONTHS + DAY})
    return df[~df["date"].isin(pd.DatetimeIndex(drop))].reset_index(drop=True)


def _ratings(gvkeys, symbol: str = "B", over: dict | None = None) -> pd.DataFrame:
    rows = [{"gvkey": g, "datadate": m, "splticrm": (over or {}).get(g, symbol), "available_at": m + DAY}
            for g in gvkeys for m in MONTHS]
    return pd.DataFrame(rows)


def _gics(gvkeys, sector: str = "20") -> pd.DataFrame:
    return pd.DataFrame({"gvkey": list(gvkeys), "gsector": sector, "indfrom": pd.Timestamp("2000-01-01"),
                         "indthru": pd.NaT, "available_at": pd.Timestamp("2000-01-02")})


def _universe(n: int = 10, seed: int = 0) -> dict:
    rng = np.random.default_rng(seed)
    bonds = [_bond(f"C{i}", f"G{i}", rng.normal(0.003, 0.01 + 0.002 * i, len(MONTHS)), mod_dur=3.0 + 0.3 * i)
             for i in range(n)]
    g = [f"G{i}" for i in range(n)]
    return {"bond_panel": pd.concat(bonds, ignore_index=True), "ratings": _ratings(g), "gics": _gics(g)}


def _run(panels, **kw) -> pd.DataFrame:
    return f04.compute(panels, AS_OF, **kw).set_index("cusip")


# ---------------------------------------------------------------- 1. contract


def test_meta_and_columns():
    for k in ("rank", "name", "level", "horizon_months", "needs", "spec", "section"):
        assert k in f04.META
    assert f04.META["rank"] == 4 and f04.META["level"] == "bond" and f04.META["horizon_months"] == 6
    out = f04.compute(_universe(), AS_OF)
    assert list(out.columns) == f04.COLS
    assert out["cusip"].is_unique and len(out) == 10
    assert (out["date"] == AS_OF).all() and (out["available_at"] == decision_time(AS_OF)).all()
    assert out["score"].notna().all() and abs(out["score"].mean()) < 1e-9
    # the score is the standardised rank of vamom
    assert out["score"].rank().tolist() == out["vamom"].rank().tolist()


# ---------------------------------------------------------------- 2. no look-ahead


def test_later_rows_and_late_revisions_do_not_change_score():
    base = _universe()
    ref = _run(base)
    p = base["bond_panel"]
    later = p[p["date"] == AS_OF].copy()
    later["date"] = AS_OF + pd.offsets.MonthEnd(1)
    later["available_at"] = later["date"] + DAY
    late_rev = p[p["date"] == FORM_M[-1]].copy()
    late_rev["price"] *= 1.3                                     # a revision known only after the decision time
    late_rev["available_at"] = AS_OF + pd.Timedelta(10, unit="D")
    late_rating = _ratings(["G0"], "D").assign(available_at=AS_OF + pd.Timedelta(5, unit="D"))
    panels = {**base, "bond_panel": pd.concat([p, later, late_rev], ignore_index=True),
              "ratings": pd.concat([base["ratings"], late_rating], ignore_index=True)}
    pd.testing.assert_frame_equal(_run(panels), ref)


def test_month_t_return_is_skipped():
    base = _universe()
    p = base["bond_panel"].copy()
    p.loc[p["date"] == AS_OF, "price"] *= 1.10                  # change the month-T return only
    pd.testing.assert_frame_equal(_run({**base, "bond_panel": p}), _run(base))


def test_helper_guard_raises_on_late_row():
    p = _bond("X", "GX", np.full(len(MONTHS), 0.01))
    p.loc[len(p) - 1, "available_at"] = AS_OF + pd.Timedelta(3, unit="D")
    with pytest.raises(LookAheadError):
        f04.monthly_excess_returns(p, decision_time(AS_OF))


# ---------------------------------------------------------------- 3. sign and volatility adjustment


def _path(form_ret: float, other: float) -> np.ndarray:
    """Formation months earn form_ret; the other vol-window months alternate +other, -other."""
    r = np.zeros(len(MONTHS))
    vol_m = pd.date_range(end="2012-11-30", periods=12, freq="ME")
    alt = 1.0
    for i, m in enumerate(MONTHS):
        if m in FORM_M:
            r[i] = form_ret
        elif m in vol_m or m < vol_m[0]:
            r[i], alt = alt * other, -alt
    return r


def test_vol_adjustment_reorders_raw_momentum():
    a = _bond("A", "GA", _path(0.01, 0.06))                     # +6%, sigma about 4%
    b = _bond("B", "GB", _path(0.005, 0.006))                   # +3%, sigma about 0.5%
    fill = [_bond(f"F{i}", f"GF{i}", _path(0.0, 0.02 + 0.002 * i)) for i in range(6)]
    g = ["GA", "GB"] + [f"GF{i}" for i in range(6)]
    out = _run({"bond_panel": pd.concat([a, b, *fill], ignore_index=True), "ratings": _ratings(g), "gics": _gics(g)})
    assert out.loc["A", "raw_mom"] == pytest.approx(0.06) and out.loc["B", "raw_mom"] == pytest.approx(0.03)
    assert out.loc["A", "raw_mom"] > out.loc["B", "raw_mom"]
    assert out.loc["B", "vamom"] > out.loc["A", "vamom"]
    assert out.loc["B", "score"] > out.loc["A", "score"]
    assert out.loc["A", "mom_sigma"] == pytest.approx(np.std(_path(0.01, 0.06)[-13:-1], ddof=1))


def test_equal_sigma_higher_return_ranks_higher():
    hi = _bond("H", "GH", _path(0.01, 0.02))
    lo = _bond("L", "GL", _path(-0.01, 0.02))
    out = _run({"bond_panel": pd.concat([hi, lo], ignore_index=True), "ratings": _ratings(["GH", "GL"]),
                "gics": _gics(["GH", "GL"])})
    assert out.loc["H", "mom_sigma"] == pytest.approx(out.loc["L", "mom_sigma"])
    assert out.loc["H", "vamom"] > 0 > out.loc["L", "vamom"]


def test_residual_removes_dts_beta():
    rng = np.random.default_rng(3)
    lam = rng.normal(0.0, 0.01, len(MONTHS))                    # the cell's return per unit of DTS each month
    bonds, g = [], []
    for i in range(6):
        mod_dur = 2.0 + i
        bonds.append(_bond(f"P{i}", f"GP{i}", lam * mod_dur * 0.05, mod_dur=mod_dur))
        g.append(f"GP{i}")
    own = lam * 4.0 * 0.05 + np.where(MONTHS.isin(FORM_M), 0.01, 0.0)  # +1% a month of own return
    bonds.append(_bond("T", "GT", own, mod_dur=4.0))
    g.append("GT")
    panels = {"bond_panel": pd.concat(bonds, ignore_index=True), "ratings": _ratings(g), "gics": _gics(g)}
    pairs = f04.monthly_excess_returns(panels["bond_panel"], decision_time(AS_OF))
    keys = f04.cell_keys(pd.Series("B", index=pairs.index), pd.Series("20", index=pairs.index))
    eps = f04.dts_residuals(pairs, keys)
    assert eps[pairs["cusip"] != "T"].abs().max() < 1e-12
    t = pairs["cusip"] == "T"
    assert eps[t & pairs["date"].isin(FORM_M)].to_numpy() == pytest.approx(0.01)
    out = _run(panels)
    assert out.loc["T", "rmom"] > 0
    assert out.drop("T")["rmom"].isna().all()                   # zero residual sd: no residual score


# ---------------------------------------------------------------- 4. sparse trades, stale and carried rows


def test_two_month_gap_spreads_evenly():
    r = np.full(len(MONTHS), 0.01)
    p = _bond("X", "GX", r, drop=[FORM_M[2]])                     # no row in 2012-08
    pairs = f04.monthly_excess_returns(p, decision_time(AS_OF))
    gap = pairs[pairs["gap_k"] == 2].iloc[0]
    assert gap["date"] == FORM_M[3] and gap["r_ex"] == pytest.approx(1.01 ** 2 - 1)
    sm = f04.spread_months(pairs.loc[[gap.name]], "r_ex")
    assert list(sm["month"]) == [FORM_M[2], FORM_M[3]] and sm["value"].to_numpy() == pytest.approx((1.01 ** 2 - 1) / 2)
    fs = f04.formation_sum(pairs, "r_ex", FORM_M)
    assert fs.loc["X", "n"] == 6 and fs.loc["X", "total"] == pytest.approx(4 * 0.01 + (1.01 ** 2 - 1))
    v = f04.vol_estimate(pairs, "r_ex", pd.date_range(end="2012-11-30", periods=12, freq="ME"))
    assert v.loc["X", "n"] == 11                                 # the gap gives one sigma observation


def test_four_month_gap_leaves_months_missing_and_four_of_six_is_nan():
    r = np.full(len(MONTHS), 0.01)
    drop = pd.date_range("2012-04-30", periods=3, freq="ME")    # rows at 2012-03 and 2012-07: a 4-month gap
    p = _bond("X", "GX", r, drop=drop)
    pairs = f04.monthly_excess_returns(p, decision_time(AS_OF))
    assert not (pairs["date"] == pd.Timestamp("2012-07-31")).any()
    fs = f04.formation_sum(pairs, "r_ex", FORM_M)
    assert fs.loc["X", "n"] == 4                                 # 2012-06 and 2012-07 missing
    others = [_bond(f"O{i}", f"GO{i}", _path(0.0, 0.01 + 0.001 * i)) for i in range(5)]
    g = ["GX"] + [f"GO{i}" for i in range(5)]
    out = _run({"bond_panel": pd.concat([p, *others], ignore_index=True), "ratings": _ratings(g), "gics": _gics(g)})
    assert out.loc["X", "mom_n_form"] == 4 and np.isnan(out.loc["X", "score"]) and np.isnan(out.loc["X", "vamom"])
    assert out.drop("X")["score"].notna().all()


def test_carried_and_stale_rows_never_enter_formation():
    r = np.full(len(MONTHS), 0.01)
    p = _bond("X", "GX", r)
    p.loc[p["date"] == FORM_M[1], ["carried", "price"]] = [True, 150.0]   # a carried row with a wild price
    pairs = f04.monthly_excess_returns(p, decision_time(AS_OF))
    assert not (pairs["date"] == FORM_M[1]).any() and not (pairs["start"] == FORM_M[1]).any()
    gap = pairs[pairs["date"] == FORM_M[2]].iloc[0]
    assert gap["gap_k"] == 2 and gap["r_ex"] == pytest.approx(1.01 ** 2 - 1)
    s = _bond("S", "GS", r)
    i = s.index[s["date"] == FORM_M[3]][0]
    s.loc[i, ["price", "n_trades"]] = [s.loc[i - 1, "price"], 1]          # one trade at the prior price
    assert f04.mark_stale(s).tolist() == [k == i for k in s.index]
    sp = f04.monthly_excess_returns(s, decision_time(AS_OF))
    assert sp.loc[sp["date"] == FORM_M[4], "gap_k"].iloc[0] == 2


# ---------------------------------------------------------------- 5. defaulted and flat bonds


def test_flat_and_defaulted_bonds_are_not_scored():
    base = _universe()
    p = base["bond_panel"].copy()
    p.loc[(p["cusip"] == "C1") & (p["date"] == AS_OF), "yield"] = np.nan   # trades flat
    rat = _ratings([f"G{i}" for i in range(10)], over={"G2": "D", "G3": "SD", "G4": "BBB"})
    out = _run({**base, "bond_panel": p, "ratings": rat})
    assert not {"C1", "C2", "C3", "C4"} & set(out.index)
    assert len(out) == 6


def test_held_bond_that_defaults_ends_at_its_last_price():
    p = _bond("X", "GX", np.full(len(MONTHS), 0.0))
    last = p.index[p["date"] == FORM_M[2]][0]
    p.loc[last, "price"] = 60.0
    p = p.loc[:last].copy()
    carry = p.iloc[[-1]].copy()
    carry["date"] = FORM_M[3]
    carry["available_at"] = carry["date"] + DAY
    carry["carried"] = True                                       # trace_panel rule 5: one carried exit row
    q = pd.concat([p, carry], ignore_index=True)
    xr = realised_excess_return(q, 6, decision_time(AS_OF), beta=0.0,
                                bench=pd.Series(0.0, index=pd.DatetimeIndex(q["date"].unique())))
    row = xr[xr["date"] == FORM_M[0]].iloc[0]
    assert row["end_carried"] and row["total"] == pytest.approx(60.0 / 100.0 - 1.0)


# ---------------------------------------------------------------- 6. missing panels


def test_missing_panels():
    base = _universe()
    assert list(f04.compute({**base, "ratings": None}, AS_OF).columns) == f04.COLS
    assert f04.compute({"ratings": base["ratings"]}, AS_OF).empty
    out = f04.compute({"bond_panel": base["bond_panel"], "ratings": base["ratings"]}, AS_OF)   # no gics, no equity
    assert len(out) == 10 and out["score"].notna().all() and out["sector"].isna().all()
    assert out["rmom"].notna().all()                             # the cell falls back to the rating class


def test_unrated_bond_without_leverage_is_not_scored():
    base = _universe()
    rat = base["ratings"][base["ratings"]["gvkey"] != "G0"]
    assert "C0" not in set(f04.compute({**base, "ratings": rat}, AS_OF)["cusip"])


# ---------------------------------------------------------------- formula helpers


def test_vol_observation_and_floor():
    pairs = pd.DataFrame({"r_ex": [0.04, 0.01], "gap_k": [2, 1]})
    assert f04.vol_observations(pairs, "r_ex").tolist() == pytest.approx([0.04 / np.sqrt(2), 0.01])
    s = pd.Series([0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.0, np.nan])
    fl = f04.floor_sigma(s)
    q = 0.01 + 0.9 * 0.01                                        # 10th percentile of 0.01 .. 0.10, linear
    assert fl.iloc[0] == pytest.approx(q) and fl.iloc[1] == pytest.approx(0.02)
    assert np.isnan(fl.iloc[10]) and np.isnan(fl.iloc[11])


def test_cell_lambdas_median_and_issuer_count():
    m = pd.Series([AS_OF] * 6)
    key = pd.Series(["B|20"] * 5 + ["CCC|20"])
    r = pd.Series([0.01, 0.02, 0.03, 0.04, 0.05, 0.10])
    dts = pd.Series([0.1, 0.2, 0.1, 0.1, 0.5, 0.2])              # r / dts = 0.1, 0.1, 0.3, 0.4, 0.1, 0.5
    lam = f04.cell_lambdas(m, key, r, dts, pd.Series([f"G{i}" for i in range(6)]))
    assert lam.loc[(AS_OF, "B|20")] == pytest.approx(0.1) and (AS_OF, "CCC|20") not in lam.index
    same = f04.cell_lambdas(m, key, r, dts, pd.Series(["G0"] * 3 + ["G1"] * 3))
    assert same.empty                                            # two issuers: below MIN_PEERS


def test_momentum_ratio_counts_and_leg_weights():
    out = f04.momentum_ratio(pd.Series([0.06, 0.06, 0.06]), pd.Series([0.02, 0.02, 0.02]),
                             pd.Series([6, 4, 6]), pd.Series([12, 12, 7]))
    assert out.iloc[0] == pytest.approx(3.0) and out.iloc[1:].isna().all()
    w = f04.leg_weights(pd.Series([0.01, 0.02, 0.04]))
    assert w.tolist() == pytest.approx([4 / 7, 2 / 7, 1 / 7])


# ---------------------------------------------------------------- evaluation grid and decision rule


def test_evaluation_grid_and_mask():
    assert len(f04.evaluation_grid(include_rating_cells=False)) == 3 * 2 * 4
    grid = f04.evaluation_grid()
    assert len(grid) == 3 * 2 * 7
    assert {c["column"] for c in grid} == {"raw_mom", "vamom", "rmom"} and {c["h"] for c in grid} == {1, 6}
    df = pd.DataFrame({"rclass": ["BB", "B", "CCC", "CCC", "IG"], "g_spread": [0.03, 0.12, 0.15, 0.25, 0.01]})
    cell = {c["subset"]: c for c in grid if c["signal"] == "va" and c["h"] == 6}
    assert f04.grid_mask(df, cell["all"]).tolist() == [True, True, True, True, False]
    assert f04.grid_mask(df, cell["lt1000"]).tolist() == [True, False, False, False, False]
    assert f04.grid_mask(df, cell["lt2000"]).tolist() == [True, True, True, False, False]
    assert f04.grid_mask(df, cell["ex_ccc"]).tolist() == [True, True, False, False, False]
    assert f04.grid_mask(df, cell["bb"]).tolist() == [True, False, False, False, False]


def test_ic_row():
    ic = pd.Series(0.05, index=pd.date_range("2008-01-31", "2022-12-31", freq="ME"))
    row = f04.ic_row(ic)
    assert row["mean_ic"] == pytest.approx(0.05) and all(row[f"ic_{y}"] == pytest.approx(0.05)
                                                         for y in (2008, 2015, 2020, 2022))


def _table(rows: dict) -> pd.DataFrame:
    """rows: (signal, h, subset) -> (mean_ic, t_hac, [ic per window]). Missing cells are weak and insignificant."""
    out = []
    for c in f04.evaluation_grid():
        mean, t, win = rows.get((c["signal"], c["h"], c["subset"]), (0.0, 0.0, [0.0] * 4))
        out.append({"signal": c["signal"], "h": c["h"], "subset": c["subset"], "mean_ic": mean, "t_hac": t,
                    **{f"ic_{y}": w for y, w in zip((2008, 2015, 2020, 2022), win)}})
    return pd.DataFrame(out)


GOOD = (0.04, 3.0, [0.03, 0.05, 0.02, -0.01])
BETTER = (0.06, 3.5, [0.05, 0.07, 0.04, -0.02])


def test_choose_branch_on_toy_tables():
    va_only = {("va", 6, "all"): GOOD, ("va", 6, "lt1000"): GOOD, ("va", 6, "bb"): GOOD}
    assert f04.choose_branch(_table(va_only)) == {**f04.choose_branch(_table(va_only)), "branch": 1, "leg": "vamom"}
    rs_wins = {**va_only, ("resid", 6, "all"): BETTER, ("resid", 6, "lt1000"): BETTER}
    assert f04.choose_branch(_table(rs_wins))["branch"] == 2 and f04.choose_branch(_table(rs_wins))["leg"] == "rmom"
    rs_mean_only = {**va_only, ("resid", 6, "all"): (0.05, 3.0, [0.02, 0.04, 0.01, -0.01])}  # higher mean, 1 of 4
    assert f04.choose_branch(_table(rs_mean_only))["branch"] == 1
    kelly = {("raw", 1, "all"): (-0.03, -2.5, [-0.02] * 4)}
    assert f04.choose_branch(_table(kelly)) == {**f04.choose_branch(_table(kelly)), "branch": 3, "leg": None}
    distress = {("va", 6, "all"): GOOD, ("va", 6, "bb"): GOOD, ("va", 6, "lt1000"): (0.01, 0.8, [0.01, 0, 0, 0])}
    assert f04.choose_branch(_table(distress))["branch"] == 4
    no_bb = {("va", 6, "all"): GOOD, ("va", 6, "lt1000"): GOOD, ("va", 6, "bb"): (-0.01, -0.5, [0.0] * 4)}
    assert f04.choose_branch(_table(no_bb)) == {**f04.choose_branch(_table(no_bb)), "branch": 0, "leg": None}
