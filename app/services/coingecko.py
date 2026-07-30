"""HTTP client for the public CoinGecko API.

Features:
- requests.Session with retry/backoff for 429/5xx responses
- thread-safe in-process TTL cache (single lock around read/write)
- upstream errors are translated into safe APIError subclasses
"""
from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterable, Tuple, Union

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from app.errors import NotFoundError, UpstreamServiceError

logger = logging.getLogger(__name__)

CacheEntry = Tuple[Any, float]


class CoinGeckoService:
    """Thin, resilient wrapper around the CoinGecko REST API."""

    def __init__(
        self,
        base_url: str = "https://api.coingecko.com/api/v3",
        cache_timeout: int = 60,
        request_timeout: int = 10,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.cache_timeout = cache_timeout
        self.request_timeout = request_timeout
        self._cache: Dict[str, CacheEntry] = {}
        self._cache_lock = threading.Lock()

        # Configure resilient Session with retries
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "CryptoPriceTrackerAPI/1.0",
                "Accept": "application/json",
            }
        )
        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            raise_on_status=False,
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _get_cached_or_fetch(self, cache_key: str, fetch_fn: Callable[[], Any]) -> Any:
        """Return a cached value if fresh, otherwise fetch and cache it."""
        now = time.time()
        if self.cache_timeout > 0:
            with self._cache_lock:
                entry = self._cache.get(cache_key)
            if entry is not None:
                data, timestamp = entry
                if now - timestamp < self.cache_timeout:
                    logger.debug("Cache hit for %s", cache_key)
                    return data

        logger.debug("Cache miss for %s, fetching from upstream", cache_key)
        data = fetch_fn()
        if self.cache_timeout > 0:
            with self._cache_lock:
                self._cache[cache_key] = (data, now)
        return data

    def _request_json(self, path: str, params: Dict[str, Any], resource_name: str) -> Any:
        """Perform a GET request and translate failures into safe API errors."""
        url = f"{self.base_url}/{path.lstrip('/')}"
        try:
            resp = self.session.get(url, params=params, timeout=self.request_timeout)
        except requests.RequestException as exc:
            logger.exception("CoinGecko request to %s failed: %s", url, exc)
            raise UpstreamServiceError() from exc

        if resp.status_code == 404:
            logger.info("CoinGecko returned 404 for %s", url)
            raise NotFoundError(f"{resource_name} not found")
        if resp.status_code == 429:
            logger.warning("CoinGecko rate limit hit for %s", url)
            raise UpstreamServiceError(
                "Upstream rate limit exceeded, please try again in a minute", 503
            )
        if not resp.ok:
            logger.error("CoinGecko returned HTTP %s for %s", resp.status_code, url)
            raise UpstreamServiceError()

        try:
            return resp.json()
        except ValueError as exc:
            logger.exception("CoinGecko returned invalid JSON for %s", url)
            raise UpstreamServiceError() from exc

    @staticmethod
    def _format_timestamp(unix_seconds: Union[int, float, None]) -> str:
        moment = (
            datetime.fromtimestamp(unix_seconds, tz=timezone.utc)
            if unix_seconds
            else datetime.now(timezone.utc)
        )
        return moment.strftime("%Y-%m-%d %H:%M:%S UTC")

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def get_simple_price(
        self,
        coin_ids: Union[Iterable[str], str] = ("bitcoin", "ethereum"),
        vs_currency: str = "usd",
    ) -> Dict[str, Dict[str, Any]]:
        """Return current price info for one or more coins."""
        ids_str = ",".join(coin_ids) if isinstance(coin_ids, (list, tuple)) else str(coin_ids)
        cache_key = f"simple_price_{ids_str}_{vs_currency}"

        def _fetch() -> Dict[str, Dict[str, Any]]:
            params = {
                "ids": ids_str,
                "vs_currencies": vs_currency,
                "include_24hr_change": "true",
                "include_last_updated_at": "true",
            }
            raw_data = self._request_json("simple/price", params, "Requested coins")

            results: Dict[str, Dict[str, Any]] = {}
            for coin_id in ids_str.split(","):
                coin_data = raw_data.get(coin_id, {})
                results[coin_id] = {
                    "coin": coin_id.capitalize(),
                    "price": coin_data.get(vs_currency),
                    "currency": vs_currency.upper(),
                    "change_24h": round(coin_data.get(f"{vs_currency}_24h_change") or 0.0, 2),
                    "timestamp": self._format_timestamp(coin_data.get("last_updated_at")),
                }
            return results

        return self._get_cached_or_fetch(cache_key, _fetch)

    def get_coin_metadata(self, coin_id: str = "bitcoin") -> Dict[str, Any]:
        """Return market metadata for a single coin."""
        cache_key = f"coin_meta_{coin_id}"

        def _fetch() -> Dict[str, Any]:
            params = {
                "localization": "false",
                "tickers": "false",
                "community_data": "false",
                "developer_data": "false",
            }
            data = self._request_json(f"coins/{coin_id}", params, f"Coin '{coin_id}'")
            market_data = data.get("market_data", {})

            return {
                "id": data.get("id"),
                "name": data.get("name"),
                "symbol": data.get("symbol", "").upper(),
                "market_cap_usd": market_data.get("market_cap", {}).get("usd"),
                "current_price_usd": market_data.get("current_price", {}).get("usd"),
                "total_supply": market_data.get("total_supply"),
                "circulating_supply": market_data.get("circulating_supply"),
                "high_24h_usd": market_data.get("high_24h", {}).get("usd"),
                "low_24h_usd": market_data.get("low_24h", {}).get("usd"),
            }

        return self._get_cached_or_fetch(cache_key, _fetch)

    def get_market_chart(
        self, coin_id: str = "bitcoin", vs_currency: str = "usd", days: int = 1
    ) -> Dict[str, Any]:
        """Return historical price points for a coin over the given period."""
        cache_key = f"chart_{coin_id}_{vs_currency}_{days}"

        def _fetch() -> Dict[str, Any]:
            params = {"vs_currency": vs_currency, "days": days}
            raw_chart = self._request_json(
                f"coins/{coin_id}/market_chart", params, f"Coin '{coin_id}'"
            )

            prices = [
                {
                    "timestamp": self._format_timestamp(item[0] / 1000.0),
                    "price": item[1],
                }
                for item in raw_chart.get("prices", [])
            ]
            return {
                "coin": coin_id.capitalize(),
                "currency": vs_currency.upper(),
                "days": days,
                "prices": prices,
            }

        return self._get_cached_or_fetch(cache_key, _fetch)
