from datetime import datetime, timezone
import pytest
from src.models import (
    Address,
    AddressType,
    ChainEcosystem,
    CrossChainBridgeEvent,
    DomainTransactionEvent,
    PersonaProfile,
    AttributionEvidence,
    ClusteringHeuristicType,
    GraphNode,
    GraphEdge,
    GraphTopology,
)
from src.fixtures import (
    VITALIK_ETH,
    SATOSHI_BTC,
    CLUSTER_WALLET_A,
    CLUSTER_WALLET_B,
    get_fixture_transactions,
    get_fixture_bridges,
)


def test_address_validation_evm():
    addr = Address.from_str(VITALIK_ETH)
    assert addr.normalized_address == VITALIK_ETH.lower()
    assert ChainEcosystem.ETHEREUM in addr.detected_ecosystems
    assert ChainEcosystem.ARBITRUM in addr.detected_ecosystems
    assert addr.address_type == AddressType.EOA


def test_address_validation_bitcoin():
    addr = Address.from_str(SATOSHI_BTC)
    assert addr.normalized_address == SATOSHI_BTC
    assert ChainEcosystem.BITCOIN in addr.detected_ecosystems


def test_address_validation_solana():
    sol_addr = "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU"
    addr = Address.from_str(sol_addr)
    assert addr.normalized_address == sol_addr
    assert ChainEcosystem.SOLANA in addr.detected_ecosystems


def test_address_validation_other_ecosystems():
    tron_addr = "TLa2f6VPqDgRE67v1736s7bJ8Ray5wYjU7"
    addr_tron = Address.from_str(tron_addr)
    assert ChainEcosystem.TRON in addr_tron.detected_ecosystems

    cosmos_addr = "cosmos1hsk6jryyqjfhp5dhc55tc9jtckygx0eph6dd02"
    addr_cosmos = Address.from_str(cosmos_addr)
    assert ChainEcosystem.COSMOS in addr_cosmos.detected_ecosystems

    near_addr = "vitalik.near"
    addr_near = Address.from_str(near_addr)
    assert ChainEcosystem.NEAR in addr_near.detected_ecosystems

    near_hex_addr = "0" * 64
    addr_near_hex = Address.from_str(near_hex_addr)
    assert ChainEcosystem.NEAR in addr_near_hex.detected_ecosystems

    generic_addr = "some_unknown_identifier"
    addr_gen = Address.from_str(generic_addr)
    assert addr_gen.normalized_address == "some_unknown_identifier"


def test_domain_transaction_utc_enforcement():
    naive_dt = datetime(2024, 1, 1, 12, 0, 0)
    tx = DomainTransactionEvent(
        tx_hash="0x123",
        chain=ChainEcosystem.ETHEREUM,
        from_address="0xaaa",
        to_address="0xbbb",
        value_native=1.5,
        fee_native=0.001,
        timestamp_utc=naive_dt,
    )
    assert tx.timestamp_utc.tzinfo == timezone.utc

    # Test with already UTC-aware datetime
    aware_dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    tx2 = DomainTransactionEvent(
        tx_hash="0x124",
        chain=ChainEcosystem.ETHEREUM,
        from_address="0xaaa",
        to_address="0xbbb",
        value_native=2.0,
        fee_native=0.001,
        timestamp_utc=aware_dt,
    )
    assert tx2.timestamp_utc == aware_dt


def test_fixture_vitalik_transactions():
    txs = get_fixture_transactions(VITALIK_ETH)
    assert len(txs) >= 4
    for tx in txs:
        assert tx.chain == ChainEcosystem.ETHEREUM
        assert tx.timestamp_utc.tzinfo == timezone.utc


def test_fixture_satoshi_and_non_evm():
    btc_txs = get_fixture_transactions(SATOSHI_BTC)
    assert len(btc_txs) == 3
    assert btc_txs[0].chain == ChainEcosystem.BITCOIN
    assert btc_txs[0].token_symbol == "BTC"
    # Verify co-inputs UTXO
    assert len(btc_txs[1].co_inputs) == 2

    sol_txs = get_fixture_transactions("9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM")
    assert len(sol_txs) == 2
    assert sol_txs[0].chain == ChainEcosystem.SOLANA
    assert sol_txs[0].token_symbol == "SOL"

    tron_txs = get_fixture_transactions("TL34sq8mSXTHi6n81qJ8Vn2X52Ssmr5x4d")
    assert len(tron_txs) == 2
    assert tron_txs[0].chain == ChainEcosystem.TRON
    assert tron_txs[0].token_symbol == "TRX"


def test_fixture_cluster_and_synthetic_transactions():
    cluster_txs = get_fixture_transactions(CLUSTER_WALLET_A)
    assert len(cluster_txs) >= 2

    synthetic_txs = get_fixture_transactions("0x9999888877776666555544443333222211110000")
    assert len(synthetic_txs) == 2


def test_cross_chain_bridge_fixtures():
    bridges = get_fixture_bridges()
    assert len(bridges) >= 2
    assert bridges[0].bridge_name == "Stargate"
    assert bridges[0].source_chain == ChainEcosystem.ETHEREUM
    assert bridges[0].destination_chain == ChainEcosystem.ARBITRUM

    # Test naive datetime in bridge event
    naive_b = CrossChainBridgeEvent(
        bridge_name="Across",
        source_chain=ChainEcosystem.POLYGON,
        source_tx_hash="0x1",
        source_address="0xa",
        destination_chain=ChainEcosystem.ARBITRUM,
        destination_address="0xb",
        token_symbol="USDC",
        amount=100.0,
        timestamp_utc=datetime(2024, 2, 1, 10, 0, 0),
    )
    assert naive_b.timestamp_utc.tzinfo == timezone.utc


def test_persona_profile_contracts():
    profile = PersonaProfile(
        persona_id="persona-001",
        label="Test Persona",
        primary_address=CLUSTER_WALLET_A,
        confidence_score=0.92,
        tags=["high-volume", "cross-chain"],
    )
    assert profile.confidence_score == 0.92
    assert profile.created_at_utc.tzinfo is not None


def test_graph_topology_contracts():
    n1 = GraphNode(id="n1", address="0xa", chain=ChainEcosystem.ETHEREUM, label="Node A", degree=2)
    n2 = GraphNode(id="n2", address="0xb", chain=ChainEcosystem.ETHEREUM, label="Node B", degree=1)
    e1 = GraphEdge(
        id="e1",
        source="n1",
        target="n2",
        tx_count=5,
        total_volume_native=10.5,
        first_seen_utc=datetime.now(timezone.utc),
        last_seen_utc=datetime.now(timezone.utc),
    )
    topo = GraphTopology(
        nodes=[n1, n2],
        edges=[e1],
        target_address="0xa",
        total_volume=10.5,
        unique_counterparties=1,
    )
    assert len(topo.nodes) == 2
    assert len(topo.edges) == 1
    assert topo.unique_counterparties == 1
