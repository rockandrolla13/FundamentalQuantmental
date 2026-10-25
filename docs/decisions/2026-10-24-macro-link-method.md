# Macro link as its own method (G5, estimate E17)

Date: 2026-10-24. Status: built, not fitted. Methodology sections: 5.2.1, 8 (Composite). Code: `hy/forward.py` (`IssuerMacroModel`), `hy/groups.py` (`E17`, bucket `G5`), `scripts/process.py` (`_macro_logit`, `group_estimates`).

## Context
The user asked for the issuer-macro downside model of Section 5.2.1 as a separate input to the combined view. Before this change the combined view had 17 estimates in 5 weight buckets: core process, two clocks, built methods (rest), credit skills, books and peers. The macro state reached the combined view only through the case weights of E1.

## Options
1. Use the 5.2.1 model for the case weights only (the first proposal). The macro view stays inside E1.
2. Use the 5.2.1 model for the case weights and as a new estimate. The same macro view then counts twice.
3. Use the 5.2.1 model as a new estimate in its own bucket. The Section 5.2 model keeps the case weights of E1.

## Choice
Option 3. This is the user's choice. The combined view now has 18 estimates in 6 buckets.

- E17 sets the spread against the model's downside risk: `z(log s) - z(logit p)`, built like E12.
- E17 is a score. The run standardises it across issuers and scales it by sd(E1).
- The bucket share is 0 until tests T1 to T7 of Section 5.2.1 pass. A zero share shows the method in the memo. It does not change the combined number or the count of groups that agree.
- E17 is NaN while no fitted model exists. It is also NaN when the fit became available after the decision time, or when an input is missing.

What this means for the reader: on one date all issuers see the same macro state, so the macro level cancels in the ranking. E17 ranks issuers by their balance sheet and by how much the economy moves an issuer of their rating and class.

## Test that settles it
1. Tests T1 to T7 of Section 5.2.1 decide whether the model is valid.
2. After they pass, E17 must have a positive rank IC after costs in at least 3 of the 4 cycle windows (2008, 2015, 2020, 2022). This is the bar of the definition of done.
3. If both pass, the user sets the G5 share. If either fails, the share stays 0.

## Open
- The live share of G5. The user decides after the tests.
- The run stores no rating history. The downgrade and upgrade flags of the issuer term are NaN. So a fitted model that uses them gives no value until the data module supplies rating history.
- The macro inputs (EBP, issuance share at t − 8, the 10-year minus 3-month slope) are not in the data module yet.
- `scripts/walkforward.py` still replays the first 14 estimates and 5 buckets. Add G5 when E17 has values.
