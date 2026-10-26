"""F02 spread to distance-to-default, with a CreditGrades variant. Spec docs/factors/F02-spread-to-d2d.md;
methodology Sections 7.1 (equity-implied PD) and 8 (S1 fair value residual). Kelly, Palhares and Pruitt (2021),
ssrn-3720789.pdf, PDF pp. 13 to 18 and 55. Bharath and Shumway (2008), repo card eqs. 8 to 12. Alber thesis,
CapArb/cap arb.pdf, PDF pp. 21 to 30.

Variant A (`score`, the primary):

    F      = debt_current + 0.5 * debt_long_term                                   (default point, B-S eq. 8)
    sig_V  = E/(E+F) * sig_E + F/(E+F) * (0.05 + 0.25 * sig_E)                     (naive asset vol, B-S eq. 10)
    DD     = [ln((E+F)/F) + (mu - 0.5 sig_V^2) T] / (sig_V sqrt T),  T = 1           (naive DD, B-S eq. 12)
    x_i    = log s_i - log Phi(-DD_j)                                               (spread per unit of PD, KPP p. 55)
    score  = rank of winsorised x within rating bucket (BB, B, CCC), mapped to [-0.5, 0.5]  (KPP p. 15)

Intuition: x is the spread the bond pays per unit of equity-implied default probability. A high x means a lot of
spread for little default risk, so the bond is cheap.

Variant B (`score_cg`, test second): the CreditGrades gap (Finger et al. 2002, exact form of Kiesel and Veraart 2008,
Alber eqs. 17 to 21).

    d      = (S + Lbar D)/(Lbar D) e^{lam^2},   A_t^2 = sig_A^2 t + lam^2
    P(t)   = Phi2(-lam/2 + ln d/lam, -A_t/2 + ln d/A_t; lam/A_t) - d Phi2(lam/2 + ln d/lam, -A_t/2 - ln d/A_t; -lam/A_t)
    s_CG   = -(1 - R) ln P(t) / t,  t = bond modified duration
    gap    = log s_mkt - log s_CG(mean implied sig_A over the past year)
    g      = sign(gap) (|gap| - mean_20 |gap|) / sd_20(gap), over the 20 prior gap days  (Alber p. 29)

Intuition: the market spread far above the equity-implied CreditGrades spread, by more than its usual gap, marks a
cheap bond. The bivariate term counts the default at once when the barrier is higher than expected.

Panels (all with `available_at`):
- `bond_panel` (have): date, cusip, gvkey, years, g_spread, mod_dur, price, yield, carried.
- `financials` (have, as a panel of production table 4.2): gvkey, period_end, debt_current, debt_long_term.
  Optional for Variant B: liabilities_total (Compustat ltq), minority_interest (mibq). USD millions.
- `equity_monthly` (have): gvkey, datadate, ret. It gives mu and the fallback sig_E.
- `market_value` (have, table 4.6 keyed by gvkey): gvkey, period_end, value (USD millions). Fallback E.
- `ratings` (have), `leverage` (have): the rating bucket, else the leverage-implied class (hy.peers).
- `equity_daily` (new, optional): gvkey, date, prc (USD), shrout (thousands, CRSP), ret. Trade day + 1 day.
- `bond_daily` (new, optional, Variant B only): cusip, date, g_spread. Trade day + 1 day.

Volatility: with at least 126 of the prior 252 daily returns, sig_E is their annualised standard deviation and mu
their compounded return. Without them, the row falls back to monthly data: sig_E from the last 36 monthly returns
(at least 24) times sqrt(12), and mu from the last 12. The column `vol_source` flags which one applies. Without
`equity_daily`, every row uses the monthly fallback, and `score_cg` is NaN. Without the required panels, compute
returns an empty frame with the output columns.
"""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd
from scipy.special import log_ndtr, ndtr, owens_t

from hy.backtest import decision_time, eligible
from hy.peers import fit_cutoffs, implied_class, rating_at, rating_class

T_YEARS = 1.0                     # DD horizon, Bharath and Shumway (card eq. 12). Spec "Our choice"
LT_DEBT_WEIGHT = 0.5              # F = current debt + half of long-term debt (card eq. 8)
SIG_D_BASE, SIG_D_SLOPE = 0.05, 0.25  # naive debt vol 0.05 + 0.25 sig_E (card eq. 9, journal p. 1347)
DAILY_WINDOW, DAILY_MIN = 252, 126    # prior 252 daily returns, at least 126 (spec Section 5 step 2)
DAYS_PER_YEAR = 252               # annualise daily vol
MONTHLY_WINDOW, MONTHLY_MIN = 36, 24  # monthly fallback: last 36 months, at least 24. Our choice (lead decision)
MU_MONTHS = 12                    # mu = stock return over the prior 12 months (card eq. 11)
EQUITY_STALE_DAYS = 7             # last daily price at most 7 days before month end. Our choice (bond_panel rule)
SPREAD_MIN, SPREAD_MAX = 0.005, 0.20  # keep 50 bp to 2000 bp (spec Section 5 step 4, KPP p. 15)
DUR_MIN = 0.25                    # keep duration >= 0.25 years (spec Section 5 step 4, KPP p. 15)
WINSOR = (0.01, 0.99)             # winsorise x at 1st and 99th percentiles (card, journal p. 1352)
HY_BUCKETS = ("BB", "B", "CCC")   # rating buckets of the within-bucket rank (spec Section 3)
CG_LBAR, CG_LAMBDA = 0.5, 0.3     # mean recovery on the barrier and its uncertainty (Alber PDF p. 21)
CG_RECOVERY = 0.3                 # bond recovery R (Alber PDF p. 24)
CG_OTHER_WEIGHT = 0.5             # D adds half of other liabilities (Alber PDF p. 22)
CG_MI_CAP = 0.5                   # minority interest deducted up to 50% of financial debt (Alber PDF p. 22)
CG_SIGMA_DAYS = 365               # price with the one-year mean of implied sig_A (Wojtowicz, Alber PDF p. 25)
CG_SIGMA_MIN = 126                # implied-sig days the mean needs. Our choice (same as DAILY_MIN)
CG_GAP_DAYS = 20                  # c = 20 days (Alber PDF p. 29)
CG_TRIGGER = 4.0                  # a = 4 (Alber PDF p. 29). In-sample choice of the source
CG_LOOKBACK_DAYS = 450            # daily rows read: one year of sig plus the 20-day gap window. Our choice
SIG_A_BOUNDS = (1e-4, 3.0)        # search range of the implied asset vol. Our choice
BISECT_STEPS = 60                 # halvings of the log range: error below 1e-15 in log sig. Our choice

META = {"rank": 2, "name": "Spread to distance-to-default (with a CreditGrades variant)", "level": "bond",
        "horizon_months": 1,
        "needs": ["bond_panel", "financials", "equity_monthly", "market_value", "ratings", "leverage",
                  "equity_daily", "bond_daily"],
        "spec": "docs/factors/F02-spread-to-d2d.md", "section": "7.1"}
REQUIRED = ("bond_panel", "financials")   # every other panel is optional and only removes coverage
COLUMNS = ["date", "cusip", "score", "available_at", "gvkey", "score_cg", "g_spread", "dd_equity", "log_pd_dd",
           "s2d_log", "s2d_rank", "s2d_rank_rb", "rating_bucket", "vol_source", "e_source", "cg_spread",
           "cg_spread_kv", "cg_gap", "cg_z", "cg_flag"]


# ---------------------------------------------------------------- Variant A formulas


def default_point(debt_current, debt_long_term) -> np.ndarray:
    """F = debt_current + 0.5 debt_long_term (spec Section 3, Bharath and Shumway eq. 8). A missing part counts as
    zero when the other part is present. Both missing gives NaN."""
    c, lt = np.asarray(debt_current, dtype=float), np.asarray(debt_long_term, dtype=float)
    f = np.nan_to_num(c) + LT_DEBT_WEIGHT * np.nan_to_num(lt)
    return np.where(np.isnan(c) & np.isnan(lt), np.nan, f)


def naive_sigma_v(E, F, sigma_e) -> np.ndarray:
    """sig_V = E/(E+F) sig_E + F/(E+F) (0.05 + 0.25 sig_E) (spec Section 3, Bharath and Shumway eq. 10).
    Intuition: a value-weighted mix of equity vol and a rough debt vol replaces the solved Merton asset vol."""
    E, F, s = (np.asarray(v, dtype=float) for v in (E, F, sigma_e))
    w = E / (E + F)
    return w * s + (1.0 - w) * (SIG_D_BASE + SIG_D_SLOPE * s)


def naive_dd(E, F, sigma_e, mu, r=None, T: float = T_YEARS) -> np.ndarray:
    """Naive DD = [ln((E+F)/F) + (mu - 0.5 sig_V^2) T] / (sig_V sqrt T) (Section 7.1, Bharath and Shumway eq. 12).

    mu is the prior-year stock return (eq. 11). Give `r` to use a risk-free drift instead. F <= 0 gives NaN.
    Intuition: DD counts the asset standard deviations between today and the default point."""
    E, F = np.asarray(E, dtype=float), np.asarray(F, dtype=float)
    drift = np.asarray(mu if r is None else r, dtype=float)
    sv = naive_sigma_v(E, F, sigma_e)
    with np.errstate(divide="ignore", invalid="ignore"):
        dd = (np.log((E + F) / F) + (drift - 0.5 * sv ** 2) * T) / (sv * np.sqrt(T))
    return np.where((F > 0) & (E > 0) & (sv > 0), dd, np.nan)


def spread_to_dd(g_spread, dd) -> np.ndarray:
    """x = log s - log Phi(-DD) (Sections 7.1 and 8 S1, KPP Table A.I, p. 55: OAS over one minus the CDF of DD).
    `log_ndtr` keeps the log PD finite for a large DD, so no PD floor is needed (spec Section 3)."""
    s = np.asarray(g_spread, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(s > 0, np.log(s), np.nan) - log_ndtr(-np.asarray(dd, dtype=float))


def winsorise(x: pd.Series, lo: float = WINSOR[0], hi: float = WINSOR[1]) -> pd.Series:
    """Clip x at its lo and hi quantiles on one date (spec Section 3, Bharath and Shumway p. 1352). NaN stays NaN."""
    q = x.quantile([lo, hi])
    return x.clip(q.iloc[0], q.iloc[1])


def centred_rank(x: pd.Series) -> pd.Series:
    """Cross-section rank mapped to [-0.5, 0.5] (spec Section 3, KPP p. 15): (rank - 1)/(n - 1) - 0.5, ties averaged.
    One value maps to 0. NaN stays NaN. Intuition: only the order counts, so outliers carry no extra weight."""
    n = x.notna().sum()
    if n == 0:
        return x * np.nan
    if n == 1:
        return x.where(x.isna(), 0.0)
    return (x.rank(method="average") - 1.0) / (n - 1.0) - 0.5


def annual_vol(r: np.ndarray, periods_per_year: int) -> float:
    """Annualised standard deviation of returns: sd(r) sqrt(periods_per_year) (Bharath and Shumway, sig_E)."""
    return float(np.std(r, ddof=1) * np.sqrt(periods_per_year))


def compound(r: np.ndarray) -> float:
    """Compounded return prod(1 + r) - 1 (Bharath and Shumway eq. 11, mu = prior-year stock return)."""
    return float(np.prod(1.0 + np.asarray(r, dtype=float)) - 1.0)


# ---------------------------------------------------------------- Variant B formulas


def cg_debt(debt_current, debt_long_term, liabilities_total=None, minority_interest=None) -> np.ndarray:
    """CreditGrades debt per issuer (spec Section 3, Alber PDF p. 22):
    D = FD + 0.5 (liabilities_total - FD) - min(minority_interest, 0.5 FD),  FD = debt_current + debt_long_term.
    A missing liabilities_total or minority_interest adds nothing. Negative other liabilities count as zero."""
    c, lt = np.asarray(debt_current, dtype=float), np.asarray(debt_long_term, dtype=float)
    fd = np.where(np.isnan(c) & np.isnan(lt), np.nan, np.nan_to_num(c) + np.nan_to_num(lt))
    lt_all = fd if liabilities_total is None else np.asarray(liabilities_total, dtype=float)
    mi = 0.0 if minority_interest is None else np.nan_to_num(np.asarray(minority_interest, dtype=float))
    other = np.clip(np.nan_to_num(lt_all - fd), 0.0, None)
    return fd + CG_OTHER_WEIGHT * other - np.minimum(mi, CG_MI_CAP * fd)


def bvn_cdf(h, k, rho) -> np.ndarray:
    """Bivariate standard normal CDF Phi2(h, k; rho) by Owen's T function (Owen 1956), for |rho| < 1:
    Phi2 = Phi(h)/2 + Phi(k)/2 - T(h, a_h) - T(k, a_k) - beta, a_h = (k - rho h)/(h sqrt(1 - rho^2)), a_k likewise,
    beta = 1/2 when h k < 0 (or h k = 0 with h + k < 0), else 0. Vectorised. The tests check it against
    scipy.stats.multivariate_normal.cdf, which the spec names (Section 6) but which is too slow for daily use."""
    h, k, rho = np.broadcast_arrays(*(np.asarray(v, dtype=float) for v in (h, k, rho)))
    h = np.where(h == 0.0, 1e-12, h)          # Owen's form divides by h and by k
    k = np.where(k == 0.0, 1e-12, k)
    c = np.sqrt(1.0 - rho ** 2)
    beta = np.where(h * k < 0, 0.5, 0.0)
    out = 0.5 * ndtr(h) + 0.5 * ndtr(k) - owens_t(h, (k - rho * h) / (h * c)) - owens_t(k, (h - rho * k) / (k * c)) - beta
    return np.clip(out, 0.0, 1.0)


def creditgrades_survival(S, D, sigma_a, t, Lbar: float = CG_LBAR, lam: float = CG_LAMBDA,
                          exact: bool = True) -> np.ndarray:
    """CreditGrades survival probability P(t) (Section 7.1, Alber PDF pp. 23 to 24, eqs. 17 to 21).

    d = (S + Lbar D)/(Lbar D) e^{lam^2}, A_t^2 = sig_A^2 t + lam^2. `exact=False` gives the Finger et al. (2002)
    form Phi(-A/2 + ln d/A) - d Phi(-A/2 - ln d/A), with the sign of eq. 21 (the printed eq. 17 has a typo).
    `exact=True` gives the Kiesel and Veraart (2008) form with the bivariate normal (eq. 21). S and D are issuer
    totals in the same unit. Intuition: the barrier is uncertain, so the firm can default at once."""
    S, D, sa, t = (np.asarray(v, dtype=float) for v in (S, D, sigma_a, t))
    with np.errstate(divide="ignore", invalid="ignore"):
        ln_d = np.log((S + Lbar * D) / (Lbar * D)) + lam ** 2
        A = np.sqrt(sa ** 2 * t + lam ** 2)
        if exact:
            p = (bvn_cdf(-lam / 2 + ln_d / lam, -A / 2 + ln_d / A, lam / A)
                 - np.exp(ln_d) * bvn_cdf(lam / 2 + ln_d / lam, -A / 2 - ln_d / A, -lam / A))
        else:
            p = ndtr(-A / 2 + ln_d / A) - np.exp(ln_d) * ndtr(-A / 2 - ln_d / A)
    ok = (S > 0) & (D > 0) & (sa > 0) & (t > 0)
    return np.where(ok, np.clip(p, 0.0, 1.0), np.nan)


def creditgrades_spread(P, t, R: float = CG_RECOVERY) -> np.ndarray:
    """s_CG = -(1 - R) ln P(t) / t (spec Section 3, our map of P to a spread at t = bond duration; R from Alber
    PDF p. 24). Intuition: the loss rate per year that the survival curve implies, times loss given default."""
    P, t = np.asarray(P, dtype=float), np.asarray(t, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where((P > 0) & (t > 0), -(1.0 - R) * np.log(P) / t, np.nan)


def implied_sigma_a(s_mkt, S, D, t, exact: bool = True, bounds: tuple[float, float] = SIG_A_BOUNDS) -> np.ndarray:
    """Asset vol at which the CreditGrades spread equals the market spread (spec Section 5 step 6, Wojtowicz in
    Alber PDF p. 25). Vectorised bisection in log sig. The model spread rises with sig, so the root is unique.
    NaN where the market spread lies outside the model spreads at the two bounds."""
    s_mkt, S, D, t = np.broadcast_arrays(*(np.asarray(v, dtype=float) for v in (s_mkt, S, D, t)))

    def spread(sig):
        return creditgrades_spread(creditgrades_survival(S, D, sig, t, exact=exact), t)

    lo, hi = np.full(s_mkt.shape, np.log(bounds[0])), np.full(s_mkt.shape, np.log(bounds[1]))
    inside = (spread(np.exp(lo)) <= s_mkt) & (s_mkt <= spread(np.exp(hi)))
    for _ in range(BISECT_STEPS):
        mid = 0.5 * (lo + hi)
        up = spread(np.exp(mid)) < s_mkt
        lo, hi = np.where(up, mid, lo), np.where(up, hi, mid)
    return np.where(inside, np.exp(0.5 * (lo + hi)), np.nan)


def cg_gap_score(gap: pd.Series, c: int = CG_GAP_DAYS, a: float = CG_TRIGGER) -> tuple[float, int]:
    """g = sign(gap_T) (|gap_T| - mean |gap|) / sd(gap), with the mean and sd over the c gap days before the last
    one, and the trigger flag (Section 8 S1, Alber PDF p. 29: enter when |gap| > mean_c |gap| + a sd).

    The window excludes the last day (our choice). With the last day inside, one point among 20 can sit at most
    19/sqrt(20) = 4.25 sd from the mean, so a = 4 could almost never fire. Flag +1 when g > a, -1 when g < -a,
    else 0. Fewer than c gap days before the last one give (NaN, 0)."""
    x = gap.dropna().to_numpy(dtype=float)
    if len(x) < c + 1:
        return np.nan, 0
    w = x[-c - 1:-1]
    sd = np.std(w, ddof=1)
    if not sd > 0:
        return np.nan, 0
    g = float(np.sign(x[-1]) * (abs(x[-1]) - np.mean(np.abs(w))) / sd)
    return g, int(g > a) - int(g < -a)


# ---------------------------------------------------------------- point-in-time inputs


def _known(df: pd.DataFrame | None, dt: pd.Timestamp) -> pd.DataFrame | None:
    """Rows public at the decision time; None stays None."""
    return None if df is None else df[pd.to_datetime(df["available_at"]) <= dt]


def _latest_financials(fin: pd.DataFrame) -> pd.DataFrame:
    """Latest fiscal quarter per gvkey, and its latest version (a restatement is a later row of the same quarter)."""
    return fin.sort_values(["gvkey", "period_end", "available_at"]).drop_duplicates("gvkey", keep="last") \
        .set_index("gvkey")


def _daily_equity(eq: pd.DataFrame, as_of: pd.Timestamp) -> pd.DataFrame:
    """Per gvkey from daily equity: E (USD millions), sig_E and mu from the last DAILY_WINDOW returns, available_at.
    Issuers with fewer than DAILY_MIN returns, or a last price older than EQUITY_STALE_DAYS, drop out."""
    e = eq[eq["date"] <= as_of].sort_values(["gvkey", "date"])
    rows = {}
    for gv, g in e.groupby("gvkey"):
        g = g.tail(DAILY_WINDOW)
        r = g["ret"].dropna().to_numpy(dtype=float)
        last = g.iloc[-1]
        if len(r) < DAILY_MIN or (as_of - last["date"]).days > EQUITY_STALE_DAYS:
            continue
        rows[gv] = {"E": abs(float(last["prc"])) * float(last["shrout"]) / 1000.0,
                    "sigma_e": annual_vol(r, DAYS_PER_YEAR), "mu": compound(r),
                    "eq_avail": g["available_at"].max()}
    return pd.DataFrame.from_dict(rows, orient="index")


def _monthly_equity(eqm: pd.DataFrame, as_of: pd.Timestamp) -> pd.DataFrame:
    """Per gvkey from monthly returns: sig_E over the last MONTHLY_WINDOW month ends (at least MONTHLY_MIN) times
    sqrt(12), and mu over the last MU_MONTHS month ends (all present)."""
    end = pd.Timestamp(as_of) + pd.offsets.MonthEnd(0)
    ends = pd.date_range(end=end, periods=MONTHLY_WINDOW, freq="ME")
    m = eqm[eqm["datadate"].isin(ends)].dropna(subset=["ret"])
    rows = {}
    for gv, g in m.groupby("gvkey"):
        r = g.sort_values("datadate")
        if len(r) < MONTHLY_MIN:
            continue
        last12 = r[r["datadate"] > end - pd.offsets.MonthEnd(MU_MONTHS)]
        rows[gv] = {"sigma_e": annual_vol(r["ret"].to_numpy(dtype=float), 12),
                    "mu": compound(last12["ret"].to_numpy()) if len(last12) == MU_MONTHS else np.nan,
                    "eq_avail": r["available_at"].max()}
    return pd.DataFrame.from_dict(rows, orient="index")


def _market_value(mv: pd.DataFrame, eqm: pd.DataFrame | None, as_of: pd.Timestamp) -> pd.DataFrame:
    """Fallback E per gvkey: the latest quarterly market value, grown by the monthly returns after its quarter end
    up to as_of (our choice: a missing month counts as zero return)."""
    v = mv[mv["period_end"] <= as_of].sort_values(["gvkey", "period_end", "available_at"]) \
        .drop_duplicates("gvkey", keep="last").set_index("gvkey")
    grow = pd.Series(1.0, index=v.index)
    if eqm is not None and len(eqm):
        m = eqm.merge(v["period_end"].rename("pe"), left_on="gvkey", right_index=True)
        m = m[(m["datadate"] > m["pe"]) & (m["datadate"] <= as_of)]
        grow = m.groupby("gvkey")["ret"].apply(lambda r: 1.0 + compound(r.fillna(0.0))).reindex(v.index).fillna(1.0)
    return pd.DataFrame({"E": v["value"].astype(float) * grow, "mv_avail": v["available_at"]})


def _rating_bucket(gvkeys: pd.Index, ratings: pd.DataFrame | None, leverage: pd.DataFrame | None,
                   as_of: pd.Timestamp, dt: pd.Timestamp) -> pd.Series:
    """Rating class per gvkey: the S&P class on file (hy.peers.rating_at), else the class that leverage implies, with
    cut-offs fitted on the ratings and leverage known at dt (hy.peers.fit_cutoffs)."""
    out = pd.Series(np.nan, index=gvkeys, dtype=object)
    if ratings is not None and len(ratings):
        out = out.fillna(rating_at(ratings, dt).reindex(gvkeys))
    if leverage is not None and len(leverage) and out.isna().any():
        hist = (ratings.assign(rclass=ratings["splticrm"].map(rating_class)).dropna(subset=["rclass"])
                .merge(leverage, left_on=["gvkey", "datadate"], right_on=["gvkey", "date"])
                if ratings is not None else pd.DataFrame(columns=["leverage", "ltm_ebitda", "rclass"]))
        hist = hist[(hist["leverage"] > 0) & (hist["ltm_ebitda"].astype(float) > 0)]
        cut = fit_cutoffs(np.log(hist["leverage"].astype(float)), hist["rclass"])
        lv = leverage[leverage["date"] <= as_of].sort_values("date").drop_duplicates("gvkey", keep="last") \
            .set_index("gvkey").reindex(gvkeys)
        imp = pd.Series([implied_class(l, bool(e > 0), cut) if e == e else None
                         for l, e in zip(lv["leverage"], lv["ltm_ebitda"].astype(float))], index=gvkeys)
        out = out.fillna(imp)
    return out


def _variant_b(bonds: pd.DataFrame, bd: pd.DataFrame, eqd: pd.DataFrame, fin: pd.DataFrame,
               as_of: pd.Timestamp, exact: bool) -> pd.DataFrame:
    """Per cusip: CreditGrades spreads (Finger and KV) at the last gap day, the gap, g and the flag (spec Section 5
    step 6). D on each day comes from the latest financials public on that day. t = month-end duration."""
    d = bd[(bd["date"] <= as_of) & (bd["date"] > as_of - pd.Timedelta(CG_LOOKBACK_DAYS, unit="D"))]
    d = d.merge(bonds[["cusip", "gvkey", "mod_dur"]], on="cusip")
    eq = eqd.assign(S=eqd["prc"].abs() * eqd["shrout"] / 1000.0)[["gvkey", "date", "S"]]
    d = d.merge(eq, on=["gvkey", "date"]).dropna(subset=["g_spread", "S"])
    if d.empty:
        return pd.DataFrame()
    f = fin.assign(D=cg_debt(fin["debt_current"], fin["debt_long_term"], fin.get("liabilities_total"),
                             fin.get("minority_interest")))[["gvkey", "available_at", "D"]]
    d = d.assign(known=(d["date"] + pd.Timedelta(1, unit="D")).astype("datetime64[ns]")).sort_values("known")
    f = f.assign(fin_at=pd.to_datetime(f["available_at"]).astype("datetime64[ns]")).drop(columns="available_at")
    d = pd.merge_asof(d, f.sort_values("fin_at"),
                      left_on="known", right_on="fin_at", by="gvkey").dropna(subset=["D"])
    if d.empty:
        return pd.DataFrame()
    S, D, t, s = (d[c].to_numpy(dtype=float) for c in ("S", "D", "mod_dur", "g_spread"))
    d["sig"] = implied_sigma_a(s, S, D, t, exact=exact)
    d = d.sort_values(["cusip", "date"])
    d["sig_bar"] = (d.set_index("date").groupby("cusip")["sig"]
                    .rolling(f"{CG_SIGMA_DAYS}D", min_periods=CG_SIGMA_MIN).mean().to_numpy())
    S, D, t = (d[c].to_numpy(dtype=float) for c in ("S", "D", "mod_dur"))
    sb = d["sig_bar"].to_numpy(dtype=float)
    d["cg_spread"] = creditgrades_spread(creditgrades_survival(S, D, sb, t, exact=False), t)
    d["cg_spread_kv"] = creditgrades_spread(creditgrades_survival(S, D, sb, t, exact=True), t)
    model = d["cg_spread_kv"] if exact else d["cg_spread"]
    d["cg_gap"] = np.log(d["g_spread"]) - np.log(model)
    rows = {}
    for cu, g in d.groupby("cusip"):
        g = g.dropna(subset=["cg_gap"])
        if g.empty or (as_of - g["date"].iloc[-1]).days > EQUITY_STALE_DAYS:
            continue
        z, flag = cg_gap_score(g["cg_gap"])
        last = g.iloc[-1]
        rows[cu] = {"cg_spread": last["cg_spread"], "cg_spread_kv": last["cg_spread_kv"], "cg_gap": last["cg_gap"],
                    "cg_z": z, "cg_flag": flag, "cg_avail": g["available_at"].max()}
    return pd.DataFrame.from_dict(rows, orient="index")


# ---------------------------------------------------------------- the factor


def compute(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp, exact: bool = True) -> pd.DataFrame:
    """F02 scores for the bonds of `bond_panel` at month end `as_of` (spec Section 5 steps 1 to 7).

    `score` = s2d_rank_rb: the within-bucket rank of x = log s - log Phi(-DD), in [-0.5, 0.5]. `score_cg` = cg_z, the
    CreditGrades gap score (KV form; `exact=False` uses the Finger form). Higher means cheaper (long). An issuer
    without equity or debt keeps its bond rows with NaN scores. Missing required panels give an empty frame."""
    as_of = pd.Timestamp(as_of)
    dt = decision_time(as_of)
    if any(panels.get(p) is None or len(panels[p]) == 0 for p in REQUIRED):
        return pd.DataFrame(columns=COLUMNS)
    pnl, fin = _known(panels["bond_panel"], dt), _known(panels["financials"], dt)
    eqm, eqd, mv = (_known(panels.get(p), dt) for p in ("equity_monthly", "equity_daily", "market_value"))
    ratings, leverage, bdaily = (_known(panels.get(p), dt) for p in ("ratings", "leverage", "bond_daily"))

    b = pnl[pnl["date"] == as_of]
    b = b[eligible(b) & b["g_spread"].between(SPREAD_MIN, SPREAD_MAX) & (b["mod_dur"] >= DUR_MIN)].copy()
    if b.empty:
        return pd.DataFrame(columns=COLUMNS)

    # Step 1: default point F from the latest public quarter.
    f = _latest_financials(fin)
    iss = pd.DataFrame(index=pd.Index(b["gvkey"].unique(), name="gvkey"))
    iss["F"] = pd.Series(default_point(f["debt_current"], f["debt_long_term"]), index=f.index).reindex(iss.index)
    iss["fin_avail"] = f["available_at"].reindex(iss.index)
    iss.loc[~(iss["F"] > 0), "F"] = np.nan

    # Step 2: E, sig_E and mu. Daily first, monthly fallback, flagged.
    daily = _daily_equity(eqd, as_of) if eqd is not None and len(eqd) else pd.DataFrame()
    monthly = _monthly_equity(eqm, as_of) if eqm is not None and len(eqm) else pd.DataFrame()
    mval = _market_value(mv, eqm, as_of) if mv is not None and len(mv) else pd.DataFrame()
    for c in ("E", "sigma_e", "mu"):
        iss[c] = daily[c].reindex(iss.index).astype(float) if c in daily else np.nan
    iss["eq_avail"] = pd.to_datetime(daily["eq_avail"].reindex(iss.index)) if "eq_avail" in daily else pd.NaT
    iss["vol_source"] = np.where(iss["sigma_e"].notna(), "daily", None)
    fb = iss["sigma_e"].isna()
    for c in ("sigma_e", "mu", "eq_avail"):
        if c in monthly:
            iss.loc[fb, c] = monthly[c].reindex(iss.index[fb])
    iss.loc[fb & iss["sigma_e"].notna(), "vol_source"] = "monthly"
    iss["e_source"] = np.where(iss["E"].notna(), "daily", None)
    if "E" in mval:
        miss = iss["E"].isna()
        iss.loc[miss, "E"] = mval["E"].reindex(iss.index[miss])
        iss.loc[miss & iss["E"].notna(), "e_source"] = "market_value"
        iss["mv_avail"] = mval["mv_avail"].reindex(iss.index).where(iss["e_source"] == "market_value")

    # Step 3: naive DD and log PD per issuer.
    iss["dd_equity"] = naive_dd(iss["E"], iss["F"], iss["sigma_e"], iss["mu"])
    iss["log_pd_dd"] = log_ndtr(-iss["dd_equity"].to_numpy(dtype=float))
    iss["rating_bucket"] = _rating_bucket(iss.index, ratings, leverage, as_of, dt)
    stamps = [c for c in ("fin_avail", "eq_avail", "mv_avail") if c in iss]
    iss["iss_avail"] = iss[stamps].apply(pd.to_datetime).max(axis=1)

    # Steps 4 and 5: join to bonds, x, winsorise, rank in the full pool and within bucket.
    out = b[["date", "cusip", "gvkey", "g_spread", "mod_dur", "available_at"]].merge(
        iss[["dd_equity", "log_pd_dd", "rating_bucket", "vol_source", "e_source", "iss_avail"]],
        left_on="gvkey", right_index=True, how="left")
    out["s2d_log"] = winsorise(pd.Series(spread_to_dd(out["g_spread"], out["dd_equity"]), index=out.index))
    out["s2d_rank"] = centred_rank(out["s2d_log"])
    hy_rows = out["rating_bucket"].isin(HY_BUCKETS)
    out["s2d_rank_rb"] = np.nan
    if hy_rows.any():
        out.loc[hy_rows, "s2d_rank_rb"] = out[hy_rows].groupby("rating_bucket")["s2d_log"].transform(centred_rank)

    # Step 6: Variant B, only with daily bonds and daily equity.
    cg = (_variant_b(out, bdaily, eqd, fin, as_of, exact)
          if bdaily is not None and len(bdaily) and eqd is not None and len(eqd) else pd.DataFrame())
    for c in ("cg_spread", "cg_spread_kv", "cg_gap", "cg_z", "cg_flag", "cg_avail"):
        out[c] = out["cusip"].map(cg[c]) if c in cg else np.nan
    out["cg_flag"] = out["cg_flag"].fillna(0).astype(int)

    # Step 7: one row per bond, stamped with the latest input it used.
    out["score"], out["score_cg"] = out["s2d_rank_rb"], out["cg_z"]
    out["available_at"] = out[["available_at", "iss_avail", "cg_avail"]].apply(pd.to_datetime).max(axis=1)
    return out[COLUMNS].reset_index(drop=True)
