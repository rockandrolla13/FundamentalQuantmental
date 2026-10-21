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
from typing import Mapping, Sequence

import numpy as np
from scipy.stats import norm
from sklearn.linear_model import LogisticRegression

DAYS_PER_QUARTER = 365.0 / 4.0
LEV_CAP = 50.0  # leverage when LTM EBITDA <= 0; keeps the scenario moments finite
RECOVERY_SHAPES = ("v", "u", "structural", "customer_replace")
FORECAST_SOURCES = ("analyst", "consensus_template", "trend_template")
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
    H = scenario.horizon
    sofr = _as_path(sofr_path, H, "sofr_path")
    lines = list(start.debt_lines)
    bal = np.array([d.face for d in lines], dtype=float)
    coupon = np.array([d.coupon for d in lines], dtype=float)
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

    for i in range(H):
        h = i + 1
        rev = rev_prev * (1.0 + scenario.g[i])
        ebitda = rev * (1.0 - scenario.v[i] - scenario.a[i])

        # Interest on D_{h-1}: no circular link to this quarter's cash (rule 5).
        debt_prev = float(bal.sum() + drawn)
        float_rate = np.array([max(sofr[i], d.floor) + d.spread for d in lines])
        is_float = np.array([d.floating for d in lines], dtype=bool)
        line_rate = np.where(is_float, float_rate, coupon) if lines else np.zeros(0)
        rcf_rate = max(sofr[i], start.revolver_floor) + start.revolver_spread
        undrawn_prev = max(0.0, avail_cap - drawn)
        interest = float((line_rate * bal).sum() / 4.0 + rcf_rate * drawn / 4.0 + start.commitment_fee * undrawn_prev / 4.0)

        tax = start.tax_rate * max(0.0, ebitda - start.da_q - interest)
        wc = working_capital(rev, scenario.v[i], scenario.inventory_days[i], scenario.receivable_days[i], scenario.payable_days[i])
        dwc = wc - wc_prev
        fcf = ebitda - scenario.capex[i] - interest - tax - dwc

        # Scheduled principal: amortisation is paid from cash; a bullet maturity refinances.
        amort = np.minimum(np.array([d.amort for d in lines], dtype=float), bal) if lines else np.zeros(0)
        bal = bal - amort
        due = float(amort.sum())
        for k, d in enumerate(lines):
            if d.maturity_q == h:
                due += bal[k]
                if not d.floating:
                    coupon[k] = d.coupon if d.refi_coupon is None else d.refi_coupon

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
