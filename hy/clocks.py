"""Cost clock against revenue clock: duration mismatch in fixed obligations (methodology Section 4.7).

A borrower's fixed obligations (rent, debt principal, take-or-pay purchases) run on one clock; its contracted
revenue runs on another. When the obligations are longer than the contracts, the gap is a bet on renewal,
and unsecured creditors carry it. This module puts both clocks on one annual grid and measures the gap.

Conventions: time `t` is in years from the as-of date; amounts in USD millions; each schedule is a list of
`Bucket`s, each spread evenly over [start, start + length).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Bucket:
    """An amount spread evenly over [start, start + length) years from the as-of date."""

    start: float
    length: float
    amount: float


def to_grid(buckets: Sequence[Bucket] | np.ndarray, horizon: int) -> np.ndarray:
    """Annual amounts on years [0,1), [1,2), ... [horizon-1, horizon). Mass past the horizon goes to the last year.

    An array passes through, cut or zero-padded to `horizon`.
    """
    if isinstance(buckets, np.ndarray):
        out = np.zeros(horizon)
        n = min(horizon, len(buckets))
        out[:n] = buckets[:n]
        out[-1] += buckets[n:].sum()
        return out
    grid = np.zeros(horizon)
    for b in buckets:
        if b.amount == 0 or np.isnan(b.amount):
            continue
        if b.length <= 0:
            grid[min(int(b.start), horizon - 1)] += b.amount
            continue
        rate = b.amount / b.length
        lo, hi = b.start, b.start + b.length
        for y in range(horizon):
            overlap = max(0.0, min(hi, y + 1) - max(lo, y))
            grid[y] += rate * overlap
        past = max(0.0, hi - max(lo, horizon))
        grid[-1] += rate * past
    return grid


def ladder(amounts: Sequence[float], first_length: float = 1.0, tail_years: float = 5.0) -> list[Bucket]:
    """Maturity ladder to buckets: first bucket of `first_length` years, then 1-year buckets, the last amount
    spread over `tail_years` (the filing's "thereafter" line).

    Intuition: filings give 5 years plus "thereafter"; the tail length is an assumption and must be stated.
    """
    out, t = [], 0.0
    for i, a in enumerate(amounts):
        if i == len(amounts) - 1:
            out.append(Bucket(t, tail_years, a))
        else:
            length = first_length if i == 0 else 1.0
            out.append(Bucket(t, length, a))
            t += length
    return out


def tail_years_run_rate(amounts: Sequence[float], default: float = 5.0) -> float:
    """Length of the "thereafter" bucket if payments continue at the last stated yearly amount until used up.

    Analyst convention for lease and purchase ladders. Intuition: a level-rent lease keeps paying the same rent;
    the tail ends when the stated total runs out. A stated weighted-average lease term averages lease lengths,
    not payment dates, so it cannot set the tail directly.
    """
    if len(amounts) < 2 or amounts[-2] <= 0 or amounts[-1] <= 0:
        return default
    return float(amounts[-1] / amounts[-2])


def uncommenced(total: float, commence_from: float, commence_to: float, term_years: float, n: int = 12) -> list[Bucket]:
    """Signed leases not yet started: `total` payments, commencements spread evenly over [from, to], each a level
    annuity over `term_years`. Intuition: the rent clock starts when the landlord delivers, not when revenue starts."""
    starts = np.linspace(commence_from, commence_to, n)
    return [Bucket(float(s), term_years, total / n) for s in starts]


def rpo(total: float, windows: Sequence[tuple[float, float, float]], tail_years: float) -> list[Bucket]:
    """Contracted revenue (remaining performance obligation) to buckets.

    `windows` are (start, length, share) from the filing; the unallocated share runs evenly over `tail_years`
    after the last window. Intuition: the backlog burns down on the filer's own stated timetable.
    """
    out, end, used = [], 0.0, 0.0
    for start, length, share in windows:
        out.append(Bucket(start, length, total * share))
        end, used = max(end, start + length), used + share
    if used < 1 - 1e-9:
        out.append(Bucket(end, tail_years, total * (1 - used)))
    return out


def interest(principal: Sequence[Bucket], outstanding: float, rate: float, horizon: int) -> np.ndarray:
    """Interest on the declining balance: outstanding at the start of each year times `rate`.

    The balance falls by the principal ladder; no refinancing is assumed. Intuition: coupons are a fixed charge
    on the same clock as the principal, and they stop only when the debt is repaid.
    """
    paid = to_grid(principal, horizon)
    opening = outstanding - np.concatenate([[0.0], np.cumsum(paid)[:-1]])
    mid = np.clip(opening - paid / 2, 0.0, None)
    return mid * rate


def duration(grid: np.ndarray) -> float:
    """Amount-weighted mean time (years, bucket mid-points). Intuition: the centre of mass of each clock."""
    t = np.arange(len(grid)) + 0.5
    s = grid.sum()
    return float((t * grid).sum() / s) if s > 0 else float("nan")


def runoff_year(grid: np.ndarray, share: float = 0.99) -> float:
    """First year end by which `share` of the schedule has passed. Intuition: when the contract book is gone."""
    c = np.cumsum(grid) / grid.sum() if grid.sum() > 0 else np.zeros_like(grid)
    hit = np.nonzero(c >= share)[0]
    return float(hit[0] + 1) if len(hit) else float(len(grid))


def share_after(grid: np.ndarray, t: float) -> float:
    """Share of the schedule that falls after year `t`. Intuition: obligations with no contract behind them."""
    s = grid.sum()
    if s <= 0:
        return float("nan")
    whole = int(np.floor(t))
    part = grid[whole] * (whole + 1 - t) if whole < len(grid) else 0.0
    return float((grid[whole + 1:].sum() + part) / s)


def concentration(shares: Mapping[str, float]) -> dict[str, float]:
    """Top-1, top-3, and a lower bound on the Herfindahl index from disclosed customer shares (fractions).

    Undisclosed customers are each below the disclosure threshold, so the HHI is a floor.
    """
    v = sorted((x for x in shares.values() if x == x), reverse=True)
    if not v:
        nan = float("nan")
        return {"top1": nan, "top3": nan, "hhi_floor": nan, "disclosed": 0.0}  # not disclosed is not zero
    return {"top1": v[0], "top3": float(sum(v[:3])), "hhi_floor": float(sum(x * x for x in v)), "disclosed": float(len(v))}


def obligation_kind(name: str) -> str:
    """Section 4.7 renewal split. Debt principal and interest are "refinance": the capital market can roll them.
    Rent and purchase commitments are "recontract": only new or renewed customer contracts pay them.
    Intuition: a bond refinanced at a wider spread survives; an empty data hall pays rent from nothing."""
    n = name.lower()
    return "refinance" if any(k in n for k in ("debt", "principal", "interest")) else "recontract"


@dataclass
class ClockResult:
    """Annual grids and the mismatch metrics for one borrower."""

    years: np.ndarray
    obligations: dict[str, np.ndarray]
    revenue: np.ndarray
    cash_margin: float
    metrics: dict[str, float]

    @property
    def obligations_total(self) -> np.ndarray:
        return sum(self.obligations.values())  # type: ignore[return-value]


def mismatch(
    obligations: Mapping[str, Sequence[Bucket]],
    revenue: Sequence[Bucket],
    cash_margin: float,
    horizon: int = 25,
    run_rate_revenue: float | None = None,
) -> ClockResult:
    """Put both clocks on one grid and measure the gap (Section 4.7).

    - `dur_obligations`, `dur_revenue`, `duration_gap`: centres of mass and their difference (years).
    - `revenue_runoff`: year by which 99% of the contract book is recognised.
    - `renewal_dependent_share`: share of fixed obligations due after the runoff. It splits (`obligation_kind`) into
      `renewal_refinance_share` (debt principal and interest: the market can roll it) and `renewal_recontract_share`
      (rent and purchase commitments: only customers can pay it). The two add up to the total. DBRS (2024) treats
      refinancing and recontracting as separate risks (research/cards/two-clocks-origin.md).
    - `contracted_cash`: revenue x `cash_margin`, the cash the contracts throw off for fixed charges
      (use an EBITDAR-type margin, because rent is one of the obligations).
    - `first_shortfall_year`, `max_cum_shortfall`: first year cumulative contracted cash falls below cumulative
      obligations, and the largest such gap: the amount that must be refinanced or won by renewal.
    - `breakeven_margin`: the cash margin at which signed contracts pay every fixed charge (sum O / sum R).
      Above 1, no margin is enough. Intuition: one testable number in place of a margin table.
    - `renewal_revenue_years`: revenue that must be signed after the runoff to pay the renewal-dependent charges at
      `cash_margin`, in years of `run_rate_revenue` (latest quarter x 4). Intuition: the size of the renewal bet
      against the business as it is today.
    """
    obs = {k: to_grid(v, horizon) for k, v in obligations.items()}
    total = sum(obs.values())
    rev = to_grid(revenue, horizon)
    cash = rev * cash_margin
    cum_gap = np.cumsum(cash) - np.cumsum(total)
    neg = np.nonzero(cum_gap < 0)[0]
    run = runoff_year(rev)
    m = {
        "obligations_total": float(total.sum()),
        "revenue_total": float(rev.sum()),
        "dur_obligations": duration(total),
        "dur_revenue": duration(rev),
        "revenue_runoff": run,
        "renewal_dependent_share": share_after(total, run),
        "renewal_dependent_amount": share_after(total, run) * float(total.sum()),
        "contracted_cash_total": float(cash.sum()),
        "coverage_contracted": float(cash.sum() / total.sum()) if total.sum() > 0 else float("nan"),
        "first_shortfall_year": float(neg[0] + 1) if len(neg) else float("nan"),
        "max_cum_shortfall": float(max(0.0, -cum_gap.min())),
    }
    for kind in ("refinance", "recontract"):
        g = sum((v for k, v in obs.items() if obligation_kind(k) == kind), np.zeros(horizon))
        amt = share_after(g, run) * float(g.sum()) if g.sum() > 0 else 0.0
        m[f"renewal_{kind}_amount"] = amt
        m[f"renewal_{kind}_share"] = amt / float(total.sum()) if total.sum() > 0 else float("nan")
    m["duration_gap"] = m["dur_obligations"] - m["dur_revenue"]
    m["breakeven_margin"] = float(total.sum() / rev.sum()) if rev.sum() > 0 else float("nan")
    m["renewal_revenue_years"] = (
        m["renewal_dependent_amount"] / cash_margin / run_rate_revenue
        if run_rate_revenue and cash_margin > 0 else float("nan")
    )
    return ClockResult(np.arange(horizon), obs, rev, cash_margin, m)
