"""Backtest of ESP and of spread per turn against peers (E13 by sector, by rating, and by both). Methodology 7.2, 11;
decision page docs/decisions/2026-10-22-esp-peer-groups.md.

Run after `scripts/backtest_alpha.py --tag full` and after the peer data pull (`hy/sources/peer_data.py`):
    PYTHONPATH=. python3 scripts/backtest_peers.py --tag full

Steps:
1. At each month end t, take the scored bonds of the alpha backtest, their maturity, the issuer's leverage at t,
   the GICS sector in force at t, and the S&P rating class known at t + 1 day.
2. Where no rating is on file, use the class implied by leverage, with cut-offs fitted on the actual ratings of the
   months before t only.
3. Form ESP and E13 against peers in three cells: sector x rating, sector only, rating only (each x maturity bucket).
   Also the run-wide spread per turn (E13 as built) and "buy the widest".
4. Score each like the alpha rules: rank IC after cost at h = 3 and 6 months (Newey-West t), the IC beyond spread
   level, and the four cycle windows. Write data/raw/backtest/peer_signals_<tag>.parquet and a "peers" block in
   summary_<tag>.json.
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
from hy import peers  # noqa: E402

OUT = ROOT / "data" / "raw" / "backtest"
SIGNALS = {
    "widest": "Buy the widest (spread level)",
    "spt_all": "E13 as built: spread per turn, all issuers",
    "esp_sr": "ESP: sector x rating",
    "esp_s": "ESP: sector",
    "esp_r": "ESP: rating",
    "e13_sr": "E13 against peers: sector x rating",
    "e13_s": "E13 against peers: sector",
    "e13_r": "E13 against peers: rating",
}


def log(msg: str) -> None:
    print(msg, flush=True)


def build_signals(tag: str) -> pd.DataFrame:
    panel = pd.read_parquet(OUT / f"panel_{tag}.parquet", columns=["date", "cusip", "years"])
    lev = pd.read_parquet(OUT / f"leverage_{tag}.parquet", columns=["date", "gvkey", "leverage", "ltm_ebitda"])
    res = pd.read_parquet(OUT / f"results_h6_{tag}.parquet", columns=["date", "cusip", "gvkey", "g_spread"])
    gics = pd.read_parquet(OUT / "gics_history.parquet")
    rat = pd.read_parquet(OUT / "sp_ratings.parquet")
    lev["gvkey"] = lev["gvkey"].astype(str)
    lev["ebitda_pos"] = (lev["ltm_ebitda"].astype(float) > 0).astype(bool)
    base = res.merge(panel, on=["date", "cusip"], how="left").merge(lev.drop(columns="ltm_ebitda"),
                                                                     on=["date", "gvkey"], how="left")
    hist_x, hist_c, rows = [], [], []
    for t, b in base.groupby("date"):
        dt = bt.decision_time(t)
        sec = peers.sector_at(gics, t)
        act = peers.rating_at(rat, dt)
        cut = peers.fit_cutoffs(hist_x, hist_c)
        b = b.copy()
        b["sector"] = b["gvkey"].map(sec)
        b["rclass_actual"] = b["gvkey"].map(act)
        b["rclass_implied"] = [peers.implied_class(lv, bool(ep) if ep == ep else False, cut)
                               for lv, ep in zip(b["leverage"], b["ebitda_pos"])]
        b["rclass"] = b["rclass_actual"].fillna(b["rclass_implied"])
        b["rclass_source"] = np.where(b["rclass_actual"].notna(), "actual",
                                      np.where(b["rclass_implied"].notna(), "implied", "none"))
        b["spread"] = b["g_spread"]
        out = peers.peer_signals(b)
        out["spt_all"] = out["log_spt"]
        out["widest"] = out["g_spread"]
        rows.append(out)
        # issuer-months with an actual class and positive leverage feed the next months' cut-offs
        iss = b[b["rclass_actual"].notna() & (b["leverage"] > 0) & b["ebitda_pos"].astype("boolean").fillna(False).astype(bool)].drop_duplicates("gvkey")
        hist_x.extend(np.log(iss["leverage"].astype(float)))
        hist_c.extend(iss["rclass_actual"])
        if t.month == 12:
            log(f"{t.date()} bonds {len(b)}  rated {int((b.rclass_source == 'actual').sum())}  "
                f"implied {int((b.rclass_source == 'implied').sum())}  cutoffs {cut and {k: round(float(np.exp(v)), 2) for k, v in cut.items()}}")
    return pd.concat(rows, ignore_index=True)


def score(sig: pd.DataFrame, tag: str) -> dict:
    cols = list(SIGNALS)
    out = {}
    for h in (3, 6):
        res = pd.read_parquet(OUT / f"results_h{h}_{tag}.parquet",
                              columns=["date", "cusip", "realised", "realised_net", "cost_rt"])
        df = res.merge(sig[["date", "cusip"] + [c for c in cols if c != "widest"] + ["widest"]], on=["date", "cusip"])
        out[h] = {}
        for c in cols:
            d = df.dropna(subset=[c])
            ev = bt.evaluate(d, c, h)
            beyond = bt.hac_mean(bt.ic_beyond(d, c, "realised_net", "widest"), h - 1) if c != "widest" else None
            out[h][c] = {"label": SIGNALS[c], "n_obs": int(len(d)), "ic_net": ev["ic_net"], "beyond_spread": beyond,
                         "cycles": ev["cycle_test_net"], "mz_slope": ev["mz"].get("b") if isinstance(ev["mz"], dict) else None}
            b = f"  beyond {beyond['mean']:+.3f} (t {beyond['t']:+.1f})" if beyond else ""
            log(f"h{h} {c:8s} IC net {ev['ic_net']['mean']:+.3f} (t {ev['ic_net']['t']:+.1f}){b}  "
                f"cycles+ {ev['cycle_test_net']['cycles_positive']}/{ev['cycle_test_net']['cycles_with_data']}")
    return out


def class_agreement(sig: pd.DataFrame) -> dict:
    """How often the implied class matches the actual class, on issuer-months that have both (2008 to 2017)."""
    d = sig.dropna(subset=["rclass_actual", "rclass_implied"]).drop_duplicates(["date", "gvkey"])
    tab = pd.crosstab(d["rclass_actual"], d["rclass_implied"])
    return {"n": int(len(d)), "exact": float((d["rclass_actual"] == d["rclass_implied"]).mean()),
            "table": {r: {c: int(tab.loc[r, c]) for c in tab.columns} for r in tab.index}}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="full")
    a = ap.parse_args()
    sig = build_signals(a.tag)
    sig.to_parquet(OUT / f"peer_signals_{a.tag}.parquet")
    agree = class_agreement(sig)
    log(f"implied vs actual class: exact {agree['exact']:.2f} on {agree['n']} issuer-months")
    cells = {k: sig[f"cell_{k}"].value_counts(normalize=True).round(3).to_dict() for k in ("esp_sr", "e13_sr")}
    log(f"cell used (share of rows): {cells}")
    res = score(sig, a.tag)
    path = OUT / f"summary_{a.tag}.json"
    summ = json.loads(path.read_text()) if path.exists() else {}
    summ["peers"] = {"class_agreement": agree, "cells_used": cells,
                     "results": {str(h): {k: {kk: vv for kk, vv in v.items()} for k, v in r.items()} for h, r in res.items()}}
    path.write_text(json.dumps(summ, indent=1, default=float))


if __name__ == "__main__":
    main()
