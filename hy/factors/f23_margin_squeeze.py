"""F23 Margin squeeze: producer minus consumer prices by sector (rank 23). Spec docs/factors/F23-margin-squeeze.md;
methodology Section 4.1 (`margin`, `margin_trend`) and Section 8 (S3, forward leverage). Sources: Quant Credit
`combined_strategies_data_requirements.csv`, row "EBITDA Margin Trends by Sector" (idea only); Morgan Stanley,
"On the Margin" (Sheets et al., 18 February 2011), p. 3 (PPI-CPI gap as pricing power, YoY % changes) and p. 7
(LTM EBITDA margin change screen). PDF page = printed page. Neither source tests a signal: there is no backtest.

    G_s,t   = (PPIin_s,t / PPIin_s,t-12 - 1) - (Pout_s,t / Pout_s,t-12 - 1)   12-month sector squeeze (p. 3)
    m_i     = sum of last 4 oibdpq / sum of last 4 saleq                      LTM EBITDA margin (p. 7)
    x_i     = (1 - m~_i) / m~_i,  m~_i = max(m_i, MARGIN_FLOOR)               exposure: cost share over margin
    I_i     = -G_s(i),t x_i                                                   projected relative EBITDA change
    tau_i   = hy.state.margin_trend over 8 quarterly margins                  issuer trend (Section 4.1)
    score_i = (z(I_i) + w z(tau_i)) / (1 + w),  z clipped to +-Z_CLIP          z(I_i) alone when tau_i is NaN

Intuition: if sales move with output prices and all other cost with input prices, dm = -(1 - m) G, so EBITDA moves
by -G (1 - m) / m. The same squeeze hurts a thin margin most. More squeeze on a thin or falling margin = short.

Inputs. A new panel `sector_prices`: `gsector` (two-digit GICS), `date` (reference month end), `ppi_input`,
`price_output` (index levels), `available_at`. The spec page holds the default GICS-to-BLS map. A month is known at
max(available_at, date + PRICE_LAG_DAYS). The panel `compustat_quarterly` of F08 with the column `saleq` added
(`gvkey`, `datadate`, `oibdpq`, `saleq`, `available_at`; 3-month flows). `leverage.ltm_ebitda` cannot serve: the
margin needs sales. Without `sector_prices`, `compustat_quarterly`, `gics` or `bond_panel` the result is empty.
Financials (GICS 40 and 60) get NaN.
"""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd

from hy.backtest import decision_time, eligible
from hy.peers import FIN_SECTORS, sector_at
from hy.state import margin_trend

YOY_MONTHS = 12          # months of the price change: "% Chg. YoY" (MS note, Exhibit 4, p. 3)
PRICE_LAG_DAYS = 31      # a price month is known at the end of the next month (our choice; BLS releases mid-month)
PRICE_STALE_DAYS = 120   # the latest price month must be at most 120 days old (our choice)
N_QUARTERS = 8           # quarters for the trend (methodology 4.1) and the L12M margin change (p. 7)
QTR_STALE_DAYS = 270     # the latest quarter must be at most 270 days old (our choice, as F08)
MARGIN_FLOOR = 0.02      # margin floor of the exposure: caps x at 49 (our choice)
TREND_WEIGHT = 0.5       # weight w of the margin trend in the score (our choice)
Z_CLIP = 3.0             # clip of the cross-issuer z-scores (our choice)
HORIZON = 3              # months (our choice; the source gives none, reader block B-F18 tests 3 months)

META = {
    "rank": 23,
    "name": "Margin squeeze: producer minus consumer prices by sector",
    "level": "bond",
    "horizon_months": HORIZON,
    "needs": ["bond_panel", "compustat_quarterly", "gics", "sector_prices"],
    "spec": "docs/factors/F23-margin-squeeze.md",
    "section": "4.1; 8 S3",
}

SECTOR_COLS = ["gsector", "squeeze", "ppi_input_yoy", "price_output_yoy", "price_date"]
MARGIN_COLS = ["gvkey", "margin", "margin_chg_12m", "margin_trend"]
BOND_COLS = ["date", "cusip", "score", "available_at", "gvkey", "gsector", "squeeze", "ppi_input_yoy",
             "price_output_yoy", "price_date", "margin", "margin_chg_12m", "margin_trend", "exposure", "impact"]


def _empty() -> pd.DataFrame:
    return pd.DataFrame(columns=BOND_COLS)


# ---------------------------------------------------------------- sector squeeze


def yoy_change(level: pd.Series, level_lag: pd.Series) -> pd.Series:
    """Year-on-year % change, level / level_lag - 1 (spec Definition; MS note Exhibit 4, p. 3). NaN where the lag
    level is missing or not positive."""
    lag = level_lag.astype(float)
    return level.astype(float) / lag.where(lag > 0) - 1.0


def sector_squeeze(prices: pd.DataFrame, dt: pd.Timestamp) -> pd.DataFrame:
    """G per gsector at decision time dt (spec build steps 2 and 3; p. 3): YoY change of `ppi_input` minus YoY change
    of `price_output` at the latest month T known at dt, against T - YOY_MONTHS. A month is known at
    max(available_at, date + PRICE_LAG_DAYS). The last vintage per (gsector, month) wins. A sector whose T is older
    than PRICE_STALE_DAYS drops out. NaN when T - 12 is missing. Intuition: costs that outrun prices squeeze margins."""
    p = prices.copy()
    p["date"] = pd.to_datetime(p["date"])
    known = np.maximum(pd.to_datetime(p["available_at"]), p["date"] + pd.Timedelta(PRICE_LAG_DAYS, unit="D"))
    p = p.assign(known_at=known)[known <= dt]
    if p.empty:
        return pd.DataFrame(columns=SECTOR_COLS)
    p["gsector"] = p["gsector"].astype(str)
    p["month"] = p["date"].dt.to_period("M")
    p = p.sort_values("known_at").drop_duplicates(["gsector", "month"], keep="last")
    last = p.sort_values("month").drop_duplicates("gsector", keep="last")
    last = last[(dt - last["date"]).dt.days <= PRICE_STALE_DAYS]
    lag = p[["gsector", "month", "ppi_input", "price_output"]].rename(
        columns={"month": "month_lag", "ppi_input": "ppi_lag", "price_output": "out_lag"})
    out = last.assign(month_lag=last["month"] - YOY_MONTHS).merge(lag, on=["gsector", "month_lag"], how="left")
    out["ppi_input_yoy"] = yoy_change(out["ppi_input"], out["ppi_lag"])
    out["price_output_yoy"] = yoy_change(out["price_output"], out["out_lag"])
    out["squeeze"] = out["ppi_input_yoy"] - out["price_output_yoy"]
    out["price_date"] = out["date"]
    return out[SECTOR_COLS].reset_index(drop=True)


# ---------------------------------------------------------------- issuer margin


def issuer_margins(cq: pd.DataFrame, dt: pd.Timestamp) -> pd.DataFrame:
    """LTM margin, its L12M change and the 8-quarter trend per gvkey at dt (spec build step 4; p. 7; methodology 4.1).

    Keeps the latest version of each quarter public at dt, then the last N_QUARTERS quarters. A firm with fewer
    quarters, a gap (quarter ends not 2 to 4 months apart), or a latest quarter older than QTR_STALE_DAYS drops out.
    m = LTM oibdpq / LTM saleq, NaN when LTM sales <= 0. margin_chg_12m = m minus the LTM margin 4 quarters back.
    The trend uses the single-quarter margins, NaN where saleq <= 0."""
    c = cq[pd.to_datetime(cq["available_at"]) <= dt].copy()
    c["datadate"] = pd.to_datetime(c["datadate"])
    c = c.sort_values("available_at").drop_duplicates(["gvkey", "datadate"], keep="last")
    c = c.sort_values(["gvkey", "datadate"]).groupby("gvkey").tail(N_QUARTERS)
    rows = []
    for g, q in c.groupby("gvkey"):
        months = q["datadate"].dt.year * 12 + q["datadate"].dt.month
        if (len(q) < N_QUARTERS or (dt - q["datadate"].iloc[-1]).days > QTR_STALE_DAYS
                or not months.diff().dropna().between(2, 4).all()):
            continue
        e, s = q["oibdpq"].to_numpy(float), q["saleq"].to_numpy(float)
        m_now = e[-4:].sum() / s[-4:].sum() if s[-4:].sum() > 0 else np.nan
        m_prev = e[:4].sum() / s[:4].sum() if s[:4].sum() > 0 else np.nan
        qm = np.where(s > 0, e / np.where(s > 0, s, 1.0), np.nan)
        rows.append({"gvkey": g, "margin": m_now, "margin_chg_12m": m_now - m_prev,
                     "margin_trend": margin_trend(qm, window=N_QUARTERS)})
    return pd.DataFrame(rows, columns=MARGIN_COLS)


def margin_exposure(margin: pd.Series, floor: float = MARGIN_FLOOR) -> pd.Series:
    """x = (1 - m~) / m~ with m~ = max(m, floor) (spec Definition). NaN stays NaN. Intuition: cost per unit of EBITDA.
    A 5% margin gives 19, a 30% margin 2.33."""
    m = margin.astype(float).clip(lower=floor)
    return (1.0 - m) / m


def squeeze_impact(squeeze: pd.Series, exposure: pd.Series) -> pd.Series:
    """I = -G x: the relative EBITDA change a squeeze G implies when sales track output prices and all other cost
    tracks input prices (spec Definition). Example: G = 0.03, m = 0.05 gives I = -0.57."""
    return -squeeze.astype(float) * exposure.astype(float)


def clipped_z(x: pd.Series, clip: float = Z_CLIP) -> pd.Series:
    """Cross-sectional z-score, (x - mean) / sd with ddof 1, clipped to +-clip (spec build step 6). NaN stays NaN.
    Fewer than 2 values or zero sd gives 0 where x is present. +-inf counts as the clip."""
    v = x.astype(float).replace([np.inf, -np.inf], np.nan)
    sd = v.std(ddof=1)
    if v.notna().sum() < 2 or not np.isfinite(sd) or sd == 0:
        z = pd.Series(np.where(v.notna(), 0.0, np.nan), index=x.index)
    else:
        z = (v - v.mean()) / sd
    z = z.where(~np.isposinf(x.astype(float)), clip).where(~np.isneginf(x.astype(float)), -clip)
    return z.clip(-clip, clip)


# ---------------------------------------------------------------- compute


def compute(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp,
            trend_weight: float = TREND_WEIGHT) -> pd.DataFrame:
    """Margin squeeze score per eligible bond of bond_panel at as_of (spec build steps 1 to 7). One row per cusip.
    score = (z(I) + w z(tau)) / (1 + w) at issuer level, z(I) alone when tau is NaN, NaN when I is NaN or the issuer
    is a financial. Empty frame (columns BOND_COLS) when sector_prices, compustat_quarterly, gics or bond_panel is
    missing. Higher score = long. No source backtest exists."""
    as_of = pd.Timestamp(as_of)
    if any(panels.get(k) is None or len(panels[k]) == 0 for k in META["needs"]):
        return _empty()
    dt = decision_time(as_of)
    p = panels["bond_panel"]
    p = p[(p["available_at"] <= dt) & (pd.to_datetime(p["date"]) == as_of)]
    p = p[eligible(p) & p["gvkey"].notna()].drop_duplicates("cusip", keep="last")
    if p.empty:
        return _empty()
    g = panels["gics"]
    sector = sector_at(g[g["available_at"] <= dt], as_of)
    iss = pd.DataFrame({"gvkey": p["gvkey"].unique()})
    iss["gsector"] = iss["gvkey"].map(sector)
    iss = iss.merge(sector_squeeze(panels["sector_prices"], dt), on="gsector", how="left")
    iss = iss.merge(issuer_margins(panels["compustat_quarterly"], dt), on="gvkey", how="left")
    fin = iss["gsector"].isin(FIN_SECTORS)
    iss.loc[fin, ["margin", "margin_chg_12m", "margin_trend"]] = np.nan
    iss["exposure"] = margin_exposure(iss["margin"])
    iss["impact"] = squeeze_impact(iss["squeeze"], iss["exposure"])
    z_i, z_t = clipped_z(iss["impact"]), clipped_z(iss["margin_trend"].where(iss["impact"].notna()))
    iss["score"] = np.where(z_t.notna(), (z_i + trend_weight * z_t) / (1.0 + trend_weight), z_i)
    out = p[["cusip", "gvkey"]].merge(iss, on="gvkey", how="left")
    out["date"] = as_of
    out["available_at"] = dt
    return out[BOND_COLS].astype({"score": float, "squeeze": float, "margin": float}).reset_index(drop=True)
