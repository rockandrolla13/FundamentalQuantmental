# Lee, Lee, and Sadka (2026), "ASC 606, revenue uncertainty, and cost of debt: short-term and long-term consequences"

Review of Accounting Studies 31(2), pp. 1019-1050, DOI 10.1007/s11142-026-09936-5. Peer-reviewed, open access. We read the publisher PDF, 33 pages. Page numbers are PDF pages. Journal page = PDF page + 1018. Evidence class: US syndicated loans. No bond spreads.

**Added at the audit close.** The screen graded this paper 3, and the cap dropped it. An earlier automated fetch hit a bot check. A plain request on 2026-11-01 returned the open access file. We did not bypass any check.

## Claim
After ASC 606, firms with a material impact show more revenue uncertainty (p. 1). Their cost of debt rises by 6%, or 22 bp, and lenders use fewer earnings covenants (pp. 3, 17). The cost effect fades over time, and the uncertainty stays (pp. 1, 4, 21).

## Method
**Difference in differences (pp. 10-12).** The treatment group is firms in the Russell 3000 that disclose a material impact of ASC 606 on accounting policy, from AuditAnalytics. The rest form the control group.

```latex
\log CostDebt_{i,l,t} = a_i + \eta_{yq} + b\,ASC606_{i,t} + \gamma' X_{i,t} + \delta' L_{l} + e_{i,l,t}
```

Intuition: compare new loans of firms that the standard moved with new loans of firms that it did not, before and after adoption. `CostDebt` is the all-in drawn spread in Dealscan.

**Windows (p. 11).** 2016 to 2019 for the short test. 2014 to 2021 for the long test.

## Data
Dealscan loans matched to Compustat, 2,154 loan observations in the short test and 3,575 in the long test (pp. 18, 22). Mean cost 206 bp (p. 12). Median firm assets near $5 billion (p. 12). About 60% of firms count as treated (p. 12).

## Result
- **Cost of debt (Table 4, p. 18).** `ASC606` on log cost: 0.0596 (se 0.0258). On raw cost: 21.634 bp (se 8.098).
- **Covenants (Table 3, p. 17).** Earnings covenants: -0.1080 (se 0.0405). Total covenants: -0.1052 (se 0.0456).
- **Long run (Table 7, p. 22).** In 2018 to 2019, log cost 0.0525 (se 0.0236) and raw cost 17.94 bp (se 6.89). In 2020 to 2021, log cost 0.0133 (se 0.0526) and raw cost 6.21 bp (se 8.06). Revenue uncertainty stays up. Columns 4 and 5 read 0.0522 (se 0.0237) and 0.0027 (se 0.0011) in 2018 to 2019, then 0.1813 (se 0.0377) and 0.0047 (se 0.0019) in 2020 to 2021.
- **R-squared from the treatment term (Table 4, p. 18).** 0.0006 and 0.0016.

## Limits
- Loans, not bonds. The paper holds no RPO level or RPO timing test. It tests adoption, not contract duration.
- Firm size leans larger than a typical high yield issuer (p. 12).
- The treatment is a disclosed material impact, so firms sort into it by business model.
- We read pp. 1-6, 10-12, 17-18, 21-23.

## Section touched
`docs/methodology.md` Section 4.7 (revenue clock).

## Use for the two clocks
**What the source says.** ASC 606 is a dated break in revenue reporting, and lenders price it for about two years.

**What our data says.** RPO data starts in 2018, at this break (`docs/decisions/2026-10-22-alpha-backtest-design.md`). So the on-file revenue clock sample starts inside the window that this paper finds abnormal.

**What we decide (our proposal, not the source's claim).** Add `rpo_regime`, and report RPO tests with and without 2018 and 2019. A clock result that lives only in those two years reads as an adoption effect.

**Test.** M1.4 and M1.8 of `docs/decisions/2026-11-01-clocks-residual-timing.md` report this cut.
