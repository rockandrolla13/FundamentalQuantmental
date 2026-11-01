# Altamuro, Johnston, Pandit, and Zhang (2012 draft), "Operating Leases and Credit Assessments"

Published in Contemporary Accounting Research 31(2), pp. 551-580, 2014, DOI 10.1111/1911-3846.12033. Peer-reviewed. **We did not open the journal article.** We read the draft of November 2012, 46 pages, from the University of Pennsylvania repository (`repository.upenn.edu/accounting_papers/3`). Page numbers are PDF pages. PDF page = printed page + 1. The journal numbers may differ. Evidence class: US bank loans and credit ratings. No bond spreads.

**Added at the audit close.** The cap dropped this paper, and the citation audit found it.

## Claim
Banks and rating agencies adjust for operating leases (p. 2). Lease-adjusted ratios explain loan spreads better than reported ratios, mainly for larger lenders (p. 2). Banks do not price retail store leases in the same way (pp. 2, 22-23). Rating agencies "appear to capitalize all operating leases mechanically" (p. 2).

## Method
**Loan spread model (p. 13, eq. 1).** Log loan spread over LIBOR on the S&P credit ratios and controls. The authors compare one model with reported ratios and one with lease-adjusted ratios, by the S&P and Moody's methods. A Hausman test reads the specification, and a Vuong test reads explanatory power (p. 5).

```latex
\log LOANSPREAD = a_0 + \sum_k a_k Ratio_k + a_8 SIZE + a_9 RATED + a_{10} CREDITRATING + \gamma' Z + \eta_{ind} + \eta_{year} + e
```

Intuition: if lenders see through the footnote, then ratios that capitalize leases fit the loan spread better than ratios as reported.

**Retail split (pp. 16-17, 22-23).** Retail and wholesale firms form a separate sample, on the conjecture that store leases are closer to rental agreements.

## Data
DealScan and Compustat, 2000 to 2009. 5,812 loan deals: 2,935 with an S&P rating and 2,877 without (p. 13). For rated firms the mean rating is near BB+ (p. 18). Mean maturity 3.6 years (p. 18).

## Result
- **Sort (Table 2 Panel D, pp. 5, 18).** Median loan spread rises by 55 bp from the lowest to the highest lease quartile. That is 31% of the median spread of 175 bp.
- **Models (Table 3, p. 20).** Adjusted R-squared rises from 56.80% to 57.56% (S&P) and 57.99% (Moody's). The Hausman and Vuong p-values are 0.0001. With credit ratings in the model, R-squared moves from 65.9% to 66.1% and 66.2%, and the Vuong test is not significant (p-values 0.29 and 0.26).
- **Retail (pp. 22-23).** Inside retail firms, the spread does not rise significantly with lease use. Outside retail, the rise is 50 bp, 29% of the median. For non-rated retail firms, lease-adjusted ratios fit worse, and the unadjusted model has the better specification.
- **Ratings (p. 23).** For rated retail firms, the rating model improves from 66% to 72.6% with adjusted ratios (p-value 0.01). So agencies do not make the retail distinction.

## Limits
- Loans only. Later work finds that loans and bonds differ (see `gordon-wang-zhao-2024-operating-lease-loan-contracts.md`).
- The sort has no controls. The authors note that risk differs across cells (p. 22).
- The R-squared gains are small, as the authors say (p. 20).
- The sample ends in 2009.
- We read pp. 1-7, 13-23 in full and the summary of the tables. We did not audit the appendix.

## Section touched
`docs/methodology.md` Section 4.7, Section 7.2. `docs/framework.md` F8.

## Use for the two clocks
**What the source says.** One lease class is too coarse for a lender: retail store leases price differently.

**What our data says.** `clocks.obligation_kind` has one lease bucket, and `clock_facts.py` puts operating and finance leases together. No lease-type split exists on file.

**What we decide (our proposal, not the source's claim).** Add a retail against other split to M1.3. Report the slope on `amt_lease_after` for GICS retail issuers apart.

**Test.** M1.3 of `docs/decisions/2026-11-01-clocks-residual-timing.md`.
