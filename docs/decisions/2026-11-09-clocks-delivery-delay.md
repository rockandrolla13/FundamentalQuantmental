# Delivery delay on the two clocks (Section 4.7.2)

Date: 2026-11-09. Status: built, report only, not fitted.

## Context
Section 4.7 reads each schedule on the filer's own timetable. A late building moves the revenue clock and leaves debt on fixed dates. Section 4.7 cannot say how many months of delay an issuer can carry. Card `junkbondinvestor-2026-who-funds-the-delay` names this as the main credit question after the November 2026 vote.

## Options
1. Leave delay to the memo. No number and no comparison across issuers.
2. Stress `first_shortfall_year` on the annual grid. The annual grid credits part-year rent at the year end. In the card's example, it reports 4 months of tolerance where the true answer is 0.
3. A monthly cumulative gap under a delay `d`, with a reserve, a rent credit, a tenant shift, and an outside date. Report the largest `d` the reserve carries.

## Choice
Option 3. `delay_tolerance` in `hy/clocks.py`. It reports only. It enters no score and no weight.

What the source says: the card's worked example and its five checks. What the data says: nothing yet. No market test has run. What we decide: build the measure, prove it on the card's example, and test it in the November 2026 window.

## Test that settles it
Among data centre issuers with material uncommenced capacity, rank by `effective_tolerance_months` at 1 November 2026. The claim holds if a lower tolerance goes with a wider spread change from 1 November to 31 December 2026. It fails if the rank correlation is zero or positive. The sample is small, so read it as a case study, not a cycle test.

## Open inputs
`reserve`, `rent_credit_ratio`, and `outside_date_months` come from indentures and leases, not from XBRL. They are analyst inputs with a citation, as in `scripts/clock_case.py`.

## First case: CoreWeave, 10-Q June 2026
Script: `scripts/clock_delay_case.py`. Inputs and the four analyst assumptions sit in its docstring. Reserve: $5.5bn of cash. Margin: 0.77 EBITDAR. Share of RPO that waits for unbuilt sites: 0.55. Window: 5 years.

| Case | Tolerance (months) | Extra need, 12 months late ($m) |
| --- | --- | --- |
| Base | 22 | 4,065 |
| Rent credits day for day | 8 | 6,608 |
| All RPO late (upper bound) | 5 | 11,457 |
| As if a landlord (rent does not move) | 15 | 4,602 |

What the data says: the cash covers a one-year delay in the base case. Rent credits and the share of revenue that waits set the answer. The capex clock is absent, so each tolerance is an upper bound. The blended interest rate is 4.0%, from LTM cash interest over average debt.
