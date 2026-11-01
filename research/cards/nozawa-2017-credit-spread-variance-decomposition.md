# Nozawa (2017), "What Drives the Cross-Section of Credit Spreads?: A Variance Decomposition Approach"

The Journal of Finance 72(5), pp. 2045–2072, DOI 10.1111/jofi.12524. Peer-reviewed journal article. We read the working paper, Finance and Economics Discussion Series 2014-62, dated August 2, 2014 (65 PDF pages), at https://www.federalreserve.gov/pubs/feds/2014/201462/201462pap.pdf. The journal text may differ. The volume and pages come from Crossref. Page numbers below are PDF pages of the 2014 file. PDF page = printed page + 1.

**Second copy, read at the audit close.** We also read the draft of February 9, 2016, 45 pages, at https://rmi.nus.edu.sg/wp-content/uploads/2020/10/43.-Yoshio-Nozawa.pdf. It sits closer to the journal date, and it gives a different view of ratings. Numbers from this copy carry the label "2016 draft". **We did not open the journal article**, so the journal's rating results stay unverified.

## Claim
A log-linear identity splits a corporate bond's credit spread into expected credit loss and expected excess return, with no default model (pp. 2, 9). Across all bonds, each part carries about half of spread variance (p. 4). Within junk bonds in the 2014 draft, the loss ratio is the larger one (p. 27). The 2016 draft shows a rating pattern instead: near even at Ba, and mostly loss only at B and below (2016 draft, p. 16). Expected loss variation is mostly idiosyncratic. Expected return variation is mostly systematic (p. 37).

## Method
1. **Spread and loss.** `s` is a price spread against a synthetic Treasury with the same cash flows, not a yield spread (pp. 11, 18–19). The cross-section correlation of the price spread with the yield spread is 0.82, and with yield spread times duration it is 0.97 (p. 12).

```latex
s_{i,t} = \log\big(P^{f}_{i,t} / P_{i,t}\big) \ (t < t_D), \qquad l_{i,t} = \log\big(P^{f}_{i,t} / P_{i,t}\big) \ (t = t_D) \quad (5,6)
```

Intuition: the spread measures how far the bond sits below its Treasury twin, and the loss is that same gap on the default date.

2. **Identity (p. 11, eq. 4; p. 13, eq. 7).** The expansion point is rho = 0.993 (p. 13).

```latex
r^{e}_{i,t+1} \approx -\rho\, s_{i,t+1} + s_{i,t} - l_{i,t+1} + const, \qquad
s_{i,t} \approx \sum_{j=1}^{T-t} \rho^{j-1} r^{e}_{i,t+j} + \sum_{j=1}^{T-t} \rho^{j-1} l_{i,t+j} + const
```

Intuition: a wide spread today must pay back later, as excess return or as credit loss, because the bond's life ends at maturity or default.

3. **VAR (p. 15).** Demean each state variable by month. Scale non-spread states by duration, because risk depends on time to maturity (p. 16). Slopes are constant across bonds and time. The base state vector is excess return, spread, and negative distance to default times duration (p. 19).

```latex
X_{i,t+1} = A X_{i,t} + B W_{i,t+1}, \qquad E\Big[\sum_j \rho^{j-1} l_{i,t+j} \mid X_{i,t}\Big] = e_L G X_{i,t}, \qquad e_1 G + e_L G = [0\ 1\ 0 \dots 0] \quad (8,9)
```

Intuition: the VAR projects each state forward and adds up the discounted forecasts, and the two long-run forecasts must sum to the spread itself.

4. **Key restriction (p. 23).** The long-run coefficients on any state other than the spread add to zero. So "variables other than the credit spreads" can forecast long-run excess return only if they "help credit spreads forecast long-run credit loss".

5. **Volatility ratios (p. 14).** `sigma(s^l) / sigma(s)` equals 1 under the expected credit loss hypothesis, and the ratio for returns equals 0. Standard errors use the delta method, clustered by time (pp. 17, 18–20).

6. **Nonlinearity (pp. 26, 29).** Fit the VAR by rating bucket, then pool the fitted parts.

7. **Diversification factor (p. 37).** A value near zero means the component is idiosyncratic.

```latex
DF_u = \frac{\sigma^2\big(s^{u}_{EW,t}\big)}{\overline{\sigma^2\big(s^{u}_{i,t}\big)}}, \qquad u \in \{l, r\}
```

Intuition: compare the variance of the market average with the mean variance of single bonds.

8. **Robustness.** Bootstrap of 10,000 paths under no return forecast (pp. 30–32). Out-of-sample cross-section regressions, Lewellen style, on 120-month and 240-month windows (pp. 33–35).

9. **Three-way extension, not estimated (pp. 63–65).** Add expected illiquidity `s^h` with a liquidity-adjusted return.

```latex
s_{i,t} \approx s^{r}_{i,t} + s^{l}_{i,t} + s^{h}_{i,t}
```

Intuition: an investor who expects to sell at a cost discounts the bond today, so expected trading cost also enters the spread.

## Data
- Monthly senior unsecured US corporate bonds, January 1973 to December 2011 (pp. 2, 20, 53). Sources in priority order: Lehman Brothers Fixed Income Database (1973 to 1997, bid quotes, some matrix prices), TRACE (2002 to 2011), Mergent FISD and NAIC (1994 to 2011), DataStream (1990 to 2011). Moody's Default Risk Service fills in default prices (pp. 16–18, 53–55).
- 546,815 bond-months in the full set (p. 56). The main sample of five-year bonds has 197,206 bond-months (p. 20).
- Rating counts: 28,507 BB, 28,923 B, 4,495 CCC and C (p. 27).
- Filters: price above the Treasury twin, price below one cent, and adjacent return product below -0.04 (p. 18). Callable bonds stay in, because few bonds were non-callable before the late 1980s (p. 18).

## Result
**All bonds, Table 2 (p. 22).**
- One-month loss on spread: 2.69 (se 0.91). One-month return on spread: 2.15 (se 0.98).
- Long-run loss on spread: 0.52 (se 0.16). Long-run return on spread: 0.48 (se 0.16).
- Long-run loss on distance to default times duration: 0.76 (se 0.34). Long-run return on the same state: -0.76 (se 0.34).
- Volatility ratios: 0.51 (se 0.16) for loss and 0.51 (se 0.15) for return.
- The standard deviation of expected return is 0.21% a month (p. 21).

**By rating, Table 4 (p. 27).**

| Bucket | sigma(s^l) / sigma(s) | se | sigma(s^r) / sigma(s) | se |
| --- | --- | --- | --- | --- |
| BB | 0.71 | 0.31 | 0.42 | 0.21 |
| B | 0.76 | 0.36 | 0.25 | 0.36 |
| CCC and C | 0.91 | 0.24 | 0.72 | 0.17 |
| Junk | 0.69 | 0.17 | 0.31 | 0.17 |
| Investment grade | 0.04 | 0.02 | 0.97 | 0.02 |

Pooled over six rating buckets, the ratios are 0.53 and 0.43, and the correlation of the two parts falls from 0.92 to 0.44 (pp. 27, 29–30).

**With market-level states, Tables 7 and 8 (pp. 39–40).**
- Linear VAR: diversification factor 0.10 for loss and 1.19 for return (p. 39).
- Rating-based VAR: factor 0.04 for loss and 1.24 for return. The correlation of the two parts is 0.01 (p. 40).
- Junk ratios: 0.61 (se 0.19) for loss and 0.47 (se 0.14) for return (p. 40).

**Out of sample, Table 6 (p. 35).** Junk slope on the VAR expected return: 0.70 (se 0.16) on a 120-month rolling window and 0.75 (se 0.22) on 240 months. Mean cross-section R² is 12.43% and 9.94%.

**Bootstrap, Table 5 (p. 31).** Under the null, the mean loss ratio is 1.05 and the mean return ratio is 0.21. The simulated p-value for the return ratio is 0.056. Fewer than 1% of paths give both a large ratio and a high positive correlation (p. 32).

**The 2016 draft (Table 2, pp. 16-17).** Holding all else fixed, one unit of spread forecasts long-run loss of 0.09 for A and above, 0.18 for Baa, 0.46 for Ba, and 0.89 for B and below. It forecasts premium of 0.90, 0.81, 0.54, and 0.12. The overall volatility ratios are 0.67 (se 0.12) for loss and 0.52 (se 0.06) for premium (pp. 3, 17). We found no junk table in this draft. These coefficients and the volatility ratios of Table 4 are different statistics, so they do not compare one to one.

**More states, Table 3 (p. 25).** With leverage, equity volatility and duration-scaled returns, the ratios are 0.53 and 0.47.

**Investment, Table 9 (p. 45).** At firm level, with both parts and controls, expected loss has -0.37 (se 0.15) and expected return has -0.17 (se 0.14). At market level, expected return has -4.19 (se 0.46) and expected loss has -1.37 (se 1.29).

## Limits
- The "excess return" part holds risk premium and mispricing together. The method does not split them. The author discusses both readings (pp. 42–43). An online appendix on systematic risk exposures (p. 34) was not opened.
- Illiquidity sits inside the return part. The author says TRACE and FISD are too short and too liquid to fit the three-way form (p. 65).
- Junk estimates are imprecise: the junk ratios have se 0.17, and the B return ratio is 0.25 with se 0.36 (p. 27). These are ratios of standard deviations, not shares, and the CCC pair does not add to one (p. 27).
- The diversification factors of Tables 7 and 8 cover all ratings. We found no junk diversification factor in the source.
- The method needs a sample that "covers at least several credit cycles" (p. 65).
- The sample mixes quotes, matrix prices and trades. Removal of matrix prices cuts the sample to 386,697 bond-months, and the loss ratio moves to 0.58 (pp. 56–57).
- Source inconsistency: the five-year column of Table 3 shows ratios 0.50 and 0.56 (p. 25). Table 2 shows 0.51 and 0.51 for the same specification (p. 22).

## Section touched
`docs/methodology.md` Section 7.1 (expected loss anchor), Section 7.3 and S1 (what the residual holds), Section 7.5 (expected convergence), Section 4.7 (test of a clock feature). Cross-reference: `gilchrist-zakrajsek-2012-credit-spreads-business-cycle.md`, `greenwood-hanson-2013-issuer-quality-bond-returns.md`.

## Use for the two clocks
**What the source says.** A state variable can forecast long-run return beyond spread only through long-run credit loss, with an equal and opposite coefficient (p. 23). Distance to default shows this pattern: +0.76 on loss and -0.76 on return (p. 22). Expected loss dominates at B and below. At Ba the split is near even (2016 draft, p. 16). Across all ratings, the factor is 0.10 for loss and 1.19 for return (p. 39). The source decomposes spreads, not residuals.

**What our data says.** Section 4.7 records the only result. The refinance share has +0.36 on log spread (t 2.0). The recontract share has -2.07 (t -2.4). Neither share ranks hedged returns beyond spread level. No VAR has run on our data. The panel with material RPO covers 2018 to 2026, 99 months. That panel does not meet the source's sample condition (p. 65).

**What we decide (our proposal, not the source's claim).**
1. **Pair test of a clock feature (changes the test of Section 4.7).** Add each clock feature times duration to `X`, and read its two long-run coefficients.
   - Loss coefficient above 0 and return coefficient below 0: the spread underprices the renewal bet. The feature is an unmodelled fact. It acts as a veto on S1, not as a long signal.
   - Both near zero: the feature adds nothing beyond spread. Keep it as a risk measure, as Section 4.7 does now.
   - Loss coefficient below 0 and return coefficient above 0: the spread overprices the renewal bet, and the feature can earn signal weight.
2. **Read the recontract sign with this split.** Section 4.7 notes that large, long-lease issuers may be stronger credits. Regress realised forward credit loss and forward excess return on the two shares, separately. A lower loss supports the stronger-credit reading. A lower return with no change in loss supports a premium or a mispricing reading.
3. **Split the S1 residual the same way.** Write the price spread as fitted part plus residual, and enter both in `X`. Compute the same volatility ratio for the whole spread on our own panel, by rating group, and read the residual beside it (Our choice, v0). A flat bar from the source has no use, because the source object differs and the rating pattern moves between drafts. That a wide residual is not mispricing by default is our inference from this source.
4. **Sample rule (our choice, v0).** Run the pair test first on cost clock features that need no RPO, because their history may start earlier. The start date needs a check in `hy/sources/clock_facts.py`. For RPO features, report the estimate and its standard error, and change no weight on that result alone.
5. **E5 weight.** A zero return coefficient gives no support for an alpha reading of E5. The 20% bucket is a user decision, so the card flags the result and changes nothing.
