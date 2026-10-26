# Batch E: research platform, flows, fundamental scoring

Base folder: `/home/ak/Documents/Quant Credit/Research Platform/`.
Page numbers: DB and SG reports use the printed page footer. RFS paper pages match PDF pages.

## Triage table

| File | Title, authors, year | Topic | Relevant (yes/no) | Why |
|---|---|---|---|---|
| 0900b8c08b403162.pdf | US ETF Insights: Portfolio Implementation Ideas with ETF Flow Risk-o-Meter, S. Mercado (Deutsche Bank), 9 Jun 2016 | EFRoM used as a risk-on and risk-off switch in multi-asset portfolios (HYG is the risk-on bond leg) | yes | Backtest of the EFRoM timing signal with HY in the risk basket |
| 2105.11490.pdf | Hidden Markov and semi-Markov models, Ruiz-Suarez, Leos-Barajas, Morales, 2021 (arXiv stat.AP) | Tutorial on HMM and HSMM state classification, ecology examples | no | Method only. It can feed a regime model for the S7 replacement, but it holds no credit factor |
| 4dd576cf_..._604.pdf | Portfolios Under Construction: Building Fundamental Alpha Capture Systems, Elledge, Shah, Zhao, Chen (Deutsche Bank), 5 Feb 2018 | Hedge fund 13F aggregate portfolio, risk-weighted industry hedges | yes (medium) | Positioning signal (13F) that can transfer to the issuer's bonds. Square-root-size hedge weights |
| A_Multifactor_Model_of_Credit_.pdf | A Multifactor Model of Credit Spreads, Bhar and Handzic, Asia-Pacific Financial Markets 18 (2011) 105-127 | Kalman filter, three latent Vasicek factors on 14 rating spread indices, 1996-2008 | no | Aggregate spread decomposition. Factors map to VIX, long rate, S&P 500. No selection or timing signal |
| Accelerating Database Analytic Query Workloads.pdf | Accelerating Database Analytic Query Workloads Using an Associative Processor, Caminal, Chronis, Wu, Patel, Martinez (Cornell, Wisconsin) | Database hardware | no | No credit content |
| ETF Flow Risk-o-Meter (EFRoM).pdf | US ETF Insights: ETF Flow Risk-o-Meter (EFRoM), S. Mercado (Deutsche Bank), 5 May 2016 | Risk-appetite composite from 14 asset-class ETF flow signals | yes | Defines EFRoM. Corp HY carries a risk factor of +0.5 |
| Global Rates Insights_ Filtering CFTC positioning data for a signal(1).pdf | Global Rates Insights: Filtering CFTC positioning data for a signal, P. Korapaty, W. Marshall (Goldman Sachs), 9 May 2019 | Direction-filtered CFTC Treasury futures positioning, residual reversal signal | yes | The listed file is a 286-byte Windows shortcut (.lnk) to a missing reMarkable file. I read the real 7-page PDF at `/media/ak/10E1026C4FA6006E/USB Stick/Street Market Research and Technical Papers (contains copies)/Filtering CFTC positioning data for a signal` (no extension). The JFEC folder copy is also a shortcut |
| SocGen_Spread Market Scoring ... (27 Sep 2011).pdf | Spread Market Scoring (SMS): Identifying credit market opportunities from fundamental data, R. Dando, J. Turc (SG Cross Asset Quant Research), 27 Sep 2011 | GAM model of 5y CDS from 3 fundamentals plus index, residual signal | yes | Fundamental fair-spread scoring with out-of-sample residual evidence |
| SystematicCreditUseCases.pdf | Systematic Research Use Cases with Query Specifications and Encompassing Topics (internal, no author, 2025) | Platform use cases adapted to credit spreads (time-of-day, nowcast, seasonality, regimes) | yes (ideas only) | Candidate signals with formulas, no evidence |
| Tactical Asset Allocation (TAA) from ETF Flows.pdf | Special ETF Research: Tactical Asset Allocation insights from ETF flows (TAARSS), S. Mercado (Deutsche Bank), 14 May 2014 | ETF flow-trend strength signal (slope times R-squared) | yes | Defines TAARSS. Fixed income sector rotation backtest includes Corp HY |
| Use Cases 1.pdf | Quantitative Research Platform Use Cases: Detailed Analysis (internal), 2 Jun 2025 | Answers to use cases E1-J5 from other bank documents (macro, vol, intraday) | no | Equity, FX and vol content. Secondary summaries of documents that are not in this batch |
| Use Cases 2.pdf | Systematic Research Use Cases with Query Specifications (internal), 2025 | Use case list A1-J5 with SQL queries | no | Platform spec. Credit items (A1 percentile spread, A3 IG-HY compression) are descriptive |
| a62ec896-add8-43af-b3ba-2aba3c02052e.pdf | Fixed-Income ETF-Flow (contra)flow strategy: adding the arbitrage comovement effects, AK, 10 Jun 2025 | Bond-level ETF par-flow reversal with arbitrage sensitivity | yes | Bond-level flow signal design and hypotheses. No evidence. Same file as `contraflowwithcomovement.pdf` (byte-identical, `cmp` passes) |
| cf02a143-a24d-4eb0-9231-7fda0e53cf6a.pdf | Blocking and Tackling: Blockchain and Cryptocurrencies (Citi Research), 28 Aug 2018 | Crypto and blockchain | no | No credit content |
| citi-developments-in-credit-market-liquidity-fimsa-011118.pdf | Developments in credit market liquidity, S. Theisen (Citi), SEC FIMSAC, 11 Jan 2018 | Credit market structure, dealer inventory, liquidity by age and size | yes (low) | Liquidity facts for the liquidity cells and the cost gate. No signal |
| code-export-6-9-2025-6_17_22-PM.txt | Diagram-as-code export of a trading pipeline architecture (internal), 9 Jun 2025 | Platform architecture | no | No factor content |
| contraflowsimple.pdf | Fixed-Income ETF-Flow (Contra)flow, AK, 10 Jun 2025 | Six-month bond par-flow, allocation vs reconstitution split, decile long-short | yes | Base contraflow signal definition. No evidence |
| e10b5396-c2d4-42b4-a5a8-b7c1c14334cc.pdf | The Flow Show: 3Rs end Bulls, M. Hartnett et al. (BofA Global Investment Strategy), 29 Jan 2021 | Weekly fund flows, proprietary contrarian indicators | yes | Defines the BofA Global Flow Trading Rule (equity plus HY flows) and the Bull and Bear components |
| export-6_1_2025, 8_41_15 PM.pdf | Untitled outline of a multi-asset research platform (internal), Jun 2025 | Platform design outline | no | No factor content |
| export-6_2_2025, 10_16_14 PM.pdf | Untitled, "Generate a document outline" page (internal), Jun 2025 | Empty template | no | No content |
| fixed_document.tex | Placeholder | None | no | The file holds only the string `<user_provided_latex_code>` (26 bytes) |
| hhab031.pdf | The Unintended Consequences of Corporate Bond ETFs: Evidence from the Taper Tantrum, Dannhauser and Hoseinzade, RFS 2021 | ETF flow-induced price pressure on corporate bonds, same-issuer design | yes | Peer-reviewed flow-pressure measures with a 4-month reversal |
| notationanddefinitions.pdf | Testable Null Hypotheses for Bond ETF Arbitrage Comovement Model, AK, 2025 | Bond arbitrage sensitivity measure, 13 hypotheses (one is IG vs HY) | yes | Defines the normalised arbitrage sensitivity used in the contraflow notes |
| paper_TradeSizeClustering.pdf | Trade Size Clustering, P. Dennis (UVA), 12 Nov 2012 | Equity trade sizes cluster at round numbers (TAQ, 2011) | no | Equity microstructure. A round-lot retail tag on TRACE is possible, but the paper has no bond evidence |
| process.pdf | Cross and Intra Asset Systematic Strategies (discussion points), AK, 3 Jun 2025 | Research process slides | no | Process only |
| quantmental what lies behind the pricing.pdf | Quantamental Strategy: What lies behind the current repricing? (Deutsche Bank Rates), 3 May 2021 | Black-Litterman sector rotation across UST, agency, credit, MBS, TIPS | no | Aggregate rates rotation narrative. No bond selection signal |
| rsi.pdf | A selective study across asset classes for directional efficacy of the risk sentiment index, A. Koukorinis, 3 Jun 2025 | Test plan for a 9-component risk sentiment index | no | Test plan only. It uses option vol and CDS inputs that we lack |
| ssrn-4875607.pdf | ETF flows and the index effect, C. Howard, Jun 2024 (SSRN) | Australian equity index additions after an ETF launch (diff-in-diff) | no | Equity. Index-inclusion flows are already known (inclusion delay). No bond evidence |

Counts: 28 files triaged. 13 relevant (yes or yes with a qualifier). The listed CFTC file is a broken shortcut. I read its content from a full copy on the USB Stick folder.

## Factors found

### F1. Bias-corrected GAM fair-spread residual (source: SocGen SMS, pages 2-7)
- Status: variant of S1 (fair value residual) and of Correia, Richardson, Tuna 2012 (theoretical spread gap). The new parts are three. (a) The model selects inputs by AIC from more than 20 candidates. (b) It uses rank-normalised inputs with piecewise-linear transforms. (c) It subtracts each name's historical mean residual before it ranks names. It also adds a ROC/WACC input that interacts with cyclicality.
- Definition. What the source says (page 5):
  $$\ln S_{i} = \alpha + \beta_{\text{index}}\ln S_{\text{index}} + \sum_{k=1}^{n}\gamma_k\, f_k\!\left(\operatorname{rank}(F_{k,i})\right)$$
  The inputs $F_k$ are profit margin (net income over revenue), debt over assets, and ROC over WACC, with a cyclical or non-cyclical split on ROC/WACC (pages 2-4). Intuition: the log spread equals the market level plus a nonlinear penalty for weak margins, high leverage and value destruction.
  The residual is $e_i = \ln S_i^{\text{mkt}} - \ln \hat S_i$. The signal is the bias-corrected residual $\tilde e_{i,t} = e_{i,t} - \bar e_{i,\,<t}$ (page 6). Intuition: compare a name with its own normal gap to the model, not with zero.
  The model ranks each input against its full-sample distribution (page 5). The model observes market data on each annual results date.
  What we propose: rank inputs within each date and rating cell, not on the full sample. The full-sample rank uses future data. Compute $\bar e_{i,<t}$ only from residuals with `available_at` before $t$.
- Data needed: Compustat point-in-time (net income, revenue, total debt, total assets, EBIT, invested capital). WACC needs an equity beta from equity returns and a cost of debt. Market spread: TRACE G-spread at the issuer level. The index term: the median HY G-spread from TRACE stands in for CDX.
- Evidence: universe of more than 400 non-financial names in Europe and North America (iTraxx Main and X-Over, CDX IG and HY, S&P 500 and EuroStoxx 600 names with CDS). More than 2,000 CDS quotes from 4bp to 7000bp, mid-2004 to 2011 (page 5). In-sample R-squared is 59-60%. The indices explain 40%, profit margin adds 12%, debt over assets adds 7%, and ROC/WACC adds 1% (3% since 2008) (pages 4-5). Out of sample for 2009-2011: the widest decile against the model outperforms and the tightest decile underperforms, and the 12-month horizon is best (pages 6-7). The widest 10% outperform Main ex-financials, CDX IG and X-Over from March 2009 (page 7). The report gives these results only as charts. It prints no t-stat or IR.
- HY applicability: medium. The sample is mostly IG CDS. CDX HY and X-Over names are in the universe. The bias correction matters for HY because static model errors (subordination, secured debt) are large there.
- Fit to our signals: extends S1 (fair spread and residual) and section 8. ROC/WACC × cyclicality is a candidate input for the `fairspread` module.
- Test: rank HY issuers monthly by $\tilde e$ against raw $e$. Measure the 12-month forward excess return over duration-matched Treasuries, by rating cell. Pass: the rank IC after costs of $\tilde e$ beats that of raw $e$ in at least 3 of the 4 cycles (2008, 2015, 2020, 2022).

### F2. Flow-trend strength: slope through origin times R-squared (TAARSS) (source: DB TAA from ETF Flows, 14 May 2014, pages 17-21 and 33)
- Status: NEW.
- Definition. What the source says (page 18). Let $Y_d$ be the cumulative net flow as % of AUM on day $d$ of the formation window, and $X_d = d$.
  $$\text{TAARSS} = \hat\beta_1^{\text{SLRTO}} \times R^2_{\text{SLR}}, \qquad \hat\beta_1^{\text{SLRTO}} = \frac{\sum_d X_dY_d}{\sum_d X_d^2}$$
  $R^2_{\text{SLR}}$ comes from the OLS fit with an intercept. Intuition: a steep, steady flow trend shows a real demand shift. A lumpy flow (a rebalance or model trade) gets a low $R^2$ and so a low weight (pages 18-19). The signal frequency (formation window) and the rebalance frequency are separate parameters (page 19). Portfolio: hold only positive signals, signal-weighted, else cash (page 20).
  What we propose: replace ETF flow with TRACE net customer flow. $Y_d = \sum_{\tau \le d}(\text{customer buy par} - \text{customer sell par})_{\tau}$ for the issuer or the sector. Scale it by the trailing 12-month total TRACE par volume of the issuer, because we lack amount outstanding. Use a 1-month or 3-month window.
- Data needed: TRACE trade side (dealer or customer, buy or sell) and par size. Note: the TRACE size cap on large trades (for example 1MM+ for HY) understates block flow.
- Evidence: the asset-class rotation over 7 years has annual return 9.82%, Sharpe 0.99, max drawdown -21.6%. Pure price momentum gives 7.98% and Sharpe 0.59. Pure flow momentum (flow over initial assets) gives 7.67% and Sharpe 0.74 (page 21, Figure 23). The fixed income sector monthly rotation (Corp IG, Corp HY, UST, MBS, TIPS, convertibles, senior loans, DM and EM debt, munis) runs Dec 2008 to Q1 2014. It returns 5.67% a year with Sharpe 1.08, against 2.89% and Sharpe 0.72 for the Barclays US Agg (page 33). No t-stats. The tests are at asset-class level, not issuer level.
- HY applicability: medium. The evidence is on asset-class ETFs. The slope-times-R² construction transfers directly to any flow series. At the issuer level it may show reversal (liquidity pressure) instead of continuation. The test must settle the sign.
- Fit to our signals: new signal (flow and positioning). It can also act as a conditioning variable for S6 forced flows.
- Test: compute the TAARSS analogue monthly per HY issuer on TRACE net customer flow. Measure the 1-month and 3-month forward excess return by quintile within rating × sector. Pass: |rank IC| > 0.02 with the same sign in at least 3 of 4 cycles, and the R² weighting beats the raw slope alone.

### F3. Flow-induced selling pressure with a 4-month reversal (source: Dannhauser and Hoseinzade, RFS 2021, pages 4, 11, 25-28)
- Status: NEW. It is in the forced-flow family (fallen angels, S6) but its trigger is fund outflows, not ratings.
- Definition. What the source says (page 11, Eq. 5, the trade-based proxy after Coval and Stafford 2007):
  $$\text{ETFpressure}_{i,j} = -\left[\frac{\sum_f \max(0,\Delta H_{i,j,f}\mid \text{Flow}_f>P_{75})}{\text{AmtOut}_{i,j,t-1}} - \frac{\sum_f \max(0,-\Delta H_{i,j,f}\mid \text{Flow}_f<P_{25})}{\text{AmtOut}_{i,j,t-1}}\right]$$
  Here $\Delta H$ is the fund's change in holdings of bond $i$ of issuer $j$ across the episode. Intuition: the sign flip makes high values mean that funds in heavy outflow are selling the bond hard.
  Hypothetical arbitrage exposure (page 11, Eq. 6): $\text{ETFArb}_{i,j} = \sum_f \%w_{i,j,f,\text{pre}}\cdot \text{C/R}\$_{f}\,/\,\text{AmtOut}_{i,j,t-1}$. Intuition: authorized participants redeem pro rata, so a bond's dollar pressure equals its pre-episode weight times the net redemption dollars.
  Identification uses issuer fixed effects. The design compares two bonds of the same issuer. A third design uses the LQD index $750m size threshold: the treatment bond meets it and the control bond misses it (page 4).
  What we propose: build a TRACE-only version for HY. Take the net customer-to-dealer selling in bond $i$ minus the issuer average over a stress window. Scale it by issue volume (amount outstanding is not available). Then go long the most-pressured bond against a same-issuer bond 1-4 months later. The index-size threshold design needs amount outstanding, so it waits for that data.
- Data needed: fund holdings (N-PORT or N-Q) and flows for the source version, which we lack. For our proxy: TRACE side and size, and the bond-to-issuer map.
- Evidence: Taper Tantrum, May-Aug 2013, US corporate bonds held by ETFs. LQD-eligible bonds widen 11.3bp more than same-issuer controls in August and 8.5bp more in September. That is 10.1% and 7.6% of the pre-episode spread. The effect is significant for 4 months and insignificant after November (page 26). A 1% rise in trade-based pressure gives a 4.0bp larger widening. A 1% rise in hypothetical pressure gives 14.8bp. The peak price impact is up to 20.35bp after duration (page 4). Mutual fund pressure is insignificant (page 26). The sample covers IG and HY ETF holdings (HYG named, page 11 footnote 15). The main LQD design is IG.
- HY applicability: high. HY ETFs and HY funds face larger outflows. The same-issuer design removes credit fundamentals, so the reversal is a liquidity premium we can harvest.
- Fit to our signals: new signal. It sits next to S6 (forced flows) and uses the S4 same-issuer frame.
- Test: in each month with HY index return below its 10th percentile, rank bonds within the issuer by the TRACE net-selling proxy. Hold the most-sold against the least-sold bond of the same issuer for 1, 2, 3 and 4 months. Pass: the mean spread-change difference reverses by at least 50% within 4 months, with t > 2 using issuer-clustered errors.

### F4. Bond-level ETF par-flow contraflow with arbitrage sensitivity (source: contraflowsimple.pdf pages 1-3; a62ec896 pages 2-5; notationanddefinitions.pdf pages 1-4; AK, 2025)
- Status: NEW design with no evidence. It extends F3 to a monthly cross-sectional signal.
- Definition. What the source says (contraflowsimple page 2, Eq. 1-6):
  $$\text{BondFlow}^{(6)}_{i,t} = \frac{P_{i,t}Q_{i,t} - P_{i,t-6}Q_{i,t-6}}{\Pi_{i,t-6}/100}, \qquad \text{DurAdjFlow}^{(6)}_{i,t} = \frac{D_{i,t-6}}{\bar D_{t-6}}\text{BondFlow}^{(6)}_{i,t}$$
  $Q$ is the ETF par held, $\Pi$ is par outstanding, and $\bar D$ is the holdings-weighted ETF duration. The flow splits into allocation flow and index reconstitution flow. Rank into deciles within rating × sector. Go long decile 1 (largest outflows) and short decile 10, dollar-neutral, monthly (page 3). Intuition: passive flow pushes price away from value, and the push reverses.
  Directional arbitrage term (a62ec896 page 3, Eq. 7): $\text{DirFlow}_{i,t} = \text{BondFlow}_{i,t} + \beta\,\operatorname{sign}(\text{Premium}_{e,t})\,\Lambda^{arb}_{i,t}$. Here $\Lambda^{arb} = \omega^{conc}\cdot\varphi^{impact}\cdot\psi^{activity}$, with $\omega^{conc} = (\sum_e w_{i,e}^2)^{1/2}$ and $\varphi = \beta_0 + \beta_1/\text{IssueSize} + \beta_2\,\text{BidAsk}$ (page 2-3). The normalised version adds a days-to-settle term and an HY dummy in price impact (notationanddefinitions page 1).
  What we decide: the notes rank on a 10-plus parameter version. The notes themselves flag overfit risk (a62ec896 page 6). Test only the base 6-month flow first, as the notes' own Phase 1 says (page 7).
- Data needed: daily ETF holdings and premium or discount (we lack these), par outstanding (we lack this), and TRACE for bid-ask and price impact.
- Evidence: none. These are design notes. Hypothesis 5 (notationanddefinitions page 3) predicts a stronger effect in HY than IG. It is untested.
- HY applicability: medium. The mechanism is strongest in HY, but the data gap blocks the test now.
- Fit to our signals: new signal. It is blocked on ETF holdings data. F3's TRACE proxy is the buildable path.
- Test: monthly decile long-short as in contraflowsimple Eq. 7. Use 2014-2024, HY only, with a 1-month hold. Pass: IR after costs > 0.5 and IR(DurAdjFlow) > IR(BondFlow).

### F5. Contrarian fund-flow trading rule on equity plus HY flows (source: BofA The Flow Show, 29 Jan 2021, page 11)
- Status: NEW. This is a market timing signal.
- Definition. What the source says (page 11, Table 4): "Buy when outflows from global equities & HY > 1.0% AUM over 4wks. Sell when inflows > 1.0% AUM over 4wks." The signal lasts 8 weeks.
  $$s_t = \begin{cases} +1 & \sum_{w=t-3}^{t} F_w/\text{AUM}_{t-4} < -1\% \\ -1 & \sum_{w=t-3}^{t} F_w/\text{AUM}_{t-4} > +1\% \\ 0 & \text{otherwise}\end{cases}$$
  Intuition: extreme retail outflows mark capitulation, so forward returns are high.
  The Bull and Bear indicator on the same page has 6 components with percentiles: HF positioning, credit market technicals, equity breadth, equity flows, bond flows and LO positioning. Sources are EPFR, CFTC and FMS. The source gives no component formulas.
- Data needed: weekly EPFR or ICI HY fund flows and AUM (we lack these). Proxy: weekly aggregate TRACE HY customer net selling over trailing 52-week volume.
- Evidence: none in this document. It gives only the rule and the current reading (0.2%, neutral).
- HY applicability: medium. HY is a named input. The rule is coarse and fires rarely.
- Fit to our signals: candidate replacement for S7 (macro-conditional tilt), used as an HY beta timing overlay.
- Test: use the TRACE proxy with the threshold set at the in-sample 5th and 95th percentile in place of ±1% AUM. Measure the 8-week forward HY index excess return after buy signals. Pass: the mean is above the unconditional mean with t > 2, and the effect holds in at least 3 of 4 cycles.

### F6. ETF Flow Risk-o-Meter change (EFRoM) (source: DB EFRoM, 5 May 2016, pages 2-4; DB EFRoM portfolios, 9 Jun 2016, pages 3-5)
- Status: NEW. This is a risk-appetite timing signal.
- Definition. What the source says (5 May 2016, page 2, Eq. 1): $\text{EFRoM}_t = \sum_{i=1}^{14}\text{TAARSS}_{i,t}\times RF_i$. The risk factors are UST -1, Gold -1, Corp IG -0.5, senior loans +0.5, Corp HY +0.5, EM debt +0.5, defensive US +0.5, US large +0.5, broad commodities +1, domestic cyclicals +1, DM intl +1, global cyclicals +1, US small +1.5, EM equity +1.5. The level is coincident, not leading (page 3). The signal is $\Delta\text{EFRoM}_t$: risk-on for the next month if the change is above 0 (page 4). Intuition: a rise in flow-weighted risk appetite leads risky asset direction.
- Data needed: ETF flows and AUM for 14 asset classes (we lack these).
- Evidence: very short. The 2016 note covers 16 months. The binary ACWI or IEI switch returns more than 21% against flat ACWI (page 4). The 60/40 portfolio with HYG in the risk-on basket runs Dec 2014 to May 2016. The EFRoM long version returns 10.8% a year with Sharpe 1.16, and the long-short returns 13.2% with Sharpe 1.91. The 60/40 benchmark returns 1.2% with Sharpe 0.13 (9 Jun 2016, page 5). The concurrent R² of the level against ACWI return is 0.42 (5 May 2016, page 3). These are backtests with no t-stats.
- HY applicability: low. The sample is 17 months and the HY leg is one of many.
- Fit to our signals: S7 replacement candidate, weaker than F5.
- Test: rebuild with TAARSS on available ETF or fund flow data, 2008-2024. Use $\Delta$EFRoM above 0 to hold HY and else Treasuries, monthly. Pass: Sharpe above buy-and-hold HY in at least 3 of 4 cycles.

### F7. Hedge fund 13F ownership of the issuer's equity as a credit signal (source: DB Alpha Capture, 5 Feb 2018, pages 4-12)
- Status: NEW for credit. It transfers an equity positioning signal.
- Definition. What the source says: the hedge fund aggregate (HFA) portfolio holds all hedge fund 13F long holdings in Russell 3000 stocks, value-weighted (page 7). The 13F lag is 45 days (page 7). Attribution against the Russell 1000: styles take 2.7% risk for 0.7% return. The residual (stock selection) takes 0.6% risk for 1.8% return (page 8). Hedge weights follow $w \propto \sqrt{\text{mcap}}$, which tracks inverse idiosyncratic volatility (page 12).
  What we propose: $\text{HFOwn}_{j,t} = \sum_{f\in HF}\text{shares}_{j,f,q}\,/\,\text{shares out}_{j,q}$, available at quarter end plus 45 days. Use $\Delta$HFOwn as an issuer-level signal for its HY bonds, residualised on equity momentum (EMC) and ESI.
- Data needed: 13F filings from SEC EDGAR (we have SEC access) and a hedge fund manager list. Thomson classification is the source's choice.
- Evidence: equity only. The source prints no IR for the residual leg in the text read.
- HY applicability: medium. Most HY issuers are public equity issuers. It overlaps with known EMC and ESI, so it needs an incremental test.
- Fit to our signals: new signal. It sits in the equity-information family next to EMC and ESI. The square-root weight rule is a portfolio construction tool for `outputs`.
- Test: quarterly, rank HY issuers by $\Delta$HFOwn residual to EMC and ESI. Measure the 3-month forward bond excess return. Pass: incremental rank IC > 0.02, t > 2, in at least 3 of 4 cycles.

### F8. Liquidity migration and cost break-even horizon (source: Citi FIMSAC, 11 Jan 2018, slides 12, 15-17)
- Status: variant of the liquidity sizing in `docs/framework.md` and of known issuer size. This is a gate, not a signal.
- Definition. What the source says: break-even days = round-trip duration-adjusted bid-ask cost over the daily yield accrual. Cost as % of yield rises from 4.03% (2007, 15 days) to 8.63% (2017, 32 days) for the Citi USBIG index (slide 12). Liquidity is transient: of the € bonds liquid in 3Q13, 44% stay liquid in 4Q13 and 25% by 2Q14 (slide 15, MarketAxess). Average daily trade count falls from 16.8 on day 1 to 4.6 on day 20 after issue (slide 16). HY bonds of $250m or less trade on fewer days (slide 17).
  What we propose: $\text{BE}_{i,t} = \dfrac{2\cdot\tfrac12 \text{BidAsk}_{i,t}\cdot D_{i,t}}{y_{i,t}/365}$. Reject a trade if the signal's expected holding period is below $\text{BE}_{i,t}$.
- Data needed: TRACE effective bid-ask (from paired dealer-customer trades), duration and yield.
- Evidence: descriptive only.
- HY applicability: medium. The HY bid-ask is wider, so the gate binds more often.
- Fit to our signals: the liquidity cells (conformal coverage per cell) and the cost step in `signals`.
- Test: apply the gate to S1-S3. Pass: net-of-cost IR rises and gross IR falls by less than 10%.

### F9. Calendar-month seasonality in spread changes (source: SystematicCreditUseCases.pdf, Use Case 7)
- Status: NEW candidate with no evidence.
- Definition. What the source says: regress $\Delta S_t$ on 11 month dummies. Each coefficient is the mean deviation against a base month (January effect, December window dressing).
- Data needed: TRACE G-spreads aggregated by rating.
- Evidence: none.
- HY applicability: low to medium. HY has known January and year-end liquidity patterns, but this document gives no numbers.
- Fit to our signals: a control variable for S1-S6 backtests, not a signal.
- Test: HY monthly G-spread changes 2003-2024 against month dummies with Newey-West errors. Pass: joint F-test p < 0.05 in both halves of the sample.

### F10. Direction-filtered positioning and the price-versus-positioning residual (source: GS Filtering CFTC positioning data, 9 May 2019, pages 1-4)
- Status: NEW.
- Definition. What the source says (pages 2-3). For investor class $c$ in week $w$, keep a tenor's net position change only when it moves with the market: net selling as yields rise, or net buying in a rally. Sum the kept changes, duration-weighted, into $	ilde F_{c,w}$ in \$mm/bp. Then fit, in sample (Jun 2006 to end 2010):
  $$\Delta y_w = a + b\,\tilde F_{c,w} + u_w, \qquad R^{(26)}_{c,t} = \sum_{w=t-25}^{t}\hat u_w$$
  Then z-score $R^{(26)}$. Signal: z above +0.25 means yields rose more than positioning implies, so expect a rally over the next 6 months. z below -0.25 means expect a sell-off. Intuition: the stable investor class (asset managers) sets the equilibrium price, and a price move beyond what that class's flow explains reverts.
  What we propose for HY: replace CFTC classes with TRACE customer net flow in HY bonds. Keep weekly flow only when it agrees in sign with the HY G-spread change. Regress the weekly HY spread change on the filtered flow. Use the 26-week cumulative residual z-score to predict the 26-week HY spread change. A sector-level version gives a cross-sectional signal (sector spread moved more than its filtered flow explains, so expect reversion).
- Data needed: source version uses CFTC CoT and TFF Treasury futures positions, which are public and free. No CFTC report covers US cash HY bonds. Our proxy uses TRACE side and size plus G-spreads.
- Evidence: 10y UST futures, Jun 2006 to Apr 2019, out of sample after 2010. The filtered asset manager flow correlates about 62% with the concurrent 6-month 10y yield change, and leveraged funds about 49% (page 2). A \$10mm/bp filtered change equals about 17-18bp of 10y yield (page 3). The 6-month residual for asset managers correlates -43% with the next 6-month yield change. Specs give -26%, leveraged funds -18%, and the raw 6-month yield change gives -35% (page 3). Outside the ±0.25 sd band, positive residuals precede a rally in 74.1% of 224 cases (mean -40bp). Negative residuals precede a sell-off in 66.8% of 253 cases (mean +21bp). The unconditional rally rate is 55.3% of 620 (page 4, Exhibit 5). Raw filtered positioning alone fails as a reversal signal (page 3). The 6-month windows overlap heavily, so the 620 cases are not independent.
- HY applicability: medium. The mechanism (price beyond what the stable holder's flow explains) transfers. The evidence is for Treasuries only, and TRACE does not tag investor class.
- Fit to our signals: S7 replacement candidate (HY beta timing). The sector version extends section 8 as a new signal.
- Test: weekly HY data 2005-2024, in-sample fit before 2011. Hold HY against Treasuries for 26 weeks when z > +0.25 and go short when z < -0.25. Pass: hit rate at least 60% on non-overlapping 26-week blocks, and the result beats the raw 26-week spread-change reversal rule.

## Top 3
1. F3, flow-induced selling pressure with a 4-month reversal (Dannhauser and Hoseinzade, RFS 2021). It has peer-reviewed same-issuer identification. The effect is 8.5-11.3bp for 4 months. We can build a TRACE-only proxy now, and it extends S6 with the S4 frame.
2. F1, the bias-corrected GAM fair-spread residual (SG SMS). It upgrades S1 directly. AIC selection, rank transforms and the own-history residual correction are cheap to add. The out-of-sample extreme deciles worked in 2009-2011.
3. F2, flow-trend strength as slope times R² (DB TAARSS) on TRACE net customer flow. It is a simple, new positioning signal from data we hold. The FI sector rotation beat the Agg (Sharpe 1.08 vs 0.72), but the test must find the issuer-level sign (continuation or reversal).

## Files not read
- None in the end. The listed CFTC file is a 286-byte shortcut, so I read its full copy from the USB Stick folder (path in the triage table). Fix the shortcut in the Research Platform folder if other tools need it.
