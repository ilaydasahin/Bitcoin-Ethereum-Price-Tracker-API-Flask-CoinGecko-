from flask import Flask, jsonify
from pycoingecko import CoinGeckoAPI
import datetime
import pandas as pd

app = Flask(__name__)
cg = CoinGeckoAPI()

# Bitcoin fiyatı endpoint
@app.route('/bitcoin', methods=['GET'])
def get_bitcoin_price():
    bitcoin_data = cg.get_coin_market_chart_by_id(id='bitcoin', vs_currency='usd', days=1)
    bitcoin_price_data = bitcoin_data['prices']
    bitcoin_df = pd.DataFrame(bitcoin_price_data, columns=['TimeStamp', 'Price'])
    bitcoin_df['date'] = bitcoin_df['TimeStamp'].apply(lambda d: datetime.datetime.utcfromtimestamp(d / 1000.0).strftime('%Y-%m-%d %H:%M:%S'))
    latest_price = bitcoin_df.iloc[-1]

    return jsonify({
        'coin': 'Bitcoin',
        'price': latest_price['Price'],
        'timestamp': latest_price['date']
    })

# Ethereum fiyatı endpoint
@app.route('/ethereum', methods=['GET'])
def get_ethereum_price():
    ethereum_data = cg.get_coin_market_chart_by_id(id='ethereum', vs_currency='eur', days=1)
    ethereum_price_data = ethereum_data['prices']
    ethereum_df = pd.DataFrame(ethereum_price_data, columns=['TimeStamp', 'Price'])
    ethereum_df['date'] = ethereum_df['TimeStamp'].apply(lambda d: datetime.datetime.utcfromtimestamp(d / 1000.0).strftime('%Y-%m-%d %H:%M:%S'))
    latest_price = ethereum_df.iloc[-1]

    return jsonify({
        'coin': 'Ethereum',
        'price': latest_price['Price'],
        'timestamp': latest_price['date']
    })

# Bitcoin info endpoint
@app.route('/bitcoin/info', methods=['GET'])
def bitcoin_info():
    coin_info = cg.get_coin_by_id('bitcoin')
    return jsonify({
        "name": coin_info['name'],
        "symbol": coin_info['symbol'],
        "market_cap": coin_info['market_data']['market_cap']['usd'],
        "total_supply": coin_info['market_data']['total_supply'],
        "circulating_supply": coin_info['market_data']['circulating_supply']
    })

if __name__ == '__main__':
    app.run(debug=True)
