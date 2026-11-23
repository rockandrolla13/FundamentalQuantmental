"""Market-implied rating and the rating-drift templates (methodology Section 4.5.1)."""

import numpy as np

from hy import state


def _market(seed=0, per_notch=8, notches=(0, 1, 2, 3, 4)):
    """Spreads fall by a fixed step per notch, with small noise. Higher notch = better rating."""
    rng = np.random.default_rng(seed)
    r = np.repeat(np.asarray(notches), per_notch)
    ls = 7.0 - 0.4 * r + rng.normal(0.0, 0.05, r.size)
    return ls, r


def test_implied_rating_matches_agency_in_a_fair_market():
    ls, r = _market()
    assert np.array_equal(state.market_implied_rating(ls, r), r)


def test_implied_rating_follows_the_price_not_the_label():
    ls, r = _market()
    ls[0] = 7.0 - 0.4 * 3  # a notch-0 issuer priced like notch 3
    assert state.market_implied_rating(ls, r)[0] == 3


def test_implied_rating_leaves_the_issuer_out_and_skips_thin_notches():
    # notch 1 holds 3 issuers. Leaving one out leaves 2 peers, below min_peers=3, so only notch 0 qualifies.
    ls = np.array([5.0, 5.0, 5.0, 5.0, 4.0, 4.0, 4.0])
    r = np.array([0, 0, 0, 0, 1, 1, 1])
    m = state.market_implied_rating(ls, r, min_peers=3)
    assert list(m[4:]) == [0, 0, 0]
    assert list(m[:4]) == [0, 0, 0, 0]
    assert list(state.market_implied_rating(ls, r, min_peers=2)[4:]) == [1, 1, 1]


def test_implied_rating_medians_are_forced_monotone():
    # notch 1 trades wider than notch 0. The running minimum sets the notch-1 median to the notch-0 level.
    ls = np.array([6.0] * 4 + [6.5] * 4 + [5.0] * 4)
    r = np.repeat([0, 1, 2], 4)
    m = state.market_implied_rating(ls, r)
    assert set(m[4:8]) == {0}  # a tie between notches 0 and 1 resolves to the worse notch
    assert set(m[8:]) == {2}


def test_drift_templates():
    fitted = np.array([1, 1, 1, 5, 3, 3])
    agency = np.array([3, 3, 3, 3, 3, 3])
    implied = np.array([1, 3, 1, 5, 3, -1])
    watch = np.array([0, 0, -1, 0, 0, 0])
    out = state.rating_drift(fitted, agency, implied, watch)
    assert list(out["template"]) == ["agency_lags", "market_misses", "none", "agency_lags", "none", "none"]
    assert list(out["direction"]) == [-1, -1, -1, 1, 0, 0]


def test_small_model_gap_calls_nothing():
    out = state.rating_drift([2], [3], [2])
    assert out["template"][0] == "none" and out["direction"][0] == 0
