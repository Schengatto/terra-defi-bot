# -*- coding: utf-8 -*-
"""
Created on 2022/04/12
@author: schengatto@gmail.com
"""
import logging

from datetime import datetime
from enum import Enum

from dateutil.relativedelta import relativedelta
from core.connectors.postgresql_connector import PostgresSqlConnector

logger = logging.getLogger()
EVENTS_FILE_PATH = "./resources/events.bot"
EVENTS_TABLE = "events"


class EventType(Enum):
    PriceStatistics = "PRICE_STATISTICS"
    PriceDailyPerformance = "PRICE_DAILY_PERFORMANCE"
    PriceSupportLevel = "PRICE_SUPPORT_LEVEL"
    PriceResistanceLevel = "PRICE_RESISTANCE_LEVEL"
    PriceIsLow = "PRICE_IS_LOW"
    PriceIsHigh = "PRICE_IS_HIGH"
    PriceWarning = "ORDER_PRICE_WARN"
    TradeBuy = "ORDER_TRADE_BUY"
    TradeSell = "ORDER_TRADE_SELL"
    Error = "ERROR"


def map_to_entity(raw_row):
    return {
        "id": raw_row[0],
        "type": raw_row[1],
        "name": raw_row[2],
        "message": raw_row[3],
        "lock_duration": int(raw_row[4]) if raw_row[4] is not None else None,
        "updated": raw_row[5]
    }


class EventsRepository:
    def __init__(self):
        self._events = self.get_events()
        # TODO automatically create table + populate it

    def get_events(self):
        read_ = f'''SELECT
                        e.id,
                        et.name,
                        e.name,
                        e.message,
                        et.lock_duration,
                        e.updated
                    FROM {EVENTS_TABLE} e
                        join event_types et on e.type = et.id
                    ORDER BY updated DESC'''
        psql = PostgresSqlConnector()
        return psql.read(read_, mapping=map_to_entity)

    def find_events_by_name(self, event_name: str):
        read_ = f'''SELECT
                        e.id,
                        et.name,
                        e.name,
                        e.message,
                        et.lock_duration,
                        e.updated
                    FROM {EVENTS_TABLE} e
                        join event_types et on e.type = et.id
                    WHERE e.name = '{event_name}'
                    ORDER BY updated DESC;'''
        psql = PostgresSqlConnector()
        return psql.read(read_, mapping=map_to_entity)

    def find_event_by_id(self, event_id: str):
        read_ = f'''SELECT
                           e.id,
                           et.name,
                           e.name,
                           e.message,
                           et.lock_duration,
                           e.updated
                       FROM {EVENTS_TABLE} e
                           join event_types et on e.type = et.id
                       WHERE e.id::text = '{event_id}
                       ORDER BY updated DESC';'''
        psql = PostgresSqlConnector()
        return psql.read(read_, mapping=map_to_entity)

    def store_event(self, event_type: EventType, name: str, message: str):
        insert_ = f'''INSERT
                    INTO {EVENTS_TABLE} (type, name, message)
                    VALUES((select id from event_types where name = '{event_type.value}'), '{name}', '{message}');
                    '''
        psql = PostgresSqlConnector()
        psql.insert(insert_)

        read_ = f'''SELECT id from {EVENTS_TABLE} ORDER BY updated DESC LIMIT 1'''
        return psql.read(read_)[0][0]

    def remove_event(self, event_id: str):
        delete_ = f"DELETE FROM {EVENTS_TABLE} WHERE id::text = '{event_id}';"
        psql = PostgresSqlConnector()
        psql.delete(delete_)
        return self.find_events_by_name(event_id) is None

    def is_recently_notified(self, event_name: str, minutes: int = None):
        try:
            result = False
            events = self.find_events_by_name(event_name)
            if len(events) > 0:
                event = events[0]
                msg_sent_time = event['updated']
                if minutes is not None:
                    result = msg_sent_time > (datetime.now() - relativedelta(minutes=minutes))
                elif event['lock_duration'] is not None:
                    result = msg_sent_time > (datetime.now() - relativedelta(minutes=event['lock_duration']))

        except:
            logging.error(f"An error occurred while checking if the event {event_name} was recently notified")
            result = False

        if result:
            logging.info(f"{event_name} was already notified recently: {msg_sent_time}")

        return result
