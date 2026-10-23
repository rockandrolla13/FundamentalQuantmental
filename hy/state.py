"""Issuer state layer: profitability, cash, capital structure, flags, rating gap, covenants (Section 4).

Each public function computes one feature of methodology Section 4 from
inputs that the Section 3 records carry. The functions take plain numbers so
the forward layer (Section 5) can call them on projected values.
`issuer_state` assembles the Section 10.2 fields from one filing.

Conventions: amounts in USD millions; rates and ratios decimal; prices per
100 face. `IssuerFinancials` holds quarterly flows. Ratios against debt use
an annual EBITDA, which `issuer_state` sets to the quarter times
`periods_per_year` (run rate) unless the caller gives an LTM figure.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Mapping, Sequence

import numpy as np
from scipy import optimize, special

from hy.inputs import IssuerFinancials, NonRecurringItem, Tranche, assert_point_in_time

DAYS_PER_YEAR = 365.0
LEASE_MULTIPLE = 8.0  # Section 4.3, pp. 267-268

# The high yield index rule (Section 3.6, `hy_oas` proxy; data module step 5). One home for the constants: the live
# TRACE benchmark (hy.sources.trace_bonds, hy.sources.forecast_sources) and the backtest (hy.backtest) both use it.
# The universe (grade H, fixed coupon, not convertible, min_years to max_years left) is built where the bonds are
# loaded; tests/test_state.py keeps those defaults equal to these.
HY_INDEX_RULE = {"min_price": 80.0, "max_yield": 0.25, "min_years": 1.0, "max_years": 15.0}
COVENANT_CUSHION_RANGE = (0.15, 0.30)  # Section 4.6, p. 356


def _safe_div(num: float, den: float) -> float:
    """Return num / den; nan when den is zero, so a missing base never reads as zero."""
    return num / den if den != 0 else float("nan")


# ---------------------------------------------------------------- 4.1 Profitability


def ebitda_adj_analyst(ebitda_reported: float, items: Iterable[NonRecurringItem]) -> float:
    """Analyst-adjusted EBITDA (Section 4.1; Figure 7.3, p. 192).

    EBITDA^adj_t = EBITDA^rep_t + sum_i a_i NR_{i,t}, with a_i = 1 when the item
    does not recur and a_i = 0 when it recurs.

    Intuition: add back a charge only when it will not come again; a charge
    that recurs is an operating cost. A positive `amount` is a charge that
    reduced reported EBITDA; a gain has a negative amount and so is removed.
    """
    return ebitda_reported + sum(it.amount for it in items if not it.recurs)


def cash_nonrecurring(items: Iterable[NonRecurringItem]) -> float:
    """Cash nonrecurring charges that the add-back hid (hy-model-standards rule 1, Section 4.2).

    CashNR_t = sum_i a_i NR_{i,t} 1[cash_i].

    Intuition: an added-back cash charge raises EBITDA but the cash still left
    the company. Recurrent items already sit in reported EBITDA, so they are
    not counted again.
    """
    return sum(it.amount for it in items if it.cash and not it.recurs)


def addback_gap(ebitda_adj_company: float, ebitda_adj_analyst_value: float) -> float:
    """Addback gap (Section 4.1): ebitda_adj_company / ebitda_adj_analyst - 1.

    Intuition: the distance between the company's story and ours; a large gap precedes misses.
    """
    return _safe_div(ebitda_adj_company, ebitda_adj_analyst_value) - 1.0


def covenant_gap(ebitda_covenant: float, ebitda_adj_analyst_value: float) -> float:
    """Covenant gap (Section 4.1; pp. 353-354): ebitda_covenant / ebitda_adj_analyst - 1.

    Intuition: permissive covenant add-backs can hide a breach that the analyst EBITDA shows.
    """
    return _safe_div(ebitda_covenant, ebitda_adj_analyst_value) - 1.0


def margin(ebitda: float, revenue: float) -> float:
    """EBITDA margin (Section 4.1): ebitda / revenue.

    Intuition: the share of each sales dollar left before capex, interest, and tax.
    """
    return _safe_div(ebitda, revenue)


def margin_peer_gap(issuer_margin: float, peer_margins: Sequence[float]) -> float:
    """Margin peer gap (Section 4.1; p. 413): margin - median(peer margins).

    Intuition: a margin far above peers gives a cushion in a downturn (HCA 17.3% against Tenet 5.9%).
    """
    if len(peer_margins) == 0:
        return float("nan")
    return issuer_margin - float(np.median(np.asarray(peer_margins, dtype=float)))


def margin_trend(margins: Sequence[float], window: int = 8) -> float:
    """Margin trend t-statistic (Section 4.1): OLS slope of margin on time over `window` quarters / SE(slope).

    slope = sum (t - tbar)(m - mbar) / sum (t - tbar)^2;
    SE = sqrt( sum e^2 / (n - 2) / sum (t - tbar)^2 ).

    Intuition: the sign gives the direction of the operating trend, the size gives its strength.
    Return nan with fewer than 3 points; return +-inf for a perfect nonzero line.
    """
    m = np.asarray(margins, dtype=float)[-window:]
    n = m.size
    if n < 3:
        return float("nan")
    t = np.arange(n, dtype=float)
    tc = t - t.mean()
    sxx = float(tc @ tc)
    slope = float(tc @ (m - m.mean())) / sxx
    resid = m - m.mean() - slope * tc
    se = math.sqrt(float(resid @ resid) / (n - 2) / sxx)
    if se < 1e-14:
        return 0.0 if abs(slope) < 1e-14 else math.copysign(math.inf, slope)
    return slope / se


def organic_growth(reported_growth: float, fx_effect: float = 0.0, mna_effect: float = 0.0,
                   price_mix_effect: float = 0.0) -> float:
    """Organic growth (Section 4.1; pp. 209-211): reported growth - FX - M&A - price-mix effects.

    Intuition: volume growth is the part that persists; FX, deals, and price do not.
    """
    return reported_growth - fx_effect - mna_effect - price_mix_effect


def surprise(ebitda_actual: float, consensus: float) -> float:
    """Earnings surprise (Section 4.1; p. 216): (ebitda_actual - consensus) / consensus.

    Intuition: a beat or a miss relative to what the market expected.
    """
    return _safe_div(ebitda_actual - consensus, abs(consensus))


# ------------------------------------------------------- 4.2 Cash flow and liquidity


def fcf(ebitda_adj: float, cash_nr: float, capex: float, cash_interest: float, cash_tax: float,
        delta_wc: float = 0.0) -> float:
    """Free cash flow (Section 4.2 with the hy-model-standards cash charge rule).

    FCF_t = EBITDA^adj_t - CashNR_t - Capex_t - CashInterest_t - CashTax_t - dWC_t.

    Intuition: keep the adjusted earnings level, but charge the cash that the add-backs hid.
    A positive `delta_wc` is a working capital build, which consumes cash.
    """
    return ebitda_adj - cash_nr - capex - cash_interest - cash_tax - delta_wc


def liquidity_L(cash: float, commitment: float, borrowing_base: float, drawn: float,
                letters_of_credit: float) -> float:
    """Static liquidity (Section 4.2; Figure 8.3, p. 229).

    L_t = Cash_t + min(Commitment_t, BorrowingBase_t) - Drawn_t - LC_t.

    Intuition: what the issuer can spend today, with the ABL capped by its borrowing base.
    """
    return cash + min(commitment, borrowing_base) - drawn - letters_of_credit


def runway_q(liquidity: float, fcf_quarterly: float) -> float:
    """Liquidity runway in quarters (Section 4.2): L / max(0, -fcf_quarterly); inf when FCF >= 0.

    Intuition: the number of quarters until the cash runs out at the current burn.
    """
    burn = max(0.0, -fcf_quarterly)
    if burn == 0.0:
        return math.inf
    return max(liquidity, 0.0) / burn


def maturities_to_h(maturity_schedule: Sequence[float], h: int) -> float:
    """Debt due within h quarters from the annual schedule of Section 3.2 (Figure 8.4, p. 229).

    Sum of maturity_schedule[0 .. ceil(h/4) - 1].

    Intuition: the wall the issuer must pay or refinance inside the horizon.
    """
    years = math.ceil(h / 4)
    return float(sum(maturity_schedule[:years]))


def wall_cover_h(liquidity: float, fcf_forecast: Sequence[float], maturities_due: float, h: int) -> float:
    """Maturity wall cover (Section 4.2): (L + sum_{q<=h} FCF_q) / sum of maturities to h.

    Intuition: below 1 the issuer must refinance; inf when nothing matures.
    """
    if maturities_due <= 0:
        return math.inf
    return (liquidity + float(sum(list(fcf_forecast)[:h]))) / maturities_due


def capex_flex(capex_total: float, capex_maintenance: float) -> float:
    """Capex flexibility (Section 4.2; p. 266): (capex_total - capex_maintenance) / capex_total.

    Intuition: the share of capex the issuer can cut in a downturn.
    """
    return _safe_div(capex_total - capex_maintenance, capex_total)


def working_capital_days(inventory: float, receivables: float, payables: float, cogs: float,
                         revenue: float, period_days: float = DAYS_PER_YEAR / 4) -> dict[str, float]:
    """Inventory, receivable, and payable days (Section 4.2; pp. 240-242).

    DIO = inventory / cogs x D; DSO = receivables / revenue x D; DPO = payables / cogs x D,
    with D the days in the flow period (91.25 for a quarter).

    Intuition: days of sales or costs that sit in each working capital account.
    """
    return {
        "inventory_days": _safe_div(inventory, cogs) * period_days,
        "receivable_days": _safe_div(receivables, revenue) * period_days,
        "payable_days": _safe_div(payables, cogs) * period_days,
    }


def cash_cycle(inventory_days: float, receivable_days: float, payable_days: float) -> float:
    """Cash conversion cycle (Section 4.2; Figure 8.6, p. 230): DIO + DSO - DPO.

    Intuition: a longer cycle consumes cash as sales grow.
    """
    return inventory_days + receivable_days - payable_days


def payable_days_trend(payable_days_history: Sequence[float], lag: int = 4) -> float:
    """Payable days trend (Section 4.2; p. 231): DPO_t - DPO_{t-4}.

    Intuition: a fall signals that suppliers tighten trade credit.
    """
    if len(payable_days_history) <= lag:
        return float("nan")
    return float(payable_days_history[-1] - payable_days_history[-1 - lag])


# ----------------------------------------------------------- 4.3 Capital structure


def _find(tranches: Sequence[Tranche], key: str) -> Tranche:
    for t in tranches:
        if t.key == key:
            return t
    raise KeyError(key)


def debt_through(tranches: Sequence[Tranche], key: str) -> float:
    """Face of every claim with rank <= rank_k, at face (Section 4.3; p. 264).

    sum_{j: rank_j <= rank_k} F_j. Pari passu claims are included.

    Intuition: the debt the value must cover before tranche k is whole.
    """
    rk = _find(tranches, key).rank
    return float(sum(t.face for t in tranches if t.rank <= rk))


def lev_face_k(tranches: Sequence[Tranche], key: str, ebitda_adj: float) -> float:
    """Face leverage through tranche k (Section 4.3; Figure 9.6, p. 261).

    Lev^face_k = sum_{j: rank_j <= rank_k} F_j / EBITDA^adj.

    Intuition: turns of EBITDA the company must be worth for tranche k to be whole.
    """
    return _safe_div(debt_through(tranches, key), ebitda_adj)


def lev_mkt_k(tranches: Sequence[Tranche], key: str, ebitda_adj: float) -> float:
    """Market leverage, the creation multiple (Section 4.3; Figure 9.9, p. 265).

    Lev^mkt_k = (sum_{j: rank_j < rank_k} F_j + P_k F_k) / EBITDA^adj, with P_k = price / 100.

    Intuition: the valuation at which a buyer of tranche k at market creates the company.
    Pari passu peers are left out, as the formula's strict inequality states.
    """
    tk = _find(tranches, key)
    senior = sum(t.face for t in tranches if t.rank < tk.rank)
    return _safe_div(senior + tk.price / 100.0 * tk.face, ebitda_adj)


def ltv_k(tranches: Sequence[Tranche], key: str, tev: float) -> float:
    """Loan to value through tranche k (Section 4.3; p. 265).

    LTV_k = sum_{j: rank_j <= rank_k} F_j / TEV.

    Intuition: the share of enterprise value that the claims through k consume; recompute
    it with the current peer multiple, because LTV moves when multiples move.
    """
    return _safe_div(debt_through(tranches, key), tev)


def coverage(ebitda_adj: float, capex: float, interest: float) -> float:
    """Interest coverage (Section 4.3; p. 262): (EBITDA^adj - Capex) / Interest.

    Intuition: how many times the cash earnings after capex pay the interest.
    Use maintenance capex for the floor version.
    """
    return _safe_div(ebitda_adj - capex, interest)


def lev_lease_adj(debt: float, rent: float, ebitda_adj: float, multiple: float = LEASE_MULTIPLE) -> float:
    """Lease-adjusted leverage (Section 4.3; pp. 267-268): (debt + 8 x rent) / (EBITDA^adj + rent).

    Intuition: capitalise rent as debt and add it back to EBITDA, so lessees and owners compare.
    Use annual rent with annual EBITDA.
    """
    return _safe_div(debt + multiple * rent, ebitda_adj + rent)


def debt_adj(debt: float, pension_underfunded: float = 0.0, guarantees_weak: float = 0.0) -> float:
    """Adjusted debt (Section 4.3; p. 273): debt + pension deficit + guarantees to weak parties.

    Intuition: a claim that a creditor will enforce is debt, whatever the balance sheet calls it.
    """
    return debt + max(pension_underfunded, 0.0) + guarantees_weak


def net_lev(debt: float, cash: float, ebitda_adj: float) -> float:
    """Net leverage (Section 4.3): (debt - cash) / EBITDA^adj.

    Intuition: unrestricted cash can repay debt today.
    """
    return _safe_div(debt - cash, ebitda_adj)


def lev_gross(debt: float, ebitda_adj: float) -> float:
    """Gross leverage (hy-model-standards rule 3): total_debt / EBITDA^adj, no cash offset.

    Intuition: the structural exposure if the cash leaves before default.
    """
    return _safe_div(debt, ebitda_adj)


def fccr(ebitda_adj: float, cash_interest: float, mandatory_amort: float) -> float:
    """Fixed charge coverage (hy-model-standards rule 3): EBITDA^adj / (cash_interest + mandatory_amort).

    Intuition: for amortising loans, principal is a fixed charge like interest.
    """
    return _safe_div(ebitda_adj, cash_interest + mandatory_amort)


# ----------------------------------------------------------- 4.4 Qualitative flags

Q_FLAGS: tuple[str, ...] = (
    "secular_decline",
    "adverse_competition",
    "cyclicality",
    "regulation",
    "customer_concentration",
    "product_concentration",
    "fad_fashion",
    "commodity",
    "mgmt_change",
    "sponsor_behavior",
)


def q_vector(flags: Mapping[str, int]) -> np.ndarray:
    """Qualitative risk vector (Section 4.4; Figure 6.2, p. 158), in the order of `Q_FLAGS`.

    q = (q_1, ..., q_10), q_i in {0, 1, 2}; a missing flag scores 0.

    Intuition: keep each risk apart, because the fair spread model learns one weight per flag.
    """
    unknown = set(flags) - set(Q_FLAGS)
    if unknown:
        raise KeyError(f"unknown flags: {sorted(unknown)}")
    v = np.array([int(flags.get(name, 0)) for name in Q_FLAGS], dtype=int)
    if np.any((v < 0) | (v > 2)):
        raise ValueError("each flag must be 0, 1, or 2")
    return v


def q_score(vector: np.ndarray) -> int:
    """Qualitative score (Section 4.4): sum_i q_i.

    Intuition: a crude total of the risk count; the vector stays the model input.
    """
    return int(np.sum(vector))


# ----------------------------------------------------------------- 4.5 Rating gap


@dataclass
class OrdinalLogit:
    """Cumulative logit model of the agency rating (Section 4.5).

    P(r <= j | x) = sigma(theta_j - x' beta), j = 0 .. K-2, with theta increasing.
    Ratings are integer notches 0 .. K-1 where a higher number is a better rating,
    so a negative gap means the model rates the issuer below the agency.

    Intuition: one latent credit quality, cut into rating classes at fitted thresholds.
    """

    beta: np.ndarray | None = None
    theta: np.ndarray | None = None
    n_classes: int = 0
    _mean: np.ndarray | None = None
    _scale: np.ndarray | None = None
    l2: float = 1e-4

    @staticmethod
    def _unpack(params: np.ndarray, p: int) -> tuple[np.ndarray, np.ndarray]:
        beta = params[:p]
        raw = params[p:]
        theta = np.concatenate([[raw[0]], raw[0] + np.cumsum(np.exp(raw[1:]))])
        return beta, theta

    def _probs(self, z: np.ndarray, theta: np.ndarray) -> np.ndarray:
        cum = special.expit(theta[None, :] - z[:, None])  # n x (K-1)
        cum = np.hstack([np.zeros((z.size, 1)), cum, np.ones((z.size, 1))])
        return np.clip(np.diff(cum, axis=1), 1e-12, 1.0)

    def fit(self, X: np.ndarray, y: np.ndarray) -> "OrdinalLogit":
        """Fit by maximum likelihood with scipy.optimize (Section 4.5).

        max sum_i log P(r_i | x_i) - l2 |beta|^2.
        """
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=int)
        if X.ndim == 1:
            X = X[:, None]
        self.n_classes = int(y.max()) + 1
        k = self.n_classes
        if k < 2:
            raise ValueError("need at least two rating classes")
        self._mean = X.mean(axis=0)
        self._scale = X.std(axis=0)
        self._scale[self._scale == 0] = 1.0
        Xs = (X - self._mean) / self._scale
        p = Xs.shape[1]

        def nll(params: np.ndarray) -> float:
            beta, theta = self._unpack(params, p)
            pr = self._probs(Xs @ beta, theta)
            return -float(np.sum(np.log(pr[np.arange(y.size), y]))) + self.l2 * float(beta @ beta)

        cum_share = np.clip(np.cumsum(np.bincount(y, minlength=k))[:-1] / y.size, 0.01, 0.99)
        theta0 = special.logit(cum_share)
        raw0 = np.concatenate([[theta0[0]], np.log(np.maximum(np.diff(theta0), 0.05))])
        x0 = np.concatenate([np.zeros(p), raw0])
        res = optimize.minimize(nll, x0, method="BFGS")
        self.beta, self.theta = self._unpack(res.x, p)
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Class probabilities P(r | x) (Section 4.5)."""
        if self.beta is None:
            raise RuntimeError("fit the model first")
        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            X = X[:, None]
        Xs = (X - self._mean) / self._scale
        return self._probs(Xs @ self.beta, self.theta)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Fitted rating r_hat = argmax_r P(r | x) (Section 4.5)."""
        return np.argmax(self.predict_proba(X), axis=1)


def rating_gap(fitted_rating: np.ndarray | int, agency_rating: np.ndarray | int) -> np.ndarray | int:
    """Rating gap in notches (Section 4.5; p. 274): gap_i = r_hat_i - r^agency_i.

    Intuition: a negative gap means fundamentals sit below the agency rating, so a downgrade
    and its forced sales are likely (p. 418).
    """
    return np.asarray(fitted_rating) - np.asarray(agency_rating) if np.ndim(fitted_rating) else \
        int(fitted_rating) - int(agency_rating)


# ---------------------------------------------------------- 4.6 Covenant headroom


def lev_max_origination(debt: float, ebitda_mgmt: float, cushion: float) -> float:
    """Covenant level set at origination (Section 4.6; p. 356): Lev^max = D / ((1 - c) EBITDA^mgmt).

    Intuition: lenders let the plan EBITDA fall by the cushion c before the test trips.
    The cushion c must lie in [0.15, 0.30]. A 15% cushion on a 4.0x plan gives 4.7x.
    """
    lo, hi = COVENANT_CUSHION_RANGE
    if not lo <= cushion <= hi:
        raise ValueError(f"cushion {cushion} outside [{lo}, {hi}]")
    return _safe_div(debt, (1.0 - cushion) * ebitda_mgmt)


def covenant_headroom(lev_cov: float, lev_max: float) -> float:
    """Maintenance covenant headroom (Section 4.6): H_t = 1 - Lev^cov_t / Lev^max_t.

    Intuition: H is the fraction by which covenant EBITDA can fall before a breach,
    because Lev^cov / (1 - H) = Lev^max. Use covenant EBITDA, never analyst EBITDA.
    """
    return 1.0 - _safe_div(lev_cov, lev_max)


# ------------------------------------------------------------- 10.2 assembly


def issuer_state(
    fin: IssuerFinancials,
    tranches: list[Tranche],
    *,
    decision_time: datetime | None = None,
    periods_per_year: int = 4,
    ebitda_ltm: float | None = None,
    peer_margins: Sequence[float] = (),
    margin_history: Sequence[float] = (),
    payable_days_history: Sequence[float] = (),
    consensus_ebitda: float | None = None,
    delta_wc: float = 0.0,
    fcf_forecast: Sequence[float] = (),
    reported_growth: float | None = None,
    fx_effect: float = 0.0,
    mna_effect: float = 0.0,
    price_mix_effect: float = 0.0,
    flags: Mapping[str, int] | None = None,
    covenant_max: float | None = None,
) -> dict[str, object]:
    """Section 10.2 profitability, cash, capital structure, and qualitative fields from one filing.

    Uses Sections 4.1 to 4.4 and 4.6. Debt is the sum of tranche faces at face (p. 264).
    Annual EBITDA is `ebitda_ltm` when given, else the quarter times `periods_per_year`.
    A field that needs an input the caller did not give is nan.

    Intuition: one row that states how the issuer earns, spends, and owes, as of this filing.
    When `decision_time` is given, every record must be available before it.
    """
    if decision_time is not None:
        assert_point_in_time([fin, *tranches], decision_time)
    nan = float("nan")
    ppy = float(periods_per_year)

    e_adj_q = ebitda_adj_analyst(fin.ebitda_reported, fin.nonrecurring_items)
    e_adj_y = ebitda_ltm if ebitda_ltm is not None else e_adj_q * ppy
    cash_nr = cash_nonrecurring(fin.nonrecurring_items)
    fcf_q = fcf(e_adj_q, cash_nr, fin.capex_total, fin.cash_interest, fin.cash_taxes, delta_wc)
    debt = float(sum(t.face for t in tranches))
    d_adj = debt_adj(debt, fin.pension_underfunded, fin.guarantees_weak)
    L = liquidity_L(fin.cash, fin.revolver_commitment, fin.borrowing_base, fin.revolver_drawn,
                    fin.letters_of_credit)
    days = working_capital_days(fin.inventory, fin.receivables, fin.payables, fin.cogs, fin.revenue,
                                DAYS_PER_YEAR / ppy)
    m = margin(e_adj_q, fin.revenue)
    qv = q_vector(flags or {})
    fwd = list(fcf_forecast)

    def cover(h: int) -> float:
        if len(fwd) < h:
            return nan
        return wall_cover_h(L, fwd, maturities_to_h(fin.maturity_schedule, h), h)

    lev_cov = _safe_div(debt, fin.ebitda_covenant * ppy) if fin.ebitda_covenant else nan

    return {
        "issuer_id": tranches[0].issuer_id if tranches else "",
        "date": fin.as_of,
        "available_at": fin.available_at,
        # Profitability (4.1)
        "ebitda_adj_analyst": e_adj_q,
        "addback_gap": addback_gap(fin.ebitda_adj_company, e_adj_q) if fin.ebitda_adj_company else nan,
        "covenant_gap": covenant_gap(fin.ebitda_covenant, e_adj_q) if fin.ebitda_covenant else nan,
        "margin": m,
        "margin_trend": margin_trend([*margin_history, m]) if margin_history else nan,
        "margin_peer_gap": margin_peer_gap(m, peer_margins),
        "organic_growth": (organic_growth(reported_growth, fx_effect, mna_effect, price_mix_effect)
                           if reported_growth is not None else nan),
        "surprise": surprise(e_adj_q, consensus_ebitda) if consensus_ebitda is not None else nan,
        # Cash and liquidity (4.2)
        "fcf": fcf_q,
        "fcf_conversion": _safe_div(fcf_q, e_adj_q),
        "fcf_to_debt": _safe_div(fcf_q * ppy, debt),
        **days,
        "cash_cycle": cash_cycle(days["inventory_days"], days["receivable_days"], days["payable_days"]),
        "payable_days_trend": (payable_days_trend([*payable_days_history, days["payable_days"]])
                               if payable_days_history else nan),
        "liquidity_L": L,
        "runway_q": runway_q(L, fcf_q),
        "wall_cover_4": cover(4),
        "wall_cover_8": cover(8),
        "capex_flex": capex_flex(fin.capex_total, fin.capex_maintenance),
        # Capital structure (4.3)
        "total_debt": debt,
        "debt_adj": d_adj,
        "lev_gross": lev_gross(debt, e_adj_y),
        "lev_adj_total": lev_gross(d_adj, e_adj_y),
        "net_lev": net_lev(debt, fin.cash, e_adj_y),
        "coverage": coverage(e_adj_q, fin.capex_total, fin.cash_interest),
        "lev_lease_adj": lev_lease_adj(debt, fin.rent_expense * ppy, e_adj_y),
        "fccr": fccr(e_adj_q, fin.cash_interest, float(sum(t.mandatory_amort for t in tranches))),
        # Qualitative (4.4)
        "q_vector": qv,
        "q_score": q_score(qv),
        "mgmt_change": int(qv[Q_FLAGS.index("mgmt_change")]),
        "sponsor_behavior": int(qv[Q_FLAGS.index("sponsor_behavior")]),
        # Covenants (4.6)
        "lev_covenant": lev_cov,
        "H_t": covenant_headroom(lev_cov, covenant_max) if covenant_max is not None else nan,
    }


def hy_index_level(spread, price, yld) -> float:
    """High yield index spread (Section 3.6): the median spread of the universe's core bonds, those with price >=
    HY_INDEX_RULE["min_price"] and 0 < yield <= HY_INDEX_RULE["max_yield"]. NaN when no bond qualifies.
    Intuition: the level a typical performing high yield bond pays; the price and yield bounds keep distressed bonds
    and print errors out of the middle."""
    s, p, y = (np.asarray(x, dtype=float) for x in (spread, price, yld))
    core = (p >= HY_INDEX_RULE["min_price"]) & (y > 0) & (y <= HY_INDEX_RULE["max_yield"])
    return float(np.median(s[core])) if core.any() else float("nan")


DISTRESS_SPREAD = 0.10  # 1,000 bp: the market's distressed cut (hy.backtest.DISTRESSED_SPREAD uses the same level)


def distress_ratio(spread, yld) -> float:
    """Share of the universe's bonds with a positive yield whose spread exceeds DISTRESS_SPREAD (Section 3.6). No price
    filter and no cap: distressed bonds are the numerator. Intuition: how much of the market trades on recovery."""
    s, y = np.asarray(spread, dtype=float), np.asarray(yld, dtype=float)
    pos = y > 0
    return float((s[pos] > DISTRESS_SPREAD).mean()) if pos.any() else float("nan")


# ---------------------------------------------------------------- one LTM rule (data module step 5b)


def _n(x) -> float:
    """None and NaN read as NaN; a number reads as itself."""
    return float(x) if x is not None and x == x else float("nan")


def last_four(quarters: Sequence) -> list:
    """The last four quarters if they are consecutive (first to last within 290 days); else [] (Section 4.2)."""
    q = sorted(quarters, key=lambda r: r.as_of)[-4:]
    if len(q) < 4 or (q[-1].as_of - q[0].as_of).days > 290:
        return []
    return q


def ltm_total(values: Sequence, allow_three: bool = True) -> float:
    """Sum of four quarterly values (Section 4.1). With `allow_three`, one missing quarter is replaced by scaling the
    other three by 4/3 (earnings fields; the input layer's stated fallback); without it a missing quarter blanks the
    LTM (cash flows). Intuition: an LTM is a year of flow; three quarters of an earnings line estimate it, three
    quarters of a cash line do not."""
    vals = [_n(v) for v in values]
    ok = [v for v in vals if v == v]
    if len(ok) == len(vals):
        return float(sum(ok))
    if allow_three and len(vals) == 4 and len(ok) == 3:
        return float(sum(ok)) * 4.0 / 3.0
    return float("nan")


def ltm_figures(quarters: Sequence) -> dict:
    """LTM flows and quarterly series from point-in-time quarters (methodology 3.2, 4.1, 4.2; quarterly-package-extraction).

    All quarters were available at the decision time (hy.data.view.DataView.financials filters on available_at). LTM = the last
    four consecutive quarters. dWC = (receivables + inventory - payables) now less four quarters earlier; NaN parts
    count as 0 with a flag. Intuition: one table of the numbers every group reads, so no group re-derives them.
    """
    q = sorted(quarters, key=lambda r: r.as_of)
    q4 = last_four(q)
    out = {"quarters": len(q), "years_of_history": round(len(q) / 4, 1)}
    if not q4:
        return out

    def ssum(attr):  # cash flows: a missing quarter blanks the LTM
        return ltm_total([getattr(r, attr) for r in q4], allow_three=False)

    def wc(r):
        return np.nansum([_n(r.receivables), _n(r.inventory)]) - np.nan_to_num(_n(r.payables))
    def esum(attr):  # earnings fields: one missing quarter is scaled from the other three (ltm_total)
        vals = [getattr(r, attr) for r in q4]
        if sum(1 for v in vals if _n(v) == _n(v)) == 3:
            out.setdefault("ltm_scaled", []).append(attr)
        return ltm_total(vals, allow_three=True)
    dwc = float(wc(q[-1]) - wc(q[-5])) if len(q) >= 5 else 0.0
    eb_adj = esum("ebitda_adj_company")
    out.update({
        "revenue": esum("revenue"), "ebitda_rep": esum("ebitda_reported"), "ebitda_adj": eb_adj,
        "addback": float(sum(i.amount for r in q4 for i in r.nonrecurring_items)),  # = -special items (a charge adds back)
        "cfo": ssum("operating_cash_flow"), "capex": ssum("capex_total"), "cash_interest": ssum("cash_interest"),
        "cash_taxes": ssum("cash_taxes"), "depreciation": ssum("depreciation"), "delta_wc": dwc,
        "delta_wc_flag": len(q) < 5, "cash": _n(q4[-1].cash),
        "maint_capex": float(sum(min(_n(r.capex_total), _n(r.depreciation)) if r.depreciation == r.depreciation
                                 else _n(r.capex_total) for r in q4)),
        "revenue_q": [_n(r.revenue) for r in q[-12:]], "ebitda_q": [_n(r.ebitda_adj_company) for r in q[-12:]],
        "ebitda_rep_q": [_n(r.ebitda_reported) for r in q[-12:]],
        "addback_q": [float(sum(i.amount for i in r.nonrecurring_items)) for r in q[-12:]],
        "cfo_q": [_n(r.operating_cash_flow) for r in q[-12:]], "capex_q": [_n(r.capex_total) for r in q[-12:]],
        "cogs_last": _n(q4[-1].cogs), "revenue_last": _n(q4[-1].revenue), "ebitda_last": _n(q4[-1].ebitda_adj_company),
    })
    out["fcf"] = out["cfo"] - out["capex"]
    out["margin_q"] = [e / r if r and r == r and e == e else float("nan") for e, r in zip(out["ebitda_q"], out["revenue_q"])]
    out["conversion_q"] = [(c - k) / e if e and e == e and c == c and k == k else float("nan")
                           for c, k, e in zip(out["cfo_q"], out["capex_q"], out["ebitda_q"])]
    return out


