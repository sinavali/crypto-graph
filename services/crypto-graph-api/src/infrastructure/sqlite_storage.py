"""
Embedded SQLite Datastore Adapter with Multi-Tenancy & Configuration Support.
Zero external database daemons required. Operates in WAL mode with UTC ISO-8601 timestamps.
"""

from datetime import datetime, timezone
import json
import sqlite3
from typing import Any, Dict, List, Optional
from libs.blockchain_contracts.auth_models import (
    SessionToken,
    Tenant,
    User,
    UserRole,
)
from libs.blockchain_contracts.config_models import (
    ConfigCategory,
    InvestigationRecord,
    SearchHistoryRecord,
    SystemConfigItem,
    WatchlistItem,
)
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
                    method_name TEXT,
                    co_inputs_json TEXT
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

                CREATE TABLE IF NOT EXISTS tenants (
                    tenant_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at_utc TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at_utc TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    token TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    tenant_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    role TEXT NOT NULL,
                    expires_at_utc TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS system_configs (
                    config_key TEXT PRIMARY KEY,
                    config_value TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT NOT NULL,
                    updated_at_utc TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS watchlist (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    address TEXT NOT NULL,
                    label TEXT,
                    chain TEXT NOT NULL,
                    notes TEXT,
                    created_at_utc TEXT NOT NULL,
                    UNIQUE(tenant_id, address)
                );

                CREATE TABLE IF NOT EXISTS saved_investigations (
                    investigation_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    target_address TEXT NOT NULL,
                    graph_data_json TEXT NOT NULL,
                    created_at_utc TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS search_history (
                    search_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    address TEXT NOT NULL,
                    chain TEXT NOT NULL,
                    searched_at_utc TEXT NOT NULL
                );
            """)

    # --- Transactions ---
    def save_transactions(self, transactions: List[DomainTransactionEvent]) -> None:
        with self._get_connection() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO transactions (
                    tx_hash, chain, from_address, to_address, value_native,
                    token_symbol, fee_native, timestamp_utc, block_number,
                    is_contract_call, method_name, co_inputs_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                        json.dumps(tx.co_inputs) if tx.co_inputs else "[]",
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
                WHERE from_address = ? OR to_address = ? OR co_inputs_json LIKE ?
                ORDER BY timestamp_utc DESC
                """,
                (addr, addr, f"%{addr}%"),
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
                    co_inputs=json.loads(row["co_inputs_json"]) if ("co_inputs_json" in row.keys() and row["co_inputs_json"]) else [],
                )
                for row in rows
            ]

    # --- Persona Profiles ---
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

    def delete_persona_profile(self, persona_id: str) -> None:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM persona_profiles WHERE persona_id = ?", (persona_id,))

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

    def get_all_personas(self) -> List[PersonaProfile]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT data_json FROM persona_profiles ORDER BY confidence_score DESC")
            return [PersonaProfile.model_validate_json(row["data_json"]) for row in cursor.fetchall()]

    # --- Tenants & Users ---
    def create_tenant(self, tenant: Tenant) -> None:
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO tenants (tenant_id, name, created_at_utc) VALUES (?, ?, ?)",
                (tenant.tenant_id, tenant.name, tenant.created_at_utc.isoformat()),
            )

    def get_all_tenants(self) -> List[Tenant]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM tenants ORDER BY created_at_utc DESC")
            return [
                Tenant(
                    tenant_id=row["tenant_id"],
                    name=row["name"],
                    created_at_utc=datetime.fromisoformat(row["created_at_utc"]),
                )
                for row in cursor.fetchall()
            ]

    def create_user(self, user: User) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO users (
                    user_id, tenant_id, username, password_hash, role, is_active, created_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user.user_id,
                    user.tenant_id,
                    user.username.lower(),
                    user.password_hash,
                    user.role.value,
                    1 if user.is_active else 0,
                    user.created_at_utc.isoformat(),
                ),
            )

    def get_user_by_username(self, username: str) -> Optional[User]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM users WHERE username = ?", (username.lower(),))
            row = cursor.fetchone()
            if row:
                return User(
                    user_id=row["user_id"],
                    tenant_id=row["tenant_id"],
                    username=row["username"],
                    password_hash=row["password_hash"],
                    role=UserRole(row["role"]),
                    is_active=bool(row["is_active"]),
                    created_at_utc=datetime.fromisoformat(row["created_at_utc"]),
                )
            return None

    def get_all_users(self) -> List[User]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM users ORDER BY created_at_utc DESC")
            return [
                User(
                    user_id=row["user_id"],
                    tenant_id=row["tenant_id"],
                    username=row["username"],
                    password_hash=row["password_hash"],
                    role=UserRole(row["role"]),
                    is_active=bool(row["is_active"]),
                    created_at_utc=datetime.fromisoformat(row["created_at_utc"]),
                )
                for row in cursor.fetchall()
            ]

    def update_user_status(self, user_id: str, is_active: bool) -> None:
        with self._get_connection() as conn:
            conn.execute("UPDATE users SET is_active = ? WHERE user_id = ?", (1 if is_active else 0, user_id))

    def update_user_role(self, user_id: str, role: UserRole) -> None:
        val = role.value if isinstance(role, UserRole) else str(role)
        with self._get_connection() as conn:
            conn.execute("UPDATE users SET role = ? WHERE user_id = ?", (val, user_id))

    # --- Sessions ---
    def save_session(self, session: SessionToken) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO sessions (token, user_id, tenant_id, username, role, expires_at_utc)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session.token,
                    session.user_id,
                    session.tenant_id,
                    session.username,
                    session.role.value,
                    session.expires_at_utc.isoformat(),
                ),
            )

    def get_session(self, token: str) -> Optional[SessionToken]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM sessions WHERE token = ?", (token,))
            row = cursor.fetchone()
            if row:
                return SessionToken(
                    token=row["token"],
                    user_id=row["user_id"],
                    tenant_id=row["tenant_id"],
                    username=row["username"],
                    role=UserRole(row["role"]),
                    expires_at_utc=datetime.fromisoformat(row["expires_at_utc"]),
                )
            return None

    def delete_session(self, token: str) -> None:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))

    # --- System Configs ---
    def set_config(self, item: SystemConfigItem) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO system_configs (config_key, config_value, category, description, updated_at_utc)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    item.config_key,
                    item.config_value,
                    item.category.value,
                    item.description,
                    item.updated_at_utc.isoformat(),
                ),
            )

    def get_config(self, key: str) -> Optional[SystemConfigItem]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM system_configs WHERE config_key = ?", (key,))
            row = cursor.fetchone()
            if row:
                return SystemConfigItem(
                    config_key=row["config_key"],
                    config_value=row["config_value"],
                    category=ConfigCategory(row["category"]),
                    description=row["description"],
                    updated_at_utc=datetime.fromisoformat(row["updated_at_utc"]),
                )
            return None

    def get_all_configs(self) -> List[SystemConfigItem]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM system_configs ORDER BY category, config_key")
            return [
                SystemConfigItem(
                    config_key=row["config_key"],
                    config_value=row["config_value"],
                    category=ConfigCategory(row["category"]),
                    description=row["description"],
                    updated_at_utc=datetime.fromisoformat(row["updated_at_utc"]),
                )
                for row in cursor.fetchall()
            ]

    # --- Watchlist ---
    def add_to_watchlist(self, item: WatchlistItem) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO watchlist (id, tenant_id, address, label, chain, notes, created_at_utc)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.id,
                    item.tenant_id,
                    item.address.lower(),
                    item.label,
                    item.chain,
                    item.notes,
                    item.created_at_utc.isoformat(),
                ),
            )

    def get_watchlist(self, tenant_id: str) -> List[WatchlistItem]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM watchlist WHERE tenant_id = ? ORDER BY created_at_utc DESC",
                (tenant_id,),
            )
            return [
                WatchlistItem(
                    id=row["id"],
                    tenant_id=row["tenant_id"],
                    address=row["address"],
                    label=row["label"],
                    chain=row["chain"],
                    notes=row["notes"],
                    created_at_utc=datetime.fromisoformat(row["created_at_utc"]),
                )
                for row in cursor.fetchall()
            ]

    def remove_from_watchlist(self, tenant_id: str, address: str) -> None:
        with self._get_connection() as conn:
            conn.execute(
                "DELETE FROM watchlist WHERE tenant_id = ? AND address = ?",
                (tenant_id, address.lower()),
            )

    # --- Saved Investigations ---
    def save_investigation(self, record: InvestigationRecord) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO saved_investigations (
                    investigation_id, tenant_id, user_id, title, target_address, graph_data_json, created_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.investigation_id,
                    record.tenant_id,
                    record.user_id,
                    record.title,
                    record.target_address.lower(),
                    record.graph_data_json,
                    record.created_at_utc.isoformat(),
                ),
            )

    def get_investigations(self, tenant_id: str) -> List[InvestigationRecord]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM saved_investigations WHERE tenant_id = ? ORDER BY created_at_utc DESC",
                (tenant_id,),
            )
            return [
                InvestigationRecord(
                    investigation_id=row["investigation_id"],
                    tenant_id=row["tenant_id"],
                    user_id=row["user_id"],
                    title=row["title"],
                    target_address=row["target_address"],
                    graph_data_json=row["graph_data_json"],
                    created_at_utc=datetime.fromisoformat(row["created_at_utc"]),
                )
                for row in cursor.fetchall()
            ]

    def get_investigation_by_id(self, investigation_id: str) -> Optional[InvestigationRecord]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM saved_investigations WHERE investigation_id = ?",
                (investigation_id,),
            )
            row = cursor.fetchone()
            if row:
                return InvestigationRecord(
                    investigation_id=row["investigation_id"],
                    tenant_id=row["tenant_id"],
                    user_id=row["user_id"],
                    title=row["title"],
                    target_address=row["target_address"],
                    graph_data_json=row["graph_data_json"],
                    created_at_utc=datetime.fromisoformat(row["created_at_utc"]),
                )
            return None

    # --- Search History ---
    def add_search_history(self, record: SearchHistoryRecord) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO search_history (search_id, tenant_id, user_id, address, chain, searched_at_utc)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    record.search_id,
                    record.tenant_id,
                    record.user_id,
                    record.address.lower(),
                    record.chain,
                    record.searched_at_utc.isoformat(),
                ),
            )

    def get_search_history(self, tenant_id: str, limit: int = 10) -> List[SearchHistoryRecord]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM search_history
                WHERE tenant_id = ?
                ORDER BY searched_at_utc DESC LIMIT ?
                """,
                (tenant_id, limit),
            )
            return [
                SearchHistoryRecord(
                    search_id=row["search_id"],
                    tenant_id=row["tenant_id"],
                    user_id=row["user_id"],
                    address=row["address"],
                    chain=row["chain"],
                    searched_at_utc=datetime.fromisoformat(row["searched_at_utc"]),
                )
                for row in cursor.fetchall()
            ]
