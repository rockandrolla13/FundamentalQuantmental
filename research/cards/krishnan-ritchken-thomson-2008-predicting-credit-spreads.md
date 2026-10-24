# Krishnan, Ritchken, and Thomson (2008), "Predicting Credit Spreads"

SSRN 970997, version of September 2008. Copy: `/home/ak/Documents/Predicting Credit Spreads.pdf`. The acknowledgement thanks an editor and two referees, so this is a journal version. The PDF does not name the journal, and this card does not assert one. Page numbers are PDF pages. The printed folio is the PDF page minus 2.

## Claim
1. The shape of a firm's own credit-spread curve (level, slope, curvature) predicts its future spread better than the spot or forward spread (pp. 2, 5).
2. The riskless curve adds further information (p. 5).
3. Given the credit-spread curve and the riskless curve, macro variables, stock-market variables, and firm-specific risk variables do not improve the out-of-sample forecast. They "only add noise" (pp. 5, 25).
4. Replacing current macro variables with Survey of Professional Forecasters forecasts does not change claim 3 (pp. 28–29).
5. The reason: the curves already impound the macro and firm information (pp. 25, 27).

## Method
**Curves (pp. 7–8).** Fit a Nelson-Siegel curve, with the Diebold-Li λ = 0.7308 (p. 11), to the riskless zero curve and to each firm's credit-spread curve each month:

```latex
s^{(n)}_j(t) = \beta_{1j}(t) + \beta_{2j}(t)\,F^{(n)}_2 + \beta_{3j}(t)\,F^{(n)}_3, \qquad F^{(n)}_2 = \frac{1-e^{-\lambda n}}{\lambda n}, \quad F^{(n)}_3 = F^{(n)}_2 - e^{-\lambda n}   \quad (5)
```

Intuition: three numbers per firm per month summarise the whole spread curve.

**Forecast (p. 10).** Regress the future curve factors on today's blocks:

```latex
\beta_j(t+h) = \eta_{j0} + \eta_1 \beta_j(t) + \eta_2 \beta_f(t) + \eta_3 \beta_I(t) + \eta_4 M(t) + \eta_5 F_j(t) + \epsilon_j(t+h)   \quad (10)
```

`β_f` is the riskless curve. `β_I` is the Bloomberg B-rated industrial index curve. `M(t)` = (real activity index, inflation index, 12-month market return, market volatility), with the two indices as first principal components of macro series purged of the riskless factors (p. 12). `F_j(t)` = (leverage, book to market, stock momentum, stock volatility) (p. 13). Panels run in four groups: investment grade or not, times manufacturing or service (p. 13).

**Hierarchy (p. 21).** Add blocks one at a time and measure the partial R². Reverse the order to check (p. 22).

**Out of sample (pp. 23–25).** Rolling estimation. Compare the mean squared prediction error of models M1 to M6 with the spot model, firm by firm. M3 = own curve factors and riskless factors. M5 adds macro. M6 adds macro and firm variables.

**SPF variant (p. 28).** Replace `M(t)` with the median 6-month-ahead SPF forecasts of GDP, CPI, industrial production, and the Moody's Aaa yield.

## Data
- Riskless: CRSP Treasury files, Fama-Bliss unsmoothed curves, 1970–2005 (p. 11).
- Corporate: Bloomberg transaction prices of senior, plain-vanilla, non-callable, fixed-coupon bonds of firms in the S&P 500 at any time in January 1990 to December 2005. A firm-month needs at least five bonds that span at least seven years (p. 14).
- Final sample: 241 firms, 11,894 firm-months (pp. 14–15). Most are investment grade. The sample holds a "sizeable" set of below investment grade firms and 3 defaults (p. 15).
- Macro: real activity and inflation indices after Ang and Piazzesi (2003). SPF quarterly forecasts (p. 28).

## Result
- **In sample (pp. 21–22).** After own curve factors, the riskless block explains about 14% of the remaining variance. Then the B-index, macro, and firm blocks each add about 2%. With credit-spread and riskless factors, 40% of the 3-year spread variance is explained, and macro plus firm blocks add less than 1%. Alone, macro and firm blocks explain 28%.
- **Contemporaneous (p. 27).** Macro and firm variables explain about 40% (3-year), 55% (5-year), and 50% (10-year) of spread variance. The share is higher for manufacturing than service, and higher for lower-rated manufacturers.
- **Out of sample, firm by firm (p. 24).** M3 beats the spot model for 84% of firms. Mean absolute error: 31 bp for M3 against 37 bp for the spot model, for the 6-month-ahead 5-year spread. Adding macro and firm variables does not improve the forecast.
- **By year (p. 25).** The model without macro and firm factors has the smallest error ratio in every year except 2002.
- **SPF (p. 29).** Models with SPF forecasts do worse than M3 and M4.

## What our data says
No fit on our data yet. Effect on the three macro links:

1. **Link 1, path probabilities (5.4).** Nothing direct.
2. **Link 2, downside weights (5.2).** Indirect. The paper forecasts spreads, not EBITDA. It says macro data adds little once market prices are in the model. If the same holds for the EBITDA decline event, `hy_oas` will carry most of the weight in the logistic and `pmi`, `sloos_tightening` will add little. Test: the incremental log loss test in `dynkin-et-al-2021-spreads-predict-defaults.md`.
3. **Link 3, revenue shift (5.2).** Nothing direct.
4. **Spread channel (Section 9.2, outside the three links).** This is the strongest warning in these sources. Section 9.2 says: "Fit `log κ_t` and `η_sector,t` on the macro vector over at least one cycle." The paper says that a macro vector does not improve a 6-month spread forecast once the curves are in. Two readings:
   - For a forecast of the spread level, use the curve and the riskless factors first. Add macro only if it wins out of sample.
   - For a scenario ("what is the spread if path m happens"), the paper does not apply. It tests forecasts with today's macro, not conditional spreads under a given macro outcome. The contemporaneous fit (40% to 55%, p. 27) supports a macro map for scenarios.

   Proposal: keep the macro map for scenario re-evaluation in 9.2. Do not use it as a spread forecast in S7 without a test. Test: on TRACE HY issuers 2007–2026, compare the 6-month out-of-sample error of `η_sector,t` from (a) its own lag and the riskless factors and (b) the same plus the macro vector. Keep (b) only if it wins in at least three of the four cycle windows.

## Limits
- Mostly investment grade S&P 500 firms, non-callable bonds. Most high yield bonds are callable. So the result may not carry over to our universe.
- Sample ends in 2005. No 2008, 2015, 2020, or 2022 window.
- Panels use only two industry groups. No sector-level macro sensitivity.
- The forecast horizon is mostly 6 months. Longer horizons are not the focus.
- The paper tests forecasts, not conditional scenario maps.

## Section touched
`docs/methodology.md` Section 9.2 (spread channel: `log κ_t` and `η_sector,t` on the macro vector), Section 8 S7 (macro-conditional sector tilt), and Section 5.2 (choice of logistic inputs).
