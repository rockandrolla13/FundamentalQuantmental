"""Tests S1 to S4 of the decision page on `sloos_tightening` and `pmi`, on the HY issuer universe.

Decision page: docs/decisions/2026-10-24-review-sloos-pmi.md (tests S1-S4). Methodology 5.2 (the pooled logistic of a
large EBITDA decline on m_t and the sector) and the proposed 5.2.1 (an issuer state term). Framework F6 (the phase
vote). Earlier study and its pass rules: docs/decisions/2026-10-24-wt-relationship-tests.md, scripts/wt_tests.py.

Run:
    PYTHONPATH=. python3 scripts/s_tests.py                    # writes data/raw/backtest/s_tests.json
    HY_DATA_ROOT=/abs/path/data/raw PYTHONPATH=. python3 scripts/s_tests.py

Unit of observation: one issuer in one fiscal quarter t (gvkey, datadate). The decision time tau is the first day on
which the LTM EBITDA of t is known in Compustat point in time (`snapshot_available_at` of its first version). The
macro vector m_t is the one known at tau (month end M = tau - 1 day, with release lags).

Event (Section 5.2): D = 1 if LTM EBITDA_{t+4} < (1 - delta) LTM EBITDA_t, with LTM EBITDA_t > 0. Each LTM is the
first-release value: the sum of four consecutive quarters, each in its latest version known on the first day the
end quarter was known. delta = 0.20 is the primary. 0.10 and 0.30 are robustness runs. The page asks for the issuer's
own delta_i. That value has no history, so this is a deviation.

Universe: gvkeys with an unambiguous TRACE HY bond link in `panel_full` in month M.

Windows: hy.backtest.CYCLE_WINDOWS. For a window that starts on day a, the model trains on rows whose outcome was
known before a (first availability of LTM_{t+4} < a). It scores rows with tau inside the window. The issuer panel
starts in 2008. So the 2008 window trains on HY-like Compustat firms 1994-2007 (debt / LTM EBITDA > 4, EBITDA > 0)
from comp.fundq. That table is the current view, not point in time. The 2008 window also replaces the two hy_oas
columns with the Baa spread level and its 3-month change, because no HY index level exists before 2008 here.

Point-in-time controls: every row carries `ltm_available_at`, `outcome_available_at` and `macro_available_at`. The
function `assert_rows_pit` checks ltm and macro <= tau for every row. The window split checks outcomes < a.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from hy import state  # noqa: E402
from hy.backtest import CYCLE_WINDOWS, benchmark_spread  # noqa: E402
from hy.forward import decline_labels, fit_decline_model  # noqa: E402
from hy.macro import _vote, phase_vote  # noqa: E402

SEED = 42
DELTA_PRIMARY = 0.20
DELTAS = (0.20, 0.10, 0.30)
LEV_CAP = 20.0
CYCLICAL_SECTORS = ("10", "15", "20", "25")  # energy, materials, industrials, consumer discretionary
HL_LEVERAGE = 4.0  # HY-like cut for the 1994-2007 Compustat training rows
QUARTER_GAP_DAYS = (80, 100)  # consecutive fiscal quarters
LTM_SPAN_DAYS = (250, 300)  # first to last quarter end of a true LTM window
YEAR_SPAN_DAYS = (350, 380)  # t to t+4
MAX_FIRST_RELEASE_DAYS = 200  # a quarter first seen later than this after its end is a back-fill, not a release
SLOOS_RELEASE_LAG_M = 1  # survey dated month m (Jan, Apr, Jul, Oct) is published in month m + 1
VOTE_MEDIAN_MONTHS, VOTE_MEDIAN_MIN = 60, 6  # trailing five-year median; the panel starts 2008-01
N_BOOT = 2000
EXIT_CODES = ("02", "03")  # comp.r_inactvcd: 02 Bankruptcy, 03 Liquidation
EXIT_MONTHS = 21  # a deletion this long after t counts as an exit inside the t..t+4 horizon
ATTRITION = ("exclude", "exits")
COMPUSTAT_TRAIN = ("1994-01-01", "2008-01-01")

M_FULL = ("spread_lvl", "spread_chg3", "sloos", "pmi", "baa_chg6")  # m_t of the 5.2 base
ISSUER = ("lev",)
DATA_FILES = {
    "panel": ("backtest", "panel_full.parquet"),
    "vintages": ("trace_panel", "fundamentals_2006-06-01_2026-09-30_3163.parquet"),
    "gics": ("backtest", "gics_history.parquet"),
    "fundq": ("compustat", "fundq_nonfin.parquet"),
    "deletions": ("compustat", "company_deletions.parquet"),  # comp.company gvkey, dlrsn, dldte (current view)
    "macro": ("macro",),
}


def data_root() -> Path:
    """The vendor data root: `HY_DATA_ROOT`, else the repo's data/raw (hy.data.config.DEFAULT_ROOT)."""
    return Path(os.environ["HY_DATA_ROOT"]) if os.environ.get("HY_DATA_ROOT") else ROOT / "data" / "raw"


# ---------------------------------------------------------------------------
# Macro inputs, monthly, each value known at month end M (decision time M + 1 day)
# ---------------------------------------------------------------------------


def _month_end(s: pd.Series | pd.DatetimeIndex) -> pd.Series:
    return pd.to_datetime(s) + pd.offsets.MonthEnd(0)


def load_macro_monthly(macro_dir: Path) -> pd.DataFrame:
    """Monthly macro inputs of m_t (Section 5.2) and the F6 votes, indexed by the month end M at which each is known.

    - pmi: Philadelphia Fed current general activity (GAC), month M. The survey is released inside its own month.
    - baa: mean of daily BAA10Y in month M. baa_chg3 and baa_chg6: change over 3 and 6 months.
    - sloos, sloos_prev: the latest and the second latest DRTSCILM readings published by M. A reading dated month m
      is published in month m + SLOOS_RELEASE_LAG_M (Fed release calendar: early in the month after the survey).
    Intuition: a value enters only once a reader could have seen it.
    """
    from wt_tests import load_survey  # noqa: PLC0415 - reuse the survey parser and its date fix

    sv = load_survey(macro_dir / "bos_dif.csv")
    gac = pd.Series(sv["GAC"].to_numpy(), index=sv.index.to_timestamp(how="end").normalize())
    baa = pd.read_csv(macro_dir / "BAA10Y.csv", na_values=".")
    baa = baa.groupby(_month_end(baa.iloc[:, 0])).agg({baa.columns[1]: "mean"}).iloc[:, 0]
    sl = pd.read_csv(macro_dir / "DRTSCILM.csv", na_values=".").dropna()
    sl_pub = _month_end(pd.to_datetime(sl.iloc[:, 0]) + pd.DateOffset(months=SLOOS_RELEASE_LAG_M))
    sl_s = pd.Series(sl.iloc[:, 1].astype(float).to_numpy(), index=sl_pub.to_numpy())
    idx = pd.date_range("1986-01-31", max(gac.index.max(), baa.index.max(), sl_s.index.max()), freq="ME")
    out = pd.DataFrame(index=idx)
    out["pmi"] = gac.reindex(idx)
    out["baa"] = baa.reindex(idx)
    out["baa_chg3"] = out["baa"] - out["baa"].shift(3)
    out["baa_chg6"] = out["baa"] - out["baa"].shift(6)
    out["sloos"] = sl_s.reindex(idx).ffill()
    out["sloos_prev"] = sl_s.shift(1).reindex(idx).ffill()
    out["macro_available_at"] = idx + pd.Timedelta(1, unit="D")
    return out


def load_market_monthly(panel: pd.DataFrame) -> pd.DataFrame:
    """HY index level and distress ratio per month end from the TRACE panel (Section 3.6, hy.state).

    hy_oas: `hy.backtest.benchmark_spread`, the median G-spread of eligible core bonds (`state.hy_index_level`).
    distress: `state.distress_ratio` over all non-carried bonds. Rows enter only when available by M + 1 day.
    hy_med5y and distress_med5y: trailing 60-month medians with at least VOTE_MEDIAN_MIN months (panel starts 2008).
    """
    p = panel[~panel["carried"].astype(bool)]
    p = p[pd.to_datetime(p["available_at"]) <= pd.to_datetime(p["date"]) + pd.Timedelta(1, unit="D")]
    hy = benchmark_spread(p, as_of=pd.to_datetime(p["available_at"]).max())
    dr = p.groupby("date").apply(lambda g: state.distress_ratio(g["g_spread"], g["yield"]), include_groups=False)
    out = pd.DataFrame({"hy_oas": hy, "distress": dr}).sort_index()
    out.index = _month_end(out.index)
    out["hy_chg3"] = out["hy_oas"] - out["hy_oas"].shift(3)
    roll = dict(window=VOTE_MEDIAN_MONTHS, min_periods=VOTE_MEDIAN_MIN)
    out["hy_med5y"] = out["hy_oas"].rolling(**roll).median()
    out["distress_med5y"] = out["distress"].rolling(**roll).median()
    return out


def f6_votes(m: pd.DataFrame) -> pd.DataFrame:
    """F6 phase votes per month that history allows (framework F6; hy.macro._vote and phase_vote).

    hy_oas: above its trailing 5-year median and up over 3 months. distress_ratio: above its trailing median.
    sloos_tightening: the last two published readings positive. pmi: GAC below 0, not 50, because GAC is a
    diffusion index centred on 0 (deviation from F6). default_rate_fcst and issuance quality: not built (None).
    majority: more than half of the available votes are late. phase_late: hy.macro.phase_vote without a prior phase
    gives late_cycle or downturn.
    """
    rows = []
    for M, r in m.iterrows():
        v = {
            "hy_oas": None if not np.isfinite([r["hy_oas"], r["hy_med5y"], r["hy_chg3"]]).all() else
            _vote("hy_oas", {"level": r["hy_oas"], "median_5y": r["hy_med5y"], "change_3m": r["hy_chg3"]}),
            "distress_ratio": None if not np.isfinite([r["distress"], r["distress_med5y"]]).all() else
            _vote("distress_ratio", {"level": r["distress"], "median_5y": r["distress_med5y"]}),
            "sloos_tightening": None if not np.isfinite([r["sloos_prev"], r["sloos"]]).all() else
            _vote("sloos_tightening", [r["sloos_prev"], r["sloos"]]),
            "pmi": None if not np.isfinite(r["pmi"]) else bool(r["pmi"] < 0.0),
            "default_rate": None,
            "issuance_quality": None,
        }
        avail = [x for x in v.values() if x is not None]
        phase, _ = phase_vote(v)
        rows.append({"M": M, "vote_hy_oas": v["hy_oas"], "vote_distress_ratio": v["distress_ratio"],
                     "vote_sloos_tightening": v["sloos_tightening"], "vote_pmi": v["pmi"],
                     "vote_majority": (sum(avail) > len(avail) / 2) if avail else None,
                     "vote_phase_late": phase in ("late_cycle", "downturn") if avail else None})
    return pd.DataFrame(rows).set_index("M")


# ---------------------------------------------------------------------------
# First-release LTM EBITDA from Compustat point in time
# ---------------------------------------------------------------------------


def first_release_ltm(vintages: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """LTM EBITDA and debt per (gvkey, datadate) as first known (Section 4.2 LTM rule, strict; Section 5.2 event).

    A(d) = first `snapshot_available_at` of quarter d. LTM(d) = sum of oibdp of d and its three previous quarters,
    each in its latest version with snapshot <= A(d). The four quarter ends must be consecutive (gaps of 80 to 100
    days). Debt = debt_current + debt_long_term of the first version of d.
    Returns (frame with gvkey, datadate, ltm_ebitda, debt, ltm_available_at, ok flags) and the trap counts.
    Intuition: the LTM a reader computed on the day the quarter came out, never a later restatement.
    """
    v = vintages.copy()
    v["gvkey"] = v["gvkey"].astype(str)
    v["snap"] = pd.to_datetime(v["snapshot_available_at"])
    n_all = v[["gvkey", "datadate"]].drop_duplicates().shape[0]
    v = v[v["snap"].notna()]
    q = (v.sort_values("snap").groupby(["gvkey", "datadate"], as_index=False)
         .first()[["gvkey", "datadate", "snap", "debt_current", "debt_long_term"]])
    q = q.rename(columns={"snap": "ltm_available_at"}).sort_values(["gvkey", "datadate"]).reset_index(drop=True)
    traps = {"issuer_quarters_in_vintages": int(n_all),
             "removed_no_snapshot_version": int(n_all - len(q))}
    g = q.groupby("gvkey")["datadate"]
    for k in (1, 2, 3):
        q[f"d{k}"] = g.shift(k)
    gaps = [(q["datadate"] - q["d1"]).dt.days, (q["d1"] - q["d2"]).dt.days, (q["d2"] - q["d3"]).dt.days]
    consec = np.logical_and.reduce([gp.between(*QUARTER_GAP_DAYS) for gp in gaps])
    span = (q["datadate"] - q["d3"]).dt.days
    # leverage_as_of (hy.sources.trace_panel) accepts any four latest quarters within 400 days.
    q["loose_only"] = (~consec) & span.le(400) & q["d3"].notna()
    q["consecutive"] = consec & span.between(*LTM_SPAN_DAYS)
    vv = v[["gvkey", "datadate", "snap", "oibdp"]].sort_values("snap")
    vals = []
    for k, col in enumerate(["datadate", "d1", "d2", "d3"]):
        left = q[["gvkey", col, "ltm_available_at"]].rename(columns={col: "datadate"}).reset_index()
        left = left.dropna(subset=["datadate"]).sort_values("ltm_available_at")
        m = pd.merge_asof(left, vv, left_on="ltm_available_at", right_on="snap", by=["gvkey", "datadate"],
                          direction="backward")
        vals.append(m.set_index("index")["oibdp"].astype(float).reindex(q.index))
    q["ltm_ebitda"] = sum(vals).where(q["consecutive"])
    q["debt"] = (q["debt_current"].astype(float).fillna(0.0) + q["debt_long_term"].astype(float).fillna(0.0)).where(
        q["debt_current"].notna() | q["debt_long_term"].notna())
    late = (q["ltm_available_at"] - q["datadate"]).dt.days > MAX_FIRST_RELEASE_DAYS
    q["late_release"] = late
    yr = q["datadate"].dt.year
    brk = ~q["consecutive"] & q["d3"].notna()
    traps.update({
        "removed_missing_quarter_in_ltm_window": int(brk.sum()),
        "removed_missing_quarter_2018_2025": int((brk & yr.between(2018, 2025)).sum()),
        "removed_missing_quarter_2008_2017": int((brk & yr.between(2008, 2017)).sum()),
        "loose_400d_rule_would_accept_false_ltm": int(q["loose_only"].sum()),
        "removed_less_than_four_quarters_history": int(q["d3"].isna().sum()),
        "removed_late_first_release": int((late & q["consecutive"]).sum()),
        "removed_ytd_cash_flow": 0,  # oibdp is an income statement field, not year to date (compustat_pit.FIELDS)
    })
    keep = ["gvkey", "datadate", "ltm_available_at", "ltm_ebitda", "debt", "consecutive", "late_release"]
    return q[keep], traps


def apply_exits(q: pd.DataFrame, deletions: pd.DataFrame | None) -> pd.DataFrame:
    """Attrition rule "exits" (decision page, frozen specification, Event 5).

    A row with LTM EBITDA_t > 0 and no outcome takes D = 1 when comp.company shows dlrsn in EXIT_CODES (bankruptcy,
    liquidation) with t < dldte <= t + EXIT_MONTHS and dldte after tau. The outcome is known on dldte + 1 day.
    Intuition: an issuer that left the file through bankruptcy had its downside, even though no t+4 LTM exists.
    `exit_event` marks the rows that the rule changed. With `deletions` None, no row changes.
    """
    q = q.copy()
    q["exit_event"] = False
    if deletions is None or q.empty:
        return q
    d = deletions[deletions["dlrsn"].astype(str).isin(EXIT_CODES)][["gvkey", "dldte"]].copy()
    d["gvkey"] = d["gvkey"].astype(str)
    d["dldte"] = pd.to_datetime(d["dldte"])
    dl = q[["gvkey"]].astype(str).merge(d.drop_duplicates("gvkey"), on="gvkey", how="left")["dldte"].to_numpy()
    dl = pd.Series(pd.to_datetime(dl), index=q.index)
    dd = pd.to_datetime(q["datadate"])
    after = pd.to_datetime(q["ltm_available_at"]) if "ltm_available_at" in q else dd  # after tau, not only after t
    cond = (q["D"].isna() & (q["ltm_ebitda"] > 0) & dl.notna() & (dl > dd) & (dl > after)
            & (dl <= dd + pd.DateOffset(months=EXIT_MONTHS)))
    q.loc[cond, "D"] = 1.0
    q.loc[cond, "outcome_available_at"] = dl[cond] + pd.Timedelta(1, unit="D")
    q["exit_event"] = cond
    return q


def attach_outcome(ltm: pd.DataFrame, delta: float, deletions: pd.DataFrame | None = None) -> pd.DataFrame:
    """Join LTM_{t+4} (first release) to each LTM_t and set the 5.2 label D (hy.forward.decline_labels).

    t+4 is the fourth next quarter of the same gvkey, 350 to 380 days later. The outcome is known at its own A(d4).
    With `deletions`, the attrition rule `apply_exits` sets D = 1 for bankruptcy and liquidation exits.
    """
    q = ltm.sort_values(["gvkey", "datadate"]).reset_index(drop=True)
    g = q.groupby("gvkey")
    q["d4"] = g["datadate"].shift(-4)
    q["ltm_t4"] = g["ltm_ebitda"].shift(-4)
    q["outcome_available_at"] = g["ltm_available_at"].shift(-4)
    ok4 = (q["d4"] - q["datadate"]).dt.days.between(*YEAR_SPAN_DAYS)
    q.loc[~ok4, ["ltm_t4", "outcome_available_at"]] = np.nan
    q["D"] = np.where(q["ltm_t4"].notna() & q["ltm_ebitda"].notna(),
                      decline_labels(q["ltm_ebitda"].fillna(0), q["ltm_t4"].fillna(0), delta), np.nan)
    return apply_exits(q, deletions)


# ---------------------------------------------------------------------------
# Issuer-quarter rows
# ---------------------------------------------------------------------------


def sector_at(gics: pd.DataFrame, keys: pd.DataFrame) -> pd.Series:
    """GICS sector of each (gvkey, tau): the record with indfrom <= tau <= indthru and available_at <= tau."""
    g = gics.copy()
    g["gvkey"] = g["gvkey"].astype(str)
    m = keys[["gvkey", "tau"]].reset_index().merge(g, on="gvkey", how="left")
    ok = (m["indfrom"] <= m["tau"]) & (m["indthru"].isna() | (m["tau"] <= m["indthru"])) & (m["available_at"] <= m["tau"])
    m = m[ok].sort_values("indfrom").drop_duplicates("index", keep="last")
    return m.set_index("index")["gsector"].astype(str).reindex(keys.index).fillna("NA")


def build_issuer_rows(ltm_o: pd.DataFrame, panel: pd.DataFrame, gics: pd.DataFrame, macro: pd.DataFrame,
                      votes: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Issuer-quarter rows of the HY universe with m_t, the issuer term, the votes and D (Sections 5.2, 5.2.1, F6).

    tau = ltm_available_at; M = tau - 1 day. The issuer is in the universe if it has an unambiguous gvkey-linked bond
    in `panel_full` at month end M that was available by tau. Leverage = debt / LTM EBITDA, clipped to [0, 20].
    """
    r = ltm_o.copy()
    r["tau"] = pd.to_datetime(r["ltm_available_at"])
    r["M"] = r["tau"] - pd.Timedelta(1, unit="D")
    counts = {}
    p = panel[panel["gvkey"].notna() & ~panel["link_ambiguous"].astype(bool) & ~panel["carried"].astype(bool)]
    p = p[pd.to_datetime(p["available_at"]) <= pd.to_datetime(p["date"]) + pd.Timedelta(1, unit="D")]
    uni = p[["date", "gvkey"]].drop_duplicates().assign(in_uni=True)
    uni["M"] = _month_end(uni["date"])
    uni["gvkey"] = uni["gvkey"].astype(str)
    r = r.merge(uni[["M", "gvkey", "in_uni"]].drop_duplicates(), on=["M", "gvkey"], how="left")
    r = r[r["in_uni"].eq(True)].drop(columns="in_uni")
    counts["universe_issuer_quarters"] = int(len(r))
    counts["universe_gvkeys"] = int(r["gvkey"].nunique())
    counts["removed_missing_quarter_in_ltm_window"] = int((~r["consecutive"]).sum())
    r = r[r["consecutive"]]
    counts["removed_late_first_release"] = int(r["late_release"].sum())
    r = r[~r["late_release"]]
    counts["removed_ltm_ebitda_not_positive"] = int((r["ltm_ebitda"] <= 0).sum())
    r = r[r["ltm_ebitda"] > 0]
    counts["exit_events_counted"] = int(r["exit_event"].sum())
    counts["removed_outcome_missing"] = int(r["D"].isna().sum())
    counts["removed_outcome_missing_t4_in_2018_2025"] = int((r["D"].isna() & r["datadate"].dt.year.between(2017, 2025)).sum())
    r = r[r["D"].notna()].copy()
    r["lev"] = (r["debt"] / r["ltm_ebitda"]).clip(0.0, LEV_CAP)
    r = r.merge(macro, left_on="M", right_index=True, how="left")
    r = r.merge(votes, left_on="M", right_index=True, how="left")
    r["spread_lvl"], r["spread_chg3"] = r["hy_oas"], r["hy_chg3"]
    r["proxy_lvl"], r["proxy_chg3"] = r["baa"], r["baa_chg3"]
    r["sector"] = sector_at(gics, r).to_numpy()
    r["source"] = "issuer_pit"
    counts["rows_final"] = int(len(r))
    counts["gvkeys_final"] = int(r["gvkey"].nunique())
    counts["event_rate"] = float(r["D"].mean())
    return r.reset_index(drop=True), counts


def build_compustat_rows(fundq: pd.DataFrame, macro: pd.DataFrame, delta: float,
                         span: tuple[str, str] = COMPUSTAT_TRAIN,
                         deletions: pd.DataFrame | None = None) -> pd.DataFrame:
    """HY-like Compustat rows for the 2008 window's training set (Section 5.2), current view, not point in time.

    LTM = rolling sum of oibdpq over four consecutive calendar quarters. tau = month end of datadate + 3 months
    + 1 day (the 10-K deadline, the latest filing date), outcome known at the same lag after t+4. Keep
    debt / LTM EBITDA > HL_LEVERAGE with LTM EBITDA > 0 and the outcome known before span[1].
    """
    df = fundq.dropna(subset=["datacqtr"]).copy()
    df["q"] = pd.PeriodIndex(df["datacqtr"].str.replace("Q", "-Q"), freq="Q")
    df = df.sort_values("datadate").drop_duplicates(["gvkey", "q"], keep="last").sort_values(["gvkey", "q"])
    df["qn"] = pd.PeriodIndex(df["q"]).asi8
    g = df.groupby("gvkey")
    qn = df["qn"]
    consec = (qn - g["qn"].shift(3)) == 3
    df["ltm_ebitda"] = g["oibdpq"].transform(lambda s: s.rolling(4, min_periods=4).sum()).where(consec)
    df["debt"] = df["dlttq"].fillna(0.0) + df["dlcq"].fillna(0.0)
    g = df.groupby("gvkey")
    df["ltm_t4"] = g["ltm_ebitda"].shift(-4).where((g["qn"].shift(-4) - qn) == 4)
    df["datadate"] = pd.to_datetime(df["datadate"])
    lag = lambda d: d + pd.offsets.MonthEnd(3) + pd.Timedelta(1, unit="D")  # noqa: E731
    df["tau"] = lag(df["datadate"])
    df["outcome_available_at"] = lag(df["datadate"] + pd.DateOffset(months=12))
    df["ltm_available_at"] = df["tau"]
    df = df[df["ltm_ebitda"] > 0]
    df = df[(df["debt"] / df["ltm_ebitda"]) > HL_LEVERAGE].copy()
    df["D"] = np.where(df["ltm_t4"].notna(),
                       decline_labels(df["ltm_ebitda"], df["ltm_t4"].fillna(0), delta), np.nan).astype(float)
    df = apply_exits(df, deletions)
    df = df[df["D"].notna()]
    df = df[(df["tau"] >= pd.Timestamp(span[0])) & (df["outcome_available_at"] < pd.Timestamp(span[1]))].copy()
    df["lev"] = (df["debt"] / df["ltm_ebitda"]).clip(0.0, LEV_CAP)
    df["M"] = df["tau"] - pd.Timedelta(1, unit="D")
    df = df.merge(macro, left_on="M", right_index=True, how="left")
    df["proxy_lvl"], df["proxy_chg3"] = df["baa"], df["baa_chg3"]
    df["spread_lvl"], df["spread_chg3"] = np.nan, np.nan
    df["sector"] = df["gsector"].astype(str)
    df["source"] = "compustat_current"
    df["gvkey"] = df["gvkey"].astype(str)
    return df.reset_index(drop=True)


def assert_rows_pit(rows: pd.DataFrame) -> None:
    """Fail if any row uses a value not known at its decision time tau (CLAUDE.md: available_at before decision)."""
    for col in ("ltm_available_at", "macro_available_at"):
        late = pd.to_datetime(rows[col]) > pd.to_datetime(rows["tau"])
        if late.any():
            raise AssertionError(f"{int(late.sum())} rows use {col} after tau")
    if (pd.to_datetime(rows["outcome_available_at"]) <= pd.to_datetime(rows["tau"])).any():
        raise AssertionError("an outcome is known at or before its own decision time")


# ---------------------------------------------------------------------------
# Window split, fit, score
# ---------------------------------------------------------------------------


def window_split(rows: pd.DataFrame, start: str, end: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Train: rows whose outcome was known before the window starts. Test: rows with tau inside the window.

    Intuition: at the window start an analyst can fit only on events that had already played out.
    """
    a, b = pd.Timestamp(start), pd.Timestamp(end) + pd.Timedelta(1, unit="D")
    train = rows[pd.to_datetime(rows["outcome_available_at"]) < a]
    test = rows[(rows["tau"] >= a) & (rows["tau"] < b)]
    return train, test


def design(rows: pd.DataFrame, cols: Sequence[str], proxy: bool) -> np.ndarray:
    """Columns of the logistic. `pmi_cyc` = pmi x 1{cyclical sector}. With `proxy`, the spread columns take Baa."""
    out = []
    if not cols:
        return np.zeros((len(rows), 0))
    for c in cols:
        if c == "pmi_cyc":
            out.append(rows["pmi"].to_numpy(float) * rows["sector"].isin(CYCLICAL_SECTORS).to_numpy(float))
        elif proxy and c in ("spread_lvl", "spread_chg3"):
            out.append(rows[c.replace("spread", "proxy")].to_numpy(float))
        else:
            out.append(rows[c].to_numpy(float))
    return np.column_stack(out)


def fit_predict(train: pd.DataFrame, test: pd.DataFrame, cols: Sequence[str], proxy: bool) -> np.ndarray:
    """Fit the 5.2 logistic (hy.forward.fit_decline_model) on train and return p for each test row.

    Each column is standardised with the train mean and sd, so a level enters as a z against the history known at
    fit time. The sector effect of a sector the train set never saw is 0 (the reference).
    """
    Xtr, Xte = design(train, cols, proxy), design(test, cols, proxy)
    mu, sd = Xtr.mean(0), Xtr.std(0)
    sd[sd == 0] = 1.0
    model = fit_decline_model((Xtr - mu) / sd, train["sector"].tolist(), train["D"].to_numpy(int))
    z = model.theta0 + ((Xte - mu) / sd) @ model.theta + test["sector"].map(model.theta_sector).fillna(0.0).to_numpy()
    return 1.0 / (1.0 + np.exp(-z))


def log_loss_rows(y: np.ndarray, p: np.ndarray) -> np.ndarray:
    """Per-row log loss -[y log p + (1 - y) log(1 - p)], p clipped to [1e-6, 1 - 1e-6]. Lower is better."""
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def block_bootstrap_mean(x: np.ndarray, blocks: np.ndarray, n_boot: int = N_BOOT, seed: int = SEED) -> dict:
    """Mean of x with a 90% and 95% interval from resampling whole blocks (quarters of tau) with replacement.

    Intuition: issuers in one quarter share the macro shock, so the quarter, not the issuer, is the independent unit.
    """
    s = pd.DataFrame({"x": x, "b": blocks}).groupby("b")["x"].agg(["sum", "count"])
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(s), size=(n_boot, len(s)))
    bs = s["sum"].to_numpy()[idx].sum(1) / s["count"].to_numpy()[idx].sum(1)
    return {"mean": float(np.mean(x)), "ci90": [float(np.percentile(bs, 5)), float(np.percentile(bs, 95))],
            "ci95": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))], "n_blocks": int(len(s))}


def block_bootstrap_share_diff(y: np.ndarray, flag: np.ndarray, blocks: np.ndarray, n_boot: int = N_BOOT,
                               seed: int = SEED) -> dict:
    """Share of y = 1 where flag is on minus where it is off, with a 95% quarter-block bootstrap interval."""
    d = pd.DataFrame({"y": y, "f": flag.astype(bool), "b": blocks})
    on = d[d["f"]].groupby("b")["y"].agg(["sum", "count"])
    off = d[~d["f"]].groupby("b")["y"].agg(["sum", "count"])
    s = pd.concat([on.add_prefix("on_"), off.add_prefix("off_")], axis=1).fillna(0.0)
    on_n, off_n = s["on_count"].sum(), s["off_count"].sum()
    out = {"share_on": float(s["on_sum"].sum() / on_n) if on_n else None,
           "share_off": float(s["off_sum"].sum() / off_n) if off_n else None,
           "n_on": int(on_n), "n_off": int(off_n), "n_blocks": int(len(s))}
    if not on_n or not off_n:
        out.update({"diff": None, "ci95": None})
        return out
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(s), size=(n_boot, len(s)))
    a = s.to_numpy()
    cols = {c: i for i, c in enumerate(s.columns)}
    with np.errstate(invalid="ignore", divide="ignore"):
        bs = (a[idx, cols["on_sum"]].sum(1) / a[idx, cols["on_count"]].sum(1)
              - a[idx, cols["off_sum"]].sum(1) / a[idx, cols["off_count"]].sum(1))
    out.update({"diff": out["share_on"] - out["share_off"],
                "ci95": [float(np.nanpercentile(bs, 2.5)), float(np.nanpercentile(bs, 97.5))]})
    return out


def ewc_test(x: Sequence[float]) -> dict:
    """One-sided test of mean(x) > 0 with the EWC long-run variance (Lazarus, Lewis, Stock, Watson 2018, JBES 36(4)).

    Lambda_j = sqrt(2/T) sum_t cos(pi j (t - 1/2) / T) u_t, u = x - mean(x); Omega = (1/nu) sum_{j=1..nu} Lambda_j^2;
    nu = max(1, floor(0.4 T^(2/3))); t = mean / sqrt(Omega / T) against Student t with nu degrees of freedom.
    The cosines with j >= 1 sum to zero over t, so the demeaning does not change Lambda_j.
    Intuition: a few low-frequency cosine projections estimate the long-run variance of a short, serially
    correlated series, and t_nu critical values keep the size honest when nu is small.
    """
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    T = len(x)
    if T < 3:
        return {"T": T, "nu": None, "mean": float(x.mean()) if T else None, "t": None, "p_one_sided": None}
    nu = max(1, int(np.floor(0.4 * T ** (2.0 / 3.0))))
    u = x - x.mean()
    tt = np.arange(1, T + 1)
    lam = np.array([np.sqrt(2.0 / T) * np.sum(np.cos(np.pi * j * (tt - 0.5) / T) * u) for j in range(1, nu + 1)])
    omega = float(np.mean(lam ** 2))
    tstat = float(x.mean() / np.sqrt(omega / T)) if omega > 0 else float("nan")
    return {"T": T, "nu": nu, "mean": float(x.mean()), "t": tstat,
            "p_one_sided": float(1 - student_t.cdf(tstat, nu)) if np.isfinite(tstat) else None}


def im_test(values: Sequence[float | None]) -> dict:
    """Ibragimov-Mueller (2010) test across q per-window estimates: t = mean / (sd / sqrt(q)), Student t with q - 1
    degrees of freedom, one-sided (mean > 0). Intuition: each window is one independent draw of the effect."""
    v = np.array([x for x in values if x is not None and np.isfinite(x)], dtype=float)
    q = len(v)
    if q < 2 or v.std(ddof=1) == 0:
        return {"q": q, "t": None, "df": q - 1 if q else None, "p_one_sided": None}
    tstat = float(v.mean() / (v.std(ddof=1) / np.sqrt(q)))
    return {"q": q, "t": tstat, "df": q - 1, "p_one_sided": float(1 - student_t.cdf(tstat, q - 1))}


def quarterly_means(x: np.ndarray, blocks: np.ndarray) -> pd.Series:
    """Mean of x across issuers within each quarter, in time order (the series that the EWC test reads)."""
    return pd.Series(x).groupby(np.asarray(blocks)).mean().sort_index()


def quarter_blocks(test: pd.DataFrame) -> np.ndarray:
    return pd.PeriodIndex(test["tau"] - pd.Timedelta(1, unit="D"), freq="Q").astype(str).to_numpy()


# ---------------------------------------------------------------------------
# Tests S1 to S4
# ---------------------------------------------------------------------------


def compare_models(train: pd.DataFrame, test: pd.DataFrame, cols_a: Sequence[str], cols_b: Sequence[str],
                   proxy: bool, keep: list | None = None) -> dict:
    """Out-of-sample gain of model b over model a: mean(logloss_a - logloss_b), Brier likewise. Positive = b better.

    Also the in-sample log-loss gain on the train rows, to flag a case where out of sample beats in sample.
    With `keep`, append (row gains, quarter blocks) for a pooled interval across windows.
    """
    y = test["D"].to_numpy(float)
    pa, pb = fit_predict(train, test, cols_a, proxy), fit_predict(train, test, cols_b, proxy)
    ll = log_loss_rows(y, pa) - log_loss_rows(y, pb)
    br = (pa - y) ** 2 - (pb - y) ** 2
    blocks = quarter_blocks(test)
    ytr = train["D"].to_numpy(float)
    is_gain = float((log_loss_rows(ytr, fit_predict(train, train, cols_a, proxy))
                     - log_loss_rows(ytr, fit_predict(train, train, cols_b, proxy))).mean())
    if keep is not None:
        keep.append((ll, blocks))
    oos = float(ll.mean())
    return {"logloss_gain": block_bootstrap_mean(ll, blocks), "brier_gain": block_bootstrap_mean(br, blocks),
            "logloss_gain_quarterly_ewc": ewc_test(quarterly_means(ll, blocks).to_numpy()),
            "logloss_a": float(log_loss_rows(y, pa).mean()), "logloss_b": float(log_loss_rows(y, pb).mean()),
            "in_sample_logloss_gain": is_gain, "flag_oos_above_is": bool(oos > 0 and oos > is_gain)}


def pooled_gain(keep: list) -> dict:
    """Gain over the test rows of all windows together, with a quarter-block interval."""
    if not keep:
        return {}
    x, b = np.concatenate([k[0] for k in keep]), np.concatenate([k[1] for k in keep])
    return block_bootstrap_mean(x, b) | {"quarterly_ewc": ewc_test(quarterly_means(x, b).to_numpy())}


def window_data(issuer: pd.DataFrame, compustat: pd.DataFrame, w: int) -> tuple[pd.DataFrame, pd.DataFrame, bool]:
    """Train and test frames of window w. 2008 trains on the Compustat rows and uses the Baa proxy columns."""
    a, b = CYCLE_WINDOWS[w]
    if w == 2008:
        tr, _ = window_split(compustat, a, b)
        _, te = window_split(issuer, a, b)
        return tr, te, True
    tr, te = window_split(issuer, a, b)
    return tr, te, False


def _clean(df: pd.DataFrame, cols: Sequence[str], proxy: bool) -> pd.DataFrame:
    need = [c.replace("spread", "proxy") if proxy and c.startswith("spread") else c for c in cols if c != "pmi_cyc"]
    return df.dropna(subset=list(dict.fromkeys(need + ["pmi", "sector", "D"])))


def run_s1_s2(issuer: pd.DataFrame, compustat: pd.DataFrame, windows: Sequence[int]) -> dict:
    """S1 (drop sloos) and S2 (pmi level, pmi x cyclical) per window, for the macro base and the macro + issuer base.

    S1 gain = logloss(m_t without sloos) - logloss(m_t). Positive: sloos earns its place.
    S2 base = m_t without pmi. Gain of form L (m_t, with pmi level) and form I (pmi level + pmi x cyclical).
    """
    out = {}
    m_nopmi = tuple(c for c in M_FULL if c != "pmi")
    m_nosloos = tuple(c for c in M_FULL if c != "sloos")
    for base_name, extra in (("macro", ()), ("macro_lev", ISSUER)):
        res = {}
        keep = {k: [] for k in ("S1_sloos", "S2_pmi_level", "S2_pmi_cyclical", "context_mt_vs_sector")}
        for w in windows:
            tr, te, proxy = window_data(issuer, compustat, w)
            allc = M_FULL + extra + ("pmi_cyc",)
            tr, te = _clean(tr, allc, proxy), _clean(te, allc, proxy)
            if len(tr) < 30 or len(te) < 30 or tr["D"].nunique() < 2:
                res[w] = {"skipped": f"n_train {len(tr)}, n_test {len(te)}"}
                continue
            res[w] = {
                "n_train": int(len(tr)), "n_test": int(len(te)), "event_rate_train": float(tr["D"].mean()),
                "event_rate_test": float(te["D"].mean()), "train_source": tr["source"].iloc[0], "spread_proxy": proxy,
                "n_test_quarters": int(len(set(quarter_blocks(te)))),
                "S1_sloos": compare_models(tr, te, m_nosloos + extra, M_FULL + extra, proxy, keep["S1_sloos"]),
                "S2_pmi_level": compare_models(tr, te, m_nopmi + extra, M_FULL + extra, proxy, keep["S2_pmi_level"]),
                "S2_pmi_cyclical": compare_models(tr, te, m_nopmi + extra, M_FULL + extra + ("pmi_cyc",), proxy,
                                                  keep["S2_pmi_cyclical"]),
                "context_mt_vs_sector": compare_models(tr, te, extra, M_FULL + extra, proxy,
                                                       keep["context_mt_vs_sector"]),
            }
        res["pooled"] = {k: pooled_gain(v) for k, v in keep.items()}
        res["pooled_without_2008"] = {
            k: pooled_gain([x for x, w in zip(v, [w for w in windows if "skipped" not in res[w]]) if w != 2008])
            for k, v in keep.items()}
        out[base_name] = res
    return out


VOTES = ("vote_hy_oas", "vote_distress_ratio", "vote_sloos_tightening", "vote_pmi", "vote_majority", "vote_phase_late")


def run_s3(issuer: pd.DataFrame, windows: Sequence[int]) -> dict:
    """S3: per vote and window, share of D = 1 among issuer-quarters with the late flag on at tau minus off.

    Also the pooled difference over all rows. A window where the flag never changes gives no comparison (None).
    """
    out = {}
    for v in VOTES:
        res = {}
        for w in windows:
            a, b = CYCLE_WINDOWS[w]
            _, te = window_split(issuer, a, b)
            te = te[te[v].notna()]
            res[w] = block_bootstrap_share_diff(te["D"].to_numpy(float), te[v].astype(bool).to_numpy(),
                                                quarter_blocks(te)) if len(te) else {"diff": None, "n_on": 0, "n_off": 0}
        d = issuer[issuer[v].notna()]
        res["pooled_all"] = block_bootstrap_share_diff(d["D"].to_numpy(float), d[v].astype(bool).to_numpy(),
                                                       quarter_blocks(d))
        out[v] = res
    return out


def drop_2020(rows: pd.DataFrame, mode: str) -> pd.DataFrame:
    """S4 exclusions. 'quarter': drop rows whose fiscal quarter t ends in 2020. 'span': drop rows whose t..t+4
    span touches any 2020 quarter (t ends between 2019-03-31 and 2020-12-31)."""
    d = pd.to_datetime(rows["datadate"])
    if mode == "quarter":
        return rows[d.dt.year != 2020]
    if mode == "span":
        return rows[(d < pd.Timestamp("2019-03-01")) | (d > pd.Timestamp("2020-12-31"))]
    raise ValueError(mode)


def count_pass(res: dict, key: str | None, windows: Sequence[int], stat: str = "logloss_gain") -> int:
    """Number of windows where the gain (or the share difference) is positive."""
    n = 0
    for w in windows:
        r = res.get(w, {})
        if key is None:
            v = r.get("diff")
        else:
            v = r.get(key, {}).get(stat, {}).get("mean") if key in r else None
        n += int(v is not None and v > 0)
    return n


def window_values(res: dict, key: str | None, windows: Sequence[int]) -> list:
    """Per-window estimate: the row mean log-loss gain of `key`, or the S3 share difference when key is None."""
    out = []
    for w in windows:
        r = res.get(w, {})
        out.append(r.get("diff") if key is None else (r[key]["logloss_gain"]["mean"] if key in r else None))
    return out


def verdicts(s12: dict, s3: dict, windows: Sequence[int], need: int) -> dict:
    """Pass flags of the decision page rules on the given windows: positive gain in at least `need` windows.

    Beside each count, the Ibragimov-Mueller t-test across the per-window values (`im_test`).
    """
    v = {}
    for base, res in s12.items():
        n1 = count_pass(res, "S1_sloos", windows)
        nl, ni = count_pass(res, "S2_pmi_level", windows), count_pass(res, "S2_pmi_cyclical", windows)
        v[base] = {"S1_windows_positive": n1, "S1_pass": n1 >= need,
                   "S1_im": im_test(window_values(res, "S1_sloos", windows)),
                   "S2_level_windows_positive": nl, "S2_cyclical_windows_positive": ni, "S2_pass": max(nl, ni) >= need,
                   "S2_level_im": im_test(window_values(res, "S2_pmi_level", windows)),
                   "S2_cyclical_im": im_test(window_values(res, "S2_pmi_cyclical", windows))}
    v["S3"] = {k: {"windows_positive": count_pass(r, None, windows), "pass": count_pass(r, None, windows) >= need,
                   "im": im_test(window_values(r, None, windows))} for k, r in s3.items()}
    v["fair_coin_pass_probability"] = float(sum(
        __import__("math").comb(len(windows), k) for k in range(need, len(windows) + 1)) / 2 ** len(windows))
    return v


def run_all(issuer: pd.DataFrame, compustat: pd.DataFrame, s4: bool) -> dict:
    """S1, S2, S3 on all four windows and on the three windows without 2008. With `s4`, also S4."""
    W = tuple(CYCLE_WINDOWS)
    s12, s3 = run_s1_s2(issuer, compustat, W), run_s3(issuer, W)
    out = {"S1_S2": s12, "S3": s3, "verdict_4_windows": verdicts(s12, s3, W, 3),
           "verdict_without_2008": verdicts(s12, s3, tuple(w for w in W if w != 2008), 2)}
    if s4:
        W3 = tuple(w for w in W if w != 2020)
        out["S4"] = {}
        for mode in ("quarter", "span"):
            iss = drop_2020(issuer, mode)
            a = run_s1_s2(iss, compustat, W3)
            for base in a:
                for w in a[base]:
                    for k in ("S2_pmi_level", "S2_pmi_cyclical"):
                        a[base][w].pop(k, None)
            b = run_s3(iss, W3)
            out["S4"][mode] = {"S1": a, "S3": b, "n_rows": int(len(iss)),
                               "verdict_2_of_3": verdicts(a, b, W3, 2), "verdict_3_of_3": verdicts(a, b, W3, 3)}
    return out


def _jsonable(x):
    if isinstance(x, dict):
        return {str(k): _jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jsonable(v) for v in x]
    if isinstance(x, (np.floating, float)):
        return None if not np.isfinite(x) else float(x)
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.bool_,)):
        return bool(x)
    return x


def main(argv: Sequence[str] | None = None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    root = data_root()
    path = lambda k: root.joinpath(*DATA_FILES[k])  # noqa: E731
    panel = pd.read_parquet(path("panel"), columns=["date", "gvkey", "g_spread", "price", "yield", "years", "mod_dur",
                                                     "available_at", "carried", "link_ambiguous", "cusip"])
    macro = load_macro_monthly(path("macro"))
    market = load_market_monthly(panel)
    mm = macro.join(market, how="left")
    votes = f6_votes(mm.loc["2008-01-31":])
    ltm, traps = first_release_ltm(pd.read_parquet(path("vintages")))
    gics = pd.read_parquet(path("gics"))
    fundq = pd.read_parquet(path("fundq"))
    macro_cols = mm[["pmi", "baa", "baa_chg3", "baa_chg6", "sloos", "sloos_prev", "hy_oas", "hy_chg3",
                     "macro_available_at"]]
    result = {"meta": {
        "decision_page": "docs/decisions/2026-10-24-review-sloos-pmi.md", "seed": SEED, "n_boot": N_BOOT,
        "windows": {str(k): v for k, v in CYCLE_WINDOWS.items()}, "cyclical_sectors": list(CYCLICAL_SECTORS),
        "traps_vintage_level": traps, "deltas": list(DELTAS), "primary_delta": DELTA_PRIMARY,
        "sign_convention": "gain = logloss(smaller or without) - logloss(with); positive means the term helps",
        "attrition_variants": list(ATTRITION), "exit_codes": list(EXIT_CODES), "exit_months": EXIT_MONTHS,
    }, "by_delta": {}}
    deletions = pd.read_parquet(path("deletions"))
    for delta in DELTAS:
        result["by_delta"][f"{delta:.2f}"] = {}
        for variant in ATTRITION:
            dl = deletions if variant == "exits" else None
            lo = attach_outcome(ltm, delta, dl)
            issuer, counts = build_issuer_rows(lo, panel, gics, macro_cols, votes)
            comp = build_compustat_rows(fundq, macro_cols, delta, deletions=dl)
            assert_rows_pit(issuer)
            assert_rows_pit(comp)
            res = run_all(issuer, comp, s4=(delta == DELTA_PRIMARY))
            res["counts"] = counts | {"compustat_train_rows_1994_2007": int(len(comp)),
                                      "compustat_event_rate": float(comp["D"].mean()),
                                      "compustat_exit_events_counted": int(comp["exit_event"].sum())}
            res["counts"]["by_window_tau"] = {
                str(w): int(window_split(issuer, *CYCLE_WINDOWS[w])[1].shape[0]) for w in CYCLE_WINDOWS}
            res["counts"]["exit_events_by_window_tau"] = {
                str(w): int(window_split(issuer, *CYCLE_WINDOWS[w])[1]["exit_event"].sum()) for w in CYCLE_WINDOWS}
            res["vote_on_share_by_window"] = {
                v: {str(w): float(window_split(issuer, *CYCLE_WINDOWS[w])[1][v].dropna().astype(float).mean())
                    for w in CYCLE_WINDOWS} for v in VOTES}
            result["by_delta"][f"{delta:.2f}"][variant] = res
            print(f"delta {delta} {variant}: rows {counts['rows_final']}, exits {counts['exit_events_counted']}, "
                  f"event rate {counts['event_rate']:.3f}", flush=True)
    out = Path(args.out) if args.out else root / "backtest" / "s_tests.json"
    out.write_text(json.dumps(_jsonable(result), indent=1, default=str))
    print(f"wrote {out}")
    return result


if __name__ == "__main__":
    main()
