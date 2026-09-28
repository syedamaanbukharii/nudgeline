"""Idempotency-Key middleware for safe POST retries."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import structlog
from fastapi import Request
from sqlalchemy import select
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from apps.api.middleware.errors import ProblemDetail
from modules.tenancy.adapters.database import get_session_factory
from modules.tenancy.domain.models import IdempotencyRecord

logger = structlog.get_logger()

_IDEMPOTENCY_TTL = timedelta(hours=24)


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """Enforce Idempotency-Key on POST requests."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method != "POST":
            return await call_next(request)

        idem_key = request.headers.get("idempotency-key")
        if not idem_key:
            return await call_next(request)

        tenant_id = getattr(request.state, "tenant_id", None)
        if tenant_id is None:
            return await call_next(request)

        factory = get_session_factory()
        async with factory() as session:
            result = await session.execute(
                select(IdempotencyRecord).where(
                    IdempotencyRecord.key == idem_key,
                    IdempotencyRecord.tenant_id == tenant_id,
                )
            )
            existing = result.scalar_one_or_none()

            if existing is not None:
                if existing.expires_at < datetime.now(timezone.utc):
                    await session.delete(existing)
                    await session.commit()
                else:
                    from fastapi.responses import ORJSONResponse

                    return ORJSONResponse(
                        status_code=existing.status_code,
                        content=existing.response_body,
                        headers={"Idempotency-Replayed": "true"},
                    )

        response = await call_next(request)

        if 200 <= response.status_code < 300:
            body = b""
            async for chunk in response.body_iterator:
                if isinstance(chunk, str):
                    body += chunk.encode()
                else:
                    body += chunk

            import orjson

            try:
                response_data = orjson.loads(body)
            except Exception:
                response_data = None

            async with factory() as session:
                record = IdempotencyRecord(
                    key=idem_key,
                    tenant_id=tenant_id,
                    status_code=response.status_code,
                    response_body=response_data,
                    expires_at=datetime.now(timezone.utc) + _IDEMPOTENCY_TTL,
                )
                session.add(record)
                await session.commit()

            from fastapi.responses import Response as FastAPIResponse

            return FastAPIResponse(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

        return response
