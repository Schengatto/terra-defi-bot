import logging
import pandas as pd

from datetime import datetime, timezone
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException, BinanceOrderException

logger = logging.getLogger()


# Read more at https://algotrading101.com/learn/binance-python-api-guide/
# python-binance_client lib doc: https://python-binance.readthedocs.io/en/latest/overview.html
# binance_client ita: https://academy.binance.com/it/articles/binance-api-series-pt-1-spot-trading-with-postman

class BinanceClient:
    def __init__(self, api_key, api_secret, testnet):
        self.isTestnet = testnet
        self.api_key = api_key
        self.api_secret = api_secret
        self.prices = dict()
        self._client = Client(api_key, api_secret, testnet=testnet)
        logger.info("Binance Client successfully initialized")

    # get balances for all assets & some account information
    def get_account_info(self):
        return self._client.get_account()

    # get balance for a specific asset only (eg: BTC)
    def get_asset_balance(self, asset):
        return self._client.get_asset_balance(asset=asset)

    # get balances for margin account
    def get_margin_account(self):
        return self._client.get_margin_account()

    # get latest price from Binance API (eg: BTCUSDT)
    def get_symbol_last_price(self, symbol):
        return float(self._client.get_symbol_ticker(symbol=symbol)["price"])

    # valid intervals - 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
    # get timestamp of earliest date data is available
    # format: csv, json
    def get_symbol_historical_data(self, symbol, interval, start_str=None, end_str=None, limit=1500,
                                   output="dataframe"):
        if start_str is None:
            klines_type: HistoricalKlinesType = HistoricalKlinesType.SPOT
            start_str = self._client._get_earliest_valid_timestamp(symbol, interval, klines_type)

        bars = self._client.get_historical_klines(symbol, interval, start_str, end_str, limit)

        # delete unwanted data - just keep date, open, high, low, close
        for line in bars:
            line[0] = datetime.fromtimestamp(line[0] / 1000.0, tz=timezone.utc)
            del line[6:]

        if output == "dataframe":
            data_frame = pd.DataFrame(bars, columns=['date', 'Open', 'High', 'Low', 'Close', 'Volume'])
            data_frame.set_index('date', inplace=True)
            return data_frame.apply(pd.to_numeric)
        else:
            return bars

    def get_account_trade_list(self, symbol):
        result = self._client.get_my_trades(symbol=symbol)
        return result

    def get_latest_price_info_by_symbol(self, symbol):
        result = self._client.get_orderbook_ticker(symbol=symbol);
        bid_price = result['bidPrice']
        bid_quantity = result['bidQty']
        ask_price = result['askPrice']
        ask_quantity = result['askQty']
        result = {
            "bid_price": float(bid_price),
            "bid_quantity": float(bid_quantity),
            "ask_price": float(ask_price),
            "ask_quantity": float(ask_quantity)
        }
        return result

    # create a real order
    def create_order(self, symbol, side, type, quantity, price):
        # create a real order if the test orders did not raise an exception
        result = None
        try:
            self._client.create_test_order(symbol=symbol, side=side, type=type, quantity=quantity)

            # timeInForce => https://www.investopedia.com/terms/t/timeinforce.asp
            result = self._client.create_order(
                symbol=symbol,
                side=side,
                type=type,
                timeInForce='GTC',
                quantity=quantity,
                price=price)

        except BinanceAPIException as e:
            # error handling goes here
            print(e)
        except BinanceOrderException as e:
            # error handling goes here
            print(e)

        return result

    # create a real order
    def spot_buy_at_current_price(self, symbol, quantity=None):
        # create a real order if the test orders did not raise an exception
        result = None
        try:
            self._client.create_test_order(symbol=symbol, side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=quantity)

            # timeInForce => https://www.investopedia.com/terms/t/timeinforce.asp
            result = self._client.create_order(
                symbol=symbol,
                side=SIDE_BUY,
                type=ORDER_TYPE_MARKET,
                quantity=quantity)

        except BinanceAPIException as e:
            # error handling goes here
            print(e)
            return e.message
        except BinanceOrderException as e:
            # error handling goes here
            print(e)
            return e.message

        return result

        # create a real order

    def spot_stop_loss_at_specific_price(self, symbol, stop_price, quantity):
        # create a real order if the test orders did not raise an exception
        result = None
        try:
            self._client.create_test_order(
                symbol=symbol,
                side=SIDE_BUY,
                type=ORDER_TYPE_STOP_LOSS,
                quantity=quantity,
                stopPrice=stop_price)

            # timeInForce => https://www.investopedia.com/terms/t/timeinforce.asp
            result = self._client.create_order(
                symbol=symbol,
                side=SIDE_BUY,
                type=ORDER_TYPE_STOP_LOSS,
                quantity=quantity,
                stopPrice=stop_price)

        except BinanceAPIException as e:
            # error handling goes here
            print(e)
            return e.message
        except BinanceOrderException as e:
            # error handling goes here
            print(e)
            return e.message

        return result

    # Send in a a buy order at the current price of the symbol
    def spot_sell_at_current_price(self, symbol, quantity):
        result = None
        try:
            self._client.create_test_order(
                symbol=symbol,
                side=SIDE_SELL,
                type=ORDER_TYPE_MARKET,
                quantity=quantity)

            result = self._client.create_order(
                symbol=symbol,
                side=SIDE_SELL,
                type=ORDER_TYPE_MARKET,
                quantity=quantity)

        except BinanceAPIException as e:
            # error handling goes here
            print(e)
            return e.message
        except BinanceOrderException as e:
            # error handling goes here
            print(e)
            return e.message

        return result

    # create a oco buy order
    def create_oco_buy_order(self, symbol, quantity, price, stop_price, stop_limit_price,
                             stop_limit_time_in_force="GTC"):
        # create a real order if the test orders did not raise an exception
        result = None
        try:
            result = self._client.order_oco_buy(
                symbol=symbol,
                quantity=quantity,
                price=price,
                stopPrice=stop_price,
                stopLimitPrice=stop_limit_price,
                stopLimitTimeInForce=stop_limit_time_in_force)

        except BinanceAPIException as e:
            # error handling goes here
            print(e)
        except BinanceOrderException as e:
            # error handling goes here
            print(e)

        return result

    # create a oco sell order
    def create_oco_sell_order(self, symbol, quantity, price, stop_price, stop_limit_price,
                              stop_limit_time_in_force="GTC"):
        # create a real order if the test orders did not raise an exception
        result = None
        try:
            result = self._client.order_oco_sell(
                symbol=symbol,
                quantity=quantity,
                price=price,
                stopPrice=stop_price,
                stopLimitPrice=stop_limit_price,
                stopLimitTimeInForce=stop_limit_time_in_force)

        except BinanceAPIException as e:
            # error handling goes here
            print(e)
        except BinanceOrderException as e:
            # error handling goes here
            print(e)

        return result

    def order_details(self, symbol, order_id):
        return self._client.get_order(symbol=symbol, orderId=order_id)

    # cancel previous orders (buy_limit['orderId']))
    def cancel_order(self, symbol, order_id):
        return self._client.cancel_order(symbol=symbol, orderId=order_id)

    # supported order type for the symbol
    def get_symbol_order_types(self, symbol):
        # use exchange info to confirm order types
        return self._client.get_symbol_info(symbol)

    # returns the list of tickers available in the market
    def get_all_tickers(self):
        return self._client.get_all_tickers()

    # returns the list of orders done for a specific symbol
    def get_all_orders_by_symbol(self, symbol, include_canceled=False):
        orders = self._client.get_all_orders(symbol=symbol)
        if include_canceled is False:
            # Filter python objects with list comprehensions
            orders = [x for x in orders if x['status'] != ORDER_STATUS_CANCELED]

        return orders

    # returns the list of orders
    def get_open_orders(self):
        orders = self._client.get_open_orders()
        return orders

    # get balances for futures account
    def futures_account_balance(self):
        return self._client.futures_account_balance()

    # Test connectivity to the Rest API
    def futures_ping_service(self):
        return self._client.futures_time()

    # get balances for futures account
    def futures_account_balance(self):
        return self._client.futures_account_balance()

    # Current exchange trading rules and symbol information
    def futures_exchange_info(self):
        return self._client.futures_exchange_info()

    # Get recent trades (up to last 500)
    def futures_recent_trades(self, symbol):
        return self._client.futures_recent_trades(symbol=symbol)

    # Get older market historical trades.
    def futures_historical_trades(self, symbol):
        return self._client.futures_historical_trades(symbol=symbol)

    # Best price/qty on the order book for a symbol or symbols.
    def futures_get_latest_price_info_by_symbol(self, symbol):
        result = self._client.futures_orderbook_ticker(symbol=symbol);
        bid_price = result['bidPrice']
        bid_quantity = result['bidQty']
        ask_price = result['askPrice']
        ask_quantity = result['askQty']
        result = {
            "bid_price": float(bid_price),
            "bid_quantity": float(bid_quantity),
            "ask_price": float(ask_price),
            "ask_quantity": float(ask_quantity)
        }
        return result

    # Get symbol historical prices
    # Check KLINE_INTERVAL enums (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
    def futures_historical_symbol_prices(self, symbol, interval, start_str=None, end_str=None, limit=1500,
                                         output="dataframe"):
        if start_str is None:
            klines_type: HistoricalKlinesType = HistoricalKlinesType.FUTURES
            start_str = self._client._get_earliest_valid_timestamp(symbol, interval, klines_type)

        bars = self._client.futures_historical_klines(symbol, interval, start_str, end_str, limit)

        # delete unwanted data - just keep date, open, high, low, close
        for line in bars:
            line[0] = datetime.fromtimestamp(line[0] / 1000.0, tz=timezone.utc)
            del line[6:]

        if output == "dataframe":
            data_frame = pd.DataFrame(bars, columns=['date', 'Open', 'High', 'Low', 'Close', 'Volume'])
            data_frame.set_index('date', inplace=True)
            return data_frame.apply(pd.to_numeric)
        else:
            return bars

    # Latest price for a symbol or symbols.
    def futures_get_ticker_performance_last_day(self, symbol):
        return self._client.futures_ticker(symbol)

    # Latest price for a symbol.
    def futures_get_symbol_price(self, symbol):
        return self._client.futures_symbol_ticker(symbol=symbol)["price"]

    def create_test_order(self, symbol, type, side, quantity):
        self._client.create_test_order(
            symbol=symbol,
            type=type,
            side=side,
            quantity=quantity
        )
        return True

    # Send in a new order.
    def futures_create_order(self, symbol, side, type, quantity, price=None, stopPrice=None, closePosition=None,
                             activationPrice=None, callbackRate=None, timeInForce="GTC", positionSide="BOTH"):
        return self._client.futures_create_order(symbol=symbol, side=side, type=type, quantity=quantity, price=price,
                                                 stopPrice=stopPrice)

    # Send in a a buy order at the current price of the symbol
    def futures_buy_at_current_price(self, symbol, quantity=None):
        if self.isTestnet is False and self.create_test_order(symbol, FUTURE_ORDER_TYPE_MARKET, "BUY",
                                                              quantity) is not True:
            raise Exception("Invalid order params")

        return self._client.futures_create_order(symbol=symbol, side=SIDE_BUY, type=FUTURE_ORDER_TYPE_MARKET,
                                                 quantity=quantity, positionSide="LONG")

    # Send in a buy order when the symbol hits a specific price
    def futures_buy_at_specific_price(self, symbol, price, quantity):
        if self.isTestnet is False and self.create_test_order(symbol, FUTURE_ORDER_TYPE_LIMIT, SIDE_BUY,
                                                              quantity) is not True:
            raise Exception("Invalid order params")

        return self._client.futures_create_order(symbol=symbol, side=SIDE_BUY, type=FUTURE_ORDER_TYPE_LIMIT,
                                                 quantity=quantity, price=price)

    # Send in a a buy order at the current price of the symbol
    def futures_sell_at_current_price(self, symbol, quantity):
        if self.isTestnet is False and self.create_test_order(symbol, FUTURE_ORDER_TYPE_MARKET, "SELL",
                                                              quantity) is not True:
            raise Exception("Invalid order params")

        return self._client.futures_create_order(symbol=symbol, side=SIDE_SELL, type=FUTURE_ORDER_TYPE_MARKET,
                                                 quantity=quantity, positionSide="LONG")

    # Send in a sell order when the symbol hits a specific price (Take profit)
    def futures_sell_at_specific_price(self, symbol, price, quantity):
        if self.isTestnet is False and self.create_test_order(symbol, FUTURE_ORDER_TYPE_LIMIT, "SELL",
                                                              quantity) is not True:
            raise Exception("Invalid order params")

        return self._client.futures_create_order(symbol=symbol, side=SIDE_SELL, type=FUTURE_ORDER_TYPE_LIMIT,
                                                 quantity=quantity, price=price)

    # Send in a sell order when the symbol hits a specific price (Stop Loss)
    def futures_place_stop_loss(self, symbol, stop_price, quantity):
        if self.isTestnet is False and self.create_test_order(symbol, FUTURE_ORDER_TYPE_STOP, "SELL",
                                                              quantity) is not True:
            raise Exception("Invalid order params")

        return self._client.futures_create_order(symbol=symbol, side=SIDE_SELL, type=FUTURE_ORDER_TYPE_STOP_MARKET,
                                                 stopPrice=stop_price, quantity=quantity, positionSide="LONG")

    # Send in a buy order when the symbol hits a specific price (Start Gain)
    def futures_place_start_gain(self, symbol, price, quantity):
        # if self.create_test_order(symbol, FUTURE_ORDER_TYPE_STOP, "BUY", quantity) is not True:
        #    raise Exception("Invalid order params")

        return self._client.futures_create_order(symbol=symbol, side=SIDE_BUY, type=FUTURE_ORDER_TYPE_STOP,
                                                 quantity=quantity, price=price)

    # Send in a buy order when the symbol hits a specific price (Take Profit)
    def futures_take_profit_order(self, symbol, take_profit, quantity):
        return self._client.futures_create_order(symbol=symbol, side=SIDE_SELL,
                                                 type=FUTURE_ORDER_TYPE_TAKE_PROFIT_MARKET,
                                                 quantity=quantity, positionSide="LONG", stopPrice=take_profit)

    # Cancel a specific order
    def futures_cancel_order(self, symbol, order_id):
        self._client.futures_cancel_order(symbol=symbol, orderId=order_id)

    def futures_get_all_orders(self, symbol):
        return self._client.futures_get_all_orders(symbol=symbol)

    def close_connection(self):
        self._client.close_connection()
