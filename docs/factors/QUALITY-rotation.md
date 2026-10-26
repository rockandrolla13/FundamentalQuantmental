# QUALITY. Up-in-quality and down-in-quality rotation (cheapest high quality, richest low quality)

- **Rank:** none (a strategy layer over F04, F09, F19, F21, F24, F27; not in the ranked list). **Status:** NEW. **Code:** package `hy/quality/` (`score`, `valuation`, `trades`, `gauge`, `phase`); tests `tests/test_quality_*.py`.
- **Sources** (PDF pages unless stated):
  - Morgan Stanley, Sheets et al., "High Yield: Pricing Tomorrow's Deleveraging Today", 18 April 2011. File `MS_Single name screens across fundamentals and valuations (Apr 2011).pdf` (folder `/home/ak/Documents/Quant Credit/Screening Models/MS Credit Stategy Screens/`), pp. 4, 7, 8.
  - Morgan Stanley, "The 10% Club", 25 August 2011. File `MS_Screen for positive FCF, strong liquidity and low cyclicality (Aug 2011).pdf`, pp. 2, 3.
  - Morgan Stanley, "Cyclicality vs. Liquidity", September 2011. File `MS_Cyclicality vs. Liquidity (Sep 2011).pdf`, p. 4.
  - Israel, Palhares, Richardson (2018), card `research/cards/israel-palhares-richardson-2018-common-factors.md`, pp. 8, 9, 27.
  - Greenwood and Hanson (2013), card `research/cards/greenwood-hanson-2013-issuer-quality-bond-returns.md`, manuscript pp. 10, 17, 47, 50, 51.
  - Houweling and van Zundert (2017), card `research/cards/houweling-van-zundert-2017-factor-investing-corporate-bonds.md`, pp. 12, 47.
- **Reader blocks:** F-F2, F-F3 (`research/notes/quant-credit-review/out_F.md`), F-B19 (`out_B.md`). The MS numbers below were checked on the PDF page.
- **Evidence:** none for the rotation itself. The MS notes are screens with no backtest. The academic sources test defensive or low-risk factors and index-level issuer quality, not this pair.

## Claim
At month end t, inside US high yield, a DTS-matched pair long the cheapest high-quality bonds and short the richest low-quality bonds earns a positive excess return over 12 months when `cycle_phase` is late cycle or downturn. The reverse pair earns a positive excess return in repair and recovery. Cheap and rich mean a positive or negative residual of log spread on quality and log duration.

## Definition
1. Quality (`hy.quality.score`). Each component is ranked across the HY universe, or within GICS sector, and mapped to [-0.5, 0.5].
```latex
F_i = \frac{\sum_k w_k\, r_{k,i}}{\sum_k w_k},\quad f_i = \operatorname{rank}(F_i),\quad g_i = \operatorname{rank}(\text{rating ordinal}_i),\quad Q_i = \operatorname{rank}\Big(\frac{w_f f_i + w_r g_i}{w_f + w_r}\Big),\quad gap_i = f_i - g_i
```
Intuition: many independent balance-sheet measures, ranked, so one bad input cannot dominate. The spread never enters `f`.

| Component | Sign | Code reused | Source |
| --- | --- | --- | --- |
| leverage, debt / EBITDA | low good | `leverage` panel, else `annual_ebitda` | methodology 4.3; MS Apr 2011 p. 8 (net leverage column) |
| coverage, EBITDA / interest | high good | `annual_ebitda`, `compustat_annual.xint` | methodology 4.3; MS Apr 2011 p. 8 ("interest coverage greater than 3x") |
| gross profit / assets | high good | F09 `profitability_change` | IPR 2018 p. 8 |
| 5-year profitability change | high good | F09 | F09 spec |
| owner cash flow / debt | high good | F19 `issuer_values` | MS Aug 2011 p. 3 ("FCF positive"); MS Apr 2011 p. 8 ("FCF to debt greater than 3%") |
| refinancing headroom | high good | F21 `issuer_scores` | MS Sep 2011 p. 4 |
| cyclicality, worst YoY EBITDA fall in 10 years | low good | F21 | MS Sep 2011 p. 4; MS Aug 2011 p. 3 |
| size, log total assets | high good | `compustat_annual.at` | Greenwood and Hanson Table 6, p. 50 |
| naive Merton DD | high good | F02 helpers | Greenwood and Hanson p. 10 fn. 6 |

Our choice: weights 1, except size and the profitability change at 0.5 (`WEIGHTS`). Size is the weakest alternate quality measure in Greenwood and Hanson (t -1.71, p. 50). At least 4 components (`MIN_COMPONENTS`). Financials (GICS 40, 60) get no fundamental score. Rating ordinal: IG 3, BB 2, B 1, CCC 0, from F04 `rating_classes` (S&P to February 2017, then the leverage-implied class). Blend weights `w_f = w_r = 0.5` (our choice). The blend needs both parts unless `blend_min_parts=1`. Variants: `kind="fundamental"`, `"rating"`, `"blend"` (default).

2. Valuation (`hy.quality.valuation`). Each month, OLS over non-distressed bonds (spread <= 1,000 bp):
```latex
\log s_i = a_t + b_t Q_i + c_t \log D_i + e_i,\qquad gap_i = s_i - \hat s_i,\qquad conv_i = D_i\, gap_i
```
Intuition: `e > 0` means the bond pays more than its quality and duration justify. Source form: IPR 2018 p. 27 (log OAS on log duration, rating and volatility). Our choice: quality replaces rating. `y_kind="level"` fits the spread in decimals. HQ and LQ: quality quintile 5 and 1 (`hq_def="score"`), rating buckets (`"rating"`, presets `bb_vs_bccc`, `crossover_vs_ccc`, `bb_vs_ccc`), or both (`"both"`). Cheap HQ = HQ with `e > 0`. Rich LQ = LQ with `e < 0`.

3. Expressions (`hy.quality.trades`) and gauge (`hy.quality.gauge`).
```latex
w_i \propto \frac{1}{DTS_i},\ \sum_{long} w_i = 1,\qquad \sum_{short} |w_j|\,DTS_j = \sum_{long} w_i\,DTS_i,\qquad JTD_i = |w_i|\Big(1 - \frac{R}{P_i/100}\Big),\qquad R^Q_t = \frac{\operatorname{med}_{LQ} s}{\operatorname{med}_{HQ} s}
```
- `up_pair`: long cheap HQ, short rich LQ. `down_pair`: long cheap LQ, short rich HQ. Single legs: `long_cheap_hq`, `short_rich_lq`, `long_cheap_lq`, `short_rich_hq`. Pairs may cross buckets: `long_buckets=("BB",)`, `short_buckets=("CCC",)`.
- 5 bonds per leg, one per issuer (our choice). R = 0.3 (F02 `CG_RECOVERY`, Alber PDF p. 24; our choice to reuse it). DTS form: Houweling and van Zundert p. 47.
- Gauge score = own-history percentile of `R^Q` minus 0.5 (F24 rule, at least 3 years). It also carries the F24 BB/BBB and B/BB 1-3y ratios.

4. Phase hook (`hy.quality.phase`). HYPOTHESIS, our choice: late cycle and downturn -> up in quality, repair and recovery -> down in quality, expansion -> none. The user overrides with `mapping`.

## Inputs
| Field | Production table, columns | as_of | available_at rule | Status |
| --- | --- | --- | --- | --- |
| spread, duration, price, years | `bond_panel`: g_spread, mod_dur, price, years, yield, carried | month end | decision_time(date) | have |
| debt, EBITDA | `annual_ebitda`: oibdp, debt | fiscal year end | max(available_at, datadate + 90 days) | have |
| monthly leverage | `leverage`: leverage, ltm_ebitda | month end | as built; at most 92 days old | have |
| sale, cogs, at, xint, che, capx, dd1, dd2, oancf, aqc, intpn, dp, dlc, dltt, revolver_undrawn | `compustat_annual` | fiscal year end | as F09 | need (F09, F19, F21 columns) |
| quarterly cash flow | `compustat_quarterly` (F19 columns) | quarter end | available_at | optional |
| rating | `ratings`: splticrm, datadate | month | available_at; at most 62 days old | have to Feb 2017 |
| sector | `gics` | spell | indfrom, available_at | have |
| DD inputs | `financials`, `equity_monthly` or `equity_daily`, `market_value` | as F02 | as F02 | optional |
| phase | `cycle_phase`: date, cycle_phase, available_at | month | available_at | need |
| gauge cache | `quality_gauge_history` (`gauge.HIST_COLS`) | month | decision_time(date) | optional |

## Build steps
1. Universe: eligible `bond_panel` rows at t with a gvkey. Drop issuers with S&P D or SD.
2. Components per gvkey at decision_time(t). Rank, combine to `f`. Rank the rating to `g`. Blend to `Q`. Compute `gap`.
3. Quintile 1 to 5 from the chosen rank. Rating bucket BBB, BB, B, CCC from F24 `cell_rating`.
4. Fit the residual. Flag cheap HQ, rich HQ, cheap LQ, rich LQ, and rank each list.
5. Pick the expression from `expression=` or from the phase hook. Build DTS-matched legs. Report carry, JTD and convergence (`trades.summary`).
6. Gauge: `R^Q` at t and in each prior month (cache or rebuild), percentile, F24 ratios.

## Code placement
`hy/quality/score.py` `compute(panels, as_of, kind, within)`; `valuation.py` `compute(..., y_kind, hq_def, hq_ratings, lq_ratings, diagnostics)`; `trades.py` `compute(..., expression, mapping, legs, long_buckets, short_buckets)` and `summary(legs)`; `gauge.py` `compute(...)`, `gauge_history`; `phase.py` `compute`, `phase_expression`. Each module has `META`. Reuses F02, F04, F08 (`lever` diagnostic), F09, F16 (`var5` diagnostic), F19, F21, F24, F27.

## Tests
Unit (`tests/test_quality_*.py`, 71 tests): no look-ahead for fundamentals, ratings, bonds, phase and gauge cache; the quality score is unchanged when spreads change; planted cheap HQ (HQC) and rich LQ (LQR) are found by score and by rating bucket; a cheap BB against a rich CCC is paired; the rating-only variant works without fundamentals; DTS match (net DTS = 0); phase mapping and override; missing panels give empty frames.

Evaluation (production machine, proposed): monthly 12-month excess return of `up_pair` over duration-matched Treasuries, net of cost, conditional on phase. Pass if it is positive in at least three of the four cycle windows (2008, 2015, 2020, 2022) and `down_pair` is positive in the repair windows after them. Also: rank IC of `resid` beyond spread within quintile 5 and within quintile 1, and the 24-month downgrade rate by `gap_flag`.

## Risks
- The implied rating after February 2017 reads leverage. The gap then shrinks by construction (`rclass_src` flags it).
- A cheap HQ bond may be cheap for an event the fundamentals miss: LBO (F08 `lever`), litigation, sector stress. Use `diagnostics=True`.
- DTS matching leaves a large short notional on tight LQ bonds (the fixture shows 6x). JTD then favours the pair, but the short carry is negative.
- Overlap with F24 (cell value) and the defensive factor of IPR 2018 (joint t 0.9 beside value, p. 11).

## Open questions
1. Weights of the components and of the blend. Default equal (our choice). The production test can fit them.
2. Phase map for expansion. Default none, because no source gives a direction.
3. F27 conflict. Nicol (short dated HY, p. 3, Fig. 4) finds B tightens against BB in rate sell-offs. The hook reports the F27 state and applies it only with `selloff_override=True`.
4. Source claims against our decisions. MS Apr 2011 p. 8 screens z-spread > 250 bp, YoY deleveraging, FCF / debt > 3%, spread per turn above the 87 bp/x median, coverage > 3x and maturity > 3 years. MS Aug 2011 p. 3 requires a 2008-09 EBITDA fall below half of the fall that forces new funding. We rank continuous measures instead of fixed cut-offs, because fixed cut-offs drift with the cycle (MS Apr 2011 p. 4: median coverage moved from 2.8x to 3.4x).
