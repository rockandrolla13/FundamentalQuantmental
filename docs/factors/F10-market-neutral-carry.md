# F10. Market-neutral credit carry

## 1. Header
- Rank 10, tier 1 (tested in credit, buildable now). Status: variant of carry (Israel, Palhares, Richardson 2018) and of roll-down. It differs from the carry of `research/cards/israel-palhares-richardson-2018-common-factors.md`: that carry is OAS alone (p. 7), with no roll-down and no hedge.
- Reader block: G-F3.
- Source: Tzotchev, "Market-neutral carry" (J.P. Morgan, 4 October 2018), `Work_Quant (1)/JPM_Market_neutral_carry_2018-10-04_2790721 (1).pdf`. PDF pages: model pp. 3 to 5, estimation pp. 7 to 8, credit pp. 16 to 20, regimes p. 40, optimisation pp. 49 to 52.
- Source evidence is on CDS indices only: iTraxx Main 3, 5, 10y, iTraxx Crossover 5y, CDX IG 3, 5, 10y, CDX HY 5y (Table 11, p. 18). No cash bond enters the test.

## 2. Claim
For US HY bonds, the part of 1-month carry that market, rating and duration exposures do not explain predicts a positive 1-month excess return. The hedged long-short has a lower correlation with the HY index than raw carry.

## 3. Definition
Source, CDS (p. 17). Carry_{i,t} = Coupon_i − CD_{i,t}(Spread_{i,t,T−1} − Spread_{i,t,T}), with CD the credit duration. Return CR = Carry − CD Δ, Δ the realised spread minus the rolled-down implied spread. Factor model Δ = a + B F + ε. Hedge: w'(CD∘a) = 0 and w'(CD∘B) = 0. Then E(w'CR) = w'Carry and Var = Σ w_i² σ_i² (pp. 17 to 18). Note: the daily return divides the coupon by 365, the carry line does not. The reader block G-F3 puts the /365 in carry.

Our cash-bond carry over h = 1/12 year, with s the G-spread, D = `mod_dur`, ŝ the fitted spread curve:

```latex
c_b=\underbrace{s_b\,h}_{\text{spread carry}}\;\underbrace{-\,D_b\big(\hat s(T_b-h)-\hat s(T_b)\big)}_{\text{roll-down}},\qquad
\hat s(T)=a_0+a_1\,\frac{1-e^{-0.4T}}{0.4T}
```
Intuition: what the bond earns over Treasuries in one month if its spread curve does not move.

Hedge (our cross-sectional form). X = [1, DTS_b, D_b, 1{B}, 1{CCC}], DTS = D × s, W = diag(1/DTS²):

```latex
\hat k=(X'WX)^{-1}X'Wc,\qquad e=c-X\hat k,\qquad \text{score}_b=e_b/\mathrm{DTS}_b,\qquad w^{*}\propto We
```
Intuition: keep only the carry that no beta, rating or duration bet pays for.

What the source does, and why our form matches it:
- The source estimates B per asset from time series: PCA on 3-month and 6-month daily and 1-year and 2-year weekly returns, positions averaged across the four (p. 7). The Kaiser rule keeps PCs with eigenvalue above 1 (pp. 8, 52). It does not regress carry cross-sectionally.
- The source allows observable factors instead of PCs, for example equities and volatility for credit (p. 3). We use observable exposures, because few HY bonds have a long clean history.
- Under w'X = 0 the portfolio variance is w'Dw (p. 4). So max w'c subject to X'w = 0 and w'Dw ≤ V² gives w ∝ D⁻¹(c − Xk̂), with k̂ the WLS coefficient. Our residual is the source's optimum when leverage, risk-contribution and cost limits (pp. 50 to 51) do not bind.
- If carry is only beta pay, Carry = Σ k_i β_i, the hedged problem has no solution (p. 5). A zero residual IC is this case.

Our choices: issuer curve with 3 or more bonds over a 2-year maturity span. Else the within-issuer slope of the rating class (`f06.within_slope`, 5 or more issuers). Else all HY. Else a flat curve (roll 0). λ = 0.4 is the F06 forward shock decay (JPM 2012 p. 22). Idiosyncratic variance proportional to DTS² (the DTS idea of reader block A2-F9, as F04 uses it). Option `market="beta"` replaces DTS with a 24-month time-series beta to the equal-weight HY excess return, 12 months minimum. Option `market="both"` keeps both.

## 4. Inputs
| Field | Table and column | as_of | available_at lag rule | Status |
|---|---|---|---|---|
| G-spread, years, modified duration | `bond_panel.g_spread`, `years`, `mod_dur` | month end | last trade + 1 day | have |
| Eligibility fields | `bond_panel.carried`, `price`, `yield` | month end | as above | have |
| Rating class | `ratings.splticrm`, then leverage-implied (`f04.rating_classes`) | `datadate` | `available_at`, stale after 62 days | have |
| Leverage for the implied class | `leverage.leverage`, `ltm_ebitda` | `date` | `available_at` | have (optional) |
| Return history (beta option) | `bond_panel.price`, `coupon`, `tsy_yield`, `accrue_to`, `hedge_date`, `n_trades` | month end | as above | have |
| CDX HY or HYG return (long-only hedge) | none | daily | close + 1 day | need (evaluation only) |

## 5. Build steps
1. Read `bond_panel` and `ratings` with `available_at` ≤ T + 1 day. Keep `eligible` and `not_distressed` rows at T.
2. Score only classes BB, B and CCC. Drop raw D and SD.
3. Fit the issuer slope, else the class slope, else the HY slope. Compute `spread_carry`, `roll` and `carry`.
4. Build X. Under `market="beta"`, compute monthly excess returns (`f04.monthly_excess_returns`) and the rolling beta.
5. Fit the WLS on all scored bonds. Need 30 bonds (our choice). Write `carry_resid`, `score` and `w_opt` (scaled to Σ|w| = 2).

## 6. Code placement
- `hy/factors/f10_market_neutral_carry.py`: `compute(panels, as_of, horizon_months=1, market="dts", weighting="dts")`.
- Helpers: `spread_carry`, `curve_slope`, `roll_down`, `exposures`, `wls_residual`, `hedge_weights`, `rolling_beta`.
- Methodology: Section 8 (composite, neutralisation) and Section 9.3 (carry = accrual plus roll-down).
- Reuse: `hy.backtest.decision_time`, `eligible`, `not_distressed`, `hy.signals.neutralise` (equal-weight check), `f04.rating_classes`, `f04.monthly_excess_returns`, `f06.shock_basis`, `f06.within_slope`.
- Columns: `date, cusip, score, available_at, gvkey, rclass, g_spread, mod_dur, spread_carry, roll, carry, slope, curve_source, dts, beta_ts, carry_resid, w_opt, status`.

## 7. Tests
Unit (`tests/test_factor_f10.py`): no look-ahead, hand checks of carry and roll, X'We = 0, equal weights match `neutralise`, a bond with extra carry ranks first, pure-beta carry gives zero residual, missing panels give an empty frame.

Evaluation (production machine): monthly rank IC of `score` against the 1-month net excess return, beyond spread, after cost. Pass: mean IC above 0 and positive in at least 3 of the 4 cycles (2008, 2015, 2020, 2022). Portfolio test from G-F3: the `w_opt` book has net Sharpe above 0.4 and correlation with the HY index below 0.3. It beats raw carry in 2008 and 2020. Source benchmark: comprehensive solution return 7.29%, volatility 8.44%, Sharpe 0.86 after costs, drawdown 16.25% (Table 12, p. 18). Ranking solution Sharpe 0.02, drawdown 55.17% (Table 13, p. 19). Correlation with aggregate credit 0.13 against 0.22 for ranking (Table 14, p. 20).

## 8. Risks
- Raw HY carry is mostly beta. Israel et al. find carry correlation 0.80 with the credit premium and alpha t 0.7 (card, pp. 14 to 15). The residual can still track spread within a class. Report IC beyond `g_spread`.
- Shorts in cash HY cost more than in CDS. Long-only form: hold the positive-`w_opt` bonds and short CDX HY or HYG for the residual DTS. This hedge lives in the evaluation, not in the code.
- Carry income fell after the GFC (p. 18, Figure 22). The source also switches off on a structural break (p. 8). We do not.
- Roll-down on a thin issuer curve is noisy. The 2-year span rule limits it.
- Turnover: the source deducts running and execution costs (p. 50). Our score has no cost term. Use `round_trip_cost` in evaluation.

## 9. Open questions
1. Statistical factors. The source uses Kaiser-rule PCs. Default: observable exposures. Variant: PCA on rating x duration cell returns, then per-bond betas.
2. Horizon. The source rebalances daily with a one-day delay (p. 8). Default h = 1 month to match the panel.
3. Score scale. Default e/DTS, the residual form of the carry-to-vol rank (p. 5). Variant: `w_opt`.
4. Regime use. Cross-asset comprehensive Sharpe by QMI regime, since 2000: contraction 1.47, slowdown 1.27 (Table 35, p. 40). This is not a credit result. Default: no regime switch.
