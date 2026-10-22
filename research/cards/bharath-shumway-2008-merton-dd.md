# Bharath and Shumway (2008), "Forecasting Default with the Merton Distance to Default Model"

Review of Financial Studies 21(3), pp. 1339–1369. Peer-reviewed journal article. Page numbers below are journal pages, with the PDF page of the JSTOR copy in brackets (PDF page = journal page − 1337).

## Claim
The Merton distance to default (DD) is a useful default predictor, but its probability is not a sufficient statistic for default (p. 1339 [2]). The value comes from the functional form, not from the solution of the Merton model (p. 1342 [5], p. 1367 [30]). A "naive" DD with no equation solved forecasts as well as the iterative DD, or slightly better (p. 1339 [2]). Past excess return and net income to total assets add information that the DD omits (p. 1357 [20]).

## Method
Three hypotheses (p. 1340 [3]). H1: the Merton probability is a sufficient statistic. H2: the z-score functional form adds information beyond its inputs. H3: the solution of the Merton model adds information. Five tests: Cox hazard models, out-of-sample decile sorts, alternative DD variants, CDS regressions, and bond spread regressions (p. 1341 [4]).

**Iterative Merton DD (pp. 1343–1345 [6–8]).** Firm value V follows dV = μV dt + σ_V V dW. The firm has one zero-coupon bond with face value F, due at T. Equity is a call on V:

```latex
E = V\,N(d_1) - e^{-rT} F\,N(d_2), \qquad d_1 = \frac{\ln(V/F) + (r + 0.5\sigma_V^2)T}{\sigma_V\sqrt{T}}, \qquad d_2 = d_1 - \sigma_V\sqrt{T}   \quad (2,3)
\sigma_E = \frac{V}{E}\,N(d_1)\,\sigma_V   \quad (5)
DD = \frac{\ln(V/F) + (\mu - 0.5\sigma_V^2)T}{\sigma_V\sqrt{T}}, \qquad \pi_{Merton} = N(-DD)   \quad (6,7)
```

Inputs: E is market equity (month-end price times shares outstanding). F is debt in current liabilities plus one half of long-term debt (Compustat items 45 and 51). r is the risk-free rate. T = 1 year. σ_E is the annualised standard deviation of the prior year of stock returns. μ is the expected annual return on assets. Intuition: DD counts the standard deviations of asset value between today and the default point.

Solution (p. 1345 [8]). The authors do not solve (2) and (5) jointly, because market leverage moves too much for (5). They follow Crosbie and Bohn (2003) and Vassalou and Xing (2004):
1. Start with σ_V = σ_E · E/(E + F).
2. Invert (2) for V on each day of the prior year.
3. Compute daily log returns on V. Re-estimate σ_V and μ from them.
4. Repeat until adjacent σ_V values differ by less than 10⁻³.

**Naive DD (pp. 1347–1348 [10–11]).** No equation is solved, and no constant is estimated or optimised (p. 1347 [10]).

```latex
\text{naive } D = F   \quad (8)
\text{naive } \sigma_D = 0.05 + 0.25\,\sigma_E   \quad (9)
\text{naive } \sigma_V = \frac{E}{E+F}\,\sigma_E + \frac{F}{E+F}\,(0.05 + 0.25\,\sigma_E)   \quad (10)
\text{naive } \mu = r_{i,t-1}   \quad (11)
\text{naive } DD = \frac{\ln[(E+F)/F] + (r_{i,t-1} - 0.5\,\text{naive }\sigma_V^2)\,T}{\text{naive }\sigma_V\sqrt{T}}   \quad (12)
\pi_{naive} = N(-\text{naive } DD)   \quad (13)
```

Inputs: the market value of debt is set to its face value F. The 5 points in (9) stand for term structure volatility. The 25% of σ_E stands for the default risk in the debt. r_{i,t-1} is the firm's stock return over the previous year. Intuition: a value-weighted mix of equity and debt volatility replaces the solved σ_V. The past stock return replaces the solved μ.

**Hazard model (p. 1349 [12]).** Cox proportional hazard with time-varying covariates:

```latex
\lambda(t) = \phi(t)\,\exp(x(t)'\beta)   \quad (14)
```

φ(t) is an unrestricted baseline hazard. Specifications (Table 3, p. 1355 [18]):

| Model | Covariates |
| --- | --- |
| 1 | π_Merton |
| 2 | π_naive |
| 3 | π_Merton, π_naive |
| 4 | ln E, ln F, 1/σ_E, r_{i,t-1} − r_{m,t-1} |
| 5 | Model 4 + π_naive |
| 6 | Model 5 + π_Merton + NI/TA |
| 7 | Model 6 without π_Merton |

r_{m,t-1} is the prior-year value-weighted CRSP NYSE/AMEX index return. NI/TA is net income over total assets.

**Out-of-sample test (p. 1356 [19]).** Each quarter, sort firms into deciles of a predictor. Count the share of defaults in each decile at the start of the default quarter. In Panel B, re-fit Models 4 to 7 each quarter on data to that quarter only (p. 1358 [21]).

## Data
- Compustat quarterly and CRSP daily, NYSE, AMEX, and NASDAQ, 1980–2003. Financial firms (SIC 6021, 6022, 6029, 6035, 6036) are out (p. 1351 [14]).
- Defaults: Altman default database for 1980–2000, Moody's list for 2001–2003. 1,449 defaults (p. 1351 [14]).
- Panel: 1,016,552 firm-months, 15,018 firms (Table 1, p. 1352 [15], Table 3).
- Out of sample: 350,662 firm-quarters, 1980–2003. Hazard-model comparison: 226,604 firm-quarters and 847 defaults, 1991–2003 (Table 4).
- Option-implied σ_E: OptionMetrics, 1996–2003, 101,201 firm-months, 88 defaults (p. 1359 [22]).
- CDS: credittrade.com, December 1998 to July 2003, 3,833 firm-months. Risk-neutral LGD is 75% (pp. 1351, 1361 [14, 24]).
- Bonds: Lehman (Warga) database, 1980–1997, trader-priced, no options, no Aaa. 61,776 bond-months. Mean spread 108 bp (pp. 1363–1366 [26–29]).
- All inputs are winsorised at the 1st and 99th percentiles. The default probabilities are not winsorised (p. 1352 [15]).

The source is inconsistent on r. The text says the 1-year Treasury constant maturity rate (p. 1351 [14]). The Table 1 and Table 7 notes say the 3-month T-bill rate.

## Result
- **Naive and iterative DD agree.** Correlation of π_Merton and π_naive is 0.8642. Correlation of σ_V and naive σ_V is 0.8748 (Table 1, p. 1352 [15]). Mean π_Merton is 10.95%, mean π_naive is 8.95%.
- **Against Moody's KMV, the naive form does as well.** For 80 firms in August 2000, rank correlation with the KMV EDF is 0.788 (π_Merton) and 0.786 (π_naive). For asset volatility it is 0.574 (iterative) and 0.853 (naive) (Table 2, p. 1354 [17]).
- **Hazard models (Table 3).** Univariate coefficients: π_Merton 3.635 (s.e. 0.068), π_naive 4.011 (0.067). In Model 3 both stay significant, so H1 fails. In Model 5, π_naive is 1.675 (0.149) beside its own inputs, so H2 holds. In Model 6, π_Merton is 0.230 (0.164) and not significant, while π_naive is 1.366 (0.178), so H3 fails. NI/TA is −0.044 (0.002).
- **Out-of-sample deciles (Table 4, Panel A, 1980–2003).** Top-decile capture: π_Merton 64.9%, π_naive 65.8%, market equity 35.7%, past excess return 44.4%, NI/TA 46.8%. Top-quintile capture: 80.0% and 80.1%. Deciles 6–10 hold 6.5% (π_Merton) and 6.7% (π_naive) of defaults.
- **Out-of-sample against fitted hazards (Table 4, Panel B, 1991–2003).** Top-decile capture: π_Merton 69.4%, π_naive 70.0%, Model 4 68.8%, Model 5 70.4%, Model 6 75.6%, Model 7 75.8%. Deciles 6–10 hold 5.7% for π_naive and 8.5% for Model 4 (p. 1358 [21]).
- **No AUC.** The paper reports no AUC or accuracy ratio. Decile capture is its only out-of-sample measure.
- **Rough level (footnote 10, p. 1356 [19]).** A firm in the top π_Merton decile has a 2.7% chance to default in the next quarter.
- **Variants (Table 5, pp. 1359–1361 [22–24]).** With μ = r, top-decile capture falls to 60.0% from almost 65%. So the drift estimate matters. A joint solution of (2) and (5) beats the iterative one but does not dominate π_naive. Implied σ_E improves capture, but only 88 defaults support it.
- **CDS (Table 6, pp. 1361–1363 [24–26]).** Correlation with the CDS-implied PD is 0.52 for π_naive and 0.38 for π_Merton. Log CDS spread on log PD: R² 0.38 (naive) and 0.26 (Merton). With both, π_Merton loses significance. The ratio π_CDS / π_naive has median 4.14 and mean 5.54. The ratio π_CDS / π_Merton has median 3.73 and mean 5.09. The lowest quartile of the ratio sits below 1, counter to theory.
- **Bond spreads (Table 7, pp. 1364–1367 [27–30]).** With rating, year, and industry dummies, both PDs are significant but small. The π_naive coefficient of 0.5 means a rise from 0% to 5% adds 2.5 bp. In a hazard model with the bond spread (571 firms, 58 defaults), the spread is significant and π_naive stays significant (2.284 and 2.316).

## What our data says (hy/fairspread.py, hy/groups.py, data/raw/backtest, 22 October 2026)
**What we hold.** The repo has no DD code. A grep for "merton", "distance to default", and "naive DD" in `hy/` finds nothing. Section 7.1 already names `dd_equity` as feature β₁₀ of the logit PD. `PDModel` in `hy/fairspread.py` accepts `dd_equity` and fills a missing value with the training median. No module produces `dd_equity` yet. Estimate E4 "Default the price assumes" has weight 0.00 in `hy/groups.py`, suspended until κ_t is fitted (mapping C2). Today the PD for each issuer comes from its scenario cases.

**Inputs on disk.**
- `data/raw/backtest/equity_monthly.parquet`: monthly total return `ret`, 383,338 rows, 2,575 gvkeys, January 2007 to September 2026. Each row has `available_at`.
- `data/raw/backtest/leverage_full.parquet`: quarterly total `debt`, 311,116 rows, 2,313 gvkeys, `datadate` May 2007 to June 2026. Each row has `available_at`.
- 2,094 gvkeys appear in both files.
- Market equity E: comp.fundq `prccq × cshoq`. We have not pulled it into a backtest file yet.
- `data/raw/backtest/sp_ratings.parquet`: 141 gvkeys carry an S&P rating of D or SD between January 2007 and February 2017. The series ends in February 2017, so it covers 2008 and 2015 but not 2020 or 2022.

**What we could build.** A naive DD per issuer per month, with T = 1:
1. σ_E: standard deviation of the prior 12 monthly returns, times √12. The paper uses one year of daily returns, so our estimate is noisier.
2. F: `dlcq + 0.5 × dlttq`. `leverage_full` holds only total debt. `hy/sources/compustat_pit.py` already maps `dlcq` and `dlttq`, so the split is one pull away.
3. E: `prccq × cshoq` at the last quarter end. Roll it forward each month with the monthly return, or pull month-end price and shares.
4. r_{i,t-1}: the compounded prior 12 monthly returns. Our `ret` is a total return, so it includes dividends.
5. `available_at` of the DD row: the latest `available_at` of its inputs. The no-look-ahead test then covers it with no change.

**How it serves E4 and κ_t.**
- The paper shows the normal CDF gives poor levels (mean π_naive 8.95%) but good ranks (p. 1346 [9], footnote 5). So use naive DD as the `dd_equity` rank feature. Let the bucket recalibration in `PDModel` set the level against the agency table.
- That recalibrated PD is a point-in-time physical PD from public data. E4 then needs the spread-implied PD and κ_t(bucket) = spread hazard divided by physical hazard, with the same LGD in both.
- The paper gives a prior for that ratio. π_CDS / π_naive has median 4.14 at a 75% risk-neutral LGD (Table 6). Our fitted κ_t should land in the same order of magnitude. If it does not, check the LGD or the PD level first.
- Cross-check: rank issuers each month by naive DD and by scenario-case PD. Flag issuers in the top naive-DD decile whose scenario PD sits in the bottom half. The paper's Enron case shows the DD lags when the stock price is too high (p. 1346 [9]). So a flag is a prompt to review, not a verdict.

**Falsifiable tests on our panel.**
1. **Default capture.** For the 141 D or SD issuers, sort the rated universe each quarter by π_naive. Measure top-decile capture at the start of the default quarter. Compare it with a sort on `leverage` and on market equity alone. The paper's 65.8% comes from all listed firms. Our universe is rated issuers only, so compare with these in-sample baselines, not with 65.8%. Reject naive DD as a PD input if it does not beat the leverage sort.
2. **Hazard increment.** Fit Model 5 of Table 3 on our 2007–2017 panel. Keep naive DD if π_naive stays significant beside ln E, ln F, 1/σ_E, and the excess return. Add `leverage` and test it again.
3. **Rank IC beyond spread.** Each month, regress π_naive on log spread and rating bucket. Take the residual. Compute its rank IC with forward bond excess return at 3, 6, and 12 months. The expected sign is negative: a high PD the spread does not price predicts underperformance. Pass rule from CLAUDE.md: the IC has the right sign after costs in at least three of 2008, 2015, 2020, and 2022.
4. **Naive against iterative.** On a sample of issuers, solve the iterative DD with monthly data. Reject the claim "naive is enough for us" if the iterative DD wins test 1 or test 3 by a material margin.

## Limits
- US listed non-financial firms, 1980–2003. Default definitions follow the Altman database and Moody's, not the agency D or SD rating we hold.
- The paper uses daily returns for σ_E. We hold monthly returns. The effect of that change on DD rank is not tested in the paper.
- The naive constants 0.05 and 0.25 are not estimated. The authors call the choice of r_{i,t-1} for μ "arbitrary at best" (p. 1348 [11]).
- One horizon only (T = 1). No AUC, no Brier score, no calibration table. Decile capture measures rank, not level.
- The bond sample ends in 1997, has a mean spread of 108 bp, and leaves out callable bonds. It says little about high yield bonds, which are mostly callable.
- The CDS sample is short (3,833 firm-months) and uses a fixed 75% LGD.
- The DD needs a listed equity. Private high yield issuers get no value, as Section 7.1 already notes.
- pdftotext garbled Equations (10) and (12) and Table 5 Panel C. Equations (10) and (12) above are rebuilt from the legible fragments. Table 5 values other than 60.0% are not quoted here.

## Section touched
`docs/methodology.md` Section 7 (fair spread model) and Section 7.1 (structural anchor: expected loss, feature `dd_equity`, and κ_t). Estimate E4 "Default the price assumes" in `hy/groups.py`. `PDModel` in `hy/fairspread.py`. No decision page yet: a sprint that builds naive DD and runs the tests above should add one.
