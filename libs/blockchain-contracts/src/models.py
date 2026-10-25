"""
Domain contracts, value objects, and schemas for crypto-graph.
Pure domain logic: zero persistence or UI dependencies. All timestamps are strictly UTC.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class ChainEcosystem(str, Enum):
    # EVM Chains
    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    BASE = "base"
    BSC = "bsc"
    AVALANCHE = "avalanche"
    FANTOM = "fantom"
    ZKSYNC = "zksync"
    LINEA = "linea"
    SCROLL = "scroll"
    CRONOS = "cronos"
    MANTLE = "mantle"
    BLAST = "blast"

    # Non-EVM Ecosystems
    BITCOIN = "bitcoin"
    LITECOIN = "litecoin"
    DOGECOIN = "dogecoin"
    SOLANA = "solana"
    TRON = "tron"
    COSMOS = "cosmos"
    NEAR = "near"


class AddressType(str, Enum):
    EOA = "eoa"
    CONTRACT = "contract"
    EXCHANGE_DEPOSIT = "exchange_deposit"
    BRIDGE_VAULT = "bridge_vault"
    UNKNOWN = "unknown"


class TokenType(str, Enum):
    NATIVE = "native"
    ERC20 = "erc20"
    SPL = "spl"
    TRC20 = "trc20"
    UTXO = "utxo"


class Address(BaseModel):
    raw_address: str
    normalized_address: str
    detected_ecosystems: List[ChainEcosystem] = Field(default_factory=list)
    address_type: AddressType = AddressType.UNKNOWN

    @classmethod
    def from_str(cls, addr_str: str) -> "Address":
        cleaned = addr_str.strip()
        detected: List[ChainEcosystem] = []
        normalized = cleaned

        # EVM address heuristic: 0x followed by 40 hex chars
        if re.match(r"^0x[a-fA-F0-9]{40}$", cleaned):
            normalized = cleaned.lower()
            detected = [
                ChainEcosystem.ETHEREUM,
                ChainEcosystem.ARBITRUM,
                ChainEcosystem.OPTIMISM,
                ChainEcosystem.BASE,
                ChainEcosystem.POLYGON,
                ChainEcosystem.BSC,
                ChainEcosystem.AVALANCHE,
                ChainEcosystem.FANTOM,
                ChainEcosystem.ZKSYNC,
                ChainEcosystem.LINEA,
                ChainEcosystem.SCROLL,
                ChainEcosystem.CRONOS,
                ChainEcosystem.MANTLE,
                ChainEcosystem.BLAST,
            ]
        # Bitcoin UTXO (Legacy 1..., Segwit 3..., Bech32 bc1...)
        elif re.match(r"^(1|3)[a-km-zA-HJ-NP-Z1-9]{25,34}$", cleaned) or re.match(r"^bc1[a-z0-9]{39,59}$", cleaned):
            normalized = cleaned
            detected = [ChainEcosystem.BITCOIN]
        # Tron (Base58Check starts with T, 34 chars)
        elif re.match(r"^T[a-km-zA-HJ-NP-Z1-9]{33}$", cleaned):
            normalized = cleaned
            detected = [ChainEcosystem.TRON]
        # Solana (Base58 encoded, 32-44 alphanumeric chars, does not contain 0, O, I, l)
        elif re.match(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$", cleaned):
            normalized = cleaned
            detected = [ChainEcosystem.SOLANA]
        # Cosmos (cosmos1...)
        elif re.match(r"^cosmos1[a-z0-9]{38}$", cleaned):
            normalized = cleaned.lower()
            detected = [ChainEcosystem.COSMOS]
        # Near (ends with .near or 64 hex chars)
        elif cleaned.endswith(".near") or re.match(r"^[a-f0-9]{64}$", cleaned):
            normalized = cleaned.lower()
            detected = [ChainEcosystem.NEAR]
        else:
            normalized = cleaned.lower()
            detected = [ChainEcosystem.ETHEREUM]

        return cls(
            raw_address=cleaned,
            normalized_address=normalized,
            detected_ecosystems=detected,
            address_type=AddressType.EOA,
        )


class DomainTransactionEvent(BaseModel):
    tx_hash: str
    chain: ChainEcosystem
    from_address: str
    to_address: str
    value_native: float = 0.0
    token_symbol: str = "NATIVE"
    token_value: float = 0.0
    fee_native: float = 0.0
    timestamp_utc: datetime
    block_number: int = 0
    is_contract_call: bool = False
    method_name: Optional[str] = None
    co_inputs: List[str] = Field(default_factory=list)

    @field_validator("timestamp_utc")
    @classmethod
    def ensure_utc(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc)


class CrossChainBridgeEvent(BaseModel):
    bridge_name: str  # Stargate, Across, Wormhole, Hop, Axelar
    source_chain: ChainEcosystem
    source_tx_hash: str
    source_address: str
    destination_chain: ChainEcosystem
    destination_tx_hash: Optional[str] = None
    destination_address: str
    token_symbol: str
    amount: float
    timestamp_utc: datetime
    status: str = "COMPLETED"

    @field_validator("timestamp_utc")
    @classmethod
    def ensure_utc(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc)


class ClusteringHeuristicType(str, Enum):
    CEX_DEPOSIT_REUSE = "cex_deposit_reuse"
    BRIDGE_CORRELATION = "bridge_correlation"
    CO_FUNDING_TEMPORAL = "co_funding_temporal"
    UTXO_COMMON_SPEND = "utxo_common_spend"


class AttributionEvidence(BaseModel):
    heuristic: ClusteringHeuristicType
    description: str
    confidence_weight: float = Field(ge=0.0, le=1.0)
    related_tx_hashes: List[str] = Field(default_factory=list)
    timestamp_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ClusteredWallet(BaseModel):
    address: str
    chain: ChainEcosystem
    first_seen_utc: datetime
    last_seen_utc: datetime
    evidences: List[AttributionEvidence] = Field(default_factory=list)


class PersonaProfile(BaseModel):
    persona_id: str
    label: str
    primary_address: str
    clustered_wallets: List[ClusteredWallet] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)
    tags: List[str] = Field(default_factory=list)
    summary: str = ""
    created_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GraphNode(BaseModel):
    id: str
    address: str
    chain: ChainEcosystem
    label: str
    node_type: str = "counterparty"  # target, counterparty, bridge, exchange, contract
    degree: int = 0
    page_rank: float = 0.0
    persona_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    tx_count: int = 1
    total_volume_native: float = 0.0
    token_symbol: str = "NATIVE"
    is_cross_chain: bool = False
    bridge_name: Optional[str] = None
    first_seen_utc: datetime
    last_seen_utc: datetime


class GraphTopology(BaseModel):
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
    target_address: str
    total_volume: float = 0.0
    unique_counterparties: int = 0
    metrics: Dict[str, Any] = Field(default_factory=dict)
