# F26. HY index time-series trend

- **Rank:** 26. **Tier:** 5 (HY index timing, candidate to replace S7). **Status:** NEW at index level. The known momentum factors (F04, F15) are cross-sectional. This factor times the whole index.
- **Level:** index. Key `index` = `"US_HY"`. One row per month end.
- **Main source:** J.P. Morgan, Kolanovic and Wei, "Momentum Strategies Across Asset Classes", 15 April 2015. File `/home/ak/Documents/Quant Credit/Work_Quant (1)/JPM_Momentum_Strategies__2015-04-15_1681565 (1).pdf`. Printed page = PDF page. Text and footnote 37 on p. 41. Index profile and rules on p. 120.
- **Variant:** Société Générale, Ravagli, Hippler, Huang, Turc, "FX timing indicators", 1 April 2010. File `/home/ak/Documents/Quant Credit/Work_Quant (1)/SG FX Timing Indicator Strategy (1).pdf`. Summary p. 1. Formulas (1) to (4) p. 4. Parameter table p. 6.
- **Construction alternative:** "Design and analysis of momentum trading strategies". File `/home/ak/Documents/Quant Credit/Design_and_analysis_of_momentum_trading_strategies.pdf`. Eq. 1 p. 4, EMA2 p. 7, path length p. 8, eq. 18 and test setup p. 11. Printed page = PDF page.
- **Reader blocks:** G-F4 (`research/notes/quant-credit-review/out_G.md`), A1-F11 (`out_A1.md`).

## Claim
When the 5-day average of the US HY index level is at or above its 50-day average, the HY index excess return over the next month is positive on average. The step position x_t then earns a positive return net of cost. The evidence is from a European CDS index only (iTraxx Crossover). No cash bond or US HY test exists in the folder.

## Definition
```latex
\mathrm{STA}_t=\tfrac15\sum_{i=0}^{4}L_{t-i},\quad
\mathrm{LTA}_t=\tfrac1{50}\sum_{i=0}^{49}L_{t-i},\quad
x_t=\mathrm{clip}\bigl(x_{t-1}+0.25\,d_t,\,-1,\,1\bigr),\quad
d_t=\begin{cases}+1&\mathrm{STA}_t\ge\mathrm{LTA}_t\\-1&\text{else}\end{cases}
```
Intuition: credit trends, and a step of 0.25 per day lets the book react fast but limits the cost of a false signal.

What the source says (JPM p. 41 footnote 37, p. 120 rules 1 to 5):
- 5-day and 50-day moving averages on the Underlying Index: STA and LTA.
- On each index business day: if STA >= LTA, raise the long exposure (or cut the short) by 0.25x, cap 1x long. If STA < LTA, raise the short exposure by 0.25x, cap 1x short.
- Execution at the closing level of the Underlying Index. Turnover is at most 25% of notional per day (p. 41).
- The source does not say whether the level is a spread or a price. It does not give the start exposure.

What we decide:
- L_t rises when credit gains. Our choice, because "long exposure" on STA >= LTA must follow the trend. With `hy_index_return`: L_t = prod(1 + r) of the daily excess return. Else L_t = −spread_t. So tightening = long. A tie STA = LTA goes long, as the source says.
- Start x = 0 on the first day with an LTA (our choice). The rule runs over all history available at the decision time. After eight same-sign days the start no longer matters.
- Score = x on the last index business day with `available_at` <= `decision_time(as_of)`. Values −1, −0.75, ..., +1.

Variant columns (not the score):
- **SG slope and curvature** (p. 4, eqs. 1 to 4): A_t = mean of L_{t−M..t} (M + 1 points), S_t = A_t − A_{t−1}, D_t = mean of S_{t−N..t}, C_t = D_t − D_{t−1}. Long if S > 0 and C > 0, short if both < 0, else flat (p. 4). M = 33, N = 4: the best EUR/USD pair (p. 6). Our choice: an FX in-sample optimum, no credit fit. The printed closed form of eq. 4 has a stray sum over i. We compute C as the difference of D, which eq. 4 defines in words.
- **EMA2 on risk-adjusted changes** (pp. 4, 7, 11): U_n = ΔL_n / σ̂_{n−1} (eq. 1). φ_n = (α + β) φ_{n−1} − αβ φ_{n−2} + U_n, the recursion of A(z) = 1/((1 − αz⁻¹)(1 − βz⁻¹)) (p. 7). α = 1 − 1/20, β = 1 − 1/40 (N = 20, 40, p. 11). σ̂² = 20-day EMA of squared changes (p. 11). Column `ema2_signal` = φ_n / sqrt(R0), R0 = (1 + αβ) / ((1 − αβ)(1 − α²)(1 − β²)) (eq. 18 at M = 1), so it has unit variance when U is white noise. `ema2_position` = its sign. ΔL = r for the return series, −Δspread for the spread series (absolute changes, p. 4).

## Inputs
| Field | Production table and column | as_of | available_at rule | Have |
|---|---|---|---|---|
| Index spread | `hy_index` `spread` (decimal), `date` | `date` | `date` + 1 day (wiring 4.5) | have |
| Index excess return | new optional panel `hy_index_return`: `date`, `excess_return` (daily index return over duration-matched Treasuries, decimal), `available_at`, optional `name` | `date` | when the close is public, at least `date` + 1 day | need |

`hy_index` must have daily rows. Wiring 4.5 asks for monthly rows at least. Monthly rows give status `not_daily` and no score. `distress` is not used.

## Build steps
1. Keep rows with `available_at` <= `decision_time(as_of)`. Keep the last vintage per `date`. Drop NaN levels.
2. Pick the series: `hy_index_return` if present, else `hy_index`. Build L_t and ΔL_t.
3. Check: at least 50 rows, median gap of the last 50 dates <= 5 calendar days, last date >= as_of − 7 days. Else NaN score with status `too_few_obs`, `not_daily` or `stale`.
4. STA, LTA, d_t, then the x_t path. Score = last x.
5. SG S, C and position. EMA2 signal after 120 changes (our choice: three times the slow period, β¹²⁰ ≈ 0.05).

## Code placement
- `hy/factors/f26_index_trend.py`. `compute(panels, as_of, short=5, long=50, step=0.25, cap=1.0, sg_m=33, sg_n=4, ema_fast=20, ema_slow=40, vol_n=20)`.
- Output columns: `date`, `index`, `score`, `available_at`, `signal_date`, `level_source`, `n_obs`, `sta`, `lta`, `jpm_signal`, `sg_slope`, `sg_curvature`, `sg_position`, `ema2_signal`, `ema2_position`, `status`.
- Helpers: `index_level`, `moving_average`, `crossover_signal`, `step_exposure`, `sg_slope_curvature`, `sg_position`, `risk_adjusted_changes`, `ema2_filter`, `ema2_unit_sd`.
- Reuses `hy.backtest.decision_time`. Docstrings cite Section 8 (S7 replacement) and Section 9.2 (macro overlay).

## Tests
- No look-ahead: rows after as_of and rows with `available_at` after the decision time change nothing.
- Sign: a steady tightening gives x = +1. A steady widening gives x = −1. The return series gives the same sign as the spread series.
- Path: a hand sequence of d_t gives the hand x_t path with the cap.
- Edges: no panel gives an empty frame. Monthly rows give `not_daily`. Fewer than 50 rows give `too_few_obs`.
- Helpers: SG S equals (f_t − f_{t−M−1})/(M + 1) (eq. 2). EMA2 weights match a_j = (α^{j+1} − β^{j+1})/(α − β) (p. 7). R0 matches the sum of a_j².
- Evaluation (production machine): daily x_t times the next-day index excess return, net of a cost per 0.25 step. Reader G-F4 proposes 0.5 bp per step as a CDX proxy, not a source number. Pass: Sharpe > 0.3 net, 2000 to 2024, and a smaller drawdown than the index in 2008 and 2020 (reader G-F4). Contract test: the mean net monthly return of x at month end over the next month is positive in at least three of the four `CYCLE_WINDOWS`.

## Risks
- Evidence is CDS index only. JCREMOXO on iTraxx Crossover 5Y, live since Jan 2012: 6.2% a year, vol 6.4%, Sharpe 0.97, max drawdown −7.4%, t-stat 1.7, to Mar 2015 (p. 120 table). The p. 41 text rounds Sharpe to 1.0.
- Source conflict on the GFC (Aug 2007 to Mar 2009). The p. 41 text gives +6.2% and Sharpe 1.0. The p. 120 table gives 1.6%, Sharpe 0.18, max drawdown −9.8%, t-stat 0.2. The text repeats the live numbers, so we use the table. Reader G-F4 copied the text. The index itself lost 8.8% a year, Sharpe −0.8 (p. 41).
- t-stats are below 2 except the 8-year column (2.2, p. 120). The record is short.
- Cash HY cannot step daily at low cost. The rule suits a beta overlay with CDX HY or ETFs, not bond selection.
- The spread series ignores carry. A flat spread with positive carry gives no signal.
- The TRACE benchmark median G-spread changes when the universe changes. Jumps can flip STA against LTA.

## Open questions
- Level: spread or return index. Our choice: return index when given. The CDS rule likely used the excess return index (it is tradable).
- Step frequency. Source: daily. Reader G-F4 suggests weekly for cash HY. Default daily. A weekly run is a production test.
- SG M, N for credit. Default the FX values 33 and 4 (p. 6). The source finds M more sensitive than N (p. 5).
- EMA2 nonlinearity. The source warns that the binary sign is not optimal (p. 4). Default: unit-variance linear signal plus its sign.
