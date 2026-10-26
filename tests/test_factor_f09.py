"""F09 profitability change: contract, no look-ahead, 90-day lag, sign, minimum history, financials, helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from hy.backtest import decision_time
from hy.factors import f09_profitability_change as f09

AS_OF = pd.Timestamp("2012-06-30")
DT = decision_time(AS_OF)
# FY2011 (Dec year end) is known at 2012-03-30; FY2006 is five fiscal years earlier


def _annual(gvkey: str, profs: dict[int, float], at: float = 100.0) -> pd.DataFrame:
    """One row per fiscal year (December year end). sale = 100, cogs = sale - prof x at, so Prof = prof."""
    rows = []
    for fy, pr in profs.items():
        d = pd.Timestamp(f"{fy}-12-31")
        rows.append({"gvkey": gvkey, "datadate": d, "fyear": fy, "sale": 100.0, "cogs": 100.0 - pr * at, "at": at,
                     "available_at": d + pd.Timedelta(90, unit="D")})
    return pd.DataFrame(rows)


def _years(lo: int, hi: int, start: float, end: float) -> dict[int, float]:
    return dict(zip(range(lo, hi + 1), np.linspace(start, end, hi - lo + 1)))


def _bonds(gvkeys, per: int = 2) -> pd.DataFrame:
    return pd.DataFrame([{"date": AS_OF, "cusip": f"{g}{k}", "gvkey": g, "years": 5.0, "g_spread": 0.04,
                          "price": 95.0, "yield": 0.08, "mod_dur": 4.0, "carried": False, "available_at": DT}
                         for g in gvkeys for k in range(per)])


def _gics(sectors: dict[str, str]) -> pd.DataFrame:
    return pd.DataFrame([{"gvkey": g, "gsector": s, "indfrom": pd.Timestamp("2000-01-01"), "indthru": pd.NaT,
                          "available_at": pd.Timestamp("2000-01-01")} for g, s in sectors.items()])


def _panels(annual=None, sectors=None):
    annual = annual if annual is not None else pd.concat(
        [_annual("UP", _years(2006, 2011, 0.20, 0.30)), _annual("DN", _years(2006, 2011, 0.30, 0.20)),
         _annual("FL", _years(2006, 2011, 0.25, 0.25))], ignore_index=True)
    keys = sorted(annual["gvkey"].unique())
    sectors = sectors or {g: "20" for g in keys}
    return {"compustat_annual": annual, "gics": _gics(sectors), "bond_panel": _bonds(keys)}


def _score(out: pd.DataFrame) -> pd.Series:
    return out.drop_duplicates("gvkey").set_index("gvkey")["score"]


# ---------------------------------------------------------------- contract


def test_meta_and_columns():
    for k in ("rank", "name", "level", "horizon_months", "needs", "spec", "section"):
        assert k in f09.META
    assert f09.META["rank"] == 9 and "compustat_annual" in f09.META["needs"]
    out = f09.compute(_panels(), AS_OF)
    assert list(out.columns) == f09.BOND_COLS
    assert out["cusip"].is_unique and len(out) == 6
    assert (out["date"] == AS_OF).all() and (out["available_at"] == DT).all()
    assert out["score"].notna().all()
    assert out.groupby("gvkey")["score"].nunique().eq(1).all()
    assert (out["fyear"] == 2011).all() and (out["fyear_lag"] == 2006).all()


@pytest.mark.parametrize("drop", ["compustat_annual", "gics", "bond_panel"])
def test_missing_panel_gives_empty_frame(drop):
    p = {k: v for k, v in _panels().items() if k != drop}
    out = f09.compute(p, AS_OF)
    assert out.empty and list(out.columns) == f09.BOND_COLS


# ---------------------------------------------------------------- sign


def test_sign_rising_profitability_scores_higher():
    s = _score(f09.compute(_panels(), AS_OF))
    assert s["UP"] == pytest.approx(0.10) and s["DN"] == pytest.approx(-0.10) and s["FL"] == pytest.approx(0.0)
    assert s["UP"] > s["FL"] > s["DN"]


# ---------------------------------------------------------------- no look-ahead and lag


def test_no_lookahead_future_rows_change_nothing():
    base = f09.compute(_panels(), AS_OF)
    p = _panels()
    late = _annual("UP", {2012: 0.90, 2013: 0.95})                     # FY2012 known in 2013: after as_of
    # a fiscal year end before as_of whose available_at claims it is known: datadate + 90 days is after DT
    early_claim = _annual("DN", {2012: 0.90}).assign(datadate=pd.Timestamp("2012-04-30"), available_at=DT)
    p["compustat_annual"] = pd.concat([p["compustat_annual"], late, early_claim], ignore_index=True)
    restated = _annual("FL", {2011: 0.99}).assign(available_at=DT + pd.Timedelta(1, unit="D"))
    p["compustat_annual"] = pd.concat([p["compustat_annual"], restated], ignore_index=True)
    future_bond = _bonds(["UP"]).assign(date=AS_OF + pd.offsets.MonthEnd(1), cusip="UPX")
    p["bond_panel"] = pd.concat([p["bond_panel"], future_bond], ignore_index=True)
    pd.testing.assert_frame_equal(f09.compute(p, AS_OF), base)


def test_ninety_day_lag_picks_prior_year():
    # at 2012-03-29 FY2011 (known 2012-03-30) is not yet known: the latest year is FY2010
    a = _annual("UP", _years(2005, 2011, 0.20, 0.32))
    out = f09.profitability_change(a, pd.Timestamp("2012-03-29"))
    assert out["fyear"].iloc[0] == 2010 and out["fyear_lag"].iloc[0] == 2005
    out = f09.profitability_change(a, pd.Timestamp("2012-03-30"))
    assert out["fyear"].iloc[0] == 2011


# ---------------------------------------------------------------- edges


def test_short_history_nan_at_5_scored_at_3():
    a = pd.concat([_annual("UP", _years(2006, 2011, 0.20, 0.30)), _annual("NEW", _years(2008, 2011, 0.10, 0.25))],
                  ignore_index=True)
    s5 = _score(f09.compute(_panels(a), AS_OF))
    assert np.isnan(s5["NEW"]) and s5["UP"] == pytest.approx(0.10)
    s3 = _score(f09.compute(_panels(a), AS_OF, window=f09.SHORT_WINDOW))
    assert s3["NEW"] == pytest.approx(0.25 - 0.10)


def test_gap_between_ends_is_allowed_missing_end_is_not():
    full = _years(2006, 2011, 0.20, 0.30)
    gap = _annual("G", {k: v for k, v in full.items() if k not in (2008, 2009)})
    no_end = _annual("E", {k: v for k, v in full.items() if k != 2006})
    s = _score(f09.compute(_panels(pd.concat([gap, no_end], ignore_index=True)), AS_OF))
    assert s["G"] == pytest.approx(0.10) and np.isnan(s["E"])


def test_nonpositive_assets_and_missing_fields_give_nan():
    a = _annual("Z", _years(2006, 2011, 0.2, 0.3))
    a.loc[a["fyear"] == 2006, "at"] = 0.0
    b = _annual("M", _years(2006, 2011, 0.2, 0.3))
    b.loc[b["fyear"] == 2011, "cogs"] = np.nan
    s = _score(f09.compute(_panels(pd.concat([a, b], ignore_index=True)), AS_OF))
    assert s.isna().all()


def test_financials_get_nan():
    s = _score(f09.compute(_panels(sectors={"UP": "40", "DN": "60", "FL": "20"}), AS_OF))
    assert np.isnan(s["UP"]) and np.isnan(s["DN"]) and s["FL"] == pytest.approx(0.0)


def test_stale_latest_record_gives_no_score():
    a = _annual("OLD", _years(2003, 2009, 0.2, 0.3))    # FY2009: 913 days before the decision time
    out = f09.compute(_panels(a), AS_OF)
    assert out["score"].isna().all() and len(out) == 2


def test_issuer_without_bonds_or_annual_data():
    p = _panels()
    p["bond_panel"] = pd.concat([p["bond_panel"], _bonds(["NOFS"], per=1)], ignore_index=True)
    out = f09.compute(p, AS_OF)
    assert len(out) == 7 and np.isnan(_score(out)["NOFS"])
    assert np.isnan(out.loc[out["gvkey"] == "NOFS", "rank"]).all()


# ---------------------------------------------------------------- helpers


def test_profitability_hand_computation():
    p = f09.profitability(pd.Series([500.0, 80.0, 10.0]), pd.Series([300.0, 100.0, 5.0]),
                          pd.Series([1000.0, 40.0, -1.0]))
    assert p.iloc[0] == pytest.approx(0.2) and p.iloc[1] == pytest.approx(-0.5) and np.isnan(p.iloc[2])


def test_profitability_change_hand_computation():
    a = pd.DataFrame({"gvkey": "H", "fyear": [2006, 2011], "datadate": pd.to_datetime(["2006-12-31", "2011-12-31"]),
                      "sale": [400.0, 600.0], "cogs": [300.0, 360.0], "at": [500.0, 800.0]})
    a["available_at"] = a["datadate"] + pd.Timedelta(90, unit="D")
    out = f09.profitability_change(a, DT)
    # (600 - 360) / 800 - (400 - 300) / 500 = 0.30 - 0.20
    assert out["score"].iloc[0] == pytest.approx(0.10)
    assert out["prof"].iloc[0] == pytest.approx(0.30) and out["prof_lag"].iloc[0] == pytest.approx(0.20)


def test_rank_unit():
    r = f09.rank_unit(pd.Series([3.0, np.nan, 1.0, 2.0, 2.0]))
    assert r.iloc[2] == -0.5 and r.iloc[0] == 0.5 and np.isnan(r.iloc[1])
    assert r.iloc[3] == r.iloc[4] == pytest.approx(0.0)
    assert f09.rank_unit(pd.Series([7.0, np.nan])).iloc[0] == 0.0
