"""Delivery delay on the two clocks (methodology Section 4.7.2), on synthetic lease schedules.

The base case is the worked example of the source card `junkbondinvestor-2026-who-funds-the-delay`: $2bn of
five-year notes at 10%, rent due from month 18, and a $300mm interest reserve that carries the coupons to then.
"""

import numpy as np
import pytest

from hy import clocks
from hy.clocks import Bucket

COUPONS = [Bucket(0.0, 5.0, 1000.0)]  # $200mm a year for five years
RENT = [Bucket(1.5, 13.5, 600.0 * 13.5)]  # $600mm a year from month 18, triple net (margin 1)


def project(**kw):
    return clocks.delay_tolerance({"interest": COUPONS}, RENT, 1.0, window_years=5, **kw)


def test_reserve_sized_to_the_rent_start_carries_no_delay():
    r = project(reserve=300.0)
    assert r.metrics["peak_need_0"] == pytest.approx(300.0)
    assert r.metrics["delay_tolerance_months"] == 0.0


def test_one_year_late_opens_one_year_of_coupon():
    assert project(reserve=300.0).metrics["extra_need_12m"] == pytest.approx(200.0)


def test_each_extra_100_of_reserve_buys_six_months():
    assert project(reserve=400.0).metrics["delay_tolerance_months"] == 6.0
    assert project(reserve=500.0).metrics["delay_tolerance_months"] == 12.0


def test_reserve_short_at_zero_delay_reads_nan():
    assert np.isnan(project(reserve=250.0).metrics["delay_tolerance_months"])


def test_need_never_falls_with_more_delay():
    r = project(reserve=300.0)
    assert np.all(np.diff(r.peak_need) >= -1e-9)


def test_rent_credit_deepens_the_gap_one_for_one():
    # A 12-month delay with day-for-day credits: 12 more months of coupon before rent, then 12 months of rent
    # credited back while coupons run. Extra need is 200 + 200.
    r = project(reserve=300.0, rent_credit_ratio=1.0)
    assert r.metrics["extra_need_12m"] == pytest.approx(400.0)


def test_tenant_rent_moves_with_delivery_and_landlord_debt_does_not():
    lease = [Bucket(1.0, 10.0, 1000.0)]
    revenue = [Bucket(1.0, 10.0, 1200.0)]
    tenant = clocks.delay_tolerance({"lease_uncommenced": lease}, revenue, 1.0, 0.0, shift=("lease_uncommenced",))
    landlord = clocks.delay_tolerance({"debt_interest": lease}, revenue, 1.0, 0.0)
    assert np.allclose(tenant.extra_need, 0.0)
    assert landlord.metrics["extra_need_12m"] > 0


def test_outside_date_before_the_cash_runs_out_sets_the_limit():
    r = project(reserve=400.0, outside_date_months=3)
    assert r.metrics["outside_date_binds"] == 1.0
    assert r.metrics["effective_tolerance_months"] == 3.0
    assert np.isnan(project(reserve=400.0).metrics["outside_date_binds"])


def test_annual_array_delays_like_buckets():
    grid = clocks.to_grid(RENT, 25)
    a = clocks.delay_gap({"interest": COUPONS}, grid, 1.0, 0.5)
    b = clocks.delay_gap({"interest": COUPONS}, clocks.ladder(list(grid), first_length=1.0, tail_years=1.0), 1.0, 0.5)
    assert a[-1] == pytest.approx(b[-1])
    assert clocks.delay_gap({"interest": COUPONS}, RENT, 1.0, 0.0)[-1] == pytest.approx(600.0 * 13.5 - 1000.0)
