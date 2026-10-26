"""F21 refinancing headroom: contract, no look-ahead, sign, flags, edge cases, helpers against hand computations."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from hy.backtest import decision_time
from hy.factors import f21_refinancing_headroom as f21

AS_OF = pd.Timestamp("2012-06-30")
DT = decision_time(AS_OF)
# FY2011 (Dec year end) is known at 2012-03-30


def _row(gvkey: str, fy: int, **v) -> dict:
    d = pd.Timestamp(f"{fy}-12-31")
    return {"gvkey": gvkey, "datadate": d, "fyear": fy, "available_at": d + pd.Timedelta(90, unit="D"), **v}


def _balance(gvkey: str, fy: int = 2011, che=20.0, xint=20.0, capx=30.0, dd1=40.0, dd2=40.0, **extra) -> dict:
    return _row(gvkey, fy, che=che, xint=xint, capx=capx, dd1=dd1, dd2=dd2, dd3=10.0, dd4=10.0, dd5=10.0, **extra)


def _ebitda(gvkey: str, path: dict[int, float], debt: float = 400.0) -> list[dict]:
    return [_row(gvkey, fy, oibdp=e, debt=debt) for fy, e in path.items()]


STABLE = {y: 100.0 for y in range(2001, 2012)}                          # never falls: C = 0
CYCLIC = {**{y: 100.0 for y in range(2001, 2012)}, 2009: 50.0}          # worst fall -50% in 2009: C = 0.5


def _bonds(gvkeys, per: int = 2) -> pd.DataFrame:
    return pd.DataFrame([{"date": AS_OF, "cusip": f"{g}{k}", "gvkey": g, "years": 5.0, "g_spread": 0.04,
                          "price": 95.0, "yield": 0.08, "mod_dur": 4.0, "carried": False, "available_at": DT}
                         for g in gvkeys for k in range(per)])


def _gics(sectors: dict[str, str]) -> pd.DataFrame:
    return pd.DataFrame([{"gvkey": g, "gsector": s, "indfrom": pd.Timestamp("2000-01-01"), "indthru": pd.NaT,
                          "available_at": pd.Timestamp("2000-01-01")} for g, s in sectors.items()])


def _panels(balance=None, ebitda=None, sectors=None):
    balance = balance if balance is not None else pd.DataFrame(
        [_balance("SAFE", che=200.0, revolver_undrawn=50.0), _balance("RISK", che=0.0, revolver_undrawn=0.0)])
    ebitda = ebitda if ebitda is not None else pd.DataFrame(_ebitda("SAFE", STABLE) + _ebitda("RISK", CYCLIC))
    keys = sorted(balance["gvkey"].unique())
    sectors = sectors or {g: "20" for g in keys}
    return {"compustat_annual": balance, "annual_ebitda": ebitda, "gics": _gics(sectors), "bond_panel": _bonds(keys)}


def _score(out: pd.DataFrame, col: str = "score") -> pd.Series:
    return out.drop_duplicates("gvkey").set_index("gvkey")[col]


# ---------------------------------------------------------------- contract


def test_meta_and_columns():
    for k in ("rank", "name", "level", "horizon_months", "needs", "spec", "section"):
        assert k in f21.META
    assert f21.META["rank"] == 21 and f21.META["spec"] == "docs/factors/F21-refinancing-headroom.md"
    out = f21.compute(_panels(), AS_OF)
    assert list(out.columns) == f21.BOND_COLS
    assert out["cusip"].is_unique and len(out) == 4
    assert (out["date"] == AS_OF).all() and (out["available_at"] == DT).all()
    assert out["score"].notna().all() and (out["fyear"] == 2011).all()
    assert out.groupby("gvkey")["score"].nunique().eq(1).all()


@pytest.mark.parametrize("drop", ["compustat_annual", "annual_ebitda", "gics", "bond_panel"])
def test_missing_panel_gives_empty_frame(drop):
    p = {k: v for k, v in _panels().items() if k != drop}
    out = f21.compute(p, AS_OF)
    assert out.empty and list(out.columns) == f21.BOND_COLS


# ---------------------------------------------------------------- no look-ahead


def test_no_lookahead():
    base = f21.compute(_panels(), AS_OF)
    p = _panels()
    late = pd.DataFrame([_balance("SAFE", fy=2012, che=0.0), _balance("RISK", fy=2012, che=1e6)])
    p["compustat_annual"] = pd.concat([p["compustat_annual"], late], ignore_index=True)
    # filed before the decision time, but datadate + 90 days lies after it
    early = _balance("RISK", fy=2012, che=1e6)
    early.update(datadate=pd.Timestamp("2012-05-31"), available_at=pd.Timestamp("2012-06-15"))
    p["compustat_annual"] = pd.concat([p["compustat_annual"], pd.DataFrame([early])], ignore_index=True)
    p["annual_ebitda"] = pd.concat([p["annual_ebitda"], pd.DataFrame(_ebitda("SAFE", {2012: 1.0}))],
                                   ignore_index=True)
    extra = _bonds(["SAFE"]).assign(date=AS_OF + pd.offsets.MonthEnd(1), available_at=DT + pd.Timedelta(31, "D"))
    p["bond_panel"] = pd.concat([p["bond_panel"], extra], ignore_index=True)
    pd.testing.assert_frame_equal(f21.compute(p, AS_OF), base)


# ---------------------------------------------------------------- sign


def test_sign_safe_above_risky():
    s = _score(f21.compute(_panels(), AS_OF))
    assert s["SAFE"] > 0 > s["RISK"]


def test_more_cash_raises_score():
    lo = _score(f21.compute(_panels(), AS_OF))["RISK"]
    bal = pd.DataFrame([_balance("SAFE", che=200.0), _balance("RISK", che=40.0)])
    hi = _score(f21.compute(_panels(balance=bal), AS_OF))["RISK"]
    assert hi > lo


# ---------------------------------------------------------------- edges and flags


def test_revolver_and_maturity_flags():
    bal = pd.DataFrame([_balance("SAFE", che=200.0, dd2=np.nan), _balance("RISK", che=0.0)])
    out = f21.compute(_panels(balance=bal), AS_OF).drop_duplicates("gvkey").set_index("gvkey")
    assert out["revolver_missing"].all()
    assert out.loc["SAFE", "mat_missing"] and not out.loc["RISK", "mat_missing"]
    assert out.loc["SAFE", "mat_2y"] == 40.0 and out.loc["SAFE", "mat_3_5y"] == 30.0


def test_use_revolver_false_ignores_it():
    bal = pd.DataFrame([_balance("SAFE", che=0.0, revolver_undrawn=100.0), _balance("RISK", che=0.0)])
    with_rcf = _score(f21.compute(_panels(balance=bal), AS_OF), "headroom")["SAFE"]
    without = _score(f21.compute(_panels(balance=bal), AS_OF, use_revolver=False), "headroom")["SAFE"]
    assert with_rcf > without


def test_financial_issuer_gets_nan():
    out = f21.compute(_panels(sectors={"SAFE": "40", "RISK": "20"}), AS_OF)
    s = _score(out)
    assert np.isnan(s["SAFE"]) and np.isfinite(s["RISK"])


def test_short_history_gives_nan():
    eb = pd.DataFrame(_ebitda("SAFE", {2009: 100.0, 2010: 90.0, 2011: 95.0}) + _ebitda("RISK", CYCLIC))
    out = f21.compute(_panels(ebitda=eb), AS_OF)
    assert np.isnan(_score(out)["SAFE"]) and _score(out, "n_changes")["SAFE"] == 2


def test_stale_record_gives_nan():
    bal = pd.DataFrame([_balance("SAFE", fy=2009, che=200.0), _balance("RISK", che=0.0)])
    out = f21.compute(_panels(balance=bal), AS_OF)
    assert np.isnan(_score(out)["SAFE"])


def test_missing_ebitda_year_gives_nan():
    eb = pd.DataFrame(_ebitda("SAFE", {y: 100.0 for y in range(2001, 2011)}) + _ebitda("RISK", CYCLIC))
    assert np.isnan(_score(f21.compute(_panels(ebitda=eb), AS_OF))["SAFE"])


# ---------------------------------------------------------------- helpers


def _s(*x):
    return pd.Series(x, dtype=float)


def test_headroom_hand_values():
    # fcf = 100 - 20 - 30 = 50; A1 = 20 + 50 - 40 = 30; A2 = 20 + 100 - 80 = 40
    args = (_s(20.0), _s(0.0), _s(100.0), _s(20.0), _s(30.0), _s(40.0), _s(40.0))
    lin = f21.headroom(*args)
    assert lin["headroom"].iloc[0] == pytest.approx(40.0 / 150.0)        # min(30/50, 40/150)
    assert f21.headroom(*args, path="flat")["headroom"].iloc[0] == pytest.approx(0.2)   # min(30/100, 40/200)
    assert lin["liquidity"].iloc[0] == 20.0 and not lin["fails_at_zero"].iloc[0]


def test_headroom_clip_and_nonpositive_ebitda():
    h = f21.headroom(_s(1e4, 0.0, 0.0, 1e4), _s(0, 0, 0, 0), _s(100.0, 100.0, -10.0, -10.0), _s(0, 20, 5, 5),
                     _s(0, 30, 5, 5), _s(0, 100, 0, 0), _s(0, 0, 0, 0))
    assert h["headroom"].iloc[0] == 1.0 and h["headroom_raw"].iloc[0] > 1.0      # clipped at 100%
    assert h["headroom"].iloc[1] == 0.0 and h["fails_at_zero"].iloc[1]           # A1 = 0 + 50 - 100 < 0
    assert h["headroom"].iloc[2] == 0.0 and h["fails_at_zero"].iloc[2]           # E < 0 burns through cash
    assert np.isnan(h["headroom"].iloc[3])                                       # E < 0, cash covers: no meaning


def test_cyclicality_hand_values():
    eb = pd.DataFrame(_ebitda("A", {2008: 100.0, 2009: 60.0, 2010: 90.0, 2011: 99.0})
                      + _ebitda("B", {2007: 100.0, 2008: 100.0, 2009: -50.0, 2010: 10.0, 2011: 20.0}))
    c = f21.cyclicality(eb, pd.Series({"A": 2011, "B": 2011})).set_index("gvkey")
    assert c.loc["A", "cyclicality"] == pytest.approx(0.4) and c.loc["A", "n_changes"] == 3
    # 2009 change -150% floored at -100%; 2010 has a negative prior year and drops out
    assert c.loc["B", "cyclicality"] == pytest.approx(1.0) and c.loc["B", "n_changes"] == 3


def test_cyclicality_window_and_rising():
    eb = pd.DataFrame(_ebitda("A", {2000: 100.0, 2001: 10.0, **{y: 100.0 + y - 2001 for y in range(2002, 2012)}}))
    c = f21.cyclicality(eb, pd.Series({"A": 2011})).set_index("gvkey")
    # the 2001 fall lies outside 2002..2011; the worst of the window is the 2002 jump (+900%), so C < 0
    assert c.loc["A", "n_changes"] == 10 and c.loc["A", "cyclicality"] < 0


def test_score_hand_value_and_cover_ratio():
    out = f21.compute(_panels(), AS_OF).drop_duplicates("gvkey").set_index("gvkey")
    # RISK: che 0, fcf 50; A1 = 10, A2 = 20; H = min(10/50, 20/150) = 2/15; C = 0.5
    assert out.loc["RISK", "headroom"] == pytest.approx(2.0 / 15.0)
    assert out.loc["RISK", "cyclicality"] == pytest.approx(0.5)
    assert out.loc["RISK", "score"] == pytest.approx(2.0 / 15.0 - 0.5)
    assert out.loc["RISK", "cover_ratio"] == pytest.approx((2.0 / 15.0) / 0.5)
    assert np.isnan(out.loc["SAFE", "cover_ratio"])          # C = 0: no ratio


def test_delever_breadth():
    eb = pd.DataFrame(_ebitda("A", {2010: 100.0}, debt=400.0) + _ebitda("A", {2011: 100.0}, debt=300.0)
                      + _ebitda("B", {2010: 100.0}, debt=300.0) + _ebitda("B", {2011: 100.0}, debt=400.0)
                      + _ebitda("C", {2010: 100.0}, debt=400.0) + _ebitda("C", {2011: 200.0}, debt=400.0)
                      + _ebitda("D", {2011: 100.0}))
    b = f21.delever_breadth(eb, pd.Series({"A": 2011, "B": 2011, "C": 2011, "D": 2011}))
    assert b == pytest.approx(2.0 / 3.0)                     # A and C delever, B levers up, D has no prior year
    assert np.isnan(f21.delever_breadth(eb, pd.Series({"D": 2011})))
    out = f21.compute(_panels(), AS_OF)
    assert out["delever_breadth"].nunique(dropna=False) == 1 and not out["breadth_peak"].any()
