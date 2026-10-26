# Ben Dor, Desclée, Dynkin, Hyman and Polbennikov (2021), *Systematic Investing in Credit*: implementation spec per chapter

Companion to `dynkin-et-al-2021-systematic-investing-in-credit.md` (signal chapters) and `dynkin-et-al-2021-spreads-predict-defaults.md` (credit cycle). This file gives one build spec per chapter, 1 to 21.

## How to read this file
- Page numbers are PDF pages of the repo-root file. For chapters 13 to 21, PDF page = book page + 28.
- Each chapter has the same parts: question, answer, data, definitions and formulas, steps, results, variants, limits, and implementation in this repo.
- Readers took every table number from the page image, not from the text layer. Charts without data labels give approximate values, and each is marked.
- "Our reading" marks a formula or rule that the book does not print. Treat it as a hypothesis, not as the book's method.
- The section "Implementation in this repo" is what we decide, not what the book says. No test in this file has run yet.
- Each chapter lists the printing errors that its reader found in the book.

## Priority index for the HY analyst
Rank 1 is the next test to build. "HY evidence" means the book reports high yield results.

| Rank | Ch. | Effect | HY evidence | Main data gap | Repo hook |
|---|---|---|---|---|---|
| 1 | 5 | Issuer issuance aggressiveness (liability growth over assets) | Mixed IG and HY | None: Compustat | S2, `hy/signals.py` |
| 2 | 19, 13, 15 | OneScore fixes: combined EMC, 3-year filter, DTS-neutral legs | EMC yes, ESP no | Amount outstanding | `hy/peers.py` |
| 3 | 18 | Turnover buffer (top 20% buy, bottom 45% sell) and cost model | IG only | Barclays LCS and TES | §7.5 cost line, `hy/backtest.py` |
| 4 | 8 | Spread-conditioned rating transition matrix | IG rows only | Ratings end Feb 2017 | PD by cycle, `hy/calibration.py` |
| 5 | 16 | Sector timing on equity momentum | Yes, +4.04%/yr | Sector aggregation rule | Replaces S7 |
| 6 | 14 | SPiDER within industry, debt-to-cash variant | Yes, IR 0.73 | None | §7.4 |
| 7 | 21 | Equity short interest (downgrade predictor) | Yes, one-sided | FIS Astec loans | S6, §9 |
| 8 | 20 | Post-earnings drift on EAR | Yes, 1.94% at 60 days | I/B/E/S for CFE only | S3, §9.5 |
| 9 | 2, 3, 4, 9 | Fallen angels, FAR score, stop-loss cost | Yes | Rating history | S6 |
| 10 | 10, 11, 17 | Coupon, maturity roll-down, issuer size | Size yes | Amount outstanding | §7.2 controls |
| 11 | 12 | Governance tilt | Yes, 10.3 bp/month | ESG vendor scores | Flag from SEC filings |
| 12 | 1, 6, 7 | Credit vs equity plus Treasuries, inclusion delay, new-issue concession | Ch. 1 yes | New-issue deal data | Risk check only |


---

## Chapter 1. Can a Combination of Treasuries and Equities Replace Credit in a Portfolio? (PDF pp. 31–100)

Page range note. The brief gave PDF pp. 43–108. The chapter starts on PDF p. 31 (book p. 3) and ends on PDF p. 100 (book p. 72). PDF pp. 101–106 hold the Part Two introduction, which frames Chapters 2 to 9. PDF pp. 107–108 are a part divider. This spec covers PDF pp. 31–100 and lists the Part Two framing at the end.

**Question.** Does credit add return that a risk-matched mix of same-issuer equity, Treasuries and cash cannot replicate?

**Answer.** Yes. From January 1993 to December 2019, issuer-matched bond portfolios beat a risk-matched mix of the same issuers' equity, 10y Treasuries and T-bills by about 1.6%/yr in IG and 2.4% to 3.4%/yr in HY. The information ratios (IR) are 0.47 to 0.84 (Table 1.4, PDF pp. 52–53). Equity variance risk premium (VRP), short Treasury puts and the betting-against-beta (BAB) factor explain most of the gap (Table 1.8, PDF pp. 69–70).

### Data

The book says:
- **Asset-allocation part (PDF p. 36).** S&P 500 total return (with dividends). Bloomberg Barclays US Treasury Index. Credit is the market-value-weighted combination of the Bloomberg Barclays US Corporate (IG) and US High Yield indices, in total return. Cash is the 3m T-bill. Monthly, January 1993 to December 2019.
- **Issuer-level universe (PDF p. 44).** All issuers in the Bloomberg Barclays US Corporate and US High Yield indices, January 1990 to December 2019. The authors link each issuer to Compustat equity with the proprietary Ben Dor and Xu (2015) bond-to-equity mapping (note 6, PDF p. 98).
- **Filters (PDF p. 44).**
  1. Drop bonds with price below $40. Note 7 (PDF p. 98) says results do not change without the price filter.
  2. Drop the whole company (bonds and equity) when the mapped equity is an ADR, trades OTC, or trades outside the US.
  3. Drop penny stocks with beginning-of-month price below $1.
- **IG and HY run separately** because of market segmentation (PDF p. 44).
- **Bond aggregation.** The authors aggregate all index bonds of one issuer to one issuer return with bond market-value weights (note 8, PDF p. 98).
- **Coverage (Table 1.1, PDF p. 45), share of index market value.**

| Year end | IG pop. ($bn) | IG mapped | IG in final sample | HY pop. ($bn) | HY mapped | HY in final sample |
|---|---|---|---|---|---|---|
| 1994 | 513 | 91% | 78% | 133 | 71% | 47% |
| 1999 | 900 | 94% | 84% | 353 | 72% | 50% |
| 2004 | 1,691 | 95% | 77% | 599 | 82% | 69% |
| 2009 | 2,548 | 96% | 81% | 704 | 71% | 62% |
| 2013 | 3,703 | 96% | 80% | 1,260 | 67% | 57% |
| 2017 | 5,172 | 97% | 80% | 1,321 | 81% | 72% |

  The text (PDF p. 46) says coverage reaches 97% (IG) and 81% (HY). Those are the "mapped" row, not the final sample row.
- **Factors.** Market factor: S&P 500 total return. Rate factor: 10y on-the-run (OTR) Treasury portfolio. Variant: the Treasury Index as both factor and hedge asset (Appendix 1.1, PDF p. 76).
- **Option data.** SPX options from OptionMetrics, from January 1996 (note 15, PDF p. 99). 10y Treasury futures options from CME (note 16). Fama-French five factors and momentum from Ken French's library. BAB from AQR (source line, PDF p. 70). Table 1.8 runs January 1996 to December 2019 (PDF p. 70).
- **Liquidity.** Liquidity Cost Score (LCS), Barclays proprietary, from January 2007 (Tables 1.15 and 1.16, PDF pp. 92–93).
- **Europe (PDF pp. 80–84).** Bloomberg Barclays Pan Euro Corporate and Pan Euro HY indices, mapped to Compustat (Ben Dor, Guan and Zeng 2018 mapping, note 20). Market factor: Stoxx 600. Rate factor: Bloomberg Barclays Euro 7–10yr Treasury index (note 21, PDF p. 100). Period: May 2005 to December 2019 (Table 1.11 note, PDF p. 83).

### Definitions and formulas

**A. Credit-index replication (asset-allocation part).** Note 5 (PDF pp. 97–98). Each month s, regress the credit index total return on the S&P 500 and Treasury Index total returns over the trailing 36 months:

```latex
R^{Credit}_{\tau} = \alpha + w_E\, R^{S\&P500}_{\tau} + w_{Tsy}\, R^{TsyIndex}_{\tau} + \varepsilon_{\tau}, \quad \tau = s-36,\dots,s-1
```
Intuition: the slopes are the equity and Treasury mix that best tracks credit month to month.

```latex
w_{T\text{-}bill} = 1 - w_E - w_{Tsy}
```
Intuition: cash takes the residual weight. The weights are used for the coming months.

- Weighted least squares with exponential decay, half-life 9 months (note 5). Equal weights and other half-lives give similar results.
- Average weights: 16% equity, 81% Treasuries, 3% T-bills (PDF p. 39).
- **Reallocation effect** = SR(benchmark + x% replication) − SR(benchmark). **Credit-specific effect** = SR(benchmark + x% credit) − SR(benchmark + x% replication) (PDF p. 40).
- The x% added replaces equity and Treasuries in the benchmark's own ratio. Example: x% credit in a 60/40 benchmark removes 0.6x% equity and 0.4x% Treasuries (PDF p. 40).

**B. Issuer-matched sensitivity matching (main method).** Note 11 (PDF p. 98).

Step 1. Form a bond portfolio and an equity portfolio with the same issuers and the same issuer weight w_i in each. Four weight schemes (PDF p. 46):
- EW: equal weight.
- Bond-VW: issuer bond market value.
- Equity-VW: issuer equity market cap.
- Total-VW: bond market value plus equity market cap.

Step 2. Estimate sensitivities in month t over the trailing 36 months (τ = t−36, …, t−1), exponential-decay weighted, half-life 9 months (PDF p. 48, note 10, PDF p. 98; half-life stated on PDF p. 97):

```latex
R^{Bond}_{\tau} = a_{B,t} + \beta_{B,t}\, SP500_{\tau} + \gamma_{B,t}\, Tsy10y_{\tau} + \varepsilon_{B,\tau}
```
```latex
R^{Equity}_{\tau} = a_{E,t} + \beta_{E,t}\, SP500_{\tau} + \gamma_{E,t}\, Tsy10y_{\tau} + \varepsilon_{E,\tau}
```
Intuition: each portfolio has a market beta and a rate beta. The 10y OTR has rate beta 1 and market beta 0 by construction.

Step 3. Solve two equations for two unknowns:

```latex
\beta_{B,t} = W_{E,t}\,\beta_{E,t}, \qquad \gamma_{B,t} = W_{E,t}\,\gamma_{E,t} + W_{T,t}, \qquad W_{RF,t} = 1 - W_{E,t} - W_{T,t}
```
Intuition: equity weight matches the market beta. Treasury weight fills the rate beta that equity does not supply. T-bills take the rest.

```latex
R^{Repl}_{t} = W_{E,t}\, R^{EqPort}_{t} + W_{T,t}\, R^{Tsy10y}_{t} + W_{RF,t}\, R^{3mTbill}_{t}
```
```latex
R^{BoR}_{t} = R^{BondPort}_{t} - R^{Repl}_{t}
```
Intuition: the bond-over-replication (BoR) return is the part of credit that same-issuer equity and Treasuries cannot copy.

- Regressions use bond **total** returns (Table 1.2 note, PDF p. 50). Our reading: the dependent variables are total returns, not excess returns. The baseline of Table 1.8 uses factor returns in excess of the 3m T-bill (PDF p. 68).
- The book does not say whether weights are fixed or drift within the month. Our reading: set weights at month-end t−1 and hold one month.

**C. Volatility matching (variant).** Note 12 (PDF p. 98):

```latex
R^{VolRepl}_{t} = HR_t\, R^{EqPort}_{t} + (1-HR_t)\, R^{3mTbill}_{t}, \qquad HR_t = \frac{\mathrm{Vol}(R^{BondPort})_{t-36,t-1}}{\mathrm{Vol}(R^{EqPort})_{t-36,t-1}}
```
Intuition: scale equity down until its trailing volatility equals the bond portfolio's. No Treasury leg.

**D. Analytical (Merton) hedge ratios (variant).** Note 13 (PDF p. 99):

```latex
HR^{equity} = \frac{\partial D / D}{\partial E / E} = \left(\frac{1}{\partial E/\partial V} - 1\right)\frac{E}{D}, \qquad \frac{\partial E}{\partial V} = N(d_1)
```
```latex
d_1 = \frac{\ln\!\left(V / book\_debt\right) + \left(r_f + \sigma^2/2\right)T}{\sigma\sqrt{T}}
```
```latex
D = \frac{MV_{index\ bonds}}{AmtOutstanding_{index\ bonds}}\cdot book\_debt, \qquad V = D + E
```
```latex
\sigma^2 = \left(\frac{E}{V}\right)^2 \sigma^2_{E,\,option\ implied\ ATM} + \left(\frac{D}{V}\right)^2 \sigma^2_{D\,(DTS)} + 2\left(\frac{E}{V}\right)\left(\frac{D}{V}\right) Corr_{DE}\,\sigma_E\,\sigma_D
```
Intuition: the bond is short a put on firm assets. Its sensitivity to equity rises with leverage and asset volatility.

- book_debt: Compustat long-term debt. E: equity market value. r_f: 3m Libor.
- The book does not define T, σ_D(DTS) or Corr_DE. Our reading: T is the issuer's market-value-weighted bond maturity. σ_D(DTS) is debt volatility estimated from duration times spread. Corr_DE is a trailing bond-equity return correlation. Label these as our reading.
- Treasury weight per issuer = issuer MV-weighted analytical duration ÷ analytical duration of the 10y OTR (PDF p. 59). T-bills take the rest.
- Build each issuer's replication, then aggregate with the four weight schemes (PDF p. 60).

**E. Factor regression (drivers).** PDF pp. 65–71, Table 1.8:

```latex
R^{BoR}_t = \alpha + \sum_k b_k F_{k,t} + e_t
```
Intuition: if VRP and low-volatility factors explain the BoR return, α shrinks toward zero.

Five nested specifications, monthly, January 1996 to December 2019:
1. Baseline: S&P 500 over r_f, 10y OTR Treasury over r_f.
2. + FF5 (SMB, HML, RMW, CMA) + momentum (MMT).
3. + Equity VRP.
4. + Bond VRP puts + Bond VRP calls.
5. + BAB.

Factor construction:
- **Equity VRP (PDF pp. 65–66, note 15, PDF p. 99).** Short a 1m-expiry ATM SPX straddle, hold to expiry, delta-hedge daily with SPX futures.

```latex
r^{opt}_t = \frac{P_t - P_{t-1} - \Delta_{t-1}\,(F_t - F_{t-1})}{S_{t-1}}
```
Intuition: the daily delta-hedged option P&L, scaled by the prior spot. The factor is the short position, so it takes the negative of this.

- **Bond VRP (PDF pp. 66–67, note 16).** Short 1m-expiry ATM puts and, separately, calls on the 10y Treasury futures, hold to expiry, delta-hedge daily with 10y futures. Same formula with the Treasury future as both hedge and denominator.
- **BAB (PDF p. 67, note 17).** Frazzini and Pedersen (2014): long low-beta stocks, short high-beta stocks, low-beta leg levered to be market neutral.

**F. Other definitions.**
- Sharpe ratio: annualised. The book does not state the risk-free rate for Chapter 1. Our reading: 3m T-bill.
- Information ratio: annualised mean ÷ annualised volatility of the BoR return.
- Autocorrelation-adjusted volatility (note 27, PDF p. 100):

```latex
\sigma_{ann} = \sigma_{monthly}\sqrt{12 + 2\cdot 11\cdot AR1}, \qquad r_t = a + AR1\, r_{t-1} + \varepsilon_t
```
Intuition: positive first-order autocorrelation raises the true annual volatility above the √12 rule.

- LCS: cost of an immediate institutional-size round trip, in percent of price, from bond-level quotes (note 24, PDF p. 100).
- Net-of-cost bond return: subtract the bond's LCS from its return when the bond leaves the portfolio (note 25, PDF p. 100). No costs on equity or Treasury legs.
- Capacity (note 19, PDF p. 100): solve `coef × x = 5% × DailyVolume / 2` for the dollar bond amount x.

### Implementation steps

1. **Map.** Link each index bond issuer to a listed equity, point in time (Ben Dor and Xu 2015 algorithm; ours must be a substitute).
2. **Filter monthly.** Drop bonds with price < $40. Drop companies with ADR, OTC or non-US equity. Drop stocks with beginning-of-month price < $1.
3. **Split** into IG and HY by index membership.
4. **Aggregate bonds to issuer.** Market-value-weighted bond total return per issuer per month (note 8).
5. **Form portfolios.** Each month, compute issuer weights under EW, Bond-VW, Equity-VW and Total-VW. Apply the same weights to bonds and equity.
6. **Estimate betas.** At each month-end t−1, run the two WLS regressions over months t−36 … t−1, half-life 9 months. Robustness: 48m and 60m windows, equal weights (note 10).
7. **Solve weights.** W_E = β_B/β_E. W_T = γ_B − W_E·γ_E. W_RF = 1 − W_E − W_T. Allow W_RF to be negative (Figure 1.4 shows weights below zero, PDF p. 39).
8. **Hold one month.** Compute R^Repl and R^BoR for month t.
9. **Test the match ex post.** Regress BoR on S&P 500 and 10y returns. Pass: both betas insignificant (Table 1.3, PDF p. 51).
10. **Report.** Average return, volatility, Sharpe or IR, worst month, maximum drawdown, correlation of bond and replication portfolios. Report by weight scheme, five-year subperiod, rating, GICS sector, liquidity bucket.
11. **Variants.** Volatility matching (C). Merton hedge ratios (D). Treasury Index in place of 10y OTR. Centred and forward 36m windows. Autocorrelation adjustment.
12. **Explain.** Run the five nested regressions in E.

Asset-allocation exercise (separate, PDF pp. 36–41):
1. Benchmarks: 20/80, 40/60, 60/40, 80/20 equity/Treasury.
2. Add x% credit, x = 0% to 100%, replacing equity and Treasuries pro rata.
3. Repeat with x% replication portfolio (Section A).
4. Plot Sharpe ratios. Split crisis months (January 2000 to December 2002, January 2008 to December 2009) from non-crisis months (PDF p. 41).

### Results

**Asset allocation (PDF pp. 36–43).**
- 60/40 benchmark Sharpe 0.71. Maximum with credit 0.86 at 69% credit (PDF p. 40).
- Optimal E/T mix in the sample was 22/78 (PDF p. 41). So the reallocation effect is positive for the 80/20 benchmark.
- Credit-specific effect is positive for every E/T mix (PDF p. 41). The benefit is large in crises and small outside them (Figure 1.7, PDF p. 43). Figure values are not legible in the text layer.

**Pre-formation sensitivities (Table 1.2, PDF p. 50), EW, trailing 36m, averaged.**

| | β S&P | % months sig. | γ 10y | % months sig. | Avg adj. R² |
|---|---|---|---|---|---|
| IG bond | 0.09 | 72% | 0.60 | 97% | 75% |
| IG equity | 0.94 | 100% | 0.00 | 12% | 86% |
| HY bond | 0.25 | 85% | 0.09 | 40% | 43% |
| HY equity | 1.28 | 100% | −0.39 | 29% | 67% |

Average replication weights (Figure 1.10, PDF p. 50): IG 9% equity, 60% Treasuries, rest T-bills. HY 19% equity, 18% Treasuries, rest T-bills.

**Post-formation check (Table 1.3, PDF p. 51).** BoR intercept (monthly, %): IG 0.15 (t = 2.54), HY 0.30 (t = 2.73). BoR betas −0.02 to −0.01, all insignificant. BoR adj. R²: IG −0.2%, HY −0.5%.

**Main performance (Table 1.4, PDF pp. 52–53), January 1993 to December 2019.**

| Univ. | Scheme | Bond ret %/yr | Bond SR | Repl ret %/yr | Repl SR | BoR ret %/yr | BoR vol | BoR IR | BoR max DD | Corr |
|---|---|---|---|---|---|---|---|---|---|---|
| IG | EW | 6.48 | 0.81 | 4.85 | 0.54 | 1.63 | 2.93 | 0.56 | −13.52 | 0.82 |
| IG | Bond-VW | 6.20 | 0.73 | 4.64 | 0.47 | 1.56 | 3.35 | 0.47 | −9.61 | 0.78 |
| IG | Equity-VW | 6.37 | 0.79 | 4.81 | 0.51 | 1.56 | 2.70 | 0.58 | −8.11 | 0.85 |
| IG | Total-VW | 6.35 | 0.78 | 4.78 | 0.51 | 1.57 | 2.79 | 0.56 | −8.10 | 0.84 |
| HY | EW | 7.99 | 0.83 | 4.56 | 0.40 | 3.43 | 5.04 | 0.68 | −17.10 | 0.68 |
| HY | Bond-VW | 7.62 | 0.79 | 5.20 | 0.51 | 2.42 | 4.65 | 0.52 | −13.52 | 0.72 |
| HY | Equity-VW | 8.03 | 1.01 | 4.68 | 0.53 | 3.34 | 3.97 | 0.84 | −8.20 | 0.70 |
| HY | Total-VW | 7.95 | 0.95 | 4.88 | 0.54 | 3.07 | 4.10 | 0.75 | −9.41 | 0.71 |

Worst BoR month: IG EW −3.11%, HY EW −6.64% (same table).

**Subperiods (Figure 1.11, PDF p. 55).** Bonds have the higher Sharpe in most five-year windows. The exception is HY 1998–2002 (PDF p. 54). The figure values are illegible in the text layer.

**By rating (Figure 1.12, PDF p. 79), EW, BoR IR.** Aaa/Aa 0.55, A 0.50, Baa 0.52, Ba 0.73, B 0.60, Caa and below 0.71 (Caa from January 2002 only).

**By GICS sector (Figure 1.13, PDF p. 80), EW, BoR IR, IG / HY.** Energy 0.19 / 0.05. Materials 0.39 / 0.71. Industrials 0.60 / 0.72. Consumer discretionary 0.41 / 0.69. Consumer staples 0.41 / 0.87. Financials 0.70 / 0.77. Other 0.35 / 0.26. The label-to-bar mapping is our reading of the chart.

**Europe (Table 1.11, PDF pp. 82–83), May 2005 to December 2019.** BoR IR: IG 0.33 to 0.46. HY 0.63 to 0.70. HY EW BoR 4.41%/yr. The text rounds to "about 0.4 for IG and 0.7 for HY" (PDF p. 84).

**Volatility matching (Table 1.5, PDF pp. 57–58).** IG fails: correlation of bond and replication is about 0.2 (0.18 to 0.26), and EW BoR is only 0.24%/yr (IR 0.04). HY works: correlation 0.57 to 0.69, BoR 2.21 to 3.08%/yr, IR 0.39 to 0.59.

**Merton hedge ratios (Tables 1.6 and 1.7, PDF pp. 61–63).**
- Mean Merton equity hedge ratio: IG 3.90%, HY 14.28%. By rating: Aaa/Aa 1.67%, A 2.80%, Baa 4.83%, Ba 8.92%, B 15.61%, Caa 26.66%. Empirical EW hedge ratio: IG 9.28%, HY 19.49%.
- BoR with Merton ratios (EW): IG 1.42%/yr, IR 0.41. HY 2.12%/yr, IR 0.37. Correlation of bond and replication: IG 0.79 vs 0.82 (OLS). HY 0.61 vs 0.68.
- Merton BoR has a negative 10y beta: IG −0.199 (sig. 1%), HY −0.428 (sig. 1%). Analytical duration overstates rate exposure.

**Cross-section (Table 1.12, PDF p. 86).** Share of issuers whose bonds beat risk-matched own equity, 1993–2019: IG 81%, HY 77% (OLS ratios). IG 84%, HY 73% (Merton). Subperiod range 55% to 93%.

**Risk underweight test (Table 1.13, PDF pp. 87–88).** Cross-sectional slope of mean BoR return on bond/replication volatility ratio: IG −0.11 (sig. 1%), HY −0.458 (sig. 1%) with OLS ratios. Negative, so higher bond risk does not explain the excess.

**Liquidity (PDF pp. 89–93).**
- S&P 500 subsample (Table 1.14): BoR 1.70 to 1.90%/yr, IR 0.49 to 0.57.
- LCS buckets (Table 1.15), EW: IG low LCS 1.45%/yr IR 0.83, high LCS 2.45%/yr IR 0.79. HY low LCS 3.86%/yr IR 1.35, high LCS 5.41%/yr IR 1.09.
- Costs (Table 1.16, January 2007 to December 2019, EW): BoR gross IG 2.02%/yr (IR 0.54), net 1.93% (IR 0.51). HY gross 4.69% (IR 0.82), net 4.18% (IR 0.73). Annualised bond cost IG 0.09%, HY 0.50%. Average LCS IG 1.02%, HY 1.56%. Average holding period IG 5.9 yr, HY 3.5 yr.

**Window position (Table 1.17, PDF p. 94), January 1993 to January 2017.** BoR %/yr (IR): IG trailing 1.60 (0.52), centred 1.88 (0.74), forward 1.72 (0.70). HY trailing 3.37 (0.64), centred 4.00 (0.93), forward 3.84 (0.93).

**Autocorrelation (Table 1.18, PDF p. 95).** IG EW bond Sharpe falls from 0.81 to 0.70. BoR IR falls from 0.56 to 0.50. Bond still beats replication. The HY page (PDF p. 96) is rotated and not checked against the image.

**Factor regression (Table 1.8, PDF pp. 69–70), intercept %/yr.**

| Spec | IG α | IG adj. R² | HY α | HY adj. R² |
|---|---|---|---|---|
| 1 Baseline | 1.806** | 0.15% | 3.495** | −0.47% |
| 2 + FF5 + MMT | 2.145*** | 5.71% | 4.153*** | 3.57% |
| 3 + Equity VRP | 1.673** | 10.66% | 3.404*** | 7.85% |
| 4 + Bond VRP | 1.12 | 16.14% | 2.557* | 12.05% |
| 5 + BAB | 0.801 | 29.02% | 2.108 | 20.76% |

- Spec 5 loadings: IG Equity VRP 0.148**, Bond VRP puts 1.368***, BAB 0.107***. HY Equity VRP 0.244**, Bond VRP puts 1.933**, BAB 0.151***. Bond VRP calls are insignificant in both.
- Stars: * 10%, ** 5%, *** 1%.
- The text (PDF p. 68) gives the baseline IG adj. R² as 0.2%. The table gives 0.15%.

**Capacity (Table 1.9, PDF p. 73), snapshot 4 May 2020.** Corporate index MV $7,323bn. SPX options notional $4,563bn, daily volume $276bn. 10y Treasury options notional $329bn, daily volume $92bn. With a 5% volume cap: $35bn of bonds per day (SPX, 0.48%) and $1bn (Treasury, 0.02%). Days to replicate: 208 and 5,273. Text on PDF p. 72 says $4,463bn for SPX open interest. The table says $4,563bn.

### Robustness and variants

What the authors vary, and what holds:
1. Weight schemes EW, Bond-VW, Equity-VW, Total-VW. Holds (Table 1.4).
2. Treasury Index in place of 10y OTR. Holds, smaller gap (Table 1.10, PDF pp. 76–78, rotated, values not read).
3. Window 36m, 48m, 60m. Equal weights or other half-lives. Holds (note 10).
4. Centred and forward windows. Holds, gap grows (Table 1.17).
5. Volatility matching. Holds in HY. Fails as a risk match in IG (Table 1.5).
6. Merton hedge ratios. Holds, weaker IR (Table 1.7).
7. Price filter off. No material change (note 7).
8. Ratings, sectors, subperiods, Europe. Holds (Appendix 1.2).
9. Liquidity: S&P 500 subsample, LCS buckets, LCS costs. Holds (Appendix 1.3).
10. Autocorrelation adjustment. Holds (Table 1.18).

### Limits and caveats

- **Proprietary inputs.** Bloomberg Barclays index returns, membership and OAS. Ben Dor and Xu bond-equity mapping. LCS. We have none of them.
- **Gross of cost** except Table 1.16, which charges bonds only. The factor legs (VRP, BAB) carry no costs.
- **HY coverage.** HY final-sample coverage is 47% to 72% of index MV (Table 1.1). Private HY issuers are out. The result covers listed HY issuers only.
- **In-sample hedge ratios** are trailing, but Table 1.17 shows forward windows do better. Look-ahead in the forward variant is deliberate and not tradable.
- **Inconsistencies in the book.** SPX open interest $4,463bn (text) vs $4,563bn (table). Coverage "97% and 81%" refers to the mapped row. Table 1.15 note says returns run from January 2010 but analysis starts 2007.
- **Not a signal.** The chapter documents a premium of bonds over equity. It does not rank bonds within credit. Its use for us is risk decomposition and a sanity check, not alpha.
- **Undefined Merton inputs.** T, σ_D(DTS) and Corr_DE have no definition in note 13.

### Implementation in this repo

What the book says vs what we decide.

- **Maps to.** Section 7.4 (spread per unit of risk) and Section 7.7 (risk premium test). Module `hy/fairspread.py` for the Merton hedge ratio. Module `hy/backtest.py` for the bond-over-replication test. Module `hy/peers.py` for issuer-equity mapping.
- **Data we have.** TRACE monthly bond prices and G-spreads. CRSP equity returns and market cap. Compustat point-in-time long-term debt. Treasury yields in `hy/sources/treasury.py`.
- **Data we lack.**
  1. Index membership and index returns. Proxy: our HY universe from `trace_panel`.
  2. Amount outstanding in the panel. Proxy: Mergent FISD offering amount, or equal weights (EW is the book's main scheme).
  3. The Ben Dor and Xu mapping. Proxy: our CUSIP-6 to CRSP PERMNO link in `trace_panel`, with `link_ambiguous` cases dropped.
  4. OptionMetrics, AQR BAB. Proxy: AQR publishes BAB returns. Skip VRP regressions until we license option data.
  5. LCS. Proxy: `bid_ask_pts` from the TRACE panel as a round-trip cost.
- **Return definition.** Bond monthly total return from TRACE month-end clean price plus accrued plus coupon. The 10y Treasury return from the CRSP or Treasury constant-maturity yield via duration approximation.
- **Lag rule.**
  - Bond and equity returns for month t carry `as_of` = last trading day of t and `available_at` = first business day of t+1.
  - Hedge weights for month t use returns with `available_at` ≤ month-end t−1.
  - Compustat debt for the Merton ratio uses the record with `available_at` ≤ month-end t−1 (the filing date, not `datadate`).
  - CRSP market cap uses the month-end t−1 value.
- **Use for HY.** The HY result (BoR IR 0.52 to 0.84) supports keeping credit as a separate asset. The BoR series per issuer gives a feature for S4 (capital structure relative value): issuers whose bonds lag their risk-matched equity.
- **Falsifiable test.**
  - Signal: monthly EW HY bond-over-replication return, sensitivity-matched as in steps 5–8, on our TRACE-CRSP universe.
  - Horizon: one month, 2005 to latest.
  - Metric: annualised IR of BoR, and post-formation betas to S&P 500 and 10y.
  - Pass: IR ≥ 0.4, and both post-formation betas with |t| < 2. Fail if IR < 0.2.
  - Second test, cross-section: share of issuers with mean BoR > 0. Pass ≥ 65% (book: 77% HY, Table 1.12).

### Part Two framing (PDF pp. 101–106), context for Chapters 2 to 9

The book says:
- June 1989 to December 2019, the Bloomberg Barclays US IG Corporate Index had average excess return 73bp/yr and average OAS 132bp. Only 56% of the promised spread was realised (PDF p. 101, citing Ng and Phelps 2011).
- Forced sale of fallen angels at index exit is a main cause. Holding them 12 to 24 months recovers part of the loss (PDF p. 102).
- A "downgrade tolerant" benchmark keeps downgraded bonds for a set time (PDF p. 103).
- Index bonds exit when remaining maturity falls under one year (PDF p. 102). New bonds enter at the month-end after issue (PDF p. 104).

---

## Chapter 2. Fallen Angels: Characteristics, Performance, and Implications for Investors (PDF pp. 109–154)

Page range note. The chapter runs PDF pp. 109–154 (book pp. 81–126). PDF pp. 155–156 are the start of Chapter 3. Part Two framing (PDF pp. 101–106) is in `ch01.md`.

**Question.** Do forced sales at the IG-to-HY boundary push fallen angel prices below fair value, and can a rules-based buyer earn the reversal?

**Answer.** Yes. Market-value-weighted fallen angels lose 15.09% against HY peers from month −12 through the downgrade month, then recover 6.63% over the next 24 months (Table 2.4, PDF p. 121). A "3-Month Reversal" portfolio beats its peer group by 0.78%/month, IR 1.03, from January 1991 to June 2010 (Table 2.9, PDF p. 142). Changes in the cash-CDS basis and in liquidity-adjusted turnover explain the cross-section (Table 2.5, PDF pp. 131–132).

### Data

The book says:
- **Event sample (PDF p. 112).** All bonds in the Bloomberg Barclays US Corporate Index with a rating event between January 1990 and December 2009.
  - Downgrade event: index exit on a downgrade from any IG rating to HY.
  - Upgrade event (control group): index entry on an upgrade from any HY rating to IG.
  - Final sample: 761 issuers, 2,251 bonds. 1,485 downgraded, 766 upgraded.
- **Exclusion.** Drop a rating event that occurs less than 36 months after an earlier rating event of the same bond (note 2, PDF p. 151).
- **Analysis window (PDF pp. 112–113).** Month −12 to month +24 around the rating-event month (month 0). A defaulted bond exits at the month-end after the default month. That price is its final value (PDF p. 113). Last sample month is June 2010 (note 7, PDF p. 152).
- **Ratings.** The index rating rule, which changed over time (note 20, PDF p. 153):
  1. Before October 2003: Moody's, or S&P if no Moody's.
  2. October 2003 to July 2005: the lower of Moody's and S&P.
  3. From July 2005: the middle of Moody's, S&P and Fitch.
- **Peer groups (PDF p. 113).** Universe: bonds in the Corporate or High Yield index with no rating event in the previous 24 months. Cells:
  - Industry: financials, industrials, utilities (3).
  - Quality: A and higher, Baa, Ba, B, Caa and lower (5).
  - Maturity: ≤ 10 years and > 10 years, except for Caa and lower (no split).
  - Total 3 × (4 × 2 + 1) = 27 cells.
  - A relative statistic is missing when the cell has fewer than 20 bonds.
- **Liquidity (PDF pp. 113–114).** Monthly, from January 2007. TRACE trades by CUSIP. LCS (Barclays Liquidity Cost Score, Konstantinovsky, Ng and Phelps 2016).
- **TRACE cleaning (note 6, PDF p. 152).** TRACE caps reported size at $1mn (HY) and $5mn (IG). The authors impute caps of $4mn (HY) and $12.5mn (IG) so that trades sum to TRACE aggregate volume. They drop trades below $100,000.
- **CDS (PDF p. 114).** Markit, from January 2004. Drop months with ten or more consecutive unchanged daily quotes (note 18, PDF p. 153).
- **Strategy period (PDF pp. 135, 141).** Portfolios start January 1991 with cash. Performance runs January 1991 to June 2010. Cash earns 1m Libor (PDF p. 136).

Table 2.1 (PDF pp. 115–116), downgrades by year: market value as a share of the HY Index peaks at 28.8% (2002), 15.4% (2005, Ford and GM), 14.2% (1991), 13.7% (2001). Downgrade counts track the Corporate Index OAS. Upgrades stay at or below 3.0% of the Corporate Index.

### Definitions and formulas

**Relative return (flow measure).** Match the bond to its peer cell at the start of each month, by industry, quality and remaining maturity at that time (PDF p. 113). Aggregate to issuer with bond market-value weights (PDF p. 113).

Cumulative relative return from window start to month T, aggregated over issuers (note 11, PDF p. 152):

```latex
R^{T}_{j} = \prod_{t=-12}^{T}\Big(1 + \sum_i w_{i,t}\,\big(R_{i,t} - R^{P}_{i,t}\big)\Big) - 1, \qquad j \in \{D, U\}
```
Intuition: compound the cross-issuer average of monthly issuer-minus-peer returns. w is the issuer weight (equal or market value).

Issuer cumulative relative return from month 0 (note 13, PDF pp. 152–153):

```latex
R^{T}_{i} = \prod_{0 \le t \le T}\big(1 + R_{i,t}\big) - \prod_{0 \le t \le T}\big(1 + R^{P}_{i,t}\big)
```
Intuition: issuer compounded return minus peer compounded return. R^P is the weighted return of the peer cells of the issuer's bonds.

- If an issuer leaves the window early (all bonds matured, called or defaulted), set its return equal to its peer return for the remaining months (PDF p. 123).
- Quarter 0 is the rating-event month. Quarter 1 is months 1–3 (note 10, PDF p. 152).
- t-statistics adjust for serial and cross-sectional correlation (Table 2.4 note). The book gives no method. Our reading: Newey-West on the monthly cross-sectional mean series.

**Relative spread (point-in-time measure).** The book gives no formula. Our reading:

```latex
RS_{b,t} = OAS_{b,t} - \overline{OAS}_{\,P(b),t}
```
Intuition: the bond's spread over the average spread of its peer cell.

- The peer cell P(b) is **static**. Set it once from the bond's characteristics right after the rating event. Hold it through the window (PDF p. 113). This avoids a jump at month 0 when the rating cell changes (note 4).
- Figure 2.1 plots the median issuer beginning-of-month relative spread (note 12).

**Turnover and liquidity (Figure 2.5 note, PDF p. 128; note 15).**

```latex
Turnover_{i,t} = \frac{\sum_{b \in i} Volume_{b,t}}{\sum_{b \in i} AmtOut_{b,t}}, \qquad RelTurnover_{i,t} = Turnover_{i,t} - Turnover_{P(i),t}
```
Intuition: the monthly share of the issuer's debt that traded, above the peer share.

```latex
LCS_{i,t} = \sum_{b \in i} \frac{MV_{b,t}}{MV_{i,t}}\,LCS_{b,t}, \qquad RelLCS_{i,t} = LCS_{i,t} - LCS_{P(i),t}
```
Intuition: issuer round-trip cost, in percent of price, above its peers.

**Cash-CDS basis (PDF p. 114; Figure 2.6 note, PDF p. 129).**

```latex
Basis_{i,t} = LiborOAS_{i,t} - CDS^{blend}_{i,t}
```
Intuition: bond spread to Libor minus a CDS spread of matched risk. A forced bond sale widens it because CDS holders face no forced sale.

- CDS^blend is a weighted mix of the issuer's 5y and 10y CDS with RPV01 equal to the issuer's spread duration.
- The book gives no weight formula. Our reading: pick weight a on 5y so that a·RPV01_5y + (1−a)·RPV01_10y = issuer spread duration.

**Regression variables (Table 2.5 note, PDF p. 132).**
- `HY at Downgrade`: 1 if the issuer carried an IG rating from all three agencies at the rating event, else 0. The label conflicts with the definition. The text (PDF p. 130) says 74% of issuers satisfy it.
- `Rating Change Size`: 1 if the downgrade in month 0 exceeds two notches, else 0.
- `Lagged 1-mth Relative Return`.
- `Change in Cash-CDS Basis`: basis at end of current month minus end of previous month.
- `Change in Rel. LCS × Rel. Turnover`: product of the monthly change in relative LCS and relative turnover.
- `Size`: natural log of the issuer market value at the end of the downgrade month.
- `End of Month 3 Cash-CDS Basis`: basis level at end of month 3.
- `ΣRelative LCS × Turnover`: sum over months 0–3 of the monthly product of relative LCS and turnover.

Panel A model (contemporaneous). One row per issuer-month in months 0–3:

```latex
r^{rel}_{i,t} = a + b_1\,HYatDG_i + b_2\,RCS_i + b_3\,r^{rel}_{i,t-1} + c_1\,\Delta Basis_{i,t} + c_2\,\Delta Basis_{i,t-1} + c_3\,(\Delta RelLCS \times RelTurn)_{i,t} + c_4\,\ln Size_i + e_{i,t}
```
Intuition: forced selling shows as basis widening and costly volume in the same month.

Panel B model (predictive). One row per issuer:

```latex
\bar r^{rel}_{i,[4,15]} = a + b\,\bar r^{rel}_{i,[0,3]} + c_1\,Basis_{i,3} + c_2\,\textstyle\sum_{t=0}^{3} (RelLCS \times Turn)_{i,t} + c_3\,\ln Size_i + e_i
```
Intuition: the larger the price pressure at month 3, the larger the 12-month rebound.

Units: returns and basis in percent. A 1% basis widening gives −1.63%/month (Panel A) and +0.15%/month ahead (Panel B) (PDF pp. 133–134).

**Portfolio statistics (Table 2.9 note, PDF p. 144).**
- Sharpe ratio uses 1m Libor.
- IR = mean ÷ standard deviation of monthly relative return. The table annualises it. Check: 0.78/2.62 × √12 = 1.03 (Table 2.10, PDF p. 148).
- Turnover = sum of absolute weight changes of all bonds, before vs after the monthly rebalance (Table 2.7 note, PDF p. 139).

**Net of cost (PDF pp. 147–149).** The printed formula reads "Portfolio Monthly Return − 2 × LCS × Turnover". The text and the worked number use one half:

```latex
R^{net} = R^{gross} - \tfrac{1}{2}\,LCS \times Turnover
```
Intuition: LCS is a round trip. Turnover counts buys and sells. So each unit of turnover pays half a round trip.

Worked: 146bp − 0.5 × 450bp × 19% = 103.25bp/month, about 12.39%/yr (PDF p. 149). We read "2×" on PDF p. 147 as a typo for "½ ×".

### Implementation steps

**Event study.**
1. Build monthly bond panel: total return, OAS, rating (index rule), industry, remaining maturity, market value.
2. Flag rating events: IG→HY index exits and HY→IG entries. Drop events within 36 months of an earlier event.
3. Each month, fill the 27 peer cells from bonds with no rating event in the last 24 months.
4. For each event bond, track months −12 to +24. Exit on default at month-end after default.
5. Compute monthly bond relative return against the dynamic peer cell. Require ≥ 20 bonds in the cell.
6. Aggregate to issuer with bond market-value weights.
7. Average across issuers per event-relative month, equal and MV weighted. Group by quarter. Compound per note 11.
8. Compute static-peer relative spreads. Plot medians for downgrades, upgrades, and the Baa3→Ba1 subset (Baa3 all year before, Ba1 to window end, PDF p. 122).
9. Form 20 buckets on mean relative return in months 0–3. Track months 4–9, 10–15, 16–21 (Figure 2.4, PDF p. 126).
10. Run Table 2.5 regressions.

**Strategies (Table 2.6, PDF p. 136; PDF pp. 135–138).** Common rules:
1. Rebalance at each month-end. No leverage. Start January 1991 with cash.
2. One bond per issuer: the largest by market value in the ≤ 10y bucket. If none, the largest in the > 10y bucket (note 24, PDF p. 153).
3. Weight each held bond `w = min(10%, 1/N)`. Cash = 1 − N·w, earns 1m Libor. Example: 8 bonds at 10% and 20% cash. Then 11 bonds at 9.09% each (PDF pp. 136–137).
4. Sell at month-end on a technical trigger (matured, called, defaulted in the month) or at month 24 after the rating event. The month-end price is the exit value (PDF p. 136).

Portfolio rules:

| Rule | Buy All | 3-Month Reversal | Flexible Reversal |
|---|---|---|---|
| Buy month | end of month 0 | end of month 3 | any of months 1–6 |
| Min. relative spread | none | > 40bp | > 40bp |
| Min. price | none | none | > $40 per $100 |
| Spread tightened vs prior month | no | no | yes |
| Not held before | n/a | n/a | yes (note 25) |
| Extra sell trigger | none | relative spread < 0 | relative spread < 0 |

- Table 2.6 prints "> 40bps". The text (PDF p. 137) says "at least 40bp". Use ≥ 40bp in a variant.
- Held bonds may fall below $40 in Flexible Reversal (PDF p. 138).

**Benchmarks (notes 27–28, PDF p. 154).**
1. Peer Group: equal-weighted return of the peer cells matched to every held fallen angel. If a cell has < 20 bonds, use the HY Index return. Cash has relative return zero.
2. Modified Peer Group: match each fallen angel to the largest bond in its quality, industry and maturity cell not yet matched to another fallen angel. Equal weight across matched bonds.

**Statistics.** Monthly mean, volatility, annualised Sharpe or IR, worst month, worst 3 months, 5th percentile. Split 1991–2000 and 2001–June 2010. Rolling 6-month relative return vs HY Index return. Net of cost per the formula above.

### Results

**Rating transitions (Table 2.2, PDF p. 117).** Of 1,485 downgrades, 1,055 (71.0%) start at Baa3. 626 of those go one notch to Ba1. 59.3% of all downgrades end at Ba1. Of 755 rated upgrades, 538 (71.3%) start at Ba1. 441 of those go to Baa3.

**Status 24 months after (Table 2.3, PDF p. 118), downgrades.**

| Event years | Bonds | HY | IG | Matured | Defaulted | Called |
|---|---|---|---|---|---|---|
| 1990–1994 | 173 | 69.9% | 9.8% | 7.5% | 2.9% | 9.8% |
| 1995–1999 | 211 | 71.6% | 15.2% | 8.5% | 0.5% | 2.8% |
| 2000–2004 | 678 | 66.2% | 9.3% | 5.9% | 15.5% | 2.1% |
| 2004–2009 | 404 | 80.4% | 5.0% | 6.7% | 6.4% | 1.5% |

The last row label "2004–2009" overlaps the row above. The book prints it so. 2001 had a 25% default rate (20% by market value) (PDF p. 118).

**Event study (Table 2.4, PDF p. 121), downgraded issuers, MV weighted.**

| Quarter | Avg rel. ret bp/month | t | Cum. rel. ret |
|---|---|---|---|
| −4 | −23.6 | −1.82 | −0.69% |
| −3 | −71.3 | −4.10** | −2.79% |
| −2 | −103.6 | −4.31** | −5.78% |
| −1 | −247.6 | −6.91** | −12.66% |
| 0 | −277.6 | −5.86** | −15.09% |
| 1 | −8.8 | −0.18 | −15.29% |
| 2 | 12.1 | 0.46 | −15.01% |
| 3 | 15.7 | 0.70 | −14.61% |
| 4 | 69.0 | 3.26** | −12.82% |
| 5 | 65.5 | 3.53** | −11.12% |
| 6 | 35.2 | 1.81 | −10.18% |
| 7 | 11.5 | 0.63 | −9.87% |
| 8 | 7.5 | 0.50 | −9.67% |

- Recovery from end of Q1 to end of Q8: (1 − 0.0967)/(1 − 0.1529) − 1 = 6.63% (PDF p. 119).
- Equal weighted: Q0 −345.7bp (t −5.71), cumulative −2.82% at window end. No Q4–Q5 reversal (PDF p. 120).
- Upgraded issuers: Q0 +89.3bp (t 8.68), cumulative +5.66% at Q0, +4.26% at window end. No reversal (PDF pp. 120–121).
- Stars: * 5%, ** 1% (Table 2.4 note).

**Relative spreads (Figure 2.1, PDF pp. 122–123).** Downgraded issuers widen about 130bp before the event (−112bp to 19.5bp). The Baa3→Ba1 subset widens −45bp to 83bp. All downgrades reach 78bp right after month 0, then converge to zero. Upgrades go from 78bp to 13bp by month 0.

**Dispersion (Figures 2.2 and 2.3, PDF pp. 124–125).**
- Top quartile ends +15.5%. Bottom quartile minimum −7.1% at month 7. 25th percentile −3.7% at month 0, −2.3% at month 24.
- 46.1% of issuers hit their minimum cumulative relative return in month 0 to month 3. 10.6% hit it in quarter 8.

**Reversal by formation bucket (Figure 2.4, PDF p. 126).** Worst bucket: −8.66% average monthly relative return in months 0–3. Then 5.75%, 1.04%, 0.86% in months 4–9, 10–15, 16–21. Only the bottom four buckets rebound strongly.

**Volume and liquidity (Figure 2.5, PDF pp. 127–128), 84 issuers downgraded January 2007 to December 2009.** Turnover rises from 5.1% to just over 18% in month 0. It returns to start level within four months. Relative LCS goes from −96bp (month −4) to +88bp (month 0), then converges over two years.

**Basis (Figure 2.6, PDF p. 129), 65 issuers from January 2004.** Median basis about 40bp before, above 100bp at month 0, about 225bp at month 3, back near the pre-event level later.

**Cross-sectional regressions (Table 2.5, PDF pp. 131–132).**

Panel A (contemporaneous):

| Variable | Model I | Model II | Model III |
|---|---|---|---|
| Intercept | −1.23 (t −1.32) | −1.52 (−1.30) | 2.95 (0.57) |
| HY at Downgrade | −0.39 (−0.43) | 0.43 (0.41) | |
| Rating Change Size | −1.00 (−0.82) | −0.99 (−0.55) | |
| Lagged 1m rel. ret | 0.07 (1.31) | 0.06 (0.93) | |
| ΔBasis | | −1.63 (−5.80) | −1.68 (−6.33) |
| Lag ΔBasis | | −0.31 (−1.29) | |
| ΔRelLCS × RelTurn | | | −0.13 (−6.08) |
| Size | | | −0.38 (−0.52) |
| N | 411 | 246 | 173 |
| Adj. R² | 0.013 | 0.144 | 0.298 |

Panel B (predictive, months 4–15):

| Variable | Model I | Model II | Model III |
|---|---|---|---|
| Intercept | 0.74 (3.96) | 0.21 (1.66) | 0.18 (0.11) |
| Avg rel. ret months 0–3 | −0.09 (−2.61) | −0.01 (−0.56) | −0.10 (−2.76) |
| Basis end month 3 | | 0.15 (2.69) | |
| ΣRelLCS × Turn | | | 0.004 (2.05) |
| Size | | | 0.11 (0.47) |
| N | 64 | 58 | 55 |
| Adj. R² | 0.085 | 0.089 | 0.152 |

Two conflicts in the book:
1. The text (PDF p. 134) says past return has no power once price-pressure proxies enter. Panel B Model III shows −0.10 with t −2.76 (p 0.01). Only Model II supports the text.
2. The introduction (PDF p. 111) says the two measures explain about 40% of the cross-section. Panel A Model III gives 0.298, and the text on PDF p. 133 says 30%.

**Portfolio composition (Tables 2.7 and 2.8, PDF pp. 139–140).**

| | Buy All | 3-Month Reversal | Flexible Reversal |
|---|---|---|---|
| Mean bonds | 47.1 | 11.7 | 13.4 |
| Mean holding (months) | 21.7 | 9.7 | 9.8 |
| Mean monthly turnover | 15.2% | 19.0% | 19.4% |
| Mean cash | 1.6% | 30.8% | 26.0% |
| Sales at 24 months | 79.5% | 17.6% | 17.4% |
| Sales on negative rel. spread | 0% | 74.5% | 75.7% |
| Sales on default | 9.3% | 4.9% | 4.3% |

Cash averages 54% in the 3-Month Reversal portfolio in 1991–2000 (PDF p. 146). It averages 3.1% (3-Month) and 1.6% (Flexible) in 2001–2010 (PDF p. 140). All three overweight financials by about 40% in 2008–2009 (PDF p. 140).

**Performance (Table 2.9, PDF pp. 142–144), January 1991 to June 2010, monthly.**

| Portfolio | Avg ret | Vol | Sharpe | Rel. peer avg | Rel. peer IR | Rel. mod. peer avg | Rel. mod. peer IR | Rel. mod. worst 3m |
|---|---|---|---|---|---|---|---|---|
| Buy All | 1.04% | 2.77% | 0.87 | 0.31% | 0.64 | 0.24% | 0.48 | −7.56% |
| 3-Month Reversal | 1.46% | 3.83% | 1.01 | 0.78% | 1.03 | 0.72% | 0.93 | −8.90% |
| Flexible Reversal | 1.21% | 3.54% | 0.85 | 0.53% | 0.81 | 0.45% | 0.66 | −11.05% |

- Peer Group: avg 0.73%, 0.67%, 0.68%. Modified Peer Group avg 0.80%, 0.74%, 0.76%.
- 3-Month Reversal by period, over Peer Group: 1991–2000 0.40%/month, IR 0.80. 2001–June 2010 1.19%/month, IR 1.25.
- 3-Month Reversal relative to modified peer: skew 0.72, kurtosis 4.38, 63% positive months (PDF p. 145).
- Rolling 6m relative return has correlation 0.22 with the HY Index return (PDF p. 146).

**Parameter sensitivity (Table 2.10, PDF p. 148), 3-Month Reversal over Peer Group.**

| Variant | Avg/month | Vol | IR | Worst 3m |
|---|---|---|---|---|
| Original (month 3, 10% cap, 40bp) | 0.78% | 2.62% | 1.03 | −9.29% |
| Buy month 1 | 0.64% | 2.52% | 0.87 | −14.00% |
| Buy month 2 | 0.67% | 2.72% | 0.85 | −11.12% |
| Buy month 4 | 0.75% | 3.02% | 0.86 | −11.67% |
| Buy month 5 | 0.66% | 3.11% | 0.73 | −11.53% |
| 5% position cap | 0.64% | 2.10% | 1.07 | −7.67% |
| Min. rel. spread 20bp | 0.70% | 2.59% | 0.93 | −10.55% |
| Min. price $40 | 0.61% | 2.05% | 1.03 | −9.29% |

The text (PDF p. 147) says the 5% cap gives "higher performance and lower risk". The table shows lower mean (0.64% vs 0.78%) and higher IR (1.07 vs 1.03).

**Net of cost (PDF pp. 147–149).** Fallen angel LCS just after downgrade is 50–60bp above HY peers, about 4–5% absolute. Net 3-Month Reversal: 72.7bp/month relative, 103.25bp/month total (about 12.39%/yr), IR 0.94 after costs.

### Robustness and variants

What the authors vary, and what holds:
1. Equal vs market-value issuer weights in the event study. The reversal is a large-issuer effect. Equal weights show no Q4–Q5 reversal (PDF p. 120).
2. Upgrades as control. No reversal. Supports forced selling over overreaction (PDF p. 122).
3. Baa3→Ba1 subset with little news. Same spread path as all downgrades (PDF p. 123).
4. Buy month 1 to 5, cap 5%, spread threshold 20bp, price floor $40. Month 3 is best. IR stays 0.73 to 1.07 (Table 2.10).
5. Two subperiods. Positive in both. Stronger in 2001–2010 (Table 2.9 Panel B).
6. Alternative peer group definitions. Similar results, not shown (PDF p. 146).
7. Net of LCS cost. IR 0.94 (PDF p. 149).

### Limits and caveats

- **Proprietary inputs.** Index membership and index rating rule, Barclays OAS, LCS, Markit CDS. We have none of them.
- **Gross of cost** in all tables. The net estimate uses averages, not a bond-level cost series. The LCS level comes from the 2007–2009 crisis sample only.
- **Equal weights with a 10% cap** are not a realistic book. Turnover 19%/month is high (PDF p. 140). Chapter 3 treats capacity.
- **Small regression samples.** N = 55 to 411. CDS from 2004, LCS from 2007.
- **Supply cycles.** The opportunity set is near empty in the 1990s (cash 54%). Returns cluster in 2001–2003 and 2008–2009.
- **Same-month execution.** The book buys at the month-end price of the signal month. No execution lag.
- **Book inconsistencies.** "2×" vs "½×" cost formula. "40%" vs "30%" explained variance. Panel B Model III past-return coefficient vs text. "> 40bp" vs "at least 40bp". 5% cap text vs table. Table 2.3 row "2004–2009".
- **IG-origin only.** The evidence covers bonds that start in the IG index. It says nothing about HY-to-lower-HY downgrades.

### Implementation in this repo

What the book says vs what we decide.

- **Maps to.** Section 8 signal S6 (rating migration and forced flows). Event definition in `hy/events.py`. Peer cells in `hy/peers.py` and `hy/groups.py`. Signal in `hy/signals.py`. Strategy test in `hy/backtest.py` and `hy/walkforward.py`. Section 9 event risk for the pre-downgrade drift (Table 2.4 quarters −4 to 0).
- **Data we have.**
  1. TRACE monthly panel: price, G-spread, `par_volume`, `n_trades`, `bid_ask_pts`.
  2. TRACE trade cleaning already caps 1MM+ and 5MM+ at the floor (`hy/sources/trace_bonds.py`). The book imputes $4mn and $12.5mn instead.
  3. Compustat point in time and CRSP for issuer size.
- **Data we lack and proxies.**
  1. Rating history. Proxy: Mergent FISD rating actions via WRDS, middle of three agencies (post-2005 index rule). Without it, S6 cannot run.
  2. Index membership. Proxy: IG/HY from the composite rating. Add a bond to the universe only if it has ≥ 1 year to maturity.
  3. OAS. Proxy: G-spread. Relative spread = bond G-spread minus the mean G-spread of its static peer cell.
  4. Amount outstanding (not in the panel). Proxy: FISD offering amount less known redemptions. Turnover = `par_volume` ÷ that amount.
  5. LCS. Proxy: `bid_ask_pts` ÷ price as round-trip cost. Relative LCS = issuer minus peer-cell mean.
  6. CDS. None. Drop the basis variables. Test only the LCS × turnover proxy.
  7. Peer cells. 3 industries is too coarse for HY. Keep the book's 27 cells for replication. Test our sector groups as a variant.
- **Lag rule.**
  - A rating action carries `as_of` = the agency action date and `available_at` = the next business day. The FISD load date is a stricter bound when it is later.
  - Month 0 is the month in which the composite rating crosses from IG to HY on an `available_at` basis.
  - Prices and G-spreads for month t carry `as_of` = last trade date in t and `available_at` = first business day of t+1.
  - Trade rule: we form the signal from data with `available_at` ≤ month-end t. We enter at the first available price in t+1. This is one step stricter than the book. Also report the book's month-end execution as a variant.
  - Peer-cell membership excludes bonds with any rating event with `available_at` in the past 24 months.
- **Falsifiable tests.**
  1. Event study. Signal: IG→HY composite downgrade. Horizon: months 4–24. Metric: MV-weighted cumulative relative return vs dynamic peer cell, sample 2005 to latest. Pass: > 0 with t ≥ 2 (book: +6.63%, Table 2.4).
  2. Strategy. Signal: 3-Month Reversal rules, relative G-spread ≥ 40bp at end of month 3, sell on negative relative spread or month 24. Horizon: monthly rebalance. Metric: annualised IR of monthly return over the peer-cell benchmark, net of ½ × bid-ask × turnover. Pass: net IR ≥ 0.5 and mean > 0 with t ≥ 2. Fail if net IR < 0.25 (book net IR 0.94, PDF p. 149).
  3. Price pressure. Signal: Σ(relative cost × turnover) over months 0–3. Horizon: mean relative return months 4–15. Metric: cross-sectional slope. Pass: slope > 0 with t ≥ 2 (book: 0.004, t 2.05, Table 2.5 Panel B).

---

## Chapter 3. Fallen Angels: Capacity, Transaction Costs, and the Bond-CDS Basis (PDF pp. 155–190)

Note on pages. The chapter opens on PDF p. 155, not p. 157. Pages 155–156 hold the introduction and the recap of the Chapter 2 rules. PDF p. 190 is blank. Endnotes are on PDF pp. 187–189.

**Question.** Does the fallen angel reversal survive time, Europe, capacity limits, bid-ask costs, and a CDS hedge?

**Answer.** Yes. The 24-month outperformance over peers holds in every five-year block since 1990 and in Europe (PDF pp. 158, 161). The strategy keeps a Sharpe ratio near 0.9–1.0 at $2bn and near 0.65 after costs (PDF pp. 168–171). A bond-minus-CDS basis trade on fallen angels gives a gross Sharpe ratio up to 3.30 and a net Sharpe ratio up to 1.74 (PDF p. 181).

### Data

**What the book says.**
- Universe for the cash strategies: the Chapter 2 sample. That is every bond in the Bloomberg Barclays US Corporate Index that left the index on a downgrade from IG to HY, 1990 onward (Chapter 2, PDF p. 112). Back-test period January 1991 to December 2011 (Table 3.6, PDF p. 169).
- Peer groups (from Chapter 2, PDF p. 113): 3 industries (financials, industrials, utilities) × 5 quality classes (A and higher, Baa, Ba, B, Caa and lower). Each class except Caa-and-lower splits into maturity ≤10y and >10y. Total 27 peer groups. Peers come from the Corporate or High Yield index, monthly, and exclude any bond with a rating event in the previous 24 months. A relative statistic is missing when its peer group has fewer than 20 bonds.
- Flow statistics (returns, turnover) use the peer group at the start of each month. Point-in-time statistics (spreads, costs) use a static peer group fixed just after the rating event (PDF p. 113).
- Defaulted bonds exit at the month-end after the default month at that price (Chapter 2, PDF p. 113, repeated PDF p. 162).
- Europe: Euro fallen angels 2000–2011, Bloomberg Barclays Euro Corporate and Euro HY indices (Tables 3.2–3.3, PDF pp. 159–160).
- Mean-reversion control universe: every bond in the Bloomberg Barclays HY Index with no IG rating in the previous 24 months (note 7, PDF p. 188).
- Default table: issuers in the HY Index 1990–2011. "Other HY" means an issuer in the HY Index that was never downgraded from IG (note 10, PDF p. 188). Issuers that defaulted straight from IG (for example Lehman 2008) are not in the table (note 11).
- Capacity: issuer-level data. All bonds of an issuer aggregate by market value (note 12, PDF p. 188). Chapter 2 used one bond per issuer.
- Transaction costs: Barclays Liquidity Cost Score (LCS), the round-trip cost of an institution-size trade as % of price, from trader quotes, CUSIP level, from January 2007 (PDF p. 169). Source: one broker-dealer (PDF p. 170).
- Basis sample: issuers downgraded to HY 2004–2010 with actively traded CDS (PDF pp. 171–172). Exclude downgrades from a corporate event (acquired or merged), because the CDS contract changes. CDS spreads and DV01 monthly, from 12 months before the downgrade to 24 months after (3-year window). Source Markit, Barclays trader quotes as backup. Drop a spread series once it is unchanged for over three months. Drop a CDS with less than one year of data in the window or less than six months in the first year after the downgrade (PDF p. 172). Final sample 101 issuer pairs (Table 3.8, PDF p. 172). 91 pairs have returns (10 lack DV01, Table 3.13 note, PDF p. 182).
- CDS contract: no-restructuring (XR). Modified restructuring (MR) where MR was much more common (note 18, PDF p. 188).
- Spreads cap at the 95th percentile (20%) (Table 3.9 note, PDF p. 173).
- Equity check (Figure 3.6, PDF p. 186): Compustat. Equity peers are one-digit SIC groups.

### Definitions and formulas

**Relative spread (Chapter 2).** Bond OAS minus the average OAS of its static peer group. The book gives no formula in Chapter 3. Our reading: `RS_{b,t} = OAS_{b,t} - mean_{j∈peer(b)} OAS_{j,t}`.

**Cumulative relative return of downgraded issuers (note 2, PDF p. 187).**
```latex
R^{D}_{T} = \prod_{t=-12}^{T}\Big(1 + \sum_{i\in D} w_{i,t}\,(R_{i,t} - R^{P}_{i,t})\Big) - 1
```
Intuition: average the issuer-minus-peer return each month across events, then compound from month −12.
`w_{i,t}` is the issuer weight in month t, `R_{i,t}` the issuer total return, `R^P_{i,t}` the market-value-weighted return of the peer groups of the issuer's bonds. Table 3.3 weights issuers by market value each quarter (PDF p. 160 note).

**Information ratio (Table 3.1 note, PDF p. 158).** Mean of the monthly cross-event average relative return over months 1–24 divided by the volatility of that monthly series. The book does not say if it is annualised. Our reading: not annualised (values 0.36–0.50).

**High and Low Supply years, Europe (PDF p. 159).** High Supply if Euro fallen angel market value exceeds 30% of the Euro HY Index market value that year (2002, 2005, 2009). Other years are Low Supply.

**Capacity-constrained issuer weight, equation (1) (PDF p. 167).**
```latex
W_i = \min\!\Big(\tfrac{1}{N},\; 10\%,\; \tfrac{Cap \times MV_i}{\text{Port.size}}\Big)
```
Intuition: equal weight, capped at 10% per issuer, and capped at a fixed share of the issuer's market value.
- `N`: number of eligible issuers. `10%`: the Chapter 2 issuer limit. `Cap`: 5% of issuer market value (base case). `MV_i`: market value of all issuer bonds. `Port.size`: fixed dollar size, $125mn to $2bn, held constant over time (note 13).
- Cash = `1 − Σ W_i`. Cash earns one-month Libor (Chapter 2, PDF p. 136).
- Only `Cap / Port.size` matters. $500mn with Cap 5% equals $250mn with Cap 2.5% (PDF p. 167).
- Worked example (PDF p. 167): $500mn, 12 issuers, 1/N = 8.33% = $41.67mn. The cap binds below MV $833.33mn. An issuer with MV $500mn gets $25mn, and cash is 3.33%.

**Net return after costs (note 15, PDF p. 188).**
```latex
R^{net}_{t} = \sum_i w_{i,t} R_{i,t} \;-\; \sum_i LCS_{i,t-1}\,\max(w_{i,t} - w_{i,t-1},\, 0)
```
Intuition: pay the half-plus spread (full LCS) only on purchases. Prices are bid marks, so sales cost nothing extra.
`LCS_{i,t-1}` is the bond bid-ask cost at the end of month t−1. Buys mark at ask = bid + LCS (PDF p. 170). The book applies the full LCS to the buy weight. Note: the book calls LCS "bid-ask" here, but LCS is a round-trip cost. We follow the formula as printed.

**Cash-CDS basis (PDF p. 173).**
```latex
B_{i,t} = S^{CDS,5y}_{i,t} - \sum_{b\in i} \tfrac{MV_b}{\sum MV} \, OAS^{Libor}_{b,t}
```
Intuition: CDS spread minus the issuer's MV-weighted Libor-OAS over all unsecured bonds. Negative basis means bonds are cheap against CDS.
All unsecured bonds under the same CDS aggregate monthly by market value (note 16).

**Market-adjusted basis, equation (2) (PDF p. 174).**
```latex
B^{adj}_{i,t} = \big(S^{CDS,5y}_{i,t} - OAS^{MVW}_{i,t}\big) - \big(S^{CDX.NA.HY,\,5y,\,on\text{-}the\text{-}run}_{t} - OAS^{HY\,Index}_{t}\big)
```
Intuition: remove the market-wide basis to keep the issuer-specific part.
The systematic term stays HY (CDX.NA.HY vs HY Index) through the downgrade month to avoid a jump (note 22, PDF p. 189).

**Alternative basis specifications (note 19, PDF p. 188).** (a) Two bonds that straddle 5y, weighted so the maturity equals the CDS maturity. If two are not available, use the bond nearest 5y. (b) The widest-spread bond each month (a proxy for cheapest-to-deliver). Both gave similar results (PDF p. 173).

**Significant negative basis (PDF p. 175).** `B^adj` at the end of the downgrade month below −120bp. 36 of 101 issuers. This is the top third by magnitude.

**Basis trade total return (Table 3.14 note, PDF p. 184).**
```latex
TR = \text{Bond price return} + (\text{Bond carry} - \text{CDS premium}) \times \text{fraction of year held}
```
Intuition: price gain on the bond leg plus coupon carry minus the protection cost.
On default, the protection buyer receives par. The book gives no explicit DV01-based CDS mark-to-market formula. It says returns need DV01 (10 pairs drop for missing DV01, PDF p. 182). Our reading: CDS leg P&L each month ≈ −ΔS^CDS × DV01 (protection buyer gains when CDS widens), plus the premium accrual.

**Basis trade transaction cost (note 24, PDF p. 189).** Bid-ask from LCS. CDS LCS = 25% of the bond LCS. Fill missing LCS with the contemporaneous sample median. Before 2007, impute LCS as the 2007 sample median × (year spread / 2007 spread). Pay ask on entry, receive bid on exit (PDF p. 178).

### Implementation steps

**A. Cash strategies (Buy All and Three-Month Reversal), from Chapter 2 with Chapter 3 changes.**
1. Each month-end, flag bonds that left the US Corporate Index on a downgrade to HY. Month 0 is the downgrade month.
2. Build 27 peer groups from index bonds with no rating event in the prior 24 months. Require ≥20 bonds, else missing (PDF p. 113). Note 27 of Chapter 2 (PDF p. 154): if a peer group has <20 bonds, use the HY Index return.
3. Compute each bond's relative spread to its static peer group.
4. Buy rules:
   - Buy All: buy at the end of month 0.
   - Three-Month Reversal: buy at the end of month 3 if relative spread ≥ 40bp (PDF p. 156).
5. Sell rules: default, call or maturity (technical), month 24, or (Reversal only) relative spread < 0.
6. Chapter 3 capacity version: hold all bonds of each issuer at MV weights (note 12). Weight issuers by equation (1). Cap = 5% of issuer MV. Run Port.size ∈ {$125mn, $250mn, $500mn, $1bn, $2bn}, constant over time.
7. Rebalance monthly to the equation (1) weights. Cash earns one-month Libor.
8. Returns are total returns at bid prices. For net returns (Feb 2007–Dec 2011), apply the note-15 formula with LCS at t−1.
9. Report average monthly return, monthly std, annualised Sharpe ratio, worst month, 5th percentile, worst 3 months. Report average turnover, average LCS, and the correlation of turnover with HY LCS.

**B. Mean-reversion control (PDF p. 162).**
1. Universe: HY Index bonds with no IG rating in the prior 24 months.
2. Rebalance monthly. Buy any bond with relative spread to peers ≥ 40bp.
3. Sell when relative spread < 0 or 21 months after purchase (21 = 24 − 3, note 8).
4. Weight EW or MV. Variant "EW with matching cash": hold each month the same cash share as the Three-Month Reversal portfolio.

**C. Bond-CDS basis trades (PDF pp. 177–178).**
1. Sample: 2004–2010 fallen angels with liquid CDS, cleaned as in Data.
2. Long leg: MV-weighted aggregate of all the issuer's outstanding bonds. Short leg: buy 5y CDS protection on the issuer. Our reading: size the CDS by DV01 to match the bond leg, because the book requires DV01 for returns.
3. No dynamic portfolio. Each issuer trade is a separate event. Aggregate across trades by event time.
4. Four variants (Table 3.12, PDF p. 179):
   - Buy All: enter end of month 0. Exit at month 24 or on a technical trigger (default, or all bonds called or matured).
   - Sell Tight: as Buy All, plus exit when `B^adj > 0`.
   - Sell Tight, Buy Wide: enter at month 0 only if `B^adj < −120bp`. Exit when `B^adj > 0`, a technical trigger, or month 24. The entry filter is not rechecked after entry.
   - Sell Tight, Buy Wide Month 3: as above, but enter at end of month 3.
5. Stop-loss variant (Panel D): exit at once when the trade's cumulative loss exceeds 5%, regardless of other rules (PDF p. 183).
6. Costs: pay ask on entry, receive bid on exit, with LCS as in note 24.
7. Statistics:
   - Panel B: an MV-weighted time series of pairs aligned on months since trade entry, to month 24. Report average return, volatility, avg/vol, Sharpe ratio, skewness, max drawdown, net Sharpe ratio, and transaction cost.
   - Panel C: statistics across all pair-months: % pairs positive, mean, vol, median, skewness, 5th percentile.

### Results

**Stability, US (Table 3.1, PDF p. 158).** Cumulative return over peers after downgrade:

| Downgrade years | # bonds | 1y | 2y | IR, 2y |
|---|---|---|---|---|
| 1990–1994 | 173 | 3.03% | 7.88% | 0.36 |
| 1995–1999 | 211 | −0.52% | 5.46% | 0.42 |
| 2000–2005 | 771 | 4.16% | 8.77% | 0.50 |
| 2006–2011 | 372 | 7.06% | 9.25% | 0.49 |

**Europe (Table 3.3, PDF p. 160; text PDF p. 161).**
- Full sample: cumulative relative return −18.54% from month −12 to month 0. Month 0 alone averages −516bp (t = −4.85). From the downgrade to month 24 the issuers gain 6.93% over peers, against 6.63% for the US in Chapter 2. The post-downgrade quarterly t-stats are not significant.
- High Supply years: −22.61% before the downgrade, +10.24% after. Low Supply years: −14.44% before, +2.48% after.
- Bolognesi et al. (2014): −5% in the event month and +0.81% next quarter. This book: −5.16% and +0.78%.

**Euro supply (Table 3.2, PDF p. 159).** Euro fallen angels reached 77.7% of the Euro HY Index MV in 2002, 30.7% in 2005 and 32.5% in 2009. The US share peaked at 28.8% in 2002 and stayed ≤15.4% in other years.

**Mean reversion is fallen-angel specific (Table 3.4, PDF pp. 163–164).** January 1991–December 2011:

| | HY Index | MR VW | MR EW | MR EW, matching cash | 3M Reversal |
|---|---|---|---|---|---|
| Avg monthly return | 0.82% | 0.88% | 1.14% | 0.80% | 1.41% |
| Monthly std | 2.66% | 3.73% | 3.93% | 3.48% | 3.71% |
| Sharpe (ann.) | 0.66 | 0.53 | 0.72 | 0.48 | 1.02 |
| Worst month | −15.91% | −16.42% | −19.35% | −19.35% | −10.76% |
| Worst 3 months | −29.82% | −34.62% | −34.96% | −34.96% | −26.01% |

Subperiod averages (MR EW matching cash vs 3M Reversal): 1991–2000 0.44% vs 0.92%. 2001–2011 1.11% vs 1.86% (PDF pp. 163–164). The 1991–2000 Sharpe ratio of MR EW matching cash is 0.03, against 0.89 for 3M Reversal (PDF p. 163). Chapter 2 relative figures: 3M Reversal 0.78%/month over peers, IR 1.03. Buy All 0.31%/month, IR 0.64. One-Month Reversal 0.64%, IR 0.87 (PDF pp. 161–162).

**Defaults (Table 3.5, PDF p. 165).** 1990–2011:
- Fallen angels: 94 defaulted issuers of 616 (15%). By amount, $119,438mn of $980,401mn (12%).
- Other HY: 943 of 3,870 issuers (24%). By amount, $323,668mn of $2,053,583mn (16%).
- The text says "88 of 614" (PDF p. 166). The table says 94 of 616. Flag: the text and the table disagree.

**Capacity (Table 3.6, PDF p. 169; Cap 5%).**

| | $125mn | $250mn | $500mn | $1bn | $2bn |
|---|---|---|---|---|---|
| Buy All avg monthly | 1.04% | 1.01% | 0.96% | 0.88% | 0.77% |
| Buy All Sharpe | 0.92 | 0.90 | 0.88 | 0.88 | 0.88 |
| Buy All worst 3m | −25.20% | −25.06% | −24.95% | −23.02% | −18.28% |
| 3M Rev avg monthly | 1.37% | 1.24% | 1.03% | 0.81% | 0.63% |
| 3M Rev std | 3.17% | 2.85% | 2.27% | 1.68% | 1.13% |
| 3M Rev Sharpe | 1.14 | 1.12 | 1.08 | 1.02 | 0.95 |
| 3M Rev worst 3m | −17.63% | −16.81% | −14.14% | −10.80% | −7.09% |

HY Index Sharpe 0.65 (PDF p. 168). At $1bn in August 2004, the 3M Reversal portfolio held only 53% in fallen angels. Buy All held 98% (PDF p. 168).

**Costs (Table 3.7, PDF p. 171; February 2007–December 2011).**

| | Buy All gross | Buy All net | 3M Rev gross | 3M Rev net | HY gross | HY net |
|---|---|---|---|---|---|---|
| Avg monthly | 1.28% | 0.91% | 1.80% | 1.21% | 0.69% | 0.66% |
| Std | 4.53% | 4.29% | 5.79% | 5.49% | 4.14% | 4.13% |
| Sharpe | 0.86 | 0.61 | 0.98 | 0.66 | 0.45 | 0.43 |

Average turnover is 18.0% for Buy All and 23.6% for 3M Reversal. Average LCS is 2.67%, 3.30% and 2.64% (HY). The turnover-to-HY-LCS correlation is 0.13 for Buy All and 0.61 for 3M Reversal. The cost drag is 37bp/month (Buy All) and 59bp/month (3M Reversal) (PDF p. 170). The HY Index costs come from Dastidar and Phelps (2011).

**Basis distribution (Table 3.10, PDF p. 174).** Market-adjusted basis at the end of the downgrade month, mean by year:

| Year | 2004 | 2005 | 2006 | 2007 | 2008 | 2009 | 2010 |
|---|---|---|---|---|---|---|---|
| Mean basis (bp) | −46 | −27 | −24 | −79 | 50 | −544 | −353 |

The 2008 positive mean comes from secured airline debt (PDF p. 174). Figure 3.3 (PDF p. 175): for the significant-negative group, the median and mean basis go from about −130 and −220bp to −380 and −520bp in the six months before the downgrade. They revert over the next two years. 17 of the 36 significant-negative issuers are financials (Table 3.11, PDF p. 177). Most of the 36 were downgraded in 2009 (Figure 3.4).

**Basis strategies (Table 3.13, PDF pp. 181–182).**

| | Buy All | Sell Tight | ST, Buy Wide | ST, BW Month 3 |
|---|---|---|---|---|
| Initial pairs | 91 | 91 | 33 | 32 |
| Early sells | 0 | 50 | 11 | 8 |
| Avg holding (months) | 24 | 14 | 18 | 17 |
| Avg monthly return | 0.5% | 0.8% | 1.8% | 1.4% |
| Monthly vol | 1.0% | 1.1% | 2.6% | 1.4% |
| Sharpe (ann.) | 1.05 | 2.04 | 2.38 | 3.30 |
| Max drawdown | 1.8% | 1.6% | 2.3% | 0.5% |
| Net Sharpe (ann.) | 0.26 | 0.97 | 1.30 | 1.74 |
| Transaction cost | 4.9% | 4.9% | 10.1% | 5.7% |
| % pairs positive | 85% | 85% | 93% | 93% |
| Pair 5th pct | −6.9% | −4.1% | −5.0% | −5.1% |
| Stop-loss exits (5%) | 30 | 16 | 7 | 6 |
| Sharpe with stop | 0.74 | 1.45 | 2.31 | 2.68 |
| Net Sharpe with stop | 0.05 | 0.63 | 1.23 | 1.53 |

- Over 60% of the Buy All two-year return accrues in the first eight months (PDF p. 180).
- Part of the Buy Wide gain comes from low 2009 financing rates (PDF p. 182).
- Delphi example (Table 3.14, PDF p. 184): entry at the downgrade (Dec-04) loses 17.5% total as a bond-only trade. The basis trade gains 4.2%. Entry three months later: bond-only −8.7%, basis +14.8%.

**Equity (Figure 3.6, PDF p. 186).** Fallen angel equities show no reversal over peers. The bonds do revert. The figure gives no table values.

### Robustness and variants

- Time blocks: all four 5-year blocks positive at 2 years (Table 3.1).
- Market: Europe shows the same pattern. The reversal is stronger in High Supply years (Table 3.3).
- Control: generic HY mean reversion with the same rules does not match the result (Table 3.4).
- Capacity: Sharpe ratio decays slowly up to $2bn (Table 3.6).
- Costs: positive net of LCS (Table 3.7).
- Basis definition: the two alternative bond aggregates give similar results (PDF p. 173, note 19).
- Absolute vs market-adjusted basis: the market adjustment is mostly a level shift. It does not create the reversal (note 23, PDF p. 189).
- Stop-loss at 5%: the Buy Wide variants keep most of their Sharpe ratio. Buy All does not (Panel D).
- Turnover: the results do not change with individual monthly turnover (Chapter 2 note 31, PDF p. 154).

### Limits and caveats

- All data are Barclays-proprietary: index membership, index OAS, LCS, trader CDS quotes. We cannot get them.
- LCS exists only from 2007. Pre-2007 basis-trade costs are imputed (note 24).
- The book says LCS likely overstates costs: one dealer, a crisis period, and EW monthly rebalance turnover (PDF p. 170).
- The basis sample is small (91 pairs, 33 and 32 in the Buy Wide variants) and concentrated in 2009 financials. The Sharpe ratios of 2–3 rest on few independent events.
- Basis-trade statistics aggregate trades in event time, not calendar time. They ignore cash management and supply variation (PDF p. 178).
- Cash results are total returns, not excess over Treasuries. Sharpe ratios use Libor cash. The book does not DTS-match.
- Capacity uses a fixed MV cap, not a price-impact model (PDF p. 167).
- The default count disagrees between text (88 of 614) and Table 3.5 (94 of 616).
- The rating method changes in the index: Moody's (or S&P) before Oct 2003, the lower of Moody's and S&P to July 2005, the middle of three after (Chapter 2 note 20, PDF p. 153).

### Implementation in this repo

**Module and section.** Signal S6 (rating migration and forced flows), methodology Section 8, in `hy/signals.py` (`s6_migration`, `flow_weight`). Peer groups map to `hy/peers.py` (`rating_class`, `maturity_bucket`, `sector_at`). Back-test rules map to `hy/backtest.py` and Section 11. The S1 residual is the "relative spread" analogue, Sections 7.3–7.5.

**What we have.** TRACE prices and G-spreads (`hy/sources/trace_panel.py`). Ratings with dates via `peers.rating_at`. Compustat point-in-time. CRSP equity for the Figure 3.6 check.

**What we lack and the proxy.**
- No index membership. Proxy: a fallen angel is a bond whose composite rating (middle of available agencies) crosses from BBB− to BB+ or lower. Month 0 is the month of that rating action.
- No OAS. Proxy: G-spread. Relative spread = bond G-spread minus the median G-spread of its peer cell (rating class × sector × maturity bucket ≤10y / >10y). Require ≥20 bonds per cell, else fall back to the rating-class median.
- No amount outstanding in the panel. Proxy: equal weight within an issuer, or FISD amount outstanding if we add it. Drop the capacity test (equation 1) until we have it.
- No LCS. Proxy: TRACE effective bid-ask from paired dealer buys and sells in the month. Charge it on purchases only, per note 15.
- No CDS. Skip the basis strategy (part C). Note it as a gap in Section 9.4 (hedges).

**Lag rule (as_of, available_at).**
- A rating action has `as_of` = action date. `available_at` = the next business day after the action is public.
- The signal is formed at month-end t from fields with `available_at ≤ t`.
- Trades fill at month-end t prices. Returns start in month t+1.
- G-spread uses the last TRACE trade at or before t. `as_of` = trade date. `available_at` = trade date + TRACE dissemination lag (we use 1 business day).
- Peer cells use ratings with `available_at ≤ t`.
- The static peer cell is fixed at the first month-end after the downgrade.

**Falsifiable test.**
- Signal: Three-Month Reversal on HY fallen angels. Buy at the end of month 3 if the G-spread relative to peers is ≥40bp. Sell when it turns negative, at month 24, or on default.
- Horizon: monthly returns, held to exit.
- Metric 1: the average monthly return over the rating-matched peer cell, in excess of the duration-matched Treasury, net of the TRACE bid-ask charge.
- Metric 2: the same rule applied to non-fallen-angel HY bonds (the Table 3.4 control) with matched cash.
- Pass:
  - the net relative return is > 0 with t > 2 over 2005–2024;
  - it is positive in at least three of the four cycles (2008, 2015, 2020, 2022);
  - it beats the control by > 30bp/month.

  The book's gross relative figure is 0.78%/month (PDF p. 161).

---

## Chapter 4. Introducing the Fallen Angel Reversal Scorecard (PDF pp. 191–218)

Note on pages. The chapter text runs PDF pp. 191–216. PDF p. 217 is the part divider "New Issuance: Index Inclusion". PDF p. 218 is blank. The notes are on PDF pp. 215–216.

**Question.** Can a monthly bond-level score rank fallen angels by next-month spread reversal better than the relative spread alone?

**Answer.** Yes. The FAR score combines the reversal stage (from price path and turnover) with stage-specific sensitivities to the relative spread per remaining month. From July 2010 to December 2019, its top-minus-bottom half earns 5.67%/yr over peers with IR 0.65 and max drawdown −9.42%. Relative OAS alone gives 3.88%/yr, IR 0.40 and drawdown −26.12% (Table 4.6, PDF p. 209). A HY Index portfolio with a FAR-weighted fallen angel overweight beats the index with IR 1.31 and 0.98 in two subperiods (Table 4.8, PDF p. 213).

### Data

**What the book says.**
- Universe: fallen angels (bonds downgraded out of the Bloomberg Barclays US Corporate Index into HY) with a **positive** relative spread right after the downgrade. Each bond stays in while its relative spread stays positive, up to 24 months after the downgrade (PDF p. 193, Table 4.5 p. 206).
- Period: January 2007–December 2019 for the turnover analysis, because TRACE volume starts in 2007 (PDF p. 193). The stage statistics (Figure 4.1, Table 4.1) use January 1991–December 2019 (PDF pp. 196, 198). The sensitivity regressions (Table 4.4) use July 2005–December 2019 (PDF p. 205). FAR score estimates start June 2010. The back-tests run July 2010–December 2019 (PDF pp. 207–208).
- Peer group: all index bonds with the same credit rating and the same level-3 industry (Barclays classification) as the fallen angel. Peer spreads and returns are market-value weighted (note 1 p. 215, Table 4.6 note p. 209). The book does not say if "same rating" means notch or letter class.
- Volume: TRACE monthly trading volume. Amount outstanding comes from the index (PDF p. 201, note 4 p. 216).
- Returns: total return of the fallen angel minus the MV-weighted total return of its peer group (Table 4.6 note).

### Definitions and formulas

**Relative spread (note 1, PDF p. 215).**
```latex
RelOAS_{b,t} = OAS_{b,t} - \sum_{j\in peer(b)} \tfrac{MV_{j,t}}{\sum MV}\,OAS_{j,t}
```
Intuition: how far the bond sits above the spread of same-rating, same-industry index bonds.
The book says "spread over the average spread". We read "over" as a difference, because the cut-offs are in bp (Chapter 2 uses 40bp).

**Relative OAS per remaining month (PDF p. 203).**
```latex
RelOAS/m_{b,t} = \frac{RelOAS_{b,t}}{24 - k_{b,t} + 1}
```
Intuition: the monthly tightening needed to close the gap by month 24 at a uniform pace.
`k_{b,t}` is the number of months since the downgrade. The downgrade month is k = 0.

**Ex post inflection month (PDF p. 195).** The month in [0, 24] after the downgrade with the highest RelOAS. Months before it form the widening stage. Months after it form the tightening stage. Both exclude the inflection month.

**Pre-Reversal indicator, real time (PDF p. 197).**
```latex
PreRev_{b,t} = \mathbf{1}\big[RelOAS_{b,t} = \max_{0\le s\le t} RelOAS_{b,s}\big]
```
Intuition: the spread is at its running maximum since the downgrade, so the bond is still widening or at the peak.

**Turnover and relative turnover (note 4, PDF p. 216).**
```latex
TO_{b,t} = \frac{Volume_{b,t}}{AmtOut_{b,t}}, \quad RelTO_{b,t} = TO_{b,t} - \sum_{j\in peer(b)} \tfrac{MV_{j,t}}{\sum MV}\,TO_{j,t}
```
Intuition: trading activity above the peer level marks the forced-selling flow.
Conflict: note 4 subtracts the peer turnover. The notes to Table 4.3 and Figure 4.3 say "over the value-weighted turnover", which can read as a ratio. We follow note 4 (difference), because it is explicit. The peer group for turnover is rating × industry (Table 4.3 note).

**Change in relative turnover (Table 4.3 note, PDF p. 201).**
```latex
\Delta RelTO_{b,t} = RelTO_{b,t} - RelTO_{b,t-1}
```
Intuition: a jump in relative turnover marks the last wave of selling, which comes with the peak.

**Turnover groups.** Large change if `ΔRelTO ≥ 5%`. Small change if `ΔRelTO < 5%`. The 5% sits between the median (4%) and the mean (6%) of ΔRelTO in inflection months. Results hold for 4–6% cut-offs and for trailing median or mean cut-offs (PDF p. 200).

**Inflection probability, real time (PDF p. 201).** Each month, take the trailing five-year window, restricted to months with PreRev = 1. For each turnover group, `P_infl(group) = (# inflection months) / (# months)`. Apply it to bonds in that group next month.

Note 5 (PDF p. 216) gives the real-time inflection label inside the estimation window:
- Drop fallen angels with fewer than 6 months of post-downgrade data at the window end.
- Redefine the inflection month as the month of highest RelOAS from the downgrade to the earlier of month 24 or the window end.

**Stage regression (Table 4.4, PDF p. 205).**
```latex
\Delta RelOAS_{b,t+1} = \alpha
 + \beta_T\, RelOAS/m_{b,t}(1-PreRev_{b,t})
 + \beta_I\, RelOAS/m_{b,t}\,PreRev_{b,t}\,Infl_{b,t}
 + \beta_W\, RelOAS/m_{b,t}\,PreRev_{b,t}(1-Infl_{b,t})
 \;[+\;\gamma\,PreRev_{b,t}] + \varepsilon
```
Intuition: the next-month spread move is a stage-dependent multiple of the uniform-pace baseline.
`Infl` is the ex post inflection dummy. Model 2 adds `γ PreRev`. For live scores, fit on a trailing five-year window with data available at t (PDF p. 204). The book does not state the estimator. Our reading: pooled OLS across bond-months, no fixed effects.

**Raw score and FAR score (Table 4.5, PDF p. 206).**
```latex
Raw_{b,t} =
\begin{cases}
-\beta_T\,RelOAS/m_{b,t} & PreRev_{b,t}=0\\[2pt]
P_{infl}\,(-\beta_I)\,RelOAS/m_{b,t} + (1-P_{infl})\,(-\beta_W)\,RelOAS/m_{b,t} & PreRev_{b,t}=1
\end{cases}
```
Intuition: the expected next-month tightening. Its sign is flipped so that a higher value means a higher expected return.
```latex
FAR_{b,t} = 100 \times \text{PercentileRank}_t(Raw_{b,t}) \in [0,100]
```
Intuition: a cross-sectional percentile among all bonds in the FAR universe that month.

### Implementation steps

1. **Flag fallen angels.** Mark each bond that leaves the IG index on a downgrade to HY. Set k = 0 in the downgrade month.
2. **Peers.** Each month, build peer cells from index bonds with the same rating and level-3 industry. Compute MV-weighted peer OAS, peer total return, and peer turnover.
3. **Inputs per bond-month.** Compute RelOAS, RelOAS/m, PreRev, TO, RelTO and ΔRelTO.
4. **Universe filter.** Keep the bond from k = 0 if RelOAS > 0 at the downgrade. Keep it while RelOAS > 0 and k ≤ 24. Once RelOAS ≤ 0, the bond leaves.
5. **Training labels.** At each month-end t, take the trailing five-year window of fallen angel bond-months. Drop bonds with fewer than 6 months of post-downgrade data. Label the inflection month as the argmax of RelOAS over [0, min(24, window end)] (note 5).
6. **Inflection probability.** In the PreRev = 1 subsample, compute the inflection share for ΔRelTO < 5% and for ΔRelTO ≥ 5%.
7. **Sensitivities.** Regress ΔRelOAS_{t+1} on the three interaction terms (Table 4.4 baseline). Keep β_T, β_I and β_W.
8. **Score.** For each live bond at t, compute Raw from the Table 4.5 formula. Choose P_infl from its ΔRelTO group. Rank by percentile into FAR on 0–100.
9. **Test A, top vs bottom halves (PDF p. 207).**
   - Each month, split the FAR universe at the median FAR: top half long, bottom half short.
   - Equal-weight the bonds, with a 10% cap per bond. If a side has fewer than 10 bonds, put the unused weight in 1m Libor. Libor earns zero relative to peers (note 6).
   - Rebalance monthly. Measure each bond's return as its total return minus its peer return.
   - Repeat the test with RelOAS and RelOAS/m as the sort variable.
   - Report the annual average, annual volatility, IR (annualised), worst month, and max drawdown.
10. **Test B, FA-tilted HY portfolio (PDF p. 211).**
    - Each month, pick the bond with the highest FAR score for each fallen angel issuer.
    - Give the top issuer a 3% overweight. Give each other issuer `3% × FAR_i / max FAR`.
    - Put the rest of the portfolio in the Bloomberg Barclays US HY Index.
    - Controls:
      - Peer-tilted: the same overweights on the industry-and-rating-matched peer bonds.
      - FA-EW-tilted: the same total overweight, equal across fallen angel issuers, MV-weighted across each issuer's bonds.
    - Report the average total return, volatility and Sharpe ratio. Report the differences against the index and against FA-EW.

### Results

**Stage statistics (Table 4.1, PDF p. 198; 1991–2019).**

| Real-time | Ex post stage | Share of obs. | Median next-month ΔRelOAS |
|---|---|---|---|
| PreRev = 1 (27%), median −14bp | Inflection | 8% | −122bp |
| PreRev = 1 | Widening, spread rising | 20% | +9bp |
| PreRev = 0 (73%), median −6bp | Widening, temporary decline | 22% | +16bp |
| PreRev = 0 | Tightening | 51% | −17bp |

- In the text, the median next-month move after a widening month is +13bp (PDF p. 195). The next move after an inflection month is −122bp, about 7 times the −17bp of a typical tightening month.
- Of the PreRev = 0 months, 70% are true tightening months (PDF p. 197).

**Turnover at inflection (Table 4.2, PDF p. 200; 2007–2019).**
- Regression of ΔRelTO on the inflection dummy, whole sample: intercept 0.33%, dummy 6.20%***.
- PreRev = 1 subsample: intercept 3.44%***, dummy 2.43%**.

**Inflection probability by turnover group (Table 4.3, PDF p. 201).**

| | Whole sample: obs. | Whole sample: P(infl) | PreRev = 1: obs. | PreRev = 1: P(infl) |
|---|---|---|---|---|
| ΔRelTO < 5% | 3,457 | 5% | 744 | 24% |
| ΔRelTO ≥ 5% | 1,349 | 12% | 523 | 32% |

In the rolling estimates, the large-change group has the higher probability in every month (Figure 4.3, PDF p. 202). The figure gives no values.

**Sensitivities (Table 4.4, PDF p. 205; July 2005–December 2019).**

| Term | Baseline | Model 2 |
|---|---|---|
| Intercept | −0.05 | −0.01 |
| β_T (tightening) | −0.82** | −0.85** |
| β_I (inflection) | −4.26*** | −4.23*** |
| β_W (widening) | 1.86*** | 1.91*** |
| PreRev | — | −0.17 (n.s.) |
| Adj. R² | 23.42% | 23.45% |

**Sorts, returns over peers (Table 4.6, PDF p. 209).** Top-minus-bottom half:

| Period | Sort | Avg %/yr | Vol %/yr | IR | Worst month % | Max DD % |
|---|---|---|---|---|---|---|
| Jul 2010–Dec 2019 | Rel OAS | 3.88 | 9.68 | 0.40 | −9.29 | −26.12 |
| | Rel OAS/m | 4.69 | 9.25 | 0.51 | −9.03 | −23.90 |
| | FAR | 5.67 | 8.75 | 0.65 | −6.54 | −9.42 |
| Jul 2010–Dec 2014 | Rel OAS | 2.67 | 5.42 | 0.49 | −5.36 | −8.69 |
| | Rel OAS/m | 5.07 | 5.73 | 0.89 | −5.73 | −7.84 |
| | FAR | 4.38 | 4.55 | 0.96 | −2.38 | −4.45 |
| Jan 2015–Dec 2019 | Rel OAS | 4.97 | 12.37 | 0.40 | −9.29 | −24.96 |
| | Rel OAS/m | 4.34 | 11.59 | 0.37 | −9.03 | −23.90 |
| | FAR | 6.83 | 11.30 | 0.60 | −6.54 | −9.42 |

Single sides, full sample:
- FAR top: 8.95%/yr, IR 0.85, max DD −12.72%. FAR bottom: 3.28%/yr, IR 0.46, max DD −15.03%.
- Rel OAS top: 8.05%/yr, IR 0.68, max DD −23.41%. Rel OAS bottom: 4.17%/yr, IR 0.75, max DD −4.92%.
- The FAR bottom half is still positive over peers in every subperiod (PDF p. 210).

**FA-tilted HY portfolio (Table 4.8, PDF p. 213).**

| | FA-tilted | Peer-tilted | HY Index | FA − Index | Peer − Index | FA-EW-tilted | FAR − EW |
|---|---|---|---|---|---|---|---|
| Sub 1, Jul 2010–Dec 2014: ret %/yr | 9.91 | 8.96 | 8.84 | 1.07 | 0.12 | 9.64 | 0.27 |
| vol %/yr | 6.38 | 6.09 | 6.15 | 0.82 | 0.29 | 6.36 | 0.41 |
| Sharpe or IR | 1.52 | 1.44 | 1.40 | 1.31 | 0.41 | 1.48 | 0.67 |
| Sub 2, Jan 2015–Dec 2019: ret %/yr | 11.43 | 6.60 | 6.11 | 5.32 | 0.50 | 9.61 | 1.81 |
| vol %/yr | 9.47 | 5.54 | 5.29 | 5.45 | 0.72 | 8.38 | 1.92 |
| Sharpe or IR | 1.08 | 0.98 | 0.93 | 0.98 | 0.68 | 1.00 | 0.94 |

The fallen angel overweight averages 23% (min 5%, Q1 18%, median 22%, Q3 29%, max 50%) (Table 4.7, PDF p. 211).

### Robustness and variants

- The ΔRelTO cut-off of 4–6%, or a trailing mean or median, gives similar results (PDF p. 200).
- Model 2 with a PreRev level term changes nothing (Table 4.4).
- FAR beats both simpler sorts in both subperiods on IR, volatility and drawdown (Table 4.6). One exception: in 2010–2014, RelOAS/m has the higher top-minus-bottom return (5.07 vs 4.38) but the lower IR.
- A peer-tilted control rules out a plain risk-loading story (Table 4.8).
- The tilt size can scale. The book says the IR stays the same in sign and magnitude when the 3% top weight changes (PDF p. 211). The book shows no table for this claim.
- Trailing five-year windows, not expanding ones, because reversal speed changed over time. Reversals were faster in 2015–2018 (PDF pp. 206–207).

### Limits and caveats

- Short live sample: July 2010–December 2019 (about 114 months). Few fallen angels per month (Figure 4.5). The IR values have wide error bands. The book reports no t-stats for Table 4.6.
- All returns are before transaction costs. Chapter 3 shows that fallen angel bid-ask costs are large (3.30% average LCS for the reversal strategy).
- Returns are total returns over peer total returns, not excess over Treasuries, and not DTS-matched. The peer match on rating and industry does not match duration.
- The relative turnover definition is ambiguous (difference in note 4, "over" in the Table 4.3 note).
- For June 2010–November 2011, fewer than 5 years of TRACE data exist for P_infl (PDF p. 207).
- The data are Barclays-proprietary: index membership, index OAS, level-3 industry.
- The 1991–2019 stage statistics (Table 4.1) include the pre-TRACE period. Only the turnover parts are 2007+.

### Implementation in this repo

**Module and section.** Signal S6 (rating migration and forced flows), methodology Section 8, `hy/signals.py`. The stage logic is a residual-dynamics model, so it also maps to Section 7.5 (residual dynamics and expected convergence; `s1_horizon`, `half_life`). Peer cells go in `hy/peers.py`. The rolling fits go in `hy/walkforward.py`. The sort tests go in `hy/backtest.py`, Section 11.

**What we have.** TRACE trades give monthly volume and G-spreads (`hy/sources/trace_panel.py`, `trace_bonds.py`). Ratings with dates come from `peers.rating_at`. Sector comes from `peers.sector_at` (GICS).

**What we lack and the proxy.**
- No index membership. Proxy: a composite rating crossing from BBB− to BB+ or lower defines the fallen angel.
- No OAS. Proxy: G-spread. RelOAS = G-spread minus the median G-spread of its rating-class × GICS-sector cell (≥20 bonds, else sector-free). We use the median because we have no MV weights.
- No amount outstanding in the panel. Turnover needs it. Proxies, in order:
  - FISD offering amount net of known calls, if we add it;
  - otherwise, volume relative to the bond's own trailing 12-month average volume, minus the same for its peer cell.

  Label the proxy in the decision page.
- No level-3 industry. Use the GICS industry group.

**Lag rule (as_of, available_at).**
- Ratings: `available_at` = public action date + 1 business day.
- TRACE volume for month t: `as_of` = month-end t. `available_at` = month-end t + 1 business day (dissemination lag). The score at t uses volume through t.
- G-spread at t: the last trade at or before t.
- β and P_infl fit only on bond-months whose next-month ΔRelOAS is known by t. That means the window ends at t−1 for the dependent variable.
- Inflection labels use the note-5 truncation at the window end. This rule prevents look-ahead.
- Trade at month-end t. Return over month t+1.

**Falsifiable test.**
- Signal: our FAR score on HY fallen angels, built as above with G-spreads and proxy turnover.
- Horizon: one month.
- Metric: the monthly top-half-minus-bottom-half return over peers, in excess of the duration-matched Treasury, after a TRACE bid-ask charge on turnover. Also the rank IC of FAR against next-month ΔRelOAS (negative is good).
- Pass:
  - the net top-minus-bottom return is > 0 with IR > 0.4 over 2010–2024;
  - FAR beats a RelOAS-only sort on IR by ≥ 0.1;
  - the rank IC is < 0 with t < −2.
- Fail: FAR does not beat the RelOAS-only sort. Then drop the stage machinery and keep the simple relative-spread rule from Chapter 3.

---

## Chapter 5. Issuance Dynamics and Performance of Corporate Bonds (PDF pp. 219–242)

**Question.** Does heavy net debt issuance predict lower subsequent credit excess returns, at the market, sector and issuer level?

**Answer.** Yes, at all three levels, in USD IG plus HY, August 1994–July 2014.
- Market: the lowest quartile of 6-month net issuance is followed by +3.04% 6-month excess return. The highest quartile is followed by −1.67% (Figure 5.2, PDF p. 223).
- Sectors: dynamic sector weights cost the market-weighted index 14bp/yr, IR −0.60 (Table 5.3, PDF p. 227).
- Issuers: moderate issuers beat aggressive issuers by 5.9bp/month, IR 0.34 (Figure 5.6, PDF p. 229). The gap survives a DTS control and an accounting-based definition.

### Data

**What the book says.**
- Universe: the "US Corporate All Ratings" composite, built from the Bloomberg Barclays US Corporate, US 144A and US High Yield indices (PDF p. 220). Combining IG and HY keeps issuers in the universe after a downgrade (note 3, PDF p. 241).
- Snapshot at 31 July 2014 (Table 5.1, PDF p. 221): 2,091 issuers, 8,207 bonds, $5,599bn outstanding. IG holds 78.1% of MV (1,032 issuers). HY holds 21.9% (1,059 issuers, 2,177 bonds, average OAS 388bp).
- Sectors: eight custom sectors built from Barclays Class 3 industries (note 4, PDF p. 241):
  - Basic and Capital Goods; Cyclical; Noncyclical; Communication and Technology;
  - Transportation and Energy; Utilities; Banks and Brokerage; Financial Others.

  The issuer tests use three broad sectors: Industrial, Utility, Financial.
- Period: August 1994–July 2014 for the issuance-return tests (Figures 5.2, 5.3, 5.6). February 1994–July 2014 for the weight tests (Tables 5.3, 5.6, 5.8). Monthly data.
- Returns: index excess returns over duration-matched Treasuries (PDF p. 222). Total returns are also shown (Figure 5.2 Panel B).
- Issuer tests: issuers mapped to Compustat GVKEY. The mapping covers about 80% of the index bonds (PDF p. 228). The mapping method is in Ben Dor and Xu (2015b) (note 9). Bond tickers were not reliable issuer identifiers over time.
- Accounting variant: Compustat total liabilities and total assets (note 15, PDF pp. 241–242).
- Liquidity: Barclays LCS from 2007 (PDF p. 239).

### Definitions and formulas

**Net issuance (note 5, PDF p. 241).**
```latex
NI_{t-h,t} = \text{GrossNew}_{t-h,t} - \text{Redemptions}_{t-h,t} - \text{Maturing}_{t-h,t}
```
Intuition: new index debt minus debt that left. "Maturing" is the amount that leaves the index, lagged 12 months, because the index drops bonds with less than one year to maturity.

**Issuance rate, market or sector (PDF p. 222, note 6).**
```latex
IR^{mkt}_{t} = \frac{NI_{t-6m,t}}{AmtOut_{t}}
```
Intuition: the pace at which the stock of debt grows. The denominator is end-of-period debt so that new entrants are defined. Beginning-of-period debt gives the same conclusions.

**Forward excess return.** The cumulative index excess return over duration-matched Treasuries over the next 6 months, `XR_{t,t+6m}`. Observations are monthly and overlap.

**Issuance quartiles.** Pool all monthly observations over the full period. Split IR^mkt into quartiles Q1 (lowest) to Q4. Report the mean `XR_{t,t+6m}` per quartile. This is an in-sample, full-period ranking. Each subperiod in Table 5.2 is ranked on its own (note 7).

**Issuer issuance rate (PDF p. 228, note 10).**
```latex
IR^{iss}_{i,t} = \frac{NI_{i,t-12m,t}}{AmtOut^{index}_{i,t}}
```
Intuition: the issuer's 12-month net index debt growth. End-of-period debt keeps new issuers in the test.

**Aggressive vs moderate (PDF p. 228).**
```latex
Aggressive_{i,t} = \mathbf{1}\big[IR^{iss}_{i,t} > IR^{index}_{t}\big]
```
Intuition: the issuer grows its index debt faster than the whole index. `IR^index_t` is the same 12-month ratio for the full index.

**Accounting variant (PDF p. 233, note 15).**
```latex
IR^{acct}_{i,t} = \frac{TL_{i,t} - TL_{i,t-12m}}{TA_{i,t}}
```
Intuition: liability growth scaled by assets, which covers loans and private debt.
`TL` is total liabilities and `TA` is total assets at period end. The issuer is aggressive if `IR^acct` exceeds the index average. The book does not say whether that average is MV-weighted or equal-weighted.

**DTS-adjusted regression (PDF p. 231, Table 5.5).** Each month, run a cross-section over issuers:
```latex
XR_{i,t+1} = \sum_{g\in\{Agg,Mod\}}\sum_{s\in\{Ind,Util,Fin\}} \lambda_{g,s,t}\; DTS_{i,t}\,\mathbf{1}\{g\}\,\mathbf{1}\{s\} + \varepsilon_{i,t+1}
```
Intuition: λ is the excess return per unit of spread risk for each issuance group in each sector.
- DTS is duration × spread. One unit equals a duration of 2.5 years and a spread of 40bp, so spread is in percent (PDF p. 233).
- The book drops the top and bottom 1% of excess-return observations (note 14).
- The book shows no intercept. Our reading: no intercept.
- The issuer DTS timing is not stated. Our reading: DTS at the start of the month and the return over the month.

**Weight-dynamics contribution (PDF pp. 226–227).**
```latex
\text{Contrib} = XR^{MW} - XR^{Const}, \qquad XR^{Const}_t = \sum_s \bar w_s\, XR_{s,t}
```
Intuition: hold each sector at its time-average weight. The gap is the cost of time-varying weights.
Per-sector contribution:
```latex
C_s = \overline{w_{s,t}\,XR_{s,t}} - \bar w_s\,\overline{XR_{s}}
```
Intuition: the time covariance of a sector's weight and its return.

**Contrarian issuer weights (PDF p. 236, Table 5.7, note 18).**
```latex
\Delta_{i,t} = \frac{1+g^{index}_t}{1+g_{i,t}} - 1, \quad \Delta_{i,t}\in[-10\%,+10\%], \quad w_{i,t} = w_{i,t-1}(1+\Delta_{i,t})
```
Intuition: an issuer keeps the weight it would have if its debt grew at the index pace. Fast issuers shrink and slow issuers grow.
- `g` is the monthly percentage growth of amount outstanding.
- At inception, weights equal market weights. New issuers enter at full market weight. The cap is ±10% of the beginning-of-month weight.
- The text describes the moderate rule in words that differ ("net absolute percentage changes"). The Table 5.7 numbers match the ratio formula for both groups. For example, (1.02/1.00) − 1 = +2.0%. The cap binds at −8% issuer growth against +3% index growth, so +12% caps to +10%. We follow the table.
- The book does not state renormalisation or price drift. Our reading: renormalise to sum 1 each month after price drift.

**Alternative sector weights (PDF p. 235).**
- Equal Weights (EW): each of the 8 sectors gets 1/8 of MV each month.
- Equal Notional (EN): each sector gets an equal par amount, so price moves alone cause no rebalance.
- Within each sector, bonds stay market weighted. This is our reading. The book does not state it.

### Implementation steps

**A. Market-level test.**
1. Each month t, compute 6-month net index issuance (note 5) and `IR^mkt_t` with end-of-period amount outstanding.
2. Compute the forward 6-month cumulative excess return over duration-matched Treasuries.
3. Pool the months August 1994–July 2014. Form IR^mkt quartiles. Report the mean forward excess and total return per quartile.

**B. Sector-level test.**
1. Repeat A per sector. Report the Q1 − Q4 mean forward 6-month excess return for the full period and for the two subperiods. Rank each subperiod on its own.
2. By issuer size: sort issuers into quartiles of index debt outstanding. Correlate the 6-month issuance rate with the next-6-month excess return per size quartile (Figure 5.3 A).
3. Build the constant-weight benchmark from time-average sector weights. Report MW, Const, and MW − Const average excess return (%/yr), volatility and IR. Decompose by sector with `C_s`.

**C. Issuer-level test.**
1. Restrict to GVKEY-mapped issuers.
2. Each month, compute `IR^iss_{i,t}` over the trailing 12 months. Label the issuer aggressive if `IR^iss > IR^index`.
3. Form MV-weighted portfolios of aggressive and moderate issuers within each broad sector and in total. Rebalance monthly (our reading, from the monthly statistics).
4. Report monthly excess return (bp/m), volatility (bp/m), and annualised IR for Mod, Agg, and Mod − Agg. Split by rating: Aaa–Aa, A, Baa, Ba–B, Caa–C.
5. Run the monthly DTS cross-sectional regression. Average λ over time per group. Report the mean, volatility and IR of λ_Mod − λ_Agg.
6. Repeat steps 2–4 with `IR^acct` from Compustat.

**D. Index alternatives.**
1. Build EW and EN sector indices. Report the monthly excess return, volatility, IR, worst month and best month, and the difference against MW.
2. Build the contrarian issuer index with the Table 5.7 rule and the ±10% cap. Compare it with MW by sector. Plot LCS (2007+) for both.

### Results

**Market quartiles (Figure 5.2, PDF p. 223; August 1994–July 2014).** Mean 6-month issuance per quartile: Q1 5%, Q2 8%, Q3 9%, Q4 14%.

| Quartile | Next-6m excess return | Next-6m total return |
|---|---|---|
| Q1 | 3.04% | 6.11% |
| Q2 | 0.71% | 3.84% |
| Q3 | 0.07% | 2.93% |
| Q4 | −1.67% | 1.64% |

No t-stats are given. The observations overlap.

**Sector Q1 − Q4, % over 6 months (Table 5.2, PDF p. 223).**

| Sector | Aug 1994–Jul 2014 | Jul 1994–Dec 2005 | Jan 2006–Jul 2014 |
|---|---|---|---|
| Basic and Capital Goods | 0.56 | 2.11 | −1.96 |
| Cyclical | 3.19 | 2.62 | 4.47 |
| Noncyclical | 0.40 | 1.00 | 0.61 |
| Communication and Technology | 4.45 | 6.10 | −0.33 |
| Transportation and Energy | 2.66 | 3.14 | 2.58 |
| Utilities | 1.76 | 2.14 | 0.02 |
| Banks and Brokerage | 4.65 | 0.64 | 9.50 |
| Financial Others | 5.09 | 1.67 | 14.66 |
| Total | 4.72 | 2.61 | 7.26 |

**Size and sector correlations (Figure 5.3, PDF p. 224; text p. 225).**
- The correlation of issuance with the next-6m excess return grows more negative with issuer size. It reaches almost −25% for the top size quartile. That quartile holds 80% of index MV.
- Banks and Brokerage: −49%, with 93% of its MV in the top size quartile.
- Basic goods: −7.6%, with 67% in the top size quartile.
- The other bar heights are read from a chart only.

**Dynamic sector weights (Table 5.3, PDF p. 227).**

| Period | MW exc. %/yr | Const exc. %/yr | MW − Const %/yr | TE %/yr | IR |
|---|---|---|---|---|---|
| Feb 1994–Jul 2014 | 0.98 | 1.12 | −0.14 | 0.24 | −0.60 |
| Feb 1994–Jun 2007 | 0.63 | 0.73 | −0.10 | 0.13 | −0.79 |
| Jul 2007–Jul 2014 | 1.65 | 1.87 | −0.22 | 0.36 | −0.60 |

Figure 5.5 (PDF p. 227) shows the sector waterfall. Communication and Technology, Cyclical, Financials ex Banks, and Banks contribute negatively. Transportation and Energy and Noncyclical contribute positively. The total is −14bp/yr. The single bar values are not printed.

**Aggressive vs moderate, index-debt definition (Figure 5.6, PDF p. 229).** Units: bp/month.

| Sector | Mod exc. | Agg exc. | Mod − Agg | Mod vol | Agg vol | Diff vol | IR Mod | IR Agg | IR Diff |
|---|---|---|---|---|---|---|---|---|---|
| Industrial | 12.0 | 8.7 | 3.3 | 163 | 154 | 49 | 0.26 | 0.20 | 0.24 |
| Utility | 12.8 | 5.9 | 6.9 | 171 | 165 | 61 | 0.26 | 0.12 | 0.39 |
| Financial | 10.3 | 6.8 | 3.6 | 151 | 167 | 82 | 0.24 | 0.14 | 0.15 |
| Total | 11.9 | 6.1 | 5.9 | 154 | 150 | 60 | 0.27 | 0.14 | 0.34 |

**By rating (Table 5.4, PDF p. 230).** Units: bp/month.

| Rating | Mod | Agg | Diff | Diff vol | IR Diff |
|---|---|---|---|---|---|
| Aaa–Aa | 4.9 | 1.5 | 3.4 | 52.6 | 0.23 |
| A | 7.6 | −3.7 | 11.3 | 82.0 | 0.48 |
| Baa | 7.3 | 10.3 | −3.0 | 52.8 | −0.20 |
| Ba–B | 31.8 | 14.0 | 17.8 | 88.9 | 0.69 |
| Caa–C | 54.2 | 23.1 | 31.1 | 387.9 | 0.28 |
| Total | 11.9 | 6.1 | 5.8 | 60.1 | 0.34 |

The book explains the Baa reversal and the strong Ba–B result by fallen angels (PDF p. 231). Fallen angels issue little. They underperform while still Baa and recover once in Ba–B.

**Per unit of DTS (Table 5.5, PDF p. 232).** Units: bp/month per DTS unit.

| Sector | Mod | Agg | Mod − Agg | Diff vol | IR Mod | IR Agg | IR Diff |
|---|---|---|---|---|---|---|---|
| Industrial | 1.23 | 0.85 | 0.38 | 2.80 | 0.52 | 0.31 | 0.47 |
| Utilities | 1.14 | 0.72 | 0.42 | 4.31 | 0.44 | 0.25 | 0.34 |
| Financial | 1.22 | 1.13 | 0.09 | 3.52 | 0.54 | 0.44 | 0.09 |

At portfolio DTS 10, this gives about 3.8 and 4.2bp/month (PDF p. 233).

**Accounting definition (Figure 5.7, PDF p. 234).** Units: bp/month.

| Sector | Mod | Agg | Mod − Agg | Diff vol | IR Diff |
|---|---|---|---|---|---|
| Industrial | 14.2 | 6.0 | 8.2 | 43 | 0.66 |
| Utility | 12.3 | 6.2 | 6.1 | 90 | 0.23 |
| Financial | 10.0 | 9.8 | 0.2 | 67 | 0.01 |
| Total | 13.5 | 5.6 | 7.9 | 39 | 0.70 |

The DTS regression on this definition gives similar results. No table is shown (note 16).

**Alternative sector weights (Table 5.6, PDF p. 235; February 1994–July 2014).** Units: bp/month.

| | MW | EW | EW − MW | EN | EN − MW |
|---|---|---|---|---|---|
| Avg exc. | 8.2 | 9.7 | 1.5 | 9.5 | 1.4 |
| Vol | 155 | 155 | 13 | 154 | 14 |
| IR | 0.18 | 0.22 | 0.40 | 0.21 | 0.33 |
| Worst month | −907 | −1002 | −95 | −1007 | −99 |
| Best month | 671 | 697 | 100 | 678 | 109 |

EW beats MW by a cumulative 3.5% over January 1994–July 2014, mostly in crises and recoveries (Figure 5.8, PDF p. 236).

**Contrarian issuer weights (Table 5.8, PDF p. 238; February 1994–July 2014).**

| Sector | MW exc. bp/m | MW vol | MW IR | Contrarian exc. | Contrarian vol | Contrarian IR |
|---|---|---|---|---|---|---|
| Basic and Capital Goods | 11.9 | 136 | 0.30 | 19.1 | 163 | 0.41 |
| Cyclical | 13.3 | 203 | 0.23 | 17.7 | 284 | 0.22 |
| Noncyclical | 10.0 | 116 | 0.30 | 13.0 | 115 | 0.39 |
| Communication and Technology | 8.7 | 201 | 0.15 | 15.3 | 188 | 0.28 |
| Transportation and Energy | 11.9 | 152 | 0.27 | 12.3 | 107 | 0.40 |
| Utilities | 9.0 | 162 | 0.19 | 10.8 | 151 | 0.25 |
| Banks and Brokerage | 8.6 | 156 | 0.19 | 13.3 | 140 | 0.33 |
| Financial Others | 11.2 | 177 | 0.22 | 19.3 | 194 | 0.34 |
| Total | 9.4 | 148 | 0.22 | 14.7 | 146 | 0.35 |

The contrarian column header prints "%/m". The values match bp/m, so we read the header as a typo. The contrarian index LCS sits above the MW index LCS throughout 2007–2014, most of all in 2008 (Figure 5.9, PDF p. 239). The figure has no values.

### Robustness and variants

- Two subperiods (Table 5.2): the sign holds in total and for most sectors. It flips for Basic and Capital Goods and for Communication and Technology after 2006, where the issuance cycle was mild (PDF p. 224).
- Beginning-of-period denominator: same conclusions (note 6). Excluding new issuers: same conclusions (note 10).
- DTS control: moderate still beats aggressive in Industrial and Utility. The effect is weak in Financial (Table 5.5).
- Accounting definition: the gap is larger (total IR 0.70) and weak in Financial (Figure 5.7).
- Rating buckets: the result holds in all buckets except Baa (Table 5.4).
- Constant-weight variants: EW and EN give the same result. Any constant scheme should work (note 17).

### Limits and caveats

- The market quartile test is in-sample. It pools overlapping 6-month windows and reports no standard errors. The quartile cut-offs use the full sample (look-ahead in the cut-offs).
- The issuer test uses market-weighted portfolios. The Mod − Agg differences are before transaction costs. Contrarian weights raise turnover and LCS (PDF p. 237). The book reports no net results.
- The sample is mostly IG: 78% of MV in July 2014. The Ba–B and Caa–C rows are the only HY evidence (Table 5.4). The Ba–B result partly reflects fallen angels.
- Issuance is measured only from index bonds. It misses loans and private debt (PDF p. 233). The accounting variant addresses this.
- The data are Barclays-proprietary: index flows, amount outstanding, OAS, DTS, Class 3 sectors, LCS, and the GVKEY map.
- The IR values appear annualised. For example, 11.9/154 × √12 ≈ 0.27 matches the table. The book does not state this.
- The contrarian renormalisation and the within-sector weights are not specified.

### Implementation in this repo

**Module and section.**
- The issuer-level "aggressive issuer" flag is an issuer state feature. It goes in Section 4.3 (capital structure), `hy/state.py`.
- It is a candidate input to S2 (fundamental momentum) in Section 8, `hy/signals.py`.
- The market and sector issuance rates feed S7 (macro-conditional sector tilt) and the Section 5.2 macro conditioning. S7 failed on its macro term, so issuance is a candidate replacement driver for `η̂_sector`.
- The DTS-adjusted test matches Section 7.4 (spread per unit of risk).
- The back-test goes in `hy/backtest.py`, Section 11.

**What we have.**
- Compustat point-in-time (`hy/sources/compustat_pit.py`): total liabilities (ltq), total assets (atq), debt (dlttq, dlcq). The accounting variant can run directly.
- TRACE bonds (`hy/sources/trace_bonds.py`): bond issue dates.
- TRACE panel: G-spreads, from which we derive a duration proxy and DTS. Treasury curve (`hy/sources/treasury.py`) for duration-matched excess returns.

**What we lack and the proxy.**
- No index amount outstanding or redemptions. Proxies:
  - (a) Use the accounting rate `IR^acct = ΔTL_{12m} / TA`. This is the book's own alternative.
  - (b) Use debt only: `(Debt_t − Debt_{t−12m}) / TA_t`, with Debt = dlttq + dlcq.
  - (c) For the market and sector rates, sum (b) across HY issuers in each sector, weighted by debt.
- No OAS or DTS. Proxy: DTS = modified duration × G-spread (%).
- No Barclays sectors. Use GICS sectors from `peers.sector_at`.

**Lag rule (as_of, available_at).**
- A Compustat quarter has `as_of` = fiscal period end. `available_at` = the SEC filing acceptance date (10-Q or 10-K). Use the report date (rdq) if the filing date is missing.
- The flag at month-end t uses the latest quarter with `available_at ≤ t`, and the quarter four quarters earlier.
- The index-average rate at t uses only issuers with `available_at ≤ t`.
- Quartile cut-offs for any market or sector test use an expanding window up to t, not the full sample.
- Trade at month-end t. Measure the return over month t+1.

**Falsifiable test.**
- Signal: moderate minus aggressive HY issuers, with the accounting definition (ΔTL_12m / TA above or below the cross-sectional median at t).
- Horizon: monthly rebalance, 1-month forward return.
- Metric: the monthly excess return over duration-matched Treasuries, regressed cross-sectionally per unit of DTS, as λ_Mod − λ_Agg. Also report the rank IC of −IR^acct against the next-month DTS-scaled excess return.
- Pass:
  - the mean λ_Mod − λ_Agg is > 0 with t > 2 over 2005–2024, after a TRACE bid-ask cost on flag changes;
  - the rank IC is > 0 in at least three of the four cycles (2008, 2015, 2020, 2022).
- Fail: the result holds only in Financial, or only before costs. Then drop the flag.

---

## Chapter 6. The Value of Waiting to Buy: Inclusion-Delay Investment-Grade Corporate Indices (PDF pp. 243–266)

Printed folio = PDF page − 28. Page 266 is blank. All page numbers below are PDF pages.

**Question.** Does an index that adds new IG issues only X months after they become eligible beat the standard IG Corporate index, and why?

**Answer.** A 24-month delay index beat the bid-adjusted standard index by 3.2bp/m in excess return from Feb 2007 to Aug 2016, with correlation 1.00 (Table 6.3, p. 250). Over Jan 1990–Aug 2016 the 1.8bp/m gain over the IG Corporate index splits into 0.9bp/m pricing convention, 1.2bp/m avoidance of "problem bonds", and −0.3bp/m seasoning (Table 6.7, p. 261). The seasoning part was −1.0bp/m before 2007 and +0.8bp/m after July 2009.

### Data

- Universe: Bloomberg Barclays US IG Corporate index and IG Long Corporate index, all bonds that meet index rules (p. 243).
- Frequency: monthly, index returns in bp/m.
- Periods:
  - LCS-based bid-price adjustment and delay indices: Feb 2007–Aug 2016, 115 months (pp. 246, 249). Delay indices start construction well before Jan 2007 so the delay is full from Feb 2007 (note 14, p. 265).
  - Decomposition with Clean and Young & Clean indices: Jan 1990–Aug 2016 (Table 6.5, p. 258).
- New issues Jan 2007–Aug 2016: 7,431 (note 8, p. 265).
- Data sources: Bloomberg Barclays index database, Barclays Liquidity Cost Scores (LCS) and trader bid-offer quotes (pp. 245–246, note 8). All proprietary.
- Timing of entry: "time from dated date" field (note 11, p. 265). HY bonds upgraded to IG still enter the next month at bid (notes 2, 6, 12).

### Definitions and formulas

**Month zero.** The month in which an index-eligible bond is announced. The bond enters the Returns Universe at the end of month 0 and earns index return in month 1 (p. 245).

**X-month inclusion-delay index (p. 244, p. 248).** Add a bond at the end of month X, counted from month 0, only if it is still index-eligible then. A bond that leaves the index (for example, a downgrade to HY) before month X never enters. X ∈ {0, 1, 3, 6, 12, 18, 24}.

**Natural weights.** Market-value weights of the delay index's own holdings (p. 248).

**Adjusted weights.** Match the IG Corporate index market-value weight in 12 cells: 3 sectors (FIN, IND, UTL) × 4 qualities (AAA, AA, A, BAA). Within a cell, use the delay index's own bonds at market-value weight (p. 245). Our reading: rescale bond weights inside each cell so that the cell total equals the IG Corporate cell weight.

**Liquidity Cost Score (p. 246).**

```latex
LCS_t = \frac{OP_t - BP_t}{BP_t}
```

Intuition: round-trip cost as a share of the bid price.

**Bid price of a new issue at entry (p. 246).**

```latex
BP_0 = \frac{OP_0}{1 + LCS_0}
```

Intuition: strip the half-spread-like offer premium from the index entry price. Source of `LCS_0`, in order: trader quote at t = 0, published LCS for month 0, LCS extended-coverage model (p. 246). Example: `OP_0` = 100.2, `LCS_0` = 0.200%, `BP_0` = 100.0.

**Bid-to-bid adjusted first-month price return (p. 246).**

```latex
AdjPriceRet_{1} = \frac{BP_1 - BP_0}{BP_0 + AI_0}
\approx ReportedPriceRet_{1} + \frac{BP_1 \cdot LCS_0}{OP_0 + AI_0}
```

Intuition: the offer-to-bid convention charges the new buyer the bid-offer cost in month 1, and this term adds it back. The approximation assumes `AI_0 × LCS_0` is small.

Then recompute beginning-of-month index weights with the lower bid value of new issues (p. 247). Every delay index uses bid-to-bid for all bonds. The "0-month delay index" is the IG Corporate index with bid-to-bid pricing for new issues (p. 244).

**Pre-2007 back-fill (p. 257–258).** No LCS before 2007. Apply a fixed first-month return uplift: +42.5bp for intermediate and +79.3bp for long new issues. Adjust bond weights to match.

**Problem bond (p. 256).** A bond downgraded to HY or that defaults within 24 months after it becomes index-eligible.

**Clean 0-month delay index (p. 256).** The 0-month delay index with problem bonds removed by look-ahead. Adjusted weights.

**Young & Clean index (p. 256).** Non-problem bonds issued within the past 24 months. Clean = 24-month delay index ∪ Young & Clean.

**Return decomposition (Table 6.7, p. 261).** Our reading of the arithmetic:

```latex
\underbrace{r_{24} - r_{IG}}_{\text{total}} =
\underbrace{(r_{0} - r_{IG})}_{\text{bid-to-bid pricing}} +
\underbrace{(r_{clean,0} - r_{0})}_{\text{problem-bond avoidance}} +
\underbrace{(r_{24} - r_{clean,0})}_{\text{seasoning}}
```

Intuition: each step removes one difference between the standard index and the delay index. The book does not write this identity. It matches Table 6.7: 0.9 + 1.2 − 0.3 = 1.8bp/m.

### Implementation steps

1. Build the monthly IG Corporate constituent list with month-0 dates from the dated-date field.
2. For each new issue, compute `BP_0` from `OP_0` and `LCS_0`. Recompute the month-1 return bid to bid. Rebuild the 0-month index weights and returns.
3. For each X, hold a queue of new bonds. At the end of month X after month 0, add each bond that is still eligible. Drop bonds that leave the index by normal rules.
4. Weight: natural (market value of own holdings) or adjusted (12-cell sector × quality match). Rebalance monthly.
5. Return: index total return and excess return over duration-matched Treasuries (the Bloomberg Barclays index excess-return definition). Monthly bp.
6. Report mean, standard deviation, annualized IR, correlation with the IG Corporate index.
7. For the decomposition, build Clean 0-month and Young & Clean indices with 24-month look-ahead. Use adjusted weights, Jan 1990–Aug 2016, with the fixed pre-2007 uplift.
8. Split into Jan 1990–Jan 2007 and Jul 2009–Aug 2016, which leaves out Feb 2007–Jun 2009.

No transaction costs enter the index returns. Turnover of adjusted-weight delay indices: about 1.2%/m for short delays and 1.45%/m for long delays (note 17, p. 265).

### Results

Table 6.1 (p. 247), IG Corporate, Feb 2007–Aug 2016, bp/m:

| | Offer-to-bid Tot | Offer-to-bid Exc | Bid-to-bid Tot | Bid-to-bid Exc | Diff Tot | Diff Exc |
|---|---|---|---|---|---|---|
| Mean | 50.7 | 6.3 | 51.5 | 7.2 | 0.9 | 0.9 |
| Stdev | 175.8 | 176.3 | 175.9 | 176.4 | 0.1 | 0.1 |
| Annual IR | 1.00 | 0.12 | 1.01 | 0.14 | | |

- Bid-to-bid adds about 0.9bp/m or 11bp/yr, about 14% (p. 247). Spike to about 2bp/m in the crisis (Figure 6.1).
- New issues' first-month MV-weighted excess return: −11bp offer-to-bid, +42bp bid-to-bid, +53bp (p. 246). IG Long: −18bp vs +62bp, 79bp (note 10, p. 265).
- IG Long (Table 6.2, p. 248): excess 1.9 vs 3.3bp/m, difference 1.4bp/m, about 16bp/yr.

Table 6.3 (p. 250), IG Corporate, natural weights, Feb 2007–Aug 2016, excess return bp/m:

| | IG Corp (O-B) | 0-mth | 1-mth | 3-mth | 6-mth | 12-mth | 18-mth | 24-mth |
|---|---|---|---|---|---|---|---|---|
| Mean | 6.3 | 7.2 | 6.5 | 6.7 | 7.3 | 8.3 | 9.5 | 10.4 |
| Stdev | 176.3 | 176.4 | 176.3 | 176.6 | 176.5 | 173.7 | 171.5 | 167.5 |
| Annual IR | 0.1 | 0.1 | 0.1 | 0.1 | 0.1 | 0.2 | 0.2 | 0.2 |
| Corr | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |

Total-return means: 50.7, 51.5, 50.8, 50.9, 51.2, 51.7, 52.4, 53.1.
- 24-month minus 0-month: 3.2bp/m, about 372bp cumulative over 115 months (p. 249).
- 1-month delay underperforms 0-month by 0.7bp/m (p. 249).

Table 6.4 (p. 251), IG Long, excess bp/m: IG Long 1.9, 0-mth 3.3, 1-mth 2.1, 3-mth 2.1, 6-mth 2.8, 12-mth 3.3, 18-mth 4.2, 24-mth 4.4. The text gives 18-mth +0.9 and 24-mth +1.1bp/m over 0-mth (p. 249).

Table 6.5 (p. 258), adjusted weights, Jan 1990–Aug 2016, excess bp/m:

| | IG Corp (O-B) | 0-mth | Clean 0-mth | 24-mth | Young & Clean |
|---|---|---|---|---|---|
| Mean | 4.7 | 5.6 | 6.8 | 6.5 | 7.7 |
| Stdev | 115.2 | 115.2 | 112.3 | 108.1 | 120.2 |
| Annual IR | 0.14 | 0.17 | 0.21 | 0.21 | 0.22 |
| Corr | | 1.00 | 1.00 | 1.00 | 0.99 |

Total-return means: 58.3, 59.2, 60.4, 58.5, 64.0.

Table 6.6 (p. 260), excess bp/m, adjusted weights:

| Period | IG Corp | 0-mth | Clean 0-mth | 24-mth | Young & Clean |
|---|---|---|---|---|---|
| Jan 1990–Jan 2007 mean | 3.8 | 4.7 | 5.9 | 4.9 | 8.0 |
| Jan 1990–Jan 2007 IR | 0.23 | 0.28 | 0.36 | 0.31 | 0.46 |
| Jul 2009–Aug 2016 mean | 6.8 | 7.7 | 9.1 | 9.9 | 7.7 |
| Jul 2009–Aug 2016 IR | 0.13 | 0.15 | 0.18 | 0.20 | 0.14 |

Table 6.7 (p. 261), 24-month delay minus IG Corporate, bp/m:

| Component | Jan 1990–Aug 2016 | Jan 1990–Jan 2007 | Jul 2009–Aug 2016 |
|---|---|---|---|
| Bid-to-bid pricing | 0.9 | 0.9 | 0.9 |
| Problem-bond avoidance | 1.2 | 1.1 | 1.4 |
| Seasoning | −0.3 | −1.0 | 0.8 |
| Total | 1.8 | 1.1 | 3.2 |

The text gives 3.1bp/m (9.9 − 6.8) for the last period total (p. 260). The table gives 3.2. The gap is rounding.

Cumulative, Jan 1990–Aug 2016 (Figure 6.10, p. 262): 716bp total, 296bp pricing, 432bp problem-bond avoidance, −12bp seasoning.

Other numbers:
- Correlation of (Clean 0-mth − 24-mth) excess return with the monthly change in IG OAS: −0.53 (p. 259).
- 24-month index: duration 0.27 shorter and OAS 8bp higher than IG Corporate on average (note 5, p. 264).
- LCS correlation with bond age 0.27, with trading volume −0.06. A 24-month-old bond can have an LCS 50% higher than at issue (p. 263).

### Robustness and variants

- Delay length 0 to 24 months, natural and adjusted weights (Tables 6.3–6.4, Figures 6.4, 6.6).
- IG Corporate and IG Long Corporate.
- Two subperiods excluding the crisis (Table 6.6).
- Quality subsets (A/Baa-only, Baa-only) are in Ng and Phelps (2016), not in the book (note 13, p. 265).

What holds: long delays (≥ 12 months) beat 0-month in every reported variant. The problem-bond part is stable at 1.1–1.4bp/m. The seasoning part changes sign across subperiods.

### Limits and caveats

- IG only. The problem-bond event is a downgrade to HY or default.
- Returns are before costs. The delay index buys at bid. A manager who buys seasoned bonds at offer pays a higher LCS (p. 263). The 296bp pricing part is hard to harvest (p. 262).
- Clean and Young & Clean use 24-month look-ahead. They are analysis tools, not investable (note 15, p. 265).
- Pre-2007 pricing uses a fixed uplift, so the pricing part is the same in all periods by construction (p. 261).
- LCS, trader quotes and the index database are Barclays proprietary.
- The financial-sector story in 2007–2009 (pp. 252–255) drives much of the natural-weight gap. One crisis dominates the Feb 2007–Aug 2016 sample.

### Implementation in this repo

**Mapping.** This is a portfolio-construction rule, not a bond signal. It maps to methodology §11 (backtest: eligibility and entry timing) and to §8 S6 (forced flows), because problem-bond avoidance is a downgrade-avoidance effect. A new-issue age filter belongs in `hy/backtest.py`.

**What we have.** TRACE trades and monthly G-spread per CUSIP (`hy/sources/trace_panel.py`), maturity from `trace_bonds`. S&P issuer ratings to Feb 2017.

**What we lack.** Index membership, dated date, amount outstanding, LCS.

**Proxies.**
- Issue date: first TRACE trade date of the CUSIP. Our reading: this is within days of the offering date for most 144A and public bonds, but this is not tested.
- Weight: `par_volume` in place of market value.
- Problem bond (HY version, ours): default, or price below 70, or G-spread above 1,000bp, within 24 months of first trade. Ratings cannot cover this after Feb 2017.
- Bid-offer cost: TRACE `bid_ask_pts` in the panel.

**Lag rule.** Bond age at month t = t − first trade date, with `available_at` = first trade + 1 day. A bond enters an X-month delay set only if X months have passed by the decision date. The problem-bond flag uses future data. Use it only to decompose results, never as a filter in a backtest.

**Falsifiable test.**
- Signal: within each month, sort HY bonds into age < 24 months and age ≥ 24 months. Within each age group, match on G-spread decile and remaining maturity bucket.
- Return: monthly excess return over duration-matched Treasuries, approximated as `g_spread/12 − mod_dur × Δg_spread`.
- Horizon: one month, TRACE 2010–2026.
- Metric: mean of (seasoned − young) matched excess return, Newey–West t with 6 lags, and its sign in the 2015, 2020 and 2022 windows.
- Pass: mean > 0 with t ≥ 2 after subtracting the bid-ask difference between the two groups, and positive in at least two of the three windows. If it fails, keep new issues eligible from month 0 in the backtest.

---

## Chapter 7. Concessions in Corporate Bond Issuance: Magnitude, Determinants, and Post-issuance Dynamics (PDF pp. 267–289)

Printed folio = PDF page − 28. Pages 290–292 are the part opener for Part 3 ("Performance Cost of Investment Constraints"), not chapter 7. All page numbers below are PDF pages.

**Question.** How large is the new-issue concession on US IG corporate bonds, what drives it, how fast does it close, and how much alpha does it give?

**Answer.** The median concession is 9bp. Eight supply and demand factors plus dummies explain 61% of its cross-section, led by deal size and index spread level and change (Table 7.6, p. 278). The concession closes mostly on day 1 (median 9bp → 3bp, then 2bp after a week) and gives an index-replicating buyer about 14bp/yr since 2008 (pp. 282, 286).

### Data

Two datasets (Table 7.1, p. 270):

| | Barclays Syndicate | Bloomberg / POINT (B/P) |
|---|---|---|
| Sample start | 2008 | 2000 |
| Bonds | 1,218 (876 issuance events) | 3,334 (2,643 events) |
| Rules-based benchmark bond | No | Yes |
| Benchmark identity | Unknown | Known |
| Maturity gap adjusted | Yes | No |
| Concession definition | ask_t − bid_(t−1) | ask_t − bid_t |
| Benchmark pricing | Multiple sources | POINT (Barclays quotes) |

- Syndicate regression period: Jan 2008–Feb 2014 (Table 7.6, p. 278).
- Universe: US IG corporate new issues. Covers issues whether or not Barclays underwrote them (p. 268).
- Other sources: Dealogic (use of proceeds), Lipper (IG fund flows), Barclays LCS (p. 276, Table 7.4 note).
- Use the Syndicate data for determinants. Use B/P for post-issue dynamics (p. 271).

### Definitions and formulas

**Concession (p. 268).**

```latex
C_i = s^{ask}_{new,i}(t) - s^{bid}_{bench,i}(t-1)
```

Intuition: the extra spread a buyer gets over the issuer's own similar outstanding bond. Syndicate: benchmark bid from the prior day, maturity-adjusted with the Bloomberg yield calculator (note 6, p. 288). B/P: benchmark bid at close of day t, no maturity adjustment. Note 2 (p. 288): the concession is the P&L of short the secondary bond, long the new issue.

**B/P benchmark bond rule (note 5, p. 288).** Same issuer, same credit notch rating, same callability, closest maturity to the new bond.

**Post-issue concession (p. 282).** Day 0 = new-issue ask spread (Bloomberg) minus benchmark bid (POINT). Days 1–20 = bid minus bid (both POINT).

**Regressors (Tables 7.3–7.4, pp. 272, 275–276; Table 7.6, p. 278).**

| Variable | Definition | Predicted sign |
|---|---|---|
| Abs. issue size | log of total issuance size | + |
| Relative size | total issuance size / issuer debt outstanding | + |
| Frequent issuer | 1 if ≥ 4 issuance events in trailing 12 months | + |
| Past issuance | log of debt issued in trailing 12 months | + |
| Index OAS level | Corporate Index OAS on day t−1 | + |
| Index OAS change | change in Corporate Index OAS over the month before pricing (t−1 to t, per Table 7.6 label) | + |
| LCS | Corporate Index LCS in the month before pricing | − |
| Peer spread diff. | peer spread change over prior 3 months | + |
| Bond redemption | log of debt redeemed or called in prior month | − |
| Fund flows | 4-week average IG fund flow, % of total assets (Lipper) | − |
| Use of proceeds | dummies M&A, Financing, CapEx. Base case GCP. | ? |
| Maturity | dummies ≤ 5y, ≥ 15y | ? |
| Industry | dummies Financials, Utilities. Base Industrials. | ? |
| Rating | dummies AA or above, A. Base BAA. | ? |
| Issuer spread | issuer spread 15 business days before pricing (avoids endogeneity) | + |

Table 7.3 (p. 272) predicts "+" for all four supply factors. Relative size proxies passive (index fund) demand, per the book.

**Regression (p. 277).** OLS of `C_i` on all regressors, one row per bond (not per deal, note 12 p. 289). The book reports no standard-error correction.

```latex
C_i = \alpha + \beta^\top x_i + \varepsilon_i
```

**Alpha of a new issue (p. 286).**

```latex
\alpha_i \approx C_i \times SD_i \times \frac{MV_i}{MV_{index}}
```

Intuition: the concession earned on the new bond, scaled by its spread duration and by its index weight. Summed over all new issues in a period, this is the alpha of a manager who gets allocations in proportion to index weights. New issues join the index only on the last day of their issue month, so the concession is outside index returns (p. 285).

### Implementation steps

1. For each new bond, record pricing date, ask spread, issuer, size, maturity, rating, use of proceeds, callability.
2. Pick the benchmark bond: same issuer, same notch, same call feature, closest maturity. Read its bid spread on t−1 (Syndicate) or t (B/P).
3. Compute `C_i`. Optional: adjust for the maturity gap on the issuer curve.
4. Build regressors as in the table above. Issuer spread at t−15 business days.
5. Fit OLS on Jan 2008–Feb 2014. Report coefficients, t-stats, adjusted R².
6. Post-issue path: compute the bid–bid spread gap on business days 1–20 after pricing. Report median and mean by day.
7. Secondary-bond effect: for each issuer, compute the market-value-weighted spread of its outstanding bonds relative to peers. Peers = Industrial bonds of the same rating in the same maturity bucket (<5y, 5–10y, >10y) (note 13, p. 289). Track from −4 to +4 weeks around pricing. Split by deal size.
8. Alpha: sum `α_i` per year over all new issues.

### Results

Table 7.2 (p. 270), distribution of concessions (bp):

| | Syndicate | B/P full | B/P matched to Syndicate |
|---|---|---|---|
| P25 | 0 | −2 | 0 |
| Median | 9 | 9 | 12 |
| P75 | 18 | 22 | 26 |
| Mean | 13.28 | 9.97 | 12.86 |
| Std | 20.98 | 30.57 | 30.26 |
| % negative | 12% | 27% | 24% |

- Bond-level correlation Syndicate vs B/P matched: 0.53. Monthly median correlation: 0.91 (p. 270, Figure 7.1).
- Median concession vs. index spread by year: correlation 0.72, monthly 0.89 (p. 273, note 9). Pre-2008 median 5–10bp, over 20bp in the crisis (p. 273).

Table 7.5 (p. 277), concession by characteristic (count, mean, median, bp):

| Group | Count | Mean | Median |
|---|---|---|---|
| AA and above | 470 | 11.54 | 10.0 |
| A | 1,492 | 10.04 | 8.0 |
| BAA | 1,372 | 9.35 | 9.0 |
| Financials | 979 | 8.00 | 8.0 |
| Industrials | 1,862 | 11.28* | 10.0 |
| Utilities | 493 | 8.91 | 7.0 |
| GCP | 1,771 | 9.89 | 8.0 |
| Financing | 810 | 10.15 | 8.0 |
| M&A | 152 | 12.39 | 12.0 |
| CapEx | 88 | 2.04* | 5.0 |
| Size Q1 (< $400mn) | 696 | 7.30 | 6.0 |
| Q2 ($400–675mn) | 609 | 8.46 | 6.5 |
| Q3 ($675mn–1bn) | 710 | 8.51 | 7.0 |
| Q4 ($1–2bn) | 740 | 11.75* | 10.0 |
| Q5 (> $2bn) | 579 | 14.28* | 13.0 |

\* = difference from the first group is significant.

Table 7.6 (p. 278), Syndicate, Jan 2008–Feb 2014, n = 1,218, adj. R² = 61%:

| Driver | Coef. | t |
|---|---|---|
| Intercept | −73.46 | −8.13*** |
| Abs. issue size (log) | 5.21 | 9.05*** |
| Issue size / debt outstanding | 3.19 | 3.00*** |
| Frequent issuer | 2.37 | 1.88* |
| Past issuance size (log) | 0.12 | 1.72* |
| Corporate Index OAS (t−1) | 0.16 | 10.68*** |
| Corporate Index OAS change (t−1, t) | 0.12 | 5.87*** |
| LCS (t−1) | −0.15 | −4.54*** |
| Three-month peer spread diff. | 0.01 | 0.93 |
| Bond redemption (prior month, log) | −2.83 | −1.29 |
| Flows to IG funds (4wk avg, % assets) | −5.65 | −1.87* |
| M&A deal | −2.95 | −1.67* |
| Financing deal | −4.38 | −4.33*** |
| CapEx deal | −2.52 | −0.69 |
| Maturity ≤ 5y | 0.41 | 0.35 |
| Maturity ≥ 15y | 2.07 | 1.85* |
| Financials | 2.15 | 1.88* |
| Utilities | 1.43 | 1.09 |
| AA or above | −0.92 | −0.59 |
| A | −1.16 | −1.09 |
| Issuer spread (−15d) | 0.02 | 3.41*** |

The text gives t = 3.90 for relative size (p. 279). The table prints 3.00. The text also says frequent issuers pay 2.4bp more (coefficient 2.37). The units of log size are not stated. Scenario 1 uses Δlog = 0.69 for $1bn → $2bn, so the log is natural log of size.

Table 7.7 (p. 280), scenarios:
- $1bn debt issuer raises deal size $1bn → $2bn: +3.63bp (size) + 3.17bp (ratio) = +6.79bp.
- Index spread 100bp a month ago → 120bp day before: +3.13 (level) + 2.4 (change) = +5.53bp.
- LCS +10bp: −1.52bp.
- A 10% fund inflow cuts the concession by only 0.6bp (p. 279).

Table 7.8 (p. 281), out-of-sample style checks:
- GE Capital 1.5% 3y, 7/9/2013: predicted 14.7bp, realized 15bp.
- Verizon 6.55% 30y, 9/11/2013: predicted 68bp, realized 90bp. Size-weighted concession for the whole $45bn deal: 74bp (p. 280).

Post-issue (pp. 282–283):
- Median concession: 9bp at pricing, 3bp after day 1, 2bp after a week, then flat (Figure 7.3).
- With Bloomberg ask for the new bond: about 0.5bp one week after pricing (Figure 7.4).

Secondary bonds (pp. 284–285):
- Verizon Sep 2013: its bonds widened about 80bp in eight days to about 190bp, then relative spread tightened 40bp after the deal.
- Mean reversion after pricing only in the 10 largest deals (> $9bn). Other deals kept widening after pricing (Figure 7.6).

Alpha (pp. 286–287):
- Concessions gave about 14bp/yr on average since 2008, above 20bp in 2008 and 2009 (Figure 7.7).
- Comparison, Table 7.9 (p. 287), from Desclée et al. (2014), 1996–2013 average alpha bp/yr: issuer selection 37.1 (vol 96.4, IR 0.38), sector rotation 12.6 (vol 67.8, IR 0.19), market timing 9.6 (vol 47.8, IR 0.2). Skill definitions in note 14 (p. 289).

### Robustness and variants

- Two datasets with different benchmark rules agree at monthly median level (0.91).
- Post-issue path with bid and with ask (Figures 7.3–7.4).
- Secondary effect by deal size thresholds ≥ $1bn, ≥ $2bn, ≥ $4bn, ≥ $5bn, top 10 (Figure 7.6).
- No out-of-sample test of the regression. Table 7.8 bonds are inside the sample (p. 282).

### Limits and caveats

- IG only, Jan 2008–Feb 2014 for the regression, a period dominated by the crisis (p. 280).
- Syndicate data is Barclays proprietary. The benchmark bond choice is discretionary (note 3).
- B/P data has more noise: 27% negative concessions (Table 7.2).
- Alpha needs primary-market allocations, which not every manager gets (p. 287). Allocation is assumed pro rata to index weight. No cost of the fill uncertainty.
- The alpha estimate is before costs.

### Implementation in this repo

**Mapping.**
- §9 event risk: a new issue is an event for the issuer's existing bonds. Pre-pricing widening and post-pricing drift (pp. 284–285) belong in `hy/events.py` as an event type.
- §7.5 residual dynamics: the concession is a residual that closes in about one day. It sets a floor on how fast a primary-market residual decays.
- §8 S4 capital structure relative value: new bond against the issuer's own outstanding curve.
- §3.3 capital structure table records each new issue.

**What we have.** TRACE trades with dealer side, G-spread per bond, maturity, `bid_ask_pts`. Compustat debt outstanding for the relative-size ratio. Treasury curve.

**What we lack.** Syndicate concession data, offering spread, use of proceeds (Dealogic), Lipper flows, LCS, deal announcement time.

**Proxies.**
- Offer spread: G-spread of customer buy trades on the first TRACE trade day.
- Benchmark: issuer's outstanding bond with the closest maturity, G-spread on the day before the first trade. Adjust for the maturity gap with the slope of the issuer's own G-spread curve where it has ≥ 3 bonds.
- Market uncertainty: median HY G-spread of the TRACE panel in place of Corporate Index OAS.
- Liquidity: median `bid_ask_pts` in place of LCS.
- Use of proceeds: 8-K or 424B prospectus text from EDGAR (`hy/sources/edgar.py`).

**Lag rule.** Pricing date is unknown, so use first TRACE trade date d. Concession `as_of` = d, `available_at` = d + 1 day (WRDS load lag, as in `trace_bonds`). All regressors must have `available_at` ≤ d − 1. Debt outstanding from the last Compustat filing with `available_at` ≤ d.

**Falsifiable test.**
- Signal: HY concession proxy as above, TRACE 2010–2026.
- Metric 1: median concession on day 0 and its decay. Pass: median > 0 with a sign test p < 0.01, and the median on day 5 is at most one third of day 0.
- Metric 2: regression of the concession on log size, size / debt, median HY G-spread at d−1, and its one-month change. Fit on 2010–2017, test on 2018–2026.
- Pass: out-of-sample R² ≥ 0.20, and the coefficients on log size and spread level stay positive with t ≥ 2 in both halves. If it fails, the book's IG determinants do not carry over to HY, and the event model uses only the empirical day-0 to day-5 path.

---

## Chapter 8. "Try-and-Hold" Credit Investing (PDF pp. 293–330)

Printed folio = PDF page − 28. All page numbers below are PDF pages.

**Question.** What is the long-horizon return distribution of a bond for an investor who must sell it on a downgrade below a rating threshold, and how does the current spread level change it?

**Answer.** For a try-and-hold investor, forced sales on downgrade, not defaults, are the main loss. A sell-at-Ba rule cuts the five-year expected excess return of a five-year Baa bond from 693bp (hold to default) to 570bp, and a sell-at-B rule gives the best return per unit of risk (Table 8.4, pp. 302–303). High spreads predict more downgrades and defaults and wider rating spread gaps for about two years, so the authors scale the year-1 transition matrix by the ratio of current to long-term spread and decay that scale with a one-year half-life (pp. 321–325, notes 22–23 p. 330).

### Data

What the book uses:

| Item | Source | Period | Page |
|---|---|---|---|
| One-year letter rating transition matrix | Moody's, Ou, Chiu, Wen, Metz (2013), Exhibit 26, "Average One-Year Letter Rating Migration Rates, 1970–2012". Withdrawn ratings removed by prorating each row to 100%. | 1970–2012 | note 8, p. 329 |
| Five-year cumulative default rates by rating | Moody's long-term average | 1970–2012 | Table 8.1, p. 295 |
| Long-term average spread per rating | Bloomberg Barclays US Corporate and US High Yield index components by rating, extended back to 1970 with unstated "approximations and adjustments". The eight months Sep 2008–Apr 2009 are dropped from the average. | 1970–2012 | note 6, p. 328 |
| Term structure of spreads | US Corporate index, average spread per rating in three maturity buckets (1–3y, 3–7y, 7–10y). Median ratio of short to medium and long to medium spread, applied to the 5y long-term level. | May 1993–Nov 2013 | note 15, p. 330 |
| Spread vs. default study | Beginning-of-year spread of the Bloomberg Barclays HY and Corporate indices. Moody's cumulative issuer-weighted default rates by annual cohort (Ou et al. 2013, Exhibit 41), IG and HY summary. | cohorts 1991–2012 | pp. 311–312, note 16 p. 330 |
| Spread vs. downgrade study | Issuer-level data from Bloomberg Barclays Corporate and HY index bonds. Issuer spread = market-value-weighted average of its bonds each month. Annual cohorts by rating. Downgrade = move to a lower full-letter rating. 2009 cohort excluded. | 1991–2013 | pp. 313–315, notes 17–19 p. 330 |
| Spread persistence study | Same bonds revisited n years later. Average spread per whole-letter rating at start and end. January cohorts. Observations dated January 2009 dropped. | 1991–2013, n = 1..5 | p. 316, note 20 p. 330 |
| Fallen angel forced-sale penalty | 78bp, from Chapter 2 of the book | — | p. 297 |

Exclusions: 2009 cohort for downgrade and spread studies, because spreads were high from illiquidity, not default risk (pp. 313–315, note 19). Single bond, not a portfolio (p. 327, note 2 p. 328).

### Definitions and formulas

**Rating states.** Moody's letter grades: Aaa, Aa, A, Baa, Ba, B, Caa, Ca-C, Default (Table 8.2, p. 298). Default is absorbing.

**Sell discipline (threshold `τ`).** Three policies (Table 8.4, p. 302):
- Sell at Ba: sell on any downgrade to Ba or lower.
- Sell at B: sell on any downgrade to B or lower.
- Hold to default: never sell. Hold to maturity or default.

**Pure buy-and-hold expected return (Table 8.1, p. 295).**

```latex
EL_5 = PD_5 \times (1 - R), \quad R = 0.40
\qquad \overline{EL} = EL_5 / 5
\qquad E[r] = \bar S - \overline{EL}
```

Intuition: the spread pays for expected default loss, and the rest is expected excess return.

**Loss on forced sale (pp. 296–297, Table 8.2 p. 298, note 7 p. 329).**

```latex
L(q_0 \to q, k) = -\min\Big(0.60,\; D_k \cdot \big[\bar S_q - \bar S_{q_0} + \pi_{FA}\,\mathbb{1}\{q_0 \in IG,\; q \in HY\}\big]\Big)
```

Intuition: a downgrade marks the bond from its book spread to the average spread of its new rating, times the spread duration still left.

- `S̄_q`: long-term average spread of rating `q`. Values (bp): Aaa 68, Aa 79, A 110, Baa 162, Ba 309, B 463, Caa 839, Ca-C 1863 (Table 8.2, p. 298).
- `q_0`: rating at purchase. The book uses the "book spread at which the bond was purchased" (p. 296). In the base model the book spread equals `S̄_{q_0}`.
- `π_FA` = 78bp. It applies only when the bond crosses from IG to HY and is sold at once (p. 297). Note 11 (p. 329): if the bond goes Baa→Ba in one year and Ba→B in the next, a sell-at-B investor sells at fair value and pays no penalty. The Table 8.4 note (p. 303) says the penalty applies "upon any direct downgrade from IG to HY".
- `D_k`: spread duration at the sale. One-year example: 4.5 for a bond that starts with duration 5, sold at an unknown time in the year (p. 297). Table 8.3 (p. 300) implies `D_k = 5.5 − k` for k = 1..5 (4.5, 3.5, 2.5, 1.5, 0.5). Check: Baa→Ba loss = 225bp × 3.5 = 7.88% in year 2, as printed.
- Loss cap 60% = 1 − recovery (note 7, p. 329). Default loss = 60%.

Worked row, Baa bond, one year (Table 8.2, p. 298):

| | Aaa | Aa | A | Baa | Ba | B | Caa | Ca-C | Default |
|---|---|---|---|---|---|---|---|---|---|
| Avg spread (bp) | 68 | 79 | 110 | 162 | 309 | 463 | 839 | 1863 | |
| Spread change from Baa (bp) | −94 | −83 | −53 | 0 | 147 | 300 | 677 | 1701 | |
| Fallen angel penalty (bp) | | | | | 78 | 78 | 78 | 78 | |
| P/L upon liquidation | 4.24% | 3.75% | 2.37% | 0.00% | −10.13% | −17.03% | −33.96% | −60.00% | −60.00% |
| Transition probability | 0.04% | 0.18% | 4.36% | 89.95% | 4.30% | 0.80% | 0.17% | 0.02% | 0.18% |
| Expected loss (sell at Ba) | | | | | −0.44% | −0.14% | −0.06% | −0.01% | −0.11% |

The book records expected loss only for events that trigger a sale (p. 297). Upgrade P/L is shown but does not enter the loss.

**Multi-year chaining (pp. 299–300).** Apply the one-year matrix once per year, not a five-year matrix. Three reasons the book gives: a downgrade then later default counts as a sale, not a default; the sale loss needs the duration at sale time; each year can use a different matrix. Note 9 (p. 329): the one-year matrix to the fifth power does not equal the historical five-year matrix.

**Carry.** Spread carry is the return source. "Cumulative expected carry return includes an adjustment for lost carry due to expected forced sales and defaults" (Table 8.4 note, p. 303). Example: Baa hold to default carry 807bp, against 5 × 162 = 810bp. The book gives no carry formula. Our reading: carry accrues at the book spread for each year the bond is held, at the reinvestment spread after a reinvestment, and is zero after a default until reinvestment at the start of the next year.

**Reinvestment (pp. 300–301).** After a sale or default, invest the proceeds in a new bond of the original rating with the same remaining maturity. Example: a five-year Baa sold after three years goes into a Baa with two years left. Losses compound: two defaults leave 0.4 × 0.4 = 16 cents per dollar (p. 301).

**Output measures (p. 304, Table 8.4 note p. 303).**
- Cumulative probability of forced sale: technically the expected count of forced sales over the horizon (note 10, p. 329).
- Expected losses, split into forced sales and defaults.
- Carry and total expected return = carry + losses.
- Volatility: standard deviation of the five-year cumulative excess return.
- VaR 98%: the five-year cumulative return the bond exceeds with 98% probability (2nd percentile).
- CVaR 98%: mean return across the worst 2% of outcomes.

The book computes tail statistics by simulation (p. 301). It gives no path count and no random seed.

**Conditioned (enhanced) model (pp. 321–325, notes 22–23 p. 330).**

Spread-state ratio per rating row `q`:

```latex
m_{q,0} = \frac{S_q^{\text{now}}}{\bar S_q}
```

Intuition: the market spread level relative to its long-run average says how stressed the next year is.

The book states a one-year half-life for spread mean reversion (note 22, p. 330). It prints no formula. Our reading, which reproduces Figure 8.16:

```latex
m_{q,t} = m_{q,0}^{\,0.5^{\,t-1}}, \quad t = 1, \dots, 5
\qquad S_{q,t} = \bar S_q \cdot m_{q,t}
```

Intuition: the state fades by half each year. Check against Figure 8.16 (p. 323) with `m_0 = 2`: 200%, 141%, 119%, 109%, 104%. The formula gives 2.00, 1.41, 1.19, 1.09, 1.04. The book does not state whether the spread path is `S̄·m_{q,t}` at the year start or a mid-year value. Our reading: start of year t.

Matrix perturbation (p. 321, p. 323, Figure 8.15 p. 322):

```latex
P'_{ij}(t) = \begin{cases}
m_{i,t}\, P_{ij} & j \text{ worse than } i \text{ (incl. default)} \\
P_{ij} / m_{i,t} & j \text{ better than } i \\
1 - \sum_{j \ne i} P'_{ij}(t) & j = i
\end{cases}
```

Intuition: one scalar raises every downgrade, its reciprocal cuts every upgrade, and the diagonal absorbs the rest so the row sums to 100%.

- Figure 8.15 uses a uniform scalar 2 and upgrade scalar 0.5 on a four-bucket matrix (Aaa-Aa, A-Baa, Ba-B, Caa-D). Long-term row A-Baa: 1.50, 95.40, 2.90, 0.24. Perturbed: 0.75, 92.97, 5.80, 0.48 (p. 322).
- In the full model each row has its own scalar `m_{i,t}` equal to the spread ratio of rating `i` (note 23, p. 330).
- Table 8.6 (p. 319) supports the scale: in the "high" downgrade state, downgrade frequency is about 2× long-term and spreads about 2× long-term.
- Guard (ours, the book is silent): if `m > 1` pushes the diagonal below 0, cap `m` so that `P'_ii ≥ 0`.

Wider rating spread gaps under stress are captured because each rating spread scales by its own ratio. Empirical support (pp. 320–321):

```latex
\text{Baa} - \text{A} = 0.22\, S_A + 0.30 \;(\%),\; R^2 = 0.36
\qquad \text{Ba} - \text{Baa} = 0.57\, S_{Baa} + 0.73 \;(\%),\; R^2 = 0.59
```

Intuition: when spreads double, the loss on a one-letter downgrade grows too.

**Empirical downgrade regressions (Figures 8.9–8.10, p. 314).** One-year full-letter downgrade frequency `DG` against beginning-of-year issuer OAS in %:

```latex
DG_A = 0.049\, OAS + 0.014,\; R^2 = 0.312 \qquad DG_{Baa} = 0.022\, OAS + 0.018,\; R^2 = 0.128
```

**Cohort rule for year-n downgrade rates (p. 315).** Year-2 rate uses only issuers rated Baa at the start of both year 1 and year 2 and with a non-missing rating at the end of year 3 (the text says "year three"). Repeat for years 3–5. Correlate each year-n rate with the spread at cohort formation.

**High/low state matrices (p. 317, Table 8.5 p. 318).** Sort years 1991–2013 by overall one-year downgrade probability. Top quartile = "high": 1999, 2001–2003, 2008–2009. Bottom quartile = "low": 1993–1994, 1996–1997, 2010, 2013. Pool issuer transitions within each set into one matrix.

### Implementation steps

Base try-and-hold model (single bond, long-term averages):

1. Load the one-year Moody's letter matrix 1970–2012 (Ou et al. 2013, Exhibit 26). Drop the "withdrawn" column and prorate each row to 100%.
2. Set `S̄_q` per rating from Table 8.2. Set `π_FA` = 78bp, recovery 40%, loss cap 60%.
3. Choose bond: initial rating `q_0`, maturity `M` = 5 years, horizon `H` = 5 years. Choose the threshold `τ` ∈ {Ba, B, none}.
4. For each simulated path, for year k = 1..H:
   1. Draw the end-of-year rating from row `q_{k−1}` of the year-k matrix.
   2. If the new rating is Default: book −60% on current capital. Set capital ×0.4.
   3. Else if the new rating is at or below `τ`: book `L(q_0 → q, k)` with `D_k = (M_rem) − 0.5`. Add `π_FA` only if this year's move crosses IG→HY. Multiply capital by (1 + L).
   4. Else: hold. Add carry for the year at the book spread.
   5. After a sale or default: reinvest at year end in a new bond rated `q_0` with the same remaining maturity. Reset `q` to `q_0` and the book spread to `S̄_{q_0}` (or `S_{q_0,k+1}` in the conditioned model).
5. Cumulative excess return per path = total carry + total losses, in bp of initial capital. Our reading: carry on reduced capital after a loss scales with that capital.
6. Across paths: report expected count of forced sales, P(default), expected losses by type, carry, total, standard deviation, 2nd percentile (VaR 98%) and the mean below it (CVaR 98%).
7. Closed-form check without simulation: compute first-passage probabilities per year (Table 8.3, p. 300). For Baa sell-at-Ba: Ba 4.30, 4.09, 3.92, 3.76, 3.63% in years 1–5. A simulation must reproduce Table 8.3 within Monte Carlo error.

Conditioned model:

8. Input current spread per rating `S_q^now` and long-term `S̄_q`. Compute `m_{q,0}`.
9. For year t, build `P'(t)` row by row with `m_{i,t} = m_{i,0}^{0.5^{t−1}}`. Set spreads `S_{q,t} = S̄_q · m_{q,t}`.
10. Use `S_{q,t}` for the sale loss in year t, for carry on reinvested bonds, and for the purchase book spread. Our reading: the loss on sale uses `S_{q,t} − S_{book}` where `S_book = S_{q_0}^{now}` for the original bond.
11. Rerun steps 4–6.

Maturity variant: vary `M` from 1 to 10 years with a flat spread curve (Figure 8.5, p. 308). Then use rating spreads by maturity, A: 81/110/119bp and Baa: 131/162/169bp for 2/5/10 years (p. 309, Figure 8.6).

### Results

Table 8.1 (p. 295), pure buy-and-hold, five-year horizon:

| Rating | Spread | 5y PD | Recovery | 5y EL | Annual EL | Annual exp. excess return |
|---|---|---|---|---|---|---|
| A | 1.10% | 0.87% | 40% | 0.52% | 0.10% | 0.99% |
| Baa | 1.62% | 1.88% | 40% | 1.13% | 0.23% | 1.40% |
| Ba | 3.09% | 10.19% | 40% | 6.11% | 1.22% | 1.87% |

Table 8.3 (p. 300), five-year Baa bond, sell at Ba. First-event probability and loss by year:

| Year | P(Ba) | P(B) | P(Default) | Loss Ba | Loss B | Loss Default |
|---|---|---|---|---|---|---|
| 1 | 4.30% | 0.80% | 0.18% | −10.13% | −17.03% | −60% |
| 2 | 4.09% | 0.76% | 0.18% | −7.88% | −13.24% | −60% |
| 3 | 3.92% | 0.73% | 0.17% | −5.63% | −9.46% | −60% |
| 4 | 3.76% | 0.70% | 0.16% | −3.38% | −5.68% | −60% |
| 5 | 3.63% | 0.68% | 0.16% | −1.13% | −1.89% | −60% |

Table 8.4 (pp. 302–303), five-year bond, five-year horizon, long-term averages. Columns: long-term spread; cumulative probability of forced sale and default (%); cumulative expected loss from forced sales and defaults (bp); carry and total expected return (bp); volatility, VaR 98%, CVaR 98% (bp).

| Policy | Rating | Spread | P(sale) | P(dflt) | EL sale | EL dflt | Carry | Total | Vol | VaR98 | CVaR98 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Sell at Ba | Aaa | 68 | 0.4 | 0.1 | −3 | −3 | 340 | 335 | 146 | 341 | 53 |
| | Aa | 79 | 1.4 | 0.2 | −9 | −13 | 394 | 373 | 297 | 395 | −723 |
| | A | 110 | 5.6 | 0.3 | −42 | −18 | 544 | 483 | 424 | −510 | −1,724 |
| | Baa | 162 | 23.7 | 0.8 | −165 | −47 | 782 | 570 | 728 | −1,083 | −3,364 |
| Sell at B | Aaa | 68 | 0.1 | 0.1 | −1 | −3 | 341 | 336 | 143 | 341 | 116 |
| | Aa | 79 | 0.4 | 0.2 | −4 | −13 | 395 | 378 | 301 | 395 | −482 |
| | A | 110 | 1.8 | 0.4 | −20 | −22 | 546 | 505 | 426 | 278 | −1,610 |
| | Baa | 162 | 7.2 | 1.1 | −72 | −66 | 800 | 662 | 753 | −1,083 | −3,937 |
| Hold to default | Aaa | 68 | 0.0 | 0.1 | 0 | −4 | 341 | 337 | 148 | 341 | 159 |
| | Aa | 79 | 0.0 | 0.3 | 0 | −15 | 395 | 380 | 310 | 395 | −379 |
| | A | 110 | 0.0 | 0.6 | 0 | −39 | 548 | 509 | 493 | 548 | −1,427 |
| | Baa | 162 | 0.0 | 1.9 | 0 | −114 | 807 | 693 | 853 | 811 | −5,117 |

Key statements:
- Baa sell-at-Ba → sell-at-B: forced-sale loss falls 165 → 72bp, return rises 570 → 662bp (p. 304).
- Baa expected-return advantage over A: 36% (hold), 31% (sell at B), 18% (sell at Ba), against a 47% spread advantage (pp. 305–306).
- Sell at B gives the best return per unit of risk for A and Baa (Figure 8.4, p. 307).
- Longer maturity raises expected loss. With sell at Ba and a flat curve, A beats Baa at long maturities (pp. 308–309). With the term structure, 2y→5y helps in all four cases. 5y→10y helps only A sell-at-B (p. 310).

Predictive power of spreads:
- Correlation of beginning-of-year spread with realized default rate: year 1 HY 0.84, IG 0.63. Year 2 HY 0.12, IG 0.18. Negative from year 3 (p. 312).
- Correlation of beginning spread with one-year downgrade rate: A 56%, Baa 36% (p. 315). Figure 8.11 (p. 315) chart read, approximate: A falls from about 56% (y1) to about 50% (y2), about 22% (y3), then negative. Baa from about 36% to about 26%, about 0% (y3), then negative.
- Spread persistence: positive correlation at 1–2 years, negative by year 3 (Figure 8.12, p. 316). Chart values near 50% at year 1.
- Same-spread cohorts vary a lot: A-rated at 140–160bp had downgrade rates from 2.48% (2010) to 20.90% (2003) (p. 313).
- 2009 outlier: A spread 488bp, Baa 698bp, downgrade rate A 14.61%, Baa 5.29% (p. 313).
- Spread mean reversion half-life: 0.7–1.0 years industrials and 1.5–4 years utilities (Longstaff–Schwartz 1995), 1–2 years in the authors' own study (note 21, p. 330).

Table 8.5 (p. 318), one-year empirical matrices from index issuers, rows = start rating, columns Aaa, Aa, A, Baa, Ba, B, Caa, Ca-C (%). No default column is printed.

| State | From | Aaa | Aa | A | Baa | Ba | B | Caa | Ca-C |
|---|---|---|---|---|---|---|---|---|---|
| Low | Aaa | 98.4 | 0.8 | 0.8 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| | Aa | 0.0 | 92.6 | 7.2 | 0.2 | 0.0 | 0.0 | 0.0 | 0.0 |
| | A | 0.1 | 1.4 | 94.5 | 3.7 | 0.3 | 0.1 | 0.0 | 0.0 |
| | Baa | 0.1 | 0.1 | 5.8 | 91.4 | 2.4 | 0.1 | 0.1 | 0.0 |
| Medium | Aaa | 90.0 | 10.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| | Aa | 0.4 | 88.3 | 11.0 | 0.2 | 0.0 | 0.0 | 0.0 | 0.0 |
| | A | 0.0 | 3.3 | 90.8 | 5.5 | 0.3 | 0.1 | 0.0 | 0.0 |
| | Baa | 0.0 | 0.2 | 5.5 | 89.6 | 3.9 | 0.6 | 0.1 | 0.0 |
| High | Aaa | 88.0 | 12.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| | Aa | 0.8 | 72.2 | 25.6 | 1.1 | 0.3 | 0.0 | 0.0 | 0.0 |
| | A | 0.2 | 2.0 | 84.7 | 11.7 | 1.0 | 0.2 | 0.1 | 0.0 |
| | Baa | 0.1 | 0.0 | 2.8 | 87.1 | 7.8 | 1.5 | 0.6 | 0.0 |
| Moody's 1970–2012 | Aaa | 90.8 | 8.5 | 0.7 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| | Aa | 1.0 | 89.5 | 8.9 | 0.5 | 0.1 | 0.0 | 0.0 | 0.0 |
| | A | 0.1 | 2.6 | 90.7 | 5.8 | 0.6 | 0.1 | 0.0 | 0.0 |
| | Baa | 0.0 | 0.2 | 4.4 | 90.0 | 4.3 | 0.8 | 0.2 | 0.0 |

Table 8.6 (p. 319), ratios to long-term averages:

| | Low A | Low Baa | Med A | Med Baa | High A | High Baa | Moody's LT A | Moody's LT Baa |
|---|---|---|---|---|---|---|---|---|
| Downgrade freq. | 4.1% | 2.6% | 5.8% | 4.6% | 13.0% | 9.9% | 6.59% | 5.47% |
| Avg BoY OAS (%) | 1.10 | 1.74 | 1.20 | 1.66 | 2.42 | 3.26 | 1.10 | 1.62 |
| Downgrade / LT | 0.62 | 0.48 | 0.89 | 0.84 | 1.98 | 1.82 | | |
| OAS / LT | 1.00 | 1.07 | 1.09 | 1.02 | 2.20 | 2.01 | | |

Conditioned model results, chart reads only (Figures 8.17–8.18, pp. 324–325):
- Low spread, 31 Jan 2007: all six points have expected five-year returns of about 280–370bp and risk of about 330–700bp. Baa beats A on return under every policy.
- High spread, 30 Nov 2011: expected returns about 1,000–1,250bp. The text gives A-rated debt about 1,200bp with risk "about 600 to 700bp" (p. 326). The chart places the A points nearer 450–520bp of risk. We cannot settle this from the page. Baa sell-at-Ba sits near 1,000bp, well below A. The book says to avoid Baa under sell at Ba in a high-spread environment (p. 326).
- Sell at B gives the best return per unit of risk in both environments (p. 325).

### Robustness and variants

- Three sell disciplines (Table 8.4).
- Four starting ratings, Aaa to Baa (Table 8.4). Ba is in Table 8.1 only.
- Maturity 1–10 years with a flat curve (Figure 8.5) and with a term structure (Figure 8.6).
- Risk metric: standard deviation against VaR and CVaR at 98%. With CVaR as the metric, A would look better still (note 14, p. 329). For A bonds, the tail measures mix default and smaller losses (note 13).
- Conditioning: uniform scalar (Figure 8.15) and per-row scalar (note 23).
- Two spread environments, Jan 2007 and Nov 2011.

What holds: sell at B beats sell at Ba on return per unit of risk in every case shown. The Baa penalty under sell at Ba grows with maturity and with spread level.

### Limits and caveats

- IG-only evidence. All worked bonds are Aaa to Baa. The fallen-angel penalty (78bp) is an IG→HY result. The book finds no similar penalty for Ba→B (note 11, p. 329).
- Single bond. The book does not model a portfolio or correlation of defaults (p. 327).
- Spread paths are expectations only. The model has no random spread shocks, so it misses a systemic widening that would raise downgrade rates in later years (p. 327).
- Fixed 40% recovery (note 4, p. 328).
- Ratings-based: one-notch A3→Baa1 counts as a downgrade, two-notch A1→A3 does not (note 17).
- Each correlation in the predictive study rests on about 22 annual points. In-sample only.
- Long-term spreads use unstated back-fill adjustments to 1970 (note 6).
- Data is Barclays proprietary (index OAS by rating, issuer-level index transitions). The Moody's matrix is published in a public Moody's study.
- No transaction costs other than the fallen-angel penalty. No path count or seed for the simulation.

### Implementation in this repo

**Mapping.**
- Methodology §8 S6 (rating migration and forced flows): the forced-sale loss `L` and `π_FA` give the size of the flow effect. The sell threshold sets who must sell.
- §6 (recovery): loss on default 60% is the book's constant. Our `hy/recovery.py` gives a bond-level recovery. Use ours in place of 40%.
- §9 (event risk): a rating downgrade is an event with probability from the conditioned matrix and P&L `L(q_0 → q, k)`. Add it to `hy/events.py` as an event type with `outcome_probabilities` from `P'(1)`.
- §11 and the goal "PD calibrated by rating and by cycle phase": the conditioned matrix is a PD by rating and spread state. `hy/calibration.py` holds the calibration tools.
- New code: a module function `transition_path(P, m0, half_life=1.0, years=5)` and `try_and_hold_mc(...)`. Our proposal: put them in `hy/forward.py` (§5, forward), because they project the rating path. The decision is open.

**Data we have.**
- S&P issuer rating `splticrm` from `comp.adsprate`, monthly, 1,732 gvkeys, January 2007 to February 2017, with `available_at` (`data/raw/backtest/sp_ratings.parquet`, see `docs/decisions/2026-10-22-esp-peer-groups.md`). No rating feed after February 2017.
- TRACE G-spread and `mod_dur` per bond per month (`hy/sources/trace_panel.py`).
- CRSP equity, Compustat point-in-time.

**Data we lack.**
- Barclays index OAS by rating. Proxy: monthly median G-spread of TRACE bonds per S&P letter rating, weighted by `par_volume` (we lack amount outstanding).
- Long-term average spread per rating 1970–2012. Proxy: the book's Table 8.2 values as a fixed prior, plus our own TRACE medians 2007–2017. Do not mix the two in one ratio without a test.
- Full Moody's matrix with default column. Source: Ou et al. (2013), Exhibit 26, a Moody's report. We hold only the Baa row (Table 8.2) and the IG rows without default (Table 8.5). Alternative: S&P annual default and transition study tables. Our own empirical matrix from `adsprate` 2007–2017 (about 10 annual cohorts).
- HY rows. Our universe is HY. The book's evidence covers IG rows. The scalar rule is untested for B and CCC rows.

**Lag rule (as_of, available_at).**
- Rating at month t: use the stored `available_at`. A transition counts only after the new rating's `available_at`.
- Spread state `m_{q,0}` at decision date d: medians from trades with `available_at` ≤ d (last trade + 1 day).
- Long-term averages `S̄_q`: compute from data with `available_at` ≤ d only (expanding window). The book's 1970–2012 values carry `available_at` = 2013-02-28 (Ou et al. 2013 date, p. 328). Before that date, flag any use as look-ahead.
- Outcome of a one-year cohort formed at d: `available_at` = d + 12 months + the rating lag. Use `hy/calibration.outcome_available_at`.

**Falsifiable tests.**
1. Spread-conditioned transitions (main test).
   - Signal: per issuer-month, `m = G-spread median of its rating bucket / expanding long-run median of that bucket`. Predict the 12-month full-letter downgrade probability with `P'` against the unconditional `P` from the same expanding window.
   - Data: `adsprate` 2007-01 to 2016-02 cohorts (outcome by 2017-02).
   - Metric: out-of-sample log loss of the downgrade event, by rating (BBB, BB, B).
   - Pass: `P'` lowers log loss in BB and B rows, and a Diebold–Mariano test (`hy/calibration.dm_test`, HAC lags 12) gives t ≥ 2. The window covers only the 2008 and 2015 cycles. Report this as two of four cycles, not three.
2. Mean-reversion half-life.
   - Signal: monthly log G-spread per rating bucket, TRACE 2010–2026.
   - Metric: half-life from the regression of Δ log spread on lagged log spread (note 21).
   - Pass: half-life between 0.5 and 2 years in each HY bucket. If it fails, replace the 1-year half-life with the fitted value.
3. Forced-sale penalty in HY.
   - Signal: bonds downgraded BB→B and B→CCC in `adsprate` 2007–2017.
   - Metric: G-spread change relative to same-rating peers from month −1 to month +3, and from +3 to +12.
   - Pass: a widening of at least 25bp at +3 that reverts by at least half by +12, with t ≥ 2. The book reports no such effect for Ba→B (note 11), so the default expectation is a fail. A fail means no `π_FA` term inside HY.

---

## Chapter 9. Effect of Rating-Based Stop-Loss Rules on Performance (PDF pp. 331–355)

Note on page range. The chapter text ends on PDF p. 355. PDF pp. 356–360 hold a blank page, the Part Three introduction (pp. 357–359) and a part-title image (p. 360). The Part Three introduction summarises Chapters 10–12 and is used in those files.

**Question.** Does a rule that sells bonds downgraded to or below a rating threshold improve the return and risk of a diversified credit portfolio?

**Answer.** No. Every stop-loss rule tested cuts average excess return in USD, EUR and GBP portfolios, and the percentage cut in return is much larger than the percentage cut in volatility or drawdown (PDF pp. 336–337, 350). Downgraded bonds also beat the bonds already in their new rating bucket, which adds to the cost of the forced sale (PDF pp. 346, 350).

### Data

What the book says:
- Universe, USD. Union of the Bloomberg Barclays US Corporate (IG) and US High Yield indices (PDF p. 332).
- Universe, EUR and GBP. Euro and sterling corporate indices. These indices start in 1999 (PDF p. 347).
- Period, USD. Portfolios start in December 1992. Returns run January 1993 to January 2015 (Table 9.2, PDF p. 335). Table 9.6 runs March 1993 to January 2015 (PDF p. 346). Spread averages in Table 9.1 run January 1994 to January 2015 (PDF p. 333).
- Period, EUR. Inception December 1998. Returns January 1999 to January 2015 (Table 9.7, PDF p. 348).
- Period, GBP. Inception August 1999. Returns September 1999 to January 2015 (Table 9.8, PDF p. 349).
- Frequency. Monthly. Portfolios rebalance every month end (PDF p. 332).
- Ratings. Index ratings in Moody's letter scale: Aaa, Aa, A (A1, A2, A3), Baa, Ba, B, Caa (PDF p. 332, note 6 p. 355). Transition rates come from Moody's one-year transition frequencies, 1970–2014 (Table 9.1, PDF p. 333).
- Weights. Market capitalisation (PDF p. 332).
- Other index rules (for example, removal below one year to maturity) apply equally to the stop-loss portfolio and to its benchmark. The authors state that these rules do not change the result (note 5, PDF p. 355).
- Source of all portfolio tables: Barclays Research (index data is proprietary).

### Definitions and formulas

**Rating buckets.** Aaa–Aa, A, Baa, Ba, B, Caa. A "Caa" sell threshold means sell at Caa1 or below (note 7, PDF p. 355).

**Buy rule.** At each month end, the portfolio buys every index bond whose rating is inside the buy range (PDF p. 332). Two buy-range families:
- Single bucket: Aaa–Aa, A, Baa, Ba, B, Caa (left panels of the tables).
- Cumulative range: Aaa–Aa, Aaa–A, Aaa–Baa, Aaa–Ba, Aaa–B, Aaa–Caa (right panels). Aaa–Baa with a Ba sell rule is the standard IG index (PDF p. 336).

**Sell rule (stop loss).** At each month end, sell any held bond rated at or below the sell threshold `SL ∈ {A, Baa, Ba, B, Caa}`. The threshold is always below the buy range. Upgraded bonds stay (note 8, PDF p. 355).

**Buy and hold (BH) benchmark.** Same buy rule. No sell rule. Bonds stay until default or maturity (PDF p. 334).

**Excess return.** Return in excess of duration-matched Treasuries (PDF p. 334).

**Incremental effect.** The tables report the stop-loss portfolio statistic minus the BH statistic, in bp/year (PDF pp. 334, 336).

```latex
\Delta R(b, SL) = \bar{R}^{xs}_{b,SL} - \bar{R}^{xs}_{b,BH}, \qquad
\Delta\sigma(b, SL) = \sigma_{b,SL} - \sigma_{b,BH}, \qquad
\Delta MDD(b, SL) = MDD_{b,SL} - MDD_{b,BH}
```
Intuition: the cost of the rule is the gap to the same portfolio with no forced sale.

**Back-of-envelope cost (introduction, PDF p. 332).**
```latex
\text{Loss given downgrade} \approx D \times (S_{\text{new bucket}} - S_{\text{old bucket}}), \qquad
\text{Annual cost} \approx p_{DG} \times D \times (S_{\text{new}} - S_{\text{old}})
```
Intuition: sell at the wider spread of the new bucket, times the chance of a downgrade per year. Example: 5.5 × (126 − 92) = 187 bp per event, times 9.6% = about 18 bp/year (PDF p. 332). The book ignores carry here (note 3, PDF p. 354). It uses the average spread of the A bucket for all lower ratings, on the assumption that an Aa bond passes A first (note 4, PDF p. 354).

**Decomposition with covariance (PDF pp. 343–344).**
```latex
E[\text{Loss}] = E[f_{DG} \times L_{DG}] = E[f_{DG}]\,E[L_{DG}] + \mathrm{Cov}(f_{DG}, L_{DG}),
\qquad L_{DG} = D \times \Delta S_{gap}
\qquad \mathrm{Cov} = \rho \, \sigma_{f} \, \sigma_{L}
```
Intuition: downgrades cluster when spread gaps are wide, so the cost is larger than the product of the averages.
- `f_DG`: rolling 12-month downgrade frequency of the Aaa–Aa portfolio.
- `ΔS_gap`: 12-month average of (spread of bonds downgraded from Aaa–Aa to A) minus (spread of Aaa–Aa bonds) (Figure 9.2, PDF p. 343).
- Inputs: D = 5.5 years, mean gap 50 bp, mean frequency 9.5%/year, ρ = 66%, σ_f = 7.6%/year, σ of gap = 48 bp (PDF pp. 343–344).
- First term 26 bp/year. Covariance term 13 bp/year. Total 39 bp/year against 41 bp/year observed (PDF p. 344).

**Appendix 9.1 single-bond model (PDF pp. 351, 353).** One Aa bond, spread S_L, duration D. Downgrade to A gives spread S_H > S_L. Annual downgrade probability p. No default.
```latex
R_{BH} = S_L, \qquad R_{SG} = S_L - pD(S_H - S_L)
\qquad \frac{R_{SG} - R_{BH}}{R_{BH}} = -pD\left(\frac{S_H}{S_L} - 1\right) \quad (1)
```
Intuition: the percentage return loss scales with duration D.
```latex
V_{SG} = [D S_L \sigma]^2, \qquad
V_{BH} = [D S_L \sigma]^2 \left\{1 + \left(\frac{S_H^2}{S_L^2} - 1\right)p\right\}
\qquad \frac{V_{SG}^{1/2} - V_{BH}^{1/2}}{V_{BH}^{1/2}} = \frac{1 - \sqrt{1 + \left(\frac{S_H^2}{S_L^2} - 1\right)p}}{\sqrt{1 + \left(\frac{S_H^2}{S_L^2} - 1\right)p}} \quad (2)
```
Intuition: volatility is DTS times σ (σ = volatility of relative spread changes). D cancels in the ratio, so the percentage risk cut does not scale with duration. The model assumes downgrade and relative spread change are independent, and constant duration (note 15, PDF p. 355). SG replaces the sold bond with a new Aa bond of the same characteristics.

**Quality-matched peer (PDF p. 346).** For each rule portfolio, build a peer that holds rating subindices. Replace each downgraded bond by the subindex of its new rating. Reset the bucket weights each month to match the rating mix of the rule portfolio that keeps downgraded bonds.

**DG portfolio (Table 9.6, PDF p. 346).** Bonds downgraded into a bucket from the bucket above (example: Aaa–Aa to A). Compared with the BH portfolio that bought into that bucket. The book does not state the holding period of the DG portfolio. Our reading: hold the downgraded bonds under the same BH rule (to maturity or default).

### Implementation steps

1. Load monthly index constituents with rating, market value, duration and excess return over duration-matched Treasuries.
2. Fix the inception month (USD December 1992, EUR December 1998, GBP August 1999).
3. For each buy range b and each rule r ∈ {BH, sell at Caa, B, Ba, Baa, A} (only thresholds below b):
   1. At each month end, add every index bond rated inside b and not yet held.
   2. Under rule r, remove every held bond rated at or below the threshold. Under BH, remove only at maturity or default.
   3. Keep upgraded bonds.
   4. Weight the holdings by market value.
4. Compute the next-month market-value-weighted excess return of each portfolio.
5. Report per portfolio: average excess return (bp/year), volatility (bp/year), maximum drawdown (bp), information ratio = mean ÷ volatility.
6. Report each rule as the difference to BH of the same buy range.
7. Split by sector (financial vs. nonfinancial, Table 9.3) and by inception (December 1992 and December 2004, Table 9.4).
8. Build quality-matched peers (Table 9.5) and DG portfolios (Table 9.6).
9. Repeat with maturity 1–5 years only (Table 9.9) and express changes in percent of BH.
10. Repeat steps 2–6 for EUR and GBP (Tables 9.7, 9.8).

No transaction costs enter any table. The book states none.

Path dependence (PDF p. 340). The holdings depend on the inception date, except for these six portfolios: Aaa–Aa sell at A, Aaa–A sell at Baa, Aaa–Baa sell at Ba, Aaa–Ba sell at B, Aaa–B sell at Caa, and BH Aaa–Caa.

### Results

All numbers are bp/year unless stated. Tables read from page images.

**Table 9.1 (PDF p. 333).** Average OAS January 1994 – January 2015: Aaa 71, Aa 92, A 126, Baa 183, Ba 350, B 515, Caa 913. Total one-year downgrade probability (Moody's 1970–2014): Aaa 9.2%, Aa 9.6%, A 6.6%, Baa 5.1%, Ba 9.8%, B 10.8%, Caa 13.5%. Default rate per year: Ba 1.11%, B 3.90%, Caa 13.46%.

**Table 9.2, USD, January 1993 – January 2015 (PDF p. 335).** BH level, then increments for sell at Caa / B / Ba / Baa / A.

| Buy bucket | BH return | Caa | B | Ba | Baa | A | BH vol | Δvol at nearest threshold | BH MDD (bp) |
|---|---|---|---|---|---|---|---|---|---|
| Aaa–Aa | 74 | −1 | −3 | −6 | −11 | −41 | 366 | −59 (A) | 1,825 |
| A | 66 | −4 | −7 | −13 | −22 | | 448 | −27 (Baa) | 2,542 |
| Baa | 116 | −13 | −22 | −39 | | | 538 | −48 (Ba) | 2,943 |
| Ba | 288 | −35 | −69 | | | | 805 | −99 (B) | 3,896 |
| B | 242 | −41 | | | | | 992 | −83 (Caa) | 4,424 |
| Caa | 275 | | | | | | 1,352 | | 5,595 |

Cumulative ranges, BH return then increments (Caa / B / Ba / Baa / A): Aaa–A 63 (−4, −7, −11, −19). Aaa–Baa 75 (−8, −12, −20). Aaa–Ba 89 (−9, −16). Aaa–B 91 (−8). Aaa–Caa 94. BH volatility: Aaa–A 418, Aaa–Baa 450, Aaa–Ba 470, Aaa–B 506, Aaa–Caa 520 (PDF p. 335).

Key statements:
- The IG index (Aaa–Baa sell at Ba) loses 20 bp/year against BH. Its volatility falls from 450 to 425. Its drawdown falls from 2,590 to 2,421 bp (PDF p. 336). Return falls 27%. Risk falls 5–7%.
- Aaa–Aa sell at A: return −41 (−56%), volatility −59 (−16%), drawdown −126 bp (−7%) (PDF p. 336).
- The A BH portfolio returns less than Aaa–Aa BH (66 vs. 74) because it held Lehman and Washington Mutual. The authors say the stop loss does not protect against jump to default (PDF p. 334).
- Over 10% of the A BH portfolio market value sits in Baa or below on average (Figure 9.1, PDF pp. 337–338).

**Table 9.3, financial vs. nonfinancial (PDF p. 339).** Aaa–Aa sell at A: financials −46, nonfinancials −16. A sell at Baa: financials −29, nonfinancials −9 (PDF p. 340). Financial Ba volatility falls from 1,501 to 1,104 (−26%) with a B threshold. Financial B volatility falls from 2,146 to 1,472 (−31%) with a Caa threshold (PDF p. 340). These portfolios were concentrated: in December 2005 the universe held 33 Ba and 18 B financial bonds (PDF p. 340).

**Table 9.4, subperiods (PDF p. 341).** Aaa–Aa sell at A: −4 in 1993–2004, −82 in 2005–2015. Baa sell at Ba: −38 and −34. A sell at Baa: −4 and −41.

**Figure 9.2 and decomposition (PDF pp. 343–344).** Peak loss given downgrade 12.5% (227 bp × 5.5 years) in 2008. Correlation of downgrade rate and spread gap 66%. Model 39 vs. actual 41.

**Table 9.5, quality-matched peers (PDF p. 345).** Peer minus rule portfolio, return: Aaa–Aa BH −24, sell at Caa −22, B −22, Ba −20, Baa −15. Aaa–A BH −12. Aaa–Baa BH −9. Aaa–Ba BH −8. Peers have slightly lower volatility. Drawdowns are similar (PDF p. 346).

**Table 9.6, downgraded bonds vs. BH (PDF p. 346).** Return, volatility, IR. BH: Aaa–Aa 74 / 366 / 0.20, A 66 / 448 / 0.15, Baa 116 / 538 / 0.22, Ba 288 / 805 / 0.36, B 242 / 992 / 0.24, Caa 275 / 1,352 / 0.20. DG: A 103 / 478 / 0.22, Baa 180 / 604 / 0.30, Ba 434 / 973 / 0.45, B 492 / 1,213 / 0.41, Caa 257 / 1,453 / 0.18. DG beats BH in every bucket except Caa.

**Table 9.7, EUR (PDF p. 348).** Baa sell at Ba −57 against BH 155 (−37%). Aaa–Baa sell at Ba −24 against 79 (−31%). Volatility 335 to 319 (−4.5%) (PDF p. 347). Aaa–Aa sell at A −47.

**Table 9.8, GBP (PDF p. 349).** A sell at Baa −91. Aaa–Baa sell at Ba −35 against 84. Holding to maturity would lift the IG index from 49 to 84 (+70%) (PDF p. 350). Sterling duration 7.6 years vs. 6 years for US (PDF p. 347).

**Table 9.9, duration test (PDF p. 352).** Percent change vs. BH. All maturities, Aaa–Aa sell at A: return −56%, volatility −16%. Maturity 1–5 years: return −33%, volatility −18%. Aaa–Baa sell at Ba: return −27% (all) vs. −12% (1–5y). Volatility −6% vs. −5%. Return cuts shrink with duration. Volatility cuts do not (PDF p. 354).

### Robustness and variants

- Sector split: the effect is larger for financials in high grades (PDF p. 340).
- Inception date and subperiod: the sign holds in both. The size in high grades comes mostly from 2008 (PDF p. 342).
- Maturity: shorter bonds lose less return in percent, as model (1) predicts (PDF p. 354).
- Markets: EUR and GBP give the same sign. GBP losses are largest, which the authors tie to longer duration (PDF p. 347).
- Threshold distance: the cost shrinks as the threshold moves away from the buy rating (PDF p. 334).

### Limits and caveats

- The study holds rule-based index portfolios, not a trading strategy. It gives no signal and no long-short return.
- No transaction costs. A real BH portfolio of downgraded bonds pays HY bid-ask spreads. A forced seller pays the fire-sale discount at the downgrade, which index pricing may not capture.
- Index data and index ratings are Barclays proprietary.
- The evidence for buy ranges in Ba, B and Caa is on HY subindices, so it applies to HY. But the main message targets IG mandates.
- Results stop in January 2015. The 2008 wave drives much of the high-grade effect.
- The appendix model is a one-bond toy. The authors say not to use it as a forecast (PDF p. 354).

### Implementation in this repo

What we decide.

**Mapping.** Methodology Section 8, S6 (rating migration and forced flows). The book gives the size of the forced-flow premium that S6 harvests: forced sellers sell downgraded bonds, and the bonds then beat their new peers (Table 9.6). Code goes in `hy/signals.py` (`migration_probabilities`, `flow_weight`, `s6_migration`). The cost decomposition belongs in `hy/events.py` (Section 9, event risk) as the expected loss from a downgrade event. Section 11 (backtest) owns the BH vs. stop-loss comparison.

**Data we have.** TRACE prices, G-spreads, modified duration (`hy/sources/trace_panel.py`). The panel keeps the TRACE master grade flag 'H' at each month end, point in time (rule 1 of `trace_panel.py`). That gives the IG to HY boundary only.

**Data we lack.** Agency letter ratings by month, rating history, amount outstanding, index membership.

**Proxy.**
1. Fallen-angel event: a CUSIP whose TRACE master grade changes from IG to 'H' between two month ends. This needs the IG rows of the master, which the panel now drops. Extend `trace_panel` to keep them for the event flag only.
2. Rating bucket inside HY: use the issuer spread bucket (G-spread tercile within the month) as a proxy for Ba / B / Caa. State it as a proxy.
3. Weight: equal weight or par-volume weight, since we lack amount outstanding.

**Lag rule.** A grade change is known at `available_at` of the first master version that carries it, plus 1 day. The portfolio acts at the next month end after that date. Never use the month-end in which the master version starts if `stdt` is after the trade window.

**Falsifiable test.**
- Signal: hold fallen angels (IG to HY in the TRACE master) for 12 months after the event month, versus HY bonds already in the panel with the same G-spread tercile and duration bucket.
- Horizon: 1, 6 and 12 months after `available_at`.
- Metric: mean monthly excess return over duration-matched Treasuries (G-spread basis), net of `bid_ask_pts / 2` at entry and exit, with Newey–West t-statistic.
- Pass: the 12-month net excess return of fallen angels beats the matched peers by more than 0 with t > 2 over 2008–2026, and the sign holds in at least three of the four cycle windows (2008, 2015, 2020, 2022). This tests the Table 9.6 claim on HY data with costs.

---

## Chapter 10. Coupon Effects in Corporate Bonds: Pricing, Empirical Duration, and Spread Convexity (PDF pp. 361–382)

Note on page range. The chapter text and notes end on PDF p. 381. PDF p. 382 is blank. The Part Three introduction on PDF p. 357 summarises this chapter.

**Question.** Inside one issuer, do premium (high-coupon) bonds trade wider, react differently to Treasury moves, and earn less than discount (low-coupon) bonds?

**Answer.** Yes. Since 2008 a 1% higher coupon adds about 10 bp of OAS inside the same issuer (PDF p. 366). Discount bonds show positive spread convexity against Treasury moves (Table 10.2, PDF p. 369). An issuer-matched long-discount, short-premium portfolio earns 3.5 bp/month with an annualised IR of 1.01 over 1992–2014, before costs, and earns most when credit risk is high (Tables 10.4, 10.7, PDF pp. 372, 377).

### Data

What the book says:
- Index. Bloomberg Barclays US Corporate (IG) bond index (PDF pp. 362, 367).
- Period. January 1992 to April 2014, monthly, 268 months (PDF pp. 365, 380 note 7).
- Pricing test and portfolio test: frequent issuers only. A frequent issuer has seven or more bonds outstanding in the month (PDF p. 365). These issuers are 11.7% of index issuers but 40.5% of eligible bonds on average. In April 2014, 158 of 1,040 issuers held 1,757 of 3,752 eligible bonds. The regressions average 105 issuers per month (note 7, PDF p. 380).
- Empirical duration test: all noncallable bonds in the IG index, 737,506 bond-months, of which 171,762 premium and 34,616 discount (note 8, PDF p. 380).
- Treasury yield change per bond: monthly change of the fitted constant-maturity yield. Use 5y for maturity below 7 years, 10y for 7 to 15 years, 30y for 15 years and above (note 10, PDF p. 380).
- Credit regime variable: Baa minus Aaa yield from Bloomberg Barclays US Credit indices. Each month, blend the Long (over 10 years) and Intermediate (below 10 years) Aaa Credit indices to match the OAD of the Baa Credit index. The premium is the Baa yield minus this blend yield (Figure 10.3 note, PDF p. 376).
- Example data (Table 10.1): four Verizon bonds, 28 April 2014, BCDS model of Pedersen (2006) with 40% recovery (note 6, PDF p. 380).
- Source: Bloomberg Barclays Indices, Barclays Research.

### Definitions and formulas

**Spread pricing (eq. 10.1, PDF p. 363).**
```latex
P = \sum_t \frac{CF_t}{\left(1 + \frac{r_t + s}{2}\right)^{2t}}
```
Intuition: one constant spread s over Treasuries prices all cash flows. It treats recovery as zero, so it ignores that recovery is paid on par.

**Bond-implied CDS (BCDS) spread (PDF p. 364).** Fit an issuer hazard curve to its CDS curve. Price the bond as expected cash flows (survive: coupon; default at t: recovery × par; after default: nothing), discounted on the Libor curve. Shift the hazard curve by a constant until model price equals market price. Read off the CDS spread at the bond's maturity. The book gives no closed formula. It points to Pedersen (2006).

**Premium measure (note 2, PDF p. 379).** The chapter uses three measures that agree for bonds of one issuer with similar maturity: dollar price, coupon, and coupon minus yield. The portfolio test uses coupon minus yield, because it does not bias the split toward long or short bonds (note 14, PDF p. 381).

**Coupon effect on spread, per month (PDF p. 366).** Pooled cross-section of frequent issuers, one regression per month:
```latex
OAS_{i,j} - \overline{OAS}_j = \alpha_j \left(sprdDur_{i,j} - \overline{sprdDur}_j\right) + \beta \left(Coupon_{i,j} - \overline{Coupon}_j\right) + \varepsilon_{i,j}
```
Intuition: α_j is the slope of issuer j's spread curve. β is the market-wide extra spread per 1% of coupon after that slope. Bars are issuer means in the month. Units: OAS in bp, coupon in percent. β = 0.1 means 10 bp per 1% coupon (PDF p. 366). The book does not state the weights. Our reading: OLS, equal weight per bond.

**Model 1, empirical duration (PDF p. 367).** Pooled over all bonds and months:
```latex
R^{adj}_{i,t} = -\beta_{treas} D_{i,t}\,\Delta y_t - \beta_{spread} D_{i,t} S_{i,t}\,\Delta y_t + \varepsilon_{i,t},
\qquad R^{adj}_{i,t} = TR_{i,t} - \tfrac{1}{12} y_{i,t-1}
```
Intuition: the hedge ratio D^emp ÷ D = β_treas + β_spread·S falls as spread rises. Carry adjustment uses the start-of-month yield, not the coupon, to avoid a coupon bias (note 9, PDF p. 380). D is analytical duration. S is spread. The book does not state the units of S in the regression. Our reading: S in percent (100 bp = 1.0), because 0.97 − 0.13 × 1.0 = 0.84, close to the 0.83 hedge ratio at 100 bp in Table 10.3.

**Model 2 (PDF pp. 368–369).**
```latex
\frac{D^{emp}_i}{D_i} = \beta_{treas} + \beta_{spread} S_i + \gamma^{k}_{g}\, PriceDistPar_i,
\qquad g \in \{prem, disc\},\ k \in \{up, dn\}
```
Intuition: bonds far from par get an extra hedge-ratio shift that depends on the side of par and on the sign of the yield change.
- Discount: price ≤ 90. Premium: price ≥ 110. Between 90 and 110, γ = 0 (PDF p. 368).
- PriceDistPar = |price − 100| ÷ 100. Our reading from Table 10.3, where price 110 gives "10%".
- k = up when Δy > 0, dn when Δy < 0.
- Our reading of the sign: with S = 1.0 and PriceDistPar = 0.10, discount on falling yields gives 0.98 − 0.15 + 1.67 × 0.10 = 0.997 ≈ 1.00, and discount on rising yields gives 0.83 − 0.109 = 0.72. Premium falling: 0.83 − 0.025 = 0.80. Premium rising: 0.83 + 0.027 = 0.86. These match Table 10.3 (PDF p. 370).

**Discount vs. premium portfolio (PDF pp. 371–372, notes 14–16 p. 381).** Defined in Implementation steps.

**Active return.**
```latex
R^{active}_t = R^{disc}_t - R^{prem}_t, \qquad IR = \frac{\overline{R^{active}}}{\sigma(R^{active})}\sqrt{12}
```
Intuition: long discounts, short premiums, issuer and duration matched.

### Implementation steps

Pricing test:
1. Each month, keep issuers with seven or more index bonds.
2. Run the cross-sectional regression above. Store β and its t-statistic. Plot the time series (Figure 10.2).

Empirical duration test:
3. Use all noncallable IG index bonds. Compute carry-adjusted monthly return. Pick the Treasury tenor by maturity (note 10).
4. Fit Model 1 by pooled OLS. Fit Model 2 with four γ terms. The note to Table 10.2 says pooled t-statistics are inflated. A monthly dummy leaves the coefficients little changed (PDF p. 369).

Portfolio test (bottom-up, issuer matched):
5. Each month, take frequent issuers (seven or more bonds).
6. Inside each issuer, rank bonds by coupon minus yield. Split into two equal groups. With an odd count, the middle bond goes to the premium group (note 15).
7. Inside each group, split the bonds into a long-duration cell and a short-duration cell. The book does not state the split rule. Our reading: split at the group median duration and value-weight within each cell.
8. Choose a target duration. Use the issuer's average duration when both groups can reach it with non-negative cell weights. Otherwise move the target into the range both groups can reach.
9. Reweight the two cells of each group to hit the target duration. If both cells of one group are longer than both cells of the other, drop the issuer for that month. This drops almost 33% of 28,198 issuer-months (PDF p. 372).
10. Issuer weight = issuer's total market value of included bonds ÷ total market value of all included bonds that month. Apply the same issuer weight to the discount and the premium portfolio (note 16).
11. Hold for one month. Rebalance monthly.
12. Compute total return and excess return (over duration-matched Treasuries) of each portfolio, and the active return.
13. Partition months by: 10y Treasury yield change quartile (Table 10.5), decile of the discount portfolio's excess return (Table 10.6, note 17), quartile of the Baa−Aaa premium (Table 10.7), quartile of the discount portfolio average price (Table 10.8).

No transaction costs are deducted.

### Results

**Table 10.1, Verizon, 28 April 2014 (PDF p. 364).** Coupon / price / ZV / BCDS / ZV at 163 BCDS: 6.4 / 118.97 / 174.3 / 162.0 / 175.3. 6.9 / 125.15 / 180.4 / 164.4 / 179.1. 7.35 / 130.27 / 190.5 / 170.4 / 182.8. 8.95 / 154.18 / 183.9 / 155.1 / 192.9. Repriced at one BCDS of 163 bp, ZV spread rises with coupon.

**Pricing regression (Figure 10.2, PDF pp. 366–367).** β about 0.1 since 2008, with strong t-statistics (the axis reaches about 30). β also spiked above 0.1 at the end of 2002 and decayed through 2003. Exact monthly values are only in the chart.

**Table 10.2 (PDF p. 369).** Model 1: β_treas 0.97 (t 405.0), β_spread −0.13 (t −144.1), adjusted R² 24%. Model 2: β_treas 0.98 (t 355.3), β_spread −0.15 (t −140.6), γ_prem^up 0.27 (t 14.6), γ_prem^dn −0.25 (t −11.8), γ_disc^up −1.09 (t −41.0), γ_disc^dn 1.67 (t 76.1), adjusted R² 25%.

**Table 10.3 (PDF p. 370).** Spread 100 bp. Premium (110): hedge ratio 0.83 (Model 1), 0.80 falling yields, 0.86 rising yields. Discount (90): 0.83, 1.00, 0.72.

**Table 10.4, January 1992 – April 2014 (PDF p. 372).**

| | Discount | Premium | Active |
|---|---|---|---|
| Total return, mean (bp/mo) | 57.1 | 53.7 | 3.5 |
| Total return, vol (bp/mo) | 151.1 | 149.5 | 12.0 |
| Total return, IR (ann.) | | | 1.01 |
| Excess return, mean (bp/mo) | 8.0 | 4.9 | 3.1 |
| Excess return, vol (bp/mo) | 119.74 | 118.31 | 11.8 |
| Excess return, IR (ann.) | | | 0.91 |
| OAS (bp) | 129.9 | 133.4 | |
| OAD | 5.25 | 5.25 | |
| Price | 100.59 | 107.91 | |
| Number of bonds | 382.9 | 424.7 | |

**Table 10.5, by 10y yield change (PDF p. 374).** Active total return (bp/mo) and IR: Q1 (< −19 bp) 5.8, 1.84. Q2 (−19 to −2) 4.9, 1.65. Q3 (−2 to 14) 0.8, 0.29. Q4 (> 14) 2.5, 0.56. Active excess return: 4.3, 4.5, 1.3, 2.4. Positive in all quartiles. Best when yields fall.

**Table 10.6, by excess-return decile (PDF p. 375).** Active excess return (bp/mo): decile 1 7.3, 2 6.1, 3 −1.3, 4 −1.2, 5 1.2, 6 0.0, 7 1.5, 8 1.1, 9 7.5, 10 9.1. Premium portfolio spread is 2.0–6.4 bp wider in every decile. Gains concentrate in the two tails.

**Table 10.7, by Baa−Aaa premium (PDF p. 377).** Active total return (bp/mo), vol, IR: Q1 (< 71 bp) 0.1, 3.2, 0.14. Q2 (71–106 bp) 0.1, 6.1, 0.03. Q3 (106–176 bp) 1.6, 9.2, 0.59. Q4 (> 176 bp) 12.2, 18.5, 2.28.

**Table 10.8, by discount portfolio price (PDF p. 378).** Discount price / premium price / active mean / vol / IR: Q1 98.0 / 105.4 / 6.5 / 14.7 / 1.53. Q2 101.3 / 112.7 / 3.4 / 8.5 / 1.39. Q3 103.4 / 114.0 / 3.0 / 12.8 / 0.82. Q4 108.4 / 120.5 / 1.0 / 10.6 / 0.34. The effect is largest when the discount bonds are furthest below par.

### Robustness and variants

- Top-down construction (reweight index cells) was tried and dropped. The authors could not control other exposures (PDF p. 371).
- Total vs. excess returns give similar active results (PDF p. 373).
- Rate direction: positive in all four yield-change quartiles (PDF p. 373).
- Credit direction: largest in both tails of market excess return (PDF p. 373).
- Rising-rate concern: the effect is largest when discount bonds sit lowest below par, so the authors expect it to hold when rates rise (PDF pp. 377–378).
- Pricing regression with a monthly dummy: coefficients little changed (Table 10.2 note).

### Limits and caveats

- IG only. No HY bonds in any test.
- Before costs. The authors say the effect may not justify a stand-alone strategy after costs. They suggest a long-only tilt toward low coupons instead (PDF p. 378).
- Index OAS, OAD and index returns are Barclays data. BCDS needs CDS curves.
- Frequent issuers only (seven or more bonds). One third of issuer-months fail the duration match.
- Sample has a falling-rate bias: average prices 100.6 (discount) vs. 107.9 (premium) (PDF p. 377).
- Pooled t-statistics are overstated (Table 10.2 note).
- The authors list other causes of the premium-bond discount, such as accounting aversion to premium bonds (notes 13, 19, PDF pp. 380–381).

### Implementation in this repo

What we decide.

**Mapping.** Section 7.2 (empirical fair spread model): add `price_dist_par` and `coupon_minus_yield` as controls inside the issuer, so a premium bond's extra spread is not read as mispricing in S1. Section 6 (recovery): the mechanism is recovery on par, so `hy/recovery.py` supplies expected recovery per 100 of face. Section 9 (event risk): the Model 2 hedge ratio gives the asymmetric rate exposure in `hy/events.py`. Section 8, S4 (capital structure relative value) in `hy/signals.py` (`s4_pair_score`) is the natural home for a same-issuer discount vs. premium pair. Backtest in `hy/backtest.py` (Section 11).

**Data we have.** TRACE panel per bond and month: `coupon`, `price`, `yield`, `g_spread`, `tsy_yield`, `mod_dur`, `years`, `bid_ask_pts`, `cusip6` (issuer), `available_at` (`hy/sources/trace_panel.py`). Treasury curve in `hy/sources/treasury.py`. Rule 1 of the panel keeps fixed-coupon non-convertible bonds.

**Data we lack.** OAS and OAD (we have G-spread and modified duration), amount outstanding for issuer weights, call flags (HY bonds are often callable, the book uses noncallable bonds), CDS curves for BCDS, a Baa−Aaa series.

**Proxy.**
1. OAS → G-spread. OAD → modified duration. Callable HY bonds near the call price break the price-distance logic. Our decision: exclude bonds with price above the first call price where the call schedule is known, else flag them.
2. Issuer weight → equal weight per issuer.
3. Frequent issuer → three or more bonds. HY issuers rarely have seven bonds. State this as a change.
4. Baa−Aaa premium → median HY G-spread of the panel, or ICE BofA HY OAS from FRED (`BAMLH0A0HYM2`), as the regime variable.
5. HY prices span much further from par (distressed bonds below 50). Cap PriceDistPar, or exclude bonds that trade flat (`FLAT_PRICE = 50`).

**Lag rule.** All fields come from the last 7 calendar days of month t. `available_at` = last trade date + 1 day. Form portfolios at t + 1 day. Measure return from t to t+1 month end. The regime quartile breakpoints must use only data up to t (expanding window), not full-sample quartiles as the book does.

**Falsifiable test.**
- Signal: inside each issuer with three or more panel bonds, long the bonds with coupon minus yield below the issuer median, short the rest, duration matched as in steps 6–10.
- Horizon: one month, rebalanced monthly, 2008–2026.
- Metric: mean active excess return (G-spread basis) net of half the bid-ask spread on turnover (`signals.net_return`), annualised IR, Newey–West t.
- Pass: net active return > 0 with t > 2, and positive in at least three of the four cycles (2008, 2015, 2020, 2022). Secondary pass: the active return in the top quartile of the expanding HY spread regime exceeds the bottom quartile (the Table 10.7 claim). A same-issuer pricing check also runs: the monthly β of OAS-proxy on coupon, after the issuer duration slope, is positive in more than 70% of months.

---

## Chapter 11. Maturity Dependence of Corporate Bond Excess Returns (PDF pp. 383–396)

**Question.** Why do long-maturity IG corporate bonds earn less excess return, and less per unit of risk, than short-maturity bonds?

**Answer.** Over January 1994 – January 2019, the 1–3 year bucket earned 93 bp/year at IR 0.53, and the 20–35 year bucket earned 43 bp/year at IR 0.06, despite a higher average OAS (Table 11.2, PDF p. 388). An attribution shows three causes that vary with maturity: roll-down (strong at short maturities, negative near 10 years), a sample-specific bear steepening of spreads, and downgrade costs that grow with maturity (PDF pp. 391–395).

### Data

What the book says:
- Index. Bloomberg Barclays US Investment Grade Corporate Bond Index (PDF p. 383).
- Period. End of January 1994 to January 2019, 25 years, monthly (PDF p. 384).
- Exclusions. Bonds with significant optionality, average life below 1 or above 35 years at the start of any month, or extremely high OAS (note 2, PDF p. 396). The book gives no OAS cut-off value.
- Buckets by average life: 1–3, 3–5, 5–7, 7–9, 9–11, 11–20, 20–35 years (PDF p. 384).
- Returns. Index excess returns: corporate total return minus total return of a duration-matched hypothetical Treasury portfolio (PDF p. 384).
- Buckets keep their natural sector mix. The attribution uses issuer curves (PDF p. 384).
- Issuer curves: issuers with bonds in at least three of the seven buckets. Their curves are pooled to give roll-down for similar issuers with fewer bonds (note 3, PDF p. 396).
- Liquidity: Barclays Liquidity Cost Scores (LCS), from January 2007 only (PDF p. 390).
- Sub-universes: A-rated and Baa-rated subsets (Table 11.4, PDF p. 394). The authors report that nonfinancials give broadly similar results (PDF p. 387). No table is shown for nonfinancials.

### Definitions and formulas

**Excess return per bucket.** Market-value-weighted index excess return of the bucket, monthly. Annualised mean in bp/year.

**Information ratio.**
```latex
IR_b = \frac{\overline{ER}_b \ (\text{bp/yr})}{\sigma(ER_b) \ (\text{bp/yr})}
```
Intuition: return per unit of excess-return volatility. Check: 93 ÷ 174 = 0.53 for the 1–3 year bucket (Table 11.2).

**Four-factor attribution (PDF p. 387).** The book defines the factors in words. It gives no formula. The formulas below are our reading. They reproduce Table 11.2 within a few bp.
```latex
ER_b = \underbrace{\overline{OAS}_b}_{\text{carry}} + \underbrace{RD_b}_{\text{roll-down}} + \underbrace{TR_b}_{\text{spread trend}} + \underbrace{DG_b}_{\text{residual, downgrade cost}}
```
Intuition: excess return is spread earned, plus price gain from rolling down the curve, minus loss from the secular widening, minus credit losses.

- Carry. Spread accretion at the start-of-month OAS. Table 11.2 carry equals average OAS, in bp/year.
```latex
\text{Carry}_b = \overline{OAS}_b
```
- Roll-down. Price return from repricing a bond at the spread of a one-month shorter maturity on its issuer curve, curve unchanged. Curves are fitted at the start of each month (PDF p. 387). Our reading of the annual figure:
```latex
RD_b \approx \overline{OASD}_b \times \overline{\text{Slope}}_b \quad (\text{slope in bp per year of maturity})
```
Intuition: a bond one year shorter sits lower on an upward curve. Check: 5.1 × 7.1 = 36 (5–7y), 7.4 × (−3.7) = −27 (9–11y), Table 11.2.
- Spread trend. Sample-specific cumulative spread change from start to end of the period (PDF p. 387). Our reading:
```latex
TR_b \approx -\overline{OASD}_b \times \frac{OAS_{b,end} - OAS_{b,start}}{T}
```
Intuition: a steady widening of Δ bp/year costs duration × Δ per year. Check: 12.1 × 4.9 = 59 vs. −60 (20–35y), 2.0 × 1.7 = 3.4 vs. −3 (1–3y).
- Downgrade cost. Residual of realised ER minus carry, roll-down and trend (PDF p. 387). It also catches unrelated spread moves (PDF p. 391).
- Excess return excluding spread trend = ER − TR.

**Rating drift (Figure 11.6, PDF p. 392).** Each month: month-end average rating minus start-of-month average rating of the same bonds, on a linear notch scale. Positive = net drift to lower quality.

**LCS per unit DTS (Figure 11.4, PDF p. 390).** Average Liquidity Cost Score divided by duration times spread. Lower = cheaper to trade per unit of spread risk.

### Implementation steps

1. Each month, take index bonds. Drop bonds with significant options, average life outside [1, 35] years, or extreme OAS.
2. Assign each bond to a maturity bucket by average life at the start of the month.
3. Compute the bucket's market-value-weighted monthly excess return over duration-matched Treasuries.
4. Report annualised mean, annualised standard deviation, IR. Repeat for five non-overlapping five-year windows (Table 11.1).
5. Fit a spread curve per issuer at the start of each month, for issuers with bonds in three or more buckets. Pool these curves to cover other issuers (note 3). The book does not give the curve form. Our reading: OAS linear (or piecewise linear) in average life per issuer, slope in bp per year.
6. Compute per bond: carry = OAS ÷ 12, roll-down = −OASD × (OAS at maturity − 1/12 minus OAS at maturity) on the issuer curve.
7. Aggregate to buckets with market weights. Annualise.
8. Compute spread trend from the bucket OAS at the start and the end of the period and the bucket OASD.
9. Set downgrade cost = realised ER − carry − roll-down − trend.
10. Repeat for A-rated and Baa-rated subsets (Table 11.4).

This chapter has no long-short strategy and no transaction costs.

### Results

**Table 11.2, US IG, 1994–2019 (PDF p. 388).** Buckets 1–3 / 3–5 / 5–7 / 7–9 / 9–11 / 11–20 / 20–35.

| Row | 1–3 | 3–5 | 5–7 | 7–9 | 9–11 | 11–20 | 20–35 |
|---|---|---|---|---|---|---|---|
| Average OAS (bp) | 103 | 120 | 141 | 149 | 139 | 162 | 163 |
| Average OASD | 2.0 | 3.6 | 5.1 | 6.4 | 7.4 | 9.6 | 12.1 |
| Average spread slope (bp/y) | 8.9 | 7.4 | 7.1 | 0.1 | −3.7 | 2.2 | 0.1 |
| Trend change in OAS (bp/y) | 1.7 | 2.5 | 3.5 | 3.7 | 4.0 | 5.6 | 4.9 |
| Spread carry (bp) | 103 | 120 | 141 | 149 | 139 | 162 | 163 |
| Roll-down (bp/y) | 16 | 25 | 36 | 0 | −27 | 20 | −2 |
| Spread trend (bp/y) | −3 | −9 | −18 | −24 | −30 | −53 | −60 |
| Residual incl. downgrade cost (bp/y) | −23 | −45 | −52 | −61 | −56 | −60 | −58 |
| Realised excess return (bp/y) | 93 | 91 | 108 | 65 | 27 | 68 | 43 |
| Excess return ex trend (bp/y) | 96 | 100 | 126 | 88 | 56 | 121 | 103 |
| StDev ER (bp/y) | 174 | 265 | 380 | 433 | 449 | 551 | 728 |
| Realised IR | 0.53 | 0.34 | 0.28 | 0.15 | 0.06 | 0.12 | 0.06 |

**Table 11.1, five-year windows (PDF p. 386).** IR falls with maturity in every window. ER of the 1–3 vs. 20–35 bucket: 1994–99 45 vs. −28. 1999–2004 102 vs. 55. 2004–09 −65 vs. −496. 2009–14 307 vs. 643. 2014–19 73 vs. 41. IR 1–3 vs. 20–35: 0.92 vs. −0.08, 0.86 vs. 0.09, −0.22 vs. −0.56, 1.59 vs. 0.64, 1.20 vs. 0.07. Longer duration paid more only in 2009–14 (PDF p. 385).

**Table 11.3, 31 January 2019 (PDF p. 389).** 9–11y bucket: 86% of bonds younger than 2 years, average age 2.5 years, 40% of new issuance. 3–5y: 35%, 4.0 years, 5%. 7–9y: 44%, 2.8 years, 6%. 20–35y: 28%, 4.3 years, 31%.

**Liquidity (Figure 11.4, PDF p. 390).** The 9–11y bucket has persistently lower LCS per DTS than 7–9y and 11–20y. The authors link this to its lower spread and inverted curve. The chart values range about 0.04 to 0.13.

**Spread trend (PDF p. 391).** Without the trend, 20–35y would have earned 103 bp/year, 60 bp more than realised. The 1–3y trend effect is 3 bp/year. Even ex-trend, extending beyond seven years adds no return.

**Attribution charts (Figures 11.7, 11.8, PDF p. 393).** 3–5y: 91 bp/year. 9–11y: 27 bp/year.

**Table 11.4, A and Baa (PDF p. 394).** A-rated ER: 80, 79, 100, 65, 10, 51, 43. IR: 0.49, 0.32, 0.29, 0.17, 0.02, 0.11, 0.07. A roll-down 9–11y: −41. Baa-rated ER: 115, 113, 127, 74, 53, 92, 56. IR: 0.52, 0.34, 0.28, 0.14, 0.10, 0.14, 0.07. Downgrade cost A: −19 to −47. Baa: −38 to −92. Baa downgrade cost is about twice A on average (PDF p. 395).

### Robustness and variants

- Five-year subperiods: the IR decline holds in all five (Table 11.1).
- Rating subsets A and Baa: same pattern, 9–11y dip in both (Table 11.4).
- Nonfinancials: broadly similar, no table (PDF p. 387).
- Ex-trend returns: the gap narrows but long bonds still do not beat 5–7y (PDF p. 391).

### Limits and caveats

- IG only. No HY bucket results.
- Descriptive attribution, not a tradable backtest. No costs, no long-short return, no t-statistics.
- Downgrade cost is a residual. It holds model error and any unrelated spread move.
- The spread trend is specific to this sample. The authors call it sample-specific (PDF p. 387).
- New-issue concession is missed, since bonds join the index at month end (PDF p. 389). This understates the 10y bucket for primary-market buyers.
- OAS, OASD, index returns and LCS are Barclays data.
- Market segmentation (liability-driven demand for long bonds) is named but not tested (PDF p. 384).

### Implementation in this repo

What we decide.

**Mapping.**
- Section 7.4 (spread per unit of risk): the chapter says spread per unit of duration overstates the reward for long bonds. Use maturity bucket as a peer-cell dimension in `hy/peers.py` and `hy/groups.py`.
- Section 7.5 (residual dynamics): roll-down is a deterministic part of expected spread change. Add expected roll-down `RD = −mod_dur × slope × Δt` from the issuer curve to the expected-return term in `hy/rv.py` or `hy/fairspread.py`.
- Section 7.2 (empirical model): include issuer curve slope and bond age as controls, because new 10y bonds trade rich.
- Section 9 (event risk): downgrade cost grows with duration. Weight the downgrade loss in `hy/events.py` by duration.
- Section 11 (backtest): report every signal by maturity bucket.

**Data we have.** TRACE panel: `g_spread`, `mod_dur`, `years`, `cusip6`, `price`, monthly (`hy/sources/trace_panel.py`). Issuer curves can be fitted per `cusip6` per month. Bond issue date may come from TRACE reference data (`hy/sources/trace_bonds.py`).

**Data we lack.** OAS and OAS duration, index excess returns, LCS, monthly agency ratings.

**Proxy.**
1. OAS → G-spread. OASD → modified duration. HY callable bonds bias long-bucket duration upward. Flag bonds with known calls.
2. Excess return → bond return minus duration-matched Treasury return from `hy/sources/treasury.py`.
3. LCS → `bid_ask_pts` ÷ (mod_dur × g_spread).
4. HY buckets: 1–3, 3–5, 5–7, 7–10, 10+ years. HY bonds are rarely longer than 10 years.
5. Downgrade cost → the residual, as in the book. No rating data needed.

**Lag rule.** Fit issuer curves on data with `available_at` ≤ t + 1 day. Compute roll-down from the start-of-month curve only. The spread-trend term uses the full sample, so it is a reporting tool, never a predictor. A predictor must not use it.

**Falsifiable test.**
- Signal: expected roll-down return `RD_i = −mod_dur_i × slope_issuer(t) × (1/12)`, from issuer curves fitted on issuers with three or more panel bonds.
- Horizon: one month and three months.
- Metric: cross-sectional rank IC of `RD_i` with next-period excess return (`signals.rank_ic`), and IC of carry + roll-down vs. carry alone.
- Pass: mean monthly rank IC of carry + roll-down exceeds carry alone by more than 0.01 with t > 2 over 2008–2026, and the IR of the 1–3y HY bucket exceeds that of the 7–10y bucket in at least three of the four cycles (2008, 2015, 2020, 2022).

---

## Chapter 12. ESG Investing in Credit (PDF pp. 397–440)

Note on page range. The chapter text, appendix and notes end on PDF p. 432. PDF pp. 433–437 hold the Part Four introduction (factor investing, Chapters 13–19). PDF pp. 438–440 are a blank page and the "Value Investing" part title. They hold no Chapter 12 content.

**Question.** Does a best-in-class ESG tilt, with every other risk exposure matched, change the return and the spread of corporate bond portfolios?

**Answer.** In IG, high-ESG portfolios beat low-ESG portfolios with matched risk, by 3.6 (MSCI) and 2.3 (Sustainalytics) bp/month in US IG and 4.3 and 3.5 bp/month in Euro IG, 2009–2018 (Table 12.5, PDF p. 411). Governance drives the US result, environment the Euro result. Spreads show no richening of high-ESG bonds, so the authors reject a demand story. In US HY (2012–2018) only the MSCI governance tilt is clearly positive: 10.3 bp/month, IR 1.1 (Table 12.11, PDF p. 425).

### Data

What the book says:
- Bond data. Bloomberg Barclays US IG Corporate, Euro IG Corporate and US HY indices (PDF p. 397).
- ESG data. MSCI ESG Research (scale 0–10) and Sustainalytics (scale 0–100). The Sustainalytics scores used are no longer its primary signal (footnote, PDF p. 397). Sustainalytics "governance" measures governance of sustainability issues, not corporate governance (Table 12.5 note, PDF p. 411).
- Mapping. ESG scores attach to companies and equity identifiers. Each bond is mapped to an equity with a score, per provider and per month, with an existing bond-equity map (PDF pp. 398–399, note 1 p. 431: Ben Dor and Xu 2015).
- Universe. Bonds with scores from both providers (intersection) (PDF p. 399, note 10 p. 432).
- Period. IG: August 2009 – April 2018. HY: October 2012 – April 2018, because HY issuer coverage jumped from 16% to 23% in Q4 2012 (PDF pp. 397, 399, 421).
- Frequency. Monthly. Portfolios rebalance at month end with the index (PDF p. 408).
- Coverage (Table 12.1, PDF p. 400). US IG market-value coverage 87% (2009) to 95% (2017). Euro IG 80% to 89%. US HY 30% to 59% by market value, 12% to 34% by issuers.
- Credit rating. Index convention: median of Moody's, S&P and Fitch, mapped to numbers (A2 = 7, A3 = 8, Baa1 = 9) (PDF pp. 404–405).

### Definitions and formulas

**ESG score.** Provider overall score and three pillar scores (E, S, G). Providers normalise scores by sector (PDF p. 401).

**ESG tiers.** Rank all companies by score at a date. Split into terciles Low, Medium, High (PDF p. 402).

**Provider agreement.** Monthly rank correlation between the two providers' scores (Figure 12.1, PDF p. 402).

**Index-matched tracking portfolios (PDF pp. 407–408).** An optimiser picks bond weights subject to constraints. Run it twice: once to maximise, once to minimise the weighted-average portfolio ESG score.
```latex
\max_{w} \ (\text{or} \ \min_{w}) \ \sum_i w_i \, ESG_i
\quad \text{s.t.} \quad
\sum_i w_i OAS_i = OAS_{idx},\ \sum_i w_i D_i = D_{idx},\ \sum_i w_i D_i OAS_i = DTS_{idx},
```
```latex
\sum_{i \in q} w_i = W^{idx}_q \ \forall q \in \{3 \text{ rating buckets}\},
\qquad
\sum_{i \in c} w_i = W^{idx}_c,\ \sum_{i \in c} w_i D_i = SD^{idx}_c,\ \sum_{i \in c} w_i D_i OAS_i = DTS^{idx}_c \ \forall c,
\qquad 0 \le w_i \le \bar{w}
```
Intuition: two portfolios with the same spread, duration, DTS, rating mix and sector-maturity mix, which differ only in ESG. The return gap is the ESG effect.
- Cells c: US IG 16 cells (8 industry sectors × 2 maturity buckets). Euro IG 10 cells (5 sectors × 2 maturity buckets) plus a control for issuer geography (PDF p. 408).
- Euro benchmark: the subset of the Euro IG index with scores from both providers (PDF p. 408).
- Concentration limits on each bond and issuer, in market weight and in DTS contribution. The book gives no limit values (PDF p. 408).
- Portfolio size: close to 180 bonds (US IG), close to 160 (US HY) (PDF pp. 408, 422).
- The book does not name the rating buckets or maturity breakpoints. It does not state whether the optimiser is linear or quadratic. Our reading: a linear programme, because the objective and constraints are linear in w.

**ESG return effect.**
```latex
r^{ESG}_t = r^{high}_t - r^{low}_t, \qquad IR = \frac{\overline{r^{ESG}}}{\sigma(r^{ESG})}\sqrt{12}
```
Intuition: return of the max-ESG portfolio minus the min-ESG portfolio, both in excess of duration-matched local Treasuries (PDF p. 410). Check: US IG MSCI 3.6 ÷ 13.6 × √12 = 0.92, and the table shows 0.9.

**ESG spread premium (PDF pp. 414–415).** Monthly cross-section over all bonds in the universe:
```latex
OAS_i = \sum_{s} \delta_s \mathbb{1}[\text{sector}_i = s] + \sum_{r} \theta_r \mathbb{1}[\text{rating}_i = r] + b \cdot OASD_i + \lambda \cdot z^{ESG}_i + \varepsilon_i
```
Intuition: λ is the spread change (bp) per one standard deviation of ESG score after rating, sector and duration. Negative λ means high-ESG bonds trade tighter. In Euro IG, add a geography control (peripheral Europe) (PDF p. 414). Table 12.8 shows sector terms with no separate intercept, ratings A1 to Baa3, and OASD (PDF p. 415). Our reading: sector dummies are the intercepts, Aaa–Aa is the omitted rating group, and z^ESG is the score standardised across bonds in the month.

**Pillar spread premium.** Same regression with E, S or G alone in place of ESG. Coefficients pooled over all months (Table 12.9, PDF p. 419).

**Downgrade notch rate (PDF p. 420).** Split issuers at the median ESG (or pillar) score. Per year:
```latex
DNR = \frac{\sum_{i} \text{notches downgraded}_i}{N_{issuers}}
```
Intuition: frequency times severity. Example: 10% one-notch plus 3% two-notch gives 16%.

**Appendix regression of returns (PDF p. 427).** Monthly cross-section:
```latex
ER_{i,t+1} = a + c_1 OAS_{i,t} + c_2 OASD_{i,t} + \sum_s d_s DTS_{i,t}\mathbb{1}[\text{sector}_i = s] + g \cdot z^{ESG}_{i,t} + \varepsilon
```
Intuition: g is the bp/month return advantage per standard deviation of ESG score. US HY uses eight industry sectors for the DTS terms (PDF p. 430). The book does not state whether the score is lagged. Our reading: the score is known at the start of the return month.

### Implementation steps

1. Map each index bond to its issuer's equity identifier, then to the MSCI and Sustainalytics scores in force at month end t.
2. Keep bonds with scores from both providers.
3. Compute tiers, provider rank correlations, tier transition matrices (12-month), and tier characteristics (Tables 12.2, 12.3).
4. At each month end t, solve the max-ESG and min-ESG programmes against the index (or covered subset) with the constraints above.
5. Hold both portfolios for one month. Compute excess returns over duration-matched Treasuries.
6. Repeat with E, S and G scores, and with each provider.
7. Repeat inside each sector: US IG eight sectors, Euro IG five sectors. Sector portfolios hold 65 to over 110 bonds (US) and 50 to over 110 (Euro) (PDF p. 410).
8. Run the monthly spread regression. Store λ and its 95% confidence interval.
9. Compute downgrade notch rates for above- and below-median groups.
10. Repeat steps 4–8 for US HY from October 2012, with matched duration, spread, rating and sector.
11. Run the appendix return regressions.

No transaction costs are deducted in any table.

### Results

**Provider agreement (Figure 12.1, PDF p. 402).** Rank correlations are positive but low. Overall ESG rises from about 35% to about 45%. Governance is lowest, about 10–20%. Values read from the chart.

**Table 12.2, one-year tier transitions (PDF p. 403).** MSCI: Low stays Low 77%, Medium stays 61%, High stays 79%. Sustainalytics: 86%, 75%, 88%. Governance is slightly less stable.

**Table 12.3, tier characteristics, 2009–2018 (PDF p. 404).** High minus Low OAS: US IG −36 bp (MSCI), −31 bp (Sustainalytics). Euro IG −22 bp, −15 bp. Rating gap is about one notch or less. Environment has the strongest link to rating and spread (PDF p. 403).

**Figure 12.2 (PDF p. 405).** Average rank correlation of credit rating with ESG score is about 2% to 20%. E is highest and G lowest for both providers.

**Table 12.4 (PDF p. 405).** MSCI ESG: USA 4.9, Euro area 6.6, Other 5.8. Sustainalytics ESG: 61.0, 70.8, 66.6. US issuers score lower on every metric, most on social.

**Table 12.5, IG, 2009–2018 (PDF p. 411).** Mean (bp/month), volatility (bp/month), IR.

| Tilt | US IG MSCI | US IG Sustainalytics | Euro IG MSCI | Euro IG Sustainalytics |
|---|---|---|---|---|
| Index ER | 17.0 / 97.5 / 0.6 | same | 16.3 / 87.0 / 0.7 | same |
| ESG | 3.6 / 13.6 / 0.9 | 2.3 / 13.5 / 0.6 | 4.3 / 11.4 / 1.3 | 3.5 / 13.9 / 0.9 |
| Environmental | 2.9 / 13.3 / 0.7 | 1.6 / 15.8 / 0.3 | 2.7 / 13.5 / 0.7 | 3.6 / 11.1 / 1.1 |
| Social | −0.8 / 13.6 / −0.2 | 0.4 / 14.5 / 0.1 | 1.8 / 10.2 / 0.6 | 2.4 / 12.1 / 0.7 |
| Governance | 5.4 / 14.4 / 1.3 | 2.1 / 13.8 / 0.5 | 2.7 / 11.0 / 0.8 | 3.4 / 13.2 / 0.9 |

Cumulative outperformance by early 2018: about 3.7% (US) and 4.5% (Euro) with MSCI, about 2.4% (US) and 3.7% (Euro) with Sustainalytics (Figures 12.3, 12.4, PDF p. 409, read from charts). The period up to 2012 is more volatile. An environmental tilt gave the highest return in the last two years in US IG (PDF p. 410).

**Table 12.6, US IG sectors, bp/month (PDF p. 412).** MSCI ESG: Basic/Capital Goods 6.6**, Cyclical 2.0, Noncyclical 5.8**, Comm & Tech 3.4*, Transport & Energy 6.9**, Utility 0.3, Banking & Brokerage 6.3**, Other Financials 5.4**. MSCI Governance in Banking & Brokerage 6.5**. MSCI Environmental in Noncyclical 8.2**. Sustainalytics ESG: −1.1, 2.4*, 10.3**, 3.5*, 8.3**, 2.4*, 2.0, 3.3**. (* 5%, ** 1% significance for positive results.)

**Table 12.7, Euro IG sectors, bp/month (PDF p. 413).** MSCI ESG: Cyclical 2.1*, Noncyclical 1.3*, Utility −2.5, Banking & Brokerage 5.5**, Other Financials 1.5. Sustainalytics ESG: −0.4, 1.9**, −0.9, 3.2*, 5.3**.

**Table 12.8, US IG spread regression, March 2018, MSCI (PDF p. 415).** ESG −0.6 bp per s.d. (t −0.5). OASD 8.4 (t 22.7). Rating terms A1 2.3, A2 8.8, A3 18.9, Baa1 35.7, Baa2 51.2, Baa3 77.6. Sector terms 57 (Noncyclical) to 87 (Banking & Brokerage). R² 71.8%.

**Figures 12.5–12.8 (PDF pp. 416–418).** US IG λ is rarely significant. No downward trend, so no evidence of richening. Euro IG λ is about −5 bp per s.d. for both providers, stable in the second half (PDF p. 417).

**Table 12.9, pooled spread premium, bp per s.d. (PDF p. 419).** MSCI US IG: ESG −3.0, E −2.2, S 0.0, G −4.2. MSCI Euro IG: −5.1, −2.3, −2.9, −5.0. Sustainalytics US IG: 2.1, 1.1, 2.6, 1.8. Sustainalytics Euro IG: −6.0, −5.9, −4.6, −3.8. Euro tilt return of 42 or 51 bp/year is much larger than, and opposite in sign to, the −5 bp premium (PDF pp. 419–420).

**Figure 12.9 (PDF p. 420).** Low-governance US IG issuers have a higher downgrade notch rate than high-governance issuers through the period, except the last year. Chart values range about 0% to 25%.

**Table 12.10, US HY tiers, 2012–2018 (PDF p. 422).** MSCI High minus Low: OAS −30 bp, OASD 0.0, LCS 0.0, rating number −0.2. Sustainalytics: OAS +20 bp, OASD +1.0, LCS +0.1, rating number −0.5. Average rating B1 to Ba3.

**HY spread premium (Figures 12.11, 12.12, PDF p. 423).** λ drifts down a little. Start and end values are not significantly different. Confidence bands are very wide, most of all in the 2015–2016 energy crisis.

**Table 12.11, US HY, 2012–2018 (PDF p. 425).** HY index ER 41.5 / 152 / 0.9. MSCI: ESG 3.8 / 28 / 0.5, E −2.4 / 39 / −0.2, S 2.3 / 31 / 0.3, G 10.3 / 32 / 1.1. Sustainalytics: ESG 2.1 / 27 / 0.3, E 2.9 / 30 / 0.3, S −0.3 / 30 / 0.0, G 3.5 / 31 / 0.4. Only MSCI governance is statistically significant (PDF p. 425).

**Table 12.13, IG return regressions, bp/month per s.d., 2009–2018 (PDF p. 429).** US IG MSCI: ESG 1.1, E 0.8, S 0.5, G 0.6. Sustainalytics: 0.9, 0.8, 0.8, 0.1. Euro IG MSCI: 0.6, 0.2, −0.5, 0.5. Sustainalytics: 0.5, 0.4, 0.3, 0.3. Average R² 30% (US), 39% (Euro). Monthly R² ranges 5% to 76% (PDF p. 427). Monthly regression coefficients correlate about 0.5 with the portfolio-simulation returns (PDF p. 430).

**Table 12.14, US HY return regressions, 2012–2018 (PDF p. 430).** MSCI: ESG 6.4, E 1.5, S 4.6, G 5.7. Combined: E 0.7, S 5.4, G 5.9. Sustainalytics: ESG 5.3, E 3.0, S 4.6, G 7.4. Combined: E −1.9, S 2.4, G 7.5. Average R² about 34–35%. ESG and governance are significant for both providers (PDF p. 430).

### Robustness and variants

- Two providers: the sign of the overall ESG tilt agrees in both markets. Pillar and sector results differ between providers (PDF pp. 410, 413).
- Pillars: governance leads in US IG, environment in Euro IG, social is weakest (PDF p. 410).
- Sector-level portfolios: mostly positive. Euro utilities negative (PDF p. 413).
- Valuation check: no richening of high-ESG bonds (PDF p. 417).
- Regression method instead of optimiser: weak positive effect, 0.5 to 1 bp/month per s.d. (PDF p. 427).
- More diversified portfolios with over 400 bonds are studied elsewhere (Dynkin et al. 2018) (note 12, PDF p. 432).

### Limits and caveats

- Short sample: under nine years for IG, five and a half years for HY.
- HY coverage is thin: 34% of issuers by the end. The covered issuers are larger and public. Private HY issuers drop out (PDF pp. 421, 426).
- HY portfolio results have low IRs. Only MSCI governance is significant (PDF p. 425).
- Before costs. The book says high tier stability limits turnover (PDF p. 402) but gives no cost estimate.
- Vendor data: MSCI and Sustainalytics scores, Barclays indices, and the Barclays bond-equity map. We have none of these.
- The Sustainalytics scores used are retired (PDF p. 397).
- The optimiser parameters (concentration limits, rating buckets, maturity breakpoints) are not given.
- The governance downgrade link is shown in a chart only, with no test statistic.

### Implementation in this repo

What we decide.

**Mapping.**
- Section 8, S6 (rating migration): the governance result is a downgrade predictor. Low governance → higher downgrade notch rate (Figure 12.9). Add a governance proxy as an input to `migration_probabilities` in `hy/signals.py`.
- Section 4.4 (qualitative risk flags) in `hy/state.py`: governance proxy fields belong here.
- Section 7.2 (empirical model) in `hy/fairspread.py`: the spread-premium regression has the same form as our fair spread regression. A governance term tests whether the market prices governance.
- Section 11 (backtest): the matched max-minus-min portfolio is a template for any characteristic test in `hy/backtest.py`.

**Data we have.** TRACE prices and G-spreads, Compustat point in time (`hy/sources/compustat_pit.py`), SEC filings (`hy/sources/edgar.py`, `hy/sources/xbrl.py`), CRSP equity. The bond-issuer link runs through `cusip6` and `ticker` in `trace_panel`.

**Data we lack.** MSCI and Sustainalytics scores, agency ratings by month, index weights.

**Proxy (governance only, from SEC filings).**
1. Auditor change or going-concern opinion (8-K Item 4.01, 10-K audit report).
2. Late filing (NT 10-K, NT 10-Q forms).
3. Material weakness in internal control (10-K Item 9A).
4. Restatement (8-K Item 4.02).
5. CEO or CFO turnover (8-K Item 5.02).
Score = count of flags in the past 24 months, ranked within sector. This is our proxy, not the book's measure. The book shows that the two vendors' governance scores correlate only about 10–20%, so no single proxy is "the" governance score.

**Lag rule.** Each flag carries `as_of` = event date and `available_at` = EDGAR acceptance timestamp + 1 day. A month-end t portfolio uses only flags with `available_at` ≤ t. Ratings for the downgrade test need a dated rating feed. Without one, use the TRACE master grade change (IG to HY) as the only observable downgrade.

**Falsifiable test.**
- Signal: governance flag count (0 = good) per issuer, ranked within sector.
- Horizon: 12 months for downgrades, one month for returns.
- Metric 1: rate of IG-to-HY events (TRACE grade flag) or price drops below 80 within 12 months, flagged vs. unflagged issuers. Metric 2: matched long-short return (zero-flag issuers minus two-or-more-flag issuers), with duration, G-spread bucket and sector matched, net of half the bid-ask spread.
- Pass: the flagged group's 12-month distress-event rate exceeds the unflagged rate with a one-sided test p < 0.05 over 2008–2026. For the return leg, the net long-short mean is positive in at least three of the four cycles (2008, 2015, 2020, 2022). A failure of the return leg with a pass on the event leg means the market already prices governance, as the book finds for US IG valuation.

---

## Chapter 13. Relative Value Investing in Credit Using Excess Spread to Peers (PDF pp. 441–462)

Book page = PDF page − 28. Every page cited below is a PDF page. Tables 13.5 and 13.8 are rotated. I read them from the page images.

**Question.** Does a bond's spread above its rating-industry-duration peers, net of excess leverage, predict its excess return?

**Answer.** Yes, in US investment grade, 1993–2016. Long above-median ESP minus short below-median ESP earns 1.78% a year at an information ratio (IR) of 1.52 and a 20% correlation with the index (Table 13.3, p. 448). In Fama-MacBeth regressions the ESP premium stays significant (t 8.1) beside spread and duration, and the spread premium loses significance (Table 13.9, p. 457).

### Data
- Universe: Bloomberg Barclays US Corporate (IG) Bond Index. Keep senior, noncallable bonds that map to Compustat (p. 445, note 7 p. 462).
- Exclusion: bonds with spreads in the top 0.5% of the sample, to remove outliers (note 7, p. 462).
- Size: over 2,000 bonds a month on average, over 4,000 in recent months (p. 445). About 2,000 above-median bonds in December 2015 (p. 459).
- Period: January 1993 to January 2016, monthly. Subperiods: Jan 1993–Jun 2007 and Jul 2007–Jan 2016 (Table 13.3, p. 448).
- Returns: excess over duration-matched Treasury portfolios, Barclays index convention (note 2, p. 461).
- Spread: Barclays index OAS (the chapter says "spread". The index convention is OAS).
- Fundamentals: Compustat. Book debt, and market equity (p. 444, note 5 p. 461).
- Liquidity: Barclays Trade Efficiency Score (TES), from 2007 only (p. 451, note 10 p. 462). TES ranks 1 (best) to 10 (worst). It blends Liquidity Cost Score and trading volume (Konstantinovsky, Ng and Phelps 2015).
- Industry: the book does not name the industry level for the peer cell. The tracking portfolios and sector DTS factors use eight sectors: basic industry, consumer cyclical, consumer noncyclical, energy, TMT, utility, banks and brokerages, other financials (note 12, p. 462).

### Definitions and formulas
**What the book says.** "We identify relative value as the portion of excess spread over peers unexplained by fundamental factors and call this measure excess spread to peers (ESP)" (p. 443). Peers are bonds in the same rating × industry × duration (maturity) cell (p. 444). Excess spread and excess leverage are "calculated over peer averages in the same rating-industry-maturity category" (p. 445). Figure 13.3 (p. 444) plots excess spread (y, %) against excess leverage over peers (x, %) for Consumer Noncyclical 3–7y Baa bonds, December 2015. It draws an upward line. Bonds above the line (upper left) are high ESP and cheap. Bonds below it (lower right) are low ESP and rich.

The book prints no ESP formula. It does not say if the leverage control is a regression, a ratio, or a cell-level line. It does not give the maturity bucket edges, other than the 3–7y example. It does not say if spread is in levels or logs.

Leverage (note 5, p. 461):

```latex
L_{i,t} = \frac{D^{book}_{i,t-3m}}{E^{mkt}_{i,t-3m} + D^{book}_{i,t-3m}}
```
Intuition: market leverage, the Merton (1974) driver of default risk. The book lags it three months.

Excess spread and excess leverage over the peer cell c (p. 445):

```latex
XS_{i,t} = s_{i,t} - \bar{s}_{c,t}, \qquad XL_{i,t} = L_{i,t} - \bar{L}_{c,t}
```
Intuition: how much more the bond pays, and how much more levered its issuer is, than the average peer.

ESP, our reading (labelled as our reading, not printed in the book):

```latex
ESP_{i,t} = XS_{i,t} - \hat{\beta}_{c,t}\, XL_{i,t}, \qquad \hat{\beta}_{c,t} = \text{OLS slope of } XS \text{ on } XL \text{ in cell } c \text{ (or pooled)}
```
Intuition: the part of the excess spread that excess leverage does not explain. The line in Figure 13.3 is the fitted XS on XL. ESP is the vertical distance to it.

ESP without leverage (Table 13.1 left panel, p. 446) is simply `XS`.

Factor exposures for the Fama-MacBeth regression (note 14, p. 462):

```latex
x^{k}_{i,t} = 2\,\big(\mathrm{pctrank}_t(k_i) - 0.5\big) \in [-1, 1], \quad k \in \{ESP, \text{duration}, \text{spread}\}
```
Intuition: a bond at the 60th ESP percentile has exposure 0.2. A median bond has exposure 0.

Sector DTS exposure: `DTS_i × 1{sector_i = j}` for each of the eight sectors (note 14, p. 462). This term carries the market factor.

Cross-sectional regression each month t (Table 13.9, p. 457, note 13 p. 462):

```latex
r^{xs}_{i,t+1} = \sum_k \lambda^{k}_{t}\, x^{k}_{i,t} + \sum_{j=1}^{8} \gamma^{j}_{t}\, DTS_{i,t}\, 1\{sector_i = j\} + \varepsilon_{i,t+1}
```
Intuition: λ is the monthly return to one unit of percentile-rank exposure. The DTS terms remove sector beta. The book does not state an intercept. Our reading: no intercept, because the sector DTS terms absorb the market.

Factor premium and t-stat: mean of the monthly λ series, and its t-statistic (Fama-MacBeth 1973).

Turnover (note 11, p. 462): the market-value share of bonds that the high-ESP portfolio buys in the month.

Security-specific volatility (notes 16–17, p. 462): residuals of the Table 13.9 regression. Variance is the time average of the cross-sectional variance of residuals within each ESP decile. Report it annualised.

### Implementation steps
1. **Universe at each month end t.** Take index bonds that are senior and noncallable and map to Compustat. Drop the top 0.5% of spreads.
2. **Leverage.** Compute `L = book debt / (market equity + book debt)` with inputs dated three months before t (note 5, p. 461).
3. **Peer cell.** Assign rating × industry × maturity bucket. Our reading: Barclays rating (Aaa/Aa, A, Baa, and the BB/B tail that the rating split shows), the eight sectors of note 12, and maturity buckets that include 3–7y.
4. **Excess spread and excess leverage.** Subtract the cell average (mean, "peer averages", p. 445) of spread and of leverage.
5. **ESP.** Remove the part of excess spread that excess leverage explains (our reading above). Also compute ESP without leverage as a variant.
6. **Decile sort.** Sort all bonds into 10 ESP deciles each month (p. 445). Market-value weight within each decile (note 9, p. 462).
7. **Long-short portfolio.** High-ESP = bonds above the median ESP. Low-ESP = bonds below the median (p. 446). Market-value weights (note 9, p. 462). Rebalance monthly. Hold one month.
8. **Buffer variants** (p. 454). "10% buffer": buy into the long leg at the top 40% of ESP. Sell when ESP drops below the median. Short leg: enter at the bottom 40%, exit when ESP rises above the median. "15% buffer": the long leg keeps bonds until they fall into the bottom 45%. The short leg keeps bonds until they reach the top 45%. The ESP formula does not change.
9. **Returns.** Excess return over duration-matched Treasuries, market-value weighted, monthly. The long-short return is high minus low. Also report high-ESP minus the index.
10. **Statistics.** Annualised mean, volatility, IR = mean/volatility, maximum drawdown, correlation with the index, index beta. Report per subperiod, per rating, financials against nonfinancials, per TES quintile.
11. **Dispersion check.** Each month compute the ESP difference between the high and low portfolios. Sort months into quintiles of it. Report the mean subsequent 12-month strategy return per quintile (Figures 13.6–13.7, pp. 451–452).
12. **Tracking portfolios** (p. 455). Each month maximise the portfolio ESP score subject to: match index DTS, duration and market-value contribution in each of the eight sectors, and match total DTS and duration. Issue cap 4%, 2% or 1%. Ticker cap = 2 × issue cap.
13. **Fama-MacBeth.** Run the step 9 regression each month. Report mean λ and t for: spread alone, duration alone, ESP alone, spread + duration, all three.
14. **Selection risk** (pp. 459–460). Draw n bonds at random from the above-median set and n from the below-median set each month. Report idiosyncratic volatility and IR against n.

### Results
**Deciles (Table 13.1, p. 446).** Annual excess return, volatility, IR, decile 1 to 10:
- Without leverage: D1 −1.19% (IR −0.24), D5 0.66% (0.19), D10 2.63% (vol 6.28%, IR 0.42).
- With leverage: D1 −1.10% (IR −0.27), D5 0.70% (0.19), D8 1.55% (0.40), D10 3.29% (vol 6.16%, IR 0.53).
- The order is near monotonic and holds in both subperiods (Figure 13.4, p. 445). The book calls the leverage gain "moderate" (p. 445).

**Score stability (Table 13.2, p. 447).** Decile 10 stays in decile 10 for 77% of bonds after 3 months and 56% after 12 months. Decile 1 stays for 70% and 44%. Scores revert toward the middle.

**Long-short (Table 13.3, p. 448).**

| Period | High−Low ret %/yr | Vol | IR | MaxDD % | Corr. index | High−Index ret | IR |
|---|---|---|---|---|---|---|---|
| 1993–2016 | 1.78 | 1.18 | 1.52 | −2.0 | 20% | 1.18 | 1.32 |
| 1993–Jun 2007 | 1.15 | 0.95 | 1.22 | −2.0 | 43% | 0.75 | 1.26 |
| Jul 2007–2016 | 2.85 | 1.44 | 1.98 | −1.7 | 14% | 1.91 | 1.56 |

- Legs 1993–2016: High ESP 1.56% (IR 0.38, MaxDD −20.1%), Low ESP −0.23%, index 0.38% (p. 448).
- High-ESP minus index correlation with the index: −20% full period, −35% 2007–2016 (p. 448).

**Characteristics (Table 13.4, p. 449).** 1993–2016, high ESP against index: spread 155 bp against 139 bp (+17 bp), duration 5.6 against 6.1 years, DTS 9.5 against 9.0, rating A3 for both. High minus low: spread +37 bp, duration −0.9, DTS +1.0. The 17 bp carry gap cannot explain a 118 bp a year return gap. The book credits mean reversion of relative spreads (p. 449).

**By rating and sector (Table 13.5, p. 450), high minus low, 1993–2016.**

| Bucket | Ret %/yr | Vol | IR | MaxDD % |
|---|---|---|---|---|
| AAA–AA | 1.01 | 1.17 | 0.86 | −4.26 |
| A | 1.97 | 1.28 | 1.54 | −1.33 |
| BBB | 1.94 | 1.85 | 1.05 | −5.35 |
| HY (BB/B) | 3.80 | 2.61 | 1.45 | −5.36 |
| Financials | 2.40 | 1.98 | 1.21 | −2.60 |
| Nonfinancials | 1.54 | 1.08 | 1.43 | −2.65 |

- HY (BB/B) by subperiod: 3.86% (IR 1.41) to Jun 2007, 3.70% (IR 1.54) after (p. 450). The book does not explain how BB/B bonds enter an IG index universe. Our reading: fallen angels kept in the sample, or a broader universe for this split. This is the only HY number in the chapter. Treat it with care.

**Dispersion (Figures 13.6–13.7, pp. 451–452).** Mean subsequent 12-month return rises with the high−low ESP gap. Quintile gap means read 0.3, 0.4, 0.5, 0.7, 1.5 (%). The Q5 bar is above 4%/yr. Q1 and Q2 bars are near 0.7%/yr (read from the chart, not a table). Q5 is mostly the 2008 crisis. The strategy lost money over 12 months in 2002 and 2015, in spread momentum episodes (p. 451).

**Liquidity (Table 13.6, p. 452), 2007–2016.** Overall 2.77%/yr, IR 1.96, index beta 6%. TES Q1 (most liquid) IR 1.57. TES Q4 IR 2.43. TES Q5 2.99%/yr, IR 2.09. Less liquid buckets show the highest IR. Trading volume falls with ESP to decile 9, then jumps in decile 10 (Figure 13.8, p. 453).

**Turnover (Table 13.7, p. 453).**

| | No buffer | 10% buffer | 15% buffer |
|---|---|---|---|
| Ret %/yr | 1.78 | 1.98 | 1.86 |
| Vol %/yr | 1.18 | 1.52 | 1.56 |
| IR | 1.52 | 1.31 | 1.20 |
| MaxDD % | −2.00 | −3.58 | −3.68 |
| Turnover high-ESP %/month | 11.2 | 5.7 | 4.3 |

**Tracking portfolios (Table 13.8, p. 456), 1993–2016.** Index 0.38%/yr. Portfolio 1 (4% cap, 34 bonds): 1.75%/yr, excess over index 1.37%, tracking IR 1.13. Portfolio 2 (2%, 59 bonds): 1.73%, excess 1.36%, IR 1.21. Portfolio 3 (1%, 109 bonds): 1.59%, excess 1.22%, IR 1.19. Spread over index: +0.15 to +0.17 percentage points.

**Fama-MacBeth (Table 13.9, p. 457), bp a month per unit of exposure.**

| Model | Spread (t) | Duration (t) | ESP (t) |
|---|---|---|---|
| Spread alone | 5.2 (2.7) | | |
| Duration alone | | −12.2 (−5.4) | |
| ESP alone | | | 15.2 (8.7) |
| Spread + duration | 7.2 (3.3) | −14.2 (−5.7) | |
| All three | 2.2 (1.1) | −10.9 (−4.5) | 12.4 (8.1) |

- The text says ESP alone has t 8.6 and t 8.0 in the full model (p. 458). The table prints 8.7 and 8.1. Use the table.
- Sector DTS premia are 0.0 to 1.0 bp a month per unit DTS, t below 2.0 (p. 457).

**Correlations (Table 13.10, p. 458).** The ESP factor correlates −24% with the credit market, −7% with spread, −22% with duration, −27% with the equity market, 2% with size, −19% with value, −6% with momentum.

**Selection risk (Figures 13.10–13.11, p. 460).** Idiosyncratic volatility is near 4%/yr in middle deciles, above 5% in decile 1, and near 10% in decile 10 (chart reading). With about 50 positions per leg the overlay IR is close to 1 (p. 460).

### Robustness and variants
- With and without the leverage control (Table 13.1). Leverage raises D10 IR from 0.42 to 0.53.
- Subperiods before and after mid-2007. The edge holds in both and is larger after.
- Rating buckets, financials against nonfinancials, TES quintiles. The edge holds in all.
- Equal weights with one bond per issuer give "even stronger" results (note 9, p. 462). The book prints no numbers.
- Turnover buffers. They halve turnover and raise return, at a lower IR.
- Concentrated tracking portfolios (34 to 109 bonds). Tracking IR stays above 1.
- Factor regression. ESP survives spread, duration and sector DTS controls.

### Limits and caveats
- IG only, apart from one BB/B split row of unclear origin (Table 13.5).
- All results are before transaction costs. The book reports turnover, not costs.
- Barclays data we cannot get: index OAS, index membership, amount outstanding (market weights), TES, the Barclays rating and sector scheme.
- The ESP formula is not printed. The leverage control form, the maturity bucket edges and the industry level are unknown.
- The strategy depends on mean reversion of relative spreads. It lost money in spread momentum years (2002, 2015).
- The top dispersion quintile is one episode (2008). The dispersion result rests on it.
- Senior noncallable bonds only. Most HY bonds are callable, so this filter cannot carry over to HY.

### Implementation in this repo
**Mapping.** Methodology 7.4 (model-free check: spread per unit of risk) and Section 8 composite through estimate E14 in `hy/groups.py`. Code: `hy/peers.py`, `peer_signals` (columns `esp_<level>` and `esp_lev_<level>`), `live_peers`. Section 11 backtest design applies.

**What exists.**
- `esp_*` = log spread minus the peer median of log spread. The cell is GICS sector × rating class (IG, BB, B, CCC) × maturity bucket (<3, 3–7, ≥7 years). A cell needs 5 other issuers, with fallbacks. Peers exclude the issuer's own bonds.
- `esp_lev_*` = ESP minus a pooled cross-section slope times excess log leverage. Leverage there is debt over LTM EBITDA, not the book's market leverage.

**Gaps against the book.**
1. Leverage ratio. The book uses `D / (E_mkt + D)`, lagged 3 months. We use debt / LTM EBITDA. Market equity needs `prccq × cshoq` from `hy/sources/compustat_pit.py`, or the month-end price × shares from `comp.secm`.
2. Mean against median, level against log. The book says "averages". We use medians of logs. We decide to keep log-median for HY, because HY spreads are skewed. Record this as our choice.
3. Callable bonds. The book keeps noncallable only. Our panel keeps callable HY bonds. Use G-spread to worst if available. Otherwise flag callable bonds and run the test on both sets.
4. Weights. The book uses market weights. The TRACE panel has no amount outstanding. Use equal weights, one bond per issuer (the book says this gives stronger results, note 9 p. 462).
5. Liquidity buckets. No TES. Proxy: TRACE monthly trade count and volume quintiles from `hy/sources/trace_panel.py`.
6. Outlier cut. Drop the top 0.5% of G-spreads each month, as the book does.

**Lag rule (no look-ahead).** Spread: the TRACE month-end G-spread, `available_at` = the last trade time in the month. Book debt: Compustat point-in-time snapshot, `snapshot_available_at` = pointdate + 1 day (`hy/sources/compustat_pit.py`). Market equity: Compustat month-end price × shares, `available_at` = datadate + 1 day. Leverage at decision time t uses debt and equity with `available_at ≤ t − 3 months`. Ratings: `available_at` = datadate + 1 day (`hy/sources/peer_data.py`). GICS: `available_at` = indfrom.

**Falsifiable test.**
- Signal: `esp_mlev_sr` = ESP with market leverage `D / (E_mkt + D)` lagged 3 months, sector × rating × maturity cell.
- Horizon: 1 month (the book's holding period) and 12 months (the repo's standard).
- Metric: monthly cross-section rank IC of the signal against next-period excess return over duration-matched Treasuries, beyond spread level (residual after rank on log spread). Also the equal-weight above-median minus below-median return, with and without the 10% buffer.
- Pass: 12-month beyond-spread IC above plain ESP (+0.096, t 2.6, decision page `2026-10-22-esp-peer-groups`) with t ≥ 2. The 1-month long-short IR must be > 0.5 in at least three of the four cycle windows (2008, 2015, 2020, 2022). Fail: keep plain `esp_sr` and drop the leverage control.

---

## Chapter 14. Long-Horizon Value Investing in Credit Using Spread per Unit of Debt-to-Earnings Ratio (PDF pp. 463–510)

Book page = PDF page − 28. Every page cited below is a PDF page. The chapter text ends on p. 507. Pages 508–510 are the part title "Momentum Investing". Rotated tables 14.2, 14.3, 14.7, 14.8, 14.10–14.19 were read from page images. Table 14.14 was read from a 150 dpi render.

**Question.** Does issuer OAS per unit of debt over sustainable (10-year mean) EBITDA predict bond excess returns over the next year?

**Answer.** Yes, in IG and in HY (Ba and B, price ≥ $50), March 1993 to February 2020. The within-industry Q5 minus Q1 portfolio, equal weight, rebalanced each February, earns 1.61%/yr at IR 1.17 in IG and 2.62%/yr at IR 0.73 in HY (Table 14.7, p. 476). The edge survives DTS risk matching, an OAS-neutral sort, transaction costs with 24-month rebalancing, and index tracking constraints.

### Data
- Universe: all bonds in the Bloomberg Barclays US Corporate (IG) and US High Yield indices, January 1993 to February 2020 (p. 465). Return sample March 1993 to February 2020.
- Keep issuers with domestic Compustat statements. "Domestic" = US or Canadian companies, or companies with ADRs (note 3, p. 506).
- Filters (pp. 465–466):
  1. Drop financials.
  2. HY: keep bonds rated B or above, with February month-end price ≥ $50 (Table 14.1 note, p. 466).
  3. Keep firms with at least 6 years of financial statements in the past 10 years.
  4. Keep firms whose latest fiscal year or fiscal quarter ends in October, November or December.
- Mapping coverage (Table 14.1, p. 466): IG 85% of index market value in 1994, 98% in 2019. HY 68% in 1994, 83% in 2019.
- February 2019 tickers (Table 14.1 Panel B, p. 466): IG 688 mapped → 480 ex financials → 470 with 6-year history → 463 final. HY 641 → 586 → 525 after rating and price → 495 → 491 final.
- Sample against benchmark (Table 14.2, p. 467), monthly average: IG sample 481 issuers, OAS 133 bp, duration 6.86, DTS 9.90, return 0.61%/yr, IR 0.15. IG benchmark 637 issuers, OAS 136, IR 0.16. HY sample 333 issuers, OAS 329, DTS 15.66, return 1.86%, IR 0.27. HY benchmark 656 issuers, OAS 426, return 2.21%, IR 0.27. Correlation of sample with benchmark 0.99 in both.
- Benchmarks: the Barclays credit index ex financials. HY benchmark also excludes bonds rated below B (Table 14.7 note, p. 476).
- Returns: excess over duration-matched Treasuries (p. 475).
- Other data: Barclays OAS and market values, Barclays Liquidity Cost Score (LCS, from 2007), I/B/E/S EBITDA consensus (from 2003), Ken French data library for equity value factors.

### Definitions and formulas
**SPiDER** (p. 468), computed once a year, at issuer level:

```latex
SPiDER_{i,t} = \frac{OAS_{i,t}}{Debt_{i,t} \,/\, \text{SustEBITDA}_{i,t}}
```
Intuition: the market price of default risk per unit of fundamental default risk. High SPiDER = cheap.

- `OAS_{i,t}` = market-value-weighted OAS of all the issuer's index bonds at end of February of year t, in percent (pp. 468, 471).
- `Debt_{i,t}` = long-term debt + short-term debt (p. 468). If the annual statement is not available, use debt from the most recent quarterly statement (note 4, p. 506).
- `SustEBITDA_{i,t}` = mean of the last 10 annual EBITDA figures, at least 6 (p. 468). If the annual statement is not available, annual EBITDA = sum of the last four quarterly EBITDA figures (note 4, p. 506).

```latex
\text{SustEBITDA}_{i,t} = \frac{1}{n}\sum_{k=0}^{n-1} EBITDA_{i,\,FY(t-1)-k}, \qquad 6 \le n \le 10
```
Intuition: long-run earnings power, less noisy and harder to manipulate than one year (Campbell and Shiller 1988, p. 468).

- Timing (pp. 468–469): OAS at end of February of year t. Fundamentals from the fiscal year or quarter that ends October to December of year t−1. The lag is at least two months between fiscal period end and formation (also note 10, p. 507).
- The book does not say how to treat negative or zero sustainable EBITDA. Our reading: drop the issuer, because the ratio has no meaning.

**D/E rating test** (p. 469, Table 14.3 p. 470). Numeric rating: Aaa = 1, Aa1 = 2, Aa2 = 3, …, C = 21, D = 22. Rating change = rating at end of window (or at index exit, whichever is earlier) minus rating at start. Issuer rating = value-weighted mean of its bond ratings. Issuers carry equal weight within a quintile. Quintiles of D/E are formed within each of five rating buckets (Aaa/Aa, A, Baa, Ba, B). Formations end of each February 1993–2017 (stop at 2017 for the 36-month window, note 5 p. 506).

**OAS on D/E cross-section** (p. 471):

```latex
OAS_{i,t} = \sum_j a_{j,t}\, 1\{industry_i = j\} + \beta_t \,(Debt/EBITDA)_{i,t} + \varepsilon_{i,t}
```
Intuition: within an industry, more debt per unit of earnings should mean a wider spread. Industries are Barclays level 3 fixed income sectors (note 6, p. 506). The text says Debt-to-EBITDA. Our reading: Debt / SustEBITDA, the same D/E as in SPiDER. Fama-MacBeth t = mean(β) / (sd(β)/√T).

**DTS volatility model** (p. 478, from Ben Dor et al. 2007):

```latex
\sigma_{\text{excess}} \approx D \cdot S \cdot \sigma^{rel}_{spread}
```
Intuition: excess return volatility is proportional to DTS, because relative spread volatility is near equal across bonds.

DTS-implied volatility of quintile i from Q1 (p. 480):

```latex
\sigma^{DTS}_{Q_i} = \frac{DTS_{Q_i}}{DTS_{Q_1}}\,\sigma_{Q_1}, \quad i = 2,\dots,5
```

DTS risk-adjusted return (p. 481), DTS at start of month t:

```latex
r^{adj}_{Q_i,t} = \frac{DTS_{Q_1,t}}{DTS_{Q_i,t}}\; r^{xs}_{Q_i,t}, \quad i = 2,\dots,5
```
Intuition: scale each quintile down to Q1's market risk, like dividing an equity return by beta (note 7, p. 506).

**Trend-adjusted EBITDA** (Table 14.10 note, p. 487):

```latex
\log(EBITDA_{i,y}) = \alpha_i + \beta_i \log(\text{age}_{i,y}) + e, \qquad \text{TrendEBITDA}_i = \exp\!\big(\hat\alpha_i + \hat\beta_i \log(\text{age}_i + 1)\big)
```
Intuition: next year's EBITDA from the issuer's own growth path. Fit each year on the past 10 years, at least 6. "1%, 5%, 10%-sig. cutoff": use the trend value only if the slope p-value is below the cut-off. Otherwise use SustEBITDA. "All": always use the trend value.

**Alternative fundamental risk measures** (p. 487):
- Interest coverage = SustEBITDA / interest expense. The signal is `OAS / (1 / coverage)`.
- Debt-to-cash = (short-term + long-term debt) / cash holdings. The signal is `OAS / (debt/cash)`.

**Transaction cost** (p. 498, Table 14.17 note p. 499): annual cost = average annual turnover × average LCS of the Q5 issuers. LCS = cost of an immediate institutional round trip, in % of price.

### Implementation steps
1. **Formation date.** End of February each year t, 1993 to 2019 (p. 475).
2. **Universe.** Index bonds at end of February. Apply the four filters above. Map bonds to issuers (Compustat gvkey).
3. **Fundamentals.** For each issuer take the fiscal year (or the last four quarters) that ends October to December of t−1. Compute Debt. Compute SustEBITDA from the last 10 annual EBITDA values, at least 6.
4. **Issuer OAS.** Market-value-weighted OAS over the issuer's index bonds at end of February.
5. **SPiDER.** OAS / (Debt / SustEBITDA).
6. **Rank.** Sort issuers into quintiles of SPiDER **within each industry** (p. 473, p. 475). The book does not name the industry level for the sort. Figure 14.7 (p. 485) shows six groups: industrials, consumer cyclicals, consumer noncyclicals, TMT, energy, utilities. The regression uses Barclays level 3 (note 6). Our reading: Barclays level 3 industry for the sort.
7. **Portfolios.** Long Q5 (high SPiDER), short Q1. Equal weight per issuer at formation (p. 475). The book does not say how weight splits across an issuer's bonds. Our reading: the issuer return is the market-value-weighted excess return of its index bonds.
8. **Holding.** Hold 12 months, to next February, regardless of rating changes or index exit (p. 475). Monthly returns are compounded inside the year.
9. **Returns.** Monthly excess return over duration-matched Treasuries. Report annualised mean, volatility, IR, worst month, maximum drawdown, correlation with the benchmark.
10. **Diagnostics.** Quintile characteristics (Tables 14.5–14.6). DTS-implied against realised volatility. DTS-adjusted IR by quintile.
11. **Carry checks** (p. 482). (a) Pure carry: long top OAS quintile, short bottom OAS quintile. (b) OAS-neutral: within each industry, split issuers into 4 OAS buckets. Within each industry × OAS bucket, split into top and bottom SPiDER halves. Long the top halves, short the bottom halves (note 8, p. 506).
12. **Rating split** (p. 484). Within each rating × industry bucket, split into top and bottom halves of SPiDER. Long top, short bottom. Report per rating (A/A+, Baa, Ba, B).
13. **Variants.** Window 1, 3, 5, 7 years. Trend EBITDA. Interest coverage. Debt-to-cash. I/B/E/S forward EBITDA (from March 2003).
14. **Practical variants.**
    - Sell issuers when they leave the index. Redistribute their weight evenly to remaining issuers (Table 14.12 note, p. 490).
    - Value weights. Value weights with a 4% issuer cap.
    - Quarterly rebalance: (a) update OAS only, D/E from last year end. (b) update OAS and the latest quarterly statements, with the 2-month lag kept.
    - 24-month holding, Jegadeesh-Titman overlap: two subportfolios, one formed in odd years, one in even years. Each starts at 50% weight. Each February close the subportfolio formed two years ago and open a new one (p. 493).
15. **Costs.** From March 2007. Cost = turnover × mean LCS of Q5. Benchmark costs zero.
16. **Tracking portfolio** (pp. 500–501). Annual, each end of February.
    - Tracking universe: senior bonds, maturity > 3 years, notional above the 25th percentile of the index notional.
    - One bond per issuer. If the issuer has bonds younger than 2 years, drop older ones. Then keep the bond with duration closest to the industry average.
    - Optimise: maximise the weighted average SPiDER. Bond cap 1% (2% when names are too few). Match benchmark sector weights and index DTS exposure. Variant: also match OAS. Variant: 2% cap.

### Results
**D/E predicts downgrades within rating (Table 14.3, p. 470).** Q5 − Q1 notch change (positive = more downgrade):

| Rating | 12m | 24m | 36m |
|---|---|---|---|
| Aaa/Aa | 0.172 | 0.388 | 0.601 |
| A | 0.072 | 0.079 | 0.076 |
| Baa | 0.082 | 0.259 | 0.450 |
| Ba | 0.086 | 0.110 | 0.001 |
| B | 0.074 | 0.207 | 0.386 |

**D/E explains OAS (Table 14.4, p. 473).** Mean slope 0.05 (t 5.48, adj. R² 85%) in IG and 0.10 (t 6.77, adj. R² 86%) in HY. One standard deviation of D/E adds 10.7 bp in IG and 28.3 bp in HY (p. 471). Slopes are positive every year except HY 2015 and 2016 (p. 471). Correlation of changes in aggregate OAS and D/E: 0.30 IG, 0.39 HY (p. 471). They decouple in 2008–2009 (illiquidity, p. 471).

**Quintile levels (Table 14.5, p. 473).** SPiDER Q1 to Q5: IG 0.20 → 1.40, HY 0.33 → 2.11. D/E Q1 to Q5: IG 5.50 → 1.34, HY 9.67 → 2.67. OAS Q1 to Q5: IG 1.12% → 1.88%, HY 3.18% → 5.62%. The D/E fall drives SPiDER more than the OAS rise.

**Quintile characteristics (Table 14.6, p. 474).** HY Q1 to Q5: OAS 358 → 542 bp, duration 4.48 → 4.03, DTS 15.77 → 21.19, bond MV $1.44bn → $0.62bn, EBITDA vol/debt 10% → 22%. IG Q5 − Q1: OAS +59 bp, DTS +3.52, EBITDA vol/debt +23 points.

**Main strategy (Table 14.7, p. 476).**

| | IG L−S | IG Q5 | IG bench | HY L−S | HY Q5 | HY bench |
|---|---|---|---|---|---|---|
| Ret %/yr | 1.61 | 1.83 | 0.63 | 2.62 | 3.64 | 2.21 |
| Vol %/yr | 1.38 | 3.91 | 4.08 | 3.60 | 7.68 | 8.34 |
| IR | 1.17 | 0.47 | 0.16 | 0.73 | 0.47 | 0.27 |
| Worst month % | −1.76 | −8.71 | −9.04 | −4.37 | −15.08 | −15.26 |
| MaxDD % | −4.68 | −23.03 | −23.23 | −9.50 | −33.54 | −39.43 |
| Corr. bench | 0.10 | 0.93 | | −0.08 | 0.87 | |

- Q5 over benchmark: IG 1.20%/yr, IR 0.78. HY 1.42%/yr, IR 0.35 (p. 476).
- Equity comparison, same period: book-to-market IR 0.60, earnings-to-price IR 0.32 (p. 476).
- Returns and IR rise monotonically Q1 to Q5 (Figure 14.4, p. 479).

**Carry and OAS-neutral (Table 14.8, p. 483).**

| | IG SPiDER | IG carry | IG OAS-neutral | HY SPiDER | HY carry | HY OAS-neutral |
|---|---|---|---|---|---|---|
| Carry (BOM OAS gap, %) | 0.59 | 1.53 | 0.05 | 1.84 | 4.52 | 0.23 |
| Ret %/yr | 1.61 | 1.29 | 0.34 | 2.62 | 1.06 | 0.97 |
| IR | 1.17 | 0.38 | 0.52 | 0.73 | 0.16 | 0.57 |
| MaxDD % | −4.68 | −21.06 | −1.80 | −9.50 | −34.29 | −3.44 |
| Corr. bench | 0.10 | 0.75 | −0.42 | −0.08 | 0.65 | −0.36 |

The OAS-neutral sort uses halves, not quintiles. The book says this dilutes the signal (note 9, p. 507).

**By rating (Table 14.9, p. 484), top half minus bottom half within rating × industry.**

| | A/A+ | Baa | Ba | B |
|---|---|---|---|---|
| Carry % | 0.12 | 0.35 | 0.60 | 1.31 |
| Ret %/yr | 0.40 | 0.75 | 0.71 | 1.70 |
| Vol %/yr | 0.63 | 1.00 | 2.36 | 2.69 |
| IR | 0.64 | 0.75 | 0.30 | 0.63 |
| MaxDD % | −1.81 | −3.81 | −9.96 | −5.88 |

**By industry (Figure 14.7, p. 485).** Q5 − Q1 is at least 128 bp/yr in IG and 134 bp/yr in HY in every industry. IR range 0.31–0.89 in IG, 0.24–0.68 in HY (p. 484).

**Alternative definitions (Table 14.10, pp. 486–487), L−S IR.**

| Variant | IG IR | HY IR | Rank corr. with original IG / HY |
|---|---|---|---|
| Original (10y) | 1.17 | 0.73 | 1 / 1 |
| 1-year EBITDA | 1.02 | 0.55 | 0.82 / 0.65 |
| 3-year | 1.08 | 0.77 | 0.90 / 0.80 |
| 5-year | 1.22 | 0.61 | 0.95 / 0.89 |
| 7-year | 1.18 | 0.63 | 0.98 / 0.96 |
| Trend, 1% cut | 1.12 | 0.80 | 0.83 / 0.77 |
| Trend, 5% cut | 1.08 | 0.83 | 0.83 / 0.74 |
| Trend, 10% cut | 1.01 | 0.77 | 0.83 / 0.73 |
| Trend, all | 1.09 | 0.74 | 0.82 / 0.69 |
| OAS × coverage | 1.05 | 0.55 | 0.82 / 0.86 |
| OAS / (debt/cash) | 0.76 | 0.95 | 0.44 / 0.30 |

Debt-to-cash has the lowest correlation with the original (0.44 IG, 0.30 HY), so it may add value in a blend (p. 485). In HY it has the highest IR (0.95).

**Analyst forecasts (Table 14.11, p. 488), March 2003–February 2020.** IG: SPiDER IR 1.06, forecast EBITDA IR 0.97, return correlation 0.85. HY: SPiDER IR 0.66, forecast IR 0.61, correlation 0.75.

**Index exit (Table 14.12, p. 490).** Selling on index exit: IG IR 1.17 → 1.10, HY 0.73 → 0.64. Mean issuers per month in both legs: IG 190, HY 129 (117 with sales).

**Weights (Table 14.13, p. 491), L−S IR.** Equal weight IG 1.17, HY 0.73. Value weight IG 0.58, HY 0.57. Value weight with 4% cap IG 0.82, HY 0.59. Long-only IR changes little (IG 0.47 → 0.37–0.40, HY 0.47 → 0.40–0.41).

**Signal decay (Figure 14.8, p. 492).** The L−S return is positive in all 8 quarters after formation. It is highest in quarter 1, has a small bump in quarter 5, and is near zero in quarter 8. The book reads this as a signal life of about two years.

**Quarterly rebalance (Table 14.14, p. 494), Q5 − Q1.**

| | Original | Quarterly OAS | Quarterly OAS + statements |
|---|---|---|---|
| IG ret / IR | 1.61 / 1.17 | 1.80 / 1.24 | 1.89 / 1.33 |
| HY ret / IR | 2.62 / 0.73 | 2.99 / 0.81 | 2.90 / 0.76 |

Table 14.14 prints a Q5 − Q1 volatility of 1.14 (IG) and 3.02 (HY) for the original. These do not match Table 14.7 (1.38 and 3.60) or the printed IR. Use Table 14.7 for the original.

**24-month holding (Table 14.15, p. 496).** IG L−S 1.29%/yr, vol 1.17, IR 1.10. HY L−S 2.38%/yr, vol 3.13, IR 0.76. HY Q5 long 3.97%, IR 0.52.

**Persistence (Table 14.16, p. 497), % of issuers.** IG Q5 stays in Q5 after 1 year: 56%. After 2 years: 42%. IG Q1: 63% and 49%. HY Q5: 48% and 34%. HY Q1: 53% and 37%. Exit from universe after 1 year: 8–25%. After 2 years: 13–40%.

**Turnover (p. 498).** Annual turnover of Q5: 43% (IG) and 55% (HY) with 12-month rebalance. 28% and 35% with 24-month.

**Costs (Table 14.17, p. 499), March 2007–February 2020.**

| | IG 12m | IG 24m | HY 12m | HY 24m |
|---|---|---|---|---|
| Q5 gross ret %/yr | 2.11 | 1.96 | 3.46 | 3.88 |
| Q5 mean LCS % | 1.21 | 1.20 | 1.84 | 1.82 |
| Turnover | 40% | 26% | 50% | 32% |
| Cost %/yr | 0.48 | 0.31 | 0.93 | 0.59 |
| Net ret %/yr | 1.63 | 1.65 | 2.53 | 3.29 |
| Net over bench %/yr | 0.58 | 0.59 | −0.29 | 0.48 |
| Net IR over bench | 0.33 | 0.37 | −0.07 | 0.13 |

Benchmark gross: IG 1.05%/yr, HY 2.82%/yr, both cost free. HY with 12-month rebalance loses to the benchmark after cost. HY with 24-month rebalance wins.

**Tracking portfolios (Tables 14.18–14.19, pp. 502–504).** About 104 bonds in IG and 92 in HY. Turnover 40% IG, 49% HY.

| | IG 1% cap | IG 1% + OAS match | IG 2% | HY 1% | HY 1% + OAS | HY 2% |
|---|---|---|---|---|---|---|
| Excess over bench %/yr | 0.62 | 0.20 | 0.89 | 0.20 | 0.30 | 0.38 |
| Tracking error %/yr | 1.21 | 1.02 | 1.44 | 2.40 | 2.38 | 2.80 |
| IR | 0.51 | 0.19 | 0.62 | 0.08 | 0.13 | 0.14 |

### Robustness and variants
- Sustainable EBITDA window 1 to 7 years, trend EBITDA, forward EBITDA. IR holds in IG (1.01–1.22). HY varies more (0.55–0.83).
- Alternative risk measures: interest coverage, debt-to-cash. Both work. Debt-to-cash is the most distinct.
- DTS-matched quintiles (Figure 14.6, p. 481). Q2–Q5 IR falls, but Q5 still beats Q1 by a wide margin.
- OAS-neutral sort. IR 0.52 IG, 0.57 HY with carry near zero.
- Every rating bucket and every industry has a positive edge.
- Index-exit rule, value weights, caps, quarterly and 24-month rebalance, costs, index tracking. The sign holds in all. HY after cost holds only with 24-month rebalance.

### Limits and caveats
- Annual signal on Barclays index OAS and market values. We have no Barclays OAS, no index membership, no LCS.
- HY sample is Ba and B with price ≥ $50. CCC and distressed bonds are out. Our HY panel keeps CCC.
- Results before cost except Table 14.17. Cost uses LCS from 2007 only, with a cost-free benchmark.
- Only issuers with fiscal periods ending October–December enter. This drops some issuers. It also aligns the cross-section.
- HY tracking IR is low (0.07–0.14). The long-short HY IR (0.73) needs shorting HY bonds, which is costly.
- Table 14.14 has internal inconsistencies between volatility and IR.
- The book does not state the industry level for the quintile sort or how to treat non-positive EBITDA.

### Implementation in this repo
**Mapping.** Methodology 7.4 (spread per unit of risk, the SPiDER paragraph) and estimate E15 in `hy/groups.py`. Code: `hy/peers.py`, `peer_signals` (columns `spider`, `spider_<level>`), `sustainable_ebitda` (10 years, at least 6, `SUST_YEARS`, `SUST_MIN`), `live_peers` (`spider_pct`). Data: `hy/sources/peer_data.py` `annual_ebitda` (`oibdp`, `debt`). Section 11 backtest design applies.

**What exists and how it differs.**
1. Rank scope. `spider` is ranked across all sectors (absolute). The book ranks quintiles within industry. `spider_sr` (log SPiDER minus the sector × rating peer median) is nearer the book. A plain within-GICS-sector rank of `spider` is the book version.
2. Spread. We use the issuer median TRACE G-spread over its bonds. The book uses the market-value-weighted OAS. The panel has no amount outstanding, so the median stays. G-spread ignores the call option. For callable HY bonds this overstates spread. Proxy: use bonds with more than 3 years to maturity and price ≤ 105 only, to reduce call option effects.
3. Timing. The book forms once a year, end of February. Our `peer_signals` runs monthly. Keep monthly scores, but test the book's annual February schedule as the primary case.
4. Filters. The book drops CCC and bonds below $50. We keep them. Apply the book filters in the primary test. Report CCC as a separate cell.
5. Financials: we drop GICS 40 and 60. This matches the book.

**Lag rule (no look-ahead).** Annual EBITDA and debt from Compustat: `available_at` = datadate + 90 days (`ANNUAL_LAG_DAYS`, `hy/sources/peer_data.py`). The book uses only 2 months. Our 90 days is stricter. Keep it. At formation date t use only fiscal years with `available_at ≤ t`. The latest annual figure must be at most 18 months old (`SUST_STALE_DAYS = 550`). Spread: TRACE month-end G-spread, `available_at` = the last trade time of the month.

**Falsifiable test.**
- Signal: `spider_ind` = within-GICS-industry-group quintile of `spider`, formed each end of February. HY bonds rated B or above, price ≥ $50, issuers with ≥ 6 years of EBITDA.
- Horizon: 12 months, equal weight per issuer, held to next February. Variant: 24-month overlapping portfolios.
- Metric: Q5 − Q1 annual excess return over duration-matched Treasuries, IR, and the 12-month rank IC beyond spread level.
- Pass: Q5 − Q1 IR ≥ 0.40 (about half the book's HY 0.73) and a 12-month beyond-spread IC above the current absolute `spider` (+0.032), with t ≥ 2. The sign must be positive in at least 3 of the 4 cycle windows (2008, 2015, 2020, 2022). After a 24-month overlap and a cost of turnover × the TRACE effective bid-ask, the Q5 excess over the B-and-above benchmark must stay positive. Fail: keep E15 at its current weight or lower it.

---

## Chapter 15. Equity Momentum in Credit (PDF pp. 511–542)

Book page = PDF page − 28. Every page cited below is a PDF page. Rotated tables 15.3–15.8, 15.11 and 15.15 were read from page images.

**Question.** Does an issuer's recent stock return predict the next-month excess return of its bonds?

**Answer.** Yes. In US IG, 1993–2017, long Q5 minus short Q1 of a combined 1-, 3- and 6-month stock return signal earns 6.34%/yr at IR 1.56 before cost (Table 15.1, p. 515). It is stronger in Baa and HY (HY 15.9%/yr, IR 1.74, Table 15.2, p. 516), contra-cyclical, and not explained by bond illiquidity. Costs remove the edge of a high-turnover version. A buffered long-only version keeps 0.78–0.91%/yr over the index after cost (Table 15.15, p. 539).

### Data
- Universe: all bonds in the Bloomberg Barclays US Corporate IG and US High Yield indices, December 1992 to May 2017 (p. 513). Results: January 1993 to May 2017.
- Bond-to-stock mapping: Barclays historical mapping (Ben Dor and Xu 2015, note 6 p. 541). Issuers with no equity data are out. Private companies are out (notes 1, 7, p. 541).
- Returns: monthly excess returns over duration-matched Treasuries, from the Barclays indices (note 5, p. 541).
- Equity: monthly stock prices on the last business day of each month (note 18, p. 542). Price returns (the book says "equity price return", p. 513). Daily prices only for the lag test.
- Liquidity: Barclays TES from January 2007 (note 17, p. 542). Barclays LCS for costs.
- Factors: Fama-French market, SMB, HML, MOM (Ken French library), and AQR QMJ (note 14, p. 541).
- IG tables compare with the US Corporate IG index. The HY row in Table 15.2 uses the HY index bonds.

### Definitions and formulas
**Illustration signal** (p. 513): 3-month stock price return. The book calls 3 months arbitrary (p. 514).

**Main signal, EMC** (p. 514, note 9 p. 541): equal-weight combination of the 1-, 3- and 6-month stock returns, each scaled by the square root of its length.

```latex
EMC_{i,t} = \frac{1}{3}\left(\frac{r^{eq}_{i,t-1m \to t}}{\sqrt{1}} + \frac{r^{eq}_{i,t-3m \to t}}{\sqrt{3}} + \frac{r^{eq}_{i,t-6m \to t}}{\sqrt{6}}\right)
```
Intuition: return volatility grows with the square root of time. The scaling puts the three horizons on one footing. A six-month trend that continues scores higher than a one-month jump (p. 514).

- The note says "normalize them by the square root of period lengths" (note 9, p. 541). The text says "rescaled for different lengths" (p. 514). Chapter 16 note 4 (p. 552) says "normalized by the lengths" and reports sector EMC in %/m. The two chapters may differ. Our reading for chapter 15: square root, as note 9 states.
- Returns are compounded price returns over each window, ending at the last business day of month t. No skip month.
- Equity return type: price return (p. 513). The book does not mention dividends.

**Issuer-specific EMC** (Table 15.14, note 19 p. 542). Regress each stock's monthly price return on the S&P 500 return over a rolling 12-month window. Take the residuals. Compound residuals over 1, 3 and 6 months, rescale as above, average.

```latex
\varepsilon_{i,m} = r_{i,m} - \hat\alpha_{i} - \hat\beta_{i}\, r_{SP500,m}, \qquad \hat\beta_i \text{ from months } t-11 \dots t
```
Intuition: remove the market part, so a market rebound does not flip the whole signal (Haesen et al. 2017).

**Turnover rule** (Appendix 15.2, p. 538). Buy when the bond's EMC percentile enters the buy zone. Sell when it falls into the sell zone. Hold in between.

**Survey, regimes and liquidity buckets.**
- S&P 500 regimes (Table 15.4): months split by S&P 500 monthly return into bottom 30%, mid 40%, top 30%.
- Credit drawdown episodes (p. 523): Aug 1997–Oct 1998, Jan–Dec 2000, Apr–Oct 2002, Mar 2007–Nov 2008, May–Nov 2011, Aug 2014–Feb 2016. Other months = recovery.
- Fed cycles (p. 526): easing = months in which the fed funds target fell. After 2008 also months with Fed asset growth > 25% p.a. (2009, 2013, note 16 p. 542). Tightening = target rose. Each split in early and late halves. "On-hold" months are pre-easing or pre-tightening.
- TES buckets: 1–3 liquid, 4–7, 8–10 illiquid (p. 529).
- Autocorrelation buckets: autocorrelation of the bond's monthly excess returns over the prior 12 months. Bottom 30%, mid 40%, top 30% (p. 530).

### Implementation steps
1. **Month end t.** Take index bonds at the start of month t+1 with a mapped listed issuer.
2. **Signal.** For each issuer compute the 1-, 3- and 6-month stock price returns to the last business day of month t. Compute EMC with the square-root scale. Assign the issuer EMC to each of its bonds.
3. **Sort.** Sort bonds into quintiles (main strategy) or deciles (Figure 15.3) of EMC. The sort is across the whole IG universe, not within sector.
4. **Weights.** The book does not state the weight inside a quintile. Our reading: market-value weights, the Barclays convention. Chapter 13 states market weights for its sorts.
5. **Strategy.** Long Q5, short Q1. Rebalance monthly (note 12, p. 541). Hold one month.
6. **Returns.** Bond excess return over duration-matched Treasuries for month t+1. Annualise mean and volatility. IR = mean / volatility.
7. **Splits.** Rating: Aaa–A (A3 and above), Baa, HY. Subperiods: Jan 1993–Jun 2007, Jul 2007–May 2017. TES buckets (2007–2017). Autocorrelation buckets. In each split, form EMC quintiles inside the bucket.
8. **Cohort decay.** Fix the above-median and below-median cohorts at formation. Track their return spread for 6 months (Figure 15.4).
9. **Selection risk.** Draw 100 bonds at random from the top 30% and from the bottom 30% of EMC. Match index weights by sector (financials, nonfinancials), rating (A3–Aaa, Baa3–Baa1) and maturity (1–5y, 5+y). Repeat 5,000 times (p. 520).
10. **Combination with ESP** (pp. 531–532). High ESP = ESP score 6–10. Low ESP = 1–5. High EMC = above-median issuer EMC. Form four buckets: HH, HL, LH, LL. Report HH against the index.
11. **Long-only with buffers** (Table 15.15, Feb 2007–May 2017, IG). Rebalance at each month end.
    - EMC1: hold only top-decile bonds. Buy on entry to the top 10%, sell on exit.
    - EMC2: buy on entry to the top 10%, sell only when the bond falls into the bottom 10% (table header). The text says "drops below the 90th percentile" (p. 538). The table header and the turnover drop (73% → 8.9% a month) support "bottom 10%".
    - EMC3: as EMC2, but buy only liquid bonds (TES 1–3).
    - Cost: Barclays LCS of each trade.
12. **Lag test.** Stock prices lagged 1, 2 or 3 business days before month end (Table 15.13).

### Results
**Deciles (Figure 15.3, p. 513, text p. 514), 3-month signal.** D1 −4.7%/yr, D10 +4.01%/yr, index 0.67%/yr. D1 volatility is about twice the others.

**Main strategy (Table 15.1, p. 515).**

| Period | Q1 | Q5 | Q5−Q1 ret / vol / IR | Q5−Index ret / IR |
|---|---|---|---|---|
| Jan 1993–May 2017 | −2.83 | 3.50 | 6.34 / 4.07 / 1.56 | 2.84 / 1.63 |
| Jan 1993–Jun 2007 | −1.50 | 2.53 | 4.03 / 2.34 / 1.72 | 2.11 / 1.77 |
| Jul 2007–May 2017 | −4.78 | 4.93 | 9.71 / 5.59 / 1.74 | 3.89 / 1.71 |

**By rating (Table 15.2, p. 516), Q5−Q1.**

| | Q1 | Q5 | Q5−Q1 | Vol | IR |
|---|---|---|---|---|---|
| Aaa–A | −1.88 | 2.02 | 3.9 | 4.72 | 0.83 |
| Baa | −4.11 | 4.74 | 8.8 | 4.72 | 1.87 |
| HY | −5.50 | 10.38 | 15.9 | 9.11 | 1.74 |

The text says HY earns 19.9%/yr (p. 516). The table and the conclusion (p. 534) say 15.9%. Use 15.9.

**Signal decay (Table 15.3, p. 517, and Figure 15.4, p. 518).**
- Only 17% of D10 issuers stay in D10 after 3 months. D1 stays at 16%.
- The above-median set loses 31% of issuers after 1 month and 52% after 6 months.
- A fixed high-minus-low cohort earns 35, 22 and 19 bp in months 1, 2, 3. It earns 95 bp cumulative over 6 months, about 80% of it in the first 3 months (pp. 518–519).

**Selection risk (Figure 15.5, p. 519).** For one month (May 2017), top-30% and bottom-30% 100-bond portfolios overlap a lot. Over 12 months (Jun 2016–May 2017), they barely overlap.

**Credit exposure by equity regime (Table 15.4, p. 522).** Net Q5−Q1 OAS: −0.31% in the worst 30% of S&P months, −0.06% in mid months, +0.14% in the best 30%. Net DTS: −0.94, −0.38, +0.45. The strategy is short spread in sell-offs.

**Correlations (Table 15.5, p. 522).** EMC with US Corp excess −43%, equity market −38%, SMB −8%, HML −9%, MOM +9%, QMJ +31%, Treasuries +11%.

**Credit drawdowns (Table 15.6, p. 524), cumulative %.**

| Episode | US Corp IG | EMC Q5−Q1 |
|---|---|---|
| Aug 1997–Oct 1998 | −5.2 | 6.8 |
| Jan–Dec 2000 | −4.4 | 6.5 |
| Apr–Oct 2002 | −5.7 | 12.4 |
| Mar 2007–Nov 2008 | −24.2 | 35.4 |
| May–Nov 2011 | −5.8 | 7.0 |
| Aug 2014–Feb 2016 | −5.8 | 16.0 |

**Regimes (Table 15.7, p. 525), Jan 1993–Apr 2017.** In drawdowns EMC earns 11.53%/yr (IR 2.13). The index loses 8.07%/yr. In recoveries EMC earns 4.30%/yr (IR 1.34). The index earns 4.12%/yr.

**Fed cycles (Table 15.8, p. 528).**

| Regime | Months | EMC ret %/yr | EMC IR | Index ret |
|---|---|---|---|---|
| On-hold pre-easing | 42 | 2.61 | 3.73 | −0.87 |
| Early easing | 40 | 8.20 | 2.79 | −1.52 |
| Late easing | 38 | 19.06 | 2.13 | 1.97 |
| On-hold pre-tightening | 103 | 4.02 | 1.82 | 1.59 |
| Early tightening | 46 | 4.51 | 2.41 | 1.58 |
| Late tightening | 24 | 3.06 | 1.55 | −0.77 |
| All | 293 | 6.34 | 1.56 | 0.67 |

**Liquidity (Table 15.9, p. 529), Feb 2007–May 2017, Q5−Q1.** TES 1–3: 9.45%/yr, IR 1.48. TES 4–7: 9.41%, IR 1.75. TES 8–10: 8.81%, IR 1.99. The return is flat across liquidity. Only volatility falls.

**Autocorrelation (Table 15.10, p. 530), Q5−Q1.** Low: 6.55%/yr, IR 1.15. Mid: 5.85%, IR 1.58. High: 6.18%, IR 1.26.

**With ESP (Table 15.11, p. 533), over the US Corp IG index, 1993–2017.**

| | Excess over index %/yr | TE | IR | Corr. with index |
|---|---|---|---|---|
| High ESP | 0.85 | 0.56 | 1.54 | 46% |
| High EMC | 1.43 | 0.99 | 1.44 | −30% |
| HH | 2.49 | 1.16 | 2.14 | −12% |

HH absolute: 3.15%/yr, IR 0.76. HH over index: 1.59%/yr (IR 2.28) to Jun 2007, 3.79%/yr (IR 2.46) after.

**Formation period (Table 15.12, p. 535), Q5−Q1.** 6-month 4.36%/yr (IR 0.85). 3-month 5.59% (IR 1.18). 1-month 4.85% (IR 1.28). Combined 6.34% (IR 1.56).

**Lag (Table 15.13, p. 536).** Price lag 0, 1, 2, 3 business days: Q5−Q1 6.43, 5.83, 5.89, 6.08%/yr. IR 1.56, 1.50, 1.37, 1.43.

**Issuer-specific EMC (Table 15.14, p. 537).** Q5−Q1 6.04%/yr, IR 1.40 (against 1.56 for total returns). Q5 over index 2.85%/yr, IR 1.50. Slightly worse. No gain.

**Long-only with costs (Table 15.15, p. 539), IG, Feb 2007–May 2017.**

| | EMC1 | EMC2 | EMC3 (liquid) |
|---|---|---|---|
| Turnover %/month | 73.3 | 8.9 | 8.9 |
| Cost bp/month | 76.8 | 8.4 | 7.4 |
| Over index before cost %/yr | 6.34 | 1.79 | 1.79 |
| IR before cost | 1.90 | 1.32 | 1.32 |
| Over index after cost %/yr | −2.87 | 0.78 | 0.91 |
| IR after cost | −1.05 | 0.59 | 0.70 |

Index 0.97%/yr, volatility 5.89%. EMC3 absolute volatility after cost 5.21%.

### Robustness and variants
- Formation period 1, 3, 6 months and combined. All work. Combined is best.
- Stock price lag of 1–3 days. The edge holds.
- Issuer-specific (market-beta-removed) momentum. Slightly worse.
- TES buckets and autocorrelation buckets. The edge does not depend on bond illiquidity.
- Subperiods, rating buckets, regimes. Positive in all.
- Combination with ESP. HH beats either alone.
- Buffered long-only portfolios. Positive after cost.

### Limits and caveats
- All results except Table 15.15 are before cost. The 1-month holding needs high turnover (73%/month for a top-decile hold).
- Shorting Q1 corporate bonds is often not feasible (p. 537).
- The quintile weighting scheme is not stated.
- Signal scaling may differ between chapter 15 (square root) and chapter 16 (length).
- HY evidence is one row (Table 15.2). All other tables are IG.
- Barclays data we cannot get: index membership, OAS, TES, LCS, the Barclays bond-equity map.
- Contra-cyclical net spread: the strategy can lose at market turning points (Haesen et al. 2017, p. 536).

### Implementation in this repo
**Mapping.** Methodology 7.4 (OneScore paragraph) and Section 8 composite through estimate E16 in `hy/groups.py`. A standalone EMC fits S2 (fundamental momentum) only as a market-side proxy. Code: `hy/peers.py` `equity_momentum` (`EMC_MONTHS = 3`) and `onescore`. Data: `hy/sources/peer_data.py` `equity_monthly` (Compustat `comp.secm` monthly total return `trt1m`, dividends included, from 2007, `available_at` = datadate + 1 day. CRSP on this licence ends December 2025, so the code does not use it). Section 11 backtest design applies.

**What exists and how it differs.**
1. Horizon. We use a 3-month compounded return. The book's main signal is the combined 1-, 3-, 6-month signal with square-root scale. Add `equity_momentum_combined` that computes the three windows and averages `r_k / sqrt(k)`. Require all 6 monthly returns.
2. Return type. We use total return (`trt1m`, dividends included). The book uses price return. The difference is the dividend yield. Keep total return. Record it as our choice. The equity history starts in 2007, so the 6-month window is complete from mid-2007.
3. Sort scope. The book's main sort is across the universe, not within sector. Our OneScore ranks EMC within GICS sector. Chapter 16 shows the across-sector part adds about 30% of the return. Test both.
4. Holding. The book rebalances monthly and holds one month. Our tests use 6- and 12-month horizons. Add a 1-month and a 3-month horizon for EMC.
5. Weights. No amount outstanding in the panel. Use equal weights, one bond per issuer.
6. HY evidence is the book's strongest (IR 1.74). Our TRACE HY panel is the right place to test it.

**Lag rule (no look-ahead).** Monthly equity returns: `available_at` = datadate + 1 day. A decision at date t uses returns with `available_at ≤ t`. The last window ends at the last month end before t. Bond return starts at the first TRACE price after t. The book shows that a 1–3 day lag keeps the edge, so the 1-day rule is safe.

**Falsifiable test.**
- Signal: `emc_c` = combined 1-, 3-, 6-month price-scaled signal, issuers with a `comp.secm` primary US issue, ranked across the whole HY panel each month end.
- Horizon: 1 month and 3 months.
- Metric: Q5 − Q1 equal-weight excess return over duration-matched Treasuries, IR, and the monthly rank IC beyond spread level.
- Pass: 1-month Q5 − Q1 IR ≥ 0.8 (about half the book's HY 1.74), and the combined signal beats the current 3-month `emc` on the 1-month beyond-spread IC with t ≥ 2. The return must be positive in the 2008, 2020 and 2022 drawdown windows (the book's contra-cyclical claim). After a cost of turnover × the TRACE effective half-spread, a buffered long-only version (buy top 10%, sell bottom 10%) must beat the equal-weight HY panel. Fail: keep `EMC_MONTHS = 3` and leave E16 unchanged.

---

## Chapter 16. Corporate Sector Timing Using Equity Momentum (PDF pp. 543–554)

Book page = PDF page − 28. Every page cited below is a PDF page. The chapter text ends on p. 552. Pages 553–554 are the part title "Size Effect". Rotated tables 16.1, 16.2 and 16.3 were read from page images.

**Question.** Does the average equity momentum of a bond sector predict that sector's next-month excess return?

**Answer.** Yes, 2007–2017, before cost. The market-weighted top 5 of 15 sectors by equity momentum beat the index by 2.38%/yr in US IG, 1.77%/yr in Euro IG and 4.04%/yr in US HY, all at IR above 1 (Table 16.3, p. 551). Sector rotation is 24–35% of the issuer-level EMC strategy's outperformance over the index (p. 547).

### Data
- Universes: Bloomberg Barclays US Corporate IG, Euro Corporate IG, US High Yield (Table 16.2, p. 546).
- Period: November 2007 to October 2017, monthly (Tables 16.1–16.3).
- Returns: excess over duration-matched Treasuries (note 1, p. 552).
- Sectors:
  - Attribution (Tables 16.1–16.2): eight custom sectors from Barclays Level 3: basic and capital goods, consumer cyclical, consumer noncyclical, communications and technology, transportation and energy, utility, banks and brokerage, financial other (Table 16.1, p. 545). The book picks eight so that each sector has enough issuers (note 2, p. 552).
  - Sector timing (Table 16.3): 15 Barclays Class 3 sectors (note 6, p. 552). Figure 16.2 (p. 548) lists technology, insurance, basic, consumer cyclical, electric, capital goods, banking, natural gas, transportation, brokerage, consumer noncyclical, energy, communications, REITs, finance.
- Equity data and bond-equity mapping as in chapter 15.

### Definitions and formulas
**Issuer EMC score** (p. 543). The EMC Scorecard ranks issuers 1 to 10 by equity momentum. Scores are not normalised within sectors (p. 543). Figure 16.1 (p. 544) sorts US IG bonds by score. Portfolios form at the start of each month and hold one month.

**Equity momentum** (note 4, p. 552): "the average of issuer stock price returns over one-, three-, and six-month horizons normalized by the lengths of the respective periods". The book reports sector momentum in %/m (p. 547, Figure 16.2). This reading divides by the length, not the square root:

```latex
EM_{i,t} = \frac{1}{3}\left(\frac{r_{i,1m}}{1} + \frac{r_{i,3m}}{3} + \frac{r_{i,6m}}{6}\right) \quad [\%/\text{month}]
```
Intuition: the average monthly stock return over three windows.

Chapter 15 note 9 (p. 541) says square root. Note 4 here says the method is "consistent with" chapter 15. The two notes conflict. Our reading: chapter 16 uses length (it matches the %/m unit). Test both.

**Sector equity momentum.** The book does not state how issuer momentum aggregates to a sector. Our reading: the market-value-weighted mean of issuer EM over the sector's index issuers:

```latex
EM_{s,t} = \sum_{i \in s} w_{i,t}\, EM_{i,t}, \qquad w_{i,t} = \frac{MV_{i,t}}{\sum_{j \in s} MV_{j,t}}
```
Intuition: the sector's stock-market trend, in the weights of its bonds.

**Sector-neutral EMC** (p. 544, note 3 p. 552). Within each of the eight sectors, long the top 20% (Q5) and short the bottom 20% (Q1) of issuer equity momentum. Aggregate the sector legs with index sector weights, so long and short legs have the same sector weights. Sector DTS contributions can still differ (note 3).

**Sector allocation contribution** (pp. 546–547):

```latex
C^{sector} = R^{EMC}_{unconstrained} - R^{EMC}_{sector\text{-}neutral}
```
Intuition: the return the unconstrained sort earns from its implicit sector bets. The book reports the mean, volatility and IR of this difference.

**Sector return response** (Figure 16.3, p. 548). Regress mean next-month sector excess return (%/m) on sector equity momentum (%/m) across sector cells:
- US IG: y = 0.075x + 0.18 (our reading of the chart labels: the upper line).
- Euro IG: y = 0.05x + 0.13.
- US HY: y = 0.08x + 0.49.

Intuition: 1%/m more equity momentum adds 5–8 bp/m of bond excess return (p. 547).

### Implementation steps
1. **Month end t.** Take index bonds with a mapped listed issuer. Assign each bond to a Class 3 sector (15 sectors) for timing, or to one of the 8 custom sectors for attribution.
2. **Issuer momentum.** Compute 1-, 3-, 6-month stock price returns to month end t. Combine as above (length scale, with square root as a variant).
3. **Sector momentum.** Aggregate issuer momentum to each sector (our reading: market-value weights).
4. **Rank sectors.** Sort the 15 sectors by momentum at the start of month t+1.
5. **Top portfolio.** Hold the top 5 sectors. Inside the portfolio, weight bonds by market value (market-capitalisation weights, p. 549). Rebalance monthly.
6. **Bottom portfolio.** Same, bottom 5 sectors.
7. **Returns.** Month t+1 excess return over duration-matched Treasuries. Report top, bottom, top − bottom and top − index: mean, volatility, maximum drawdown, IR.
8. **Attribution.**
   - Unconstrained EMC: issuer quintiles across the whole universe, top-quintile portfolio.
   - Sector-neutral EMC: issuer quintiles inside each of the 8 sectors, aggregated with index sector weights.
   - Contribution = unconstrained − sector-neutral, for Q5 − Q1 and for Q5 − index.

### Results
**Issuer scores (Figure 16.1, text p. 543), US IG, Nov 2007–Oct 2017.** EMC = 1: −7.2%/yr. EMC = 10: 8.10%/yr. Index 1.43%/yr. The relation is near monotonic.

**Sector-neutral EMC by sector (Table 16.1, p. 545), Q5 − Q1, %/yr (IR).**

| Sector | US IG | Euro IG | US HY |
|---|---|---|---|
| Basic & cap. goods | 6.97 (1.76) | 4.32 (1.35) | 10.96 (2.08) |
| Cons. cyclical | 7.96 (1.36) | 3.68 (1.17) | 17.77 (1.28) |
| Cons. noncyclical | 3.56 (1.93) | 1.91 (1.41) | 5.94 (1.31) |
| Comm. & tech | 7.05 (1.53) | 2.90 (1.10) | 13.54 (1.75) |
| Transport & energy | 7.83 (2.00) | 2.35 (0.79) | 15.96 (1.86) |
| Utility | 3.62 (1.63) | 0.92 (0.38) | 6.89 (1.08) |
| Banks & brokerage | 6.83 (0.66) | 5.48 (1.11) | 30.22 (0.96) |
| Financial other | 10.19 (1.10) | 4.95 (0.92) | 17.09 (0.86) |

**Attribution (Table 16.2, p. 546).**

| | Q5−Q1 unconstrained | Q5−Q1 neutral | Q5−Q1 sector contrib. (IR) | Q5−index unconstrained | Q5−index neutral | Q5−index sector contrib. (IR) |
|---|---|---|---|---|---|---|
| US IG | 10.03 | 6.98 | 3.05 (1.39) | 3.98 | 3.01 | 0.97 (0.69) |
| Euro IG | 5.67 | 4.21 | 1.46 (0.98) | 2.64 | 1.94 | 0.70 (0.79) |
| US HY | 18.73 | 13.20 | 5.52 (1.12) | 9.76 | 6.38 | 3.38 (0.77) |

Sector rotation is 24% to 35% of the Q5 outperformance over the index (p. 547). The conclusion rounds it to about 30% (p. 550).

**Sector dispersion (Figure 16.2, p. 548).** At 31 October 2017, technology momentum was +4.3%/m (US IG) and +3.3%/m (Euro IG). Finance was −5.9%/m and −9.9%/m (p. 547).

**Sector timing (Table 16.3, p. 551).**

| | Index | Top 5 | Bottom 5 | Top−Bottom | Top−Index |
|---|---|---|---|---|---|
| US IG ret %/yr | 1.43 | 3.81 | −0.86 | 4.67 | 2.38 |
| US IG vol | 5.96 | 5.47 | 6.74 | 3.57 | 1.97 |
| US IG MaxDD % | −22.34 | −15.74 | −28.63 | −1.73 | −1.04 |
| US IG IR | 0.24 | 0.70 | −0.13 | 1.31 | 1.21 |
| Euro IG ret | 1.04 | 2.82 | −1.03 | 3.85 | 1.77 |
| Euro IG IR | 0.26 | 0.76 | −0.20 | 1.38 | 1.09 |
| US HY ret | 4.71 | 8.75 | 1.01 | 7.75 | 4.04 |
| US HY vol | 12.00 | 13.25 | 12.51 | 6.57 | 3.83 |
| US HY MaxDD % | −41.55 | −38.28 | −46.71 | −6.57 | −2.81 |
| US HY IR | 0.39 | 0.66 | 0.08 | 1.18 | 1.05 |

**Timing of gains (Figures 16.4–16.5, pp. 549–550).** Most of the outperformance comes in 2008 and 2009. Gains also come in 2011 and 2015–2016. Returns are small in calm years. The HY annual excess over index in 2008 and 2009 is above 12% (chart reading).

### Robustness and variants
- Three universes (US IG, Euro IG, US HY). The sign holds in all.
- Within-sector EMC works in every sector. It is weakest in utilities and consumer noncyclical (low cyclicality), banks in US IG, and financials in HY (p. 544).
- The book does not test costs, other top-N choices, other weights or other horizons for sector timing.

### Limits and caveats
- One 10-year window, November 2007 to October 2017. Most of the gain is the 2008–2009 crisis.
- All results are before transaction costs (p. 550).
- The sector aggregation of momentum and the exact scaling (length or square root) are not stated clearly.
- Barclays Class 3 sectors and index market weights. We use GICS and have no amount outstanding.
- The top-5 portfolio is not DTS-matched to the index. Part of the return may be a beta tilt. The book does not test this.

### Implementation in this repo
**Mapping.** Methodology Section 8, S7 (macro-conditional sector tilt). S7 failed its test and left the composite (decision page `2026-10-24-s7-sector-tilt`). The S7 test found that sector spread alone ranks sector returns (rank IC +0.167, t 3.1). A sector equity momentum tilt is a candidate replacement for S7. No module computes it now. The natural home is a function `sector_momentum` in `hy/peers.py`, next to `equity_momentum`, or in `hy/signals.py` for S7. It uses `peer_data.equity_monthly` and `peer_data.gics_history`.

**Data we have and lack.**
- Have: Compustat monthly total stock returns from 2007 (`comp.secm`), GICS history, TRACE bond returns and G-spreads.
- Lack: Barclays Class 3 sectors, index market weights, Euro IG.
- Proxy: 11 GICS sectors or 24 GICS industry groups in place of 15 Class 3 sectors. Top 4 of 11 sectors, or top 8 of 24 industry groups, keeps the book's one-third share. Equal weight across issuers, one bond per issuer, in place of market weights. Sector momentum = equal-weight mean of issuer EM (market cap weights as a variant, from month-end price × shares in `comp.secm`).

**Lag rule (no look-ahead).** Equity returns: `available_at` = datadate + 1 day. GICS: `available_at` = indfrom. The decision at the first day of month t+1 uses only returns to the end of month t and the GICS code in force at that date. Bond returns start at the first TRACE price after the decision.

**Falsifiable test.**
- Signal: `sector_em` = equal-weight mean of issuer EM (length-scaled 1-, 3-, 6-month) by GICS sector, monthly, on the TRACE HY panel 2008–2026.
- Horizon: 1 month.
- Metric: (a) Top 4 minus HY-panel equal-weight excess return, IR. (b) Cross-sector rank IC of `sector_em` against next-month sector excess return, beyond the sector spread level (the S7 test's +0.167).
- Pass: top-minus-panel IR ≥ 0.5 before cost (half the book's HY 1.05), positive in at least 3 of the 4 cycle windows (2008, 2015, 2020, 2022), and a beyond-spread sector IC with t ≥ 2. Also: sector rotation must add ≥ 20% of the unconstrained issuer EMC Q5 return over the panel (the book shows 24–35%). Fail: keep S7 out of the composite and use within-sector EMC only.

---

## Chapter 17. Issuer Size Premium in Credit Markets (PDF pp. 555–587)

**Question.** Do bonds of small issuers earn a spread or return premium over bonds of large issuers with the same risk?

**Answer.** Small issuers trade at wider spreads, but rating, sector and liquidity explain most of the gap. The residual size spread premium was 3.0 bp in IG and 5.3 bp in HY on 31 May 2018 (Table 17.8, PDF p. 571). With systematic exposures matched, small-issuer portfolios underperform large-issuer portfolios by 67 bp/yr in IG and 32 bp/yr in HY, 1994 to 2018 (Table 17.10, PDF p. 578). The authors reject size as a credit factor (PDF p. 580).

### Data

- Universe: Bloomberg Barclays US Corporate IG index and US HY index (PDF p. 555).
- The book keeps only US-domiciled issuers. It drops Yankees (USD bonds of foreign issuers), because a large foreign issuer can have a small USD footprint (note 2, PDF p. 586).
- Snapshot on 31 May 2018: 629 IG and 784 HY issuers. Of these, 573 IG and 576 HY are public (Table 17.1, PDF p. 556).
- Period: December 1993 or January 1994 to May 2018, monthly. Figure 17.5 starts January 1993 (PDF p. 566). Performance tables use January 1994 to May 2018 (Table 17.4, PDF p. 564).
- Subperiods: 1994 to 2006 and 2007 to 2018 (Table 17.4, PDF p. 564).
- Index rules exclude bonds below $300m outstanding in IG and $250m in HY. This rule can remove some small issuers (note 4, PDF p. 586).
- In 2000 the index raised its minimum amount outstanding. Average issuer size jumps at that date (PDF p. 562).
- Subordinated issues are excluded when bond data is aggregated to the issuer (PDF pp. 559, 562).
- Liquidity: Barclays Liquidity Cost Score (LCS), bond level, from January 2007 only (PDF p. 571). LCS comes from trader bid–offer quotes. It measures the round-trip cost (note 7, PDF p. 586).
- Trading volume: monthly volume as a percentage of amount outstanding (Table 17.6, PDF p. 568). The source of volume is not stated.
- Rating: index rating number from 1 to 24 on a linear scale. A higher number is a lower rating (note 9, PDF p. 587).
- Total debt and equity market cap (Table 17.1 only) come from balance sheets and stock prices. For a private subsidiary of a public parent, the book uses the parent's data (note 5, PDF p. 586).

### Definitions and formulas

**Issuer size (the measure the book uses).** Sum of par amount outstanding of the issuer's bonds in the US IG and HY indices together (PDF p. 557, note 3 p. 586).

```latex
Size_{i,t} = \sum_{b \in \text{index}(i,t)} AmtOut_{b,t}
```

Intuition: the issuer's footprint in the benchmark, free of bond prices.

- The book uses amount outstanding, not market value, so that size does not depend on price (note 3, PDF p. 586).
- An issuer can appear in both indices, for example senior IG debt plus subordinated HY debt. The book sums both (note 3, PDF p. 586).
- The book rejects two other measures (PDF p. 557). Equity market cap mixes valuation into size. Total balance-sheet debt is quarterly, and reporting cycles differ.
- Index debt is on average 30% of total balance-sheet debt (PDF p. 557).

**Relative size.** The book sorts on size relative to peers on each date, not on absolute size. Average issuer size grew from $1.4bn to $6.8bn in IG and from $0.6bn to $1.6bn in HY since 1994 (PDF p. 558).

**Issuer-level analytics.** Bond OAS, OAD, DTS and returns are aggregated to the issuer with bond market-cap weights. Subordinated issues are excluded (PDF pp. 559, 562).

```latex
x_{i,t} = \frac{\sum_{b \in i} MV_{b,t}\, x_{b,t}}{\sum_{b \in i} MV_{b,t}}, \qquad x \in \{OAS, OAD, DTS, r^{exc}\}
```

Intuition: the issuer behaves like its bonds, weighted by the money in each.

**DTS.** Duration times spread, in % × yr (Table 17.5, PDF p. 565). Excess return volatility is a linear function of DTS (Ben Dor et al. 2007, cited PDF p. 563).

```latex
DTS_{i,t} = OASD_{i,t} \times OAS_{i,t}
```

Intuition: the expected loss from a proportional spread move.

**Volatility per unit of DTS (Table 17.5, PDF p. 565).** The book normalises each month's portfolio excess return by the DTS at the start of that month. It then takes the volatility of the normalised series. The units in the table are "%/m".

```latex
\sigma^{DTS}_P = \operatorname{sd}_t\!\left(\frac{r^{exc}_{P,t}}{DTS_{P,t-1}}\right)
```

Intuition: if spreads move in proportion, this ratio is the same for every portfolio.

**Annualised volatility over longer horizons (note 8, PDF p. 587).** Multiply the volatility of monthly, quarterly and semiannual returns by √12, √4 and √2. Quarterly and semiannual returns overlap and are sampled monthly.

```latex
\sigma^{ann}_{h} = \sqrt{12/h}\;\operatorname{sd}_t\!\left(\sum_{k=0}^{h-1} r_{t-k}\right),\quad h \in \{1,3,6\}
```

Intuition: if prices are stale, monthly volatility is too low and long-horizon volatility shows the true risk. The book sums the returns. Compounding is our alternative, and the book does not say which it uses.

**Spread premium regressions (Models 1–3, PDF p. 569, Appendix 17.1 pp. 580–583).** The book runs one cross-sectional regression on each date, across issuers. It compares the method to Fama–MacBeth (note 10, PDF p. 587). Variables:
- `Small` dummy = 1 for the bottom 30% of issuers by size. `Large` dummy = 1 for the top 30%. Medium (middle 40%) is the omitted size group.
- `OAD`: issuer duration.
- Sector dummies. IG has eight: BAS, CYC, NCY, COT, TRE, UTI, BAB, FIO (Table 17.12, PDF p. 581). HY has five: BAS, CYC, NCY, UAE, FIN (Table 17.13, PDF p. 582). No separate intercept appears, so the sector dummies act as intercepts (our reading).
- Rating dummies. IG: A1, A2, A3, BAA1, BAA2, BAA3, so AAA to AA3 is the omitted group (our reading). HY: BA2, BA3, B1, B2, B3, "CCC and below", so BA1 is the omitted group (our reading).
- Liquidity: LCS divided by duration (PDF p. 569, note 12 p. 587). The tables label it "Bid-Ask".

```latex
\text{Model 1: } OAS_i = \beta_S\,Small_i + \beta_L\,Large_i + \gamma\,OAD_i + \sum_k \delta_k\,Sec_{ik} + \varepsilon_i
```
```latex
\text{Model 2: Model 1} + \sum_r \theta_r\,Rat_{ir}, \qquad \text{Model 3: Model 2} + \lambda\,\frac{LCS_i}{OAD_i}
```
```latex
SML = \hat\beta_S - \hat\beta_L
```

Intuition: SML is the spread gap between small and large issuers that duration, sector, rating and liquidity do not explain.

- Example check: IG Model 1 gives Small 11.8 and Large −5.4, so SML = 17.2 bp (Table 17.12, PDF p. 581).
- The book does not state the regression weights. Equal weight per issuer is our reading.
- Spread units are bp.

**Attribution of the small-minus-large spread gap (Figure 17.7, PDF pp. 571–572).** The book splits the gap each month into size, liquidity and rating parts. It averages the monthly results by year. It gives no formula. Our reading:

```latex
\Delta OAS^{S-L} = \underbrace{SML^{(3)}}_{size} + \underbrace{\hat\lambda\,\big(\overline{LCS/OAD}_S - \overline{LCS/OAD}_L\big)}_{liquidity} + \underbrace{\textstyle\sum_r \hat\theta_r\,(w^S_r - w^L_r)}_{rating} + \text{sector, duration terms}
```

Intuition: each part is a coefficient times the gap in that characteristic between the two portfolios.

**Spread premium by size decile (Figure 17.8, note 12 PDF p. 587).** Regress issuer spreads on sector dummies, rating dummies, duration, and LCS over duration. The model has no size term. Average the residuals within each size decile. The mean premium across all sizes is zero by construction.

**Transition matrix (Tables 17.2, 17.3, PDF pp. 560–561).** The book sorts issuers into size deciles at the start and at the end of rolling 12-month windows. It counts the share of issuers that move from each decile to each other decile.

### Implementation steps

1. **Universe.** Each month take the Bloomberg Barclays US Corporate IG and US HY index constituents. Keep US-domiciled issuers. Drop subordinated issues from the issuer aggregation (PDF p. 562, note 2 p. 586).
2. **Size.** Sum par amount outstanding per issuer across both indices on the rebalance date (note 3, PDF p. 586).
3. **Issuer analytics.** Aggregate bond OAS, OAD, DTS and the next-month excess return to the issuer with bond market-cap weights (PDF pp. 559, 562).
4. **Sort.** Rank issuers on size within each universe (IG, HY) separately. Small = bottom 30%. Medium = middle 40%. Large = top 30% (PDF p. 559).
5. **Weights.** Inside each portfolio, weight issuers by market cap (PDF p. 562).
6. **Rebalance.** Repeat the sort at the start of each month. The holding period is one month (PDF p. 559). The book applies no buffer and no turnover limit.
7. **Return.** Portfolio excess return for the month. The chapter does not define the return. The book's convention is excess return over duration-matched Treasuries (ch. 18 note 7, PDF p. 622). The chapter gives no transaction costs.
8. **Statistics.** Average excess return (%/yr), volatility (%/yr), maximum drawdown (%), information ratio = mean / volatility (Table 17.4, PDF p. 564). Report average DTS and volatility per DTS (Table 17.5). Report LCS (Figure 17.4), autocorrelation at lags of 1 and 2 months (Figure 17.5), and volatility at 1, 3 and 6 months (Figure 17.6).
9. **Spread premium.** Each month run Models 1–3 across issuers. Record SML. Run the decile-residual version for Figure 17.8. Liquidity data limits the attribution to 2007–2018 (PDF p. 571).
10. **Exposure-matched portfolios (PDF p. 574).** Each month solve two optimisations over index bonds. One minimises issuer size (Small portfolio). The other maximises issuer size (Large portfolio). Constraints:
    - Portfolio OAS, OAD and DTS equal the index values.
    - Weights, OAD contributions and DTS contributions equal the index values in each of 16 sector × maturity buckets.
    - Weights and duration contributions equal the index values in each rating bucket.
    - "Strong restrictions" on issuer concentration, set as limits on deviation from index issuer weight and from index issuer DTS contribution. The book does not give the limit values.
    - The book does not write the objective as a formula. Our reading: minimise or maximise the portfolio-weighted average issuer size, Σ w_b · Size_{i(b)}.
    - The book also does not list the 16 sector × maturity buckets or the rating buckets.
    - HY uses the same method (note 15, PDF p. 587).
11. **SML return.** SML return = Small portfolio excess return minus Large portfolio excess return, each month (PDF p. 573).
12. **Relaxed variant (Appendix, PDF p. 583).** Repeat step 10, but let portfolio OAS and DTS deviate up to 10% from the index. Keep the sector, rating and duration-contribution constraints.

### Results

**Sorted portfolios (Table 17.4, PDF p. 564), January 1994 to May 2018.**
- IG: Small 1.12%/yr excess return, 3.48%/yr volatility, IR 0.32. Large 0.68%/yr, 4.2%/yr, IR 0.16.
- HY: Small 2.6%/yr, 7.82%/yr, IR 0.33. Large 2.61%/yr, 10.63%/yr, IR 0.25.
- 1994–2006, IR: IG Small 0.43, Large 0.15. HY Small 0.20, Large 0.18.
- 2007–2018, IR: IG Small 0.33, Large 0.19. HY Small 0.44, Large 0.30.
- In HY, Small beats Large on raw excess return only in 2007–2018: 4.21 vs 3.65%/yr (PDF p. 563, Table 17.4).

**Volatility per DTS (Table 17.5, PDF p. 565).**
- Full period, IG: Small 6.6, Large 9.6 (%/m per DTS), with average DTS 10.8 and 9.0.
- Full period, HY: Small 8.8, Large 11.2, with DTS 23.4 and 21.3.
- Small portfolios carry more DTS but have lower volatility. The text gives the gap as about 30% lower in IG and 20% lower in HY (PDF p. 563).

**Liquidity and stale prices.**
- LCS of Small is more than 50% higher than LCS of Large, 2007–2018 (Figure 17.4, PDF p. 566).
- Autocorrelation of excess returns is much higher for Small (Figure 17.5, PDF p. 566).
- At quarterly and semiannual horizons, IG Small volatility exceeds IG Large volatility. HY Small stays slightly below HY Large (Figure 17.6, PDF pp. 566–567).
- The authors conclude that the low volatility of small issuers is an artefact of illiquidity (PDF p. 567).

**Characteristics, 31 May 2018 (Table 17.6, PDF p. 568).**
- IG Small − Large: OAS +14 bp, rating number +0.6, LCS +0.29%, monthly volume 4.2% vs 7.2% of amount outstanding.
- HY Small − Large: OAS +86 bp, rating number +1.5, LCS +0.45%, volume 11.7% vs 13.9%.
- Sector mix: IG Small overweights basic and capital goods (+18 pts) and financial others (+17 pts). It underweights communication and technology (−16 pts) and banks and brokerage (−13 pts).
- HY Small overweights basic and capital goods (+20 pts) and cyclical (+9 pts). It underweights communication and technology (−14 pts).
- Full-period HY SML characteristics: OAS +174 bp, OAD −0.9 yr, DTS +2.1, rating number +1.3 (Table 17.7, PDF p. 570).

**Spread premium (Table 17.8, PDF p. 571; Tables 17.12–17.13, PDF pp. 581–582).**

| | IG M1 | IG M2 | IG M3 | HY M1 | HY M2 | HY M3 |
|---|---|---|---|---|---|---|
| SML, bp | 17.2 | 5.7 | 3.0 | 69.1 | 6.9 | 5.3 |
| R² | 26% | 72% | 73% | 4% | 34% | 35% |

- IG Model 3 coefficients: Small 6.6 (t 2.6), Large 3.6 (t 1.4), liquidity 0.79 (t 3.2).
- HY Model 3 coefficients: Small 19.5 (t 0.9), Large 14.2 (t 0.7), liquidity 0.21 (t 2.9), CCC and below 445 (t 10.5).
- Over time, IG size premium ranges from −22 bp (2008) to 24 bp (2012). The IG liquidity component falls from 48–58 bp (2008–2009) to 3 bp (2018). The IG rating component is 17 bp in 2018 (PDF p. 571).
- HY: the rating component ranges from 32 bp (2013) to 175 bp (2016) and is 73 bp in 2018 (PDF p. 572).
- HY size premium is negative in 2008–2010, peaks at 70 bp in 2014, and is 13 bp in 2018 (PDF p. 573).
- The conclusion gives a HY range of −171 to 70 bp (PDF p. 580).
- The size premium is U-shaped across deciles. Both the smallest and the very largest issuers carry a positive premium (Figure 17.8, PDF p. 573).

**Exposure-matched SML (Table 17.10, PDF p. 578).**
- Full period, IG: SML −0.67%/yr, volatility 1.65%/yr, IR −0.41, max drawdown −15.9%.
- Full period, HY: SML −0.32%/yr, volatility 4.31%/yr, IR −0.07, max drawdown −21%.
- 1994–2006: IG −0.28%/yr, HY +0.12%/yr.
- 2007–2018: IG −1.12%/yr (IR −0.52), HY −0.81%/yr (IR −0.16).
- Diversification of the IG portfolios: Small holds about 480–570 bonds of 280–330 issuers. Large holds about 370–420 bonds of 105–127 issuers (Table 17.9, PDF p. 576).
- Average issuer size in 2014–2018: $0.88bn Small vs $5.91bn Large (Table 17.9, PDF p. 576).
- SML is positive in crises (Table 17.11, PDF p. 579). IG Jan–Sep 2002 total +5.6%, with communication and technology +20.2%. HY Jan 2001–Jul 2002 total +14.2%, with communication and technology +43.3%. HY Apr–Nov 2008 total +7.6%, with financials +38.7%.

**Relaxed constraints, OAS and DTS ±10% (Table 17.14, PDF p. 584).**
- Full period: IG SML −0.16%/yr (IR −0.09). HY SML +0.03%/yr (IR 0.01).
- 2007–2018: IG −0.31%/yr, HY +0.20%/yr.

### Robustness and variants

- Two subperiods (1994–2006, 2007–2018): the sign of the matched SML holds in IG. HY is +0.12 then −0.81%/yr (Table 17.10).
- Three regression specifications: SML falls as controls rise (Table 17.8).
- Longer-horizon volatility removes the apparent low risk of small issuers in IG (Figure 17.6).
- Relaxed OAS and DTS constraints let small issuers keep their extra carry. SML then moves to about zero, but not positive (Table 17.14).
- Size deciles: the premium is not monotone (Figure 17.8).
- The book did not test other size definitions (equity cap, total debt) for returns. Table 17.1 only describes them.

### Limits and caveats

- **What the source says:** the size spread premium is small after controls and the return premium is negative. **What we decide:** size is a control variable in the fair spread model and is not a signal.
- Bloomberg Barclays index data, LCS and index amount outstanding are proprietary. We cannot get them.
- All results are before transaction costs. Small issuers have higher LCS, so a net-of-cost SML would be more negative.
- The optimiser's concentration limits, bucket definitions and objective are not stated. A reader cannot reproduce Tables 17.9–17.10 exactly.
- HY regressions have low R² in Model 1 (4%) and weak t-stats on the size dummies in Models 2–3 (t < 1, Table 17.13).
- Liquidity attribution starts in 2007 only.
- The sorted-portfolio IRs favour small issuers, but stale prices inflate them (PDF p. 567). Do not use those IRs as evidence.
- Index minimum size rules cut off the smallest issuers. The "small" group is small only relative to index peers (note 4, PDF p. 586).

### Implementation in this repo

**Where it maps.**
- `hy/fairspread.py`, methodology Section 7.2: size is already a control there. `fairspread.py` line 223 sets the sign of `log_amount_outstanding` to −1. Section 7.2's liquidity row lists `log amount_outstanding` (methodology line 618).
- `hy/backtest.py`, Section 11: the stale-price diagnostic and the matched long-short test.
- Section 8: size does not become a signal S1–S7. The book's evidence goes against that.

**Data we have and lack.**
- Lack: index amount outstanding, Barclays LCS, TES, index rating number, Barclays sectors.
- Have: TRACE `bid_ask_pts`, `n_trades`, `par_volume`, `g_spread`, `mod_dur` (`hy/sources/trace_panel.py`). We also have Compustat point-in-time debt and CRSP market equity.

**Proxies (our decision).**
1. Issuer size proxy, primary: the sum of the issuer's book debt (current plus long-term) from `compustat_pit`. The book rejects this measure because it is quarterly (PDF p. 557). It is still the nearest field we have. Record the gap.
2. Issuer size proxy, secondary: the count of the issuer's distinct CUSIPs live in the TRACE panel at month end t. This count follows index footprint more closely but ignores bond size.
3. LCS proxy: `bid_ask_pts / price_mid`, a round-trip cost in decimal of price, as in `backtest.round_trip_cost`. Divide by `mod_dur` for the "LCS per unit of duration" control.
4. DTS proxy: `mod_dur × g_spread`. We have G-spread, not OAS.

**Lag rule.**
- TRACE fields: `available_at` = last trade date in the 7-day month-end window + 1 day (`trace_panel` rule 6).
- Compustat debt: `available_at` = `snapshot_available_at` of the point-in-time vintage. Use the latest vintage with `available_at` ≤ decision time.
- Decision time for month end t = t + 1 day (`backtest.decision_time`).
- The size sort at t reads only rows with `available_at` ≤ t + 1 day. `assert_no_lookahead` enforces this.

**Falsifiable tests.**
1. **Size as a signal.**
   - Signal: within-month issuer size tercile (bottom 30% vs top 30%) on the debt proxy. Run it inside each of 5 G-spread quintiles, with `backtest.spread_neutral_long_short`.
   - Horizon: 3 months.
   - Metric: mean net small-minus-large realised excess return (HAC t, `hac_mean`) and rank IC beyond spread (`ic_beyond`).
   - Pass, which means size enters Section 8 as a signal: rank IC beyond spread > 0 after costs in at least 3 of the 4 cycles 2008, 2015, 2020, 2022.
   - Book prediction: fail (HY matched SML −0.32%/yr).
2. **Stale-price check.**
   - Measure the first-order autocorrelation of monthly equal-weight excess returns of the small and the large tercile, 2008 onward.
   - Pass, which confirms the book's mechanism on TRACE: small autocorrelation exceeds large autocorrelation by at least 0.10.
   - If it passes, report Section 11 volatilities at the 3-month horizon (√4 scale, overlapping) beside the monthly ones.
3. **Size spread premium (Section 7.2 control).**
   - Run monthly cross-sectional OLS of issuer G-spread on small and large dummies, `mod_dur`, GICS sector dummies, rating dummies, and `bid_ask_pts/price/mod_dur`.
   - Pass, which keeps size in the fair line: the time-mean of SML is > 0 with HAC t > 2.
   - If it fails, drop `log_amount_outstanding` from Section 7.2 and record the result on a decision page.

---

## Chapter 18. Integrating Systematic Strategies into Credit Portfolio Construction (PDF pp. 591–623)

**Question.** Can the ESP value signal and the EMC momentum signal beat the US IG index after turnover control, a liquidity filter and bond-level transaction costs?

**Answer.** Yes, in US IG from March 2007 to July 2019. A turnover-buffer portfolio on the combined ESP-EMC signal beats the index by 1.78%/yr after LCS costs, with IR 1.26 (Table 18.4, PDF p. 610). An optimised portfolio with an 11% monthly turnover budget and index-matched exposures beats it by 1.45%/yr after costs, with IR 1.05 (Table 18.5, PDF p. 615). Costs take about 0.9–1.0%/yr from each.

### Data

- Universe: Bloomberg Barclays US Corporate IG index constituents (PDF p. 592).
- Period: March 2007 to July 2019, monthly. Subperiods: March 2007 to December 2012 and January 2013 to July 2019 (Tables 18.2, 18.4, 18.5).
- Down-cycle analysis (Table 18.1, PDF p. 598): January 1993 to July 2019.
- Signals: Barclays ESP scorecard (ch. 13) and EMC scorecard (ch. 15). Both are produced at the start of each month (note 4, PDF p. 622).
  - ESP is a bond-level score from 1 to 10. EMC is an issuer-level score from 1 to 10. A higher score is more attractive (PDF pp. 593–594).
  - The ESP method runs separately on US Corporate IG, US HY Ba-B and Euro Corporate Senior IG (note 6, PDF p. 622).
- Returns: excess returns over duration-matched Treasury portfolios, as the index provider publishes them (note 7, PDF pp. 622–623).
- Costs: Barclays Liquidity Cost Score (LCS), bond level. History for US IG and HY starts January 2007 (Table 18.3, PDF p. 601). The average LCS of USD Credit IG in July 2019 is 0.608% (Table 18.3).
- Liquidity filter: Barclays Trade Efficiency Score (TES), bond level, 1 (best) to 10 (worst) (PDF p. 602, ch. 13 note 10 PDF p. 462).
- Bond-equity mapping: EMC needs each issuer's stock ticker (Figure 18.2, PDF p. 594). The chapter gives no mapping details.

### Definitions and formulas

**ESP (recap from ch. 13, as ch. 18 states it, PDF pp. 593–594).**
1. Form peer groups by rating, sector and maturity.
2. Compute each bond's excess spread over its peer-group average.
3. Regress the excess spread on three fundamental ratios: financial leverage, net debt over EBITDA, and interest coverage (EBIT over interest). Financials use only long-term debt over long-term assets (note 5, PDF p. 622).
4. Rank the residual (the unexplained excess spread) across all bonds in the index. Map the rank to scores 1–10.

```latex
ESP^{raw}_b = \left(s_b - \bar s_{peer(b)}\right) - \hat\beta' \left(F_{i(b)} - \bar F_{peer(b)}\right), \qquad ESP_b = \text{decile}\big(\operatorname{rank}(ESP^{raw}_b)\big)
```

Intuition: a bond is cheap when its spread is above its peers by more than its fundamentals explain.

- The left side is our reading. The book gives no closed formula. Our reading demeans F within peers. The book says only that it uses regression analysis.
- Ch. 18 names three ratios. The repo card (from ch. 13) names only market leverage. Record both. Ch. 18 describes the production scorecard.

**EMC (recap from ch. 15, PDF p. 594).** The book takes the equal-weight mean of 1-, 3- and 6-month stock returns, "adjusted for the lengths of the signal formation periods". The repo card reads this adjustment as division by √(months) (ch. 15 note 9, PDF p. 541).

```latex
EMC^{raw}_i = \tfrac{1}{3}\left(\frac{r_{i,1m}}{\sqrt{1}} + \frac{r_{i,3m}}{\sqrt{3}} + \frac{r_{i,6m}}{\sqrt{6}}\right), \qquad EMC_i = \text{decile}\big(\operatorname{rank}(EMC^{raw}_i)\big)
```

Intuition: a steady stock trend scores higher than a one-month jump.

**Combined signal (Figure 18.14, PDF p. 612).**

```latex
C_b = 0.5\,ESP_b + 0.5\,EMC_{i(b)}
```

Intuition: buy cheap bonds of issuers whose stock rises.

- Ch. 18 combines at the bond level (ch. 19, PDF p. 625).
- The book ranks C_b across the eligible universe for the buffer thresholds. "Top 20%" and "bottom 45%" are percentiles of C_b (PDF p. 606).

**Top portfolios (note 10, PDF p. 623).** Top ESP = bonds with ESP 9 or 10, the top 20% of index bonds. Top EMC = issuers with EMC 9 or 10, the top 20% of index issuers.

**Combined Portfolios 50/50.** Equal-weight mix of the top ESP and top EMC portfolios (PDF p. 598).

**Combined Signals 50/50.** Bonds in the top quintile of C_b (PDF p. 598).

**Sort portfolios** are market-cap weighted (PDF p. 594).

**Rank correlation (note 8, PDF p. 623).** Kendall's τ between ESP and EMC across index constituents each month.

```latex
\tau = \frac{N_{concordant} - N_{discordant}}{\binom{n}{2}}
```

Intuition: the share of pairs that the two scores order the same way, minus the share they order in opposite ways.

**Down-cycle (PDF p. 597).** A significant top-to-trough decline in cumulative index excess return within a rolling 12-month period. The book gives no threshold. It lists seven episodes (Table 18.1).

**LCS (PDF p. 601).** The cost of an immediate round trip of a typical institutional size, in % of price, from Barclays trader two-way quotes.

```latex
LCS_b = \begin{cases} (s^{bid}_b - s^{offer}_b)\times OASD_b & \text{spread-quoted bonds} \\ (P^{offer}_b - P^{bid}_b)/P^{bid}_b & \text{price-quoted bonds} \end{cases}
```

Intuition: the price you lose to buy and then sell at once.

- LCS is conservative, because investors see competing dealer quotes (note 17, PDF p. 623).

**TES (PDF p. 602, ch. 13 note 10 PDF p. 462).** A relative 1–10 rank that blends LCS per unit of duration with trading volume. Lower TES = higher volume and lower LCS per unit of duration. The book gives no blend formula. Our reading:

```latex
TES_b = \text{decile}_t\Big(\tfrac12\operatorname{rank}\big(LCS_b/OASD_b\big) + \tfrac12\operatorname{rank}\big(-Vol_b/AmtOut_b\big)\Big)
```

Intuition: cheap and busy bonds get a low score.

**Turnover (ch. 13 note 11, PDF p. 462).** The market-value share of bonds that the portfolio buys in the month. The turnover budget is "the maximum percentage of portfolio market value that can be rebalanced in a given month" (PDF p. 613).

```latex
TO_t = \sum_b \max\!\left(0,\; w_{b,t} - \tilde w_{b,t}\right) = \tfrac12 \sum_b \left|w_{b,t} - \tilde w_{b,t}\right|
```

Intuition: the share of the book that changes. Here \tilde w is the prior weight after drift. The second equality holds when the portfolio is fully invested.

**Transaction cost (PDF pp. 600–602, 608).** The book measures historical rebalancing costs with bond-level LCS. It does not state whether one trade pays the full LCS or half of it. Our reading, which is the standard reading of a round-trip measure: each buy or sell pays half the LCS on the traded market value.

```latex
TC_t = \sum_b \tfrac12\,LCS_{b,t}\,\left|w_{b,t} - \tilde w_{b,t}\right|, \qquad r^{net}_{P,t} = r^{exc}_{P,t} - TC_t
```

Intuition: a round trip costs one full LCS.

- Plausibility check (our arithmetic, not the book's): 10.4%/month one-way turnover gives 2 × 10.4% × 12 ≈ 250% traded per year. At ½·LCS of about 0.35%, the drag is about 0.9%/yr. The book reports 0.88%/yr (Table 18.4). So the half-LCS reading fits.

**DTS (note 11, PDF p. 623).** Duration × spread, the exposure to proportional spread moves.

### Implementation steps

**A. Signal check (Tables 18.1–18.2).**
1. At the start of each month, read ESP and EMC for every index bond.
2. Form market-cap-weighted portfolios by score pairs (1–2, 3–4, …, 9–10). Hold one month. Record the excess return (Figure 18.3, PDF p. 595).
3. Build Top ESP, Top EMC, Combined Portfolios 50/50 and Combined Signals 50/50, as defined above. Report the return over the index, the TEV and the IR before costs (Table 18.2, PDF p. 599).

**B. Strategy 1: turnover buffer (PDF pp. 605–611).**
1. **Eligibility.** At each month start, keep index bonds with TES ≤ 3. Only these can be bought (PDF p. 606).
2. **Signal.** Compute C_b = 0.5 ESP + 0.5 EMC. Rank it within the index universe. The book does not say whether it ranks within all index bonds or within eligible bonds only. Our reading is all index bonds.
3. **Buy rule.** Buy an eligible bond that is not held when its C_b is in the top 20% (PDF p. 606).
4. **Sell rule.** Sell a held bond when its C_b drops to or below the bottom 45%, that is, percentile ≤ 45% (PDF p. 606).
5. **Hold rule.** Keep any held bond with C_b between those thresholds, even when its TES later rises above 3. Average TES of held bonds drifts from 2 to the index mean of 5 (Figure 18.11, PDF p. 609).
6. **Weights.** The book does not state the weights. Our reading is market-cap weights across held bonds, as in the sorts (PDF p. 594). Drop bonds that leave the index. The book does not state this rule. It is our reading.
7. **Constraints.** None. The portfolio does not match index exposures. Its DTS exceeds index DTS in 2014–2019 (Figure 18.13, PDF p. 611).
8. **Rebalance** monthly. No fixed holding period: a bond stays until the sell rule fires.
9. **Costs.** Charge LCS on every trade at the time of the trade, as in the formula above.
10. **Statistics.** Absolute excess return, volatility, IR. Excess over the index, TEV, IR. Report before and after costs (Table 18.4). Report turnover on a rolling 12-month window (Figure 18.9) and holding-time distribution (Figure 18.10).

**C. Strategy 2: turnover budget with linear optimisation (PDF pp. 611–617, Figure 18.14).** The book gives the elements but not the tolerance values. The formulation below is our reading. Each element cites the book. Each δ is an unstated parameter.

```latex
\max_{w \ge 0}\; \sum_b w_b\,C_b
```

Intuition: hold as much of the strongest combined signal as the constraints allow.

subject to:

```latex
\sum_b w_b = 1 \quad\text{(fully invested)}
```
```latex
w_b = 0 \;\text{ if } \tilde w_b = 0 \text{ and } \big(TES_b > 3 \text{ or } M_b < 3\text{y}\big) \quad\text{(no new buys of illiquid or short bonds; existing ones may stay, PDF p. 612)}
```
```latex
w_b \le \tilde w_b \;\text{ if } TES_b > 3 \text{ or } M_b < 3\text{y} \quad\text{(our reading: keep or sell, never add)}
```
```latex
\Big|\textstyle\sum_b w_b X_b - X^{idx}\Big| \le \delta_X,\quad X \in \{OAS, OAD, DTS\} \quad\text{(PDF pp. 612–613)}
```
```latex
\Big|\textstyle\sum_{b\in k} w_b - W^{idx}_k\Big| \le \delta_W,\;\; \Big|\textstyle\sum_{b\in k} w_b OAD_b - OAD^{idx}_k\Big| \le \delta_D,\;\; \Big|\textstyle\sum_{b\in k} w_b DTS_b - DTS^{idx}_k\Big| \le \delta_S \quad\forall\, \text{sector } k
```
```latex
\Big|\textstyle\sum_{b\in i} w_b - W^{idx}_i\Big| \le \delta_I \quad\forall\,\text{issuer } i \quad\text{(issuer concentration, PDF p. 612)}
```
```latex
\tfrac12\textstyle\sum_b |w_b - \tilde w_b| \le x \quad\text{(turnover budget, PDF p. 613)}
```

Intuition of each constraint row: stay invested, trade only liquid long bonds, match the index risk, match index sector structure, stay diversified, and change at most x of the book.

- The |·| terms become linear with split variables w_b = \tilde w_b + u_b − v_b, with u, v ≥ 0. The program is then an LP. The book calls it "a linear optimization program" (PDF p. 612).
- The book does not give sector partitions or δ values. Ch. 17 uses a related matched set: 16 sector × maturity buckets plus rating buckets, with weights, OAD and DTS contributions (PDF p. 574). That set is a defensible fill-in, labelled as ours.

Steps:
1. Each month, start from the drifted prior weights \tilde w.
2. Solve the LP for budget x. Passive index tracking (new issues, ageing, rating moves) uses a small part of x (PDF p. 613).
3. Charge LCS on |w − \tilde w|.
4. Hold one month. Repeat.
5. Repeat the full backtest for a grid of x from 0% to about 70% a month (Figure 18.15). The grid for ESP alone runs to about 30% (Figure 18.20).
6. Plot gross excess over the index, TC and TEV against x (Figure 18.15). Plot net excess over the index against x (Figure 18.16).
7. Pick x = 11%. The book picks it "with hindsight" (PDF p. 614). It is close to the buffer's 10.4% turnover (note 18, PDF p. 623).
8. Appendix 18.1: same LP with C_b replaced by ESP alone or EMC alone. All other rules stay the same (PDF p. 619).

### Results

**Signal sorts, before costs, March 2007 – July 2019 (PDF pp. 595–596).**
- ESP 1–2: −0.74%/yr. ESP 9–10: 3.39%/yr.
- EMC 1–2: −4.25%/yr. EMC 9–10: 4.55%/yr.
- Index: 1.08%/yr.

**Down-cycles, excess over the index, %/yr (Table 18.1, PDF p. 598).**
- Top EMC beats the index in all seven episodes. Example: Apr–Oct 2002 +14.2.
- Top ESP lags the index in six of seven. Example: Apr–Oct 2002 −9.9. The exception is Aug 1997 – Oct 1998, +0.4.
- Other periods (71% of months): Top EMC +2.4, Top ESP +2.6.

**Combining, before costs, over the index (Table 18.2, PDF p. 599).**

| Portfolio | Exc. ret. %/yr | TEV %/yr | IR |
|---|---|---|---|
| Top ESP | 2.31 | 1.60 | 1.45 |
| Top EMC | 3.48 | 2.07 | 1.68 |
| Combined Portfolios 50/50 | 2.89 | 1.51 | 1.92 |
| Combined Signals 50/50 | 6.00 | 2.91 | 2.06 |

- Combined Signals by subperiod: 8.67%/yr (IR 2.23) in 2007–2012 and 3.64%/yr (IR 2.85) in 2013–2019.
- The ESP-EMC rank correlation stays near zero over time (Figure 18.4, PDF p. 596).

**Buffer strategy (Table 18.4, PDF p. 610; text PDF p. 608).**

| Period | Before TC over index | After TC over index | TEV after | IR after |
|---|---|---|---|---|
| 2007–2019 | 2.66 | 1.78 | 1.41 | 1.26 |
| 2007–2012 | 3.94 | 2.79 | 1.75 | 1.59 |
| 2013–2019 | 1.52 | 0.88 | 0.92 | 0.95 |

- Cost drag: 0.88%/yr overall, 1.15%/yr in 2007–2012, 0.64%/yr in 2013–2019 (PDF p. 608).
- Turnover: 7% to 14% a month on a rolling basis, 10.4% on average (PDF p. 606).
- Holding time, 2007–2012: mean 14.0 months, median 9.0, p10 3.0, p90 32.7. 2013–2019: mean 14.1, median 10.0, p90 33.0 (Figure 18.10, PDF p. 607).
- Volume of held bonds falls from 23% to 7% of notional a month over 24 months (PDF p. 608).

**Budget strategy, x = 11% (Table 18.5, PDF p. 615).**

| Period | Before TC over index | After TC over index | TEV after | IR after |
|---|---|---|---|---|
| 2007–2019 | 2.41 | 1.45 | 1.38 | 1.05 |
| 2007–2012 | 3.32 | 2.12 | 1.90 | 1.12 |
| 2013–2019 | 1.61 | 0.85 | 0.57 | 1.50 |

- Absolute excess return: 3.49%/yr before TC and 2.52%/yr after TC, against 1.08%/yr for the index.
- Holding time: mean 9.7 months (2007–2012) and 9.8 months (2013–2019). Median 7.0. The 2013–2019 p10 is 2.0 and p90 is 21.0 (Figure 18.18, PDF p. 616). The 2007–2012 p10 and p90 are not legible.
- Return and TC both rise with x. Net return peaks at moderate x and falls at high x. TEV is about flat in x (Figures 18.15–18.16, PDF pp. 613–614). The point values are read from charts, so we do not quote them.

**Buffer vs budget, after TC (Table 18.6, PDF p. 618).**
- Full period: budget 1.45%/yr (IR 1.05), buffer 1.78%/yr (IR 1.26).
- 2007–2012: budget lags buffer by 0.67%/yr (2.12 vs 2.79).
- 2013–2019: about equal (0.85 vs 0.88).

**Single signals, x = 11%, after TC (Table 18.7, PDF p. 621).**
- Full period: EMC 0.75%/yr (IR 0.50), ESP 0.42%/yr (IR 0.46), combined 1.45%/yr (IR 1.05).
- Table 18.7's title says "Turnover Buffer", but its rows say "Turn Budget". The text (PDF p. 620) supports "budget". We read it as budget.

### Robustness and variants

- Two turnover controls, buffer and budget, give similar net results (Table 18.6).
- A grid of turnover budgets: net outperformance is flat over a wide range, so a lower budget is the prudent choice (PDF p. 614).
- Subperiods: costs and TEV are higher in 2007–2012, which includes 2008.
- Single-signal versions are weaker than the combination (Appendix 18.1).
- Figure 18.8 Panel B gives an alternative buffer, but the book does not test it. Buy on high ESP unless EMC is very low (a "value trap" guard). Sell on low ESP (PDF p. 606).
- The book argues that a slower uniform rebalance frequency (quarterly, semiannual) is worse, because signal reversion speed differs across bonds. It gives no numbers (PDF p. 607).

### Limits and caveats

- **What the source says:** value plus momentum survives conservative costs in IG. **What we decide:** adopt the buffer rule and the half-LCS-per-trade cost model as the Section 11 implementation test. Do not adopt the reported numbers as HY evidence.
- IG only. No HY test in this chapter.
- Short sample: 2007–2019 (about 12 years), one crisis. The budget of 11% was chosen with hindsight (PDF p. 614).
- Proprietary inputs: ESP and EMC scorecards, LCS, TES and index analytics are Barclays data.
- LCS is a dealer quote and conservative (note 17, PDF p. 623). Our TRACE bid-ask proxy is a different object, because it is realised and not quoted.
- The book leaves out the optimiser tolerances, the sector partition, the issuer limits, the TES formula and the buffer weight scheme. These are our readings above.
- TEV and IR come from monthly returns. The book does not adjust them for autocorrelation.

### Implementation in this repo

**Where it maps.**
- Methodology Section 7.5, the alpha cost line: replace "full round trip on every formation" with "½ round-trip cost × |Δw|".
- Section 8, the composite: the buffer rule acts on the composite rank.
- Section 11: the backtest design.
- Code:
  - `hy/backtest.py` has `round_trip_cost`, `turnover_cost`, `long_short` and `book_legs`. The buffer rule and the turnover-budget LP are new functions there.
  - `hy/peers.py` supplies `esp_sr`, `emc` and `onescore`.
  - `hy/signals.py` holds the cycle test.

**Data we have and lack.**
- Have:
  - `bid_ask_pts / price_mid` as a round-trip cost proxy (`trace_panel` rule 4).
  - `n_trades` and `par_volume`.
  - `mod_dur` and `g_spread`, so DTS = `mod_dur × g_spread`.
  - `years` to maturity.
  - Issuer ESP and EMC from `peers.py`.
- Lack: LCS, TES, amount outstanding (so no volume over notional), index weights and index OAS.

**Proxies (our decision).**
1. Cost: `cost_rt = bid_ask_pts / price_mid`, already in `backtest.round_trip_cost`. Charge ½ · `cost_rt` per traded unit.
2. TES proxy:
   - Within each month, take the mean of two percentile ranks. One rank is `cost_rt / mod_dur`, ascending. The other is `par_volume`, descending.
   - Cut the mean into deciles 1–10.
   - Eligible to buy: TES ≤ 3.
   - Without amount outstanding, volume is in par dollars, not turnover. This choice favours large issues. Record the bias.
3. Benchmark: the equal-weight or par-volume-weight TRACE HY universe that `backtest.eligible` defines. This replaces the Barclays index.
4. Exposure constraints for the LP: match universe G-spread, `mod_dur`, DTS, GICS sector weights and rating weights.

**Lag rule.**
- Signals use rows with `available_at` ≤ decision time t + 1 day.
- EMC uses month-end returns with `available_at` ≤ decision time (`equity_momentum`).
- The cost of a trade at t uses `bid_ask_pts` from month t, which is known at t + 1 day.
- The realised return runs from t to t + h on the next panel rows.
- The TES proxy at t uses only month-t volume and cost.

**Falsifiable test.**
- Signal: the composite (OneScore, or Section 8 composite) on TRACE HY, 2010 onward.
- Rule: buy when rank ≥ 80th percentile and TES proxy ≤ 3. Sell when rank ≤ 45th percentile. Use market-value weights.
- Horizon: monthly rebalance. Measure the one-month realised excess return.
- Metric: net excess return over the universe benchmark after ½ · `cost_rt` · |Δw|, HAC t-stat, and IR.
- Pass, all three must hold:
  1. Net excess return > 0 in at least 3 of the 4 cycles 2008, 2015, 2020, 2022. TRACE coverage decides whether 2008 is in the sample.
  2. Net IR ≥ 0.5 over the full sample.
  3. Mean turnover ≤ 60% of the turnover of the decile-sort `long_short` on the same signal.
- Fail: the composite is not implementable at TRACE costs. Record a decision page and keep it as a ranking tool only.

---

## Chapter 19. OneScore: Combining Quantitative and Fundamental Views in Credit (PDF pp. 625–635)

**Question.** Does an issuer-level, sector-neutral mix of ESP (value) and EMC (equity momentum) pick credit winners in every sector and in every market regime?

**Answer.** Yes, in US IG and before costs. Top-minus-bottom OneScore earns 4.00%/yr with IR 4.84 over five years to February 2020, and it is positive in every sector (Table 19.2, PDF p. 630). With DTS-matched legs, OneScore earns 27–89 bp/month in every drawdown episode since 1997 (Table 19.3, PDF p. 631). DTS matching also removes most of the market direction of ESP and EMC (Table 19.4, PDF p. 633).

### Data

- Universe: Bloomberg Barclays US Corporate IG index (PDF pp. 626, 628).
- Snapshot example: 28 February 2020, basic industry (Table 19.1, PDF p. 627).
- Performance windows:
  - Figure 19.1 and Table 19.2: 1, 3 and 5 years to 28 February 2020 (PDF pp. 629–630).
  - Tables 19.3–19.4: January 1993 to March 2020 (Table 19.4 title, PDF p. 633). Table 19.3 has 325 months in total (episodes plus 230 other months).
- Frequency: monthly. Portfolios form at the start of each month (PDF p. 628).
- Inputs: Barclays ESP (ch. 13) and EMC (ch. 15) bond scores (PDF p. 625).
- Filter: drop bonds with maturity of 3 years or less, both for the signal and for the portfolios (PDF pp. 626, 628; note 2, PDF p. 635).
- Returns: excess over duration-matched Treasuries. The book says total returns give similar results (note 3, PDF p. 635).
- Costs: none. No turnover limit. All results are before costs (note 1, PDF p. 635).
- Sectors: the rows of Table 19.2 list 13 industry sectors (PDF p. 630):
  - basic industry, capital goods, consumer cyclical, healthcare and pharma, noncyclical
  - energy, utility, technology, communication
  - banking/brokerage/financing, insurance, REITs, transportation
  - The book does not state the exact partition used to rank. Our reading: these 13.

### Definitions and formulas

**Step 1. Issuer signal.** Take the market-weight mean of bond ESP and bond EMC over the issuer's bonds with maturity > 3 years (PDF p. 626).

```latex
ESP_{i,t} = \frac{\sum_{b\in i,\,M_b>3} MV_{b,t}\,ESP_{b,t}}{\sum_{b\in i,\,M_b>3} MV_{b,t}}, \qquad EMC_{i,t}\ \text{likewise}
```

Intuition: analysts rate issuers, not bonds, so the signal lives at the issuer. Short bonds add little spread duration (note 2, PDF p. 635).

**Step 2. Within-sector rank.** Rank ESP_i and EMC_i within each industry sector k. This normalises them, so every sector has strong and weak names (PDF p. 626).

```latex
u^{ESP}_{i,t} = \operatorname{pctrank}_{k(i)}\!\left(ESP_{i,t}\right),\qquad u^{EMC}_{i,t} = \operatorname{pctrank}_{k(i)}\!\left(EMC_{i,t}\right)
```

Intuition: separate issuer selection from sector allocation. The book says "ranked (normalized)" but gives no exact scale. A percentile rank is our reading.

**Step 3. Equal-weight average and re-rank (PDF p. 626).**

```latex
\bar u_{i,t} = \tfrac12\left(u^{ESP}_{i,t} + u^{EMC}_{i,t}\right),\qquad OneScore_{i,t} = 1 + \Big\lfloor 10\cdot\operatorname{pctrank}_{k(i)}(\bar u_{i,t}) - \epsilon \Big\rfloor \in \{1,\dots,10\}
```

Intuition: an issuer scores high only when it is both cheap and in a rising stock within its sector. A higher OneScore is more attractive (PDF p. 626). The decile mapping is our reading of "ranks falling into decile groups".

- Table 19.1 prints ESP and EMC "normalized within the basic industry sector" on a 1–10 scale, with one decimal (for example, KCN ESP 8.1, EMC 9.4, OneScore 10; PDF pp. 627–628). So the per-signal normalisation appears to map to a continuous 1–10 scale. This is our reading.

**Portfolio rule (PDF p. 628).**
- Top set: in each sector, up to 10 issuers with the highest OneScore. Bottom set: up to 10 with the lowest.
- Concentrated sectors (for example, transportation) get fewer issuers. The book gives no rule for "fewer". Our reading: cap at 10 and at no more than one decile of the sector's issuers.
- Combine top issuers across all sectors into one portfolio, and bottom issuers into another.
- Issuers carry equal weight. Bonds inside an issuer carry market weight. Only bonds with maturity > 3 years enter.
- Long-short = top minus bottom.

```latex
r^{Top}_{t+1} = \frac{1}{N_{Top}}\sum_{i\in Top}\ \sum_{b\in i,\,M_b>3}\frac{MV_{b,t}}{MV_{i,t}}\,r^{exc}_{b,t+1},\qquad r^{LS}_{t+1} = r^{Top}_{t+1} - r^{Bot}_{t+1}
```

Intuition: each chosen issuer counts once, whatever its debt size.

**ESP and EMC long-short (PDF p. 629).** Same construction as OneScore: equal-weight top and bottom issuers on the within-sector normalised ESP or EMC.

**DTS matching (PDF p. 632, notes 4–5 PDF p. 635).** Scale each leg's monthly excess return to a DTS of 12. The value 12 is about the time-average DTS of the US IG index over 1993–2020.

```latex
\tilde r^{leg}_{t+1} = r^{leg}_{t+1}\cdot\frac{12}{DTS^{leg}_{t}},\qquad \tilde r^{LS}_{t+1} = \tilde r^{Top}_{t+1} - \tilde r^{Bot}_{t+1}
```

Intuition: both legs carry the same spread risk, so the long-short no longer bets on the market. In practice this needs cash in high-spread periods and leverage in benign periods (note 5, PDF p. 635). DTS is measured at the start of the month (PDF p. 632).

**Drawdown episodes.** The method of Figure 18.5 (ch. 18): significant top-to-trough falls in cumulative index excess return (PDF p. 629). The book gives eight episodes and no threshold (Table 19.3).

### Implementation steps

1. At the start of month t, take index bonds with maturity > 3 years. Read bond ESP and EMC, both known at t.
2. Aggregate to the issuer with market weights (step 1 above).
3. Within each of the 13 sectors, compute the percentile rank of issuer ESP and of issuer EMC.
4. Average the two ranks with equal weight. Re-rank the average within the sector. Cut it into deciles 1–10 = OneScore.
5. In each sector, select up to 10 top and up to 10 bottom issuers.
6. Build the Top and Bottom portfolios: equal weight across issuers, market weight across each issuer's bonds of > 3 years.
7. Hold one month. Record each leg's excess return over duration-matched Treasuries.
8. Record each leg's start-of-month DTS. Compute the DTS-matched leg returns (× 12 / DTS).
9. Repeat monthly. No turnover limit and no costs.
10. Statistics:
    - Average excess return, volatility and IR (%/yr) over 1, 3 and 5 years, per sector and in total (Table 19.2).
    - Mean monthly return in each drawdown episode and in the other months (Table 19.3).
    - Correlation of the monthly strategy returns with each other, with US Corp IG excess return, with US Treasury return and with the S&P 500. Split drawdown months from other months (Table 19.4).

### Results

**Top minus bottom, periods ending 28 February 2020 (Table 19.2, PDF p. 630).**

| | Ret 1y | Ret 3y | Ret 5y | Vol 5y | IR 1y | IR 3y | IR 5y |
|---|---|---|---|---|---|---|---|
| ALL | 3.24 | 3.24 | 4.00 | 0.83 | 6.58 | 6.23 | 4.84 |

- By sector, 5-year return %/yr: basic industry 8.57, capital goods 2.47, consumer cyclical 4.91, healthcare and pharma 3.82, noncyclical 3.00, energy 4.73, utility 3.6, technology 4.22, communication 3.03, banking/brokerage/financing 3.57, insurance 4.01, REITs 3.28, transportation 2.03.
- Every sector is positive in every window.
- Lowest 5-year IR: energy 0.93 and transportation 0.92. Highest: consumer cyclical 3.61.
- Lowest 1-year return: energy 0.27 (IR 0.08).
- The text claims especially strong results in basic, cyclical and technology (PDF p. 629).

**Drawdown episodes, bp per month (Table 19.3, PDF p. 631).**

| Episode | Months | US Corp IG | EMC raw | ESP raw | OneScore raw | EMC DTS | ESP DTS | OneScore DTS |
|---|---|---|---|---|---|---|---|---|
| Aug 1997–Oct 1998 | 15 | −35 | 14 | −3 | 10 | 18 | 44 | 52 |
| Jan 2000–Dec 2000 | 12 | −37 | 44 | −3 | 24 | 39 | 17 | 34 |
| Apr 2002–Oct 2002 | 7 | −82 | 113 | 1 | 80 | 94 | 23 | 83 |
| Mar 2007–Nov 2008 | 21 | −128 | 88 | 24 | 67 | 53 | 17 | 43 |
| May 2011–Nov 2011 | 7 | −83 | 52 | 18 | 39 | 35 | 24 | 39 |
| Aug 2014–Feb 2016 | 19 | −31 | 38 | 1 | 30 | 28 | 11 | 30 |
| Feb 2018–Dec 2018 | 11 | −36 | 19 | 14 | 21 | 14 | 28 | 27 |
| Jan 2020–Mar 2020 | 3 | −432 | 175 | −77 | 66 | 86 | 38 | 89 |
| Other periods | 230 | 35 | 26 | 36 | 39 | 22 | 25 | 31 |

- Raw ESP is pro-cyclical. Its worst month average is −77 bp in Jan–Mar 2020.
- Raw EMC is contra-cyclical.
- After DTS matching, all three strategies are positive in every episode (PDF p. 632).

**Correlations, January 1993 – March 2020 (Table 19.4, PDF p. 633; text PDF p. 634).**

| Pair | Raw, drawdown | Raw, other | DTS-matched, drawdown | DTS-matched, other |
|---|---|---|---|---|
| EMC vs ESP | −32% | 43% | −38% | 11% |
| ESP vs US Corp | 34% | 44% | −6% | −22% |
| EMC vs US Corp | −64% | 20% | −50% | −11% |
| OneScore vs US Corp | −37% | 35% | −48% | −28% |
| OneScore vs EMC | 67% | 81% | 41% | 54% |
| OneScore vs ESP | 43% | 84% | 62% | 82% |

### Robustness and variants

- Windows of 1, 3 and 5 years give consistent IRs (PDF p. 629).
- Every sector is positive. Sector portfolios are concentrated, up to 10 names a side (Table 19.2).
- Total returns give a similar top-over-bottom result to excess returns (note 3, PDF p. 635).
- Raw vs DTS-matched legs: DTS matching changes the regime behaviour of ESP and EMC but keeps every strategy positive (Tables 19.3–19.4).
- Ch. 18 combines at the bond level, and this chapter combines at the issuer level within sectors. The book does not compare the two head to head.

### Limits and caveats

- **What the source says:** sector-neutral issuer OneScore works in every IG sector and regime before costs. **What we decide:** keep OneScore as the issuer-level value-momentum composite. Make DTS-matched legs the default in Section 11. Treat the IR levels as an upper bound.
- IG only. No HY evidence in this chapter.
- Before costs and without turnover limits (note 1, PDF p. 635). Ch. 18 shows costs of about 1%/yr for a similar IG signal.
- The Table 19.2 IRs (4.8–6.6 for ALL) come from short windows of 1 to 5 years in a benign period. The 1-year IR rests on 12 monthly returns.
- DTS matching needs leverage or cash (note 5, PDF p. 635). The matched return is not directly investable without a funding cost.
- The book does not give the sector partition, the rule for "fewer issuers" in concentrated sectors, or the rank scale.
- ESP and EMC are Barclays scorecards. Ours are reconstructions.
- Table 19.1 shows analyst ratings beside scores, but the book does not test whether agreement between analyst and model adds return. This is a gap in the quantamental claim.

### Implementation in this repo

**Where it maps.**
- `hy/peers.py` `onescore()`: methodology Section 7.4 (OneScore paragraph) and Section 8 (the composite).
- Backtest: `hy/backtest.py` and `scripts/backtest_onescore.py` (Section 11).
- Decision page: `docs/decisions/2026-10-22-onescore.md`.

**Gaps between the code and the book (code read on this date).**
1. Aggregation: the code takes the median `esp_sr` over all of the issuer's bonds (`peers.py` line 305). The book takes the market-weight mean over bonds with maturity > 3 years. Our panel has no amount outstanding, so market weight is not possible. Use equal weight or `par_volume` weight. The 3-year filter is possible now, because `years` is in the panel.
2. EMC: `equity_momentum` uses a 3-month compounded return (`EMC_MONTHS = 3`). The book uses the 1, 3 and 6-month combination (ch. 15, note 9 PDF p. 541).
3. Final step: the code stops at the mean of the two sector percentiles. It does not re-rank or cut deciles. Inside a sector the order is the same, so rank IC within a sector does not change. A cross-sector top-10 selection does change, because the re-rank puts every sector on the same 0–1 scale. Add the re-rank before any per-sector top-N rule.
4. Sectors: the code uses GICS sectors (`sector_at`). The book uses 13 Barclays-style sectors. Keep GICS and record the difference. `MIN_SECTOR = 5` sets the minimum sector size for a rank.
5. Portfolio: the code has no "up to 10 per sector, equal weight across issuers" builder. Add one to `backtest.book_legs`, with a per-sector cap.
6. DTS matching: there is no DTS-scaled leg return. Add `dts = mod_dur × g_spread` at t. Add leg return × 12 / DTS_leg. For HY, use the time-mean DTS of the TRACE HY universe in place of 12, because 12 is an IG number.

**Lag rule.**
- `esp_sr` uses panel rows with `available_at` ≤ t + 1 day.
- EMC uses CRSP month-end returns with `available_at` ≤ decision time.
- Compustat ratios inside ESP use point-in-time vintages with `snapshot_available_at` ≤ decision time.
- DTS for the scale uses month-t `mod_dur` and `g_spread`, known at t + 1 day.
- The return runs from t to t + 1 month.

**Falsifiable test.**
- Signal: OneScore built to the book's rules on TRACE HY: maturity > 3 years, re-rank, up to 10 issuers per GICS sector a side, equal weight across issuers.
- Horizon: 1 month, rebalance monthly.
- Metric:
  - HAC t-stat of the monthly DTS-matched top-minus-bottom return.
  - Its correlation with the universe excess return in stress months.
  - Net-of-cost return with ½ · `cost_rt` · |Δw| per trade (ch. 18 cost model).
- Pass, all three must hold:
  1. The DTS-matched net return is > 0 in at least 3 of the 4 cycles 2008, 2015, 2020, 2022.
  2. The full-sample HAC t ≥ 2.
  3. The correlation with the universe excess return in stress months is below the correlation of the raw (unmatched) version.
- Fail on 1 or 2: OneScore stays a ranking aid in memos, not a position signal. Amend the decision page `2026-10-22-onescore`.

---

## Chapter 20. Does the Post-Earnings-Announcement Drift Extend to Credit Markets? (PDF pp. 641–680)

**Question.** Do corporate bond prices drift for weeks in the direction of an earnings surprise, and can a credit portfolio capture the drift?

**Answer.** Yes. Bonds of issuers with the most positive surprise outperform those with the most negative surprise for about 60 to 70 trading days. The equity announcement return (EAR) is the strongest of three surprise measures, and the effect is two to four times larger in HY than in IG (PDF pp. 642, 652–653, 658). An index-tracking portfolio that maximises EAR beats the index in both IG and HY (PDF pp. 673–674).

### Data

What the book says:

- Universe: all bonds in the Bloomberg Barclays US Corporate (IG) and US High Yield (HY) indices, January 2001 to December 2017 (PDF p. 643). Daily data starts in 2001. The sample starts there for that reason (note 4, PDF p. 679).
- Event results start in April 2001, because the bucket breakpoints need the previous quarter (PDF p. 652).
- Bond-to-equity mapping: Barclays proprietary map of Ben Dor and Xu (2015) (PDF p. 642; note 5, PDF p. 680). The map is not commercially available.
- Equity data: Compustat for stock prices, returns, book-to-market and market value (PDF p. 649).
- Earnings data: I/B/E/S for reported EPS and analyst forecasts (PDF p. 649).
- Benchmark for EAR: the 25 Fama-French size by book-to-market portfolios, from Kenneth French's data library (note 7, PDF p. 680).
- Filters (PDF p. 643):
  1. Drop issuers whose mapped equity is an ADR or trades over the counter.
  2. Cross-check the announcement date in Compustat and I/B/E/S. Drop the event if the two dates differ by more than two calendar days.
  3. Drop firms with no I/B/E/S analyst coverage.
  4. Drop firms without complete stock returns over the three-day window around the announcement.
- Final sample: 1,929 unique firms, 847 firms per quarter on average, 30 quarterly announcements per firm on average (PDF p. 643).
- Coverage by market value at end-2017: 84% of IG and 70% of HY (Table 20.1, PDF p. 644). HY coverage is lower because more HY issuers are private (PDF p. 643).

Table 20.1 (PDF p. 644), year-end market value and coverage:

| | 2001 | 2005 | 2009 | 2013 | 2017 |
|---|---|---|---|---|---|
| IG index ($bn) | 1,590 | 1,609 | 2,555 | 3,727 | 5,192 |
| IG mapped | 90% | 95% | 98% | 97% | 98% |
| IG in final sample | 68% | 77% | 82% | 81% | 84% |
| HY index ($bn) | 318 | 596 | 747 | 1,270 | 1,339 |
| HY mapped | 80% | 87% | 82% | 80% | 85% |
| HY in final sample | 64% | 66% | 58% | 54% | 70% |

The sample matches the index in sector mix, OAS and OASD (Figures 20.1 and 20.2, PDF p. 645). Announcements cluster in February and March, because Q4 reports come out with the annual report (Figure 20.3, PDF p. 646).

### Definitions and formulas

**Announcement date.** The quarter-q earnings announcement date $q_t$. The book takes it from Compustat and checks it against I/B/E/S (PDF p. 643). Compustat gives no time of day (note 11, PDF p. 680).

**SUE (defined, not used).** The book defines SUE and then drops it in favour of CFE (PDF pp. 646–647).

```latex
SUE_{i,q} = \frac{EPS_{i,q} - E(EPS_{i,q})}{\sigma_{i,q}}
```
Intuition: the surprise against a seasonal random walk, in units of past surprise volatility. $\sigma_{i,q}$ is the standard deviation of earnings surprises over the last eight quarters (PDF p. 647).

```latex
E(EPS_{i,q}) = EPS_{i,q-4} + \frac{\sum_{n=1}^{8}\left(EPS_{i,q-n} - EPS_{i,q-n-4}\right)}{8}
```
Intuition: the same quarter last year, plus the mean year-on-year change over the last eight quarters (seasonal random walk with drift, PDF p. 647).

**CFE, consensus forecast error (used).**

```latex
CFE_{i,q} = \frac{EPS_{i,q} - \text{Consensus}_{i,q}}{p_{i,q}}
```
Intuition: the EPS beat over the analyst consensus, per dollar of share price (PDF p. 647).

- $EPS_{i,q}$: reported EPS from I/B/E/S (PDF p. 649).
- $p_{i,q}$: stock close price at the most recent month-end before the announcement (PDF p. 647).
- Consensus: the mean of the most recent forecast of each analyst before the announcement date (PDF p. 649).
- Exclude analysts who stopped coverage before the announcement. Apply this rule in real time: keep an analyst whose stop was announced only after the announcement (note 10, PDF p. 680).
- Exclude estimates on an accounting basis different from the majority. I/B/E/S flags these in the IBDSL table (PDF p. 649).

**EAR, earnings announcement return (the main signal).**

```latex
EAR_{i,q} = \prod_{t=q_t-1}^{q_t+1}\left(1+R_{i,t}\right) - \prod_{t=q_t-1}^{q_t+1}\left(1+FF_t\right)
```
Intuition: the stock's three-day buy-and-hold return around the announcement, minus that of its size and book-to-market peer portfolio (PDF p. 648).

- Window: day $q_t-1$ to day $q_t+1$. The window ends at $q_t+1$ because some firms announce after the close (note 6, PDF p. 680).
- $R_{i,t}$: daily stock return. $FF_t$: daily return of the Fama-French 25 size by book-to-market portfolio that holds stock $i$ (PDF p. 648; note 7, PDF p. 680).

**BAR, bond announcement return.**

```latex
BAR_{i,q} = \sum_{j=q_t-1}^{q_t+1}\left(\sum_{k=1}^{N_i} w^{MV}_{k,j-1}\left(R_{k,j} - R_{peers,j}\right)\right)
```
Intuition: the issuer's bond return over the same three days, net of same-rating, same-industry peers, summed over days (PDF pp. 648–649).

- $R_{k,j}$: daily return of bond $k$. Use excess return for IG and total return for HY (PDF p. 649).
- $R_{peers,j}$: value-weighted return of index bonds in the same rating and industry bucket (PDF p. 648).
- Peer buckets: 4 ratings by 8 industries (PDF p. 648). Ratings: A+/A, Baa, Ba, B/B− (note 9, PDF p. 680). Industries: financials, basic industry, capital goods, consumer cyclical, consumer noncyclical, transportation and energy, technology and communications, utility (note 9).
- $w^{MV}_{k,j-1}$: weight of bond $k$ in the issuer, by market value of the previous day. The superscript $j-1$ is as printed (PDF p. 649).
- Daily abnormal returns are summed, not compounded, over days.

**Abnormal bond return, raw version (Table 20.4).** The daily abnormal return of bond $k$ is $R_{k,t} - R_{peers,t}$, aggregated to the issuer by market value (PDF pp. 648–649).

**Abnormal bond return, DTS-adjusted version (Tables 20.5 onward).**

```latex
R^{DTS\text{-}adj.abn}_{k,t} = R_{k,t} - \frac{DTS_{k,t}}{DTS_{peers,t}}\,R_{peers,t}
```
Intuition: scale the peer return up or down to the bond's own spread risk before you subtract it (PDF p. 655).

- $DTS_{k,t}$: duration times spread of bond $k$ on day $t$.
- $DTS_{peers,t}$: market-value-weighted mean DTS of the peer bucket on day $t$.
- Aggregate the daily bond values to the issuer, then sum over the window (PDF p. 655).

**Post-announcement drift (the target).** The sum of the issuer's daily abnormal returns from trading day $t+2$ over the next H trading days. H is 30, 60, 90 or 120 (PDF pp. 649, 652). Day $t+1$ is skipped. The skip keeps the drift window clear of the EAR and BAR window (note 11, PDF p. 680). Return units: excess return for IG, total return for HY (PDF p. 649). Panel C of Table 20.4 also shows HY in excess return (PDF p. 652).

**Regression variables (PDF p. 666).**

- Dependent: cumulative DTS-adjusted abnormal bond return over [2, 21], [22, 41] and [42, 61] trading days. Day 0 is the announcement date (note 16, PDF p. 680).
- Stock momentum: stock return over [−250, −21] trading days. That is 250 days, with the last 20 days skipped. The return is net of the matched Fama-French portfolio (Table 20.9 note, PDF p. 665).
- Stock reversal: stock return over [−20, −2], also net of the Fama-French portfolio.
- Past bond return: DTS-adjusted abnormal bond return over [−20, −2].
- lag(EAR): the EAR of the previous quarter.
- Controls: sector dummies and rating dummies.
- Preprocessing: trim all continuous variables at the 0.5 and 99.5 percentiles. Standardise each to mean 0 and standard deviation 1 within each year-quarter.
- Errors: clustered by year-quarter.

**Liquidity proxies (PDF p. 662; Table 20.8 note, PDF p. 663).**

- TES, the Barclays Trade Efficiency Score from 1 (liquid) to 10. TES combines LCS bid-offer cost and volume. The issuer value is the market-value-weighted bond TES at the last month-end before the announcement, rounded to an integer. TES exists only from 2007.
- Autocorrelation of the issuer's daily excess returns over [t−121, t−2]. It needs at least 60 daily observations. Rank into terciles each quarter.

**Tracking-portfolio ranking.** An issuer's EAR is the EAR of its most recent announcement in the past three months (PDF p. 670).

**ESP filter.** ESP is the Chapter 13 bond score from 1 to 10. It ranks a bond's spread over peers after it removes issuer characteristics and fundamentals. A high score means cheap (PDF p. 676).

### Implementation steps

**A. Event study (Tables 20.4 to 20.8)**

1. For each issuer and quarter, get the announcement date from Compustat. Check it against I/B/E/S. Drop the event if the dates differ by more than two calendar days (PDF p. 643).
2. Compute CFE, EAR and BAR as defined above.
3. Assign each event to a quintile of the chosen measure. Do this within its sector. Use the quintile cut-offs of the same sector and universe from the previous quarter (PDF pp. 651, 659). The lagged cut-offs make the step tradable. The sector split removes sector effects.
4. Track each issuer from trading day t+2. Sum the daily abnormal returns over H = 30, 60, 90 and 120 trading days (PDF p. 652).
5. Report the mean cumulative abnormal return per quintile and the Q5 − Q1 spread. Mark significance at 1%, 5% and 10% (Table 20.4, PDF pp. 653–654). The book does not state the test. Our reading is a two-sample t-test on event means.
6. Repeat with DTS-adjusted abnormal returns in both the target and BAR (Table 20.5, PDF pp. 656–657).
7. Split the Q5 − Q1 result by year, by industry, by rating and by liquidity (Figures 20.4 and 20.5, Tables 20.6 to 20.8).

**B. Regressions (Tables 20.9 and 20.10)**

1. Build the dependent variables over [2, 21], [22, 41] and [42, 61].
2. Run univariate pooled regressions on CFE, EAR and BAR, one at a time (Table 20.9, PDF p. 665).
3. Run the multivariate regression on CFE, EAR, BAR, stock momentum, stock reversal, past bond return and lag(EAR), with sector and rating dummies (Table 20.10, PDF pp. 667–668).
4. Use the trim, standardisation and clustering rules above.

**C. Tracking portfolio (Tables 20.11 to 20.13)**

1. Rebalance monthly (PDF p. 670).
2. Build the tracking universe. Keep senior bonds with more than three years to maturity. Keep bonds with notional above the 25th percentile of the index (PDF p. 670).
3. Keep one bond per issuer. If the issuer has eligible bonds younger than two years, drop its bonds older than two years. Then keep the bond with duration closest to the industry average (PDF p. 670).
4. Solve for weights that maximise the portfolio's weighted mean EAR. EAR is the issuer's latest EAR within the past three months (PDF p. 670).
5. Apply these constraints (PDF p. 670):
   - weight per bond ≤ 1% (base case) or ≤ 2% (variant);
   - sector weights equal to the index;
   - portfolio DTS equal to the index DTS;
   - portfolio OAS equal to the index OAS (one variant drops this).
   The book does not name the solver. Our reading: a linear programme with weights ≥ 0 that sum to 1.
6. Build the Min-EAR portfolio the same way, but minimise EAR (PDF p. 672).
7. Hold for one month. Report the return of Max-EAR over the index and of Max-EAR over Min-EAR (Table 20.12, PDF pp. 673–674).
8. Units: IG uses excess returns and the information ratio. HY uses total returns and a Sharpe ratio on one-month Libor (Table 20.12 note, PDF p. 674).
9. ESP variant: keep only bonds with ESP ≥ 5. Use a 2% cap. For HY, track a B/Ba subset of the index, because ESP exists only for bonds rated B and above (PDF p. 676).

No transaction costs enter any table. The tracking universe has a mean LCS of 0.95% in IG and 1.78% in HY (Table 20.11, PDF p. 671). The book does not net LCS out of the returns.

### Results

**Surprise statistics (Table 20.3, PDF p. 650).** All rows are in %.

| Universe | Measure | Mean | Std | 5th | 50th | 95th |
|---|---|---|---|---|---|---|
| IG | CFE | −0.39 | 38.40 | −0.38 | 0.05 | 0.66 |
| IG | EAR | 0.06 | 5.20 | −7.44 | 0.07 | 7.52 |
| IG | BAR | 0.01 | 1.06 | −0.64 | 0.00 | 0.71 |
| HY | CFE | −3.28 | 219.59 | −3.28 | 0.06 | 1.85 |
| HY | EAR | 0.01 | 9.44 | −13.63 | −0.03 | 13.43 |
| HY | BAR | 0.02 | 2.23 | −1.72 | 0.01 | 1.86 |

Rank correlations: CFE–EAR is 0.28 in IG and 0.32 in HY. CFE–BAR is 0.02 in IG and 0.11 in HY. EAR–BAR is 0.05 in IG and 0.18 in HY (PDF p. 650). CFE has fat negative tails from near-bankrupt firms with low prices (PDF p. 651).

**Raw abnormal returns, Q5 − Q1 (Table 20.4, PDF pp. 653–654).** Columns are H = 30 / 60 / 90 / 120 trading days.

| Panel | CFE | EAR | BAR |
|---|---|---|---|
| A, IG excess | 0.22 / 0.32 / 0.31 / 0.32 (all ***) | 0.37 / 0.53 / 0.59 / 0.57 (all ***) | 0.09** / 0.13** / 0.20*** / 0.15** |
| B, HY total | 0.76 / 0.90 / 1.14 / 1.22 (all ***) | 1.30 / 1.72 / 1.96 / 2.10 (all ***) | 0.32*** / 0.37** / 0.62*** / 0.62** |
| C, HY excess | 0.75 / 0.90 / 1.13 / 1.23 (all ***) | 1.32 / 1.74 / 1.99 / 2.15 (all ***) | 0.35*** / 0.41** / 0.72*** / 0.75** |

The EAR legs in IG: Q1 is −0.17 / −0.24 / −0.17 / −0.18 and Q5 is 0.20 / 0.29 / 0.42 / 0.39. In HY: Q1 is −0.56 / −0.82 / −1.00 / −1.24 and Q5 is 0.74 / 0.90 / 0.96 / 0.86 (PDF p. 653). In HY most of the spread at long horizons comes from the short (Q1) leg.

**DTS-adjusted abnormal returns, Q5 − Q1 (Table 20.5, PDF pp. 656–657).**

| Panel | CFE | EAR | BAR |
|---|---|---|---|
| A, IG excess | 0.13*** / 0.23*** / 0.17*** / 0.13* | 0.35 / 0.58 / 0.63 / 0.58 (all ***) | 0.04 / 0.13** / 0.12* / 0.06 |
| C, HY total | 0.92 / 1.28 / 1.58 / 1.83 (all ***) | 1.36 / 1.94 / 2.28 / 2.58 (all ***) | 0.21* / 0.34** / 0.61*** / 0.85*** |

The EAR spread holds or grows after the DTS adjustment. The DTS adjustment does not help BAR (PDF p. 658).

**Decay.** The cumulative drift rises steadily for about 70 trading days, then stops. It does not reverse (Figure 20.4, PDF p. 659). In HY the Q1 leg keeps falling beyond 70 days (PDF p. 658).

**By year.** EAR Q5 − Q1 is positive in every year from 2001 to 2017, in IG and in HY (Figure 20.5, PDF p. 660). The bar heights are readable only roughly. We do not quote them.

**By industry, EAR Q5 − Q1, DTS-adjusted, 30 / 60 / 90 days (Table 20.6, PDF p. 661).** All 48 cells are positive. The IG range at 90 days is 0.22 (consumer noncyclical) to 1.18 (financials). The HY range at 90 days is 1.19 (utility) to 3.33 (transportation and energy).

**By rating (Table 20.7, PDF p. 662).**

| Rating | 30 d | 60 d | 90 d | Median EAR Q1 | Median EAR Q5 |
|---|---|---|---|---|---|
| A or higher | 0.28 | 0.64 | 0.74 | −4.22 | 4.61 |
| BBB | 0.41 | 0.53 | 0.55 | −4.89 | 5.02 |
| BB | 0.80 | 1.10 | 1.18 | −7.56 | 7.60 |
| B or lower | 1.66 | 2.40 | 2.88 | −9.31 | 9.27 |

The spread grows as the rating falls. Part of the cause is larger surprises in lower ratings.

**By liquidity, EAR Q5 − Q1, 30 / 60 / 90 days (Table 20.8, PDF p. 663).**

| Proxy | Bucket | IG | HY |
|---|---|---|---|
| TES 1–3 | Liquid | 0.33 / 0.68 / 0.75 | 0.77 / 1.53 / 2.00 |
| TES 4–6 | Medium | 0.41 / 0.55 / 0.64 | 1.29 / 2.12 / 2.51 |
| TES 7–10 | Illiquid | 0.52 / 0.89 / 1.09 | 1.53 / 1.97 / 1.90 |
| Autocorrelation | Low | 0.43 / 0.68 / 0.78 | 1.86 / 2.35 / 2.97 |
| Autocorrelation | Medium | 0.34 / 0.49 / 0.56 | 1.38 / 1.98 / 2.32 |
| Autocorrelation | High | 0.28 / 0.52 / 0.51 | 0.83 / 1.44 / 1.24 |

The drift exists in the liquid buckets. With the autocorrelation proxy, the drift is larger for liquid issuers. The book concludes that illiquidity does not explain the drift (PDF p. 664).

**Univariate regressions, coefficient (t-stat) (Table 20.9, PDF p. 665).** Columns are [2,21] / [22,41] / [42,61].

| | IG | HY |
|---|---|---|
| EAR | 0.06 (9.26) / 0.05 (6.73) / 0.02 (2.51) | 0.15 (5.93) / 0.06 (7.62) / 0.05 (5.38) |
| CFE | 0.02 (2.63) / 0.02 (1.98) / 0.01 (1.19) | 0.07 (4.06) / 0.04 (2.95) / 0.03 (2.22) |
| BAR | −0.04 (−3.22) / 0.01 (0.60) / 0.01 (1.11) | 0.03 (1.91) / 0.03 (2.38) / 0.02 (1.81) |

The adjusted R² is 0.0% to 0.5% in IG and 0.1% to 2.2% in HY.

**Multivariate regressions, coefficient (t-stat) (Table 20.10, PDF pp. 667–668).**

| | IG | HY |
|---|---|---|
| EAR | 0.06 (8.84) / 0.05 (6.32) / 0.01 (2.07) | 0.14 (3.73) / 0.05 (6.23) / 0.04 (4.98) |
| CFE | 0.01 (0.69) / 0.00 (0.42) / 0.00 (0.36) | 0.04 (2.25) / 0.02 (1.49) / 0.02 (1.14) |
| BAR | −0.05 (−3.74) / 0.00 (0.19) / 0.01 (1.01) | −0.02 (−1.10) / 0.01 (0.59) / 0.01 (0.79) |
| Stock [−250,−21] | 0.01 (1.53) / 0.01 (2.06) / 0.01 (1.76) | 0.02 (2.21) / 0.03 (3.12) / 0.04 (4.02) |
| Stock [−20,−2] | 0.04 (5.94) / 0.03 (2.87) / 0.02 (2.34) | 0.07 (7.02) / 0.04 (3.77) / 0.03 (3.43) |
| Bond [−20,−2] | −0.06 (−3.33) / −0.02 (−1.36) / 0.00 (−0.14) | −0.05 (−2.49) / 0.04 (1.73) / 0.05 (3.48) |
| lag(EAR) | 0.01 (2.38) / 0.00 (−0.04) / −0.01 (−0.75) | 0.00 (−0.18) / 0.00 (0.39) / 0.00 (0.26) |
| Adj. R² | 1.2% / 0.3% / 0.1% | 2.9% / 0.9% / 1.1% |

EAR stays significant beside stock momentum, reversal, past bond return and lag(EAR). The text says CFE is no longer significant (PDF p. 666). The table shows HY CFE at t = 2.25 in [2,21]. The text and the table disagree on that one cell. BAR has a significant negative coefficient in the first 20 days in IG. Pre-crisis and post-crisis subperiods give similar EAR coefficients. The book does not report them (PDF p. 669).

**Tracking universe and portfolio (Table 20.11, PDF p. 671), monthly averages.**

| | # bonds | OAS (bp) | DTS | LCS (%) |
|---|---|---|---|---|
| IG index | 3,890 | 162 | 10.85 | 0.88 |
| IG tracking portfolio | 105 | 162 | 10.85 | 0.95 |
| HY index | 1,755 | 566 | 23.12 | 1.68 |
| HY tracking portfolio | 100 | 566 | 23.12 | 1.78 |

**Tracking portfolio performance (Table 20.12, PDF pp. 673–674).** "Over index" is Max-EAR minus index. "L/S" is Max-EAR minus Min-EAR. Returns are in %/yr. Ratios are annualised.

| Cap | Match | Universe | Over index: ret / TE / IR | L/S: ret / vol / IR |
|---|---|---|---|---|
| 1% | DTS + sector | IG | 0.87 / 1.17 / 0.74 | 1.74 / 1.20 / 1.45 |
| 1% | DTS + OAS + sector | IG | 0.40 / 1.10 / 0.36 | 1.48 / 1.10 / 1.35 |
| 2% | DTS + sector | IG | 1.12 / 1.54 / 0.73 | 2.45 / 1.85 / 1.32 |
| 2% | DTS + OAS + sector | IG | 0.60 / 1.33 / 0.45 | 2.01 / 1.68 / 1.20 |
| 1% | DTS + sector | HY | 1.97 / 2.65 / 0.74 | 3.06 / 2.41 / 1.27 |
| 1% | DTS + OAS + sector | HY | 1.96 / 2.88 / 0.68 | 3.04 / 2.37 / 1.29 |
| 2% | DTS + sector | HY | 2.73 / 3.15 / 0.87 | 5.02 / 3.51 / 1.43 |
| 2% | DTS + OAS + sector | HY | 2.48 / 3.14 / 0.79 | 4.72 / 3.56 / 1.33 |

Worst month of Max-EAR over the index (1%, DTS + OAS + sector): −1.67% in IG and −6.06% in HY. In IG, Max-EAR beats the index mainly early in the sample and from late 2008 to early 2011. Max-EAR minus Min-EAR rises steadily, and the slope is steeper after 2010 (Figure 20.6, PDF pp. 672, 675).

**ESP filter (Table 20.13, PDF p. 677), 2% cap, DTS + OAS + sector.**

| | Without filter: over index ret / IR | With ESP ≥ 5: over index ret / IR | ESP ≥ 5 Min-EAR ret / ratio |
|---|---|---|---|
| IG (excess) | 0.60 / 0.45 | 1.06 / 0.84 | 0.34 / 0.07 |
| HY B/Ba (total) | 1.78 / 0.79 | 3.25 / 1.14 | 7.95 / 0.74 (Sharpe) |

The filtered Max-EAR portfolio: IG 2.17%/yr excess at IR 0.51. HY B/Ba 10.67%/yr total at Sharpe 1.09 (PDF p. 677). A filtered Min-EAR portfolio does much worse. So ESP does not explain the whole gain (PDF p. 676).

### Robustness and variants

- Three surprise measures. EAR is the strongest, CFE is second, BAR is the weakest (PDF pp. 652, 664).
- Raw against DTS-adjusted abnormal returns. The EAR results hold or grow (PDF p. 658). With the DTS adjustment only in the target, results match the unadjusted case (note 13, PDF p. 680).
- HY in total against excess return. The two are almost the same (Table 20.4 Panel C).
- Every year, all 8 industries, and all 4 rating buckets give a positive Q5 − Q1 (PDF pp. 660–662).
- Both liquidity proxies. The drift does not rise as liquidity falls (PDF p. 664).
- Control for stock momentum, reversal, past bond return and lag(EAR). EAR survives (PDF pp. 666, 669).
- Pre-crisis and post-crisis subperiods give similar EAR coefficients. The book does not report them (PDF p. 669).
- Pooled IG plus HY regression with separate slopes. The HY slope stays larger (note 17, PDF p. 680).
- Tracking portfolio. Variants: drop the OAS match, use a 1% or 2% cap, use Min-EAR as the short, add an ESP ≥ 5 filter. Max-EAR beats the index in every variant (PDF p. 672).

### Limits and caveats

- Proprietary inputs: index membership, daily index returns, OAS, DTS, TES, LCS and ESP all come from Barclays. The bond-to-equity map is also proprietary (PDF p. 642).
- No costs: no table nets out transaction costs. The portfolio rebalances every month. The book does not report turnover.
- HY evidence covers public-equity issuers only. HY coverage is 54% to 70% of index market value (Table 20.1). Private HY issuers have no EAR.
- Stale signal: the portfolio treats an EAR from 3 months ago the same as an EAR from last week. The book says this is not efficient (PDF p. 675).
- The significance test of Tables 20.4 and 20.5 is not described. Event overlap within a quarter makes the stars likely optimistic. This is our reading.
- The HY Q5 − Q1 spread at long horizons comes mostly from the Q1 leg (Table 20.4 Panel B). Shorting HY bonds is costly. In a long-only book the gain comes from avoiding names, not from shorting them.
- The text and the table disagree on CFE significance in HY [2,21] (Table 20.10).
- The TES buckets differ between the text (1–3, 4–7, 8–10, PDF p. 662) and Table 20.8 (1–3, 4–6, 7–10, PDF p. 663).
- The sample runs from 2001 to 2017. It covers the 2008 and 2015 cycles but not 2020 or 2022.

### Implementation in this repo

**Mapping.** Methodology Section 9 (event-driven risk), with an equity-reaction feature in Section 8 next to S3. Specifically:

- 9.1 taxonomy: add the event type `earnings_announcement`.
- 9.5 post-event update: the signal is the post-event drift over t+2 to t+61. A position opened on the event exits when the drift window closes.
- S3: CFE is the consensus-gap part of S3, measured at the announcement.
- Code:
  - `hy/events.py`: event dates and EAR.
  - `hy/signals.py`: the EAR quintile and the drift signal.
  - `hy/peers.py` and `hy/groups.py`: the rating by sector peer buckets.
  - `hy/backtest.py` and `hy/walkforward.py`: the event study and the monthly tilt.
- Section 11 holds the test below.

**What we have.**

- Compustat `fundq.rdq`, the report date. It is already used in `hy/data/adapters/compustat.py` and `scripts/pull_sector_data.py`.
- CRSP daily stock returns.
- TRACE daily bond prices and G-spreads (`hy/sources/trace_panel.py`).
- Treasury curves (`hy/sources/treasury.py`), to turn total returns into excess returns.
- SEC filing timestamps (`hy/sources/edgar.py`). The 8-K Item 2.02 acceptance time gives the intraday timing that Compustat lacks.

**What we lack, and the proxy.**

| Missing | Proxy |
|---|---|
| Barclays index membership and index weights | Our HY universe from `trace_bonds`, with liquidity filters on TRACE trade count |
| Bond market value weights (no amount outstanding in the panel) | Equal-weight the bonds of an issuer. Or pull `amt_outstanding` from FISD on WRDS. |
| Index OAS and DTS | G-spread × spread duration from TRACE as DTS |
| I/B/E/S consensus | Pull `ibes.statsum_epsus` or detail `ibes.det_epsus` and `ibes.actu_epsus` via WRDS, if licensed. Without it, drop CFE and keep EAR. EAR needs only CRSP and the FF25 daily file. |
| Fama-French 25 daily | Kenneth French library (public) |
| Bond-to-equity map | CUSIP-6 issuer match from TRACE to the CRSP and Compustat CUSIP, plus a parent table. Check the match by hand on a sample. |
| TES and LCS | TRACE trade count and the Roll or bid-ask measure, for the liquidity split |

**Lag rule (no look-ahead).** Every field carries `as_of` and `available_at`.

- `EAR_iq`: `as_of` = announcement date $q_t$. `available_at` = close of $q_t+1$. Use it from $q_t+2$ only. This is the book's skip day (note 11).
- `CFE_iq`: `available_at` = the later of the I/B/E/S actual's `anndats_act` and the close of $q_t$. The consensus may use only forecasts with `anndats` before $q_t$.
- Quintile breakpoints: use the previous quarter's cut-offs per sector. Never use current-quarter cut-offs.
- Bond return windows start at the close of $q_t+1$.
- Rule: a feature is usable at decision time τ only if `available_at` < τ. The existing no-look-ahead test must cover the EAR and CFE fields.

**Falsifiable test.**

- Signal: EAR quintile within our sector buckets, with previous-quarter cut-offs.
- Universe: HY issuers in our TRACE panel with listed equity.
- Horizon: cumulative DTS-adjusted abnormal bond return from t+2 to t+61. Use total return for HY and peers matched by rating bucket and sector.
- Metric: mean Q5 − Q1 abnormal return, and the rank IC of EAR against that return. Use t-stats clustered by year-quarter.
- Pass:
  1. Q5 − Q1 > 0 with t ≥ 2 on the full sample.
  2. Q5 − Q1 > 0 in at least three of the four cycle windows 2008, 2015, 2020 and 2022, after a round-trip cost of one bid-ask (CLAUDE.md definition of done).
- Benchmark: the book's HY DTS-adjusted EAR Q5 − Q1 at 60 days is 1.94% (Table 20.5).
- Fail: if Q5 − Q1 ≤ 0 after costs in two or more cycles, drop EAR as a standalone signal. Keep EAR only as an event-risk input under Section 9.

---

## Chapter 21. Equity Short Interest as a Signal for Credit Investing (PDF pp. 681–718)

**Question.** Does the share of a company's stock on loan predict its bond downgrades and its bond returns?

**Answer.** Yes, as a one-sided signal. Issuers with high equity short interest (ESI) in their rating bucket get more downgrades over 3 to 12 months in every rating bucket (Table 21.5, PDF p. 690). In index-replicating portfolios matched on OAS, DTS and sectors, the max-ESI portfolio lags the index by 1.61%/yr in IG and 1.97%/yr in HY (Table 21.8, PDF p. 696). A raw quintile sort fails, because high-ESI issuers carry more spread risk (PDF p. 691).

### Data

What the book says:

- Bond universe: Bloomberg Barclays US Corporate (IG) and US High Yield (HY) indices, January 2007 to December 2019 (PDF p. 685).
- Inclusion, checked each month: the issuer's parent has common stock listed on a US exchange, and that stock is in at least one open lending transaction. If so, all of the issuer's index bonds enter the sample (PDF p. 685).
- Exclusion: ADRs. ESI in ADRs differs materially from ESI in common stock (PDF p. 685).
- Bond-to-equity map: Ben Dor and Xu (2015), Barclays proprietary (PDF p. 683).
- Lending data: FIS Astec Analytics, a commercial securities-lending data set (PDF p. 683).
  - Lenders and borrowers contribute the data. It is matched and aggregated to security level, at daily frequency.
  - The file is updated each morning for the previous trading day.
  - Identifiers: CUSIP or ISIN as of the report date.
  - Coverage is partial. Shares on loan are a lower bound.
  - A security appears only while at least one loan is open (PDF p. 683).
- Shares outstanding: Compustat North America (PDF p. 685).
- Sectors: the Bloomberg sector of the issuer's largest index bond, mapped to eight groups (note 5, PDF p. 718). The groups are consumer discretionary, consumer staples, energy and transport, financials and real estate, industrials, communications and IT, materials, and utilities.

Table 21.3 (PDF p. 686), share of index market value mapped to ESI:

| | 2007 | 2010 | 2013 | 2016 | 2019 |
|---|---|---|---|---|---|
| IG index ($bn) | 1,978 | 2,843 | 3,727 | 4,907 | 5,809 |
| IG mapped | 76% | 80% | 82% | 82% | 84% |
| HY index ($bn) | 629 | 930 | 1,270 | 1,334 | 1,277 |
| HY mapped | 57% | 57% | 58% | 66% | 75% |

Sample against index (Table 21.4, PDF p. 687):

| | Avg # bonds | OAS (bp) | DTS | IR | Max DD (%) |
|---|---|---|---|---|---|
| IG index | 4,557 | 153 | 11.52 | 0.22 | −20.05 |
| IG sample | 3,856 | 150 | 11.59 | 0.22 | −17.74 |
| HY index | 1,905 | 503 | 20.20 | 0.35 | −44.76 |
| HY sample | 1,213 | 442 | 18.52 | 0.33 | −40.63 |

The HY sample has lower spread and DTS than the HY index, because it has no private issuers (PDF p. 686).

### Definitions and formulas

**ESI, equity short interest (the signal).**

```latex
ESI_{i,t} = \frac{\text{Shares Lent}_{i,t}}{\text{Shares Outstanding}_{i,t}}
```
Intuition: the fraction of the company's shares out on loan. The book uses it as a proxy for informed shorting (PDF pp. 681, 686).

- Shares Lent: the FIS Astec field "Units" for the equity, which is the number of shares lent (PDF p. 684). Apply these filters (PDF p. 684):
  - Contract Type = A (any, which includes overnight and long term);
  - Loan Stage = A (all loans open at business close);
  - Collateral Type = A (cash and noncash).
- Shares Outstanding: from Compustat North America (PDF p. 685).
- Worked example: 2,000,000 shares lent and 100,000,000 shares outstanding give ESI = 2%. This is the 28 January 2020 row of Table 21.2. Its retail loan rate average is 3.55% (PDF p. 685).
- Note: ESI is shares on loan from securities-lending data. It is not exchange-reported short interest.
- Sample means: value-weighted ESI is 1.28% in IG and 3.27% in HY. Equal-weighted ESI is higher, so smaller firms carry more ESI (PDF pp. 686, 688).

**Signal date and lag.** Portfolios form on the last trading day of each month. They use each issuer's most recent ESI value (PDF p. 691). The downgrade test uses the ESI value from the previous month-end (PDF p. 689). The FIS Astec file for day d arrives the morning of d+1 (PDF p. 683). The book gives no further lag. Our reading: the month-end ESI is known by the next morning. A one-trading-day lag is the minimum.

**Lending fee.** The FIS Astec "Retail Loan Rate Average" is the weighted mean fee across all tickets for the security and date. It is used only descriptively. HY fees are higher than IG fees. The cheapest HY sector, industrials at 0.77%/yr, costs more than the dearest IG sector, utilities at 0.64%/yr (PDF pp. 684, 688). The fee is not used in any strategy.

**Rating notch scale (Table 21.5 note, PDF p. 690).** Aaa = 1, Aa1 = 2, …, C = 21, D = 22. A higher number is a worse rating.

- Issuer rating: the value-weighted mean of its bond ratings.
- Rating change: the end rating minus the start rating. The end rating is the last rating available at the earlier of the issuer's index exit or the window end.
- Changes are equally weighted within a quintile.
- A positive change means a downgrade.

**BSI, bond short interest (alternative signal).** BSI at bond level is the notional in lending transactions over the notional outstanding (note 7, PDF p. 718). Issuer BSI is the mean over all of the issuer's bonds that have at least one open lending transaction in the current month (PDF p. 698). The book says "average". It does not say whether the mean is weighted.

**CSI, combined short interest.**

```latex
CSI_{i,t} = z(ESI_{i,t}) + z(BSI_{i,t})
```
Intuition: equal weight on equity shorting and bond shorting. $z(\cdot)$ standardises the variable to mean 0 and standard deviation 1 each month (PDF p. 704).

**ESIvalue, short interest combined with relative value.**

```latex
ESIvalue_{i,t} = z(ESI_{i,t}) - z(ESP_{i,t})
```
Intuition: high values flag issuers that are both heavily shorted and expensive against their peers (PDF p. 712).

- ESP is the Chapter 13 bond score from 1 to 10. A high score means cheap.
- Company-level ESP is the value-weighted mean of the ESP of its index bonds (note 9, PDF p. 718).
- ESP exists only for bonds rated B and above (PDF p. 708).

**Interaction regression (PDF p. 707).**

```latex
r_{i,t+1} = a + b\,ESI_{i,t} + c\,BSI_{i,t} + d\,BSI_{i,t}\cdot ESI_{i,t} + \varepsilon_{i,t}
```
Intuition: the test asks whether the joint tail of ESI and BSI explains the return beyond each signal alone.

- The book prints the second term as "c BSI" twice. We read the first as ESI, as in Table 21.14.
- Data: monthly total returns of bonds in the HY replication universe, 2007 to 2019.
- Method: OLS with Newey-West standard errors (Table 21.14, PDF p. 708).

### Implementation steps

**A. Downgrade test (Tables 21.5 and 21.9)**

1. At each month-end, take each issuer's ESI from the previous month-end (PDF p. 689).
2. Within each of six rating buckets (Aaa/Aa, A, Baa, Ba, B, Caa/Ca/C), sort issuers into ESI quintiles (Table 21.5 note).
3. For each issuer, record the notch change over 3, 6, 9 and 12 months. Use the end-rating rule above.
4. Average the changes with equal weights within each quintile. Report Q1 through Q5 and the spread.
5. Repeat with BSI (Table 21.9, PDF p. 700).

**B. Quintile sort (Figure 21.3, Table 21.6)**

1. On the last trading day of each month, sort issuers within each of the eight sectors into ESI quintiles (PDF p. 691).
2. Value-weight issuers at formation. Hold for one month, then rebalance.
3. Report IG excess return over duration-matched Treasuries, and HY total return. The HY Sharpe ratio uses one-month Libor (PDF pp. 691–692).
4. The long-short is Q1 − Q5: long the least shorted issuers and short the most shorted.

**C. Index-replicating portfolios (Table 21.8, the main test)**

1. Rebalance monthly (PDF p. 694).
2. Build the replication universe (PDF p. 694):
   - senior bonds only;
   - time to maturity above three years;
   - notional above the 25th percentile of index notional at month-end.
3. Keep one bond per issuer. If at least one eligible bond is younger than two years, drop the bonds older than two years. Then keep the bond with duration closest to its industry average.
4. Choose weights that maximise the portfolio's mean ESI, subject to these constraints (PDF p. 694):
   - issuer weight ≤ 2%, which gives at least 50 issuers;
   - sector weights equal to the index;
   - portfolio OAS equal to the index OAS;
   - portfolio DTS equal to the index DTS.
   The book does not name the solver. Our reading: a linear programme with weights ≥ 0 that sum to 1.
5. Build Min-ESI the same way, but minimise ESI.
6. Hold one month. Report Index − Max, Min − Max (the "ESI strategy"), and Min − Index.
7. Units: IG excess return over a duration-matched Treasury portfolio. HY total return (Table 21.7 note, PDF p. 695).

The book reports no transaction costs. The max-ESI IG portfolio's LCS is 0.96% against 0.84% for the index. In HY it is 1.67% against 1.56% (Table 21.7). The book reports no turnover.

**D. Variants**

1. BSI: add the filter that the issuer has both ESI and BSI. Repeat steps B and C with BSI (PDF pp. 698–699).
2. CSI: repeat step C in HY with CSI (Table 21.12).
3. Double sort: build independent 5 × 5 quintiles on ESI and BSI in HY. Report counts, mean ESI, mean BSI and next-month total return per cell, with equal weights (Table 21.13, PDF p. 706).
4. ESP split: split the replication universe into expensive bonds (ESP 1–5) and cheap bonds (ESP 6–10). Run Max-ESI and Min-ESI in each (Table 21.15, PDF p. 711).
5. ESIvalue: run Max and Min on ESIvalue. The ESI strategy is Min − Max. The ESP strategy is Max ESP − Min ESP (Table 21.16, PDF p. 713).
6. EMC split (Appendix 21.1): split on Chapter 15 equity momentum score. EMC above 5 is high, 5 and below is low. Run Max-ESI and Min-ESI in each (Table 21.17, PDF p. 717).

### Results

**Downgrades, Q5 − Q1 in notches (Table 21.5, PDF p. 690).** Columns are 3 / 6 / 9 / 12 months. The column is printed "Q1–Q5", but the values equal Q5 minus Q1.

| Rating bucket | ESI | BSI (Table 21.9, PDF p. 700) |
|---|---|---|
| Aaa/Aa | .10 / .14 / .18 / .19 | .00 / .01 / .02 / .03 |
| A | .06 / .12 / .17 / .22 | −.01 / −.02 / −.03 / −.03 |
| Baa | .05 / .11 / .17 / .22 | .04 / .07 / .10 / .14 |
| Ba | .12 / .24 / .35 / .43 | .09 / .18 / .26 / .31 |
| B | .13 / .24 / .32 / .39 | .07 / .14 / .19 / .24 |
| Caa/Ca/C | .14 / .28 / .38 / .45 | .06 / .12 / .15 / .17 |

ESI separates downgrade risk in every bucket, and the gap grows with the horizon. At 12 months, the Q5 changes are .40 (Aaa/Aa), .24 (A), .17 (Baa), .41 (Ba), .29 (B) and .35 (Caa/Ca/C). BSI is weaker than ESI in every bucket. In IG, BSI shows no effect (PDF p. 699).

**Quintile sort (Figure 21.3, PDF pp. 691–692).** The Q1 − Q5 information ratio is −0.08 in IG and 0.16 in HY. The IG Q1 Sharpe is 0.22, the same as the index. The HY Q1 Sharpe is 0.82 against 0.77 for the index. The HY Q5 Sharpe is 0.38. The bar heights are readable only roughly. We do not quote them.

**Quintile characteristics (Table 21.6, PDF p. 693).** Columns are Q1 → Q5.

| | IG | HY |
|---|---|---|
| Quality (rating number) | 3.05 → 3.65 | 5.55 → 5.84 |
| OAS (bp) | 144 / 162 / 169 / 178 / 211 | 438 / 432 / 461 / 487 / 629 |
| DTS | 11.17 → 14.11 | 17.94 → 24.95 |
| LCS (%) | 0.19 → 0.33 | 0.83 → 0.79 |
| ESI (%) | 0.31 / 0.64 / 1.13 / 2.10 / 5.98 | 0.54 / 1.51 / 2.96 / 5.71 / 14.09 |

Q5 carries more spread and DTS. This explains why the raw sort fails.

**Replication universe and portfolio (Table 21.7, PDF p. 695).**

| | Bonds per month | OAS (bp) | DTS | LCS (%) | ESI (%) |
|---|---|---|---|---|---|
| IG index | 4,547 | 170 | 12.27 | 0.84 | 1.39 |
| IG replication universe | 546 | 174 | 11.79 | 0.84 | 1.80 |
| IG Max-ESI | 55 | 170 | 12.27 | 0.96 | 6.94 |
| HY index | 1,897 | 551 | 22.09 | 1.56 | 4.56 |
| HY replication universe | 400 | 493 | 20.59 | 1.43 | 4.78 |
| HY Max-ESI | 55 | 551 | 22.09 | 1.67 | 15.90 |

**Main result (Table 21.8, PDF p. 696).** Each cell gives annual return %, volatility %, IR or Sharpe, worst month %, and correlation with the index.

| | Min-ESI | Max-ESI | Min − Max | Index − Max | Min − Index |
|---|---|---|---|---|---|
| IG (excess) | 1.64 / 4.81 / 0.34 / −6.70 / 0.95 | −0.42 / 5.13 / −0.08 / −10.36 / 0.91 | 2.06 / 1.61 / 1.28 / −0.77 / −0.06 | 1.61 / 2.20 / 0.73 / −3.55 / 0.33 | 0.45 / 1.63 / 0.28 / −2.11 / −0.50 |
| HY (total) | 7.04 / 9.22 / 0.63 / −17.20 / 0.95 | 5.44 / 10.22 / 0.40 / −18.84 / 0.96 | 1.61 / 3.02 / 0.53 / −2.77 / −0.35 | 1.97 / 2.66 / 0.75 / −4.40 / −0.08 | −0.37 / 3.01 / −0.12 / −3.55 / −0.13 |

The IG index has an excess return of 1.18%/yr at IR 0.22. The HY index has a total return of 7.41%/yr at Sharpe 0.63.

- The index beats Max-ESI in 104 of 155 months in IG and in 100 of 155 months in HY (PDF pp. 697–698).
- In IG, most of the Min − Index gain comes from 2008 and 2009 (PDF p. 697).
- In HY, Min-ESI lags the index. The signal is one-sided: it finds losers, not winners (PDF p. 698).

**BSI replication (Table 21.11, PDF p. 702).**

- IG: Min − Max is −0.73%/yr at IR −0.45. Index − Max is 0.05%/yr. BSI fails in IG.
- HY: Min − Max is 2.52%/yr at IR 0.64. Index − Max is 1.26%/yr. Min − Index is 1.26%/yr.
- The book's reason for the IG failure: market makers borrow IG bonds to fill client buy orders. That borrowing carries no issuer information (PDF p. 699).
- After June 2009, IG Min − Max BSI is −0.15%/yr (PDF p. 703).

**BSI quintiles (Table 21.10, PDF p. 701).** Columns are Q1 → Q5.

- IG returns: 1.99 / 1.03 / 1.22 / 0.95 / 1.32 %/yr. The Q1 IR is 0.44.
- HY returns: 8.76 / 6.42 / 8.67 / 6.50 / 4.67 %/yr. Sharpe ratios: 0.90 / 0.61 / 0.80 / 0.57 / 0.36.

**CSI in HY (Table 21.12, PDF p. 705).**

| | Min-CSI | Min-ESI | Max-CSI | Max-ESI | Index − Max CSI | Index − Max ESI |
|---|---|---|---|---|---|---|
| Return (%/yr) | 7.11 | 7.03 | 5.54 | 5.31 | 1.97 | 2.19 |
| Sharpe or IR | 0.64 | 0.63 | 0.43 | 0.40 | 0.76 | 0.79 |

CSI does not improve on ESI.

- Cross-sectional correlation of BSI and ESI: Pearson 0.20 and Spearman 0.18 in HY, Pearson 0.14 and Spearman 0.01 in IG (PDF p. 704).
- Portfolio overlap: Max-ESI and Max-BSI share 22% of bonds. ESI and CSI share 57%. BSI and CSI share 62% (PDF p. 707).
- Double-sort returns: the ESI5 × BSI5 cell returns −2.12%/yr. The ESI5 × BSI1 cell returns 8.95%/yr (Table 21.13 Panel B, PDF p. 706). The two signals share their information in the joint tail.

**Interaction regression (Table 21.14, PDF p. 708).**

| | Column 1 | Column 2 | Column 3 | Column 4 |
|---|---|---|---|---|
| Intercept | 0.6135*** | 0.7005*** | 0.7513*** | 0.7333*** |
| ESI (b) | −0.0392*** | | −0.0329*** | −0.0298*** |
| BSI (c) | | −0.0359*** | −0.0249*** | −0.0188* |
| ESI × BSI (d) | | | | −0.0008* |

The printed column heads are "BSI", "ESI", "BSI and ESI" and "With interaction". The first two heads appear swapped against the row labels. We read column 1 as ESI alone and column 2 as BSI alone.

**ESI within ESP halves (Table 21.15, PDF p. 711).** Min − Max ESI, given as return %/yr and IR or Sharpe.

| | Whole universe | Expensive (ESP 1–5) | Cheap (ESP 6–10) |
|---|---|---|---|
| IG | 2.05 / 1.27 | 1.25 / 1.00 | 1.08 / 0.79 |
| HY | 1.60 / 0.53 | 0.93 / 0.95 | 1.86 / 0.87 |

ESI works inside both halves, so ESP does not subsume it. The company-level Spearman correlation of ESP and ESI is 0.08 in IG and −0.04 in HY (PDF p. 708).

**ESIvalue (Table 21.16, PDF p. 713).** Each long-short is given as return %/yr, volatility %, and IR or Sharpe.

| | ESI strategy | ESP strategy | ESIvalue strategy |
|---|---|---|---|
| IG | 2.05 / 1.61 / 1.27 | 2.06 / 1.47 / 1.40 | 3.37 / 1.39 / 2.42 |
| HY | 1.60 / 3.02 / 0.53 | 5.70 / 2.91 / 1.96 | 5.13 / 2.83 / 1.81 |

In IG the combination wins on both legs. Min-ESIvalue returns 2.45 at IR 0.50, and Max-ESIvalue returns −0.92 at IR −0.19. In HY, ESP alone beats the combination. ESI is best on the short leg and ESP is best on the long leg (PDF p. 712).

**ESI within EMC halves (Table 21.17, PDF p. 717).** Min − Max ESI, given as return %/yr and IR or Sharpe.

| | Low EMC | High EMC |
|---|---|---|
| IG | 1.33 / 1.14 | 1.28 / 1.05 |
| HY | 1.52 / 0.91 | 0.46 / 0.37 |

The Spearman correlation of EMC and ESI is −0.01 in IG and −0.09 in HY (PDF p. 715). The text calls Table 21.17 "Table 22.17", which is a typo (PDF p. 715).

### Robustness and variants

- Univariate sort against risk-matched replication. The sort fails and the matched portfolio works. Risk matching on OAS, DTS and sectors is required (PDF p. 698).
- BSI: it works in HY and fails in IG. ESI subsumes its information (PDF pp. 699, 703, 707).
- CSI: no gain over ESI (PDF p. 704).
- ESP halves and EMC halves: ESI holds in each, except for weak results in HY high-EMC (Table 21.17).
- ESIvalue: a large gain in IG, no gain in HY (PDF p. 712).
- The book reports no subperiod split of Table 21.8. Figure 21.4 shows Index − Max rising through the whole IG sample (PDF p. 697).

### Limits and caveats

- Proprietary inputs: FIS Astec lending data is commercial, and Barclays did not release it. Index OAS, DTS, LCS, ESP, EMC and the bond-to-equity map are Barclays data.
- The lending data covers only part of the market. ESI is a lower bound, and a missing value can mean "no loans" or "no reporter" (PDF p. 683).
- No costs or turnover are reported. All returns are before costs.
- The sample runs from 2007 to 2019. It covers the 2008 and 2015 cycles but not 2020 or 2022.
- HY coverage is 57% to 75% of the index (Table 21.3). The ESP variants cover only B-and-above names (54% coverage, PDF p. 708).
- One-sided: in HY, Min-ESI does not beat the index (Table 21.8). The value is in avoidance or underweight, not in a long tilt.
- Printed errors: the "Q1–Q5" heads in Tables 21.5 and 21.9 show Q5 − Q1. The regression formula on PDF p. 707 has a typo. The column heads of Table 21.14 appear swapped. The text cites "Table 22.17" for Table 21.17.
- Index statistics differ across tables. The HY index volatility is 10.89 in Table 21.8 and 9.61 in Table 21.16. The book does not explain the difference.

### Implementation in this repo

**Mapping.**

- Methodology Section 8, S6 (rating migration and forced flows): ESI is a direct predictor of the 3- to 12-month downgrade probability. It feeds `P(down_12m | gap_i)` in S6.
- Section 9.1 (event taxonomy): an ESI jump into the top quintile of its rating bucket is a negative positional-risk flag.
- Section 11 (backtest): the replication test and the downgrade test.
- Code:
  - `hy/signals.py`: the ESI feature and the quintile within rating and sector.
  - `hy/calibration.py`: the downgrade-probability uplift by ESI quintile.
  - `hy/rv.py` and `hy/peers.py`: the ESIvalue combination with our ESP analogue.
  - `hy/backtest.py`: the matched long-short.

**What we have and lack.**

| Need | Status | Proxy or source |
|---|---|---|
| Shares on loan (FIS Astec) | Lack | Compustat `comp.sec_shortint` on WRDS. It holds exchange-reported short interest (`shortint`) per `gvkey`/`iid` and `datadate`, twice a month. It counts settled short positions, not shares on loan. It is our closest proxy. Markit Securities Finance is the closer match if WRDS licenses it. |
| Shares outstanding | Have | CRSP daily `shrout`, or Compustat `cshoq` |
| Bond-to-equity map | Partial | CUSIP-6 issuer match from TRACE to CRSP and Compustat, plus a parent table |
| Bond short interest (BSI) | Lack | None on WRDS. Skip BSI. The book shows ESI subsumes it in HY. |
| Index OAS, DTS and sectors | Lack | G-spread × spread duration from TRACE as DTS. Use our sector map. |
| Ratings history | Need | Mergent FISD ratings on WRDS, for the downgrade test |
| ESP | Lack | Our peer-residual spread from `hy/peers.py` |

**Lag rule (no look-ahead).**

- Each `sec_shortint` row has `datadate` = the settlement date. Store it as `as_of`.
- The exchanges publish short interest some business days after settlement. Set `available_at` = `datadate` plus the observed publication lag. Measure that lag from the FINRA calendar before use. Never use zero.
- `ESI_it` = `shortint` / `shrout`. Take `shrout` from CRSP as of `as_of`. Take `available_at` from the later of the two inputs.
- At month-end τ, use the latest ESI with `available_at` < τ. This matches the book's "most recent value" at the last trading day (PDF p. 691).
- Ratings: use the rating effective date as `as_of`, and the publication date as `available_at`.

**Falsifiable tests.**

1. **Downgrade test (S6).**
   - Signal: ESI quintile within each rating bucket (Ba, B, Caa/Ca/C), at each month-end.
   - Horizon: 6 and 12 months.
   - Metric: Q5 − Q1 mean notch change, on the book's scale with D = 22.
   - Pass: at 12 months, Q5 − Q1 > 0 in all three HY buckets, with t ≥ 2 (Newey-West).
   - Benchmark: the book's 12-month values are .43, .39 and .45 (Table 21.5).
   - Fail: if Q5 − Q1 ≤ 0 in any bucket, `sec_shortint` does not proxy FIS Astec. Drop ESI from S6.
2. **Return test (Section 11).**
   - Signal: the Max-ESI portfolio against our HY universe. Match DTS, G-spread and sector weights. Cap each issuer at 2%. Rebalance monthly and hold one month.
   - Metric: annualised (universe − Max-ESI) total return, after a one-bid-ask round-trip cost on turnover.
   - Pass: positive in at least three of the four cycle windows 2008, 2015, 2020 and 2022, with full-sample IR ≥ 0.3.
   - Benchmark: the book reports 1.97%/yr at IR 0.75 before costs (Table 21.8).
   - Use: treat ESI as an underweight screen only. Do not treat it as a long signal, because Min-ESI lags the HY index (Table 21.8).
