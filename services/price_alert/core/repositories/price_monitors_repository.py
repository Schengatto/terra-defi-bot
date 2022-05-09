# -*- coding: utf-8 -*-
"""
Created on 2022/04/12
@author: schengatto@gmail.com
"""
import logging

from core.connectors.postgresql_connector import PostgresSqlConnector

logger = logging.getLogger()
PRICE_MONITOR_TABLE = "price_monitors"


def map_to_entity(raw_row):
    return {
        "id": raw_row[0],
        "name": raw_row[1],
        "price_symbol": raw_row[2],
        "terra_pair_symbol": raw_row[3],
        "terra_pair_mainnet": raw_row[4],
        "terra_pair_testnet": raw_row[5],
        "ask_token_symbol": raw_row[6],
        "ask_token_mainnet": raw_row[7],
        "ask_token_testnet": raw_row[8],
        "price_provider": raw_row[9],
        "active": raw_row[10],
        "reliability": int(raw_row[11]),
        "updated": raw_row[12]
    }


class PriceMonitorsRepository:
    def __init__(self):
        self._price_monitors = self.get_price_monitors()

    def get_price_monitors(self):
        read_ = f'''
                SELECT
                    pm.id,
                    pm.name,
                    s.name,
                    tp.name,
                    tp.mainnet_contract,
                    tp.testnet_contract,
                    tt.symbol,
                    tt.mainnet_contract,
                    tt.testnet_contract,
                    p.name,
                    pm.active,
                    pm.reliability,
                    pm.updated
                FROM {PRICE_MONITOR_TABLE} pm
                    join price_symbols s on pm.price_symbol = s.id
                    join price_providers p on s.price_provider = p.id
                    left join terra_pairs tp on s.terra_pair = tp.id 
                    left join terra_tokens tt on s.ask_token = tt.id
                WHERE pm.active = true
                ORDER BY updated'''
        psql = PostgresSqlConnector()
        return psql.read(read_, mapping=map_to_entity)

    def find_monitor_by_symbol(self, symbol: str):
        read_ = f'''
                SELECT
                    pm.id,
                    pm.name,
                    s.name,
                    tp.name,
                    tp.mainnet_contract,
                    tp.testnet_contract,
                    tt.symbol,
                    tt.mainnet_contract,
                    tt.testnet_contract,
                    p.name,
                    pm.active,
                    pm.reliability,
                    pm.updated
                FROM {PRICE_MONITOR_TABLE} pm
                    join price_symbols s on pm.price_symbol = s.id
                    join price_providers p on s.price_provider = p.id
                    left join terra_pairs tp on s.terra_pair = tp.id 
                    left join terra_tokens tt on s.ask_token = tt.id
                WHERE pm.active = true
                    AND s.name ILIKE '%{symbol}%'
                ORDER BY updated'''
        psql = PostgresSqlConnector()
        return psql.read(read_, mapping=map_to_entity)

    def find_monitor_by_id(self, price_monitor_id: str):
        read_ = f'''
                SELECT
                    pm.id,
                    pm.name,
                    s.name,
                    tp.name,
                    tp.mainnet_contract,
                    tp.testnet_contract,
                    tt.symbol,
                    tt.mainnet_contract,
                    tt.testnet_contract,
                    p.name,
                    pm.active,
                    pm.reliability,
                    pm.updated
                FROM {PRICE_MONITOR_TABLE} pm
                    join price_symbols s on pm.price_symbol = s.id
                    join price_providers p on s.price_provider = p.id
                    left join terra_pairs tp on s.terra_pair = tp.id 
                    left join terra_tokens tt on s.ask_token = tt.id
               WHERE pm.id::text = '{price_monitor_id}'
               ORDER BY updated'''
        psql = PostgresSqlConnector()
        return psql.read(read_, mapping=map_to_entity)

    def store_price_monitor(self, symbol: str, name: str):
        insert_ = f'''INSERT
                    INTO {PRICE_MONITOR_TABLE} (price_symbol, name)
                    VALUES((select id from price_symbols where name = '{symbol}'), '{name}');
                    '''
        psql = PostgresSqlConnector()
        psql.insert(insert_)

        read_ = f'''SELECT id from {PRICE_MONITOR_TABLE} ORDER BY updated DESC LIMIT 1'''
        return psql.read(read_)[0][0]

    def update_price_monitor(self, monitor_id: str, reliability: int):
        update_ = f'''UPDATE {PRICE_MONITOR_TABLE} SET reliability = {reliability} WHERE id::text = '{monitor_id}';'''
        psql = PostgresSqlConnector()
        psql.update(update_)
        return self.find_monitor_by_id(monitor_id)

    def remove_price_monitor(self, price_monitor_id: str):
        delete_ = f"DELETE FROM {PRICE_MONITOR_TABLE} WHERE id::text = '{price_monitor_id}';"
        psql = PostgresSqlConnector()
        psql.delete(delete_)
        return self.find_events_by_name(price_monitor_id) is None
