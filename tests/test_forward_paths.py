"""Tests for the forecast-linked scenarios of hy/forward.py (methodology Section 5.4; framework F6).

Synthetic issuers only. No real issuer figures.
"""

from __future__ import annotations

from datetime import datetime

import numpy as np
import pytest
from scipy.stats import kstest

from hy.events import MacroPath
from hy.forward import (
    LOSS_OF_CONTRACT,
    CaseWeights,
    DebtLine,
    DeclineModel,
    IssuerStart,
    apply_f66,
    base_from_consensus,
    base_scenario,
    case_weights_by_path,
    driver_shift,
    f6_cases,
    f6_weights,
    forward_features_by_path,
    forward_revisions,
    lev_mixture,
    link_drivers,
    mixture_pit,
    run_case_under_path,
    run_grid,
    run_scenario,
)

H = 8
DRIVERS = dict(v=0.60, a=0.20, inventory_days=60.0, receivable_days=45.0, payable_days=40.0, capex=8.0)
A4_TEMPLATE = {"annual": (-0.20, -0.10), "recovery_shape": "u", "trough_margin": 0.12}


def make_path(name: str, prob: float = 0.25, policy: float | np.ndarray = 0.04, gdp: float | np.ndarray = 0.02,
              spread: float = 0.04, default_rate: float = 0.03, pmi: float = 51.0) -> MacroPath:
    def arr(x):
        return np.full(H, x, dtype=float) if np.ndim(x) == 0 else np.asarray(x, dtype=float)

    return MacroPath(name=name, prob=prob, y2=arr(policy) + 0.002, y10=arr(policy) + 0.005, policy_rate=arr(policy),
                     gdp_growth=arr(gdp), pmi=arr(pmi), index_spread=arr(spread), default_rate=arr(default_rate))


def make_start(float_face: float = 200.0, notes_face: float = 200.0, maturity_q: int | None = 4,
               revolver: float = 60.0, cash0: float = 15.0, revenue_q0: float = 100.0) -> IssuerStart:
    lines = (
        DebtLine("term_loan", face=float_face, floating=True, spread=0.035, floor=0.005, amort=0.5),
        DebtLine("notes", face=notes_face, coupon=0.07, maturity_q=maturity_q),
    )
    e = revenue_q0 * 0.2
    return IssuerStart(
        revenue_q0=revenue_q0, ebitda_hist=(e, e, e, e), interest_hist=(7.0, 7.0, 7.0, 7.0), cash0=cash0,
        debt_lines=lines, revolver_commitment=revolver, revolver_spread=0.03, commitment_fee=0.005,
        inventory_days0=60.0, receivable_days0=45.0, payable_days0=40.0, cogs_ratio0=0.60, da_q=5.0, min_cash=5.0,
    )


def fns(p_access: float = 0.9, treasury: float = 0.04, s_fair: float = 0.05):
    return dict(
        s_fair_fn=lambda path, q: s_fair,
        p_refi_access_fn=lambda path, q: p_access,
        forward_treasury_fn=lambda path, q, tenor: treasury,
    )


def make_base(g: float = 0.01):
    return base_scenario(H, g=g, **DRIVERS)


# ---------------------------------------------------------------------------
# Monotonicity
# ---------------------------------------------------------------------------


def test_higher_policy_path_never_lowers_floating_interest():
    rng = np.random.default_rng(7)
    start = make_start(cash0=2.0)
    cases = f6_cases(make_base(0.0), "A4", (), A4_TEMPLATE)
    rate_fns = dict(
        s_fair_fn=lambda path, q: 0.05,
        p_refi_access_fn=lambda path, q: 0.9,
        forward_treasury_fn=lambda path, q, tenor: float(path.policy_rate[q - 1]) + 0.005,
    )
    for _ in range(40):
        lo = rng.uniform(0.0, 0.06, H)
        hi = lo + rng.uniform(0.0, 0.03, H)
        for sc in cases.values():
            a = run_case_under_path(start, sc, make_path("lo", policy=lo), **rate_fns)
            b = run_case_under_path(start, sc, make_path("hi", policy=hi), **rate_fns)
            assert np.all(b.interest >= a.interest - 1e-12)


def test_lower_gdp_path_never_raises_base_revenue():
    rng = np.random.default_rng(11)
    start = make_start()
    cases = {"base": make_base(0.01)}
    for beta in (0.1, 0.5, 2.0):
        for _ in range(20):
            hi_g = rng.uniform(-0.04, 0.05, H)
            lo_g = hi_g - rng.uniform(0.0, 0.04, H)
            paths = [make_path("hi", 0.5, gdp=hi_g), make_path("lo", 0.5, gdp=lo_g)]
            grid = run_grid(start, cases, paths, betas={"g": beta}, trend=0.02, **fns())
            assert np.all(grid[("base", "lo")].revenue <= grid[("base", "hi")].revenue + 1e-12)


def test_driver_shift_and_provenance():
    path = make_path("recession", gdp=-0.01)
    path.extra["provenance"] = {"gdp_growth": {"source": "spf", "vintage": datetime(2026, 8, 15)}}
    np.testing.assert_allclose(driver_shift(0.5, path.gdp_growth, 0.02), np.full(H, -0.015))
    shifted = link_drivers(make_base(0.01), path, {"g": 0.5}, 0.02)
    np.testing.assert_allclose(shifted.g, np.full(H, 0.01 - 0.015))
    prov = shifted.provenance["g"]
    assert prov["source"] == "spf" and prov["vintage"] == datetime(2026, 8, 15) and prov["beta"] == 0.5
    # hy.macro PathSet.sources form, keyed by variable.
    src = {"gdp_growth": ("spf", datetime(2026, 8, 1), datetime(2026, 8, 15), "survey_bins")}
    via_sources = link_drivers(make_base(0.01), make_path("m"), {"g": 0.5}, 0.02, forecast_rows=src)
    assert via_sources.provenance["g"]["source"] == "spf" and via_sources.provenance["g"]["method"] == "survey_bins"
    # No forecast row: the shift is logged as an assumption, not hidden.
    bare = link_drivers(make_base(0.01), make_path("x"), {"g": 0.5}, 0.02)
    assert bare.provenance["g"]["basis"] == "logged_assumption"


def test_base_from_consensus_stores_gaps():
    cons = dict(g=0.01, **DRIVERS)
    base = base_from_consensus(cons, {"g": 0.002, "v": -0.01})
    np.testing.assert_allclose(base.g, 0.012)
    np.testing.assert_allclose(base.v, 0.59)
    assert base.gaps == {"g": 0.002, "v": -0.01}
    assert base.forecast_source == "analyst"


# ---------------------------------------------------------------------------
# Refinance logic (F6.3)
# ---------------------------------------------------------------------------


def test_refinance_succeeds_above_half_at_forward_plus_fair():
    start = make_start(maturity_q=4)
    sc = make_base(0.01)
    path = make_path("flat", policy=0.04)
    ok = run_case_under_path(start, sc, path, **fns(p_access=0.6, treasury=0.04, s_fair=0.05))
    ref = run_scenario(start, sc, path.policy_rate)  # old coupon kept at the maturity
    rec = ok.refi_coupons["notes"]
    assert rec["status"] == "refinanced" and rec["new"] == pytest.approx(0.09) and rec["old"] == pytest.approx(0.07)
    assert ok.refi_fail_q is None and ok.claims_view is False
    np.testing.assert_allclose(ok.interest[:4], ref.interest[:4])
    # dCashInt = M (y_T + s_fair - c_old) / 4 in the first quarter after the maturity.
    assert ok.interest[4] - ref.interest[4] == pytest.approx(200.0 * (0.09 - 0.07) / 4.0)
    assert ok.macro_path == "flat"


def test_refinance_fails_at_or_below_half_and_engages_claims_view():
    start = make_start(maturity_q=4)
    sc = make_base(0.01)
    path = make_path("shut", policy=0.04)
    ref = run_scenario(start, sc, path.policy_rate)
    for p in (0.4, 0.5):
        bad = run_case_under_path(start, sc, path, distressed_coupon_add=0.05, **fns(p_access=p))
        assert bad.claims_view is True and bad.refi_fail_q == 4
        assert bad.refi_coupons["notes"]["status"] == "failed"
        assert bad.refi_coupons["notes"]["new"] == pytest.approx(0.12)
        assert bad.debt[4] == pytest.approx(ref.debt[4], rel=0.05)  # amount stays outstanding
        assert bad.interest[4] - ref.interest[4] == pytest.approx(200.0 * 0.05 / 4.0)


def test_no_maturity_no_refi_record():
    out = run_case_under_path(make_start(maturity_q=None), make_base(), make_path("m"), **fns(p_access=0.0))
    assert out.refi_coupons is None and out.refi_fail_q is None and not out.claims_view


# ---------------------------------------------------------------------------
# Case set (F6)
# ---------------------------------------------------------------------------


def test_management_absent_without_guidance():
    cases = f6_cases(make_base(), "A4", (), A4_TEMPLATE)
    assert "management" not in cases
    assert set(cases) == {"base", "down_moderate", "down_severe", "upside"}
    cases = f6_cases(make_base(), "A4", (), A4_TEMPLATE, guidance={"g": 0.02}, consensus=dict(g=0.012, **DRIVERS))
    assert cases["management"].forecast_source == "management"
    assert cases["management"].provenance["filled_from"]["case"] == "base"
    assert cases["consensus"].forecast_source == "consensus"


def test_severe_case_rules():
    cases = f6_cases(make_base(0.0), "A4", (), A4_TEMPLATE)
    mod, sev = cases["down_moderate"], cases["down_severe"]
    lvl = lambda s: np.cumprod(1 + s.g)  # noqa: E731
    assert lvl(sev).min() < lvl(mod).min()  # deeper decline
    np.testing.assert_allclose(sev.payable_days, mod.payable_days - 10.0)
    assert (1.0 - sev.v - sev.a).min() <= 0.12 - 0.01 + 1e-12  # margin below the historic trough


def test_m3_branch_and_a8():
    t = {**A4_TEMPLATE, "contract_share": 0.25}
    cases = f6_cases(make_base(), "A4", ("M3",), t)
    assert LOSS_OF_CONTRACT in cases
    assert np.cumprod(1 + cases[LOSS_OF_CONTRACT].g)[-1] < np.cumprod(1 + cases["down_moderate"].g)[-1]
    with pytest.raises(ValueError):
        f6_cases(make_base(), "A4", ("M3",), A4_TEMPLATE)
    with pytest.raises(ValueError):
        f6_cases(make_base(), "A8", (), A4_TEMPLATE)


def test_coin_toss_recorded():
    rec = [True, False] * 6
    cases = f6_cases(make_base(), "A4", (), A4_TEMPLATE, analyst_record=rec)
    assert cases["base"].provenance["coin_toss"]["result"] == "pass"
    cases = f6_cases(make_base(), "A4", (), A4_TEMPLATE, analyst_record=[True] * 12)
    assert cases["base"].provenance["coin_toss"]["result"] == "fail"


# ---------------------------------------------------------------------------
# Weights (F6 table, archetype adjustment, M3, F6.6)
# ---------------------------------------------------------------------------


def test_archetype_adjustment_numbers():
    w = f6_weights("late_cycle", "A4")
    tot = 0.50 + 0.25 * 1.3 + 0.10 * 1.3 + 0.15
    assert w["base"] == pytest.approx(0.50 / tot)  # 0.452489
    assert w["down_moderate"] == pytest.approx(0.325 / tot)  # 0.294118
    assert w["down_severe"] == pytest.approx(0.13 / tot)  # 0.117647
    assert w["upside"] == pytest.approx(0.15 / tot)
    w5 = f6_weights("Late cycle", "A5")
    tot5 = 0.50 + 0.25 * 0.7 + 0.10 * 0.7 + 0.15
    assert w5["base"] == pytest.approx(0.50 / tot5)  # 0.558659
    assert w5.down_multiplier == 0.7
    assert dict(f6_weights("late_cycle", "A5", contracted_revenue=False)) == pytest.approx(
        {"base": 0.5, "down_moderate": 0.25, "down_severe": 0.10, "upside": 0.15})
    assert dict(f6_weights("expansion", "A6")) == pytest.approx(
        {"base": 0.60, "down_moderate": 0.15, "down_severe": 0.05, "upside": 0.20})
    m3 = f6_weights("expansion", "A6", ("M3",), m3_prob=0.4)
    assert m3[LOSS_OF_CONTRACT] == pytest.approx(0.06) and m3["down_moderate"] == pytest.approx(0.09)
    assert m3.m3_prob == 0.4
    with pytest.raises(ValueError):
        f6_weights("expansion", "A6", ("M3",))


def test_weights_sum_to_one_per_path():
    paths = [make_path("soft", 0.4, spread=0.03, pmi=53), make_path("rec", 0.3, spread=0.08, default_rate=0.07, pmi=45),
             make_path("hfl", 0.3, spread=0.05, pmi=49)]
    model = DeclineModel(theta0=-3.0, theta=np.array([25.0, 10.0, -0.02]))
    for phase in ("expansion", "late_cycle", "downturn", "repair", "recovery"):
        for arch, mods, q in (("A4", (), None), ("A5", ("M3",), 0.3), ("A6", ("M1",), None)):
            for dm in (None, model):
                wb = case_weights_by_path(paths, phase, arch, mods, dm, m3_prob=q)
                for m in paths:
                    assert sum(wb[m.name].values()) == pytest.approx(1.0)
                    assert min(wb[m.name].values()) >= 0
                    assert wb[m.name].source == ("f6_table" if dm is None else "logistic_5_2+f6_upside")
    wb = case_weights_by_path(paths, "late_cycle", "A4", (), model, promote=False)
    assert wb["rec"].w_down > wb["soft"].w_down  # a recession path raises the downside weight


def test_f66_fires_above_half_only():
    above = {"base": 0.39, "down_moderate": 0.36, "down_severe": 0.15, "upside": 0.10}
    below = {"base": 0.41, "down_moderate": 0.34, "down_severe": 0.15, "upside": 0.10}
    new, fired = apply_f66(above)
    assert fired and new.promoted and new.relabel["base"] == "down_moderate"
    assert sum(new.values()) == pytest.approx(1.0)
    assert dict(new) == pytest.approx({"base": 0.10, "down_moderate": 0.39, "down_severe": 0.51, "upside": 0.0})
    same, fired = apply_f66(below)
    assert not fired and dict(same) == pytest.approx(below)
    again, fired = apply_f66(new)  # fires once
    assert not fired and dict(again) == dict(new)
    # Downturn table: w_down = 0.55 > 0.5, so F6.6 fires for every path.
    wb = case_weights_by_path([make_path("a", 1.0)], "downturn", "A6")
    assert wb["a"].promoted


# ---------------------------------------------------------------------------
# Outputs: mixture moments, revisions, PIT
# ---------------------------------------------------------------------------


def _setup_grid(start=None, seed=0):
    rng = np.random.default_rng(seed)
    start = start or make_start()
    probs = rng.dirichlet(np.ones(4))
    paths = [
        make_path("soft", probs[0], policy=0.035, gdp=0.025, spread=0.03, pmi=53),
        make_path("recession", probs[1], policy=0.02, gdp=-0.02, spread=0.08, default_rate=0.07, pmi=44),
        make_path("hfl", probs[2], policy=0.055, gdp=0.01, spread=0.05, pmi=49),
        make_path("rally", probs[3], policy=0.03, gdp=0.02, spread=0.035, pmi=52),
    ]
    cases = f6_cases(make_base(0.01), "A4", (), A4_TEMPLATE, consensus=dict(g=0.011, **DRIVERS))
    access = {"soft": 0.8, "recession": 0.3, "hfl": 0.6, "rally": 0.9}
    run_fns = dict(
        s_fair_fn=lambda path, q: float(path.index_spread[q - 1]) + 0.01,
        p_refi_access_fn=lambda path, q: access[path.name],
        forward_treasury_fn=lambda path, q, tenor: float(path.y10[q - 1]),
    )
    grid = run_grid(start, cases, paths, betas={"g": 0.4}, trend=0.02, covenant_max_leverage=6.0, **run_fns)
    model = DeclineModel(theta0=-3.0, theta=np.array([25.0, 10.0, -0.02]))
    w = case_weights_by_path(paths, "late_cycle", "A4", (), model, promote=False)
    return start, paths, grid, w


def test_mixture_mean_and_variance_equal_brute_force():
    start, paths, grid, w = _setup_grid()
    df = forward_features_by_path(grid, paths, w, start, pd_fn=lambda f: 0.01 * f["lev_fwd_4"],
                                  s_fair_fn=lambda f: 0.02 + 0.005 * f["lev_fwd_4"], oas=0.06)
    assert list(df["macro_path"]) == ["soft", "recession", "hfl", "rally", "weighted"]
    wrow = df.set_index("macro_path").loc["weighted"]
    for h, mu_col, sd_col in ((4, "lev_fwd_4", "lev_fwd_sd"), (8, "lev_fwd_8", "lev_fwd_sd_8")):
        vals, mass = [], []
        for m in paths:
            for s, ws in w[m.name].items():
                vals.append(grid[(s, m.name)].leverage[h - 1])
                mass.append(m.prob * ws)
        vals, mass = np.array(vals), np.array(mass)
        mean = mass @ vals
        assert wrow[mu_col] == pytest.approx(mean)
        assert wrow[sd_col] ** 2 == pytest.approx(mass @ (vals - mean) ** 2)
    atoms, masses = lev_mixture(grid, paths, w, h=4)
    assert masses.sum() == pytest.approx(1.0) and masses @ atoms == pytest.approx(wrow["lev_fwd_4"])
    pr = df.set_index("macro_path")
    assert pr.loc["recession", "refi_fail_share"] == pytest.approx(1.0)  # access 0.3 fails in every case
    assert pr.loc["soft", "refi_fail_share"] == 0.0
    assert wrow["pd_12m"] == pytest.approx(pr["p_path"].iloc[:4] @ pr["pd_12m"].iloc[:4])
    assert wrow["resid_bp"] == pytest.approx((0.06 - wrow["s_fair"]) * 1e4)
    assert wrow["weight_source"] == "logistic_5_2+f6_upside"


def test_forward_revisions():
    start, paths, grid, w = _setup_grid(seed=1)
    new = forward_features_by_path(grid, paths, w, start)
    start2, paths2, grid2, w2 = _setup_grid(start=make_start(notes_face=150.0), seed=2)
    old = forward_features_by_path(grid2, paths2, w2, start2)
    r = forward_revisions(new, old)
    nw = new.set_index("macro_path").loc["weighted"]
    ow = old.set_index("macro_path").loc["weighted"]
    assert r["rev_lev"] == pytest.approx(nw["lev_fwd_4"] - ow["lev_fwd_4"]) and r["rev_lev"] > 0
    assert r["gap_consensus"] == pytest.approx(nw["base_lev_4"] - nw["consensus_lev_4"])
    assert np.isnan(r["gap_mgmt"])  # no management case: no gap
    assert forward_revisions(new, old, mgmt_lev_4=4.0)["gap_mgmt"] == pytest.approx(nw["base_lev_4"] - 4.0)
    assert set(r["dp_path"]) == {"soft", "recession", "hfl", "rally"}
    assert sum(r["dp_path"].values()) == pytest.approx(0.0, abs=1e-12)


def test_pit_of_realised_leverage_is_uniform():
    """Synthetic issuers: realised Lev_4 = Lev^s_4(m) + noise, with m ~ p(m) and s ~ w_s(m)."""
    rng = np.random.default_rng(20261022)
    noise_sd = 0.15
    pits = []
    for i in range(100):
        start = make_start(float_face=rng.uniform(100, 300), notes_face=rng.uniform(100, 300),
                           maturity_q=int(rng.integers(2, 9)), cash0=rng.uniform(5, 40),
                           revenue_q0=rng.uniform(80, 140))
        _, paths, grid, w = _setup_grid(start=start, seed=1000 + i)
        atoms, masses = lev_mixture(grid, paths, w, h=4)
        p = np.array([m.prob for m in paths])
        for _ in range(6):
            m = paths[rng.choice(len(paths), p=p)]
            cases = list(w[m.name])
            s = cases[rng.choice(len(cases), p=np.array([w[m.name][c] for c in cases]))]
            realised = grid[(s, m.name)].leverage[3] + noise_sd * rng.standard_normal()
            pits.append(mixture_pit(realised, atoms, masses, noise_sd))
    assert len(pits) >= 500
    assert kstest(pits, "uniform").pvalue > 0.01


def test_case_weights_is_a_mapping():
    cw = f6_weights("repair", "A1")
    assert isinstance(cw, CaseWeights) and set(cw) == {"base", "down_moderate", "down_severe", "upside"}
    assert cw.w_down == pytest.approx(0.35)
