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

from core.helpers.init_database_helper import InitDatabaseHelper
from core.services.config_service import ConfigurationService
from core.repositories.events_repository import EventsRepository
from core.repositories.orders_repository import OrdersRepository, OrderType
from core.repositories.transactions_repository import TransactionsRepository
from core.connectors.terra_client import TerraClient
from core.functions.core_functions import check_pair_current_swap_info
from core.repositories.terra_tokens_repository import TerraTokensRepository

app = Flask(__name__)
app.config['CORS_HEADERS'] = 'Content-Type'
cors = CORS(app, resources={r"/*": {"origins": "*"}})

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger()

configurationService = ConfigurationService()

# init database helpers
initDatabaseHelper = InitDatabaseHelper()

# services
tokensRepository = TerraTokensRepository()
eventsService = EventsRepository()
transactionsService = TransactionsRepository()
ordersService = OrdersRepository()


def is_valid_token(token):
    first = mnemonic_key.split(" ")[0]
    last = mnemonic_key.split(" ")[-1]
    return token == f"{first}-{last}"


@app.route('/health')
def service_status():
    result = {"status": "OK", "terra-node": "testnet" if is_testnet else "mainnet"}
    return jsonify(result)


@app.route('/wallet/address')
def get_address():
    result = tc.get_address()
    return jsonify(result)


@app.route('/wallet/balance')
def get_balance():
    b = tc.get_full_balance()
    return jsonify(b)


@app.route('/wallet/balance/<token>')
def get_balance_by_coin(token: str):
    if token in tokensRepository.get_native_tokens():
        b = {
            f"{token}": tc.get_balance()[token].amount
        }
    else:
        balance = tc.get_coin_balance(token)
        b = {
            f"{token}": balance["result"]["balance"]
        }
    return jsonify(b)


@app.route('/terra/coins')
def get_native_coins():
    result = tc.get_native_coins()
    return jsonify(result)


# TODO: change in POST
@app.route('/terra/swap')
def swap_trade():
    pair_contract = request.args.get("pair_contract")
    offer_token_contract = request.args.get("offer_token_contract")
    ask_token_contract = request.args.get("ask_token_contract")
    amount = request.args.get("amount")
    token = request.headers['token'] if 'token' in request.headers else None

    if not is_valid_token(token):
        raise Exception("Invalid token")

    if pair_contract is None:
        raise Exception("Provide a valid value to pair_contract")

    if offer_token_contract is None:
        raise Exception("Provide a valid value to offer_token_contract")

    if ask_token_contract is None:
        raise Exception("Provide a valid value to ask_token_contract")

    if amount is None:
        raise Exception("Provide a valid value to amount_to_swap")

    error = False
    try:
        tx, price = tc.swap(pair_contract=pair_contract,
                            offer_token_contract=offer_token_contract,
                            ask_token_contract=ask_token_contract,
                            amount_to_swap=amount)
        tx_url = f"{tc.terra_finder_url()}{tx}"
        message = f"Traded {amount} {ask_token_contract} for {offer_token_contract}. Tx: {tx_url} @ {price}"
        transactionsService.save_transaction(pair_contract, offer_token_contract, ask_token_contract,
                                             float(amount), price, tx)
    except Exception as e:
        message = f"Error while trading {amount} {ask_token_contract} for {offer_token_contract}.\n {e}"
        logging.info(message)
        error = True

    return {"message": message, "error": error}


@app.route('/terra/swap-price', methods=['GET'])
def current_swap_price():
    pair_contract = request.args.get("pair_contract")
    ask_token_contract = request.args.get("ask_token_contract")
    if pair_contract is None:
        raise Exception("Provide a valid value to pair_contract")
    if ask_token_contract is None:
        raise Exception("Provide a valid value to ask_token_contract")

    trade_info = tc.current_swap_price(pair_contract=pair_contract, ask_token_contract=ask_token_contract)
    return trade_info


@app.route('/orders', methods=['GET'])
def get_orders():
    result = ordersService.get_orders()
    return jsonify(result)


@app.route('/orders', methods=['POST'])
def create_order():
    try:
        result = "Bad Response"

        request_data = request.get_json()
        pair_name = request_data["pair_name"] or None
        asked_token_symbol = request_data["asked_token_symbol"] or None
        order_type = request_data["type"] or None
        price = request_data["price"] or None
        amount = request_data["amount"] or None
        token = request.headers['token'] if 'token' in request.headers else None

        available_pair_names = list(map(lambda t: t['name'], tokensRepository.get_pairs()))
        if pair_name is None or pair_name not in available_pair_names:
            result = "Provide a valid value to pair_name: " + ",".join(available_pair_names)
            raise Exception(result)

        available_token_symbols = list(map(lambda t: t['symbol'], tokensRepository.get_tokens()))
        if asked_token_symbol is None or asked_token_symbol not in available_token_symbols:
            result = "Provide a valid value to asked_token_symbol: " + ",".join(available_token_symbols)
            raise Exception(result)

        allowed_order_types = [OrderType.Buy.value, OrderType.Sell.value, OrderType.Warn.value]
        if order_type is None or order_type not in allowed_order_types:
            result = "Provide a valid value to order: " + ",".join(allowed_order_types)
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

        result = ordersService.store_new_order(pair_name=pair_name,
                                               asked_token_symbol=asked_token_symbol,
                                               order_type=order_type,
                                               price=float(price),
                                               amount=float(amount) if amount is not None else None)
    except Exception as e:
        logger.error(e)

    return jsonify(result)


@app.route('/orders', methods=['DELETE'])
def remove_order():
    order_id = request.args.get("id") or None
    ordersService.remove_order(order_id)
    return "Done"


@app.route('/events', methods=['GET'])
def get_events():
    result = eventsService.get_events()
    return jsonify(result)


@app.route('/events/<event_name>', methods=['GET'])
def get_events_by_name(event_name: str):
    result = eventsService.find_event_by_name(event_name)
    return jsonify(result)


@app.route('/events/<event_name>', methods=['DELETE'])
def remove_event(event_name: str):
    result = eventsService.remove_event(event_name)
    return jsonify(result)


@app.route('/tokens/<token_id>', methods=['GET'])
def get_token_by_id(token_id: str):
    result = tokensRepository.find_token_by_id(token_id)
    return jsonify(result)


@app.route('/tokens', methods=['GET'])
def get_tokens():
    token_symbol = request.args.get("symbol") or None
    token_name = request.args.get("name") or None
    mainnet_contract = request.args.get("mainnet_contract") or None
    testnet_contract = request.args.get("testnet_contract") or None
    result = tokensRepository.get_tokens(token_symbol=token_symbol,
                                         token_name=token_name,
                                         mainnet_contract=mainnet_contract,
                                         testnet_contract=testnet_contract)
    return jsonify(result)


@app.route('/tokens-pairs/<pair_id>', methods=['GET'])
def get_tokens_pair_by_id(pair_id: str):
    result = tokensRepository.find_pair_by_id(pair_id)
    return jsonify(result)


@app.route('/tokens-pairs', methods=['GET'])
def get_tokens_pairs():
    pair_name = request.args.get("name") or None
    mainnet_contract = request.args.get("mainnet_contract") or None
    testnet_contract = request.args.get("testnet_contract") or None
    result = tokensRepository.get_pairs(pair_name=pair_name,
                                        mainnet_contract=mainnet_contract,
                                        testnet_contract=testnet_contract)
    return jsonify(result)


@app.route('/tokens-pairs-price/<pair_contract>', methods=['GET'])
def get_tokens_pairs_price(pair_contract: str):
    token_contract = request.args.get("token_contract") or None
    result = check_pair_current_swap_info(pair_contract, token_contract, is_testnet)
    return jsonify(result)


@app.route('/tokens-pairs-details', methods=['GET'])
def get_tokens_pairs_details():
    is_node_testnet = request.args.get("node") == 'testnet' or is_testnet
    result = tokensRepository.get_testnet_pairs_details() if is_node_testnet else tokensRepository.get_mainnet_pairs_details()
    return jsonify(result)


@app.route('/tokens-pairs-available', methods=['GET'])
def get_tokens_pairs_available():
    is_node_testnet = request.args.get("node") == 'testnet' or is_testnet
    result = tokensRepository.get_testnet_pairs_details() if is_node_testnet else tokensRepository.get_mainnet_pairs_details()
    return jsonify(list(map(lambda p: p['name'], result)))


@app.route('/wallet/transactions')
def get_transactions():
    return jsonify(transactionsService.get_transactions())


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
is_testnet = (not os.getenv("MAINNET") == 'true') if os.getenv(
    "MAINNET") is not None else configurationService.get_configuration("testnet")
tc = TerraClient(mnemonic_key, testnet=is_testnet)
logging.info(f"Connected to {'testnet' if tc.is_testnet() else 'mainnet'} with wallet address {tc.get_address()}")
logging.info(f"Wallet balance: {tc.get_full_balance()}")

PORT_FIELD = "server_port_test" if is_testnet else "server_port"
SERVER_PORT = configurationService.get_configuration(PORT_FIELD)

SSL_CONTEXT = None
SSL_CERTIFICATES_FOLDER = os.getenv("SSL_CERTIFICATES_FOLDER", "./settings/certs/")
if SSL_CERTIFICATES_FOLDER is not None and os.path.exists(SSL_CERTIFICATES_FOLDER) and os.path.exists(f"{SSL_CERTIFICATES_FOLDER}/fullchain.pem") and os.path.exists(f"{SSL_CERTIFICATES_FOLDER}/privkey.pem") :
    SSL_CONTEXT = (f"{SSL_CERTIFICATES_FOLDER}/fullchain.pem", f"{SSL_CERTIFICATES_FOLDER}/privkey.pem")

service_port = os.getenv("API_SERVICE_PORT") if os.getenv("API_SERVICE_PORT") is not None else SERVER_PORT

if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0', port=service_port, ssl_context=SSL_CONTEXT)
