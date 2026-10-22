"""Tests for hy.peers: rating classes, point-in-time sector and rating, implied class, ESP and E13 against peers."""

import numpy as np
import pandas as pd
import pytest

from hy import peers


@pytest.mark.parametrize("sym,cls", [("AAA", "IG"), ("A-", "IG"), ("BBB-", "IG"), ("BB+", "BB"), ("BB-", "BB"),
                                     ("B+", "B"), ("B-", "B"), ("CCC+", "CCC"), ("CC", "CCC"), ("SD", "CCC"),
                                     ("D", "CCC"), ("NR", None), (None, None), ("", None)])
def test_rating_class(sym, cls):
    assert peers.rating_class(sym) == cls


def test_maturity_bucket():
    assert [peers.maturity_bucket(y) for y in (1.0, 2.99, 3.0, 6.9, 7.0, 25.0)] == [0, 0, 1, 1, 2, 2]


def test_sector_at_is_point_in_time():
    g = pd.DataFrame({"gvkey": ["1", "1"], "gsector": ["20", "45"],
                      "indfrom": pd.to_datetime(["2000-01-01", "2020-01-01"]),
                      "indthru": pd.to_datetime(["2019-12-31", None])})
    assert peers.sector_at(g, pd.Timestamp("2015-06-30"))["1"] == "20"
    assert peers.sector_at(g, pd.Timestamp("2021-06-30"))["1"] == "45"


def test_rating_at_ignores_future_and_stale():
    r = pd.DataFrame({"gvkey": ["1", "1", "2"], "splticrm": ["BB", "B", "BBB"],
                      "datadate": pd.to_datetime(["2015-05-31", "2015-06-30", "2014-01-31"])})
    r["available_at"] = r["datadate"] + pd.Timedelta(days=1)
    got = peers.rating_at(r, pd.Timestamp("2015-06-30"))   # the June rating is not public until 1 July
    assert got["1"] == "BB"
    assert "2" not in got.index                             # older than RATING_STALE_DAYS


def test_cutoffs_increase_and_classify():
    rng = np.random.default_rng(0)
    centres = {"IG": 2.0, "BB": 3.5, "B": 5.0, "CCC": 8.0}
    x, c = [], []
    for k, m in centres.items():
        x += list(np.log(m) + rng.normal(0, 0.1, 200))
        c += [k] * 200
    cut = peers.fit_cutoffs(x, c)
    vals = list(cut.values())
    assert vals == sorted(vals)
    assert peers.implied_class(2.0, True, cut) == "IG"
    assert peers.implied_class(5.0, True, cut) == "B"
    assert peers.implied_class(12.0, True, cut) == "CCC"
    assert peers.implied_class(3.0, False, cut) == "CCC"     # negative EBITDA
    assert peers.fit_cutoffs(x[:10], c[:10]) is None         # too few rows


def _cell(n_issuers, spread_of, sector="20", rclass="B", lev=4.0):
    return pd.DataFrame({"gvkey": [f"g{i}" for i in range(n_issuers)], "years": 5.0,
                         "spread": [spread_of(i) for i in range(n_issuers)], "leverage": lev,
                         "sector": sector, "rclass": rclass})


def test_esp_excludes_own_issuer_and_signs():
    df = _cell(7, lambda i: 0.04)
    df.loc[0, "spread"] = 0.08                               # issuer 0 pays twice its peers
    out = peers.peer_signals(df)
    assert out.loc[0, "esp_sr"] == pytest.approx(np.log(2.0))
    assert out.loc[0, "cell_esp_sr"] == "sr"
    assert out.loc[1, "esp_sr"] == pytest.approx(0.0)        # median of others is 0.04 (one 0.08 among six)


def test_e13_uses_spread_per_turn():
    df = _cell(7, lambda i: 0.04)
    df.loc[0, "leverage"] = 2.0                              # same spread, half the leverage: twice the SPT
    out = peers.peer_signals(df)
    assert out.loc[0, "e13_sr"] == pytest.approx(np.log(2.0))
    assert out.loc[0, "esp_sr"] == pytest.approx(0.0)


def test_fallback_when_cell_too_small():
    a = _cell(3, lambda i: 0.04, sector="45")                # sector 45 x B: only 2 other issuers
    b = _cell(8, lambda i: 0.05, sector="20")
    b["gvkey"] = [f"h{i}" for i in range(8)]
    out = peers.peer_signals(pd.concat([a, b], ignore_index=True))
    assert out.loc[0, "cell_esp_sr"] == "r"                  # falls back to the rating cell
    assert out.loc[0, "esp_sr"] == pytest.approx(np.log(0.04 / 0.05))
