# Market-implied rating and the two rating-drift templates (Section 4.5.1)

Date: 2026-11-23. Status: built and tested on synthetic data. No market test has run.

## Context
The rating gap of Section 4.5 compares the fitted rating with the agency rating. It cannot say whether the bond price already agrees with the fitted rating. The European single-name spec v. 080212 (card `european-single-name-spec-2012`, p. 13) splits rating trades by that question, with Moody's bond market implied ratings.

What the source says: two templates, model and market agree but the agency lags, or the model calls a change that the market does not price. It gives no cut-offs and no test.

What the data says: nothing yet.

## Options
1. **Keep the two-rating gap.** Simple, but one signal mixes two trades with different horizons.
2. **Buy Moody's market implied ratings.** Vendor data. It cannot enter the public repository, and it hides its method.
3. **Build a market-implied rating from the cross-section.** Leave the issuer out, take the median log spread of each agency notch, force the medians to fall with the rating, and pick the nearest notch.

## Choice
Option 3. Reasons:
1. It uses only data that the analyst already holds: spreads and agency ratings.
2. Leaving the issuer out stops a bond from pulling its own notch towards itself. `hy/peers.py` uses the same rule.
3. The running minimum stops a thin or noisy notch from giving an implied rating out of order.

Our choice, with no source:
1. A model gap of 2 notches before the model calls a change (`DRIFT_MODEL_CUT`).
2. A market gap of 1 notch before the price "agrees" (`DRIFT_MARKET_CUT`).
3. A notch needs 3 other issuers (`MIR_MIN_PEERS`).
4. A tie between two notches goes to the worse notch.

## Tests that settle it
1. **Wiring (done).** `tests/test_rating_drift.py` holds 6 tests: a fair market gives back the agency ratings, the implied rating follows the price, the leave-out and thin-notch rules, the monotone medians, and both templates.
2. **Market.** Over the next 6 months, `market_misses` names should move further in the direction of the model gap than `agency_lags` names. If both move the same, the third rating adds nothing.
3. **Agency.** `agency_lags` names should get the rating action more often than names with no template within 12 months.

## Limits
1. The implied rating ignores duration and seniority. A long or junior bond trades wider at the same rating. A later version can use the fair spread residual of Section 7 in place of the raw spread.
2. One date, one cross-section. Notches with few issuers drop out.
