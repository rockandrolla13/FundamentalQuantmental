# S&P Global Ratings (2019), "Corporate Methodology: Ratios And Adjustments"

S&P Global Ratings criteria, published 1 April 2019, effective immediately. Rating agency methodology. We read the public copy on the Maalot site, 13 pages. Citations below give the paragraph and the PDF page. The related guidance article of the same date holds the detailed lease mechanics, and we did not open it. Evidence class: agency judgement, no sample statistics.

## Claim
S&P treats some transactions as debt-like, whatever the filer reports (para. 7, p. 4). Leases are debt-like. Future commitments to buy goods or services that the firm has not received are not debt-like, because they are executory contracts (para. 10, p. 5). The agency expects these updated criteria to cause negligible rating changes, none by more than one notch (para. 3, p. 1).

## Method
**Adjusted debt principle (para. 9, p. 5).** S&P adds three groups to reported debt:
1. Incurred liabilities with no future operating benefit, such as underfunded retiree benefits and asset retirement obligations.
2. Commitments on or off the balance sheet to buy or use long-life assets, such as leases, where the benefits of ownership accrue to the company.
3. Accelerated asset monetisation in the place of borrowing, such as securitisation and factoring.

**The line (para. 10, p. 5).** "We do not consider a company's future commitments to purchase goods or services it has not received as akin to debt. This is because these are executory contracts, which means a counterparty must still perform an action and the benefits of ownership have yet to accrue to the company."

**Leases (para. 26, p. 7).** S&P adjusts debt, earnings, cash flow and interest. It may raise lease liabilities if remaining lease terms look "artificially short relative to the expected use of the lease asset".

**Cash (paras. 23-25, p. 7).** Adjusted debt is net of accessible cash. S&P does not net cash where weaker business characteristics or ownership by financial sponsors do not support it.

**Trade credit (para. 11, p. 5).** Payables are out of debt, unless a firm defers payment beyond the term customary for its supply chain.

**Ratios (p. 4).** Core ratios are FFO to debt and debt to EBITDA. Supplementary ratios include CFO to debt, FOCF to debt and DCF to debt.

```latex
\text{AdjDebt} = \text{Debt} + \text{Leases} + \text{PRB}_{\text{after tax}} + \text{ARO} + \text{Securitised receivables} - \text{AccessibleCash}
```

Our summary of paras. 9 and 22-32, not a formula from the text. Intuition: debt is every prior call on cash for an asset whose benefit the firm already has.

## Data
None. The document states agency principles.

## Result
- Routine adjustments apply to all companies where material (para. 22, p. 6). Leases are on that list.
- Purchase commitments are not on that list, and para. 10 excludes them.
- The criteria do not apply to project finance entities and corporate securitisations (para. 2, p. 1).
- Situational adjustments are rare (para. 37, p. 9). They cover litigation, multi-employer pensions and similar items (para. 39, p. 9).

## Limits
- A statement of method, not a test. It does not show that the adjustments improve default prediction.
- Sector-specific adjustments sit in other criteria and we did not open them (para. 40, p. 9).
- The text gives no number for capitalising a lease. The guidance article may give one.
- The executory argument in para. 10 also fits a lease in law (see `becker-josephson-xu-2023-executory-contract-rejection.md`). S&P draws its line on whether the benefit has begun to accrue, not on the legal class.
- The copy sits on the Maalot site, not on the S&P site. The text carries the S&P header and date.

## Section touched
`docs/methodology.md` Section 4.3 (`lev_lease_adj`, `debt_adj`) and Section 4.7 (classes in `O_t`). `docs/framework.md` F5 (going-concern view). `hy/clocks.py` (`obligation_kind`).

## Use for the two clocks
**What the source says.** Rent is a debt-like claim. A purchase commitment is not. A rating already reflects this split.

**What the data says.** `clocks.obligation_kind` draws its line elsewhere. It files debt as refinance and files rent and purchases together as recontract. Section 4.7 finds the wrong sign on that combined bucket (-2.07, t -2.4). The test has no rating and no leverage control (`renewal_split_test` in `scripts/backtest_clocks.py`).

**What we decide (our proposal, not the source's claim).**
1. Use three classes on the cost clock: funded debt, leases, and purchase commitments. Do not add purchases to any leverage-like measure such as E5 at face.
2. Control for lease-adjusted leverage in every clock regression. Use the Section 4.3 field `lev_lease_adj`, because plain leverage leaves rent out and a share with rent in it then proxies for the missing part.
3. Report the test with and without rating dummies. A rating already holds the lease adjustment, so the coefficient with ratings measures only what the agencies miss.
4. For a sponsor-owned issuer, do not net cash in the clock's cover ratios. This follows para. 25.
5. Test. Refit the split regression with the three classes and `lev_lease_adj`. The S&P line passes when the lease coefficient is above the purchase coefficient, with a difference t above 2 (Our choice, v0).
