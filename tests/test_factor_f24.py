"""F24 cell valuation percentile: contract, no look-ahead, the history cache, sign, thin cells, short history, CCC
pooling, excluded ratings, missing panels, and the formula helpers against hand numbers and p. 5 of the source."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from hy.backtest import decision_time
from hy.factors import f24_cell_percentile as f24

AS_OF = pd.Timestamp("2012-12-31")
MONTHS = pd.date_range(end=AS_OF, periods=48, freq="ME")      # 2009-01 .. 2012-12: 47 prior months
DAY = pd.Timedelta(1, unit="D")
T = np.arange(len(MONTHS), dtype=float)

# cell -> (S&P symbol, years, spread path in decimals, issuers)
CELLS = {
    "BBB13": ("BBB", 2.0, np.full(len(T), 0.0063), 5),
    "BB13": ("BB", 2.0, 0.0300 - 0.0001 * T, 5),                 # tightest now: P = 0
    "BB710": ("BB+", 8.0, 0.0200 + 0.0001 * T, 5),               # widest now: P = 1
    "B13": ("B-", 2.0, 0.0429 + 0.0020 * np.sin(T), 5),
    "CCC_a": ("CCC+", 2.0, 0.0800 + 0.0001 * T, 3),              # CCC pools tenors: 3 + 3 issuers
    "CCC_b": ("CCC", 8.0, 0.0800 + 0.0001 * T, 3),
    "A13": ("A", 2.0, np.full(len(T), 0.0040), 5),               # A and better: no cell
    "B35": ("B", 4.0, 0.0400 + 0.0001 * T, 4),                   # thin: 4 issuers
}


def _rows(name: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    sym, years, path, n = CELLS[name]
    bonds, rats = [], []
    for k in range(n):
        g = f"{name}_G{k}"
        bonds.append(pd.DataFrame({"date": MONTHS, "cusip": f"{name}_C{k}", "gvkey": g, "years": years,
                                   "g_spread": path + 0.0002 * k, "price": 100.0, "yield": 0.07, "mod_dur": 4.0,
                                   "carried": False, "available_at": MONTHS + DAY}))
        rats.append(pd.DataFrame({"gvkey": g, "datadate": MONTHS, "splticrm": sym, "available_at": MONTHS + DAY}))
    return pd.concat(bonds), pd.concat(rats)


def _panels(cells=tuple(CELLS)) -> dict:
    parts = [_rows(c) for c in cells]
    return {"bond_panel": pd.concat([b for b, _ in parts], ignore_index=True),
            "ratings": pd.concat([r for _, r in parts], ignore_index=True)}


@pytest.fixture(scope="module")
def base() -> dict:
    return _panels()


@pytest.fixture(scope="module")
def ref(base) -> pd.DataFrame:
    return f24.compute(base, AS_OF).set_index("cusip")


# ---------------------------------------------------------------- 1. contract


def test_meta_and_columns(base, ref):
    for k in ("rank", "name", "level", "horizon_months", "needs", "spec", "section"):
        assert k in f24.META
    assert f24.META["rank"] == 24 and f24.META["level"] == "bond" and f24.META["horizon_months"] == 3
    out = f24.compute(base, AS_OF)
    assert list(out.columns) == f24.COLS
    assert out["cusip"].is_unique
    assert (out["date"] == AS_OF).all() and (out["available_at"] == decision_time(AS_OF)).all()
    # BB, B and CCC bonds only: no BBB, no A rows
    assert set(out["rating"]) == {"BB", "B", "CCC"}
    assert len(out) == 5 + 5 + 5 + 6 + 4


# ---------------------------------------------------------------- 2. no look-ahead and the cache


def test_later_rows_and_late_revisions_do_not_change_output(base, ref):
    p = base["bond_panel"]
    later = p[p["date"] == AS_OF].copy()
    later["date"] = pd.Series(AS_OF + pd.offsets.MonthEnd(1), index=later.index).astype("datetime64[ns]")
    later["available_at"] = later["date"] + DAY
    later["g_spread"] = 0.50
    late = p[p["date"] == MONTHS[10]].copy()                      # a revision known only after as_of
    late["g_spread"] = 0.90
    late["available_at"] = pd.Series(AS_OF + pd.Timedelta(5, unit="D"), index=late.index).astype("datetime64[ns]")
    r = base["ratings"]
    late_r = r[r["datadate"] == AS_OF].assign(splticrm="D", available_at=AS_OF + pd.Timedelta(3, unit="D"))
    late_r["available_at"] = late_r["available_at"].astype("datetime64[ns]")
    panels = {"bond_panel": pd.concat([p, later, late], ignore_index=True),
              "ratings": pd.concat([r, late_r], ignore_index=True)}
    out = f24.compute(panels, AS_OF).set_index("cusip")
    pd.testing.assert_frame_equal(out.sort_index(), ref.sort_index())


def test_cache_gives_the_same_result_and_late_cache_rows_are_ignored(base, ref):
    cache = f24.cell_history(base, MONTHS[:-1])
    assert list(cache.columns) == f24.HIST_COLS
    bad = cache[cache["date"] == MONTHS[5]].assign(median_spread=9.0, available_at=AS_OF + pd.Timedelta(9, unit="D"))
    out = f24.compute({**base, "cell_history": pd.concat([cache, bad], ignore_index=True)}, AS_OF).set_index("cusip")
    pd.testing.assert_frame_equal(out.sort_index(), ref.sort_index())


# ---------------------------------------------------------------- 3. sign


def test_widest_cell_scores_one_and_tightest_scores_zero(ref):
    assert (ref.loc[ref["cell"] == "BB|7-10", "score"] == 1.0).all()
    assert (ref.loc[ref["cell"] == "BB|1-3", "score"] == 0.0).all()
    assert (ref.loc[ref["cell"] == "BB|1-3", "cell_n_hist"] == len(MONTHS) - 1).all()
    b = ref.loc[ref["cell"] == "B|1-3", "score"]
    assert b.between(0, 1).all() and b.nunique() == 1


# ---------------------------------------------------------------- 4. edge cases


def test_ccc_pools_tenors(ref):
    ccc = ref[ref["rating"] == "CCC"]
    assert set(ccc["cell"]) == {"CCC|all"} and (ccc["cell_n_issuers"] == 6).all()
    assert (ccc["score"] == 1.0).all()


def test_thin_cell_has_no_score(ref):
    thin = ref[ref["cell"] == "B|3-5"]
    assert len(thin) == 4 and thin["score"].isna().all() and thin["cell_spread"].isna().all()


def test_short_history_gives_nan(base):
    out = f24.compute(base, AS_OF, min_history_years=4)           # 48 months needed, 47 exist
    assert out["score"].isna().all()
    out = f24.compute(base, AS_OF, window_months=12, min_history_years=1)
    bb = out[out["cell"] == "BB|7-10"]
    assert (bb["score"] == 1.0).all() and (bb["cell_n_hist"] == 12).all()


def test_defaulted_issuer_dropped(base):
    r = base["ratings"].copy()
    r.loc[(r["gvkey"] == "BB13_G0") & (r["datadate"] == AS_OF), "splticrm"] = "D"
    out = f24.compute({**base, "ratings": r}, AS_OF)
    assert "BB13_C0" not in set(out["cusip"])
    assert out.loc[out["cell"] == "BB|1-3", "score"].isna().all()   # 4 issuers left: thin


def test_missing_panels_give_empty_frame(base):
    for k in ("bond_panel", "ratings"):
        out = f24.compute({kk: v for kk, v in base.items() if kk != k}, AS_OF)
        assert out.empty and list(out.columns) == f24.COLS
    out = f24.compute(base, pd.Timestamp("2015-06-30"))           # no rows that month
    assert out.empty and list(out.columns) == f24.COLS


def test_ratio_columns_are_index_level(ref):
    assert ref["ratio_bb_bbb"].nunique() == 1 and ref["ratio_b_bb"].nunique() == 1
    bb = 0.0300 - 0.0001 * T[-1] + 0.0002 * 2                    # median of 5 issuers: offset k = 2
    bbb = 0.0063 + 0.0002 * 2
    assert ref["ratio_bb_bbb"].iloc[0] == pytest.approx(bb / bbb)
    assert ref["ratio_bb_bbb_pct"].iloc[0] == 0.0                 # BB tightens, BBB flat: lowest ratio so far


# ---------------------------------------------------------------- 5. formula helpers


def test_tenor_bucket_edges():
    y = pd.Series([1.0, 3.0, 3.01, 5.0, 6.9, 7.0, 10.0, 10.5, np.nan])
    assert f24.tenor_bucket(y).tolist()[:-1] == ["1-3", "1-3", "3-5", "3-5", "5-7", "5-7", "7-10", "10+"]
    assert pd.isna(f24.tenor_bucket(y).iloc[-1])


def test_cell_rating_maps_ig_to_bbb_only():
    rc = pd.Series(["IG", "IG", "IG", "BB", "CCC", None])
    raw = pd.Series(["BBB-", "A+", np.nan, "BB", "CCC-", np.nan])
    out = f24.cell_rating(rc, raw)
    assert out.iloc[0] == "BBB" and pd.isna(out.iloc[1])         # A+ has no cell
    assert out.iloc[2] == "BBB" and out.iloc[3] == "BB" and out.iloc[4] == "CCC" and pd.isna(out.iloc[5])


def test_own_history_percentile_hand_numbers():
    x = pd.Series([1.0, 3.0, 2.0, 5.0, 4.0], index=pd.date_range("2020-01-31", periods=5, freq="ME"))
    p = f24.own_history_percentile(x, min_obs=2)
    assert p["pct"].isna().tolist()[:2] == [True, True]
    assert p["pct"].iloc[2:].tolist() == [0.5, 1.0, 0.75]       # 2 vs {1,3}; 5 vs {1,3,2}; 4 vs {1,3,2,5}
    w = f24.own_history_percentile(x, min_obs=2, window=2)
    assert w["pct"].iloc[4] == 0.5 and w["n_hist"].iloc[4] == 2  # 4 vs {2,5}
    tie = f24.own_history_percentile(pd.Series([2.0, 2.0, 2.0], index=x.index[:3]), min_obs=2)
    assert tie["pct"].iloc[2] == 0.0                              # strict "<" (p. 11)


def test_spread_ratios_match_source_page_5():
    wide = pd.DataFrame({"BBB|1-3": [63.0], "BB|1-3": [224.0], "B|1-3": [429.0]}, index=[AS_OF])
    r = f24.spread_ratios(wide)
    assert r["ratio_bb_bbb"].iloc[0] == pytest.approx(3.556, abs=1e-3)   # "above 3.5x" (p. 5)
    assert r["ratio_b_bb"].iloc[0] == pytest.approx(1.915, abs=1e-3)
    eur = f24.spread_ratios(pd.DataFrame({"BBB|1-3": [77.0], "BB|1-3": [199.0]}, index=[AS_OF]))
    assert eur["ratio_bb_bbb"].iloc[0] == pytest.approx(2.584, abs=1e-3) and eur["ratio_b_bb"].isna().all()


def test_cell_medians_issuer_threshold():
    b = pd.DataFrame({"cusip": list("abcde"), "gvkey": ["g1", "g1", "g2", "g3", "g4"], "g_spread": [1, 2, 3, 4, 5.0],
                      "rating": "BB", "tenor": "1-3", "cell": "BB|1-3"})
    assert np.isnan(f24.cell_medians(b, 5).loc["BB|1-3", "median_spread"])
    m = f24.cell_medians(b, 4).loc["BB|1-3"]
    assert m["median_spread"] == 3.0 and m["n_bonds"] == 5 and m["n_issuers"] == 4
