# F20. Tail dependence of spread changes with the market

- **Rank:** 20. **Tier:** 3. **Status:** NEW. Low-risk variant: a nonlinear form of the market beta of spread changes. Candidate control for the S1 residual (methodology Section 8) and a tail input to the position risk measures (Section 9.3).
- **Source:** Pelster and Vilsmeier (2018), "The determinants of CDS spreads: evidence from the model space", *Review of Derivatives Research* 21: 63–118. File `/home/ak/Documents/Quant Credit/The determinants of CDS spreads_ evidence from.pdf`. Pages below are PDF pages. Printed page = PDF page + 62. Sample: p. 5. Daily data and quarterly averages: p. 6. Table 1: p. 8. Copula forms: pp. 8–9. Expected signs: p. 10. Variables: Table 3, p. 13. Sign restrictions: Table 4, p. 15. BMA: Table 6, p. 26. HY subsample: Table 9, p. 30. Out-of-sample: Table 13, p. 38, and pp. 39–40. Estimation: Appendix A, pp. 40–44.
- **Reader block:** A2-F10 (`research/notes/quant-credit-review/out_A2.md`). The reader writes "Gumbel U+L plus t-copula 35.5%". Table 13 row 1(j) is GumbelU + GumbelL + tCop + dtCop, 35.517% (p. 38). The UTD formula in the block is the standard t-copula result, not a formula of the paper.

## Claim
In US high yield, issuers whose G-spread changes have a higher upper tail dependence (UTD) with the market's spread changes, after control for rating class and spread level, widen more over the next quarter. So they earn a lower bond excess return over the next 3 months. Higher UTD = short.

## Definition
```latex
\lambda_U = 2\,t_{\nu+1}\!\left(-\sqrt{\frac{(\nu+1)(1-\rho)}{1+\rho}}\right),\qquad
\rho = \sin\!\left(\tfrac{\pi}{2}\,\tau_K\right),\qquad
\hat\nu = \arg\max_{\nu}\sum_{t}\log c_{\rho,\nu}(u_{1t},u_{2t})
```
Here u_1 and u_2 are the pseudo-observations of the issuer's and the market's filtered log spread changes, τ_K is Kendall's tau of the pair, and c is the bivariate t-copula density. Intuition: λ_U is the chance that the issuer widens in its worst 1% of periods given that the market widens in its worst 1%, as the 1% shrinks to zero.

What the source says:
- UTD and LTD are the "upper and lower tail dependence of daily CDS spread returns with CDS market returns", from a dynamic copula (Table 3, p. 13). CDSMarket is the daily log return of the Markit CDS market spread (p. 13). Spread returns are log differences (p. 6).
- Copulas: t, Gumbel, rotated Clayton, SJC (pp. 8–9). Upper tail = joint widening, "relevant in case of CDS" (p. 9). The t-copula has λ_U = λ_L (p. 44).
- Estimation: an AR(m)-GARCH(p,q) filter per series, m and the GARCH form by AIC. Then the empirical CDF with divisor T + 1. Then maximum likelihood of the copula (p. 41). The t-copula correlation follows the Patton (2006) update, ρ_t = tanh(f_t / 2) (p. 42). The degrees of freedom follow an exponential quadratic spline with k = 3 segments (p. 43). The estimated ν "is never larger than 21" (footnote 17, p. 39).
- The daily UTD enters as its quarterly average (p. 6). A firm needs at least 1 year of consecutive data (p. 5). The paper gives no other window. The dynamic copula runs over each firm's full sample (Appendix A, pp. 40–43).
- Empirical tail dependence follows Frahm et al. (2005), and only serves the goodness-of-fit test (Table 2, p. 10).

What we decide:
- Our choice: a static t-copula on a rolling window that ends at as_of. A full-sample dynamic fit reads the future. ρ by Kendall tau inversion (exact for every elliptical copula), ν by one-dimensional pseudo maximum likelihood on [2, 100].
- Our choice: filter = AR(1) by OLS on consecutive pairs, then division by an EWMA volatility with λ = 0.94. The source uses AR-GARCH by AIC. EWMA is the GARCH(1,1) limit with no constant.
- Frequency and window. `bond_daily` present: weekly changes (last trade of the week), 104 weeks, at least 52. Daily HY trades are sparse, so a daily change mixes 1-day and 5-day gaps. `freq="D"` stays as an option: 504 trade days, at least 250 (1 year, after p. 5). Only `bond_panel`: monthly changes, 60 months, at least 48. Our choices. With 48 to 60 points ν is weak, so λ_U mostly follows ρ. The column `freq` flags the source.
- Issuer change: the mean of the log G-spread changes of the issuer's bonds over consecutive periods. A gap gives no change. Our choice: a median spread across bonds jumps when the bond mix changes.
- Market change: the equal-weight mean of all issuers' changes in the period, leaving the issuer out. A period with fewer than 10 other issuers is NaN. Our choice.
- `utd_emp`: the empirical upper tail share at k = ⌊√n⌋. It is the share of the top k periods of the market that are also in the top k of the issuer. Our choice, a model-free check.
- Control: `utd_ctrl` = cross-sectional OLS residual of λ_U on rating class dummies and log issuer G-spread (`hy.signals.neutralise`). Without `ratings`, log spread only. Fewer than 20 scored issuers: `utd_ctrl` = λ_U minus its mean.
- Score = standardised percentile rank of −`utd_ctrl`. Higher score = long. See the sign note in Risks.

## Inputs
| Field | Production table and column | as_of | available_at rule | Have |
|---|---|---|---|---|
| Month-end G-spread, eligibility | `bond_panel` `date`, `cusip`, `gvkey`, `g_spread`, `years`, `yield`, `price`, `mod_dur`, `carried`, `n_trades` | `date` | panel `available_at` | have |
| Daily G-spread (optional) | `bond_daily` `cusip`, `date`, `g_spread` (par-weighted day mean, F02 panel) | trade day | trade day + 1 day | need |
| Rating class (optional) | `ratings.splticrm`, else implied class from `leverage` | `datadate` | panel `available_at` | have |

Every row the score reads has `available_at` <= `decision_time(t)` and a date <= t.

## Build steps
1. Keep rows with `available_at` <= `decision_time(t)` and date <= t.
2. Universe at t: `eligible` `bond_panel` rows with a gvkey. With `ratings`: class BB, B or CCC, raw S&P symbol not D or SD (F04 rule).
3. Per bond: last positive G-spread per period (week, trade day, or month). Monthly rows drop stale and carried rows (`f04.mark_stale`). Log change over consecutive periods only.
4. Issuer change = mean of its bonds' changes. Market change = leave-one-out mean over all issuers in the panel.
5. Per issuer in the universe, keep the last W periods. Filter both series (AR(1), EWMA). Keep joint observations. Need n >= the minimum.
6. Pseudo-observations u = rank / (n + 1). Fit ρ and ν. Compute λ_U and `utd_emp`.
7. Neutralise λ_U on rating class and log spread. Rank −`utd_ctrl`, standardise, write `score`.

## Code placement
- `hy/factors/f20_tail_dependence.py`. `compute(panels, as_of, freq="auto", window=None, min_obs=None)`. META level "issuer", key `gvkey`, horizon 3 months.
- Output columns: `date`, `gvkey`, `score`, `available_at`, `utd`, `utd_emp`, `utd_ctrl`, `rho`, `nu`, `n_obs`, `freq`, `ctrl`, `rclass`, `g_spread`.
- Helpers: `log_changes`, `market_changes`, `ar1_ewma_filter`, `pseudo_obs`, `t_copula_loglik`, `fit_t_copula`, `t_tail_dependence`, `empirical_upper_tail`, `control_residual`.
- Reuses `hy.backtest.decision_time`, `eligible`, `MIN_BONDS`, `f04.rating_classes`, `f04.mark_stale`, `f04.HY_CLASSES`, `f04.DEFAULT_SYMBOLS`, `hy.signals.neutralise`, `standardise_by_date`. scipy for the copula.

## Tests
- Unit (`tests/test_factor_f20.py`): contract, one row per gvkey. No look-ahead: rows after t and late `available_at` change nothing. Sign: an issuer that widens with the market only in its large moves gets a higher λ_U and a lower score than an independent issuer. Helpers against hand values: λ_U at ρ = 0.5, ν = 4 and ν = 10. Edges: missing `bond_panel` gives an empty frame, missing `bond_daily` falls back to monthly, short history gives NaN, gaps give no change.
- Evaluation (production machine): monthly rank IC of `score` beyond `g_spread` (`ic_beyond`) on the 3-month excess return, after cost, positive in at least three of the four `CYCLE_WINDOWS`. Second test (reader A2-F10): adding lagged λ_U to the S1 fair-spread regression lowers the out-of-sample RMSE of next-quarter issuer log spread change by 3% or more, Diebold-Mariano p < 0.05.

## Risks
- Sign. The paper regresses the quarterly log CDS change on the UTD of the prior quarter, with firm fixed effects: t-copula coefficient 0.848 (s.e. 0.152), F 30.95 (Table 1, p. 8). The BMA long-run multiplier is 0.636 unrestricted and 0.702 restricted (Table 6, p. 26). In the high-volatility (HY) subsample it is 0.429 and 0.550 (Table 9, p. 30). Table 4 imposes no sign on tCop (p. 15). A positive spread change is a negative bond return. So the paper shows: higher lagged UTD, lower future return. The paper also expects high-UTD contracts to "trade at a premium" (p. 10), a statement on levels. Our choice: short high UTD after control for spread level, so the level premium stays in the control.
- Within against across. Firm fixed effects make Table 1 a within-firm result. The score ranks across issuers. The cross-sectional sign is untested.
- Forecast strength. Out-of-sample RMSE: AR(2) 51.728%, tCop alone 39.000%, row 1(j) 35.517%, full BMA 34.611% (Table 13, p. 38). tCop alone does not beat Common (p = 0.453). Merton and macro variables add almost nothing (pp. 39–40).
- Data transfer. The source uses liquid on-the-run Markit 5-year CDS, 2001 to 2014, 277 firms (pp. 5–6). TRACE HY G-spreads are sparse and carry bid-ask bounce. The AR(1) step absorbs part of the bounce.
- Weak ν. At about 100 joint changes the ν estimate is noisy. In the unit test, one of 12 tail-dependent issuers with ρ = 0.81 fits ν = 100, so its λ_U falls near zero. Compare `utd` with `utd_emp` and the rank of ρ before a production run. A cap on ν (the source never exceeds 21, p. 39) is a variant to test.
- Overlap: λ_U rises with ρ, so the score is close to a low-beta tilt. Expect a high rank correlation with a plain spread-change beta. The source states no number.
- Cost: low turnover. One week or one month enters each window.

## Open questions
- Static against dynamic copula. Our choice: static on a rolling window. A Patton (2006) update fitted on the window only is the source form.
- Copula family. Our choice: t only. The paper finds Gumbel U and L add to tCop (pp. 39–40). A Gumbel fit is the next step.
- Window. Our choice: 104 weeks. Rerun with 52 weeks and with the quarterly average of a 52-week rolling λ_U, the source aggregation.
- Within-issuer variant. Score the change of λ_U over the quarter (dtCop, LRM 0.191, p. 26) as a second column.
