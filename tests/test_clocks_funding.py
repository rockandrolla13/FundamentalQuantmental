"""Funding source of a delay gap (methodology Section 4.7.2)."""

import math

import pytest

from hy import clocks


def test_cash_fills_first_and_nothing_reaches_the_market():
    f = clocks.funding_source(200.0, cash=300.0, committed=500.0)
    assert f["from_cash"] == 200.0 and f["from_committed"] == 0.0 and f["from_market"] == 0.0
    assert f["last_source"] == "cash" and f["market_share"] == 0.0


def test_order_is_cash_committed_promised_market():
    f = clocks.funding_source(1000.0, cash=100.0, committed=200.0, promised=300.0, market_cap=2000.0)
    assert [f[f"from_{k}"] for k in clocks.FUNDING_ORDER] == [100.0, 200.0, 300.0, 400.0]
    assert f["last_source"] == "market"
    assert f["market_share"] == pytest.approx(0.4)
    assert f["market_capacity_used"] == pytest.approx(400.0 / (0.2 * 2000.0))


def test_a_lower_stock_price_uses_more_of_the_capacity():
    before = clocks.funding_source(500.0, cash=100.0, market_cap=3000.0)["market_capacity_used"]
    after = clocks.funding_source(500.0, cash=100.0, market_cap=3000.0 * 0.68)["market_capacity_used"]
    assert after > before


def test_no_gap_and_no_market_cap():
    f = clocks.funding_source(0.0, cash=10.0)
    assert f["last_source"] == "none" and f["from_market"] == 0.0
    assert math.isnan(clocks.funding_source(50.0)["market_capacity_used"])
