# -*- coding: utf-8 -*-
"""
Created on 2022/04/12
@author: schengatto@gmail.com
"""
import json

import schedule

from core.functions.core_functions import *
from core.helpers.init_database_helper import InitDatabaseHelper
from core.repositories.events_repository import EventsRepository, EventType
from core.repositories.orders_repository import OrdersRepository, OrderType
from core.repositories.terra_tokens_repository import TerraTokensRepository
from core.repositories.transactions_repository import TransactionsRepository
from core.services.config_service import ConfigurationService
from core.utilities.notifications_utils import send_telegram_msg

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger()

# configuration
configurationService = ConfigurationService()
is_testnet = (not os.getenv("MAINNET") == 'true') if os.getenv(
    "MAINNET") is not None else configurationService.get_configuration("testnet")

SERVER_HOST = os.getenv("API_SERVICE_HOST", configurationService.get_configuration('web_server_url'))
PORT_FIELD = "server_port_test" if is_testnet else "server_port"
SERVER_PORT = os.getenv("API_SERVICE_PORT", configurationService.get_configuration(PORT_FIELD))
WEB_SERVER_URL = f"{SERVER_HOST}:{SERVER_PORT}/"
AUTOMATIC_BUY_LOW = configurationService.get_configuration("automatic_buy_low")
AUTOMATIC_SELL_HIGH = configurationService.get_configuration("automatic_sell_high")
IS_TELEGRAM_ENABLED = configurationService.get_configuration("telegram_enabled")

logger.info(f"Service started using node {'testnet' if is_testnet else 'mainnet'}")

# init database helpers
initDatabaseHelper = InitDatabaseHelper()

# services
eventsService = EventsRepository()
transactionsService = TransactionsRepository()
terraTokensRepository = TerraTokensRepository()
ordersService = OrdersRepository()


def send_telegram_notification(messages=[], images=[]):
    if IS_TELEGRAM_ENABLED:
        conf = "./settings/telegram_conf/testnet.conf" if is_testnet else "./settings/telegram_conf/mainnet.conf"
        send_telegram_msg(messages=messages, images=images, conf=conf)


def get_api_token():
    first = mnemonic_key.split(" ")[0]
    last = mnemonic_key.split(" ")[-1]
    return f"{first}-{last}"


def wallet_balance():
    r = requests.get(f'{WEB_SERVER_URL}/wallet/balance')
    return r.json()


def get_token_balance(token_contract: str):
    r = requests.get(f'{WEB_SERVER_URL}/wallet/balance/{token_contract}')
    return r.json()


def process_orders():
    orders = ordersService.get_orders()
    orderGroups = {}
    for order in orders:
        key = f"{order['terra_pair']}@{order['token']}"
        if key not in orderGroups:
            orderGroups[key] = []
        orderGroups[key].append(order)

    for op in list(orderGroups.keys()):
        logger.debug(f"OrderGroup: {op}")
        try:
            terra_pair_id = op.split('@', 1)[0]
            token_id = op.split('@', 1)[1]
            # TODO move token contract and pair contract on order object for best performances
            order_token_symbol = terraTokensRepository.find_token_by_id(token_id)[0]
            pair = terraTokensRepository.find_pair_by_id(terra_pair_id)[0]
            token_contract = order_token_symbol["testnet_contract"] if is_testnet else order_token_symbol[
                "mainnet_contract"]
            pair_contract = pair["testnet_contract"] if is_testnet else pair["mainnet_contract"]
            trade_info = check_pair_current_swap_info(pair_contract, token_contract, is_testnet)['trade']
            current_price = float(trade_info['price'])
            asked_token_symbol = trade_info['ask']
            asked_token_address = trade_info['ask_contract']
            offered_token_symbol = trade_info['offer']
            offered_token_address = trade_info['offer_contract']

            logger.info(f"Current price {current_price} {offered_token_symbol}.")
            messages_to_send = []

            for order in orderGroups[op]:
                order_id = order["id"]
                order_type = order["type"]
                logger.info(f"Order: {order_id} | {order_type}")
                # target price in a range of 1% from current price

                if order_type in [OrderType.Buy.value, OrderType.Sell.value]:
                    swap_amount = int(order["amount"])
                    message = f"Current price is {current_price}!!!"
                    if order_type == OrderType.Buy.value and current_price * 1.002 > float(
                            order["price"]) > current_price * 0.995:
                        logger.info(f"Processing order: {order['type']} @ price {current_price}")
                        event_name = f"{current_price}_{EventType.TradeBuy.value}_{order_id}"
                        current_token_balance = int(get_token_balance(offered_token_address)[offered_token_address])
                        if swap_amount < current_token_balance:
                            messages_to_send.append(f"❗ {message}")
                            message = swap_tokens(pair_contract, offered_token_address, asked_token_address,
                                                  swap_amount, current_price)
                            messages_to_send.append(message)
                            eventsService.store_event(EventType.TradeBuy, event_name, message)
                            ordersService.set_order_processed(order_id)
                        else:
                            raise Exception(f"Insufficient balance: {current_token_balance} {offered_token_symbol}")
                    elif order_type == OrderType.Sell.value and current_price * 1.005 > float(
                            order["price"]) > current_price * 0.998:
                        logger.info(f"Processing order: {order['type']} @ price {current_price}")
                        event_name = f"{asked_token_symbol}_{EventType.TradeSell.value}_{order_id}"
                        current_token_balance = int(get_token_balance(offered_token_address)[offered_token_address])
                        if swap_amount < current_token_balance:
                            messages_to_send.append(f"❗ {message}")
                            message = swap_tokens(pair_contract, asked_token_address, offered_token_address,
                                                  swap_amount, current_price)
                            messages_to_send.append(message)
                            eventsService.store_event(EventType.TradeSell, event_name, message)
                            ordersService.set_order_processed(order_id)
                        else:
                            raise Exception(f"Insufficient balance: {current_token_balance} {offered_token_symbol}")

                elif order_type == OrderType.Warn.value and current_price * 1.003 > float(
                        order["price"]) > current_price * 0.997:
                    event_name = f"{asked_token_symbol}_{EventType.PriceWarning.value}_{order_id}"
                    message = f"Current price is {current_price}!!!"
                    eventsService.store_event(EventType.PriceWarning, event_name, message)
                    messages_to_send.append(f"❗ {message}")
                    ordersService.set_order_processed(order_id)

                if len(messages_to_send) > 0:
                    messages_to_send.insert(0, f"{asked_token_symbol}:")
                    msgs = "\n\n".join(messages_to_send)
                    logger.info(msgs)
                    send_telegram_notification(messages=[msgs])

        except Exception as e:
            msg = f"❌ There was an error processing orderGroup {op}: {e}"
            logger.error(msg)
            send_telegram_notification(messages=[msg])


def swap_tokens(pair_contract: str, offer_contract: str, ask_contract: str, amount, price):
    params = {
        "pair_contract": pair_contract,
        "offer_token_contract": offer_contract,
        "ask_token_contract": ask_contract,
        "amount": str(amount)
    }
    check_price_resp = requests.get(f"{WEB_SERVER_URL}/terra/swap-price", params=params).json()
    if float(check_price_resp['price']) > price * 1.01:
        raise Exception(f"Market price is higher than current price: {check_price_resp['price']} {price}")

    headers = {
        "token": get_api_token()
    }
    response = requests.get(f"{WEB_SERVER_URL}/terra/swap", params=params, headers=headers).json()
    if response["error"]:
        raise Exception(response["message"])
    message = response["message"]

    logging.info(message)
    return message


def read_mnemonic_key():
    mk_fp = configurationService.get_configuration("mk_file")
    if not os.path.exists(mk_fp):
        raise Exception(f"Mnemonic file not found: {mk_fp}")

    mk_file = open(mk_fp, "r+")
    mk = json.loads(mk_file.readline())
    if len(mk) < 24:
        raise Exception(f"Invalid mnemonic... it should have at least 24 words")

    return " ".join(mk)


mnemonic_key = read_mnemonic_key()

# do logic
process_orders()

# next calls are scheduled
schedule.every(1).minute.do(process_orders)
while True:
    # Checks whether a scheduled task
    # is pending to run or not
    schedule.run_pending()
    time.sleep(10)
