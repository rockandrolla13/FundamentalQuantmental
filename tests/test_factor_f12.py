"""F12 ETF pressure and contraflow: contract, no look-ahead, sign, formulas, edge cases."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from hy.backtest import decision_time
from hy.factors import f12_etf_pressure as f12

AS_OF = pd.Timestamp("2016-06-30")
MONTHS = pd.date_range("2015-01-31", AS_OF, freq="ME")
DAYS = pd.bdate_range("2015-01-01", AS_OF)
Q = 10e6                                                  # par each ETF holds of each bond
AMT = 100e6                                               # par outstanding of each bond
HOLD = {"HYG": ["A", "B", "C"], "JNK": ["C", "D"]}        # E is held by no ETF


def _panel(amt_out: bool = True) -> pd.DataFrame:
    rng = np.random.default_rng(1)
    rows = []
    for c in "ABCDE":
        for m in MONTHS:
            r = {"date": m, "cusip": c, "price": 95.0 + rng.normal(0, 1.0), "yield": 0.08, "years": 5.0,
                 "g_spread": 0.04, "mod_dur": 4.0, "carried": False, "par_volume": 5e6}
            if amt_out:
                r["amt_out"] = AMT
            rows.append(r)
    p = pd.DataFrame(rows)
    p["available_at"] = p["date"] + pd.Timedelta(1, unit="D")
    return p


def _flows(rate: dict[str, float] | None = None) -> pd.DataFrame:
    """Shares stay flat except on the last weekday of each month, when they change by `rate` (HYG creates 1%,
    JNK redeems 1%). NAV drifts up 0.1% a day for HYG and down for JNK."""
    rate = rate or {"HYG": 0.01, "JNK": -0.01}
    rows = []
    last = pd.Series(DAYS).groupby(pd.Series(DAYS).dt.to_period("M")).max()
    for e, g in rate.items():
        s, nav = 1e8, 80.0
        for d in DAYS:
            if d in set(last):
                s *= 1.0 + g
            nav *= 1.001 if e == "HYG" else 0.999
            rows.append({"etf": e, "date": d, "shares_out": s, "nav": nav})
    f = pd.DataFrame(rows)
    f["available_at"] = f["date"] + pd.Timedelta(1, unit="D")
    return f


def _holdings(extra: list[dict] | None = None) -> pd.DataFrame:
    rows = [{"etf": e, "date": m, "cusip": c, "par_held": Q} for e, cs in HOLD.items() for m in MONTHS for c in cs]
    h = pd.DataFrame(rows + (extra or []))
    h["available_at"] = h["date"] + pd.Timedelta(1, unit="D")
    return h


def _panels(**kw) -> dict[str, pd.DataFrame]:
    return {"bond_panel": kw.get("panel", _panel()), "etf_flows": kw.get("flows", _flows()),
            "etf_holdings": kw.get("holdings", _holdings())}


@pytest.fixture(scope="module")
def base() -> pd.DataFrame:
    return f12.compute(_panels(), AS_OF).set_index("cusip")


# ---------------------------------------------------------------- contract


def test_meta_and_columns(base):
    for k in ("rank", "name", "level", "horizon_months", "needs", "spec", "section"):
        assert k in f12.META
    assert f12.META["rank"] == 12 and f12.META["level"] == "bond"
    assert set(f12.META["needs"]) == {"bond_panel", "etf_flows", "etf_holdings"}
    out = f12.compute(_panels(), AS_OF)
    assert list(out.columns) == f12.BOND_COLS
    assert out["cusip"].is_unique and set(out["cusip"]) == set("ABCDE")
    assert (out["date"] == AS_OF).all() and (out["available_at"] == decision_time(AS_OF)).all()


# ---------------------------------------------------------------- sign and hand values


def test_allocation_pressure_hand_value(base):
    # six month-end creations of 1% each buy 6% of the 10m held: 600k par over 100m outstanding
    assert base.loc["A", "pressure_alloc"] == pytest.approx(6 * 0.01 * Q / AMT)
    assert base.loc["D", "pressure_alloc"] == pytest.approx(-6 * 0.01 * Q / AMT)
    assert base.loc["C", "pressure_alloc"] == pytest.approx(0.0, abs=1e-12)   # bought by HYG, sold by JNK
    assert base.loc["A", "score"] == pytest.approx(-base.loc["A", "pressure_alloc"])
    assert (base["scale_basis"] == "par").all()


def test_sign_contraflow(base):
    # pressure then reversal: the ETF-bought bond scores below the ETF-sold bond
    assert base.loc["A", "score"] < 0 < base.loc["D", "score"]
    assert base.loc["A", "score"] < base.loc["C", "score"] < base.loc["D", "score"]


def test_total_and_recon():
    # D enters HYG at 2016-03-31 with 5m: total flow +5m from HYG, allocation adds HYG flows after entry
    entry = pd.Timestamp("2016-03-31")
    extra = [{"etf": "HYG", "date": m, "cusip": "D", "par_held": 5e6} for m in MONTHS if m >= entry]
    out = f12.compute(_panels(holdings=_holdings(extra)), AS_OF).set_index("cusip")
    alloc = (-6 * 0.01 * Q + 3 * 0.01 * 5e6) / AMT          # JNK six redemptions, HYG April-June creations on 5m
    assert out.loc["D", "pressure_alloc"] == pytest.approx(alloc)
    assert out.loc["D", "pressure_total"] == pytest.approx(5e6 / AMT)
    assert out.loc["D", "pressure_recon"] == pytest.approx(5e6 / AMT - alloc)
    tot = f12.compute(_panels(holdings=_holdings(extra)), AS_OF, basis="total").set_index("cusip")
    assert tot.loc["D", "score"] == pytest.approx(-5e6 / AMT)


def test_share_flow_and_flow_column():
    f = pd.DataFrame({"etf": "X", "date": pd.date_range("2016-01-01", periods=3), "shares_out": [100.0, 102.0, 96.9],
                      "available_at": pd.Timestamp("2016-01-05")})
    fr = f12.share_flow(f)
    assert fr["frac"].tolist() == pytest.approx([0.02, -0.05])
    g = f.drop(columns="shares_out").assign(flow=[0.0, 5.0, -2.0], aum=[100.0, 110.0, 108.0])
    assert f12.share_flow(g)["frac"].tolist() == pytest.approx([0.05, -2.0 / 110.0])


def test_snapshot_for_strict():
    snaps = pd.DatetimeIndex(["2016-01-31", "2016-02-29"])
    days = pd.Series(pd.to_datetime(["2016-01-15", "2016-01-31", "2016-02-10"]))
    assert f12.snapshot_for(snaps, days).isna().tolist()[:2] == [True, True]
    assert f12.snapshot_for(snaps, days).iloc[2] == pd.Timestamp("2016-01-31")
    assert f12.snapshot_for(snaps, days, strict=False).iloc[1] == pd.Timestamp("2016-01-31")


def test_arb_sensitivity_hand_value():
    w = pd.Series([0.5, 0.3, 0.2], index=list("abc"))
    c = pd.Series([1.0, 2.0, 4.0], index=list("abc"))
    num = c * w ** 0.5
    lam = f12.arb_sensitivity(w, c)
    assert lam.to_numpy() == pytest.approx((num / (w * num).sum()).to_numpy())
    assert (w * lam).sum() == pytest.approx(1.0)                      # weighted mean is 1 (Shim p. 13)
    # a bond without c drops out and the weights renormalise
    lam2 = f12.arb_sensitivity(w, c.drop("c"))
    assert list(lam2.index) == ["a", "b"] and ((w[["a", "b"]] / 0.8) * lam2).sum() == pytest.approx(1.0)


def test_price_impact_hand_value():
    m = pd.date_range("2015-07-31", AS_OF, freq="ME")
    px = 100.0 * np.cumprod(np.r_[1.0, np.full(len(m) - 1, 1.02)])
    p = pd.DataFrame({"date": m, "cusip": "A", "price": px, "par_volume": 4e6})
    c = f12.price_impact(p, AS_OF)
    assert c["A"] == pytest.approx(0.02 / np.sqrt(4e6))
    assert f12.price_impact(p.iloc[-4:], AS_OF).empty                 # fewer than MIN_C_MONTHS ratios


def test_etf_month_return():
    f = _flows()
    r = f12.etf_month_return(f, AS_OF)
    n = f[f["etf"] == "HYG"].set_index("date")["nav"]
    assert r["HYG"] == pytest.approx(n.loc[:AS_OF].iloc[-1] / n.loc[:"2016-05-31"].iloc[-1] - 1.0)
    g = f.assign(ret=0.001)
    k = ((g["date"] > "2016-05-31") & (g["date"] <= AS_OF) & (g["etf"] == "HYG")).sum()
    assert f12.etf_month_return(g, AS_OF)["HYG"] == pytest.approx(1.001 ** k - 1.0)


def test_arb_score_sign():
    # in JNK, D is far less liquid than C at the same weight: Lambda_D > 1. JNK fell, so D over-reacted down
    p = _panel()
    p.loc[p["cusip"] == "D", "par_volume"] = 5e4
    out = f12.compute(_panels(panel=p), AS_OF).set_index("cusip")
    assert out.loc["D", "arb_sensitivity"] > 1.0
    assert out.loc["D", "etf_return"] < 0
    assert out.loc["D", "arb_score"] > 0                              # long: the down move reverts up
    assert np.isnan(out.loc["E", "arb_score"])


# ---------------------------------------------------------------- no look-ahead


def test_no_lookahead(base):
    late_f = _flows()
    late_f = late_f[late_f["date"] == late_f["date"].max()].assign(shares_out=5e8)
    day = pd.Timedelta(1, unit="D")
    late_f = pd.concat([late_f.assign(date=AS_OF + 3 * day, available_at=AS_OF + 4 * day),
                        late_f.assign(available_at=AS_OF + pd.Timedelta(10, unit="D"))])
    late_h = _holdings()
    late_h = late_h[late_h["date"] == AS_OF].assign(par_held=1e9, available_at=AS_OF + pd.Timedelta(10, unit="D"))
    late_p = _panel()
    late_p = late_p[late_p["date"] == AS_OF].assign(date=AS_OF + pd.offsets.MonthEnd(1), par_volume=1.0,
                                                    available_at=AS_OF + pd.offsets.MonthEnd(1))
    panels = _panels(flows=pd.concat([_flows(), late_f]), holdings=pd.concat([_holdings(), late_h]),
                     panel=pd.concat([_panel(), late_p]))
    out = f12.compute(panels, AS_OF).set_index("cusip")
    pd.testing.assert_frame_equal(out, base)


# ---------------------------------------------------------------- edge cases


@pytest.mark.parametrize("drop", ["etf_flows", "etf_holdings", "bond_panel"])
def test_missing_panel_gives_empty(drop):
    panels = _panels()
    panels.pop(drop)
    out = f12.compute(panels, AS_OF)
    assert out.empty and list(out.columns) == f12.BOND_COLS


def test_unheld_bond_is_nan(base):
    assert base.loc["E", "n_etfs"] == 0 and np.isnan(base.loc["E", "score"])
    assert base.loc["C", "n_etfs"] == 2


def test_volume_scale_without_amt_out():
    out = f12.compute(_panels(panel=_panel(amt_out=False)), AS_OF).set_index("cusip")
    assert (out["scale_basis"] == "volume").all()
    assert out.loc["A", "pressure_alloc"] == pytest.approx(6 * 0.01 * Q / (6 * 5e6))


def test_par_scale_with_missing_amt_out_is_nan():
    p = _panel()
    p.loc[p["cusip"] == "A", "amt_out"] = np.nan
    out = f12.compute(_panels(panel=p), AS_OF, scale="par").set_index("cusip")
    assert np.isnan(out.loc["A", "score"]) and not np.isnan(out.loc["B", "score"])
