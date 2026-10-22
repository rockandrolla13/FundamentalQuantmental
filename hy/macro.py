"""Macro path builder: forecast quantiles to named macro paths with probabilities (methodology 5.4, 9.2; framework F6).

The builder does four things.
1. It reads GDP growth and CPI quantiles from the forecast registry at the decision time. It fits one normal per
   variable and puts a bivariate normal on the standardised plane (zG, zC). Five rectangles partition the plane.
   The probability of each rectangle is the quantile mass of a path.
2. It reads the other path variables (policy rate, Treasury yields, index spread, default rate, PMI) from the
   registry. It shifts each one per path with a stated rule. When a source has no row, the variable falls back in the order of
   `hy.forecasts.FALLBACK_ORDER`, and the builder logs each fallback.
3. It classifies the macro phase with the six-indicator vote of framework F6.
4. It combines the phase prior with the quantile mass in a Bayesian update and records prior, mass, and posterior.

Assumptions (all v0; each one needs a decision page before a live weight depends on it)
- Region cut `c = 0.8416`, the 20th and 80th percentiles of a standard normal.
- Correlation of the GDP and CPI forecast errors `rho = -0.2`. Use `estimate_rho` on history to replace it.
- Reference anchors and scales of the plane: GDP 1.8% trend, 1.5% scale; CPI 2.5% anchor, 1.0% scale.
- Taylor-type policy shift: `a_pi = 1.5`, `a_y = 0.5`.
- Default yield split when no history: y2 `b_g = 0.5, b_p = 0.9`; y10 `b_g = 0.6, b_p = 0.5`.
- Spread map: 150 bp wider per -1 sd of GDP. Default rate map: +1.5 points per -1 sd. PMI map: 50 + 4 zG.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime

import numpy as np
import pandas as pd
from scipy import integrate
from scipy.stats import norm

from hy.events import MacroPath, YieldSplit, fit_spread_betas, fit_yield_split, split_yield_change, validate_paths
from hy.forecasts import FALLBACK_ORDER, ForecastRegistry, assert_no_lookahead, widen_factor

PATH_NAMES = ("soft_landing", "recession", "higher_for_longer", "disinflation_rally", "stagflation")
PHASES = ("expansion", "late_cycle", "downturn", "repair", "recovery")
HORIZON_Q = 8

Z80 = 1.2816      # z of the 90th percentile: q90 - q10 = 2 x 1.2816 sigma for a normal
CUT = 0.8416      # z of the 80th percentile: the region cut c
RHO_DEFAULT = -0.2

# Reference anchor and scale of each axis of the plane (assumption, v0). z = (X - anchor) / scale.
REFERENCE = {"gdp_growth": (0.018, 0.015), "cpi": (0.025, 0.010)}

TAYLOR = {"a_pi": 1.5, "a_y": 0.5}  # d_policy = a_pi x d_cpi + a_y x d_gdp (assumption, v0)

# Yield split defaults when the caller passes no history (assumption, v0). dy = b_g dG + b_p dP.
DEFAULT_SPLIT = {"y2": YieldSplit(0.0, 0.5, 0.9), "y10": YieldSplit(0.0, 0.6, 0.5)}

# Maps from the GDP z score when the registry has no row (assumption, v0): level = base + slope x (-zG).
ZG_MAP = {
    "index_spread": (0.045, 0.015),   # 450 bp at trend; 150 bp wider per -1 sd
    "default_rate": (0.035, 0.015),   # 3.5% at trend; +1.5 points per -1 sd
    "pmi": (50.0, -4.0),              # 50 at trend; 50 + 4 zG
}
LOGGED_LEVELS = {"policy_rate": 0.04, "term_spread": 0.0075}  # last resort constants (assumption, v0)

# Phase prior over the five paths. v0, calibrate. Rows sum to 1.
PHASE_PRIOR: dict[str, dict[str, float]] = {
    "expansion": dict(zip(PATH_NAMES, (0.45, 0.10, 0.20, 0.20, 0.05))),
    "late_cycle": dict(zip(PATH_NAMES, (0.30, 0.25, 0.25, 0.10, 0.10))),
    "downturn": dict(zip(PATH_NAMES, (0.15, 0.45, 0.10, 0.20, 0.10))),
    "repair": dict(zip(PATH_NAMES, (0.35, 0.20, 0.15, 0.25, 0.05))),
    "recovery": dict(zip(PATH_NAMES, (0.45, 0.10, 0.15, 0.25, 0.05))),
}

DEFAULT_SOURCES: dict[str, tuple[str, ...]] = {
    "gdp_growth": ("spf", "consensus"),
    "cpi": ("spf", "consensus"),
    "policy_rate": ("fomc_sep",),
    "y2": ("ust_forward",),
    "y10": ("ust_forward",),
    "hy_spread": (),       # empty: any source, in sorted order
    "default_rate": (),
    "pmi": (),
}
MARKET_SOURCES: dict[str, tuple[str, ...]] = {"policy_rate": ("ust_forward",)}


# ---------------------------------------------------------------------------
# Regions of the (zG, zC) plane
# ---------------------------------------------------------------------------


def regions(c: float = CUT) -> dict[str, tuple[float, float, float, float]]:
    """Rectangles (g_lo, g_hi, c_lo, c_hi) on the standardised plane, one per path.

    recession: zG < -c and zC <= c. stagflation: zG < -c and zC > c. higher_for_longer: zG >= -c and zC > c.
    disinflation_rally: zG >= -c and zC < -c. soft_landing: the rest (zG >= -c and -c <= zC <= c).
    Intuition: a path is a corner of the growth and inflation plane; the middle is the soft landing.
    """
    inf = np.inf
    return {
        "soft_landing": (-c, inf, -c, c),
        "recession": (-inf, -c, -inf, c),
        "higher_for_longer": (-c, inf, c, inf),
        "disinflation_rally": (-c, inf, -inf, -c),
        "stagflation": (-inf, -c, c, inf),
    }


def region_stats(m_g: float, m_c: float, s_g: float, s_c: float, rho: float = RHO_DEFAULT,
                 c: float = CUT) -> pd.DataFrame:
    """Mass and conditional mean of each region under (zG, zC) ~ N((m_g, m_c), [[s_g^2, r s_g s_c], [., s_c^2]]).

    Formula: P(R) = integral over g of phi_G(g) [Phi(b(g)) - Phi(a(g))] dg, with zC given zG = g normal with mean
    mu(g) = m_c + rho s_c (g - m_g) / s_g and sd s = s_c sqrt(1 - rho^2); a, b are the standardised zC bounds.
    E[zC 1_R] adds the inner closed form mu(g) dPhi + s (phi(a) - phi(b)).
    Intuition: integrate the inner axis in closed form and the outer axis by quadrature, so the five masses add to 1.
    Returns a frame indexed by path with `mass`, `zg_mean`, `zc_mean`.
    """
    if not abs(rho) < 0.99:
        raise ValueError(f"rho={rho} must lie inside (-0.99, 0.99)")
    if s_g <= 0 or s_c <= 0:
        raise ValueError("scales must be positive")
    s_cond = s_c * np.sqrt(1.0 - rho**2)
    lo_g, hi_g = m_g - 12 * s_g, m_g + 12 * s_g
    out = {}
    for name, (g1, g2, c1, c2) in regions(c).items():
        a_, b_ = max(g1, lo_g), min(g2, hi_g)
        if a_ >= b_:
            out[name] = (0.0, np.nan, np.nan)
            continue

        def inner(g, c1=c1, c2=c2):
            mu = m_c + rho * s_c * (g - m_g) / s_g
            a, b = (c1 - mu) / s_cond, (c2 - mu) / s_cond
            dphi = norm.cdf(b) - norm.cdf(a)
            return norm.pdf(g, m_g, s_g), mu, dphi, norm.pdf(a) - norm.pdf(b)

        def f_p(g):
            w, _, d, _ = inner(g)
            return w * d

        def f_g(g):
            w, _, d, _ = inner(g)
            return g * w * d

        def f_c(g):
            w, mu, d, e = inner(g)
            return w * (mu * d + s_cond * e)

        pts = [x for x in (-c, m_g) if a_ < x < b_]
        kw = dict(points=pts or None, limit=200, epsabs=1e-12, epsrel=1e-10)
        p = integrate.quad(f_p, a_, b_, **kw)[0]
        eg = integrate.quad(f_g, a_, b_, **kw)[0]
        ec = integrate.quad(f_c, a_, b_, **kw)[0]
        out[name] = (p, eg / p if p > 1e-14 else np.nan, ec / p if p > 1e-14 else np.nan)
    df = pd.DataFrame.from_dict(out, orient="index", columns=["mass", "zg_mean", "zc_mean"]).loc[list(PATH_NAMES)]
    tot = df["mass"].sum()
    if abs(tot - 1.0) > 1e-6:
        raise ArithmeticError(f"region masses sum to {tot}")
    df["mass"] = df["mass"] / tot
    return df


def estimate_rho(history: pd.DataFrame, x: str = "gdp_growth", y: str = "cpi", bounds=(-0.9, 0.9)) -> float:
    """Correlation of GDP and CPI forecast errors (or realised deviations) from history, clipped to `bounds`.

    Pass columns `<x>_error` and `<y>_error` when present; else the function uses `x` and `y` deviations.
    Intuition: when growth surprises come with inflation surprises of the opposite sign, stagflation is rarer.
    """
    cx, cy = (f"{x}_error", f"{y}_error") if f"{x}_error" in history else (x, y)
    d = history[[cx, cy]].dropna()
    if len(d) < 8:
        return RHO_DEFAULT
    return float(np.clip(np.corrcoef(d[cx], d[cy])[0, 1], *bounds))


def reference_from_history(history: pd.DataFrame) -> dict[str, tuple[float, float]]:
    """Anchor (median) and scale (standard deviation) per axis from realised history; else the defaults.

    Intuition: a recession is a growth rate far below the usual one, so the usual one sets the axis.
    """
    ref = dict(REFERENCE)
    for v in ref:
        if v in history and history[v].notna().sum() >= 8:
            s = history[v].dropna()
            ref[v] = (float(s.median()), float(s.std(ddof=1)))
    return ref


def widen_from_report(report: pd.DataFrame) -> dict[tuple[str, str], float]:
    """(source, variable) -> widen factor from an error report of `ForecastRegistry.error_report`.

    The caller must build the report from rows whose horizon matured before the decision time.
    Intuition: pool the horizons, weight coverage by count, and widen the bands of a source that misses.
    """
    out = {}
    for (s, v), g in report.groupby(["source", "variable"]):
        n = int(g["n"].sum())
        cov = float(np.average(g["coverage_80"].astype(float), weights=g["n"])) if n else np.nan
        out[(s, v)] = widen_factor(cov, n)
    return out


# ---------------------------------------------------------------------------
# Phase vote (framework F6)
# ---------------------------------------------------------------------------

INDICATORS = ("hy_oas", "distress_ratio", "sloos_tightening", "pmi", "default_rate", "issuance_quality")


def _vote(name: str, x) -> bool | None:
    """One indicator vote: True for late cycle or downturn, False otherwise, None when not available."""
    if x is None:
        return None
    if isinstance(x, (bool, np.bool_)):
        return bool(x)
    if name == "hy_oas":
        return bool(x["level"] > x["median_5y"] and x["change_3m"] > 0)
    if name == "distress_ratio":
        return bool(x["level"] > x["median_5y"])
    if name == "sloos_tightening":
        last2 = list(x)[-2:]
        return bool(len(last2) == 2 and all(v > 0 for v in last2))
    if name == "pmi":
        return bool(float(x) < 50)
    if name == "default_rate":
        return bool(x["fcst"] > x["ttm"])
    if name == "issuance_quality":
        return bool(x["ccc_share"] > x["ccc_median"] and x["covlite_share"] > x["covlite_median"])
    raise KeyError(name)


def late_count(votes: Mapping[str, bool | None]) -> float:
    """Late-cycle vote count on a six-indicator basis: count x 6 / available. NaN when none is available.

    Intuition: two late votes out of three readings carry the same weight as four out of six.
    """
    avail = [v for v in votes.values() if v is not None]
    return float(sum(avail) * len(INDICATORS) / len(avail)) if avail else float("nan")


def phase_vote(indicators: Mapping[str, object], prior_phase: str | None = None,
               prior_count: float | None = None) -> tuple[str, dict[str, bool | None]]:
    """Classify the macro phase by the six-indicator vote of framework F6. Returns (phase, votes).

    Indicator inputs (each one may also be a bool, or None when not available):
    - hy_oas: {"level", "median_5y", "change_3m"}. Late when above the five-year median and up over three months.
    - distress_ratio: {"level", "median_5y"}. Late when above the median.
    - sloos_tightening: sequence of quarterly net tightening. Late when the last two are positive.
    - pmi: level. Late when below 50.
    - default_rate: {"fcst", "ttm"}. Late when the forecast is above the trailing twelve months.
    - issuance_quality: {"ccc_share", "ccc_median", "covlite_share", "covlite_median"}. Late when both are above.

    Rule. Let n be `late_count(votes)`. Map n: 0 to 1 expansion, 2 to 3 late_cycle, 4 or more downturn
    (n >= 3.5 after the scale to six counts as 4). With a prior phase and its count:
    - A downturn count always gives downturn.
    - After downturn or repair, a lower count gives repair when n maps to late_cycle, and recovery when n maps
      to expansion.
    - Repair with a flat count stays repair.
    - Recovery with a lower count stays recovery. Recovery with a flat or higher count takes the mapped phase.
    With no available indicator, the phase is the prior phase, else late_cycle (the neutral row).
    Intuition: the same vote count means repair on the way down from a downturn and late cycle on the way up.
    """
    votes = {k: _vote(k, indicators.get(k)) for k in INDICATORS}
    n = late_count(votes)
    if n != n:
        return (prior_phase or "late_cycle"), votes
    raw = "expansion" if n < 1.5 else ("late_cycle" if n < 3.5 else "downturn")
    if prior_phase is None or prior_count is None or raw == "downturn":
        return raw, votes
    falling = n < prior_count
    if prior_phase in ("downturn", "repair") and falling:
        return ("repair" if raw == "late_cycle" else "recovery"), votes
    if prior_phase == "repair" and n == prior_count and raw == "late_cycle":
        return "repair", votes
    if prior_phase == "recovery" and falling:
        return "recovery", votes
    return raw, votes


# ---------------------------------------------------------------------------
# Bayesian combination
# ---------------------------------------------------------------------------


def bayes_update(prior: Mapping[str, float], mass: Mapping[str, float]) -> tuple[dict[str, float], dict[str, float]]:
    """Posterior over paths and the log likelihood ratio per path. Returns (posterior, llr).

    Formula: p(m | F) = pi(m) L(m) / sum_k pi(k) L(k), with the quantile mass L(m) as the likelihood of the
    forecast evidence F under path m. llr(m) = log L(m) - log sum_k pi(k) L(k) = log p(m | F) - log pi(m).
    Intuition: the forecast moves weight toward the paths it makes more likely than the phase prior expects.
    """
    names = list(prior)
    if set(names) != set(mass):
        raise ValueError("prior and mass must cover the same paths")
    pi = np.array([prior[k] for k in names], dtype=float)
    lk = np.array([mass[k] for k in names], dtype=float)
    if (pi < 0).any() or (lk < 0).any():
        raise ValueError("negative probability")
    ev = float(pi @ lk)
    if ev <= 0:
        raise ValueError("prior and mass have no common support")
    post = pi * lk / ev
    with np.errstate(divide="ignore"):
        llr = np.log(lk) - np.log(ev)
    return dict(zip(names, post / post.sum())), dict(zip(names, llr))


# ---------------------------------------------------------------------------
# Path set
# ---------------------------------------------------------------------------


@dataclass
class PathSet:
    """Named macro paths with prior, quantile mass, posterior, phase, sources, and logged assumptions (Section 5.4).

    `sources[variable] = (source, vintage, available_at, method)`. A fallback has the tier name as source.
    """

    paths: list[MacroPath]
    prior: dict[str, float]
    mass: dict[str, float]
    posterior: dict[str, float]
    llr: dict[str, float]
    phase: str
    votes: dict[str, bool | None]
    sources: dict[str, tuple]
    assumptions: list[str]
    decision_time: datetime
    region: pd.DataFrame = field(default_factory=pd.DataFrame)

    def probs(self) -> pd.DataFrame:
        """One row per path: prior, mass, posterior, llr."""
        return pd.DataFrame({"prior": self.prior, "mass": self.mass, "posterior": self.posterior,
                             "llr": self.llr}).loc[list(PATH_NAMES)]

    def path(self, name: str) -> MacroPath:
        return next(p for p in self.paths if p.name == name)


def path_prob_changes(old: PathSet, new: PathSet) -> pd.DataFrame:
    """Per-path change in prior, mass, and posterior between two path sets (revision tracking, signal S7).

    Formula: d_x(m) = x_new(m) - x_old(m) for x in (prior, mass, posterior). Each column sums to zero.
    Intuition: a move in the recession posterior is macro news; S7 trades the news, not the level.
    """
    a, b = old.probs(), new.probs()
    out = pd.DataFrame({f"d_{k}": b[k] - a[k] for k in ("prior", "mass", "posterior")})
    out["posterior_old"], out["posterior_new"] = a["posterior"], b["posterior"]
    out.index.name = "path"
    return out


class _Reader:
    """Reads one `as_of` snapshot of the registry and resolves each variable through the fallback order."""

    def __init__(self, registry: ForecastRegistry, t: datetime, sources: Mapping[str, Sequence[str]],
                 horizon: int, log: list[str], rec: dict[str, tuple]) -> None:
        self.t, self.horizon, self.log, self.rec = t, horizon, log, rec
        self.snap = registry.as_of(t)
        assert_no_lookahead(self.snap, t)
        self.sources = sources

    def pick(self, variable: str, order: Sequence[str]) -> pd.DataFrame:
        df = self.snap[self.snap["variable"] == variable] if len(self.snap) else self.snap
        if df.empty:
            return df
        for s in list(order) or sorted(df["source"].unique()):
            hit = df[df["source"] == s]
            if len(hit):
                return hit.sort_values("horizon_q")
        return df.iloc[0:0]

    def curve(self, rows: pd.DataFrame, col: str) -> np.ndarray:
        """Values for path quarters 1..H, aligned from the vintage quarter to the decision quarter.

        horizon_q counts from the vintage quarter, so path quarter k reads horizon_q = k + offset. Missing horizons
        take linear interpolation and flat extrapolation.
        """
        v = rows[col].where(rows[col].notna(), rows["point"]).astype(float)
        vint = pd.Timestamp(rows["vintage"].max())
        offset = (pd.Timestamp(self.t).to_period("Q") - vint.to_period("Q")).n
        k = np.arange(1, self.horizon + 1) + offset
        ok = v.notna().to_numpy()
        if not ok.any():
            return np.full(self.horizon, np.nan)
        return np.interp(k, rows["horizon_q"].to_numpy(dtype=float)[ok], v.to_numpy()[ok])

    def record(self, variable: str, rows: pd.DataFrame, method_suffix: str = "") -> None:
        r = rows.iloc[-1]
        meth = str(r["method"]) + (f"; {method_suffix}" if method_suffix else "")
        self.rec[variable] = (str(r["source"]), pd.Timestamp(rows["vintage"].max()),
                              pd.Timestamp(rows["available_at"].max()), meth)

    def fallback(self, variable: str, tier: str, what: str) -> None:
        if tier not in FALLBACK_ORDER:
            raise ValueError(tier)
        self.rec[variable] = (tier, None, None, what)
        self.log.append(f"{variable}: {tier} ({' > '.join(FALLBACK_ORDER)}): {what}")


def _normal_curve(reader: _Reader, variable: str, widen: Mapping[tuple[str, str], float],
                  reference: Mapping[str, tuple[float, float]]):
    """Median and sigma per path quarter for one variable: sigma = w (q90 - q10) / (2 x 1.2816).

    Intuition: the 10th to 90th percentile band of a normal spans 2.56 sigma, so the band gives sigma.
    Returns (mu, sigma, found).
    """
    anchor, scale = reference[variable]
    rows = reader.pick(variable, reader.sources[variable])
    if rows.empty:
        reader.fallback(variable, "logged_assumption",
                        f"no forecast row; median = anchor {anchor:.4f}, sigma = reference scale {scale:.4f}")
        return np.full(reader.horizon, anchor), np.full(reader.horizon, scale), False
    mu = reader.curve(rows, "q50")
    w = float(widen.get((str(rows["source"].iloc[-1]), variable), 1.0))
    if rows["q10"].notna().any() and rows["q90"].notna().any():
        lo, hi = reader.curve(rows, "q10"), reader.curve(rows, "q90")
        sig = np.maximum(w * (hi - lo) / (2 * Z80), 1e-6)
        reader.record(variable, rows, f"normal from q10 q50 q90, widen {w:.3f}")
    else:
        sig = np.full(reader.horizon, w * scale)
        reader.record(variable, rows, f"point only, widen {w:.3f}")
        reader.log.append(f"{variable}: logged_assumption: no quantiles; sigma = reference scale {scale:.4f}")
    return mu, sig, True


def build_paths(
    registry: ForecastRegistry,
    decision_time: datetime,
    *,
    phase_indicators: Mapping[str, object],
    history: pd.DataFrame | None = None,
    widen: Mapping[tuple[str, str], float] | None = None,
    rho: float = RHO_DEFAULT,
    horizon: int = HORIZON_Q,
    sources: Mapping[str, Sequence[str]] | None = None,
    reference: Mapping[str, tuple[float, float]] | None = None,
    taylor: Mapping[str, float] | None = None,
    prior_phase: str | None = None,
    prior_count: float | None = None,
    cut: float = CUT,
) -> PathSet:
    """Build the five macro paths at `decision_time` from forecast rows readable at that time (Section 5.4, 9.2).

    Steps and formulas
    1. Per variable X in (gdp_growth, cpi) and path quarter h: X_h ~ N(mu_h, sigma_h). Average over h to one
       normal, mu_bar and sigma_bar (the averages treat the horizons as comonotone, a stated assumption).
    2. Plane: z = (X - anchor) / scale. Under the forecast, (zG, zC) has mean ((mu_bar - a) / s) and sd
       (sigma_bar / s) with correlation rho. mass(m) = P(region m). Intuition: a weak growth median moves the
       forecast cloud into the recession corner.
    3. Path levels: u(m) = E[(X - mu_bar) / sigma_bar | region m]; X_h(m) = mu_h + sigma_h u(m). Intuition: each
       path sits at the centre of its corner, measured in the units of each horizon's own band.
    4. Policy: P_h(m) = P_h + max(-P_h, a_pi dC_h(m) + a_y dG_h(m)), with dX_h(m) = X_h(m) - mu_h. Intuition: the
       Fed leans against inflation more than against growth; the floor keeps the rate at or above zero.
    5. Yields per tenor: y_h(m) = fwd_h + dy_h(m), dy = b_g dG + b_p dP; dy^growth = b_g dG and
       dy^policy = dy - dy^growth (events.split_yield_change), so the parts add to dy exactly.
    6. Spread, default rate, PMI: base_h + slope x -(zG_h(m) - zG_h(median)) when the registry has the variable,
       else the ZG_MAP level at zG_h(m).
    7. Phase from `phase_vote`; prior from PHASE_PRIOR; posterior from `bayes_update`.

    `history` (optional) holds columns `d_growth_fcst`, `d_policy_exp` and `dy2`, `dy10` (or `dy` for both); with at
    least 8 rows the builder fits a YieldSplit per tenor with events.fit_yield_split.
    The function reads the registry only through one `registry.as_of(decision_time)` call.
    """
    log: list[str] = []
    rec: dict[str, tuple] = {}
    src = {**DEFAULT_SOURCES, **(sources or {})}
    if reference is None and history is not None and {"gdp_growth", "cpi"} & set(history.columns):
        ref = reference_from_history(history)  # realised history sets the axis (decision page, path construction)
        log.append(f"reference from realised history: {ref}")
    else:
        ref = {**REFERENCE, **(reference or {})}
        if reference is None:
            log.append(f"logged_assumption: reference point {REFERENCE} (no realised history passed)")
    tay = {**TAYLOR, **(taylor or {})}
    widen = widen or {}
    rd = _Reader(registry, decision_time, src, horizon, log, rec)

    # 1-3. Quantile mass and the GDP and CPI paths.
    (aG, sG_ref), (aC, sC_ref) = ref["gdp_growth"], ref["cpi"]
    muG, sigG, okG = _normal_curve(rd, "gdp_growth", widen, ref)
    muC, sigC, okC = _normal_curve(rd, "cpi", widen, ref)
    log.append(f"plane: anchors gdp {aG:.4f} cpi {aC:.4f}; scales gdp {sG_ref:.4f} cpi {sC_ref:.4f}; "
               f"rho {rho}; cut {cut}; horizons averaged as comonotone")
    mG, mC = (muG.mean() - aG) / sG_ref, (muC.mean() - aC) / sC_ref
    sg, sc = sigG.mean() / sG_ref, sigC.mean() / sC_ref
    reg = region_stats(mG, mC, sg, sc, rho, cut)
    if okG or okC:
        mass = reg["mass"].to_dict()
    else:
        mass = {k: 1.0 / len(PATH_NAMES) for k in PATH_NAMES}
        rd.fallback("path_mass", "f6_table", "no GDP or CPI forecast; flat likelihood, posterior = F6 phase prior")
    uG = (reg["zg_mean"] - mG) / sg
    uC = (reg["zc_mean"] - mC) / sc

    # 4. Policy rate base path.
    pol_rows = rd.pick("policy_rate", src["policy_rate"])
    if len(pol_rows):
        pol = rd.curve(pol_rows, "q50")
        rd.record("policy_rate", pol_rows)
    else:
        mk = rd.pick("policy_rate", MARKET_SOURCES["policy_rate"])
        if len(mk):
            pol = rd.curve(mk, "q50")
            rd.record("policy_rate", mk, "market_implied fallback")
            log.append(f"policy_rate: market_implied ({' > '.join(FALLBACK_ORDER)}): {mk['source'].iloc[-1]} forward")
        else:
            pol = np.full(horizon, LOGGED_LEVELS["policy_rate"])
            rd.fallback("policy_rate", "logged_assumption", f"flat {LOGGED_LEVELS['policy_rate']:.4f}")
    log.append(f"policy shift: d_policy = {tay['a_pi']} x d_cpi + {tay['a_y']} x d_gdp, floor at zero")

    # 5. Forward curve and yield split per tenor.
    fwd = {}
    for ten in ("y2", "y10"):
        rows = rd.pick(ten, src[ten])
        if len(rows):
            fwd[ten] = rd.curve(rows, "q50")
            rd.record(ten, rows)
        else:
            add = 0.0 if ten == "y2" else LOGGED_LEVELS["term_spread"]
            fwd[ten] = pol + add
            rd.fallback(ten, "logged_assumption", f"policy path + {add:.4f}")
    split = _yield_splits(history, log)

    # 6. Base levels for spread, default rate, PMI.
    zG_med = (muG - aG) / sG_ref
    base = {}
    for var, reg_var in (("index_spread", "hy_spread"), ("default_rate", "default_rate"), ("pmi", "pmi")):
        rows = rd.pick(reg_var, src.get(reg_var, ()))
        lvl, slope = ZG_MAP[var]
        if len(rows):
            base[var] = ("registry", rd.curve(rows, "q50"))
            rd.record(var, rows, f"path shift {slope} x -(zG - zG_median)")
            log.append(f"{var}: logged_assumption: path shift slope {slope} per -1 sd of GDP")
        else:
            base[var] = ("map", None)
            rd.fallback(var, "logged_assumption", f"level {lvl} + {slope} x -zG")

    # Build paths.
    phase, votes = phase_vote(phase_indicators, prior_phase, prior_count)
    prior = dict(PHASE_PRIOR[phase])
    posterior, llr = bayes_update(prior, mass)
    paths = []
    for m in PATH_NAMES:
        g = muG + sigG * (uG[m] if np.isfinite(uG[m]) else 0.0)
        cpi = muC + sigC * (uC[m] if np.isfinite(uC[m]) else 0.0)
        dG, dC = g - muG, cpi - muC
        p = np.maximum(pol + tay["a_pi"] * dC + tay["a_y"] * dG, 0.0)
        dP = p - pol
        extra: dict[str, np.ndarray] = {"cpi": cpi, "d_gdp": dG, "d_cpi": dC, "d_policy": dP}
        ys = {}
        for ten in ("y2", "y10"):
            sp = split[ten]
            dy = sp.b_growth * dG + sp.b_policy * dP
            gpart, ppart = split_yield_change(sp, dy, dG)
            ys[ten] = fwd[ten] + dy
            extra[f"dy_{ten}"], extra[f"dy_growth_{ten}"], extra[f"dy_policy_{ten}"] = dy, gpart, ppart
        extra["dy"], extra["dy_growth"], extra["dy_policy"] = extra["dy_y10"], extra["dy_growth_y10"], extra["dy_policy_y10"]
        zG = (g - aG) / sG_ref
        extra["zG"] = zG
        lv = {}
        for var, (kind, b) in base.items():
            lvl, slope = ZG_MAP[var]
            lv[var] = b + slope * -(zG - zG_med) if kind == "registry" else lvl + slope * -zG
            if var != "pmi":
                lv[var] = np.maximum(lv[var], 0.0)
        paths.append(MacroPath(m, posterior[m], ys["y2"], ys["y10"], p, g, lv["pmi"], lv["index_spread"],
                               lv["default_rate"], extra))
    validate_paths(paths)
    return PathSet(paths, prior, mass, posterior, llr, phase, votes, rec, log, decision_time, reg)


def _yield_splits(history: pd.DataFrame | None, log: list[str]) -> dict[str, YieldSplit]:
    """YieldSplit per tenor from history with events.fit_yield_split, else the logged defaults."""
    out = {}
    for ten, col in (("y2", "dy2"), ("y10", "dy10")):
        c = col if history is not None and col in history else "dy"
        if history is not None and {c, "d_growth_fcst", "d_policy_exp"} <= set(history.columns):
            h = history[[c, "d_growth_fcst", "d_policy_exp"]].dropna()
            if len(h) >= 8:
                out[ten] = fit_yield_split(h[c].to_numpy(), h["d_growth_fcst"].to_numpy(), h["d_policy_exp"].to_numpy())
                log.append(f"yield split {ten}: fitted on {len(h)} rows: b_g {out[ten].b_growth:.3f}, "
                           f"b_p {out[ten].b_policy:.3f}")
                continue
        out[ten] = DEFAULT_SPLIT[ten]
        log.append(f"yield split {ten}: logged_assumption ({' > '.join(FALLBACK_ORDER)}): default b_g "
                   f"{out[ten].b_growth}, b_p {out[ten].b_policy}")
    return out


# ---------------------------------------------------------------------------
# Spread betas by rating bucket and sector (Section 9.2)
# ---------------------------------------------------------------------------


def fit_beta_table(panel: pd.DataFrame, min_n: int = 8) -> pd.DataFrame:
    """beta_g and beta_p per (rating_bucket, sector) from the two-factor split of Section 9.2.

    Formulas: dy = a + b_g dG + b_p dP + e (events.fit_yield_split); dy^growth = b_g dG and
    dy^policy = dy - dy^growth (events.split_yield_change); ds = c + beta_g dy^growth + beta_p dy^policy + e
    (events.fit_spread_betas). Expected signs: beta_g < 0 < beta_p.
    Intuition: growth-driven yield rises tighten credit; policy-driven rises widen it.
    The function flags a cell whose signs fail or whose count is below `min_n`. It does not raise.
    Panel columns: date, rating_bucket, sector, ds, dy, d_growth_fcst, d_policy_exp.
    """
    rows = []
    for (rb, sec), g in panel.groupby(["rating_bucket", "sector"], sort=True):
        g = g.dropna(subset=["ds", "dy", "d_growth_fcst", "d_policy_exp"])
        n = len(g)
        if n < min_n:
            rows.append(dict(rating_bucket=rb, sector=sec, beta_g=np.nan, beta_p=np.nan, b_growth=np.nan,
                             b_policy=np.nan, n=n, sign_ok=False, flag="too_few"))
            continue
        sp = fit_yield_split(g["dy"].to_numpy(), g["d_growth_fcst"].to_numpy(), g["d_policy_exp"].to_numpy())
        gp, pp = split_yield_change(sp, g["dy"].to_numpy(), g["d_growth_fcst"].to_numpy())
        bg, bp = fit_spread_betas(g["ds"].to_numpy(), gp, pp)
        ok = bool(bg < 0 < bp)
        rows.append(dict(rating_bucket=rb, sector=sec, beta_g=bg, beta_p=bp, b_growth=sp.b_growth,
                         b_policy=sp.b_policy, n=n, sign_ok=ok, flag="" if ok else "sign_fail"))
    return pd.DataFrame(rows)
