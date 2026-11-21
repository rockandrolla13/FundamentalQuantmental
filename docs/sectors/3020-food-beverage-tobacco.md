# 3020 Food, Beverage and Tobacco

Archetype (framework F2): no F2 archetype fits branded food and beverage well. Frame branded issuers as A4 with the low-cyclicality template below, and record the misfit in `issuer_state` (F2.1, Our choice). Frame agribusiness and protein processors as A3 Commodity producers, because a traded price sets their revenue and margin. Modifiers that often apply: M2 for tobacco and for categories with five years of volume decline, M1 for sponsor-owned packaged food issuers, M3 for a supplier with one retailer above 20% of revenue.
GICS industries covered: 302010 Beverages (30201010 Brewers, 30201020 Distillers and Vintners, 30201030 Soft Drinks and Non-alcoholic Beverages), 302020 Food Products (30202010 Agricultural Products and Services, 30202030 Packaged Foods and Meats), 302030 Tobacco (30203010).

## Sources
| Source | Type | Date | Opened | Pages or sections used |
|---|---|---|---|---|
| S&P Global Ratings, "Sector-Specific Corporate Methodology". Section 10 Consumer Staples And Branded Nondurables, Section 2 Agribusiness, Commodity Foods, And Agricultural Cooperatives. Public copy: South Dakota PUC docket EL26-003, Exhibit TDS-2, https://puc.sd.gov/commission/dockets/electric/2026/EL26-003/Vol2Section6/Exh2TStevens.pdf | rating agency criteria | 7 July 2025, republished 26 Sept 2025 | yes | pp. 10-16, 47-50. Appendix 3, pp. 244-248 |
| S&P, "Key Credit Factors For The Branded Nondurables Industry". Maalot copy, https://www.maalot.co.il/Publications/MT20190324131207.PDF | rating agency criteria | 7 May 2015, republished after review of 1 May 2018 | yes | paras. 7, 10-13, 17. Status not verified, may be superseded by the 2025 methodology |
| S&P, "Standard & Poor's Assigns Industry Risk Assessments To 38 Nonfinancial Corporate Industries". Maalot copy, https://maalot.co.il/publications/MT20150505165520.pdf | rating agency release | 20 Nov 2013 | yes | table, pp. 1-2. Status not verified, may be superseded by the 2025 methodology |
| S&P, "Key Credit Factors For The Agribusiness And Commodity Foods Industry" | rating agency criteria | not known | no | not opened. Search found no public copy |
| Moody's, "Consumer Packaged Goods", "Beverage", "Protein and Agriculture" and "Tobacco" methodologies | rating agency criteria | not known | no | not opened. ratings.moodys.com blocked the request with a bot check. We did not bypass it |
| Fitch sector criteria for food, beverage and tobacco | rating agency criteria | not known | no | not opened |
| `research/cards/gatto-2023-credit-cycle-and-recession-cases.md` | practitioner book | 2023 | yes (card) | Figure 6.4, p. 163: consumer staples are non-cyclical |
| `research/cards/augustin-cong-corhay-weber-2026-price-rigidities-credit.md` | working paper | 2026 | yes (card) | sticky output prices widen spreads after shocks |
| `research/cards/sp-global-2019-ratios-and-adjustments.md` | rating agency criteria | 2019 | yes (card) | adjusted debt principle, para. 9 |

## Industry risk
- S&P cyclicality assessment: branded nondurables 2 (low). Average peak-to-trough falls since 1952 were about 1.1% in revenue and 3.2% in EBITDA. In 2007 to 2009 they were 3.8% and 5.4% (branded nondurables KCF para. 17). Agribusiness and commodity foods 4 (moderately high) (2013 release).
- S&P competitive risk and growth assessment: branded nondurables 2 (low), agribusiness 3 (intermediate). Global industry risk is 2 and 3. Private label penetration drives price competition in some categories (branded nondurables KCF para. 12). The 2025 article does not restate these values.

## EBITDA, leverage and coverage
- EBITDA definition: analyst EBITDA of F3. Brand impairments are recurrent when they appear in two of five years (F3 C1). For tobacco under M2, treat restructuring as recurrent (F3 C2). For agribusiness, mark hedge gains and losses to the period of the physical sale (Our choice).
- Leverage measure: `lev_gc_total`. For a grain merchandiser, S&P may deduct readily marketable inventories from debt when trading is 10% to 20% of earnings (ARMI adjustment, S&P 2025, p. 10). Report leverage with and without the deduction.
- Coverage measure: `coverage = (ebitda_adj_analyst - capex) / cash_interest` (F5).
- Agency standard or supplementary ratios for the sector:
  - Agribusiness: FOCF to debt is preferred. DCF to debt for high dividend payers. EBITDA to interest and FFO plus cash interest over cash interest for seasonal issuers (S&P 2025, p. 15).
  - Branded: the 2025 Section 10 states no sector supplementary ratio. S&P measures operating leverage as the percentage change in EBIT over the percentage change in sales (S&P 2025, p. 49).
  - S&P EBITDA margin bands, average range: non-alcoholic beverages and packaged foods 10% to 20%, tobacco and alcoholic beverages 15% to 30%, grain processors and merchandisers 3% to 5%, commodity food ingredients 12% to 15%, meat and protein processors 5% to 10% (Appendix 3, pp. 244-245).

## Drivers

### Branded packaged food and beverages (30201010, 30201020, 30201030, 30202030 branded)
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev` | log of `(dlc + dltt)` over LTM EBITDA, clipped to [0.1, 20] | + | `hy.sector.drivers`, SECTOR-models 3.1 consumer_staples row |
| `coverage` | `oibdp / xint`, clipped to [−5, 30] | − | SECTOR-models 3.1 consumer_staples row |
| `margin_trend` | slope of `oibdpq / saleq` over 8 quarters over its standard error | − | SECTOR-models 3.1. F8 |
| `gross_margin` | `(sale - cogs) / sale` | − | S&P 2025, p. 50: sensitivity to raw material costs. Our choice |
| `organic_growth` | reported growth less FX, M&A and price, from the filing | − | F8. Branded nondurables KCF para. 12. Our choice |

### Agribusiness and protein processors (30202010, 30202030 commodity)
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev` | log of debt over LTM EBITDA, with and without the ARMI deduction | + | S&P 2025, p. 10. Agency weight |
| `ebitda_cyc` | minus the worst YoY change of `oibdp` over 10 years | + | S&P volatility adjustment, p. 15. Agency weight |
| `fcf_debt` | `(oancf - capx) / (dlc + dltt)` | − | S&P 2025, p. 15, preferred ratio. Agency weight |
| `deriv_margin` | cash collateral posted on derivatives over liquidity, from the filing | + | S&P 2025, p. 16: margin calls. Agency weight |

### Tobacco (30203010)
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev` | log of debt over LTM EBITDA | + | `hy.sector.drivers` |
| `vol_decline` | minus the 3-year average change in units shipped, from the filing | + | F2 M2. Our choice |
| `margin_trend` | slope of margin over 8 quarters over its standard error | − | F8. Our choice |

## Downside case
- Branded: the volume fall is small. S&P records average falls of 1.1% in revenue and 3.2% in EBITDA, and 3.8% and 5.4% in 2007 to 2009 (KCF para. 17). The larger risk is margin. Run an input cost spike that the issuer passes through one to two quarters late, plus a shift to private label (Our choice). Sticky prices widen spreads after shocks (Augustin et al. card).
- Agribusiness: run the F6 A3 rule. Use the crop or protein spread at the 10th percentile of ten years, plus the margin calls of the hedge book at that price.
- Tobacco: run the M2 rule. Use the worst three-year volume decline and an excise tax rise. Shorten the terminal value (F7.4).

## Collateral and recovery
- Branded: value is the brand as a going concern. A strong consumer brand can carry value above the F7.5 intangibles default. Use precedent brand sales.
- Plants liquidate at the F7.5 machinery rate. Finished goods inventory sits high in the F7.5 range. Perishable goods sit low.
- Agribusiness: readily marketable inventories liquidate near market value when hedged (Our choice). Hedge counterparties close out under the safe harbours and claim the net (F5 derivatives row).
- Tobacco: litigation and settlement obligations may survive a case. Size them by F5 litigation rules.
- Co-packer and supply contracts are executory. Code them with `hy.clocks.purchase_essentiality`.

## Events and calendar
- Monthly world agricultural supply and demand estimates from the US Department of Agriculture.
- Crop, cattle, hog, cocoa, coffee and sugar price moves.
- Excise tax votes and tobacco product rule releases.
- Retailer shelf reset dates and annual price negotiations with large retailers.
- Quarterly results with organic growth split into price and volume.

## Instructions for the analyst
1. Frame the issuer as branded, commodity, or tobacco. Record the F2 misfit for branded issuers.
2. For a grain merchandiser, compute leverage with and without the ARMI deduction.
3. Treat recurrent brand impairments and tobacco restructuring as operating costs.
4. Size liquidity after margin calls at the stress price for commodity issuers.
5. Map hedges, co-packer contracts and litigation claims to their F5 rows.
6. Build the downside as a margin case for branded issuers and a price deck for commodity issuers.
7. Value branded issuers on precedent brand sales. Value tobacco with a terminal value that declines.
8. Pass the F9 gate. Name the USDA release, price round or results date as the catalyst.

## Open questions
- Which archetype fits branded staples? F2 has none. Test: compare spread fit errors of branded staples under A4 rules and under a new low-cyclicality archetype. A result goes to a decision page, not to this file.
- Does `organic_growth` volume carry spread information beyond `margin_trend`? Test: add it to the consumer_staples fit and check the sign and IC.
- Do the 2015 KCF peak-to-trough figures hold after 2020? Test: recompute them from Compustat for 2020 to 2023 with the input cost shock.
- Does `deriv_margin` predict wider agribusiness spreads? Test: event study on margin call disclosures in 2008 and 2022.
