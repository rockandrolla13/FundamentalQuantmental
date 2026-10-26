"""hy.quality.trades: DTS-matched pairs, cross-bucket pairs, single legs, carry and jump-to-default, phase routing."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

import test_quality_fixtures as fx
from hy.quality import trades as qt
from hy.quality import valuation as qv


def _phase(name: str, at=None) -> pd.DataFrame:
    return pd.DataFrame([{"date": fx.AS_OF, "cycle_phase": name, "available_at": at or fx.AS_OF}])


def test_up_pair_is_dts_matched_and_holds_planted_names():
    legs = qt.compute(fx.panels(), fx.AS_OF, expression="up_pair")
    assert list(legs.columns) == qt.LEG_COLS
    lo, sh = legs[legs["leg"] == "long"], legs[legs["leg"] == "short"]
    assert "HQC" in set(lo["gvkey"]) and "LQR" in set(sh["gvkey"])
    assert lo["gvkey"].is_unique and sh["gvkey"].is_unique
    s = qt.summary(legs)
    assert s["net_dts"] == pytest.approx(0.0, abs=1e-12)
    assert s["long_mv"] == pytest.approx(1.0) and s["short_mv"] < 0
    assert (lo["score"] > 0).all() and (sh["score"] < 0).all()
    assert s["conv_return"] > 0
    assert (legs["date"] == fx.AS_OF).all() and (legs["available_at"] == fx.DT).all()


def test_cross_bucket_pair_long_cheap_bb_short_rich_ccc():
    legs = qt.compute(fx.panels(), fx.AS_OF, expression="up_pair", hq_def="rating", hq_ratings=("BB",),
                      lq_ratings=("CCC",), long_buckets=("BB",), short_buckets=("CCC",))
    lo, sh = legs[legs["leg"] == "long"], legs[legs["leg"] == "short"]
    assert set(lo["rating_bucket"]) == {"BB"} and set(sh["rating_bucket"]) == {"CCC"}
    assert lo.sort_values("resid", ascending=False)["gvkey"].iloc[0] == "HQC"
    assert sh.sort_values("resid")["gvkey"].iloc[0] == "LQR"
    assert qt.summary(legs)["net_dts"] == pytest.approx(0.0, abs=1e-12)


def test_down_pair_is_the_reverse():
    legs = qt.compute(fx.panels(), fx.AS_OF, expression="down_pair")
    lo, sh = legs[legs["leg"] == "long"], legs[legs["leg"] == "short"]
    assert len(lo) and len(sh)
    assert (lo["quintile"] == 1).all() and (sh["quintile"] == 5).all()
    assert (lo["weight_mv"] > 0).all() and (sh["weight_mv"] < 0).all()
    assert qt.summary(legs)["net_dts"] == pytest.approx(0.0, abs=1e-12)


@pytest.mark.parametrize("expr,leg,name", [("long_cheap_hq", "long", "HQC"), ("short_rich_lq", "short", "LQR")])
def test_single_leg_lists(expr, leg, name):
    legs = qt.compute(fx.panels(), fx.AS_OF, expression=expr)
    assert set(legs["leg"]) == {leg}
    assert legs.iloc[0]["gvkey"] == name
    mv = qt.summary(legs)["long_mv" if leg == "long" else "short_mv"]
    assert mv == pytest.approx(1.0 if leg == "long" else -1.0)


def test_rating_only_pair_without_fundamentals():
    p = {k: v for k, v in fx.panels().items() if k not in ("compustat_annual", "annual_ebitda")}
    legs = qt.compute(p, fx.AS_OF, expression="up_pair", kind="rating", hq_def="rating",
                      hq_ratings=("BB",), lq_ratings=("CCC",))
    assert "HQC" in set(legs.loc[legs["leg"] == "long", "gvkey"])
    assert "LQR" in set(legs.loc[legs["leg"] == "short", "gvkey"])


def test_dts_weights_equal_contribution_and_target():
    d = pd.Series([0.1, 0.2, 0.4])
    w = qt.dts_weights(d)
    assert w.sum() == pytest.approx(1.0) and np.allclose(w * d, (w * d).iloc[0])
    w2 = qt.dts_weights(d, target_dts=0.5)
    assert (w2 * d).sum() == pytest.approx(0.5) and np.allclose(w2 * d, 0.5 / 3)


def test_jtd_formula_and_asymmetry():
    j = qt.jtd(pd.Series([1.0, -2.0]), pd.Series([100.0, 60.0]), recovery=0.3)
    assert np.allclose(j, [0.7, 2.0 * 0.5])
    legs = qt.compute(fx.panels(), fx.AS_OF, expression="up_pair")
    s = qt.summary(legs)
    assert s["jtd_short_gain"] > 0 and s["jtd_long_loss"] > 0
    assert s["jtd_ratio"] == pytest.approx(s["jtd_short_gain"] / s["jtd_long_loss"])
    assert s["net_carry"] == pytest.approx(float((legs["weight_mv"] * legs["g_spread"]).sum()))


@pytest.mark.parametrize("phase,expr", [("downturn", "up_pair"), ("late_cycle", "up_pair"),
                                        ("Recovery", "down_pair"), ("repair", "down_pair")])
def test_phase_selects_expression(phase, expr):
    p = {**fx.panels(), "cycle_phase": _phase(phase)}
    legs = qt.compute(p, fx.AS_OF)
    assert len(legs) and set(legs["expression"]) == {expr}


def test_phase_without_expression_or_unknown_gives_empty():
    for p in ({**fx.panels(), "cycle_phase": _phase("expansion")}, fx.panels(),
              {**fx.panels(), "cycle_phase": _phase("downturn", at=fx.DT + pd.Timedelta(1, "D"))}):
        out = qt.compute(p, fx.AS_OF)
        assert out.empty and list(out.columns) == qt.LEG_COLS


def test_pair_without_a_leg_is_empty():
    v = qv.compute(fx.panels(), fx.AS_OF)
    v = v.assign(rich_lq=False)
    assert qt.build_legs(v, "up_pair").empty
    with pytest.raises(ValueError):
        qt.build_legs(v, "sideways")


def test_missing_panels_give_empty_frame():
    p = {k: v for k, v in fx.panels().items() if k != "bond_panel"}
    out = qt.compute(p, fx.AS_OF, expression="up_pair")
    assert out.empty and list(out.columns) == qt.LEG_COLS
