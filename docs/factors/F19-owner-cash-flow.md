# F19. Owner cash flow to debt (maintenance capex adjusted)

- **Rank:** 19. **Tier:** 3 (tested outside credit, or weak credit evidence, buildable now). **Status:** variant of `fcf_to_debt` (methodology Section 4.2). It extends the S1 inputs (Section 8).
- **Sources:** Leng, Ward et al. (Deutsche Bank, 18 Feb 2019), "Value Anatomy", file `/home/ak/Documents/Quant Credit/Work_Quant (1)/Value Anatomy (1).pdf`. PDF page = printed page. Definition pp. 11–13, appendix p. 32. Backtest setup p. 4. Results pp. 22–23. Conflict: Gonzalez, Natividade, Anand (Deutsche Bank, 3 May 2019), "Time To Cross the Bridge", file `.../Work_Quant (1)/Factors/ebec8f2e_e912_4244_887d_25aab7db39ce_604 (1).pdf`, p. 11.
- **Reader blocks:** F-F11 and F-F12 (`research/notes/quant-credit-review/out_F.md`). Every number below was checked on the source page.
- **Corrections to the reader block.** (1) F-F11 cites p. 12 for the min rule. p. 13 says "maximum of the average ... and the current capital expenditure", then "capped at the current level". The appendix (p. 32) says "minimum ... We therefore cap the maintenance investment at its current level". The min is right. p. 13 has a typo. (2) F-F11 says Owner Earnings-to-price has "lower turnover". p. 22 says "relative similar turnover". Lower turnover is the Owner Book-to-price result (p. 23).

## Claim
Among US HY issuers in one GICS sector, those with a higher LTM owner cash flow to total debt have a higher next-month bond excess return over duration-matched Treasuries, beyond spread. The monthly rank IC beyond spread is positive.

## Definition
```latex
\mathrm{MCX}_{i,t} = \min\Big(\mathrm{CAPX}_{i,t},\ \tfrac13\textstyle\sum_{k=0}^{2}\mathrm{CAPX}_{i,t-k}\Big),
\qquad
\mathrm{MAQ}_{i,t} = \min\Big(\mathrm{AQC}_{i,t},\ \tfrac13\textstyle\sum_{k=0}^{2}\mathrm{AQC}_{i,t-k}\Big)
```
```latex
\mathrm{OCF}_{i,t} = \mathrm{CFO}_{i,t} + \mathrm{INT}_{i,t} - \mathrm{MCX}_{i,t} - \mathrm{MAQ}_{i,t},
\qquad
x_{i,t} = \frac{\mathrm{OCF}_{i,t}}{\mathrm{DLC}_{i,t} + \mathrm{DLTT}_{i,t}},
\qquad
\mathrm{score}_{i,t} = \mathrm{pct}_{\text{sector}}(x_{i,t}) - 0.5
```
t is the latest 12-month period, t − k the 12 months k years earlier. Intuition: growth capex is optional in a downturn, so a creditor should count only the capex that keeps the business standing.

What the source says:
- Owner Earnings = net income + R&D + D&A + deferred taxes + other non-cash items − preferred dividends − ΔNWC − maintenance capex − maintenance acquisitions (table, p. 13).
- Interest expense is excluded because it pays the debt holders (p. 12). So the source deducts it.
- Maintenance capex is "the minimum of current capital expenditure and the three-year moving average of capital expenditure". Acquisitions take the same rule (p. 12, p. 32). R&D and other intangibles are growth and are added back (p. 12).
- The rule misclassifies steady growth capex as maintenance (p. 32).
- Backtest: quintile sort, monthly rebalance, sector neutral, financials and real estate excluded (p. 4). MSCI North America, Europe, Asia, 1997–2018 (p. 22).

What we decide:
- Start from Compustat `oancf`. It already deducts ΔNWC, cash taxes and cash interest, and excludes preferred dividends. Our choice.
- Add back gross cash interest (`intpn`, else `xint`). Our choice: the cash flow serves all debt, and CFO already holds the interest tax shield. Reader block F-F11 proposed Int(1 − τ). We reject it because τ is a number the source does not give.
- Do not add R&D back. Our choice: R&D is cash spent, and in HY it sits mostly in two sectors. See open questions.
- Do not deduct preferred dividends. Our choice: preferred stock is junior to the bonds.
- The 3-year mean includes the current year (p. 12: "three-year moving average"). Our choice where p. 13 says "past three years".
- Missing `aqc` counts as 0. Our choice: Compustat leaves it blank for many firms with no deals.
- Alternative proxy `maint="dp"`: MCX = depreciation. This is the floor of `docs/framework.md` F4.7 for archetypes A4 and A5. Default `"min3y"`, the source rule.
- Rank within GICS 2-digit sector over the issuers with an eligible bond at t (p. 4 is sector neutral). Sector rank needs `MIN_SECTOR` = 5 issuers (`hy.peers`), else NaN. Financials (GICS 40, 60) get NaN (p. 4). Total debt ≤ 0 gives NaN. No winsorisation: the rank controls outliers.
- Higher score = long. Our choice of horizon: 1 month, the source's rebalance (p. 4).

## Inputs
| Field | Production table and column | as_of | available_at rule | Have |
|---|---|---|---|---|
| CFO, capex (3-month) | `compustat_quarterly.oancf`, `.capx` (de-cumulated `oancfy`, `capxy`), as in F08 | `datadate` | `rdq`, else snapshot day | need (F08 panel) |
| Debt | `compustat_quarterly.dlcq`, `.dlttq`, as in F08 | `datadate` | same | need (F08 panel) |
| Cash interest (3-month) | **added** `compustat_quarterly.intpn` (de-cumulated `intpny`), fallback **added** `.xintq` | `datadate` | same | need |
| Acquisitions (3-month) | **added** `compustat_quarterly.aqc` (de-cumulated `aqcy`) | `datadate` | same | need |
| Depreciation | **added** `compustat_quarterly.dpq` (only for `maint="dp"`) | `datadate` | same | need |
| Annual fallback | **added** to `compustat_annual` (F09): `oancf`, `capx`, `aqc`, `intpn`, `xint`, `dp`, `dlc`, `dltt` (`comp.funda`) | `datadate`, `fyear` | max(`available_at`, datadate + 90 days) | need |
| GICS sector | `gics.gsector`, `indfrom`, `indthru` | `indfrom` | panel `available_at` | have |
| Universe | `bond_panel` `gvkey` and the `eligible` columns | `date` | panel `available_at` | have |

USD millions. `financials` (`docs/production_wiring.md` 4.2) maps `oancfq`, `capxq`, `intpnq` to the same flows, but no panel exports it. `aqc` is in no table today.

## Build steps
1. At month end t, keep `compustat_quarterly` rows with `available_at` ≤ `decision_time(t)`. Keep the latest version per (gvkey, datadate).
2. Per gvkey, take the last 12 quarters. They must step by one fiscal quarter, and the latest must be at most 270 days old (F08 `STALE_DAYS`).
3. Sum quarters 1–4 (latest), 5–8 and 9–12 into CAPX_t, CAPX_t−1, CAPX_t−2. The same for AQC. CFO and INT are the latest 4-quarter sums. Debt is the latest dlcq + dlttq.
4. An issuer without a valid quarterly block uses `compustat_annual`: fiscal years y, y − 1, y − 2 matched on `fyear`, latest at most 550 days old (`SUST_STALE_DAYS`). Column `fin_source` records the path.
5. Compute MCX, MAQ, OCF and x. Also the control `fcf_debt` = (CFO − CAPX_t) / debt, the plain FCF to debt of the DB note.
6. Drop financials. Rank x within sector over issuers with an eligible bond at t. Copy the issuer score to each eligible bond.

## Code placement
- `hy/factors/f19_owner_cash_flow.py`. `compute(panels, as_of, maint="min3y", interest=True) -> pd.DataFrame`.
- Output: `date`, `cusip`, `score`, `available_at`, `gvkey`, `sector`, `ocf_debt`, `fcf_debt`, `owner_cf`, `cfo`, `interest`, `maint_capex`, `growth_capex`, `maint_acq`, `debt`, `period_end`, `fin_source`.
- Helpers: `maintenance(current, lag1, lag2)`, `owner_cash_flow(...)`, `to_debt(x, debt)`, `quarterly_blocks`, `annual_blocks`, `issuer_values`, `sector_score`.
- Docstrings cite methodology Section 4.2 (`fcf_to_debt`, `capex_flex`) and Section 8 (S1).
- Reuses `hy.backtest.decision_time`, `eligible`; `hy.peers.sector_at`, `FIN_SECTORS`, `SUST_STALE_DAYS`, `_sector_pct`; F08 `STALE_DAYS`, `_consecutive`; F09 `known_annual`.

## Tests
- Unit: no look-ahead (a quarter or restatement after the decision time changes nothing). Sign: within one sector, the issuer with more cash flow per unit of debt scores higher. Growth capex: a capex spike raises OCF against plain FCF. Edges: missing `gics` or `bond_panel`, or both fundamentals panels, gives an empty frame. 11 quarters gives NaN without annual data. A gap or stale quarter gives NaN. Debt ≤ 0 gives NaN. A financial gives NaN. A sector with 4 issuers gives NaN. Missing `aqc` counts as 0. Helpers against hand numbers.
- Evaluation: monthly rank IC of the score beyond `g_spread`, 1-month horizon, after cost from `bid_ask_pts` and turnover. Pass: positive in at least three of the four `CYCLE_WINDOWS`. Conflict test: the same IC for the sector rank of `fcf_debt`. Adopt F19 only if its IC beats `fcf_debt` in at least three cycles. Reader test (F-F11): as an added S1 regressor, out-of-sample spread R² rises by at least 0.01 and the sign (higher x, lower fair spread) holds in every rating cell.

## Risks
- **Conflict with the DB credit note.** On CDS of over 400 CDX IG and HY names, January 2004 to December 2018 (p. 3), "free cash flows to debt, interest coverage ratio, net debt to EBITDA" gave results that "were inconclusive". None was "as defensive and economically significant as the DTD signal" (p. 11). Value Anatomy finds the owner adjustment helps equity value, with "higher returns, lower volatility, lower drawdowns" than E/P (p. 22). When each is right: the DB result holds for liquid CDS, where a market-based DTD reacts faster than quarterly filings. The equity result holds for a valuation signal scaled by price. Neither tests owner cash flow over debt in HY bonds. **Our choice:** build F19 as an S1 input and a ranked factor, and keep `fcf_debt` beside it. The conflict test above settles it. Reason: the DB note gives no number, so "inconclusive" is no evidence of a wrong sign, and HY bonds are slower and more fundamental than CDX names.
- Evidence sits in charts only (pp. 22–23). The source states no Sharpe ratio in the text.
- Overlap: high with leverage (S1 peer input) and with F02 distance to default. The source states no correlation.
- Capex-heavy sectors (energy, telecom, cable) mix growth and maintenance capex. The min rule counts steady growth as maintenance (p. 32).
- IFRS filers may report interest paid in financing. The add-back then double counts. Compustat North America is mostly US GAAP.
- Turnover is low: inputs change once a quarter.

## Open questions
- R&D. The source adds it back (p. 12). Default: no. A run with R&D added back settles it for sectors 35 and 45.
- Maintenance proxy. Default: min rule (pp. 12, 32). The `dp` proxy follows framework F4.7. A sales-growth-adjusted capex appears in no source page we read, so we do not build it.
- Window of the mean. Default: current year plus two prior (p. 12). p. 13 may mean the three prior years.
- Interest add-back. Default: gross. `interest=False` gives the levered version for a comparison.
