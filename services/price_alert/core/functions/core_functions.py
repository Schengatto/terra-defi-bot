# -*- coding: utf-8 -*-
"""
Created on 2022/04/12
@author: schengatto@gmail.com
"""
import logging
import os
import time

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mpl_dates
import mplfinance as mpf
import requests

from core.connectors.prices import get_symbol_prices
from datetime import datetime
from core.utilities import notifications_utils, pdf_utils

logger = logging.getLogger()

OUTPUT_FOLDER = "./resources/"


def get_prices(symbol, provider, period="1mo", interval="8h"):
    df = get_symbol_prices(symbol, period=period, interval=interval, provider=provider)
    df['Date'] = pd.to_datetime(df.index)
    df['Date'] = df['Date'].apply(mpl_dates.date2num)
    has_volumes = 'Volume' in df.columns
    if has_volumes:
        df = df.loc[:, ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
    else:
        df = df.loc[:, ['Date', 'Open', 'High', 'Low', 'Close']]
    return df


def get_daily_performance(symbol, provider):
    p = get_prices(symbol, provider, period="1d")
    initial = p.iloc[0]["Close"]
    current = p.iloc[-1]["Close"]
    return round(((current - initial) / initial) * 100, 2)


def find_min_max(prices):
    tmp = prices.copy(deep=True)
    min_price = tmp["Low"].min()
    max_price = tmp["High"].max()
    return min_price, max_price


# to make sure the new level area does not exist already
def is_far_from_level(value, levels, df):
    ave = np.mean(df['High'] - df['Low'])
    return np.sum([abs(value - level) < ave for _, level in levels]) == 0


# determine bullish fractal
def is_support(df, i):
    cond1 = df['Low'][i] < df['Low'][i - 1]
    cond2 = df['Low'][i] < df['Low'][i + 1]
    cond3 = df['Low'][i + 1] < df['Low'][i + 2]
    cond4 = df['Low'][i - 1] < df['Low'][i - 2]
    return cond1 and cond2 and cond3 and cond4


# determine bearish fractal
def is_resistance(df, i):
    cond1 = df['High'][i] > df['High'][i - 1]
    cond2 = df['High'][i] > df['High'][i + 1]
    cond3 = df['High'][i + 1] > df['High'][i + 2]
    cond4 = df['High'][i - 1] > df['High'][i - 2]
    return cond1 and cond2 and cond3 and cond4


# method 1: fractal candlestick pattern
def find_supports_and_resistances(df):
    levels = []
    supports = []
    resistances = []
    for i in range(2, df.shape[0] - 2):
        if is_support(df, i):
            level = df['Low'][i]
            if is_far_from_level(level, levels, df):
                levels.append((i, level))
                supports.append((i, level))
        elif is_resistance(df, i):
            level = df['High'][i]
            if is_far_from_level(level, levels, df):
                levels.append((i, level))
                resistances.append((i, level))
    return levels, supports, resistances


# for visualization
def plot_all(supports, resistances, df, symbol):
    has_volumes = 'Volume' in df.columns

    levels = []
    colors = []
    for support in supports:
        levels.append(support[1])
        colors.append('b')

    for resistance in resistances:
        levels.append(resistance[1])
        colors.append('y')

    date_format = '%d/%m/%Y'
    mc = mpf.make_marketcolors(base_mpf_style='sas')
    s = mpf.make_mpf_style(marketcolors=mc)
    fig, axis_list = mpf.plot(df,
                              title=f"{symbol}",
                              type='candle',
                              figscale=1.2,
                              datetime_format=date_format,
                              returnfig=True,
                              style=s,
                              tight_layout=True,
                              mav=(3, 6, 9),
                              hlines=dict(hlines=levels, colors=colors, linewidths=1, alpha=0.4))

    if has_volumes:
        price_slots = 30
        bucket_size = (max(df['Close']) - min(df['Close'])) / price_slots
        volume_profile = df['Volume'].groupby(
            df['Close'].apply(lambda x: bucket_size * round(x / bucket_size, 0))).sum()

        vp_bars_needed = 50
        price_slot = (max(df['Close']) - min(df['Close'])) / vp_bars_needed
        volume_profile_y = volume_profile.keys().values
        volume_profile_x = volume_profile.values / 50000000
        volume_profile_axis = fig.add_axes(axis_list[0].get_position())
        volume_profile_axis.set_axis_off()
        volume_profile_axis.set_xlim(right=1.6 * max(volume_profile_x))
        volume_profile_axis.barh(volume_profile_y, volume_profile_x, height=0.75 * price_slot, align='center',
                                 color='cyan', alpha=0.25)

    # mpf.show()
    fig.savefig(f"{OUTPUT_FOLDER}{symbol}.png")
    plt.close()
    return f"{OUTPUT_FOLDER}{symbol}.png"


def create_pdf_report(title, messages=[], images=[]):
    datetime_suffix = datetime.now().strftime("%Y-%m-%d %H:%M")
    date_suffix = datetime.now().strftime("%Y-%m-%d")

    report_filename = f"{title}_{date_suffix}"
    report_title = f"{title} {datetime_suffix}"

    pdf = pdf_utils.create_pdf(report_title)
    last_element_idx = max(len(messages), len(images))

    # signal descriptions
    for idx in range(last_element_idx):
        if len(messages) > idx:
            pdf_utils.add_text_row(pdf, messages[idx])

        if len(images) > idx:
            pdf_utils.add_image(pdf, images[idx])

        if ((idx + 1) % 2) == 0 and (last_element_idx - 1) > idx:
            pdf.add_page()

    pdf_utils.save_pdf(pdf, report_filename)
    notifications_utils.send_telegram_msg(files=[f"{OUTPUT_FOLDER}{report_filename}.pdf"])
    os.remove(f"{OUTPUT_FOLDER}{report_filename}.pdf")


def check_pair_current_swap_info(pair: str, ask_token: str = None, is_testnet=False):
    retries = 3
    base_terra_swap_api_url = "https://api-bombay.terraswap.io" if is_testnet else "https://api.terraswap.io"
    price_check_url = f"{base_terra_swap_api_url}/dashboard/pairs/{pair}"

    while retries > 0:
        try:
            # resp: {token = {"tokenAddress": "terra1<WALLET_ADDRESS>", "symbol": "ANC", "price": "2.0474324831"}}
            data = requests.get(price_check_url).json()
            token1 = data['token0']
            token2 = data['token1']
            retries = 0

            if token1['tokenAddress'] == ask_token:
                return {"token1": token1, "token2": token2,
                        "trade": {"price": token1['price'], "offer": token2['symbol'], "ask": token1['symbol'],
                                  "offer_contract": token2["tokenAddress"], "ask_contract": token1['tokenAddress']},
                        }
            elif token2['tokenAddress'] == ask_token:
                return {"token1": token1, "token2": token2,
                        "trade": {"price": token2['price'], "offer": token1['symbol'], "ask": token2['symbol'],
                                  "offer_contract": token1["tokenAddress"], "ask_contract": token2['tokenAddress']},
                        }
            elif ask_token is None:
                return token1, token2

            else:
                raise Exception(f"Invalid token or pair {pair}")

        except:
            logging.info(f"Error while contacting {price_check_url}")
            retries -= 1
            time.sleep(1)
