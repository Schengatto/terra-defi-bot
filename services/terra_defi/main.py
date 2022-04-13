# -*- coding: utf-8 -*-
"""
Created on 2022/04/12
@author: schengatto@gmail.com
"""
import json
import logging
import schedule
import time
import requests

from lib.utils import send_telegram_msg
from core.config_service import ConfigurationService
from core.events_registry_service import EventsRegistryService
from core.transactions_registry_service import TransactionsRegistryService
from core.orders_registry_service import OrdersRegistryService
from core.core_functions import *

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
logger = logging.getLogger()

configurationService = ConfigurationService()
eventsService = EventsRegistryService()
transactionsService = TransactionsRegistryService()
ordersService = OrdersRegistryService()

WEB_SERVER_URL = configurationService.get_configuration("web_server_url")
AUTOMATIC_BUY_LOW = configurationService.get_configuration("automatic_buy_low")
AUTOMATIC_SELL_HIGH = configurationService.get_configuration("automatic_sell_high")


def get_api_token():
    first = mnemonic_key.split(" ")[0]
    last = mnemonic_key.split(" ")[-1]
    return f"{first}-{last}"


def wallet_balance():
    r = requests.get(f'{WEB_SERVER_URL}/wallet/balance')
    return r.json()


def analyze_symbols():
    for asset in symbols:
        try:
            event_key = None
            ordersService.force_resync()
            symbol = asset.split("|")[0]
            provider = asset.split("|")[1]

            # trade coin
            if symbol == "LUNAUSDT":
                coin = 'uluna'
            elif symbol == "ANCUSDT":
                coin = "ANC"
            elif symbol == "MIRUSDT":
                coin = "MIR"
            else:
                raise Exception(f"Invalid coin: {symbol}")

            orders = ordersService.find_orders_by_symbol(symbol)
            prices = get_prices(symbol, provider)

            # last 24h performance
            daily_performance = get_daily_performance(symbol, provider)

            # min and max price for the selected period
            min_price, max_price = find_min_max(prices)
            low_price = round(min_price * 1.05, 2)
            high_price = round(max_price * 0.95, 2)
            current_price = prices.iloc[-1]["Close"]

            # support and resistances levels
            levels, supports, resistances = find_supports_and_resistances(prices)

            logger.info(f"Current price {current_price}. Orders: {orders}")
            messages_to_send = []

            # statistics
            message = f"🔎 Current price: {current_price} | Min: {min_price} | Max: {max_price} " \
                      f"| Low: {low_price} | High: {high_price} | Perf: {daily_performance}%"
            event_key = f"{symbol}_Statistics"
            if not eventsService.recently_notified(event_key, minutes=1140):
                eventsService.store_event(event_key)
                logging.info(message)
                messages_to_send.append(message)

            if current_price <= low_price:
                message = f"↘️ Low price detected. Current price is {current_price}, minimum price last month: {low_price}! Daily performance {daily_performance}%"
                event_key = f"{symbol}_LowPrice"
                if not eventsService.recently_notified(event_key, minutes=720):
                    eventsService.store_event(event_key)
                    logging.info(message)
                    messages_to_send.append(message)
                    if AUTOMATIC_BUY_LOW:
                        # BUY HERE
                        swap_amount = int(wallet_balance()['uusd'] * 0.10)
                        error, message = buy_coin(coin, swap_amount)
                        messages_to_send.append(message)
                        if error:
                            eventsService.remove_event(event_key)

            if current_price >= high_price:
                message = f"↗️ High price detected. Current price is {current_price}, maximum price last month: {high_price}! Daily performance {daily_performance}%"
                event_key = f"{symbol}_HighPrice"
                if not eventsService.recently_notified(event_key, minutes=720):
                    eventsService.store_event(event_key)
                    logging.info(message)
                    messages_to_send.append(message)
                    if AUTOMATIC_SELL_HIGH:
                        # SELL HERE
                        swap_amount = int(wallet_balance()[coin])
                        error, message = sell_coin(coin, swap_amount)
                        messages_to_send.append(message)
                        if error:
                            eventsService.remove_event(event_key)

            for order in orders:
                # target price in a range of 1% from current price
                order_id = order["id"]
                if order["type"] in ["BUY", "SELL"] and current_price * 1.003 > float(order["price"]) > current_price * 0.997:
                    coin = order["coin"]
                    swap_amount = int(order["amount"])
                    message = f"❗ Current price is {current_price}!!!"
                    if order["type"] == "BUY":
                        event_key = f"{symbol}_BUY_{order_id}"
                        current_ust_balance = int(wallet_balance()['uusd'])
                        if swap_amount < current_ust_balance:
                            messages_to_send.append(message)
                            error, message = buy_coin(coin, swap_amount)
                            messages_to_send.append(message)
                            if not error:
                                eventsService.store_event(event_key)
                                ordersService.set_order_processed(symbol, order_id)
                                # TODO remove
                                check = ordersService.find_order_by_id(symbol, order_id)
                                if check["processed"] is False:
                                    ordersService.remove_order(symbol, order_id)
                    else:
                        event_key = f"{symbol}_SELL_{order_id}"
                        current_coin_balance = int(wallet_balance()[coin])
                        if swap_amount < current_coin_balance:
                            messages_to_send.append(message)
                            error, message = sell_coin(coin, swap_amount)
                            messages_to_send.append(message)
                            if not error:
                                eventsService.store_event(event_key)
                                ordersService.set_order_processed(symbol, order_id)
                                # TODO remove
                                check = ordersService.find_order_by_id(symbol, order_id)
                                if check["processed"] is False:
                                    ordersService.remove_order(symbol, order_id)


                elif order["type"] == "WARN" and current_price * 1.003 > int(order["price"]) > current_price * 0.997:
                    event_key = f"{symbol}_WARN_{order_id}"
                    eventsService.store_event(event_key)
                    messages_to_send.append(f"❗ Current price is {current_price}!!!")
                    ordersService.set_order_processed(symbol, order_id)

            if len(messages_to_send) > 0:
                messages_to_send.insert(0, f"{symbol}:")
                msgs = "\n\n".join(messages_to_send)
                plot_all(supports, resistances, prices, symbol, provider)
                send_telegram_msg(messages=[msgs], images=[f"./resources/{symbol}.png"])

        except Exception as e:
            msg = f"❌ There was an error processing {asset}: {e}"
            logger.error(msg)
            raise Exception(e)
            if event_key is not None:
                eventsService.remove_event(event_key)
                # send_telegram_msg(messages=[msg])


def buy_coin(coin, amount):
    error = False
    try:
        params = {
            "from": "uusd",
            "to": coin,
            "amount": str(amount)
        }
        headers = {
            "token": get_api_token()
        }
        response = requests.get(f"{WEB_SERVER_URL}/terra/swap", params=params, headers=headers).json()
        if response["error"]:
            raise Exception(response["message"])
        message = response["message"]
        transactionsService.store_transaction(message)
    except Exception as e:
        message = response["message"]
        error = True

    logging.info(message)
    return error, message


def sell_coin(coin, amount):
    error = False
    try:
        params = {
            "from": coin,
            "to": "uusd",
            "amount": str(amount)
        }
        headers = {
            "token": get_api_token()
        }
        response = requests.get(f"{WEB_SERVER_URL}/terra/swap", params=params, headers=headers).json()
        if response["error"]:
            raise Exception(response["message"])
        message = response["message"]
        transactionsService.store_transaction(message)
    except Exception as e:
        message = response["message"]
        error = True

    logging.info(message)
    return error, message


def read_mnemonic_key():
    mk_fp = configurationService.get_configuration("mk_file")
    if not os.path.exists(mk_fp):
        raise Exception(f"Mnemonic file not found: {mk_fp}")

    mk_file = open(mk_fp, "r+")
    mk = json.loads(mk_file.readline())
    if len(mk) < 24:
        raise Exception(f"Invalid mnemonic... it should have at least 24 words")

    return " ".join(mk)


symbols = configurationService.get_configuration("symbols")
logger.info(symbols)

mnemonic_key = read_mnemonic_key()

# do logic
analyze_symbols()

# next calls are scheduled
schedule.every(1).minute.do(analyze_symbols)
while True:
    # Checks whether a scheduled task
    # is pending to run or not
    schedule.run_pending()
    time.sleep(10)
