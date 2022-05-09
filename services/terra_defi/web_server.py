# -*- coding: utf-8 -*-
"""
Created on 2022/04/12
@author: schengatto@gmail.com
"""
import json
import logging
import os
import asyncio

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from flask import Flask, request, jsonify, Response
from flask_cors import CORS

from core.helpers.init_database_helper import InitDatabaseHelper
from core.services.config_service import ConfigurationService
from core.repositories.events_repository import EventsRepository
from core.repositories.orders_repository import OrdersRepository, OrderType, OrderStatus
from core.repositories.transactions_repository import TransactionsRepository
from core.connectors.terra_client import TerraClient
from core.functions.core_functions import check_pair_current_swap_info, current_ust_prices
from core.repositories.terra_tokens_repository import TerraTokensRepository
from core.repositories.positions_repository import PositionsRepository

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
positionsService = PositionsRepository()

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["12 per second"]
)


def is_valid_auth_token(token: str):
    first = mnemonic_key.split(" ")[0]
    last = mnemonic_key.split(" ")[-1]
    return token == f"{first}-{last}"


def is_valid_auth_token_header(req):
    auth_token = req.headers['authToken'] if 'authToken' in request.headers else None
    return is_valid_auth_token(auth_token)


async def get_swap_price(pair_contract: str = None, ask_token_contract: str = None):
    price = tc.current_swap_price(pair_contract=pair_contract, ask_token_contract=ask_token_contract)['price']
    return round(price, 4)


@app.route('/login', methods=['POST'])
@limiter.limit("1/second", override_defaults=True)
def login():
    request_data = request.get_json()
    auth_token = request_data["authToken"] or None

    if not is_valid_auth_token(auth_token):
        return Response(response="Unauthorized", status=401)

    return jsonify({"walletAddress": tc.get_address()})


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


@app.route('/wallet/balance-symbols')
def get_balance_with_symbols():
    tokens = request.args.get("tokens") or "ANC,MIR,MARS,TWD"
    contracts = []
    for t in tokens.split(","):
        ti = tokensRepository.find_token_by_symbol(t)
        c = ti['mainnet_contract'] if is_testnet is False else ti['testnet_contract']
        contracts.append(c)

    b = tc.get_full_balance(tokens=contracts)
    result = {}
    for c in b:
        token = tokensRepository.find_token_by_contract(c)
        result[token['symbol']] = round(b[c] / 10 ** token['decimal_digits'], 4)

    return jsonify(result)


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
    order_id = request.args.get("order_id")

    if not is_valid_auth_token_header(request):
        return Response(response="Unauthorized", status=401)

    if pair_contract is None:
        return Response(response="Provide a valid value to pair_contract", status=401)

    if offer_token_contract is None:
        return Response(response="Provide a valid value to offer_token_contract", status=401)

    if ask_token_contract is None:
        return Response(response="Provide a valid value to ask_token_contract", status=401)

    if amount is None:
        return Response(response="Provide a valid value to amount_to_swap", status=401)

    logging.info(f"Swap: {pair_contract}, {offer_token_contract}, {ask_token_contract}, {amount}")

    error = False
    try:
        tx, price, amount_received = tc.swap(pair_contract=pair_contract,
                                             offer_token_contract=offer_token_contract,
                                             ask_token_contract=ask_token_contract,
                                             amount_to_swap=amount)
        tx_url = f"{tc.terra_finder_url()}{tx}"

        offered_token = tokensRepository.find_token_by_contract(offer_token_contract)
        asked_token = tokensRepository.find_token_by_contract(ask_token_contract)

        offered_amount = round(int(amount) / 10 ** int(offered_token['decimal_digits']), 4)
        received_amount = round(int(amount_received) / 10 ** int(asked_token['decimal_digits']), 6)

        message = f"Traded {offered_amount} {offered_token['symbol']} for {received_amount:.6f} {asked_token['symbol']}. Tx: {tx_url} @ price: {price}"
        transaction_id = transactionsService.save_transaction(pair_contract,
                                                              offer_token_contract,
                                                              ask_token_contract,
                                                              float(amount),
                                                              float(amount_received),
                                                              price,
                                                              tx,
                                                              order_id=order_id)

        # TODO temp
        if offer_token_contract == 'uusd':
            positionsService.open_position(pair_contract, ask_token_contract, transaction_id)

        else:
            # TODO: write for better performances - close position if any
            positions = positionsService.get_positions()
            for p in positions:
                if p.open_order_id == order_id:
                    positionsService.close_position(p, transaction_id)
                    break

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
        return Response(response="Provide a valid value to pair_contract", status=401)
    if ask_token_contract is None:
        return Response(response="Provide a valid value to ask_token_contract", status=401)

    trade_info = tc.current_swap_price(pair_contract=pair_contract, ask_token_contract=ask_token_contract)
    return trade_info


@app.route('/orders', methods=['GET'])
def get_orders():
    result = ordersService.get_orders()
    return jsonify(result)


@app.route('/orders-grouped', methods=['GET'])
def get_orders_grouped():
    prices = request.args.get("prices") or None
    orders = ordersService.get_orders()
    groups = []
    for o in orders:
        found = None
        g = {"terra_pair": o['terra_pair'],
             "name": o["name"],
             "terra_pair_contract": o['terra_pair_contract'],
             "orders": []}
        for grp in groups:
            if g["terra_pair"] == grp["terra_pair"]:
                found = grp
                break
        if found is not None:
            grp["orders"].append(o)
        else:
            g["orders"].append(o)
            groups.append(g)

    if prices is not None:
        current_prices = current_ust_prices()
        for grp in groups:
            pair = grp['terra_pair_contract']
            grp['price'] = current_prices[pair]

    return jsonify(groups)


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

        if not is_valid_auth_token_header(request):
            return Response(response="Unauthorized", status=401)

        available_pair_names = list(map(lambda t: t['name'], tokensRepository.get_pairs()))
        if pair_name is None or pair_name not in available_pair_names:
            result = "Provide a valid value to pair_name: " + ",".join(available_pair_names)
            return Response(response=result, status=401)

        available_token_symbols = list(map(lambda t: t['symbol'], tokensRepository.get_tokens()))
        if asked_token_symbol is None or asked_token_symbol not in available_token_symbols:
            result = "Provide a valid value to asked_token_symbol: " + ",".join(available_token_symbols)
            return Response(response=result, status=401)

        allowed_order_types = [OrderType.Buy.value, OrderType.Sell.value, OrderType.Warn.value]
        if order_type is None or order_type not in allowed_order_types:
            result = "Provide a valid value to order: " + ",".join(allowed_order_types)
            return Response(response=result, status=401)

        if price is None:
            result = "Provide a valid value to price"
            return Response(response=result, status=401)

        if order_type in ["BUY", "SELL"] and amount is None:
            result = "Provide a valid value to amount"
            return Response(response=result, status=401)

        result = ordersService.store_new_order(pair_name=pair_name,
                                               asked_token_symbol=asked_token_symbol,
                                               order_type=order_type,
                                               price=float(price),
                                               amount=int(amount) if amount is not None else None)
    except Exception as e:
        logger.error(e)

    return jsonify(result)


@app.route('/orders', methods=['DELETE'])
def remove_order():
    if not is_valid_auth_token_header(request):
        return Response(response="Unauthorized", status=401)

    order_id = request.args.get("id") or None
    ordersService.remove_order(order_id)
    return "Done"


@app.route('/orders', methods=['PATCH'])
def retry_order():
    if not is_valid_auth_token_header(request):
        return Response(response="Unauthorized", status=401)

    order_id = request.args.get("id") or None
    ordersService.update_order_status(order_id, OrderStatus.ToProcess)
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


@app.route('/tokens/pairs-price-ust', methods=['GET'])
def get_current_price_by_pair_contract():
    pair_name = request.args.get("pair_name") or None
    pair_contract = request.args.get("pair_contract")

    if pair_name is None and pair_contract is None:
        result = "Provide a valid value to pair_name or pair_contract"
        return Response(response=result, status=400)

    if pair_contract is None:
        key = "testnet_contract" if is_testnet else "mainnet_contract"
        pair_contract = tokensRepository.find_pair_by_name(pair_name)[key]

    price_ust = current_ust_prices[pair_contract]
    return {"price": price_ust}


@app.route('/tokens/prices-ust', methods=['GET'])
def get_current_tokens_price_ust():
    return current_ust_prices()


@app.route('/tokens/pairs-price', methods=['GET'])
def get_tokens_pairs_price_terra_swap():
    pair_name = request.args.get("pair_name") or None
    pair_contract = request.args.get("pair_contract") or None
    token_symbol = request.args.get("token_symbol") or None
    token_contract = request.args.get("token_contract") or None

    if pair_name is None and pair_contract is None:
        result = "Provide a valid value to pair_name or pair_contract"
        return Response(response=result, status=400)

    if pair_contract is None:
        key = "testnet_contract" if is_testnet else "mainnet_contract"
        pair_contract = tokensRepository.find_pair_by_name(pair_name)[key]

    if token_contract is None and token_symbol is not None:
        key = "testnet_contract" if is_testnet else "mainnet_contract"
        token_contract = tokensRepository.find_token_by_symbol(token_symbol)[key]

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


@app.route('/positions', methods=['GET'])
def get_positions():
    if not is_valid_auth_token_header(request):
        return Response(response="Unauthorized", status=401)

    include_closed = False if request.args.get("include_closed", True) == "false" else True
    result = list(map(lambda p: p.toJSON(), positionsService.get_positions(include_closed=include_closed)))
    return jsonify(result)


@app.route('/positions', methods=['POST'])
def close_position():
    if not is_valid_auth_token_header(request):
        return Response(response="Unauthorized", status=401)

    request_data = request.get_json()
    position_id = request_data["id"] or None

    # sell transaction to close the position
    position = positionsService.find_position_by_id(position_id)
    if position is None:
        return Response(response=f"Position with id {position_id} was not found", status=404)

    pair_contract = position.pair_mainnet_contract if is_testnet is False else position.pair_testnet_contract
    offer_token_contract = position.token_mainnet_contract if is_testnet is False else position.token_testnet_contract
    ust_token = tokensRepository.find_token_by_symbol("UST")
    ask_token_contract = ust_token['mainnet_contract'] if is_testnet is False else ust_token["testnet_contract"]
    amount = position.open_transaction_amount_received
    logging.info(f"Swap: {pair_contract}, {offer_token_contract}, {ask_token_contract}, {amount}")
    try:
        tx, price, amount_received = tc.swap(pair_contract=pair_contract,
                                             offer_token_contract=offer_token_contract,
                                             ask_token_contract=ask_token_contract,
                                             amount_to_swap=amount)
        tx_url = f"{tc.terra_finder_url()}{tx}"

        offered_token = tokensRepository.find_token_by_contract(offer_token_contract)
        asked_token = tokensRepository.find_token_by_contract(ask_token_contract)

        offered_amount = round(int(amount) / 10 ** int(offered_token['decimal_digits']), 4)
        received_amount = round(int(amount_received) / 10 ** int(asked_token['decimal_digits']), 6)

        message = f"Traded {offered_amount} {offered_token['symbol']} for {received_amount:.6f} {asked_token['symbol']}. Tx: {tx_url} @ price: {price}"
        transaction_id = transactionsService.save_transaction(pair_contract, offer_token_contract, ask_token_contract,
                                                              float(amount), float(amount_received), price, tx)

        positionsService.close_position(position_id, transaction_id)

    except Exception as e:
        message = f"Error while trading {amount} {ask_token_contract} for {offer_token_contract}.\n {e}"
        logging.info(message)
        return Response(response=message, status=500)

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
is_testnet = (not os.getenv("MAINNET") == 'true') if os.getenv(
    "MAINNET") is not None else configurationService.get_configuration("testnet")
tc = TerraClient(mnemonic_key, testnet=is_testnet)
logging.info(f"Connected to {'testnet' if tc.is_testnet() else 'mainnet'} with wallet address {tc.get_address()}")
logging.info(f"Wallet balance: {tc.get_full_balance()}")

PORT_FIELD = "server_port_test" if is_testnet else "server_port"
SERVER_PORT = configurationService.get_configuration(PORT_FIELD)

SSL_CONTEXT = None
SSL_CERTIFICATES_FOLDER = os.getenv("SSL_CERTIFICATES_FOLDER", "./settings/certs/")
if SSL_CERTIFICATES_FOLDER is not None and os.path.exists(SSL_CERTIFICATES_FOLDER) and os.path.exists(
        f"{SSL_CERTIFICATES_FOLDER}/fullchain.pem") and os.path.exists(f"{SSL_CERTIFICATES_FOLDER}/privkey.pem"):
    SSL_CONTEXT = (f"{SSL_CERTIFICATES_FOLDER}/fullchain.pem", f"{SSL_CERTIFICATES_FOLDER}/privkey.pem")

service_port = os.getenv("API_SERVICE_PORT") if os.getenv("API_SERVICE_PORT") is not None else SERVER_PORT

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    # app.run(debug=False, host='0.0.0.0', port=service_port, ssl_context=SSL_CONTEXT)
    app.run(debug=False, host='0.0.0.0', port=service_port)
