import numpy as np
import pandas as pd
import pytest

from hy import clocks, rv


def test_modified_duration_matches_textbook_par_bond():
    # 5-year 6% semi-annual par bond: modified duration about 4.27.
    assert rv.modified_duration(0.06, 0.06, 5.0) == pytest.approx(4.265, abs=0.01)
    assert rv.modified_duration(0.06, 0.06, 0.0) == 0.0


def test_expected_loss_anchor_and_kappa():
    s_el = rv.el_spread(0.036, 0.60)
    assert s_el == pytest.approx(-np.log(1 - 0.036) * 0.6)
    assert rv.kappa(2 * s_el, 0.036, 0.60) == pytest.approx(2.0)


def test_lease_adjusted_leverage_book_formula():
    assert rv.lease_adjusted_leverage(debt=400.0, rent=10.0, ebitda=90.0) == pytest.approx((400 + 80) / 100)


def test_cover_to_maturity_inside_and_after_the_book():
    # Contracts pay 40/yr for 3 years at full margin; rent 10/yr for 10 years.
    res = clocks.mismatch({"rent": [clocks.Bucket(0, 10, 100.0)]}, [clocks.Bucket(0, 3, 120.0)], 1.0, 12)
    assert rv.cover_to_maturity(res, 2.0) == pytest.approx(80.0 / 20.0)
    assert rv.cover_to_maturity(res, 10.0) == pytest.approx(120.0 / 100.0)
    assert rv.cover_to_maturity(res, 2.5) == pytest.approx(100.0 / 25.0)


def test_curve_fit_and_common_tenors():
    a, b = rv.curve_fit([3.0, 5.0], [0.05, 0.06])
    assert rv.curve_at((a, b), 4.0) == pytest.approx(0.055)
    assert rv.curve_fit([4.0], [0.07]) == (0.07, 0.0)
    assert rv.common_tenors([3.6, 5.7], [1.0, 30.0]) == [4.0, 5.0]
    assert rv.common_tenors([1.0, 2.0], [5.0, 8.0]) == [3.5]  # no overlap: midpoint of the gap


def test_pair_price_of_risk_picks_more_spread_per_unit():
    a = rv.IssuerRisk("A", lev_lease_adj=6.0, breakeven_margin=1.08)
    b = rv.IssuerRisk("B", lev_lease_adj=3.0, breakeven_margin=0.84)
    t = rv.pair_price_of_risk(0.06, 0.02, a, b).set_index("metric")
    assert t.loc["lev_lease_adj", "bp_per_unit_A"] == pytest.approx(100.0)
    assert t.loc["lev_lease_adj", "gap_bp_per_unit"] == pytest.approx(400 / 3)
    assert t.loc["lev_lease_adj", "cheaper"] == "A"
    assert "renewal_dependent_ebitda_years" not in t.index  # NaN risk is skipped, not zero


def test_benchmark_excess_uses_bucket_median_and_iqr():
    buckets = pd.DataFrame({"lo": [1, 3], "hi": [3, 5], "median": [0.03, 0.035], "iqr": [0.01, 0.01349]})
    ex, z = rv.benchmark_excess(0.045, 4.0, buckets)  # 100 bp over a bucket whose robust sd is 100 bp
    assert ex == pytest.approx(100.0) and z == pytest.approx(1.0)
