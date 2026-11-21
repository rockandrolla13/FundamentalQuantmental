# 2030 Transportation

Archetype (framework F2): A5 Asset-heavy contracted for airlines, marine shipping, rail and transport equipment lessors. Three sub-industries differ. Frame trucking and asset-light logistics as A4. Frame toll roads, airports and ports as A7 when one concession carries the debt. Modifiers that often apply: M1 (sponsor-owned trucking and logistics) and M3 (a shipowner with one charterer above 20% of revenue).
GICS industries covered: 203010 Air Freight & Logistics, 203020 Passenger Airlines, 203030 Marine Transportation, 203040 Ground Transportation (rail and trucking), 203050 Transportation Infrastructure. GICS may place a transport equipment lessor in 201070 Trading Companies & Distributors. We cover lessors here, because their drivers follow the asset.

## Sources
| Source | Type | Date | Opened | Pages or sections used |
|---|---|---|---|---|
| S&P Global Ratings, "Sector-Specific Corporate Methodology" (SSCM). Copy filed as Exhibit TDS-2 in South Dakota PUC docket EL26-003: https://puc.sd.gov/commission/dockets/electric/2026/EL26-003/Vol2Section6/Exh2TStevens.pdf | rating agency criteria | July 7, 2025, republished Sept. 26, 2025 | yes | Section 28 Railroad, Package Express, And Logistics (p. 155), Section 36 Transportation Cyclical (p. 194), Section 37 Transportation Infrastructure (p. 201), Appendix 3 (p. 244) |
| S&P, "Key Credit Factors For The Transportation Cyclical Industry" and "...Transportation Infrastructure Industry" | rating agency criteria | before 2024 | not opened | Status not verified, may be superseded by the 2025 methodology. SSCM lists its April 4, 2024 predecessor as fully superseded |
| S&P, "Key Credit Factors For The Operating Leasing Industry" | rating agency criteria | not known | not opened | SSCM lists it as related criteria. We found no public copy. |
| Standard & Poor's, "Standard & Poor's Assigns Industry Risk Assessments To 38 Nonfinancial Corporate Industries". Copy: https://maalot.co.il/publications/MT20150505165520.pdf | rating agency criteria | Nov. 20, 2013 | yes (copy) | Industry risk table, p. 2 |
| Moody's, "Passenger Airlines" methodology (August 2021, per third-party filings), and the shipping and surface transportation methodologies | rating agency methodology | 2021 and not known | not opened | moodys.com needs a login |
| Fitch, transportation sector navigators | rating agency methodology | not known | not opened | fitchratings.com needs a login |
| `research/cards/ciliberto-schenone-2012-airline-bankruptcy-competition.md` | peer-reviewed article card | 2012 | yes | Tables 6 to 9, pp. 46 to 49, and p. 12 |
| `research/cards/kavussanos-tsouknidis-shipping-bond-spread-changes.md` | working paper card | undated, about 2015 | yes | Table 6, p. 41, and pp. 23 to 24 |
| `research/cards/benmelech-bergman-2009-collateral-pricing.md`, `benmelech-bergman-2011-collateral-channel.md` | article cards | 2009, 2011 | yes | Table 6, Table 12, Table VI, Table VII |
| `research/cards/gavazza-2010-asset-liquidity-aircraft-leases.md` | peer-reviewed article card | 2010 | yes | pp. 64 to 65, Table 5 |
| `research/cards/altamuro-johnston-pandit-zhang-2012-operating-leases-credit.md`, `jung-scarlat-2024-asc842-bond-yields.md` | article cards | 2012, 2024 | yes | Claim sections |
| `research/cards/chen-kacperczyk-ortiz-molina-2010-unions-debt.md` | article card | 2010 | yes | Table III, Table IV |
Write "not opened" when a source could not be read. Never cite a search snippet.

## Industry risk
Values are the 2013 S&P assessments (1 is very low risk, 6 is very high risk). S&P may have changed them since.
- S&P cyclicality assessment: transportation cyclical (airlines, shipping, trucking) 5, high. Railroads and package express 3, intermediate. Transportation infrastructure 2, low. Transportation leasing 2, low. Reason: S&P states that cyclical transportation has high operating leverage from large fixed assets (SSCM Section 36). Its EBITDA SER bands are the widest of all sectors in SSCM Appendix 3: category 6 starts above 106%, against 52% overall.
- S&P competitive risk and growth assessment: transportation cyclical 4, moderately high. Railroads and package express 2, low. Transportation infrastructure 2, low. Transportation leasing 3, intermediate. Global industry risk: 5, 2, 2 and 3.

## EBITDA, leverage and coverage
- EBITDA definition: EBITDAR for airlines, chartered-in shipping and trucking with leased tractors. For shipping, use EBITDA less drydock and special survey capex. For lessors, use EBITDA less depreciation, because depreciation is the asset value loss (Our choice).
- Leverage measure: `lev_lease_adj = (debt + lease_debt) / (ebitda_adj_analyst + rent)` (F8). Use the ASC 842 lease liability when reported, and `8 * xrent` only as the fallback (`hy/sector/drivers.py` `LEASE_MULTIPLE`). Altamuro et al. (2012) state that lease-adjusted ratios explain loan spreads better than reported ratios.
- Coverage measure: `fccr` with rent (F8, required for A5 airlines). For rail and infrastructure, use `(ffo + cash_interest) / cash_interest`.
- Agency standard or supplementary ratios for the sector:
  - Transportation cyclical: S&P weights its ratios 50% on the current year and 50% on the first forecast year, because it views the sector as prospectively volatile (SSCM Section 36). Copy this weight in the F6 base case for airlines, shipping and trucking.
  - Railroads and package express: `(ffo + cash_interest) / cash_interest` and EBITDA to interest. FOCF to debt for capital intensity (SSCM Section 28). S&P states that a railroad more likely defaults because it runs out of cash than because its capital structure fails.
  - Transportation infrastructure: FFO to debt is the core ratio, and FFO cash interest coverage is the supplementary ratio (SSCM Section 37).
  - S&P margin bands (below average, average, above average): shipping EBITDA margin below 10%, 10% to 30%, above 30%. Trucking and airlines below 8%, 8% to 15%, above 15%. Railroads EBIT margin below 18%, 18% to 36%, above 36%. Package express and logistics EBIT margin below 4%, 4% to 7%, above 7%. Transportation infrastructure EBITDA margin below 30%, 30% to 55%, above 55% (SSCM Appendix 3).

## Drivers

### 203020 Passenger Airlines
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev_lease` | `log((debt + lease_debt) / (ltm oibdp + xrent))`, capped at 20x | + | Our choice (`hy/sector/drivers.py`, methodology Section 4.3). Altamuro et al. (2012) test lease-adjusted ratios on loan spreads |
| `fccr` | `(ebitda_adj_analyst + rent) / (cash_interest + rent)` | − | Our choice (F8, A5) |
| `casm_gap` | unit cost without fuel minus the peer median, per available seat mile | + | Agency weight: SSCM Section 36. Labour cost is a good way to tell airline cost structures apart |
| `redeploy_operators_5` | fleet-weighted count of operators with 5 or more aircraft of each type | − | Tested on secured aircraft tranches at issue: Benmelech and Bergman (2009), −0.523 (t −2.39), Table 6. Secured tranches only |
| `peer_shock` | peer bankruptcies on the same aircraft types (`hy/clocks.py`) | + | Tested on secured tranches: Benmelech and Bergman (2011), 64.666 (se 27.984), Table VI. The effect reverses 120 to 240 days after exit (Table VII) |

- Rival effect of a peer filing (Ciliberto and Schenone 2012). The filer cuts seats on a route by about 35% after emergence: −0.426, or −34.7%, Table 7, p. 47. Rivals see near zero product-market effect: seats −5.7% with route trends and +2.0%, not significant, without them (Table 7). Rival fares move +0.8% (Table 8). Rival load factors rise about 3 log points (Table 9).
- So set the `product_market` channel to zero for a rival bond. Keep the `collateral` channel for secured tranches on shared types through `peer_shock` (card decision, our proposal). Move no rival unsecured bond on a peer filing.
- The filer cuts fares and seats in the one to three quarters before it files (Tables 5, 7, 8). Use this pattern as a hazard input for A5 airlines, not as a signal.

### 203030 Marine Transportation
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `sector_earn_chg` | month change of the log freight earnings index (ClarkSea), lag one month | − | Tested on weekly spread changes: Kavussanos and Tsouknidis, sum of freight lags −0.1218, Table 6, p. 41, pp. 23 to 24. A common sector factor. Put it in the sector-by-date effect η and the S7 tilt, not in the issuer driver list |
| `charter_cover` | revenue days under fixed-rate time charter in the next 12 months over available days | − | Agency weight: SSCM Section 36. Long fixed-rate charters give less volatile revenue than spot |
| `fleet_age` | capacity-weighted mean vessel age | + | Agency weight: SSCM Section 36 |
| `vessel_ltv` | secured debt over charter-free fleet market value | + | Our choice (F2 A5 collateral basis) |
| `log_lev` | `log(clip(debt / ltm oibdp, 0.1, 20))` | + | Our choice |

- Freight earnings lags drive shipping spread changes. Kavussanos and Tsouknidis find lags of 2 to 4 weeks, with a negative net sign (p. 23). VIX and a cyclical bond index also enter. Issuer market leverage and Altman z do not survive the final model (card, "Use for the A5 archetype").
- The card flags limits. The liquidity proxy holds the bond price. Two-way clusters cut t values by about 2 to 4 times. The test is on changes, not on levels.
- Segment matters. S&P views dry bulk as far more volatile than gas carriers on long take-or-pay charters (SSCM Section 36).

### 203040 Ground Transportation: trucking (A4 frame)
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `op_ratio` | operating expenses with depreciation over operating revenue | + | Agency weight: SSCM Section 36 |
| `ebitda_cyc` | minus the worst YoY change in `oibdp` over 10 fiscal years | + | Our choice (F2 A4) |
| `contract_share` | contract revenue over contract plus spot revenue | − | Agency weight: SSCM Section 36 |
| `fleet_age` | mean tractor age | + | Agency weight: SSCM Section 36. Younger fleets need less capex |

### 203040 Ground Transportation: rail
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `coverage` | `(ffo + cash_interest) / cash_interest` | − | Agency weight: SSCM Section 28 |
| `fcf_debt` | `clip((oancf - capx) / debt, -1, 1)` | − | Agency weight: SSCM Section 28 |
| `log_lev` | `log(clip(debt / ltm oibdp, 0.1, 20))` | + | Our choice |

### 203050 Transportation Infrastructure (A7 frame)
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `ffo_debt` | `ffo / debt` | − | Agency weight: SSCM Section 37 core ratio |
| `ffo_cover` | `(ffo + cash_interest) / cash_interest` | − | Agency weight: SSCM Section 37 supplementary ratio |
| `concession_tail` | years from the final debt maturity to the concession end | − | Agency weight: SSCM Section 37. S&P assesses negative leverage tolerance without a credible plan to repay well before the concession ends |
| `heavy_share` | heavy vehicle or commodity share of traffic | + | Agency weight: SSCM Section 37. Heavy goods traffic reacts more in a downturn |

### Transport equipment lessors
- Use `redeploy_operators_5` for aircraft and `redeploy_r` for other assets (Gavazza card update). Use `fleet_age` and the weighted lease term left.
- S&P rates operating lessors under a separate criteria article that we did not open. Decide A5 against A8 only after that article is read.

## Downside case
1. Airlines: cut revenue by the worse of the 2008 to 2009 and the 2020 sector peak-to-trough, from the repo panel. Add a fuel shock to the last peak price, net of the hedge book.
2. Airlines in the claims view: build the filer as a smaller carrier. Scale going-concern revenue and fleet by about −35%, the seat cut of Ciliberto and Schenone, Table 7 (default under R9).
3. Shipping: drop time charter equivalent earnings to the trough of the freight index over the last 15 years. Roll each charter to that rate at expiry. Drop vessel values with earnings, then test the loan minimum value clauses.
4. Trucking: cut spot rates to the last trough. Hold contract rates until each renewal date. Release receivables on the way down (F2 A4).
5. Infrastructure: cut traffic by the worst year in the asset history. Hold tariffs at the concession formula, and test the distribution lock-up (F2 A7).
6. Rail: cut carloads by the worse of the last two recessions. Rail has high fixed cost, so apply the issuer's own operating leverage from that recession.

## Collateral and recovery
- Section 1110 lets a lessor or secured lender take an aircraft after a 60-day grace period (Gavazza p. 64, Ciliberto p. 12). F5 treats aircraft and vessel financings as secured, with their own cure-or-surrender regime.
- An operating lessor counts as the owner. A capital lessor counts as a secured lender, roughly (Gavazza pp. 64 to 65). A rejected aircraft lease becomes a general unsecured claim (Ciliberto p. 12). Equipment lease claims are not capped (F2 A5).
- Most lessors renegotiate rather than repossess, because redeployment in a distressed industry can cost more (Ciliberto p. 12). So the lease claim in the rejection set is often a rate cut, not a full rejection.
- Value aircraft and vessels at appraised forced-sale value (F7 A5). Use charter-free values for vessels. A widely flown type keeps more value: weight the appraisal by `redeploy_operators_5`.
- Rail track and infrastructure concessions have little liquidation value. Value them as a going concern (F7 A7 project DCF). Concession assets may revert to the grantor. Read the termination compensation clause.
- Airline slots, routes and loyalty programs hold going-concern value. Their value falls in a liquidation (Our choice).
- Holdco debt above an infrastructure concession is structurally subordinated (F2 A7).

## Events and calendar
- Airlines: monthly traffic releases by carriers. US DOT T-100 traffic data (monthly) and DB1B fare sample (quarterly). TSA checkpoint throughput (daily). EIA jet fuel prices (weekly).
- Airline peer Chapter 11 filing: add it to the A5 event class with two channels, `collateral` and `product_market` (Ciliberto card, our proposal).
- Shipping: ClarkSea index (weekly) and the Baltic Dry Index (daily). Vessel appraisal dates at loan covenant tests.
- Trucking: Cass Freight Index and ATA truck tonnage (monthly). Spot rate indices (weekly).
- Rail: AAR weekly carload reports. Surface Transportation Board rulings.
- Infrastructure: monthly traffic reports. Concession tariff reset dates.
- All A5 issuers: labour contract amendable dates and union votes.

## Instructions for the analyst
1. Frame the issuer as A5, A4 or A7 by sub-industry. Write the segment: dry bulk, tanker, container, gas carrier, or passenger, cargo, truckload.
2. Build EBITDAR and lease-adjusted leverage. Use the ASC 842 liability before the 8 times rent fallback.
3. Weight the base case 50% on the current year and 50% on the first forecast year for cyclical transportation.
4. Compute liquidity with undrawn committed lines and unencumbered aircraft or vessels (F4).
5. Size secured aircraft and vessel claims under Section 1110. Size the lease rejection set with renegotiation as the base outcome.
6. Run the sub-industry downside case. For a filer, use the smaller carrier at about −35% capacity.
7. Value on appraised assets in a forced sale (F7 A5). Weight appraisals by redeployability.
8. On a peer filing, move only secured tranches on shared assets. Gate the call against implied recovery (F9).

## Open questions
- Does a peer airline filing move rival bonds through the route overlap? Test: the `rival_jump` regression of the Ciliberto card on TRACE spreads. The zero rule holds when the overlap slope is not different from zero at 5% in both windows.
- Does `sector_earn_chg` predict next-month spread changes for shipping and airline bonds? Test: the Kavussanos card regression, with clusters by issuer and month and the issuer permutation null. A pass adds it to S7 for that group.
- Do unions lower spreads in airlines, rail and trucking? Chen, Kacperczyk and Ortiz-Molina (2010) find stronger unions with narrower spreads, −186.862 (t 3.33), Table III. But 93% of the variation is across industries, and the sample ends in 1998. The user closed labour for the clocks. Test inside this group with sector effects before use.
- Does `recontract_bite` carry one sign for lessors and lessees? Benmelech and Bergman (2009 draft, p. 6) cite lease renegotiation in poor fleet markets. Split the test by distress (Gavazza card, M1.15).
- Is a transport equipment lessor A5 or A8? Open the S&P operating leasing criteria and record the choice in a decision page.
