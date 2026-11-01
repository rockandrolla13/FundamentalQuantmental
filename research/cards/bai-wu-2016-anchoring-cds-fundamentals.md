# Bai and Wu (2016), "Anchoring Credit Default Swap Spreads to Firm Fundamentals"

Journal of Financial and Quantitative Analysis 51(5), pp. 1521–1543, DOI 10.1017/S0022109016000533. Peer-reviewed journal article. **CDS evidence, not bond evidence. Added by citation chasing.** The review screen marked this paper eligible in `residual_explanation` at grade 3, and the cap dropped it (`/home/ak/Gitrepos/sr-tracks/clocks-residual-timing/screening/leads_check.md`). We added it because Section 7.2 needs a fair level that can hold a sparse feature. We read a text extract of a JSTOR scan in the wiki staging folder (`bai-2016-anchoring-cds-spreads-firm-fundamentals.md`). The extract cuts the right edge of some lines. It lacks the t-statistics of Table 3 Panel B and the 4-week WCDS row of Table 4. Page numbers below are printed journal pages. The Internet Appendix was not opened.

## Claim
A Merton distance to default plus nine firm characteristics explains a mean of 77% of the weekly cross-section of log CDS spreads (Table 2, p. 1533). The market's deviation from this value forecasts the CDS change (Table 3, pp. 1538–1539). The authors read the deviation as "most likely driven by nonfundamental factors, such as supply-demand shocks" (p. 1537).

## Method
1. **Merton anchor (p. 1529, eqs. 4, 5).** Distance to default `d` uses total debt over market cap and 1-year realized stock volatility, with `T = 10` and `r = 0` for all firms.

```latex
RCDS = -6000 \ln N(d) / T, \qquad \ln CDS_t = f_t(\ln RCDS_t) + R_t
```

Intuition: turn distance to default into a spread unit, and let one local quadratic map per date absorb what the Merton form gets wrong about the level.

2. **One map per characteristic (p. 1530, eqs. 6, 7).** Our notation for equation 7, because the extract cuts it.

```latex
F^k_t = f^k_t(\ln MCDS_t) + x^k_t, \qquad R_t = g^k_t(x^k_t) + e^k_t
```

Intuition: remove what the anchor already knows from a characteristic, then allow a nonlinear link between the remainder and the anchor's error.

3. **Stack with shrinkage (pp. 1530–1531, eqs. 8, 11, 13).**

```latex
R_t = X_t W_t + e_t, \qquad W_t = (X_t'X_t + P_{t-1})^{-1}(X_t'R_t + P_{t-1}W_{t-1}), \qquad \ln WCDS_t = \ln MCDS_t + X_t W_t
```

Intuition: each week's weights start from last week's, so a feature keeps its weight only if it stays useful over time.

The prior is equal weights, and `theta = 0.98` sets the smoothness (p. 1531). The extract garbles equation 12, so we do not copy it.

4. **Missing values (pp. 1530–1531, eqs. 9, 10).** A firm's missing prediction takes a weighted mean of its available predictions. The prior prediction is zero. The error variance of each prediction is proportional to `1 - R^2` (p. 1531).
5. **Tests.**
   - Fit on a random half of firms and score on the other half (Table 2, pp. 1533–1534).
   - Weekly correlation of the deviation with the future CDS change, by paired difference between valuations (Table 3, p. 1538).
   - Long-short exercise on the deviation (eq. 18, p. 1539).

## Data
- Markit 5-year CDS, Capital IQ, OptionMetrics, CRSP (p. 1524).
- Every Wednesday from Jan. 8, 2003 to Sept. 30, 2009. 579 US nonfinancial firms, 351 weeks, 138,200 firm-weeks (p. 1524).
- Spreads above 10,000 bp dropped (p. 1524).
- A 45-day rule matches filings to market data (p. 1525).
- Nine characteristics: two leverage ratios, interest coverage, working capital over assets, EBIT over assets, retained earnings over assets, size, momentum, implied over realized volatility (p. 1525).
- Standard deviation of CDS: 345.71 bp across firms, 154.55 bp over time, 34.27 bp for the weekly change (p. 1527).

## Result
**Mean weekly cross-section R² (Table 2, pp. 1523, 1533–1534).**

| Valuation | Full sample | In-sample half | Out-of-sample half |
| --- | --- | --- | --- |
| Bivariate linear (BLR) | 49% | 51% | 25% |
| Merton map (MCDS) | 65% | 65% | 64% |
| Stack (WCDS) | 77% | 77% | 74% |

WCDS ranges from 67% to 85% over weeks, with a t-statistic of 54.46. The difference WCDS minus MCDS has a mean of 0.11, t 6.41 (Table 2, p. 1533).

**Largest weights (p. 1536).** Size, retained earnings over assets, and implied over realized volatility hold the highest positive weights. The two leverage ratios and interest coverage hold small weights, and these weights can turn negative. The authors say that the Merton measure already holds most leverage information.

**Forecast correlation of deviation with future change (Table 3, pp. 1538–1539).**

| Horizon | BLR | MCDS | WCDS | WCDS minus MCDS |
| --- | --- | --- | --- | --- |
| 1 week | −0.05 (t −7.11) | −0.06 (t −10.08) | −0.07 (t −15.89) | −0.02 (t −5.51) |
| 4 weeks | −0.09 | −0.10 | −0.12 | −0.02 |

**Investment exercise (Table 4, p. 1540).** Annualized information ratio by horizon.
- BLR: 0.13 at 1 week, 0.32 at 4 weeks.
- MCDS: 1.51 at 1 week, 0.80 at 4 weeks.
- WCDS: 2.26 at 1 week (mean 32.14%, standard deviation 14.22%), 1.98 at 2 weeks, 1.73 at 3 weeks. The text gives about 1.5 at 4 weeks, with a mean above 20% (p. 1541).

**Common variation (p. 1522).** The authors say that the regression residuals likely reflect common variation in risk premia. So they focus on the cross-section.

## Limits
- CDS, not bonds. The authors state that bonds add a term structure effect and a liquidity component (p. 1524). So the R² values do not carry over to our panel without a test.
- One sample of under seven years, with one crisis. The sample holds firms with CDS quotes, so it may underweight small HY issuers. The paper gives no HY split in the text that we read.
- The authors do not treat the exercise as a realistic backtest. Markit quotes are not executable, and OTC cost varies by institution (p. 1541). Table 4 shows no cost.
- Source inconsistency: the text gives a mean of 21.14% with a standard deviation of 14.22% and an information ratio of 2.26 (p. 1540). Table 4 gives 32.14%. Only 32.14% matches the ratio.
- The "supply-demand" reading is an inference from reversal (p. 1537). We found no direct test against a flow or a dealer measure in the text. Our reasoning, not the paper's: a negative forecast correlation also fits a stale quote.
- The weights use the full cross-section of each date, and no future dates, by construction. The 45-day rule is an assumption, and the paper checks it against Capital IQ filing dates (p. 1525).

## Section touched
`docs/methodology.md` Section 7.2 (`f_t`, the fair spread), Section 7.3 (residual), Section 7.5 (convergence), Section 4.7 (clock test), Section 3.1 (`cds_5y`). `hy/clocks.py`.

## Use for the two clocks
**What the source says.** A date-by-date stack can absorb sparse, noisy and nonlinear features. It gives each feature a weight, and it scores the result out of sample. The deviation from the stack forecasts the spread change more strongly at 4 weeks than at 1 week.

**What our data says.** As built, the Section 7.2 fair spread is the peer median. Section 4.7 reports the two renewal shares on 187 issuers with material RPO, in a monthly regression with no controls (`renewal_split_test` in `scripts/backtest_clocks.py`). RPO is sparse, so a plain multiple regression loses every other issuer. No anchor of this type has run on our data. We have no result for bonds.

**What we decide (our proposal, not the source's claim).**
1. **A research arm for the interim `f_t` (Section 7.2).** Use the same steps on bond spreads, with a maturity map first, because the source names term structure as the gap (p. 1524). Compare the deviation with the peer median residual, by rank IC beyond spread. This changes no live score until the comparison runs.
2. **Clock test by weight and by forecast.** Run the stack with and without each clock feature. Report three outputs:
   - The change in out-of-sample half R².
   - The path of the feature's weight `W_t`.
   - The paired difference in forecast correlation, as in the last column of Table 3.
   
   Pass rule (our choice, v0): the out-of-sample R² rises by at least one percentage point, and the paired difference has a t-statistic below −2. A clock weight near zero means that spread levels hold no use for the clock beyond the other features.
3. **Read the shape of the −2.07.** Plot the map of equation 7 for each renewal share, after the orthogonal step. This shows if the coefficient in Section 4.7 is a slope over the range or a tail effect. It also tests the untested Section 4.7 reason ("large, long-lease issuers are stronger credits"), because size and retained earnings sit in the same stack. A cost clock that acts as extra leverage may take a small weight, as the leverage ratios do here (p. 1536). So read a small weight on the refinance share with that in mind.
4. **Missing value rule for RPO.** Use equations 9 and 10 in place of a dropped issuer. Keep a flag for missing RPO. A missing value may carry meaning, since a firm may have no contracted revenue. The source does not cover this case.
5. **Do not read the deviation as mispricing by default.** The source infers transitory supply and demand. Other cards in this theme read a residual as a fact or as a risk (`mamaysky-shen-wu-2026-credit-information-earnings-calls.md`, `bartram-grinblatt-nozawa-2025-bond-book-to-market-mispricing.md`). Use the classifier of the Bartram card.
