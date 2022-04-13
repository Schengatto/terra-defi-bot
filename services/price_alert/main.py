import sys
import logging
import os
import schedule
import time
import json
import pandas as pd
import numpy as np
import matplotlib.dates as mpl_dates
import matplotlib.pyplot as plt

from datetime import datetime
from dateutil.relativedelta import relativedelta
from mplfinance.original_flavor import candlestick_ohlc
from prices import get_symbol_prices
from lib import utils, pdf_utils


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
    min_price = tmp["Low"].min();
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
    return (cond1 and cond2 and cond3 and cond4)


# determine bearish fractal
def is_resistance(df, i):
    cond1 = df['High'][i] > df['High'][i - 1]
    cond2 = df['High'][i] > df['High'][i + 1]
    cond3 = df['High'][i + 1] > df['High'][i + 2]
    cond4 = df['High'][i - 1] > df['High'][i - 2]
    return (cond1 and cond2 and cond3 and cond4)


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

    plt.savefig(f"{symbol}.png")
    plt.close()
    return f"{symbol}.png"


def get_stored_notification():
    if not os.path.exists('notifications.bot'):
        file1 = open("notifications.bot", "w")
        file1.write("{}")
        file1.close()

    file1 = open("notifications.bot", "r+")
    stored_notifications = json.loads(file1.readline())
    return stored_notifications


def store_notification(key):
    now = datetime.now()
    stored_notifications = get_stored_notification()
    stored_notifications[key] = datetime.timestamp(now)
    file1 = open("notifications.bot", "w")
    file1.write(json.dumps(stored_notifications))
    file1.close()


def already_notified(key, minutes=60):
    try:
        stored_notifications = get_stored_notification()
        msg_sent_time = datetime.fromtimestamp(stored_notifications[key])
        is_already_notified = msg_sent_time > (datetime.now() - relativedelta(minutes=minutes))
        result = True if is_already_notified else False
    except:
        result = False

    if result:
        logging.info(f"{key} already notified recently: {msg_sent_time}")

    return result


def analyze_symbols():
    for asset in symbols:
        try:
            symbol = asset.split("|")[0]
            provider = asset.split("|")[1]

            prices = get_prices(symbol, provider)

            # last 24h performance
            daily_performance = get_daily_performance(symbol, provider)

            # min and max price for the selected period
            min_price, max_price = find_min_max(prices)
            low_price =  round(min_price * 1.05, 2)
            high_price = round(max_price * 0.95, 2)
            current_price = prices.iloc[-1]["Close"]

            # support and resistances levels
            levels, supports, resistances = find_supports_and_resistances(prices)

            messages_to_send = []

            # statistics
            message = f"🔎 Current price: {current_price} | Min: {min_price} | Max: {max_price} " \
                      f"| Low: {low_price} | High: {high_price} | Perf: {daily_performance}%"
            event_key = f"{symbol}_Statistics"
            if not already_notified(event_key, minutes=720):
                store_notification(event_key)
                logging.info(message)
                messages_to_send.append(message)

            if daily_performance >= 10 or daily_performance <= -10:
                message = f"📈 Daily performance {daily_performance}%. Current price: '{current_price}'"
                event_key = f"{symbol}_D"
                if not already_notified(event_key, minutes=480):
                    store_notification(event_key)
                    logging.info(message)
                    messages_to_send.append(message)

            for s in supports:
                if (s[1] * 0.998) >= current_price >= s[1]:
                    message = f"⚠️ Current price '{current_price}' is near to a support level: {s[1]}"
                    event_key = f"{symbol}_S_{s[1]}"
                    if not already_notified(event_key):
                        store_notification(event_key)
                        logging.info(message)
                        messages_to_send.append(message)

            for r in resistances:
                if r[1] >= current_price >= (r[1] * 1.002):
                    message = f"⚠️ Current price '{current_price}' is near to a resistance level: {r[1]}"
                    event_key = f"{symbol}_R_{r[1]}"
                    if not already_notified(event_key):
                        store_notification(event_key)
                        logging.info(message)
                        messages_to_send.append(message)

            if current_price <= low_price:
                message = f"↘️ Low price detected. Current price is {current_price}, minimum price last month: {low_price}! Daily performance {daily_performance}%"
                event_key = f"{symbol}_L_{symbol[1]}"
                if not already_notified(event_key):
                    store_notification(event_key)
                    logging.info(message)
                    messages_to_send.append(message)

            if current_price >= high_price:
                message = f"↗️ High price detected. Current price is {current_price}, maximum price last month: {high_price}! Daily performance {daily_performance}%"
                event_key = f"{symbol}_H_{symbol[1]}"
                if not already_notified(event_key):
                    store_notification(event_key)
                    logging.info(message)
                    messages_to_send.append(message)

            if len(messages_to_send) > 0:
                messages_to_send.insert(0, f"{symbol}:")
                msgs = "\n\n".join(messages_to_send)
                plot_all(supports, resistances, prices, symbol, provider)
                utils.send_telegram_msg(messages=[msgs], images=[f"./{symbol}.png"])

        except Exception as e:
            msg = f"❌ There was an error processing {asset}: {e}"
            logger.error(msg)
            utils.send_telegram_msg(messages=[msg])


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
    utils.send_telegram_msg(files=[f"{report_filename}.pdf"])
    os.remove(f"{report_filename}.pdf")


def yearly_range_analysis():
    images = []
    for asset in symbols:
        try:
            symbol = asset.split("|")[0]
            provider = asset.split("|")[1]
            prices = get_prices(symbol, provider, period="1y", interval="1d")
            levels, supports, resistances = find_supports_and_resistances(prices)
            img_file = plot_all(supports, resistances, prices, symbol, provider)
            images.append(img_file)
            logger.info(f"{symbol} processed")

        except Exception as e:
            msg = f"❌ There was an error processing yearly analysis {asset}: {e}"
            logger.error(msg)
            utils.send_telegram_msg(messages=[msg])

    logger.info(images)
    if len(images):
        create_pdf_report("Yearly analysis", images=images)


args = sys.argv[1:]
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
logger = logging.getLogger()

symbols = args[0].split(",") if len(args) > 0 else "LUNAUSDT|binance_spot," \
                                                   "ANCUSDT|binance_spot," \
                                                   "MIRUSDT|binance_spot," \
                                                   "crypto-com-chain|coingecko," \
                                                   "mmfinance|coingecko," \
                                                   "mad-meerkat-optimizer|coingecko," \
                                                   "ETHUSDT|binance_spot," \
                                                   "BTCUSDT|binance_spot".split(",")
logger.info(symbols)

# execute_logics
analyze_symbols()

# next calls are scheduled
schedule.every(1).minute.do(analyze_symbols)
schedule.every(1).day.do(yearly_range_analysis)
while True:
    # Checks whether a scheduled task
    # is pending to run or not
    schedule.run_pending()
    time.sleep(10)
