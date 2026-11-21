# 3510 Health Care Equipment and Services

Archetype (framework F2): A2 for providers (hospitals, physician groups, post-acute care). A4 for medical products, with a low-cyclicality recession template. A6 for health care technology. Modifiers that often apply: M1 (sponsor-owned providers and device makers), M3 (one product or one payer contract above 20% of revenue).
GICS industries covered: 351010 Health Care Equipment and Supplies, 351020 Health Care Providers and Services, 351030 Health Care Technology.

## Sources
| Source | Type | Date | Opened | Pages or sections used |
|---|---|---|---|---|
| S&P Global Ratings, "Sector-Specific Corporate Methodology". Public copy: South Dakota PUC docket EL26-003, Exhibit TDS-2, https://puc.sd.gov/commission/dockets/electric/2026/EL26-003/Vol2Section6/Exh2TStevens.pdf | rating agency criteria | July 7, 2025, republished Sept. 26, 2025 | yes | Section 17 Health Care Equipment (exhibit pp. 92-96). Section 18 Health Care Services (pp. 97-102). Appendix 3 margin and SER tables (pp. 244-252) |
| S&P Global Ratings, "Key Credit Factors For The Health Care Services Industry", https://www.maalot.co.il/Publications/MT20160622152017.pdf | rating agency criteria. Status not verified, may be superseded by the 2025 methodology | April 16, 2014, republished April 1, 2016 | yes | paras. 5, 7, 10-15 (industry risk, cyclicality), 66, 71, 76, 81 (EBITDAR coverage) |
| S&P Global Ratings, "Standard & Poor's Assigns Industry Risk Assessments To 38 Nonfinancial Corporate Industries", https://maalot.co.il/publications/MT20150505165520.pdf | rating agency table | Nov. 20, 2013 | yes | Industry risk table, pp. 1-2 |
| S&P Global Ratings, "Key Credit Factors For The Medical Products Industry" | rating agency criteria | unknown | not opened | No public copy found. Section 17 of the 2025 article replaces it here |
| Moody's, health care service providers and medical products methodologies | rating agency methodology | unknown | not opened | ratings.moodys.com returns a login page |
| Malone, Pink and Holmes (2024), card `research/cards/malone-pink-holmes-2024-rural-hospital-distress.md` | peer-reviewed journal, repo card | 2024 | yes | Table 2, p. 7. Limits section |
| Richards and Whaley (2024), Adelino, Lewellen and McCartney (2022), Enumah and Chang (2021), in `research/notes/sector-sources-shortlist.md` | peer-reviewed journals | 2021-2024 | not opened | Listed as candidates only |

## Industry risk
- S&P cyclicality assessment: health care services "low risk" (2). Health care equipment "low risk" (2) (2013 table, pp. 1-2). The 2014 article reports no peak-to-trough revenue decline for providers in any recession since 1968. The EBITDA margin fell 6.2% on average, peak to trough, and 3.8% in 2007-2009 (para. 12). Reimbursement changes move provider results more than the macro cycle does (para. 15).
- S&P competitive risk and growth assessment: health care services "intermediate risk" (3), industry risk "intermediate" (3). Health care equipment "low risk" (2), industry risk "low" (2) (2013 table). These are 2013 values. We did not find a later public list.

## EBITDA, leverage and coverage
- EBITDA definition, providers: analyst EBITDA after bad debt expense (F2 A2). Under ASC 606 most patient bad debt reduces revenue as an implicit price concession, so read both lines. Remove one-off government relief grants from analyst EBITDA. Keep state supplemental payments in EBITDA, but tag them as policy revenue (Our choice).
- EBITDA definition, medical products: analyst EBITDA under F3. Do not add back recall costs or product liability settlements when they recur (F3 C5).
- Leverage measure: `lev_lease_adj = (debt + lease_debt) / (ebitda_adj_analyst + rent)` for providers (F5). S&P calls operating leases its largest adjustment for this sector (2014, para. 76). Use `lev_gc_total` for medical products.
- Coverage measure: providers use `fccr` (F5). S&P uses `EBITDAR / (interest + rent)` when rent is large (2025 Section 18, exhibit p. 101). Medical products use `coverage` (F5).
- Agency supplementary ratios:
  - Providers: EBITDAR to interest plus rent. S&P scale: above 8.0x minimal, 5.0x to 8.0x modest, 3.0x to 5.0x intermediate, 2.5x to 3.0x significant, 2.2x to 2.5x aggressive, below 2.2x highly leveraged (Section 18). S&P uses CFO to debt and FOCF to debt "less often" for providers.
  - Medical products: EBITDA to interest when the core ratios read "significant" or weaker. FOCF to debt for equipment lessors and contract manufacturers (Section 17).
  - EBITDA margin bands (Appendix 3): health care services below 15% below average, 15% to 25% average, above 25% above average. Health care equipment: below 22%, 22% to 35%, above 35%.

## Drivers

### Hospitals, physician groups, post-acute (A2)
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev_lease` | log of `(dlc + dltt + 8 xrent) / (oibdp + xrent)`, clipped (`hy.sector.drivers`) | + | Our choice. S&P lease adjustment, 2014 para. 76 (agency weight) |
| `margin` | `oibdp / sale`, LTM | − | tested: Malone et al. (2024) Table 2, p. 7. Total margin at t, t−1 and t−2 all lower distress 2 years ahead. Distress, not spreads. Rural nonprofit sample |
| `log_size` | log of LTM `sale` | − | tested: Malone et al. (2024) Table 2, p. 7, net patient revenue. Distress, not spreads. Candidate, not in `hy.sector.drivers` |
| `fcf_debt` | `(oancf − capx) / (dlc + dltt)` | − | Our choice |
| `labour_ratio` | `xlr / sale` (salaries and benefits over revenue) | + | Our choice. F2 A2 names labour cost. Malone et al. do not test labour (p. 9) |
| `gov_payer_share` | Medicare plus Medicaid share of revenue, from the filing | + | agency weight: S&P payor profile in scale, scope and diversity (2014 para. 42). Malone et al. find Medicaid mix not significant (+0.02, p. 7) |

### Medical products (A4)
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev` | log of `(dlc + dltt) / oibdp`, clipped | + | Our choice |
| `fcf_debt` | `(oancf − capx) / (dlc + dltt)` | − | Our choice |
| `margin_trend` | 8-quarter slope t-statistic of `oibdpq / saleq` | − | Our choice |
| `consumable_share` | Consumables and disposables share of revenue, from the segment note | − | agency weight: S&P Section 17, "stable and recurring revenue stream" |
| `rd_int` | `xrd / sale` against the peer median | − | agency weight: S&P Section 17 asks for R&D "at least comparable to peers'" |

Health care technology follows the A6 drivers of `4510-software-services.md`.

## Downside case
1. Providers: cut the base EBITDA by the largest payment-rate change in the last ten annual payment rules for the issuer's main service line. Add the worst 4-quarter rise in labour cost per unit of volume from the issuer's own last five years.
2. Providers: run a volume case with elective procedures deferred. Take the depth and length from the issuer's own 2020 quarters.
3. Providers: hold revenue flat in the recession case. S&P finds no recession revenue decline since 1968 (2014 para. 12). The margin falls instead.
4. Medical products: take the 2020 elective-procedure stop as the volume template for products in discretionary procedures. For high medical-necessity products use the A4 template at half depth (Our choice). Add one recall or product withdrawal on the largest product line.

## Collateral and recovery
- Providers: owned facilities at sale-leaseback value (F7 A2). Receivables net of contractual allowances, at the low end of the F7.5 band.
- Government payers can recoup past overpayments from future payments. Recoupment claims rank with care (F2 A2). Size them from disclosed audits and reserves.
- A master lease with a health care landlord can be one contract in a case. Then the issuer must assume or reject all sites together. Read the lease and model both outcomes (Our choice).
- Licences, certificates of need and payer contracts hold value only in a going concern. Give them zero in the liquidation case.
- Medical products: patents and product registrations hold most of the value. Use the F7.5 intangibles band. Product liability mass torts can go to a trust under F5. Size them as a contingent claim.

## Events and calendar
- CMS annual payment rules. The inpatient hospital rule (IPPS) is usually final in early August, effective Oct. 1. The skilled nursing, inpatient rehabilitation, psychiatric and hospice rules follow the same cycle.
- The outpatient hospital (OPPS), physician fee schedule and home health rules are usually final in early November, effective Jan. 1.
- State Medicaid budgets and supplemental payment approvals. Most states start the fiscal year on July 1.
- Federal budget votes on Medicaid and on marketplace subsidies.
- Medical products: FDA clearances and approvals, recalls, and hospital capital budget seasons. Tariff decisions on imported devices.

## Instructions for the analyst
1. Frame the issuer as A2, A4 or A6. Record the government payer share in `issuer_state`.
2. Build analyst EBITDA after bad debt. Remove one-off relief grants. Tag supplemental payments as policy revenue.
3. Compute `lev_lease_adj` and `fccr` for providers. Place EBITDAR coverage on the S&P scale.
4. Size liquidity through the next two payment-rule dates. Treat a rule cut as a cash event.
5. Size recoupment claims and master lease outcomes in the claims view.
6. Run the payment-rule, labour and elective-deferral cases. Hold provider revenue flat in the recession case.
7. Value providers at the trough peer multiple. Value medical products at the peer multiple and the patent life.
8. Gate the memo under F9. Report the S&P margin band beside `margin`.

## Open questions
- Does a multi-year margin level beat `margin_trend` for HY hospital issuers? Test: the three nested fits of the Malone card, step 7. Adopt `margin_3y` if the AUC rises by at least 0.02 in three of four cycles.
- Does government payer share carry a sign in HY provider spreads? No source tests it. Test: add `gov_payer_share` to the GICS 35 sector fit and keep it only if the sign holds.
- No source tests for-profit HY hospital bond spreads (shortlist gap 4). Open Richards and Whaley (2024) next. It covers hospitals after a leveraged buyout.
- Is labour cost a better downside driver than bad debt? Malone et al. find no bad debt effect (p. 7). Test `labour_ratio` against bad debt over revenue in the same fit.
