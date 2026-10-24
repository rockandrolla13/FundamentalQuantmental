# López-Salido, Stein and Zakrajšek (2017), "Credit-Market Sentiment and the Business Cycle"

Quarterly Journal of Economics (2017). Peer-reviewed journal article. This card reads the Federal Reserve Board revision, FEDS 2015-028r1 (version dated 30 December 2016, "forthcoming in the QJE"). It also checks the NBER Working Paper 21879 (January 2016) for numbers that changed. Page numbers below are the printed pages of the FEDS version. Check any number against the journal version before it enters a decision page.

## Claim
Credit-market sentiment in year t−2 forecasts a fall in economic activity in years t and t+1 (p. 1). Sentiment here means a low expected return on credit risk. The mechanism is predictable mean reversion: when credit is priced aggressively, spreads widen later, and the widening coincides with the start of a contraction (p. 1). The same signal does not work for stock-market sentiment (pp. 2, 12–13). Balance-sheet measures of leverage add nothing in a US-only sample (pp. 25–27). The signal also forecasts a fall in net debt issuance and a rise in net equity issuance, with larger effects on low-rated firms (pp. 31–39).

## Method
**Step 1: sentiment proxy (pp. 9, 11).** Follow Greenwood and Hanson (2013). Forecast the annual change in the Baa–Treasury spread with two variables dated t−2: the log of the high yield share of gross bond issuance (HYS) and the level of the spread. An alternative adds the term spread. A second alternative uses the excess bond premium (EBP) of Gilchrist and Zakrajšek (2012) for 1973–2015.

```latex
\Delta s_t = \theta_1' z_{1,t-2} + \nu_{1t}   \quad (2)
```

Intuition: the fitted change is the part of the spread move that follows from past valuation, not from news about cash flows. The authors read it as the unwinding of sentiment.

**Step 2: activity (p. 11).** Regress activity on the fitted value. The two steps are estimated together by nonlinear least squares to handle the generated regressor. Newey–West standard errors.

```latex
\Delta y_{t+h} = \beta_1 \Delta \hat{s}_t + \beta_2 \hat{r}^{SP}_t + \gamma' x_{t-1} + \epsilon_{t+h}, \qquad h \ge 0   \quad (4)
```

Here y is log real GDP per capita (or investment, durables, unemployment). The control x holds lagged growth and, in some columns, inflation and Treasury yield changes. The authors state that this is not an instrumental-variable design, because the sentiment proxies would not meet the exclusion restriction (p. 2).

**Firm investment by rating (p. 37).** Interact the fitted spread change with three rating buckets: high yield (Ba1 to Ca), low investment grade (A1 to Baa3), and high investment grade (Aaa to Aa3). Rating is as of the end of t−1.

```latex
\Delta \ln I_{jt} = \sum_k \beta_k\, \Delta\hat{s}_t \cdot \mathbf{1}[RTG_{j,t-1}=k] + \gamma_1 \Delta \ln Y_{jt} + \gamma_2 \Delta \ln Q_{j,t-1} + \eta_j + \epsilon_{jt}   \quad (5)
```

Intuition: low-rated firms load more on the market-wide credit factor. Y is sales and Q is Tobin's Q.

## Data
- Annual US data, 1929–2015. The conservative baseline is 1952–2015 (pp. 2, 16).
- Activity: real GDP per capita, business fixed investment, residential investment, durable goods consumption, unemployment rate (Appendix A.1, p. 45).
- Spread: Moody's Baa yield less the 10-year Treasury yield, December values (pp. 8, 45).
- High yield share: fraction of non-financial gross bond issuance rated below investment grade by Moody's. Taken from Greenwood and Hanson for 1926–2008 and extended to 2015 (p. 46).
- Financing mix: Financial Accounts of the United States for 1952–2015 (p. 32). Firm panel 1985–2015 with a senior unsecured rating: 1,844 firms and 15,895 observations for all rated firms, 1,382 firms and 7,811 observations for high yield firms (Table 12 note, p. 36).
- Investment panel 1973–2015: 1,674 rated firms, 17,540 observations (Table 13 note, p. 38).
- Firm data come from Compustat merged with the Moody's Default and Recovery Database. Utilities, finance, and some other sectors are out (pp. 46–47).

## Result
- **Spread changes forecast growth (Table 1, p. 10).** The coefficient on the lagged change in the Baa–Treasury spread is −1.997 (s.e. 0.746), adjusted R² 0.425. A one-standard-deviation rise (86 bp) goes with a fall of 0.37 standard deviations in next-year GDP growth, about 1.8 points (p. 11).
- **First step (Table 2, pp. 12–13).** The log HYS coefficient is 0.095 (s.e. 0.024). The spread level coefficient is −0.248 (0.042). R² is 0.10. A high junk share or a low spread at t−2 predicts a spread rise at t. Standardised coefficients are 0.18 and −0.30 (footnote 14, p. 13).
- **Second step, full sample (Table 2, p. 12).** The coefficient on the fitted spread change is −4.800 (s.e. 1.134), R² 0.379. A move from the 25th to the 75th percentile cuts cumulative GDP per capita growth by about 3.2 points over t and t+1, and raises unemployment by nearly 1.5 points (p. 2). Footnote 18 on p. 20 gives 3.2 and 1.4. The working paper says 3.0 and 1.2.
- **Post-war sample (Table 3, p. 18).** 1952–2015: −2.680 (0.576). 1952–2007: −2.910 (0.679). With macro controls: −3.169 (0.945) and −3.903 (1.308). The estimates are stable over rolling 40-year windows for the last 30 years but smaller than the full-sample value (Figure 4, p. 17). Three observations are influential: 1932, 1934, 1977 (p. 14).
- **Horizons and size (Table 4, p. 19).** Baseline move of 29 to 30 bp between the 25th and 75th percentile. Cumulative effects for GDP per capita: −0.786 (h = 0), −1.213 (through t+1, s.e. 0.300), −1.102 (through t+2). Business fixed investment: −2.653, −4.830, −5.527. Residential investment: −4.843, −7.050, −6.576. Durables: −2.246, −2.925, −1.677. Unemployment: +0.455, +0.770, +0.872 points. The effect on output is significant in t and t+1 and not in t+2 (pp. 16–17).
- **Stock sentiment (Table 2, p. 12).** With the fitted stock return alone the coefficient is 0.145 (0.057). With both, the stock coefficient is 0.069 (0.050) and the credit coefficient stays at −4.409 (1.053). Other stock predictors fail even alone (Appendix B, p. 13).
- **Alternative proxies (Table 5, p. 21).** Adding the term spread lifts first-step R² from 0.10 to 0.135 for 1929–2015. The second-step coefficient is −3.993 (0.929). The EBP alone gives −3.016 (0.928) for 1973–2015, first-step coefficient −0.443 (0.124), R² 0.077. With the larger fitted variation, the P25 to P75 move is 45 bp and the GDP effect is 1.7 points, unemployment 1.1 points (p. 22).
- **Asymmetry (Tables 6–7, pp. 23–24).** Raw spread rises have coefficients of −2.304 (full sample), −1.648 (1952–2015), −1.459 (1973–2015). Falls have −1.586, −0.838, −0.828. None of the three differences is significant. For the EBP over 1973–2015, rises give −2.331 (0.566) and falls −0.542 (0.252). The difference is −1.789 (0.648), significant (p. 24). The fitted two-step measure shows no robust asymmetry (Table 7).
- **Leverage (Tables 8–10, pp. 26–30).** Five-year bank credit growth, private credit to GDP, business credit to GDP, household credit to GDP, and corporate debt to assets are insignificant in 1952–2015. The sentiment coefficient stays near −2.96 to −2.99. The balance-sheet variables are persistent, with half-lives of 4 to 8 years. Sentiment has a half-life of about 1.4 years (p. 28). The interaction with the business credit gap is −43.016 (11.358). The effect at the 90th percentile of the gap is −2.624 (0.772) and at the 10th percentile −0.791 (0.698). In the other three interactions the effect at the 90th percentile is between 1.5 and 3.3 times the effect at the 10th, and only one interaction is significant (p. 29).
- **Bank standards (Figure 5, p. 20).** The sentiment measure and the net fraction of banks tightening standards (SLOOS-based, 1991–2013) move together. The text gives no coefficient.
- **Financing mix (Tables 11–12, pp. 34–36).** Aggregate, 1952–2015: net equity issuance +0.973 (0.336), net debt issuance −0.882 (0.449), mix effect 1.855. Firm level, all rated firms: +1.171 (0.422) and −0.856 (0.412). High yield firms: +0.858 (0.386) and −1.964 (0.496), mix effect 2.823. For high yield firms the debt effect is more than twice the equity effect, so substitution is incomplete (p. 36).
- **Firm investment by rating (Table 13, pp. 38–39).** A 100 bp rise in the fitted spread change at t−2 goes with a fall in capital expenditure growth in year t of 14.0 points for high yield (s.e. 3.724), 11.5 for low investment grade, and 3.6 for high investment grade (insignificant). With sales and Q controls: 7.1 (2.409), 4.3 (2.043), and +1.062 (3.165). The Wald test of equal coefficients, high yield against high investment grade, has p = 0.013 without controls and 0.021 with controls. The text says the signal also forecasts a fall in sales growth (p. 39). The working paper reports 14, 10, 5 without controls and about 11, 5, below 1 with controls.

## What our data says
This section is our proposal. The paper tests no EBITDA outcome, no bond return, and no sample after 2015. The sentiment data are annual and the spread is the Baa–Treasury spread, not the high yield spread.

**Link 2: the downside-weight logistic (Section 5.2).**
- Signal: a lagged sentiment term, in addition to the current `hy_oas` level and its recent change.
- Sign: the two parts differ. A recent rise in the spread predicts weak growth (Table 1, coefficient −1.997). A low spread level two years ago predicts a later spread rise and weak growth (Table 2). So in a logistic on a four-quarter EBITDA drop, the recent change should carry a positive coefficient. At a lag of two years, a low spread level should carry a negative coefficient on the downside probability and a high junk share a positive one. A pooled logistic that has only the current `hy_oas` level can confuse these two.
- Size: from 25th to 75th percentile of the fitted move, about 1.2 points of cumulative GDP per capita over two years in the post-war sample (Table 4). We have no EBITDA size.
- Horizon: the effect starts in year t of a t−2 signal and fades by t+2 (Table 4). The four-quarter horizon of Section 5.2 sits at the front edge. Test an eight-quarter horizon as well.
- Rating gradient: the effect on investment is about twice as large for high yield as for low investment grade with controls (7.1 against 4.3, Table 13). It is near zero for high investment grade. This supports a macro-by-rating interaction in the logistic, not a sector effect alone. The paper does not test sector differences.
- Equity inputs: do not add stock valuation as a macro input to the downside weight. Equity sentiment has no incremental power (Table 2).
- Leverage interaction: a positive interaction between sentiment and a credit gap is plausible (Table 10), but only one of four is significant. Treat it as a candidate, not a design input.

**Link 3: the growth shift `beta_sector × (G_h(m) − Ḡ)` (Sections 5.2, 9.2).** The paper says sentiment also forecasts a fall in sales growth (p. 39) and gives the fall in capex by rating. It gives no sales growth size and no sector beta. The rating gradient suggests the revenue shift by rating bucket may differ at equal sector. The test below checks it.

**Link 1: path probabilities (Section 5.4).** Sentiment at t−2 is a state variable the phase prior `π_phase` of framework F6 can use. A compressed spread and a high junk share raise the prior of the recession path two years out. This is a proposal. The paper does not map sentiment to named paths.

**Refinancing (Section 9.2).** High yield firms cut net debt issuance by 1.964 points of assets per 1 point of fitted spread widening, and only add 0.858 in equity (Table 12). This supports `refi_access(m)` falling when sentiment reverses, and it supports a link from `p_refi` to the sentiment state two years before the maturity wall.

**HY-index hedge.** The first-step regression is a forecast of the spread change. A low spread level and a high junk share predict a wider Baa–Treasury spread (Table 2, R² 0.10). The P25 to P75 range of the forecast is 30 to 45 bp. The paper does not test the high yield index return. The companion paper by Greenwood and Hanson (2013) does (see its card).

**Falsifiable test (proposed, not run).** Add to the Section 5.2 logistic a two-year-lagged term built from the log junk share, the spread level, and the term spread, estimated first on its own in a first step as in Equation 2. Interact it with three rating buckets. Score out of sample after 2011 with log loss and the Clark–West test against the model with current `hy_oas` and its change only. Predicted signs: positive for high yield, smaller for low investment grade, near zero for high investment grade. Reject the claim if the high yield coefficient is not positive in at least three of the cycles 2008, 2015, 2020, 2022. Reject the rating ordering if the high yield coefficient is not larger than the investment grade coefficient.

## Limits
- Annual data. 86 observations at most. Three influential years: 1932, 1934, 1977 (p. 14).
- The sample ends in 2015. It contains no 2020 or 2022 episode.
- The spread is Moody's Baa less the 10-year Treasury. It is not a high yield spread. The junk share is issuance by rating, not an index spread.
- Predicted changes in the spread are generated regressors. The authors correct standard errors by joint estimation (p. 11). The first-step R² is 0.08 to 0.15.
- The authors say the design is not an instrumental-variable design. The demand explanation of Rognlie, Shleifer and Simsek (2016) is not ruled out (pp. 2–3).
- Outcome variables are GDP, investment, durables, unemployment, capex, and financing flows. No EBITDA, no default, and no bond return.
- Asymmetry tests have low power. Only the EBP change shows a significant difference (p. 24).
- The balance-sheet result rests on a single-country series. The authors warn that persistence leaves little power (pp. 27–28).
- Numbers differ between the working paper and the FEDS revision (full-sample GDP effect 3.0 against 3.2, unemployment 1.2 against 1.4, rating-bucket investment effects). Use the revision and recheck against the QJE text.
- The 29 bp and 30 bp figures for the percentile move both appear in the text (Table 4 note and p. 18).

## Section touched
`docs/methodology.md` Section 5.2 (lagged sentiment and rating interaction in the downside logistic, horizon), Section 5.4 (sentiment in the phase prior), Section 9.2 (refinancing access, hedge sizing from the spread-reversal forecast). No decision page yet.
