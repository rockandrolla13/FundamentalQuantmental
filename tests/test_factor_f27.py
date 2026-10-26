"""F27 real-yield shock regime: contract, no look-ahead, regime signs, edges, correlation fallback, helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from hy.backtest import decision_time
from hy.factors import f27_real_yield_regime as f27

AS_OF = pd.Timestamp("2021-02-28")
DT = decision_time(AS_OF)
T0 = AS_OF - pd.offsets.MonthEnd(3)                 # 2020-11-30
DAYS = pd.bdate_range("2018-01-01", "2021-03-31")   # rows after as_of exist on purpose


def _path(base: float, move: float, seed: int, noise: float = 0.01) -> pd.Series:
    """Daily level in FRED percent: base + noise, plus a linear ramp of `move` from T0 to AS_OF, flat after."""
    rng = np.random.default_rng(seed)
    x = base + rng.normal(0.0, noise, len(DAYS))
    ramp = np.clip((DAYS - T0).days / (AS_OF - T0).days, 0.0, 1.0)
    return pd.Series(x + move * ramp, index=DAYS)


def _long(series: dict[str, pd.Series]) -> pd.DataFrame:
    rows = [pd.DataFrame({"series_id": k, "date": s.index, "value": s.to_numpy()}) for k, s in series.items()]
    m = pd.concat(rows, ignore_index=True)
    m["available_at"] = m["date"] + pd.Timedelta(1, unit="D")
    return m


def _macro(d_real: float, d_be: float, t10yie: bool = True, extra: dict | None = None) -> dict[str, pd.Series]:
    """DGS10 = DFII10 + breakeven. Moves in percent points over T0 .. AS_OF."""
    real, be = _path(0.5, d_real, 1), _path(1.5, d_be, 2)
    s = {"DGS10": real + be, "DFII10": real}
    if t10yie:
        s["T10YIE"] = be
    s.update(extra or {})
    return s


def _panels(d_real=0.1, d_be=0.5, **kw) -> dict[str, pd.DataFrame]:
    return {"macro_series": _long(_macro(d_real, d_be, **kw))}


def _row(panels, **kw) -> pd.Series:
    out = f27.compute(panels, AS_OF, **kw)
    assert len(out) == 1
    return out.iloc[0]


# ---------------------------------------------------------------- contract


def test_meta_and_columns():
    for k in ("rank", "name", "level", "horizon_months", "needs", "spec", "section"):
        assert k in f27.META
    assert f27.META["rank"] == 27 and f27.META["level"] == "index" and "macro_series" in f27.META["needs"]
    out = f27.compute(_panels(), AS_OF)
    assert list(out.columns) == f27.COLS and list(out.columns[:4]) == ["date", "index", "score", "available_at"]
    assert len(out) == 1 and out["index"].iloc[0] == "US_HY"
    assert out["date"].iloc[0] == AS_OF and out["available_at"].iloc[0] == DT
    assert out["status"].iloc[0] == "ok" and np.isfinite(out["score"].iloc[0])


def test_missing_macro_panel_gives_empty_frame():
    for p in ({}, {"macro_series": _long(_macro(0.1, 0.5)).iloc[0:0]}, {"hy_index": pd.DataFrame()}):
        out = f27.compute(p, AS_OF)
        assert out.empty and list(out.columns) == f27.COLS


# ---------------------------------------------------------------- no look-ahead


def test_no_look_ahead():
    p = _panels()
    base = f27.compute(p, AS_OF)
    m = p["macro_series"]
    after = m[m["date"] > AS_OF].copy()
    after["value"] += 5.0                                   # wild values dated after as_of
    late = m[m["date"] == m.loc[m["date"] <= AS_OF, "date"].max()].copy()
    late["value"] -= 3.0                                    # a revision published after the decision time
    late["available_at"] = DT + pd.Timedelta(3, unit="D")
    q = {"macro_series": pd.concat([m[m["date"] <= AS_OF], after, late], ignore_index=True)}
    pd.testing.assert_frame_equal(base, f27.compute(q, AS_OF))


# ---------------------------------------------------------------- regime signs


@pytest.mark.parametrize("d_real,d_be,regime,lead,score", [
    (0.10, 0.50, "inflation_selloff", "breakeven", 1.0),    # breakeven-led rise of 60 bp
    (0.50, 0.10, "real_selloff", "real", -1.0),             # real-led rise of 60 bp
    (-0.40, -0.20, "rally", "real", -1.0),                  # fall of 60 bp
    (0.05, 0.05, "neutral", "real", 0.0),                   # 10 bp: below the 40 bp threshold
])
def test_regime_sign(d_real, d_be, regime, lead, score):
    r = _row(_panels(d_real, d_be))
    assert r["regime"] == regime and r["lead"] == lead and r["score"] == score
    assert r["d_nominal"] == pytest.approx((d_real + d_be) / 100, abs=0.0006)


def test_split_signal_sign_follows_breakeven_lead():
    assert _row(_panels(0.1, 0.5))["split_signal"] > 0
    assert _row(_panels(0.5, 0.1))["split_signal"] < 0


def test_regime_scores_override_flips_real_selloff():
    r = _row(_panels(0.5, 0.1), regime_scores={"real_selloff": 1.0})
    assert r["regime"] == "real_selloff" and r["score"] == 1.0


# ---------------------------------------------------------------- edges


def test_missing_real_yield_gives_missing_series():
    s = _macro(0.1, 0.5)
    del s["DFII10"]
    r = _row({"macro_series": _long(s)})
    assert r["status"] == "missing_series" and np.isnan(r["score"])


def test_stale_endpoint_gives_stale():
    s = {k: v[v.index <= "2021-01-15"] for k, v in _macro(0.1, 0.5).items()}
    r = _row({"macro_series": _long(s)})
    assert r["status"] == "stale" and np.isnan(r["score"]) and r["regime"] is None


def test_derived_breakeven_is_exact():
    r = _row(_panels(0.1, 0.5, t10yie=False))
    assert r["be_source"] == "derived" and r["split_gap"] == pytest.approx(0.0, abs=1e-12)
    r2 = _row(_panels(0.1, 0.5, t10yie=True))
    assert r2["be_source"] == "T10YIE" and r2["split_gap"] == pytest.approx(0.0, abs=1e-12)


def test_t10yie_gap_is_reported():
    s = _macro(0.1, 0.5)
    s["T10YIE"] = s["T10YIE"] + 0.02 * ((s["T10YIE"].index > T0).astype(float))   # 2 bp basis from Dec
    r = _row({"macro_series": _long(s)})
    assert r["split_gap"] == pytest.approx(-0.0002, abs=1e-9)


def test_nan_values_are_skipped():
    s = _macro(0.1, 0.5)
    s["DFII10"] = s["DFII10"].copy()
    s["DFII10"].iloc[-40:] = np.nan          # real-yield prints NaN from early Feb: no value near as_of
    r = _row({"macro_series": _long(s)})
    assert r["status"] == "stale"


# ---------------------------------------------------------------- correlation conditioner


def _spread(rate: pd.Series, beta: float, seed: int = 7) -> pd.Series:
    rng = np.random.default_rng(seed)
    return 4.0 + beta * (rate - rate.iloc[0]) + rng.normal(0.0, 0.01, len(rate)).cumsum() * 0.2


def test_rho_weekly_on_fred_when_hy_index_is_monthly():
    s = _macro(0.1, 0.5)
    s["DGS5"] = s["DGS10"] - 0.5
    s["BAMLH0A0HYM2"] = _spread(s["DGS5"], -2.0)            # spreads tighten when rates rise
    me = pd.date_range("2018-01-31", "2021-02-28", freq="ME")
    hy = pd.DataFrame({"date": me, "spread": 0.04, "available_at": me + pd.Timedelta(1, unit="D")})
    r = _row({"macro_series": _long(s), "hy_index": hy})
    assert r["rho_source"] == "BAMLH0A0HYM2" and r["rho_freq"] == "weekly" and r["rate_tenor"] == "DGS5"
    assert r["rho_n"] == 12 and r["rho_nominal"] < -0.5 and not r["rho_positive"]


def test_rho_monthly_fallback_and_gate():
    s = _macro(0.1, 0.5)
    me = pd.date_range("2018-01-31", "2021-02-28", freq="ME")
    nom = s["DGS10"].reindex(me, method="ffill") / 100
    hy = pd.DataFrame({"date": me, "spread": 0.04 + 1.5 * (nom.to_numpy() - nom.iloc[0]),   # spread up with rates
                       "available_at": me + pd.Timedelta(1, unit="D")})
    p = {"macro_series": _long(s), "hy_index": hy}
    r = _row(p)
    assert r["rho_source"] == "hy_index" and r["rho_freq"] == "monthly" and r["rho_n"] == 24
    assert r["rho_positive"] and r["regime"] == "inflation_selloff" and r["score"] == 1.0
    assert _row(p, rho_gate=True)["score"] == -1.0          # Jezek p. 4: taper-fear sell-off widens


def test_no_spread_source_leaves_rho_empty():
    r = _row(_panels())
    assert r["rho_source"] is None and np.isnan(r["rho_nominal"]) and r["rho_n"] == 0


# ---------------------------------------------------------------- quality compression


def test_quality_columns():
    s = _macro(0.1, 0.5)
    bb = pd.Series(3.0, index=DAYS)
    b = pd.Series(np.where(DAYS > T0, 4.2, 4.5), index=DAYS)      # B - BB from 150 to 120 bp
    ccc = pd.Series(np.where(DAYS > T0, 8.0, 8.5), index=DAYS)    # CCC - B from 400 to 380 bp
    s.update({"BAMLH0A1HYBB": bb, "BAMLH0A2HYB": b, "BAMLH0A3HYC": ccc})
    r = _row({"macro_series": _long(s)})
    assert r["b_bb_change"] == pytest.approx(-0.0030) and r["ccc_b_change"] == pytest.approx(-0.0020)
    assert r["rate_tenor"] == "DGS10" and r["compression_state"] and r["quality_tilt"] == 1.0
    q = _row(_panels(0.05, 0.05))
    assert not q["compression_state"] and q["quality_tilt"] == 0.0 and np.isnan(q["b_bb_change"])


# ---------------------------------------------------------------- helpers


def test_value_at_and_yield_split_by_hand():
    idx = pd.to_datetime(["2020-11-27", "2020-11-30", "2021-02-26"])
    nom, real = pd.Series([0.010, 0.011, 0.016], idx), pd.Series([-0.008, -0.008, -0.006], idx)
    assert f27.value_at(nom, pd.Timestamp("2020-11-29")) == 0.010
    assert np.isnan(f27.value_at(nom, pd.Timestamp("2021-02-20")))           # 3 months back, 7-day tolerance
    sp = f27.yield_split(nom, real, None, AS_OF, 3)
    assert sp["d_nominal"] == pytest.approx(0.005) and sp["d_real"] == pytest.approx(0.002)
    assert sp["d_breakeven"] == pytest.approx(0.003) and sp["real_share"] == pytest.approx(0.4)


def test_classify_regime_by_hand():
    assert f27.classify_regime(0.004, 0.002, 0.002) == ("real_selloff", "real")   # tie: real-led
    assert f27.classify_regime(0.0039, 0.001, 0.0029) == ("neutral", "breakeven")
    assert f27.classify_regime(-0.004, -0.001, -0.003) == ("rally", "breakeven")
    assert f27.classify_regime(np.nan, 0.0, 0.0) == (None, None)
    # Nicol p. 3 Fig. 4: the smallest of the 6 sell-offs, 2019, is 43 bp on the 5y: above the 40 bp threshold
    assert f27.classify_regime(0.0043, 0.0, 0.0043)[0] == "inflation_selloff"


def test_split_zscores_by_hand():
    me = pd.date_range("2018-01-31", "2021-02-28", freq="ME")
    real = pd.Series(np.arange(len(me)) % 2 * 0.002, index=me)              # alternates 0, 20 bp
    be = pd.Series(np.arange(len(me)) * 0.001, index=me)                     # +10 bp a month
    h = f27.month_end_changes(real, AS_OF, 3, 24)
    assert len(h) == 24 and set(np.round(np.abs(h), 6)) == {0.002}         # 3-month changes are +-20 bp
    rys, bes = f27.split_zscores(0.004, 0.003, real, be, AS_OF, 3, 24, 12)
    assert rys == pytest.approx(0.004 / np.std(h, ddof=1))
    assert np.isnan(bes)                                                     # constant 30 bp changes: sd 0


def test_change_corr_by_hand():
    wk = pd.date_range("2020-10-02", "2021-02-26", freq="W-FRI")
    rng = np.random.default_rng(3)
    y = pd.Series(rng.normal(0, 0.001, len(wk)).cumsum(), index=wk)
    s = pd.Series(rng.normal(0, 0.001, len(wk)).cumsum(), index=wk)
    rho, n = f27.change_corr(s, y, AS_OF, "W-FRI", 12, 8)
    assert n == 12 and rho == pytest.approx(np.corrcoef(s.diff().tail(12), y.diff().tail(12))[0, 1])
    assert np.isnan(f27.change_corr(s.iloc[::6], y.iloc[::6], AS_OF, "W-FRI", 12, 8)[0])   # too sparse


def test_rise_from_trough_by_hand():
    idx = pd.to_datetime(["2020-11-15", "2020-12-15", "2021-01-15", "2021-02-26"])
    y = pd.Series([0.003, 0.0045, 0.002, 0.0063], idx)
    assert f27.rise_from_trough(y, AS_OF, 3) == pytest.approx(0.0043)       # Nov 15 lies outside 3 months
    assert f27.rise_from_trough(y, AS_OF, 3) >= f27.COMPRESSION
