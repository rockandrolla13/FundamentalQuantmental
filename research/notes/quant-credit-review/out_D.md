# Batch D: factor models and factor pricing

Scope: 27 files in `Factors/` under `/home/ak/Documents/Quant Credit/`. Page numbers are PDF pages unless the text says "journal p.".
Each block separates three things: **Source** (what the paper says), **Data** (what we have), and **Proposal** (what we decide or test).

## Triage table

| File | Title, authors, year | Topic | Relevant | Why |
| --- | --- | --- | --- | --- |
| 1-s2.0-S0165176519302010-main.pdf | Day-of-the-week effect in anomaly returns: international evidence. Chiah, Zhong, 2019 (Econ. Letters) | QMJ premium by weekday, 24 equity markets | no | Equity calendar effect. Monday QMJ premium is 2.89x its daily mean (p. 1). No credit content. A cheap HY junk-by-weekday check is possible but low value. |
| 1-s2.0-S0169207010000051-main.pdf | Finding profitable forecast combinations using probability scoring rules. Grant, Johnstone, 2010 (IJF) | Rank and pool probability forecasters by scoring rules, Kelly bets | yes (low) | Method to weight external PD and default-rate forecasters (see Methods M10). |
| 1-s2.0-S0304405X16301490-main.pdf | Momentum crashes. Daniel, Moskowitz, 2016 (JFE) | Momentum crash forecast and dynamic weight | yes | Crash control for our bond and equity momentum legs (variant of momentum). |
| 1-s2.0-S0304407617301677-main.pdf | Using PCA to estimate a high dimensional factor model with high-frequency data. Aït-Sahalia, Xiu, 2017 (J. Econometrics) | Number of factors, low rank plus sector-block covariance | yes | Estimator for the number of credit factors and a sector-block residual covariance (M2). |
| 1-s2.0-S0304407618301696-main.pdf | Large-dimensional factor modeling based on high-frequency observations. Pelger, 2019 (J. Econometrics) | HF PCA, continuous vs jump factors, perturbed eigenvalue ratio | yes (method) | Jump and continuous factor split, number-of-factor test (M2). |
| 1-s2.0-S0304407618301702-main.pdf | Knowing factors or factor loadings, or neither? Dai, Lu, Xiu, 2019 (J. Econometrics) | Covariance with noisy, asynchronous data: TSR vs CSR vs PCA | yes | TRACE trades are noisy and asynchronous. Refresh-time and pre-averaging apply (M3). |
| 1-s2.0-S0304407620300129-main.pdf | High-frequency factor models and regressions. Aït-Sahalia, Kalnina, Xiu, 2020 (J. Econometrics) | Time-varying beta regression, idiosyncratic vol and jumps | yes | Idiosyncratic jump share of issuer equity as a credit signal (factor F12). Duplicate of ssrn-3319890. |
| 1-s2.0-S0304407623000131-main.pdf | Estimation of common factors for microstructure noise and efficient price (DPCA). Li, Chen, Linton, 2023 (J. Econometrics) | Factor structure in microstructure noise | yes (low) | Dealer-wide common noise in TRACE prints may bias bond factor estimates (M3). |
| 1-s2.0-S0378426604001074-main (1).pdf | Factors affecting the valuation of corporate bonds. Elton, Gruber, Agrawal, Mann, 2004 (JBF) | Pricing errors within rating class vs bond traits | yes | Five priced traits beyond the letter rating: notch, split rating, bond-vs-issuer rating, coupon, new issue (F1 to F4, M1). IG only. |
| 1-s2.0-S0378426615002824-main.pdf | A new approach to statistical arbitrage: dynamic factor models of prices. Focardi, Fabozzi, Mitov, 2016 (JBF) | Price-level vs return-level dynamic factor models, DM test, stat-arb test | yes (method) | Spread levels mean-revert. A level-based factor model and the stat-arb test fit S1 (M5). |
| 1-s2.0-S0927539811000041-main.pdf | Residual momentum. Blitz, Huij, Martens, 2011 (JEF) | Momentum on factor-model residuals | yes | Variant of bond momentum (F5). Equity evidence. |
| 1-s2.0-S1544612325002272-main.pdf | Firm-specific versus systematic momentum. Graef, Hoechle, Schmid, 2025 (FRL) | Split momentum into systematic and idiosyncratic parts | yes | Evidence that the idiosyncratic part carries momentum (F5). |
| 2015-09_MarkusPelger.pdf | Understanding systematic risk: a high-frequency approach. Pelger, 2015 (WP) | Empirical HF factors for S&P 500 | no | Empirical companion of the 2019 paper. Equity results only: four continuous factors (market, oil, finance, electricity), one jump factor (p. 1). |
| 2f08da6e_..._604.pdf | Quantcraft: The return of the machines (N-LASR). Tomasi, Deutsche Bank, 2020 | AdaBoost alpha aggregation, equity | yes (method) | Signal aggregator for our composite (M8). |
| 4729290.pdf | Optimal option market making and volatility arbitrage. Lucic, Tse, 2024 (WP) | Option quotes via HJB | no | Option market making. No credit factor. We lack option data. |
| Credit Factor Framework (PDF, no extension) | Credit Factor Framework v0.85. AK, undated draft | Desk credit factor plan: HCA, TS-PCA, CS-PCA, panel regressions, RAMIC, N-LASR for bonds | yes | Curve slope, curvature, term premium residual, fundamental composite, RAMIC, permutation R² (F7 to F10, M6). |
| EBSCO-FullText-08_05_2026.pdf | Systematic momentum: a new class of price patterns. Li, Yuan, Zhou, 2025 (Mgmt. Sci.) | Momentum in the characteristic-explained return | yes | New signal (F6). Authors cite a corporate bond follow-up (p. 22). |
| Fundamental Factors for Banks.pdf | Building fundamental factors for banks. Ward, Shah, Tentes et al., Deutsche Bank, 2019 | Bank-specific value, asset quality, balance sheet, profitability | yes (low) | Fills a gap: our leverage metrics fail for banks (F11). Equity evidence only. |
| Quantitative Economics - 2016 - Chang - ... .pdf | Evaluating factor pricing models using high-frequency panels. Chang, Choi, Kim, Park, 2016 (QE) | Time-change sampling for valid factor tests | yes (method) | A variance clock for our factor tests (M4). |
| Robust High-Dimensional Volatility Matrix Estimation ... .pdf | Robust high-dimensional volatility matrix estimation for HF factor model. Fan, Kim, 2018 (JASA) | Huber realized vol plus POET | yes (low) | Heavy tails in bond returns. Robust input to the covariance (M2). |
| d3ea8aa0_..._604.pdf | Global Factor Monitor. Deutsche Bank, Nov 2020 | Monthly ARP performance note | no | Performance commentary. Credit appears only inside cross-asset carry. No new definition. |
| hhad006_supplementary_data.pdf | Factor momentum, Internet Appendix. Arnott, Kalesnik, Linnainmaa, 2023 (RFS) | Factor momentum vs industry momentum, simulations | yes | Factor-level timing for our signal set (F13). Appendix only. Main paper is not in the folder. |
| hhw107_supp.pdf | Mispricing factors, Online Appendix. Stambaugh, Yuan, 2017 (RFS) | Robustness tables for M-4 equity model | no | Equity robustness tables. No credit content. |
| hhy131 (1).pdf | Replicating anomalies. Hou, Xue, Zhang, 2020 (RFS) | 452 anomalies, NYSE breakpoints, value weights, t hurdles | yes (method) | Test protocol for every new signal (M7). |
| nbag006.pdf | Multifactor timing with deep learning. Cotturo, Liu, Proner, 2026 (JFEC) | Multitask LSTM factor timing | yes (method) | Candidate structure to replace S7 (M9). |
| ssrn-3319890.pdf | High-frequency factor models and regressions. Aït-Sahalia, Kalnina, Xiu, 2019 (WP 19-04) | Same paper as 1-s2.0-S0304407620300129 | yes (duplicate) | Read the journal version. |
| ssrn-4021620.pdf | The high-frequency factor zoo. Aleti, 2022 (WP) | Continuous vs jump vs semijump premia, 224 HF equity factors | no | Needs intraday equity factor portfolios. Finding: most market premium comes from jump risk (p. 2). No direct credit use now. |

Counts: 27 files triaged. 21 relevant (one is a duplicate). 6 not relevant.

## Factors found

### F1. Split rating between agencies (source: Elton et al. 2004, pdf p. 10 Table 3, p. 15 Table 7)
- Status: NEW. The repo has no split-rating feature.
- Definition. Source: within a Moody's rating class, a bond that S&P rates lower trades cheaper, and a bond that S&P rates higher trades richer.
  $$\text{SPLIT}_i = \text{notch}^{S\&P}_i - \text{notch}^{Moody's}_i, \qquad D^{+}_i = \mathbb{1}\{\text{SPLIT}_i > 0\},\ D^{-}_i = \mathbb{1}\{\text{SPLIT}_i < 0\}$$
  Intuition: the second agency adds information that the first one does not hold. Use notches, so Baa vs BBB+ counts as a split (p. 9). Peer group: rating class x sector, per month.
- Data needed: issue ratings from two agencies with dates. We lack ratings after Feb 2017. Proposal: test on 2002 to Feb 2017 only, or buy a ratings feed.
- Evidence. Source: Lehman (Warga) IG data, 1987 to 1996, trader-priced bonds, Aa to Baa. The pricing error for "S&P lower" and "S&P higher" differs with t-scores from 1.0 (Financial Aa) to 16.1 (Financial A) (p. 10). In the joint regression, the split dummies have the expected sign in all cases and are significant at 1% in all but one (p. 15). IG only.
- HY applicability: medium. Split ratings are more common near the BB to B boundary. Ratings data after 2017 is the blocker.
- Fit to our signals: extends S6 (rating migration) and the ESP peer cell of Section 7.2.
- Test. Signal: residual of log spread on the rating x sector x maturity cell, regressed on `SPLIT`. Horizon: 3 months forward excess return of bonds with `SPLIT < 0` against `SPLIT > 0` in the same cell. Metric: rank IC of `-SPLIT` with forward excess return, 2002 to 2016. Pass: IC > 0 with t > 2, and the contemporaneous spread loading has the source's sign.

### F2. Bond rating vs issuer rating gap (source: Elton et al. 2004, pdf p. 13 Table 6, p. 15 Table 7)
- Status: variant of S4 (capital structure relative value).
- Definition. Source: a bond rated above its issuer has a model price above its invoice price. So the market prices it cheaper than its bond-rating peers. A bond rated below its issuer trades richer than its bond-rating peers (p. 13).
  $$G_i = \text{notch}(\text{bond}_i) - \text{notch}(\text{issuer}_i), \qquad \text{error}_i = P^{model}_i - P^{invoice}_i = a + b_1 \mathbb{1}\{G_i>0\} + b_2 \mathbb{1}\{G_i<0\} + \dots$$
  Intuition: agencies put more weight on recovery than the market does. The market puts more weight on default probability, which is the same for all bonds of one issuer.
- Data needed: issue and issuer ratings, or our own seniority and recovery (`recovery_k_adj`, Section 6.2). Proposal: replace the agency notch gap with our model recovery gap, so the test does not need ratings after 2017.
- Evidence. Source: IG, 1987 to 1996. t-scores between "higher" and "lower" groups range from 7.8 to 34.9, except Aa financials (0.86) (p. 13). In Table 7, the signs agree in all 10 groups with data, and 7 are significant at 1% (p. 15-16).
- HY applicability: high. HY structures have wide notching (secured vs unsecured vs holdco). The source effect is a statement that peer cells by bond rating misprice notched bonds.
- Fit to our signals: S4 and the ESP cell definition in Section 7.2.
- Test. Signal: the spread gap to bond-rating peers, regressed on our model `LGD` gap to the issuer's senior unsecured debt. Horizon: 6 months. Metric: rank IC of the residual after the regression against the residual before it. Pass: the regression-adjusted ESP has a higher 6-month IC than plain ESP, with a paired t > 2.

### F3. Notch within letter, scaled by maturity (source: Elton et al. 2004, pdf p. 9 Table 2, p. 15 Table 7)
- Status: variant of ESP (Dynkin et al. ch. 13) peer cell.
- Definition. Source: plus-rated bonds have negative pricing errors and minus-rated bonds have positive pricing errors against a letter-class curve. The effect grows with maturity (p. 9).
  $$V_{1,i} = \text{maturity}_i \cdot \mathbb{1}\{+\}_i, \qquad V_{2,i} = \text{maturity}_i \cdot \mathbb{1}\{-\}_i$$
  Intuition: a letter-class curve is too coarse, and the coarseness costs more for long bonds.
- Data needed: notched ratings with dates. Our ESP cell uses "rating class". Proposal: confirm that `rating class` in `hy.peers` is the notch, not the letter.
- Evidence. Source: for minus vs flat Baa industrials the gap is over 1% of invoice price (p. 9). Effect size rises as rating falls (p. 9). IG only.
- HY applicability: medium. HY cells are thin. Notch cells will often fail the 5-issuer rule.
- Fit to our signals: Section 7.2 peer cell and the fallback chain.
- Test. Signal: ESP on notch x sector x maturity against ESP on letter x sector x maturity. Horizon: 12 months. Metric: rank IC beyond spread. Pass: the notch version beats the letter version by a paired t > 2. A failure keeps the letter cell.

### F4. Coupon and new-issue effects (source: Elton et al. 2004, pdf p. 11 Table 4, p. 12 Table 5)
- Status: variant of the coupon and price effect and of the new-issue concession and seasoning (Dynkin et al.). New IG evidence only.
- Definition. Source: demeaned coupon $c_i - \bar c$ and a dummy $\mathbb{1}\{\text{age}_i < 1\text{y}\}$. High coupons price cheap. Bonds in their first year price rich (p. 11-12).
- Evidence. Source: first-year bonds trade at a premium with t from 2.3 to 21.3 (p. 11). Coupon groups differ with F = 122.49 in a two-way ANOVA for Baa industrials (p. 12). The authors say coupon may proxy for something other than tax (p. 12, note 11). IG only.
- HY applicability: low as a new factor. The repo already holds both effects. In HY the coupon effect mixes with call option value.
- Fit: Section 7.2 Term and Liquidity blocks. No new test needed.

### F5. Residual bond momentum (source: Blitz et al. 2011, pdf p. 3-5; Graef et al. 2025, pdf p. 3-4)
- Status: variant of momentum (Houweling and van Zundert 2017, Israel et al. 2018).
- Definition. Source (Blitz): regress each stock's excess return on factors over months t-36 to t-1. Sum the residuals over months t-12 to t-2. Divide by their standard deviation over the same window. Leave out alpha (p. 3-4).
  $$r_{i,\tau} = \alpha_i + \beta_i^{\top} f_\tau + \varepsilon_{i,\tau}, \quad \tau \in [t-36, t-1], \qquad RMOM_{i,t} = \frac{\sum_{\tau=t-12}^{t-2} \hat\varepsilon_{i,\tau}}{\hat\sigma(\hat\varepsilon_{i,t-12:t-2})}$$
  Intuition: total-return momentum bets on the persistence of factor returns. The residual keeps only the issuer news that diffuses slowly.
  Proposal for bonds: use excess return over duration-matched Treasuries. Use factors: HY market excess return times DTS, sector excess return, and rating-bucket return. Need at least 24 of 36 months.
- Data needed: monthly TRACE bond excess returns, DTS, sector and rating labels. All in the repo (ratings before 2017, or our model rating bucket after).
- Evidence. Source (Blitz, CRSP, 1930 to 2009, equity): at a 1-month hold, residual momentum earns 11.20% a year at 12.49% volatility, Sharpe 0.90. Total-return momentum earns 10.26% at 22.70%, Sharpe 0.45 (p. 5, Table 2). Over 2000 to 2009 total-return momentum lost 8.5% a year and residual momentum earned 4.7% (p. 1). Source (Graef, CRSP, 1966 to 2019, equity): sorts on the medium-term idiosyncratic return earn 0.571% a month (t 3.24). Sorts on the medium-term systematic return earn 0.200% (t 1.00) (p. 4, Table 2). Equity only.
- HY applicability: medium-high. Bond momentum in HY is weak and has crash risk in junk rallies. A residual version removes the beta bet that hurts in rebounds (Blitz p. 1-2 on 2009).
- Fit to our signals: new signal in the momentum family. It also gives a clean test of S2, which is a residual-type momentum on fundamentals.
- Test. Signal: RMOM against total bond momentum, 12-2 months, DTS-neutral quintile legs. Horizon: 1 and 3 months. Metric: Sharpe after a 50 bp round-trip cost, and rank IC by cycle. Pass: RMOM Sharpe above total momentum Sharpe, and IC > 0 in at least three of 2008, 2015, 2020, 2022.

### F6. Systematic momentum on characteristic premia (source: Li, Yuan, Zhou 2025, pdf p. 5 Eq. 2-4, p. 21 Table 9)
- Status: NEW.
- Definition. Source: each period, run a cross-sectional regression of returns on rank-standardised characteristics known at the prior close. The fitted part is the systematic component SYS. Sort on past SYS (p. 5).
  $$c_{s,t-1,j} = \frac{\text{rank}_{s,j}/(n+1) - \overline{\text{rank}}}{\sum_s |\text{rank}_{s,j}/(n+1) - \overline{\text{rank}}|}, \quad r_{s,t} = \alpha_t + \sum_{j=1}^{p} c_{s,t-1,j}\,\theta_{t,j} + \epsilon_{s,t}, \quad SYS_{s,t} = \sum_j c_{s,t-1,j}\,\hat\theta_{t,j}$$
  Intuition: arbitrageurs correct mispricing across many characteristics slowly. So the part of a return that the characteristics explain persists, through own and cross lead-lag of premia (p. 2).
  Proposal for bonds: characteristics = our state and signal fields (spread, DTS, ESP, leverage, coverage, S1 to S6 scores, rating bucket, age, issue size proxy). Form monthly. Sort on last month's SYS.
- Data needed: monthly bond excess returns and the characteristic panel. All in the repo.
- Evidence. Source: Russell 1000, TAQ 1993 to 2020 and CRSP. Monthly SMOM earns 16.58% a year (t 6.44), Sharpe 0.82. JT momentum earns 13.41%, Sharpe 0.55 (p. 21, Table 9). Factor momentum loses its alpha after a control for SMOM (p. 20). The intraday version has a net Sharpe 0.62 after cost (p. 14). The authors state the pattern holds for corporate bonds in follow-up work (Beckmeyer et al. 2023), with no numbers in this file (p. 22). Equity evidence only.
- HY applicability: medium. The cross-section of HY bonds is small, so the regression of month-t returns on p characteristics needs p small (about 10 to 15) or a ridge penalty.
- Fit to our signals: new signal. It also tests whether the signal premia of Section 8 are persistent, which bears on the IC weights of the composite.
- Test. Signal: SYS from a ridge cross-sectional regression on 12 characteristics. Horizon: 1 month. Metric: DTS-neutral quintile spread and rank IC, 2005 to 2026. Pass: t > 2.78 (the HXZ hurdle, M7) and IC > 0 in at least three of the four stress cycles.

### F7. Dynamic crash-managed momentum weight (source: Daniel, Moskowitz 2016, pdf p. 7, p. 13 Eq. 6)
- Status: variant of momentum and EMC.
- Definition. Source: the momentum premium falls in panic states, which are bear markets with high volatility. Weight the strategy by forecast mean over forecast variance (p. 13).
  $$w^{*}_{t-1} = \frac{1}{2\lambda}\frac{\mu_{t-1}}{\sigma^2_{t-1}}, \qquad \mu_{t-1} = \hat\gamma_0 + \hat\gamma_{int}\, I_{B,t-1}\,\hat\sigma^2_{m,t-1}$$
  $I_{B,t-1} = 1$ when the market's cumulative return over the past 24 months is negative (p. 7). $\hat\sigma^2_{m}$ is the variance of 126 daily market returns. $\sigma^2_{t-1}$ comes from a GJR-GARCH plus 126-day realised variance.
  Intuition: losers in a bear market behave like call options on the market, so a long-short momentum book is short a call in the rebound.
  Proposal for HY: market = TRACE HY panel excess return index. Apply to EMC and to F5.
- Evidence. Source: across markets and asset classes, including fixed income futures, the dynamic strategy has Sharpe 1.19, four times static US equity momentum (p. 3). No corporate bond test.
- HY applicability: medium-high. HY momentum crashed in the 2009 junk rally (AK framework p. 12 states the same for N-LASR).
- Fit to our signals: momentum legs of OneScore (E16), and the composite sizing in Section 8.
- Test. Signal: EMC scaled by $w^{*}$ against unscaled EMC. Horizon: 1 month. Metric: Sharpe and max drawdown, 2004 to 2026, with $\mu$ fitted on an expanding window. Pass: higher Sharpe and smaller drawdown in 2009 and 2020.

### F8. Credit curve slope and curvature (source: Credit Factor Framework, pdf p. 14-15)
- Status: variant of maturity and roll-down (Dynkin et al.).
- Definition. Source:
  $$Slope = s_{10y} - s_{2\text{-}3y}, \qquad Curvature = s_{5y} - 0.5\, s_{10y} + 0.5\, s_{2y}$$
  The source sizes slope trades DV01-neutral, which gives hedge ratios near 2.7 to 3x (p. 14). Note: the written fly formula has $+0.5\,s_{2y}$. The usual tent form is $s_{5y} - 0.5(s_{2y}+s_{10y})$. We record both and use the tent form.
  Intuition: PC2 of the credit curve is a low-duration bet with carry and roll-down. It loses when the curve inverts in broad stress (p. 14).
- Data needed: issuer or sector spread curves from TRACE G-spreads. In the repo.
- Evidence: none. The source is a plan with no backtest.
- HY applicability: medium. Few HY issuers have three or more liquid maturities. Sector x rating curves are feasible.
- Fit: Section 7.2 Term block and S4 (short-dated vs long-dated, stressed issuer).
- Test. Signal: long the front, short the back, DTS-neutral, in sector x rating cells with positive slope. Horizon: 3 months. Metric: Sharpe after cost. Pass: Sharpe > 0.3 and no loss over 10% of risk in the curve inversion months of 2008 and 2020.

### F9. Credit term premium residual, "directionless slope" (source: Credit Factor Framework, pdf p. 15)
- Status: NEW.
- Definition. Source: regress the 5s10s spread slope on the 2-year spread. The residual is the term premium.
  $$s_{10y}-s_{5y} = \alpha + \beta\, s_{2y} + \epsilon, \qquad TP = (s_{10y}-s_{5y}) - \hat\beta\, s_{2y}$$
  Intuition: the slope that the front-end level does not explain pays for duration risk. A high TP is a cushion for the long end.
- Data needed: sector or index spread curves. In the repo. Fit $\beta$ on a rolling window before the decision time.
- Evidence: the source gives a narrative example (Nov 2022) and no statistics. No number to report.
- HY applicability: medium-low. It is a market-level duration timing signal, not a bond selector.
- Fit: candidate input for a market-directional overlay in Section 9.2. Not a cross-sectional signal.
- Test. Signal: TP percentile per sector curve. Horizon: 3 months. Metric: rank IC of TP with the long-minus-short maturity excess return across sectors. Pass: IC > 0 with t > 2.

### F10. Four-ratio fundamental credit composite (source: Credit Factor Framework, pdf p. 16)
- Status: variant of quality and fundamental state features (Section 4, `q_score`).
- Definition. Source: z-score four ratios within GICS sector, then sum with equal weights.
  $$FC_i = z_{sec}(\text{EBIT}/\text{interest}) + z_{sec}(\text{FCF}/\text{debt}) - z_{sec}(\text{net debt}/\text{EBITDA}) + z_{sec}(\text{EBITDA margin})$$
- Data needed: Compustat point-in-time. In the repo.
- Evidence: none in the source.
- HY applicability: high as a control. Its value is as a simple baseline that a richer model must beat.
- Fit: Section 7.2 Capital structure and Quality blocks.
- Test. Signal: FC as the only predictor of 12-month excess return beyond spread. Metric: rank IC. Pass rule for us: the fair spread model of Section 7.2 must beat FC by a paired t > 2. A failure means the model adds nothing over four ratios.

### F11. Bank-specific fundamentals (source: Deutsche Bank 2019, pdf p. 10 Fig. 8, p. 12 Fig. 10, p. 1)
- Status: NEW. The repo has no bank metrics, and leverage and EBITDA are not meaningful for banks (p. 3-4).
- Definition. Source (US banks, sign in brackets):
  1. Coverage ratio = loan loss reserves / (non-performing assets + loans 90 days past due) (+).
  2. Problem loan growth, annual (-).
  3. Non-interest-bearing deposits / total deposits, and its 3-year change (+).
  4. Interest expense / interest-bearing liabilities (-).
  5. Tier 1 leverage, 3-year change (+). Also NPA ratio (-), LDR (-), efficiency ratio (-).
  Intuition: sticky cheap funding and loss reserves decide a bank's credit quality, not EBITDA.
- Data needed: bank call-report fields. Source uses S&P SNL. Proposal: use Compustat Bank or FR Y-9C through WRDS, if the licence covers them. We do not hold these now.
- Evidence. Source: US banks, equity returns, Jan 2000 to Aug 2018, quintile long-short. Sharpe: non-interest deposit ratio 1.05, Int-Expense/IBL 0.79, problem loan growth 0.75, coverage ratio 0.73 (p. 12). The risk parity composite has Sharpe 1.64 (p. 1). Equity only.
- HY applicability: low. Few US HY issuers are banks. Use it for the financial issuers in the universe, or as a credit gate on bank counterparties.
- Fit: Section 4 for the financial sector only.
- Test. Signal: composite of items 1 to 5 for HY and crossover financial issuers. Horizon: 6 months. Metric: rank IC of the composite with spread change. Pass: IC > 0 with t > 2. Expect low power, because the sample is small.

### F12. Idiosyncratic jump share of issuer equity (source: Aït-Sahalia, Kalnina, Xiu 2020, pdf p. 4 R² definition, p. 15 jump share, p. 17 earnings)
- Status: NEW.
- Definition. Source: with a time-varying beta regression on 5-minute Fama-French plus momentum factors, split each stock's idiosyncratic risk into idiosyncratic volatility (IdV) and idiosyncratic jumps (IdJ). Jumps are increments above a threshold $u_n = 3\Delta_n^{0.47}\sqrt{BV_t}$.
  $$R^2_t = 1 - \frac{IdV_t + IdJ_t}{QV_t}, \qquad JS_{i,t} = \frac{IdJ_{i,t}}{IdV_{i,t} + IdJ_{i,t}}$$
  Intuition: an equity that jumps on its own news is closer to a jump to default. Spreads should widen before the jump share is priced.
- Data needed: intraday equity prices (we have CRSP daily, and MIDAS, not TAQ). Proposal: a daily version with thresholded daily residual returns from a rolling factor regression, over 63 days.
- Evidence. Source: all NYSE, AMEX and NASDAQ stocks, 1996 to 2017. Idiosyncratic jumps are about 10% of idiosyncratic risk on average (p. 15). Earnings surprises raise IdJ, and disappointments raise it more than beats (p. 17). Equity only. No credit test.
- HY applicability: medium. It needs a listed issuer (OneScore covers the same subset).
- Fit: new input to the event model of Section 9 and to PD (Section 7.1).
- Test. Signal: daily-data JS over 63 days, ranked within rating bucket. Horizon: 6 months. Metric: rank IC with spread change, and AUC for a downgrade or default within 12 months. Pass: IC > 0 with t > 2, and AUC gain over Merton DD > 0.01.

### F13. Factor momentum on our signal returns (source: Arnott, Kalesnik, Linnainmaa 2023, Internet Appendix p. 1-4)
- Status: NEW for credit. Candidate replacement for S7.
- Definition. Source: each month, go long factors whose prior-month return is above the median and short those below. Hold one month (p. 2, Fig. A1 note).
  $$w_{f,t} = \mathbb{1}\{r_{f,t-1} > \text{med}_g\, r_{g,t-1}\} - \mathbb{1}\{r_{f,t-1} < \text{med}_g\, r_{g,t-1}\}$$
  Intuition: factor premia are persistent (AR(1) with $\kappa = 0.8$ in the simulation, p. 3).
  Proposal for credit: factors = the long-short returns of S1 to S6, ESP, carry, low risk and sector value. Also a time-series version: hold a factor when its trailing 12-month return is positive.
- Data needed: our own signal return series. In the repo after each backtest.
- Evidence. Source: the appendix shows factor momentum on 43 equity factors has no break from the 1990s, while industry momentum is in drawdown for over 20 years (p. 1). In simulation, factor momentum has t from 6.2 to 7.2 (p. 4, Table A1). The main paper's empirical numbers are not in this file. Graef et al. (2025) dispute that factor momentum drives stock momentum (pdf p. 1-4). Equity only.
- HY applicability: medium. Few credit factors give a weak cross-section (8 to 10). The time-series form is more robust there.
- Fit: Section 8 composite weights. It replaces S7 as the "conditional tilt" with a falsifiable rule.
- Test. Signal: time-series factor momentum on 8 credit factor returns. Horizon: 1 month. Metric: Sharpe of the timed composite against the static IC-weighted composite. Pass: Sharpe gain > 0.1 with a Ledoit-Wolf Sharpe-difference t > 2.

## Methods worth adopting

### M1. Characteristic-shifted spot curves and the error-reduction ratio (Elton et al. 2004, pdf p. 16-18, Table 9)
- What it does. Source: fit a Nelson-Siegel curve per rating class each month. Add the characteristic terms as level shifts: $r_{0t} = a_0 + (a_1+a_2)\frac{1-e^{-a_3 t}}{a_3 t} - a_2 e^{-a_3 t} + \sum_j b_j V_{ij}$ (p. 16). Then compare three mean absolute pricing errors: rating only (a), rating plus the bond's own mean error of the last six months (b), and rating plus characteristics (c). The ratio $d = (a-c)/(a-b)$ is the share of the persistent error that characteristics explain. For Baa industrials, (a) 1.172, (b) 0.613, (c) 0.898, d = 48.96% (p. 18).
- Why it helps us. The ratio is a clean benchmark for our fair spread model. The gap (b) says that half of a rating-only residual persists bond by bond. A persistent residual is a bond effect, not a mispricing that closes.
- Where it fits. Section 7.2 validation and Section 7.5. Proposal: report d for each refit. Test S1 net of the bond's trailing 6-month mean residual against plain S1. Pass: the net version has a higher 3-month IC by paired t > 2.

### M2. Number of factors and a low-rank plus sector-block covariance (Aït-Sahalia and Xiu 2017, pdf p. 3-5; Pelger 2019, pdf p. 1; Fan and Kim 2018, pdf p. 2)
- What it does. Source (AX): choose $\hat r = \arg\min_{1\le j\le r_{max}} \big(d^{-1}\lambda_j(\hat\Sigma) + j\,g(n,d)\big) - 1$, with $g(n,d) = \mu\,\big((n^{-1}\log d)^{1/2} + d^{-1}m_d\big)^{\kappa}$, where $m_d$ is the largest sector block (p. 4-5). Residual covariance is block-diagonal by GICS (p. 2-3). Pelger uses a perturbed eigenvalue ratio and splits continuous from jump factors. Fan and Kim feed Huber-robust realised covariances into POET, which needs only finite fourth moments.
- Why it helps us. The Credit Factor Framework (pdf p. 7) asks for PCA but sets the number of PCs by eye. Bond returns have heavy tails and sector clustering. A tested $\hat r$ and a sector-block residual give a risk model for DTS-neutral legs and a factor count to report.
- Where it fits. Section 9.3 position risk, and the hedge in S1. Test: out-of-sample minimum-variance portfolio of HY bonds. Pass: realised volatility below that of the sample covariance and of a DTS-only model.

### M3. Refresh-time, pre-averaging, and common noise for TRACE (Dai, Lu, Xiu 2019, pdf p. 1; Li, Chen, Linton 2023, pdf p. 1)
- What it does. Source (DLX): for asynchronous noisy prices, sample at refresh times (all assets traded once), pre-average to cut noise, then fit a factor model. The horse race finds that TSR (known factors) or PCA with location thresholding (sector blocks) wins (p. 1). Li, Chen and Linton show the noise itself has a factor structure in S&P 500 intraday data (p. 1).
- Why it helps us. TRACE prints are asynchronous, and dealer-wide price noise can be common across bonds. A naive daily covariance of HY bond returns is biased toward zero correlation for illiquid bonds.
- Where it fits. The return panel behind the risk model and behind F5 and F6. Test: compare correlations of bond pairs of one issuer from refresh-time sampled returns against last-price daily returns. Pass: refresh-time correlations are higher and closer to the equity-implied correlation.

### M4. Variance-clock sampling for factor tests (Chang et al. 2016, pdf p. 2-3, p. 9)
- What it does. Source: sample returns at random times $T_n$ where the market's quadratic variation grows by a fixed amount, $[S]_{T_n} - [S]_{T_{n-1}} = \int_{T_{n-1}}^{T_n}\sigma^2_t\,dt = \Delta$. By the DDS theorem the errors become close to i.i.d. normal. Regressions and pricing tests are then valid under stochastic volatility with leverage. Fixed-interval tests give "logically inconsistent" results (p. 3).
- Why it helps us. HY spread volatility is strongly time-varying (2008, 2020). Our IC t-stats and MZ slopes use calendar months. A variance clock is the formal version of the RFQ and volume clocks the AK framework asks for (pdf p. 7).
- Where it fits. Section 11 backtest design and Section 7.5 size calibration. Test: rerun the S1 and OneScore IC tests on a clock where HY index realised variance accumulates a fixed amount. Pass: the conclusions agree with the calendar results. A disagreement flags the calendar result as unreliable.

### M5. Spread-level dynamic factor model and a statistical arbitrage test (Focardi, Fabozzi, Mitov 2016, pdf p. 1, p. 21)
- What it does. Source: fit a dynamic factor model to log price levels, not returns. The levels mean-revert around one integrated factor. Few lags capture what a return model needs many lags for. Compare forecasts with Diebold-Mariano, and test the strategy with the Hogan et al. (2004) statistical arbitrage test. Long-short returns are near 27% a year on S&P 500 stocks, weekly trading (p. 21). Equity only.
- Why it helps us. Credit spreads are levels with known mean reversion. A statistical level model gives a model-free S1 benchmark and an independent residual. The Hogan test asks whether profit grows while its variance shrinks, which is a stricter bar than a Sharpe ratio.
- Where it fits. Section 7.5 and S1 validation. Test: PCA on log spreads of a balanced HY panel, VAR(1) on the factors, residual as a signal. Pass: DM test shows better 1-month spread forecasts than a random walk with t > 2, and the strategy passes the Hogan test at 5%.

### M6. DTS-scaled IC (RAMIC), start-date averaging, and permutation R² (Credit Factor Framework, pdf p. 16-19)
- What it does. Source: the cross-sectional RAMIC uses a top and bottom decile binary signal and scales the forward return by DTS: $RAMIC_{t,h} = E\big[\tilde s^i_t \cdot \bar r^i_{t+h} / dts^i_t\big]\times 252$ (p. 19). Average results over all start dates of a non-overlapping horizon, for example 20 start dates for a 1-month horizon (p. 19). The marginal R² of a factor is the average over all orderings of the sequential R² gain on residuals, after a LASSO screen (p. 16-17). This is the Shapley (LMG) decomposition. Variables get an inverse-normal rank transform first (p. 16).
- Why it helps us. Our IC treats a BB bond and a CCC bond alike. RAMIC compares returns per unit of DTS, which matches our DTS-neutral legs. Start-date averaging removes key-date luck from 12-month tests. Shapley R² gives an order-free answer to "what does E13 add beyond ESP".
- Where it fits. Section 11 metrics and the bucket weights in Section 7.4. Proposal: report RAMIC beside rank IC for each signal, and Shapley R² for the E-buckets.

### M7. Replication hurdles (Hou, Xue, Zhang 2020, pdf p. 1, p. 8)
- What it does. Source: 65% of 452 anomalies fail |t| ≥ 1.96 with NYSE breakpoints and value-weighted returns. With the multiple-test cutoff 2.78, 82% fail (p. 1). Microcaps are 3.2% of market value but 60.7% of stocks (p. 2).
- Why it helps us. Small HY bonds are the "microcaps" of credit. Equal-weighted bond sorts overstate edge.
- Where it fits. Section 11. Proposal: test every new signal (F1 to F13) with breakpoints from the larger half of bonds by TRACE volume, because we lack amount outstanding. Weight by TRACE volume. Use |t| ≥ 2.78 as the pass bar for a new signal.

### M8. Boosted signal aggregator with monotone constraints and four training windows (Deutsche Bank Quantcraft 2020, pdf p. 3-6, p. 12; Credit Factor Framework pdf p. 9-13)
- What it does. Source: rank each feature in [0,1], demean within sector, label the top 30% and bottom 30% by vol-scaled sector-neutral forward return, and drop the middle. Train four models: 1-year, 5-year, same calendar month over 10 years, and a hedge model on the worst 50% of weeks. Average them. Force monotone, non-negative use of each feature. Regress the signal on market beta and keep the residual. N-LASR beats RF, XGB, NN, NNLS and equal weight (p. 6). Full-sample Sharpe 1.47 for N-LASR against 1.28 for the factor composite (p. 12). Equity, MSCI World, 2003 to 2020. The AK framework adds sector x size x beta cells to stop the low-beta bias that caused the March 2009 drawdown (pdf p. 12).
- Why it helps us. Our composite weights by trailing IC per cycle phase. That is a linear, one-window rule. The monotone constraint keeps the signs the framework demands.
- Where it fits. Section 8 composite. Test: N-LASR-style aggregator against the IC-weighted composite on the same E-scores. Pass: higher out-of-sample RAMIC and Sharpe, with t > 2 on the difference. Expect smaller gains, because the bond cross-section is about one tenth of 1,200 stocks.

### M9. Multitask neural factor timing (Cotturo, Liu, Proner 2026, pdf p. 1-3)
- What it does. Source: one network predicts the outperformance of several factors at once. Shared layers learn common macro states (LSTM), and factor-specific layers map them. Out of sample 1990 to 2021, the dynamic multitask model has multifactor Sharpe 0.82 against 0.60 for buy-and-hold (p. 3). Unemployment, leverage, profitability and money are the main inputs. Equity factors only.
- Why it helps us. S7 failed with a linear macro map. A shared-state model uses all signals at once, which the short credit history needs.
- Where it fits. Replacement candidate for S7. Low priority: monthly TRACE history from 2002 gives about 290 months, which is thin for an LSTM. Test F13 first. Test M9 only if F13 passes.

### M10. Kelly score to weight external forecasters (Grant, Johnstone 2010, pdf p. 1)
- What it does. Source: rank probability forecasters by Brier, log, a Kelly score (paper profit from Kelly bets), and a categorical score. Pool the top forecasters. The categorical score ranks forecasters well, and a bootstrap shows the gain is not chance (p. 1). Sports betting data.
- Why it helps us. The repo holds many external forecasts (agency default forecasts, sell-side consensus, SPF). A Kelly score against market-implied default rates measures which source adds money, not only accuracy.
- Where it fits. Section 5.2 scenario weights. Low priority.

## Top 3
1. F5 residual bond momentum: it uses only data we hold, it fixes the junk-rally beta bet in bond momentum, and the source doubles the equity Sharpe (0.90 vs 0.45).
2. M1 plus F2 (Elton et al.): the error-reduction ratio is a direct test of our fair spread model, and the notching result says peer cells by bond rating misprice notched HY bonds.
3. F6 systematic momentum: it is a new signal with the strongest reported monthly result (Sharpe 0.82, t 6.44), built from our existing characteristic panel, and the authors report a corporate bond follow-up.

Not read in full: none. Every file opened. The Factor Momentum file holds only the Internet Appendix, so main-paper results are missing.
