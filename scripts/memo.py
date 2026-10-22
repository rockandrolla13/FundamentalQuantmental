"""Write the issuer memos in plain English from scripts/process.py output: one analyst, four method groups.

    PYTHONPATH=. python3 scripts/memo.py     # reads data/raw/process/*.json, writes docs/writeup/issuer_memos.tex

Each memo opens with the call and the combined view across the four groups. Then one section per group:
G1 core process (Gatto's seven steps, the method, the rulebook, the relative value paper), G2 built methods (the two
clocks in full, the stories and cases, relative value, the gate, the health panel), G3 credit skills (add-backs,
covenants, watchlist, trajectory, memo checks), G4 books (Kricheff; Ganguin and Bilardello). The framework's full
memo (F12) sections all appear; the front page ranks every issuer on the combined number with one column per group.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "raw" / "process"
FIGS = ROOT / "docs" / "writeup" / "figures"
OUT = ROOT / "docs" / "writeup" / "issuer_memos.tex"

STEP_NAMES = {
    "1": "Load the data", "2": "Describe the business", "3": "Check the earnings", "4": "Cash and debt due",
    "5": "Debt, ratios, covenants", "6": "Bills against contracts", "7": "Economic stories", "8": "Company value",
    "9": "Compare with peers", "9b": "Compare the pair", "10": "Expected profit", "11": "Price against our view",
    "12": "Events and watchlist", "13": "Health check panel", "14": "Combined view", "14b": "Size calibration",
    "15": "Decision against cash",
}
MARK = {"done": "\\textcolor{good}{\\textbf{D}}", "partial": "\\textcolor{amber}{\\textbf{P}}", "blocked": "\\textcolor{bad}{\\textbf{B}}"}
GROUPS = {
    "G1": ("Core process", "Gatto's seven steps, our method and rulebook, and the relative value paper"),
    "G2C": ("Two clocks", "the bills the company owes against the revenue customers have signed for"),
    "G2": ("Built methods (rest)", "the spread level, the fair line and the pair, the economic stories, the health panel"),
    "G3": ("Credit skills", "the lender's checklists: add-backs, covenants, watchlist, trend, memo structure"),
    "G4": ("Books and peers", "Kricheff's cash bridge and ratios; the S\\&P risk profiles and rating anchor; "
           "spread against peers (Dynkin et al.)"),
}
ESTIMATE_WORDS = {  # plain words, then where it comes from (research/combined_framework_spec.md S14)
    "E0": ("Spread level: the extra pay over the market (carry)", "Spec S14 E0; K15"),
    "E1": ("Weighted cases and stories", "M5.4, M7.5"),
    "E2": ("Spread against the fair line", "M7.4, M7.5"),
    "E3": ("The pair", "M7.4; F10 S4"),
    "E4": ("Default chance the price assumes (shown, weight 0)", "F9; mapping C2"),
    "E5": ("The two clocks", "M4.7"),
    "E6": ("Health panel", "F8"),
    "E7": ("Earnings quality, add-backs, FCF check (can only lower)", "F3; ebitda-addback-treatment; hy-model-standards"),
    "E8": ("Access to new money and the funding gap", "F4; RV PDF E75-E76"),
    "E9": ("Debt against market value", "F7.7"),
    "E10": ("Return above cash, repriced in every story", "RV PDF E50-E60; C1, C3"),
    "E11": ("Watchlist tier (can only lower)", "borrower-monitoring; covenant-compliance"),
    "E12": ("Spread against the S\\&P risk score", "Ganguin and Bilardello ch. 10"),
    "E13": ("Spread per turn of leverage (with the trap guard)", "Kricheff ch. 21"),
    "E14": ("Excess spread to sector and rating peers (ESP)", "Dynkin et al. ch. 13"),
    "E15": ("SPiDER: spread per unit of debt to 10-year EBITDA", "Dynkin et al. ch. 14"),
    "E16": ("OneScore: sector ranks of ESP and 3-month stock return", "Dynkin et al. ch. 19"),
}
GLOSSARY = [
    ("Spread", "The extra yield a bond pays over a US Treasury of the same maturity. More risk, more spread."),
    ("bp (basis point)", "One hundredth of a percent. 100 bp = 1\\%."),
    ("EBITDA", "Yearly earnings before interest, tax, depreciation and amortisation: the cash the business makes before paying lenders."),
    ("EBITDAR", "EBITDA before rent. Used when rent is one of the bills."),
    ("Add-back", "A cost the company takes out of its own earnings figure because it calls the cost a one-off."),
    ("Leverage", "Debt divided by yearly earnings. With leases: (debt + leases) / (EBITDA + rent). 3x means three years of earnings."),
    ("Coverage", "How many times earnings (after capital spending, where stated) pay the interest bill."),
    ("Liquidity", "Cash plus unused credit lines, less the cash the business needs to run."),
    ("Funding gap", "Liquidity plus free cash flow, less the debt that falls due, quarter by quarter, if no lender refinances. Below zero, the company needs new money."),
    ("Refinancing shock", "The extra yearly interest when debt that falls due is refinanced at today's rates and spread."),
    ("Covenant headroom", "How far earnings (or cash) can fall before a loan test is broken."),
    ("Watchlist", "The lender's list of borrowers to watch: watch closely, watchlist, or workout."),
    ("Two clocks", "One clock counts the bills (rent, debt, interest) the company owes each year; the other counts the revenue customers have signed for. When the bills outlast the contracts, bondholders bet on renewals."),
    ("Fair spread", "The spread a company with this leverage pays, read off a line fitted across the companies in the run."),
    ("Economic story", "One of five views of the next two years, each with a probability from economists' forecasts and the stage of the cycle."),
    ("Breakeven default probability", "The yearly default rate at which the spread only pays for the loss in default. Our default chance below it favours the bond."),
    ("Loss on price", "What a holder loses in default per unit paid for the bond: price less the recovery, with the recovery discounted for the wait."),
    ("Expected profit (alpha)", "What the bond should earn above a hedge, after expected default losses; in bp a year."),
    ("Decision against cash", "The same money in the bond or in cash for six months, across every story and the default case."),
    ("Spread per turn", "The spread divided by leverage: bp paid for each year of earnings the debt represents."),
    ("S\\&P risk score", "A 1 (safest) to 10 (default) score that blends business risk and financial risk; it maps to a rating class."),
    ("Open question", "A number the data cannot give. An analyst must find it before the memo becomes a call."),
]
METRIC_WORDS = {
    "coverage": ("Coverage", "x"), "fccr": ("Fixed-charge cover", "x"), "fcf_conversion": ("Cash conversion (FCF / EBITDA)", ""),
    "fcf_to_debt": ("Free cash flow / debt", ""), "wall_cover_4_base": ("Cash to meet debt due in 1 year (base case)", "x"),
    "refi_score_now": ("Refinancing access score (0 to 6)", ""), "eq_score": ("Earnings-quality flags", ""),
    "w_down": ("Weight on the downside cases", ""), "p_refi_4": ("Chance debt due in 1 year is not covered", ""),
    "p_liq_short_8": ("Chance cash runs out within 2 years", ""), "margin_trend_t": ("Margin trend (t-statistic)", ""),
}
RISK_TEXT = {
    "coverage": ("Earnings after capital spending do not cover interest.", "capital spending falls, or earnings rise"),
    "fccr": ("Earnings do not cover interest plus rent.", "earnings rise or rent falls"),
    "fcf_conversion": ("Little of the earnings turns into free cash.", "growth spending ends"),
    "fcf_to_debt": ("Free cash flow repays little debt.", "free cash flow turns positive"),
    "wall_cover_4_base": ("Cash on hand and expected cash flow do not cover debt due within a year.", "a completed refinancing"),
    "refi_score_now": ("Weak access to the bond market.", "a new bond issue at or near par"),
    "eq_score": ("Earnings-quality flags are raised.", "flags clear in the next two quarters"),
    "w_down": ("The downside cases carry a large weight.", "the cycle indicators improve"),
    "p_refi_4": ("Debt due within a year may not be covered.", "refinancing completes"),
    "p_liq_short_8": ("Cash may run out within two years.", "new financing or lower spending"),
    "margin_trend_t": ("Margins are falling.", "two quarters of stable margins"),
}
METHODS = [
    ("Top", "The call and the combined view of the four groups", "Methodology 8; F10, F12.1; decision 2026-10-22-four-group-combination"),
    ("G1", "The business, earnings, cash, debt, value, the funding gap, the refinancing shock, the decision against cash",
     "Gatto steps 1-7; M4.1-4.3, M6, M7.5; F2-F5, F7; RV PDF (hyrv mapping items 1-4; C2, C3)"),
    ("G2", "The two clocks, the stories and cases, relative value and the pair, expected profit, the gate, the health panel",
     "M4.7, M5.1-5.4, M7.4-7.5; F6, F8, F9, F10 S4"),
    ("G3", "Add-backs, the FCF check, covenant headroom, watchlist, trajectory, memo structure",
     "hy-model-standards; ebitda-addback-treatment; covenant-compliance; borrower-monitoring; credit-memo-standards"),
    ("G4", "Kricheff's cash bridge, ratio set, snapshot and spread per turn; the S\\&P profiles and anchor",
     "Kricheff ch. 9, 10, 21, 24; Ganguin and Bilardello ch. 2-5, 10, App. E"),
    ("End", "Coming events, open questions, the record", "F11, F12"),
]


def esc(s) -> str:
    s = "" if s is None else str(s)
    for a, b in (("\\", "\\textbackslash{}"), ("&", "\\&"), ("%", "\\%"), ("$", "\\$"), ("#", "\\#"), ("_", " "),
                 ("{", "\\{"), ("}", "\\}"), ("~", "-"), ("^", "")):
        s = s.replace(a, b)
    return s


def ok(x) -> bool:
    return x is not None and not (isinstance(x, float) and x != x)


def pct(x, nd=0):
    return "n/a" if not ok(x) else f"{x * 100:.{nd}f}\\%"


def num(x, nd=1, unit=""):
    if not ok(x):
        return "n/a"
    if isinstance(x, str):
        return esc(x)
    return f"{x:,.{nd}f}{unit}"


def bp(x):
    return "n/a" if not ok(x) else f"{x:+,.0f}"


def bn(m):
    return "n/a" if not ok(m) else f"\\${m / 1e3:,.1f}bn"


def table(head, rows, spec=None):
    spec = spec or ("l" + "r" * (len(head) - 1))
    size = "\\scriptsize" if len(head) > 6 else "\\footnotesize"
    out = [f"\\begin{{center}}{size}\\setlength{{\\tabcolsep}}{{3.5pt}}\\begin{{tabular}}{{@{{}}{spec}@{{}}}}\\toprule",
           " & ".join(head) + " \\\\\\midrule"]
    out += [" & ".join(str(c) for c in r) + " \\\\" for r in rows]
    out.append("\\bottomrule\\end{tabular}\\end{center}")
    return "\n".join(out)


def box(text: str) -> str:
    return (f"\\par\\noindent\\fcolorbox{{gray}}{{gray!6}}{{\\parbox{{\\dimexpr\\linewidth-2\\fboxsep-2\\fboxrule-1pt}}{{\\sloppy "
            f"{text}}}}}\n")


def plain_call(g: dict) -> str:
    if not g:
        return "Not reached: an earlier step is blocked."
    side = "cheap" if g.get("direction") == "cheap" else "expensive"
    if g.get("G1") and g.get("G3") and g.get("G6"):
        return (f"Watch. The bond looks {side} by more than the model's noise, every check points the same way, and the "
                "expected profit beats trading costs. Before it becomes a trade, an analyst must name a dated event that "
                "would close the gap and the level that would prove the view wrong.")
    why = []
    if not g.get("G1"):
        why.append("no gap between price and our view is bigger than the noise")
    if not g.get("G3"):
        why.append("the expected profit does not beat trading costs")
    if not g.get("G6"):
        why.append("the checks point in different directions")
    return "Pass. This is a view of the company, not a trade: " + "; ".join(why) + "."


GROUP_OF = {"E0": "G2", "E1": "G2", "E2": "G2", "E3": "G2", "E4": "G1", "E5": "G2C", "E6": "G2", "E7": "G1",
            "E8": "G1", "E9": "G1", "E10": "G1", "E11": "G3", "E12": "G4", "E13": "G4", "E14": "G4", "E15": "G4", "E16": "G4"}  # hy.groups.ESTIMATES
BUCKET_ORDER = ("G1", "G2C", "G2", "G3", "G4")  # hy.groups.BUCKETS
BUCKET_LABEL = {"G1": "G1", "G2C": "G2 clocks", "G2": "G2 rest", "G3": "G3", "G4": "G4"}
VERDICT_COL = {"supports owning": "good", "leans to owning": "amber", "against owning": "bad", "no view": "gray",
               "no objection": "good"}


def vword(v: str) -> str:
    return f"\\textcolor{{{VERDICT_COL.get(v, 'gray')}}}{{{v}}}"


def group_box(cb: dict, g: str, extra: str) -> str:
    """The group's verdict box and its estimate table."""
    gr = cb["groups"][g]
    name, what = GROUPS[g]
    one = (" Its estimates can only lower the combined number: a clean checklist earns no credit."
           if gr.get("one_way_only") else "")
    head = (f"\\textbf{{Verdict: {vword(gr['verdict'])}.}} This group reads {what}. Its estimate of expected profit is "
            f"{bp(gr['alpha_bp_yr'])} bp a year before trading costs (costs are {num(cb['cost'], 0)} bp a year); "
            f"{gr['agree']} of {gr['n']} of its weighted estimates point the same way. It carries {pct(gr.get('group_share'))} "
            f"of the combined view and ranks {gr.get('rank', 'n/a')} of the issuers on this group alone.{one} {extra}")
    rows = [[ESTIMATE_WORDS[r["estimate"]][0], bp(r["alpha_bp_yr"]), pct(r["weight"]), bp(r["contribution"]),
             ESTIMATE_WORDS[r["estimate"]][1]] for r in gr["rows"]]
    have = {r["estimate"] for r in gr["rows"]}
    missing = [ESTIMATE_WORDS[k][0] for k in ESTIMATE_WORDS if GROUP_OF.get(k) == g and k not in have]
    out = box(head) + table(["Estimate", "bp a year", "Weight in group", "Adds", "Where it comes from"], rows,
                            "p{6.2cm}rrrp{4.2cm}")
    if missing:
        out += f"\nNo estimate (data missing): {esc(', '.join(missing).lower())}.\n"
    return out


def memo(d: dict) -> str:
    st, t, name = d["steps"], d["ticker"], d["name"]
    O = lambda k: st.get(k, {}).get("outputs", {})  # noqa: E731
    g, fr, nm, lq, cs, ck = O("11"), O("2"), O("3"), O("4"), O("5"), O("6")
    cases, va, rvo, al, pairs, panel = O("7"), O("8"), O("9"), O("10"), O("9b").get("pairs", []), O("13").get("panel", [])
    ev, dc, cb = O("12"), O("15"), O("14")
    L = [f"\\section*{{{esc(name)} ({t})}}\\pdfbookmark[1]{{{t}}}{{bm-{t}}}\\label{{memo-start-{t}}}"]
    rep = dc.get("replaces_position")
    L.append(box(f"\\textbf{{Recommendation.}} {esc(plain_call(g))} "
                 + (f"If the money went elsewhere, the best alternative in this run is {esc(rep)}. " if rep else "")
                 + "Position size and hedge: open until the call passes."))

    # ------------------------------------------------------------------ combined view
    sz = O("14b")
    if cb.get("groups"):
        L.append("\\subsection*{The combined view: four groups, one estimate}")
        L.append("Each group of methods estimates the same thing: what the bond should earn above a hedge, in bp a year. "
                 f"The combined estimate weighs the four groups. It ranks {cb.get('rank')} of the issuers in this run. "
                 f"{cb.get('groups_agree')} of {cb.get('groups_n')} groups point the same way as the combination.")
        rows = [[f"{BUCKET_LABEL[gg]}. {GROUPS[gg][0]}", bp(cb['groups'][gg]['alpha_bp_yr']), pct(cb['groups'][gg].get('group_share')),
                 bp(cb['groups'][gg].get('contribution')), vword(cb['groups'][gg]['verdict'])] for gg in BUCKET_ORDER]
        rows += [["\\textbf{Combined, before trading costs}", "", "", f"\\textbf{{{bp(cb['combined_before_cost'])}}}", ""],
                 ["Trading costs", "", "", bp(-cb["cost"]), ""],
                 ["\\textbf{Combined, after trading costs}", "", "", f"\\textbf{{{bp(cb['combined_after_cost'])}}}", ""],
                 ["Weighted cases and stories alone, after costs", "", "", bp(cb["anchor_after_cost"]), ""],
                 [f"Calibrated: after-cost number x measured slope {num(sz.get('mz_b'), 3)}", "", "", bp(sz.get("alpha_sized")), ""]]
        L.append(table(["Group", "bp a year", "Weight", "Adds", "Call"], rows, "lrrrl"))
        diff = cb["combined_after_cost"] - cb["anchor_after_cost"]
        L.append(f"Against the weighted cases and stories alone, the combination is {abs(diff):,.0f} bp a year "
                 f"{'higher' if diff > 0 else 'lower'}: the other methods {'add to' if diff > 0 else 'take away from'} "
                 "the case for owning the bond. A group that supports owning must beat the trading costs on its own. "
                 "The weights are the user's choice: core process 45\\%, two clocks 20\\%, and 11.7\\% each for the "
                 "rest of the built methods, the credit skills and the books. The backtest alone would have put most "
                 "weight on the built methods.")
        if sz:
            use = ("The slope is not above zero by two standard errors, so the number ranks the bond but does not size it."
                   if not sz.get("slope_significant") else "The calibrated number sizes the position.")
            L.append(box(f"\\textbf{{Alpha sizes are uncalibrated.}} The backtest (2008 to 2026) shows that this kind of "
                         "estimate ranks bonds well but overstates the size of the move. Realised alpha has been about "
                         f"{num(sz.get('mz_b'), 2)} times the predicted alpha (standard error {num(sz.get('mz_se_b'), 2)}; "
                         f"{num(sz.get('mz_b_pilot'), 2)} since 2019). The calibrated number multiplies by that slope: "
                         f"{bp(sz.get('alpha_sized'))} bp a year after costs ({bp(sz.get('alpha_sized_pilot'))} on the 2019 "
                         f"slope). {use} Decision page: 2026-10-22-alpha-backtest-design. The backtest has no default-loss "
                         "term yet."))

    # ------------------------------------------------------------------ G1
    L.append("\\section*{G1. Core process: Gatto's steps, our method and rulebook, the relative value paper}")
    if cb.get("groups"):
        L.append(group_box(cb, "G1", f"Best alternative for the same money: {esc(rep or 'n/a')}."))
    cheap = rvo.get("cheap_by_bp")
    L.append("\\subsection*{G1.1 Thesis}")
    L.append(f"The bond pays {num(rvo.get('spread_5y_bp'), 0)} bp over Treasuries at 5 years. A company with its leverage "
             f"({num(rvo.get('lev_lease_adj'), 1, 'x')} with leases) pays {num(rvo.get('fair_5y_bp'), 0)} bp on the fair line, so the bond is "
             f"{'cheap' if (cheap or 0) > 0 else 'expensive'} by {num(abs(cheap or 0), 0)} bp. "
             + ("The bills outlast the signed contracts (section G2.1), so part of the extra spread pays for a renewal bet that the line does not see. "
                if ck.get("breakeven_margin") is not None else "")
             + "What would reveal it, and when: open question.")

    L.append("\\subsection*{G1.2 The business}")
    L.append("\\begin{enumerate}")
    L.append(f"\\item \\textbf{{What it sells:}} {esc(fr.get('sells') or 'open question')}")
    L.append(f"\\item \\textbf{{How it earns:}} {esc(fr.get('earns') or 'open question')}.")
    L.append(f"\\item \\textbf{{What it must spend to stand still:}} rent of about \\${num(fr.get('rent_per_year_bn'), 1)}bn a year, plus maintenance capital spending.")
    L.append("\\item \\textbf{Competition:} open question.")
    L.append(f"\\item \\textbf{{What breaks it:}} {esc(fr.get('breaks') or 'open question')}.")
    L.append("\\end{enumerate}")
    L.append(f"Business type: {esc(fr.get('archetype'))}" + (f"; flags: {esc(', '.join(fr.get('modifiers')))}" if fr.get("modifiers") else "") + ".")

    L.append("\\subsection*{G1.3 Earnings, normalised}")
    flags = nm.get("eq_flags", {})
    raised = [k for k, v in flags.items() if v]
    L.append(f"Last 12 months: EBITDA {bn(nm.get('ebitda_ltm_m'))} at a {pct(nm.get('margin_ltm'))} margin; margin trend over 8 quarters "
             f"{num(nm.get('margin_trend_t'), 1)} (t-statistic: above 1 rising, below $-1$ falling). One-off items {bn(nm.get('special_items_ltm_m'))}. "
             f"Free cash flow {bn(nm.get('fcf_ltm_m'))}: {pct(nm.get('fcf_conversion'))} of EBITDA. "
             f"Earnings-quality flags raised: {esc(', '.join(raised)) if raised else 'none'} (of {len(flags)} tests the data supports). "
             "The add-back detail is in section G3.1.")

    L.append("\\subsection*{G1.4 Cash, the funding gap, and the refinancing shock}")
    L.append(table(["Item", "Value"], [
        ["Cash", bn(lq.get("cash_m"))], ["Unused credit lines (tagged)", bn(lq.get("revolver_capacity_m"))],
        ["Less cash needed to run", bn(lq.get("min_cash_m"))], ["Liquidity", bn(lq.get("L_eff_m"))],
        ["Runway at today's cash burn, all capital spending (quarters)", num(lq.get("runway_static_q"), 1)],
        ["First quarter cash runs out, severe case, maintenance spending only", num(lq.get("runway_scen_q"), 0)],
        ["First quarter cash runs out, severe case, all committed spending", num(lq.get("runway_full_capex_scen_q"), 0)],
        ["\\textbf{Runway we quote (the shortest)}",
         "\\textbf{none in 8 quarters}" if not isinstance(lq.get("runway_quoted_q"), (int, float))
         else f"\\textbf{{{num(lq.get('runway_quoted_q'), 1)}}} ({esc(lq.get('runway_quoted_basis'))})"],
        ["Debt due in the next 18 months", bn(lq.get("wall_18m_m"))],
        ["Cash to meet debt due in a year, base case", num(lq.get("wall_cover_4_base"), 2, "x")],
        ["Refinancing access score, likely story (0 to 6)", num(cases.get("modal_path") and lq.get("refi_score_by_path", {}).get(cases.get("modal_path")), 0)],
    ], "lr"))
    if "funding_gap_min" in lq:
        fq = lq.get("first_gap_q")
        L.append("\\textbf{Funding gap if no lender refinances.} We add cash, the unused lines and the free cash flow of the "
                 "cases, then take off the debt as it falls due, quarter by quarter. The minimum cash kept back is one month "
                 f"of cash operating costs ({bn(lq.get('c_min_m'))}).")
        L.append(table(["Measure", "Value"], [
            ["Lowest point, likely story (maintenance spending only)", bn(lq.get("funding_gap_min"))],
            ["First quarter below zero, likely story", f"quarter {fq}" if fq else "none in 8 quarters"],
            ["Lowest point with all capital spending", bn(lq.get("funding_gap_min_full_capex_m"))],
            ["First quarter below zero with all capital spending", f"quarter {lq['first_gap_q_full_capex']}" if lq.get("first_gap_q_full_capex") else "none in 8 quarters"],
            ["Lowest point, severe case", bn(lq.get("funding_gap_min_severe_m"))],
            ["Severe case with all capital spending: first quarter below zero", esc(f"quarter {lq['runway_full_capex_q']}" if isinstance(lq.get("runway_full_capex_q"), int) else lq.get("runway_full_capex_q") or "n/a")],
            ["Lowest point, weighted over the stories", bn(lq.get("funding_gap_min_weighted_m"))],
            ["Debt due inside 8 quarters, share of all debt", pct(lq.get("maturity_share_8q"))],
        ], "lr"))
        L.append(f"\\textbf{{Refinancing shock.}} {bn(lq.get('refi_amount_8q_m'))} falls due in the next two years. It pays about "
                 f"{pct(lq.get('c_old'), 2)} today ({esc(lq.get('c_old_source'))}). Refinanced at the forecast Treasury rate plus today's "
                 f"spread, yearly interest changes by {bn(lq.get('delta_I'))} ({pct(lq.get('delta_I_to_ebitda'), 1)} of EBITDA). "
                 f"Interest cover after refinancing: {num(lq.get('cash_cov_after_refi'), 1, 'x')}; after capital spending "
                 f"{num(lq.get('after_capex_cov_after_refi'), 1, 'x')}. Free cash flow after the shock: {pct(lq.get('fcf_after_refi_to_debt'), 1)} of debt.")

    L.append("\\subsection*{G1.5 Debt: going-concern view}")
    L.append(table(["Measure", "Value"], [
        ["Debt", bn(cs.get("debt_m"))], ["Lease liabilities", bn(cs.get("lease_debt_m"))], ["EBITDA, last 12 months", bn(cs.get("ebitda_ltm_m"))],
        ["Debt / EBITDA", num(cs.get("lev_gc_total"), 1, "x")], ["(Debt + leases) / (EBITDA + rent)", num(cs.get("lev_lease_adj"), 1, "x")],
        ["Net debt / EBITDA", num(cs.get("net_lev"), 1, "x")], ["Coverage (after all capital spending)", num(cs.get("coverage"), 1, "x")],
        ["Fixed-charge cover (after maintenance spending)", num(cs.get("fccr"), 2, "x")]], "lr"))
    bonds = cs.get("bonds", [])[:6]
    if bonds:
        L.append(table(["Bond", "Coupon", "Matures", "Price", "Yield", "Spread (bp)"],
                       [[b["cusip"], pct(b["coupon"], 2), b["maturity"], num(b["price"], 1), pct(b.get("yield"), 2), num(b["spread_bp"], 0)] for b in bonds]))
    L.append("Claims view (who is paid what in a default): open question until the debt documents are read.")

    L.append("\\subsection*{G1.6 Company value}")
    L.append(f"Market value of the whole company \\${num(va.get('market_tev_bn'), 0)}bn (shares \\${num(va.get('market_cap_bn'), 0)}bn plus net debt): "
             f"{num(va.get('tev_to_ebitda'), 1, 'x')} EBITDA; debt is {pct(va.get('debt_to_market_tev'))} of it. "
             "Our own valuation range and the bonds' recovery if the company defaults: open questions (they need a peer set and a distressed multiple).")

    if dc.get("mu_excess") is not None:
        rb = dc.get("reference_bond", {})
        L.append("\\subsection*{G1.7 The decision against cash}")
        L.append(f"We put the same money in the bond nearest five years ({esc(rb.get('cusip'))}, {pct(rb.get('coupon'), 2)} due "
                 f"{esc(rb.get('maturity'))}, price {num(rb.get('price'), 2)} plus {num(rb.get('accrued'), 2)} accrued) or in "
                 f"six-month Treasury bills at {pct(dc.get('r_cash'), 2)}. In each story the bond either survives and is repriced, or "
                 f"defaults and returns {num(100 * (dc.get('recovery_pv') or 0), 0)} per 100 (a 40\\% recovery paid a year later, "
                 f"valued at 15\\% a year). In default the holder loses {pct(dc.get('l_def'))} of the price paid.")
        L.append(table(["Measure", "Value"], [
            ["Expected return above cash, bp a year", bp(dc.get("mu_excess_bp_yr"))],
            ["Chance of a loss over six months", pct(dc.get("pi_loss"), 1)],
            ["Chance of doing worse than cash", pct(dc.get("pi_cash"), 1)],
            ["Average loss in the worst 5\\% of outcomes", pct(dc.get("es95"), 1)],
            ["Same, with rates and the market hedged out, bp a year", bp(dc.get("mu_hedged_bp_yr"))],
            ["Best alternative in this run (worst 5\\% loss within the 25\\% budget)", esc(dc.get("best_admissible"))],
            ["Return given up against that alternative, bp a year", bp(dc.get("opportunity_cost_bp_yr"))],
        ], "lr"))

    # ------------------------------------------------------------------ G2
    L.append("\\section*{G2. Built methods: two clocks, stories and cases, relative value, the gate}")
    if cb.get("groups"):
        L.append(group_box(cb, "G2", f"Gate: {esc(plain_call(g).split('.')[0]).lower()}."))
    L.append("\\subsection*{G2.1 The two clocks: bills against what pays for them}")
    if cb.get("groups", {}).get("G2C"):
        L.append(group_box(cb, "G2C", "The clocks count as their own bucket in the combined view."))
    bt = ck.get("by_type_bn", {})
    L.append(f"Fixed bills total \\${num(ck.get('fixed_charges_bn'), 1)}bn, centred {num(ck.get('centre_years'), 1)} years out: "
             + ", ".join(f"{esc(k.lower())} \\${num(v, 1)}bn" for k, v in bt.items()) + ". "
             f"That is {num(ck.get('years_of_ebitdar'), 1)} years of today's EBITDAR; next year's bills take {pct(ck.get('year1_share_of_ebitdar'))} of it.")
    if ck.get("breakeven_margin") is not None:
        be = ck["breakeven_margin"]
        rows = [["Signed contracts (RPO)", f"\\${num(ck.get('rpo_bn'), 1)}bn"],
                ["Where bills centre / where contract cash centres", f"year {num(ck.get('centre_years'), 1)} / year {num(ck.get('contract_centre_years'), 1)}"],
                ["Contracts 99\\% booked by", f"year {num(ck.get('runoff_years'), 0)}"],
                ["Margin needed for contracts to pay every bill", ("over 100\\% (no margin is enough)" if be > 1 else pct(be))],
                ["Company margin (EBITDAR)", pct(ck.get("company_margin"))],
                ["Share of bills paid by contracts at that margin", pct(ck.get("coverage_contracted"))],
                ["Bills due after the contracts end", f"\\${num(ck.get('renewal_dependent_bn'), 1)}bn ({pct(ck.get('renewal_dependent_share'))})"],
                ["\\quad of which debt to refinance", f"\\${num(ck.get('renewal_refinance_bn'), 1)}bn ({pct(ck.get('renewal_refinance_share'))})"],
                ["\\quad of which rent and purchases to recontract", f"\\${num(ck.get('renewal_recontract_bn'), 1)}bn ({pct(ck.get('renewal_recontract_share'))})"],
                ["Revenue to sign after the contracts end", f"{num(ck.get('renewal_revenue_years'), 1)} years of today's revenue"],
                ["Largest running shortfall", f"\\${num(ck.get('largest_shortfall_bn'), 1)}bn"],
                ["Top three customers", pct(ck.get("top3_customers"))]]
        for k, v in ck.get("scenarios", {}).items():
            rows.append([esc(k.replace("_", " ")).capitalize(), f"contracts pay {pct(v['coverage'])}; shortfall \\${num(v['shortfall_bn'], 1)}bn"])
        for k, v in ck.get("margin_sensitivity", {}).items():
            rows.append([f"Share paid by contracts at a {k.split('_')[1]} margin", pct(v)])
        L.append(table(["Measure", "Value"], rows, "lr"))
    else:
        L.append("The company discloses no material signed revenue, so the second clock is today's earnings held flat (chart at the end).")

    L.append("\\subsection*{G2.2 Economic stories and cases}")
    mp = cases.get("modal_path", "")
    cst = cases.get("case_stats", [])
    if cst:
        L.append(f"Cases on the most likely story ({esc(mp)}), stage of the cycle: {esc(cases.get('phase'))}.")
        L.append(table(["Case", "Weight", "Growth / qtr", "Leverage in 1 yr", "Peak leverage", "Lowest liquidity", "Cash runs out", "Refi fails"],
                       [[esc(c["case"].replace("_", " ")), pct(c["weight"]), pct(c["growth_q"], 1), num(c["lev_4"], 1, "x"), num(c["lev_peak"], 1, "x"),
                         bn(c["liq_min"]), num(c["first_shortfall_q"], 0) if c["first_shortfall_q"] else "no", num(c["first_refi_fail_q"], 0) if c["first_refi_fail_q"] else "no"]
                        for c in cst]))
    L.append(table(["Story", "Chance", "Leverage in 1 yr", "Peak leverage (down)", "Refi fails", "Default chance", "Expected profit (bp/yr)"],
                   [[esc(r["macro_path"].replace("_", " ")), pct(r["p_path"]), num(r["lev_fwd_4"], 1, "x"), num(r["lev_peak_down"], 1, "x"),
                     pct(r["refi_fail_share"]), pct(r["pd_12m"], 1), num(al.get("by_path_bp_year", {}).get(r["macro_path"]), 0)]
                    for r in cases.get("by_path", [])]))

    L.append("\\subsection*{G2.3 Relative value and the pair}")
    L.append(f"Fair line: {esc(rvo.get('fair_line'))}. 5-year spread {num(rvo.get('spread_5y_bp'), 0)} bp against a fair {num(rvo.get('fair_5y_bp'), 0)} bp.")
    pe = rvo.get("peers")
    if pe:
        def rel(x):
            return f"{(math.exp(x) - 1) * 100:+.0f}\\%" if x is not None else "n/a"
        src = "S\\&P rating" if pe["rating_source"] == "actual" else "implied by leverage"
        L.append(f"\\textbf{{Against peers.}} Peers are the high yield bonds that traded in {pe['peer_month']} "
                 f"({pe['n_panel_bonds']:,} bonds with leverage on file), in the same 3 to 7 year maturity bucket. "
                 f"Sector: {esc(pe['sector'])}. Rating class: {pe['rating_class']} ({src}). "
                 "A positive value means the issuer pays more than the median peer.")
        L.append(table(["Peer group", "Excess spread to peers (ESP)", "Spread per turn against peers (E13)"],
                       [["Sector and rating", rel(pe.get("esp_sr")), rel(pe.get("e13_sr"))],
                        ["Sector only", rel(pe.get("esp_s")), rel(pe.get("e13_s"))],
                        ["Rating only", rel(pe.get("esp_r")), rel(pe.get("e13_r"))]]))
        if pe.get("cell_esp_sr") != "sr":
            L.append("The sector and rating cell has fewer than five other issuers, so that row uses the "
                     + {"r": "rating", "s": "sector", "all": "whole panel"}.get(pe.get("cell_esp_sr"), "next") + " cell.")
        if pe.get("spider_pct") is not None:
            L.append(f"\\textbf{{SPiDER}} (spread per unit of debt to 10-year average EBITDA; Dynkin et al. 2021, ch. 14): "
                     f"cheaper than {pct(pe['spider_pct'], 0)} of the peer bonds across all sectors, and "
                     f"{rel(pe.get('spider_sr'))} against sector and rating peers. "
                     "It enters the score as E15 at 3\\%. Its edge beyond spread level is small (t 1.3 at 12 months).")
        elif pe.get("spider_note"):
            L.append(f"\\textbf{{SPiDER}}: {esc(pe['spider_note'])}")
        if pe.get("onescore") is not None:
            L.append(f"\\textbf{{OneScore}} (Dynkin et al. 2021, ch. 19): {pct(pe['onescore'], 0)} of the way from the bottom "
                     f"to the top of its sector. It averages two sector ranks: value (ESP, {pct(pe.get('esp_sec'), 0)}) and the "
                     f"stock's 3-month return ({pct(pe.get('emc_3m'), 1)}, rank {pct(pe.get('emc_sec'), 0)}). "
                     "It enters the score as E16 at 4.5\\%.")
    for p in pairs:
        other = p["b"] if p["a"] == t else p["a"]
        por = p.get("price_of_risk", [])
        if por:
            L.append(f"\\textbf{{Against {other}.}} Spreads at 5 years: " + ", ".join(f"{k} {v:,.0f} bp" for k, v in p["s5_bp"].items()) + ".")
            words = {"lev_lease_adj": "turn of leverage", "renewal_dependent_ebitda_years": "year of EBITDA that depends on renewal",
                     "breakeven_margin": "unit of breakeven margin", "duration_gap": "year of clock gap"}
            L.append(table(["Spread per", p["a"], p["b"], "Cheaper"],
                           [[words.get(r["metric"], r["metric"]), num(r.get(f"bp_per_unit_{p['a']}"), 0), num(r.get(f"bp_per_unit_{p['b']}"), 0), r["cheaper"]] for r in por]))
        a = p["alpha"]
        hl = a.get("half_life_weeks")
        L.append(f"The fair line favours long {a['long']}, short {a['short']}: a gap of {num(a.get('gap_bp'), 0)} bp, which halves in about "
                 f"{num(float(hl) if hl not in (None, 'nan') else None, 0)} weeks on six months of trades. "
                 + (f"Under the stories the pair earns {', '.join(f'{esc(k)} {v:+.0f}' for k, v in p['pair_alpha_by_path_bp'].items())} bp a year; "
                    f"weighted {p['pair_alpha_weighted_bp']:+.0f} bp before costs." if p.get("pair_alpha_by_path_bp") else ""))

    L.append("\\subsection*{G2.4 Expected profit and price against our view}")
    L.append(f"Hedged 5-year bond over six months: {num(al.get('weighted_bp_year_before_cost'), 0)} bp a year before trading costs, "
             f"{num(al.get('weighted_bp_year_after_cost'), 0)} bp after. It {'beats' if al.get('passes_cost_test') else 'does not beat'} costs. "
             f"The expected default loss is charged on the price paid: {pct(al.get('l_def'))} of it in default, not "
             f"{pct(al.get('lgd_face_v0'))} of face.")
    rows = []
    for r in g.get("table", []):
        def f(v, row=r["row"]):
            if v is None:
                return "open"
            if isinstance(v, str):
                return esc(v)
            return pct(v, 1) if "probability" in row.lower() or "default chance" in row.lower() else (f"{v:,.0f}" if "bp" in row else f"{v:.2f}")
        rows.append([esc(r["row"]), f(r["market_implies"]), f(r["our_view"]), f(r["gap"]), f(r["noise"]),
                     ("yes" if r["passes_G1"] else "no") if r.get("tested", True) else "not tested"])
    L.append(table(["Question", "Price assumes", "Our view", "Gap", "Noise", "Gap bigger than noise?"], rows, "p{5.2cm}rrrrl"))
    L.append("The first row turns the spread into a default chance with a fixed price of risk. That is not a real default "
             "chance, so it is shown but not tested. The breakeven row asks a cleaner question: is our default chance below "
             "the rate at which the spread only just pays for default losses?")

    L.append("\\subsection*{G2.5 Risks and the health panel}")
    reds = [r for r in panel if r["band"] == "red"]
    if reds:
        L.append("\\begin{itemize}" + "".join(f"\\item {RISK_TEXT[r['metric']][0]} Tracked by: {METRIC_WORDS[r['metric']][0].lower()} "
                                               f"({num(r['value'], 2)}). Resolves when: {RISK_TEXT[r['metric']][1]}." for r in reds) + "\\end{itemize}")
    colour = {"red": "\\textcolor{bad}{red}", "amber": "\\textcolor{amber}{amber}", "green": "\\textcolor{good}{green}", "n/a": "n/a"}
    L.append(table(["Measure", "Value", "Band"], [[METRIC_WORDS[r["metric"]][0], num(r["value"], 2), colour[r["band"]]] for r in panel], "lrl"))

    # ------------------------------------------------------------------ G3
    L.append("\\section*{G3. Credit skills: the lender's checklists applied to a public bond}")
    if cb.get("groups"):
        L.append(group_box(cb, "G3", f"Watchlist: {esc(ev.get('watch_tier', 'n/a'))}."))
    L.append("\\subsection*{G3.1 Add-backs and their cash effect}")
    if "addback_ltm_m" in nm:
        fl = nm.get("addback_flags", {})
        L.append(f"Reported EBITDA over the last 12 months is {bn(nm.get('ebitda_rep_ltm_m'))}. The company's own measure adds back "
                 f"{bn(nm.get('addback_ltm_m'))} of one-off items to reach {bn(nm.get('ebitda_adj_ltm_m'))}: {pct(nm.get('addback_category_share'), 1)} "
                 "of reported EBITDA (a negative figure is a one-off gain taken out). "
                 + ("This is above the 5\\% line the lender's checklist sets for one item. " if fl.get("single_above_5pct") else "This is under the 5\\% line for one item. ")
                 + ("The total is above 10\\%. " if fl.get("total_above_10pct") else "")
                 + (f"Add-backs appear in each of the last {nm.get('addback_recurring_quarters')} quarters, so they are not one-offs. "
                    if fl.get("recurring") else "They do not recur in three quarters running. ")
                 + f"If every add-back were paid in cash, free cash flow would be {bn(nm.get('fcf_if_addbacks_cash_m'))}. "
                 f"The two roads to free cash flow (the EBITDA bridge, {bn(nm.get('fcf_waterfall_m'))}; operating cash flow less capital "
                 f"spending, {bn(nm.get('fcf_ocf_route_m'))}) differ by {pct(nm.get('fcf_check_gap'))} of EBITDA"
                 + (": above the 10\\% tolerance, so an earnings-quality flag is raised." if nm.get("fcf_check_flag") else ": within the 10\\% tolerance.")
                 + " The add-back table by category is an open question: the data has one total line.")
    L.append("\\subsection*{G3.2 Covenant headroom}")
    covs = cs.get("covenants", [])
    if covs:
        L.append("The filing states these maintenance tests. We test them on our own ratio, which uses our EBITDA, not the "
                 "covenant's, and the whole group.")
        L.append(table(["Test", "Level", "Our ratio", "Headroom", "Band", "Notes"],
                       [[esc(c["name"][:48]), num(c["level"], 2), num(c["actual"], 2), pct(c["headroom"]), esc(c["tier"]),
                         esc("; ".join([x for x, y in (("only tested below a trigger", c["springing"]),
                                                       ("binds a subsidiary group", c["subsidiary"]),
                                                       ("our ratio is only a bound for this test", not c.get("comparable", True))) if y]
                                       + [c.get("basis", "")]))]
                        for c in covs], "p{3.8cm}rrrp{1.9cm}p{4.4cm}"))
        if cs.get("headroom_H") is not None:
            L.append(f"Tightest headroom we can read: {pct(cs.get('headroom_H'))} ({esc(cs.get('headroom_tier'))}). The lender's bands: "
                     "20\\% or more is comfortable, 10\\% to 20\\% needs attention, under 10\\% is tight.")
        else:
            L.append("No test can be read on our own ratio: each one binds a narrower group of debt or needs the credit lines. "
                     "Headroom stays an open question; it does not move the watchlist.")
    else:
        L.append("The 10-Q and 10-K text state no maintenance test level. Public bonds are often tested only when the company "
                 "borrows more or pays out cash. Headroom is an open question until the credit agreement is read.")
    L.append("\\subsection*{G3.3 Watchlist and trajectory}")
    reasons = ev.get("watch_reasons", [])
    L.append(f"Watchlist tier: \\textbf{{{esc(ev.get('watch_tier', 'n/a'))}}}"
             + (f" because {esc('; '.join(reasons))}." if reasons else ": no trigger is met.")
             + f" EBITDA against the same months a year earlier: {pct(ev.get('ebitda_vs_prior_year'), 1)} (no plan is public, so last year stands in for it)."
             + (f" Open: {esc('; '.join(ev.get('watch_open')))}." if ev.get("watch_open") else ""))
    trj = ev.get("trajectory", {})
    if trj:
        L.append(table(["Measure", "Direction", "How much weight", "Change on a year earlier, last quarter"],
                       [[esc(k), esc(v["call"]), esc(v["weight"]), pct(v.get("yoy_last"), 1)] for k, v in trj.items()], "llll"))
        L.append("One quarter is an observation, two a data point, three or four a trend."
                 + (" The measures point different ways; the memo must explain why." if ev.get("trajectory_conflict") else ""))
    L.append("\\subsection*{G3.4 Memo structure check}")
    mc = cb.get("memo_checks", [])
    if mc:
        L.append(table(["Section", "Requires", "Status"],
                       [[esc(r["section"]), esc(r["requires"]), "\\textcolor{good}{pass}" if r["status"] == "pass" else "\\textcolor{amber}{open}"]
                        for r in mc], "lp{9cm}l"))
    nt = cb.get("not_transferable", [])
    if nt:
        L.append("\\textbf{Rules that do not transfer to a public bond:}\\begin{itemize}"
                 + "".join(f"\\item {esc(b)} ({esc(a)})" for a, b in nt) + "\\end{itemize}")

    # ------------------------------------------------------------------ G4
    L.append("\\section*{G4. Books: Kricheff, and Ganguin and Bilardello (S\\&P)}")
    sp, kr = cs.get("sp", {}), cs.get("kricheff", {})
    if cb.get("groups"):
        L.append(group_box(cb, "G4", f"S\\&P anchor class: {esc(sp.get('sp_anchor_class', 'n/a'))}."))
    kb = nm.get("kricheff_bridge_m", {})
    if kb:
        L.append("\\subsection*{G4.1 Kricheff's cash-flow bridge and ratio set}")
        L.append(table(["Line (last 12 months)", "Value"], [
            ["Adjusted EBITDA", bn(kb.get("ebitda_adj"))], ["less capital spending", bn(kb.get("capex"))],
            ["less cash interest", bn(kb.get("cash_interest"))], ["less cash taxes", bn(kb.get("cash_taxes"))],
            ["less increase in working capital", bn(kb.get("delta_wc"))], ["\\textbf{Free cash flow}", f"\\textbf{{{bn(kb.get('fcf'))}}}"],
            ["Check: free cash flow before capital spending less operating cash flow", bn(kb.get("cfo_gap"))],
            ["Free cash flow after dividends", "open (dividends not loaded)"]], "lr"))
        L.append(table(["Ratio", "Value", "Ratio", "Value"], [
            ["EBITDA / cash interest", num(kr.get("cash_cov"), 1, "x"), "Debt / EBITDA", num(kr.get("lev_gross"), 1, "x")],
            ["(EBITDA $-$ capex) / interest", num(kr.get("after_capex_cov"), 1, "x"), "Net debt / EBITDA", num(kr.get("lev_net"), 1, "x")],
            ["(EBITDA $-$ maintenance capex) / interest", num(kr.get("after_maint_capex_cov"), 1, "x"), "Free cash flow / debt", pct(kr.get("fcf_to_debt"), 1)],
            ["EBITDA / debt (highest rate at 1x cover)", pct(kr.get("ebitda_to_debt"), 1), "Market value / EBITDA", num(kr.get("ev_to_ebitda"), 1, "x")],
            ["Equity cushion (1 $-$ debt / market value)", pct(kr.get("equity_cushion")), "Spread per turn of leverage", f"{num(rvo.get('spt_total'), 0)} bp"],
        ], "lrlr"))
        snap_need = (kb.get("cfo") or 0) < (kb.get("capex") or 0)
        L.append(f"Kricheff's snapshot rule: {'operating cash flow does not cover capital spending, so the issuer lives on the capital markets and needs the detailed liquidity work of section G1.4' if snap_need else 'operating cash flow covers capital spending'}. "
                 f"Spread per turn compares the bond with the run's median of {num(cb.get('spt_median_bp'), 0)} bp a turn. "
                 "Kricheff warns that a high spread per turn can mean weak cash flow, not value; read it with free cash flow / debt. "
                 "The book measures leverage through each bond's rank; with no face by rank, total leverage stands in.")
    if sp:
        L.append("\\subsection*{G4.2 The S\\&P risk profiles and the rating anchor}")
        rt, fp, bp_ = sp.get("ratios", {}), sp.get("financial_parts", {}), sp.get("business_parts", {})
        L.append("S\\&P adds leases to debt and scores each ratio against the median of each rating class (CreditStats "
                 "2002, from the book). Scores run from 1 (safest) to 10 (default).")
        L.append(table(["Ratio", "Value", "Score", "BB median", "B median"], [
            ["Debt / (debt + market value of equity)", pct((rt.get("debt_to_cap") or 0) / 100), num(fp.get("debt_to_cap"), 1), "57.5\\%", "78.5\\%"],
            ["Funds from operations / debt", pct((rt.get("ffo_to_debt") or 0) / 100), num(fp.get("ffo_to_debt"), 1), "19.5\\%", "10.8\\%"],
            ["Free operating cash flow / debt", pct((rt.get("focf_to_debt") or 0) / 100), num(fp.get("focf_to_debt"), 1), "8.5\\%", "2.5\\%"],
            ["EBITDA / interest (with lease interest)", num(rt.get("ebitda_cov"), 1, "x"), num(fp.get("ebitda_cov"), 1), "3.2x", "1.8x"],
            ["EBITDA margin", pct(rt.get("ebitda_margin")), num(fp.get("profitability"), 1), "", ""],
        ], "lrrrr"))
        L.append(f"Financial risk score {num(sp.get('sp_financial_score'), 1)}. Business risk score {num(sp.get('business_risk_score'), 1)}: "
                 f"industry {num(bp_.get('industry'), 0)}, steadiness of sales {num(bp_.get('sales_consistency'), 0)} (year-on-year growth "
                 f"varies by {pct(sp.get('revenue_yoy_sd'), 1)}), customer spread {num(bp_.get('diversity'), 0)}. "
                 f"The book puts {pct(sp.get('w_business'))} of the weight on business risk for this class, so the default risk score is "
                 f"{num(sp.get('sp_default_risk_score'), 1)}: the \\textbf{{{esc(sp.get('sp_anchor_class'))}}} class. "
                 + (f"Across the run, a company with this score pays about {num(cb.get('sp_fair_bp'), 0)} bp; the bond pays "
                    f"{num(rvo.get('spread_5y_bp'), 0)} bp. " if cb.get("sp_fair_bp") else "The line from score to spread across the run "
                    "did not slope upward, so it gives no estimate. ")
                 + "The 2005 edition has no modern anchor table; its own weighting table stands in for it.")

    # ------------------------------------------------------------------ end
    L.append("\\section*{Coming events, open questions, and the record}")
    L.append("\\begin{itemize}" + "".join(f"\\item {esc(e['event'])}: {esc(e.get('date') or '')}{' (estimate)' if e.get('confirmed') is False else ''}"
                                           f"{' - ' + bn(e['amount_m']) if e.get('amount_m') else ''}." for e in ev.get("events", [])) + "\\end{itemize}")
    oq = []
    for k in ("11", "5", "4", "15", "8", "3", "2", "7", "9", "10", "12"):
        for q in st.get(k, {}).get("open_questions", []):
            if q not in oq:
                oq.append(q)
    L.append("\\textbf{Open questions, most important first:}\\begin{enumerate}" + "".join(f"\\item {esc(q)}" for q in oq[:10]) + "\\end{enumerate}")
    L.append("\\textbf{Record (filled at exit):} exit date; return against the rating-matched index; worst point against the index; reason; the rule that would have helped.")
    L.append("\\newpage")
    for fig, cap in ((f"clocks_all_{t}.png", "The two clocks (section G2.1)."), (f"scenarios_{t}.png", "The company under each economic story (section G2.2).")):
        if (FIGS / fig).exists():
            L.append(f"\\begin{{figure}}[H]\\centering\\includegraphics[width=0.95\\linewidth]{{figures/{fig}}}\\caption*{{{cap}}}\\end{{figure}}")
    for p in pairs:
        fig = f"rv_{p['a']}_{p['b']}.png"
        if (FIGS / fig).exists():
            L.append(f"\\begin{{figure}}[H]\\centering\\includegraphics[width=0.85\\linewidth]{{figures/{fig}}}\\caption*{{The pair (section G2.3).}}\\end{{figure}}")
    L.append("\\newpage")
    return "\n".join(L)


def main() -> None:
    run = json.loads((PROC / "_run.json").read_text())
    ds = [json.loads((PROC / f"{t}.json").read_text()) for t in run["tickers"] if (PROC / f"{t}.json").exists()]
    m = run["macro"]
    check = [f"{d['ticker']} & " + " & ".join(MARK.get(d["steps"].get(k, {}).get("status", "blocked"), "blocked") for k in STEP_NAMES) + " \\\\" for d in ds]
    head = " & ".join(f"\\rotatebox{{90}}{{{v}}}" for v in STEP_NAMES.values())
    paths = "\n".join(f"{esc(p['name'])} & {pct(p['prob'])} & {pct(p['gdp'], 1)} & {pct(p['policy_q8'], 1)} & {p['hy_spread'] * 1e4:.0f} \\\\" for p in m["paths"])
    methods = "\n".join(f"{a} & {b} & {c} \\\\" for a, b, c in METHODS)
    rk = sorted([d for d in ds if d["steps"].get("14", {}).get("outputs", {}).get("groups")],
                key=lambda d: d["steps"]["14"]["outputs"]["rank"])

    def C(d):
        return d["steps"]["14"]["outputs"]
    gw = run.get("group_weights", {})
    rank_table = table(["Rank", "Issuer", "Combined", "Calibrated",
                        *[f"{BUCKET_LABEL[k]} ({gw.get(k, 0) * 100:.0f}\\%)" for k in BUCKET_ORDER], "Cases", "Best alt.", "Gate"],
                       [[C(d)["rank"], d["ticker"], f"\\textbf{{{bp(C(d)['combined_after_cost'])}}}",
                         bp(d["steps"].get("14b", {}).get("outputs", {}).get("alpha_sized")),
                         *[bp(C(d)["groups"][gg]["alpha_bp_yr"]) for gg in BUCKET_ORDER],
                         bp(C(d)["anchor_after_cost"]), esc(d["steps"].get("15", {}).get("outputs", {}).get("replaces_position", "n/a")),
                         plain_call(d["steps"].get("11", {}).get("outputs", {})).split(".")[0]] for d in rk], "rlrrrrrrrrll"
                       ).replace("\\tabcolsep}{3.5pt}", "\\tabcolsep}{2pt}")
    sz0 = rk[0]["steps"].get("14b", {}).get("outputs", {}) if rk else {}
    wtxt = ", ".join(f"{GROUPS[k][0].lower()} {gw.get(k, 0) * 100:.1f}\\%" for k in BUCKET_ORDER)
    tex = rf"""\documentclass[11pt,a4paper]{{article}}
\usepackage[margin=2cm]{{geometry}}
\usepackage{{booktabs,xcolor,hyperref,enumitem,graphicx,float,caption,array}}
\definecolor{{good}}{{HTML}}{{2E7D4F}}\definecolor{{amber}}{{HTML}}{{B07D1A}}\definecolor{{bad}}{{HTML}}{{B5403A}}
\setlist{{itemsep=1pt,topsep=2pt}}\emergencystretch=3em
\title{{Issuer memos: one analyst, four groups of methods}}
\author{{FundamentalQuantmental HY Analyst: one memo per company, written by the process}}
\date{{Data as known on {run['decision']}}}
\begin{{document}}
\maketitle
\noindent\fcolorbox{{gray}}{{gray!6}}{{\parbox{{\dimexpr\linewidth-2\fboxsep-2\fboxrule-1pt}}{{\sloppy
\textbf{{How these memos are made.}} One analyst runs every company through four groups of methods. Group 1 is the core process: Gatto's seven steps, our method, our rulebook and the relative value paper. Group 2 is the set of methods we built: the two clocks, the fair line and the pair, the economic stories, the gate and the health panel. Group 3 applies the lender's checklists (the credit skills) where public filings allow. Group 4 applies two books: Kricheff, and Ganguin and Bilardello (S\&P). Each group gives its own estimate of expected profit above a hedge, in bp a year. The combined estimate weighs five buckets as the user set them ({wtxt}) and pays trading costs once. Each step is \textcolor{{good}}{{done}}, \textcolor{{amber}}{{partial}} (it ran but needs an analyst input), or \textcolor{{bad}}{{blocked}}. Missing inputs appear as open questions.}}}}

\section*{{All issuers, ranked by the combined view}}
The combined column is after trading costs; the five bucket columns (with their weights) are before costs, in bp a year. ``Cases'' is the weighted cases and stories after costs. ``Best alt.'' is the position the same money would rather hold (cash when nothing in the run beats it). \textbf{{Alpha sizes are uncalibrated}}: in the backtest, realised alpha was about {num(sz0.get('mz_b'), 2)} times the predicted alpha, so ``Calibrated'' multiplies the combined number by that slope (decision page 2026-10-22-alpha-backtest-design). The slope is not significant, so the numbers rank the issuers but do not size positions.
{rank_table}

\section*{{What each part of a memo answers}}
\begin{{center}}\footnotesize\begin{{tabular}}{{@{{}}lp{{7.2cm}}p{{6.4cm}}@{{}}}}\toprule Memo part & What it answers & Where it comes from \\\midrule
{methods}
\bottomrule\end{{tabular}}\end{{center}}

\section*{{Which steps ran}}
\textcolor{{good}}{{\textbf{{D}}}} done, \textcolor{{amber}}{{\textbf{{P}}}} partial (ran; needs an analyst input), \textcolor{{bad}}{{\textbf{{B}}}} blocked.
\begin{{center}}\footnotesize
\begin{{tabular}}{{@{{}}l{'c' * len(STEP_NAMES)}@{{}}}}\toprule
 & {head} \\\midrule
{chr(10).join(check)}
\bottomrule\end{{tabular}}\end{{center}}

\section*{{The economic stories used in every memo}}
Probabilities combine economists' forecasts (Philadelphia Fed survey, Fed projections, Treasury market) with the stage of the cycle ({esc(m['phase'])}).
\begin{{center}}\footnotesize\begin{{tabular}}{{@{{}}lrrrr@{{}}}}\toprule Story & Chance & GDP growth & Fed rate in 2 years & High yield spread (bp) \\\midrule
{paths}
\bottomrule\end{{tabular}}\end{{center}}
\newpage
\section*{{Words used}}
\begin{{description}}
{chr(10).join(f"\\item[{k}] {v}" for k, v in GLOSSARY)}
\end{{description}}
\newpage
{chr(10).join(memo(d) for d in ds)}
\end{{document}}
"""
    OUT.write_text(tex)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
