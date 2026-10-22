"""Forward estimates: scenario engine, macro weights, forward features (methodology Section 5).

The engine rolls revenue, EBITDA, working capital, cash, and each debt
tranche forward one quarter at a time under named scenarios (Section 5.1).
A pooled logistic model of a large EBITDA decline sets the scenario weights
from the macro state (Section 5.2). The weighted paths give the forward
features that the fair spread model reads (Section 5.3).

Conventions: USD millions, quarterly flows, rates as decimals, horizon
index h = 1..H (array position h - 1). Interest accrues on the balance at
the end of quarter h - 1, so the engine needs no iterative solver
(hy-model-standards, rule 5). Inputs are plain numbers; this module reads
no other layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any, Callable, Iterator, Mapping, Sequence

import numpy as np
import pandas as pd
from scipy.stats import binomtest, norm
from sklearn.linear_model import LogisticRegression

if TYPE_CHECKING:  # duck-typed at run time: this module reads no other layer
    from hy.events import MacroPath

DAYS_PER_QUARTER = 365.0 / 4.0
LEV_CAP = 50.0  # leverage when LTM EBITDA <= 0; keeps the scenario moments finite
RECOVERY_SHAPES = ("v", "u", "structural", "customer_replace")
FORECAST_SOURCES = ("analyst", "consensus_template", "trend_template", "management", "consensus")
MAIN_RISKS = (
    "cyclicality",
    "customer_concentration",
    "single_source_supplier",
    "roll_up",
    "discretionary_consumer",
    "none",
)
TM_CORP_RECESSION = (-0.20, -0.10)  # annual revenue change, year 1 then year 2 (pp. 290, 306)

# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------


def _as_path(x: float | Sequence[float] | np.ndarray, horizon: int, name: str) -> np.ndarray:
    arr = np.asarray(x, dtype=float)
    if arr.ndim == 0:
        return np.full(horizon, float(arr))
    if arr.shape != (horizon,):
        raise ValueError(f"{name}: expected {horizon} quarters, got shape {arr.shape}")
    return arr.copy()


@dataclass(frozen=True)
class Scenario:
    """Per-quarter driver vector of one named case (Section 5.1, Figure 10.18, p. 306).

    `g` is quarterly revenue growth, `v` the variable cost ratio (also the
    COGS ratio for working capital), `a` the SG&A ratio, the three `*_days`
    the working capital days, and `capex` the capex in USD millions per
    quarter. Downside cases carry a `recovery_shape` tag (hy-model-standards,
    rule 4). `forecast_source` records where the drivers came from.
    """

    name: str
    g: np.ndarray
    v: np.ndarray
    a: np.ndarray
    inventory_days: np.ndarray
    receivable_days: np.ndarray
    payable_days: np.ndarray
    capex: np.ndarray
    recovery_shape: str | None = None
    forecast_source: str = "analyst"
    main_risk: str | None = None
    gaps: dict[str, Any] | None = None  # analyst gap per driver over consensus (Section 5.4)
    provenance: dict[str, Any] | None = None  # forecast row behind each driver shift (Section 5.4)

    def __post_init__(self) -> None:
        h = int(np.asarray(self.g).size)
        if h < 1:
            raise ValueError(f"{self.name}: empty driver path")
        for f in ("g", "v", "a", "inventory_days", "receivable_days", "payable_days", "capex"):
            object.__setattr__(self, f, _as_path(getattr(self, f), h, f"{self.name}.{f}"))
        if self.recovery_shape is not None and self.recovery_shape not in RECOVERY_SHAPES:
            raise ValueError(f"{self.name}: recovery_shape {self.recovery_shape!r} not in {RECOVERY_SHAPES}")
        if self.forecast_source not in FORECAST_SOURCES:
            raise ValueError(f"{self.name}: forecast_source {self.forecast_source!r} not in {FORECAST_SOURCES}")

    @property
    def horizon(self) -> int:
        return int(self.g.size)


@dataclass(frozen=True)
class DebtLine:
    """One funded tranche for the roll-forward (Section 5.1; hy-model-standards rule 5).

    A fixed line pays `coupon`. A floating line pays max(SOFR, floor) plus
    `spread`. `amort` is the scheduled principal per quarter. At
    `maturity_q` the engine assumes a refinance at `refi_coupon` (default:
    the old coupon), so the balance stays and the maturity counts in wall
    cover (Section 4.2) and in the refinance cost term of Section 9.2.
    """

    name: str
    face: float
    coupon: float = 0.0
    floating: bool = False
    spread: float = 0.0
    floor: float = 0.0
    amort: float = 0.0
    maturity_q: int | None = None
    refi_coupon: float | None = None


@dataclass(frozen=True)
class IssuerStart:
    """Issuer position at decision time t, the h = 0 point of the recursion (Sections 4.2, 5.1).

    `ebitda_hist` and `interest_hist` hold the last four quarters, oldest
    first, so LTM ratios exist from h = 1. The `*_days0` fields and
    `cogs_ratio0` give the opening working capital. `cov_ebitda_uplift` is
    covenant EBITDA divided by adjusted EBITDA (rule 1: keep the bases apart).
    `sweep_share` is the share of surplus cash, after the revolver repays,
    that prepays the floating (prepayable) term lines pro rata; 0 keeps it as cash.
    """

    revenue_q0: float
    ebitda_hist: tuple[float, float, float, float]
    interest_hist: tuple[float, float, float, float]
    cash0: float
    debt_lines: tuple[DebtLine, ...]
    revolver_commitment: float = 0.0
    revolver_drawn0: float = 0.0
    revolver_spread: float = 0.0
    revolver_floor: float = 0.0
    commitment_fee: float = 0.0
    borrowing_base: float = float("inf")
    letters_of_credit: float = 0.0
    inventory_days0: float = 0.0
    receivable_days0: float = 0.0
    payable_days0: float = 0.0
    cogs_ratio0: float = 0.0
    da_q: float = 0.0
    tax_rate: float = 0.25
    min_cash: float = 0.0
    cov_ebitda_uplift: float = 1.0
    sweep_share: float = 0.0

    @property
    def debt0(self) -> float:
        return float(sum(d.face for d in self.debt_lines) + self.revolver_drawn0)

    @property
    def lev0(self) -> float:
        return _leverage(self.debt0, float(sum(self.ebitda_hist)))

    @property
    def liquidity0(self) -> float:
        return liquidity(self.cash0, self.revolver_commitment, self.borrowing_base, self.revolver_drawn0, self.letters_of_credit)


@dataclass(frozen=True)
class ScenarioPath:
    """Engine output for one scenario; every array has one entry per quarter h = 1..H (Section 5.1)."""

    name: str
    revenue: np.ndarray
    ebitda: np.ndarray
    interest: np.ndarray
    tax: np.ndarray
    delta_wc: np.ndarray
    fcf: np.ndarray
    debt: np.ndarray  # total funded debt, revolver included, at face
    revolver_drawn: np.ndarray
    cash: np.ndarray
    liquidity: np.ndarray
    leverage: np.ndarray  # gross: debt / LTM EBITDA
    net_leverage: np.ndarray  # (debt - cash) / LTM EBITDA
    coverage: np.ndarray
    headroom: np.ndarray
    wall_cover: np.ndarray
    effective_rate: np.ndarray  # interest / D_{h-1}, the i_h(m) of Section 5.1
    recovery_shape: str | None = None
    forecast_source: str = "analyst"
    refi_fail_q: int | None = None  # first quarter of a failed refinance (F6.3)
    claims_view: bool = False  # True when a refinance fails: the F5 claims view applies
    refi_coupons: dict[str, dict[str, Any]] | None = None  # per refinanced line: quarter, old and new coupon
    macro_path: str | None = None  # name of the macro path m that drove the run


# ---------------------------------------------------------------------------
# Section 5.1: scenario engine
# ---------------------------------------------------------------------------


def _leverage(debt: float, ltm_ebitda: float) -> float:
    return min(debt / ltm_ebitda, LEV_CAP) if ltm_ebitda > 0 else LEV_CAP


def liquidity(cash: float, commitment: float, borrowing_base: float, drawn: float, letters_of_credit: float) -> float:
    """Static liquidity (Section 4.2): L = Cash + min(Commitment, BorrowingBase) - Drawn - LC.

    Intuition: liquidity is what the issuer can spend today without new capital.
    """
    return float(cash + min(commitment, borrowing_base) - drawn - letters_of_credit)


def working_capital(revenue_q: float, cogs_ratio: float, inv_days: float, rec_days: float, pay_days: float) -> float:
    """Net working capital from days (Section 4.2, Figure 8.6, p. 230; formulas pp. 240-242).

    WC = (rec_days * Rev + inv_days * COGS - pay_days * COGS) / (365 / 4), with COGS = v * Rev.
    Intuition: a longer cash cycle ties more cash to each dollar of quarterly sales.
    """
    cogs = cogs_ratio * revenue_q
    return float((rec_days * revenue_q + (inv_days - pay_days) * cogs) / DAYS_PER_QUARTER)


def covenant_headroom(debt: float, ltm_ebitda: float, max_leverage: float, cov_ebitda_uplift: float = 1.0) -> float:
    """Maintenance covenant headroom (Section 4.6): H = 1 - Lev^cov / Lev^max.

    Lev^cov = D / (uplift * LTM EBITDA_adj), where uplift converts adjusted to covenant EBITDA.
    Intuition: H is the share of covenant EBITDA the issuer can lose before a breach.
    """
    cov_ebitda = cov_ebitda_uplift * ltm_ebitda
    lev_cov = debt / cov_ebitda if cov_ebitda > 0 else np.inf
    return float(1.0 - lev_cov / max_leverage)


# Callback at a maturity: (h, k, line, coupon_k, spread_k) -> (new coupon_k, new spread_k).
MaturityRule = Callable[[int, int, DebtLine, float, float], tuple[float, float]]


def _default_maturity(h: int, k: int, d: DebtLine, coupon_k: float, spread_k: float) -> tuple[float, float]:
    """Section 5.1 default: a fixed line refinances at `refi_coupon` (else its old coupon); a floating line keeps its terms."""
    if d.floating:
        return coupon_k, spread_k
    return (d.coupon if d.refi_coupon is None else d.refi_coupon), spread_k


def _roll_forward(
    start: IssuerStart,
    scenario: Scenario,
    sofr: np.ndarray,
    covenant_max_leverage: float,
    on_maturity: MaturityRule = _default_maturity,
) -> dict[str, np.ndarray]:
    """The one recursion of Section 5.1. `run_scenario` and `run_case_under_path` both call it."""
    H = scenario.horizon
    lines = list(start.debt_lines)
    bal = np.array([d.face for d in lines], dtype=float)
    coupon = np.array([d.coupon for d in lines], dtype=float)
    spread = np.array([d.spread for d in lines], dtype=float)
    avail_cap = min(start.revolver_commitment, start.borrowing_base) - start.letters_of_credit

    rev_prev = start.revenue_q0
    wc_prev = working_capital(rev_prev, start.cogs_ratio0, start.inventory_days0, start.receivable_days0, start.payable_days0)
    cash = start.cash0
    drawn = start.revolver_drawn0
    L0 = start.liquidity0
    ebitda_all = list(start.ebitda_hist)
    interest_all = list(start.interest_hist)

    out = {k: np.zeros(H) for k in (
        "revenue", "ebitda", "interest", "tax", "delta_wc", "fcf", "debt", "revolver_drawn", "cash",
        "liquidity", "leverage", "net_leverage", "coverage", "headroom", "wall_cover", "effective_rate")}
    cum_fcf = 0.0
    cum_due = 0.0
    is_float = np.array([d.floating for d in lines], dtype=bool)

    for i in range(H):
        h = i + 1
        rev = rev_prev * (1.0 + scenario.g[i])
        ebitda = rev * (1.0 - scenario.v[i] - scenario.a[i])

        # Interest on D_{h-1}: no circular link to this quarter's cash (rule 5).
        debt_prev = float(bal.sum() + drawn)
        float_rate = np.array([max(sofr[i], d.floor) for d in lines]) + spread if lines else np.zeros(0)
        line_rate = np.where(is_float, float_rate, coupon) if lines else np.zeros(0)
        rcf_rate = max(sofr[i], start.revolver_floor) + start.revolver_spread
        undrawn_prev = max(0.0, avail_cap - drawn)
        interest = float((line_rate * bal).sum() / 4.0 + rcf_rate * drawn / 4.0 + start.commitment_fee * undrawn_prev / 4.0)

        tax = start.tax_rate * max(0.0, ebitda - start.da_q - interest)
        wc = working_capital(rev, scenario.v[i], scenario.inventory_days[i], scenario.receivable_days[i], scenario.payable_days[i])
        dwc = wc - wc_prev
        fcf = ebitda - scenario.capex[i] - interest - tax - dwc

        # Scheduled principal: amortisation is paid from cash; a bullet maturity refinances (or fails, F6.3).
        amort = np.minimum(np.array([d.amort for d in lines], dtype=float), bal) if lines else np.zeros(0)
        bal = bal - amort
        due = float(amort.sum())
        for k, d in enumerate(lines):
            if d.maturity_q == h:
                due += bal[k]
                coupon[k], spread[k] = on_maturity(h, k, d, float(coupon[k]), float(spread[k]))

        # Cash waterfall: draw on a shortfall, repay the revolver from a surplus.
        cash_pre = cash + fcf - float(amort.sum())
        if cash_pre < start.min_cash:
            draw = min(start.min_cash - cash_pre, max(0.0, avail_cap - drawn))
        else:
            draw = -min(cash_pre - start.min_cash, drawn)
        drawn += draw
        cash = cash_pre + draw

        # Optional sweep of the remaining surplus into the prepayable floating lines.
        surplus = cash - start.min_cash
        if start.sweep_share > 0 and surplus > 0 and lines:
            prepayable = np.where(is_float, bal, 0.0)
            prepay = min(start.sweep_share * surplus, float(prepayable.sum()))
            if prepay > 0:
                bal = bal - prepay * prepayable / prepayable.sum()
                cash -= prepay

        debt = float(bal.sum() + drawn)
        ebitda_all.append(ebitda)
        interest_all.append(interest)
        ltm_e = float(sum(ebitda_all[-4:]))
        ltm_i = float(sum(interest_all[-4:]))
        cum_fcf += fcf
        cum_due += due

        out["revenue"][i] = rev
        out["ebitda"][i] = ebitda
        out["interest"][i] = interest
        out["tax"][i] = tax
        out["delta_wc"][i] = dwc
        out["fcf"][i] = fcf
        out["debt"][i] = debt
        out["revolver_drawn"][i] = drawn
        out["cash"][i] = cash
        out["liquidity"][i] = liquidity(cash, start.revolver_commitment, start.borrowing_base, drawn, start.letters_of_credit)
        out["leverage"][i] = _leverage(debt, ltm_e)
        out["net_leverage"][i] = _leverage(debt - cash, ltm_e)
        out["coverage"][i] = ltm_e / ltm_i if ltm_i > 0 else np.inf
        out["headroom"][i] = covenant_headroom(debt, ltm_e, covenant_max_leverage, start.cov_ebitda_uplift)
        out["wall_cover"][i] = (L0 + cum_fcf) / cum_due if cum_due > 0 else np.inf
        out["effective_rate"][i] = 4.0 * interest / debt_prev if debt_prev > 0 else 0.0

        rev_prev, wc_prev = rev, wc

    return out


def run_scenario(
    start: IssuerStart,
    scenario: Scenario,
    sofr_path: Sequence[float] | np.ndarray,
    covenant_max_leverage: float = np.inf,
) -> ScenarioPath:
    """Roll the three statements forward under one scenario (Section 5.1; Section 9.2 rate channel).

    Rev_h = Rev_{h-1}(1 + g_h); EBITDA_h = Rev_h(1 - v_h - a_h);
    FCF_h = EBITDA_h - Capex_h - Interest_h(D_{h-1}, SOFR_h) - Tax_h - dWC_h;
    each tranche D_{k,h} = D_{k,h-1} - Amort_{k,h}; the revolver draws when
    cash falls below `min_cash` and repays first from any surplus; the rest
    of the surplus prepays floating term lines by `sweep_share` and stays
    in cash otherwise. Hence (D_h - Cash_h) - (D_{h-1} - Cash_{h-1}) = -FCF_h.
    Tax_h = tax_rate * max(0, EBITDA_h - D&A - Interest_h). Floating lines and
    the revolver pay max(SOFR_h, floor) + spread; undrawn revolver pays the
    commitment fee. Outputs per h: liquidity L, leverage D / LTM EBITDA
    (gross, and net of cash),
    coverage LTM EBITDA / LTM interest, headroom H against
    `covenant_max_leverage`, and wall cover (L_0 + sum FCF) / sum principal due.
    Intuition: one recursion makes EBITDA, cash, debt, and liquidity move together.
    """
    sofr = _as_path(sofr_path, scenario.horizon, "sofr_path")
    out = _roll_forward(start, scenario, sofr, covenant_max_leverage)
    return ScenarioPath(name=scenario.name, recovery_shape=scenario.recovery_shape,
                        forecast_source=scenario.forecast_source, **out)


def run_scenarios(
    start: IssuerStart,
    scenarios: Sequence[Scenario],
    sofr_path: Sequence[float] | np.ndarray,
    covenant_max_leverage: float = np.inf,
) -> dict[str, ScenarioPath]:
    """Run every scenario on one macro rate path (Section 5.1). Intuition: same issuer, same rates, different drivers."""
    return {s.name: run_scenario(start, s, sofr_path, covenant_max_leverage) for s in scenarios}


# ---------------------------------------------------------------------------
# Section 5.1: scenario builders
# ---------------------------------------------------------------------------


def annual_to_quarterly(annual_changes: Sequence[float]) -> np.ndarray:
    """Convert annual revenue changes to a smooth quarterly growth path (Section 5.1).

    g_q = (1 + r_year)^(1/4) - 1, repeated for the four quarters of each year.
    Intuition: four equal quarterly steps compound to the annual change.
    """
    r = np.asarray(annual_changes, dtype=float)
    if np.any(r <= -1.0):
        raise ValueError("annual change must exceed -100%")
    return np.repeat((1.0 + r) ** 0.25 - 1.0, 4)


def base_scenario(
    horizon: int,
    g: float | Sequence[float],
    v: float | Sequence[float],
    a: float | Sequence[float],
    inventory_days: float | Sequence[float],
    receivable_days: float | Sequence[float],
    payable_days: float | Sequence[float],
    capex: float | Sequence[float],
    name: str = "base",
    forecast_source: str = "analyst",
) -> Scenario:
    """Base case from analyst drivers; scalars broadcast to every quarter (Section 5.1, base row).

    Intuition: the base case is a coin toss up or down, not conservative by habit (p. 285).
    """
    return Scenario(
        name=name,
        g=_as_path(g, horizon, "g"),
        v=_as_path(v, horizon, "v"),
        a=_as_path(a, horizon, "a"),
        inventory_days=_as_path(inventory_days, horizon, "inventory_days"),
        receivable_days=_as_path(receivable_days, horizon, "receivable_days"),
        payable_days=_as_path(payable_days, horizon, "payable_days"),
        capex=_as_path(capex, horizon, "capex"),
        forecast_source=forecast_source,
    )


def _recovery_quarters(shape: str) -> int:
    return {"v": 2, "u": 4, "structural": 0, "customer_replace": 8}[shape]


def _relative_level(
    horizon: int, shock_g: np.ndarray, shape: str, recovery_stretch: float, replace_share: float
) -> np.ndarray:
    """Revenue level of the downside relative to the base, r_h = Rev^down_h / Rev^base_h."""
    r = np.ones(horizon)
    n_shock = min(horizon, shock_g.size)
    r[:n_shock] = np.cumprod(1.0 + shock_g[:n_shock])
    if n_shock == horizon:
        return r
    r_trough = r[n_shock - 1]
    target = {"v": 1.0, "u": 1.0, "structural": r_trough,
              "customer_replace": r_trough + replace_share * (1.0 - r_trough)}[shape]
    n_rec = max(1, int(round(_recovery_quarters(shape) * recovery_stretch)))
    for j, i in enumerate(range(n_shock, horizon), start=1):
        r[i] = r_trough + (target - r_trough) * min(1.0, j / n_rec)
    return r


def _apply_level(base: Scenario, r: np.ndarray) -> np.ndarray:
    """Quarterly growth that puts the downside level at r_h times the base level."""
    base_level = np.cumprod(1.0 + base.g)
    level = base_level * r
    prev = np.concatenate(([1.0], level[:-1]))
    return level / prev - 1.0


def downside_scenario(
    base: Scenario,
    main_risk: str = "cyclicality",
    recession_annual: Sequence[float] = TM_CORP_RECESSION,
    recovery_shape: str | None = None,
    margin_squeeze: float = 0.0,
    sga_fixed_share: float = 0.5,
    customer_share: float = 0.20,
    replace_share: float = 0.5,
    organic_g: float = 0.0,
    depth: float = 1.0,
    recovery_stretch: float = 1.0,
    payable_days_cut: float = 0.0,
    name: str = "down_moderate",
) -> Scenario:
    """Downside case driven by the issuer's main risk flag (Section 5.1; Section 4.4; hy-model-standards rule 4).

    Revenue level r_h = Rev^down_h / Rev^base_h. `cyclicality`,
    `discretionary_consumer`, and `none` take the recession path
    `recession_annual` (default TM Corp: -20% then -10%, pp. 290, 306) scaled
    by `depth`. `customer_concentration` loses `customer_share` of revenue in
    quarter 1. `single_source_supplier` keeps revenue and raises `v` by
    `margin_squeeze`. `roll_up` sets growth to `organic_g`. SG&A has a fixed
    dollar share, so a_h^down = a_h(s_f / r_h + 1 - s_f): margin falls below
    the trough as revenue falls (p. 386). Payable days fall by `payable_days_cut`.
    Intuition: the downside models what goes wrong for this issuer, not a generic template.
    """
    if main_risk not in MAIN_RISKS:
        raise ValueError(f"main_risk {main_risk!r} not in {MAIN_RISKS}")
    H = base.horizon
    default_shape = {"customer_concentration": "customer_replace", "single_source_supplier": "structural",
                     "roll_up": "structural"}.get(main_risk, "u")
    shape = recovery_shape or default_shape

    if main_risk in ("cyclicality", "discretionary_consumer", "none"):
        rec = np.asarray(recession_annual, dtype=float) * depth
        shock = annual_to_quarterly(rec)
        r = _relative_level(H, shock, shape, recovery_stretch, replace_share)
        g = _apply_level(base, r)
    elif main_risk == "customer_concentration":
        shock = np.array([-customer_share * depth])
        r = _relative_level(H, shock, shape, recovery_stretch, replace_share)
        g = _apply_level(base, r)
    elif main_risk == "single_source_supplier":
        g = base.g.copy()
    else:  # roll_up: no acquisitions, organic growth only
        g = np.full(H, organic_g)
    r = np.cumprod(1.0 + g) / np.cumprod(1.0 + base.g)

    a = base.a * (sga_fixed_share / r + (1.0 - sga_fixed_share))
    v = base.v + margin_squeeze
    return replace(
        base, name=name, g=g, v=v, a=a,
        payable_days=np.maximum(base.payable_days - payable_days_cut, 0.0),
        recovery_shape=shape, main_risk=main_risk,
    )


def severe_scenario(
    base: Scenario,
    main_risk: str = "cyclicality",
    recession_annual: Sequence[float] = TM_CORP_RECESSION,
    recovery_shape: str | None = None,
    depth: float = 1.5,
    recovery_stretch: float = 2.0,
    payable_days_cut: float = 15.0,
    margin_squeeze: float = 0.02,
    **kwargs: float,
) -> Scenario:
    """Severe downside: same risk, deeper and longer, trade credit tightens (Section 5.1, severe row, p. 306).

    Defaults: decline times 1.5, recovery twice as slow, payable days minus 15,
    variable cost ratio plus 2 points. These are judgement defaults with no card yet.
    Intuition: the severe case stacks a revenue fall, a margin squeeze, and a working capital drain.
    """
    return downside_scenario(
        base, main_risk=main_risk, recession_annual=recession_annual, recovery_shape=recovery_shape,
        depth=depth, recovery_stretch=recovery_stretch, payable_days_cut=payable_days_cut,
        margin_squeeze=margin_squeeze, name="down_severe", **kwargs,
    )


def upside_scenario(base: Scenario, moderate: Scenario, name: str = "upside") -> Scenario:
    """Upside mirrored on the moderate downside (Section 5.1, upside row).

    r^up_h = 2 - r^down_h for the revenue level; v^up = 2v - v^down; a^up = 2a - a^down, floored at 0.
    Intuition: absent a named catalyst, the upside is as far above the base as the downside is below.
    """
    r_down = np.cumprod(1.0 + moderate.g) / np.cumprod(1.0 + base.g)
    r_up = np.maximum(2.0 - r_down, 1e-6)
    return replace(
        base, name=name, g=_apply_level(base, r_up),
        v=np.maximum(2.0 * base.v - moderate.v, 0.0),
        a=np.maximum(2.0 * base.a - moderate.a, 0.0),
        payable_days=base.payable_days.copy(),
        recovery_shape=None, main_risk=None,
    )


def build_scenario_set(
    base_drivers: Mapping[str, float | Sequence[float]],
    horizon: int = 8,
    analyst_g: float | Sequence[float] | None = None,
    consensus_g: float | Sequence[float] | None = None,
    trend_g: float | Sequence[float] | None = None,
    main_risk: str = "cyclicality",
    recession_annual: Sequence[float] = TM_CORP_RECESSION,
    recovery_shape: str | None = None,
    growth_shift: float | Sequence[float] = 0.0,
) -> dict[str, Scenario]:
    """Build base, moderate, severe, and upside cases with the fallback order (Section 5.1, last paragraph).

    Order of the growth source: analyst -> consensus with the sector
    recession template -> trend growth with the same template. The result
    carries `forecast_source` so the model can discount mechanical cases.
    `growth_shift` is the Section 5.2 term beta_sector (G_h(m) - G_bar).
    `base_drivers` holds v, a, inventory_days, receivable_days, payable_days, capex.
    Intuition: always produce a full set of cases, and label how mechanical each one is.
    """
    if analyst_g is not None:
        g, source = analyst_g, "analyst"
    elif consensus_g is not None:
        g, source = consensus_g, "consensus_template"
    elif trend_g is not None:
        g, source = trend_g, "trend_template"
    else:
        raise ValueError("no growth source: pass analyst_g, consensus_g, or trend_g")
    g_path = shift_growth(_as_path(g, horizon, "g"), growth_shift)
    base = base_scenario(horizon, g=g_path, forecast_source=source, **base_drivers)  # type: ignore[arg-type]
    mod = downside_scenario(base, main_risk=main_risk, recession_annual=recession_annual, recovery_shape=recovery_shape)
    sev = severe_scenario(base, main_risk=main_risk, recession_annual=recession_annual, recovery_shape=recovery_shape)
    up = upside_scenario(base, mod)
    return {s.name: s for s in (base, mod, sev, up)}


# ---------------------------------------------------------------------------
# Section 5.2: macro conditioning
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DeclineModel:
    """Pooled logistic model P(event | m_t, sector) = sigma(theta_0 + theta' m_t + theta_sector) (Section 5.2).

    `direction` is "down" for EBITDA_{t+4} < (1 - delta) EBITDA_t and "up"
    for EBITDA_{t+4} > (1 + delta) EBITDA_t. Sector effects are one-hot
    columns with the first sector as reference (theta_sector = 0).
    """

    theta0: float
    theta: np.ndarray
    theta_sector: dict[str, float] = field(default_factory=dict)
    direction: str = "down"

    def predict(self, m: Sequence[float] | np.ndarray, sector: str | None = None) -> float:
        """Fitted event probability for one macro vector and sector (Section 5.2). Intuition: a late-cycle m raises p."""
        z = self.theta0 + float(np.dot(self.theta, np.asarray(m, dtype=float)))
        if sector is not None:
            z += self.theta_sector.get(sector, 0.0)
        return float(1.0 / (1.0 + np.exp(-z)))


def decline_labels(ebitda_t: np.ndarray, ebitda_t4: np.ndarray, delta: float | np.ndarray, direction: str = "down") -> np.ndarray:
    """Event label for the Section 5.2 fit: 1{EBITDA_{t+4} < (1 - delta_i) EBITDA_t}, or the mirror for "up".

    Intuition: delta_i is the EBITDA fall in the issuer's own moderate downside, so the label means "the downside happened".
    """
    e0 = np.asarray(ebitda_t, dtype=float)
    e4 = np.asarray(ebitda_t4, dtype=float)
    if direction == "down":
        return (e4 < (1.0 - np.asarray(delta)) * e0).astype(int)
    if direction == "up":
        return (e4 > (1.0 + np.asarray(delta)) * e0).astype(int)
    raise ValueError("direction must be 'down' or 'up'")


def fit_decline_model(
    macro: np.ndarray,
    sectors: Sequence[str],
    labels: np.ndarray,
    direction: str = "down",
    c: float = 1e4,
) -> DeclineModel:
    """Fit the pooled logistic model of Section 5.2 on issuer-quarter rows.

    P(y = 1 | m, sector) = sigma(theta_0 + theta' m + theta_sector); weak L2
    (C = `c`) keeps the fit finite under separation. Rows must hold only
    data available at each row's decision time; the caller enforces this.
    Intuition: one model pooled across issuers learns how the cycle moves the odds of a large miss.
    """
    X_m = np.asarray(macro, dtype=float)
    if X_m.ndim == 1:
        X_m = X_m.reshape(-1, 1)
    if X_m.shape[0] != len(sectors):
        raise ValueError("macro must have shape (n_rows, n_macro) with one row per sector label")
    sec = np.asarray(sectors)
    levels = sorted(set(sec.tolist()))
    dummies = np.column_stack([(sec == s).astype(float) for s in levels[1:]]) if len(levels) > 1 else np.zeros((len(sec), 0))
    X = np.hstack([X_m, dummies])
    model = LogisticRegression(C=c, max_iter=5000)
    model.fit(X, np.asarray(labels, dtype=int))
    k = X_m.shape[1]
    theta_sector = {levels[0]: 0.0}
    theta_sector.update({s: float(model.coef_[0, k + j]) for j, s in enumerate(levels[1:])})
    return DeclineModel(theta0=float(model.intercept_[0]), theta=model.coef_[0, :k].copy(),
                        theta_sector=theta_sector, direction=direction)


def scenario_weights(p_down: float, p_up: float, severe_fraction: float = 0.25) -> dict[str, float]:
    """Scenario weights from the fitted probabilities (Section 5.2).

    w_down_moderate = (1 - f) p_down, w_down_severe = f p_down, w_upside = p_up,
    w_base = 1 - p_down - p_up. If p_down + p_up > 1, both scale down to sum to 1.
    The severe case is a subset of the large-decline event, so the two downside
    weights split p_down rather than add to it. p_up is the mirror event
    EBITDA_{t+4} > (1 + delta) EBITDA_t from a second fit of the same model.
    Intuition: the macro sets the odds of each case; the base case takes what is left.
    """
    if not 0.0 <= severe_fraction <= 1.0:
        raise ValueError("severe_fraction must lie in [0, 1]")
    pd_, pu = float(np.clip(p_down, 0.0, 1.0)), float(np.clip(p_up, 0.0, 1.0))
    tot = pd_ + pu
    if tot > 1.0:
        pd_, pu = pd_ / tot, pu / tot
    w = {
        "base": max(0.0, 1.0 - pd_ - pu),
        "down_moderate": (1.0 - severe_fraction) * pd_,
        "down_severe": severe_fraction * pd_,
        "upside": pu,
    }
    s = sum(w.values())
    return {k: v / s for k, v in w.items()}


def fit_sector_beta(rev_growth: np.ndarray, macro_growth: np.ndarray) -> tuple[float, float]:
    """OLS sensitivity of sector revenue growth to macro growth (Section 5.2; Section 9.2 growth channel).

    g_sector,t = alpha + beta_sector G_t + e_t. Returns (beta_sector, standard error).
    Both series in the same units (for example quarterly growth).
    Intuition: a cyclical sector has a large beta, a defensive one a small beta (HCA, p. 413).
    """
    y = np.asarray(rev_growth, dtype=float)
    x = np.asarray(macro_growth, dtype=float)
    X = np.column_stack([np.ones_like(x), x])
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ coef
    dof = max(1, y.size - 2)
    sigma2 = float(resid @ resid) / dof
    cov = sigma2 * np.linalg.inv(X.T @ X)
    return float(coef[1]), float(np.sqrt(cov[1, 1]))


def growth_shift(beta_sector: float, macro_growth_path: Sequence[float] | np.ndarray, trend_growth: float) -> np.ndarray:
    """Macro shift of the growth driver (Section 5.2; Section 9.2): beta_sector (G_h(m) - G_bar).

    Intuition: a forecast below trend pulls revenue growth down in proportion to the sector beta.
    """
    return beta_sector * (np.asarray(macro_growth_path, dtype=float) - trend_growth)


def shift_growth(g: np.ndarray, shift: float | Sequence[float] | np.ndarray) -> np.ndarray:
    """Apply g_h(m) = g_h + beta_sector (G_h(m) - G_bar) to a growth path (Section 9.2 growth channel).

    Intuition: the scenario stays issuer specific; the macro moves its level.
    """
    return np.asarray(g, dtype=float) + _as_path(shift, np.asarray(g).size, "growth_shift")


# ---------------------------------------------------------------------------
# Section 5.3: forward features
# ---------------------------------------------------------------------------


def breach_probability(
    paths: Mapping[str, ScenarioPath], weights: Mapping[str, float], h: int, bandwidth: float = 0.05
) -> float:
    """Smoothed covenant breach probability (Section 5.3, `p_breach_h`).

    p_breach_h = sum_s w_s Phi(-min_{k<=h} H^s_k / bw).
    Intuition: a case near zero headroom counts as half a breach, so the
    probability moves smoothly with the forecast instead of jumping.
    """
    if bandwidth <= 0:
        raise ValueError("bandwidth must be positive")
    return float(sum(w * norm.cdf(-np.min(paths[s].headroom[:h]) / bandwidth) for s, w in weights.items()))


def _check_weights(paths: Mapping[str, ScenarioPath], weights: Mapping[str, float]) -> None:
    missing = set(weights) - set(paths)
    if missing:
        raise KeyError(f"weights name scenarios with no path: {sorted(missing)}")
    if any(w < 0 for w in weights.values()) or not np.isclose(sum(weights.values()), 1.0):
        raise ValueError("weights must be nonnegative and sum to 1")


def forward_features(
    paths: Mapping[str, ScenarioPath],
    weights: Mapping[str, float],
    lev_t: float,
    debt_t: float,
    horizons: Sequence[int] = (4, 8),
    bandwidth: float = 0.05,
    severe: str = "down_severe",
    base: str = "base",
    consensus_lev_4: float | None = None,
    mgmt_lev_4: float | None = None,
    prior_lev_fwd_4: float | None = None,
) -> dict[str, float | bool | str]:
    """Forward features over the weighted scenarios (Section 5.3).

    E[Lev_{t+h}] = sum_s w_s Lev^s_h; sd = sqrt(sum_s w_s (Lev^s_h - E)^2);
    delev_h = lev_fwd_h - lev_t; lev_peak_down = max_h Lev^severe_h;
    liq_min_down = min_h L^severe_h; p_breach_h from `breach_probability`;
    p_liq_short_h = sum_s w_s 1{min_{k<=h} L^s_k < 0};
    p_refi_h = sum_s w_s 1{min_{k<=h} WallCover^s_k < 1};
    fcf_debt_fwd = E[sum_{h=1..4} FCF_h] / D_t; cov_fwd_h = E[Cov_h];
    rev_lev = lev_fwd_4 - prior vintage; gap_consensus and gap_mgmt =
    base Lev_4 minus the consensus and management Lev_4. A path named
    "consensus" or "management" in `paths` serves when the scalar is absent.
    `downside_is_base` = w_down > 0.5, the book's check (p. 311).
    Intuition: the fair spread model reads the expected path and its tails, not a point forecast.
    """
    _check_weights(paths, weights)
    f: dict[str, float | bool | str] = {}
    for h in horizons:
        lev = np.array([paths[s].leverage[h - 1] for s in weights])
        w = np.array(list(weights.values()))
        mean = float(w @ lev)
        f[f"lev_fwd_{h}"] = mean
        f[f"delev_{h}"] = mean - lev_t
        f[f"lev_fwd_sd_{h}"] = float(np.sqrt(w @ (lev - mean) ** 2))
        f[f"p_breach_{h}"] = breach_probability(paths, weights, h, bandwidth)
        f[f"p_liq_short_{h}"] = float(sum(wt * (np.min(paths[s].liquidity[:h]) < 0) for s, wt in weights.items()))
        f[f"p_refi_{h}"] = float(sum(wt * (np.min(paths[s].wall_cover[:h]) < 1) for s, wt in weights.items()))
        f[f"cov_fwd_{h}"] = float(sum(wt * paths[s].coverage[h - 1] for s, wt in weights.items()))

    if severe in paths:
        f["lev_peak_down"] = float(np.max(paths[severe].leverage))
        f["liq_min_down"] = float(np.min(paths[severe].liquidity))
    f["fcf_debt_fwd"] = float(sum(wt * paths[s].fcf[:4].sum() for s, wt in weights.items()) / debt_t) if debt_t > 0 else np.nan

    lev4 = f.get("lev_fwd_4", np.nan)
    f["rev_lev"] = float(lev4 - prior_lev_fwd_4) if prior_lev_fwd_4 is not None else np.nan
    base_lev4 = float(paths[base].leverage[3]) if base in paths else np.nan
    if consensus_lev_4 is None and "consensus" in paths:
        consensus_lev_4 = float(paths["consensus"].leverage[3])
    if mgmt_lev_4 is None and "management" in paths:
        mgmt_lev_4 = float(paths["management"].leverage[3])
    f["gap_consensus"] = base_lev4 - consensus_lev_4 if consensus_lev_4 is not None else np.nan
    f["gap_mgmt"] = base_lev4 - mgmt_lev_4 if mgmt_lev_4 is not None else np.nan

    w_down = float(sum(wt for s, wt in weights.items() if s.startswith("down")))
    f["w_down"] = w_down
    f["downside_is_base"] = w_down > 0.5
    f["forecast_source"] = paths[base].forecast_source if base in paths else ""
    return f


# ===========================================================================
# Forecast-linked scenarios, Section 5.4
# ===========================================================================
#
# This section links the scenario engine to the forecast registry and to the
# macro paths of Section 9.2. Every case runs under every macro path m. The
# path sets the policy rate (floating interest, F6.4), the refinance coupon
# (F6.3), and the growth driver shift (Section 9.2 growth channel). The case
# weights w_s(m) come from the Section 5.2 logistic once it is calibrated,
# else from the F6 table. Outputs are per path plus a probability-weighted row.
#
# Stated assumptions (each needs a decision page before production use):
#   REFI_TENOR_YEARS = 5      tenor of the Treasury that prices a refinance
#   REFI_ACCESS_THRESHOLD = 0.5   F6.3 cut-off on p_refi_access
#   distressed_coupon_add = 0.05  coupon step-up while a failed maturity stays outstanding
#   floating refinance: the new margin over the policy rate equals s_fair(m)
#   path arrays shorter than the case horizon hold their last value
#   SEVERE_TROUGH_BUFFER = 0.01   severe margin sits 1 point below the historic trough
#   SEVERE_EXTRA_SQUEEZE = 0.02   severe variable cost add when no trough margin is given
#   CONTRACTED_DEFAULT = True     A2 and A5 take the 0.7 downside multiplier unless told otherwise
#   promotion (F6.6) applies once per path; it does not iterate

PHASES = ("expansion", "late_cycle", "downturn", "repair", "recovery")
ARCHETYPES = ("A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8")
MODIFIERS = ("M1", "M2", "M3")
WEIGHTED_CASES = ("base", "down_moderate", "down_severe", "upside")
LOSS_OF_CONTRACT = "down_moderate_loss_contract"

# Framework F6, macro phase weight table: base, moderate, severe, upside.
F6_WEIGHT_TABLE: dict[str, dict[str, float]] = {
    "expansion": {"base": 0.60, "down_moderate": 0.15, "down_severe": 0.05, "upside": 0.20},
    "late_cycle": {"base": 0.50, "down_moderate": 0.25, "down_severe": 0.10, "upside": 0.15},
    "downturn": {"base": 0.35, "down_moderate": 0.35, "down_severe": 0.20, "upside": 0.10},
    "repair": {"base": 0.50, "down_moderate": 0.25, "down_severe": 0.10, "upside": 0.15},
    "recovery": {"base": 0.55, "down_moderate": 0.15, "down_severe": 0.05, "upside": 0.25},
}
CYCLICAL_DOWN_MULT = 1.3  # A3, A4
CONTRACTED_DOWN_MULT = 0.7  # A2, A5 with contracted revenue

# F2 downside driver mapped onto the engine's main-risk switch (template can override).
ARCHETYPE_MAIN_RISK = {
    "A1": "discretionary_consumer",  # same-store sales decline
    "A2": "none",  # reimbursement change: a revenue step set by the template
    "A3": "cyclicality",  # price deck at the 10th percentile, as an annual revenue path
    "A4": "cyclicality",  # own peak-to-trough revenue in the last recession
    "A5": "customer_concentration",  # contract roll-off: a one-step loss, then re-let
    "A6": "none",  # worst net retention year, as an annual revenue path
    "A7": "customer_concentration",  # asset-specific shock: a one-step loss
}

REFI_TENOR_YEARS = 5.0
REFI_ACCESS_THRESHOLD = 0.5
SEVERE_DEPTH = 1.5
SEVERE_EXTRA_RECOVERY_Q = 4
SEVERE_PAYABLE_CUT = 10.0
SEVERE_TROUGH_BUFFER = 0.01
SEVERE_EXTRA_SQUEEZE = 0.02
DEFAULT_MACRO_FIELDS = ("index_spread", "default_rate", "pmi")
DEFAULT_DRIVER_LINKS = {"g": "gdp_growth"}


def _norm_phase(phase: str) -> str:
    p = phase.strip().lower().replace(" ", "_").replace("-", "_")
    if p not in F6_WEIGHT_TABLE:
        raise ValueError(f"phase {phase!r} not in {PHASES}")
    return p


def _check_archetype(archetype: str, modifiers: Sequence[str]) -> None:
    if archetype not in ARCHETYPES:
        raise ValueError(f"archetype {archetype!r} not in {ARCHETYPES}")
    if archetype == "A8":
        raise ValueError("A8 financials are out of scope (framework F2); route to a separate rulebook")
    bad = set(modifiers) - set(MODIFIERS)
    if bad:
        raise ValueError(f"modifiers {sorted(bad)} not in {MODIFIERS}")


def _path_array(path: "MacroPath", field_name: str, horizon: int) -> np.ndarray:
    """Read one path variable as an H-quarter array; a short path holds its last value (stated assumption)."""
    if hasattr(path, field_name):
        a = np.asarray(getattr(path, field_name), dtype=float)
    else:
        extra = getattr(path, "extra", {}) or {}
        if field_name not in extra:
            raise KeyError(f"path {getattr(path, 'name', '?')!r} has no variable {field_name!r}")
        a = np.asarray(extra[field_name], dtype=float)
    a = np.atleast_1d(a)
    if a.size >= horizon:
        return a[:horizon].copy()
    return np.concatenate([a, np.full(horizon - a.size, a[-1])])


def _path_provenance(path: "MacroPath", variable: str, forecast_row: Any) -> dict[str, Any]:
    """Source and vintage of the forecast behind a path variable.

    Order: the explicit `forecast_row` (a mapping, a ForecastRow, or the hy.macro
    `PathSet.sources[variable]` tuple (source, vintage, available_at, method)); then `path.provenance[variable]` or `path.extra["provenance"]`
    when the path builder stored one; else a logged assumption with the path name and no vintage.
    """
    if forecast_row is not None:
        if isinstance(forecast_row, tuple):  # hy.macro PathSet.sources: (source, vintage, available_at, method)
            keys = ("source", "vintage", "available_at", "method")
            row = dict(zip(keys, forecast_row))
        elif isinstance(forecast_row, Mapping):
            row = dict(forecast_row)
        else:
            row = dict(vars(forecast_row))
        return {**{k: row.get(k) for k in ("source", "vintage", "available_at", "method") if k in row},
                "source": row.get("source"), "vintage": row.get("vintage"), "basis": "forecast_row"}
    for holder in (getattr(path, "provenance", None), (getattr(path, "extra", {}) or {}).get("provenance")):
        if isinstance(holder, Mapping):
            rec = holder.get(variable, holder)
            if isinstance(rec, Mapping) and "source" in rec:
                return {"source": rec.get("source"), "vintage": rec.get("vintage"), "basis": "path_builder"}
    return {"source": f"macro_path:{getattr(path, 'name', '?')}", "vintage": None, "basis": "logged_assumption"}


# ---------------------------------------------------------------------------
# 5.4 (1) Driver linkage
# ---------------------------------------------------------------------------


def driver_shift(beta_sector: float, forecast_path: Sequence[float] | np.ndarray, trend: float) -> np.ndarray:
    """Shift of one driver per quarter: delta_h(m) = beta_sector (G_h(m) - G_bar) (Sections 5.2, 9.2).

    `forecast_path` holds G_h(m), the forecast variable under path m, in the units in which
    `beta_sector` was fitted (see `fit_sector_beta`). `trend` is G_bar. Pass as G_bar the forecast
    that the base drivers already embed (for a consensus base, the consensus path), so that path
    equal to that forecast leaves the base unchanged.
    Intuition: a path below the embedded forecast pulls the driver down in proportion to the sector beta.
    """
    return growth_shift(beta_sector, forecast_path, trend)


def link_drivers(
    base_drivers: Scenario | Mapping[str, Any],
    path: "MacroPath",
    betas: Mapping[str, float],
    trend: float | Mapping[str, float],
    links: Mapping[str, str] | None = None,
    forecast_rows: Mapping[str, Any] | None = None,
) -> Scenario | dict[str, np.ndarray]:
    """Shift each linked driver by its path forecast: x_h(m) = x_h + beta_x (G^x_h(m) - G_bar^x) (Section 9.2).

    `betas` maps a driver ("g", "v", ...) to its sensitivity; `links` maps the driver to the path
    variable (default: "g" -> "gdp_growth"). `trend` is G_bar, one number or one per driver.
    With a Scenario input the result is a Scenario whose `provenance[driver]` records the path,
    variable, beta, trend, and the forecast row (source, vintage). `forecast_rows` is keyed by
    driver or by path variable; `PathSet.sources` from hy.macro passes as is. With a mapping input the
    result is a dict of shifted per-quarter arrays and a "provenance" key.
    Intuition: the case stays issuer specific; the macro path moves its level.
    """
    links = {**DEFAULT_DRIVER_LINKS, **(links or {})}
    forecast_rows = forecast_rows or {}
    is_scen = isinstance(base_drivers, Scenario)
    if is_scen:
        H = base_drivers.horizon
        drivers = {k: getattr(base_drivers, k) for k in betas}
    else:
        drivers = dict(base_drivers)
        H = next((np.asarray(v).size for v in drivers.values() if np.ndim(v) == 1), 1)
    shifted: dict[str, np.ndarray] = {}
    prov: dict[str, Any] = {}
    for drv, beta in betas.items():
        if drv not in links:
            raise KeyError(f"driver {drv!r} has no linked path variable; pass links")
        var = links[drv]
        t = trend[drv] if isinstance(trend, Mapping) else trend
        G = _path_array(path, var, H)
        shifted[drv] = shift_growth(_as_path(drivers[drv], H, drv), driver_shift(beta, G, float(t)))
        prov[drv] = {"path": getattr(path, "name", None), "variable": var, "beta": float(beta), "trend": float(t),
                     **_path_provenance(path, var, forecast_rows.get(drv, forecast_rows.get(var)))}
    if is_scen:
        old = dict(base_drivers.provenance or {})
        return replace(base_drivers, **shifted, provenance={**old, **prov})
    return {**{k: np.asarray(v, dtype=float) for k, v in drivers.items()}, **shifted, "provenance": prov}


def _to_scenario(x: Scenario | Mapping[str, Any], name: str, source: str, horizon: int,
                 fill: Scenario | None = None) -> Scenario:
    """Turn a driver mapping into a Scenario; drivers it omits come from `fill` and are recorded."""
    if isinstance(x, Scenario):
        return replace(x, name=name, forecast_source=source)
    keys = ("g", "v", "a", "inventory_days", "receivable_days", "payable_days", "capex")
    given = {k: x[k] for k in keys if k in x}
    filled = [k for k in keys if k not in given]
    if filled and fill is None:
        raise ValueError(f"{name}: drivers {filled} missing and no case to fill them from")
    for k in filled:
        given[k] = getattr(fill, k)
    prov = dict(x.get("provenance", {})) if isinstance(x.get("provenance", {}), Mapping) else {}
    if filled:
        prov["filled_from"] = {"case": fill.name, "drivers": filled}  # type: ignore[union-attr]
    return Scenario(name=name, forecast_source=source, provenance=prov or None,
                    **{k: _as_path(v, horizon, k) for k, v in given.items()})


def base_from_consensus(
    consensus: Scenario | Mapping[str, Any],
    gaps: Mapping[str, float | Sequence[float]],
    horizon: int = 8,
    name: str = "base",
) -> Scenario:
    """Base case = consensus drivers + the analyst's stated gap per driver (Section 5.4; F6 base row).

    x^base_h = x^cons_h + gap_x. `gaps` is stored on the Scenario so the edge over the market
    view is auditable and `gap_consensus` traces to a stated number, not to a hidden edit.
    Intuition: the analyst states only where and by how much the view differs from the market.
    """
    cons = _to_scenario(consensus, "consensus", "consensus", horizon)
    unknown = set(gaps) - {"g", "v", "a", "inventory_days", "receivable_days", "payable_days", "capex"}
    if unknown:
        raise KeyError(f"gaps name unknown drivers: {sorted(unknown)}")
    shifted = {k: getattr(cons, k) + _as_path(v, cons.horizon, k) for k, v in gaps.items()}
    prov = {**(cons.provenance or {}), "base": "consensus + analyst gap"}
    return replace(cons, name=name, forecast_source="analyst", gaps=dict(gaps), provenance=prov, **shifted)


# ---------------------------------------------------------------------------
# 5.4 (2) F6 case set
# ---------------------------------------------------------------------------


def coin_toss_test(analyst_record: Sequence[bool] | Sequence[tuple[float, float]], alpha: float = 0.05,
                   min_n: int = 8) -> dict[str, Any]:
    """F6 base row: actuals beat the analyst base about half the time.

    `analyst_record` holds booleans (actual above base) or (actual, base) pairs. The test is a
    two-sided binomial test of share = 0.5. Fewer than `min_n` records give "insufficient".
    Intuition: a base case that actuals beat most of the time is conservative by habit.
    """
    rec = list(analyst_record)
    above = [bool(r[0] > r[1]) if isinstance(r, (tuple, list)) else bool(r) for r in rec]
    n, k = len(above), int(sum(above))
    if n < min_n:
        return {"n": n, "share_above": k / n if n else float("nan"), "p_value": float("nan"), "result": "insufficient"}
    p = float(binomtest(k, n, 0.5).pvalue)
    return {"n": n, "share_above": k / n, "p_value": p, "result": "pass" if p >= alpha else "fail"}


def _severe_stretch(shape: str) -> float:
    n = _recovery_quarters(shape)
    return (n + SEVERE_EXTRA_RECOVERY_Q) / n if n > 0 else 1.0


def f6_cases(
    base: Scenario,
    archetype: str,
    modifiers: Sequence[str],
    recession_template: Mapping[str, Any],
    guidance: Scenario | Mapping[str, Any] | None = None,
    consensus: Scenario | Mapping[str, Any] | None = None,
    analyst_record: Sequence[Any] | None = None,
    catalyst: Scenario | None = None,
) -> dict[str, Scenario]:
    """Build the F6 case set: management, consensus, base, down_moderate, down_severe, upside.

    Management: guidance as given; absent when `guidance` is None (do not invent, p. 285).
    Consensus: the sell-side median drivers. Base: `base` (see `base_from_consensus`); the
    coin-toss test on `analyst_record` is stored in `base.provenance["coin_toss"]`.

    Moderate downside: the archetype's main risk at the severity of the last cycle, from
    `recession_template` keys: `annual` (annual revenue changes, for example the A4 peak-to-trough
    path or the A3 10th-percentile deck), `shock` (one-step revenue loss share, A5 and A7),
    `recovery_shape`, `main_risk` (overrides the archetype default), `margin_squeeze`,
    `payable_days_cut`, `sga_fixed_share`, `replace_share`, `trough_margin` (historic trough
    EBITDA margin), and `contract_share` (M3 only).

    Severe downside: decline x 1.5, recovery one year longer (n_rec + 4 quarters), payable days
    minus 10 more than the moderate, and the EBITDA margin min_h (1 - v_h - a_h) below the
    historic trough by 1 point; with no trough given, v rises 2 points over the moderate.

    Upside: the mirror of the moderate (`upside_scenario`) unless a `catalyst` case is passed.
    M3 adds `down_moderate_loss_contract`: the moderate case with a further permanent loss of
    `contract_share` of revenue in quarter 1; `f6_weights` splits the moderate weight over the two.
    Intuition: each archetype fails in its own way; the template states how, with numbers.
    """
    _check_archetype(archetype, modifiers)
    t = dict(recession_template)
    risk = t.get("main_risk", ARCHETYPE_MAIN_RISK[archetype])
    annual = tuple(t.get("annual", TM_CORP_RECESSION))
    kw: dict[str, Any] = {k: t[k] for k in ("sga_fixed_share", "replace_share") if k in t}
    if "shock" in t:
        kw["customer_share"] = float(t["shock"])
    squeeze = float(t.get("margin_squeeze", 0.0))
    pay_cut = float(t.get("payable_days_cut", 0.0))

    cases: dict[str, Scenario] = {}
    if guidance is not None:
        cases["management"] = _to_scenario(guidance, "management", "management", base.horizon, fill=base)
    if consensus is not None:
        cases["consensus"] = _to_scenario(consensus, "consensus", "consensus", base.horizon, fill=base)
    if analyst_record is not None:
        base = replace(base, provenance={**(base.provenance or {}), "coin_toss": coin_toss_test(analyst_record)})
    cases["base"] = replace(base, name="base")

    mod = downside_scenario(base, main_risk=risk, recession_annual=annual, recovery_shape=t.get("recovery_shape"),
                            margin_squeeze=squeeze, payable_days_cut=pay_cut, name="down_moderate", **kw)
    mod = replace(mod, provenance={**(base.provenance or {}), "rule": f"F6 moderate, {archetype}",
                                   "template": dict(t)})
    cases["down_moderate"] = mod
    if "M3" in modifiers:
        if "contract_share" not in t:
            raise ValueError("M3 needs recession_template['contract_share']; do not invent the contract size")
        loc = downside_scenario(mod, main_risk="customer_concentration", customer_share=float(t["contract_share"]),
                                recovery_shape="structural", name=LOSS_OF_CONTRACT)
        cases[LOSS_OF_CONTRACT] = replace(loc, provenance={**(mod.provenance or {}), "rule": "F6 M3 loss of contract"})

    shape = mod.recovery_shape or "u"
    sev = downside_scenario(base, main_risk=risk, recession_annual=annual, recovery_shape=shape,
                            margin_squeeze=squeeze, payable_days_cut=pay_cut + SEVERE_PAYABLE_CUT,
                            depth=SEVERE_DEPTH, recovery_stretch=_severe_stretch(shape), name="down_severe", **kw)
    margin = 1.0 - sev.v - sev.a
    if "trough_margin" in t:
        target = float(t["trough_margin"]) - SEVERE_TROUGH_BUFFER
        extra = max(0.0, float(margin.min()) - target)
        rule = f"min margin {target:.4f} = trough - {SEVERE_TROUGH_BUFFER}"
    else:
        extra = SEVERE_EXTRA_SQUEEZE
        rule = f"no trough margin given: v + {SEVERE_EXTRA_SQUEEZE}"
    sev = replace(sev, v=sev.v + extra, provenance={**(base.provenance or {}), "rule": f"F6 severe, {archetype}",
                                                     "margin_rule": rule})
    cases["down_severe"] = sev

    if catalyst is not None:
        cases["upside"] = replace(catalyst, name="upside", provenance={**(catalyst.provenance or {}), "rule": "catalyst"})
    else:
        up = upside_scenario(base, mod)
        cases["upside"] = replace(up, provenance={**(base.provenance or {}), "rule": "mirror of moderate"})
    return cases


# ---------------------------------------------------------------------------
# 5.4 (3) One case under one macro path
# ---------------------------------------------------------------------------


def run_case_under_path(
    start: IssuerStart,
    scenario: Scenario,
    path: "MacroPath",
    *,
    s_fair_fn: Callable[[Any, int], float],
    p_refi_access_fn: Callable[[Any, int], float],
    forward_treasury_fn: Callable[[Any, int, float], float],
    covenant_max_leverage: float = np.inf,
    distressed_coupon_add: float = 0.05,
    refi_tenor_years: float = REFI_TENOR_YEARS,
) -> ScenarioPath:
    """Run one case under macro path m (F6.3, F6.4; Section 9.2 rate channel).

    Recursion (Section 5.1), per quarter h:
      Rev_h = Rev_{h-1} (1 + g_h(m)); EBITDA_h = Rev_h (1 - v_h - a_h).
      Intuition: revenue compounds; costs scale with it.
      Interest_h = sum_k r_{k,h} D_{k,h-1} / 4 + r^rcf_h Drawn_{h-1} / 4 + fee Undrawn_{h-1} / 4,
      with r_{k,h} = max(policy_h(m), floor_k) + spread_k for floating lines and c_k for fixed lines.
      Intuition: floating debt reprices each quarter with the path; fixed debt waits for a refinance.
      FCF_h = EBITDA_h - Capex_h - Interest_h - Tax_h - dWC_h.
      Intuition: cash left after operations, investment, the lenders, and the state.
      D_h = D_{h-1} - Amort_h + Draw_h - Prepay_h; Cash_h = Cash_{h-1} + FCF_h - Amort_h + Draw_h - Prepay_h.
      Intuition: a shortfall is borrowed on the revolver; a surplus repays it first.
      L_h = Cash_h + min(Commitment, BorrowingBase) - Drawn_h - LC; Headroom_h = 1 - Lev^cov_h / Lev^max.
      Intuition: liquidity and headroom fall out of the same cash and debt.
    Refinance at a maturity quarter tau <= H (F6.3):
      if p_refi_access(m, tau) > 0.5: c_new = y_T(m, tau, tenor) + s_fair(m, tau), so from tau + 1
      dCashInt = M_tau (y_T(m) + s_fair(m) - c_old) / 4 per quarter.
      Intuition: the maturity rolls at the market price of the path, not at the old coupon.
      else: `refi_fail_q` = tau, `claims_view` = True (F5 engaged), the amount stays outstanding at
      c_old + `distressed_coupon_add`, and the case continues as a distressed exchange path.
    A floating line that refinances keeps floating with margin s_fair(m, tau) (stated assumption).
    `DebtLine.refi_coupon` is ignored here: the path sets the coupon.
    """
    H = scenario.horizon
    policy = _path_array(path, "policy_rate", H)
    refi: dict[str, dict[str, Any]] = {}
    fail: list[int] = []

    def on_maturity(h: int, k: int, d: DebtLine, coupon_k: float, spread_k: float) -> tuple[float, float]:
        p = float(p_refi_access_fn(path, h))
        old = spread_k if d.floating else coupon_k
        if p > REFI_ACCESS_THRESHOLD:
            s = float(s_fair_fn(path, h))
            y = float(forward_treasury_fn(path, h, refi_tenor_years))
            new = s if d.floating else y + s
            rec = {"q": h, "status": "refinanced", "p_refi_access": p, "treasury": y, "s_fair": s}
        else:
            new = old + distressed_coupon_add
            fail.append(h)
            rec = {"q": h, "status": "failed", "p_refi_access": p, "treasury": np.nan, "s_fair": np.nan}
        rec.update(old=old, new=new, floating=d.floating)
        refi[d.name] = rec
        return (coupon_k, new) if d.floating else (new, spread_k)

    out = _roll_forward(start, scenario, policy, covenant_max_leverage, on_maturity)
    return ScenarioPath(
        name=scenario.name, recovery_shape=scenario.recovery_shape, forecast_source=scenario.forecast_source,
        refi_fail_q=min(fail) if fail else None, claims_view=bool(fail), refi_coupons=refi or None,
        macro_path=getattr(path, "name", None), **out,
    )


# ---------------------------------------------------------------------------
# 5.4 (4) Grid: every case under every path
# ---------------------------------------------------------------------------


def run_grid(
    start: IssuerStart,
    cases: Mapping[str, Scenario],
    paths: Sequence["MacroPath"],
    *,
    betas: Mapping[str, float] | None = None,
    trend: float | Mapping[str, float] | None = None,
    links: Mapping[str, str] | None = None,
    forecast_rows: Mapping[str, Any] | None = None,
    **fns: Any,
) -> dict[tuple[str, str], ScenarioPath]:
    """Run every case s under every path m: grid[(s, m)] = ScenarioPath (Section 5.4; F6 x Section 9.2).

    With `betas`, each case's drivers shift by path first (`link_drivers`), so
    g^s_h(m) = g^s_h + beta (G_h(m) - G_bar). `fns` pass to `run_case_under_path`.
    Intuition: the grid holds the issuer's whole forward distribution before any weight is applied.
    """
    if betas and trend is None:
        raise ValueError("betas need a trend G_bar")
    grid: dict[tuple[str, str], ScenarioPath] = {}
    for m in paths:
        for name, sc in cases.items():
            sc_m = link_drivers(sc, m, betas, trend, links, forecast_rows) if betas else sc  # type: ignore[arg-type]
            grid[(name, m.name)] = run_case_under_path(start, sc_m, m, **fns)  # type: ignore[arg-type]
    return grid


# ---------------------------------------------------------------------------
# 5.4 (5) Case weights per path
# ---------------------------------------------------------------------------


@dataclass(frozen=True, eq=False)
class CaseWeights(Mapping[str, float]):
    """Case weights w_s(m) for one path, with their audit trail (F6 weight table, Section 5.2, F6.6).

    Behaves as a read-only mapping case -> weight, so `forward_features` accepts it.
    `source` is "f6_table" or "logistic_5_2". `relabel` maps an F6 role to the case that fills it
    after an F6.6 promotion.
    """

    w: dict[str, float]
    source: str
    phase: str | None = None
    archetype: str | None = None
    down_multiplier: float = 1.0
    m3_prob: float | None = None
    promoted: bool = False
    relabel: dict[str, str] | None = None

    def __getitem__(self, k: str) -> float:
        return self.w[k]

    def __iter__(self) -> Iterator[str]:
        return iter(self.w)

    def __len__(self) -> int:
        return len(self.w)

    @property
    def w_down(self) -> float:
        """Combined downside weight: sum of the weights of every case named down*."""
        return float(sum(v for k, v in self.w.items() if k.startswith("down")))


def _m3_split(w: dict[str, float], m3_prob: float | None) -> dict[str, float]:
    """M3: the moderate weight w_mod splits into w_mod (1 - q) and w_mod q for the loss-of-contract branch."""
    if m3_prob is None:
        return w
    q = float(m3_prob)
    if not 0.0 <= q <= 1.0:
        raise ValueError("m3_prob must lie in [0, 1]")
    out = dict(w)
    out[LOSS_OF_CONTRACT] = w["down_moderate"] * q
    out["down_moderate"] = w["down_moderate"] * (1.0 - q)
    return out


def f6_weights(
    phase: str,
    archetype: str,
    modifiers: Sequence[str] = (),
    m3_prob: float | None = None,
    contracted_revenue: bool = True,
) -> CaseWeights:
    """F6 table weights with the archetype adjustment and the M3 branch.

    w_s = table[phase][s]; for A3 and A4 both downside weights x 1.3; for A2 and A5 with
    contracted revenue x 0.7; then w_s <- w_s / sum_s w_s. With M3, the moderate weight splits
    by the analyst's stated probability q (`m3_prob`, required with M3).
    Intuition: a commodity or cyclical issuer is more exposed to the same phase; a contracted one less.
    """
    _check_archetype(archetype, modifiers)
    ph = _norm_phase(phase)
    w = dict(F6_WEIGHT_TABLE[ph])
    mult = 1.0
    if archetype in ("A3", "A4"):
        mult = CYCLICAL_DOWN_MULT
    elif archetype in ("A2", "A5") and contracted_revenue:
        mult = CONTRACTED_DOWN_MULT
    w["down_moderate"] *= mult
    w["down_severe"] *= mult
    tot = sum(w.values())
    w = {k: v / tot for k, v in w.items()}
    if "M3" in modifiers and m3_prob is None:
        raise ValueError("M3 needs m3_prob, the analyst's stated loss-of-contract probability")
    w = _m3_split(w, m3_prob if "M3" in modifiers else None)
    return CaseWeights(w=w, source="f6_table", phase=ph, archetype=archetype, down_multiplier=mult,
                       m3_prob=m3_prob if "M3" in modifiers else None)


def apply_f66(weights: Mapping[str, float], threshold: float = 0.5) -> tuple[CaseWeights, bool]:
    """F6.6: if w_down > 0.5, the moderate downside becomes the base and the cases shift down one step.

    Role shift: base <- down_moderate, down_moderate <- down_severe, down_severe <- down_severe
    (no deeper case exists), upside <- base. As weights on the existing case paths:
    w'(base case) = w_up, w'(moderate) = w_base, w'(severe) = w_mod + w_sev, w'(upside case) = 0.
    The M3 branch keeps its share q of the moderate group. The sum stays 1. The rule fires once.
    Intuition: when the downside is the likely outcome, it is the base case (p. 311).
    """
    cw = weights if isinstance(weights, CaseWeights) else CaseWeights(w=dict(weights), source="given")
    w_down = cw.w_down
    if cw.promoted or w_down <= threshold:
        return cw, False
    w = cw.w
    w_mod_group = w.get("down_moderate", 0.0) + w.get(LOSS_OF_CONTRACT, 0.0)
    q = w.get(LOSS_OF_CONTRACT, 0.0) / w_mod_group if w_mod_group > 0 else 0.0
    new = {
        "base": w.get("upside", 0.0),
        "down_moderate": w.get("base", 0.0) * (1.0 - q),
        "down_severe": w_mod_group + w.get("down_severe", 0.0),
        "upside": 0.0,
    }
    if LOSS_OF_CONTRACT in w:
        new[LOSS_OF_CONTRACT] = w.get("base", 0.0) * q
    relabel = {"base": "down_moderate", "down_moderate": "down_severe", "down_severe": "down_severe", "upside": "base"}
    return replace(cw, w=new, promoted=True, relabel=relabel), True


def _macro_vector(path: "MacroPath", fields: Sequence[str], window: int) -> np.ndarray:
    return np.array([float(np.mean(_path_array(path, f, window))) for f in fields])


def case_weights_by_path(
    paths: Sequence["MacroPath"],
    phase: str,
    archetype: str,
    modifiers: Sequence[str] = (),
    decline_model: DeclineModel | None = None,
    *,
    up_model: DeclineModel | None = None,
    sector: str | None = None,
    macro_fields: Sequence[str] = DEFAULT_MACRO_FIELDS,
    window: int = 4,
    severe_fraction: float = 0.25,
    m3_prob: float | None = None,
    contracted_revenue: bool = True,
    promote: bool = True,
) -> dict[str, CaseWeights]:
    """Case weights w_s(m) for each macro path (Section 5.2; F6 weight table; F6.6).

    With a calibrated `decline_model`: p_down(m) = sigma(theta_0 + theta' x(m) + theta_sector), where
    x(m) is the mean of `macro_fields` over the first `window` quarters of path m (the window of
    the four-quarter decline event); p_up(m) from `up_model`, else the F6 table upside weight.
    The weights then follow `scenario_weights` (severe share f = 0.25). Without a model, every path
    takes the F6 table with the archetype adjustment. M3 splits the moderate weight in both cases.
    With `promote`, F6.6 applies per path. `CaseWeights.source` records which rule set the weights.
    Intuition: the same issuer is more likely in its downside on a recession path than on a soft landing.
    """
    table = f6_weights(phase, archetype, modifiers, m3_prob, contracted_revenue)
    out: dict[str, CaseWeights] = {}
    for m in paths:
        if decline_model is not None:
            x = _macro_vector(m, macro_fields, window)
            if x.size != np.asarray(decline_model.theta).size:
                raise ValueError(f"decline_model expects {np.asarray(decline_model.theta).size} macro inputs, "
                                 f"macro_fields gives {x.size}")
            p_down = decline_model.predict(x, sector)
            p_up = up_model.predict(x, sector) if up_model is not None else F6_WEIGHT_TABLE[table.phase]["upside"]  # type: ignore[index]
            w = _m3_split(scenario_weights(p_down, p_up, severe_fraction), table.m3_prob)
            cw = CaseWeights(w=w, source="logistic_5_2" if up_model is not None else "logistic_5_2+f6_upside",
                             phase=table.phase, archetype=archetype, m3_prob=table.m3_prob)
        else:
            cw = table
        if promote:
            cw, _ = apply_f66(cw)
        out[m.name] = cw
    return out


# ---------------------------------------------------------------------------
# 5.4 (6) Outputs per path and across paths
# ---------------------------------------------------------------------------


def _p_path_dict(p_path: Mapping[str, float] | Sequence["MacroPath"]) -> dict[str, float]:
    p = dict(p_path) if isinstance(p_path, Mapping) else {m.name: float(m.prob) for m in p_path}
    if any(v < 0 for v in p.values()) or not np.isclose(sum(p.values()), 1.0):
        raise ValueError("path probabilities must be nonnegative and sum to 1")
    return p


def lev_mixture(
    grid: Mapping[tuple[str, str], ScenarioPath],
    p_path: Mapping[str, float] | Sequence["MacroPath"],
    w_by_path: Mapping[str, Mapping[str, float]],
    h: int = 4,
) -> tuple[np.ndarray, np.ndarray]:
    """Atoms and masses of the forward leverage mixture: Lev^s_h(m) with mass p(m) w_s(m) (Section 5.4).

    Intuition: the forecast distribution is a finite mixture over paths and cases.
    """
    p = _p_path_dict(p_path)
    vals, mass = [], []
    for m, pm in p.items():
        for s, ws in w_by_path[m].items():
            vals.append(float(grid[(s, m)].leverage[h - 1]))
            mass.append(pm * ws)
    return np.array(vals), np.array(mass)


def mixture_pit(x: float, atoms: np.ndarray, masses: np.ndarray, noise_sd: float = 0.0) -> float:
    """Probability integral transform of a realised value against the mixture: F(x) = sum_j q_j Phi((x - a_j) / sd).

    With `noise_sd` = 0 the mixture is discrete and F is a step function.
    Intuition: if the model is right, F(realised) is uniform on [0, 1] over many decisions.
    """
    if noise_sd <= 0:
        return float(masses[atoms <= x].sum())
    return float(masses @ norm.cdf((x - atoms) / noise_sd))


def forward_features_by_path(
    grid: Mapping[tuple[str, str], ScenarioPath],
    p_path: Mapping[str, float] | Sequence["MacroPath"],
    w_by_path: Mapping[str, Mapping[str, float]],
    start: IssuerStart,
    *,
    pd_fn: Callable[[dict[str, Any]], float] | None = None,
    s_fair_fn: Callable[[dict[str, Any]], float] | None = None,
    oas: float | None = None,
    bandwidth: float = 0.05,
) -> pd.DataFrame:
    """Forward features per macro path and the probability-weighted row (Sections 5.3, 5.4; F6.8).

    Mixture over paths m and cases s:
      E_t[Lev_{t+h}] = sum_m sum_s p(m) w_s(m) Lev^s_h(m).
      Intuition: the expected leverage averages every case on every path by its probability.
      Var_t[Lev_{t+h}] = sum_m sum_s p(m) w_s(m) (Lev^s_h(m) - E_t[Lev_{t+h}])^2
                       = sum_m p(m) [Var_m + (E_m - E_t)^2]   (law of total variance).
      Intuition: dispersion comes from the cases inside a path and from the paths themselves.
    Per path m the columns follow `forward_features` with w_s(m). The "weighted" row takes
    p(m)-weighted means of the per-path values (probabilities, coverage, lev_peak_down, liq_min_down,
    refi_fail_share, base and reference case leverage), `lev_fwd_sd` from the total variance,
    pd_12m = sum_m p(m) PD(m), and s_fair = sum_m p(m) s_fair(m).
    refi_fail_share(m) = sum_s w_s(m) 1{refi_fail_q^s(m) is set}. resid_bp = (oas - s_fair) x 1e4.
    `pd_fn` and `s_fair_fn` take the feature dict of one row. The recursion and the refinance
    coupon are stated in `run_case_under_path`.
    """
    p = _p_path_dict(p_path)
    rows = []
    for m, pm in p.items():
        w = w_by_path[m]
        paths_m = {s: path for (s, mm), path in grid.items() if mm == m}
        f = forward_features(paths_m, w, start.lev0, start.debt0, horizons=(4, 8), bandwidth=bandwidth)
        row: dict[str, Any] = {
            "macro_path": m, "p_path": pm,
            "lev_fwd_4": f["lev_fwd_4"], "lev_fwd_8": f["lev_fwd_8"],
            "lev_fwd_sd": f["lev_fwd_sd_4"], "lev_fwd_sd_8": f["lev_fwd_sd_8"],
            "lev_peak_down": f.get("lev_peak_down", np.nan), "liq_min_down": f.get("liq_min_down", np.nan),
            "p_breach_4": f["p_breach_4"], "p_liq_short_8": f["p_liq_short_8"], "p_refi_4": f["p_refi_4"],
            "cov_fwd_4": f["cov_fwd_4"],
            "refi_fail_share": float(sum(wt for s, wt in w.items() if paths_m[s].refi_fail_q is not None)),
            "w_down": float(sum(wt for s, wt in w.items() if s.startswith("down"))),
            "base_lev_4": float(paths_m["base"].leverage[3]) if "base" in paths_m else np.nan,
            "consensus_lev_4": float(paths_m["consensus"].leverage[3]) if "consensus" in paths_m else np.nan,
            "mgmt_lev_4": float(paths_m["management"].leverage[3]) if "management" in paths_m else np.nan,
            "weight_source": getattr(w, "source", "given"), "promoted": bool(getattr(w, "promoted", False)),
        }
        row["pd_12m"] = float(pd_fn(row)) if pd_fn is not None else np.nan
        row["s_fair"] = float(s_fair_fn(row)) if s_fair_fn is not None else np.nan
        rows.append(row)

    df = pd.DataFrame(rows)
    pv = df["p_path"].to_numpy()
    wrow: dict[str, Any] = {"macro_path": "weighted", "p_path": float(pv.sum())}
    mean_cols = ("lev_fwd_4", "lev_fwd_8", "lev_peak_down", "liq_min_down", "p_breach_4", "p_liq_short_8",
                 "p_refi_4", "cov_fwd_4", "refi_fail_share", "w_down", "base_lev_4", "consensus_lev_4",
                 "mgmt_lev_4", "pd_12m", "s_fair")
    for c in mean_cols:
        wrow[c] = float(pv @ df[c].to_numpy(dtype=float))
    for sd_col, mu_col in (("lev_fwd_sd", "lev_fwd_4"), ("lev_fwd_sd_8", "lev_fwd_8")):
        within = pv @ df[sd_col].to_numpy(dtype=float) ** 2
        between = pv @ (df[mu_col].to_numpy(dtype=float) - wrow[mu_col]) ** 2
        wrow[sd_col] = float(np.sqrt(within + between))
    srcs = sorted(set(df["weight_source"]))
    wrow["weight_source"] = srcs[0] if len(srcs) == 1 else "mixed:" + ",".join(srcs)
    wrow["promoted"] = bool(df["promoted"].any())
    df = pd.concat([df, pd.DataFrame([wrow])], ignore_index=True)
    df["resid_bp"] = (oas - df["s_fair"]) * 1e4 if oas is not None else np.nan
    return df


# ---------------------------------------------------------------------------
# 5.4 (7) Revisions between vintages, forward part
# ---------------------------------------------------------------------------


def _weighted(features: Any) -> Mapping[str, Any]:
    if isinstance(features, Mapping):
        return features
    hit = features[features["macro_path"] == "weighted"]
    if hit.empty:
        raise ValueError("features frame has no 'weighted' row")
    return hit.iloc[0].to_dict()


def forward_revisions(
    new_features: Any,
    old_features: Any,
    consensus_lev_4: float | None = None,
    mgmt_lev_4: float | None = None,
) -> dict[str, Any]:
    """Forward revisions between two vintages (Section 5.3 `rev_lev`, `gap_consensus`, `gap_mgmt`; signals S3, S7).

    rev_lev = lev_fwd_4^weighted(v) - lev_fwd_4^weighted(v - 1).
    Intuition: a revision is news; the signal trades the change, not the level.
    gap_consensus = base Lev_4 - consensus Lev_4; gap_mgmt = base Lev_4 - management Lev_4, each the
    p(m)-weighted base and reference case of the new vintage unless a scalar is passed.
    Intuition: the gap is the analyst's edge over the market view and the optimism haircut on management.
    dp_path[m] = p_new(m) - p_old(m) for the paths present in both vintages.
    """
    new_w, old_w = _weighted(new_features), _weighted(old_features)
    base4 = float(new_w.get("base_lev_4", np.nan))
    cons = consensus_lev_4 if consensus_lev_4 is not None else new_w.get("consensus_lev_4", np.nan)
    mgmt = mgmt_lev_4 if mgmt_lev_4 is not None else new_w.get("mgmt_lev_4", np.nan)
    dp: dict[str, float] = {}
    if not isinstance(new_features, Mapping) and not isinstance(old_features, Mapping):
        pn = new_features[new_features["macro_path"] != "weighted"].set_index("macro_path")["p_path"]
        po = old_features[old_features["macro_path"] != "weighted"].set_index("macro_path")["p_path"]
        dp = {k: float(pn[k] - po[k]) for k in pn.index if k in po.index}
    return {
        "rev_lev": float(new_w["lev_fwd_4"]) - float(old_w["lev_fwd_4"]),
        "gap_consensus": base4 - float(cons) if cons is not None else np.nan,
        "gap_mgmt": base4 - float(mgmt) if mgmt is not None else np.nan,
        "dp_path": dp,
    }


# ---------------------------------------------------------------------------
# Funding gap and refinancing shock (RV PDF E75 to E77; mapping Top 10 items 3 and 4)
# ---------------------------------------------------------------------------


def funding_gap(cash0: float, drawable: float, min_cash: float, fcf_q: Sequence[float],
                maturities_q: Sequence[float], other_uses_q: Sequence[float] | None = None,
                debt0: float | None = None) -> dict[str, Any]:
    """Funding gap by quarter with no new financing (methodology 4.2, 5.3; framework F4; RV PDF E75, E76).

    G_h = C_0 + A_drawable - C_min + sum_{u<=h} FCF_u - M_h - U_h, with M_h the debt due through quarter h and
    U_h other committed uses. FundingNeed_h = max(0, -G_h); MaturityShare_h = M_h / D_0.
    Returns the path G, its minimum, the first quarter with G_h < 0 (None when the gap never opens), the largest
    need, and the maturity share at the horizon.

    Intuition: if the market shuts, this is how long cash, the revolver and the business carry the debt that falls due.
    """
    fcf = np.asarray(list(fcf_q), dtype=float)
    mat = np.asarray(list(maturities_q), dtype=float)
    if fcf.shape != mat.shape:
        raise ValueError("fcf_q and maturities_q need the same length")
    uses = np.zeros_like(fcf) if other_uses_q is None else np.asarray(list(other_uses_q), dtype=float)
    g = cash0 + drawable - min_cash + np.cumsum(fcf) - np.cumsum(mat) - np.cumsum(uses)
    neg = np.nonzero(g < 0)[0]
    m_h = float(mat.sum())
    return {"G": g, "funding_gap_min": float(g.min()) if g.size else float("nan"),
            "first_gap_q": int(neg[0] + 1) if neg.size else None,
            "funding_need_max": float(max(0.0, -g.min())) if g.size else 0.0,
            "maturity_share": m_h / debt0 if debt0 else float("nan")}


def refinancing_shock(refi_amounts: Sequence[float], c_old: Sequence[float] | float, c_new: Sequence[float],
                      ebitda: float, cash_interest: float, capex: float, fcf: float, debt: float) -> dict[str, float]:
    """Refinancing interest shock and its effect (methodology 5.4 `dCashInt_h(m)`; RV PDF E77; Cases A and E).

    dI = sum_k D_refi,k (c_new,k - c_old,k). Reports dI / E, cash coverage after refinancing E / (I_c + dI),
    after-capex coverage (E - K) / (I_c + dI), FCF - dI, and (FCF - dI) / D.

    Intuition: leverage can stay flat while the new coupon eats the free cash flow; the signal is that effect.
    """
    d = np.asarray(list(refi_amounts), dtype=float)
    new = np.asarray(list(c_new), dtype=float)
    old = np.full_like(d, float(c_old)) if np.ndim(c_old) == 0 else np.asarray(list(c_old), dtype=float)
    if not d.shape == new.shape == old.shape:
        raise ValueError("refi_amounts, c_old and c_new need the same length")
    di = float((d * (new - old)).sum())
    ic = cash_interest + di

    def div(a, b):
        return a / b if b and b == b and b > 0 else float("nan")
    return {"delta_I": di, "delta_I_to_E": div(di, ebitda), "cash_cov_after": div(ebitda, ic),
            "after_capex_cov_after": div(ebitda - capex, ic), "fcf_after": fcf - di,
            "fcf_after_to_debt": div(fcf - di, debt), "refi_amount": float(d.sum())}
