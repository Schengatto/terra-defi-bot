from terra_sdk.client.lcd import LCDClient
from terra_sdk.key.mnemonic import MnemonicKey
from terra_sdk.core.market import MsgSwap
from terra_sdk.core.coins import Coins
from terra_sdk.core.coins import Coin
from terra_sdk.core.wasm import MsgExecuteContract
from terra_sdk.core.fee import Fee
from terra_sdk.client.lcd.api.tx import CreateTxOptions

# Doc: https://algotrading101.com/learn/terra-luna-python-guide/

use_testnet = True
if use_testnet:
    terra = LCDClient("https://bombay-lcd.terra.dev", "bombay-12")
else:
    terra = LCDClient("https://lcd.terra.dev", "columbus-5")


# Add more moeny here: https://faucet.terra.money/
mk = MnemonicKey(
    "<WALLET_MNEMONIC>")

address = mk.acc_address
private_key = mk.private_key
wallet = terra.wallet(mk)

balance = terra.bank.balance(address)[0]

print("Wallet info:")
print(f"address: {address}")
print(f"balance: {balance}")

# Available tokens
# print(terra.oracle.active_denoms())

# print(balance[0]['uluna'].amount)

do_swap = True

if do_swap:
    # Swap 5% Luna to UST
    amount_to_swap = int(balance['uluna'].amount * 0.02)
    print(f"Swap: {amount_to_swap} uluna to UST")
    swap_msg = MsgSwap(address, Coin("uluna", amount_to_swap),  "uusd")
    fee = Fee(200000, "120000uluna")
    swap_tx = CreateTxOptions(msgs=[swap_msg], fee=fee)
    tx = wallet.create_and_sign_tx(swap_tx)
    result = terra.tx.broadcast(tx)
    tx_hash = result.txhash

    print(f"tx hash: {tx_hash}")
    print(result)

# https://docs.mirror.finance/networks#testnet-1
mir_ust_pair_address = "terra18qpjm4zkvqnpjpw0zn0tdr8gdzvt8au35v45xf"
mir_contract = "terra10llyp6v3j3her8u3ce66ragytu45kcmd9asj3u"