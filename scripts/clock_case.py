"""Cost clock against revenue clock for any ticker (methodology Section 4.7).

Derives every input from the issuer's latest 10-Q or 10-K (XBRL tags and prose), the point-in-time financials
store, and stated defaults (`hy/sources/clock_inputs.py`). An analyst YAML in `data/analyst_inputs/<T>.yaml` overrides
any field. Writes one figure and one JSON per issuer; the JSON maps every input to its source.

Run from the repo root (needs $SEC_USER_AGENT = "Name email" for the SEC archive):
    PYTHONPATH=. python3 scripts/clock_case.py --tickers CRWV ORCL
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib
import matplotlib.ticker

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from hy import clocks
from hy.sources import clock_inputs as ci
from hy.sources import schedules as sc
from hy.sources import xbrl_instance as xi

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
FIG = ROOT / "docs" / "writeup" / "figures"
OUT = RAW / "clocks"
OVERRIDES = ROOT / "data" / "analyst_inputs"
HORIZON = 25


def _v(inputs: dict, key: str) -> Any:
    """Value of an input; accepts (value, source) pairs or bare values."""
    x = inputs.get(key)
    return x[0] if isinstance(x, tuple) and len(x) == 2 and isinstance(x[1], str) else x


def build_case(inputs: dict) -> dict:
    """The Section 4.7 case for one issuer from `clock_inputs.derive_inputs` output.

    Returns the metrics, scenarios, sensitivities, ladders, and the ClockResult under `_res`. When the filer
    discloses no RPO, the revenue clock is skipped: `revenue_clock` says why and only obligation metrics remain.
    """
    cik = _v(inputs, "cik")
    q = xi.load_instance(cik, _v(inputs, "q"), cache_root=RAW)
    k = xi.load_instance(cik, _v(inputs, "k"), cache_root=RAW) if _v(inputs, "k") else None
    as_of = sc.as_of_date(q)
    obligations: dict[str, list] = {}
    notes: dict[str, str] = {}

    op = sc.ladder(q, "operating_lease")
    if op is None and k is not None:
        op = sc.ladder(k, "operating_lease")
    if op is not None:
        # Thereafter: rent continues at the last stated yearly amount until the total is used up.
        tail = clocks.tail_years_run_rate(op.amounts)
        obligations["Leases in force"] = sc.to_buckets(op, tail)
        notes["lease_tail_years"] = f"{tail:.1f}"
    fin = sc.ladder(q, "finance_lease")
    if fin is not None:
        obligations.setdefault("Leases in force", [])
        obligations["Leases in force"] += sc.to_buckets(fin, clocks.tail_years_run_rate(fin.amounts))

    total, lo, hi = sc.lease_not_commenced(q)
    if not np.isnan(total):
        w0, w1 = _v(inputs, "uncommenced_window")
        obligations["Signed leases not yet started"] = clocks.uncommenced(total, w0, w1, _v(inputs, "uncommenced_term"))
        notes["uncommenced_total"] = f"{total:,.0f}"

    debt = sc.ladder(q, "debt")
    shift = 0.0
    if debt is None and k is not None:
        debt = sc.ladder(k, "debt")
        shift = (as_of - sc.as_of_date(k)).days / 365.25  # 10-K ladder, aged to the 10-Q date
    bs_debt, bs_src = sc.balance_sheet_debt(q)
    debt, notes["debt_ladder"] = sc.reconcile_debt(debt, bs_debt)
    notes["balance_sheet_debt"] = f"{bs_debt:,.0f} ({bs_src})"
    if debt is not None:
        dbuckets = [clocks.Bucket(max(0.0, b.start - shift), b.length, b.amount)
                    for b in sc.to_buckets(debt, _v(inputs, "debt_tail_years"))]
        obligations["Debt principal"] = dbuckets
        rate = _v(inputs, "interest_rate")
        if rate is not None:
            obligations["Interest"] = clocks.interest(dbuckets, debt.total, rate, HORIZON)
        else:
            notes["interest"] = "skipped: no interest rate derived or given"

    pur = sc.ladder(q, "purchase")
    if pur is not None:
        obligations["Purchase commitments"] = sc.to_buckets(pur, clocks.tail_years_run_rate(pur.amounts, 2.0))
    elif _v(inputs, "purchase"):
        amt, yrs = _v(inputs, "purchase")
        obligations["Purchase commitments"] = [clocks.Bucket(0.0, yrs, amt)]

    rpo_total = _v(inputs, "rpo_total")
    windows = [tuple(w) for w in (_v(inputs, "rpo_windows") or [])]
    rpo_tail = _v(inputs, "rpo_tail_years")
    has_rpo = rpo_total is not None and rpo_total == rpo_total and rpo_total > 0
    revenue = clocks.rpo(rpo_total, windows, rpo_tail) if has_rpo else []
    ebitda, lease_cost, ltm_rev = _v(inputs, "ltm_ebitda"), _v(inputs, "annual_lease_cost") or 0.0, _v(inputs, "ltm_revenue")
    margin = (ebitda + lease_cost) / ltm_rev if ebitda is not None and ltm_rev else float("nan")
    run_rate = _v(inputs, "run_rate_revenue")
    res = clocks.mismatch(obligations, revenue, margin if margin == margin else 0.0, HORIZON, run_rate)
    m = dict(res.metrics)
    if margin != margin:  # no LTM EBITDA: say so rather than score the contracts at a zero margin
        for key in ("contracted_cash_total", "coverage_contracted", "first_shortfall_year", "max_cum_shortfall",
                    "renewal_revenue_years"):
            m[key] = float("nan")
        notes["margin"] = "missing: " + ci.sources(inputs).get("ltm_ebitda", "no LTM EBITDA")
    m["ebitdar_margin"] = margin
    m["renewal_dependent_years_of_ebitda"] = m["renewal_dependent_amount"] / ebitda if ebitda else float("nan")
    shares = sc.customer_shares(q)
    m.update({f"cust_{k2}": v for k2, v in clocks.concentration(shares).items()})

    scen, sens = {}, {}
    if has_rpo and margin == margin:
        if shares:
            # hy-model-standards rule: the downside comes from the main risk flag (customer concentration).
            # RPO by customer is not disclosed; assume the top customer's RPO share equals its revenue share.
            top = max(shares.values())
            lost = clocks.rpo(rpo_total * (1 - top), windows, rpo_tail)
            scen["top_customer_stops_paying"] = clocks.mismatch(obligations, lost, margin, HORIZON, run_rate).metrics
        extra_lease = _v(inputs, "scenario_extra_lease")
        if extra_lease:
            s0, s1 = extra_lease["window"]
            extra = dict(obligations)
            extra["Signed leases not yet started"] = (obligations.get("Signed leases not yet started", [])
                                                      + clocks.uncommenced(extra_lease["amount"], s0, s1, extra_lease["term"]))
            scen["with_excluded_lease"] = clocks.mismatch(extra, revenue, margin, HORIZON, run_rate).metrics
        sens = {f"margin_{mm:.2f}": clocks.mismatch(obligations, revenue, mm, HORIZON).metrics["coverage_contracted"]
                for mm in (0.2, 0.35, 0.5, round(margin, 2))}
        sens.update({f"rpo_tail_{t}y": clocks.mismatch(obligations, clocks.rpo(rpo_total, windows, t), margin, HORIZON)
                     .metrics["renewal_dependent_share"] for t in (0.5, 2.0, 5.0)})
    if has_rpo:
        revenue_clock = "built" if margin == margin else "built without margin metrics: " + notes["margin"]
    else:
        for key in ("dur_revenue", "revenue_runoff", "renewal_dependent_share", "renewal_dependent_amount",
                    "coverage_contracted", "breakeven_margin", "duration_gap", "renewal_revenue_years",
                    "first_shortfall_year", "max_cum_shortfall", "renewal_dependent_years_of_ebitda"):
            m[key] = float("nan")
        revenue_clock = "skipped: " + ci.sources(inputs).get("rpo_total", "no RPO disclosed")

    return {"ticker": _v(inputs, "ticker"), "name": _v(inputs, "name"), "as_of": str(as_of.date()),
            "available_at": _v(inputs, "available_at"), "rpo_total": rpo_total, "rpo_windows": windows,
            "revenue_clock": revenue_clock, "rating": _v(inputs, "rating"),
            "metrics": m, "scenarios": scen, "sensitivity": sens, "notes": notes,
            "inputs": {key: {"value": val[0], "source": val[1]} if isinstance(val, tuple) else {"value": val, "source": ""}
                       for key, val in inputs.items()},
            "recourse": _v(inputs, "recourse"),
            "ladders": {"operating_lease": op.amounts if op else None, "debt": debt.amounts if debt else None,
                        "debt_first_length": debt.first_length if debt else None, "debt_shift": shift},
            "_res": res}


COLORS = {"Leases in force": "#E8A33D", "Signed leases not yet started": "#F6D08B", "Debt principal": "#B5403A",
          "Interest": "#E08A84", "Purchase commitments": "#8C8C8C"}


def figure(case: dict, path: Path) -> None:
    """Two panels: annual fixed obligations against contracted cash, then the cumulative gap (Section 4.7)."""
    res: clocks.ClockResult = case["_res"]
    m = case["metrics"]
    y0 = pd.Timestamp(case["as_of"]).year + pd.Timestamp(case["as_of"]).month / 12
    years = y0 + np.arange(HORIZON + 1)
    tot = res.obligations_total
    show = int(min(HORIZON, np.nonzero(tot > 0.005 * tot.max())[0].max() + 1))  # until the obligations end
    fig, (a, b) = plt.subplots(2, 1, figsize=(12, 8.2), height_ratios=[3, 2], sharex=True)
    bottom = np.zeros(HORIZON)
    for name, grid in res.obligations.items():
        a.bar(years[:show], grid[:show] / 1e3, bottom=bottom[:show] / 1e3, width=0.85, color=COLORS[name],
              label=name, align="edge", zorder=2)
        bottom += grid
    cash = res.revenue * res.cash_margin
    xs = np.append(years[:show], years[show])
    low = res.revenue * 0.20
    a.fill_between(xs, np.append(low[:show], low[show - 1]) / 1e3, np.append(cash[:show], cash[show - 1]) / 1e3,
                   step="post", color="#2E7D4F", alpha=0.18, zorder=1,
                   label="Contract cash if the margin is only 20% (stress) up to the company margin")
    a.step(xs, np.append(cash[:show], cash[show - 1]) / 1e3, where="post", zorder=3,
           color="#2E7D4F", lw=2.6, label=f"Cash from signed contracts at company margin ({res.cash_margin:.0%})")
    run = y0 + m["revenue_runoff"]
    a.axvline(run, color="#2E7D4F", ls="--", lw=1.2)
    a.axvspan(run, years[show], color="#B5403A", alpha=0.06)
    top = a.get_ylim()[1]
    after = tot[int(np.ceil(m["revenue_runoff"])):show]
    y_txt = (after.max() / 1e3 if len(after) else 0.0) + 0.05 * top  # just above the bars past the runoff
    box = {"facecolor": "white", "edgecolor": "none", "alpha": 0.85, "pad": 1.5}
    a.text(run + 0.15, y_txt + 0.30 * top, f"Contract book gone\n(99% recognised by {run:.0f})", color="#2E7D4F",
           fontsize=9, va="bottom", bbox=box)
    a.text(run + 0.15, y_txt, f"Renewal-dependent:\n${m['renewal_dependent_amount'] / 1e3:,.0f}bn of fixed charges\n"
           f"({m['renewal_dependent_share']:.0%} of the total,\n{m['renewal_dependent_years_of_ebitda']:.1f} years of today's EBITDA)",
           color="#B5403A", fontsize=9, va="bottom", bbox=box)
    a.set_ylabel("USD bn per year")
    be = m["breakeven_margin"]
    be_txt = "no margin is enough" if be > 1 else f"needs a {be:.0%} margin"
    a.set_title(f"{case['name']}: what is owed each year against what signed contracts pay\n"
                f"Fixed charges centre on year {m['dur_obligations']:.1f}, contract cash on year "
                f"{m['dur_revenue']:.1f}. To pay every charge from signed contracts: {be_txt}.", fontsize=11, loc="left")
    a.legend(fontsize=8, loc="upper left", bbox_to_anchor=(1.01, 1.0), frameon=False)
    gap = np.cumsum(cash) - np.cumsum(res.obligations_total)
    b.fill_between(years[:show] + 0.5, 0, gap[:show] / 1e3, where=gap[:show] < 0, color="#B5403A", alpha=0.35, step=None)
    b.fill_between(years[:show] + 0.5, 0, gap[:show] / 1e3, where=gap[:show] >= 0, color="#2E7D4F", alpha=0.35)
    b.plot(years[:show] + 0.5, gap[:show] / 1e3, color="black", lw=1.2)
    b.axhline(0, color="black", lw=0.6)
    i = int(np.argmin(gap[:show]))
    if gap[i] < 0:
        b.annotate(f"Largest shortfall ${m['max_cum_shortfall'] / 1e3:,.0f}bn:\nmust come from new contracts,\nrenewals, or new debt",
                   (years[i] + 0.5, gap[i] / 1e3), xytext=(years[0] + 0.3, gap[i] / 1e3 * 0.75), fontsize=9,
                   arrowprops={"arrowstyle": "->", "lw": 0.8})
    b.set_ylabel("Cumulative cash from contracts\nminus fixed charges, USD bn", fontsize=9)
    b.set_xlabel("Year")
    for ax in (a, b):
        ax.spines[["top", "right"]].set_visible(False)
    b.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
    fig.text(0.01, 0.005, f"Source: {case['name']} SEC filings as of {case['as_of']} (XBRL), hy/clocks.py. "
             "Assumptions listed in the write-up.", fontsize=7, color="#555")
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(path, dpi=160)
    plt.close(fig)


def figure_obligations(case: dict, path: Path) -> None:
    """Cost clock only, for a filer with no signed revenue (RPO): fixed charges against today's EBITDAR held flat.

    The flat line is not contracted. It answers a narrower question: if earnings stay where they are, how much of
    them do the fixed charges take each year? Intuition: without a contract book, today's earnings are the only clock.
    """
    res: clocks.ClockResult = case["_res"]
    inp = case["inputs"]
    ebitda = (inp.get("ltm_ebitda") or {}).get("value")
    rent = (inp.get("annual_lease_cost") or {}).get("value") or 0.0
    if not ebitda:
        print(f"{case['ticker']}: no cost-clock figure; no LTM EBITDA")
        return
    ebitdar = ebitda + rent
    y0 = pd.Timestamp(case["as_of"]).year + pd.Timestamp(case["as_of"]).month / 12
    years = y0 + np.arange(HORIZON + 1)
    tot = res.obligations_total
    show = int(min(HORIZON, np.nonzero(tot > 0.005 * tot.max())[0].max() + 1))
    fig, (a, b) = plt.subplots(2, 1, figsize=(12, 7.6), height_ratios=[3, 2], sharex=True)
    bottom = np.zeros(HORIZON)
    for name, grid in res.obligations.items():
        a.bar(years[:show], grid[:show] / 1e3, bottom=bottom[:show] / 1e3, width=0.85, color=COLORS[name],
              label=name, align="edge", zorder=2)
        bottom += grid
    a.axhline(ebitdar / 1e3, color="#2E7D4F", ls="--", lw=2, zorder=3,
              label=f"Today's EBITDAR held flat (${ebitdar / 1e3:,.1f}bn): not contracted")
    overflow = show == HORIZON  # the grid sums every year past the horizon into its last bucket
    if overflow:
        a.bar(years[show - 1], tot[show - 1] / 1e3, width=0.85, align="edge", fill=False, hatch="///",
              edgecolor="#555", zorder=4, label=f"{years[show - 1]:.0f} and later, summed (not one year)")
    peak = int(np.argmax(tot[:show - 1] if overflow else tot[:show]))
    share1 = tot[0] / ebitdar
    a.set_title(f"{case['name']}: fixed charges each year against today's earnings (no signed revenue disclosed)\n"
                f"Year 1 takes {share1:.0%} of today's EBITDAR; the peak year ({years[peak]:.0f}) takes "
                f"{tot[peak] / ebitdar:.0%}. All charges equal {tot.sum() / ebitdar:.1f} years of today's EBITDAR.",
                fontsize=11, loc="left")
    a.set_ylabel("USD bn per year")
    a.legend(fontsize=8, loc="upper left", bbox_to_anchor=(1.01, 1.0), frameon=False)
    gap = np.cumsum(np.full(HORIZON, ebitdar)) - np.cumsum(tot)
    b.fill_between(years[:show] + 0.5, 0, gap[:show] / 1e3, where=gap[:show] < 0, color="#B5403A", alpha=0.35)
    b.fill_between(years[:show] + 0.5, 0, gap[:show] / 1e3, where=gap[:show] >= 0, color="#2E7D4F", alpha=0.35)
    b.plot(years[:show] + 0.5, gap[:show] / 1e3, color="black", lw=1.2)
    b.axhline(0, color="black", lw=0.6)
    b.set_ylabel("Cumulative EBITDAR (flat)\nminus fixed charges, USD bn", fontsize=9)
    b.set_xlabel("Year")
    b.text(0.01, 0.92, "Green: today's earnings, if they hold, pay the charges so far. Red: they do not.",
           transform=b.transAxes, fontsize=9, va="top")
    for ax in (a, b):
        ax.spines[["top", "right"]].set_visible(False)
    b.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
    fig.text(0.01, 0.005, f"Source: {case['name']} SEC filings as of {case['as_of']} (XBRL); EBITDA from the "
             "point-in-time loader; hy/clocks.py.", fontsize=7, color="#555")
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(path, dpi=160)
    plt.close(fig)


def summary(case: dict) -> str:
    m, t = case["metrics"], case["ticker"]
    if case["revenue_clock"].startswith("skipped"):
        return (f"{t}: obligations ${m['obligations_total'] / 1e3:,.0f}bn, duration {m['dur_obligations']:.1f}y | "
                f"revenue clock {case['revenue_clock']}")
    return (f"{t}: obligations ${m['obligations_total'] / 1e3:,.0f}bn vs RPO ${m['revenue_total'] / 1e3:,.0f}bn | "
            f"duration {m['dur_obligations']:.1f}y vs {m['dur_revenue']:.1f}y | runoff yr {m['revenue_runoff']:.0f} | "
            f"renewal-dependent {m['renewal_dependent_share']:.0%} (${m['renewal_dependent_amount'] / 1e3:,.0f}bn, "
            f"{m['renewal_dependent_years_of_ebitda']:.1f}x EBITDA) | coverage {m['coverage_contracted']:.2f} | "
            f"max shortfall ${m['max_cum_shortfall'] / 1e3:,.0f}bn | margin {m['ebitdar_margin']:.0%} | "
            f"top3 {m.get('cust_top3', float('nan')):.0%} | breakeven margin {m['breakeven_margin']:.2f} | "
            f"renewal revenue {m['renewal_revenue_years']:.1f}y of run-rate")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tickers", nargs="+", default=["CRWV", "ORCL"])
    ap.add_argument("--as-of", default=None, help="decision time; filings accepted after it are not read")
    ap.add_argument("--overrides", default=str(OVERRIDES))
    args = ap.parse_args()
    FIG.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    for tic in args.tickers:
        tic = tic.upper()
        try:
            inputs = ci.derive_inputs(tic, RAW, args.overrides, args.as_of)
            case = build_case(inputs)
        except LookupError as exc:  # no Compustat or SEC match, or no 10-Q or 10-K (a 20-F filer)
            print(f"{tic}: skipped: {exc}")
            continue
        rpo, run = case["rpo_total"], _v(inputs, "run_rate_revenue")
        material = case["revenue_clock"] == "built" and rpo and run and rpo >= run
        if case["revenue_clock"] == "built" and not material:
            # RPO below one year of revenue: the contract clock says little about this business (decision page 4.7).
            case["revenue_clock"] = f"immaterial: RPO {rpo:,.0f} is below one year of run-rate revenue {run:,.0f}"
        if material:
            figure(case, FIG / f"clocks_{tic}.png")
        else:
            figure_obligations(case, FIG / f"clocks_{tic}.png")
        dump = {k: v for k, v in case.items() if k != "_res"}
        (OUT / f"{tic}.json").write_text(json.dumps(dump, indent=2, default=lambda x: float(x) if isinstance(
            x, (np.floating, np.integer)) else str(x)))
        print(summary(case))
        if case["scenarios"]:
            print("   scenarios:", {k: {"coverage": round(v["coverage_contracted"], 2), "shortfall": round(v["max_cum_shortfall"]),
                                       "renew_share": round(v["renewal_dependent_share"], 2)} for k, v in case["scenarios"].items()},
                  "sens:", {k: round(v, 2) for k, v in case["sensitivity"].items()})
        fallback = ci.defaults_used(inputs)
        if fallback:
            print("   defaults:", fallback)


if __name__ == "__main__":
    main()
