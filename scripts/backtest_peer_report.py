"""Figures for docs/writeup/backtest_peer_line.tex (decision page 2026-10-23-peer-fair-spread).

Reads data/raw/backtest/summary_peer_line_<tag>.json and portfolios_<tag>.parquet from scripts/backtest_peer_line.py
(run it twice: default and --keep-distressed), plus the cached replay for the worked example. Writes
docs/writeup/figures/peer_*.png. Colour follows the entity in every figure: widest orange, old leverage line blue,
peer line aqua (palette validated with the dataviz skill; aqua and yellow sit below 3:1, so every line is labelled).

    PYTHONPATH=. python3 scripts/backtest_peer_report.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from hy import backtest as bt  # noqa: E402
from hy.data.config import CONFIG  # noqa: E402

OUT = CONFIG.path("backtest")
FIG = ROOT / "docs" / "writeup" / "figures"
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, MUTED, GRID, SHADE, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#efeeea", "#fcfcfb"
GOOD, BAD = "#0ca30c", "#d03b3b"
COLOR = {"widest": ORANGE, "fair_line_net": BLUE, "peer_line_net": AQUA, "peer_carry_net": AQUA}
NAME = {"widest": "Buy the widest", "fair_line_net": "Old leverage line", "peer_line_net": "Peer gap",
        "peer_carry_net": "Peer gap + carry"}
plt.rcParams.update({"font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": MUTED, "xtick.color": MUTED,
                     "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF})


def shade_cycles(ax) -> None:
    for a, b in bt.CYCLE_WINDOWS.values():
        ax.axvspan(pd.Timestamp(a), pd.Timestamp(b), color=SHADE, zorder=0, lw=0)
    ax.text(pd.Timestamp("2008-01-01"), 1.0, " stress windows shaded", transform=ax.get_xaxis_transform(),
            va="top", fontsize=7, color=MUTED)


def fig_anatomy() -> Path:
    """Two real bonds, June 2023, 6 months: the forecast and the realised return built term by term."""
    panel = pd.read_parquet(OUT / "panel_full.parquet")
    bench = bt.benchmark_spread(panel, pd.to_datetime(panel["available_at"]).max())
    res = pd.read_parquet(OUT / "results_h6_full.parquet")
    sig = pd.read_parquet(OUT / "peer_signals_full.parquet", columns=["date", "cusip", "esp_sr"])
    t = pd.Timestamp("2023-06-30")
    rows = {"161175BS2": "Rich against peers\n(B, 26 years, price 78)", "071734AH0": "Distressed, cheap against peers\n(B, 4.6 years, price 42)"}
    d = res[(res["date"] == t) & res["cusip"].isin(rows)].merge(sig, on=["date", "cusip"]) \
        .merge(panel[["date", "cusip", "mod_dur"]], on=["date", "cusip"]).set_index("cusip")
    rho = bt.RHO_PRIOR_M
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.6))
    for ax, (cu, title) in zip(axes, rows.items()):
        r = d.loc[cu]
        S = bench[t]
        beta = r["g_spread"] / S
        fair = r["g_spread"] * np.exp(-r["esp_sr"])
        fc = r["mod_dur"] * (1 - rho ** 6) * (r["g_spread"] - fair) - r["cost_rt"]
        terms = [("Bond: price + coupon", r["total"]), ("- Treasury", -r["tsy_ret"]),
                 (f"- {beta:.2f} x HY index", -beta * r["bench_ret"]), ("- cost", -r["cost_rt"])]
        tops = np.cumsum([0.0] + [v for _, v in terms]) * 1e4
        span = max(np.max(np.abs(tops)), abs(fc) * 1e4) * 1.0
        off = 0.04 * span
        run = 0.0
        for i, (lab, v) in enumerate(terms):
            ax.bar(i, v * 1e4, bottom=run * 1e4, color=GOOD if v >= 0 else BAD, width=0.6, alpha=0.85)
            ax.text(i, (run + v) * 1e4 + (off if v >= 0 else -off), f"{v * 1e4:+.0f}", ha="center",
                    va="bottom" if v >= 0 else "top", fontsize=8, color=INK)
            run += v
        real = run
        ax.bar(len(terms), real * 1e4, color=MUTED, width=0.6)
        ax.text(len(terms), real * 1e4 + (off if real >= 0 else -off), f"{real * 1e4:+.0f}", ha="center",
                va="bottom" if real >= 0 else "top", fontsize=8, fontweight="bold", color=INK)
        ax.bar(len(terms) + 1.2, fc * 1e4, color=AQUA, width=0.6)
        ax.text(len(terms) + 1.2, fc * 1e4 + (off if fc >= 0 else -off), f"{fc * 1e4:+.0f}", ha="center",
                va="bottom" if fc >= 0 else "top", fontsize=8, fontweight="bold", color=INK)
        ax.set_xticks(list(range(len(terms))) + [len(terms), len(terms) + 1.2])
        ax.set_xticklabels([t_ for t_, _ in terms] + ["Realised", "Forecast"], rotation=30, ha="right", fontsize=7.5)
        ax.axhline(0, color=MUTED, lw=0.8)
        ax.set_title(title, fontsize=9, loc="left", color=INK)
        ax.set_ylabel("bp of price over 6 months")
        ax.grid(axis="y", color=GRID, lw=0.6)
        lo = min(0.0, tops.min(), fc * 1e4)
        hi = max(0.0, tops.max(), fc * 1e4)
        ax.set_ylim(lo - 0.18 * (hi - lo), hi + 0.30 * (hi - lo))
        ax.text(0.02, 0.97, f"spread {r['g_spread'] * 1e4:.0f} bp, peers {fair * 1e4:.0f} bp, DTS beta {beta:.2f}",
                transform=ax.transAxes, ha="left", va="top", fontsize=7, color=MUTED)
    fig.suptitle("Recipe of one backtest row, June 2023 to December 2023 (spread-move hedge, TRACE cost)", x=0.01, ha="left",
                 fontsize=10, color=INK)
    fig.tight_layout()
    p = FIG / "peer_anatomy.png"
    fig.savefig(p, dpi=200)
    plt.close(fig)
    return p


def fig_wealth(port: pd.DataFrame) -> Path:
    """Growth of 1 in the quarterly books, after turnover cost, distressed bonds out; one panel per hedge."""
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.8), sharey=False)
    specs = {"carry_kept": [("widest", "decile", "-"), ("fair_line_net", "decile", "-"), ("peer_carry_net", "decile", "-"),
                            ("peer_carry_net", "spread_neutral", "--")],
             "spread_move": [("widest", "decile", "-"), ("fair_line_net", "decile", "-"), ("peer_line_net", "decile", "-"),
                             ("peer_line_net", "spread_neutral", "--")]}
    titles = {"carry_kept": "Carry kept: hedge 1 x HY index", "spread_move": "Spread move only: DTS hedge"}
    for ax, (hedge, books) in zip(axes, specs.items()):
        shade_cycles(ax)
        ends = []
        for pred, book, ls in books:
            s = port[(port["hedge"] == hedge) & (port["predictor"] == pred) & (port["book"] == book)
                     & (port["timing"] == "same_month")].set_index("date")["net_turnover"].sort_index()
            w = (1 + s).cumprod()
            lab = NAME[pred] + (", spread-neutral" if book == "spread_neutral" else "")
            ax.plot(w.index, w.values, color=COLOR[pred], lw=2, ls=ls)
            ends.append((w.iloc[-1], lab, COLOR[pred]))
        ends.sort()
        lo, hi = ax.get_ylim()
        gap = (hi - lo) * 0.07
        placed = []
        for v, lab, c in ends:
            y = v if not placed or v - placed[-1] > gap else placed[-1] + gap
            placed.append(y)
            ax.text(w.index[-1] + pd.Timedelta(days=60), y, f"{lab} {v:.2f}", fontsize=7, color=INK, va="center")
            ax.plot([w.index[-1], w.index[-1] + pd.Timedelta(days=50)], [v, y], color=c, lw=0.8)
        ax.axhline(1, color=MUTED, lw=0.8)
        ax.set_title(titles[hedge], fontsize=9, loc="left", color=INK)
        ax.set_ylabel("growth of 1, after 15 bp cost")
        ax.grid(axis="y", color=GRID, lw=0.6)
        ax.set_xlim(right=w.index[-1] + pd.Timedelta(days=2300))
        ax.set_xticks([pd.Timestamp(f"{y}-01-01") for y in range(2008, 2027, 4)])
        ax.set_xticklabels([str(y) for y in range(2008, 2027, 4)])
        ax.spines["bottom"].set_bounds(mdates.date2num(pd.Timestamp("2008-01-01")), mdates.date2num(w.index[-1]))
    fig.suptitle("Quarterly long-short books, 2008 to 2026, distressed out, 15 bp cost (solid: decile, dashed: spread-neutral)",
                 x=0.01, ha="left", fontsize=10, color=INK)
    fig.tight_layout()
    p = FIG / "peer_wealth.png"
    fig.savefig(p, dpi=200)
    plt.close(fig)
    return p


def fig_cost(summary: dict, proxy: dict) -> Path:
    """Gross and net per year for each book at 15 bp of price per round trip, with the TRACE-proxy net beside it."""
    rows = []
    for hedge in ("carry_kept", "spread_move"):
        for key, v in summary["portfolios"][hedge].items():
            pred, book, timing = key.split("|")
            if timing != "same_month":
                continue
            pk = key.replace("peer_carry_net", "peer_carry_net")
            pv = proxy["portfolios"][hedge].get(pk, {})
            rows.append((hedge, NAME[pred] + (" (spread-neutral)" if book == "spread_neutral" else ""), pred,
                         v["gross"]["ann_mean"], v["cost_turnover_per_quarter"] * 4, v["net_turnover"]["ann_mean"],
                         pv.get("net_turnover", {}).get("ann_mean", np.nan)))
    df = pd.DataFrame(rows, columns=["hedge", "label", "pred", "gross", "cost", "net", "net_proxy"])
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.4), sharex=True)
    titles = {"carry_kept": "Carry kept", "spread_move": "Spread move only"}
    for ax, hedge in zip(axes, ("carry_kept", "spread_move")):
        d = df[df["hedge"] == hedge].reset_index(drop=True)
        y = np.arange(len(d))[::-1]
        for yi, r in zip(y, d.itertuples()):
            ax.annotate("", xy=(r.net * 100, yi), xytext=(r.gross * 100, yi),
                        arrowprops=dict(arrowstyle="->", color=MUTED, lw=1))
            ax.plot(r.gross * 100, yi, "o", color=COLOR[r.pred], ms=8, mec=SURF, mew=2)
            ax.plot(r.net * 100, yi, "s", color=GOOD if r.net > 0 else BAD, ms=7, mec=SURF, mew=2)
            ax.plot(r.net_proxy * 100, yi, "x", color=MUTED, ms=6, mew=1.2)
            ax.text(max(r.gross, r.net) * 100 + 0.3, yi, f"cost {r.cost * 100:.1f}%", va="center", fontsize=7, color=MUTED)
        ax.set_yticks(y)
        ax.set_yticklabels(d["label"], fontsize=7.5)
        ax.axvline(0, color=MUTED, lw=0.8)
        ax.set_xlabel("% a year")
        ax.set_title(titles[hedge], fontsize=9, loc="left", color=INK)
        ax.grid(axis="x", color=GRID, lw=0.6)
    fig.suptitle("Circle: before cost.  Square: after 15 bp a round trip (0.6 to 0.7 points a year).  "
                 "x: after the TRACE proxy (2.5 to 3 points).", x=0.01, ha="left", fontsize=9.5, color=INK)
    fig.tight_layout()
    p = FIG / "peer_cost.png"
    fig.savefig(p, dpi=200)
    plt.close(fig)
    return p


def fig_distressed(ex: dict, al: dict) -> Path:
    """Before and after: the carry-kept decile books with and without bonds at 1,000 bp and wider."""
    preds = ["widest", "fair_line_net", "peer_carry_net"]
    fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.0))
    for ax, (metric, lab) in zip(axes, (("ann_mean", "return after turnover cost, % a year"),
                                         ("max_drawdown", "worst drawdown, %"))):
        y = np.arange(len(preds))[::-1]
        for yi, p in zip(y, preds):
            k = f"{p}|decile|same_month"
            a_ = al["portfolios"]["carry_kept"][k]["net_turnover"][metric] * 100
            e_ = ex["portfolios"]["carry_kept"][k]["net_turnover"][metric] * 100
            ax.plot([a_, e_], [yi, yi], color=GRID, lw=3, zorder=1)
            ax.plot(a_, yi, "o", color=MUTED, ms=8, mec=SURF, mew=2, zorder=2)
            ax.plot(e_, yi, "o", color=COLOR[p], ms=8, mec=SURF, mew=2, zorder=2)
            ax.text(a_, yi + 0.22, f"{a_:+.1f}", ha="center", fontsize=7, color=MUTED)
            ax.text(e_, yi + 0.22, f"{e_:+.1f}", ha="center", fontsize=7, color=INK)
        ax.set_yticks(y)
        ax.set_yticklabels([NAME[p] for p in preds], fontsize=8)
        ax.set_xlabel(lab)
        ax.axvline(0, color=MUTED, lw=0.8)
        ax.grid(axis="x", color=GRID, lw=0.6)
        ax.set_ylim(-0.5, len(preds) - 0.4)
    axes[0].set_title("grey: all bonds   colour: distressed out", fontsize=8, loc="left", color=MUTED)
    fig.suptitle("Distressed bonds bring a high return with a deep drawdown: the default premium, not skill",
                 x=0.01, ha="left", fontsize=10, color=INK)
    fig.tight_layout()
    p = FIG / "peer_distressed.png"
    fig.savefig(p, dpi=200)
    plt.close(fig)
    return p


def fig_beyond(ex: dict) -> Path:
    """IC beyond spread level with a month skipped, by horizon and hedge; cycles positive written on each bar."""
    fig, ax = plt.subplots(figsize=(7.2, 3.0))
    items = [("spread_move", "fair_line_net"), ("spread_move", "peer_line_net"),
             ("carry_kept", "fair_line_net"), ("carry_kept", "peer_carry_net")]
    hs = [h for h in ("3", "6", "12") if h in ex["horizons"]]
    width = 0.2
    for i, (hedge, p) in enumerate(items):
        for j, h in enumerate(hs):
            x = ex["horizons"][h].get(hedge, {}).get("skip_month", {}).get(p)
            if not x or not x.get("beyond_spread"):
                continue
            v, c = x["beyond_spread"]["mean"], x["beyond_spread_cycles"]["cycles_positive"]
            xpos = j + (i - 1.5) * width
            ax.bar(xpos, v, width * 0.9, color=COLOR[p], alpha=1.0 if hedge == "spread_move" else 0.55,
                   hatch=None if hedge == "spread_move" else "//", edgecolor=SURF)
            ax.text(xpos, v + 0.004, f"{c}/4", ha="center", fontsize=7, color=INK)
    ax.set_xticks(range(len(hs)))
    ax.set_xticklabels([f"{h} months" for h in hs])
    ax.set_ylabel("rank IC beyond spread level")
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.axhline(0, color=MUTED, lw=0.8)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=BLUE, label="Old line, spread move"), Patch(color=AQUA, label="Peer gap, spread move"),
                       Patch(facecolor=BLUE, alpha=0.55, hatch="//", label="Old line + carry"),
                       Patch(facecolor=AQUA, alpha=0.55, hatch="//", label="Peer gap + carry")],
              fontsize=7, frameon=False, loc="upper left")
    ax.set_title("What the signal adds once spread level is held fixed (month skipped; label = cycles positive)",
                 fontsize=9, loc="left", color=INK)
    fig.tight_layout()
    p = FIG / "peer_beyond.png"
    fig.savefig(p, dpi=200)
    plt.close(fig)
    return p


def pct(x: float, nd: int = 1) -> str:
    return "--" if x is None or x != x else f"{x * 100:+.{nd}f}"


def tables(ex: dict, al: dict, proxy: dict) -> Path:
    """LaTeX tables for the document, written from the JSON results so no number is copied by hand."""
    L = []
    # Table 1: rank IC after cost, same month and skip a month, both hedges, 3/6/12 months.
    L.append("% generated by scripts/backtest_peer_report.py -- do not edit")
    L.append("\\newcommand{\\PeerIcTable}{\\begin{tabular}{llrrrrr}\\toprule")
    L.append("Hedge & Signal & h & IC & $t$ & Skip a month & Beyond spread, skip \\\\ \\midrule")
    for hedge, preds in (("carry_kept", ["widest", "fair_line_net", "peer_carry_net"]),
                         ("spread_move", ["widest", "fair_line_net", "peer_line_net"])):
        for h in ("3", "6", "12"):
            x = ex["horizons"].get(h, {}).get(hedge)
            if not x:
                continue
            for p in preds:
                if p not in x["predictors"]:
                    continue
                ic, sk = x["predictors"][p]["ic_net"], x["skip_month"][p]
                bs = sk.get("beyond_spread")
                bsc = sk.get("beyond_spread_cycles")
                L.append(f"{hedge.replace('_', ' ')} & {NAME[p]} & {h} & {ic['mean']:+.3f} & {ic['t']:.1f} & "
                         f"{sk['ic_net']['mean']:+.3f} ({sk['cycle_test_net']['cycles_positive']}/4) & "
                         + (f"{bs['mean']:+.3f} ($t$ {bs['t']:.1f}, {bsc['cycles_positive']}/4)" if bs else "--") + " \\\\")
            L.append("\\addlinespace")
    L.append("\\bottomrule\\end{tabular}}")
    # Table 2: quarterly books at 15 bp (and the TRACE proxy net).
    L.append("\\newcommand{\\PeerBookTable}{\\begin{tabular}{lllrrrrrrr}\\toprule")
    L.append("Hedge & Book & Timing & Gross & Net 15 bp & Net TRACE & Sharpe & Vol & Worst DD & Cycles \\\\ \\midrule")
    for hedge in ("carry_kept", "spread_move"):
        for key, v in ex["portfolios"][hedge].items():
            pred, book, timing = key.split("|")
            n, g = v["net_turnover"], v["gross"]
            pr = proxy["portfolios"][hedge].get(key, {}).get("net_turnover", {}).get("ann_mean")
            L.append(f"{hedge.replace('_', ' ')} & {NAME[pred]}{' (s-n)' if book == 'spread_neutral' else ''} & "
                     f"{timing.replace('_month', '')} & {pct(g['ann_mean'])} & {pct(n['ann_mean'])} & {pct(pr)} & "
                     f"{n['sharpe']:+.2f} & {n['ann_vol'] * 100:.1f} & {n['max_drawdown'] * 100:.0f} & "
                     f"{n['cycles_positive']}/{n['cycles_with_data']} \\\\")
        L.append("\\addlinespace")
    L.append("\\bottomrule\\end{tabular}}")
    # Table 3: distressed in and out, carry kept, decile, same month.
    L.append("\\newcommand{\\PeerDistressTable}{\\begin{tabular}{lrrrrrr}\\toprule")
    L.append("Book & \\multicolumn{3}{c}{All bonds} & \\multicolumn{3}{c}{Distressed out} \\\\")
    L.append(" & Net & Sharpe & Worst DD & Net & Sharpe & Worst DD \\\\ \\midrule")
    for p in ("widest", "fair_line_net", "peer_carry_net"):
        k = f"{p}|decile|same_month"
        a_, e_ = al["portfolios"]["carry_kept"][k]["net_turnover"], ex["portfolios"]["carry_kept"][k]["net_turnover"]
        L.append(f"{NAME[p]} & {pct(a_['ann_mean'])} & {a_['sharpe']:+.2f} & {a_['max_drawdown'] * 100:.0f} & "
                 f"{pct(e_['ann_mean'])} & {e_['sharpe']:+.2f} & {e_['max_drawdown'] * 100:.0f} \\\\")
    L.append("\\bottomrule\\end{tabular}}")
    out = ROOT / "docs" / "writeup" / "peer_tables.tex"
    out.write_text("\n".join(L) + "\n")
    return out


def main() -> None:
    # Main case: the user's execution cost, 15 bp of price per round trip (top of 12 to 15 bp); the TRACE bid-ask
    # proxy is the sensitivity.
    ex = json.loads((OUT / "summary_peer_line_ex_distressed_cost15.json").read_text())
    al = json.loads((OUT / "summary_peer_line_all_cost15.json").read_text())
    proxy = json.loads((OUT / "summary_peer_line_ex_distressed.json").read_text())
    port = pd.read_parquet(OUT / "portfolios_ex_distressed_cost15.parquet")
    for p in (fig_anatomy(), fig_wealth(port), fig_cost(ex, proxy), fig_distressed(ex, al), fig_beyond(ex),
              tables(ex, al, proxy)):
        print(f"wrote {p}")


if __name__ == "__main__":
    main()
