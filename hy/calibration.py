"""Size calibration: map a predicted return to the return that history supports (methodology 7.5 "Size
calibration", Section 11; spec S14b; decision page docs/decisions/2026-10-23-size-calibration.md).

The analyst ranks bonds well, but its predicted sizes are wrong: the Mincer-Zarnowitz (MZ) slope of realised on
predicted return is near 0, not 1. This module fits, point in time, the map from a raw prediction x to the
calibrated prediction m(x), and evaluates each candidate map out of sample.

Conventions:
1. A row is one (formation date, prediction x, realised y) pair over a horizon of h months. x and y are decimal
   returns over the h months, after cost.
2. The outcome of a row is finished at the end of month date + h. It becomes usable at the decision time of that
   month end (`hy.backtest.decision_time`, + 1 day). This is the row's `available_at`. A bond that stopped trading
   before date + h still waits the full h months, so a row truncated by the end of the data is never used.
3. A fit at decision time T uses only rows with available_at <= T (`known_by`). `assert_finished` raises
   `LookAheadError` on any other row.

Candidate maps (each is one function below):
1. linear: pooled MZ (a, b) with Driscoll-Kraay HAC errors, slope shrunk toward 0 (`shrink_slope`).
2. bucket: one linear fit per spread band, slopes partially pooled toward the pooled fit (`partial_pool`).
3. isotonic: mean realised by decile of x, forced monotone (`pava`).
The choice among them is made out of sample (`choose_method`), not on in-sample fit.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from hy.data.pit import LookAheadError

Z_SIGNIFICANT = 2.0          # spec S14b: the slope must be above 0 by 2 standard errors
MIN_MONTHS = 24              # fewest finished formation months before any slope is used
SPREAD_BANDS = (0.0, 0.04, 0.07, 0.10)   # bucket edges on the formation spread (decimal): <400, 400-700, 700-1000 bp
N_BINS = 10                  # isotonic bins (deciles of x)
METHODS = ("linear", "bucket", "isotonic")
COMPARATORS = ("unshrunk",)  # scored out of sample, never chosen: the test of the shrinkage rule
FILE_NAME = "size_calibration.json"


# ---------------------------------------------------------------- rows and the point-in-time rule


def outcome_available_at(date, h_months: int) -> pd.Series:
    """available_at of an h-month outcome formed at month end `date` (methodology 7.5 size calibration, rule 2).

    available_at = (date + h month ends) + 1 day. Intuition: a return is known only once its horizon has ended.
    """
    end = pd.to_datetime(pd.Series(date)) + pd.offsets.MonthEnd(int(h_months))
    return end + pd.Timedelta(1, unit="D")


def calibration_rows(df: pd.DataFrame, pred: str, real: str, h_months: int, spread: str | None = "g_spread",
                     date_col: str = "date") -> pd.DataFrame:
    """Rows (date, x, y, available_at, bucket) for the calibration (methodology 7.5 size calibration, rule 1).

    bucket = the spread band of the bond at formation (`SPREAD_BANDS`), or 0 when no spread column is given.
    Intuition: one row per bond-month pairs what the model said with what then happened.
    """
    d = pd.DataFrame({"date": pd.to_datetime(df[date_col]).to_numpy(), "x": df[pred].to_numpy(dtype=float),
                      "y": df[real].to_numpy(dtype=float)}, index=df.index)
    if spread is not None and spread in df:
        d["bucket"] = spread_band(df[spread].to_numpy(dtype=float))
    else:
        d["bucket"] = 0
    d = d.replace([np.inf, -np.inf], np.nan).dropna(subset=["x", "y"])
    d = d[d["bucket"] >= 0]
    d["available_at"] = outcome_available_at(d["date"], h_months).to_numpy()
    return d


def spread_band(s: np.ndarray, edges: Sequence[float] = SPREAD_BANDS) -> np.ndarray:
    """Band index 0..len(edges)-2 of each spread; -1 when outside the edges or missing. Intuition: tight, middle, wide."""
    s = np.asarray(s, dtype=float)
    out = np.searchsorted(np.asarray(edges[1:-1]), s, side="right")
    return np.where(np.isfinite(s) & (s >= edges[0]) & (s < edges[-1]), out, -1)


def known_by(rows: pd.DataFrame, as_of: pd.Timestamp) -> pd.DataFrame:
    """The rows whose outcome is finished at `as_of` (available_at <= as_of). Intuition: only closed trades teach."""
    return rows[rows["available_at"] <= pd.Timestamp(as_of)]


def assert_finished(rows: pd.DataFrame, as_of: pd.Timestamp) -> None:
    """Raise `LookAheadError` when any row's outcome finishes after `as_of`. Every fit calls this."""
    late = rows["available_at"] > pd.Timestamp(as_of)
    if late.any():
        raise LookAheadError(f"{int(late.sum())} calibration rows finish after {pd.Timestamp(as_of).date()}; "
                             f"first: formed {rows.loc[late, 'date'].min().date()}")


# ---------------------------------------------------------------- linear map


def date_moments(rows: pd.DataFrame, by: Sequence[str] = ("date",)) -> pd.DataFrame:
    """Per-date sums n, sx, sy, sxx, sxy, syy (methodology 7.5 size calibration, eq. MZ).

    Intuition: an OLS fit and its Driscoll-Kraay errors need only these six sums per date, so an expanding refit
    each month costs one cumulative sum, not a pass over every bond.
    """
    g = rows.assign(xx=rows["x"] ** 2, xy=rows["x"] * rows["y"], yy=rows["y"] ** 2).groupby(list(by))
    m = g.agg(n=("x", "size"), sx=("x", "sum"), sy=("y", "sum"), sxx=("xx", "sum"), sxy=("xy", "sum"),
              syy=("yy", "sum"))
    return m.sort_index()


def fit_linear(moments: pd.DataFrame, lags: int) -> dict[str, float]:
    """Pooled MZ fit y = a + b x with Driscoll-Kraay standard errors, from per-date moments (methodology 7.5, 11).

    b = (N SXY - SX SY) / (N SXX - SX^2), a = (SY - b SX) / N. Per-date score sums: sum u = sy - a n - b sx and
    sum x u = sxy - a sx - b sxx; Newey-West with `lags` = h - 1 over dates. Same estimator as
    `hy.backtest.mincer_zarnowitz`. Intuition: b says how much of each predicted bp arrived.
    """
    m = moments
    N, SX, SY, SXX, SXY = (float(m[c].sum()) for c in ("n", "sx", "sy", "sxx", "sxy"))
    T = int((m["n"] > 0).sum())
    nan = {"a": np.nan, "b": np.nan, "se_a": np.nan, "se_b": np.nan, "n": int(N), "n_months": T}
    det = N * SXX - SX ** 2
    if N < 30 or T < 2 or det <= 0:
        return nan
    b = (N * SXY - SX * SY) / det
    a = (SY - b * SX) / N
    s = np.column_stack([m["sy"] - a * m["n"] - b * m["sx"], m["sxy"] - a * m["sx"] - b * m["sxx"]])
    S = s.T @ s
    for lag in range(1, min(int(lags), T - 1) + 1):
        g = s[lag:].T @ s[:-lag]
        S += (1.0 - lag / (lags + 1.0)) * (g + g.T)
    inv = np.linalg.inv(np.array([[N, SX], [SX, SXX]]))
    se = np.sqrt(np.clip(np.diag(inv @ S @ inv), 0, None))
    return {"a": float(a), "b": float(b), "se_a": float(se[0]), "se_b": float(se[1]), "n": int(N), "n_months": T}


def shrink_slope(b: float, se_b: float, n_months: int, z: float = Z_SIGNIFICANT,
                 min_months: int = MIN_MONTHS) -> float:
    """Positive-part James-Stein shrink of the MZ slope toward 0 (spec S14b; methodology 7.5 size calibration).

    b_s = max(0, b) x max(0, 1 - (z se_b / b)^2), and b_s = 0 when n_months < min_months. At t = z the slope is 0
    (the S14b "rank only" rule); at t = 2z it keeps 75%; at t = 10 it keeps 96%.
    Intuition: a slope the data cannot tell from zero sizes nothing; a sure slope is kept almost whole.
    """
    if not (np.isfinite(b) and np.isfinite(se_b)) or n_months < min_months or b <= 0:
        return 0.0
    if se_b <= 0:
        return float(b)
    return float(b * max(0.0, 1.0 - (z * se_b / b) ** 2))


def partial_pool(b_k: np.ndarray, se_k: np.ndarray, b_pool: float) -> tuple[np.ndarray, float]:
    """Shrink bucket slopes toward the pooled slope: b_k* = w_k b_k + (1 - w_k) b_pool, w_k = tau^2 / (tau^2 + se_k^2).

    tau^2 = the DerSimonian-Laird between-bucket variance (0 when the buckets agree within their noise). Returns
    (b_k*, tau^2). Methodology 7.5 size calibration, eq. pool. Intuition: a bucket keeps its own slope only as far as
    it is both different and precisely measured.
    """
    b_k, se_k = np.asarray(b_k, float), np.asarray(se_k, float)
    ok = np.isfinite(b_k) & np.isfinite(se_k) & (se_k > 0)
    out = np.full(b_k.shape, float(b_pool))
    if ok.sum() < 2:
        return out, 0.0
    w = 1.0 / se_k[ok] ** 2
    mu = (w * b_k[ok]).sum() / w.sum()
    Q = (w * (b_k[ok] - mu) ** 2).sum()
    tau2 = max(0.0, (Q - (ok.sum() - 1)) / (w.sum() - (w ** 2).sum() / w.sum()))
    wk = tau2 / (tau2 + se_k[ok] ** 2)
    out[ok] = wk * b_k[ok] + (1.0 - wk) * b_pool
    return out, float(tau2)


# ---------------------------------------------------------------- isotonic map


def pava(y: np.ndarray, w: np.ndarray) -> np.ndarray:
    """Pool-adjacent-violators: the weighted least-squares non-decreasing fit to `y` (methodology 7.5, eq. iso).

    Intuition: where a higher bin earned less than a lower one, average the two; repeat until the steps only rise.
    """
    y, w = np.asarray(y, float).copy(), np.asarray(w, float).copy()
    vals, wts, sizes = [], [], []
    for yi, wi in zip(y, w):
        vals.append(yi), wts.append(wi), sizes.append(1)
        while len(vals) > 1 and vals[-2] > vals[-1]:
            v2, w2, s2 = vals.pop(), wts.pop(), sizes.pop()
            tw = wts[-1] + w2
            vals[-1] = (vals[-1] * wts[-1] + v2 * w2) / tw if tw > 0 else (vals[-1] + v2) / 2
            wts[-1], sizes[-1] = tw, sizes[-1] + s2
    return np.repeat(vals, sizes)


def fit_isotonic(x: np.ndarray, y: np.ndarray, n_bins: int = N_BINS) -> dict[str, list[float]]:
    """Monotone map by bin of x: edges at the pooled quantiles of x, value = PAVA of mean y per bin (eq. iso).

    Returns {"edges": inner edges, "value": calibrated return per bin, "n": rows per bin}. Intuition: the decile
    plot of Section 11, made to rise, read as a lookup table. It caps the map at the top bin's realised mean, so a
    huge raw prediction cannot buy a huge size.
    """
    x, y = np.asarray(x, float), np.asarray(y, float)
    if len(x) < 10 * n_bins:
        return {"edges": [], "value": [], "n": []}
    edges = np.unique(np.quantile(x, np.linspace(0, 1, n_bins + 1)[1:-1]))
    k = np.searchsorted(edges, x, side="right")
    n = np.bincount(k, minlength=len(edges) + 1).astype(float)
    sy = np.bincount(k, weights=y, minlength=len(edges) + 1)
    mean = np.divide(sy, n, out=np.zeros_like(sy), where=n > 0)
    return {"edges": edges.tolist(), "value": pava(mean, n).tolist(), "n": n.astype(int).tolist()}


def apply_isotonic(iso: Mapping[str, Sequence[float]], x) -> np.ndarray:
    """Look up the bin of each x and return that bin's calibrated value (NaN when the map is empty)."""
    x = np.asarray(x, float)
    if not iso.get("value"):
        return np.full(x.shape, np.nan)
    k = np.searchsorted(np.asarray(iso["edges"]), x, side="right")
    return np.asarray(iso["value"])[k]


# ---------------------------------------------------------------- the calibration record


@dataclass
class Calibration:
    """One fitted size map (spec S14b record). Serialises to JSON; `available_at` is when a process may read it.

    Units: decimal returns over `horizon_months`, after cost. `a`, `b` are the shrunk linear map; `a_raw`, `b_raw`,
    `se_a`, `se_b` the unshrunk MZ fit. `use` is "size" when the raw slope is above 0 by `Z_SIGNIFICANT` standard
    errors, else "rank only, minimum size" (S14b rule).
    """

    predictor: str
    horizon_months: int
    method: str
    fit_date: str
    available_at: str
    n_rows: int
    n_months: int
    a: float
    b: float
    a_raw: float
    b_raw: float
    se_a: float
    se_b: float
    use: str
    buckets: dict[str, Any] = field(default_factory=dict)
    isotonic: dict[str, Any] = field(default_factory=dict)
    evaluation: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _clean(asdict(self))

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> "Calibration":
        keys = cls.__dataclass_fields__.keys()
        return cls(**{k: (np.nan if d.get(k) is None and k in ("a_raw", "b_raw", "se_a", "se_b") else d[k])
                      for k in keys if k in d})

    @property
    def significant(self) -> bool:
        return self.use == "size"


def _clean(o: Any) -> Any:
    """JSON-safe copy: NaN and inf become None, numpy scalars become floats."""
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return float(o) if np.isfinite(o) else None
    if isinstance(o, np.integer):
        return int(o)
    return o


def fit_calibration(rows: pd.DataFrame, as_of: pd.Timestamp, h_months: int, predictor: str, method: str = "linear",
                    min_months: int = MIN_MONTHS, z: float = Z_SIGNIFICANT, n_bins: int = N_BINS,
                    moments: pd.DataFrame | None = None, bucket_moments: pd.DataFrame | None = None) -> Calibration:
    """Fit one size map at decision time `as_of` from the rows finished by then (methodology 7.5 size calibration).

    The linear fit is always made: it sets `use` and is the pooled target of the buckets. Raises `LookAheadError`
    if `rows` holds an unfinished row (call `known_by` first). `moments` and `bucket_moments` are optional
    precomputed `date_moments` of exactly these rows (by date; by bucket and date), for the expanding loop.
    Intuition: the map a desk could have built that day.
    """
    assert_finished(rows, as_of)
    lin = fit_linear(date_moments(rows) if moments is None else moments, lags=h_months - 1)
    b_s = shrink_slope(lin["b"], lin["se_b"], lin["n_months"], z, min_months)
    N, SX, SY = len(rows), float(rows["x"].sum()), float(rows["y"].sum())
    a_s = (SY - b_s * SX) / N if N and lin["n_months"] >= min_months else 0.0
    sig = bool(np.isfinite(lin["b"]) and np.isfinite(lin["se_b"]) and lin["se_b"] > 0
               and lin["b"] > z * lin["se_b"] and lin["n_months"] >= min_months)
    cal = Calibration(predictor=predictor, horizon_months=int(h_months), method=method,
                      fit_date=str(pd.Timestamp(as_of).date()), available_at=str(pd.Timestamp(as_of)),
                      n_rows=int(N), n_months=int(lin["n_months"]), a=float(a_s), b=float(b_s),
                      a_raw=lin["a"], b_raw=lin["b"], se_a=lin["se_a"], se_b=lin["se_b"],
                      use="size" if sig else "rank only, minimum size")
    if method == "bucket":
        cal.buckets = fit_buckets(rows, b_s, h_months, min_months, z, bucket_moments)
    elif method == "isotonic":
        cal.isotonic = fit_isotonic(rows["x"].to_numpy(), rows["y"].to_numpy(), n_bins) \
            if lin["n_months"] >= min_months else {"edges": [], "value": [], "n": []}
    return cal


def fit_buckets(rows: pd.DataFrame, b_pool: float, h_months: int, min_months: int = MIN_MONTHS,
                z: float = Z_SIGNIFICANT, bucket_moments: pd.DataFrame | None = None) -> dict[str, Any]:
    """Per spread band: raw MZ slope, then partial pooling toward the shrunk pooled slope (eq. pool), then the
    intercept that keeps each band's mean: a_k = mean y_k - b_k* mean x_k. Intuition: wide bonds may need a smaller
    slope than tight ones, but only if the data says so clearly."""
    bm = date_moments(rows, by=("bucket", "date")) if bucket_moments is None else bucket_moments
    fits = {k: fit_linear(g.droplevel(0), h_months - 1) for k, g in bm.groupby(level=0)}
    stats = rows.groupby("bucket").agg(mx=("x", "mean"), my=("y", "mean"), n=("x", "size"))
    keys = sorted(fits)
    bk = np.array([fits[k]["b"] for k in keys])
    sek = np.array([fits[k]["se_b"] for k in keys])
    pooled, tau2 = partial_pool(bk, sek, b_pool)
    out = {"edges": list(SPREAD_BANDS), "tau2": tau2, "by": {}}
    for k, bstar in zip(keys, pooled):
        bstar = max(0.0, float(bstar)) if fits[k]["n_months"] >= min_months else float(b_pool)
        st = stats.loc[k]
        out["by"][str(int(k))] = {"b_raw": fits[k]["b"], "se_b": fits[k]["se_b"], "b": bstar,
                                  "a": float(st["my"] - bstar * st["mx"]), "n": int(st["n"])}
    return out


def apply(cal: Calibration, x, bucket=None) -> np.ndarray:
    """Calibrated return m(x) for raw predictions `x` (decimal over the horizon; spec S14b).

    linear: a + b x. bucket: a_k + b_k x for the bond's spread band, the pooled line when the band is unknown.
    isotonic: the bin value. Intuition: the raw number keeps the rank; this number is what history says it is worth.
    """
    x = np.asarray(x, float)
    lin = cal.a + cal.b * x
    if cal.method == "bucket" and cal.buckets and bucket is not None:
        bk = np.broadcast_to(np.asarray(bucket), x.shape)
        out = lin.copy()
        for k, v in cal.buckets["by"].items():
            sel = bk == int(k)
            out[sel] = v["a"] + v["b"] * x[sel]
        return out
    if cal.method == "isotonic" and cal.isotonic.get("value"):
        return apply_isotonic(cal.isotonic, x)
    if cal.method == "unshrunk" and np.isfinite(cal.b_raw) and cal.n_months > 0:
        return cal.a_raw + cal.b_raw * x       # comparator only: the MZ line without shrinkage
    return lin


def size_bp_yr(cal: Calibration, alpha_net_bp_yr: float, bucket: int | None = None) -> float:
    """Spec S14b in the memo's units: bp a year in, bp a year out, through the h-month map.

    x = alpha / 1e4 x h / 12; sized = m(x) x 1e4 x 12 / h. Intuition: the map was fitted on h-month returns, so
    convert into its units and back.
    """
    if alpha_net_bp_yr is None or alpha_net_bp_yr != alpha_net_bp_yr:
        return float("nan")
    h = cal.horizon_months
    x = alpha_net_bp_yr / 1e4 * h / 12.0
    return float(apply(cal, np.array([x]), None if bucket is None else np.array([bucket]))[0] * 1e4 * 12.0 / h)


# ---------------------------------------------------------------- expanding window, out of sample


def expanding_forecasts(rows: pd.DataFrame, h_months: int, predictor: str, methods: Sequence[str] = METHODS,
                        min_months: int = MIN_MONTHS) -> tuple[pd.DataFrame, dict[str, list[Calibration]]]:
    """Out-of-sample calibrated forecasts: for each formation month T, fit each map on rows finished by
    decision_time(T) and apply it to the rows formed at T (methodology 7.5 size calibration; Section 11).

    Returns (rows with one column per method, the fits by method). Rows before the first fit with `min_months`
    finished months get NaN. Intuition: every forecast is one the desk could have made on the day.
    """
    rows = rows.sort_values("date", kind="stable").reset_index(drop=True)
    pred = {m: np.full(len(rows), np.nan) for m in methods}
    fits: dict[str, list[Calibration]] = {m: [] for m in methods}
    mom = date_moments(rows)
    bmom = date_moments(rows, by=("bucket", "date"))
    avail = rows.groupby("date")["available_at"].max()
    pos = rows.groupby("date").indices
    for T in sorted(pos):
        T = pd.Timestamp(T)
        dec = T + pd.Timedelta(1, unit="D")
        done = avail.index[avail <= dec]          # formation dates whose every outcome is finished by dec
        if len(done) < min_months:
            continue
        train = rows.iloc[: pos[done.max()].max() + 1]   # rows are sorted by date, so a prefix
        bm = bmom[bmom.index.get_level_values("date") <= done.max()]
        idx = pos[T]
        for m in methods:
            cal = fit_calibration(train, dec, h_months, predictor, m, min_months,
                                  moments=mom.loc[:done.max()], bucket_moments=bm)
            pred[m][idx] = apply(cal, rows["x"].to_numpy()[idx], rows["bucket"].to_numpy()[idx])
            fits[m].append(cal)
    return rows.assign(**pred), fits


def dm_test(e_base: pd.Series, e_alt: pd.Series, dates: pd.Series, lags: int) -> dict[str, float]:
    """Diebold-Mariano on squared errors: mean over dates of (e_base^2 - e_alt^2), Newey-West t (Section 11).

    Positive t: the alternative forecast has the smaller loss. Intuition: the per-month loss gap, tested with the
    overlap of horizons taken into account."""
    from hy.backtest import hac_mean  # noqa: PLC0415 - keep this module light for the process import

    d = pd.DataFrame({"g": e_base.to_numpy() ** 2 - e_alt.to_numpy() ** 2, "date": dates.to_numpy()}).dropna()
    return hac_mean(d.groupby("date")["g"].mean(), lags)


def demean_by_date(df: pd.DataFrame, cols: Sequence[str], date_col: str = "date") -> pd.DataFrame:
    """Subtract each date's mean from `cols` (Section 11, cross-sectional MZ). Intuition: the market-wide move of a
    month is common to every bond, so it says nothing about how much more one bond earns than another."""
    return df.assign(**{c: df[c] - df.groupby(date_col)[c].transform("mean") for c in cols})


def choose_method(oos: pd.DataFrame, h_months: int, methods: Sequence[str] = METHODS, z: float = Z_SIGNIFICANT,
                  real: str = "y") -> tuple[str, dict[str, Any]]:
    """Pick the map out of sample: start with `linear`; take a richer map only when its squared error beats linear
    by a Diebold-Mariano t above `z` (Section 11). Intuition: complexity must pay for itself in later months."""
    d = oos.dropna(subset=list(methods))
    tests = {m: dm_test(d[real] - d["linear"], d[real] - d[m], d["date"], h_months - 1) for m in methods if m != "linear"}
    best, best_t = "linear", z
    for m, t in tests.items():
        if np.isfinite(t["t"]) and t["t"] > best_t:
            best, best_t = m, t["t"]
    return best, {m: _clean(t) for m, t in tests.items()}


# ---------------------------------------------------------------- the calibration file


def default_path() -> Path:
    from hy.data.config import CONFIG  # noqa: PLC0415

    return CONFIG.path("calibration", FILE_NAME)


def save(records: Sequence[Calibration], path: Path, meta: Mapping[str, Any] | None = None) -> Path:
    """Write the records (every expanding refit, so a replay can read the one of its day) and the run notes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = {"meta": _clean(dict(meta or {})), "records": [r.to_dict() for r in records]}
    path.write_text(json.dumps(doc, indent=1, allow_nan=False))
    return path


def load(path: Path) -> list[Calibration]:
    """Read the records of a calibration file; an absent file gives []."""
    if not Path(path).exists():
        return []
    return [Calibration.from_dict(r) for r in json.loads(Path(path).read_text()).get("records", [])]


def latest_before(records: Sequence[Calibration], decision_time: pd.Timestamp, predictor: str | None = None,
                  horizon_months: int | None = None, chosen_only: bool = True) -> Calibration | None:
    """The latest record with available_at <= decision_time (point in time), for the predictor and horizon.

    `chosen_only` keeps records whose `evaluation["chosen"]` is true (the method the out-of-sample test picked).
    Intuition: a replay of 2015 must use the map that existed in 2015.
    """
    t = pd.Timestamp(decision_time)
    ok = [r for r in records if pd.Timestamp(r.available_at) <= t
          and (predictor is None or r.predictor == predictor)
          and (horizon_months is None or r.horizon_months == horizon_months)
          and (not chosen_only or r.evaluation.get("chosen", False))]
    return max(ok, key=lambda r: pd.Timestamp(r.available_at)) if ok else None
