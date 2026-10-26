# Folder C: capital structure arbitrage, equity-credit links, CDS-bond basis

Scope: 17 files in `CapArb/` (15 PDFs, 2 Python files). Two PDFs are the same paper (Kapadia and Pu 2012). Page numbers below are journal page numbers unless marked "PDF p.".

Main finding: only one paper gives strong, HY-tested evidence for a bond-return signal from equity-derivative data. That paper is Cao, Goyal, Xiao, Zhan (2023) on implied volatility changes. It needs option data, which we do not have. The same paper shows that a change in realized stock volatility does not replace it. All CDS-bond basis signals need CDS data. They are not buildable here. Two signals can be built from TRACE and equity data alone: equity-credit discordance (adapted from Kapadia and Pu 2012) and an equity-implied spread gap with self-calibrated volatility (a variant of a known factor).

## Triage table

| File | Title, authors, year | Topic | Relevant (yes/no) | Why |
|---|---|---|---|---|
| EBSCO-FullText-08_05_2026.pdf | Implied Volatility Changes and Corporate Bond Returns. Cao, Goyal, Xiao, Zhan. Management Science 69(3), 2023 | Option implied volatility change predicts US corporate bond returns (TRACE 2002-2017) | yes | Strongest bond-return signal in the folder. Tests HY. Also reports lagged stock return and bond abnormal volume as bond predictors. |
| Limited arbitrage between equity and credit markets (no extension, PDF 1.7, 23 pages) | Limited arbitrage between equity and credit markets. Kapadia, Pu. JFE 105, 2012 | Equity-CDS concordance measure, cap-arb trade returns | yes | Defines a nonparametric equity-credit discordance measure. It can be ported to bond spreads. |
| limited arb.pdf | Same paper as above (text extract identical) | Duplicate | yes (duplicate) | Read once. Listed with the file above. |
| CDS-bond basis and bond return predictability.pdf | CDS-bond basis and bond return predictability. Kim, Li, Zhang. J. Empirical Finance 38, 2016 | Residual CDS-bond basis predicts bond returns | yes | Bond-return predictor with IG and HY split. Needs CDS. |
| Journal of Futures Markets - 2017 - Kim - The CDS-Bond Basis Arbitrage and the Cross Section of Corporate Bond Returns.pdf | The CDS-Bond Basis Arbitrage and the Cross Section of Corporate Bond Returns. Kim, Li, Zhang. J. Futures Markets 37, 2017 | Basis factor (LMH) as priced risk factor | yes (negative HY result) | Basis factor priced in IG only. Not priced in HY. Needs CDS. |
| choi-et-al-2018-dealer-liquidity-provision-...-cds-bond-basis.pdf | Dealer Liquidity Provision and the Breakdown of the Law of One Price. Choi, Shachar, Shin. Management Science 65(9), 2019 | Dealer net buys vs basis, basis-trade unwind, Lehman-underwritten bonds | yes (event risk) | Crisis event evidence: basis-arbitrage crowding and lead-underwriter failure predict bond losses. |
| cap arb perspective.pdf | Rethinking Capital Structure Arbitrage: A Price Discovery Perspective. Avino, Lazar. J. Alternative Investments, Spring 2020 | CreditGrades cap-arb plus Hasbrouck information-share filter | yes (variant) | Adds a lead-lag filter to the equity-implied spread gap. Weak results. Needs CDS as written. |
| cap arb.pdf | Capital Structure Arbitrage: exploiting temporary mispricing between equity prices and CDS spreads using the CreditGrades model. Alber. MSc dissertation, Univ. Catolica Portuguesa, 2017 | CreditGrades cap-arb, Europe, adaptive trigger | yes (variant) | Gives the CreditGrades formulas, a self-calibrated volatility input, and an adaptive entry band. Cites Duarte et al. (2007) HY result. |
| s11156-013-0400-x.pdf | Evaluation of conducting capital structure arbitrage using the multi-period extended Geske-Johnson model. Ju, Chen, Yeh, Yang. Rev. Quant. Finance Acc. 44, 2015 | Structural model with debt maturity ladder vs CreditGrades | yes (variant, weak) | Uses debt maturity schedule in the equity-implied spread. Arbitrage profit insignificant. |
| phthesis.pdf | Capital Structure Arbitrage. Papadimitraki. MSc thesis, Univ. of Piraeus, 2018 | Merton synthetic CDS, trade CDS against 10-delta put implied vol | no | Case studies only (a few European names). No cross-sectional evidence. Needs options and CDS. |
| jdqs-12-2024-0048.pdf | Do changes in the implied volatility of stock options predict future changes in CDS spreads? Hong, Park. J. Derivatives and Quantitative Studies 33(2), 2025 | Korean ΔIV predicts ΔCDS | yes (supporting) | Out-of-sample support for Cao et al. in Korea CDS. Small sample. |
| Int Rev Finance - 2018 - Da Fonseca - The Co-Movement of CDS Spreads, Equity Returns and Volatility.pdf | The Co-Movement of CDS Spreads, Equity Returns and Volatility: Evidence from Asia-Pacific Markets. Da Fonseca, Gottschalk. Int. Review of Finance 20(3), 2020 | VAR lead-lag of CDS, equity, realized vol, 2007-2010 | no | Asia-Pacific CDS. Firm-level equity returns lead CDS changes. No bond-return test. |
| jrf-04-2014-0044.pdf | The relative informational efficiency of stocks, options and credit default swaps during the financial crisis. Amadori, Bekkour, Lehnert. J. Risk Finance 15(5), 2014 | European stock, option, CDS lead-lag | no | CDS and stock lead in the crisis. No bond test. Europe. |
| 1-s2.0-S1059056016303240-main.pdf | Liquidity basis between credit default swaps and corporate bonds markets. Kim. Int. Review of Econ. and Finance 48, 2017 | CDS liquidity Granger-causes bond liquidity, May 2009-June 2011 | no | Liquidity dynamics only. No return signal. Needs CDS. |
| ME_2019082716502954.pdf | CDS-Bond Basis Dynamic and Credit Spread Price Discovery: A Test for European Corporate and Sovereign Bond Markets. Patane, Tedesco, Zedda. Modern Economy 10, 2019 | Cointegration and price discovery CDS vs bond, Europe 2011-2018 | no | Price discovery shares only. No return signal. Low-tier journal. |
| etf_rfq_simulation.py | ETF create/redeem RFQ simulation (no author), 462 lines | Synthetic simulation of ETF basket arbitrage, RFQ fill probability, integer optimisation | no | Read as text only. Random data. No credit factor. |
| test_etf_rfq_simulation.py | 3-line runner for the file above | Script stub | no | Calls the simulation only. |

Count: 17 files triaged. 16 distinct works (one duplicate pair). 10 files relevant (9 distinct papers plus the duplicate). Factor content comes from 8 papers.

## Factors found

### F-C1. Change in option implied volatility, ΔImpVOL (source: EBSCO-FullText-08_05_2026.pdf, pp. 1378-1394)
- Status: NEW. The known list holds the variance risk premium (an IV level against realized volatility). ΔImpVOL is a one-month change in IV. Cao et al. show it is not the IV level (corr 0.08 to 0.11 with the level, Table 1 Panel B, p. 1379).
- Definition (source): 
  $$\Delta \text{ImpVOL}_{i,t} = \tfrac12\big(\Delta \text{CVOL}_{i,t} + \Delta \text{PVOL}_{i,t}\big),\qquad \Delta \text{CVOL}_{i,t} = \text{IV}^{call}_{\Delta=0.5,\,365d}(t^-) - \text{IV}^{call}_{\Delta=0.5,\,365d}(t^- - 1\text{m})$$
  Intuition: a bond is a short put on firm assets, so a rise in expected volatility lowers bond value, and bonds react late.
  - IV comes from the OptionMetrics volatility surface, delta 0.5, 365-day expiry, month-end values (p. 1379).
  - The IV date is one day before the bond price date. This skip avoids price-pressure bias (p. 1379).
  - Sort bonds monthly into deciles, value-weight by prior-month bond market cap, hold one month (p. 1380).
  - ΔCVOL − ΔPVOL (the An et al. 2014 "news" variable) does not predict bond returns in the full sample (p. 1382).
- Data needed: daily ATM 365-day call and put IV per issuer (OptionMetrics). TRACE month-end prices. We lack option data. The repo cannot build this signal today.
- Evidence (source):
  - TRACE, July 2002 to August 2017, 881,625 bond-months, 2,327 firms, IG and HY (p. 1379).
  - Decile 10−1 on ΔCVOL+ΔPVOL: −0.60%/month raw, 11-factor alpha −0.98%/month, t = −5.57 (pp. 1376, 1382).
  - Fama-MacBeth slope on ΔImpVOL: −0.051 (t = −4.55) alone, −0.047 (t = −4.89) with all controls (Table 5, p. 1387).
  - HY: within rating quintile 4 (BB) the 5−1 alpha is −0.51% (t = −2.10). Within quintile 5 (B and below) it is −0.69% (t = −2.14). AAA-AA gives −0.09% (t = −1.44) (Table 4, p. 1384).
  - Long maturity and illiquid bonds show the largest effect: −1.32% and −1.19% per month (Table 4, p. 1384).
  - Net of costs, HY ("Junk"), EHP $1M cost of 30 bp: bond+stock alpha −0.54%/month, t = −1.69. At $100K cost or the Bao-Pan-Wang cost the effect is gone (Table 11, p. 1394).
  - Channel: ΔImpVOL predicts the next-month change in EDF, CHS default probability, CDS spreads and rating downgrades (Tables 6-7, pp. 1389-1391).
  - Predictability is 5 to 8 times larger on rating announcement days (p. 1377).
  - The effect decays fast after one month (Online Appendix Table A1, cited p. 1383).
  - Supporting evidence: Hong and Park (2025) find a High−Low ΔIV quartile spread of +4.392 bp per month in future Korean CDS changes (10% level), April 2005 to October 2012. Ex-crisis it is +3.703 bp (5% level) (jdqs-12-2024-0048.pdf, pp. 158-159).
- Important for us (source): a change in stock realized volatility does not substitute. In Table 5 model (4) the ΔStock Vol slope is 0.040 (t = 1.43). In model (5) it is 0.059 (t = 1.80), which has the wrong sign. The ΔBond Vol slope is −0.044 (t = −1.39) (p. 1387).
- HY applicability: high if option data exist. The effect is larger in HY and in long bonds. Many US HY issuers are public and have listed options. Costs consume most of the HY alpha at small trade size.
- Fit to our signals: new signal. It feeds methodology section 8 as an event-risk and short-horizon overlay. It also feeds the forward PD module, because it predicts ΔEDF and downgrades.
- Test (proposal): buy OptionMetrics IV for 2002-2017 on our TRACE HY universe. Compute the monthly cross-sectional rank IC of −ΔImpVOL against next-month bond excess return within HY. Pass if the mean IC is > 0.02 with Newey-West t > 2. The decile 10−1 net of 30 bp cost must also be negative with t < −1.65.

### F-C2. One-month lagged stock return as a bond-level predictor (source: EBSCO-FullText-08_05_2026.pdf, p. 1387)
- Status: variant of EMC (equity momentum, 1/3/6 m). New evidence: one-month horizon, bond level, 2002-2017 TRACE, with ΔImpVOL and volatility controls.
- Definition (source): $\text{LagStockRet}_{i,t} = R^{stock}_{i,t-1\to t}$, the issuer stock return over the prior month. The regression uses it as a control with next-month bond excess return on the left side. Intuition: bonds absorb equity news with a lag.
- Data needed: CRSP or our equity returns, TRACE month-end prices. We have both.
- Evidence (source): Fama-MacBeth slope 0.070 (t = 15.58) to 0.080 (t = 14.83) across models (2)-(5), IG and HY pooled, July 2002 to August 2017 (Table 5, p. 1387). The paper gives no HY-only split for this control.
- HY applicability: high. Equity sensitivity rises as rating falls (Kapadia and Pu 2012, p. 545, citing Schaefer and Strebulaev 2008: bond-return sensitivity of 0.70 at quasi-leverage 0.20 against 24.17 at 0.50).
- Fit to our signals: S2 fundamental momentum, or the EMC leg of OneScore. Proposal: add the 1-month lag as a separate horizon, not only inside the sqrt-scaled 1/3/6 m blend.
- Test (proposal): within HY bonds, run monthly Fama-MacBeth of next-month excess return on the 1-month stock return, with controls for EMC(3,6m), rating, maturity and lagged bond return. Pass if the slope t > 3 in at least three of the four cycles 2008, 2015, 2020, 2022.

### F-C3. Bond abnormal trading volume (source: EBSCO-FullText-08_05_2026.pdf, p. 1387)
- Status: NEW. It is TRACE-only.
- Definition (source): "abnormal trading volume of bonds ... calculated using the procedure of Gervais et al. (2001)". The main text gives no exact window. Our proposed reconstruction:
  $$\text{AbnVol}_{b,t} = \ln V_{b,t} - \frac{1}{12}\sum_{k=1}^{12}\ln V_{b,t-k}$$
  Here $V$ is the monthly TRACE par volume of bond $b$. Intuition (source, via Gervais et al.): high volume draws attention and raises later prices, and low volume does the reverse.
- Data needed: TRACE par volume per bond per month. We have this.
- Evidence (source): slope +0.034 (t = 2.10) in model (5), with 211,656 bond-months, IG and HY pooled, 2002-2017. The stock abnormal volume slope is −0.016 (t = −0.89) (Table 5, p. 1387). This is one specification only, used as a control. The paper gives no HY split.
- HY applicability: medium. HY bonds trade less often, so the volume signal has more noise. Volume spikes in HY often come with news, so they may also carry event risk with the opposite sign.
- Fit to our signals: new signal. It could also condition S6 forced-flow signals.
- Test (proposal): HY TRACE 2005-2024, monthly quintile sort on AbnVol, one-month hold. Pass if Q5−Q1 is > 0 with Newey-West t > 2 after control for lagged bond return (reversal), and if the rank IC is positive in at least three of the four cycles.

### F-C4. Equity-credit discordance on bond spreads (source: Limited arbitrage between equity and credit markets, pp. 546, 551, 553-554)
- Status: NEW. The known list has no concordance-based signal.
- Definition (source, for CDS): for firm $i$ with $M$ daily observations,
  $$\hat k_i = \sum_{\tau=1}^{M-1}\sum_{k=1}^{M-\tau} \mathbb 1\big[\Delta CDS^{\tau}_{i,k}\,\Delta P^{\tau}_{i,k} > 0\big],\qquad \kappa_i = \frac{4\hat k_i}{M(M-1)} - 1$$
  In the Merton model stock and credit always move in opposite spread direction, so $\kappa = -1$ means full integration. A higher $\kappa$ means less integration (Eq. 2-3, p. 546).
  - Trade rule (source): open a trade when, over the past $\tau$ = 5 or 10 business days, $\Delta CDS\cdot\Delta P > 0$ and $|\Delta P/P| > 3\%$. Go long stock and buy protection if the stock fell. Do the reverse if it rose. Hold 1 or 2 months, with a stop at 10% of equity. The hedge ratio comes from a regression of monthly ΔCDS on stock returns (p. 553).
- Our proposal (no CDS): replace ΔCDS with the issuer-level median TRACE G-spread change $\Delta S_i$ over the same 5 business days, using only bonds with trades at both ends. Bond-only signal:
  $$D_{i,t} = \text{sign}\big(r^{eq}_{i,t-5\to t}\big)\cdot \mathbb 1\big[\Delta S_{i,t-5\to t}\; r^{eq}_{i,t-5\to t} > 0\big]\cdot \mathbb 1\big[|r^{eq}_{i,t-5\to t}|>3\%\big]$$
  $D = +1$ means overweight the bond and $D = -1$ means underweight it. A discordant move has the spread change and the stock return with the same sign.
  In words: if the stock fell by more than 3% and the bond spread tightened, expect the bond to lose, so underweight it. If the stock rose by more than 3% and the spread widened, overweight the bond. The paper does not separate which leg converges. The bond leg may carry none of the return.
- Data needed: daily equity returns, daily TRACE G-spreads per issuer. We have both.
- Evidence (source, CDS, 214 US firms, January 2001 to March 2009):
  - 5-day discrepancies are 40.75% of all observations. In HY they are 38.79%, with a mean absolute CDS move of 19.75 bp against the model sign (Table 4, p. 551).
  - Mean excess return per trade, 1-month rule, all firms: 0.24% pre-crisis and 1.21% in the crisis. The portfolio earns over 6% a year with a Sharpe ratio of 0.45 (pp. 553-554).
  - HY only: −0.05% per trade pre-crisis (1-month rule) and 0.27% (2-month rule). In the crisis it is 0.19% and 3.25% (Table 6, p. 554). The source gives no t-statistics per rating group.
  - Integration falls when CDS liquidity falls and idiosyncratic risk rises (p. 544).
- HY applicability: medium. The construction is cheap and fits HY, where equity sensitivity is high. But the source HY trade evidence is weak before 2008. TRACE spread noise in HY may create false discordance.
- Fit to our signals: new signal. It works as a short-horizon overlay on S2. The rolling $\kappa_i$ can also act as a conditioning variable: trust S1 fair-value signals less when $\kappa_i$ is high.
- Test (proposal): HY issuers with daily TRACE and equity data, 2005-2024. Form $D_{i,t}$ weekly and measure the 20-day bond excess return. Pass if the mean bond-leg return of $D$-signed positions is > 0 with t > 2 after a 30 bp round-trip cost, and if the hit rate is > 52%.

### F-C5. Equity-implied (CreditGrades) spread gap with self-calibrated volatility and adaptive trigger (source: cap arb.pdf, PDF pp. 21-25 and 29; cap arb perspective.pdf, pp. 77-79 and 83; s11156-013-0400-x.pdf, pp. 109-110)
- Status: variant of the Correia-Richardson-Tuna theoretical spread gap and of Bharath-Shumway distance to default. There are three new pieces:
  1. Calibrate asset volatility to the market spread, then use its rolling 1-year mean (Wojtowicz 2014, as used by Alber, PDF p. 25).
  2. Use an issuer-specific adaptive entry band (Alber, PDF p. 29).
  3. Trade only the lagging market by information share (Avino and Lazar, pp. 78-79).
- Definition (source): CreditGrades survival probability
  $$P(t)=\Phi\!\Big(-\tfrac{A_t}{2}+\tfrac{\ln d}{A_t}\Big)-d\,\Phi\!\Big(-\tfrac{A_t}{2}-\tfrac{\ln d}{A_t}\Big),\quad d=\frac{S_0+\bar L D}{\bar L D}e^{\lambda^2},\quad A_t^2=\Big(\sigma_S^{*}\frac{S^*}{S^*+\bar L D}\Big)^2 t+\lambda^2$$
  - Inputs: $\bar L = 0.5$, $\lambda = 0.3$, and $R = 0.3$ for the spread formula. $D$ is debt per share: short-term plus long-term interest-bearing debt plus 0.5 × other liabilities, less minority interest capped at 50% (PDF pp. 21-24).
  - Kiesel and Veraart (2008) show this formula is an approximation. It is poor when the share-to-debt ratio is below 0.796 (PDF p. 24). That ratio is common in HY, so use the bivariate-normal exact form.
  - Entry rule (Alber): enter when $|s^{model}-s^{mkt}| > \bar d_c + a\,\sigma_d$. Here $\bar d_c$ is the c-day mean absolute gap, with $a = 4$ and $c = 20$ days chosen by Sharpe ratio in-sample. Exit inside 1%, with a maximum hold of 180 days (PDF p. 29).
  - Avino-Lazar filter: fit a VECM on the market spread and the equity-implied spread. Compute the Hasbrouck information share $IS$. Trade the credit leg only when $IS_{credit} < 20\%$, meaning credit lags (pp. 77-79).
  - Intuition: the equity market prices default risk. When the bond spread departs from the equity-implied spread more than usual for that issuer, the gap tends to close.
- Our proposal (no CDS): use the issuer TRACE G-spread at matched duration in place of the CDS spread. Use the Compustat point-in-time liabilities for $D$.
- Data needed: equity price, shares, Compustat liabilities (point in time), TRACE G-spread, Treasury curve. We have all of these.
- Evidence (source, all CDS):
  - Alber: 67 European firms, 2008-2015, annual alpha 2.3%. It is 5.7% in 2008-2011 and 0.25% (not significant) in 2012-2015. 82% of the firms are IG and only 5 are HY (PDF pp. 2, 26).
  - Duarte, Longstaff, Yu (2007), as cited by Alber: after fees, only the highest-trigger strategy in the speculative-grade universe has a significant alpha, 0.680% per month at the 10% level (PDF p. 18).
  - Avino-Lazar: US and European CDS, 2005-2009. Pre-crisis Sharpe ratios are negative for every strategy and grade. In the crisis, speculative grade with θ = 2 gives Strategy 4 a Sharpe ratio of 1.01 (mean 3.62%/month, N = 24 months). IG Strategy 3 gives 1.24 (Exhibit 5, p. 83).
  - Ju et al.: 369 North American obligors, 2004-2008. Adding a multi-period debt maturity ladder (extended Geske-Johnson) gives model spreads closer to market than CreditGrades, but the arbitrage profit is insignificant (pp. 109-110).
- HY applicability: medium. Theory says the gap matters most in HY. The evidence is crisis-driven and CDS-based. Equity-hedged trade legs are not needed for a long-only bond tilt.
- Fit to our signals: S1 fair value residual. It adds an equity-market fair spread beside our fundamental fair spread. The Ju et al. debt-ladder variant fits the F5 claims schedule from SEC filings.
- Test (proposal): HY TRACE 2005-2024. Compute the monthly gap $g = s^{TRACE} - s^{CG}$, standardised by the issuer's own rolling 20-day band. Pass if the next-month rank IC of $g$ against bond excess return is > 0 (wide bonds outperform), with t > 2 after control for S1 and EMC. Also require incremental IC over Correia-Richardson-Tuna > 0.01.

### F-C6. Residual CDS-bond basis (source: CDS-bond basis and bond return predictability.pdf, pp. 310-314 and 328)
- Status: variant of "bond-CDS basis on fallen angels". New definition: strip the frictions, then use the residual for all bonds.
- Definition (source): $\text{Basis}_{i,t} = CDS_{i,t,\tau} - Z_{i,t,\tau}$, with the CDS interpolated to bond maturity and $Z$ the Z-spread over the swap curve. Run a daily cross-sectional regression (Bai and Collin-Dufresne 2014) of the basis on these frictions:
  - bond turnover, liquidity betas, and counterparty beta to a primary-dealer stock index;
  - CDS betas to LIBOR-OIS and to the repo spread;
  - a collateral-quality index and the stock market beta.
  The regression runs separately for IG and HY. $\text{Basis}^{resid} = \text{Basis} - \widehat{\text{Basis}}$ (pp. 310-311, Appendix A pp. 330-331). Intuition: a negative residual means the bond is cheap against CDS after frictions, so the bond price rises.
- Data needed: Markit CDS curve (we lack), TRACE, swap curve, Compustat, CRSP.
- Evidence (source):
  - 2003-2008, 765 IG and 229 HY firms (p. 311).
  - The Low−High quintile earns an abnormal 1.79% over 20 days, 2.40% over 40 days and 2.68% over 60 days (p. 309).
  - Fama-MacBeth slope −1.67 (t = −26.35) at 20 days, all bonds (Table 2, p. 314).
  - HY slopes range from −0.87 to −1.65, against −1.68 to −2.67 for IG (p. 328).
  - Kim, Li, Zhang (2017, J. Futures Markets) find the LMH basis factor earns about 3% a year in IG (p. 836). It is not priced in HY ("almost non-existent", PDF p. 20, journal p. 855).
- HY applicability: low for us. It needs CDS, and HY basis effects are weaker.
- Fit to our signals: S4 capital structure relative value, if CDS data ever arrive.
- Test (proposal, only with CDS): HY subsample 2009-2024. Pass if the 20-day Fama-MacBeth slope on the residual basis is < 0 with t < −3 after a 30 bp cost.

### F-C7. Dealer-distress and basis-unwind event risk (source: choi-et-al-2018-...-cds-bond-basis.pdf, pp. 4113-4117)
- Status: NEW, as an event-risk flag. It is not a return factor for normal periods.
- Definition (source):
  - $LU_b = 1$ if Lehman Brothers is the lead underwriter of bond $b$ (from Mergent FISD).
  - $\text{BasisArb1}_b = -\text{basis}_b(\text{Aug 2008}) \times \mathbb 1[\text{maturity} \in [4.5, 5.5]\text{y}]$, a proxy for crowded negative-basis trades.
  - $CDSYES_b$ flags a bond whose issuer has a quoted CDS.
  - Intuition: the lead underwriter makes the market in its bonds. When that dealer fails, or when levered basis traders unwind, the bond loses liquidity support (pp. 4113, 4117).
- Our proposal: generalise to "lead-underwriter or main-dealer distress". Flag bonds whose lead underwriter shows a large equity drawdown or CDS jump. Use the flag as positional event risk in the events module.
- Data needed: FISD lead underwriter field (our repo lists no FISD). Bank equity prices, which we have.
- Evidence (source): September 2008, Lehman-underwritten bonds return 2.8% less than other bonds (Table 7, p. 4117). With CDS, the extra drop is −4% (10% level). Bonds with CDS return 2% per month less over September to December 2008 (5% level, p. 4115). A one-standard-deviation rise in BasisArb2 lowers the monthly return by about 2.5% (p. 4115). The sample is IG and HY, 2005-2009, with one event.
- HY applicability: medium. HY bonds depend more on the underwriter's market-making, but the evidence rests on one event.
- Fit to our signals: methodology `events` module (event-driven positional risk). New event type.
- Test (proposal): event study over dealer-stress episodes (2008, March 2020, March 2023 bank stress). Pass if bonds whose lead underwriter is in the worst bank-equity decile underperform matched bonds (same rating, maturity bucket) by > 1% over 20 days, with t > 2.

## Top 3

1. ΔImpVOL (F-C1, NEW). It has the strongest and cleanest HY evidence in the folder: B-and-below alpha of −0.69%/month (t = −2.14), and it predicts downgrades and ΔEDF. The one blocker is the missing option data, and the source shows that realized-vol change does not replace it.
2. Equity-credit discordance on TRACE spreads (F-C4, NEW). It can be built today from TRACE and equity data. Its nonparametric form avoids model error. The source HY evidence is weak (−0.05% per trade pre-crisis), so it needs our own test before use.
3. Bond abnormal trading volume (F-C3, NEW). It is TRACE-only and costs nothing to build. The source gives a positive slope (t = 2.10) as a control, but there is no HY split and only one specification.

Note: the most promising buildable variant is the CreditGrades spread gap on TRACE spreads (F-C5, variant of the Correia-Richardson-Tuna spread gap). Use the exact Kiesel-Veraart survival formula for HY leverage.

## Files not read in full
- None unreadable. All PDFs gave text. The Avino-Lazar Exhibit 1 trading-rule table has an encoded font. The rules were taken from the body text (pp. 78-79). Kapadia-Pu Table 6 signs were checked on the page image, because text extraction drops minus signs.
