"""Quarterly walk-forward of the full four-group analyst, 2024 to 2026 (decision page 2026-10-22-walkforward-2024).

    PYTHONPATH=.:scripts python3 scripts/walkforward.py run        # the process at every quarter end (slow, cached)
    PYTHONPATH=.:scripts python3 scripts/walkforward.py outcomes   # realised hedged returns over 3 and 6 months
    PYTHONPATH=.:scripts python3 scripts/walkforward.py report     # tables, figures, docs/writeup/walkforward_2024.tex
    PYTHONPATH=.:scripts python3 scripts/walkforward.py all

At each quarter end t from 2024-03-31 to the last one with three months of TRACE after it, scripts/process.py runs
for 15 issuers (7 new, the 8 of the memos) as known at t + 1 day, into data/raw/walkforward/runs/<t>/. The
fair line is fitted on that date's cross-section. Weights are the user's five buckets; S14b is as built. Each run is
audited for look-ahead (filings, forecast sources, the curve). The outcome is what the issuer's bonds earned over the
next 3 and 6 months against the model's hedges (hy.walkforward.bond_realised), after cost.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import process  # noqa: E402

from hy import walkforward as wf  # noqa: E402
from hy.data.pit import DataUnavailable  # noqa: E402
from hy.data.config import CONFIG
from hy.data.factory import open_source, open_view  # noqa: E402
from hy.data.outcomes import RealisedOutcomes  # noqa: E402

RAW = CONFIG.root
OUT = RAW / "walkforward"
RUNS = OUT / "runs"
NEW = ["HTZ", "CLF", "FYBR", "RIG", "CHTR", "AAL", "OPI"]
CURRENT = ["CRWV", "ORCL", "HCA", "THC", "CCL", "NCLH", "MGM", "WYNN"]
TICKERS = NEW + CURRENT
PAIRS = [("CRWV", "ORCL"), ("HCA", "THC"), ("CCL", "NCLH"), ("MGM", "WYNN")]
FIRST, TRACE_END = "2024-03-31", "2026-09-17"
HORIZONS = (3, 6)


def dates() -> list[pd.Timestamp]:
    return wf.decision_dates(FIRST, TRACE_END, min_months=min(HORIZONS))


# --------------------------------------------------------------------------------------------- 1. run and audit


def audit(run_dir: Path, q: pd.Timestamp) -> dict:
    """No-look-ahead audit of one run (hy.walkforward.assert_pit raises on a breach).

    Checks: the decision time is t + 1 day; every forecast source's last vintage was available by then; the curve
    date is on or before t; each issuer's filing was accepted on or before the decision time (EDGAR index).
    """
    dec = wf.decision_time(q)
    r = json.loads((run_dir / "_run.json").read_text())
    if pd.Timestamp(r["decision"]) != dec:
        raise wf.LookAheadError(f"decision {r['decision']} is not {dec.date()}")
    src = r["macro"].get("forecast_sources", [])
    wf.assert_pit([s.get("last_available_at") for s in src if s.get("last_available_at") not in ("None", "nan", "NaT")],
                  dec, "forecast sources")
    wf.assert_pit([r["macro"].get("curve_date")], q, "Treasury curve")
    acc = []
    for t in r["tickers"]:
        d = json.loads((run_dir / f"{t}.json").read_text())
        accession = str(d["steps"]["1"]["outputs"].get("filing", "")).split(" ")[0]
        idx = _acceptance(t, accession)
        if idx is not None:
            acc.append(idx)
    wf.assert_pit(acc, dec, "filing acceptance")
    return {"date": str(q.date()), "decision": str(dec.date()), "filings_checked": len(acc), "forecast_sources": len(src),
            "curve_date": r["macro"].get("curve_date"), "passed": True}


_ACC: dict = {}


def _acceptance(ticker: str, accession: str):
    """Acceptance time of one of the issuer's accessions, from its filing list as known today (the audit looks back)."""
    if ticker not in _ACC:
        view = open_view(pd.Timestamp.now())
        try:
            fl = view.filings(view.issuer(ticker), ["10-Q", "10-K", "10-Q/A", "10-K/A"])
        except DataUnavailable:
            fl = []
        _ACC[ticker] = {f.accession: pd.Timestamp(f.available_at) for f in fl}
    return _ACC[ticker].get(accession)


def run_all(refresh: bool = False) -> pd.DataFrame:
    """The process at every decision date (cached per date); then the audit. Returns the timing and audit table."""
    base = open_view(pd.Timestamp(FIRST))  # one source; process.run moves it to each date
    rows = []
    for q in dates():
        d = RUNS / str(q.date())
        t0 = time.time()
        status = "cached"
        if refresh or not (d / "_run.json").exists():
            try:
                process.run(TICKERS, str(q.date()), PAIRS, out_dir=d, figures=False, view=base)
                status = "ran"
            except Exception as e:  # noqa: BLE001 - one failed date is recorded, the rest run
                rows.append({"date": str(q.date()), "status": f"failed: {type(e).__name__}: {e}"[:200], "seconds": time.time() - t0})
                print(f"{q.date()}: FAILED {type(e).__name__}: {e}")
                continue
        a = audit(d, q)
        n = len(json.loads((d / "_run.json").read_text())["tickers"])
        rows.append({**a, "status": status, "issuers": n, "seconds": round(time.time() - t0, 1)})
        print(f"{q.date()}: {status}, {n} issuers, audit passed, {time.time() - t0:.0f}s")
    out = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT / "runs_audit.csv", index=False)
    return out


# --------------------------------------------------------------------------------------------- 2. predictions


ESTIMATE_IDS = [f"E{i}" for i in range(14)]
BUCKETS = ["G1", "G2C", "G2", "G3", "G4"]


def _g(d, *ks):
    for k in ks:
        d = d.get(k, {}) if isinstance(d, dict) else {}
    return d if d != {} else None


def predictions() -> pd.DataFrame:
    """One row per (date, issuer): every prediction and the key output of every step S1 to S15, read from the runs."""
    rows = []
    for q in dates():
        d = RUNS / str(q.date())
        if not (d / "_run.json").exists():
            continue
        run = json.loads((d / "_run.json").read_text())
        for t in run["tickers"]:
            st = json.loads((d / f"{t}.json").read_text())["steps"]
            O = lambda k: st.get(k, {}).get("outputs", {})  # noqa: E731
            cb, gate, lq, cs, ck, cases = O("14"), O("11"), O("4"), O("5"), O("6"), O("7")
            r = {"date": q, "ticker": t, "new": t in NEW, "s_index_bp": run["macro"]["s_index_now"] * 1e4,
                 "phase": run["macro"]["phase"],
                 # S1-S3
                 "filing": O("1").get("filing"), "bonds_priced": O("1").get("bonds_priced"),
                 "archetype": O("2").get("archetype"), "ebitda_ltm_bn": (O("3").get("ebitda_ltm_m") or np.nan) / 1e3,
                 "margin": O("3").get("margin_ltm"), "fcf_ltm_bn": (O("3").get("fcf_ltm_m") or np.nan) / 1e3,
                 "eq_score": O("3").get("eq_score"),
                 # S4
                 "liquidity_bn": (lq.get("L_eff_m") or np.nan) / 1e3, "runway_q": wf.numeric_or_nan(lq.get("runway_quoted_q")),
                 "runway_basis": lq.get("runway_quoted_basis"), "funding_gap_min_bn": (lq.get("funding_gap_min") or np.nan) / 1e3,
                 "delta_I_to_ebitda": lq.get("delta_I_to_ebitda"), "wall_18m_bn": (lq.get("wall_18m_m") or np.nan) / 1e3,
                 # S5
                 "lev": cs.get("lev_lease_adj"), "net_lev": cs.get("net_lev"), "cash_cov": cs.get("cash_cov"),
                 "headroom": cs.get("headroom_H"), "sp_class": _g(cs, "sp", "sp_anchor_class"),
                 # S6-S8
                 "years_of_ebitdar": ck.get("years_of_ebitdar"), "breakeven_margin": ck.get("breakeven_margin"),
                 "modal_path": cases.get("modal_path"),
                 "pd_12m": float(sum(x["p_path"] * x["pd_12m"] for x in cases.get("by_path", []))) if cases.get("by_path") else np.nan,
                 "lev_fwd_4": next((x["lev_fwd_4"] for x in cases.get("by_path", []) if x["macro_path"] == cases.get("modal_path")), np.nan),
                 "debt_to_tev": O("8").get("debt_to_market_tev"),
                 # S9-S11
                 "s5_bp": O("9").get("spread_5y_bp"), "fair_bp": O("9").get("fair_5y_bp"), "cheap_bp": O("9").get("cheap_by_bp"),
                 "alpha_e1_after_cost": O("10").get("weighted_bp_year_after_cost"),
                 "call": "Watch" if gate.get("G1") and gate.get("G3") and gate.get("G6") else ("Pass" if gate else None),
                 "direction": gate.get("direction"), "G1": gate.get("G1"), "G3": gate.get("G3"), "G6": gate.get("G6"),
                 # S12-S15
                 "watch_tier": O("12").get("watch_tier"),
                 "reds": sum(1 for x in O("13").get("panel", []) if x["band"] == "red"),
                 "combined_before_cost": cb.get("combined_before_cost"), "combined_after_cost": cb.get("combined_after_cost"),
                 "cost_bp_yr": cb.get("cost"), "rank": cb.get("rank"),
                 "alpha_sized": O("14b").get("alpha_sized"), "mz_b": O("14b").get("mz_b"),
                 "mu_excess_bp_yr": O("15").get("mu_excess_bp_yr"), "best_alt": O("15").get("replaces_position"),
                 "bonds": [b["cusip"] for b in cs.get("bonds", [])]}
            for g in BUCKETS:
                r[g] = _g(cb, "groups", g, "alpha_bp_yr")
                r[f"{g}_contrib"] = _g(cb, "groups", g, "contribution")
            est = {x["estimate"]: x["alpha_bp_yr"] for x in cb.get("rows", [])}
            r.update({e: est.get(e, np.nan) for e in ESTIMATE_IDS})
            rows.append(r)
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------------------------- 3. outcomes


def outcomes() -> pd.DataFrame:
    """Realised hedged excess return per (date, issuer, horizon): the mean over the bonds the model priced at t.

    Per bond (hy.walkforward.bond_realised): start = the run's snapshot price and yield; end = the last TRACE quote in
    (t, t + h] (an early exit when the bond stopped trading); Treasury hedge at the bond's duration from the curve at
    t and at exit; market hedge with DTS beta s_bond / S_index (the model's), and beta = 1 beside it; cost = the
    model's round trip, 20 bp of spread x duration. Annualised to bp a year. Nothing here feeds a prediction.
    """
    from hy import rv
    from hy.sources import treasury as tr

    src = open_source()
    pred = predictions()
    bench, curves, rows = {}, {}, []
    day1 = pd.Timedelta(1, unit="D")  # a trade day's quote, curve and index level are public the next day

    for q, g in pred.groupby("date"):
        cus = sorted({c for cs in g["bonds"] for c in cs})
        if not cus:
            continue
        # Future data on purpose: the realised path after the decision, never a model input (hy.data.outcomes).
        out = RealisedOutcomes(src, wf.decision_time(q))

        def S_at(day):
            day = pd.Timestamp(day).normalize()
            if day not in bench:
                bench[day] = out.hy_index(day + day1).spread
            return bench[day]

        def curve_at(day):
            day = pd.Timestamp(day).normalize()
            if day not in curves:
                curves[day] = out.curve(day + day1).as_row()
            return curves[day]

        last = min(q + pd.DateOffset(months=max(HORIZONS)), pd.Timestamp(TRACE_END))
        quotes = out.observations(cus, last + day1).rename(
            columns={"date": "trade_date", "price": "price_vw", "yield": "yield_vw"})
        run = RUNS / str(q.date())
        S0 = json.loads((run / "_run.json").read_text())["macro"]["s_index_now"]
        c0 = curve_at(q)
        for _, r in g.iterrows():
            st5 = json.loads((run / f"{r['ticker']}.json").read_text())["steps"]["5"]["outputs"]
            for h in HORIZONS:
                e = q + pd.DateOffset(months=h)
                if e > pd.Timestamp(TRACE_END):
                    continue
                per = []
                for b in st5.get("bonds", []):
                    eq = wf.end_quote(quotes, b["cusip"], q, e)
                    if eq is None or b.get("price") is None or b.get("yield") is None:
                        continue
                    T0 = (pd.Timestamp(b["maturity"]) - q).days / 365.25
                    tau = (eq["date"] - q).days / 365.25
                    dur = rv.modified_duration(b["yield"], b["coupon"], T0)
                    tsy0 = float(tr.interpolate(c0, T0))
                    tsy1 = float(tr.interpolate(curve_at(eq["date"]), max(T0 - tau, 0.1)))
                    S1 = S_at(eq["date"])
                    s0 = (b.get("spread_bp") or 0) / 1e4
                    cost = 20 / 1e4 * dur
                    dts = wf.bond_realised(b["price"], eq["price"], b["coupon"], tau, tsy0, tsy1, dur, s0, S0, S1,
                                           beta=s0 / S0 if S0 else 1.0, cost=cost)
                    one = wf.bond_realised(b["price"], eq["price"], b["coupon"], tau, tsy0, tsy1, dur, s0, S0, S1,
                                           beta=1.0, cost=cost)
                    per.append({"dts": dts["realised"], "dts_net": dts["net"], "b1_net": one["net"], "total": dts["total"],
                                "months": tau * 12, "early": eq["early"], "price_end": eq["price"]})
                if not per:
                    continue
                p = pd.DataFrame(per)
                m = p["months"].mean()
                rows.append({"date": q, "ticker": r["ticker"], "h": h, "n_bonds": len(p), "n_early": int(p["early"].sum()),
                             "realised_bp_yr": wf.annualise_bp(p["dts"].mean(), m),
                             "realised_net_bp_yr": wf.annualise_bp(p["dts_net"].mean(), m),
                             "realised_b1_net_bp_yr": wf.annualise_bp(p["b1_net"].mean(), m),
                             "total_return_pct": 100 * p["total"].mean(), "months": m})
        print(f"{q.date()}: outcomes for {g['ticker'].nunique()} issuers")
    out = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    out.to_parquet(OUT / "outcomes.parquet", index=False)
    pred.drop(columns=["bonds"]).to_parquet(OUT / "predictions.parquet", index=False)
    return out


# --------------------------------------------------------------------------------------------- 4. report

FIG = ROOT / "docs" / "writeup" / "figures"
TEX = ROOT / "docs" / "writeup" / "walkforward_2024.tex"
COL = {"G1": "#3B6EA8", "G2C": "#8E5BA8", "G2": "#5FA0C8", "G3": "#B5403A", "G4": "#B07D1A"}
BNAME = {"G1": "Core process", "G2C": "Two clocks", "G2": "Built methods (rest)", "G3": "Credit skills", "G4": "Books"}
EWORD = {"E0": "Spread level (carry)", "E1": "Weighted cases and stories", "E2": "Fair-line convergence",
         "E3": "Pair convergence", "E4": "Default the price assumes (weight 0)", "E5": "Two clocks",
         "E6": "Health panel", "E7": "Earnings quality (one way)", "E8": "Liquidity and funding gap",
         "E9": "Debt against market value", "E10": "Return above cash, repriced", "E11": "Watchlist (one way)",
         "E12": "Spread against S&P score", "E13": "Spread per turn"}


def scores(df: pd.DataFrame) -> pd.DataFrame:
    """Every predictor against the outcome, per horizon. Numbers after cost meet the realised after cost; buckets and
    estimates (before cost) meet the realised before cost."""
    rows = []
    for h in HORIZONS:
        d = df[df["h"] == h]
        sets = [("Combined, after cost", "combined_after_cost", "realised_net_bp_yr"),
                ("Combined, calibrated (S14b)", "alpha_sized", "realised_net_bp_yr"),
                ("Cases and stories alone (E1), after cost", "alpha_e1_after_cost", "realised_net_bp_yr"),
                ("Combined, after cost, 7 new issuers only", "combined_after_cost", "realised_net_bp_yr")]
        sets += [(f"Bucket: {BNAME[g]}", g, "realised_bp_yr") for g in BUCKETS]
        sets += [(f"{e} {EWORD[e]}", e, "realised_bp_yr") for e in ESTIMATE_IDS]
        for name, pred, real in sets:
            dd = d[d["new"]] if "new issuers only" in name else d
            if dd[pred].notna().sum() < 5:
                continue
            rows.append({"h": h, "predictor": name, "column": pred, **wf.score(dd, pred, real)})
    return pd.DataFrame(rows)


def _events() -> dict:
    """Credit events per issuer from cached EDGAR 8-K item codes, and results dates (item 2.02). Display only: the
    8-K item codes are not a data-contract kind, so this report reads the warehouse's EDGAR files directly."""
    view = open_view(pd.Timestamp.now())
    out = {}
    for t in TICKERS:
        try:
            cik = view.issuer(t).cik
        except DataUnavailable:
            continue
        f = RAW / "edgar" / f"CIK{str(cik).zfill(10)}.json"
        if not f.exists():
            continue
        r = json.loads(f.read_text())["filings"]["recent"]
        rows = [(r["filingDate"][i], r["items"][i]) for i in range(len(r["form"])) if r["form"][i] == "8-K"]
        res = [pd.Timestamp(r["filingDate"][i]) for i in range(len(r["form"]))
               if r["form"][i] in ("10-Q", "10-K") and FIRST <= r["filingDate"][i] <= TRACE_END]
        out[t] = {"credit": wf.events_from_8k(rows, FIRST, TRACE_END), "results": res}
    return out


def timeline_figure(t: str, d: pd.DataFrame, ev: dict, path: Path) -> None:
    """Teaching figure per issuer: top, what the analyst predicted against what then happened; bottom, which bucket
    drove the prediction. Credit events from 8-K filings are marked; results dates are ticks."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    d = d.sort_values("date")
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 7.2), sharex=True, gridspec_kw={"height_ratios": [1.15, 1]})
    a1.axhline(0, color="#999", lw=0.8)
    a1.plot(d["date"], d["combined_after_cost"], "-o", color="#222", lw=2, label="Predicted: combined, after cost (raw)")
    a1.plot(d["date"], d["alpha_sized"], "--", color="#222", lw=1.2, label="Predicted: calibrated (x slope)")
    for h, c, m in ((3, "#D9822B", "s"), (6, "#E8B37A", "^")):
        col = f"real_{h}"
        if col in d and d[col].notna().any():
            a1.plot(d["date"], d[col], m, color=c, ms=8, label=f"Realised next {h} months, after cost")
    for _, r in d[d["call"] == "Watch"].iterrows():
        a1.annotate("Watch", (r["date"], r["combined_after_cost"]), textcoords="offset points", xytext=(0, 9),
                    ha="center", fontsize=8, color="#2E7D4F", weight="bold")
    lo, hi = a1.get_ylim()
    for k, (when, label) in enumerate(ev.get("credit", [])):
        a1.axvline(when, color="#B5403A", ls=":", lw=1)
        a1.text(when, hi - (hi - lo) * (0.07 + 0.09 * (k % 4)), " " + label, fontsize=7, color="#B5403A", va="top")
    for when in ev.get("results", []):
        a1.plot([when], [lo], marker="|", color="#666", ms=9, clip_on=False)
    a1.set_ylabel("bp a year")
    a1.set_title(f"{t}: what the analyst predicted at each quarter end, and what the bonds then earned", fontsize=11)
    a1.legend(fontsize=7.5, loc="lower left", ncol=2, frameon=False)
    a1.text(0.995, 0.02, "ticks: results filed; red lines: credit events from 8-K filings",
            transform=a1.transAxes, ha="right", fontsize=7, color="#666")
    x = np.arange(len(d))
    dates_ = d["date"].to_numpy()
    width = pd.Timedelta(55, unit="D")
    pos, neg = np.zeros(len(d)), np.zeros(len(d))
    for g in BUCKETS:
        v = d[f"{g}_contrib"].fillna(0).to_numpy(float)
        base = np.where(v >= 0, pos, neg)
        a2.bar(dates_, v, width=width, bottom=base, color=COL[g], label=BNAME[g])
        pos, neg = pos + np.clip(v, 0, None), neg + np.clip(v, None, 0)
    a2.plot(d["date"], d["combined_before_cost"], "o-", color="#222", lw=1.2, ms=4, label="Combined, before cost")
    a2.axhline(0, color="#999", lw=0.8)
    a2.set_ylabel("bp a year, before cost")
    a2.set_title("Which bucket pushed the prediction up or down (contribution = bucket estimate x weight)", fontsize=9.5)
    a2.legend(fontsize=7, ncol=3, frameon=False, loc="lower left")
    del x
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def summary_figures(sc: pd.DataFrame, df: pd.DataFrame) -> None:
    """Pooled IC by bucket and estimate (with the quarter-to-quarter spread), and predicted against realised."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    for h in HORIZONS:
        s = sc[sc["h"] == h].copy()
        s = s[~s["predictor"].str.contains("new issuers only")]
        fig, ax = plt.subplots(figsize=(9, 0.32 * len(s) + 1.4))
        y = np.arange(len(s))[::-1]
        se = s["ic_mean"] / s["ic_t"].replace(0, np.nan)
        colors = ["#222" if p.startswith("Combined") or p.startswith("Cases") else
                  (COL.get(s["column"].iloc[i], "#5FA0C8") if p.startswith("Bucket") else "#9BB7D4")
                  for i, p in enumerate(s["predictor"])]
        ax.barh(y, s["ic_mean"], xerr=1.96 * se.fillna(0), color=colors, alpha=0.9, error_kw={"lw": 0.8})
        ax.set_yticks(y)
        ax.set_yticklabels(s["predictor"], fontsize=7.5)
        ax.axvline(0, color="#999", lw=0.8)
        ax.set_xlabel("Mean quarterly rank IC across issuers (bar: 95% band from the spread across quarters)")
        ax.set_title(f"Which numbers ranked the issuers well, next {h} months", fontsize=10)
        fig.tight_layout()
        fig.savefig(FIG / f"wf_ic_{h}m.png", dpi=140)
        plt.close(fig)
    d = df[df["h"] == 3].dropna(subset=["combined_after_cost", "realised_net_bp_yr"])
    fig, ax = plt.subplots(figsize=(6.5, 5))
    ax.scatter(d["combined_after_cost"], d["realised_net_bp_yr"], c=np.where(d["new"], "#D9822B", "#3B6EA8"), s=22, alpha=0.8)
    lim = np.nanpercentile(np.abs(np.r_[d["combined_after_cost"], d["realised_net_bp_yr"]]), 97)
    ax.plot([-lim, lim], [-lim, lim], color="#999", ls="--", lw=0.8)
    sl = wf.cluster_slope(d, "combined_after_cost", "realised_net_bp_yr")
    xs = np.linspace(-lim, lim, 10)
    ax.plot(xs, sl.get("intercept", 0) + sl["slope"] * xs, color="#222", lw=1.5)
    ax.text(0.02, 0.97, f"fitted slope {sl['slope']:.2f} (se {sl['se']:.2f}); dashed line = slope 1\norange = 7 new issuers",
            transform=ax.transAxes, va="top", fontsize=8)
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_xlabel("Predicted combined alpha after cost, bp a year")
    ax.set_ylabel("Realised next 3 months after cost, bp a year")
    ax.set_title("Size check: predicted against realised", fontsize=10)
    fig.tight_layout()
    fig.savefig(FIG / "wf_scatter.png", dpi=140)
    plt.close(fig)
    ic = wf.rank_ic_by_date(df[df["h"] == 3], "combined_after_cost", "realised_net_bp_yr")
    ic1 = wf.rank_ic_by_date(df[df["h"] == 3], "E1", "realised_bp_yr")
    fig, ax = plt.subplots(figsize=(8, 3.2))
    ax.bar(ic.index - pd.Timedelta(12, unit="D"), ic.values, width=24, color="#222", label="Combined")
    ax.bar(ic1.index + pd.Timedelta(12, unit="D"), ic1.reindex(ic1.index).values, width=24, color="#5FA0C8", label="E1 cases alone")
    ax.axhline(0, color="#999", lw=0.8)
    ax.set_ylabel("rank IC, next 3 months")
    ax.set_title("Quarter by quarter: did the ranking work?", fontsize=10)
    ax.legend(fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(FIG / "wf_ic_by_quarter.png", dpi=140)
    plt.close(fig)


def _esc(x) -> str:
    s = "" if x is None or (isinstance(x, float) and x != x) else str(x)
    for a, b in (("\\", "\\textbackslash{}"), ("&", "\\&"), ("%", "\\%"), ("$", "\\$"), ("#", "\\#"), ("_", " ")):
        s = s.replace(a, b)
    return s


def _f(x, nd=0, sign=True):
    if x is None or (isinstance(x, float) and x != x):
        return "--"
    if isinstance(x, str):
        return _esc(x)
    return f"{x:+,.{nd}f}" if sign else f"{x:,.{nd}f}"


def _table(head, rows, spec):
    out = [f"\\begin{{center}}\\scriptsize\\setlength{{\\tabcolsep}}{{3pt}}\\begin{{tabular}}{{@{{}}{spec}@{{}}}}\\toprule",
           " & ".join(head) + " \\\\\\midrule"]
    out += [" & ".join(str(c) for c in r) + " \\\\" for r in rows]
    out.append("\\bottomrule\\end{tabular}\\end{center}")
    return "\n".join(out)


def why(prev: pd.Series | None, cur: pd.Series) -> str:
    """One plain sentence on why the prediction moved since last quarter: the bucket whose contribution moved most,
    the call, and the step outputs that moved with it."""
    if prev is None:
        return "First quarter of the test."
    dif = {g: (cur[f"{g}_contrib"] or 0) - (prev[f"{g}_contrib"] or 0) for g in BUCKETS
           if cur[f"{g}_contrib"] == cur[f"{g}_contrib"] and prev[f"{g}_contrib"] == prev[f"{g}_contrib"]}
    parts = []
    if dif:
        g = max(dif, key=lambda k: abs(dif[k]))
        parts.append(f"{BNAME[g].lower()} moved most ({dif[g]:+.0f} bp)")
    for col, word, nd in (("lev", "leverage", 1), ("s5_bp", "5-year spread", 0), ("cheap_bp", "gap to fair", 0)):
        a, b = prev.get(col), cur.get(col)
        if a is not None and b is not None and a == a and b == b and abs(b - a) > (0.5 if col == "lev" else 25):
            parts.append(f"{word} {a:,.{nd}f} to {b:,.{nd}f}")
    if prev.get("call") != cur.get("call"):
        parts.append(f"call {prev.get('call')} to {cur.get('call')}")
    if prev.get("watch_tier") != cur.get("watch_tier"):
        parts.append(f"watchlist {prev.get('watch_tier')} to {cur.get('watch_tier')}")
    return ("; ".join(parts) + ".").capitalize() if parts else "Little changed."


ISSUER_NOTE = {  # sector words for the issuer table (archetype from data/analyst_inputs)
    "HTZ": "car rental (fleet financed by asset-backed debt)", "CLF": "steel and iron ore",
    "FYBR": "fibre and copper telecom", "RIG": "offshore drilling", "CHTR": "cable", "AAL": "airline",
    "OPI": "office property trust", "CRWV": "AI data centres", "ORCL": "software and cloud", "HCA": "hospitals",
    "THC": "hospitals", "CCL": "cruise lines", "NCLH": "cruise lines", "MGM": "casinos", "WYNN": "casinos",
}


def _ic_rows(sc: pd.DataFrame, h: int, which) -> list:
    s = sc[(sc["h"] == h) & sc["predictor"].map(which)]
    return [[_esc(r["predictor"]), _f(r["ic_mean"], 2), _f(r["ic_t"], 1), _f(r["ic_pos_share"] * 100, 0, False) + "\\%",
             _f(r["ic_pooled"], 2), _f(r["hit_rate"] * 100, 0, False) + "\\%", f"{_f(r['slope'], 3)} ({_f(r['slope_se'], 3, False)})",
             int(r["n"])] for _, r in s.iterrows()]


def write_tex(sc, gates, wide, df, ev, audit) -> str:
    """The write-up in plain English: what was tested, the pooled answer, the gate, then each issuer quarter by quarter."""
    head = ["Predictor", "IC", "t", "IC $>$ 0", "Pooled IC", "Hit rate", "Slope (se)", "n"]
    spec = "p{6.0cm}rrrrrrr"
    n_q = wide["date"].nunique()
    n_iss = wide["ticker"].nunique()
    n3 = int((df["h"] == 3).sum())
    c3 = sc[(sc["h"] == 3) & (sc["column"] == "combined_after_cost") & ~sc["predictor"].str.contains("new")].iloc[0]
    c6 = sc[(sc["h"] == 6) & (sc["column"] == "combined_after_cost") & ~sc["predictor"].str.contains("new")]
    c6 = c6.iloc[0] if len(c6) else None
    secs = audit["seconds"].sum() if "seconds" in audit else float("nan")
    L = []
    L.append(r"""\section*{What this test asks}
At the end of every quarter from March 2024, the analyst ran the full process for 15 companies, using only what was
public the next morning: filings already accepted by the SEC, bond trades already reported, the Treasury curve of that
day, and forecasts already published. It produced one number per company: the expected profit of owning its bonds
against a hedge, in bp a year. We then measured what the bonds actually earned over the next three and six months
against the same hedges, after trading costs. The question is simple: \textbf{did a higher number come before a better
result?}""")
    L.append(r"""\textbf{How to read the scores.} The \emph{rank IC} is the correlation between the order of the predictions and the
order of the results across companies in one quarter: $+1$ is a perfect ranking, $0$ is no skill. We average it over
quarters; $t$ is that average over its quarter-to-quarter noise. The \emph{hit rate} is the share where the sign was
right. The \emph{slope} says whether the size was right: a slope of 1 means a 100 bp prediction earned 100 bp. Standard
errors are clustered by quarter, because every company shares the same market move in a quarter.""")
    L.append(r"\section*{The issuers}")
    L.append("Seven new companies join the eight of the memos. Each new one is an SEC filer with point-in-time Compustat "
             "data and bonds that trade in TRACE from early 2024; together they span seven industries, and several had "
             "credit events in the window. Candidates that failed the data check were replaced: Lumen, Bath \\& Body "
             "Works and Viasat (their bonds trade under subsidiary symbols), EchoStar (its ticker maps to another company "
             "in Compustat), Carvana (too few public trades), Uniti (its SEC registrant has no filings before 2025).")
    rows = []
    for t in NEW + CURRENT:
        d = wide[wide["ticker"] == t]
        rows.append([t, _esc(ISSUER_NOTE.get(t, "")), _esc(d["archetype"].dropna().iloc[0] if d["archetype"].notna().any() else "--"),
                     "new" if t in NEW else "memo", int(d["combined_after_cost"].notna().sum()),
                     _esc("; ".join(sorted({x for _, x in ev.get(t, {}).get("credit", [])}))[:70] or "--")])
    L.append(_table(["Issuer", "Business", "Type", "Set", "Quarters", "Credit events in 8-K filings, 2024 to 2026"], rows,
                    "llllrp{6.2cm}"))
    L.append(r"\section*{The answer, pooled over all issuers and quarters}")
    msg3 = (f"Over {n_q} quarters and {n_iss} issuers ({n3} issuer-quarters with a 3-month result), the combined number "
            f"after cost had a mean rank IC of {c3['ic_mean']:+.2f} (t {c3['ic_t']:+.1f}); it was positive in "
            f"{c3['ic_pos_share'] * 100:.0f}\\% of quarters. Its hit rate was {c3['hit_rate'] * 100:.0f}\\%. The slope of "
            f"realised on predicted was {c3['slope']:+.3f} (se {c3['slope_se']:.3f}).")
    if c6 is not None:
        msg3 += (f" Over six months: IC {c6['ic_mean']:+.2f} (t {c6['ic_t']:+.1f}), hit rate {c6['hit_rate'] * 100:.0f}\\%, "
                 f"slope {c6['slope']:+.3f}.")
    L.append(r"\noindent\fcolorbox{gray}{gray!6}{\parbox{\dimexpr\linewidth-2\fboxsep-2\fboxrule-1pt}{\sloppy "
             + r"\textbf{Headline.} " + msg3 + r" \textbf{How sure can we be?} Not very. Each quarter ranks 15 companies at most, "
             r"and there are " + str(n_q) + r" quarters, so a mean IC needs to be about $\pm$0.2 or more before it stands out "
             r"from noise. The six-month results overlap from one quarter to the next, so they are not independent. Read "
             r"these as a first check on direction, not a measure of skill.}}")
    L.append(r"\begin{figure}[H]\centering\includegraphics[width=0.8\linewidth]{figures/wf_ic_by_quarter.png}\end{figure}")
    for h in HORIZONS:
        L.append(f"\\subsection*{{Every number, next {h} months}}")
        L.append("The combined, calibrated and cases-alone numbers are after cost and meet the result after cost. "
                 "Buckets and estimates are before cost and meet the result before cost.")
        L.append(_table(head, _ic_rows(sc, h, lambda p: p.startswith(("Combined", "Cases"))) +
                        [["\\midrule " + r[0]] + r[1:] for r in _ic_rows(sc, h, lambda p: p.startswith("Bucket"))[:1]] +
                        _ic_rows(sc, h, lambda p: p.startswith("Bucket"))[1:] +
                        [["\\midrule " + r[0]] + r[1:] for r in _ic_rows(sc, h, lambda p: p.startswith("E"))[:1]] +
                        _ic_rows(sc, h, lambda p: p.startswith("E"))[1:], spec))
        L.append(f"\\begin{{figure}}[H]\\centering\\includegraphics[width=0.85\\linewidth]{{figures/wf_ic_{h}m.png}}\\end{{figure}}")
    L.append(r"""\subsection*{Size: alpha sizes are uncalibrated}
The scatter shows the predicted number against what happened. The calibrated number multiplies the raw one by the
slope measured in the panel backtest (S14b). \textbf{That slope comes from a backtest whose sample (2008 to August 2026)
overlaps this test's window}, so the calibrated number here is not an out-of-sample test of the calibration; it is shown
for completeness.
\begin{figure}[H]\centering\includegraphics[width=0.6\linewidth]{figures/wf_scatter.png}\end{figure}""")
    L.append(r"\section*{The gate: Watch or Pass, against what happened}")
    L.append("A Watch call says the bond is mispriced by more than the noise, every check agrees, and the expected profit "
             "beats costs. For a cheap Watch, being right means the bond then earned more than its hedge after cost; for a "
             "rich one, less. A Pass is not a forecast of direction, but we show its results by the direction the checks leaned.")
    for h, g in gates.items():
        if len(g):
            L.append(f"\\textbf{{Next {h} months.}}")
            L.append(_table(["Call", "Leaning", "Calls", "Mean result (bp a year, after cost)", "Went the way it leaned"],
                            [[r["call"], r["direction"], int(r["n"]), _f(r["mean_bp_yr"]), f"{r['right_share'] * 100:.0f}\\%"]
                             for _, r in g.iterrows()], "llrrr"))
    L.append(r"\section*{Issuer by issuer}")
    L.append("Each page shows, per quarter end, what the analyst predicted and what then happened (top chart), which bucket "
             "drove the prediction (bottom chart), the key output of every step, and one line on why the prediction moved.")
    for t in NEW + CURRENT:
        d = wide[wide["ticker"] == t].sort_values("date")
        if d.empty:
            continue
        L.append(f"\\newpage\\subsection*{{{t}: {_esc(ISSUER_NOTE.get(t, ''))}}}")
        L.append(f"\\begin{{figure}}[H]\\centering\\includegraphics[width=0.98\\linewidth]{{figures/wf_{t}.png}}\\end{{figure}}")
        L.append(_table(["Quarter end", "Combined", "Calibr.", "Real. 3m", "Real. 6m", "G1", "Clocks", "G2 rest", "G3", "G4", "Call"],
                        [[r["date"].strftime("%Y-%m"), _f(r["combined_after_cost"]), _f(r["alpha_sized"]), _f(r.get("real_3")),
                          _f(r.get("real_6")), _f(r["G1"]), _f(r["G2C"]), _f(r["G2"]), _f(r["G3"]), _f(r["G4"]), _esc(r["call"])]
                         for _, r in d.iterrows()], "lrrrrrrrrrl"))
        L.append(_table(["Quarter end", "Leverage", "Runway (q)", "Funding gap", "Bills (yrs)", "PD 12m", "Spread", "Fair",
                         "Watchlist", "Best alt."],
                        [[r["date"].strftime("%Y-%m"), _f(r["lev"], 1, False), _f(r["runway_q"], 1, False),
                          (f"\\${r['funding_gap_min_bn']:,.1f}bn" if r["funding_gap_min_bn"] == r["funding_gap_min_bn"] else "--"),
                          _f(r["years_of_ebitdar"], 1, False), (f"{r['pd_12m'] * 100:.1f}\\%" if r["pd_12m"] == r["pd_12m"] else "--"),
                          _f(r["s5_bp"], 0, False), _f(r["fair_bp"], 0, False), _esc(r["watch_tier"]), _esc(r["best_alt"])]
                         for _, r in d.iterrows()], "lrrrrrrrll"))
        prev, items = None, []
        for _, r in d.iterrows():
            items.append(f"\\item[{r['date'].strftime('%Y-%m')}] {_esc(why(prev, r))}")
            prev = r
        L.append("\\textbf{Why the prediction moved:}\\begin{description}\\setlength{\\itemsep}{0pt}" + "".join(items) + "\\end{description}")
    L.append(r"\newpage\section*{Limits}")
    lim = [
        f"Small sample: {n_iss} issuers over {n_q} quarters. A rank IC from 15 names is noisy; one quarter can swing the mean.",
        "Six-month results overlap across quarters, so they are not independent observations.",
        "The calibration slope (S14b) and the spec weights rest on a backtest that overlaps this window. The user's bucket "
        "weights were set in October 2026, after the window: the weights themselves are not point in time.",
        "Forecast sources that publish no history (for example a source whose cache holds only the newest vintage) fall "
        "back by rule at early dates; the run log lists the sources each date used.",
        "TRACE covers the bonds that trade; an issuer whose bonds traded below 80 drops out of the fair line on that date.",
        "Rating changes are not in the data, so the timelines mark credit events from 8-K item codes only.",
        "The realised hedge uses the TRACE high yield benchmark (median spread), not a tradeable index.",
    ]
    L.append("\\begin{itemize}" + "".join(f"\\item {_esc(x)}" for x in lim) + "\\end{itemize}")
    L.append(f"Point-in-time audit: {int(audit.get('passed', pd.Series(dtype=bool)).fillna(False).sum())} of {len(audit)} decision dates "
             f"passed (filing acceptance, forecast vintages, curve date). Run time for the process at all dates: "
             f"{secs / 60:,.0f} minutes (cached runs count as seconds).")
    body = "\n\n".join(L)
    return rf"""\documentclass[11pt,a4paper]{{article}}
\usepackage[margin=2cm]{{geometry}}
\usepackage{{booktabs,xcolor,hyperref,enumitem,graphicx,float,caption,array}}
\emergencystretch=3em
\title{{The analyst, quarter by quarter: a walk-forward test, 2024 to 2026}}
\author{{FundamentalQuantmental HY Analyst}}
\date{{Decision dates {wide['date'].min():%Y-%m-%d} to {wide['date'].max():%Y-%m-%d}; TRACE to {TRACE_END}}}
\begin{{document}}
\maketitle
{body}
\end{{document}}
"""


def report() -> None:
    """Scores, figures, and docs/writeup/walkforward_2024.tex."""
    pred = pd.read_parquet(OUT / "predictions.parquet")
    outc = pd.read_parquet(OUT / "outcomes.parquet")
    df = outc.merge(pred, on=["date", "ticker"], how="left")
    sc = scores(df)
    sc.to_csv(OUT / "scores.csv", index=False)
    gates = {h: wf.gate_outcomes(df[df["h"] == h], "call", "direction", "realised_net_bp_yr") for h in HORIZONS}
    wide = pred.copy()
    for h in HORIZONS:
        wide = wide.merge(outc[outc["h"] == h][["date", "ticker", "realised_net_bp_yr"]].rename(
            columns={"realised_net_bp_yr": f"real_{h}"}), on=["date", "ticker"], how="left")
    wide.to_parquet(OUT / "timeline.parquet", index=False)
    ev = _events()
    FIG.mkdir(parents=True, exist_ok=True)
    for t, d in wide.groupby("ticker"):
        timeline_figure(t, d, ev.get(t, {}), FIG / f"wf_{t}.png")
    summary_figures(sc, df)
    audit = pd.read_csv(OUT / "runs_audit.csv")
    tex = write_tex(sc, gates, wide, df, ev, audit)
    TEX.write_text(tex)
    (OUT / "results.json").write_text(json.dumps({
        "scores": sc.to_dict("records"), "gates": {h: g.to_dict("records") for h, g in gates.items()},
        "n_predictions": int(len(pred)), "n_outcomes": {h: int((outc["h"] == h).sum()) for h in HORIZONS}},
        indent=1, default=str))
    print(f"wrote {TEX}")


def main() -> None:
    global TICKERS, PAIRS, FIRST, TRACE_END  # the options below replace this machine's defaults for the whole run
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("what", choices=["run", "outcomes", "report", "all"])
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--tickers", nargs="+", help="issuers to replay (default: this machine's 15)")
    ap.add_argument("--pairs", nargs="*", help="pairs as A:B (default: this machine's 4)")
    ap.add_argument("--first", help=f"first quarter end (default {FIRST})")
    ap.add_argument("--last", help=f"last trade day of the bond data (default {TRACE_END})")
    a = ap.parse_args()
    TICKERS = [t.upper() for t in a.tickers] if a.tickers else TICKERS
    PAIRS = [tuple(p.upper().split(":")) for p in a.pairs] if a.pairs is not None else PAIRS
    FIRST, TRACE_END = a.first or FIRST, a.last or TRACE_END
    if a.what in ("run", "all"):
        run_all(a.refresh)
    if a.what in ("outcomes", "all"):
        outcomes()
    if a.what in ("report", "all"):
        report()


if __name__ == "__main__":
    main()
