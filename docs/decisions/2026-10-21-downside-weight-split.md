# Scenario weights: split the decline probability between the two downside cases

## Context
Section 5.2 fits `p`, the probability of a large EBITDA decline over four quarters. The old text gave `p` to the moderate downside, and gave the severe case "a fixed fraction of it". Read literally, the two downside weights add up to more than `p`.

## Options
1. Moderate `p`, severe `fp`. The total downside weight `(1 + f)p` exceeds the fitted probability of the decline event.
2. Moderate `(1 − f)p`, severe `fp`. The total downside weight equals `p`.

## Choice
Option 2, with `f = 0.25`. The severe case is a deeper version of the same decline event, not a separate event. So the two cases must share the probability of that event. The value of `f` is judgement. It has no source card yet.

## Test
`tests/test_forward.py::test_downside_weights_split_p_between_moderate_and_severe`: with `p = 0.2`, the moderate weight is 0.15, the severe weight is 0.05, and all weights sum to 1. The test passes.

Open test on real data: the Section 11 reliability test for `w_down(m)` uses the sum of the two downside weights.

Changed: `docs/methodology.md` Section 5.2 and the root copy.
