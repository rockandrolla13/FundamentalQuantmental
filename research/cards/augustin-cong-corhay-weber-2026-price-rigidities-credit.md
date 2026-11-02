# Augustin, Cong, Corhay, and Weber (2026), "Price Rigidities and Credit Risk"

Journal of Financial and Quantitative Analysis 61(6), pp. 2737-2775, DOI 10.1017/S0022109025102512. Peer-reviewed, open access. We read the publisher PDF, 40 pages. Page numbers are PDF pages. Journal page = PDF page + 2736. Evidence class: S&P 500 firms, corporate bonds. No high yield sample.

**Added at the audit close.** The screen graded this paper 3, and the cap dropped it. An earlier automated fetch hit a bot check. A plain request on 2026-11-01 returned the open access file. We did not bypass any check.

## Claim
Firms with sticky output prices carry lower leverage, shorter debt, and a higher cost of debt (p. 1). Their credit spreads rise more after monetary shocks and after the Lehman failure, "especially when they face high preshock rollover risk" (p. 1).

## Method
**Measure (pp. 2, 20).** `FPA` is the frequency of price adjustment, from micro data of the Producer Price Index at industry level.

**Lehman test (p. 32, eq. 30).**

```latex
CREDIT\_SPREAD_{\ell it} = \alpha + \beta\,POST_t \times FPA_{jt} + \delta_1 FPA_{jt} + \delta_2 POST_t + \gamma' X_{\ell it} + \eta_t + \nu_k + \varepsilon_{\ell it}
```

Intuition: a firm that cannot change prices has less room when uncertainty jumps, so its spread should rise more.

**Triple difference (p. 35).** `TREATED` is rollover exposure above 10%, the share of debt due in 2009 (pp. 3, 35). The test reads `POST` x `TREATED` x `FPA`.

## Data
All firms ever in the S&P 500 over 1982 to 2018 (pp. 19, 22). TRACE bond transactions: 541,798 monthly observations, 12,500 bonds, 493 firms (p. 22). Bond issues: 6,858 bonds from 676 firms (p. 22).

## Result
The text layer of our copy drops minus signs in tables, so we read signs from the authors' text.

- **Lehman, panel (Table 9, p. 33).** `POST` x `FPA`: 0.67 in absolute value (t 2.79), up to 1.08 (t 3.71) with industry by month effects. The sign is negative: "credit spreads for fully sticky-price firms rise 67 bps more than those for fully flexible firms" (p. 32).
- **Lehman, cross-section (Table 9, p. 33).** 172 bp to 243 bp from two months before to two months after (p. 3).
- **Triple difference (Table 10, p. 35).** Full sample: 0.74 (t 2.34) to 1.24 (t 3.05) in absolute value. Matched sample: 1.49 (t 5.77) to 2.17 (t 4.09). The authors state that the triple interaction is negative (p. 35).
- **Pre-trend (p. 33).** Quarterly coefficients before the failure are indistinguishable from zero.

## Limits
- S&P 500 firms, so not a high yield sample.
- One shock for the triple difference.
- `FPA` is an industry measure from restricted micro data. Our panel cannot build it.
- We read pp. 1-3, 19-22, 32-36. We did not audit the model section.

## Section touched
`docs/methodology.md` Section 4.7, Section 9.1 (maturity row). `docs/decisions/2026-11-01-clocks-residual-timing.md` Method 4.

## Use for the two clocks
**What the source says.** Debt due soon amplifies a shock more for firms with rigid revenue. This is a test in spreads, with a stale exposure: debt due in 2009, read before the failure.

**What our data says.** No such interaction exists on file. Section 4.7 has no state term.

**What we decide (our proposal, not the source's claim).**
1. Add this paper as a third price source behind the debt term of Method 4, with the label S&P 500 firms.
2. Keep rigid prices as a lead. It needs a source for `FPA`.

**Test.** M4.3 reads the debt term. The rigid-price term waits for an `FPA` source.
