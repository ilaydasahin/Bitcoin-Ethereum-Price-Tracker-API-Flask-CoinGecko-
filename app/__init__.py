"""Application factory for the Crypto Price Tracker API."""
from __future__ import annotations

import logging
import os

from flask import Flask

from app.config import config_by_name


def create_app(config_name: str | None = None) -> Flask:
    """Create and configure a Flask application instance."""
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

    _configure_logging(app)

    from app.errors import register_error_handlers

    register_error_handlers(app)

    # Attach the CoinGecko service to the app (dependency injection via
    # app.extensions instead of a global mutable singleton).
    from app.services.coingecko import CoinGeckoService

    app.extensions["coingecko"] = CoinGeckoService(
        base_url=app.config["COINGECKO_BASE_URL"],
        cache_timeout=app.config["CACHE_DEFAULT_TIMEOUT"],
        request_timeout=app.config["REQUEST_TIMEOUT"],
    )

    from app.api.routes import api_bp

    app.register_blueprint(api_bp)

    return app


def _configure_logging(app: Flask) -> None:
    """Configure structured logging for the application."""
    log_level = getattr(logging, app.config.get("LOG_LEVEL", "INFO").upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    app.logger.setLevel(log_level)
