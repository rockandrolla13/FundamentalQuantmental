"""Signals layer: S1 to S7, the composite, and the force rank (methodology Section 8).

Every signal is a score per bond. Positive means long. Inputs are plain
numpy arrays and pandas frames, already filtered to `available_at <= t`
by the input layer. This module does not call the fair spread model; the
caller passes fair spreads that the model produced.

Units: spreads are decimals (0.054 is 540 bp) unless a name ends in `_bp`.
Prices are per 100 face.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats
from scipy.special import expit, logit

CYCLES: tuple[int, ...] = (2008, 2015, 2020, 2022)
CASH = "CASH"  # The only valid `replaces_position` for a book that has free capacity.


class MissingReplacementError(ValueError):
    """Raised when a new position enters the book without `replaces_position` (Section 8, force rank; Section 11)."""


def _arr(x: Iterable[float] | float) -> np.ndarray:
    return np.asarray(x, dtype=float)


def _xs_sigma(x: np.ndarray) -> float:
    """Cross-sectional standard deviation, NaN-aware, with a floor that avoids division by zero."""
    s = float(np.nanstd(x, ddof=1)) if np.sum(np.isfinite(x)) > 1 else 0.0
    return s if s > 1e-12 else np.nan


# ---------------------------------------------------------------------------
# S1. Fair value residual
# ---------------------------------------------------------------------------


def s1_residual(z: np.ndarray, q_alpha: np.ndarray | float, event_contaminated: np.ndarray) -> np.ndarray:
    """S1 = z * 1{|z| > q_{1-alpha}} * 1{event_contaminated = 0} (Section 8, S1).

    Intuition: a residual counts only when it sits outside the model's measured
    ignorance and no fresh event has made the model state stale.
    """
    z = _arr(z)
    q = np.broadcast_to(_arr(q_alpha), z.shape)
    clean = ~np.asarray(event_contaminated, dtype=bool)
    out = np.where((np.abs(z) > q) & clean, z, 0.0)
    return np.where(np.isfinite(z), out, 0.0)


def half_life(rho: np.ndarray | float) -> np.ndarray:
    """h_{1/2} = log 2 / (-log rho) (Section 7.5), used for the S1 horizon.

    Intuition: a residual that decays fast gives a short trade; rho >= 1 never converges.
    """
    rho = _arr(rho)
    with np.errstate(divide="ignore", invalid="ignore"):
        hl = np.log(2.0) / -np.log(rho)
    return np.where((rho > 0) & (rho < 1), hl, np.inf)


def s1_horizon(rho: np.ndarray | float) -> np.ndarray:
    """S1 horizon = 2 * h_{1/2} periods (Section 8, S1 table; Section 7.5).

    Intuition: two half-lives close three quarters of the gap, which is enough to be paid.
    """
    return 2.0 * half_life(rho)


def s1_entry(
    z: np.ndarray,
    q_alpha: np.ndarray | float,
    event_contaminated: np.ndarray,
    exp_conv_ret_h: np.ndarray,
    bid_ask_bp: np.ndarray,
    spread_duration: np.ndarray,
) -> np.ndarray:
    """Entry rule: S1 != 0 and |exp_conv_ret_h| > round-trip cost (Section 8, S1 table, Entry).

    Round-trip cost as a price fraction is `bid_ask_bp * spread_duration / 10,000`
    (Section 9.3, exit cost `bid_ask_bp * sdv01`, scaled to a unit of price).
    Intuition: a mispricing that the bid-ask eats is not a trade.
    """
    s1 = s1_residual(z, q_alpha, event_contaminated)
    cost = _arr(bid_ask_bp) * _arr(spread_duration) / 1e4
    return (s1 != 0.0) & (np.abs(_arr(exp_conv_ret_h)) > cost)


def s1_exit(
    z: np.ndarray,
    q_alpha: np.ndarray | float,
    periods_held: np.ndarray,
    horizon: np.ndarray,
    event_reset: np.ndarray,
) -> np.ndarray:
    """Exit rule: |z| < q/2, or the horizon ends, or an event resets the state (Section 8, S1 table, Exit).

    Intuition: take profit when half the band is gone; do not hold past the expected convergence time.
    """
    z = _arr(z)
    q = np.broadcast_to(_arr(q_alpha), z.shape)
    return (np.abs(z) < 0.5 * q) | (_arr(periods_held) >= _arr(horizon)) | np.asarray(event_reset, dtype=bool)


@dataclass(frozen=True)
class TighteningTrade:
    """Result of `spread_tightening_return`. Returns are decimals."""

    price_return: float
    carry_return: float
    horizon_return: float
    annualised: float


def spread_tightening_return(
    s_now: float,
    s_target: float,
    spread_duration: float,
    yield_to_worst: float,
    horizon_years: float,
    convexity: float = 0.0,
    compound: bool = True,
) -> TighteningTrade:
    """Return of a spread-closing trade: -D^s * ds + 1/2 C ds^2 + y * h (Section 8, S1 paragraph; Section 7.5 E[r]).

    Annualise by compounding, (1 + r_h)^(1/h) - 1, or simply, r_h / h.
    Intuition: the S1 long earns the price gain from the spread close plus the carry while it waits.
    This is the book's spread tightening trade (pp. 517-518): 540 bp to 440 bp in six months.
    """
    ds = s_target - s_now
    price_ret = -spread_duration * ds + 0.5 * convexity * ds * ds
    carry = yield_to_worst * horizon_years
    r_h = price_ret + carry
    ann = (1.0 + r_h) ** (1.0 / horizon_years) - 1.0 if compound else r_h / horizon_years
    return TighteningTrade(price_ret, carry, r_h, ann)


# ---------------------------------------------------------------------------
# S2. Fundamental momentum
# ---------------------------------------------------------------------------


def s2_momentum(
    s_fair_t: np.ndarray,
    s_fair_prev: np.ndarray,
    s_t: np.ndarray,
    s_prev: np.ndarray,
) -> np.ndarray:
    """S2 = [log s_t - log s_{t-1}] - [log s_hat_t - log s_hat_{t-1}]_{kappa, eta fixed} (Section 8, S2).

    Pass `s_fair_t` evaluated with kappa and eta held at their t-1 values, so the
    fair term holds only the issuer's own change. Positive means fundamentals
    improved more than the spread tightened.
    Intuition: spreads move after fundamentals and before ratings (p. 274).
    """
    d_fair = np.log(_arr(s_fair_t)) - np.log(_arr(s_fair_prev))
    d_mkt = np.log(_arr(s_t)) - np.log(_arr(s_prev))
    return d_mkt - d_fair


# ---------------------------------------------------------------------------
# S3. Estimate revision and consensus gap
# ---------------------------------------------------------------------------


def analyst_bias(
    analyst_id: Sequence[str], forecast_lev: np.ndarray, realised_lev: np.ndarray
) -> dict[str, float]:
    """Bias_a = mean(forecast_lev - realised_lev) over closed forecasts of analyst a (Section 8, S3 failure mode).

    Intuition: a habitually conservative analyst (positive bias) shows a false negative-leverage gap; subtract it.
    """
    df = pd.DataFrame({"a": list(analyst_id), "e": _arr(forecast_lev) - _arr(realised_lev)})
    return df.groupby("a")["e"].mean().to_dict()


def s3_revision_gap(
    rev_lev: np.ndarray,
    gap_consensus: np.ndarray,
    bias: np.ndarray | float | None = None,
) -> np.ndarray:
    """S3 = -rev_lev / sigma(rev_lev) - (gap_consensus - bias) / sigma(gap_consensus) (Section 8, S3).

    Sigma is the cross-sectional standard deviation on the date. Missing parts count as zero.
    Intuition: less leverage ahead, and an analyst below consensus on leverage, both say long.
    """
    rev = _arr(rev_lev)
    gap = _arr(gap_consensus) - (0.0 if bias is None else _arr(bias))
    a = -rev / _xs_sigma(rev)
    b = -gap / _xs_sigma(gap)
    return np.nan_to_num(a, nan=0.0) + np.nan_to_num(b, nan=0.0)


# ---------------------------------------------------------------------------
# S4. Capital structure relative value
# ---------------------------------------------------------------------------


def s4_pair_score(
    s_k: np.ndarray,
    s_j: np.ndarray,
    kappa: np.ndarray | float,
    lam: np.ndarray | float,
    lgd_k: np.ndarray,
    lgd_j: np.ndarray,
    sigma_pair: np.ndarray | float,
) -> np.ndarray:
    """S4_{k,j} = [(s_k - s_j) - kappa * lambda * (LGD_k - LGD_j)] / sigma_pair (Section 8, S4; Section 7.4).

    Positive: long k, short j. Size the pair by jump-to-default (events.jtd_neutral_ratio).
    Intuition: inside one issuer the default probability cancels, so the gap must pay only for the recovery gap.
    """
    fair_gap = _arr(kappa) * _arr(lam) * (_arr(lgd_k) - _arr(lgd_j))
    return ((_arr(s_k) - _arr(s_j)) - fair_gap) / _arr(sigma_pair)


def spread_per_turn(s_k: float, s_j: float, lev_k: float, lev_j: float) -> float:
    """SPT_{k,j} = (s_k - s_j) / (Lev_k - Lev_j) (Section 7.4), the model-free S4 check.

    Intuition: HCA unsecured paid 35 bp per extra turn against 172 bp for the second lien; the first was rich.
    """
    return (s_k - s_j) / (lev_k - lev_j)


# ---------------------------------------------------------------------------
# S5. Document optionality
# ---------------------------------------------------------------------------


def s5_put_value(p_lbo: np.ndarray, coc_put_price: np.ndarray, price: np.ndarray) -> np.ndarray:
    """S5_put = p_LBO * max(0, coc_put_price - P) / P (Section 8, S5).

    Intuition: a change of control put pays the gap to 101 times the chance that a deal happens.
    """
    p = _arr(price)
    return _arr(p_lbo) * np.maximum(0.0, _arr(coc_put_price) - p) / p


def s5_lme_value(pi_lme: np.ndarray, recovery: np.ndarray, recovery_lme: np.ndarray, price: np.ndarray) -> np.ndarray:
    """S5_LME = -pi_LME * (R - R^LME) * 100 / P (Section 8, S5). R is a fraction of face.

    Negative for an exposed tranche (R^LME < R), positive for a protected one (R^LME > R).
    Intuition: the PU Corp uptier halved the recovery of the tranche left behind (p. 504).
    """
    return -_arr(pi_lme) * (_arr(recovery) - _arr(recovery_lme)) * 100.0 / _arr(price)


# ---------------------------------------------------------------------------
# S6. Rating migration and forced flows
# ---------------------------------------------------------------------------

# Placeholder priors for a single-B issuer with zero gap. Calibrate to the agency
# migration matrix before use (Section 11, PD row). Gap is in notches, positive
# means the fitted rating is better than the agency rating (Section 4.5).
P_UP_BASE = 0.10
P_DOWN_BASE = 0.15
SLOPE_PER_NOTCH = 0.6


def migration_probabilities(
    gap: np.ndarray,
    p_up_base: float = P_UP_BASE,
    p_down_base: float = P_DOWN_BASE,
    slope: float = SLOPE_PER_NOTCH,
) -> tuple[np.ndarray, np.ndarray]:
    """P(up | gap) = expit(logit p_up0 + b*gap), P(down | gap) = expit(logit p_down0 - b*gap) (Section 8, S6).

    A logistic map, not an ordered logit. If the two sum above 0.95 both are scaled down to 0.95.
    Parameters: p_up0 = 10%, p_down0 = 15%, b = 0.6 per notch; placeholders until fitted.
    Intuition: a positive gap means fundamentals rate the issuer better than the agency does, so an upgrade is likelier.
    """
    g = _arr(gap)
    up = expit(logit(p_up_base) + slope * g)
    down = expit(logit(p_down_base) - slope * g)
    tot = up + down
    scale = np.where(tot > 0.95, 0.95 / tot, 1.0)
    return up * scale, down * scale


def flow_weight(index_weight: np.ndarray, constrained_share: np.ndarray) -> np.ndarray:
    """w_flow = constrained_share * index_weight / mean(index_weight) (Section 8, S6).

    Intuition: forced flows are larger when more holders are rating-constrained and the bond is a big index name.
    """
    iw = _arr(index_weight)
    m = np.nanmean(iw)
    return _arr(constrained_share) * (iw / m if m > 0 else np.zeros_like(iw))


def s6_migration(p_up: np.ndarray, p_down: np.ndarray, w_flow: np.ndarray) -> np.ndarray:
    """S6 = [P(up_12m | gap) - P(down_12m | gap)] * w_flow (Section 8, S6).

    Intuition: the price moves twice on a rating change, once on the move and once on the forced flow (p. 418).
    """
    return (_arr(p_up) - _arr(p_down)) * _arr(w_flow)


# ---------------------------------------------------------------------------
# S7. Macro-conditional sector tilt
# ---------------------------------------------------------------------------


def s7_sector_tilt(
    eta: Mapping[str, float],
    eta_hat: Mapping[str, float],
    d_w_down: Mapping[str, float],
    theta: float = 1.0,
) -> dict[str, float]:
    """S7_sector = [eta_{sector,t} - eta_hat_sector(m_t)] - theta * dw^down_{sector,t} (Section 8, S7).

    Intuition: a sector that trades wider than its macro forecast implies, with no rise in downside weight, is cheap.
    """
    return {s: (eta[s] - eta_hat[s]) - theta * d_w_down.get(s, 0.0) for s in eta}


def apply_sector_tilt(sector: Sequence[str], tilt: Mapping[str, float]) -> np.ndarray:
    """Broadcast S7 from sector to bond (Section 8, S7: apply it as a tilt on every bond in the sector).

    Intuition: the tilt is a sector view, so every bond in the sector carries it.
    """
    return np.array([tilt.get(s, 0.0) for s in sector], dtype=float)


# ---------------------------------------------------------------------------
# Composite, sizing, force rank
# ---------------------------------------------------------------------------


def standardise(x: np.ndarray) -> np.ndarray:
    """S_tilde = (S - mean_t S) / sd_t S on one date's cross-section (Section 8, composite).

    Missing and constant signals map to zero. Intuition: unit variance lets the IC weights, not the units, set the mix.
    """
    x = _arr(x)
    sd = _xs_sigma(x)
    if not np.isfinite(sd):
        return np.zeros_like(x)
    return np.nan_to_num((x - np.nanmean(x)) / sd, nan=0.0)


def standardise_by_date(df: pd.DataFrame, cols: Sequence[str], date_col: str = "date") -> pd.DataFrame:
    """Apply `standardise` per date to each column in `cols` (Section 8, composite).

    Intuition: a score is relative to the universe on that day, never to the future.
    """
    out = df.copy()
    for c in cols:
        out[c] = df.groupby(date_col)[c].transform(lambda s: pd.Series(standardise(s.to_numpy()), index=s.index))
    return out


def ic_weights(ic_by_phase: pd.DataFrame, phase: str) -> pd.Series:
    """w_{j,phase} proportional to max(0, IC_{j,phase}), summing to one (Section 8, composite).

    `ic_by_phase` has signals as rows and phases as columns. All zero when no signal has a positive IC.
    Intuition: a signal that lost money in this phase of the cycle gets no vote in it.
    """
    w = ic_by_phase[phase].clip(lower=0.0).fillna(0.0)
    tot = w.sum()
    return w / tot if tot > 0 else w * 0.0


def neutralise(c: np.ndarray, exposures: np.ndarray) -> np.ndarray:
    """C_perp = C - X (X'X)^-1 X'C, with X = [1, beta_mkt, duration] (Section 8, composite).

    Cross-sectional OLS residual. Intuition: the composite must pay for the residual, not for index beta or duration.
    """
    c = _arr(c)
    x = np.atleast_2d(_arr(exposures))
    if x.shape[0] != c.shape[0]:
        x = x.T
    X = np.column_stack([np.ones(c.shape[0]), x])
    coef, *_ = np.linalg.lstsq(X, c, rcond=None)
    return c - X @ coef


def composite(
    signals: np.ndarray,
    weights: np.ndarray,
    beta_mkt: np.ndarray,
    duration: np.ndarray,
) -> np.ndarray:
    """C_i = sum_j w_j * S_tilde_{j,i}, then neutralised to beta and duration (Section 8, composite).

    `signals` is (n_bonds, n_signals) on one date. Intuition: blend the standardised views, then strip the market bets.
    """
    s = np.atleast_2d(_arr(signals))
    z = np.column_stack([standardise(s[:, j]) for j in range(s.shape[1])])
    c = z @ _arr(weights)
    return neutralise(c, np.column_stack([_arr(beta_mkt), _arr(duration)]))


def adv_cap(target_notional: np.ndarray, adv: np.ndarray, k: float) -> np.ndarray:
    """n_i <= k * ADV_i, sign kept (Section 8, composite; Section 11 backtest capacity cap).

    Intuition: a position that takes weeks to exit is a liquidity bet, not a signal bet.
    """
    n = _arr(target_notional)
    cap = k * _arr(adv)
    return np.sign(n) * np.minimum(np.abs(n), cap)


def force_rank(ids: Sequence[str], composite_score: np.ndarray) -> pd.DataFrame:
    """Force rank = composite sorted across the whole universe, rank 1 = best long (Section 8, force rank; p. 369).

    No grouping by sector. Intuition: the book makes analysts rank outside their coverage so capital goes to the best idea.
    """
    c = _arr(composite_score)
    df = pd.DataFrame({"id": list(ids), "composite": c})
    df["force_rank"] = df["composite"].rank(ascending=False, method="first").astype(int)
    return df.sort_values("force_rank").reset_index(drop=True)


def admit_position(new_id: str, replaces_position: str | None, book: Iterable[str]) -> set[str]:
    """Admit a new position only with `replaces_position` (Section 8, force rank; Section 11, Who supplies what).

    `replaces_position` must name a position in the book, or be `CASH` for free capacity.
    The replaced position leaves the book. Raises MissingReplacementError otherwise.
    Intuition: the book asks of every new idea which position it replaces (p. 369).
    """
    held = set(book)
    if replaces_position is None or not str(replaces_position).strip():
        raise MissingReplacementError(f"{new_id}: replaces_position is required")
    if replaces_position != CASH and replaces_position not in held:
        raise MissingReplacementError(f"{new_id}: replaces_position {replaces_position!r} is not in the book")
    held.discard(replaces_position)
    held.add(new_id)
    return held


# ---------------------------------------------------------------------------
# Validation: rank IC net of costs, by cycle phase (Section 11)
# ---------------------------------------------------------------------------


def net_return(fwd_return: np.ndarray, turnover: np.ndarray, bid_ask_bp: np.ndarray, spread_duration: np.ndarray) -> np.ndarray:
    """r_net = r - turnover * (bid_ask_bp / 2) * D^s / 10,000 (Section 11, Signals row and Backtest design).

    Each one-way trade pays half the quoted bid-ask in spread, times spread duration in price.
    Intuition: a signal that trades a lot must clear its own costs.
    """
    cost = _arr(turnover) * 0.5 * _arr(bid_ask_bp) * _arr(spread_duration) / 1e4
    return _arr(fwd_return) - cost


def rank_ic(signal: np.ndarray, fwd_return: np.ndarray) -> float:
    """IC = Spearman rank correlation of signal and forward return on one date (Section 11, Signals row).

    Intuition: rank IC asks only whether the order was right, so outliers in returns do not drive it.
    """
    s, r = _arr(signal), _arr(fwd_return)
    ok = np.isfinite(s) & np.isfinite(r)
    if ok.sum() < 3 or np.ptp(s[ok]) == 0 or np.ptp(r[ok]) == 0:
        return np.nan
    return float(stats.spearmanr(s[ok], r[ok]).statistic)


def rank_ic_by_phase(
    df: pd.DataFrame,
    signal_cols: Sequence[str],
    net_ret_col: str = "ret_net",
    date_col: str = "date",
    phase_col: str = "cycle_phase",
) -> pd.DataFrame:
    """IC_{j,phase} = mean over dates in the phase of rank_ic(S_j, r_net) (Section 11, Signals row).

    Returns signals as rows and phases as columns, ready for `ic_weights`. Pass returns net of costs.
    Intuition: a signal must work in each phase, not only on average.
    """
    rows = []
    for (d, ph), g in df.groupby([date_col, phase_col]):
        rows.append({"phase": ph, **{c: rank_ic(g[c].to_numpy(), g[net_ret_col].to_numpy()) for c in signal_cols}})
    per_date = pd.DataFrame(rows)
    return per_date.groupby("phase")[list(signal_cols)].mean().T


def passes_cycle_test(
    ic_by_cycle: Mapping[int, float],
    cycles: Sequence[int] = CYCLES,
    min_pass: int = 3,
) -> bool:
    """Pass when IC after costs > 0 in at least 3 of the 4 cycles 2008, 2015, 2020, 2022 (Section 11, Signals row; CLAUDE.md).

    A missing cycle counts as a fail. Intuition: one lucky cycle is not evidence; three of four is.
    """
    wins = sum(1 for c in cycles if np.isfinite(ic_by_cycle.get(c, np.nan)) and ic_by_cycle[c] > 0)
    return wins >= min_pass
