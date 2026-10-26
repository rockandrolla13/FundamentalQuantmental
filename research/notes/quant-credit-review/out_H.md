# Batch H: Screening Models, Missing Papers, FX, Statistical Techniques, BMI, zip archives

Paths are relative to `/home/ak/Documents/Quant Credit/`. Page numbers are the printed page numbers unless the entry says "PDF p.".

Scope notes:
- The list has 41 files. The two zip archives hold 8 PDFs each. The `ETFs` zip is a byte-for-byte copy of the `drive-download` zip (md5 match), so 8 zip PDFs count once. In the drive zip, `0900b8c08b1b510b.pdf` and `0900b8c08b1b510b (1).pdf` are identical. `0900b8c08b403162.pdf` has the same size as `Research Platform/0900b8c08b403162.pdf`, so I skipped it as a duplicate.
- Unzipped to `scratchpad/qc/unzip_drive/` and `scratchpad/qc/unzip_ETFs/`.
- I did not run any code from the folder. I read the BMI `.md` spec. The `.py`, `.tex` and `.pdf` files in `BMI/files/` repeat the same content.
- `Specification Draft ... .docx`: I read the PDF version only, as the brief instructs.
- `Missing Papers/jostova-2013-momentum.pdf` is the FDIC working paper 2010-04 (revision 31 July 2010), not the 2013 RFS print. The numbers below come from the working paper.
- `Missing Papers/kelly-2026-ipca.pdf` is the econometrics IPCA paper (Kelly, Korsaye, Pruitt, Su, April 2026). It is not the corporate bond paper (Kelly, Palhares, Pruitt). It has no credit evidence.

## Triage table

| File | Title, authors or bank, year | Topic | Relevant (yes/no) | Why |
|---|---|---|---|---|
| Screening Models/Lehman LEVER/Introducing LEVER ... (9 January 2006).pdf | Introducing LEVER: A Framework for Scoring LEVeraging Event Risk. Trinh, Bhattacharya, Devarajan, Heike, Pomper, Wolosky. Lehman Brothers, 2006 | LBO and leveraged-recap event-risk score, firm and macro | yes | Full Firm LEVER-Score definition, weights, LBO hit-rate evidence. New event signal. |
| Screening Models/Lehman LEVER/Trading Event Risk ... using LEVER (2007).pdf | Lehman QCR Quarterly 2007-Q1. Contains "Trading Event Risk in Credit Markets using LEVER" (pp. 30–41) and "Introducing CMetrics" (pp. 42+) | LEVER as a bond trading signal, LEVER x spread corner trades | yes | Bond excess-return evidence for LEVER, revised inputs, macro-scaled trade. CMetrics gives one accrual ratio. |
| Screening Models/MS Credit Stategy Screens/MS_Cyclicality vs. Liquidity (Sep 2011).pdf | High Yield: Looking for the Best in Stress. Sheets, Graber et al. Morgan Stanley, 2011 | European HY cyclicality versus liquidity scatter | yes | Exact liquidity-headroom rule (p. 4). |
| .../MS_Screen for positive FCF, strong liquidity and low cyclicality (Aug 2011).pdf | The 10% Club. Morgan Stanley, 2011 | HY bonds yielding 10% with stress cushion | yes | Two-rule screen: FCF positive, 2008-09 EBITDA fall below half the refi trigger (p. 3). |
| .../MS_Screening for EBITDA margin trends by sector (Feb 2011).pdf | On the Margin. Morgan Stanley, 2011 | Margin trend, PPI minus CPI, margin versus debt growth | yes (minor) | Margin-change versus debt-change quadrant. Sector screen (p. 7). |
| .../MS_Sensitivity of EBITDA to growth & Mapping EBITD declines to refinancing needs (Aug 2011).pdf | Stressing Growth and High Yield. Morgan Stanley, 2011 | EBITDA stress, refinancing need, refi success by leverage, SPL reversion | yes | Defines refinancing risk, refi success schedule (p. 6), cyclicality versus headroom scatter. |
| .../MS_Single name screens ... (Apr 2011).pdf | High Yield: Pricing Tomorrow's Deleveraging Today. Morgan Stanley, 2011 | Six-rule HY cash bond screen | yes | Exact screen thresholds (p. 8). |
| .../MS_Single name screens ... (Mar 2011).pdf | High Grade, Mid-Cycle. Morgan Stanley, 2011 | CDS per leverage, CDS per implied vol, leverage trend, sector SPL z-score, credit-cycle composite | yes | Screen rules (p. 7), sector SPL z versus own history (p. 6), cycle composite (p. 3). |
| Screening Models/Specification Draft_European Single Name Fundamental Analysis (v. 080212).pdf | Internal spec draft, 2012 (no author) | Single-name RV template: SPL, spread vs coverage, rating drift, cyclicality vs liquidity, LEVER | yes | Leave-one-out sector SPL predicted spread (p. 8–9). Confirms the MS refi rule (p. 11). |
| Screening Models/Specification Draft ... (v. 080212).docx | Same document, Word format | Same | no | Duplicate of the PDF. Not read separately. |
| Screening Models/UBS_Valuation Mutiples Primer (Nov 2001).pdf | Valuation Multiples: A Primer. UBS Warburg, 2001 | Equity multiples | no | Equity valuation primer. No credit signal. |
| Screening Models/CS HOLT/HOLT ValueSearch - Reference Handbook.pdf | HOLT ValueSearch Reference Handbook. Credit Suisse HOLT, about 2010 | CFROI, fade, Merton PD | no | PD uses leverage and 90-day vol in a Merton model (p. 49). This is the known Merton DD. Rest is equity. |
| Missing Papers/bali-2022-bond-ml.pdf | Predicting Corporate Bond Returns: Merton Meets Machine Learning. Bali, Goyal, Huang, Jiang, Wen. SFI WP 20-110, May 2022 | ML bond return forecasts with Merton hedge-ratio structure | yes | New forecast structure. TRACE 2002-2017. Long-short evidence. |
| Missing Papers/jostova-2013-momentum.pdf | Momentum in Corporate Bond Returns. Jostova, Nikolova, Philipov, Stahel. FDIC WP 2010-04 (July 2010) | Bond price momentum by rating | yes | HY-specific momentum evidence and construction. Variant. |
| Missing Papers/kelly-2026-ipca.pdf | Instrumented Principal Component Analysis. Kelly, Korsaye, Pruitt, Su. April 2026 | Econometrics of IPCA | yes (method) | Method for characteristic-driven loadings. No credit data in this file. |
| Missing Papers/van-zundert-2017-volatility-momentum.pdf | Volatility-Adjusted Momentum. van Zundert. Thesis ch. 4, 2017 | Momentum sorted on return per unit vol | yes | HY and rating-bucket evidence. Variant. |
| Missing Papers/van-zundert-2018-thesis-full.pdf | Empirical Studies on the Cross-Section of Corporate Bond and Stock Markets. van Zundert. Tilburg PhD, 2018 | Ch. 3 stock-bond integration, ch. 4 vol-adjusted momentum, ch. 5 momentum spillover, ch. 6 factor investing | yes | Ch. 5 residual equity momentum with HY evidence. Ch. 3 bond-implied expected return. Ch. 6 is the known Houweling-van Zundert paper. |
| BMI/files/credit_bmi_v2.md | Credit-BMI v2: An Operational Spread-Forecasting Engine. Rebuild of a Morgan Stanley note, June 2026 | Index-level IG and HY excess-return timing with conformal intervals | yes | Candidate replacement for S7. Six macro blocks fully specified. |
| BMI/files/credit_bmi_v2.pdf, .tex, .py, credit_bmi_model.py | Same spec and code | Same | no | Duplicates of the `.md`. Code not run. |
| Statistical Techniques/1-s2.0-S0167947320301870-main.pdf | Statistical inference for inter-arrival times of extreme events in bursty time series. Hees, Nayak, Straka. CSDA 2021 | Extreme-event clustering statistics | no | Method only. Possible use for default clustering. No factor. |
| Statistical Techniques/2406.09521v2.pdf | Randomization Inference: Theory and Applications. Ritzwoller, Romano, Shaikh. arXiv 2025 | Permutation tests | no | Test method. Could support signal tests. No factor. |
| Statistical Techniques/2511.04469v4.pdf | Towards Causal Market Simulators. Thumm, Ontaneda Mijares. arXiv 2026 | Causal VAE market generator | no | Synthetic data. No factor. |
| FX Work/10 things about the FX Market.pdf | 10 Things You Didn't Know About Currency Markets. Hafeez. Deutsche Bank, 2007 | FX facts | no | FX only. |
| FX Work/FX Carry Paper.pdf | Machine Learning in FX Carry Basket Prediction. Fletcher, Redpath, D'Alessandro. 2009 | ANN, SVM on FX carry | no | FX only. |
| FX Work/HYbrid SVM trading in FX.pdf | FX Forecasting with Hybrid SVMs. Zinzalian, Simeonov, Robeva. 2009 | SVM FX direction | no | FX only. |
| FX Work/ICML2006.pdf | Reinforcement Learning for Optimized Trade Execution (slides). Nevmyvaka, Feng, Kearns. ICML 2006 | RL execution | no | Equity microstructure. |
| FX Work/KearnsNevmyvakaHFTRiskBooks.pdf | Machine Learning for Market Microstructure and HFT. Kearns, Nevmyvaka. 2013 | HFT ML | no | Microstructure. No HY transfer. |
| FX Work/MKL NIPS.pdf | Currency Forecasting using Multiple Kernel Learning. Fletcher, Hussain, Shawe-Taylor. 2010 | MKL for EURUSD | no | FX only. |
| FX Work/academic_5788_7994294_12927.pdf | Stock Turning Points Detection by PSO clustering and SVM. Fan et al. 2010 | Stock turning points | no | Low quality. Equity. |
| FX Work/cdcLudkovski.pdf | Bayesian Quickest Detection with Observation-Changepoint Feedback. Ludkovski. 2012 | Change-point detection | no | Method only. |
| FX Work/erp_24jan2013.pdf | Exchange Rate Perspectives: FEER v. BEER. Deutsche Bank, 2013 | FX fair value models | no | FX only. |
| FX Work/fx_deriv_29oct.pdf | FX Derivatives Focus: Carry and Volatility in EMFX. Natividade. Deutsche Bank, 2007 | Carry versus implied vol | no | Carry per unit vol idea. Needs options data. Known carry family. |
| FX Work/fx_spl_11oct2007 (1).pdf | FX Special Report: Extreme Days Do Make A Difference. Hafeez. Deutsche Bank, 2007 | Carry returns without best or worst days | no | FX only. |
| FX Work/fxguide_may2002.pdf | DB Guide to Exchange-Rate Determination. Deutsche Bank, 2002 | FX model survey | no | FX only. |
| FX Work/pub-et_10962.pdf | Time-Frequency Projection Filters. Hlawatsch, Kozek. IEEE TSP 1994 | Signal processing | no | Method only. |
| FX Work/quant_20111101.pdf | Quant Craft: Breaking Out? Chen, Natividade. Deutsche Bank, 2011 | Projection-filter breakout signals | no | FX and macro technicals. |
| FX Work/quantcraft_120718.pdf | Quantcraft: Technical Analysis Meets Machine Learning (TARA). Natividade. Deutsche Bank, 2012 | ML technicals | no | FX technicals. |
| FX Work/rlexec.pdf | Reinforcement Learning for Optimized Trade Execution. Nevmyvaka, Feng, Kearns. ICML 2006 | RL execution | no | Equity microstructure. |
| zip: 0900b8c08b1b510b.pdf (and identical "(1)" copy) | US ETF Insights: ETF Flow Risk-o-Meter (EFRoM). Mercado et al. Deutsche Bank, 5 May 2016 | ETF-flow risk appetite | no (low) | Equity TAA. 16-month backtest. Flow idea noted in one low block. |
| zip: 0900b8c08b37dc81.pdf | The Flow Whisperer, June 2016. Mercado. Deutsche Bank | TAARSS monthly update | no | Monthly update. |
| zip: 0900b8c08b7e5e5b.pdf and "(1)" (near-identical) | The Flow Whisperer, August 2016. Mercado. Deutsche Bank | TAARSS monthly update | no | Monthly update. |
| zip: 0900b8c08b403162.pdf | US ETF Insights: Portfolio Implementation Ideas with EFRoM. Deutsche Bank, 9 June 2016 | ETF flows | no | Duplicate of `Research Platform/0900b8c08b403162.pdf` by size. Skipped. |
| zip: 341b683e_..._604.pdf | Quantitative Musing: Happy birthday reversion. Tomasi. Deutsche Bank, March 2022 | Equity mean reversion | no | Equity only. |
| zip: 378375ed_..._604.pdf | What Happens When the World Goes Passive? Active ETF Flow Strategies. Deutsche Bank, July 2018 | ETF ownership and stock anomalies | no | Equity holdings. We lack HY ETF holdings. |

## Factors found

### F1. Firm LEVER-Score: leveraging event risk (source: Introducing LEVER 2006, pp. 8–9, 13–14; Trading Event Risk 2007, p. 32)
- Status: NEW.
- What the source says. The score ranks a firm's chance of an LBO or a leveraged recap in the next quarter. It has three equal parts: Valuation, Operation, Execution. Each part is the average rank of its inputs.
  - Valuation: book-to-market (high is risk, $\alpha=+1$). EV/EBITDA (low is risk, $\alpha=-1$).
  - Operation: free cash flow yield, FCF / market cap (high is risk). Capex growth, one-year change in capex (low is risk).
  - Execution: FCF variability (low is risk). Firm size, market cap or EV (small is risk). The 2007 version adds cash / market cap (high is risk) and defines FCF variability as the two-year volatility of FCF divided by debt (2007, p. 32 fn. 4–6).
  - Normalisation (2006, p. 9):
  $$V_i^{N}=\alpha_V\left(\frac{V_i}{\bar V^{U_V}}-1\right)$$
  where $\bar V^{U_V}$ is the market-value-weighted mean of $V$ in universe $U_V$. Intuition: the score measures how far the firm sits from a cap-weighted norm, signed so that "more LBO-friendly" is higher.
  - Peer universe: sector peers for book-to-market, EV/EBITDA and (2006 only) capex growth. Whole universe for the other inputs. The 2007 text says only B/M and EV/EBITDA use sector peers.
  - Aggregation: rank each $V^N$ cross-sectionally. Part score = mean rank of its inputs. Firm score = mean of the three parts. The authors map the score to a uniform 0–10 scale (2006 p. 9 fn. 9). A score above 7.5 marks high risk.
  - Filters: drop financials. Drop technology firms before 2001 (2006, p. 8).
  - Timing: quarterly accounts. The authors recompute monthly as filers report (2007, p. 34 fn. 8).
- Data needed: Compustat point-in-time book equity, total debt, cash, EBITDA, CFO, capex, CRSP market cap. SIC or GICS sector. All in the repo. An LBO and recap event list for tests: SDC is not in the repo. A proxy is SEC 8-K merger filings plus S-4 and SC 13E-3 (going-private) filings, which the SEC download can fetch.
- Evidence (2006, S&P 1500, 1995–2005, about 900 scored names a quarter, 32 LBOs, pp. 13–14):
  - The top 100 scores one quarter before caught 14 of 32 LBOs. The top 150 caught 19. The top 200 caught 20. The bottom 100 caught 0. The bottom 200 caught 1.
  - 63% of LBO targets scored 7.5 or more, against 25% of non-targets. 6% of targets scored 2.5 or less. 84% of targets scored 5 or more.
  - Part scores: share of targets above 7.5 is Valuation 50%, Operation 50%, Execution 59%. Share below 2.5 is 9%, 9%, 19% (Fig. 11a). The text says the Operation score has the lowest Type II error, but the table shows Valuation and Operation tied at 9%.
  - Universe is equity index names, IG and HY bonds mixed. No HY-only result.
- HY applicability: high for BB and crossover issuers with weak covenants. Medium for single-B names that already carry sponsor leverage. The sign can flip for HY bonds with a 101 change-of-control put or a portability clause. A buyout then can pay holders, not hurt them.
- Fit to our signals: extends S5 (document optionality) and the `events` layer. It gives the prior probability of a control event. S5 gives the payoff to the bond if the event occurs. Expected event loss = P(LEVER) × (loss given event from the covenant read).
- Test: logit of a 12-month going-private or leveraged-recap event on the Firm LEVER-Score, US non-financial issuers with TRACE bonds, 2003–2024. Pass if the out-of-sample AUC is at least 0.65 and the top score quintile holds at least 40% of events.

### F2. LEVER x spread corner trades, static and macro-scaled (source: Trading Event Risk 2007, pp. 33–40)
- Status: NEW (event-risk conditioning of a value sort). It is related to ESP, but the second sort is event risk, not fundamentals.
- What the source says:
  - Universe: Lehman US IG Corporate Index names in the S&P 1500, 1990–2006. The authors sort inside rating x duration buckets.
  - Simple trade: long the bottom 20% LEVER, short the top 20%. Hold 3 months, rebalance monthly, average three overlapping books. Zero costs.
  - Corner trades: sort each LEVER tercile into OAS terciles. LH = low LEVER, high spread ("core long"). HL = high LEVER, low spread ("core short"). LL and HH are the defensive pair.
  - Combined trade (p. 39):
  $$\text{Trade}_t=(LH-HL)_t+w_t\,(LL-HH)_t,\qquad w_t=0.1\times\text{Macro LEVER-Score}_t$$
  Intuition: always hold the positive-carry event trade. Add the negative-carry pair only when the macro climate favours buyouts.
- Data needed: F1 inputs, G-spread or OAS by bond (we have G-spreads from TRACE), rating and duration buckets. Ratings after Feb 2017 are missing. Use a spread-implied rating or a Compustat-based rating model for the bucket.
- Evidence (IG only, zero costs, monthly excess returns in bp):
  - Simple trade, Fig. 3 p. 34, IR in brackets. 1990–2006: AA 1 (0.08), A 3 (0.30), BBB 5 (0.19). 2004–2006: AA −0 (−0.07), A 7 (0.55), BBB 16 (0.74).
  - LH−HL, Fig. 7 p. 37: 16 bp a month, IR 1.04 (1990–2006). 15 bp, IR 0.78 (1999–2006). 10 bp, IR 1.59 (2004–2006).
  - LL−HH, Fig. 8 p. 37: −9 bp, IR −0.30 (1990–2006). 9 bp, IR 0.43 (2004–2006).
  - Regression on the Macro score, Fig. 10 p. 39: LL−HH slope 12.0 (t 2.88). LH−HL slope −2.9 (t −1.33).
  - Combined, 1990–2006, Fig. 11 p. 40: AA 8 bp IR 0.51, A 14 bp IR 0.73, BBB 22 bp IR 0.55, overall 14 bp IR 0.90, hit ratio 59%. Correlation −20% with the IG index. Correlation −1% with ESPRI.
  - The payoff grows down the rating scale. That is a reason to expect a larger effect in BB, but the source does not test HY.
- HY applicability: medium-high. Not tested in HY. Covenant protection differs in HY, so the sign must come from S5.
- Fit to our signals: S1 x S5 interaction. Use S1 residual in place of raw OAS for the spread sort.
- Test: in US HY 2003–2024, sort on LEVER tercile x S1-residual tercile inside rating x duration buckets. Measure the LH−HL 3-month excess return over duration-matched Treasuries, net of TRACE half-spread. Pass if the IR is at least 0.4 and the trade is positive in at least three of the four stress cycles (2008, 2015, 2020, 2022).

### F3. Macro LEVER-Score: buyout climate (source: Introducing LEVER 2006, pp. 6–7, 10–11, 15; 2007, p. 33)
- Status: NEW (time-series conditioner for event risk).
- What the source says: a one-year-lagged regression of the count of large LBOs (deal size above $250m) on eight variables. The source gives correlations with the LBO count, 1990–2005 (Fig. 3, p. 6): GDP growth +31%, 10y yield change −29%, 2s10s slope change −52%, S&P 500 return −12%, S&P 500 dividend yield −75%, S&P 500 cash-flow yield +22%, S&P 500 leverage −23%, credit spread change +51% (lagged about −13%), private equity raised in the prior year +65%. Scale 0–10. The January 2006 reading was 8. The source does not print the regression coefficients.
- Data needed: FRED macro and rates, S&P 500 aggregates from Compustat, HY spread change from our TRACE index. PE fundraising is not in the repo. Proxy candidates: sponsor-backed leveraged loan issuance (not in repo) or count of SC 13E-3 filings (SEC, in reach).
- Evidence: an in-sample chart (Fig. 8, p. 11) and the LL−HH slope in F2. No out-of-sample statistic.
- HY applicability: medium. It times the event leg, not spreads.
- Fit to our signals: an input to the `events` layer that scales F1. It is not an S7 replacement on its own.
- Test: regress next-year US going-private count on the lagged score, 1995–2024, with the coefficients estimated on expanding windows. Pass if the out-of-sample correlation with the next-year count is at least 0.5.

### F4. Refinancing headroom versus cyclicality (source: MS Stressing Growth and High Yield, Aug 2011, pp. 5–7; MS Cyclicality vs. Liquidity, Sep 2011, p. 4; European spec, p. 11)
- Status: NEW.
- What the source says:
  - Liquidity headroom $H_i$ is the largest EBITDA cut that a firm can take over two years before it must come to market.
  - The firm needs refinancing if (a) negative FCF burns through balance-sheet cash, or (b) available liquidity cannot cover bond maturities over the two years.
  - Inputs are cash, LTM EBITDA, LTM interest expense, LTM capex.
  - Cyclicality $C_i$ is the worst year-on-year LTM EBITDA change over the last decade.
  - "Above the line" names have $H_i>C_i$. They can survive a decline worse than their worst year before they need the market. MS treats them as candidates to add risk. Names below the line are candidates to cut risk.
  - The authors note gaps. The rule ignores loan maturities, the undrawn revolver and parent support.
  - In formula form (our reconstruction of the rule):
  $$H_i=\max\Big\{d\in[0,1]:\ \text{Cash}_i+\textstyle\sum_{k=1}^{2}\big[(1-d)\,\text{EBITDA}^{LTM}_i-\text{Int}^{LTM}_i-\text{Capex}^{LTM}_i\big]\ \ge\ \text{Mat}^{0\text{–}2y}_i\Big\}$$
  $$C_i=-\min_{q\in\text{last 40 quarters}}\frac{\text{EBITDA}^{LTM}_{i,q}-\text{EBITDA}^{LTM}_{i,q-4}}{\text{EBITDA}^{LTM}_{i,q-4}},\qquad S_i=H_i-C_i$$
  Intuition: $S_i$ measures how many "worst years" of cushion the firm has before a forced refinancing.
  - Default mapping (Aug 2011, p. 6, Exhibit 11, labelled subjective): refi success rate by net leverage at refinancing. Below 3.0x: 100%. 3.0–4.0x: 75%. 4.0–5.0x: 50%. 5.0–6.0x: 25%. Above 6.0x: 0%. The table prints the first row as "X > 3.0x", which must be a typo for "X < 3.0x".
  - The Aug 2011 "10% Club" screen (p. 3) uses two rules: FCF positive, and a 2008–09 EBITDA decline less than half the decline that would force new funding.
- Data needed: Compustat quarterly cash (`cheq`), `oibdpq`, `xintq`, `capxy`. Debt maturities from Compustat annual `dd1`–`dd5` or the 10-K maturity table from SEC filings. Revolver availability from 10-K text (S5 parsing) closes the gap the authors flag. All in the repo.
- Evidence: descriptive only.
  - Universe is about 100 European HY issuers. With zero EBITDA growth, about one fifth of XOver names fail the two-year test (Aug 2011, p. 5).
  - A cut half as deep as 2008–09 maps to about 12% two-year defaults (p. 6).
  - No return test.
- HY applicability: high. It targets the refinancing-wall channel that drives HY defaults.
- Fit to our signals: the `framework.md` F3 liquidity sizing step and the `forward` layer stress. It gives a cardinal input to PD by cycle phase. As a signal it extends S1: a low $S_i$ at a tight S1 residual is a short.
- Test: PD test. Logit of 24-month default or distressed exchange on $S_i$, controlling for leverage and Merton DD, US HY 2003–2024. Pass if $S_i$ adds at least 0.02 out-of-sample AUC. Return test: the top-minus-bottom $S_i$ quintile inside rating buckets earns a positive 6-month excess return in at least three of four stress cycles.

### F5. Leave-one-out sector spread-per-leverage gap, LTM and NTM (source: European spec, pp. 8–9; MS Mar 2011, p. 6)
- Status: variant of SPiDER (spread per unit of debt to EBITDA).
- What the source says:
  $$\text{SPL}_i=\frac{s_i}{\text{NetDebt}_i/\text{EBITDA}_i},\qquad \hat s_i=\overline{\text{SPL}}_{\text{sector}\setminus i}\times\text{Lev}_i,\qquad \text{Gap}_i=s_i-\hat s_i$$
  Intuition: price the firm's leverage at the sector's going rate per turn, leaving the firm itself out.
  - A positive gap is cheap. In the stylised example (Table 9, p. 9), company C is +60 bp cheap and company B is −43 bp rich.
  - The NTM version uses the analyst-forecast net leverage in the denominator.
  - A twin metric replaces leverage with EBIT/interest coverage: $s_i/(\text{EBIT}/\text{Int})$ (p. 9).
  - MS (Mar 2011, p. 6) adds a sector-level z-score of SPL against its own history, paired with a composite fundamental score.
- Data needed: G-spread from TRACE, Compustat net debt and EBITDA. Forward EBITDA needs I/B/E/S, which the S3 build may already use.
- Evidence: none. These are templates.
- HY applicability: medium. SPL is not linear in leverage for HY. Our S1 fair-spread model already captures a non-linear map.
- Fit to our signals: S1 baseline and sanity check. The NTM version links S1 to S3: the gap between the LTM and NTM gaps measures the deleveraging the market already prices.
- Test: the rank IC of $\text{Gap}^{NTM}_i-\text{Gap}^{LTM}_i$ against the next 3-month excess return in US HY. Pass if the IC is positive after costs in at least three of four cycles.

### F6. MS six-rule HY cash bond screen (source: MS Apr 2011, p. 8)
- Status: variant (boolean composite of value, quality, deleveraging).
- What the source says: buy-list rules.
  1. Z-spread above 250 bp.
  2. Year-on-year issuer deleveraging.
  3. FCF / debt above 3%.
  4. Spread per leverage (z-spread) above the market median (87 bp per turn then).
  5. EBITDA / interest above 3x.
  6. Maturity above 3 years.
  The sell list is the reverse. Mar 2011 (p. 7) uses CDS / net leverage above average, CDS / implied vol above average, and faster year-on-year deleveraging than average.
- Data needed: all in repo except implied vol. Use 3-month realised equity vol instead.
- Evidence: none. The output is only a list of names.
- HY applicability: medium-high as a gate, low as a ranked signal.
- Fit to our signals: a candidate pre-filter for the `framework.md` F9 gate.
- Test: an equal-weight portfolio of bonds that pass all six rules versus the HY universe, monthly, 2003–2024. Pass if the excess-return IR is at least 0.3 net of costs.

### F7. Merton-restricted machine-learning bond forecast (source: Bali et al. 2022, eq. 10–11 pp. 7–8, eq. 19–21 pp. 21–22; Tables 3, 6, 7 at PDF pp. 44, 47, 48)
- Status: NEW (forecast structure). It is related to EMC, but it uses forecast stock returns times a firm hedge ratio, not past equity returns.
- What the source says:
  $$E_t[R^B_{i,t+1}]=\hat h_{i,t}\,E_t[R^S_{i,t+1}]+E_t[R^B_{i,t+1}-\hat h_{i,t}R^S_{i,t+1}]=\hat h_{i,t}\,\psi_1(X^S_{i,t})+\psi_2(X^B_{i,t})$$
  Intuition: a bond is partly a short put on the firm. Predict the equity-like part with stock characteristics. Predict the residual with bond characteristics.
  - $\hat h_{i,t}$ is the slope of a 36-month rolling regression of firm excess bond return on firm excess stock return (eq. 19).
  - $\psi_1$ uses 94 stock characteristics. $\psi_2$ uses 43 bond characteristics. Both are fitted with ML: random forest, FFN, LSTM, penalised regressions, combination.
  - Training is 3 years, validation 2 years, test is the rest.
  - Firm-level bond returns are value-weighted by amount outstanding.
- Data needed: TRACE monthly bond returns (have). CRSP equity returns (have). Stock characteristics from Compustat and CRSP (have). Bond characteristics: most come from TRACE (illiquidity, Roll, VaR, momentum, reversal). Amount outstanding is missing. Equal weighting is a fallback, and the authors say equal-weight results are similar (fn. 11, p. 16).
- Evidence (TRACE, July 2002–Dec 2017, 75% IG and 25% HY observations, monthly):
  - Bond characteristics only, Table 3: High−Low 0.33–0.79% a month. RF 0.79% (t 2.78). LSTM 0.79% (t 3.33). Combination 0.67% (t 3.41). OLS 0.16% (t 1.38).
  - Merton-restricted, Table 7: 0.55–0.92% a month. LSTM 0.92% (t 2.69). Combination 0.84% (t 3.27). Gain over bond-only is 0.13–0.24% a month, t from 1.93 to 2.81.
  - Out-of-sample R² rises to 4.95% for the combination (Table 6), against 2.09% for bond-only.
  - Adding stock characteristics without the structure adds nothing (Table 5).
  - The authors say the results hold after Roll-spread costs. The numbers are in Online Appendix OA1, which is not in the folder.
  - Almost all of the spread comes from the top decile. RF decile 10 earns 1.37% against 0.49–0.69% for deciles 1–9 (Table 3).
  - No HY-only split. The hedge-ratio MSE is lower for HY than for IG (p. 23).
- HY applicability: high. Hedge ratios are largest in HY, so the equity leg matters most there.
- Fit to our signals: a new signal and a benchmark for S1 and S2. The $\psi_2$ residual leg is a pure bond-specific forecast.
- Test: walk-forward on US HY TRACE 2005–2024 with the Bali split. Pass if the Merton-restricted High−Low decile spread beats the bond-only model by at least 0.10% a month (t ≥ 2) and keeps a positive rank IC after costs in three of four cycles.

### F8. Bond downside risk, 5% VaR (source: Bali et al. 2022, appendix p. 29, feature importance pp. 15–16)
- Status: NEW to the known list (Bai, Bali and Wen 2019 measure). It is the opposite sign of a low-risk tilt.
- What the source says: $\text{VaR5}_{i,t}=-(\text{second-lowest monthly bond return over } t-35..t)$. Variants are VaR10 (fourth lowest), ES5 (mean of the two lowest), ES10 (mean of the four lowest). The authors flip the sign so that a higher value means more downside risk. Bai, Bali and Wen price high VaR with a higher expected return.
- Data needed: 36 months of TRACE monthly returns. We have them.
- Evidence in this file: feature importance only. The "risk" group (VaR, ES, coskewness, betas) is the second most important group after illiquidity (Fig. 4, p. 16). This file does not report a standalone premium. Do not cite one.
- HY applicability: medium. It may only proxy for distress. It needs a control for rating and S1.
- Fit to our signals: a candidate control in the S1 residual and an input to F7.
- Test: Fama-MacBeth of the next-month HY excess return on VaR5 with rating, duration, S1 residual and momentum controls, 2005–2024. Pass if the Newey-West t ≥ 2.5 (a high bar for a published factor).

### F9. Jostova bond price momentum: HY evidence and construction (source: Jostova et al. WP 2010, pp. 1–3, 12, 19–24)
- Status: variant of momentum (Houweling and van Zundert, Israel et al.).
- What the source says:
  - Construction (p. 12): rank on the cumulative total bond return over months $t-6$ to $t-1$. Skip month $t$. Hold $t+1$ to $t+6$. Deciles, equal weight, six overlapping books.
  $$\text{MOM}_{i,t}=\prod_{k=1}^{6}(1+r_{i,t-k})-1$$
  Intuition: bond prices under-react, but only where default news dominates.
  - Data: Lehman, DataStream, Bloomberg, TRACE, FISD. 1973–2008, 77,150 bonds.
- Evidence (1991–2008, bp a month):
  - All bonds 64 (t 4.53). NIG 190 (t 7.84). IG 12 (insignificant).
  - The worst rating quintile (average rating 13.61, about BB−/B+) earns 173. The other quintiles earn 1 to 21, all insignificant.
  - Profits come from winners. Q5 winners earn 233 against Q1 winners at 66. Losers earn 60 against 65.
  - Removing D-rated bonds cuts the profit from 63 to 28 (t 2.03). Removing B− or worse (8.27% of bonds) makes it insignificant (pp. 20–21).
  - TRACE traded bonds, July 2002–2008: 114 (t 2.05). It loses 5% significance once CCC+ or worse bonds are removed.
  - Duration-adjusted Q5 profit is 129 (t 5.73).
  - After conservative small-trade costs of 1.25% per trade, the NIG six-month profit is 6.96% (pp. 23–24).
  - Total return, not excess return. Equal weight.
- HY applicability: high but narrow. The edge sits in B− and below and in defaulted bonds. Our universe rules (default handling, price floors, CCC inclusion) decide whether we capture it.
- Fit to our signals: a control for S2 and S6. It shows that momentum in HY overlaps with rating-migration flows (S6).
- Test: replicate on TRACE 2003–2024 with excess returns over duration-matched Treasuries. Report by rating bucket. Pass if the B and CCC bucket profit has t ≥ 2 after TRACE-measured costs. Expect, and accept, no effect in BB.

### F10. Volatility-adjusted bond momentum (source: van Zundert 2017, pp. 100–103, 111–113, Tables 4.6–4.7 pp. 123–124)
- Status: variant of momentum.
- What the source says:
  $$\text{VAMOM}_{i,t}=\frac{\sum_{k=1}^{6}r^{ex}_{i,t-k}}{\hat\sigma_{i,t-12:t-1}},\qquad w_{i,t}\propto\frac{1.7\%}{\hat\sigma_{i,t-12:t-1}}$$
  Intuition: rank on return per unit of risk, so long-duration and CCC bonds do not crowd the tails.
  - $r^{ex}$ is the excess return over duration-matched Treasuries. $\hat\sigma$ is the monthly std of excess returns over the past 12 months, skipping the latest month.
  - Deciles. Hold 6 months. Overlapping books. Position scaled to a 1.7% vol target.
  - Universe: Barclays US IG and HY indices, Jan 1994–Dec 2015.
  - The 90/10 percentile ratio of bond vol is 14.2, against 3.1 for stocks. That ratio is why the adjustment matters more for bonds.
- Evidence (annualised %, t in brackets):
  - Full sample, Table 4.6: standard WML 0.38 (0.12), SR 0.04. VA-MOM 3.18 (4.58), SR 1.04, 5-factor alpha 3.26 (4.82).
  - HY, Table 4.7: standard 2.56 (0.60), alpha 6.29 (2.05). VA-MOM 4.02 (4.03), alpha 4.52 (4.44).
  - By rating, VA-MOM quintile return: BB 1.78 (2.79), B 2.71 (3.91), CCC–C 4.36 (4.98). Standard momentum is significant only in CCC–C on alpha, 10.44 (2.99).
  - Costs are not deducted.
- HY applicability: high. It works in BB and B, where Jostova's raw momentum fails.
- Fit to our signals: replaces any raw-return momentum control in S2 and S6. Use as a candidate stand-alone signal.
- Test: TRACE-based excess returns 2003–2024, US HY. Pass if the VA-MOM decile spread has t ≥ 3 and stays positive in BB alone, net of costs.

### F11. Residual equity momentum spillover (source: van Zundert thesis 2018, ch. 5, pp. 127–128, 132–133, 138; Tables 5.2, 5.4, 5.6 pp. 148–152)
- Status: variant of EMC (equity momentum).
- What the source says:
  $$E_{i,t}=\alpha_i+\beta_i\,\text{RMRF}_t+\varepsilon_{i,t}\ \ (36\text{-month rolling}),\qquad \text{RM}_{i,t}=\frac{\sum_{k=1}^{6}\varepsilon_{i,t-k}}{\text{sd}(\varepsilon_{i,t-36:t-1})}$$
  Intuition: rank on the firm-specific equity news only. The market part of equity momentum loads on default risk and crashes after equity bear markets.
  - Lag 1 month. Deciles of companies. Equal-weight the company's bonds. Hold 6 months. Overlapping books.
  - Excess returns over Treasuries. Barclays US IG and HY constituents with listed equity, Jan 1994–Dec 2013.
  - The total-return version picks low-default-risk winners after equity sell-offs. The HY winner-minus-loser rating gap is −1.98 notches in the lowest equity-market quintile (Table 5.4).
- Evidence, HY panel (annualised, Table 5.6 p. 152):
  - Total spillover: 5.79% (t 1.59), vol 13.25%, SR 0.44.
  - Residual: 6.13% (t 2.88), vol 8.40%, SR 0.73.
  - After a DEF-beta hedge: residual 7.83% (t 4.58), SR 1.14.
  - Against rating x maturity peers: residual 5.96% (t 3.21), SR 0.81.
  - All-universe worst drawdown: 80% (total, 2009) against 25% (residual). In 2003: −51% against −14% (p. 139).
  - The DEF beta's dependence on the market return falls from 1.02 to 0.41 in HY (p. 138).
  - Costs are not deducted.
- HY applicability: high. It uses data we hold and fixes the 2009 crash risk in EMC.
- Fit to our signals: replace the EMC leg of OneScore with RM. It can also act as an S2 cross-check: does equity news lead the change in fair spread?
- Test: rank IC of RM against the next 6-month HY excess return over duration-matched Treasuries, TRACE 2003–2024. Pass if the IC is positive after costs in at least three of four cycles, and the 2009 drawdown is at most half of the total-return EMC drawdown.

### F12. Bond-implied expected excess return and stock-bond disagreement (source: van Zundert thesis 2018, ch. 3, pp. 49–50, 55, 61–63)
- Status: variant of the Correia, Richardson, Tuna value gap (spread net of expected default loss).
- What the source says:
  - Expected bond excess return to maturity $T$, with default only at maturity:
  $$E_t[r^B_j]-y_g=\Big[(1+y_g+s_j)^{T_j}(1-L\pi_j)\Big]^{1/T_j}-1-y_g$$
  $\pi_j$ is the PD to maturity and $L$ the loss rate.
  - Implied equity return: $E_t[r^E_j]=y_g+\frac{\delta E/E}{\delta B/B}\big(E_t[r^B_j]-y_g\big)$. The elasticity comes from a panel regression on leverage, equity vol, yield and maturity (eq. 3.4).
  - Bond side: the 1-month realised bond return rises across expected-return deciles from −0.09% to 0.29% a month (Table 3.4 Panel A, p. 61). The 5-year realised returns line up with the expected returns.
  - Equity side: the bond-implied D1−D10 realised equity return is −1.79% a month (t −3.35) against an implied +1.27%. The effect is stronger for high-default-risk firms. Sample 1994–2015.
- Data needed: G-spread, a PD model (we have Merton DD and the repo PD), duration, equity vol, leverage.
- Evidence: as above. The bond leg is the known value premium. The new fact is that equity mispricing against bonds is largest in high-PD firms.
- HY applicability: medium. For a bond book it mainly confirms that the S1-type expected return predicts bond returns at 1 month and 5 years.
- Fit to our signals: S1 (check the expected-return form against the spread-gap form). It is also a hedge signal: short equity when the bond-implied equity return is high.
- Test: rank IC of $E_t[r^B]-y_g$ against the next-month HY excess return, 2003–2024, compared with the S1 residual. Pass if the IC stays positive after controlling for S1. If it does not, keep S1 alone.

### F13. Credit-BMI v2: index-level HY timing with conformal intervals (source: BMI/files/credit_bmi_v2.md, sections 1.2–3.7)
- Status: NEW candidate to replace S7 (macro-conditional tilt, which failed).
- What the source says. The target is the h-day sum of ICE BofA H0A0 excess returns, with h = 5, 21, 63 days. There are six blocks, each z-scored on an expanding window and mapped to $s=20[\Phi(z)-0.5]$:
  1. VIX 21-day change (sign −).
  2. 4-month exponentially decaying HY excess-return momentum divided by 4-month realised vol (not z-scored, sign +).
  3. Risk-appetite composite change, with a contrarian flip when its 6-month z is above +3 or below −4.
  4. Liquidity: NY Fed primary-dealer corporate positions (9-day publication lag) and the CDX.IG minus cash OAS basis (sign −).
  5. Structural: median issuer 3-month equity vol, median net debt/EV, 3-month downgrades minus upgrades (sign −).
  6. Systematic: PC1 of the 21-day change in rating-bucket OAS changes (sign −).
  Momentum is cut 60% when 21-day OAS vol is above its expanding 80th percentile. A quantile model (L1 or LightGBM, purged CV) feeds CQR plus ACI ($\gamma=0.02$). The rule trades only when the full 90% interval clears costs (HY cash 12 bp). Size is proportional to point forecast over width. Full size needs sign agreement across the 1W, 1M and 3M horizons.
- Data needed: VIX, NY Fed dealer positions, FRED ICE BofA OAS (`BAMLH0A0HYM2` and rating sub-indices are public). We lack the H0A0 excess-return series and CDX. Build an HY excess-return index from TRACE. Drop the CDX leg or use the HY ETF-NAV basis. Ratings after Feb 2017 are missing, which hits block 5.
- Evidence: secondhand only.
  - The source note reports hit rates of 67% (IG) and 62% (HY), and 66–68% when all signals agree against 61% overall. That note is not in the folder.
  - The v2 numbers are synthetic only: 0.899 coverage against a 0.90 target.
  - There is no real-data backtest in the file.
- HY applicability: high for the index timing problem that S7 targets.
- Fit to our signals: S7 replacement. It also supplies the conformal decision rule that `framework.md` F9 needs.
- Test: walk-forward on our TRACE HY excess-return index, 2005–2024, h = 21 days. Pass if empirical coverage is within 2 points of 90%, the hit rate on traded days is at least 58%, and the net Sharpe is above zero in at least three of four stress cycles.

### F14. Credit-cycle phase composite and deleveraging breadth (source: MS Mar 2011, p. 3; MS Apr 2011, pp. 2–4)
- Status: NEW input for cycle-phase PD calibration.
- What the source says: MS stacks five cycle measures and calls the cycle "mid-cycle" when all five read like early 2004:
  1. Year-on-year L12M EBITDA growth.
  2. Year-on-year total debt growth.
  3. Year-on-year L12M capex growth.
  4. Announced M&A value (10-week moving average).
  5. Net % of banks that tighten loans to non-financial firms (ECB survey).
  Breadth adds the % of issuers that delever year on year. Above 70% "marked the peak of market breadth" (Apr 2011, p. 2). The capex/depreciation ratio is a payback-risk gauge (fell from 102% to 63%, Apr 2011, p. 4).
- Data needed: Compustat aggregates (have). Fed SLOOS for the US bank survey (public). M&A value: SEC 8-K counts as a proxy.
- Evidence: none. Descriptive.
- HY applicability: medium.
- Fit to our signals: the cycle-phase label for "PD calibrated by rating and by cycle phase" in the definition of done. It also offers a possible S7 regime input.
- Test: classify quarters 1995–2024 into phases with the composite. Pass if HY 12-month default rates differ across phases (chi-square p < 0.01) and the phase label improves PD calibration (Brier score) out of sample.

### F15. Low-priority items (one line each)
- EBITDA-margin change versus debt-change quadrant (MS Feb 2011, pp. 4–7). Variant of issuance aggressiveness. Rising margin with falling debt is the good quadrant. No evidence.
- Cash-flow discrepancy (Lehman CMetrics 2007, p. 66). NEW accrual-quality ratio: $(\text{CFO}-(\text{EBEI}+\text{D\&A}+\text{non-cash}))/|\text{CFO}|$. The source says a low value relative to peers or history flags aggressive accounting. No evidence.
- ETF-flow risk appetite (DB EFRoM, May 2016, pp. 2–3). Level $=\sum_{i=1}^{14}\text{TAARSS}_i\times\text{RiskFactor}_i$. The month-on-month change is the timing signal. Evidence is a 16-month equity backtest only. An HY version would use HYG and JNK share-creation flows. Low.
- Sector SPL z-score against own history plus a composite fundamental score (MS Mar 2011, p. 6). Variant of SPiDER at sector level. Could feed S7.

## Top 3
1. F1 + F2 Firm LEVER-Score with spread conditioning. It is a fully specified, buildable event-risk signal from Compustat alone. It caught 63% of LBOs in the top quartile and gave an IG LH−HL IR of 1.04. It feeds the event module directly. HY evidence is missing, so the first job is the HY test.
2. F11 Residual equity momentum spillover (variant of EMC). It has the strongest HY evidence in this batch: SR 0.73, or 1.14 after a DEF hedge, t 4.58. It uses only TRACE and equity returns we hold. It cuts the 2009 drawdown from 80% to 25%.
3. F4 Refinancing headroom versus cyclicality. It is a direct HY default channel (the two-year refinancing need against the worst EBITDA year), built from Compustat `dd1`–`dd5` and 10-K revolver data. It fills the liquidity-sizing gap. It has no return evidence yet, so it must pass the PD test first.
