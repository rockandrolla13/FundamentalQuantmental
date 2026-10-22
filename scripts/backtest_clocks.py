"""Backtest of the two-clocks signals (methodology Sections 4.7 and 11; combined score estimate E5).

Run after `scripts/backtest_alpha.py --tag full` (it reads that run's panel and results):
    PYTHONPATH=. python3 scripts/backtest_clocks.py --tag full

Steps:
1. Map each scored issuer (gvkey) to its SEC CIK through `comp.company`.
2. Fetch SEC companyfacts for each CIK (`hy/sources/clock_facts.py`; cached under data/raw/edgar/).
3. Build the Section 4.7 clocks at every 10-K and 10-Q (`clock_facts.filing_states`).
4. At each month end from 2018, take the latest filing known at month end + 1 day and form three signals:
   e5 = -(fixed charges in years of EBITDAR), dgap = -duration gap, renew = -renewal-dependent share (RPO material).
5. Score each like the alpha rules: rank IC after cost at h = 3 and 6 months (Newey-West t, h - 1 lags), the IC beyond
   spread level, and the 2020 and 2022 cycle windows. Write data/raw/backtest/clock_*.parquet, a "clocks" block in
   summary_<tag>.json, and docs/writeup/figures/backtest_clocks_<tag>.png.
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
import matplotlib.ticker
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from hy import backtest as bt  # noqa: E402
from hy.sources import clock_facts as cf  # noqa: E402
from hy.sources import compustat_pit as cp  # noqa: E402
from hy.sources import trace_panel as tp  # noqa: E402

RAW = ROOT / "data" / "raw"
OUT = RAW / "backtest"
FIG = ROOT / "docs" / "writeup" / "figures"
START = pd.Timestamp("2018-01-31")
SIGNALS = {"e5": "E5: -(fixed charges in years of EBITDAR)", "dgap": "-(duration gap)",
           "renew": "-(renewal-dependent share), RPO material"}
PREDICTORS = ["widest", "fair_conv", "fair_line", "fair_line_net"]
BLUE, ORANGE, AQUA, VIOLET, INK, MUTED, SHADE = "#2a78d6", "#eb6834", "#1baf7a", "#6250d6", "#0b0b0b", "#52514e", "#e9e8e4"


def log(msg: str) -> None:
    print(msg, flush=True)


def fundamentals_history(months: list[pd.Timestamp]) -> pd.DataFrame:
    """Leverage, LTM EBITDA, LTM revenue, and debt as known at each month (from the cached Compustat PIT pull)."""
    paths = sorted((RAW / "trace_panel").glob("fundamentals_*.parquet"), key=lambda p: p.stat().st_size)
    return tp.leverage_history(pd.read_parquet(paths[-1]), months)


def cik_map(gvkeys: list[str]) -> dict[str, str]:
    p = RAW / "trace_panel" / "comp_company_cik.parquet"
    if p.exists():
        c = pd.read_parquet(p)
    else:
        c = cp.connect().raw_sql("select gvkey, cik from comp.company where cik is not null")
        p.parent.mkdir(parents=True, exist_ok=True)
        c.to_parquet(p, index=False)
    c = c[c["gvkey"].isin(gvkeys)].dropna()
    return {str(g): f"{int(float(k)):010d}" for g, k in zip(c["gvkey"], c["cik"])}


def build_states(ciks: list[str]) -> pd.DataFrame:
    frames = []
    for c in sorted(set(ciks)):
        f = cf.load_facts(c, RAW)
        if len(f):
            s = cf.filing_states(f, c)
            if len(s):
                frames.append(s)
    return pd.concat(frames, ignore_index=True)


def monthly_signals(states: pd.DataFrame, fund: pd.DataFrame, cmap: dict[str, str], months: list[pd.Timestamp]) -> pd.DataFrame:
    out = []
    for m in months:
        as_of = bt.decision_time(m)
        f = fund[fund["date"] == m]
        s = cf.clock_signals_as_of(states, f, cmap, as_of)
        if len(s):
            out.append(s.assign(date=m))
    return pd.concat(out, ignore_index=True)


def score(df: pd.DataFrame, sig: str, h: int) -> dict:
    """Rank IC after cost (and gross), IC beyond spread level, widest on the same rows, cycles 2020 and 2022."""
    d = df.dropna(subset=[sig])
    ic_net = bt.ic_series(d, sig, "realised_net")
    by = bt.ic_by_window(ic_net)
    return {
        "ic_gross": bt.hac_mean(bt.ic_series(d, sig, "realised"), h - 1),
        "ic_net": bt.hac_mean(ic_net, h - 1),
        "ic_beyond_spread": bt.hac_mean(bt.ic_beyond(d, sig, "realised_net", "widest"), h - 1),
        "widest_same_rows": bt.hac_mean(bt.ic_series(d, "widest", "realised_net"), h - 1),
        "ic_net_by_year": {int(k): float(v) for k, v in bt.ic_by_year(ic_net).items()},
        "cycles_with_data": {c: by[c] for c in (2020, 2022)},
        "cycles_positive_of_covered": int(sum(by[c] > 0 for c in (2020, 2022) if np.isfinite(by[c]))),
        "spread_link": bt.hac_mean(bt.ic_series(d.assign(raw=-d[sig]), "raw", "g_spread"), h - 1),
        "coverage": {"bond_months": int(len(d)), "bonds": int(d["cusip"].nunique()), "issuers": int(d["gvkey"].nunique()),
                     "months": int(d["date"].nunique()), "first": str(d["date"].min().date()) if len(d) else None,
                     "bonds_per_month_median": float(d.groupby("date").size().median()) if len(d) else 0.0},
        "_ic_net": ic_net, "_beyond": bt.ic_beyond(d, sig, "realised_net", "widest"),
    }


def figure(res: dict, tag: str) -> Path:
    hs = sorted(res)
    fig, axes = plt.subplots(len(hs), 1, figsize=(10.5, 3.5 * len(hs)), sharex=True)
    axes = np.atleast_1d(axes)
    cols = {"e5": BLUE, "dgap": AQUA, "renew": VIOLET}
    for ax, h in zip(axes, hs):
        for c, (lo, hi) in [(2020, (2019.5, 2020.5)), (2022, (2021.5, 2022.5))]:
            ax.axvspan(lo, hi, color=SHADE, lw=0, zorder=0)
        sigs = [s for s in SIGNALS if res[h][s]["coverage"]["bond_months"] > 0]
        width = 0.8 / len(sigs)
        for k, s in enumerate(sigs):
            yr = pd.Series(res[h][s]["ic_net_by_year"])
            ax.bar(yr.index + (k - (len(sigs) - 1) / 2) * width, yr.to_numpy(), width=width * 0.95, color=cols[s],
                   label=f"{SIGNALS[s]}: IC {res[h][s]['ic_net']['mean']:+.3f} (t {res[h][s]['ic_net']['t']:.1f}); "
                         f"beyond spread {res[h][s]['ic_beyond_spread']['mean']:+.3f} "
                         f"(t {res[h][s]['ic_beyond_spread']['t']:.1f})", zorder=2)
        ax.axhline(0, color=INK, lw=0.8)
        ax.set_title(f"h = {h} months: rank IC after cost of the clock signals, by formation year", fontsize=10, loc="left")
        ax.set_ylabel("mean monthly IC", color=MUTED)
        ax.grid(axis="y", color="#dddcd8", lw=0.6, zorder=0)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        ax.text(0.995, 0.97, "Signs as the score uses them: higher = fewer years of fixed charges.\n"
                "Good: bars above 0, and a positive IC beyond spread. Grey = 2020 and 2022 cycles.",
                transform=ax.transAxes, ha="right", va="top", fontsize=8, color=MUTED)
        ax.legend(loc="lower left", fontsize=7.5, frameon=False)
    axes[-1].xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(1))
    axes[-1].xaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter("%d"))
    axes[-1].set_xlabel("formation year", color=MUTED)
    fig.tight_layout()
    p = FIG / f"backtest_clocks_{tag}.png"
    fig.savefig(p, dpi=150)
    plt.close(fig)
    return p


def _clean(o):
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items() if not str(k).startswith("_")}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, (float, np.floating)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return o


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="full")
    ap.add_argument("--h", type=int, nargs="+", default=[3, 6])
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    t_all = time.time()
    frames = {h: pd.read_parquet(OUT / f"results_h{h}_{a.tag}.parquet") for h in a.h}
    frames = {h: f[f["date"] >= START].dropna(subset=PREDICTORS) for h, f in frames.items()}
    months = sorted(set().union(*[set(f["date"]) for f in frames.values()]))
    gvkeys = sorted(set().union(*[set(f["gvkey"].dropna().astype(str)) for f in frames.values()]))
    cmap = cik_map(gvkeys)
    log(f"scored issuers since 2018: {len(gvkeys)}; with a CIK: {len(cmap)}")
    pull = cf.load_many(sorted(set(cmap.values())), RAW, workers=a.workers, log=log)
    log(f"companyfacts: {pull}")
    t0 = time.time()
    states = build_states(list(cmap.values()))
    states.to_parquet(OUT / f"clock_states_{a.tag}.parquet", index=False)
    fund = fundamentals_history(months)
    sig = monthly_signals(states, fund, cmap, months)
    sig.to_parquet(OUT / f"clock_signals_{a.tag}.parquet", index=False)
    build_s = time.time() - t0
    res = {}
    for h, f in frames.items():
        d = f.merge(sig[["date", "gvkey", "e5", "dgap", "renew", "fixed_charge_years", "rpo_material", "debt_source"]],
                    on=["date", "gvkey"], how="inner")
        res[h] = {s: score(d, s, h) for s in SIGNALS}
        res[h]["_n_rows"] = len(d)
        for s in SIGNALS:
            r = res[h][s]
            log(f"h={h} {s:6s} IC net {r['ic_net']['mean']:+.4f} (t {r['ic_net']['t']:.2f})  beyond spread "
                f"{r['ic_beyond_spread']['mean']:+.4f} (t {r['ic_beyond_spread']['t']:.2f})  widest same rows "
                f"{r['widest_same_rows']['mean']:+.3f}  cycles {r['cycles_with_data']}  n {r['coverage']}")
    fig = figure(res, a.tag)
    states_cov = {
        "ciks_with_facts": int(states["cik"].nunique()), "filings": int(len(states)),
        "first_filing": str(states["as_of"].min().date()), "rpo_filings_share": float(states["rpo_total"].notna().mean()),
        "gap_filled_share": float(states["gap_filled"].mean()),
        "carried_any_share": float((states["carried"] != "").mean()),
        "signal_issuer_months": int(len(sig)), "rpo_material_issuer_months": int(sig["rpo_material"].sum()),
        "compustat_debt_fallback_share": float((sig["debt_source"] == "compustat").mean()),
        "fixed_charge_years_median": float(sig["fixed_charge_years"].median()),
    }
    block = {"issuers_scored_since_2018": len(gvkeys), "issuers_with_cik": len(cmap), "pull": pull,
             "build_seconds": build_s, "states": states_cov,
             "results": {str(h): {s: r[s] for s in SIGNALS} for h, r in res.items()},
             "figure": str(fig.relative_to(ROOT)), "total_seconds": time.time() - t_all}
    p = OUT / f"summary_{a.tag}.json"
    summary = json.loads(p.read_text()) if p.exists() else {}
    summary["clocks"] = _clean(block)
    p.write_text(json.dumps(summary, indent=1, default=str))
    log(f"states: {json.dumps(_clean(states_cov))}")
    log(f"done in {(time.time() - t_all) / 60:.1f} min; clocks block in {p}")


if __name__ == "__main__":
    main()
