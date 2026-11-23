"""Support label against support contents on synthetic issuers (methodology Section 4.7.3).

Claim under test: the market sorts AI-capacity borrowers by one label, "has a big-tech contract", and not by the
terms of the contract. Where the label and the terms disagree, the spread is wrong until a dated event shows the
terms. Five steps:
    1. Score the contents (`hy.clocks.support_frame`).
    2. Ask what the market prices (`hy.clocks.label_test`).
    3. Rank the mis-sort per issuer (`hy.clocks.label_gap`).
    4. Name the next event that can force a reprice (`hy.clocks.next_catalyst`).
    5. Test whether the gap forecasts the 6 months of spread change that start one month later (rank IC, `hy.backtest.ic_series`).

This tests the wiring, not the claim. No issuer is real. The script plants one error of each kind. Market A prices
the label until each issuer's event, then moves to the contents over 6 months. Market B (placebo) prices the
contents from the start. The checks: the planted issuers carry the flags in market A, the gap IC is negative in A,
and in B the label test finds contents pricing and the IC is not significant. 40 issuers is more than the 10 to 20 real
names, so a real run has wider errors.

Run from the repo root: PYTHONPATH=. python3 scripts/support_gap.py
"""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from hy import clocks
from hy.backtest import decision_time, hac_mean, ic_series

N, MONTHS, H, SKIP = 40, 24, 6, 1
START = pd.Timestamp("2026-01-31")
ERR1, ERR2 = "LABEL_WEAK", "NOLABEL_STRONG"
LABEL_PREMIUM, CONTENTS_SLOPE = 0.6, 1.5  # log-spread effects, Our choice


def issuers(seed: int = 0) -> pd.DataFrame:
    """Synthetic support inputs, public on 2025-12-31. Label holders draw more investment-grade revenue."""
    rng = np.random.default_rng(seed)
    label = rng.uniform(size=N) < 0.5
    df = pd.DataFrame({
        "issuer": [f"I{k:02d}" for k in range(N)], "label": label,
        "coverage": rng.uniform(0.3, 1.2, N), "contract_years": rng.uniform(2, 10, N),
        "debt_years": rng.uniform(4, 8, N), "non_cancellable": rng.uniform(0.3, 1.0, N),
        "ig_share": np.where(label, rng.uniform(0.6, 1.0, N), rng.uniform(0.0, 0.5, N)),
        "commenced_share": rng.uniform(0.1, 1.0, N), "reach_share": rng.uniform(0.4, 1.0, N),
        "catalyst_month": rng.integers(3, MONTHS - H, N), "available_at": pd.Timestamp("2025-12-31"),
    })
    plants = {ERR1: dict(label=True, coverage=0.6, contract_years=3.0, debt_years=7.0, non_cancellable=0.2,
                         ig_share=1.0, commenced_share=0.1, reach_share=0.4, catalyst_month=4),
              ERR2: dict(label=False, coverage=1.0, contract_years=8.0, debt_years=5.0, non_cancellable=0.95,
                         ig_share=0.6, commenced_share=1.0, reach_share=1.0, catalyst_month=4)}
    for k, (name, vals) in enumerate(plants.items()):
        df.loc[k, "issuer"] = name
        for c, v in vals.items():
            df.loc[k, c] = v
    return df


def spreads(sup: pd.DataFrame, placebo: bool, seed: int = 0) -> pd.DataFrame:
    """Monthly spreads in bp. Weight on contents: 0 before the catalyst, then a 6-month ramp to 1 (1 in placebo)."""
    rng = np.random.default_rng(seed + 1)
    base = 6.0 + rng.normal(0, 0.15, N)
    lab_px = -LABEL_PREMIUM * sup["label"].astype(float).to_numpy()
    con_px = -CONTENTS_SLOPE * (sup["support_score"].to_numpy() - sup["support_score"].mean()) + lab_px.mean()
    rows = []
    for m in range(MONTHS):
        w = np.ones(N) if placebo else np.clip((m - sup["catalyst_month"].to_numpy()) / H, 0.0, 1.0)
        log_s = base + (1 - w) * lab_px + w * con_px + rng.normal(0, 0.03, N)
        rows.append(pd.DataFrame({"date": START + pd.offsets.MonthEnd(m), "issuer": sup["issuer"],
                                  "spread": np.exp(log_s)}))
    return pd.concat(rows, ignore_index=True)


def run(placebo: bool, seed: int = 0, show: bool = True) -> dict:
    sup = clocks.support_frame(issuers(seed), decision_time(START))                                   # step 1
    panel = spreads(sup, placebo, seed).merge(sup[["issuer", "label", "support_score"]], on="issuer")
    t0 = panel[panel["date"] == START]
    test = clocks.label_test(t0)                                                                      # step 2
    gap0 = clocks.label_gap(t0).set_index("issuer")                                                   # step 3
    flagged = gap0[gap0["label_too_tight"] | gap0["unlabelled_too_wide"]].copy()
    flagged["catalyst"] = [clocks.next_catalyst(                                                     # step 4
        {"terms_filed": START + pd.offsets.MonthEnd(int(sup.set_index("issuer").loc[i, "catalyst_month"]))},
        START)[0] for i in flagged.index]
    # step 5: gap at t against the change in log spread from t + 1 to t + 1 + H. The one-month skip keeps the spread
    # at t out of the target: with it, noise at t alone gives a negative IC (Dickerson et al. 2026, shared price).
    wide = np.log(panel.pivot(index="date", columns="issuer", values="spread"))
    fwd = wide.shift(-(H + SKIP)) - wide.shift(-SKIP)
    gaps = pd.concat([clocks.label_gap(g).assign(date=d) for d, g in panel.groupby("date")])
    gaps = gaps.merge(fwd.stack().rename("fwd").reset_index(), on=["date", "issuer"]).dropna(subset=["fwd"])
    ic = ic_series(gaps, "gap", "fwd", min_n=20)
    ic_stat = hac_mean(ic.dropna(), lags=H - 1)
    if show:
        name = "B (placebo: prices contents)" if placebo else "A (prices label until the event)"
        print(f"\n=== Market {name} ===")
        print("Step 2:", {k: round(v, 3) if isinstance(v, float) else v for k, v in test.items()})
        print("Step 3 and 4, flagged issuers at", START.date())
        cols = ["label", "support_score", "spread", "gap", "label_too_tight", "unlabelled_too_wide", "catalyst"]
        print(flagged[cols].round(3).to_string() if len(flagged) else "  none")
        print(f"Step 5: mean rank IC of gap on {H}-month log spread change {ic_stat['mean']:+.3f} "
              f"(t {ic_stat['t']:+.2f}, {ic.notna().sum()} dates)")
    return {"test": test, "gap0": gap0, "ic": ic_stat}


def main(seed: int = 0) -> None:
    a, b = run(False, seed), run(True, seed)
    checks = {
        "A: market prices the label only": a["test"]["prices_label_only"],
        f"A: {ERR1} flagged label_too_tight": bool(a["gap0"].loc[ERR1, "label_too_tight"]),
        f"A: {ERR2} flagged unlabelled_too_wide": bool(a["gap0"].loc[ERR2, "unlabelled_too_wide"]),
        "A: gap IC negative with t < -2": a["ic"]["mean"] < 0 and a["ic"]["t"] < -2,
        "B: label test finds contents pricing": not b["test"]["prices_label_only"],
        "B: gap IC not significant (|t| < 2)": abs(b["ic"]["t"]) < 2,
    }
    print()
    for k, v in checks.items():
        print(f"{'PASS' if v else 'FAIL'}  {k}")
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--seed", type=int, default=0)
    main(ap.parse_args().seed)
