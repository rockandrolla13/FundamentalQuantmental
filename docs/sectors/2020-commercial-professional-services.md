# 2020 Commercial and Professional Services

Archetype (framework F2): A4 Cyclical industrials for staffing and volume-driven support services. Two sub-industries differ. Frame contracted asset-light services as A6 when recurring revenue passes 70% (the F2 A6 test). Frame environmental services as A5, because landfills and fleets make it asset heavy and contracted. Modifiers that often apply: M1 (S&P states that most large deals in this sector are leveraged buyouts, SSCM Section 6) and M3 (one large outsourcing contract).
GICS industries covered: 202010 Commercial Services & Supplies (environmental and facilities services, diversified support services, security and alarm services, office services, commercial printing), 202020 Professional Services (human resource and employment services, research and consulting, data processing and outsourced services).

## Sources
| Source | Type | Date | Opened | Pages or sections used |
|---|---|---|---|---|
| S&P Global Ratings, "Sector-Specific Corporate Methodology" (SSCM). Copy filed as Exhibit TDS-2 in South Dakota PUC docket EL26-003: https://puc.sd.gov/commission/dockets/electric/2026/EL26-003/Vol2Section6/Exh2TStevens.pdf | rating agency criteria | July 7, 2025, republished Sept. 26, 2025 | yes | Section 6 Business And Consumer Services (p. 32), Section 15 Environmental Services (p. 84), Appendix 3 (p. 244) |
| S&P, "Key Credit Factors For The Business And Consumer Services Industry" and "...Environmental Services Industry" | rating agency criteria | before 2024 | not opened | Status not verified, may be superseded by the 2025 methodology. SSCM lists its April 4, 2024 predecessor as fully superseded |
| Standard & Poor's, "Standard & Poor's Assigns Industry Risk Assessments To 38 Nonfinancial Corporate Industries". Copy: https://maalot.co.il/publications/MT20150505165520.pdf | rating agency criteria | Nov. 20, 2013 | yes (copy) | Industry risk table, p. 2 |
| Moody's, "Business and Consumer Services" and "Environmental Services and Waste Management" methodologies | rating agency methodology | not known | not opened | moodys.com needs a login |
| Fitch, sector navigator for business services | rating agency methodology | not known | not opened | fitchratings.com needs a login |
| `research/cards/favilukis-lin-zhao-2017-labor-obligations.md` | working paper card | 2017 | yes | Claim |
| `research/cards/becker-josephson-xu-2023-executory-contract-rejection.md` | article card | 2023 | yes | Claim |
| `research/cards/kim-kung-2013-asset-redeployability.md` | working paper card | 2013 | yes | p. 32 |
Write "not opened" when a source could not be read. Never cite a search snippet.

## Industry risk
Values are the 2013 S&P assessments (1 is very low risk, 6 is very high risk). S&P may have changed them since.
- S&P cyclicality assessment: business and consumer services 3, intermediate. Environmental services 2, low. Reason: most waste volume is nondiscretionary, and S&P gives the low volatility table to franchise-protected municipal and medical waste (SSCM Section 15).
- S&P competitive risk and growth assessment: business and consumer services 3, intermediate. Environmental services 2, low. Global industry risk: 3 and 2.

## EBITDA, leverage and coverage
- EBITDA definition: analyst EBITDA of F3. Most issuers are sponsor-owned and acquisitive. S&P states that leveraged buyouts write up assets and distort ROC, and that large acquisitions distort EBITDA (SSCM Section 6). So read `addback_gap` and EQ flags before any ratio. For environmental services, use EBITDA less maintenance capex. Count landfill cell construction as maintenance capex (Our choice).
- Leverage measure: `lev_gc_total`. Add PIK interest to debt each quarter. For environmental services, add landfill closure and post-closure obligations to `debt_adj` (Our choice. We did not open S&P "Ratios And Adjustments").
- Coverage measure: `coverage = (ebitda_adj_analyst - capex) / cash_interest`. Exclude PIK interest from the denominator, and report the PIK share beside it.
- Agency standard or supplementary ratios for the sector:
  - Low working capital and capex: FOCF to debt, `(cfo - capex) / debt` (SSCM Section 6).
  - High dividend payout: DCF to debt, `(cfo - capex - dividends) / debt` (SSCM Section 6).
  - PIK debt from a sponsor: S&P gives more weight to `(ffo + cash_interest) / cash_interest` (SSCM Section 6).
  - Environmental services with a preliminary assessment of intermediate or stronger: FOCF to debt. Weaker: `(ffo + cash_interest) / cash_interest` and EBITDA to interest (SSCM Section 15).
  - S&P EBITDA margin bands (below average, average, above average): facilities services below 10%, 10% to 20%, above 20%. General support services below 15%, 15% to 25%, above 25%. Professional services below 20%, 20% to 30%, above 30%. Distribution services below 5%, 5% to 9%, above 9%. Environmental services below 12%, 12% to 24%, above 24% (SSCM Appendix 3). S&P may weigh peers above these bands (SSCM Section 6).

## Drivers
Common drivers for all sub-industries.

| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev` | `log(clip((dlc + dltt) / ltm oibdp, 0.1, 20))` | + | Our choice (methodology 7.2 sign) |
| `fcf_debt` | `clip((oancf - capx) / debt, -1, 1)` | − | Agency weight: FOCF to debt is the S&P preferred ratio (SSCM Sections 6, 15) |
| `coverage` | cash interest form, `(ffo + cash_interest) / cash_interest` when PIK debt exists | − | Agency weight: SSCM Section 6 |
| `margin_trend` | 8-quarter t-statistic of `oibdpq / saleq` | − | Our choice |

No source in the repo tests these drivers on spreads in this group.

### Human resource and employment services (staffing)
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `ebitda_cyc` | minus the worst YoY change in `oibdp` over 10 fiscal years | + | Our choice (F2 A4) |
| `recv_days` | receivables over revenue times 365 | + | Agency weight: SSCM Section 6 states that receivables drive working capital, and that government customers may pay late |
| `labor_flex` | temporary and part-time staff cost over total direct labour cost | − | Agency weight: SSCM Section 6 names part-time and seasonal staff as a source of cost flexibility. Our choice of formula |

- Staffing revenue moves with temporary employment. The wage bill is the cost of sales, so gross margin per hour holds better than revenue (Our choice).
- Favilukis, Lin and Zhao (2017 draft) state that pre-committed labour payments make interest payments riskier. That claim is aggregate, not tested on staffing bonds.

### Contracted outsourced and support services (A6 frame)
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `retention` | revenue retained from last year's customers over last year's revenue | − | Agency weight: SSCM Section 6 uses contract retention rates to measure service quality |
| `cust_top1` | largest customer share of revenue | + | Agency weight: SSCM Section 6. Framework M3 above 20% |
| `capex_maint_int` | maintenance capex over revenue | + | Agency weight: SSCM Section 6, reinvestment needs |

### Environmental and facilities services (A5 frame)
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `capex_int` | `clip(ltm capx / ltm sale, 0, 2)` | + | Our choice (`hy/sector/drivers.py`) |
| `franchise_share` | revenue under municipal franchise or long-term contract over revenue | − | Agency weight: SSCM Section 15 low volatility table conditions |
| `airspace_years` | permitted and expected landfill airspace over annual tons placed | − | Our choice. SSCM Section 15 calls landfills a barrier to entry that is rarely for sale |
| `vertical_int` | internalisation rate, tons sent to own disposal sites over tons collected | − | Agency weight: SSCM Section 15 prefers integrated firms through commodity price cycles |

## Downside case
1. Staffing: cut revenue by the peak-to-trough change in US temporary help services employment (BLS) in 2008 to 2009 and in 2020. Use the worse one. Hold gross margin per hour, and cut SG&A only with a lag of two quarters (Our choice).
2. Contracted services: remove the largest contract at its next renewal date (M3). Cut `retention` by the issuer's worst annual drop. Reset price on renewed contracts to the peer median margin.
3. Environmental services: drop recycled commodity prices to the last trough. Cut special and industrial waste volume with industrial production in the last recession. Hold franchise collection volume flat.
4. All sub-industries: hold the PIK share. Add capitalised PIK interest to debt in each case quarter (F6 mechanics).
5. Release receivables on the way down for staffing. Reverse it in the recovery year (F2 A4 rule).

## Collateral and recovery
- Basis for asset-light services: going concern value of the customer base (F7 A6). Liquidation value is small. Kim and Kung (2013) rank legal services at the top of redeployability, at 0.68, and oil and gas at 0.12 (p. 32). Redeployability does not make an intangible customer base liquid.
- Receivables follow F7.5 at 85% to 95%. Cut them for government payers, because S&P notes slower payment (SSCM Section 6).
- Staffing claims: unpaid wages and benefits up to the per-employee cap, and certain taxes, rank as priority unsecured claims (F5 table, §507). A staffing issuer can carry a large priority pool. Size it from the payroll cycle at the filing date.
- Environmental services: value permitted landfills at going concern. Closure, post-closure and cleanup obligations travel with the site (Our choice). Do not treat them as dischargeable general unsecured claims until a legal source settles it.
- Long-term service contracts are executory contracts. The debtor can reject them, and Becker, Josephson and Xu (2023) state that the rejection option raises debt capacity (p. 2). Count rejection damages in `P_U`.

## Events and calendar
- BLS Employment Situation report, first Friday of each month. Read the temporary help services line.
- ISM Services PMI, third business day of each month.
- Municipal franchise awards and contract renewal dates in the issuer filings.
- Recycled commodity price indices, monthly, for environmental services.
- Sponsor actions under M1: add-on acquisitions, dividend recaps, and repricings.

## Instructions for the analyst
1. Frame each segment as A4, A6 or A5 with the F2 tests. Report both views when two fit (F2.1).
2. Read `addback_gap` and acquisition add-backs first. Sponsor-owned issuers often show the largest gaps.
3. Split interest into cash and PIK. Add PIK to debt. Compute coverage on cash interest.
4. Compute FOCF to debt, or DCF to debt for a high payout.
5. For staffing, size the wage and payroll tax priority claims in the F5 claims view.
6. For environmental services, add closure and post-closure obligations to `debt_adj`.
7. Run the sub-industry downside case. Value on going concern (A6) or appraised assets (A5).
8. Gate the call against the market-implied recovery (F9).

## Open questions
- Does `retention` price spreads in sponsor-owned services? Test: regress log spread on `retention` and the 7.2 features. Read the sign against the issuer permutation null.
- Does S&P add closure and post-closure obligations to debt? Open "Corporate Methodology: Ratios And Adjustments" and record the rule.
- What share of the wage priority pool reaches the unsecured pool in a staffing default? No repo source covers it. Collect claims registers from staffing Chapter 11 cases.
- Does the A6 frame or the A4 frame give the better recovery forecast for outsourced services? Compute both for each default in the repo panel and compare the error.
