"""Forecast registry: every external forecast with its vintage and release time (methodology Section 5.4).

One row per source, variable, horizon, and vintage. The registry is the only door through which a forecast
enters a scenario: path probabilities (hy.macro), driver shifts (hy.forward), and event outcome weights
(hy.events) all read it through `as_of(t)`, which returns only rows with `available_at <= t`.

Fields
- `source`: issuer of the forecast, e.g. "spf", "fomc_sep", "ust_forward", "sloos", "analyst", "consensus".
- `variable`: a name in `VARIABLES` (macro) or "<issuer>:<driver>" (issuer forecasts).
- `horizon_q`: quarters ahead of the vintage quarter (0 = the vintage quarter itself).
- `vintage`: the date the forecast was made; `available_at`: the first moment the market could read it.
- `point`, `q10`, `q50`, `q90`: the forecast and its quantiles, in decimals (rates, growth) or levels (PMI).
- `method`: how the quantiles were obtained ("survey_bins", "dot_range", "market_implied", "stub", ...).

Forecast error accounting stores realised values against every row whose horizon has matured, and reports
bias, absolute error, and quantile coverage by source and horizon. The coverage feeds `widen_factor`, which
hy.macro uses to scale the quantile spread before it computes path probabilities.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime

import numpy as np
import pandas as pd

from hy.inputs import LookAheadError

VARIABLES = (
    "gdp_growth",      # real GDP growth, annualised quarter on quarter
    "cpi",             # CPI inflation, year on year
    "unemployment",    # unemployment rate
    "policy_rate",     # policy rate, quarter average (fed funds midpoint)
    "y2", "y10",       # Treasury yields (par)
    "pmi",             # manufacturing PMI, level
    "hy_spread",       # high yield index spread
    "distress_ratio",  # share of the HY index above 1,000 bp
    "default_rate",    # speculative-grade default rate, trailing 12 months
    "sloos_tightening",  # net share of banks tightening C&I standards
)

COLUMNS = ("source", "variable", "horizon_q", "vintage", "available_at", "point", "q10", "q50", "q90", "method")

# Fallback order when a source is missing (framework F6, forecast linkage rule).
FALLBACK_ORDER = ("market_implied", "f6_table", "logged_assumption")


@dataclass(frozen=True)
class ForecastRow:
    """One forecast of one variable at one horizon from one vintage (Section 5.4)."""

    source: str
    variable: str
    horizon_q: int
    vintage: datetime
    available_at: datetime
    point: float
    q10: float = float("nan")
    q50: float = float("nan")
    q90: float = float("nan")
    method: str = ""

    def __post_init__(self) -> None:
        if self.available_at < self.vintage:
            raise ValueError(f"{self.source}/{self.variable}: available_at precedes vintage")
        q = [x for x in (self.q10, self.q50, self.q90) if x == x]
        if q != sorted(q):
            raise ValueError(f"{self.source}/{self.variable}/h{self.horizon_q}: quantiles not ordered")


class ForecastRegistry:
    """All forecast rows, every vintage. Read through `as_of` only."""

    def __init__(self, rows: Iterable[ForecastRow] = ()) -> None:
        self._rows: list[ForecastRow] = list(rows)
        self._realised: dict[tuple[str, datetime], float] = {}
        self.strict_reads: list[datetime] = []  # decision times served, for audit

    def add(self, rows: ForecastRow | Iterable[ForecastRow]) -> None:
        if isinstance(rows, ForecastRow):
            rows = [rows]
        self._rows.extend(rows)

    def frame(self) -> pd.DataFrame:
        """Every row, every vintage, for audit and error accounting. Not for decisions."""
        return pd.DataFrame([asdict(r) for r in self._rows], columns=COLUMNS)

    def as_of(self, decision_time: datetime, latest_only: bool = True) -> pd.DataFrame:
        """Rows readable at `decision_time`: `available_at <= decision_time` (framework R5).

        With `latest_only`, keep the newest vintage per (source, variable, horizon). The returned frame carries
        `decision_time` so that downstream code can assert it never reads past it.
        Intuition: a forecast published tomorrow cannot move a weight today.
        """
        self.strict_reads.append(decision_time)
        df = self.frame()
        if df.empty:
            return df.assign(decision_time=decision_time)
        df = df[df["available_at"] <= decision_time]
        if latest_only and len(df):
            df = df.sort_values(["vintage", "available_at"]).groupby(["source", "variable", "horizon_q"]).tail(1)
        out = df.reset_index(drop=True)
        assert_no_lookahead(out, decision_time)
        return out.assign(decision_time=decision_time)

    def get(self, decision_time: datetime, variable: str, source: str | None = None,
            sources_in_order: Sequence[str] = ()) -> pd.DataFrame:
        """One variable's term structure (one row per horizon) from the first available source in order.

        Returns an empty frame when no source has it; the caller then applies `FALLBACK_ORDER`.
        """
        df = self.as_of(decision_time)
        df = df[df["variable"] == variable]
        order = [source] if source else list(sources_in_order) or sorted(df["source"].unique())
        for s in order:
            hit = df[df["source"] == s]
            if len(hit):
                return hit.sort_values("horizon_q").reset_index(drop=True)
        return df.iloc[0:0]

    # -- realised values and error accounting -------------------------------------------------------

    def record_realised(self, variable: str, period_end: datetime, value: float) -> None:
        """Store the realised value of `variable` for the quarter ending `period_end`."""
        self._realised[(variable, pd.Timestamp(period_end).to_period("Q").to_timestamp(how="end").normalize())] = value

    def errors(self) -> pd.DataFrame:
        """Forecast minus realised for every row whose target quarter has a realised value.

        Target quarter = vintage quarter + `horizon_q`. Adds `inside_80`: realised inside [q10, q90].
        """
        df = self.frame()
        if df.empty or not self._realised:
            return pd.DataFrame(columns=[*COLUMNS, "target", "realised", "error", "abs_error", "inside_80"])
        tgt = [(pd.Timestamp(v).to_period("Q") + int(h)).to_timestamp(how="end").normalize()
               for v, h in zip(df["vintage"], df["horizon_q"])]
        df = df.assign(target=tgt)
        df["realised"] = [self._realised.get((var, t), np.nan) for var, t in zip(df["variable"], df["target"])]
        df = df[df["realised"].notna()].copy()
        df["error"] = df["point"] - df["realised"]
        df["abs_error"] = df["error"].abs()
        has_q = df["q10"].notna() & df["q90"].notna()
        df["inside_80"] = np.where(has_q, (df["realised"] >= df["q10"]) & (df["realised"] <= df["q90"]), np.nan)
        return df.reset_index(drop=True)

    def error_report(self) -> pd.DataFrame:
        """Bias, mean absolute error, and 80% band coverage by source, variable, and horizon (Section 5.4)."""
        e = self.errors()
        if e.empty:
            return pd.DataFrame(columns=["source", "variable", "horizon_q", "n", "bias", "mae", "coverage_80"])
        g = e.groupby(["source", "variable", "horizon_q"])
        return g.agg(n=("error", "size"), bias=("error", "mean"), mae=("abs_error", "mean"),
                     coverage_80=("inside_80", "mean")).reset_index()


def assert_no_lookahead(rows: pd.DataFrame, decision_time: datetime) -> None:
    """Raise LookAheadError if any forecast row was not readable at `decision_time` (framework R5)."""
    if len(rows) and (pd.to_datetime(rows["available_at"]) > pd.Timestamp(decision_time)).any():
        late = rows.loc[pd.to_datetime(rows["available_at"]) > pd.Timestamp(decision_time), ["source", "variable"]]
        raise LookAheadError(f"forecast rows not available at {decision_time}: {late.to_dict('records')}")


def widen_factor(coverage_80: float, n: int, target: float = 0.80, min_n: int = 8, bounds=(0.5, 3.0)) -> float:
    """Scale for the quantile spread so that the 80% band would have covered `target` of outcomes.

    Under normality the band half-width is 1.2816 sigma; a band that covered c instead of 0.80 has an
    effective half-width of z((1+c)/2) sigma. The factor is 1.2816 / z((1+c)/2). With fewer than `min_n`
    matured rows, return 1 (no evidence, no change).
    Intuition: a source whose bands miss too often gets wider bands before it moves a probability.
    """
    from scipy.stats import norm

    if n < min_n or not (coverage_80 == coverage_80):
        return 1.0
    c = float(np.clip(coverage_80, 0.02, 0.98))
    return float(np.clip(norm.ppf((1 + target) / 2) / norm.ppf((1 + c) / 2), *bounds))


def revisions(registry: ForecastRegistry, t_new: datetime, t_old: datetime, variables: Sequence[str] = VARIABLES) -> pd.DataFrame:
    """Change in point forecasts between what was known at `t_old` and at `t_new`, per source/variable/horizon.

    Intuition: a revision is news; signals S3 and S7 trade the news, not the level.
    """
    new = registry.as_of(t_new).set_index(["source", "variable", "horizon_q"])["point"]
    old = registry.as_of(t_old).set_index(["source", "variable", "horizon_q"])["point"]
    d = (new - old).dropna().rename("revision").reset_index()
    return d[d["variable"].isin(variables) | d["variable"].str.contains(":")]
