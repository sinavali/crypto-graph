"""
Domain models for Multi-Tenancy, User Management, and Captcha Challenges.
Pure domain logic: UTC-enforced, zero external persistence or UI coupling.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class UserRole(str, Enum):
    ADMIN = "admin"
    MEMBER = "member"


class Tenant(BaseModel):
    tenant_id: str
    name: str
    created_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("created_at_utc")
    @classmethod
    def ensure_utc(cls, v: datetime) -> datetime:
        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)


class User(BaseModel):
    user_id: str
    tenant_id: str
    username: str
    password_hash: str
    role: UserRole = UserRole.MEMBER
    is_active: bool = True
    created_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("created_at_utc")
    @classmethod
    def ensure_utc(cls, v: datetime) -> datetime:
        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)


class SessionToken(BaseModel):
    token: str
    user_id: str
    tenant_id: str
    username: str
    role: UserRole
    expires_at_utc: datetime

    @field_validator("expires_at_utc")
    @classmethod
    def ensure_utc(cls, v: datetime) -> datetime:
        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at_utc


class CaptchaChallenge(BaseModel):
    challenge_id: str
    question_text: str
    answer_hash: str
    created_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at_utc: datetime

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at_utc
