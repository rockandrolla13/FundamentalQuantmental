"""Tests for the fair spread layer (methodology Section 7; Section 11 rows PD, Fair spread, Conformal band)."""

import math

import numpy as np
import pandas as pd
import pytest

from hy import fairspread as fs


# --- 7.1 anchor -------------------------------------------------------------


def test_hazard_and_anchor_units():
    lam = fs.hazard(0.036)
    assert lam == pytest.approx(-math.log(0.964))
    s_el = fs.expected_loss_spread_bp(0.036, 0.6)
    assert s_el == pytest.approx(lam * 0.6 * 1e4)
    kappa = fs.kappa_by_bucket({"B": 400.0}, {"B": 200.0})
    assert kappa["B"] == pytest.approx(2.0)
    assert fs.anchor_spread_bp(s_el, kappa["B"]) == pytest.approx(2.0 * s_el)


def test_pd_5y_constant_hazard_and_term_table():
    p1 = np.array([0.036])
    assert fs.pd_5y(p1)[0] == pytest.approx(1 - 0.964**5)
    # With the book table, an issuer at the bucket rate reproduces the 5y rate.
    p5 = fs.pd_5y(p1, ["HY"], fs.DEFAULT_PD_TABLE)
    assert p5[0] == pytest.approx(0.1416, abs=1e-12)


def _pd_data(rng, n=6000):
    buckets = rng.choice(["BB", "B", "CCC"], size=n, p=[0.4, 0.45, 0.15])
    shift = pd.Series(buckets).map({"BB": -1.0, "B": 0.0, "CCC": 1.5}).to_numpy()
    X = pd.DataFrame(
        {
            "lev_fwd_4": rng.normal(5 + shift, 1.0),
            "cov_fwd_4": rng.normal(2.5 - shift, 0.7),
            "p_liq_short_8": rng.beta(1, 8, n),
            "dd_equity": np.where(rng.random(n) < 0.3, np.nan, rng.normal(2 - shift, 1)),
        }
    )
    eta = -5 + 0.6 * X["lev_fwd_4"] - 0.5 * X["cov_fwd_4"] + 3 * X["p_liq_short_8"]
    y = rng.random(n) < 1 / (1 + np.exp(-eta.to_numpy()))
    return X, y.astype(int), buckets


def test_pd_calibration_by_rating(rng):
    """Section 11, PD row: mean fitted PD per bucket equals the agency table after recalibration."""
    X, y, b = _pd_data(rng)
    model = fs.PDModel().fit(X, y, b)
    p = model.predict_pd12(X, b)
    for bucket in ["BB", "B", "CCC"]:
        target = fs.DEFAULT_PD_TABLE[bucket][0]
        assert p[b == bucket].mean() == pytest.approx(target, abs=1e-3)
    # Rank order inside a bucket follows the fundamentals.
    m = b == "B"
    assert np.corrcoef(p[m], X.loc[m, "lev_fwd_4"])[0, 1] > 0
    assert np.all((model.predict_pd5y(X, b) > p))


# --- 7.2 empirical model ----------------------------------------------------


def _spread_panel(rng, n=3000):
    dates = pd.to_datetime("2024-01-31") + pd.to_timedelta(rng.integers(0, 6, n) * 30, unit="D")
    sector = rng.choice(["energy", "tech", "retail"], n)
    X = pd.DataFrame(
        {
            "lev_adj_k": rng.uniform(2, 8, n),
            "coverage": rng.uniform(1, 6, n),
            "bid_ask_bp": rng.uniform(10, 120, n),
            "log_amount_outstanding": rng.uniform(5, 7.5, n),
        }
    )
    log_anchor = np.log(rng.uniform(150, 500, n))
    sec_eff = pd.Series(sector).map({"energy": 0.15, "tech": -0.1, "retail": 0.05}).to_numpy()
    f = 0.12 * X["lev_adj_k"] - 0.08 * X["coverage"] + 0.002 * X["bid_ask_bp"] - 0.05 * X["log_amount_outstanding"]
    log_s = log_anchor + f.to_numpy() + sec_eff + rng.normal(0, 0.15, n)
    return X, log_s, log_anchor, sector, dates


def test_monotone_signs(rng):
    """Section 11, Fair spread row: spread non-decreasing in leverage, non-increasing in coverage."""
    X, log_s, log_anchor, sector, dates = _spread_panel(rng)
    model = fs.FairSpreadModel(half_life=90.0).fit(X, log_s, log_anchor, sector, dates)
    assert model.cst_ == [1, -1, 1, -1]
    grid = np.linspace(0, 10, 41)
    for i in range(20):
        base = X.iloc[[i] * len(grid)].reset_index(drop=True)
        sec = [sector[i]] * len(grid)
        dt = [dates[i]] * len(grid)
        anc = np.full(len(grid), log_anchor[i])
        lev = base.copy()
        lev["lev_adj_k"] = grid
        assert np.all(np.diff(model.predict_log_spread(lev, sec, dt, anc)) >= -1e-12)
        cov = base.copy()
        cov["coverage"] = grid
        assert np.all(np.diff(model.predict_log_spread(cov, sec, dt, anc)) <= 1e-12)
    # The model recovers the sector ordering and fits better than the anchor alone.
    eta = model.eta_.groupby("sector")["eta"].mean()
    assert eta["energy"] > eta["retail"] > eta["tech"]
    resid = log_s - model.predict_log_spread(X, sector, dates, log_anchor)
    assert resid.std() < 0.2 < (log_s - log_anchor).std()


def test_recency_weights_halve_per_half_life():
    w = fs.recency_weights(pd.to_datetime(["2024-01-01", "2024-01-31", "2024-03-01"]), half_life=30.0)
    assert w[-1] == pytest.approx(1.0)
    assert w[1] == pytest.approx(0.5 ** (30 / 30.0))


# --- 7.3 conformal ----------------------------------------------------------


def test_conformal_quantile_finite_sample():
    s = np.arange(1, 20, dtype=float)  # n = 19
    assert fs.conformal_quantile(s, 0.1) == 18.0  # k = ceil(20 * 0.9) = 18
    assert fs.conformal_quantile(s[:5], 0.1) == np.inf  # k = 6 > 5


def test_conformal_coverage_per_mondrian_cell(rng):
    """Section 11, Conformal band row: realised coverage within 2 SE of 1 - alpha in every cell."""
    alpha = 0.1
    ratings, liqs = ["BB", "B", "CCC"], ["liquid", "illiquid"]
    scale = {("BB", "liquid"): 0.05, ("BB", "illiquid"): 0.10, ("B", "liquid"): 0.10,
             ("B", "illiquid"): 0.20, ("CCC", "liquid"): 0.25, ("CCC", "illiquid"): 0.45}

    def draw(n_per_cell):
        rows = []
        for (r, l), sc in scale.items():
            x = rng.uniform(0, 1, n_per_cell)
            eps = rng.standard_t(5, n_per_cell) * sc * (0.5 + 1.5 * x)  # heteroskedastic in x too
            rows.append(pd.DataFrame({"r": r, "l": l, "x": x, "liq": float(l == "illiquid"),
                                      "ccc": float(r == "CCC"), "eps": eps}))
        return pd.concat(rows, ignore_index=True)

    train = draw(400)
    feats = ["x", "liq", "ccc"]
    sig = fs.NoiseScaleModel().fit(train[feats], train["eps"])
    n_cal, n_test, reps = 199, 200, 150  # (n_cal + 1)(1 - alpha) is an integer: exact expected coverage
    cover = {k: [] for k in scale}
    for _ in range(reps):
        cal, test = draw(n_cal), draw(n_test)
        cp = fs.MondrianConformal(alpha=alpha).fit(fs.z_score(cal["eps"], sig.predict(cal[feats])), cal["r"], cal["l"])
        z = fs.z_score(test["eps"], sig.predict(test[feats]))
        q = cp.threshold(test["r"], test["l"])
        hit = np.abs(z) <= q
        for k in scale:
            m = (test["r"] == k[0]) & (test["l"] == k[1])
            cover[k].append(hit[m.to_numpy()].mean())
    for k, c in cover.items():
        c = np.asarray(c)
        se = c.std(ddof=1) / math.sqrt(reps)
        assert abs(c.mean() - (1 - alpha)) <= 2 * se, (k, c.mean(), se)
    # Flags are disjoint and use the band.
    cheap, rich = fs.cheap_rich_flags(np.array([-3.0, 0.0, 3.0]), 2.0)
    assert cheap.tolist() == [False, False, True] and rich.tolist() == [True, False, False]


def test_noise_scale_tracks_heteroskedasticity(rng):
    x = rng.uniform(0, 1, (4000, 1))
    eps = rng.normal(0, 0.1 + 0.4 * x[:, 0])
    sig = fs.NoiseScaleModel().fit(x, eps).predict(np.array([[0.0], [1.0]]))
    assert sig[1] > 2.5 * sig[0]


def test_aci_tracks_target_under_drift(rng):
    """Section 7.3 ACI: coverage tracks 1 - alpha when the noise scale drifts; the static band misses."""
    T, window, alpha, gamma = 6000, 250, 0.1, 0.01
    scale = np.exp(np.linspace(0, 6.0, T + window))  # noise scale rises 400-fold
    scores = np.abs(rng.normal(0, scale))
    aci = fs.adaptive_conformal(scores, alpha, gamma, window, adaptive=True)
    static = fs.adaptive_conformal(scores, alpha, gamma, window, adaptive=False)
    bound = (max(alpha, 1 - alpha) + gamma) / (gamma * T)  # Gibbs and Candes (2021), Prop. 4.1
    assert abs(aci.coverage - (1 - alpha)) <= bound
    assert static.coverage < (1 - alpha) - 0.03
    assert aci.alpha_t[-1] < alpha  # band widened to keep up
    assert fs.aci_update(0.1, 1.0, 0.1, 0.01) == pytest.approx(0.1 - 0.009)


# --- 7.4 spread per turn ----------------------------------------------------


def test_hca_spread_per_turn():
    """Section 7.4: HCA memo pp. 412-413."""
    assert fs.spread_per_turn(224, 0, 1.3, 0) == pytest.approx(172, abs=0.5)
    assert fs.spread_per_turn(60, 0, 1.7, 0) == pytest.approx(35, abs=0.5)
    gap = fs.model_pair_gap_bp(2.0, fs.hazard(0.03), 0.7, 0.3)
    assert gap == pytest.approx(2.0 * -math.log(0.97) * 0.4 * 1e4)


# --- 7.5 residual dynamics --------------------------------------------------


def test_half_life_and_ar1(rng):
    assert fs.half_life(0.5) == pytest.approx(1.0)
    assert fs.half_life(1.0) == np.inf and fs.half_life(-0.2) == 0.0
    e = np.zeros(5000)
    for t in range(1, len(e)):
        e[t] = 0.8 * e[t - 1] + rng.normal()
    assert fs.fit_ar1(e) == pytest.approx(0.8, abs=0.02)


def test_expected_convergence_return_units():
    # 100 bp cheap, rho 0.5, h 1: half the gap closes = 50 bp; D_s 4 -> 2% plus 0.5% carry.
    r = fs.expected_convergence_return(0.005, 4.0, 0.5, 1, 100.0)
    assert r == pytest.approx(0.025)


def test_event_contaminated():
    flag = fs.event_contaminated(
        ["2024-06-10"] * 4,
        pd.to_datetime(["2024-06-07", "2024-06-01", "2024-06-12", None]),
    )
    assert flag.tolist() == [1, 0, 0, 0]


# --- 7.2 peer fair spread (decision page 2026-10-23-peer-fair-spread) ---------


def test_peer_fair_spread_is_the_peer_median():
    # ESP = log s - median log s of peers, so the fair spread is s exp(-ESP): the peers' median spread.
    f = fs.peer_fair_spread(0.05, np.log(0.05 / 0.04), 0.3, s_index=0.03)
    assert f["fair"] == pytest.approx(0.04)
    assert f["basis"] == "sector peers" and f["noise_log"] == pytest.approx(0.3)


def test_peer_fair_spread_falls_back_to_the_index():
    for esp in (None, float("nan")):
        f = fs.peer_fair_spread(0.05, esp, None, s_index=0.03)
        assert f["fair"] == pytest.approx(0.03) and f["basis"] == "HY index"
        assert f["noise_log"] != f["noise_log"]  # NaN: no peer dispersion, so the gate does not test it


def test_dts_beta():
    assert fs.dts_beta(0.06, 0.03) == pytest.approx(2.0)
    assert fs.dts_beta(0.06, 0.0) != fs.dts_beta(0.06, 0.0)  # NaN without an index spread
