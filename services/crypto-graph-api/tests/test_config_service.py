import pytest
from libs.blockchain_contracts.config_models import ConfigCategory
from src.domain.config_service import ConfigService
from src.infrastructure.sqlite_storage import SqliteGraphStorage


def test_config_service_defaults_and_updates():
    storage = SqliteGraphStorage(":memory:")
    config = ConfigService(storage)

    # Defaults seeded
    timeout = config.get_float("rpc.timeout_seconds")
    assert timeout == 4.0

    offline = config.get_bool("rpc.offline_mode")
    assert offline is False

    retries = config.get_int("rpc.max_retries")
    assert retries == 3

    endpoints = config.get_json("rpc.endpoints")
    assert "ethereum" in endpoints
    assert len(endpoints["ethereum"]) > 0

    # Dynamic update
    config.set("rpc.timeout_seconds", "8.5")
    assert config.get_float("rpc.timeout_seconds") == 8.5

    config.set("rpc.offline_mode", "true")
    assert config.get_bool("rpc.offline_mode") is True

    # Grouped by category
    categories = config.get_all_by_category()
    assert "rpc" in categories
    assert "heuristics" in categories
    assert "graph" in categories
    assert "security" in categories
