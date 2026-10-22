"""Expected alpha per bond: forecast-conditional excess return after hedge, losses, and costs (Sections 7.5, 9.2, 9.4).

The forward layer (Section 5.4) gives, for each macro path m, a probability p(m), a fair spread s_fair(m), and
a default probability. This module turns them into the expected return a hedged long position earns over a
horizon of h years, and splits it into parts so that each part traces to an input.

Per path m, for a bond with spread s, spread duration D, residual persistence rho (quarterly), market beta b,
index spread S, and loss given default LGD:

    carry(m)       = (s - b S) h                        spread earned less the hedge's spread
    converge(m)    = D (1 - rho^(4h)) (s - s_fair(m))   Section 7.5: part of the gap to fair that closes by h
    loss(m)        = PD_h(m) LGD                        expected default loss over h
    alpha(m)       = carry(m) + converge(m) - loss(m)
    alpha          = sum_m p(m) alpha(m) + E[event P&L] - cost

The hedge removes the systematic channel of Section 9.2: rate moves through the effective rate duration and
spread moves through `beta_mkt`. What remains is the issuer's own return. The cost is the round-trip bid-ask.

Intuition: the bond pays its spread; the hedge costs the market's; the mispricing closes at its measured speed;
defaults take their expected share. Alpha is what is left, averaged over the macro stories.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class BondInputs:
    """One bond at the decision time. Spreads and rates in decimals; durations in years."""

    cusip: str
    oas: float
    spread_duration: float
    rho_q: float = 0.85          # quarterly AR(1) persistence of the residual (Section 7.5); 0.85 = 4-quarter half-life
    beta_mkt: float = 1.0        # sensitivity of the bond spread to the index spread (Section 9.3)
    index_spread: float = 0.0    # hedge instrument spread (CDX HY or sector basket)
    lgd: float = 0.6             # loss given default (Section 6, `lgd_k_adj`)
    bid_ask_bp: float = 0.0      # quoted bid-ask in spread bp; round trip costs once (half on entry, half on exit)


def pd_over_horizon(pd_12m: float, h_years: float) -> float:
    """Constant-hazard PD over h years: 1 - (1 - PD12)^h. Intuition: the 12-month PD compounds."""
    return float(1.0 - (1.0 - pd_12m) ** h_years)


def path_alpha(bond: BondInputs, s_fair: float, pd_12m: float, h_years: float) -> dict[str, float]:
    """Alpha parts under one macro path (module formula). Returns decimals of price (per 1 of notional)."""
    carry = (bond.oas - bond.beta_mkt * bond.index_spread) * h_years
    close = 1.0 - bond.rho_q ** (4 * h_years)
    converge = bond.spread_duration * close * (bond.oas - s_fair)
    loss = pd_over_horizon(pd_12m, h_years) * bond.lgd
    return {"carry": carry, "converge": converge, "loss": loss, "alpha": carry + converge - loss}


def expected_alpha(
    bond: BondInputs,
    by_path: pd.DataFrame,
    h_years: float = 0.5,
    event_pnl: float = 0.0,
) -> dict:
    """Probability-weighted alpha over macro paths, net of cost, with its parts and dispersion.

    `by_path` has one row per macro path with columns macro_path, p_path, s_fair, pd_12m (a "weighted" row, if
    present, is ignored and recomputed). Returns a dict with per-path rows, the weighted parts, `alpha_net`,
    `alpha_sd` (dispersion across paths), `info_ratio` = alpha_net / alpha_sd, and `passes_g3` (framework F9 G3:
    alpha after cost above zero).
    """
    rows = by_path[by_path["macro_path"] != "weighted"].copy()
    p = rows["p_path"].to_numpy(dtype=float)
    if not np.isclose(p.sum(), 1.0, atol=1e-6):
        raise ValueError(f"p_path sums to {p.sum()}, not 1")
    parts = pd.DataFrame([path_alpha(bond, s, d, h_years) for s, d in zip(rows["s_fair"], rows["pd_12m"])])
    parts.insert(0, "macro_path", rows["macro_path"].to_numpy())
    parts.insert(1, "p_path", p)
    w = {k: float((parts[k] * p).sum()) for k in ("carry", "converge", "loss", "alpha")}
    cost = bond.bid_ask_bp / 1e4 * bond.spread_duration  # round trip: bid-ask in spread terms times duration
    net = w["alpha"] + event_pnl - cost
    sd = float(np.sqrt((p * (parts["alpha"] - w["alpha"]) ** 2).sum()))
    return {
        "cusip": bond.cusip, "h_years": h_years, "by_path": parts,
        **{f"{k}_w": v for k, v in w.items()}, "event_pnl": event_pnl, "cost": cost,
        "alpha_net": net, "alpha_net_bp_ann": net / h_years * 1e4,
        "alpha_sd": sd, "info_ratio": net / sd if sd > 0 else float("nan"),
        "passes_g3": bool(net > 0),
    }


def alpha_table(bonds: Mapping[str, BondInputs], by_path: Mapping[str, pd.DataFrame], h_years: float = 0.5,
                event_pnl: Mapping[str, float] | None = None) -> pd.DataFrame:
    """One row per bond: weighted parts, net alpha (also annualised bp), dispersion, information ratio, G3 flag."""
    out = []
    for cusip, b in bonds.items():
        r = expected_alpha(b, by_path[cusip], h_years, (event_pnl or {}).get(cusip, 0.0))
        out.append({k: v for k, v in r.items() if k != "by_path"})
    return pd.DataFrame(out).sort_values("alpha_net", ascending=False).reset_index(drop=True)
