"""Relative value report for pairs of issuers (methodology Sections 4.3, 4.7, 7.2, 7.4, 7.5; framework F5, F9).

For each issuer: lease-adjusted leverage from the filing (F5), the cost-clock metrics when RPO exists (4.7), and
the bond curve from TRACE G-spreads. For each pair: spreads at common tenors, spread per unit of each risk, and a
verdict that holds only where the risk metrics agree (7.4). Across all issuers: a fair-spread line of log 5-year
spread on lease-adjusted leverage (a small 7.2 cross-section) gives each issuer's residual. The pair gap's
persistence comes from TRACE history (7.5), so the convergence speed is measured, not assumed.

Run from the repo root (WRDS and SEC access needed):
    PYTHONPATH=. python3 scripts/rv_pair.py --pairs CRWV:ORCL HCA:THC CCL:NCLH MGM:WYNN
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import clock_case  # noqa: E402
import scenarios  # noqa: E402

from hy import rv, state  # noqa: E402
from hy.fairspread import fit_ar1, half_life  # noqa: E402
from hy.sources import trace_bonds as tb  # noqa: E402
from hy.sources import treasury as tr  # noqa: E402
from hy.data.config import CONFIG  # noqa: E402
from hy.data.factory import open_view  # noqa: E402
from hy.data.view import DataView  # noqa: E402

RAW = CONFIG.root
OUT = RAW / "rv"
FIG = ROOT / "docs" / "writeup" / "figures"
TENOR = 5.0          # reference tenor for the cross-section and the pair gap
H_YEARS = 0.5        # alpha horizon
HISTORY_DAYS = 180   # TRACE history for the pair-gap persistence


def issuer_block(ticker: str, decision: pd.Timestamp, start: str, end: str, view: DataView | None = None) -> dict:
    """Filing-based risk, clock metrics, and the bond curve for one issuer, as known at `decision`. Every input comes
    through `view` (hy.data.view)."""
    view = view or open_view(decision)
    issuer = view.issuer(ticker)
    inputs = view.facts(issuer).values
    case = clock_case.build_case(inputs, view)
    q = view.balance_sheet(issuer, inputs["q"][0])
    debt, debt_src = q.debt, q.debt_source
    lease = np.nansum([q.operating_lease_liability, q.finance_lease_liability])
    ebitda = inputs["ltm_ebitda"][0]
    rent = inputs["annual_lease_cost"][0] or 0.0
    cash = q.cash
    m = case["metrics"]
    risk = rv.IssuerRisk(
        ticker, lev_lease_adj=state.issuer_leverage(debt, lease, ebitda, rent),  # F5 going-concern view (hy.state)
        breakeven_margin=m.get("breakeven_margin", float("nan")),
        renewal_dependent_ebitda_years=m.get("renewal_dependent_years_of_ebitda", float("nan")),
        duration_gap=m.get("duration_gap", float("nan")),
        rating=(inputs.get("rating") or (None, ""))[0],
        extra={"debt": debt, "debt_source": debt_src, "ebitda_source": inputs["ltm_ebitda"][1], "lease_debt": lease, "ebitda_ltm": ebitda, "rent": rent, "cash": cash,
               "net_lev": state.net_lev(debt, cash, ebitda) if ebitda else float("nan")})

    ok = [b for b in view.bonds(issuer) if not b.convertible and b.fixed and b.seniority in ("senior_unsecured", "secured")]
    m_ok = pd.DataFrame([{"cusip": b.cusip, "coupon": b.coupon, "maturity": pd.Timestamp(b.maturity), "seniority": b.seniority,
                          "grade": b.grade} for b in ok], columns=["cusip", "coupon", "maturity", "seniority", "grade"])
    obs = view.observations(ok, pd.Timestamp(start))
    # tb.latest_snapshot still reads the TRACE names; it moves to the domain with neutral names in step 7.
    quotes = obs.rename(columns={"date": "trade_date", "price": "price_vw", "yield": "yield_vw"}).drop(columns="available_at")
    snap = tb.latest_snapshot(quotes) if len(quotes) else pd.DataFrame()
    bonds = pd.DataFrame()
    basis = "none"
    if len(snap):
        bonds = snap.merge(m_ok[["cusip", "coupon", "maturity", "seniority", "grade"]], on="cusip")
        curve = view.curve().as_row()
        bonds["maturity_years"] = (pd.to_datetime(bonds["maturity"]) - pd.Timestamp(end)).dt.days / 365.25
        bonds = bonds[bonds["maturity_years"].between(1.0, 15.0) & (bonds["price"] >= 80)].copy()
        bonds["g_spread"] = tb.g_spread(bonds["yield"], bonds["maturity"], pd.Timestamp(end), curve)
        bonds["ticker"] = ticker
        # Compare like with like across issuers: senior unsecured when there are at least two, else every bond.
        su = bonds[bonds["seniority"] == "senior_unsecured"]
        bonds, basis = (su, "senior unsecured") if len(su) >= 2 else (bonds, "all seniorities")
    recent = False
    if len(quotes) and len(bonds):
        first = quotes[quotes["cusip"].isin(bonds["cusip"])].groupby("cusip")["trade_date"].min()
        recent = bool((pd.to_datetime(first) > pd.Timestamp(start) + pd.Timedelta(14, unit="D")).any())
    longest = bonds.sort_values("maturity_years").iloc[-1][["g_spread", "price"]].to_dict() if len(bonds) else None
    return {"inputs": inputs, "recent_raise": recent, "longest": longest,
            "basis": basis, "ticker": ticker, "name": case["name"], "case": case, "risk": risk, "bonds": bonds, "quotes": quotes,
            "filing": f"{inputs['q'][0]} ({case['as_of']})", "revenue_clock": case["revenue_clock"], "issuer": issuer}


def daily_tenor_spread(block: dict, fit: tuple[float, float], year_curves: pd.DataFrame) -> pd.Series:
    """Issuer spread at TENOR per day: each bond's G-spread moved to TENOR along today's fitted slope, averaged."""
    q = block["quotes"]
    if q.empty or block["bonds"].empty:
        return pd.Series(dtype=float)
    mats = block["bonds"].set_index("cusip")["maturity"]
    q = q[q["cusip"].isin(mats.index)].copy()
    out = {}
    for d, g in q.groupby("trade_date"):
        day = pd.Timestamp(d)
        rows = year_curves.loc[:day]
        if rows.empty:
            continue
        curve = rows.iloc[-1]
        T = (pd.to_datetime(g["cusip"].map(mats)) - day).dt.days / 365.25
        s = g["yield_vw"].to_numpy() - tr.interpolate(curve, T.to_numpy())
        out[day] = float(np.mean(s - fit[1] * (T.to_numpy() - TENOR)))
    return pd.Series(out).sort_index()


def pair_block(a: dict, b: dict, fits: dict, resid: dict, curves: pd.DataFrame) -> dict:
    sa, sb = rv.curve_at(fits[a["ticker"]], TENOR), rv.curve_at(fits[b["ticker"]], TENOR)
    tenors = rv.common_tenors(a["bonds"]["maturity_years"], b["bonds"]["maturity_years"])
    by_tenor = [{"tenor": t, f"s_{a['ticker']}_bp": rv.curve_at(fits[a["ticker"]], t) * 1e4,
                 f"s_{b['ticker']}_bp": rv.curve_at(fits[b["ticker"]], t) * 1e4} for t in tenors]
    por = rv.pair_price_of_risk(sa, sb, a["risk"], b["risk"])
    votes = por["cheaper"].value_counts().to_dict() if len(por) else {}
    # Pair gap history (Section 7.5): persistence of the TENOR spread gap on weekly means. Daily TRACE yields bounce
    # between bid and ask; that noise biases a daily AR(1) toward zero persistence.
    ga, gb = daily_tenor_spread(a, fits[a["ticker"]], curves), daily_tenor_spread(b, fits[b["ticker"]], curves)
    gap = (ga - gb).dropna()
    weekly = gap.resample("W").mean().dropna()
    rho_w = fit_ar1((weekly - weekly.mean()).to_numpy()) if len(weekly) >= 12 else float("nan")
    hl_weeks = half_life(rho_w) if rho_w == rho_w and 0 < rho_w < 1 else float("nan")
    # Cross-section verdict: long the issuer with the larger residual (cheaper against the fair line).
    long_, short_ = (a, b) if resid[a["ticker"]] > resid[b["ticker"]] else (b, a)
    rgap = resid[long_["ticker"]] - resid[short_["ticker"]]  # log-spread residual gap
    s_long = rv.curve_at(fits[long_["ticker"]], TENOR)
    d5 = rv.modified_duration(0.045 + s_long, 0.045 + s_long, TENOR)  # spread duration at TENOR, near-par bond
    weeks = 52 * H_YEARS
    close = 1 - rho_w ** weeks if rho_w == rho_w and 0 < rho_w < 1 else float("nan")
    gap_bp = s_long * (1 - np.exp(-rgap)) * 1e4  # bp by which the long is cheap against the fair line, net of the short
    alpha = {"long": long_["ticker"], "short": short_["ticker"], "residual_gap_log": rgap, "gap_bp": gap_bp,
             "rho_weekly": rho_w, "half_life_weeks": hl_weeks, "close_share_h": close,
             "alpha_convergence_bp_price": d5 * close * gap_bp if close == close else float("nan"),
             "note": ("DV01-neutral at 5y. Convergence only: the spread difference between the legs is not alpha, "
                      "because it pays for the difference in default risk; default loss needs ratings, none on file. "
                      "Before trading cost.")}
    agree = len(votes) == 1
    return {"a": a["ticker"], "b": b["ticker"], "s5_bp": {a["ticker"]: sa * 1e4, b["ticker"]: sb * 1e4},
            "by_tenor": by_tenor, "price_of_risk": por.to_dict("records"), "votes": votes,
            "metrics_agree": agree, "cross_section_long": long_["ticker"], "alpha": alpha,
            "gap_history_n": int(len(gap))}


def figure(a: dict, b: dict, fits: dict, buckets: pd.DataFrame, pair: dict, path: Path) -> None:
    """Spread against maturity for both issuers, fitted curves, and the HY benchmark band (teaching figure)."""
    fig, ax = plt.subplots(figsize=(10, 5.6))
    for blk, col in ((a, "#4E79A7"), (b, "#E15759")):
        bd = blk["bonds"]
        if bd.empty:
            continue
        ax.scatter(bd["maturity_years"], bd["g_spread"] * 1e4, color=col, s=40, zorder=3,
                   label=f"{blk['ticker']} bonds (lease-adj. leverage {blk['risk'].lev_lease_adj:.1f}x)")
        x = np.linspace(bd["maturity_years"].min(), bd["maturity_years"].max(), 20)
        ax.plot(x, [rv.curve_at(fits[blk["ticker"]], t) * 1e4 for t in x], color=col, lw=1.5)
    mid = (buckets["lo"] + buckets["hi"]) / 2
    ax.fill_between(mid, (buckets["median"] - buckets["iqr"] / 2) * 1e4, (buckets["median"] + buckets["iqr"] / 2) * 1e4,
                    color="#999", alpha=0.18, label="TRACE high yield benchmark, middle half (crossover-heavy)")
    ax.axvline(TENOR, color="#555", ls=":", lw=1)
    al = pair["alpha"]
    n = sum(pair["votes"].values())
    per_risk = "; ".join(f"{t} on {k} of {n}" for t, k in pair["votes"].items())
    verdict = (f"Fair-spread line: long {al['long']}, short {al['short']}. "
               f"More spread per unit of risk: {per_risk} risk measures.")
    ax.set_title(f"{a['ticker']} against {b['ticker']}: G-spread by maturity\n{verdict}", loc="left", fontsize=10)
    ax.set_xlabel("Years to maturity")
    ax.set_ylabel("G-spread, bp")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(fontsize=8, frameon=False, loc="upper left")
    fig.text(0.01, 0.005, "Source: TRACE via WRDS, US Treasury par curve, SEC filings; hy/rv.py, scripts/rv_pair.py",
             fontsize=7, color="#555")
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(path, dpi=150)
    plt.close(fig)


def write_macro_section(report: dict, scen: dict, path: Path) -> None:
    """Generated LaTeX section: the live macro paths, then each pair's alpha under each path (Sections 5.4, 9.2)."""
    m = report["macro"]
    names = [p["name"] for p in m["paths"]]
    rows = "\n".join(f"{p['name'].replace('_', ' ')} & {p['prob']:.0%} & {p['gdp']:.1%} & {p['policy_q8']:.1%} & "
                      f"{p['y10_q8']:.1%} & {p['hy_spread'] * 1e4:.0f} \\\\".replace("%", "\\%") for p in m["paths"])
    votes = ", ".join(f"{k.replace('_', ' ')} {'late' if v else 'not late'}" for k, v in m["votes"].items() if v is not None)
    pair_rows = []
    for pr in report["pairs"]:
        if "pair_alpha_by_path_bp" not in pr:
            continue
        vals = " & ".join(f"{pr['pair_alpha_by_path_bp'][n]:+.0f}" for n in names)
        pair_rows.append(f"Long {pr['alpha']['long']}, short {pr['alpha']['short']} & {vals} & {pr['pair_alpha_weighted_bp']:+.0f} \\\\")
    head = " & ".join(n.replace("_", " ") for n in names)
    tex = f"""\\section{{Macro paths and the pairs under each path}}
\\textbf{{The paths.}} Live forecasts as known on {report['decision'][:10]}: SPF (GDP and CPI, with ranges from its probability bins),
FOMC SEP (policy rate), Treasury forwards (yields), and the TRACE high yield level ({m['s_index_now'] * 1e4:.0f} bp). Phase: {m['phase'].replace('_', ' ')},
from the indicators that have data ({votes}). Probabilities combine the forecast mass with the phase prior (methodology Section 5.4).

\\begin{{center}}\\footnotesize\\setlength{{\\tabcolsep}}{{4pt}}
\\begin{{tabular}}{{@{{}}lrrrrr@{{}}}}\\toprule
Path & Probability & GDP (avg) & Policy rate, 2 years & 10y yield, 2 years & HY spread (bp) \\\\\\midrule
{rows}
\\bottomrule
\\end{{tabular}}
\\end{{center}}

\\textbf{{Each pair under each path}} (bp a year, 6-month horizon, before cost; long minus short, DV01-neutral at 5 years).
Each leg's alpha comes from its own scenario page in the clock write-up: convergence to fair, the loss gap to a spread-sized hedge,
and the default risk that the issuer's own cases add when a refinancing fails (framework F4, F6.3).

\\begin{{center}}\\footnotesize\\setlength{{\\tabcolsep}}{{4pt}}
\\begin{{tabular}}{{@{{}}l{'r' * len(names)}r@{{}}}}\\toprule
Trade & {head} & Weighted \\\\\\midrule
{chr(10).join(pair_rows)}
\\bottomrule
\\end{{tabular}}
\\end{{center}}
\\textbf{{How to read it.}} A pair that wins in the likely path but loses heavily in a tail path is a bet on that tail not coming.
The weighted column already prices the tails at their probability.
"""
    path.write_text(tex)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pairs", nargs="+", default=["CRWV:ORCL", "HCA:THC", "CCL:NCLH", "MGM:WYNN"])
    ap.add_argument("--end", default="2026-09-17", help="last TRACE date; filings read as of the next day")
    args = ap.parse_args()
    end = pd.Timestamp(args.end)
    decision = end + pd.Timedelta(1, unit="D")
    start = (end - pd.Timedelta(HISTORY_DAYS, unit="D")).strftime("%Y-%m-%d")
    pairs = [tuple(p.upper().split(":")) for p in args.pairs]
    tickers = list(dict.fromkeys(t for p in pairs for t in p))

    con = CONFIG.connect()  # the benchmark band of the figure only (display; no data-contract kind)
    curves = open_view(decision).curve_history(pd.Timestamp(f"{start[:4]}-01-01"))
    bench = tb.hy_benchmark(con, args.end, cache_root=RAW)
    buckets = tb.benchmark_by_bucket(bench, tr.curve_on(end, cache_root=RAW))

    blocks, fits = {}, {}
    for t in tickers:
        try:
            blocks[t] = issuer_block(t, decision, start, args.end)
        except Exception as e:  # report the failure for this name and keep going
            print(f"{t}: skipped ({type(e).__name__}: {e})")
            continue
        bd = blocks[t]["bonds"]
        fits[t] = rv.curve_fit(bd["maturity_years"], bd["g_spread"]) if len(bd) else (float("nan"), 0.0)
        r = blocks[t]["risk"]
        print(f"{t}: {len(bd)} bonds ({blocks[t]['basis']}) | lev_lease_adj {r.lev_lease_adj:.2f}x | 5y spread "
              f"{rv.curve_at(fits[t], TENOR) * 1e4:.0f} bp | clock: {blocks[t]['revenue_clock'][:40]}")

    # Cross-section fair line (Section 7.2, small): log s5 = a + b * lev_lease_adj.
    xs = pd.DataFrame({t: {"s5": rv.curve_at(fits[t], TENOR), "lev": blocks[t]["risk"].lev_lease_adj}
                       for t in blocks}).T.astype(float).dropna()
    xs = xs[xs["s5"] > 0]
    b_, a_ = np.polyfit(xs["lev"], np.log(xs["s5"]), 1)
    xs["fair_s5"] = np.exp(a_ + b_ * xs["lev"])
    xs["resid_log"] = np.log(xs["s5"]) - np.log(xs["fair_s5"])
    resid = xs["resid_log"].to_dict()
    print(f"\nCross-section: log s5 = {a_:.3f} + {b_:.3f} x lev_lease_adj (n={len(xs)}; sign "
          f"{'ok' if b_ > 0 else 'WRONG'})")
    print((xs.assign(s5_bp=xs["s5"] * 1e4, fair_bp=xs["fair_s5"] * 1e4)[["lev", "s5_bp", "fair_bp", "resid_log"]])
          .round(2).to_string())

    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    report = {"end": args.end, "decision": str(decision), "tenor": TENOR, "h_years": H_YEARS,
              "cross_section": {"a": a_, "b": b_, "n": int(len(xs)), "table": xs.reset_index(names="ticker").to_dict("records")},
              "benchmark": buckets.to_dict("records"), "issuers": {}, "pairs": []}
    for t, blk in blocks.items():
        r = blk["risk"]
        report["issuers"][t] = {
            "name": blk["name"], "filing": blk["filing"], "curve_basis": blk["basis"], "revenue_clock": blk["revenue_clock"],
            "lev_lease_adj": r.lev_lease_adj, "net_lev": r.extra["net_lev"], "ebitda_ltm": r.extra["ebitda_ltm"],
            "debt": r.extra["debt"], "debt_source": r.extra["debt_source"], "ebitda_source": r.extra["ebitda_source"],
            "lease_debt": r.extra["lease_debt"], "breakeven_margin": r.breakeven_margin,
            "renewal_dependent_ebitda_years": r.renewal_dependent_ebitda_years, "rating": r.rating,
            "bonds": blk["bonds"][["cusip", "coupon", "maturity", "maturity_years", "yield", "g_spread", "price",
                                   "as_of"]].assign(g_spread_bp=lambda d: d["g_spread"] * 1e4).to_dict("records")
            if len(blk["bonds"]) else []}
    for a, b in pairs:
        if a not in blocks or b not in blocks or a not in resid or b not in resid:
            print(f"pair {a}:{b} skipped: missing data")
            continue
        pr = pair_block(blocks[a], blocks[b], fits, resid, curves)
        figure(blocks[a], blocks[b], fits, buckets, pr, FIG / f"rv_{a}_{b}.png")
        report["pairs"].append(pr)
        al = pr["alpha"]
        print(f"\n{a} vs {b}: 5y {pr['s5_bp']} | votes {pr['votes']} | long {al['long']} short {al['short']} | "
              f"gap {al['gap_bp']:.0f} bp | half-life {al['half_life_weeks']:.1f} wk | convergence alpha "
              f"{al['alpha_convergence_bp_price']:.0f} bp of price over {H_YEARS}y")
    # Macro paths and issuer scenarios (Section 5.4): one run feeds this report and the clock write-up.
    mac = scenarios.live_paths(open_view(decision), decision, end)
    scen_dir = RAW / "scenarios"
    scen_dir.mkdir(parents=True, exist_ok=True)
    report["macro"] = {"phase": mac.paths.phase, "votes": mac.paths.votes, "prior": mac.paths.prior,
                       "mass": mac.paths.mass, "posterior": mac.paths.posterior, "s_index_now": mac.s_index_now,
                       "snapshots": mac.snapshots.to_dict("records"), "assumptions": mac.paths.assumptions,
                       "sources": {k: [str(x) for x in v] for k, v in mac.paths.sources.items()},
                       "paths": [{"name": p.name, "prob": p.prob, "gdp": float(p.gdp_growth.mean()),
                                  "policy_q8": float(p.policy_rate[-1]), "y10_q8": float(p.y10[-1]),
                                  "hy_spread": float(p.index_spread[:4].mean())} for p in mac.paths.paths]}
    scen = {}
    for t, blk in blocks.items():
        if t not in xs.index:
            continue
        try:
            inputs = blk["inputs"]
            arch = (inputs.get("archetype") or ("A4", ""))[0]
            start_, drv, info = scenarios.issuer_start(inputs, blk["case"], decision, open_view(decision))
            s5, sf5 = float(xs.loc[t, "s5"]), float(xs.loc[t, "fair_s5"])
            d5 = rv.modified_duration(0.04 + s5, 0.04 + s5, TENOR)
            pts = scenarios.refi_points(s5, blk["longest"], blk["recent_raise"])
            out = scenarios.issuer_scenarios(start_, drv, arch, mac, s_now=s5, s_fair_now=sf5, spread_duration=d5, points=pts)
        except Exception as e:
            print(f"{t}: scenarios skipped ({type(e).__name__}: {e})")
            continue
        scen[t] = out
        scenarios.scenario_figure(blk["name"], t, out, FIG / f"scenarios_{t}.png")
        dump = {"ticker": t, "name": blk["name"], "archetype": arch, "info": info, "s5": s5, "fair_s5": sf5,
                "table": out["table"].to_dict("records"), "alpha": out["alpha"], "phase": out["phase"],
                "refi_points": out["refi_points"], "refi_score_by_path": out["refi_score_by_path"],
                "promoted": out["promoted"], "case_weights": out["case_weights"], "v0": scenarios.V0}
        (scen_dir / f"{t}.json").write_text(json.dumps(dump, indent=2, default=str))
        print(f"{t}: scenarios done | weighted alpha after cost {out['alpha']['alpha_net_bp_ann']:.0f} bp/yr")
    # Pair alpha by path: long minus short, DV01-neutral at 5 years (both legs priced at TENOR).
    for pr in report["pairs"]:
        lo, sh = pr["alpha"]["long"], pr["alpha"]["short"]
        if lo in scen and sh in scen:
            a_l = scen[lo]["table"].set_index("macro_path")["alpha"]
            a_s = scen[sh]["table"].set_index("macro_path")["alpha"]
            p_ = scen[lo]["table"].set_index("macro_path")["p_path"]
            by = ((a_l - a_s) / scenarios.V0["h_years"] * 1e4)
            pr["pair_alpha_by_path_bp"] = by.round(1).to_dict()
            pr["pair_alpha_weighted_bp"] = float((by * p_).sum())
    write_macro_section(report, scen, ROOT / "docs" / "writeup" / "rv_macro_section.tex")
    (OUT / "rv_pairs.json").write_text(json.dumps(report, indent=2, default=str))
    print(f"\nwrote {OUT / 'rv_pairs.json'}")


if __name__ == "__main__":
    main()
