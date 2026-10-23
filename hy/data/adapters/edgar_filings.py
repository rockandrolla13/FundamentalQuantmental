"""EDGAR adapter: filings and the inputs derived from them (wraps hy.sources.edgar, hy.sources.clock_inputs)."""

from __future__ import annotations

from datetime import datetime
from typing import Sequence

import pandas as pd

from hy.data.adapters import guarded_fetch
from hy.data.config import DataConfig
from hy.data.pit import DataUnavailable
from hy.data.records import Filing, Issuer, IssuerFacts
from hy.sources import clock_inputs as ci
from hy.sources import edgar


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
