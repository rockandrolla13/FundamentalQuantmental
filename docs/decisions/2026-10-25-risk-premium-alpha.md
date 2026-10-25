# How much alpha: the risk premium test sizes, the estimates rank

Date: 2026-10-25. Status: built. Methodology section: 7.7. Code: `hy/alpha.py` (`credit_excess_states`, `risk_premium_alpha`), `scripts/process.py` (`risk_premium`, step 15, `combined_view`), `scripts/scenarios.py` (`p_liq_short_h`), `hy/groups.py` (E10 weight 0).

## Context
The user asked that the algorithm specification decide how much alpha a bond has. The user then set the question: "is there enough risk premium priced in for total return", not "survive or default".

Before this change:
- Step 15 compared one bond with cash. Almost any bond with a positive spread beats cash on average, so that test had a low bar.
- The 18-estimate combination gave the alpha number. The size calibration says that number can only rank.
- Step 15 had no zero-convergence case.
- A case that ran out of cash inside the horizon did not raise the default chance of step 15.

## Options
1. Keep "beats cash" as the alpha. Low bar: it pays a CCC bond for risk the market charges for.
2. Required premium from a fixed policy hurdle. Simple, but the number has no source.
3. Required premium from same-rating peers. It measures relative value inside a cell. It does not ask whether the cell itself pays for its risk.
4. Required premium at the price of risk of the HY index, in the same scenarios. The bond must earn `λ × ES_bond` with `λ = μ_index / ES_index`.

## Choice
Option 4. This is the user's choice ("go" on 2026-10-25).
- First build: the risk premium alpha sized and the 18 estimates ranked. E10 (excess over cash) had weight 0.
- User correction, same day: "the alpha should be a weighted number using all the models not just one". So:
  - E10 is now the risk premium alpha. It replaces the excess over cash, which used the same step 15 cash flows.
  - E10 keeps its v0 weight 0.05. Its effective weight is 10% (G1 40% over E7, E8, E9, E10).
  - The alpha of a bond is the weighted combination of all estimates, before trading costs. It also sets the rank.
- The test reports the alpha with the peer gap closing and with no closure.
- No trading cost enters the test. The user removed it on 2026-10-25. The test measures the premium in the price, not the cost of a trade.
- A case that runs out of cash inside the horizon defaults at `p_default_given_liq_short` (v0 0.5). The other half is the rescue branch.

Assumption that a reviewer may reject: each path takes its expected default share, for the bond and the index. The single-name default jump is not in the tail. Reason: a book of bonds diversifies that jump, and the market pays for risk that does not diversify. The expected default cost stays inside μ. Step 15 still shows the binary survive and default states, with P(loss) and the single-bond ES95, beside the test.

## Test that settles it
1. The size calibration refits with the weighted alpha as the predictor. The alpha sizes positions only if the fitted slope is positive and the map says "size".
2. Rank IC of the weighted alpha, and of E10 alone, against realised 6-month excess return over the DTS-hedged index, positive in at least 3 of 4 cycle windows (2008, 2015, 2020, 2022).
3. Compare with option 3: if same-rating peers give the higher IC, record it and revisit.

## Open
- The yardstick index runs at the bond's tenor. A full index model would use the index's own duration and default mix.
- The recession path has a low probability (1.7% in the 2026-09-18 run). λ depends on it, because the tail sets ES_index.
- Recovery, delay and the discount rate on a defaulted claim are v0 (R 0.4, 1 year, 15%).
