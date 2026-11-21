# 3010 Consumer Staples Distribution and Retail

Archetype (framework F2): A1 Lease-heavy consumer for food retail, drug retail and staples merchandise retail. Food distributors carry little rent and fit no archetype well. Frame them as A4 with low cyclicality, and test the A1 trigger each filing (Our choice). Modifiers that often apply: M1 for sponsor-owned grocers and distributors, M2 for formats that lose share to discounters and online channels for five years.
GICS industries covered: 301010 Consumer Staples Distribution and Retail (30101010 Drug Retail, 30101020 Food Distributors, 30101030 Food Retail, 30101040 Consumer Staples Merchandise Retail).

## Sources
| Source | Type | Date | Opened | Pages or sections used |
|---|---|---|---|---|
| S&P Global Ratings, "Sector-Specific Corporate Methodology", Section 31 Retail And Restaurants, which includes grocery wholesalers. Public copy: South Dakota PUC docket EL26-003, Exhibit TDS-2, https://puc.sd.gov/commission/dockets/electric/2026/EL26-003/Vol2Section6/Exh2TStevens.pdf | rating agency criteria | 7 July 2025, republished 26 Sept 2025 | yes | pp. 171-177. Appendix 3, pp. 244-248 |
| S&P, "Standard & Poor's Assigns Industry Risk Assessments To 38 Nonfinancial Corporate Industries". Maalot copy, https://maalot.co.il/publications/MT20150505165520.pdf | rating agency release | 20 Nov 2013 | yes | table, pp. 1-2. Status not verified, may be superseded by the 2025 methodology |
| S&P, "Key Credit Factors For The Retail And Restaurants Industry" | rating agency criteria | not known | no | not opened. Search found no public copy |
| Moody's, "Retail and Apparel" methodology | rating agency criteria | not known | no | not opened. ratings.moodys.com blocked the request with a bot check. We did not bypass it |
| Fitch sector criteria for retail and distribution | rating agency criteria | not known | no | not opened |
| `research/cards/gatto-2023-credit-cycle-and-recession-cases.md` | practitioner book | 2023 | yes (card) | Figure 6.4, p. 163: supermarkets are non-cyclical |
| `research/cards/altamuro-johnston-pandit-zhang-2012-operating-leases-credit.md`, `lim-mann-mihov-2017-operating-leases-credit-capacity.md`, `gordon-wang-zhao-2024-operating-lease-loan-contracts.md` | journal articles and drafts | 2012-2024 | yes (cards) | lease pricing in loans and bonds |
| `research/cards/heese-shin-wang-2025-variable-leases.md` | journal article | 2025 | yes (card) | variable leases off the balance sheet |
| `research/cards/jankowitsch-nagler-subrahmanyam-2014-recovery-rates.md` | journal article | 2014 | yes (card) | p. 40: retail mean recovery price |

## Industry risk
- S&P cyclicality assessment: retail and restaurants 3 (intermediate), which covers grocers, drugstores and grocery wholesalers (2013 release, S&P 2025 p. 171 scope). Gatto classes supermarkets as non-cyclical (Gatto card, p. 163). The agency score covers all retail, so it overstates cyclicality for grocers (our reading).
- S&P competitive risk and growth assessment: 3 (intermediate). Global industry risk is 3. The 2025 article does not restate these values. S&P notes that discounters and value retailers offer tough price competition in many countries (S&P 2025, p. 172).

## EBITDA, leverage and coverage
- EBITDA definition: EBITDAR and analyst EBITDA of F3, side by side. Add variable lease expense to rent (Heese et al. card). Treat industry-wide pharmacy litigation as an operating cost, not an add-back (F3 C5).
- Leverage measure: `lev_lease_adj = (debt + lease_debt) / (ebitda_adj_analyst + rent)` for A1 issuers (F5). `lev_gc_total` for a distributor below the A1 trigger.
- Coverage measure: `fccr = (ebitda_adj_analyst + rent - maintenance_capex) / (cash_interest + rent + mandatory_amortisation)` for A1 (F5). `coverage = (ebitda_adj_analyst - capex) / cash_interest` for distributors.
- Agency standard or supplementary ratios for the sector:
  - EBITDA to interest, FOCF to debt and DCF to debt. FOCF after lease payments. CFO to debt when capex constrains FOCF (S&P 2025, p. 177).
  - EBITDAR over cash interest plus rent, with S&P bands: above 8.0x minimal, 5.0x to 8.0x modest, 3.0x to 5.0x intermediate, 2.5x to 3.0x significant, 2.2x to 2.5x aggressive, under 2.2x highly leveraged (S&P 2025, p. 177).
  - S&P EBITDA margin band for discounters, food retailers, drugstores and convenience stores: under 5% below average, 5% to 10% average, over 10% above average (Appendix 3, p. 246). Food distributors sit in distribution services, 5% to 9% average (p. 244).

## Drivers

### Food retail, drug retail and staples merchandise retail (30101010, 30101030, 30101040)
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev_lease` | log of `(debt + 8 × xrent) / (EBITDA + xrent)`, falls back to `log_lev` | + | SECTOR-models 3.1, F5. Lim et al. (2017) and Gordon et al. (2024) cards. Tested on bond spreads |
| `ebitdar_cover` | `(oibdp + xrent) / (xint + xrent)` | − | S&P 2025, p. 177 bands. Agency weight |
| `sss_trend` | same-store sales growth less its 8-quarter mean, from the filing | − | S&P 2025, p. 175. Agency weight |
| `margin_trend` | slope of `oibdpq / saleq` over 8 quarters over its standard error | − | SECTOR-models 3.1, consumer_staples row. F8 |
| `fcf_debt` | `(oancf - capx) / (dlc + dltt)` | − | S&P 2025, p. 177. Agency weight |

For drug retail, report `rx_share`, pharmacy revenue over total revenue, beside the table. Pharmacy reimbursement sets the drug retail margin (Our choice). Sign not set until a test runs.

### Food distributors (30101020)
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev` | log of `(dlc + dltt)` over LTM EBITDA, clipped to [0.1, 20] | + | `hy.sector.drivers`, SECTOR-models 3.1 consumer_staples row |
| `coverage` | `oibdp / xint`, clipped to [−5, 30] | − | SECTOR-models 3.1 consumer_staples row |
| `cash_cycle` | inventory days plus receivable days less payable days | + | F8. Our choice |
| `margin_trend` | slope of margin over 8 quarters over its standard error | − | F8. Our choice |

## Downside case
Volume is defensive, so the downside is a margin case, not a volume case (Gatto card, p. 163). Hold same-store sales at the last downturn path. Cut gross margin to the trough of the last price war or the last food inflation spike, whichever is lower. Keep rent and union labour fixed. For drug retail, apply the last pharmacy reimbursement cut of the same kind (F6 A2 logic, Our choice). For distributors, cut the gross margin by the last fuel and labour cost shock and widen the cash cycle by the worst year. The severe case follows F6. No opened source gives a sector peak-to-trough figure.

## Collateral and recovery
- Grocery inventory turns fast, so the borrowing base moves with each week. Perishable goods liquidate below the F7.5 inventory range. Shelf-stable goods sit inside it (Our choice).
- Pharmacy prescription files have sale value to another pharmacy operator. Value them on a precedent sale per script, not on a multiple (Our choice).
- Owned stores and distribution centres at 70% to 80% (F7.5). Below-market leases have assignment value.
- Rejected store leases follow the F5 cap. Multi-employer pension plans give a withdrawal liability claim when union stores close (F5 pensions row).
- Prior for the F7.7 recovery check: mean recovery price 33.40 for retail bonds, N 33 (Jankowitsch et al. card, p. 40).

## Events and calendar
- Monthly advance retail sales release, food and beverage stores line.
- Monthly consumer price index, food at home.
- Union labour contract expiry dates in each market.
- Changes to federal food assistance benefits.
- Pharmacy reimbursement and drug pricing rule releases.

## Instructions for the analyst
1. Test the A1 trigger. Frame a distributor below it as low-cyclicality A4.
2. Add variable lease expense to rent. Compute EBITDAR, `lev_lease_adj` and `fccr`.
3. Treat recurrent pharmacy litigation as operating cost. Do not add it back.
4. Size liquidity on the weekly borrowing base. Deduct union pension contributions due.
5. Map store leases and multi-employer pension withdrawal claims to their F5 rows.
6. Build the downside as a margin case. Hold volume at the last downturn path.
7. Value on lease-adjusted peers and on liquidation. Add prescription files at precedent value.
8. Pass the F9 gate. Name the retail sales release, CPI print or contract date as the catalyst.

## Open questions
- Does the retail industry risk score overstate grocer cyclicality in spreads? Test: compare the spread beta to the HY index of 3010 issuers with 2550 issuers in 2008 and 2020.
- Do bonds of grocers price lease debt like funded debt? Altamuro et al. find no loan spread response inside retail. The bond papers find a response in bonds. We choose `log_lev_lease`. Test: fit both on 3010 bonds and compare rank IC.
- Does `rx_share` raise or lower drug retail spreads? Test: add it to the 3010 fit and read the sign.
- What do pharmacy prescription files recover in a sale? Test: collect precedent sale prices per script from bankruptcy sale orders.
