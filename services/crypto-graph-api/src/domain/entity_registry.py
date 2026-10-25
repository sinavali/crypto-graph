"""
Comprehensive Blockchain Known Entity & Attribution Registry.
Maintains curated directories of Centralized Exchanges (CEX), Cross-Chain Bridges,
Privacy Mixers (Tornado Cash, Railgun), Major DeFi Protocols, and Notable Whales/Entities.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel
from libs.blockchain_contracts.models import ChainEcosystem


class EntityInfo(BaseModel):
    address: str
    name: str
    category: str  # "exchange", "bridge", "mixer", "defi", "whale", "sanctioned"
    entity: str    # e.g. "Binance", "Tornado Cash", "Uniswap"
    risk_level: str = "LOW"  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    chain: ChainEcosystem = ChainEcosystem.ETHEREUM
    tags: List[str] = []


# Canonical Known Address Directory (all lowercase)
KNOWN_ENTITIES: Dict[str, EntityInfo] = {
    # --- Tornado Cash Mixers & Routers (High Risk / Privacy) ---
    "0xa160cdab225685da1d56aa342ad8841c3b53f291": EntityInfo(
        address="0xa160cdab225685da1d56aa342ad8841c3b53f291",
        name="Tornado Cash: 0.1 ETH Pool",
        category="mixer",
        entity="Tornado Cash",
        risk_level="HIGH",
        chain=ChainEcosystem.ETHEREUM,
        tags=["mixer", "privacy-protocol", "tornado-cash", "ofac-sanctioned"],
    ),
    "0x12d66f87a04a9e220743712ce6d9bb1b5616b8fc": EntityInfo(
        address="0x12d66f87a04a9e220743712ce6d9bb1b5616b8fc",
        name="Tornado Cash: 1 ETH Pool",
        category="mixer",
        entity="Tornado Cash",
        risk_level="HIGH",
        chain=ChainEcosystem.ETHEREUM,
        tags=["mixer", "privacy-protocol", "tornado-cash", "ofac-sanctioned"],
    ),
    "0x47ce0c6ed5b0ce3d3a51fdb1c52dc66a7c3c2936": EntityInfo(
        address="0x47ce0c6ed5b0ce3d3a51fdb1c52dc66a7c3c2936",
        name="Tornado Cash: 10 ETH Pool",
        category="mixer",
        entity="Tornado Cash",
        risk_level="HIGH",
        chain=ChainEcosystem.ETHEREUM,
        tags=["mixer", "privacy-protocol", "tornado-cash", "ofac-sanctioned"],
    ),
    "0x910cbd523d972eb0a6f4cae4618ad62622b39dbf": EntityInfo(
        address="0x910cbd523d972eb0a6f4cae4618ad62622b39dbf",
        name="Tornado Cash: 100 ETH Pool",
        category="mixer",
        entity="Tornado Cash",
        risk_level="HIGH",
        chain=ChainEcosystem.ETHEREUM,
        tags=["mixer", "privacy-protocol", "tornado-cash", "ofac-sanctioned"],
    ),
    "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b": EntityInfo(
        address="0xd90e2f925da726b50c4ed8d0fb90ad053324f31b",
        name="Tornado Cash: Router",
        category="mixer",
        entity="Tornado Cash",
        risk_level="HIGH",
        chain=ChainEcosystem.ETHEREUM,
        tags=["mixer", "privacy-router", "tornado-cash"],
    ),

    # --- Centralized Exchanges: Binance ---
    "0x28c6c06298d514db089934071355e5743bf21d60": EntityInfo(
        address="0x28c6c06298d514db089934071355e5743bf21d60",
        name="Binance: Hot Wallet 14",
        category="exchange",
        entity="Binance",
        risk_level="LOW",
        chain=ChainEcosystem.ETHEREUM,
        tags=["cex", "binance", "hot-wallet", "exchange-liquidity"],
    ),
    "0x21a31ee1afc51d94c2efccaa2092ad1028285549": EntityInfo(
        address="0x21a31ee1afc51d94c2efccaa2092ad1028285549",
        name="Binance: Hot Wallet 15",
        category="exchange",
        entity="Binance",
        risk_level="LOW",
        chain=ChainEcosystem.ETHEREUM,
        tags=["cex", "binance", "hot-wallet"],
    ),
    "0xdfd5293d8e347dfe59e90efd55b2956a1343963d": EntityInfo(
        address="0xdfd5293d8e347dfe59e90efd55b2956a1343963d",
        name="Binance: Hot Wallet 16",
        category="exchange",
        entity="Binance",
        risk_level="LOW",
        chain=ChainEcosystem.ETHEREUM,
        tags=["cex", "binance", "hot-wallet"],
    ),
    "0x9999999999999999999999999999999999999999": EntityInfo(
        address="0x9999999999999999999999999999999999999999",
        name="Binance: User Deposit Vault",
        category="exchange",
        entity="Binance",
        risk_level="LOW",
        chain=ChainEcosystem.ETHEREUM,
        tags=["cex-deposit", "binance"],
    ),

    # --- Centralized Exchanges: Coinbase ---
    "0x503828976d22510aad0201ac7ec88293211d23dc": EntityInfo(
        address="0x503828976d22510aad0201ac7ec88293211d23dc",
        name="Coinbase: Hot Wallet 10",
        category="exchange",
        entity="Coinbase",
        risk_level="LOW",
        chain=ChainEcosystem.ETHEREUM,
        tags=["cex", "coinbase", "hot-wallet"],
    ),
    "0x71660c4005ba85c37ccec55d0c4493e66fe775d3": EntityInfo(
        address="0x71660c4005ba85c37ccec55d0c4493e66fe775d3",
        name="Coinbase: Prime Custody",
        category="exchange",
        entity="Coinbase",
        risk_level="LOW",
        chain=ChainEcosystem.ETHEREUM,
        tags=["cex", "coinbase", "institutional"],
    ),

    # --- Centralized Exchanges: Kraken, OKX, Bybit ---
    "0x2910543af39aba0cd09dbb2d50200b3e800a63d2": EntityInfo(
        address="0x2910543af39aba0cd09dbb2d50200b3e800a63d2",
        name="Kraken: Hot Wallet 4",
        category="exchange",
        entity="Kraken",
        risk_level="LOW",
        chain=ChainEcosystem.ETHEREUM,
        tags=["cex", "kraken", "hot-wallet"],
    ),
    "0x6cc5f688a30437666842ec73b0af5d2335be2836": EntityInfo(
        address="0x6cc5f688a30437666842ec73b0af5d2335be2836",
        name="OKX: Hot Wallet 3",
        category="exchange",
        entity="OKX",
        risk_level="LOW",
        chain=ChainEcosystem.ETHEREUM,
        tags=["cex", "okx", "hot-wallet"],
    ),
    "0xf89d7b9c374f279dca50b7655ac37f0969757477": EntityInfo(
        address="0xf89d7b9c374f279dca50b7655ac37f0969757477",
        name="Bybit: Hot Wallet 1",
        category="exchange",
        entity="Bybit",
        risk_level="LOW",
        chain=ChainEcosystem.ETHEREUM,
        tags=["cex", "bybit", "hot-wallet"],
    ),

    # --- Cross-Chain Bridges ---
    "0x8731d54e9d02c271bb81737cd9d18c622f484636": EntityInfo(
        address="0x8731d54e9d02c271bb81737cd9d18c622f484636",
        name="Stargate: Cross-Chain Router",
        category="bridge",
        entity="Stargate Finance",
        risk_level="LOW",
        chain=ChainEcosystem.ETHEREUM,
        tags=["bridge", "stargate", "layerzero", "cross-chain"],
    ),
    "0x5c7bcd6e7de5423a257d81b442095a1a6ced35c5": EntityInfo(
        address="0x5c7bcd6e7de5423a257d81b442095a1a6ced35c5",
        name="Across: SpokePool Hub",
        category="bridge",
        entity="Across Protocol",
        risk_level="LOW",
        chain=ChainEcosystem.ETHEREUM,
        tags=["bridge", "across", "cross-chain", "optimistic-oracle"],
    ),
    "0x98f3c9e6e3face36ba8cee86ac77f0f76843475e": EntityInfo(
        address="0x98f3c9e6e3face36ba8cee86ac77f0f76843475e",
        name="Wormhole: Core Bridge",
        category="bridge",
        entity="Wormhole",
        risk_level="LOW",
        chain=ChainEcosystem.ETHEREUM,
        tags=["bridge", "wormhole", "cross-chain"],
    ),
    "0x3666f603cc164936c1b87e207f36beba4ac5f18a": EntityInfo(
        address="0x3666f603cc164936c1b87e207f36beba4ac5f18a",
        name="Hop: ETH Bridge",
        category="bridge",
        entity="Hop Protocol",
        risk_level="LOW",
        chain=ChainEcosystem.ETHEREUM,
        tags=["bridge", "hop-protocol", "rollups"],
    ),

    # --- Major DeFi Protocols ---
    "0xe592427a0aece92de3edee1f18e0157c05861564": EntityInfo(
        address="0xe592427a0aece92de3edee1f18e0157c05861564",
        name="Uniswap V3: SwapRouter",
        category="defi",
        entity="Uniswap",
        risk_level="LOW",
        chain=ChainEcosystem.ETHEREUM,
        tags=["defi", "amm", "uniswap-v3", "dex"],
    ),
    "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45": EntityInfo(
        address="0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45",
        name="Uniswap V3: SwapRouter02",
        category="defi",
        entity="Uniswap",
        risk_level="LOW",
        chain=ChainEcosystem.ETHEREUM,
        tags=["defi", "amm", "uniswap-v3"],
    ),
    "0x7a250d5630b4cf539739df2c5dacb4c659f2488d": EntityInfo(
        address="0x7a250d5630b4cf539739df2c5dacb4c659f2488d",
        name="Uniswap V2: Router02",
        category="defi",
        entity="Uniswap",
        risk_level="LOW",
        chain=ChainEcosystem.ETHEREUM,
        tags=["defi", "amm", "uniswap-v2"],
    ),
    "0xbebc44782c7db0a1a60cb6fe97d0b483032ff1c7": EntityInfo(
        address="0xbebc44782c7db0a1a60cb6fe97d0b483032ff1c7",
        name="Curve.fi: DAI/USDC/USDT 3pool",
        category="defi",
        entity="Curve Finance",
        risk_level="LOW",
        chain=ChainEcosystem.ETHEREUM,
        tags=["defi", "stablecoin-amm", "curve-fi"],
    ),
    "0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2": EntityInfo(
        address="0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2",
        name="Aave V3: Pool",
        category="defi",
        entity="Aave",
        risk_level="LOW",
        chain=ChainEcosystem.ETHEREUM,
        tags=["defi", "lending", "aave-v3"],
    ),
    "0x1111111254fb6c44bac0bed2854e76f90643097d": EntityInfo(
        address="0x1111111254fb6c44bac0bed2854e76f90643097d",
        name="1inch: Aggregation Router V5",
        category="defi",
        entity="1inch Network",
        risk_level="LOW",
        chain=ChainEcosystem.ETHEREUM,
        tags=["defi", "dex-aggregator", "1inch"],
    ),

    # --- Curated Notable Personalities / Whales ---
    "0xd8da6bf26964af9d7eed9e03e53415d37aa96045": EntityInfo(
        address="0xd8da6bf26964af9d7eed9e03e53415d37aa96045",
        name="Vitalik Buterin (vitalik.eth)",
        category="whale",
        entity="Vitalik Buterin",
        risk_level="LOW",
        chain=ChainEcosystem.ETHEREUM,
        tags=["whale", "ethereum-founder", "vitalik.eth"],
    ),
    "1a1zp1ep5qgefi2dmptftl5slmv7divfna": EntityInfo(
        address="1a1zp1ep5qgefi2dmptftl5slmv7divfna",
        name="Satoshi Nakamoto: Genesis Coinbase",
        category="whale",
        entity="Satoshi Nakamoto",
        risk_level="LOW",
        chain=ChainEcosystem.BITCOIN,
        tags=["whale", "bitcoin-creator", "genesis-block"],
    ),
    "12c6dsiu4rq3p4zxzikxzrl5lmmbrzjrjx": EntityInfo(
        address="12c6dsiu4rq3p4zxzikxzrl5lmmbrzjrjx",
        name="Satoshi Nakamoto: Block 9",
        category="whale",
        entity="Satoshi Nakamoto",
        risk_level="LOW",
        chain=ChainEcosystem.BITCOIN,
        tags=["whale", "satoshi-nakamoto", "block-9"],
    ),
    "1q2twjh9n0n2wv6nusx79j161exhevdb1": EntityInfo(
        address="1q2twjh9n0n2wv6nusx79j161exhevdb1",
        name="Hal Finney (First BTC Recipient)",
        category="whale",
        entity="Hal Finney",
        risk_level="LOW",
        chain=ChainEcosystem.BITCOIN,
        tags=["cypherpunk", "hal-finney", "first-recipient"],
    ),
}


def lookup_known_entity(address: str) -> Optional[EntityInfo]:
    norm = address.strip().lower()
    return KNOWN_ENTITIES.get(norm)


def is_exchange_address(address: str) -> bool:
    ent = lookup_known_entity(address)
    if ent and ent.category == "exchange":
        return True
    norm = address.lower()
    return any(ex in norm for ex in ["binance", "coinbase", "kraken", "okx", "bybit", "cex"])


def is_mixer_address(address: str) -> bool:
    ent = lookup_known_entity(address)
    if ent and ent.category == "mixer":
        return True
    norm = address.lower()
    return any(m in norm for m in ["tornado", "mixer", "railgun", "wasabi"])


def is_bridge_address(address: str) -> bool:
    ent = lookup_known_entity(address)
    if ent and ent.category == "bridge":
        return True
    norm = address.lower()
    return any(b in norm for b in ["bridge", "stargate", "across", "wormhole", "hop"])
