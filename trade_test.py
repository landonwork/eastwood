# Standard library imports
import threading
from datetime import datetime

# Third party library imports
import yaml
from yaml import CLoader
import requests
import pandas_datareader as web
import alpaca_trade_api as alpaca
import yfinance as yf

keys = yaml.load(open('paper_key.yml','r'), Loader=CLoader)

api = alpaca.REST(
    keys['API Key ID'],
    keys['Secret Key'],
    keys['Endpoint']
    )

# How to get account information
account = api.get_account()
# print(account._raw)
# print(account.equity, account.last_equity)

# How to get a list of tradable, shortable stocks
active_assets = api.list_assets(status='active')
stocks =  [a for a in active_assets if a.exchange in ('NASDAQ','NYSE') and a.tradable and a.shortable]
# print(stocks[0]._raw)
# print(len(stocks))
# print([stock.symbol for stock in stocks])

# How to submit an order
# api.submit_order(
#     symbol = 'WEN',
#     qty = 1,
#     side = 'buy',
#     type = 'market',
#     time_in_force = 'day'
# )

# How to check a position
def get_position(ticker):
    try:
        position = api.get_position(ticker)
        print(f'You have {position.qty} shares of {ticker}')
        return position.qty
    except alpaca.rest.APIError as e:
        reason = eval(e.response.content.decode())['message']
        if reason == 'position does not exist':
            print(0)
            return 0
        else:
            raise e
        
get_position('F')


# How to get the current price of a stock
# We're working on it
def get_current_price(symbol):
    ticker = yf.Ticker(symbol)
    todays_data = ticker.history(period='1d')
    return todays_data['Close'][0]
print(f"The current price of AAPL is {get_current_price('AAPL')}")
