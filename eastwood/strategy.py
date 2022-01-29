# Strategies
## Standard library imports
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
from datetime import datetime
from time import sleep

## Third party library import
import pandas as pd

## Package relative imports
from .account import AlpacaAccount
from .pairs import CointegratedPair

__all__ = [
    'PairsTrader',
    ]

class TradingStrategy(ABC):
    """"""
    def __init__(self):
        raise NotImplementedError

    @abstractmethod
    def open_position(self):
        raise NotImplementedError

    @abstractmethod
    def close_position(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def acct(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def trade_time(self):
        raise NotImplementedError

    @abstractmethod
    def set_trade_time(self):
        raise NotImplementedError

    @abstractmethod
    def run(self):
        raise NotImplementedError


class PairsTrader(TradingStrategy):
    """"""
    def __init__(self, acct: "TradingAccount", pairs: List[Tuple[str, str]],
            trade_time: "datetime.time", tolerance: float = .25, **kwargs):
        self.__acct = acct
        self.__pairs = tuple()
        self.__trade_time = trade_time
        self.__tolerance = tolerance
        self.__params = kwargs
        self.__has_traded = False
        self.__open_positions = self.check_pairs()

        for pair in pairs:
            self.__pairs = self.__pairs + (CointegratedPair(*pair, **kwargs),)
        # print("Pairs models trained!")

        print("Ready to trade!")

    @property
    def acct(self):
        return self.__acct

    @property
    def pairs(self):
        return self.__pairs

    def add_pair(self, ticker1, ticker2):
        self.__pairs = self.__pairs + (CointegratedPair(ticker1, ticker2, **self.params),)

    def remove_pair(self, ticker1, ticker2):
        pair = (ticker1, ticker2)
        pairs = [coint for coint in self.pairs if set(coint.tickers) != set(pair)]
        self.__pairs = pairs
        
    def is_open(self, pair):
        positions = self.acct.get_positions()
        return positions.get(pair[0],0) != 0 or positions.get(pair[1],0) != 0
    
    @property
    def trade_time(self):
        return self.__trade_time

    def set_trade_time(self, t: "datetime.time"):
        self.__trade_time = t

    @property
    def tolerance(self):
        return self.__tolerance

    @property
    def params(self):
        return self.__params
        
        
    def check_pairs(self) -> int:
        count = 0
        for pair in self.pairs:
            if self.is_open(pair.tickers):
                count += 1
        return count
        
    def decide_quantities(self, ticker1, ticker2) -> dict:
        price1 = self.acct.get_price(ticker1)
        price2 = self.acct.get_price(ticker2)
        portion = self.acct.get_buying_power() / (len(self.pairs) - self.__open_positions)
        qty1 = (portion / 2) // price1
        qty2 = (portion / 2) // price2
        return {ticker1: qty1, ticker2: qty2}

    def open_position(self, ticker1: str, ticker2: str, qty1: int, qty2: int):
        """Opens a pairs position by buying ticker1 and shorting ticker2"""
        self.acct.buy(ticker1, qty1)
        self.acct.short(ticker2, qty2)
        self.__open_positions += 1

    def close_all_positions(self):
        """Closes all positions on the account"""
        self.acct.close_all_positions()

    def close_position(self, ticker1: str, ticker2: str):
        """Closes a single pairs position"""
        self.acct.api.close_position(ticker1)
        self.acct.api.close_position(ticker2)
        self.__open_positions -= 1

    def run(self):
        try:
            while True:
                t = datetime.now().time()
                lets_trade = (t >= self.trade_time
                    and not self.__has_traded 
                    and self.acct.is_market_open())
                if lets_trade:
                    print(f"Let's trade! {datetime.now()}")
                    # Am I allowed to buy pr sell?
                    for pair in self.pairs:
                        
                        ticker1 = pair.tickers[0]
                        ticker2 = pair.tickers[1]
                        p1 = self.acct.get_price(ticker1)
                        p2 = self.acct.get_price(ticker2)
                        deviance = pair.find_deviance(pd.Series([p1, p2], index=[ticker1, ticker2]))
                        
                        if self.is_open(pair.tickers):
                            direction = 'up' if self.acct.get_position(pair.tickers[0]) < 0 else 'down'
                            # print(direction, deviance)
                            if (direction == 'up') and (deviance <= 0):
                                print(f"Closing up position! {pair.tickers}, {deviance}")
                                self.close_position(*pair.tickers)
                            if (direction == 'down') and (deviance >= 0):
                                print(f"Closing down position! {pair.tickers}, {deviance}")
                                self.close_position(*pair.tickers)
                            
                            
                        if deviance > self.tolerance and not self.is_open(pair.tickers): # Up position
                            print(f"Opening up position! {pair.tickers}, {deviance}")
                            qtys = self.decide_quantities(ticker1, ticker2)
                            qty1 = qtys[ticker1]
                            qty2 = qtys[ticker2]
                            self.open_position(ticker2, ticker1, qty2, qty1)
                            
                        if deviance < -self.tolerance and not self.is_open(pair.tickers): # Down position
                            print(f"Opening down position! {pair.tickers}, {deviance}")
                            qtys = self.decide_quantities(ticker1, ticker2)
                            qty1 = qtys[ticker1]
                            qty2 = qtys[ticker2]
                            self.open_position(ticker1, ticker2, qty1, qty2)
                            
                    print("That was fun!")
                    self.__has_traded = True
                    # self.check_pairs()
                    # for pair in self.check_pairs():
                    #     portion = self.acct.get_buying_power() / len(self.pairs)
                    #     something something
                elif t >= self.trade_time and not self.__has_traded:
                    self.__has_traded = True
                    print(f"Looks like the market is closed today! {datetime.now()}")
                elif t >= self.trade_time:
                    print(f"I guess I've already traded today. {datetime.now()}")
                elif t < self.trade_time:
                    self.__has_traded = False
                    print(f"I don't think it's time to trade yet, but now I'm ready to.  {datetime.now()}")
                else:
                    print(f"I don't know what's happening. {datetime.now()}")
                sleep(3600)
                    
        except KeyboardInterrupt:
    	    self.close_all_positions()
    	    print("All positions closed!")
                # There will be a chance here to set the trade time
                # and add or remove pairs

    def __str__(self):
        return "PairsTrader({}, pairs: {})".format(type(self.acct), self.pairs)

    def __repr__(self):
        return "PairsTrader"

