from flask import Blueprint, jsonify, request, current_app
from app.services.coingecko import CoinGeckoService

api_bp = Blueprint('api', __name__)
cg_service = None

def get_service():
    global cg_service
    if cg_service is None:
        cg_service = CoinGeckoService(
            base_url=current_app.config['COINGECKO_BASE_URL'],
            cache_timeout=current_app.config['CACHE_DEFAULT_TIMEOUT'],
            request_timeout=current_app.config['REQUEST_TIMEOUT']
        )
    return cg_service

@api_bp.route('/', methods=['GET'])
def index():
    return jsonify({
        'status': 'online',
        'service': 'Crypto Price Tracker API',
        'version': '1.0.0',
        'message': 'Welcome to Crypto Price Tracker REST API',
        'endpoints': {
            'health': '/health',
            'prices': '/api/v1/prices?coins=bitcoin,ethereum&vs_currency=usd',
            'coin_metadata': '/api/v1/coins/bitcoin',
            'coin_history': '/api/v1/coins/bitcoin/history?days=7',
            'legacy_bitcoin': '/bitcoin',
            'legacy_ethereum': '/ethereum'
        },
        'documentation': 'https://github.com/ilaydasahin/Bitcoin-Ethereum-Price-Tracker-API-Flask-CoinGecko-'
    }), 200

@api_bp.route('/favicon.ico', methods=['GET'])
def favicon():
    return '', 204

@api_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'Crypto Price Tracker API',
        'version': '1.0.0'
    }), 200

@api_bp.route('/api/v1/prices', methods=['GET'])
def get_prices():
    coins_param = request.args.get('coins', 'bitcoin,ethereum')
    vs_currency = request.args.get('vs_currency', 'usd').lower()
    coin_list = [c.strip().lower() for c in coins_param.split(',') if c.strip()]
    
    try:
        service = get_service()
        data = service.get_simple_price(coin_ids=coin_list, vs_currency=vs_currency)
        return jsonify({'status': 'success', 'data': data}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api_bp.route('/api/v1/coins/<string:coin_id>', methods=['GET'])
def get_coin_info(coin_id):
    try:
        service = get_service()
        data = service.get_coin_metadata(coin_id.lower())
        return jsonify({'status': 'success', 'data': data}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api_bp.route('/api/v1/coins/<string:coin_id>/history', methods=['GET'])
def get_coin_history(coin_id):
    vs_currency = request.args.get('vs_currency', 'usd').lower()
    days = request.args.get('days', 1, type=int)
    try:
        service = get_service()
        data = service.get_market_chart(coin_id.lower(), vs_currency=vs_currency, days=days)
        return jsonify({'status': 'success', 'data': data}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Legacy Backward Compatibility Endpoints
@api_bp.route('/bitcoin', methods=['GET'])
def legacy_bitcoin_price():
    try:
        service = get_service()
        data = service.get_simple_price(coin_ids=['bitcoin'], vs_currency='usd')
        btc_info = data.get('bitcoin', {})
        return jsonify({
            'coin': 'Bitcoin',
            'price': btc_info.get('price'),
            'timestamp': btc_info.get('timestamp')
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/ethereum', methods=['GET'])
def legacy_ethereum_price():
    try:
        service = get_service()
        data = service.get_simple_price(coin_ids=['ethereum'], vs_currency='eur')
        eth_info = data.get('ethereum', {})
        return jsonify({
            'coin': 'Ethereum',
            'price': eth_info.get('price'),
            'timestamp': eth_info.get('timestamp')
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/bitcoin/info', methods=['GET'])
def legacy_bitcoin_info():
    try:
        service = get_service()
        info = service.get_coin_metadata('bitcoin')
        return jsonify({
            'name': info.get('name'),
            'symbol': info.get('symbol'),
            'market_cap': info.get('market_cap_usd'),
            'total_supply': info.get('total_supply'),
            'circulating_supply': info.get('circulating_supply')
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
