"""RFC 9457 problem+json error handling."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from modules.identity.application.accounts import AccountError
from modules.integrations.application.store import IntegrationError
from modules.workflows.application.manage import WorkflowError

if TYPE_CHECKING:
    from fastapi import FastAPI, Request


class ProblemDetail(Exception):
    """RFC 9457 problem detail."""

    def __init__(
        self,
        *,
        status: int = 500,
        title: str = "Internal Server Error",
        detail: str | None = None,
        type_uri: str = "about:blank",
        instance: str | None = None,
        extensions: dict[str, Any] | None = None,
    ) -> None:
        self.status = status
        self.title = title
        self.detail = detail
        self.type_uri = type_uri
        self.instance = instance
        self.extensions = extensions or {}
        super().__init__(detail or title)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to RFC 9457 format."""
        body: dict[str, Any] = {
            "type": self.type_uri,
            "title": self.title,
            "status": self.status,
        }
        if self.detail:
            body["detail"] = self.detail
        if self.instance:
            body["instance"] = self.instance
        body.update(self.extensions)
        return body


logger = structlog.get_logger()

_DOMAIN_ERRORS = (AccountError, IntegrationError, WorkflowError)


def _problem(status: int, title: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"type": "about:blank", "title": title, "status": status},
        media_type="application/problem+json",
    )


def register_error_handlers(app: FastAPI) -> None:
    """Register global error handlers returning problem+json. Never leaks stack traces."""

    @app.exception_handler(AccountError)
    @app.exception_handler(IntegrationError)
    @app.exception_handler(WorkflowError)
    async def domain_handler(_: Request, exc: Exception) -> JSONResponse:
        assert isinstance(exc, _DOMAIN_ERRORS)
        return _problem(exc.status, exc.message)

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("request.failed", path=request.url.path)
        return _problem(500, "Something went wrong. Please try again.")

    @app.exception_handler(ProblemDetail)
    async def problem_handler(_: Request, exc: ProblemDetail) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status,
            content=exc.to_dict(),
            media_type="application/problem+json",
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "type": "about:blank",
                "title": exc.detail if isinstance(exc.detail, str) else "Error",
                "status": exc.status_code,
            },
            media_type="application/problem+json",
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "type": "urn:nudgeline:validation-error",
                "title": "Validation Error",
                "status": 422,
                "errors": [
                    {
                        "field": ".".join(str(loc) for loc in e["loc"]),
                        "message": e["msg"],
                        "type": e["type"],
                    }
                    for e in exc.errors()
                ],
            },
            media_type="application/problem+json",
        )
