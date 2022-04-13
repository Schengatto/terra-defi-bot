# -*- coding: utf-8 -*-
"""
Created on 2022/04/12
@author: schengatto@gmail.com
"""
import logging
import requests
import json, time, urllib, re, base64
from urllib.request import Request

from terra_sdk.client.lcd import LCDClient
from terra_sdk.core.wasm import MsgExecuteContract
from terra_sdk.key.mnemonic import MnemonicKey
from terra_sdk.core.market import MsgSwap
from terra_sdk.core.coins import Coins
from terra_sdk.core.coins import Coin
from terra_sdk.core.fee import Fee
from terra_sdk.client.lcd.api.tx import CreateTxOptions

logger = logging.getLogger()

# Extra doc: https://githubhot.com/repo/terra-money/terra.py/issues/52


def cw20_tokens(testnet=True):
    if testnet:
        return {
            'MIR': {"pair_address": "terra1cz6qp8lfwht83fh9xm9n94kj04qc35ulga5dl0",
                    "contract": "terra10llyp6v3j3her8u3ce66ragytu45kcmd9asj3u"},
            'ANC': {"pair_address": "terra1wfvczps2865j0awnurk9m04u7wdmd6qv3fdnvz",
                    "contract": "terra1747mad58h0w4y589y3sk84r5efqdev9q4r02pc"},
        }
    else:
        return {
            'MIR': {"pair_address": "terra1amv303y8kzxuegvurh0gug2xe9wkgj65enq2ux",
                    "contract": "terra15gwkyepfc6xgca5t5zefzwy42uts8l2m4g40k6"},
            'ANC': {"pair_address": "terra1gm5p3ner9x9xpwugn9sp6gvhd0lwrtkyrecdn3",
                    "contract": "terra1<WALLET_ADDRESS>"},
        }


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
        return "https://finder.terra.money/testnet/tx/" if self._isTestnet else "https://finder.terra.money/mainnet/tx/"

    def get_full_balance(self):
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
        for coin in ["ANC", "MIR", "bLuna"]:
            try:
                balance = self.get_coin_balance(coin)
                b[coin] = int(balance["result"]["balance"])
            except:
                logger.debug(f"{coin}: 0")
        return b

    def get_coin_balance(self, coin):
        if coin not in ["ANC", "MIR"]:
            raise Exception("Invalid coin. Valid value: ANC | MIR")

        query_msg = '{"balance":{"address":"' + self.get_address() + '"}}'
        response = requests.get(
            f"{get_lcd_address(self._isTestnet)[0]}/wasm/contracts/{cw20_tokens(self._isTestnet)[coin]['contract']}/store",
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

    def swap(self,
             from_coin=None,
             to_coin=None,
             amount_to_swap=None):

        if from_coin is None:
            raise Exception("Provide a valid value to from_coin")

        if to_coin is None:
            raise Exception("Provide a valid value to to_coin")

        if amount_to_swap is None:
            raise Exception("Provide a valid value to amount_to_swap")

        logging.info(f"Swap: {amount_to_swap} {from_coin} to {to_coin}")
        address = self.get_address()

        coin = Coin(from_coin, f"{amount_to_swap}").to_data()
        coins = Coins.from_data([coin])

        # NATIVE --> NATIVE
        if from_coin == 'uluna' or to_coin == 'uluna':
            swap_msg = MsgSwap(address, Coin(from_coin, amount_to_swap), to_coin)

        # UST --> CW20:
        elif from_coin == 'uusd':
            if to_coin not in ["ANC", "MIR", "bLuna"]:
                raise Exception("Provide a valid value to to_asset: ANC | MIR | bLuna")

            swap_msg = MsgExecuteContract(
                sender=address,
                contract=cw20_tokens(self._isTestnet)[to_coin]['pair_address'],
                execute_msg={
                    "swap": {
                        "max_spread": "0.01",
                        "offer_asset": {
                            "info": {
                                "native_token": {
                                    "denom": from_coin,
                                },
                            },
                            "amount": f"{amount_to_swap}",
                        },
                    },
                },
                coins=coins,
            )

        # CW20 --> UST:
        elif to_coin == 'uusd':
            swap_msg = MsgExecuteContract(
                sender=address,
                contract=cw20_tokens(self._isTestnet)[from_coin]['contract'],
                execute_msg={
                    "send": {
                        "contract": cw20_tokens(self._isTestnet)[from_coin]['pair_address'],
                        "amount": f"{amount_to_swap}",
                        "msg": to_base64_string({
                            "swap": {
                                "offer_asset": {
                                    "info": {
                                        "token": {
                                            "contract_addr": "uusd"
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

        swap_tx = CreateTxOptions(msgs=[swap_msg], gas_prices=live_gas_prices, gas_adjustment='1.5',
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

        logger.info(tx)
        return result.txhash

