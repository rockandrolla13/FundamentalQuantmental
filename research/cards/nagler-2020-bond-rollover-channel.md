# Nagler (2020), "Yield Spreads and the Corporate Bond Rollover Channel"

Review of Finance 24(2), pp. 345–379, DOI 10.1093/rof/rfz005. Peer-reviewed. Corporate bonds. **We did not open the journal article.** We read the job market version under an earlier title, "Rolling over Corporate Bonds: How Market Liquidity affects Credit Risk", version of 16 November 2015, 70 pages, from the Bocconi finance page. The journal numbers may differ. Every number below comes from the 2015 version. Page numbers are PDF pages. PDF page = printed page + 1.

## Claim
Bond liquidity moves yield spreads through exposure to bond rollover (p. 1). The effect grows with the size of the exposure, appears across the term structure, and is stronger for riskier firms (p. 1). The rollover rate alone has no relation with spread changes once firm and year effects enter. Only its interaction with the bond's own liquidity change does (p. 35). Without firm effects, the stand-alone term is significant: 0.0139 and 0.0043, then 0.0022 with firm effects (Table 8, p. 60).

## Method
**Rollover rate (p. 17).** Maturing bond amount over total bond amount of the firm in a period.

**Model link (p. 11).**

```latex
rE = (r-\delta)XE_X + \tfrac{1}{2}\sigma^2 X^2 E_{XX} + \delta X - (1-\tau)C - h\phi P + \phi(D-P)
```

Intuition: φ(D − P) is the loss that equity absorbs when bonds roll below par, so the rollover rate φ sets the size of the liquidity effect on default.

**Matched difference-in-differences (pp. 26–30).** The Lehman filing gives the liquidity shock. A firm is treated when at least 10%, 15% or 20% of bond financing matures in 2009 (p. 27). Controls do not roll over in 2009 (p. 26). Match at the end of 2007 on liquidity, rating, bond and firm fields, one to four, with replacement (p. 26 and footnote). The source argues that bond maturity dates come from decisions in the distant past, which limits endogeneity (p. 20).

```latex
\Delta y_{ij} = \alpha + \beta\, Treat_{ij} + \epsilon_{ij} \quad (8,\ \text{p. 29})
```

Intuition: compare matched bonds of firms that must roll debt after the shock with bonds of firms that need not. Δy is the change in the average spread from August 2008 to December 2008.

**Panel (p. 33).** Quarterly spread changes on bonds, with standard errors clustered by firm.

```latex
\Delta y_{ij,t} = \alpha + \beta_1 \Delta Liq_{ij,t} + \beta_2 \Delta Liq_{ij,t}\times Rollover_{j,t} + \beta_3 \Delta CR_{j,t} + \beta_4 Rollover_{j,t} + \beta_5 X_{ij,t} + FE + \epsilon \quad (9)
```

Intuition: β₁ is the direct liquidity effect, and β₂ is the part that passes through refinancing. Rollover is the 1-year-ahead rate. Liquidity is price dispersion, Amihud and Roll.

## Data
429 S&P 500 constituents at the start of 2005, without financials and utilities. 13,402 bonds, about 22 million trades, 2005 to 2011 (pp. 14–15). TRACE, Mergent FISD, Compustat, swap curve as risk-free rate (pp. 14–15). Treated and control bonds average near BBB (p. 28). Bonds are 69% to 74% of book debt (p. 18).

## Result
- Firms do roll over. Issuance on redemption per firm-year gives R² of 66% to 78% and slopes of 0.90 to 1.05 (p. 21). Conditional on a maturity, the mean rollover rate is 15%, sd 24% (p. 22).
- Transaction costs tripled to 150 bp after Lehman (p. 23).
- Pooled treatment effect (Table 6, p. 58): 99 bp (se 47) at 10%, 197 bp (se 78) at 15%, 278 bp (se 133) at 20%. Treated firms: 65, 39, 23.
- By tenor at 15% (p. 30): short 191 bp, medium 217 bp, long 256 bp. The largest effect is 474 bp, for long bonds at 20% (p. 31).
- Investment grade only: 72, 141, 191 bp (pp. 31–32).
- Rating: treated firms lose 0.33 notches at 10% and 1.18 notches at 20% (p. 31, n. 8).
- Bonds with slow liquidity reversion: 131 bp and 362 bp, against 99 bp and 278 bp (p. 32, n. 9). Median half-life of liquidity is about 21 days (same note).
- Panel R²: 36% with liquidity alone, 38% with one interaction, 39% with all, 41% with maturity terms, 46% with credit risk terms (pp. 36–37).
- Size (p. 37): a 100 bp cost rise and a 10%, 15% or 20% rollover rate add 119, 178 or 237 bp. At 10%, add about 1 bp per year of maturity and about 10 bp per rating notch.
- Stand-alone rollover is insignificant with firm and year effects (p. 35).

## Limits
- S&P 500 issuers near BBB. No separate high yield sample.
- One shock. Treated cells are small: 23 firms at 20% (p. 58).
- Parallel trends are stated, not shown (p. 27, n. 6).
- Bonds only. Loans due in 2009 do not count toward treatment.
- Spread levels in bp, so long bonds with higher spreads can show larger bp effects.
- Inconsistent figures in this version: 13% against 15% for the conditional rollover rate (p. 5, p. 22), and "ATE of 195 bp" (pp. 5, 39) with no such row in Table 6.

## Section touched
`docs/methodology.md` Section 4.7 (test of the split), Section 7.2 (liquidity block), Section 9.1 (maturity and refinance window), Section 9.4 (wall limit).

## Use for the two clocks
This section is our proposal, not the source's claim.

**What the source says.** In firm-effect regressions of spread changes, the rollover rate alone explains nothing. The change in a bond's own liquidity times the exposure does. This is not a test of spread levels. All numbers are pre-publication.

**What our data says.** The split test is a monthly level regression of log spread on the two shares, with no market state, no firm effect and no control (`scripts/backtest_clocks.py`, `renewal_split_test`). It gave +0.36 (t 2.0) and −2.07 (t −2.4) (Section 4.7). Neither share ranks hedged returns beyond spread.

**What we decide.** Replace the level test with an interaction panel. Keep the two shares as reported risk measures until this runs.

```latex
\Delta \log s_{b,t} = a_b + g_t + \beta_1\,\Delta MS_t \times Due^{debt}_{i,t,12} + \beta_2\,\Delta MS_t \times Due^{fixed}_{i,t,12} + \beta_3\,\Delta MS_t \times Exp^{RPO}_{i,t,12} + \gamma' X_{b,t} + e_{b,t}
```

Intuition: each clock matters only when the market state makes its due amount expensive to replace.

Inputs: `Due^debt` is principal due in 12 months over total debt. `Due^fixed` is rent and purchase commitments due in 12 months over EBITDAR. `Exp^RPO` is RPO that ends in 12 months over LTM revenue. It needs the XBRL instance timing, because company facts drop it. MS is a liquidity state, as in the source. The factor in `boyarchenko-elias-2024-global-credit-cycle.md` is our extension, and it enters as an arm only. Each field obeys `available_at` before the month starts. The log form follows `ben-dor-et-al-2007-dts.md`.

**Stale-ladder event study.** Set treatment from a filing at least 12 months before each shock, in the windows of `hy.backtest.CYCLE_WINDOWS`. Our choice, v0. Compare with matched bonds that have no amount due in the 12 months after the shock.

**Later change.** Method 4 of `docs/decisions/2026-11-01-clocks-residual-timing.md` replaces this panel. It removes `Exp^RPO`, it reads rent through a demand state, and it uses clusters by issuer and month.

**Test.** β₁ > 0 with t above 2 pooled, and positive in at least three of the four windows. β₂ and β₃ are new and have no prior sign from this source. A clock feature enters the fair spread only as an interaction, and only if its coefficient passes that bar. Our choice, v0.
