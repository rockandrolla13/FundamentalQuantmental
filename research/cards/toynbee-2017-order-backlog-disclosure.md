# Toynbee (2017), "Implications of Disclosing Order Backlog"

Added by citation chasing. Habib, Ranasinghe and Bhuiyan cite it (their PDF p. 6), and the shortlist names it as open. It is a different document from Toynbee (2026) in the Journal of Financial Reporting, which we could not open. PhD dissertation, University of Washington, 2017, 83 pages. Not peer reviewed as a journal article. Page numbers below are PDF pages. PDF page = printed page + 3. Evidence class: manufacturing firms, equity prices and investment. No credit outcome.

## Claim
Firms that disclose the dollar amount of order backlog have higher forward earnings response coefficients and greater investment efficiency (p. 3). These effects are concentrated in make-to-order firms, where backlog is a stronger signal of demand (p. 3). Backlog has weak disclosure rules, and firms often count cancellable orders (p. 4).

## Method
**Comparison (p. 5).** Disclosers against non-disclosers with a similar chance of material backlog. The test uses the fact of disclosure and not the amount (p. 5, footnote 3).

**Sample design (p. 6).** Fifteen manufacturing industries in which backlog is common, so that non-disclosure is less likely to mean no backlog. Propensity score match.

**Price test (p. 25).** The forward earnings response coefficient, FERC, is the sum of the slopes on next-year earnings and next-year return, each interacted with the discloser indicator.

```latex
Ret_{i,t} = \dots + \lambda_7 (Earn_{i,t+1} \times Discloser_{i,t}) + \lambda_8 (Ret_{i,t+1} \times Discloser_{i,t}) + e_{i,t}, \qquad \text{FERC} = \lambda_7 + \lambda_8
```

Intuition: if backlog tells investors about next year, today's price moves more with next year's earnings for firms that disclose it.

**Business model split (p. 26).** `MTS` is 1 when finished goods exceed 50% of total inventory. These firms make to stock.

## Data
- Fifteen manufacturing industries, 1996 to 2014 (p. 6).
- The share of disclosers across the industries runs from 37.8% to 95.3% (p. 22).
- Backlog over sales averages 0.133 to 1.077 across industries (p. 22).
- Only 27.6% of disclosers report non-zero deferred revenue, and backlog exceeds deferred revenue for 93.3% of those (p. 10, footnote 6).
- In manufacturing the share of firms that disclose backlog fell from 47.0% in 1973 to 24.8% in 2015 (p. 12).

## Result
**Price (Table 3 Panel B, p. 54).** Next-year earnings times discloser:

| Sample | Make to order (`MTS = 0`) | Make to stock (`MTS = 1`) |
| --- | --- | --- |
| Full, no controls | 0.378 (t 2.44) | 0.060 (t 0.25) |
| Full, with controls | 0.197 (t 1.94) | -0.006 (t -0.05) |
| Matched, no controls | 0.509 (t 2.59) | -0.245 (t -0.64) |

F-test on the sum for make-to-order firms, full sample: 5.70 and 3.78. For make-to-stock firms: 0.25 and 0.07.

**Quality of the number (pp. 4, 11).**
- "Firm" order has no precise definition, so backlog can vary across and within firms.
- Some firms count only non-cancellable orders, and others count cancellable ones.
- Filings do not usually state an expected cancellation rate.

**Disclosure gap (p. 6).** Deere and AGCO are direct competitors, and only Deere discloses backlog. So non-disclosure does not imply no backlog.

**Rules (p. 5, footnote 4).** ASC 606 requires the aggregate transaction price of unsatisfied performance obligations, and the timing of recognition.

## Limits
- A dissertation. Discretion over disclosure may bias the results toward finding benefits (p. 39).
- Manufacturing only. The author warns against extension to other sectors (p. 39).
- Disclosure, not the amount, is the test variable (p. 5, footnote 3).
- The sample ends before ASC 606 applies. So it does not test RPO.
- No credit test.

## Section touched
`docs/methodology.md` Section 4.7 (revenue clock, RPO as filed, rule 3, `rpo_material` filter). `hy/sources/clock_facts.py`. `hy/sources/clock_inputs.py`.

## Use for the two clocks
**What the source says.** A signed-order number varies by issuer in meaning. It carries information mainly where production follows orders. Absence of the number does not mean absence of orders.

**What the data says.** `clock_facts.py` treats `RevenueRemainingPerformanceObligation` as a clean total. The filter `RPO_MATERIAL` keeps issuers with RPO at or above 25% of LTM revenue. The 187 issuers of Section 4.7 are the result of that selection. We could not open Toynbee (2026) on how far the practical expedient limits RPO disclosure.

**What we decide (our proposal, not the source's claim).**
1. Keep RPO and backlog as separate fields. RPO comes from the audited note, and backlog comes from Item 1 and is not audited. Do not fill one with the other.
2. Add `rpo_scope_flag`, set from filing text when the issuer states that it excludes short contracts from RPO or uses a practical expedient. A flagged RPO is a floor on the revenue clock, so report `revenue_runoff` as a lower bound.
3. Report the split test for two groups: contract businesses and make-to-stock businesses, with the finished goods share above 0.50 as the split (source's line, p. 26).
4. Replace the 25% filter in robustness with lines of 10% and 50% (Our choice, v0). If the recontract sign changes across lines, then the Section 4.7 result depends on the selection.
5. **A proxy that reaches earlier windows.** Item 101(c)(1)(viii) of Regulation S-K, as quoted here, asks for dollar backlog and "an indication of the portion thereof not reasonably expected to be filled within the current fiscal year" (p. 61). That gives two time buckets, before RPO exists. So add `ob_sales` and `ob_beyond_fy_share` from Compustat backlog and 10-K text, 2004 to 2018, inside industries with disclosure of at least 25% (source's floor, p. 19). Label it a proxy, because cancellable orders can enter it (p. 4). The current text of 17 CFR 229.101, as opened on 2026-11-01, holds no backlog line, after the amendment at 85 FR 63759 (October 8, 2020). So the proxy has no legal basis after that date. Test M1.8 of `docs/decisions/2026-11-01-clocks-residual-timing.md` reads it.
