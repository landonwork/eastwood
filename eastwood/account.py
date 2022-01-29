# Accounts
from abc import ABC, abstractmethod

# Standard library imports

# Third party library imports
import alpaca_trade_api as alpaca

# Package relative imports



__all__ = [
    'AlpacaAccount'
    ]

class TradingAccount(ABC):

    def __init__(self):
        raise(NotImplementedError)

    @abstractmethod
    def get_cash_balance(self):
        raise(NotImplementedError)

    @abstractmethod
    def get_buying_power(self):
        raise(NotImplementedError)

    @abstractmethod
    def get_account_value(self):
        raise(NotImplementedError)
 
    @abstractmethod
    def get_positions(self):
        raise(NotImplementedError)

    @abstractmethod
    def get_position(self, ticker):
        raise(NotImplementedError)

    @abstractmethod
    def get_price(self, ticker):
        raise(NotImplementedError)

    @abstractmethod
    def buy(self, ticker: str, qty: int):
        raise(NotImplementedError)

    @abstractmethod
    def sell(self, ticker: str, qty: int):
        raise(NotImplementedError)

    @abstractmethod
    def short(self, ticker: str, qty: int):
        raise(NotImplementedError)

    @abstractmethod
    def buy_to_cover(self, ticker: str, qty: int):
        raise(NotImplementedError)
    
    @abstractmethod
    def is_market_open(self, ticker: str, qty: int):
        raise(NotImplementedError)


class AlpacaAccount(TradingAccount):
    
    def __init__(self, url: str, key_id: str, key: str):
        self.__url = url
        self.__key_id = key_id
        self.__key = key
        self.__api = alpaca.REST(self.__key_id, self.__key, self.__url)

    @property
    def url(self):
        return self.__url

    @property
    def key(self):
        return self.__key

    @property
    def key_id(self):
        return self.__key_id

    @property
    def api(self):
        return self.__api

    def get_cash_balance(self):
        return float(self.api.get_account().cash)

    def get_buying_power(self):
        return float(self.api.get_account().buying_power)

    def get_account_value(self):
        return float(self.api.get_account().equity)

    def get_positions(self):
        return {x.symbol: int(x.qty) for x in self.api.list_positions()}
    
    def get_position(self, ticker):
        positions = self.get_positions()
        return int(positions.get(ticker, 0))

    def close_all_positions(self):
        self.api.close_all_positions()

    def get_price(self, ticker):
        price = self.api.get_latest_trade(ticker).p
        return float(price)

    def buy(self, ticker: str, qty: int):
        self.api.submit_order(
            symbol = ticker,
            qty = qty,
            side = 'buy',
            type = 'market',
            time_in_force = 'day'
        )

    def sell(self, ticker: str, qty: int):
        self.api.submit_order(
            symbol = ticker,
            qty = qty,
            side = 'sell',
            type = 'market',
            time_in_force = 'day'
        )
        
    def short(self, ticker: str, qty: int):
        self.sell(ticker, qty)

    def buy_to_cover(self, ticker: str, qty: int):
        self.buy(ticker, qty)

    def is_market_open(self):
        return self.api.get_clock().is_open
