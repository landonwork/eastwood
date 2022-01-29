# Pairs tools

# Standard library imports
from itertools import permutations
from datetime import datetime, timedelta
from typing import Union

# Third party library imports
import pandas_datareader as web
import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import adfuller
import statsmodels.api as sm

__all__ = [
    'get_historical_prices',
    'are_cointegrated',
    'CointegratedPair'
    ]

# Package relative imports

def get_historical_prices(tickers, logs=False,  **kwargs):
    df = web.DataReader(tickers, 'stooq', **kwargs)
    levels = df['Close']
    if logs:
        levels = np.log(levels)
    return levels

def are_cointegrated(ticker1: str, ticker2: str, data: pd.DataFrame = None,
        verbose = False, **kwargs) -> float:
    """
    Takes two ticker symbols and tests the residuals of the linear model for stationarity.
    Function returns a p-value. The smaller the p-value, the more likely the two stocks are cointegrated.
    kwargs are for the get_historical_prices function and include logs=False, start, and end
    
    Most likely you will need to provide a `start` parameter that is a datetime object
    If you do not and then receive this error:
        MissingDataError: exog contains inf or nans
    Then you will need to limit your request to a shorter period of time
    """
    tickers = [ticker1, ticker2]
    if data is None:
        levels = get_historical_prices(tickers, **kwargs)
    else:
        levels = data[[ticker1, ticker2]]

    lin_model = sm.OLS(levels[ticker1], levels[ticker2])
    lin_model = lin_model.fit()
    res = adfuller(lin_model.resid)

    if verbose:
        print(f"\n{ticker1} & {ticker2}\n================")
        print(f"P-value: {res[1]: .4f}")
        logs = kwargs.get('logs',False)
        print(f"Logs: {logs}")

    return res[1]


class CointegratedPair:
    """
    This class represents the cointegrated relationship of two stocks

    """
    def __init__(self, ticker1: str, ticker2: str, **kwargs):

        self.tickers = [ticker1, ticker2]
        levels = get_historical_prices(self.tickers, **kwargs)
        best_p = 1.

        # We have to select the parameters for our linear model (target, feature, logs) that make the
        # p-value on the resid coefficient the most significant
        for logs in [False, True]:

            if logs:
                levels = np.log(levels)

            diffs = levels.diff(-1).dropna()

            for p in permutations(self.tickers,2):
                lin_model = sm.OLS(levels[p[0]],levels[p[1]])
                lin_model = lin_model.fit()
                resid = lin_model.resid.iloc[:-1]

                df = pd.DataFrame({
                    p[0]: diffs[p[0]],
                    p[1]: diffs[p[1]],
                    'resid': resid,
                    p[0]+'_lead': diffs[p[0]].shift()
                }).dropna()

                # Error correction model
                error_model = sm.OLS(df[p[0]+'_lead'],df.drop(columns=p[0]+'_lead'))
                error_model = error_model.fit()

                # print(error_model.summary())
                # print(error_model.pvalues[2])

                if error_model.pvalues[2] < best_p:
                    self.model = lin_model
                    self.tickers = p
                    self.logs = logs
                    best_p = error_model.pvalues[2]

        self.resid_pvalue = best_p
        self.stddev = np.std(self.model.resid)

    # Private method because the only place where np.log happens is in self.find_deviance
    def __predict(self, x: float) -> float:
        return self.model.predict(x)[0]

    def find_deviance(self, prices: 'pd.Series') -> float:

        assert isinstance(prices, pd.Series), "CointegratedPair.find_deviance requires a pd.Series object"

        if self.logs:
            prices = np.log(prices)

        y = prices[self.tickers[0]]
        y_hat = self.__predict(prices[self.tickers[1]])
        return (y - y_hat) / self.stddev

    def __str__(self):
        return "CointegratedPair"+str((*self.tickers, self.logs))

    def __repr__(self):
        return self.__str__()

if __name__ == '__main__':
    prices = get_historical_prices(['WEN','MCD'])
    print(prices.head())
    print(are_cointegrated('WEN', 'MCD', prices))
    print(CointegratedPair('WEN', 'MCD'))
