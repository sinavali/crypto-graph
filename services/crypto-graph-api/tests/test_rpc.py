import asyncio
import pytest
from libs.blockchain_contracts.models import ChainEcosystem
from src.infrastructure.rpc_rotator import ResilientRpcRotator, CircuitState, EndpointHealth


def test_endpoint_health_circuit_breaker():
    health = EndpointHealth("https://test-rpc.example.com")
    assert health.is_available() is True
    assert health.state == CircuitState.CLOSED

    # Record 3 failures to trip circuit breaker
    health.record_failure()
    health.record_failure()
    health.record_failure()
    assert health.state == CircuitState.OPEN
    assert health.is_available() is False

    # Simulate success reset
    health.record_success()
    assert health.state == CircuitState.CLOSED
    assert health.is_available() is True


def test_rpc_rotator_round_robin():
    rotator = ResilientRpcRotator(offline_mode=True)
    ep1 = rotator.get_next_endpoint(ChainEcosystem.ETHEREUM)
    ep2 = rotator.get_next_endpoint(ChainEcosystem.ETHEREUM)
    assert ep1 != ep2


def test_rpc_rotator_fetch_offline():
    rotator = ResilientRpcRotator(offline_mode=True)
    txs = asyncio.run(rotator.fetch_transactions("0xd8da6bf26964af9d7eed9e03e53415d37aa96045"))
    assert len(txs) > 0
    bridges = asyncio.run(rotator.fetch_bridge_events("0xd8da6bf26964af9d7eed9e03e53415d37aa96045"))
    assert len(bridges) > 0
