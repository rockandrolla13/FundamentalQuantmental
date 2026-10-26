"""Sector fair-spread models (hy.sector.fairspread, hy.sector.drivers): contract, empty frames, no look-ahead, sign
(planted cheap bond), recovered driver signs, the sign rule, Huber robustness, thin-sector fallback, financials,
driver hand checks."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from hy.sector import drivers as dr
from hy.sector import fairspread as fs
from hy.sector.synthetic import make_panels

AS_OF = pd.Timestamp("2015-06-30")
DT = AS_OF + pd.Timedelta(1, unit="D")
LATE = DT + pd.Timedelta(5, unit="D")


@pytest.fixture(scope="module")
def panels():
    return make_panels(AS_OF, sectors={"10": 30, "25": 25, "35": 6}, cheap=["G10_3"], two_bonds=["G10_5"])


@pytest.fixture(scope="module")
def out(panels):
    return fs.compute(panels, AS_OF)


# ---------------------------------------------------------------- 1. contract


def test_meta_and_columns(out):
    for k in ("rank", "name", "level", "horizon_months", "needs", "spec", "section"):
        assert k in fs.META
    assert list(out.columns) == fs.COLS
    assert out["cusip"].is_unique and len(out) == 30 + 25 + 6 + 1
    assert (out["date"] == AS_OF).all() and (out["available_at"] == DT).all()
    assert out["score"].notna().all()
    np.testing.assert_allclose(out["s_fair"], out["g_spread"] * np.exp(-out["resid_log"]), rtol=1e-12)


@pytest.mark.parametrize("drop", ["bond_panel", "gics", "leverage"])
def test_missing_required_panel_gives_empty(panels, drop):
    p = {k: v for k, v in panels.items() if k != drop}
    res = fs.compute(p, AS_OF)
    assert res.empty and list(res.columns) == fs.COLS
    assert fs.compute({}, AS_OF).empty


def test_optional_panels_missing_still_score(panels):
    p = {k: panels[k] for k in ("bond_panel", "gics", "leverage")}
    res = fs.compute(p, AS_OF)
    assert len(res) == 62 and res["score"].notna().all()
    assert res["rclass"].isna().all()
    assert set(res["drivers"]) == {"log_lev"}


# ---------------------------------------------------------------- 2. no look-ahead


def test_no_lookahead(panels, out):
    p = {k: v.copy() for k, v in panels.items()}
    b = p["bond_panel"]
    nxt = AS_OF + pd.offsets.MonthEnd(1)
    future = b[b["date"] == AS_OF].assign(date=nxt, g_spread=0.09, available_at=nxt + pd.Timedelta(1, unit="D"))
    restated = b[b["date"] == AS_OF].assign(g_spread=0.02, available_at=LATE)
    p["bond_panel"] = pd.concat([b, future, restated], ignore_index=True)
    lv = p["leverage"]
    p["leverage"] = pd.concat([lv, lv[lv["date"] == AS_OF].assign(leverage=15.0, available_at=LATE)], ignore_index=True)
    r = p["ratings"]
    p["ratings"] = pd.concat([r, r[r["datadate"] == AS_OF].assign(splticrm="CCC-", available_at=LATE)], ignore_index=True)
    cq = p["compustat_quarterly"]
    p["compustat_quarterly"] = pd.concat([cq, cq.assign(datadate=AS_OF, capx=1e4, available_at=LATE)], ignore_index=True)
    ca = p["compustat_annual"]
    p["compustat_annual"] = pd.concat([ca, ca.assign(datadate=AS_OF, fyear=2015, xrent=1e3, available_at=LATE)],
                                      ignore_index=True)
    ae = p["annual_ebitda"]
    p["annual_ebitda"] = pd.concat([ae, ae.assign(datadate=AS_OF, fyear=2015, oibdp=-50.0, available_at=LATE)],
                                   ignore_index=True)
    g = p["gics"]
    p["gics"] = pd.concat([g, g.assign(gsector="40", indfrom=AS_OF - pd.Timedelta(10, unit="D"), available_at=LATE)],
                          ignore_index=True)
    pd.testing.assert_frame_equal(fs.compute(p, AS_OF), out)


# ---------------------------------------------------------------- 3. sign and fit


def test_planted_cheap_bond_is_cheapest_in_sector(out):
    energy = out[out["group"] == "energy"].set_index("cusip")
    assert energy["score"].idxmax() == "C10_3_0"
    assert energy.loc["C10_3_0", "score"] > 3.0
    assert energy.loc["C10_3_0", "resid_log"] == pytest.approx(np.log(1.6), abs=0.1)


def test_sector_model_recovers_driver_signs(out):
    m = out.attrs["models"]["energy"]
    assert m["model"] == "sector"
    assert m["coef"]["log_lev"] > 0 and m["coef"]["capex_int"] > 0
    for d in m["drivers"]:
        assert dr.SIGNS[d] * m["coef"][d] >= 0


def test_sign_rule_drops_wrong_sign_driver(rng):
    n = 200
    x1, x2 = rng.standard_normal(n), rng.standard_normal(n)
    y = 0.5 * x1 + 0.3 * x2 + 0.01 * rng.standard_normal(n)       # coverage enters with a positive (wrong) sign
    X = pd.DataFrame({"const": 1.0, "log_lev": x1, "coverage": x2})
    b, kept = fs.signed_fit(y, X, dr.SIGNS)
    assert kept == ["log_lev"] and "coverage" not in b.index
    assert b["log_lev"] == pytest.approx(0.5, abs=0.05)


def test_huber_resists_an_outlier(rng):
    x = np.linspace(0, 1, 60)
    y = 1.0 + 2.0 * x + 0.01 * rng.standard_normal(60)
    y[5] += 5.0
    X = np.column_stack([np.ones(60), x])
    b_ols, *_ = np.linalg.lstsq(X, y, rcond=None)
    b_h = fs.huber_fit(y, X)
    assert abs(b_h[1] - 2.0) < abs(b_ols[1] - 2.0)
    assert b_h[1] == pytest.approx(2.0, abs=0.05)


def test_constant_driver_is_not_used(out):
    # synthetic gross margin and debt wall are the same for every issuer: no information, no column
    assert "gross_margin" not in out.loc[out["group"] == "consumer_disc", "drivers"].iloc[0]
    assert "mat_wall" not in out.loc[out["group"] == "consumer_disc", "drivers"].iloc[0]


# ---------------------------------------------------------------- 4. fallback and universe


def test_thin_sector_uses_pooled_model(out, panels):
    assert (out.loc[out["group"] == "health_care", "model"] == "pooled").all()
    assert (out.loc[out["group"] == "energy", "model"] == "sector").all()
    assert set(out.loc[out["group"] == "health_care", "drivers"]) == {",".join(
        out.attrs["models"]["health_care"]["drivers"])}
    pooled_all = fs.compute(panels, AS_OF, min_issuers=1000)
    assert (pooled_all["model"] == "pooled").all()
    assert "sec_25" in pooled_all.attrs["models"]["energy"]["coef"]       # sector effects eta_sector


def test_pooled_fallback_fails_cleanly_with_too_few_bonds():
    p = make_panels(AS_OF, sectors={"10": 4})
    res = fs.compute(p, AS_OF)
    assert len(res) == 4 and (res["model"] == "none").all() and res["score"].isna().all()


def test_financials_are_not_scored():
    p = make_panels(AS_OF, sectors={"10": 20, "40": 20})
    res = fs.compute(p, AS_OF)
    assert set(res["gsector"]) == {"10"}


def test_lease_leverage_alternate_without_rent(panels):
    p = dict(panels)
    p["compustat_annual"] = panels["compustat_annual"].drop(columns="xrent")
    res = fs.compute(p, AS_OF)
    assert res.loc[res["group"] == "consumer_disc", "drivers"].iloc[0].startswith("log_lev")
    assert "log_lev_lease" not in res.loc[res["group"] == "consumer_disc", "drivers"].iloc[0]
    full = fs.compute(panels, AS_OF)
    assert "log_lev_lease" in full.loc[full["group"] == "consumer_disc", "drivers"].iloc[0]


# ---------------------------------------------------------------- 5. drivers


def test_capped_log_leverage():
    lev = pd.Series([4.0, -3.0, 50.0, 0.01, np.nan])
    e = pd.Series([10.0, -1.0, 10.0, 10.0, np.nan])
    out = dr.capped_log_leverage(lev, e)
    np.testing.assert_allclose(out[:4], np.log([4.0, dr.LEV_CAP, dr.LEV_CAP, 0.1]))
    assert np.isnan(out.iloc[4])


def test_issuer_drivers_hand_check(panels):
    d = dr.issuer_drivers(panels, AS_OF)
    lv = panels["leverage"].query("date == @AS_OF").set_index("gvkey")
    ca = panels["compustat_annual"].set_index("gvkey")
    g = "G25_4"
    assert d.loc[g, "log_lev"] == pytest.approx(np.log(lv.loc[g, "leverage"]))
    assert d.loc[g, "capex_int"] == pytest.approx(ca.loc[g, "capx"] / ca.loc[g, "sale"])
    assert d.loc[g, "mat_wall"] == pytest.approx(0.15)
    assert d.loc[g, "gross_margin"] == pytest.approx(0.4)
    assert d.loc[g, "coverage"] == pytest.approx(lv.loc[g, "ltm_ebitda"] / ca.loc[g, "xint"])
    assert d.loc[g, "fcf_debt"] == pytest.approx((0.8 * 100 - ca.loc[g, "capx"]) / lv.loc[g, "debt"])
    rent = ca.loc[g, "xrent"]
    lease = (lv.loc[g, "debt"] + 8 * rent) / (lv.loc[g, "ltm_ebitda"] + rent)
    assert d.loc[g, "log_lev_lease"] == pytest.approx(np.log(lease))
    assert np.isfinite(d.loc[g, "ebitda_cyc"]) and np.isfinite(d.loc[g, "margin_trend"])
    assert list(d.columns) == list(dr.DRIVER_NAMES)


def test_every_group_driver_has_a_sign():
    for names in list(dr.SECTOR_DRIVERS.values()) + [dr.POOLED_DRIVERS]:
        for n in names:
            assert n in dr.SIGNS and n in dr.DRIVER_NAMES
