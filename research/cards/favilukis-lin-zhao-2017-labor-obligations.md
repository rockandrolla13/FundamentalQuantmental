# Favilukis, Lin, and Zhao (2017 draft), "The Elephant in the Room: the Impact of Labor Obligations on Credit Markets"

Working paper, draft of January 26, 2017, 67 pages, from a Notre Dame seminar page (`mendoza.nd.edu/wp-content/uploads/2019/01/2017_spring_seminar_series_xiaoji_lin_paper.pdf`). **Not peer reviewed in the copy we read.** Page numbers are PDF pages, and they equal the printed pages. Evidence class: aggregate US credit spread and firm-level default frequency in many countries. No bond-level spread.

**Added at the audit close.** The screen graded an earlier version 3, and the cap dropped it.

## Claim
Wage growth and labor share forecast aggregate credit spreads and debt growth (p. 1). High labor share firms choose lower financial leverage (p. 1). A model with sticky wages and long-term debt produces large spreads with low default rates, "because pre-committed payments to labor make other committed payments (i.e. interest) riskier" (p. 1).

## Method
**Measures (p. 13).**

```latex
LS_{i,t} = \frac{XLR_{i,t}}{XLR_{i,t} + EBITDA_{i,t}}, \qquad \Delta XLR_{i,t} = \frac{XLR_{i,t} - XLR_{i,t-1}}{0.5\,(XLR_{i,t} + XLR_{i,t-1})}
```

Intuition: labor share reads how much of operating cash is already promised to staff.

**Firm test (p. 14, eq. 1).** A cross-section in each period of next-period EDF on the labor measure, then Fama-MacBeth means with Newey-West errors (pp. 14, 16).

## Data
Aggregate US, 1948 to 2014, Moody's Baa less Aaa (pp. 9-10, 12). Firms in many countries, 1992 to 2011, with Moody's KMV EDF (p. 13). `XLR` is labor expense from Compustat (p. 13).

## Result
- **Aggregate (pp. 2, 10).** Wage growth on next-year spread: t -4.15, R-squared 0.28. Labor share: t 2.55, R-squared 0.09. A 1% fall in wage growth goes with 15 bp more spread. A 1% rise in labor share goes with 11 bp more.
- **Firms (Table 3, p. 16).** EDF on labor share: 0.43 (t 5.46) alone, 0.61 (t 4.55) with all controls. EDF on labor growth: -0.92 (t -7.64), -0.45 (t -7.20).
- **Leverage (p. 18).** Labor share on financial leverage: univariate t -32.86.

## Limits
- EDF is a model output, not a price. The authors discuss this (p. 13).
- The aggregate spread is Baa less Aaa, not high yield.
- Firm tests use Fama-MacBeth with Newey-West errors on persistent firm measures. `petersen-2005-panel-standard-errors.md` warns that such t values run high.
- Draft. A later version may differ.
- We read pp. 1-5, 10, 13-14, 16, 18.

## Section touched
`docs/methodology.md` Section 4.7 (classes on the cost clock). `docs/decisions/2026-11-01-clocks-residual-timing.md`, leads table.

## Use for the two clocks
**What the source says.** Wages are a fixed claim that competes with interest. The cost clock holds no labor class.

**What our data says.** `hy/clocks.py` has debt, interest, leases, and purchases. No labor field exists on file. `XLR` coverage on our panel is not on file.

**What we decide (our proposal, not the source's claim).** Keep this as a lead, and do not add a fourth class now. Filed labor contracts have no ladder, so a class would rest on a share and not on a schedule. Report `labor_share` as a control candidate when coverage is known.

**Test.** Report the `XLR` coverage of the bond panel. Below 50% of issuers (Our choice, v0), the lead stays closed.

## Update, 2026-11-02: AER 2020 version
AER 110(6), 1673-1712. An agent read it. Table 2D: `LS` on EDF 0.71 (se 0.08), labor growth -0.45 (se 0.06). Table 4: 5-year CDS on `LS` 1.78 (se 0.38), on labor growth -0.37 (se 0.17). Table 3 shows labor growth -0.08 (se 0.06) and its interaction with rigidity -0.21 (se 0.04), so the effect sits in rigid firms, and the draft's Table 4 and A1 conflict is settled in print. It has no firm bond spread test, no US firm regression, no industry effects, and no lagged default control at firm level. US `XLR` coverage is 7% (n. 15). The user lifted the coverage gate on 2026-11-02. **We decide:** labor stays out of `O_t`, because the margin is after labor. Use `stress_margin` and `labor_share`, with non-positive denominators reading 1. Chen et al. (2010) give an opposite sign for union voice.

**Status, 2026-11-02:** the user closed labor for the clocks. This card is a record only, and its decisions no longer apply.
