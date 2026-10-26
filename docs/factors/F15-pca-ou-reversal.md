# F15. PCA residual reversal with an Ornstein-Uhlenbeck s-score

## 1. Header
- **Rank:** 15 of 30, Tier 3 (tested outside credit, buildable now). **Status:** NEW. A short-horizon leg for Section 8. It uses the AR(1) residual dynamics of Section 7.5 on a statistical-factor residual.
- **Sources (all under `/home/ak/Documents/Quant Credit/`). Pages are PDF pages.**
  - Tomasi et al., Deutsche Bank Quantcraft "Reversion: new horizons" (17 March 2021), `Work_Quant (1)/reversion_long_doc (1).pdf`, pp. 2 to 7 and Appendix pp. 22 to 23. The method is Avellaneda and Lee (2009). The folder does not hold that paper.
  - The same study as slides, `Work_Quant (1)/9b070dd5_8bd1_40c7_ace2_768097379409_604 (1).pdf`, pp. 3 to 5.
  - `anonymous_rfq_alpha_feature_research_spec_from_quantcraft.md`, Families 3, 4 and 5 (variance-ratio, low-volatility and risk-appetite conditioners). No numbers.
- **Reader blocks:** F-F9 (`out_F.md`), G-F2 (`out_G.md`), B-F11 (`out_B.md`). Every number below was checked on the source page.
- **Reader corrections.** G-F2 gives a half-life cut of 8 weeks. The source has no such cut. Its only filter is 0 < b < 1 (pp. 7, 22). F-F9 puts the volatility result (p. 5, Fig. 4) on PCA-OU. Fig. 4 shows the EWMA strategies. No block reports the cross-sectional mean μ* (p. 22) or the ±4 winsorisation (p. 23).

## 2. Claim
In US high yield, a bond whose cumulative residual return (after the first n statistical factors) sits below its own OU equilibrium earns a higher excess return over duration-matched Treasuries in the next month. The rank IC of s beyond `g_spread` is positive after cost in at least three of the four cycles.

## 3. Definition
```latex
R^{*} = \tfrac{R - \bar R}{\operatorname{sd}(R)} = U S V^{\top}, \quad F = U_{n} S_{n} \ (T \times n) \qquad
r_{b,u} = c_b + F_u \beta_b + \varepsilon_{b,u}, \quad u \in \text{last } T' \text{ periods}
```
```latex
X_k = \sum_{u=1}^{k} \varepsilon_u, \quad X_{k+1} = a + b X_k + e_{k+1}, \quad
\mu = \tfrac{a}{1-b}, \ \theta = -\ln b \cdot A, \ \sigma_{eq} = \sqrt{\tfrac{\operatorname{var}(e)}{1-b^2}}, \quad
s = -\frac{X_{T'} - (\mu - \mu^{*})}{\sigma_{eq}}
```
Intuition: once the common factors leave the return, the residual price drifts back to its own mean, and s measures the gap in units of the residual's own equilibrium volatility.

What the source says:
- PCA on z-scored returns of the assets in the universe. T = 3 or 5 years of weekly returns (pp. 5, 6). Fixed n in {1, 2, 3, 4, 6, 12} (p. 6), or the smallest n whose squared singular values reach a fraction f in {0.05, 0.1, 0.2, 0.3, 0.4, 0.5} of the total (p. 5 note 13, p. 7).
- Regress the last T' unstandardised returns on the last T' rows of F, with an intercept. T' in {13, 26, 52} weeks (p. 6). The intercept makes X_{T'} = 0 (p. 22).
- OU fit by the lag-1 OLS of Eq. A2. var(e) = RSS / (n − 1 − 2) (Eq. A7). θ = −log(b) × 52 for weekly data (Eq. A4). θ does not enter s (p. 22).
- No signal when b ≤ 0 or b ≥ 1 (pp. 7, 22). Coverage above 99.8% for T' of half a year or one year, about 95% for one quarter (p. 7).
- s = −(X_n − μ)/σ_eq (Eq. A8). The source replaces μ by the mean μ* over the assets with a signal (p. 22). Winsorise s at ±4 (p. 23).
- Positions: open long in the top x% of s, close only below y%. Short is symmetric. x in {10, 20}, y in {30, 50} (p. 3). Best global set: x = 10%, y = 30% (p. 4 note 9). Signal-weighted positions, divided by their absolute sum (p. 23).
- Equities, January 2001 to October 2020, 4 bp cost, t+1 (t+2 global) execution (p. 3). Best net Sharpe 0.75 global, 0.77 North America, 0.80 Europe, 1.19 Asia. EWMA reversion: 0.34, 0.55, 0.39, 0.84 (p. 7). 144 configurations tested (p. 7).

What we decide:
- **Centring.** The literal p. 22 rule with X_{T'} = 0 gives s = μ*/σ_eq, one sign for every asset. Our choice: replace μ by μ − μ* (the Avellaneda-Lee centred form). Option `mu_mode` "own" (μ) and "pooled" (μ*, the literal text) stay for the production test.
- **Monthly default.** r = monthly excess return over the duration-matched Treasury (`f04_bond_momentum.monthly_excess_returns`). T = 36 months (the 3-year case, p. 6). T' = 12 months (the one-year case, p. 6). n = 3. A = 12. Our choices.
- **Daily option.** `bond_daily` (F02 columns). r_d = s_{d−1} Δt − D (s_d − s_{d−1}) with D the bond's `mod_dur` at as_of. T = 252, T' = 63 trading days (the one-quarter case). A = 252. Our choices.
- **Speed filter.** Keep 0 < b < 1, and require the half-life ln 2 / (−ln b) to be at most T'/2 periods. Our choice, after Avellaneda and Lee, who keep fast reversion only.
- **Bid-ask bounce.** (1) Trade-weighted prices: the monthly mark is the par-weighted price of the month's last 7 days (`build_panels.py`). `bond_daily.g_spread` must be the par-weighted mean of the day's trades. (2) Skip one period: the monthly window ends at t − 1, so the price that starts the outcome return never enters the signal. The daily window ends 7 calendar days before t, the span of the month-end mark. `skip = 0` stays as a test.
- **Coverage.** A bond enters the PCA with at least 24 of 36 months (daily: 168 of 252 days), z-score 0 where missing. The OU fit needs all T' returns. Monthly gaps of up to 3 months spread R/k (F04 rule). Daily no-trade days carry the last spread for up to 10 days, and at least half the T' days need a trade.

## 4. Inputs
| Field | Production table and column | as_of | available_at rule | Have |
|---|---|---|---|---|
| Month-end price, coupon, duration, Treasury yield | `bond_panel` `price`, `coupon`, `mod_dur`, `tsy_yield`, `accrue_to`, `hedge_date` | `date` | panel `available_at` | have |
| Universe filters | `bond_panel` `carried`, `years`, `yield`, `g_spread`, `n_trades` | `date` | panel `available_at` | have |
| Issuer key | `bond_panel.gvkey` | `date` | panel `available_at` | have |
| Daily spread (optional) | `bond_daily` `cusip`, `date`, `g_spread` (par-weighted day mean), optional `n_trades` | trade day | trade day + 1 day (F02) | need |
| Cost | `bond_panel.bid_ask_pts` | `date` | panel `available_at` | have |

## 5. Build steps
1. Filter every panel to `available_at <= decision_time(as_of)`. Universe: `eligible` and `not_distressed` bonds at as_of with a `gvkey`.
2. Monthly returns of the universe bonds over the T months to t − skip (F04 helpers). Daily: spread returns over the T trading days to t − 7 days.
3. Option `level = "issuer"`: average the bond returns of each gvkey per period.
4. z-score the columns, SVD, keep n PCs (fixed, or by `var_frac`). F = U_n S_n.
5. One OLS of the last T' raw returns on [1, F] for every complete column. Keep the residuals.
6. Per column: X, the lag-1 OLS, μ, θ, σ_eq, half-life. Status `no_reversion` when b is outside (0, 1). Status `slow` when the half-life exceeds T'/2.
7. μ* = mean μ over the columns with status `ok`. s = −(X_{T'} − (μ − μ*))/σ_eq, winsorised at ±4. score = s.
8. Diagnostics: `vr` = Var(3-period residual sums) / (3 Var(residuals)) (Family 3). `pct` = percentile of score. `entry_signal` = ±1 in the top or bottom 10% (open band, p. 3).

## 6. Code placement
- `hy/factors/f15_pca_ou_reversal.py`: `compute(panels, as_of, freq="monthly", level="bond", n_pcs=3, var_frac=None, pca_window=None, ou_window=None, skip=None, mu_mode="centred")`.
- Helpers: `pca_factors`, `pc_residuals`, `ou_fit`, `s_score`, `variance_ratio`, `hysteresis`, `signal_weights`, `daily_spread_returns`.
- Reuses `hy.backtest.decision_time`, `eligible`, `not_distressed`, `hy.signals.half_life`, `hy.factors.f04_bond_momentum.monthly_excess_returns` and `spread_months`.
- Docstrings cite methodology Section 8 (new leg) and 7.5 (AR(1) residual and half-life). Columns: `date`, `cusip`, `score`, `available_at`, `gvkey`, `status`, `x_last`, `mu`, `mu_star`, `b`, `theta`, `half_life`, `sigma_eq`, `n_pcs`, `var_explained`, `vr`, `pct`, `entry_signal`, `freq`.

## 7. Tests
- Unit: contract. No look-ahead (rows after as_of and late `available_at` change nothing). With skip 1, a change to the month-t return changes nothing. Sign: bonds with a negative residual shock score above bonds with a positive shock. Edges: missing `bond_daily` with `freq="daily"` gives an empty frame. Short history gives NaN. A trending residual (b ≥ 1) gives `no_reversion`. Helpers against hand values.
- Evaluation (production): monthly rank IC of score beyond `g_spread` (`ic_beyond`), h = 1 month, after `round_trip_cost` × turnover under the x = 10%, y = 30% hysteresis. Pass: positive in at least three of the four `CYCLE_WINDOWS`. Second test (F-F9): S1 entries timed by s beat S1 alone on net IR by at least 0.1 in three of four cycles. Bounce check: run skip 0 and skip 1. If only skip 0 passes, the edge is bounce, and the factor fails.

## 8. Risks
- Bounce. TRACE marks revert by construction. The skip and the 7-day mark may also remove real reversal at a one-month horizon.
- Cost. The source assumes 4 bp per trade (p. 3). HY bid-ask is much larger. Reversion has high turnover (p. 3), so a gross edge may not survive.
- Data. 36 monthly points give a noisy PCA, and 12 points a noisy AR(1). The source warns that a short window lowers coverage (p. 7).
- Overlap. Opposite sign to F04 momentum at short horizons. Close to F06 (curve residual) and F05 (flow reversal). The source gives no correlation.
- Regime. The number of PCs for 50% of variance fell from about 25 to a few in 2008 (p. 7). A fixed n under-removes the common factor in a crisis. The source tested 144 configurations (p. 7), so its best Sharpe overstates a live result.

## 9. Open questions
- n and T. The source leaves them to search. Default n = 3, T = 36 months. Test n in {1, 3, 6} and `var_frac` 0.3.
- Centring of μ. Default μ − μ* (above). Test "own".
- Bond or issuer. Default bond (the source runs on single stocks). Issuer cuts gaps for one-bond issuers. Test both.
- Conditioners (Families 3 to 5). The spec leaves θ_VR, q_low and the risk-appetite threshold open. Default: report `vr`, no filter. The low-volatility and risk-appetite filters need VIX, MOVE and CDX panels. They wait for the production test.
- Portfolio. DTS-neutral legs (F-F9) or signal weights (p. 23). Default signal weights in each leg.
