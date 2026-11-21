# 2550 Consumer Discretionary Distribution and Retail

Archetype (framework F2): A1 Lease-heavy consumer. A4 Cyclical industrials is the second archetype for distributors with little rent. Modifiers that often apply: M1 for sponsor-owned retailers, M2 for department stores and other formats with five years of volume decline.
GICS industries covered: 255010 Distributors (25501010), 255030 Broadline Retail (25503030), 255040 Specialty Retail (25504010 Apparel Retail, 25504020 Computer and Electronics Retail, 25504030 Home Improvement Retail, 25504040 Other Specialty Retail, 25504050 Automotive Retail, 25504060 Homefurnishing Retail).

## Sources
| Source | Type | Date | Opened | Pages or sections used |
|---|---|---|---|---|
| S&P Global Ratings, "Sector-Specific Corporate Methodology", Section 31 Retail And Restaurants. Section 6 Business And Consumer Services for distributors. Public copy: South Dakota PUC docket EL26-003, Exhibit TDS-2, https://puc.sd.gov/commission/dockets/electric/2026/EL26-003/Vol2Section6/Exh2TStevens.pdf | rating agency criteria | 7 July 2025, republished 26 Sept 2025 | yes | pp. 32-35, 171-177. Appendix 3, pp. 244-248 |
| S&P, "Standard & Poor's Assigns Industry Risk Assessments To 38 Nonfinancial Corporate Industries". Maalot copy, https://maalot.co.il/publications/MT20150505165520.pdf | rating agency release | 20 Nov 2013 | yes | table, pp. 1-2. Status not verified, may be superseded by the 2025 methodology |
| S&P, "Key Credit Factors For The Retail And Restaurants Industry" | rating agency criteria | not known | no | not opened. Search found no public copy |
| S&P, "Corporate Methodology: Ratios And Adjustments" | rating agency criteria | 1 April 2019 | yes (card `sp-global-2019-ratios-and-adjustments.md`) | para. 26: lease adjustments |
| Moody's, "Retail and Apparel" methodology | rating agency criteria | not known | no | not opened. ratings.moodys.com blocked the request with a bot check. We did not bypass it |
| Fitch sector criteria for retail | rating agency criteria | not known | no | not opened |
| `research/cards/altamuro-johnston-pandit-zhang-2012-operating-leases-credit.md` | journal article draft | 2012 | yes (card) | pp. 22-23: retail loan spreads and leases |
| `research/cards/lim-mann-mihov-2017-operating-leases-credit-capacity.md`, `gordon-wang-zhao-2024-operating-lease-loan-contracts.md` | journal article, draft | 2017, 2024 | yes (cards) | Table 3 and Table 7 Panel B: bonds price capitalised leases |
| `research/cards/heese-shin-wang-2025-variable-leases.md`, `jung-scarlat-2024-asc842-bond-yields.md` | journal articles | 2024, 2025 | yes (cards) | variable leases off the balance sheet. Lease gap at the first ASC 842 report |
| `research/cards/jankowitsch-nagler-subrahmanyam-2014-recovery-rates.md` | journal article | 2014 | yes (card) | p. 40: retail mean recovery price |
| `research/cards/baker-baugh-sammon-2020-customer-churn.md` | working paper | 2020 | yes (card) | churn and revenue volatility in consumer firms |
| `research/cards/kricheff-2012-macro-drivers-and-scenarios.md` | practitioner book | 2012 | yes (card) | Table 12-1, p. 64: retail revenue model |

## Industry risk
- S&P cyclicality assessment: retail and restaurants 3 (intermediate). Business and consumer services, which holds distributors, 3 (2013 release). Gatto lists dollar stores as a counter-cyclical segment inside retail (Gatto card, p. 163).
- S&P competitive risk and growth assessment: 3 (intermediate) for both groups. Global industry risk is 3. The 2025 article does not restate these values.

## EBITDA, leverage and coverage
- EBITDA definition: EBITDAR and analyst EBITDA of F3, side by side. Store closure impairments are recurrent under A1 and M2 (F3 C1). Add variable lease expense to rent, because ASC 842 leaves it off the balance sheet (Heese et al. card, p. 1).
- Leverage measure: `lev_lease_adj = (debt + lease_debt) / (ebitda_adj_analyst + rent)` (F5). For an automotive retailer, report leverage with and without floor plan notes. Floor plan debt finances new vehicle inventory (Our choice).
- Coverage measure: `fccr = (ebitda_adj_analyst + rent - maintenance_capex) / (cash_interest + rent + mandatory_amortisation)` (F5).
- Agency standard or supplementary ratios for the sector:
  - EBITDA to interest, FOCF to debt and DCF to debt. FOCF after lease payments. CFO to debt when capex constrains FOCF (S&P 2025, p. 177).
  - EBITDAR over cash interest plus rent, with S&P bands: above 8.0x minimal, 5.0x to 8.0x modest, 3.0x to 5.0x intermediate, 2.5x to 3.0x significant, 2.2x to 2.5x aggressive, under 2.2x highly leveraged (S&P 2025, p. 177).
  - SG&A over gross profit for automotive retailers (S&P 2025, p. 175).
  - S&P EBITDA margin bands, average range: department stores and specialty retailers 10% to 16%, discounters and similar formats 5% to 10%, automotive retailers 3.5% to 4.0%, distribution services 5% to 9% (Appendix 3, pp. 244-246).

## Drivers

### Store-based and broadline retail (255030, 255040 except automotive retail)
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev_lease` | log of `(debt + 8 × xrent) / (EBITDA + xrent)`, falls back to `log_lev` | + | SECTOR-models 3.1, F5. Lim et al. (2017) and Gordon et al. (2024) cards. Tested on bond spreads |
| `ebitdar_cover` | `(oibdp + xrent) / (xint + xrent)` | − | S&P 2025, p. 177 bands. Agency weight |
| `sss_trend` | same-store sales growth less its 8-quarter mean, from the filing | − | S&P 2025, pp. 175-176. F2 A1 downside driver. Agency weight |
| `gross_margin` | `(sale - cogs) / sale` | − | SECTOR-models 3.1. Kricheff p. 59. S&P 2025, p. 176 |
| `inv_days` | `invt / cogs × 365` at the same quarter a year earlier | + | S&P 2025, p. 176: markdown risk. Our choice of formula |
| `mat_wall` | `(dd1 + dd2) / (dlc + dltt)` | + | SECTOR-models 3.1. Our choice |

### Automotive retail (25504050)
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev` | log of non-floor-plan debt over LTM EBITDA | + | `hy.sector.drivers`. Our choice to exclude floor plan |
| `sga_gross` | `xsga / (sale - cogs)` | + | S&P 2025, p. 175. Agency weight |
| `parts_service_share` | parts and service gross profit over total gross profit, from segment notes | − | S&P 2025, p. 177: parts and service sales. Our choice |
| `fcf_debt` | `(oancf - capx) / (dlc + dltt)` | − | S&P 2025, p. 177. Agency weight |

### Distributors (255010)
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev` | log of `(dlc + dltt)` over LTM EBITDA | + | `hy.sector.drivers` |
| `cash_cycle` | inventory days plus receivable days less payable days | + | F8. Our choice |
| `gross_margin` | `(sale - cogs) / sale` | − | Our choice |
| `fcf_debt` | `(oancf - capx) / (dlc + dltt)` | − | S&P 2025, p. 35. Agency weight |

## Downside case
Run the F6 A1 rule. Cut same-store sales to the decline of the last downturn and set gross margin at the trough. Keep rent fixed and cut payroll only to the share the filing shows as variable. Inventory bought for the season consumes cash when sales miss (F6.5). Recompute the ABL borrowing base on the lower inventory and receivables (F4.2). Tighten payable days by 10 in the severe case (F6). Set the store rejection set from the footprint: stores with negative four-wall EBITDA, or the stores the filing lists as under review (F2 A1). No opened source gives a sector peak-to-trough figure.

## Collateral and recovery
- Inventory and receivables at the F7.5 net orderly liquidation rates. Inventory value peaks before the holiday season and is lowest after it. Use the inventory level at the quarter the downside case defaults.
- Owned real estate at 70% to 80% (F7.5). Below-market leases have assignment value in a sale. Above-market leases do not.
- Rejected store leases follow the F5 cap. Size the claim for each rejection set.
- The ABL lender holds the first lien on inventory and receivables. Bonds usually sit behind it, so liquidation value often leaves little for unsecured bonds (F7 A1 row).
- Prior for the recovery check: mean recovery price 33.40 for retail bonds, N 33 (Jankowitsch et al. card, p. 40). The all-sector unsecured mean is 39.09. Use the prior only in the F7.7 market check.
- A strong private label or consumer brand can carry value above the F7.5 intangibles default. Use a precedent sale.

## Events and calendar
- Monthly advance retail sales release.
- Holiday season results in January, and back-to-school results in September.
- Monthly or weekly ABL borrowing base certificates, when the documents require them.
- Store closure announcements and lease renewal dates in the 10-K lease note.
- Tariff decisions on imported consumer goods.

## Instructions for the analyst
1. Confirm A1: rent above 8% of sales, or lease liability above net debt.
2. Add variable lease expense to rent. Compute EBITDAR, `lev_lease_adj` and `fccr`.
3. Treat store closure costs and impairments as recurrent. Do not add them back.
4. Size liquidity at the pre-holiday peak. Recompute the borrowing base in the downside case.
5. Build three store rejection sets from the footprint. Size each lease claim with the F5 cap.
6. Run the downside on same-store sales and gross margin at the last trough.
7. Value on lease-adjusted peers and on liquidation. Report which one binds.
8. Pass the F9 gate. Name the holiday results or the retail sales release as the catalyst.

## Open questions
- Do bond spreads of retailers price lease debt like funded debt? Sources disagree. Altamuro et al. find that loan spreads inside retail do not rise with leases, and that agencies still capitalise retail leases (pp. 22-23). Lim et al. and Gordon et al. find that bonds price the capitalised lease. Altamuro is right for bank loans. The bond papers are right for bonds, which we price. We choose `log_lev_lease`. Test: fit `log_lev_lease` against `log_lev` on 2550 bonds and compare out-of-sample rank IC.
- Does `sss_trend` add to `margin_trend`? Test: add it to the consumer_disc fit and check the sign and the IC gain.
- Do the filing proxies of customer churn carry information for retail spreads? Test: report `rev_abs_growth` and `sga_sales` beside the fit, as the Baker et al. card proposes, and read their rank IC.
- Does the retail recovery prior hold after 2010? Test: rebuild the Jankowitsch recovery outcome for retail defaults from 2011 onward.
