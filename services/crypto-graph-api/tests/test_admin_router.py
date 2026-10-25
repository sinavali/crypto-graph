import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.infrastructure.admin_router import router as admin_router
from src.infrastructure.auth_router import router as auth_router, captcha_engine
from src.domain.auth_service import AuthService
from src.domain.config_service import ConfigService
from src.infrastructure.sqlite_storage import SqliteGraphStorage
from libs.blockchain_contracts.fixtures import VITALIK_ETH
from libs.blockchain_contracts.models import PersonaProfile


@pytest.fixture
def app_client():
    app = FastAPI()
    storage = SqliteGraphStorage(":memory:")
    auth_service = AuthService(storage)
    config_service = ConfigService(storage)

    app.state.storage = storage
    app.state.auth_service = auth_service
    app.state.config_service = config_service

    app.include_router(auth_router)
    app.include_router(admin_router)

    client = TestClient(app)
    return client, auth_service, storage


def test_admin_rbac_and_config_updating(app_client):
    client, auth_service, storage = app_client

    # Anonymous access blocked
    res = client.get("/api/v1/admin/configs")
    assert res.status_code == 401

    # Login as admin
    admin_session = auth_service.authenticate("admin", "AdminPass123!")
    headers = {"Authorization": f"Bearer {admin_session.token}"}

    # Admin access succeeds
    res = client.get("/api/v1/admin/configs", headers=headers)
    assert res.status_code == 200
    configs = res.json()
    assert "rpc" in configs

    # Update config
    update_res = client.post(
        "/api/v1/admin/configs",
        headers=headers,
        json={"configs": {"heuristics.cex_deposit_weight": "0.95"}},
    )
    assert update_res.status_code == 200

    # Test RPC probe
    test_rpc = client.post(
        "/api/v1/admin/rpc/test",
        headers=headers,
        json={"url": "https://cloudflare-eth.com", "timeout_seconds": 2.0},
    )
    assert test_rpc.status_code == 200
    assert "latency_ms" in test_rpc.json()


def test_admin_persona_management(app_client):
    client, auth_service, storage = app_client
    admin_session = auth_service.authenticate("admin", "AdminPass123!")
    headers = {"Authorization": f"Bearer {admin_session.token}"}

    # Create dummy persona
    p = PersonaProfile(
        persona_id="persona-test-01",
        label="Unknown Persona",
        primary_address=VITALIK_ETH,
        confidence_score=0.75,
        tags=["initial"],
    )
    storage.save_persona_profile(p)

    # List personas
    res = client.get("/api/v1/admin/personas", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) >= 1

    # Update persona
    up_res = client.post(
        f"/api/v1/admin/personas/{p.persona_id}",
        headers=headers,
        json={"label": "Whale Entity Alpha", "tags": ["whale", "defi"]},
    )
    assert up_res.status_code == 200
    assert up_res.json()["label"] == "Whale Entity Alpha"

    # Link new wallet to persona
    link_res = client.post(
        f"/api/v1/admin/personas/{p.persona_id}",
        headers=headers,
        json={"label": "Whale Entity Alpha", "tags": ["whale", "defi"]},
    )
    assert link_res.status_code == 200
    assert link_res.json()["label"] == "Whale Entity Alpha"

    # Link new wallet to persona
    link_res = client.post(
        f"/api/v1/admin/personas/{p.persona_id}/link",
        headers=headers,
        json={
            "address": "0xsecondary_wallet_123",
            "chain": "arbitrum",
            "reason": "Confirmed telegram signature match",
            "confidence_weight": 0.99,
        },
    )
    assert link_res.status_code == 200
    data = link_res.json()
    assert len(data["clustered_wallets"]) >= 1
    assert data["confidence_score"] >= 0.90

    # Unlink the wallet
    unlink_res = client.post(
        f"/api/v1/admin/personas/{p.persona_id}/unlink",
        headers=headers,
        json={"address": "0xsecondary_wallet_123"},
    )
    assert unlink_res.status_code == 200
    assert "0xsecondary_wallet_123" not in [w["address"] for w in unlink_res.json()["clustered_wallets"]]

    # Cannot unlink primary address
    bad_unlink = client.post(
        f"/api/v1/admin/personas/{p.persona_id}/unlink",
        headers=headers,
        json={"address": VITALIK_ETH},
    )
    assert bad_unlink.status_code == 400

    # Create custom persona
    custom_res = client.post(
        "/api/v1/admin/personas",
        headers=headers,
        json={"primary_address": "0x9876543210987654321098765432109876543210", "label": "Custom Alpha"},
    )
    assert custom_res.status_code == 200
    custom_id = custom_res.json()["persona_id"]

    # Delete persona
    del_res = client.delete(f"/api/v1/admin/personas/{custom_id}", headers=headers)
    assert del_res.status_code == 200


def test_admin_tenant_and_user_management(app_client):
    client, auth_service, storage = app_client
    admin_session = auth_service.authenticate("admin", "AdminPass123!")
    headers = {"Authorization": f"Bearer {admin_session.token}"}

    # Create tenant
    ten_res = client.post("/api/v1/admin/tenants", headers=headers, json={"name": "Cyber Defense Unit"})
    assert ten_res.status_code == 200
    tenant_id = ten_res.json()["tenant_id"]

    # Admin creates user inside tenant
    user_res = client.post(
        "/api/v1/admin/users",
        headers=headers,
        json={"tenant_id": tenant_id, "username": "investigator_bob", "password": "SecurePassword1!", "role": "member"},
    )
    assert user_res.status_code == 200
    user_id = user_res.json()["user_id"]

    # Toggle user active status
    tog_res = client.post(f"/api/v1/admin/users/{user_id}/toggle-active", headers=headers)
    assert tog_res.status_code == 200
    assert tog_res.json()["is_active"] is False

    # Update user role
    role_res = client.post(f"/api/v1/admin/users/{user_id}/role", headers=headers, json={"role": "admin"})
    assert role_res.status_code == 200
    assert role_res.json()["role"] == "admin"
