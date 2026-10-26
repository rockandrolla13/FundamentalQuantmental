# F02. Spread to distance-to-default (with a CreditGrades variant)

## 1. Header
- **Rank:** 2 of 30, Tier 1 (tested in credit, buildable now).
- **Status:** variant of S1 fair value residual (Section 8) and of the Correia, Richardson and Tuna (2012) credit relative value gap. Variant B (CreditGrades) is a variant of the same gap with an equity-implied spread.
- **Sources (all under `/home/ak/Documents/Quant Credit/`):** Kelly, Palhares, Pruitt (2021), `ssrn-3720789.pdf`, PDF pp. 13 to 18, 31, 55, 58. Alber thesis, `CapArb/cap arb.pdf`, PDF pp. 2, 18, 21 to 30. Avino and Lazar (2020), `CapArb/cap arb perspective.pdf`, journal pp. 82 to 83.
- **Reader blocks:** A2-F5, C-F5. **Repo cards:** `research/cards/bharath-shumway-2008-merton-dd.md`, `research/cards/correia-richardson-tuna-2012-value-investing-credit.md`.
- **What it adds beyond the two cards.** Bharath and Shumway give the DD but no bond return test for high yield. Correia, Richardson and Tuna map PD to a spread with fixed constants (T = 5, R = 40%, λ = 0.5) and their returns end in May 2009. F02 divides the spread by the raw PD with no mapping constants. Its evidence covers ICE IG and HY to December 2020, and it survives inside a 29-characteristic model. Variant B adds a market-implied default barrier and an issuer-own time-series band.

## 2. Claim
Among US high yield bonds of listed issuers, a high spread per unit of equity-implied default probability predicts a higher DTS-scaled excess return over the next month, with a positive sign, beyond the spread level.

## 3. Definition
**Variant A (primary).** Source says (p. 55): "the option-adjusted spread, divided by one minus the CDF of the Shumway distance-to-default".

```latex
S2D_{i,t} = \frac{s_{i,t}}{1-\Phi(DD_{j,t})} = \frac{s_{i,t}}{\Phi(-DD_{j,t})}, \qquad x_{i,t} = \log s_{i,t} - \log\Phi(-DD_{j,t})
```

Intuition: spread paid per unit of default probability. A high value means the bond pays a lot for little default risk. Bond i belongs to issuer j.

- **What the source leaves open.** The paper cites "Shumway (2001)" (p. 55) and Israel et al. (2018) for the DD. It does not state naive or iterative Merton, horizon, debt measure, or volatility window.
- **Our choice: the naive DD of Bharath and Shumway (2008),** repo card eqs. 8 to 12. `F = debt_current + 0.5 × debt_long_term`. E = month-end price × shares. T = 1 year. σ_E = annualised standard deviation of the prior 252 daily returns, fallback prior 12 monthly returns × √12. σ_V = E/(E+F)·σ_E + F/(E+F)·(0.05 + 0.25σ_E). μ = the stock return over the prior 12 months. `DD = [ln((E+F)/F) + (μ − 0.5σ_V²)T] / (σ_V √T)`.
- **Scaling.** Source says: each month, rank characteristics cross-sectionally and map them to [−0.5, 0.5] (p. 15). The rank of S2D equals the rank of x. Our choice: compute x with `scipy.special.log_ndtr(-DD)`, so no PD floor is needed. Winsorise x at the 1st and 99th percentiles per month (Bharath and Shumway card). Rank within rating bucket (BB, B, CCC) and also in the full HY cross-section.

**Variant B (test second): CreditGrades gap.** Source says, Finger et al. (2002) as reported by Alber (PDF p. 23, eqs. 17 to 19):

```latex
P(t) = \Phi\Big(-\tfrac{A_t}{2} + \tfrac{\ln d}{A_t}\Big) - d\,\Phi\Big(-\tfrac{A_t}{2} - \tfrac{\ln d}{A_t}\Big), \quad d = \frac{S_0 + \bar L D}{\bar L D}\,e^{\lambda^2}, \quad A_t^2 = \Big(\sigma_S^{*}\frac{S^{*}}{S^{*}+\bar L D}\Big)^2 t + \lambda^2
```

The printed eq. 17 shows "+ ln d / A_t" in the second term. That is a typo: eq. 21 and the reader block carry the minus sign. Kiesel and Veraart (2008) exact form (PDF p. 24, eq. 21), with Φ₂ the bivariate normal CDF and correlation as the third argument:

```latex
P(t) = \Phi_2\Big(-\tfrac{\lambda}{2} + \tfrac{\ln d}{\lambda},\; -\tfrac{A_t}{2} + \tfrac{\ln d}{A_t};\; \tfrac{\lambda}{A_t}\Big) - d\,\Phi_2\Big(\tfrac{\lambda}{2} + \tfrac{\ln d}{\lambda},\; -\tfrac{A_t}{2} - \tfrac{\ln d}{A_t};\; -\tfrac{\lambda}{A_t}\Big)
```

Intuition: the default barrier is uncertain, so a firm can default at once when the barrier is higher than expected. The bivariate term counts that first-day jump exactly.

- **Parameters (source).** L̄ = 0.5 and λ = 0.3 (PDF p. 21). R = 0.3 (PDF p. 24). D = short-term plus long-term interest-bearing debt + 0.5 × other liabilities, less minority interest capped at 50% of financial debt (PDF p. 22). Asset volatility σ_A = σ_S·S/(S + L̄D) (PDF p. 23, eq. 16). Kiesel and Veraart show the approximation is poor when the share-to-debt ratio is below 0.796 (PDF p. 24, footnote 15). Many HY issuers sit below that ratio.
- **Volatility (source).** Wojtowicz (2014): imply σ from the market spread each day, then price with its one-year mean (PDF p. 25). Finger et al. used a 1000-day mean of equity volatility (PDF p. 23).
- **Gap and trigger (source, PDF p. 29).** Enter when |s^model − s^mkt| > d̄_c + a·σ_d. d̄_c is the c-day mean of the absolute gap, and σ_d is the standard deviation of the gap. a = 4 and c = 20 days. Exit inside a 1% interval (PDF p. 29) or after 180 days (PDF p. 30).
- **Our choice.** Work in issuer totals, not per share: d does not change. Map P(t) to a spread with s^CG = −(1−R) ln P(t) / t at t = bond duration. Use the same map for both P(t) forms, so the only difference is the KV term. The source CDS formula (eq. 20, PDF p. 24) uses the Finger approximation inside G(t), so we do not use it with KV. Score g = sign(gap)·(|gap| − d̄₂₀)/σ_d,₂₀ with gap = log s^mkt − log s^CG. The trigger flag is g > 4.

## 4. Inputs
| Field | Production table and column | `as_of` | `available_at` lag rule | Status |
|---|---|---|---|---|
| Bond spread s | `bond_panel.g_spread` (G-spread, not OAS) | month end | panel `available_at` (bond_obs: trade day + 1 day) | have |
| Daily bond yield (Variant B gap) | `bond_obs.yield`, `bond_obs.date` | trade day | trade day + 1 day | have |
| Duration | `bond_panel.mod_dur` | month end | panel `available_at` | have |
| Short and long debt | `financials.debt_current`, `financials.debt_long_term` (`dlcq`, `dlttq`) | `period_end` | EDGAR acceptance time of the 10-Q or 10-K. Typical lag 40 to 90 days | have |
| Other liabilities, minority interest (Variant B D) | Compustat `ltq`, `mibq` | `period_end` | as `financials` | need |
| Daily equity price and shares (E, σ_E, S) | new table `equity_daily` (CRSP `prc`, `shrout`, `ret`) | trade day | trade day + 1 day (our choice, same rule as `bond_obs`) | need |
| Monthly equity return (fallback σ_E, μ) | `equity_monthly.ret` | month end | panel `available_at` | have |
| Quarterly market value (fallback E) | `market_value.value` | quarter end | `rdq` | have |
| Risk-free rate r | `treasury_curve` 1-year column | curve date | next day | have |
| Rating bucket | `ratings.splticrm`, else leverage-implied class | `datadate` | panel `available_at`. Ends February 2017 on this machine | have |

The DD row takes the latest `available_at` of its inputs. The decision time is `hy.backtest.decision_time(month_end)`, month end + 1 day.

## 5. Build steps
1. For each issuer and month end t, take the latest `financials` row with `available_at` ≤ decision time. Compute F. Drop the issuer if F ≤ 0.
2. From `equity_daily`, take E at t and the prior 252 daily returns (minimum 126). Compute σ_E and μ. Use the monthly fallback when daily data is absent, and flag the row.
3. Compute naive σ_V, DD and `log_pd = log_ndtr(-DD)` per issuer.
4. Join to each eligible bond in `bond_panel` at t (`hy.backtest.eligible`). Keep bonds with g_spread from 50 bp to 2000 bp and duration ≥ 0.25 years, as in the source (p. 15).
5. Compute x = log g_spread − log_pd. Winsorise per month. Rank to [−0.5, 0.5] by month and within rating bucket.
6. Variant B: per issuer and trade day, compute s^CG (Finger and KV) at each bond's duration. Imply σ_A from the market spread each day. Price with its trailing 252-day mean. Compute the gap and g on the 20-day window. At month end, keep g and the flag.
7. Write one row per bond per month end with `as_of = t` and `available_at` = max of input `available_at`.

## 6. Code placement
- **Module:** `hy/fairspread.py`, Section 7.1 block, beside `PDModel`. It fills the empty feature `dd_equity`.
  - `naive_dd(E, F, sigma_e, mu, r=None, T=1.0) -> np.ndarray`. Docstring cites Section 7.1 and Bharath and Shumway eq. 12.
  - `spread_to_dd(g_spread, dd) -> np.ndarray` returns x. Docstring cites Section 7.1 and Section 8 S1, KPP Table A.I.
  - `creditgrades_survival(S, D, sigma_a, t, Lbar=0.5, lam=0.3, exact=True) -> np.ndarray`. Docstring cites Section 7.1 and Alber eqs. 17 to 21.
  - `creditgrades_spread(P, t, R=0.3) -> np.ndarray`.
- **Module:** `hy/signals.py`. `s1_d2d_score(df, by="rating_bucket") -> pd.Series`, and `cg_gap_score(gap: pd.Series, c=20, a=4.0) -> pd.DataFrame`. Docstrings cite Section 8 S1.
- **Output columns:** `dd_equity`, `log_pd_dd`, `s2d_log`, `s2d_rank`, `s2d_rank_rb`, `cg_spread`, `cg_spread_kv`, `cg_gap`, `cg_z`, `cg_flag`, plus `as_of`, `available_at`.
- **Reuse:** no Merton or DD function exists in `hy/` (grep for "merton", "distance", "dd_equity" finds only the `PD_FEATURES` name). Reuse `hy.backtest.decision_time`, `assert_no_lookahead`, `eligible`, `ic_series`, `ic_beyond`, `cycle_test`, `long_short`, `evaluate`, and `hy.signals.rank_ic`, `standardise_by_date`. Use `scipy.stats.multivariate_normal.cdf` for Φ₂.

## 7. Tests
- **No look-ahead.** A 10-Q accepted on day t + 2 must not enter the score at month end t. `assert_no_lookahead` must pass on every input frame.
- **Sign on a synthetic case.** Two issuers with the same DD and spreads of 300 bp and 600 bp: the wider bond ranks higher. Two issuers with the same spread: the higher DD ranks higher.
- **DD monotone.** DD falls when F rises, and when σ_E rises. **KV against Finger.** At share-to-debt ratio 2, the two P(t) agree within 1e-3. At ratio 0.5, they differ. KV P(t) lies in [0, 1] for all test inputs.
- **Edge cases.** No equity: score NaN, not zero. Fewer than 126 daily returns: monthly fallback with a flag. Defaulted bond or spread > 2000 bp: excluded. Sparse trades: a bond with no trade in the last 7 days of the month has no score. Variant B with fewer than 20 gap days: g is NaN.
- **Evaluation.** Horizon 1 month (source), also 3 and 6 months. Target: DTS-scaled excess return, `realised_net`. Use `ic_beyond(df, "s2d_rank_rb", "realised_net", control="g_spread")`.
  - Pass 1: mean monthly rank IC beyond spread > 0 after costs in at least 3 of 4 cycles (`cycle_test`).
  - Pass 2 (reader A2 proposal): top-minus-bottom quintile within rating bucket, 1-month return, t > 2 (`hac_mean`).
  - Pass 3 (our choice): IC beyond spread stays > 0 with `dd_equity` alone as a second control. That shows the ratio adds to the PD rank.
  - Variant B pass (reader C proposal): next-month rank IC of `cg_z` > 0 with t > 2, after control for S1 and OneScore, and incremental IC over Variant A > 0.01.

## 8. Risks
- **Spread overlap.** S2D is spread over a PD, so it loads on spread. The source gives no correlation with spread. The source Sharpe of spread alone is 0.81 (p. 16). Always test beyond spread.
- **Equity momentum overlap.** DD moves with the stock price. The source does not state the correlation with equity momentum (Sharpe 1.76, p. 16). Test against OneScore (E16).
- **Beta.** Source says high S2D predicts lower future market beta (coefficient −0.13, p. 18). So the factor is not a disguised high-beta bet.
- **Scaling.** The 1.25 Sharpe uses DtS-scaled returns (p. 16). Without scaling, the Sharpe is 0.68 (p. 58). The source uses ICE OAS. Our G-spread includes call value, so callable HY bonds look wide. That bias can inflate x for callable bonds.
- **Variant B evidence is weak for HY.** Alber: 67 European firms, 5 HY (PDF p. 26). Alpha 2.3% a year over 2008 to 2015, 5.7% over 2008 to 2011, and 0.25% (not significant) over 2012 to 2015 (PDF p. 2). The trigger a = 4, c = 20 was chosen by Sharpe on the whole sample (PDF p. 29), so it is in-sample. Avino and Lazar: pre-crisis Sharpe ratios are negative for every strategy (Exhibit 5, p. 83).
- **Cost and turnover.** Variant A uses quarterly debt and monthly equity, so turnover is moderate. The source reports no single-factor turnover. Variant B uses daily data and turns over faster.
- **Coverage.** Private issuers get no score (Section 7.1).

## 9. Open questions
1. **Naive or iterative DD.** The source does not say. Default: naive. Reason: Bharath and Shumway find naive as good or better, and it needs no solver. Run the iterative DD on a sample as a check.
2. **Debt measure and horizon.** Default: `dlcq + 0.5 dlttq`, T = 1, as Bharath and Shumway and Correia et al. use. Test T = 5 to match HY bond durations.
3. **Volatility window.** Default: 252 daily returns. Correia et al. use 12 monthly returns with zero drift. Test both.
4. **Rank pool.** Default: within rating bucket. Reason: the reader test uses it, and it removes most of the spread level. Report the full-pool result too.
5. **Avino-Lazar filter.** Source: trade the credit leg only when the credit information share is below 20% (journal p. 82). Default: leave it out of Variant B v1. Reason: a VECM per issuer needs daily spreads that sparse HY trades do not give.
