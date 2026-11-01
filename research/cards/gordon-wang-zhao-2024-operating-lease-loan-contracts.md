# Gordon, Wang, and Zhao (2024 draft), "Hidden in Plain Sight: Operating Lease Accounting and Private Loan Contracts"

Working paper, DOI of the SSRN record 10.2139/ssrn.4582752. **Not peer reviewed in the copy we read.** We read the file dated January 22, 2024 from the Columbia Accounting Design Project page (57 pages). Page numbers are PDF pages. PDF page = printed page + 1. Evidence class: US bank loans, plus a US bond issue test that pools ratings.

**Added at the audit close.** The screen graded this paper 3, and the cap dropped it.

## Claim
Lease expense explains the part of loan spreads that comes from lease risk, and capitalized lease liabilities add nothing (pp. 1, 24-25). ASC 842 does not change this (p. 25). Bond investors behave differently: they "place more weight on capitalized operating leases than lease expenses when setting bond prices" (p. 1).

## Method
**Spread regression (p. 19).** `SPREAD` is the log all-in drawn spread of a loan tranche. `LEASE_EXP` is lease expense over total assets. `OLEASE_LIAB` is the imputed operating lease liability over total assets. `CLEASE` is capital leases over total assets.

```latex
SPREAD_{ijt} = a + b_1 LEASE\_EXP_{it} + b_2 OLEASE\_LIAB_{it} + b_3 CLEASE_{it} + \gamma' X_{it} + \delta' L_{ijt} + \eta_t + \epsilon_{ijt}
```

Intuition: put the income statement measure and the balance sheet measure in one regression, and read which one carries the price of lease risk.

**Bond test (p. 32).** The same model, with the log new-issue bond spread from SDC, bond amount, and months to maturity.

## Data
- Loans: Refinitiv Dealscan matched to Compustat, 2010 to 2021. 9,860 loan observations from 5,396 tranches and 1,462 firms (pp. 18-19). Mean spread 221 bp (p. 21).
- Bonds: public issues from SDC by listed firms, 2010 to 2021. 4,553 issues. Mean spread 206 bp, median 147 bp, mean maturity 138 months (Table 7 Panel A, p. 55).
- The bond table has no rating split.

## Result
**Loans (Table 3, p. 48).** Without firm effects: `OLEASE_LIAB` alone 0.090 (p 0.472). `LEASE_EXP` alone 0.829 (p 0.013). Both: 1.406 (p 0.003) on expense and -0.389 (p 0.036) on the liability. With firm effects: 0.458 (p 0.118), 0.960 (p 0.037), and 0.767 (p 0.057) with 0.309 (p 0.256).

**Bonds (Table 7 Panel B, p. 55).**

| Column | `LEASE_EXP` | `OLEASE_LIAB` | `POST` x `LEASE_EXP` | `POST` x `OLEASE_LIAB` |
| --- | --- | --- | --- | --- |
| 1 | | 4.130 (p 0.000) | | |
| 2 | 2.569 (p 0.020) | | | |
| 3 | 1.547 (p 0.155) | 3.396 (p 0.001) | | |
| 4 | | 4.027 (p 0.000) | | 0.585 (p 0.656) |
| 5 | 3.418 (p 0.016) | | -3.011 (p 0.100) | |
| 6 | 2.394 (p 0.103) | 2.877 (p 0.003) | -2.566 (p 0.169) | 1.597 (p 0.253) |

Leverage is 0.91 to 0.93 in these columns, each with p 0.000 (p. 55).

**Debt after ASC 842 (p. 26, note 19).** Firms with more lease liability before adoption raise non-lease debt more after it. The coefficient is 0.501, significant at 1%.

**Contract terms (p. 12).** Fewer than 10 percent of contracts in the sample treat operating leases as debt.

## Limits
- This is a conference draft. A later version may differ.
- The bond test is a side test, at issue, with no high yield column and no secondary market price.
- `OLEASE_LIAB` is imputed before ASC 842, and the authors say that the discount rate drives part of its sign in loans (p. 24).
- The bond sample holds firms that issue public bonds, so it leans to large firms. Mean log size is 10.0 (p. 55).

## Section touched
`docs/methodology.md` Section 4.7, Section 7.2. `docs/framework.md` F8.

## Use for the two clocks
**What the source says.** At equal leverage, a larger lease liability goes with a wider new-issue bond spread. In loans, the expense carries the price, and the liability does not.

**What our data says.** The share on file reads -2.07 (t -2.4), with no leverage control. `hy/sources/schedules.py` reads lease ladders only from ASC 842 tags, so no lease field exists on file for earlier months.

**What we decide (our proposal, not the source's claim).**
1. Read lease amount and first-year rent side by side in M1.2, because the source separates them.
2. Do not carry the loan result to bonds. The source itself shows that the two markets differ.

**Test.** M1.2 and M1.7 of `docs/decisions/2026-11-01-clocks-residual-timing.md`.
