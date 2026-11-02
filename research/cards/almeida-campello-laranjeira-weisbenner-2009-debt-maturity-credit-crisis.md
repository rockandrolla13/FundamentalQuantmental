# Almeida, Campello, Laranjeira and Weisbenner (2009), "Corporate Debt Maturity and the Real Effects of the 2007 Credit Crisis"

Added by citation chasing. Choi, Hackbarth and Zechner cite it (draft PDF p. 29) as forthcoming in Critical Finance Review. We read NBER Working Paper 14990, May 2009, 36 pages. We did not open the journal version, so its numbers may differ. Page numbers below are PDF pages. PDF page = printed page + 2. Evidence class: firm level, investment as the outcome. No spreads and no defaults.

## Claim
Some firms had much of their long-term debt due just after the third quarter of 2007. They cut investment by 2.5% of capital per quarter more than similar firms with later maturities (p. 2). That is about one third of pre-crisis investment (p. 2). In normal times, the maturity mix of long-term debt has no effect on investment (p. 2).

## Method
**Identification (p. 4).** Long-term debt due right after August 2007 reflects choices made years earlier. So it is plausibly exogenous to outcomes after the crisis.

**Treatment (p. 16).** The share of long-term debt due within one year.

```latex
\text{Treat}_{i} = \mathbb{1}\left\{ \frac{dd1_{i}}{dd1_{i} + dltt_{i}} > 0.20 \right\}, \qquad \frac{dltt_i + dd1_i}{assets_i} > 0.05
```

Intuition: an old contract happens to fall due in a bad month, and the firm cannot change that date on short notice.

**Estimator (pp. 5, 15).** The authors use the matching estimator of Abadie and Imbens (2002), on size, industry, rating class, Q, long-term leverage, cash flow and cash. The outcome is the change in investment from the first three quarters of 2007 to the same quarters of 2008.

**Falsification (pp. 5-6).**
- The same test in each year 2000 to 2006.
- Firms with little long-term debt.
- Treatment set from the 2005 maturity profile, which rules out firms that foresaw the crisis.

## Data
- Compustat firms with fiscal year ends from September to January, 1,067 firms in the 2007 sample (p. 15).
- Long-term debt ladders `dd1` to `dd5` come only from the annual file (p. 15).
- Outcome: capital expenditure over lagged property, plant and equipment (p. 15).

## Result
**Baseline (p. 6).** Treated firms: quarterly investment falls from 7.8% to 5.7% of capital. Control firms: it moves from 7.3% up by 0.1%. The difference in differences is 2.2% before matching and 2.5% after (p. 6).

**Heavy long-term debt users (p. 6).** The drop is 3.4%.

**Placebo (p. 6).** Maturity has no relation with changes in investment from 2000 to 2006.

**Firm choice (pp. 4, 10).** The authors find no change in the debt profile in the years before the crisis (p. 4, footnote 2). Many firms have no significant debt due in 2008 (p. 10).

## Limits
- One crisis. The outcome is investment, so the test does not price risk in bonds.
- The sample window ends at the third quarter of 2008.
- Choi et al. show that firms manage maturity profiles in general. Here the authors find persistence, and the difference matters for how exogenous a ladder is.
- A fixed 20% line. The paper varies it in robustness (p. 16).

## Section touched
`docs/methodology.md` Section 4.2 (`wall_cover_h`), Section 4.7 (test of the split), Section 9 (maturity events, wall limit), Section 11 (test design).

## Use for the two clocks
**What the source says.** The outcome here is investment, not price. Firms with long-term debt due right after the third quarter of 2007 cut investment more (p. 6). The relation is absent in the placebo years 2000 to 2006 (p. 6). An old ladder provides a natural experiment. This source says nothing on when clock risk enters bond prices.

**What the data says.** Section 4.7 tests the shares month by month over 99 months with no state split. Section 11 uses four cycle windows, but RPO data covers only 2020 and 2022.

**What we decide (our proposal, not the source's claim).**
1. Change the test design for all clock features. Measure the ladder at least two years before the stress window. Match within sector and rating class. Read spread change and hedged return in the window.

```latex
\Delta s_{i,w} = a + b\,\text{Treat}_{i,w-2y} + \gamma X_{i,w-2y} + e_{i,w}
```

Intuition: a ladder set two years before the shock cannot respond to the shock.

2. Apply the same design to the revenue clock. Contracts and leases expire on old dates too. An issuer whose RPO runs off or whose lease tail starts inside the stress window is the treated firm.
3. Report the placebo: the same regression in months with no stress. Pass needs `b` above 0 in the stress windows and `b` near 0, with absolute t below 1 (Our choice, v0), in the placebo months.
4. This is a test design for risk taking. It says when a clock date should change a position, and it adds no factor. Do not duplicate E8 or F21: those are level scores.
