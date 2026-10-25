import pytest
from datetime import datetime, timezone
from libs.blockchain_contracts.models import (
    ChainEcosystem,
    DomainTransactionEvent,
    PersonaProfile,
)
from src.infrastructure.sqlite_storage import SqliteGraphStorage


def test_sqlite_storage_transactions():
    storage = SqliteGraphStorage(":memory:")
    addr = "0xabc123"

    txs = [
        DomainTransactionEvent(
            tx_hash="0xtx1",
            chain=ChainEcosystem.ETHEREUM,
            from_address=addr,
            to_address="0xdef456",
            value_native=1.23,
            fee_native=0.001,
            timestamp_utc=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        ),
        DomainTransactionEvent(
            tx_hash="0xtx2",
            chain=ChainEcosystem.ETHEREUM,
            from_address="0x999999",
            to_address=addr,
            value_native=4.56,
            fee_native=0.001,
            timestamp_utc=datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc),
        ),
    ]

    storage.save_transactions(txs)
    stored = storage.get_transactions_for_address(addr)
    assert len(stored) == 2
    assert stored[0].tx_hash == "0xtx2"  # Ordered desc by timestamp


def test_sqlite_storage_persona():
    storage = SqliteGraphStorage(":memory:")
    profile = PersonaProfile(
        persona_id="persona-100",
        label="Test Persona",
        primary_address="0xabc123",
        confidence_score=0.88,
        tags=["trader"],
    )

    storage.save_persona_profile(profile)
    retrieved = storage.get_persona_profile("persona-100")
    assert retrieved is not None
    assert retrieved.persona_id == "persona-100"
    assert retrieved.confidence_score == 0.88

    # Non-existent ID returns None
    assert storage.get_persona_profile("non_existent") is None
