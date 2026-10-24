# Greenwood and Hanson (2013), "Issuer Quality and Corporate Bond Returns"

Review of Financial Studies 26(6), pp. 1483–1525. Peer-reviewed journal article. This card reads the author manuscript of February 2013 from the Harvard DASH repository. Page numbers below are the manuscript pages: text on pp. 1–37, tables on pp. 44–53. The Internet Appendix is not in the text file and was not read. Check any number against the journal pages before it enters a decision page.

## Claim
The credit quality of firms that issue debt falls during credit booms, and this fall forecasts low excess returns on corporate bonds (abstract, p. 1). Quality forecasts better than the aggregate amount of debt issued (pp. 20–22). The signal is strongest for high yield bonds and weaker for BBB and AAA bonds (p. 17). It forecasts returns at 1 to 3 years, with most power in the first two years (p. 17). It also forecasts wider BBB spreads and higher high yield default rates (p. 25). The authors do not claim that issuer quality causes the low returns. They claim that firms issue more when credit is cheap (p. 1).

## Method
**Spread model (p. 6).** The spread of type-θ firms is expected default loss plus a loading β_θ on a market-wide expected excess return δ_t. The expected excess return is the loading times δ_t.

```latex
s_{\theta t} = \lambda_{\theta t} + \beta_\theta \delta_t, \qquad E_t[rx_{\theta,t+1}] = \beta_\theta \delta_t   \quad (1,2)
```

Intuition: a spread is low either because default is unlikely or because the expected return is low. The spread alone cannot tell which. Firms of high default risk have β_H > β_L, so their debt issuance reacts more to δ_t (pp. 6–7). The difference in issuance between high and low risk firms removes the common target-leverage shock (p. 8).

**Issuer quality measure (pp. 9–10).** Each year, sort firms by net debt issuance scaled by lagged assets. Take the top and bottom NYSE quintiles. Compare the average Merton expected default frequency (EDF) decile of the two groups.

```latex
ISS^{EDF}_t = \frac{\sum_i \mathbf{1}[\text{High } d_{it}]\, EDF_{it}}{N^{High}_t} - \frac{\sum_i \mathbf{1}[\text{Low } d_{it}]\, EDF_{it}}{N^{Low}_t}   \quad (8)
```

A value of 1 means high issuers sit on average one decile higher in default risk than low issuers (p. 10). The EDF is the naive Merton measure of Bharath and Shumway (2008): face value of debt is short-term debt plus half of long-term debt, drift is the prior 12-month stock return, and asset volatility is `E/(E+F) σ_E + F/(E+F) (0.05 + 0.25 σ_E)`, where σ_E is the annualised volatility of monthly stock returns over the prior 12 months (footnote 6, p. 10).

**High yield share (p. 13).** HYS_t is the dollar share of non-financial corporate bond issuance rated high yield by Moody's. The regressions use log(HYS).

**Forecast regression (pp. 16, 19).** Cumulative k-year log excess return on the high yield index, with Newey–West errors allowing k lags.

```latex
rx^{HY}_{t \to t+k} = a + b\,X_t + u_{t+k}   \quad (10)
rx^{HY}_{t \to t+k} = a + b\,X_t + c\,(y^{G}_{L}-y^{G}_{S})_t + d\,y^{G}_{S,t} + e\,(y^{BBB}_{L}-y^{G}_{L})_t + f\,rx^{HY}_t + u_{t+k}   \quad (11)
```

Intuition: the second form asks whether issuer quality adds to the term spread, the short rate, the BBB credit spread, and the lagged return. Excess return is the log return minus the log return on intermediate Treasuries, which have about 5 years of maturity, close to the index duration of just under 5 years (pp. 15–16).

**Out-of-sample R² (p. 28).** Expanding window with 20 years of data for the first fit, first forecast for 1973 (footnote 25, p. 29).

```latex
R^2_{OS} = 1 - \frac{\sum_{t=s}^{T}(rx_t - \widehat{rx}_t)^2}{\sum_{t=s}^{T}(rx_t - \overline{rx}_t)^2}   \quad (12)
```

## Data
- Firm data: Compustat and CRSP non-financial firms, 1962–2008. The mean EDF is 0.06 and the median is about 0 (Table 1, p. 44).
- ISS^EDF: 1962–2008, mean 0.25, standard deviation 0.48 (Table 1 Panel B, p. 44). The series is in Table 2 (p. 46).
- HYS: 1926–2008. Sources: Hickman (1960) and Atkinson (1967) to 1965, hand-collected Moody's Bond Survey for 1966–1982, Mergent FISD for 1983–2008. Mean 0.18, standard deviation 0.15 (spliced series). The correlation of HYS and ISS^EDF is 0.47 before 1982 and 0.58 after (p. 13).
- High yield returns: Morningstar/Ibbotson 1927–1982 and Barclays Capital (formerly Lehman) from 1983. The index return includes the price return at default (footnote 15, p. 16). BBB and AAA returns: Ibbotson to 1989 and Barclays from 1990 (pp. 15–16).
- One-year excess high yield log return: mean 0.45%, standard deviation 13.10%. Two-year: mean −0.23%, standard deviation 14.34% (Table 1 Panel D, p. 45). High yield default rate: mean 3.36%, standard deviation 3.10%.
- Controls: term spread, short rate, BBB less government yield spread, lagged excess return, output gap, industrial production, consumption growth, recession dummy, the Lettau–Ludvigson cay, eight Ludvigson–Ng factors, and the Cochrane–Piazzesi factor (pp. 15, 23).

## Result
- **Univariate forecast (Table 3, p. 47).** High yield excess return on ISS^EDF, 1962–2008. One year: b = −9.534 (t −3.97), R² 0.12. Two years: −15.254 (t −5.29), R² 0.26. Three years: −17.301 (t −3.68), R² 0.29. One standard deviation of ISS (0.47 decile) lowers the next-year excess return by 4.5%, about 0.35 standard deviations (p. 17). The simple correlation of ISS with the following two-year excess return is −0.51 (p. 16).
- **Modern sample (Table 3).** 1983–2008: −11.132 (t −2.64, R² 0.10), −21.021 (t −5.20, R² 0.32), −27.966 (t −6.19, R² 0.48).
- **HYS (Table 3).** Full sample 1926–2008: −1.517 (t −1.77, R² 0.02) at one year. 1983–2008: −11.483 (t −2.77, R² 0.15), −14.264 (t −4.23), −17.798 (t −5.76, R² 0.28). The 1933 observation (HYS 0.639) weakens the full-sample result (p. 15).
- **Rating gradient (Table 3).** ISS coefficient at one year: high yield −9.534, BBB −5.311, AAA −2.278. At two years: −15.254, −6.945, −3.321. At three years the AAA t-statistic is −1.50. The authors read this as lower-rated bonds loading more on the common credit factor (p. 17).
- **Controls (Table 4, p. 48).** One year, 1962–2008: the ISS coefficient moves from −9.534 to −7.636 (t −3.45) with term spread and short rate, −8.617 with credit spread and lagged return, −6.282 (t −2.40) with all. Two years: −11.022, −18.052, −13.890. Three years: −14.214, −21.697, −19.343. For 1983–2008 at one year the coefficient is −6.120 (t −1.07) with controls, −4.492 (t −0.85) with all, and not significant. At two and three years it stays large: −15.865 (t −2.49) and −35.669 (t −7.09) with all controls. The credit spread coefficient is not significant in most columns.
- **Quantity against quality (Table 5, p. 49).** Two-year high yield return. Aggregate debt growth: −5.212 (t −3.97), R² 0.13. With ISS in the same regression it falls to −2.433 (t −1.49) while ISS stays at −12.978 (t −3.78). By EDF quintile of the debt growing, one standard deviation of debt growth at the safest quintile lowers the two-year return by 3.47 points (t −2.04, R² 0.06) and at the riskiest quintile by 7.09 points (t −3.76, R² 0.24). In a race of quintile 1 against quintile 5, only quintile 5 survives (−6.631, t −3.09).
- **Robustness (Table 6, p. 50).** Baseline −15.254 (t −5.29). 1952–2008: −9.403 (t −3.03). Pre-1983: −8.994 (t −3.90). 1983 onward: −21.021 (t −5.20). Dropping 2008–2009: −14.556. Output gap: −13.592. Leads and lags of macro variables: −11.834 (t −2.67). Eight macro factors: −12.303. Aggregate corporate leverage: −15.252. Contemporaneous market excess return: −13.409 (t −5.32). Fama–French factors: −11.011 (t −4.88). Alternate quality measures, univariate: Shumway distress −18.751 (t −3.60), interest coverage −15.318 (t −3.41), leverage −7.804 (t −2.42), size −10.967 (t −1.71). Six of seven alternate characteristics are significant (p. 24). Short-term debt issuers give −3.531 (t −0.86), long-term debt issuers −18.663 (t −4.28).
- **Symmetry (footnote 16, p. 17).** Rises of ISS give b+ = −12.786 (t −2.30). Falls give b− = −17.008 (t −3.24). The difference is not significant.
- **Spreads and defaults (Table 7, p. 51).** ISS forecasts a rise in the BBB spread. One-year change: 0.609 (t 4.07) alone and 0.237 (t 1.45) with all controls. Two-year change: 0.925 (t 5.33) alone and 0.419 (t 2.14) with all controls. The text calls ISS a strong univariate forecaster that stays significant with controls (p. 25). It forecasts the high yield default rate in years t+1, t+2, t+3. Coefficient, univariate and with controls: 1.502 (t 2.48) and 1.352 (t 2.39) for t+1, 2.990 (t 3.53) and 3.322 (t 4.62) for t+2, 2.488 (t 1.78) and 3.269 (t 1.91) for t+3. The pdftotext layout of this table is ambiguous, so the column pairing is read from the header and row counts.
- **Negative expected returns (p. 28).** ISS forecast significantly negative three-year cumulative excess returns in 14 years since 1962, and all but one were followed by negative realised returns. At one and two years it gave 7 and 14 such years. The null that expected returns are never negative is strongly rejected in the Internet Appendix.
- **Out of sample (p. 29).** R²_OS is 8.3% at one year, 16.9% at two years, 10.5% at three years. The annual Sharpe ratio of the high yield excess return is 4%. The authors say an R² of 8% would let a mean-variance investor raise the expected excess return by a factor of 54 (p. 29, footnote 26).
- **Not an equity signal (p. 29).** ISS is largely disconnected from equity predictors such as the dividend yield and cay. It has little power for excess stock returns. It has some negative power for HML and SMB.
- **Beta of the index to equity (p. 26).** High values of ISS go with higher future loadings of the high yield excess return on the market excess return. The text gives no coefficient.
- **Intermediaries (Table 8, pp. 30–32).** Controls for insurer, broker-dealer and bank balance sheets, lagged bank stock returns, and loan loss provisions barely change the ISS coefficient. For example with insurer capital the coefficient is −13.102 (t −3.41) and −14.251 (t −3.69).
- **Reach for yield and extrapolation (Table 9, pp. 32–35).** ISS rises when the term spread or the short rate is low or has fallen. The term spread and T-bill yield alone explain 44% of the level of ISS (36% in changes). ISS is high after low default rates and high past high yield returns. These two explain 65% of the two-year change in ISS (p. 35). Instrumenting ISS with past default rates gives b = −18.503 (t −4.93), against OLS −15.254 (footnote 30, p. 35).
- **Cost of credit (p. 18).** The three-year coefficient divided by the index duration of 5 years gives −3.46. One standard deviation of ISS (0.48) then equals a 1.66 point yearly fall in the cost of credit for high yield firms. For BBB firms it is 0.63 points.
- **Link to bank standards (footnote 12, p. 14).** Changes in ISS have a correlation of −0.51 with the SLOOS measure of tighter bank lending standards, in 1967–1983 and 1990–2008.

## What our data says
This section is our proposal. The paper tests only index-level returns, spreads, and default rates. It has no issuer-level result, no EBITDA, and no sample after 2008.

**Link 2: the downside-weight logistic (Section 5.2).**
- Signal: issuer quality adds a different fact from the spread level. The paper says a spread is low either because default is unlikely or because the expected return is low (p. 6). Table 4 shows the BBB spread adds little to a forecast of high yield returns. So `hy_oas` alone is a weak input to a downside weight. Add a credit-quality-of-issuers input.
- Sign: high ISS or high junk share goes with higher default rates in years t+1 to t+3 (Table 7). Expected sign in the logistic: positive.
- Size: 1.4 to 3.3 points of high yield default rate per unit of ISS at t+1 to t+3. The mean default rate is 3.36%. One unit of ISS is about two standard deviations. The sizes are for the index, not for an EBITDA decline.
- Horizon: the return signal peaks at two to three years (R² 0.26 and 0.29 in Table 3). The default signal has the largest coefficient at t+2 (Table 7). A four-quarter logistic may sit on the front edge. Test an eight-quarter horizon.
- Rating gradient: the effect is largest for high yield, about 1.8 times the BBB coefficient at one year and 2.2 times at two years (Table 3). This supports a rating interaction.

**Link 1: path probabilities (Sections 5.4, F6 phase prior).** High ISS and low past defaults point to late-cycle risk in 1 to 3 years. The paper does not map this to named GDP and CPI paths, so any mapping is our own rule.

**Link 3: the growth shift (Sections 5.2, 9.2).** The paper does not test sales or growth. It supports no value for `beta_sector`. Do not cite it for Link 3.

**HY-index hedge (Section 9.2).** This is the most direct use.
- The expected excess return of the high yield index changes with ISS. A rise of one standard deviation lowers the next-year excess return by 4.5 points and the two-year excess return by about 7 points (0.47 × 15.254). The loading of the index on the stock market rises when ISS is high (p. 26). Both facts argue for a larger hedge when ISS is high, and the second is the one that sets the hedge ratio.
- The paper does not test a hedge ratio. It does not split the high yield index by rating, so it cannot set a ratio for a single B or BB bond.
- The rating gradient (Table 3) says BBB bonds carry about half of the credit-factor loading of the high yield index at one year (−5.311 against −9.534). This supports the bucket-specific `beta_g` and `beta_p` of Section 9.2.

**Link to the existing DD plan.** The EDF in this paper is the same naive Merton DD that the card `research/cards/bharath-shumway-2008-merton-dd.md` proposes. The paper builds it from monthly stock returns over the prior 12 months (footnote 6, p. 10). That settles one open limit of the earlier card: the daily-return DD is not required to get a useful rank. An ISS^EDF series needs net debt issuance for a wide Compustat universe, not only for rated issuers.

**Falsifiable tests (proposed, not run).**
1. Build ISS^EDF from our naive DD and Compustat net debt issuance for all non-financial firms, annually, with NYSE quintile breakpoints. Regress the two-year excess return of a high yield index over duration-matched Treasuries on ISS. Expected sign: negative. Reject if the sign is positive or the expanding-window out-of-sample R² is below zero over the available post-2008 sample. State the sample length. It is short, so report block-bootstrap intervals.
2. Hedge test. For each long position, hold a hedge ratio `h_t = β̂_t (1 + γ ISS_t)` against the high yield index. Compare the variance of the hedged P&L with a constant `β̂_t` in each of the cycles 2008, 2015, 2020, 2022. Reject the use of ISS in the hedge if it lowers hedged variance in fewer than three of the four.
3. Default input. Check whether ISS adds to the consensus high yield default forecast in `default_rate_fcst` for the next 8 quarters. Score with a Diebold–Mariano test. Reject if it adds no gain.

## Limits
- One annual time series of 47 years for ISS (1962–2008). The 2- and 3-year returns overlap, so the effective sample is small. Newey–West errors correct the t-statistics, not the sample size.
- The sample ends in 2008. The paper does not cover QE, the 2015 energy stress, 2020, or 2022. The 2008 value of ISS is 0.095 (Table 2). The paper's sample does not show what followed.
- The 1983–2008 one-year result with controls is not significant (t −1.07). The strongest results sit at two and three years.
- The index is a single aggregate. Pre-1983 high yield returns come from Ibbotson, and the paper does not describe the bonds. The index return includes default losses.
- The signal is not causal. The authors say so (p. 1). They cannot separate a rational price of risk, intermediary frictions, and over-extrapolation (pp. 35–36).
- ISS^EDF needs listed equity for the EDF and firm-level debt issuance. Private high yield issuers are out. The universe is all listed non-financial firms, not rated issuers.
- Footnote 16 and Table 6 show the result does not depend on one construction. The Internet Appendix holds further checks and was not read.
- pdftotext flattened Table 7. The column pairing above comes from the header and the row counts.

## Section touched
`docs/methodology.md` Section 9.2 (HY-index hedge ratio, bucket-specific betas), Section 5.2 (issuer-quality input and eight-quarter horizon in the downside logistic), Section 5.4 (late-cycle prior). `research/cards/bharath-shumway-2008-merton-dd.md` (naive DD from monthly returns, footnote 6). No decision page yet.
