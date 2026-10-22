# Duration mismatch features (Section 4.7)

## Context
Leverage and coverage use one period of earnings. They do not show when fixed obligations fall due against when contracted revenue arrives. The source card `research/cards/radhakrishnan-2026-ai-buildout-risk.md` argues that this gap is where neocloud credit risk sits. The filings tag the needed schedules in XBRL, but the company-facts feed drops the dimensional facts (RPO timing, customer shares).

## Options
1. Leave it to the analyst's memo. No number, no test, not comparable across issuers.
2. A single ratio, for example uncommenced leases over RPO. Ignores timing, which is the whole point.
3. Both schedules on one annual grid from the filing's own XBRL instance, with duration, runoff, renewal-dependent share, contracted coverage, and cumulative shortfall; every assumption stated and stressed.

## Choice
Option 3. `hy/sources/xbrl_instance.py` reads the full instance with dimensions. `hy/sources/schedules.py` extracts ladders and checks each against its stated total. `hy/clocks.py` computes the features. Fields the filing does not give are analyst inputs with a citation in `scripts/clock_case.py`.

Results at the latest filings (base assumptions):

| | CoreWeave (Jun-2026) | Oracle (Aug-2026) |
| --- | --- | --- |
| Fixed obligations against RPO | $112bn against $104bn | $559bn against $664bn |
| Breakeven margin (sum O over sum R) | 1.08 | 0.84 |
| Centre of charges against centre of contract cash | year 5.3 against 3.4 | year 8.2 against 3.4 |
| Renewal-dependent share | 24% ($27bn, 7.2x LTM EBITDA) | 37% ($205bn, 6.0x LTM EBITDA) |
| Revenue to sign after runoff | 3.4 years of run-rate | 4.8 years of run-rate |
| Contract cover at company EBITDAR margin | 0.71 | 0.65 |
| Contract cover at a 20% margin | 0.18 | 0.24 |
| Top customer does not pay (CoreWeave) | cover 0.45, shortfall $61bn | n/a (no disclosure) |

Correction, 22 October 2026: the first run stretched the lease "thereafter" bucket to match the stated 12-year average remaining term. That average weights lease lengths, not payment dates, so it overstated the tail (to 25 years). The tail now runs at the last stated yearly amount (8.3 years for CoreWeave). CoreWeave's duration gap fell from 3.3 to 1.9 years; the breakeven margin and the shortfall did not change.

## Test
Offline: `tests/test_clocks.py` (mass conservation, run-rate tail, breakeven margin, a hand-solved mismatch case, ladder layout and reconciliation, dimensional parsing).
Open test that settles the feature's value: across issuers with RPO and lease disclosure, `renewal_dependent_ebitda_years` must have a positive partial correlation with spread after the Section 7.2 features, and a positive rank IC for spread change around renewal dates.

Known limits: the margin on AI backlog is unknown and likely below the company margin (the 20% row bounds it); early surplus cash is treated as available for later charges, so the shortfall is a lower bound.
