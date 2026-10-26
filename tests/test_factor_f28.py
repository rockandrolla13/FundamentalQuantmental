"""F28 HY index fair value gap net of carry: contract, no look-ahead, sign, helpers, edge cases."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from hy.backtest import decision_time
from hy.factors import f28_index_fair_value_gap as f28

AS_OF = pd.Timestamp("2012-12-31")
MONTHS = pd.date_range("2000-01-31", AS_OF, freq="ME")
DAY = pd.Timedelta(1, unit="D")
COEF = np.array([0.03, 0.0004, 0.004, 0.0008])   # true a, b_sloos, b_slope, b_vix of the synthetic spread


def _macro(seed: int = 0) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Three monthly series dated at month end, public the next day. Returns (long panel, wide matrix)."""
    rng = np.random.default_rng(seed)
    n = len(MONTHS)
    wide = pd.DataFrame({"DRTSCILM": np.cumsum(rng.normal(0, 5, n)) % 60 - 20,
                         "T10Y3M": 1.5 + np.sin(np.arange(n) / 12.0) * 1.5,
                         "VIXCLS": 20 + 8 * np.cos(np.arange(n) / 7.0) + rng.normal(0, 2, n)}, index=MONTHS)
    rows = [{"series_id": c, "date": d, "value": v, "available_at": d + DAY}
            for c in wide.columns for d, v in wide[c].items()]
    return pd.DataFrame(rows), wide


def _hy(wide: pd.DataFrame, noise: float = 0.002, seed: int = 1, last_gap: float = 0.0) -> pd.DataFrame:
    """Spread = true fair value + noise; `last_gap` shifts the as_of month."""
    rng = np.random.default_rng(seed)
    s = COEF[0] + wide.to_numpy() @ COEF[1:] + rng.normal(0, noise, len(wide))
    s[-1] = COEF[0] + wide.iloc[-1].to_numpy() @ COEF[1:] + last_gap
    return pd.DataFrame({"date": MONTHS, "spread": s, "available_at": MONTHS + DAY, "name": "synthetic"})


def _panels(last_gap: float = 0.0, **kw):
    mac, wide = _macro()
    return {"hy_index": _hy(wide, last_gap=last_gap, **kw), "macro_series": mac}


def _run(panels, **kw) -> pd.Series:
    kw.setdefault("duration", 4.0)
    out = f28.compute(panels, AS_OF, **kw)
    assert len(out) == 1
    return out.iloc[0]


# ---------------------------------------------------------------- contract


def test_meta_and_columns():
    for k in ("rank", "name", "level", "horizon_months", "needs", "spec", "section"):
        assert k in f28.META
    assert f28.META["rank"] == 28 and f28.META["level"] == "index"
    out = f28.compute(_panels(), AS_OF, duration=4.0)
    assert list(out.columns) == f28.COLS
    assert len(out) == 1 and out["index"].iloc[0] == "US_HY"
    assert out["date"].iloc[0] == AS_OF and out["available_at"].iloc[0] == decision_time(AS_OF)
    assert out["status"].iloc[0] == "ok" and np.isfinite(out["score"].iloc[0])


def test_fit_close_to_truth():
    r = _run(_panels())
    assert r["r2"] > 0.8 and r["n_train"] == len(MONTHS)
    assert abs(r["misalignment"]) < 0.002


# ---------------------------------------------------------------- no look-ahead


def test_no_lookahead():
    p = _panels(last_gap=0.01)
    base = _run(p)
    later = pd.date_range(AS_OF + pd.offsets.MonthEnd(1), periods=6, freq="ME")
    hy = pd.concat([p["hy_index"], pd.DataFrame({"date": later, "spread": 0.5, "available_at": later + DAY})])
    # same-month row published after the decision time, and a late vintage of an old macro month
    hy = pd.concat([hy, pd.DataFrame({"date": [AS_OF], "spread": [0.9], "available_at": [decision_time(AS_OF) + DAY]})])
    mac = p["macro_series"]
    extra = pd.DataFrame({"series_id": "VIXCLS", "date": list(later) + [MONTHS[10], AS_OF],
                          "value": [99.0] * 6 + [500.0, 500.0],
                          "available_at": list(later + DAY) + [AS_OF + 30 * DAY, decision_time(AS_OF) + DAY]})
    out = _run({"hy_index": hy, "macro_series": pd.concat([mac, extra])})
    for c in ("score", "spread", "fair_spread", "misalignment", "alpha_h", "n_train"):
        assert out[c] == pytest.approx(base[c], nan_ok=True)


def test_late_vintage_used_only_after_release():
    mac, _ = _macro()
    rows = mac[mac["series_id"] == "DRTSCILM"].copy()
    rows["date"], rows["available_at"] = pd.to_datetime(rows["date"]), pd.to_datetime(rows["available_at"])
    d = MONTHS[50]
    rev = pd.DataFrame({"series_id": ["DRTSCILM"], "date": [d], "value": [123.0], "available_at": [MONTHS[52] + DAY]})
    r = pd.concat([rows, rev])
    assert f28.macro_at(r, d) == pytest.approx(rows.loc[rows["date"] == d, "value"].iloc[0])
    assert f28.macro_at(r[r["date"] <= d], MONTHS[52]) == 123.0


# ---------------------------------------------------------------- sign


def test_cheap_index_goes_long():
    r = _run(_panels(last_gap=0.02))
    assert r["misalignment"] > 0.015 and r["score"] > 0 and r["position"] == 1.0


def test_rich_index_goes_short():
    r = _run(_panels(last_gap=-0.03))
    assert r["misalignment"] < -0.025 and r["score"] < 0 and r["position"] == -1.0


def test_small_rich_gap_with_carry_never_short():
    r = _run(_panels(last_gap=-0.001))
    assert r["misalignment"] < 0
    assert r["score"] == pytest.approx(4.0 * r["misalignment"] + r["spread"] * 6 / 12)
    assert r["position"] in (0.0, 1.0)
    assert _run(_panels(last_gap=-0.001), threshold=0.5)["position"] == 0.0


# ---------------------------------------------------------------- helpers


def test_fit_fair_value_recovers_coefficients():
    _, wide = _macro()
    y = pd.Series(COEF[0] + wide.to_numpy() @ COEF[1:], index=MONTHS)
    f = f28.fit_fair_value(y, wide)
    np.testing.assert_allclose(f["coef"], COEF, atol=1e-10)
    assert f["r2"] == pytest.approx(1.0) and f["n"] == len(MONTHS)
    assert f28.fit_fair_value(y.iloc[:10], wide.iloc[:10])["coef"] is None


def test_fair_spread_weight():
    assert f28.fair_spread(np.array([0.01, 2.0]), [0.02], 0.08, 0.0) == pytest.approx(0.05)
    assert f28.fair_spread(np.array([0.01, 2.0]), [0.02], 0.08, 0.25) == pytest.approx(0.25 * 0.08 + 0.75 * 0.05)


def test_edge_and_position_by_hand():
    assert f28.carry_over(0.05, 6) == pytest.approx(0.025)
    assert f28.carry_adjusted_edge(0.01, 0.05, 4.0, 6, 1.0) == pytest.approx(0.04 + 0.025)
    assert f28.carry_adjusted_edge(-0.01, 0.05, 4.0, 6, 0.5) == pytest.approx(-0.02 + 0.025)
    assert f28.edge_position(0.065, 0.0) == 1.0
    assert f28.edge_position(-0.01, 0.02) == 0.0
    assert f28.edge_position(-0.03, 0.02) == -1.0
    assert f28.edge_position(0.02, 0.02) == 0.0          # strict inequality, rule (3)
    assert np.isnan(f28.edge_position(np.nan))


def test_convergence_alpha_half_of_gap():
    """A series that closes half of each gap in h months gives alpha = 0.5 (about the 18-month share, p. 2)."""
    rng = np.random.default_rng(3)
    idx = pd.date_range("2001-01-31", periods=80, freq="ME")
    m = pd.Series(rng.normal(0, 0.01, 80), index=idx)
    s = pd.Series(0.05, index=idx, dtype=float)
    h = 6
    for i in range(80 - h):
        s.iloc[i + h] = s.iloc[i] - 0.5 * m.iloc[i]
    a, n = f28.convergence_alpha(m, s, h, min_obs=24)
    assert n == 80 - h and a == pytest.approx(0.5)
    assert np.isnan(f28.convergence_alpha(m.iloc[:20], s.iloc[:20], h)[0])


def test_macro_at_stale_and_missing():
    rows = pd.DataFrame({"series_id": "X", "date": pd.to_datetime(["2010-01-01"]), "value": [1.0],
                         "available_at": pd.to_datetime(["2010-02-02"])})
    assert np.isnan(f28.macro_at(rows, pd.Timestamp("2010-01-31")))      # public on 2 Feb, after the 1 Feb decision time
    assert f28.macro_at(rows, pd.Timestamp("2010-03-31")) == 1.0
    assert np.isnan(f28.macro_at(rows, pd.Timestamp("2010-12-31")))      # older than 190 days


def test_index_duration_from_bond_panel():
    b = pd.DataFrame({"date": AS_OF, "mod_dur": [3.0, 4.0, 5.0, 9.0], "carried": [False, False, False, True],
                      "years": 5.0, "yield": 0.08, "price": 95.0, "g_spread": 0.04,
                      "available_at": AS_OF + DAY})
    assert f28.index_duration(b, AS_OF, decision_time(AS_OF)) == pytest.approx(4.0)
    p = _panels(last_gap=0.02)
    p["bond_panel"] = b
    out = f28.compute(p, AS_OF).iloc[0]
    assert out["duration"] == pytest.approx(4.0) and out["status"] == "ok"


# ---------------------------------------------------------------- edge cases


def test_missing_panels_give_empty_frame():
    p = _panels()
    for drop in ("hy_index", "macro_series"):
        q = {k: v for k, v in p.items() if k != drop}
        out = f28.compute(q, AS_OF, duration=4.0)
        assert out.empty and list(out.columns) == f28.COLS


def test_short_history():
    r = _run(_panels(), min_train=len(MONTHS) + 1)
    assert r["status"] == "too_few_obs" and np.isnan(r["score"])


def test_no_duration():
    r = f28.compute(_panels(), AS_OF).iloc[0]
    assert r["status"] == "no_duration" and np.isnan(r["score"]) and np.isfinite(r["misalignment"])


def test_stale_or_missing_series():
    p = _panels()
    mac = p["macro_series"]
    p["macro_series"] = mac[~((mac["series_id"] == "VIXCLS") & (pd.to_datetime(mac["date"]) > AS_OF - pd.Timedelta(200, unit="D")))]
    assert _run(p)["status"] == "stale_macro"
    assert _run(_panels(), regressors=("DRTSCILM", "NOPE"))["status"] == "stale_macro"


def test_no_spread_in_month():
    p = _panels()
    p["hy_index"] = p["hy_index"][p["hy_index"]["date"] < AS_OF]
    r = _run(p)
    assert r["status"] == "no_spread" and np.isnan(r["score"])


def test_fitted_kappa():
    r = _run(_panels(last_gap=0.02), kappa=None)
    assert r["alpha_n"] >= f28.MIN_ALPHA_OBS and np.isfinite(r["alpha_h"])
    assert 0.0 <= r["kappa"] <= 1.0
    assert r["score"] == pytest.approx(r["kappa"] * 4.0 * r["misalignment"] + r["carry"])


def test_nan_spreads_ignored():
    p = _panels()
    hy = p["hy_index"].copy()
    hy.loc[5, "spread"] = np.nan
    r = _run({"hy_index": hy, "macro_series": p["macro_series"]})
    assert r["status"] == "ok" and r["n_train"] == len(MONTHS) - 1
