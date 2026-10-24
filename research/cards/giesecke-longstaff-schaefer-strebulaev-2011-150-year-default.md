# Giesecke, Longstaff, Schaefer, and Strebulaev (2011), "Corporate Bond Default Risk: A 150-Year Perspective"

Journal of Financial Economics 102(2), pp. 233–250. Peer-reviewed journal article. We read the open working paper: NBER Working Paper 15848, March 2010, https://www.nber.org/papers/w15848. Page and table numbers below are those of w15848. The journal version may differ in tables and numbers. Quote the journal only after a check against it.

## Claim
US non-financial corporate bond default rates, 1866–2008, cluster in long and persistent default cycles (pp. 1–2, 15–17). Lagged stock market return and stock market variance forecast the next year's default rate. Lagged credit spreads and an NBER recession indicator do not, once lagged default rates are in (pp. 22–23, Table 5). Default cycles and business cycles have a correlation of only 0.263 (p. 18). Credit spreads average about twice expected default losses, and they do not respond to realised default rates (pp. 25–26, Table 6).

## Method
**Default rate (pp. 4–7, App. B).** Annual value-weighted rate: par value of bonds of issuers that first enter distress in the year, divided by the par value of all non-financial bonds in the start-of-year snapshot. Distress covers missed coupon or principal, bondholder committee, receivership, bankruptcy, and reorganisation (p. 7, App. C).

**Forecast regression (p. 22, Table 5).** Annual data, 1866–2008, three lags of each variable, Newey-West t-statistics:

```latex
\ln(DR_t + 0.0001) = a + \sum_{k=1}^{3} b_k \ln(DR_{t-k} + 0.0001) + \sum_{k=1}^{3} c_k' x_{t-k} + \varepsilon_t
```

Intuition: ask which lagged market or macro series adds to the default rate's own past in a forecast of next year's rate.

Four groups of x (pp. 19–22):
1. Structural: annual stock market return, variance of monthly stock returns within the year, riskless long yield, and slope (high-grade corporate yield minus commercial paper yield).
2. Reduced form: credit spread (high-grade corporate yield minus government yield).
3. Macro: share of the year in an NBER recession.
4. Combined: all of the above.

**Default cycle (p. 16).** A run of years in which the default rate exceeds its 1866–2008 mean of 1.517%.

**Spread regression (p. 26, Table 6).** Credit spread on its own lags and on current and lagged default rate, stock return, and recession share.

## Data
- Default rates, 1866–2008, 143 annual observations (Table 1). Sources: Commercial and Financial Chronicle for 1866–1899 and 1966–1969, Hickman (1953, 1958, 1960) for 1900–1943, Atkinson (1967) for 1944–1965, Moody's for 1970–2008, Federal Reserve Flow of Funds for the par denominator from 1966 (App. A–B).
- Stock returns: Schwert (1990) to 1929, CRSP value-weighted after (p. 18).
- Yields: Homer and Sylla (1991) and the Federal Reserve H.15 release. Municipal yields proxy the riskless rate for 1866–1918 (p. 20).
- The spread is a high-grade spread. Mean 0.603 points, serial correlation 0.883 (Table 4). It is not a high yield spread.

## Result
- **Level and shape (Table 1).** Mean 1.517%, median 0.545%, standard deviation 2.414%, skewness 3.307, serial correlation 0.628. Post-war (1946–2008): mean 0.304%, median 0.098%, serial correlation 0.680.
- **Default cycles last longer than recessions (pp. 16–17).** 13 default cycles against 31 NBER recessions. Mean length 3.2 years against about 1.5 years. Serial correlation of the yearly indicator: 0.574 for default cycles, 0.267 for recessions.
- **Weak link to recessions.** The correlation of the yearly default-cycle and recession indicators is 0.263 (p. 18). The worst three-year default period, 1873–1875 (35.90%), had an NBER fraction of 0.72. The Depression period 1933–1935 (12.88%) had 0.08 (Table 3).
- **Own lags dominate (Table 5).** Lag 1 of the log default rate: 0.351 (t = 4.08) in the structural model, 0.483 (6.23) in the spread-only model. Lag 3: 0.351 (3.30). Adjusted R² is 0.752 (structural), 0.699 (spread), 0.708 (recession), 0.747 (combined). Most of the fit comes from the lags.
- **Stock market terms add information (Table 5, combined).** Lag 1 stock return −1.807 (t = −3.07). Lag 1 return variance +5.704 (t = 2.86). Riskless rate and slope: no lag significant at 5%.
- **Credit spread adds nothing (Table 5).** Lag 1 spread: 0.215 (t = 0.62) alone, −0.406 (−1.21) in the combined model.
- **Recession adds little (Table 5).** Lag 1 recession share: 0.538 (t = 1.81) alone, −0.260 (−0.67) combined.
- **Spread against loss (pp. 24–25).** Average spread 153.3 bp. Expected loss about 75 bp at a 50% loss rate. Ratio 2.04. Premium about 80 bp. The standard error of the mean spread is 4.18 bp.
- **Spreads ignore realised defaults (Table 6).** The current and lagged default rate coefficients are between −0.014 and 0.010, all with |t| < 0.8. The current stock return enters at −0.282 (t = −2.13) in the combined model.

## What our data says (docs/methodology.md 5.2 and 5.4, hy/macro.py, hy/groups.py, data/raw/backtest, 24 October 2026)
**What the plan holds.** Section 5.2 sets m_t = (`hy_oas`, `sloos_tightening`, `default_rate_fcst`, `pmi`, sector drivers). The planned logistic has no lag of its own event rate. Estimates E1 and E10 read the resulting case weights. The F6 phase vote in `hy/macro.py` already reads `hy_oas`, `pmi`, `default_rate`, and `sloos_tightening`.

**What this paper changes.**
1. **Put the lagged event rate in m_t.** The strongest predictor of next year's default rate is its own past at lags 1 and 3 (Table 5). Default cycles last about twice as long as recessions (p. 16). For 5.2, add the trailing share of issuers with a large EBITDA decline (the event rate itself, by sector and overall) as a covariate. This is the observable cousin of the frailty term in `duffie-eckner-horel-saita-2009-frailty.md`.
2. **Do not expect `hy_oas` to carry the physical forecast.** A lagged high-grade spread adds nothing to the default forecast (t = 0.62, combined t = −1.21). Spreads hold a premium of about 2 times expected loss and ignore realised defaults (Table 6). A high yield OAS is a different series. Still, the prior is that most of its variation is premium. In 5.2, `hy_oas` may still carry information, but test it against the lagged event rate before it enters.
3. **`pmi` and recession-type series may be weak.** The recession share is not significant once stock market terms enter (Table 5). The 0.263 correlation of default cycles and recessions (p. 18) says a growth signal alone will miss many credit cycles. Our five macro paths in 5.4 are built from GDP and CPI. So the 5.2 link from path to case weight will be weak unless it routes through a credit variable.
4. **Add equity market return and variance.** The lagged market return (t = −3.07) and variance (t = 2.86) are the only exogenous terms that survive (Table 5). Both are cheap: S&P 500 return and realised volatility. Their signs match the structural model. Note that Duffie, Saita, and Wang find the opposite sign for the S&P 500 return once firm distance to default is in (`duffie-saita-wang-2007-multi-period-default.md`). The sign at the aggregate level and the sign given firm state can differ.
5. **κ_t prior for E4 and E10.** The paper gives a spread-to-expected-loss ratio of 2.04 over 143 years (p. 25). Bharath and Shumway give a median CDS-to-naive-PD ratio of 4.14 at the firm level (`bharath-shumway-2008-merton-dd.md`). The two differ in rating mix, period, and LGD. Treat 2 to 4 as the prior range for κ_t in E4. Treat a fitted κ_t outside it as a prompt to check LGD and PD level.

**Falsifiable tests (not run).**
1. **Lagged event rate.** On `annual_ebitda.parquet` (event: EBITDA_{t+1y} < 0.8 EBITDA_t), compute the yearly event share. Fit 5.2 with and without the share at lags 1 to 3. Keep the lags if a likelihood ratio test rejects at 5% and the walk-forward log loss falls in at least 3 of 2008, 2015, 2020, and 2022.
2. **Spread against lag.** In the model with lags, report the z-statistic of `hy_oas`. Drop `hy_oas` from 5.2 (keep it in the F6 phase vote) if |z| < 2.
3. **Credit cycle against growth cycle.** Regress the yearly event share on lagged `pmi` alone and on the lagged share alone. If R² for `pmi` is less than half that of the lag, route the 5.4 macro paths into 5.2 through a credit variable, not through growth alone.

## Limits
- We read the 2010 working paper. The 2011 JFE version may differ.
- Aggregate value-weighted default rates of all bonds, mostly investment grade and mostly railroads before 1900. Not firm-level, not high yield, not EBITDA.
- The spread series is high-grade only and partly built from proxies (p. 20). It understates the average spread (p. 24).
- The pre-1900 rates for 1878–1899 count bond issues, not par (App. B).
- Three lags of six series on 143 years leaves about 120 degrees of freedom. The tests have low power to reject a weak effect.
- Bankruptcy law and market structure changed many times (Section 3.2). Pooled coefficients over 150 years may hide regime changes.

## Section touched
`docs/methodology.md` Section 5.2 (covariates of the macro logistic: add the lagged event rate and equity market terms, test `hy_oas`), Section 5.4 (route macro paths through a credit variable), and Section 7.1 (κ_t prior). Estimates E1, E4, and E10 in `hy/groups.py`. No decision page yet: the sprint that fits 5.2 should record the covariate set.
