# Moreira and Muir (2017), "Volatility-Managed Portfolios"

The Journal of Finance, DOI 10.1111/jofi.12513. Peer-reviewed. **Evidence from equities and currency carry, not credit.** We read NBER Working Paper 22208, April 2016, revised June 2016, 57 pages. Page numbers are PDF pages. The journal numbers may differ.

## Claim
A factor scaled by the inverse of last month's realised variance earns a large alpha on the factor itself (pp. 2–3). Variance is forecastable and does not forecast returns one for one, so the mean-variance trade-off weakens when variance rises (p. 3). The strategy takes less risk in recessions and crises (pp. 3–4).

## Method
**Scaling (pp. 7–8).**

```latex
f^{\sigma}_{t+1} = \frac{c}{\hat{\sigma}^2_t(f)}\, f_{t+1}, \qquad \hat{\sigma}^2_t(f) = RV^2_t(f) = \sum_{d=1/22}^{1}\Big(f_{t+d} - \tfrac{1}{22}\sum_{d} f_{t+d}\Big)^2
```

Intuition: hold less of a factor after a volatile month and more after a calm one. c sets the managed factor to the same unconditional sd as the original. The sample choice of c does not change the Sharpe ratio (p. 8, n. 5).

**Spanning test (p. 8).**

```latex
f^{\sigma}_{t+1} = \alpha + \beta f_{t+1} + e_{t+1} \quad (3)
```

Intuition: a positive α says that the scaled factor adds return per unit of the original factor's risk.

**Cost test (p. 13, Table 4, p. 35).** Market factor only. Alternatives that trade less: inverse vol, expected variance by AR(1) in logs, and caps on weight at 1 and 1.5.

## Data
Daily and monthly factors. Market, SMB, HML, momentum from 1926, RMW and CMA from 1963, ROE and IA from 1967, FX carry from 1983, all to 2015 (Table 1, p. 32).

## Result
- Alphas in percent a year (Table 1, p. 32): market 4.86 (se 1.56), HML 1.97, momentum 12.51 (se 1.71), RMW 2.44, carry 2.78, ROE 5.48, IA 1.55. SMB −0.58 and CMA 0.38 are not significant.
- Market beta 0.61, R² 0.37. Appraisal ratio 0.33 (p. 3, Table 2, p. 33).
- Mean-variance utility gain of 65% (p. 5).
- Recession beta (Table 3, p. 34): market managed 0.83, less 0.51 in recession, so 0.32 (p. 13).
- Subsamples, market alpha (Table 2, p. 33): 8.11 (1926–1955), 2.06 (1956–1985), 4.22 (1986–2015).
- VAR (p. 4): a mean-variance investor cuts risk by about 50% after a one-sd variance shock, then adds risk back as the shock fades.
- Alphas decline with the rebalancing horizon (pp. 4, 18–19).

**Cost (Table 4, p. 35).**

| Rule | Mean abs. weight change | Alpha | Alpha after 14 bp | Break-even |
| --- | --- | --- | --- | --- |
| 1 / RV² | 0.73 | 4.86% | 3.63% | 56 bp |
| 1 / RV | 0.38 | 3.85% | 3.21% | 84 bp |
| 1 / expected RV² | 0.37 | 3.30% | 2.68% | 74 bp |
| Capped at 1 | 0.16 | 2.12% | 1.85% | 110 bp |
| Capped at 1.5 | 0.16 | 3.10% | 2.83% | 161 bp |

## Limits
- No credit factor in the table.
- Cost test covers the market only, with equity costs (p. 13). Bond costs are far higher.
- Leverage reaches a 99th percentile weight of 6.4 in the base rule (p. 14).
- The alpha test needs a mix of scaled and unscaled portfolios with weights known only after the fact. `cederburg-et-al-2020-volatility-managed-real-time.md` tests this.
- Source note: appraisal ratio is 0.33 on p. 3 and 0.34 on p. 10.

## Section touched
`docs/methodology.md` Section 9.4 (position scale), Section 8 (sizing), and `docs/decisions/2026-10-26-conviction-book.md` layer 1.

## Use for the two clocks
This section is our proposal, not the source's claim.

**What the source says.** A scale on recent variance moves risk out of crises and earns alpha on equity factors. Caps cut trading by more than half and raise break-even cost.

**What our data says.** No test on our panel. The conviction-book page holds total DTS in a band set by phase. It has no volatility term. F26 uses a time-series trend.

**What we decide.**
1. Treat this as a candidate rule for the point inside the band, not as a new book. Scale the book DTS target by the inverse of realised volatility of daily HY index spread returns.
2. Use the capped form, because bond costs are high. Cap at the band limits.
3. Compare only by direct net Sharpe and drawdown against the static band, as Cederburg et al. advise. Do not rely on a spanning alpha.

Clock use: a clock feature that widens spreads in a shock has a volatility beta. Test whether scaling down in volatile months removes the rollover loss window that `nagler-2020-bond-rollover-channel.md` finds from August to December 2008.

**Test.** Arm of the conviction-book test against the static band (T2). Pass: higher net Sharpe in at least three of four windows, with turnover added below the break-even from `dickerson-nozawa-robotti-2025-factor-delays.md`. Stop here if the rule fails. Our choice, v0.
