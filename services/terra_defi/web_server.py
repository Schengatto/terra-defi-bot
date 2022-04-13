# -*- coding: utf-8 -*-
"""
Created on 2022/04/12
@author: schengatto@gmail.com
"""
import json
import logging
import os

from flask import Flask, request, jsonify
from flask_cors import CORS

from lib.terra_client import TerraClient
from core.config_service import ConfigurationService
from core.events_registry_service import EventsRegistryService
from core.transactions_registry_service import TransactionsRegistryService
from core.orders_registry_service import OrdersRegistryService

app = Flask(__name__)
app.config['CORS_HEADERS'] = 'Content-Type'
cors = CORS(app, resources={r"/*": {"origins": "*"}})

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
logger = logging.getLogger()

configurationService = ConfigurationService()
eventsService = EventsRegistryService()
transactionsService = TransactionsRegistryService()
ordersService = OrdersRegistryService()


def is_valid_token(token):
    first = mnemonic_key.split(" ")[0]
    last = mnemonic_key.split(" ")[-1]
    return token == f"{first}-{last}"


@app.route('/health')
def service_status():
    result = "OK"
    resp = jsonify(result)
    return resp


@app.route('/wallet/address')
def get_address():
    result = tc.get_address()
    return jsonify(result)


@app.route('/wallet/balance')
def get_balance():
    b = tc.get_full_balance()
    return jsonify(b)


@app.route('/wallet/balance/<coin>')
def get_balance_by_coin(coin: str):
    balance = tc.get_coin_balance(coin)
    b = {
        f"{coin}": balance["result"]["balance"]
    }
    return jsonify(b)


@app.route('/terra/coins')
def get_native_coins():
    result = tc.get_native_coins()
    return jsonify(result)


# TODO: change in POST
@app.route('/terra/swap')
def swap_non_native():
    from_asset = request.args.get("from")
    to_asset = request.args.get("to")
    amount = request.args.get("amount")
    token = request.headers['token'] if 'token' in request.headers else None

    if not is_valid_token(token):
        raise Exception("Invalid token")

    if from_asset is None:
        raise Exception("Provide a valid value to from_asset")

    if to_asset is None:
        raise Exception("Provide a valid value to to_asset")

    if amount is None:
        raise Exception("Provide a valid value to amount_to_swap")

    error = False
    try:
        tx = tc.swap(from_coin=from_asset,
                     to_coin=to_asset,
                     amount_to_swap=amount)
        tx_url = f"{tc.terra_finder_url()}{tx}"
        message = f"Traded {amount} {from_asset} for {to_asset}. Tx: {tx_url}"
        transactionsService.store_transaction(message)
    except Exception as e:
        message = f"Error while trading {amount} {from_asset} for {to_asset}.\n {e}"
        logging.info(message)
        error = True

    return {"message": message, "error": error}


@app.route('/orders/list')
def get_orders():
    ordersService.force_resync()
    result = ordersService.get_orders()
    return jsonify(result)


# TODO: change in POST
@app.route('/orders/create')
def create_order():
    try:
        result = "Bad Response"
        symbol = request.args.get("symbol") or None
        order_type = request.args.get("order") or None
        price = request.args.get("price") or None
        amount = request.args.get("amount") or None
        token = request.headers['token'] if 'token' in request.headers else None

        if symbol is None or symbol not in ["LUNAUSDT", "ANCUSDT", "MIRUSDT"]:
            result = "Provide a valid value to symbol." + ",".join(["LUNAUSDT", "ANCUSDT", "MIRUSDT"])
            raise Exception(result)

        # trade coin
        if symbol == "LUNAUSDT":
            coin = 'uluna'
        elif symbol == "ANCUSDT":
            coin = "ANC"
        elif symbol == "MIRUSDT":
            coin = "MIR"
        else:
            raise Exception(f"Invalid coin: {symbol}")

        if order_type is None or order_type not in ["BUY", "SELL", "WARN"]:
            result = "Provide a valid value to order." + ",".join(["BUY", "SELL", "WARN"])
            raise Exception(result)

        if order_type in ["BUY", "SELL"] and not is_valid_token(token):
            result = "Invalid token"
            raise Exception(result)

        if price is None:
            result = "Provide a valid value to price"
            raise Exception(result)

        if order_type in ["BUY", "SELL"] and amount is None:
            result = "Provide a valid value to amount"
            raise Exception(result)

        ordersService.force_resync()
        result = ordersService.store_new_order(symbol=symbol,
                                               coin=coin,
                                               order_type=order_type,
                                               price=float(price),
                                               amount=str(amount))
    except Exception as e:
        logger.error(e)

    return jsonify(result)


@app.route('/orders/remove')
def remove_order():
    symbol = request.args.get("symbol") or None
    order_id = request.args.get("id") or None
    ordersService.force_resync()
    ordersService.remove_order(symbol, order_id)
    return "Done"


@app.route('/wallet/transactions')
def get_transactions():
    return transactionsService.get_transactions()


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
use_testnet = configurationService.get_configuration("testnet")
tc = TerraClient(mnemonic_key, testnet=use_testnet)
logging.info(f"Connected to {'testnet' if tc.is_testnet() else 'mainnet'} with wallet address {tc.get_address()}")
logging.info(f"Wallet balance: {tc.get_full_balance()}")

if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0', port=5020)
