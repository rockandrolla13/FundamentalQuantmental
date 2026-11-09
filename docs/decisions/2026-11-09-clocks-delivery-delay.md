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
