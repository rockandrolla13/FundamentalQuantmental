# "Debt Refinancing and Corporate Bond Returns" (conference version, 30 October 2023)

Working paper. Corporate bonds, US. Proceedings file of the 2024 WDSI meeting (`wdsinet.org/Annual_Meetings/2024_Proceedings/papers/submission_109.pdf`, fetched by plain HTTP, because the HTTPS certificate failed), 60 pages. Page numbers are PDF pages. PDF page = printed page + 2 in the tables.

**Version and author note.** The file names no authors. A search listing of another copy (AUT, returned 403 to our fetch) names Yifei Li, Anni Wang, Qun Wu and Ting Zhang. The shortlist entry is Hou, Li, Wang, Wu and Zhang (2025), "Debt Refinancing, Distress Risk, and Corporate Bond Returns", DOI 10.2139/ssrn.4720640, SSRN only. We infer that this file is an earlier version. **We did not open the 2025 paper.** It may differ.

## Claim
Bonds of firms with more debt due soon earn higher excess returns in the next year (p. 2). Short-term leverage carries this premium and total leverage does not (p. 5). The premium sits in high yield, in illiquid bonds and in long bonds, and rises with tight credit, high rates and low sentiment (pp. 2, 25–36). It loads on credit and liquidity factors, and the authors read this as compensation (pp. 2, 39–40). The table does not settle that reading (see Result).

## Method
**Refinancing intensity (p. 17).**

```latex
RI_{j,t} = \frac{dd1 + dd2 + dd3}{dd1 + dltt}
```

Intuition: the share of a firm's debt that must meet the market within three years. Annual Compustat data, lagged six months (pp. 16–17).

**Panel (p. 20).** Monthly excess return over the T-bill on RI, with issuer and year effects, errors clustered by bond (p. 50).

```latex
R_{i,t+1} = \alpha + \beta RI_{j,t} + \gamma' X_{i,j,t} + \tau_t + \lambda_j + \epsilon_{i,t+1} \quad (4)
```

Intuition: ask if bonds of firms with more debt due soon earn more next month, at equal leverage and within an issuer. Controls: leverage, ROE, maturity, rating, issue size, reversal, Amihud illiquidity, call dummy (p. 21). Interactions with default risk, illiquidity, maturity, crisis, the funds rate and sentiment follow in equations (5) to (10) (pp. 24–35).

**Portfolios (p. 37).** Independent 2 x 3 x 3 sort on rating, maturity and RI. The premium is the high-RI return less the low-RI return, averaged across cells.

## Data
TRACE Enhanced, Mergent FISD, Compustat and CRSP. July 2002 to December 2020. 296,864 bond-months and 7,812 bonds (p. 16). Listed non-financial firms only (p. 15). 144A bonds excluded (p. 16). Median rating A−, mean maturity 10.46 years, mean RI 0.27 (p. 19). The rating row reads median 7 (A−) and 75th percentile 9 (BBB) (Table 1, p. 49). About 80% of bonds are callable (p. 19).

## Result
- RI coefficient 0.165 (t 3.18) with all controls (Table 2, p. 50). One sd of RI (0.16) adds 2.64 bp a month, about 32 bp a year (p. 21). Leverage is insignificant (p. 21).
- By credit (pp. 25–26): RI × HY is 1.19 (t 4.78). One sd adds 19 bp a month, or 2.28% a year, for high yield bonds. The plain RI term becomes insignificant. The RI effect is negative at AA− and above (p. 25).
- By maturity (p. 29): one sd adds 0.9% a year for long bonds relative to short bonds. Medium bonds show no significant difference.
- By illiquidity (p. 28): RI × high Roll illiquidity is 0.647, significant at 1%.
- Crisis (pp. 31–32): RI × GFC is 1.33 (t 3.87), or 21 bp a month per sd. RI × pandemic (February and March 2020) is 6.65 (t 5.92). Outside the crisis, RI is 0.079, significant at 10%.
- Rates (p. 34): per sd of RI, +5.62 bp a month at funds rate of 2% or more, +17.7 bp at 4.5% or more.
- Sentiment (p. 36, Table 8, p. 57): RI × high risk aversion is 0.432 (t 2.75). RI × low issuer quality is 0.968 (t 2.76).
- Long-short premium (Table 10, p. 59): equal weight 0.103 (t 2.18). FF3 intercept 0.086 (t 1.93). With default, term and liquidity factors, the intercept is 0.060 (t 1.19). Value weight 0.082 (t 2.01), and 0.074 (t 0.72) with those factors. Loadings on default are significant at the 10% level only (t 1.92 and t 1.79). Loadings on liquidity are 0.413 (t 2.28) and 0.248 (t 2.15).
- So the intercept keeps 58% and 90% of its size, and it loses significance because its error grows (our arithmetic). A failure to reject does not show that the factors explain the premium.

## Limits
- Mostly investment grade: median A− (p. 19). The high yield effect comes from an interaction, not a high yield sample.
- Listed firms only, no 144A bonds. Many US high yield issuers fall outside.
- No cost test. The portfolio rebalances monthly on an annual signal.
- The crisis terms use a dummy on the same month as the return. Their sign is high-RI bonds earn more within the crisis. Nagler (2015 version, pp. 30–31) finds high-rollover bonds widen more from August to December 2008. The two windows differ.
- The file reports 0.4% and 0.3% a month per sd of RI for high and medium EDF (p. 25). That looks too large beside 19 bp a month for high yield (p. 26) and 0.04% a month for BBB− (p. 25).
- Conference draft. Peer review unknown.

## Section touched
`docs/methodology.md` Section 4.7, Section 8 (composite signs for E5 and E8), Section 7.7 (risk premium test), Section 9.4 (wall limit).

## Use for the two clocks
This section is our proposal, not the source's claim.

**What the source says.** Near-term refinancing need earns a premium, and the interaction with a high yield dummy is positive. The sample has a median rating of A−, and the draft holds no high yield-only premium. The authors read the premium as compensation (p. 40). The draft's Table 10 cannot separate compensation from mispricing.

**What our data says.** E5 has an IC after cost of −0.082 (t −4.5) at 3 months and −0.114 (t −4.7) at 6 months, opposite to its sign (`docs/decisions/2026-10-22-alpha-backtest-design.md`). The page reads: "high-charge issuers earned their extra spread". The clock ICs beyond spread are not significant. Our file does not test this source. `e5` holds all obligations and has no timing (`hy/sources/clock_facts.py`), and the record uses a hedge at beta = 1. The source says that leverage does not predict returns (p. 21), so a leverage-like `e5` is a different object.

**What we decide.**
1. Add `refi_intensity_3y` (the RI formula) as a risk exposure in Section 8, not as a score with a long sign. Note that E8 rewards wall cover. RI is a ratio with no cash term and a three-year window, so it does not duplicate E8 or F21.
2. Ask a different question from "avoid or own". Report RI beside the conviction book as an exposure. Whether debt due soon earns compensation is open, and M5.3 reads it.
3. Test whether RI adds beyond spread, as for all clocks.

**Test.** On the TRACE panel: rank IC of RI beyond spread by rating cell, at 6 and 12 months. Keep RI as a signal only if it is positive in at least three of four cycles in the B and CCC cells after the costs in `dickerson-nozawa-robotti-2025-factor-delays.md`. Otherwise keep it as a risk report. Our choice, v0.
