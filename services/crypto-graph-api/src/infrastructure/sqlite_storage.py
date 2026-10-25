"""
Embedded SQLite Datastore Adapter.
Zero external database daemons required. Operates in WAL mode with UTC ISO-8601 timestamps.
"""

from datetime import datetime, timezone
import json
import sqlite3
from typing import List, Optional
from libs.blockchain_contracts.models import (
    ChainEcosystem,
    DomainTransactionEvent,
    PersonaProfile,
)
from ..domain.ports import GraphStoragePort


class SqliteGraphStorage(GraphStoragePort):
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        if self.db_path != ":memory:":
            self._conn.execute("PRAGMA journal_mode = WAL;")
        self._init_schema()

    def _get_connection(self) -> sqlite3.Connection:
        return self._conn

    def _init_schema(self) -> None:
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS transactions (
                    tx_hash TEXT PRIMARY KEY,
                    chain TEXT NOT NULL,
                    from_address TEXT NOT NULL,
                    to_address TEXT NOT NULL,
                    value_native REAL NOT NULL,
                    token_symbol TEXT NOT NULL,
                    fee_native REAL NOT NULL,
                    timestamp_utc TEXT NOT NULL,
                    block_number INTEGER NOT NULL,
                    is_contract_call INTEGER NOT NULL,
                    method_name TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_tx_from ON transactions (from_address);
                CREATE INDEX IF NOT EXISTS idx_tx_to ON transactions (to_address);

                CREATE TABLE IF NOT EXISTS persona_profiles (
                    persona_id TEXT PRIMARY KEY,
                    primary_address TEXT NOT NULL,
                    confidence_score REAL NOT NULL,
                    data_json TEXT NOT NULL,
                    created_at_utc TEXT NOT NULL
                );
            """)

    def save_transactions(self, transactions: List[DomainTransactionEvent]) -> None:
        with self._get_connection() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO transactions (
                    tx_hash, chain, from_address, to_address, value_native,
                    token_symbol, fee_native, timestamp_utc, block_number,
                    is_contract_call, method_name
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        tx.tx_hash,
                        tx.chain.value,
                        tx.from_address.lower(),
                        tx.to_address.lower(),
                        tx.value_native,
                        tx.token_symbol,
                        tx.fee_native,
                        tx.timestamp_utc.isoformat(),
                        tx.block_number,
                        1 if tx.is_contract_call else 0,
                        tx.method_name,
                    )
                    for tx in transactions
                ],
            )

    def get_transactions_for_address(self, address: str) -> List[DomainTransactionEvent]:
        addr = address.lower()
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM transactions
                WHERE from_address = ? OR to_address = ?
                ORDER BY timestamp_utc DESC
                """,
                (addr, addr),
            )
            rows = cursor.fetchall()
            return [
                DomainTransactionEvent(
                    tx_hash=row["tx_hash"],
                    chain=ChainEcosystem(row["chain"]),
                    from_address=row["from_address"],
                    to_address=row["to_address"],
                    value_native=row["value_native"],
                    token_symbol=row["token_symbol"],
                    fee_native=row["fee_native"],
                    timestamp_utc=datetime.fromisoformat(row["timestamp_utc"]),
                    block_number=row["block_number"],
                    is_contract_call=bool(row["is_contract_call"]),
                    method_name=row["method_name"],
                )
                for row in rows
            ]

    def save_persona_profile(self, profile: PersonaProfile) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO persona_profiles (
                    persona_id, primary_address, confidence_score, data_json, created_at_utc
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    profile.persona_id,
                    profile.primary_address.lower(),
                    profile.confidence_score,
                    profile.model_dump_json(),
                    profile.created_at_utc.isoformat(),
                ),
            )

    def get_persona_profile(self, persona_id: str) -> Optional[PersonaProfile]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT data_json FROM persona_profiles WHERE persona_id = ?",
                (persona_id,),
            )
            row = cursor.fetchone()
            if row:
                return PersonaProfile.model_validate_json(row["data_json"])
            return None
