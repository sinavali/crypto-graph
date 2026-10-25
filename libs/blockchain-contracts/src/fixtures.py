"""
Deterministic offline fixtures for unit, integration, and end-to-end replay testing.
Enables 100% hermetic CI execution with zero live RPC/network dependency.
"""

from datetime import datetime, timezone
from typing import Dict, List
from .models import (
    Address,
    AddressType,
    ChainEcosystem,
    CrossChainBridgeEvent,
    DomainTransactionEvent,
    PersonaProfile,
    ClusteredWallet,
    AttributionEvidence,
    ClusteringHeuristicType,
)

# Curated canonical addresses
VITALIK_ETH = "0xd8da6bf26964af9d7eed9e03e53415d37aa96045"
VITALIK_ARB = "0xd8da6bf26964af9d7eed9e03e53415d37aa96045"
SATOSHI_BTC = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
BINANCE_HOT_WALLET = "0x28c6c06298d514db089934071355e5743bf21d60"
COINBASE_HOT_WALLET = "0x503828976d22510aad0201ac7ec88293211d23dc"
STARGATE_ROUTER = "0x8731d54e9d02c271bb81737cd9d18c622f484636"
UNISWAP_V3_ROUTER = "0xe592427a0aece92de3edee1f18e0157c05861564"

# Clustered test persona addresses
CLUSTER_WALLET_A = "0x1111111111111111111111111111111111111111"
CLUSTER_WALLET_B = "0x2222222222222222222222222222222222222222"
CLUSTER_WALLET_C = "0x3333333333333333333333333333333333333333"
CEX_SHARED_DEPOSIT = "0x9999999999999999999999999999999999999999"


def get_fixture_transactions(address: str) -> List[DomainTransactionEvent]:
    norm = address.lower()
    
    # Vitalik transactions fixture
    if norm == VITALIK_ETH:
        return [
            DomainTransactionEvent(
                tx_hash="0xaa01010101010101010101010101010101010101010101010101010101010101",
                chain=ChainEcosystem.ETHEREUM,
                from_address=BINANCE_HOT_WALLET,
                to_address=VITALIK_ETH,
                value_native=100.0,
                token_symbol="ETH",
                fee_native=0.0021,
                timestamp_utc=datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
                block_number=19000000,
            ),
            DomainTransactionEvent(
                tx_hash="0xaa02020202020202020202020202020202020202020202020202020202020202",
                chain=ChainEcosystem.ETHEREUM,
                from_address=VITALIK_ETH,
                to_address=UNISWAP_V3_ROUTER,
                value_native=25.0,
                token_symbol="ETH",
                fee_native=0.0054,
                timestamp_utc=datetime(2024, 1, 16, 14, 30, 0, tzinfo=timezone.utc),
                block_number=19000500,
                is_contract_call=True,
                method_name="exactInputSingle",
            ),
            DomainTransactionEvent(
                tx_hash="0xaa03030303030303030303030303030303030303030303030303030303030303",
                chain=ChainEcosystem.ETHEREUM,
                from_address=VITALIK_ETH,
                to_address=STARGATE_ROUTER,
                value_native=10.0,
                token_symbol="ETH",
                fee_native=0.0035,
                timestamp_utc=datetime(2024, 1, 18, 9, 15, 0, tzinfo=timezone.utc),
                block_number=19001200,
                is_contract_call=True,
                method_name="swapETH",
            ),
            DomainTransactionEvent(
                tx_hash="0xaa04040404040404040404040404040404040404040404040404040404040404",
                chain=ChainEcosystem.ETHEREUM,
                from_address=COINBASE_HOT_WALLET,
                to_address=VITALIK_ETH,
                value_native=50.0,
                token_symbol="ETH",
                fee_native=0.0019,
                timestamp_utc=datetime(2024, 2, 1, 10, 0, 0, tzinfo=timezone.utc),
                block_number=19100000,
            ),
        ]

    # Cluster persona test fixture
    if norm in (CLUSTER_WALLET_A, CLUSTER_WALLET_B, CLUSTER_WALLET_C):
        return [
            DomainTransactionEvent(
                tx_hash="0xcc01010101010101010101010101010101010101010101010101010101010101",
                chain=ChainEcosystem.ETHEREUM,
                from_address=CLUSTER_WALLET_A,
                to_address=CEX_SHARED_DEPOSIT,
                value_native=5.0,
                token_symbol="ETH",
                fee_native=0.001,
                timestamp_utc=datetime(2024, 3, 1, 10, 0, 0, tzinfo=timezone.utc),
                block_number=19200000,
            ),
            DomainTransactionEvent(
                tx_hash="0xcc02020202020202020202020202020202020202020202020202020202020202",
                chain=ChainEcosystem.ETHEREUM,
                from_address=CLUSTER_WALLET_B,
                to_address=CEX_SHARED_DEPOSIT,
                value_native=7.5,
                token_symbol="ETH",
                fee_native=0.001,
                timestamp_utc=datetime(2024, 3, 1, 10, 25, 0, tzinfo=timezone.utc),
                block_number=19200100,
            ),
            DomainTransactionEvent(
                tx_hash="0xcc03030303030303030303030303030303030303030303030303030303030303",
                chain=ChainEcosystem.ETHEREUM,
                from_address=CLUSTER_WALLET_A,
                to_address=CLUSTER_WALLET_C,
                value_native=1.0,
                token_symbol="ETH",
                fee_native=0.0008,
                timestamp_utc=datetime(2024, 3, 2, 8, 0, 0, tzinfo=timezone.utc),
                block_number=19205000,
            ),
        ]

    # Default synthetic fallback for generic queries
    return [
        DomainTransactionEvent(
            tx_hash=f"0x99{abs(hash(norm)):062x}"[:66],
            chain=ChainEcosystem.ETHEREUM,
            from_address=BINANCE_HOT_WALLET,
            to_address=norm,
            value_native=12.5,
            token_symbol="ETH",
            fee_native=0.0015,
            timestamp_utc=datetime(2024, 4, 1, 12, 0, 0, tzinfo=timezone.utc),
            block_number=19500000,
        ),
        DomainTransactionEvent(
            tx_hash=f"0x88{abs(hash(norm + 'tx2')):062x}"[:66],
            chain=ChainEcosystem.ETHEREUM,
            from_address=norm,
            to_address=UNISWAP_V3_ROUTER,
            value_native=3.2,
            token_symbol="ETH",
            fee_native=0.003,
            timestamp_utc=datetime(2024, 4, 2, 16, 45, 0, tzinfo=timezone.utc),
            block_number=19500800,
            is_contract_call=True,
            method_name="swap",
        ),
    ]


def get_fixture_bridges() -> List[CrossChainBridgeEvent]:
    return [
        CrossChainBridgeEvent(
            bridge_name="Stargate",
            source_chain=ChainEcosystem.ETHEREUM,
            source_tx_hash="0xaa03030303030303030303030303030303030303030303030303030303030303",
            source_address=VITALIK_ETH,
            destination_chain=ChainEcosystem.ARBITRUM,
            destination_tx_hash="0xbb03030303030303030303030303030303030303030303030303030303030303",
            destination_address=VITALIK_ETH,
            token_symbol="ETH",
            amount=10.0,
            timestamp_utc=datetime(2024, 1, 18, 9, 22, 0, tzinfo=timezone.utc),
            status="COMPLETED",
        ),
        CrossChainBridgeEvent(
            bridge_name="Across",
            source_chain=ChainEcosystem.POLYGON,
            source_tx_hash="0xdd01010101010101010101010101010101010101010101010101010101010101",
            source_address=CLUSTER_WALLET_A,
            destination_chain=ChainEcosystem.OPTIMISM,
            destination_tx_hash="0xee01010101010101010101010101010101010101010101010101010101010101",
            destination_address=CLUSTER_WALLET_B,
            token_symbol="USDC",
            amount=5000.0,
            timestamp_utc=datetime(2024, 3, 5, 15, 10, 0, tzinfo=timezone.utc),
            status="COMPLETED",
        ),
    ]
