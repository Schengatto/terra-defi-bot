# -*- coding: utf-8 -*-
"""
Created on 2022/04/12
@author: schengatto@gmail.com
"""
import json
import os
import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta

EVENTS_FILE_PATH = "./resources/events.bot"


def init_service():
    if not os.path.exists(EVENTS_FILE_PATH):
        file1 = open(EVENTS_FILE_PATH, "w")
        file1.write("{}")
        file1.close()

    events_file = open(EVENTS_FILE_PATH, "r+")
    stored_events = json.loads(events_file.read())
    return stored_events


class EventsRegistryService:
    def __init__(self):
        self._events = init_service()

    def get_events(self):
        return self._events

    def get_event(self, key: str):
        if key in self._events:
            return self._events[key]
        return None

    def remove_event(self, key: str):
        if key in self._events:
            stored_events = self._events
            del stored_events[key]
            file1 = open(EVENTS_FILE_PATH, "w")
            file1.write(json.dumps(stored_events))
            file1.close()

    def align_stored_events(self):
        if not os.path.exists(EVENTS_FILE_PATH):
            file1 = open(EVENTS_FILE_PATH, "w")
            file1.write("{}")
            file1.close()

        file1 = open(EVENTS_FILE_PATH, "r+")
        self._events = json.loads(file1.readline())

    def store_event(self, key):
        now = datetime.now()
        stored_events = self._events
        stored_events[key] = datetime.timestamp(now)
        file1 = open(EVENTS_FILE_PATH, "w")
        file1.write(json.dumps(stored_events))
        file1.close()

    def recently_notified(self, key, minutes=60):
        try:
            stored_events = self._events
            msg_sent_time = datetime.fromtimestamp(stored_events[key])
            is_already_notified = msg_sent_time > (datetime.now() - relativedelta(minutes=minutes))
            result = True if is_already_notified else False
        except:
            result = False

        if result:
            logging.info(f"{key} already notified recently: {msg_sent_time}")

        return result
