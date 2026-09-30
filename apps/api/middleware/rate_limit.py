"""GCRA rate limiter backed by Valkey."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from apps.api.middleware.errors import ProblemDetail

if TYPE_CHECKING:
    from starlette.requests import Request
    from starlette.responses import Response

logger = structlog.get_logger()

# GCRA Lua script for atomic rate limiting
_GCRA_SCRIPT = """
local key = KEYS[1]
local emission_interval = tonumber(ARGV[1])
local burst = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local limit = burst * emission_interval

local tat = tonumber(redis.call('GET', key) or '0')
if tat == 0 then
    tat = now
end

local new_tat = math.max(tat, now) + emission_interval
local allow_at = new_tat - limit

if allow_at > now then
    local retry_after = allow_at - now
    return {0, tostring(retry_after), tostring(math.ceil(limit / emission_interval))}
end

redis.call('SET', key, tostring(new_tat), 'EX', math.ceil(limit))
local remaining = math.floor((limit - (new_tat - now)) / emission_interval)
return {1, tostring(remaining), tostring(math.ceil(limit / emission_interval))}
"""


class RateLimitMiddleware(BaseHTTPMiddleware):
    """GCRA rate limiter per API key and per tenant."""

    def __init__(self, app, valkey_pool=None, per_key: int = 100, per_tenant: int = 1000):
        super().__init__(app)
        self.valkey_pool = valkey_pool
        self.per_key = per_key
        self.per_tenant = per_tenant

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if self.valkey_pool is None:
            return await call_next(request)

        api_key_id = getattr(request.state, "api_key_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        if api_key_id:
            allowed, headers = await self._check(f"rl:key:{api_key_id}", self.per_key)
            if not allowed:
                raise ProblemDetail(
                    status=429,
                    title="Rate Limit Exceeded",
                    detail="API key rate limit exceeded",
                    extensions=headers,
                )

        if tenant_id:
            allowed, headers = await self._check(f"rl:tenant:{tenant_id}", self.per_tenant)
            if not allowed:
                raise ProblemDetail(
                    status=429,
                    title="Rate Limit Exceeded",
                    detail="Tenant rate limit exceeded",
                    extensions=headers,
                )

        response = await call_next(request)
        return response

    async def _check(self, key: str, rate: int) -> tuple[bool, dict]:
        emission_interval = 60.0 / rate
        burst = rate
        now = time.time()

        result = await self.valkey_pool.eval(_GCRA_SCRIPT, 1, key, emission_interval, burst, now)

        allowed = bool(result[0])
        headers = {
            "RateLimit-Remaining": str(result[1]),
            "RateLimit-Limit": str(result[2]),
        }
        if not allowed:
            headers["Retry-After"] = str(result[1])
        return allowed, headers
