"""Sector-relative factor scores and the sector composite. Spec docs/factors/SECTOR-models.md, section 3.2;
methodology Section 8 (composite: w proportional to max(0, IC)); Dynkin et al. (2021) ch. 13 (peers within an
industry cell, PDF p. 444) and ch. 16 (sector-neutral equity momentum, PDF pp. 543 to 545, note 4 p. 552).

    r_f,i     = pct rank of factor f's score among the scored bonds of i's GICS sector - 0.5   in (-0.5, 0.5]
    C_i       = sum_f w_f,g r_f,i / sum_f w_f,g     over the factors with a rank for bond i, g = i's group
    w_f,g     = 1 by default (equal weights); production sets w from the trailing IC per sector (ic_group_weights)
    EM_i      = (r_1m / 1 + r_3m / 3 + r_6m / 6) / 3           issuer equity momentum, %/month (ch. 16 note 4, p. 552)

Intuition: a concentrated within-sector book needs to know which names are best inside the sector, not across the
market. Ranking inside the sector removes the sector's own level, which a long-short pair inside the sector does not
earn. Dynkin et al. find the sector-neutral equity momentum sort works in each of eight HY sectors (Table 16.1, p. 545:
Q5 - Q1 from 5.94% to 30.22% a year, 2007 to 2017, before cost), which supports ranking inside the sector.

Factor keys: "sector_fs" (hy.sector.fairspread), "emc16" (EM_i above), or an int rank of hy.factors.REGISTRY. An
index-level factor has no cross-section and raises ValueError. Issuer-level scores pass to each bond of the issuer.
Without `bond_panel` or `gics` the result is an empty frame. A factor whose panels are missing gives no rank, and the
composite uses the rest.
"""

from __future__ import annotations

import importlib
from typing import Iterable, Mapping

import numpy as np
import pandas as pd

from hy.backtest import decision_time
from hy.factors import REGISTRY
from hy.peers import MIN_SECTOR, _sector_pct, equity_momentum
from hy.sector import fairspread
from hy.sector.common import month_end, present, universe
from hy.signals import ic_weights

DEFAULT_FACTORS: tuple = ("sector_fs", "emc16", 4, 10, 19)   # value, momentum, carry, cash quality (our choice)
EM_WINDOWS = (1, 3, 6)       # months of the ch. 16 equity momentum (note 4, p. 552)
MIN_COMPONENTS = 1           # ranked factors a composite needs (our choice)
HORIZON = 1                  # months: the ch. 13 and ch. 16 holding period (PDF pp. 446, 543)

META = {
    "rank": None,
    "name": "Sector-relative factor composite",
    "level": "bond",
    "horizon_months": HORIZON,
    "needs": ["bond_panel", "gics", "leverage", "ratings", "equity_monthly"],
    "spec": "docs/factors/SECTOR-models.md",
    "section": "8 composite",
}
REQUIRED = ("bond_panel", "gics")
BASE_COLS = ["date", "cusip", "score", "available_at", "gvkey", "gsector", "group", "n_components"]


# ---------------------------------------------------------------- helpers


def factor_name(key) -> str:
    """Column name of a factor key: the string itself, or fNN for a REGISTRY rank."""
    return key if isinstance(key, str) else f"f{int(key):02d}"


def within_sector_rank(x: pd.Series, sector: pd.Series, min_n: int = MIN_SECTOR) -> pd.Series:
    """Percentile rank of x within GICS sector minus 0.5; NaN where the sector has fewer than min_n values
    (hy.peers._sector_pct). Higher = better inside the sector."""
    return _sector_pct(x.astype(float), sector) - 0.5


def issuer_em(equity: pd.DataFrame, as_of, windows: tuple[int, ...] = EM_WINDOWS) -> pd.Series:
    """EM_i of the module docstring per gvkey: the mean of the compounded 1-, 3- and 6-month stock returns to month
    end as_of, each divided by its length (ch. 16 note 4, p. 552; our reading: length, not square root). Each window
    must be complete (hy.peers.equity_momentum). Only returns with available_at <= decision_time(as_of)."""
    as_of = month_end(as_of)
    dt = decision_time(as_of)
    e = equity.assign(datadate=pd.to_datetime(equity["datadate"]), available_at=pd.to_datetime(equity["available_at"]))
    parts = [equity_momentum(e, as_of, dt, months=m) / m for m in windows]
    return pd.concat(parts, axis=1).mean(axis=1, skipna=False).rename("em")


def sector_em(em: pd.Series, sector: pd.Series) -> pd.Series:
    """Equal-weight mean of issuer EM per GICS sector (ch. 16 sector momentum; equal weights our proxy for the book's
    market weights, card ch. 16 "Data we have and lack")."""
    d = pd.DataFrame({"em": em, "s": sector.reindex(em.index)}).dropna()
    return d.groupby("s")["em"].mean().rename("sector_em")


def factor_frame(key, panels: Mapping[str, pd.DataFrame], as_of, **params) -> pd.DataFrame:
    """Score frame of one factor key at as_of: columns score and cusip (bond level) or gvkey (issuer level)."""
    if key == "sector_fs":
        return fairspread.compute(panels, as_of, **params)
    if key == "emc16":
        if not present(panels, "equity_monthly"):
            return pd.DataFrame(columns=["gvkey", "score"])
        em = issuer_em(panels["equity_monthly"], as_of)
        return pd.DataFrame({"gvkey": em.index, "score": em.to_numpy()})
    if isinstance(key, str) or int(key) not in REGISTRY:
        raise ValueError(f"unknown factor key {key!r}")
    mod = importlib.import_module(REGISTRY[int(key)])
    if mod.META["level"] == "index":
        raise ValueError(f"factor {key} is index level: no cross-section to rank within a sector")
    return mod.compute(panels, as_of, **params)


def to_bonds(frame: pd.DataFrame, bonds: pd.DataFrame) -> pd.Series:
    """Score per universe bond: by cusip when the frame has cusips, else the issuer score by gvkey."""
    if frame is None or frame.empty or "score" not in frame:
        return pd.Series(np.nan, index=bonds.index)
    f = frame.dropna(subset=["score"])
    if "cusip" in f and f["cusip"].notna().any():
        return bonds["cusip"].map(f.drop_duplicates("cusip", keep="last").set_index("cusip")["score"]).astype(float)
    return bonds["gvkey"].map(f.drop_duplicates("gvkey", keep="last").set_index("gvkey")["score"]).astype(float)


def weights_for(weights, group: str, names: Iterable[str]) -> pd.Series:
    """Weights of the factors `names` in `group`. weights None: all 1. A flat mapping {factor: w} applies to every
    group. A nested mapping {group: {factor: w}} applies per group, with key "default" for groups not named. A factor
    not named gets 0. A negative weight raises ValueError."""
    names = list(names)
    if weights is None:
        return pd.Series(1.0, index=names)
    if weights and all(isinstance(v, Mapping) for v in weights.values()):
        weights = weights.get(group, weights.get("default"))
        if weights is None:
            return pd.Series(1.0, index=names)
    w = pd.Series({n: float(weights.get(n, 0.0)) for n in names}, dtype=float)
    if (w < 0).any():
        raise ValueError("composite weights must be non-negative (Section 8: w proportional to max(0, IC))")
    return w


def ic_group_weights(ic: pd.DataFrame) -> dict[str, dict[str, float]]:
    """Per-group weights from a trailing IC table (rows = factor names, columns = groups), w proportional to
    max(0, IC) (Section 8; hy.signals.ic_weights). A group where no factor has a positive IC gets all zero, so its
    composite is NaN: no factor has earned a vote there."""
    return {g: ic_weights(ic, g).to_dict() for g in ic.columns}


# ---------------------------------------------------------------- panel step


def compute(panels: Mapping[str, pd.DataFrame], as_of, factors: Iterable = DEFAULT_FACTORS, weights=None,
            frames: Mapping[str, pd.DataFrame] | None = None, min_components: int = MIN_COMPONENTS) -> pd.DataFrame:
    """Sector composite per bond at month end as_of (spec section 3.2). Columns BASE_COLS then rank_<factor>.

    `frames` gives precomputed score frames by factor name (factor_name), so production can reuse its runs. score =
    the weighted mean of the within-sector ranks the bond has; NaN with fewer than `min_components` ranks of positive
    weight. Higher = long."""
    as_of = month_end(as_of)
    names = [factor_name(f) for f in factors]
    cols = BASE_COLS + [f"rank_{n}" for n in names]
    if any(not present(panels, k) for k in REQUIRED):
        return pd.DataFrame(columns=cols)
    u = universe(panels, as_of)
    if u.empty:
        return pd.DataFrame(columns=cols)
    for key, name in zip(factors, names):
        fr = frames[name] if frames is not None and name in frames else factor_frame(key, panels, as_of)
        u[f"rank_{name}"] = within_sector_rank(to_bonds(fr, u), u["gsector"])
    R = u[[f"rank_{n}" for n in names]]
    score = pd.Series(np.nan, index=u.index)
    n_comp = pd.Series(0, index=u.index)
    for grp, idx in u.groupby("group").groups.items():
        w = weights_for(weights, grp, names).to_numpy()
        r = R.loc[idx].to_numpy(float)
        has = np.isfinite(r) & (w > 0)
        wsum = (has * w).sum(axis=1)
        val = np.where(has, r, 0.0) @ w
        n_comp.loc[idx] = has.sum(axis=1)
        ok = (has.sum(axis=1) >= min_components) & (wsum > 0)
        score.loc[idx] = np.where(ok, val / np.where(wsum > 0, wsum, 1.0), np.nan)
    u["score"], u["n_components"] = score, n_comp.astype(int)
    u["date"], u["available_at"] = as_of, decision_time(as_of)
    return u[cols].reset_index(drop=True)
