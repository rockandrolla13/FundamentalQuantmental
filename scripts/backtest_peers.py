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
4. Book versions (Dynkin et al. 2021): ESP with the excess-leverage control (ch. 13) and SPiDER with sustainable
   EBITDA from `peer_data.annual_ebitda` (ch. 14), absolute and against sector x rating peers.
5. Score each like the alpha rules: rank IC after cost at h = 3, 6 and 12 months (Newey-West t), the IC beyond spread
   level, and the four cycle windows. SPiDER also on the book's annual schedule: February month ends only, h = 12.
   The h = 12 realised returns come from `backtest.realised_excess_return` and are cached as results_h12_<tag>. Write data/raw/backtest/peer_signals_<tag>.parquet and a "peers" block in
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
    "esp_lev_sr": "ESP with leverage control (book): sector x rating",
    "esp_lev_r": "ESP with leverage control (book): rating",
    "spider": "SPiDER (book): absolute, sustainable EBITDA",
    "spider_sr": "SPiDER against sector x rating peers",
}
HORIZONS = (3, 6, 12)


def log(msg: str) -> None:
    print(msg, flush=True)


def build_signals(tag: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    panel = pd.read_parquet(OUT / f"panel_{tag}.parquet", columns=["date", "cusip", "years"])
    lev = pd.read_parquet(OUT / f"leverage_{tag}.parquet", columns=["date", "gvkey", "leverage", "ltm_ebitda", "debt"])
    res = pd.read_parquet(OUT / f"results_h6_{tag}.parquet", columns=["date", "cusip", "gvkey", "g_spread"])
    gics = pd.read_parquet(OUT / "gics_history.parquet")
    rat = pd.read_parquet(OUT / "sp_ratings.parquet")
    ann = pd.read_parquet(OUT / "annual_ebitda.parquet")
    lev["gvkey"] = lev["gvkey"].astype(str)
    lev["ebitda_pos"] = (lev["ltm_ebitda"].astype(float) > 0).astype(bool)
    base = res.merge(panel, on=["date", "cusip"], how="left").merge(lev.drop(columns="ltm_ebitda"),
                                                                     on=["date", "gvkey"], how="left")
    hist_x, hist_c, rows, slopes = [], [], [], {}
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
        b["sust_ebitda"] = b["gvkey"].map(peers.sustainable_ebitda(ann, dt))
        out = peers.peer_signals(b)
        slopes[t] = out.attrs["esp_lev_slope"]
        out["spt_all"] = out["log_spt"]
        out["widest"] = out["g_spread"]
        rows.append(out)
        # issuer-months with an actual class and positive leverage feed the next months' cut-offs
        iss = b[b["rclass_actual"].notna() & (b["leverage"] > 0) & b["ebitda_pos"].astype("boolean").fillna(False).astype(bool)].drop_duplicates("gvkey")
        hist_x.extend(np.log(iss["leverage"].astype(float)))
        hist_c.extend(iss["rclass_actual"])
        if t.month == 12:
            log(f"{t.date()} bonds {len(b)}  rated {int((b.rclass_source == 'actual').sum())}  "
                f"implied {int((b.rclass_source == 'implied').sum())}  spider {int(out['spider'].notna().sum())}  "
                f"lev slope sr {slopes[t].get('sr', np.nan):+.2f}  "
                f"cutoffs {cut and {k: round(float(np.exp(v)), 2) for k, v in cut.items()}}")
    sig = pd.concat(rows, ignore_index=True)
    sig.attrs = {}
    return sig, pd.DataFrame(slopes).T


def results_h12(tag: str) -> pd.DataFrame:
    """Realised 12-month hedged excess return per (bond, month), net of the round-trip cost; cached."""
    path = OUT / f"results_h12_{tag}.parquet"
    if path.exists():
        return pd.read_parquet(path)
    panel = pd.read_parquet(OUT / f"panel_{tag}.parquet")
    as_of = pd.to_datetime(panel["available_at"]).max()
    real = bt.realised_excess_return(panel, 12, as_of=as_of)
    cost = panel[["date", "cusip"]].assign(cost_rt=bt.round_trip_cost(panel))
    df = real.merge(cost, on=["date", "cusip"])
    df["realised_net"] = df["realised"] - df["cost_rt"]
    df = df[df["realised"].notna()]
    df.to_parquet(path, index=False)
    return df


def score(sig: pd.DataFrame, tag: str) -> dict:
    cols = list(SIGNALS)
    out = {}
    for h in HORIZONS:
        res = (results_h12(tag) if h == 12 else pd.read_parquet(OUT / f"results_h{h}_{tag}.parquet"))[
            ["date", "cusip", "realised", "realised_net", "cost_rt"]]
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
    out["annual_feb"] = annual_spider(df)
    return out


def annual_spider(df: pd.DataFrame) -> dict:
    """The book's schedule: form at each February month end, hold 12 months; df holds the h = 12 rows."""
    feb = df[df["date"].dt.month == 2]
    out = {}
    for c in ("widest", "spider", "spider_sr", "esp_lev_sr", "esp_sr"):
        d = feb.dropna(subset=[c])
        ic = bt.ic_series(d, c, "realised_net")
        beyond = bt.ic_beyond(d, c, "realised_net", "widest") if c != "widest" else None
        out[c] = {"years": int(ic.notna().sum()), "ic_net": bt.hac_mean(ic, 0),
                  "beyond_spread": bt.hac_mean(beyond, 0) if beyond is not None else None,
                  "cycles": bt.cycle_test(ic), "ic_by_year": {str(k.year): float(v) for k, v in ic.items()}}
        b = f"  beyond {out[c]['beyond_spread']['mean']:+.3f} (t {out[c]['beyond_spread']['t']:+.1f})" if beyond is not None else ""
        log(f"annual Feb h12 {c:10s} IC net {out[c]['ic_net']['mean']:+.3f} (t {out[c]['ic_net']['t']:+.1f}){b}  "
            f"years {out[c]['years']}")
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
    sig, sl = build_signals(a.tag)
    sig.to_parquet(OUT / f"peer_signals_{a.tag}.parquet")
    agree = class_agreement(sig)
    log(f"implied vs actual class: exact {agree['exact']:.2f} on {agree['n']} issuer-months")
    cells = {k: sig[f"cell_{k}"].value_counts(normalize=True).round(3).to_dict() for k in ("esp_sr", "e13_sr", "spider_sr")}
    log(f"ESP leverage slope (median over months): {sl.median().round(3).to_dict()}; share positive "
        f"{(sl > 0).mean().round(2).to_dict()}")
    cover = {"spider_rows": float(sig["spider"].notna().mean()), "spider_issuer_months":
             int(sig.dropna(subset=["spider"]).drop_duplicates(["date", "gvkey"]).shape[0])}
    log(f"SPiDER coverage: {cover}")
    log(f"cell used (share of rows): {cells}")
    res = score(sig, a.tag)
    path = OUT / f"summary_{a.tag}.json"
    summ = json.loads(path.read_text()) if path.exists() else {}
    summ["peers"] = {"class_agreement": agree, "cells_used": cells, "spider_coverage": cover,
                     "esp_lev_slope_median": sl.median().to_dict(),
                     "results": {str(h): r for h, r in res.items()}}
    path.write_text(json.dumps(summ, indent=1, default=float))


if __name__ == "__main__":
    main()
