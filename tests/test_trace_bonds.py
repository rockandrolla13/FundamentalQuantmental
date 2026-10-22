import numpy as np
import pandas as pd
import pytest

from hy.sources import trace_bonds as tb
from hy.sources import treasury as tr


class StubWrds:
    """Return canned frames by matching table names in the SQL text."""

    def __init__(self, master=None, quotes=None, bench=None):
        self.master, self.quotes, self.bench, self.sql = master, quotes, bench, []

    def raw_sql(self, sql):
        self.sql.append(sql)
        if tb.MASTER_TABLE in sql and "trace.trace " in sql:
            return self.bench.copy()
        if tb.MASTER_TABLE in sql:
            return self.master.copy()
        return self.quotes.copy()


def _master():
    base = dict(company_symbol="CRWV", issuer_nm="COREWEAVE INC", cpn_type_cd="FXPV", ind_144a="Y", grade="H")
    rows = [
        # old and current version of a senior note
        dict(cusip_id="21873SAB4", scrty_ds="Senior Unsecured Corporate Debt Security", debt_type_cd="S-CBND",
             cpn_rt="9.2500000", mtrty_dt="2030-06-01", cnvrb_fl="N", stdt="2025-05-21", enddt="2025-05-21"),
        dict(cusip_id="21873SAB4", scrty_ds="Senior Unsecured Note", debt_type_cd="S-NT",
             cpn_rt="9.2500000", mtrty_dt="2030-06-01", cnvrb_fl="N", stdt="2025-05-22", enddt="2026-09-17"),
        # convertible: current version is S-BND but the flag says convertible
        dict(cusip_id="21873SAD0", scrty_ds="Senior Unsecured Convertible Debt Security", debt_type_cd="S-VBND",
             cpn_rt="1.75", mtrty_dt="2031-12-01", cnvrb_fl="Y", stdt="2025-12-09", enddt="2025-12-09"),
        dict(cusip_id="21873SAD0", scrty_ds="Senior Unsecured Bond", debt_type_cd="S-BND",
             cpn_rt="1.75", mtrty_dt="2031-12-01", cnvrb_fl="Y", stdt="2025-12-10", enddt="2026-09-17"),
        dict(cusip_id="21873SZZ9", scrty_ds="Senior Secured Note", debt_type_cd="SSC-NT",
             cpn_rt="7.0", mtrty_dt="2029-01-15", cnvrb_fl="N", stdt="2025-01-01", enddt="2026-09-17"),
    ]
    return pd.DataFrame([{**base, **r} for r in rows])


def test_bond_master_picks_current_version_and_flags(tmp_path):
    con = StubWrds(master=_master())
    m = tb.bond_master(con, ["crwv"], cache_root=tmp_path).set_index("cusip")
    assert len(m) == 3
    assert m.loc["21873SAB4", "debt_type"] == "S-NT"
    assert m.loc["21873SAB4", "coupon"] == pytest.approx(0.0925)
    assert m.loc["21873SAB4", "seniority"] == "senior_unsecured"
    assert m.loc["21873SAD0", "is_convertible"] and m.loc["21873SAD0", "seniority"] == "other"
    assert m.loc["21873SZZ9", "seniority"] == "secured"
    assert m["is_144a"].all() and m["fixed"].all()
    assert m.loc["21873SAB4", "maturity"] == pd.Timestamp("2030-06-01")
    assert "'CRWV'" in con.sql[0]
    tb.bond_master(con, ["CRWV"], cache_root=tmp_path)
    assert len(con.sql) == 1  # served from cache


def test_seniority_handles_missing_codes():
    assert tb.seniority(pd.NA, None, False) == "other"
    assert tb.seniority("1LN-NT", "First Lien Note", False) == "secured"


def test_inputs_are_validated_before_sql():
    con = StubWrds(master=_master())
    with pytest.raises(ValueError):
        tb.bond_master(con, ["CRWV'; drop table x; --"])
    with pytest.raises(ValueError):
        tb.bond_quotes(con, ["21873SAB4' or 1=1"], "2026-09-01", "2026-09-17")
    assert con.sql == []


@pytest.mark.parametrize("text, par", [("1MM+", 1e6), ("5MM+", 5e6), ("250000", 250000.0), ("250000.00", 250000.0),
                                       (" 1mm+ ", 1e6), ("abc", np.nan), (None, np.nan)])
def test_parse_volume(text, par):
    out = tb.parse_volume(text)
    assert (np.isnan(out) and np.isnan(par)) or out == par


def test_volume_sql_has_no_percent_sign():
    assert "%" not in tb.VOLUME_SQL and "%" not in tb._trades_ctes("t.cusip_id in ('21873SAB4')") + tb._live_trades_sql()


def _trades():
    d = "2026-09-15"
    rows = [
        # (status, seq, orig_seq, vol, yield pct, price)
        ("M", 1, None, "1MM+", 10.0, 95.0),
        ("M", 2, None, "250000.00", 12.0, 93.0),
        ("M", 3, None, "50000.00", 20.0, 80.0),  # retail size: dropped
        ("M", 4, None, "5MM+", 99.0, 50.0),  # cancelled by seq 5
        ("N", 5, 4, "5MM+", 99.0, 50.0),
        ("M", 6, None, "500000", 50.0, 70.0),  # corrected by seq 7
        ("O", 7, 6, "500000", 11.0, 94.0),
        ("M", 8, None, "1MM+", None, 94.0),  # NULL yield: dropped
    ]
    return pd.DataFrame([dict(cusip_id="21873SAB4", trd_exctn_dt=d, trc_st=s, msg_seq_nb=q, orig_msg_seq_nb=o,
                              ascii_rptd_vol_tx=v, yld_pt=y, rptd_pr=p, yld_sign_cd=None) for s, q, o, v, y, p in rows])


def test_clean_and_volume_weighted_daily_math():
    day = tb.aggregate_daily(tb.clean_trades(_trades())).iloc[0]
    par = np.array([1e6, 250e3, 500e3])
    assert day["n_trades"] == 3
    assert day["par_volume"] == pytest.approx(par.sum())
    assert day["yield_vw"] == pytest.approx((par @ np.array([10.0, 12.0, 11.0])) / par.sum() / 100)
    assert day["price_vw"] == pytest.approx((par @ np.array([95.0, 93.0, 94.0])) / par.sum())


def _daily(cusip, dates, yields, prices, pars):
    return pd.DataFrame({"cusip_id": cusip, "trd_exctn_dt": dates, "n_trades": 2, "par_volume": pars,
                         "yield_vw_pct": yields, "price_vw": prices})


def test_bond_quotes_queries_both_tables_and_converts_units(tmp_path):
    con = StubWrds(quotes=_daily("21873SAB4", ["2026-09-15"], [11.5], [93.0], [2e6]))
    q = tb.bond_quotes(con, ["21873SAB4"], "2026-08-15", "2026-09-17", cache_root=tmp_path)
    assert q.loc[0, "yield_vw"] == pytest.approx(0.115)
    sql = con.sql[0]
    assert "trace.trace t" in sql and "trace.trace_btds144a t" in sql
    assert "par >= 100000" in sql and "'2026-08-15'" in sql
    tb.bond_quotes(con, ["21873SAB4"], "2026-08-15", "2026-09-17", cache_root=tmp_path)
    assert len(con.sql) == 1


def test_latest_snapshot_window_and_available_at():
    q = pd.concat([
        _daily("A00000001", ["2026-09-01", "2026-09-08", "2026-09-17"], [20.0, 10.0, 12.0], [90.0, 95.0, 93.0], [5e6, 1e6, 3e6]),
        _daily("B00000002", ["2026-09-10"], [8.0], [101.0], [1e6]),
    ])
    snap = tb.latest_snapshot(tb._finish_daily(q), window_days=10).set_index("cusip")
    a = snap.loc["A00000001"]
    assert a["n_days"] == 2  # 09-01 is outside the 10 days that end on 09-17
    assert a["yield"] == pytest.approx((1e6 * 0.10 + 3e6 * 0.12) / 4e6)
    assert a["as_of"] == pd.Timestamp("2026-09-17")
    assert a["available_at"] == pd.Timestamp("2026-09-18")
    assert snap.loc["B00000002", "as_of"] == pd.Timestamp("2026-09-10")


def _curve():
    row = pd.Series({t: 0.04 for t in tr.TENOR_COLUMNS})
    row[5.0], row[10.0] = 0.035, 0.045
    row["available_at"] = pd.Timestamp("2026-09-18")
    row.name = pd.Timestamp("2026-09-17")
    return row


def test_g_spread_arithmetic_and_no_look_ahead():
    c = _curve()
    as_of = pd.Timestamp("2026-09-17")
    mat = as_of + pd.Timedelta(round(7.5 * tb.DAYS_PER_YEAR), unit="D")
    assert tb.g_spread(0.09, mat, as_of, c) == pytest.approx(0.09 - (0.04 + 0.005 / 6), abs=1e-5)  # 7.5y: 1/6 of 7y->10y
    out = tb.g_spread([0.08, 0.10], [as_of + pd.Timedelta(round(5 * 365.25), unit="D")] * 2, [as_of] * 2, c)
    assert out == pytest.approx([0.045, 0.065], abs=1e-5)
    with pytest.raises(ValueError):
        tb.g_spread(0.09, mat, "2026-09-16", c)


def test_benchmark_by_bucket_medians_and_distress_filter():
    as_of = pd.Timestamp("2026-09-17")
    yrs = [2.0, 2.0, 2.0, 2.0, 4.0, 2.0]
    df = pd.DataFrame({
        "cusip": [f"X0000000{i}" for i in range(6)],
        "maturity": [as_of + pd.Timedelta(round(y * tb.DAYS_PER_YEAR), unit="D") for y in yrs],
        "yield": [0.06, 0.07, 0.08, 0.20, 0.30, -0.01],
        "price": [100.0, 99.0, 98.0, 70.0, 85.0, 100.0],  # 4th distressed; 5th yield above 25%; 6th negative yield
        "as_of": as_of, "available_at": as_of + pd.Timedelta(1, unit="D"),
    })
    out = tb.benchmark_by_bucket(df, _curve()).set_index("bucket")
    assert out.loc["1-3y", "count"] == 3
    assert out.loc["1-3y", "median"] == pytest.approx(0.07 - 0.04)
    assert out.loc["1-3y", "iqr"] == pytest.approx(0.01)
    assert out.loc["3-5y", "count"] == 0 and np.isnan(out.loc["3-5y", "median"])
    assert (out["available_at"] == pd.Timestamp("2026-09-18")).all()


def test_hy_benchmark_sql_and_shape():
    raw = pd.DataFrame({"cusip_id": ["21873SAB4"], "mtrty_dt": ["2030-06-01"], "debt_type_cd": ["S-NT"],
                        "company_symbol": ["CRWV"], "last_trade": ["2026-09-16"], "n_trades": [40],
                        "par_volume": [5e7], "yield_vw_pct": [11.5], "price_vw": [93.0]})
    con = StubWrds(bench=raw)
    b = tb.hy_benchmark(con, "2026-09-17", window_days=10)
    sql = con.sql[0]
    assert "grade = 'H'" in sql and "cnvrb_fl = 'N'" in sql and "'FXPV'" in sql
    assert "between '2026-09-08' and '2026-09-17'" in sql
    assert b.loc[0, "yield"] == pytest.approx(0.115)
    assert b.loc[0, "available_at"] == pd.Timestamp("2026-09-17")
