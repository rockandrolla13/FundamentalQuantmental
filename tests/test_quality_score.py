"""hy.quality.score: contract, no look-ahead, spread-free fundamentals, rating and blend variants, gap flags."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

import test_quality_fixtures as fx
from hy.quality import score as qs


def _with(p: dict, **extra) -> dict:
    return {**p, **extra}


# ---------------------------------------------------------------- contract


def test_meta_and_columns():
    for k in ("rank", "name", "level", "horizon_months", "needs", "spec", "section"):
        assert k in qs.META
    assert qs.META["spec"] == "docs/factors/QUALITY-rotation.md"
    out = qs.compute(fx.panels(), fx.AS_OF)
    assert list(out.columns) == qs.BOND_COLS
    assert out["cusip"].is_unique and len(out) == 2 * len(fx.issuers())
    assert (out["date"] == fx.AS_OF).all() and (out["available_at"] == fx.DT).all()
    assert out["score"].between(-0.5, 0.5).all()
    assert out.groupby("gvkey")["score"].nunique().eq(1).all()
    assert set(qs.WEIGHTS) == set(qs.SIGNS)


@pytest.mark.parametrize("kind,drop", [("fundamental", "compustat_annual"), ("fundamental", "annual_ebitda"),
                                       ("fundamental", "gics"), ("rating", "ratings"), ("blend", "bond_panel"),
                                       ("rating", "bond_panel"), ("fundamental", "bond_panel")])
def test_missing_panels_give_empty_frame(kind, drop):
    p = {k: v for k, v in fx.panels().items() if k != drop}
    out = qs.compute(p, fx.AS_OF, kind=kind)
    assert out.empty and list(out.columns) == qs.BOND_COLS


def test_blend_empty_only_without_both_groups():
    p = {k: v for k, v in fx.panels().items() if k not in ("ratings", "compustat_annual")}
    assert qs.compute(p, fx.AS_OF, kind="blend").empty


def test_bad_kind_raises():
    with pytest.raises(ValueError):
        qs.compute(fx.panels(), fx.AS_OF, kind="spread")


# ---------------------------------------------------------------- no look-ahead and no spread


def test_no_lookahead():
    base = qs.compute(fx.panels(), fx.AS_OF)
    p = fx.panels()
    qm = fx.issuers()
    late_ann, late_eb = fx.fundamentals({g: 1.0 - q for g, q in qm.items()})
    late_ann = late_ann[late_ann["fyear"] == 2011].assign(fyear=2012, datadate=pd.Timestamp("2012-03-31"),
                                                          available_at=fx.DT + pd.Timedelta(1, "D"))
    late_eb = late_eb[late_eb["fyear"] == 2011].assign(fyear=2012, datadate=pd.Timestamp("2012-03-31"),
                                                       available_at=fx.DT + pd.Timedelta(1, "D"))
    p["compustat_annual"] = pd.concat([p["compustat_annual"], late_ann], ignore_index=True)
    p["annual_ebitda"] = pd.concat([p["annual_ebitda"], late_eb], ignore_index=True)
    flip = p["ratings"].assign(splticrm="CCC", available_at=fx.DT + pd.Timedelta(5, "D"))
    p["ratings"] = pd.concat([p["ratings"], flip], ignore_index=True)
    nxt = fx.bonds(qm, [fx.AS_OF + pd.offsets.MonthEnd(1)])
    p["bond_panel"] = pd.concat([p["bond_panel"], nxt], ignore_index=True)
    pd.testing.assert_frame_equal(qs.compute(p, fx.AS_OF), base)


@pytest.mark.parametrize("kind", ["fundamental", "blend", "rating"])
def test_quality_does_not_use_the_spread(kind, rng):
    base = qs.compute(fx.panels(), fx.AS_OF, kind=kind)
    p = fx.panels()
    p["bond_panel"] = p["bond_panel"].assign(
        g_spread=p["bond_panel"]["g_spread"] * rng.uniform(0.2, 3.0, len(p["bond_panel"])))
    pd.testing.assert_frame_equal(qs.compute(p, fx.AS_OF, kind=kind), base)


# ---------------------------------------------------------------- sign and variants


def test_fundamental_rank_rises_with_quality():
    out = qs.compute(fx.panels(), fx.AS_OF, kind="fundamental")
    f = fx.by_issuer(out, "fund_rank")
    qm = pd.Series(fx.issuers())
    assert f.corr(qm.reindex(f.index), method="spearman") > 0.95
    assert f["HQC"] == f.max() and f["LQR"] == f.min()
    assert fx.by_issuer(out, "quintile")["HQC"] == 5 and fx.by_issuer(out, "quintile")["LQR"] == 1
    assert (fx.by_issuer(out, "n_components") == 8).all()


def test_component_signs_on_planted_names():
    out = qs.compute(fx.panels(), fx.AS_OF)
    x = out.drop_duplicates("gvkey").set_index("gvkey")
    assert x.loc["HQC", "x_leverage"] < x.loc["LQR", "x_leverage"]
    assert x.loc["HQC", "x_coverage"] > x.loc["LQR", "x_coverage"]
    assert x.loc["HQC", "x_cyclicality"] < x.loc["LQR", "x_cyclicality"]
    assert x.loc["HQC", "x_headroom"] >= x.loc["LQR", "x_headroom"]


def test_rating_only_works_without_fundamentals():
    p = {k: v for k, v in fx.panels().items() if k not in ("compustat_annual", "annual_ebitda", "gics")}
    out = qs.compute(p, fx.AS_OF, kind="rating")
    assert len(out) and out["score"].notna().all()
    r = fx.by_issuer(out, "rating_rank")
    assert r["HQC"] > r["G10"] > r["LQR"]
    assert out["fund_rank"].isna().all() and out["fund_rating_gap"].isna().all()
    assert set(fx.by_issuer(out, "rating_bucket")) == {"BB", "B", "CCC"}


def test_blend_is_between_parts_and_needs_both_by_default():
    out = qs.compute(fx.panels(), fx.AS_OF, kind="blend")
    assert out["score"].notna().all()
    p = {k: v for k, v in fx.panels().items() if k != "ratings"}
    assert qs.compute(p, fx.AS_OF, kind="blend")["score"].isna().all()
    one = qs.compute(p, fx.AS_OF, kind="blend", blend_min_parts=1)
    pd.testing.assert_series_equal(one["score"], qs.compute(p, fx.AS_OF, kind="fundamental")["score"])


def test_blend_weights_move_toward_rating():
    rating_heavy = qs.compute(fx.panels(), fx.AS_OF, blend_weights={"fundamental": 0.0, "rating": 1.0})
    rating = qs.compute(fx.panels(), fx.AS_OF, kind="rating")
    pd.testing.assert_series_equal(rating_heavy["score"], rating["score"])


def test_gap_flags_mislabelled_issuers():
    qm = {**fx.issuers(), "MISU": 0.97, "MISD": 0.03}
    p = fx.panels(qm)
    r = p["ratings"]
    r.loc[r["gvkey"] == "MISU", "splticrm"] = "CCC"
    r.loc[r["gvkey"] == "MISD", "splticrm"] = "BB"
    out = qs.compute(p, fx.AS_OF)
    gap, flag = fx.by_issuer(out, "fund_rating_gap"), fx.by_issuer(out, "gap_flag")
    assert gap["MISU"] > qs.GAP_FLAG and flag["MISU"] == "upgrade_candidate"
    assert gap["MISD"] < -qs.GAP_FLAG and flag["MISD"] == "downgrade_candidate"
    assert flag["G15"] is None or pd.isna(flag["G15"])
    assert (fx.by_issuer(out, "rclass_src") == "actual").all()


def test_defaulted_issuer_leaves_universe():
    p = fx.panels()
    p["ratings"].loc[p["ratings"]["gvkey"] == "G05", "splticrm"] = "D"
    assert "G05" not in set(qs.compute(p, fx.AS_OF)["gvkey"])


def test_financials_get_no_fundamental_score():
    p = fx.panels(sectors={"G10": "40"})
    f = fx.by_issuer(qs.compute(p, fx.AS_OF, kind="fundamental"), "fund_rank")
    assert np.isnan(f["G10"]) and f.drop("G10").notna().all()


def test_within_sector_ranks_each_sector():
    qm = fx.issuers()
    sectors = {g: ("25" if i % 2 else "20") for i, g in enumerate(qm)}
    out = qs.compute(fx.panels(sectors=sectors), fx.AS_OF, kind="fundamental", within="sector")
    f = fx.by_issuer(out, "fund_rank")
    assert f.notna().all()
    # the top of each sector by latent quality scores near the top of the universe rank
    s = pd.Series(sectors)
    for sec in ("20", "25"):
        names = s[s == sec].index
        best = pd.Series(qm)[names].idxmax()
        assert f[names].idxmax() == best


def test_min_components():
    x = pd.DataFrame({k: [0.1, np.nan] for k in qs.COMPONENTS}, index=["a", "b"])
    x.loc["b", ["leverage", "coverage", "size"]] = 0.2
    c = qs.composite(x)
    assert c.loc["a", "n_components"] == len(qs.COMPONENTS) and np.isclose(c.loc["a", "fund_raw"], 0.1)
    assert c.loc["b", "n_components"] == 3 and np.isnan(c.loc["b", "fund_raw"])


def test_leverage_panel_overrides_annual():
    p = fx.panels()
    lv = pd.DataFrame({"date": fx.AS_OF, "gvkey": ["HQC", "LQR"], "leverage": [9.0, -1.0],
                       "ltm_ebitda": [10.0, -5.0], "debt": [90.0, 5.0], "available_at": fx.DT})
    x = qs.fundamental_inputs(_with(p, leverage=lv), fx.AS_OF)
    assert x.loc["HQC", "x_leverage"] == 9.0 and np.isinf(x.loc["LQR", "x_leverage"])
    late = lv.assign(available_at=fx.DT + pd.Timedelta(1, "D"))
    x2 = qs.fundamental_inputs(_with(p, leverage=late), fx.AS_OF)
    assert x2.loc["HQC", "x_leverage"] == pytest.approx(2.0)


def test_quintile_mapping():
    q = qs.quintile(pd.Series([-0.5, -0.31, 0.0, 0.29, 0.5, np.nan]))
    assert list(q[:5]) == [1, 1, 3, 4, 5] and pd.isna(q.iloc[5])
