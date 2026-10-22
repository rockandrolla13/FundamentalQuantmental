"""Obligation and revenue schedules from one filing's XBRL instance (methodology Section 4.7 inputs).

Reads maturity ladders (operating leases, finance leases, debt principal, purchase obligations), the
remaining performance obligation and its timing, customer concentration, and signed leases not yet
commenced. Every ladder is checked against its stated total; a ladder that does not add up is reported,
not silently used.

10-Q ladders start with "remainder of fiscal year"; the following buckets are then full fiscal years, even
when tagged "next twelve months". 10-K ladders start with the next twelve months.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from hy import clocks

FAMILIES = {
    "operating_lease": ("LesseeOperatingLeaseLiabilityPayments", "LesseeOperatingLeaseLiabilityPaymentsDue",
                        "LesseeOperatingLease"),
    "finance_lease": ("FinanceLeaseLiabilityPayments", "FinanceLeaseLiabilityPaymentsDue", "FinanceLeaseLiability"),
    "debt": ("LongTermDebtMaturitiesRepaymentsOfPrincipal", None, "LongTermDebtMaturit"),
    "purchase": ("UnrecordedUnconditionalPurchaseObligation", "UnrecordedUnconditionalPurchaseObligationBalanceSheetAmount",
                 "UnconditionalPurchaseObligation"),
}
# bucket suffix -> position; 0 = remainder of fiscal year
SUFFIXES = [
    (0, ("RemainderOfFiscalYear", "DueInRemainderOfFiscalYear")),
    (1, ("DueNextTwelveMonths", "InNextTwelveMonths", "BalanceOnFirstAnniversary")),
    (2, ("DueYearTwo", "InYearTwo", "BalanceOnSecondAnniversary")),
    (3, ("DueYearThree", "InYearThree", "BalanceOnThirdAnniversary")),
    (4, ("DueYearFour", "InYearFour", "BalanceOnFourthAnniversary")),
    (5, ("DueYearFive", "InYearFive", "BalanceOnFifthAnniversary")),
]
AFTER = re.compile(r"(?:AfterYear(?:Four|Five)|AfterFifthYear|Thereafter|ToBePaidAfterYearFour|MaturityAfterYearFour)$")


def _local(c: str) -> str:
    return c.split(":")[-1]


def _undimensioned(df: pd.DataFrame, as_of: pd.Timestamp) -> pd.DataFrame:
    return df[(df["n_dims"] == 0) & (df["end"] == as_of) & df["start"].isna() & df["value"].notna()]


def as_of_date(df: pd.DataFrame) -> pd.Timestamp:
    """Balance-sheet date of the filing (the most common instant date)."""
    return df.loc[df["start"].isna(), "end"].mode().iloc[0]


def months_to_fiscal_year_end(df: pd.DataFrame, as_of: pd.Timestamp) -> float:
    """Months from `as_of` to the next fiscal year end, from dei:CurrentFiscalYearEndDate ("--MM-DD")."""
    s = df.loc[df["concept"] == "dei:CurrentFiscalYearEndDate", "text"]
    if not len(s):
        return 12.0
    mm = int(s.iloc[0][2:4])
    m = (mm - as_of.month) % 12
    return float(m if m else 12)


@dataclass
class Ladder:
    family: str
    amounts: list[float]
    first_length: float
    total: float
    reconciles: bool
    concepts: list[str] = field(default_factory=list)


# Filers tag the debt ladder under more than one family name; the first family that yields buckets wins.
DEBT_STEMS = {  # stem -> key that the "after year N" tag contains (filers often use their own tag for that line)
    "LongTermDebtMaturitiesRepaymentsOfPrincipal": "LongTermDebtMaturit",
    "LongTermDebtAndCapitalLeaseObligationsRepaymentsOfPrincipal": "LongTermDebtAndCapitalLeaseObligations",
    "LongTermDebtAndLeaseObligationsRepaymentsOfPrincipal": "LongTermDebtAndLeaseObligations",
}


def ladder(df: pd.DataFrame, family: str) -> Ladder | None:
    """One maturity ladder: bucket amounts in USD millions, the first bucket's length in years, and a sum check.

    For debt, every family name in `DEBT_STEMS` is tried in order (prefix ignored, so a filer's own tag counts).
    """
    if family == "debt":
        for stem, after_key in DEBT_STEMS.items():
            got = _ladder(df, family, stem, after_key)
            if got is not None:
                return got
        return None
    stem, _, after_key = FAMILIES[family]
    return _ladder(df, family, stem, after_key)


def _ladder(df: pd.DataFrame, family: str, stem: str, after_key: str) -> Ladder | None:
    _, total_concept, _ = FAMILIES[family]
    as_of = as_of_date(df)
    u = _undimensioned(df, as_of)
    loc = u.assign(local=u["concept"].map(_local))
    buckets: dict[int, float] = {}
    used = []
    for pos, sufs in SUFFIXES:
        hit = loc[loc["local"].isin([stem + s for s in sufs])]
        if len(hit):
            buckets[pos] = float(hit["value"].iloc[0]) / 1e6
            used.append(hit["concept"].iloc[0])
    after = loc[loc["local"].str.contains(after_key) & loc["local"].str.contains(AFTER)]
    if not buckets and not len(after):
        return None
    tail = float(after["value"].iloc[0]) / 1e6 if len(after) else 0.0
    if len(after):
        used.append(after["concept"].iloc[0])
    has_remainder = 0 in buckets
    positions = sorted(buckets)
    amounts = [buckets[p] for p in positions] + [tail]
    first_length = months_to_fiscal_year_end(df, as_of) / 12 if has_remainder else 1.0
    tot = loc[loc["local"] == total_concept]["value"] if total_concept else pd.Series(dtype=float)
    total = float(tot.iloc[0]) / 1e6 if len(tot) else float(sum(amounts))
    ok = abs(sum(amounts) - total) <= max(1.0, 0.005 * total)
    if not ok and total > sum(amounts) and tail == 0.0:
        # The "thereafter" line is untagged (Oracle purchase obligations): the residual is the tail.
        amounts[-1] = total - sum(amounts[:-1])
        used.append("residual_to_tail")
        ok = True
    return Ladder(family, amounts, first_length, total, ok, used)


DEBT_TOTAL_TAGS = ("LongTermDebt", "DebtInstrumentCarryingAmount", "LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities",
                   "DebtAndCapitalLeaseObligations")
DEBT_PART_TAGS = (("LongTermDebtCurrent", "LongTermDebtNoncurrent"), ("NotesPayableCurrent", "LongTermNotesAndLoans"),
                  ("DebtCurrent", "LongTermDebtNoncurrent"))


def _instant(df: pd.DataFrame, local: str) -> float:
    as_of = as_of_date(df)
    hit = df[(df["concept"].map(_local) == local) & (df["n_dims"] == 0) & (df["end"] == as_of) & df["start"].isna()]
    return float(hit["value"].iloc[0]) / 1e6 if len(hit) else float("nan")


def balance_sheet_debt(df: pd.DataFrame) -> tuple[float, str]:
    """Total financial debt at the balance-sheet date in USD m: a total tag, else current plus non-current (F5)."""
    for t in DEBT_TOTAL_TAGS:
        v = _instant(df, t)
        if v == v:
            return v, f"tag {t}"
    for cur, non in DEBT_PART_TAGS:
        a, b = _instant(df, cur), _instant(df, non)
        if b == b:
            return (0.0 if a != a else a) + b, f"tags {cur} + {non}"
    return float("nan"), "no debt tag"


def reconcile_debt(lad: Ladder | None, bs_debt: float, fallback_years: float = 10.0) -> tuple[Ladder | None, str]:
    """Check a debt ladder against balance-sheet debt; fill a missing tail; build an even ladder when none exists.

    - Ladder short of the balance sheet by more than 5% with an empty tail: the residual becomes the tail.
    - No ladder but a balance-sheet total: spread the total evenly over `fallback_years` (logged assumption).
    Intuition: principal that the filing does not schedule still falls due; leaving it out understates the clock.
    """
    if lad is None:
        if bs_debt == bs_debt and bs_debt > 0:
            n = int(fallback_years)
            return (Ladder("debt", [bs_debt / n] * n + [0.0], 1.0, bs_debt, True, ["even_fallback"]),
                    f"assumption: no debt ladder tagged; balance-sheet debt {bs_debt:,.0f} spread evenly over {n} years")
        return None, "no debt ladder and no balance-sheet debt"
    short = bs_debt - sum(lad.amounts)
    if bs_debt == bs_debt and short > 0.05 * bs_debt and lad.amounts[-1] == 0.0:
        amounts = list(lad.amounts[:-1]) + [short]
        return (Ladder("debt", amounts, lad.first_length, bs_debt, True, lad.concepts + ["residual_to_tail_bs"]),
                f"ladder short of balance-sheet debt by {short:,.0f}; residual put in 'thereafter'")
    return lad, "ladder as filed"


def rpo_windows(df: pd.DataFrame) -> tuple[float, list[tuple[float, float, float]]]:
    """Remaining performance obligation total (USD m) and its (start, length, share) windows in years from as-of."""
    as_of = as_of_date(df)
    loc = df.assign(local=df["concept"].map(_local))
    tot = loc[(loc["local"] == "RevenueRemainingPerformanceObligation") & (loc["n_dims"] == 0) & (loc["end"] == as_of)]
    if not len(tot):
        return float("nan"), []
    axis = "RevenueRemainingPerformanceObligationExpectedTimingOfSatisfactionStartDateAxis"
    pct = loc[loc["local"] == "RevenueRemainingPerformanceObligationPercentage"]
    per = loc[loc["local"] == "RevenueRemainingPerformanceObligationExpectedTimingOfSatisfactionPeriod1"]
    period = {_axis_member(d, axis): t for d, t in zip(per["dims"], per["text"])}
    windows = []
    for d, v in zip(pct["dims"], pct["value"]):
        start = _axis_member(d, axis)
        if start is None:
            continue
        s0 = (pd.Timestamp(start) - as_of).days / 365.25
        length = _iso_years(period.get(start)) if period.get(start) else float("nan")
        windows.append((round(max(0.0, s0), 3), length, float(v)))
    windows.sort()
    # A window without a stated length runs to the next window's start.
    fixed = []
    for i, (s0, ln, sh) in enumerate(windows):
        if np.isnan(ln):
            ln = windows[i + 1][0] - s0 if i + 1 < len(windows) else 1.0
        fixed.append((s0, ln, sh))
    return float(tot["value"].iloc[0]) / 1e6, fixed


def _axis_member(dims: dict, axis: str) -> str | None:
    for k, v in dims.items():
        if _local(k) == axis:
            return v
    return None


def _iso_years(s: str) -> float:
    m = re.fullmatch(r"P(?:(\d+)Y)?(?:(\d+)M)?", s or "")
    if not m:
        return float("nan")
    return int(m.group(1) or 0) + int(m.group(2) or 0) / 12


def customer_shares(df: pd.DataFrame) -> dict[str, float]:
    """Revenue share by named customer for the latest quarter (shortest period ending at the as-of date)."""
    as_of = as_of_date(df)
    loc = df.assign(local=df["concept"].map(_local))
    c = loc[(loc["local"] == "ConcentrationRiskPercentage1") & (loc["end"] == as_of)]
    rows = []
    for d, v, st in zip(c["dims"], c["value"], c["start"]):
        short = {_local(k): _local(m) for k, m in d.items()}
        if short.get("ConcentrationRiskByBenchmarkAxis", "").startswith("Revenue") and "MajorCustomersAxis" in short:
            rows.append((short["MajorCustomersAxis"], v, (as_of - st).days))
    if not rows:
        return {}
    shortest = min(r[2] for r in rows)
    return {name: val for name, val, days in rows if days == shortest}


def lease_not_commenced(df: pd.DataFrame) -> tuple[float, float, float]:
    """Signed leases not yet commenced: (total USD m, min term years, max term years), NaN when not tagged.

    Looks for an undimensioned USD concept naming a lease not yet commenced; else a purchase obligation whose
    member names data centers without a range axis (CoreWeave tags its leases this way).
    """
    as_of = as_of_date(df)
    loc = df.assign(local=df["concept"].map(_local))
    amt = loc[loc["local"].str.contains("NotYetCommenced") & (loc["unit"].fillna("").str.upper().str.contains("USD"))
              & (loc["n_dims"] == 0) & (loc["end"] == as_of)]
    total = float(amt["value"].iloc[0]) / 1e6 if len(amt) else float("nan")
    if np.isnan(total):
        po = loc[(loc["local"] == "UnrecordedUnconditionalPurchaseObligationBalanceSheetAmount") & (loc["end"] == as_of)]
        for d, v in zip(po["dims"], po["value"]):
            short = {_local(k): _local(m) for k, m in d.items()}
            if "RangeAxis" not in short and any("DataCenter" in m for m in short.values()):
                total = float(v) / 1e6
                break
    terms = loc[loc["local"].str.contains("NotYetCommencedTermOfContract")]
    lo = hi = float("nan")
    for d, t in zip(terms["dims"], terms["text"]):
        rng = {_local(m) for m in d.values()}
        if "MinimumMember" in rng:
            lo = _iso_years(t)
        if "MaximumMember" in rng:
            hi = _iso_years(t)
    return total, lo, hi


def to_buckets(lad: Ladder, tail_years: float) -> list[clocks.Bucket]:
    return clocks.ladder(lad.amounts, lad.first_length, tail_years)
