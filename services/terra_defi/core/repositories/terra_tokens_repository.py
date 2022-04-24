# -*- coding: utf-8 -*-
"""
Created on 2022/04/12
@author: schengatto@gmail.com
"""
import logging

from core.connectors.postgresql_connector import PostgresSqlConnector

logger = logging.getLogger()
TERRA_TOKENS_TABLE = "terra_tokens"
TERRA_PAIRS_TABLE = "terra_pairs"

# TODO get them from database
TERRA_NATIVE_COINS = ['uaud', 'ucad', 'uchf', 'ucny', 'udkk', 'ueur', 'ugbp', 'uhkd', 'uidr', 'uinr', 'ujpy', 'ukrw',
                      'umnt', 'umyr', 'unok', 'uphp', 'usdr', 'usek', 'usgd', 'uthb', 'utwd', 'uusd', 'uluna']


def map_terra_token_to_entity(raw_row):
    return {
        "id": raw_row[0],
        "name": raw_row[1],
        "symbol": raw_row[2],
        "protocol": raw_row[3],
        "decimal_digits": int(raw_row[4]),
        "icon": raw_row[5],
        "mainnet_contract": raw_row[6],
        "testnet_contract": raw_row[7],
        "is_native": raw_row[8],
        "updated": raw_row[9]
    }


def map_terra_pair_to_entity(raw_row):
    return {
        "id": raw_row[0],
        "name": raw_row[1],
        "asset1": raw_row[2],
        "asset2": raw_row[3],
        "mainnet_contract": raw_row[4],
        "testnet_contract": raw_row[5],
        "updated": raw_row[6]
    }


def map_terra_pair_details_to_entity(raw_row):
    return {
        "id": raw_row[0],
        "name": raw_row[1],
        "contract": raw_row[2],
        "protocol": raw_row[3],
        "token1_symbol": raw_row[4],
        "token1_contract": raw_row[5],
        "token2_symbol": raw_row[6],
        "token2_contract": raw_row[7],
    }


class TerraTokensRepository:
    def __init__(self):
        logger.info("TerraTokensRepository initialized")

    def get_tokens(self, token_symbol=None, token_name=None, mainnet_contract=None, testnet_contract=None):
        read_ = f'''SELECT
                        tt.id,
                        tt.name,
                        tt.symbol,
                        tt.protocol,
                        tt.decimal_digits,
                        tt.icon,
                        tt.mainnet_contract,
                        tt.testnet_contract,
                        tt.is_native,
                        tt.updated
                    FROM {TERRA_TOKENS_TABLE} tt
                    WHERE 1=1'''
        if token_symbol is not None:
            read_ = f"{read_} AND tt.symbol ILIKE '%{token_symbol}%'"
        if token_name is not None:
            read_ = f"{read_} AND tt.name ILIKE '%{token_name}%'"
        if mainnet_contract is not None:
            read_ = f"{read_} AND tt.mainnet_contract ILIKE '%{mainnet_contract}%'"
        if testnet_contract is not None:
            read_ = f"{read_} AND tt.testnet_contract ILIKE '%{testnet_contract}%'"
        psql = PostgresSqlConnector()
        return psql.read(read_, mapping=map_terra_token_to_entity)

    def get_native_tokens(self):
        return TERRA_NATIVE_COINS

    def find_token_by_symbol(self, symbol: str):
        read_ = f'''SELECT
                        tt.id,
                        tt.name,
                        tt.symbol,
                        tt.protocol,
                        tt.decimal_digits,
                        tt.icon,
                        tt.mainnet_contract,
                        tt.testnet_contract,
                        tt.is_native,
                        tt.updated
                    FROM {TERRA_TOKENS_TABLE} tt
                    WHERE tt.symbol = '{symbol}'
                    ORDER BY tt.is_native, tt.updated'''
        psql = PostgresSqlConnector()
        return psql.read(read_, mapping=map_terra_token_to_entity)

    def find_token_by_id(self, token_id: str):
        read_ = f'''SELECT
                        tt.id,
                        tt.name,
                        tt.symbol,
                        tt.protocol,
                        tt.decimal_digits,
                        tt.icon,
                        tt.mainnet_contract,
                        tt.testnet_contract,
                        tt.is_native,
                        tt.updated
                    FROM {TERRA_TOKENS_TABLE} tt
                    WHERE tt.id::text = '{token_id}'
                    ORDER BY tt.is_native, tt.updated'''
        psql = PostgresSqlConnector()
        return psql.read(read_, mapping=map_terra_token_to_entity)

    def find_pair_by_id(self, pair_id: str = None):
        read_ = f'''SELECT
                           tp.id,
                           tp.name,
                           tp.asset1,
                           tp.asset2,
                           tp.mainnet_contract,
                           tp.testnet_contract,
                           tp.protocol,
                           tp.updated
                        FROM {TERRA_PAIRS_TABLE} tp
                        WHERE tp.id::text = '{pair_id}';'''
        psql = PostgresSqlConnector()
        return psql.read(read_, mapping=map_terra_pair_to_entity)

    def get_pairs(self, pair_name=None, mainnet_contract=None, testnet_contract=None):
        read_ = f'''SELECT
                           tp.id,
                           tp.name,
                           tp.asset1,
                           tp.asset2,
                           tp.mainnet_contract,
                           tp.testnet_contract,
                           tp.protocol,
                           tp.updated
                       FROM {TERRA_PAIRS_TABLE} tp
                       WHERE 1=1'''
        if pair_name is not None:
            read_ = f"{read_} AND tp.name ILIKE '%{pair_name}%'"
        if mainnet_contract is not None:
            read_ = f"{read_} AND tp.mainnet_contract ILIKE '%{mainnet_contract}%'"
        if testnet_contract is not None:
            read_ = f"{read_} AND tp.name ILIKE '%{testnet_contract}%'"
        psql = PostgresSqlConnector()
        return psql.read(read_, mapping=map_terra_pair_to_entity)

    def get_mainnet_pairs_details(self):
        read_ = f'''
        select 
            tp.id as id,
            tp.name as pair_name,
            tp.mainnet_contract as pair_contract,
            tp.protocol as pair_protocol,
            tt1.symbol as token1_symbol,
            tt1.mainnet_contract as token1_contract,
            tt2.symbol as token2_symbol,
            tt2.mainnet_contract as token2_contract
        from terra_pairs tp
                join terra_tokens tt1 on tt1.id = tp.asset1
                join terra_tokens tt2 on tt2.id = tp.asset2
        where tp.mainnet_contract is not NULL;'''
        psql = PostgresSqlConnector()
        return psql.read(read_, mapping=map_terra_pair_to_entity)

    def get_testnet_pairs_details(self, ):
        read_ = f'''
        select 
            tp.id as id,
            tp.name as pair_name,
            tp.testnet_contract as pair_contract,
            tp.protocol as pair_protocol,
            tt1.symbol as token1_symbol,
            tt1.testnet_contract as token1_contract,
            tt2.symbol as token2_symbol,
            tt2.testnet_contract as token2_contract
        from terra_pairs tp
                join terra_tokens tt1 on tt1.id = tp.asset1
                join terra_tokens tt2 on tt2.id = tp.asset2
        where tp.testnet_contract is not NULL;'''
        psql = PostgresSqlConnector()
        return psql.read(read_, mapping=map_terra_pair_to_entity)

    def save_token(self, symbol: str = None, name: str = None, mainnet_contract: str = None,
                   testnet_contract: str = None, icon: str = None, protocol: str = None, is_native: bool = False):
        insert_ = f'''INSERT INTO {TERRA_TOKENS_TABLE} (name, symbol, icon, mainnet_contract, testnet_contract, protocol, is_native)
                        VALUES ('{name}', '{symbol}', '{icon}', '{mainnet_contract}', '{testnet_contract}', '{protocol}', {is_native});'''
        psql = PostgresSqlConnector()
        psql.insert(insert_)

        read_ = f'''SELECT id from {TERRA_TOKENS_TABLE} ORDER BY updated DESC LIMIT 1'''
        return psql.read(read_)[0][0]

    def remove_token(self, token_id: str):
        delete_ = f"DELETE FROM {TERRA_TOKENS_TABLE} WHERE id::text = '{token_id}';"
        psql = PostgresSqlConnector()
        psql.delete(delete_)
        return self.find_order_by_id(token_id) is None


