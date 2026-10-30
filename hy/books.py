"""Group G4: the book methods per issuer. Kricheff (A Pragmatist's Guide to Leveraged Finance, 2nd ed.) and
Ganguin and Bilardello (Standard & Poor's Fundamentals of Corporate Credit Analysis, 2005).

Kricheff: the cash-flow bridge (ch. 9, "Free Cash Flow"; ch. 10, "Free Cash Flow Ratios"), the credit ratio set
(ch. 10, "Credit Ratios"), the credit snapshot (ch. 24), and spread per turn of leverage (ch. 21, "Value, Relative
Value, and Comparable Analysis").
S&P: adjusted debt with leases (ch. 5; Appendix E lease model at 10%), the cash-flow ratio set (ch. 5, "Cash Flow
Ratios"), the 1-to-10 score template (ch. 10, Tables 10-1 to 10-7), and the 2000-2002 CreditStats medians by rating.
The 2005 edition has no post-2008 anchor matrix; the Table 10-5 weighting stands in for it (stated).
"""

from __future__ import annotations

from typing import Any, Mapping

import numpy as np

from hy import state

# S&P ch. 10 (Tables 10-8 to 10-12): 2002 CreditStats medians by rating class, with the score at the class midpoint
# (Table 10-1: very low risk 1-2 = AA, low 3-4 = A, moderate 5-6 = BBB, high 7-8 = BB, very high 9-10 = B).
SP_MEDIANS_2002 = {  # class: (score, debt/capital %, FFO/debt %, FOCF/debt %, EBITDA interest cover x)
    "AA": (1.5, 37.6, 66.2, 36.8, 15.9),
    "A": (3.5, 40.6, 42.7, 23.1, 10.0),
    "BBB": (5.5, 46.3, 30.7, 16.8, 5.5),
    "BB": (7.5, 57.5, 19.5, 8.5, 3.2),
    "B": (9.5, 78.5, 10.8, 2.5, 1.8),
}
# End points for scores beyond the medians (v0, stated): 1 at the best end; 10 at debt/capital 100%, FFO/debt 0,
# FOCF/debt -10%, cover 1.0x (Kricheff ch. 10: 1x is the point where interest is only just covered).
SP_ENDS = {"debt_to_cap": (20.0, 100.0), "ffo_to_debt": (100.0, 0.0), "focf_to_debt": (60.0, -10.0), "ebitda_cov": (25.0, 1.0)}
# S&P ch. 10 prose (SP:7027): profitability 15%, balance sheet 15%, cash-flow adequacy 40%, financial flexibility 30%.
SP_FIN_WEIGHTS = {"profitability": 0.15, "debt_to_cap": 0.15, "ffo_to_debt": 0.20, "focf_to_debt": 0.20, "ebitda_cov": 0.30}
# S&P ch. 10 Table 10-5: business and financial weights by business risk class (midpoints of the ranges).
SP_BF_WEIGHTS = ((2.0, 0.60), (4.0, 0.55), (6.0, 0.45), (8.0, 0.30), (10.0, 0.15))
# Industry risk by framework F2 archetype (S&P ch. 2, Table 2-2 is garbled in the conversion; v0 mapping, stated):
# A1 retail high, A2 healthcare services low to moderate, A3 commodity high, A4 cyclical high, A5 contracted
# assets moderate, A6 software and technology moderate, A7 asset-specific moderate to high.
SP_INDUSTRY = {"A1": 7.0, "A2": 4.0, "A3": 8.0, "A4": 7.0, "A5": 5.0, "A6": 5.0, "A7": 6.0}
SP_LEASE_RATE = 0.10  # Appendix E: discount and implicit interest at 10%
SP_CLASSES = ((2.0, "AA"), (4.0, "A"), (6.0, "BBB"), (8.0, "BB"), (10.0, "B"))


def _div(a: float, b: float) -> float:
    return a / b if b and b == b and a == a else float("nan")


# --------------------------------------------------------------------------- Kricheff


def kricheff_bridge(ebitda_adj: float, capex: float, cash_interest: float, cash_taxes: float, delta_wc: float,
                    cfo: float, dividends: float | None = None) -> dict[str, float]:
    """Kricheff's free cash flow (ch. 9 "Free Cash Flow"; ch. 10 "Free Cash Flow Ratios").

    FCF = adjusted EBITDA - capex - cash interest - cash taxes - increase in working capital. Check: FCF + capex
    should be close to CFO ("FCF before capex should approximate CFO"); `cfo_gap` is the difference. FCF after
    dividends subtracts a regular dividend when one is given. Unleveraged FCF = EBITDA - capex.
    Intuition: start from the earnings lenders lend against, then take out every cash bill before debt repayment.
    """
    fcf = state.fcf(ebitda_adj, 0.0, capex, cash_interest, cash_taxes, delta_wc)  # the one bridge (hy.state)
    return {"ebitda_adj": ebitda_adj, "capex": capex, "cash_interest": cash_interest, "cash_taxes": cash_taxes,
            "delta_wc": delta_wc, "fcf": fcf, "unleveraged_fcf": ebitda_adj - capex, "cfo": cfo,
            "cfo_gap": (fcf + capex) - cfo if cfo == cfo else float("nan"),
            "fcf_after_dividends": fcf - dividends if dividends is not None else float("nan")}


def kricheff_ratios(ebitda: float, capex: float, maint_capex: float, cash_interest: float, debt: float, cash: float,
                    fcf: float, market_cap: float) -> dict[str, float]:
    """Kricheff's credit ratio set (ch. 10 "Credit Ratios") and the equity cushion (ch. 10, EV against leverage).

    EBITDA / cash interest; (EBITDA - capex) / interest, "the more pragmatic ratio"; (EBITDA - maintenance capex) /
    interest; debt / EBITDA; net debt / EBITDA; FCF / debt; EBITDA / debt (the highest rate at 1x cover);
    EV / EBITDA with EV = market cap + debt - cash; equity cushion = 1 - debt / EV.
    Intuition: how many times earnings pay interest, how many years they take to repay debt, how much equity sits below.
    """
    ev = market_cap + debt - cash if market_cap == market_cap else float("nan")
    return {"cash_cov": _div(ebitda, cash_interest), "after_capex_cov": _div(ebitda - capex, cash_interest),
            "after_maint_capex_cov": _div(ebitda - maint_capex, cash_interest), "lev_gross": state.lev_gross(debt, ebitda),
            "lev_net": state.net_lev(debt, cash, ebitda), "fcf_to_debt": _div(fcf, debt), "ebitda_to_debt": _div(ebitda, debt),
            "ev_to_ebitda": _div(ev, ebitda), "equity_cushion": 1.0 - _div(debt, ev) if ev == ev else float("nan")}


def kricheff_snapshot(cfo: float, capex: float, cash_interest: float, wall_18m: float, liquidity: float) -> dict[str, Any]:
    """Kricheff ch. 24 credit snapshot rule: if CFO does not cover capex and interest, or maturities are near and
    liquidity does not meet them, do a detailed liquidity analysis. CFO under US GAAP is after interest paid, so the
    test is CFO >= capex. Intuition: a business that cannot fund its own spending lives on the capital markets.
    """
    funds_itself = cfo == cfo and capex == capex and cfo >= capex
    near = wall_18m == wall_18m and wall_18m > 0 and (liquidity != liquidity or liquidity < wall_18m)
    return {"funds_itself": bool(funds_itself), "maturities_exceed_liquidity": bool(near),
            "detailed_liquidity_needed": bool((not funds_itself) or near)}


def spread_per_turn_bp(spread_bp: float, leverage: float) -> float:
    """Spread per turn of leverage (Kricheff ch. 21): spread to worst / leverage at the bond, bp per turn.

    Bond-level leverage needs the debt ahead of each bond; with no face by rank, total leverage stands in (stated).
    Intuition: how much spread the bond pays for each year of earnings the debt represents.
    """
    return _div(spread_bp, leverage) if leverage and leverage > 0 else float("nan")


# Cut-offs for the E13 trap guard. The book gives the three signs but no numbers (p. 124), so these are our choice
# (decision page 2026-10-22-e13-trap-guard). Peer cut-offs join the fixed ones when the run has min_peers values.
SPT_TRAP = {"lev_q": 0.8, "fcf_q": 0.2, "tev_debt_thin": 1.25, "min_peers": 5, "lev_abs": 6.0, "fcf_abs": 0.02,
            "signs_for_trap": 2}


def spt_trap_guard(lev: float | None, fcf_to_debt: float | None, tev_to_debt: float | None,
                   lev_peers, fcf_peers) -> dict[str, Any]:
    """Trap guard for spread per turn (Kricheff ch. 21, p. 124; methodology 7.4, E13).

    The book's widest spread per turn bond (DataFone) is a trap on three signs: the highest total leverage (7x), FCF to
    debt "meaningfully lower" than peers (0.1%), and a "minimal" equity cushion. Hard floor: FCF / debt <= 0 or
    TEV / debt <= 1, or either unknown, is a trap. Signs: leverage >= the run's lev_q quantile; FCF / debt <= the
    run's fcf_q quantile; TEV / debt <= tev_debt_thin. Two or more signs is a trap. The fixed cut-offs lev_abs and
    fcf_abs always apply too, so a run full of cash burners cannot drag the FCF cut below fcf_abs. A run with fewer
    than min_peers values uses only the fixed cut-offs.
    Intuition: one sign is the risk the spread pays for; the signs together are the book's trap.
    """
    c = SPT_TRAP
    fin = lambda x: x is not None and x == x  # noqa: E731
    hard = not (fin(fcf_to_debt) and fcf_to_debt > 0 and fin(tev_to_debt) and tev_to_debt > 1)
    lp = np.array([x for x in lev_peers if fin(x)], dtype=float)
    fp = np.array([x for x in fcf_peers if fin(x)], dtype=float)
    peer = len(lp) >= c["min_peers"] and len(fp) >= c["min_peers"]
    lev_cut = min(float(np.quantile(lp, c["lev_q"])), c["lev_abs"]) if peer else c["lev_abs"]
    fcf_cut = max(float(np.quantile(fp, c["fcf_q"])), c["fcf_abs"]) if peer else c["fcf_abs"]
    signs = {"high_leverage": bool(fin(lev) and lev >= lev_cut),
             "low_fcf": bool(fin(fcf_to_debt) and fcf_to_debt <= fcf_cut),
             "thin_cushion": bool(fin(tev_to_debt) and tev_to_debt <= c["tev_debt_thin"])}
    return {"hard_fail": bool(hard), "signs": signs, "basis": "peer" if peer else "absolute",
            "lev_cut": lev_cut, "fcf_cut": fcf_cut,
            "trap": bool(hard or sum(signs.values()) >= c["signs_for_trap"])}


# --------------------------------------------------------------------------- S&P


def sp_adjusted(debt: float, lease_liability: float, ebitda: float, cash_interest: float) -> dict[str, float]:
    """S&P adjusted debt, EBITDA and interest for operating leases (ch. 5 "Adjusted debt"; Appendix E at 10%).

    Debt_adj = debt + lease liability; implicit interest = 10% x lease liability, added to interest and to EBITDA
    (the Appendix E reading; the book's text and its operating-income line disagree, stated). The ASC 842 liability
    replaces the book's own present value of the commitments. Intuition: a lease is a loan by another name.
    """
    lease = lease_liability if lease_liability == lease_liability else 0.0
    ii = SP_LEASE_RATE * lease
    return {"debt_adj": debt + lease, "implicit_interest": ii, "ebitda_adj": ebitda + ii, "interest_adj": cash_interest + ii}


def sp_ratios(debt_adj: float, market_cap: float, ffo: float, focf: float, ebitda_adj: float, interest_adj: float,
              ebitda_margin: float) -> dict[str, float]:
    """S&P core ratios (ch. 5 "Cash Flow Ratios", "Leverage Ratios"): debt / (debt + market equity) in %,
    FFO / debt %, FOCF / debt %, EBITDA / interest x, EBITDA margin. FFO = CFO + increase in working capital
    (ch. 5 Table 5-1: OCF = FFO +- change in WC); FOCF = CFO - capex.
    Intuition: payback (how fast cash repays debt) and payment (how easily earnings pay interest).
    """
    return {"debt_to_cap": 100 * _div(debt_adj, debt_adj + market_cap) if market_cap == market_cap else float("nan"),
            "ffo_to_debt": 100 * _div(ffo, debt_adj), "focf_to_debt": 100 * _div(focf, debt_adj),
            "ebitda_cov": _div(ebitda_adj, interest_adj), "ebitda_margin": ebitda_margin}


def _ratio_score(name: str, x: float) -> float:
    """Score 1 (best) to 10 (default) by linear interpolation between the 2002 CreditStats medians (S&P ch. 10)."""
    if x != x:
        return float("nan")
    col = {"debt_to_cap": 1, "ffo_to_debt": 2, "focf_to_debt": 3, "ebitda_cov": 4}[name]
    best, worst = SP_ENDS[name]
    xs = [best] + [v[col] for v in SP_MEDIANS_2002.values()] + [worst]
    ys = [1.0] + [v[0] for v in SP_MEDIANS_2002.values()] + [10.0]
    if xs[0] > xs[-1]:  # higher is better: np.interp needs increasing x
        xs, ys = xs[::-1], ys[::-1]
    return float(np.interp(x, xs, ys))


def sp_margin_score(margin: float) -> float:
    """Profitability score (S&P ch. 5: margins above 20% strong, 10% to 20% average, below 10% weak) on the 1-10 scale:
    strong 3, average 5, weak 8 (v0 mapping of the three words, stated)."""
    if margin != margin:
        return float("nan")
    return 3.0 if margin > 0.20 else (5.0 if margin >= 0.10 else 8.0)


def sp_financial_score(ratios: Mapping[str, float]) -> dict[str, Any]:
    """Financial risk score 1 to 10 (S&P ch. 10 "Financial Risk and Credit Ratios", Table 10-4 template).

    Each ratio scores against the 2002 medians; the margin scores on the ch. 5 words; the weights follow the ch. 10
    prose (cash-flow adequacy most). Missing parts drop out and the weights renormalise.
    Intuition: where the issuer's ratios sit among the rating classes, cash flow first.
    """
    parts = {k: _ratio_score(k, ratios.get(k, float("nan"))) for k in ("debt_to_cap", "ffo_to_debt", "focf_to_debt", "ebitda_cov")}
    parts["profitability"] = sp_margin_score(ratios.get("ebitda_margin", float("nan")))
    ok = {k: v for k, v in parts.items() if v == v}
    w = sum(SP_FIN_WEIGHTS[k] for k in ok)
    score = sum(SP_FIN_WEIGHTS[k] * v for k, v in ok.items()) / w if w else float("nan")
    return {"parts": parts, "sp_financial_score": score}


def sp_business_score(archetype: str, revenue_yoy_sd: float, top_customer: float | None) -> dict[str, Any]:
    """Business risk score 1 to 10 (S&P ch. 2 and 3; ch. 10 "Industry and Business Risk Scores", Table 10-3 template).

    Keys and v0 weights: industry risk by archetype 0.50; sales consistency (sd of year-on-year revenue growth:
    below 5% scores 3, 5% to 15% scores 5, above 15% scores 7) 0.25; customer diversity (top customer above 20%
    scores 8, 10% to 20% scores 6, else or undisclosed 5) 0.25.
    Intuition: how hard the industry is, how steady the sales are, and how much one customer can hurt.
    """
    ind = SP_INDUSTRY.get(archetype, 6.0)
    cons = float("nan") if revenue_yoy_sd != revenue_yoy_sd else (3.0 if revenue_yoy_sd < 0.05 else (5.0 if revenue_yoy_sd <= 0.15 else 7.0))
    tc = top_customer if top_customer is not None and top_customer == top_customer else None
    div = 8.0 if tc is not None and tc > 0.20 else (6.0 if tc is not None and tc > 0.10 else 5.0)
    parts = {"industry": ind, "sales_consistency": cons, "diversity": div}
    wts = {"industry": 0.50, "sales_consistency": 0.25, "diversity": 0.25}
    ok = {k: v for k, v in parts.items() if v == v}
    w = sum(wts[k] for k in ok)
    return {"parts": parts, "business_risk_score": sum(wts[k] * v for k, v in ok.items()) / w}


def sp_class(score: float) -> str:
    """Rating class of a 1-10 score (S&P ch. 10 Table 10-1 bands)."""
    if score != score:
        return "n/a"
    for hi, c in SP_CLASSES:
        if score <= hi:
            return c
    return "B"


def sp_default_risk_score(business: float, financial: float) -> dict[str, Any]:
    """Default risk score (S&P ch. 10 Table 10-5 weights, Table 10-7 combination): w_b B + w_f F, with the weights set
    by the business risk class (riskier business, more weight on the financial score).
    Intuition: a weak business needs a strong balance sheet; a strong business can carry more debt.
    """
    wb = next(w for hi, w in SP_BF_WEIGHTS if business <= hi) if business == business else float("nan")
    s = wb * business + (1 - wb) * financial if wb == wb and financial == financial else float("nan")
    return {"w_business": wb, "sp_default_risk_score": s, "sp_anchor_class": sp_class(s)}
