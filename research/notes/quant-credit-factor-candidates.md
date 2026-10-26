# New factor candidates from the Quant Credit folder (ranked)

Source folder: `/home/ak/Documents/Quant Credit` (about 310 files after duplicates). Nine readers triaged every file on 2026-10-26. Their full reports are in `research/notes/quant-credit-review/out_*.md`. Each block there gives the formula, data, evidence with pages, and a test. `known_factors.md` in the same folder lists what the readers treated as already known.

## How we ranked
1. Evidence: a published result in corporate bonds or CDS ranks first. Evidence from another asset class ranks next. A definition with no result ranks last.
2. Data: a factor that our data builds (TRACE with side and contra-party flags, Compustat point-in-time, SEC filings, equity returns, Treasury curve, FRED) ranks above one that needs new data.
3. HY fit: the effect must plausibly hold in US high yield.

"Block" points to the reader report and block number, for example `A2-F4` is block F4 in `out_A2.md`. Evidence is what the source says. No test has run on our data.

## Tier 1. Tested in credit, buildable now
| Rank | Factor | Evidence (source) | Block | Signal hook |
|---|---|---|---|---|
| 1 | IPCA conditional factor model (bond loadings from characteristics) | ICE HY and IG 1999–2020. Out-of-sample net Sharpe 2.48 at 19 bp one-way cost. HY out-of-sample R² about 46–48% (Kelly, Palhares, Pruitt 2021) | A2-F4 | New aggregator over S1–S7 |
| 2 | Spread to distance-to-default (with a CreditGrades variant) | Characteristic portfolio Sharpe 1.25, IG and HY 1999–2020 (same paper). CreditGrades gap with self-calibrated volatility (cap arb notes) | A2-F5, C-F5 | Variant of S1 value |
| 3 | Residual equity momentum spillover | HY panel Sharpe 0.73, 1.14 after a default-factor hedge (t 4.58). Cuts the 2009 drawdown from 80% to 25% (van Zundert 2018) | H-F11 | Variant of EMC |
| 4 | Volatility-adjusted and residual bond momentum | Works in BB and B where raw momentum fails (van Zundert 2017). Residual version doubles Sharpe in equities (Blitz 2011). Warning: raw 6-month bond momentum reverses, Sharpe −0.84 (A2-F8) | H-F10, D-F5, A2-F8 | New momentum leg |
| 5 | Flow-induced selling pressure, same-issuer reversal | ETF-outflow bonds widen 8.5–11.3 bp more than a same-issuer bond, for about 4 months, then revert (Dannhauser and Hoseinzade 2021) | E-F3, B-F1, B-F3, A2-F15 | Extends S6, S4 setup |
| 6 | Within-issuer curve residual on par-adjusted spread | EM USD bonds 2006–2011: IR 1.20 before cost, 0.81 after 20 bp (JPM 2012). Par adjustment removes the price bias that HY bonds at 40–90 suffer (Martin) | G-F1, A2-F1, A1-F1, B-F12 | Extends S4 |
| 7 | Merton-restricted machine-learning bond forecast | TRACE July 2002–Dec 2017, 25% HY observations (Bali et al. 2022) | H-F7 | New forecast structure |
| 8 | LEVER event-risk score, and the LEVER x spread corner trade | 63% of LBOs fall in the top LEVER quartile, S&P 1500 1995–2005. Corner trade IR 1.04, IG only, zero cost (Lehman 2006, 2007) | H-F1, H-F2, H-F3 | S5, Section 9 |
| 9 | Profitability change over 5 years | Characteristic portfolio Sharpe 0.60, IG and HY 1999–2020. Level alone 0.14 (Kelly et al.) | A2-F7 | Extends S2 |
| 10 | Market-neutral credit carry | CDS indices: Sharpe 0.86 after cost, max drawdown 16% (JPM 2018) | G-F3 | Variant of carry |

## Tier 2. Tested in credit, needs data we may lack
| Rank | Factor | Evidence (source) | Block | Data needed |
|---|---|---|---|---|
| 11 | Change in option implied volatility | Bonds rated B and below: alpha −0.69% a month (t −2.14). Predicts downgrades (Cao, Goyal, Xiao, Zhan 2023) | C-F1 | OptionMetrics |
| 12 | HY ETF pressure and contraflow | Equity ETF contraflow Sharpe 1.29. Arbitrage sensitivity alpha −0.65% a month, equities | B-F9, A2-F12, A2-F13 | ETF flows and holdings |

## Tier 3. Tested outside credit, or weak credit evidence, buildable now
| Rank | Factor | Evidence (source) | Block | Signal hook |
|---|---|---|---|---|
| 13 | Realized bond illiquidity (Amihud), level and shock | SPY 2006–2018 only (Lacava 2023). Illiquidity is the top feature group in Bali et al. | F-F7, F-F8 | New, also a cost gate |
| 14 | Bond abnormal trading volume | Positive slope t 2.10 as a control (Cao et al. 2023). Abnormal trading before events (TRACE study) | C-F3, A1-F17 | New, Section 9 |
| 15 | PCA residual reversal with an Ornstein-Uhlenbeck s-score | Equities net Sharpe 0.75–1.19. Bond bid-ask bounce is a risk | F-F9, G-F2, B-F11 | New short-horizon leg |
| 16 | Bond downside risk (5% VaR) | Second most important feature group in Bali et al. No standalone premium in the file | H-F8 | New risk leg |
| 17 | Bond return skewness | Sharpe −0.67 alone. Not significant once other characteristics enter | A2-F6 | Control |
| 18 | Equity-credit discordance | Kapadia and Pu 2012, CDS. Pre-crisis HY result weak | C-F4 | Variant of EMC |
| 19 | Owner cash flow to debt (maintenance capex adjusted) | Equities 1997–2018. DB credit note found plain FCF to debt inconclusive | F-F11 | Extends S1 inputs |
| 20 | Tail dependence of spread changes with the market | CDX IG and HY 2001–2014, t-copula coefficient 0.85 | A2-F10 | Low-risk variant |

## Tier 4. Definitions with no backtest, buildable now
| Rank | Factor | What it is | Block | Signal hook |
|---|---|---|---|---|
| 21 | Refinancing headroom against cyclicality | The EBITDA cut a firm survives for two years before refinancing, against its worst year in 10 | H-F4 | S3, Section 9 |
| 22 | Credit curve shape against level (term premium) | Slope and curvature that the spread level does not explain | B-F13, A1-F7, D-F8, D-F9 | Extends S4 |
| 23 | Margin squeeze: producer minus consumer prices by sector | Thin-margin HY issuers lose when input costs outrun prices | B-F18 | Sector input |
| 24 | Rating x tenor cell valuation percentile | Each rating and maturity cell against its own spread history | F-F3, G-F10 | Curve and quality tilt |

## Tier 5. HY index timing (candidates to replace S7)
| Rank | Factor | Evidence (source) | Block |
|---|---|---|---|
| 25 | Credit-BMI v2 composite with dealer positions and a rating-bucket common factor | Second-hand hit rates 67% IG, 62% HY (Morgan Stanley). Your own spec, FRED inputs | B-F14, B-F15, B-F16, A2-F11, H-F13 |
| 26 | HY index time-series trend | Crossover CDS index live 2012–2015: Sharpe 1.0, max drawdown −7.4% (JPM 2015) | G-F4 |
| 27 | Real-yield shock regime | HY spreads tightened a median 65 bp in the 6 largest rate sell-offs since 2008. The real-against-inflation split is untested | F-F1, G-F9 |
| 28 | HY index fair value gap net of carry | FX: about 50% of a gap closes in 18 months (JPM 2009) | G-F5 |
| 29 | Macro momentum: PMI and earnings revision ratio | Government bonds since 1998: IR 0.59 and 0.84 (JPM 2015) | G-F6, F-F5 |
| 30 | HY spread against VIX gap | Screen only, no result | A1-F16 |

## Methods found, not factors
- Error-reduction ratio to test the fair spread model (D-M1).
- No-trade band that scales with the cube root of cost (A1-F3).
- Expected convergence share q(h) and a deterioration gate on convergence trades (A2-F2, A2-F3).
- DTS-scaled information coefficient and replication hurdles (D-M6, D-M7).
- Coverage backtests for conformal bands (G triage, Campbell 2005).

## Dropped
- Restates a known factor: industry equity leads industry credit (book ch. 16), spread per unit of leverage (SPiDER), MS six-rule screen.
- No usable data or evidence: media sentiment, calendar seasonality, 13F hedge fund ownership, CFTC positioning for HY, HY reinvestment cash flow (needs amount outstanding), lead-underwriter distress flag (one event).
- Ratings after February 2017 needed: split ratings, bond against issuer rating gap, notch within letter (D-F1 to D-F3). Revisit if the production machine has a rating feed.
