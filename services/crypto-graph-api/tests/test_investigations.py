import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.infrastructure.investigation_router import router as inv_router
from src.infrastructure.auth_router import router as auth_router
from src.domain.auth_service import AuthService
from src.infrastructure.sqlite_storage import SqliteGraphStorage
from libs.blockchain_contracts.fixtures import VITALIK_ETH


@pytest.fixture
def inv_client():
    app = FastAPI()
    storage = SqliteGraphStorage(":memory:")
    auth_service = AuthService(storage)

    app.state.storage = storage
    app.state.auth_service = auth_service

    app.include_router(auth_router)
    app.include_router(inv_router)

    client = TestClient(app)
    return client, auth_service


def test_watchlist_and_investigation_multitenant_isolation(inv_client):
    client, auth_service = inv_client

    # Create 2 users in different tenants
    u1 = auth_service.register_user("investigator1", "Pass12345!", tenant_name="Firm A")
    u2 = auth_service.register_user("investigator2", "Pass12345!", tenant_name="Firm B")

    s1 = auth_service.authenticate("investigator1", "Pass12345!")
    s2 = auth_service.authenticate("investigator2", "Pass12345!")

    h1 = {"Authorization": f"Bearer {s1.token}"}
    h2 = {"Authorization": f"Bearer {s2.token}"}

    # User 1 adds to watchlist
    w_res1 = client.post(
        "/api/v1/investigations/watchlist",
        headers=h1,
        json={"address": VITALIK_ETH, "chain": "ethereum", "label": "Vitalik Main"},
    )
    assert w_res1.status_code == 200

    # User 1 can see their watchlist item
    list1 = client.get("/api/v1/investigations/watchlist", headers=h1).json()
    assert len(list1) == 1
    assert list1[0]["address"] == VITALIK_ETH.lower()

    # User 2 CANNOT see User 1's watchlist item (Multi-Tenant Isolation)
    list2 = client.get("/api/v1/investigations/watchlist", headers=h2).json()
    assert len(list2) == 0

    # Save investigation for User 1
    save_res = client.post(
        "/api/v1/investigations/saved",
        headers=h1,
        json={
            "title": "Vitalik Bridge Flow Analysis",
            "target_address": VITALIK_ETH,
            "graph_data": {"elements": {"nodes": [], "edges": []}},
        },
    )
    assert save_res.status_code == 200
    inv_id = save_res.json()["investigation_id"]

    # User 1 loads investigation
    inv_load1 = client.get(f"/api/v1/investigations/saved/{inv_id}", headers=h1)
    assert inv_load1.status_code == 200
    assert inv_load1.json()["title"] == "Vitalik Bridge Flow Analysis"

    # User 2 is blocked from loading User 1's investigation (Tenant Isolation)
    inv_load2 = client.get(f"/api/v1/investigations/saved/{inv_id}", headers=h2)
    assert inv_load2.status_code == 404

    # Remove from watchlist
    del_res = client.delete(f"/api/v1/investigations/watchlist/{VITALIK_ETH}", headers=h1)
    assert del_res.status_code == 200
    assert len(client.get("/api/v1/investigations/watchlist", headers=h1).json()) == 0
