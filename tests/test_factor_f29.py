"""Tests for F29 macro momentum (docs/factors/F29-macro-momentum.md). Small synthetic panels built here."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from hy.backtest import decision_time
from hy.factors import f29_macro_momentum as f

AS_OF = pd.Timestamp("2015-06-30")


def _monthly(series_id: str, values, last: str = "2015-05-31", lag_days: int = 1) -> pd.DataFrame:
    """Monthly readings ending at `last`, each released `lag_days` after the next month starts."""
    dates = pd.date_range(end=last, periods=len(values), freq="ME")
    return pd.DataFrame({"series_id": series_id, "date": dates, "value": np.asarray(values, dtype=float),
                         "available_at": dates + pd.Timedelta(lag_days, unit="D")})


def _counts(region: str, up, down, last: str = "2015-06-30") -> pd.DataFrame:
    dates = pd.date_range(end=last, periods=len(up), freq="ME")
    return pd.DataFrame({"date": dates, "region": region, "n_up": up, "n_down": down,
                         "available_at": dates - pd.Timedelta(10, unit="D")})


def _panels(local_up=True, global_up=True, rr=None) -> dict[str, pd.DataFrame]:
    loc = [50, 51, 52, 53] if local_up else [53, 52, 51, 50]
    glo = [50, 50.5, 51, 52] if global_up else [52, 51, 50.5, 50]
    p = {"macro_series": pd.concat([_monthly("ism_pmi", loc), _monthly("global_pmi", glo)], ignore_index=True)}
    if rr is not None:
        p["revision_counts"] = rr
    return p


def _rr_panel(up: bool) -> pd.DataFrame:
    a, b = ([40, 45, 50, 60], [60, 55, 50, 40]) if up else ([60, 50, 45, 40], [40, 50, 55, 60])
    return pd.concat([_counts("US", a, b), _counts("GLOBAL", a, b)], ignore_index=True)


# ---------------------------------------------------------------- contract


def test_meta_and_columns():
    for k in ("rank", "name", "level", "horizon_months", "needs", "spec", "section"):
        assert k in f.META
    assert f.META["rank"] == 29 and f.META["level"] == "index"
    out = f.compute(_panels(), AS_OF)
    assert list(out.columns) == f.COLS
    assert len(out) == 1 and out["index"].iloc[0] == "US_HY"
    assert out["date"].iloc[0] == AS_OF and out["available_at"].iloc[0] == decision_time(AS_OF)


def test_missing_panels_give_empty_frame():
    out = f.compute({}, AS_OF)
    assert out.empty and list(out.columns) == f.COLS
    assert f.compute({"macro_series": pd.DataFrame()}, AS_OF).empty


# ---------------------------------------------------------------- no look-ahead


def test_no_lookahead():
    base = _panels(rr=_rr_panel(True))
    ref = f.compute(base, AS_OF)
    dt = decision_time(AS_OF)
    late_ms = pd.DataFrame({"series_id": ["ism_pmi", "ism_pmi", "global_pmi"],
                            "date": [pd.Timestamp("2015-06-30"), pd.Timestamp("2015-07-31"), pd.Timestamp("2015-06-30")],
                            "value": [10.0, 5.0, 10.0],
                            "available_at": [dt + pd.Timedelta(1, unit="h"), dt + pd.Timedelta(30, unit="D"), dt + pd.Timedelta(1, unit="D")]})
    late_rc = pd.DataFrame({"date": [pd.Timestamp("2015-06-30")], "region": ["US"], "n_up": [0], "n_down": [100],
                            "available_at": [dt + pd.Timedelta(1, unit="h")]})
    bumped = {"macro_series": pd.concat([base["macro_series"], late_ms], ignore_index=True),
              "revision_counts": pd.concat([base["revision_counts"], late_rc], ignore_index=True)}
    pd.testing.assert_frame_equal(ref, f.compute(bumped, AS_OF))


# ---------------------------------------------------------------- sign


@pytest.mark.parametrize("loc,glo,want", [(True, True, 1.0), (False, False, -1.0), (True, False, 0.0)])
def test_pmi_sign(loc, glo, want):
    out = f.compute(_panels(loc, glo), AS_OF)
    assert out["pmi_signal"].iloc[0] == want and out["score"].iloc[0] == want
    assert out["score_basis"].iloc[0] == "pmi" and out["pmi_basis"].iloc[0] == "local_global"


def test_revision_sign_and_mean():
    up = f.compute(_panels(True, True, _rr_panel(True)), AS_OF)
    assert up["rr_signal"].iloc[0] == 1.0 and up["score"].iloc[0] == 1.0
    assert up["score_basis"].iloc[0] == "pmi+rr"
    mixed = f.compute(_panels(True, True, _rr_panel(False)), AS_OF)
    assert mixed["rr_signal"].iloc[0] == -1.0 and mixed["score"].iloc[0] == 0.0
    half = f.compute(_panels(True, False, _rr_panel(True)), AS_OF)
    assert half["score"].iloc[0] == 0.5


# ---------------------------------------------------------------- fallbacks and edges


def test_local_only_when_no_global():
    p = {"macro_series": _monthly("ism_pmi", [53, 52, 51, 50])}
    out = f.compute(p, AS_OF)
    assert out["pmi_signal"].iloc[0] == -1.0 and out["pmi_basis"].iloc[0] == "local"


def test_philly_proxy_when_no_ism():
    p = {"macro_series": _monthly("philly_gac", [-5, -2, 1, 4])}
    out = f.compute(p, AS_OF)
    assert out["pmi_source"].iloc[0] == "philly_gac" and out["score"].iloc[0] == 1.0


def test_revision_only():
    out = f.compute({"revision_counts": _rr_panel(True)}, AS_OF)
    assert out["score"].iloc[0] == 1.0 and out["score_basis"].iloc[0] == "rr"


def test_stale_pmi():
    p = {"macro_series": _monthly("ism_pmi", [50, 51, 52, 53], last="2015-02-28")}
    out = f.compute(p, AS_OF)
    assert np.isnan(out["score"].iloc[0]) and out["status"].iloc[0] == "stale"


def test_gap_in_pmi_gives_no_change():
    d = _monthly("ism_pmi", [50, 51, 52, 53])
    out = f.compute({"macro_series": d.drop(index=1)}, AS_OF)   # the reading 2 months back is missing
    assert np.isnan(out["pmi_local_chg"].iloc[0]) and out["status"].iloc[0] == "no_signal"


# ---------------------------------------------------------------- helpers


def test_revision_ratio_hand():
    assert np.allclose(f.revision_ratio([60, 30, 0], [40, 70, 0])[:2], [0.2, -0.4])
    assert np.isnan(f.revision_ratio([0], [0])[0])


def test_change_over_and_agree():
    s = pd.Series([50.0, 52.0, 55.0], index=pd.date_range("2015-01-31", periods=3, freq="ME"))
    assert f.change_over(s, 2) == 5.0
    assert np.isnan(f.change_over(s, 3))
    assert f.agree_signal(1.0, 2.0) == (1.0, "local_global")
    assert f.agree_signal(-1.0, -0.1) == (-1.0, "local_global")
    assert f.agree_signal(0.0, 1.0) == (0.0, "local_global")
    assert f.agree_signal(-2.0, np.nan) == (-1.0, "local")


def test_pc1_weights_hand():
    c = pd.DataFrame([[1.0, 0.5], [0.5, 1.0]], index=list("ab"), columns=list("ab"))
    assert np.allclose(f.pc1_weights(c), [0.5, 0.5])
    c3 = pd.DataFrame([[1.0, 0.8, 0.0], [0.8, 1.0, 0.0], [0.0, 0.0, 1.0]], index=list("abc"), columns=list("abc"))
    w = f.pc1_weights(c3)   # largest eigenvalue 1.8 with vector (1, 1, 0) / sqrt 2
    assert np.isclose(w.sum(), 1.0) and np.allclose(w, [0.5, 0.5, 0.0])


def test_averaged_spearman_hand():
    df = pd.DataFrame({"a": [1, 2, 3, 4, 5, 6], "b": [1, 3, 2, 4, 6, 5], "c": [6, 5, 4, 3, 2, 1]}, dtype=float)
    got = f.averaged_spearman(df, step=2)
    r0 = df.iloc[0::2].corr(method="spearman").loc["a", "b"]   # rows 0, 2, 4
    r1 = df.iloc[1::2].corr(method="spearman").loc["a", "b"]   # rows 1, 3, 5
    assert np.isclose(got.loc["a", "b"], (r0 + r1) / 2)
    assert got.loc["a", "c"] == 0.0 and got.loc["a", "a"] == 1.0   # negative correlation set to 0


def test_rolling_z_hand():
    x = pd.Series([1.0, 2.0, 3.0, 10.0], index=pd.date_range("2015-01-01", periods=4, freq="D"))
    z = f.rolling_z(x, "10D", min_obs=3)
    v = x.to_numpy()
    assert np.isnan(z.iloc[1]) and np.isclose(z.iloc[3], (10 - v.mean()) / v.std(ddof=1))


def test_beat_component_three_month_change():
    ms = _monthly("beat:growth:ip", [1, 2, 4, 7, 11], last="2015-05-31")
    shock = _monthly("shock:growth:ip", [0.1, -0.2], last="2015-05-31")
    ms = pd.concat([ms, ms.assign(value=99.0, available_at=ms["available_at"] + pd.Timedelta(5, unit="D")), shock])
    comps = f.beat_components(ms, "beat", "growth")
    assert list(comps) == ["ip"]
    assert np.allclose(comps["ip"].to_numpy(), [7 - 1, 11 - 2])    # first release only, change over 3 months
    assert np.allclose(f.beat_components(ms, "shock", "growth")["ip"].to_numpy(), [0.1, -0.2])


def _cycle_components(tail: float) -> pd.DataFrame:
    """Three growth levels on a common factor; the last 6 months move by `tail` per month."""
    rng = np.random.default_rng(7)
    n = 72
    g = np.sin(np.arange(n) / 6.0)
    g[-6:] = g[-7] + tail * np.arange(1, 7)
    rows = []
    for j, lag in enumerate((1, 8, 15)):
        vals = g + 0.1 * rng.standard_normal(n)
        rows.append(_monthly(f"beat:growth:s{j}", vals, last="2015-05-31", lag_days=lag))
    return pd.concat(rows, ignore_index=True)


@pytest.mark.parametrize("tail,sign", [(0.5, 1.0), (-0.5, -1.0)])
def test_beat_index_sign(tail, sign):
    out = f.compute({"macro_series": _cycle_components(tail)}, AS_OF)
    assert np.sign(out["growth_beat_z"].iloc[0]) == sign
    assert np.isnan(out["inflation_beat"].iloc[0]) and out["status"].iloc[0] == "no_signal"


def test_beat_index_no_lookahead():
    ms = _cycle_components(0.5)
    ref = f.compute({"macro_series": ms}, AS_OF)
    late = _monthly("beat:growth:s0", [50.0], last="2015-06-30", lag_days=2)   # released after decision time
    pd.testing.assert_frame_equal(ref, f.compute({"macro_series": pd.concat([ms, late])}, AS_OF))
