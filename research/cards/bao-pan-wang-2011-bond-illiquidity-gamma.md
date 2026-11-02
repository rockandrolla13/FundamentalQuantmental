# Bao, Pan, and Wang (2011), "The Illiquidity of Corporate Bonds"

The Journal of Finance 66(3), pp. 911–946, DOI 10.1111/j.1540-6261.2011.01655.x. Peer-reviewed journal article. We read the authors' final manuscript of July 15, 2010, with its Internet Appendix (55 PDF pages). The live MIT DSpace file (hdl.handle.net/1721.1/75381) returned HTTP 429. So we read the Internet Archive copy of that same open-access file: https://web.archive.org/web/2022/https://dspace.mit.edu/bitstream/handle/1721.1/75381/Pan_The%20illiquidity.pdf. The volume and pages come from the cover page. Page numbers below are PDF pages. PDF page = manuscript page + 2.

## Claim
Corporate bond illiquidity is large and exceeds what bid-ask spreads explain (p. 2). A bond-level measure from price reversals explains cross-section yield spreads with large economic size, after controls for fundamentals and bond characteristics (pp. 4, 28). Aggregate illiquidity explains monthly spread changes of bonds rated A and above. It matters less for junk bonds, where credit risk matters more (p. 17).

## Method
1. **Price split (p. 9, eq. 1).** `f_t` is a random walk. `u_t` is transitory and has no correlation with `f_t`.

```latex
p_t = f_t + u_t, \qquad \gamma = -\operatorname{Cov}(\Delta p_t, \Delta p_{t+1}) \quad (1,2)
```

Intuition: illiquidity pushes the price away from value for a short time, so price changes reverse, and the size of the reversal measures illiquidity.

2. **Link to the bid-ask spread (p. 21, eq. 4).** In the Roll model, the implied spread follows from gamma.

```latex
s^{Roll} = 2\sqrt{\gamma}
```

Intuition: if bid-ask bounce were the only friction, the reversal would equal half the spread squared.

3. **Estimation.** Log clean prices, trade-by-trade or daily, by bond and by month. At least 10 paired price changes per estimate (p. 30, note 10). The price change spans at most one week (p. 30, note 10). The authors delete repeated inter-dealer trades (p. 7). Standard errors cluster by bond and by day (p. 30, note 11).
4. **Bond-level test (pp. 17–20, Table VI).** Monthly Fama-MacBeth regression of the yield spread on gamma, a call dummy and rating dummies. Added controls: equity volatility, CDS spread, age, maturity, log issuance, turnover, trade size, trade count, percent of days traded, quoted bid-ask spread. Newey-West errors.
5. **Aggregate test (pp. 16–17, Table V).** Regress the monthly change in index yield spread on the change in aggregate gamma. Aggregate gamma is the cross-section median. The controls are the CDS index, VIX, bond volatility, term spread and lagged returns.
6. **Reversal decay (p. 24, eq. 6).** `gamma_tau` for lags 1, 2 and 3.

## Data
- FINRA TRACE, Phase I and Phase II bonds, April 14, 2003 to June 30, 2009 (p. 7). The bond-level sample holds 1,035 bonds (p. 7).
- **Investment grade only.** The authors exclude junk bonds, because the Phase I and II junk bonds were chosen for liquidity (p. 7).
- Selection: a bond must trade on at least 75% of business days and exist for at least one year in TRACE (p. 7).
- Sample bonds are more liquid than TRACE as a whole: monthly turnover 7.51% against 3.71%, and 208 trades a month against 33 (p. 8).
- Other sources: CRSP, FISD, Bloomberg quoted bid-ask, Datastream CDS and Barclays indices, CBOE VIX (p. 8).

## Result
**Size (Table II, p. 41).** Daily data: mean gamma 1.18 (robust t 16.53), median 0.56. Trade-by-trade: mean 0.63 (t 19.42), median 0.34. The median gamma implies a bid-ask spread of 1.50%, against a median quoted spread of 0.28% (p. 6).

**Portfolio level (Table II, p. 41).** Equal-weight portfolio gamma is −0.0050 (t −0.71). The authors read this as an idiosyncratic transitory part that diversifies away (p. 11).

**Commonality (pp. 12–13).** Aggregate gamma averaged 0.30 before August 2007 and peaked at 3.37 in October 2008 (p. 14). Its change regressed on the VIX change has R² above 67%, and 33% with 2008 and 2009 removed (pp. 14–15).

**Bond characteristics (Table III, p. 42).** One more year of age adds 0.19 to gamma (t 2.98). Log issuance has −0.56 (t −2.26). Maturity has +0.05 (t 2.18).

**Cross-section of spreads (Table VI, p. 45).**
- Gamma alone with rating and call dummies: 0.17 (t 9.60). So one unit of gamma adds 17 bp (p. 18). The mean cross-section R² rises from 19.00% to 30.27% (pp. 18–19).
- The cross-section standard deviation of gamma is 2.03 (p. 18). One standard deviation sets two bonds of one rating apart by 35 bp (p. 28).
- With the CDS spread: gamma 0.12 (t 6.69), CDS 0.69 (t 12.94).
- Age, with gamma in the regression: 0.01 (t 0.89). Quoted bid-ask with gamma: 0.18 (t 0.47).
- Percent of days traded: 0.01 (t 3.12), which the authors call the wrong sign (p. 20).

**Aggregate spread changes (Table V, p. 44).**

| Index | Gamma alone (t) | Adj. R² | Gamma with controls (t) | Adj. R² |
| --- | --- | --- | --- | --- |
| A, full sample | 1.074 (8.55) | 59.86% | 0.879 (7.87) | 85.12% |
| Junk, full sample | 2.114 (4.22) | 23.22% | 0.348 (0.64) | 85.50% |
| Junk, before 2008 | 3.678 (4.67) | 29.40% | −0.063 (−0.10) | 80.25% |

The CDS index carries the junk result: 1.461 (t 3.25) in the full sample, and 3.025 (t 9.85) before 2008.

**Decay (Table VIII, p. 47; Table IA.V, p. 55).** Trade-by-trade: 0.628 at lag 1, 0.124 at lag 2, 0.030 at lag 3. Daily: 1.177 at lag 1 and −0.001 at lag 2. By horizon: 1.21 weekly (p. 11), 1.16 bi-weekly and 0.80 monthly (t 2.02). Only 17.09% of bonds are significant at the monthly horizon (p. 30, note 13).

**Asymmetry (Table IX, p. 48).** Reversal after a price fall exceeds reversal after a price rise by 0.2326 on daily data (robust t 5.59).

## Limits
- Investment grade only at bond level. The paper gives no bond-level result for high yield (p. 7).
- The 75% trade-day filter selects liquid bonds. Most HY bonds would fail it, so the measure may lose coverage where it matters most. The paper does not test that.
- Yield spread levels are not returns. The authors find returns too noisy to test risk factors on this sample (p. 6).
- Gamma does not separate transitory frictions from short-term risk premia. The authors assume no time-varying premium over short horizons (p. 30, note 9).
- Source inconsistency: the text says quoted bid-ask spreads relate negatively to yield spreads in the last two columns of Table VI (p. 19). Table VI shows +0.18 and +0.02 there (p. 45). Table AI, for non-callable bonds, shows −0.53 and −0.50 (p. 34).
- Sample ends June 2009 (p. 7).

## Section touched
`docs/methodology.md` Section 7.2 (liquidity block of `x`), Section 7.3 (noise scale `sigma(x)`), Section 7.5 (residual half-life), Section 9 (event windows). Related factor: `docs/factors/F13-realized-illiquidity.md`, which uses Amihud, not gamma.

## Use for the two clocks
**What the source says.** Reversal-based illiquidity explains investment grade spreads beyond rating, equity volatility and CDS (p. 45). Quoted bid-ask and age add nothing once gamma enters (p. 45). In the aggregate, junk spread changes follow the CDS index, not gamma (p. 44).

**What our data says.** No gamma exists on our panel, and no test has run. Section 7.2 lists `bid_ask_bp`, `log amount_outstanding`, `trace_count` and bond age as the liquidity block. `renewal_split_test` in `scripts/backtest_clocks.py` regresses log spread on a constant and the two shares only. So the Section 4.7 result of +0.36 and −2.07 has no liquidity control and no other control.

**What we decide (our proposal, not the source's claim).**
1. **Liquidity step in every clock test.** Add monthly gamma from daily TRACE prices to the liquidity block of Section 7.2. Report the coefficient on each clock share with and without gamma. If the coefficient moves toward zero, the clock proxies for trade friction. In speculative grade, pooled Roll has a negative sign and no significance (t −0.12 and −1.16), while a composite `lambda` is significant (`dick-nielsen-feldhutter-lando-2012-corporate-bond-liquidity.md`, Table 3). So use the composite as the main HY control, and report gamma beside it.
2. **Do not copy the 75% filter.** Keep the 10-pair minimum (p. 30, note 10). Report gamma coverage by rating class, and treat missing gamma as a separate flag.
3. **Noise test of the S1 residual.** In liquid investment grade bonds, reversal ends after a few trades (p. 24, Table VIII, p. 47) and within a day (p. 24, Table IA.V, p. 55). The sample is investment grade only, with a 75% trade-day filter, and it leaves junk out on purpose (p. 7). No opened source tests this in HY. So a one-week skip is Our choice, v0, and lag decay by rating needs a measure before the skip length is fixed. A residual that closes in the skip window may be friction. This adds to the half-life of Section 7.5, because the AR(1) at monthly frequency sees only what survives a month.
4. **Scale for the band.** Use gamma as an input of `sigma(x)` in Section 7.3. Test: conformal coverage by liquidity cell improves against the current block.
5. **Risk taking.** Do not use aggregate gamma as a risk gauge for HY beyond a CDS index until a test supports it (p. 44). This keeps Section 9 unchanged.
