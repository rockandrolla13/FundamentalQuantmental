# Kricheff (2012), *A Pragmatist's Guide to Leveraged Finance*: macro drivers of the revenue model

FT Press, 2012, first edition. Practitioner book, not peer reviewed. Page numbers are PDF pages of the copy in the repo root, which equal the printed folios. The card `kricheff-pragmatists-guide-leveraged-finance.md` covers the relative value chapters. This card covers only chapter 12 and the passages on cycle sensitivity.

## Claim
1. Build the revenue model top down from macro drivers. GDP is a start, but an industry-specific driver is usually better (ch. 12, p. 63).
2. Measure how a driver affects revenue from the issuer's own history: check the correlation, or fit a multiple regression (p. 64).
3. Third-party macro forecasts have errors. Compare past macro projections with actuals and adjust the forecast that drives the model (p. 64).
4. Choose a driver that is published often, so the model can update. A weaker annual series beats a stronger series that comes once in ten years (p. 63).
5. Cycle sensitivity sets how much leverage the market accepts. A highly cyclical manufacturer gets 3x to 4x. A stable satellite operator gets more (p. 52).

## Method
**Driver model (pp. 63–66).** Revenue is a function of macro drivers and issuer plans. Two examples:
- Retailer: consensus national consumer spending drives sales per square foot. The issuer's store plan drives square feet. Revenue is the product (Table 12-1, p. 64).
- Tire maker: national new-car sales and inflation drive unit volume and price. Replacement tires stay about constant (p. 66).

```latex
Rev_{t} = \underbrace{f(\text{driver}_t)}_{\text{market}} \times \underbrace{\text{capacity}_t \text{ or share}_t}_{\text{issuer plan}}
```

Intuition: the macro sets the market, and the issuer's plan sets its slice.

**Calibration (p. 64).** "Go back through recent results for the last several years to see how well correlated a company's revenue is to these factors." Or "utilize multiple regression to determine how various factors in the past have caused revenue to move".

**Scenario (p. 69).** Cut EBITDA by 10% across the projection. In the tire example, FCF and EBITDA to interest are the most sensitive metrics. A second use: solve for the EBITDA decline that turns FCF negative, then judge if that decline is realistic.

**Process order (pp. 140–141).** Start each credit review from a macro context so that the analyst does not have to act as an economist. The book gives no rule for how the context changes the numbers.

## Data
Illustrations only. No sample, no regression output.

## Result
No statistical result. The book supports the structure of link 3 and gives three design rules: an industry driver over GDP, a check of the macro forecast's own error, and a frequent driver.

## What our data says
No fit on our data yet. Effect on the three macro links:

1. **Link 1, path probabilities (5.4).** Nothing direct. Rule 3 (adjust the macro forecast for its own past error) is the same idea as the `k_src` widen factor of Section 5.4. That supports the widen factor in kind. The book gives no number.
2. **Link 2, downside weights (5.2).** Nothing direct. The breakeven decline (p. 69) gives a check on the threshold `δ_i`. Proposal: store the breakeven EBITDA decline at which FCF turns negative next to `δ_i`. Flag issuers where `δ_i` exceeds the breakeven, because there the moderate downside already means cash burn.
3. **Link 3, revenue shift (5.2).**
   - Supports the regression. `fit_sector_beta` in `hy/forward.py` regresses sector revenue growth on macro growth. That is the book's method (p. 64).
   - The book prefers an industry driver to GDP (p. 63). Our shift uses one macro growth series for every sector (`G_h(m) − G_bar`). Section 3.6 already defines `sector_drivers[]` (oil price, housing starts, retail sales, hospital admissions), but Section 5.2 does not use it. Proposal: regress each sector's revenue growth on its own `sector_drivers[]` series, and keep GDP as the fallback. Each driver then needs a forecast with a vintage in the Section 5.4 registry. Test: for each sector, compare the out-of-sample R² of revenue growth on GDP with the R² on the sector driver over 2007–2026. Keep the sector driver only where it wins in at least three of the four cycle windows (2008, 2015, 2020, 2022).
   - The issuer plan stays separate from the macro shift (p. 64). This matches Section 5.2: "The scenario definitions stay issuer specific. The macro state sets how likely each one is."

## Limits
- Practitioner advice. No data, no test.
- The book does not say how to turn a macro forecast into case weights.
- The book is about single-issuer models. It says nothing on a pooled sector beta.
- An industry driver needs its own forecast with a vintage. The registry of Section 5.4 holds few industry series today.

## Section touched
`docs/methodology.md` Section 5.2 (`β_sector` regression and the choice of driver, threshold `δ_i`) and Section 5.4 (forecast error and `k_src`). `hy/forward.py` (`fit_sector_beta`, `growth_shift`).
