"""Backtest of equity momentum in credit (EMC) and OneScore (Dynkin et al. 2021, ch. 15, 18, 19). Methodology 7.4, 11;
decision page docs/decisions/2026-10-22-onescore.md.

Run after `scripts/backtest_peers.py --tag full` and the equity pull (`peer_data.equity_monthly`):
    PYTHONPATH=. python3 scripts/backtest_onescore.py --tag full

Steps:
1. Read the monthly peer signals (ESP per bond, GICS sector at t) from peer_signals_<tag>.parquet.
2. At each month end t, EMC = the issuer's stock total return over the 3 months to t, known at t + 1 day.
3. OneScore = mean of the within-sector percentile ranks of issuer ESP and EMC (`peers.onescore`).
4. Score each at h = 3, 6 and 12 months: rank IC after cost (Newey-West t), the IC beyond spread level, and both by
   cycle window. The beyond-spread cycle test is the bar ESP failed. Also the ESP-EMC correlation by cycle window.
   Write onescore_signals_<tag>.parquet and a "onescore" block in summary_<tag>.json.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from hy import backtest as bt  # noqa: E402
from hy import peers  # noqa: E402
from backtest_peers import results_h12  # noqa: E402
from hy.data.config import CONFIG  # noqa: E402

OUT = CONFIG.path("backtest")
SIGNALS = {
    "widest": "Buy the widest (spread level)",
    "esp_sr": "ESP, sector x rating (bond level)",
    "esp_sec": "ESP, issuer rank within sector",
    "emc": "EMC: 3-month stock return",
    "emc_sec": "EMC, rank within sector",
    "onescore": "OneScore: ESP and EMC ranks, equal weights",
}


def log(msg: str) -> None:
    print(msg, flush=True)


def build(tag: str) -> pd.DataFrame:
    sig = pd.read_parquet(OUT / f"peer_signals_{tag}.parquet", columns=["date", "cusip", "gvkey", "sector", "esp_sr", "widest"])
    eq = pd.read_parquet(OUT / "equity_monthly.parquet")
    rows = []
    for t, b in sig.groupby("date"):
        emc = peers.equity_momentum(eq, t, bt.decision_time(t))
        out = peers.onescore(b.dropna(subset=["esp_sr"]), emc)
        rows.append(out)
        if t.month == 12:
            log(f"{t.date()} bonds {len(out)}  with EMC {int(out['emc'].notna().sum())}  "
                f"OneScore {int(out['onescore'].notna().sum())}")
    return pd.concat(rows, ignore_index=True)


def score(sig: pd.DataFrame, tag: str) -> dict:
    out = {}
    for h in (3, 6, 12):
        res = (results_h12(tag) if h == 12 else pd.read_parquet(OUT / f"results_h{h}_{tag}.parquet"))[
            ["date", "cusip", "realised", "realised_net", "cost_rt"]]
        df = res.merge(sig[["date", "cusip"] + list(SIGNALS)], on=["date", "cusip"])
        df = df.dropna(subset=["onescore"])          # one common sample: bonds of listed issuers with both parts
        out[h] = {"n_obs": int(len(df))}
        for c in SIGNALS:
            ev = bt.evaluate(df, c, h)
            r = {"label": SIGNALS[c], "ic_net": ev["ic_net"], "cycles": ev["cycle_test_net"]}
            line = f"h{h} {c:9s} IC net {ev['ic_net']['mean']:+.3f} (t {ev['ic_net']['t']:+.1f})"
            if c != "widest":
                b = bt.ic_beyond(df, c, "realised_net", "widest")
                r["beyond_spread"] = bt.hac_mean(b, h - 1)
                r["beyond_cycles"] = bt.cycle_test(b)
                bc = r["beyond_cycles"]["by_cycle"]
                line += (f"  beyond {r['beyond_spread']['mean']:+.3f} (t {r['beyond_spread']['t']:+.1f})  beyond by cycle "
                         + " ".join(f"{k} {v:+.2f}" for k, v in bc.items())
                         + f"  ({r['beyond_cycles']['cycles_positive']}/{r['beyond_cycles']['cycles_with_data']})")
            out[h][c] = r
            log(line)
    return out


def esp_emc_correlation(sig: pd.DataFrame) -> dict:
    """Rank correlation of issuer ESP and EMC within each month, averaged by cycle window and overall."""
    iss = sig.dropna(subset=["esp_sec", "emc_sec"]).drop_duplicates(["date", "gvkey"])
    c = iss.groupby("date").apply(lambda g: g["esp_sec"].corr(g["emc_sec"], method="spearman"))
    return {"all": float(c.mean()), "by_cycle": {str(k): float(v) for k, v in bt.ic_by_window(c).items()}}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="full")
    a = ap.parse_args()
    sig = build(a.tag)
    sig.to_parquet(OUT / f"onescore_signals_{a.tag}.parquet")
    corr = esp_emc_correlation(sig)
    log(f"ESP-EMC rank correlation: {corr['all']:+.3f}; by cycle {({k: round(v, 3) for k, v in corr['by_cycle'].items()})}")
    res = score(sig, a.tag)
    path = OUT / f"summary_{a.tag}.json"
    summ = json.loads(path.read_text()) if path.exists() else {}
    summ["onescore"] = {"esp_emc_corr": corr, "results": {str(h): r for h, r in res.items()}}
    path.write_text(json.dumps(summ, indent=1, default=float))


if __name__ == "__main__":
    main()
