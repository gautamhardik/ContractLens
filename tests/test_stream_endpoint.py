import pytest
from fastapi.testclient import TestClient
from src.api.server import app, load_corpus_state

@pytest.fixture(scope="module")
def client():
    load_corpus_state(data_raw_dir="Data/raw", max_docs=3)
    return TestClient(app)

def test_query_stream_endpoint(client):
    """Verify that /api/query/stream returns text/event-stream with status, token, and complete events."""
    with client.stream("POST", "/api/query/stream", json={"query": "What are the payment terms?"}) as resp:
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")
        
        events_found = []
        for line in resp.iter_lines():
            if line.startswith("event:"):
                events_found.append(line.split(":", 1)[1].strip())
        
        assert "status" in events_found
        assert "token" in events_found
        assert "complete" in events_found
