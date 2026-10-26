# F01. IPCA conditional factor model (bond loadings from characteristics)

## 1. Header
- Rank 1. Tier 1: tested in credit, buildable now for the core set of characteristics.
- Status: NEW. It is an aggregator, signal S8, over characteristics and over S1 to S7 inputs.
- Source: Kelly, Palhares, Pruitt (2021), `/home/ak/Documents/Quant Credit/ssrn-3720789.pdf` (KPP). Pages are PDF pages: method pp. 6–9, data pp. 13–16, out-of-sample pp. 11–13 and 21–22, strategies pp. 28–30, characteristics pp. 31–33, segments p. 39, Table A.I p. 55, Table A.II p. 56, Tables IA.III to IA.V pp. 58–60.
- Reader blocks: A2-F4 (model), A2-F5 to A2-F9 (inputs: spread-to-D2D, skewness, profitability change, momentum, DtS target).

## 2. Claim
At each month end t, the out-of-sample IPCA expected return of a US high yield bond ranks its next 1-month DtS-scaled credit excess return with a positive sign, beyond spread level and after costs.

## 3. Definition
```latex
r_{i,t+1} = \beta_{i,t}' f_{t+1} + \varepsilon_{i,t+1}, \qquad \beta_{i,t} = z_{i,t}' \Gamma_\beta, \qquad
r_{i,t+1} = \frac{\tilde r_{i,t+1}}{\max(DtS_{i,t},\, 0.25)}, \qquad
\hat E_t[r_{i,t+1}] = z_{i,t}' \hat\Gamma_{\beta,t}\, \hat\lambda_t
```
Intuition: the characteristics tell which bonds load on the priced latent factors, and the loadings update each month with the characteristics.

Source says:
- Zero alpha (Γα = 0). K = 5 factors (p. 21). For K = 5 the test fails to reject zero alpha at 1%, p-value 2.6% (Table A.II, p. 56).
- z holds 29 characteristics plus a constant, L = 30 (p. 16). Each month the code ranks, demeans and scales each characteristic to [−0.5, 0.5]. The constant stays 1 (p. 15).
- r̃ is the bond total return minus a Treasury hedge portfolio (p. 14). DtS = duration × spread. The floor is 0.25. Forty percent of bonds sit below the floor (p. 14). DtS mean 0.529, median 0.35 (footnote 14, p. 14).
- Screens: spread 50 to 2000 bp at the start of the month, duration at least 0.25 years, no missing characteristic (p. 15).
- Estimation: alternating least squares (ALS) on the first-order conditions (p. 8, eqs. 2 and 3, footnote 6):
  - factor step: `f_{t+1} = (Γ' Z_t' Z_t Γ)^{-1} Γ' Z_t' r_{t+1}`, a cross-section regression of returns on betas.
  - Γ step: `vec(Γ') = (Σ_t Z_t'Z_t ⊗ f_{t+1} f_{t+1}')^{-1} Σ_t (Z_t ⊗ f_{t+1}')' r_{t+1}`, a pooled regression of returns on characteristics times factors.
  - Normalise: Γ'Γ = I, factor second moment diagonal and descending, factor means non-negative (p. 9).
- Out-of-sample: expanding window from month 1 to t gives Γ̂. The first test month is 36 months after the sample start (pp. 21–22). λ̂ is the mean factor return up to t (footnote 12, p. 13).
- Strategy: equal-weight quintiles of Ê_t, long top, short bottom, rebalanced monthly (p. 13). Cost 19 bp one way on |Δw| (p. 29). Weight smoothing `w̃_t = (1 − γ) w_t + γ w̃_{t−1}` (p. 30).

Our choice:
- Universe: the HY `bond_panel`, rows that pass `hy.backtest.eligible`, plus the KPP spread and duration screens.
- Missing characteristic: rank 0 (the cross-section median), and a flag column per group. KPP drop the row. TRACE gaps would drop too many HY bonds.
- Refit every month. ALS tolerance 1e-6 on the largest change in Γ, at most 500 iterations. Start from the first K right singular vectors of the managed portfolios `x_t = Z_t' r_{t+1} / N_t` (p. 8, eq. 4).
- λ̂_t: the mean of the in-sample factors of the fit at t. Factors from earlier fits have other rotations, so their mean has no meaning.
- Score: `s8_ipca` = Ê_t standardised by date (`hy.signals.standardise_by_date`). The page keeps Ê_t in DtS units, so the rank is return per unit of spread risk.

## 4. Inputs
`as_of` is the month end t unless the row says otherwise. Decision time = t + 1 day (`hy.backtest.decision_time`). "Have" means the production tables hold the field today. Ratings are "have" only when the user exports the `ratings` panel. This machine's ratings end in February 2017.

| # | KPP characteristic (Table A.I, p. 55) | Our field: table and column | `available_at` rule | Status |
|---|---|---|---|---|
| T1 | Credit excess return r̃ | `bond_panel` price, coupon, tsy_yield, mod_dur: `total − tsy_ret` of `realised_excess_return` | t+1 row: last trade + 1 day | have |
| T2 | DtS | `bond_panel` mod_dur × g_spread | last trade + 1 day | have, biased (box below) |
| 1 | Bond age | first month of the bond in `bond_panel` (left-censored). Issue date is not in `bonds` | last trade + 1 day | need `bonds.issue_date` |
| 2 | Coupon | `bonds.coupon` | static | have |
| 3 | Face value | amount outstanding, not in `bonds` | issue date | need |
| 4 | Book-to-price | book equity, not in `financials`. `market_value.value` | filing acceptance | need book equity |
| 5 | Debt-to-EBITDA | `leverage.leverage` | month end + 1 day | have |
| 6 | Duration | `bond_panel.mod_dur` (bullet, calls ignored) | last trade + 1 day | have, biased |
| 7 | Mom. 6m equity (6-2) | `equity_monthly.ret` | export `available_at` | have |
| 8 | Earnings-to-price | net income, not in `financials` | filing acceptance | need |
| 9 | Equity market cap | `market_value.value` (quarterly) | `rdq` | have, stale up to a quarter |
| 10 | Equity volatility | `equity_monthly.ret`, 24 months | export `available_at` | have |
| 11 | Firm total debt | `leverage.debt` | month end + 1 day | have |
| 12 | Mom. 6m (bond, 6-2) | T1 series | last trade + 1 day | have |
| 13 | Mom. 6m industry | item 12 minus its `gics.gsector` mean | `gics.available_at` | have |
| 14 | Mom. 6m × rating | item 12 × item 22 | `ratings.available_at` | have if exported |
| 15 | Book leverage | equity, minority interest, preferred: not in `financials` | filing acceptance | need |
| 16 | Market leverage | `debt_current + debt_long_term − cash − inventory`, `market_value.value`. No minority interest, no preferred | filing acceptance, `rdq` | partial |
| 17 | Turnover volatility | `financials.revenue` over total assets. Assets not in `financials` | filing acceptance | need assets |
| 18 | Spread | `bond_panel.g_spread` (G-spread, not OAS) | last trade + 1 day | have, biased |
| 19 | Operating leverage | `(revenue − ebitda_adj_company) / ebitda_adj_company`, LTM | filing acceptance | have |
| 20 | Profitability | `(revenue − cogs) / assets` | filing acceptance | need assets |
| 21 | Profitability change, 5 years | item 20 now minus 5 years earlier | filing acceptance | need assets |
| 22 | Rating, 1 to 22 | `ratings.splticrm` mapped to 1 (AAA) to 22 (D) | `ratings.available_at`, stale after 62 days | have if exported |
| 23 | Distance-to-default (Shumway) | `market_value.value`, `equity_monthly.ret`, `leverage.debt`, `treasury_curve` | latest of the four | have (rank 2 page) |
| 24 | Bond skewness, 60 months | T1 series | last trade + 1 day | have, sparse |
| 25 | Mom. 6m log(Spread) | `log g_spread(t−6) − log g_spread(t)` | last trade + 1 day | have, biased |
| 26 | Spread-to-D2D | `g_spread / Φ(−DD)` | latest of items 18 and 23 | have, biased |
| 27 | Bond volatility, 24 months | T1 series | last trade + 1 day | have, sparse |
| 28 | Value-at-risk | 2nd lowest T1 over 36 months, at least 24 | last trade + 1 day | have, sparse |
| 29 | VIX beta, 60 months | needs Mkt-RF, HML, SMB, DEF, TERM, VIX | publication date | need |

Count: 17 have, 2 have if `ratings` is exported, 1 partial, 9 need. The four largest Γ rows are all "have": spread 0.34, constant 0.34, duration 0.32, bond volatility 0.31 (Table IX, p. 31).

**G-spread bias and our fix.** KPP use the vendor's option-adjusted spread and spread duration. They say callability "create[s] large distortions in bond spreads and returns" and that TRACE users must make crude adjustments (p. 13). Our `g_spread` is yield to maturity minus the Treasury curve, and `mod_dur` is a bullet duration (`hy.backtest` docstring, assumption 2). For a callable bond, the yield includes pay for the call option that the investor sells to the issuer. So G-spread exceeds OAS by the option cost. The gap grows as the price rises toward and above the call price. The bullet duration then overstates the effective duration, so DtS is too large and the scaled return too small. The model then ranks premium callable bonds too cheap, and their upside is capped at the call price. Our fix, in order:
1. Need: `bonds.first_call_date` and `bonds.first_call_price`. With them, compute the spread to worst and the duration to worst, and use both in items 6, 18, 25, 26 and T2.
2. Until then: add `price_premium = max(price − 100, 0) / 100` as instrument 31, so Γ can learn the distortion.
3. Report the IC separately for price below 100 and price at or above 102. The bias is small below par, so a gap between the two cells measures it.

## 5. Build steps
1. For each month end t, take `bond_panel` rows with `date ≤ t`. Keep carried rows for returns only (`trace_panel` rule 5).
2. Compute T1 per bond and month with `realised_excess_return(panel, 1, as_of)`: r̃ = `total − tsy_ret`. Divide by `max(DtS, 0.25)` at the start month.
3. Build the characteristics of section 4 at each month. Every input passes `assert_no_lookahead` at the decision time.
4. Apply the screens: eligible, spread 0.005 to 0.20, `mod_dur ≥ 0.25`, not carried.
5. Rank-scale each characteristic per month to [−0.5, 0.5]. Set missing values to 0. Append the constant 1.
6. Fit ALS on the pairs (z_s, r_{s+1}) with s + 1 ≤ t. Skip t until 36 months of pairs exist.
7. Compute λ̂_t, then Ê_t = z_t' Γ̂_t λ̂_t for every screened bond at t. Also write `ipca_er_ret = Ê_t × max(DtS, 0.25)`, the forecast in decimal return per month.
8. Write `s8_ipca` = Ê_t standardised by date. Copy `as_of = t` and `available_at = decision_time(t)` to each row.

## 6. Code placement
- Module `hy/ipca.py` holds the estimator, beside `hy/peers.py`. `hy/signals.py` gets the wrapper `s8_ipca`. Docstrings cite methodology Section 8, a new subsection "S8. Conditional factor expected return", with KPP eqs. (1), (2), (3) and (10). The tests cite Section 11.
- `rank_scale(chars: pd.DataFrame, cols: Sequence[str], date_col: str = "date") -> pd.DataFrame`
- `dts_scaled_return(r_tilde, mod_dur, g_spread, floor: float = 0.25) -> np.ndarray`
- `fit_ipca(Z: Mapping[pd.Timestamp, np.ndarray], R: Mapping[pd.Timestamp, np.ndarray], K: int = 5, tol: float = 1e-6, max_iter: int = 500) -> IPCAFit` with fields `gamma` (L × K), `factors` (T × K), `lam`, `n_iter`, `impact` (row norms of Γ, as Table IX).
- `class IPCAPredictor`, a dataclass that fits the `hy.backtest.Predictor` signature `(panel_up_to_t, fund_up_to_t, as_of, h_months) -> pd.Series`, in the pattern of `hy.backtest.FairLine`.
- Output columns: `date`, `cusip`, `ipca_er`, `ipca_er_ret`, `ipca_beta_1` to `ipca_beta_5`, `s8_ipca`, `as_of`, `available_at`.
- Reuse (all exist):
  - `hy.backtest`: `decision_time`, `assert_no_lookahead`, `eligible`, `realised_excess_return`, `round_trip_cost`, `run_predictions`.
  - `hy.backtest` scoring: `ic_series`, `ic_beyond`, `cycle_test`, `long_short`, `spread_neutral_long_short`, `book_legs`, `turnover_cost`, `portfolio_stats`, `hac_mean`.
  - `hy.peers`: `equity_momentum` (call it with `months=5` and month end t − 1 for 6-2), `sector_at`, `rating_at`.
  - `hy.signals`: `standardise_by_date`, `composite`, `neutralise`, `rank_ic_by_phase`, `passes_cycle_test`.
  - `hy.walkforward`: `rank_ic_by_date`.
- New helper: `rating_number(symbol) -> int`, S&P letter to 1 to 22. `hy.peers.rating_class` gives only 4 classes.

## 7. Tests
- No look-ahead: change every panel row with date > t. The forecast at t must not change. A row with `available_at` after the decision time raises `LookAheadError`.
- Sign: simulate 2,000 bonds over 120 months with K = 1, a known Γ and λ > 0. Γ̂ recovers Γ up to sign with correlation above 0.95. The rank IC of Ê_t against the true expected return is above 0.9.
- ALS: given Γ, the factor step equals the closed form of eq. (2). After the fit, Γ'Γ = I within 1e-8.
- Rank scale: every value lies in [−0.5, 0.5], the median is 0, and a missing value maps to 0.
- DtS: a bond with DtS 0.1 is divided by 0.25.
- Edge cases:
  - Sparse trades: a bond with a gap month has no return for that month. Its 24-month volatility is missing until 12 returns exist (our choice).
  - Missing equity: a private issuer gets 0 in the equity items and `flag_equity = 1`. Its forecast exists.
  - Defaulted bonds: a spread above 2000 bp, or a carried row, gets no score and enters no fit.
  - Thin month: fewer than `MIN_BONDS` = 20 bonds skips the month.
- Evaluation, horizon 1 month, rebalanced monthly:
  1. Rank IC of `s8_ipca` beyond spread (`ic_beyond`, control `g_spread`), net of `cost_rt`. Pass: positive in at least 3 of the 4 cycles 2008, 2015, 2020, 2022 (`cycle_test`).
  2. Quintile long-short after cost, γ = 0.3 smoothing. Pass: net Sharpe above 0.5 at 19 bp one way (A2-F4 bar) and above 0 at the TRACE bid-ask cost.
  3. Out-of-sample total R² (KPP eq. 6) above 0.

## 8. Risks
- Cost. KPP report a monthly turnover of 68% (tangency) and 76% (quintile spread) at γ = 0 (Table VIII, p. 29). The net Sharpe falls from 2.48 at 19 bp to 1.27 at 25 bp and to −1.71 at 40 bp, tangency, γ = 0 (Table IA.IV, p. 59). HY bid-ask on TRACE can exceed 19 bp one way, so cost can remove the effect.
- Slow variant. 19 low-volatility characteristics cut turnover by about 40 points. Net Sharpe is then 1.90 tangency and 1.57 quintile spread (p. 30, Table IA.V p. 60). Of these 19, 11 are "have" in section 4.
- Overlap: spread, duration and bond volatility drive Γ (p. 33). So `s8_ipca` will correlate with spread level and with DtS. KPP give no correlation number. The beyond-spread IC tests this.
- Overlap with S1: S1 and spread-to-D2D both measure value. Run `ic_beyond` of S1 with control `s8_ipca` and the reverse.
- Data: KPP use ICE IG and HY, Dec 1999 to Dec 2020, 14,600 bonds, 555,894 bond-months (pp. 14–15). Our panel is HY only, TRACE, with G-spread. The HY fit in KPP holds within one IG and HY model: out-of-sample total R² 48.6% for BB, 45.8% for B to D, 46.0% to 48.5% across HY liquidity terciles (Table XIII, p. 39). Nobody tested a HY-only fit.
- Cycle coverage: `build_panels.py` starts at 2010-01-31 in the guide. Then the first forecast is 2013-01 and 2008 has no data, which `cycle_test` counts as a fail. To test 2008, start the panel at 2005-01-31 or earlier.

## 9. Open questions
1. Missing characteristics. Source: complete cases only (p. 15). Default: rank 0 and a flag. Check: refit on complete cases and compare the IC.
2. Universe. Source: IG and HY in one model, not re-estimated per segment (p. 39). Default: HY only, because our panel holds grade H only. Check: add BBB bonds if the panel gains them.
3. K. Source: K = 5. The quintile Sharpe peaks at K = 4, 3.76 against 3.53 (Table VII, p. 28). Default: K = 5. Report K = 1 to 5 out of sample, and never pick K on the test years.
4. 6-2 momentum. Source gives no month count beyond "6-2" (p. 55). Default: compound months t − 5 to t − 1, skip month t.
5. Equity volatility and DD inputs. Source gives no window for equity volatility. Default: 24 months, to match bond volatility.
6. Role in the composite. Default: `s8_ipca` enters the Section 8 composite as one more signal with IC weights by phase. Version B adds `esp_sr`, EMC and S2 as instruments. If B beats the composite IC (HAC t above 2 on the paired IC difference), B replaces the composite for those signals. The two never both enter, so no signal counts twice.
7. Tangency portfolio. Source reports it (Sharpe 6.23 gross, p. 28). Default: skip it. It shorts every bond in the cross-section, which an HY book cannot do. Score the quintile spread only.
