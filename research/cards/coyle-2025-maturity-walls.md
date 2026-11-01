# Coyle (2025), "Maturity Walls"

Working paper, Study Center Gerzensee, December 2025. Corporate bonds, US. **Added by citation chasing** from the review's dropped list (SSRN 6001134, "Maturity Walls", 2026). We read the author's copy (`users.ssc.wisc.edu/~pcoyle/Coyle_MaturityWalls.pdf`, 63 pages). Page numbers are PDF pages. The SSRN 2026 version was not opened and may differ.

## Claim
A maturity wall is a state in which most of a firm's debt falls due within one to two years (p. 1). 47% of non-financial bond issuers have one (p. 10). In the estimated model, walls raise credit spreads by 21% (36 bp) and default rates by 25% (30 bp) (p. 1, p. 4). A model without walls understates the default response to a credit freeze by up to 60% (p. 1, p. 5).

## Method
**Measure (p. 9).**

```latex
\sigma_{Mat,t} = \sqrt{\sum_{m=1}^{M} s_{m,t}\,(m - \mu_{Mat,t})^2}, \qquad s_{m,t} = \frac{b_{m,t}}{\sum_j b_{j,t}}, \qquad \mu_{Mat,t} = \sum_{m=1}^{M} s_{m,t}\, m
```

Intuition: the spread of debt payments around their mean date, in years. A wall is `σ_Mat ≤ 1` (p. 10).

The author prefers it to a Herfindahl index. Debt split between years 1 and 2 and debt split between years 1 and 20 have the same Herfindahl (0.5). Their `σ_Mat` values are 0.5 and 9.5 (p. 10).

**Regressions (pp. 10–15).** Standardised firm-year panel with fixed effects and firm clusters. Dependent variables: `σ_Mat` (Table 1, p. 12), and default probability and new issue spread (Table 2, p. 15).

**Model (pp. 3–4).** Firms choose debt and a dispersed or concentrated schedule. They pay a fixed issuance cost, and quadratic equity costs stand for rollover risk. Estimation by simulated method of moments (p. 4). The causal effect comes from a counterfactual economy with only concentrated schedules (p. 4).

## Data
Mergent FISD and Compustat, 1995 to 2019, without financials and utilities (p. 8). 1,432 firms, 17,972 firm-years (p. 8). Mean `σ_Mat` 2.7 years, median 1.4 (p. 10). Mean 5.4 bonds a firm, median 3 (p. 9).

## Result
- Who has walls (Table 1, p. 12, firm and year effects). `σ_Mat` per sd: size +1.247 years, leverage +0.373, age +0.653, bonds outstanding +0.668, average maturity +0.990, interest coverage −0.342.
- Default and pricing (Table 2, p. 15), per sd of `σ_Mat`: default probability −0.645 points, new issue spread −11.4 bp (se 4.7). Leverage +52.5 bp. Average maturity +2.9 bp, not significant. So the spread of dates carries information that the mean date does not.
- Walls in the raw data (p. 3): 97 bp more default probability and 34 bp more new issue spread.
- Means by wall status (Table 9, p. 56). Wall firms: 1.83 bonds (median 1), spread 273 bp, market leverage 0.39, assets $3.8bn. Others: 8.62 bonds (median 6), spread 175 bp, market leverage 0.30, assets $18.2bn.
- Freeze (p. 5, p. 46). Aggregate default rises 1.68 points. Firms that must repay a wall at the freeze default about 4 points more. A standard long-term debt model understates default by 60%, and an average-maturity model by 16%.
- Model default share: walls account for 14% of defaults (p. 4).

## Limits
- Most wall firms have one bond (Table 9, p. 56), so the measure is close to a bond count for small issuers.
- FISD holds bonds. Loans and leases are outside the measure.
- New issue spreads only, 1,213 observations (Table 2, p. 15). Secondary spreads and returns are not tested.
- The causal numbers are model counterfactuals, not estimates from an experiment.
- Internal inconsistency: walls are held by "more leveraged" firms on p. 4 and by "lowly leveraged" firms on p. 7. Table 1 fits the second reading within fixed effects. Table 9 shows higher raw leverage for wall firms.
- Working paper. Not peer reviewed.

## Section touched
`docs/methodology.md` Section 4.7 (new feature), Section 4.2 (`wall_cover_h`), Section 7.2 (forward block), Section 9.4 (wall limit).

## Use for the two clocks
This section is our proposal, not the source's claim.

**What the source says.** The second moment of the debt ladder has information beyond the mean date.

**What our data says.** No test on our panel. `hy/clocks.py` reports centres (`dur_obligations`, `dur_revenue`), a runoff and shares. It has no dispersion term.

**What we decide.** Add three features to `hy.clocks.mismatch`, built from the same annual grid.

```latex
\sigma^{debt} = \operatorname{sd}_{w}(t \mid principal_t), \qquad \sigma^{O} = \operatorname{sd}_{w}(t \mid O_t), \qquad \sigma^{R} = \operatorname{sd}_{w}(t \mid R_t)
```

Intuition: a lumpy clock forces a large decision on one date, and a smooth clock does not.

Rules:
1. Use the full debt ladder from the filing, with loans, so a one-bond issuer does not read as a wall by default.
2. Report `n_instruments` beside `σ^debt`. Treat `σ^debt` as uninformative when one instrument holds all debt. Our choice, v0.
3. Do not add the 1-year cut as a hard flag until our panel supports it.

`σ^debt` differs from `wall_cover_h` and F21. Those measure cash against an amount due. This measures how the due amounts bunch in time.

**Test.** In the interaction panel of `nagler-2020-bond-rollover-channel.md`, add ΔMS × (−σ^debt). Pass: positive and significant in at least three of four windows, after size, leverage and `rollover_rate_12m`. Our choice, v0.
