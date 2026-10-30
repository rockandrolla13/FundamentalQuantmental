# F01b. Short-horizon IPCA entry timer (5 to 10 trading days)

## 1. Header
- Rank 1b. A variant of F01 (`docs/factors/F01-ipca.md`). Tier: design only, no source tests this horizon.
- Status: NEW variant. Role: an entry and exit timer for the bonds that the monthly F01 book selects. It is not a standalone factor.
- Source: Kelly, Palhares, Pruitt (2021), SSRN 3720789 (KPP), for the estimator only. KPP test 1-month returns only (pp. 13–16). Every short-horizon choice on this page is "Our choice".
- Reuses: F01 (estimator), F05 (customer flow), F13 (liquidity), F14 (abnormal volume), F15 (daily excess returns), F11 (implied volatility), F12 (ETF flow).

## 2. Claim
At the close of trading day d, the IPCA expected return of a US high yield bond ranks its DtS-scaled excess return over trading days d+2 to d+1+H, H in {5, 10}, with a positive sign. Within the bonds that the monthly F01 book adds, entry on the timer's signal gets a better average price than entry on the first trading day of the month, after costs.

The second sentence is the claim that matters. The timer passes or fails on the entry-price saving, not on its stand-alone IC.

## 3. Definition
```latex
r^{(H)}_{i,d} = \frac{\sum_{u=d+2}^{d+1+H} \tilde r_{i,u}}{\max(DtS_{i,d},\, 0.25)}, \qquad
\tilde r_{i,u} = s_{i,u-1}\,\Delta t_u - D_{i,d}\,(s_{i,u} - s_{i,u-1}), \qquad
\hat E_d[r^{(H)}_{i,d}] = z_{i,d}'\,\hat\Gamma_d\,\hat\lambda_d
```
Intuition: the same IPCA model as F01, but the target is the next 5 or 10 days and the instruments include fast inputs that move inside a week.

Our choices:
- **Skip one day.** The target starts at d+2, not d+1. The close-to-close move from d to d+1 holds most of the bid-ask bounce: a bond that last traded at the bid tends to print the ask next. Skipping one day stops the bounce from posing as a reversal signal. It also matches execution: a trader acts on day d+1.
- **Daily return.** `r̃` is carry minus duration times the spread change, from `hy.factors.f15_pca_ou_reversal.daily_spread_returns`. The day's spread is the par-weighted mean of the day's trades (`bond_daily.g_spread`). A day with no trade carries the last spread for at most 10 days (F15 `MAX_FFILL_DAYS`).
- **DtS floor.** 0.25, as in F01 (KPP p. 14). D and DtS are fixed at day d.
- **K = 3.** Weekly returns are noisier than monthly returns, so fewer factors. Report K = 1 to 5. Never pick K on the test years.
- **Fit dates.** Fit on non-overlapping dates only: one date per H trading days, the last trading day of each week for H = 5, and every second week for H = 10. Overlapping windows reuse the same days and inflate the fit.
- **Expanding window.** Refit once a week, after the Friday close. Between refits, hold Γ̂ and λ̂ fixed and update z daily. A pair enters the fit only when its whole target window ends before the decision time.
- **Warm-up.** 104 fit dates for H = 5 (two years of weeks), 52 for H = 10.
- **λ̂.** The mean of the in-sample factors of the current fit, as in F01.

### Instruments z (rank-scaled to [−0.5, 0.5] each day, missing = 0, plus a constant)
Anchors (slow, copied from the last F01 month end, `hy.factors.f01_ipca.characteristics`):

| # | Name | Definition |
|---|---|---|
| A1 | `spread` | `g_spread` at d |
| A2 | `duration` | `mod_dur` at d |
| A3 | `rating` | 1 to 22, as F01 item 22 |
| A4 | `bond_vol` | F01 item 27 |
| A5 | `mom_bond` | F01 item 12, 6-2 months |
| A6 | `price_premium` | F01 item 31 |

Fast (daily, new):

| # | Name | Definition | Panel |
|---|---|---|---|
| S1 | `rev_1w` | DtS-scaled excess return over days d−4 to d | `bond_daily` |
| S2 | `rev_1m` | DtS-scaled excess return over days d−21 to d−5 | `bond_daily` |
| S3 | `eq_1w` | stock return over days d−4 to d | `equity_daily` |
| S4 | `flow_10d` | F05 `P^(10)`: net customer sales over 10 days per unit of normal volume | `trace_daily_flow` |
| S5 | `abn_vol_5d` | log of 5-day par volume minus the log mean over days d−40 to d−6 (F14 windows) | `bond_daily` |
| S6 | `illiq_20d` | Amihud over 20 days: mean of abs(daily return) / par volume | `bond_daily` |
| S7 | `d_iv_1w` | change in 365-day 50-delta implied volatility over 5 days (F11 inputs) | `option_iv` |
| S8 | `stale_days` | trading days since the last trade, capped at 10 | `bond_daily` |

S1 and S2 carry the reversal. S3 carries the equity lead. S4 to S6 carry the liquidity and flow pressure. S8 lets Γ discount stale prices. The fit learns every sign. The page assumes none.

### Timing rule (the output the trader uses)
For each bond on the F01 change list (a buy or a sell that the monthly rebalance asks for):
1. `edge = Ê_d × max(DtS, 0.25)`, the forecast excess return over H days in decimal.
2. `hurdle = cost_rt / 2`, the one-way cost from `hy.backtest.round_trip_cost`.
3. Buy order: `act = 1` when `edge > −hurdle`, so the timer does not expect the next H days to cost more than the trade itself. Else `act = 0` (wait).
4. Sell order: the mirror. `act = 1` when `edge < hurdle`.
5. **Patience cap.** Act on day 10 of the month whatever the signal says. The timer may delay a trade. It may never cancel one. This keeps the monthly book intact and limits the cost of a wrong timer to 10 days of drift.

All thresholds are our choice. The production test (section 7) settles them.

## 4. Inputs
`as_of` is trading day d. Decision time = `hy.backtest.decision_time(d)` = d + 1 day. That function adds one calendar day to any date, so it serves daily use unchanged.

| Field | Table and column | `available_at` rule | Status |
|---|---|---|---|
| Daily spread, volume, trades | `bond_daily`: `cusip`, `date`, `g_spread`, `par_volume`, `n_trades` | trade day + 1 day | need (PRODUCTION_DATA §3) |
| Duration, price, bid-ask | `bond_panel`: `mod_dur`, `price`, `bid_ask_pts` (last month end) | as F01 | have |
| Anchors A1 to A6 | as F01 | as F01 | have (A3 if `ratings` exported) |
| Daily stock return | `equity_daily`: `gvkey`, `date`, `ret` | trade day + 1 day | need (PRODUCTION_DATA §2) |
| Customer flow | `trace_daily_flow` (F05) | trade day + dissemination lag + load lag | need, and see the box |
| Implied volatility | `option_iv` (F11) | date + 1 day | need, optional |
| F01 change list | output of `hy.factors.f01_ipca.compute` at the last month end, plus the current book | decision time of that month end | have |

**Live TRACE feed.** The WRDS Enhanced TRACE load lag is about 5 weeks (PRODUCTION_DATA §3). A 5-day signal cannot wait 5 weeks. So:
1. For the historical fit, use WRDS with `load_lag = 0` and accept that the history assumes live data.
2. For live use, feed S4 from the FINRA real-time TRACE feed. Its side and contra-party fields are coarser: without them, S4 is NaN and takes rank 0.
3. Report the IC with and without S4. If S4 adds nothing, drop it and the live feed with it.

## 5. Build steps
1. Build the daily excess return grid from `bond_daily` with `daily_spread_returns`, using `mod_dur` at the last month end.
2. For each fit date d in the history, build z_d: the anchors from the last F01 month end at or before d, and S1 to S8 from rows with `available_at ≤ d + 1 day`.
3. Rank-scale z_d per date with `hy.factors.f01_ipca.rank_scale`. Append the constant.
4. Build the target r^(H) for each fit date. Keep a pair only when day d+1+H + 1 day ≤ the decision time of the refit date.
5. Screens: the F01 screens (eligible, spread 0.005 to 0.20, `mod_dur ≥ 0.25`), plus at least one trade in days d−4 to d. A bond with no trade that week gets no score.
6. Fit with `hy.factors.f01_ipca.fit_ipca` on the non-overlapping pairs, K = 3. Store Γ̂ and λ̂ until the next weekly refit.
7. Each day d: compute Ê_d with `expected_return`, then `edge`, `hurdle` and `act` for the bonds on the change list. Every bond also gets `score` = Ê_d standardised by date.
8. Write one row per bond per day with `date = d` and `available_at = decision_time(d)`.

## 6. Code placement
- Module `hy/factors/f01b_ipca_short.py`. Tests `tests/test_factor_f01b.py`. Not in `REGISTRY`, because the registry holds monthly factors keyed by rank. Add a second map, `hy.factors.TIMERS = {"1b": "hy.factors.f01b_ipca_short"}`.
- `META`: as the contract, but `horizon_days` (5 or 10) in place of `horizon_months`, `"freq": "daily"`, `"role": "timer"`, `"parent": 1`.
- Functions:
  - `forward_return(ret: pd.DataFrame, dts: pd.Series, d: pd.Timestamp, h: int, skip: int = 1) -> pd.Series`
  - `fast_characteristics(panels, d: pd.Timestamp, dt: pd.Timestamp) -> pd.DataFrame` (S1 to S8)
  - `fit_dates(calendar: pd.DatetimeIndex, h: int) -> pd.DatetimeIndex` (non-overlapping)
  - `fit_timer(panels, refit_date: pd.Timestamp, h: int, K: int) -> IPCAFit`
  - `timing_rule(edge: pd.Series, hurdle: pd.Series, side: pd.Series, day_of_month: int, cap: int = 10) -> pd.Series`
  - `compute(panels, as_of, h=5, K=3, fit=None, change_list=None, **params) -> pd.DataFrame`. With `fit` given, skip the refit. Production passes the weekly fit to each day, because one refit costs much more than one forecast.
- Output columns: `date`, `cusip`, `score`, `available_at`, `gvkey`, `ipca_er_h`, `edge`, `hurdle`, `side`, `act`, `days_waited`, `n_fast` (fast inputs present), `stale_days`.
- Reuse, do not copy:
  - `hy.factors.f01_ipca`: `rank_scale`, `fit_ipca`, `factor_step`, `normalise`, `expected_return`, `dts_scaled_return`, `characteristics`, `screen`.
  - `hy.factors.f15_pca_ou_reversal.daily_spread_returns`.
  - `hy.factors.f05_flow_pressure_reversal.bond_pressure` (S4).
  - `hy.factors.f14_abnormal_volume.abnormal_log_volume` (S5).
  - `hy.factors.f11_delta_implied_vol` loaders (S7).
  - `hy.backtest`: `decision_time`, `eligible`, `round_trip_cost`. `hy.signals.standardise`.

## 7. Tests
Unit tests, on synthetic data:
- No look-ahead: change every `bond_daily` row after d. The score at d does not change. A training pair whose target window ends after the decision time is absent from the fit.
- Skip day: plant a pure bid-ask bounce (prices alternate bid and ask, no true move). The fitted coefficient on `rev_1w` is near zero with the skip, and clearly negative without it.
- Sign: plant a true 1-week reversal in the target window d+2 onward. The rank IC of the score against the planted expected return is above 0.8.
- Fit dates: no two fit dates are fewer than H trading days apart.
- Timing rule: a buy with `edge` below `−hurdle` waits. On day 10 it acts. A sell mirrors.
- Missing panels: no `bond_daily` gives an empty frame. No `trace_daily_flow` or `option_iv` sets S4 or S7 to rank 0 and still scores.
- Stale bond: no trade in days d−4 to d gives no score.

Evaluation on the production machine, H = 5 and H = 10:
1. **Entry saving (the pass test).** For every bond the monthly F01 rebalance trades, compare the execution price on the `act` day with the price on trading day 1 of the month. Measure the saving in DtS-scaled return, net of the extra cost of waiting. Pass: mean saving above 0 in at least 3 of the 4 cycles 2008, 2015, 2020, 2022. Use a HAC t-statistic above 2 over the full sample.
2. **Stand-alone IC (diagnostic).** Weekly rank IC of `score` against r^(H) on non-overlapping dates, beyond `rev_1w` alone. If the full model adds nothing over plain reversal, use plain reversal: it is simpler.
3. **Patience cap.** Re-run test 1 with the cap at 5 and 15 days. Pick the cap on 2004 to 2014 only.

Note: `trace_daily_flow` has side data from about 2012. Before 2012, S4 is rank 0. The 2008 cycle tests the model without flow.

## 8. Risks
- **Cost.** A stand-alone weekly book would trade about four times as often as F01. F01 already reaches a negative Sharpe at 40 bp one way (KPP Table IA.IV, p. 59). The timer role avoids this, because it adds no trades.
- **Bid-ask bounce.** The skip day removes most of it. Trades of a different size sit at different prices, and the par-weighted mean only partly corrects for this. Test with customer buys only as a check.
- **Sparse trades.** Many HY bonds trade a few times a week. The screen drops bonds with no trade in the week, so the timer serves the liquid part of the book. Illiquid bonds enter on day 1.
- **Overlap.** S1 and S2 overlap with F15 (PCA residual reversal). S4 overlaps with F05. Run the entry-saving test with F15 alone as the timer too. Keep F01b only if it beats F15.
- **Data cost.** The live TRACE feed and daily equity add cost. The two-step test in section 4 decides whether S4 earns its feed.
- **No evidence.** No source tests IPCA at a 5 to 10 day horizon in HY. The whole page is a hypothesis.

## 9. Open questions
1. H. Default: 5. A trader acts within a week, and a 10-day forecast covers the patience cap. Test both.
2. Anchors. Default: six anchors. Option: all 16 F01 instruments. More slow instruments add little in a week and cost fit stability.
3. Fit frequency. Default: weekly refit. Daily refits cost much more and change Γ̂ little week to week.
4. Exit timing. Default: the same rule for sells. Option: exits act at once, because a forced sale often follows bad news. Test both.
5. One model or two. Default: one fit across HY. Option: separate fits for BB and for B and below, as the up-in-quality work does (`docs/factors/QUALITY-rotation.md`). Test only if the full-HY fit passes.
