"""
Application Use Cases for crypto-graph API.
Orchestrates domain services, resilient RPC rotators, and local storage.
"""

from typing import Any, Dict, List, Optional
from libs.blockchain_contracts.models import (
    Address,
    ChainEcosystem,
    CrossChainBridgeEvent,
    DomainTransactionEvent,
    GraphTopology,
    PersonaProfile,
)
from ..domain.analytics import GraphAnalyticsEngine
from ..domain.clustering import PersonaClusteringEngine
from ..domain.ports import GraphStoragePort, RpcProviderPort


class CryptoGraphUseCases:
    def __init__(
        self,
        rpc_provider: RpcProviderPort,
        storage: GraphStoragePort,
        analytics: Optional[GraphAnalyticsEngine] = None,
        clustering: Optional[PersonaClusteringEngine] = None,
    ):
        self.rpc = rpc_provider
        self.storage = storage
        self.analytics = analytics or GraphAnalyticsEngine()
        self.clustering = clustering or PersonaClusteringEngine()

    async def lookup_address(self, raw_address: str) -> Dict[str, Any]:
        """Validates, detects ecosystem, and fetches initial transactions."""
        address = Address.from_str(raw_address)
        txs = await self.rpc.fetch_transactions(address.normalized_address)
        self.storage.save_transactions(txs)

        total_val = sum(tx.value_native for tx in txs)
        return {
            "address": address.normalized_address,
            "raw_address": address.raw_address,
            "detected_ecosystems": [e.value for e in address.detected_ecosystems],
            "transaction_count": len(txs),
            "total_volume_native": round(total_val, 4),
            "recent_transactions": [tx.model_dump(mode="json") for tx in txs[:5]],
        }

    async def get_graph_topology(self, raw_address: str) -> Dict[str, Any]:
        """Computes NetworkX graph and returns Cytoscape.js JSON payload."""
        address = Address.from_str(raw_address)
        txs = self.storage.get_transactions_for_address(address.normalized_address)
        if not txs:
            txs = await self.rpc.fetch_transactions(address.normalized_address)
            self.storage.save_transactions(txs)

        bridges = await self.rpc.fetch_bridge_events(address.normalized_address)
        persona = self.clustering.compute_persona(address.normalized_address, txs, bridges)

        topology = self.analytics.build_topology(
            target_address=address.normalized_address,
            transactions=txs,
            bridge_events=bridges,
            persona=persona,
        )
        return self.analytics.to_cytoscape_json(topology)

    async def get_persona_profile(self, raw_address: str) -> Dict[str, Any]:
        """Executes multi-heuristic clustering and returns persona profile."""
        address = Address.from_str(raw_address)
        txs = self.storage.get_transactions_for_address(address.normalized_address)
        if not txs:
            txs = await self.rpc.fetch_transactions(address.normalized_address)
            self.storage.save_transactions(txs)

        bridges = await self.rpc.fetch_bridge_events(address.normalized_address)
        persona = self.clustering.compute_persona(address.normalized_address, txs, bridges)
        self.storage.save_persona_profile(persona)

        return persona.model_dump(mode="json")

    async def get_cross_chain_flows(self, raw_address: str) -> List[Dict[str, Any]]:
        """Returns detected cross-chain bridge flows for the address."""
        address = Address.from_str(raw_address)
        bridges = await self.rpc.fetch_bridge_events(address.normalized_address)
        return [b.model_dump(mode="json") for b in bridges]
