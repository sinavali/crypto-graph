"""
Graph Analytics Engine powered by NetworkX.
Constructs directional multi-chain interaction graphs, computes topological metrics,
and produces Cytoscape.js ready visualization payloads.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import networkx as nx
from libs.blockchain_contracts.models import (
    ChainEcosystem,
    CrossChainBridgeEvent,
    DomainTransactionEvent,
    GraphEdge,
    GraphNode,
    GraphTopology,
    PersonaProfile,
)
from .entity_registry import (
    is_bridge_address,
    is_exchange_address,
    is_mixer_address,
    lookup_known_entity,
)


class GraphAnalyticsEngine:
    def build_topology(
        self,
        target_address: str,
        transactions: List[DomainTransactionEvent],
        bridge_events: Optional[List[CrossChainBridgeEvent]] = None,
        persona: Optional[PersonaProfile] = None,
    ) -> GraphTopology:
        target_norm = target_address.lower()
        bridge_events = bridge_events or []
        G = nx.DiGraph()

        # Track aggregation per node and edge
        node_types: Dict[str, str] = {target_norm: "target"}
        node_chains: Dict[str, ChainEcosystem] = {}
        edge_data: Dict[tuple, Dict[str, Any]] = {}
        total_volume = 0.0

        # Process transactions
        for tx in transactions:
            src = tx.from_address.lower()
            dst = tx.to_address.lower()
            total_volume += tx.value_native

            node_chains[src] = tx.chain
            node_chains[dst] = tx.chain

            # Determine entity category for src
            if src not in node_types:
                known_src = lookup_known_entity(src)
                if known_src:
                    node_types[src] = known_src.category
                elif is_mixer_address(src):
                    node_types[src] = "mixer"
                elif is_exchange_address(src):
                    node_types[src] = "exchange"
                elif is_bridge_address(src):
                    node_types[src] = "bridge"
                else:
                    node_types[src] = "counterparty"

            # Determine entity category for dst
            if dst not in node_types:
                known_dst = lookup_known_entity(dst)
                if known_dst:
                    node_types[dst] = known_dst.category
                elif is_mixer_address(dst):
                    node_types[dst] = "mixer"
                elif is_exchange_address(dst):
                    node_types[dst] = "exchange"
                elif is_bridge_address(dst):
                    node_types[dst] = "bridge"
                elif tx.is_contract_call:
                    node_types[dst] = "contract"
                else:
                    node_types[dst] = "counterparty"

            edge_key = (src, dst)
            if edge_key not in edge_data:
                edge_data[edge_key] = {
                    "tx_count": 0,
                    "volume": 0.0,
                    "first_seen": tx.timestamp_utc,
                    "last_seen": tx.timestamp_utc,
                    "is_cross_chain": False,
                    "bridge_name": None,
                    "token_symbol": tx.token_symbol,
                }
            e = edge_data[edge_key]
            e["tx_count"] += 1
            e["volume"] += tx.value_native
            if tx.timestamp_utc < e["first_seen"]:
                e["first_seen"] = tx.timestamp_utc
            if tx.timestamp_utc > e["last_seen"]:
                e["last_seen"] = tx.timestamp_utc

            G.add_edge(src, dst, weight=e["volume"] + 0.1)

        # Process cross-chain bridge events
        for bridge in bridge_events:
            src = bridge.source_address.lower()
            dst = bridge.destination_address.lower()
            bridge_node = f"bridge_{bridge.bridge_name.lower()}"
            node_types[bridge_node] = "bridge"
            node_chains[bridge_node] = bridge.source_chain

            # Link src -> bridge -> dst
            for u, v in [(src, bridge_node), (bridge_node, dst)]:
                edge_key = (u, v)
                if edge_key not in edge_data:
                    edge_data[edge_key] = {
                        "tx_count": 1,
                        "volume": bridge.amount,
                        "first_seen": bridge.timestamp_utc,
                        "last_seen": bridge.timestamp_utc,
                        "is_cross_chain": True,
                        "bridge_name": bridge.bridge_name,
                        "token_symbol": bridge.token_symbol,
                    }
                else:
                    e = edge_data[edge_key]
                    e["tx_count"] += 1
                    e["volume"] += bridge.amount
                G.add_edge(u, v, weight=bridge.amount + 0.1)

        if len(G) == 0:
            G.add_node(target_norm)
            node_chains[target_norm] = ChainEcosystem.ETHEREUM

        # Compute NetworkX topological metrics
        try:
            page_ranks = nx.pagerank(G, alpha=0.85, max_iter=100)
        except Exception:
            page_ranks = {n: 1.0 / len(G) for n in G.nodes()}

        degree_dict = dict(G.degree())

        # Map persona clustered addresses if available
        persona_addresses = set()
        persona_id = None
        if persona:
            persona_id = persona.persona_id
            persona_addresses = {w.address.lower() for w in persona.clustered_wallets}

        # Build GraphNode list with entity recognition & risk rating
        nodes: List[GraphNode] = []
        for node_id in G.nodes():
            chain = node_chains.get(node_id, ChainEcosystem.ETHEREUM)
            n_type = node_types.get(node_id, "counterparty")
            p_id = persona_id if node_id in persona_addresses else None

            known_ent = lookup_known_entity(node_id)
            if known_ent:
                if node_id == target_norm:
                    label = f"{known_ent.name} (Target)"
                else:
                    label = known_ent.name
                risk = known_ent.risk_level
                base_tags = list(known_ent.tags)
            elif node_id == target_norm:
                label = f"Target: {node_id[:6]}...{node_id[-4:]}"
                risk = "LOW"
                base_tags = ["target"]
            elif node_id.startswith("bridge_"):
                label = node_id.replace("bridge_", "").capitalize() + " Bridge"
                risk = "LOW"
                base_tags = ["cross-chain-bridge"]
            else:
                label = f"{node_id[:6]}...{node_id[-4:]}" if len(node_id) > 12 else node_id
                risk = "LOW"
                base_tags = []

            tags = list(base_tags)
            if node_id == target_norm and "target" not in tags:
                tags.append("target")
            if p_id and "persona-clustered" not in tags:
                tags.append("persona-clustered")
            if n_type == "mixer" and "privacy-mixer" not in tags:
                tags.append("privacy-mixer")
                risk = "HIGH"
            elif n_type == "exchange" and "cex-liquidity" not in tags:
                tags.append("cex-liquidity")

            nodes.append(
                GraphNode(
                    id=node_id,
                    address=node_id,
                    chain=chain,
                    label=label,
                    node_type=n_type,
                    degree=degree_dict.get(node_id, 0),
                    page_rank=round(page_ranks.get(node_id, 0.0), 6),
                    persona_id=p_id,
                    tags=tags,
                    risk_level=risk,
                )
            )

        # Build GraphEdge list
        edges: List[GraphEdge] = []
        for (u, v), d in edge_data.items():
            edge_id = f"edge_{u[:6]}_{v[:6]}_{abs(hash(u + v)) % 10000}"
            edges.append(
                GraphEdge(
                    id=edge_id,
                    source=u,
                    target=v,
                    tx_count=d["tx_count"],
                    total_volume_native=round(d["volume"], 4),
                    token_symbol=d.get("token_symbol", "ETH"),
                    is_cross_chain=d["is_cross_chain"],
                    bridge_name=d["bridge_name"],
                    first_seen_utc=d["first_seen"],
                    last_seen_utc=d["last_seen"],
                )
            )

        counterparties = len([n for n in nodes if n.node_type not in ("target", "bridge")])

        metrics = {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "density": round(nx.density(G), 4) if len(G) > 1 else 0.0,
            "connected_components": nx.number_weakly_connected_components(G),
        }

        return GraphTopology(
            nodes=nodes,
            edges=edges,
            target_address=target_norm,
            total_volume=round(total_volume, 4),
            unique_counterparties=counterparties,
            metrics=metrics,
        )

    def to_cytoscape_json(self, topology: GraphTopology) -> Dict[str, Any]:
        """Convert GraphTopology to Cytoscape.js format."""
        cy_nodes = []
        for n in topology.nodes:
            cy_nodes.append({
                "data": {
                    "id": n.id,
                    "label": n.label,
                    "address": n.address,
                    "chain": n.chain.value,
                    "node_type": n.node_type,
                    "degree": n.degree,
                    "page_rank": n.page_rank,
                    "persona_id": n.persona_id,
                    "tags": n.tags,
                    "risk_level": n.risk_level,
                }
            })

        cy_edges = []
        for e in topology.edges:
            cy_edges.append({
                "data": {
                    "id": e.id,
                    "source": e.source,
                    "target": e.target,
                    "tx_count": e.tx_count,
                    "volume": e.total_volume_native,
                    "is_cross_chain": e.is_cross_chain,
                    "bridge_name": e.bridge_name,
                }
            })

        return {
            "elements": {
                "nodes": cy_nodes,
                "edges": cy_edges,
            },
            "summary": {
                "target_address": topology.target_address,
                "total_volume": topology.total_volume,
                "unique_counterparties": topology.unique_counterparties,
                "metrics": topology.metrics,
            }
        }
