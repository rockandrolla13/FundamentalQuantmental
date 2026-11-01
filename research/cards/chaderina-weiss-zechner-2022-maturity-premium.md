# Chaderina, Weiss and Zechner (2022), "The maturity premium"

Journal of Financial Economics 144, pp. 670–694, DOI 10.1016/j.jfineco.2021.07.008. Peer-reviewed. Open access under CC BY. **Evidence from equities.** We read the journal version (25 pages) from `opinvisindi.is`. Page numbers are PDF pages. Printed page = PDF page + 669.

## Claim
Firms with longer debt maturity earn an equity premium of 0.21% a month that unconditional factor models do not explain (pp. 1–2, 6). Long-term debt is sticky, so leverage and beta stay high in downturns, when the price of risk is high (pp. 1–2). A conditional CAPM removes the alpha (p. 20).

## Method
**Measure (p. 4).** DM is the share of long-term debt due in more than three years, from Compustat.

**Sort (pp. 5–6).** Monthly double sort into size quintiles and then conditional DM quintiles. LMS is long the long-maturity bucket and short the short-maturity bucket, equal across size groups.

**Model (pp. 6–7).** A partial-equilibrium dynamic trade-off model on DeMarzo and He (2020). Firms refinance maturing debt each instant and can change face value then. Shareholders do not buy back debt, because the buyback gives wealth to remaining creditors (p. 2).

**Crisis experiment (pp. 15–17).** Pick firms with an average maturity at origination of 5 to 7 years in December 2007. Sort them on the remaining DM of fiscal 2007 at the 40th and 60th percentiles.

```latex
Lev_{i,t} = \alpha_i + \tau_t + \beta\,(Post_t \times LT_i) + \epsilon_{i,t} \quad (\text{Table 7, p. 16})
```

Intuition: firms with the same preferred maturity differ in remaining maturity only because of past issue dates, so the shock sorts them by chance.

**Conditional test (p. 20).** Conditional CAPM of Boguth et al. (2011), with the beta of LMS allowed to vary.

## Data
CRSP and Compustat, January 1976 to December 2017. 1,840,640 firm-months and 18,392 firms (p. 4). Financials are included in the base case (p. 4, n. 3). Crisis sample: 108 short, 54 medium, 108 long firms (Table 6, p. 16).

## Result
- LMS alpha (Table 3, p. 6): CAPM 0.21% (t 2.93), FF3 0.15% (t 2.31), FF5 0.10% (t 1.67). Smallest size group CAPM 0.44% (t 2.98). The two largest size groups: 0.04% and 0.03%, not significant.
- Value premium in the same sample: 0.37% a month (p. 2). LMS loads on HML, 0.18 (t 3.92) in FF5 (p. 6).
- Calibrated model: long-short alpha 0.19% a month (p. 2).
- Crisis leverage (Table 7, p. 16): short-maturity firms +14%, long-maturity firms a further +3%.
- Crisis beta (p. 17): the long-short beta is negative in the second half of 2008. It is positive and significant from 2009.
- Stickiness (p. 18): slope of debt change on excess leverage is −1.1 for the short quintile and −0.22, insignificant, for the long quintile.
- Annual leverage change at high excess leverage (Table 8, p. 19): short −14.88%, long −7.24%.
- Beta of LMS against price of risk: correlation 0.48 quarterly (p. 19).
- Conditional alpha of LMS: 0.11% (t 1.52) (Table 9, p. 20).

## Limits
- Equity returns. Bond returns and spreads are not tested.
- The effect is in small firms (p. 6). The FF5 alpha is weak (t 1.67).
- Model has no seniority and no transaction cost (p. 6). It holds maturity choice fixed (p. 4).
- DM comes from Compustat buckets.
- The sort does not hold leverage fixed. Long buckets have higher leverage: 32.08% against 23.89% (Table 2, p. 5).
- One crisis for the experiment.

## Section touched
`docs/methodology.md` Section 4.7 (time profile of the debt clock), Section 9.1 (event window after a shock), Section 8 (cycle-phase weights).

## Use for the two clocks
This section is our proposal, not the source's claim.

**What the source says.** Short debt and long debt carry risk at different dates. Short-maturity firms spike first and then delever. Long-maturity firms stay at high leverage and high beta for longer (pp. 2–3, 17). The authors say the short-term premium of Friewald et al. fits their view of short-maturity firms as risky over short horizons (p. 3).

**What our data says.** Section 4.7 reports +0.36 (t 2.0) on debt due after year 2 (the backtest fixes the revenue clock at 2 years, `hy/sources/clock_facts.py`). This has the same direction as this paper's long-maturity risk. But our coefficient is a spread level, not a return, and no control enters. We cannot claim support.

**What we decide.**
1. Add event-time windows to every clock test: month 0 to 6 and month 7 to 36 after a shock. Our choice, v0. Short-dated debt should show in the first window. Long-dated debt should show in the second.
2. Add `leverage_stickiness`: the issuer's slope of debt change on excess leverage, from filings. Use it as a state variable of the debt clock.
3. Copy the assignment: within issuers of similar maturity at origination, use remaining maturity at the shock date.

**Test.** In the panel of `nagler-2020-bond-rollover-channel.md`, split the post-shock path by remaining DM. Pass: the short-DM group widens more by month 6, and the long-DM group stays wider at month 24. Run on 2008 and 2020, the two windows with a sharp shock. Our choice, v0. Treat equity evidence as a prior only.
