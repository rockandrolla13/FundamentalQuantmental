"""Tests for the rate and inflation stress screen (hy.events, methodology Section 9.2)."""

import numpy as np
import pandas as pd
import pytest

from hy import events as ev
from hy.sector.synthetic import make_panels


def _issuer(**kw):
    base = dict(gvkey="X", debt=500.0, ebitda=100.0, cash_interest=30.0, due_1y=25.0, due_2y=50.0,
                tsy_yield=0.04, spread=0.05, phi_float=0.3, passthrough=0.6, cost_base=300.0)
    base.update(kw)
    return base


def _cov(scen=ev.RateInflationScenario(), **kw):
    return float(ev.rate_inflation_screen(pd.DataFrame([_issuer(**kw)]), scen)["cov_stress"].iloc[0])


def test_cost_squeeze_passthrough_and_linearity():
    assert ev.cost_squeeze(300.0, 0.04, 1.0) == 0.0
    assert ev.cost_squeeze(300.0, 0.04, 0.0) == pytest.approx(12.0)
    assert ev.cost_squeeze(300.0, 0.08, 0.5) == pytest.approx(2 * ev.cost_squeeze(300.0, 0.04, 0.5))
    assert ev.cost_squeeze(300.0, 0.04, 1.7) == 0.0  # clipped


def test_quarterly_ladder_sums():
    m = ev.quarterly_ladder(40.0, 80.0)
    assert m.sum() == pytest.approx(120.0)
    assert ev.quarterly_ladder(40.0, 80.0, h=4).sum() == pytest.approx(40.0)


def test_coverage_falls_with_floating_share():
    covs = [_cov(phi_float=p) for p in (0.0, 0.3, 0.6, 0.9)]
    assert all(a > b for a, b in zip(covs, covs[1:]))


def test_coverage_falls_with_cost_inflation_when_sticky():
    lo = _cov(ev.RateInflationScenario(cost_inflation=0.0), passthrough=0.2)
    hi = _cov(ev.RateInflationScenario(cost_inflation=0.06), passthrough=0.2)
    full = _cov(ev.RateInflationScenario(cost_inflation=0.06), passthrough=1.0)
    assert hi < lo
    assert full == pytest.approx(lo)


def test_refinancing_below_old_coupon_raises_coverage():
    # old coupon 0.12 > new yield 0.04 + 0.015 + 0.05: rolling debt lowers interest
    scen = ev.RateInflationScenario(d_sofr=0.0)
    no_wall = _cov(scen, cash_interest=60.0, due_1y=0.0, due_2y=0.0, phi_float=0.0)
    wall = _cov(scen, cash_interest=60.0, due_1y=150.0, due_2y=150.0, phi_float=0.0)
    assert wall > no_wall


def test_double_hit_needs_wall_and_sticky():
    rows = [_issuer(gvkey="both", due_1y=150.0, due_2y=150.0, passthrough=0.1),
            _issuer(gvkey="wall_only", due_1y=150.0, due_2y=150.0, passthrough=0.9),
            _issuer(gvkey="sticky_only", due_1y=10.0, due_2y=10.0, passthrough=0.1),
            _issuer(gvkey="unknown", due_1y=150.0, due_2y=150.0, passthrough=np.nan)]
    out = ev.rate_inflation_screen(pd.DataFrame(rows)).set_index("gvkey")
    assert out["double_hit"].to_dict() == {"both": True, "wall_only": False, "sticky_only": False, "unknown": False}
    assert not out.loc["unknown", "terms_known"]


def test_rank_one_is_lowest_stressed_coverage():
    rows = [_issuer(gvkey=f"I{k}", phi_float=p) for k, p in enumerate((0.1, 0.9, 0.5))]
    out = ev.rate_inflation_screen(pd.DataFrame(rows))
    assert out.iloc[0]["gvkey"] == "I1"
    assert list(out["rank"]) == [1, 2, 3]


def test_stress_inputs_ignore_late_rows():
    p = make_panels(seed=1)
    base = ev.stress_inputs(p, "2015-06-30").set_index("gvkey")
    late = p["compustat_annual"].iloc[[0]].copy()
    late["datadate"] = pd.Timestamp("2015-06-30")
    late["dd1"] = 1e9
    late["available_at"] = pd.Timestamp("2015-08-01")  # after the decision time
    terms = pd.DataFrame({"gvkey": [late["gvkey"].iloc[0]], "phi_float": [0.99], "passthrough": [0.0],
                          "available_at": [pd.Timestamp("2015-09-01")]})
    p2 = dict(p, compustat_annual=pd.concat([p["compustat_annual"], late]), debt_terms=terms)
    after = ev.stress_inputs(p2, "2015-06-30").set_index("gvkey")
    g = late["gvkey"].iloc[0]
    assert after.loc[g, "due_1y"] == pytest.approx(base.loc[g, "due_1y"])
    assert np.isnan(after.loc[g, "phi_float"])


def test_planted_double_hit_ranks_first_on_synthetic_panels():
    p = make_panels(seed=2)
    ca = p["compustat_annual"].copy()
    target = "G25_3"
    i = ca.index[ca["gvkey"] == target]
    debt = float((ca.loc[i, "dlc"] + ca.loc[i, "dltt"]).iloc[0])
    ca.loc[i, "dd1"], ca.loc[i, "dd2"] = 0.3 * debt, 0.3 * debt
    p["compustat_annual"] = ca
    g = sorted(ca["gvkey"].unique())
    p["debt_terms"] = pd.DataFrame({"gvkey": g, "phi_float": [0.9 if x == target else 0.1 for x in g],
                                    "passthrough": [0.1 if x == target else 0.9 for x in g],
                                    "available_at": pd.Timestamp("2015-01-01")})
    out = ev.rate_inflation_screen(ev.stress_inputs(p, "2015-06-30"))
    top = out.sort_values("rank_exposure").iloc[0]
    assert top["gvkey"] == target and top["double_hit"]
    assert out["double_hit"].sum() == 1


def test_exposure_rank_ignores_start_level():
    rows = [_issuer(gvkey="strong_exposed", cash_interest=10.0, phi_float=0.9, passthrough=0.0),
            _issuer(gvkey="weak_sheltered", cash_interest=60.0, phi_float=0.0, passthrough=1.0,
                    due_1y=0.0, due_2y=0.0)]
    out = ev.rate_inflation_screen(pd.DataFrame(rows)).set_index("gvkey")
    assert out.loc["weak_sheltered", "rank"] == 1  # lowest level
    assert out.loc["strong_exposed", "rank_exposure"] == 1  # largest loss
    assert out.loc["weak_sheltered", "pct_loss"] == pytest.approx(0.0)
