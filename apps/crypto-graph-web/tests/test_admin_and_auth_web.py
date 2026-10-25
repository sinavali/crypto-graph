import pytest
from fastapi.testclient import TestClient
from src.app import app, captcha_engine, auth_service, storage
from libs.blockchain_contracts.auth_models import UserRole
from libs.blockchain_contracts.config_models import WatchlistItem, InvestigationRecord, SearchHistoryRecord
from libs.blockchain_contracts.models import PersonaProfile, ClusteredWallet, ChainEcosystem
from datetime import datetime, timezone

client = TestClient(app)


def test_auth_login_view_renders_captcha():
    response = client.get("/auth/login")
    assert response.status_code == 200
    assert "Sign In" in response.text
    assert "Security Challenge" in response.text
    assert "<svg" in response.text
    assert 'name="captcha_id"' in response.text


def test_auth_register_view_renders():
    response = client.get("/auth/register")
    assert response.status_code == 200
    assert "Create a multi-tenant investigator workspace" in response.text
    assert "Organization / Tenant Name" in response.text
    assert "<svg" in response.text


def test_register_action_captcha_validation():
    # Submit with wrong captcha
    res = client.post(
        "/auth/register",
        data={
            "tenant_name": "Acme Corp",
            "username": "investigator_alice",
            "password": "Password123!",
            "captcha_id": "invalid_id",
            "captcha_solution": "wrong",
        },
    )
    assert res.status_code == 200
    assert "Invalid or expired security captcha solution" in res.text

    # Generate valid challenge
    cid, _ = captcha_engine.generate_challenge()
    challenge = captcha_engine._challenges[cid]
    # Solve question
    txt = challenge.question_text
    if "+" in txt:
        parts = txt.replace(" = ?", "").split("+")
        sol = str(int(parts[0].strip()) + int(parts[1].strip()))
    elif "-" in txt:
        parts = txt.replace(" = ?", "").split("-")
        sol = str(int(parts[0].strip()) - int(parts[1].strip()))
    elif "×" in txt:
        parts = txt.replace(" = ?", "").split("×")
        sol = str(int(parts[0].strip()) * int(parts[1].strip()))
    else:
        sol = txt.replace(" ", "")

    res_valid = client.post(
        "/auth/register",
        data={
            "tenant_name": "Apex Intelligence",
            "username": "alice_registered",
            "password": "Password123!",
            "captcha_id": cid,
            "captcha_solution": sol,
        },
        follow_redirects=False,
    )
    assert res_valid.status_code == 303
    assert res_valid.headers["location"] == "/"
    assert "session_token" in res_valid.cookies


def test_login_action_and_session_cookie():
    # Attempt with wrong password
    cid, _ = captcha_engine.generate_challenge()
    challenge = captcha_engine._challenges[cid]
    txt = challenge.question_text
    if "+" in txt:
        parts = txt.replace(" = ?", "").split("+")
        sol = str(int(parts[0].strip()) + int(parts[1].strip()))
    elif "-" in txt:
        parts = txt.replace(" = ?", "").split("-")
        sol = str(int(parts[0].strip()) - int(parts[1].strip()))
    elif "×" in txt:
        parts = txt.replace(" = ?", "").split("×")
        sol = str(int(parts[0].strip()) * int(parts[1].strip()))
    else:
        sol = txt.replace(" ", "")

    bad_login = client.post(
        "/auth/login",
        data={
            "username": "admin",
            "password": "WrongPassword!",
            "captcha_id": cid,
            "captcha_solution": sol,
        },
    )
    assert bad_login.status_code == 200
    assert "Invalid credentials" in bad_login.text

    # Login with correct admin password
    cid2, _ = captcha_engine.generate_challenge()
    challenge2 = captcha_engine._challenges[cid2]
    txt2 = challenge2.question_text
    if "+" in txt2:
        parts = txt2.replace(" = ?", "").split("+")
        sol2 = str(int(parts[0].strip()) + int(parts[1].strip()))
    elif "-" in txt2:
        parts = txt2.replace(" = ?", "").split("-")
        sol2 = str(int(parts[0].strip()) - int(parts[1].strip()))
    elif "×" in txt2:
        parts = txt2.replace(" = ?", "").split("×")
        sol2 = str(int(parts[0].strip()) * int(parts[1].strip()))
    else:
        sol2 = txt2.replace(" ", "")

    good_login = client.post(
        "/auth/login",
        data={
            "username": "admin",
            "password": "AdminPass123!",
            "captcha_id": cid2,
            "captcha_solution": sol2,
        },
        follow_redirects=False,
    )
    assert good_login.status_code == 303
    assert "session_token" in good_login.cookies


def test_admin_pages_authorization_gate():
    # Anonymous unauthenticated requests redirect to /auth/login
    client.cookies.clear()
    for path in ["/admin/config", "/admin/personas", "/admin/tenants"]:
        res = client.get(path, follow_redirects=False)
        assert res.status_code == 303
        assert res.headers["location"] == "/auth/login"

    # Authenticate as member (non-admin)
    member_user = auth_service.register_user("member_bob", "Password123!", role=UserRole.MEMBER)
    member_session = auth_service.authenticate("member_bob", "Password123!")
    client.cookies.set("session_token", member_session.token)

    for path in ["/admin/config", "/admin/personas", "/admin/tenants"]:
        res_member = client.get(path, follow_redirects=False)
        assert res_member.status_code == 303
        assert res_member.headers["location"] == "/auth/login"

    # Authenticate as admin
    admin_session = auth_service.authenticate("admin", "AdminPass123!")
    client.cookies.set("session_token", admin_session.token)

    # Admin access succeeds on all views
    res_cfg = client.get("/admin/config")
    assert res_cfg.status_code == 200
    assert "System Configuration Engine" in res_cfg.text
    assert "Multi-Chain RPC Pools" in res_cfg.text

    res_per = client.get("/admin/personas")
    assert res_per.status_code == 200
    assert "Persona Profile Administration" in res_per.text

    res_ten = client.get("/admin/tenants")
    assert res_ten.status_code == 200
    assert "Multi-Tenant & User Directory" in res_ten.text


def test_investigation_panel_partial_multitenant():
    # Unauthenticated partial
    client.cookies.clear()
    unauth_res = client.get("/partials/investigation-panel")
    assert unauth_res.status_code == 200
    assert "Sign in to isolate your investigations" in unauth_res.text

    # Seed watchlist and investigation for admin tenant
    admin_session = auth_service.authenticate("admin", "AdminPass123!")
    storage.add_to_watchlist(
        WatchlistItem(
            id="watch-01",
            tenant_id=admin_session.tenant_id,
            address="0xd8da6bf26964af9d7eed9e03e53415d37aa96045",
            label="Vitalik Ethereum",
            chain="ethereum",
        )
    )
    storage.save_investigation(
        InvestigationRecord(
            investigation_id="inv-01",
            tenant_id=admin_session.tenant_id,
            user_id=admin_session.user_id,
            title="Vitalik Stargate Bridge Investigation",
            target_address="0xd8da6bf26964af9d7eed9e03e53415d37aa96045",
            graph_data_json="{}",
        )
    )

    client.cookies.set("session_token", admin_session.token)
    auth_res = client.get("/partials/investigation-panel")
    assert auth_res.status_code == 200
    assert "Vitalik Ethereum" in auth_res.text
    assert "Vitalik Stargate Bridge Investigation" in auth_res.text


def test_logout_clears_cookie():
    admin_session = auth_service.authenticate("admin", "AdminPass123!")
    client.cookies.set("session_token", admin_session.token)
    res = client.post("/auth/logout", follow_redirects=False)
    assert res.status_code == 303
    assert res.headers["location"] == "/"


def test_index_view_with_authenticated_search_and_bearer_token():
    admin_session = auth_service.authenticate("admin", "AdminPass123!")
    client.cookies.clear()
    # Test Bearer header fallback
    headers = {"Authorization": f"Bearer {admin_session.token}"}
    res = client.get("/?address=0xd8da6bf26964af9d7eed9e03e53415d37aa96045", headers=headers)
    assert res.status_code == 200
    assert "admin" in res.text

    # Verify search was recorded in tenant history
    history = storage.get_search_history(admin_session.tenant_id)
    assert any(h.address == "0xd8da6bf26964af9d7eed9e03e53415d37aa96045" for h in history)


def test_register_action_duplicate_username_error():
    cid, _ = captcha_engine.generate_challenge()
    challenge = captcha_engine._challenges[cid]
    txt = challenge.question_text
    if "+" in txt:
        parts = txt.replace(" = ?", "").split("+")
        sol = str(int(parts[0].strip()) + int(parts[1].strip()))
    elif "-" in txt:
        parts = txt.replace(" = ?", "").split("-")
        sol = str(int(parts[0].strip()) - int(parts[1].strip()))
    elif "×" in txt:
        parts = txt.replace(" = ?", "").split("×")
        sol = str(int(parts[0].strip()) * int(parts[1].strip()))
    else:
        sol = txt.replace(" ", "")

    # 'admin' is already registered
    res = client.post(
        "/auth/register",
        data={
            "tenant_name": "Core Org",
            "username": "admin",
            "password": "Password123!",
            "captcha_id": cid,
            "captcha_solution": sol,
        },
    )
    assert res.status_code == 200
    assert "already registered" in res.text
