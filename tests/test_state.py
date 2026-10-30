"""Tests for hy/state.py (methodology Section 4)."""

from __future__ import annotations

import math
from datetime import datetime

import numpy as np
import pytest

from hy import state as st
from hy.inputs import IssuerFinancials, LookAheadError, NonRecurringItem, Tranche

T0 = datetime(2025, 3, 31)
T1 = datetime(2025, 5, 1)


def _tr(key: str, rank: int, face: float, price: float = 100.0, **kw) -> Tranche:
    return Tranche(key=key, as_of=T0, available_at=T1, issuer_id="X", rank=rank, face=face, price=price, **kw)


ITEMS = (
    NonRecurringItem("restructuring_cash", 10.0, recurs=False, cash=True),
    NonRecurringItem("impairment", 5.0, recurs=False, cash=False),
    NonRecurringItem("recurring_restructuring", 7.0, recurs=True, cash=True),
    NonRecurringItem("asset_sale_gain", -3.0, recurs=False, cash=False),
)


# 4.1 ---------------------------------------------------------------------------


def test_ebitda_adj_adds_back_only_nonrecurring():
    assert st.ebitda_adj_analyst(100.0, ITEMS) == pytest.approx(100 + 10 + 5 - 3)


def test_cash_nonrecurring_counts_only_added_back_cash_items():
    assert st.cash_nonrecurring(ITEMS) == pytest.approx(10.0)


def test_gaps():
    assert st.addback_gap(120.0, 100.0) == pytest.approx(0.2)
    assert st.covenant_gap(130.0, 100.0) == pytest.approx(0.3)
    assert math.isnan(st.addback_gap(1.0, 0.0))


def test_margin_and_peer_gap():
    m = st.margin(17.3, 100.0)
    assert st.margin_peer_gap(m, [0.059, 0.10, 0.12]) == pytest.approx(0.173 - 0.10)


def test_margin_trend_sign_and_strength(rng):
    t = np.arange(8)
    up = 0.10 + 0.005 * t + rng.normal(0, 0.001, 8)
    down = 0.10 - 0.005 * t + rng.normal(0, 0.001, 8)
    assert st.margin_trend(up) > 3
    assert st.margin_trend(down) < -3
    assert math.isnan(st.margin_trend([0.1, 0.2]))
    # Only the last 8 quarters count.
    assert st.margin_trend(np.r_[np.zeros(20) + 5.0, up]) == pytest.approx(st.margin_trend(up))


def test_organic_growth_and_surprise():
    assert st.organic_growth(0.10, 0.02, 0.05, 0.01) == pytest.approx(0.02)
    assert st.surprise(110.0, 100.0) == pytest.approx(0.10)


# 4.2 ---------------------------------------------------------------------------


def test_fcf_charges_cash_addbacks():
    assert st.fcf(130.0, 10.0, 30.0, 20.0, 5.0, 5.0) == pytest.approx(60.0)


def test_liquidity_caps_commitment_by_borrowing_base():
    assert st.liquidity_L(50.0, 200.0, 150.0, 40.0, 10.0) == pytest.approx(150.0)
    assert st.liquidity_L(50.0, 200.0, math.inf, 40.0, 10.0) == pytest.approx(200.0)


def test_runway_and_wall_cover():
    assert st.runway_q(100.0, -25.0) == pytest.approx(4.0)
    assert st.runway_q(100.0, 5.0) == math.inf
    sched = (100.0, 200.0, 0.0, 0.0, 0.0)
    assert st.maturities_to_h(sched, 4) == 100.0
    assert st.maturities_to_h(sched, 8) == 300.0
    assert st.wall_cover_h(50.0, [10.0] * 8, 300.0, 8) == pytest.approx(130.0 / 300.0)
    assert st.wall_cover_h(50.0, [10.0] * 8, 0.0, 4) == math.inf


def test_capex_flex_and_cash_cycle():
    assert st.capex_flex(40.0, 30.0) == pytest.approx(0.25)
    d = st.working_capital_days(100.0, 200.0, 50.0, 365.0, 730.0, period_days=365.0)
    assert d == pytest.approx({"inventory_days": 100.0, "receivable_days": 100.0, "payable_days": 50.0})
    assert st.cash_cycle(**d) == pytest.approx(150.0)
    assert st.payable_days_trend([60, 58, 55, 52, 45]) == pytest.approx(-15.0)


# 4.3 ---------------------------------------------------------------------------

STRUCT = [_tr("tl", 1, 300.0), _tr("ssn", 2, 200.0, price=80.0), _tr("ssn2", 2, 100.0), _tr("sub", 3, 100.0, price=50.0)]


def test_face_and_market_leverage():
    assert st.lev_face_k(STRUCT, "tl", 100.0) == pytest.approx(3.0)
    assert st.lev_face_k(STRUCT, "ssn", 100.0) == pytest.approx(6.0)  # pari passu included
    assert st.lev_mkt_k(STRUCT, "ssn", 100.0) == pytest.approx((300 + 0.8 * 200) / 100)
    assert st.lev_mkt_k(STRUCT, "sub", 100.0) == pytest.approx((600 + 50) / 100)


def test_ltv_rises_when_peer_multiple_falls():
    # Skill example: 6x leverage on a 10x business is 60% LTV; at 8x it is 75%.
    s = [_tr("a", 1, 600.0)]
    assert st.ltv_k(s, "a", 10 * 100.0) == pytest.approx(0.60)
    assert st.ltv_k(s, "a", 8 * 100.0) == pytest.approx(0.75)


def test_lease_adjusted_leverage_hand_check():
    # (500 + 8 x 50) / (100 + 50) = 900 / 150 = 6.0x, against 5.0x unadjusted.
    assert st.lev_lease_adj(500.0, 50.0, 100.0) == pytest.approx(6.0)
    assert st.lev_gross(500.0, 100.0) == pytest.approx(5.0)


def test_other_ratios():
    assert st.coverage(100.0, 20.0, 40.0) == pytest.approx(2.0)
    assert st.debt_adj(500.0, 30.0, 20.0) == pytest.approx(550.0)
    assert st.debt_adj(500.0, -30.0, 0.0) == pytest.approx(500.0)  # overfunded pension is no asset
    assert st.net_lev(500.0, 100.0, 100.0) == pytest.approx(4.0)
    assert st.fccr(100.0, 30.0, 20.0) == pytest.approx(2.0)


# 4.4 ---------------------------------------------------------------------------


def test_q_vector_keeps_order_and_bounds():
    v = st.q_vector({"cyclicality": 2, "sponsor_behavior": 1})
    assert v.shape == (10,)
    assert v[st.Q_FLAGS.index("cyclicality")] == 2
    assert st.q_score(v) == 3
    with pytest.raises(ValueError):
        st.q_vector({"commodity": 3})
    with pytest.raises(KeyError):
        st.q_vector({"weather": 1})


# 4.5 ---------------------------------------------------------------------------


def test_ordinal_model_recovers_ratings(rng):
    n, k = 3000, 5
    X = rng.normal(size=(n, 3))
    beta = np.array([1.5, -1.0, 0.5])
    theta = np.array([-2.0, -0.7, 0.7, 2.0])
    latent = X @ beta + rng.logistic(size=n)
    y = np.searchsorted(theta, latent)  # class j when theta_{j-1} < latent <= theta_j
    model = st.OrdinalLogit().fit(X, y)
    # Coefficients come back on the standardised scale; rescale to compare.
    assert model.beta / model._scale == pytest.approx(beta, abs=0.15)
    # Fitted ratings agree with the argmax under the true parameters (the oracle).
    from scipy.special import expit
    cum = np.hstack([np.zeros((n, 1)), expit(theta[None, :] - (X @ beta)[:, None]), np.ones((n, 1))])
    oracle = np.argmax(np.diff(cum, axis=1), axis=1)
    pred = model.predict(X)
    assert np.mean(pred == oracle) > 0.95
    assert np.mean(np.abs(pred - y) <= 1) >= np.mean(np.abs(oracle - y) <= 1) - 0.02
    assert model.predict_proba(X).sum(axis=1) == pytest.approx(np.ones(n))


def test_rating_gap_sign():
    assert st.rating_gap(3, 5) == -2
    assert list(st.rating_gap(np.array([3, 5]), np.array([3, 4]))) == [0, 1]


# 4.6 ---------------------------------------------------------------------------


def test_covenant_origination_book_example():
    # p. 356: a 15% cushion on a 4.0x plan gives a 4.7x covenant.
    assert st.lev_max_origination(400.0, 100.0, 0.15) == pytest.approx(4.0 / 0.85)
    assert round(st.lev_max_origination(400.0, 100.0, 0.15), 1) == 4.7
    with pytest.raises(ValueError):
        st.lev_max_origination(400.0, 100.0, 0.05)


def test_headroom_is_ebitda_decline_to_breach():
    lev_max = 4.0 / 0.85
    h = st.covenant_headroom(4.0, lev_max)
    assert h == pytest.approx(0.15)
    assert 4.0 / (1 - h) == pytest.approx(lev_max)


# 10.2 --------------------------------------------------------------------------


def _fin(**kw) -> IssuerFinancials:
    base = dict(
        key="X", as_of=T0, available_at=T1, revenue=500.0, ebitda_reported=100.0,
        nonrecurring_items=ITEMS, ebitda_adj_company=125.0, ebitda_covenant=130.0,
        cash_interest=20.0, cash_taxes=5.0, capex_total=30.0, capex_maintenance=20.0,
        inventory=80.0, receivables=100.0, payables=60.0, cogs=300.0, cash=50.0,
        revolver_commitment=200.0, revolver_drawn=40.0, borrowing_base=150.0, letters_of_credit=10.0,
        maturity_schedule=(100.0, 200.0, 0.0, 0.0, 0.0), rent_expense=5.0,
        pension_underfunded=20.0, guarantees_weak=10.0,
    )
    base.update(kw)
    return IssuerFinancials(**base)


def test_issuer_state_fields():
    out = st.issuer_state(_fin(), STRUCT, flags={"cyclicality": 2}, fcf_forecast=[10.0] * 8,
                          margin_history=[0.2] * 7, covenant_max=2.0)
    assert out["ebitda_adj_analyst"] == pytest.approx(112.0)
    assert out["fcf"] == pytest.approx(112 - 10 - 30 - 20 - 5)
    assert out["liquidity_L"] == pytest.approx(150.0)
    assert out["total_debt"] == pytest.approx(700.0)
    assert out["lev_gross"] == pytest.approx(700 / 448)
    assert out["lev_adj_total"] == pytest.approx(730 / 448)
    assert out["lev_lease_adj"] == pytest.approx((700 + 8 * 20) / (448 + 20))
    assert out["wall_cover_4"] == pytest.approx((150 + 40) / 100)
    assert out["q_score"] == 2 and out["q_vector"].shape == (10,)
    assert out["H_t"] == pytest.approx(1 - (700 / 520) / 2.0)
    assert math.isnan(out["surprise"])


def test_issuer_state_blocks_look_ahead():
    with pytest.raises(LookAheadError):
        st.issuer_state(_fin(), STRUCT, decision_time=datetime(2025, 4, 15))


# --------------------------------------------------------------------------- one HY index rule (data module step 5)


def test_hy_index_level_is_the_median_of_the_core_bonds():
    from hy import state as st
    spread = np.array([0.02, 0.03, 0.04, 0.50, 0.05])
    price = np.array([100.0, 99.0, 95.0, 40.0, 79.0])   # the 40 and the 79 fail the price floor
    yld = np.array([0.06, 0.07, 0.08, 0.60, 0.09])
    assert st.hy_index_level(spread, price, yld) == pytest.approx(0.03)
    assert np.isnan(st.hy_index_level(np.array([0.5]), np.array([40.0]), np.array([0.6])))


def test_every_hy_index_user_shares_the_rule_constants():
    import inspect
    from hy import state as st
    from hy.sources import trace_bonds as tb
    r = st.HY_INDEX_RULE
    sig = inspect.signature(tb.hy_benchmark).parameters
    assert sig["min_years"].default == r["min_years"] and sig["max_years"].default == r["max_years"]
    sig = inspect.signature(tb.benchmark_by_bucket).parameters
    assert sig["min_price"].default == r["min_price"] and sig["max_yield"].default == r["max_yield"]


def test_distress_ratio_counts_every_positive_yield_bond():
    from hy import state as st
    spread = np.array([0.03, 0.12, 0.30, 0.05])
    yld = np.array([0.07, 0.16, 0.34, -0.01])   # the last has no positive yield: out of the count
    assert st.distress_ratio(spread, yld) == pytest.approx(2 / 3)  # 1,200 bp and 3,000 bp are both distressed


# --------------------------------------------------------------------------- one LTM rule (data module step 5b)


def test_last_four_needs_consecutive_quarters():
    from types import SimpleNamespace as Q
    from hy import state as st
    qs = [Q(as_of=datetime(2025, m, 28)) for m in (3, 6, 9, 12)]
    assert len(st.last_four(qs)) == 4
    shifted = [Q(as_of=datetime(2024, 12, 31))] + qs[:3]   # Dec-2024 to Sep-2025: 271 days, within 290
    assert len(st.last_four(shifted)) == 4
    broken = [Q(as_of=datetime(2024, 9, 30))] + qs[1:]  # first to last 365 days: not consecutive
    assert st.last_four(broken) == []


def test_ltm_total_sums_four_and_scales_three():
    from hy import state as st
    assert st.ltm_total([1.0, 2.0, 3.0, 4.0]) == pytest.approx(10.0)
    assert st.ltm_total([1.0, 2.0, float("nan"), 3.0]) == pytest.approx(6.0 * 4 / 3)   # earnings: 3 of 4 x 4/3
    assert np.isnan(st.ltm_total([1.0, 2.0, float("nan"), 3.0], allow_three=False))  # cash flows: strict
    assert np.isnan(st.ltm_total([1.0, float("nan"), float("nan"), 3.0]))
    assert np.isnan(st.ltm_total([None, 1.0, 2.0, 3.0], allow_three=False))


def test_one_ltm_home():
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    import process
    from hy import state as st
    from hy.sources import clock_inputs as ci
    assert process.ltm_figures is st.ltm_figures and ci.last_four is st.last_four


def test_one_bridge_fcf():
    # Kricheff's FCF is the Section 4.2 bridge with no cash non-recurring charge: one formula, one home.
    from hy import books
    from hy import state as st
    k = books.kricheff_bridge(1000.0, 300.0, 200.0, 50.0, 20.0, cfo=740.0)
    assert k["fcf"] == pytest.approx(st.fcf(1000.0, 0.0, 300.0, 200.0, 50.0, 20.0)) == pytest.approx(430.0)


# --------------------------------------------------------------------------- leverage: one per use (step 5b)


def test_issuer_leverage_is_lease_adjusted():
    from hy import state as st
    # MGM, 18 Sep 2026: filed debt 6,068, lease liabilities 24,090; (6,068 + 24,090) / (EBITDA + rent).
    assert st.issuer_leverage(6068.0, 24090.0, 2407.0, 2321.0) == pytest.approx(30158.0 / 4728.0)
    assert st.issuer_leverage(100.0, 0.0, 50.0, 0.0) == pytest.approx(2.0)          # no leases: debt / EBITDA
    assert np.isnan(st.issuer_leverage(100.0, 0.0, 0.0, 0.0))                         # no EBITDA: undefined
    assert st.issuer_net_leverage(100.0, 20.0, 30.0, 50.0, 10.0) == pytest.approx(90.0 / 60.0)


def test_negative_ebitda_reads_as_the_cap_not_as_low_leverage():
    # The sign trap: debt / negative EBITDA is a negative ratio, which ranks below every healthy issuer.
    from hy import books
    from hy import state as st
    t = [_tr("a", 1, 1000.0)]
    for lev in (st.lev_gross(1000.0, -50.0), st.net_lev(1000.0, 100.0, -50.0), st.lev_lease_adj(1000.0, 10.0, -50.0),
                st.lev_face_k(t, "a", -50.0), st.lev_mkt_k(t, "a", -50.0), st.issuer_leverage(1000.0, 0.0, -50.0, 0.0),
                st.issuer_net_leverage(1000.0, 0.0, 100.0, -50.0, 0.0)):
        assert lev == st.LEV_CAP
    # No net debt and no earnings: nothing to lever, and the two negatives must not multiply into a positive ratio.
    assert st.net_lev(100.0, 300.0, -50.0) == 0.0
    assert st.issuer_net_leverage(100.0, 0.0, 300.0, -50.0, 0.0) == 0.0
    # Monotone: a thin positive EBITDA can never read worse than a negative one.
    assert st.lev_gross(1000.0, 1.0) == st.LEV_CAP
    assert st.lev_gross(1000.0, 50.0) == st.LEV_CAP
    # Rent can lift a negative EBITDA above zero: EBITDAR is the denominator, so the ratio stays a real number.
    assert st.issuer_leverage(100.0, 0.0, -10.0, 60.0) == pytest.approx(2.0)
    # Net cash on positive EBITDA stays negative, and zero EBITDA stays undefined.
    assert st.net_lev(100.0, 300.0, 50.0) == pytest.approx(-4.0)
    assert np.isnan(st.lev_gross(100.0, 0.0))
    # The guard treats the negative EBITDA issuer as it treats the +20x issuer.
    same = dict(fcf_to_debt=0.03, tev_to_debt=1.2, lev_peers=[], fcf_peers=[])
    assert books.spt_trap_guard(st.issuer_leverage(1000.0, 0.0, -50.0, 0.0), **same)["trap"]
    assert books.spt_trap_guard(st.issuer_leverage(1000.0, 0.0, 50.0, 0.0), **same)["trap"]


def test_lev_cap_is_the_panel_cap():
    from hy import state as st
    from hy.sector import drivers
    from hy.sources import trace_panel
    assert st.LEV_CAP == trace_panel.LEV_CAP == drivers.LEV_CAP


def test_issuer_analysis_uses_issuer_leverage(monkeypatch):
    import sys
    from pathlib import Path
    from types import SimpleNamespace
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    import process
    from hy import state as st
    monkeypatch.setattr(st, "issuer_leverage", lambda *a: 7.77)
    monkeypatch.setattr(st, "issuer_net_leverage", lambda *a: 6.66)
    blk = {"risk": SimpleNamespace(extra={"debt": 100.0, "lease_debt": 10.0, "rent": 1.0, "cash": 5.0})}
    ltm = {"ebitda_adj": 50.0, "capex": 5.0, "maint_capex": 4.0, "cash_interest": 6.0, "cash": 5.0, "fcf": 9.0,
           "cfo": 14.0, "delta_wc": 0.0, "revenue": 200.0, "revenue_q": []}
    k = process.book_block(blk, ltm, 300.0, "A4", None)["kricheff"]
    assert k["lev_gross"] == 7.77 and k["lev_net"] == 6.66


def test_margin_trend_gaps():
    # A missing quarter drops out and keeps its time position; the fit equals OLS on the kept points.
    m = np.array([0.10, 0.11, np.nan, 0.12, 0.14, 0.13, np.nan, 0.16])
    x = np.flatnonzero(~np.isnan(m)).astype(float)
    b, a = np.polyfit(x, m[x.astype(int)], 1)
    res = m[x.astype(int)] - (a + b * x)
    se = np.sqrt((res ** 2).sum() / (x.size - 2) / ((x - x.mean()) ** 2).sum())
    assert st.margin_trend(m, min_points=6) == pytest.approx(b / se)
    assert math.isnan(st.margin_trend(m, min_points=7))
