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
{chr(10).join(page(d) for d in ds)}
\end{{document}}
"""
    OUT.write_text(tex)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
