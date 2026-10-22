# Gonzalez, Natividade and Thakkar (2018), "Factor Investing in Corporate Credit"

Deutsche Bank Cross Asset Quantitative & Derivatives Research, slide deck, distributed 31 July 2018. Sell-side research, not peer reviewed. 45 PDF pages, marked "do not redistribute". Page numbers below are PDF pages. PDF page = slide footer number + 1.

## Claim
Single-name CDS returns carry cross-sectional factor premia like those in equities. Value, low risk and momentum exist in US CDS after the authors remove credit beta with DTS (duration times spread). Value explains the most cross-sectional variance of all credit styles (p. 10). Value and low risk earn positive returns before costs, and both are weaker in HY than in IG (p. 17). Residual HY CDS returns and residual HY stock returns predict HY CDS returns at medium horizons. IG shows short-term reversal instead (pp. 20–21).

## Method
1. Attribution (pp. 8–10). Cross-sectional regressions of spreads on factor scores. The authors average each factor's marginal R-squared over all 720 orderings of a forward stepwise fit. This removes the effect of collinearity on the attribution.
2. Factor definitions (pp. 9, 13–14):
   - Value, attribution version: residual of a cross-sectional regression of spread on Merton distance to default and the 3-month spread change.
   - Value, trade version: fair spread minus market CDS spread. The fair spread comes from a time-series regression of spread on Merton distance to default. Distance to default follows Bharath and Shumway (2004): 12-month horizon, debt = short-term debt + long-term debt due within one year, drift = risk-free rate.
   - Quality, attribution version: ROIC and net debt to equity. Net debt = book debt + minority interest + preferred - cash.
   - Low risk, attribution version: S&P rating mapped to a 1 to 10 score (AAA = 1, D or SD = 10).
   - Low risk, trade version (marked "work in progress", p. 14): a quality index from EBITDA / interest, free cash flow / debt, net debt / EBITDA and EBITDA margin. Each ratio is ranked within its sector. Long the 1-year CDS (sell protection) and short the 5-year CDS (buy protection).
   - Size: net debt score, used only as a control. Other controls: GICS level 1 sector, and 252-day betas to MSCI USA, to credit (IG + HY) and to VIX.
   - Carry: named in the literature review (pp. 5–6) but not built.
   - Momentum (pp. 19–22): no backtest. The deck cites 6M-1M bond returns (Jostova et al. 2013) and 7M-1M standardised residual equity returns (Haesen et al. 2017). It runs panel auto-regressions of daily residual CDS mark-to-market on its own lag and on lagged residual stock returns. Residuals come from 1-year rolling regressions on the on-the-run index.
   - Reversal (pp. 24–29): name spread regressed on index spread. Enter when the 12-month mark-to-market R-squared exceeds 50% and the residual exceeds the largest of 2 standard deviations, 2 bid-offers and 10 bp. Hedge with the index at the mark-to-market beta. Exit when the residual falls below 0.5 standard deviations or at a stop loss.
3. Neutralisation (pp. 15–16). Signals are bucketed by DTS because "spreads by itself are predictors of credit returns". Sort within sector into quintiles. Long the top quintile, short the bottom quintile. Positions carry equal DTS, not equal weight or equal volatility. The deck states that DTS adapts faster than volatility in stress.
4. Portfolio construction (pp. 37–38). Minimum distance to target weights under four constraints: zero index beta, a rating cap, a position cap tied to average weekly volume, and a turnover limit. Covariance from shrunk EWMA estimates.

## Data
- Factor backtests: 5-year and 1-year single-name CDS of names that were in CDX.NA.IG (125 names) or CDX.NA.HY (100 names), January 2004 to June 2018. About 400 names in total. Financials excluded (p. 12).
- Attribution: about 225 on-the-run names as of December 2017, about 190 with listed equity (p. 8).
- Momentum regressions: 159 names with more than 80% data coverage (p. 20).
- Reversal: 5-year CDS of on-the-run CDX.NA.IG and iTraxx Europe ex-financials names since 2012 (p. 24). IG only.
- Rebalance frequency and holding horizon for value and low risk: not stated.

## Result
- PCA (p. 4): PC1 explains about 32% of weekly CDS returns, similar to the same firms' stocks. PC1 influence falls as the rating falls.
- Attribution (p. 10): value has the largest explanatory power among the credit styles. Betas matter most in 2008–2009 and 2011.
- Backtests before costs (p. 17): the deck reports annualised return, volatility, maximum drawdown and Sharpe ratio. No IC and no t-statistics.

| Strategy | Return | Volatility | Max drawdown | Sharpe |
| --- | --- | --- | --- | --- |
| IG + HY low risk | 0.47% | 0.50% | -0.72% | 0.94 |
| IG low risk | 0.49% | 0.53% | -1.67% | 0.92 |
| HY low risk | 0.32% | 0.97% | -2.46% | 0.33 |
| IG + HY value | 0.62% | 0.99% | -2.54% | 0.63 |
| IG value | 0.90% | 1.10% | -3.74% | 0.82 |
| HY value | 0.23% | 1.13% | -3.05% | 0.20 |

- Momentum (pp. 20–21): positive medium and long-term persistence of residual HY CDS returns. Residual HY stock returns lead residual HY CDS returns. The pattern is much weaker below B-.
- Reversal after costs (pp. 30–31): 67% of 241 European IG trades since September 2012 are profitable. 73% of 77 trades since March 2012 are profitable. The second slide title says European, but its footnote cites CDX.NA.IG series. It is probably the US test. Most trades last a few weeks. Jump to default and slow decoupling are the main losses (p. 32).

## What our data says (TRACE HY panel, 2008 to 2026, rank IC after cost)
Our numbers: buy the widest gives IC 0.27 at 6 months and 0.34 at 12 months, positive in all four cycle windows. ESP adds +0.072 beyond spread at 6 months (t 2.6) but fails three of four cycles. With a leverage control, ESP adds only +0.029 (t 1.2). SPiDER adds +0.032 at 12 months (t 1.3). Equity momentum (3-month stock return) adds +0.038 at 3 months (t 4.8), in three of four cycles. OneScore adds +0.034 at 6 months (t 2.1), in three of four cycles. We have no defensive or quality factor.

Where DB agrees with our data:
1. Spread level predicts returns. DB neutralises it out with DTS for this reason (p. 15). Our widest-spread result is the same fact, and it is the strongest signal we have.
2. Value is weak in HY once spread level is removed. DB HY value has Sharpe 0.20 before costs (p. 17). Our ESP and SPiDER give small, unstable beyond-spread ICs.
3. Equity information leads HY credit at medium horizons (p. 21). Our 3-month equity momentum is the most significant beyond-spread signal (t 4.8).

Where DB differs:
1. DB trades CDS on CDX names. We trade cash bonds across the TRACE HY universe, which holds smaller and less liquid issuers.
2. DB value anchors on Merton distance to default. Our ESP anchors on peer median spread. DB never tests value against a peer anchor.
3. DB removes spread level with DTS buckets and DTS-equal weights. We remove the spread rank from the signal rank. The two may not give the same answer.
4. DB reports Sharpe ratios before costs, with a sample that ends in June 2018. We report IC after costs in four cycle windows, including 2020 and 2022.
5. DB finds low risk stronger than value in HY (Sharpe 0.33 against 0.20). We have not built low risk.

What we could adopt:
1. Low risk factor. Build the DB quality index: EBITDA / interest, free cash flow / debt, net debt / EBITDA and EBITDA margin, each ranked within sector. Test: beyond-spread rank IC after cost at 6 and 12 months, positive in at least three of four cycles.
2. Merton value. Compute Bharath-Shumway distance to default for listed issuers. Take the residual of log spread on distance to default as a second value signal beside ESP. Test: beyond-spread IC against ESP on one common sample.
3. DTS-bucket check. Repeat our beyond-spread tests with sorts inside DTS buckets and sectors. Test: the sign and the cycle count match our rank-removal result.
4. Momentum refinements. Use residual stock returns (stock return minus beta times market return) with a one-month skip (7M-1M). Report results above and below B-. Test: residual 7M-1M against raw 3-month on the same sample.
5. Liquidity cap. Cap each position at a fraction of average weekly volume, as DB does (p. 37). Section 8 already has `n_i <= k * ADV_i`, so this needs no change.

## Limits
- Slide deck: terse, no appendix of tables, no IC, no t-statistics, no cycle split.
- Value and low risk results exclude transaction costs (p. 12). Only the reversal tests include costs.
- CDS on index constituents only. CDX.NA.HY holds 100 names, which are the larger and more liquid HY issuers.
- Low risk trade version is work in progress (p. 14). Momentum has no portfolio backtest.
- Sample ends June 2018. It misses the 2020 and 2022 cycles.
- Rebalance frequency, signal lag and survivorship treatment are not stated.
- One slide label (p. 31) appears to contradict its footnote.

## Section touched
`docs/methodology.md` Section 7.4 (Merton value as a second cross-issuer anchor beside ESP and SPiDER) and Section 8 Signals (low risk factor, residual equity momentum, DTS-bucket neutralisation). Decision page `docs/decisions/2026-10-22-onescore.md`.
