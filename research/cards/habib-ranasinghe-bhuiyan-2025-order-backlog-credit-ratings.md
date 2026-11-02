# Habib, Ranasinghe and Bhuiyan (2025), "Sales Order Backlog and Credit Ratings"

Accounting in Europe, published online 5 May 2024, DOI 10.1080/17449480.2024.2345871. Peer-reviewed journal article. We read the publisher PDF from the Massey University repository, 28 pages. The publisher site returned 403 to the automated fetch. Page numbers below are PDF pages. PDF page = printed page + 1. Evidence class: US corporate issuers, credit ratings, no bond spreads.

## Claim
Firms with higher order backlog have higher credit ratings (p. 2). Rating agencies appear to treat backlog as a positive signal of future earnings (p. 2). When sales grow faster than backlog, ratings are lower. The authors also read a rise in backlog against sales as a positive signal (pp. 4, 8). Their own coefficient does not support that second sentence (see Limits).

## Method
**Model (p. 7, equation 1).** OLS of a numeric S&P rating on backlog, firm controls, and industry and year effects. Standard errors are clustered by firm.

```latex
RATING_{i,t} = b_0 + b_1 OB_{i,t} + b_2 DAC_{i,t} + \dots + b_{14} Z\_DUM_{i,t} + \sum_j \lambda_j IND_j + \sum_k \lambda_k YEAR_k + \varepsilon_{i,t} \quad (1)
```

Intuition: the regression asks whether a firm with more contracted orders gets a better rating than its ratios justify.

**Rating scale (p. 7).** 1 is D and 21 is AAA.

**Backlog measures (p. 8).** `LN_OB` is the log of backlog. `AVG_OB` is backlog over average assets. `ΔSALE-ΔOB` is the change in sales less the change in backlog, which the authors split into positive and negative values.

```latex
\text{Gap}_{i,t} = \Delta SALE_{i,t} - \Delta OB_{i,t}
```

Intuition: Lev and Thiagarajan (1993) read sales that outrun orders as a warning. The authors note that it may also mean strong demand (p. 23, note 4).

**Endogeneity (pp. 21-22).** Added governance and firm controls, entropy balancing, and two-stage least squares with the leave-one-out mean of backlog in the two-digit industry and year.

## Data
- US firms with S&P long-term issuer ratings from Compustat, without financials and utilities (p. 6).
- The baseline sample is 10,181 firm-years after screens (p. 7).
- Machinery and computer equipment make up 34.08% of observations. Stores and auto dealers make up 22.47% (Table 1, p. 7).
- Backlog comes from Capital IQ. It covers sales backlog and unfunded backlog. It is not available for railroads, finance, airlines or utilities (p. 23, note 3).
- Mean rating 10.49, which is about BB (p. 8). The sample leans to high yield.
- Backlog is unaudited and non-GAAP (p. 2).

## Result
**Baseline (Table 4 Panel A, p. 12).**

| Measure | Coefficient | Standard error |
| --- | --- | --- |
| `LN_OB` | 0.221 | 0.063 |
| `AVG_OB` | 0.441 | 0.221 |
| `ΔSALE-ΔOB`, all | -0.061 | 0.082 |
| `ΔSALE-ΔOB`, positive | -1.685 | 0.286 |
| `ΔSALE-ΔOB`, negative | 0.923 | 0.204 |

**Checks.** The ordered probit on `LN_OB` is 0.158 (se 0.047) (p. 13). Entropy balancing gives 0.217 (se 0.072) (p. 18). Two-stage least squares gives 0.288 (se 0.105) (p. 18).

**Industry split (p. 22).** In consumer durables, manufacturing and business equipment, `LN_OB` is 0.31 (t 2.68). In the rest it is positive and not significant.

**Macro (p. 22).** Untabulated: the coefficient on economic policy uncertainty is -0.006, and backlog times uncertainty is 0.0009 (both p below 0.01).

**A control of interest (Table 5 Panel A, p. 16).** Asset redeployability is 8.176 (se 2.176) in the rating regression, in one specification.

## Limits
- Ratings, not spreads or returns. A rating is not a test of mispricing.
- Backlog disclosure is voluntary in practice. Non-disclosers fall out of the sample (see `toynbee-2017-order-backlog-disclosure.md`).
- The sample ends in 2017, so it is before ASC 606 RPO data.
- The instrument is a peer mean, and such an instrument can affect the rating directly through industry conditions.
- The 25th percentile of `LN_OB` is 0 (Table 2, p. 9). So zeros matter, and the log form may reflect a zero group.
- Source inconsistency: the sample starts in 1980 in the abstract and in Section 3.1 (pp. 2, 6). It starts in 1987 in the introduction (p. 3).
- Source inconsistency: the authors convert 0.221 with `exp(0.221) - 1` (p. 9). The dependent variable is not in logs, so that conversion does not apply. We quote the raw coefficient.
- Source inconsistency: the "interquartile change" of `AVG_OB` uses the 75th percentile alone, 0.441 times 0.373 (p. 9).
- Source inconsistency: the shift from the 25th to the 75th percentile of the positive gap is written as a rise of 0.31 in rating (p. 15). With a negative coefficient, that shift lowers the rating.
- Source inconsistency: the negative part of the gap takes negative values, with mean -0.247 (pp. 8-9). Its coefficient is +0.923 (se 0.204) (p. 12). So a larger negative gap goes with a lower rating. Read by arithmetic, ratings fall as the gap moves away from zero on either side. The authors state the opposite for the negative part (pp. 4, 8). Our first reading copied the authors' text with no check.

## Section touched
`docs/methodology.md` Section 4.7 (revenue clock, RPO) and Section 7.2 (forward block of the fair spread). Section 7.3 residual. `hy/sources/clock_facts.py` (`RPO_MATERIAL`).

## Use for the two clocks
**What the source says.** The level of contracted orders is a credit positive in a rating. A change in orders against sales also carries information.

**What the data says.** The clocks use RPO only for timing. In the backtest RPO enters only through a filter: `RPO_MATERIAL = 0.25` of LTM revenue in `clock_facts.py`. So the amount of RPO has no role in the split test. Section 4.7 has no feature for RPO level or RPO drift.

**What we decide (our proposal, not the source's claim).**
1. Add two features to the forward block of Section 7.2. They explain the residual and they do not need timing data.

```latex
\text{rpo\_intensity}_{i,t} = \frac{RPO_{i,t}}{\text{LTM revenue}_{i,t}}, \qquad \text{rpo\_drift}_{i,t} = \frac{\Delta \text{Revenue}_{i,t} - \Delta RPO_{i,t}}{\text{average assets}_{i,t}}
```

Intuition: more signed revenue may lower risk. The source reads only the positive part of the gap as a warning.

2. Split `rpo_drift` into a positive part and a negative part, with no sign prior for either. `rpo_drift` may not be monotone, because the source's two slopes point to a fall in rating on both sides. The sign constraint in Section 7.2 stays off until a test fixes a sign.
3. Test. Regress log spread on `rpo_intensity`, the two parts of `rpo_drift`, and the panel-level Section 7.2 features. Read each sign against the permutation null. Then test the rank IC of each part beyond spread in the 2020 and 2022 windows, the only cycles with RPO data.
