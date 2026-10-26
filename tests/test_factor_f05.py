"""F05 flow pressure reversal: contract, no look-ahead, side map, cap, formulas, sign, edge cases."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from hy.backtest import decision_time
from hy.factors import f05_flow_pressure_reversal as f05

AS_OF = pd.Timestamp("2016-06-30")
DAYS = pd.bdate_range("2010-01-01", AS_OF)
MONTHS = pd.date_range("2010-01-31", AS_OF, freq="ME")
W = f05.trading_days(AS_OF, f05.WINDOW)            # the 63 days of W_t
ISSUERS = {"A": "G1", "B": "G1", "C": "G2", "D": "G2", "E": "G3"}


def _panel(price: dict[str, float] | None = None) -> pd.DataFrame:
    rows = []
    for c, g in ISSUERS.items():
        for m in MONTHS:
            px = (price or {}).get(c, 95.0) if m == AS_OF else 95.0
            rows.append({"date": m, "cusip": c, "gvkey": g, "price": px, "yield": 0.08, "years": 5.0,
                         "g_spread": 0.04, "mod_dur": 4.0, "carried": False})
    p = pd.DataFrame(rows)
    p["available_at"] = p["date"] + pd.Timedelta(1, unit="D")
    return p


def _flow(event: str = "sell", flat_tail: bool = True, seed: int = 0) -> pd.DataFrame:
    """Every bond trades 1 sale and 1 purchase a day with noise. In W_t the G1 bonds trade balanced, except that
    bond A takes heavy net sales (or purchases) for the first 53 days, then 10 flat days."""
    rng = np.random.default_rng(seed)
    rows = []
    for c in ISSUERS:
        e = rng.normal(0.0, 2e5, len(DAYS))
        sell, buy = 1e6 + e, 1e6 - e
        if c in ("A", "B"):
            inw = DAYS.isin(W)
            sell, buy = np.where(inw, 1e6, sell), np.where(inw, 1e6, buy)
            if c == "A" and event:
                hit = DAYS.isin(W if not flat_tail else W[:-f05.SHORT])
                extra = 1.5e6 if event == "sell" else 0.0
                sell = np.where(hit, sell + extra, sell)
                buy = np.where(hit & (event == "buy"), buy + 1.5e6, buy)
        rows.append(pd.DataFrame({"date": DAYS, "cusip": c, "cust_sell_par": sell, "cust_buy_par": buy,
                                  "cust_sell_n": 1, "cust_buy_n": 1}))
    f = pd.concat(rows, ignore_index=True)
    f["available_at"] = f["date"] + pd.Timedelta(1, unit="D")
    return f


def _run(flow=None, panel=None) -> pd.DataFrame:
    panels = {"bond_panel": _panel() if panel is None else panel, "trace_daily_flow": _flow() if flow is None else flow}
    return f05.compute(panels, AS_OF).set_index("cusip")


@pytest.fixture(scope="module")
def base() -> pd.DataFrame:
    return _run()


# ---------------------------------------------------------------- contract


def test_meta_and_columns(base):
    for k in ("rank", "name", "level", "horizon_months", "needs", "spec", "section"):
        assert k in f05.META
    assert f05.META["rank"] == 5 and "trace_daily_flow" in f05.META["needs"]
    out = f05.compute({"bond_panel": _panel(), "trace_daily_flow": _flow()}, AS_OF)
    assert list(out.columns) == f05.BOND_COLS
    assert out["cusip"].is_unique and set(out["cusip"]) == set(ISSUERS)
    assert (out["date"] == AS_OF).all() and (out["available_at"] == decision_time(AS_OF)).all()


def test_missing_flow_panel_gives_empty_frame():
    out = f05.compute({"bond_panel": _panel()}, AS_OF)
    assert out.empty and list(out.columns) == f05.BOND_COLS
    out = f05.compute({"bond_panel": _panel(), "trace_daily_flow": _flow().iloc[:0]}, AS_OF)
    assert out.empty


# ---------------------------------------------------------------- no look-ahead


def test_no_lookahead(base):
    flow, panel = _flow(), _panel()
    late = pd.DataFrame({"date": pd.bdate_range("2016-07-01", "2016-08-31"), "cusip": "B", "cust_sell_par": 9e7,
                         "cust_buy_par": 0.0, "cust_sell_n": 50, "cust_buy_n": 0})
    late["available_at"] = late["date"] + pd.Timedelta(1, unit="D")
    late_report = late.iloc[:5].assign(date=W[-5:], available_at=pd.Timestamp("2016-08-15"))
    future = panel[panel["date"] == AS_OF].assign(date=pd.Timestamp("2016-07-31"), price=30.0,
                                                  available_at=pd.Timestamp("2016-08-01"))
    out = _run(pd.concat([flow, late, late_report], ignore_index=True), pd.concat([panel, future], ignore_index=True))
    pd.testing.assert_frame_equal(out, base)


# ---------------------------------------------------------------- sign on a synthetic issuer


def test_sign_sold_bond_scores_long(base):
    a, b = base.loc["A"], base.loc["B"]
    assert a["f05_pressure"] > 0 and a["f05_months_sold"] == 3
    assert a["f05_trigger"] and a["f05_exhausted"]
    assert a["f05_score"] == pytest.approx(a["f05_rel_pressure"]) and a["f05_score"] > 0
    assert a["score"] == pytest.approx(a["f05_score"] / f05.HOLD) and a["n_cohorts"] == 1
    assert b["f05_score"] == 0 and np.isnan(b["score"])
    assert a["pair_short"] == "B" and b["pair_short"] is None
    assert a["f05_rel_pressure_n"] == pytest.approx(0.0)      # same trade counts: the count twin sees no flow


def test_flip_sides_no_trigger():
    out = _run(_flow(event="buy"))
    assert out.loc["A", "f05_pressure"] < 0 and not out.loc["A", "f05_trigger"]
    assert out.loc["A", "f05_score"] == 0 and np.isnan(out.loc["A", "score"])


def test_no_flat_tail_not_exhausted():
    out = _run(_flow(flat_tail=False))
    assert out.loc["A", "f05_trigger"] and not out.loc["A", "f05_exhausted"]
    assert out.loc["A", "f05_score"] == 0 and np.isnan(out.loc["A", "score"])


# ---------------------------------------------------------------- edge cases


def test_single_bond_issuer_is_nan(base):
    assert np.isnan(base.loc["E", "f05_rel_pressure"]) and np.isnan(base.loc["E", "score"])
    assert np.isnan(base.loc["E", "f05_score"])


def test_few_trades_is_nan():
    flow = _flow()
    thin = (flow["cusip"] == "A") & flow["date"].isin(W)
    keep = flow["date"].isin(W[:2])
    flow = flow[~thin | keep]                                   # 2 days x 2 trades = 4 trades in W_t
    out = _run(flow)
    assert np.isnan(out.loc["A", "score"]) and np.isnan(out.loc["B", "f05_rel_pressure"])


def test_flat_price_is_nan():
    out = _run(panel=_panel(price={"A": 40.0}))
    assert np.isnan(out.loc["A", "score"]) and np.isnan(out.loc["A", "f05_rel_pressure"])


def test_reads_no_equity(base):
    out = f05.compute({"bond_panel": _panel(), "trace_daily_flow": _flow(),
                       "equity_monthly": pd.DataFrame({"gvkey": ["G1"], "ret": [0.5]})}, AS_OF).set_index("cusip")
    pd.testing.assert_frame_equal(out, base)


# ---------------------------------------------------------------- daily flow helper


def test_side_map_and_min_par():
    t = pd.DataFrame({
        "cusip_id": ["X"] * 5, "trd_exctn_dt": ["2016-06-01"] * 5,
        "par": [200_000.0, 300_000.0, 500_000.0, 50_000.0, 400_000.0],
        "side": ["B", "S", "B", "B", "S"], "contra_party_type": ["C", "C", "D", "C", "D"],
    })
    out = f05.daily_flow_from_trades(t)
    assert len(out) == 1
    r = out.iloc[0]
    assert (r["cust_sell_par"], r["cust_buy_par"], r["cust_sell_n"], r["cust_buy_n"]) == (200_000, 300_000, 1, 1)
    assert r["available_at"] == pd.Timestamp("2016-06-02")
    lagged = f05.daily_flow_from_trades(t, load_lag=pd.Timedelta(35, unit="D"))
    assert lagged["available_at"].iloc[0] == pd.Timestamp("2016-07-07")


def test_cap_reads_as_floor_on_raw_reports():
    raw = pd.DataFrame({
        "cusip_id": ["X", "X", "X"], "trd_exctn_dt": ["2016-06-01"] * 3, "msg_seq_nb": [1, 2, 3],
        "orig_msg_seq_nb": [None, None, 2], "trc_st": ["M", "M", "N"], "rptd_pr": [90.0, 91.0, 91.0],
        "ascii_rptd_vol_tx": ["1MM+", "250000.00", "250000.00"], "side": ["B", "B", "B"],
        "contra_party_type": ["C", "C", "C"],
    })
    out = f05.daily_flow_from_trades(raw)                        # report 2 is cancelled by report 3
    assert out["cust_sell_par"].iloc[0] == 1_000_000 and out["cust_sell_n"].iloc[0] == 1
    assert out["cust_buy_n"].iloc[0] == 0


# ---------------------------------------------------------------- formula helpers


def test_bond_pressure_hand():
    # days: vol window Jun 24, Jun 27; W_t = Jun 28, 29, 30
    f = pd.DataFrame({"date": pd.to_datetime(["2016-06-24", "2016-06-28", "2016-06-29", "2016-06-30"]),
                      "cusip": "X", "cust_sell_par": [1e6, 3e5, 0.0, 2e5], "cust_buy_par": [1e6, 0.0, 1e5, 0.0],
                      "cust_sell_n": [1, 1, 0, 1], "cust_buy_n": [1, 0, 1, 0]})
    r = f05.bond_pressure(f, AS_OF, window=3, short=1, vol_window=2).iloc[0]
    assert r["pressure"] == pytest.approx(4e5 / (3 * 1e6))
    assert r["pressure_short"] == pytest.approx(0.2)
    assert r["pressure_n"] == pytest.approx(1 / 3)
    assert r["months_sold"] == 1 and r["n_trades"] == 3


def test_relative_pressure_hand():
    p = pd.Series([0.3, 0.1, -0.2, 0.5])
    dts = pd.Series([1.0, 2.0, 3.0, 1.0])
    iss = pd.Series(["X", "X", "X", "Y"])
    rp = f05.relative_pressure(p, dts, iss)
    assert rp.iloc[0] == pytest.approx(0.38)
    assert rp.iloc[1] == pytest.approx(0.175)
    assert rp.iloc[2] == pytest.approx(-0.2 - 0.5 / 3)
    assert np.isnan(rp.iloc[3])


def test_trigger_threshold_hand():
    hist = [pd.Series(np.arange(1.0, 11.0))] * 12
    assert f05.trigger_threshold(hist) == pytest.approx(9.1)
    assert np.isnan(f05.trigger_threshold(hist[:11]))


def test_f05_score_and_hold():
    rp = pd.Series([0.5, 0.5, 0.5, 0.5, np.nan], index=list("abcde"))
    p = pd.Series([0.4, -0.1, 0.4, 0.4, 0.4], index=rp.index)
    m = pd.Series([3, 3, 1, 3, 3], index=rp.index)
    rs = pd.Series([-0.1, -0.1, -0.1, 0.2, -0.1], index=rp.index)
    s = f05.f05_score(rp, p, m, rs, c=0.3)
    assert s["f05"].tolist()[:4] == [0.5, 0.0, 0.0, 0.0] and np.isnan(s["f05"].iloc[4])
    score, n = f05.hold_score([s["f05"], pd.Series({"a": 0.0, "b": 0.7})])
    assert score["a"] == pytest.approx(0.5 / 6) and score["b"] == pytest.approx(0.7 / 6)
    assert np.isnan(score["c"]) and n["a"] == 1


def test_winsorise():
    x = pd.Series(np.arange(101.0))
    w = f05.winsorise(x)
    assert w.min() == pytest.approx(1.0) and w.max() == pytest.approx(99.0)
