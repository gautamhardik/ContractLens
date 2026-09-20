"""Integration and Unit Tests for NVIDIA NIM Provider (Phase 10/10)."""

import os
import json
import pytest
from unittest.mock import patch, MagicMock

from src.rag.nvidia_provider import NvidiaNIMProvider
from src.rag.generator import FakeLLMProvider, get_default_llm_provider
from src.retrieval.nvidia_embed import NvidiaDenseRetriever
from src.models.chunk import RetrievalChunk


def test_nvidia_provider_fallback_when_unconfigured():
    """Verify that NvidiaNIMProvider falls back gracefully when API key is missing."""
    with patch.dict(os.environ, {"NVIDIA_API_KEY": ""}):
        provider = NvidiaNIMProvider(api_key="")
        result = provider.generate("system prompt", "QUESTION: What is the agreement?")
        data = json.loads(result)
        assert "answer" in data
        assert "claims" in data


def test_nvidia_provider_retry_and_mock_response():
    """Verify JSON parsing and handling with mock HTTP 200 response."""
    mock_payload = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "answer": "Payment is due within 30 days [E1].",
                        "claims": [{"text": "Payment is due within 30 days", "evidence_ids": ["E1"]}]
                    })
                }
            }
        ]
    }
    
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps(mock_payload).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        provider = NvidiaNIMProvider(api_key="nvapi-mock-test")
        result = provider.generate("sys", "user")
        data = json.loads(result)
        assert data["answer"] == "Payment is due within 30 days [E1]."
        assert len(data["claims"]) == 1
        assert data["claims"][0]["evidence_ids"] == ["E1"]


def test_get_default_llm_provider_factory():
    """Verify factory returns NvidiaNIMProvider when NVIDIA_API_KEY is present."""
    with patch.dict(os.environ, {"NVIDIA_API_KEY": "nvapi-test-key"}):
        provider = get_default_llm_provider()
        assert isinstance(provider, NvidiaNIMProvider)

    with patch.dict(os.environ, {"NVIDIA_API_KEY": "", "LLM_PROVIDER": "fake"}):
        provider = get_default_llm_provider()
        assert isinstance(provider, FakeLLMProvider)


def test_nvidia_dense_retriever_cosine_similarity():
    """Verify mathematical correctness of cosine similarity."""
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    v3 = [0.0, 1.0, 0.0]
    assert pytest.approx(NvidiaDenseRetriever._cosine_similarity(v1, v2), 0.001) == 1.0
    assert pytest.approx(NvidiaDenseRetriever._cosine_similarity(v1, v3), 0.001) == 0.0
