"""Centralized error handling for the API.

All handlers return a consistent JSON envelope and never leak internal
exception details to the client. Full tracebacks are written to the log.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Tuple

import requests
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)

JsonResponse = Tuple[Any, int]


class APIError(Exception):
    """Base class for errors that are safe to expose to the client."""

    status_code: int = 500
    message: str = "Internal server error"

    def __init__(self, message: str | None = None, status_code: int | None = None) -> None:
        super().__init__(message or self.message)
        if message is not None:
            self.message = message
        if status_code is not None:
            self.status_code = status_code

    def to_dict(self) -> Dict[str, Any]:
        return {"status": "error", "message": self.message}


class ValidationError(APIError):
    """Raised when client input fails validation (HTTP 400)."""

    status_code = 400
    message = "Invalid request parameters"


class NotFoundError(APIError):
    """Raised when a requested resource does not exist (HTTP 404)."""

    status_code = 404
    message = "Resource not found"


class UpstreamServiceError(APIError):
    """Raised when the upstream data provider fails (HTTP 502)."""

    status_code = 502
    message = "Upstream data provider is unavailable, please try again later"


def register_error_handlers(app: Flask) -> None:
    """Attach JSON error handlers to the application."""

    @app.errorhandler(APIError)
    def handle_api_error(error: APIError) -> JsonResponse:
        if error.status_code >= 500:
            logger.error("API error: %s", error.message)
        else:
            logger.info("Client error (%s): %s", error.status_code, error.message)
        return jsonify(error.to_dict()), error.status_code

    @app.errorhandler(requests.RequestException)
    def handle_upstream_error(error: requests.RequestException) -> JsonResponse:
        # Log the real cause server-side; expose only a generic message.
        logger.exception("Upstream request failed: %s", error)
        return jsonify(UpstreamServiceError().to_dict()), UpstreamServiceError.status_code

    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException) -> JsonResponse:
        return (
            jsonify({"status": "error", "message": error.description or error.name}),
            error.code or 500,
        )

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception) -> JsonResponse:
        # Never leak internals (str(e)) to the client.
        logger.exception("Unhandled exception: %s", error)
        return jsonify({"status": "error", "message": "Internal server error"}), 500
