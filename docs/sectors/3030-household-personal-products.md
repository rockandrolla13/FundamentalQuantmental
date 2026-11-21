# 3030 Household and Personal Products

Archetype (framework F2): no F2 archetype fits branded household and personal products well. Frame them as A4 with the low-cyclicality template below, and record the misfit in `issuer_state` (F2.1, Our choice). Modifiers that often apply: M3 for an issuer with one retailer above 20% of revenue, M1 for sponsor-owned issuers.
GICS industries covered: 303010 Household Products (30301010), 303020 Personal Care Products (30302010).

## Sources
| Source | Type | Date | Opened | Pages or sections used |
|---|---|---|---|---|
| S&P Global Ratings, "Sector-Specific Corporate Methodology", Section 10 Consumer Staples And Branded Nondurables (household products and personal products subsectors). Public copy: South Dakota PUC docket EL26-003, Exhibit TDS-2, https://puc.sd.gov/commission/dockets/electric/2026/EL26-003/Vol2Section6/Exh2TStevens.pdf | rating agency criteria | 7 July 2025, republished 26 Sept 2025 | yes | pp. 47-50. Appendix 3, pp. 244-248 |
| S&P, "Key Credit Factors For The Branded Nondurables Industry". Maalot copy, https://www.maalot.co.il/Publications/MT20190324131207.PDF | rating agency criteria | 7 May 2015, republished after review of 1 May 2018 | yes | paras. 7, 10-14, 17. Status not verified, may be superseded by the 2025 methodology |
| S&P, "Standard & Poor's Assigns Industry Risk Assessments To 38 Nonfinancial Corporate Industries". Maalot copy, https://maalot.co.il/publications/MT20150505165520.pdf | rating agency release | 20 Nov 2013 | yes | table, pp. 1-2. Status not verified, may be superseded by the 2025 methodology |
| Moody's, "Consumer Packaged Goods" methodology | rating agency criteria | not known | no | not opened. ratings.moodys.com blocked the request with a bot check. We did not bypass it |
| Fitch sector criteria for consumer products | rating agency criteria | not known | no | not opened |
| `research/cards/gatto-2023-credit-cycle-and-recession-cases.md` | practitioner book | 2023 | yes (card) | Figure 6.4, p. 163: consumer staples are non-cyclical |
| `research/cards/irvine-park-yildizhan-2016-customer-concentration-life-cycle.md` | journal article | 2016 | yes (card) | customer concentration, input to M3 |
| `research/cards/augustin-cong-corhay-weber-2026-price-rigidities-credit.md` | working paper | 2026 | yes (card) | sticky output prices widen spreads after shocks |

## Industry risk
- S&P cyclicality assessment: branded nondurables 2 (low). Average peak-to-trough falls since 1952 were about 1.1% in revenue and 3.2% in EBITDA. In 2007 to 2009 they were 3.8% and 5.4% (branded nondurables KCF para. 17). The KCF lists GDP, unemployment, household net worth, consumer sentiment, disposable income and the price of gasoline as cyclicality drivers (para. 11).
- S&P competitive risk and growth assessment: 2 (low). Global industry risk is 2 (2013 release, KCF para. 10). Price competition is intense in categories with high private label penetration, such as household paper goods (KCF para. 12). The 2025 article does not restate these values.

## EBITDA, leverage and coverage
- EBITDA definition: analyst EBITDA of F3. Treat slotting fees and trade promotion as revenue deductions, not add-backs (Our choice). Brand impairments are recurrent when they appear in two of five years (F3 C1).
- Leverage measure: `lev_gc_total`. Add receivable securitisation and factoring to debt, because they replace borrowing (S&P 2019 card, para. 9).
- Coverage measure: `coverage = (ebitda_adj_analyst - capex) / cash_interest` (F5).
- Agency standard or supplementary ratios for the sector:
  - The 2025 Section 10 states no sector supplementary ratio. S&P measures operating leverage as the percentage change in EBIT over the percentage change in sales (S&P 2025, p. 49).
  - S&P evaluates working capital by total asset turnover, inventory turnover and the cash conversion cycle (S&P 2025, p. 49).
  - S&P EBITDA margin band for personal care and household products: under 15% below average, 15% to 25% average, over 25% above average (Appendix 3, p. 245).
  - S&P treats revenue concentration above 50% in one category or customer as a weakness of scale, scope and diversity (S&P 2025, p. 49).

## Drivers

### Household products (30301010)
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev` | log of `(dlc + dltt)` plus securitised receivables over LTM EBITDA, clipped to [0.1, 20] | + | `hy.sector.drivers`, SECTOR-models 3.1 consumer_staples row |
| `coverage` | `oibdp / xint`, clipped to [−5, 30] | − | SECTOR-models 3.1 consumer_staples row |
| `margin_trend` | slope of `oibdpq / saleq` over 8 quarters over its standard error | − | SECTOR-models 3.1. F8 |
| `gross_margin` | `(sale - cogs) / sale` | − | S&P 2025, p. 50: raw material and energy cost sensitivity. Our choice |
| `cust_top_share` | revenue share of the largest retailer customer, from the 10-K concentration note | + | F2 M3. S&P 2025, p. 49. Our choice |

### Personal care products (30302010)
Use the household products table. Add `organic_growth`, reported growth less FX, M&A and price, sign −, from F8 (Our choice). Prestige beauty is more discretionary than mass personal care. Treat it like luxury apparel for price cyclicality (KCF para. 14 by analogy, Our choice).

## Downside case
The volume fall is small. S&P records average falls of 1.1% in revenue and 3.2% in EBITDA, and 3.8% and 5.4% in 2007 to 2009 (KCF para. 17). Run a margin case instead. Raise the main inputs to their ten-year 90th percentile: pulp, resin, oil-based chemicals and freight. Pass the cost through one to two quarters late (Our choice). Add a retailer inventory destock of one quarter of shipments to the top customer under M3 (Our choice). Shift share to private label in the categories the filing names as most exposed. The severe case follows F6.

## Collateral and recovery
- Value is the brand portfolio as a going concern. A strong consumer brand can carry value above the F7.5 intangibles default. Use precedent brand sales.
- Finished goods inventory sits high in the F7.5 range. Raw materials and packaging sit low.
- Receivables from large retailers liquidate at the high end of the F7.5 range while the retailer is solvent. Securitised receivables leave the estate.
- Contract manufacturer and supply agreements are executory. Code them with `hy.clocks.purchase_essentiality`.

## Events and calendar
- Monthly pulp, resin and freight price releases.
- Retailer shelf reset dates and annual line reviews with large retailers.
- Retailer inventory releases, because a destock cuts shipments for one or two quarters.
- Quarterly results with organic growth split into price and volume.
- FX moves for issuers with large sales outside the United States.

## Instructions for the analyst
1. Frame the issuer as household or personal care. Record the F2 misfit and `cust_top_share`.
2. Deduct trade promotion and slotting fees from revenue. Do not add them back.
3. Add securitised and factored receivables to debt.
4. Size liquidity after the seasonal inventory build and any loss of the securitisation.
5. Map supply contracts and the securitisation vehicle to their F5 rows.
6. Build the downside as an input cost and destock case.
7. Value on precedent brand sales and peer EV to EBITDA.
8. Pass the F9 gate. Name the line review, results date or input price release as the catalyst.

## Open questions
- Which archetype fits branded household products? F2 has none. Test: compare spread fit errors under A4 rules and under a new low-cyclicality archetype. A result goes to a decision page.
- Does `cust_top_share` carry a spread premium after leverage? Test: add it to the consumer_staples fit and check the sign and IC.
- Does pass-through lag predict margin trough depth? Test: regress the 2021 to 2023 gross margin fall on the lag between input cost and price changes.
