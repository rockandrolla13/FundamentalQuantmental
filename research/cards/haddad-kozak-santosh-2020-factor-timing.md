# Haddad, Kozak and Santosh (2020), "Factor Timing"

The Review of Financial Studies, DOI 10.1093/rfs/hhaa017. Peer-reviewed. **Evidence from equities.** We read NBER Working Paper 26708, January 2020, 80 pages. Page numbers are PDF pages. The journal numbers may differ.

## Claim
The optimal factor timing portfolio equals the stochastic discount factor (p. 2). Under a limit on Sharpe ratios, only the largest principal components of the factors can have predictable returns of size (pp. 4, 15). Predict those components, and factor timing adds value out of sample (pp. 4–5).

## Method
Five steps (p. 17):
1. Start from a set of factors F.
2. Reduce them to dominant components Z by principal components.
3. Forecast each component on its own.
4. Map forecasts back to factors through their loadings.
5. Form the timing portfolio.

**Portfolio (p. 16, p. 38).**

```latex
R^{opt}_{t+1} \approx E_t[Z_{t+1}]' \Sigma^{-1}_{Z,t} Z_{t+1} \quad (10), \qquad \omega_{P.A.T.,t} = \Sigma_Z^{-1}\big[0,\ [E_t - E](PC_{1,t+1}), \ldots, [E_t - E](PC_{5,t+1})\big] \quad (15)
```

Intuition: scale each dominant bet by its forecast, and leave out small components, because large forecasts there would imply an impossible Sharpe ratio.

**Predictor (p. 21).** One per component: its own net log book-to-market.

```latex
bm_{i,t} = q_i'\, bm^{F}_t, \qquad Z_{i,t+1} = a_i + b_i\, bm_{i,t} + e_{i,t+1}
```

Intuition: a wide value spread forecasts a high return on that component. Parameters come from the first half of the sample, and out-of-sample results from the second half (pp. 19, 22). Number of components: five, from a bound on the Sharpe ratio (pp. 19–20).

## Data
50 anomaly long-short portfolios from CRSP and Compustat, January 1974 to December 2017, value-weight decile sorts, market-adjusted and rescaled with first-half estimates (pp. 18–19). Five components explain 60% of the variance (Table 1, p. 19).

## Result
- Own-valuation forecasts (Table 2, p. 23). Out-of-sample monthly R²: PC1 4.82%, PC4 3.52%, market 1.00%. t: PC1 4.31, PC4 3.74, market 1.24. Stambaugh bias on the market is nearly the size of its estimate (p. 23).
- Forecast of each anomaly by its own ratio gives half of the predictability of the restricted method (p. 5). Total out-of-sample R² is about 1% a month (p. 5).
- Portfolios (Table 6, p. 37). Out-of-sample Sharpe: factor investing 0.76, market timing 0.63, factor timing 0.87, anomaly timing 0.96, pure anomaly timing 0.77. Out-of-sample information ratio over the static portfolio: 0.42 (factor timing), 0.60 (anomaly timing), 0.59 (pure). Market timing: −0.64.
- Expected utility: 1.66 static, 2.96 factor timing (Table 6, p. 37).
- Rebalancing (Table A.5, p. 70), pure anomaly timing.

| Frequency | Sharpe | Utility | Monthly turnover | Correlation with monthly |
| --- | --- | --- | --- | --- |
| Monthly | 0.71 | 1.26 | 0.41 | 1.00 |
| Quarterly | 0.72 | 1.08 | 0.20 | 0.98 |
| Semi-annual | 0.82 | 0.88 | 0.13 | 0.92 |
| Annual | 0.79 | 0.81 | 0.08 | 0.88 |

- Loadings of size and value are pro-cyclical, and that of momentum is counter-cyclical (p. 6). SDF variance moves at business-cycle frequency, not always in recessions (p. 6).

## Limits
- Equities only. Equity factor returns have a known factor structure. Credit factor returns may differ.
- No transaction cost test. The authors say direct cost measures are needed for a firm conclusion (p. 40).
- First-half and second-half split. One sample.
- Long-short portfolios with full leverage. A credit book cannot short at that scale.
- The Sharpe bound and number of components rest on assumptions (pp. 19–20).

## Section touched
`docs/methodology.md` Section 8 (composite weights `w_{j,phase}`), `docs/decisions/2026-10-26-conviction-book.md` (layer 2 playbook, test T5), and factor F01 by name only.

## Use for the two clocks
This section is our proposal, not the source's claim.

**What the source says.** Time the few large components, not each factor. Use valuation spread as the forecast. Slow rebalancing keeps most of the benefit.

**What our data says.** Section 8 weights signals by trailing IC per phase. The conviction-book page expects several cells to be untestable, because five phases over four windows give few episodes per phase (test T5). None of the 30 factors has a result on our data.

**What we decide.** Propose a low-dimension alternative to `w_{j,phase}`.

1. Form monthly return series for the factors in `hy/factors`, net of the cost in `dickerson-nozawa-robotti-2025-factor-delays.md`.
2. Take the first three to five components on an early window. Our choice, v0.
3. Forecast each component by its own spread gap: the DTS-weighted spread of the long leg less that of the short leg, in log form. Spread replaces book-to-market as the credit value ratio.
4. Tilt family weights by the forecast, on a quarterly or slower schedule (Table A.5).

Clock use: add the clock risk-mimicking portfolios (high against low `rollover_rate_12m`) to the factor set. Test whether their premium has a value spread that forecasts it. This answers "when does the book get paid for refinancing risk?"

**Test.** Out-of-sample, on the production machine. Pass: the information ratio of the tilt over static weights is above zero after costs, in at least three of four windows, with one-way turnover below the static book plus 20 points a year. Fewer than 60 months of factor returns makes the test untestable. Our choice, v0.
