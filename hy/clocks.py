"""Cost clock against revenue clock: duration mismatch in fixed obligations (methodology Section 4.7).

A borrower's fixed obligations (rent, debt principal, take-or-pay purchases) run on one clock; its contracted
revenue runs on another. When the obligations are longer than the contracts, the gap is a bet on renewal,
and unsecured creditors carry it. This module puts both clocks on one annual grid and measures the gap.

Conventions: time `t` is in years from the as-of date; amounts in USD millions; each schedule is a list of
`Bucket`s, each spread evenly over [start, start + length).
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np

# Moody's lease multiple as Lim, Mann, Mihov (2017) state it. Same value as hy.state.LEASE_MULTIPLE; a test holds them equal.
MOODYS_RENT_MULTIPLE = 8.0
# Obligation classes of Section 4.7.1. Andrade, Henry, Nanda (2014 draft) price each one apart.
OBLIGATION_CLASSES = ("debt", "lease", "purchase_essential", "purchase_moderate", "purchase_non_essential")


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


def obligation_class(name: str) -> str:
    """Section 4.7.1 class of an obligation line. It reports only, and `obligation_kind` stays as the Section 4.7 split.

    Finance leases go to debt, because a finance lessor is roughly a secured lender (card gavazza-2010). A purchase
    line with no essentiality label reads "purchase_moderate": Andrade et al. pool moderate and missing in one group.
    Intuition: three claims with one name in the old split can price differently per dollar."""
    n = name.lower()
    if any(k in n for k in ("debt", "principal", "interest", "finance lease", "capital lease")):
        return "debt"
    if any(k in n for k in ("purchase", "take-or-pay", "take or pay")):
        if "non-essential" in n or "non essential" in n or "nonessential" in n:
            return "purchase_non_essential"
        return "purchase_essential" if "essential" in n else "purchase_moderate"
    return "lease"


def sp_tail_years(amounts: Sequence[float]) -> float:
    """Whole years after the stated ladder: the closest integer to thereafter / last stated year, at least 1.

    S&P method as Andrade et al. (2014 draft, p. 16) and Lim et al. (2017) state it. `tail_years_run_rate` keeps the
    fraction for the time grid. NaN when no positive last stated year exists, because the rule then has no rate."""
    if len(amounts) < 2 or amounts[-1] <= 0:
        return 0.0
    if amounts[-2] <= 0:
        return float("nan")
    return float(max(1, int(np.floor(amounts[-1] / amounts[-2] + 0.5))))


def sp_present_value(amounts: Sequence[float], rate: float) -> float:
    """Present value of a filed ladder: stated years, then the "thereafter" line at a constant yearly amount.

    `amounts` holds the stated years, then "thereafter". Payments fall at year end (Andrade et al., p. 16). It serves
    leases and purchase commitments. The discount rate is a choice, and each source differs: swap rate less 10 bp
    (Andrade et al.), firm bond yield (Jung and Scarlat, Appendix). Intuition: a dollar of rent due in 12 years is not a
    dollar of debt today."""
    if len(amounts) < 2 or rate <= -1:
        return float("nan")
    stated = np.asarray(amounts[:-1], dtype=float)
    pv = float((stated / (1.0 + rate) ** np.arange(1, len(stated) + 1)).sum())
    n = sp_tail_years(amounts)
    if n != n:
        return float("nan")
    if n == 0:
        return pv
    years = np.arange(len(stated) + 1, len(stated) + int(n) + 1)
    return pv + float(((amounts[-1] / n) / (1.0 + rate) ** years).sum())


def moodys_lease(pv_contract: float, rent: float, multiple: float = MOODYS_RENT_MULTIPLE) -> float:
    """The higher of the contractual present value and `multiple` x current rent (Lim et al. 2017, p. 102).

    Use it before ASC 842 only, by the framework F8 rule. Intuition: the contract value holds only signed payments, and
    the multiple reads rent as if it never ends. NaN when an input is NaN."""
    return float(max(pv_contract, multiple * rent)) if pv_contract == pv_contract and rent == rent else float("nan")


def lease_renewal_gap(pv_contract: float, rent: float, ebitdar: float, multiple: float = MOODYS_RENT_MULTIPLE) -> float:
    """(Moody's lease - contractual present value) / EBITDAR. Our extension, with no source test.

    Intuition: rent that the business needs after the signed term ends, in years of today's cash. NaN at EBITDAR <= 0."""
    if not ebitdar > 0:
        return float("nan")
    return (moodys_lease(pv_contract, rent, multiple) - pv_contract) / ebitdar


def executory_leverage(debt: float, pv_leases: float, pv_purchases: float, market_equity: float) -> dict[str, float]:
    """Three leverage parts over one denominator (Andrade et al. 2014 draft, pp. 16-17). The parts add to total leverage.

    Intuition: compare the three claims per unit of leverage, on the Merton firm value. Issuers with no listed equity
    read NaN. Each part shares a denominator, so test the parts with the placebo of Method 2, data rule 7."""
    total = market_equity + debt + pv_leases + pv_purchases
    if not total > 0:
        nan = float("nan")
        return {"bs_debt": nan, "op_leases": nan, "purchase_obligations": nan}
    return {"bs_debt": debt / total, "op_leases": pv_leases / total, "purchase_obligations": pv_purchases / total}


def lease_gap(actual: float, estimated: float, assets: float) -> dict[str, float]:
    """Lease liability that the prior footnote did not show, over assets (Jung and Scarlat 2024, Appendix).

    `gap` is actual less estimated. `undervalued` and `overvalued` are its two parts, both at or above 0. Intuition: only
    a surprise can move a price, and the source finds a yield rise on the undervalued part only."""
    if not assets > 0:
        nan = float("nan")
        return {"gap": nan, "undervalued": nan, "overvalued": nan}
    gap = (actual - estimated) / assets
    return {"gap": gap, "undervalued": max(gap, 0.0), "overvalued": max(-gap, 0.0)}


_TERMINABLE = re.compile(r"\b(can|may) (now )?terminate\b")
_NON_ESSENTIAL = re.compile(r"raw material|commodit|capital project|capital expenditure|construction")
_ESSENTIAL = re.compile(r"network|telecommunication|transport services|pipeline|software")


def purchase_essentiality(text: str, retail: bool = False) -> str:
    """Code a filing's purchase obligation text as "essential", "non_essential", or "moderate".

    Keyword form of the coding principles of Andrade et al. (2014 draft, p. 18). The authors coded by judgement, so this
    coder is our extension. Commodities and capex are non-essential. Specialized inputs are essential. Retail inventory
    is essential. The earlier mention wins when text lists several. A right to terminate reads non-essential (our
    reading of the Chiron example). The coder matches 9 of the 10 printed examples of the source Appendix B, in sample.
    A test names the miss. Run an audit of hand-coded filings before a result reads this field."""
    t = " ".join(text.lower().split())
    if _TERMINABLE.search(t):
        return "non_essential"
    non, ess = _NON_ESSENTIAL.search(t), _ESSENTIAL.search(t)
    if non and (not ess or non.start() < ess.start()):
        return "non_essential"
    if ess:
        return "essential"
    return "essential" if retail and "inventory" in t else "moderate"


def customer_persistence(
    history: Sequence[Mapping[str, float]], min_share: float = 0.10, min_years: int = 3
) -> dict[str, float]:
    """Durable, new, and dropped customer shares from annual customer lists, oldest first. Revenue clock input.

    A durable customer holds at least `min_share` in at least `min_years` filings and in the latest one (Oliveira et al.
    2017, pp. 134-135). `dropped_share` is the prior-year share of customers absent from the latest list. Absence can
    mean a lost contract, or a customer below 10% (Oliveira et al.). Reading it as non-renewal is our extension. An empty
    latest list is NaN, because not disclosed is not zero. Names must already be matched by the caller."""
    latest = {k: v for k, v in history[-1].items() if v == v} if history else {}
    if not latest:
        nan = float("nan")
        return {"durable_share": nan, "new_share": nan, "dropped_share": nan, "n_durable": nan}
    counts = {k: sum(1 for y in history if y.get(k, 0.0) >= min_share) for k in latest}
    durable = [k for k, v in latest.items() if v >= min_share and counts[k] >= min_years]
    prior = history[-2] if len(history) > 1 else {}
    return {
        "durable_share": float(sum(latest[k] for k in durable)),
        "new_share": float(sum(v for k, v in latest.items() if k not in prior)) if prior else float("nan"),
        "dropped_share": float(sum(v for k, v in prior.items() if k not in latest and v == v)) if prior else float("nan"),
        "n_durable": float(len(durable)),
    }


def cost_elasticity(costs: Sequence[float], sales: Sequence[float], lag: int = 4, min_obs: int = 20) -> float:
    """Slope of log change in cash operating costs on log change in sales, over year-on-year quarters.

    Bhojraj et al. (2021, eq. 1, p. 83) use 40 quarters, and report similar results at 20 and 32. Both series run oldest
    first. Pass only quarters public at the decision time. A slope near 1 means costs flex with sales. A slope near 0
    means costs are fixed. Intuition: this is the cost clock in one number, measured from cash and not from any disclosed
    schedule. NaN below `min_obs` valid changes, or with no variation in sales."""
    c, r = np.asarray(costs, dtype=float), np.asarray(sales, dtype=float)
    if len(c) != len(r) or len(c) <= lag:
        return float("nan")
    ok = (c[lag:] > 0) & (c[:-lag] > 0) & (r[lag:] > 0) & (r[:-lag] > 0)
    if int(ok.sum()) < min_obs:
        return float("nan")
    dc, dr = np.log(c[lag:][ok] / c[:-lag][ok]), np.log(r[lag:][ok] / r[:-lag][ok])
    var = float(((dr - dr.mean()) ** 2).sum())
    return float(((dr - dr.mean()) * (dc - dc.mean())).sum() / var) if var > 0 else float("nan")


def labor_share(labor_expense: float, ebitda: float) -> float:
    """Labor expense over labor expense plus EBITDA, clipped to [0, 1] (Favilukis et al., 2017 draft, p. 13).

    A non-positive denominator reads 1, by the same logic as the negative EBITDA leverage cap: the worst issuers must not
    read as low labor risk. The clip is our rule. Intuition: wages are a claim that ranks ahead of the bond in practice,
    so the larger their share of value added, the less cash the bond has behind it. NaN when labor expense is NaN."""
    if labor_expense != labor_expense or ebitda != ebitda:
        return float("nan")
    denom = labor_expense + ebitda
    return 1.0 if denom <= 0 else float(np.clip(labor_expense / denom, 0.0, 1.0))


def stress_margin(margin: float, labor_to_revenue: float, revenue_fall: float, labor_elasticity: float) -> float:
    """Cash margin after a revenue fall, when other costs flex fully and labor flexes by `labor_elasticity`. Our extension.

    m - (L / R) x (1 - rho) / (1 - x). Use this for labor in the Section 4.7 downside. Do not add a labor line to the
    obligations, because the EBITDAR margin is already after labor, so a line would count labor twice."""
    if not 0.0 <= revenue_fall < 1.0:
        return float("nan")
    return margin - labor_to_revenue * revenue_fall * (1.0 - labor_elasticity) / (1.0 - revenue_fall)


def float_unhedged(floating_debt: float, pay_fixed_notional: float, total_debt: float) -> float:
    """Share of debt that floats after pay-fixed swaps. Our extension of Campello et al. (w16622), who count gross notional.

    Intuition: `interest` uses one fixed rate, so this field shows how far that rate can move. Swaps to floating do not
    reduce it. NaN unless total debt is positive."""
    if not total_debt > 0:
        return float("nan")
    return float(np.clip((floating_debt - pay_fixed_notional) / total_debt, 0.0, 1.0))


def collateral_weighted(pool: Mapping[str, float], by_type: Mapping[str, float]) -> float:
    """Value-weighted mean of a per-type score over a collateral pool (Benmelech and Bergman, w13874 and w15708).

    `pool` maps an asset type to its weight, seats x count for aircraft. `by_type` maps a type to its score: other
    operators with at least 5 of the type for redeployability, or failed operators for a peer shock. The caller removes
    the issuer and bankrupt operators from the counts. A type with no score makes the result NaN, because a missing type
    is not a zero. Our extension applies the same form to vessels, rigs, and rail cars."""
    total = float(sum(pool.values()))
    if not total > 0 or any(k not in by_type for k in pool):
        return float("nan")
    return float(sum(w * by_type[k] for k, w in pool.items()) / total)


def peer_shock(pool: Mapping[str, float], failed_by_type: Mapping[str, float]) -> float:
    """log(1 + seat-weighted failed operators of the pool's asset types), with the natural log.

    Benmelech and Bergman (2011) state a log form, give no base, and print effects on mixed scales. So fit our own slope.
    The first failed buyer is about 19.5 bp in base 10 and 44.8 bp in natural log, on their coefficient of 64.666."""
    v = collateral_weighted(pool, failed_by_type)
    return float(np.log1p(v)) if v == v and v >= 0 else float("nan")


def industry_distress(peer_returns: Sequence[float], cut: float = -0.30, min_peers: int = 5) -> float:
    """1 if the median peer stock return is at or below `cut`, else 0 (Acharya et al. 2007, Distress1, p. 802).

    The caller leaves the issuer out of `peer_returns`. Peers are the 3-digit SIC group in the source. NaN below
    `min_peers` valid returns. Intuition: when an industry is in distress, its natural buyers cannot pay, so recovery
    falls. The source tests recovery only, in 1982 to 1999."""
    v = [x for x in peer_returns if x == x]
    if len(v) < min_peers:
        return float("nan")
    return 1.0 if float(np.median(v)) <= cut else 0.0


def competition_flag(hhi: float, hhi_all_industries: Sequence[float]) -> float:
    """1 if the industry concentration is in the lowest yearly quartile, else 0 (Valta 2012, `Competition`, p. 664).

    The source uses the fitted Hoberg-Phillips SIC-3 index and tests loan spreads. A bond test is still open. NaN when
    the inputs are missing. Intuition: rivals limit how far a borrower can pass on a cost shock."""
    v = [x for x in hhi_all_industries if x == x]
    if hhi != hhi or not v:
        return float("nan")
    return 1.0 if hhi <= float(np.quantile(v, 0.25)) else 0.0


BORROWING_BASE_FACTORS = {  # low, high share of PV-10 by reserve class. Gilje et al. (2020), Fig. 3, p. 1319
    "producing": (0.90, 0.95),
    "nonproducing": (0.65, 0.75),
    "undeveloped": (0.25, 0.50),
    "unproved": (0.0, 0.0),
}


def borrowing_base_collateral(pv10_by_class: Mapping[str, float]) -> tuple[float, float]:
    """Low and high lendable value of an E&P reserve book: sum of factor x PV-10 (Gilje et al. 2020, Fig. 3, p. 1319).

    An unknown class raises an error, because a silent zero would understate nothing and hide a typing fault. Intuition:
    banks lend against producing wells, and much less against undrilled ones, so the base resets on what is in the ground."""
    lo = hi = 0.0
    for k, v in pv10_by_class.items():
        f = BORROWING_BASE_FACTORS[k]
        lo, hi = lo + f[0] * v, hi + f[1] * v
    return lo, hi


def soft_revenue(run_rate: float, churn: float, horizon: int = 25) -> np.ndarray:
    """Revenue grid with no contracts: today's run rate decays by `churn` a year, R0 (1 - churn)^t. Our extension.

    It gives a revenue clock to issuers with no RPO, and `mismatch` accepts the grid. Read `coverage_contracted`,
    `breakeven_margin`, and `max_cum_shortfall` on it. Do not read `revenue_runoff`, because a decay has no contract end, so that
    field moves with the grid length. A well decline rate can stand in for `churn` in E&P (our extension). Gourio and Rudanko (w17191) set 0.15
    from anecdote and test no credit outcome, so `churn` is a stated assumption. Report the result at several values. Each
    year is the mean over the year, so the first year is below the run rate. Intuition: customers leave at a rate, and
    fixed charges do not."""
    if not 0.0 <= churn < 1.0 or not run_rate >= 0:
        return np.full(horizon, np.nan)
    if churn == 0.0:
        return np.full(horizon, float(run_rate))
    decay = np.log(1.0 - churn)
    t = np.arange(horizon, dtype=float)
    return run_rate * ((1.0 - churn) ** (t + 1) - (1.0 - churn) ** t) / decay


def delta_drc(drc: float, drc_prior: float, assets: float, assets_prior: float) -> float:
    """Change in the current deferred revenue liability over average assets (Prakash and Sinha 2009 draft, p. 13).

    A rise depresses this year's margin and lifts next year's, because revenue waits and period costs do not. The source
    finds a positive link to next-year margin and to next-year stock return. It has no bond test. ASC 606 renames and
    remeasures the liability, so flag the adoption year. NaN unless all inputs exist and average assets are positive."""
    avg = (assets + assets_prior) / 2.0
    return (drc - drc_prior) / avg if avg > 0 and drc == drc and drc_prior == drc_prior else float("nan")


def rev_abs_growth(revenue: float, revenue_prior: float) -> float:
    """Absolute log change in yearly revenue. An outcome in Baker et al. (w27707, Table 5), and our proxy for revenue
    instability where no RPO exists. It has no credit test. NaN unless both years are positive."""
    return abs(float(np.log(revenue / revenue_prior))) if revenue > 0 and revenue_prior > 0 else float("nan")


def sga_sales(sga: float, sales: float, sic: int | None = None) -> float:
    """SG&A over sales, the customer capital proxy that Baker et al. test (w27707). NaN for SIC 5000 to 5999, because
    the source calls the proxy poor in retail and restaurants. It has no credit test."""
    if sic is not None and 5000 <= sic <= 5999:
        return float("nan")
    return sga / sales if sales > 0 else float("nan")


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
      `renewal_<class>_amount` splits the same total by `OBLIGATION_CLASSES`. It reports only (Section 4.7.1).
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
    for cls in OBLIGATION_CLASSES:
        g = sum((v for k, v in obs.items() if obligation_class(k) == cls), np.zeros(horizon))
        m[f"renewal_{cls}_amount"] = share_after(g, run) * float(g.sum()) if g.sum() > 0 else 0.0
    m["duration_gap"] = m["dur_obligations"] - m["dur_revenue"]
    m["breakeven_margin"] = float(total.sum() / rev.sum()) if rev.sum() > 0 else float("nan")
    m["renewal_revenue_years"] = (
        m["renewal_dependent_amount"] / cash_margin / run_rate_revenue
        if run_rate_revenue and cash_margin > 0 else float("nan")
    )
    return ClockResult(np.arange(horizon), obs, rev, cash_margin, m)
