import pytest
from fastapi.testclient import TestClient
from src.app import app
from libs.blockchain_contracts.fixtures import VITALIK_ETH, SATOSHI_BTC

client = TestClient(app)


def test_index_dashboard_render():
    response = client.get("/")
    assert response.status_code == 200
    assert "crypto-graph" in response.text
    assert "Target Address" in response.text
    assert "searchCurrentAddress" in response.text


def test_address_summary_partial():
    response = client.get(f"/partials/address-summary?address={VITALIK_ETH}")
    assert response.status_code == 200
    assert VITALIK_ETH.lower() in response.text
    assert "Verified" in response.text
    assert "Transactions" in response.text


def test_persona_card_partial():
    response = client.get(f"/partials/persona-card?address={VITALIK_ETH}")
    assert response.status_code == 200
    assert "Persona Profile" in response.text
    assert "Clustered Wallets" in response.text


def test_counterparties_partial():
    response = client.get(f"/partials/counterparties?address={VITALIK_ETH}")
    assert response.status_code == 200
    assert "Top Counterparties" in response.text
    assert "Connections" in response.text


def test_cross_chain_partial():
    response = client.get(f"/partials/cross-chain?address={VITALIK_ETH}")
    assert response.status_code == 200
    assert "Cross-Chain Flows" in response.text
    assert "Protocol" in response.text


def test_graph_data_endpoint():
    response = client.get(f"/api/graph-data?address={VITALIK_ETH}")
    assert response.status_code == 200
    data = response.json()
    assert "elements" in data
    assert len(data["elements"]["nodes"]) > 0
    assert len(data["elements"]["edges"]) > 0


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
