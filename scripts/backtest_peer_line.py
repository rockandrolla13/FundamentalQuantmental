"""Backtest of the peer fair spread with the DTS hedge (methodology 7.2, 7.5, 11; decision page
2026-10-23-peer-fair-spread).

Steps:
1. Read the cached replay (results_h<h>_full.parquet: realised parts, cost, the old fair line and widest), the
   monthly peer signals (peer_signals_full.parquet: ESP per bond against sector x rating x maturity peers) and the
   panel (mod_dur, the HY benchmark spread).
2. Peer forecast per bond-month: D (1 - rho^h) (s - s exp(-ESP_sr)) less the round-trip cost. rho comes from past
   issuer ESP only (`hy.backtest.peer_rho`). With the DTS hedge the carry term is zero.
3. Realised with the DTS hedge: total - tsy - (s / S) x the index leg (`hy.backtest.dts_realised`).
4. Score peer_line_net, the old fair_line_net and widest on one common sample: IC after cost, the cycle test, the
   IC beyond spread level, the Mincer-Zarnowitz slope, and the decile long-short.
5. Write data/raw/backtest/summary_peer_line.json.

Run from the repo root (no WRDS access needed; every input is cached):
    PYTHONPATH=. python3 scripts/backtest_peer_line.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hy import backtest as bt  # noqa: E402

OUT = ROOT / "data" / "raw" / "backtest"
HORIZONS = (3, 6, 12)
PREDICTORS = ["widest", "fair_line_net", "peer_line_net"]


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


def score(df: pd.DataFrame, h: int, preds: list[str]) -> dict:
    lags = h - 1
    out = {"n_bond_months": int(len(df)), "n_months": int(df["date"].nunique()), "predictors": {}}
    for p in preds:
        ev = bt.evaluate(df, p, h, real="realised_dts", real_net="realised_dts_net")
        out["predictors"][p] = {k: v for k, v in ev.items() if not k.startswith("_")}
    lines = [p for p in preds if p != "widest"]
    out["beyond_spread"] = {p: bt.hac_mean(bt.ic_beyond(df, p, "realised_dts_net", "widest"), lags) for p in lines}
    out["beyond_spread_cycles"] = {p: bt.cycle_test(bt.ic_beyond(df, p, "realised_dts_net", "widest")) for p in lines}
    if "fair_line_net" in preds:
        out["old_line_beta1_reference"] = {"ic_net": bt.hac_mean(bt.ic_series(df, "fair_line_net", "realised_net"), lags),
                                           "mz": bt.mincer_zarnowitz(df, "fair_line_net", "realised", lags)}
    return out


def main() -> None:
    panel = pd.read_parquet(OUT / "panel_full.parquet")
    as_of = pd.to_datetime(panel["available_at"]).max()
    bench = bt.benchmark_spread(panel, as_of)
    dur = panel[["date", "cusip", "mod_dur"]]
    sig = pd.read_parquet(OUT / "peer_signals_full.parquet", columns=["date", "cusip", "gvkey", "g_spread", "esp_sr"])
    summary = {"tag": "full", "hedge": "DTS beta s / S on the HY benchmark", "predictors": PREDICTORS, "horizons": {}}
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
        preds = [p for p in PREDICTORS if p in res.columns or p == "peer_line_net"]
        if "widest" not in res.columns:  # the 12-month cache holds returns only: spread level from the peer file
            res = res.merge(sig[["date", "cusip", "g_spread"]].assign(widest=sig["g_spread"]), on=["date", "cusip"])
            preds = ["widest"] + [p for p in preds if p != "widest"]
        log(f"h={h}: peer forecasts")
        pf = peer_forecasts(sig, dur, h)
        df = res.merge(pf, on=["date", "cusip"], how="inner")
        df["peer_line_net"] = df["peer_conv"] - df["cost_rt"]
        S = df["date"].map(bench)
        df["realised_dts"] = bt.dts_realised(df["total"], df["tsy_ret"], df["bench_ret"], df["g_spread"], S)
        df["realised_dts_net"] = df["realised_dts"] - df["cost_rt"]
        df = df.dropna(subset=preds + ["realised", "realised_net", "realised_dts"])
        log(f"h={h}: scoring {len(df):,} bond-months on {preds}")
        summary["horizons"][h] = score(df, h, preds)
        # Skip a month: forecast at t, return from t+1. One month-end price sets both the gap and the start of the
        # return, so a noisy price can fake a signal (bid-ask bounce); skipping a month removes that shared noise.
        fc = df[["date", "cusip"] + preds].assign(date=df["date"] + pd.offsets.MonthEnd(1))
        sk = fc.merge(df[["date", "cusip", "realised_dts_net"]], on=["date", "cusip"], how="inner")
        summary["horizons"][h]["skip_month"] = {
            p: {"ic_net": bt.hac_mean(bt.ic_series(sk, p, "realised_dts_net"), h - 1),
                "beyond_spread": bt.hac_mean(bt.ic_beyond(sk, p, "realised_dts_net", "widest"), h - 1) if p != "widest" else None,
                "beyond_spread_cycles": bt.cycle_test(bt.ic_beyond(sk, p, "realised_dts_net", "widest")) if p != "widest" else None}
            for p in preds}
        summary["horizons"][h]["rho_first_fitted"] = pf.attrs.get("rho_first_fitted")
    (OUT / "summary_peer_line.json").write_text(json.dumps(summary, indent=2, default=str))
    log(f"wrote {OUT / 'summary_peer_line.json'}")
    for h, r in summary["horizons"].items():
        P = r["predictors"]
        log(f"\nh = {h} months, {r['n_bond_months']:,} bond-months, {r['n_months']} months (DTS-hedged realised, after cost)")
        for p in P:
            ic, cy, mz = P[p]["ic_net"], P[p]["cycle_test_net"], P[p]["mz"]
            log(f"  {p:14} IC {ic['mean']:+.3f} (t {ic['t']:.1f})  cycles {cy['cycles_positive']}/{cy['cycles_with_data']}"
                f"  MZ slope {mz.get('b', float('nan')):.2f}")
        for p, v in r["beyond_spread"].items():
            c = r["beyond_spread_cycles"][p]
            log(f"  beyond spread {p:14} IC {v['mean']:+.3f} (t {v['t']:.1f})  cycles {c['cycles_positive']}/{c['cycles_with_data']}")
        for p, v in r["skip_month"].items():
            if v["beyond_spread"]:
                c = v["beyond_spread_cycles"]
                log(f"  skip a month  {p:14} IC {v['ic_net']['mean']:+.3f} (t {v['ic_net']['t']:.1f})  beyond spread "
                    f"{v['beyond_spread']['mean']:+.3f} (t {v['beyond_spread']['t']:.1f})  cycles {c['cycles_positive']}/{c['cycles_with_data']}")


if __name__ == "__main__":
    main()
