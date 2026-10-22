"""Event layer: taxonomy, macro paths, the yield split, position P&L, risk measures, limits (methodology Section 9).

The fair spread model is an input, not an import: callers pass
`fair_log_spread: Callable[[np.ndarray], np.ndarray]` that maps a feature
matrix (n, k) to log fair spreads (n,). Re-evaluating it under the outcome
features gives the event sensitivity (Section 9.2).

Units: yields and spreads are decimals (0.01 is 100 bp). Prices are per 100
face. Notionals and dollar risk are in currency units. `dpnl` is in price
points per 100 face.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

import numpy as np
import pandas as pd
from scipy.special import expit

N_QUARTERS = 8


# ---------------------------------------------------------------------------
# 9.1 Event taxonomy
# ---------------------------------------------------------------------------


class EventType(str, Enum):
    """The fourteen event types of Section 9.1."""

    EARNINGS = "earnings"
    COVENANT_TEST = "covenant_test"
    MATURITY_REFI = "maturity_refi"
    CALL_TENDER = "call_tender"
    RATING_REVIEW = "rating_review"
    INDEX_REBALANCE = "index_rebalance"
    MNA_LBO = "mna_lbo"
    SPONSOR_RECAP = "sponsor_recap"
    LME = "lme"
    ASSET_SALE = "asset_sale"
    LITIGATION = "litigation"
    MACRO_RELEASE = "macro_release"
    SECTOR_SHOCK = "sector_shock"
    BANKRUPTCY = "bankruptcy"


OUTCOMES: dict[EventType, tuple[str, ...]] = {
    EventType.EARNINGS: ("beat", "in_line", "miss"),
    EventType.COVENANT_TEST: ("pass", "waiver", "acceleration"),
    EventType.MATURITY_REFI: ("refinanced", "extended", "distressed_exchange", "default"),
    EventType.CALL_TENDER: ("called", "not_called"),
    EventType.RATING_REVIEW: ("upgrade", "affirm", "downgrade"),
    EventType.INDEX_REBALANCE: ("in", "out"),
    EventType.MNA_LBO: ("deal", "no_deal"),
    EventType.SPONSOR_RECAP: ("done", "not_done"),
    EventType.LME: ("drop_down", "uptier", "exchange", "none"),
    EventType.ASSET_SALE: ("sold", "not_sold"),
    EventType.LITIGATION: ("adverse", "neutral"),
    EventType.MACRO_RELEASE: ("path",),
    EventType.SECTOR_SHOCK: ("path",),
    EventType.BANKRUPTCY: ("filed",),
}

DEFAULT_OUTCOMES: frozenset[str] = frozenset({"default", "filed", "acceleration"})


# ---------------------------------------------------------------------------
# 9.2 Macro paths
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MacroPath:
    """One named macro path with a probability and quarterly arrays (Section 9.2).

    Arrays hold eight quarters. Yields, rates, growth, and spreads are decimals.
    """

    name: str
    prob: float
    y2: np.ndarray
    y10: np.ndarray
    policy_rate: np.ndarray
    gdp_growth: np.ndarray
    pmi: np.ndarray
    index_spread: np.ndarray
    default_rate: np.ndarray
    extra: dict[str, np.ndarray] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.prob <= 1.0:
            raise ValueError(f"{self.name}: prob {self.prob} outside [0, 1]")
        for f in ("y2", "y10", "policy_rate", "gdp_growth", "pmi", "index_spread", "default_rate"):
            a = np.asarray(getattr(self, f), dtype=float)
            if a.ndim != 1 or a.size == 0:
                raise ValueError(f"{self.name}.{f}: need a non-empty quarterly array")
            object.__setattr__(self, f, a)


def validate_paths(paths: Sequence[MacroPath], tol: float = 1e-6) -> None:
    """Check sum_m p(m) = 1 and equal path lengths (Section 9.2: four to six paths, each with a probability).

    Intuition: the event expectation is a probability-weighted sum, so the weights must be a distribution.
    """
    tot = sum(p.prob for p in paths)
    if abs(tot - 1.0) > tol:
        raise ValueError(f"path probabilities sum to {tot}, not 1")
    if len({p.y10.size for p in paths}) > 1:
        raise ValueError("paths have different horizons")


# ---------------------------------------------------------------------------
# 9.2 Yield split and systematic spread response
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class YieldSplit:
    """dy = a + b_g * dG + b_p * dP + e, fitted by OLS (Section 9.2, the Treasury forecast needs a split)."""

    intercept: float
    b_growth: float
    b_policy: float


def fit_yield_split(dy: np.ndarray, d_growth_fcst: np.ndarray, d_policy_exp: np.ndarray) -> YieldSplit:
    """Two-factor OLS of the yield change on growth forecast and expected policy rate changes (Section 9.2).

    Intuition: a yield rise from better growth and one from a tighter Fed look the same on the screen but not to credit.
    """
    X = np.column_stack([np.ones(len(dy)), d_growth_fcst, d_policy_exp])
    coef, *_ = np.linalg.lstsq(X, np.asarray(dy, dtype=float), rcond=None)
    return YieldSplit(float(coef[0]), float(coef[1]), float(coef[2]))


def split_yield_change(
    split: YieldSplit, dy: np.ndarray | float, d_growth_fcst: np.ndarray | float
) -> tuple[np.ndarray, np.ndarray]:
    """dy^growth = b_g * dG; dy^policy = dy - dy^growth (Section 9.2, dy(m) = dy^growth(m) + dy^policy(m)).

    The policy part absorbs the intercept and the residual, so the two parts add to dy exactly.
    Intuition: whatever growth does not explain is treated as discount-rate (policy) news, the side that widens spreads.
    """
    dy = np.asarray(dy, dtype=float)
    g = split.b_growth * np.asarray(d_growth_fcst, dtype=float)
    return g, dy - g


def fit_spread_betas(ds: np.ndarray, dy_growth: np.ndarray, dy_policy: np.ndarray) -> tuple[float, float]:
    """OLS of ds^sys on dy^growth and dy^policy, returns (beta_g, beta_p) (Section 9.2; Section 11, Spread split row).

    Intuition: re-estimate each quarter and check the signs hold, beta_g < 0 and beta_p > 0.
    """
    X = np.column_stack([np.ones(len(ds)), dy_growth, dy_policy])
    coef, *_ = np.linalg.lstsq(X, np.asarray(ds, dtype=float), rcond=None)
    return float(coef[1]), float(coef[2])


def systematic_spread_change(
    dy_growth: np.ndarray | float, dy_policy: np.ndarray | float, beta_g: float, beta_p: float
) -> np.ndarray:
    """ds^sys(m) = beta_g * dy^growth(m) + beta_p * dy^policy(m), beta_g < 0 < beta_p (Section 9.2).

    Raises ValueError when the signs fail. Intuition: growth-driven yield rises tighten credit; policy-driven rises widen it.
    """
    if not (beta_g < 0 < beta_p):
        raise ValueError(f"sign check failed: beta_g={beta_g} must be < 0 and beta_p={beta_p} must be > 0")
    return beta_g * np.asarray(dy_growth, dtype=float) + beta_p * np.asarray(dy_policy, dtype=float)


def effective_rate_duration(mod_duration: np.ndarray | float, spread_duration: np.ndarray | float, beta: float) -> np.ndarray:
    """D_eff = D + D^s * beta (Section 9.2; Section 9.3, rdv01_eff).

    Intuition: shorter than modified duration in a growth-driven move (beta < 0), longer in a policy-driven one.
    """
    return np.asarray(mod_duration, dtype=float) + np.asarray(spread_duration, dtype=float) * beta


# ---------------------------------------------------------------------------
# 9.2 Rate channel
# ---------------------------------------------------------------------------


def rate_price_change(price: np.ndarray | float, mod_duration: np.ndarray | float, convexity: np.ndarray | float, dy: np.ndarray | float) -> np.ndarray:
    """dP = P * (-D * dy + 1/2 * C * dy^2), in price points (Section 9.2, rate channel).

    Intuition: about 1% of price per year of duration per 1% of yield (p. 116), bent by convexity.
    """
    dy = np.asarray(dy, dtype=float)
    return np.asarray(price, dtype=float) * (-np.asarray(mod_duration, dtype=float) * dy + 0.5 * np.asarray(convexity, dtype=float) * dy * dy)


def cash_interest_change(
    total_debt: float,
    phi_float: float,
    d_sofr_h: float,
    maturities: np.ndarray,
    y_treasury: np.ndarray,
    s_fair: np.ndarray | float,
    c_old: np.ndarray,
    h: int,
) -> float:
    """dCashInt_h(m) = phi_float * D * dSOFR_h(m) + sum_{tau <= h} M_tau * [y_T(m) + s_hat(m) - c_old] (Section 9.2).

    Annual interest run-rate change at quarter h. `maturities`, `y_treasury`, `c_old` are per quarter.
    Intuition: rates reach a bond issuer through its floating debt now and through each refinanced maturity later (p. 99).
    """
    m = np.asarray(maturities, dtype=float)[:h]
    yt = np.asarray(y_treasury, dtype=float)[:h]
    s = np.broadcast_to(np.asarray(s_fair, dtype=float), np.asarray(maturities).shape)[:h]
    c = np.asarray(c_old, dtype=float)[:h]
    return float(phi_float * total_debt * d_sofr_h + np.sum(m * (yt + s - c)))


# ---------------------------------------------------------------------------
# 9.2 Position P&L under an outcome and a path
# ---------------------------------------------------------------------------


def fair_spread_change(fair_log_spread: Callable[[np.ndarray], np.ndarray], x_base: np.ndarray, x_outcome: np.ndarray) -> np.ndarray:
    """ds_idio = s_hat(x(o, m)) - s_hat(x) by re-evaluating the fair spread model (Section 9.2).

    Intuition: the model that prices the bond today also prices it after the outcome; the gap is the event sensitivity.
    """
    xb = np.atleast_2d(np.asarray(x_base, dtype=float))
    xo = np.atleast_2d(np.asarray(x_outcome, dtype=float))
    return np.exp(fair_log_spread(xo)) - np.exp(fair_log_spread(xb))


def position_pnl(
    price: float,
    mod_duration: float,
    spread_duration: float,
    dy: float,
    ds_sys: float,
    ds_idio: float,
    carry_h: float,
    default: bool = False,
    recovery_adj: float = 0.0,
) -> float:
    """dP(o,m) = -D*dy*P - D^s*[ds^sys + ds_idio]*P + carry_h - 1{default}(P - 100 R^adj) (Section 9.2).

    In price points. Duration terms scale by price because D is a percentage sensitivity.
    On default the rate and spread terms are dropped: the price converges to recovery (p. 530),
    so keeping them would double count the loss. `carry_h` is in price points over the horizon.
    Intuition: the bond moves with rates, the market spread, and its own fair spread, unless it defaults.
    """
    if default:
        return float(carry_h - (price - 100.0 * recovery_adj))
    return float(-mod_duration * dy * price - spread_duration * (ds_sys + ds_idio) * price + carry_h)


def outcome_probabilities(
    event_type: EventType,
    *,
    w_down: float | None = None,
    p_breach: float | None = None,
    p_refi: float | None = None,
    refi_access: float | None = None,
    beat_share: float = 0.5,
    waiver_share: float = 0.95,
    extend_share: float = 0.5,
    default_share: float = 0.5,
) -> dict[str, float]:
    """P(o | e, m) by the Section 9.2 rules.

    Earnings: miss = w_down(m); the rest splits beat and in line by `beat_share`.
    Covenant test: breach = p_breach(m), split waiver and acceleration by `waiver_share`; acceleration is rare (p. 355).
    Maturity: failed refi = p_refi(m) * (1 - refi_access(m)); failure splits extension against
    distressed exchange or default by `extend_share`, the distressed part by `default_share`.
    The share parameters are placeholders until Section 11 calibrates P(o | e, m).
    Intuition: the macro path sets the downside weight, and the downside weight sets how likely a bad outcome is.
    """
    if event_type is EventType.EARNINGS:
        miss = float(w_down)
        rest = 1.0 - miss
        return {"beat": rest * beat_share, "in_line": rest * (1.0 - beat_share), "miss": miss}
    if event_type is EventType.COVENANT_TEST:
        b = float(p_breach)
        return {"pass": 1.0 - b, "waiver": b * waiver_share, "acceleration": b * (1.0 - waiver_share)}
    if event_type is EventType.MATURITY_REFI:
        fail = float(p_refi) * (1.0 - float(refi_access))
        distressed = fail * (1.0 - extend_share)
        return {
            "refinanced": 1.0 - fail,
            "extended": fail * extend_share,
            "distressed_exchange": distressed * (1.0 - default_share),
            "default": distressed * default_share,
        }
    raise NotImplementedError(f"no rule in Section 9.2 for {event_type}; pass P(o | e, m) directly")


def refi_access(kappa: np.ndarray | float, primary_open: np.ndarray | float, kappa_ref: float = 2.0, slope: float = 2.0) -> np.ndarray:
    """refi_access(m) = primary_open(m) * expit(-slope * (kappa(m) - kappa_ref)) (Section 9.2, access falls when kappa is high).

    `primary_open` is 1 when the new issue market is open on the path, else 0, or a share in [0, 1].
    kappa_ref and slope are placeholders. Intuition: when risk is dear and the window is shut, nobody refinances.
    """
    return np.asarray(primary_open, dtype=float) * expit(-slope * (np.asarray(kappa, dtype=float) - kappa_ref))


def expected_event_pnl(pnl: np.ndarray, p_path: np.ndarray, p_outcome_given_path: np.ndarray) -> float:
    """E[dP | e] = sum_m p(m) sum_o P(o | e, m) dP(o, m) (Section 9.2). Grids are (n_paths, n_outcomes).

    Intuition: weight each cell of the outcome by path grid by how likely it is.
    """
    w = np.asarray(p_path, dtype=float)[:, None] * np.asarray(p_outcome_given_path, dtype=float)
    return float(np.sum(w * np.asarray(pnl, dtype=float)))


def event_var(pnl: np.ndarray, p_path: np.ndarray, p_outcome_given_path: np.ndarray, alpha: float = 0.05) -> float:
    """EventVaR_alpha = Quantile_alpha{dP(o, m)} under the weights p(m) P(o | e, m) (Section 9.2).

    Inverted-CDF quantile: the smallest dP with cumulative weight >= alpha.
    Equal weights reproduce `np.quantile(..., method="inverted_cdf")`.
    Intuition: the loss that the event exceeds with probability alpha, across outcomes and paths.
    """
    x = np.asarray(pnl, dtype=float).ravel()
    w = (np.asarray(p_path, dtype=float)[:, None] * np.asarray(p_outcome_given_path, dtype=float)).ravel()
    keep = w > 0
    x, w = x[keep], w[keep] / w[keep].sum()
    order = np.argsort(x, kind="stable")
    cdf = np.cumsum(w[order])
    idx = int(np.searchsorted(cdf, alpha - 1e-12, side="left"))
    return float(x[order][min(idx, x.size - 1)])


@dataclass(frozen=True)
class EventGrid:
    """Spread change (bp) and P&L (points) on the (path, outcome) grid, plus audit feature deltas."""

    outcomes: tuple[str, ...]
    paths: tuple[str, ...]
    dspread_bp: np.ndarray
    dpnl: np.ndarray
    features_delta: list[list[np.ndarray]]


def event_pnl_grid(
    *,
    price: float,
    mod_duration: float,
    spread_duration: float,
    x_base: np.ndarray,
    x_outcome: Callable[[str, MacroPath], np.ndarray],
    outcomes: Sequence[str],
    paths: Sequence[MacroPath],
    dy: Mapping[str, float],
    ds_sys: Mapping[str, float],
    carry_h: float,
    recovery_adj: Mapping[str, float],
    fair_log_spread: Callable[[np.ndarray], np.ndarray],
    default_outcomes: frozenset[str] = DEFAULT_OUTCOMES,
) -> EventGrid:
    """dP(o, m) and ds(o, m) for one position and one event over every outcome and path (Section 9.2).

    `x_outcome(o, m)` returns the feature vector the outcome implies under the path.
    `dy`, `ds_sys`, `recovery_adj` are keyed by path name.
    Intuition: one fair spread model, re-evaluated once per cell, fills the event matrix.
    """
    xb = np.asarray(x_base, dtype=float)
    nm, no = len(paths), len(outcomes)
    dsp = np.zeros((nm, no))
    pnl = np.zeros((nm, no))
    fd: list[list[np.ndarray]] = []
    for i, m in enumerate(paths):
        row = []
        for j, o in enumerate(outcomes):
            xo = np.asarray(x_outcome(o, m), dtype=float)
            ds_i = float(fair_spread_change(fair_log_spread, xb, xo)[0])
            dflt = o in default_outcomes
            dsp[i, j] = (ds_sys[m.name] + ds_i) * 1e4
            pnl[i, j] = position_pnl(
                price, mod_duration, spread_duration, dy[m.name], ds_sys[m.name], ds_i, carry_h, dflt, recovery_adj[m.name]
            )
            row.append(xo - xb)
        fd.append(row)
    return EventGrid(tuple(outcomes), tuple(p.name for p in paths), dsp, pnl, fd)


# ---------------------------------------------------------------------------
# 9.3 Position risk measures
# ---------------------------------------------------------------------------


def sdv01(spread_duration: np.ndarray | float, price: np.ndarray | float, notional: np.ndarray | float) -> np.ndarray:
    """sdv01 = spread_duration * (price / 100) * notional / 10,000 (Section 9.3).

    Price is per 100, so it enters as a fraction. Intuition: dollars lost per 1 bp of spread widening.
    """
    return np.asarray(spread_duration, dtype=float) * np.asarray(price, dtype=float) / 100.0 * np.asarray(notional, dtype=float) / 1e4


def rdv01_eff(
    mod_duration: np.ndarray | float, spread_duration: np.ndarray | float, beta: float, price: np.ndarray | float, notional: np.ndarray | float
) -> np.ndarray:
    """rdv01_eff = (mod_duration + spread_duration * beta) * (price / 100) * notional / 10,000 (Section 9.3).

    Intuition: the rate hedge must net out the part of a yield move that the spread gives back.
    """
    return effective_rate_duration(mod_duration, spread_duration, beta) * np.asarray(price, dtype=float) / 100.0 * np.asarray(notional, dtype=float) / 1e4


def jtd(notional: np.ndarray | float, price: np.ndarray | float, recovery_adj: np.ndarray | float) -> np.ndarray:
    """jtd = notional * (price - 100 * recovery_k_adj) / 100 (Section 9.3).

    Intuition: on default the bond drops from its price to its model recovery.
    """
    return np.asarray(notional, dtype=float) * (np.asarray(price, dtype=float) - 100.0 * np.asarray(recovery_adj, dtype=float)) / 100.0


def el_h(pd_h: np.ndarray | float, lgd_adj: np.ndarray | float, notional: np.ndarray | float) -> np.ndarray:
    """el_h = pd_h * lgd_k_adj * notional (Section 9.3; Section 7.1).

    Intuition: risk is the chance of default times the severity (p. 119).
    """
    return np.asarray(pd_h, dtype=float) * np.asarray(lgd_adj, dtype=float) * np.asarray(notional, dtype=float)


def exit_cost(bid_ask_bp: np.ndarray | float, sdv01_value: np.ndarray | float) -> np.ndarray:
    """exit_cost = bid_ask_bp * sdv01 (Section 9.3). Intuition: the bid-ask in bp times dollars per bp."""
    return np.asarray(bid_ask_bp, dtype=float) * np.asarray(sdv01_value, dtype=float)


def exit_days(notional: np.ndarray | float, adv: np.ndarray | float, k: float) -> np.ndarray:
    """exit_days = notional / (k * ADV) (Section 9.3). Intuition: trade at most k times daily volume per day."""
    return np.asarray(notional, dtype=float) / (k * np.asarray(adv, dtype=float))


def jtd_neutral_ratio(price_k: float, recovery_k: float, price_j: float, recovery_j: float) -> float:
    """N_j / N_k = (P_k - 100 R_k) / (P_j - 100 R_j) (Section 9.3, pair sizing by jump-to-default).

    Intuition: size the short so that a default costs the long what it pays the short.
    """
    return (price_k - 100.0 * recovery_k) / (price_j - 100.0 * recovery_j)


def dv01_neutral_ratio(spread_duration_k: float, price_k: float, spread_duration_j: float, price_j: float) -> float:
    """N_j / N_k = (D^s_k P_k) / (D^s_j P_j), the spread-DV01-neutral ratio (Section 9.3 note on pair sizing).

    Intuition: neutral to a parallel spread move, not to a default (p. 530); kept for comparison.
    """
    return (spread_duration_k * price_k) / (spread_duration_j * price_j)


def hedge_ratio(sdv01_value: np.ndarray | float, ds_dsmkt: np.ndarray | float) -> np.ndarray:
    """h_i = sdv01_i * ds_i / ds_mkt (Section 9.3, systematic hedge ratio).

    Intuition: hedge the part of the spread that moves with the market, not the residual the signal pays for.
    """
    return np.asarray(sdv01_value, dtype=float) * np.asarray(ds_dsmkt, dtype=float)


# ---------------------------------------------------------------------------
# 9.4 Event-conditional limits
# ---------------------------------------------------------------------------


def band_gate_scale(q_alpha: np.ndarray | float, sigma_x: np.ndarray | float, ref: float = 1.0, cap: float = 2.0) -> np.ndarray:
    """scale = min(cap, ref / (q_alpha * sigma_x)) (Section 9.4, band gating).

    `ref` is the band width that earns a full-size position. Intuition: a wide band means the model knows less; size less.
    """
    w = np.asarray(q_alpha, dtype=float) * np.asarray(sigma_x, dtype=float)
    return np.minimum(cap, ref / w)


def pre_event_cap(target_notional: float, worst_dpnl: float, exp_conv_ret_h: float, budget_frac: float = 0.5) -> float:
    """N_cap = min(N, budget / (|worst dP| / 100)), budget = budget_frac * exp_conv_ret_h * N (Section 9.4, pre-event cap).

    Applies to events inside five days. `worst_dpnl` is in points per 100 face.
    Intuition: do not risk more on one event than a fraction of what the trade expects to earn.
    """
    loss_per_unit = max(0.0, -worst_dpnl) / 100.0
    if loss_per_unit == 0.0:
        return float(target_notional)
    budget = budget_frac * abs(exp_conv_ret_h) * abs(target_notional)
    return float(np.sign(target_notional) * min(abs(target_notional), budget / loss_per_unit))


def g_decreasing(w_down: np.ndarray | float, gamma: float = 3.0) -> np.ndarray:
    """g(w) = exp(-gamma * w), strictly decreasing in w (Section 9.4). gamma = 3 is a placeholder."""
    return np.exp(-gamma * np.asarray(w_down, dtype=float))


def regime_jtd_limit(jtd_base: float, w_down: np.ndarray | float, g: Callable[[np.ndarray], np.ndarray] = g_decreasing) -> np.ndarray:
    """jtd_limit = jtd_base * g(w_down(m_t)), g decreasing (Section 9.4, regime limit).

    Intuition: cut single-name default exposure as the downside weight rises.
    """
    return jtd_base * g(np.asarray(w_down, dtype=float))


@dataclass(frozen=True)
class LimitCheck:
    """Exposure, limit, utilisation (exposure / limit) and breach flag for one limit."""

    exposure: float
    limit: float
    utilisation: float
    breach: bool


def _check(exposure: float, limit: float) -> LimitCheck:
    util = exposure / limit if limit > 0 else (np.inf if exposure > 0 else 0.0)
    return LimitCheck(float(exposure), float(limit), float(util), bool(util > 1.0))


def wall_limit(
    gross: np.ndarray, wall_cover_4: np.ndarray, paths: Sequence[MacroPath], primary_open: Mapping[str, bool], cap_base: float
) -> LimitCheck:
    """Gross to issuers with wall_cover_4 < 1 <= cap_base * sum_m p(m) 1{primary open on m} (Section 9.4, wall limit).

    Intuition: refinance risk is macro risk; allow wall exposure only in proportion to the paths where the market is open.
    """
    exposed = float(np.sum(np.abs(np.asarray(gross, dtype=float))[np.asarray(wall_cover_4, dtype=float) < 1.0]))
    share_open = sum(p.prob for p in paths if primary_open.get(p.name, False))
    return _check(exposed, cap_base * share_open)


def correlated_event_limit(jtd_values: np.ndarray, sector_driver: Sequence[str], limit: float) -> pd.DataFrame:
    """sum_{i in driver} jtd_i <= limit, per shared sector driver (Section 9.4, correlated-event limit).

    Intuition: one commodity path hits every issuer on that driver together.
    """
    df = pd.DataFrame({"driver": list(sector_driver), "jtd": np.asarray(jtd_values, dtype=float)})
    out = df.groupby("driver")["jtd"].sum().to_frame("exposure")
    out["limit"] = limit
    out["utilisation"] = out["exposure"] / limit
    out["breach"] = out["utilisation"] > 1.0
    return out


# ---------------------------------------------------------------------------
# Section 10.4 event_matrix
# ---------------------------------------------------------------------------


def event_matrix_block(
    *,
    date: datetime,
    available_at: datetime,
    position_id: str,
    cusip: str,
    event_id: str,
    event_type: EventType,
    event_date: datetime,
    date_confirmed: bool,
    grid: EventGrid,
    p_path: Mapping[str, float],
    p_outcome_given_path: np.ndarray,
) -> pd.DataFrame:
    """One position and one event as long rows, one per (outcome, path) (Section 10.4; Section 9.2).

    Intuition: the long form lets the portfolio layer sum P&L by path and by event without reshaping.
    """
    rows = []
    for i, m in enumerate(grid.paths):
        for j, o in enumerate(grid.outcomes):
            rows.append(
                {
                    "date": date,
                    "available_at": available_at,
                    "position_id": position_id,
                    "cusip": cusip,
                    "event_id": event_id,
                    "event_type": EventType(event_type).value,
                    "event_date": event_date,
                    "date_confirmed": bool(date_confirmed),
                    "outcome": o,
                    "macro_path": m,
                    "p_path": float(p_path[m]),
                    "p_outcome_given_path": float(p_outcome_given_path[i, j]),
                    "dspread_bp": float(grid.dspread_bp[i, j]),
                    "dpnl": float(grid.dpnl[i, j]),
                    "features_delta": np.asarray(grid.features_delta[i][j]).tolist(),
                }
            )
    return pd.DataFrame(rows)


def build_event_matrix(blocks: Sequence[pd.DataFrame]) -> pd.DataFrame:
    """Concatenate position-event blocks into the long event_matrix (Section 10.4).

    Checks that P(o | e, m) sums to one within each (position, event, path).
    Intuition: a probability leak in one block would bias every expected P&L downstream.
    """
    if not blocks:
        return pd.DataFrame()
    df = pd.concat(blocks, ignore_index=True)
    s = df.groupby(["position_id", "event_id", "macro_path"])["p_outcome_given_path"].sum()
    if not np.allclose(s.to_numpy(), 1.0, atol=1e-6):
        raise ValueError(f"P(o | e, m) does not sum to 1: {s[~np.isclose(s, 1.0)].to_dict()}")
    return df


# ---------------------------------------------------------------------------
# Section 10.4 event_matrix from a macro path set and per-path case weights
# ---------------------------------------------------------------------------

WEIGHTED = "weighted"
"""Name of the probability-weighted row in a per-path table. It is not a path."""

_DOWN_PREFIX = "down"
_UP_PREFIX = "up"


def _path_feature_rows(path_features: pd.DataFrame | Mapping[str, Mapping[str, float]] | None) -> dict[str, Mapping[str, float]]:
    """Return {path name: feature row}, without the weighted row.

    Accept a DataFrame with a `macro_path` column (or index) and one row per path,
    or a plain dict path -> dict of features. Raise ValueError on a duplicate path.
    """
    if path_features is None:
        return {}
    if isinstance(path_features, pd.DataFrame):
        df = path_features.set_index("macro_path") if "macro_path" in path_features.columns else path_features
        names = [str(k) for k in df.index]
        if len(names) != len(set(names)):
            raise ValueError("path_features has more than one row for a macro path; pass one issuer at a time")
        return {str(k): row for k, row in df.iterrows() if str(k) != WEIGHTED}
    return {str(k): v for k, v in path_features.items() if str(k) != WEIGHTED}


def _feature(row: Mapping[str, float], names: Sequence[str], path: str) -> float:
    for n in names:
        if n in row and row[n] is not None and not pd.isna(row[n]):
            return float(row[n])
    raise KeyError(f"path {path!r}: path_features has none of {list(names)}")


def _check_case_weights(w: Mapping[str, float], path: str, tol: float) -> None:
    vals = np.asarray(list(w.values()), dtype=float)
    if np.any(vals < -tol) or abs(vals.sum() - 1.0) > tol:
        raise ValueError(f"path {path!r}: case weights {dict(w)} are not a distribution")


def outcome_probs_from_cases(
    event_type: EventType | str,
    w_by_path: Mapping[str, Mapping[str, float]],
    path_features: pd.DataFrame | Mapping[str, Mapping[str, float]] | None = None,
    *,
    waiver_share: float = 0.9,
    extend_share: float = 0.5,
    default_share: float = 0.5,
    tol: float = 1e-6,
) -> pd.DataFrame:
    """P(o | e, m) for each macro path m from the case weights and the per-path forward features (Section 9.2; framework F11).

    Return a frame with one row per path (index `macro_path`) and one column per outcome in
    `OUTCOMES[event_type]` order. Each row sums to 1. The weighted row is not a path; it is dropped.

    Earnings: P(miss | m) = w_down(m) = sum of the case weights whose name starts with "down";
    P(beat | m) = w_up(m), the upside weight; P(in_line | m) = 1 - w_down(m) - w_up(m).
    Intuition: an earnings miss is the downside case that comes true, so its odds are the downside weight.

    Covenant test: P(breach | m) = p_breach_4(m); P(pass | m) = 1 - P(breach | m);
    the breach splits into waiver and acceleration by `waiver_share` (default 0.9, a placeholder).
    Intuition: most breaches end in a waiver at a fee; acceleration is rare (p. 355).

    Maturity and refinance: P(fail | m) = p_refi_4(m) * (1 - p_refi_access(m)); P(refinanced | m) = 1 - P(fail | m).
    The failure splits into extension, distressed exchange, and default by `extend_share` and `default_share`.
    Intuition: a refinance fails only when the issuer needs the market and the market is shut.

    `w_by_path` is {path: {case: weight}}; `path_features` carries `p_breach_4`, `p_refi_4`, and
    `p_refi_access` (or `refi_access`) per path. The share parameters stay placeholders until Section 11 calibrates them.
    """
    et = EventType(event_type)
    paths = [str(m) for m in w_by_path if str(m) != WEIGHTED]
    if not paths:
        raise ValueError("w_by_path has no macro path")
    feats = _path_feature_rows(path_features)
    rows: dict[str, dict[str, float]] = {}
    for m in paths:
        w = w_by_path[m]
        _check_case_weights(w, m, tol)
        if et is EventType.EARNINGS:
            down = float(sum(v for k, v in w.items() if str(k).startswith(_DOWN_PREFIX)))
            up = float(sum(v for k, v in w.items() if str(k).startswith(_UP_PREFIX)))
            rows[m] = {"beat": up, "in_line": 1.0 - down - up, "miss": down}
            continue
        if m not in feats:
            raise KeyError(f"path {m!r}: no row in path_features")
        if et is EventType.COVENANT_TEST:
            b = float(np.clip(_feature(feats[m], ("p_breach_4",), m), 0.0, 1.0))
            rows[m] = outcome_probabilities(et, p_breach=b, waiver_share=waiver_share)
        elif et is EventType.MATURITY_REFI:
            p_refi = float(np.clip(_feature(feats[m], ("p_refi_4",), m), 0.0, 1.0))
            access = float(np.clip(_feature(feats[m], ("p_refi_access", "refi_access"), m), 0.0, 1.0))
            rows[m] = outcome_probabilities(
                et, p_refi=p_refi, refi_access=access, extend_share=extend_share, default_share=default_share
            )
        else:
            raise NotImplementedError(f"no case-weight rule in Section 9.2 for {et.value}; pass P(o | e, m) directly")
    out = pd.DataFrame.from_dict(rows, orient="index")[list(OUTCOMES[et])]
    out.index.name = "macro_path"
    s = out.sum(axis=1).to_numpy()
    if np.any(out.to_numpy() < -tol) or not np.allclose(s, 1.0, atol=tol):
        raise ValueError(f"P(o | e, m) is not a distribution per path: {dict(zip(out.index, s))}")
    return out


def failed_refi_probability(p_refi_4: np.ndarray | float, p_refi_access: np.ndarray | float) -> np.ndarray:
    """P(fail | m) = p_refi_4(m) * (1 - p_refi_access(m)) (Section 9.2; framework F11, maturity row).

    Intuition: the issuer must need new money and find the window shut; either alone is not a failure.
    """
    return np.asarray(p_refi_4, dtype=float) * (1.0 - np.asarray(p_refi_access, dtype=float))


def _yield_parts(name: str, paths: Mapping[str, MacroPath] | None, feats: Mapping[str, Mapping[str, float]], h_q: int) -> tuple[float, float]:
    """(dy_growth, dy_policy) of path `name` at quarter h_q, from MacroPath.extra, else from path_features."""
    if paths is not None and name in paths:
        src: Mapping = paths[name].extra
    elif name in feats:
        src = feats[name]
    else:
        raise KeyError(f"path {name!r}: no dy_growth and dy_policy in paths or path_features")
    out = []
    for k in ("dy_growth", "dy_policy"):
        if k not in src:
            raise KeyError(f"path {name!r}: missing {k}")
        a = np.atleast_1d(np.asarray(src[k], dtype=float))
        out.append(float(a[min(h_q, a.size) - 1]))
    return out[0], out[1]


def event_matrix_from_paths(
    *,
    date: datetime,
    available_at: datetime,
    position: Mapping[str, object],
    event: Mapping[str, object],
    path_probs: Mapping[str, float],
    w_by_path: Mapping[str, Mapping[str, float]],
    path_features: pd.DataFrame | Mapping[str, Mapping[str, float]] | None,
    pnl_fn: Callable[[str, str], float | Mapping[str, object]],
    paths: Sequence[MacroPath] | Mapping[str, MacroPath] | None = None,
    h_q: int = 1,
    tol: float = 1e-6,
    **share_kwargs: float,
) -> pd.DataFrame:
    """Long event_matrix rows for one position and one event, one row per (outcome, path) (Section 10.4; Section 9.2).

    p_path(m) comes from the posterior of the macro path set; P(o | e, m) comes from `outcome_probs_from_cases`.
    The P&L of each cell follows Section 9.2:

        dP(o, m) = -D dy(m) P - D^s [ds_sys(m) + s_hat(x(o, m)) - s_hat(x)] P + carry_h - 1{default}(P - 100 R_adj(m)),
        dy(m) = dy_growth(m) + dy_policy(m),  ds_sys(m) = beta_g dy_growth(m) + beta_p dy_policy(m).

    Intuition: one path sets the rate and market spread move, one outcome sets the issuer's own spread move, and the two add.

    `position` holds `position_id`, `cusip`, `price`, `mod_duration`, `spread_duration`, `beta_g`, `beta_p`,
    `carry_h`, and `recovery_adj` (a number or a dict by path). `event` holds `event_id`, `event_type`,
    `event_date`, `date_confirmed`. `pnl_fn(outcome, path)` returns ds_idio = s_hat(x(o, m)) - s_hat(x)
    as a decimal, or a dict with `ds_idio` and optional `features_delta` and `recovery_adj`.
    `paths` supplies `extra["dy_growth"]` and `extra["dy_policy"]` per path, read at quarter `h_q`
    (cumulative change from the decision date); without `paths`, `path_features` must carry them.
    Raise ValueError when p_path does not sum to 1, when the path names disagree, or when P(o | e, m) leaks.
    """
    pp = {str(k): float(v) for k, v in path_probs.items() if str(k) != WEIGHTED}
    vals = np.asarray(list(pp.values()), dtype=float)
    if vals.size == 0 or np.any(vals < -tol) or abs(vals.sum() - 1.0) > tol:
        raise ValueError(f"p_path is not a distribution: sum {vals.sum() if vals.size else 0.0}")
    et = EventType(event["event_type"])
    p_out = outcome_probs_from_cases(et, w_by_path, path_features, tol=tol, **share_kwargs)
    if set(p_out.index) != set(pp):
        raise ValueError(f"path names differ: p_path {sorted(pp)} against case weights {sorted(p_out.index)}")
    p_out = p_out.loc[list(pp)]
    pmap: Mapping[str, MacroPath] | None
    if paths is None:
        pmap = None
    elif isinstance(paths, Mapping):
        pmap = {str(k): v for k, v in paths.items()}
    else:
        pmap = {p.name: p for p in paths}
    feats = _path_feature_rows(path_features)

    price = float(position["price"])
    d_mod, d_spr = float(position["mod_duration"]), float(position["spread_duration"])
    beta_g, beta_p = float(position["beta_g"]), float(position["beta_p"])
    carry = float(position.get("carry_h", 0.0))
    rec = position.get("recovery_adj", 0.0)
    outcomes = tuple(p_out.columns)
    names = tuple(pp)
    nm, no = len(names), len(outcomes)
    dsp, pnl = np.zeros((nm, no)), np.zeros((nm, no))
    fd: list[list[np.ndarray]] = []
    dyg_col, dyp_col, dss_col = np.zeros(nm), np.zeros(nm), np.zeros(nm)
    for i, m in enumerate(names):
        dyg, dyp = _yield_parts(m, pmap, feats, h_q)
        ds_sys = float(systematic_spread_change(dyg, dyp, beta_g, beta_p))
        dyg_col[i], dyp_col[i], dss_col[i] = dyg, dyp, ds_sys
        rec_m = float(rec[m]) if isinstance(rec, Mapping) else float(rec)
        row = []
        for j, o in enumerate(outcomes):
            r = pnl_fn(o, m)
            if isinstance(r, Mapping):
                ds_i = float(r["ds_idio"])
                delta = np.asarray(r.get("features_delta", []), dtype=float)
                rec_o = float(r.get("recovery_adj", rec_m))
            else:
                ds_i, delta, rec_o = float(r), np.zeros(0), rec_m
            dsp[i, j] = (ds_sys + ds_i) * 1e4
            pnl[i, j] = position_pnl(price, d_mod, d_spr, dyg + dyp, ds_sys, ds_i, carry, o in DEFAULT_OUTCOMES, rec_o)
            row.append(delta)
        fd.append(row)
    grid = EventGrid(outcomes, names, dsp, pnl, fd)
    blk = event_matrix_block(
        date=date,
        available_at=available_at,
        position_id=str(position["position_id"]),
        cusip=str(position.get("cusip", "")),
        event_id=str(event["event_id"]),
        event_type=et,
        event_date=event["event_date"],
        date_confirmed=bool(event.get("date_confirmed", False)),
        grid=grid,
        p_path=pp,
        p_outcome_given_path=p_out.to_numpy(),
    )
    idx = {m: i for i, m in enumerate(names)}
    k = blk["macro_path"].map(idx).to_numpy()
    blk["dy_growth"], blk["dy_policy"], blk["ds_sys"] = dyg_col[k], dyp_col[k], dss_col[k]
    return build_event_matrix([blk])


def event_matrix_risk(em: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """E[dP | e], EventVaR_alpha, and the worst dP per (date, position, event) from long event_matrix rows (Section 9.2).

    Reuse `expected_event_pnl` and `event_var` on the (path, outcome) grid of each block.
    Intuition: the long table holds every cell; the risk numbers are its weighted mean and its alpha quantile.
    """
    out = []
    for (d, pos, evt), g in em.groupby(["date", "position_id", "event_id"], sort=False):
        pnl = g.pivot(index="macro_path", columns="outcome", values="dpnl")
        po = g.pivot(index="macro_path", columns="outcome", values="p_outcome_given_path").loc[pnl.index, pnl.columns]
        p_path = g.groupby("macro_path")["p_path"].first().loc[pnl.index].to_numpy()
        P, W = pnl.fillna(0.0).to_numpy(), po.fillna(0.0).to_numpy()
        out.append(
            {
                "date": d,
                "position_id": pos,
                "event_id": evt,
                "exp_dpnl": expected_event_pnl(P, p_path, W),
                "event_var_alpha": event_var(P, p_path, W, alpha),
                "worst_outcome_pnl": float(g["dpnl"].min()),
            }
        )
    return pd.DataFrame(out)


def catalysts_in_horizon(events: Sequence[Mapping], decision, h_years: float) -> list[dict]:
    """Catalysts for the call (framework F9 G2, F11; methodology 9.1): the events that fall inside the holding horizon.

    An event with a `date` counts when decision < date <= decision + h_years. An event with `years` (time from the
    decision, such as debt due) counts when years <= h_years. An undated event does not count. Order is kept.
    Intuition: a gap closes on a date, so only the events before the exit can close it.
    """
    t0 = pd.Timestamp(decision)
    t1 = t0 + pd.Timedelta(round(h_years * 365.25), unit="D")
    out = []
    for e in events:
        if e.get("date"):
            d = pd.Timestamp(e["date"])
            if t0 < d <= t1:
                out.append(dict(e))
        elif e.get("years") is not None and e["years"] == e["years"] and e["years"] <= h_years:
            out.append(dict(e))
    return out
