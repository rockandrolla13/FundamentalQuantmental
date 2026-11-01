# Bretscher, Schmid, Sen, and Sharma (2022 draft), "Institutional Corporate Bond Pricing"

Published in The Review of Financial Studies 39(3), pp. 605-660, DOI 10.1093/rfs/hhaf067. Peer-reviewed. OpenAlex marks the journal copy as closed. **We did not open the journal article.** We read the conference draft of January 2022, 74 pages, at `conference.nber.org/conf_papers/f163197/f163197.pdf`. Page numbers are PDF pages. PDF page = printed page + 1. The journal numbers may differ. Evidence class: US corporate bonds, investment grade and high yield.

**Added at the audit close.** The screen graded this paper 3, and the cap dropped it.

## Claim
A demand system links institutional holdings to bond characteristics (p. 1). Life insurers have inelastic demand, and mutual funds have elastic demand (pp. 1, 4). The composition of institutional demand is a state variable for bond prices (pp. 1, 3). A fire sale by mutual funds widens short high yield bonds most (p. 5).

## Method
**Demand (p. 13, eq. 2).** Log portfolio weight on yield and characteristics, after Koijen and Yogo (2019).

```latex
\ln \delta_{i,t}(n) = \alpha_i + \beta_{0,i}\, y_t(n) + \beta_{1,i}' x_t(n) + u_{i,t}(n)
```

Intuition: each institution holds a bond by its yield and traits, and what the traits do not explain is latent demand `u`. The authors instrument yield with the holdings of other investors, because mandates persist (p. 4). Market clearing then gives counterfactual prices (pp. 2-3).

## Data
Thomson Reuters eMAXX holdings, WRDS Bond Returns, and FISD, 2006 to 2020 (pp. 3, 9-10). Institutions hold about 45% to 50% of the amount outstanding (p. 10). The authors note a slightly lower number of high yield bonds than the market (p. 12).

## Result
- Market-wide demand elasticity near 3.7 (pp. 4, 24).
- Mean elasticity for mutual funds 11.6 (p. 23).
- Price impact rose in the financial crisis and stayed high after it (pp. 4-5).
- Mutual funds prefer high yield, short bonds, and large issues. Life insurers prefer investment grade, long bonds, and small issues (p. 4).

## Limits
- The paper gives counterfactuals, not a forecast test of a residual.
- eMAXX is a licensed feed that the data contract does not hold.
- Draft of 2022. The journal version may differ.
- We read pp. 1-7, 9-13, 21-25.

## Section touched
`docs/methodology.md` Section 7.3 (what the residual holds). `docs/decisions/2026-11-01-clocks-residual-timing.md`, leads table.

## Use for the two clocks
**What the source says.** Who holds a bond can move its price. So a residual after fundamentals can hold demand.

**What our data says.** No holdings data exists on file. Method 3 has no demand layer.

**What we decide (our proposal, not the source's claim).** Keep this as a lead. It brings a fourth row of explanation for the residual: holder demand. Gabaix, Koijen, Richmond, and Yogo (2025) may test the same idea through embeddings, by their abstract. That paper stays unopened, so it supports no claim.

**Test.** When a holdings feed exists, add the latent demand mean of a bond's holders to the layer ladder of Method 3. Pass: fold-scored partial R-squared of at least 1 percentage point, above the permutation null (Our choice, v0).
