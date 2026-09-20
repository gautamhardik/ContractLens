"""Tests for API Authentication, Rate Limiting, and Security Headers (Phase 10/10)."""

import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from src.api.server import app
from src.api.auth import RateLimiter, rate_limiter

client = TestClient(app)


def test_security_headers_present():
    """Verify security headers are injected into HTTP responses."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert resp.headers.get("X-XSS-Protection") == "1; mode=block"


def test_rate_limiter_logic():
    """Verify rate limiter blocks when threshold is reached."""
    limiter = RateLimiter(requests_per_minute=3)
    ip = "192.168.1.100"
    assert limiter.is_allowed(ip) is True
    assert limiter.is_allowed(ip) is True
    assert limiter.is_allowed(ip) is True
    assert limiter.is_allowed(ip) is False


def test_auth_enforcement():
    """Verify endpoint rejects requests with 401 when CONTRACTLENS_API_KEY is configured and token is missing."""
    with patch.dict(os.environ, {"CONTRACTLENS_API_KEY": "secret-enterprise-key-123"}):
        resp = client.post("/api/query", json={"query": "Test question"})
        assert resp.status_code == 401

        # Test valid X-API-Key header
        resp_valid = client.post(
            "/api/query",
            json={"query": "Test question"},
            headers={"X-API-Key": "secret-enterprise-key-123"}
        )
        assert resp_valid.status_code in (200, 503)  # 200 or 503 if corpus not loaded in test mode
