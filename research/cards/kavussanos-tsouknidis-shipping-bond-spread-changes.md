# Kavussanos and Tsouknidis (undated SSRN copy), "The determinants of credit spead changes in global shipping bonds"

SSRN working paper, abstract id 2640579. The PDF names no journal and states no year in its text. The PDF metadata gives a creation date of 22 April 2015. The acknowledgements cite four anonymous referees and an earlier title, "Determinants of Bond Spreads in the US Transportation Sector" (p. 32). We read all 45 PDF pages. Page numbers below are printed page numbers. Printed page = PDF page − 1. Evidence class: panel regression of weekly spread changes in one A5 industry (cargo shipping), 54 bonds of 20 issuers, in sample only.

## Claim
Weekly changes in shipping bond spreads move with five factors: bond liquidity, stock market volatility, a cyclical bond index, lagged freight earnings, and the bond's credit rating (p. 1). The choice of significant variables depends on two-way cluster standard errors (p. 1). Without them, five to eight extra variables test as significant (pp. 28-29).

## Method
**Generic panel model (p. 7, eq. 1).**

```latex
y_{it} = \mu + a_i + \alpha_t + \sum_{g=1}^{G} \beta_{gi}\, x_{git} + \sum_{k=1}^{K} \gamma_{ik}\, z_{kt} + u_i + \varepsilon_{it}
```

Intuition: the spread of bond i at week t has a bond level, a week level, bond variables `x` and variables `z` that are common to all bonds.

`y` is the bond yield minus the yield of the US Treasury with the closest maturity (p. 7, Table 1 p. 35). `x` holds the bond variables: term to maturity, market value of the issue, rating, seniority (pp. 10-11). `z` holds the issuer, industry, macro, rate and Fama-French variables (pp. 11-14). The authors use a common `γ_k` for all bonds (p. 7, note 7).

**Estimated form (p. 9, Table 6 notes p. 41).** Most series are I(1), so the authors estimate eq. (1) in first differences (p. 9). Δ is the log first difference (p. 41). Altman z, seniority, VIX, paperbill and the Fama-French factors stay in levels, because they test as I(0) (p. 18).

```latex
\Delta \log s_{it} = \mu + \alpha_t + \sum_g \beta_g\, \Delta \log x_{git} + \sum_k \gamma_k\, \Delta \log z_{k,t-l} + \varepsilon_{it}
```

Intuition: the test asks which weekly news moves the spread, not which bonds sit wide.

**Model choice (pp. 8-9, 19-20).** A Hausman test picks fixed or random effects. An F test then compares fixed effects with pooled OLS, and a Breusch-Pagan LM test compares random effects with pooled OLS. Fixed effects models use maximum likelihood (p. 9). M1 to M5 each hold one group of variables (p. 18). M6 holds the significant variables from all groups. The authors pick M6 by the lowest Schwarz BIC and the highest adjusted R² (p. 19). Two variables with a correlation above 60% never enter one model together (p. 19). Freight lags 1 to 5 weeks are candidates (p. 23).

**Standard errors (pp. 9-10, 20).** Fixed effects models use two-way clusters by bond and week. Random effects models use clusters by bond only (p. 10). The clusters are bond issues and weekly dates (p. 20). The paper prints no variance formula. The formula of the cited method is in card `petersen-2005-panel-standard-errors` (p. 26 of that copy).

```latex
V_{bond \& week} = V_{bond} + V_{week} - V_{White}
```

Intuition: add the correlation inside a bond to the correlation inside a week, and subtract the diagonal that both terms count.

**Standardised coefficient (p. 24, note 31).**

```latex
\beta_i^{*} = \beta_i \, \frac{s_{x_i}}{s_y}
```

Intuition: the number of standard deviations the spread change moves for one standard deviation of the driver.

**Net freight effect (p. 23).** The sum of the lag coefficients on Δlog ClarkSea.

## Data
- All fixed coupon bonds of listed cargo shipping companies, issued or traded January 2003 to June 2010 (p. 14). Convertibles and floaters are out (p. 14). An issuer must earn above 60% of income from shipping transport (p. 14).
- 31 drilling and cruise bonds are out (p. 14, note 19). The start sample of 125 bonds falls to 54 bonds of 20 issuers (p. 15).
- 42 of the 54 bonds have a US-resident issuer, and 42 list on the NYSE (p. 15, Table 3 p. 37).
- Vessel profile: 30 diversified, 15 tanker, 5 container, 4 bulk (Table 3 Panel C, p. 37).
- 45 bonds (83.33%) are speculative grade with a mean coupon of 8.28% (p. 15).
- 390 weekly dates, about 250 weeks per bond, 14,081 bond-weeks (p. 17).
- Sources: Datastream for spreads and most series. Bloomberg for ratings, Altman z and the two Merrill Lynch indices. Clarksons for freight earnings (p. 16). Spreads are winsorised at the 1st and 99th percentiles (p. 16, note 22).
- Freight variables: the ClarkSea index, and a "freight rate combined index". The combined index gives each issuer the ClarkSea sub-index of its fleet when one segment holds over 60% of its vessels (pp. 16-17).
- Ratings map to numbers from AAA = 1 to D = 22, averaged over the agencies (Table 2, p. 36).

## Result
All coefficients below are two-way cluster estimates. The t value is in brackets.

**Whole period, M6 (Table 6, p. 41).** Adjusted R² 25.24%, 7,295 bond-weeks, 54 bond clusters, 370 week clusters. Bond and time fixed effects.
- Δ market value of the bond: −2.0253 (−12.41). Standardised −0.4453.
- Δ rating: 0.0849 (2.09). Standardised 0.0103.
- Δ ClarkSea lag 2: −0.0947 (−2.37). Lag 3: +0.0959 (2.19). Lag 4: −0.1230 (−3.20).
- The sum of the freight lags is −0.1218 (p. 23). The standardised net effect is −0.0853 (p. 24).
- Δ GISC cyclical bond index: 1.1133 (4.80). Standardised 0.1305.
- VIX level: 0.0203 (4.57). Standardised 0.1276.
- Market value has the largest standardised effect. GISC and VIX follow, then freight, then rating (p. 24).

**Groups alone, whole period (Table 6, p. 41).**
- M1, bond and issuer group: adjusted R² 18.20%. Δ maturity −0.2202 (−7.04), Δ market value −1.9604 (−9.87), Δ rating 0.1151 (1.89), Δ market equity over total assets −0.0045 (−2.52), Altman z 0.0022 (1.28), seniority −0.0011 (−1.74).
- M2, industry and macro group with ClarkSea: adjusted R² 7.37%. ClarkSea lag 4 −0.0794 (−2.69), GISC 0.8458 (3.472), MSCI World −0.5557 (−5.28), VIX 0.0106 (2.38).
- M3, the same group with the fleet-matched index: adjusted R² 7.29%. Combined index lag 4 −0.0458 (−2.49).
- M4, rates group: adjusted R² 14.43%. Δ 10-year −0.3533 (−4.39), Δ 2-year −0.1301 (−3.74), Δ slope 0.0221 (2.95), paperbill 0.0058 (1.96).
- M5, Fama-French group: adjusted R² 2.82%.

**Before the crisis, January 2003 to July 2007, M6 (Table 7, p. 42).** Adjusted R² 22.27%, 7,252 bond-weeks, 47 bonds.
- Δ market value −2.1569 (−5.82), standardised −0.4112.
- ClarkSea lag 4 −0.0994 (−2.26), standardised −0.0681. Lags 2 and 3 are not in the model.
- GISC 1.2927 (5.17), standardised 0.1635.
- VIX 0.0574 (3.11), standardised 0.1741.
- Δ rating is not significant in M6 (p. 25). In M1 it is 0.1007 (1.66).

**After the onset of the crisis, August 2007 to June 2010, M6 (Table 8, p. 43).** Adjusted R² 16.91%, 6,515 bond-weeks, 51 bonds.
- Δ market value −0.8638 (−1.84), significant at 10% only. Standardised −0.3466.
- ClarkSea lag 2 −0.0938 (−2.10), lag 3 +0.1168 (2.46), lag 4 −0.0991 (−2.39).
- VIX 0.0215 (2.98), standardised 0.1078.
- GISC and rating leave the model (p. 27).
- In M1, Δ rating is 0.0521 (0.27), and Altman z is 0.0191 (1.95) (Table 8, p. 43). The adjusted R² of M1 is 24.50%, on 16 bonds only (p. 26, note 32).

**With and without two-way clusters (Table 9, p. 44).** The coefficients are the same. The t values fall by a factor of about 2 to 4 (our arithmetic from Table 9).

| Variable | Whole, none | Whole, two-way | Before, none | Before, two-way | Crisis, none | Crisis, two-way |
|---|---|---|---|---|---|---|
| Δ market value | −27.42 | −12.41 | −15.72 | −5.82 | −4.15 | −1.84 |
| Δ GISC | 12.02 | 4.80 | 16.19 | 5.17 | not in model | not in model |
| Δ rating | 1.92 | 2.09 | not in model | not in model | not in model | not in model |
| VIX | 9.26 | 4.57 | 12.04 | 3.11 | 7.65 | 2.98 |
| ClarkSea lag 2 | −5.66 | −2.37 | not in model | not in model | −6.89 | −2.10 |
| ClarkSea lag 3 | 4.87 | 2.19 | not in model | not in model | 7.22 | 2.46 |
| ClarkSea lag 4 | −7.65 | −3.20 | −6.70 | −2.26 | −7.33 | −2.39 |

- Without clusters, five more variables test as significant in the whole period: Altman z, ClarkSea lag 5, Δ HW00, Δ slope and the paperbill (p. 28). The before period gains six, and the crisis period gains eight (p. 29). The paper does not report those coefficients (p. 29, note 33).
- Country of residence fixed effects leave M6 "virtually the same" (p. 21). The paper reports no numbers for this check.

## Limits
- **Mechanical liquidity proxy (our view).** Market value is price times amount on issue (p. 10). A spread rise lowers the price in the same week. So part of the −2.0253 is the dependent variable on both sides. The largest "driver" is not a clean liquidity measure.
- **Few issuer clusters (our view).** The clusters are 54 bonds, not 20 issuers (p. 15, p. 20). Bonds of one issuer share issuer news. Card `petersen-2005-panel-standard-errors` (p. 27) says two-way clusters need enough clusters in both dimensions.
- **Selection on the test data.** M6 keeps only the significant variables, picked by BIC and adjusted R² on the same sample (p. 19). The t values in M6 then overstate the evidence. The paper has no hold-out test.
- **Identification of common regressors.** VIX, GISC and ClarkSea are the same for all bonds in one week. M6 also holds time fixed effects (Table 6, p. 41). The paper does not say how weekly time dummies and weekly common regressors are both identified. The frequency of the time dummies is not reported.
- **Fixed effects after differences.** The authors say that first differences remove `a_i` (p. 9). The differenced models still carry bond fixed effects (Tables 6 to 8). These then act as bond trends. The paper does not discuss this.
- **No book leverage or coverage.** The only issuer variables are market equity over total assets and Altman z (p. 11). Neither enters any M6.
- **Change model, not level model.** The test explains weekly changes. It does not test which bonds are wide in the cross-section.
- Number mismatch: the text gives a mean spread of 676.19 bp for 2003 to 2010 (p. 4). Table 5 gives 557.07 bp (p. 40).
- Number mismatch: the text says the market value effect is "approximately 6.5 times" the rating effect (p. 24). The standardised values give 0.4453 over 0.0103, about 43 (our arithmetic).
- Number mismatch: the text gives a crisis net standardised freight effect of −0.0822 (p. 27). The Table 8 values sum to −0.0722 (our arithmetic: −0.0891 + 0.1108 − 0.0939).
- Number mismatch: the text counts 14 tanker bonds (p. 15). Table 3 Panel C counts 15, and only 15 makes the total 54 (p. 37).
- Number mismatch: the seniority code runs from 1 to 6 (p. 11, Table 1 p. 35). The sample holds seven seniority types (p. 15, Table 3 p. 38), and Table 5 shows a maximum of 7 (p. 40).
- Number mismatch: the text says the lowest yearly standard deviation of spreads is 393.92 bp in 2003 (p. 17). Table 4 gives 605.26 bp for 2003 and 251.88 bp for 2004 as the lowest (p. 39). 393.92 is the 2004 mean spread.
- Number mismatch: the whole-period M6 has 7,295 bond-weeks (Table 6, p. 41). The two sub-period M6 models hold 7,252 and 6,515, a sum of 13,767 (Tables 7 and 8). The paper does not explain the loss.
- Date mismatch: the whole period ends in July 2010 on p. 18 and in June 2010 elsewhere (pp. 14, 17, Table 6).
- Text against table: the paper says that all M6 coefficients have the expected sign (p. 23). ClarkSea lag 3 is positive in the whole and crisis periods (Tables 6 and 8). Only the sum of the lags is negative.
- Text against text: the abstract names credit rating as a main determinant (p. 1), and the conclusions repeat it (p. 32). The discussion says rating is "not revealed as truly significant" (p. 31).
- Text against table: the paper says clusters lower the t values (p. 28). For Δ rating the t value rises from 1.92 to 2.09 (Table 9, p. 44).
- Procedure against table: the crisis M1 carries bond fixed effects (Table 8, p. 43). Its F test of bond effects against pooled OLS has p = 0.2024, which fails the stated rule (p. 9).
- Sign of the text: the paper says a higher Altman z leads to "a higher bond spread expectation" (p. 11). The expected sign in the same paragraph and in Table 1 is negative (p. 35).
- Print errors: Table 8 shows the M6 constant as −0.0605 with t (2.65) (p. 43). Table 7 shows the M1 constant as 0.0003 with t (−0.09) (p. 42).

## Section touched
`docs/methodology.md` Section 7.2 (the liquidity block and the sector-by-date effect η), Section 8 S7 (macro-conditional sector tilt), Section 11 (validation, standard errors). `docs/factors/SECTOR-models.md` Section 1 (evidence gap) and Section 3.1 (industrials row). `hy/sector/drivers.py` `SECTOR_DRIVERS`. `docs/framework.md` F2, archetype A5 downside driver. `docs/decisions/2026-11-01-clocks-residual-timing.md` (clusters by issuer and month). `hy/walkforward.py` `cluster_slope`.

## Use for the A5 archetype
**What the source says.** In cargo shipping, weekly spread changes follow lagged freight earnings with a net negative sign, a cyclical sector bond index, VIX, and bond liquidity. Two issuer fundamentals, market leverage and Altman z, do not survive the final model. Two-way clusters cut the t values by a factor of about 2 to 4 and remove five to eight variables.

**What the data says.** Shipping issuers fall into the industrials group (GICS 20). That group uses `log_lev` +, `ebitda_cyc` +, `margin_trend` − and `coverage` − (`hy/sector/drivers.py`). This paper tests none of those four drivers. The repo holds no freight earnings series and no schema for one (`data/schemas/`). The fair spread of Section 7.2 is a level cross-section with sector-by-date effects. The liquidity block already gives size a negative sign. `hy/walkforward.py` `cluster_slope` clusters by date only. The decision page `2026-11-01-clocks-residual-timing` already asks for clusters by issuer and month and a permutation null.

**What we decide (our proposal, not the source's claim).**
1. Keep the industrials driver list for shipping. Keep the evidence gap of `SECTOR-models.md` open. This paper tests changes, not levels, and none of the four drivers.
2. Put the freight channel in the sector effect, not in the bond driver list. A series common to the sector has no spread inside one sector on one date, so η absorbs it. The fleet-matched index adds nothing over the general index (adjusted R² 7.29% against 7.37%, Table 6 p. 41). So do not add an issuer freight exposure driver yet.
3. Add `sector_earn_chg` to the S7 tilt for A5 groups with a traded earnings index (ClarkSea for shipping). The sign in spread is −. The lag is one month, because the paper finds lags of 2 to 4 weeks (p. 23).
4. Keep size with a negative sign in the liquidity block. Do not use the change in bond market value as a driver, because it holds the bond price.
5. Use two-way clusters by issuer and month for every sector driver test. Report the t value with no clusters beside it. Below 40 issuers, read the pass from a permutation null across issuers, as the decision page `2026-11-01-clocks-residual-timing` does.
6. Test.

```latex
\Delta \log s_{i,m} = a + \phi_0\, \Delta \log E_{g(i),m} + \phi_1\, \Delta \log E_{g(i),m-1} + b\, \Delta \log S^{HY}_m + c\, \Delta \mathrm{VIX}_m + e_{i,m}
```

Intuition: if a sector's earnings index falls, the bonds of that sector widen more than the HY index in the next month.

Run it on the TRACE shipping and airline bonds, with `E` the sector earnings index and `S^HY` the HY index spread. Use no month effects, because they absorb `E`. The claim passes when φ0 + φ1 < 0 with a t value below −2 under clusters by issuer and month. It must also sit below the 5th percentile of the issuer permutation null. The claim fails when the sum is at or above 0, or when either check fails. A pass adds `sector_earn_chg` to S7 for that group. A fail removes it.
