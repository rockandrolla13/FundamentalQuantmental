"""hy.quality.valuation: residual fit, planted cheap HQ and rich LQ, rating-bucket groups, no look-ahead."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

import test_quality_fixtures as fx
from hy.quality import valuation as qv


def test_columns_and_contract():
    out = qv.compute(fx.panels(), fx.AS_OF)
    assert list(out.columns) == qv.COLS
    assert out["cusip"].is_unique and (out["available_at"] == fx.DT).all()
    assert out["score"].equals(out["resid"])
    assert out["fit_n"].iloc[0] >= qv.MIN_FIT
    assert out["fit_b_quality"].iloc[0] < 0          # the market pays less spread for more quality
    assert np.allclose(out["dts"], out["mod_dur"] * out["g_spread"])


def test_missing_panels_give_empty_frame():
    p = {k: v for k, v in fx.panels().items() if k != "bond_panel"}
    out = qv.compute(p, fx.AS_OF)
    assert out.empty and list(out.columns) == qv.COLS
    p = {k: v for k, v in fx.panels().items() if k != "ratings"}
    assert qv.compute(p, fx.AS_OF, kind="rating").empty


@pytest.mark.parametrize("kind", ["blend", "fundamental"])
def test_planted_cheap_hq_and_rich_lq_are_found(kind):
    out = qv.compute(fx.panels(), fx.AS_OF, kind=kind)
    top_hq = qv.candidates(out, "cheap_hq", n=1)
    top_lq = qv.candidates(out, "rich_lq", n=1)
    assert top_hq["gvkey"].iloc[0] == "HQC" and top_hq["resid"].iloc[0] > 0
    assert top_lq["gvkey"].iloc[0] == "LQR" and top_lq["resid"].iloc[0] < 0
    assert out.loc[out["gvkey"] == "HQC", "spread_gap"].gt(0).all()
    assert out.loc[out["gvkey"] == "LQR", "conv_return"].lt(0).all()


def test_rating_bucket_groups_find_bb_and_ccc():
    out = qv.compute(fx.panels(), fx.AS_OF, hq_def="rating", hq_ratings=("BB",), lq_ratings=("CCC",))
    assert set(out.loc[out["is_hq"], "rating_bucket"]) == {"BB"}
    assert set(out.loc[out["is_lq"], "rating_bucket"]) == {"CCC"}
    assert qv.candidates(out, "cheap_hq", n=1)["gvkey"].iloc[0] == "HQC"
    assert qv.candidates(out, "rich_lq", n=1)["gvkey"].iloc[0] == "LQR"


def test_lists_cut_by_rating_bucket():
    out = qv.compute(fx.panels(), fx.AS_OF, hq_def="rating", hq_ratings=("BB",), lq_ratings=("B", "CCC"))
    only_b = qv.candidates(out, "cheap_lq", buckets=("B",))
    assert len(only_b) and set(only_b["rating_bucket"]) == {"B"}
    only_ccc = qv.candidates(out, "rich_lq", buckets=("CCC",))
    assert set(only_ccc["rating_bucket"]) == {"CCC"} and only_ccc["gvkey"].iloc[0] == "LQR"
    allq = qv.candidates(out, "rich_lq", one_per_issuer=False)
    assert allq["rich_lq_rank"].is_monotonic_increasing


def test_both_definition_is_intersection():
    s = qv.compute(fx.panels(), fx.AS_OF, hq_def="score")
    r = qv.compute(fx.panels(), fx.AS_OF, hq_def="rating")
    b = qv.compute(fx.panels(), fx.AS_OF, hq_def="both")
    assert (b["is_hq"] == (s["is_hq"] & r["is_hq"])).all()
    assert (b["is_lq"] == (s["is_lq"] & r["is_lq"])).all()


def test_rating_only_variant_finds_planted_pair_without_fundamentals():
    p = {k: v for k, v in fx.panels().items() if k not in ("compustat_annual", "annual_ebitda")}
    out = qv.compute(p, fx.AS_OF, kind="rating", hq_def="rating", hq_ratings=("BB",), lq_ratings=("CCC",))
    assert qv.candidates(out, "cheap_hq", n=1)["gvkey"].iloc[0] == "HQC"
    assert qv.candidates(out, "rich_lq", n=1)["gvkey"].iloc[0] == "LQR"


def test_fit_recovers_exact_relation():
    q = np.linspace(-0.5, 0.5, 40)
    d = 2.0 + 6.0 * ((np.arange(40) * 7) % 40) / 40.0
    s = np.exp(-3.0 - 1.2 * q + 0.3 * np.log(d))
    df = pd.DataFrame({"g_spread": s, "mod_dur": d, "quality_rank": q})
    res, info = qv.fit_residuals(df)
    assert np.allclose(res["resid"], 0.0, atol=1e-10) and np.allclose(info["coef"], [-3.0, -1.2, 0.3])
    lvl, info2 = qv.fit_residuals(df.assign(g_spread=0.05 - 0.02 * q + 0.001 * d), y_kind="level")
    assert np.allclose(lvl["resid"], 0.0, atol=1e-12) and np.isclose(info2["coef"][1], -0.02)


def test_fit_needs_min_bonds_and_skips_distressed():
    df = pd.DataFrame({"g_spread": [0.05] * 5, "mod_dur": [4.0] * 5, "quality_rank": np.linspace(-0.5, 0.5, 5)})
    res, info = qv.fit_residuals(df)
    assert res["resid"].isna().all() and info["n"] == 5
    big = pd.DataFrame({"g_spread": [0.04] * 30 + [0.5], "mod_dur": [4.0] * 31,
                        "quality_rank": list(np.linspace(-0.5, 0.5, 30)) + [0.0]})
    res2, info2 = qv.fit_residuals(big)
    assert info2["n"] == 30 and res2["resid"].iloc[-1] > 0


def test_no_lookahead():
    base = qv.compute(fx.panels(), fx.AS_OF)
    p = fx.panels()
    nxt = fx.bonds(fx.issuers(), [fx.AS_OF + pd.offsets.MonthEnd(1)])
    late = p["bond_panel"].assign(g_spread=0.5, available_at=fx.DT + pd.Timedelta(2, "D"))
    p["bond_panel"] = pd.concat([p["bond_panel"], nxt, late], ignore_index=True)
    pd.testing.assert_frame_equal(qv.compute(p, fx.AS_OF), base)


def test_diagnostics_off_by_default():
    out = qv.compute(fx.panels(), fx.AS_OF)
    assert out["lever"].isna().all() and out["var5"].isna().all()
    p = {k: v for k, v in fx.panels().items() if k != "ratings"}
    out2 = qv.compute(p, fx.AS_OF, kind="fundamental", diagnostics=True)   # F08 and F16 lack panels: NaN, no error
    assert len(out2) == len(out) and out2["lever"].isna().all() and out2["var5"].isna().all()
