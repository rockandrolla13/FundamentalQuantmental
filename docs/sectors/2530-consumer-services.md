# 2530 Consumer Services

Archetype (framework F2): A1 Lease-heavy consumer for restaurants, fitness clubs and cinemas. A7 Project-like and single-asset is the second archetype for casinos. Cruise lines, theme parks and hotel owners fit A5 by the capex test. Hotel franchisors and managers fit A4 (Our choice). Modifiers that often apply: M1 for sponsor-owned restaurants, fitness and education issuers, M3 for a casino with one property above 20% of EBITDA.
GICS industries covered: 253010 Hotels, Restaurants and Leisure (25301010 Casinos and Gaming, 25301020 Hotels, Resorts and Cruise Lines, 25301030 Leisure Facilities, 25301040 Restaurants), 253020 Diversified Consumer Services (25302010 Education Services, 25302020 Specialized Consumer Services).

## Sources
| Source | Type | Date | Opened | Pages or sections used |
|---|---|---|---|---|
| S&P Global Ratings, "Sector-Specific Corporate Methodology". Section 20 Leisure And Sports, Section 31 Retail And Restaurants, Section 6 Business And Consumer Services. Public copy: South Dakota PUC docket EL26-003, Exhibit TDS-2, https://puc.sd.gov/commission/dockets/electric/2026/EL26-003/Vol2Section6/Exh2TStevens.pdf | rating agency criteria | 7 July 2025, republished 26 Sept 2025 | yes | pp. 32-35, 110-116, 171-177. Appendix 3, pp. 244-248 |
| S&P, "Standard & Poor's Assigns Industry Risk Assessments To 38 Nonfinancial Corporate Industries". Maalot copy, https://maalot.co.il/publications/MT20150505165520.pdf | rating agency release | 20 Nov 2013 | yes | table, pp. 1-2. Status not verified, may be superseded by the 2025 methodology |
| S&P, "Key Credit Factors For The Leisure And Sports Industry" | rating agency criteria | 5 March 2014, from a cross-reference only | no | not opened. Search found no public copy |
| S&P, "Key Credit Factors For The Retail And Restaurants Industry" | rating agency criteria | not known | no | not opened |
| Moody's, "Gaming", "Lodging and Cruise" and "Restaurant" methodologies | rating agency criteria | not known | no | not opened. ratings.moodys.com blocked the request with a bot check. We did not bypass it |
| Fitch sector criteria for gaming, lodging and restaurants | rating agency criteria | not known | no | not opened |
| `research/cards/lim-mann-mihov-2017-operating-leases-credit-capacity.md`, `gordon-wang-zhao-2024-operating-lease-loan-contracts.md`, `altamuro-johnston-pandit-zhang-2012-operating-leases-credit.md` | journal articles and drafts | 2012-2024 | yes (cards) | lease pricing in bonds and loans |
| `research/cards/dogan-2016-operating-leases-operating-leverage.md` | journal article | 2016 | yes (card) | non-cancellable leases act as operating leverage |
| `research/cards/gatto-2023-credit-cycle-and-recession-cases.md` | practitioner book | 2023 | yes (card) | Figure 6.4, p. 163: restaurants are pro-cyclical |
| `research/notes/sector-sources-shortlist.md`, A1 rows | shortlist | 2026-11-21 | metadata only | Gu and Kim (2002) restaurant risk. Not opened. Equity beta only |

## Industry risk
- S&P cyclicality assessment: leisure and sports 4 (moderately high), which covers casinos, hotels, cruise, theme parks and fitness. Retail and restaurants 3 (intermediate). Business and consumer services 3, which covers education and specialised services (2013 release).
- S&P competitive risk and growth assessment: 3 (intermediate) for all three groups. Global industry risk is 3 for all three. The 2025 article does not restate these values.

## EBITDA, leverage and coverage
- EBITDA definition: analyst EBITDA of F3. Report EBITDAR for restaurants, fitness clubs, cinemas and leased hotels. For a casino held in a project structure, report project EBITDA at the asset and distributions to the holdco (F2 A7). Treat pre-opening costs of new units as recurrent when the issuer opens units every year (Our choice).
- Leverage measure: `lev_lease_adj = (debt + lease_debt) / (ebitda_adj_analyst + rent)` for A1 issuers (F5). `lev_gc_total` for A4 and A5 issuers. Asset-level debt over project EBITDA, and holdco debt over distributions, for A7 casinos.
- Coverage measure: `fccr = (ebitda_adj_analyst + rent - maintenance_capex) / (cash_interest + rent + mandatory_amortisation)` for A1 (F5). Debt service coverage at the asset for A7.
- Agency standard or supplementary ratios for the sector:
  - Restaurants: EBITDA to interest, FOCF to debt and DCF to debt. FOCF after lease payments. EBITDAR over cash interest plus rent, with S&P bands: above 8.0x minimal, 5.0x to 8.0x modest, 3.0x to 5.0x intermediate, 2.5x to 3.0x significant, 2.2x to 2.5x aggressive, under 2.2x highly leveraged (S&P 2025, p. 177).
  - Leisure and sports: EBITDA to interest is preferred. FOCF to debt for gaming, lodging, cruise, theme parks and fitness. CFO to debt for timeshare and toy makers (S&P 2025, p. 115).
  - Consumer services: FOCF to debt. Give more weight to FFO plus cash interest over cash interest when sponsor debt pays interest in kind (S&P 2025, p. 35).
  - S&P EBITDA margin bands, average range: restaurants 14% to 23%, leisure and sports 20% to 30%, consumer services 18% to 24% (Appendix 3, pp. 244-246).

## Drivers

### Restaurants (25301040)
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev_lease` | log of `(debt + 8 × xrent) / (EBITDA + xrent)`, falls back to `log_lev` | + | SECTOR-models 3.1, F5. Lim et al. (2017) card: leases price near debt in bonds under the S&P measure. Tested on new-issue spreads |
| `ebitdar_cover` | `(oibdp + xrent) / (xint + xrent)` | − | S&P 2025, p. 177 bands. Agency weight |
| `sss_trend` | same-store sales growth less its 8-quarter mean, from the filing | − | S&P 2025, p. 175. F2 A1 downside driver. Agency weight |
| `franchise_share` | franchised units over total units, from the filing | − | S&P 2025, p. 177: franchise cuts cost exposure. Agency weight |
| `mat_wall` | `(dd1 + dd2) / (dlc + dltt)` | + | SECTOR-models 3.1, consumer_disc row. Our choice |

### Casinos and gaming (25301010)
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev` | log of `(dlc + dltt)` over LTM EBITDA, clipped to [0.1, 20] | + | `hy.sector.drivers` |
| `coverage` | `oibdp / xint`, clipped to [−5, 30] | − | S&P 2025, p. 115, preferred ratio. Agency weight |
| `prop_top_share` | EBITDA share of the largest property, from segment notes | + | F2 A7 and M3. Our choice |
| `fair_share` | share of market gaming revenue over share of market gaming capacity, from state reports | − | S&P 2025, p. 110: market share premium. Agency weight |
| `capex_int` | `capx / sale` | + | S&P 2025, p. 115: development and maintenance capex. Our choice |

### Hotels, resorts, cruise lines and leisure facilities (25301020, 25301030)
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev` | log of `(dlc + dltt)` over LTM EBITDA | + | `hy.sector.drivers` |
| `revpar_gap` | RevPAR growth less the industry RevPAR growth, or net yield growth less peers for cruise | − | S&P 2025, p. 114. Agency weight |
| `capex_int` | `capx / sale` | + | F2 A5 trigger. S&P 2025, p. 115 FOCF use |
| `fcf_debt` | `(oancf - capx) / (dlc + dltt)` | − | S&P 2025, p. 115. Agency weight |
| `owned_share` | owned or leased rooms over total rooms, for hotel issuers | + | S&P 2025, p. 114: franchising and management give cost flexibility. Agency weight |

### Fitness clubs and cinemas (inside 25301030)
Use the restaurant table. Replace `franchise_share` with `new_unit_share`, new clubs over total clubs, sign +. S&P states that new clubs drain EBITDA until membership covers fixed costs (S&P 2025, p. 115). Agency weight.

### Education and specialized consumer services (253020)
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev` | log of `(dlc + dltt)` over LTM EBITDA | + | `hy.sector.drivers` |
| `fcf_debt` | `(oancf - capx) / (dlc + dltt)` | − | S&P 2025, p. 35. Agency weight |
| `gov_funding_share` | revenue from government student aid over revenue, from the filing | + | F2 A2 payer rule applied by analogy. Our choice |
| `margin_trend` | slope of margin over 8 quarters over its standard error | − | F8. Our choice |

## Downside case
- Restaurants, fitness and cinemas: run the F6 A1 rule. Cut same-store sales to the last downturn and hold rent fixed. Rent does not fall with sales, so the margin falls faster than sales (Dogan 2016 card, operating leverage).
- Casinos: run the F6 A7 rule. Apply the asset shock the documents test for: a new competitor in the market, a tax rise, or a closure. Test the distribution block at the holdco.
- Hotels and cruise: run the F6 A5 rule on RevPAR or net yield. Lodging and cruise costs are largely fixed for owners. A franchisor loses fees in line with RevPAR but keeps its cost flexibility (S&P 2025, p. 114).
- Education: cut enrolment and government funding to the worst disclosed year.
- No opened source gives a sector peak-to-trough figure. Each figure comes from the issuer's own record.

## Collateral and recovery
- Restaurants and fitness: owned real estate at sale-leaseback value, equipment at the F7.5 machinery rate, and little inventory. Liquidation value often binds (F7 A1 row). Rejected store leases follow the F5 cap.
- A franchisor with a whole business securitisation holds its royalties in a separate vehicle. Treat that debt as structurally senior to parent bonds (Our choice).
- Casinos: value the asset with a project DCF under the shock (F7 A7 row). A buyer needs regulator approval to hold the licence, so add a time-to-sale haircut (Our choice).
- Native American gaming: S&P assigns no recovery rating, because creditor rights against a sovereign nation are uncertain (S&P 2025, p. 116). Set recovery to a scenario range, not a waterfall.
- Cruise ships: appraised value in a forced sale (F7 A5 row). Vessel financings follow their own regime (F5 equipment row).
- Hotels: owned real estate at appraisal. Management and franchise contracts are executory and code with `hy.clocks.purchase_essentiality`.

## Events and calendar
- Monthly state gaming revenue reports. Licence renewal dates and new casino openings in the same market.
- Gaming tax votes in state budgets.
- Weekly and monthly RevPAR releases. Cruise booking reports and ship delivery dates.
- State minimum wage changes, often on 1 January. Beef, chicken and other food input prices.
- Federal student aid rule releases and accreditation decisions.

## Instructions for the analyst
1. Frame the issuer by sub-industry. Assign A1, A4, A5 or A7 by the F2 tests.
2. For A1, compute EBITDAR, `lev_lease_adj` and `fccr`. Do not add back recurrent pre-opening costs.
3. For a casino, split asset EBITDA from holdco distributions. Read the distribution test first.
4. Size liquidity after rent, maintenance capex, and committed new units or ships.
5. Map store leases, franchise agreements and securitisation vehicles to their F5 rows.
6. Build the downside on same-store sales, RevPAR, net yield, or the asset shock.
7. Value A1 issuers on liquidation and lease-adjusted peers. Value A7 assets on project DCF.
8. Pass the F9 gate. Name the gaming report, RevPAR release or results date that carries the catalyst.

## Open questions
- Do bonds of restaurants price lease debt like funded debt? Sources disagree. Altamuro et al. find loan spreads inside retail do not rise with leases. Lim et al. and Gordon et al. find bonds price the capitalised lease. We choose the bond evidence because we price bonds. Test: fit `log_lev_lease` against `log_lev` on restaurant bonds and compare rank IC.
- Does `franchise_share` lower spreads after `ebitdar_cover`? Test: add it to the restaurant fit and check the sign.
- Does `fair_share` predict casino spreads? Test: build it from state monthly reports and add it to the gaming fit.
- Which archetype fits a hotel franchisor best? Test: compare spread fit errors under A4 and A5 rules for franchisors.
