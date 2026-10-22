"""Tests for the path-aware event matrix and the per-path output rows (methodology Sections 9.2, 10).

Synthetic data only.
"""

from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from hy import events as ev
from hy import outputs as out
from hy.inputs import LookAheadError

PATHS = ("soft_landing", "recession", "higher_for_longer")
P_PATH = {"soft_landing": 0.5, "recession": 0.3, "higher_for_longer": 0.2}
W_BY_PATH = {
    "soft_landing": {"base": 0.60, "down_moderate": 0.15, "down_severe": 0.05, "upside": 0.20},
    "recession": {"base": 0.35, "down_moderate": 0.35, "down_severe": 0.20, "upside": 0.10},
    "higher_for_longer": {"base": 0.50, "down_moderate": 0.25, "down_severe": 0.10, "upside": 0.15},
}
DY = {"soft_landing": (0.002, 0.000), "recession": (-0.010, -0.005), "higher_for_longer": (0.000, 0.008)}


def _features():
    df = pd.DataFrame(
        {
            "macro_path": list(PATHS) + ["weighted"],
            "p_breach_4": [0.05, 0.40, 0.15, 0.164],
            "p_refi_4": [0.30, 0.60, 0.50, 0.43],
            "p_refi_access": [0.90, 0.30, 0.60, 0.66],
        }
    )
    return df


def _macro_paths():
    q = np.zeros(ev.N_QUARTERS)
    return [
        ev.MacroPath(
            m, P_PATH[m], q + 0.04, q + 0.042, q + 0.05, q + 0.02, q + 50, q + 0.04, q + 0.03,
            extra={"dy_growth": q + DY[m][0], "dy_policy": q + DY[m][1]},
        )
        for m in PATHS
    ]


POSITION = {
    "position_id": "P1", "cusip": "SYN000001", "price": 95.0, "mod_duration": 4.0, "spread_duration": 4.0,
    "beta_g": -0.5, "beta_p": 0.4, "carry_h": 1.5, "recovery_adj": {"soft_landing": 0.5, "recession": 0.35, "higher_for_longer": 0.45},
}


def _event(et):
    return {"event_id": "E1", "event_type": et, "event_date": datetime(2026, 11, 5), "date_confirmed": True}


def _pnl_fn(o, m):
    bad = {"miss": 0.01, "waiver": 0.005, "acceleration": 0.03, "extended": 0.01, "distressed_exchange": 0.03}
    good = {"beat": -0.003}
    return {"ds_idio": bad.get(o, 0.0) + good.get(o, 0.0), "features_delta": [1.0 if o in bad else 0.0]}


def _em(et=ev.EventType.EARNINGS, **kw):
    args = dict(
        date=datetime(2026, 10, 21), available_at=datetime(2026, 10, 20), position=POSITION, event=_event(et),
        path_probs=P_PATH, w_by_path=W_BY_PATH, path_features=_features(), pnl_fn=_pnl_fn, paths=_macro_paths(),
    )
    args.update(kw)
    return ev.event_matrix_from_paths(**args)


# --- P(o | e, m) ----------------------------------------------------------


@pytest.mark.parametrize("et", [ev.EventType.EARNINGS, ev.EventType.COVENANT_TEST, ev.EventType.MATURITY_REFI])
def test_outcome_probs_rows_sum_to_one(et):
    p = ev.outcome_probs_from_cases(et, W_BY_PATH, _features())
    assert list(p.index) == list(PATHS)  # the weighted row is not a path
    assert list(p.columns) == list(ev.OUTCOMES[et])
    np.testing.assert_allclose(p.sum(axis=1), 1.0, atol=1e-12)
    assert (p.to_numpy() >= 0).all()


def test_earnings_rule_uses_case_weights():
    p = ev.outcome_probs_from_cases("earnings", W_BY_PATH)
    assert p.loc["recession", "miss"] == pytest.approx(0.55)  # down_moderate + down_severe
    assert p.loc["recession", "beat"] == pytest.approx(0.10)  # upside
    assert p.loc["recession", "in_line"] == pytest.approx(0.35)
    assert p.loc["recession", "miss"] > p.loc["soft_landing", "miss"]


def test_covenant_rule_and_waiver_share():
    p = ev.outcome_probs_from_cases(ev.EventType.COVENANT_TEST, W_BY_PATH, _features())
    assert p.loc["recession", "pass"] == pytest.approx(0.60)
    assert p.loc["recession", "waiver"] == pytest.approx(0.40 * 0.9)
    assert p.loc["recession", "acceleration"] == pytest.approx(0.40 * 0.1)


def test_failed_refi_probability_formula():
    p = ev.outcome_probs_from_cases(ev.EventType.MATURITY_REFI, W_BY_PATH, _features())
    f = _features().set_index("macro_path")
    for m in PATHS:
        fail = f.loc[m, "p_refi_4"] * (1 - f.loc[m, "p_refi_access"])
        assert 1 - p.loc[m, "refinanced"] == pytest.approx(fail)
        assert ev.failed_refi_probability(f.loc[m, "p_refi_4"], f.loc[m, "p_refi_access"]) == pytest.approx(fail)
    assert ev.failed_refi_probability(0.6, 0.3) == pytest.approx(0.42)
    # The refi_access name serves when p_refi_access is absent.
    alt = _features().rename(columns={"p_refi_access": "refi_access"})
    pd.testing.assert_frame_equal(ev.outcome_probs_from_cases("maturity_refi", W_BY_PATH, alt), p)


def test_outcome_probs_reject_bad_case_weights_and_missing_features():
    bad = {**W_BY_PATH, "recession": {"base": 0.5, "down_moderate": 0.3}}
    with pytest.raises(ValueError):
        ev.outcome_probs_from_cases("earnings", bad)
    with pytest.raises(KeyError):
        ev.outcome_probs_from_cases("covenant_test", W_BY_PATH, _features().iloc[1:])
    with pytest.raises(NotImplementedError):
        ev.outcome_probs_from_cases("litigation", W_BY_PATH, _features())


# --- event matrix ---------------------------------------------------------


@pytest.mark.parametrize("et", [ev.EventType.EARNINGS, ev.EventType.COVENANT_TEST, ev.EventType.MATURITY_REFI])
def test_event_matrix_p_path_sums_to_one(et):
    em = _em(et)
    assert len(em) == len(PATHS) * len(ev.OUTCOMES[et])
    np.testing.assert_allclose(em.groupby("outcome")["p_path"].sum(), 1.0)
    np.testing.assert_allclose(em.groupby("macro_path")["p_outcome_given_path"].sum(), 1.0)
    assert {"dy_growth", "dy_policy", "ds_sys"} <= set(em.columns)
    assert out.validate_frame(em, "event_matrix") is em


def test_event_matrix_rejects_p_path_leak():
    with pytest.raises(ValueError, match="p_path"):
        _em(path_probs={**P_PATH, "recession": 0.25})
    with pytest.raises(ValueError, match="path names"):
        _em(path_probs={"soft_landing": 0.5, "recession": 0.5})
    # The weighted entry is ignored, not counted.
    _em(path_probs={**P_PATH, "weighted": 1.0})


def test_event_matrix_pnl_matches_section_9_2():
    em = _em().set_index(["macro_path", "outcome"])
    dyg, dyp = DY["recession"]
    ds_sys = -0.5 * dyg + 0.4 * dyp
    exp = -4.0 * (dyg + dyp) * 95.0 - 4.0 * (ds_sys + 0.01) * 95.0 + 1.5
    assert em.loc[("recession", "miss"), "dpnl"] == pytest.approx(exp)
    assert em.loc[("recession", "miss"), "ds_sys"] == pytest.approx(ds_sys)
    # Default rows converge to recovery.
    mat = _em(ev.EventType.MATURITY_REFI).set_index(["macro_path", "outcome"])
    assert mat.loc[("recession", "default"), "dpnl"] == pytest.approx(1.5 - (95.0 - 35.0))


def test_policy_driven_yield_rise_lowers_long_pnl():
    lo = _macro_paths()
    hi = [
        ev.MacroPath(p.name, p.prob, p.y2, p.y10, p.policy_rate, p.gdp_growth, p.pmi, p.index_spread, p.default_rate,
                     extra={"dy_growth": p.extra["dy_growth"], "dy_policy": p.extra["dy_policy"] + 0.01})
        for p in lo
    ]
    a = _em(paths=lo).set_index(["macro_path", "outcome"])["dpnl"]
    b = _em(paths=hi).set_index(["macro_path", "outcome"])["dpnl"]
    assert (b < a).all()


def test_event_matrix_risk_reuses_helpers():
    em = _em()
    r = ev.event_matrix_risk(em, alpha=0.05)
    assert len(r) == 1
    pnl = em.pivot(index="macro_path", columns="outcome", values="dpnl")
    po = em.pivot(index="macro_path", columns="outcome", values="p_outcome_given_path")
    pp = em.groupby("macro_path")["p_path"].first().loc[pnl.index].to_numpy()
    assert r.loc[0, "exp_dpnl"] == pytest.approx(ev.expected_event_pnl(pnl.to_numpy(), pp, po.to_numpy()))
    assert r.loc[0, "event_var_alpha"] == pytest.approx(ev.event_var(pnl.to_numpy(), pp, po.to_numpy(), 0.05))
    assert r.loc[0, "worst_outcome_pnl"] == pytest.approx(em["dpnl"].min())


# --- validate_frame on per-path tables -------------------------------------


def _path_frame(table, entities=("A", "B")):
    t = out.TABLES[table]
    key = "cusip" if table == "bond_daily" else "issuer_id"
    rows = []
    for e in entities:
        for m in list(PATHS) + ["weighted"]:
            rows.append({key: e, "macro_path": m, "p_path": P_PATH.get(m, np.nan)})
    df = pd.DataFrame(rows)
    for c in t.columns:
        if c not in df.columns:
            df[c] = None
    df["date"] = datetime(2026, 10, 21)
    df["available_at"] = datetime(2026, 10, 20)
    return df[list(t.columns)]


@pytest.mark.parametrize("table", ["bond_daily", "issuer_state"])
def test_validate_accepts_path_rows(table):
    df = _path_frame(table)
    assert out.validate_frame(df, table) is df


@pytest.mark.parametrize("table", ["bond_daily", "issuer_state"])
def test_validate_catches_missing_and_duplicate_weighted_row(table):
    df = _path_frame(table)
    missing = df[~((df["macro_path"] == "weighted") & (df.index < 4))]
    with pytest.raises(out.SchemaError, match="0 weighted rows"):
        out.validate_frame(missing, table)
    dup = pd.concat([df, df[df["macro_path"] == "weighted"].iloc[[0]]], ignore_index=True)
    with pytest.raises(out.SchemaError, match="2 weighted rows"):
        out.validate_frame(dup, table)


@pytest.mark.parametrize("table", ["bond_daily", "issuer_state"])
def test_validate_catches_p_path_leak(table):
    df = _path_frame(table)
    df.loc[1, "p_path"] = 0.25
    with pytest.raises(out.SchemaError, match="p_path"):
        out.validate_frame(df, table)
    # A tiny error inside the tolerance passes.
    ok = _path_frame(table)
    ok.loc[1, "p_path"] = 0.3 + 1e-9
    out.validate_frame(ok, table)


def test_validate_still_catches_look_ahead_with_paths():
    df = _path_frame("issuer_state")
    df.loc[2, "available_at"] = datetime(2026, 10, 22)
    with pytest.raises(LookAheadError):
        out.validate_frame(df, "issuer_state")


def test_validate_catches_event_matrix_p_path_leak():
    em = _em()
    em.loc[em["macro_path"] == "recession", "p_path"] = 0.2
    with pytest.raises(out.SchemaError, match="p_path"):
        out.validate_frame(em, "event_matrix")


def test_schema_columns_for_forecast_linkage():
    assert {"macro_path", "p_path", "w_down", "phase", "forecast_vintage", "lev_fwd_sd", "refi_fail_share",
            "pd_12m", "s_fair"} <= set(out.ISSUER_STATE.columns)
    assert {"macro_path", "p_path", "s_fair", "resid_bp", "pd_12m", "beta_g", "beta_p"} <= set(out.BOND_DAILY.columns)
    assert {"beta_g", "beta_p"} <= set(out.PORTFOLIO_RISK.columns)
    assert "macro_path" in out.BOND_DAILY.keys and "macro_path" in out.ISSUER_STATE.keys
    assert out.json_schema("issuer_state")["properties"]["forecast_vintage"]["format"] == "date-time"
