"""Synthetic panels for the hy.quality tests. No tests here: the other test_quality_*.py files import it.

One latent quality q in [0, 1] per issuer drives every fundamental: leverage 7x to 2x, coverage, gross profit
over assets and its trend, owner cash flow, liquidity, the 2009 EBITDA fall, and size. The spread falls with q.
Two planted issuers break the spread link: HQC (best fundamentals, rated BB+, wide spread) and LQR (worst
fundamentals, rated CCC, tight spread).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from hy.backtest import decision_time

AS_OF = pd.Timestamp("2012-06-30")
DT = decision_time(AS_OF)
N = 30
YEARS = range(2001, 2012)


def issuers() -> dict[str, float]:
    q = {f"G{i:02d}": 0.02 + 0.96 * i / (N - 1) for i in range(N)}
    q.update({"HQC": 1.0, "LQR": 0.0})
    return q


def rating_symbol(g: str, q: float) -> str:
    if g == "HQC":
        return "BB+"
    if g == "LQR":
        return "CCC"
    return "BB" if q >= 0.6 else ("B" if q >= 0.3 else "CCC+")


def spread(g: str, q: float, k: int) -> float:
    """Normal names: 300 bp at the top to 1100 bp at the bottom, with a small bond wiggle k."""
    if g == "HQC":
        return 0.090 + 0.002 * k
    if g == "LQR":
        return 0.025 + 0.002 * k
    return 0.03 + 0.08 * (1.0 - q) + 0.001 * k + 0.002 * np.sin(7.0 * q)


def _ann(g: str, fy: int, **v) -> dict:
    d = pd.Timestamp(f"{fy}-12-31")
    return {"gvkey": g, "datadate": d, "fyear": fy, "available_at": d + pd.Timedelta(90, unit="D"), **v}


def fundamentals(q_map: dict[str, float]) -> tuple[pd.DataFrame, pd.DataFrame]:
    ann, ebd = [], []
    for g, q in q_map.items():
        debt = 100.0 * (7.0 - 5.0 * q)
        at = 600.0 * (1.0 + q)
        for fy in YEARS:
            e = 100.0 * (1.0 - (0.6 - 0.5 * q)) if fy == 2009 else 100.0
            prof = 0.05 + 0.10 * q + 0.01 * q * (fy - 2006)
            xint = 0.08 * debt
            ann.append(_ann(g, fy, sale=500.0, cogs=500.0 - prof * at, at=at, che=10.0 + 100.0 * q, xint=xint,
                            capx=20.0, dd1=0.1 * debt, dd2=0.1 * debt, oancf=e - xint - 15.0 - 30.0 * (1 - q),
                            aqc=0.0, intpn=xint, dp=20.0, dlc=0.1 * debt, dltt=0.9 * debt,
                            revolver_undrawn=50.0 * q))
            ebd.append(_ann(g, fy, oibdp=e, debt=debt))
    return pd.DataFrame(ann), pd.DataFrame(ebd)


def months(n: int = 1) -> list[pd.Timestamp]:
    return list(pd.date_range(end=AS_OF, periods=n, freq="ME"))


def bonds(q_map: dict[str, float], month_list=None, per: int = 2, widen=None) -> pd.DataFrame:
    """Two bonds per issuer per month end. `widen(month_index)` scales spreads by 1 + widen x (1 - q)."""
    rows = []
    month_list = month_list or months(1)
    for mi, m in enumerate(month_list):
        f = widen(mi) if widen else 0.0
        for g, q in q_map.items():
            for k in range(per):
                s = spread(g, q, k) * (1.0 + f * (1.0 - q))
                years = 4.0 + 3.0 * k
                rows.append({"date": m, "cusip": f"{g}B{k}", "gvkey": g, "years": years, "g_spread": s,
                             "price": 100.0 - 40.0 * (1.0 - q) if g != "LQR" else 98.0, "yield": s + 0.02,
                             "mod_dur": 0.85 * years, "carried": False, "available_at": decision_time(m)})
    return pd.DataFrame(rows)


def ratings(q_map: dict[str, float], month_list=None) -> pd.DataFrame:
    month_list = month_list or months(1)
    return pd.DataFrame([{"gvkey": g, "datadate": m, "splticrm": rating_symbol(g, q), "available_at": m}
                         for m in month_list for g, q in q_map.items()])


def gics(q_map: dict[str, float], sectors: dict[str, str] | None = None) -> pd.DataFrame:
    sectors = sectors or {}
    return pd.DataFrame([{"gvkey": g, "gsector": sectors.get(g, "20"), "indfrom": pd.Timestamp("2000-01-01"),
                          "indthru": pd.NaT, "available_at": pd.Timestamp("2000-01-01")} for g in q_map])


def panels(q_map: dict[str, float] | None = None, month_list=None, widen=None, sectors=None) -> dict:
    q_map = q_map or issuers()
    ann, ebd = fundamentals(q_map)
    return {"bond_panel": bonds(q_map, month_list, widen=widen), "compustat_annual": ann, "annual_ebitda": ebd,
            "gics": gics(q_map, sectors), "ratings": ratings(q_map, month_list)}


def by_issuer(out: pd.DataFrame, col: str) -> pd.Series:
    return out.drop_duplicates("gvkey").set_index("gvkey")[col]
