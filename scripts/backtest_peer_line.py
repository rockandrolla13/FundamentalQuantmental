"""Backtest of the peer fair spread with the DTS hedge (methodology 7.2, 7.5, 11; decision page
2026-10-23-peer-fair-spread).

Steps:
1. Read the cached replay (results_h<h>_full.parquet: realised parts, cost, the old fair line and widest), the
   monthly peer signals (peer_signals_full.parquet: ESP per bond against sector x rating x maturity peers) and the
   panel (mod_dur, the HY benchmark spread).
2. Peer forecast per bond-month: D (1 - rho^h) (s - s exp(-ESP_sr)) less the round-trip cost. rho comes from past
   issuer ESP only (`hy.backtest.peer_rho`). With the DTS hedge the carry term is zero.
3. Realised with the DTS hedge: total - tsy - (s / S) x the index leg (`hy.backtest.dts_realised`).
4. Leave distressed bonds out (spread >= 1,000 bp at formation; `hy.backtest.not_distressed`) unless
   --keep-distressed.
5. Score peer_line_net, the old fair_line_net and widest on one common sample: IC after cost, the cycle test, the
   IC beyond spread level, the Mincer-Zarnowitz slope, each also with a month skipped.
6. Quarterly long-short portfolios (h = 3): formed at each quarter end, held 3 months, no overlap. Plain decile sort
   (top minus bottom tenth) and spread-neutral double sort (5 spread groups x 5 signal groups). Each also formed at t
   and earned from t + 1 (skip a month).
7. Write data/raw/backtest/summary_peer_line_<tag>.json and portfolios_<tag>.parquet; tag = ex_distressed or all.

Run from the repo root (no WRDS access needed; every input is cached):
    PYTHONPATH=. python3 scripts/backtest_peer_line.py                     # distressed bonds out
    PYTHONPATH=. python3 scripts/backtest_peer_line.py --keep-distressed   # every bond, for comparison
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hy import backtest as bt  # noqa: E402
from hy.data.config import CONFIG  # noqa: E402

OUT = CONFIG.path("backtest")
HORIZONS = (3, 6, 12)


def log(msg: str) -> None:
    print(msg, flush=True)


def peer_forecasts(sig: pd.DataFrame, dur: pd.DataFrame, h: int) -> pd.DataFrame:
    """Peer convergence alpha per (date, cusip) with rho from past issuer ESP only."""
    iss = sig.dropna(subset=["esp_sr"]).groupby(["date", "gvkey"])["esp_sr"].median()
    history = {m: iss.xs(m) for m in iss.index.get_level_values(0).unique()}
    rho = {m: bt.peer_rho(history, m) for m in sorted(history)}
    d = sig[["date", "cusip", "g_spread", "esp_sr"]].dropna().merge(dur, on=["date", "cusip"], how="inner")
    r = d["date"].map(lambda m: rho[m][0]).to_numpy(dtype=float)
    d["peer_conv"] = bt.peer_convergence_alpha(d["g_spread"], d["esp_sr"], d["mod_dur"], r, h)  # rho per month
    src = pd.Series({m: v[1] for m, v in rho.items()})
    d.attrs["rho_first_fitted"] = str(src[src == "fitted"].index.min().date()) if (src == "fitted").any() else None
    d.attrs["rho_last"] = float(list(rho.values())[-1][0])
    return d[["date", "cusip", "peer_conv"]]


# Two hedges (decision page 2026-10-23-peer-fair-spread):
#   spread_move: realised_dts = total - Treasury - (s / S) x index leg. The bond's carry cancels against the hedge,
#                so the return is the relative spread move. Forecast: peer convergence less cost.
#   carry_kept:  realised = total - Treasury - 1 x index leg. The bond keeps its carry over the index. Forecast: peer
#                convergence plus carry (s - S) h / 12, less cost; the old fair_line_net was built the same way.
HEDGES = {"spread_move": ("realised_dts", ["widest", "fair_line_net", "peer_line_net"]),
          "carry_kept": ("realised", ["widest", "fair_line_net", "peer_carry_net"])}


def score(df: pd.DataFrame, h: int, preds: list[str], real: str) -> dict:
    lags, net = h - 1, f"{real}_net"
    out = {"n_bond_months": int(len(df)), "n_months": int(df["date"].nunique()), "predictors": {}}
    for p in preds:
        ev = bt.evaluate(df, p, h, real=real, real_net=net)
        out["predictors"][p] = {k: v for k, v in ev.items() if not k.startswith("_")}
    lines = [p for p in preds if p != "widest"]
    out["beyond_spread"] = {p: bt.hac_mean(bt.ic_beyond(df, p, net, "widest"), lags) for p in lines}
    out["beyond_spread_cycles"] = {p: bt.cycle_test(bt.ic_beyond(df, p, net, "widest")) for p in lines}
    # Skip a month: forecast at t, return from t+1. One month-end price sets both the gap and the start of the
    # return, so a noisy price can fake a signal (bid-ask bounce); skipping a month removes that shared noise.
    fc = df[["date", "cusip"] + preds].assign(date=df["date"] + pd.offsets.MonthEnd(1))
    sk = fc.merge(df[["date", "cusip", net]], on=["date", "cusip"], how="inner")
    out["skip_month"] = {
        p: {"ic_net": bt.hac_mean(bt.ic_series(sk, p, net), lags),
            "cycle_test_net": bt.cycle_test(bt.ic_series(sk, p, net)),
            "beyond_spread": bt.hac_mean(bt.ic_beyond(sk, p, net, "widest"), lags) if p != "widest" else None,
            "beyond_spread_cycles": bt.cycle_test(bt.ic_beyond(sk, p, net, "widest")) if p != "widest" else None}
        for p in preds}
    return out


def portfolios(df: pd.DataFrame, preds: list[str], real: str) -> tuple[dict, pd.DataFrame]:
    """Quarterly long-short books on the 3-month horizon, same month and skip a month (see the module steps)."""
    q = bt.quarter_end_dates(df["date"])
    same = df[df["date"].isin(q)]
    fc = df[df["date"].isin(q)][["date", "cusip"] + preds].assign(date=lambda x: x["date"] + pd.offsets.MonthEnd(1))
    skip = fc.merge(df[["date", "cusip", real, "cost_rt", "widest"]].drop(columns=["widest"] if "widest" in preds else []),
                    on=["date", "cusip"], how="inner")
    skip = skip.assign(date=skip["date"] - pd.offsets.MonthEnd(1))   # label by formation date
    stats, series = {}, []
    for timing, d in (("same_month", same), ("skip_month", skip)):
        for p in preds:
            books = {"decile": bt.long_short(d, p, real, "cost_rt", n_bins=10)}
            if p != "widest":
                books["spread_neutral"] = bt.spread_neutral_long_short(d, p, real, "cost_rt", "widest")
            for kind, ls in books.items():
                key = f"{p}|{kind}|{timing}"
                legs = bt.book_legs(d, p, "cusip", control="widest" if kind == "spread_neutral" else None,
                                    n_bins=5 if kind == "spread_neutral" else 10)
                tc = bt.turnover_cost(legs.merge(d[["date", "cusip", "cost_rt"]], on=["date", "cusip"]), "cusip", "cost_rt")
                ls["cost_turnover"] = tc["cost"].reindex(ls.index)
                ls["turnover"] = tc["turnover"].reindex(ls.index)
                ls["net_turnover"] = ls["gross"] - ls["cost_turnover"]
                stats[key] = {"net": bt.portfolio_stats(ls["net"]), "gross": bt.portfolio_stats(ls["gross"]),
                              "net_turnover": bt.portfolio_stats(ls["net_turnover"]),
                              "cost_per_quarter": float(ls["cost"].mean()),
                              "cost_turnover_per_quarter": float(ls["cost_turnover"].mean()),
                              "turnover_mean": float(ls["turnover"].iloc[1:].mean())}
                series.append(ls.reset_index().rename(columns={"index": "date"}).assign(predictor=p, book=kind, timing=timing))
    return stats, pd.concat(series, ignore_index=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep-distressed", action="store_true", help="score bonds at 1,000 bp and wider too")
    ap.add_argument("--cost-bp", type=float, default=None,
                    help="flat round-trip cost in bp of price for every bond; default: the TRACE bid-ask proxy")
    a = ap.parse_args()
    tag = ("all" if a.keep_distressed else "ex_distressed") + (f"_cost{a.cost_bp:g}" if a.cost_bp is not None else "")
    panel = pd.read_parquet(OUT / "panel_full.parquet")
    as_of = pd.to_datetime(panel["available_at"]).max()
    bench = bt.benchmark_spread(panel, as_of)
    dur = panel[["date", "cusip", "mod_dur"]]
    sig = pd.read_parquet(OUT / "peer_signals_full.parquet", columns=["date", "cusip", "gvkey", "g_spread", "esp_sr"])
    summary = {"tag": tag, "hedges": {k: {"realised": v[0], "predictors": v[1]} for k, v in HEDGES.items()},
               "cost": f"flat {a.cost_bp:g} bp of price per round trip" if a.cost_bp is not None
               else "TRACE bid-ask proxy per bond (hy.backtest.round_trip_cost)",
               "distressed": "kept" if a.keep_distressed else f"out: spread >= {bt.DISTRESSED_SPREAD * 1e4:.0f} bp at formation",
               "horizons": {}, "portfolios": {}}
    port_series = []
    for h in HORIZONS:
        f = OUT / f"results_h{h}_full.parquet"
        if not f.exists():
            log(f"h={h}: no cached replay, skipped")
            continue
        res = pd.read_parquet(f)
        need = {"total", "tsy_ret", "bench_ret", "cost_rt"}
        if not need <= set(res.columns):
            log(f"h={h}: cached replay lacks {sorted(need - set(res.columns))}, skipped")
            continue
        if "widest" not in res.columns:  # the 12-month cache holds returns only: spread level from the peer file
            res = res.merge(sig[["date", "cusip", "g_spread"]].assign(widest=sig["g_spread"]), on=["date", "cusip"])
        log(f"h={h}: peer forecasts")
        pf = peer_forecasts(sig, dur, h)
        df = res.merge(pf, on=["date", "cusip"], how="inner")
        if a.cost_bp is not None:  # the user's execution cost; the cached old line had the proxy cost taken off
            if "fair_line_net" in df:
                df["fair_line_net"] = df["fair_line_net"] + df["cost_rt"] - a.cost_bp / 1e4
            df["cost_rt"] = a.cost_bp / 1e4
        S = df["date"].map(bench)
        df["peer_line_net"] = df["peer_conv"] - df["cost_rt"]
        df["peer_carry_net"] = df["peer_conv"] + (df["g_spread"] - S) * h / 12.0 - df["cost_rt"]
        df["realised_dts"] = bt.dts_realised(df["total"], df["tsy_ret"], df["bench_ret"], df["g_spread"], S)
        df["realised_dts_net"] = df["realised_dts"] - df["cost_rt"]
        df["realised_net"] = df["realised"] - df["cost_rt"]
        cols = sorted({p for _, ps in HEDGES.values() for p in ps if p in df.columns})
        df = df.dropna(subset=cols + ["realised", "realised_dts"])
        n_all = len(df)
        if not a.keep_distressed:
            df = df[bt.not_distressed(df)]
        log(f"h={h}: scoring {len(df):,} bond-months ({n_all - len(df):,} distressed out)")
        summary["horizons"][h] = {"n_distressed_out": int(n_all - len(df)), "rho_first_fitted": pf.attrs.get("rho_first_fitted")}
        for hedge, (real, preds) in HEDGES.items():
            preds = [p for p in preds if p in df.columns]
            summary["horizons"][h][hedge] = score(df, h, preds, real)
            if h == 3:
                st, ser = portfolios(df, preds, real)
                summary["portfolios"][hedge] = st
                port_series.append(ser.assign(hedge=hedge))
    (OUT / f"summary_peer_line_{tag}.json").write_text(json.dumps(summary, indent=2, default=str))
    if port_series:
        pd.concat(port_series, ignore_index=True).to_parquet(OUT / f"portfolios_{tag}.parquet", index=False)
    log(f"wrote {OUT / f'summary_peer_line_{tag}.json'}")
    for h, r in summary["horizons"].items():
        for hedge in HEDGES:
            if hedge not in r:
                continue
            x = r[hedge]
            log(f"\nh = {h} months, {hedge}: {x['n_bond_months']:,} bond-months, after cost")
            for p, v in x["predictors"].items():
                ic, cy, sk = v["ic_net"], v["cycle_test_net"], x["skip_month"][p]
                log(f"  {p:14} IC {ic['mean']:+.3f} (t {ic['t']:.1f}) cycles {cy['cycles_positive']}/4 | skip {sk['ic_net']['mean']:+.3f}"
                    f" (t {sk['ic_net']['t']:.1f}) cycles {sk['cycle_test_net']['cycles_positive']}/4 | MZ {v['mz'].get('b', float('nan')):.2f}")
                if p in x["beyond_spread"]:
                    bs, c = sk["beyond_spread"], sk["beyond_spread_cycles"]
                    log(f"  {'':14} beyond spread, skip a month {bs['mean']:+.3f} (t {bs['t']:.1f}) cycles {c['cycles_positive']}/4")
    for hedge, ports in summary["portfolios"].items():
        for key, v in ports.items():
            g, n, nt = v["gross"], v["net"], v["net_turnover"]
            if n.get("n"):
                log(f"  {hedge:11} {key:44} gross {g['ann_mean']:+.2%} (Sh {g['sharpe']:+.2f})  turnover {v['turnover_mean']:.0%}"
                    f"  net(turnover) {nt['ann_mean']:+.2%} (Sh {nt['sharpe']:+.2f}, DD {nt['max_drawdown']:+.0%}, cycles"
                    f" {nt['cycles_positive']}/{nt['cycles_with_data']})  net(full) {n['ann_mean']:+.2%}")

if __name__ == "__main__":
    main()
