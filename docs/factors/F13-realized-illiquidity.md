# F13. Realized bond illiquidity (Amihud), level and shock

## 1. Header
- **Rank:** 13 of 30, Tier 3 (tested outside credit, buildable now).
- **Status:** NEW. No bond liquidity factor exists in Section 8. It also serves as a cost gate for other factors, and it feeds the liquidity block of Section 7.2.
- **Sources (all under `/home/ak/Documents/Quant Credit/`):**
  - Lacava, Ranaldo and Santucci de Magistris, "Realized Illiquidity" (3 January 2023), `Work_Quant (1)/Realized Illiquidity.pdf`, PDF pp. 7, 11 to 12, 21 to 24, 41.
  - Deutsche Bank, "Designing a Liquidity based Toolkit" (22 November 2016), `Work_Quant (1)/Designing a Liquidity based Toolkit (1).pdf`, PDF pp. 6 to 8, 12 to 14, 20 to 21.
- **Reader blocks:** F-F7, F-F8.

## 2. Claim
Among US high yield bonds, a bond with a higher realized Amihud illiquidity than its rating and maturity peers earns a higher excess return over the next month. The sign is positive.

## 3. Definition
**What the source says.** Realized Amihud is realized absolute variation over dollar volume (eq. 5, p. 7). The classic daily Amihud is the case I = 1 (p. 7). Sample at 5 to 10 minutes, because the highest frequencies carry a large microstructure bias (p. 12, Table 2 p. 13). The paper fits a MEM-AHAR model on daily SPY data: HAR terms of 1, 5 and 22 days and a leverage dummy (eq. 14, p. 21). The fitted mean is expected illiquidity. The residual is unexpected illiquidity (p. 23).

```latex
A_{b,W}=\frac{\sum_{k\in W}\lvert\log p_k-\log p_{k-1}\rvert}{\sum_{k\in W}\nu_k},\qquad L_{b,t}=\log\!\big(10^6A_{b,t}\big),\qquad A^{M}_{b,t}=\frac{\lvert\log(P_t/P_{t-1})\rvert}{V_tP_t/100}
```

Intuition: a bond whose price moves far per dollar traded is costly to exit. Holders ask a premium for that cost.
- **Prices (our choice).** p_k is the last TRACE trade price in each 5-minute interval (previous tick, p. 12). Trades with par under $100,000 drop out (reader F-F7 proposal). Returns run between consecutive sampled prices inside the window, across days too. ν_k = price / 100 × par.
- **Window and sparse bonds (our choice).** The window is calendar month t. A bond needs 5 sampled returns (`measure` "trace"). With fewer, the window grows to months t−2 to t ("trace_3m"). With fewer still, or without TRACE trades, the bond takes A^M from `bond_panel` ("panel", flagged). A^M is eq. 5 with one monthly return, the coarse measure the source calls three times less efficient than its high-low twin (p. 11).
- **Shock (our choice, after eq. 37, p. 41).** A pooled log-linear HAR per measure family, fit by OLS on the 36 target months before t:

```latex
L_{b,m}=\omega+a_1L_{b,m-1}+a_3\bar L^{(3)}_{b,m-1}+a_{12}\bar L^{(12)}_{b,m-1}+\varepsilon_{b,m},\qquad \text{shock}_{b,t}=L_{b,t}-\hat L_{b,t}
```

The monthly terms 1, 3 and 12 months replace the daily 1, 5 and 22 days. The 3-month mean needs 2 values, the 12-month mean 6. The fit needs 200 bond-months. Otherwise the expectation is the bond's own 12-month mean with 3 values (`shock_source` "own"). We drop the leverage dummy γ. Its estimate is small (0.037 on the realized Amihud, Table 6, p. 22).
- **Liquidity change.** `illiq_change` = L_t − L_{t−3} (reader F-F8 proposal of 63 days). Positive means worse liquidity.
- **Score.** Winsorise L at 1% and 99% per family. z inside the cell: family × rating class × maturity bucket (`hy.peers.maturity_bucket`), then family × class, then family. A cell needs 10 bonds. The shock z is cross-sectional per family. `score` = level z + SHOCK_WEIGHT × shock z, with SHOCK_WEIGHT = 0 until the evaluation settles the shock sign (Section 9).
- **Score sign: what the sources support.**
  - Level, positive. Lacava gives the rationale only: higher expected illiquidity raises the ex-ante return (p. 23). Table 7 Panel b (p. 24) gives expected illiquidity +3.63 at the monthly horizon, 10% level, ×100. That is a time series on SPY, not a cross-section. DB finds an illiquidity premium in the level of European equities (p. 14), but the level lost 11% in 2008 (p. 21, note 43).
  - Shock, current return negative. Unexpected illiquidity has −10.28 daily and −37.79 monthly, both 1% level, ×100 (Table 7 Panel b, p. 24). The R² of 0.16 belongs to the joint model of both components.
  - Shock, later return. Lacava argues a shock raises expected illiquidity and so the later return (p. 23), but does not test it. DB finds the opposite at weekly horizons: long improving liquidity, a continuation signal with fast decay (p. 14). It earned +15% in 2008 (p. 21).
  - Our choice: `shock_z` keeps the positive sign (positive shock, later long), after Lacava. The score holds the level only.
- **Cost gate.** `illiq` = 10⁶ A. `impact_bp` = A × $1mm × 10⁴, the price impact of a $1mm trade. `illiq_pct` = percentile of A inside its family. `cost_gate_pass` = `illiq_pct` ≤ 0.80 (our choice). `cost_rt` = `hy.backtest.round_trip_cost` (bid-ask over price).

## 4. Inputs
| Field | Production table and column | `as_of` | `available_at` lag rule | Status |
|---|---|---|---|---|
| Trade price, par, time | new panel `trace_trades`: `cusip`, `trade_time`, `price`, `par`, `available_at` | trade time | trade day + `DISSEMINATION_LAG` (+ WRDS load lag live) | need (export with `trd_exctn_tm`) |
| Monthly price, volume, trades | `bond_panel.price`, `par_volume`, `n_trades`, `carried` | month end | panel `available_at` | have |
| Bid-ask | `bond_panel.bid_ask_pts` | month end | panel `available_at` | have |
| Years, eligibility fields | `bond_panel.years`, `yield`, `g_spread`, `mod_dur` | month end | panel `available_at` | have |
| Rating class | `ratings.splticrm`, `leverage.leverage`, `ltm_ebitda` | `datadate` | panel `available_at` | have (optional) |

`trace_daily_flow` (F05) has no prices, so it cannot carry this measure. Only `bond_panel` is required.

## 5. Build steps
1. Export cleaned TRACE trades with execution time. `trades_from_trace` builds `trace_trades`.
2. Filter every panel to `available_at` ≤ `decision_time(as_of)`. Sample trade prices on the 5-minute grid.
3. For each of the 49 month ends t−48 to t: TRACE measure per bond, with the 3-month extension.
4. For the same months: the panel measure A^M per bond.
5. Per family: wide L by month and bond, pooled HAR fit, shock at t, change against t−3.
6. Keep `eligible` rows of `bond_panel` at t. Each bond takes its TRACE measure, else the panel measure. A raw D or SD rating gets no score.
7. Cells, winsorised level z, shock z, score.
8. Cost gate columns. Write one row per bond, with `measure` "no_measure" where no measure exists.

## 6. Code placement
- **Module:** `hy/factors/f13_realized_illiquidity.py`. `compute(panels, as_of, sample="5min", min_returns=5, extend_months=3, hist_months=36, min_fit=200, min_cell=10, shock_weight=0.0, gate_pct=0.80)`.
- **Helpers:** `trades_from_trace`, `sample_prices`, `realized_amihud`, `trace_measure`, `panel_measure`, `har_terms`, `fit_har`, `illiquidity_shock`, `peer_z`, `cost_gate`.
- **Section to cite:** Section 8 (new signal). Section 7.2 liquidity block. Section 9.3 exit cost.
- **Output columns:** `date`, `cusip`, `score`, `available_at`, `gvkey`, `measure`, `illiq`, `log_illiq`, `n_returns`, `dollar_volume`, `expected`, `shock`, `shock_source`, `illiq_change`, `level_z`, `shock_z`, `rclass`, `cell`, `illiq_pct`, `impact_bp`, `cost_rt`, `cost_gate_pass`.
- **Reuse:** `hy.backtest.decision_time`, `eligible`, `round_trip_cost`. `hy.peers.maturity_bucket`. `hy.factors.f04_bond_momentum.rating_classes`, `DEFAULT_SYMBOLS`. `hy.factors.f05_flow_pressure_reversal.winsorise`. `hy.sources.trace_bonds.parse_volume`, `MIN_PAR`, `DISSEMINATION_LAG`.

## 7. Tests
- **Unit (`tests/test_factor_f13.py`).** Contract. No look-ahead: July trades, a June trade loaded in July, and July panel rows change nothing. Sign: the bond with the widest price moves per dollar ranks top. Shock: a bond whose moves triple in month t gets a positive shock equal to the hand value, and flat bonds get zero. Sparse: 2 returns in June gives "trace_3m", no trades gives "panel". Missing `trace_trades` gives the panel measure for all bonds. Missing `bond_panel` gives an empty frame. Defaulted issuer has no score. Hand checks of every helper.
- **Evaluation (production machine).** Horizon 1 month, also 3. Target: excess return over duration-matched Treasuries. Pass 1: monthly rank IC of `level_z` after costs, net of the G-spread (`hy.signals.neutralise`), positive in at least 3 of the 4 cycles (2008, 2015, 2020, 2022), HAC t > 2. Report the 2008 drawdown. Pass 2: rank IC of `shock_z` at 1 and 3 months. A positive IC with t > 2 sets SHOCK_WEIGHT = 1. A negative IC with t < −2 confirms DB continuation and sets SHOCK_WEIGHT = −1. Otherwise it stays 0. Pass 3: the score must still rank after the cost gate removes the top 20%.

## 8. Risks
- **No bond evidence.** Lacava tests SPY from January 2006 to June 2018 (p. 22). DB tests European equities. Neither tests bonds.
- **Intraday price impact failed once.** DB found no illiquidity premium from a 5-minute high-low over volume measure (p. 12). The best variant had an IR of 0.1 (p. 12, note 19).
- **Bid-ask bounce.** Dealer buy and dealer sell prices alternate, so RPV partly measures the spread. The 5-minute grid and the par floor cut it only in part.
- **Crisis.** The equity level strategy lost 11% in 2008 (DB p. 21). The premium leg is long the bonds that are hardest to sell in a crisis.
- **Costs.** The long leg holds the costly bonds by build. The after-cost test decides. The cost gate and the premium pull in opposite directions.
- **Overlap.** The level may load on issue size, age and rating. The source gives no correlation with these. The reader target for the change signal is a correlation below 0.3 with the level (F-F8).

## 9. Open questions
1. **Shock sign.** Lacava implies a later rise, DB a weekly continuation. Default: weight 0, column kept, Pass 2 decides.
2. **Window.** The reader proposes a rolling 21 days. Default: the calendar month, so the TRACE and panel measures share one unit period.
3. **MEM against log-linear OLS.** Lacava prefers the Gamma MEM on daily data (p. 21). Monthly bond data have gaps. Default: pooled log-linear OLS (eq. 37, p. 41).
4. **High-low Amihud.** Lacava's high-low form (p. 11) needs daily high and low prices. No production panel has them. Not built.
5. **Mixed families.** TRACE and panel measures have different scales. Default: separate z per family, flagged by `measure`.
