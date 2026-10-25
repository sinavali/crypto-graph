import pytest
from datetime import datetime, timezone
from libs.blockchain_contracts.models import (
    ChainEcosystem,
    ClusteringHeuristicType,
    CrossChainBridgeEvent,
    DomainTransactionEvent,
)
from src.domain.clustering import PersonaClusteringEngine


def test_persona_clustering_standalone_wallet():
    engine = PersonaClusteringEngine()
    target = "0xaaaa111122223333444455556666777788889999"
    txs = [
        DomainTransactionEvent(
            tx_hash="0x11",
            chain=ChainEcosystem.ETHEREUM,
            from_address="0xbbbb",
            to_address=target,
            value_native=10.0,
            fee_native=0.001,
            timestamp_utc=datetime.now(timezone.utc),
        )
    ]
    persona = engine.compute_persona(target, txs, [])
    assert persona.primary_address == target.lower()
    assert len(persona.clustered_wallets) == 1
    assert persona.confidence_score == 0.50


def test_persona_clustering_cex_deposit_reuse():
    engine = PersonaClusteringEngine()
    target = "0xwallet1"
    shared_deposit = "0xbinance_deposit_123"
    wallet2 = "0xwallet2"

    txs = [
        DomainTransactionEvent(
            tx_hash="0x1",
            chain=ChainEcosystem.ETHEREUM,
            from_address=target,
            to_address=shared_deposit,
            value_native=2.0,
            fee_native=0.001,
            timestamp_utc=datetime.now(timezone.utc),
        ),
        DomainTransactionEvent(
            tx_hash="0x2",
            chain=ChainEcosystem.ETHEREUM,
            from_address=wallet2,
            to_address=shared_deposit,
            value_native=3.0,
            fee_native=0.001,
            timestamp_utc=datetime.now(timezone.utc),
        ),
    ]

    persona = engine.compute_persona(target, txs, [])
    assert len(persona.clustered_wallets) == 2
    assert wallet2 in [w.address for w in persona.clustered_wallets]
    assert "cex-clustered" in persona.tags
    assert persona.confidence_score >= 0.80


def test_persona_clustering_bridge_correlation():
    engine = PersonaClusteringEngine()
    target = "0xwallet_eth"
    dest_wallet = "0xwallet_arb"

    # Forward bridge (target -> dest)
    bridge_events = [
        CrossChainBridgeEvent(
            bridge_name="Stargate",
            source_chain=ChainEcosystem.ETHEREUM,
            source_tx_hash="0xb1",
            source_address=target,
            destination_chain=ChainEcosystem.ARBITRUM,
            destination_address=dest_wallet,
            token_symbol="USDC",
            amount=1000.0,
            timestamp_utc=datetime(2024, 1, 1, tzinfo=timezone.utc),
        ),
        # Reverse bridge (src -> target)
        CrossChainBridgeEvent(
            bridge_name="Across",
            source_chain=ChainEcosystem.POLYGON,
            source_tx_hash="0xb2",
            source_address="0xwallet_poly",
            destination_chain=ChainEcosystem.ETHEREUM,
            destination_address=target,
            token_symbol="ETH",
            amount=2.0,
            timestamp_utc=datetime(2024, 1, 2, tzinfo=timezone.utc),
        ),
    ]

    persona = engine.compute_persona(target, [], bridge_events)
    assert len(persona.clustered_wallets) == 3
    assert dest_wallet in [w.address for w in persona.clustered_wallets]
    assert "0xwallet_poly" in [w.address for w in persona.clustered_wallets]
    assert "cross-chain-operator" in persona.tags
    assert persona.confidence_score >= 0.80


def test_persona_clustering_co_funding_and_wallet_updates():
    engine = PersonaClusteringEngine()
    target = "0xroot_wallet"
    funded_wallet = "0xfunded_wallet_1"

    txs = [
        # Direct small funding
        DomainTransactionEvent(
            tx_hash="0xfund1",
            chain=ChainEcosystem.ETHEREUM,
            from_address=target,
            to_address=funded_wallet,
            value_native=0.5,
            fee_native=0.001,
            timestamp_utc=datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc),
        ),
        # Another transfer updating timestamps
        DomainTransactionEvent(
            tx_hash="0xfund2",
            chain=ChainEcosystem.ETHEREUM,
            from_address=target,
            to_address=funded_wallet,
            value_native=0.2,
            fee_native=0.001,
            timestamp_utc=datetime(2024, 1, 5, 12, 0, tzinfo=timezone.utc),
        ),
    ]

    persona = engine.compute_persona(target, txs, [])
    assert len(persona.clustered_wallets) == 2
    assert funded_wallet in [w.address for w in persona.clustered_wallets]
    wallet_obj = next(w for w in persona.clustered_wallets if w.address == funded_wallet)
    assert len(wallet_obj.evidences) == 2
    assert wallet_obj.last_seen_utc == datetime(2024, 1, 5, 12, 0, tzinfo=timezone.utc)
