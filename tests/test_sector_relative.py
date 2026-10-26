"""Sector-relative factor scores and the sector composite (hy.sector.relative): within-sector ranks, equal and IC
weights, issuer-to-bond mapping, REGISTRY factors, ch. 16 equity momentum, empty frames, no look-ahead."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from hy.sector import relative as rl
from hy.sector.synthetic import make_panels

AS_OF = pd.Timestamp("2015-06-30")
DT = AS_OF + pd.Timedelta(1, unit="D")
LATE = DT + pd.Timedelta(5, unit="D")
FAST = ("sector_fs", "emc16")


@pytest.fixture(scope="module")
def panels():
    return make_panels(AS_OF, sectors={"10": 20, "25": 20, "35": 3}, cheap=["G10_3"], two_bonds=["G25_1"])


@pytest.fixture(scope="module")
def out(panels):
    return rl.compute(panels, AS_OF, factors=FAST)


def test_within_sector_rank():
    x = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, 10.0, 20.0, 30.0])
    s = pd.Series(["10"] * 5 + ["20"] * 3)
    r = rl.within_sector_rank(x, s)
    np.testing.assert_allclose(r[:5], [-0.3, -0.1, 0.1, 0.3, 0.5])
    assert r[5:].isna().all()                       # sector with fewer than MIN_SECTOR values: no rank


def test_meta_and_columns(out):
    for k in ("rank", "name", "level", "horizon_months", "needs", "spec", "section"):
        assert k in rl.META
    assert list(out.columns) == rl.BASE_COLS + ["rank_sector_fs", "rank_emc16"]
    assert out["cusip"].is_unique and (out["date"] == AS_OF).all() and (out["available_at"] == DT).all()


def test_equal_weights_are_the_mean_of_ranks(out):
    big = out[out["gsector"] != "35"]
    np.testing.assert_allclose(big["score"], big[["rank_sector_fs", "rank_emc16"]].mean(axis=1))
    assert (big["n_components"] == 2).all()
    assert out.loc[out["gsector"] == "35", "score"].isna().all()   # 3 issuers: below MIN_SECTOR


def test_planted_cheap_bond_tops_its_sector_on_value(out):
    e = out[out["gsector"] == "10"].set_index("cusip")
    assert e["rank_sector_fs"].idxmax() == "C10_3_0" and e.loc["C10_3_0", "rank_sector_fs"] == pytest.approx(0.5)


def test_flat_and_nested_weights(panels, out):
    only_fs = rl.compute(panels, AS_OF, factors=FAST, weights={"sector_fs": 1.0})
    big = only_fs["gsector"] != "35"
    np.testing.assert_allclose(only_fs.loc[big, "score"], out.loc[big, "rank_sector_fs"])
    assert (only_fs.loc[big, "n_components"] == 1).all()
    nested = rl.compute(panels, AS_OF, factors=FAST,
                        weights={"energy": {"sector_fs": 3.0, "emc16": 1.0}, "default": {"emc16": 1.0}})
    e = nested["group"] == "energy"
    np.testing.assert_allclose(nested.loc[e, "score"],
                               (3 * out.loc[e, "rank_sector_fs"] + out.loc[e, "rank_emc16"]) / 4)
    c = nested["group"] == "consumer_disc"
    np.testing.assert_allclose(nested.loc[c, "score"], out.loc[c, "rank_emc16"])
    with pytest.raises(ValueError):
        rl.compute(panels, AS_OF, factors=FAST, weights={"sector_fs": -1.0})


def test_ic_group_weights():
    ic = pd.DataFrame({"energy": [0.06, 0.02, -0.01], "utilities": [-0.02, -0.01, -0.03]},
                      index=["sector_fs", "emc16", "f10"])
    w = rl.ic_group_weights(ic)
    assert w["energy"] == pytest.approx({"sector_fs": 0.75, "emc16": 0.25, "f10": 0.0})
    assert sum(w["utilities"].values()) == 0.0


def test_group_without_positive_ic_has_no_score(panels):
    w = {"energy": {"sector_fs": 0.0, "emc16": 0.0}, "consumer_disc": {"sector_fs": 1.0}}
    res = rl.compute(panels, AS_OF, factors=FAST, weights=w)
    assert res.loc[res["group"] == "energy", "score"].isna().all()
    assert res.loc[res["group"] == "consumer_disc", "score"].notna().all()


def test_precomputed_issuer_frame_maps_to_every_bond(panels):
    fr = pd.DataFrame({"gvkey": [f"G25_{k}" for k in range(20)], "score": np.arange(20.0)})
    res = rl.compute(panels, AS_OF, factors=("custom",), frames={"custom": fr})
    c = res[res["gsector"] == "25"].set_index("cusip")
    assert c.loc["C25_1_0", "rank_custom"] == c.loc["C25_1_1", "rank_custom"]
    assert c["rank_custom"].idxmax() == "C25_19_0"


def test_registry_factor_and_index_factor(panels):
    res = rl.compute(panels, AS_OF, factors=(10,))
    assert "rank_f10" in res and res["rank_f10"].notna().sum() > 0
    with pytest.raises(ValueError):
        rl.compute(panels, AS_OF, factors=(25,))
    with pytest.raises(ValueError):
        rl.factor_frame("nope", panels, AS_OF)


def test_issuer_em_hand_check():
    months = pd.date_range(end=AS_OF, periods=6, freq="ME")
    r = [0.01, 0.02, -0.01, 0.03, 0.00, 0.02]
    eq = pd.DataFrame({"gvkey": "A", "datadate": months, "ret": r, "available_at": months + pd.Timedelta(1, unit="D")})
    short = eq.iloc[1:].assign(gvkey="B")              # five months: the 6-month window is incomplete
    late = pd.DataFrame({"gvkey": ["A"], "datadate": [AS_OF], "ret": [0.5], "available_at": [LATE]})
    em = rl.issuer_em(pd.concat([eq, short, late], ignore_index=True), AS_OF)
    r1, r3, r6 = r[-1], np.prod(1 + np.array(r[-3:])) - 1, np.prod(1 + np.array(r)) - 1
    assert em["A"] == pytest.approx((r1 + r3 / 3 + r6 / 6) / 3)
    assert "B" not in em.index or np.isnan(em["B"])


def test_sector_em_equal_weight():
    em = pd.Series({"a": 0.01, "b": 0.03, "c": -0.02})
    s = pd.Series({"a": "10", "b": "10", "c": "25"})
    np.testing.assert_allclose(rl.sector_em(em, s).sort_index().to_numpy(), [0.02, -0.02])


def test_missing_panels_give_empty(panels):
    for drop in ("bond_panel", "gics"):
        res = rl.compute({k: v for k, v in panels.items() if k != drop}, AS_OF, factors=FAST)
        assert res.empty and "score" in res
    no_eq = rl.compute({k: v for k, v in panels.items() if k != "equity_monthly"}, AS_OF, factors=FAST)
    assert no_eq["rank_emc16"].isna().all() and no_eq.loc[no_eq["gsector"] != "35", "score"].notna().all()


def test_no_lookahead(panels, out):
    p = {k: v.copy() for k, v in panels.items()}
    b = p["bond_panel"]
    p["bond_panel"] = pd.concat([b, b[b["date"] == AS_OF].assign(g_spread=0.02, available_at=LATE)], ignore_index=True)
    e = p["equity_monthly"]
    p["equity_monthly"] = pd.concat([e, e[e["datadate"] == AS_OF].assign(ret=0.9, available_at=LATE)],
                                    ignore_index=True)
    pd.testing.assert_frame_equal(rl.compute(p, AS_OF, factors=FAST), out)
