"""Exception handlers that return a fixed JSON shape and never leak internals."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..utils.errors import ApiError

log = logging.getLogger("travel_partner.errors")


def _error(status: int, code: str, message: str, headers: dict | None = None) -> JSONResponse:
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status, headers=headers)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def api_error(_: Request, exc: ApiError) -> JSONResponse:
        return _error(exc.status, exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        # Report which fields failed, but never echo the submitted values back.
        fields = sorted({".".join(str(p) for p in e["loc"] if p != "body") for e in exc.errors()})
        return _error(422, "invalid_request", f"Invalid or missing fields: {', '.join(fields) or 'body'}.")

    @app.exception_handler(RateLimitExceeded)
    async def rate_limited(_: Request, __: RateLimitExceeded) -> JSONResponse:
        return _error(429, "rate_limited", "Too many requests. Please slow down a little.", {"Retry-After": "60"})

    @app.exception_handler(StarletteHTTPException)
    async def http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = {404: "not_found", 405: "method_not_allowed"}.get(exc.status_code, "http_error")
        message = "Not found." if exc.status_code == 404 else "Request could not be processed."
        return _error(exc.status_code, code, message)

    @app.exception_handler(Exception)
    async def unhandled(_: Request, exc: Exception) -> JSONResponse:
        log.error("unhandled error: %s", type(exc).__name__)
        return _error(500, "internal_error", "Something went wrong on our side. Please try again.")
