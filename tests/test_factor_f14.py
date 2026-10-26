"""F14 bond abnormal trading volume: contract, no look-ahead, sign, zero months, issuer level, daily basis,
pre-event columns, next event, event study, helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from hy.backtest import decision_time
from hy.factors import f14_abnormal_volume as f14

AS_OF = pd.Timestamp("2015-06-30")
DT = decision_time(AS_OF)
MONTHS = pd.date_range(end=AS_OF, periods=18, freq="ME")
DAY = pd.Timedelta(1, unit="D")


def _row(cusip, gvkey, date, vol, n=10, carried=False):
    return {"date": date, "cusip": cusip, "gvkey": gvkey, "years": 5.0, "g_spread": 0.04, "price": 98.0,
            "yield": 0.07, "mod_dur": 4.0, "carried": carried, "par_volume": vol, "n_trades": n,
            "available_at": date + DAY}


def _panel(skip_d=True, carried_d=False):
    """A1 spikes 5x at t, A2 and B1 stay flat, C1 has 4 months only, D1 misses (or carries) month t-3."""
    rows = []
    for m in MONTHS:
        last = m == AS_OF
        rows.append(_row("A1", "A", m, 5e6 if last else 1e6, 50 if last else 10))
        rows.append(_row("A2", "A", m, 2e6, 20))
        rows.append(_row("B1", "B", m, 1e6, 10))
        if m >= MONTHS[-4]:
            rows.append(_row("C1", "C", m, 3e6, 30))
        if m == MONTHS[-4]:
            if carried_d:
                rows.append(_row("D1", "D", m, 1e6, 10, carried=True))
            continue
        rows.append(_row("D1", "D", m, 1e6, 10))
    return pd.DataFrame(rows)


def _days():
    return pd.bdate_range(end=AS_OF, periods=60)


def _daily(spike=6e5):
    """A1 and A2 trade every business day. Volume alternates 0.9e5 and 1.1e5. A1 spikes on the last 5 days."""
    days = _days()
    rows = []
    for i, d in enumerate(days):
        base = 0.9e5 if i % 2 == 0 else 1.1e5
        rows.append({"cusip": "A1", "date": d, "par_volume": spike if i >= len(days) - 5 else base, "n_trades": 2,
                     "available_at": d + DAY})
        rows.append({"cusip": "A2", "date": d, "par_volume": base, "n_trades": 2, "available_at": d + DAY})
    return pd.DataFrame(rows)


def _events():
    return pd.DataFrame([
        {"gvkey": "A", "event_date": AS_OF + pd.Timedelta(10, unit="D"), "event_type": "earnings",
         "available_at": AS_OF - pd.Timedelta(30, unit="D")},
        {"gvkey": "A", "event_date": AS_OF + pd.Timedelta(5, unit="D"), "event_type": "earnings",
         "available_at": DT + DAY},                                             # not yet known
        {"gvkey": "B", "event_date": AS_OF + pd.Timedelta(40, unit="D"), "event_type": "rating_review",
         "available_at": AS_OF - pd.Timedelta(3, unit="D")},
        {"gvkey": "D", "event_date": AS_OF + pd.Timedelta(3, unit="D"), "event_type": "litigation",
         "available_at": AS_OF - pd.Timedelta(3, unit="D")},                    # type not in EVENT_TYPES
    ])


def _out(panels, **kw) -> pd.DataFrame:
    return f14.compute(panels, AS_OF, **kw).set_index("cusip")


# ---------------------------------------------------------------- contract


def test_meta_and_columns():
    for k in ("rank", "name", "level", "horizon_months", "needs", "spec", "section"):
        assert k in f14.META
    assert f14.META["rank"] == 14 and f14.META["horizon_months"] == 1
    out = f14.compute({"bond_panel": _panel()}, AS_OF)
    assert list(out.columns) == f14.COLS
    assert out["cusip"].is_unique and set(out["cusip"]) == {"A1", "A2", "B1", "C1", "D1"}
    assert (out["date"] == AS_OF).all() and (out["available_at"] == DT).all()


def test_missing_panels():
    out = f14.compute({}, AS_OF)
    assert out.empty and list(out.columns) == f14.COLS
    out = _out({"bond_panel": _panel()})
    assert (out["volume_basis"] == "window7").all()
    assert out[["abn_vol_pre", "abn_vol_pre_z", "abn_trades_pre", "days_to_event"]].isna().all().all()
    assert out["next_event_type"].isna().all()


# ---------------------------------------------------------------- no look-ahead


def test_no_lookahead():
    base = f14.compute({"bond_panel": _panel(), "bond_daily": _daily(), "events": _events()}, AS_OF)
    p = _panel()
    later = pd.DataFrame([_row("A1", "A", AS_OF + pd.offsets.MonthEnd(1), 9e9, 900),
                          _row("B1", "B", AS_OF + pd.offsets.MonthEnd(1), 9e9, 900)])
    revised = pd.DataFrame([_row("B1", "B", AS_OF, 9e9, 900)]).assign(available_at=DT + DAY)
    d = _daily()
    d_late = pd.DataFrame([{"cusip": "A2", "date": AS_OF + DAY, "par_volume": 9e9, "n_trades": 99,
                            "available_at": AS_OF + 2 * DAY}])
    noisy = f14.compute({"bond_panel": pd.concat([p, later, revised], ignore_index=True),
                         "bond_daily": pd.concat([d, d_late], ignore_index=True), "events": _events()}, AS_OF)
    pd.testing.assert_frame_equal(base, noisy)


# ---------------------------------------------------------------- sign and formula


def test_sign_spike_scores_above_flat():
    out = _out({"bond_panel": _panel()})
    assert out.loc["A1", "score"] > out.loc["A2", "score"]
    assert out.loc["A1", "score"] > out.loc["B1", "score"]
    assert out.loc["B1", "abn_vol"] == pytest.approx(0.0, abs=1e-12)


def test_hand_values():
    out = _out({"bond_panel": _panel()})
    assert out.loc["A1", "abn_vol"] == pytest.approx(np.log1p(5e6) - np.log1p(1e6))
    assert out.loc["A1", "abn_ratio"] == pytest.approx(5.0)
    assert out.loc["A1", "abn_trades"] == pytest.approx(np.log1p(50) - np.log1p(10))
    assert out.loc["A1", "n_hist"] == 12
    # winsorisation keeps the order and stays inside the range
    s, a = out["score"].dropna(), out["abn_vol"].dropna()
    assert s.between(a.min(), a.max()).all() and s.rank().equals(a.rank())


def test_short_history_gives_nan():
    out = _out({"bond_panel": _panel()})
    assert out.loc["C1", "n_hist"] == 3 and np.isnan(out.loc["C1", "score"])
    assert np.isnan(out.loc["C1", "score"])
    out = _out({"bond_panel": _panel()}, min_hist=3)
    assert out.loc["C1", "abn_vol"] == pytest.approx(0.0, abs=1e-12)


@pytest.mark.parametrize("carried", [False, True])
def test_missing_or_carried_month_counts_zero(carried):
    out = _out({"bond_panel": _panel(carried_d=carried)})
    assert out.loc["D1", "n_hist"] == 12
    assert out.loc["D1", "abn_vol"] == pytest.approx(np.log1p(1e6) - np.log1p(11e6 / 12))


def test_issuer_level_fixed_bond_set():
    out = _out({"bond_panel": _panel()})
    assert out.loc["A1", "abn_vol_issuer"] == pytest.approx(np.log1p(7e6) - np.log1p(3e6))
    assert out.loc["A1", "n_bonds_issuer"] == 2 and out.loc["A2", "abn_vol_issuer"] == out.loc["A1", "abn_vol_issuer"]
    # C1 has no full history, so issuer C has no measure
    assert np.isnan(out.loc["C1", "abn_vol_issuer"])


def test_daily_basis_sums_full_month():
    out = _out({"bond_panel": _panel(), "bond_daily": _daily()})
    assert out.loc[["A1", "A2"], "volume_basis"].eq("month").all()
    # bonds without daily rows keep the panel window, so a partial bond_daily does not zero them
    assert out.loc[["B1", "C1", "D1"], "volume_basis"].eq("window7").all()
    assert out.loc["B1", "abn_vol"] == pytest.approx(0.0, abs=1e-12)
    d = _daily().assign(m=lambda x: x["date"] + pd.offsets.MonthEnd(0))
    v = d[d["cusip"] == "A2"].groupby("m")["par_volume"].sum()
    # the panel starts 18 months back, so months before the daily rows count as zero volume
    mean = v.reindex(MONTHS[-13:-1]).fillna(0.0).mean()
    assert out.loc["A2", "abn_vol"] == pytest.approx(np.log1p(v[AS_OF]) - np.log1p(mean))


# ---------------------------------------------------------------- pre-event and events


def test_pre_event_columns():
    out = _out({"bond_panel": _panel(), "bond_daily": _daily(), "events": _events()})
    days = _days()
    base = np.where(np.arange(len(days)) % 2 == 0, 0.9e5, 1.1e5)
    x = (np.where(np.arange(len(days)) >= len(days) - 5, 6e5, base) + base) / 2   # issuer A daily mean
    est = x[len(days) - 40:len(days) - 5]
    abn = x[-5:].mean() - est.mean()
    assert out.loc["A1", "abn_vol_pre"] == pytest.approx(abn)
    assert out.loc["A1", "abn_vol_pre_z"] == pytest.approx(abn / est.std(ddof=1))
    assert out.loc["A1", "abn_trades_pre"] == pytest.approx(0.0)
    assert np.isnan(out.loc["B1", "abn_vol_pre"])             # B has no daily trades


def test_next_event():
    out = _out({"bond_panel": _panel(), "events": _events()})
    assert out.loc["A1", "next_event_type"] == "earnings" and out.loc["A1", "days_to_event"] == 10
    assert out.loc["B1", "next_event_type"] == "rating_review" and out.loc["B1", "days_to_event"] == 40
    assert pd.isna(out.loc["D1", "next_event_type"])          # litigation is not in EVENT_TYPES


def test_event_abnormal_matches_source_equation():
    days = _days()
    ev = pd.DataFrame([{"gvkey": "A", "event_date": days[-8], "event_type": "earnings",
                        "available_at": days[-30]}])
    cg = pd.Series({"A1": "A", "A2": "A"})
    res = f14.event_abnormal(_daily(), ev, cg, AS_OF)
    assert list(res.columns) == f14.EVENT_COLS
    assert list(res["rel_day"]) == list(range(-5, 6))
    i0 = len(days) - 8
    base = np.where(np.arange(len(days)) % 2 == 0, 0.9e5, 1.1e5)
    x = (np.where(np.arange(len(days)) >= len(days) - 5, 6e5, base) + base) / 2
    est = x[i0 - 40:i0 - 5]
    r = res.set_index("rel_day")
    assert r.loc[0, "abn_vol"] == pytest.approx(x[i0] - est.mean())
    assert r.loc[5, "abn_vol"] == pytest.approx(x[i0 + 5] - est.mean())
    assert (res["n_bonds"] == 2).all()
    # an event whose window runs past as_of does not enter
    late = ev.assign(event_date=days[-3])
    assert f14.event_abnormal(_daily(), late, cg, AS_OF).empty


# ---------------------------------------------------------------- helpers


def test_helpers():
    assert f14.abnormal_log_volume(np.e - 1, 0.0) == pytest.approx(1.0)
    abn, z = f14.abnormal_measure([3.0, 5.0], [1.0, 2.0, 3.0])
    assert abn == pytest.approx(2.0) and z == pytest.approx(2.0)
    abn, z = f14.abnormal_measure([3.0], [1.0, 1.0])
    assert abn == pytest.approx(2.0) and np.isnan(z)
    assert np.isnan(f14.abnormal_measure([], [1.0, 2.0])[0])
