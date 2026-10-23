"""Refit the size calibration from whatever backtest outputs exist under the data root (spec S14b; methodology 7.5
size calibration, Section 11; decision page docs/decisions/2026-10-23-size-calibration.md).

Steps:
1. Build the bond-month forecasts and realised returns as `scripts/backtest_peer_line.py` builds them (its
   `peer_forecasts` and `HEDGES`), with a flat round-trip cost (default 15 bp of price) and distressed bonds out
   (spread >= 1,000 bp at formation; `hy.backtest.not_distressed`).
2. For each forecast and horizon: expanding-window, point-in-time fits of three size maps (linear MZ with shrinkage,
   spread-band buckets with partial pooling, isotonic by decile; `hy.calibration`). Each month T is forecast with
   the maps fitted on outcomes finished by decision_time(T).
3. Score each map out of sample: MZ slope of realised on the calibrated forecast (target 1), squared error, rank IC,
   the decile table and the four stress windows. Choose the map by a Diebold-Mariano test against linear.
4. Write every monthly fit of the chosen map to CONFIG.path("calibration", "size_calibration.json"), and the
   scores to size_calibration_eval.json beside it. `hy.groups.size_map` reads the first file.

Run from the repo root (no WRDS access needed; every input is cached):
    HY_DATA_ROOT=/path/to/data/raw PYTHONPATH=. python3 scripts/calibrate_sizes.py
    PYTHONPATH=. python3 scripts/calibrate_sizes.py --cost-bp 15 --horizons 3 6 12
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
sys.path.insert(0, str(ROOT / "scripts"))

from backtest_peer_line import peer_forecasts  # noqa: E402 - reuse, do not duplicate
from hy import backtest as bt  # noqa: E402
from hy import calibration as cb  # noqa: E402
from hy.data.config import CONFIG  # noqa: E402
from hy.data.sources import WarehouseSource  # noqa: E402
from hy.data.view import DataView  # noqa: E402

# forecast -> realised return after cost it is scored against (backtest_peer_line.HEDGES, without "widest", which is
# a spread level and not a return forecast). The carry-kept peer forecast is the one hy.groups sizes with.
TARGETS = {"peer_carry_net": "realised_net", "peer_line_net": "realised_dts_net", "fair_line_net": "realised_net"}
TYPICAL_BP_YR = (-200.0, 0.0, 100.0, 300.0, 600.0, 1000.0)


def log(msg: str) -> None:
    print(msg, flush=True)


def build_frame(h: int, res: pd.DataFrame, sig: pd.DataFrame, dur: pd.DataFrame, bench: pd.Series,
                cost_bp: float, keep_distressed: bool) -> pd.DataFrame:
    """Forecasts and realised returns per bond-month at horizon h, as in backtest_peer_line.main (same columns)."""
    if "widest" not in res.columns:
        res = res.merge(sig[["date", "cusip", "g_spread"]].assign(widest=sig["g_spread"]), on=["date", "cusip"])
    df = res.merge(peer_forecasts(sig, dur, h), on=["date", "cusip"], how="inner")
    if "fair_line_net" in df:
        df["fair_line_net"] = df["fair_line_net"] + df["cost_rt"] - cost_bp / 1e4
    df["cost_rt"] = cost_bp / 1e4
    S = df["date"].map(bench)
    df["peer_line_net"] = df["peer_conv"] - df["cost_rt"]
    df["peer_carry_net"] = df["peer_conv"] + (df["g_spread"] - S) * h / 12.0 - df["cost_rt"]
    df["realised_dts"] = bt.dts_realised(df["total"], df["tsy_ret"], df["bench_ret"], df["g_spread"], S)
    df["realised_dts_net"] = df["realised_dts"] - df["cost_rt"]
    df["realised_net"] = df["realised"] - df["cost_rt"]
    df = df.dropna(subset=["peer_conv", "realised", "realised_dts"])
    return df if keep_distressed else df[bt.not_distressed(df)]


def safe_mz(d: pd.DataFrame, lags: int) -> dict:
    """MZ of y on f; NaN when f does not vary (a map with b = 0 on every date has no cross-sectional slope)."""
    if len(d) < 30 or not np.nanstd(d["f"].to_numpy(dtype=float)) > 1e-12:
        return {"a": np.nan, "b": np.nan, "se_a": np.nan, "se_b": np.nan, "t_b_eq_1": np.nan, "n": int(len(d))}
    return bt.mincer_zarnowitz(d, "f", "y", lags)


def score(oos: pd.DataFrame, col: str, h: int) -> dict:
    """Out-of-sample scores of one forecast column against y (Section 11)."""
    d = oos.dropna(subset=[col]).rename(columns={col: "f"})
    lags = h - 1
    mz = safe_mz(d, lags)
    # cross-sectional MZ: date means out of both, so the slope tests the size gaps between bonds on one date
    mz_xs = safe_mz(cb.demean_by_date(d, ["f", "y"]), lags)
    ic = bt.ic_series(d, "f", "y")
    by = {}
    for k, (a, b) in bt.CYCLE_WINDOWS.items():
        w = d[(d["date"] >= pd.Timestamp(a)) & (d["date"] <= pd.Timestamp(b))]
        m = safe_mz(w, lags)
        mx = safe_mz(cb.demean_by_date(w, ["f", "y"]), lags)
        by[k] = {"mz_b": m["b"], "mz_se_b": m["se_b"], "mz_xs_b": mx["b"], "n": m["n"],
                 "ic": float(bt.ic_series(w, "f", "y").mean()) if len(w) else np.nan,
                 "mean_f": float(w["f"].mean()) if len(w) else np.nan, "mean_y": float(w["y"].mean()) if len(w) else np.nan}
    dec = bt.decile_calibration(d.assign(xr=d["x"]), "xr", "y")       # deciles of the RAW forecast, shared by all maps
    fmean = d.assign(decile=bt.decile_ranks(d, "x")).groupby("decile")["f"].mean()
    dec["calibrated_mean"] = dec["decile"].map(fmean)
    return {"mz": mz, "mz_xs": mz_xs, "mse": float(((d["y"] - d["f"]) ** 2).mean()), "ic": bt.hac_mean(ic, lags),
            "by_window": by, "deciles": dec.round(6).to_dict(orient="list"), "n": int(len(d))}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cost-bp", type=float, default=15.0, help="flat round-trip cost in bp of price (user: 15)")
    ap.add_argument("--keep-distressed", action="store_true")
    ap.add_argument("--horizons", type=int, nargs="+", default=[3, 6, 12])
    ap.add_argument("--min-months", type=int, default=cb.MIN_MONTHS)
    ap.add_argument("--out", type=Path, default=None, help="default: CONFIG.path('calibration', 'size_calibration.json')")
    a = ap.parse_args()
    src = CONFIG.path("backtest")
    out_path = a.out or cb.default_path()
    panel = DataView(WarehouseSource(CONFIG), pd.Timestamp.now()).panel("bond_panel")
    bench = bt.benchmark_spread(panel, pd.to_datetime(panel["available_at"]).max())
    dur = panel[["date", "cusip", "mod_dur"]]
    sig = pd.read_parquet(src / "peer_signals_full.parquet", columns=["date", "cusip", "gvkey", "g_spread", "esp_sr"])
    records: list[cb.Calibration] = []
    evaluation: dict = {}
    for h in a.horizons:
        f = src / f"results_h{h}_full.parquet"
        if not f.exists():
            log(f"h={h}: no cached replay at {f}, skipped")
            continue
        res = pd.read_parquet(f)
        if not {"total", "tsy_ret", "bench_ret", "cost_rt"} <= set(res.columns):
            log(f"h={h}: cached replay lacks the return parts, skipped")
            continue
        df = build_frame(h, res, sig, dur, bench, a.cost_bp, a.keep_distressed)
        data_end = pd.to_datetime(res["end_date"]).max() if "end_date" in res else df["date"].max()
        for pred, real in TARGETS.items():
            if pred not in df:
                continue
            rows = cb.calibration_rows(df, pred, real, h)
            log(f"h={h} {pred}: {len(rows):,} bond-months, {rows['date'].nunique()} months; expanding fits")
            oos, fits = cb.expanding_forecasts(rows, h, pred, methods=cb.METHODS + cb.COMPARATORS,
                                               min_months=a.min_months)
            oos["raw"] = oos["x"]
            oos["v0"] = 0.0 + 0.08 * oos["x"]
            # score only outcomes that ran their full horizon inside the data, on the sample every map covers
            ev = oos[(oos["date"] + pd.offsets.MonthEnd(h) <= data_end)].dropna(subset=list(cb.METHODS))
            chosen, dm = cb.choose_method(ev, h)
            scores = {m: score(ev, m, h) for m in ("raw", "v0", *cb.METHODS, *cb.COMPARATORS)}
            last = {m: fits[m][-1] for m in cb.METHODS + cb.COMPARATORS}
            evaluation[f"{pred}|h{h}"] = {
                "predictor": pred, "realised": real, "horizon_months": h, "chosen": chosen, "dm_vs_linear": dm,
                "oos_start": str(ev["date"].min().date()), "oos_end": str(ev["date"].max().date()),
                "scores": scores, "final_fit": {m: c.to_dict() for m, c in last.items()},
                "typical_bp_yr": {f"{x:g}": cb.size_bp_yr(last[chosen], x) for x in TYPICAL_BP_YR}}
            for c in fits[chosen]:
                c.evaluation = {"chosen": True}
            fits[chosen][-1].evaluation = {"chosen": True, "dm_vs_linear": dm,
                                           "oos_mz_b": scores[chosen]["mz"]["b"], "oos_mz_b_raw": scores["raw"]["mz"]["b"]}
            records += fits[chosen]
            s = scores
            dms = ", ".join(f"{k} {v['t']:+.1f}" for k, v in dm.items() if v.get("t") is not None)
            log(f"  chosen {chosen}; OOS {s['raw']['n']:,} bond-months from {evaluation[f'{pred}|h{h}']['oos_start']};"
                f" DM t vs linear: {dms}")
            for m, v in s.items():
                w = " ".join(f"{k}:{x['mz_b']:+.2f}/{x['mz_xs_b']:+.2f}" for k, x in v["by_window"].items()
                             if x["mz_b"] == x["mz_b"])
                log(f"    {m:9} MZ b {v['mz']['b']:+.3f} (se {v['mz']['se_b']:.3f}) xs {v['mz_xs']['b']:+.3f}"
                    f" | MSE x1e4 {v['mse'] * 1e4:6.2f} | IC {v['ic']['mean']:+.3f} | windows pooled/xs {w}")
            fl = last["linear"]
            log(f"  final linear fit {fl.fit_date}: b_raw {fl.b_raw:+.3f} (se {fl.se_b:.3f}) -> b {fl.b:.3f},"
                f" a {fl.a * 1e4:+.1f} bp, use: {fl.use}")
    meta = {"written": str(pd.Timestamp.now().floor("s")), "data_root": str(CONFIG.root), "cost_bp": a.cost_bp,
            "distressed": "kept" if a.keep_distressed else "out: spread >= 1,000 bp at formation",
            "min_months": a.min_months, "z": cb.Z_SIGNIFICANT, "units": "decimal return over horizon_months, after cost",
            "groups_reads": {"predictor": "peer_carry_net", "horizon_months": 6}}
    cb.save(records, out_path, meta)
    (out_path.parent / "size_calibration_eval.json").write_text(json.dumps(cb._clean({"meta": meta, **evaluation}), indent=1))
    log(f"wrote {out_path} ({len(records)} records) and {out_path.parent / 'size_calibration_eval.json'}")


if __name__ == "__main__":
    main()
