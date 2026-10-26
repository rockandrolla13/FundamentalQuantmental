"""F06 Within-issuer curve residual on par-adjusted spread (rank 6). Spec docs/factors/F06-issuer-curve-residual.md;
methodology Section 8 (S4 capital structure relative value) and Section 6.2 (recovery). Sources: Osband and Goulden
(J.P. Morgan, 2012), PDF pp. 6 to 13 and 22; Martin, "The credit spread curve", PDF pp. 6, 11 to 15, 19 to 20;
stat-arb bridge note, PDF pp. 3 to 4. Pages are PDF pages.

    P/100 - 1   = (c - rhat(T) - s) Pi(T)                         par-adjusted spread s (Martin eq. 9, p. 12)
    Phat/100    = c Pi(T) + B(T) Q(T) + R Xi(T),  Q(t) = e^(-lam t)  flat hazard lam solves Phat = P (eq. 1, p. 6)
    R           = (70 - 3 r)%,  r the linear rating                 recovery falls with rating (p. 19)
    shat_-b(T)  = a0 + a1 (1 - e^(-0.4 T)) / (0.4 T)                forward shock curve, fit without bond b (JPM p. 22)
    e_b         = s_b - shat_-b(T_b),  z_b = e_b / se_-b            residual, positive = cheap (bridge p. 3)
    score       = RV_b = e_b Pi_b(T_b - dt)                         price value of convergence (Martin eq. 20, p. 20)

Intuition: one issuer has one default process, so a bond off its own curve carries a technical that fades. The
par adjustment stops high-coupon bonds at 110 from looking cheap only because yield ignores recovery.

Tiers. `issuer`: MIN_ISSUER_BONDS or more bonds on the gvkey x seniority curve. `group_shape`: 2 to 4 bonds; the
slope a1 comes from the other issuers of the sector x rating class cell (within-issuer regression), the level a0 from
the issuer's other bonds. `single`: one bond, no score.

Calls. A callable bond priced at or above its call price trades to the call, so its spread to maturity is wrong:
`call_status` "itm", dropped. Without call data the call price is the proxy 100 x (1 + c/2).

Inputs. `bond_panel` is required. Optional: `treasury_curve` (production table 4.7: `date`, one column per tenor in
years, `available_at`; fallback: the panel's `tsy_yield` against `years`), a new panel `bond_terms` (`cusip`,
`seniority`, `callable`, `call_price` per 100, `available_at`), `ratings`, `leverage`, `gics`. Without `bond_panel`
the result is an empty frame.
"""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd
from scipy.optimize import brentq

from hy.backtest import decision_time, eligible, not_distressed
from hy.peers import (FALLBACK, MIN_PEERS, RATING_STALE_DAYS, fit_cutoffs, implied_class, rating_class,
                      sector_at)
from hy.sources.treasury import interpolate

SHOCK_LAMBDA = 0.4          # forward shock decay, expected life 2.5 years (JPM p. 22)
MIN_ISSUER_BONDS = 5        # bonds an issuer curve needs (JPM pp. 6, 8)
MIN_SHAPE_BONDS = 2         # fewest bonds for the group_shape tier (our choice, after reader B-F12)
ENTRY_BP, ENTRY_SE = 0.0030, 1.0      # base signal: 30 bp and 1 standard error (JPM p. 8)
STRICT_BP, STRICT_SE = 0.0040, 1.5    # strict signal: 40 bp and 1.5 standard errors (JPM pp. 10, 13)
HOLD = 2                    # holding period in months (JPM p. 8, pp. 16 to 17)
REC_BASE, REC_SLOPE = 0.70, 0.03      # recovery (70 - 3 r)% (Martin p. 19)
DEFAULT_NOTCH = 15          # B: notch when no class is known (our choice: the HY middle)
CLASS_NOTCH = {"IG": 10, "BB": 12, "B": 15, "CCC": 18}  # middle notch of an implied class (our choice)
GRID_STEP = 0.5             # trapezium step in years (Martin eq. 11, p. 12; p. 8 footnote 9)
LAMBDA_MAX = 5.0            # upper bound of the hazard search (our choice: a 99% one-year default rate)
PROXY_CALL_PREMIUM = 0.5    # proxy call price par + half a coupon (our choice, no source in the folder)

META = {
    "rank": 6,
    "name": "Within-issuer curve residual on par-adjusted spread",
    "level": "bond",
    "horizon_months": HOLD,
    "needs": ["bond_panel", "treasury_curve", "bond_terms", "ratings", "leverage", "gics"],
    "spec": "docs/factors/F06-issuer-curve-residual.md",
    "section": "8",
}

COLS = ["date", "cusip", "score", "available_at", "gvkey", "seniority", "status", "tier", "n_curve", "pas",
        "hazard", "recovery", "rpv01", "fit", "resid", "se", "z", "signal_base", "signal_strict", "call_status",
        "curve_source"]

NOTCHES = ["AAA", "AA+", "AA", "AA-", "A+", "A", "A-", "BBB+", "BBB", "BBB-", "BB+", "BB", "BB-",
           "B+", "B", "B-", "CCC+", "CCC", "CCC-", "CC", "C"]


# ---------------------------------------------------------------- formula helpers


def rating_notch(symbol: str | None) -> int | None:
    """Linear rating r of an S&P symbol: AAA 1, AA+ 2, ..., BBB- 10, BB 12, B 15, C 21, SD and D 22 (Martin p. 19)."""
    if not isinstance(symbol, str) or not symbol.strip():
        return None
    s = symbol.strip().upper()
    if s in ("SD", "D"):
        return 22
    return NOTCHES.index(s) + 1 if s in NOTCHES else None


def recovery_rate(notch: float) -> float:
    """Recovery (70 - 3 r)% of par, floored at 0 (spec Section 3; Martin p. 19). BBB- 40%, BB 34%, B 25%."""
    return max(REC_BASE - REC_SLOPE * float(notch), 0.0)


def discount_factors(curve_row: pd.Series, step: float = GRID_STEP, max_t: float = 30.0) -> tuple[np.ndarray, np.ndarray]:
    """Bootstrap semiannual discount factors on a `step` grid from a Treasury par curve (spec Section 3, our choice).

    A par bond with yield y_k and maturity t_k prices at 1: B_k = (1 - y_k/2 sum_{j<k} B_j) / (1 + y_k/2), on the
    0.5-year coupon grid. `curve_row` is a row with float tenor keys (`hy.sources.treasury` form). Returns (t, B)
    with t[0] = 0, B[0] = 1. Intuition: the price today of 1 dollar paid at t, read off Treasury par yields."""
    t_cpn = np.arange(0.5, max_t + 1e-9, 0.5)
    y = np.asarray(interpolate(curve_row, t_cpn), dtype=float)
    b = np.empty_like(t_cpn)
    acc = 0.0
    for k, yk in enumerate(y):
        b[k] = (1.0 - yk / 2.0 * acc) / (1.0 + yk / 2.0)
        acc += b[k]
    t_all = np.concatenate([[0.0], t_cpn])
    b_all = np.concatenate([[1.0], b])
    grid = np.arange(0.0, max_t + 1e-9, step)
    return grid, np.exp(np.interp(grid, t_all, np.log(b_all)))


def _disc(t: np.ndarray, grid: np.ndarray, b: np.ndarray) -> np.ndarray:
    """B(t) by linear interpolation of log B, flat forward rate beyond the grid end."""
    lb = np.log(b)
    fwd = (lb[-1] - lb[-2]) / (grid[-1] - grid[-2])
    return np.exp(np.where(t <= grid[-1], np.interp(t, grid, lb), lb[-1] + fwd * (t - grid[-1])))


def flat_hazard_legs(T: float, lam: float, disc, step: float = GRID_STEP) -> dict[str, float]:
    """Pi, Xi, rhat*Pi and B(T)Q(T) for Q(t) = e^(-lam t) by the trapezium rule (Martin eq. 11, p. 12).

    `disc(t)` returns B(t). The grid runs 0, step, 2 step, ... and ends at T. These sums satisfy the parity
    B(T)Q(T) + Xi + rhat Pi = 1 (eq. 8) exactly."""
    t = np.arange(0.0, T, step)
    t = np.append(t, T) if T - t[-1] > 1e-12 else t
    b, q = disc(t), np.exp(-lam * t)
    pi = float(np.sum((b[:-1] * q[:-1] + b[1:] * q[1:]) / 2.0 * np.diff(t)))
    xi = float(np.sum((b[:-1] + b[1:]) / 2.0 * (q[:-1] - q[1:])))
    r_pi = float(np.sum((q[:-1] + q[1:]) / 2.0 * (b[:-1] - b[1:])))
    return {"pi": pi, "xi": xi, "r_pi": r_pi, "bq": float(b[-1] * q[-1])}


def model_price(c: float, T: float, lam: float, recovery: float, disc, step: float = GRID_STEP) -> float:
    """Phat = 100 (c Pi + B(T)Q(T) + R Xi) (Martin eq. 1, p. 6). Coupon c is a decimal, paid continuously."""
    g = flat_hazard_legs(T, lam, disc, step)
    return 100.0 * (c * g["pi"] + g["bq"] + recovery * g["xi"])


def par_adjusted_spread(price: float, c: float, T: float, recovery: float, disc,
                        step: float = GRID_STEP) -> dict[str, float]:
    """Par-adjusted spread s of one bond (Martin eq. 9, p. 12) with a flat hazard fitted to its price.

    lam solves Phat(lam) = price. Then s = c - rhat - (P/100 - 1)/Pi, which equals (1 - R) Xi / Pi (eq. 7, p. 11).
    A price above the risk-free value takes lam = 0 (s <= 0). A price below Phat(LAMBDA_MAX) has no hazard: status
    "below_recovery" and NaN. Intuition: the running spread the bond would pay at par.
    Source check (p. 15): COLOM 4% '24 at 100.10 and 8.125% '24 at 125.50 with R = 0 give s = 258 and 298 bp."""
    nan = {"pas": np.nan, "hazard": np.nan, "rpv01": np.nan, "status": "no_price"}
    if not (np.isfinite(price) and np.isfinite(c) and np.isfinite(T)) or T <= 0 or price <= 0:
        return nan
    f = lambda lam: model_price(c, T, lam, recovery, disc, step) - price  # noqa: E731
    if f(LAMBDA_MAX) > 0:
        return {**nan, "status": "below_recovery"}
    lam = 0.0 if f(0.0) <= 0 else brentq(f, 0.0, LAMBDA_MAX, xtol=1e-10)
    g = flat_hazard_legs(T, lam, disc, step)
    s = c - g["r_pi"] / g["pi"] - (price / 100.0 - 1.0) / g["pi"]
    return {"pas": s, "hazard": lam, "rpv01": g["pi"], "status": "ok"}


def shock_basis(T: np.ndarray | float, lam: float = SHOCK_LAMBDA) -> np.ndarray:
    """x(T) = (1 - e^(-lam T)) / (lam T), the forward shock regressor (JPM p. 22). x(0) = 1, x falls to 0 in T.

    The source divides by T, not lam T. With lam fixed the constant goes into a1, so the fit is the same."""
    T = np.asarray(T, dtype=float)
    return -np.expm1(-lam * T) / (lam * T)


def _ols(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float]:
    """OLS y = a0 + a1 x. Returns a0, a1, and the standard error of the fit (n - 2 degrees of freedom)."""
    X = np.column_stack([np.ones_like(x), x])
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    dof = len(y) - 2
    se = float(np.sqrt(np.sum((y - X @ coef) ** 2) / dof)) if dof > 0 else np.nan
    return float(coef[0]), float(coef[1]), se


def loo_curve(T: np.ndarray, s: np.ndarray, lam: float = SHOCK_LAMBDA) -> tuple[np.ndarray, np.ndarray]:
    """Leave-one-out forward shock fit (spec Section 3; JPM p. 22, bridge p. 3).

    For each bond b: fit shat(T) = a0 + a1 x(T) on the other bonds, return shat_-b(T_b) and the fit standard error
    se_-b. Intuition: the bond is judged against a curve it did not shape."""
    x = shock_basis(T, lam)
    fit, se = np.full(len(s), np.nan), np.full(len(s), np.nan)
    for b in range(len(s)):
        keep = np.arange(len(s)) != b
        a0, a1, se[b] = _ols(x[keep], s[keep])
        fit[b] = a0 + a1 * x[b]
    return fit, se


def within_slope(x: np.ndarray, s: np.ndarray, issuer: np.ndarray) -> tuple[float, float, int]:
    """Curve slope a1 from within-issuer variation (spec Section 3, group_shape tier; our choice).

    Regress s - mean_i(s) on x - mean_i(x) over issuers with 2 or more bonds. Returns a1, the residual standard
    error (dof = n - issuers - 1) and the issuer count. Intuition: the group gives the shape, never the level."""
    d = pd.DataFrame({"x": x, "s": s, "i": issuer})
    d = d[d.groupby("i")["x"].transform("size") >= 2]
    if d.empty:
        return np.nan, np.nan, 0
    xd = d["x"] - d.groupby("i")["x"].transform("mean")
    sd = d["s"] - d.groupby("i")["s"].transform("mean")
    n_i = int(d["i"].nunique())
    sxx = float(np.sum(xd ** 2))
    if sxx <= 0:
        return np.nan, np.nan, n_i
    a1 = float(np.sum(xd * sd) / sxx)
    dof = len(d) - n_i - 1
    se = float(np.sqrt(np.sum((sd - a1 * xd) ** 2) / dof)) if dof > 0 else np.nan
    return a1, se, n_i


def call_status(price: float, coupon: float, callable_: object, call_price: float) -> str:
    """Call status (spec Section 3): "bullet", "otm" (callable, price below call price), "itm" (price at or above
    the call price: the bond trades to the call, dropped). Unknown terms use the proxy call price 100 (1 + c/2):
    "proxy_itm" (dropped) or "unknown"."""
    if callable_ is None or (isinstance(callable_, float) and np.isnan(callable_)):
        return "proxy_itm" if price >= 100.0 * (1.0 + PROXY_CALL_PREMIUM * coupon) else "unknown"
    if not bool(callable_):
        return "bullet"
    if not np.isfinite(call_price):
        return "proxy_itm" if price >= 100.0 * (1.0 + PROXY_CALL_PREMIUM * coupon) else "otm"
    return "itm" if price >= call_price else "otm"


# ---------------------------------------------------------------- panel steps


def _known(panels: Mapping[str, pd.DataFrame], name: str, dt: pd.Timestamp) -> pd.DataFrame | None:
    df = panels.get(name)
    if df is None or len(df) == 0:
        return None
    return df[df["available_at"] <= dt]


def _curve_row(bonds: pd.DataFrame, tsy: pd.DataFrame | None, as_of: pd.Timestamp) -> tuple[pd.Series, str, pd.Timestamp]:
    """Latest Treasury par curve at or before as_of, else the bond panel's (years, tsy_yield) pairs (spec step 2)."""
    if tsy is not None:
        t = tsy[pd.to_datetime(tsy["date"]) <= as_of].sort_values("date")
        if len(t):
            last = t.iloc[-1]
            pts = {}
            for k, v in last.items():
                try:
                    pts[float(k)] = float(v)
                except (TypeError, ValueError):
                    continue
            row = pd.Series(pts).dropna()
            if len(row) >= 2:
                return row, "treasury_curve", pd.Timestamp(last["available_at"])
    p = bonds.dropna(subset=["tsy_yield", "years"])
    row = p.groupby((p["years"] * 4).round() / 4)["tsy_yield"].median()
    row.index = row.index.astype(float)
    return row, "bond_panel", pd.Timestamp(p["available_at"].max())


def _issuer_rating(panels: Mapping[str, pd.DataFrame], dt: pd.Timestamp, gvkeys) -> pd.DataFrame:
    """Per gvkey: notch, class and its source (actual S&P, else leverage-implied, else none) (spec step 3)."""
    out = pd.DataFrame(index=pd.Index(pd.unique(gvkeys), name="gvkey"))
    out["notch"], out["rclass"], out["rclass_source"] = np.nan, None, "none"
    ratings = _known(panels, "ratings", dt)
    if ratings is not None:
        r = ratings[ratings["datadate"] >= dt - pd.Timedelta(RATING_STALE_DAYS, unit="D")]
        sym = r.sort_values("datadate").drop_duplicates("gvkey", keep="last").set_index("gvkey")["splticrm"]
        sym = sym.reindex(out.index)
        out["notch"] = sym.map(rating_notch).astype(float)
        out["rclass"] = sym.map(rating_class)
        out.loc[out["rclass"].notna(), "rclass_source"] = "actual"
    lev = _known(panels, "leverage", dt)
    if lev is not None and ratings is not None:
        hist = ratings.assign(rc=ratings["splticrm"].map(rating_class)).dropna(subset=["rc"]).merge(
            lev[["date", "gvkey", "leverage", "ltm_ebitda"]], left_on=["gvkey", "datadate"],
            right_on=["gvkey", "date"], how="inner")
        hist = hist[(hist["leverage"] > 0) & (hist["ltm_ebitda"].astype(float) > 0)]
        cut = fit_cutoffs(np.log(hist["leverage"].astype(float)), hist["rc"])
        now = lev.sort_values("date").drop_duplicates("gvkey", keep="last").set_index("gvkey")
        miss = out.index[out["rclass"].isna() & out.index.isin(now.index)]
        for g in miss:
            cls = implied_class(float(now.at[g, "leverage"]), float(now.at[g, "ltm_ebitda"]) > 0, cut)
            if cls is not None:
                out.at[g, "rclass"], out.at[g, "rclass_source"] = cls, "implied"
    fill = out["rclass"].map(CLASS_NOTCH)
    out["notch"] = out["notch"].fillna(fill).fillna(DEFAULT_NOTCH)
    gics = _known(panels, "gics", dt)
    out["sector"] = out.index.map(sector_at(gics, dt)) if gics is not None else None
    return out


def _cell(df: pd.DataFrame, level: str) -> pd.Series:
    """Group key at a FALLBACK level: sector x class ("sr"), class ("r"), sector ("s"), or all."""
    s, r = df["sector"].astype(str), df["rclass"].astype(str)
    key = {"sr": s + "|" + r, "r": r, "s": s, "all": pd.Series("all", index=df.index)}[level]
    bad = {"sr": df["sector"].isna() | df["rclass"].isna(), "r": df["rclass"].isna(), "s": df["sector"].isna(),
           "all": pd.Series(False, index=df.index)}[level]
    return key.where(~bad)


def _group_slope(ok: pd.DataFrame, row_curve: str, cell_row: pd.Series) -> tuple[float, float]:
    """Slope and standard error for one group_shape curve from the other issuers of its cell (FALLBACK chain)."""
    others = ok[ok["curve"] != row_curve]
    for level in FALLBACK["sr"]:
        key = cell_row.get(level)
        if level != "all" and (key is None or key != key):
            continue
        peer = others[others[f"cell_{level}"] == key] if level != "all" else others
        a1, se, n_i = within_slope(peer["x"].to_numpy(), peer["s"].to_numpy(), peer["curve"].to_numpy())
        if n_i >= MIN_PEERS and np.isfinite(a1):
            return a1, se
    return np.nan, np.nan


def compute(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp, horizon_months: int = HOLD,
            measure: str = "pas", bullets_only: bool = False) -> pd.DataFrame:
    """F06 score per bond at month end `as_of` (spec Sections 3 and 5; methodology Section 8 S4).

    measure "pas" uses the par-adjusted spread with RPV01. "g_spread" uses the G-spread with modified duration (the
    A2-F1 comparison). Returns one row per eligible bond with the COLS columns; NaN score where a step drops it."""
    as_of = pd.Timestamp(as_of)
    dt = decision_time(as_of)
    panel = _known(panels, "bond_panel", dt)
    if panel is None:
        return pd.DataFrame(columns=COLS)
    bonds = panel[pd.to_datetime(panel["date"]) == as_of]
    bonds = bonds[eligible(bonds) & not_distressed(bonds)].drop_duplicates("cusip", keep="last").copy()
    if bonds.empty:
        return pd.DataFrame(columns=COLS)

    terms = _known(panels, "bond_terms", dt)
    if terms is not None:
        t = terms.sort_values("available_at").drop_duplicates("cusip", keep="last").set_index("cusip")
        for col in ("seniority", "callable", "call_price"):
            if col in t:
                bonds[col] = bonds["cusip"].map(t[col])
    if "seniority" not in bonds:
        bonds["seniority"] = "unknown"
    bonds["seniority"] = bonds["seniority"].fillna("unknown")
    bonds["callable"] = bonds["callable"] if "callable" in bonds else None
    bonds["call_price"] = bonds["call_price"].astype(float) if "call_price" in bonds else np.nan
    bonds["call_status"] = [call_status(float(p), float(c), k, float(cp)) for p, c, k, cp in
                            zip(bonds["price"], bonds["coupon"], bonds["callable"], bonds["call_price"])]

    curve_row, curve_source, curve_avail = _curve_row(bonds, _known(panels, "treasury_curve", dt), as_of)
    grid, bgrid = discount_factors(curve_row)
    disc = lambda t: _disc(np.asarray(t, dtype=float), grid, bgrid)  # noqa: E731
    iss = _issuer_rating(panels, dt, bonds["gvkey"])
    bonds = bonds.join(iss, on="gvkey")
    bonds["recovery"] = bonds["notch"].map(recovery_rate)

    h = horizon_months / 12.0
    rows = []
    for r in bonds.itertuples(index=False):
        dropped = r.call_status in ("itm", "proxy_itm") or (bullets_only and r.call_status != "bullet")
        if measure == "g_spread":
            res = {"pas": float(r.g_spread), "hazard": np.nan, "rpv01": float(r.mod_dur), "status": "ok"}
            fwd = max(float(r.mod_dur) - h, 0.0)
        else:
            res = par_adjusted_spread(float(r.price), float(r.coupon), float(r.years), float(r.recovery), disc)
            fwd = (flat_hazard_legs(max(float(r.years) - h, 1e-6), res["hazard"], disc)["pi"]
                   if res["status"] == "ok" else np.nan)
        rows.append({**res, "fwd_pi": fwd, "status": "call" if dropped else res["status"]})
    bonds = pd.concat([bonds.reset_index(drop=True), pd.DataFrame(rows)], axis=1)
    bonds["curve"] = bonds["gvkey"].astype(str) + "|" + bonds["seniority"].astype(str)
    bonds["x"], bonds["s"] = shock_basis(bonds["years"].to_numpy(float)), bonds["pas"]
    for level in ("sr", "r", "s"):
        bonds[f"cell_{level}"] = _cell(bonds, level)

    ok = bonds[bonds["status"] == "ok"]
    n_curve = ok.groupby("curve").size()
    bonds["n_curve"] = bonds["curve"].map(n_curve).fillna(0).astype(int)
    bonds["tier"] = np.select([bonds["n_curve"] >= MIN_ISSUER_BONDS, bonds["n_curve"] >= MIN_SHAPE_BONDS],
                              ["issuer", "group_shape"], "single")
    bonds["fit"], bonds["se"] = np.nan, np.nan
    for curve, g in ok.groupby("curve"):
        idx = g.index
        if len(g) >= MIN_ISSUER_BONDS:
            fit, se = loo_curve(g["years"].to_numpy(float), g["s"].to_numpy(float))
        elif len(g) >= MIN_SHAPE_BONDS:
            first = g.iloc[0]
            a1, se_g = _group_slope(ok, curve, first[["cell_sr", "cell_r", "cell_s"]].rename(
                lambda c: c.removeprefix("cell_")))
            lvl = g["s"] - a1 * g["x"]
            a0 = (lvl.sum() - lvl) / (len(g) - 1)        # mean over the issuer's other bonds
            fit, se = (a0 + a1 * g["x"]).to_numpy(), np.full(len(g), se_g)
        else:
            continue
        bonds.loc[idx, "fit"], bonds.loc[idx, "se"] = fit, se

    bonds["resid"] = bonds["s"] - bonds["fit"]
    bonds["z"] = bonds["resid"] / bonds["se"]
    bonds["score"] = bonds["resid"] * bonds["fwd_pi"]
    a, z = bonds["resid"].abs(), bonds["z"].abs()
    bonds["signal_base"] = np.sign(bonds["resid"]).where((a >= ENTRY_BP) & (z >= ENTRY_SE), 0.0).fillna(0.0)
    bonds["signal_strict"] = np.sign(bonds["resid"]).where((a >= STRICT_BP) & (z >= STRICT_SE), 0.0).fillna(0.0)
    bonds["date"], bonds["curve_source"] = as_of, curve_source
    bonds["available_at"] = max(pd.Timestamp(bonds["available_at"].max()), curve_avail)
    return bonds[COLS].reset_index(drop=True)
