# Gatto (2023), *The Credit Investor's Handbook*: credit cycle, cyclicality, and recession cases

Wiley, 2023. Practitioner book, not peer reviewed. This card covers only the passages that link the macro state to issuer forecasts and case weights. Page numbers are PDF pages of `/home/ak/Downloads/The Credit Investors Handbook ... Gatto ....pdf`, the same convention as `docs/methodology.md`.

## Claim
1. The credit cycle has four phases: expansion, downturn, repair, recovery (ch. 2, pp. 79–80). Bank lending standards tighten when the economy enters recession, and the tightening feeds back into the economy (p. 79).
2. Cyclicality is "a function of the correlation between an industry's sales and the business cycle" (p. 162). An industry is pro-cyclical, non-cyclical, or counter-cyclical (Figure 6.4, p. 163).
3. Cost structure decides how a revenue fall reaches EBITDA. A mostly fixed cost base leaves little room to cut costs in a recession (pp. 163–164).
4. Every cyclical issuer needs a recession downside case, sized from the issuer's own record in past recessions (pp. 285, 287, 306).
5. Case probabilities are an educated guess for the committee to debate (p. 311). The book gives one numeric example of macro case weights: no recession 80%, modest recession 15%, severe recession 5% (Figure 19.14, p. 536).
6. Not every credit downturn is a recession. The 2022 high yield bear market came from Fed tightening against inflation while the economy and profits stayed in good shape (pp. 98–99).

## Method
The book gives no formula for the macro link. It gives these rules and examples.

**Cycle phases (pp. 79–80).**
| Phase | What the book says happens |
| --- | --- |
| Expansion | Lax lending standards, cheap credit, issuers add leverage |
| Downturn | Economy slows into recession, defaults rise, lenders tighten, only high quality issuers keep access |
| Repair | Defaults start to fall, issuers cut costs and growth capex, some restructure in Chapter 11 |
| Recovery | Issuers pay down debt, then lenders relax standards and markets reopen |

The book warns that the cycle is not linear (pp. 81–82). Example: 2020 spent very little time in repair and recovery. It also states a base rate: "Historically, a recession happens on average every five years" (p. 96). The book gives no source for this rate.

**Cyclicality types (Figure 6.4, p. 163).**
| Type | Behaviour | Examples |
| --- | --- | --- |
| Pro-cyclical | Grows with the economy, does poorly in recession | Autos, restaurants, housing |
| Non-cyclical | No correlation with the economy | Healthcare, consumer staples, supermarkets |
| Counter-cyclical | Does better in recession | Repair and maintenance, bankruptcy advisory, collection agencies |

A sector can hold counter-cyclical segments, for example dollar stores inside retail (p. 163). Defensive is not uniform: hospitals are non-cyclical, but elective surgery is cyclical (p. 402).

**Recession case construction (TM Corp, pp. 290, 306–309).** Sales repeat the issuer's own 2008–2009 path: minus 20% then minus 10%, back to the pre-recession level in the third year. Variable COGS rises from 33.1% to 34.0% of sales. SG&A ratios stay, but "margin declines due to the absorption of the fixed component of SG&A over a lower sales base" (p. 306). Inventory and payable days worsen. Capex falls to maintenance, then catches up.

**Macro case weights (pp. 532–536).** A capital structure trade (long secured term loan, short unsecured bond) has three macro scenarios over two years. Each scenario has a P&L. The consensus recession odds weight them:

```latex
E[\text{P\&L}] = \sum_{s} p_s\,\text{P\&L}_s, \qquad (p_{none}, p_{modest}, p_{severe}) = (0.80,\ 0.15,\ 0.05)
```

Intuition: the total recession probability is 0.20, and the severe case takes one quarter of it. The book then says the trade makes sense only if "your firm believes the chances of a recession are much higher than the market is projecting" (p. 536).

## Data
Case studies only: TM Corp (fictional, pp. 290–311), VCC (pp. 380–391), HCA (pp. 402–413). Four lived downturns: 1997–1998, 2000–2002, 2008–2009, 2020 (Figure 2.2, p. 82). Auto sales fell 40% in the 2008 recession (p. 163). No sample, no estimation.

## Result
No statistical result. The usable numbers are:
- Recession base rate of one in five years (p. 96), so about 20% a year.
- Severe share of the recession probability: 0.05 / 0.20 = 0.25 (p. 536).
- TM Corp recession path: minus 20% then minus 10% (p. 290). VCC: 0% then minus 5% revenue, margin 120 bp below its lowest historic margin (p. 390).

## What our data says
No fit on our data yet. Effect on the three macro links:

1. **Link 1, path probabilities (5.4).** Supports the method only in spirit. The book weights macro scenarios by a consensus recession probability (p. 536). Our path masses come from forecast quantiles, which is a stricter form of the same idea. The p. 536 contrast between "our" odds and "the market's" odds is the gap that a market-implied path probability would measure. See `research/notes/creditmacro-macro-link.md`.
2. **Link 2, downside weights (5.2, F6).**
   - The book gives the first source for `f = 0.25`. Decision page `2026-10-21-downside-weight-split` says "The value of `f` is judgement. It has no source card yet." Figure 19.14 splits a 20% recession probability as 15% modest and 5% severe, so f = 0.25 (p. 536). That is one worked example of consensus odds, not an estimate.
   - The base rate of one recession in five years (p. 96) matches the expansion row of the F6 table, where the two downside weights add to 0.20.
   - The book has four phases. Section 3.6 already labels five (`cycle_phase`: expansion, late cycle, downturn, repair, recovery). But the F6 weight table has rows for only three: expansion, late cycle, downturn. So a repair or recovery quarter has no weight row. In repair, defaults fall while spreads may stay wide. In the F6 vote, `hy_oas` counts as "late cycle or downturn" only when it is above median and rises. But `distress_ratio` counts when it is above median, with no trend condition. So a repair quarter can still collect stress votes. Proposal: add weight rows for repair and recovery, and add a trend condition to `distress_ratio`. Test: in quarters that the Section 3.6 rules label repair (candidates, not yet labelled from data: 2009 H2, 2016 H2, 2020 H2), the realised EBITDA decline rate should sit below the downturn row weight.
   - The logistic models an EBITDA decline. The 2022 example (pp. 98–99) is a spread downturn with no EBITDA decline. Proposal: keep the policy rate channel (F6.4 and the `higher for longer` path) separate from the decline event, and do not expect the logistic to fire in a 2022-type quarter. Test: in the 2022 window, the realised EBITDA decline rate should stay near its expansion rate while `hy_oas` rises.
3. **Link 3, revenue shift (5.2).**
   - Supports the regression. The book defines cyclicality as the correlation of industry sales with the cycle (p. 162). That is the slope that `fit_sector_beta` in `hy/forward.py` estimates.
   - The sign can be negative. Counter-cyclical sectors exist (p. 163). The code must not floor `β_sector` at zero.
   - Revenue alone understates the EBITDA move. The book puts the fixed share of SG&A into the recession margin (p. 306). In `hy/forward.py` the downside cases apply `sga_fixed_share` (default 0.5) through `a_h^down = a_h(s_f / r_h + 1 − s_f)`. The macro shift of the base case (`shift_growth`) changes only `g`, and `a` stays a ratio of revenue. Proposal: apply the same fixed-share rule to the shifted base case. Test: on issuers with a recession in their history, the shifted base case with the fixed share should give a smaller EBITDA error at the trough than the case without it.
   - Sector is too coarse for some issuers. A segment can have a different sign from its sector (p. 163, p. 402). Proposal: allow an issuer override of `β_sector` with a logged rationale.

## Limits
- Practitioner judgement. No sample, no test, no out-of-sample record.
- The 80/15/5 split is a stated "consensus view" for one trade example. The book does not say where the consensus comes from.
- The one-in-five-years base rate has no citation in the book.
- Case studies are single issuers. The TM Corp recession path is one issuer's history and is fictional.

## Section touched
`docs/methodology.md` Section 5.2 (downside weight split `f`, phase prior, `β_sector` sign and the fixed-cost channel) and Section 5.4 (path probabilities against market odds). `docs/framework.md` F6 (phase vote and weight table). Decision page `docs/decisions/2026-10-21-downside-weight-split.md` (first source for `f = 0.25`). `hy/forward.py` (`fit_sector_beta`, `shift_growth`, `downside_scenario`).
