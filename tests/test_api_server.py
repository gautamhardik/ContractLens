"""Tests for ContractLens FastAPI REST server."""

import pytest
from fastapi.testclient import TestClient
from src.api.server import app, load_corpus_state, state


@pytest.fixture(scope="module")
def client():
    # Load limited corpus (first 3 docs: AMX, Access Amendment, Access MSA)
    load_corpus_state(data_raw_dir="Data/raw", max_docs=3)
    return TestClient(app)


def test_health_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["loaded_documents"] == 3
    assert data["total_obligations"] > 0


def test_portfolio_endpoint(client):
    res = client.get("/api/portfolio")
    assert res.status_code == 200
    data = res.json()
    assert data["total_contracts"] == 3
    assert "governing_laws" in data
    assert "payment_terms" in data
    assert len(data["counterparties"]) > 0


def test_contracts_list(client):
    res = client.get("/api/contracts")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 3
    assert data[0]["document_id"] == "doc_01"
    assert data[0]["contract_type"] != ""


def test_contract_detail(client):
    res = client.get("/api/contracts/doc_01")
    assert res.status_code == 200
    data = res.json()
    assert "document" in data
    assert "intelligence" in data
    assert "obligations" in data
    assert len(data["document"]["pages"]) > 0


def test_risks_endpoint(client):
    res = client.get("/api/risks")
    assert res.status_code == 200
    data = res.json()
    assert "total_signals" in data
    assert "high_risk_contracts" in data


def test_amendments_endpoint(client):
    # doc_02 is Access Amendment, doc_03 is Access MSA
    res = client.get("/api/amendments/doc_02")
    assert res.status_code == 200
    data = res.json()
    assert data["total_modifications"] > 0
    assert len(data["changes"]) > 0
    assert data["full_force_confirmed"] is True


def test_query_endpoint(client):
    # Grounded query to ContractAgent
    payload = {
        "query": "Which contracts involve E*TRADE?",
    }
    res = client.post("/api/query", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "answer" in data
    assert len(data["citations"]) >= 1
    assert data["grounding_status"].lower() in ["supported", "partially_supported"]
