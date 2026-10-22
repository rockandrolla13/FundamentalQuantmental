# Scenario engine defaults under macro paths (methodology Section 5.4, framework F6)

## Context
`hy/forward.py` now runs every F6 case under every macro path. The framework states the mechanics (F6.1 to F6.8) but leaves some numbers open. The task forbids a number set by hand without a decision page. This page lists them.

## Choice (all v0; framework R9 applies to each)

| Item | Default | Reason |
| --- | --- | --- |
| Refinance tenor | The new coupon prices off the 5-year forward Treasury on the maturity date under the path | Typical new-issue tenor for high yield |
| Access threshold | Refinance when `p_refi_access > 0.5`; exactly 0.5 fails | F6.3 says "exceeds" |
| Failed refinance | The maturity stays outstanding at its old coupon plus 5 points; `claims_view` is set; framework F5 takes over | A distressed exchange usually pays more; the claims view gives the recovery |
| Floating line that refinances | New margin equals `s_fair(m)` | Same pricing rule as a bond |
| Severe case margin | 1 point below the historic trough; with no trough given, the variable cost ratio rises 2 points over the moderate case | F6 table says "below the historic trough" without a size |
| Contracted revenue | A2 and A5 count as contracted for the 0.7 downside multiplier unless told otherwise | F6 archetype adjustment |
| F6.6 | Fires once per path; on by default | Avoids a cascade |
| Upside weight with the logistic | From the F6 table until an upside model is fitted | Section 5.2 fits only the decline event |
| Trend growth `G_bar` | The GDP forecast that the consensus base already embeds | Otherwise the shift counts the forecast twice |

## Decision: F6.6 shifts the weights (analyst, 22 October 2026)
When the combined downside weight exceeds 0.5, the weights shift down one step (downturn table: base, moderate, severe, upside 0.35, 0.35, 0.20, 0.10 become 0.10, 0.39, 0.51, 0.00). The forward distribution becomes more pessimistic: `lev_fwd_4`, `pd_12m`, and the event odds all use the shifted weights. The rejected reading only renamed which case is the base.

Consequence to watch: in a promoted state the earnings event reads a miss from the shifted downside weights, so the beat probability can fall to zero. Test that settles it: over matured earnings events in promoted states, the realised miss rate must lie inside the binomial band of the predicted miss probability; if it lies below, revisit the shift.

## Test
`tests/test_forward_paths.py`: monotone interest and revenue, refinance logic, weights sum to one, the F6.6 rule, mixture moments against brute force, and the probability integral transform of realised leverage (KS p = 0.55 on 600 synthetic draws; a biased model and a model with half the true dispersion both fail).
