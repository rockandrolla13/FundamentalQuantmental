"""Two-clocks measures as known at each 10-K and 10-Q, from SEC XBRL companyfacts (methodology Sections 4.7 and 11).

`scripts/clock_case.py` builds the Section 4.7 case from one filing's full XBRL instance. A backtest needs the same
case at every filing of about 1,500 issuers, so this module reads the companyfacts feed instead (one document per
issuer, every filing's undimensioned facts). Each filing's facts become an undimensioned instance table, and the
existing code runs on it unchanged: `schedules.ladder`, `schedules.reconcile_debt`, `clocks.ladder`,
`clocks.tail_years_run_rate`, `clocks.rpo`, and `clocks.mismatch`.

Rules (each one is a decision):
1. Obligations: operating and finance lease payments, debt principal, purchase obligations, each from its maturity
   ladder. No interest (no rate in the feed) and no leases not yet commenced (dimensional, absent from the feed).
2. Tag names. Filers use rolling-year and newer purchase names that `schedules.SUFFIXES` does not list; they are mapped
   to the listed names when the listed name is absent (`canonical_tag`). A missing year inside a ladder counts as
   zero (`fill_ladder_gaps`), so later buckets keep their positions; such ladders are flagged.
3. RPO timing. Companyfacts drops the dimensional timing facts. The revenue clock therefore uses the `clock_inputs`
   default: the whole RPO evenly over `DEFAULT_RPO_TAIL` = 2 years. The duration gap is then the obligation duration
   less 1 year, and the renewal-dependent share is the share of obligations due after year 2.
4. Timing. Companyfacts gives the filing date, not the acceptance time. A filing's measures are available from the
   filing date + 1 day. A filing that omits a ladder takes the last earlier one (at most `CARRY_DAYS` old), aged by
   the time between the two balance-sheet dates, as `clock_case` ages a 10-K ladder to a 10-Q date.
"""

from __future__ import annotations

import gzip
import json
import re
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

import numpy as np
import pandas as pd

from hy import clocks
from hy.sources import clock_inputs as ci
from hy.sources import schedules as sc

USER_AGENT = "FundamentalQuantmental ak.g.home@protonmail.ch"
BASE = "https://data.sec.gov/api/xbrl/companyfacts/"
MAX_PER_SECOND = 8.0          # SEC limit is 10; stay under it across threads
HORIZON = 25                  # years on the clock grid, as in clock_case
CARRY_DAYS = 400              # oldest ladder a later filing may carry forward
PERIODIC = ("10-K", "10-Q", "10-K/A", "10-Q/A", "10-KT", "10-QT")
STEMS = tuple(dict.fromkeys(
    [v[0] for v in sc.FAMILIES.values()] + list(sc.DEBT_STEMS)
    + ["UnrecordedUnconditionalPurchaseObligation", "RevenueRemainingPerformanceObligation"]
))
DEBT_TAGS = tuple(sc.DEBT_TOTAL_TAGS) + tuple(t for pair in sc.DEBT_PART_TAGS for t in pair)
_ORD = {"Second": "Two", "Third": "Three", "Fourth": "Four", "Fifth": "Five"}
_RENAMES = [
    (re.compile(r"Due(?:In)?Next(?:Rolling)?TwelveMonths$"), lambda m: "DueNextTwelveMonths"),
    (re.compile(r"DueIn(?:Rolling)?Year(Two|Three|Four|Five)$"), lambda m: f"DueYear{m.group(1)}"),
    (re.compile(r"DueIn(Second|Third|Fourth|Fifth)Year$"), lambda m: f"DueYear{_ORD[m.group(1)]}"),
    (re.compile(r"(?:DueAfterRollingYearFive|DueInRollingAfterYearFive)$"), lambda m: "DueAfterYearFive"),
]


# ---------------------------------------------------------------- fetch and cache


class RateLimiter:
    """At most `per_second` calls across all threads."""

    def __init__(self, per_second: float = MAX_PER_SECOND) -> None:
        self.gap = 1.0 / per_second
        self.lock = threading.Lock()
        self.next_t = 0.0

    def wait(self) -> None:
        with self.lock:
            now = time.monotonic()
            t = max(now, self.next_t)
            self.next_t = t + self.gap
        if t > now:
            time.sleep(t - now)


_LIMIT = RateLimiter()


def fetch_sec_json(url: str, limiter: RateLimiter = _LIMIT) -> dict | None:
    """GET a JSON document from sec.gov with the project User-Agent; None on 404 (no XBRL filer)."""
    if not url.startswith("https://data.sec.gov/"):
        raise ValueError("only data.sec.gov is allowed")
    limiter.wait()
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "gzip"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
            if resp.headers.get("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def keep_tag(tag: str) -> bool:
    return tag.startswith(STEMS) or tag in DEBT_TAGS


def extract(doc: dict | None) -> pd.DataFrame:
    """Long table of the kept us-gaap USD facts: tag, start, end, val (USD), accn, form, filed, fp."""
    cols = ["tag", "start", "end", "val", "accn", "form", "filed", "fp"]
    rows = []
    for tag, body in ((doc or {}).get("facts", {}).get("us-gaap", {}) or {}).items():
        if not keep_tag(tag):
            continue
        for f in body.get("units", {}).get("USD", []):
            rows.append((tag, f.get("start"), f["end"], float(f["val"]), f["accn"], f.get("form"), f.get("filed"),
                         f.get("fp")))
    df = pd.DataFrame(rows, columns=cols)
    for c in ("start", "end", "filed"):
        df[c] = pd.to_datetime(df[c], errors="coerce")
    return df


def cache_path(root: Path, cik: int | str) -> Path:
    return Path(root) / "edgar" / f"clockfacts_CIK{int(float(cik)):010d}.parquet"


def load_facts(cik: int | str, cache_root: Path, fetch: Callable[[str], dict | None] = fetch_sec_json) -> pd.DataFrame:
    """Kept facts for one CIK; the extract (not the full document) is cached as parquet, an empty file for a 404."""
    p = cache_path(cache_root, cik)
    if p.exists():
        return pd.read_parquet(p)
    df = extract(fetch(f"{BASE}CIK{int(float(cik)):010d}.json"))
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(p, index=False)
    return df


def load_many(ciks: Sequence[str], cache_root: Path, workers: int = 4, log: Callable[[str], None] = print) -> dict[str, float]:
    """Fetch every uncached CIK with `workers` threads under one shared rate limit. Returns timing."""
    todo = [c for c in ciks if not cache_path(cache_root, c).exists()]
    t0, done, fails = time.time(), [0], []

    def one(c: str) -> None:
        try:
            load_facts(c, cache_root)
        except Exception as e:  # noqa: BLE001  (one bad document must not stop the pull; it is reported)
            fails.append((c, repr(e)[:120]))
        done[0] += 1
        if done[0] % 200 == 0:
            log(f"  companyfacts {done[0]}/{len(todo)}: {time.time() - t0:.0f} s")

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(one, todo))
    return {"fetched": len(todo), "seconds": time.time() - t0, "failed": len(fails), "fail_examples": fails[:5]}


# ---------------------------------------------------------------- one filing as an instance table


def canonical_tag(tag: str) -> str:
    """Map rolling-year and newer purchase-obligation names to the names `schedules.SUFFIXES` lists (rule 2)."""
    for rx, fn in _RENAMES:
        m = rx.search(tag)
        if m:
            return tag[: m.start()] + fn(m)
    return tag


def fill_ladder_gaps(tags: Mapping[str, float]) -> tuple[dict[str, float], bool]:
    """Insert zero for a missing year between the first year and the last stated year of each ladder (rule 2).

    `schedules._ladder` stacks the buckets it finds in order, so a missing year would move every later bucket one
    year earlier. Returns the filled tags and whether any gap was filled.
    """
    out, filled = dict(tags), False
    stems = list(sc.DEBT_STEMS) + [v[0] for v in sc.FAMILIES.values() if v[0] not in sc.DEBT_STEMS]
    for stem in stems:
        found = {}
        for pos, sufs in sc.SUFFIXES:
            for s in sufs:
                if stem + s in out:
                    found[pos] = s
        if not found:
            continue
        lo = 0 if 0 in found else 1
        style = next((_style(s) for p, s in sorted(found.items()) if p >= 1), None)
        for pos in range(lo, max(found) + 1):
            if pos not in found:
                sufs = dict(sc.SUFFIXES)[pos]
                pick = next((s for s in sufs if _style(s) == style), sufs[0])
                out[stem + pick] = 0.0
                filled = True
    return out, filled


def _style(suffix: str) -> str:
    """Naming style of a ladder suffix: 'Due...' (leases), 'In...' (debt), 'Balance...' (old purchase names)."""
    for k in ("Due", "In", "Balance"):
        if suffix.startswith(k):
            return k
    return ""


def filing_frame(facts: pd.DataFrame, accn: str, fye_month: int) -> pd.DataFrame:
    """Instance-shaped table (concept, value, text, start, end, dims, n_dims) of one filing at its balance-sheet date.

    Values in USD, as in `xbrl_instance`. Adds dei:CurrentFiscalYearEndDate so `schedules` can size a 10-Q's
    remainder-of-year bucket.
    """
    f = facts[(facts["accn"] == accn) & facts["start"].isna()]
    as_of = f["end"].max()
    f = f[f["end"] == as_of]
    vals: dict[str, float] = {}
    for tag, v in zip(f["tag"], f["val"]):
        vals.setdefault(tag, v)
    for tag in list(vals):
        c = canonical_tag(tag)
        if c != tag and c not in vals:
            vals[c] = vals.pop(tag)
    vals, filled = fill_ladder_gaps(vals)
    rows = [{"concept": f"us-gaap:{k}", "value": v, "text": None, "start": pd.NaT, "end": as_of, "dims": {},
             "n_dims": 0} for k, v in vals.items()]
    rows.append({"concept": "dei:CurrentFiscalYearEndDate", "value": np.nan, "text": f"--{int(fye_month):02d}-28",
                 "start": pd.NaT, "end": as_of, "dims": {}, "n_dims": 0})
    out = pd.DataFrame(rows)
    out.attrs["gap_filled"] = filled
    return out


def fiscal_year_end_month(facts: pd.DataFrame) -> int:
    """Month of the fiscal year end: the most common balance-sheet month of the 10-K filings (12 if none)."""
    k = facts[facts["form"].astype(str).str.startswith("10-K")]
    if k.empty:
        return 12
    ends = k.groupby("accn")["end"].max().dropna()
    return int(ends.dt.month.mode().iloc[0]) if len(ends) else 12


# ---------------------------------------------------------------- the Section 4.7 case per filing


def _debt_tail(lad: sc.Ladder) -> float:
    """`clock_inputs` debt tail rule: run-rate tail when the last two buckets are positive, capped; else 5 years."""
    if len(lad.amounts) >= 2 and lad.amounts[-2] > 0 and lad.amounts[-1] > 0:
        return min(clocks.tail_years_run_rate(lad.amounts), ci.MAX_DEBT_TAIL)
    return ci.DEFAULT_DEBT_TAIL


def _aged(buckets: list[clocks.Bucket], shift: float) -> list[clocks.Bucket]:
    """`clock_case` ageing: a ladder dated `shift` years before the as-of date starts that much earlier."""
    return [clocks.Bucket(max(0.0, b.start - shift), b.length, b.amount) for b in buckets]


def filing_states(facts: pd.DataFrame, cik: str) -> pd.DataFrame:
    """One row per periodic filing: the Section 4.7 obligation and revenue clocks as known at its filing date.

    Columns: cik, accn, form, as_of, available_at, obligations_total, lease_total, debt_total, purchase_total,
    dur_obligations, dur_revenue, duration_gap, renewal_dependent_share, rpo_total, rent_1y, carried (components
    taken from an earlier filing), gap_filled. Amounts in USD millions.
    """
    f = facts[facts["form"].isin(PERIODIC) & facts["filed"].notna()]
    if f.empty:
        return pd.DataFrame()
    fye = fiscal_year_end_month(f)
    filings = f.groupby("accn").agg(form=("form", "first"), filed=("filed", "min")).sort_values("filed")
    last: dict[str, tuple[pd.Timestamp, object]] = {}
    rows = []
    for accn, meta in filings.iterrows():
        df = filing_frame(f, accn, fye)
        if df["end"].isna().all():
            continue
        as_of = sc.as_of_date(df)
        found = {
            "op": sc.ladder(df, "operating_lease"), "fin": sc.ladder(df, "finance_lease"),
            "debt": sc.ladder(df, "debt"), "pur": sc.ladder(df, "purchase"),
        }
        rpo_total = sc._instant(df, "RevenueRemainingPerformanceObligation")
        found["rpo"] = rpo_total if rpo_total == rpo_total and rpo_total > 0 else None
        use, carried = {}, []
        for key, val in found.items():
            if val is not None:
                last[key] = (as_of, val)
                use[key] = (val, 0.0)
            elif key in last and (as_of - last[key][0]).days <= CARRY_DAYS:
                use[key] = (last[key][1], (as_of - last[key][0]).days / 365.25)
                carried.append(key)
        obligations: dict[str, list[clocks.Bucket]] = {}
        for key in ("op", "fin"):
            if key in use:
                lad, shift = use[key]
                obligations.setdefault("Leases in force", [])
                obligations["Leases in force"] += _aged(sc.to_buckets(lad, clocks.tail_years_run_rate(lad.amounts)), shift)
        bs_debt, _ = sc.balance_sheet_debt(df)
        debt, shift = use.get("debt", (None, 0.0))
        debt, _ = sc.reconcile_debt(debt, bs_debt)
        if debt is not None:
            obligations["Debt principal"] = _aged(sc.to_buckets(debt, _debt_tail(debt)), shift)
        if "pur" in use:
            lad, shift = use["pur"]
            obligations["Purchase commitments"] = _aged(sc.to_buckets(lad, clocks.tail_years_run_rate(lad.amounts, 2.0)), shift)
        if not obligations:
            continue
        rpo = use.get("rpo", (None, 0.0))[0]
        revenue = clocks.rpo(rpo, [], ci.DEFAULT_RPO_TAIL) if rpo else []
        m = clocks.mismatch(obligations, revenue, 0.0, HORIZON).metrics
        grids = {k: clocks.to_grid(v, HORIZON).sum() for k, v in obligations.items()}
        op = use.get("op", (None, 0.0))[0]
        rent = op.amounts[0] / op.first_length if op is not None and op.first_length > 0 else 0.0
        rows.append({
            "cik": str(cik), "accn": accn, "form": meta["form"], "as_of": as_of,
            "available_at": pd.Timestamp(meta["filed"]) + pd.Timedelta(days=1),
            "obligations_total": m["obligations_total"], "lease_total": grids.get("Leases in force", 0.0),
            "debt_total": grids.get("Debt principal", 0.0), "purchase_total": grids.get("Purchase commitments", 0.0),
            "dur_obligations": m["dur_obligations"],
            "dur_revenue": m["dur_revenue"] if rpo else np.nan,
            "duration_gap": m["duration_gap"] if rpo else np.nan,
            "renewal_dependent_share": m["renewal_dependent_share"] if rpo else np.nan,
            "renewal_refinance_share": m["renewal_refinance_share"] if rpo else np.nan,
            "renewal_recontract_share": m["renewal_recontract_share"] if rpo else np.nan,
            "rpo_total": rpo if rpo else np.nan, "rent_1y": rent,
            "carried": ",".join(carried), "gap_filled": bool(df.attrs.get("gap_filled", False)),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- monthly signals


YEARS_CAP = 50.0              # fixed charges in years of EBITDAR when EBITDAR <= 0
RPO_MATERIAL = 0.25           # RPO at least this share of LTM revenue makes the renewal share meaningful
STALE_DAYS = 456              # balance-sheet date at most 15 months before the decision time


def clock_signals_as_of(states: pd.DataFrame, fundamentals_t: pd.DataFrame, cik_by_gvkey: Mapping[str, str],
                        as_of: pd.Timestamp) -> pd.DataFrame:
    """The three Section 4.7 signals per issuer as known at `as_of`, oriented as the combined score uses them
    (higher = less clock risk = expected to earn more):

    e5     = -(obligations_total / EBITDAR), EBITDAR = LTM EBITDA + first-year rent; EBITDAR <= 0 maps to -YEARS_CAP.
             When the filing gives no debt, Compustat debt at `as_of` is added (`debt_source = 'compustat'`).
    dgap   = -duration_gap                       (only where RPO exists)
    renew  = -renewal_dependent_share            (only where RPO >= RPO_MATERIAL x LTM revenue)
    renew_refi, renew_recon = the same, split into debt (refinance) and rent plus purchases (recontract)

    Uses the latest filing with `available_at <= as_of` whose balance-sheet date is at most `STALE_DAYS` old, and the
    issuer's fundamentals row known at `as_of`. Intuition: fixed charges a lender must be paid, measured in years of
    the cash that pays them.
    """
    from hy.backtest import assert_no_lookahead

    t = pd.Timestamp(as_of)
    assert_no_lookahead(fundamentals_t, t, "fundamentals")
    s = states[(states["available_at"] <= t) & ((t - states["as_of"]).dt.days <= STALE_DAYS)]
    s = s.sort_values(["cik", "available_at"]).groupby("cik").tail(1).set_index("cik")
    fund = fundamentals_t.drop_duplicates("gvkey", keep="last").set_index("gvkey")
    rows = []
    for g, cik in cik_by_gvkey.items():
        if cik not in s.index or g not in fund.index:
            continue
        r, fr = s.loc[cik], fund.loc[g]
        obligations, debt_source = r["obligations_total"], "xbrl"
        if r["debt_total"] <= 0 and fr.get("debt", 0.0) > 0:
            # The filing tags no debt ladder and no debt total: add Compustat debt as known at `as_of`.
            obligations, debt_source = obligations + fr["debt"], "compustat"
        ebitdar = fr["ltm_ebitda"] + r["rent_1y"]
        years = obligations / ebitdar if ebitdar > 0 else YEARS_CAP
        material = r["rpo_total"] == r["rpo_total"] and fr.get("ltm_revenue", np.nan) > 0 and \
            r["rpo_total"] >= RPO_MATERIAL * fr["ltm_revenue"]
        rows.append({"gvkey": g, "cik": cik, "fixed_charge_years": float(min(max(years, 0.0), YEARS_CAP)),
                     "e5": -float(min(max(years, 0.0), YEARS_CAP)),
                     "dgap": -r["duration_gap"] if r["duration_gap"] == r["duration_gap"] else np.nan,
                     "renew": -r["renewal_dependent_share"] if material else np.nan,
                     "renew_refi": -r.get("renewal_refinance_share", np.nan) if material else np.nan,
                     "renew_recon": -r.get("renewal_recontract_share", np.nan) if material else np.nan,
                     "rpo_material": bool(material), "debt_source": debt_source, "state_as_of": r["as_of"],
                     "available_at": max(r["available_at"], fr["available_at"])})
    return pd.DataFrame(rows)
