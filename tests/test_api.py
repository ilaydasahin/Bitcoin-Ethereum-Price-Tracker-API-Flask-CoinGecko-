from unittest.mock import patch

def test_root_index(client):
    response = client.get('/')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'online'
    assert json_data['service'] == 'Crypto Price Tracker API'
    assert 'endpoints' in json_data

def test_health_check(client):
    response = client.get('/health')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'healthy'
    assert json_data['service'] == 'Crypto Price Tracker API'

@patch('app.services.coingecko.CoinGeckoService.get_simple_price')
def test_get_prices(mock_get_price, client):
    mock_get_price.return_value = {
        'bitcoin': {
            'coin': 'Bitcoin',
            'price': 65000.0,
            'currency': 'USD',
            'change_24h': 2.5,
            'timestamp': '2026-07-30 02:40:00 UTC'
        },
        'ethereum': {
            'coin': 'Ethereum',
            'price': 3500.0,
            'currency': 'USD',
            'change_24h': 1.8,
            'timestamp': '2026-07-30 02:40:00 UTC'
        }
    }
    
    response = client.get('/api/v1/prices?coins=bitcoin,ethereum')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'success'
    assert 'bitcoin' in json_data['data']
    assert json_data['data']['bitcoin']['price'] == 65000.0

@patch('app.services.coingecko.CoinGeckoService.get_coin_metadata')
def test_get_coin_info(mock_get_meta, client):
    mock_get_meta.return_value = {
        'id': 'bitcoin',
        'name': 'Bitcoin',
        'symbol': 'BTC',
        'market_cap_usd': 1200000000000,
        'current_price_usd': 65000.0,
        'total_supply': 21000000,
        'circulating_supply': 19700000,
        'high_24h_usd': 66000.0,
        'low_24h_usd': 64000.0
    }
    
    response = client.get('/api/v1/coins/bitcoin')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'success'
    assert json_data['data']['symbol'] == 'BTC'

@patch('app.services.coingecko.CoinGeckoService.get_simple_price')
def test_legacy_bitcoin_price(mock_get_price, client):
    mock_get_price.return_value = {
        'bitcoin': {
            'coin': 'Bitcoin',
            'price': 65000.0,
            'timestamp': '2026-07-30 02:40:00 UTC'
        }
    }
    response = client.get('/bitcoin')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['coin'] == 'Bitcoin'
    assert json_data['price'] == 65000.0
