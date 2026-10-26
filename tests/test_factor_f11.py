"""F11 ΔImpVOL: contract, no look-ahead, skip day, window, change formula, sign, winsorising, optional panels."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from hy.backtest import decision_time
from hy.factors import f11_delta_implied_vol as f11

AS_OF = pd.Timestamp("2015-06-30")
PREV = pd.Timestamp("2015-05-31")
DAYS = pd.bdate_range("2015-05-01", "2015-06-30")      # IV trading days; the last is 2015-06-30, 2015-05-29


def _iv(levels: dict[str, tuple[float, float]], jump: dict[str, float] | None = None) -> pd.DataFrame:
    """Flat IV per gvkey: (call, put) level in May; June adds `jump` to both from June 1."""
    rows = []
    for g, (c, p) in levels.items():
        for d in DAYS:
            j = (jump or {}).get(g, 0.0) if d.month == 6 else 0.0
            rows.append({"gvkey": g, "date": d, "cvol": c + j, "pvol": p + j})
    iv = pd.DataFrame(rows)
    iv["available_at"] = iv["date"] + pd.Timedelta(1, unit="D")
    return iv


def _bonds(gvkeys, per: int = 2) -> pd.DataFrame:
    rows = [{"date": AS_OF, "cusip": f"{g}{k}", "gvkey": g, "years": 5.0, "g_spread": 0.05, "price": 95.0,
             "yield": 0.08, "mod_dur": 4.0, "carried": False, "available_at": AS_OF + pd.Timedelta(1, unit="D")}
            for g in gvkeys for k in range(per)]
    return pd.DataFrame(rows)


def _panels(jump=None):
    lv = {"A": (0.30, 0.32), "B": (0.40, 0.41), "C": (0.25, 0.27)}
    return {"option_iv": _iv(lv, jump or {"A": 0.05, "B": -0.04, "C": 0.0}), "bond_panel": _bonds(lv)}


def _score(out: pd.DataFrame) -> pd.Series:
    return out.groupby("gvkey")["score"].first()


# ---------------------------------------------------------------- contract


def test_meta_and_columns():
    for k in ("rank", "name", "level", "horizon_months", "needs", "spec", "section"):
        assert k in f11.META
    assert f11.META["rank"] == 11 and "option_iv" in f11.META["needs"] and f11.META["horizon_months"] == 1
    out = f11.compute(_panels(), AS_OF)
    assert list(out.columns) == f11.COLS
    assert out["cusip"].is_unique and len(out) == 6
    assert (out["date"] == AS_OF).all() and (out["available_at"] == decision_time(AS_OF)).all()
    assert out["score"].notna().all()
    assert out.groupby("gvkey")["score"].nunique().eq(1).all()


@pytest.mark.parametrize("drop", ["option_iv", "bond_panel"])
def test_missing_required_panel_gives_empty_frame(drop):
    p = {k: v for k, v in _panels().items() if k != drop}
    out = f11.compute(p, AS_OF)
    assert out.empty and list(out.columns) == f11.COLS
    out = f11.compute({**_panels(), drop: pd.DataFrame()}, AS_OF)
    assert out.empty


# ---------------------------------------------------------------- sign and formula


def test_sign_rising_iv_scores_low():
    s = _score(f11.compute(_panels(), AS_OF, winsor=0.0))
    # A: IV up 5 points, B: down 4 points, C: flat. score = -ΔImpVOL
    assert s["B"] > s["C"] > s["A"]
    assert s["A"] == pytest.approx(-0.05) and s["B"] == pytest.approx(0.04) and s["C"] == pytest.approx(0.0)


def test_iv_change_hand_computation():
    cur = pd.DataFrame({"gvkey": ["X", "Y"], "cvol": [0.36, 0.20], "pvol": [0.40, 0.22], "iv_date": AS_OF})
    prev = pd.DataFrame({"gvkey": ["X", "Z"], "cvol": [0.30, 0.5], "pvol": [0.38, 0.5], "iv_date": PREV})
    c = f11.iv_change(cur, prev).set_index("gvkey")
    assert c.loc["X", "d_cvol"] == pytest.approx(0.06) and c.loc["X", "d_pvol"] == pytest.approx(0.02)
    assert c.loc["X", "d_impvol"] == pytest.approx(0.04)          # (0.06 + 0.02) / 2
    assert c.loc["X", "impvol"] == pytest.approx(0.38)            # (0.36 + 0.40) / 2
    assert np.isnan(c.loc["Y", "d_impvol"]) and np.isnan(c.loc["Z", "d_impvol"])


def test_call_minus_put_news_does_not_move_score():
    # call up 3, put down 3: ΔCVOL - ΔPVOL = 6 points, ΔImpVOL = 0 (p. 1382: the difference does not predict)
    cur = pd.DataFrame({"gvkey": ["X"], "cvol": [0.33], "pvol": [0.27], "iv_date": AS_OF})
    prev = pd.DataFrame({"gvkey": ["X"], "cvol": [0.30], "pvol": [0.30], "iv_date": PREV})
    assert f11.iv_change(cur, prev)["d_impvol"].iloc[0] == pytest.approx(0.0)


def test_winsorise_clips_tails_and_keeps_nan():
    x = pd.Series(list(np.arange(1.0, 201.0)) + [np.nan, 1e6])
    w = f11.winsorise(x, 0.005)
    lo, hi = np.nanquantile(x.to_numpy(float), [0.005, 0.995])
    assert w.max() == pytest.approx(hi) and w.min() == pytest.approx(lo) and w.isna().sum() == 1
    assert f11.winsorise(x, 0.0).equals(x.astype(float))


# ---------------------------------------------------------------- timing


def test_month_end_iv_skips_last_day_and_uses_window():
    iv = _iv({"A": (0.30, 0.30)})
    last = DAYS[DAYS.month == 6][-1]
    iv.loc[iv["date"] == last, ["cvol", "pvol"]] = 0.90           # spike on the month's last IV day
    m = f11.month_end_iv(iv, AS_OF)
    assert m["iv_date"].iloc[0] == DAYS[DAYS.month == 6][-2] and m["cvol"].iloc[0] == pytest.approx(0.30)
    # with no skip the spike enters
    assert f11.month_end_iv(iv, AS_OF, skip_days=0)["cvol"].iloc[0] == pytest.approx(0.90)


def test_stale_iv_outside_window_gives_nan():
    iv = _iv({"A": (0.30, 0.30), "B": (0.30, 0.30)}, {"A": 0.02, "B": 0.02})
    june = DAYS[DAYS.month == 6]
    # B stops quoting 10 trading days before month end: no row in the last 5 days before the skip
    iv = iv[~((iv["gvkey"] == "B") & (iv["date"] > june[-10]))]
    s = _score(f11.compute({"option_iv": iv, "bond_panel": _bonds(["A", "B"])}, AS_OF))
    assert np.isfinite(s["A"]) and np.isnan(s["B"])


def test_missing_put_gives_nan():
    p = _panels()
    iv = p["option_iv"].copy()
    iv.loc[(iv["gvkey"] == "A") & (iv["date"].dt.month == 5), "pvol"] = np.nan
    s = _score(f11.compute({**p, "option_iv": iv}, AS_OF))
    assert np.isnan(s["A"]) and np.isfinite(s["B"])


def test_no_lookahead():
    p = _panels()
    base = f11.compute(p, AS_OF)
    iv = p["option_iv"]
    late = iv[iv["date"] >= "2015-06-01"].copy()
    late["date"] = late["date"] + pd.offsets.MonthBegin(1)        # July rows
    late["cvol"] += 1.0
    hidden = iv[iv["date"] == DAYS[-2]].copy()                    # obs-day rows known only after decision time
    hidden["available_at"] = decision_time(AS_OF) + pd.Timedelta(1, unit="D")
    hidden["cvol"] += 1.0
    bonds = pd.concat([p["bond_panel"], p["bond_panel"].assign(date=pd.Timestamp("2015-07-31"))])
    out = f11.compute({"option_iv": pd.concat([iv, late, hidden]), "bond_panel": bonds}, AS_OF)
    pd.testing.assert_frame_equal(base, out)


# ---------------------------------------------------------------- optional panels and edges


def test_optional_extras():
    p = _panels()
    out = f11.compute(p, AS_OF)
    assert out["rating_class"].isna().all() and out["lag_stock_ret"].isna().all()
    ratings = pd.DataFrame({"gvkey": ["A", "B", "C"], "datadate": pd.Timestamp("2015-06-15"),
                            "splticrm": ["B-", "BB", "CCC+"], "available_at": pd.Timestamp("2015-06-16")})
    eq = pd.DataFrame({"gvkey": ["A", "B"], "datadate": AS_OF, "ret": [-0.10, 0.05],
                       "available_at": AS_OF + pd.Timedelta(1, unit="D")})
    out = f11.compute({**p, "ratings": ratings, "equity_monthly": eq}, AS_OF)
    r = out.groupby("gvkey").first()
    assert r.loc["A", "rating_class"] == "B" and r.loc["C", "rating_class"] == "CCC"
    assert r.loc["A", "lag_stock_ret"] == pytest.approx(-0.10) and np.isnan(r.loc["C", "lag_stock_ret"])
    # extras never change the score
    pd.testing.assert_series_equal(out["score"], f11.compute(p, AS_OF)["score"])


def test_issuer_without_options_and_ineligible_bonds():
    p = _panels()
    bonds = pd.concat([p["bond_panel"], _bonds(["D"], per=1)], ignore_index=True)
    bonds.loc[bonds["cusip"] == "A1", "carried"] = True
    out = f11.compute({**p, "bond_panel": bonds}, AS_OF).set_index("cusip")
    assert "A1" not in out.index and np.isnan(out.loc["D0", "score"])
