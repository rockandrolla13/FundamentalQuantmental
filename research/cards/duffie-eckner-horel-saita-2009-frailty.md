# Duffie, Eckner, Horel, and Saita (2009), "Frailty Correlated Default"

Journal of Finance 64(5), pp. 2089–2123. Peer-reviewed journal article. We read the published version from the author's site: https://www.darrellduffie.com/uploads/1/4/8/0/148007615/duffieecknerhorelsaita2009.pdf. Page numbers below are journal pages.

## Claim
Defaults of US public non-financial firms cluster in time more than observed firm and macro covariates explain (p. 2089). A common latent factor ("frailty") with an annual volatility of about 43% fixes this (p. 2102). Without it, the tail of the portfolio default count is too thin by a large margin (pp. 2105–2106). The latent factor does not improve the ranking of firms (p. 2113). It changes the level and the clustering of defaults across firms.

## Method
**Intensity with frailty (pp. 2092, 2097).** Firm covariates U_it, observed macro covariates V_t, a common latent factor Y_t, and an optional firm-level static factor Z_i:

```latex
\lambda_{it} = \exp(\beta_1 + \beta \cdot W_{it} + \eta\,Y_t), \qquad W_{it} = (1, U_{it}, V_t)   \quad (1)
```

Intuition: every firm's default rate moves up and down with one hidden common shock, on top of what the observed covariates say.

**Latent factor dynamics (p. 2098).**

```latex
dY_t = -\kappa\,Y_t\,dt + dB_t, \qquad Y_0 = 0   \quad (4)
```

Intuition: the hidden shock mean-reverts. η sets its size and κ sets how fast it fades.

**Likelihood (p. 2098).** The likelihood integrates the complete-data likelihood over the path density of Y:

```latex
L(\gamma, \theta \mid W, D) = L(\gamma \mid W)\; E\left[ \prod_{i=1}^{m} e^{-\sum_{t} \lambda_{it}\Delta t} \prod_{t} \big[ D_{it}\lambda_{it}\Delta t + (1 - D_{it}) \big] \;\middle|\; W, D \right]   \quad (3)
```

Intuition: the data must be likely on average over all hidden paths, so years with too many or too few defaults pull the hidden path.

Estimation: Monte Carlo EM with a Gibbs sampler for the path of Y (App. A–B). Filtering for E(ηY_t | F_t) uses the forward-backward algorithm (p. 2103).

**Model comparison (p. 2108).** Twice the log Bayes factor of frailty against no frailty. Above 10 counts as very strong evidence (Kass and Raftery 1995).

**Quantile test (pp. 2113–2114).** At the start of each year 1980–2003, compute the model distribution of the number of defaults in the next 12 months among active firms. Record the quantile of the realised count. A correct model gives quantiles near uniform with no serial correlation.

## Data
- 2,793 US public non-financial firms, 402,434 firm-months, January 1979 to March 2004. Data used to December 2003 (p. 2099).
- Exits (Table I, p. 2100): 176 bankruptcies, 320 other defaults, 1,047 mergers or acquisitions, 671 other exits.
- Covariates (pp. 2100–2101): distance to default (DD), trailing 1-year own stock return, 3-month T-bill rate, trailing 1-year S&P 500 return. The same data as Duffie, Saita, and Wang (2007), with a few more exits found.

## Result
- **Frailty fit (Table II, p. 2102).** Constant −1.029 (0.201). DD −1.201 (0.037). Own return −0.646 (0.076). 3-month T-bill −0.255 (0.033). S&P 500 return +1.556 (0.300). η = 0.125 (0.017) a month, about 43.3% a year. κ = 0.018 (0.004) a month.
- **No-frailty fit (Table III, p. 2103).** Constant −2.093. DD −1.200. Own return −0.681. T-bill −0.106 (0.034). S&P 500 +1.481 (0.997), not significant. The firm coefficients barely move. The T-bill coefficient more than doubles with frailty.
- **One standard deviation of DD.** A negative one-standard-deviation shock to DD raises the intensity by about e^{1.2} − 1 ≈ 230% (p. 2102).
- **Size of the hidden factor.** The frailty multiplier in 2001 is about e^{1.1}, about three times its 1995 level (p. 2103). Defaults ran above the covariate model in 1986–1991 and below it in the mid-1990s. Trough to peak, the factor moves the average default rate by a factor of two or more (p. 2093).
- **Bayes factor.** Twice the log Bayes factor is 22.6, very strong evidence for frailty (p. 2108).
- **Tail of the 5-year count, 1,813 firms active in January 1998 (pp. 2105–2106).** With frailty: 95th percentile 216, 99th 265 defaults. Independent frailty: 144 and 150. Common start but independent shocks: 180 and 204. Realised: 195, near the 91st percentile of the frailty model. The models without a common factor give almost zero probability to more than 200 defaults.
- **Parameter uncertainty (p. 2110).** The 99th percentile rises from 265 to 275 when the posterior uncertainty of η and κ enters. κ is hard to pin down.
- **Trailing default rate is not a substitute (Table IV, pp. 2112–2113).** Without frailty, the trailing 1-year default rate has a coefficient of 7.154 (1.000). A 1 point rise in the trailing rate raises every intensity by about 7.1%. The T-bill coefficient falls to −0.086 (0.135), not significant. The quantile test still rejects this model.
- **Quantile test (pp. 2113–2114, Figure 9).** Without frailty, the realised count sits below the 1st percentile in 1994 and above the 99.9th percentile in 1990 and 2001. The yearly quantiles are serially correlated: p = 0.004 without frailty, p = 0.019 with the trailing default rate, p = 0.62 with frailty.
- **Ranking does not change.** Accuracy ratios with and without frailty are "essentially the same" (p. 2113). Firm covariates, DD above all, do the sorting.
- **Rejected macro covariates (p. 2101).** GDP growth, industrial production growth, the BBB-AAA yield spread, industry-average DD, and firm size are "at best marginally significant" given the four basic covariates.

## What our data says (docs/methodology.md 5.2 and 5.4, hy/macro.py, hy/groups.py, data/raw/backtest, 24 October 2026)
**What the plan holds.** Section 5.2 is a pooled logistic σ(θ_0 + θ'm_t + θ_sector) with no time effect beyond m_t. Its fitted p sets the downside weight of every case in Section 5.4. Estimate E1 "Weighted cases and stories" reads those weights. Estimate E10 "Excess over cash" reads μ = Σ q X in `hy/alpha.py`, so it moves with the same weights. CLAUDE.md asks for a near-uniform probability integral transform (PIT) and for calibration by cycle phase.

**What this paper changes.**
1. **Observed macro will not absorb the year effect.** Even with the best firm covariates and four macro series, a common hidden factor with about 43% annual volatility remains (Table II). Our m_t is coarser than theirs for firm events. Expect the 5.2 residual to carry a year effect. A pooled logistic without one will give yearly event counts that are too tight around the forecast. That is the failure in Figure 9.
2. **Two candidate fixes, from cheap to full.**
   - A year random intercept: σ(θ_0 + θ'm_t + θ_sector + u_t), u_t ~ N(0, τ²). Integrate u_t out when forecasting. This is the static form of frailty.
   - An AR(1) latent year effect, u_t = φ u_{t−1} + e_t, filtered on the yearly event counts. This is the paper's dynamic form. It lets the current year's realised decline rate update next year's p. κ = 0.018 a month means a half-life of about 3 years.
3. **`default_rate` in m_t helps but does not replace the latent term.** The trailing default rate is significant (7.154 per unit, Table IV) but the quantile test still rejects. Keep `default_rate` (and `default_rate_fcst`) in m_t. Do not treat it as the fix for clustering.
4. **Ranking and level are separate jobs.** Frailty does not change accuracy ratios (p. 2113). So the 5.2 test of AUC and the 5.2 test of calibration are separate tests. The rank job needs firm covariates (see `duffie-saita-wang-2007-multi-period-default.md`). The level job needs the latent year term.
5. **E1 and E10 at the book level.** With a latent common factor, the downside weights of all issuers move together more than m_t implies. The mean of E1 per issuer changes little. The spread of E10 across the book, and any tail feature such as `lev_peak_down` or `p_liq_short_h` summed over issuers, is too narrow without it. The book-level risk report should draw u_t once per scenario, not once per issuer.
6. **Macro signs again.** The T-bill coefficient doubles once frailty enters (−0.106 to −0.255). The BBB-AAA spread is not significant given DD. So the sign and size of `hy_oas` in 5.2 may depend on whether a latent year term is present. Fix the specification before a monotone-sign test asserts a sign.

**Falsifiable tests (not run).**
1. **Yearly count PIT.** Fit the 5.2 logistic on `data/raw/backtest/annual_ebitda.parquet` (event: EBITDA_{t+1y} < 0.8 EBITDA_t). Walk forward by year. For each year, compute the distribution of the event count as a sum of independent Bernoulli(p_i). Record the quantile of the realised count. Reject the pooled form if a Kolmogorov-Smirnov test rejects uniformity at 5% or the lag-1 autocorrelation of the quantiles is significant at 5%.
2. **Random intercept.** Refit with a year random intercept. Keep it if the likelihood ratio test of τ² = 0 rejects at 5% (half chi-square) and test 1 then passes.
3. **Cycle years.** Report the quantile of the realised count in 2008, 2015, 2020, and 2022 under both forms. The pooled form fails if any of the four sits outside the 1% to 99% band.

## Limits
- Defaults of listed US firms, 1979–2003. The paper does not study EBITDA declines. The transfer of the frailty result to an operating event is a hypothesis, which test 1 checks.
- One common factor only. The authors did not try sector frailty because the data are too sparse (pp. 2096, 2099). Our θ_sector is fixed, not latent.
- κ and the size of firm heterogeneity Z_i are poorly identified (pp. 2109–2110).
- Frailty can absorb a wrong functional form. The authors test a non-parametric DD response in the Internet Appendix and find it roughly linear (pp. 2108–2109). We did not read the Internet Appendix.
- The doubly-stochastic assumption still holds on the enlarged information set, so contagion (one default causes another) is outside the model (p. 2101).

## Section touched
`docs/methodology.md` Section 5.2 (macro conditioning of the scenario weights: add a year effect), Section 5.4 (case weights under paths: draw the common term once per scenario), and Section 11 (calibration by cycle phase, PIT). Estimates E1 and E10 in `hy/groups.py`. No decision page yet: the sprint that fits 5.2 should record the choice between pooled, random intercept, and AR(1) latent term.
