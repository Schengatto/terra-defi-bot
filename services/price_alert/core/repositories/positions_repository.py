# -*- coding: utf-8 -*-
"""
Created on 2022/05/06
@author: schengatto@gmail.com
"""
import json
from typing import Any, Union

from core.connectors.postgresql_connector import PostgresSqlConnector

from core.functions.database_functions import getStrOrNone, getIntOrNone, getBoolOrNone, \
    getFloatOrNone, getTimestampOrNone

POSITIONS_TABLE = "positions"


class Position:
    def __init__(self,
                 id_position: str = None,
                 pair_name: str = None,
                 pair_mainnet_contract: str = None,
                 pair_testnet_contract: str = None,
                 token_symbol: str = None,
                 token_icon: str = None,
                 token_decimal_digits: int = None,
                 token_mainnet_contract: str = None,
                 token_testnet_contract: str = None,
                 open_transaction_price: float = None,
                 open_transaction_amount_offered: int = None,
                 open_transaction_amount_received: int = None,
                 open_transaction_hash: str = None,
                 open_transaction_created: float = None,
                 close_transaction_price: float = None,
                 close_transaction_hash: str = None,
                 close_transaction_created: float = None,
                 close_transaction_amount_offered: int = None,
                 close_transaction_amount_received: int = None,
                 stop_loss_price: float = None,
                 take_profit_price: float = None,
                 created: float = None,
                 updated: float = None,
                 trailing_stop_loss: bool = None,
                 open_order_id: str = None):
        self.id_position = id_position
        self.pair_name = pair_name
        self.pair_mainnet_contract = pair_mainnet_contract
        self.pair_testnet_contract = pair_testnet_contract
        self.token_symbol = token_symbol
        self.token_icon = token_icon
        self.token_decimal_digits = token_decimal_digits
        self.token_mainnet_contract = token_mainnet_contract
        self.token_testnet_contract = token_testnet_contract
        self.open_transaction_price = open_transaction_price
        self.open_transaction_amount_offered = open_transaction_amount_offered
        self.open_transaction_amount_received = open_transaction_amount_received
        self.open_transaction_hash = open_transaction_hash
        self.open_transaction_created = open_transaction_created
        self.close_transaction_price = close_transaction_price
        self.close_transaction_hash = close_transaction_hash
        self.close_transaction_created = close_transaction_created
        self.close_transaction_amount_offered = close_transaction_amount_offered
        self.close_transaction_amount_received = close_transaction_amount_received
        self.stop_loss_price = stop_loss_price
        self.take_profit_price = take_profit_price
        self.created = created
        self.updated = updated
        self.trailing_stop_loss = trailing_stop_loss
        self.open_order_id = open_order_id

    def toJSON(self):
        return json.loads(json.dumps(self, default=lambda o: o.__dict__))


def map_to_entity(raw_row: Any) -> Position:
    return Position(
        id_position=getStrOrNone(raw_row[0]),
        pair_name=getStrOrNone(raw_row[1]),
        pair_mainnet_contract=getStrOrNone(raw_row[2]),
        pair_testnet_contract=getStrOrNone(raw_row[3]),
        token_symbol=getStrOrNone(raw_row[4]),
        token_icon=getStrOrNone(raw_row[5]),
        token_decimal_digits=getIntOrNone(raw_row[6]),
        token_mainnet_contract=getStrOrNone(raw_row[7]),
        token_testnet_contract=getStrOrNone(raw_row[8]),
        open_transaction_price=getFloatOrNone(raw_row[9]),
        open_transaction_amount_offered=getIntOrNone(raw_row[10]),
        open_transaction_amount_received=getIntOrNone(raw_row[11]),
        open_transaction_hash=getStrOrNone(raw_row[12]),
        open_transaction_created=getTimestampOrNone(raw_row[13]),
        close_transaction_price=getFloatOrNone(raw_row[14]),
        close_transaction_amount_offered=getIntOrNone(raw_row[15]),
        close_transaction_amount_received=getIntOrNone(raw_row[16]),
        close_transaction_hash=getStrOrNone(raw_row[17]),
        close_transaction_created=getTimestampOrNone(raw_row[18]),
        stop_loss_price=getFloatOrNone(raw_row[19]),
        take_profit_price=getFloatOrNone(raw_row[20]),
        created=getTimestampOrNone(raw_row[21]),
        updated=getTimestampOrNone(raw_row[22]),
        trailing_stop_loss=getBoolOrNone(raw_row[23]),
        open_order_id=getStrOrNone(raw_row[24]),
    )


class PositionsRepository:
    def find_position_by_id(self, position_id: str) -> Union[Position, None]:
        read_ = f'''
        SELECT
            p.id,
            tp.name,
            tp.mainnet_contract,
            tp.testnet_contract,
            tt.symbol,
            tt.icon,
            tt.decimal_digits,
            tt.mainnet_contract,
            tt.testnet_contract,
            t1.price,
            t1.amount_offered,
            t1.amount_received,
            t1.transaction_hash,
            t1.created,
            t2.price,
            t2.amount_offered,
            t2.amount_received,
            t2.transaction_hash,
            t2.created,
            p.stop_loss_price,
            p.take_profit_price,
            p.created,
            p.updated,
            p.trailing_stop_loss,
            t1.order_id
        FROM {POSITIONS_TABLE} p
            join terra_pairs tp on p.terra_pair = tp.id
            join terra_tokens tt on p.terra_token = tt.id
            join transactions t1 on p.open_transaction = t1.id
            left join transactions t2 on p.close_transaction = t2.id
        WHERE p.id::text = '{position_id}'
        ORDER BY tt.name ASC, t1.price ASC, p.updated DESC;
        '''
        psql = PostgresSqlConnector()
        result = psql.read(read_, mapping=map_to_entity)
        return result[0] if len(result) > 0 else None

    def get_positions(self, include_closed=True) -> list[Position]:
        read_ = f'''
        SELECT
            p.id,
            tp.name,
            tp.mainnet_contract,
            tp.testnet_contract,
            tt.symbol,
            tt.icon,
            tt.decimal_digits,
            tt.mainnet_contract,
            tt.testnet_contract,
            t1.price,
            t1.amount_offered,
            t1.amount_received,
            t1.transaction_hash,
            t1.created,
            t2.price,
            t2.amount_offered,
            t2.amount_received,
            t2.transaction_hash,
            t2.created,
            p.stop_loss_price,
            p.take_profit_price,
            p.created,
            p.updated,
            p.trailing_stop_loss,
            t1.order_id
        FROM {POSITIONS_TABLE} p
            join terra_pairs tp on p.terra_pair = tp.id
            join terra_tokens tt on p.terra_token = tt.id
            join transactions t1 on p.open_transaction = t1.id
            left join transactions t2 on p.close_transaction = t2.id
       '''
        if not include_closed:
            read_ = f"{read_} WHERE t2.transaction_hash is NULL"

        read_ = f"{read_} ORDER BY tt.name ASC, t1.price ASC, p.updated DESC;"
        psql = PostgresSqlConnector()
        result = psql.read(read_, mapping=map_to_entity)
        return result

    def open_position(self,
                      terra_pair_contract: str,
                      terra_token_contract: str,
                      open_transaction_id: str):
        insert_ = f'''INSERT
                    INTO {POSITIONS_TABLE} (terra_pair, terra_token, open_transaction)
                    VALUES(
                        (select id from terra_pairs where mainnet_contract = '{terra_pair_contract}' OR testnet_contract = '{terra_pair_contract}'),
                        (select id from terra_tokens where mainnet_contract = '{terra_token_contract}' OR testnet_contract = '{terra_token_contract}'),
                        '{open_transaction_id}'
                    );'''
        psql = PostgresSqlConnector()
        psql.insert(insert_)

        read_ = f'''SELECT id from {POSITIONS_TABLE} ORDER BY updated DESC LIMIT 1'''
        result = psql.read(read_)
        return result[0][0] if len(result) > 0 else None

    def close_position(self,
                       position_id: str,
                       close_transaction_id: str):
        insert_ = f'''
        UPDATE {POSITIONS_TABLE}
        SET 
            close_transaction = '{close_transaction_id}',
            updated = CURRENT_TIMESTAMP
        WHERE id::text = '{position_id}';'''
        psql = PostgresSqlConnector()
        psql.insert(insert_)

        return self.find_position_by_id(position_id)

    def update_position(self,
                        position_id: str,
                        stop_loss_price: float,
                        take_profit_price: float,
                        trailing_stop_loss: bool = False):
        insert_ = f'''
                UPDATE {POSITIONS_TABLE}
                SET 
                    stop_loss_price = {stop_loss_price},
                    take_profit_price = {take_profit_price},
                    trailing_stop_loss = {trailing_stop_loss},
                    updated = CURRENT_TIMESTAMP
                WHERE id::text = '{position_id}';'''
        psql = PostgresSqlConnector()
        psql.insert(insert_)

        return self.find_position_by_id(position_id)
