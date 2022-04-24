import logging
import sys
import time

import schedule

from core.repositories.price_monitors_repository import PriceMonitorsRepository
from core.utilities import pdf_utils
from core.helpers.init_database_helper import InitDatabaseHelper
from core.utilities.notifications_utils import send_telegram_msg
from core.repositories.events_repository import EventsRepository, EventType
from core.functions.core_functions import *

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

# init database helpers
initDatabaseHelper = InitDatabaseHelper()

eventsService = EventsRepository()
priceMonitorsService = PriceMonitorsRepository()


CHECK_DEFI_PRICE = os.getenv("CHECK_DEFI_PRICE", False) == 'true'
PLACE_ORDERS = os.getenv("PLACE_ORDERS", False) == 'true'
IS_TELEGRAM_ENABLED = os.getenv("USE_TELEGRAM", False) == 'true'
API_SERVICE_HOST = os.getenv("API_SERVICE_HOST", 'localhost')
API_SERVICE_PORT = os.getenv("API_SERVICE_PORT", 5020)

def analyze_symbols():
    monitors = priceMonitorsService.get_price_monitors()
    for monitor in monitors:
        try:
            include_plot = False
            symbol = monitor["price_symbol"]
            provider = monitor["price_provider"]

            prices = get_prices(symbol, provider)

            # last 24h performance
            daily_performance = get_daily_performance(symbol, provider)

            # min and max price for the selected period
            min_price, max_price = find_min_max(prices)
            low_price = round(min_price * 1.05, 2)
            high_price = round(max_price * 0.95, 2)
            current_price = prices.iloc[-1]["Close"]

            if CHECK_DEFI_PRICE:
                resp = requests.get(f"http://{API_SERVICE_HOST}:{API_SERVICE_PORT}/tokens-pairs-price/{monitor['terra_pair_mainnet']}?token_contract={monitor['ask_token_mainnet']}").json()
                print(current_price, resp['trade']['price'])

            # support and resistances levels
            levels, supports, resistances = find_supports_and_resistances(prices)

            messages_to_send = []

            # statistics
            message = f"🔎 Current price: {current_price} | Min: {min_price} | Max: {max_price} " \
                      f"| Low: {low_price} | High: {high_price} | Daily performance: {daily_performance}%"
            event_name = f"{symbol}_Statistics"
            if not eventsService.is_recently_notified(event_name):
                eventsService.store_event(EventType.PriceStatistics, event_name, message)
                logging.info(message)
                messages_to_send.append(message)
                include_plot = True

            if daily_performance >= 10 or daily_performance <= -10:
                message = f"📈 Daily performance {daily_performance}%. Current price: {current_price}"
                event_name = f"{symbol}_D"
                if not eventsService.is_recently_notified(event_name):
                    eventsService.store_event(EventType.PriceDailyPerformance, event_name, message)
                    logging.info(message)
                    messages_to_send.append(message)
                    include_plot = True

            for s in supports:
                if (s[1] * 0.998) >= current_price >= s[1]:
                    message = f"⚠️ Current price '{current_price}' is near to a support level: {s[1]}"
                    event_name = f"{symbol}_S_{s[1]}"
                    if not eventsService.is_recently_notified(event_name):
                        eventsService.store_event(EventType.PriceSupportLevel, event_name, message)
                        logging.info(message)
                        messages_to_send.append(message)

            for r in resistances:
                if r[1] >= current_price >= (r[1] * 1.002):
                    message = f"⚠️ Current price '{current_price}' is near to a resistance level: {r[1]}"
                    event_name = f"{symbol}_R_{r[1]}"
                    if not eventsService.is_recently_notified(event_name):
                        eventsService.store_event(EventType.PriceResistanceLevel, event_name, message)
                        logging.info(message)
                        messages_to_send.append(message)

            if current_price <= low_price:
                message = f"↘️ Low price detected. Current price is {current_price}, minimum price last month: {low_price}! Daily performance {daily_performance}%"
                event_name = f"{symbol}_L_{symbol[1]}"
                if not eventsService.is_recently_notified(event_name):
                    eventsService.store_event(EventType.PriceIsLow, event_name, message)
                    logging.info(message)
                    messages_to_send.append(message)
                    # TODO: WIP
                    if PLACE_ORDERS:
                        print(f"check: {monitor['terra_pair_symbol']} {monitor['ask_token_symbol']} {current_price} {EventType.TradeBuy.value}")

            if current_price >= high_price:
                message = f"↗️ High price detected. Current price is {current_price}, maximum price last month: {high_price}! Daily performance {daily_performance}%"
                event_name = f"{symbol}_H_{symbol[1]}"
                if not eventsService.is_recently_notified(event_name):
                    eventsService.store_event(EventType.PriceIsHigh, event_name, message)
                    logging.info(message)
                    messages_to_send.append(message)
                    # TODO: WIP
                    if PLACE_ORDERS:
                        print(
                            f"check: {monitor['terra_pair_symbol']} {monitor['ask_token_symbol']} {current_price} {EventType.TradeSell.value}")

            if len(messages_to_send) > 0:
                messages_to_send.insert(0, f"{symbol}:")
                msgs = "\n\n".join(messages_to_send)
                if include_plot:
                    plot_all(supports, resistances, prices, symbol)
                    if IS_TELEGRAM_ENABLED:
                        send_telegram_msg(messages=[msgs], images=[f"./resources/{symbol}.png"])
                elif IS_TELEGRAM_ENABLED:
                    send_telegram_msg(messages=[msgs])

        except Exception as e:
            msg = f"❌ There was an error processing {symbol}: {e}"
            logger.error(msg)
            if IS_TELEGRAM_ENABLED:
                send_telegram_msg(messages=[msg])


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

analyze_symbols()

# next calls are scheduled
schedule.every(1).minute.do(analyze_symbols)
schedule.every().day.at("08:00").do(yearly_range_analysis)
while True:
    # Checks whether a scheduled task
    # is pending to run or not
    schedule.run_pending()
    time.sleep(10)
