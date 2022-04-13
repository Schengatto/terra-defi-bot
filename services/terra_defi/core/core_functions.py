# -*- coding: utf-8 -*-
"""
Created on 2022/04/12
@author: schengatto@gmail.com
"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mpl_dates

from mplfinance.original_flavor import candlestick_ohlc
from lib.prices import get_symbol_prices
from datetime import datetime
from lib import utils, pdf_utils

OUTPUT_FOLDER = "./resources/"


def get_prices(symbol, provider, period="1mo", interval="8h"):
    df = get_symbol_prices(symbol, period=period, interval=interval, provider=provider)
    df['Date'] = pd.to_datetime(df.index)
    df['Date'] = df['Date'].apply(mpl_dates.date2num)
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
def plot_all(supports, resistances, df, symbol, provider):
    width = 0.22 if provider == "binance_spot" else 0.11

    fig, ax = plt.subplots(figsize=(16, 9))
    ax.twinx()
    candlestick_ohlc(ax, df.values, width=width, colorup='green',
                     colordown='red', alpha=0.8)
    date_format = mpl_dates.DateFormatter('%d %b %Y')
    ax.xaxis.set_major_formatter(date_format)
    for support in supports:
        plt.hlines(support[1], xmin=df['Date'][support[0]], xmax=
        max(df['Date']), colors='blue', linestyle='--', label=support[1])

    for resistance in resistances:
        plt.hlines(resistance[1], xmin=df['Date'][resistance[0]], xmax=
        max(df['Date']), colors='orange', linestyle='--', label=resistance[1])

    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.title(f"{symbol} | {provider}")
    plt.grid(True)

    plt.savefig(f"{OUTPUT_FOLDER}{symbol}.png")
    plt.close()
    return f"{symbol}.png"


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

        if ((idx + 1) % 2) == 0 and last_element_idx > idx:
            pdf.add_page()

    pdf_utils.save_pdf(pdf, report_filename)
    utils.send_telegram_msg(files=[f"{OUTPUT_FOLDER}{report_filename}.pdf"])
    os.remove(f"{OUTPUT_FOLDER}{report_filename}.pdf")
