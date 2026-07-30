"""Tests for input validation and centralized error handling."""
from unittest.mock import patch

from app.errors import NotFoundError, UpstreamServiceError


# --------------------------------------------------------------------- #
# Input validation -> 400
# --------------------------------------------------------------------- #
def test_history_invalid_days_returns_400(client):
    response = client.get('/api/v1/coins/bitcoin/history?days=abc')
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['status'] == 'error'
    assert "days" in json_data['message']


def test_history_days_out_of_range_returns_400(client):
    response = client.get('/api/v1/coins/bitcoin/history?days=9999')
    assert response.status_code == 400
    assert 'between 1 and 365' in response.get_json()['message']


def test_prices_unsupported_vs_currency_returns_400(client):
    response = client.get('/api/v1/prices?vs_currency=dogecoin')
    assert response.status_code == 400
    assert 'vs_currency' in response.get_json()['message']


def test_prices_empty_coins_returns_400(client):
    response = client.get('/api/v1/prices?coins=,,')
    assert response.status_code == 400
    assert 'coins' in response.get_json()['message']


def test_prices_too_many_coins_returns_400(client):
    coins = ','.join(f'coin{i}' for i in range(11))
    response = client.get(f'/api/v1/prices?coins={coins}')
    assert response.status_code == 400
    assert 'Too many coins' in response.get_json()['message']


def test_invalid_coin_id_returns_400(client):
    response = client.get('/api/v1/coins/BTC$$$')
    assert response.status_code == 400
    assert 'coin id' in response.get_json()['message'].lower()


# --------------------------------------------------------------------- #
# Centralized error handlers
# --------------------------------------------------------------------- #
@patch('app.services.coingecko.CoinGeckoService.get_simple_price')
def test_unexpected_error_does_not_leak_details(mock_get_price, client):
    mock_get_price.side_effect = RuntimeError('secret internal detail: db password')

    response = client.get('/api/v1/prices')
    assert response.status_code == 500
    json_data = response.get_json()
    assert json_data == {'status': 'error', 'message': 'Internal server error'}
    assert 'secret' not in str(json_data)


@patch('app.services.coingecko.CoinGeckoService.get_coin_metadata')
def test_upstream_error_returns_502(mock_get_meta, client):
    mock_get_meta.side_effect = UpstreamServiceError()

    response = client.get('/api/v1/coins/bitcoin')
    assert response.status_code == 502
    assert response.get_json()['status'] == 'error'


@patch('app.services.coingecko.CoinGeckoService.get_coin_metadata')
def test_unknown_coin_returns_404(mock_get_meta, client):
    mock_get_meta.side_effect = NotFoundError("Coin 'unknowncoin' not found")

    response = client.get('/api/v1/coins/unknowncoin')
    assert response.status_code == 404
    assert 'not found' in response.get_json()['message']


def test_unknown_route_returns_json_404(client):
    response = client.get('/no/such/route')
    assert response.status_code == 404
    assert response.get_json()['status'] == 'error'


def test_wrong_method_returns_json_405(client):
    response = client.post('/health')
    assert response.status_code == 405
    assert response.get_json()['status'] == 'error'
