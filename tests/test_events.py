"""Tests for hy.events (methodology Section 9)."""

from datetime import datetime

import numpy as np
import pytest

from hy import events as ev


def _path(name, prob, dy10=0.0):
    q = np.zeros(ev.N_QUARTERS)
    return ev.MacroPath(name, prob, q + 0.04, q + 0.042 + dy10, q + 0.05, q + 0.02, q + 50, q + 0.04, q + 0.03)


def test_taxonomy_complete():
    assert len(ev.EventType) == 14
    assert set(ev.OUTCOMES) == set(ev.EventType)


def test_macro_paths_validate():
    ev.validate_paths([_path("soft", 0.6), _path("recession", 0.4)])
    with pytest.raises(ValueError):
        ev.validate_paths([_path("soft", 0.6), _path("recession", 0.3)])
    with pytest.raises(ValueError):
        ev.MacroPath("x", 1.2, *([np.zeros(8)] * 7))


def test_growth_yield_rise_tightens_policy_widens(rng):
    # Fit the split and the betas on synthetic history with known signs.
    n = 400
    dG, dP = rng.normal(size=n) * 0.005, rng.normal(size=n) * 0.005
    dy = 0.6 * dG + 0.9 * dP + rng.normal(scale=1e-4, size=n)
    split = ev.fit_yield_split(dy, dG, dP)
    assert split.b_growth == pytest.approx(0.6, abs=0.02) and split.b_policy == pytest.approx(0.9, abs=0.02)
    g, p = ev.split_yield_change(split, dy, dG)
    np.testing.assert_allclose(g + p, dy)
    ds = -0.8 * g + 0.5 * p + rng.normal(scale=1e-5, size=n)
    bg, bp = ev.fit_spread_betas(ds, g, p)
    assert bg < 0 < bp
    assert ev.systematic_spread_change(0.01, 0.0, bg, bp) < 0  # growth-driven rise tightens
    assert ev.systematic_spread_change(0.0, 0.01, bg, bp) > 0  # policy-driven rise widens
    with pytest.raises(ValueError):
        ev.systematic_spread_change(0.01, 0.0, 0.3, 0.5)
    # Effective rate duration: shorter in a growth move, longer in a policy move.
    assert ev.effective_rate_duration(4.0, 4.0, bg) < 4.0 < ev.effective_rate_duration(4.0, 4.0, bp)


def test_rate_price_change_duration_rule():
    # About 1% of price per year of duration per 1% of yield (p. 116).
    assert ev.rate_price_change(100.0, 4.0, 0.0, 0.01) == pytest.approx(-4.0)
    assert ev.rate_price_change(100.0, 4.0, 30.0, 0.01) == pytest.approx(-4.0 + 0.15)


def test_cash_interest_change():
    # 40% floating of 1,000 debt, SOFR +1%: +4. 100 matures in q1 at 6% and refinances at 4.5% + 4% = 8.5%: +2.5.
    out = ev.cash_interest_change(1000.0, 0.4, 0.01, [100.0, 0, 0, 0], [0.045] * 4, 0.04, [0.06] * 4, h=2)
    assert out == pytest.approx(4.0 + 2.5)


def test_position_pnl_and_default_term():
    assert ev.position_pnl(100.0, 4.0, 4.0, 0.01, -0.005, 0.0, 0.5) == pytest.approx(-4.0 + 2.0 + 0.5)
    assert ev.position_pnl(90.0, 4.0, 4.0, 0.01, 0.0, 0.0, 0.5, default=True, recovery_adj=0.4) == pytest.approx(0.5 - 50.0)


def test_outcome_probability_rules():
    p = ev.outcome_probabilities(ev.EventType.EARNINGS, w_down=0.3)
    assert p["miss"] == 0.3 and sum(p.values()) == pytest.approx(1.0)
    p = ev.outcome_probabilities(ev.EventType.COVENANT_TEST, p_breach=0.2)
    assert p["pass"] == pytest.approx(0.8) and sum(p.values()) == pytest.approx(1.0)
    p = ev.outcome_probabilities(ev.EventType.MATURITY_REFI, p_refi=0.5, refi_access=0.6)
    assert 1 - p["refinanced"] == pytest.approx(0.5 * 0.4) and sum(p.values()) == pytest.approx(1.0)
    acc = ev.refi_access([1.0, 4.0], [1.0, 1.0])
    assert acc[0] > acc[1]
    assert ev.refi_access(1.0, 0.0) == 0.0


def test_event_var_equals_empirical_quantile(rng):
    pnl = rng.normal(size=(5, 4))
    p_path = np.full(5, 0.2)
    p_out = np.full((5, 4), 0.25)
    for a in (0.05, 0.1, 0.25):
        assert ev.event_var(pnl, p_path, p_out, a) == pytest.approx(np.quantile(pnl.ravel(), a, method="inverted_cdf"))
    assert ev.expected_event_pnl(pnl, p_path, p_out) == pytest.approx(pnl.mean())


def test_event_var_respects_weights():
    pnl = np.array([[-10.0, 1.0]])
    assert ev.event_var(pnl, [1.0], [[0.04, 0.96]], 0.05) == 1.0
    assert ev.event_var(pnl, [1.0], [[0.06, 0.94]], 0.05) == -10.0


def test_jtd_neutral_pair_gives_equal_jump_losses():
    pk, rk, pj, rj = 95.0, 0.60, 80.0, 0.25  # long secured k, short unsecured j
    ratio = ev.jtd_neutral_ratio(pk, rk, pj, rj)
    nk = 1e6
    assert ev.jtd(nk, pk, rk) == pytest.approx(ev.jtd(nk * ratio, pj, rj))


def test_dv01_neutral_pair_is_not_jtd_neutral():
    # Short-dated against long-dated, stressed issuer (p. 530): both legs converge to one recovery.
    pk, dk, pj, dj, r = 92.0, 1.5, 70.0, 5.0, 0.35
    nk = 1e6
    nj = nk * ev.dv01_neutral_ratio(dk, pk, dj, pj)
    assert ev.sdv01(dk, pk, nk) == pytest.approx(ev.sdv01(dj, pj, nj))
    net_jump = -ev.jtd(nk, pk, r) + ev.jtd(nj, pj, r)
    assert abs(net_jump) > 0.1 * ev.jtd(nk, pk, r)
    assert net_jump < 0  # the long loses more than the short gains


def test_risk_measures_units():
    assert ev.sdv01(4.0, 100.0, 1e6) == pytest.approx(400.0)
    assert ev.rdv01_eff(4.0, 4.0, -0.5, 100.0, 1e6) == pytest.approx(200.0)
    assert ev.el_h(0.04, 0.6, 1e6) == pytest.approx(24_000.0)
    assert ev.exit_cost(50.0, 400.0) == pytest.approx(20_000.0)
    assert ev.exit_days(10e6, 5e6, 0.2) == pytest.approx(10.0)
    assert ev.hedge_ratio(400.0, 1.2) == pytest.approx(480.0)


def test_limits():
    s = ev.band_gate_scale([1.0, 2.0], [1.0, 1.0])
    assert s[0] > s[1]
    cap = ev.pre_event_cap(1e6, worst_dpnl=-10.0, exp_conv_ret_h=0.05, budget_frac=0.5)
    assert cap * 10.0 / 100 == pytest.approx(0.5 * 0.05 * 1e6)
    lim = ev.regime_jtd_limit(1e6, np.array([0.1, 0.3, 0.6]))
    assert np.all(np.diff(lim) < 0)
    paths = [_path("soft", 0.7), _path("recession", 0.3)]
    w = ev.wall_limit([5.0, 5.0, 5.0], [0.5, 2.0, 0.9], paths, {"soft": True, "recession": False}, cap_base=10.0)
    assert w.exposure == 10.0 and w.limit == pytest.approx(7.0) and w.breach
    c = ev.correlated_event_limit([3.0, 4.0, 2.0], ["oil", "oil", "gas"], 5.0)
    assert bool(c.loc["oil", "breach"]) and not bool(c.loc["gas", "breach"])


def test_event_grid_and_matrix():
    beta = np.array([0.1, -0.2])  # log fair spread rises in leverage, falls in coverage

    def fair_log_spread(x):
        return np.log(0.05) + x @ beta

    paths = [_path("soft", 0.6), _path("recession", 0.4)]
    outcomes = ev.OUTCOMES[ev.EventType.EARNINGS]
    shocks = {"beat": np.array([-0.2, 0.1]), "in_line": np.zeros(2), "miss": np.array([0.5, -0.3])}
    grid = ev.event_pnl_grid(
        price=95.0, mod_duration=4.0, spread_duration=4.0, x_base=np.zeros(2),
        x_outcome=lambda o, m: shocks[o] * (1.5 if m.name == "recession" else 1.0),
        outcomes=outcomes, paths=paths, dy={"soft": 0.0, "recession": -0.01},
        ds_sys={"soft": 0.0, "recession": 0.01}, carry_h=1.0, recovery_adj={"soft": 0.5, "recession": 0.4},
        fair_log_spread=fair_log_spread,
    )
    assert grid.dpnl.shape == (2, 3)
    assert grid.dspread_bp[0, 1] == pytest.approx(0.0)
    assert grid.dpnl[0, 2] < grid.dpnl[0, 1] < grid.dpnl[0, 0]  # miss < in line < beat
    p_out = np.array([[0.4, 0.4, 0.2], [0.25, 0.25, 0.5]])
    blk = ev.event_matrix_block(
        date=datetime(2026, 10, 21), available_at=datetime(2026, 10, 21), position_id="P1", cusip="X",
        event_id="E1", event_type=ev.EventType.EARNINGS, event_date=datetime(2026, 11, 5), date_confirmed=True,
        grid=grid, p_path={"soft": 0.6, "recession": 0.4}, p_outcome_given_path=p_out,
    )
    em = ev.build_event_matrix([blk])
    assert len(em) == 6
    assert set(em.columns) >= {"outcome", "macro_path", "dpnl", "dspread_bp", "features_delta"}
    with pytest.raises(ValueError):
        ev.build_event_matrix([blk.assign(p_outcome_given_path=0.1)])


def test_catalysts_in_horizon_keep_dated_and_near_events_only():
    evs = [{"event": "Next quarterly results", "date": "2026-11-20", "confirmed": False},
           {"event": "Results after the horizon", "date": "2027-09-01", "confirmed": False},
           {"event": "Debt due by 0.4 years out", "years": 0.4, "amount_m": 500, "confirmed": True},
           {"event": "Debt due by 2.0 years out", "years": 2.0, "amount_m": 900, "confirmed": True},
           {"event": "Undated note", "confirmed": False}]
    got = ev.catalysts_in_horizon(evs, datetime(2026, 9, 18), 0.5)
    assert [c["event"] for c in got] == ["Next quarterly results", "Debt due by 0.4 years out"]
    assert ev.catalysts_in_horizon([], datetime(2026, 9, 18), 0.5) == []
