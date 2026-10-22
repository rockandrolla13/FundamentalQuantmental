"""Group G3: the credit skills applied to public high yield issuers (hy-model-standards and six private-credit skills).

Each function implements one rule that public filings (XBRL, 10-K and 10-Q text, Compustat) can support. Rules that
need a compliance certificate, a borrower package or a management plan do not transfer; `NOT_TRANSFERABLE` lists
them so the memo can say so. Thresholds are quoted from the skills and are v0 defaults (framework R9).

Skill files: .claude/skills/hy-model-standards/SKILL.md; ~/.claude/skills/{credit-model-standards,
credit-memo-standards, ebitda-addback-treatment, covenant-compliance, borrower-monitoring,
quarterly-package-extraction}/SKILL.md.
"""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

import numpy as np

# ebitda-addback-treatment: flag one category above 5% of EBITDA; flag the total above 10% (the skill says 10-15%).
ADDBACK_SINGLE = 0.05
ADDBACK_TOTAL = 0.10
ADDBACK_RECUR_Q = 3          # "same add-back at similar levels for 3-4 consecutive quarters": not one-time
FCF_CHECK_TOL = 0.15         # hy-model-standards FCF check: |(OCF - capex) - waterfall FCF| / EBITDA (spec S3: 0.15)
# covenant-compliance cushion bands.
HEADROOM_COMFORT, HEADROOM_TIGHT = 0.20, 0.10
# borrower-monitoring: performance against plan (public proxy: the same quarters a year earlier).
WATCH_CLOSELY, WATCHLIST = 0.10, 0.20
TIERS = ("none", "watch closely", "watchlist", "workout")

NOT_TRANSFERABLE = [
    ("covenant-compliance", "The compliance certificate is the source of truth; public bonds have none. "
     "Headroom here uses our own ratio against a level parsed from the filing text."),
    ("covenant-compliance", "Equity cures, step-down schedules and window-dressing checks need the credit agreement "
     "and monthly revolver balances."),
    ("borrower-monitoring", "Performance against the sponsor plan: no plan is public. The proxy is the same "
     "quarters a year earlier."),
    ("ebitda-addback-treatment", "Add-back caps and the certificate reconciliation live in the credit agreement. "
     "Compustat gives one special-items line, not the category table."),
    ("credit-memo-standards", "Sources and uses at entry, the sponsor case and the management call apply to new "
     "loans, not to bonds bought in the secondary market."),
    ("quarterly-package-extraction", "Monthly lender packages do not exist for public issuers; XBRL quarters "
     "replace them."),
]


def _div(a: float, b: float) -> float:
    return a / b if b and b == b and a == a else float("nan")


# --------------------------------------------------------------------------- ebitda-addback-treatment


def addback_bridge(ebitda_rep_q: Sequence[float], addback_q: Sequence[float], cash_share: float = 0.0) -> dict[str, Any]:
    """Reported-to-adjusted EBITDA bridge and its flags (ebitda-addback-treatment; credit-memo-standards item 7).

    Inputs are quarterly, oldest first: reported EBITDA and the add-back (minus Compustat special items). LTM uses
    the last four. load = addback_LTM / |EBITDA_rep LTM|. Flags: single category above 5% of EBITDA; total above 10%;
    recurring when the last 3 or more quarters carry an add-back of the same sign. cash_effect = cash_share x
    addback_LTM is the cash that left the business (decision page 2026-10-21-fcf-cash-nonrecurring: v0 share 0).

    Intuition: an add-back that shows up every quarter is a cost of doing business, not a one-off.
    """
    rep = np.asarray(list(ebitda_rep_q), dtype=float)
    ab = np.nan_to_num(np.asarray(list(addback_q), dtype=float))
    last = rep[-4:]
    n_ok = int((~np.isnan(last)).sum())
    # One quarter missing: 3 quarters x 4/3, the input layer's LTM fallback; fewer than 3: no LTM.
    rep_ltm = float(np.nansum(last)) * (4.0 / n_ok) if n_ok >= 3 else float("nan")
    ab_ltm = float(ab[-4:].sum())
    load = _div(ab_ltm, abs(rep_ltm))
    run = 0
    sign = np.sign(ab[-1]) if ab.size else 0.0
    for x in ab[::-1]:
        if sign != 0 and np.sign(x) == sign and x != 0:
            run += 1
        else:
            break
    flags = {"single_above_5pct": bool(load == load and abs(load) > ADDBACK_SINGLE),
             "total_above_10pct": bool(load == load and abs(load) > ADDBACK_TOTAL),
             "recurring": bool(run >= ADDBACK_RECUR_Q)}
    return {"ebitda_rep_ltm": rep_ltm, "addback_ltm": ab_ltm, "ebitda_adj_ltm": rep_ltm + ab_ltm,
            "addback_load": load, "recurring_quarters": int(run), "cash_effect": cash_share * ab_ltm,
            "cash_effect_if_all_cash": ab_ltm, "addback_flags": flags}


def fcf_check_gap(ocf: float, capex: float, ebitda_adj: float, cash_nr: float, cash_interest: float,
                  cash_tax: float, delta_wc: float) -> dict[str, float | bool]:
    """FCF check of hy-model-standards and credit-model-standards: waterfall FCF against OCF - capex.

    Waterfall FCF = EBITDA_adj - CashNR - capex - cash interest - cash tax - dWC (methodology 4.2). gap =
    |(OCF - capex) - waterfall| / EBITDA_adj; a gap above the 15% tolerance raises a flag (spec S3; the skill
    names none). Intuition: two roads to free cash flow must meet; when they do not, something is off the bridge.
    """
    wf = ebitda_adj - cash_nr - capex - cash_interest - cash_tax - delta_wc
    gap = _div(abs((ocf - capex) - wf), abs(ebitda_adj))
    return {"fcf_waterfall": wf, "fcf_ocf_route": ocf - capex, "fcf_check_gap": gap,
            "fcf_check_flag": bool(gap == gap and gap > FCF_CHECK_TOL)}


# --------------------------------------------------------------------------- covenant-compliance

_RATIO = r"(\d+(?:\.\d+)?)\s*(?:to|:)\s*1(?:\.0+)?\b"
COVENANT_PATTERNS = {
    "max_leverage": re.compile(r"((?:[\w\-]+ ){0,5}leverage ratio)[^;]{0,160}?(?:not to exceed|no more than|not more than|"
                               r"maximum|financial covenant of|of)\s*(?:of\s*)?" + _RATIO, re.I),
    "min_coverage": re.compile(r"((?:[\w\-]+ ){0,4}(?:interest coverage|fixed charge coverage|debt service ratio|"
                               r"debt service coverage))[^;]{0,200}?(?:not less than|at least|minimum|"
                               r"financial covenant of|of)\s*(?:of\s*)?" + _RATIO, re.I),
    "min_liquidity": re.compile(r"((?:free |minimum )liquidity)[^;]{0,60}?(?:no less than|not less than|at least|of)\s*"
                                r"\$\s?([\d,]+(?:\.\d+)?)\s*(million|billion)?", re.I),
}


def parse_covenants(text: str) -> list[dict[str, Any]]:
    """Maintenance covenant levels stated in the 10-K or 10-Q debt note (covenant-compliance; methodology 4.6).

    Finds a maximum leverage ratio, a minimum coverage ratio, and a minimum liquidity amount in plain text. Returns
    one dict per covenant kind (first match in the text) with the matched words as evidence, a `springing` flag
    (the test applies only below a trigger), and a `subsidiary` flag (the test binds a subsidiary group, so the
    consolidated ratio is only a proxy).

    Intuition: the filing often states the test level in one sentence; read it before calling headroom open.
    """
    t = re.sub(r"\s+", " ", text)
    out = []
    for kind, pat in COVENANT_PATTERNS.items():
        for m in pat.finditer(t):
            ctx = t[max(0, m.start() - 300): m.end() + 60]
            level = float(m.group(2).replace(",", ""))
            if kind == "min_liquidity":
                level = level / 1e6 if not m.group(3) and level > 1e5 else level * (1e3 if (m.group(3) or "").lower() == "billion" else 1.0)
            if kind != "min_liquidity" and not 0.5 <= level <= 15:
                continue
            out.append({"kind": kind, "name": m.group(1).strip(), "level": level,
                        "springing": bool(re.search(r"\bunless\b|falls below|springing|to the extent", ctx[250:], re.I)),
                        "subsidiary": bool(re.search(r"\b(?:WRF|subsidiar|MGM China|Macau|CVA)\b", m.group(0))),
                        "evidence": ctx[200:][:300]})
            break
    return out


def covenant_headroom(kind: str, level: float, actual: float) -> float:
    """Headroom as the EBITDA cushion (covenant-compliance; methodology 4.6 H_t = 1 - Lev / Lev_max).

    Leverage: H = 1 - actual / max. Coverage: H = 1 - min / actual (EBITDA can fall by H before the test trips).
    Liquidity: H = 1 - min / actual. Intuition: the share by which the measure can worsen before a breach.
    """
    if actual != actual or level != level:
        return float("nan")
    if kind == "max_leverage":
        return 1.0 - _div(actual, level)
    return 1.0 - _div(level, actual)


def headroom_tier(h: float) -> str:
    """Cushion band of covenant-compliance: >= 20% comfortable, 10% to 20% elevated attention, < 10% tight, < 0 breach."""
    if h != h:
        return "open"
    if h < 0:
        return "breach"
    return "comfortable" if h >= HEADROOM_COMFORT else ("elevated attention" if h >= HEADROOM_TIGHT else "tight")


# --------------------------------------------------------------------------- borrower-monitoring


def trajectory(series_q: Mapping[str, Sequence[float]], higher_is_better: Mapping[str, bool] | None = None) -> dict[str, dict]:
    """Trend call per dimension from year-on-year quarterly changes (borrower-monitoring, "Trajectory").

    For each dimension, take the year-on-year change of each of the last four quarters (needs eight quarters). Count
    the consecutive most recent quarters that moved the same way. 1 quarter: an observation; 2: a data point;
    3 or 4: a trend. The call is "improving", "deteriorating" or "stable" (no change of note: |change| < 1%).

    Intuition: one bad quarter is noise; three in a row is a trend the lender must act on.
    """
    hib = higher_is_better or {}
    out = {}
    for k, s in series_q.items():
        x = np.asarray(list(s), dtype=float)
        if x.size < 8 or np.isnan(x[-8:]).any():
            out[k] = {"call": "open", "weight": "no data", "run": 0, "yoy_last": float("nan")}
            continue
        yoy = (x[-4:] - x[-8:-4]) / np.where(np.abs(x[-8:-4]) > 0, np.abs(x[-8:-4]), np.nan)
        good = 1.0 if hib.get(k, True) else -1.0
        sgn = np.where(np.abs(yoy) < 0.01, 0.0, np.sign(yoy) * good)
        run, last = 0, sgn[-1]
        for v in sgn[::-1]:
            if v == last:
                run += 1
            else:
                break
        call = "stable" if last == 0 else ("improving" if last > 0 else "deteriorating")
        weight = "observation" if run == 1 else ("data point" if run == 2 else "trend")
        out[k] = {"call": call, "weight": weight, "run": int(run), "yoy_last": float(yoy[-1])}
    return out


def watchlist_tier(ebitda_vs_prior: float, fcf_ltm: float, liquidity: float, wall_18m: float, runway_q: float | None,
                   wall_cover_4: float | None, refi_score: int | None, headroom: float = float("nan"),
                   revolver_known: bool = True) -> dict[str, Any]:
    """Watchlist tier (borrower-monitoring categories 1 and 2; covenant-compliance bands).

    Category 1 (performance against plan; proxy: LTM EBITDA against the LTM a year earlier): a fall of 10% or more
    is "watch closely"; 20% or more is "watchlist". Category 2 (each one puts the issuer on the watchlist):
    insufficient cash flow (LTM FCF < 0); thin liquidity (liquidity below the 18-month wall, or runway under four
    quarters); a maturity with no clear refinancing path (base-case wall cover below 1 and refinance score 2 or less).
    Headroom below 10% adds "watchlist"; a breach is "workout"; so is thin liquidity together with no refinancing path.
    The skill's thin-liquidity test is "no other sources": with the revolver capacity unknown (`revolver_known` False)
    the trigger cannot be read, so it becomes an open item, not a flag.

    Intuition: the borrower should be on the watchlist before the breach, not after it.
    """
    reasons, tier = [], 0
    if ebitda_vs_prior == ebitda_vs_prior:
        if ebitda_vs_prior <= -WATCHLIST:
            tier = max(tier, 2)
            reasons.append(f"EBITDA {ebitda_vs_prior:.0%} against a year earlier")
        elif ebitda_vs_prior <= -WATCH_CLOSELY:
            tier = max(tier, 1)
            reasons.append(f"EBITDA {ebitda_vs_prior:.0%} against a year earlier")
    thin = (liquidity == liquidity and wall_18m == wall_18m and liquidity < wall_18m) or (
        runway_q is not None and runway_q == runway_q and runway_q < 4)
    open_items = []
    if thin and not revolver_known:
        thin = False
        open_items.append("liquidity against debt due cannot be read: revolver capacity not tagged")
    no_path = wall_cover_4 is not None and wall_cover_4 < 1 and (refi_score if refi_score is not None else 0) <= 2
    for flag, text in ((fcf_ltm == fcf_ltm and fcf_ltm < 0, "free cash flow is negative"),
                       (thin, "liquidity is thin against debt due"), (no_path, "debt falls due with no clear refinancing path")):
        if flag:
            tier = max(tier, 2)
            reasons.append(text)
    if headroom == headroom:
        if headroom < 0:
            tier = 3
            reasons.append("covenant breached")
        elif headroom < HEADROOM_TIGHT:
            tier = max(tier, 2)
            reasons.append(f"covenant headroom {headroom:.0%}")
        elif headroom < HEADROOM_COMFORT:
            tier = max(tier, 1)
            reasons.append(f"covenant headroom {headroom:.0%}")
    if thin and no_path:
        tier = 3
    return {"watchlist_tier": TIERS[tier], "tier_n": tier, "reasons": reasons, "open": open_items}


# --------------------------------------------------------------------------- credit-memo-standards


MEMO_CHECKS = (
    ("Executive summary", "the business in one sentence, the opportunity, 2 to 3 reasons, 2 to 3 risks"),
    ("Capital structure", "each tranche with face, coupon, maturity; senior, total and net leverage; LTV"),
    ("Terms", "maintenance covenant levels and test dates; incurrence baskets; call terms"),
    ("Investment merits", "free cash flow generation and the base-case deleveraging path"),
    ("Key risks", "3 to 5 issuer-specific risks, each with a mitigant"),
    ("Historical financials", "at least 3 years, quarterly where available"),
    ("EBITDA adjustments", "reported-to-adjusted bridge with the load as a share of EBITDA and the 5% flag"),
    ("Model output", "base and downside: EBITDA, FCF, leverage path, covenant headroom, liquidity runway"),
)


def memo_checks(have: Mapping[str, bool]) -> list[dict[str, Any]]:
    """Structure checks of credit-memo-standards against what the process filled for this issuer.

    `have` maps each MEMO_CHECKS section to True when the process supplies every required item. Returns one row per
    section with "pass" or "open". Intuition: a memo with a hole in a required section is not ready for committee.
    """
    return [{"section": s, "requires": r, "status": "pass" if have.get(s) else "open"} for s, r in MEMO_CHECKS]
