# -*- coding: utf-8 -*-
"""
Created on 2022/04/12
@author: schengatto@gmail.com
"""
import logging
import requests
import json, time, urllib, base64
from urllib.request import Request

from terra_sdk.client.lcd import LCDClient
from terra_sdk.core.wasm import MsgExecuteContract
from terra_sdk.key.mnemonic import MnemonicKey
from terra_sdk.core.market import MsgSwap
from terra_sdk.core.coins import Coins
from terra_sdk.core.coins import Coin
from terra_sdk.core.fee import Fee
from terra_sdk.client.lcd.api.tx import CreateTxOptions

from core.functions.core_functions import check_pair_current_swap_info
from core.repositories.terra_tokens_repository import TerraTokensRepository

terra_coins_repository = TerraTokensRepository()

logger = logging.getLogger()

TERRA_NATIVE_COINS = ['uaud', 'ucad', 'uchf', 'ucny', 'udkk', 'ueur', 'ugbp', 'uhkd', 'uidr', 'uinr', 'ujpy', 'ukrw',
                      'umnt', 'umyr', 'unok', 'uphp', 'usdr', 'usek', 'usgd', 'uthb', 'utwd', 'uusd', 'uluna']


# Extra doc: https://githubhot.com/repo/terra-money/terra.py/issues/52

def get_lcd_address(testnet=True):
    if testnet:
        return "https://bombay-lcd.terra.dev", "bombay-12"
    else:
        return "https://lcd.terra.dev", "columbus-5"


def to_base64_string(data: dict) -> str:
    data_string = json.dumps(data)
    return base64.b64encode(data_string.encode("utf-8")).decode("utf-8")


# Doc: https://algotrading101.com/learn/terra-luna-python-guide/
class TerraClient:
    def __init__(self, mnemonic_key, testnet=True):
        self._isTestnet = testnet
        self._mk = MnemonicKey(mnemonic_key)
        lcd_address = get_lcd_address(testnet)
        self._terra = LCDClient(lcd_address[0], lcd_address[1])
        self._wallet = self._terra.wallet(self._mk)
        self._available_tokens = self.__load_available_coins()
        logger.info("Terra Client successfully initialized")

    def close_connection(self):
        return self._terra.session.close()

    def is_testnet(self):
        return self._isTestnet

    def get_address(self):
        return self._mk.acc_address

    def get_private_key(self):
        return self._mk.private_key

    def get_wallet(self):
        return self._terra()

    def get_balance(self):
        return self._terra.bank.balance(self.get_address())[0]

    def terra_finder_url(self):
        return "https://terrasco.pe/testnet/tx/" if self._isTestnet else "https://terrasco.pe/mainnet/tx/"

    def __load_available_coins(self):
        return list(map(lambda t: t['testnet_contract'] if self._isTestnet else t['mainnet_contract'],
                        terra_coins_repository.get_tokens()))

    def get_full_balance(self, tokens=[]):
        balance = self.get_balance()

        # native
        coins = self.get_native_coins()
        coins.append("uluna")
        b = {}
        for c in coins:
            try:
                b[c] = balance[c].amount
            except:
                if c in ['uusd', 'uluna']:
                    b[c] = 0
                logger.debug(f"{c}: 0")

        # CW20
        for token_contract in tokens:
            try:
                balance = self.get_coin_balance(token_contract)
                b[token_contract] = int(balance["result"]["balance"])
            except:
                logger.debug(f"{token_contract}: 0")
        return b

    def get_coin_balance(self, token_contract):
        if token_contract not in self._available_tokens:
            raise Exception(f"Invalid coin. Valid value: {', '.join(self._available_tokens)})")

        query_msg = '{"balance":{"address":"' + self.get_address() + '"}}'
        response = requests.get(
            f"{get_lcd_address(self._isTestnet)[0]}/wasm/contracts/{token_contract}/store",
            params={"query_msg": query_msg},
        ).json()
        return response

    def get_native_coins(self):
        return self._terra.oracle.active_denoms()

    def swap_native(self, from_asset="uluna", to_asset="uusd", amount_to_swap=None, fee=Fee(200000, "120000uluna")):
        if amount_to_swap is None:
            raise Exception("Provide a valid value to amount_to_swap")

        logging.info(f"Swap: {amount_to_swap} {from_asset} to {to_asset}")
        address = self.get_address()
        swap_msg = MsgSwap(address, Coin(from_asset, amount_to_swap), to_asset)
        swap_tx = CreateTxOptions(msgs=[swap_msg], fee=fee)
        tx = self._wallet.create_and_sign_tx(swap_tx)
        result = self._terra.tx.broadcast(tx)
        return result.txhash

    def current_swap_price(self,
                           pair_contract: str = None,
                           ask_token_contract: str = None):
        if pair_contract is None:
            raise Exception("Provide a valid value to from_coin")

        if ask_token_contract is None:
            raise Exception("Provide a valid value to to_coin")

        return check_pair_current_swap_info(pair_contract, ask_token_contract)['trade']

    def swap(self,
             pair_contract: str = None,
             offer_token_contract: str = None,
             ask_token_contract: str = None,
             amount_to_swap: str = None):

        if pair_contract is None:
            raise Exception("Provide a valid value to pair_contract")

        if ask_token_contract is None:
            raise Exception("Provide a valid value to ask_token_contract")

        if offer_token_contract is None:
            raise Exception("Provide a valid value to offer_token_contract")

        if amount_to_swap is None:
            raise Exception("Provide a valid value to amount_to_swap")

        logging.info(f"Swap: {amount_to_swap} {offer_token_contract} to {ask_token_contract}")
        address = self.get_address()

        coin = Coin(offer_token_contract, f"{amount_to_swap}").to_data()
        logging.basicConfig(
            format='%(asctime)s %(levelname)-8s %(message)s',
            level=logging.INFO,
            datefmt='%Y-%m-%d %H:%M:%S')
        coins = Coins.from_data([coin])

        # NATIVE --> NATIVE (check if Both token are native)
        if offer_token_contract in TERRA_NATIVE_COINS and ask_token_contract in TERRA_NATIVE_COINS:
            swap_msg = MsgSwap(address, Coin(offer_token_contract, amount_to_swap), ask_token_contract)

        # UST --> CW20:
        elif offer_token_contract in TERRA_NATIVE_COINS:
            if ask_token_contract not in self._available_tokens:
                raise Exception(f"Provide a valid value to to_asset: {', '.join(self._available_tokens)}")

            swap_msg = MsgExecuteContract(
                sender=address,
                contract=pair_contract,
                execute_msg={
                    "swap": {
                        "max_spread": "0.01",
                        "offer_asset": {
                            "info": {
                                "native_token": {
                                    "denom": offer_token_contract,
                                },
                            },
                            "amount": f"{amount_to_swap}",
                        },
                    },
                },
                coins=coins,
            )

        # CW20 --> UST:
        elif ask_token_contract in TERRA_NATIVE_COINS:
            if offer_token_contract not in self._available_tokens:
                raise Exception(f"Provide a valid value to to_asset: {', '.join(self._available_tokens)}")

            swap_msg = MsgExecuteContract(
                sender=address,
                contract=offer_token_contract,
                execute_msg={
                    "send": {
                        "contract": pair_contract,
                        "amount": f"{amount_to_swap}",
                        "msg": to_base64_string({
                            "swap": {
                                "offer_asset": {
                                    "info": {
                                        "token": {
                                            "contract_addr": ask_token_contract
                                        }
                                    },
                                    "amount": f"{amount_to_swap}"
                                },
                            }
                        })
                    }
                }
            )

        url_request = Request("https://fcd.terra.dev/v1/txs/gas_prices", headers={"User-Agent": "Mozilla/5.0"})
        live_gas_prices = json.loads(urllib.request.urlopen(url_request).read().decode())

        # TODO make fee_denoms a param
        swap_tx = CreateTxOptions(msgs=[swap_msg], gas_prices=live_gas_prices, gas_adjustment='1.2',
                                  fee_denoms=['uusd'])
        tx = self._wallet.create_and_sign_tx(swap_tx)
        tx_error = True
        delay = 1
        count = 0
        while tx_error and count < 100:
            result = self._terra.tx.broadcast(tx)
            logging.info(result)
            logging.info(result.gas_used)
            tx_error = result.is_tx_error()
            count = count + 1
            if tx_error:
                logging.debug(f"\nCount: {count}")
                time.sleep(delay)
                if count <= 5:
                    delay = (delay * 2)

        if tx_error:
            logging.error(f"\nError: {tx_error}")
            return f"{tx_error}"

        price = 0
        amount_received = 0
        try:
            if 'wasm' in result.logs[0].events_by_type:
                amount_received = float(result.logs[0].events_by_type['wasm']['amount'][0])
                price = float(amount_to_swap) / amount_received
            elif 'coin_received' in result.logs[0].events_by_type:
                amount_received = float(result.logs[0].events_by_type['coin_received']['amount'][1].replace(ask_token_contract, ''))
                price = float(amount_to_swap) / amount_received
        except:
            logger.error("Unable to get the amount value from the transaction event 'wasm'")

        logger.info(tx)
        return result.txhash, round(price, 4), amount_received
