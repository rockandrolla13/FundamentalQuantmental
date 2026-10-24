# Vassalou (2003), "News Related to Future GDP Growth as a Risk Factor in Equity Returns"

Journal of Financial Economics 68(1), 2003. Peer-reviewed journal article. This card reads the final draft of 7 January 2002, marked "Forthcoming: Journal of Financial Economics". Copy: `000331315.pdf` in the repo root (44 pages). Page numbers below are PDF pages. They equal the printed page numbers of the draft. Check any number against the journal version before it enters a decision page.

## Claim
A factor that tracks news about GDP growth over the next four quarters, plus the market factor, prices the 25 Fama-French size and book-to-market portfolios about as well as the Fama-French three-factor model (abstract p. 2, p. 28). Once this factor is in the model, SMB and HML lose most or all of their power to explain the cross-section (pp. 20–23, 28). The author reads this as evidence that SMB and HML are priced mainly because they carry news about future GDP growth (p. 19, p. 28). A version built only from two bond portfolios, the corporate-minus-government return (DEF) and the long-minus-short government return (TERM), does the same job (pp. 26–27, Table 8).

## Method
**Mimicking portfolio (Section 4, pp. 14–18).** News about future GDP growth is not observable. The author projects future GDP growth on returns of eight zero-investment base assets: the six Fama-French size and book-to-market portfolios in excess of the T-bill, plus DEF and TERM. Lagged control variables filter out the predictable part of the base-asset returns (Lamont's method).

```latex
GDPGR_{t,t+4} = a + c\,B_{t-1,t} + k_1 TERMY_{t-2,t-1} + k_2 DEFY_{t-2,t-1} + k_3 CAY_{t-2,t-1} + k_4 RF_{t-1,t} + e_{t,t+4}   \quad (9)
TRB_{t-1,t} = c\,B_{t-1,t}   \quad (11)
```

Intuition: the portfolio weights `c` are the part of each asset's return that forecasts next year's GDP growth, after the controls remove what the asset was expected to earn anyway.

`GDPGR_{t,t+4}` is annualised GDP growth over the next four quarters. TERMY is a term yield spread. DEFY is a default yield spread. CAY is the Lettau-Ludvigson consumption-wealth ratio. RF is the 30-day T-bill rate. The weights `c` come from one quarterly regression over the full sample, 1953 to 1998. The author applies the same `c` to quarterly base-asset returns (QFTRALL) and to monthly returns (MFTRALL) (p. 18). The weights need not sum to one because the base assets are zero-investment portfolios (p. 17).

**Asset pricing tests (Section 2, pp. 5–11).** Linear stochastic discount factor, estimated by GMM.

```latex
E(R\,m) = p, \qquad m = b_0 + f' b_1   \quad (1, 2)
\lambda = -R^0\,\mathrm{cov}(f, f')\,b_1   \quad (3)
```

Intuition: a factor is priced when the discount factor loads on it, and its premium `λ` follows from that loading and the factor covariance.

- **One step (quarterly).** The moments of regression (9) sit on top of the pricing moments. A selection matrix forces the regression moments to hold exactly. The standard errors then include the estimation error of the mimicking portfolio, the "generated regressor" problem (pp. 4, 6–7).
- **Two step (monthly and quarterly).** Estimate `c` first, then price assets with the fixed portfolio. The coefficients are the same as in one step. The standard errors differ (p. 4).
- **Model comparison.** Hansen-Jagannathan (HJ) distance, the maximum pricing error over the test assets. The p-value comes from 100,000 simulated chi-square draws (pp. 8–9).
- **Do SMB and HML add anything?** Wald test in one step, Newey-West ΔJ in two steps (pp. 10, Equation 7).

```latex
\Delta J = T\,J(\text{restricted}) - T\,J(\text{unrestricted}) \sim \chi^2(\#\text{restrictions})   \quad (7)
```

Intuition: drop SMB and HML. If the fit gets only a little worse, they carried nothing the GDP-news factor did not already carry.

- **Stability.** Andrews (1993) supLM test on the interval [0.15, 0.85] (p. 9).
- **Managed portfolios.** Returns scaled by TERMY as a conditioning variable (pp. 10–11).
- **Choice of base assets (Section 6).** Rebuild the factor from DEF and TERM only (QFIX), and from the six equity portfolios only (QEQ) (pp. 25–27).

## Data
- Test assets: the 25 Fama-French value-weighted size and book-to-market portfolios plus the 30-day T-bill. The quarterly tests use 12 of the 25, chosen to include the hardest to price, such as small growth (pp. 11–12, Table 1).
- Base assets: the six Fama-French 2×3 portfolios, and DEF and TERM from the Ibbotson 1999 SBBI Yearbook (pp. 12–13).
- Controls: DEFY and TERMY from the St Louis Fed, CAY from Lettau and Ludvigson, RF from Ibbotson (p. 13).
- GDP: seasonally adjusted, from CITIBASE. One vintage, not real time (p. 13).
- Sample: 1953 to 1998, set by CAY. Monthly tests use 540 observations. Quarterly tests use 180 (p. 13).

The source is inconsistent on three definitions.
1. DEFY is the Moody's Baa minus Aaa yield in the text (p. 13). The Table 2 note says long-term corporate minus long-term government yield (p. 34).
2. TERMY is the 10-year minus 1-year government yield in the text (pp. 11, 13). The Table 2 and Table 5 notes say long-term Treasury minus T-bill (pp. 34, 37).
3. TERM is the 30-year government return minus the short rate in the text (p. 12). The Table 2 note says long-term minus one-year government return (p. 34).

## Result
**The base assets forecast GDP growth (Table 2, p. 34; text pp. 15–17).**
- Eight base assets only, 1953–1998: adjusted R² 16.12%, χ²(8) 43.91, bootstrap p-value 0.0020.
- Subperiods 1953Q1–1975Q2 and 1975Q3–1998Q4: adjusted R² 18.58% and 18.78%. Bootstrap p-values 0.0654 and 0.1439. The author ascribes the weak bootstrap result to 90 observations per subperiod.
- With the controls (the column that builds the portfolio): adjusted R² 38.62%, χ²(8) 18.88, asymptotic p-value 0.0155, bootstrap p-value 0.0973.
- DEF carries the largest weight. Without controls: 0.333 (t 3.06). With controls: 0.142 (t 1.73). No equity weight has |t| above 1.16 in the full sample with controls. TERM: 0.013 (t 0.52).
- Controls: RF −1.888 (t −4.35), DEFY 0.006 (t 2.65), CAY 0.373 (t 1.81), TERMY 0.001 (t 1.00).

**The factor (Table 3, p. 35).**
- Mean return QFTRALL 0.172 (t 4.02), MFTRALL 0.058 (t 4.25). Standard deviation 0.569 and 0.315. A positive mean means a positive risk premium (p. 18).
- Correlation with SMB: 0.425 (quarterly), 0.291 (monthly). With HML: 0.280 and 0.290.
- Regression of the factor on SMB and HML: adjusted R² 28.76% (QFTRALL) and 19.08% (MFTRALL).

**SMB and HML lose their power (quarterly, one step).**

| Model | Over-identification p | Wald(SMB&HML) p | Source |
| --- | --- | --- | --- |
| QFTRALL, unscaled | 0.0391 | 0.4465 | Table 4 B, p. 36 |
| RMRF + QFTRALL, unscaled | 0.0348 | 0.0895 | Table 4 C, p. 36 |
| QFTRALL, scaled by TERMY | 0.3724 | 0.6992 | Table 5 B, p. 37 |
| RMRF + QFTRALL, scaled | 0.3090 | 0.3482 | Table 5 C, p. 37 |

The QFTRALL premium is 0.002 (one-step t 2.20) unscaled and 0.003 (t 2.03) scaled. With RMRF, the unscaled one-step t falls to 1.97 (pp. 20–21, Tables 4–5).

**Monthly comparison, 26 test assets (Table 6, p. 38; text pp. 22–23).**
- HJ distance: CAPM 0.418, Fama-French 0.358, MFTRALL 0.3817, RMRF + MFTRALL 0.381. The J-test and the HJ test reject all four models.
- Add SMB and HML to MFTRALL: ΔJ 3.110 (p 0.2112), HJ falls from 0.382 to 0.373. Add them to RMRF + MFTRALL: ΔJ 6.834 (p 0.0774), HJ falls to 0.370. For the CAPM the same addition gives ΔJ 20.259 (p 0.0000).
- supLM: CAPM 13.636 and Fama-French 14.793, both marked unstable. MFTRALL 13.086 and RMRF + MFTRALL 8.643 pass (p. 23).
- Scaled by TERMY (Table 7, p. 39): HJ Fama-French 0.292, RMRF + MFTRALL 0.299. ΔJ p-values 0.2987 and 0.5385. No model fails supLM.

**Which portfolios.** The paper reports no factor betas by portfolio. It reports pricing errors only. The GDP-news model misprices the three smallest growth portfolios (11, 21, 31) more than the Fama-French model. It prices the large-cap portfolios slightly better than the Fama-French model. It prices every portfolio except the smallest growth portfolio better than the CAPM (p. 22, Figure 1, p. 43).

**Bond portfolios as test assets (footnote 5, p. 23).** The GDP-news model underprices TERM by 24 bp a year and DEF by 68 bp a year. The Fama-French model underprices TERM by 100 bp and DEF by only 6 bp. The author concludes that SMB and HML hold information about DEF that the GDP-news factor does not hold. She says it may be default risk and does not test it.

**Bond-only factor (Table 8, p. 40; text p. 26).** QFIX weights: DEF 0.203 (t 2.95), TERM 0.041 (t 1.93), joint p-value 0.0048. With RMRF + QFIX, Wald(SMB&HML) is 0.03 (p 0.9841) and ΔJ is 0.7910 (p 0.8516). HJ distance 0.3882 (p 0.6970), against 0.397 for the quarterly Fama-French model. supLM passes.

**Equity-only factor (Table 9, pp. 41–42; text p. 27).** RMRF + QEQ has HJ distance 0.442 (p 0.0029). Adding SMB and HML lowers it to 0.395, with ΔJ 4.857 (p 0.0882). The quarterly CAPM has 0.518 and RMRF + QFTRALL has 0.440 (p. 27). The bond-only factor beats the equity-only factor.

## What our data says
This section is our proposal. The paper tests equity portfolio returns only. It tests no issuer, no default, no bond spread, and no EBITDA. Overall relevance to the credit analyst: medium-low. One finding matters: the corporate-minus-government bond return carries most of the market's news about next year's GDP.

**What we hold (checked 24 October 2026).**
- SPF GDP and CPI medians and densities, quarterly, from 1990 Q2, with `available_at` (`hy/sources/forecast_sources.py`, `load_spf`; card `forecast-spf`).
- `data/raw/backtest/equity_monthly.parquet`: monthly issuer equity returns, no daily returns (card `bharath-shumway-2008-merton-dd`).
- `hy_oas` from ICE is a stub. The source is daily when wired (card `forecast-ice-hy-oas`).
- No Fama-French factors and no mimicking portfolio in `hy/` or `scripts/`. A grep for "mimick" finds nothing.

**Link 1: path probabilities (Section 5.4).** The paths read GDP and CPI quantiles from forecasts that update each quarter. A return-based GDP-news proxy could update between survey vintages. The proxy measures news, not the level of the expectation. So use its cumulative return since the last SPF vintage as an early estimate of the next revision. It would shift the GDP mean of the path normal before the next survey arrives. Two conditions apply.
1. The paper fits `c` on the full 1953–1998 sample with GDP growth up to 1999. That is look-ahead. A point-in-time version must fit `c` on an expanding window, with GDP read at its release date and its first vintage. Framework R5 and the no-look-ahead test then cover it.
2. The paper gives no evidence on CPI news. A GDP-only proxy moves one axis of the joint normal only.

**Link 2: downside weights (Section 5.2.1).** DEF has the largest weight in the factor (Table 2, Table 8). DEF is the excess return of corporate bonds over Treasuries, so it moves against the change in the credit spread. This agrees with Gilchrist-Zakrajšek: the credit spread forecasts GDP (card `gilchrist-zakrajsek-2012-credit-spreads-business-cycle`). The proposed `m_t` already holds the EBP and the four-quarter change in `hy_oas`. A GDP-news proxy built from DEF would add the same information a second time. If we add it to the path probabilities, we must not also read the spread change in the logistic without a test that the two carry separate information. The paper does not report the DEF weight net of the spread change, so it cannot settle this.

**Link 3: `beta_sector` (Sections 5.2, 9.2).** Weak. Our `beta_sector` is the sensitivity of sector revenue growth to the GDP path gap. The paper estimates no sector loadings and no fundamentals. The loading of a sector equity return on a GDP-news factor is a different object: a return beta, not a revenue elasticity. It could serve only as a cross-check on the rank order of the cyclical class of Section 4.4.

**Section 9.2, growth versus policy split.** The split regresses the yield change on the change in the growth forecast. The SPF gives that change once a quarter. A daily GDP-news proxy could give a daily growth regressor. The QFIX version holds TERM with a positive weight (0.041, Table 8). So regressing a Treasury yield change on it is partly circular. Use the equity-only version (QEQ) for this regressor if we build one.

**Equity-based issuer inputs (distance to default, `dd_equity`).** The paper says nothing about firm default. Footnote 5 (p. 23) only suggests that SMB and HML price DEF through default risk. The follow-up work on default risk in equity returns is Vassalou and Xing (2004), which the Bharath-Shumway card cites for the iterative DD. That paper, not this one, bears on `dd_equity`. It has no card yet.

**Falsifiable test (proposed, not run).** Question: does a point-in-time market GDP-news proxy forecast the next SPF revision of GDP growth?
1. Each quarter, fit regression (9) on an expanding window from 1970. Use realised GDP growth known at that date only. Base assets: the six Fama-French portfolios, a corporate-minus-Treasury return, and a long-minus-short Treasury return.
2. Build the daily or monthly portfolio return with the weights fixed at the last fit.
3. Sum its return from the `available_at` of SPF vintage v to the deadline of vintage v + 1.
4. Regress the revision in the SPF median four-quarter GDP growth forecast, v to v + 1, on that sum. Use 1990 Q2 onwards, Newey-West errors.
5. Compare with a benchmark that uses the change in `hy_oas` over the same window only. Score with the Clark-West test.

Reject the proxy for Section 5.4 if the slope is not positive at the 5% level. Reject it also if it does not beat the `hy_oas` change benchmark in at least three of the four cycle windows 2008, 2015, 2020, 2022.

## Limits
- Equity test assets only, and only portfolios sorted by size and book-to-market. No credit asset is a test asset except DEF and TERM in footnote 5.
- DEF is an investment grade long-term corporate index return (Ibbotson). It is not high yield. The high yield weight on GDP news is not measured.
- Sample 1953–1998. It ends before 2001 and holds none of our four cycle windows. No out-of-sample test.
- The weights `c` use the full sample and final-vintage GDP. The factor is not point-in-time.
- The proxy captures only the GDP news that asset returns reflect (p. 14). It is not a forecast of the level of GDP growth.
- Individual weights are weak. In the column used to build the factor, no single weight has |t| above 1.74. The bootstrap p-value of the joint test is 0.0973 (Table 2).
- All monthly models fail the J-test and the HJ test on unscaled returns (Table 6). The claim is "as good as Fama-French", not "correct".
- The text and table notes disagree on the definitions of DEFY, TERMY, and TERM (see Data). Table 4 Panel A gives a joint p-value of 0.0126, where Table 2 gives 0.0155 for the same coefficients.

## Section touched
`docs/methodology.md` Section 5.4 (path probabilities: a candidate update between survey vintages), Section 5.2.1 (`m_t`: a warning about double counting the spread change), and Section 9.2 (a daily growth regressor for the growth and policy split). No change to any section yet. No decision page: the test above must pass first.
