"""Expected alpha per bond: forecast-conditional excess return after hedge, losses, and costs (Sections 7.5, 9.2, 9.4).

The forward layer (Section 5.4) gives, for each macro path m, a probability p(m), a fair spread s_fair(m), and
a default probability. This module turns them into the expected return a hedged long position earns over a
horizon of h years, and splits it into parts so that each part traces to an input.

Per path m, for a bond with spread s, spread duration D, residual persistence rho (quarterly), market beta b,
index spread S, and loss given default LGD:

    carry(m)       = (s - b S) h                        spread earned less the hedge's spread
    converge(m)    = D (1 - rho^(4h)) (s - s_fair(m))   Section 7.5: part of the gap to fair that closes by h
    loss(m)        = PD_h(m) LGD - b EL_index(m) h      own expected default loss, less the hedge's (a short
                                                        index position gains when index names default)
    alpha(m)       = carry(m) + converge(m) - loss(m)
    alpha          = sum_m p(m) alpha(m) + E[event P&L] - cost

The hedge removes the systematic channel of Section 9.2: rate moves through the effective rate duration and
spread moves through `beta_mkt`. What remains is the issuer's own return. The cost is the round-trip bid-ask.

Intuition: the bond pays its spread; the hedge costs the market's; the mispricing closes at its measured speed;
defaults take their expected share. Alpha is what is left, averaged over the macro stories.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class BondInputs:
    """One bond at the decision time. Spreads and rates in decimals; durations in years."""

    cusip: str
    oas: float
    spread_duration: float
    rho_q: float = 0.85          # quarterly AR(1) persistence of the residual (Section 7.5); 0.85 = 4-quarter half-life
    beta_mkt: float = 1.0        # sensitivity of the bond spread to the index spread (Section 9.3)
    index_spread: float = 0.0    # hedge instrument spread (CDX HY or sector basket)
    lgd: float = 0.6             # loss given default (Section 6, `lgd_k_adj`)
    bid_ask_bp: float = 0.0      # quoted bid-ask in spread bp; round trip costs once (half on entry, half on exit)


def pd_over_horizon(pd_12m: float, h_years: float) -> float:
    """Constant-hazard PD over h years: 1 - (1 - PD12)^h. Intuition: the 12-month PD compounds."""
    return float(1.0 - (1.0 - pd_12m) ** h_years)


def path_alpha(bond: BondInputs, s_fair: float, pd_12m: float, h_years: float,
               index_el: float = 0.0) -> dict[str, float]:
    """Alpha parts under one macro path (module formula). Returns decimals of price (per 1 of notional).

    `index_el` is the hedge index's expected default loss per year under the path; the hedge earns beta x it.
    """
    carry = (bond.oas - bond.beta_mkt * bond.index_spread) * h_years
    close = 1.0 - bond.rho_q ** (4 * h_years)
    converge = bond.spread_duration * close * (bond.oas - s_fair)
    loss = pd_over_horizon(pd_12m, h_years) * bond.lgd - bond.beta_mkt * index_el * h_years
    return {"carry": carry, "converge": converge, "loss": loss, "alpha": carry + converge - loss}


def expected_alpha(
    bond: BondInputs,
    by_path: pd.DataFrame,
    h_years: float = 0.5,
    event_pnl: float = 0.0,
) -> dict:
    """Probability-weighted alpha over macro paths, net of cost, with its parts and dispersion.

    `by_path` has one row per macro path with columns macro_path, p_path, s_fair, pd_12m, and optionally index_el
    (a "weighted" row, if present, is ignored and recomputed). Returns a dict with per-path rows, the weighted parts, `alpha_net`,
    `alpha_sd` (dispersion across paths), `info_ratio` = alpha_net / alpha_sd, and `passes_g3` (framework F9 G3:
    alpha after cost above zero).
    """
    rows = by_path[by_path["macro_path"] != "weighted"].copy()
    p = rows["p_path"].to_numpy(dtype=float)
    if not np.isclose(p.sum(), 1.0, atol=1e-6):
        raise ValueError(f"p_path sums to {p.sum()}, not 1")
    iel = rows["index_el"] if "index_el" in rows else pd.Series(0.0, index=rows.index)
    parts = pd.DataFrame([path_alpha(bond, s, d, h_years, e) for s, d, e in zip(rows["s_fair"], rows["pd_12m"], iel)])
    parts.insert(0, "macro_path", rows["macro_path"].to_numpy())
    parts.insert(1, "p_path", p)
    w = {k: float((parts[k] * p).sum()) for k in ("carry", "converge", "loss", "alpha")}
    cost = bond.bid_ask_bp / 1e4 * bond.spread_duration  # round trip: bid-ask in spread terms times duration
    net = w["alpha"] + event_pnl - cost
    sd = float(np.sqrt((p * (parts["alpha"] - w["alpha"]) ** 2).sum()))
    return {
        "cusip": bond.cusip, "h_years": h_years, "by_path": parts,
        **{f"{k}_w": v for k, v in w.items()}, "event_pnl": event_pnl, "cost": cost,
        "alpha_net": net, "alpha_net_bp_ann": net / h_years * 1e4,
        "alpha_sd": sd, "info_ratio": net / sd if sd > 0 else float("nan"),
        "passes_g3": bool(net > 0),
    }


def alpha_table(bonds: Mapping[str, BondInputs], by_path: Mapping[str, pd.DataFrame], h_years: float = 0.5,
                event_pnl: Mapping[str, float] | None = None) -> pd.DataFrame:
    """One row per bond: weighted parts, net alpha (also annualised bp), dispersion, information ratio, G3 flag."""
    out = []
    for cusip, b in bonds.items():
        r = expected_alpha(b, by_path[cusip], h_years, (event_pnl or {}).get(cusip, 0.0))
        out.append({k: v for k, v in r.items() if k != "by_path"})
    return pd.DataFrame(out).sort_values("alpha_net", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Full scenario repricing and the decision against cash (RV PDF Section 9, E50 to E60; mapping Top 10 item 1)
# ---------------------------------------------------------------------------


def accrued_interest(coupon: float, years_to_maturity: float, freq: int = 2) -> float:
    """Accrued interest per 100 face on a 30/360 bullet (RV PDF U1, U2): coupon x 100 x fraction of the period run.

    The coupon dates step back from maturity in 1/freq years, so the fraction run is the part of the current period
    already elapsed. Intuition: the buyer pays the seller the coupon earned since the last payment date.
    """
    period = 1.0 / freq
    left = years_to_maturity - np.floor(years_to_maturity / period) * period  # time to the next coupon
    return float(coupon * 100.0 / freq * (1.0 - left / period)) if left > 1e-9 else 0.0


def bond_price(coupon: float, years: float, ytm: float, freq: int = 2) -> float:
    """Dirty price per 100 of a bullet with `years` left (RV PDF E1): sum of coupons and principal at the yield.

    Each cash flow at time t (coupon dates step back from maturity) is discounted by (1 + y/f)^(f t). A bond with
    no time left is worth its principal. Intuition: the price is the present value of what is still to be paid.
    """
    if years <= 1e-9:
        return 100.0
    period = 1.0 / freq
    n = int(np.floor(years / period + 1e-9))
    t = years - np.arange(0, n + 1) * period
    t = t[t > 1e-9]
    v = (1.0 + ytm / freq) ** (-freq * t)
    return float((coupon * 100.0 / freq * v).sum() + 100.0 * v[0])


def coupons_paid(coupon: float, years: float, h: float, freq: int = 2) -> float:
    """Coupons per 100 paid in (0, h] on a bullet with `years` left. Intuition: carry received in cash before H."""
    period = 1.0 / freq
    t = years - np.arange(0, int(np.floor(years / period + 1e-9)) + 1) * period
    return float(coupon * 100.0 / freq * ((t > 1e-9) & (t <= h + 1e-9)).sum())


def expected_shortfall(returns: Sequence[float], probs: Sequence[float], level: float = 0.95) -> float:
    """Discrete expected shortfall of the loss L = -return in the worst (1 - level) of probability (RV PDF E58).

    Intuition: the average loss in the bad tail, with the last state counted only for the part inside the tail.
    """
    r = np.asarray(list(returns), dtype=float)
    p = np.asarray(list(probs), dtype=float)
    tail = 1.0 - level
    order = np.argsort(r)
    acc, s = 0.0, 0.0
    for i in order:
        take = min(p[i], tail - acc)
        if take <= 0:
            break
        s += take * (-r[i])
        acc += take
    return float(s / tail)


def decision_against_cash(dirty_price: float, coupon: float, years: float, h: float, states: pd.DataFrame,
                          recovery_pv_per_1: float, r_cash: float, freq: int = 2, es_level: float = 0.95) -> dict:
    """Common-capital horizon wealth of one bond against cash, by macro path and default state (RV PDF E50 to E58).

    `states` has one row per macro path m: p_path, pd_h (default probability over h), y_tsy_H (Treasury par yield at
    H for the remaining tenor), s_H (the bond's spread at H). Per path and state d in {survive, default}:
        q_{m,d}  = p(m) (1 - PD_H(m)) or p(m) PD_H(m)
        W_survive = price at H of what is left, at y_tsy_H + s_H, plus coupons paid in (0, H]
        W_default = 100 R_PV  (recovery discounted for delay; no further coupons)
        R_net = W / K - 1, K = the dirty price today; X = R_net - r_cash h
    Returns the state table and mu = sum q X (excess over cash), pi_loss = P(R_net < 0), pi_cash = P(X < 0), and
    es95 of L = -R_net. Default and recovery sit inside the cash flows, so expected loss is not subtracted again
    (RV PDF R164; mapping C3).

    Intuition: put the same money in the bond or in cash for H; compare what you hold at H across every story.
    """
    rows = []
    for r in states.itertuples(index=False):
        w_s = bond_price(coupon, years - h, r.y_tsy_H + r.s_H, freq) + coupons_paid(coupon, years, h, freq)
        w_d = 100.0 * recovery_pv_per_1
        for state, q, w in (("survive", r.p_path * (1 - r.pd_h), w_s), ("default", r.p_path * r.pd_h, w_d)):
            rn = w / dirty_price - 1.0
            rows.append({"macro_path": r.macro_path, "state": state, "q": q, "wealth": w, "r_net": rn,
                         "x_cash": rn - r_cash * h})
    tab = pd.DataFrame(rows)
    q = tab["q"].to_numpy()
    if not np.isclose(q.sum(), 1.0, atol=1e-6):
        raise ValueError(f"state probabilities sum to {q.sum()}, not 1")
    return {"states": tab, "mu_excess": float((q * tab["x_cash"]).sum()),
            "pi_loss": float(q[tab["r_net"].to_numpy() < 0].sum()), "pi_cash": float(q[tab["x_cash"].to_numpy() < 0].sum()),
            "es95": expected_shortfall(tab["r_net"], q, es_level), "expected_wealth": float((q * tab["wealth"]).sum())}


def credit_excess_states(dirty_price: float, coupon: float, years: float, h: float, paths: pd.DataFrame,
                         recovery_pv_per_1: float, r_tsy: float, cost_in: float = 0.0, cost_out: float = 0.0,
                         freq: int = 2, es_level: float = 0.95) -> dict:
    """Total return over a Treasury of the same tenor, by macro path, with rates held (methodology 7.7).

    `paths` has one row per macro path m: p_path, d_h (share of the claim that defaults within h), y_H (Treasury
    yield of the remaining tenor at H; today's curve, so rates are held), s_H (the spread at H). Per path:
        W_s = price at H at y_H + s_H, less the exit cost, plus coupons paid in (0, H];  W_d = 100 R_PV
        W   = (1 - d_h) W_s + d_h W_d;  K = dirty price + entry cost;  X = W / K - 1 - r_tsy
    `cost_in` and `cost_out` are fractions of price. Returns the path table, mu = sum p X, and es = the
    expected shortfall of -X in the worst (1 - es_level) of probability.
    Intuition: what the credit earns above Treasuries in each economy, with the default share taken on the way.
    The path default share, not a 0 / 1 jump, measures the risk a diversified book carries; the expected default
    loss sits inside mu either way.
    """
    rows = []
    k = dirty_price + 100.0 * cost_in
    for r in paths.itertuples(index=False):
        w_s = bond_price(coupon, years - h, r.y_H + r.s_H, freq) - 100.0 * cost_out + coupons_paid(coupon, years, h, freq)
        w = (1.0 - r.d_h) * w_s + r.d_h * 100.0 * recovery_pv_per_1
        rows.append({"macro_path": r.macro_path, "p_path": r.p_path, "d_h": r.d_h, "s_H": r.s_H, "wealth": w,
                     "x_tsy": w / k - 1.0 - r_tsy})
    tab = pd.DataFrame(rows)
    p = tab["p_path"].to_numpy(dtype=float)
    if not np.isclose(p.sum(), 1.0, atol=1e-6):
        raise ValueError(f"path probabilities sum to {p.sum()}, not 1")
    return {"paths": tab, "mu": float((p * tab["x_tsy"]).sum()), "es": expected_shortfall(tab["x_tsy"], p, es_level)}


def risk_premium_alpha(mu_bond: float, es_bond: float, mu_index: float, es_index: float) -> dict:
    """How much alpha: the bond's excess return less the premium its risk needs at the index's price (methodology 7.7).

    lambda = max(0, mu_index) / es_index, the index's expected excess return per unit of tail loss;
    required = lambda x max(0, es_bond); alpha = mu_bond - required.
    The price of risk is undefined when the index has no tail loss in the scenarios (es_index <= 0): alpha is NaN.
    A negative index excess sets lambda to 0 and raises a flag: the scenarios then pay nothing for credit risk.
    Intuition: the bond must pay at least what the market pays for the same amount of bad-case loss.
    """
    if not (es_index == es_index) or es_index <= 0:
        return {"lambda": float("nan"), "required": float("nan"), "alpha": float("nan"),
                "flag": "the index has no tail loss in these scenarios: the price of risk is undefined"}
    lam = max(0.0, mu_index) / es_index
    req = lam * max(0.0, es_bond)
    return {"lambda": lam, "required": req, "alpha": mu_bond - req,
            "flag": "the index earns no excess in these scenarios" if mu_index <= 0 else None}


def opportunity_cost(mu: Mapping[str, float], es: Mapping[str, float], es_budget: float) -> dict[str, dict]:
    """Opportunity cost against the best admissible alternative, cash included (RV PDF E60, R87; framework F1 R8).

    Admissible: ES95 <= budget. Cash is always admissible with mu = 0. For each bond a,
    OC_a = max(0, max_{admissible j != a} mu_j) - mu_a, and `best_admissible` names that j (cash when no bond beats it).
    Intuition: the position must beat the best thing the same money could do instead.
    """
    out = {}
    for a in mu:
        others = {j: mu[j] for j in mu if j != a and es.get(j, np.inf) <= es_budget}
        best, best_mu = ("cash", 0.0)
        if others:
            j = max(others, key=others.get)
            if others[j] > 0:
                best, best_mu = j, others[j]
        out[a] = {"best_admissible": best, "opportunity_cost": best_mu - mu[a], "admissible": es.get(a, np.inf) <= es_budget}
    return out


def treasury_return(y_T: float, y_left: float, years: float, h: float, freq: int = 2) -> float:
    """Horizon return of a Treasury with coupon y_T and the bond's dates, priced at y_T today and y_left at H.

    R = (price at H + coupons paid in (0, H]) / dirty price today - 1. The dirty price today includes accrued
    interest, so the denominator is the bond price at its own yield, not 100. Intuition: the rate hedge's return when
    the curve does not move is its yield plus roll-down over the horizon.
    """
    p0 = bond_price(y_T, years, y_T, freq)
    return (bond_price(y_T, years - h, y_left, freq) + coupons_paid(y_T, years, h, freq)) / p0 - 1.0
