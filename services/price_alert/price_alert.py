import sys
import threading
from time import sleep

import schedule
import random

from core.functions.core_functions import *
from core.helpers.init_database_helper import InitDatabaseHelper
from core.repositories.events_repository import EventsRepository, EventType
from core.repositories.orders_repository import OrdersRepository, OrderType
from core.repositories.price_monitors_repository import PriceMonitorsRepository
from core.utilities import pdf_utils
from core.utilities.notifications_utils import send_telegram_msg

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

# init database helpers
initDatabaseHelper = InitDatabaseHelper()

eventsService = EventsRepository()
priceMonitorsService = PriceMonitorsRepository()
ordersService = OrdersRepository()

IS_TELEGRAM_ENABLED = os.getenv("USE_TELEGRAM") == 'true' if os.getenv("USE_TELEGRAM") is not None else False
API_SERVICE_HOST = os.getenv("API_SERVICE_HOST", 'http://localhost')
API_SERVICE_PORT = os.getenv("API_SERVICE_PORT", 5020)
CHECK_DEFI_PRICE = os.getenv("CHECK_DEFI_PRICE") == 'true' if os.getenv("CHECK_DEFI_PRICE") is not None else True
AUTO_BUY = os.getenv("AUTO_BUY") == 'true' if os.getenv("AUTO_BUY") is not None else False
AUTO_BUY_AMOUNT = float(os.getenv("AUTO_BUY_AMOUNT", 10*1000000))
API_TOKEN = os.getenv("API_TOKEN")


def buy_token_and_place_sell(pair_name, asked_token_symbol, price, amount=AUTO_BUY_AMOUNT, reliability=0):
    logger.info(f"Placing BUY and SELL for {pair_name} => {asked_token_symbol} @ {price}")
    messages_to_send = []
    result = ordersService.store_new_order(pair_name=pair_name,
                                           asked_token_symbol=asked_token_symbol,
                                           order_type=OrderType.Buy.value,
                                           price=float(price),
                                           amount=int(amount) if amount is not None else None)

    messages_to_send.append(f"New order placed: {result}")

    # place also SELL order
    SELL_AMOUNT = float(AUTO_BUY_AMOUNT) / float(price) * 0.97

    if reliability == 0:
        sell_price = price * 1.04
    elif reliability > 5:
        sell_price = price * 1.08
    else:
        sell_price = price * 1.06

    result = ordersService.store_new_order(pair_name=pair_name,
                                           asked_token_symbol=asked_token_symbol,
                                           order_type=OrderType.Sell.value,
                                           price=float(sell_price),
                                           amount=int(SELL_AMOUNT))

    messages_to_send.append(f"New order placed: {result}")

    if IS_TELEGRAM_ENABLED:
        msgs = "\n\n".join(messages_to_send)
        send_telegram_msg(messages=[msgs])


def calc_monitor_reliability(prices):
    performance = get_timeframe_performance(prices)
    prices = prices.reset_index()
    worst_daily_perf = 100
    for index, row in prices.iterrows():
        perf = round(((row['Close'] - row['Open']) / row['Open']) * 100, 2)
        if perf < worst_daily_perf:
            worst_daily_perf = perf

    worst_interval = worst_daily_perf / 10
    if performance < 0:
        return 0
    elif performance >= 200:
        return 10 + worst_interval
    elif performance >= 100:
        return 8 + worst_interval
    else:
        return 5 + worst_interval


def update_monitor_reliability():
    monitors = priceMonitorsService.get_price_monitors()
    for monitor in monitors:
        symbol = monitor["price_symbol"]
        provider = monitor["price_provider"]
        prices = get_prices(symbol, provider)
        reliability = calc_monitor_reliability(prices)
        priceMonitorsService.update_price_monitor(monitor['id'], reliability)


def process_monitor(monitor):
    spam_delay = random.randint(0, 2)
    sleep(spam_delay)

    try:
        include_plot = False
        symbol = monitor["price_symbol"]
        provider = monitor["price_provider"]
        reliability = monitor['reliability']

        yearly_prices = get_prices(symbol, provider)

        if reliability == -1:
            reliability = calc_monitor_reliability(yearly_prices)
            priceMonitorsService.update_price_monitor(monitor['id'], reliability)

        BAD_PERFORMANCE_BID_THRESHOLD = (15 - reliability) * -1

        # last 24h performance and weekly performance
        daily_perf, weekly_perf, yearly_performance = get_price_performance(yearly_prices)

        monthly_prices = yearly_prices.tail(30)
        # min and max price for the selected period
        min_price, max_price = find_min_max(monthly_prices)

        low_price = round(min_price * 1.05, 2)
        high_price = round(max_price * 0.95, 2)
        current_price = monthly_prices.iloc[-1]["Close"]
        defi_price = None

        if CHECK_DEFI_PRICE and monitor['terra_pair_mainnet'] is not None:
            resp = requests.get(
                f"{API_SERVICE_HOST}:{API_SERVICE_PORT}/tokens-pairs-price/{monitor['terra_pair_mainnet']}?token_contract={monitor['ask_token_mainnet']}").json()
            defi_price = resp['trade']['price']

        # support and resistances levels
        levels, supports, resistances = find_supports_and_resistances(yearly_prices)

        messages_to_send = []

        # statistics
        message = f"🔎 Current price: {current_price} | last month Min: {min_price} | Lat month Max: {max_price} " \
                  f"| Low Price: {low_price} | High Price: {high_price} | Daily performance: {daily_perf}% " \
                  f"| Weekly performance: {weekly_perf}% | Reliability: {reliability} (0: bad, 5: good, 10: very good)"
        event_name = f"{symbol}_Statistics"
        if not eventsService.is_recently_notified(event_name):
            eventsService.store_event(EventType.PriceStatistics, event_name, symbol, message)
            logging.info(message)
            messages_to_send.append(message)
            include_plot = True

        if daily_perf <= BAD_PERFORMANCE_BID_THRESHOLD:
            message = f"📈 Daily performance {daily_perf}%. Current price: {current_price}"
            event_name = f"{symbol}_D-10"
            if not eventsService.is_recently_notified(event_name):
                try:
                    logging.info(message)
                    messages_to_send.append(message)
                    include_plot = True
                    logger.info(f"{symbol}: AUTOBUY CHECK => {AUTO_BUY and monitor['terra_pair_mainnet'] is not None}")
                    if AUTO_BUY and monitor['terra_pair_mainnet'] is not None:
                        price = defi_price if defi_price is not None else current_price
                        buy_token_and_place_sell(monitor['terra_pair_symbol'], monitor['ask_token_symbol'], float(price))

                except Exception as e:
                    eventsService.store_event(EventType.PriceDailyPerformance, event_name, symbol, message)
                    raise Exception(f"Something went wrong handling daily performance. {e}")

                finally:
                    eventsService.store_event(EventType.PriceDailyPerformance, event_name, symbol, message)

        if daily_perf >= 10:
            message = f"📈 Daily performance {daily_perf}%. Current price: {current_price}"
            event_name = f"{symbol}_D+10"
            if not eventsService.is_recently_notified(event_name):
                eventsService.store_event(EventType.PriceDailyPerformance, event_name, symbol, message)
                logging.info(message)
                messages_to_send.append(message)
                include_plot = True
                # TODO: WIP SELL

        for s in supports:
            if (s[1] * 0.998) >= current_price >= s[1]:
                message = f"⚠️ Current price '{current_price}' is near to a support level: {s[1]}"
                event_name = f"{symbol}_S_{s[1]}"
                if not eventsService.is_recently_notified(event_name):
                    eventsService.store_event(EventType.PriceSupportLevel, event_name, symbol, message)
                    logging.info(message)
                    messages_to_send.append(message)

        for r in resistances:
            if r[1] >= current_price >= (r[1] * 1.002):
                message = f"⚠️ Current price '{current_price}' is near to a resistance level: {r[1]}"
                event_name = f"{symbol}_R_{r[1]}"
                if not eventsService.is_recently_notified(event_name):
                    eventsService.store_event(EventType.PriceResistanceLevel, event_name, symbol, message)
                    logging.info(message)
                    messages_to_send.append(message)

        if current_price <= low_price:
            message = f"↘️ Low price detected. Current price is {current_price}, minimum price last month: {low_price}! Daily performance {daily_perf}%"
            event_name = f"{symbol}_L_{symbol[1]}"
            if not eventsService.is_recently_notified(event_name):
                eventsService.store_event(EventType.PriceIsLow, event_name, symbol, message)
                logging.info(message)
                messages_to_send.append(message)
                # TODO: WIP BUY

        if current_price >= high_price:
            message = f"↗️ High price detected. Current price is {current_price}, maximum price last month: {high_price}! Daily performance {daily_perf}%"
            event_name = f"{symbol}_H_{symbol[1]}"
            if not eventsService.is_recently_notified(event_name):
                eventsService.store_event(EventType.PriceIsHigh, event_name, symbol, message)
                logging.info(message)
                messages_to_send.append(message)
                # TODO: WIP SELL

        if len(messages_to_send) > 0:
            messages_to_send.insert(0, f"{symbol}:")
            msgs = "\n\n".join(messages_to_send)
            if include_plot and False:
                plot_all(supports, resistances, yearly_prices, symbol)
                if IS_TELEGRAM_ENABLED:
                    send_telegram_msg(messages=[msgs], images=[f"./resources/{symbol}.png"])
            elif IS_TELEGRAM_ENABLED:
                send_telegram_msg(messages=[msgs])

    except Exception as e:
        msg = f"❌ There was an error processing {symbol}: {e}"
        logger.error(msg)
        if IS_TELEGRAM_ENABLED and "Temporary failure in name resolution" not in msg and "'NoneType' object" not in msg:
            send_telegram_msg(messages=[msg])


def analyze_symbols():
    monitors = priceMonitorsService.get_price_monitors()
    for monitor in monitors:
        threads = []
        t = threading.Thread(target=process_monitor,
                             args=[monitor])
        threads.append(t)
        t.start()


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
    send_telegram_msg(files=[f"{report_filename}.pdf"])
    os.remove(f"{report_filename}.pdf")


def yearly_range_analysis():
    images = []
    monitors = priceMonitorsService.get_price_monitors()
    logging.info(monitors)
    for monitor in monitors:
        try:
            symbol = monitor["price_symbol"]
            provider = monitor["price_provider"]
            prices = get_prices(symbol, provider, period="1y", interval="1d")
            levels, supports, resistances = find_supports_and_resistances(prices)
            img_file = plot_all(supports, resistances, prices, symbol)
            images.append(img_file)
            logger.info(f"{symbol} processed")

        except Exception as e:
            msg = f"❌ There was an error processing yearly analysis {symbol}: {e}"
            logger.error(msg)
            if IS_TELEGRAM_ENABLED:
                send_telegram_msg(messages=[msg])

    logger.info(images)
    if len(images):
        create_pdf_report("Yearly analysis", images=images)


args = sys.argv[1:]
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
logger = logging.getLogger()

logger.info("IS_TELEGRAM_ENABLED: ", IS_TELEGRAM_ENABLED)
logger.info("CHECK_DEFI_PRICE", CHECK_DEFI_PRICE)
logger.info("AUTOBUY: ", AUTO_BUY)
logger.info("AUTOBUY: ", AUTO_BUY_AMOUNT)

update_monitor_reliability()
analyze_symbols()

# next calls are scheduled
schedule.every(30).seconds.do(analyze_symbols)
schedule.every().day.at("08:00").do(yearly_range_analysis)
schedule.every().day.at("20:00").do(yearly_range_analysis)
schedule.every().day.at("01:00:30").do(update_monitor_reliability)
while True:
    # Checks whether a scheduled task
    # is pending to run or not
    schedule.run_pending()
    time.sleep(10)
