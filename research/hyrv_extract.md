# Extract: *High-Yield Bond Relative Value* (comprehensive methodology PDF)

Source file: `high_yield_relative_value.pdf` (repo root). 69 PDF pages: a cover page, a contents page (i), and pages 1 to 67. The PDF is dated 21 October 2026. It calls itself an "Integrated research specification". The cover says: **"No trading backtest claimed"**.

The PDF has its own structure. Part I (Sections 3 to 10) is Gatto's seven-step process. Part II (Sections 11 to 22) gives the support methods and the evidence. This extract keeps the PDF order and the PDF section numbers. In this file, "Section n" means a PDF section. It does not mean a section of `docs/methodology.md`.

## Labels

| Label | Meaning |
| --- | --- |
| `E<n>` | The PDF equation with number n (E1 to E173) |
| `U<n>` | A formula or a worked computation that has no number in the PDF |
| `P<n>` | A procedure: an ordered set of steps |
| `R<n>` | A decision rule, a threshold, or a prohibition |
| [D] | The input is data |
| [Doc] | The input comes from a document: an indenture, a credit agreement, a plan, a filing note that a parser cannot read |
| [J] | The input is analyst judgement |

Source keys, as the PDF uses them: [1] Gatto, *The Credit Investor's Handbook*, page numbers are pages of the supplied 611-page reflowed PDF. [2] Gatto 2025 article on First Brands. [3] Silver Point Form 10. [4] Golin, *The Bank Credit Analysis Handbook* (2001). [5] Seiz, chapter 26 in Golin. [6] Kricheff, *A Pragmatist's Guide to Leveraged Finance* (2012), pages of the supplied 165-page PDF. [7] Scalia (ed.), *Corporate Credit Analysis and AI* (Springer, 2026); [8] to [21] are chapters of [7]. [22] Fortress. [23] ICE index methodology. [24] to [26] Basel CAP10, LCR20, NSF20. [27] Martin, arXiv:2201.01330. [28] MSCI DTS note. [29] FINRA TRACE.

The PDF labels each item with one of three types. "Source method" is a procedure that a cited passage supports. "Operational definition" writes that procedure in explicit notation. "Trading implementation" is a proposal that needs new data and validation (Section 1.2). This extract keeps those labels where the PDF gives them.

---

## Front matter (cover page)

**Objective (quoted).** "Underwrite the company, value the exact loan or bond, and decide whether its expected return justifies its downside, uncertainty, liquidity and use of portfolio capital. The recommendation must compare feasible alternatives on consistent terms, including retaining an existing holding or keeping cash."

**Roles of the sources.**

| Source | Role |
| --- | --- |
| Gatto | Foundation. The seven-step sequence, from transaction analysis to an investment recommendation. |
| Kricheff | Support. Cash-flow underwriting, refinancing, covenants, contractual options, capital structure, events, distressed recovery. |
| Scalia (ed.) | Support. Corporate features, default models, calibration, expert review, machine learning, empirical evidence. |
| Golin and Seiz | Support. Bank-issuer credit analysis and instrument-relative pricing. Bank ratios apply only when the borrower is a financial institution. |

**Not done.** "No trading backtest claimed."

---

## Section 1. Gatto as the governing investment process (p. 1–2)

**(a) Prescribes.**
- P1. Use one investment process: Gatto's seven steps. Step 3 has three parts: profitability, cash flow and liquidity, capital structure.
- Sources and uses applies to originations only. A secondary purchase starts at the later underwriting and comparison stages.
- Rank each proposal against existing positions and the pipeline. Decide which holding to sell to fund it (Gatto ch. 13). Force-rank the portfolio each quarter across sectors.
- Section 1.1: three questions with separate targets: (1) creditworthiness (ability to pay, PD over a horizon, stress vulnerability); (2) security value (the price or spread that the claim, cash flows, options, recovery, liquidity and required compensation justify); (3) trade value (whether a position at executable prices earns enough after financing, hedging, costs and adverse scenarios). Plus an allocation question: does the investment improve the portfolio more than the feasible alternatives?
- Section 1.2: label each item as source method, operational definition, or trading implementation. Label study results, source teaching examples and original numerical examples separately.
- Section 1.3: the seven stages and their outputs:

| Stage | Required output |
| --- | --- |
| 1 Funding and uses | For originations: reconciled transaction, recipients of proceeds, opening debt and cash |
| 2 Business assessment | Evidence on operating resilience, management incentives, failure paths |
| 3 Financial statements | Earnings quality, cash conversion, liquidity, debt capacity on consistent definitions |
| 4 Forecasts | Integrated operating, cash, debt and financing paths under explicit scenarios |
| 5 Company valuation | Enterprise-value range and the loss-absorption capacity behind each claim |
| 6 Claim structure | Enforceable rights, priority, options, covenants, timing of claim cash flows |
| 7 Investment decision | Net-payoff comparison, risk limits, alternatives, sizing, investment memorandum |

- P2 (Section 1.4). The sequence is iterative. A guarantee limit found in Step 6 can change accessible cash in Step 3 and recovery in Step 5. A funding shortfall in Step 4 can change the transaction in Step 1. Re-run the affected stages. Keep a dated decision trail.
- Keep three files: an issuer credit file, a security valuation file, and an investment comparison and decision file. Link one issuer analysis to every claim of that issuer.

**(b) Formulas.** None.

**(c) Rules.**
- R1. "A one-year physical probability of default (PD) is not an option-adjusted spread (OAS), and an OAS residual is not an expected investment return."
- R2. "A stronger issuer can have an expensive bond. A weaker issuer can have an attractive claim at the right price."
- R3. "A model score or a wide spread never waives an unfinished underwriting stage."
- R4. A corporate loan that a bank originated is a corporate claim. Use the Golin bank ratios only when the issuer itself is a bank.
- R5. "The final recommendation must state the best feasible alternative and explain the choice." The comparison universe informs value; the feasible universe determines the action (HCA case: a bond-only mandate still reads loan prices).
- R6. Gatto page numbers refer to the supplied reflowed PDF, not to the print edition. Golin page numbers carry forward an earlier extraction.

**(d) Inputs.** Mandate and feasible universe [J]; existing holdings and pipeline [D, internal].

**(e) Outputs.** Issuer credit file; security valuation file; comparison and decision file.

**(f) Sources.** Gatto introduction, PDF pp. 54–60; ch. 5, pp. 142–154; ch. 13, pp. 366–370; Seiz ch. 26, pp. 585–599; Scalia ch. 3, pp. 29–30; ch. 11, pp. 263–264.

---

## Section 2. Universe, data, and measurement rules (p. 2–5)

### 2.1 Opportunity set before the model universe

**(a)** Define the mandate's feasible opportunity set first: loans, other bonds, existing holdings, eligible rate or credit benchmarks, hedged packages, cash. Record excluded or unassessed alternatives and the reason. An initial implementation can use one currency and performing, fixed-rate, cash-pay corporate bonds. Keep bank-issuer models separate. Add distressed claims, convertibles, contingent capital, PIK and floating-rate debt only when their engines support a credible comparison. Keep callable bonds only with their full redemption schedules and coherent option assumptions. A long-only switch process can come before a strategy that needs bond borrow.
Map issuer and bond identifiers, consolidation, guarantees, operating subsidiaries and holding-company issuers explicitly.

**(c) Rules.**
- R7. "A same-rating peer group does not define the whole investment choice."
- R8. "A relevant permitted alternative without adequate data remains an explicit coverage gap, not proof that the preferred bond beats it."
- R9. "Repeated bonds of one issuer are related observations, not independent credit assessments."

**(f)** Kricheff ch. 10, PDF pp. 50–53; ch. 15, pp. 86–92.

### 2.2 Minimum data schema

**(d) Inputs (the schema).**

| Record | Fields | Update trigger | Input type |
| --- | --- | --- | --- |
| Issuer accounts | Original filings, reporting perimeter, currency, fiscal period, publication timestamp, debt adjustments, unrestricted cash, normalized earnings, cash-flow bridge | Each release, restatement or material event; retain all vintages | [D], adjustments [J] |
| Bank supplement | Capital, RWA, problem loans, reserves, write-offs, funding mix, asset encumbrance, maturity and repricing gaps | Reporting date plus events; label disclosure lag | [D] |
| Credit behavior | Facilities, drawn amounts, drawable capacity, borrowing conditions, overdue payments, payment incidents | Monthly for licensed registers; disclosure frequency for public proxies | [D] or [Doc] |
| Security master | Issuer and guarantors, collateral pools, rank, coupon, frequency, maturity, calls, puts, resets, deferral, covenants, baskets, outstanding face | Issuance, amendment, consent, exchange, call, paydown | [Doc] mostly; coupon and maturity [D] |
| Market observations | Bid and ask or trade price, clean or dirty convention, accrued interest, size, timestamp, OAS, sensitivities, analytics version | Every decision time; reject stale or incompatible observations | [D] |
| Events and text | Ratings and dates, earnings, acquisitions, equity issuance, dividends, tenders, defaults, recoveries, article publication and first-seen times | Event-driven; entity mapping and duplicate control | [D] |
| Implementation | Executable size, price impact, bid-ask cost, financing, borrow availability and fee, hedge spec, exit assumptions | Before each trade and during monitoring | [D] internal |

**(c) Rules.**
- R10. "US TRACE transactions can support liquidity and transaction-price estimates; they do not establish a firm executable quote for a particular future order."
- R11. Scalia credit-register inputs and internal ICAS ratings are not available to a public-market investor. A disclosed revolver is a useful alternative input, but it differs from a monthly bank-system facility record.

**(f)** FINRA TRACE [29]; Scalia ch. 3, pp. 45–46, 56–59; ch. 5, p. 119.

### 2.3 Notation and units

**(b) Definitions.** i issuer, b bond, t decision time, H horizon. E = underwritten EBITDA (nonfinancial); E_bank = bank equity where ambiguous. D debt, C unrestricted cash, I_c cash interest, K cash capex, W working-capital cash use. K also denotes investor capital in the comparison engine. Prices P per 100 face; N face currency.
- U1. P_d = P_c + AI (dirty = clean + accrued interest).
- U2. MV = N P_d / 100.

Units: spreads in bp unless a derivative states decimals. PD and recovery in [0, 1]. Leverage in times; margins in fractions or percent; working-capital periods in days; CS01 in currency per bp. Cash-flow variables are TTM; keep seasonal forecasts separately.

### 2.4 Promised yield, money multiple, realized return

**Source method.** Gatto separates price, yield and spread, and uses IRR and multiple of invested capital. His ch. 3 example: buy 1,000 face at 88; four semiannual coupons of 60; principal at two years. The reported 19.53% yield is twice the semiannual IRR, not an effective annual return.

**(b) Formulas (operational definition: performing bullet bond, bought on a coupon date).**
- E1. P_d = Σ_{k=1}^{mT} (100c/m) / (1 + y/m)^k + 100 / (1 + y/m)^{mT}. m coupons a year, coupon rate c, maturity T.
- E2. y_effective = (1 + y/m)^m − 1.
- E3. MOIC = total positive investor cash receipts / total cash invested.
- U3. Example: MOIC = 1,240 / 880 = 1.4091x; effective annual equivalent "approximately 20.48%".

**(c) Rules.**
- R12. Between coupon dates, use actual dated cash flows, accrued interest and the market day count.
- R13. "MOIC omits timing; an annualized IRR can exaggerate the economic importance of a small gain realized over a very short period."
- R14. Promised yield assumes contractual payment. An expected return needs default, calls, sale price and costs. Do not rank a distressed claim by a yield it is unlikely to pay.
- R15. Entry uses the executable offer and the actual settlement amount. Exit uses a feasible bid and size. Gatto's quote "94/96, size 2 × 3 million" means sell 2 million at 94 or buy 3 million at 96.
- R16. "Verify the actual clean, dirty or flat convention for each instrument rather than assigning it solely from geography."

**(f)** Gatto ch. 3, PDF pp. 108–119.

### 2.5 Accounting normalization and point-in-time rules

**Source method.** Golin: comparable definitions, peer selection, trend reading. Scalia expert assessment: accounting adjustments, financial flexibility, group links, forward information. Kricheff: reconcile earnings to cash available for debt service.

**(a)** For every raw item store: statement definition, as-of period, release timestamp, original value, adjustment, adjusted value, evidence.

**(b)**
- E4. available_{i,k,t} = 1{t^release_{i,k} + ℓ_{i,k} ≤ t}. ℓ is a justified ingestion and trading delay.

**(c) Rules.**
- R17. "Reporting period end is not the information date." A restatement is available only from its own publication time. Do not backfill later accounts, legal terms or final recovery values into earlier decisions.
- R18. For debt, leases, pensions, factoring and securitizations keep reported and analytically adjusted definitions; use one convention consistently.
- R19. Cash netting needs accessibility to the relevant obligor. Consolidated restricted cash does not automatically support the bond.
- R20. Separate financial debt from all liabilities, provisions from cash payments, and maintenance capex from a supported estimate of expansion capex.

**(f)** Golin ch. 5, pp. 88–104; Scalia ch. 5, pp. 117–126, 135–137; Kricheff chs. 9–10, PDF pp. 38–56; chs. 15–16.

### 2.6 Derived feature template

**(b) Formulas.** For a valid comparable metric x:
- E5. Δ_4 x_{i,t} = x_{i,t} − x_{i,t−4q}.
- E6. x^peer_{i,t} = x_{i,t} − median_{j∈P_{i,t}} x_{j,t}.
- E7. Δx^rel_{i,t} = Δ_4 x_{i,t} − median_{j∈P_{i,t}} Δ_4 x_{j,t}.
- E8. x^stress_{i,t} = x_i (explicit downside assumptions).
- E9. Age_{i,k,t} = t − t^release_{i,k}.

**(c) Rules.**
- The PDF says this is "an implementation of Golin's peer/trend method, not a source-calibrated scoring system."
- R21. Define peers by business, country, size and accounting regime before you observe outcomes. For banks add franchise and funding model. For bonds add claim, currency and tenor controls at the valuation stage.
- R22. Flag negative or near-zero EBITDA, net cash, zero interest and zero reported NPLs. "Do not convert undefined ratios into excellent ranks."
- R23. Fit imputation, winsorization, scaling, tree bins and feature selection only in training data. Keep missingness when it carries information.
- R24. "algebraic transformations of the same information are not independent confirmation."

**(f)** Golin ch. 5, pp. 92–104.

---

# Part I. The seven-step investment process

Part I preface: stage order and source procedures come from Gatto's full text. Notation, data conventions, acceptance checks and the comparison engine are operational implementations. Gatto intro pp. 54–60; chs. 5–13, pp. 142–414.

## Section 3. Step 1: sources and uses (p. 6–7)

**Decision question.** "What is being financed, who receives the proceeds, and what claims and cash remain after the transaction?"

**(a) Procedure (source method).**
- P3. Sources and uses applies to originations only. Find why the borrower needs money and which sources fund that need. Build a closing balance sheet for an origination, refinancing, acquisition, distribution or restructuring. For a secondary purchase, rebuild the current capital structure and pending financing events in the later steps. The investor's purchase pays the seller; it does not add issuer cash. Keep issuer funding apart from investor trade cash flow.
- Classify the funding purpose: acquisition, seasonal working capital, productive investment, distribution, operating losses, refinancing. Match it to the sources.
- For a borrowing-base facility, record eligible collateral, advance rates, reserves, letters of credit, commitment and drawn balance.

**Source examples.** VCC: a $20 million revolver, initially undrawn, is potential liquidity, not closing proceeds. The $200 million term loan pays $188.7 million of existing debt, $9.5 million of fees, $1.8 million of opening cash. HCA: separate rolled existing debt from new money. Gatto's illustrative ABL advances 90% against eligible receivables and 85% against inventory orderly-liquidation value: "these are example terms, not general parameters."

**(b) Formulas.**
- E10. DebtProceeds + FreshEquity + ExistingCashUsed = PurchasePayments + DebtRetirementCash + Distributions + Fees + OpeningCashFunded + OtherSpecifiedUses. (Gross cash proceeds before separately listed fees.)
- E11. DebtProceeds_k = D^{new,face}_k · P^{issue}_k / 100.
- E12. D^{post,face} = D^{pre,face} − D^{retired,face} + D^{new,face}.

**(c) Rules.**
- R25. Include each cash movement once. If issuance costs are netted from proceeds, remove them from the uses line.
- R26. A retirement at a premium or discount changes cash and face debt by different amounts.
- R27. Reconcile opening cash to legal entities. Separate unrestricted operating cash from restricted, pledged and minimum balances.
- R28. Letters of credit consume availability. A revolver that shares collateral with a term loan can have different draw conditions.
- R29. Record sponsor cash, seller rollover, deferred and contingent consideration, LCs, guarantees, leases and other debt-like items without merging legally different claims.
- R30. "Do not proceed on a closing model that balances only by assuming an uncommitted financing plug."

**(d) Inputs.** Transaction terms and proceeds [Doc]; pre-transaction capital structure [D] or [Doc]; legal-entity cash [Doc]; borrowing-base terms [Doc].

**(e) Outputs.** A balanced sources-and-uses table; pre and post debt by legal entity and rank; a cash-accessibility map; a list of unresolved funding conditions. Features: net new face debt, cash proceeds per unit of new face, distribution over debt proceeds, near-term maturities, sponsor cash at risk, minimum liquidity at closing. "These are transaction descriptors; their predictive value requires testing."

**(f)** Gatto ch. 5, Figs. 5.1–5.6, PDF pp. 142–154 (ABL pp. 148–150); Kricheff ch. 18, PDF pp. 107–114.

---

## Section 4. Step 2: qualitative analysis (p. 7–8)

**Decision question.** "What makes this business able to generate cash, and which plausible changes can impair that ability?"

**(a) Procedure.**
- P4. Analyse the revenue engine, competitive position, fixed and variable costs, customer and supplier dependence, cyclicality, regulation, management incentives, ownership and financial policy. Each conclusion needs an observable transmission channel.
- Gatto's eight industry-risk categories: secular decline, competition, cyclicality, regulation, customer concentration, product concentration, fad and fashion, commodity exposure. For the three to five material risks, find whether the exposure is analysable, what evidence is missing, how it changes cash generation, and which downside scenario represents it.
- Strategy: competitive position and SWOT. Management: guidance against actual results, incentives, operating history, adaptability. ESG: separate cash-flow effects from mandate requirements.
- P5 (4.1). Keep an evidence ledger: assertion; dated support; contrary evidence; forecast variable affected; downside magnitude; next observation that confirms or weakens it.
- Separate management's operating skill from its willingness to protect creditors: review distributions, acquisitions, asset transfers, reporting reliability, covenant behavior, access to independent information.
- 4.2 (source method). Gatto's cycle analysis: easy financing weakens underwriting and re-leverages; contraction brings cash-flow and refinancing pressure; repair brings cost cuts, cash generation and restructuring. Sponsor incentives (grow, refinance, distribute, exit) can reverse a creditor's expected deleveraging. Trading implementation: store the specific mechanism (maturity exposure in a market closure, floating-rate burden, capex flexibility, potential sponsor distributions, acquisition leverage, financing certainty). Condition scenarios on observable credit availability and operating demand.

**Source cases.** A $200 million software loan with one customer at 40% of sales, 25% after an acquisition, an 80% variable cost base: complete nonrenewal still caused a debt-service shortfall, so a separate recovery judgement was necessary. A rejected product-company LBO: 80% of sales with two retailers, no supply contracts, readily copied products, 60% fixed costs. "These are practitioner underwriting cases, not estimates of the predictive accuracy of a concentration factor."

**(b) Formulas (proposed measurements).**
- E13. CustomerHHI = Σ_j (Revenue_j / Revenue)².
- E14. TopCustomerShare = max_j Revenue_j / Revenue.
- E15. FixedCostShare = IdentifiedFixedOperatingCosts / OperatingCosts.

**(c) Rules.**
- R31. "Qualitative analysis must change the forecast."
- R32. "An undisclosed customer split is missing information, not zero concentration."
- R33. Cost classes must be valid over the chosen horizon: a cost fixed over three months may be avoidable over two years.
- R34. Convert exposures into scenarios in Step 4. Do not add arbitrary qualitative scores to quantitative ratios.
- R35. Do not treat a cycle label as a mechanical clock or a market-timing signal. A hung syndication or a forced-sale discount can create a candidate; the seven steps decide whether the discount pays for the risk.
- R36. "Good narrative quality is insufficient without that connection" (to revenue, margin, cash conversion, funding, valuation or claim rights).

**(d) Inputs.** Segment and customer disclosures [D] (XBRL concentration axis where tagged); cost structure [D] partly, classification [J]; management record [D] and [J]; sponsor and financial policy [Doc] and [J].

**(e) Outputs.** A business-risk thesis; a financial-policy thesis; the main failure paths; a dated peer set selected for economic comparability.

**(f)** Gatto ch. 6, Figs. 6.2–6.16, PDF pp. 157–184 (cases pp. 166–170); ch. 2, pp. 79–100; ch. 4, pp. 123–140; Scalia ch. 5, pp. 117–126.

---

## Section 5. Step 3: financial statement analysis (p. 8–12)

**Decision question.** "What are sustainable earnings, cash generation and the actual burden of the capital structure?" Keep three measures side by side: reported, underwritten, contract-defined.

### 5.1 The three source procedures

- P6. Profitability, six substeps: (1) reconcile reported to adjusted income, with support for each nonrecurring item; (2) adjusted history of three to five years for a noncyclical business, a full cycle with a recession for a cyclical one; (3) earnings quality; (4) repeat for direct competitors; (5) explain performance against expectations and peers, its quality and its drivers; (6) prioritize management questions and diligence.
- R37. "A repeated cash cost does not disappear because management calls a particular instance nonrecurring." When a write-down is removed for comparability, its economic risk stays in the downside forecast.
- P7. Cash flow and liquidity, ten substeps: (1) immediately available liquidity; (2) five-year debt maturities; (3) free cash flow; (4) cash cycle and prospective working-capital changes; (5) additional financing and refinancing capacity; (6) trade-creditor support; (7) maintenance against growth capex; (8) other liquidity levers; (9) conclusion on funding failure and turnaround runway; (10) prioritized diligence. R38. "A current ratio cannot substitute for this analysis."
- P8. Capital structure, six substeps: full capital-structure table; credit ratios; debt-like and contingent obligations; ratings and trajectory; whether leverage suits business risk; follow-up diligence. The table lists every loan, bond and equity instrument ordered by impairment risk, with amount, coupon, maturity, price, yield, ratings and cumulative claim metrics, and identifies alternative investments in the same issuer.

### 5.2 Earnings-quality signals specified by Gatto

- P9. Five tests: (1) orders and backlog: reconcile the backlog bridge; compare order growth with sales growth; book-to-bill; (2) constant-currency organic growth: separate volume and price and mix from currency translation, acquisitions and divestitures, on a constant perimeter; (3) receivable quality: channel, payment and return terms, receivable days, customer credit, allowance against gross receivables, aging; (4) inventory and absorption costing: inventory days against history and peers; overproduction moves fixed cost into inventory and lifts margin while cash and write-down risk worsen; (5) expense sustainability: R&D and advertising cuts, bad-debt provision, unusual capitalized expense; reconcile cost classes before comparing gross margins.
- The PDF says: "These procedures are explicit in the source; standardized scores, regression coefficients and trading thresholds built from them are our research extensions."

**(b) Formulas.**
- E16. Backlog_u = Backlog_{u−1} + Orders_u − Shipments_u.
- E17. BookToBill_u = Orders_u / Revenue_u.
- E18. DemandGap_u = g^orders_u − g^revenue_u. (PDF: "our proposed summary".)
- E19. AllowanceRatio_u = ADA_u / AR^gross_u. ADA is the receivable allowance.
- E20. g^{organic,cc}_u = Σ_c FX_{c,0} Revenue^{same scope,local}_{c,u} / Σ_c FX_{c,0} Revenue^{same scope,local}_{c,u−1} − 1. FX_{c,0} is one fixed comparison-period rate, base currency per unit of local currency.
- E21. X_LTM = X_{last FY} + X_{current YTD} − X_{prior comparable YTD}.
- U4. MGEC: adjusted annual EBITDA 46,259; LTM EBITDA = 46,259 + 31,907 − 30,122 = 48,044 ($ thousands).
- U5. Texas Instruments, September 2006: quarterly sales +1.7%, orders −12.2%, book-to-bill 0.91; sales then fell about 7.9% in each of the next two quarters. "This supports investigating demand divergence; it does not establish a profitable bond-trading rule."
- U6. MGEC organic: reported 150,780 includes 25,000 acquired; organic 125,780; prior year 155,120; organic growth ≈ 125,780 / 155,120 − 1 = −18.9%; reported decline only 2.8%.

**(c) Rules.** R39. Orders, shipments and revenue must use compatible value and period definitions; add recorded cancellations, currency effects or reclassifications to the backlog bridge. R40. Investigate any unreconciled bridge before you read its signal. R41. "An adverse ratio is a diligence signal, not proof of misconduct."

### 5.3 Cash generation, liquidity and financing structure

**(b) Formulas.**
- E22. E = EBITDA_unadjusted + AcceptedSignedAdjustments.
- E23. FCF = E − I_c − T_c − K − W − O.
- E24. GrossLeverage = D / E.
- E25. CashInterestCoverage = E / I_c.
- E26. AfterCapexCoverage = (E − K) / I_c.
- E27. RepaymentCapacity = FCF / D.

FCF convention: after cash interest, cash taxes and capex; before distributions. W is a working-capital cash use. O holds only cash uses not already deducted.

**(c) Rules.** R42. A CFO-based calculation must not deduct interest, tax or working capital twice. R43. Map debt by obligor, guarantee, collateral, currency, maturity, interest type, payment form. Through-leverage and claims ahead of the target matter beside total leverage. Track the PIK-to-cash-pay transition. R44. "Positive annual FCF does not establish liquidity at every interim date; inspect monthly cash minima and actual draw conditions." R45. Scalia variables can sharpen diagnosis and give an independently validated PD; "They do not replace the accounting reconciliation." R46. For a bank issuer, use asset quality, loss absorption, capital and funding measures, not corporate EBITDA ratios.

### 5.4 Liquidity: recurring generation against temporary cash release

**Source method.** Gatto's liquidity FCF = adjusted EBITDA − capex − cash interest − cash taxes, then the cash effect of working-capital change. It differs from unlevered FCF for valuation. Cash restructuring charges excluded from recurring EBITDA return to the cash forecast when paid. Cash cycle = inventory days + receivable days − payable days; quarterly averages preferred for seasonal issuers.

**(b) Worked formulas (JCP 2012, $ millions).**
- E28. ImmediateLiquidity = 930 + 1,241 = 2,171.
- E29. FCF_{before WC} = −541 − 810 − 226 = −1,577.
- E30. FCF_{including WC} = −1,577 + 631 = −946.

The analyst excludes a tax refund (not recurring) and assumes no near-term cash taxes. "This is not a literal reproduction of reported CFO less capex." The $631 million working-capital release came from lower inventory and higher payables while the business deteriorated. The $1.162 billion payable balance "deserved attention alongside bond maturities."

**(c) Rules.** R47. Static liquidity cannot be read without recurring burn and trade support. R48. Gatto rejects equating maintenance capex with depreciation. In JCP, prior spend of about $500 million gives an initial maintenance estimate; later guidance changes it to $400 million. State the evidence and timing of a revision.

### 5.5 Claim-specific creation leverage and debt-like obligations

**(b) Formulas.**
- E31. CreationLeverage_k = [Σ_{j≺k} D^face_j + Σ_{j∈k} D^face_j P_j / 100] / E. j ≺ k: claims senior to layer k (at face). j ∈ k: claims at layer k (at price P_j per 100).
- U7. MGEC through-unsecured: (138,000 + 30,000 + 45,000(0.79) + 2,000(0.795)) / 48,044 = 4.27x.
- U8. MGEC through-subordinated: (215,000 + 15,000(0.68)) / 48,044 = 4.69x.
- U9. MGEC after-capex coverage (E − K)/I ≈ 1.7x, with I = the example's interest expense; the cash version uses I_c.
- E32. LeaseLeverage_{8x} = (D + 8R) / (E + R).
- E33. LeaseLeverage_{liability} = (D + L_op) / (E + R). D excludes the added operating leases; R annual operating rent; L_op reported operating-lease liability.
- E34. U^pension = max(PBO − FMV_assets, 0).
- E35. PensionLeverage = (D + U^pension) / (E + PensionExpense − ServiceCost).

**(c) Rules.**
- R49. Senior claims enter at face "because they must be satisfied before value reaches the junior layer." Apply the actual legal-entity and collateral ranking. "Valuing every senior claim at its discounted market price would answer a different question and understate the claims ahead of the target security."
- R50. Gatto prefers the liability method (E33) when E32 and E33 diverge, because it reflects remaining lease term.
- R51. Pension: add underfunding to debt and pension expense to EBITDA; excluding service cost from that add-back is "technically correct because service cost is compensation." E35 assumes the expense was deducted in E, underfunding is not already in D, and the components are reconciled. It does not remove future cash contributions from the liquidity forecast. "A surplus is not automatically unrestricted issuer cash."
- R52. "These historical US examples are not automatic rules for all reporting regimes."

**(d) Inputs, Section 5 as a whole.** Statements and notes [D]; adjustment acceptance [J]; orders and backlog [D] where disclosed, often only in text [Doc]; allowance for doubtful accounts [D] (XBRL); FX by country and acquired revenue [Doc]; debt by tranche, rank and price [D] for bonds, [Doc] for loans and ranking; lease liability and rent [D]; pension PBO, assets, expense, service cost [D].

**(e) Outputs.** A reconciled historical record; an earnings-adjustment register; a cash-flow bridge; a debt and commitment schedule; a list of data limits. "Every feature retains its definition, unit, perimeter and information timestamp."

**(f) Sources.** Gatto ch. 7, Fig. 7.2, substeps, PDF pp. 190–216; Figs. 7.8–7.10 (pp. 198–200), 7.12–7.26 (pp. 202–216), 7.18 (p. 208), 7.21 (pp. 209–210); ch. 8, Figs. 8.2–8.16, pp. 226–254; ch. 9, Figs. 9.5–9.17, pp. 259–282; ch. 10, Figs. 10.21–10.24, pp. 312–316; Kricheff chs. 9–10, PDF pp. 38–56.

---

## Section 6. Step 4: forecasting (p. 12–14)

**Decision question.** "How does the company fund itself and service each obligation through plausible operating and financing paths?"

**(a) Procedure.**
- Forecast operating drivers first, then earnings, working capital, cash taxes, capex, interest, debt and liquidity.
- R53. "Use a horizon long enough to include the next material refinancing or contractual change, even when the proposed trade horizon is shorter. A six-month trading idea can still depend on the credibility of a maturity eighteen months away."
- P10 (6.1, Gatto Fig. 10.2). Eight items: (1) input adjusted history; (2) drivers and sensitized cells on an assumptions page; (3) forecast the income statement; (4) forecast the balance sheet except cash and debt; (5) forecast cash flow and link cash and debt back to the balance sheet; (6) change assumptions to run scenarios; (7) summarize results and credit ratios; (8) assign probabilities where appropriate and explain the judgement.
- The worked model separates fixed and variable COGS and SG&A; uses the forward reference-rate curve plus each loan's spread; links refinancing and revolver draws to interest; forecasts receivables, inventory and payables from days. PP&E rolls forward by capex minus depreciation.
- P11. Cash sweep order: after mandatory debt payments, surplus cash first repays the revolver, then accumulates. A shortfall first uses cash above the operating minimum, then needs a revolver draw. "Our implementation additionally enforces actual draw capacity and records an unfunded gap instead of treating required borrowing as automatically available." Average-debt interest may need iteration.
- P12 (6.3). Start with base, adverse, severe stress and recovery or resolution paths, plus event outcomes. Specify joint assumptions: volumes, prices, margins, collection days, inventory, supplier terms, capex flexibility, reference rates, borrowing spreads, available facilities, covenants, asset sales, shareholder actions. Stress refinancing availability as well as price.
- Compute the funding screen G_h (E75), its minimum across dates, and the first date at which a required payment fails without an uncommitted action.
- Include a reverse stress: "the combination of operating and financing changes that first breaks the thesis, rather than only a fixed percentage EBITDA shock."

**(b) Formulas.**
- E36. AR_u = 2 · DSO_u · Revenue_u / 365 − AR_{u−1}. (Annual revenue; beginning and end average. Parallel annual-COGS equations for inventory and payables.)
- E37. Revenue_u = Σ_j Volume_{j,u} Price_{j,u}.
- E38. C_u = C_{u−1} + FCF_u + DebtCashProceeds_u + EquityProceeds_u + NetAssetSaleCash_u − DebtRetirementCash_u − Distributions_u − FinancingFees_u.
- E39. D^face_u = D^face_{u−1} + NewFaceDebt_u + PIKAccrual_u − FaceDebtRetired_u + OtherContractualChanges_u.

**(c) Rules.**
- R54. "No forecast statement cell should contain an unexplained hardcoded assumption." Management or consensus case, analyst base case and downside cases are distinct.
- R55. A reasonable base case is "approximately as likely to be beaten as missed; deliberate pessimism belongs in downside cases."
- R56. For a shorter forecast bucket, align flow and day count; "do not divide a quarterly flow by 365 in this inversion." An end-balance implementation must state the changed convention.
- R57. Exclude asset-sale proceeds and financing fees from the FCF bridge when they appear in E38. Interest on new debt and lost interest income feed future FCF. PIK adds to the claim without cash. Use explicit timing for interest and debt circularity.
- R58. "assuming unlimited debt at a higher coupon can conceal the actual failure mode."
- R59. "A coverage threshold is an analytical warning unless it is also a verified contractual test." Step 6 decides legal consequences.
- R60. If probabilities q_ω are used, the states must be mutually exclusive and collectively exhaustive, q_ω ≥ 0, Σ q_ω = 1. "If the scenario set deliberately omits default, the expected return is conditional on survival." "A few named stresses alone do not establish the probability or severity of the entire tail." Scalia physical PDs can inform the distribution "only after horizon, definition, issuer population and calibration are aligned."
- R61. "Scenario probabilities remain an explicit judgment to debate with the investment committee." Scalia-style models "do not convert a selected narrative stress into a calibrated whole-distribution PD automatically."

**Source cases.**
- TM Corp downside: sales growth −20%, −10%, 15%, 15%, 1.5%; inventory days up first; supplier terms tighter; capex cut then catch-up. Net leverage peaks at 9.2x in year two; liquidity low of about $6.7 million only in year four; debt service funded by the revolver although after-capex coverage is below 1x in the first two years. The teaching model runs cash to zero; a positive operating-cash minimum needs earlier borrowing.
- JCP: base restores promotions and gradually recovers EBITDA; downside has slower recovery and a $500 million working-capital drain. With a $100 million minimum cash balance the downside needs $677 million more borrowing in 2013 and $1.514 billion in 2014, above the initially disclosed $1.241 billion availability. "Treat the base and downside as contemporaneous underwriting hypotheses, not as predictions proven by the subsequent historical outcome."
- Customer-loss example: a 15–20% loss severity is plausible; the probabilities differ between a sticky software relationship and a replaceable commodity supplier.

**(d) Inputs.** Adjusted history [D] plus [J]; drivers [J] or forecast registry [D]; forward reference-rate curve [D]; loan spreads, floors, amortization, sweeps [Doc]; revolver capacity and draw conditions [Doc]; minimum operating cash [J] or [D]; scenario probabilities [J].

**(e) Outputs.** A consistent scenario model with quarterly or finer debt service and liquidity, terminal debt, potential credit events, uncertain assumptions, a reverse stress.

**(f)** Gatto ch. 10, Fig. 10.2, PDF pp. 285–287; Figs. 10.7–10.14, pp. 294–300; pp. 296–303; Figs. 10.18–10.20, pp. 306–310, 317; Figs. 10.21–10.24, pp. 312–316; p. 311.

---

## Section 7. Step 5: corporate valuation (p. 14–16)

**Decision question.** "What is the business worth across scenarios, and how much value supports the creditor claims?"

**(a) Procedure.**
- Estimate value independently of the debt to repay. Use several methods when data support them: comparable EV multiples, cash-flow valuation, asset and liquidation values.
- P13 (7.1). Gatto's four methods: (1) public company comparables: consistent EV multiples (EV/EBITDA, EV/sales, EV/(EBITDA − capex)), explain premium or discount for size, diversification, growth, margins, capital intensity; (2) precedent acquisitions: date, control value, synergies, buyer circumstances; (3) DCF: unlevered cash flow, required return, terminal value; (4) liquidation: realizable proceeds by asset class less disposal and wind-down costs.
- Observable identity for quoted equity: debt − cash + equity market capitalization.

**(b) Formulas.**
- E40. UFCF_t = E_t − K_t − W_t − T^unlev_t − O^unlev_t. T^unlev excludes the interest tax shield.
- E41. WACC = w_D r_D (1 − τ) + w_E r_E.
- E42. UFCF_u = EBIT_u (1 − τ_u) + DA_u − K_u − ΔNWC_u.
- E43. EV_0 = Σ_{u=1}^{T} UFCF_u / (1 + r)^u + TV_T / (1 + r)^T.
- E44. TV_T = UFCF_{T+1} / (r − g), r > g; EV^multiple_ω = m_ω E^consistent_ω.
- E45. V^available_ω = EV^resolution_ω + C^distributable_ω − ProcessCosts_ω − ClaimsAheadOutsideTheWaterfall_ω.

**(c) Rules.**
- R62. "A management forecast and a transaction multiple based on that same forecast are not fully independent evidence."
- R63. The four methods "should not be averaged mechanically."
- R64. Check CAPM-based equity returns against opportunity cost and the portfolio manager's judgement.
- R65. The terminal value must be discounted to today. The PDF notes Gatto's p. 328 perpetuity expression labels it present value without the final discount; the PDF keeps the discount.
- R66. The compact tax formula assumes taxable earnings; model cash taxes directly when losses or tax attributes matter. Align nominal cash flows, currency, inflation and discount rate. "Do not apply a stable-growth terminal formula to a business that has not reached a supportable stable state."
- R67. Recovery value is the value at the actual resolution date within the relevant obligor or collateral pool. Stressed EBITDA and stressed multiples can fall together. Add cash only if not in EV and accessible to that pool. "Deduct a priority claim here or in the waterfall, never both."
- R68. Do not assume a quoted asset value is realizable after time, costs and enforcement limits.
- R69. "Equity cushion is a sensitivity to enterprise value, not a cash reserve." A security can have high asset coverage and still an inadequate return at its price.

**Source case (VCC, anonymized 2019 refinancing).** Comparables EV $262.5–297.5m; precedents $297.5–332.5m; DCF downside, base, upside $228.9m, $275.7m, $399.4m; base DCF 12% discount rate and 8x exit multiple. Liquidation gives only $101.7–123.8m for secured creditors after costs. The source leaves liquidation out of its going-concern chart, so "the lowest valuation supports a $200m loan" holds only for the going-concern cases. Liquidation covers about 51–62% of the loan before any further senior revolver claim. "This is a case-specific choice of valuation regime that the investment memo must make explicit."

**(d) Inputs.** Peer multiples [D] for public peers (equity price, shares, debt, EBITDA); precedent deals [Doc] or licensed [D]; forecast UFCF [J] plus model; discount rate [J]; asset appraisals and liquidation rates [Doc] and [J]; process costs [J].

**(e) Outputs.** EV range by scenario; valuation sensitivities; accessible-value pools; a dated recovery-value bridge. Features: EV over debt, value ahead of the target claim, cumulative leverage through the claim, recovery sensitivity to value and delay.

**(f)** Gatto ch. 11, PDF pp. 319–332; p. 328; ch. 13, p. 393, note 1.

---

## Section 8. Step 6: structuring and documentation (p. 16–17)

**Decision question.** "Which cash flows and legal protections belong to this specific loan or bond, and how can they change?"

**(a) Procedure.**
- P14. Read the governing documents and amendments. Map obligors, guarantors, excluded subsidiaries, collateral, lien ranking, intercreditor terms, payment priority, permitted debt and investments, restricted payments, reporting duties, defaults, cures, voting thresholds, transfer restrictions. Separate contractual subordination, structural subordination and collateral priority.
- P15 (8.1). Gatto's twelve review items: amount, debt class, maturity, amortization and cash sweep, coupon, fees and OID, calls and prepayment, change of control, subordination, collateral, covenants, amendment rights.
- Keep scheduled amortization, covenant excess-cash-flow repayment and voluntary deleveraging apart in the model. Map priority to particular assets and guarantors: an ABL and a term loan can hold different ranks over different pools.
- P16 (8.2). Convert terms into scenario cash flows. Bonds: calls, puts, make-wholes, tenders, change of control, deferral, PIK. Loans: reset, compounding, observation lag, floor, margin, day count, principal schedule, OID, fees, amortization, repricing protection, prepayment, settlement delay, funding commitments.
- Translate negative covenants into action-specific capacity where feasible.

**(b) Formulas.**
- U10. Gatto coverage definitions: E/I; (E − K)/I; (E − K − T_c)/(I + mandatory principal). "These are alternative contractual definitions, not interchangeable ratio names."
- E46. L_max = 100 / (25(1 − 0.15)) = 4.706x ≈ 4.7x. (Debt 100, projected EBITDA 25, cushion 15%; general cushion 15–30%.)
- E47. DebtCapacity = L_max E^legal − D^legal.
- E48. EBITDAFallToLimit = 1 − D^legal / (L_max E^legal).
- E49. Coupon_{k,ω} = N_{k−1,ω} Δt_k [max(r^ref_{k,ω}, f) + m]. Floating-rate loan with floor f, margin m. "This is a template, not a universal loan convention."

**(c) Rules.**
- R70. "Do not infer equal recovery from a shared rating or an issuer-level description."
- R71. Maintenance tests differ from incurrence tests. Contractual EBITDA adjustments and debt exclusions can differ from the analyst's economic measures.
- R72. "The cushion reduces the EBITDA denominator; it is not a 15% increase in the original leverage ratio."
- R73. E47 and E48 hold at fixed debt under verified legal definitions. Test timing, baskets, cures and waivers change the consequence. "A covenant breach is a contractual event to analyze, not an automatic assumption of immediate liquidation."
- R74. A rate decline can cut loan income and lift a fixed-rate bond price; keep both effects in the same scenario.
- R75. Investor return depends on amount and timing at purchase-price economics, not only recovery as a percentage of face.
- R76. "The same issuer default state must feed all of its claims"; do not give independent defaults to the loan and the bond of one issuer.
- R77. Basket interactions, conditions, exceptions and transferred assets matter. A legal permission to incur debt is not a forecast that it will be incurred; a stress case can test that path. New priming debt is a new priority claim and cash; model the use or dissipation of that cash before you estimate the loss to existing creditors.
- R78. "An uncertain legal right must appear as uncertainty or a scenario; it cannot be silently assumed favorable in the investment case."

**(d) Inputs.** Indenture, credit agreement, intercreditor, amendments [Doc]; covenant EBITDA definitions [Doc]; reference-rate curve [D].

**(e) Outputs.** A claim map; a contractual cash-flow engine; an option and event schedule; a documented waterfall; unresolved legal questions.

**(f)** Gatto ch. 12, PDF pp. 337–356; Kricheff chs. 15–18, PDF pp. 86–114.

---

## Section 9. Step 7: investment recommendation and comparative value (p. 17–20)

**Decision question.** "Given the completed underwriting, which feasible use of capital offers the most attractive compensation for its risks, costs and portfolio effects?"

**(a) Procedure.**
- Compare the target loan or bond with other claims of the issuer, eligible claims of other issuers, existing holdings, permitted hedged packages and cash. "A credit score, yield, spread residual or target price is an input to this comparison." Keep the full payoff distribution. Explain the next-best feasible choice.
- Source requirement: Gatto requires comparing expected return and possible loss against existing holdings and pipeline, including the holding to sell. The PDF states: the book "does not prescribe the report's common-horizon wealth engine, scenario probabilities, expected-shortfall limits or allocation objective."
- Screening memo (decides whether to spend diligence) against final memo (leads with action and relative value, thesis, risks and mitigants, analysis for debate).
- P17 (9.1). Let A_t = feasible actions: buy, retain, reduce, sell, switch, hold cash, eligible hedge package. Apply mandate, access, quote size, borrow, liquidity, currency, concentration, funding constraints. Record exclusions and unavailable information. For each action store: instruments and quantities; timestamp; executable entry terms; common horizon H; base currency; allocated capital K; unused cash; financing and collateral; distribution dates; scenario terminal values; entry and exit costs; portfolio changes.
- P18 (9.4). Keep the quarterly cross-sector force-ranking plus event-driven reviews: revisit positions and pending ideas at current realizable prices, including what to sell.
- P19. The memorandum must contain: (1) action and price: instrument, size, entry limit, horizon, funding, hedge; (2) underwriting: outputs of Steps 1–6 with contrary evidence and open questions; (3) payoffs: dated cash flows, terminal values, scenario assumptions and probabilities, net expected return, adverse outcomes; (4) comparison: best feasible alternatives including cash or retention, and why the chosen action fits the mandate better after costs and risk; (5) portfolio fit: exposures, tail loss, concentration, liquidity, capital commitments; (6) monitoring: catalysts, price and valuation triggers, thesis falsifiers, review dates, add, reduce or exit conditions.

**(b) Formulas.**
- E50. B_{a,0} = K − V_{a,0} − TC_{a,0}. (Unused cash of a fully funded action.)
- E51. W_{a,H,ω} = V_{a,H,ω} + B_{a,0} A_{0,H,ω} + Σ_{0<u≤H} CF_{a,u,ω} A_{u,H,ω} − TC_{a,H,ω}. A_{u,H,ω} is the assumed accumulation factor from u to H.
- E52. R^net_{a,H,ω} = W_{a,H,ω} / K − 1.
- E53. X_{a,H,ω} = R^net_{a,H,ω} − R^cash_{H,ω}.
- E54. µ_a = Σ_ω q_ω X_{a,H,ω}.
- E55. r^annual_{a,ω} = (W_{a,H,ω} / K)^{1/H_years} − 1. (Full reinvestment inside the allocation; no external flows.)
- E56. π^loss_a = Σ_ω q_ω 1{R^net_{a,ω} < 0}.
- E57. π^cash_a = Σ_ω q_ω 1{X_{a,ω} < 0}.
- E58. ES_α(L_a) = min_z [z + (1/(1 − α)) Σ_ω q_ω max(L_{a,ω} − z, 0)], with L_a = −R^net_a, 0 < α < 1. Alternative: L_a = max(−R^net_a, 0); state which.
- E59. ΔES_a = ES_α(L_{P+a}) − ES_α(L_P).
- E60. OC_a = max_{j∈A^admissible_t} µ_j − µ_a. Defined only for a ∈ A^admissible_t.

**(c) Rules.**
- R79. "'Every alternative' means the materially relevant feasible opportunity set; a selected peer group is only one subset."
- R80. Use the same funding policy for all actions, but keep their actual financing costs and collateral terms. A private claim without a credible exit gets an explicit hold or conservative exit value, "not an invented executable market price."
- R81. The fully funded branch needs B_{a,0} ≥ 0 and enough interim cash. Ledger: coupons, principal, call proceeds, recoveries, hedge settlements; fees on their dates. Terminal value excludes settled claims. "Costs embedded in an executable price are not deducted again." "A derivative's minimum initial margin is not an equivalent denominator to a fully funded bond investment."
- R82. Convert foreign cash flows at payment-date FX and terminal values at the horizon rate; model actual hedge settlements. Apply one tax convention.
- R83. A security IRR does not count reinvested distributions twice. "Averaging scenario IRRs generally does not give the IRR of expected cash flows." Use horizon wealth for the main comparison; annualize only when wealth is nonnegative and the horizon is defined.
- R84. Report for each action: expected net and excess return, loss probability, probability below cash, tail loss, recovery-sensitive loss, liquidity demand, uncertainty. "Expected shortfall is only as credible as the modeled tail."
- R85. "Do not collapse the decision into yield/PD, spread/leverage, return/CS01 or a universal Sharpe ratio." One transparent choice: maximize expected net excess return subject to capital-loss, liquidity, concentration and funding limits. Another: a documented risk-penalty objective. Limits and risk aversion are investment policy.
- R86. Portfolio effect: use common joint scenarios, consistent capital, correlated issuer shocks. "Standalone expected shortfall does not establish diversification or marginal portfolio risk." Include the sale leg of a switch. Opportunity cost uses current realizable values, not historical purchase price.
- R87. OC_a is useful only when capital basis and risk limits are comparable. "Cash and retaining an existing holding remain valid choices when no feasible switch improves the objective after costs."
- R88. "No favorable model output exempts a candidate from the recommendation or its alternatives comparison."

**(d) Inputs.** Feasible set and mandate [J]; executable quotes [D] (TRACE only proxies them, R10); scenario terminal values [model]; scenario probabilities [J]; cash return [D]; costs [D]; risk limits α and budgets [J, policy].

**(e) Outputs.** Per action: µ_a, π^loss, π^cash, ES, ΔES, OC; the chosen action; the best feasible alternative; the memorandum.

**(f)** Gatto ch. 13, PDF pp. 366–371.

---

## Section 10. Gatto's distressed-credit extension (p. 20–25)

**Place.** Step 2 identifies business, ownership and creditor incentives; Step 4 forecasts liquidity and restructuring paths; Step 5 values assets and the reorganized business; Step 6 sets each claim's rights; Step 7 chooses. Gatto: the seven steps are "necessary but insufficient" when restructuring or a liquidity crisis is expected. Eight strategy families: new financing, spread tightening, distressed for control, fundamental value, capital-structure arbitrage, trade claims and vendor puts, liquidations, special situations. R89. "A distressed screen is therefore a research trigger; it does not establish an attractive investment." Units in the examples: USD millions; prices per 100. Legal cases describe the book's account at publication, not current law.

### 10.1 Claim map before recovery

**(a) Source method.** Separate time, contractual and structural subordination. Near-maturity debt may be repaid before a crisis, but an earlier filing removes that advantage. Contractual subordination depends on the actual beneficiaries of a turnover provision. Structural subordination depends on each entity's assets, liabilities, guarantees and intercompany claims. "Consolidated leverage cannot determine these distributions." Operational: keep an entity graph of operating assets, accessible cash, obligors, collateral, guarantees, intercompany loans, allowed claims and turnover.

**(b) Formulas.**
- E61. d^(0)_{j,ω} = F^allowed_{j,ω} min(1, A_ω / Σ_{k∈U} F^allowed_{k,ω}). A_ω is nonnegative value left for the pool after senior distributions and costs. Then apply contractual transfers, caps, and redistribute residuals.
- U11. Turnover example: 125 for unsecured; senior bond 1 = 60, senior bond 2 = 40, trade = 50, subordinated = 75. Initial distributions 33.33, 22.22, 27.78, 41.67. Both senior bonds benefit: 97.22% each; trade 55.56%; sub 0. Only bond 1 benefits: 100%, 55.56%, 55.56%, 20%.
- U12. TA Wang: separate-entity recoveries 36.67% (holdco bond), 83.33% (OpCo 1 unsecured), 100% (OpCo 2 unsecured). Consolidation: EV 110 − secured 45 = 65 for 130 of unsecured: all 50%.
- U13. Teich: separate-entity recovery 2(400) / (800 + 500 + 500) = 44.44%; consolidation 400 / (800 + 500) = 30.77%. On the original 500 face; asset pool stays 400.

**(c) Rules.** R90. "A generic senior-first waterfall misses this distinction." R91. Multiple estates, guarantees and intercompany flows need a coupled calculation: do not duplicate assets or pay a limited entitlement twice. R92. Kmart: trade claims worth 5–10 points less than bonds; a claim-basis risk when you hedge trade receivables with bonds. Owens Corning: guaranteed bank debt against unguaranteed parent bonds. Legal-outcome asymmetry can motivate a trade, but borrow, carry, guarantee validity, settlement, funding and interim price risk "prevent treating it as risk-free arbitrage."

### 10.2 Plan allocation against economic recovery value

**(a)** A restructuring can distribute cash, new debt, equity, warrants. New debt at face is not its market value. The fulcrum can get equity worth more than its face. "Plan valuation determines allocation; an analyst's economic valuation determines what that allocation is worth."

**(b)**
- U14. David's Rigatoni: exit financing 150 retires the first 150 of claims; senior unsecured 200, junior 400. Plan EV 300: equity 150, all to seniors. Plan EV 675: equity 525; seniors get 200/525 = 38.10%, juniors 61.90%. Economic EV 400: equity worth 250; senior package worth 250 under the first allocation, 95.24 under the second.
- E62. V^package_{b,ω} = C_{b,ω} + MV(NewDebt_{b,ω}) + α_{b,ω} MV(NewEquity_ω) + MV(Warrants_{b,ω}).

**(c)** R93. "Recomputing ownership from the analyst's economic value would erase the contractual allocation effect." R94. Include subscription payments, DIP commitments and other new cash as dated investment flows. Adjust ownership for management incentives, rights offerings and dilution. Do not subtract a cash contribution in both the package and the ledger.

### 10.3 Resolution time, new funding, disputed value

**(a)** Prepackaged, negotiated and freefall processes differ; also failed reorganization, asset sales, administrative insolvency. Store monthly cash burn, financing availability, plan support, distribution dates, delay stresses. R95. "A recovery estimate without timing and financing needs cannot determine an investment return."
- U15. Credit bid: secured face 450 bought at 82 costs 369 and may give 450 of bidding credit. "The 81 difference is neither a cash receipt nor a complete acquisition return." A stalking-horse break fee pays for a commitment with execution and deterioration risk.
- R96. Treat litigation as a separate uncertain asset or liability with legal cost, collectibility and delay. Caesars examiner range 3.6–5.1 billion "is not a realized cash recovery."
- U16. Tailored Brands: buy 880 term-loan face at 40, cost 352. An 85% equity allocation is worth 340, 750.13 or 1,190: money multiples 0.966, 2.131, 3.381. "These are scenario values, not realized investment returns." Later funding diluted nonparticipants. R97. Reserve follow-on capital and model the ability to participate; "identifying the fulcrum claim alone is insufficient."

### 10.4 Liability management

**(a)** J.Crew: track restricted subsidiaries, unrestricted subsidiaries and loan parties apart. Asset transfers and investment baskets can remove collateral value. Review action-specific capacity, affected guarantees and liens, consideration, consent, challenge scenarios. The author "does not claim that the eventual impairment caused solely by J.Crew's transfer can be isolated."
- U17. Hypothetical uptier: original debt 2,000; downside value 1,500–1,750; future DIP 100. Original recovery 70.0–82.5%. A block exchanges 1,002 old into 952 priority debt and adds 200 new money; 998 old debt stays out. If the new cash is consumed: (1,500 − 100 − 952 − 200)/998 = 24.85%; (1,750 − 100 − 952 − 200)/998 = 49.90%.
- R98. "Credit any new cash still available in the resolution pool; subtracting the new senior claim while ignoring retained proceeds overstates impairment." The example is distinct from the historical Serta amounts and disputes.
- R99. CDS hedges: model credit-event definitions, deliverable obligations, cheapest-to-deliver, auction settlement. Cash recovery and auction price need not match. Manufactured-event examples are not evidence that issuer PD alone prices a CDS hedge.

### 10.5 Liquidation and contingent purchase commitments

**(a)** P20. Liquidation sequence: asset inventory; realizable values; all claims and priority; waterfall.
- U18. KHA: assets 3,476, 3,809, 4,200 leave 1,377, 1,728, 2,135 for unsecured after DIP, wind-down, priority and secured. Unsecured claims 4,043, 3,876, 3,807. Recoveries 34.06%, 44.58%, 56.08%.
- R100. Stress asset realizations, claim disputes and time jointly. Property: reconcile rent to NOI before a cap rate. Favorable lease: value the net rental advantage over remaining term, subject to transfer rights. Lease-rejection and nonfinancial claims come from documents and case analysis; "the book's simplified historical legal descriptions are not a universal statutory calculation."
- U19. Vendor put: 1.5 million premium for three months on 25 million receivables; 90% strike needs 22.5 million cash on exercise; net claim cost 21 million; sale at 60 gives 15 million; loss 6 million. R101. "An annualized premium quotation conceals both recovery risk and the liquidity needed to purchase the claim."

### 10.6 Return generation against portfolio insurance

- U20. Long 10 million secured loan, short 10 million unsecured bond, both at par; loan coupon 8.25%, bond 9.5%; carry −125,000 a year; two-year carry plus 25 bp unwind per leg = 300,000. Scenarios (loan exit, bond exit, probability, P&L $m): no recession (100, 100, 80%, −0.30); modest (97, 90, 15%, +0.40); severe (90, 35, 5%, +5.20). Weighted P&L 0.8(−0.30) + 0.15(0.40) + 0.05(5.20) = 0.08 million.
- R102. "This currency P&L is not a return on zero capital." Reserve margin and funding; check borrow; use a common capital denominator. "Equal face does not establish rate, spread or recovery neutrality." "Do not cap a bond short's loss at a price of 100."
- R103. Evaluate a long-senior short-junior package in joint portfolio scenarios as well as standalone.

### 10.7 to 10.9 JCP trades (historical worked recommendations)

- U21. Trade 1: buy 10 million of 7.125% 2023 notes at 89.5; short 10 million of 7.4% 2037 notes at 82. Thesis: the small 255 million 2023 issue had a restrictive incurrence covenant; a tender to remove it helps the long; new secured debt hurts other unsecured. Net cash 10(89.5 − 82)/100 = 0.75 million. Carry 10,000,000(0.07125 − 0.074) = −27,500 a year. Reported outcome: tender at 145; short bond 81.5. Gross price P&L 10(145 − 89.5)/100 + 10(82 − 81.5)/100 = 5.60 million, before carry, borrow, funding and execution.
- R104. The chapter's ~500 million capacity estimate lacks public detail; its covenant wording conflicts with Chapter 12. "obtain the governing indenture before calculating capacity." The make-whole depends on terms and Treasury rates. The 0.75 million "is neither sufficient required capital nor a proven worst-case loss." "Its lesson is a claim-specific catalyst, not a generic long recommendation on a troubled issuer."
- U22. Trade 2: buy 10 million 6.375% 2036 at 75 (7.5 million). Spread compression 100–150 bp; one-year exit prices 84.1 and 88.9; default sale at 35, no terminal coupon. Interim coupon 0.31875; final receipts 8.72875, 9.20875, 3.50000; nominal IRR 20.1%, 25.9%, −59.1% (twice semiannual IRR). Effective annual: about 21.06%, 27.58%, −50.34%. Reported prices about 72.6 after one year and 76 after two: about 5.3% and 9.1% nominal annual IRR. R105. "A positive realized return does not by itself establish that the original risk was attractively compensated." A distressed exit quote of 35 is not necessarily final recovery.
- U23. Trade 3: short 10 million of stock at 15.20. Scenario prices 0, 2.78, 11.80, 20.18 with probabilities 30%, 10%, 50%, 10%: expected about 8.2. At 8.30 average: 10,000,000/15.20 × (15.20 − 8.30) ≈ 4.54 million gross. Book excludes stock-borrow charges. R106. "Equity-short losses are unbounded." "the three JCP recommendations were discussed at different 2013 dates, so their reported outcomes are not a synchronized executable backtest."

**(d) Inputs, Section 10.** Entity graph, guarantees, turnover, intercompany claims [Doc]; plan terms [Doc]; asset realizations [Doc] and [J]; claim amounts [Doc]; resolution timing [J]; CDS terms [Doc]; borrow [D].

**(e) Outputs.** Claim map and entity graph; package values per claim; dated recovery ledger with funding needs; LME exposure; liquidation waterfall; portfolio-insurance evaluation.

**(f)** Gatto ch. 14, PDF pp. 416–423; ch. 15, pp. 428–440; ch. 16, pp. 447–466; ch. 17, pp. 471–496; ch. 18, pp. 498–512; ch. 19, pp. 514–572.

---

# Part II. Supporting methods and research evidence

## Section 11. Supporting module: corporate credit features (p. 26–30)

**Place.** Detail for Step 3, forecasts for Step 4, contractual headroom for Step 6. "These features quantify the underwriting evidence; they do not independently select the investment."

### 11.1 Risk families

Source: Scalia's statistical model groups profitability, indebtedness, interest burden, debt service, liquidity and working capital, with sector and size differences; the expert layer adds accounting adjustments, flexibility, governance, sector and country, group. R107. Keep three parallel sets of earnings and debt: reported, underwritten, contract-defined. "The differences are informative and must not be silently collapsed."

### 11.2 Source feature dictionary (Scalia, Table 6, §5.4)

| Feature | Definition and unit | Note |
| --- | --- | --- |
| Cash profitability | CF^source / Sales; CF^source / Assets | Cerved/Cebi-reclassified "cash flow"; not proven equal to CFO or FCF |
| Value-added productivity | ValueAdded / Assets | Sector-specific |
| Equity cushion | Equity / (D^financial − Cash) | Net-cash and negative-equity cases are separate states |
| Interest burden | Interest / EBITDA; Interest / CF^source; Interest / Sales | Inverse coverage, "not 'times coverage'" |
| Average debt cost | ROD = Interest / D^financial | Align period and average debt |
| Sales to debt | Sales / D^{total,net} | Not repayment capacity |
| Cash buffer | Cash / D^short | Restricted cash needs review |
| Current ratio | CurrentAssets / CurrentLiabilities | Receivables and inventory less liquid |
| Financial mismatch | (CurrentLiabilities − CurrentAssets) / Assets | Positive = short-term deficit |
| Working-capital duration | Receivable days, inventory days, their sum, payable days | Nonlinear reading |
| Sales and maturity | Sales growth or contraction; log firm age; sector size controls | No universal linear sign |

Formulas U24 to U34 are the eleven rows above. Development-sample medians (Table 6): interest/EBITDA 20.3% nondefault, 56.6% default; cash/short-term debt 4.9% against 1.7%. R108. "These are development-sample summaries, not universal buy/sell thresholds." R109. If only public statements exist, build CFO and FCF features independently; "do not label them exact reproductions of CF^source." R110. A ratio can be a useful covariate without being an adequate underwriting test: the Scalia current ratio "does not supersede Gatto's cash, facility, working-capital and maturity analysis."

### 11.3 Cash earnings, debt service, FCF

**(b)**
- E63. E = EBITDA_unadjusted + accepted signed adjustments.
- E64. Gross leverage = D / E.
- E65. Net leverage = (D − C_available) / E.
- E66. Cash coverage = E / I_c.
- E67. Total coverage = E / I_total.
- E68. After-capex coverage = (E − K) / I_c.
- E69. FCF = E − I_c − T_c − K − W − O.
- E70. Debt repayment capacity = FCF / D.
- U35. FCF = CFO_norm − K, when CFO is normalized to include cash interest and taxes.
- E71. Addback dependence = (E_covenant − E_underwritten) / E_underwritten.
- E72. Cash conversion = CFO_norm / E_underwritten.

**(c)** W positive = cash use. If you start from management-adjusted EBITDA, subtract rejected add-backs. Show pre- and post-distribution cash generation when policy matters. R111. A maintenance-only capex case is a sensitivity, "not proof that planned growth capex is avoidable." R112. "Cash coverage can overstate sustainable capacity when payment-in-kind or deferred-pay debt will later require cash coupons." R113. E71 and E72 are "report-engineered features." "noncash does not automatically mean irrelevant, and nonrecurring does not automatically mean unacceptable." R114. "FCF/debt measures capacity to repay, while the cash-allocation policy determines whether debt actually declines."

### 11.4 Working capital and operating forecasts

- E73. DSO = 365 · Receivables / Sales_TTM; DIO = 365 · Inventory / COGS_TTM.
- E74. DPO = 365 · TradePayables / COGS_TTM; CCC = DSO + DIO − DPO.

R115. These 365-day average-balance formulas are Gatto's; Scalia gives only their statistical role. Gatto allows purchases as an alternative DPO denominator. Use one declared convention; prefer frequent averages for seasonal issuers. VAT, factoring, supply-chain finance, acquisitions and seasonal endpoints distort comparisons. R116. Derive the working-capital cash effect from forecast balances; do not assume both a cash release and better collection days. R117. Capex/sales and capex/depreciation are diagnostics; "a low ratio alone does not prove underinvestment."

### 11.5 Refinancing and a dated liquidity schedule

**Source method.** Interest can rise sharply with unchanged debt/EBITDA; nominally undrawn facilities may not be drawable.
- E75. G_h = C_0 + A_{drawable,h} + Σ_{u≤h} FCF_u − M_h − U_h − C_min.
- E76. FundingNeed_h = max(0, −G_h); MaturityShare_h = M_h / D_0.
- E77. ΔI = Σ_k D_{refi,k} (c_{new,k} − c_{old,k}).

Definitions: FCF_u for non-overlapping buckets, not overlapping TTM. M_h, U_h cumulative principal retirement and other uses through h, net of amounts already in FCF. A_{drawable,h} accessible undrawn capacity counted once. C_min minimum operating cash. R118. "This is a capacity screen: drawing a facility creates debt and interest in the subsequent forecast." Use the minimum gap across monthly or finer buckets. Account for borrowing bases, covenants, restricted subsidiaries, committed against uncommitted lines, springing maturities. R119. E77 is for a fixed amount refinanced for a full year; prorate by dates; add fees, floors, resets, hedge expiry. "The core signal is the effect on coverage, FCF and liquidity, not the coupon change in isolation." Do not mix the funding-gap and full-refinancing scenarios.

### 11.6 Covenant headroom and policy risk

- E78. H_L = L_max − D_cov / E_cov.
- E79. DeclineToBreach = 1 − D_cov / (L_max E_cov).
- E80. H_C = Coverage_cov − Coverage_min.

R120. E79 holds debt and definitions fixed and needs positive EBITDA; a negative value means the simple test is already breached; it does not prove a legal breach. Incurrence covenants restrict new actions; they do not trigger default from existing leverage. R121. Track debt-funded distributions, primary equity proceeds received, debt retired, acquisitions, asset transfers, new senior claims. "Avoid adding overlapping basket capacities as though all were independently available." "An IPO dominated by secondary sales can enrich existing owners without providing issuer cash."

### 11.7 Credit-behavior features

- E81. Util^(m)_{i,t} = (1/m) Σ_{u=0}^{m−1} Drawn_{i,t−u} / Granted_{i,t−u}.
- E82. OverdraftMonths_{i,t} = Σ_{u=0}^{5} 1{Overdraft_{i,t−u} > 0}.
- E83. UnpaidSales_{i,t} = Unpaid^(6m)_{i,t} / Sales_{i,t}.
- E84. BankWithdrawal_{i,t} = 1{n^banks_{i,t} < n^banks_{i,t−6m}}.

Source windows: three months for current-account revolvers, six for other facilities. R122. "No facility is distinct from zero utilization." For public HY use disclosed drawn and drawable revolver amounts, changes, covenant status and payment incidents. Absolute undrawn capacity matters: "two firms at 80% utilization can have very different cash buffers." Behavioral variables may matter less for large, diversified-funding firms.

**(d) Inputs, Section 11.** Statements [D]; adjustments [J]; covenant EBITDA [Doc]; revolver capacity and draw [D] partly, [Doc] for conditions; maturity ladder [D]; new coupon assumptions [D] from curve plus spread; credit-register data [not available publicly].

**(f)** Scalia ch. 3, §5.4, pp. 49–65 (Table 6, p. 51); ch. 5, §3.2, pp. 117–126; ch. 9, pp. 225–230; Kricheff chs. 9–13, PDF pp. 38–76; ch. 16, pp. 94–101; ch. 18, pp. 111–114; ch. 19, pp. 116–117; ch. 24, p. 138; Gatto ch. 8, pp. 226–254.

---

## Section 12. Supporting module: bank-issuer credit analysis (p. 30–34)

**Place.** Issuer adaptation for Steps 2–5 when the borrower is a bank. "It is not the underwriting framework for ordinary corporate leveraged loans." CAMEL: capital, asset quality, management, earnings, liquidity; assess jointly; no fixed weights.

**(a) Procedure.** 12.1: peer selection by business model, franchise, country, size, accounting, asset mix, funding. Keep a dated management and control review (underwriting changes, concentration, related parties, control weaknesses, growth, distributions, reporting) with direction of concern, not a numeric score. Analyse the feedback loop: asset deterioration, credit costs, capital, funding withdrawal, asset sales, further losses, instrument terms. R123. Do not apply Scalia corporate PD coefficients to banks, bank subordinated debt or coupon-cancellation events.

**(b) Formulas.**
- E85. ROE = ROA × TotalAssets / Equity.
- E86. NI/E = (NI/A) × (A/E), average balances.
- E87. IGRC = (Net profits attributable to shareholders − Cash dividends) / Shareholders' equity.
- E88. NPL ratio (%) = 100 · NPL / TL.
- E89. NPL coverage = LLR / NPL.
- E90. Problem loans to buffers = NPL / (LLR + E).
- E91. Loan-loss coverage = Earnings before provisions and taxes / Net write-offs.
- E92. Severe-loss coverage ("dead bank ratio") = (LLR + E) / (NPL + FA + RL).
- E93. Blended recovery ratio = (C + U + H) / NPL.
- E94. Net economic loss = NPL − (C + U + H).
- E95. Liquid-assets ratio = Liquid assets / Total assets.
- E96. Liquidity ratio = Liquid assets / Short-term liabilities.
- E97. Loans to stable funds = Net loans / Stable funds.
- U36. Stable funds = Customer deposits + Official deposits + Medium/long-term liabilities + Free capital funds.
- U37. Free capital funds = E_consolidated − Minority interest − Fixed assets.
- E98. Gap_k = A_k − L_k; CumGap_K = Σ_{k≤K} Gap_k.
- E99. CET1 ratio = CET1 / RWA.
- E100. Capital headroom$ = CET1 − h_applicable RWA.
- E101. LCR = eligible HQLA / 30-day stressed net outflows.
- E102. NSFR = available stable funding / required stable funding.
- E103. Concentration HHI = Σ_g w_g².
- E104. Encumbrance = encumbered assets / total assets.

**(c) Rules.** R124. Remove exceptional gains for recurrent profitability; do not count profitability and leverage combined as independent evidence. R125. Asset-growth-minus-IGRC is "a proposed diagnostic ... not a source-prescribed formula." R126. Check whether an NPL ratio fall comes from cures, a larger denominator, charge-offs, disposals or a changed definition. Map each vendor field to an explicit denominator (total loans = face loans and advances including financial leases; gross adds unearned interest; net subtracts reserves). R127. Write-offs are a flow, NPLs a stock; not interchangeable denominators. E92 below one means buffers do not cover the assumed loss. R128. These are "loss-absorption diagnostics, not calibrated default probabilities or regulatory capital tests." R129. In E93 exclude collateral-sale proceeds from U to avoid double counting; E93 is a portfolio recovery, "not a bond-pricing formula." R130. If equity is already parent-attributable, do not deduct minority interests again. Historical stable funds is not modern NSFR ASF. R131. E98 sign is assets minus liabilities; do not mix repricing and maturity gaps; do not equate them with bond CS01 or duration. R132. E99–E104 need jurisdiction rules; h_applicable is instrument-specific; do not sum overlapping classification systems in one HHI. R133. Run a linked stress ledger; do not deduct the same reserve twice. R134. AT1 coupon cancellation is not an event of default under Basel CAP10. Model each liability by whether a guarantee or transfer protects it. R135. "A narrower spread on a protected senior claim does not prove that a subordinated claim is cheap."

**(e) Outputs.** Four conclusions: sustainable earnings and internal capital generation; loss absorption under asset-quality stress; ability to meet stressed outflows; consequences for the specific instrument.

**(d) Inputs.** Bank call reports or filings [D]; Pillar 3 capital and liquidity [D]; instrument terms [Doc]; stress shocks [J].

**(f)** Golin ch. 5, pp. 88–104; ch. 6, pp. 119–124; ch. 10, pp. 232–233; ch. 13, pp. 305–313; ch. 14, pp. 328–337; App. B, pp. 633–644; chs. 8–9, 15, 17–18; Seiz ch. 26, pp. 591–593; Basel [24]–[26].

---

## Section 13. The security: claim, options, recovery and events (p. 34–36)

### 13.1 Issuer leverage against claim protection

- E105. L_total = D_total / E_issuer.
- E106. L_{through,b} = (D_{senior to b} + D_{same rank as b}) / E_relevant.
- E107. SpreadPerTurn_b = STW_b / L_{through,b}. (bp per leverage turn; Kricheff screen on spread-to-worst.)

R136. An OAS version is an adaptation. The screen "does not control for total debt service, cash flow, duration, optionality, liquidity or recovery timing." (DataFone case, Section 20.) R137. Build the legal claim map first (opco and holdco, restricted and unrestricted subsidiaries, guarantees, collateral exclusions, lien priority, pari passu, transfer limits, structural subordination). "A company label such as 'senior notes' does not establish equivalent asset access."

### 13.2 Recovery waterfall and purchase-price economics

- E108. Recovery_b = (N_b / D_r) min(D_r, [V − Σ_{j<r} D_j]_+), [x]_+ = max(x, 0).
- E109. P^scenario = Σ_s q^P_s R_s / (1 + k_s)^{τ_s}, Σ q^P_s = 1. Recovery R_s per 100 after τ_s years; scenario rate k_s.
- U38. Immediate-recovery return = (R − P_0) / P_0, "not R/100 − 1".
- U39. Delayed annual IRR = (R / P_0)^{1/τ} − 1.
- E110. CushionOnDebt = (V − D) / D; CushionOnValue = (V − D) / V.

R138. Add accessible cash once; subtract priority costs once. "New senior financing may also supply cash or preserve operating value; modeling only the extra claim can fabricate a loss." R139. E109 is a physical-probability scenario value, "not the same measure as risk-neutral pricing." R140. The two cushions are not interchangeable and neither is a calibrated recovery forecast. Public equity value or an optimistic multiple does not replace a downside EV.

### 13.3 Calls, extension, cash-pay transitions, tenders

- E111. N_{t+h} = N_t Π_{u=t+1}^{t+h} (1 + r^PIK_u).
- E112. K_blend = Σ_j w_j K_j, Σ_j w_j = 1. (Principal fractions retired by mechanism j at price K_j.)

R141. w_j are principal fractions, "not event probabilities." If timing differs, discount full scenario cash flows. Weights respect size limits and financing capacity. "A first call date is an option held by the issuer, not a promised repayment date." A consent or exchange can cut float and liquidity. R142. Record call and no-call, extension, reset, cash-pay transition, refinancing economics after premiums and fees, and the failed-transaction case. "Yield-to-worst is a contractual yield calculation ... not a default-adjusted worst investment outcome." "A high current coupon can coexist with poor horizon returns when a premium-priced bond is called."

### 13.4 Event analysis as a pro forma balance sheet

**Source method.** Kricheff covers acquisitions, asset sales, primary equity, distributions, refinancing and ownership changes over "a roughly six-to-eighteen-month horizon" with assigned probabilities; "it does not supply empirically estimated event probabilities."
- P21. For event a, build completion and failure branches: cash and debt sources and uses, costs, acquired or sold earnings, accepted synergies, collateral and guarantee changes, expected date, legal risk.
- E113. Δŝ_{b,a} = ŝ_b(F^a, B^a, L^a, M) − ŝ_b(F^0, B^0, L^0, M).

R143. The signal is the difference between this estimate and the market response, after probability and time to completion. Separate equity dilution, sponsor proceeds and issuer proceeds. "Positive equity performance is not automatically positive credit news."

**(d) Inputs.** Debt by rank [D] for bonds, [Doc] for loans and ranking; STW [D]; EV scenarios [model]; recovery timing and discount rate [J]; call schedules, PIK terms [Doc]; event terms [Doc].

**(f)** Kricheff ch. 10, PDF pp. 50–53; chs. 13–15, pp. 72–92; ch. 16, pp. 95–101; ch. 17, pp. 103–106; ch. 18, pp. 107–114; ch. 21, pp. 123–125; ch. 23, pp. 129–136; Seiz ch. 26, pp. 590–599.

---

## Section 14. Default models, macro conditioning and expert assessment (p. 36–39)

**Place.** Support for Steps 2–4 and review. "Step 7 still requires security payoffs, prices, costs and competing investments."

### 14.1 Target and horizon

Source: Scalia forecasts a one-year default of Italian nonfinancial firms on a bank-system label (bad debt, unlikely-to-pay, overdue); at end-year T it uses T − 1 financials, October T credit data, defaults in T + 1.
- E114. y^(12m)_{i,t} = 1{specified issuer default event in (t, t + 12m]}.

R144. Document distressed exchanges, grace periods, repeated defaults, resolution, censoring. Only nondefaulted issuers with observable outcomes enter the sample. A 12-month label enters training only after its window and reporting delay mature. Calls and refinancings are security events, not defaults. Bank coupon cancellation can need a separate model.

### 14.2 Interpretable modular logit

Source: 11 financial submodels by sector and statement type; three credit-behavior models by size; four size-specific integration models; tree transforms before logistic estimation.
- E115. F_i = a_F + Σ_k β_k T_k(x_ik); B_i = a_B + Σ_j γ_j U_j(z_ij).
- E116. η_i = a + b_F F_i + b_B B_i.
- E117. p_i = σ(η_i) = 1 / (1 + exp(−η_i)); logit(p) = log(p / (1 − p)).

R145. Use the correct inverse-logit (source Eq. 4, printed p. 42, PDF p. 60); "an earlier displayed sign inconsistency should not be copied." R146. Start with a regularized logit or a parsimonious nonlinear benchmark on public features. Use sector interactions or partial pooling when sectors have few defaults. Learn bins and thresholds within training folds. Source cutoffs "are not portable rules for another HY universe."

### 14.3 Calibration separate from ranking

- E118. Δa = logit(DR_target) − logit(DR_train).
- E119. p^shifted_i = σ(η_i + Δa).
- E120. Solve δ_t: Σ_i w_i σ(η_{i,t} + δ_t) / Σ_i w_i = DR̂_t.
- E121. p_pop / (1 − p_pop) = [p_sample / (1 − p_sample)] · [π_pop / (1 − π_pop)] / [π_sample / (1 − π_sample)].

R147. E118 is an intercept shift; it preserves rank and AUC. The source used 2014–2021 target and 2015–2018 training, so its later validation is partly in sample (the chapter says so). R148. Use a separate past-only calibration sample. E120 is an extension: the logit difference of averages does not force the mean of heterogeneous PDs to the target. State whether weights are counts or exposure. R149. E121 holds only under pure outcome-based sampling; verify calibration on untouched later data at original prevalence. Disclose any probability clipping.

### 14.4 Macro conditioning and panel information

Source: a satellite model forecasts aggregate or sector default conditions and updates micro PDs; template has a statistical-PD measure, credit demand and credit rates at two-quarter lags, GDP at a four-quarter lag.
- E122. g(DR_t) = a + Σ_ℓ θ_ℓ^T m_{t−ℓ} + ε_t.

R150. The source regression and table are not fully consistent on level and change labels; reconcile before you reproduce coefficients. Show base against adverse PD. A common shift keeps within-group order; sector shifts can reorder. R151. "Do not add the same macro deterioration independently to both financial statements and PD without specifying whether one effect is incremental." Panel random-effects gains are modest in two submodels; specify initialization for new firms; they are challengers.

### 14.5 Structured expert assessment

- E123. p^expert_i = σ(η_i + Σ_j a_j z_ij).

R152. η_i is the baseline score, not a probability. If evidence cannot estimate a_j, keep reason-coded judgements; do not invent precise adjustments. P22. Each adjustment records: original prediction; new dated evidence; module; direction and materiality; alternative reading; response; reviewer; expiry or review trigger. R153. "historical backtests cannot grant undocumented hindsight vetoes only to losing observations. Test overrides against their own subsequent outcomes."

### 14.6 Stacked machine learning as a challenger

- E124. p^stack_i = σ(a + b_RF p̂^OOF_{RF,i} + b_XGB p̂^OOF_{XGB,i} + b_NN p̂^OOF_{NN,i}).

R154. Not a convex average. Train the meta-model on out-of-fold predictions, refit base learners for scoring. Use chronological folds, mature labels, issuer-aware checks. Accept complexity only if it improves out-of-time discrimination, calibration, stability and decisions against the same-data baseline. "A model with higher AUC but unstable tail probabilities is unsuitable for probability-sensitive sizing."

### 14.7 Explain disagreement before you use it

- E125. g(x) = E[g(X)] + Σ_k φ^g_k(x), with g = f_ML − f_base.
- U40. d_i = logit(p^challenger_i) − logit(p^baseline_i), both calibrated to the same target.

R155. Keep the expected baseline difference. State the output scale and background distribution. SHAP "does not establish causality or prove the bond is mispriced." R156. Align horizon, default definition, PIT against TTC, borrower, information date and selection before you read a PD gap (IRB and ICAS study). d_i "is a discrepancy on a score scale, not basis points of cheapness."

**(d) Inputs.** Default labels [D] (need a public-bond default event set); public features [D]; target default-rate forecast [D] (agency forecasts are licensed); macro series [D]; expert evidence [J].

**(f)** Scalia [8] §5.1–5.5, §7, pp. 40–74; [9] §2–4, pp. 87–99; [10] §3.2, pp. 117–126; [11] §3.5, §6, App. D, pp. 274–288; [18] §3–5, pp. 237–250.

---

## Section 15. Forward information: text, governance and climate (p. 39–41)

**Place.** Evidence for Step 2 and Step 4. Admit a new feature only when its creditor channel and incremental evidence exist.

- E126. A_{m,k,i,t} = (1/|N_{i,t}|) Σ_{a∈N_{i,t}} X_{m,k,a}; M_{m,k,i,t} = max_{a∈N_{i,t}} X_{m,k,a}. Six-month article set.
- E127. LayoffRate = annual dismissals / employees with permanent contracts.
- E128. TurnoverRate = (annual hires + annual terminations) / average employees.
- E129. FixedTermRate = fixed-term employees / average employees.
- E130. s_S = −3.44 + 3.09 LayoffRate + 0.14 TurnoverRate − 0.19 WageQuartile + 0.12 1{TurnoverRate = 0}.
- E131. p_S = σ(s_S).
- E132. p^augmented_i = σ(a + b_F F*_i + b_B B*_i + b_S S*_i + b_G G*_i), S = logit(p_S), G = logit(p_G), stars = normalized.
- U41. H_{i,s} = Σ_v w_iv h_{v,s}, weights sum to one over a declared perimeter.
- E133. ΔCF_{i,s} = −LostOperatingCash_{i,s} − RepairCash_{i,s} + InsuranceReceipts_{i,s} − AdaptationCapex_{i,s}.
- U42. Δp_{i,s} = p(F_{i,s}) − p(F_{i,0}).
- E134. EC_i = ExtraEUA_i (P̂^EUA_{t+1} − P^EUA_t).

**Rules.** R157. Keep article count, no-news flag, coverage, dedup status, entity confidence. "No news is not the same state as neutral news." The max of a one-hot bad class and the max of a probability mean different things. P23. Structured credit-event record: type; issuer and entity; publication time; completion time; source passage; cash and debt effect; collateral or covenant effect; analyst check. R158. "An LLM pretrained after historical events may contain later knowledge"; a historical test needs a model-vintage design or a contamination assessment. R159. Social data have a two-year lag; several governance variables and the knowledge graph are not public. E130 is "an empirical illustration, not a ready-to-use HY model." Do not put raw PDs into coefficients that expect normalized scores. Governance is excluded from the source medium and large models; large-firm social gain is not significant. R160. Headquarters need not represent operating assets. A weighted hazard score "is not a PD and is not an expected loss." Do not deduct an accounting impairment again as cash. R161. ExtraEUA is the signed quantity relative to free allocation, "not automatically all reported carbon emissions"; check scheme membership; "A regulatory allowance price shock is not a universal tax on all Scope 1–3 emissions." R162. Cyber: the source "explicitly leaves the mapping from cyber exposure to creditworthiness for future work." Disclosure intensity is not exposure. R163 (15.6, admission rule). A feature enters production only with: a stable definition; lawful accessible data; historical publication timestamps; a missingness policy; a plausible credit channel; incremental out-of-time evidence; a monitoring rule. Keep negative findings.

**(d) Inputs.** News with first-seen times [D, licensed]; workforce and governance data [D, mostly not public in the US]; asset locations and hazards [D] plus [J]; EUA prices and allocations [D].

**(f)** Scalia [12] §5, pp. 422–425; [13] §3–4, App. A, pp. 380–406; [14] §6, pp. 162–167; [15] pp. 293–344; [16] §4, Eq. 6, p. 358; [17] pp. 439–440; Kricheff chs. 16–19, PDF pp. 94–117.

---

## Section 16. From credit assessment to fair bond value (p. 42–44)

**Place.** Valuation support for Step 7. OAS, peer residuals and issuer curves "diagnose compensation"; the final choice uses E51.

- E135. E^P[Π_H] = Σ_ω q^P_ω [V_{H,ω} − V_0 + CF_{0:H,ω} + Π^hedge_{H,ω} − Financing_ω − Borrow_ω − TradingCost_ω].
- E136. EL^P_H = PD^P_H × LGD_H × EAD_H.
- U43. S^P(T) = exp[−∫_0^T λ^P(u) du]; PD^P(0, T) = 1 − S^P(T).
- E137. ŝ_{b,t} = f(F_{i,t}, p^P_{i,t}, B_{b,t}, L_{b,t}, M_t).
- E138. e_{b,t} = s^market_{b,t} − ŝ^fair_{b,t}.
- U44. Issuer curve: s_b = α_i + g_i(tenor_b) + θ^T B_b + ε_b.
- E139. P^Q_b = Σ_{k=1}^n C_k D(t_k) S^Q(t_k) + 100 D(T) S^Q(T) + 100 R_b ∫_0^T D(u) λ^Q(u) S^Q(u) du.
- U45. e^P_b = P̂_b − P^executable_b.
- E140. Z^RV_{b,t} = e_{b,t} / u_{b,t}.
- E141. R_conv ≈ D_s q e 10^−4; e_cost = c / (D_s q) × 10^4.

**Rules.**
- R164. Full scenario repricing avoids overlapping carry, roll-down and pull-to-par pieces. Use reference marks with all execution differences in TradingCost, or executable values with only costs not already embedded. Partial scenario coverage gives a conditional result. Calls and principal enter cash flows. "Default and recovery enter scenario cash flows or terminal claim value, so expected loss is not subtracted again." A dollar P&L on different capital is not a comparable return.
- R165. E136 "is an exposure-based expected-loss approximation ... not a bond-spread model. A bond bought below or above par has different purchase-price return economics." "Do not translate a 12-month issuer PD into an OAS by simply multiplying by LGD, and do not infer a physical PD by dividing OAS by LGD."
- R166. "A one-year point estimate alone does not identify a five-year term structure." Pricing hazards λ^Q "use a different measure and can absorb premiums and model errors."
- R167. OAS: one analytics convention across candidates; keep YTW and price as diagnostics; spread duration and rate duration differ. Archive the analytics version. Separate a volatility or exercise-model change from a change in credit compensation. Prefer full repricing for large moves, premium callables and changing exercise regimes.
- R168. Fair-spread model: F normalized fundamentals; p^P calibrated PD "if useful"; B rank, currency, tenor, optionality; L liquidity; M market and sector compensation. Fit bank and nonfinancial separately; handle distressed separately. "PD and its underlying financials can be redundant; test whether the PD summary adds anything." Start with regularized linear or additive in OAS bp, or log s; log retransformation is not unbiased. Date effects in a historical fit cannot be known for a future date; estimate current compensation from contemporaneous peers or factors.
- R169. Positive e = wider than model = cheapness candidate, "subject to omitted credit, option, legal, liquidity and stale-price explanations." "Do not feed the same bond's current price or yield into the model in a way that reconstructs OAS through an identity."
- R170. Peer model: separate issuer and issue ratings; keep outlook and watch dates; "rating notches are ordinal, not equal PD intervals." Use issuer weights so one issuer with many bonds does not dominate.
- R171. Issuer curve: fit the same legal, guarantee, rank class and currency; allow for calls and liquidity; prefer a price-based curve when spreads are not comparable. "a bond should not validate its own residual" (leave one out). Shrink sparse curves toward peer curves.
- R172. Deep-discount bonds: coupon differences distort spread and yield ranks; fit survival and recovery or scenario prices; read the residual in price or expected return.
- R173. E139 assumes deterministic discounting, survival-contingent coupons and immediate fractional recovery of par. Use Section 13 waterfall and timing to challenge R_b. "An attractive point estimate that disappears under a modest recovery haircut should receive a different risk budget from a robust discrepancy."
- R174. u is a documented positive fair-value error scale from past out-of-time residuals by sector, rating, tenor and liquidity segment; Z^RV "is not automatically a normal-distribution z-score." "Large unexplained residuals can be model failures rather than strong trades."
- R175. E141 is only the conditional convergence part; it excludes carry, default, market repricing and hedges. c is all-in cost as a fraction of purchase value; D_s q > 0. Estimate or stress q from prior evidence; "do not assume every residual closes." "When no credible convergence mechanism exists, a cost hurdle alone is insufficient."

**(d) Inputs.** Scenario values [model]; OAS [D, needs call schedule and vol model]; spread duration [D]; fundamentals [D]; liquidity [D]; peer set [J]; costs c [D]; convergence fraction q [J or estimated]; recovery R_b [J or model].

**(f)** ICE [23]; Martin [27]; Golin ch. 5, pp. 88–104; pp. 532–533, 553–554; Seiz ch. 26, pp. 585–598; Kricheff ch. 23, PDF pp. 133–136.

---

## Section 17. Signal catalogue: hypotheses and rejection tests (p. 44–47)

**Place.** Candidate generation for Step 7. "No entry is asserted to be profitable." "Fundamental features explain risk; a signal additionally requires a mismatch between compensation and risk or a predictable change in that mismatch." Each candidate needs horizon, catalyst, executable expression and a reason it might be wrong.

| ID | Signal | Formula | Reject if |
| --- | --- | --- | --- |
| S1 | Fundamental peer value | e = s − ŝ; Z^RV = e/u (E138, E140), with credit, claim, option, liquidity controls | Executable prices remove the edge; an omitted risk explains it; later residuals do not predict net relative returns |
| S2 | Issuer-curve value | U46. e^curve_b = s_b − ŝ_{i,−b}(tenor_b, B_b), or a leave-one-out price residual | Gap follows different guarantees, calls or settlement; too few curve points; convergence fails under costs |
| S3 | Credit improvement not in price | E142. I^lag_{b,t} = Δs^market_{b,t} − Δŝ^fair_{b,t} = Δe_{b,t}, over matched windows with market controls | Information was available earlier; market move mismeasured; model overreacts to transitory earnings |
| S4 | Refinancing burden against spread | Joint: ΔI/E, stressed FCF/D, min_h G_h, H_L; fair value before and after realistic refinancing cost | Facilities, assets or cash cover the need; price already reflects the adverse case |
| S5 | Cash-quality discrepancy | Normalized minus reported leverage; add-back dependence (E71); cash conversion (E72); FCF/D | Adjustments substantiated; temporary uses reverse; no information beyond credit controls |
| S6 | Bank growth, asset quality, funding | Asset growth − IGRC; ΔNPL coverage; NPL/(LLR + E); capital headroom; encumbrance; cumulative gaps. "a diagnostic vector, not an unestimated weighted score" | NPL ratio falls by denominator growth while buffers and liquidity worsen (for improvement thesis); capital, cures and funding offset (for bear thesis) |
| S7 | Capital-structure RV | E143. G_rank = (s_J − s_S) − (ŝ_J − ŝ_S); scenario-price gaps in distress | Legal rights uncertain; priming capacity omitted; gain needs an implausible recovery order |
| S8 | Call and extension value | U47. E^P[R_A] − E^P[R_B] across call, tender, extension scenarios | No call capacity; premiums and fees kill issuer incentive; benefit fails under extension and rate or spread stress |
| S9 | Event pro forma value | Event-adjusted fair-price change (E113) against market response, weighted over completion and failure | Secondary owner sale; proceeds distributed; completion risk dominates; new terms hurt the target bond |
| S10 | Model disagreement (review signal) | d_i (U40), persistence, drivers | Different labels, calibration periods, regulatory conservatism, missing data, selection. "Only incremental return testing can promote the review flag" |
| S11 | New credit information from text | Six-month adverse means and maxima (E126), changes, verified event types, novelty, coverage | Stale, duplicate, wrong entity, already in data, equity sentiment only |
| S12 | Temporary technical dislocation | E144. Shock_{b,t} = Δs_{b,t} − β̂_{b,t−1} Δs_{sector,t}; then supply, selling, turnover, quote dispersion, post-shock residual | New credit news; permanent liquidity loss; stale marks; investor-base change |
| S12b | Gatto spread retracement | U48. SpreadRetracement_t = (s_{observed peak} − s_t) / (s_{observed peak} − s_{pre shock}); Macy's (1095 − 823)/(1095 − 369) = 37.47% | Use only peaks and reference dates observable at decision time; adjust for rates, duration, liquidity, changed structure. "not a buy signal by itself" |
| S13 | Stress-resilient RV | U49. min_{s∈S} R^net_{b,s}, or expected return subject to scenario-loss limits. "a portfolio preference, not a source-published alpha" | Advantage depends on unverified support, optimistic refinancing, or correlated shocks treated as independent |
| S14 | Forward-demand divergence | Book-to-bill, g^orders − g^revenue, backlog depletion, organic cc growth, ΔDSO, ΔDIO, allowance ratio; reforecast drivers first | Seasonality, benign backlog conversion, acquisition scope, cancellation accounting, known product cycle, already in price |
| S15 | Plan allocation against economic recovery | Value cash, new debt, equity, warrants per claim per outcome (E62); compare with purchase cost, discounted, with new-money obligations, dilution, negotiation risk, delay | Thesis assumes ownership changes with analyst value; treats new-debt face as cash; omits competing claims; cannot fund the path |

17.5 rules. R176. A residual, event, cash-quality gap or refinancing change "can generate a candidate; it is not a universal prerequisite or final decision rule." Use ablation. R177. "Do not average arbitrary z-scores with opposite economic meanings and call the result a validated composite." P24. Entry record: eligible security; public information snapshot; completed underwriting; legal and option review; fair-value interval; executable price; net-return scenarios; best feasible alternative; catalyst and horizon; model and liquidity uncertainty; hedge; risk budget; rejection and exit conditions. R178. "No universal residual, PD or coverage cutoff is claimed from the books." Thresholds are estimated or set as explicit risk policy on development data.

**(f)** Gatto chs. 7–10, pp. 202–316; ch. 19, pp. 519–523; chs. 15–17; Seiz ch. 26, pp. 588–598; Golin ch. 5.

---

## Section 18. Portfolio construction, hedging and execution (p. 47–49)

- E145. D_s = −(1/P_d) ∂P_d/∂s; CS01 = MV_d D_s 10^−4. (s in decimals.)
- E146. MV_L D_{s,L} ≈ MV_S D_{s,S}; N_S = N_L (P_{d,L} D_{s,L}) / (P_{d,S} D_{s,S}).
- E147. DTS = D_s s; ΔP/P ≈ −DTS Δs/s.
- E148. Π^convergence = 40(300) + 10(300) = $15,000. (Bond A OAS 600 against fair 520; B 500 against 520; D_s = 3.0 each; $1 million each leg; CS01 = $300 per bp; A tightens 40, B widens 10.) "0.75% of $2 million gross exposure before carry, execution, financing, borrow."
- E149. JTD_b = N_b (P_{d,b}/100 − R_b).
- E150. max_w µ_gross^T w − (γ/2) w^T Σ w − C(w − w_old) − F(w) − B(w).

**Rules.** R179. CS01 is the approximate loss on a long for +1 bp. For complex securities bump and reprice. Rate DV01 and key rates need separate curve bumps. R180. E146 "does not neutralize rates, sector beta, currency, liquidity or jump-to-default." CS01 targets equal absolute moves; DTS targets proportional moves; choose which exposure to isolate. R181. E149 is an event scenario, not an expected loss; it can be negative. Stress both legs together for common-issuer default; do not assume an immediate gain on the short or equal recovery across ranks. R182. Size from several limits: expected return and uncertainty; issuer loss under adverse recovery; sector and country concentration; rate and credit beta; liquidation capacity; funding and margin; borrow. "Correlated defaults and liquidity deterioration can dominate small daily spread risk." A bank capital trigger needs its own scenario. R183. E150: if costs are already in µ, do not deduct again. Σ under-represents default and stressed liquidity; add those limits. Include a cash holding and a self-financing constraint. Constrain gross, net, issuer, sector, rate, CS01, beta, currency, stressed loss, margin, liquidity. No short without confirmed borrow. Penalize turnover and uncertain values. "A simpler ranking with explicit risk limits is preferable until inputs support a reliable optimizer." "the optimizer must not force capital into a trade when cash or retention is preferable." R184. Long-only: test switches and active weights against a benchmark, including the return of the security sold. Index or futures hedges leave single-name, recovery, sector and basis risk. R185 (18.5). Cost at intended size and timing: bid-ask, impact, fees, financing, borrow and recall, hedge spreads, exit. Short coupon is a negative cash flow; do not deduct it twice. Separate transaction prices from executable quotes. Coefficients for a cost model "require execution data." Value at actual buy ask and sell bid; cost both legs at entry and exit; do not net long and short financing unless agreements permit. Limit size by executable depth and liquidation horizon. Track implementation shortfall. R186 (18.6). Write exit rules at entry: residual closes; catalyst occurs or fails; horizon ends; credit or funding deterioration; legal or call change; borrow lost; risk limit binds. "A valuation stop prompts reassessment, while a market-price stop ... cannot guarantee a loss cap in a gapping or illiquid market." Refresh both sides. Attribute P&L to rates, broad credit, issuer and curve, carry, event and recovery, execution, financing, residual; categories must sum to actual P&L.

**(d) Inputs.** Dirty price, accrued, spread, duration [D]; recovery [J or model]; covariance Σ [D]; risk aversion γ [J]; costs [D]; borrow [D].

**(f)** MSCI DTS [28]; ICE [23].

---

## Section 19. What the source studies actually establish (p. 49–51)

"None is a demonstrated HY bond relative-value backtest."

| Study | Result as stated | Limits stated by the PDF |
| --- | --- | --- |
| Statistical model (Table 12) | Binary-default AUC 0.876 to 0.885 (Dec 2018) and 0.833 to 0.845 (Dec 2020) | 2014–2021 calibration overlaps later validation; the chapter says so |
| Expert assessment | 25,000+ records 2016–2022; AUC 85.3% statistical to 87.0% full | Expert can be more conservative without better calibration; not every year improves; sample ends before the 2024 Bayesian method. "Do not translate a 1.7 percentage-point AUC improvement into spread compression or portfolio return." Sequential attribution depends on order |
| Stacked ML | ~2.5 million obs 2014–2023; train 2015–2019 plus 2022; AUC baseline to stacked: 2014 financial 0.737 to 0.764 (+2.7); 2023 financial 0.755 to 0.791 (+3.6); 2023 credit behavior 0.823 to 0.839 (+1.6); 2014 complete 0.874 to 0.880 (+0.6); 2023 complete 0.854 to 0.873 (+1.9); 2020 0.872 to 0.885 (+1.3); 2021 0.838 to 0.852 (+1.4). 2023 complete 95% interval for the difference 0.017–0.021 | 2014 and pandemic tests are retrospective, not forward-only (training includes 2022); Italian nonfinancial firms, not HY; no calibration fix after undersampling; "no execution, hedge, financing or bond-return experiment is reported" |
| Model-review cases | Industrial: baseline PD 0.51% against meta 1.57% (difference 1.06 pp); drivers interest/EBITDA, days payable, CF/sales. Medium/large: 0.99% against 2.42%; drivers overdraft persistence, unpaid receivables/sales, utilization | No subsequent default or trading profit reported. "Model disagreement itself is not a buy/sell direction" |
| News sentiment | 2016–2020; 6,006 firms; 351,755 firm-months; S-ICAS 86.2%, combined 87.1%, news alone 65.1% (matched ensemble) | Coverage selection, window and model selection, LLM vintage need scrutiny |
| Social and governance | 2023 AUC micro 84.1 to 84.9; small 86.5 to 87.4; medium 87.5 to 88.3; large 90.4 to 90.8 "statistically insignificant" | Governance excluded from medium and large models; some high-risk classes underpredict |
| Macro and panel | Common PD shift does not change AUC; panel AUC 86.05 to 86.33 and 75.38 to 75.49 | Two submodels only; new-firm treatment open |
| IRB and ICAS | Pledge coefficient on log-PD ratio about −0.40 to −0.23 (bank controls) to −0.027 (bank and rating-class controls) | Regression coefficients, not yield or return units |
| Climate survey | 577 responses of 1,102 contacted; adverse carbon scenario downgrades 14% (sector proxy) against 25% (granular) | Scenario output, not realized migration; response selection |
| Cyber | Taxonomy and extraction method | Credit mapping left for future work |

Evidence standard (quoted box): "AUC measures ordering of default risk. Calibration measures the probability level. A scenario study measures the output of assumptions. A worked example checks economic arithmetic. A profitable relative-value methodology additionally needs actual later-period bond outcomes, executable prices, hedges and costs."

**(f)** Scalia [8] §7, pp. 73–74; [10] §4, pp. 126–129; [11] §3–4, §6.2, App. C, App. E, pp. 267–290; [12] §3, §6.5, pp. 414–432; [13] pp. 379, 399–402; [9] §3–4, Table 4.5, pp. 92–99; [18] §5, pp. 245–250; [14] pp. 146–166; [17] p. 440.

---

## Section 20. Worked credit and relative-value cases (p. 51–59)

Cases A–C are Kricheff teaching examples recalculated. Cases D–H and I are original hypothetical applications. J is Gatto's 2025 article. K–M are Gatto book cases. "They are arithmetic and decision examples, not observed trades, forecasts or backtests."

| Case | Content and numbers | Method lesson |
| --- | --- | --- |
| A. Unchanged leverage, weaker cash (Kricheff Table 18-2) | Loan 1,000 refinances 3% to 6%; senior notes 400 at 8%; sub 250 at 10%. Debt 1,650; EBITDA 180; cash interest 87 to 117; capex 30, tax 0, WC 3; FCF 60 to 30; Debt/EBITDA 9.17x both; EBITDA/cash interest 2.07x to 1.54x; FCF/debt 3.64% to 1.82%. U50: ΔI = 1,000(6% − 3%) = 30 | "A leverage-only fair-value model misses the deterioration." Add refinancing calendar and funding-cost stress |
| B. Spread-per-turn trap (Kricheff Table 21-1) | DataFone: STW 475; bond-level lev 3.5x; total 7.0x; FCF/debt 0.1%; EV/EBITDA 7.1x; spread per turn 135.7. Phone Inc.: 300; 3.5x; 3.5x; 5.0%; 7.0x; 85.7. U51: value cushion (7.1 − 7.0)/7.1 = 1.41% against (7.0 − 3.5)/7.0 = 50% | Pair claim-level protection with whole-issuer debt service before you read spread as value. STW is not OAS |
| C. Recovery is not today's price (Kricheff ch. 23) | E151. P_0 = 50 / 1.20² = 34.72. Extension: 50/1.20³ = 28.94 | Include reorganization time, cash burn, liquidity of distributed securities |
| D. Bank case (original) | Bank A 430 bp against peer 350. Assets 1,000 to 1,200; equity 80 to 84; loans 600 to 750; NPLs 60 to 66; LLR 24 to 24; liquid assets 240 to 180; ST liabilities 300 to 400; NI 10 to 11; dividends 10 to 7. ROA 1.00%; ROE 12.50% to 13.41%; IGRC 4/82 = 4.88%; equity growth 5% against 20% asset growth; equity/assets 8% to 7%; NPL ratio 10.00% to 8.80%; coverage 40.00% to 36.36%; NPL/(LLR + E) 57.69% to 61.11%. Recovery 12 + 8 + 6 = 26; loss 40; incremental provision 16. E152. NI^stress = 11 − 16 = −5; E^stress = 84 − 16 = 68. E153. A^stress = 1,184; E/A = 5.74%. Liquidity: liquid/assets 24% to 15%; liquid/ST 80% to 45%; 40 pledged; 10% haircut on 140 gives 126; outflows 160; shortfall 34 | Higher ROE, lower NPL ratio and 80 bp more do not establish value. "this case does not invent a fair OAS or PD" |
| E. Equal headline leverage, unequal resilience (original) | Debt 600; mgmt EBITDA 120 (5.0x); rejected add-backs 5 (A) and 25 (B); interest 45; taxes 8. A: EBITDA 115, capex 30, WC 5, lev 5.22x, cov 2.56x, after-capex 1.89x, FCF 27, FCF/D 4.50%. B: 95, 40, 20, 6.32x, 2.11x, 1.22x, −18, −3.00%. Refi 180 from 6% to 11%: interest +9 to 54; FCF 18 and −27; with EBITDA −15%: FCF 0.75 and −41.25; after-capex coverage 1.25x and 0.75x | "Equal reported leverage is insufficient for equal fair spreads." "Cash weakness is not itself a short signal if the price already reflects it" |
| F. Same issuer, different claims (original) | Secured loan 300 at 95; junior bonds 400 at 55; cash +40; costs ahead −60. EV 250, 450, 650: distributable 230, 430, 630; loan 230, 300, 300; bond 0, 130, 330; per 100: loan 76.67, 100, 100; bond 0, 32.50, 82.50; returns loan −19.30%, +5.26%, +5.26%; bond −100.00%, −40.91%, +50.00%. U52: IRR (100/95)^{1/2} − 1 = 2.60%; PV at 10% = 100/1.1² = 82.64 | "A bond at 55 is not cheap merely because it is below par." A loan that gets par later can still return poorly at its price |
| G. Better PD, less RV (original) | A prev: PD 6%, fair 550, market 600, residual +50; A now: 4%, 450, 480, +30; B now: 5%, 500, 580, +80. D_s 3.0 and 2.5; error scales 45 and 35; costs 0.50% and 0.40%; q = 0.5. E154. R^A_conv − c_A = 3(0.5)(30)10^−4 − 0.005 = −0.05%. E155. R^B_conv − c_B = 2.5(0.5)(80)10^−4 − 0.004 = +0.60%. Residual/error 0.67 and 2.29; cost hurdles 33.33 and 32 bp | Credit improvement can come with less relative value. "B merits further investigation, not a claim of positive unconditional return" |
| H. Coupon defeated by call (original) | A costs 106, coupon 8; B costs 99, coupon 7; six months. E156. R_A,call = (102 + 4 − 106)/106 = 0. E157. R_A,no call = (105 + 4 − 106)/106 = 2.83%. E158. E[R_A | no default] = 0.75(0) + 0.25(2.83%) = 0.71%. E159. R_B = (99 + 3.5 − 99)/99 = 3.54%. Current yield A 7.55% against B 7.07% | Horizon assumptions favor B despite the higher current yield |
| I. Loan, bond, peer or cash (original Step 7) | A loan 300 and junior bond 200; resolution value 220 + 20 − 40 = 200, loan recovery 66.6667%, bond 0. Loan cost 100.5 all-in, coupon 9, terminal 100, 100, 94; bond cost 90.9, coupon 10, terminal 101, 100, 65. Probabilities 20%, 60%, 15%, 5%. Receipts per 100: loan 109, 109, 103, 66.6667; bond 111, 110, 75, 0. B bond returns 10%, 8%, 3%, −20%; cash 4%. E160. R^loan_resolution = 66.6667/100.5 − 1 = −33.6650%. E161. R^bond_base = 110/90.9 − 1 = 21.0121%. Results: expected net return loan 5.4561%, A bond 9.4059%, B bond 6.2500%, cash 4.0000%; excess over cash 1.4561%, 5.4059%, 2.2500%, 0; P(capital loss) 5%, 20%, 5%, 0; P(below cash) 20%, 20%, 20%, 0; 95% ES of capital loss 33.6650%, 100%, 20%, 0. Budget: 95% ES ≤ 25%; both A claims fail; B and cash admissible. Mix 93.75% B and 6.25% A bond: E162. ES95% = 0.9375(20%) + 0.0625(100%) = 25%. E163. E[R^mix] = 0.9375(6.25%) + 0.0625(9.4059%) = 6.4472% | The ES addition works only because the same 5% state is the worst for both; "not a general identity for portfolio ES." B is best standalone; the mix improves it when feasible; neither is "globally optimal across unexamined portfolios" |
| J. Acquisition-masked contraction (Gatto 2025 article) | E164. g^reported = 160,549/155,120 − 1 = 3.50%. E165. g^organic = (160,549 − 25,000)/155,120 − 1 = −12.62% | Reconcile perimeter, timing and FX first; "not a verified 2023-book case or a validated trading signal" |
| K. VCC (Gatto book) | $200m term loan, LIBOR + 700, 1.5% floor, 2.25% OID, 2.5% annual amortization, $20m first-out revolver; maturity springs to six months before material sub debt; mezz due Dec 2022; noncall 12 months then 102, 101, par; ECF sweep. Closing secured 200, cash 12.1, mezz 85.7: gross debt 285.7, net 273.6, projected EBITDA 37.5, net leverage 7.30x. E166. CashBeforePrincipal = 37.5 − 4.2 − 17.0 − 2.3 − 1.5 = 12.5. E167. CashAfterAmortization = 12.5 − 5.0 = 7.5. Rating estimate B/B− loan, CCC+ corporate; 50–100 bp premium plus tighter covenants judged attractive. Repayment IRR year 1 to maturity: 14.6%, 11.7%, 10.2%, 9.7%, 9.5%; money multiple 1.14, 1.22, 1.28, 1.35, 1.43. Postmortem: EBITDA about $43m by March 2021; $70m upsizing April 2021; $631m sale; repaid at 101; reported IRR 10.6% | Source calls 273.6 "total debt" though net of cash; calls 7.5 "free cash flow" though after principal; forecasts omit the required ECF sweep. The 10.6% is "an origination-relationship result, not the return of a generic secondary purchase" |
| L. HCA (Gatto book) | YTW, spread, through-leverage: HCA cash-pay 2L 2014 9.125%, 449, 4.8x; TLB 7.650%, 225, 3.5x; PIK 2L 2016 9.625%, 499, 4.8x; unsecured 2016 9.730%, 509, 6.5x; Tenet unsecured 2014 9.875%, 524, 6.9x; BB index 7.030%, 241; B index 8.140%, 353; Healthcare index 8.820%, 415. Judgements: 224 bp pickup over TLB adequate for ~1.3 more turns; PIK 50 bp insufficient for two more years and deferral option; unsecured 60 bp insufficient where cumulative LTV goes ~63% to 85%; Tenet 75 bp insufficient for higher leverage, weaker rating, no collateral. Bonds have subsidiary guarantees, second priority on some pools, third on ABL collateral. Forecast assumes 100% of FCF repays first-lien though the sweep is 50%. Postmortem: called at 104.56 in June 2011; about 10% annualized against 8.9% for the HY index; March 2009 trough 77 against 55 for the index | The column is labelled "Spread", not OAS; align quote convention, tenor, options, liquidity, funding before you attribute differences to credit. The 100% FCF sweep "is a management-policy assumption to stress, not an unconditional creditor right." One case "does not establish a profitable general trading rule" |
| M. Quinn (Gatto appendix, no solution) | OpCo senior EUR450m at 8.5% cash; HoldCo EUR900m at 7.5% PIK with stapled equity and control; HoldCo trades at 8. Sale of Building Products and Packaging for EUR85m to enable a Glass sale. Glass EUR60m EBITDA at 6.1–6.5x; Plastics EUR15m at 7.5x; Radiators zero EBITDA, liquidation EUR17.5–22.5m net | Model sale completion, delay, senior cash interest, costs, funding, control strategy. "Any chosen probability, discount rate or purchase-price answer is our worked analysis; the appendix does not provide one" |

**(f)** Kricheff ch. 18, Table 18-2, PDF p. 114; ch. 21, Table 21-1, pp. 123–124; ch. 23, p. 136; chs. 9–15, 23; Golin ch. 6, ch. 10, ch. 14, App. B; Gatto 2025 [2]; Gatto ch. 13, PDF pp. 370–414; appendix pp. 577–584.

---

## Section 21. Validation, monitoring and implementation (p. 60–63)

**21.1 Three layers.**

| Layer | Question and metrics | Failure that blocks promotion |
| --- | --- | --- |
| Issuer credit | Rank and level of future defaults: AUC, precision and recall, Brier, log loss, calibration, tail and subgroup stability | Strong AUC with unreliable probabilities; unavailable inputs; stale or leaked labels; poor performance in the target HY population |
| Security valuation | Comparable compensation and claim differences: later spread and price errors, segment bias, intervals, monotonicity, scenario plausibility | Own-price target reconstruction; persistent errors by rank, call or liquidity; unexplained extreme residuals; cannot price legal events |
| Trading implementation | Net returns under constraints: net P&L, drawdown, exposures, turnover, costs, capacity, default and event losses | Mid-price gains vanish at executable prices; returns are beta or carry; borrow or liquidity unavailable; gains depend on few names or hindsight |

**21.2 Default metrics.**
- E168. Brier = (1/N) Σ_i (p_i − y_i)².
- E169. LogLoss = −(1/N) Σ_i [y_i log p_i + (1 − y_i) log(1 − p_i)].
- E170. O/E = Σ_i y_i / Σ_i p_i.
- U53. AUC = Pr(p_D > p_N) + ½ Pr(p_D = p_N); Gini = 2AUC − 1.
- U54. Calibration regression: logit Pr(y_i = 1) = a_c + b_c logit(p_i); ideal a_c = 0, b_c = 1.
R187. "O/E near one does not guarantee calibration within grades or risk tails." Use frozen cohorts for static-pool tests. Binomial traffic lights assume independent defaults; use sector, time and issuer-aware uncertainty when that fails. Label regulatory PDs (floors, conservatism) apart from best-estimate physical PDs.

**21.3 Chronological validation protocol.** P25, nine steps: (1) freeze the research spec: universe, labels, features, horizon, execution delay, benchmark, costs, hedge, risk budgets; (2) freeze each historical choice set: eligible alternatives, actual quotes, sizes, funding, access; same rules for chosen and rejected actions; include cash, retention, mixtures; no hindsight comparator; (3) use only matured outcomes; "A shorter return embargo does not solve an unmatured default label"; (4) train all transformations inside the split; keep a later validation period and an untouched final period; (5) generate upstream scores honestly (as of the date or out of fold); "A downstream chronological split does not repair a full-sample upstream PD model"; (6) purge overlapping outcome windows; embargo where needed; account for repeated issuers and related bonds in intervals; (7) keep failed and retired claims: defaults, exchanges, tenders, calls, recoveries, late payments, delistings; do not substitute unknown final recoveries; (8) simulate the intended implementation at a delayed executable price with borrow, funding, size limits, costs on all legs, actual coupons and actions; failed and partial fills stay; (9) evaluate later periods and regimes: expansion, recession, rising and falling rates, distressed, illiquid; held-out issuers. "These rules ... must not be claimed as already satisfied by those studies."

**21.4 Return and portfolio metrics.**
- E171. R_{0:H} = (P_{d,H} + CF_{0:H} − P_{d,0}) / P_{d,0}. (Constant face.)
- E172. R_{0:H} = (N_H P_{d,H}/100 + CF^currency_{0:H} − N_0 P_{d,0}/100) / (N_0 P_{d,0}/100). (Changing face.)
- U55. DD_t = NAV_t / max_{u≤t} NAV_u − 1.
R188. Redeemed bond: terminal value zero, principal in cash. Default: actual recovery distributions. "Subtracting expected default loss from returns already containing default losses would double count." Report valuation MAE and RMSE by sector, rank, rating, tenor, price, liquidity; bias; interval coverage. Signals: cross-sectional rank correlation with later hedged returns; monotone portfolio sorts; issuer and time-aware inference. "Do not annualize overlapping-horizon Sharpe ratios as if observations were independent." Factor-adjusted analysis "does not by itself establish a causal source of alpha."

**21.5 Baselines and ablations.** Compare with cash, the current portfolio, simple switches, mandate allocations, a rating, sector and tenor matched portfolio, raw-spread ranking, carry selection, simple issuer curves, a compact credit model. R189. Measure against the best alternative identified ex ante; "an ex-post best performer is a hindsight diagnostic, not an investable benchmark." Ablate: normalized cash flow, refinancing and covenants, bank funding and asset quality, PD model, macro overlay, expert review, text, other alternative data. Test under conservative costs, slower timing, less convergence, recovery delay, other liquidity, removal of dominant names. "A signal that only improves today's fit, or only works with inaccessible data, should not be promoted." Materiality thresholds come from the mandate.

**21.6 Monitoring.** Source: track the 10th, 25th, 50th, 75th, 90th percentiles of final, financial and behavioral PDs by sector, size, region.
- E173. T_jk(H) = #{i : rating_{i,t} = j, rating_{i,t+H} = k} / #{i : rating_{i,t} = j}.
R190. Handle default, withdrawal and missing outcomes explicitly. Use fixed score definitions across vintages. Perturbation tests; stability under alternative accounting adjustments; sensitivity to missing data. "Do not interpret a product of normalized quality scores as a calibrated probability of safe operation." Remedies: correct data; narrow the universe; cut confidence and risk; suspend a signal; recalibrate on matured data; replace a model after independent review. Keep every prior version.

**21.7 Implementation sequence.**

| Stage | Deliverable | Acceptance evidence |
| --- | --- | --- |
| 1 Data and definitions | Issuer and entity map; security master; PIT accounts; formula registry; action history | Reconciled sample issuers, cash bridges, legal claims, timestamps; no missing required options |
| 2 Seven-step underwriting | Steps 1–6 files; provisional Step 7 alternatives memo | Steps reconcile cash, debt, claim value; alternatives and open questions explicit; bank treatment where relevant |
| 3 Baseline models | Interpretable PD; calibration; bank and corporate fair-spread models; issuer curves; uncertainty scales | Later-period credit and valuation results; failure analysis; no price identity or generated-feature leakage |
| 4 Investment-selection experiment | Dated alternatives registry; common-capital payoff engine; costs; allocation rules; walk-forward portfolio | Net selection against cash, retention, alternatives; survives ablations and stresses; credible capacity and funding |
| 5 Challengers | Stacking, macro and expert additions, text, alternative data | Same-sample incremental evidence; stable calibration; research-only status if insufficient |
| 6 Controlled deployment | Shadow book, decision archive, limits, execution feedback, monitoring | Reconstructible decisions; prospective results; suspension and change-control rules |

Cadence: daily prices, actions, quote quality, borrow, risk; new filings trigger accounting and PD refresh; material events trigger legal, liquidity and pro forma re-underwriting; calibration and net results reviewed only after labels mature. P26. Keep a dated journal of all proposed trades and rejected alternatives. Gatto recommends six-month postmortems: returns, thesis realization, mistakes; attribute to carry, spread, rates, recovery, legal allocation, unexpected events.

Minimum decision standard (quoted box): "Complete Gatto's seven-step process as operationalized here. Explain what was known, why the issuer can pay, what the exact claim receives under stress, its net-return distribution at executable prices, the best feasible alternative, the reason for the allocation, and the evidence that would reverse the decision."

**(f)** Scalia [8] §6, pp. 68–73; [19] §6.1, pp. 207–209; [20] §2, pp. 178–182; [21] §3–4, pp. 20–24; Gatto ch. 19, p. 571; ch. 20, pp. 574–575.

---

## Section 22. Source coverage and reproducibility notes (p. 63–65)

**Statements.** The integrated schema, comparison engine, statistical hypotheses and allocation rules "are this report's implementation, not a claim that an author published the complete trading system or demonstrated its profitability."

**Gatto coverage.** Full 611-page reflowed ebook; detailed extraction emphasizes chs. 5–19; image formulas and tables visually checked and recomputed. No fixed offset to the 416-page print edition is assumed.

**Gatto source discrepancies the PDF corrects.** (i) Ch. 11 terminal value is discounted to the valuation date. (ii) JCP WACC: stated 60/40 debt/equity conflicts with the 40/60 exhibit that gives 15.6%; neither is a calibrated rate. (iii) VCC "total debt" 273.6 is net of 12.1 cash; gross is 285.7. (iv) VCC liquidation 101.7–123.8 is below the 200 secured claim. (v) JCP historical and downside exhibits have inconsistent cells; reconciled to chs. 7–8. Substep counts follow the figures: six in ch. 9, eight in Fig. 10.2. Turnover and intercompany claims are not a single-pool waterfall. Ch. 12 and ch. 19 describe JCP's incurrence restriction inconsistently. Short bonds are not capped at par. Several return exhibits use twice the semiannual IRR.

**Kricheff.** 165-page reflowed PDF. The p. 53 statement 1,500/250 = 3 is wrong; correct is 6. The p. 108 acquisition multiple and p. 123 CellCo leverage inconsistencies are avoided. Table 18-3 numbers missing in the supplied layout are not rebuilt.

**Golin.** Formulas carry forward the earlier verified extraction; "this revision does not claim a fresh full-volume page-by-page verification."

**Scalia.** Correct inverse logit used; intercept adjustment treated as a shift; SHAP baseline kept. The macro chapter labels the same error figures as both MSE and RMSE, so no precise performance claim is made. Provider cash flow is not relabeled CFO or FCF. S/G concentration descriptions are not treated as reproducible HHI fields.

**Other.** Bank capital and liquidity concepts, OAS and risk sensitivities are supplementary; not a verification of a jurisdiction's rules or a security's terms. Fortress's public text does not define CARV; the earlier CARV request is context only.

**Not done (quoted).** "No historical HY security panel, live quote set, borrow book, portfolio mandate or trade-cost dataset was supplied. Consequently this document provides source extraction, formulas, research hypotheses, study interpretation, verified numerical examples and a deployment specification. It does not supply fitted HY coefficients, estimated convergence probabilities, investable trade recommendations or an empirical net-return backtest."

---

## Summary of what the PDF says is not done

1. No trading backtest (cover; Section 22).
2. No fitted HY coefficients; no estimated convergence probabilities; no investable recommendations (Section 22).
3. No historical HY security panel, live quotes, borrow book, mandate, or trade-cost data (Section 22).
4. None of the source studies is an HY relative-value backtest (Section 19).
5. Golin formulas not re-verified page by page in this revision (Section 22).
6. Kricheff Table 18-3 numbers not rebuilt (Section 22).
7. Exact JCP covenant capacity not calculable from public detail (Section 10.7).
8. Quinn case has no supplied solution (Section 20.13).
9. Cyber-to-credit mapping not done by the source (Section 15.5).
10. The three JCP trades are not a synchronized executable backtest (Section 10.9).
11. Thresholds: "No universal residual, PD or coverage cutoff is claimed from the books" (Section 17.5).
12. The chronological protocol must not be claimed as already satisfied by the source studies (Section 21.3).

## Counts

| Item | Count | Range |
| --- | --- | --- |
| Numbered formulas | 173 | E1 to E173 |
| Unnumbered formulas and worked computations | 55 | U1 to U55 (U24 to U34 are the 11 rows of the Scalia dictionary) |
| Formulas in total | 228 | |
| Procedures | 26 | P1 to P26 |
| Decision rules, thresholds and prohibitions | 190 | R1 to R190 |
| Signal hypotheses | 16 | S1 to S15 plus S12b (Gatto retracement) |
| Worked cases | 13 | A to M (Section 20) plus the JCP, TM Corp, VCC, uptier, KHA and other Part I examples |
