# 2010 Capital Goods

Archetype (framework F2): A4 Cyclical industrials. Equipment rental fleets differ: frame them as A5 for collateral and capex. Modifiers that often apply: M1 and M3. M1 fits sponsor-owned machinery, building products and distributors. M3 fits defense contractors and tier 2 aerospace suppliers, where one government or one aircraft program can pass 20% of revenue.
GICS industries covered: 201010 Aerospace & Defense, 201020 Building Products, 201030 Construction & Engineering, 201040 Electrical Equipment, 201050 Industrial Conglomerates, 201060 Machinery, 201070 Trading Companies & Distributors (industrial distributors and equipment rental only. Transport equipment lessors go to `2030-transportation.md`).

## Sources
| Source | Type | Date | Opened | Pages or sections used |
|---|---|---|---|---|
| S&P Global Ratings, "Sector-Specific Corporate Methodology" (SSCM). It replaces the separate Key Credit Factors articles for these sectors. Copy filed as Exhibit TDS-2 in South Dakota PUC docket EL26-003: https://puc.sd.gov/commission/dockets/electric/2026/EL26-003/Vol2Section6/Exh2TStevens.pdf | rating agency criteria | July 7, 2025, republished Sept. 26, 2025 | yes | Section 1 Aerospace And Defense (p. 4), Section 5 Building Materials (p. 28), Section 7 Capital Goods (p. 36), Section 14 Engineering And Construction (p. 79), Appendix 3 profitability and SER tables (p. 244) |
| S&P, "Key Credit Factors For The Aerospace And Defense Industry", "...Capital Goods...", "...Engineering And Construction..." | rating agency criteria | 2013 to 2014 | not opened | Status not verified, may be superseded by the 2025 methodology. SSCM lists its April 4, 2024 predecessor as fully superseded |
| Standard & Poor's, "Standard & Poor's Assigns Industry Risk Assessments To 38 Nonfinancial Corporate Industries". Copy: https://maalot.co.il/publications/MT20150505165520.pdf. S&P page https://www.spglobal.com/ratings/en/regulatory/article/-/view/sourceId/8337654 returned 403. | rating agency criteria | Nov. 20, 2013 | yes (copy) | Industry risk table, p. 2 |
| Moody's, "Aerospace and Defense", "Manufacturing", "Construction" rating methodologies | rating agency methodology | not known | not opened | moodys.com needs a login |
| Fitch, sector navigators for industrials | rating agency methodology | not known | not opened | fitchratings.com needs a login |
| `research/cards/habib-ranasinghe-bhuiyan-2025-order-backlog-credit-ratings.md` | peer-reviewed article card | 2025 | yes | Table 4 Panel A, p. 12, and industry split, p. 22 |
| `research/cards/toynbee-2017-order-backlog-disclosure.md`, `rajgopal-shevlin-venkatachalam-2003-order-backlog.md` | article cards | 2017, 2003 | yes | Claim sections |
| `research/cards/bhojraj-bloomfield-jang-yehuda-2021-cost-structure-cds.md` | peer-reviewed article card | 2021 | yes | Table 4, Table 7 |
| `research/cards/kim-kung-2013-asset-redeployability.md` | working paper card | 2013 | yes | Table 4, p. 32 |
Write "not opened" when a source could not be read. Never cite a search snippet.

## Industry risk
Values are the 2013 S&P assessments (1 is very low risk, 6 is very high risk). S&P may have changed them since. SSCM 2025 does not restate them for these sectors.
- S&P cyclicality assessment: aerospace and defense 4, moderately high. Capital goods 3, intermediate. Building materials 4, moderately high. Engineering and construction 3, intermediate. Reason: demand follows the investment cycle, and SSCM Section 7 classes capital goods demand as early, mid or late cycle.
- S&P competitive risk and growth assessment: aerospace and defense 3. Capital goods 3. Building materials 3. Engineering and construction 4, moderately high. The global industry risk is 3 for the first three and 4 for engineering and construction.

## EBITDA, leverage and coverage
- EBITDA definition: analyst EBITDA of F3. Do not add back forward-loss charges on fixed-price contracts. Treat them as recurrent when an issuer books two in eight quarters (Our choice). For equipment rental, use EBITDA less fleet maintenance capex (F2 A5 rule).
- Leverage measure: `lev_gc_total = total_debt / ebitda_adj_analyst`. Use `debt_adj` with the pension deficit for the leverage view (F5 table, `debt_adj` row). SSCM Section 7 names pension cost as a cost flexibility factor.
- Coverage measure: `coverage = (ebitda_adj_analyst - capex) / cash_interest` (F8).
- Agency standard or supplementary ratios for the sector:
  - Aerospace and defense, capital goods, engineering and construction: FOCF to debt, `(cfo - capex) / debt` (SSCM Sections 1, 7, 14). Reason: advance payments and working capital swings make cash flow lumpy.
  - Engineering and construction with capex above peers: CFO to debt, `cfo / debt` (SSCM Section 14).
  - Building materials with a preliminary assessment of intermediate or stronger: CFO to debt (SSCM Section 5). Otherwise FOCF to debt.
  - Equipment rental: S&P moves its assessment toward FOCF to debt when FOCF and FFO diverge (SSCM Section 7). Rental fleets age in a downturn and capex falls.
  - Engineering and construction liquidity: subtract letters of credit outstanding from the revolver. Do not count customer advance payments as free cash (SSCM Section 14, Liquidity).
  - S&P EBITDA margin bands (below average, average, above average): aerospace and defense below 10%, 10% to 18%, above 18%. Capital goods manufacturers below 11%, 11% to 18%, above 18%. Equipment rental below 30%, 30% to 40%, above 40%. Industrial distributors below 5%, 5% to 9%, above 9%. Engineering and construction below 6%, 6% to 11%, above 11%. General building products below 9%, 9% to 18%, above 18% (SSCM Appendix 3). Use them as an outside check on `margin` ranks, not as F8 bands.

## Drivers
Common drivers for all sub-industries. These are the industrials list of `hy/sector/drivers.py` plus one agency ratio.

| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev` | `log(clip((dlc + dltt) / ltm oibdp, 0.1, 20))` | + | Our choice (methodology 7.2 sign, `SECTOR_DRIVERS["industrials"]`) |
| `ebitda_cyc` | minus the worst YoY change in `oibdp` over 10 fiscal years | + | Our choice (F2 A4, `docs/factors/SECTOR-models.md` 3.1) |
| `margin_trend` | 8-quarter t-statistic of `oibdpq / saleq` | − | Our choice. Agency weight: SSCM Section 7 reads cost position from the EBITDA margin against peers |
| `coverage` | `clip(ltm oibdp / ltm xint, -5, 30)` | − | Our choice |
| `fcf_debt` | `clip((oancf - capx) / debt, -1, 1)` | − | Agency weight: FOCF to debt is the S&P preferred ratio (SSCM Sections 1, 7, 14) |

No source in the repo tests these five drivers on spreads in this group.

### 201010 Aerospace & Defense
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `rpo_intensity` | remaining performance obligation or backlog over LTM `sale` | − | Tested on ratings, not spreads: Habib et al. (2025), `LN_OB` 0.221 (se 0.063), Table 4 Panel A, p. 12. Stronger in manufacturing and business equipment, 0.31 (t 2.68), p. 22 |
| `fixed_price_share` | fixed-price contract revenue over revenue, from the contract-type footnote | + | Agency weight: SSCM Section 1. Fixed-price contracts move the overrun risk to the contractor |
| `program_conc` | revenue share of the largest aircraft or weapons program | + | Agency weight: SSCM Section 1. Our choice of formula |

- Separate commercial aerospace from defense in the frame. Commercial suppliers follow OEM production rates. Defense contractors follow procurement and R&D budgets (SSCM Section 1).
- Give a tier 2 build-to-print supplier a weaker position than a supplier that owns the part IP (SSCM Section 1).
- Count aftermarket revenue apart. S&P states that aftermarket sales have a much higher margin than original equipment (SSCM Section 1).

### 201020 Building Products
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `gross_margin` | `(sale - cogs) / sale` | − | Agency weight: SSCM Section 5 reads pass-through ability from gross margin trends against direct peers |
| `rr_share` | repair and remodel revenue over revenue, from the end-market footnote | − | Agency weight: SSCM Section 5. Homebuilder demand is highly cyclical, and repair and replacement demand is very stable |
| `cust_top1` | largest customer share of sales | + | Agency weight: SSCM Section 5 sets more than 20% from one entity as a weak trait. A big-box retailer can be an exception |

### 201030 Construction & Engineering
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `rpo_intensity` | backlog over LTM revenue | − | Tested on ratings (Habib et al. 2025). Agency weight: SSCM Section 14 operating efficiency |
| `fixed_price_share` | fixed-price backlog over total backlog | + | Agency weight: SSCM Section 14. Large first-of-a-kind fixed-price construction carries the most risk |
| `loss_freq` | count of quarters with a contract loss charge in the last 12 quarters | + | Agency weight: SSCM Section 14 judges execution by the size and frequency of contract losses. Our choice of formula |
| `loc_use` | letters of credit outstanding over revolver commitment | + | Agency weight: SSCM Section 14, Liquidity |

### 201040, 201050, 201060 Electrical Equipment, Conglomerates, Machinery
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `book_to_bill` | orders over shipments, last 4 quarters | − | Our choice (F8 A4 metric). Agency weight: SSCM Section 7 counts high cancellation rates in the backlog as a weak trait |
| `aftermarket_share` | service and aftermarket revenue over revenue | − | Agency weight: SSCM Section 7. Aftersales give a more stable income with a higher margin |
| `cost_elasticity` | operating cost elasticity to sales (`hy/clocks.py`) | no sign prior | Tested on CDS in investment grade only. Bhojraj et al. (2021): speculative grade hedge 0.067 (t 0.21), Table 7. Use it as a level control |

### 201070 Trading Companies & Distributors
- Industrial distributors: use `cash_cycle` (F8) and `gross_margin`. S&P margin bands for distributors are below 5%, 5% to 9%, above 9% (SSCM Appendix 3).
- Equipment rental: use `capex_int` with sign +, and fleet age with sign + (Our choice). S&P adjusts toward FOCF to debt (SSCM Section 7).

## Downside case
1. Take the peak-to-trough revenue change of the issuer's GICS industry in 2008 to 2009 and in 2020. Measure it from the repo annual panel. Use the worse one.
2. Shift the trough by the backlog cover. A late-cycle issuer with `rpo_intensity` above 1 reaches its trough one year later (Our choice).
3. Apply operating leverage to the revenue fall. Use the issuer's own fixed cost share from the last downturn, or `cost_elasticity` when no downturn is in its history.
4. Release working capital on the way down. SSCM Section 7 states that inventory and receivable liquidation lifts FOCF early in a downturn. Reverse the release in the recovery year.
5. For aerospace and defense and for engineering and construction, add one forward-loss charge on the largest fixed-price program. Size it as the program's estimate at completion margin (Our choice).
6. For defense, add a funding delay of one quarter of cash receipts at the start of the US fiscal year (Our choice). For commercial aerospace, cut the largest program to its last trough production rate.

## Collateral and recovery
- Basis: plant and equipment at orderly liquidation value, and receivables (F2 A4). F7 method for A4: EV to mid-cycle EBITDA and going concern at the trough multiple.
- Use the F7.5 table. Machinery 10% to 20%. Inventory 60% to 75%, with work in progress low. Aerospace and engineered machinery hold more work in progress, so start at the low end.
- Equipment rental fleets are generic and mobile. Value them at appraised orderly liquidation value, the A5 basis. Use `redeploy_r` (Kim and Kung) for the industry as a cross-check.
- Claims that differ from F5 defaults: pension termination claims (`claim_haircut_pension`) and warranty claims (F2 A4). Customer advance payments in engineering and construction become claims when work stops. Add them to the unsecured pool `P_U`.
- Surety indemnity claims in engineering and construction rank as general unsecured claims (Our choice. No repo source tests their size).

## Events and calendar
- ISM Manufacturing PMI, first business day of each month.
- US Census durable goods orders (advance report, then full M3 report), monthly.
- Issuer orders and backlog in each 10-Q and 10-K. F2 A4 lists order and backlog releases as an event class.
- Aircraft OEM monthly deliveries and production rate announcements, for aerospace suppliers.
- US defense budget request (usually February), appropriations, and continuing resolutions before the fiscal year starts on October 1.
- US Census housing starts and construction spending, monthly, for building products and engineering and construction.

## Instructions for the analyst
1. Frame the issuer as A4. Name the cycle position: early, mid or late cycle (SSCM Section 7).
2. Split revenue into original equipment and aftermarket. Split contracts into fixed-price and cost-plus.
3. Normalise EBITDA. Keep forward-loss charges in the analyst number. Add the pension deficit to `debt_adj`.
4. For engineering and construction, subtract letters of credit from the revolver in `liquidity_L_eff`.
5. Compute FOCF to debt beside `lev_gc_total`. Use CFO to debt for building products when S&P would.
6. Size pension, warranty and customer advance claims in the F5 claims view.
7. Run the downside case with the backlog lag and the working capital release.
8. Value at the trough multiple (F7 A4). Gate the call against the market-implied recovery (F9).

## Open questions
- Does `rpo_intensity` price HY spreads, not only ratings? Test: regress log spread on `rpo_intensity` and the 7.2 features in this group, as in the Habib card. Read the sign against the permutation null.
- Is `book_to_bill` monotone in spread? Toynbee (2017) states that firms often count cancellable orders. Test the sign by quintile, and split by disclosure of cancellable orders.
- What haircut applies to US government receivables in a default? Anti-assignment rules may limit their value as collateral. No repo source covers it. Open a legal source before a default memo uses a number.
- Does `fixed_price_share` carry a positive sign in spread after margin? S&P states that fixed-price contracts offer higher margins (SSCM Section 1). Test both drivers together.
