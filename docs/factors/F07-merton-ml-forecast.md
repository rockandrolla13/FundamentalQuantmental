# F07. Merton-restricted machine-learning bond forecast

- **Rank:** 7. **Tier:** 1 (tested in credit, buildable now). **Status:** NEW forecast structure. It is related to EMC, but it multiplies a forecast stock return by a firm hedge ratio. EMC uses the past stock return.
- **Source:** Bali, Goyal, Huang, Jiang and Wen (2022), "Predicting Corporate Bond Returns: Merton Meets Machine Learning", Swiss Finance Institute Research Paper 20-110. File `/home/ak/Documents/Quant Credit/Missing Papers/bali-2022-bond-ml.pdf`. Pages below are printed pages. PDF page = printed page + 2.
- **Reader blocks:** H-F7 (forecast), H-F8 (risk features) in `research/notes/quant-credit-review/out_H.md`. Every number below was checked on the source page.
- **Correction to H-F7:** the gain of the restricted forecast over bond-only (Table 7, p. 46) is 0.06% to 0.24% a month for the nine ML models, t 1.93 to 2.81. PLS gives 0.06 (t 1.93), RF 0.07 (t 2.04). The reader block gives 0.13 to 0.24. The HY hedge-ratio MSE claim is on p. 25, not p. 23.

## Claim
For US HY issuers with listed equity, the firm forecast ĥ·ψ1(XS) + ψ2(XB) predicts the next 1-month bond excess return over duration-matched Treasuries. The rank IC beyond spread is positive after cost. Its top-minus-bottom decile spread beats the bond-only forecast f1(XB) on the same panel.

## Definition
```latex
E_t[R^B_{i,t+1}] = \hat h_{i,t}\,E_t[R^S_{i,t+1}] + E_t[R^B_{i,t+1} - \hat h_{i,t} R^S_{i,t+1}]
                 = \hat h_{i,t}\,\psi_1(X^S_{i,t}) + \psi_2(X^B_{i,t})                       \quad (11),(21)
R^B_{i,s} = \alpha_i + h_{i,t} R^S_{i,s} + e^B_{i,s}, \quad s = t-35,\dots,t                 \quad (19)
```
Intuition: a bond is riskless debt minus a put on the firm. The put part moves with the stock, so predict it with stock characteristics. Predict the rest with bond characteristics.

What the source says:
- Eq. (10)–(11), p. 8: RBmRS = RB − h·RS. Its expectation is α, the bond-only part. Eq. (8) comes from the structural link dD/D − h dE/E = α dt (eq. 4, p. 7).
- Eq. (19), p. 21: ĥ is the OLS slope of firm excess bond return on firm excess stock return over the 36 months t−35 to t (Choi and Kim 2018). The structural hedge ratio is h = (∂D/∂V)/(∂E/∂V) × E/D (eq. 3, p. 7).
- Eq. (20)–(21), p. 21: ψ1 fits RS_{t+1} on 94 stock characteristics (Green, Hand and Zhang 2017). ψ2 fits RBmRS_{t+1} on 43 bond characteristics (Appendix B, pp. 29–35).
- Learners: OLS, PCA, PLS, LASSO, Ridge, ENet, RF, FFN, LSTM, and the mean of the eight ML forecasts (p. 9). Split: 3 years train, 2 years validation, rest test, July 2002 to December 2017 (p. 10).
- Missing characteristics take the cross-sectional median of the month (fn. 7, p. 13).
- Firm return and characteristics: value-weighted by amount outstanding. Equal weights give "qualitatively similar results" (fn. 11, p. 16).

Our choices:
- Bond return: excess over the duration-matched Treasury, `realised_excess_return(beta=0)`. The source uses the T-bill. Its maturity-matched check gives bond-only spreads of 0.31% to 0.73% (p. 20, Table OA3).
- Firm return and features: equal weight across the issuer's eligible bonds. We have no amount outstanding.
- ĥ needs at least 24 of the 36 months. An issuer without ĥ or without stock features gets ĥ = 0, so its label is RB and its score is ψ2 (`has_equity` False).
- Features: rank each one per month to [−1, 1]. A missing value becomes 0, the median rank (fn. 7, p. 13).
- Learner: one scikit-learn `RandomForestRegressor` per leg. 100 trees, depth 6, leaf 20, max features 0.5, `random_state` 0. RF is the best tree model in Tables 3 and 7. No validation tuning.
- Walk-forward: expanding window. Refit at each December month end. Train only on rows whose label is realised (label `available_at` ≤ decision time of the refit date). The first fit needs 36 formation months (the source's 3-year training span).

## Inputs
| Field | Production table and column | as_of | available_at rule | Have |
|---|---|---|---|---|
| Bond excess return, 1 month | `bond_panel` `price`, `coupon`, `tsy_yield`, `mod_dur`, `accrue_to`, `hedge_date`, `carried` | `date` | panel `available_at` (date + 1 day) | have |
| MAT, DUR | `bond_panel.years`, `bond_panel.mod_dur` | `date` | panel | have |
| Spread (our addition, not in the 43) | `bond_panel.g_spread`, log | `date` | panel | have |
| AvgBidAsk proxy | `bond_panel.bid_ask_pts` / `price` | `date` | panel | have (proxy) |
| Size proxy | `bond_panel.par_volume`, log | `date` | panel | have (proxy). Amount outstanding: need |
| Rating (1 = AAA … 21 = C and D) | `ratings.splticrm` | `datadate` | `available_at`, at most 62 days old | have to Feb 2017 |
| VaR5, VaR10, ES5, ES10, VOL, SKEW, KURT, β_Bond, COSKEW, ISKEW, REV, MOM6, MOM12, LTR | built from the bond monthly returns | month end | label `available_at` | have |
| Stock return | `equity_monthly.ret` | `datadate` | datadate + 1 day | have, from 2007 |
| Stock features: mom1m, mom6m, mom12m, mom36m, chmom, retvol, beta | built from `equity_monthly.ret` | `datadate` | as above | have (monthly proxies) |
| Leverage (stock feature) | `leverage.leverage`, log | `date` | panel | have |
| T-bill (optional) | new panel `tbill_monthly`: `date`, `rf`, `available_at` | month end | download time | need. Missing: rf = 0 |
| Age, ILLIQ, Roll, Amihud and 13 other daily liquidity measures, β_DEF, β_TERM, β_VIX, β_UNC, factor betas | daily TRACE and factor series | | | need |
| The other 87 GHZ stock characteristics | CRSP and Compustat | | | need |

## Build steps
1. Filter every panel to `available_at` ≤ `decision_time(as_of)`. Missing `bond_panel` or `equity_monthly` gives an empty frame.
2. Bond monthly returns: `realised_excess_return(h = 1, beta = 0)` per cusip and formation month. Label `available_at` = the end row's `available_at`.
3. Firm bond return RB per gvkey and month: equal-weight mean. Stock excess return RS = `ret` − rf.
4. ĥ per gvkey and month t: OLS slope of RB on RS over t−35 to t, at least 24 pairs.
5. Bond features per cusip at t, then the firm mean. Return windows: REV is month t. MOM6 is t−6 to t−1. MOM12 is t−11 to t−1. LTR is t−47 to t−12. The 36-month risk window is t−35 to t (at least 24 months). The source writes these one month earlier because its t is the return month.
6. Stock features per gvkey at t. Rank every feature per month to [−1, 1], NaN to 0.
7. Fit date F = latest December month end ≤ as_of. ψ1 trains on (XS_t, RS_{t+1}). ψ2 trains on (XB_t, RB_{t+1} − ĥ_t RS_{t+1}). Both use only rows with label `available_at` ≤ `decision_time(F)`.
8. Score at as_of: ĥ·ψ1 + ψ2 for every gvkey with an eligible bond at as_of. A pre-fitted model may come in `params`. It must carry a label date ≤ `decision_time(as_of)`.

## Code placement
- `hy/factors/f07_merton_ml_forecast.py`. `compute(panels, as_of, **params) -> DataFrame`. `fit(panels, as_of, **params) -> MertonModel`. `walk_forward(panels, months, **params)` refits once a year.
- Helpers: `rolling_slope`, `hedge_ratio`, `rbmrs`, `merton_forecast`, `downside_risk`, `window_stats`, `return_windows`, `stock_windows`, `rank_features`, `build_features`, `training_set`, `fit_date`.
- Output: `date`, `gvkey`, `score`, `available_at`, `h_hat`, `psi1_stock`, `psi2_bond`, `has_equity`, `n_bonds`, `fit_date`. With `bond_only=True` also `f1_bond_only` (the f1(XB) benchmark).
- Reuses `hy.backtest.decision_time`, `realised_excess_return`, `eligible`, `assert_no_lookahead`, and `hy.peers.RATING_STALE_DAYS`.
- Docstrings cite methodology Section 8 (new signal "Merton-restricted expected return") and Section 11 (backtest design), with eqs. (10), (11), (19)–(21).

## Tests
- Unit: the training set never holds a label realised after `decision_time(F)`. Rows dated after as_of do not change the output. A pre-fitted model with a later label date raises `LookAheadError`. Sign: a synthetic panel where RB = h·RS + noise and RS is predictable from mom1m ranks the high-forecast issuer first. Edges: missing `equity_monthly` gives an empty frame. A private issuer gets ĥ = 0 and a finite score. Fewer than 24 pairs gives no ĥ.
- Helpers: ĥ matches a hand OLS slope. VaR5 is minus the second-lowest return. The forecast combines as ĥ·ψ1 + ψ2.
- Evaluation: horizon 1 month, US HY TRACE 2005–2024. Monthly rank IC of `score` beyond `g_spread` (`ic_beyond`), net of `bid_ask_pts` cost and turnover. Pass: positive in at least three of the four `CYCLE_WINDOWS`. And the restricted High−Low decile spread beats `f1_bond_only` by at least 0.10% a month, Newey-West t ≥ 2 (our threshold, near the source's median gain).

## Risks
- Source evidence, value-weighted, 75% IG and 25% HY (p. 13): bond-only High−Low 0.16% (OLS, t 1.38) to 0.79% a month (RF t 2.78, LSTM t 3.33). Combination 0.67% (t 3.41) (Table 3, p. 42). Restricted 0.55% to 0.92% for ML. RF 0.86% (t 3.01), LSTM 0.92% (t 2.69), Combination 0.84% (t 3.27). OLS 0.18% (t 1.07) (Table 7, p. 46).
- Out-of-sample R² of the restricted Combination is 4.95% (Table 6, p. 45). Bond-only Combination is 2.09% (p. 14).
- Stock characteristics without the structure add little (p. 21, Table 5).
- No HY-only split. Hedge-ratio MSE is lower for HY than IG (p. 25, Table 10).
- Most of the spread is in the top decile. RF decile 10 earns 1.37%. Deciles 1 to 9 earn 0.49% to 0.69% (Table 3, p. 42). A long-only HY book can use it.
- Costs: the net-of-cost check covers bond-only Table 3 only, with Roll spreads (p. 19, Table OA1, not in the folder). The restricted model has no cost number.
- Overlap: ψ1 loads on stock momentum, so it overlaps EMC and F03. ψ2 loads on illiquidity, VaR and bond momentum (Figs. 1–4, pp. 15–16). The source gives no correlation with EMC.
- Data: `equity_monthly` starts in 2007. ĥ then starts in 2009 and the first fit in 2012. The 2008 cycle window is empty until the equity export starts in 2004.
- Our feature set is 20 of 43 bond and 7 of 94 stock characteristics. Expect a weaker ψ2 than the source.

## Open questions
- Learner. Default RF, deterministic. A Ridge or forecast mean is a robustness run.
- ĥ = 0 for private issuers. The source drops them. Default: keep them with `has_equity` False. Test the equity-only subset as a check.
- Refit cadence. The source does not state one. Default: yearly, expanding window.
- Spread as a ψ2 feature. The source omits it. Default: include it, because the evaluation controls for spread anyway.
- Rating scale. The source says 21 = CCC (p. 29), but its own count reaches CCC at 18. Default: S&P notches, AAA = 1, C and D = 21.
