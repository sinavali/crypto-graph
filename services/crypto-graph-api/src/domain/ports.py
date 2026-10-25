"""Ports (interfaces) for crypto-graph Hexagonal architecture."""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from libs.blockchain_contracts.models import (
    ChainEcosystem,
    DomainTransactionEvent,
    CrossChainBridgeEvent,
    PersonaProfile,
    GraphTopology,
)


class RpcProviderPort(ABC):
    @abstractmethod
    async def fetch_transactions(self, address: str, chain: Optional[ChainEcosystem] = None) -> List[DomainTransactionEvent]:
        """Fetch historical transaction events for an address."""
        pass

    @abstractmethod
    async def fetch_bridge_events(self, address: str) -> List[CrossChainBridgeEvent]:
        """Fetch cross-chain bridge events involving this address."""
        pass


class GraphStoragePort(ABC):
    @abstractmethod
    def save_transactions(self, transactions: List[DomainTransactionEvent]) -> None:
        """Persist normalized transactions in local storage."""
        pass

    @abstractmethod
    def get_transactions_for_address(self, address: str) -> List[DomainTransactionEvent]:
        """Retrieve stored transactions for an address."""
        pass

    @abstractmethod
    def save_persona_profile(self, profile: PersonaProfile) -> None:
        """Persist persona clustering profile."""
        pass

    @abstractmethod
    def get_persona_profile(self, persona_id: str) -> Optional[PersonaProfile]:
        """Retrieve persona clustering profile by ID."""
        pass
