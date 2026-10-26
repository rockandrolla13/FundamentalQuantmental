"""F08 LEVER event-risk score and the LEVER x spread corner trade (rank 8). Spec docs/factors/F08-lever-event-risk.md;
methodology Section 8 S5 (`p_LBO`, document optionality) and Section 9.1 (M&A or LBO row). Sources: Trinh et al.
(2006), "Introducing LEVER", PDF pp. 6-11 and 13-15 (PDF page = printed page + 1); Lehman QCR Quarterly 2007-Q1,
"Trading Event Risk in Credit Markets using LEVER", pp. 32-40 (PDF page = printed page).

    V_N_i    = alpha_V (V_i / |mean_w V over U_V| - 1)                    normalise on the cap-weighted norm (2006 p. 10)
    P_i      = mean over V in part P of rank(V_N_i)                        Valuation, Operation, Execution (2007 p. 32)
    LEVER_i  = 10 U((P_val + P_op + P_exe) / 3)                            uniform 0-10 scale (2006 p. 10 fn. 9)
    score_b  = 1[LH] - 1[HL] + w (1[LL] - 1[HH]),  w = 0.1 x Macro LEVER   corner trade (2007 pp. 35-39)

Intuition: a firm that is cheap, cash-rich and easy to finance draws a sponsor, and the buyout debt hurts its bonds.
Buy low event risk where the spread is wide. Sell high event risk where the spread is tight.

Inputs (alpha, peer universe): book to market (+1, sector), EV / EBITDA (-1, sector), FCF yield (+1, all), capex
growth (-1, all), FCF variability (-1, all), cash / market cap (+1, all), market cap (-1, all). 2007 version.

Panels. A new panel `compustat_quarterly`: one row per gvkey, `datadate` and version, with `available_at` (rdq, else
the point-in-time snapshot day) and Compustat `fundq` fields `ceqq`, `prccq`, `cshoq`, `cheq`, `dlcq`, `dlttq`,
`oibdpq`, plus the 3-month flows `oancf` and `capx` (de-cumulated `oancfy`, `capxy`). USD millions. Two optional
panels: `bond_terms` (`cusip`, `coc_put_price`, `available_at`) and `macro_lever` (`date`, `macro_lever` on 0-10,
`available_at`). Without `compustat_quarterly`, `gics` or `bond_panel` the result is empty. Without `macro_lever`,
w = 0 (the static trade only). Without `bond_terms`, every bond counts as having no put. Without `ratings` and
`leverage`, every bond sits in rating class "NR".

Sign. High LEVER means high event risk and a lower expected return for a bond without a change-of-control put. A bond
with a put at 100 or more gets NaN: the event can pay its holder, and S5 prices that case.
The trade evidence is IG only and zero cost (2007 pp. 33-34). The source does not test HY.
"""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd

from hy.backtest import decision_time, eligible, not_distressed
from hy.peers import (FIN_SECTORS, MIN_SECTOR, fit_cutoffs, implied_class, maturity_bucket, rating_at, rating_class,
                      sector_at)

# Inputs: name -> (part, alpha, peer universe). Alphas: 2006 p. 9 Fig. 5 and p. 10; 2007 p. 32 Fig. 2.
# Peers: sector for B/M and EV/EBITDA only (2007 p. 32 fn. 7). 2006 also puts capex growth in sector peers.
INPUTS: dict[str, tuple[str, int, str]] = {
    "bm": ("val", +1, "sector"),
    "ev_ebitda": ("val", -1, "sector"),
    "fcf_yield": ("op", +1, "all"),
    "capex_growth": ("op", -1, "all"),
    "fcf_var": ("exe", -1, "all"),
    "cash_mcap": ("exe", +1, "all"),
    "size": ("exe", -1, "all"),
}
PARTS = ("val", "op", "exe")
N_QUARTERS = 8                # two years: FCF variability (2007 p. 32 fn. 6) and year-on-year capex growth (fn. 5)
STALE_DAYS = 270              # the latest quarter must be at most 270 days old (our choice)
TECH_SECTOR = "45"            # GICS information technology
TECH_FROM = pd.Timestamp("2001-01-01")   # technology enters from 2001 (2006 p. 9)
LEVER_TAIL = 0.20             # bottom 20%, middle 60%, top 20% of LEVER in a bucket (2007 p. 33)
N_SPREAD = 3                  # three equal OAS groups inside each LEVER category (2007 p. 35)
MACRO_WEIGHT = 0.1            # w = 0.1 x Macro LEVER-Score (2007 p. 35 and p. 39)
MIN_BUCKET = 15               # bonds a rating x duration bucket needs: three per LEVER tail (our choice)
PUT_PRICE = 100.0             # a change-of-control put at or above par removes the bond (our choice)
MACRO_STALE_DAYS = 456        # the macro score must be at most 15 months old (our choice; the series is annual)
MIN_MACRO_YEARS = 12          # year pairs the macro regression needs (our choice)
HOLD = 3                      # hold 3 months, rebalance monthly, three overlapping books (2007 pp. 33-34)

META = {
    "rank": 8,
    "name": "LEVER event-risk score and LEVER x spread corner trade",
    "level": "bond",
    "horizon_months": HOLD,
    "needs": ["bond_panel", "compustat_quarterly", "gics", "ratings", "leverage", "bond_terms", "macro_lever"],
    "spec": "docs/factors/F08-lever-event-risk.md",
    "section": "8 S5; 9.1",
}

OUT_COLS = ["date", "cusip", "score", "available_at", "gvkey", "lever", "lever_val", "lever_op", "lever_exe",
            "lever_grp", "spread_grp", "corner", "bucket", "macro_lever", "w"]
CQ_COLS = ["ceqq", "prccq", "cshoq", "cheq", "dlcq", "dlttq", "oibdpq", "oancf", "capx"]


def _empty() -> pd.DataFrame:
    return pd.DataFrame(columns=OUT_COLS)


def _known(df: pd.DataFrame | None, dt: pd.Timestamp) -> pd.DataFrame | None:
    """Rows public at the decision time, or None when the panel is absent."""
    if df is None:
        return None
    return df[pd.to_datetime(df["available_at"]) <= dt]


# ---------------------------------------------------------------- firm inputs


def _consecutive(dates: pd.Series) -> bool:
    """True when quarter ends step by 2 to 4 months (one fiscal quarter; 52-53 week years shift the month)."""
    m = dates.dt.year * 12 + dates.dt.month
    return bool(m.diff().dropna().between(2, 4).all())


def quarter_inputs(q: pd.DataFrame) -> pd.Series:
    """The seven LEVER inputs from one firm's last N_QUARTERS quarters, oldest first (spec Definition table).

    LTM sums the last four 3-month flows. FCF = oancf - capx (2007 p. 32 fn. 4). Capex growth is LTM capex over the
    LTM capex a year before, minus 1 (fn. 5). FCF variability is the sd of the 8 quarterly FCF over debt (fn. 6).
    A non-positive denominator gives NaN for that input (our choice). Intuition: a sponsor wants cheap equity, free
    cash to service new debt, and a stable, small target."""
    last = q.iloc[-1]
    mkcap = float(last["prccq"]) * float(last["cshoq"])
    debt = float(last["dlcq"]) + float(last["dlttq"])
    fcf = (q["oancf"] - q["capx"]).to_numpy(float)
    capx = q["capx"].to_numpy(float)
    ebitda = float(q["oibdpq"].iloc[-4:].sum())
    capx_ltm, capx_prev = capx[-4:].sum(), capx[:4].sum()
    ok = mkcap > 0

    def div(a: float, b: float, good: bool) -> float:
        return a / b if good and np.isfinite(a) and np.isfinite(b) else np.nan

    return pd.Series({
        "bm": div(float(last["ceqq"]), mkcap, ok),
        "ev_ebitda": div(mkcap + debt - float(last["cheq"]), ebitda, ok and ebitda > 0),
        "fcf_yield": div(fcf[-4:].sum(), mkcap, ok),
        "capex_growth": div(capx_ltm, capx_prev, capx_prev > 0) - 1.0,
        "fcf_var": div(float(np.std(fcf, ddof=1)), debt, debt > 0),
        "cash_mcap": div(float(last["cheq"]), mkcap, ok),
        "size": mkcap if ok else np.nan,
        "mkcap": mkcap if ok else np.nan,
    })


def firm_inputs(cq: pd.DataFrame, dt: pd.Timestamp) -> pd.DataFrame:
    """LEVER inputs per gvkey at the decision time (spec build steps 1-2; 2007 p. 34 fn. 8).

    Keeps the latest version of each quarter public at dt, then the last N_QUARTERS consecutive quarters. A firm with
    fewer quarters, a gap, or a latest quarter older than STALE_DAYS drops out."""
    c = cq[pd.to_datetime(cq["available_at"]) <= dt].copy()
    c["datadate"] = pd.to_datetime(c["datadate"])
    c = c.sort_values("available_at").drop_duplicates(["gvkey", "datadate"], keep="last")
    c = c.sort_values(["gvkey", "datadate"]).groupby("gvkey").tail(N_QUARTERS)
    rows = {}
    for g, q in c.groupby("gvkey"):
        if len(q) < N_QUARTERS or (dt - q["datadate"].iloc[-1]).days > STALE_DAYS or not _consecutive(q["datadate"]):
            continue
        rows[g] = quarter_inputs(q)
    return pd.DataFrame.from_dict(rows, orient="index").rename_axis("gvkey")


# ---------------------------------------------------------------- Firm LEVER-Score


def normalise(v: pd.Series, mkcap: pd.Series, alpha: int, groups: pd.Series | None = None) -> pd.Series:
    """V_N = alpha (V / |mean_w V| - 1), mean_w = market-value-weighted mean over the peer universe (2006 p. 10).

    With `groups`, the peer universe is the firm's sector. A sector with fewer than MIN_SECTOR values takes the
    whole-universe mean (our choice). Dividing by |mean| keeps the order when the mean is negative (our choice).
    Intuition: distance from the cap-weighted norm, signed so that more LBO-friendly is higher."""
    ok = v.notna() & mkcap.notna() & (mkcap > 0)
    w = mkcap.where(ok)
    vw = (v * w).where(ok)
    m_all = vw.sum() / w.sum() if w.sum() > 0 else np.nan
    m = pd.Series(m_all, index=v.index)
    if groups is not None:
        gk = groups.reindex(v.index)
        num, den, cnt = vw.groupby(gk).sum(), w.groupby(gk).sum(), v.where(ok).groupby(gk).count()
        sec = (num / den).where(cnt >= MIN_SECTOR)
        m = gk.map(sec).fillna(m_all)
    m = m.abs().where(m.abs() > 0)
    return alpha * (v / m - 1.0)


def uniform(x: pd.Series) -> pd.Series:
    """Map scores to a uniform 0-10 scale: 10 (rank - 1) / (n - 1) (2006 p. 10 fn. 9; formula our choice)."""
    r, n = x.rank(), x.count()
    if n == 1:
        return x.where(x.isna(), 5.0)
    return 10.0 * (r - 1.0) / (n - 1.0)


def firm_lever(inputs: pd.DataFrame, sector: pd.Series, when: pd.Timestamp) -> pd.DataFrame:
    """Firm LEVER-Score per gvkey with the three part scores, all on 0-10 (2006 pp. 9-10; 2007 p. 32).

    Drops financials and firms without a sector, and technology before 2001 (2006 p. 9). Each normalised input is
    ranked across the whole universe. A part is the mean of its available input ranks. The firm needs all three
    parts (our choice). Firm score = mean of the parts (2007 p. 32), then mapped to uniform 0-10."""
    sec = sector.reindex(inputs.index)
    keep = sec.notna() & ~sec.isin(FIN_SECTORS)
    if when < TECH_FROM:
        keep &= sec != TECH_SECTOR
    x, sec = inputs[keep], sec[keep]
    if x.empty:
        return pd.DataFrame(columns=["lever", "lever_val", "lever_op", "lever_exe"])
    ranks = pd.DataFrame(index=x.index)
    for name, (_, alpha, peers) in INPUTS.items():
        vn = normalise(x[name], x["mkcap"], alpha, sec if peers == "sector" else None)
        ranks[name] = vn.rank(pct=True)
    parts = pd.DataFrame({p: ranks[[n for n, (q, _, _) in INPUTS.items() if q == p]].mean(axis=1) for p in PARTS})
    firm = parts.mean(axis=1, skipna=False)
    out = pd.DataFrame({"lever": uniform(firm)})
    for p in PARTS:
        out[f"lever_{p}"] = uniform(parts[p].where(firm.notna()))
    return out.dropna(subset=["lever"])


# ---------------------------------------------------------------- Macro LEVER-Score


def macro_lever_score(drivers: pd.DataFrame, counts: pd.DataFrame, as_of: pd.Timestamp,
                      cols: list[str] | None = None, min_years: int = MIN_MACRO_YEARS) -> float:
    """Macro LEVER-Score at as_of on 0-10, for the production machine to fill the `macro_lever` panel.

    `drivers`: one row per `year` with driver columns and `available_at`. `counts`: `year`, `n_lbo` (large LBOs,
    deal size above $250m) and `available_at`. OLS of n_lbo in year y on the drivers of year y-1 (2006 p. 10), fit
    on the year pairs public at the decision time. The forecast uses the latest driver year. Score = 10 x the share
    of in-sample fitted values at or below the forecast (our choice: the source prints no coefficients and no
    scaling). Intuition: a high score means next year looks like the busiest buyout years of the sample."""
    dt = decision_time(as_of)
    d = drivers[pd.to_datetime(drivers["available_at"]) <= dt].set_index("year").sort_index()
    n = counts[pd.to_datetime(counts["available_at"]) <= dt].set_index("year")["n_lbo"]
    cols = cols or [c for c in d.columns if c != "available_at"]
    d = d[cols].astype(float).dropna()
    lagged = d.copy()
    lagged.index = lagged.index + 1
    pair = lagged.join(n.rename("n_lbo"), how="inner").dropna()
    if d.empty or len(pair) < max(min_years, len(cols) + 2):
        return np.nan
    X = np.column_stack([np.ones(len(pair)), pair[cols].to_numpy(float)])
    beta, *_ = np.linalg.lstsq(X, pair["n_lbo"].to_numpy(float), rcond=None)
    fitted = X @ beta
    fc = float(np.r_[1.0, d[cols].iloc[-1].to_numpy(float)] @ beta)
    return 10.0 * float(np.mean(fitted <= fc))


def macro_at(macro: pd.DataFrame | None, dt: pd.Timestamp) -> tuple[float, pd.Timestamp | None]:
    """Latest Macro LEVER-Score public at dt and at most MACRO_STALE_DAYS old, clipped to 0-10, with its available_at."""
    if macro is None:
        return np.nan, None
    m = macro[(pd.to_datetime(macro["available_at"]) <= dt)
              & (pd.to_datetime(macro["date"]) >= dt - pd.Timedelta(MACRO_STALE_DAYS, unit="D"))]
    if m.empty:
        return np.nan, None
    row = m.sort_values(["date", "available_at"]).iloc[-1]
    return float(np.clip(row["macro_lever"], 0.0, 10.0)), pd.Timestamp(row["available_at"])


# ---------------------------------------------------------------- corner trade


def rating_classes(gvkeys: pd.Series, ratings: pd.DataFrame | None, leverage: pd.DataFrame | None,
                   dt: pd.Timestamp) -> pd.Series:
    """Rating class per bond row: actual S&P class, else the leverage-implied class, else "NR" (spec Definition).

    Reuses hy.peers.rating_at, fit_cutoffs and implied_class, as live_peers does. Every input is public at dt."""
    out = pd.Series("NR", index=gvkeys.index, dtype=object)
    act = rating_at(ratings, dt) if ratings is not None else pd.Series(dtype=object)
    if leverage is not None and ratings is not None:
        r = ratings[ratings["available_at"] <= dt]
        hist = r.assign(rclass=r["splticrm"].map(rating_class)).dropna(subset=["rclass"]).merge(
            leverage[["date", "gvkey", "leverage", "ltm_ebitda"]], left_on=["gvkey", "datadate"],
            right_on=["gvkey", "date"], how="inner")
        hist = hist[(hist["leverage"] > 0) & (hist["ltm_ebitda"].astype(float) > 0)]
        cut = fit_cutoffs(np.log(hist["leverage"].astype(float)), hist["rclass"])
        lv = leverage.sort_values("date").drop_duplicates("gvkey", keep="last").set_index("gvkey")
        imp = pd.Series({g: implied_class(float(lv.at[g, "leverage"]), float(lv.at[g, "ltm_ebitda"]) > 0, cut)
                         for g in lv.index}, dtype=object)
        out = gvkeys.map(imp).fillna(out)
    return gvkeys.map(act).fillna(out)


def assign_buckets(rclass: pd.Series, years: pd.Series, min_bucket: int = MIN_BUCKET) -> pd.Series:
    """Rating x duration bucket per bond (2007 p. 33). Duration bucket = hy.peers.maturity_bucket on years (our
    choice). When any duration bucket of a rating class has fewer than min_bucket bonds, the whole class sorts as
    one bucket. A class with fewer than min_bucket bonds gets NaN (our choice)."""
    rc = rclass.astype(str)
    full = rc + "|" + years.map(maturity_bucket).astype(str)
    small = full.map(full.value_counts()) < min_bucket
    pooled = rc.isin(rc[small])
    b = full.where(~pooled, rc)
    return b.where(rc.map(rc.value_counts()) >= min_bucket)


def corner_groups(df: pd.DataFrame, spread_col: str, tail: float = LEVER_TAIL) -> pd.DataFrame:
    """LEVER category and spread group per bond, inside each bucket (2007 pp. 33 and 35).

    lever_grp: L for the bottom `tail` of LEVER, H for the top `tail`, M between. spread_grp: L, M, H thirds of
    spread inside each bucket x LEVER category. Ranks are percentile ranks with ties averaged."""
    eps = 1e-9
    pl = df.groupby("bucket")["lever"].rank(pct=True)
    lg = np.where(pl <= tail + eps, "L", np.where(pl > 1.0 - tail + eps, "H", "M"))
    out = pd.DataFrame({"lever_grp": lg}, index=df.index)
    ps = df[spread_col].groupby([df["bucket"], out["lever_grp"]]).rank(pct=True)
    out["spread_grp"] = np.where(ps <= 1.0 / N_SPREAD + eps, "L", np.where(ps > 1.0 - 1.0 / N_SPREAD + eps, "H", "M"))
    return out


def corner_score(lever_grp: pd.Series, spread_grp: pd.Series, w: float) -> pd.Series:
    """score = 1[LH] - 1[HL] + w (1[LL] - 1[HH]); every other cell 0 (2007 p. 39). First letter LEVER, second spread.

    Intuition: LH - HL is the positive-carry core trade. LL - HH is the defensive pair, scaled by the buyout climate."""
    cell = lever_grp.astype(str) + spread_grp.astype(str)
    return cell.map({"LH": 1.0, "HL": -1.0, "LL": w, "HH": -w}).fillna(0.0).astype(float)


def put_bonds(terms: pd.DataFrame | None, dt: pd.Timestamp) -> set:
    """CUSIPs with a change-of-control put at PUT_PRICE or more, public at dt (methodology 3.4 `coc_put_price`)."""
    if terms is None:
        return set()
    t = terms[(pd.to_datetime(terms["available_at"]) <= dt) & (terms["coc_put_price"].astype(float) >= PUT_PRICE)]
    return set(t["cusip"])


def compute(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp, spread_col: str = "g_spread",
            macro_weight: float = MACRO_WEIGHT) -> pd.DataFrame:
    """Corner-trade score per bond at as_of, with the Firm LEVER-Score as the extra column `lever` (spec build steps).

    Higher score = long. A bond in a cell outside the four corners scores 0. NaN means no score: no LEVER, a put,
    or a bucket too small. `available_at` is the latest available_at of all rows read."""
    as_of = pd.Timestamp(as_of)
    dt = decision_time(as_of)
    bp, cq, gics = (_known(panels.get(k), dt) for k in ("bond_panel", "compustat_quarterly", "gics"))
    if bp is None or cq is None or gics is None:
        return _empty()
    ratings, leverage = _known(panels.get("ratings"), dt), _known(panels.get("leverage"), dt)
    terms = _known(panels.get("bond_terms"), dt)
    inputs = firm_inputs(cq, dt)
    if inputs.empty:
        return _empty()
    lev = firm_lever(inputs, sector_at(gics, as_of), as_of)
    b = bp[pd.to_datetime(bp["date"]) == as_of]
    b = b[eligible(b) & not_distressed(b, spread_col)].drop_duplicates("cusip", keep="last").copy()
    if b.empty or lev.empty:
        return _empty()
    b = b.join(lev, on="gvkey")
    b.loc[b["cusip"].isin(put_bonds(terms, dt)), "lever"] = np.nan
    macro, macro_avail = macro_at(_known(panels.get("macro_lever"), dt), dt)
    w = macro_weight * macro if np.isfinite(macro) else 0.0

    s = b[b["lever"].notna() & b[spread_col].notna()].copy()
    s["bucket"] = assign_buckets(rating_classes(s["gvkey"], ratings, leverage, dt), s["years"])
    s = s[s["bucket"].notna()]
    b["bucket"] = s["bucket"]
    if not s.empty:
        g = corner_groups(s, spread_col)
        b[["lever_grp", "spread_grp"]] = g
        b["corner"] = g["lever_grp"] + g["spread_grp"]
        b["score"] = corner_score(g["lever_grp"], g["spread_grp"], w)
    for c in ("lever_grp", "spread_grp", "corner", "score"):
        if c not in b:
            b[c] = np.nan
    stamps = [bp["available_at"].max(), cq["available_at"].max(), gics["available_at"].max(), macro_avail]
    stamps += [p["available_at"].max() for p in (ratings, leverage, terms) if p is not None and not p.empty]
    b["date"] = as_of
    b["available_at"] = max(pd.Timestamp(x) for x in stamps if x is not None and pd.notna(x))
    b["macro_lever"], b["w"] = macro, w
    return b[OUT_COLS].reset_index(drop=True)
