"""F23 margin squeeze: contract, no look-ahead, price lag, sign, edges, helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from hy.backtest import decision_time
from hy.factors import f23_margin_squeeze as f23

AS_OF = pd.Timestamp("2012-06-30")
DT = decision_time(AS_OF)
# A price month is known at month end + 31 days. May 2012 is known at DT (May 31 + 31 days = July 1 = DT). June 2012
# is not (July 31), although its available_at (July 1) is: the lag floor binds.


def _prices(sector: str, g_in: float, g_out: float, last: str = "2012-06-30") -> pd.DataFrame:
    """24 month ends to `last`. Input and output levels grow at constant monthly rates, so each 12-month change is
    g_in and g_out. available_at = month end + 1 day, so the lag floor binds."""
    dates = pd.date_range(end=last, periods=24, freq="ME")
    k = np.arange(24) / 12.0
    return pd.DataFrame({"gsector": sector, "date": dates, "ppi_input": 100.0 * (1 + g_in) ** k,
                         "price_output": 100.0 * (1 + g_out) ** k, "available_at": dates + pd.Timedelta(1, unit="D")})


def _quarters(gvkey: str, margins, sale: float = 100.0, last: str = "2012-03-31") -> pd.DataFrame:
    """One row per quarter, oldest first, ending at `last`. saleq = sale, oibdpq = margin x sale."""
    ends = pd.date_range(end=last, periods=len(margins), freq="QE")
    return pd.DataFrame({"gvkey": gvkey, "datadate": ends, "saleq": sale, "oibdpq": np.asarray(margins) * sale,
                         "available_at": ends + pd.Timedelta(45, unit="D")})


def _bonds(gvkeys, per: int = 2) -> pd.DataFrame:
    return pd.DataFrame([{"date": AS_OF, "cusip": f"{g}{k}", "gvkey": g, "years": 5.0, "g_spread": 0.04,
                          "price": 95.0, "yield": 0.08, "mod_dur": 4.0, "carried": False, "available_at": DT}
                         for g in gvkeys for k in range(per)])


def _gics(sectors: dict[str, str]) -> pd.DataFrame:
    return pd.DataFrame([{"gvkey": g, "gsector": s, "indfrom": pd.Timestamp("2000-01-01"), "indthru": pd.NaT,
                          "available_at": pd.Timestamp("2000-01-01")} for g, s in sectors.items()])


FLAT = [0.05] * 8


def _panels(cq=None, sectors=None, prices=None):
    cq = cq if cq is not None else pd.concat(
        [_quarters("THIN", [0.05] * 8), _quarters("FAT", [0.30] * 8),
         _quarters("FALL", np.linspace(0.40, 0.26, 8)), _quarters("RISE", np.linspace(0.20, 0.34, 8))],
        ignore_index=True)
    keys = sorted(cq["gvkey"].unique())
    sectors = sectors or {g: "20" for g in keys}
    prices = prices if prices is not None else pd.concat([_prices("20", 0.06, 0.02), _prices("40", 0.06, 0.02)])
    return {"compustat_quarterly": cq, "gics": _gics(sectors), "bond_panel": _bonds(keys), "sector_prices": prices}


def _iss(out: pd.DataFrame, col: str = "score") -> pd.Series:
    return out.drop_duplicates("gvkey").set_index("gvkey")[col]


# ---------------------------------------------------------------- contract


def test_meta_and_columns():
    for k in ("rank", "name", "level", "horizon_months", "needs", "spec", "section"):
        assert k in f23.META
    assert f23.META["rank"] == 23 and "sector_prices" in f23.META["needs"]
    out = f23.compute(_panels(), AS_OF)
    assert list(out.columns) == f23.BOND_COLS
    assert out["cusip"].is_unique and len(out) == 8
    assert (out["date"] == AS_OF).all() and (out["available_at"] == DT).all()
    assert out["score"].notna().all()
    assert out.groupby("gvkey")["score"].nunique().eq(1).all()
    assert (out["price_date"] == pd.Timestamp("2012-05-31")).all()


@pytest.mark.parametrize("drop", ["sector_prices", "compustat_quarterly", "gics", "bond_panel"])
def test_missing_panel_gives_empty_frame(drop):
    p = {k: v for k, v in _panels().items() if k != drop}
    out = f23.compute(p, AS_OF)
    assert out.empty and list(out.columns) == f23.BOND_COLS


# ---------------------------------------------------------------- no look-ahead


def test_future_rows_change_nothing():
    base = f23.compute(_panels(), AS_OF)
    p = _panels()
    late = pd.Timestamp("2012-07-15")
    future_prices = pd.DataFrame({"gsector": "20", "date": [pd.Timestamp("2012-05-31"), pd.Timestamp("2012-06-30")],
                                  "ppi_input": [500.0, 500.0], "price_output": [1.0, 1.0], "available_at": late})
    future_q = pd.DataFrame({"gvkey": ["THIN", "THIN"], "datadate": [pd.Timestamp("2012-03-31"),
                                                                    pd.Timestamp("2012-06-30")],
                             "saleq": 100.0, "oibdpq": -90.0, "available_at": late})
    future_b = _bonds(["THIN"]).assign(date=pd.Timestamp("2012-07-31"), g_spread=0.5)
    p["sector_prices"] = pd.concat([p["sector_prices"], future_prices], ignore_index=True)
    p["compustat_quarterly"] = pd.concat([p["compustat_quarterly"], future_q], ignore_index=True)
    p["bond_panel"] = pd.concat([p["bond_panel"], future_b], ignore_index=True)
    pd.testing.assert_frame_equal(f23.compute(p, AS_OF), base)


def test_price_lag_floor_binds():
    # June 2012 has available_at July 1 (= DT) but June 30 + 31 days = July 31 > DT, so May stays the latest.
    s = f23.sector_squeeze(_prices("20", 0.06, 0.02), DT)
    assert s["price_date"].iloc[0] == pd.Timestamp("2012-05-31")
    later = f23.sector_squeeze(_prices("20", 0.06, 0.02), pd.Timestamp("2012-07-31"))
    assert later["price_date"].iloc[0] == pd.Timestamp("2012-06-30")


def test_last_vintage_wins():
    p = _prices("20", 0.06, 0.02)
    rev = p[p["date"] == pd.Timestamp("2012-05-31")].assign(ppi_input=lambda d: d["ppi_input"] * 1.01,
                                                            available_at=pd.Timestamp("2012-06-20"))
    s = f23.sector_squeeze(pd.concat([p, rev], ignore_index=True), DT)
    assert s["ppi_input_yoy"].iloc[0] == pytest.approx(1.06 * 1.01 - 1.0)


# ---------------------------------------------------------------- sign


def test_thin_margin_scores_below_fat_when_squeezed():
    s = _iss(f23.compute(_panels(), AS_OF))
    assert s["THIN"] < s["FAT"]


def test_order_flips_when_prices_outrun_costs():
    p = _panels(prices=_prices("20", 0.02, 0.06))
    s = _iss(f23.compute(p, AS_OF))
    assert s["THIN"] > s["FAT"]


def test_falling_margin_scores_below_rising_at_equal_level():
    # FALL and RISE have the same LTM margin (0.30) now; only the trend differs.
    out = f23.compute(_panels(), AS_OF)
    m, s = _iss(out, "margin"), _iss(out)
    assert m["FALL"] == pytest.approx(m["RISE"], abs=0.05)
    assert _iss(out, "margin_trend")["FALL"] < 0 < _iss(out, "margin_trend")["RISE"]
    assert s["FALL"] < s["RISE"]


# ---------------------------------------------------------------- edges


def test_missing_lag_month_gives_nan():
    pr = _prices("20", 0.06, 0.02)
    pr = pr[pr["date"] != pd.Timestamp("2011-05-31")]
    out = f23.compute(_panels(prices=pr), AS_OF)
    assert out["squeeze"].isna().all() and out["score"].isna().all()


def test_stale_prices_give_nan():
    out = f23.compute(_panels(prices=_prices("20", 0.06, 0.02, last="2011-12-31")), AS_OF)
    assert out["score"].isna().all()


def test_short_history_and_bad_sales_give_nan():
    cq = pd.concat([_quarters("THIN", [0.05] * 8), _quarters("FAT", [0.30] * 8), _quarters("SHORT", [0.10] * 6),
                    _quarters("NOSALE", [0.10] * 8, sale=0.0)], ignore_index=True)
    s = _iss(f23.compute(_panels(cq=cq), AS_OF))
    assert np.isnan(s["SHORT"]) and np.isnan(s["NOSALE"])
    assert s[["THIN", "FAT"]].notna().all()


def test_gap_in_quarters_gives_nan():
    q = _quarters("GAP", [0.10] * 9)
    q = q.drop(index=4)
    cq = pd.concat([_quarters("THIN", FLAT), _quarters("FAT", [0.30] * 8), q], ignore_index=True)
    assert np.isnan(_iss(f23.compute(_panels(cq=cq), AS_OF))["GAP"])


def test_financial_gives_nan():
    p = _panels(sectors={"THIN": "20", "FAT": "20", "FALL": "20", "RISE": "40"})
    s = _iss(f23.compute(p, AS_OF))
    assert np.isnan(s["RISE"]) and s[["THIN", "FAT", "FALL"]].notna().all()


def test_negative_ebitda_hits_the_floor():
    cq = pd.concat([_quarters("NEG", [-0.10] * 8), _quarters("FAT", [0.30] * 8)], ignore_index=True)
    out = f23.compute(_panels(cq=cq), AS_OF)
    assert _iss(out, "exposure")["NEG"] == pytest.approx(49.0)
    assert _iss(out)["NEG"] < _iss(out)["FAT"]


# ---------------------------------------------------------------- helpers


def test_yoy_and_squeeze_by_hand():
    assert f23.yoy_change(pd.Series([106.0]), pd.Series([100.0])).iloc[0] == pytest.approx(0.06)
    assert np.isnan(f23.yoy_change(pd.Series([106.0]), pd.Series([0.0])).iloc[0])
    s = f23.sector_squeeze(_prices("20", 0.06, 0.02), DT)
    assert s["squeeze"].iloc[0] == pytest.approx(0.04)


def test_exposure_and_impact_by_hand():
    x = f23.margin_exposure(pd.Series([0.05, 0.30, 0.01, np.nan]))
    assert x.iloc[0] == pytest.approx(19.0) and x.iloc[1] == pytest.approx(0.7 / 0.3)
    assert x.iloc[2] == pytest.approx(49.0) and np.isnan(x.iloc[3])
    assert f23.squeeze_impact(pd.Series([0.03]), pd.Series([19.0])).iloc[0] == pytest.approx(-0.57)


def test_issuer_margins_by_hand():
    q = _quarters("A", [0.10, 0.10, 0.10, 0.10, 0.20, 0.20, 0.20, 0.20])
    m = f23.issuer_margins(q, DT).set_index("gvkey")
    assert m.loc["A", "margin"] == pytest.approx(0.20)
    assert m.loc["A", "margin_chg_12m"] == pytest.approx(0.10)
    assert m.loc["A", "margin_trend"] > 0


def test_clipped_z():
    z = f23.clipped_z(pd.Series([1.0, 2.0, 3.0, np.nan]))
    assert z.iloc[:3].tolist() == pytest.approx([-1.0, 0.0, 1.0]) and np.isnan(z.iloc[3])
    big = f23.clipped_z(pd.Series([0.0] * 20 + [100.0]))
    assert big.iloc[-1] == pytest.approx(3.0)
    inf = f23.clipped_z(pd.Series([1.0, 2.0, np.inf]))
    assert inf.iloc[2] == 3.0
    assert f23.clipped_z(pd.Series([5.0, np.nan])).tolist()[0] == 0.0
