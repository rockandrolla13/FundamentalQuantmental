from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from hy.forecasts import FALLBACK_ORDER, ForecastRegistry, ForecastRow
from hy.macro import (
    CUT,
    PATH_NAMES,
    PHASE_PRIOR,
    bayes_update,
    build_paths,
    estimate_rho,
    fit_beta_table,
    path_prob_changes,
    phase_vote,
    region_stats,
    regions,
)

V = datetime(2026, 8, 1)
AV = datetime(2026, 8, 14)
T = datetime(2026, 9, 30)
NEUTRAL = {"pmi": 52.0, "hy_oas": {"level": 3.0, "median_5y": 4.0, "change_3m": -0.1}}


def _rows(var, src, mid, half, v=V, av=AV, method="survey_bins", h_max=10):
    out = []
    for h in range(h_max + 1):
        q = (mid - half, mid, mid + half) if half is not None else (np.nan, np.nan, np.nan)
        out.append(ForecastRow(src, var, h, v, av, mid, *q, method=method))
    return out


def _registry(gdp=0.018, cpi=0.025, extra=True):
    rows = _rows("gdp_growth", "spf", gdp, 0.02) + _rows("cpi", "spf", cpi, 0.012)
    if extra:
        rows += _rows("policy_rate", "fomc_sep", 0.035, 0.01, method="dot_range")
        rows += _rows("y2", "ust_forward", 0.036, None, method="market_implied")
        rows += _rows("y10", "ust_forward", 0.042, None, method="market_implied")
        rows += _rows("hy_spread", "ice", 0.032, None, method="market_implied")
        rows += _rows("default_rate", "moodys", 0.03, 0.01, method="agency")
        rows += _rows("pmi", "ism_consensus", 51.0, 2.0)
    return ForecastRegistry(rows)


# -- probabilities --------------------------------------------------------------------------------


def test_phase_prior_rows_sum_to_one():
    for phase, row in PHASE_PRIOR.items():
        assert tuple(row) == PATH_NAMES
        assert sum(row.values()) == pytest.approx(1.0, abs=1e-12), phase


def test_mass_prior_posterior_sum_to_one():
    ps = build_paths(_registry(), T, phase_indicators=NEUTRAL)
    assert sum(ps.mass.values()) == pytest.approx(1.0, abs=1e-6)
    assert sum(ps.prior.values()) == pytest.approx(1.0, abs=1e-12)
    assert sum(ps.posterior.values()) == pytest.approx(1.0, abs=1e-12)
    assert sum(p.prob for p in ps.paths) == pytest.approx(1.0, abs=1e-12)
    assert [p.name for p in ps.paths] == list(PATH_NAMES)
    assert all(p.y10.size == 8 for p in ps.paths)


def test_bayes_update_arithmetic_and_llr():
    prior = dict(zip(PATH_NAMES, (0.4, 0.2, 0.2, 0.1, 0.1)))
    mass = dict(zip(PATH_NAMES, (0.5, 0.1, 0.1, 0.2, 0.1)))
    post, llr = bayes_update(prior, mass)
    ev = sum(prior[k] * mass[k] for k in PATH_NAMES)
    for k in PATH_NAMES:
        assert post[k] == pytest.approx(prior[k] * mass[k] / ev)
        assert llr[k] == pytest.approx(np.log(post[k] / prior[k]))
    flat = dict.fromkeys(PATH_NAMES, 0.2)
    assert bayes_update(prior, flat)[0] == pytest.approx(prior)


def test_region_mass_matches_monte_carlo(rng):
    m, s, rho = np.array([-0.4, 0.3]), np.array([1.3, 0.8]), -0.35
    cov = np.array([[s[0] ** 2, rho * s[0] * s[1]], [rho * s[0] * s[1], s[1] ** 2]])
    z = rng.multivariate_normal(m, cov, size=400_000)
    stats = region_stats(m[0], m[1], s[0], s[1], rho, CUT)
    assert stats["mass"].sum() == pytest.approx(1.0, abs=1e-6)
    for name, (g1, g2, c1, c2) in regions(CUT).items():
        g_in = (z[:, 0] >= g1) & (z[:, 0] < g2) if np.isfinite(g1) else z[:, 0] < g2
        c_in = (z[:, 1] >= c1) & (z[:, 1] <= c2)
        inside = g_in & c_in
        assert stats.loc[name, "mass"] == pytest.approx(inside.mean(), abs=0.01), name
        assert stats.loc[name, "zg_mean"] == pytest.approx(z[inside, 0].mean(), abs=0.02), name
        assert stats.loc[name, "zc_mean"] == pytest.approx(z[inside, 1].mean(), abs=0.02), name


def test_lower_gdp_median_raises_recession_mass():
    base = build_paths(_registry(gdp=0.018), T, phase_indicators=NEUTRAL)
    weak = build_paths(_registry(gdp=0.002), T, phase_indicators=NEUTRAL)
    assert weak.mass["recession"] > base.mass["recession"]
    assert weak.posterior["recession"] > base.posterior["recession"]
    assert weak.path("recession").gdp_growth.mean() < base.path("recession").gdp_growth.mean()


def test_widen_factor_moves_mass_to_the_corners():
    narrow = build_paths(_registry(), T, phase_indicators=NEUTRAL)
    wide = build_paths(_registry(), T, phase_indicators=NEUTRAL, widen={("spf", "gdp_growth"): 2.0})
    assert wide.mass["soft_landing"] < narrow.mass["soft_landing"]


def test_path_levels_order_by_region():
    ps = build_paths(_registry(), T, phase_indicators=NEUTRAL)
    rec, soft = ps.path("recession"), ps.path("soft_landing")
    hfl, dis = ps.path("higher_for_longer"), ps.path("disinflation_rally")
    assert (rec.gdp_growth < soft.gdp_growth).all()
    assert (rec.index_spread > soft.index_spread).all()
    assert (rec.default_rate > soft.default_rate).all()
    assert (hfl.policy_rate > dis.policy_rate).all()
    assert (hfl.extra["cpi"] > dis.extra["cpi"]).all()


# -- yield split ----------------------------------------------------------------------------------


def test_yield_parts_add_up_per_path(rng):
    n = 40
    dg, dp = rng.normal(0, 0.01, n), rng.normal(0, 0.005, n)
    hist = pd.DataFrame({"d_growth_fcst": dg, "d_policy_exp": dp,
                         "dy2": 0.3 * dg + 1.0 * dp + rng.normal(0, 1e-4, n),
                         "dy10": 0.7 * dg + 0.4 * dp + rng.normal(0, 1e-4, n)})
    ps = build_paths(_registry(), T, phase_indicators=NEUTRAL, history=hist)
    for p in ps.paths:
        np.testing.assert_allclose(p.extra["dy_growth"] + p.extra["dy_policy"], p.extra["dy"], atol=1e-15)
        np.testing.assert_allclose(p.extra["dy_growth_y2"] + p.extra["dy_policy_y2"], p.extra["dy_y2"], atol=1e-15)
        np.testing.assert_allclose(p.y10 - p.extra["dy"], _registry().get(T, "y10")["point"].iloc[1:9], atol=1e-12)
    assert any("fitted on 40 rows" in a for a in ps.assumptions)


def test_fit_beta_table_recovers_betas_and_flags_wrong_sign(rng):
    frames = []
    truth = {("BB", "energy"): (-0.8, 1.5), ("B", "retail"): (-1.2, 2.0), ("CCC", "tech"): (0.9, 1.0)}
    for (rb, sec), (bg, bp) in truth.items():
        n = 400
        dg, dpe = rng.normal(0, 0.01, n), rng.normal(0, 0.005, n)
        dy = 0.5 * dg + 0.9 * dpe + rng.normal(0, 1e-3, n)
        g_part = 0.5 * dg
        ds = bg * g_part + bp * (dy - g_part) + rng.normal(0, 1e-4, n)
        frames.append(pd.DataFrame({"date": pd.RangeIndex(n), "rating_bucket": rb, "sector": sec, "ds": ds,
                                    "dy": dy, "d_growth_fcst": dg, "d_policy_exp": dpe}))
    tab = fit_beta_table(pd.concat(frames)).set_index(["rating_bucket", "sector"])
    for key, (bg, bp) in truth.items():
        assert tab.loc[key, "beta_g"] == pytest.approx(bg, abs=0.1)
        assert tab.loc[key, "beta_p"] == pytest.approx(bp, abs=0.1)
        assert tab.loc[key, "n"] == 400
    assert tab.loc[("CCC", "tech"), "flag"] == "sign_fail"
    assert not tab.loc[("CCC", "tech"), "sign_ok"]
    assert tab.loc[("BB", "energy"), "sign_ok"]


# -- no look-ahead and fallbacks ------------------------------------------------------------------


class SpyRegistry(ForecastRegistry):
    """Records every read. Fails when a read asks for a time other than the decision time."""

    def __init__(self, rows, t):
        super().__init__(rows)
        self.t, self.calls = t, []

    def as_of(self, decision_time, latest_only=True):
        self.calls.append(decision_time)
        assert decision_time == self.t, "read at a time other than the decision time"
        out = super().as_of(decision_time, latest_only)
        assert (pd.to_datetime(out["available_at"]) <= pd.Timestamp(self.t)).all()
        return out


def test_build_paths_never_reads_a_row_released_after_t():
    rows = list(_registry()._rows)
    late = _rows("gdp_growth", "spf", -0.08, 0.02, v=datetime(2026, 9, 25), av=datetime(2026, 10, 15))
    spy = SpyRegistry(rows + late, T)
    ps = build_paths(spy, T, phase_indicators=NEUTRAL)
    clean = build_paths(_registry(), T, phase_indicators=NEUTRAL)
    assert spy.calls and all(c == T for c in spy.calls)
    assert ps.mass == pytest.approx(clean.mass)
    np.testing.assert_allclose(ps.path("recession").gdp_growth, clean.path("recession").gdp_growth)
    assert ps.sources["gdp_growth"][2] <= pd.Timestamp(T)


def test_decision_before_release_uses_logged_fallbacks():
    early = datetime(2026, 8, 10)  # before AV
    ps = build_paths(SpyRegistry(_registry()._rows, early), early, phase_indicators=NEUTRAL)
    assert sum(ps.posterior.values()) == pytest.approx(1.0)
    assert ps.mass == pytest.approx(dict.fromkeys(PATH_NAMES, 0.2))
    assert ps.posterior == pytest.approx(ps.prior)  # flat likelihood: F6 table governs
    assert ps.sources["path_mass"][0] == "f6_table"
    for var in ("gdp_growth", "cpi", "policy_rate", "y2", "y10", "index_spread", "default_rate", "pmi"):
        assert ps.sources[var][0] in FALLBACK_ORDER, var
        assert any(a.startswith(f"{var}:") for a in ps.assumptions), var
    assert all(" > ".join(FALLBACK_ORDER) in a for a in ps.assumptions if "logged_assumption (" in a)


def test_policy_falls_back_to_market_implied_forward():
    reg = _registry()
    reg._rows = [r for r in reg._rows if r.source != "fomc_sep"]
    reg.add(_rows("policy_rate", "ust_forward", 0.033, None, method="market_implied"))
    ps = build_paths(reg, T, phase_indicators=NEUTRAL)
    assert ps.sources["policy_rate"][0] == "ust_forward"
    assert any(a.startswith("policy_rate: market_implied") for a in ps.assumptions)


# -- phase vote -----------------------------------------------------------------------------------


LATE = {
    "hy_oas": {"level": 5.0, "median_5y": 4.0, "change_3m": 0.4},
    "distress_ratio": {"level": 0.12, "median_5y": 0.08},
    "sloos_tightening": [5.0, 12.0],
    "pmi": 47.0,
    "default_rate": {"fcst": 0.05, "ttm": 0.035},
    "issuance_quality": {"ccc_share": 0.15, "ccc_median": 0.10, "covlite_share": 0.9, "covlite_median": 0.8},
}


def test_phase_vote_examples():
    phase, votes = phase_vote(LATE)
    assert phase == "downturn" and sum(votes.values()) == 6
    assert phase_vote({"pmi": 53.0, "hy_oas": False, "sloos_tightening": [3.0, -1.0]})[0] == "expansion"
    mid = {**{k: False for k in LATE}, "pmi": 48.0, "sloos_tightening": [1.0, 2.0]}
    assert phase_vote(mid)[0] == "late_cycle"
    # Two late votes out of three readings scale to four of six: downturn.
    assert phase_vote({"pmi": 48.0, "default_rate": True, "hy_oas": False})[0] == "downturn"
    assert phase_vote({})[0] == "late_cycle"
    assert phase_vote({}, prior_phase="repair")[0] == "repair"


def test_phase_vote_repair_and_recovery_rules():
    mid = {**{k: False for k in LATE}, "pmi": 48.0, "sloos_tightening": [1.0, 2.0], "default_rate": True}
    assert phase_vote(mid)[0] == "late_cycle"
    assert phase_vote(mid, prior_phase="downturn", prior_count=5)[0] == "repair"
    assert phase_vote(mid, prior_phase="repair", prior_count=3)[0] == "repair"
    low = {k: False for k in LATE}
    assert phase_vote(low, prior_phase="repair", prior_count=3)[0] == "recovery"
    assert phase_vote(low, prior_phase="recovery", prior_count=1)[0] == "recovery"
    assert phase_vote(low, prior_phase="recovery", prior_count=0)[0] == "expansion"
    assert phase_vote(mid, prior_phase="expansion", prior_count=1)[0] == "late_cycle"
    assert phase_vote(LATE, prior_phase="repair", prior_count=2)[0] == "downturn"


def test_phase_drives_the_prior():
    ps = build_paths(_registry(), T, phase_indicators=LATE)
    assert ps.phase == "downturn" and ps.prior == PHASE_PRIOR["downturn"]


# -- revision tracking ----------------------------------------------------------------------------


def test_path_prob_changes_arithmetic():
    a = build_paths(_registry(gdp=0.018), T, phase_indicators=NEUTRAL)
    b = build_paths(_registry(gdp=0.005), T, phase_indicators=LATE)
    d = path_prob_changes(a, b)
    for k in PATH_NAMES:
        assert d.loc[k, "d_posterior"] == pytest.approx(b.posterior[k] - a.posterior[k])
        assert d.loc[k, "d_prior"] == pytest.approx(b.prior[k] - a.prior[k])
        assert d.loc[k, "d_mass"] == pytest.approx(b.mass[k] - a.mass[k])
    assert d[["d_prior", "d_mass", "d_posterior"]].sum().abs().max() < 1e-9
    assert d.loc["recession", "d_posterior"] > 0


def test_estimate_rho(rng):
    x = rng.normal(size=500)
    hist = pd.DataFrame({"gdp_growth": x, "cpi": -0.5 * x + rng.normal(size=500)})
    assert estimate_rho(hist) == pytest.approx(-0.5 / np.sqrt(1.25), abs=0.07)
    assert estimate_rho(hist.head(3)) == -0.2


def test_reference_point_comes_from_history_when_given():
    import pandas as pd

    from hy import macro

    hist = pd.DataFrame({"gdp_growth": [0.03] * 6 + [0.01] * 6, "cpi": [0.02] * 12})
    ref = macro.reference_from_history(hist)
    assert ref["gdp_growth"][0] == pytest.approx(0.02) and ref["cpi"][0] == pytest.approx(0.02)


def test_sigma_comes_from_probability_bins_when_medians_have_no_range():
    from datetime import datetime

    from hy import macro
    from hy.forecasts import ForecastRegistry, ForecastRow

    v, a = datetime(2026, 8, 11), datetime(2026, 8, 15)
    rows = [ForecastRow("spf", var, h, v, a, mid, method="survey_median")
            for var, mid in (("gdp_growth", 0.02), ("cpi", 0.025)) for h in range(5)]
    rows += [ForecastRow("spf_prob", var, h, v, a, mid, mid - 0.0256, mid, mid + 0.0256, "survey_bins")
             for var, mid in (("gdp_growth", 0.02), ("cpi", 0.025)) for h in (1, 5)]
    ps = macro.build_paths(ForecastRegistry(rows), datetime(2026, 10, 21), phase_indicators={})
    assert not any("no quantiles" in x for x in ps.assumptions)
    assert any("sigma from spf_prob" in x for x in ps.assumptions)
