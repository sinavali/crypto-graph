"""
Multi-Tenant Authentication and Session Management Service.
Features salted cryptographic password hashing, role-based authorization (Admin / Member),
and tenant-scoped session tokens.
"""

from datetime import datetime, timezone, timedelta
import hashlib
import hmac
import secrets
from typing import Optional, Tuple
from libs.blockchain_contracts.auth_models import (
    SessionToken,
    Tenant,
    User,
    UserRole,
)


class AuthService:
    def __init__(self, storage_port, config_service=None):
        self.storage = storage_port
        self.config_service = config_service
        self._init_default_admin()

    def _hash_password(self, password: str, salt: Optional[str] = None) -> str:
        s = salt or secrets.token_hex(16)
        key = hashlib.pbkdf2_hmac("sha256", password.encode(), s.encode(), iterations=100_000)
        return f"{s}${key.hex()}"

    def _verify_password(self, password: str, stored_hash: str) -> bool:
        try:
            salt, key_hex = stored_hash.split("$", 1)
            calculated_key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations=100_000)
            return hmac.compare_digest(key_hex, calculated_key.hex())
        except Exception:
            return False

    def _init_default_admin(self) -> None:
        """Seeds default tenant and admin user if database is empty."""
        existing_users = self.storage.get_all_users()
        if not existing_users:
            default_tenant = Tenant(
                tenant_id="tenant-core",
                name="Core Organization",
            )
            self.storage.create_tenant(default_tenant)

            admin_user = User(
                user_id="user-admin-01",
                tenant_id=default_tenant.tenant_id,
                username="admin",
                password_hash=self._hash_password("AdminPass123!"),
                role=UserRole.ADMIN,
            )
            self.storage.create_user(admin_user)

    def register_user(
        self,
        username: str,
        password: str,
        tenant_name: Optional[str] = None,
        role: UserRole = UserRole.MEMBER,
    ) -> User:
        clean_user = username.strip().lower()
        if not clean_user or len(clean_user) < 3:
            raise ValueError("Username must be at least 3 characters long.")
        min_len = self.config_service.get_int("auth.password_min_length", 6) if self.config_service else 6
        if len(password) < min_len:
            raise ValueError(f"Password must be at least {min_len} characters long.")

        existing = self.storage.get_user_by_username(clean_user)
        if existing:
            raise ValueError(f"Username '{clean_user}' is already registered.")

        # Create or assign tenant
        t_name = (tenant_name or f"{clean_user}'s Org").strip()
        tenant = Tenant(
            tenant_id=f"tenant-{secrets.token_hex(8)}",
            name=t_name,
        )
        self.storage.create_tenant(tenant)

        user = User(
            user_id=f"user-{secrets.token_hex(8)}",
            tenant_id=tenant.tenant_id,
            username=clean_user,
            password_hash=self._hash_password(password),
            role=role,
        )
        self.storage.create_user(user)
        return user

    def authenticate(self, username: str, password: str, session_hours: Optional[int] = None) -> SessionToken:
        clean_user = username.strip().lower()
        user = self.storage.get_user_by_username(clean_user)
        if not user or not user.is_active:
            raise ValueError("Invalid credentials or account disabled.")

        if not self._verify_password(password, user.password_hash):
            raise ValueError("Invalid credentials.")

        hours = session_hours if session_hours is not None else (
            self.config_service.get_int("auth.session_hours", 24) if self.config_service else 24
        )
        token_str = secrets.token_hex(32)
        expires = datetime.now(timezone.utc) + timedelta(hours=hours)
        session = SessionToken(
            token=token_str,
            user_id=user.user_id,
            tenant_id=user.tenant_id,
            username=user.username,
            role=user.role,
            expires_at_utc=expires,
        )
        self.storage.save_session(session)
        return session

    def validate_session(self, token: str) -> Optional[SessionToken]:
        session = self.storage.get_session(token)
        if session and not session.is_expired:
            return session
        if session and session.is_expired:
            self.storage.delete_session(token)
        return None

    def logout(self, token: str) -> None:
        self.storage.delete_session(token)
