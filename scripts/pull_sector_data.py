"""Data pull for the sector rules and the medium-term model (decision pages 2026-10-24-wt-sector-rules and
2026-10-24-medium-term-model, "How the test is built", step 1). Vendor data stays out of git: files go to
data/raw/sector_rules/ (or $HY_DATA_ROOT/sector_rules/).

Run (WRDS access needed; each file is skipped when it exists):
    PYTHONPATH=. python3 scripts/pull_sector_data.py

Files:
- fundq_all.parquet    comp.fundq, US firms (comp.company fic = 'USA'), all sectors, 1990-, INDL/STD/D/C.
- gics_hist.parquet    comp.co_hgic: GICS sector and industry group in force from indfrom to indthru.
- crsp_msf.parquet     crsp.msf for US common stocks (share codes 10, 11; exchanges 1-3), 1993-, with the
                       delisting return folded in: (1 + ret)(1 + dlret) - 1 in the delisting month.
- ccm_link.parquet     crsp.ccmxpf_lnkhist, link types LU and LC, primary links P and C.
- fred_<id>.csv        HSN1F (new home sales), OEHRENWBSHNO (household owners' equity).
"""

from __future__ import annotations

import os
import sys
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FRED_IDS = ("HSN1F", "OEHRENWBSHNO")


def out_dir() -> Path:
    base = Path(os.environ["HY_DATA_ROOT"]) if os.environ.get("HY_DATA_ROOT") else ROOT / "data" / "raw"
    d = base / "sector_rules"
    d.mkdir(parents=True, exist_ok=True)
    return d


SQL = {
    "fundq_all": """
        select f.gvkey, f.datadate, f.fyearq, f.fqtr, f.datacqtr, f.rdq, f.saleq, f.revtq, f.oibdpq, f.ibq,
               f.atq, f.ceqq, f.dlttq, f.dlcq
        from comp.fundq f join comp.company c on c.gvkey = f.gvkey
        where f.indfmt = 'INDL' and f.datafmt = 'STD' and f.popsrc = 'D' and f.consol = 'C'
          and c.fic = 'USA' and f.datadate >= '1990-01-01'""",
    "gics_hist": "select gvkey, indfrom, indthru, gsector, ggroup, gind from comp.co_hgic",
    "ccm_link": """
        select gvkey, lpermno as permno, linktype, linkprim, linkdt, linkenddt from crsp.ccmxpf_lnkhist
        where linktype in ('LU', 'LC') and linkprim in ('P', 'C')""",
    "crsp_msf": """
        select m.permno, m.date, m.ret, m.prc, m.shrout, d.dlret
        from crsp.msf m
        join crsp.msenames n on n.permno = m.permno and m.date between n.namedt and n.nameendt
        left join crsp.msedelist d on d.permno = m.permno
             and date_trunc('month', d.dlstdt) = date_trunc('month', m.date)
        where n.shrcd in (10, 11) and n.exchcd in (1, 2, 3) and m.date >= '1993-01-01'""",
}


def pull_wrds(d: Path) -> None:
    from hy.sources.compustat_pit import connect  # noqa: PLC0415 - WRDS only when needed

    con = None
    for name, sql in SQL.items():
        p = d / f"{name}.parquet"
        if p.exists():
            print(f"{name}: cached ({p})")
            continue
        con = con or connect()
        df = con.raw_sql(sql)
        if name == "crsp_msf":
            r, dl = df["ret"].astype(float), df["dlret"].astype(float)
            df["ret_total"] = (1 + r.fillna(0.0)) * (1 + dl.fillna(0.0)) - 1
            df.loc[r.isna() & dl.isna(), "ret_total"] = float("nan")
        df.to_parquet(p, index=False)
        print(f"{name}: {len(df):,} rows")
    if con is not None:
        con.close()


def pull_fred(d: Path) -> None:
    for sid in FRED_IDS:
        p = d / f"fred_{sid}.csv"
        if p.exists():
            print(f"{sid}: cached")
            continue
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"
        with urllib.request.urlopen(url, timeout=60) as r:  # noqa: S310 - fixed FRED host
            p.write_bytes(r.read())
        print(f"{sid}: {sum(1 for _ in p.open()) - 1} rows")


def main() -> None:
    d = out_dir()
    pull_fred(d)
    pull_wrds(d)


if __name__ == "__main__":
    main()
