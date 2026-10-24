"""The Wolfe Trahan sector rotation claims as 15 rules, tested at three layers (decision page
docs/decisions/2026-10-24-wt-sector-rules.md, specification S1-S10; methodology Section 8 and 5.2).

Layer 1: firm fundamentals (EBITDA for R1-R8, ROE for R9-R15), all US firms and HY issuers.
Layer 2: HY bond credit excess returns per sector (TRACE panel).
Layer 3: stock returns per sector (CRSP, 500 largest US common stocks).

Run after scripts/pull_sector_data.py and scripts/backtest_alpha.py --tag full:
    PYTHONPATH=. python3 scripts/wt_sector_rules.py [--draws 1000]
Writes data/raw/backtest/wt_sector_rules.json.

Pre-run clarification (recorded on the decision page): P4 multiplies the signal by the outcome minus its own mean
known at t (outcomes complete by t), so a pair that always grows faster does not count as a hit.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t as t_dist

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from hy.backtest import CYCLE_WINDOWS  # noqa: E402
from wt_robustness import ewc_nu, har_t, lrv_ewc, romano_wolf, stationary_bootstrap_index  # noqa: E402
from wt_tests import clark_west, load_fred_monthly, load_survey  # noqa: E402

OOS_START_M = pd.Period("2012-01", "M")
OOS_START_Q = pd.Period("2012Q1", "Q")
Z_MIN_MONTHS = 60
MIN_LTM_SALES = 40.0
MIN_FIRMS = {"all": 20, "hy": 5}
MIN_BONDS = 10
MIN_STOCKS = 5
TOP_STOCKS = 500
K_PRIMARY = 4
BLOCK_MONTHS = 24
WINDOWS_STOCK = {2001: ("2001-01-01", "2002-12-31"), **CYCLE_WINDOWS}
SEED = 20261024

# Groups: a list of (level, code). level "s" = GICS sector, "g" = industry group, "all" = every firm.
HYPER = [("s", "45"), ("s", "40")]
COUNTER = [("s", "35"), ("s", "30"), ("s", "55")]
EARLY = [("s", "25")]
LATE = [("s", "20")]
LATE_WIDE = [("s", "20"), ("s", "15"), ("s", "10")]
MARKET = [("all", "")]
FIN = [("s", "40")]
NONFIN = [("not_s", "40")]
REAL_ESTATE = [("s", "60"), ("g", "4040")]

RULES = {
    "R1": dict(rows="85, 130", signal="gac", sign=+1, h=3, long=HYPER, short=COUNTER, fin=False),
    "R2": dict(rows="152", signal="cpi", sign=-1, h=6, long=HYPER, short=COUNTER, fin=False),
    "R3": dict(rows="73, 96", signal="cpi", sign=-1, h=3, long=EARLY, short=LATE, fin=False),
    "R4": dict(rows="94", signal="ppc", sign=+1, h=3, long=LATE, short=EARLY, fin=False),
    "R5": dict(rows="47", signal="cpi", sign=-1, h=3, long=EARLY, short=MARKET, fin=False),
    "R6": dict(rows="78", signal="oil", sign=+1, h=3, long=[("s", "10")], short=EARLY, fin=False),
    "R7": dict(rows="114", signal="gs10", sign=-1, h=3, long=[("s", "55")], short=MARKET, fin=False),
    "R8": dict(rows="115", signal="gac", sign=-1, h=3, long=[("s", "55")], short=MARKET, fin=False),
    "R9": dict(rows="55", signal="noc", sign=+1, h=3, long=FIN, short=MARKET, fin=True),
    "R10": dict(rows="57, 63", signal="gac", sign=+1, h=3, long=FIN, short=MARKET, fin=True),
    "R11": dict(rows="61", signal="gs10", sign=+1, h=3, long=FIN, short=NONFIN, fin=True),
    "R12": dict(rows="66", signal="ppc", sign=+1, h=6, long=REAL_ESTATE, short=FIN, fin=True),
    "R13": dict(rows="103", signal="oeh", sign=+1, h=3, long=FIN, short=MARKET, fin=True),
    "R14": dict(rows="133", signal="hsn", sign=+1, h=3, long=[("g", "4010")], short=MARKET, fin=True),
    "R15": dict(rows="64", signal="gac", sign=+1, h=3, long=[("g", "4020")], short=[("g", "4030")], fin=True),
}
LEVEL_SIGNALS = ("gac", "noc", "ppc")  # diffusion indexes enter as levels; the rest as 12-month changes


def data_root() -> Path:
    return Path(os.environ["HY_DATA_ROOT"]) if os.environ.get("HY_DATA_ROOT") else ROOT / "data" / "raw"


# ---------------------------------------------------------------------------
# S2. Signals
# ---------------------------------------------------------------------------


def expanding_z(x: pd.Series, min_obs: int = Z_MIN_MONTHS) -> pd.Series:
    """z_t = (x_t - mean(x_s, s <= t)) / sd(x_s, s <= t) with at least `min_obs` values (spec S2.2)."""
    x = x.dropna()
    m, s = x.expanding(min_obs).mean(), x.expanding(min_obs).std()
    return (x - m) / s


def owners_equity_monthly(path: Path) -> pd.Series:
    """Household owners' equity, quarterly (Z.1). A quarter dated at its first month is known 3 months after the
    quarter end: dated 2020-01 (Q1, ends March) is known from June 2020. Forward filled to months."""
    df = pd.read_csv(path, na_values=".")
    s = pd.Series(df.iloc[:, 1].astype(float).to_numpy(), index=pd.to_datetime(df.iloc[:, 0]).dt.to_period("M"))
    s.index = s.index + 2 + 3
    return s


def raw_signals(macro_dir: Path, sector_dir: Path, alt: bool = False) -> pd.DataFrame:
    """X_t per month, known at month end (spec S2.1). `alt` swaps the transform (robustness S8.1): diffusion
    indexes become 6-month changes, the change series become levels."""
    sv = load_survey(macro_dir / "bos_dif.csv")
    out = {}
    for name, col in (("gac", "GAC"), ("noc", "NOC"), ("ppc", "PPC")):
        x = sv[col]
        out[name] = x.diff(6) if alt else x
    def chg12(s, log=True):
        if alt:
            return s
        return 100 * np.log(s / s.shift(12)) if log else s - s.shift(12)
    out["cpi"] = chg12(load_fred_monthly(macro_dir / "CPIAUCNS.csv", 1))
    out["oil"] = chg12(load_fred_monthly(macro_dir / "WTISPLC.csv", 0))
    out["gs10"] = chg12(load_fred_monthly(macro_dir / "GS10.csv", 0), log=False)
    out["hsn"] = chg12(load_fred_monthly(sector_dir / "fred_HSN1F.csv", 1))
    oeh = owners_equity_monthly(sector_dir / "fred_OEHRENWBSHNO.csv")
    oeh_x = oeh if alt else 100 * np.log(oeh / oeh.shift(4))
    idx = pd.period_range("1960-01", max(v.index.max() for v in out.values()), freq="M")
    out["oeh"] = oeh_x.reindex(idx).ffill(limit=3)
    return pd.DataFrame({k: v.reindex(idx) for k, v in out.items()})


def standardise(raw: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({c: expanding_z(raw[c]) for c in raw}).reindex(raw.index)


# ---------------------------------------------------------------------------
# S3. Groups
# ---------------------------------------------------------------------------


def gics_at(keys: pd.DataFrame, gics: pd.DataFrame) -> pd.DataFrame:
    """GICS sector and group of each (gvkey, date): the record with indfrom <= date <= indthru. Before a firm's
    first record (GICS history starts in the late 1990s), its first record applies. Returns gsector, ggroup."""
    g = gics.copy()
    g["gvkey"] = g["gvkey"].astype(str)
    g["indfrom"] = pd.to_datetime(g["indfrom"])
    g["indthru"] = pd.to_datetime(g["indthru"])
    first = g.groupby("gvkey")["indfrom"].transform("min")
    g.loc[g["indfrom"] == first, "indfrom"] = pd.Timestamp("1900-01-01")
    k = keys[["gvkey", "date"]].copy()
    k["gvkey"] = k["gvkey"].astype(str)
    k["_i"] = np.arange(len(k))
    m = k.merge(g, on="gvkey", how="left")
    ok = (m["indfrom"] <= m["date"]) & (m["indthru"].isna() | (m["date"] <= m["indthru"]))
    m = m[ok].sort_values("indfrom").drop_duplicates("_i", keep="last").set_index("_i")
    out = pd.DataFrame(index=np.arange(len(k)))
    out["gsector"] = m["gsector"].astype(object).reindex(out.index).fillna("NA").astype(str)
    out["ggroup"] = m["ggroup"].astype(object).reindex(out.index).fillna("NA").astype(str)
    out.index = keys.index
    return out


def in_group(gsector: pd.Series, ggroup: pd.Series, spec: list) -> pd.Series:
    """Membership of each row in a group spec (spec S3.2)."""
    hit = pd.Series(False, index=gsector.index)
    for level, code in spec:
        if level == "all":
            hit |= gsector.notna() & (gsector != "NA")
        elif level == "s":
            hit |= gsector == code
        elif level == "not_s":
            hit |= gsector.notna() & (gsector != "NA") & (gsector != code)
        elif level == "g":
            hit |= ggroup == code
    return hit


# ---------------------------------------------------------------------------
# S4. Layer 1: firm outcomes
# ---------------------------------------------------------------------------


def firm_wide(fq: pd.DataFrame) -> tuple[dict[str, pd.DataFrame], pd.PeriodIndex]:
    """Wide firm x calendar-quarter matrices: LTM sales, EBITDA, IB (sums of 4 consecutive quarters, a gap gives
    NaN), and point values of CEQ, AT and debt. Sales = saleq, else revtq (banks)."""
    df = fq.dropna(subset=["datacqtr"]).copy()
    df["q"] = pd.PeriodIndex(df["datacqtr"].str.replace("Q", "-Q"), freq="Q")
    df = df.sort_values("datadate").drop_duplicates(["gvkey", "q"], keep="last")
    df["sales"] = df["saleq"].fillna(df["revtq"])
    df["debt"] = df["dlttq"].fillna(0.0) + df["dlcq"].fillna(0.0)
    cols = pd.period_range(df["q"].min(), df["q"].max(), freq="Q")
    W = {}
    for c, name in (("sales", "S"), ("oibdpq", "E"), ("ibq", "IB")):
        w = df.pivot(index="gvkey", columns="q", values=c).reindex(columns=cols)
        W[name] = w.T.rolling(4, min_periods=4).sum().T
    for c, name in (("ceqq", "CEQ"), ("atq", "AT"), ("debt", "D")):
        W[name] = df.pivot(index="gvkey", columns="q", values=c).reindex(columns=cols)
    big = W["S"] > MIN_LTM_SALES
    for k in W:
        W[k] = W[k].where(big)
    return W, cols


def winsor_cols(x: pd.DataFrame, p: float = 0.01) -> pd.DataFrame:
    return x.clip(lower=x.quantile(p), upper=x.quantile(1 - p), axis=1)


def firm_outcome(W: dict, name: str, k: int) -> pd.DataFrame:
    """Firm outcome at quarter q over q -> q+k (spec S4). Columns are q."""
    S, E, IB = W["S"], W["E"], W["IB"]
    fwd = lambda X: X.shift(-k, axis=1)  # noqa: E731
    if name == "d_ebitda":
        y = (fwd(E) - E) / S
    elif name == "d_earn":
        y = (fwd(IB) - IB) / S
    elif name == "d_roe":
        y = (fwd(IB) - IB) / W["CEQ"].where(W["CEQ"] > 0)
    elif name == "d_margin":
        y = fwd(E / S) - E / S
    elif name == "d_margin_fin":
        r = IB / W["AT"].where(W["AT"] > 0)
        y = fwd(r) - r
    elif name == "g_sales":
        y = np.log(fwd(S) / S)
    elif name == "d_lev":
        lev = (W["D"] / E.where(E > 0)).clip(0, 20)
        y = fwd(lev) - lev
    else:
        raise ValueError(name)
    return winsor_cols(y.replace([np.inf, -np.inf], np.nan))


def quarter_membership(S: pd.DataFrame, gics: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """gsector and ggroup of each firm at each quarter end (wide, firm x quarter), for the observed cells of S."""
    keys = S.stack().reset_index()[["gvkey", "q"]] if S.columns.name == "q" else S.stack().reset_index().iloc[:, :2]
    keys.columns = ["gvkey", "q"]
    keys["date"] = keys["q"].dt.to_timestamp(how="end").dt.normalize()
    g = gics_at(keys, gics)
    keys["gsector"], keys["ggroup"] = g["gsector"].to_numpy(), g["ggroup"].to_numpy()
    sec = keys.pivot(index="gvkey", columns="q", values="gsector").reindex(index=S.index, columns=S.columns)
    grp = keys.pivot(index="gvkey", columns="q", values="ggroup").reindex(index=S.index, columns=S.columns)
    return sec, grp


def group_stat(Y: pd.DataFrame, member: pd.DataFrame, min_n: int, weights: pd.DataFrame | None = None) -> pd.Series:
    """Median firm per quarter (or the weighted mean when `weights` is given, robustness S8.3)."""
    Ym = Y.where(member & Y.notna())
    n = Ym.notna().sum()
    if weights is None:
        v = Ym.median()
    else:
        w = weights.where(Ym.notna())
        v = (Ym * w).sum() / w.sum()
    return v.where(n >= min_n)


def wide_member(sec: pd.DataFrame, grp: pd.DataFrame, spec: list) -> pd.DataFrame:
    out = pd.DataFrame(False, index=sec.index, columns=sec.columns)
    for c in sec.columns:
        out[c] = in_group(sec[c], grp[c], spec).to_numpy()
    return out


# ---------------------------------------------------------------------------
# S5. Layers 2 and 3: returns
# ---------------------------------------------------------------------------


def bond_returns(results: pd.DataFrame, gics: pd.DataFrame) -> pd.DataFrame:
    """Per bond-month: credit excess return x = total - tsy_ret (winsorised per month), gsector, ggroup."""
    b = results.dropna(subset=["gvkey", "total", "tsy_ret"]).copy()
    b["x"] = b["total"] - b["tsy_ret"]
    lo = b.groupby("date")["x"].transform(lambda v: v.quantile(0.01))
    hi = b.groupby("date")["x"].transform(lambda v: v.quantile(0.99))
    b["x"] = b["x"].clip(lo, hi)
    b["date"] = pd.to_datetime(b["date"])
    g = gics_at(b[["gvkey", "date"]], gics)
    b["gsector"], b["ggroup"] = g["gsector"], g["ggroup"]
    b["m"] = b["date"].dt.to_period("M")
    return b[["m", "gvkey", "x", "gsector", "ggroup"]]


def stock_panel(msf: pd.DataFrame, link: pd.DataFrame, gics: pd.DataFrame, horizons: tuple[int, ...]) -> pd.DataFrame:
    """The TOP_STOCKS largest stocks at each month end t, their market value at t, the compounded return over
    t+1..t+h for each h (months after a delisting count as 0), and their GICS at t through the CCM link."""
    m = msf.copy()
    m["m"] = pd.to_datetime(m["date"]).dt.to_period("M")
    m["me"] = m["prc"].abs() * m["shrout"]
    R = m.pivot_table(index="m", columns="permno", values="ret_total", aggfunc="last").sort_index()
    R = R.reindex(pd.period_range(R.index.min(), R.index.max(), freq="M"))
    L = np.log1p(R.fillna(0.0))
    C = L.cumsum()
    top = m.dropna(subset=["me"]).sort_values("me", ascending=False).groupby("m").head(TOP_STOCKS)
    out = top[["m", "permno", "me"]].copy()
    ri = R.index.get_indexer(out["m"])
    ci = R.columns.get_indexer(out["permno"])
    first = R.shift(-1).to_numpy()[ri, ci]
    for h in horizons:
        fwd = np.expm1((C.shift(-h) - C).to_numpy()[ri, ci])
        out[f"r{h}"] = np.where(np.isfinite(first), fwd, np.nan)  # need the first month after t
    out["date"] = out["m"].dt.to_timestamp(how="end").dt.normalize()
    lk = link.dropna(subset=["permno"]).copy()
    lk["permno"] = lk["permno"].astype(int)
    lk["gvkey"] = lk["gvkey"].astype(str)
    out["permno"] = out["permno"].astype(int)
    lk["linkdt"] = pd.to_datetime(lk["linkdt"])
    lk["linkenddt"] = pd.to_datetime(lk["linkenddt"]).fillna(pd.Timestamp("2100-01-01"))
    j = out.reset_index().merge(lk[["permno", "gvkey", "linkdt", "linkenddt", "linkprim"]], on="permno", how="left")
    j = j[(j["linkdt"] <= j["date"]) & (j["date"] <= j["linkenddt"])]
    j = j.sort_values("linkprim", ascending=False).drop_duplicates("index").set_index("index")
    out["gvkey"] = j["gvkey"].reindex(out.index)
    out = out.dropna(subset=["gvkey"])
    g = gics_at(out[["gvkey", "date"]], gics)
    out["gsector"], out["ggroup"] = g["gsector"], g["ggroup"]
    return out


def pair_returns(df: pd.DataFrame, value: str, rule: dict, min_n: int, weight: str | None,
                 long: list | None = None, short: list | None = None) -> pd.Series:
    """Long minus short group return per month (equal weight, or weighted by `weight`)."""
    out = {}
    for side, spec in (("L", long or rule["long"]), ("S", short or rule["short"])):
        mem = in_group(df["gsector"], df["ggroup"], spec) & df[value].notna()
        d = df[mem]
        if weight is None:
            g = d.groupby("m")[value].agg(["mean", "size"])
            v = g["mean"]
        else:
            g = d.assign(wv=d[value] * d[weight]).groupby("m").agg(wv=("wv", "sum"), w=(weight, "sum"),
                                                                     size=(value, "size"))
            v = g["wv"] / g["w"]
        out[side] = v.where(g["size"] >= min_n)
    return (out["L"] - out["S"]).dropna()


# ---------------------------------------------------------------------------
# S6, S7. Scoring
# ---------------------------------------------------------------------------


def ewc_slope(y: np.ndarray, X: np.ndarray, j: int = 1) -> dict:
    """OLS slope j with EWC errors (LLSW 2018): t, nu, one-sided p from Student t_nu."""
    T = len(y)
    if T < 12:
        return {"b": np.nan, "t": np.nan, "p": np.nan, "T": T, "nu": None}
    nu = ewc_nu(T)
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    t = har_t(y, X, j, lambda v: lrv_ewc(v, nu))
    return {"b": float(b[j]), "t": float(t), "p": float(1 - t_dist.cdf(t, nu)), "T": T, "nu": nu}


def design(y: pd.Series, zs: pd.Series, control: pd.Series | None) -> pd.DataFrame:
    d = pd.concat([y.rename("y"), zs.rename("z")], axis=1)
    if control is not None:
        d["c"] = control
    return d.dropna()


def regress(d: pd.DataFrame) -> dict:
    X = np.column_stack([np.ones(len(d)), d["z"].to_numpy()] + ([d["c"].to_numpy()] if "c" in d else []))
    return ewc_slope(d["y"].to_numpy(), X, 1)


def centred(y: pd.Series, k: int) -> pd.Series:
    """y_t minus the mean of outcomes complete by t (those with start date <= t - k), spec P4 clarification.
    `y` must carry every period (full_index)."""
    known = y.shift(k).expanding(8).mean()
    return y - known


def cycle_hits(d: pd.DataFrame, k: int, windows: dict) -> dict:
    yf = d["y"].reindex(pd.period_range(d.index.min(), d.index.max(), freq=d.index.freq))
    yc = centred(yf, k).reindex(d.index)
    prod = d["z"] * yc
    ts = prod.index.to_timestamp()
    out = {}
    for w, (a, b) in windows.items():
        v = prod[(ts >= pd.Timestamp(a)) & (ts <= pd.Timestamp(b))].dropna()
        out[str(w)] = {"n": int(len(v)), "mean": float(v.mean()) if len(v) else None}
    return out


def score(y: pd.Series, zs: pd.Series, control: pd.Series | None, k: int, oos: pd.Period, windows: dict,
          need: int) -> dict:
    """P1, P3, P4 for one rule on one layer (P2 needs the family; see family_rw)."""
    d = design(y, zs, control)
    if len(d) < 24:
        return {"status": "no data", "n": int(len(d))}
    ins, out = d[d.index < oos], d[d.index >= oos]
    r_in, r_out = regress(ins) if len(ins) >= 12 else {}, regress(out)
    base = d[["c"]] if "c" in d else d[[]]
    cw = clark_west(d["y"], base, d.drop(columns="y"), k=k, start=oos)
    cyc = cycle_hits(d, k, windows)
    hits = sum(1 for v in cyc.values() if v["mean"] is not None and v["mean"] > 0)
    testable = sum(1 for v in cyc.values() if v["mean"] is not None)
    res = {"status": "ok", "n": int(len(d)), "first": str(d.index[0]), "in_sample": r_in, "oos": r_out,
           "clark_west": cw, "cycles": cyc, "cycle_hits": hits, "cycle_testable": testable}
    res["P1"] = bool(np.isfinite(r_out["t"]) and r_out["b"] > 0 and r_out["p"] < 0.05)
    res["P3"] = bool(np.isfinite(cw.get("p", np.nan)) and cw["p"] < 0.05)
    res["P4"] = bool(testable >= need and hits >= need)
    return res


def holm(p: dict) -> dict:
    keys = [k for k, v in p.items() if v is not None and np.isfinite(v)]
    order = sorted(keys, key=lambda k: p[k])
    m, out, prev = len(order), {}, 0.0
    for i, k in enumerate(order):
        prev = max(prev, min(1.0, (m - i) * p[k]))
        out[k] = prev
    return out


# ---------------------------------------------------------------------------
# Layer builders: each returns {rule: (y, zs, control, k)} for a given signal frame
# ---------------------------------------------------------------------------


def layer1_series(W: dict, sec: pd.DataFrame, grp: pd.DataFrame, rows: pd.Index, min_n: int, k: int = K_PRIMARY,
                  weighted: bool = False, late: list | None = None) -> dict:
    """Pair outcome P_q for each rule (primary outcome), restricted to firms in `rows`."""
    cache, out = {}, {}
    wts = W["S"] if weighted else None
    for rid, r in RULES.items():
        name = "d_roe" if r["fin"] else "d_ebitda"
        if (name, k) not in cache:
            cache[(name, k)] = firm_outcome(W, name, k).loc[rows]
        Y = cache[(name, k)]
        lg, sh = r["long"], r["short"]
        if late is not None:
            lg = late if lg == LATE else lg
            sh = late if sh == LATE else sh
        ml = wide_member(sec.loc[rows], grp.loc[rows], lg)
        ms = wide_member(sec.loc[rows], grp.loc[rows], sh)
        w = wts.loc[rows] if wts is not None else None
        P = group_stat(Y, ml, min_n, w) - group_stat(Y, ms, min_n, w)
        out[rid] = P.dropna()
    return out


def at_quarter_end(zm: pd.Series) -> pd.Series:
    q = zm[zm.index.month % 3 == 0]
    q.index = q.index.asfreq("Q")
    return q


def full_index(y: pd.Series, freq: str) -> pd.Series:
    """Reindex to every period between the first and last, so a shift by k moves k periods, not k rows."""
    return y.reindex(pd.period_range(y.index.min(), y.index.max(), freq=freq))


def run_family(series: dict, Z: pd.DataFrame, freq: str, k_of: Callable[[str], int], control: bool,
               windows: dict, need: int, shift_months: int = 0, drop_2020: bool = False) -> dict:
    """Score the 15 rules of one layer. `series[rid]` is the pair outcome indexed by Period (Q or M)."""
    oos = OOS_START_Q if freq == "Q" else OOS_START_M
    res = {}
    for rid, r in RULES.items():
        y = series.get(rid)
        if y is None or len(y) == 0:
            res[rid] = {"status": "no data", "n": 0}
            continue
        y = full_index(y, freq)
        zm = r["sign"] * Z[r["signal"]].shift(shift_months)
        zs = at_quarter_end(zm) if freq == "Q" else zm
        k = k_of(rid)
        c = y.shift(k) if control else None
        if drop_2020:
            keep = y.index.year != 2020
            y = y[keep]
        res[rid] = score(y, zs, c, k, oos, windows, need)
    return res


def family_rw(series: dict, Z: pd.DataFrame, freq: str, k_of: Callable[[str], int], control: bool,
              draws: int, seed: int = SEED) -> dict:
    """Romano-Wolf stepdown p across the 15 rules (spec P2). Null draws: one stationary bootstrap index on the
    monthly signal frame per draw, shared by all rules (block mean BLOCK_MONTHS); outcomes and controls fixed."""
    oos = OOS_START_Q if freq == "Q" else OOS_START_M
    rids = [r for r in RULES if series.get(r) is not None and len(series[r])]
    def t_obs_for(Zx):
        ts = []
        for rid in rids:
            r = RULES[rid]
            zm = r["sign"] * Zx[r["signal"]]
            zs = at_quarter_end(zm) if freq == "Q" else zm
            y = full_index(series[rid], freq)
            k = k_of(rid)
            d = design(y, zs, y.shift(k) if control else None)
            d = d[d.index >= oos]
            ts.append(regress(d)["t"] if len(d) >= 12 else np.nan)
        return np.array(ts)
    t_obs = t_obs_for(Z)
    Zv = Z.dropna(how="all")
    rng = np.random.default_rng(seed)
    null = np.empty((draws, len(rids)))
    for i in range(draws):
        idx = stationary_bootstrap_index(len(Zv), BLOCK_MONTHS, rng)
        Zb = pd.DataFrame(Zv.to_numpy()[idx], index=Zv.index, columns=Zv.columns)
        null[i] = t_obs_for(Zb)
    p = romano_wolf(t_obs, null)
    return {rid: float(pv) for rid, pv in zip(rids, p)}


def finish(res: dict, rw: dict | None) -> dict:
    hp = holm({rid: v.get("oos", {}).get("p") for rid, v in res.items() if v.get("status") == "ok"})
    for rid, v in res.items():
        if v.get("status") != "ok":
            continue
        v["holm_p"] = hp.get(rid)
        v["rw_p"] = rw.get(rid) if rw else None
        v["P2"] = bool(v["rw_p"] is not None and v["rw_p"] < 0.05)
        v["pass"] = v["P1"] and v["P2"] and v["P3"] and v["P4"]
    return res


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def hy_gvkeys_by_quarter(panel: pd.DataFrame) -> dict:
    p = panel.dropna(subset=["gvkey"])
    if "link_ambiguous" in p:
        p = p[~p["link_ambiguous"].fillna(False).astype(bool)]
    p = p.assign(q=pd.to_datetime(p["date"]).dt.to_period("Q"), gvkey=p["gvkey"].astype(str))
    return p.groupby("q")["gvkey"].agg(set).to_dict()


def restrict_hy(W: dict, hyq: dict) -> dict:
    """Mask firm-quarters that are not HY issuers at q."""
    mask = pd.DataFrame(False, index=W["S"].index, columns=W["S"].columns)
    for q, keys in hyq.items():
        if q in mask.columns:
            mask[q] = mask.index.isin(list(keys))
    return {k: v.where(mask) for k, v in W.items()}


def as_float(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """WRDS returns nullable extension dtypes (Float64 with pd.NA); cast to float64 with NaN for numpy code."""
    for c in cols:
        if c in df:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")
    return df


def main(argv=None) -> dict:
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=1000)
    a = ap.parse_args(argv)
    root = data_root()
    sd = root / "sector_rules"
    raw = raw_signals(root / "macro", sd)
    Z = standardise(raw)
    Z_alt = standardise(raw_signals(root / "macro", sd, alt=True))
    gics = pd.read_parquet(sd / "gics_hist.parquet")
    out = {"rules": {rid: {k: v for k, v in r.items() if k not in ("long", "short")} | {
        "long": r["long"], "short": r["short"]} for rid, r in RULES.items()}}

    # Layer 1
    fq = as_float(pd.read_parquet(sd / "fundq_all.parquet"),
                  ["saleq", "revtq", "oibdpq", "ibq", "atq", "ceqq", "dlttq", "dlcq"])
    fq["gvkey"] = fq["gvkey"].astype(str)
    fq["datacqtr"] = fq["datacqtr"].astype(object)
    W, quarters = firm_wide(fq)
    quarters = quarters[(quarters >= pd.Period("1994Q1", "Q"))]
    W = {k: v[quarters] for k, v in W.items()}
    firms = W["S"].index[W["S"].notna().any(axis=1)]
    W = {k: v.loc[firms] for k, v in W.items()}
    print(f"layer 1: {len(firms):,} firms, {len(quarters)} quarters")
    sec, grp = quarter_membership(W["S"], gics)
    panel = pd.read_parquet(root / "backtest" / "panel_full.parquet", columns=["date", "gvkey", "link_ambiguous"])
    W_hy = restrict_hy(W, hy_gvkeys_by_quarter(panel))
    kq = lambda rid: K_PRIMARY  # noqa: E731
    L1 = {"all": layer1_series(W, sec, grp, firms, MIN_FIRMS["all"]),
          "hy": layer1_series(W_hy, sec, grp, firms, MIN_FIRMS["hy"])}
    out["layer1"] = {}
    for u, ser in L1.items():
        res = run_family(ser, Z, "Q", kq, True, CYCLE_WINDOWS, 3)
        rw = family_rw(ser, Z, "Q", kq, True, a.draws)
        out["layer1"][u] = finish(res, rw)
        print(f"layer 1 {u}: done")

    # Layer 2
    br = {h: bond_returns(pd.read_parquet(root / "backtest" / f"results_h{h}_full.parquet"), gics) for h in (3, 6)}
    L2 = {rid: pair_returns(br[r["h"]], "x", r, MIN_BONDS, None) for rid, r in RULES.items()}
    km = lambda rid: RULES[rid]["h"]  # noqa: E731
    res = run_family(L2, Z, "M", km, False, CYCLE_WINDOWS, 3)
    out["layer2"] = finish(res, family_rw(L2, Z, "M", km, False, a.draws))
    print("layer 2: done")

    # Layer 3
    msf = as_float(pd.read_parquet(sd / "crsp_msf.parquet"), ["ret", "prc", "shrout", "dlret", "ret_total"])
    link = pd.read_parquet(sd / "ccm_link.parquet")
    sp = stock_panel(msf, link, gics, (3, 6))
    L3 = {rid: pair_returns(sp, f"r{r['h']}", r, MIN_STOCKS, "me") for rid, r in RULES.items()}
    res = run_family(L3, Z, "M", km, False, WINDOWS_STOCK, 4)
    out["layer3"] = finish(res, family_rw(L3, Z, "M", km, False, a.draws))
    print("layer 3: done")

    # S8 robustness: sign and OOS t of each variant (never used to pass)
    rob = {}
    variants = {
        "alt_transform": dict(Z=Z_alt),
        "lead_minus_1q": dict(shift=-3),
        "lead_plus_1q": dict(shift=3),
        "ex_2020": dict(drop_2020=True),
    }
    for vname, v in variants.items():
        Zv = v.get("Z", Z)
        s = v.get("shift", 0)
        d20 = v.get("drop_2020", False)
        rob[vname] = {
            "layer1_all": run_family(L1["all"], Zv, "Q", kq, True, CYCLE_WINDOWS, 3, s, d20),
            "layer2": run_family(L2, Zv, "M", km, False, CYCLE_WINDOWS, 3, s, d20),
            "layer3": run_family(L3, Zv, "M", km, False, WINDOWS_STOCK, 4, s, d20),
        }
    rob["k2"] = {"layer1_all": run_family(layer1_series(W, sec, grp, firms, MIN_FIRMS["all"], k=2), Z, "Q",
                                          lambda rid: 2, True, CYCLE_WINDOWS, 3)}
    rob["sales_weighted"] = {"layer1_all": run_family(
        layer1_series(W, sec, grp, firms, MIN_FIRMS["all"], weighted=True), Z, "Q", kq, True, CYCLE_WINDOWS, 3)}
    wide1 = layer1_series(W, sec, grp, firms, MIN_FIRMS["all"], late=LATE_WIDE)
    wide2 = {rid: pair_returns(br[r["h"]], "x", r, MIN_BONDS, None,
                               long=LATE_WIDE if r["long"] == LATE else None,
                               short=LATE_WIDE if r["short"] == LATE else None) for rid, r in RULES.items()
             if LATE in (r["long"], r["short"])}
    rob["late_wide"] = {"layer1_all": run_family({k: wide1[k] for k in ("R3", "R4")}, Z, "Q", kq, True,
                                                 CYCLE_WINDOWS, 3),
                        "layer2": run_family(wide2, Z, "M", km, False, CYCLE_WINDOWS, 3)}
    out["robustness"] = rob
    out["robust_share"] = robust_share(out)

    path = root / "backtest" / "wt_sector_rules.json"
    path.write_text(json.dumps(out, indent=1, default=_json))
    print_summary(out)
    return out


def robust_share(out: dict) -> dict:
    """Spec S8.7: per rule and layer, the share of variants whose OOS slope keeps the claimed sign (b > 0)."""
    share = {}
    for layer in ("layer1_all", "layer2", "layer3"):
        for rid in RULES:
            signs = []
            for v in out["robustness"].values():
                r = v.get(layer, {}).get(rid)
                if r and r.get("status") == "ok" and np.isfinite(r["oos"]["b"]):
                    signs.append(r["oos"]["b"] > 0)
            share.setdefault(rid, {})[layer] = (float(np.mean(signs)) if signs else None, len(signs))
    return share


def _json(x):
    if isinstance(x, (np.floating, np.integer)):
        return x.item()
    if isinstance(x, np.bool_):
        return bool(x)
    if isinstance(x, (pd.Period, pd.Timestamp)):
        return str(x)
    return str(x)


def print_summary(out: dict) -> None:
    def cell(v):
        if not v or v.get("status") != "ok":
            return "   no data          "
        o = v["oos"]
        flags = "".join(c if v[f"P{i}"] else "." for i, c in zip(range(1, 5), "1234"))
        return f"{o['b']:+.3f} t{o['t']:+5.2f} {flags}{' PASS' if v['pass'] else '     '}"
    print(f"{'rule':5s} {'L1 fundamentals (all)':26s} {'L1 HY issuers':26s} {'L2 HY bonds':26s} {'L3 stocks':26s}")
    for rid in RULES:
        print(f"{rid:5s} {cell(out['layer1']['all'].get(rid)):26s} {cell(out['layer1']['hy'].get(rid)):26s} "
              f"{cell(out['layer2'].get(rid)):26s} {cell(out['layer3'].get(rid)):26s}")


if __name__ == "__main__":
    main()
