"""Write docs/writeup/clocks_all.tex from data/raw/clocks/<ticker>.json (methodology Section 4.7).

Run `scripts/clock_case.py --tickers ...` first (it writes the JSON and the figures), copy the figures to
docs/writeup/figures/clocks_all_<ticker>.png, then:
    PYTHONPATH=. python3 scripts/clocks_report.py --tickers CRWV ORCL HCA THC CCL NCLH MGM WYNN
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "clocks"
SCEN = ROOT / "data" / "raw" / "scenarios"
RVJ = ROOT / "data" / "raw" / "rv" / "rv_pairs.json"
OUT = ROOT / "docs" / "writeup" / "clocks_all.tex"


def nz(x):
    return x is not None and x == x


def load(t: str) -> dict:
    d = json.loads((RAW / f"{t}.json").read_text())
    i, m = d["inputs"], d["metrics"]
    eb = (i.get("ltm_ebitda") or {}).get("value")
    rent = (i.get("annual_lease_cost") or {}).get("value") or 0.0
    d["ebitdar"] = eb + rent if eb else None
    d["years_ebitdar"] = m["obligations_total"] / d["ebitdar"] if d["ebitdar"] else None
    d["contract"] = d["revenue_clock"] == "built"
    return d


def fmt_bn(x):
    return f"\\${x / 1e3:,.0f}bn" if nz(x) else "n/a"


def page(d: dict) -> str:
    t, m, n = d["ticker"], d["metrics"], d["notes"]
    lines = [f"\\section{{{d['name']} ({t}), filing of {d['as_of']}}}",
             f"\\begin{{figure}}[H]\\centering\\includegraphics[width=\\linewidth]{{figures/clocks_all_{t}.png}}\\end{{figure}}",
             "\\begin{itemize}"]
    lines.append(f"\\item \\textbf{{Fixed charges:}} {fmt_bn(m['obligations_total'])}, centred on year {m['dur_obligations']:.1f}. "
                 f"That is {d['years_ebitdar']:.1f} years of today's EBITDAR." if d["years_ebitdar"] else
                 f"\\item \\textbf{{Fixed charges:}} {fmt_bn(m['obligations_total'])}, centred on year {m['dur_obligations']:.1f}.")
    if d["contract"]:
        be = m["breakeven_margin"]
        lines.append(f"\\item \\textbf{{Signed contracts:}} {fmt_bn(d['rpo_total'])}. Breakeven margin {be:.2f}"
                     + (" (no margin is enough)." if be > 1 else f" against a company margin of {m['ebitdar_margin']:.0%}."))
        lines.append(f"\\item \\textbf{{Renewal bet:}} {m['renewal_dependent_share']:.0%} of charges "
                     f"({fmt_bn(m['renewal_dependent_amount'])}) fall due after the contracts end; "
                     f"{m['renewal_revenue_years']:.1f} years of current revenue must be signed to pay them.")
    else:
        why = "no signed revenue disclosed" if d["revenue_clock"].startswith("skipped") else "signed revenue under one year of sales"
        lines.append(f"\\item \\textbf{{No contract clock}} ({why}). The green line is today's EBITDAR held flat, not a contract.")
    lines.append(f"\\item \\textbf{{Debt schedule:}} {n.get('debt_ladder', 'as filed').replace('$', '')}; "
                 f"balance-sheet debt {n.get('balance_sheet_debt', 'n/a')}.")
    lines.append("\\end{itemize}\\newpage")
    return "\n".join(lines)


def scenario_page(t: str) -> str:
    """Scenario page for one issuer from data/raw/scenarios/<t>.json (methodology Section 5.4, 7.5; F4, F6)."""
    f = SCEN / f"{t}.json"
    if not f.exists():
        return ""
    d = json.loads(f.read_text())
    rows = []
    for r in d["table"]:
        rows.append(f"{r['macro_path'].replace('_', ' ')} & {r['p_path']:.0%} & {r['lev_fwd_4']:.1f}x & {r['lev_peak_down']:.1f}x & "
                    f"{d['refi_score_by_path'][r['macro_path']]} & {r['p_refi_4']:.0%} & {r['refi_fail_share']:.0%} & "
                    f"{r['pd_12m']:.1%} & {r['alpha'] / 0.5 * 1e4:+.0f} \\\\".replace("%", "\\%"))
    a = d["alpha"]
    pts = d["refi_points"]
    have = [k.replace("_", " ") for k in ("rating_proxy", "recent_raise") if pts.get(k)]
    return f"""\\section*{{{d['name']} ({t}): scenarios under each macro path}}
\\begin{{figure}}[H]\\centering\\includegraphics[width=\\linewidth]{{figures/scenarios_{t}.png}}\\end{{figure}}
\\begin{{center}}\\small
\\begin{{tabular}}{{@{{}}lrrrrrrrr@{{}}}}\\toprule
Path & Prob. & Lev. 4q & Peak lev. (down) & F4 score & Wall risk & Refi fails & PD 12m & Alpha (bp/yr) \\\\\\midrule
{chr(10).join(rows)}
\\bottomrule
\\end{{tabular}}
\\end{{center}}
\\begin{{itemize}}
\\item \\textbf{{Weighted expected alpha}}, hedged 5-year bond, 6-month horizon: {a['alpha_w'] / 0.5 * 1e4:+.0f} bp a year before cost,
{a['alpha_net_bp_ann']:+.0f} bp after a {d['v0']['bid_ask_bp']:.0f} bp bid-ask round trip. Framework F9 G3 (alpha after cost above zero): {'passes' if a['passes_g3'] else 'fails'}.
\\item \\textbf{{Inputs}}: archetype {d['archetype']}; 5-year spread {d['s5'] * 1e4:.0f} bp against a fair {d['fair_s5'] * 1e4:.0f} bp (pair report fair line);
starting growth {d['info']['g_q']:.1%} a quarter; {d['info']['maturing_in_8q']:,.0f} of {d['info']['debt_total']:,.0f} debt due inside 8 quarters.
F4 points held at every path: {', '.join(have) if have else 'none'}.
\\item \\textbf{{Read with care}}: fair spread, default probability, and refinance access follow the v0 rules of
\\texttt{{docs/decisions/2026-10-22-issuer-scenario-defaults.md}}. Under spread-proportional pricing a mispricing scales with the market,
so the stress paths enlarge it; real stress often widens a gap before it closes.
\\end{{itemize}}
\\newpage""".replace("%", "\\%") if False else _scen_tex(d, t, rows, a, have)


def _scen_tex(d, t, rows, a, have) -> str:
    pct = lambda x: f"{x:.1%}".replace("%", "\\%")
    return (f"\\section*{{{d['name']} ({t}): scenarios under each macro path}}\n"
            f"\\begin{{figure}}[H]\\centering\\includegraphics[width=\\linewidth]{{figures/scenarios_{t}.png}}\\end{{figure}}\n"
            "\\begin{center}\\footnotesize\\setlength{\\tabcolsep}{4pt}\n\\begin{tabular}{@{}lrrrrrrrr@{}}\\toprule\n"
            "Path & Prob. & Lev. 4q & Peak lev. (down) & F4 score & Wall risk & Refi fails & PD 12m & Alpha (bp/yr) \\\\\\midrule\n"
            + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n\\end{center}\n\\begin{itemize}\n"
            f"\\item \\textbf{{Weighted expected alpha}}, hedged 5-year bond, 6-month horizon: {a['alpha_w'] / 0.5 * 1e4:+.0f} bp a year before cost, "
            f"{a['alpha_net_bp_ann']:+.0f} bp after a {d['v0']['bid_ask_bp']:.0f} bp bid-ask round trip. Framework F9 G3 (alpha after cost above zero): "
            f"{'passes' if a['passes_g3'] else 'fails'}.\n"
            f"\\item \\textbf{{Inputs}}: archetype {d['archetype']}; 5-year spread {d['s5'] * 1e4:.0f} bp against a fair {d['fair_s5'] * 1e4:.0f} bp "
            f"(pair report fair line); starting growth {pct(d['info']['g_q'])} a quarter; {d['info']['maturing_in_8q']:,.0f} of "
            f"{d['info']['debt_total']:,.0f} (USD m) of debt due inside 8 quarters. F4 points held on every path: {', '.join(have) if have else 'none'}.\n"
            "\\item \\textbf{Read with care}: fair spread, default probability, and refinance access follow the v0 rules of "
            "\\texttt{docs/decisions/2026-10-22-issuer-scenario-defaults.md}. Under spread-proportional pricing a mispricing scales "
            "with the market, so the stress paths enlarge it; real stress often widens a gap before it closes.\n"
            "\\end{itemize}\n\\newpage")


def macro_box() -> str:
    if not RVJ.exists():
        return ""
    m = json.loads(RVJ.read_text()).get("macro")
    if not m:
        return ""
    rows = "\n".join(f"{p['name'].replace('_', ' ')} & {p['prob']:.0%} & {p['gdp']:.1%} & {p['policy_q8']:.1%} & {p['y10_q8']:.1%} & "
                      f"{p['hy_spread'] * 1e4:.0f} \\\\".replace("%", "\\%") for p in m["paths"])
    return ("\\section*{The macro paths behind every scenario page}\n"
            f"Phase {m['phase'].replace('_', ' ')} (from the F6 indicators with data). Sources: SPF, FOMC SEP, Treasury forwards, TRACE high yield level "
            f"({m['s_index_now'] * 1e4:.0f} bp).\n"
            "\\begin{center}\\small\n\\begin{tabular}{@{}lrrrrr@{}}\\toprule\n"
            "Path & Probability & GDP (avg) & Policy rate, 2 years & 10y yield, 2 years & HY spread (bp) \\\\\\midrule\n"
            + rows + "\n\\bottomrule\n\\end{tabular}\n\\end{center}\n\\newpage\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", nargs="+", default=["CRWV", "ORCL", "HCA", "THC", "CCL", "NCLH", "MGM", "WYNN"])
    args = ap.parse_args()
    ds = [load(t) for t in args.tickers]
    rows = []
    for d in ds:
        m = d["metrics"]
        be = f"{m['breakeven_margin']:.2f}" if d["contract"] else "--"
        rd = f"{m['renewal_dependent_share']:.0%}".replace("%", "\\%") if d["contract"] else "--"
        ye = f"{d['years_ebitdar']:.1f}" if d["years_ebitdar"] else "n/a"
        rows.append(f"{d['ticker']} & {fmt_bn(m['obligations_total'])} & {m['dur_obligations']:.1f} & {ye} & {be} & {rd} \\\\")
    worst = max((d for d in ds if d["years_ebitdar"]), key=lambda d: d["years_ebitdar"])
    best = min((d for d in ds if d["years_ebitdar"]), key=lambda d: d["years_ebitdar"])
    tex = rf"""\documentclass[11pt,a4paper]{{article}}
\usepackage[margin=2.1cm]{{geometry}}
\usepackage{{booktabs,xcolor,hyperref,enumitem,graphicx,float}}
\setlist{{itemsep=1pt,topsep=2pt}}
\title{{The two clocks, eight issuers}}
\author{{FundamentalQuantmental, HY Analyst, methodology Section 4.7}}
\date{{Filings as known on 18 September 2026}}
\begin{{document}}
\maketitle
\noindent\fcolorbox{{gray}}{{gray!6}}{{\parbox{{\dimexpr\linewidth-2\fboxsep-2\fboxrule}}{{\sloppy%
\textbf{{How to read this.}} Each page puts what the issuer owes each year (rent, debt, interest, purchase commitments) against what pays for it.
Two issuers disclose a large signed contract book (CRWV, ORCL): their green line is contract cash. The others do not: their green line is today's EBITDAR held flat. That line is not a promise; it asks how much of today's earnings the fixed charges take.

\smallskip
\textbf{{The one number to compare across all eight:}} fixed charges in years of today's EBITDAR. {best['ticker']} needs {best['years_ebitdar']:.1f} years; {worst['ticker']} needs {worst['years_ebitdar']:.1f}.}}}}

\begin{{center}}\small
\begin{{tabular}}{{@{{}}lrrrrr@{{}}}}\toprule
Issuer & Fixed charges & Centre (years) & Years of EBITDAR & Breakeven margin & Renewal-dependent \\\midrule
{chr(10).join(rows)}
\bottomrule
\end{{tabular}}
\end{{center}}

\textbf{{Changes against the first CoreWeave and Oracle note.}} This run derives every input from the filings. CoreWeave's interest rate is the cash rate from the loader (4\%) instead of the hand-entered 9\%, and its contract timing comes from the 10-Q text (months 25 to 48, then 49 to 78). Its breakeven margin moves from 1.08 to 1.03 and its renewal-dependent share from 24\% to 31\%.

\textbf{{Fallbacks used.}} HCA tags a debt schedule that is short of its balance-sheet debt; the missing amount is put in ``thereafter''. Tenet discloses signed revenue below one year of sales, so its contract clock is treated as immaterial. Leases that run past 25 years are summed into the last bar, which is hatched.
\newpage
{macro_box()}
{chr(10).join(page(d) + chr(10) + scenario_page(d["ticker"]) for d in ds)}
\end{{document}}
"""
    OUT.write_text(tex)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
