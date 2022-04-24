from core.connectors.postgresql_connector import PostgresSqlConnector

ORDERS_TABLE = "orders"


class OrdersDatabaseHelper:
    def __init__(self):
        self.__init_database()

    def __init_database(self):
        self.__create_tables()

    def __create_tables(self):
        create_ = f'''
        CREATE TABLE IF NOT EXISTS public.{ORDERS_TABLE}
        (
            id uuid NOT NULL DEFAULT uuid_generate_v4(),
            terra_pair uuid NOT NULL,
            terra_token uuid NOT NULL,
            type varchar NOT NULL,
            price numeric NOT NULL,
            amount numeric,
            retries smallint DEFAULT 0,
            processed boolean NOT NULL DEFAULT false,
            updated timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT "{ORDERS_TABLE}_pk" PRIMARY KEY (id),
            CONSTRAINT {ORDERS_TABLE}_fk_terra_pair
             foreign key (terra_pair)
             REFERENCES public.terra_pairs (id),
            CONSTRAINT {ORDERS_TABLE}_fk_terra_tokens
             foreign key (terra_token)
             REFERENCES public.terra_tokens (id)
        );'''
        psql = PostgresSqlConnector()
        psql.create(create_)
