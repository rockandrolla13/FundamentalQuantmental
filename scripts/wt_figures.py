"""Figures for the Wolfe Trahan write-up (docs/writeup/wt_relationships.tex).

Run after scripts/wt_tests.py:
    PYTHONPATH=. python3 scripts/wt_figures.py
Writes docs/writeup/figures/wt_scorecard.png, wt_h1_story.png, wt_exposure.png.
"""

from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import wt_tests as w  # noqa: E402

FIG = ROOT / "docs/writeup/figures"
GOOD, BAD, GREY, BLUE = "#2E7D4F", "#B5403A", "#9A9A9A", "#2F5D8A"
OUTCOME_WORDS = {"dv_k2": "cost ratio, 2q", "dsg_k4": "sales growth, 4q", "dsg_k2": "sales growth, 2q",
                 "debitda_k4": "EBITDA, 4q", "dmargin_k4": "margin, 4q", "decline_k4": "EBITDA decline odds, 4q"}


def load_results() -> list[dict]:
    return [json.loads(Path(f).read_text()) for f in sorted(glob.glob(str(ROOT / "data/raw/backtest/wt_firm_*.json")))]


def scorecard(results: list[dict]) -> None:
    """Claim-signed t before the note (x) against after it (y). Top right = held in both periods."""
    pts = []
    for r in results:
        for kind, marker in (("A", "o"), ("A_high_leverage", "^"), ("B", "s")):
            for o in r[kind]:
                s = o["sign_claimed"]
                x, y = o["regression"]["claim_period"]["t"], o["regression"]["holdout"]["t"]
                if x is None or y is None or not (np.isfinite(x) and np.isfinite(y)):
                    continue
                lab = o.get("group") or f"{o['target']} vs {o['comparison']}"
                lab = ("high-leverage " if kind == "A_high_leverage" else "") + lab
                pts.append(dict(x=s * x, y=s * y, m=marker, ok=o["pass"], claim=r["claim"], lab=lab, out=o["outcome"]))
    d = pd.DataFrame(pts)
    fig, ax = plt.subplots(figsize=(9.5, 7.2))
    lim = 6.5
    ax.axhspan(2, lim, xmin=(2 + lim) / (2 * lim), color=GOOD, alpha=0.07)
    for v in (0,):
        ax.axhline(v, color="black", lw=0.8)
        ax.axvline(v, color="black", lw=0.8)
    for v in (-2, 2):
        ax.axhline(v, color=GREY, lw=0.6, ls="--")
        ax.axvline(v, color=GREY, lw=0.6, ls="--")
    for m, name in (("o", "A: average firm in the group"), ("^", "A-HL: high-leverage firms only"),
                    ("s", "B: group minus comparison, same quarter")):
        sel = d[d["m"] == m]
        ax.scatter(sel["x"], sel["y"], marker=m, s=46, c=np.where(sel["ok"], GOOD, GREY),
                   edgecolor="white", linewidth=0.6, label=name, zorder=3)
    offsets = [(-150, 40), (-60, -50), (25, -55)]
    for (_, p), off in zip(d[d["ok"]].sort_values("y", ascending=False).iterrows(), offsets):
        ax.annotate(f"{p['claim']} {p['lab']}: {OUTCOME_WORDS[p['out']]}", (p["x"], p["y"]), xytext=off,
                    textcoords="offset points", fontsize=8, color=GOOD,
                    arrowprops=dict(arrowstyle="-", color=GOOD, lw=0.6))
    n_both = int(((d["x"] > 2) & (d["y"] > 2)).sum())
    n_wrong = int((d["y"] < -2).sum())
    ax.text(lim - 0.2, lim - 0.3, f"held in both periods: {n_both}", ha="right", va="top", fontsize=10, color=GOOD,
            weight="bold")
    ax.text(-lim + 0.2, -2.3, f"wrong way after 2011 (t < -2): {n_wrong},\nall input-price tests (H1)",
            ha="left", va="top", fontsize=9, color=BAD)
    ax.text(lim - 0.2, -lim + 0.3, "held to 2011,\nwrong way after", ha="right", va="bottom", fontsize=10, color=BAD)
    ax.text(-lim + 0.2, lim - 0.3, "only after 2011", ha="left", va="top", fontsize=10, color="#555555")
    ax.text(-lim + 0.2, -lim + 0.3, "wrong way in both", ha="left", va="bottom", fontsize=10, color=BAD)
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_xlabel("t-statistic in the claimed direction, 1994-2011 (what the notes could see)")
    ax.set_ylabel("t-statistic in the claimed direction, 2012-2026 (the true test)")
    ax.set_title(f"{len(d)} tests. {n_both} held the claimed way in both periods (|t| > 2). "
                 f"{int(d['ok'].sum())} passed every rule (green).", fontsize=11.5, loc="left")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.24), ncol=2, frameon=False, fontsize=8.5)
    fig.text(0.01, 0.005, "Dashed lines: |t| = 2. Each point is one test: a group, an outcome, and a firm set. "
             "Newey-West t with controls (survey activity, Baa spread change, bank lending standards, own lag).",
             fontsize=7.5, color="#555555")
    fig.tight_layout()
    fig.savefig(FIG / "wt_scorecard.png", dpi=160)
    plt.close(fig)


def h1_story() -> None:
    """Prices paid against what the average industrial firm did next: costs, then sales."""
    macro = w.build_macro(ROOT / "data/raw/macro")
    W, info = w.firm_matrices(pd.read_parquet(ROOT / "data/raw/compustat/fundq_nonfin.parquet"))
    out, hl = w.firm_outcomes(W), w.high_leverage(W)
    ind = w.group_members(info, "Industrials")
    dv_hl = w.group_mean(out["dv_k2"], ind, hl)
    dsg = w.group_mean(out["dsg_k4"], ind)
    z = w.make_signal(macro, "PPC", "change2")
    qs = pd.period_range("1994Q1", "2026Q2", freq="Q")
    x = qs.to_timestamp()
    fig, axs = plt.subplots(3, 1, figsize=(10, 8.2), sharex=True, gridspec_kw={"height_ratios": [1.1, 1, 1]})
    for ax in axs:
        for c, (a, b) in w.CYCLE_WINDOWS.items():
            ax.axvspan(pd.Timestamp(a), pd.Timestamp(b), color=GREY, alpha=0.15, lw=0)
        ax.axhline(0, color="black", lw=0.7)
    zz = z.reindex(qs)
    axs[0].plot(x, zz, color=BLUE, lw=1.4)
    on = zz > 1
    axs[0].scatter(x[on.to_numpy()], zz[on], color=BAD, s=18, zorder=3, label="signal: z > 1")
    axs[0].set_ylabel("prices paid,\n6-month jump (z)")
    axs[0].set_title("H1. Input-price jumps came as demand recovered. Costs then rose a little; sales sped up.",
                     loc="left", fontsize=11.5)
    for lab, q in (("2009 recovery", "2009Q3"), ("2020-21 reopening", "2020Q4"), ("2004", "2004Q1")):
        p = pd.Period(q, "Q")
        axs[0].annotate(lab, (p.to_timestamp(), zz[p]), xytext=(4, 8), textcoords="offset points", fontsize=8,
                        color=BAD)
    axs[0].legend(loc="lower left", fontsize=8, frameon=False)
    axs[1].bar(x, 100 * dv_hl.reindex(qs), width=70, color=np.where(dv_hl.reindex(qs) > 0, BAD, GOOD))
    axs[1].set_ylabel("cost / sales, next 2q\n(pts, high-leverage\nindustrials)")
    axs[1].text(0.01, 0.97, "Red = costs rose faster than sales (margin squeeze). After jumps, the squeeze is real\n"
                "but small: +0.2 pts per 1 sd (t = 3.7 to 2011, 3.1 after).", transform=axs[1].transAxes,
                fontsize=8, va="top", bbox=dict(facecolor="white", edgecolor="none", alpha=0.85))
    axs[2].bar(x, 100 * dsg.reindex(qs), width=70, color=np.where(dsg.reindex(qs) < 0, BAD, GOOD))
    axs[2].set_ylabel("sales growth change,\nnext 4q (pts, average\nindustrial firm)")
    axs[2].text(0.01, 0.92, "The claim says sales slow after a jump. They sped up instead (t = +5.2 after 2011): "
                "the jumps marked recoveries.", transform=axs[2].transAxes, fontsize=8, va="top")
    fig.text(0.01, 0.005, "Grey bands: the cycle windows 2008-09, 2015-16, 2020, 2022. Equal-weighted firm means; "
             "about 550 industrial firms a quarter.", fontsize=7.5, color="#555555")
    fig.tight_layout()
    fig.savefig(FIG / "wt_h1_story.png", dpi=160)
    plt.close(fig)


def exposure(results: list[dict]) -> None:
    """Test C: does a firm's past sensitivity to the signal carry over? Coefficient after 2011 with a 2-se bar."""
    rows = []
    for r in results:
        for o in r["C"]:
            h = o["holdout"]
            if h["coef"] is None or not np.isfinite(h["coef"]):
                continue
            se = abs(h["coef"] / h["t"]) if h["t"] else np.nan
            rows.append(dict(lab=f"{r['claim']}  {r['signal'].split(' ')[0]} -> {OUTCOME_WORDS[o['outcome']]}",
                             c=h["coef"], se=se, t=h["t"]))
    d = pd.DataFrame(rows).sort_values("c")
    fig, ax = plt.subplots(figsize=(9.5, 0.32 * len(d) + 1.6))
    y = np.arange(len(d))
    col = np.where(d["t"].abs() > 3, np.where(d["c"] > 0, GOOD, BAD), GREY)
    ax.barh(y, d["c"], xerr=2 * d["se"], color=col, error_kw=dict(ecolor="#666666", lw=0.8))
    ax.set_yticks(y, d["lab"], fontsize=8)
    ax.axvline(0, color="black", lw=0.8)
    ax.axvline(1, color=GOOD, lw=0.8, ls="--")
    ax.text(1.02, len(d) - 0.6, "1 = a firm's past\nsensitivity carries\nover in full", fontsize=8, color=GOOD, va="top")
    ax.text(0.02, -0.9, "0 = no carry-over", fontsize=8, color="#555555")
    ax.set_xlabel("carry-over of each firm's own past sensitivity (Fama-MacBeth slope), 2012-2026")
    ax.set_title("Test C. For some signals, firms that reacted more before reacted more again.\n"
                 "Green = |t| > 3 and positive.", loc="left", fontsize=11)
    fig.tight_layout()
    fig.savefig(FIG / "wt_exposure.png", dpi=160)
    plt.close(fig)


def main() -> None:
    res = load_results()
    scorecard(res)
    exposure(res)
    h1_story()
    print("wrote", FIG / "wt_scorecard.png", FIG / "wt_h1_story.png", FIG / "wt_exposure.png")


if __name__ == "__main__":
    main()
