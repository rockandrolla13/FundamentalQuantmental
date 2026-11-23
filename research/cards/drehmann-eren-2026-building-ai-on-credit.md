# Drehmann and Eren (2026), "Building AI on credit: structures and spillovers"

BIS Bulletin No 140, Bank for International Settlements, 27 October 2026 (PDF p. 1). Authors: Mathias Drehmann and Egemen Eren (PDF p. 1). We read the 8-page PDF `bisbull140.pdf` and its 2-page online annex `bisbull140_annex.pdf`. Page numbers below are PDF pages. For the main text, printed page = PDF page - 2. The annex prints the same numbers as its PDF pages. Evidence class: BIS Bulletin, staff analysis, not peer-reviewed. The views are the authors', not those of the BIS (PDF p. 2). The authors state that they used AI for research assistance and editorial work (PDF p. 2). Two companion pieces add facts below, cited as separate documents:
- B120: Aldasoro, Doerr and Rees (2026), "Financing the AI boom: from cash flows to debt", BIS Bulletin No 120, 7 January 2026, `bisbull120.pdf` (PDF p. 1). Printed page = PDF page - 2.
- QR box: "Financing the AI infrastructure boom: on- and off-balance sheet borrowing", BIS Quarterly Review, March 2026, 16 March 2026, `r_qt2603u.htm`. The HTML file names no authors. Bulletin 140 cites it as Eren, Krohn and Todorov (2026) (PDF p. 8). The HTML has no page numbers, so we cite body paragraphs 1 to 4.

## Claim
Off-balance sheet commitments from a few large firms transform the credit rating of AI data-centre debt and draw in institutional capital (PDF p. 3). The structures hide the final allocation of risk. The ultimate exposures sit with a few large firms, more than their balance sheets show (PDF p. 4). On 18 AI-financing news days in 2026, the 10-year Treasury term premium rose about 1.5 basis points. The rise reversed within two trading days. Investment-grade (IG) spreads did not change significantly (PDF pp. 7-8). The authors call these event-day associations, not causal effects (PDF p. 7, note 7).

## Method
**Structure map (PDF pp. 4-6, Graph 2).** The authors draw a stylised network from market sources and company communications. Graph 2 is the "authors' elaboration" (PDF p. 5). The section has no regression and no sample.

**Event study (PDF p. 7, annex p. 1, Table A1).** An AI news day is a session with one of four event types: hyperscaler results, a jumbo bond deal of $20 billion or more, chip vendor results, or chip vendor financing news (annex p. 2, Table A2). Releases after the 16:00 ET close count on the next session (annex p. 2).

```latex
\Delta TP^{10y}_t = \alpha + \beta\, AI_t + \gamma\, \Delta y^{2y}_t + \delta\, FOMC_t + \varepsilon_t
```

Intuition: `beta` is the extra daily move in the term premium on an AI news day, net of the move that the change in expected policy rates explains. `TP` is the Adrian, Crump and Moench (2013) 10-year term premium. `AI_t` is the news-day dummy. `FOMC_t` marks the six FOMC statement days (annex pp. 1-2). The authors use the 2-year yield change as the proxy for expected policy rates (PDF p. 7). Standard errors are Newey-West with four lags (annex p. 1). Column 5 replaces the dependent variable with the daily change in the ICE BofA US corporate IG option-adjusted spread (annex p. 1). Graph 3.B repeats the regression at each maturity of the Gürkaynak, Sack and Wright zero-coupon curve (PDF p. 7).

## Data
- Event study: 179 daily observations, 18 AI news days. Nineteen events fall on 18 sessions, because 30 April holds two events (annex pp. 1-2).
- Event list: 7 hyperscaler result events, 7 jumbo bond deals, 3 chip vendor results and 2 chip vendor financing announcements (annex p. 2, Table A2).
- Outcomes: the ACM term premium, the zero-coupon Treasury curve, and the aggregate IG OAS index (annex p. 1). The study holds no issuer-level spread, no high-yield (HY) spread, no CDS spread and no vehicle bond price.
- Structure facts: market sources, company communications and Moody's Ratings (2026) (PDF pp. 3, 5-6).
- B120 private credit data: PitchBook loans to firms in the verticals "Artificial Intelligence", "Big Data" and "Cloud Tech" (B120 PDF p. 7, Graph 3 note).

## Result
**Who owns the asset (PDF pp. 4-5).** A special purpose vehicle (SPV) owns the data centre. Its income comes from the contracts it signs. It issues a bond or an asset-backed security, often placed privately with several institutional investors.

**Who signs the contracts (PDF p. 5).** IG hyperscalers lease capacity, sometimes on short initial terms with options to renew. Some take a minority stake or give a residual-value guarantee. Neoclouds and AI labs, mostly unrated or below IG, sign similar contracts. Neoclouds also borrow against their chips, often at floating rates.

**Who lends (PDF p. 5).** Banks give construction loans to some vehicles. Banks also lend to the private credit funds that hold vehicle debt. The chip vendor holds equity in some neoclouds and buys capacity from some of them. In some cases it gives contingent support for facility lease obligations. The QR box says that vehicles raise debt through private placements, often with private credit firms. Private credit funds, insurers and other institutional investors hold the debt (QR box, paras 3-4).

**Who bears the loss (PDF p. 6).** If a hyperscaler does not renew or ends a lease early, the vehicle must find a new tenant or sell the assets. Residual-value guarantees are "typically capped". Losses fall on insurers, funds and other holders of the debt, and on their bank lenders.

**Collateral (PDF p. 5).** The ring-fenced building, power connection and cooling plant can go to other tenants. Chips have fewer other uses and may lose value with each generation. For that reason, capacity contracts and initial lease terms "typically run for a few years".

**On and off balance sheet (PDF pp. 3, 6).** Moody's puts the largest hyperscalers' data-centre lease commitments at $1.2 trillion by mid-2026. About $820 billion of that relates to leases not yet started (PDF p. 3). Aggregate off-balance sheet commitments already exceed reported debt (PDF p. 6). Leases not yet started are disclosed but not recorded as debt. Guarantees carry little or no recorded value until payment becomes likely (PDF p. 6). An unconsolidated vehicle lets a hyperscaler record its payments as operating expenses (PDF p. 6).

**Worked case (PDF pp. 5-6, notes 3 and 5).** The Hyperion data centre is a joint venture between Meta and Blue Owl managed funds. It raised $27.3 billion of privately placed, A+ rated senior secured bonds. Meta's leases begin in 2029 and run for four years initially. Renewal options extend the total term to up to 20 years. Residual-value protection is limited and covers the first 16 years. Meta does not consolidate the venture. S&P rated the bonds A+, one notch below Meta. They priced at 225 bp over Treasuries in October 2025. Two weeks later, Meta's own 20-year and 30-year bonds priced at 88 bp and 98 bp. The gap is 127 to 137 bp (our arithmetic). The source does not give the Hyperion bond maturity.

**Vendor support (PDF p. 5 note 4, annex p. 2).** NVIDIA may give residual-value support for up to 25% of a project, form unspecified. It announced guarantees of up to $105 billion for data-centre leases of an OpenAI affiliate on 17 August 2026.

**Event study (annex p. 1, Table A1).**

| Column | Dependent variable | AI news day | AI days | Obs | R2 |
| --- | --- | --- | --- | --- | --- |
| (1) baseline | Term premium | 1.53*** (0.46) | 18 | 179 | 0.11 |
| (2) 17 Jun to 18 Sep | Term premium | 2.88*** (0.64) | 8 | 65 | 0.09 |
| (3) financing news only | Term premium | 2.15*** (0.43) | 9 | 179 | 0.11 |
| (4) more controls | Term premium | 1.80*** (0.54) | 18 | 179 | 0.19 |
| (5) IG spread | IG OAS | 0.13 (0.24) | 18 | 179 | 0.04 |

The term premium moves about 3.5 bp on a typical day (PDF p. 8). The 90% band of Graph 3.B excludes zero at maturities from 8 to 30 years (PDF p. 8). Hyperscaler bonds of 10 years or more were about 24% of 2026 corporate issuance at those maturities and 13% of gross Treasury issuance. In 2024 the shares were about 3% and 1.5% (PDF p. 8).

**Related pricing facts in the companions.** Private credit loans to AI firms and to other firms carry similar spreads, 6.2 pp against 6.1 pp. Maturities are 4.7 against 4.8 years, and the secured shares are 46% against 48% (B120 PDF p. 6). The spread difference stays insignificant after loan and borrower controls (B120 PDF p. 7, note 6). Hyperscaler CDS spreads rose, especially for hyperscalers with lower ratings (QR box, para 2). The box gives no figure in its text.

## Limits
- The structure section is descriptive. It gives no count of vehicles, no distribution of lease terms, and no share of cancellable contracts.
- The event study tests aggregate rates and the aggregate IG index only. It does not test HY bonds, CDS, vehicle bonds or any issuer cross-section. It holds no contract-term variable.
- The events are hyperscaler and vendor news, not neocloud news. A neocloud event lies outside the sample.
- With 18 event days, one confounded day can move `beta`. The authors say some news may be anticipated or coincide with other events (PDF p. 7, note 7).
- The Hyperion spread gap is one deal. The bonds differ from Meta's bonds in maturity, placement and liquidity, so the gap does not isolate the contract terms.
- Source inconsistency: the Graph 3 note starts the sample on 6 January 2026 (PDF p. 7). The annex starts it on 5 January 2026 (annex p. 1).
- Source inconsistency: the key takeaways call the spillover to IG bond markets "small and short-lived" (PDF p. 3). The IG coefficient is 0.13 with a standard error of 0.24, not significant (annex p. 1). So "short-lived" applies to the term premium only.

## Section touched
`docs/methodology.md` Section 4.7.3 (support contents), Section 4.7 (`coverage_contracted`), Section 4.7.2 (delivery delay), Section 9.2 (rate channel). Decision page `2026-11-23-support-label-gap`.

**Section 4.7.3, term by term.**
1. `T^c / T^d`: informs the input. Initial terms are short and renewal is an option (PDF p. 5). Hyperion has 4 firm years against up to 20 with options (PDF p. 5, note 3). Read `T^c` as the firm initial term, not the option term. The source does not inform the Basel cut-offs of 1.25x and 0.9x.
2. `q^nc`: informs the sign only. A hyperscaler can end a lease early (PDF p. 6). The source gives no non-cancellable share.
3. `q^ig` and `NONIG_CREDIT = 0.5`: informs the split. Hyperscalers are IG. Neoclouds and AI labs are mostly unrated or below IG (PDF p. 5). The source does not inform the 0.5.
4. `q^on` and `UNSTARTED_CREDIT = 0.5`: informs the scale. About 68% of hyperscaler lease commitments had not started by mid-2026 (our arithmetic, 820 over 1,200, PDF p. 3). The source does not inform the 0.5.
5. `q^reach`: informs the structure. The SPV owns the asset and earns the contract cash, and the parent does not consolidate it (PDF pp. 4-5). Our inference: the contract cash reaches the SPV bond. It reaches the sponsor's own unsecured debt only through equity distributions.
6. Gap in `S_i`: the formula has no term for residual-value guarantees or vendor backstops. The source says they exist and are capped (PDF pp. 5-6). It gives no cap for hyperscaler guarantees, so we add no term now.
7. Steps 2 and 5 (`label_test`, gap IC): not informed. The event study measures the daily change in the Treasury term premium and the aggregate IG OAS on hyperscaler and vendor news days. It touches no HY bond spread and no CDS spread. It is not a test of label against contents. The Hyperion gap of 127 to 137 bp is one deal, not a test. B120 tests the AI sector label in private credit loan spreads and finds no difference, but it holds no contract contents.
8. The mis-sort cut of 0.25 rank, the one-month skip and `MIN_BONDS = 20`: not informed.

**Section 4.7.** The $1.2 trillion of lease commitments sits outside reported debt (PDF pp. 3, 6). This supports the use of disclosed commitments, not balance-sheet debt, as the obligation side of `coverage_contracted`. It changes no formula.

**Section 4.7.2.** Hyperion's leases begin in 2029 (PDF p. 5, note 3). Most commitments have not started (PDF p. 3). This informs the size of the exposure to delay. It does not inform `delay_tolerance`.

**Section 9.2.** The event study shows a supply effect on long Treasury yields of about 1.5 bp per news day, which reverses within two trading days (PDF pp. 7-8). That effect is too small and too short to add a third part to the growth and policy split of `Delta y`. Recheck it if the 24% share of long corporate issuance rises further (PDF p. 8).
