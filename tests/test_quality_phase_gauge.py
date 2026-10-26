"""hy.quality.phase (phase hook mapping, override, no look-ahead) and hy.quality.gauge (quality spread ratio)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

import test_quality_fixtures as fx
from hy.quality import gauge as qg
from hy.quality import phase as qp


# ---------------------------------------------------------------- phase hook


@pytest.mark.parametrize("phase,direction,expr", [
    ("late cycle", "up", "up_pair"), ("downturn", "up", "up_pair"), ("repair", "down", "down_pair"),
    ("recovery", "down", "down_pair"), ("expansion", None, None), ("Late_Cycle", "up", "up_pair"),
    ("nonsense", None, None), (None, None, None)])
def test_default_mapping(phase, direction, expr):
    assert qp.phase_direction(phase) == direction
    assert qp.phase_expression(phase) == expr


def test_mapping_is_a_hypothesis_and_overridable():
    assert qp.HYPOTHESIS is True
    assert qp.phase_expression("expansion", {"expansion": "down"}) == "down_pair"
    assert qp.phase_expression("downturn", {"downturn": None}) is None
    assert qp.phase_expression("downturn", legs="long") == "long_cheap_hq"
    assert qp.phase_expression("recovery", legs="short") == "short_rich_hq"
    with pytest.raises(ValueError):
        qp.phase_direction("downturn", {"downturn": "sideways"})


def _cp(rows) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["date", "cycle_phase", "available_at"])


def test_compute_reads_latest_known_phase():
    cp = _cp([(pd.Timestamp("2012-05-31"), "late cycle", pd.Timestamp("2012-06-01")),
              (fx.AS_OF, "downturn", fx.AS_OF),
              (fx.AS_OF, "recovery", fx.DT + pd.Timedelta(1, "D"))])       # revised after the decision time
    out = qp.compute({"cycle_phase": cp}, fx.AS_OF)
    assert list(out.columns) == qp.COLS and len(out) == 1
    r = out.iloc[0]
    assert r["cycle_phase"] == "downturn" and r["expression"] == "up_pair" and r["score"] == -1.0
    assert r["available_at"] == fx.DT and bool(r["hypothesis"])


def test_compute_missing_panel_and_unknown_phase():
    assert qp.compute({}, fx.AS_OF).empty
    out = qp.compute({"cycle_phase": _cp([(fx.AS_OF, "???", fx.AS_OF)])}, fx.AS_OF)
    assert np.isnan(out["score"].iloc[0]) and out["expression"].iloc[0] is None


def test_selloff_override(monkeypatch):
    cp = _cp([(fx.AS_OF, "downturn", fx.AS_OF)])
    fake = pd.DataFrame([{"compression_state": True}])
    monkeypatch.setattr(qp.f27, "compute", lambda panels, as_of: fake)
    p = {"cycle_phase": cp, "macro_series": pd.DataFrame({"x": [1]})}
    off = qp.compute(p, fx.AS_OF).iloc[0]
    on = qp.compute(p, fx.AS_OF, selloff_override=True).iloc[0]
    assert off["direction"] == "up" and bool(off["rate_selloff"])
    assert on["direction"] == "down" and on["expression"] == "down_pair" and on["score"] == 1.0


# ---------------------------------------------------------------- gauge


MONTHS = fx.months(5)


def _gpanels():
    return fx.panels(month_list=MONTHS, widen=lambda mi: 0.1 * mi)


def test_month_ratio_matches_hand_median():
    p = _gpanels()
    r = qg.month_ratio(p, fx.AS_OF)
    from hy.quality import score as qs
    q = qs.compute(p, fx.AS_OF)
    s = q["cusip"].map(p["bond_panel"][p["bond_panel"]["date"] == fx.AS_OF].set_index("cusip")["g_spread"])
    assert r["med_hq"] == pytest.approx(s[q["quintile"] == 5].median())
    assert r["med_lq"] == pytest.approx(s[q["quintile"] == 1].median())
    assert r["ratio_lq_hq"] == pytest.approx(r["med_lq"] / r["med_hq"]) and r["ratio_lq_hq"] > 1


def test_gauge_wide_quality_spread_scores_high():
    out = qg.compute(_gpanels(), fx.AS_OF, min_history_years=0.25, rating_ratios=False)
    assert list(out.columns) == qg.COLS and len(out) == 1
    r = out.iloc[0]
    assert r["n_hist"] == 4 and r["ratio_pct"] == 1.0 and r["score"] == 0.5
    assert r["available_at"] == fx.DT


def test_gauge_needs_history():
    out = qg.compute(_gpanels(), fx.AS_OF, rating_ratios=False)      # 3 years needed, 4 months held
    assert np.isnan(out["score"].iloc[0]) and out["n_hist"].iloc[0] == 4


def test_gauge_cache_equals_rebuild_and_ignores_late_rows():
    p = _gpanels()
    rebuilt = qg.compute(p, fx.AS_OF, min_history_years=0.25, rating_ratios=False)
    cache = qg.gauge_history(p, MONTHS[:-1], kind="blend", hq_def="score")
    assert list(cache.columns) == qg.HIST_COLS
    late = cache.assign(ratio_lq_hq=99.0, available_at=fx.DT + pd.Timedelta(1, "D"),
                        date=MONTHS[0] - pd.offsets.MonthEnd(1))
    p2 = {**p, "quality_gauge_history": pd.concat([cache, late.iloc[:1]], ignore_index=True)}
    cached = qg.compute(p2, fx.AS_OF, min_history_years=0.25, rating_ratios=False)
    pd.testing.assert_frame_equal(cached, rebuilt)


def test_gauge_rating_groups_and_f24_columns():
    out = qg.compute(_gpanels(), fx.AS_OF, hq_def="rating", hq_ratings=("BB",), lq_ratings=("CCC",),
                     min_history_years=0.25)
    r = out.iloc[0]
    assert r["hq_def"] == "rating" and r["ratio_lq_hq"] > 1
    for c in ("ratio_bb_bbb", "ratio_b_bb", "ratio_bb_bbb_pct", "ratio_b_bb_pct"):
        assert c in out.columns


def test_gauge_missing_panels_give_empty_frame():
    p = {k: v for k, v in _gpanels().items() if k != "bond_panel"}
    out = qg.compute(p, fx.AS_OF)
    assert out.empty and list(out.columns) == qg.COLS
