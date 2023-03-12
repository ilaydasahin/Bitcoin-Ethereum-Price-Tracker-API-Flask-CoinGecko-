import time
import requests
from datetime import datetime, timezone
from urllib3.util import Retry
from requests.adapters import HTTPAdapter

class CoinGeckoService:
    def __init__(self, base_url="https://api.coingecko.com/api/v3", cache_timeout=60, request_timeout=10):
        self.base_url = base_url.rstrip('/')
        self.cache_timeout = cache_timeout
        self.request_timeout = request_timeout
        self._cache = {}
        
        # Configure resilient Session with retries
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CryptoPriceTrackerAPI/1.0',
            'Accept': 'application/json'
        })
        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            raise_on_status=False
        )
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

    def _get_cached_or_fetch(self, cache_key, fetch_fn):
        now = time.time()
        if self.cache_timeout > 0 and cache_key in self._cache:
            data, timestamp = self._cache[cache_key]
            if now - timestamp < self.cache_timeout:
                return data
        
        data = fetch_fn()
        if self.cache_timeout > 0:
            self._cache[cache_key] = (data, now)
        return data

    def get_simple_price(self, coin_ids=('bitcoin', 'ethereum'), vs_currency='usd'):
        ids_str = ','.join(coin_ids) if isinstance(coin_ids, (list, tuple)) else coin_ids
        cache_key = f"simple_price_{ids_str}_{vs_currency}"

        def _fetch():
            url = f"{self.base_url}/simple/price"
            params = {
                'ids': ids_str,
                'vs_currencies': vs_currency,
                'include_24hr_change': 'true',
                'include_last_updated_at': 'true'
            }
            resp = self.session.get(url, params=params, timeout=self.request_timeout)
            resp.raise_for_status()
            raw_data = resp.json()

            results = {}
            for coin_id in ids_str.split(','):
                coin_data = raw_data.get(coin_id, {})
                last_updated = coin_data.get('last_updated_at')
                formatted_time = (
                    datetime.fromtimestamp(last_updated, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                    if last_updated else datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                )
                results[coin_id] = {
                    'coin': coin_id.capitalize(),
                    'price': coin_data.get(vs_currency),
                    'currency': vs_currency.upper(),
                    'change_24h': round(coin_data.get(f'{vs_currency}_24h_change', 0.0), 2),
                    'timestamp': formatted_time
                }
            return results

        return self._get_cached_or_fetch(cache_key, _fetch)

    def get_coin_metadata(self, coin_id='bitcoin'):
        cache_key = f"coin_meta_{coin_id}"

        def _fetch():
            url = f"{self.base_url}/coins/{coin_id}"
            params = {
                'localization': 'false',
                'tickers': 'false',
                'community_data': 'false',
                'developer_data': 'false'
            }
            resp = self.session.get(url, params=params, timeout=self.request_timeout)
            resp.raise_for_status()
            data = resp.json()
            market_data = data.get('market_data', {})

            return {
                'id': data.get('id'),
                'name': data.get('name'),
                'symbol': data.get('symbol', '').upper(),
                'market_cap_usd': market_data.get('market_cap', {}).get('usd'),
                'current_price_usd': market_data.get('current_price', {}).get('usd'),
                'total_supply': market_data.get('total_supply'),
                'circulating_supply': market_data.get('circulating_supply'),
                'high_24h_usd': market_data.get('high_24h', {}).get('usd'),
                'low_24h_usd': market_data.get('low_24h', {}).get('usd')
            }

        return self._get_cached_or_fetch(cache_key, _fetch)

    def get_market_chart(self, coin_id='bitcoin', vs_currency='usd', days=1):
        cache_key = f"chart_{coin_id}_{vs_currency}_{days}"

        def _fetch():
            url = f"{self.base_url}/coins/{coin_id}/market_chart"
            params = {'vs_currency': vs_currency, 'days': days}
            resp = self.session.get(url, params=params, timeout=self.request_timeout)
            resp.raise_for_status()
            raw_chart = resp.json()

            prices = [
                {
                    'timestamp': datetime.fromtimestamp(item[0] / 1000.0, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'),
                    'price': item[1]
                }
                for item in raw_chart.get('prices', [])
            ]
            return {
                'coin': coin_id.capitalize(),
                'currency': vs_currency.upper(),
                'days': days,
                'prices': prices
            }

        return self._get_cached_or_fetch(cache_key, _fetch)
