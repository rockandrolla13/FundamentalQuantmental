"""EDGAR adapter: filings, the inputs derived from them, and each filing's balance sheet and schedules (wraps
hy.sources.edgar, hy.sources.clock_inputs, hy.sources.xbrl_instance, hy.sources.schedules)."""

from __future__ import annotations

from datetime import datetime
from typing import Sequence

import pandas as pd

from hy.data.adapters import guarded_fetch
from hy.data.config import DataConfig
from hy.data.pit import DataUnavailable
from hy.data.records import LADDER_FAMILIES, BalanceSheet, Filing, Issuer, IssuerFacts, Ladder
from hy.sources import clock_inputs as ci
from hy.sources import edgar
from hy.sources import schedules as sc
from hy.sources import xbrl_instance as xi


def facts(iss: Issuer, decision_time: datetime, cfg: DataConfig) -> IssuerFacts:
    """`derive_inputs` as known at `decision_time`; stamped with the latest 10-Q acceptance."""
    try:
        v = ci.derive_inputs(iss.ticker, cfg.root, as_of=decision_time, allow_wrds=cfg.allow_network)
    except Exception as exc:  # noqa: BLE001
        raise DataUnavailable("facts", iss.ticker, f"{type(exc).__name__}: {exc}") from exc
    acc = pd.Timestamp(v["q_acceptance"][0]).tz_localize(None).to_pydatetime()
    return IssuerFacts(iss.ticker, acc, acc, issuer_ticker=iss.ticker, values=v)


def filings(iss: Issuer, forms: Sequence[str], cfg: DataConfig) -> list[Filing]:
    """The EDGAR filing index rows of `forms`, each stamped with its acceptance time."""
    if not iss.cik:
        raise DataUnavailable("filings", iss.ticker, "no CIK")
    idx = edgar.filing_index(iss.cik, fetch=guarded_fetch(cfg, edgar.fetch_json), cache_root=cfg.root)
    idx = idx[idx["form"].isin(list(forms))]
    out = []
    for r in idx.itertuples():
        acc = pd.Timestamp(r.acceptance).tz_localize(None).to_pydatetime()
        out.append(Filing(str(r.accession), acc, acc, issuer_ticker=iss.ticker, form=str(r.form), accession=str(r.accession)))
    return out


def acceptance(iss: Issuer, accession: str, cfg: DataConfig):
    """The EDGAR acceptance time (naive UTC) of one accession of the issuer."""
    if not iss.cik:
        raise DataUnavailable("filing", iss.ticker, "no CIK")
    try:
        idx = edgar.filing_index(iss.cik, fetch=guarded_fetch(cfg, edgar.fetch_json), cache_root=cfg.root)
    except Exception as exc:  # noqa: BLE001
        raise DataUnavailable("filing", accession, f"{type(exc).__name__}: {exc}") from exc
    hit = idx.loc[idx["accession"] == accession, "acceptance"]
    if hit.empty or pd.isna(hit.iloc[0]):
        raise DataUnavailable("filing", accession, "not in the EDGAR filing index")
    return pd.Timestamp(hit.iloc[0]).to_pydatetime()


# Credit-line capacity tags, in order of preference (the scenario engine's revolver rule).
REVOLVER_TAGS = ("LineOfCreditFacilityRemainingBorrowingCapacity", "LineOfCreditFacilityMaximumBorrowingCapacity")


def _ladder(lad) -> Ladder | None:
    return None if lad is None else Ladder(lad.family, list(lad.amounts), lad.first_length, lad.total, lad.reconciles,
                                           list(lad.concepts))


def balance_sheet(iss: Issuer, accession: str, cfg: DataConfig) -> BalanceSheet:
    """Balance-sheet values and schedules of one filing from its XBRL instance. The rules are the ones that
    scripts/clock_case.py, scripts/rv_pair.py and scripts/scenarios.py applied to the instance before (data module)."""
    acc_time = acceptance(iss, accession, cfg)
    try:
        q = xi.load_instance(iss.cik, accession, cache_root=cfg.root, fetch=guarded_fetch(cfg, edgar.fetch_json),
                             fetch_raw=guarded_fetch(cfg, xi.fetch_bytes))
    except Exception as exc:  # noqa: BLE001
        raise DataUnavailable("balance_sheet", accession, f"{type(exc).__name__}: {exc}") from exc
    as_of = pd.Timestamp(sc.as_of_date(q)).to_pydatetime()
    debt, debt_src = sc.balance_sheet_debt(q)
    cap = None
    for tag in REVOLVER_TAGS:
        hit = q[(q["concept"].str.split(":").str[-1] == tag) & (q["n_dims"] == 0)]
        if len(hit):
            cap = float(hit["value"].iloc[0]) / 1e6
            break
    return BalanceSheet(
        accession, as_of, max(as_of, acc_time), issuer_ticker=iss.ticker, accession=accession, debt=debt,
        debt_source=debt_src, operating_lease_liability=sc._instant(q, "OperatingLeaseLiability"),  # noqa: SLF001
        finance_lease_liability=sc._instant(q, "FinanceLeaseLiability"),  # noqa: SLF001
        cash=sc._instant(q, "CashAndCashEquivalentsAtCarryingValue"),  # noqa: SLF001
        revolver_capacity=cap, ladders={f: _ladder(sc.ladder(q, f)) for f in LADDER_FAMILIES},
        lease_not_commenced=sc.lease_not_commenced(q), customer_shares=sc.customer_shares(q))
