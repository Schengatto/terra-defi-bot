import pandas as pd

from pycoingecko import CoinGeckoAPI
from datetime import datetime

cg = CoinGeckoAPI()

#lista = cg.get_coins_list()
#print(lista)

"mad-meerkat-optimizer"

#x = cg.get_price("mad-meerkat-optimizer", "")
#print(x)

prices = cg.get_coin_ohlc_by_id("mad-meerkat-optimizer", "usd", 30)
print(prices)

df = pd.DataFrame(prices, columns=['Date', 'Open', 'High', 'Low', "Close"])
# datetime.fromtimestamp(timestamp)
#apply(lambda x: x.date())
#df['date'] = pd.to_datetime(df['Date'])

df['date'] = df['Date'].apply(lambda x: datetime.fromtimestamp(x / 1e3))
# df['date'] = df['date'].dt.tz_localize('UTC')
df.set_index('date', inplace=True)

# df = pd.json_normalize(prices, meta=['school_name', 'class'])
print(df)