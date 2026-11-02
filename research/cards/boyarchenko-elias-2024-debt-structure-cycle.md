# Boyarchenko and Elias (2024), "Corporate Debt Structure over the Global Credit Cycle"

Federal Reserve Bank of New York Staff Report 1139, December 2024, DOI 10.59576/sr.1139. Working paper. Corporate bonds and loans, global. We read the staff report (63 pages). Page numbers are PDF pages. PDF page = printed page + 2.

## Claim
Firms prepay debt early for two motives: interest savings and maturity extension (p. 3). Tight global credit lowers the chance of prepayment and lowers what a prepayment achieves (pp. 2, 4). Debt then reaches maturity with higher probability, which exposes firms to rollover risk (p. 5).

## Method
**Events (p. 9).** Prepayment: an instrument last seen more than 12 months before contractual maturity. Maturity: last seen within 12 months of it. Issuance: first seen.

**Interest incentive (p. 15).** Linear probability model at the instrument level.

```latex
Prepayment_{i,t+1} = \beta_0 + \beta_R\big(IR_{i,t} - IR_{c,t}\big) + \ldots + \epsilon_{i,t} \quad (1)
```

Intuition: an instrument whose coupon sits above new issue coupons for peers is in the money for a refinance. Peers share country-year, currency, original maturity bucket and EDF tercile (p. 15). Included instruments have at least 1.5 years left, and absolute moneyness below 5% (p. 15).

**Maturity incentive (p. 18).**

```latex
Prepayment_{i,t+1} = \beta_0 + \beta_M \frac{Age_{i,t}}{Original\ maturity_{i,t}} + \ldots + \epsilon_{i,t} \quad (2)
```

Intuition: an old bond has little life left, so a firm that wants long debt refinances it first. Both β are step functions with country, firm and currency effects (pp. 15, 18).

**Cycle (p. 28).**

```latex
Prepayment_{i,t+1} = \beta_0 + \beta_I Incentive_{i,t} + \beta_G GCC_t + \beta_{IG}\, Incentive_{i,t}\times GCC_t + \ldots + \epsilon_{i,t}
```

Intuition: β_IG shows if tight credit weakens or strengthens each motive. GCC is the global credit factor of Staff Report 1094, compounded to annual (p. 27). Firm-level outcomes follow in equation (3) (p. 23).

## Data
Capital IQ Debt Capital Structure with Compustat, Worldscope and Moody's KMV EDF. 44 countries and 61,906 non-financial firms. 1,826,163 instruments, of which 108,090 enter the prepayment measure (p. 12). Comprehensive from 2002 (p. 11). The data carry no call schedule or covenant data and have sparse issue dates (pp. 10–11).

## Result
- Base rate for bonds: about 8.6% a year (p. 15, and Table 4a constant 8.62, p. 39).
- Interest incentive, bonds (Table 4a, p. 39): moneyness of at least 2.5 adds 2.98 points (se 0.86). Negative moneyness has no effect.
- Maturity incentive, bonds (Table 8a, p. 43, against age share 0.5): at origination −13.66 points, at age share 0.8 and above +4.65 points. So a bond is far more likely to go in the last fifth of its life.
- Near maturity, the extension motive dominates interest savings (p. 21).
- Loans are prepaid more and are more sensitive to the maturity motive. In the pooled test, loans have a prepay rate 14 points higher (p. 19).
- Bond-issue events extend average maturity most when issuance comes with a retirement (p. 24). Refinancing for maturity lengthens maturity, and refinancing for interest lowers coupons (p. 26).
- Cycle, bonds (Table 20, p. 55): global credit −0.92 (se 0.32) on prepayment. Moneyness × global credit 0.05, not significant.
- Cycle, maturity motive (Table 21, p. 56, bonds): global credit −1.47 (se 0.14). Maturity incentive × global credit +2.57 (se 1.38). Firms prepay less, but react more to age in tight conditions (p. 29).
- Effectiveness (pp. 30–32): in tight conditions, EDF falls less, maturity rises less, and coupons fall less after a prepayment.

## Limits
- Global sample. Bond share of firm debt averages 11% (p. 13), so loan-reliant firms dominate.
- No call provisions (p. 10), so a "prepayment" mixes calls, tenders and exchanges.
- Annual frequency and accounting-date timing (p. 11).
- With the global financial cycle factor in the same regression, the maturity interaction is not significant (p. 30). This sits against the Table 21 reading on p. 29.
- The authors find no difference in cycle sensitivity by firm risk (p. 8). They state that this differs from Mian and Santos (2018), which we did not open.

## Section touched
`docs/methodology.md` Section 4.7 (effective debt clock), Section 5.3 (`p_refi_h`), Section 9.1 (maturity and refinance window, call date or tender), Section 9.2 (`M_τ` in the rate channel).

## Use for the two clocks
This section is our proposal, not the source's claim.

**What the source says.** The debt clock is a choice. It runs off faster than the contract when incentives and credit conditions allow, and it stalls when credit is tight.

**What our data says.** `hy/clocks.py` uses the contractual ladder with no early retirement (`interest`: "no refinancing is assumed"). `docs/decisions/2026-10-22-alpha-backtest-design.md` builds the debt clock from filed ladders. We have no estimate of a hazard on our panel.

**What we decide.** Add an effective debt clock beside the contractual clock.

```latex
\Pr(\text{prepay}_{b,t+1}) = \Lambda\Big(a + b_1 \max(c_b - c^{peer}_t, 0) + b_2\, \tfrac{Age_{b,t}}{Mat_b} + b_3\, CallOpen_{b,t} + b_4\, GCC_t + b_5\, \tfrac{Age_{b,t}}{Mat_b}\times GCC_t + b_6\, Rating_{b,t}\Big)
```

Intuition: the expected date of a refinance moves with moneyness, age, the call schedule and credit conditions. `CallOpen` is our addition, because high yield bonds are callable and the source lacks call data.

Outputs: `effective_debt_grid`, `D_debt_eff`, and the gap to the contractual centre. `p_refi_h` of Section 5.3 and the `M_τ` of Section 9.2 then read the effective grid.

**Test.** On FISD actions, in high yield only. Pass: out-of-sample AUC above a model with age only, and a negative `b_4` in all four cycle windows. Our choice, v0. `D_debt_eff` must also lower the error of `p_refi_4` against realised refinancing. This test needs FISD call and redemption data, so it does not run in this sprint.
