"""Errors that are safe to show to clients: a fixed code and a short, generic message."""

from __future__ import annotations


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


def not_found() -> ApiError:
    return ApiError(404, "session_not_found", "Your planning session has expired. Please start a new one.")
