# Choi, Hackbarth and Zechner (2018), "Corporate debt maturity profiles"

Journal of Financial Economics, DOI 10.1016/j.jfineco.2018.07.009. Peer-reviewed journal article. We read an earlier draft: "Granularity of Corporate Debt: Theory and Tests", dated 11 January 2012, 44 pages, on a Tel Aviv University seminar page. The publisher page returned 403. We did not open the journal version, and it may differ in measure and in numbers. Page numbers below are PDF pages of the draft. PDF page = printed page + 1. Evidence class: bond issuers, debt structure as the outcome, no spreads and no defaults.

## Claim
Firms spread bond maturity dates across time, and this is a managed choice (p. 1). It is better to diversify the roll-over when market access can freeze (p. 1). Debt is more dispersed for larger and more mature firms (p. 1). It is also more dispersed for firms with better investment opportunities, more tangible assets, higher leverage and lower current cash flow (p. 1). New issues avoid maturity dates where the firm already has debt (p. 1).

## Method
**Model (pp. 6-11).** A firm funds two projects with one bond or two bonds. In each period the market freezes with probability `λ`. A bond that cannot roll forces liquidation of a project. A firm with two bonds liquidates the worse project, and a firm with one bond liquidates both.

```latex
V_M(\lambda) - 2k - [V_S(\lambda) - k] = \tfrac{1}{2}\lambda H - k \quad (5)
```

Intuition: a spread of maturities pays more when freezes are more likely and when the projects at risk are worth more, and it costs one more issue.

**Measure (p. 20).** Group each bond's maturity into the nearest integer year, compute the fraction of total bonds per year, then the Herfindahl index.

```latex
GRAN1_{i,t} = -\sum_{y} f_{i,y,t}^2, \qquad GRAN2_{i,t} = \frac{1}{\sum_{y} f_{i,y,t}^2}
```

Intuition: the measure is high when the debt falls due in many small amounts and low when it falls due at once.

**Cross-section (p. 22, equation 9).** Regress next-year granularity on Q, size, age, leverage, tangibility and profitability, with year, industry or firm effects.

**Adjustment speed (p. 24, equation 10).** Add the lagged measure. The speed is one minus the lag coefficient.

**New issue test (pp. 25-26, equation 11).** Linear probability of a new bond in maturity bucket `K_j` on the firm's deviation from a benchmark profile in each bucket. The benchmark comes from 128 groups within each industry.

## Data
- Mergent FISD and annual Compustat, 1991 to 2009, without financials and utilities (p. 20).
- 16,593 firm-years, of which 9,288 have at least two bonds (pp. 3-4).
- 16,176 bond issues (p. 21).
- Means for firms with at least two bonds (Table 3, p. 37): `GRAN1` -0.43, `GRAN2` 3.46, 8.24 bonds, assets $11,895.8 million, leverage 0.28.
- The measure covers bonds only and leaves out bank loans (p. 20, footnote 10).

## Result
**Determinants (Table 5 Panel A, p. 39).** With no effects, on `GRAN1`: Q 0.057 (t 5.33), size 0.127 (t 27.67), leverage 0.29 (t 8.55), tangibility 0.127 (t 5.26), profitability -0.15 (t -4.34), R-squared 0.456. With firm and year effects, leverage is 0.353 (t 13.02) and tangibility is 0.001 (t 0.03).

**Speed (p. 24).** The lag coefficient runs from about 0.8 to 0.5, so the speed is about 0.2 to 0.5.

**New issues (Table 7 Panel A1, p. 43).** Own-bucket coefficients run from -0.09 (t -1.87) for 1 to 2 years to -0.974 (t -9.91) for 21 years and longer. For 9 to 10 years it is -0.772 (t -8.38).

## Limits
- The draft has no bond spread, no return and no default test. It does not show that dispersion lowers credit risk.
- Bonds only. A high yield issuer with term loans is mis-measured (p. 20, footnote 10).
- Sample firms have public bonds, and they lean large.
- Leverage may cause dispersion or follow from it. The authors note this (p. 23).
- The draft is from 2012, under a different title, and the published measure may differ.
- Source inconsistency: the text gives sizes as "$1,769B vs. $11,896B" (p. 21). Table 3 gives these in millions.
- Source inconsistency: the adjustment speed is 20% to 40% on p. 4 and 0.2 to 0.5 on p. 24.
- The text reads the -0.772 coefficient as "77% lower" (p. 4). The regressor is a deviation of a fraction, not an indicator, so this holds only for a deviation of 1.

## Section touched
`docs/methodology.md` Section 4.7 (`renewal_refinance_share`), Section 4.2 (`wall_cover_h`), Section 9 (maturity events). Related and not duplicated: estimate E8, factor F21.

## Use for the two clocks
**What the source says.** The debt clock is not given. Firms shape it toward a target, at a speed of 0.2 to 0.5 per year. Larger and more levered firms spread their debt more.

**What the data says.** Section 4.7 reports a refinance coefficient of +0.36 (t 2.0). In the backtest `renewal_refinance_share` is debt due after year 2 over all obligations. So it rises with the debt weight and with long maturities. It does not measure how the debt is spread. `he-xiong-2012-rollover-risk-credit-risk.md` reaches the same reading of +0.36 from the theory side. F21 and `wall_cover_h` measure near-term maturities against liquidity, and they do not measure dispersion.

**What we decide (our proposal, not the source's claim).**
1. Add `debt_gran = -sum f_y^2` from the debt ladder in the filing, plus `debt_gran_bond` from FISD. The filing ladder holds loans, which fixes the gap in footnote 10. The filing's "thereafter" bucket is coarse, so report the share in it beside the measure.
2. Keep it apart from E8 and F21. Reject the new feature if its rank correlation with `wall_cover_4` is above 0.5 in the panel (Our choice, v0).
3. Control for size and leverage, because this paper shows that both drive dispersion. Without them `debt_gran` measures the issuer's scale.
4. The benefit depends on `λ`, the chance of a market freeze. So interact `debt_gran` with a credit supply measure, such as SLOOS (`research/cards/forecast-sloos.md`).
5. Test. In spread changes around a credit shock, the source's logic passes when issuers with higher `debt_gran` widen less, after spread level, leverage and size.
