# He, Khorrami, and Song (2022), "Commonality in Credit Spread Changes: Dealer Inventory and Intermediary Distress"

The Review of Financial Studies 35(10), pp. 4630–4673, DOI 10.1093/rfs/hhac004. Peer-reviewed journal article. We read NBER Working Paper 26494, November 2019 (81 PDF pages), at https://www.nber.org/system/files/working_papers/w26494/w26494.pdf. The journal text may differ. The volume and pages come from Crossref. Page numbers below are PDF pages. PDF page = printed page + 2.

## Claim
Two intermediary factors, a broad distress measure and a dealer bond inventory measure, explain about 50% of the common variation in credit spread changes beyond structural factors (p. 2). A margin-constraint model explains why loadings rise as credit quality falls (pp. 2–3).

## Method
1. **Structural residuals (p. 18, eq. 1).** Run a quarterly time series regression for each bond, following Collin-Dufresne, Goldstein, and Martin (2001).

```latex
\Delta cs_{i,t} = \alpha_i + \beta_{1,i}\Delta Lev_{i,t} + \beta_{2,i}\Delta VIX_t + \beta_{3,i}\Delta Jump_t + \beta_{4,i}\Delta r^{10y}_t + \beta_{5,i}(\Delta r^{10y}_t)^2 + \beta_{6,i}\Delta Slope_t + \beta_{7,i} Ret^{SP}_t + \varepsilon_{i,t}
```

Intuition: remove all that a structural model says should move the spread, and see what is left.

2. **Cohorts (pp. 18–19).** Assign each bond to one of 15 cohorts, three maturity groups by five rating groups. Average the residuals per cohort. Take principal components of the 15 series.
3. **Intermediary factors (pp. 12–15).**
   - `Delta Inventory^A`: quarterly log change of dealers' cumulative net customer order flow in par value, from enhanced TRACE with dealer identifiers. The authors adjust for maturity and primary trades (pp. 12–13).
   - `Delta Distress`: first principal component of the He-Kelly-Manela nonlinear leverage change and the Hu-Pan-Wang Treasury noise change (pp. 14–15).
4. **Residual regression (pp. 20–21, eqs. 2, 3).**

```latex
\varepsilon_{g,t} = \alpha_g + \beta_{1,g}\Delta Inventory^A_t + \beta_{2,g}\Delta Distress_t + u_{g,t}, \qquad FVE_G = 1 - \frac{\sum_{g \in G} u^{var}_g}{\sum_{g \in G} \varepsilon^{var}_g} \quad (2,3)
```

Intuition: the fraction of variance explained says how much of the residual that the structural model leaves behind is dealer balance-sheet stress.

5. **Placebo sort (p. 31).** Margin is the mechanism, so a sort on a variable unrelated to margin should show no loading pattern. The authors use maturity and trading volume.
6. **Spillover and segmentation (pp. 31–33).** High-yield inventory explains investment grade bonds and the reverse. Bond inventory explains CDS, not MBS, CMBS, ABS or index options. Distress explains all of them.
7. **Instruments (pp. 33–38).** Institutional sales of fallen angels and unexpected insured losses as instruments for dealer inventory.

## Data
- Enhanced TRACE, 2005 Q1 to 2015 Q2, with inventory built from 2002 Q3 (pp. 9, 12). FISD, CRSP, Compustat, eMAXX holdings, Markit CDS (pp. 10, 16–17).
- Baseline: 2,584 bonds, 653 firms, 55,938 bond-quarters (p. 11). About 35% of observations are high yield (p. 11).
- Senior unsecured, fixed coupon, no embedded options except make-whole calls. No financial or utility issuers (p. 10).
- A bond needs at least four years of consecutive quarterly changes (p. 11).

## Result
**Structural fit (Table 3, p. 45; p. 19).** Mean adjusted R² is about 30% to 40% at BBB and above and about 55% at BB and below.

**Commonality (Table 3, p. 45).** First PC explains 81.7% of residual variation and the second 5.6%. BB and B cohorts account for about 86% of total residual variation (p. 19). In monthly data, PC1 explains 76% (pp. 20, 23).

**Intermediary factors (Table 4, p. 46; p. 4).** They explain 53% of PC1. FVE for all residuals is 48.2%, about two thirds from distress and one third from inventory (p. 21). One standard deviation is linked to 3 to 30 bp a quarter for inventory and 5 to 60 bp for distress (p. 4).

| Cohort | Inventory (t) | Distress (t) | Adj. R² |
| --- | --- | --- | --- |
| Medium BB | 0.129 (3.05) | 0.251 (5.93) | 0.414 |
| Medium B | 0.278 (5.46) | 0.499 (6.48) | 0.647 |
| Long B | 0.362 (3.66) | 0.722 (4.30) | 0.591 |
| Medium AA | 0.011 (0.59) | 0.048 (3.96) | 0.140 |

**Liquidity adds little (Table 5, p. 47; p. 22).** The change in the Dick-Nielsen, Feldhütter and Lando illiquidity measure explains 3.2% of residual variation alone. It raises FVE from 48.2% to 48.8%. Its significance is mostly in high ratings. The authors note a correlation of 0.95 with the Bao-Pan-Wang measure (p. 22, note 22).

**Monthly (p. 23).** FVE falls to 20%.

**Instruments (Table 16, p. 58).** With the fallen-angel instrument, inventory effects are larger than OLS: 0.740 (t 2.18) in short B and 0.654 (t 2.80) in long B. The insured-loss instrument is weak (MP statistic 2.100 against a critical value of 12.374).

**Bond factors (Table 17, p. 59).** Distress explains the BBW-style return factors, which are themselves under dispute: LRF slope −1.120 (t −6.28), R² 0.586. Inventory is not significant there.

## Limits
- These are changes, not levels, and common variation, not cross-section mispricing. About half of the common part stays unexplained.
- Quarterly fit is high and monthly fit is lower, so horizon matters (pp. 19–20, 23).
- The sample needs four years of data per bond and drops all options except make-whole, so it favours survivors.
- Fallen angel sales are not fully exogenous. The authors state this caution (p. 33).
- Contemporaneous regressions. The paper is about explanation, not forecast. It offers no tradable test.
- The evidence that Collin-Dufresne et al. (2001) found 76% comes from this paper's description (p. 20). We could not open the 2001 paper.
- Friewald and Nagler (2019) explain 23% of PC1, and they report a first PC of 48%. This paper reports their numbers (pp. 8, 20). We did not open that paper.

## Section touched
`docs/methodology.md` Section 7.2 (`eta_sector,t` and the common part), Section 7.3 (residual), Section 7.5 (convergence), Section 3.6 and Section 9 (risk state). Related: the excess bond premium card `gilchrist-zakrajsek-2012-credit-spreads-business-cycle.md`.

## Use for the two clocks
**What the source says.** After structural factors, the residuals of credit spread changes are mostly one common factor, largest in low ratings, and half of it is dealer and intermediary stress. Standard illiquidity measures add little.

**What our data says.** Section 7.2 removes sector-by-date effects only. No test on our data shows how much common variation stays in the S1 residual. The conviction book does not use a dealer state.

**What we decide (our proposal, not the source's claim).**
1. **A common-factor check on the residual (changes Section 7.2).** Run the same step when `f_t` exists. As built, `eps` is a peer gap by sector, class, and maturity, so cohort means sit near 0, and the step does not apply. Use the correlation matrix of cohort means. Noise alone gives a first component near 13.5% for 12 cohorts and 99 months, and one thin cell can lift a covariance form to 76% (our simulation, `analysis/sensitivity/close/pc1_check.py` in the track folder). Compare with the 95th percentile after a shuffle of months per cohort.
2. **Fix for the residual.** Distress coefficients run from 0.048 to 0.499 between medium AA and medium B (p. 46). First-component loadings run from 0.055 to 0.431 (p. 45). Inside HY the gap is smaller: 0.251 at medium BB and 0.499 at medium B, about two times. A sector-by-date effect cannot remove this. So add rating-by-maturity-by-date effects, or loadings on the two factors. Test the change with S1's IC beyond spread.
3. **The clock sort as a placebo.** Build cohorts by clock quintile within rating, then run equation (2). If loadings rise with the clock inside one rating class, the clock is a margin or stress exposure, so it is a systematic risk measure. If loadings stay flat, then any clock effect on the residual is not this common part. This also tests the Section 4.7 phrase "risk measure".
4. **Risk state for sizing (our proposal, untested).** Section 7.5 fits one AR(1) speed for the residual. The model implies that dealer constraints hold prices away from value. So test the convergence speed of S1 by quartile of the distress factor and of the inventory factor. If convergence stops in high distress, then the phase band of `2026-10-26-conviction-book.md` should cut risk on that state. Otherwise, leave the band alone. The source does not test this.
5. **Keep the liquidity effect separate.** Liquidity level (gamma) belongs in the cross-section of `x`. Intermediary stress belongs in the common part. Do not treat one as a proxy for the other, because the two have a low correlation (p. 15).
