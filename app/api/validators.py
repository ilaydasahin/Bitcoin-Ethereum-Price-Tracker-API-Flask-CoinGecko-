"""Request parameter validation helpers for the API routes."""
from __future__ import annotations

import re
from typing import List

from app.errors import ValidationError

# CoinGecko coin ids are lowercase slugs (e.g. "bitcoin", "matic-network").
COIN_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,49}$")

SUPPORTED_VS_CURRENCIES = frozenset(
    {"usd", "eur", "gbp", "try", "jpy", "chf", "cad", "aud", "btc", "eth"}
)

MAX_COINS_PER_REQUEST = 10
MIN_HISTORY_DAYS = 1
MAX_HISTORY_DAYS = 365


def validate_vs_currency(raw_value: str) -> str:
    """Validate and normalize the vs_currency query parameter."""
    vs_currency = (raw_value or "").strip().lower()
    if vs_currency not in SUPPORTED_VS_CURRENCIES:
        supported = ", ".join(sorted(SUPPORTED_VS_CURRENCIES))
        raise ValidationError(
            f"Unsupported vs_currency '{vs_currency}'. Supported values: {supported}"
        )
    return vs_currency


def validate_coin_id(raw_value: str) -> str:
    """Validate and normalize a single coin id."""
    coin_id = (raw_value or "").strip().lower()
    if not COIN_ID_PATTERN.match(coin_id):
        raise ValidationError(
            f"Invalid coin id '{raw_value}'. Expected a lowercase slug like 'bitcoin'"
        )
    return coin_id


def validate_coin_list(raw_value: str) -> List[str]:
    """Validate and normalize the comma-separated coins query parameter."""
    coin_ids = [part.strip().lower() for part in (raw_value or "").split(",") if part.strip()]
    if not coin_ids:
        raise ValidationError("Parameter 'coins' must contain at least one coin id")
    if len(coin_ids) > MAX_COINS_PER_REQUEST:
        raise ValidationError(
            f"Too many coins requested ({len(coin_ids)}). Maximum is {MAX_COINS_PER_REQUEST}"
        )
    return [validate_coin_id(coin_id) for coin_id in coin_ids]


def validate_days(raw_value: str) -> int:
    """Validate and convert the days query parameter to an int."""
    try:
        days = int(raw_value)
    except (TypeError, ValueError):
        raise ValidationError(
            f"Parameter 'days' must be an integer, got '{raw_value}'"
        ) from None
    if not MIN_HISTORY_DAYS <= days <= MAX_HISTORY_DAYS:
        raise ValidationError(
            f"Parameter 'days' must be between {MIN_HISTORY_DAYS} and {MAX_HISTORY_DAYS}"
        )
    return days
