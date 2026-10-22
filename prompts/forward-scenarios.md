ultrathink

# Task: add forward-looking scenario analysis and link it to forecasts

Read first: CLAUDE.md; docs/methodology.md Sections 5, 7.1, 9.2 and 10;
docs/framework.md F4, F6, F9 and F11. Keep their section numbers. Extend,
do not renumber.

## Objective
Build the layer that turns external forecasts into issuer scenarios, and
issuer scenarios into forecast-conditional outputs: forward features, PD,
fair spread, event P&L. Every scenario weight and every driver shift must
trace to a named forecast with a vintage date, or to a market-implied
quantity. No weight or shift may be set by hand without a decision page.

## Inputs to wire
1. Macro forecasts, with vintage and `available_at`:
   survey consensus (GDP growth, CPI, unemployment) with quantiles;
   the central bank's rate projections; fed funds futures; the Treasury
   forward curve; rating agency default rate forecasts; the bank lending
   survey; high yield index spread and distress ratio.
2. Sector forecasts by archetype (framework F2): energy price decks for
   A3; reimbursement schedules for A2; housing and auto forecasts for A4;
   AI capex and utilisation forecasts for compute infrastructure.
3. Issuer forecasts: management guidance, sell-side consensus with count
   and dispersion, and the analyst's base, downside, and upside cases,
   each with a vintage.

## Build, in this order
1. `hy/forecasts.py`: a forecast registry. One row per source, variable,
   horizon, vintage. Fields: `source`, `variable`, `horizon_q`, `vintage`,
   `available_at`, `point`, `q10`, `q50`, `q90`, `method`. A reader that
   returns only rows with `available_at` before the decision time.
2. `hy/macro.py`: a path builder. Construct 4 to 6 named macro paths
   from the forecast quantiles: soft landing, recession, higher for longer,
   disinflation rally, stagflation. Each path is a quarterly vector of
   2-year and 10-year Treasury yields, policy rate, GDP growth, PMI,
   index spread, default rate, 8 quarters long. Set path probabilities
   from the quantile mass of the forecast distribution, then combine with
   the phase prior of framework F6 as a Bayesian update. Record both.
   Split each path's yield change into a growth part and a policy part
   with the two-factor regression of methodology Section 9.2 and store
   `beta_g` and `beta_p` by rating bucket and sector.
3. `hy/forward.py`: the scenario engine of methodology Section 5.1 and
   framework F6. Each driver links to a forecast variable through a
   sensitivity `beta_sector` estimated on history. The base case equals
   consensus plus the analyst's stated per-driver gap; store the gap.
   Downside and upside cases follow F6. Interest follows the policy rate
   path for floating debt. Each maturity inside the horizon refinances at
   the forward Treasury for its date plus the fair spread under that path,
   or fails per F6.3. Run every case under every macro path.
4. Weights: `w_s(m)` from the logistic of methodology Section 5.2 once
   calibrated; until then the F6 table with the archetype adjustment. The
   combined downside weight above 0.5 promotes the downside to base (F6.6).
5. Outputs per issuer, per path, and probability-weighted across paths:
   `lev_fwd_4`, `lev_fwd_8`, `lev_fwd_sd`, `lev_peak_down`, `liq_min_down`,
   `p_breach_4`, `p_liq_short_8`, `p_refi_4`, `cov_fwd_4`, `pd_12m`,
   `s_fair`, `resid_bp`. Write them to `issuer_state` and `bond_daily`
   with a `macro_path` column and a `weighted` row.
6. `hy/events.py`: the event matrix of methodology Section 10.4 with
   `p_path` from step 2 and `p_outcome_given_path` from step 4. Position
   P&L per outcome and path follows the formula in Section 9.2.
7. Revision tracking: on every new vintage compute `rev_lev`,
   `gap_consensus`, `gap_mgmt`, and the change in each path probability.
   Expose them to signal S3 and S7.
8. Forecast error accounting: store realised values against every
   forecast row at maturity of its horizon. Report bias and absolute
   error by source and horizon. Use it to widen or shrink the quantile
   mass in step 2.

## Mathematics to state in the docstrings
- The recursion for revenue, EBITDA, FCF, debt, liquidity, and headroom.
- `E_t[Lev_{t+h}] = sum over paths and cases of p(m) w_s(m) Lev^s_h(m)`
  and its variance.
- The yield split: `dy = dy_growth + dy_policy`,
  `ds_sys = beta_g dy_growth + beta_p dy_policy`.
- The refinance coupon: forward Treasury at the maturity date under path
  m, plus `s_fair(m)`, minus the old coupon, applied to the maturity
  amount in the FCF recursion.
- One sentence of intuition beside each formula.

## Tests, all must pass
- No look-ahead: a decision at time t reads no forecast row with
  `available_at` after t. Build a fixture that fails if it does.
- Path probabilities sum to one before and after the Bayesian update.
- Monotonicity: a higher policy rate path never lowers floating interest
  cost; a lower GDP path never raises base case revenue for a positive
  `beta_sector`.
- PIT: on synthetic data with known paths, the probability integral
  transform of realised leverage against the predicted distribution is
  near uniform.
- Refinance logic: a maturity refinances when `p_refi_access` exceeds 0.5
  and fails otherwise, with the claims view engaged on failure.
- Synthetic issuers only. No real issuer figures in tests or docs.

## Documents to update
- docs/methodology.md: add Section 5.4 "Forecast linkage" with the
  registry, the path builder, the weight update, and the error accounting.
  Add the yield split betas to Section 9.2 outputs and to Section 10.
- docs/framework.md: add to F6 the rule that every weight and every
  driver shift cites a forecast row or a market-implied quantity, and
  the fallback order when a source is missing: market-implied, then the
  F6 table, then a logged assumption.
- docs/decisions/: one page for the path construction method, one for
  the Bayesian combination with the phase prior.
- research/cards/: one card per forecast source with its coverage,
  cadence, revision policy, and known biases.

## Working rules
- Ask at most three clarifying questions, then proceed with stated
  defaults. State each default in the decision page.
- Write all prose in ASD-STE100 Simplified Technical English.
- Finish with a one-page summary: what was built, what the tests cover,
  which forecast sources are wired, which are stubbed, and the first
  three calibration tasks once real data arrives.
