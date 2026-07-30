"""Unit tests for the CoinGeckoService TTL cache."""
import threading

from app.services.coingecko import CoinGeckoService


def test_cache_returns_cached_value_within_ttl():
    service = CoinGeckoService(cache_timeout=60)
    calls = []

    def fetch():
        calls.append(1)
        return {'value': len(calls)}

    first = service._get_cached_or_fetch('key', fetch)
    second = service._get_cached_or_fetch('key', fetch)

    assert first == second == {'value': 1}
    assert len(calls) == 1


def test_cache_disabled_when_timeout_zero():
    service = CoinGeckoService(cache_timeout=0)
    calls = []

    def fetch():
        calls.append(1)
        return len(calls)

    assert service._get_cached_or_fetch('key', fetch) == 1
    assert service._get_cached_or_fetch('key', fetch) == 2


def test_cache_is_thread_safe_under_concurrent_access():
    service = CoinGeckoService(cache_timeout=60)
    errors = []

    def worker(worker_id: int):
        try:
            for i in range(200):
                service._get_cached_or_fetch(f'key_{worker_id}_{i % 10}', lambda: i)
        except Exception as exc:  # pragma: no cover
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(n,)) for n in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors
