# 2520 Consumer Durables and Apparel

Archetype (framework F2): A4 Cyclical industrials for homebuilders, household durables and leisure products. A1 Lease-heavy consumer is the second archetype for an apparel brand whose own stores push rent above 8% of sales. Modifiers that often apply: M1 for sponsor-owned durables and apparel issuers, M3 for a supplier with one retailer customer above 20% of revenue.
GICS industries covered: 252010 Household Durables (25201010 Consumer Electronics, 25201020 Home Furnishings, 25201030 Homebuilding, 25201040 Household Appliances, 25201050 Housewares and Specialties), 252020 Leisure Products (25202010), 252030 Textiles, Apparel and Luxury Goods (25203010 Apparel, Accessories and Luxury Goods, 25203020 Footwear, 25203030 Textiles).

## Sources
| Source | Type | Date | Opened | Pages or sections used |
|---|---|---|---|---|
| S&P Global Ratings, "Sector-Specific Corporate Methodology". Section 9 Consumer Durables, Section 10 Consumer Staples And Branded Nondurables (apparel), Section 19 Homebuilders And Real Estate Developers, Section 20 Leisure And Sports (toy companies). Public copy: South Dakota PUC docket EL26-003, Exhibit TDS-2, https://puc.sd.gov/commission/dockets/electric/2026/EL26-003/Vol2Section6/Exh2TStevens.pdf | rating agency criteria | 7 July 2025, republished 26 Sept 2025 | yes | pp. 43-50, 103-116. Appendix 3, pp. 244-248 |
| S&P, "Key Credit Factors For The Branded Nondurables Industry". Maalot copy, https://www.maalot.co.il/Publications/MT20190324131207.PDF | rating agency criteria | 7 May 2015, republished after review of 1 May 2018 | yes | paras. 7, 10-14 (apparel price cyclicality). Status not verified, may be superseded by the 2025 methodology |
| S&P, "Standard & Poor's Assigns Industry Risk Assessments To 38 Nonfinancial Corporate Industries". Maalot copy, https://maalot.co.il/publications/MT20150505165520.pdf | rating agency release | 20 Nov 2013 | yes | table, pp. 1-2. Status not verified, may be superseded by the 2025 methodology |
| S&P, "Key Credit Factors For The Consumer Durables Industry" and "Key Credit Factors For The Homebuilder And Real Estate Developer Industry" | rating agency criteria | not known | no | not opened. Search found no public copy |
| Moody's, "Homebuilding And Property Development", "Consumer Durables" and "Apparel" methodologies | rating agency criteria | not known | no | not opened. ratings.moodys.com blocked the request with a bot check. We did not bypass it |
| Fitch sector criteria for homebuilders and consumer products | rating agency criteria | not known | no | not opened |
| `research/cards/gatto-2023-credit-cycle-and-recession-cases.md` | practitioner book | 2023 | yes (card) | Figure 6.4, p. 163: housing is pro-cyclical |
| `research/cards/habib-ranasinghe-bhuiyan-2025-order-backlog-credit-ratings.md` | journal article | 2025 | yes (card) | backlog and ratings, for homebuilder orders |
| `research/cards/augustin-cong-corhay-weber-2026-price-rigidities-credit.md` | working paper | 2026 | yes (card) | sticky output prices and spreads after shocks |

## Industry risk
- S&P cyclicality assessment: homebuilders 5 (high), consumer durables 3 (intermediate), leisure and sports 4 (moderately high), branded nondurables 2 (low) for apparel. Non-luxury apparel shows more price cyclicality than luxury goods (branded nondurables KCF para. 14).
- S&P competitive risk and growth assessment: homebuilders 3, consumer durables 3, leisure and sports 3, branded nondurables 2. Global industry risk is 4 for homebuilders, 3 for durables and leisure, and 2 for branded nondurables (2013 release). The 2025 article does not restate these values.

## EBITDA, leverage and coverage
- EBITDA definition: analyst EBITDA of F3. For a homebuilder, add back the capitalised interest that flows through cost of sales, and treat land impairments under C1 (Our choice). For an apparel brand with own stores, report EBITDAR beside EBITDA (F2 A1).
- Leverage measure: `lev_gc_total` for durables and apparel. `lev_lease_adj` when rent exceeds 8% of sales. For a homebuilder, report `debt_cap = debt / (debt + book equity)` beside `lev_gc_total`.
- Coverage measure: `coverage = (ebitda_adj_analyst - capex) / cash_interest`. For a homebuilder, use interest incurred, not interest expensed, in the denominator (Our choice).
- Agency standard or supplementary ratios for the sector:
  - Durables: FOCF to debt is preferred. Use FFO plus cash interest over cash interest, and EBITDA over interest, for seasonal issuers or when the score is significant or weaker (S&P 2025, p. 46).
  - Homebuilders: CFO, FOCF and DCF to debt, two coverage ratios, and debt to debt plus equity. S&P bands on historical cost: under 25% minimal, 25% to 35% modest, 35% to 45% intermediate, 45% to 50% significant, 50% to 60% aggressive, over 60% highly leveraged (S&P 2025, pp. 108-109).
  - S&P EBITDA margin bands: diversified durables 8% to 14% average, home appliances 6% to 9%, apparel 10% to 15% (Appendix 3, pp. 244-245). S&P sets no fixed margin band for homebuilders (p. 244).

## Drivers

### Homebuilding (25201030)
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `debt_cap` | `(dlc + dltt) / (dlc + dltt + ceq)` | + | S&P 2025, p. 109 bands. Agency weight |
| `gross_margin` | `(sale - cogs) / sale`, with capitalised interest added back to the margin | − | Our choice |
| `book_to_bill` | net new orders over closings, units, from the filing | − | Habib et al. (2025) card, rating test on backlog. Tested on ratings |
| `spec_share` | speculative homes in inventory over total homes in inventory, from the filing | + | S&P 2025, p. 107: S&P monitors this share against peers. Agency weight |
| `land_years` | lots owned over trailing twelve-month closings | + | Our choice |

### Household durables and leisure products (252010 except homebuilding, 252020)
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev` | log of `(dlc + dltt)` over LTM EBITDA, clipped to [0.1, 20] | + | `hy.sector.drivers`, Section 4.3 |
| `fcf_debt` | `(oancf - capx) / (dlc + dltt)` | − | S&P 2025, p. 46, preferred ratio. Agency weight |
| `gross_margin` | `(sale - cogs) / sale` | − | SECTOR-models 3.1, consumer_disc row. Kricheff p. 59. Our choice |
| `inv_days` | `invt / cogs × 365` | + | F8 `cash_cycle`. S&P 2025, p. 114: obsolete toy inventory. Our choice |
| `ebitda_cyc` | minus the worst YoY change of `oibdp` over 10 years | + | S&P volatility adjustment for furniture, p. 46. Agency weight |

### Apparel, footwear and luxury (252030)
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev_lease` | log of `(debt + 8 × xrent) / (EBITDA + xrent)`, falls back to `log_lev` | + | SECTOR-models 3.1, F5 |
| `gross_margin` | `(sale - cogs) / sale` | − | branded nondurables KCF para. 12 on promotion. Our choice |
| `margin_trend` | slope of margin over 8 quarters over its standard error | − | F8. Our choice |
| `inv_days` | `invt / cogs × 365` | + | Our choice |

## Downside case
- Homebuilders: run the F6 A4 rule on orders and average sale price from the issuer's last housing downturn. Hold land spend at the plan for two quarters, because land contracts commit cash ahead of sales (Our choice). Book land impairments in the case and do not add them back.
- Durables and leisure products: run the F6 A4 rule. Durables sales release working capital early in a downturn, so FOCF to debt can beat FFO to debt at first (S&P 2025, p. 46).
- Apparel: run the A1 rule when the issuer is lease-heavy. Otherwise cut gross margin to its last trough and add a markdown on excess seasonal inventory.
- No opened source gives a sector peak-to-trough figure for these groups. Each figure comes from the issuer's own record.

## Collateral and recovery
- Homebuilders: land, lots and homes under construction are the collateral. F7.5 has no land row. Value land at the sale prices of comparable lots in the downturn, with a range. Do not use book value.
- Option lots carry a deposit only. A rejected option contract creates a general unsecured damage claim less mitigation (F5 purchase obligations row).
- Durables and apparel: inventory at the F7.5 rates of 60% to 75% of net orderly liquidation value. Finished goods sit high in the range. Seasonal and fashion goods sit low.
- A strong consumer brand can carry value above the F7.5 intangibles default. Use a precedent brand sale, not a multiple.
- Apparel store leases follow the F5 capped claim rule.

## Events and calendar
- Monthly new residential construction and new home sales releases. Monthly mortgage rate data.
- Quarterly homebuilder orders, closings, and cancellation rate in each filing.
- Holiday season results for durables, toys and apparel, in January.
- Tariff decisions on imported goods, and input cost moves in cotton, steel and resin.
- Retailer inventory releases, because a retailer destock cuts orders to durables and apparel suppliers.

## Instructions for the analyst
1. Frame the issuer as homebuilder, durables maker, leisure products maker, or apparel brand.
2. For apparel, test rent against 8% of sales. Above it, apply the A1 rules.
3. For a homebuilder, add back capitalised interest in cost of sales. Use interest incurred for coverage.
4. Size liquidity at the seasonal peak for durables and apparel, and after land commitments for homebuilders.
5. Map land option contracts and store leases to their F5 claim rows.
6. Build the downside from the issuer's own last downturn. Book impairments and markdowns inside it.
7. Value homebuilders on land at downturn prices. Value brands on precedent sales.
8. Pass the F9 gate. Name the housing release or the season that carries the catalyst.

## Open questions
- Does `debt_cap` beat `log_lev` for homebuilders in the spread fit? Test: fit both in the consumer_disc group, homebuilders only, and compare out-of-sample rank IC.
- What share of land book value survives a housing downturn? Test: compare land impairments and land sale prices in 2007 to 2011 filings with prior book values.
- Does `spec_share` carry a premium after leverage? Test: add it to the homebuilder fit and check the sign.
- Is apparel closer to staples or to discretionary in spreads? Test: compare spread betas to the HY index in 2008 and 2020 for 252030 against 2550 and 3030.
