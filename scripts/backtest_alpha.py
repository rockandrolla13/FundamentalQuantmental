"""Backtest of the expected alpha forecast against the `widest` rule (methodology Sections 7.5, 11; rv_pairs.tex).

Steps:
1. Pull the monthly TRACE panel (one WRDS query per month, cached) and the Treasury par curves.
2. Link bond issuers to Compustat and build leverage as known at each month end.
3. Replay every month end: each predictor sees only data available at month end + 1 day.
4. Measure realised alpha over h months; score IC, calibration, long-short after cost, PIT, and the cycle test.
5. Write data/raw/backtest/*.parquet, summary_<tag>.json, and figures docs/writeup/figures/backtest_*.png.

Run from the repo root (WRDS access needed for uncached months):
    PYTHONPATH=. python3 scripts/backtest_alpha.py --start 2019-01 --end 2026-08 --tag pilot
    PYTHONPATH=. python3 scripts/backtest_alpha.py --start 2008-01 --end 2026-08 --tag full
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker  # noqa: F401
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hy import backtest as bt  # noqa: E402
from hy.sources import compustat_pit as cp  # noqa: E402
from hy.sources import trace_panel as tp  # noqa: E402
from hy.sources import treasury as tr  # noqa: E402

RAW = ROOT / "data" / "raw"
OUT = RAW / "backtest"
FIG = ROOT / "docs" / "writeup" / "figures"
FUND_START, FUND_END = "2006-06-01", "2026-09-30"   # one window for every run, so the per-issuer cache is reused
PREDICTORS = ["widest", "fair_conv", "fair_line", "fair_line_net"]
LABEL = {"widest": "widest (G-spread)", "fair_conv": "fair line, convergence only",
         "fair_line": "fair line, carry + convergence", "fair_line_net": "fair line, after cost"}
BLUE, ORANGE, AQUA, INK, MUTED, SHADE = "#2a78d6", "#eb6834", "#1baf7a", "#0b0b0b", "#52514e", "#e9e8e4"


def log(msg: str) -> None:
    print(msg, flush=True)


def curve_lookup(years: range):
    curves = pd.concat([tr.par_curve(y, RAW) for y in years]).sort_index()

    def curve_for(t: pd.Timestamp) -> pd.Series:
        return curves[curves.index <= t].iloc[-1]

    return curve_for


def build_inputs(months: list[pd.Timestamp], workers: int) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    timing = {}
    t0 = time.time()
    pulled = tp.pull_months(months, RAW, workers=workers, log=log)
    timing["trace_pull_s"] = time.time() - t0
    timing["trace_months_pulled"] = len(pulled)
    curve_for = curve_lookup(range(months[0].year - 1, months[-1].year + 1))
    panel = tp.build_panel(months, RAW, curve_for)
    con = cp.connect()
    t0 = time.time()
    sec = tp.security_table(con, RAW)
    links = tp.link_issuers(panel[["cusip6", "ticker"]], sec)
    panel = panel.merge(links, on=["cusip6", "ticker"], how="left")
    gvkeys = sorted(links["gvkey"].dropna().astype(str).unique())
    vint = tp.load_fundamentals(con, gvkeys, FUND_START, FUND_END, RAW, log=log)
    timing["fundamentals_pull_s"] = time.time() - t0
    fund = tp.leverage_history(vint, months)
    return panel, fund, timing


def coverage(panel: pd.DataFrame, fund: pd.DataFrame) -> dict:
    real = panel[~panel["carried"]]
    elig = real[bt.eligible(real)]
    lev = elig.merge(fund[["date", "gvkey", "leverage"]], on=["date", "gvkey"], how="left")
    keys = real[["cusip6", "ticker", "link_source"]].drop_duplicates()
    return {
        "months": int(real["date"].nunique()), "bond_months": int(len(real)), "bonds": int(real["cusip"].nunique()),
        "eligible_bond_months": int(len(elig)), "issuer_keys": int(len(keys)),
        "issuer_keys_linked_share": float((keys["link_source"] != "none").mean()),
        "link_source_counts": keys["link_source"].value_counts().to_dict(),
        "eligible_bond_months_with_leverage_share": float(lev["leverage"].notna().mean()),
        "issuers_with_leverage_per_month_median": float(fund.groupby("date")["gvkey"].nunique().median()),
        "exit_rows": int(panel["carried"].sum()),
        "bid_ask_source_share": real["bid_ask_source"].value_counts(normalize=True).round(3).to_dict(),
        "median_round_trip_cost_bp": float(bt.round_trip_cost(real).median() * 1e4),
    }


def run_horizon(panel: pd.DataFrame, fund: pd.DataFrame, h: int) -> tuple[pd.DataFrame, dict, bt.FairLine]:
    gross = bt.FairLine(mode="gross")
    preds = {"widest": bt.predict_widest, "fair_conv": bt.FairLine(mode="conv", memo=gross.memo, fits=gross.fits),
             "fair_line": gross, "fair_line_net": bt.FairLine(mode="net", memo=gross.memo, fits=gross.fits)}
    long = bt.run_predictions(panel, fund, preds, h, log=log)
    wide = long.pivot_table(index=["date", "cusip"], columns="predictor", values="alpha_hat").reset_index()
    as_of = pd.to_datetime(panel["available_at"]).max()
    real = bt.realised_excess_return(panel, h, as_of=as_of)
    cost = panel[["date", "cusip"]].assign(cost_rt=bt.round_trip_cost(panel))
    extra = panel[["date", "cusip", "gvkey", "link_source", "g_spread", "price"]]
    df = wide.merge(real, on=["date", "cusip"], how="inner").merge(cost, on=["date", "cusip"]).merge(extra, on=["date", "cusip"])
    df["realised_net"] = df["realised"] - df["cost_rt"]
    df = df[df["realised"].notna()]
    common = df.dropna(subset=PREDICTORS)
    res = {"n_bond_months_common": int(len(common)), "n_bond_months_all": int(len(df)), "predictors": {}}
    for p in PREDICTORS:
        ev = bt.evaluate(common, p, h)
        res["predictors"][p] = {k: v for k, v in ev.items() if not k.startswith("_")}
        if p != "widest":
            res["predictors"][p]["pit"] = bt.pit_summary(bt.pit_values(common, p, "realised", h))
    w = bt.evaluate(df.dropna(subset=["widest"]), "widest", h)
    res["widest_full_universe"] = {k: v for k, v in w.items() if not k.startswith("_")}
    # Skip a month: predict at t, earn from t+1 to t+1+h. A noisy month-end price sets both the spread signal and the
    # start of the return (bid-ask bounce); skipping a month removes that shared noise.
    skip = wide.assign(date=wide["date"] + pd.offsets.MonthEnd(1)).merge(real, on=["date", "cusip"]).merge(cost, on=["date", "cusip"])
    skip["realised_net"] = skip["realised"] - skip["cost_rt"]
    skip = skip.dropna(subset=PREDICTORS + ["realised"])
    res["skip_month"] = {p: {"ic_net": bt.hac_mean(bt.ic_series(skip, p, "realised_net"), h - 1),
                             "cycle_test_net": bt.cycle_test(bt.ic_series(skip, p, "realised_net")),
                             "mz": bt.mincer_zarnowitz(skip, p, "realised", h - 1)} for p in PREDICTORS}
    # Does the fair line add to spread level? Per date, remove from realised_net its linear fit on the spread rank;
    # then score the convergence term against what is left.
    res["beyond_spread"] = {p: bt.hac_mean(bt.ic_beyond(common, p, "realised_net", "widest"), h - 1)
                            for p in ("fair_conv", "fair_line_net")}
    c6 = common[common["link_source"] == "cusip6"]
    res["cusip6_links_only"] = {p: {"ic_net": bt.hac_mean(bt.ic_series(c6, p, "realised_net"), h - 1)} for p in PREDICTORS}
    rho = pd.Series({k: v[0] for k, v in gross.rho_log.items()})
    src = pd.Series({k: v[1] for k, v in gross.rho_log.items()})
    fits = pd.DataFrame(gross.fits).T
    res["rho_monthly_last"] = float(rho.iloc[-1])
    res["rho_first_fitted_month"] = str(src[src == "fitted"].index.min().date()) if (src == "fitted").any() else None
    res["fair_line_slope_median"] = float(fits["b"].median())
    res["fair_line_issuers_median"] = float(fits["n"].median())
    return df, res, gross


# ---------------------------------------------------------------- figures


def _shade_cycles(ax, years_axis: bool = True) -> None:
    for c, (a, b) in bt.CYCLE_WINDOWS.items():
        lo, hi = (pd.Timestamp(a).year - 0.5, pd.Timestamp(b).year + 0.5) if years_axis else (pd.Timestamp(a), pd.Timestamp(b))
        ax.axvspan(lo, hi, color=SHADE, zorder=0, lw=0)


def fig_ic_by_year(results: dict, frames: dict, tag: str) -> Path:
    hs = sorted(results)
    fig, axes = plt.subplots(len(hs), 1, figsize=(10, 3.4 * len(hs)), sharex=True)
    axes = np.atleast_1d(axes)
    for ax, h in zip(axes, hs):
        df = frames[h].dropna(subset=PREDICTORS)
        series = {p: bt.ic_by_year(bt.ic_series(df, p, "realised_net")) for p in ("widest", "fair_line_net")}
        years = sorted(set().union(*[s.index for s in series.values()]))
        _shade_cycles(ax)
        for k, (p, col) in enumerate([("widest", ORANGE), ("fair_line_net", BLUE)]):
            s = series[p].reindex(years)
            ax.bar(np.array(years) + (k - 0.5) * 0.38, s.to_numpy(), width=0.36, color=col, label=LABEL[p], zorder=2)
        ax.axhline(0, color=INK, lw=0.8)
        for p, col in [("widest", ORANGE), ("fair_line_net", BLUE)]:
            m = results[h]["predictors"][p]["ic_net"]
            ax.axhline(m["mean"], color=col, lw=1.2, ls="--", zorder=1)
        cyc = results[h]["predictors"]["fair_line_net"]["cycle_test_net"]
        cw = results[h]["predictors"]["widest"]["cycle_test_net"]
        ax.set_title(f"h = {h} months: rank IC after cost, by formation year "
                     f"(fair line positive in {cyc['cycles_positive']} of {cyc['cycles_with_data']} cycles with data; "
                     f"widest {cw['cycles_positive']})", fontsize=10, loc="left", color=INK)
        ax.set_ylabel("mean monthly IC", color=MUTED)
        ax.grid(axis="y", color="#dddcd8", lw=0.6, zorder=0)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.text(0.995, 0.97, "Good: bars above 0, most of all in the grey stress windows.\n"
                "Dashed lines: full-sample means. Project bar: IC > 0 in 3 of 4 cycles.",
                transform=ax.transAxes, ha="right", va="top", fontsize=8, color=MUTED)
    axes[0].legend(loc="lower left", fontsize=8, frameon=False)
    axes[-1].set_xlabel("formation year (grey = cycle window: 2008-09, 2015-16, 2020, 2022)", color=MUTED)
    for ax in axes:
        ax.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(2))
        ax.xaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter("%d"))
    fig.tight_layout()
    p = FIG / f"backtest_ic_by_year_{tag}.png"
    fig.savefig(p, dpi=150)
    plt.close(fig)
    return p


def fig_calibration(results: dict, frames: dict, tag: str) -> Path:
    hs = sorted(results)
    fig, axes = plt.subplots(1, len(hs), figsize=(5.2 * len(hs), 4.6))
    axes = np.atleast_1d(axes)
    for ax, h in zip(axes, hs):
        df = frames[h].dropna(subset=PREDICTORS)
        lims = []
        for p, col in [("fair_line", BLUE), ("fair_conv", AQUA)]:
            cal = bt.decile_calibration(df, p, "realised")
            x, y, e = cal["pred_mean"] * 1e4, cal["real_mean"] * 1e4, 1.96 * cal["real_se"] * 1e4
            mz = results[h]["predictors"][p]["mz"]
            ax.errorbar(x, y, yerr=e, fmt="o-", color=col, ms=5, lw=1.5, capsize=2,
                        label=f"{LABEL[p]}: MZ slope b = {mz['b']:.2f} (se {mz['se_b']:.2f})")
            lims += [x.min(), x.max(), y.min(), y.max()]
        lo, hi = min(lims), max(lims)
        ax.plot([lo, hi], [lo, hi], color=INK, lw=1, ls="--")
        ax.text(hi * 0.97, hi * 0.80, "45-degree line:\npredicted = realised", ha="right", va="top", fontsize=8, color=INK)
        ax.axhline(0, color="#c9c8c3", lw=0.8)
        ax.axvline(0, color="#c9c8c3", lw=0.8)
        ax.set_title(f"h = {h} months: realised against predicted alpha, by decile", fontsize=10, loc="left")
        ax.set_xlabel("predicted alpha, decile mean (bp over h)", color=MUTED)
        ax.set_ylabel("realised alpha, decile mean (bp over h)", color=MUTED)
        ax.text(0.02, 0.98, "Good: points on the dashed line (slope 1).\nFlatter than the line = the model is\n"
                "too confident: right order, too big.\nFlat on the left = a rich bond is not\npunished as predicted.",
                transform=ax.transAxes, va="top", fontsize=8, color=MUTED)
        ax.legend(loc="lower right", fontsize=7.5, frameon=False)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    fig.tight_layout()
    p = FIG / f"backtest_calibration_{tag}.png"
    fig.savefig(p, dpi=150)
    plt.close(fig)
    return p


def fig_long_short(results: dict, frames: dict, tag: str) -> Path:
    hs = sorted(results)
    fig, axes = plt.subplots(len(hs), 1, figsize=(12.5, 3.5 * len(hs)), sharex=True)
    axes = np.atleast_1d(axes)
    for ax, h in zip(axes, hs):
        df = frames[h].dropna(subset=PREDICTORS)
        _shade_cycles(ax, years_axis=False)
        for p, col in [("widest", ORANGE), ("fair_line", BLUE)]:
            ls = bt.long_short(df, p, "realised", "cost_rt")
            for kind, style in [("net", "-"), ("gross", ":")]:
                path = ls[kind].dropna().iloc[::h]
                w = (1 + path).cumprod()
                w = pd.concat([pd.Series([1.0], index=[path.index[0] - pd.offsets.MonthEnd(1)]), w])
                summ = results[h]["predictors"][p][f"long_short_{kind}"]
                lab = (f"{LABEL[p]}, {kind}:\n  mean {summ['ann_mean'] * 100:+.1f}% a year (t {summ['t']:.1f}), "
                       f"compounded {summ['cagr'] * 100:+.1f}% a year,\n  max drawdown {summ['max_drawdown'] * 100:.0f}%")
                ax.plot(w.index, w.to_numpy(), style, color=col, lw=2 if kind == "net" else 1.2, label=lab)
        ax.axhline(1, color=INK, lw=0.8)
        ax.set_yscale("log")
        ax.set_ylabel("growth of 1 (log)", color=MUTED)
        ax.set_title(f"h = {h} months: top minus bottom decile, held h months, rebalanced every h months",
                     fontsize=10, loc="left")
        ax.text(0.995, 0.03, "Good: the solid (after cost) line rises and its falls are shallow.\n"
                "Gap from dotted to solid = cost. Grey = cycle windows.\n"
                "Mean minus compounded = the cost of deep drawdowns.",
                transform=ax.transAxes, ha="right", va="bottom", fontsize=8, color=MUTED)
        ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0), fontsize=7.5, frameon=False)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    fig.tight_layout()
    p = FIG / f"backtest_long_short_{tag}.png"
    fig.savefig(p, dpi=150)
    plt.close(fig)
    return p


def _jsonable(o):
    if isinstance(o, dict):
        return {str(k): _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_jsonable(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return o


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2019-01")
    ap.add_argument("--end", default="2026-08")
    ap.add_argument("--h", type=int, nargs="+", default=[3, 6])
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--tag", default="pilot")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    months = tp.month_ends(a.start, a.end)
    t_all = time.time()
    panel, fund, timing = build_inputs(months, a.workers)
    panel.to_parquet(OUT / f"panel_{a.tag}.parquet", index=False)
    fund.to_parquet(OUT / f"leverage_{a.tag}.parquet", index=False)
    cov = coverage(panel, fund)
    log(f"coverage: {json.dumps(_jsonable(cov))}")
    results, frames = {}, {}
    for h in a.h:
        t0 = time.time()
        df, res, _ = run_horizon(panel, fund, h)
        timing[f"replay_h{h}_s"] = time.time() - t0
        df.to_parquet(OUT / f"results_h{h}_{a.tag}.parquet", index=False)
        results[h], frames[h] = res, df
        for p in PREDICTORS:
            r = res["predictors"][p]
            log(f"h={h} {p:14s} IC net {r['ic_net']['mean']:+.4f} (t {r['ic_net']['t']:.2f})  MZ b {r['mz']['b']:.2f}  "
                f"LS net {r['long_short_net']['ann_mean'] * 100:+.2f}%/y  cycles {r['cycle_test_net']['cycles_positive']}  "
                f"skip-month IC net {res['skip_month'][p]['ic_net']['mean']:+.4f} (t {res['skip_month'][p]['ic_net']['t']:.2f})")
    figs = [fig_ic_by_year(results, frames, a.tag), fig_calibration(results, frames, a.tag), fig_long_short(results, frames, a.tag)]
    timing["total_s"] = time.time() - t_all
    summary = {"tag": a.tag, "start": a.start, "end": a.end, "horizons": a.h, "coverage": cov, "timing": timing,
               "cycle_windows": bt.CYCLE_WINDOWS, "beta": bt.DEFAULT_BETA, "rho_prior_monthly": bt.RHO_PRIOR_M,
               "loss_term": False, "results": {str(h): r for h, r in results.items()},
               "figures": [str(f.relative_to(ROOT)) for f in figs]}
    path = OUT / f"summary_{a.tag}.json"
    if path.exists():  # keep blocks that other scripts add (scripts/backtest_clocks.py writes "clocks")
        summary = {**{k: v for k, v in json.loads(path.read_text()).items() if k not in summary}, **summary}
    path.write_text(json.dumps(_jsonable(summary), indent=1, default=str))
    log(f"done in {timing['total_s'] / 60:.1f} min; summary {OUT / f'summary_{a.tag}.json'}")


if __name__ == "__main__":
    main()
