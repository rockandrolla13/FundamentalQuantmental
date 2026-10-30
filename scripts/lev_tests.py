"""Tests L1 and L2 of the decision page: debt to revenue and negative book equity as failure predictors.

Decision page: docs/decisions/2026-10-30-revenue-leverage-and-negative-equity.md. Methodology 4.3 (capital structure).
Neither feature enters `hy/` unless its test passes here.

Run (WRDS may ask for a login, so run this in a terminal):
    PYTHONPATH=. python3 scripts/lev_tests.py                  # writes data/raw/backtest/lev_tests.json
    PYTHONPATH=. python3 scripts/lev_tests.py --input f.parquet   # a saved pull; WRDS stays closed

Unit of observation: one US non-financial, non-utility firm in one fiscal year, from comp.funda. Universe: debt at or
above MIN_DEBT_USD_M, with EBITDA <= 0 or debt / EBITDA > HL_LEVERAGE.

Decision time: datadate + AVAIL_LAG_DAYS, because comp.funda is the current view, not point in time.

Event: Compustat deletion for bankruptcy or liquidation (dlrsn 02, 03) within EVENT_MONTHS after the decision time. A
firm deleted before the decision time leaves the sample. A row's outcome counts as known at the end of its window.

Windows: hy.backtest.CYCLE_WINDOWS. For a window that starts on day a, the model trains on rows whose outcome was
known before a, and it scores rows with a decision time inside the window.

L1 (debt to revenue): rows with EBITDA <= 0, where leverage ties at the cap. Base: size. Full: size, log debt / revenue.
L2 (negative book equity): all rows. Base: capped log leverage, size. Full: base and the flag ceq < 0.

Pass rule, fixed before the first run: the firm-block bootstrap 95% interval of the pooled out-of-sample AUC gain lies
above zero, and at least 3 of the 4 windows show a positive gain with a positive coefficient.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from hy.backtest import CYCLE_WINDOWS
from hy.data.config import CONFIG
from hy.state import LEV_CAP

MIN_DEBT_USD_M = 150.0    # proxy for a bond issuer; a firm below this rarely issues in the HY market (our choice)
HL_LEVERAGE = 4.0         # the HY-like cut of scripts/wt_tests.py and scripts/s_tests.py
AVAIL_LAG_DAYS = 90       # the slowest 10-K deadline
EVENT_MONTHS = 36         # the deletion date lags the filing, so the window is long (our choice)
EVENT_CODES = ("02", "03")
EXCLUDED_SECTORS = ("40", "55")
FIRST_YEAR, LAST_YEAR = 1994, 2022
MIN_TEST_EVENTS = 5       # a window with fewer events gives no reading and counts as not passed (our choice)
MIN_WINDOWS = 3           # of the 4 cycles (CLAUDE.md, definition of done)
N_BOOT = 1000
TESTS = {"L1_debt_to_revenue": {"mask": "neg_ebitda", "base": ["size"], "extra": "log_d_rev"},
         "L2_negative_book_equity": {"mask": None, "base": ["log_lev", "size"], "extra": "neg_book"}}
SQL = f"""SELECT f.gvkey, f.datadate, f.fyear, f.sale, f.oibdp, f.dltt, f.dlc, f.ceq, f.at,
                 c.dlrsn, c.dldte, c.gsector
FROM comp.funda f JOIN comp.company c ON f.gvkey = c.gvkey
WHERE f.indfmt = 'INDL' AND f.datafmt = 'STD' AND f.popsrc = 'D' AND f.consol = 'C' AND f.curcd = 'USD'
  AND f.fyear BETWEEN {FIRST_YEAR} AND {LAST_YEAR} AND c.loc = 'USA'"""


def _code(x: pd.Series) -> pd.Series:
    """Compustat codes as clean strings: 2.0, '2' and '02' give one value after zfill by the caller."""
    return x.astype("string").str.replace(r"\.0$", "", regex=True)


def build_rows(raw: pd.DataFrame) -> pd.DataFrame:
    """The sample with features and event (methodology 4.3): d = dltt + dlc; log_lev = log(clip(d / EBITDA, 0.1, cap)),
    with EBITDA <= 0 read as the cap; log_d_rev = log(clip(d / sale, 0.01, 50)); neg_book = ceq < 0; size = log at.
    Intuition: debt / revenue still ranks firms when earnings are negative and leverage says only "at the cap"."""
    df = raw.copy()
    df["datadate"], df["dldte"] = pd.to_datetime(df["datadate"]), pd.to_datetime(df["dldte"])
    df["debt"] = df["dltt"].fillna(0.0) + df["dlc"].fillna(0.0)
    keep = (df["debt"] >= MIN_DEBT_USD_M) & (df["sale"] > 0) & (df["at"] > 0) & df["oibdp"].notna() & df["ceq"].notna()
    df = df[keep & ~_code(df["gsector"]).isin(EXCLUDED_SECTORS).fillna(False)].copy()
    df["neg_ebitda"] = df["oibdp"] <= 0
    lev = (df["debt"] / df["oibdp"].where(~df["neg_ebitda"])).fillna(LEV_CAP)
    df = df[df["neg_ebitda"] | (lev > HL_LEVERAGE)].copy()
    df["lev"] = lev.reindex(df.index).clip(upper=LEV_CAP)
    df["available_at"] = df["datadate"] + pd.Timedelta(days=AVAIL_LAG_DAYS)
    df["outcome_available_at"] = df["available_at"] + pd.DateOffset(months=EVENT_MONTHS)
    df = df[~(df["dldte"] <= df["available_at"])].copy()   # gone before the decision time
    failed = _code(df["dlrsn"]).str.zfill(2).isin(EVENT_CODES).fillna(False)
    df["y"] = (failed & (df["dldte"] <= df["outcome_available_at"])).astype(int)
    df["log_lev"] = np.log(df["lev"].clip(lower=0.1))
    df["log_d_rev"] = np.log((df["debt"] / df["sale"]).clip(0.01, 50.0))
    df["neg_book"] = (df["ceq"] < 0).astype(float)
    df["size"] = np.log(df["at"])
    return df.reset_index(drop=True)


def window_split(rows: pd.DataFrame, a: str, b: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Train on rows whose outcome was known before a; score rows with a decision time in [a, b]. No look-ahead."""
    a_, b_ = pd.Timestamp(a), pd.Timestamp(b)
    return (rows[rows["outcome_available_at"] < a_],
            rows[(rows["available_at"] >= a_) & (rows["available_at"] <= b_)])


def _fit(train: pd.DataFrame, test: pd.DataFrame, cols: list[str]) -> tuple[np.ndarray, np.ndarray]:
    """A logistic fit on train: the test probabilities and the coefficients. C = 1e6 is close to no penalty."""
    m = LogisticRegression(C=1e6, max_iter=2000).fit(train[cols], train["y"])
    return m.predict_proba(test[cols])[:, 1], m.coef_[0]


def run_test(rows: pd.DataFrame, spec: dict, n_boot: int = N_BOOT, seed: int = 7) -> dict:
    """One test over the cycle windows: AUC gain per window, the pooled gain, its interval, and the pass rule."""
    sample = rows[rows[spec["mask"]]] if spec["mask"] else rows
    full = [*spec["base"], spec["extra"]]
    windows, stack = {}, []
    for w, (a, b) in CYCLE_WINDOWS.items():
        train, test = window_split(sample, a, b)
        res = {"n": len(test), "events": int(test["y"].sum()), "train_events": int(train["y"].sum()), "gain": None,
               "coef": None, "passed": False}
        if res["events"] >= MIN_TEST_EVENTS and res["events"] < res["n"] and train["y"].nunique() == 2:
            p0, _ = _fit(train, test, spec["base"])
            p1, coef = _fit(train, test, full)
            res["gain"] = float(roc_auc_score(test["y"], p1) - roc_auc_score(test["y"], p0))
            res["coef"] = float(coef[-1])
            res["passed"] = res["gain"] > 0 and res["coef"] > 0
            stack.append(pd.DataFrame({"gvkey": test["gvkey"].to_numpy(), "y": test["y"].to_numpy(), "p0": p0, "p1": p1}))
        windows[w] = res
    out = {"windows": windows, "windows_passed": sum(r["passed"] for r in windows.values()), "pooled_gain": None,
           "ci95": None, "passed": False}
    if not stack:
        return out
    oos = pd.concat(stack, ignore_index=True)
    out["pooled_gain"] = float(roc_auc_score(oos["y"], oos["p1"]) - roc_auc_score(oos["y"], oos["p0"]))
    groups = list(oos.groupby("gvkey").indices.values())
    y, p0, p1 = oos["y"].to_numpy(), oos["p0"].to_numpy(), oos["p1"].to_numpy()
    rng = np.random.default_rng(seed)
    gains = []
    for _ in range(n_boot):
        s = np.concatenate([groups[i] for i in rng.integers(0, len(groups), len(groups))])
        if 0 < y[s].sum() < len(s):
            gains.append(roc_auc_score(y[s], p1[s]) - roc_auc_score(y[s], p0[s]))
    lo, hi = np.percentile(gains, [2.5, 97.5])
    out["ci95"] = [float(lo), float(hi)]
    out["passed"] = bool(lo > 0 and out["windows_passed"] >= MIN_WINDOWS)
    return out


def describe(rows: pd.DataFrame) -> dict:
    """Counts and failure rates that say how much each idea could matter, before any fit."""
    ne = rows[rows["neg_ebitda"]]
    terc = pd.qcut(ne["log_d_rev"], 3, labels=["low", "mid", "high"], duplicates="drop")
    pe = rows[~rows["neg_ebitda"]]
    bins = pd.cut(pe["lev"], [HL_LEVERAGE, 6.0, 8.0, LEV_CAP], labels=["4-6x", "6-8x", "8x+"])
    tab = lambda g: {str(k): {"n": len(v), "events": int(v["y"].sum()), "rate": float(v["y"].mean())} for k, v in g}  # noqa: E731
    return {"rows": len(rows), "firms": int(rows["gvkey"].nunique()), "events": int(rows["y"].sum()),
            "neg_ebitda_share": float(rows["neg_ebitda"].mean()), "neg_book_share": float(rows["neg_book"].mean()),
            "neg_ebitda_by_debt_to_revenue": tab(ne.groupby(terc, observed=True)),
            "pos_ebitda_by_leverage_and_book": tab(pe.groupby([bins, "neg_book"], observed=True))}


def load_raw(input_path: str | None) -> pd.DataFrame:
    """The Compustat pull from a saved file, else from WRDS, saved once under the data root (vendor data, not in git)."""
    if input_path:
        return pd.read_parquet(input_path)
    cache = CONFIG.path("backtest", "lev_tests_funda.parquet")
    if cache.exists():
        return pd.read_parquet(cache)
    raw = CONFIG.connect().raw_sql(SQL, date_cols=["datadate", "dldte"])
    cache.parent.mkdir(parents=True, exist_ok=True)
    raw.to_parquet(cache)
    return raw


def main(argv: Sequence[str] | None = None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--input", default=None, help="a saved parquet of the pull; WRDS stays closed")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    rows = build_rows(load_raw(args.input))
    result = {"describe": describe(rows), "tests": {k: run_test(rows, spec) for k, spec in TESTS.items()}}
    out = Path(args.out) if args.out else CONFIG.path("backtest", "lev_tests.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1, default=str))
    for k, r in result["tests"].items():
        print(f"{k}: {'PASS' if r['passed'] else 'FAIL'}; pooled AUC gain {r['pooled_gain']}, 95% interval {r['ci95']}, "
              f"windows passed {r['windows_passed']} of {len(CYCLE_WINDOWS)}")
    print(f"wrote {out}")
    return result


if __name__ == "__main__":
    main()
