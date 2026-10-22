"""Relative value between issuers: spread per unit of risk (methodology Sections 7.1, 7.4, 8 S4, 4.7).

The book compares each bond with its peers and its own capital structure by spread per turn of leverage
(HCA memo, pp. 412-413). This module does the same across two or more issuers, and adds three yardsticks:
the expected-loss anchor of Section 7.1, the high yield market at the same maturity, and the duration
mismatch of Section 4.7 (does the bond mature inside the signed contract book?).

Conventions: spreads and yields in decimals unless a name ends in `_bp`; maturities in years from the
pricing date; amounts in USD millions.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from hy import clocks

# Long-run anchors. Book: speculative grade one-year default rate 3.60%, 1981-2021 (Figure 9.19, p. 274).
SPEC_GRADE_PD_1Y = 0.036
# Assumption: senior unsecured loss given default 60% (recovery 40%); replace with Section 6 recovery when built.
SENIOR_UNSECURED_LGD = 0.60


def modified_duration(ytm: float, coupon: float, maturity: float, freq: int = 2) -> float:
    """Modified duration of a fixed-coupon bullet bond priced at its yield (no call option).

    Intuition: price change per unit of yield change; used as spread duration for the convergence return.
    """
    if maturity <= 0:
        return 0.0
    n = max(1, int(np.ceil(maturity * freq)))
    t = maturity - (n - np.arange(1, n + 1)) / freq  # cash-flow times, last at maturity
    y = ytm / freq
    cf = np.full(n, coupon / freq * 100.0)
    cf[-1] += 100.0
    disc = (1 + y) ** (-t * freq)
    price = (cf * disc).sum()
    mac = (t * cf * disc).sum() / price
    return float(mac / (1 + y))


def hazard(pd_1y: float) -> float:
    """Section 7.1: lambda = -log(1 - PD12)."""
    return float(-np.log(1.0 - pd_1y))


def el_spread(pd_1y: float, lgd: float) -> float:
    """Section 7.1: s_EL = lambda x LGD. Intuition: the spread that only pays for expected default losses."""
    return hazard(pd_1y) * lgd


def kappa(spread: float, pd_1y: float, lgd: float) -> float:
    """Section 7.1: spread over expected-loss spread. Intuition: how many times its expected loss a bond pays.

    For the market, use the benchmark spread with the speculative-grade PD; for a bond, its own spread and PD.
    """
    s_el = el_spread(pd_1y, lgd)
    return float(spread / s_el) if s_el > 0 else float("nan")


def lease_adjusted_leverage(debt: float, rent: float, ebitda: float, multiple: float = 8.0) -> float:
    """Section 4.3: (debt + 8 x rent) / (EBITDA + rent), pp. 267-268. Intuition: rent is debt service by another name."""
    den = ebitda + rent
    return float((debt + multiple * rent) / den) if den > 0 else float("nan")


def cover_to_maturity(res: clocks.ClockResult, maturity: float) -> float:
    """Section 4.7 at bond level: contract cash over fixed charges, both cumulative to the bond's maturity.

    At or above 1, the signed contracts pay every fixed charge that falls due before the bond is repaid.
    Intuition: a bond repaid inside the contract book does not depend on renewal; one repaid after it does.
    """
    t = np.arange(len(res.revenue))
    w = np.clip(maturity - t, 0.0, 1.0)  # share of each year before maturity
    cash = (res.revenue * res.cash_margin * w).sum()
    owed = (res.obligations_total * w).sum()
    return float(cash / owed) if owed > 0 else float("nan")


def curve_fit(maturities: Sequence[float], spreads: Sequence[float]) -> tuple[float, float]:
    """Issuer spread curve s = a + b x T by least squares; a flat curve when there is one bond or one maturity."""
    m = np.asarray(maturities, dtype=float)
    s = np.asarray(spreads, dtype=float)
    ok = ~(np.isnan(m) | np.isnan(s))
    m, s = m[ok], s[ok]
    if len(m) == 0:
        return float("nan"), 0.0
    if len(m) == 1 or np.ptp(m) < 0.25:
        return float(s.mean()), 0.0
    b, a = np.polyfit(m, s, 1)
    return float(a), float(b)


def curve_at(fit: tuple[float, float], tenor: float) -> float:
    return fit[0] + fit[1] * tenor


def common_tenors(mats_a: Sequence[float], mats_b: Sequence[float], step: float = 1.0) -> list[float]:
    """Whole-year tenors inside both issuers' maturity ranges; else the midpoint of the gap between them.

    Intuition: compare spreads where both curves have bonds, not by extrapolation.
    """
    lo = max(min(mats_a), min(mats_b))
    hi = min(max(mats_a), max(mats_b))
    if hi >= lo:
        grid = np.arange(np.ceil(lo / step) * step, hi + 1e-9, step)
        return [float(x) for x in grid] if len(grid) else [float((lo + hi) / 2)]
    return [float((lo + hi) / 2)]


@dataclass
class IssuerRisk:
    """Risk numbers for one issuer; NaN when not available."""

    ticker: str
    lev_lease_adj: float
    breakeven_margin: float = float("nan")
    renewal_dependent_ebitda_years: float = float("nan")
    duration_gap: float = float("nan")
    pd_1y: float = float("nan")
    rating: str | None = None
    extra: dict = field(default_factory=dict)


RISK_METRICS = {
    "lev_lease_adj": "turn of lease-adjusted leverage",
    "renewal_dependent_ebitda_years": "year of EBITDA that depends on renewal",
    "breakeven_margin": "unit of breakeven margin",
    "duration_gap": "year of duration gap",
}


def pair_price_of_risk(spread_a: float, spread_b: float, risk_a: IssuerRisk, risk_b: IssuerRisk) -> pd.DataFrame:
    """Section 7.4 across issuers: spread gap over risk gap for each risk metric (bp per unit).

    Also gives each issuer's spread per unit of risk. The issuer with more spread per unit of a risk is the
    cheaper one on that risk; the verdict holds only where the metrics agree.
    """
    rows = []
    for key, label in RISK_METRICS.items():
        ra, rb = getattr(risk_a, key), getattr(risk_b, key)
        if np.isnan(ra) or np.isnan(rb) or ra <= 0 or rb <= 0:
            continue
        per_a, per_b = spread_a / ra * 1e4, spread_b / rb * 1e4
        slope = (spread_a - spread_b) / (ra - rb) * 1e4 if ra != rb else float("nan")
        rows.append({
            "metric": key, "unit": label, f"risk_{risk_a.ticker}": ra, f"risk_{risk_b.ticker}": rb,
            f"bp_per_unit_{risk_a.ticker}": per_a, f"bp_per_unit_{risk_b.ticker}": per_b,
            "gap_bp_per_unit": slope,
            "cheaper": risk_a.ticker if per_a > per_b else risk_b.ticker,
        })
    return pd.DataFrame(rows)


def benchmark_excess(spread: float, maturity: float, buckets: pd.DataFrame) -> tuple[float, float]:
    """Spread over the high yield benchmark median in the bond's maturity bucket, in bp, and a robust z-score.

    `buckets` has columns lo, hi, median, iqr (decimals). z uses IQR / 1.349 as the scale.
    """
    hit = buckets[(buckets["lo"] <= maturity) & (maturity < buckets["hi"])]
    if not len(hit):
        hit = buckets.iloc[[int(np.argmin(np.abs((buckets["lo"] + buckets["hi"]) / 2 - maturity)))]]
    med, iqr = float(hit["median"].iloc[0]), float(hit["iqr"].iloc[0])
    z = (spread - med) / (iqr / 1.349) if iqr > 0 else float("nan")
    return (spread - med) * 1e4, float(z)


def bond_table(
    bonds: pd.DataFrame, clock_results: Mapping[str, clocks.ClockResult], risks: Mapping[str, IssuerRisk],
    buckets: pd.DataFrame | None, market_kappa: float | None,
) -> pd.DataFrame:
    """Per-bond relative value table.

    `bonds` needs ticker, cusip, coupon, maturity_years, yield, g_spread. Adds modified duration, spread per turn,
    cover to maturity, benchmark excess, and kappa against the market where a PD exists.
    """
    out = bonds.copy()
    out["mod_duration"] = [modified_duration(y, c, m) for y, c, m in zip(out["yield"], out["coupon"], out["maturity_years"])]
    out["g_spread_bp"] = out["g_spread"] * 1e4
    out["spread_per_turn_bp"] = [s * 1e4 / risks[t].lev_lease_adj if risks[t].lev_lease_adj > 0 else np.nan
                                 for s, t in zip(out["g_spread"], out["ticker"])]
    out["cover_to_maturity"] = [cover_to_maturity(clock_results[t], m) if t in clock_results else np.nan
                                for t, m in zip(out["ticker"], out["maturity_years"])]
    if buckets is not None and len(buckets):
        ex = [benchmark_excess(s, m, buckets) for s, m in zip(out["g_spread"], out["maturity_years"])]
        out["excess_vs_hy_bp"] = [e[0] for e in ex]
        out["z_vs_hy"] = [e[1] for e in ex]
    pds = [risks[t].pd_1y for t in out["ticker"]]
    out["kappa"] = [kappa(s, p, SENIOR_UNSECURED_LGD) if p == p else np.nan for s, p in zip(out["g_spread"], pds)]
    if market_kappa:
        out["kappa_vs_market"] = out["kappa"] / market_kappa
    return out
