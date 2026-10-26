"""Issuer quality score: fundamentals, rating, and their blend (spec docs/factors/QUALITY-rotation.md, Definition 1).
Methodology Section 4.2 (cash flow and liquidity), 4.3 (capital structure), 4.1 (profitability), 4.5 (rating gap).

    r_k,i     = rank of sign_k x_k,i in the HY universe (or within GICS sector), mapped to [-0.5, 0.5]
    F_i       = sum_k w_k r_k,i / sum_k w_k  over the components k that issuer i has (at least MIN_COMPONENTS)
    f_i       = rank of F_i in [-0.5, 0.5]                                     fundamental quality
    g_i       = rank of the rating ordinal (IG 3, BB 2, B 1, CCC 0) in [-0.5, 0.5]  rating quality
    Q_i       = (w_f f_i + w_r g_i) / (w_f + w_r)                              blended quality
    gap_i     = f_i - g_i                                                       fundamentals against rating

Intuition: rank many independent measures of balance sheet strength, so one bad input cannot dominate. The spread
never enters F, so F can find a bond that the agencies, or the market, mislabel.

Components (x_k, sign, source). Leverage: debt / EBITDA, lower is better (methodology 4.3; Greenwood and Hanson
2013, Table 6, p. 50). Coverage: EBITDA / interest, higher is better (methodology 4.3; MS Apr 2011 p. 8: "interest
coverage greater than 3x"). Profitability: gross profit / assets (F09 `profitability`; Israel, Palhares,
Richardson 2018, p. 8). Profitability trend: 5-year change (F09 `profitability_change`). Owner cash flow to debt
(F19 `issuer_values`; MS Aug 2011 p. 3: "FCF positive"). Refinancing headroom and cyclicality (F21
`issuer_scores`; MS Sep 2011 p. 4). Size: log total assets (Greenwood and Hanson 2013, Table 6, p. 50). Distance
to default: the naive Merton DD of F02, equity based (Greenwood and Hanson 2013, p. 10, footnote 6).

Rating. `hy.factors.f04_bond_momentum.rating_classes`: S&P to February 2017, then the leverage-implied class. The
implied class reads leverage, so after 2017 the gap shrinks by construction (column `rclass_src` flags it).
"""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd

from hy.backtest import decision_time, eligible
from hy.factors import f02_spread_to_d2d as f02
from hy.factors.f04_bond_momentum import DEFAULT_SYMBOLS, rating_classes
from hy.factors.f09_profitability_change import known_annual, profitability_change, rank_unit
from hy.factors.f19_owner_cash_flow import annual_blocks, issuer_values, quarterly_blocks, sector_score
from hy.factors.f21_refinancing_headroom import issuer_scores
from hy.factors.f24_cell_percentile import cell_rating
from hy.peers import FIN_SECTORS, SUST_STALE_DAYS, rating_class, sector_at

# Component weights. Our choice: equal weight (the equal-risk mix of Israel, Palhares, Richardson 2018, p. 9),
# half weight for size (the weakest alternate quality measure of Greenwood and Hanson 2013, Table 6: t -1.71)
# and for the profitability trend (a change, not a level; F09 tests it as momentum).
WEIGHTS: dict[str, float] = {"leverage": 1.0, "coverage": 1.0, "profitability": 1.0, "prof_trend": 0.5,
                             "ocf_debt": 1.0, "headroom": 1.0, "cyclicality": 1.0, "size": 0.5, "dd": 1.0}
SIGNS: dict[str, float] = {"leverage": -1.0, "coverage": 1.0, "profitability": 1.0, "prof_trend": 1.0,
                           "ocf_debt": 1.0, "headroom": 1.0, "cyclicality": -1.0, "size": 1.0, "dd": 1.0}
COMPONENTS = tuple(WEIGHTS)
MIN_COMPONENTS = 4                 # components an issuer needs for a fundamental score (our choice)
BLEND_WEIGHTS = {"fundamental": 0.5, "rating": 0.5}   # w_f, w_r (our choice: no source weighs the two)
BLEND_MIN_PARTS = 2                # parts the blend needs; 1 lets one part stand in for the other (our choice)
RATING_ORDINAL = {"IG": 3.0, "BB": 2.0, "B": 1.0, "CCC": 0.0}   # hy.peers.CLASSES order
GAP_FLAG = 0.25                    # |gap| that flags an upgrade or downgrade candidate (our choice: > 1 quintile)
LEV_STALE_DAYS = 92                # a `leverage` panel row older than this falls back to annual_ebitda (our choice)
KINDS = ("blend", "fundamental", "rating")
WITHIN = ("universe", "sector")
FUND_PANELS = ("compustat_annual", "annual_ebitda", "gics")

META = {
    "rank": None,
    "name": "Issuer quality score (fundamental, rating, blend)",
    "level": "bond",
    "horizon_months": 12,
    "needs": ["bond_panel", "compustat_annual", "annual_ebitda", "gics", "ratings", "leverage",
              "compustat_quarterly", "financials", "equity_monthly", "equity_daily", "market_value"],
    "spec": "docs/factors/QUALITY-rotation.md",
    "section": "4.2; 4.3; 4.5",
}

ISSUER_COLS = (["gvkey", "sector", "rclass", "rclass_src", "rating_bucket", "n_components", "fund_raw",
                "fund_rank", "rating_rank", "blend_rank", "fund_rating_gap", "gap_flag"]
               + [f"x_{k}" for k in COMPONENTS])
BOND_COLS = ["date", "cusip", "score", "available_at", "gvkey", "kind", "quality_rank", "quintile"] + ISSUER_COLS[1:]


def _present(panels: Mapping[str, pd.DataFrame], name: str) -> bool:
    return panels.get(name) is not None and len(panels[name]) > 0


# ---------------------------------------------------------------- universe


def universe(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp) -> pd.DataFrame:
    """Eligible bonds of bond_panel at month end as_of, known at decision_time(as_of), one row per cusip, with a
    gvkey. An issuer with a raw S&P symbol D or SD drops out (the F04 rule). The universe is the scoring pool."""
    as_of = pd.Timestamp(as_of) + pd.offsets.MonthEnd(0)
    dt = decision_time(as_of)
    p = panels["bond_panel"]
    p = p[(p["available_at"] <= dt) & (pd.to_datetime(p["date"]) == as_of)]
    p = p.sort_values("available_at").drop_duplicates("cusip", keep="last")
    p = p[eligible(p) & p["gvkey"].notna()]
    if _present(panels, "ratings") and len(p):
        r = panels["ratings"]
        r = r[(r["available_at"] <= dt)].sort_values("datadate").drop_duplicates("gvkey", keep="last")
        raw = r.set_index("gvkey")["splticrm"].astype(str).str.strip().str.upper()
        p = p[~p["gvkey"].map(raw).isin(DEFAULT_SYMBOLS)]
    return p.reset_index(drop=True)


# ---------------------------------------------------------------- components


def leverage_coverage(panels: Mapping[str, pd.DataFrame], dt: pd.Timestamp, as_of: pd.Timestamp) -> pd.DataFrame:
    """Leverage (debt / EBITDA) and coverage (EBITDA / interest) per gvkey (methodology 4.3).

    Leverage: the `leverage` panel row of the latest month end <= as_of, at most LEV_STALE_DAYS old, else debt /
    oibdp of the latest `annual_ebitda` fiscal year known at dt. EBITDA <= 0 gives +inf (worst). Debt <= 0 gives 0.
    Coverage: oibdp / xint of the latest fiscal year (annual_ebitda joined to compustat_annual on gvkey, fyear).
    xint <= 0 with oibdp > 0 gives +inf (best). Columns leverage, coverage."""
    out = pd.DataFrame(columns=["leverage", "coverage"], dtype=float)
    if _present(panels, "annual_ebitda"):
        e = known_annual(panels["annual_ebitda"], dt)
        e = e.assign(fyear=e["fyear"].astype(int)).sort_values(["gvkey", "fyear"]).drop_duplicates("gvkey", keep="last")
        e = e[(dt - e["datadate"]).dt.days <= SUST_STALE_DAYS].set_index("gvkey")
        eb, debt = e["oibdp"].astype(float), e["debt"].astype(float)
        lev = (debt / eb.where(eb > 0)).where(eb > 0, np.inf).where(debt > 0, 0.0).where(eb.notna() & debt.notna())
        out = pd.DataFrame({"leverage": lev}, index=e.index)
        if _present(panels, "compustat_annual"):
            a = known_annual(panels["compustat_annual"], dt)
            a = a.assign(fyear=a["fyear"].astype(int)).set_index(["gvkey", "fyear"])
            xint = a["xint"].astype(float).reindex(list(zip(e.index, e["fyear"]))).to_numpy() \
                if "xint" in a else np.full(len(e), np.nan)
            xi = pd.Series(xint, index=e.index)
            cov = (eb / xi.where(xi > 0)).where(xi > 0, np.where(eb > 0, np.inf, np.nan))
            out["coverage"] = cov.where(xi.notna() & eb.notna())
        else:
            out["coverage"] = np.nan
    if _present(panels, "leverage"):
        lv = panels["leverage"]
        lv = lv[(lv["available_at"] <= dt) & (pd.to_datetime(lv["date"]) <= as_of)].copy()
        lv["date"] = pd.to_datetime(lv["date"])
        lv = lv[(as_of - lv["date"]).dt.days <= LEV_STALE_DAYS]
        lv = lv.sort_values(["date", "available_at"]).drop_duplicates("gvkey", keep="last").set_index("gvkey")
        eb = lv["ltm_ebitda"].astype(float)
        val = lv["leverage"].astype(float).where(eb > 0, np.inf).where(eb.notna())
        out = out.reindex(out.index.union(val.index))
        out.loc[val.index, "leverage"] = val.where(val.notna(), out.loc[val.index, "leverage"])
    return out.astype(float)


def distance_to_default(panels: Mapping[str, pd.DataFrame], dt: pd.Timestamp, as_of: pd.Timestamp) -> pd.Series:
    """Naive Merton DD per gvkey, F02 build steps 1 to 3 (Bharath and Shumway 2008 eq. 12). Equity and balance sheet
    only: no spread. Needs `financials` and `equity_daily` or `equity_monthly`. E from daily prices, else from
    `market_value`. Empty series when an input is missing."""
    fin = f02._known(panels.get("financials"), dt)
    if fin is None or not len(fin):
        return pd.Series(dtype=float, name="dd")
    f = f02._latest_financials(fin)
    F = pd.Series(f02.default_point(f["debt_current"], f["debt_long_term"]), index=f.index)
    eqd, eqm, mv = (f02._known(panels.get(k), dt) for k in ("equity_daily", "equity_monthly", "market_value"))
    iss = pd.DataFrame(index=F.index)
    daily = f02._daily_equity(eqd, as_of) if eqd is not None and len(eqd) else pd.DataFrame()
    monthly = f02._monthly_equity(eqm, as_of) if eqm is not None and len(eqm) else pd.DataFrame()
    mval = f02._market_value(mv, eqm, as_of) if mv is not None and len(mv) else pd.DataFrame()
    for c in ("E", "sigma_e", "mu"):
        iss[c] = daily[c].reindex(iss.index).astype(float) if c in daily else np.nan
        if c in monthly:
            iss[c] = iss[c].fillna(monthly[c].reindex(iss.index).astype(float))
    if "E" in mval:
        iss["E"] = iss["E"].fillna(mval["E"].reindex(iss.index).astype(float))
    dd = f02.naive_dd(iss["E"], F.where(F > 0), iss["sigma_e"], iss["mu"])
    return pd.Series(dd, index=iss.index, name="dd").dropna()


def fundamental_inputs(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp) -> pd.DataFrame:
    """Raw component values x_k per gvkey at decision_time(as_of) (spec build step 2). Every input passes the
    available_at rule of the factor it comes from. Columns x_<component>, NaN where an input is missing."""
    as_of = pd.Timestamp(as_of) + pd.offsets.MonthEnd(0)
    dt = decision_time(as_of)
    parts: dict[str, pd.Series] = {}
    lc = leverage_coverage(panels, dt, as_of)
    parts["leverage"], parts["coverage"] = lc.get("leverage"), lc.get("coverage")
    if _present(panels, "compustat_annual"):
        ca = panels["compustat_annual"]
        if {"sale", "cogs", "at"} <= set(ca.columns):
            pc = profitability_change(ca, dt).set_index("gvkey")
            parts["profitability"], parts["prof_trend"] = pc["prof"], pc["score"]
            a = known_annual(ca, dt).sort_values(["gvkey", "fyear"]).drop_duplicates("gvkey", keep="last")
            a = a[(dt - a["datadate"]).dt.days <= SUST_STALE_DAYS].set_index("gvkey")
            at = a["at"].astype(float)
            parts["size"] = np.log(at.where(at > 0))
        blocks = [quarterly_blocks(panels["compustat_quarterly"], dt)] if _present(panels, "compustat_quarterly") \
            else []
        done = blocks[0]["gvkey"] if blocks else []
        ann = annual_blocks(ca, dt)
        blocks.append(ann[~ann["gvkey"].isin(done)])
        blocks = [b for b in blocks if len(b)]
        if blocks:
            parts["ocf_debt"] = issuer_values(pd.concat(blocks, ignore_index=True)).set_index("gvkey")["ocf_debt"]
        if all(_present(panels, k) for k in FUND_PANELS) and "che" in ca:
            hs = issuer_scores(panels, dt).set_index("gvkey")
            parts["headroom"], parts["cyclicality"] = hs["headroom"], hs["cyclicality"]
    parts["dd"] = distance_to_default(panels, dt, as_of)
    parts = {k: v for k, v in parts.items() if v is not None and len(v)}
    idx = pd.Index(sorted(set().union(*[set(v.index) for v in parts.values()])) if parts else [], name="gvkey")
    out = pd.DataFrame(index=idx)
    for k in COMPONENTS:
        out[f"x_{k}"] = parts[k].astype(float).groupby(level=0).last().reindex(idx) if k in parts else np.nan
    return out


def component_ranks(x: pd.DataFrame, sector: pd.Series | None = None, within: str = "universe") -> pd.DataFrame:
    """r_k = rank of sign_k x_k mapped to [-0.5, 0.5] (spec Definition 1). `within="sector"` ranks inside GICS
    sector (F19 `sector_score`, NaN below MIN_SECTOR issuers). +inf and -inf rank at the ends. Columns COMPONENTS."""
    if within not in WITHIN:
        raise ValueError(f"within must be one of {WITHIN}")
    out = pd.DataFrame(index=x.index)
    for k in COMPONENTS:
        v = SIGNS[k] * x[f"x_{k}"].astype(float)
        if within == "sector":
            out[k] = sector_score(v, sector.reindex(x.index))
        else:
            out[k] = rank_unit(v)
    return out


def composite(ranks: pd.DataFrame, weights: Mapping[str, float] = WEIGHTS,
              min_components: int = MIN_COMPONENTS) -> pd.DataFrame:
    """F = weighted mean of the available component ranks (spec Definition 1). NaN with fewer than
    `min_components`. Intuition: a missing measure is skipped, not scored as average. Columns fund_raw,
    n_components."""
    w = pd.Series({k: float(weights.get(k, 0.0)) for k in ranks.columns})
    have = ranks.notna() & (w > 0)
    num = (ranks.fillna(0.0) * w).sum(axis=1)
    den = (have * w).sum(axis=1)
    n = have.sum(axis=1)
    raw = (num / den.where(den > 0)).where(n >= min_components)
    return pd.DataFrame({"fund_raw": raw, "n_components": n.astype(int)})


def rating_info(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp, gvkeys: pd.Index) -> pd.DataFrame:
    """Rating class (F04 `rating_classes`), its source (actual or implied), and the cell bucket BBB, BB, B, CCC
    (F24 `cell_rating`) per gvkey. NaN without the `ratings` panel. Columns rclass, rclass_src, rating_bucket."""
    out = pd.DataFrame(index=gvkeys, columns=["rclass", "rclass_src", "rating_bucket"], dtype=object)
    if not _present(panels, "ratings"):
        return out
    cls = rating_classes(panels["ratings"], panels.get("leverage"), pd.Timestamp(as_of)).reindex(gvkeys)
    out["rclass"] = cls["rclass"]
    out["rclass_src"] = np.where(cls["raw"].map(rating_class).notna(), "actual",
                                 np.where(cls["rclass"].notna(), "implied", None))
    out["rating_bucket"] = cell_rating(cls["rclass"], cls["raw"])
    return out


def blend(fund_rank: pd.Series, rating_rank: pd.Series, weights: Mapping[str, float] = BLEND_WEIGHTS,
          min_parts: int = BLEND_MIN_PARTS) -> pd.Series:
    """Q = (w_f f + w_r g) / (w_f + w_r) over the parts present, re-ranked to [-0.5, 0.5] (spec Definition 1).
    NaN with fewer than `min_parts` parts. A part with weight 0 is not needed, so weights (0, 1) give the rating
    rank alone."""
    parts = pd.DataFrame({"fundamental": fund_rank, "rating": rating_rank})
    w = pd.Series({k: float(weights[k]) for k in parts.columns})
    have = parts.notna() & (w > 0)
    need = min(int(min_parts), int((w > 0).sum()))
    q = (parts.fillna(0.0) * w).sum(axis=1) / (have * w).sum(axis=1).where(have.sum(axis=1) > 0)
    return rank_unit(q.where(have.sum(axis=1) >= max(need, 1)))


def gap_flag(gap: pd.Series, cut: float = GAP_FLAG) -> pd.Series:
    """"upgrade_candidate" where fundamentals rank above the rating by at least `cut`, "downgrade_candidate" where
    below, else None (methodology 4.5: a negative gap anticipates a downgrade; signal S6)."""
    out = pd.Series(None, index=gap.index, dtype=object)
    out[gap >= cut] = "upgrade_candidate"
    out[gap <= -cut] = "downgrade_candidate"
    return out


def quintile(rank: pd.Series) -> pd.Series:
    """Quality quintile 1 (lowest) to 5 (highest) from a rank in [-0.5, 0.5]. NaN stays NaN (Int64)."""
    q = np.floor((rank.astype(float) + 0.5) * 5.0) + 1.0
    return q.clip(1, 5).astype("Int64")


def issuer_quality(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp, gvkeys, within: str = "universe",
                   weights: Mapping[str, float] = WEIGHTS, blend_weights: Mapping[str, float] = BLEND_WEIGHTS,
                   min_components: int = MIN_COMPONENTS, blend_min_parts: int = BLEND_MIN_PARTS) -> pd.DataFrame:
    """Quality per gvkey of `gvkeys` (the universe issuers) at as_of (spec build steps 2 to 5). Financials (GICS 40,
    60) get no fundamental score. Ranks run over `gvkeys` only. Columns ISSUER_COLS."""
    as_of = pd.Timestamp(as_of) + pd.offsets.MonthEnd(0)
    dt = decision_time(as_of)
    idx = pd.Index(pd.unique(pd.Series(list(gvkeys))), name="gvkey")
    if _present(panels, "gics"):
        g = panels["gics"]
        sector = idx.to_series().map(sector_at(g[g["available_at"] <= dt], as_of))
    else:
        sector = pd.Series(np.nan, index=idx, dtype=object)
    x = fundamental_inputs(panels, as_of).reindex(idx)
    x.loc[sector.isin(FIN_SECTORS).to_numpy()] = np.nan
    if not _present(panels, "gics"):
        x[:] = np.nan                       # financials cannot be removed without gics: no fundamental score
    comp = composite(component_ranks(x, sector, within), weights, min_components)
    out = pd.concat([rating_info(panels, as_of, idx), comp, x], axis=1)
    out["sector"] = sector
    out["fund_rank"] = rank_unit(out["fund_raw"])
    out["rating_rank"] = rank_unit(out["rclass"].map(RATING_ORDINAL).astype(float))
    out["blend_rank"] = blend(out["fund_rank"], out["rating_rank"], blend_weights, blend_min_parts)
    both = out["fund_rank"].notna() & out["rating_rank"].notna()
    out["fund_rating_gap"] = (rank_unit(out["fund_raw"].where(both))
                              - rank_unit(out["rclass"].map(RATING_ORDINAL).astype(float).where(both)))
    out["gap_flag"] = gap_flag(out["fund_rating_gap"])
    out = out.rename_axis("gvkey").reset_index()
    return out[ISSUER_COLS]


def required_ok(panels: Mapping[str, pd.DataFrame], kind: str) -> bool:
    """bond_panel always. `fundamental` needs FUND_PANELS, `rating` needs ratings, `blend` needs one of the two."""
    if not _present(panels, "bond_panel"):
        return False
    fund = all(_present(panels, k) for k in FUND_PANELS)
    rat = _present(panels, "ratings")
    return {"fundamental": fund, "rating": rat, "blend": fund or rat}[kind]


def compute(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp, kind: str = "blend", within: str = "universe",
            weights: Mapping[str, float] = WEIGHTS, blend_weights: Mapping[str, float] = BLEND_WEIGHTS,
            min_components: int = MIN_COMPONENTS, blend_min_parts: int = BLEND_MIN_PARTS) -> pd.DataFrame:
    """Quality score per eligible bond at as_of (spec build steps 1 to 5). One row per cusip.

    score = quality_rank = fund_rank, rating_rank or blend_rank by `kind`, in [-0.5, 0.5]. It is a characteristic:
    higher = higher quality. The expression (hy.quality.trades) sets the trade sign. NaN = no score. The spread is
    never read. Empty frame (columns BOND_COLS) when the panels of `kind` are missing (`required_ok`)."""
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {KINDS}")
    as_of = pd.Timestamp(as_of) + pd.offsets.MonthEnd(0)
    if not required_ok(panels, kind):
        return pd.DataFrame(columns=BOND_COLS)
    b = universe(panels, as_of)
    if b.empty:
        return pd.DataFrame(columns=BOND_COLS)
    iss = issuer_quality(panels, as_of, b["gvkey"], within, weights, blend_weights, min_components, blend_min_parts)
    out = b[["cusip", "gvkey"]].merge(iss, on="gvkey", how="left")
    out["kind"] = kind
    out["quality_rank"] = out[{"blend": "blend_rank", "fundamental": "fund_rank", "rating": "rating_rank"}[kind]]
    out["quintile"] = quintile(out.drop_duplicates("gvkey").set_index("gvkey")["quality_rank"]).reindex(
        out["gvkey"]).to_numpy()
    out["score"] = out["quality_rank"]
    out["date"] = as_of
    out["available_at"] = decision_time(as_of)
    return out[BOND_COLS].astype({"score": float, "quality_rank": float}).reset_index(drop=True)
