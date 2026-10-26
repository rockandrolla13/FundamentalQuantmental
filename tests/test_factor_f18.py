"""F18 equity-credit discordance: contract, no look-ahead, sign, kappa, trade rule, monthly fallback, edge cases."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from hy.backtest import decision_time
from hy.factors import f18_equity_credit_discordance as f18

AS_OF = pd.Timestamp("2012-06-30")          # a Saturday: the last trade day is Friday 29 June
DAYS = pd.bdate_range("2012-01-02", "2012-06-29")
DAY = pd.Timedelta(1, unit="D")

# last 5-day total stock return, and whether the spread moves against Merton (with the stock) in that window
CASES = {"A": (-0.05, True),    # stock down, spread tighter: D = -1
         "B": (0.05, True),     # stock up, spread wider: D = +1
         "C": (0.05, False),    # stock up, spread tighter (Merton): D = 0
         "E": (0.02, True)}     # discordant but below 3%: D = 0


def _daily(cases=CASES, seed: int = 0):
    """Merton paths: spread = 0.05 - 0.1 (P - 1), so every pair is concordant. A discordant case moves the spread
    the other way in the last 5 days. Two bonds per issuer, 20 bp apart."""
    rng = np.random.default_rng(seed)
    eq, bd = [], []
    for g, (r5, disc) in cases.items():
        ret = rng.normal(0.0, 0.01, len(DAYS))
        ret[-5:] = (1.0 + r5) ** 0.2 - 1.0
        p = np.cumprod(1.0 + ret)
        s = 0.05 - 0.1 * (p - 1.0)
        if disc:
            s[-5:] = s[-6] + np.sign(r5) * 0.001 * np.arange(1, 6)
        eq.append(pd.DataFrame({"gvkey": g, "date": DAYS, "ret": ret}))
        for k in range(2):
            bd.append(pd.DataFrame({"cusip": f"{g}{k}", "date": DAYS, "g_spread": s + 0.002 * k}))
    eq, bd = pd.concat(eq, ignore_index=True), pd.concat(bd, ignore_index=True)
    eq["available_at"] = eq["date"] + DAY
    bd["available_at"] = bd["date"] + DAY
    return eq, bd


def _bond_panel(gvkeys=tuple(CASES), spreads: dict | None = None) -> pd.DataFrame:
    """Month-end rows at as_of and the month before. `spreads` maps gvkey to (previous, as_of) g_spread."""
    rows = []
    for d in (pd.Timestamp("2012-05-31"), AS_OF):
        for g in gvkeys:
            for k in range(2):
                gs = 0.05 if spreads is None else spreads[g][int(d == AS_OF)]
                rows.append({"date": d, "cusip": f"{g}{k}", "gvkey": g, "years": 5.0, "g_spread": gs + 0.002 * k,
                             "price": 95.0, "yield": 0.08, "mod_dur": 4.0, "carried": False,
                             "available_at": d + DAY})
    return pd.DataFrame(rows)


def _equity_monthly(rets: dict) -> pd.DataFrame:
    """13 month ends to as_of. `rets` maps gvkey to the return of the as_of month. Earlier months 1%."""
    ends = pd.date_range(end=AS_OF, periods=13, freq="ME")
    rows = [{"gvkey": g, "datadate": d, "ret": r if d == ends[-1] else 0.01} for g, r in rets.items() for d in ends]
    e = pd.DataFrame(rows)
    e["available_at"] = e["datadate"] + DAY
    return e


def _panels():
    eq, bd = _daily()
    return {"bond_panel": _bond_panel(), "equity_daily": eq, "bond_daily": bd}


def _by_issuer(out: pd.DataFrame) -> pd.DataFrame:
    return out.drop_duplicates("gvkey").set_index("gvkey")


# ---------------------------------------------------------------- contract


def test_meta_and_columns():
    for k in ("rank", "name", "level", "horizon_months", "needs", "spec", "section"):
        assert k in f18.META
    assert f18.META["rank"] == 18 and {"equity_daily", "bond_daily"} <= set(f18.META["needs"])
    out = f18.compute(_panels(), AS_OF)
    assert list(out.columns) == f18.COLUMNS
    assert out["cusip"].is_unique and len(out) == 2 * len(CASES)
    assert (out["date"] == AS_OF).all() and (out["available_at"] == decision_time(AS_OF)).all()
    assert (out["freq_source"] == "daily").all()
    assert out.groupby("gvkey")["score"].nunique().eq(1).all()


# ---------------------------------------------------------------- sign


def test_sign_of_discordant_moves():
    iss = _by_issuer(f18.compute(_panels(), AS_OF))
    assert iss.loc["A", "score"] == -1.0      # stock fell, spread tightened: the spread must widen, underweight
    assert iss.loc["B", "score"] == 1.0       # stock rose, spread widened: the spread must tighten, overweight
    assert iss.loc["C", "score"] == 0.0       # concordant move
    assert iss.loc["E", "score"] == 0.0       # discordant but |r| < 3%
    assert iss.loc["A", "stock_ret"] == pytest.approx(-0.05)
    assert iss.loc["A", "d_spread"] == pytest.approx(-0.005) and iss.loc["A", "n_bonds"] == 2
    assert iss.loc[["A", "B", "E"], "discordant"].eq(1.0).all() and iss.loc["C", "discordant"] == 0.0
    # the trade opened inside the last 5-day move is still open at as_of
    assert iss.loc["A", "open_dir"] == -1.0 and DAYS[-5] <= iss.loc["A", "open_since"] <= DAYS[-1]


def test_kappa_on_merton_path_is_minus_one():
    iss = _by_issuer(f18.compute(_panels(), AS_OF))
    assert iss.loc["C", "kappa"] == pytest.approx(-1.0) and iss.loc["C", "n_pairs"] == 78
    assert iss.loc["C", "kappa_z"] == pytest.approx(np.arctanh(-0.99))
    # a discordant last week raises kappa above -1
    assert iss.loc["A", "kappa"] > -1.0


# ---------------------------------------------------------------- no look-ahead


def test_no_look_ahead():
    p = _panels()
    base = f18.compute(p, AS_OF)
    later = pd.bdate_range("2012-07-02", "2012-07-31")
    eq, bd = p["equity_daily"], p["bond_daily"]
    eq2 = pd.concat([eq, pd.DataFrame({"gvkey": "A", "date": later, "ret": 0.2, "available_at": later + DAY})])
    bd2 = pd.concat([bd, pd.DataFrame({"cusip": "A0", "date": later, "g_spread": 0.5, "available_at": later + DAY}),
                     # a late print for a day before as_of, published after the decision time
                     pd.DataFrame({"cusip": ["A0", "A1"], "date": DAYS[-1], "g_spread": 0.9,
                                   "available_at": AS_OF + pd.Timedelta(10, unit="D")})])
    late_bp = _bond_panel().assign(date=pd.Timestamp("2012-07-31"), available_at=pd.Timestamp("2012-08-01"))
    q = {"bond_panel": pd.concat([p["bond_panel"], late_bp]), "equity_daily": eq2, "bond_daily": bd2}
    pd.testing.assert_frame_equal(f18.compute(q, AS_OF), base)


# ---------------------------------------------------------------- edge cases


def test_missing_panels_give_empty_frame():
    p = _panels()
    for keep in ({"bond_panel"}, {"bond_panel", "equity_daily"}, {"equity_daily", "bond_daily"}):
        out = f18.compute({k: v for k, v in p.items() if k in keep}, AS_OF)
        assert out.empty and list(out.columns) == f18.COLUMNS


def test_monthly_fallback_is_flagged_and_signed():
    spreads = {"A": (0.06, 0.05), "B": (0.05, 0.06), "C": (0.05, 0.06), "E": (0.05, 0.06)}
    eqm = _equity_monthly({"A": -0.08, "B": 0.08, "C": -0.08, "E": 0.05})
    out = f18.compute({"bond_panel": _bond_panel(spreads=spreads), "equity_monthly": eqm}, AS_OF)
    iss = _by_issuer(out)
    assert (iss["freq_source"] == "monthly").all()
    assert iss.loc["A", "score"] == -1.0 and iss.loc["B", "score"] == 1.0
    assert iss.loc["C", "score"] == 0.0           # concordant
    assert iss.loc["E", "score"] == 0.0           # 5% is below the 6.73% monthly threshold
    assert iss.loc["A", "d_spread"] == pytest.approx(-0.01)


def test_sparse_trades_give_nan_not_zero():
    eq, bd = _daily()
    bd = bd[~(bd["cusip"].str[0].eq("A") & (bd["date"] == DAYS[-6]))]
    out = f18.compute({"bond_panel": _bond_panel(), "equity_daily": eq, "bond_daily": bd}, AS_OF)
    iss = _by_issuer(out)
    assert np.isnan(iss.loc["A", "score"]) and iss.loc["A", "n_bonds"] == 0
    assert iss.loc["B", "score"] == 1.0


def test_sparse_daily_issuer_falls_back_to_monthly():
    eq, bd = _daily()
    bd = bd[~(bd["cusip"].str[0].eq("A") & (bd["date"] == DAYS[-6]))]
    spreads = {g: (0.06, 0.05) for g in CASES}
    eqm = _equity_monthly({g: -0.08 for g in CASES})
    out = f18.compute({"bond_panel": _bond_panel(spreads=spreads), "equity_daily": eq, "bond_daily": bd,
                       "equity_monthly": eqm}, AS_OF)
    iss = _by_issuer(out)
    assert iss.loc["A", "freq_source"] == "monthly" and iss.loc["A", "score"] == -1.0
    assert iss.loc["B", "freq_source"] == "daily" and iss.loc["B", "score"] == 1.0


def test_stale_equity_drops_daily_mode():
    eq, bd = _daily()
    eq = eq[~((eq["gvkey"] == "B") & (eq["date"] > pd.Timestamp("2012-06-20")))]
    iss = _by_issuer(f18.compute({"bond_panel": _bond_panel(), "equity_daily": eq, "bond_daily": bd}, AS_OF))
    assert np.isnan(iss.loc["B", "score"]) and pd.isna(iss.loc["B", "freq_source"])
    assert iss.loc["A", "score"] == -1.0


def test_missing_equity_issuer_keeps_bond_rows():
    eq, bd = _daily()
    out = f18.compute({"bond_panel": _bond_panel(), "equity_daily": eq[eq["gvkey"] != "E"], "bond_daily": bd},
                      AS_OF)
    assert len(out) == 2 * len(CASES)
    assert out.loc[out["gvkey"] == "E", "score"].isna().all()


# ---------------------------------------------------------------- formula helpers


def test_discordance_signal_hand_values():
    r = [-0.05, 0.05, 0.05, 0.02, 0.05, np.nan, 0.05]
    ds = [-0.001, 0.002, -0.001, 0.001, 0.0, 0.001, np.nan]
    got = f18.discordance_signal(r, ds)
    np.testing.assert_array_equal(got[:5], [-1.0, 1.0, 0.0, 0.0, 0.0])   # a zero change is not a discrepancy
    assert np.isnan(got[5]) and np.isnan(got[6])
    assert f18.discordance_signal(0.03, 0.001) == 0.0                    # strict: |r| must exceed 3%


def test_issuer_spread_change():
    assert f18.issuer_spread_change([0.05, 0.07, np.nan], [0.04, 0.05, 0.03]) == (pytest.approx(0.015), 2)
    ds, n = f18.issuer_spread_change([np.nan], [0.03])
    assert np.isnan(ds) and n == 0


def test_kappa_source_example_p546():
    # P = 100, 80, 90. CDS 50, 30, 60: pairs [1,2] and [2,3] discordant, [1,3] not: kappa = 4*2/6 - 1 = 1/3.
    k, n = f18.kendall_kappa([100, 80, 90], [50, 30, 60])
    assert k == pytest.approx(1.0 / 3.0) and n == 3
    # CDS 50, 30, 40: arbitrage across every pair, kappa = 4*3/6 - 1 = 1 (less integrated)
    assert f18.kendall_kappa([100, 80, 90], [50, 30, 40])[0] == pytest.approx(1.0)
    # Merton: spread always against the stock
    assert f18.kendall_kappa([1, 2, 3, 4], [4, 3, 2, 1])[0] == pytest.approx(-1.0)


def test_kappa_median_over_bonds_and_min_pairs():
    spreads = np.array([[1.0, np.nan], [2.0, 5.0], [np.nan, 4.0]])
    # pairs: (1,2) bond 1 +1 -> discordant with dP>0; (2,3) bond 2 -1 -> concordant; (1,3) no common bond
    k, n = f18.kendall_kappa([1.0, 2.0, 3.0], spreads, min_pairs=2)
    assert n == 2 and k == pytest.approx(0.0)
    assert np.isnan(f18.kendall_kappa([1.0, 2.0, 3.0], spreads, min_pairs=3)[0])


def test_fisher_z():
    assert f18.fisher_z(0.5) == pytest.approx(0.5 * np.log(3.0))
    assert f18.fisher_z(1.0) == pytest.approx(np.arctanh(0.99))


def test_trade_entries_no_overlap():
    d = pd.to_datetime(["2012-01-03", "2012-01-10", "2012-02-02", "2012-02-03", "2012-03-05"])
    t = f18.trade_entries(d, [1, -1, 0, -1, 1], hold_months=1)
    # 10 Jan is inside the first trade; 3 Feb is on its exit day, so a new trade opens
    assert list(t["entry"]) == [d[0], d[3], d[4]] and list(t["direction"]) == [1, -1, 1]
    assert t["exit"].iloc[0] == pd.Timestamp("2012-02-03")
    assert f18._open_trade(t, pd.Timestamp("2012-02-20")) == (-1.0, d[3])
    od, since = f18._open_trade(t.iloc[:1], pd.Timestamp("2012-02-20"))
    assert od == 0.0 and pd.isna(since)
