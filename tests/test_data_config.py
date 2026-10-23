"""Tests for hy.data.config: one data root and one WRDS connection (design: data module, step 2; AR-DEP-001)."""

from pathlib import Path

from hy.data import config

REPO = Path(__file__).resolve().parents[1]


def test_default_root_is_the_repo_data_raw(monkeypatch):
    monkeypatch.delenv("HY_DATA_ROOT", raising=False)
    assert config.DataConfig.from_env().root == REPO / "data" / "raw"


def test_env_points_a_run_at_another_root(monkeypatch, tmp_path):
    monkeypatch.setenv("HY_DATA_ROOT", str(tmp_path))
    c = config.DataConfig.from_env()
    assert c.root == tmp_path and c.path("backtest") == tmp_path / "backtest"


def test_connect_is_lazy_and_shared(monkeypatch):
    calls = []
    monkeypatch.setattr(config, "_open_wrds", lambda user: calls.append(user) or object())
    config.reset_connection()
    c = config.DataConfig(root=REPO / "data" / "raw", wrds_user="u")
    assert calls == []                     # nothing opens until asked
    a, b = c.connect(), c.connect()
    assert a is b and calls == ["u"]        # one connection per process


def test_no_network_config_refuses_to_connect(monkeypatch):
    config.reset_connection()
    c = config.DataConfig(root=REPO, allow_network=False)
    try:
        c.connect()
    except config.NetworkDisabled:
        pass
    else:
        raise AssertionError("allow_network=False must refuse")
