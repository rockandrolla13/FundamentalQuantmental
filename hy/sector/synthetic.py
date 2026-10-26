"""Synthetic panels for the sector package tests and for a smoke run on the production machine. No real data.

Each issuer has leverage L ~ U(2, 7), capex intensity c ~ U(0.05, 0.30) and a margin. The true log spread is

    log s = log 0.03 + 0.35 log L + 1.0 c + 0.04 eps,   eps ~ N(0, 1)

so in every sector the spread rises in leverage and in capex intensity. `cheap` multiplies the spreads of the named
issuers by CHEAP_FACTOR (a planted cheap bond). All panels carry the columns of docs/production_wiring.md section 5
and docs/factors/PRODUCTION_DATA.md section 2, with `available_at` after each record's date.
"""

from __future__ import annotations

from typing import Iterable, Mapping

import numpy as np
import pandas as pd

DAY = pd.Timedelta(1, unit="D")
CHEAP_FACTOR = 1.6


def make_panels(as_of="2015-06-30", sectors: Mapping[str, int] | None = None, seed: int = 0,
                cheap: Iterable[str] = (), two_bonds: Iterable[str] = (), months: int = 3,
                noise: float = 0.04, years: Mapping[str, float] | None = None) -> dict[str, pd.DataFrame]:
    """Panels for issuers G<sector>_<k> in each GICS sector of `sectors` (sector -> issuer count).

    One bond per issuer (cusip C<sector>_<k>_0), two for the issuers in `two_bonds`. Bond rows exist for the last
    `months` month ends to as_of. `years` fixes the maturity of the named issuers' bonds."""
    as_of = pd.Timestamp(as_of) + pd.offsets.MonthEnd(0)
    sectors = sectors or {"10": 25, "25": 25, "35": 6}
    rng = np.random.default_rng(seed)
    cheap, two = set(cheap), set(two_bonds)
    mends = pd.date_range(end=as_of, periods=months, freq="ME")
    bonds, lev, gics, rat, cq, ca, ae, eq = [], [], [], [], [], [], [], []
    for sec, n in sectors.items():
        for k in range(n):
            g = f"G{sec}_{k}"
            L = float(rng.uniform(2.0, 7.0)) if g not in cheap else 3.0
            c = float(rng.uniform(0.05, 0.30))
            ebitda = 100.0
            debt = L * ebitda
            sale = ebitda / float(rng.uniform(0.15, 0.30))
            rate = float(rng.uniform(0.05, 0.10))
            log_s = np.log(0.03) + 0.35 * np.log(L) + 1.0 * c + noise * float(rng.standard_normal())
            s = float(np.exp(log_s)) * (CHEAP_FACTOR if g in cheap else 1.0)
            cls = "BB" if L < 3.5 else ("B" if L < 5.5 else "CCC")
            for b in range(2 if g in two else 1):
                yrs = float(rng.uniform(2.0, 10.0))
                yrs = float((years or {}).get(g, yrs))
                for m in mends:
                    bonds.append({"date": m, "cusip": f"C{sec}_{k}_{b}", "gvkey": g, "years": yrs, "g_spread": s,
                                  "price": 100.0, "yield": 0.04 + s, "coupon": 0.04 + s, "mod_dur": 0.85 * yrs,
                                  "tsy_yield": 0.04, "bid_ask_pts": 0.5, "n_trades": 10, "par_volume": 1e6,
                                  "carried": False, "accrue_to": m, "hedge_date": m,
                                  "maturity": m + pd.DateOffset(years=int(yrs)),
                                  "available_at": m + DAY})
            for m in mends:
                lev.append({"date": m, "gvkey": g, "leverage": L, "ltm_ebitda": ebitda, "debt": debt,
                            "available_at": m + DAY})
                rat.append({"gvkey": g, "datadate": m, "splticrm": cls, "available_at": m + DAY})
            gics.append({"gvkey": g, "gsector": sec, "indfrom": pd.Timestamp("2000-01-01"), "indthru": pd.NaT,
                         "available_at": pd.Timestamp("2000-01-01")})
            qends = pd.date_range(end=as_of - pd.offsets.QuarterEnd(1), periods=8, freq="QE")
            for i, qd in enumerate(qends):
                cq.append({"gvkey": g, "datadate": qd, "rdq": qd + 40 * DAY, "available_at": qd + 40 * DAY,
                           "saleq": sale / 4, "oibdpq": ebitda / 4 * (1 + 0.01 * (i - 4)), "xintq": rate * debt / 4,
                           "capx": c * sale / 4, "oancf": 0.8 * ebitda / 4, "dlcq": 0.1 * debt, "dlttq": 0.9 * debt,
                           "cheq": 20.0, "dpq": 0.6 * c * sale / 4})
            fy_end = pd.Timestamp(f"{as_of.year - 1}-12-31")
            ca.append({"gvkey": g, "datadate": fy_end, "fyear": as_of.year - 1, "sale": sale, "cogs": 0.6 * sale,
                       "capx": c * sale, "oancf": 0.8 * ebitda, "xint": rate * debt, "dlc": 0.1 * debt,
                       "dltt": 0.9 * debt, "dd1": 0.05 * debt, "dd2": 0.10 * debt, "xrent": 0.05 * sale,
                       "che": 20.0, "at": 2 * debt, "available_at": fy_end + 60 * DAY})
            for y in range(10):
                fy = as_of.year - 10 + y
                d = pd.Timestamp(f"{fy}-12-31")
                ae.append({"gvkey": g, "datadate": d, "fyear": fy,
                           "oibdp": ebitda * (1 + 0.1 * float(rng.standard_normal())), "debt": debt,
                           "available_at": d + 60 * DAY})
            for m in pd.date_range(end=as_of, periods=8, freq="ME"):
                eq.append({"gvkey": g, "datadate": m, "ret": 0.01 * float(rng.standard_normal()),
                           "available_at": m + DAY})
    return {"bond_panel": pd.DataFrame(bonds), "leverage": pd.DataFrame(lev), "gics": pd.DataFrame(gics),
            "ratings": pd.DataFrame(rat), "compustat_quarterly": pd.DataFrame(cq),
            "compustat_annual": pd.DataFrame(ca), "annual_ebitda": pd.DataFrame(ae),
            "equity_monthly": pd.DataFrame(eq)}
