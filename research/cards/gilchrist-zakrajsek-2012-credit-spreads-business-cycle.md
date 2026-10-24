# Gilchrist and Zakrajšek (2012), "Credit Spreads and Business Cycle Fluctuations"

American Economic Review (2012). Peer-reviewed journal article. This card reads the working paper version, NBER Working Paper 17021 (May 2011), which has not been peer reviewed. Page numbers below are the printed working paper pages. Check any number against the journal version before it enters a decision page.

## Claim
A credit spread index built from individual bond prices predicts economic activity better than the Baa–Aaa spread or the paper–bill spread (pp. 1, 8–10). Most of that power comes from the excess bond premium (EBP), the part of the spread that expected default does not explain (pp. 20–23). Since 1985 the expected default part has no power for GDP growth, and the EBP carries all of it (pp. 23, 32). A shock to the EBP that is orthogonal to the state of the economy lowers output, investment, prices, and equity prices (p. 24). The authors read the EBP as the risk-bearing capacity of financial intermediaries, not as a forecast of default (pp. 27–31).

## Method
**GZ credit spread (pp. 3–6).** For each bond k of firm i, build a risk-free bond with the same cash flows. Discount it with zero-coupon Treasury yields. The spread is the corporate yield minus the yield of that synthetic Treasury. The index is the simple average over all bond-firm observations in month t.

```latex
S^{GZ}_t = \frac{1}{N_t}\sum_i \sum_k S_{it}[k]   \quad (1)
```

Intuition: the index removes the duration mismatch that distorts the Baa–Aaa spread.

**Forecast regression (p. 7).** One regression per indicator and per horizon h, estimated by OLS with Hodrick (1992) standard errors.

```latex
\nabla^{h} Y_{t+h} = \alpha + \sum_{i=1}^{p} \beta_i \nabla Y_{t-i} + \gamma_1 TS_t + \gamma_2 RFF_t + \gamma_3 CS_t + \epsilon_{t+h}   \quad (2)
```

TS is the term spread (10-year minus 3-month). RFF is the real federal funds rate. CS is one credit spread. Intuition: the test asks what the spread adds beyond the yield curve and the policy stance. The tables report standardised coefficients.

**Spread pricing equation (p. 11).** Regress the log spread of each bond on a firm default measure and bond traits. Double-cluster errors by firm and month.

```latex
\ln S_{it}[k] = \beta\, DFT_{it} + \gamma' Z_{it}[k] + \epsilon_{it}[k]   \quad (3)
\widehat{S}_{it}[k] = \exp\big(\hat\beta DFT_{it} + \hat\gamma' Z_{it} + \hat\sigma^2/2\big), \qquad EBP_t = S^{GZ}_t - \widehat{S}^{GZ}_t
```

Intuition: the fitted spread is the price of expected default. The EBP is what is left over, and the authors read it as the price of bearing credit risk. The default measure DFT is the Merton distance to default (DD), solved with the iterative method of Bharath and Shumway (2008). The default point is current liabilities plus half of long-term liabilities, T = 1 year (pp. 12–14). The controls Z are duration, amount outstanding, coupon, age, a callable flag, S&P rating fixed effects, and 3-digit industry fixed effects (p. 15).

**Option adjustment for callable bonds (p. 17).** The callable flag interacts with every control. Callable bonds also depend on the level, slope, and curvature of the Treasury curve and on realised volatility of the 10-year yield. Intuition: a falling Treasury level raises the value of the call and so raises the fitted spread.

**VAR (pp. 23–24).** Eight variables, two lags, recursive order: consumption, investment, GDP, GDP deflator inflation, EBP, excess stock return, 10-year Treasury yield, federal funds rate. The EBP shock affects activity and prices with a lag. The yields and stock prices react in the same quarter.

## Data
- Bonds: senior unsecured, fixed coupon, non-financial issuers. Lehman/Warga and Merrill Lynch month-end prices (p. 3).
- Sample: January 1973 to September 2010. 346,126 bond-months, 5,982 bonds, 1,112 firms (Table 1, p. 5).
- Trims: spreads below 5 bp or above 3,500 bp are out. Issues below $1 million par are out. Remaining maturity must lie between 1 and 30 years (p. 4).
- Mean spread 204 bp, standard deviation 281 bp, median 118 bp. Median rating BBB1. 67.2% of bonds are callable. Mean duration 6.47 years (Table 1, p. 5).
- The GZ index has a standard deviation near 100 bp. The Baa–Aaa spread has 50 bp (pp. 6–7).
- Activity series: payroll employment, unemployment rate, manufacturing industrial production (monthly), real GDP and its components (quarterly).
- SLOOS: net percent of banks that tightened C&I standards. No survey exists for 1984–89 (Figure 7 note, p. 28).
- Broker-dealer CDS and equity returns, 2003 to 2010 (pp. 29–31).

## Result
- **GZ spread beats the standard spreads (Table 2, pp. 8–9).** Standardised coefficient at 12 months for payroll growth: GZ −0.497 (t 13.4), Baa–Aaa +0.054 (t 1.15), paper–bill −0.080 (t 2.29). Adjusted R² for payroll growth at 12 months: baseline 0.422, with GZ 0.579. For the unemployment rate at 12 months: baseline 0.270, with GZ 0.417. A rise of 100 bp in the GZ spread lowers industrial production growth by almost 3.0 points (annualised) over the next three months (p. 8).
- **GDP (Table 3, p. 10).** Four-quarter horizon: GZ coefficient −0.482 (t 5.74), Baa–Aaa −0.066 (t 0.52), paper–bill −0.105 (t 0.82). Adjusted R²: baseline 0.215, with GZ 0.369. A rise of 100 bp in the GZ spread lowers real GDP growth by more than 1.25 points over four quarters (p. 10).
- **Default sensitivity of spreads (Table 4–5, pp. 16–17).** A one-standard-deviation fall in DD widens spreads by about 15 bp on average (p. 15). By bond type the marginal effect is 0.190 points for noncallable bonds and 0.129 points for callable bonds (Table 5). The text states 29 bp and 13 bp for a one-standard-deviation fall in DD (p. 18). The source does not reconcile these with the Table 5 values and the Table 5 standard deviation of 3.946, so quote the text figures with care. The log-spread regression adjusted R² is 0.649 without the option terms and 0.700 with them.
- **Callable spreads and the Treasury curve (Table 5, p. 17, text p. 18).** A one-standard-deviation rise in the level factor lowers callable spreads by 0.783 points, almost 80 bp. A rise in the slope factor lowers them by 18 bp. A rise in rate volatility widens them by 27 bp.
- **EBP path (pp. 19–20).** The option adjustment explains about 200 bp of the rise in the GZ spread in autumn 2008. The EBP rose before or during every recession except 1990–91. It hit a low in late 2003 and a record 275 bp in October 2008.
- **Split forecasts (Table 6, p. 21).** At 12 months for payroll growth: predicted spread −0.355 (t 9.63), EBP −0.369 (t 14.5). At 3 months: predicted −0.202, EBP −0.259. For the unemployment rate at 3 months: predicted 0.134, EBP 0.331. The EBP coefficient is larger in absolute size in all six columns. At 12 months for payroll growth the two are close (0.369 against 0.355).
- **GDP split (Table 7, p. 22).** Full sample, four quarters: predicted spread −0.258 (t 2.56), EBP −0.364 (t 5.36), adjusted R² 0.365. A rise of 100 bp in the EBP lowers GDP growth by more than 1.5 points. The same rise in the predicted spread lowers it by 0.5 points (p. 21).
- **Since 1985 (Table 7, p. 23).** Predicted spread −0.023 (t 0.20). EBP −0.501 (t 6.80). Adjusted R² 0.357. A rise of 100 bp in the EBP lowers GDP growth by about 2.0 points (p. 23). Inventory investment, structures, and equipment investment react most. The EBP effect is more than twice the predicted-spread effect for these (p. 23).
- **VAR (pp. 24–26).** A one-standard-deviation EBP shock is about 20 bp. GDP bottoms about 0.5 points below trend after five quarters. Investment falls more and for longer. The text reports "appreciable disinflation", a fall in the federal funds rate from about one quarter after the shock, and a fall in the 10-year yield. The cumulative excess stock return falls by about 7.0 points. The shock explains more than 10% of output variance and 25% of business investment variance at business cycle frequencies (p. 24).
- **Link to credit supply (pp. 27–31).** The EBP and the net percent of banks tightening C&I standards have a "strikingly high" correlation, especially late in the sample (pp. 28–29). The paper gives no coefficient. Financial sector ROA moves against the EBP (p. 29). An adverse shock to broker-dealer returns raises the broker-dealer 1-year CDS spread at once and the EBP with a path close to the CDS path (pp. 30–31).

## What our data says
This section is our proposal. The paper does not test any of it. The paper tests no bond return, no EBITDA, and no high yield sample.

**Fit to the sample.** The GZ sample is mostly investment grade (median BBB1), callable (67.2%), and long dated (mean term 11.3 years). Our book is high yield. The DD slope, the callable adjustment, and the EBP all come from that mix. Treat the sizes below as direction only.

**Link 2: the downside-weight logistic (Section 5.2).**
- Signal: a spread residual, not the spread level. The paper shows that the part of the spread that expected default explains has no power for GDP since 1985 (Table 7, p. 23). The part that it does not explain carries all of it.
- Sign: a higher EBP lowers growth, so it raises the large EBITDA decline probability. Expected sign of its logistic coefficient: positive.
- Size: 100 bp of EBP lowers GDP growth by about 2.0 points in 1985–2010 (p. 23). We have no EBITDA size from the paper.
- Horizon: 1 to 4 quarters (Table 3, p. 10).
- Implication: `hy_oas` in `m_t` mixes the two parts. A model that uses `hy_oas` and `default_rate_fcst` together may recover the split, because the default forecast stands for the expected default part. Add `sloos_tightening` because the paper links it to the EBP (p. 28). Check that the three terms are not collinear before reading any coefficient.

**Link 3: the growth shift `beta_sector × (G_h(m) − Ḡ)` (Sections 5.2, 9.2).** A spread widening and a GDP path are not independent. The EBP leads GDP by up to four quarters (Table 7). A GDP forecast that already includes the spread signal, together with a spread input in the logistic for the same issuer, counts the same information twice. State in the decision page which forecast vintage reads the spread.

**Link 1: path probabilities (Section 5.4).** An EBP shock moves GDP down and prices down, with lower policy rates and lower long yields (p. 24). In the GDP and CPI forecast distribution this is the recession or disinflation region. It is not the stagflation region. Use this to check the sign of the correlation ρ between GDP and CPI in the joint normal. A negative ρ puts too much mass on stagflation for a credit-led downturn. The paper does not estimate ρ, so this is a plausibility check only.

**Rate hedge and Section 9.2.** The paper supports two signs in 9.2. The 10-year yield falls after an EBP shock (p. 24), so spreads widen when growth-driven yields fall. That matches `beta_g < 0`. The level factor lowers callable spreads by 0.783 points per standard deviation (Table 5), so a callable bond has a spread response to the Treasury level in addition to its modified duration. Callable high yield bonds need the effective rate duration of 9.2 more than the paper's mixed sample does.

**HY-index hedge.** The spread level is a state variable. The paper gives no evidence that the spread level or the EBP predicts the return of the high yield index. Do not use it as a hedge ratio signal. Use it to set the hedge size only if a test shows that the HY-index drawdown depends on it.

**Falsifiable test (proposed, not run).** Fit the pooled logistic of Section 5.2 on a point-in-time panel with four macro input sets: `hy_oas` only, `hy_oas` plus `default_rate_fcst`, the same plus `sloos_tightening`, and a spread residual from the log-spread regression of Equation 3 with our own default measure. Score each on an out-of-sample period after 2011 with log loss and the Clark–West test. Reject the claim "the residual carries the signal" if the residual set does not beat the level set in at least three of the four cycles 2008, 2015, 2020, 2022. Reject it too if the residual coefficient has the wrong sign in any of them.

## Limits
- Working paper text. Not the journal text.
- Mostly investment grade, callable, long dated bonds. No high yield split.
- The EBP is a residual of a model with the Merton DD. A different default measure gives a different EBP. The paper shows no robustness check on that choice.
- The macro tests are in-sample. No out-of-sample forecast test appears in the text.
- No issuer-level outcome. The paper predicts aggregate GDP and its parts. It does not predict firm EBITDA or defaults.
- The SLOOS link is a plot and the words "strikingly high". The text gives no correlation figure. The survey has a gap for 1984–89.
- The causal reading (credit supply, risk-bearing capacity) rests on the broker-dealer VAR for 2003–2010 and on recursive identification (pp. 24, 30). The authors also name a disaster-risk reading (p. 27). The paper does not separate the two.
- Standardised coefficients. The text does not give the unit of standardisation.
- pdftotext flattened the tables. The numbers above are read from the text layout.

## Section touched
`docs/methodology.md` Section 5.2 (macro inputs to the downside weight: `hy_oas`, `sloos_tightening`, `default_rate_fcst`), Section 5.4 (sign of the GDP and CPI correlation), Section 9.2 (growth channel, `beta_g < 0`, effective rate duration of callable bonds). No decision page yet.
