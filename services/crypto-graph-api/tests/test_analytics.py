import pytest
from datetime import datetime, timezone
from libs.blockchain_contracts.models import (
    ChainEcosystem,
    CrossChainBridgeEvent,
    DomainTransactionEvent,
)
from src.domain.analytics import GraphAnalyticsEngine


def test_graph_analytics_empty():
    engine = GraphAnalyticsEngine()
    topo = engine.build_topology("0xempty", [])
    assert len(topo.nodes) == 1
    assert len(topo.edges) == 0
    assert topo.unique_counterparties == 0


def test_graph_analytics_with_transactions():
    engine = GraphAnalyticsEngine()
    target = "0xtarget"
    c1 = "0xcounterparty1"
    c2 = "0xcounterparty2"

    txs = [
        DomainTransactionEvent(
            tx_hash="0x1",
            chain=ChainEcosystem.ETHEREUM,
            from_address=c1,
            to_address=target,
            value_native=5.0,
            fee_native=0.001,
            timestamp_utc=datetime.now(timezone.utc),
        ),
        DomainTransactionEvent(
            tx_hash="0x2",
            chain=ChainEcosystem.ETHEREUM,
            from_address=target,
            to_address=c2,
            value_native=2.5,
            fee_native=0.001,
            timestamp_utc=datetime.now(timezone.utc),
        ),
    ]

    topo = engine.build_topology(target, txs)
    assert len(topo.nodes) == 3
    assert len(topo.edges) == 2
    assert topo.total_volume == 7.5
    assert topo.unique_counterparties == 2

    # Verify PageRank was calculated
    for node in topo.nodes:
        assert node.page_rank > 0.0

    # Verify Cytoscape JSON conversion
    cy_data = engine.to_cytoscape_json(topo)
    assert "elements" in cy_data
    assert len(cy_data["elements"]["nodes"]) == 3
    assert len(cy_data["elements"]["edges"]) == 2


def test_graph_analytics_with_bridges_and_persona():
    engine = GraphAnalyticsEngine()
    target = "0xtarget"
    c1 = "0xcounterparty"
    dest = "0xdest"

    txs = [
        DomainTransactionEvent(
            tx_hash="0x1",
            chain=ChainEcosystem.ETHEREUM,
            from_address=c1,
            to_address=target,
            value_native=1.0,
            fee_native=0.001,
            timestamp_utc=datetime.now(timezone.utc),
        ),
    ]

    bridges = [
        CrossChainBridgeEvent(
            bridge_name="Stargate",
            source_chain=ChainEcosystem.ETHEREUM,
            source_tx_hash="0xb1",
            source_address=target,
            destination_chain=ChainEcosystem.ARBITRUM,
            destination_address=dest,
            token_symbol="USDC",
            amount=500.0,
            timestamp_utc=datetime.now(timezone.utc),
        ),
    ]

    topo = engine.build_topology(target, txs, bridge_events=bridges)
    assert any(n.node_type == "bridge" for n in topo.nodes)
    assert any(e.is_cross_chain for e in topo.edges)
    cy = engine.to_cytoscape_json(topo)
    assert len(cy["elements"]["nodes"]) >= 3
