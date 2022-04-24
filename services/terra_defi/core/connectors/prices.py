# -*- coding: utf-8 -*-
"""
Created on 2022/04/12
@author: schengatto@gmail.com
"""
import pytz
import yfinance as yf
import pandas as pd

from datetime import datetime
from dateutil.relativedelta import relativedelta
from core.connectors import binance_connector as bc
from pycoingecko import CoinGeckoAPI


# Valid periods: dly,1d,3d,5d,1w,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
# + hours 1 is needed to capture also the interval of the current hour.
def get_starting_date(period='max'):
    if period in ["1h", "dly"]:
        yesterday = datetime.utcnow() - relativedelta(days=1, hours=1)
        datetime_value = yesterday.replace(hour=23, minute=59, second=59, microsecond=0)
    elif period == "1d":
        datetime_value = datetime.utcnow() - relativedelta(days=1, hours=1)
    elif period == "3d":
        datetime_value = datetime.utcnow() - relativedelta(days=3, hours=1)
    elif period == "5d":
        datetime_value = datetime.utcnow() - relativedelta(days=5, hours=1)
    elif period == "1w":
        datetime_value = datetime.utcnow() - relativedelta(days=7, hours=1)
    elif period == "1mo":
        datetime_value = datetime.utcnow() - relativedelta(months=1, hours=1)
    elif period == "3mo":
        datetime_value = datetime.utcnow() - relativedelta(months=3, hours=1)
    elif period == "6mo":
        datetime_value = datetime.utcnow() - relativedelta(months=6, hours=1)
    elif period == "1y":
        datetime_value = datetime.utcnow() - relativedelta(years=1, hours=1)
    elif period == "2y":
        datetime_value = datetime.utcnow() - relativedelta(years=2, hours=1)
    elif period == "5y":
        datetime_value = datetime.utcnow() - relativedelta(years=5, hours=1)
    elif period == "10y":
        datetime_value = datetime.utcnow() - relativedelta(years=10, hours=1)
    elif period == "ytd":
        datetime_value = datetime.utcnow().date().replace(month=1, day=1)
    else:  # includes "max"
        datetime_value = datetime.utcnow().date().replace(month=1, day=1, year=2000)

    return datetime_value


# Valid intervals: ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d"]
# + hours 1 is needed to capture also the interval of the current hour.
def get_ending_date(interval="1d"):
    if interval in ["1m", "3m", "5m", "30m"]:
        interval_min = int(interval[0:-1])
        last_valid_min = interval_min * int(datetime.utcnow().minute / interval_min)
        datetime_value = datetime.utcnow().replace(minute=last_valid_min, second=0, microsecond=0)
    elif interval in ["1h", "2h", "4h", "6h", "8h", "12h"]:
        interval_hour = int(interval[0:-1])
        last_valid_hour = interval_hour * int(datetime.utcnow().hour / interval_hour)
        datetime_value = datetime.utcnow().replace(hour=last_valid_hour, minute=0, second=0, microsecond=0)
    else:  # 1d
        dt = datetime.utcnow() - relativedelta(hours=1)
        datetime_value = dt.replace(hour=0, minute=0, second=0, microsecond=0)

    return datetime_value


def available_symbols(provider):
    if provider in ["binance_spot", "binance_spot_test"]:
        client = bc.BinanceClient(None, None, False)
        return client.get_all_tickers()


def has_symbol_prices(symbol, provider):
    if provider in ["binance_spot", "binance_spot_test"]:
        try:
            prices = get_binance_spot_prices(symbol,
                                             interval="1h",
                                             period="dly",
                                             testnet=provider == "binance_spot_test")
            return len(prices) > 0
        except:
            return False
    elif provider in ["binance_futures", "binance_futures_test"]:
        try:
            prices = get_binance_futures_prices(symbol,
                                                interval="1h",
                                                period="dly",
                                                testnet=provider == "binance_futures_test")
            return len(prices) > 0
        except:
            return False
    else:
        raise Exception(f"Invalid provider: {provider}")


def get_binance_spot_prices(symbol, interval="1d", start_date=None, end_date=None, period=None, testnet=False):
    if start_date is None:
        start_date = get_starting_date(period)

    if end_date is None:
        end_date = get_ending_date(interval)

    client = bc.BinanceClient(None, None, testnet)
    history_prices = pd.DataFrame()
    last_index = start_date

    while last_index is None or (int(last_index.timestamp()) < (int(end_date.timestamp() - 1))):
        start_str = f"{round(last_index.timestamp() * 1000, 0)}"
        end_str = f"{round(end_date.timestamp() * 1000, 0)}"
        portion = client.get_symbol_historical_data(symbol=symbol,
                                                    interval=interval,
                                                    start_str=start_str,
                                                    end_str=end_str)
        history_prices = pd.concat([history_prices, portion])
        if len(history_prices) == 0 or last_index == history_prices.index[-1]:
            raise Exception(
                f"No prices found for {symbol} in the timeframe {last_index} - {end_date}")

        print(f"Downloading prices from {last_index} to {history_prices.index[-1]}")
        last_index = history_prices.index[-1];

    client.close_connection()

    if period == "1h":
        utc = pytz.UTC
        target = datetime.utcnow() - relativedelta(hours=1, minutes=1)
        print(f"{history_prices.index[-1].to_pydatetime().timestamp()}")
        print(f"{target.timestamp()}")
        history_prices = history_prices[history_prices.index.to_pydatetime() >= utc.localize(target)]

    return history_prices


def get_binance_futures_prices(symbol, interval, start_date=None, end_date=None, period=None, testnet=False):
    if start_date is None:
        start_date = get_starting_date(period)

    if end_date is None:
        end_date = datetime.utcnow()

    client = bc.BinanceClient(None, None, testnet)
    history_prices = pd.DataFrame()
    last_index = start_date

    while last_index is None or last_index.date() < end_date:
        start_str = f"{round(last_index.timestamp() * 1000, 0)}"
        end_str = f"{round(end_date * 1000, 0)}"
        portion = client.futures_historical_symbol_prices(symbol=symbol,
                                                          interval=interval,
                                                          start_str=start_str,
                                                          end_str=end_str)
        history_prices = pd.concat([history_prices, portion])
        if len(history_prices) == 0 or last_index == history_prices.index[-1]:
            raise Exception(
                f"No prices found for {symbol} in the timeframe {last_index.date()} - {end_date}")

        print(f"Downloading prices from {last_index} to {history_prices.index[-1]}")
        last_index = history_prices.index[-1];

    client.close_connection()

    if period == "1h":
        utc = pytz.UTC
        target = datetime.utcnow() - relativedelta(hours=1, minutes=1)
        print(f"{history_prices.index[-1].to_pydatetime().timestamp()}")
        print(f"{target.timestamp()}")
        history_prices = history_prices[history_prices.index.to_pydatetime() >= utc.localize(target)]

    return history_prices


def get_coingecko_prices(symbol, period="1d"):
    allowed_periods = ["1d", "3d", "5d", "1w", "1mo", "3mo", "1y"]
    if period not in allowed_periods:
        raise Exception(f"Provide a period. Valid periods: {', '.join(allowed_periods)}")

    days = 1
    if period == "3d":
        days = 3
    elif period == "5d":
        days = 5
    elif period == "1w":
        days = 7
    elif period == "1mo":
        days = 30
    elif period == "3mo":
        days = 90
    elif period == "1y":
        days = 365

    # https://www.coingecko.com/en/api/documentation
    cg = CoinGeckoAPI()
    prices = cg.get_coin_ohlc_by_id(symbol, "usd", days)
    df = pd.DataFrame(prices, columns=['Date', 'Open', 'High', 'Low', "Close"])
    df['date'] = df['Date'].apply(lambda x: datetime.fromtimestamp(x / 1e3))
    df.set_index('date', inplace=True)
    return df


# returns the historical prices in dataframe format with columns 'date', 'Open', 'High', 'Low', 'Close', 'Volume'.
def get_symbol_prices(symbol, period=None, interval=None, provider='binance_spot', start_date=None, end_date=None):
    allowed_periods = ["1h", "dly", "1d", "3d", "5d", "1w", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
    allowed_intervals = ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d"]
    if (start_date is None or end_date is None) and period not in allowed_periods:
        raise Exception(f"Provide a period. Valid periods: {', '.join(allowed_periods)}")

    if interval not in allowed_intervals:
        raise Exception(f"Provide an interval. Valid intervals: {', '.join(allowed_intervals)}")

    if provider == "yahoo":
        return yf.download(tickers=symbol, period=period, interval=interval, start_date=start_date, end_date=end_date)
    elif provider in ["binance_spot", "binance_spot_test"]:
        return get_binance_spot_prices(symbol,
                                       interval=interval,
                                       period=period,
                                       testnet=provider == "binance_spot_test",
                                       start_date=start_date,
                                       end_date=end_date)
    elif provider in ["binance_futures", "binance_futures_test"]:
        return get_binance_futures_prices(symbol,
                                          interval=interval,
                                          period=period,
                                          testnet=provider == "binance_futures_test",
                                          start_date=start_date,
                                          end_date=end_date)
    elif provider in ["coingecko"]:
        return get_coingecko_prices(symbol, period=period)
    else:
        raise Exception(f"Invalid provider: {provider}")


def get_current_bid_ask(symbol, provider="binance_spot"):
    if provider in ["binance_spot", "binance_spot_test"]:
        client = bc.BinanceClient(None, None, provider == "binance_spot_test")
        return client.get_latest_price_info_by_symbol(symbol)
    elif provider in ["binance_futures", "binance_futures_test"]:
        client = bc.BinanceClient(None, None, provider == "binance_futures_test")
        return client.futures_get_latest_price_info_by_symbol(symbol)
    else:
        raise Exception(f"Invalid provider: {provider}")

# TEST


# s_date = "2021-01-03 00:00:00"
# e_date = "2021-03-31 23:59:59"
# print(get_symbol_prices("BTCUSDT",
#                        interval="1m",
#                        period="5d",
#                        provider="binance_spot"))
# print(has_symbol_prices("PAXUSDT", provider="binance_spot"))
# print(get_current_bid_ask("BTCUSDT"))

