"""Recovery layer: value range, waterfall, and liability management adjustment (Section 6).

Value is lognormal. Recovery of tranche k is the expected payoff of a call
spread on enterprise value between strikes S_k and S_k + F_k, divided by F_k.
The lognormal makes that expectation closed form (Black-style); a Monte Carlo
function checks it.

Conventions: amounts in USD millions; rates decimal; prices per 100 face.
"""

from __future__ import annotations

import math
from typing import Mapping, Sequence

import numpy as np
from scipy import special

from hy.inputs import Tranche

Z_FOOTBALL = 1.28  # Section 6.1: the football field spans the 10th to 90th percentile

# Section 6.1, p. 332: VCC liquidation rates (low, high) per asset class.
VCC_LIQUIDATION_RATES: dict[str, tuple[float, float]] = {
    "cash": (1.00, 1.00),
    "receivables": (0.85, 0.95),
    "inventory": (0.60, 0.75),
    "real_estate": (0.70, 0.80),
    "machinery": (0.10, 0.20),
    "other": (0.00, 0.15),
}
LIQUIDATION_EXPENSE = 0.05  # Section 6.1, p. 332

# Placeholder LME coefficients (gamma_0, gamma_1, gamma_2). Not calibrated; Section 6.3
# requires a fit on the liability management cases since 2015 (p. 498).
GAMMA_LME_DEFAULT = (-3.0, 1.0, 3.0)


# ------------------------------------------------------ 6.1 Enterprise value range


def comparables_value(ebitda_adj: float, sector_multiple: float) -> float:
    """Comparable companies value (Section 6.1; p. 414): sector multiple x EBITDA^adj.

    Intuition: the company is worth what the market pays for peers per unit of EBITDA.
    """
    return sector_multiple * ebitda_adj


def precedent_value(ebitda_adj: float, deal_multiple: float) -> float:
    """Precedent transactions value (Section 6.1): deal multiple x EBITDA^adj.

    Intuition: what a buyer paid for control of a similar business; use for the sale case.
    """
    return deal_multiple * ebitda_adj


def dcf_value(fcf_path: Sequence[float], discount_rate: float, terminal_growth: float,
              periods_per_year: int = 4) -> float:
    """Discounted cash flow value (Section 6.1).

    V = sum_h FCF_h / (1+r)^(h/n) + TV / (1+r)^(H/n), TV = n FCF_H (1+g) / (r - g),
    with n periods per year and r, g annual.

    Intuition: the value of the base case cash path from Section 5 plus a growing perpetuity.
    """
    if discount_rate <= terminal_growth:
        raise ValueError("discount rate must exceed terminal growth")
    f = np.asarray(fcf_path, dtype=float)
    if f.size == 0:
        raise ValueError("empty FCF path")
    t = np.arange(1, f.size + 1) / periods_per_year
    disc = (1.0 + discount_rate) ** -t
    tv = periods_per_year * f[-1] * (1.0 + terminal_growth) / (discount_rate - terminal_growth)
    return float(f @ disc + tv * disc[-1])


def liquidation_value(assets: Mapping[str, float], rates: Mapping[str, float] | None = None,
                      expense: float = LIQUIDATION_EXPENSE, wind_down: float = 0.0) -> float:
    """Liquidation value (Section 6.1; Figure 11.18, p. 332).

    V_liq = (1 - expense) sum_a rate_a x book_a - wind_down. The default rate per asset is the
    midpoint of the VCC range; the default expense is 5% of gross proceeds.

    Intuition: the floor value that secured lenders can count on when the business stops.
    """
    gross = 0.0
    for name, book in assets.items():
        if rates is not None and name in rates:
            r = rates[name]
        elif name in VCC_LIQUIDATION_RATES:
            lo, hi = VCC_LIQUIDATION_RATES[name]
            r = 0.5 * (lo + hi)
        else:
            raise KeyError(f"no liquidation rate for {name}")
        gross += r * book
    return gross * (1.0 - expense) - wind_down


def football_field(ranges: Mapping[str, tuple[float, float]]) -> tuple[float, float, float]:
    """Read low, mid, and high value from the football field (Section 6.1; Figure 11.19, p. 332).

    V_low = mean of method lows; V_high = mean of method highs; V_mid = sqrt(V_low V_high).

    Intuition: each method gives a bar; the field is where the bars agree on average.
    The geometric mid keeps V_mid at the median of the lognormal.
    """
    lows = np.array([r[0] for r in ranges.values()], dtype=float)
    highs = np.array([r[1] for r in ranges.values()], dtype=float)
    lo, hi = float(lows.mean()), float(highs.mean())
    return lo, math.sqrt(lo * hi), hi


def lognormal_params(v_low: float, v_mid: float, v_high: float, z: float = Z_FOOTBALL) -> tuple[float, float]:
    """Lognormal value from the football field (Section 6.1).

    mu_V = log V_mid, sigma_V = (log V_high - log V_low) / (2 x 1.28).

    Intuition: the field's low and high are the 10th and 90th percentiles of value.
    """
    if not 0 < v_low <= v_mid <= v_high:
        raise ValueError("need 0 < v_low <= v_mid <= v_high")
    return math.log(v_mid), (math.log(v_high) - math.log(v_low)) / (2.0 * z)


def default_value(distressed_multiple: float, ebitda_severe: float, dip: float = 0.0,
                  costs: float = 0.0) -> float:
    """Value conditional on default (Section 6.1; p. 503).

    V_default = distressed multiple x severe downside EBITDA - DIP - bankruptcy costs.

    Intuition: in default the value is a low multiple of a low EBITDA, and the DIP and the
    lawyers are paid first. Floored at zero.
    """
    return max(distressed_multiple * ebitda_severe - dip - costs, 0.0)


# -------------------------------------------------------- 6.2 Waterfall and recovery


def payoff(v: np.ndarray | float, senior: float, face: float) -> np.ndarray | float:
    """Tranche payoff (Section 6.2): Pay_k(V) = min(F_k, max(0, V - S_k)).

    Intuition: the tranche owns the slice of value between S_k and S_k + F_k.
    """
    return np.minimum(face, np.maximum(0.0, np.asarray(v, dtype=float) - senior))


def _call_lognormal(strike: float, mu: float, sigma: float) -> float:
    """E[(V - K)^+] for log V ~ N(mu, sigma^2): e^{mu + s^2/2} N(d1) - K N(d2)."""
    mean = math.exp(mu + 0.5 * sigma * sigma)
    if strike <= 0:
        return mean - strike
    if sigma <= 0:
        return max(math.exp(mu) - strike, 0.0)
    d1 = (mu - math.log(strike) + sigma * sigma) / sigma
    d2 = d1 - sigma
    return mean * special.ndtr(d1) - strike * special.ndtr(d2)


def recovery_closed_form(senior: float, face: float, mu: float, sigma: float) -> float:
    """Recovery in closed form for lognormal value (Section 6.2).

    R_k = E[Pay_k(V)] / F_k = (C(S_k) - C(S_k + F_k)) / F_k,
    C(K) = e^{mu + s^2/2} N(d1) - K N(d2), d1 = (mu - log K + s^2) / s, d2 = d1 - s.

    Intuition: the tranche is long a call struck at S_k and short a call struck at S_k + F_k.
    """
    if face <= 0:
        raise ValueError("face must be positive")
    return (_call_lognormal(senior, mu, sigma) - _call_lognormal(senior + face, mu, sigma)) / face


def recovery_monte_carlo(senior: float, face: float, mu: float, sigma: float,
                         rng: np.random.Generator, n: int = 200_000) -> float:
    """Monte Carlo check of the closed form (Section 6.2): mean of Pay_k(V_i) / F_k, log V_i ~ N(mu, s^2).

    Intuition: simulate the value, pay the slice, average.
    """
    v = np.exp(mu + sigma * rng.standard_normal(n))
    return float(np.mean(payoff(v, senior, face))) / face


def waterfall(tranches: Sequence[Tranche], mu: float, sigma: float, admin_claims: float = 0.0) -> dict[str, float]:
    """Recovery per tranche with pari passu pooling (Section 6.2; Chapter 15).

    For each rank group g: S_g = admin + sum_{rank_j < rank_g} F_j, F_g = sum_{rank_j = rank_g} F_j,
    and every tranche in g gets R_g = E[Pay(V; S_g, F_g)] / F_g.

    Intuition: equal-rank claims share their slice pro rata, so they recover the same fraction.
    """
    ranks = sorted({t.rank for t in tranches})
    out: dict[str, float] = {}
    senior = admin_claims
    for r in ranks:
        group = [t for t in tranches if t.rank == r]
        pool = float(sum(t.face for t in group))
        rec = recovery_closed_form(senior, pool, mu, sigma) if pool > 0 else float("nan")
        for t in group:
            out[t.key] = rec
        senior += pool
    return out


def senior_claims(tranches: Sequence[Tranche], key: str, admin_claims: float = 0.0) -> tuple[float, float]:
    """S_k and the pari passu pool face for tranche k (Section 6.2).

    S_k = admin + sum_{rank_j < rank_k} F_j; F_pool = sum_{rank_j = rank_k} F_j.

    Intuition: the claims ahead of tranche k and the pool it shares.
    """
    tk = next(t for t in tranches if t.key == key)
    s = admin_claims + sum(t.face for t in tranches if t.rank < tk.rank)
    pool = sum(t.face for t in tranches if t.rank == tk.rank)
    return float(s), float(pool)


# ------------------------------------------------------------ 6.2 Market checks


def check_creation_vs_distressed(creation_multiple: float, v_default: float, ebitda_adj: float) -> dict[str, float | bool]:
    """Check 1 (Section 6.2): creation multiple lev_mkt_k against V_default / EBITDA^adj.

    Intuition: a creation multiple below the distressed multiple means the market price
    sits below model recovery.
    """
    distressed = v_default / ebitda_adj if ebitda_adj else float("nan")
    return {
        "creation_multiple": creation_multiple,
        "distressed_multiple": distressed,
        "price_below_recovery": bool(creation_multiple < distressed),
    }


def market_implied_recovery(prices: Sequence[float], maturities: Sequence[float]) -> float:
    """Check 2 (Section 6.2; p. 530): price / 100 of the longest bond of the same rank.

    Intuition: in distress, equal-rank bonds converge to one recovery price, and the longest
    bond carries the least time value. Use only when the issuer is distressed.
    """
    if len(prices) == 0 or len(prices) != len(maturities):
        raise ValueError("need matched prices and maturities")
    return float(prices[int(np.argmax(maturities))]) / 100.0


def ltv_scenarios(debt_through_k: float, v_low: float, v_mid: float, v_high: float) -> dict[str, float]:
    """Check 3 (Section 6.2; p. 332): ltv_k at V_low, V_mid, V_high.

    LTV_k(V) = sum_{rank_j <= rank_k} F_j / V.

    Intuition: an LTV below 1 at V_low means the tranche stays covered in the bad case
    (VCC: 67% at mid, 87% at low).
    """
    return {
        "ltv_k_low": debt_through_k / v_low,
        "ltv_k_mid": debt_through_k / v_mid,
        "ltv_k_high": debt_through_k / v_high,
    }


# ---------------------------------------------------- 6.3 Liability management


def lme_score(
    *,
    v_mid: float,
    face_k: float,
    unrestricted_sub_capacity: float = 0.0,
    investment_capacity: float = 0.0,
    bare_majority: bool = False,
    pro_rata_carveouts: bool = False,
    lien_basket: float = 0.0,
    debt_basket: float = 0.0,
    sponsor_behavior: int = 0,
    weights: Sequence[float] = (1.0, 1.0, 1.0, 1.0, 0.5),
) -> float:
    """LME exposure score (Section 6.3).

    score_k = w1 (unrestricted_sub + investment) / V_mid + w2 1[bare majority]
              + w3 1[pro rata carve-outs] + w4 (lien + debt baskets) / F_k + w5 sponsor_behavior.

    Intuition: more room to move collateral or to prime, and a sponsor that did it before,
    raise the chance that a document takes value from tranche k. Distance to distress enters
    pi_lme, not this score. Weights are uncalibrated defaults.
    """
    w1, w2, w3, w4, w5 = weights
    return (w1 * (unrestricted_sub_capacity + investment_capacity) / v_mid
            + w2 * float(bare_majority) + w3 * float(pro_rata_carveouts)
            + w4 * (lien_basket + debt_basket) / face_k + w5 * sponsor_behavior)


def pi_lme(score: float, p_liq_8: float, gamma: Sequence[float] = GAMMA_LME_DEFAULT) -> float:
    """LME probability (Section 6.3): pi = sigma(gamma_0 + gamma_1 score_k + gamma_2 p^liq_8).

    Intuition: the option is used when the documents allow it and the issuer nears distress.
    """
    g0, g1, g2 = gamma
    return float(special.expit(g0 + g1 * score + g2 * p_liq_8))


def recovery_lme(senior: float, face: float, mu: float, sigma: float, priming_debt: float = 0.0,
                 value_stripped: float = 0.0) -> float:
    """Stressed recovery R^LME_k (Section 6.3; pp. 499-504).

    Uptier: S_k -> S_k + priming. Drop-down: V -> V (1 - value_stripped / V_mid), so
    mu -> mu + log(1 - value_stripped / e^mu). The closed form of Section 6.2 then applies.

    Intuition: a document move puts new claims ahead of you or takes collateral away.
    """
    frac = value_stripped / math.exp(mu)
    if frac >= 1.0:
        return 0.0
    return recovery_closed_form(senior + priming_debt, face, mu + math.log1p(-frac), sigma)


def recovery_adj(r_clean: float, r_lme: float, pi: float) -> float:
    """LME-adjusted recovery (Section 6.3): R^adj_k = (1 - pi) R_k + pi R^LME_k.

    Intuition: a probability blend of the clean and the stressed waterfall.
    """
    if not 0.0 <= pi <= 1.0:
        raise ValueError("pi must lie in [0, 1]")
    return (1.0 - pi) * r_clean + pi * r_lme


# ---------------------------------------------------------------- 6.4 Outputs


def tranche_outputs(
    tranches: Sequence[Tranche],
    key: str,
    *,
    ebitda_adj: float,
    v_low: float,
    v_mid: float,
    v_high: float,
    v_default: float | None = None,
    admin_claims: float = 0.0,
    p_liq_8: float = 0.0,
    lme_inputs: Mapping[str, float | bool | int] | None = None,
    priming_debt: float = 0.0,
    value_stripped: float = 0.0,
    gamma: Sequence[float] = GAMMA_LME_DEFAULT,
) -> dict[str, float]:
    """Section 6.4 outputs for tranche k.

    Recovery is conditional on default: log V ~ N(log V_default, sigma_V^2) with sigma_V from the
    football field. When `v_default` is None, V_mid is the centre. `ebitda_adj` is annual.

    Intuition: one row per tranche with the value range, LTV, clean and LME recovery,
    the recovery price, and the creation multiple.
    """
    mu_mid, sigma = lognormal_params(v_low, v_mid, v_high)
    centre = v_default if v_default is not None else v_mid
    mu_def = math.log(max(centre, 1e-9))
    s_k, pool = senior_claims(tranches, key, admin_claims)
    r_clean = recovery_closed_form(s_k, pool, mu_def, sigma)
    score = lme_score(v_mid=v_mid, face_k=pool, **(lme_inputs or {}))
    pi = pi_lme(score, p_liq_8, gamma)
    r_l = recovery_lme(s_k, pool, mu_def, sigma, priming_debt, value_stripped)
    r_adj = recovery_adj(r_clean, r_l, pi)

    tk = next(t for t in tranches if t.key == key)
    through_k = s_k - admin_claims + pool
    creation = (s_k - admin_claims + tk.price / 100.0 * tk.face) / ebitda_adj
    return {
        "tev_low": v_low,
        "tev_mid": v_mid,
        "tev_high": v_high,
        "tev_default": centre,
        "v_sigma": sigma,
        **ltv_scenarios(through_k, v_low, v_mid, v_high),
        "recovery_k": r_clean,
        "lgd_k": 1.0 - r_clean,
        "recovery_k_lme": r_l,
        "recovery_k_adj": r_adj,
        "lgd_k_adj": 1.0 - r_adj,
        "lme_score_k": score,
        "pi_lme": pi,
        "recovery_price_k": 100.0 * r_adj,
        "creation_multiple_k": creation,
    }
