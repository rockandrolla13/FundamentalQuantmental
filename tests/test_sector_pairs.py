"""Within-sector long-short pairs (hy.sector.pairs): sign (planted cheap bond is the long), DTS-neutral hedge, match
rules, one issuer per leg, convergence, carry and JTD hand checks, pooled AR(1), legs contract, empty frames, no
look-ahead."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from hy.sector import pairs as pr
from hy.sector.synthetic import make_panels

AS_OF = pd.Timestamp("2015-06-30")
DT = AS_OF + pd.Timedelta(1, unit="D")
LATE = DT + pd.Timedelta(5, unit="D")


@pytest.fixture(scope="module")
def panels():
    return make_panels(AS_OF, sectors={"10": 30, "25": 25}, cheap=["G10_3", "G25_7"], two_bonds=["G10_3"],
                       years={"G25_7": 5.0})


@pytest.fixture(scope="module")
def table(panels):
    return pr.pairs(panels, AS_OF)


# ---------------------------------------------------------------- 1. sign and structure


def test_planted_cheap_bond_is_the_long(table):
    for sec, g in (("10", "G10_3"), ("25", "G25_7")):
        first = table[table["gsector"] == sec].iloc[0]
        assert first["long_gvkey"] == g and first["pair_id"] == f"{sec}-1"
    assert not table["short_gvkey"].isin(["G10_3", "G25_7"]).any()


def test_long_without_a_dts_match_is_skipped():
    # random maturity: the planted bond's DTS (0.70) is more than 1.5 times every rich bond's DTS
    p = make_panels(AS_OF, sectors={"10": 30, "25": 25}, cheap=["G10_3", "G25_7"], two_bonds=["G10_3"])
    t = pr.pairs(p, AS_OF)
    assert "G25_7" not in set(t["long_gvkey"]) and len(t[t["gsector"] == "25"]) > 0
    loose = pr.select_pairs(pr._scored(p, AS_OF, None).query("gsector == '25'"), dts_tol=10.0)
    assert any(pr._scored(p, AS_OF, None).loc[i, "gvkey"] == "G25_7" for i, _ in loose)


def test_pairs_are_dts_neutral(table, panels):
    assert len(table) == 2 * pr.N_PAIRS
    np.testing.assert_allclose(table["net_dts"], 0.0, atol=1e-12)
    np.testing.assert_allclose(table["hedge_ratio"], table["dts_long"] / table["dts_short"])
    legs = pr.compute(panels, AS_OF)
    dts = legs.merge(table[["long_cusip", "dts_long"]].rename(columns={"long_cusip": "cusip", "dts_long": "d"}),
                     on="cusip", how="left")
    dts["d"] = dts["d"].fillna(dts["cusip"].map(table.set_index("short_cusip")["dts_short"]))
    np.testing.assert_allclose((dts["weight"] * dts["d"]).groupby(dts["pair_id"]).sum(), 0.0, atol=1e-12)


def test_selection_rules(table):
    assert (table["long_score"] > 0).all() and (table["short_score"] < 0).all()
    np.testing.assert_allclose(table["score"], table["long_score"] - table["short_score"])
    assert (np.abs(np.log(table["dts_long"] / table["dts_short"])) <= np.log1p(pr.DTS_TOL) + 1e-12).all()
    for _, g in table.groupby("gsector"):
        iss = list(g["long_gvkey"]) + list(g["short_gvkey"])
        assert len(iss) == len(set(iss))                      # one issuer per leg, no reuse
        assert g["long_score"].is_monotonic_decreasing        # cheapest long first


def test_bucket_mode_matches_rating_and_maturity(panels):
    t = pr.pairs(panels, AS_OF, mode="bucket", n_pairs=5)
    from hy.sector.common import universe
    u = universe(panels, AS_OF).set_index("cusip")
    assert len(t) > 0
    assert (u.loc[t["long_cusip"], "rclass"].to_numpy() == u.loc[t["short_cusip"], "rclass"].to_numpy()).all()
    assert (u.loc[t["long_cusip"], "mat_bucket"].to_numpy() == u.loc[t["short_cusip"], "mat_bucket"].to_numpy()).all()
    np.testing.assert_allclose(t["net_dts"], 0.0, atol=1e-12)
    with pytest.raises(ValueError):
        pr.pairs(panels, AS_OF, mode="dv01")


def test_scores_override_picks_the_named_long(panels):
    from hy.sector.common import universe
    u = universe(panels, AS_OF)
    sc = u[["cusip"]].assign(score=np.linspace(-1, 1, len(u)))
    target = u.loc[u["gsector"] == "25", "cusip"].iloc[0]
    sc.loc[sc["cusip"] == target, "score"] = 5.0
    t = pr.pairs(panels, AS_OF, scores=sc)
    assert t.loc[t["gsector"] == "25", "long_cusip"].iloc[0] == target
    assert t["fair_long"].notna().all()                      # fair spread still from the sector model


# ---------------------------------------------------------------- 2. hand checks


def _leg(s, d, f, price, rclass):
    return pd.Series({"g_spread": s, "mod_dur": d, "s_fair": f, "price": price, "rclass": rclass, "dts": s * d})


def test_pair_metrics_hand_check():
    L, S = _leg(0.06, 4.0, 0.05, 95.0, "B"), _leg(0.04, 5.0, 0.045, 101.0, "BB")
    rho, H = 0.8, 6
    m = pr.pair_metrics(L, S, rho, H)
    h = 0.06 * 4.0 / (0.04 * 5.0)
    q = 1 - rho ** H
    assert m["hedge_ratio"] == pytest.approx(h)
    assert m["net_dts"] == pytest.approx(0.0, abs=1e-12)
    assert m["net_dur"] == pytest.approx(4.0 - h * 5.0)
    assert m["exp_conv"] == pytest.approx(4.0 * q * 0.01 - h * 5.0 * q * (-0.005))
    assert m["carry"] == pytest.approx(0.5 * (0.06 - h * 0.04))
    r_l, r_s = 0.70 - 0.03 * 15, 0.70 - 0.03 * 12            # F06 class middle notches: B 15, BB 12
    assert m["rec_long"] == pytest.approx(r_l) and m["rec_short"] == pytest.approx(r_s)
    j_l, j_s = 1 - 100 * r_l / 95.0, h * (1 - 100 * r_s / 101.0)
    assert m["jtd_loss_long"] == pytest.approx(j_l) and m["jtd_gain_short"] == pytest.approx(j_s)
    assert m["jtd_ratio"] == pytest.approx(j_l / j_s)
    assert m["jtd_ok"] == (j_l / j_s <= pr.JTD_MAX)
    assert m["hedge_jtd"] == pytest.approx(j_l / (1 - 100 * r_s / 101.0))


def test_jtd_check_flags_an_asymmetric_pair():
    L, S = _leg(0.09, 1.5, 0.07, 95.0, "CCC"), _leg(0.03, 6.0, 0.035, 104.0, "BB")
    m = pr.pair_metrics(L, S, 0.8, 6)
    assert m["jtd_ratio"] > pr.JTD_MAX and not m["jtd_ok"]
    assert pr.class_recovery(None) == pytest.approx(0.40)


def test_drop_jtd_fail(panels, table):
    kept = pr.pairs(panels, AS_OF, drop_jtd_fail=True)
    assert kept["jtd_ok"].all() and len(kept) == table["jtd_ok"].sum()


def test_rho_from_half_life():
    assert pr.rho_from_half_life(3.0) ** 3 == pytest.approx(0.5)
    assert pr.rho_from_half_life(0.0) == 0.0


def test_pooled_rho_from_history(rng, panels):
    months = pd.date_range(end=AS_OF - pd.offsets.MonthEnd(1), periods=60, freq="ME")
    rows = []
    for c in ["X1", "X2", "X3"]:
        e = 0.0
        for m in months:
            e = 0.8 * e + 0.05 * rng.standard_normal()
            rows.append({"date": m, "cusip": c, "resid_log": e, "available_at": m + pd.Timedelta(1, unit="D")})
    hist = pd.DataFrame(rows)
    rho = pr.pooled_rho(hist, ["X1", "X2", "X3"], DT)
    assert rho == pytest.approx(0.8, abs=0.1)
    noisy = pd.concat([hist, hist.assign(resid_log=rng.standard_normal(len(hist)), available_at=LATE)])
    assert pr.pooled_rho(noisy, ["X1", "X2", "X3"], DT) == pytest.approx(rho)
    assert np.isnan(pr.pooled_rho(hist, ["X1"], DT, min_pairs=1000))
    # in the pair run, a sector's history sets rho
    from hy.sector.common import universe
    cus = universe(panels, AS_OF).query("gsector == '10'")["cusip"]
    h10 = hist.assign(cusip=hist["cusip"].map(dict(zip(["X1", "X2", "X3"], cus[:3]))))
    t = pr.pairs({**panels, "residual_history": h10}, AS_OF)
    assert t.loc[t["gsector"] == "10", "rho"].iloc[0] == pytest.approx(rho)
    assert t.loc[t["gsector"] == "25", "rho"].iloc[0] == pytest.approx(pr.rho_from_half_life(pr.HALF_LIFE))


# ---------------------------------------------------------------- 3. contract, empty, no look-ahead


def test_meta_and_legs(panels, table):
    for k in ("rank", "name", "level", "horizon_months", "needs", "spec", "section"):
        assert k in pr.META
    legs = pr.compute(panels, AS_OF)
    assert list(legs.columns) == pr.LEG_COLS and list(table.columns) == pr.PAIR_COLS
    assert len(legs) == 2 * len(table)
    assert (legs["date"] == AS_OF).all() and (legs["available_at"] == DT).all()
    lo, sh = legs[legs["leg"] == "long"], legs[legs["leg"] == "short"]
    assert (lo["weight"] == 1.0).all() and (sh["weight"] < 0).all()
    assert (lo["score"] > 0).all() and (sh["score"] < 0).all()


@pytest.mark.parametrize("drop", ["bond_panel", "gics", "leverage"])
def test_missing_panels_give_empty(panels, drop):
    p = {k: v for k, v in panels.items() if k != drop}
    assert pr.pairs(p, AS_OF).empty and list(pr.pairs(p, AS_OF).columns) == pr.PAIR_COLS
    legs = pr.compute(p, AS_OF)
    assert legs.empty and list(legs.columns) == pr.LEG_COLS


def test_no_lookahead(panels, table):
    p = {k: v.copy() for k, v in panels.items()}
    b = p["bond_panel"]
    nxt = AS_OF + pd.offsets.MonthEnd(1)
    p["bond_panel"] = pd.concat([b, b[b["date"] == AS_OF].assign(g_spread=0.02, available_at=LATE),
                                 b[b["date"] == AS_OF].assign(date=nxt, available_at=nxt + pd.Timedelta(1, unit="D"))],
                                ignore_index=True)
    lv = p["leverage"]
    p["leverage"] = pd.concat([lv, lv.assign(leverage=1.0, available_at=LATE)], ignore_index=True)
    r = p["ratings"]
    p["ratings"] = pd.concat([r, r.assign(splticrm="BB+", available_at=LATE)], ignore_index=True)
    pd.testing.assert_frame_equal(pr.pairs(p, AS_OF), table)
