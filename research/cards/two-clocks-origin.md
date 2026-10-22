# Origin of the two clocks: fixed obligations against contracted revenue

Lineage card. Written 22 October 2026. It covers many sources, not one. Each source below was opened. Quotes are verbatim from the opened text.

## Question
Where does the idea come from: measure the time profile of fixed obligations (the cost clock) against the time profile of contracted revenue (the revenue clock), and treat the gap as credit risk? Which prior work states it first, and which states it best?

## Short answer
- The measure is old. Bank gap analysis put both sides of a balance sheet into time buckets, and duration gap reduced them to one number of years (Kaufman 1984). Our `D_O - D_R` is that formula applied to a borrower's charges and contracts instead of a bank's assets and deposits.
- The credit framing is also old. Bank supervisors grade project finance by whether the off-take contract outlasts the debt (Basel slotting criteria, 2003 text). A rating agency named the same risk for data centres in 2024 (Morningstar DBRS).
- The closest precedent for a corporate high yield issuer is WeWork (2019 S-1). It disclosed both clocks: 15-year leases and $47.2bn of lease payments against month-to-month members and $4.0bn of committed revenue backlog.
- Radhakrishnan (2026) applies the idea to AI capacity providers. Oracle's own 10-K (June 2026) already stated the mismatch. A Bisnow report (September 2025) quotes a lawyer who called it "a WeWork mismatch".
- Our model is a re-statement, not a new idea. What it adds is a set of scalar features from public filings for a non-financial corporate issuer: uncommenced leases and purchase commitments on the same grid as RPO, `breakeven_margin`, and the renewal-dependent amount in years of EBITDA.

---

## Source 1. Kaufman (1984), bank duration gap and maturity gap

George G. Kaufman, "Measuring and managing interest rate risk: a primer", *Economic Perspectives*, Federal Reserve Bank of Chicago, vol. 8, January/February 1984, pp. 16-29. URL: https://www.chicagofed.org/digital_assets/publications/economic_perspectives/1984/ep_jan_feb1984_part2_kaufman.pdf (scanned PDF, read by OCR).

- **Claim.** "the interest rate risk of a target account is related to the difference, or gap, between the average duration of the assets of the institution and the average duration of the deposits." The duration gap for the capital-to-asset ratio is `Da - Dp`. For capital it is `Da - w Dp`, with `w = P/A`.
- **Method.** Macaulay duration of each side, weighted by market value. The paper also describes the older "maturity gap" method: classify each account "by their terms to maturity or to first permissible repricing", group them into "maturity-period buckets", and compute "net balances, or maturity gaps in dollars" per bucket.
- **Data.** A worked example bank balance sheet. No empirical sample.
- **Result.** In the example, the duration gap is 1.9 years for capital and 1.7 years for the capital-to-asset ratio. The paper warns that bucket gaps "cannot be simply summed" and that "the gap in any one bucket ... is unlikely to be representative". One summary number in years is the answer it offers.
- **Limits.** The risk factor is the interest rate, not renewal. The bank side has no renewal decision by a customer. Duration is present-value weighted. A footnote credits G. O. Bierwag for an economic-income gap and Alden Toevs for a net-income gap (Federal Reserve Bank of San Francisco, *Economic Review*, Spring 1983). I did not open the Toevs paper or Bierwag and Kaufman (1985, *Financial Analysts Journal*).
- **Section touched.** Methodology 4.7 (`duration_gap`, the annual grid). Framework S6.

## Source 2. Basel Committee slotting criteria for specialised lending (2003 text)

"Annex 4: Supervisory Slotting Criteria for Specialised Lending", printed pages 176-184, attached to the US agencies' Basel II release of 30 April 2003. URL: https://www.federalreserve.gov/boarddocs/press/bcreg/2003/20030430/attachment9.pdf. The UK FCA carries the same criteria as BIPRU 4 Annex 1 (I opened only its index page).

- **Claim.** Contract tenor against debt tenor is a credit grade. Project finance, off-take risk, take-or-pay contract: Strong has "tenor of contract comfortably exceeds the maturity of the debt". Good: "tenor of contract exceeds the maturity of the debt". Satisfactory: "tenor of contract generally matches the maturity of the debt". Weak: "tenor of contract does not exceed the maturity of the debt".
- **Method.** A four-grade supervisory scorecard. Other rows apply the same logic: "Duration of the credit compared to the duration of the project", graded from "Useful life of the project significantly exceeds tenor of the loan" (Strong) to "may not exceed tenor of the loan" (Weak). Income-producing real estate grades lease length, scattered lease maturities, and "tenant retention upon lease expiration". Object finance grades the "capability to re-market asset when it comes off-lease".
- **Data.** None. Supervisory judgement.
- **Result.** The gap between the contract clock and the debt clock sets a risk weight. A contract that ends before the debt is the weakest grade.
- **Limits.** Grades, not numbers. It treats one project and one debt, not a corporate with many leases and many contracts. It looks only at the end date, not the full time profile.
- **Section touched.** Methodology 4.7 (`revenue_runoff`, `renewal_dependent_share`). Framework S6.

## Source 3. Morningstar DBRS (2024), "Emerging Credit Risks in Project Finance Transactions"

Commentary, 1 May 2024. Authors: Biao Gong and Arthi Sambasivan. URL: https://www.ipfa.org/wp-content/uploads/2024/09/Emerging-Credit-Risk-in-Project-Finance.pdf

- **Claim.** "We have seen an increase in refinancing and/or recontracting risk in recent years, as partially amortizing debt and shorter contract terms have become more prevalent in project finance transactions. These risks are especially common within the project transactions to finance data centers and other digital infrastructure assets." It adds: "Refinancing and recontracting risks are intertwined but distinctive concepts."
- **Method.** A three-type table. Type 1: "Partially amortizing debt with significant remaining revenue contractual tail" (refinancing risk only, "Managable"). Type 2: "debt maturity coinciding with contract renewal" (both risks, "Case by Case"). Type 3: "Fully amortizing debt with exposure to recontracting/merchant risk" (recontracting only, "Case by Case").
- **Data.** Agency experience. No sample statistics.
- **Result.** Recontracting risk "require[s] case-by-case analysis that considers the assets' essentiality, replaceability, and market competitiveness in the future". A hyperscale data centre that is essential to the anchor tenant "will have a much better likelihood of having its contract renewed than less competitive co-location facilities". The agency "may use additional credit metrics such as project loan coverage ratios" to size the effect.
- **Limits.** Project finance, not unsecured corporate debt. No formula. It does not treat leases the borrower pays as a third clock.
- **Section touched.** Methodology 4.7 (the split between debt and lease obligations, the renewal downside in rule 4). Framework S6.

## Source 4. WeWork Companies Inc., Form S-1/A, 4 September 2019

URL: https://www.sec.gov/Archives/edgar/data/1533523/000119312519236798/d781982ds1a.htm (amendment to the S-1 of 14 August 2019. I read the amendment.).

- **Claim.** "Substantially all of our leases with our landlords are for terms that are significantly longer than the terms of our membership agreements with our members. The average length of the initial term of our U.S. leases is approximately 15 years, and our future undiscounted minimum lease cost payment obligations under signed operating and finance leases was $47.2 billion as of June 30, 2019. If we are unable to replace members who may terminate their membership agreements with us, our cash flows and ability to make payments under our lease agreements with our landlords may be adversely affected."
- **Method.** Issuer risk factor plus two disclosed quantities. "Committed revenue backlog" is defined as "total non-cancelable contractual commitments, net of discounts, remaining under agreements entered into as of such date".
- **Data.** At 30 June 2019: committed revenue backlog $4.0bn, run-rate revenue $3.3bn. Weighted average remaining lease term 14 years (operating) and 11 years (finance). Many members "may terminate their membership agreements with us at any time upon as little notice as one calendar month."
- **Result.** Both clocks in one filing: about $47bn of fixed charges over 14 to 15 years against about $4bn of contracted revenue. WeWork filed for Chapter 11 in November 2023 (common knowledge. I did not open the petition.).
- **Limits.** One issuer. The filing states the mismatch but offers no measure of it.
- **Section touched.** Methodology 4.7 (a natural out-of-sample test case). Framework S6.

## Source 5. Oracle Corporation, Form 10-K for the year to 31 May 2026, filed 22 June 2026

URL: https://www.sec.gov/Archives/edgar/data/1341439/000119312526277521/orcl-20260531.htm (risk factors, page 18).

- **Claim.** "the terms, renewal options and pricing adjustments in our long-term data center leases typically do not align with the duration and pricing of customer contracts, and if customers do not renew their contracts, we may be unable to re-lease, repurpose or assign such capacity on acceptable terms, if at all." Also: "if we overestimate customer demand or any of our key customers are unable to pay or otherwise perform under their contracts with us, we could be locked into multi-year commitments for excess data center space and related capital expenditures, as well as associated financings, without receiving corresponding revenue."
- **Method.** Issuer risk factor.
- **Data.** None in the passage. The lease figures are in the notes.
- **Result.** The issuer names the mismatch, renewal, and re-lease risk before Radhakrishnan (October 2026).
- **Limits.** Boilerplate risk factor. No quantity.
- **Section touched.** Methodology 4.7. Framework S6.

## Source 6. CoreWeave, Form S-1, 3 March 2025

URL: https://www.sec.gov/Archives/edgar/data/1769628/000119312525044231/d899798ds1.htm

- **Claim.** "many of the leases we have entered into for third-party data centers have multi-year terms and fixed capacity. If we do not accurately anticipate the data center capacity required by our customers ... we would incur additional costs due to leasing more capacity than is used and paid for by our customers".
- **Method.** Issuer risk factor.
- **Result.** It names the volume risk of fixed leases. I did not find, in this filing, a sentence that compares lease term with contract term.
- **Limits.** Volume framing, not a timing framing.
- **Section touched.** Methodology 4.7.

## Source 7. Bisnow (2025), neocloud lease risk for data centre owners

Dan Rabb, "Cloud Providers Like CoreWeave See 'Unrivaled' Growth But Present Risks For Data Center Firms", Bisnow, 21 September 2025. URL: https://www.bisnow.com/national/news/data-center/neoclouds-like-coreweave-see-unrivaled-growth-but-risks-keep-data-center-firms-wary-131051

- **Claim.** "While traditional data center leases span 10 to 15 years, neocloud GPU contracts are typically just two to five years." Jeffrey Moerdler (Mintz), speaking in July 2025: "I'm worried that there's a mismatch between their leasing space on a 10 to 15-year lease," and "It's kind of a WeWork mismatch."
- **Method.** Trade press, conference remarks.
- **Result.** The neocloud form of the idea, with the WeWork link, is in print more than a year before Radhakrishnan (2026).
- **Limits.** Landlord view, not the bondholder view. No numbers from filings.
- **Section touched.** Methodology 4.7.

## Source 8. He and Xiong (2012), rollover risk and credit risk

Zhiguo He and Wei Xiong, "Rollover Risk and Credit Risk", NBER Working Paper 15653, January 2010. Published in *Journal of Finance* 67(2), 2012. URL: https://nber.org/papers/w15653 (I opened the abstract page only).

- **Claim.** "This paper models a firm's rollover risk generated by conflict of interest between debt and equity holders." Worse market liquidity and shorter debt maturity raise the default threshold.
- **Method.** Structural model in the Leland (1994) and Leland and Toft (1996) tradition.
- **Result.** When debt must roll over, the firm defaults earlier than its fundamentals alone imply.
- **Limits.** The mismatch here is debt maturity against asset life. It has no contract clock. It is the theory for the refinancing half of our gap, not the recontracting half.
- **Section touched.** Methodology 4.7 (why the debt part of `O` is a separate risk). Methodology 7 (spread sign).

## Source 9. Dechow, Sloan, and Soliman (2004), implied equity duration

"Implied Equity Duration: A New Measure of Equity Risk", *Review of Accounting Studies* 9(2), 197-228. URL: https://ideas.repec.org/a/spr/reaccs/v9y2004i2d10.1023_brast.0000028186.44328.3f.html (abstract page only).

- **Claim.** "Duration is an important and well-established risk characteristic for fixed income securities." The authors build a duration for a firm's cash flows from accounting data.
- **Result.** Equity duration moves with stock volatility and beta.
- **Limits.** One duration for the whole firm, not two clocks. It shows that Macaulay duration of non-financial cash flows from filings has a precedent.
- **Section touched.** Methodology 4.7 (`D_O`, `D_R`).

## Sources searched and not opened
- Lease capitalisation in credit: Altamuro, Johnston, Pandit, and Zhang (2014), "Operating Leases and Credit Assessments", *Contemporary Accounting Research* 31(2), 551-580. I opened only the citation page. It had no abstract. Moody's and S&P lease adjustment methodologies: not found in open form.
- Moody's, S&P, and Fitch project finance criteria on contract tails: not found in open form. Fitch rating actions (Kleen Energy, 2011) appeared in search but I did not open them.
- Aircraft lessors and shipping: SMBC Aviation Capital reports lease term against borrowing term, but the page failed to load (HTTP 502). No agency methodology text opened.
- S&P "non-coterminous" Section 8 housing bond criteria (Bond Buyer, 20 June 2003, opened): bonds whose subsidy contract "is scheduled to expire before the maturity date of the bonds". A news report of criteria, not the criteria.
- Diamond (1991), Leland (1994), Macaulay (1938), Gatti, Esty: not opened for this card.

---

## Lineage

### What the sources say
1. **Method, 1970s to 1984.** Banks bucket both sides of the balance sheet by time and take the net per bucket (maturity gap). Duration gap reduces both sides to one number of years (Kaufman 1984, citing Bierwag and Toevs).
2. **Credit framing, 2001 to 2003 and older.** Project finance and supervisory criteria grade a deal by whether the contract outlasts the debt (Basel slotting). Rating agencies apply the same logic to subsidy contracts that end before bonds (S&P, 2003).
3. **Corporate high yield case, 2019.** WeWork disclosed both clocks in its S-1. It later failed.
4. **Data centres, 2024 to 2026.** DBRS (2024) flags recontracting risk in data-centre project finance. Bisnow (2025) quotes "a WeWork mismatch" for neoclouds. Oracle's 10-K (2026) states the mismatch as a risk factor. Radhakrishnan (2026) frames it for unsecured neocloud debt.

### What the data says
- We have one confirmed case in the repo (CoreWeave, `scripts/clock_case.py`). We have no test yet that the features predict spread or default.
- WeWork gives an outside case with a known outcome. Its S-1 has every input the model needs: lease ladder, backlog, run-rate revenue.

### What we decide
- Cite Kaufman (1984) for the formula, Basel slotting (2003 text) for the credit grade, DBRS (2024) for the split of refinancing and recontracting, and WeWork (2019) as the precedent case. Keep Radhakrishnan (2026) as the source for the AI capacity application.
- Call the model a re-statement. Do not claim the idea is new.

### What our model borrows
- The time grid and net per bucket (maturity gap). Our `max_cum_shortfall` is a cumulative maturity gap.
- One summary in years (duration gap). Our `D_O` and `D_R` are cash-weighted centres with no discount. That is the weighted average life of structured finance plus half a year, not the present-value Macaulay duration of Kaufman.
- The rule that a contract which ends before the obligation is weak (slotting, DBRS).

### What our model adds
- Three obligation types on one grid: leases in force, signed leases not yet commenced, and purchase commitments, beside debt and interest. The precedents look at one debt against one contract.
- RPO from the filing as the revenue clock, on the filer's own timetable.
- Scalar features that a spread model can use: `breakeven_margin`, `coverage_contracted`, and the renewal-dependent amount in years of EBITDA.
- Customer concentration as the renewal downside.

### What our model lacks
- **Refinancing against recontracting.** DBRS treats them as distinct. `renewal_dependent_share` adds debt principal and rent into one number. Debt can roll over in a capital market. A lease cannot be cancelled. A contract must be re-signed with a customer.
- **Re-marketability of the asset.** Slotting and DBRS both grade the chance that someone else takes the capacity ("essentiality, replaceability", "capability to re-market"). Our model uses only customer shares.
- **Discounting.** The centres carry no time value. For long leases this overstates `D_O` against a present-value gap. Report both.

---

## What this changes in methodology 4.7

1. **Recommended change: split the renewal-dependent amount by clock.** Add `refi_dependent_share` (debt principal due after `revenue_runoff`) and `recontract_dependent_share` (rent and purchase commitments due after `revenue_runoff`). Keep `renewal_dependent_share` as their sum. Source: DBRS (2024) types 1 to 3. Test: in the spread regression of the decision page `2026-10-22-duration-mismatch`, the recontract part has a larger positive coefficient than the refinance part.
2. **Add a citation line.** State that `duration_gap` is the bank duration gap of Kaufman (1984) applied to charges and contracts, and that the centres are undiscounted. Add `duration_gap_pv` with present-value weights as a check.
3. **Add a slotting grade.** Map `revenue_runoff` against the obligation runoff to the four Basel grades (contract comfortably exceeds, exceeds, matches, does not exceed). It gives a coarse feature that agencies and banks already use.
4. **Add a re-marketability input.** A flag or score for whether the capacity has other users (asset essentiality, location, power). Undisclosed is NaN, not 0.
5. **Add WeWork as a test case.** Build the clocks from the 2019 S-1/A. The test passes if `renewal_dependent_ebitda_years` and `coverage_contracted` place WeWork in the worst decile of the issuer panel at the 2019 filing date.

## Section touched
`docs/methodology.md` Section 4.7 (lineage, suggested features). Framework S6 in `docs/writeup/combined_framework.tex`. No file other than this card changed.
