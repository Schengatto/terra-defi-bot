# -*- coding: utf-8 -*-
"""
Created on 2022/04/12
@author: schengatto@gmail.com
"""
import json
import logging
from enum import Enum

from core.connectors.postgresql_connector import PostgresSqlConnector

logger = logging.getLogger()
ORDERS_FILE_PATH = "./resources/orders.bot"
ORDERS_TABLE = "orders"


class OrderType(Enum):
    Buy = "BUY"
    Sell = "SELL"
    Warn = "WARN"


def map_to_entity(raw_row):
    return {
        "id": raw_row[0],
        "type": raw_row[1],
        "price": float(raw_row[2]),
        "amount": float(raw_row[3]) if raw_row[3] is not None else None,
        "token": raw_row[4],
        "terra_pair": raw_row[5],
        "name": raw_row[6],
        "processed": raw_row[7],
        "updated": raw_row[8]
    }


class OrdersRepository:
    def get_orders(self, include_processed: bool = False):
        read_ = f'''SELECT
                        o.id,
                        o.type,
                        o.price,
                        o.amount,
                        o.terra_token,
                        o.terra_pair,
                        tp.name,
                        o.processed,
                        o.updated
                    FROM {ORDERS_TABLE} o
                        join terra_pairs tp on o.terra_pair = tp.id
                    WHERE 1=1'''
        if not include_processed:
            read_ = f"{read_} AND processed = false"
        psql = PostgresSqlConnector()
        return psql.read(read_, mapping=map_to_entity)

    def find_orders_by_price_symbol(self, price_symbol: str, include_processed: bool = False):
        read_ = f'''SELECT
                        o.id,
                        o.type,
                        o.price,
                        o.amount,
                        o.terra_token,
                        o.terra_pair,
                        tp.name,
                        o.processed,
                        o.updated
                    FROM {ORDERS_TABLE} o
                        join terra_pairs tp on o.terra_pair = tp.id'''
        if include_processed:
            read_ = f"{read_} WHERE tp.name ILIKE '%{price_symbol}%'"
        else:
            read_ = f"{read_} WHERE tp.name ILIKE '%{price_symbol}%' AND processed = false"
        psql = PostgresSqlConnector()
        return psql.read(read_, mapping=map_to_entity)

    def find_order_by_id(self, order_id: str):
        read_ = f'''SELECT
                        o.id,
                        o.type,
                        o.price,
                        o.amount,
                        o.terra_token,
                        o.terra_pair,
                        tp.name,
                        o.processed,
                        o.updated
                    FROM {ORDERS_TABLE} o
                        join terra_pairs tp on o.terra_pair = tp.id
                    WHERE o.id::text = '{order_id}';'''
        psql = PostgresSqlConnector()
        return psql.read(read_, mapping=map_to_entity)

    def store_new_order(self, pair_name: str = None, asked_token_symbol: str = None, order_type: str = None, price: float = None, amount: float = None):
        insert_ = f'''INSERT
            INTO {ORDERS_TABLE} (terra_pair, terra_token, type, price, amount)
            VALUES(
                (select id from terra_pairs where name = '{pair_name}'),
                (select id from terra_tokens where symbol = '{asked_token_symbol}'),
                '{order_type}',
                {price},
                {amount if amount is not None else 'null'}
            );
            '''
        psql = PostgresSqlConnector()
        psql.insert(insert_)

        read_ = f'''SELECT id from {ORDERS_TABLE} ORDER BY updated DESC LIMIT 1'''
        return psql.read(read_)[0][0]

    def remove_order(self, order_id: str):
        delete_ = f"DELETE FROM {ORDERS_TABLE}"
        if order_id is not None:
            delete_ = f"{delete_} WHERE id::text = '{order_id}';"
        psql = PostgresSqlConnector()
        psql.delete(delete_)
        return self.find_order_by_id(order_id) is None

    def set_order_processed(self, order_id: str):
        update_ = f"UPDATE {ORDERS_TABLE} SET processed = true, updated = CURRENT_TIMESTAMP WHERE id::text = '{order_id}';"
        psql = PostgresSqlConnector()
        psql.update(update_)
        return self.find_order_by_id(order_id)

    def export_orders(self):
        file1 = open(ORDERS_FILE_PATH, "w")
        file1.write(json.dumps(self.get_orders()))
        file1.close()
