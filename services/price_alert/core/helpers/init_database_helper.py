from core.connectors.postgresql_connector import PostgresSqlConnector
from core.helpers.events_database_helper import EventsDatabaseHelper
from core.helpers.orders_database_helper import OrdersDatabaseHelper
from core.helpers.price_database_helper import PriceDatabaseHelper
from core.helpers.terra_tokens_database_helper import TerraTokensDatabaseHelper
from core.helpers.transactions_database_helper import TransactionsDatabaseHelper

DATABASE_NAME = "terra_defi"
TERRA_TOKENS_TABLE = "terra_tokens"
TERRA_PAIRS_TABLE = "terra_pairs"
PRICE_PROVIDERS = "price_providers"
PRICE_SYMBOLS = "price_symbols"
PRICE_MONITORS = "price_monitors"
EVENT_TYPES_TABLE = "event_types"
EVENTS_TABLE = "events"
ORDERS_TABLE = "orders"
TRANSACTIONS_TABLE = "transactions"


class InitDatabaseHelper:
    def __init__(self):
        if not self.__has_database_created():
            self.__create_database()

        if not self.__has_terra_tokens_table() or not self.__has_terra_pairs_table:
            TerraTokensDatabaseHelper()

        if not self.__has_price_providers_table():
            PriceDatabaseHelper()

        if not self.__has_events_table():
            EventsDatabaseHelper()

        if not self.__has_orders_table():
            OrdersDatabaseHelper()

        if not self.__has_transactions_table():
            TransactionsDatabaseHelper()

    def __has_database_created(self):
        read_ = f'''select exists(SELECT datname FROM pg_catalog.pg_database WHERE lower(datname) = lower('{DATABASE_NAME}'));'''
        psql = PostgresSqlConnector()
        return psql.read(read_)[0][0]

    def __create_database(self):
        create_ = f'''
        CREATE DATABASE IF NOT EXISTS terra_defi
            WITH
            OWNER = terra_defi_db_user
            ENCODING = 'UTF8'
            LC_COLLATE = 'en_US.utf8'
            LC_CTYPE = 'en_US.utf8'
            TABLESPACE = pg_default
            CONNECTION LIMIT = -1;
        '''
        psql = PostgresSqlConnector()
        psql.create_database(create_)

        create_ = f'''CREATE EXTENSION IF NOT EXISTS "uuid-ossp" SCHEMA public;'''
        psql = PostgresSqlConnector()
        psql.create(create_)

    def __has_terra_tokens_table(self):
        read_ = f'''
        SELECT EXISTS (
            SELECT FROM 
                pg_tables
            WHERE 
                schemaname = 'public' AND 
                tablename  = '{TERRA_TOKENS_TABLE}'
            );
        '''
        psql = PostgresSqlConnector()
        return psql.read(read_)[0][0]

    def __has_terra_pairs_table(self):
        read_ = f'''
        SELECT EXISTS (
            SELECT FROM 
                pg_tables
            WHERE 
                schemaname = 'public' AND 
                tablename  = '{TERRA_PAIRS_TABLE}'
            );
        '''
        psql = PostgresSqlConnector()
        return psql.read(read_)[0][0]

    def __has_price_providers_table(self):
        read_ = f'''
        SELECT EXISTS (
            SELECT FROM 
                pg_tables
            WHERE 
                schemaname = 'public' AND 
                tablename  = '{PRICE_PROVIDERS}'
            );
        '''
        psql = PostgresSqlConnector()
        return psql.read(read_)[0][0]

    def __has_events_table(self):
        read_ = f'''
           SELECT EXISTS (
               SELECT FROM 
                   pg_tables
               WHERE 
                   schemaname = 'public' AND 
                   tablename  = '{EVENTS_TABLE}'
               );
           '''
        psql = PostgresSqlConnector()
        return psql.read(read_)[0][0]

    def __has_orders_table(self):
        read_ = f'''
        SELECT EXISTS (
            SELECT FROM 
                pg_tables
            WHERE 
                schemaname = 'public' AND 
                tablename  = '{ORDERS_TABLE}'
            );
        '''
        psql = PostgresSqlConnector()
        return psql.read(read_)[0][0]

    def __has_transactions_table(self):
        read_ = f'''
          SELECT EXISTS (
              SELECT FROM 
                  pg_tables
              WHERE 
                  schemaname = 'public' AND 
                  tablename  = '{TRANSACTIONS_TABLE}'
              );
          '''
        psql = PostgresSqlConnector()
        return psql.read(read_)[0][0]
