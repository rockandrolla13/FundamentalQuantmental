"""Tests for hy.data.source protocols, FakeSource and WarehouseSource (design: data module, step 3).

The warehouse tests read the local caches under data/raw (vendor data, not in git) with the network off; they skip
when the cache is absent.
"""

from datetime import datetime

import pandas as pd
import pytest

from hy.data import config, records, source, sources
from hy.data.pit import DataUnavailable

T = datetime(2026, 9, 18)
PROTOCOLS = (source.IssuerSource, source.FilingSource, source.BondSource, source.MarketSource,
             source.ReferenceSource, source.ForecastSource, source.AnalystSource)


def _fake() -> sources.FakeSource:
    iss = records.Issuer("ABC", gvkey="000001", cik="1", name="ABC Corp")
    fin = records.IssuerFinancials("000001", datetime(2026, 6, 30), datetime(2026, 8, 1), revenue=100.0)
    bond = records.Bond("000001AA1", "ABC", 0.06, datetime(2031, 6, 1), "senior_unsecured", True, False)
    obs = pd.DataFrame({"cusip": ["000001AA1"], "date": [datetime(2026, 9, 17)], "price": [98.0], "yield": [0.07],
                        "n_trades": [3], "par_volume": [5e6], "available_at": [datetime(2026, 9, 18)]})
    curve = records.Curve("UST", datetime(2026, 9, 17), datetime(2026, 9, 17), tenors=(1.0, 5.0), yields=(0.04, 0.042))
    return sources.FakeSource(issuers=[iss], financials=[fin], bonds=[bond], observations=obs, curves=[curve])


def test_fake_source_satisfies_every_protocol():
    f = _fake()
    for p in PROTOCOLS:
        assert isinstance(f, p), p.__name__


def test_fake_source_answers_and_says_what_is_missing():
    f = _fake()
    iss = f.issuers(["ABC"])[0]
    assert f.financials(iss)[0].revenue == 100.0
    assert f.bonds(iss)[0].cusip == "000001AA1"
    assert list(f.observations(f.bonds(iss), datetime(2026, 1, 1), T).columns) == list(records.BOND_OBS_COLUMNS)
    assert f.curve(T).yields == (0.04, 0.042)
    with pytest.raises(DataUnavailable):
        f.issuers(["ZZZ"])
    with pytest.raises(DataUnavailable):
        f.hy_index(T)


def test_curve_is_the_latest_public_one_not_the_one_dated_today():
    # A curve dated d is public at d + 1. Asked on d, a source must give the curve of d - 1.
    d0, d1 = datetime(2026, 9, 16), datetime(2026, 9, 17)
    c0 = records.Curve("UST", d0, datetime(2026, 9, 17), tenors=(5.0,), yields=(0.040,))
    c1 = records.Curve("UST", d1, datetime(2026, 9, 18), tenors=(5.0,), yields=(0.041,))
    f = sources.FakeSource(curves=[c0, c1])
    assert f.curve(d1).as_of == d0 and f.curve(datetime(2026, 9, 18)).as_of == d1


def test_observation_frames_are_checked():
    with pytest.raises(ValueError, match="columns"):
        records.check_observations(pd.DataFrame({"cusip": ["x"]}))


def test_warehouse_source_satisfies_every_protocol():
    w = sources.WarehouseSource(config.DataConfig(allow_network=False))
    for p in PROTOCOLS:
        assert isinstance(w, p), p.__name__


@pytest.mark.skipif(not (config.DEFAULT_ROOT / "compustat_pit" / "issuers.json").exists(), reason="no local cache")
def test_warehouse_source_reads_the_cache_offline():
    w = sources.WarehouseSource(config.DataConfig(allow_network=False))
    hca = w.issuers(["HCA"])[0]
    assert hca.gvkey == "022260" and hca.cik
    fin = w.financials(hca)
    assert fin and isinstance(fin[0], records.IssuerFinancials)
    bonds = w.bonds(hca)
    assert bonds and all(isinstance(b, records.Bond) for b in bonds)
    c = w.curve(T)
    assert isinstance(c, records.Curve) and c.available_at <= T and len(c.tenors) == len(c.yields) > 5
    with pytest.raises(DataUnavailable, match="step 5"):
        w.hy_index(T)
