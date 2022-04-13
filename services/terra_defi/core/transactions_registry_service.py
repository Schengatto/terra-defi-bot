# -*- coding: utf-8 -*-
"""
Created on 2022/04/12
@author: schengatto@gmail.com
"""
import json
import os
from datetime import datetime

TRANSACTIONS_FILE_PATH = "./resources/transactions.bot"


def init_service():
    if not os.path.exists(TRANSACTIONS_FILE_PATH):
        file = open(TRANSACTIONS_FILE_PATH, "w")
        file.close()

    events_file = open(TRANSACTIONS_FILE_PATH, "r+")
    stored_transactions = events_file.read()
    return stored_transactions


class TransactionsRegistryService:
    def __init__(self):
        self._transactions = init_service()

    def get_transactions(self):
        return self._transactions

    def align_with_file(self):
        if not os.path.exists(TRANSACTIONS_FILE_PATH):
            file = open(TRANSACTIONS_FILE_PATH, "w")
            file.close()

        file = open(TRANSACTIONS_FILE_PATH, "r+")
        self._transactions = json.loads(file.readline())

    def store_transaction(self, msg):
        now = datetime.now()
        file = open(TRANSACTIONS_FILE_PATH, "a+")
        file.write(f"{now} | {datetime.timestamp(now)} | {msg}\n")
        file.close()
