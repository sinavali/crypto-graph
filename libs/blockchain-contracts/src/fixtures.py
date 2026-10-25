"""
Deterministic offline fixtures for unit, integration, and end-to-end replay testing.
Enables 100% hermetic CI execution with zero live RPC/network dependency.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
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
TORNADO_01_ETH = "0xa160cdab225685da1d56aa342ad8841c3b53f291"

BINANCE_HOT_WALLET = "0x28c6c06298d514db089934071355e5743bf21d60"
COINBASE_HOT_WALLET = "0x503828976d22510aad0201ac7ec88293211d23dc"
KRAKEN_HOT_WALLET = "0x2910543af39aba0cd09dbb2d50200b3e800a63d2"
STARGATE_ROUTER = "0x8731d54e9d02c271bb81737cd9d18c622f484636"
ACROSS_SPOKE = "0x5c7bcd6e7de5423a257d81b442095a1a6ced35c5"
UNISWAP_V3_ROUTER = "0xe592427a0aece92de3edee1f18e0157c05861564"
CURVE_3POOL = "0xbebc44782c7db0a1a60cb6fe97d0b483032ff1c7"

# Clustered test persona addresses
CLUSTER_WALLET_A = "0x1111111111111111111111111111111111111111"
CLUSTER_WALLET_B = "0x2222222222222222222222222222222222222222"
CLUSTER_WALLET_C = "0x3333333333333333333333333333333333333333"
CEX_SHARED_DEPOSIT = "0x9999999999999999999999999999999999999999"


def get_fixture_transactions(address: str) -> List[DomainTransactionEvent]:
    norm = address.lower()
    
    # Tornado Cash 0.1 ETH Pool Fixture (Rich Multi-Chain & Multi-Hop Network)
    if norm == TORNADO_01_ETH:
        base_time = datetime(2024, 4, 10, 8, 0, 0, tzinfo=timezone.utc)
        depositor_1 = "0xc4352b572f7d598dc175631a60071685b791c7cd"
        depositor_2 = "0x8589427373d6d84e98730d7795d8f6f8731fda16"
        depositor_3 = "0x7777777777777777777777777777777777777777"
        withdrawer_1 = "0x3a10427373d6d84e98730d7795d8f6f8731fbb99"
        withdrawer_2 = "0x4b20427373d6d84e98730d7795d8f6f8731fcc88"
        relayer_arb = "0x5c30427373d6d84e98730d7795d8f6f8731fdd77"

        txs = [
            # Inflow 1: Depositor 1 deposits 0.1 ETH
            DomainTransactionEvent(
                tx_hash="0xb490c334147ce18fc84f74e043a37c2f3f2333f16aed6614f86021c915c9b5c7",
                chain=ChainEcosystem.ETHEREUM,
                from_address=depositor_1,
                to_address=TORNADO_01_ETH,
                value_native=0.1,
                token_symbol="ETH",
                fee_native=0.0035,
                timestamp_utc=base_time,
                block_number=19600000,
                is_contract_call=True,
                method_name="deposit",
            ),
            # Inflow 2: Depositor 2 deposits 0.1 ETH
            DomainTransactionEvent(
                tx_hash="0xef9055b8b3667983a2fc0505b003db3419340637445375f1e64dde91cf30c2af",
                chain=ChainEcosystem.ETHEREUM,
                from_address=depositor_2,
                to_address=TORNADO_01_ETH,
                value_native=0.1,
                token_symbol="ETH",
                fee_native=0.0032,
                timestamp_utc=base_time + timedelta(hours=2),
                block_number=19600500,
                is_contract_call=True,
                method_name="deposit",
            ),
            # Inflow 3: Depositor 3 deposits 0.1 ETH
            DomainTransactionEvent(
                tx_hash="0xda1055b8b3667983a2fc0505b003db3419340637445375f1e64dde91cf30c2b0",
                chain=ChainEcosystem.ETHEREUM,
                from_address=depositor_3,
                to_address=TORNADO_01_ETH,
                value_native=0.1,
                token_symbol="ETH",
                fee_native=0.0031,
                timestamp_utc=base_time + timedelta(hours=3),
                block_number=19600700,
                is_contract_call=True,
                method_name="deposit",
            ),
            # Outflow 1: Mixer withdraws 0.1 ETH to Withdrawer 1
            DomainTransactionEvent(
                tx_hash="0xfa2055b8b3667983a2fc0505b003db3419340637445375f1e64dde91cf30c2c1",
                chain=ChainEcosystem.ETHEREUM,
                from_address=TORNADO_01_ETH,
                to_address=withdrawer_1,
                value_native=0.1,
                token_symbol="ETH",
                fee_native=0.0041,
                timestamp_utc=base_time + timedelta(hours=12),
                block_number=19602500,
                is_contract_call=True,
                method_name="withdraw",
            ),
            # Outflow 2: Mixer withdraws 0.1 ETH to Withdrawer 2
            DomainTransactionEvent(
                tx_hash="0xfb3055b8b3667983a2fc0505b003db3419340637445375f1e64dde91cf30c2d2",
                chain=ChainEcosystem.ETHEREUM,
                from_address=TORNADO_01_ETH,
                to_address=withdrawer_2,
                value_native=0.1,
                token_symbol="ETH",
                fee_native=0.0039,
                timestamp_utc=base_time + timedelta(hours=14),
                block_number=19603000,
                is_contract_call=True,
                method_name="withdraw",
            ),
            # 2-Hop Interconnections: Depositor 1 was funded by Binance
            DomainTransactionEvent(
                tx_hash="0xcc01000100010001000100010001000100010001000100010001000100010001",
                chain=ChainEcosystem.ETHEREUM,
                from_address=BINANCE_HOT_WALLET,
                to_address=depositor_1,
                value_native=5.0,
                token_symbol="ETH",
                fee_native=0.0012,
                timestamp_utc=base_time - timedelta(days=1),
                block_number=19585000,
            ),
            # 2-Hop Interconnections: Depositor 2 was funded by Kraken
            DomainTransactionEvent(
                tx_hash="0xcc02000200020002000200020002000200020002000200020002000200020002",
                chain=ChainEcosystem.ETHEREUM,
                from_address=KRAKEN_HOT_WALLET,
                to_address=depositor_2,
                value_native=10.0,
                token_symbol="ETH",
                fee_native=0.0015,
                timestamp_utc=base_time - timedelta(days=2),
                block_number=19570000,
            ),
            # 2-Hop Interconnections: Withdrawer 1 swaps 0.1 ETH on Uniswap V3
            DomainTransactionEvent(
                tx_hash="0xcc03000300030003000300030003000300030003000300030003000300030003",
                chain=ChainEcosystem.ETHEREUM,
                from_address=withdrawer_1,
                to_address=UNISWAP_V3_ROUTER,
                value_native=0.1,
                token_symbol="ETH",
                fee_native=0.0028,
                timestamp_utc=base_time + timedelta(hours=15),
                block_number=19603200,
                is_contract_call=True,
                method_name="exactInputSingle",
            ),
            # 2-Hop Interconnections: Withdrawer 1 deposits proceeds into Coinbase Prime
            DomainTransactionEvent(
                tx_hash="0xcc04000400040004000400040004000400040004000400040004000400040004",
                chain=ChainEcosystem.ETHEREUM,
                from_address=withdrawer_1,
                to_address=COINBASE_HOT_WALLET,
                value_native=0.095,
                token_symbol="ETH",
                fee_native=0.0011,
                timestamp_utc=base_time + timedelta(hours=16),
                block_number=19603400,
            ),
            # 2-Hop Interconnections: Withdrawer 2 routes into Stargate Bridge to Arbitrum
            DomainTransactionEvent(
                tx_hash="0xcc05000500050005000500050005000500050005000500050005000500050005",
                chain=ChainEcosystem.ETHEREUM,
                from_address=withdrawer_2,
                to_address=STARGATE_ROUTER,
                value_native=0.1,
                token_symbol="ETH",
                fee_native=0.0035,
                timestamp_utc=base_time + timedelta(hours=17),
                block_number=19603600,
                is_contract_call=True,
                method_name="swapETH",
            ),
            # Arbitrum execution: Relayer bridge hop on Arbitrum L2
            DomainTransactionEvent(
                tx_hash="0xcc06000600060006000600060006000600060006000600060006000600060006",
                chain=ChainEcosystem.ARBITRUM,
                from_address=STARGATE_ROUTER,
                to_address=relayer_arb,
                value_native=0.098,
                token_symbol="ETH",
                fee_native=0.0002,
                timestamp_utc=base_time + timedelta(hours=17, minutes=20),
                block_number=198000000,
            ),
        ]
        return txs

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

    # --- Rich Multi-Chain & Multi-Hop Synthetic Graph for Any Target Address ---
    seed = abs(hash(norm))
    t0 = datetime(2024, 3, 1, 10, 0, 0, tzinfo=timezone.utc)
    is_evm = norm.startswith("0x")
    sym = "ETH" if is_evm else "BTC"
    chain_root = ChainEcosystem.ETHEREUM if is_evm else ChainEcosystem.BITCOIN

    # Generate realistic multi-hop counterparties
    p1 = f"0x{(seed * 3) % (16**40):040x}" if is_evm else f"1{(seed * 3) % (10**25):025d}"
    p2 = f"0x{(seed * 7) % (16**40):040x}" if is_evm else f"1{(seed * 7) % (10**25):025d}"
    p3 = f"0x{(seed * 11) % (16**40):040x}" if is_evm else f"1{(seed * 11) % (10**25):025d}"
    dest_cex_deposit = f"0x{(seed * 17) % (16**40):040x}" if is_evm else f"1{(seed * 17) % (10**25):025d}"

    txs = [
        # Hop 1: Inflow from Binance Hot Wallet
        DomainTransactionEvent(
            tx_hash=f"0x91{abs(hash(norm + 'in1')):062x}"[:66],
            chain=chain_root,
            from_address=BINANCE_HOT_WALLET if is_evm else "coinbase",
            to_address=norm,
            value_native=18.5,
            token_symbol=sym,
            fee_native=0.0018,
            timestamp_utc=t0,
            block_number=19400000,
        ),
        # Hop 1: Outflow swapping on Uniswap V3
        DomainTransactionEvent(
            tx_hash=f"0x92{abs(hash(norm + 'swap1')):062x}"[:66],
            chain=chain_root,
            from_address=norm,
            to_address=UNISWAP_V3_ROUTER if is_evm else p1,
            value_native=4.2,
            token_symbol=sym,
            fee_native=0.0032,
            timestamp_utc=t0 + timedelta(days=1),
            block_number=19405000,
            is_contract_call=True,
            method_name="exactInputSingle" if is_evm else None,
        ),
        # Hop 1: Transfer to Counterparty P1
        DomainTransactionEvent(
            tx_hash=f"0x93{abs(hash(norm + 'p1')):062x}"[:66],
            chain=chain_root,
            from_address=norm,
            to_address=p1,
            value_native=2.5,
            token_symbol=sym,
            fee_native=0.0011,
            timestamp_utc=t0 + timedelta(days=2),
            block_number=19410000,
        ),
        # Hop 1: Outflow into Stargate Bridge (Cross-Chain)
        DomainTransactionEvent(
            tx_hash=f"0x94{abs(hash(norm + 'bridge1')):062x}"[:66],
            chain=chain_root,
            from_address=norm,
            to_address=STARGATE_ROUTER if is_evm else p2,
            value_native=6.0,
            token_symbol=sym,
            fee_native=0.0028,
            timestamp_utc=t0 + timedelta(days=3),
            block_number=19416000,
            is_contract_call=True,
            method_name="swapETH" if is_evm else None,
        ),
        # Hop 1: Deposit to CEX Shared Deposit Account
        DomainTransactionEvent(
            tx_hash=f"0x95{abs(hash(norm + 'cexdep')):062x}"[:66],
            chain=chain_root,
            from_address=norm,
            to_address=dest_cex_deposit,
            value_native=3.0,
            token_symbol=sym,
            fee_native=0.0014,
            timestamp_utc=t0 + timedelta(days=4),
            block_number=19422000,
        ),
        # --- 2-Hop Connections Between Counterparties ---
        # Hop 2: Counterparty P1 also deposits to the SAME CEX deposit address (Clustering Heuristic 1!)
        DomainTransactionEvent(
            tx_hash=f"0x96{abs(hash(norm + 'p1_dep')):062x}"[:66],
            chain=chain_root,
            from_address=p1,
            to_address=dest_cex_deposit,
            value_native=1.8,
            token_symbol=sym,
            fee_native=0.0012,
            timestamp_utc=t0 + timedelta(days=4, hours=2),
            block_number=19422500,
        ),
        # Hop 2: Counterparty P1 transfers funds to P2
        DomainTransactionEvent(
            tx_hash=f"0x97{abs(hash(norm + 'p1_p2')):062x}"[:66],
            chain=chain_root,
            from_address=p1,
            to_address=p2,
            value_native=0.5,
            token_symbol=sym,
            fee_native=0.0009,
            timestamp_utc=t0 + timedelta(days=5),
            block_number=19428000,
        ),
        # Hop 2: Counterparty P2 swaps on Curve Pool
        DomainTransactionEvent(
            tx_hash=f"0x98{abs(hash(norm + 'p2_curve')):062x}"[:66],
            chain=chain_root,
            from_address=p2,
            to_address=CURVE_3POOL if is_evm else p3,
            value_native=0.5,
            token_symbol=sym,
            fee_native=0.0022,
            timestamp_utc=t0 + timedelta(days=6),
            block_number=19434000,
            is_contract_call=True,
            method_name="exchange",
        ),
        # Hop 2: Destination L2 execution (Arbitrum)
        DomainTransactionEvent(
            tx_hash=f"0x99{abs(hash(norm + 'l2_arb')):062x}"[:66],
            chain=ChainEcosystem.ARBITRUM,
            from_address=STARGATE_ROUTER if is_evm else p1,
            to_address=p3,
            value_native=5.9,
            token_symbol="ETH",
            fee_native=0.0003,
            timestamp_utc=t0 + timedelta(days=3, minutes=25),
            block_number=197500000,
        ),
        # Hop 2: P3 transfers to Coinbase Hot Wallet
        DomainTransactionEvent(
            tx_hash=f"0x9a{abs(hash(norm + 'p3_cb')):062x}"[:66],
            chain=ChainEcosystem.ARBITRUM if is_evm else chain_root,
            from_address=p3,
            to_address=COINBASE_HOT_WALLET if is_evm else "coinbase",
            value_native=5.8,
            token_symbol="ETH" if is_evm else "BTC",
            fee_native=0.0002,
            timestamp_utc=t0 + timedelta(days=7),
            block_number=197800000,
        ),
    ]
    return txs


def get_fixture_bridges(address: Optional[str] = None) -> List[CrossChainBridgeEvent]:
    norm = address.strip().lower() if address else None

    # Vitalik specific bridge events
    if norm == VITALIK_ETH.lower():
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
        ]

    # Tornado Cash 0.1 ETH specific cross-chain bridge events
    if norm == TORNADO_01_ETH:
        withdrawer_2 = "0x4b20427373d6d84e98730d7795d8f6f8731fcc88"
        relayer_arb = "0x5c30427373d6d84e98730d7795d8f6f8731fdd77"
        return [
            CrossChainBridgeEvent(
                bridge_name="Stargate",
                source_chain=ChainEcosystem.ETHEREUM,
                source_tx_hash="0xcc05000500050005000500050005000500050005000500050005000500050005",
                source_address=withdrawer_2,
                destination_chain=ChainEcosystem.ARBITRUM,
                destination_tx_hash="0xcc06000600060006000600060006000600060006000600060006000600060006",
                destination_address=relayer_arb,
                token_symbol="ETH",
                amount=0.1,
                timestamp_utc=datetime(2024, 4, 11, 1, 0, 0, tzinfo=timezone.utc),
                status="COMPLETED",
            ),
            CrossChainBridgeEvent(
                bridge_name="Across",
                source_chain=ChainEcosystem.ETHEREUM,
                source_tx_hash="0xdd07000700070007000700070007000700070007000700070007000700070007",
                source_address=TORNADO_01_ETH,
                destination_chain=ChainEcosystem.POLYGON,
                destination_tx_hash="0xee07000700070007000700070007000700070007000700070007000700070007",
                destination_address="0x6d40427373d6d84e98730d7795d8f6f8731fee66",
                token_symbol="ETH",
                amount=0.5,
                timestamp_utc=datetime(2024, 4, 11, 4, 15, 0, tzinfo=timezone.utc),
                status="COMPLETED",
            ),
        ]

    # Cluster persona specific bridge events
    if norm in (CLUSTER_WALLET_A.lower(), CLUSTER_WALLET_B.lower(), CLUSTER_WALLET_C.lower()):
        return [
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

    # Default bridge events tailored to the queried address
    if norm:
        seed = abs(hash(norm))
        dest_wallet = f"0x{(seed * 11) % (16**40):040x}" if norm.startswith("0x") else f"1{(seed * 11) % (10**25):025d}"
        return [
            CrossChainBridgeEvent(
                bridge_name="Stargate",
                source_chain=ChainEcosystem.ETHEREUM if norm.startswith("0x") else ChainEcosystem.BITCOIN,
                source_tx_hash=f"0x94{abs(hash(norm + 'bridge1')):062x}"[:66],
                source_address=norm,
                destination_chain=ChainEcosystem.ARBITRUM,
                destination_tx_hash=f"0x99{abs(hash(norm + 'l2_arb')):062x}"[:66],
                destination_address=dest_wallet,
                token_symbol="ETH",
                amount=6.0,
                timestamp_utc=datetime(2024, 3, 4, 10, 0, 0, tzinfo=timezone.utc),
                status="COMPLETED",
            ),
        ]

    # Global default
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
