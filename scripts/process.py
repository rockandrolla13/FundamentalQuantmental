"""Run the HY Analyst process step by step for each issuer (framework F1 order; methodology Sections 3 to 9).

    PYTHONPATH=. python3 scripts/process.py --tickers CRWV ORCL HCA THC CCL NCLH MGM WYNN

Order (framework R2): inputs -> frame (F2) -> normalise (F3) -> liquidity (F4) -> capital structure (F5) ->
clocks (4.7) -> cases under macro paths (F6, 5.4) -> valuation (F7) -> relative value (7.4) -> expected alpha (7.5)
-> gate (F9) -> events (F11) -> decision against cash -> combined view across the four groups -> memo (F12).

One analyst, four method groups. Every step carries the groups it serves:
  G1 core process: Gatto's seven steps, methodology.md, framework.md F1 to F13, the RV PDF additions
     (research/hyrv_mapping.md Top 10 items 1 to 4; conflicts C2, C3);
  G2 built methods: the two clocks, the fair line and pairs, the economic stories, cases and alpha, the F9 gate, F8;
  G3 credit skills: hy-model-standards and the six private-credit skills, applied where public filings allow;
  G4 books: Kricheff, and Ganguin and Bilardello (S&P).
Step and metric names follow research/combined_framework_spec.md.

Every step returns a status: "done", "partial", or "blocked". A blocked or partial step lists what is missing as
open questions; the memo prints them (F12: a field left empty is an open question, never dropped). Results go to
data/raw/process/<ticker>.json and the memos to docs/writeup/issuer_memos.tex/.pdf.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import clock_case  # noqa: E402
import rv_pair  # noqa: E402
import scenarios  # noqa: E402

from hy import alpha as hal  # noqa: E402
from hy import events as hev  # noqa: E402
from hy import books, fairspread, forward, groups, peers, recovery, rv, skills  # noqa: E402
from hy.sources import clock_inputs as ci  # noqa: E402
from hy.sources import compustat_pit as cp  # noqa: E402
from hy.sources import edgar  # noqa: E402
from hy.sources import forecast_sources as fs  # noqa: E402
from hy.sources import trace_bonds as tb  # noqa: E402
from hy.sources import treasury as tr  # noqa: E402

RAW = ROOT / "data" / "raw"
OUT = RAW / "process"
FIG = ROOT / "docs" / "writeup" / "figures"
TENOR = 5.0
# G1 v0 defaults (decision page 2026-10-22-four-group-combination): recovery per 1 of face (1 - V0 lgd), required
# return on a defaulted claim, years from default to distribution, and the ES budget for an admissible position.
G1_V0 = {"recovery": 1 - scenarios.V0["lgd"], "k_default": 0.15, "tau_default": 1.0, "es_budget": 0.25}  # spec S15: 0.25

# Framework F2 downside drivers by archetype (the "what breaks it" line).
F2_BREAKS = {
    "A1": "same-store sales and gross margin fall; working capital peaks before the season",
    "A2": "a reimbursement rule change, bad debt, or labour cost inflation",
    "A3": "the price deck and the decline rate",
    "A4": "volume falls with GDP on a high fixed cost base",
    "A5": "contracts roll off or churn; the asset value cycle turns",
    "A6": "net retention and bookings fall; cost cuts reverse",
    "A7": "an asset-specific shock or a block on distributions",
}


@dataclass
class Step:
    step: str
    section: str
    status: str = "done"
    outputs: dict = field(default_factory=dict)
    sources: dict = field(default_factory=dict)
    open_questions: list = field(default_factory=list)
    groups: list = field(default_factory=list)  # method groups the step serves (G1 to G4)


STEP_GROUPS = {  # research/combined_framework_spec.md, `groups` per step
    "1": ["G1", "G2", "G3"], "2": ["G1", "G3", "G4"], "3": ["G1", "G3", "G4"], "4": ["G1", "G2", "G3", "G4"],
    "5": ["G1", "G3", "G4"], "6": ["G2", "G4"], "7": ["G1", "G2", "G3", "G4"], "8": ["G1", "G3", "G4"],
    "9": ["G1", "G2", "G4"], "9b": ["G2"], "10": ["G1", "G2"], "11": ["G1", "G2", "G3"], "12": ["G1", "G3", "G4"],
    "13": ["G1", "G2", "G3", "G4"], "14": ["G1", "G2", "G3", "G4"], "14b": ["G1", "G2"], "15": ["G1"],
}


def _f(x, nd=2):
    return None if x is None or (isinstance(x, float) and x != x) else round(float(x), nd)


# ---------------------------------------------------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------------------------------------------------


def step_inputs(con, t, decision, start, end) -> tuple[Step, dict]:
    blk = rv_pair.issuer_block(con, t, decision, start, end)
    inputs = blk["inputs"]
    s = Step("1 Inputs", "Methodology 3; framework R5")
    s.outputs = {"filing": blk["filing"], "bonds_priced": int(len(blk["bonds"])), "curve_basis": blk["basis"],
                 "decision_time": str(decision.date())}
    s.sources = {k: v for k, v in ci.sources(inputs).items() if k in ("ltm_ebitda", "ltm_revenue", "interest_rate",
                                                                      "q", "k", "archetype")}
    if blk["bonds"].empty:
        s.status = "partial"
        s.open_questions.append("No priced bond in TRACE for this issuer: spreads and alpha cannot be read.")
    return s, blk


def business_text(inputs: dict) -> tuple[str, str]:
    """First two sentences of the 10-K business section, skipping the table of contents."""
    v = ci.values(inputs)
    acc = v.get("k") or v.get("q")
    txt = ci.filing_text(v["cik"], acc, RAW)
    for m in re.finditer(r"Item\s*1\.?\s*Business\.?", txt, re.I):
        body = re.sub(r"\s+", " ", txt[m.end(): m.end() + 3000])
        if "Item 1A" in body[:400] or re.search(r"\b\d{1,3} Item", body[:200]):
            continue  # table of contents
        body = re.sub(r"^(General|Overview|OVERVIEW|Our Company|Our Business)\s+", "", body.strip())
        sents = re.split(r"(?<=[.])\s+(?=[A-Z])", body)
        return " ".join(sents[:2])[:500], f"10-K {acc}, Item 1"
    return "", "not found"


def step_frame(blk) -> Step:
    inputs, case = blk["inputs"], blk["case"]
    s = Step("2 Frame the business", "Framework F2")
    arch = (inputs.get("archetype") or (None, ""))[0]
    if not arch:
        s.status = "blocked"
        s.open_questions.append("Assign the archetype (framework F2) in data/analyst_inputs/<ticker>.yaml.")
        return s
    sells, src = business_text(inputs)
    v = ci.values(inputs)
    rev, eb = v.get("ltm_revenue"), v.get("ltm_ebitda")
    rent = v.get("annual_lease_cost") or 0.0
    top = case["metrics"].get("cust_top1")
    mods = ["M3 concentration"] if top and top == top and top > 0.2 else []
    s.outputs = {
        "archetype": arch, "modifiers": mods,
        "sells": sells or None,
        "earns": f"revenue {rev / 1e3:,.1f}bn a year at a {eb / rev:.0%} EBITDA margin" if rev and eb else None,
        "rent_per_year_bn": _f(rent / 1e3, 2),
        "breaks": F2_BREAKS.get(arch, "") + (f"; the largest customer is {top:.0%} of revenue" if mods else ""),
    }
    s.sources = {"sells": src, "archetype": ci.sources(inputs).get("archetype", "")}
    s.status = "partial"
    s.open_questions.append("Market structure: number of players and price discipline (framework F2, line 4).")
    if not sells:
        s.open_questions.append("Business description not found in the 10-K text.")
    return s


def _eq_tests(quarters) -> tuple[dict, list]:
    """Framework F3 earnings-quality tests that the quarterly data supports: EQ1, EQ2, EQ5, EQ7."""
    q = sorted(quarters, key=lambda r: r.as_of)
    flags, notes = {}, []
    if len(q) >= 8:
        a, b = q[-4:], q[-8:-4]
        rev_a, rev_b = sum(r.revenue for r in a), sum(r.revenue for r in b)
        g = rev_a / rev_b - 1 if rev_b else np.nan

        def days(x, y):
            return (x / y * 91) if x == x and y and y == y else np.nan
        rd_a, rd_b = days(a[-1].receivables, a[-1].revenue), days(b[-1].receivables, b[-1].revenue)
        flags["EQ1 receivables"] = bool(rd_b and rd_a / rd_b - 1 > 0.10 and g < 0.05) if rd_a == rd_a and rd_b == rd_b else None
        iv_a, iv_b = days(a[-1].inventory, a[-1].cogs), days(b[-1].inventory, b[-1].cogs)
        flags["EQ2 inventory"] = bool(iv_b and iv_a / iv_b - 1 > 0.10 and g < 0) if iv_a == iv_a and iv_b == iv_b and iv_b > 0 else None

        def conv(w):
            e = sum(r.ebitda_adj_company for r in w if r.ebitda_adj_company == r.ebitda_adj_company)
            c = sum((r.operating_cash_flow - r.capex_total) for r in w
                    if r.operating_cash_flow == r.operating_cash_flow and r.capex_total == r.capex_total)
            return c / e if e else np.nan
        ca, cb = conv(a), conv(b)
        flags["EQ7 conversion"] = bool(ca < 0.3 and cb < 0.3) if ca == ca and cb == cb else None
        notes.append(f"cash conversion (CFO - capex) / EBITDA: last year {ca:.2f}, year before {cb:.2f}")
    if len(q) >= 20:
        years = {}
        for r in q[-20:]:
            years.setdefault(r.as_of.year, False)
            years[r.as_of.year] |= bool(r.nonrecurring_items)
        flags["EQ5 recurrence"] = sum(years.values()) >= 3
    return flags, notes


def _n(x) -> float:
    return float(x) if x is not None and x == x else float("nan")


def fill_cash_flow_gaps(quarters, cik, decision, n: int = 9) -> tuple[list, list]:
    """Fill NaN cash flows in the last `n` quarters from the first filing of each quarter (hy.sources.xbrl
    `cash_flow_from_filing`; methodology 3.2). Compustat de-cumulates year-to-date cash flows within one snapshot;
    when the predecessor quarter is missing there, the quarter comes back NaN (CCL Aug-2025, WYNN Jun-2026 on
    2026-09-18). Only filings accepted on or before `decision` are read. Returns the quarters and the filled list.
    Intuition: a missing quarter must not shrink the LTM to three quarters, nor blank the runway.
    """
    from dataclasses import replace as _replace

    from hy.sources import xbrl
    q = sorted(quarters, key=lambda r: r.as_of)
    gaps = [i for i in range(max(0, len(q) - n), len(q))
            if q[i].operating_cash_flow != q[i].operating_cash_flow or q[i].capex_total != q[i].capex_total]
    if not gaps or not cik:
        return q, []
    try:
        facts = xbrl.company_facts(cik, cache_root=RAW)
        idx = edgar.filing_index(cik, cache_root=RAW)
    except Exception:  # noqa: BLE001 - without EDGAR the gap stays NaN and the LTM stays NaN
        return q, []
    filled = []
    for i in gaps:
        cf = xbrl.cash_flow_from_filing(facts, idx, cik, pd.Timestamp(q[i].as_of), decision)
        if not cf:
            continue
        upd = {}
        for fld, attr in (("operating_cash_flow", "operating_cash_flow"), ("capex", "capex_total")):
            if getattr(q[i], attr) != getattr(q[i], attr) and cf[fld] == cf[fld]:
                upd[attr] = cf[fld]
        if q[i].cash_interest != q[i].cash_interest and cf["interest_paid"] == cf["interest_paid"]:
            upd["cash_interest"] = cf["interest_paid"]
        if q[i].cash_taxes != q[i].cash_taxes and cf["taxes_paid"] == cf["taxes_paid"]:
            upd["cash_taxes"] = cf["taxes_paid"]
        if upd:
            q[i] = _replace(q[i], **upd)
            filled.append(f"{q[i].as_of:%Y-%m-%d} from {cf['accession']}: {', '.join(upd)}")
    return q, filled


def ltm_figures(quarters) -> dict:
    """LTM flows and quarterly series from point-in-time quarters (methodology 3.2, 4.1, 4.2; quarterly-package-extraction).

    All quarters were available at the decision time (ci.loader_quarters filters on available_at). LTM = the last
    four consecutive quarters. dWC = (receivables + inventory - payables) now less four quarters earlier; NaN parts
    count as 0 with a flag. Intuition: one table of the numbers every group reads, so no group re-derives them.
    """
    q = sorted(quarters, key=lambda r: r.as_of)
    q4 = ci.last_four(q)
    out = {"quarters": len(q), "years_of_history": round(len(q) / 4, 1)}
    if not q4:
        return out

    def ssum(attr):
        vals = [_n(getattr(r, attr)) for r in q4]
        return float(sum(vals)) if all(v == v for v in vals) else float("nan")  # a missing quarter blanks the LTM

    def wc(r):
        return np.nansum([_n(r.receivables), _n(r.inventory)]) - np.nan_to_num(_n(r.payables))
    def esum(attr):
        """Earnings fields: with one quarter missing, 3 quarters x 4/3, the input layer's stated fallback
        (clock_inputs.ltm), so every group reads the same EBITDA; cash flows stay strict."""
        vals = [_n(getattr(r, attr)) for r in q4]
        ok = [v for v in vals if v == v]
        if len(ok) == 4:
            return float(sum(ok))
        if len(ok) == 3:
            out.setdefault("ltm_scaled", []).append(attr)
            return float(sum(ok)) * 4.0 / 3.0
        return float("nan")
    dwc = float(wc(q[-1]) - wc(q[-5])) if len(q) >= 5 else 0.0
    eb_adj = esum("ebitda_adj_company")
    out.update({
        "revenue": esum("revenue"), "ebitda_rep": esum("ebitda_reported"), "ebitda_adj": eb_adj,
        "addback": float(sum(i.amount for r in q4 for i in r.nonrecurring_items)),  # = -special items (a charge adds back)
        "cfo": ssum("operating_cash_flow"), "capex": ssum("capex_total"), "cash_interest": ssum("cash_interest"),
        "cash_taxes": ssum("cash_taxes"), "depreciation": ssum("depreciation"), "delta_wc": dwc,
        "delta_wc_flag": len(q) < 5, "cash": _n(q4[-1].cash),
        "maint_capex": float(sum(min(_n(r.capex_total), _n(r.depreciation)) if r.depreciation == r.depreciation
                                 else _n(r.capex_total) for r in q4)),
        "revenue_q": [_n(r.revenue) for r in q[-12:]], "ebitda_q": [_n(r.ebitda_adj_company) for r in q[-12:]],
        "ebitda_rep_q": [_n(r.ebitda_reported) for r in q[-12:]],
        "addback_q": [float(sum(i.amount for i in r.nonrecurring_items)) for r in q[-12:]],
        "cfo_q": [_n(r.operating_cash_flow) for r in q[-12:]], "capex_q": [_n(r.capex_total) for r in q[-12:]],
        "cogs_last": _n(q4[-1].cogs), "revenue_last": _n(q4[-1].revenue), "ebitda_last": _n(q4[-1].ebitda_adj_company),
    })
    out["fcf"] = out["cfo"] - out["capex"]
    out["margin_q"] = [e / r if r and r == r and e == e else float("nan") for e, r in zip(out["ebitda_q"], out["revenue_q"])]
    out["conversion_q"] = [(c - k) / e if e and e == e and c == c and k == k else float("nan")
                           for c, k, e in zip(out["cfo_q"], out["capex_q"], out["ebitda_q"])]
    return out


def ltm_ready(ltm: dict) -> bool:
    """True when ltm_figures found four consecutive quarters and an LTM EBITDA (not None, not NaN)."""
    x = ltm.get("ebitda_adj")
    return x is not None and x == x


def step_normalise(blk, decision) -> Step:
    s = Step("3 Normalise earnings", "Framework F3; methodology 4.1")
    v = ci.values(blk["inputs"])
    quarters, _ = ci.loader_quarters(v["ticker"], v.get("gvkey"), RAW, decision)
    quarters, filled = fill_cash_flow_gaps(quarters, v.get("cik"), decision)
    blk["_quarters"] = quarters
    ltm = blk["_ltm"] = ltm_figures(quarters)
    flags, notes = _eq_tests(quarters)
    q4 = ci.last_four(quarters)
    spi = -sum(i.amount for r in q4 for i in r.nonrecurring_items) if q4 else 0.0
    qs = sorted(quarters, key=lambda r: r.as_of)[-8:]
    mg = np.array([r.ebitda_adj_company / r.revenue if r.revenue and r.ebitda_adj_company == r.ebitda_adj_company
                   else np.nan for r in qs])
    ok = ~np.isnan(mg)
    trend = None
    if ok.sum() >= 6:
        x = np.arange(len(mg))[ok]
        b, a = np.polyfit(x, mg[ok], 1)
        res = mg[ok] - (a + b * x)
        se = np.sqrt((res ** 2).sum() / (len(x) - 2) / ((x - x.mean()) ** 2).sum())
        trend = float(b / se) if se > 0 else None  # F8 margin_trend: slope over its standard error
    fcf = sum((r.operating_cash_flow - r.capex_total) for r in q4
              if r.operating_cash_flow == r.operating_cash_flow and r.capex_total == r.capex_total) if q4 else np.nan
    eb = v.get("ltm_ebitda")
    debt = blk["risk"].extra["debt"]
    s.outputs = {"ebitda_ltm_m": _f(eb, 0), "special_items_ltm_m": _f(spi, 0), "margin_ltm": _f(eb / v["ltm_revenue"], 3)
                 if eb and v.get("ltm_revenue") else None, "margin_trend_t": _f(trend), "fcf_ltm_m": _f(fcf, 0),
                 "fcf_conversion": _f(fcf / eb) if eb else None, "fcf_to_debt": _f(fcf / debt) if debt else None,
                 "eq_flags": flags, "eq_score": int(sum(1 for f in flags.values() if f)), "notes": notes}
    # G3 ebitda-addback-treatment and hy-model-standards FCF check; G4 Kricheff ch. 9-10 cash-flow bridge.
    if ltm_ready(ltm):
        ab = skills.addback_bridge(ltm["ebitda_rep_q"], ltm["addback_q"], cash_share=0.0)
        chk = skills.fcf_check_gap(ltm["cfo"], ltm["capex"], ltm["ebitda_adj"], 0.0, ltm["cash_interest"],
                                   ltm["cash_taxes"], ltm["delta_wc"])
        kb = books.kricheff_bridge(ltm["ebitda_adj"], ltm["capex"], ltm["cash_interest"], ltm["cash_taxes"],
                                   ltm["delta_wc"], ltm["cfo"])
        s.outputs.update({
            "ebitda_rep_ltm_m": _f(ab["ebitda_rep_ltm"], 0), "ebitda_adj_ltm_m": _f(ltm["ebitda_adj"], 0),
            "addback_ltm_m": _f(ab["addback_ltm"], 0), "addback_category_share": _f(ab["addback_load"], 3),
            # spec S3: addback_gap = E_co / E_adj - 1, with the analyst rejecting a recurring add-back (E_adj = E_rep).
            "addback_gap": _f(ab["ebitda_adj_ltm"] / ab["ebitda_rep_ltm"] - 1, 3)
            if ab["addback_flags"]["recurring"] and ab["ebitda_rep_ltm"] else 0.0,
            "addback_flags": ab["addback_flags"], "addback_recurring_quarters": ab["recurring_quarters"],
            "fcf_if_addbacks_cash_m": _f(ltm["fcf"] - max(0.0, ab["cash_effect_if_all_cash"]), 0),
            "fcf_check_gap": _f(chk["fcf_check_gap"], 3), "fcf_check_flag": chk["fcf_check_flag"],
            "fcf_waterfall_m": _f(chk["fcf_waterfall"], 0), "fcf_ocf_route_m": _f(chk["fcf_ocf_route"], 0),
            "kricheff_bridge_m": {k: _f(v, 0) for k, v in kb.items()},
            "years_of_history": ltm["years_of_history"], "ltm_scaled_x4_3": ltm.get("ltm_scaled", []),
        })
        if chk["fcf_check_flag"]:
            s.outputs["eq_flags"]["FCF check (waterfall against OCF less capex)"] = True
            s.outputs["eq_score"] += 1
    s.sources = {"ebitda": ci.sources(blk["inputs"]).get("ltm_ebitda", ""), "special_items": "Compustat spiq (PIT)",
                 "addback_rule": "ebitda-addback-treatment skill", "bridge": "Kricheff ch. 9, 10"}
    if filled:
        s.sources["cash_flow_gap_fill"] = filled
    s.status = "partial"
    s.open_questions += [
        "Add-back table by class C1 to C10: read the company's adjusted EBITDA reconciliation (8-K exhibit 99); "
        "Compustat gives one special-items line, so the 5% test runs on the total.",
        "Cash share of the special items (decision page 2026-10-21-fcf-cash-nonrecurring sets 0 until read).",
        "Covenant EBITDA definition from the credit agreement (methodology 4.6).",
    ]
    return s


def fwd_tsy(path, q: int, tenor: float) -> float:
    """Treasury par yield for `tenor` at quarter q of a macro path: linear between the path's 2y and 10y points
    (scenarios.issuer_scenarios uses the same rule). Intuition: the rate the issuer refinances over, path by path."""
    i = min(max(q, 1), len(path.y2)) - 1
    y2, y10 = float(path.y2[i]), float(path.y10[i])
    return y2 + (y10 - y2) * (min(max(tenor, 2.0), 10.0) - 2.0) / 8.0


def funding_and_refi(blk, sc_out, info, start_, mac, s5) -> dict:
    """G1 additions to step 4 (research/hyrv_mapping.md Top 10 items 3 and 4; methodology 4.2, 5.4; framework F4).

    Funding gap G_h = C_0 + A_drawable - C_min + sum FCF_u - M_h per path, with no new financing: FCF from the
    case-weighted engine (maintenance capex only) and again with full capex (growth capex is a real use of cash
    unless separately financed); C_min = one month of cash operating cost, (revenue - EBITDA) / 3 of the last
    quarter (framework F4.4 default); M_h = debt lines due by quarter h (the filing's ladder, methodology 4.7).
    Refinancing shock dI = sum D_refi (c_new - c_old): D_refi = debt due inside 8 quarters; c_old = the mean TRACE
    coupon of bonds due inside 27 months, else the derived cash interest rate; c_new = the path's Treasury par yield
    for 5 years at the maturity quarter plus today's 5-year issuer spread. Probability-weighted across paths.
    """
    ltm = blk.get("_ltm", {})
    H = len(next(iter(sc_out["fcf_by_path"].values()))) if sc_out.get("fcf_by_path") else 8
    mat = np.zeros(H)
    for ln in start_.debt_lines:
        if ln.maturity_q and 1 <= ln.maturity_q <= H:
            mat[ln.maturity_q - 1] += ln.face
    rev_q, eb_q = ltm.get("revenue_last", np.nan), ltm.get("ebitda_last", np.nan)
    c_min = max(0.0, (rev_q - eb_q) / 3.0) if rev_q == rev_q and eb_q == eb_q else start_.min_cash
    growth_q = max(0.0, info["capex_total_q"] - info["capex_case_q"])
    debt0 = info["debt_total"]
    probs = {p.name: p.prob for p in mac.paths.paths}
    by_path, by_path_full = {}, {}
    for m, f in sc_out["fcf_by_path"].items():
        g = forward.funding_gap(start_.cash0, start_.revolver_commitment, c_min, f, mat, debt0=debt0)
        gf = forward.funding_gap(start_.cash0, start_.revolver_commitment, c_min, np.asarray(f) - growth_q, mat, debt0=debt0)
        by_path[m] = {"min": _f(g["funding_gap_min"], 0), "first_gap_q": g["first_gap_q"], "G": [_f(x, 0) for x in g["G"]]}
        by_path_full[m] = {"min": _f(gf["funding_gap_min"], 0), "first_gap_q": gf["first_gap_q"]}
    modal = sc_out["modal_path"]
    sev = sc_out.get("fcf_severe_by_path", {}).get(modal)
    gsev = forward.funding_gap(start_.cash0, start_.revolver_commitment, c_min, sev, mat, debt0=debt0) if sev else None
    # Spec K14: run the severe case again with committed (all) capex; quote the shorter runway.
    gsev_full = (forward.funding_gap(start_.cash0, start_.revolver_commitment, c_min, np.asarray(sev) - growth_q, mat,
                                     debt0=debt0) if sev else None)
    w_min = float(sum(probs[m] * by_path[m]["min"] for m in by_path))
    # Refinancing shock.
    bonds = blk["bonds"]
    near = bonds[bonds["maturity_years"] <= 2.25] if len(bonds) else bonds
    c_old = float(near["coupon"].mean()) if len(near) else float(info["rate"])
    c_old_src = "TRACE coupons of bonds due inside 27 months" if len(near) else "derived cash interest rate (LTM interest / debt)"
    lines = [ln for ln in start_.debt_lines if ln.maturity_q and ln.maturity_q <= H]
    shock = {}
    for p in mac.paths.paths:
        c_new = [fwd_tsy(p, ln.maturity_q, TENOR) + s5 for ln in lines]
        shock[p.name] = forward.refinancing_shock([ln.face for ln in lines], c_old, c_new, ltm.get("ebitda_adj", np.nan),
                                                  ltm.get("cash_interest", np.nan), ltm.get("capex", np.nan),
                                                  ltm.get("fcf", np.nan), debt0)
    wd = {k: float(sum(probs[m] * shock[m][k] for m in shock)) for k in next(iter(shock.values()))} if shock else {}
    return {
        "funding_gap_min": _f(by_path[modal]["min"], 0), "first_gap_q": by_path[modal]["first_gap_q"],
        "funding_gap_min_weighted_m": _f(w_min, 0), "funding_gap_min_full_capex_m": by_path_full[modal]["min"],
        "first_gap_q_full_capex": by_path_full[modal]["first_gap_q"],
        "funding_gap_min_severe_m": _f(gsev["funding_gap_min"], 0) if gsev else None,
        "first_gap_q_severe": gsev["first_gap_q"] if gsev else None,
        "runway_full_capex_q": (gsev_full["first_gap_q"] or "no gap in 8 quarters") if gsev_full else None,
        "funding_gap_by_path": by_path, "funding_gap_full_capex_by_path": by_path_full,
        "maturities_by_q_m": [_f(x, 0) for x in mat], "debt_due_12m_m": _f(float(mat[:4].sum()), 0), "c_min_m": _f(c_min, 0), "growth_capex_q_m": _f(growth_q, 0),
        "maturity_share_8q": _f(float(mat.sum()) / debt0, 3) if debt0 else None,
        "delta_I": _f(wd.get("delta_I"), 0), "delta_I_to_ebitda": _f(wd.get("delta_I_to_E"), 3),
        "cash_cov_after_refi": _f(wd.get("cash_cov_after")), "after_capex_cov_after_refi": _f(wd.get("after_capex_cov_after")),
        "fcf_after_refi_m": _f(wd.get("fcf_after"), 0), "fcf_after_refi_to_debt": _f(wd.get("fcf_after_to_debt"), 3),
        "refi_amount_8q_m": _f(sum(ln.face for ln in lines), 0), "c_old": _f(c_old, 4), "c_old_source": c_old_src,
        "delta_I_by_path_m": {m: _f(v["delta_I"], 0) for m, v in shock.items()},
    }


def runways(static_q: float | None, scen_q: int | None, full: dict | None) -> dict:
    """Runways side by side and the one to quote (spec S4 and K14; framework F4).

    static: liquidity / today's burn (FCF after all capex); severe, maintenance capex: the cases' first liquidity
    shortfall; severe, committed capex: the same case with all capex funded. Quote the shortest; no shortfall in 8
    quarters counts as 9. Intuition: the cases fund only maintenance capex, so their runway is the optimistic one.
    """
    full_q = (full or {}).get("first_shortfall_q")
    cands = {"static": static_q if static_q is not None and static_q != float("inf") else None,
             "severe, maintenance capex": scen_q, "severe, committed capex": full_q if full else None}
    have = {k: v for k, v in cands.items() if v is not None}
    worst = min(have, key=have.get) if have else None
    return {"runway_full_capex_scen_q": full_q if full_q else ("no shortfall in 8 quarters" if full else None),
            "liq_min_full_capex_m": _f((full or {}).get("liq_min"), 0),
            "runway_quoted_q": _f(have[worst], 1) if worst else "no shortfall in 8 quarters",
            "runway_quoted_basis": worst or "every run lasts 8 quarters"}


def step_liquidity(blk, sc_out, start_info, start_, mac=None, s5=None) -> Step:
    s = Step("4 Liquidity and the wall", "Framework F4")
    t = sc_out["table"].set_index("macro_path")
    pts = sc_out["refi_points"]
    stats = {c["case"]: c for c in sc_out["case_stats"]}
    cash = start_.cash0
    l_eff = cash + start_info["revolver_capacity"] - start_.min_cash  # F4 formula with no borrowing base data
    fcf_q = (blk["_fcf_ltm"] / 4.0) if blk.get("_fcf_ltm") == blk.get("_fcf_ltm") and blk.get("_fcf_ltm") is not None else np.nan
    runway_static = None if fcf_q != fcf_q else (float("inf") if fcf_q >= 0 else l_eff / -fcf_q)
    lad = blk["case"]["ladders"]["debt"] or []
    first = blk["case"]["ladders"]["debt_first_length"] or 1.0
    wall_18m, t_ = 0.0, 0.0
    for i, amt in enumerate(lad[:-1]):
        t_ += first if i == 0 else 1.0
        if t_ <= 1.5 + 1e-9:
            wall_18m += amt
    sev = stats.get("down_severe", {})
    s.outputs = {
        "cash_m": _f(cash, 0), "revolver_capacity_m": _f(start_info["revolver_capacity"], 0),
        "min_cash_m": _f(start_.min_cash, 0), "L_eff_m": _f(l_eff, 0),
        "runway_static_q": "no burn" if runway_static == float("inf") else _f(runway_static, 1),
        "runway_scen_q": sev.get("first_shortfall_q") or "no shortfall in 8 quarters",
        **runways(runway_static, sev.get("first_shortfall_q"), sc_out.get("severe_full_capex")),
        "wall_18m_m": _f(wall_18m, 0), "wall_cover_4_base": _f(stats.get("base", {}).get("wall_cover_4")),
        "debt_due_in_8q_m": _f(start_info["maturing_in_8q"], 0), "debt_total_m": _f(start_info["debt_total"], 0),
        "min_liquidity_severe_by_path_m": {m: _f(x, 0) for m, x in t["liq_min_down"].items()},
        "refi_score_by_path": sc_out["refi_score_by_path"],
        "refi_points_held": [k for k in ("rating_proxy", "recent_raise", "unencumbered", "sponsor") if pts.get(k)],
    }
    if mac is not None and sc_out.get("fcf_by_path"):
        s.outputs.update(funding_and_refi(blk, sc_out, start_info, start_, mac, s5))
        if not start_info["revolver_capacity"] and (s.outputs.get("funding_gap_min") or 0) < 0:
            s.open_questions.append("The funding gap opens only because no revolver capacity is tagged: read the "
                                    "credit facility note before using the gap.")
        s.sources["funding_gap"] = "RV PDF E75, E76 (mapping item 3); scenario engine FCF; filing debt ladder"
        s.sources["refinancing_shock"] = "RV PDF E77 (mapping item 4); path Treasury forwards plus today's spread"
    s.status = "partial"
    if not start_info["revolver_capacity"]:
        s.open_questions.append("Revolver commitment, draw, and borrowing base: not tagged; read the credit agreement note.")
    s.open_questions.append("F4 points 3 (unencumbered assets) and 6 (sponsor support) are scored 0 until read.")
    return s


def covenant_block(blk, liq: dict, ltm: dict) -> dict:
    """G3 covenant-compliance: levels parsed from the 10-Q, then the 10-K, debt note; headroom on our ratio.

    Headroom (methodology 4.6): leverage H = 1 - Lev / Lev_max, with net leverage when the covenant is a net test;
    coverage H = 1 - min / actual, with EBITDA / cash interest (debt service adds debt due in 12 months); liquidity
    H = 1 - min / L_eff. Our ratio uses analyst EBITDA, not covenant EBITDA, and the consolidated group; a covenant
    on a subsidiary group is flagged as a proxy. Intuition: the share by which the measure can worsen before a breach.
    """
    v = ci.values(blk["inputs"])
    found = {}
    for acc in (v.get("q"), v.get("k")):
        if not acc:
            continue
        try:
            txt = ci.filing_text(v["cik"], acc, RAW)
        except Exception:  # noqa: BLE001 - a missing text leaves the covenant an open question
            continue
        for c in skills.parse_covenants(txt):
            if c["kind"] not in found:
                found[c["kind"]] = {**c, "filing": acc}
    debt, cash = blk["risk"].extra["debt"], ltm.get("cash", np.nan)
    eb, ic = ltm.get("ebitda_adj", np.nan), ltm.get("cash_interest", np.nan)
    due_12m = liq.get("debt_due_12m_m") or 0.0
    rows = []
    for kind, c in found.items():
        name = c["name"].lower()
        if kind == "max_leverage":
            actual = (debt - (cash if "net" in name and cash == cash else 0.0)) / eb if eb else np.nan
            basis = "net debt / EBITDA" if "net" in name else "debt / EBITDA"
        elif kind == "min_coverage":
            den = ic + (due_12m if "debt service" in name else 0.0)
            actual = eb / den if den else np.nan
            basis = "EBITDA / (cash interest + debt due in 12 months)" if "debt service" in name else "EBITDA / cash interest"
        else:
            rev = liq.get("revolver_capacity_m") or 0.0
            actual = (cash if cash == cash else 0.0) + rev
            basis = "cash + unused lines (tagged)" if rev else "cash only (unused lines not tagged)"
        h = skills.covenant_headroom(kind, c["level"], actual)
        # Comparable only when our ratio measures what the test measures. A subsidiary test, a secured or first-lien
        # leverage test against our total debt, or a liquidity test below its level with untagged lines gives a
        # bound, not a reading: shown as a proxy, kept out of headroom_H and the watchlist (open question).
        narrower = kind == "max_leverage" and any(w in name for w in ("secured", "first lien", "senior"))
        lower_bound_fails = kind == "min_liquidity" and not liq.get("revolver_capacity_m") and h == h and h < 0
        comparable = not (c["subsidiary"] or narrower or lower_bound_fails)
        rows.append({"kind": kind, "name": c["name"], "level": _f(c["level"]), "actual": _f(actual), "basis": basis,
                     "headroom": _f(h, 3), "tier": skills.headroom_tier(h) if comparable else "proxy only (open)",
                     "comparable": comparable, "springing": c["springing"],
                     "subsidiary": c["subsidiary"], "filing": c["filing"], "evidence": c["evidence"][:220]})
    hs = [r["headroom"] for r in rows if r["headroom"] is not None and r["comparable"]]
    hmin = min(hs) if hs else None
    return {"covenants": rows, "headroom_H": hmin, "headroom_tier": skills.headroom_tier(hmin if hmin is not None else np.nan),
            "covenants_open": [r["name"] for r in rows if not r["comparable"]]}


def book_block(blk, ltm: dict, mcap: float, archetype: str, top_customer) -> dict:
    """G4 book methods per issuer: Kricheff's ratio set and snapshot (ch. 10, 24) and the S&P profile (ch. 2-5, 10).

    S&P: adjusted debt and EBITDA for leases (Appendix E), FFO = CFO + increase in working capital, FOCF = CFO - capex,
    the financial score against the 2002 CreditStats medians, the business score, and the default risk score with the
    Table 10-5 weights. Intuition: two textbook analysts read the same filing with their own checklists.
    """
    r = blk["risk"].extra
    debt, lease = r["debt"], r["lease_debt"]
    eb = ltm.get("ebitda_adj", np.nan)
    kr = books.kricheff_ratios(eb, ltm.get("capex", np.nan), ltm.get("maint_capex", np.nan), ltm.get("cash_interest", np.nan),
                               debt, ltm["cash"] if ltm.get("cash") is not None and ltm["cash"] == ltm["cash"] else 0.0,
                               ltm.get("fcf", np.nan), mcap)
    adj = books.sp_adjusted(debt, lease, eb, ltm.get("cash_interest", np.nan))
    ffo = ltm.get("cfo", np.nan) + ltm.get("delta_wc", 0.0)
    rat = books.sp_ratios(adj["debt_adj"], mcap, ffo, ltm.get("fcf", np.nan), adj["ebitda_adj"], adj["interest_adj"],
                          eb / ltm["revenue"] if ltm.get("revenue") else np.nan)
    fin = books.sp_financial_score(rat)
    rq = np.asarray(ltm.get("revenue_q", []), dtype=float)
    yoy = (rq[4:] / rq[:-4] - 1) if rq.size >= 8 else np.array([])
    yoy_sd = float(np.nanstd(yoy, ddof=1)) if yoy.size >= 3 else float("nan")
    bus = books.sp_business_score(archetype, yoy_sd, top_customer)
    drs = books.sp_default_risk_score(bus["business_risk_score"], fin["sp_financial_score"])
    return {"kricheff": {k: _f(v) for k, v in kr.items()},
            "sp": {"debt_adj_m": _f(adj["debt_adj"], 0), "implicit_lease_interest_m": _f(adj["implicit_interest"], 0),
                   "ffo_m": _f(ffo, 0), "ratios": {k: _f(v) for k, v in rat.items()},
                   "financial_parts": {k: _f(v) for k, v in fin["parts"].items()}, "sp_financial_score": _f(fin["sp_financial_score"]),
                   "business_parts": {k: _f(v) for k, v in bus["parts"].items()}, "business_risk_score": _f(bus["business_risk_score"]),
                   "revenue_yoy_sd": _f(yoy_sd, 3), "w_business": _f(drs["w_business"]),
                   "sp_default_risk_score": _f(drs["sp_default_risk_score"]), "sp_anchor_class": drs["sp_anchor_class"]}}


def step_capstructure(blk, liq: dict | None = None, mcap: float = float("nan"), archetype: str = "A4",
                      top_customer=None) -> Step:
    s = Step("5 Capital structure", "Framework F5; methodology 4.3")
    r = blk["risk"]
    bonds = blk["bonds"]
    rows = []
    for b in bonds.sort_values("maturity_years").to_dict("records"):
        rows.append({"cusip": b["cusip"], "coupon": _f(b["coupon"], 4), "maturity": str(pd.Timestamp(b["maturity"]).date()),
                     "price": _f(b["price"], 1), "yield": _f(b["yield"], 4), "spread_bp": _f(b["g_spread"] * 1e4, 0),
                     "seniority": b["seniority"]})
    v = ci.values(blk["inputs"])
    eb, rent = r.extra["ebitda_ltm"], r.extra["rent"] or 0.0
    intr = blk.get("_interest_ltm")
    capex, maint = blk.get("_capex_ltm"), blk.get("_maint_capex_ltm")
    cov = (eb - capex) / intr if eb and intr and capex is not None else None
    fccr = (eb + rent - maint) / (intr + rent) if eb and intr and maint is not None else None
    s.outputs = {"debt_m": _f(r.extra["debt"], 0), "lease_debt_m": _f(r.extra["lease_debt"], 0),
                 "ebitda_ltm_m": _f(eb, 0), "rent_m": _f(rent, 0), "lev_gc_total": _f(r.extra["debt"] / eb) if eb else None,
                 "lev_lease_adj": _f(r.lev_lease_adj), "net_lev": _f(r.extra["net_lev"]),
                 "coverage": _f(cov), "fccr": _f(fccr), "cash_interest_ltm_m": _f(intr, 0), "bonds": rows}
    ltm = blk.get("_ltm", {})
    if ltm_ready(ltm):
        bb = book_block(blk, ltm, mcap, archetype, top_customer)
        k = bb["kricheff"]
        s.outputs.update({"lev_gross": k["lev_gross"], "lev_net": k["lev_net"], "cash_cov": k["cash_cov"],
                          "after_capex_cov": k["after_capex_cov"], "fcf_to_debt": k["fcf_to_debt"],
                          "ffo_to_debt": bb["sp"]["ratios"]["ffo_to_debt"], "focf_to_debt": bb["sp"]["ratios"]["focf_to_debt"],
                          "kricheff": k, "sp": bb["sp"]})
        s.outputs.update(covenant_block(blk, liq or {}, ltm))
    s.sources = {"debt": r.extra["debt_source"], "bonds": "TRACE via WRDS, last 10 days",
                 "ratios": "Kricheff ch. 10; S&P ch. 5 and 10", "covenants": "10-Q then 10-K text (covenant-compliance skill)"}
    s.status = "partial"
    s.open_questions += ["Face amount of each tranche and the secured debt ahead of the bonds (debt note table).",
                         "Claims view: allowed claims by class and the entity map (framework F5)."]
    for nm_ in s.outputs.get("covenants_open", []):
        s.open_questions.append(f"Covenant '{nm_}': our ratio is only a bound for this test (subsidiary group, narrower "
                                "debt, or untagged credit lines); read the credit agreement definition.")
    if not s.outputs.get("covenants"):
        s.open_questions.append("Maintenance covenant levels: none stated in the 10-Q or 10-K text; read the credit "
                                "agreement exhibit (public bonds are often incurrence-only).")
    return s


def step_clocks(blk) -> Step:
    s = Step("6 Two clocks", "Methodology 4.7")
    case = blk["case"]
    m = case["metrics"]
    res = case["_res"]
    by_type = {k: _f(float(np.sum(v)) / 1e3, 1) for k, v in res.obligations.items()}
    rent = blk["risk"].extra["rent"] or 0.0
    ebitdar = (blk["risk"].extra["ebitda_ltm"] or 0.0) + rent
    tot = res.obligations_total
    s.outputs = {"fixed_charges_bn": _f(m["obligations_total"] / 1e3, 1), "by_type_bn": by_type,
                 "centre_years": _f(m["dur_obligations"], 1), "contract_clock": case["revenue_clock"][:80],
                 "years_of_ebitdar": _f(m["obligations_total"] / ebitdar, 1) if ebitdar else None,
                 "year1_share_of_ebitdar": _f(tot[0] / ebitdar) if ebitdar else None}
    if case["revenue_clock"] == "built":
        s.outputs.update({
            "rpo_bn": _f(case["rpo_total"] / 1e3, 1), "contract_centre_years": _f(m["dur_revenue"], 1),
            "duration_gap": _f(m["duration_gap"], 1), "runoff_years": _f(m["revenue_runoff"], 0),
            "breakeven_margin": _f(m["breakeven_margin"]), "company_margin": _f(m["ebitdar_margin"]),
            "coverage_contracted": _f(m["coverage_contracted"]),
            "renewal_dependent_share": _f(m["renewal_dependent_share"]),
            "renewal_dependent_bn": _f(m["renewal_dependent_amount"] / 1e3, 1),
            "renewal_refinance_bn": _f(m["renewal_refinance_amount"] / 1e3, 1),
            "renewal_recontract_bn": _f(m["renewal_recontract_amount"] / 1e3, 1),
            "renewal_refinance_share": _f(m["renewal_refinance_share"]),
            "renewal_recontract_share": _f(m["renewal_recontract_share"]),
            "renewal_revenue_years": _f(m["renewal_revenue_years"], 1),
            "largest_shortfall_bn": _f(m["max_cum_shortfall"] / 1e3, 1),
            "top3_customers": _f(m.get("cust_top3")),
            "scenarios": {k: {"coverage": _f(v["coverage_contracted"]), "shortfall_bn": _f(v["max_cum_shortfall"] / 1e3, 1)}
                          for k, v in case["scenarios"].items()},
            "margin_sensitivity": {k: _f(v) for k, v in case["sensitivity"].items() if k.startswith("margin")},
        })
    return s


def step_cases(sc_out) -> Step:
    s = Step("7 Cases under macro paths", "Framework F6; methodology 5.4")
    t = sc_out["table"]
    s.outputs = {"phase": sc_out["phase"], "archetype": sc_out["archetype"], "modal_path": sc_out["modal_path"],
                 "case_stats": sc_out["case_stats"], "promoted": sc_out["promoted"],
                 "by_path": t[["macro_path", "p_path", "lev_fwd_4", "lev_peak_down", "refi_fail_share", "pd_12m"]]
                 .round(3).to_dict("records")}
    s.status = "partial"
    s.open_questions.append("Consensus and management guidance (no licensed source): the base case is trailing growth.")
    return s


def market_value(con, gvkey: str, decision: pd.Timestamp) -> tuple[float, str]:
    """Equity value from Compustat: price x shares of the latest quarter reported on or before `decision` (F7.7)."""
    df = con.raw_sql(f"select datadate, rdq, prccq, cshoq from comp.fundq where gvkey = '{gvkey}' "
                     f"and rdq <= '{decision.date()}' and prccq is not null order by datadate desc limit 1")
    if df.empty:
        return float("nan"), "no Compustat price"
    r = df.iloc[0]
    return float(r["prccq"] * r["cshoq"]), f"Compustat fundq {r['datadate']} (reported {r['rdq']})"


def step_valuation(con, blk, decision, mcap_src: tuple | None = None) -> Step:
    s = Step("8 Valuation", "Framework F7")
    r = blk["risk"]
    v = ci.values(blk["inputs"])
    mcap, src = mcap_src if mcap_src else market_value(con, v["gvkey"], decision)
    tev = mcap + r.extra["debt"] - (r.extra["cash"] if r.extra["cash"] == r.extra["cash"] else 0.0)
    eb = r.extra["ebitda_ltm"]
    s.outputs = {"market_cap_bn": _f(mcap / 1e3, 1), "market_tev_bn": _f(tev / 1e3, 1),
                 "tev_to_ebitda": _f(tev / eb, 1) if eb else None, "debt_to_market_tev": _f(r.extra["debt"] / tev)}
    s.sources = {"market_cap": src}
    s.status = "partial"
    s.open_questions += ["Peer set of at least four issuers of the same archetype (F3.3) for the valuation range (F7.1).",
                         "Distressed multiple (F7.3) and the recovery of the bonds if the company defaults (F7.9)."]
    return s


def step_rv(t, xs, s_index: float, lev_gross=None) -> Step:
    """Step 9: the bond against its sector peers and the HY index (methodology 7.2, 7.4; decision page
    2026-10-23-peer-fair-spread). z_rv = log(s / fair) / the peers' robust sd of log spread."""
    s = Step("9 Relative value", "Methodology 7.4")
    row = xs.loc[t]
    nz = row["noise_log"]
    s.outputs = {"spread_5y_bp": _f(row["s5"] * 1e4, 0), "fair_5y_bp": _f(row["fair_s5"] * 1e4, 0),
                 "cheap_by_bp": _f((row["s5"] - row["fair_s5"]) * 1e4, 0), "lev_lease_adj": _f(row["lev"]),
                 "z_rv": _f(row["resid_log"] / nz) if nz == nz and nz > 0 else None,
                 "hy_index_bp": _f(s_index * 1e4, 0), "vs_index_bp": _f((row["s5"] - s_index) * 1e4, 0),
                 "dts_beta": _f(fairspread.dts_beta(row["s5"], s_index)),
                 "spt_total": _f(books.spread_per_turn_bp(row["s5"] * 1e4, lev_gross), 1) if lev_gross else None,
                 "fair_basis": row["fair_basis"],
                 "fair_line": ("median 5-year spread of sector x rating x maturity peers on the TRACE panel"
                               if row["fair_basis"] == "sector peers" else "HY index spread (no peer cell)")}
    s.status = "partial"
    s.open_questions.append("Rating-index and sector-index spreads (F12 full memo, section 9): no licensed source.")
    return s


GICS_SECTORS = {"10": "Energy", "15": "Materials", "20": "Industrials", "25": "Consumer Discretionary",
                "30": "Consumer Staples", "35": "Health Care", "40": "Financials", "45": "Information Technology",
                "50": "Communication Services", "55": "Utilities", "60": "Real Estate"}


def peer_table(blocks: dict, xs, decision: pd.Timestamp) -> pd.DataFrame | None:
    """Peers for the run's issuers: ESP, spread per turn, SPiDER and OneScore by sector, by rating, and by both
    (hy.peers; decision pages 2026-10-22-esp-peer-groups, 2026-10-23-peer-fair-spread). Peers are the TRACE high yield
    panel's bonds in the latest month at or before `decision`. Each issuer enters as its 5-year point with the panel's
    own leverage (Compustat debt / LTM EBITDA, point in time), so it joins the cell by the same rule as its peers.
    Returns None when the panel files are missing; the fair spread then falls back to the HY index."""
    bt_dir = RAW / "backtest"
    need = ["panel_full.parquet", "leverage_full.parquet", "gics_history.parquet", "sp_ratings.parquet"]
    if not all((bt_dir / f).exists() for f in need):
        return None
    lev = pd.read_parquet(bt_dir / "leverage_full.parquet")
    lev["gvkey"] = lev["gvkey"].astype(str)
    known = lev[(lev["date"] <= decision) & (lev["available_at"] <= decision)].sort_values("date")
    last = known.groupby("gvkey").tail(1).set_index("gvkey")
    rows = []
    for t in blocks:
        gv = ci.values(blocks[t]["inputs"]).get("gvkey")
        if t not in xs.index or not gv:
            continue
        r = last.loc[str(gv)] if str(gv) in last.index else None
        rows.append({"ticker": t, "gvkey": str(gv), "spread": float(xs.loc[t, "s5"]),
                     "leverage": float(r["leverage"]) if r is not None else np.nan,
                     "ebitda_pos": bool(r is not None and float(r["ltm_ebitda"]) > 0),
                     "debt": float(r["debt"]) if r is not None else np.nan})
    if not rows:
        return None
    return peers.live_peers(pd.DataFrame(rows),
                            pd.read_parquet(bt_dir / "panel_full.parquet", columns=["date", "gvkey", "years", "g_spread"]),
                            lev, pd.read_parquet(bt_dir / "gics_history.parquet"),
                            pd.read_parquet(bt_dir / "sp_ratings.parquet"), decision,
                            annual=pd.read_parquet(bt_dir / "annual_ebitda.parquet")
                            if (bt_dir / "annual_ebitda.parquet").exists() else None,
                            equity=pd.read_parquet(bt_dir / "equity_monthly.parquet")
                            if (bt_dir / "equity_monthly.parquet").exists() else None)


def add_peers(steps_all: dict, res: pd.DataFrame | None) -> None:
    """Step 9 peer block from `peer_table`. Values are log differences: +0.20 means the issuer pays about 22% more
    than the peer median."""
    if res is None:
        return
    for t, r in res.iterrows():
        if t not in steps_all or "9" not in steps_all[t]:
            continue
        o = steps_all[t]["9"].outputs
        o["peers"] = {
            "sector": GICS_SECTORS.get(str(r["sector"]), str(r["sector"])), "rating_class": r["rclass"],
            "rating_source": r["rclass_source"], "peer_month": res.attrs["peer_month"],
            "n_panel_bonds": res.attrs["n_peer_bonds"],
            "implied_cutoffs_x": {k: round(v, 2) for k, v in res.attrs["cutoffs"].items()},
            **{f"esp_{k}": _f(r[f"esp_{k}"], 3) for k in ("sr", "s", "r")},
            **{f"e13_{k}": _f(r[f"e13_{k}"], 3) for k in ("sr", "s", "r")},
            **{f"esp_lev_{k}": _f(r.get(f"esp_lev_{k}"), 3) for k in ("sr", "s", "r")},
            "spider": _f(r.get("spider"), 3), "spider_sr": _f(r.get("spider_sr"), 3),
            "spider_pct": _f(r.get("spider_pct"), 3),
            "emc_3m": _f(r.get("emc"), 3), "emc_sec": _f(r.get("emc_sec"), 3), "esp_sec": _f(r.get("esp_sec"), 3),
            "onescore": _f(r.get("onescore"), 3),
            "spider_note": None if r.get("spider") == r.get("spider") else
            "No SPiDER: fewer than 6 annual EBITDA figures, a financial issuer, or non-positive sustainable EBITDA.",
            "cell_esp_sr": r["cell_esp_sr"], "cell_e13_sr": r["cell_e13_sr"],
            "peer_sd_log": _f(r.get("esp_sd_sr"), 3), "n_peers": int(r.get("esp_n_sr") or 0)}
        steps_all[t]["9"].open_questions = [q for q in steps_all[t]["9"].open_questions if "Rating-index" not in q]
        steps_all[t]["9"].open_questions.append(
            "Peer rating class is implied by leverage: no rating source after February 2017 (decision page "
            "2026-10-22-esp-peer-groups). The analyst may enter the actual rating.")


def step_pair(t, pairs_out: list) -> Step:
    s = Step("9b Pair comparison", "Methodology 7.4, 7.5; framework F10 S4")
    mine = [p for p in pairs_out if t in (p["a"], p["b"])]
    if not mine:
        s.status = "blocked"
        s.open_questions.append("No pair partner in this run.")
        return s
    s.outputs = {"pairs": mine}
    return s


F8_BANDS = {  # metric: (better, green threshold, red threshold) from framework F8
    "coverage": ("high", 2.0, 1.25), "fccr": ("high", 1.5, 1.1), "fcf_conversion": ("high", 0.30, 0.10),
    "fcf_to_debt": ("high", 0.10, 0.03), "wall_cover_4_base": ("high", 1.5, 1.0), "refi_score_now": ("high", 4, 1.5),
    "eq_score": ("low", 0.5, 2.5), "w_down": ("low", 0.25, 0.5), "p_refi_4": ("low", 0.05, 0.20),
    "p_liq_short_8": ("low", 0.05, 0.20), "margin_trend_t": ("high", 1.0, -1.0),
}


def step_metrics(st: dict, sc_out) -> Step:
    """Framework F8 panel: each metric with its default band, red items first."""
    s = Step("13 Metrics panel", "Framework F8")
    w = sc_out["weighted"]
    vals = {
        "coverage": st["5"].outputs.get("coverage"), "fccr": st["5"].outputs.get("fccr"),
        "fcf_conversion": st["3"].outputs.get("fcf_conversion"), "fcf_to_debt": st["3"].outputs.get("fcf_to_debt"),
        "wall_cover_4_base": st["4"].outputs.get("wall_cover_4_base"),
        "refi_score_now": sc_out["refi_score_by_path"].get(sc_out["modal_path"]),
        "eq_score": st["3"].outputs.get("eq_score"), "margin_trend_t": st["3"].outputs.get("margin_trend_t"),
        "w_down": _f(sum(v for k, v in sc_out["case_weights"][sc_out["modal_path"]].items() if k.startswith("down"))),
        "p_refi_4": _f(w.get("p_refi_4")) if w is not None else None,
        "p_liq_short_8": _f(w.get("p_liq_short_8")) if w is not None else None,
    }
    rows = []
    for k, v in vals.items():
        better, g, r = F8_BANDS[k]
        if v is None or v != v:
            band = "n/a"
        elif better == "high":
            band = "green" if v > g else ("red" if v < r else "amber")
        else:
            band = "green" if v < g else ("red" if v > r else "amber")
        rows.append({"metric": k, "value": v, "band": band})
    order = {"red": 0, "amber": 1, "green": 2, "n/a": 3}
    s.outputs = {"panel": sorted(rows, key=lambda x: order[x["band"]])}
    return s


def _o(st: dict, k: str) -> dict:
    v = st.get(k)
    return v.outputs if v is not None else {}


def group_estimates(steps_all: dict, scen: dict, xs, s_index: float) -> tuple[dict, dict, float]:
    """Estimates E0 to E16 per issuer in bp a year before cost (research/combined_framework_spec.md S14; hy.groups).

    alpha type: E0 spread level (s5 - S_index) x 1e4 with beta = 1 (spec K15); E1 scenario-weighted alpha; E2 fair-line
    convergence D (1 - rho^(4h)) (s - s_fair) / h; E3 pair convergence signed by the leg; E4 the spread-implied PD
    gap x l_def (weight 0 until kappa_t is fitted, mapping C2); E10 excess over cash mu_excess / H (step 15).
    score type (standardised across the run, x sd(E1)): E5 -years of EBITDAR in fixed bills; E6 (greens - reds) /
    bands; E8 refinance score (likely story) + min(wall cover, 3) + 1{funding_gap_min >= 0}; E9 -debt / market TEV;
    E12 z(log s5) - z(S&P default risk score), positive = the spread is wide for the score; E13 spread per turn against
    peers of the same GICS sector and rating class (hy.peers, ESP style; log SPT minus the peer median), falling back to
    the run-wide spread per turn when no peer value exists; 0 when books.spt_trap_guard calls a trap (Kricheff
    p. 124: FCF / debt <= 0 or TEV / debt <= 1, or two of high leverage, low FCF / debt and a thin cushion); E14 ESP against sector and rating peers (log spread minus the peer median); E15 SPiDER, log spread /
    (debt / 10-year mean EBITDA), absolute across sectors (Dynkin et al. 2021, ch. 13 and 14; NaN without 6 annual
    EBITDA figures); E16 OneScore, the mean of the within-sector ranks of ESP and the 3-month stock return
    (Dynkin et al. ch. 19; NaN for an unlisted issuer).
    one_way type (scaled, then min(0, x)): E7 -(earnings-quality flags + add-back flags + FCF check flag); E11
    -(watch tier) - 1{headroom falling} (headroom history not stored yet: the second term is 0).
    Intuition: each estimate is one witness; pricing witnesses speak in bp, score witnesses rank the issuers.
    """
    h, rho = scenarios.V0["h_years"], scenarios.V0["rho_q"]
    lgd = scenarios.V0["lgd"]
    tick = [t for t in steps_all if t in scen]
    raw = {t: {} for t in tick}
    score = {t: {} for t in tick}
    for t in tick:
        st, sc = steps_all[t], scen[t]
        s5, sf = float(xs.loc[t, "s5"]), float(xs.loc[t, "fair_s5"])
        d5 = rv.modified_duration(0.04 + s5, 0.04 + s5, TENOR)
        raw[t]["E0"] = (s5 - s_index) * 1e4
        raw[t]["E1"] = sc["alpha"]["alpha_w"] / h * 1e4
        raw[t]["E2"] = groups.convergence_alpha_bp(s5 - sf, d5, rho, h)
        for p in _o(st, "9b").get("pairs", []):
            a = p["alpha"]
            v = a.get("alpha_convergence_bp_price")
            if v is not None and v == v:
                raw[t]["E3"] = (v if a["long"] == t else -v) / h
        g0 = _o(st, "11").get("table", [{}])[0]
        if g0.get("gap") is not None:
            raw[t]["E4"] = -g0["gap"] * (_o(st, "10").get("l_def") or lgd) * 1e4
        mu = _o(st, "15").get("mu_excess_bp_yr")
        if mu is not None:
            raw[t]["E10"] = mu
        lq, cs, nm, ev = _o(st, "4"), _o(st, "5"), _o(st, "3"), _o(st, "12")
        score[t]["E5"] = -(_o(st, "6").get("years_of_ebitdar") or np.nan)
        bands = [r["band"] for r in _o(st, "13").get("panel", []) if r["band"] != "n/a"]
        score[t]["E6"] = (bands.count("green") - bands.count("red")) / len(bands) if bands else np.nan
        eqf = {k: v for k, v in (nm.get("eq_flags") or {}).items() if not k.startswith("FCF check")}
        score[t]["E7"] = -float(sum(1 for v in eqf.values() if v) + sum(1 for v in (nm.get("addback_flags") or {}).values() if v)
                                + int(bool(nm.get("fcf_check_flag"))))
        ref = lq.get("refi_score_by_path", {}).get(sc["modal_path"])
        wc = lq.get("wall_cover_4_base")
        fg = lq.get("funding_gap_min")
        untagged = not lq.get("revolver_capacity_m") and fg is not None and fg < 0  # gap rests on missing data
        score[t]["E8"] = ((ref if ref is not None else np.nan) + (min(wc, 3.0) if wc else 0.0)
                          + (1.0 if fg is not None and fg >= 0 and not untagged else 0.0))
        ltv = _o(st, "8").get("debt_to_market_tev")
        score[t]["E9"] = -ltv if ltv is not None else np.nan
        tn = ev.get("watch_tier_n")
        score[t]["E11"] = -float(tn) if tn is not None else np.nan
        score[t]["_drs"] = cs.get("sp", {}).get("sp_default_risk_score")
        score[t]["_spt"] = _o(st, "9").get("spt_total")
        pe9 = _o(st, "9").get("peers") or {}
        score[t]["_spt_peer"] = pe9.get("e13_sr")
        score[t]["E14"] = pe9["esp_sr"] if pe9.get("esp_sr") is not None else np.nan
        score[t]["E15"] = pe9["spider"] if pe9.get("spider") is not None else np.nan
        score[t]["E16"] = pe9["onescore"] if pe9.get("onescore") is not None else np.nan
        k = cs.get("kricheff", {})
        score[t]["_trap_in"] = (k.get("lev_gross"), k.get("fcf_to_debt"), (1.0 / ltv) if ltv else None)
    lev_run = [score[t]["_trap_in"][0] for t in tick]
    fcf_run = [score[t]["_trap_in"][1] for t in tick]
    for t in tick:  # Kricheff's trap guard (p. 124) needs the run's leverage and FCF / debt as peers
        score[t]["_trap"] = books.spt_trap_guard(*score[t]["_trap_in"], lev_run, fcf_run)
        score[t]["_spt_ok"] = not score[t]["_trap"]["trap"]
    sd1 = float(np.nanstd([raw[t]["E1"] for t in tick], ddof=1)) if len(tick) > 2 else 1.0
    zs = groups.zscore({t: float(np.log(xs.loc[t, "s5"])) for t in tick})
    zd = groups.zscore({t: score[t]["_drs"] if score[t]["_drs"] is not None else np.nan for t in tick})
    zp = groups.zscore({t: score[t]["_spt"] if score[t]["_spt"] is not None else np.nan for t in tick})
    for t in tick:
        score[t]["E12"] = zs[t] - zd[t] if zs[t] == zs[t] and zd[t] == zd[t] else np.nan
        pe = score[t]["_spt_peer"]
        e13 = pe if pe is not None and pe == pe else zp[t]
        # Guarded-out issuers stay out of the standardisation and get exactly 0 after it (below): a raw 0 would
        # standardise to a credit whenever the run's mean is negative.
        score[t]["E13"] = e13 if score[t]["_spt_ok"] else np.nan
    for k in ("E5", "E6", "E7", "E8", "E9", "E11", "E12", "E13", "E14", "E15", "E16"):
        sc_ = groups.scale_scores({t: score[t][k] for t in tick}, sd1)
        for t in tick:
            v = sc_[t]
            if groups.ESTIMATES[k][2] == "one_way":
                v = groups.one_way(v)
            if k == "E13" and not score[t]["_spt_ok"]:
                v = 0.0
            if v == v:
                raw[t][k] = v
    for t in tick:  # an unlisted issuer has no OneScore: ESP stands in, so ESP carries E16's share too
        if "E16" not in raw[t] and "E14" in raw[t]:
            raw[t]["E16"] = raw[t]["E14"]
    return raw, {"sd_anchor": sd1, "spt_median_bp": float(np.nanmedian([score[t]["_spt"] for t in tick
                                                                          if score[t]["_spt"] is not None]))
                 if tick else None, "s_index_bp": s_index * 1e4}, h


def combined_view(steps_all: dict, scen: dict, xs, s_index: float) -> dict:
    """One analyst across the four groups: group alphas, verdicts, and the combined alpha set against the
    scenario-weighted alpha (methodology 7.5, 8; framework F10, F12.1; spec S14; hy.groups.combine).

    Ranks: by the combined alpha after cost (spec: raw alpha sets the rank), and by each group's alpha. Then the
    decision against cash across the run: opportunity cost and the best admissible alternative (spec S15; F1 R8).
    """
    raw, meta, h = group_estimates(steps_all, scen, xs, s_index)
    out = {}
    for t in raw:
        cost = scen[t]["alpha"]["cost"] / h * 1e4
        res = groups.combine(raw[t], cost, raw[t]["E1"])
        for g, v in res["groups"].items():
            v["verdict"] = groups.verdict(v["alpha_bp_yr"], cost, v["one_way_only"])
        rows = [{"estimate": k, "name": groups.ESTIMATES[k][1], "group": groups.ESTIMATES[k][0], "type": groups.ESTIMATES[k][2],
                 "alpha_bp_yr": raw[t][k], "w_v0": groups.ESTIMATES[k][3]} for k in groups.ESTIMATES if k in raw[t]]
        gate = _o(steps_all[t], "11")
        out[t] = {**res, "rows": rows, "group_weights": groups.GROUP_WEIGHTS,
                  "gate_pass": bool(gate.get("G1") and gate.get("G3") and gate.get("G6")), **meta}
    for t, i in groups.rank({t: out[t]["combined_after_cost"] for t in out}).items():
        out[t]["rank"] = i
    for g in groups.GROUP_NAMES:
        for t, i in groups.rank({t: out[t]["groups"][g]["alpha_bp_yr"] for t in out}).items():
            out[t]["groups"][g]["rank"] = i
    mu = {t: _o(steps_all[t], "15").get("mu_excess") for t in out}
    es = {t: _o(steps_all[t], "15").get("es95") for t in out}
    mu = {t: v for t, v in mu.items() if v is not None}
    oc = hal.opportunity_cost(mu, {t: v for t, v in es.items() if v is not None}, G1_V0["es_budget"])
    for t, v in oc.items():
        out[t]["decision"] = {**v, "opportunity_cost_bp_yr": _f(v["opportunity_cost"] / h * 1e4, 0)}
    return out


def memo_have(st: dict) -> dict:
    """What the process fills for each credit-memo-standards section (hy.skills.MEMO_CHECKS), from the step outputs.

    Capital structure needs face by tranche and Terms needs covenant levels plus call terms, which public data gives
    only in part; EBITDA adjustments need the category table, which Compustat does not give. Intuition: a section
    passes only when every item it requires is filled from data, not from an open question.
    """
    fr, nm, cs, cases = _o(st, "2"), _o(st, "3"), _o(st, "5"), _o(st, "7")
    panel = _o(st, "13").get("panel", [])
    base = [c for c in cases.get("case_stats", []) if c["case"] == "base"]
    down = [c for c in cases.get("case_stats", []) if c["case"].startswith("down")]
    return {
        "Executive summary": bool(fr.get("sells") and _o(st, "11").get("call")),
        "Capital structure": False,  # face by tranche is open (TRACE has no amount outstanding)
        "Terms": False,  # call schedules and incurrence baskets are open
        "Investment merits": bool(nm.get("fcf_ltm_m") is not None and base),
        "Key risks": sum(1 for r in panel if r["band"] in ("red", "amber")) >= 3,
        "Historical financials": (nm.get("years_of_history") or 0) >= 3,
        "EBITDA adjustments": False,  # one special-items total, no category table
        "Model output": bool(base and down and cs.get("headroom_H") is not None),
    }


BACKTEST = RAW / "backtest"


def measured_slope(predictor: str = "fair_line_net", horizon: str = "6") -> dict:
    """Mincer-Zarnowitz slope of realised on predicted alpha from the finished backtest (read only; decision page
    2026-10-22-alpha-backtest-design). Full sample 2008-2026 is the calibration; the 2019-2026 pilot is shown as the
    range. Falls back to the spec S14b v0 (a = 0, b = 0.08) when the file is missing.
    """
    out = {"a": groups.SIZED_V0[0], "b": groups.SIZED_V0[1], "se_b": None, "b_pilot": None,
           "source": "spec S14b v0 (backtest summary not found)", "predictor": predictor, "horizon_months": int(horizon)}
    try:
        full = json.loads((BACKTEST / "summary_full.json").read_text())
        mz = full["results"][horizon]["predictors"][predictor]["mz"]
        out.update({"b": float(mz["b"]), "se_b": float(mz["se_b"]),
                    "source": f"data/raw/backtest/summary_full.json ({full['start']} to {full['end']}), {predictor}, "
                              f"{horizon}-month horizon; decision page 2026-10-22-alpha-backtest-design"})
        pil = json.loads((BACKTEST / "summary_pilot.json").read_text())
        out["b_pilot"] = float(pil["results"][horizon]["predictors"][predictor]["mz"]["b"])
    except (OSError, KeyError, ValueError):
        pass
    return out


def step_size_calibration(t, comb: dict, slope: dict) -> Step:
    """Spec S14b: alpha_sized = b x alpha_net, b = the backtest's Mincer-Zarnowitz slope (a held at 0; the
    team-lead instruction is to multiply by the measured slope). Spec rule: if b is not above 0 by 2 standard errors,
    the number ranks issuers but sizes nothing beyond the minimum. Raw alpha sets the rank; the calibrated one feeds
    size. Intuition: the model ranks bonds well but predicts moves about twelve times too large.
    """
    s = Step("14b Size calibration", "Spec S14b; methodology 7.5; decision page 2026-10-22-alpha-backtest-design")
    c = comb.get(t)
    if not c:
        s.status = "blocked"
        return s
    b, se = slope["b"], slope["se_b"]
    sig = bool(se and b > 2 * se)
    s.outputs = {"mz_b": _f(b, 3), "mz_se_b": _f(se, 3), "mz_b_pilot": _f(slope["b_pilot"], 3), "source": slope["source"],
                 "alpha_raw_after_cost": _f(c["combined_after_cost"], 0),
                 "alpha_sized": _f(b * c["combined_after_cost"], 0),
                 "alpha_sized_pilot": _f(slope["b_pilot"] * c["combined_after_cost"], 0) if slope["b_pilot"] else None,
                 "anchor_sized": _f(b * c["anchor_after_cost"], 0),
                 "slope_significant": sig, "use": "size" if sig else "rank only, minimum size",
                 "calibrated": False, "loss_term_in_backtest": False}
    s.status = "partial"
    s.open_questions.append("Alpha sizes are uncalibrated: the backtest slope is far below 1 and the panel has no "
                            "default-loss term; recalibrate once the loss term is on.")
    return s


def step_combined(t, comb: dict) -> Step:
    s = Step("14 Combined view", "Methodology 8 (composite); framework F10, F12.1; four groups")
    c = comb.get(t)
    if not c:
        s.status = "blocked"
        s.open_questions.append("No estimates to combine.")
        return s
    s.outputs = c
    s.status = "partial"
    s.open_questions.append("Group and estimate weights are v0; replace them by each estimate's trailing rank IC (backtest).")
    return s


def step_alpha(sc_out, ref: dict | None = None) -> Step:
    s = Step("10 Expected alpha", "Methodology 7.5")
    a = sc_out["alpha"]
    t = sc_out["table"]
    s.outputs = {"l_def": _f((ref or {}).get("l_def"), 3), "lgd_face_v0": scenarios.V0["lgd"],
                 "jtd_per_mm": _f(1e6 * ((ref or {}).get("dirty_price", np.nan) / 100 - G1_V0["recovery"]), 0) if ref else None,
                 "info_ratio": _f(a.get("info_ratio")),
                 "reference_bond": {k: (ref or {}).get(k) for k in ("cusip", "coupon", "maturity", "price", "dirty_price")},
                 "weighted_bp_year_before_cost": _f(a["alpha_w"] / 0.5 * 1e4, 0),
                 "weighted_bp_year_after_cost": _f(a["alpha_net_bp_ann"], 0),
                 "by_path_bp_year": {m: _f(x / 0.5 * 1e4, 0) for m, x in zip(t["macro_path"], t["alpha"])},
                 "passes_cost_test": a["passes_g3"]}
    s.status = "partial"
    s.open_questions.append("Alpha rests on v0 rules (decision page issuer-scenario-defaults); the backtest decides them.")
    return s


def step_gate(t, steps: dict, xs, sc_out, ref: dict | None = None) -> Step:
    """Framework F9: what the price implies against our view, row by row; then the gate rules G1, G2, G3, G6.

    Mapping C2: the spread-to-PD row (1 - exp(-s / (kappa LGD)) at a fixed v0 kappa) is not a physical PD, so it is
    shown, renamed, and kept out of G1 and G6 until kappa is fitted by rating bucket and date. The market-implied
    default row in the gate is the breakeven default rate instead: the yearly default rate at which the bond's spread
    only pays for its default loss on the purchase price, be = s / L_def (mapping C3: L_def on price, with recovery
    discounted for delay). It is a hurdle the price sets, not a PD; our PD below it votes "cheap".
    """
    s = Step("11 Gate: price against view", "Framework F9")
    k, lgd = scenarios.V0["kappa"], scenarios.V0["lgd"]
    row = xs.loc[t]
    implied_pd = 1 - np.exp(-row["s5"] / (k * lgd))
    tab = sc_out["table"]
    view_pd = float((tab["p_path"] * tab["pd_12m"]).sum())
    nz = float(row["noise_log"])  # the peers' robust sd of log spread; NaN on the index fallback
    l_def = (ref or {}).get("l_def") or (1 - G1_V0["recovery"])
    be = float(row["s5"]) / l_def if l_def > 0 else np.nan
    sp = steps["5"].outputs.get("sp", {})
    rows = [
        {"row": "Default chance at the v0 price of risk (shown, not tested)", "market_implies": _f(implied_pd, 3),
         "our_view": _f(view_pd, 3), "gap": _f(view_pd - implied_pd, 3), "noise": None, "tested": False},
        {"row": "Breakeven default probability, 12 months (loss on price)", "market_implies": _f(be, 3),
         "our_view": _f(view_pd, 3), "gap": _f(view_pd - be, 3), "noise": _f(0.5 * be, 3), "tested": True},
        {"row": f"Spread against fair, {row['fair_basis']} (bp)", "market_implies": _f(row["s5"] * 1e4, 0),
         "our_view": _f(row["fair_s5"] * 1e4, 0), "gap": _f((row["fair_s5"] - row["s5"]) * 1e4, 0),
         "noise": _f(nz * row["fair_s5"] * 1e4, 0) if nz == nz else None, "tested": nz == nz},
        {"row": "Rating class", "market_implies": None, "our_view": sp.get("sp_anchor_class"), "gap": None, "noise": None,
         "tested": False},
        {"row": "Recovery if default (per 1 of face, discounted for delay)", "market_implies": None,
         "our_view": _f(recovery.recovery_pv(G1_V0["recovery"], G1_V0["k_default"], G1_V0["tau_default"]), 2),
         "gap": None, "noise": None, "tested": False},
    ]
    for r in rows:
        r["passes_G1"] = bool(r["tested"] and r["gap"] is not None and r["noise"] is not None and abs(r["gap"]) > r["noise"])
    g1 = any(r["passes_G1"] for r in rows)
    # Signs: our PD above the breakeven is bearish; a negative spread-vs-fair gap
    # (bond pays more than fair) is bullish. Map to "bond cheap" = +1. Untested rows do not vote.
    cheap_votes = [-np.sign(r["gap"]) for r in rows if r["tested"] and r["gap"] is not None]
    g6 = len(set(v for v in cheap_votes if v != 0)) == 1
    g3 = bool(sc_out["alpha"]["passes_g3"])
    g2 = False  # a dated catalyst that the gap maps to: needs the analyst (earnings date alone is not a catalyst)
    if g1 and g3 and g6:
        call = "Watch: relative value candidate. Needs a dated catalyst (G2) and an invalidation level (G8)."
    else:
        call = "Pass: credit opinion only. " + ", ".join(
            x for x, ok in (("no gap larger than its noise (G1)", g1), ("alpha after cost not above zero (G3)", g3),
                            ("the gaps disagree in sign (G6)", g6)) if not ok) + "."
    s.outputs = {"table": rows, "G1": g1, "G2": g2, "G3": g3, "G6": g6, "call": call, "direction":
                 "cheap" if cheap_votes and np.mean(cheap_votes) > 0 else "rich"}
    s.status = "partial"
    s.open_questions += ["A dated catalyst that would close the gap (G2).",
                         "The observable and level that would prove the call wrong (G8)."]
    return s


def step_events(blk, decision, st: dict | None = None, sc_out=None) -> Step:
    s = Step("12 Events in the next 90 days", "Framework F11")
    v = ci.values(blk["inputs"])
    idx = edgar.filing_index(v["cik"], cache_root=RAW)
    per = idx[idx["form"].isin(["10-Q", "10-K"]) & (idx["acceptance"] <= decision)].sort_values("acceptance")
    ev = []
    if len(per):
        nxt = per["acceptance"].iloc[-1] + pd.Timedelta(91, unit="D")
        ev.append({"event": "Next quarterly results (estimated from filing cadence)", "date": str(nxt.date()),
                   "confirmed": False})
    lad = blk["case"]["ladders"]["debt"]
    if lad:
        first_len = blk["case"]["ladders"]["debt_first_length"] or 1.0
        ev.append({"event": f"Debt due by {first_len:.1f} years out", "amount_m": _f(lad[0], 0), "years": float(first_len),
                   "confirmed": True})
    s.outputs = {"events": ev}
    if st is not None:
        s.outputs.update(monitoring_block(blk, st, sc_out))
    s.status = "partial"
    s.open_questions.append("Call dates, covenant test dates, and rating reviews: not in the data yet.")
    return s


def monitoring_block(blk, st: dict, sc_out) -> dict:
    """G3 borrower-monitoring: trajectory per dimension and the watchlist tier.

    Trajectory on revenue, EBITDA, EBITDA margin and cash conversion ((CFO - capex) / EBITDA), each from year-on-year
    quarterly changes. Watchlist: LTM EBITDA against the LTM a year earlier (the public proxy for "plan"), LTM FCF,
    liquidity against the 18-month wall, the static runway, base-case wall cover with the refinance score, and the
    covenant headroom. Intuition: the borrower should be on the watchlist before the breach, not after it.
    """
    ltm = blk.get("_ltm", {})
    eq = np.asarray(ltm.get("ebitda_q", []), dtype=float)
    vs_prior = float(eq[-4:].sum() / eq[-8:-4].sum() - 1) if eq.size >= 8 and eq[-8:-4].sum() > 0 else float("nan")
    tr_ = skills.trajectory({"revenue": ltm.get("revenue_q", []), "EBITDA": ltm.get("ebitda_q", []),
                             "EBITDA margin": ltm.get("margin_q", []), "cash conversion": ltm.get("conversion_q", [])})
    lq, cs = st["4"].outputs, st["5"].outputs
    run_q = lq.get("runway_static_q")
    wl = skills.watchlist_tier(vs_prior, ltm.get("fcf", np.nan), lq.get("L_eff_m") or np.nan, lq.get("wall_18m_m") or 0.0,
                               run_q if isinstance(run_q, (int, float)) else None, lq.get("wall_cover_4_base"),
                               sc_out["refi_score_by_path"].get(sc_out["modal_path"]),
                               cs.get("headroom_H") if cs.get("headroom_H") is not None else np.nan,
                               revolver_known=bool(lq.get("revolver_capacity_m")))
    calls = [v["call"] for v in tr_.values() if v["call"] != "open"]
    return {"watch_tier": wl["watchlist_tier"], "watch_tier_n": wl["tier_n"], "watch_reasons": wl["reasons"],
            "watch_open": wl["open"],
            "ebitda_vs_prior_year": _f(vs_prior, 3), "trajectory": tr_,
            "trajectory_conflict": "improving" in calls and "deteriorating" in calls}


def reference_bond(bonds: pd.DataFrame) -> dict | None:
    """The bond nearest 5 years (TENOR) with its accrued interest and dirty price (RV PDF U1, U2; 30/360 semiannual)."""
    if bonds is None or bonds.empty:
        return None
    b = bonds.iloc[(bonds["maturity_years"] - TENOR).abs().argsort().iloc[0]]
    acc = hal.accrued_interest(float(b["coupon"]), float(b["maturity_years"]))
    return {"cusip": b["cusip"], "coupon": float(b["coupon"]), "years": float(b["maturity_years"]),
            "maturity": str(pd.Timestamp(b["maturity"]).date()), "price": float(b["price"]), "accrued": acc,
            "dirty_price": float(b["price"]) + acc, "g_spread": float(b["g_spread"])}


def step_decision(t, ref: dict, sc_out, mac, xs, curve_now, decision, events: list | None = None) -> Step:
    """Decision against cash (spec S15; RV PDF Section 9, E50 to E60; mapping Top 10 item 1 and C1, C3).

    Reference bond = the one nearest 5 years. Horizon h = V0 h_years. Per macro path m and default state:
      survive: the bond's spread at H, s_H = s_b S_H(m) / S - (1 - rho^(4h)) (s5 - s_fair) S_m / S (the market moves
               and the issuer's gap closes at the engine's speed), Treasury at H = the path's par yield for the
               remaining tenor; default: 100 x R_PV with R_PV = R / (1 + k)^tau.
    Unhedged: excess over cash mu, P(loss), P(below cash), ES95 (the PDF decision quantities).
    Hedged (shown beside it): rates held at today's curve and the market move removed, s_H = s_b - (1 - rho^(4h))
    (s5 - s_fair) S_m / S; subtract a Treasury of the same tenor and beta x (index carry - index expected loss), with
    beta = s_b / S, the DTS hedge on the HY index (decision page 2026-10-23-peer-fair-spread; the walk-forward realises
    the same hedge). The total hedged return is that hedged mu. Catalysts: the step 12 events dated within the horizon.
    E10 of the combined view uses the unhedged mu. Intuition: the same money in the bond or in cash; then the same with
    the market hedged out.
    """
    s = Step("15 Decision against cash", "RV PDF Section 9; methodology 7.5, 8; framework F1 R8")
    if not ref:
        s.status = "blocked"
        s.open_questions.append("No priced bond: the decision against cash needs a price.")
        return s
    h, rho, kappa = scenarios.V0["h_years"], scenarios.V0["rho_q"], scenarios.V0["kappa"]
    S = mac.s_index_now
    s5, sf5 = float(xs.loc[t, "s5"]), float(xs.loc[t, "fair_s5"])
    close = 1 - rho ** (4 * h)
    rpv = recovery.recovery_pv(G1_V0["recovery"], G1_V0["k_default"], G1_V0["tau_default"])
    T, c, sb, P = ref["years"], ref["coupon"], ref["g_spread"], ref["dirty_price"]
    pdh = {r["macro_path"]: hal.pd_over_horizon(r["pd_12m"], h) for r in sc_out["table"].to_dict("records")}
    y_left_now = float(tr.interpolate(curve_now, max(T - h, 0.1)))
    un, hd = [], []
    for p in mac.paths.paths:
        S_H, S_m = float(p.index_spread[1]), float(np.mean(p.index_spread[:4]))
        conv = close * (s5 - sf5) * S_m / S
        un.append({"macro_path": p.name, "p_path": p.prob, "pd_h": pdh[p.name], "y_tsy_H": fwd_tsy(p, 2, T - h),
                   "s_H": max(5e-4, sb * S_H / S - conv)})
        hd.append({"macro_path": p.name, "p_path": p.prob, "pd_h": pdh[p.name], "y_tsy_H": y_left_now,
                   "s_H": max(5e-4, sb - conv)})
    r_cash = float(tr.interpolate(curve_now, h))
    dec = hal.decision_against_cash(P, c, T, h, pd.DataFrame(un), rpv, r_cash)
    hed = hal.decision_against_cash(P, c, T, h, pd.DataFrame(hd), rpv, r_cash)
    y_T = float(tr.interpolate(curve_now, T))
    r_tsy = hal.treasury_return(y_T, y_left_now, T, h)
    beta = fairspread.dts_beta(sb, S)  # DTS hedge on the HY index; the walk-forward realises the same beta
    idx = sum(p.prob * (S * h - float(np.mean(p.index_spread[:4])) / kappa * h) for p in mac.paths.paths)
    mu_h = hed["mu_excess"] + r_cash * h - r_tsy - beta * idx
    st = dec["states"]
    s.outputs = {
        "reference_bond": ref, "horizon_years": h, "r_cash": _f(r_cash, 4), "recovery_pv": _f(rpv, 3),
        "l_def": _f(recovery.price_based_loss(P, G1_V0["recovery"], G1_V0["k_default"], G1_V0["tau_default"]), 3),
        "mu_excess": _f(dec["mu_excess"], 4), "mu_excess_bp_yr": _f(dec["mu_excess"] / h * 1e4, 0),
        "pi_loss": _f(dec["pi_loss"], 3), "pi_cash": _f(dec["pi_cash"], 3), "es95": _f(dec["es95"], 3),
        "expected_wealth": _f(dec["expected_wealth"], 2), "mu_hedged_bp_yr": _f(mu_h / h * 1e4, 0),
        "total_hedged_return_bp_yr": _f(mu_h / h * 1e4, 0), "hedge": "Treasury of the same tenor + DTS beta x HY index",
        "fair_basis": xs.loc[t, "fair_basis"], "catalysts": hev.catalysts_in_horizon(events or [], decision, h),
        "beta": _f(beta), "states": [{k: (_f(v, 4) if isinstance(v, float) else v) for k, v in r.items()}
                                     for r in st.to_dict("records")],
    }
    s.status = "partial"
    s.open_questions.append("Recovery, delay and the required return on a defaulted claim are v0 (R = 0.4, tau = 1 year, "
                            "k = 15%); the claims view and documents replace them.")
    return s


# ---------------------------------------------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------------------------------------------


def run(tickers, end_str, pairs, out_dir: Path | None = None, figures: bool = True, con=None):
    """Run every step for every issuer as known at end_str + 1 day; write <out_dir>/<ticker>.json and _run.json.

    `out_dir` defaults to data/raw/process (the memo's input). The walk-forward (scripts/walkforward.py) passes its own
    folder per decision date and `figures=False`, so a past date never overwrites the memo's data or charts.
    """
    out_dir = OUT if out_dir is None else Path(out_dir)
    end = pd.Timestamp(end_str)
    decision = end + pd.Timedelta(1, unit="D")
    start = (end - pd.Timedelta(rv_pair.HISTORY_DAYS, unit="D")).strftime("%Y-%m-%d")
    con = con or cp.connect()
    mac = scenarios.live_paths(con, decision, end)
    curve_now = tr.curve_on(end, cache_root=RAW)  # Treasury par curve as of the last TRACE date (no look-ahead)
    steps_all, blocks, fits = {}, {}, {}
    for t in tickers:
        try:
            s1, blk = step_inputs(con, t, decision, start, end_str)
        except Exception as e:
            print(f"{t}: inputs failed ({type(e).__name__}: {e})")
            continue
        blocks[t] = blk
        bd = blk["bonds"]
        fits[t] = rv.curve_fit(bd["maturity_years"], bd["g_spread"]) if len(bd) else (float("nan"), 0.0)
        steps_all[t] = {"1": s1}
    # Universe step: the fair spread from sector peers on the TRACE panel, the HY index where no peer cell exists
    # (methodology 7.2; decision page 2026-10-23-peer-fair-spread). It does not depend on the other tickers in the run.
    xs = pd.DataFrame({t: {"s5": rv.curve_at(fits[t], TENOR), "lev": blocks[t]["risk"].lev_lease_adj} for t in blocks}).T
    xs = xs.astype(float).dropna()
    xs = xs[xs["s5"] > 0]
    ptab = peer_table(blocks, xs, decision)
    fair = {t: fairspread.peer_fair_spread(float(xs.loc[t, "s5"]),
                                   ptab.loc[t, "esp_sr"] if ptab is not None and t in ptab.index else None,
                                   ptab.loc[t, "esp_sd_sr"] if ptab is not None and t in ptab.index else None,
                                             mac.s_index_now) for t in xs.index}
    xs["fair_s5"] = [fair[t]["fair"] for t in xs.index]
    xs["fair_basis"] = [fair[t]["basis"] for t in xs.index]
    xs["noise_log"] = [fair[t]["noise_log"] for t in xs.index]
    xs["resid_log"] = np.log(xs["s5"] / xs["fair_s5"])
    for t, blk in blocks.items():
        st = steps_all[t]
        st["2"] = step_frame(blk)
        st["3"] = step_normalise(blk, decision)
        if t not in xs.index:
            print(f"{t}: no spread; steps 7 to 11 blocked")
            continue
        arch = st["2"].outputs.get("archetype") or "A4"
        start_, drv, info = scenarios.issuer_start(blk["inputs"], blk["case"], decision)
        qs = blk.get("_quarters") or ci.loader_quarters(t, ci.values(blk["inputs"]).get("gvkey"), RAW, decision)[0]
        q4 = ci.last_four(qs)
        if q4:
            blk["_fcf_ltm"] = sum((r.operating_cash_flow - r.capex_total) for r in q4)
            blk["_interest_ltm"] = sum(r.cash_interest for r in q4)
            blk["_capex_ltm"] = sum(r.capex_total for r in q4)
            blk["_maint_capex_ltm"] = sum(min(r.capex_total, r.depreciation) if r.depreciation == r.depreciation
                                          else r.capex_total for r in q4)
        s5, sf5 = float(xs.loc[t, "s5"]), float(xs.loc[t, "fair_s5"])
        pts = scenarios.refi_points(s5, blk["longest"], blk["recent_raise"])
        ref = reference_bond(blk["bonds"])
        if ref:  # mapping C3 and Top 10 item 2: default loss on the purchase price, recovery discounted for delay
            ref["l_def"] = recovery.price_based_loss(ref["dirty_price"], G1_V0["recovery"], G1_V0["k_default"],
                                                     G1_V0["tau_default"])
        blk["_ref"] = ref
        sc_out = scenarios.issuer_scenarios(start_, drv, arch, mac, s_now=s5, s_fair_now=sf5,
                                            spread_duration=rv.modified_duration(0.04 + s5, 0.04 + s5, TENOR), points=pts,
                                            loss_given_default=ref["l_def"] if ref else None,
                                            capex_committed_q=info["capex_total_q"])
        if figures:
            scenarios.scenario_figure(blk["name"], t, sc_out, FIG / f"scenarios_{t}.png")
        blk["_sc_out"] = sc_out
        mcap, mcap_src = market_value(con, ci.values(blk["inputs"])["gvkey"], decision)
        st["4"] = step_liquidity(blk, sc_out, info, start_, mac, s5)
        st["5"] = step_capstructure(blk, st["4"].outputs, mcap, arch, blk["case"]["metrics"].get("cust_top1"))
        st["2"].outputs["business_risk"] = st["5"].outputs.get("sp", {}).get("business_risk_score")
        st["6"] = step_clocks(blk)
        st["7"] = step_cases(sc_out)
        st["8"] = step_valuation(con, blk, decision, (mcap, mcap_src))
        st["9"] = step_rv(t, xs, mac.s_index_now, lev_gross=st["5"].outputs.get("lev_gross"))
        st["10"] = step_alpha(sc_out, ref)
        st["11"] = step_gate(t, st, xs, sc_out, ref)
        st["12"] = step_events(blk, decision, st, sc_out)
        st["13"] = step_metrics(st, sc_out)
        st["15"] = step_decision(t, ref, sc_out, mac, xs, curve_now, decision, st["12"].outputs.get("events", []))
        print(f"{t}: " + " | ".join(f"{k}:{v.status[0]}" for k, v in st.items()))
    add_peers(steps_all, ptab)
    # Pair step (methodology 7.4, 7.5): spread per unit of risk, gap half-life, and the pair under each path.
    curves = pd.concat([tr.par_curve(y, cache_root=RAW) for y in sorted({start[:4], str(end.year)})]).sort_index()
    curves = curves[~curves.index.duplicated()]
    resid = xs["resid_log"].to_dict()
    pairs_out = []
    for a, b in pairs or []:
        if a in blocks and b in blocks and a in resid and b in resid:
            pr = rv_pair.pair_block(blocks[a], blocks[b], fits, resid, curves)
            lo, sh = pr["alpha"]["long"], pr["alpha"]["short"]
            if "_sc_out" in blocks[lo] and "_sc_out" in blocks[sh]:
                al = blocks[lo]["_sc_out"]["table"].set_index("macro_path")
                ash = blocks[sh]["_sc_out"]["table"].set_index("macro_path")
                by = (al["alpha"] - ash["alpha"]) / scenarios.V0["h_years"] * 1e4
                pr["pair_alpha_by_path_bp"] = by.round(1).to_dict()
                pr["pair_alpha_weighted_bp"] = float((by * al["p_path"]).sum())
            pairs_out.append(pr)
    for t in steps_all:
        steps_all[t]["9b"] = step_pair(t, pairs_out)
    scen_out = {t: blocks[t]["_sc_out"] for t in steps_all if "_sc_out" in blocks[t]}
    comb = combined_view(steps_all, scen_out, xs, mac.s_index_now)
    slope = measured_slope()
    for t in steps_all:
        steps_all[t]["14"] = step_combined(t, comb)
        steps_all[t]["14b"] = step_size_calibration(t, comb, slope)
        if comb.get(t):
            steps_all[t]["14"].outputs["alpha_sized"] = steps_all[t]["14b"].outputs.get("alpha_sized")
        dec = comb.get(t, {}).get("decision")
        if dec and "15" in steps_all[t]:
            steps_all[t]["15"].outputs.update({**dec, "replaces_position": dec["best_admissible"]})
        if steps_all[t]["14"].outputs:
            steps_all[t]["14"].outputs["memo_checks"] = skills.memo_checks(memo_have(steps_all[t]))
            steps_all[t]["14"].outputs["not_transferable"] = skills.NOT_TRANSFERABLE
        for k, v in steps_all[t].items():
            v.groups = STEP_GROUPS.get(k, [])
    out_dir.mkdir(parents=True, exist_ok=True)
    macro = {"phase": mac.paths.phase, "votes": mac.paths.votes, "paths": [
        {"name": p.name, "prob": p.prob, "gdp": float(p.gdp_growth.mean()), "policy_q8": float(p.policy_rate[-1]),
         "y10_q8": float(p.y10[-1]), "hy_spread": float(p.index_spread[:4].mean())} for p in mac.paths.paths],
        "s_index_now": mac.s_index_now, "decision": str(decision.date()),
        # Point-in-time audit trail (scripts/walkforward.py): what each forecast source and the curve were as of.
        "forecast_sources": fs.source_status().astype(str).to_dict("records"), "curve_date": str(curve_now.name)}
    for t, st in steps_all.items():
        dump = {"ticker": t, "name": blocks[t]["name"], "macro": macro, "steps": {k: asdict(v) for k, v in st.items()}}
        (out_dir / f"{t}.json").write_text(json.dumps(dump, indent=2, default=str))
    (out_dir / "_run.json").write_text(json.dumps({"tickers": list(steps_all), "macro": macro, "decision": str(decision.date()),
                                               "fair_line": {"basis": xs["fair_basis"].value_counts().to_dict(), "n": int(len(xs))},
                                               "group_weights": groups.GROUP_WEIGHTS, "estimates": groups.ESTIMATES,
                                               "g1_v0": G1_V0}, indent=2, default=str))
    return steps_all


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tickers", nargs="+", default=["CRWV", "ORCL", "HCA", "THC", "CCL", "NCLH", "MGM", "WYNN"])
    ap.add_argument("--end", default="2026-09-17", help="last TRACE date; filings as known the next day")
    ap.add_argument("--pairs", nargs="*", default=["CRWV:ORCL", "HCA:THC", "CCL:NCLH", "MGM:WYNN"])
    args = ap.parse_args()
    pairs = [tuple(p.upper().split(":")) for p in args.pairs]
    run([t.upper() for t in args.tickers], args.end, pairs)
    import memo  # noqa: E402  (writes docs/writeup/issuer_memos.tex)
    memo.main()


if __name__ == "__main__":
    main()
