# Palazzo and Yang (2019), "Spike in 2019Q1 Leverage Ratios: The Impact of Operating Leases"

FEDS Notes, Board of Governors of the Federal Reserve System, December 13, 2019, DOI 10.17016/2380-7172.2464, at https://www.federalreserve.gov/econres/notes/feds-notes/spike-in-2019Q1-leverage-ratios-20191213.html. Staff note, not peer reviewed. We read the full web page. It has no page numbers, so we cite sections and tables. Evidence class: US listed non-financial firms. No bond spreads.

**Added at the audit close.** The screen graded this note 2, and the cap dropped it.

## Claim
Compustat leverage jumps in 2019:Q1 because operating leases reach the balance sheet (Section 1). Net debt issuance explains little of the jump (Section 1).

## Method
**Change in debt (Section 4.1, Table 2).** The change in debt from 2018:Q4 to 2019:Q1, over 2018:Q4 assets, on net debt issuance and the XBRL operating lease liability.

```latex
\frac{\Delta Debt_{i}}{Assets_{i,18Q4}} = a + b_1 \frac{NetIssuance_{i}}{Assets_{i,18Q4}} + b_2 \frac{OLL_{i}}{Assets_{i,18Q4}} + b_3 \Big(\frac{OLL_{i}}{Assets_{i,18Q4}}\Big)^2 + e_i
```

Intuition: if reported debt absorbs the lease liability one for one, `b_2` sits near 1, and the constant falls to zero.

**Lease measure (Section 3).** XBRL tags for operating lease liability, current and non-current. The Compustat rent schedule `XRENT` and `MRC1` to `MRC5` and `MRCTA` serve as a check (Appendix). The authors call a discounted schedule fragile (Section 3).

## Data
US non-financial firms on the NYSE, NASDAQ, or AMEX. 2,964 firms in 2019:Q1, and 1,858 with XBRL lease data (Sections 3, 4).

## Result
- **Size (Section 1).** Aggregate leverage rises by about 1.8 points, and median leverage by about 3.7 points.
- **Debt (Table 2).** The lease coefficient is 1.08 (se 0.06) in column 3, with the square -0.91 (se 0.09). It is 1.02 (se 0.04) on all firms in column 5. R-squared is 0.74 with net issuance in column 4.
- **Attribution (Section 4.2).** For the average firm, 69% of the change in the leverage ratio comes from leases, and 8% from net debt. For the median firm, 76% and 0%.
- **Firms with no lease data (Table 1).** They show little change in median leverage.
- **Adjusted ratio (Section 1).** After removal of leases, leverage rises by 0.3 points at aggregate and 0.8 points at the median.

## Limits
- One quarter. It covers firms that adopted in 2019:Q1.
- The debt field is the Compustat field that the authors use. We did not open the Compustat item definitions, so the step in `dlcq` and `dlttq` is an inference from this table and from Kallen (p. 9).
- No price, no spread, and no high yield split.

## Section touched
`docs/methodology.md` Section 4.3, Section 4.7. `docs/framework.md` F8. `hy/sources/compustat_pit.py`, `hy/sources/trace_panel.py`, `hy/peers.py`, `hy/state.py`.

## Use for the two clocks
**What the source says.** Reported debt absorbed the lease liability near one for one at adoption.

**What our data says.** `hy/sources/compustat_pit.py` builds panel debt from `dlcq` and `dlttq`. Panel `leverage` is that debt over LTM EBITDA (`hy/sources/trace_panel.py`). The implied class cut-offs were fitted on 2008 to 2017, before adoption (`2026-10-22-esp-peer-groups`). `hy.state.lev_lease_adj` adds 8 times rent to debt. So three on-file fields may break at adoption:

1. Panel `leverage` may step up for lease-heavy issuers.
2. The implied class may move those issuers to a weaker cell, with no change in the business.
3. `lev_lease_adj` on panel debt may count leases twice after adoption. Framework F8 uses the balance-sheet liability after 2018 and 8 times rent before, so it needs a debt field with no leases in it.

No file records whether this happens or how large it is.

**What we decide (our proposal, not the source's claim).**
1. Add `lev_ex_lease`: debt less the XBRL operating lease liability after adoption, over EBITDA. Use it as the leverage control in Method 2, so one field holds across the regime.
2. Print the mean change in panel `leverage` at each issuer's first ASC 842 filing, against issuers with no leases, before any test reads a class after 2019.

**Test.** That print comes first. If the step is near zero, the three risks above fall away.
