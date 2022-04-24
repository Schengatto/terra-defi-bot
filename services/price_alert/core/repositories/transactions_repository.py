# -*- coding: utf-8 -*-
"""
Created on 2022/04/23
@author: schengatto@gmail.com
"""
from core.connectors.postgresql_connector import PostgresSqlConnector

TRANSACTIONS_TABLE = "transactions"


def map_to_entity(raw_row):
    return {
        "id": raw_row[0],
        "pair": raw_row[1],
        "offered_token": raw_row[2],
        "asked_token": raw_row[3],
        "amount": float(raw_row[4]),
        "price": float(raw_row[5]),
        "tx_hash": raw_row[6],
        "updated": raw_row[7]
    }


class TransactionsRepository:
    def get_transactions(self):
        read_ = f'''SELECT
                        t.id,
                        tp.name,
                        tt1.symbol,
                        tt2.symbol,
                        t.amount,
                        t.price,
                        t.transaction_hash,
                        t.updated
                    FROM {TRANSACTIONS_TABLE} t
                        join terra_pairs tp on t.terra_pair = tp.id
                        join terra_tokens tt1 on t.offered_token = tt1.id
                        join terra_tokens tt2 on t.asked_token = tt2.id
        '''
        psql = PostgresSqlConnector()
        return psql.read(read_, mapping=map_to_entity)

    def save_transaction(self,
                         terra_pair_contract: str,
                         offered_token_contract: str,
                         asked_token_contract: str,
                         amount: float,
                         price: float,
                         tx_hash: str):
        insert_ = f'''INSERT
                    INTO {TRANSACTIONS_TABLE} (terra_pair, offered_token, asked_token, price, amount, transaction_hash)
                    VALUES(
                        (select id from terra_pairs where mainnet_contract = '{terra_pair_contract}' OR testnet_contract = '{terra_pair_contract}'),
                        (select id from terra_tokens where mainnet_contract = '{offered_token_contract}' OR testnet_contract = '{offered_token_contract}'),
                        (select id from terra_tokens where mainnet_contract = '{asked_token_contract}' OR testnet_contract = '{asked_token_contract}'),
                        {price},
                        {amount},
                        '{tx_hash}'
                    );
                    '''
        psql = PostgresSqlConnector()
        psql.insert(insert_)

        read_ = f'''SELECT id from {TRANSACTIONS_TABLE} ORDER BY updated DESC LIMIT 1'''
        return psql.read(read_)[0][0]
