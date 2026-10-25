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
SATOSHI_BLOCK9 = "12c6DSiU4Rq3P4ZxziKxzrL5LmMBrzjrJX"
HAL_FINNEY_BTC = "1Q2TWJh9n0n2Wv6NuSx79J161ExHEVDb1"
SOLANA_SAMPLE = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
TRON_SAMPLE = "TL34sq8mSXTHi6n81qJ8Vn2X52Ssmr5x4d"
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
    
    # Vitalik transactions fixture (EVM)
    if norm == VITALIK_ETH.lower():
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

    # Satoshi Bitcoin UTXO Fixture (with multi-input co-spend)
    if norm in (SATOSHI_BTC.lower(), SATOSHI_BLOCK9.lower()):
        return [
            DomainTransactionEvent(
                tx_hash="4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b",
                chain=ChainEcosystem.BITCOIN,
                from_address="coinbase",
                to_address=SATOSHI_BTC,
                value_native=50.0,
                token_symbol="BTC",
                fee_native=0.0,
                timestamp_utc=datetime(2009, 1, 3, 18, 15, 5, tzinfo=timezone.utc),
                block_number=0,
            ),
            DomainTransactionEvent(
                tx_hash="f4184fc596403b9d638783cf57adfe4c75c605f6356fbc91338530e9831e9e16",
                chain=ChainEcosystem.BITCOIN,
                from_address=SATOSHI_BTC,
                to_address=HAL_FINNEY_BTC,
                value_native=10.0,
                token_symbol="BTC",
                fee_native=0.0001,
                timestamp_utc=datetime(2009, 1, 12, 3, 30, 25, tzinfo=timezone.utc),
                block_number=170,
                co_inputs=[SATOSHI_BTC, SATOSHI_BLOCK9],
            ),
            DomainTransactionEvent(
                tx_hash="a1075db55d416d3ca199f55b6084e2115b9345e16c5cf302fc80e9d5fbf5d48d",
                chain=ChainEcosystem.BITCOIN,
                from_address="coinbase",
                to_address=SATOSHI_BLOCK9,
                value_native=50.0,
                token_symbol="BTC",
                fee_native=0.0,
                timestamp_utc=datetime(2009, 1, 9, 2, 54, 25, tzinfo=timezone.utc),
                block_number=9,
            ),
        ]

    # Solana Sample Fixture
    if norm == SOLANA_SAMPLE.lower():
        return [
            DomainTransactionEvent(
                tx_hash="5VERv8NMvzbJMEkV8xnrLkEaWRtSz9CosKDYjCJjBRnbJLgp8uirBgmQpjKhoR4tjF3ZpRzrFmBV6UjKdiSZkQUc",
                chain=ChainEcosystem.SOLANA,
                from_address="5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1",
                to_address=SOLANA_SAMPLE,
                value_native=1500.0,
                token_symbol="SOL",
                fee_native=0.000005,
                timestamp_utc=datetime(2024, 2, 10, 14, 0, 0, tzinfo=timezone.utc),
                block_number=245000000,
            ),
            DomainTransactionEvent(
                tx_hash="4ubT7VzD7v6M7gq99kL9wT7v8NMvzbJMEkV8xnrLkEaWRtSz9CosKDYjCJjBRnbJLgp8uirBgmQpjKhoR4tjF3",
                chain=ChainEcosystem.SOLANA,
                from_address=SOLANA_SAMPLE,
                to_address="CuieVDEDtLo7FypA9SbLM9saXFdb1dsshveFi79ujvnG",
                value_native=250.0,
                token_symbol="SOL",
                fee_native=0.000005,
                timestamp_utc=datetime(2024, 2, 11, 16, 20, 0, tzinfo=timezone.utc),
                block_number=245010000,
                is_contract_call=True,
                method_name="raydium_swap",
            ),
        ]

    # Tron Sample Fixture
    if norm == TRON_SAMPLE.lower():
        return [
            DomainTransactionEvent(
                tx_hash="4f4a34b3e85f0f3531b4ce6ad19a8684ad332a67be0e6538a8e3df32f1465814",
                chain=ChainEcosystem.TRON,
                from_address="TG3XXyExBkPp9nzdajDZsozEu4MrDYUogV",
                to_address=TRON_SAMPLE,
                value_native=250000.0,
                token_symbol="TRX",
                fee_native=1.1,
                timestamp_utc=datetime(2024, 3, 1, 8, 30, 0, tzinfo=timezone.utc),
                block_number=59000000,
            ),
            DomainTransactionEvent(
                tx_hash="6d4b22c1e85f0f3531b4ce6ad19a8684ad332a67be0e6538a8e3df32f1465819",
                chain=ChainEcosystem.TRON,
                from_address=TRON_SAMPLE,
                to_address="TXJZv8NMvzbJMEkV8xnrLkEaWRtSz9CosKD",
                value_native=50000.0,
                token_symbol="TRX",
                fee_native=2.5,
                timestamp_utc=datetime(2024, 3, 2, 11, 0, 0, tzinfo=timezone.utc),
                block_number=59012000,
                is_contract_call=True,
                method_name="transferTRC20",
            ),
        ]

    # Cluster persona test fixture
    if norm in (CLUSTER_WALLET_A.lower(), CLUSTER_WALLET_B.lower(), CLUSTER_WALLET_C.lower()):
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
            chain=ChainEcosystem.ETHEREUM if norm.startswith("0x") else ChainEcosystem.BITCOIN,
            from_address=BINANCE_HOT_WALLET,
            to_address=norm,
            value_native=12.5,
            token_symbol="ETH" if norm.startswith("0x") else "BTC",
            fee_native=0.0015,
            timestamp_utc=datetime(2024, 4, 1, 12, 0, 0, tzinfo=timezone.utc),
            block_number=19500000,
        ),
        DomainTransactionEvent(
            tx_hash=f"0x88{abs(hash(norm + 'tx2')):062x}"[:66],
            chain=ChainEcosystem.ETHEREUM if norm.startswith("0x") else ChainEcosystem.BITCOIN,
            from_address=norm,
            to_address=UNISWAP_V3_ROUTER,
            value_native=3.2,
            token_symbol="ETH" if norm.startswith("0x") else "BTC",
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
