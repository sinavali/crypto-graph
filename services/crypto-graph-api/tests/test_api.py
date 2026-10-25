import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.infrastructure.api_router import router
from libs.blockchain_contracts.fixtures import VITALIK_ETH

app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_address_lookup_endpoint():
    response = client.post("/api/v1/address/lookup", json={"address": VITALIK_ETH})
    assert response.status_code == 200
    data = response.json()
    assert data["address"] == VITALIK_ETH.lower()
    assert "ethereum" in data["detected_ecosystems"]
    assert data["transaction_count"] > 0


def test_address_graph_endpoint():
    response = client.get(f"/api/v1/address/{VITALIK_ETH}/graph")
    assert response.status_code == 200
    data = response.json()
    assert "elements" in data
    assert len(data["elements"]["nodes"]) > 0
    assert len(data["elements"]["edges"]) > 0


def test_address_persona_endpoint():
    response = client.get(f"/api/v1/address/{VITALIK_ETH}/persona")
    assert response.status_code == 200
    data = response.json()
    assert "persona_id" in data
    assert data["confidence_score"] > 0.0


def test_address_cross_chain_endpoint():
    response = client.get(f"/api/v1/address/{VITALIK_ETH}/cross-chain")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
