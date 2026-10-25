"""
Domain models for System Configurations and User Investigations.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class ConfigCategory(str, Enum):
    RPC = "rpc"
    HEURISTICS = "heuristics"
    GRAPH = "graph"
    SECURITY = "security"
    TENANCY = "tenancy"


class SystemConfigItem(BaseModel):
    config_key: str
    config_value: str
    category: ConfigCategory
    description: str = ""
    updated_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("updated_at_utc")
    @classmethod
    def ensure_utc(cls, v: datetime) -> datetime:
        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)


class WatchlistItem(BaseModel):
    id: str
    tenant_id: str
    address: str
    label: str
    chain: str
    notes: str = ""
    created_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("created_at_utc")
    @classmethod
    def ensure_utc(cls, v: datetime) -> datetime:
        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)


class InvestigationRecord(BaseModel):
    investigation_id: str
    tenant_id: str
    user_id: str
    title: str
    target_address: str
    graph_data_json: str
    created_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("created_at_utc")
    @classmethod
    def ensure_utc(cls, v: datetime) -> datetime:
        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)


class SearchHistoryRecord(BaseModel):
    search_id: str
    tenant_id: str
    user_id: str
    address: str
    chain: str
    searched_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
