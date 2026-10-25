"""
Multi-heuristic persona clustering engine.
Pure domain logic: clusters multiple public addresses into a unified persona with Bayesian confidence scoring.
"""

from datetime import datetime, timezone
from typing import Dict, List, Set, Tuple
from libs.blockchain_contracts.models import (
    Address,
    AttributionEvidence,
    ChainEcosystem,
    ClusteredWallet,
    ClusteringHeuristicType,
    CrossChainBridgeEvent,
    DomainTransactionEvent,
    PersonaProfile,
)


class PersonaClusteringEngine:
    """
    Applies 4 distinct heuristic strategies to discover multi-wallet clusters:
    1. CEX Deposit Address Reuse (default weight 0.85)
    2. Cross-Chain Bridge Correlation (default weight 0.80)
    3. Co-Funding & Temporal Coordination (default weight 0.70)
    4. UTXO Common-Spend (default weight 0.90)
    """

    HEURISTIC_WEIGHTS = {
        ClusteringHeuristicType.UTXO_COMMON_SPEND: 0.90,
        ClusteringHeuristicType.CEX_DEPOSIT_REUSE: 0.85,
        ClusteringHeuristicType.BRIDGE_CORRELATION: 0.80,
        ClusteringHeuristicType.CO_FUNDING_TEMPORAL: 0.70,
    }

    def __init__(self, config_service=None):
        self.config_service = config_service

    def get_weight(self, heuristic: ClusteringHeuristicType) -> float:
        if self.config_service:
            key_map = {
                ClusteringHeuristicType.CEX_DEPOSIT_REUSE: "heuristics.cex_deposit_weight",
                ClusteringHeuristicType.BRIDGE_CORRELATION: "heuristics.bridge_correlation_weight",
                ClusteringHeuristicType.CO_FUNDING_TEMPORAL: "heuristics.co_funding_weight",
                ClusteringHeuristicType.UTXO_COMMON_SPEND: "heuristics.utxo_common_spend_weight",
            }
            config_key = key_map.get(heuristic)
            if config_key:
                return self.config_service.get_float(config_key, self.HEURISTIC_WEIGHTS[heuristic])
        return self.HEURISTIC_WEIGHTS[heuristic]

    def compute_persona(
        self,
        target_address: str,
        transactions: List[DomainTransactionEvent],
        bridge_events: List[CrossChainBridgeEvent],
    ) -> PersonaProfile:
        target_norm = target_address.lower()
        clustered_wallets: Dict[str, ClusteredWallet] = {}
        all_evidences: List[AttributionEvidence] = []

        # Ensure target address is represented in the cluster
        now = datetime.now(timezone.utc)
        target_wallet = ClusteredWallet(
            address=target_norm,
            chain=ChainEcosystem.ETHEREUM if target_norm.startswith("0x") else ChainEcosystem.BITCOIN,
            first_seen_utc=now,
            last_seen_utc=now,
            evidences=[],
        )
        clustered_wallets[target_norm] = target_wallet

        # Heuristic 1: CEX Deposit Address Reuse
        # Find external deposit addresses that target deposited to
        deposits_by_target = {
            tx.to_address.lower()
            for tx in transactions
            if tx.from_address.lower() == target_norm and tx.to_address.lower() != target_norm
        }

        # Check if any other transactions share this same deposit address
        for tx in transactions:
            from_addr = tx.from_address.lower()
            to_addr = tx.to_address.lower()
            if from_addr != target_norm and to_addr in deposits_by_target:
                evidence = AttributionEvidence(
                    heuristic=ClusteringHeuristicType.CEX_DEPOSIT_REUSE,
                    description=f"Shared centralized deposit destination '{to_addr[:10]}...' with target",
                    confidence_weight=self.get_weight(ClusteringHeuristicType.CEX_DEPOSIT_REUSE),
                    related_tx_hashes=[tx.tx_hash],
                    timestamp_utc=tx.timestamp_utc,
                )
                all_evidences.append(evidence)
                self._add_or_update_wallet(clustered_wallets, from_addr, tx.chain, tx.timestamp_utc, evidence)

        # Heuristic 2: Cross-Chain Bridge Correlation
        # Match source and destination addresses from bridge events
        for bridge in bridge_events:
            src = bridge.source_address.lower()
            dst = bridge.destination_address.lower()
            if src == target_norm and dst != target_norm:
                evidence = AttributionEvidence(
                    heuristic=ClusteringHeuristicType.BRIDGE_CORRELATION,
                    description=f"Cross-chain {bridge.bridge_name} bridge transfer to destination '{dst[:10]}...' on {bridge.destination_chain.value}",
                    confidence_weight=self.get_weight(ClusteringHeuristicType.BRIDGE_CORRELATION),
                    related_tx_hashes=[bridge.source_tx_hash],
                    timestamp_utc=bridge.timestamp_utc,
                )
                all_evidences.append(evidence)
                self._add_or_update_wallet(clustered_wallets, dst, bridge.destination_chain, bridge.timestamp_utc, evidence)
            elif dst == target_norm and src != target_norm:
                evidence = AttributionEvidence(
                    heuristic=ClusteringHeuristicType.BRIDGE_CORRELATION,
                    description=f"Received cross-chain {bridge.bridge_name} bridge transfer from '{src[:10]}...' on {bridge.source_chain.value}",
                    confidence_weight=self.get_weight(ClusteringHeuristicType.BRIDGE_CORRELATION),
                    related_tx_hashes=[bridge.source_tx_hash],
                    timestamp_utc=bridge.timestamp_utc,
                )
                all_evidences.append(evidence)
                self._add_or_update_wallet(clustered_wallets, src, bridge.source_chain, bridge.timestamp_utc, evidence)

        # Heuristic 3: Co-Funding & Direct Transfers
        max_funding = self.config_service.get_float("heuristics.co_funding_max_value", 1.0) if self.config_service else 1.0
        for tx in transactions:
            from_addr = tx.from_address.lower()
            to_addr = tx.to_address.lower()
            # Direct reciprocal transfers with small value (< max_funding ETH) or testing values
            if from_addr == target_norm and to_addr != target_norm and tx.value_native <= max_funding and not tx.is_contract_call:
                evidence = AttributionEvidence(
                    heuristic=ClusteringHeuristicType.CO_FUNDING_TEMPORAL,
                    description=f"Direct seed funding transfer of {tx.value_native} {tx.token_symbol} to '{to_addr[:10]}...'",
                    confidence_weight=self.get_weight(ClusteringHeuristicType.CO_FUNDING_TEMPORAL),
                    related_tx_hashes=[tx.tx_hash],
                    timestamp_utc=tx.timestamp_utc,
                )
                all_evidences.append(evidence)
                self._add_or_update_wallet(clustered_wallets, to_addr, tx.chain, tx.timestamp_utc, evidence)

        # Heuristic 4: UTXO Common-Spend (multi-input co-spend clustering)
        for tx in transactions:
            if tx.co_inputs and len(tx.co_inputs) > 1:
                co_inputs_lower = [addr.lower() for addr in tx.co_inputs]
                if target_norm in co_inputs_lower:
                    for other_input in co_inputs_lower:
                        if other_input != target_norm:
                            evidence = AttributionEvidence(
                                heuristic=ClusteringHeuristicType.UTXO_COMMON_SPEND,
                                description=f"UTXO multi-input co-spend in tx '{tx.tx_hash[:10]}...' with '{other_input[:10]}...'",
                                confidence_weight=self.get_weight(ClusteringHeuristicType.UTXO_COMMON_SPEND),
                                related_tx_hashes=[tx.tx_hash],
                                timestamp_utc=tx.timestamp_utc,
                            )
                            all_evidences.append(evidence)
                            self._add_or_update_wallet(clustered_wallets, other_input, tx.chain, tx.timestamp_utc, evidence)

        # Calculate Bayesian Noisy-OR confidence score: 1 - product(1 - w_i)
        if all_evidences:
            prob_independent_false = 1.0
            for ev in all_evidences:
                prob_independent_false *= (1.0 - ev.confidence_weight)
            confidence = round(min(1.0, max(0.0, 1.0 - prob_independent_false)), 4)
        else:
            baseline = self.config_service.get_float("heuristics.standalone_baseline_confidence", 0.50) if self.config_service else 0.50
            confidence = baseline  # Single standalone wallet baseline

        # Generate persona label and tags
        wallet_count = len(clustered_wallets)
        tags = ["active-trader"]
        if wallet_count > 1:
            tags.append("multi-wallet-persona")
        if any(e.heuristic == ClusteringHeuristicType.BRIDGE_CORRELATION for e in all_evidences):
            tags.append("cross-chain-operator")
        if any(e.heuristic == ClusteringHeuristicType.CEX_DEPOSIT_REUSE for e in all_evidences):
            tags.append("cex-clustered")
        if any(e.heuristic == ClusteringHeuristicType.UTXO_COMMON_SPEND for e in all_evidences):
            tags.append("utxo-clustered")

        persona_id = f"persona-{abs(hash(target_norm)):08x}"
        summary = (
            f"Persona {persona_id} clusters {wallet_count} address(es) across "
            f"{len(set(w.chain for w in clustered_wallets.values()))} network(s) "
            f"with {confidence * 100:.1f}% confidence."
        )

        return PersonaProfile(
            persona_id=persona_id,
            label=f"Persona {persona_id[:12]}",
            primary_address=target_norm,
            clustered_wallets=list(clustered_wallets.values()),
            confidence_score=confidence,
            tags=tags,
            summary=summary,
        )

    def _add_or_update_wallet(
        self,
        clustered_wallets: Dict[str, ClusteredWallet],
        address: str,
        chain: ChainEcosystem,
        timestamp_utc: datetime,
        evidence: AttributionEvidence,
    ) -> None:
        if address in clustered_wallets:
            wallet = clustered_wallets[address]
            wallet.evidences.append(evidence)
            if timestamp_utc < wallet.first_seen_utc:
                wallet.first_seen_utc = timestamp_utc
            if timestamp_utc > wallet.last_seen_utc:
                wallet.last_seen_utc = timestamp_utc
        else:
            clustered_wallets[address] = ClusteredWallet(
                address=address,
                chain=chain,
                first_seen_utc=timestamp_utc,
                last_seen_utc=timestamp_utc,
                evidences=[evidence],
            )
