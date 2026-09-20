"""Test Dynamic Contract Upload and Live Ingestion.

Verifies POST /api/contracts/upload:
1. Rejection of non-PDF files.
2. Ingestion of a valid contract PDF into live state.
3. Automatic rebuilding of indices, knowledge graph, and query answering for the newly uploaded document.
"""

import io
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from src.api.server import app, state, load_corpus_state


@pytest.fixture(scope="module")
def client():
    load_corpus_state(max_docs=2)
    return TestClient(app)


def test_upload_rejects_non_pdf(client):
    """Verify that non-PDF uploads are rejected with HTTP 400."""
    response = client.post(
        "/api/contracts/upload",
        files={"file": ("test.txt", b"some text content", "text/plain")}
    )
    assert response.status_code == 400
    assert "Only PDF files" in response.json()["detail"]


def test_upload_ingests_contract_dynamically(client):
    """Verify that uploading a valid PDF ingests it, extracts intelligence, and updates state."""
    raw_pdf = Path("Data/raw/Turtle Beach-Foxconn MSA.pdf")
    if not raw_pdf.exists():
        # Fallback to any existing PDF
        pdfs = list(Path("Data/raw").glob("*.pdf"))
        if not pdfs:
            pytest.skip("No PDF found in Data/raw")
        raw_pdf = pdfs[0]

    with open(raw_pdf, "rb") as f:
        pdf_bytes = f.read()

    initial_doc_count = len(state.documents)

    response = client.post(
        "/api/contracts/upload",
        files={"file": ("uploaded_test_agreement.pdf", pdf_bytes, "application/pdf")}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    uploaded_doc_id = data["document_id"]
    assert uploaded_doc_id in state.documents
    assert len(state.documents) == initial_doc_count + 1

    # Verify that get_contract_detail retrieves the newly uploaded doc
    detail_resp = client.get(f"/api/contracts/{uploaded_doc_id}")
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()
    assert detail_data["document"]["document_id"] == uploaded_doc_id
    assert len(detail_data["document"]["pages"]) > 0

    # Verify query answering works over the new document
    query_resp = client.post("/api/query", json={"query": "Who are the parties in this manufacturing agreement?", "document_id": uploaded_doc_id})
    assert query_resp.status_code == 200
    query_data = query_resp.json()
    assert len(query_data["answer"]) > 0
