from core.connectors.postgresql_connector import PostgresSqlConnector
from core.helpers.events_database_helper import EventsDatabaseHelper
from core.helpers.orders_database_helper import OrdersDatabaseHelper
from core.helpers.price_database_helper import PriceDatabaseHelper
from core.helpers.terra_tokens_database_helper import TerraTokensDatabaseHelper
from core.helpers.transactions_database_helper import TransactionsDatabaseHelper
from core.helpers.positions_database_helper import PositionsDatabaseHelper

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
POSITIONS_TABLE = "positions"


class InitDatabaseHelper:
    def __init__(self):
        if not self.__has_database_created():
            self.__create_database()

        if not self.__has_table(TERRA_TOKENS_TABLE) or not self.__has_table(TERRA_PAIRS_TABLE):
            TerraTokensDatabaseHelper()

        if not self.__has_table(PRICE_PROVIDERS):
            PriceDatabaseHelper()

        if not self.__has_table(EVENTS_TABLE):
            EventsDatabaseHelper()

        if not self.__has_table(ORDERS_TABLE):
            OrdersDatabaseHelper()

        if not self.__has_table(TRANSACTIONS_TABLE):
            TransactionsDatabaseHelper()

        if not self.__has_table(POSITIONS_TABLE):
            PositionsDatabaseHelper()

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

    def __has_table(self, table_name: str):
        read_ = f'''
        SELECT EXISTS (
            SELECT FROM 
                pg_tables
            WHERE 
                schemaname = 'public' AND 
                tablename  = '{table_name}'
            );
        '''
        psql = PostgresSqlConnector()
        return psql.read(read_)[0][0]
