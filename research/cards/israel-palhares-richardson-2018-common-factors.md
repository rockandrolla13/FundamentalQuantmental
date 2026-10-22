# Israel, Palhares, Richardson (2018), "Common Factors in Corporate Bond Returns"

Peer-reviewed journal article, Journal of Investment Management 16(2), pp. 17–46. Authors from AQR Capital Management. Page numbers below are PDF pages (PDF page = journal page − 16).

## Claim
Four characteristics explain part of the cross-section of corporate bond excess returns: carry, defensive, momentum and value (p. 1). Defensive, momentum and value earn significant risk-adjusted returns. Carry does not earn a reliable premium alone (p. 11). An equal-risk mix of all four beats each one and survives transaction costs in a long-only portfolio (pp. 16, 19). Market risk premia and equity anomalies do not explain the returns. Mispricing evidence is strongest for momentum (p. 26).

## Method
1. Universe. Each month, keep one representative bond per issuer: senior, main rating class, 5 to 15 years to maturity when available, at most 2 years old when available, then the largest issue (p. 5).
2. Carry = option-adjusted spread (OAS) (p. 7). The authors accept that OAS misstates carry when the credit curve is not flat.
3. Defensive = equal-risk mix of three measures (pp. 8, 27):
   - low market leverage: net debt (book debt + minority interest + preferred stock − cash) / (net debt + market value of equity), with a six-month lag on statements;
   - high gross profitability: gross profits / assets (Novy-Marx 2013);
   - low effective duration.
   The authors exclude beta and volatility, because both mix duration and spread, and spread is carry (p. 8).
4. Momentum = equal-risk mix of the trailing six-month bond excess return and the trailing six-month issuer equity return (pp. 8, 27).
5. Value = spread relative to a default-risk anchor. A cheap bond has a high spread for its default risk (p. 9). Two measures (p. 27):
   - empirical: residual of a monthly cross-sectional regression of log OAS on log duration, rating, and 12-month bond excess-return volatility;
   - structural: residual of a regression of log OAS on the log of a structural default probability (Bharath and Shumway 2008 in the text, Shumway 2001 in the appendix table). Only issuers with listed equity have it.
6. A missing sub-measure scores zero, so the mix covers any issuer with one measure (p. 29, note 1).
7. Neutralisation. The authors demean each characteristic within five quintiles of duration times spread (DTS), an ex-ante beta. They exclude carry and duration from this step (p. 9).
8. Tests:
   - Fama–MacBeth regressions of next-month duration-hedged excess return on normalised ranks, with controls for market beta, rating, duration and age percent (p. 10);
   - value-weighted quintile portfolios, raw and scaled to 5% volatility (pp. 9, 12);
   - alphas against CREDIT, EQUITY, TSY, SMB, HML, UMD and QMJ (p. 15);
   - a long-only optimised portfolio with costs from Chen et al. (2007) by rating and maturity (pp. 17–18).
9. The combined score is an equal-weighted average of linear-in-ranks portfolios, each scaled to 5% volatility (p. 9).

## Data
1. Bank of America Merrill Lynch US Corporate Master and US High Yield Master constituents, monthly, January 1997 to April 2015 (p. 5).
2. 274,665 bond-months, 11,804 bonds, 4,296 issuers. The average month holds 1,247 bonds and $573bn notional, 59% investment grade and 41% high yield (pp. 5–6).
3. 48% of the universe links to Compustat (p. 5). Ratings are S&P, coded 1 (AAA) to 10 (D) (p. 6).
4. Horizon: one month ahead in all tests. The paper reports no rank information coefficient (IC).

## Result
1. Fama–MacBeth, one characteristic at a time (Table 3, p. 11): carry 0.00 (t 1.0), defensive 0.15 (t 5.0), momentum 0.15 (t 3.3), value 0.26 (t 5.8).
2. Fama–MacBeth, all four together (p. 11): carry 0.14 (t 2.3), defensive 0.03 (t 0.9), momentum 0.22 (t 7.1), value 0.30 (t 10.7). Average R-squared is 0.15.
3. Defensive loses significance next to value and momentum. The authors say their value anchors already hold leverage and profitability information (p. 11).
4. Quintile Q5 − Q1 Sharpe ratios (Table 4, p. 12):

   | Characteristic | Return | Volatility | Sharpe | Sharpe at 5% vol |
   | --- | --- | --- | --- | --- |
   | Carry | 4.1% | 11.7% | 0.35 | 0.19 |
   | Defensive | 2.7% | 2.4% | 1.11 | 1.21 |
   | Momentum | 2.9% | 3.4% | 0.85 | 1.12 |
   | Value | 3.9% | 2.2% | 1.75 | 1.80 |
   | Combined | 5.4% | 2.5% | 2.19 | 2.32 |

5. Carry correlates 0.80 with the credit market premium. Its loading on CREDIT is 0.58 (t 10.5), and its alpha is 0.05% per month (t 0.7) (pp. 14–15).
6. Monthly alphas (Table 6, p. 15): defensive 0.75% (t 5.3), momentum 0.55% (t 3.9), value 1.02% (t 8.1), combined 1.23% (t 9.6). The combined information ratio is 2.25 (p. 16).
7. Correlations among the four are low or negative. Carry vs momentum is −0.30. Defensive vs momentum is 0.40. Momentum vs value is −0.16 (p. 14).
8. Carry has its largest drawdown in the 2008 crisis (p. 13).
9. Long-only, net of costs (Table 7, p. 19): 5.26% excess return, Sharpe 1.03. The benchmark gives 3.84% and Sharpe 0.69. Active return is 2.20% with 2.56% tracking error, information ratio 0.86.
10. Long-only limits (p. 18): active weight within 25 bp per bond, OAS within 50 bp of the benchmark, duration within 0.5 years, turnover at most 10% per month, minimum trade $100,000.
11. Bond trading cost per unit of risk is more than four times that of equity (p. 16).
12. Risk tests: the combined portfolio does better when VIX and CPI rise and industrial production falls. It is a macro hedge, not a macro risk (Table 8, pp. 19, 21). Only value loads on broker–dealer leverage shocks (−0.18, t 2.2).
13. Mispricing tests: momentum returns are larger among bonds with low analyst coverage, low institutional ownership and small issue size (Table 10, pp. 23–24). Momentum longs get 5.7% higher sales revisions than shorts over 12 months (t 7.28). That revision maps to about 112 bp, one third of the 290 bp momentum premium (p. 26).

## What our data says
Our backtests use the TRACE high yield panel, 2008 to 2026. The measure is rank IC after cost. "Beyond spread" means IC after removal of the spread rank. Cycle windows are 2008, 2015, 2020 and 2022.

Where the paper agrees with our data:
1. Momentum adds to spread. Their joint t is 7.1. Our 3-month equity momentum (EMC) adds +0.038 beyond spread at 3 months (t 4.8) and +0.027 at 6 months. It is positive beyond spread in 3 of 4 cycles.
2. Momentum and value mix well. Their momentum–value return correlation is −0.16. Our ESP and EMC ranks correlate −0.11 (decision page `2026-10-22-onescore`). OneScore (ESP + EMC sector ranks) adds +0.034 at 6 months (t 2.1) in 3 of 4 cycles.

Where the paper differs from our data:
1. Carry. They find no standalone carry premium (t 1.0, Sharpe 0.35). Our "buy the widest" proxy gives net IC 0.27 at 6 months and 0.34 at 12 months, positive in all 4 cycles. Their sample mixes 59% investment grade with high yield and uses a one-month horizon. Ours is high yield only, at 6 and 12 months. We have not tested which difference explains the gap.
2. Value strength. Value is their strongest factor (t 10.7 jointly). Our value-type signals are weak beyond spread:
   - fair-line residual (leverage regression): +0.036 (t 2.2);
   - ESP (log spread minus sector x rating x maturity peer median): +0.072 at 6 months and +0.096 at 12 months (t 2.6, Section 7.4), but it fails 3 of 4 cycles beyond spread;
   - SPiDER (spread / (debt / 10-year mean EBITDA)): +0.032 at 12 months (t 1.3).
3. The two tests differ. Their value test controls for beta, rating and duration, plus DTS-quintile demeaning. Our beyond-spread test removes the full spread rank. Value is a spread residual, so our test is harder on it.
4. Defensive. They find a standalone defensive premium (t 5.0, Sharpe 1.11). We have no defensive or quality factor, so we cannot compare.

What we could adopt:
1. A defensive factor D1: equal-risk mix of low market leverage, high gross profitability (gross profits / assets) and low duration. Lag statements by our `available_at` rule, not a fixed six months. Test it beyond spread and beyond OneScore, because their joint t falls to 0.9.
2. Their empirical value: residual of log OAS on log duration, rating and 12-month excess-return volatility, fitted each month. It needs no fundamentals, so it covers private issuers. Compare it with ESP, which uses peer medians instead of a regression.
3. Credit momentum: the six-month bond excess return. Add it to EMC as an equal-risk mix and test whether it covers private issuers that EMC misses.
4. DTS-quintile demeaning of every non-carry signal. This is the neutral form the OneScore decision page asks for to fix the 2020 window.
5. Equal-risk combination with zero for a missing sub-measure. This keeps the score defined for issuers without listed equity.

## Limits
1. One-month horizon only. The paper gives no evidence at our 6- and 12-month horizons.
2. The sample ends in April 2015. It holds the 2008 and 2015 windows but not 2020 or 2022.
3. Investment grade is 59% of the sample. The paper shows no high yield subsample.
4. One bond per issuer removes curve and capital-structure effects. Our panel holds several bonds per issuer.
5. Factor definitions are composites with equal-risk weights. The paper does not report each sub-measure alone.
6. Compustat coverage is 48%, so defensive and structural value cover about half the issuers.
7. The authors work at AQR, which sells products built on these factors.
8. No IC is reported, so our IC figures and their Sharpe ratios and t-statistics are not directly comparable.

## Section touched
`docs/methodology.md` Section 7.4 (spread per unit of risk, peer signals) and Section 8 (Quantamental signals). Decision page `docs/decisions/2026-10-22-onescore.md`.
