# 5510 Utilities

Archetype (framework F2): no F2 row fits regulated utilities exactly. Frame them as A5 Asset-heavy contracted, with the rate order in place of the contract. Two sub-industries differ. Frame merchant power producers as A3, because a traded power price sets revenue. Frame contracted power producers, renewables platforms and project holdcos as A7 (F2 lists power under A7). Modifiers that often apply: M1 (sponsor-owned power producers) and M3 (one plant or one offtaker above 20% of revenue).
GICS industries covered: 551010 Electric Utilities, 551020 Gas Utilities, 551030 Multi-Utilities, 551040 Water Utilities, 551050 Independent Power and Renewable Electricity Producers.

Most regulated operating utilities hold investment grade ratings. HY exposure in this group sits mainly in utility holdcos, power producers and project holdcos. The drivers below follow that mix.

## Sources
| Source | Type | Date | Opened | Pages or sections used |
|---|---|---|---|---|
| S&P Global Ratings, "Sector-Specific Corporate Methodology" (SSCM). Copy filed as Exhibit TDS-2 in South Dakota PUC docket EL26-003: https://puc.sd.gov/commission/dockets/electric/2026/EL26-003/Vol2Section6/Exh2TStevens.pdf | rating agency criteria | July 7, 2025, republished Sept. 26, 2025 | yes | Section 30 Regulated Utilities (p. 164), Section 38 Unregulated Power And Gas (p. 212), Appendix 3 (p. 244) |
| S&P, "Key Credit Factors For The Regulated Utilities Industry" (Nov. 19, 2013) and "Key Credit Factors For The Unregulated Power And Gas Industry" (March 28, 2014) | rating agency criteria | 2013, 2014 | not opened | Status not verified, may be superseded by the 2025 methodology |
| Standard & Poor's, "Standard & Poor's Assigns Industry Risk Assessments To 38 Nonfinancial Corporate Industries". Copy: https://maalot.co.il/publications/MT20150505165520.pdf | rating agency criteria | Nov. 20, 2013, editor's note March 28, 2014 | yes (copy) | Industry risk table, p. 2 |
| Moody's, "Regulated Electric and Gas Utilities" and "Unregulated Utilities and Unregulated Power Companies" methodologies | rating agency methodology | not known | not opened | moodys.com needs a login |
| Fitch, utilities sector navigators | rating agency methodology | not known | not opened | fitchratings.com needs a login |
| `research/cards/becker-josephson-xu-2023-executory-contract-rejection.md` | article card | 2023 | yes | Claim |
| `research/cards/coyle-2025-maturity-walls.md` | working paper card | 2025 | yes | Claim, pp. 1, 4 |
| `research/cards/radhakrishnan-2026-ai-buildout-risk.md` | practitioner note card | 2026 | yes | Claim |
Write "not opened" when a source could not be read. Never cite a search snippet.

## Industry risk
Values are the 2013 S&P assessments (1 is very low risk, 6 is very high risk). S&P may have changed them since.
- S&P cyclicality assessment: regulated utilities 2, low. Unregulated power and gas 4, moderately high. SSCM Section 38 restates the 4. S&P says recession data for the young unregulated sector is limited and inconclusive, so it aligns cyclicality with competitive risk.
- S&P competitive risk and growth assessment: regulated utilities 1, very low. Unregulated power and gas 4, moderately high. Global industry risk: 1 and 4. Regulated utilities also have the narrowest EBITDA SER bands among corporates in SSCM Appendix 3: category 1 is 3% or less.

## EBITDA, leverage and coverage
- EBITDA definition, regulated: reported EBITDA with regulatory accounting kept. S&P does not remove the effects of regulatory accounting (SSCM Section 30). Remove the revenue and expense of securitised recovery bonds, and deconsolidate that debt (SSCM Section 30).
- EBITDA definition, power producers: EBITDA at the forward curve and at a stress curve, with the hedge book marked (F2 A3). For A7 issuers, use project EBITDA and debt service coverage at the asset, and holdco coverage from distributions only.
- Leverage measure: `lev_gc_total` on `debt_adj`. Add imputed debt for long-term purchased power agreements, for regulated utilities and for power producers (SSCM Sections 30, 38). For gas distributors, net storage inventory against short-term debt when near-term cost recovery is certain (SSCM Section 30).
- Coverage measure: `coverage = (ebitda_adj_analyst - capex) / cash_interest`. Capex is large in this group, so also report EBITDA over interest. For a holdco, use `distributions / holdco cash_interest`.
- Agency standard or supplementary ratios for the sector:
  - SSCM Sections 30 and 38 name no supplementary ratio. They set the volatility table instead.
  - Regulated, low volatility table: about two thirds or more of cash flow from low-risk regulated networks, with a strong regulatory advantage (SSCM Section 30).
  - Regulated, medial table: about half or more of cash flow comes from regulated activities with at least adequate regulatory advantage. Country risk must be 4 or better (SSCM Section 30).
  - Power producers, medial table only with a large share from regulated or strongly protected revenue: capacity payments, contracts for difference, feed-in tariffs, PPAs, and take-or-pay contracts. A baseload PPA usually does not qualify (SSCM Section 38).
  - Profitability: S&P sets no fixed margin bands for regulated utilities. It compares the earned ROE with the authorised ROE (SSCM Section 30, Appendix 3). Unregulated EBITDA margin bands are below 15%, 15% to 30%, above 30%. Retail suppliers are below 5%, 5% to 10%, above 10% (SSCM Appendix 3).

## Drivers

### Regulated utilities and utility holdcos (551010 to 551040)
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev` | `log(clip(debt_adj / ltm oibdp, 0.1, 20))` | + | Our choice (`SECTOR_DRIVERS["utilities"]`) |
| `coverage` | `clip(ltm oibdp / ltm xint, -5, 30)` | − | Our choice (`SECTOR_DRIVERS["utilities"]`) |
| `mat_wall` | `clip((dd1 + dd2) / (dlc + dltt), 0, 1)` | + | Our choice (`SECTOR_DRIVERS["utilities"]`). Coyle (2025) models a 36 bp spread rise from walls across all sectors (p. 4), not utilities alone |
| `roe_gap` | earned ROE minus authorised ROE, weighted by rate base per jurisdiction | − | Agency weight: SSCM Section 30 profitability |
| `reg_lag` | change in regulatory assets for deferred costs over rate base, last 8 quarters | + | Our choice. SSCM Section 30 counts timely cost recovery as financial stability |
| `capex_int` | `clip(ltm capx / ltm sale, 0, 2)` | + | Our choice. SSCM Section 30 counts a large, complex capex program as a weak trait |

- Regulatory advantage replaces competitive advantage. S&P scores four sub-factors per jurisdiction: regulatory stability, tariff design, financial stability, and regulatory independence. Business strategy then moves the score up or down (SSCM Section 30).
- Industrial load in a one-industry local economy adds cyclicality (SSCM Section 30). Record the industrial share of load as a flag.

### Independent power and renewable producers (551050)
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `contracted_share` | gross margin under contract or hedge in the next 3 years over total gross margin | − | Agency weight: SSCM Section 38. Contracts with creditworthy offtakers longer than 8 years count as a strong trait |
| `contract_tenor` | gross-margin-weighted years left on PPAs and contracts for difference | − | Agency weight: SSCM Section 38 |
| `merit_pos` | capacity-weighted plant variable cost against the regional clearing price | + | Agency weight: SSCM Section 38, merit order position |
| `log_lev` | `log(clip(debt_adj / ltm oibdp, 0.1, 20))` | + | Our choice |
| `offtaker_conc` | largest offtaker share of contracted revenue | + | Agency weight: SSCM Section 38. Framework M3 |

- Put the regional spark spread or forward power price in the sector-by-date effect η, not in the issuer list. It is common to all issuers in one market (Our choice, by analogy with the shipping freight factor of the Kavussanos card).
- A short position is a loss trigger. S&P weighs a history of temporary short positions, where a plant outage forces spot purchases to meet fixed-price sales (SSCM Section 38).
- The Radhakrishnan (2026) card finds data centre contracts concentrated, with start dates the provider does not control. By analogy, apply M3 to a large data centre load contract (Our choice).

## Downside case
1. Regulated: hold rates flat for two years while capex continues. Fund the gap with debt (Our choice).
2. Regulated: disallow from rate base the capex above the approved budget on the largest project (Our choice).
3. Regulated: add one storm or wildfire cost with recovery delayed by two years. Size it from the largest such cost in the jurisdiction history.
4. Power producers: drop forward power and capacity prices to the lowest level in the last 10 years at each hub. Hold contracted volumes at contract prices, and test each offtaker for default.
5. Power producers: add a forced outage at the largest plant during the worst price spike in the last 10 years. Buy the short volume at that spot price (SSCM Section 38).
6. All: refinance `mat_wall` debt at the stress spread of F6. Post collateral on the hedge book at the price spike.

## Collateral and recovery
- Regulated operating utilities: first mortgage bonds hold a lien on utility plant. Value is rate base times the regulated multiple, as a going concern. Liquidation is not a realistic case (F7.8).
- Utility holdco debt is structurally subordinated to operating company debt and preferred stock (F2 A7). Ring-fence terms can block distributions. Read the regulator orders on dividends.
- Securitised recovery bonds sit outside the estate. S&P deconsolidates them (SSCM Section 30). Exclude them from claims and from asset value.
- Power producers: value plants at appraisal under the stress curve (F7 A3 or A7). Project debt is non-recourse. The holdco recovers only the equity residual after project debt.
- PPAs are executory contracts. Becker, Josephson and Xu (2023) state that the option to reject executory contracts raises debt capacity (p. 2). A rejected above-market PPA becomes a counterparty claim in `P_U`. Whether the federal energy regulator can block a rejection is not settled in the repo.
- Hedge counterparties hold termination claims (F2 A3). Size them at the stress curve mark.

## Events and calendar
- Rate case filings, staff recommendations, and commission orders on state dockets. Fuel and purchased power adjustment filings.
- Federal energy regulator orders on transmission ROE and on wholesale market rules.
- Capacity auctions: PJM Base Residual Auction, ISO New England Forward Capacity Auction, MISO Planning Resource Auction.
- EIA weekly natural gas storage report, Thursday. Forward power and gas curves, daily.
- Summer and winter peak seasons. Atlantic hurricane season from June 1 to November 30. Wildfire season by region.
- Tax credit rule releases for renewable generation.

## Instructions for the analyst
1. Frame each segment: regulated (A5), merchant (A3), or contracted and project (A7).
2. Score each jurisdiction on the four S&P regulatory sub-factors. Record the earned and authorised ROE.
3. Add PPA imputed debt to `debt_adj`. Deconsolidate securitised recovery bonds.
4. For a holdco, compute coverage from distributions only. Read the ring-fence and dividend limits.
5. For power producers, mark the hedge book at the forward and the stress curve.
6. Run the downside case. Add the collateral call under the price spike to `liquidity_L_eff`.
7. Size hedge termination and PPA rejection claims in the F5 claims view.
8. Value regulated assets on rate base and plants at the stress curve. Gate the call against implied recovery (F9).

## Open questions
- Does `roe_gap` or `reg_lag` price HY utility holdco spreads? Test: regress log spread on both and the 7.2 features. Few HY issuers exist, so read the result against the issuer permutation null.
- Does a change in regional spark spread predict next-month spread changes of power producer bonds? Test: the Kavussanos card regression with the power price index as `E`. A pass adds it to S7.
- Can a debtor reject a PPA without the energy regulator's consent? No repo source covers it. Open the court rulings and record the rule in a decision page.
- How large are wildfire tort claims in the unsecured pool? No repo source covers it. Collect claims registers from utility Chapter 11 cases before a memo uses a size.
