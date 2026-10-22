"""Offline tests of the monthly TRACE panel: trade cleaning in all three status eras, volume parsing, the monthly
aggregate, bid-ask proxy, survivorship exit rows, issuer link, and point-in-time leverage (Sections 3.1, 3.2, 11)."""

import numpy as np
import pandas as pd
import pytest

from hy.sources import trace_panel as tp


def _trade(cusip, day, seq, st, vol, pr, yld=7.0, orig=None, side=None, cpt=None, asof=None):
    return dict(cusip_id=cusip, trd_exctn_dt=day, msg_seq_nb=seq, orig_msg_seq_nb=orig, trc_st=st,
                ascii_rptd_vol_tx=vol, rptd_pr=pr, yld_pt=yld, yld_sign_cd=None, side=side, contra_party_type=cpt,
                asof_cd=asof)


@pytest.mark.parametrize("trade,cancel,correct", [("T", "C", "W"), ("G", "H", "I"), ("M", "N", "O")])
def test_clean_trades_removes_cancelled_and_corrected_reports_in_every_era(trade, cancel, correct):
    rows = [
        _trade("A", "2020-06-29", 1, trade, "200000", 100.0),
        _trade("A", "2020-06-29", 2, trade, "300000", 101.0),          # cancelled below
        _trade("A", "2020-06-29", 3, cancel, "300000", 101.0, orig=2),
        _trade("A", "2020-06-29", 4, trade, "1MM+", 99.0),             # corrected below
        _trade("A", "2020-06-29", 5, correct, "1MM+", 98.5, orig=4),
        _trade("A", "2020-06-30", 6, trade, "500000", 97.0, asof="R"),  # reversal dropped
        _trade("A", "2020-06-30", 7, trade, "5MM+", 102.0, yld=None),   # no yield: kept for price
    ]
    c = tp.clean_trades(pd.DataFrame(rows))
    assert sorted(c["pr"].tolist()) == [98.5, 100.0, 102.0]
    assert c.loc[c["pr"] == 98.5, "par"].item() == 1_000_000.0     # '1MM+' read as its floor
    assert c.loc[c["pr"] == 102.0, "par"].item() == 5_000_000.0
    assert np.isnan(c.loc[c["pr"] == 102.0, "yld"].item())


def test_aggregate_window_weights_by_par_and_drops_retail():
    rows = [
        _trade("A", "2020-06-29", 1, "M", "100000", 100.0, yld=6.0, side="S", cpt="C"),
        _trade("A", "2020-06-29", 2, "M", "300000", 98.0, yld=6.4, side="B", cpt="C"),
        _trade("A", "2020-06-30", 3, "M", "50000", 90.0, yld=9.0),          # retail size: out
        _trade("A", "2020-06-30", 4, "M", "200000", 99.0, yld=None),        # no yield: in price only
    ]
    g = tp.aggregate_window(tp.clean_trades(pd.DataFrame(rows))).iloc[0]
    assert g["n_trades"] == 3 and g["par_volume"] == 600_000
    assert g["price_vw"] == pytest.approx((100 * 1 + 98 * 3 + 99 * 2) / 6)
    assert g["yield_vw_pct"] == pytest.approx((6.0 * 1 + 6.4 * 3) / 4)
    assert g["px_dealer_sell"] - g["px_dealer_buy"] == pytest.approx(2.0)
    assert g["day_range"] == pytest.approx(2.0)          # only 29 June has two trades
    assert g["last_trade"] == pd.Timestamp("2020-06-30")


def test_month_sql_has_no_percent_sign_and_uses_all_status_eras():
    sql = tp.month_sql("2008-06-15")
    assert "%" not in sql
    assert "'2008-06-24' and '2008-06-30'" in sql
    for code in ("T", "G", "M", "W", "I", "O", "C", "H", "N"):
        assert f"'{code}'" in sql
    assert "stdt <= '2008-06-30'" in sql                 # master version in force then, not today's


def _curve(date="2020-06-30", level=0.01):
    row = pd.Series({1.0: level, 5.0: level, 10.0: level, 30.0: level}, name=pd.Timestamp(date))
    return row


def _raw(**kw):
    base = dict(cusip_id="123456AB7", last_trade=pd.Timestamp("2020-06-30"), n_trades=4, par_volume=2e6,
                price_vw=100.0, yield_vw_pct=7.0, px_dealer_sell=100.5, px_dealer_buy=99.5, day_range=0.8,
                mtrty_dt=pd.Timestamp("2025-06-30"), cpn_rt=7.0, company_symbol="ABC")
    base.update(kw)
    return pd.DataFrame([base])


def test_finish_month_units_spread_duration_and_bid_ask():
    p = tp.finish_month(_raw(), "2020-06-30", _curve()).iloc[0]
    assert p["yield"] == pytest.approx(0.07) and p["g_spread"] == pytest.approx(0.06)
    assert p["cusip6"] == "123456" and p["coupon"] == pytest.approx(0.07)
    assert p["bid_ask_pts"] == pytest.approx(1.0) and p["bid_ask_source"] == "side"
    assert 4.0 < p["mod_dur"] < 4.3
    assert p["available_at"] == pd.Timestamp("2020-07-01")


def test_finish_month_fills_missing_yield_from_price_and_falls_back_to_day_range():
    p = tp.finish_month(_raw(yield_vw_pct=np.nan, price_vw=95.0, px_dealer_sell=np.nan), "2020-06-30", _curve()).iloc[0]
    assert p["yield_source"] == "from_price"
    assert tp.price_from_yield(p["yield"], 0.07, p["years"]) == pytest.approx(95.0, abs=1e-6)
    assert p["bid_ask_source"] == "day_range" and p["bid_ask_pts"] == pytest.approx(0.8)


def test_finish_month_rejects_a_curve_after_month_end():
    with pytest.raises(ValueError):
        tp.finish_month(_raw(), "2020-06-30", _curve("2020-07-01"))


def test_exit_rows_carry_last_price_one_month_and_redeem_matured_bonds():
    rows = []
    for m in ["2020-01-31", "2020-02-29", "2020-03-31"]:
        rows.append(tp.finish_month(_raw(cusip_id="AAAAAAAA1", last_trade=pd.Timestamp(m) - pd.Timedelta(days=1)), m,
                                    _curve(m)))
    rows.append(tp.finish_month(_raw(cusip_id="BBBBBBBB1", price_vw=40.0,
                                     last_trade=pd.Timestamp("2020-01-29")), "2020-01-31", _curve("2020-01-31")))
    rows.append(tp.finish_month(_raw(cusip_id="CCCCCCCC1", mtrty_dt=pd.Timestamp("2020-02-15"),
                                     last_trade=pd.Timestamp("2020-01-30")), "2020-01-31", _curve("2020-01-31")))
    panel = tp.add_exit_rows(pd.concat(rows, ignore_index=True))
    b = panel[panel["cusip"] == "BBBBBBBB1"]
    assert len(b) == 2 and b["carried"].tolist() == [False, True]
    ex = b.iloc[1]
    assert ex["date"] == pd.Timestamp("2020-02-29") and ex["price"] == 40.0
    assert ex["accrue_to"] == pd.Timestamp("2020-01-29") and ex["hedge_date"] == pd.Timestamp("2020-01-31")
    c = panel[(panel["cusip"] == "CCCCCCCC1") & panel["carried"]].iloc[0]
    assert c["price"] == 100.0 and c["accrue_to"] == pd.Timestamp("2020-02-15")
    assert not panel[panel["cusip"] == "AAAAAAAA1"]["carried"].any()   # still trading at the panel end


def test_link_prefers_cusip6_then_ticker_and_flags_ambiguity():
    sec = pd.DataFrame({"gvkey": ["001", "002", "003", "003"], "iid": ["01"] * 4,
                        "cusip": ["111111101", "222222101", "333333101", "333333202"], "tic": ["AAA", "BBB", "ZZZ", "ZZ"],
                        "conm": ["a", "b", "c", "c"]})
    sec = pd.concat([sec, pd.DataFrame({"gvkey": ["004"], "iid": ["01"], "cusip": ["222222909"], "tic": ["QQQ"],
                                        "conm": ["d"]})], ignore_index=True)
    bonds = pd.DataFrame({"cusip6": ["111111", "999999", "222222", "777777"], "ticker": ["XXX", "BBB", "BBB", "NONE"]})
    out = tp.link_issuers(bonds, sec).set_index("cusip6")
    assert out.loc["111111", "gvkey"] == "001" and out.loc["111111", "link_source"] == "cusip6"
    assert out.loc["999999", "gvkey"] == "002" and out.loc["999999", "link_source"] == "ticker"
    assert out.loc["222222", "link_ambiguous"]
    assert out.loc["777777", "link_source"] == "none"


def _vintages():
    q = pd.to_datetime(["2019-03-31", "2019-06-30", "2019-09-30", "2019-12-31", "2020-03-31"])
    rows = []
    for i, d in enumerate(q):
        rows.append(dict(gvkey="001", datadate=d, vintage=0, snapshot_available_at=d + pd.Timedelta(days=45),
                         pit_exact=True, oibdp=25.0, debt_current=10.0, debt_long_term=290.0))
    # restatement of Q4 2019 seen later: EBITDA falls to 5
    rows.append(dict(gvkey="001", datadate=q[3], vintage=1, snapshot_available_at=pd.Timestamp("2020-06-01"),
                     pit_exact=True, oibdp=5.0, debt_current=10.0, debt_long_term=290.0))
    # a row without a snapshot date never enters
    rows.append(dict(gvkey="002", datadate=q[4], vintage=0, snapshot_available_at=pd.NaT, pit_exact=False,
                     oibdp=10.0, debt_current=0.0, debt_long_term=50.0))
    return pd.DataFrame(rows)


def test_leverage_as_of_uses_only_versions_known_then():
    v = _vintages()
    a = tp.leverage_as_of(v, "2020-04-30").set_index("gvkey")
    assert a.loc["001", "leverage"] == pytest.approx(300.0 / 100.0)     # Q1 2020 is not known yet: 2019 quarters
    assert a.loc["001", "datadate"] == pd.Timestamp("2019-12-31")
    assert "002" not in a.index
    b = tp.leverage_as_of(v, "2020-06-30").set_index("gvkey")
    assert b.loc["001", "datadate"] == pd.Timestamp("2020-03-31")
    assert b.loc["001", "leverage"] == pytest.approx(300.0 / 80.0)      # restated Q4 now known
    assert (b["available_at"] <= pd.Timestamp("2020-06-30")).all()


def test_leverage_caps_negative_ebitda_and_drops_stale_quarters():
    v = _vintages()
    v["oibdp"] = -5.0
    assert tp.leverage_as_of(v, "2020-06-30").set_index("gvkey").loc["001", "leverage"] == tp.LEV_CAP
    assert tp.leverage_as_of(v, "2021-06-30").empty
