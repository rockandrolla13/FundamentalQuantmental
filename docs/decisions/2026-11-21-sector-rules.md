# Sector rules per GICS industry group (framework F2.5 to F2.8)

Date: 2026-11-21. Status: rules written, no test run. Sections touched: `docs/framework.md` F2, `docs/factors/SECTOR-models.md` section 3.1, methodology Section 8 (S7).

## Context
Framework F2 holds eight archetypes. An archetype sets the frame, but it does not name the drivers of one industry. `SECTOR-models.md` section 1 records the gap: "No source in the repo tests a sector-specific driver list against spreads or returns." The user asked on 2026-11-21 for drivers and steps for every S&P sector.

## Options
1. Keep eight archetypes only. The analyst picks drivers per memo. Two analysts then pick different drivers for the same industry.
2. Add rows to the archetype table for each industry. The table then grows past what a reader can scan.
3. Keep the archetype table. Add one page per GICS industry group in `docs/sectors/`, and one map table in F2.

## Choice
Option 3. GICS is the S&P and MSCI classification, and `hy.sector` already groups bonds by GICS sector. Each page names its sources and says which ones the authors could open. S&P Global Ratings "Sector-Specific Corporate Methodology" (July 2025) gives the industry list and the agency ratios. It replaced the separate "Key Credit Factors" articles. The older articles still hold the industry risk scores and the recession history by sector, but their status after July 2025 is not verified. Academic cards give the tested drivers.

What the source says: see each sector page and the three cards below. What the data says: nothing yet. No driver list has run against spreads in the repo. What we decide: freeze the driver lists and the three changes below, then test them.

## Three changes from new cards
1. **A2 hospitals (F2.6).** Read three years of total margin. Source: `research/cards/malone-pink-holmes-2024-rural-hospital-distress.md`.
2. **A5 airlines (F2.7).** Size a filer on a fleet about one third smaller. Treat a peer filing as a collateral event only. Source: `research/cards/ciliberto-schenone-2012-airline-bankruptcy-competition.md`.
3. **A5 shipping (F2.8).** Send freight earnings to S7 as a sector factor. Source: `research/cards/kavussanos-tsouknidis-shipping-bond-spread-changes.md`.

## Tests that settle it
1. **Sector driver lists.** For each GICS group with at least 15 issuers, fit `hy.sector.fairspread` with the sector page's drivers, and fit the pooled model. The sector list holds if its residual z has a higher six-month rank IC than the pooled residual, after costs, in at least three of the four cycles 2008, 2015, 2020 and 2022. It fails otherwise, and the pooled model stays.
2. **F2.6.** In health care (GICS 3510), add `margin_3y`, the mean total margin over three years, to the driver list. The rule holds if its coefficient on log spread is negative under the sign constraint and the out-of-sample IC rises. If `margin_trend` then takes the wrong sign, it leaves the list.
3. **F2.7.** Regress the spread change of each rival airline bond on its seat overlap with a filer, over the 30 trading days after the filing. The rule holds if the coefficient on overlap is zero for unsecured bonds. Secured bonds on shared aircraft types should show a positive coefficient.
4. **F2.8.** Add the one-month lagged freight index change to S7 for marine shipping. The rule holds if the S7 sector IC rises with two-way clusters by issuer and month, and a permutation of the freight series gives no such rise.

## Open decisions from the sector pages
1. Branded staples fit no archetype (F2.10). A ninth archetype may fit better than A4 with a low-cyclicality template.
2. Capex sign. `hy.sector.drivers` gives `capex_int` a "+" sign. S&P reads low reinvestment in paper as weak. The materials page tests capex over depreciation with a "−" sign.
3. Retail leases. One loan study finds no lease pricing. Two bond studies find it. The retail page follows the bond evidence.
4. The S&P industry risk scores come from the 2013 table. The 2025 text confirms only the score for unregulated power.
5. Most new drivers have no field in `data/schemas/`, for example reserves, hedges, pass-through contracts and churn.

## Open inputs
Many S&P articles need a login. A sector page marks such a source "not opened" and keeps its drivers as "Our choice" or "agency weight" until someone reads it.
