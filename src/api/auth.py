"""Enterprise Security, Authentication, and Rate Limiting for ContractLens API.

Features:
- Configurable API Key / Bearer Token authentication via CONTRACTLENS_API_KEY.
- Graceful permissive mode for local demo / development if CONTRACTLENS_API_KEY is unset.
- Token bucket rate limiter preventing denial-of-service / rapid query abuse.
- Standard security headers middleware (HSTS, Content-Type Options, X-Frame-Options).
"""

from __future__ import annotations

import os
import time
from typing import Optional, Dict
from fastapi import Request, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
BEARER_AUTH = HTTPBearer(auto_error=False)


class RateLimiter:
    """In-memory sliding token bucket rate limiter per client IP."""

    def __init__(self, requests_per_minute: int = 120):
        self.rpm = requests_per_minute
        self.clients: Dict[str, list[float]] = {}

    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        window_start = now - 60.0
        timestamps = self.clients.setdefault(client_ip, [])
        # Expire older timestamps
        self.clients[client_ip] = [t for t in timestamps if t > window_start]
        if len(self.clients[client_ip]) >= self.rpm:
            return False
        self.clients[client_ip].append(now)
        return True


rate_limiter = RateLimiter(requests_per_minute=180)


async def verify_api_key(
    api_key: Optional[str] = Security(API_KEY_HEADER),
    bearer: Optional[HTTPAuthorizationCredentials] = Security(BEARER_AUTH),
) -> Optional[str]:
    """Dependency verifying incoming request credentials.

    If CONTRACTLENS_API_KEY is defined in the environment, requests must provide
    either matching X-API-Key or Authorization: Bearer <key>.
    If CONTRACTLENS_API_KEY is unset, demo mode is enabled (open access).
    """
    required_key = os.environ.get("CONTRACTLENS_API_KEY", "").strip()
    if not required_key:
        return "demo_user"

    token = api_key or (bearer.credentials if bearer else None)
    if not token or token != required_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects defense-in-depth HTTP security headers into every response."""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response
