# -*- coding: utf-8 -*-
"""
Created on 2022/04/12
@author: schengatto@gmail.com
"""
import json
import os
import uuid
import logging
from datetime import datetime

logger = logging.getLogger()
ORDERS_FILE_PATH = "./resources/orders.bot"


def read_file():
    if not os.path.exists(ORDERS_FILE_PATH):
        file = open(ORDERS_FILE_PATH, "w")
        file.write("{}")
        file.close()

    orders_file = open(ORDERS_FILE_PATH, "r+")
    stored_events = json.loads(orders_file.read())
    return stored_events


class OrdersRegistryService:
    def __init__(self):
        self._orders = read_file()

    def get_orders(self):
        return self._orders

    def find_orders_by_symbol(self, symbol: str, processed=False):
        orders = self.get_orders()
        results = []
        if symbol in orders:
            for order in orders[symbol]:
                if order['processed'] == processed:
                    results.append(order)
        return results

    def find_order_by_id(self, symbol: str, order_id: str):
        orders = self.get_orders()
        if symbol in orders:
            for order in orders[symbol]:
                if order["id"] == order_id:
                    return order
        return None

    def remove_order(self, symbol: str, order_id: str):
        if symbol in self._orders:
            events = self._orders[symbol]
            for idx, event in enumerate(events):
                if event["id"] == order_id:
                    del events[idx]
                    self.commit_orders()

    def set_order_processed(self, symbol: str, order_id: str):
        orders = self.get_orders()
        if symbol in orders:
            for order in orders[symbol]:
                if order["id"] == order_id:
                    order["processed"] = True
                    order["updated"] = datetime.timestamp(datetime.now())
                    self.commit_orders()
                    return

        logger.info(f"Order for symbol {symbol} and id {order_id} not found.")

    def store_new_order(self, symbol=None, coin=None, order_type=None, price=None, amount=None):
        order_id = str(uuid.uuid4())
        new_order = {
            "id": order_id,
            "type": order_type,
            "coin": coin,
            "price": price,
            "amount": str(amount),
            "processed": False,
            "updated": datetime.timestamp(datetime.now())
        }
        if symbol not in self._orders:
            self._orders = {symbol: []}
        orders = self._orders[symbol]
        orders.append(new_order)
        self.commit_orders()
        return order_id

    def commit_orders(self):
        file1 = open(ORDERS_FILE_PATH, "w")
        file1.write(json.dumps(self._orders))
        file1.close()

    def force_resync(self):
        self._orders = read_file()
