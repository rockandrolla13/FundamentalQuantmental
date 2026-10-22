"""Excess spread to peers (ESP) and spread per turn against peers (E13 by sector and by rating). Methodology 7.2;
framework F7.7; Kricheff ch. 21; decision page docs/decisions/2026-10-22-esp-peer-groups.md.

Barclays QPS lists ESP ("Excess Spread to Peers") and SPiDER ("Spread per unit of Debt To Earnings Ratio") but does
not publish either method. The definitions here are ours:

    cell(i, t)   = GICS sector x rating class x maturity bucket at t           (the peer group)
    ESP_i        = log s_i - median over peers j of log s_j                      (excess spread to peers)
    SPT_i        = s_i / L_i                                                     (spread per turn, Kricheff; SPiDER)
    E13_cell_i   = log SPT_i - median over peers j of log SPT_j                  (spread per turn against peers)

Peers exclude the issuer's own bonds. A cell needs MIN_PEERS other issuers; otherwise the next cell in FALLBACK
applies. Positive values mean the bond pays more than its peers: cheap. Every input is point in time.

Rating class: S&P long-term issuer rating where one is on file (to February 2017). Otherwise the class implied by
leverage: cut-offs fitted on the actual ratings of the months before t (midpoints of the class medians of log
leverage). Negative or zero EBITDA maps to CCC.
"""

from __future__ import annotations

from typing import Iterable, Mapping

import numpy as np
import pandas as pd

CLASSES = ("IG", "BB", "B", "CCC")
MAT_EDGES = (3.0, 7.0)          # maturity buckets: under 3 years, 3 to 7, 7 and over
MIN_PEERS = 5                   # other issuers a cell needs
MIN_FIT = 500                   # issuer-months of actual ratings needed to fit the implied cut-offs
RATING_STALE_DAYS = 62          # a monthly rating older than this is not "on file"
FALLBACK = {"sr": ("sr", "r", "s", "all"), "s": ("s", "all"), "r": ("r", "all"), "all": ("all",)}


def rating_class(symbol: str | None) -> str | None:
    """S&P symbol to class: BBB- and better IG; BB+ to BB- BB; B+ to B- B; CCC+ and below (CC, C, SD, D) CCC."""
    if not isinstance(symbol, str) or not symbol.strip():
        return None
    base = symbol.strip().upper().rstrip("+-")
    return {"AAA": "IG", "AA": "IG", "A": "IG", "BBB": "IG", "BB": "BB", "B": "B",
            "CCC": "CCC", "CC": "CCC", "C": "CCC", "SD": "CCC", "D": "CCC"}.get(base)


def maturity_bucket(years: float) -> int:
    """0 under 3 years, 1 from 3 to 7, 2 for 7 and over."""
    return int(np.searchsorted(MAT_EDGES, years, side="right"))


def sector_at(gics: pd.DataFrame, t: pd.Timestamp) -> pd.Series:
    """GICS sector per gvkey in force at t (indfrom <= t <= indthru or open)."""
    g = gics[(gics["indfrom"] <= t) & (gics["indthru"].isna() | (gics["indthru"] >= t))]
    return g.sort_values("indfrom").drop_duplicates("gvkey", keep="last").set_index("gvkey")["gsector"].astype(str)


def rating_at(ratings: pd.DataFrame, decision_time: pd.Timestamp) -> pd.Series:
    """Actual rating class per gvkey known at the decision time; a rating older than RATING_STALE_DAYS drops out."""
    r = ratings[ratings["available_at"] <= decision_time]
    r = r[r["datadate"] >= decision_time - pd.Timedelta(days=RATING_STALE_DAYS)]
    r = r.sort_values("datadate").drop_duplicates("gvkey", keep="last")
    return r.set_index("gvkey")["splticrm"].map(rating_class).dropna()


def fit_cutoffs(log_lev: Iterable[float], classes: Iterable[str]) -> dict[str, float] | None:
    """Leverage cut-offs between classes: midpoints of adjacent class medians of log leverage, forced increasing.

    Returns {"IG|BB": c1, "BB|B": c2, "B|CCC": c3} in log leverage, or None with fewer than MIN_FIT rows.
    Intuition: a leverage closer to the typical B issuer than to the typical BB issuer reads as B.
    """
    d = pd.DataFrame({"x": list(log_lev), "c": list(classes)}).dropna()
    d = d[np.isfinite(d["x"])]
    if len(d) < MIN_FIT:
        return None
    med = d.groupby("c")["x"].median()
    if not all(c in med for c in CLASSES):
        return None
    m = [float(med[c]) for c in CLASSES]
    for i in range(1, 4):
        m[i] = max(m[i], m[i - 1] + 1e-6)
    return {f"{CLASSES[i]}|{CLASSES[i + 1]}": (m[i] + m[i + 1]) / 2 for i in range(3)}


def implied_class(leverage: float, ebitda_positive: bool, cutoffs: Mapping[str, float] | None) -> str | None:
    """Rating class implied by leverage. Non-positive EBITDA reads as CCC; no debt reads as IG."""
    if not ebitda_positive:
        return "CCC"
    if cutoffs is None or leverage != leverage:
        return None
    if leverage <= 0:
        return "IG"
    x = np.log(leverage)
    for i, key in enumerate(("IG|BB", "BB|B", "B|CCC")):
        if x < cutoffs[key]:
            return CLASSES[i]
    return "CCC"


def _cell_key(df: pd.DataFrame, level: str) -> pd.Series:
    m = df["mat"].astype(str)
    if level == "sr":
        return df["sector"].astype(str) + "|" + df["rclass"].astype(str) + "|" + m
    if level == "s":
        return df["sector"].astype(str) + "|" + m
    if level == "r":
        return df["rclass"].astype(str) + "|" + m
    return m


def _peer_median(df: pd.DataFrame, col: str, level: str) -> tuple[pd.Series, pd.Series]:
    """Leave-own-issuer-out median of `col` within the cell at `level`, and the number of other issuers."""
    key = _cell_key(df, level)
    med = pd.Series(np.nan, index=df.index)
    npeer = pd.Series(0, index=df.index)
    ok = df[col].notna() & key.notna() & ~key.str.contains("nan|None")
    for _, idx in df[ok].groupby(key[ok]).groups.items():
        cell = df.loc[idx]
        vals, issuers = cell[col].to_numpy(), cell["gvkey"].to_numpy()
        n_iss = len(set(issuers))
        for g in set(issuers):
            own = issuers == g
            rows = cell.index[own]
            npeer.loc[rows] = n_iss - 1
            if n_iss - 1 >= MIN_PEERS:
                med.loc[rows] = float(np.median(vals[~own]))
    return med, npeer


def peer_signals(bonds: pd.DataFrame, levels: Iterable[str] = ("sr", "s", "r")) -> pd.DataFrame:
    """ESP and spread per turn against peers for one date.

    `bonds` columns: gvkey, years, spread (decimal), leverage, sector, rclass. Returns, per row: mat, log_s, log_spt,
    esp_<level>, e13_<level>, and cell_<level> (the level actually used after FALLBACK).
    """
    df = bonds.copy()
    df["mat"] = df["years"].map(maturity_bucket)
    df["log_s"] = np.where(df["spread"] > 0, np.log(df["spread"].clip(lower=1e-9)), np.nan)
    spt = df["spread"] / df["leverage"]
    df["log_spt"] = np.where((df["leverage"] > 0) & (df["spread"] > 0), np.log(spt.clip(lower=1e-12)), np.nan)
    cache: dict[tuple[str, str], pd.Series] = {}
    for col in ("log_s", "log_spt"):
        for lvl in ("sr", "s", "r", "all"):
            cache[(col, lvl)] = _peer_median(df, col, lvl)[0]
    for level in levels:
        for col, name in (("log_s", "esp"), ("log_spt", "e13")):
            out = pd.Series(np.nan, index=df.index)
            used = pd.Series(None, index=df.index, dtype=object)
            for lvl in FALLBACK[level]:
                med = cache[(col, lvl)]
                fill = out.isna() & med.notna() & df[col].notna()
                out[fill] = df.loc[fill, col] - med[fill]
                used[fill] = lvl
            df[f"{name}_{level}"] = out
            df[f"cell_{name}_{level}"] = used
    return df


def live_peers(issuers: pd.DataFrame, panel: pd.DataFrame, leverage: pd.DataFrame, gics: pd.DataFrame,
               ratings: pd.DataFrame, as_of: pd.Timestamp) -> pd.DataFrame:
    """ESP and E13 against peers for live issuers, with the latest TRACE panel month at or before `as_of` as peers.

    `issuers` columns: ticker, gvkey, spread (5-year, decimal), leverage, ebitda_pos. Each issuer enters as one 5-year
    point (maturity bucket 1). The peers are the panel's bonds that month with leverage, sector and class. Cut-offs for
    the implied class are fitted on every actual rating on file (all before as_of). Returns one row per ticker with
    sector, rclass, rclass_source, esp_* and e13_* and the cell used.
    """
    month = panel.loc[panel["date"] <= as_of, "date"].max()
    p = panel[panel["date"] == month][["gvkey", "years", "g_spread"]].rename(columns={"g_spread": "spread"})
    lv = leverage[leverage["date"] == month][["gvkey", "leverage", "ltm_ebitda"]].copy()
    lv["ebitda_pos"] = lv["ltm_ebitda"].astype(float) > 0
    p = p.merge(lv.drop(columns="ltm_ebitda"), on="gvkey", how="inner")
    act_all = ratings.assign(rclass=ratings["splticrm"].map(rating_class)).dropna(subset=["rclass"])
    hist = act_all.merge(leverage[["date", "gvkey", "leverage", "ltm_ebitda"]], left_on=["gvkey", "datadate"],
                         right_on=["gvkey", "date"], how="inner")
    hist = hist[(hist["leverage"] > 0) & (hist["ltm_ebitda"].astype(float) > 0)]
    cut = fit_cutoffs(np.log(hist["leverage"].astype(float)), hist["rclass"])
    me = issuers.assign(years=5.0)
    allb = pd.concat([p.assign(ticker=None), me[["ticker", "gvkey", "years", "spread", "leverage", "ebitda_pos"]]],
                     ignore_index=True)
    allb = allb[~allb["gvkey"].isin(me["gvkey"]) | allb["ticker"].notna()]  # live issuers enter once, as the 5y point
    sec = sector_at(gics, as_of)
    act = rating_at(ratings, as_of)
    allb["sector"] = allb["gvkey"].map(sec)
    allb["rclass_actual"] = allb["gvkey"].map(act)
    allb["rclass_implied"] = [implied_class(l, bool(e), cut) for l, e in zip(allb["leverage"], allb["ebitda_pos"])]
    allb["rclass"] = allb["rclass_actual"].fillna(allb["rclass_implied"])
    allb["rclass_source"] = np.where(allb["rclass_actual"].notna(), "actual", "implied")
    out = peer_signals(allb)
    res = out[out["ticker"].notna()].set_index("ticker")
    res.attrs.update({"peer_month": str(pd.Timestamp(month).date()), "n_peer_bonds": int(len(p)),
                      "cutoffs": {k: float(np.exp(v)) for k, v in (cut or {}).items()}})
    return res
