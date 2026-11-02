# Kallen (2026), "Hidden Leverage in Nonfinancial Corporations"

International Finance Discussion Papers 1441, Federal Reserve Board, July 2026, DOI 10.17016/IFDP.2026.1441. Working paper. We read the Board file, https://www.federalreserve.gov/econres/ifdp/files/ifdp1441.pdf, 49 pages. Page numbers are PDF pages. PDF page = printed page + 1. Evidence class: US listed firms. No bond spreads.

**Added at the audit close.** The screen graded this paper 3, and the cap dropped it.

## Claim
Before 2019, operating leases are one form of debt off the balance sheet (p. 2). Firms with substantial use of hidden debt are smaller, report lower leverage, and are more often rated high yield or not rated (pp. 2, 4, 25). When ASC 842 reveals the leases, affected firms cut capital spending by 25% and research by 14%, and they raise reported non-lease debt (pp. 2, 28, 31).

## Method
**Lease liability before ASC 842 (pp. 8-9).** The author takes the present value of the Compustat lease schedule, `MRC1` to `MRC5` and `MRCTA`, at Moody's Baa yield. Payments beyond five years amortize over years 6 to 10.

```latex
L^{PV}_{i,t} = \sum_{\tau=1}^{5} \frac{MRC\tau_{i,t}}{(1+y^{Baa}_t)^{\tau}} + \sum_{\tau=6}^{10} \frac{MRCTA_{i,t}/5}{(1+y^{Baa}_t)^{\tau}}
```

Intuition: turn the footnote schedule into a debt-like number with a market discount rate. This formula is our writing of the text on pp. 8-9. The paper states it in words.

**Companion note.** `palazzo-yang-2019-leverage-operating-leases.md` measures the step in reported debt in 2019:Q1.

**Dates (p. 9).** "Under ASC 842, operating leases should be brought onto firms' balance sheets in fiscal year 2019 for firms whose fiscal years end in December, and in 2020 for all other firms."

**Non-lease debt (p. 9).** Total debt less capital leases, and less the present value of operating leases after they reach the balance sheet.

**Revelation test (pp. 26-27).** A firm is flagged when leased PPE over gross PPE jumps by more than three standard deviations in 2019 or 2020, or when reported leverage jumps by more than two standard deviations and the firm had substantial leases. The sample runs from 2011 to 2024.

**Intra-period debt (pp. 8-9, 17).** Interest expense over prior debt gives an implied rate. A gap between actual and predicted interest flags debt repaid before the period end.

## Data
Compustat North America, annual 1995 to 2024, quarterly from 1980 (p. 11). Non-financial firms that use GAAP.

## Result
- **Shares (Table 2, p. 17).** 29.2% of firms use substantial operating leases over 1995 to 2018. 12.0% show suspicious interest. 8.2% show both.
- **Who (Table 6, p. 25, logit).** S&P high yield rating 0.874 (se 0.186). No S&P rating 1.025 (se 0.144). Non-lease leverage -3.402 (se 0.501).
- **Balance sheet impact (Table 7, p. 27).** 47.5% had substantial leases at some point in 2011 to 2018. 17.2% show a substantial balance sheet impact.
- **Investment (p. 28).** Capital spending falls by 25.2%, and research by 13.7%, relative to the pre-revelation mean.
- **Debt (Table 10, p. 32).** Hidden debt x post on non-lease leverage: 0.027 (se 0.012) and 0.030 (se 0.013). Hidden debt alone: -0.038 (se 0.011). Implied interest rate: -1.568 (se 0.274) and -2.119 (se 0.287).

## Limits
- No bond price, no spread, and no default outcome.
- The author reads "hidden" debt as a choice to deceive (p. 2). Other papers find that lenders already see leases (p. 6). See `altamuro-johnston-pandit-zhang-2012-operating-leases-credit.md`.
- The flags use fixed lines of two and three standard deviations. The source gives no test of these lines.
- Discussion paper. "Preliminary materials" by the series note (p. 1).
- We read pp. 1-11, 17, 25-32. We did not audit the appendix.

## Section touched
`docs/methodology.md` Section 4.7. `hy/sources/schedules.py`, `hy/sources/clock_facts.py`. `docs/framework.md` F8.

## Use for the two clocks
**What the source says.** ASC 842 sets a dated break in reported lease debt. Lease-heavy firms report less non-lease debt before it and more after it. The Compustat schedule `MRC1` to `MRC5` gives a route to the earlier years.

**What our data says.** `FAMILIES` in `hy/sources/schedules.py` reads only `LesseeOperatingLeaseLiabilityPayments*` and `FinanceLeaseLiabilityPayments*`. `keep_tag` in `hy/sources/clock_facts.py` drops other stems. So the recontract share in the 2018 to 2026 test holds no operating rent before each issuer's first ASC 842 filing. `rent_1y` is 0 there. The count of affected issuer-months is not on file.

**What we decide (our proposal, not the source's claim).**
1. Read `mrc1` to `mrc5` and the older lease tags up to the first ASC 842 filing. Add `lease_regime`.
2. Rerun the split test on months after adoption only, as hypothesis 9 of the review.
3. Use the present value of the prior schedule as the expected liability in M1.7.

**Test.** M1.7 and hypothesis 9 in `research/notes/clocks-systematic-review.md`.
