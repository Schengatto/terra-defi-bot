from core.connectors.postgresql_connector import PostgresSqlConnector

TRANSACTIONS_TABLE = "transactions"


class TransactionsDatabaseHelper:
    def __init__(self):
        self.__init_database__()

    def __init_database__(self):
        self.__create_transactions_table__()

    def __create_transactions_table__(self):
        create_ = f'''
        CREATE TABLE IF NOT EXISTS public.{TRANSACTIONS_TABLE}
        (
            id uuid NOT NULL DEFAULT uuid_generate_v4(),
            terra_pair uuid NOT NULL,
            offered_token uuid NOT NULL,
            asked_token uuid NOT NULL,
            price numeric NOT NULL,
            amount_offered numeric NOT NULL,
            amount_received numeric NOT NULL,
            transaction_hash varchar NOT NULL,
            order_id uuid,
            created timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT "{TRANSACTIONS_TABLE}_pk" PRIMARY KEY (id),
            CONSTRAINT {TRANSACTIONS_TABLE}_fk_terra_pair
             foreign key (terra_pair)
             REFERENCES public.terra_pairs (id),
            CONSTRAINT {TRANSACTIONS_TABLE}_fk_terra_tokens1
             foreign key (offered_token)
             REFERENCES public.terra_tokens (id),
            CONSTRAINT {TRANSACTIONS_TABLE}_fk_terra_tokens2
             foreign key (asked_token)
             REFERENCES public.terra_tokens (id),
            CONSTRAINT transactions_fk_orders
             foreign key (order_id)
             REFERENCES public.orders (id)
        );
        '''
        psql = PostgresSqlConnector()
        psql.create(create_)

        create_ = f'''
        CREATE UNIQUE INDEX IF NOT EXISTS {TRANSACTIONS_TABLE}_unique_idx_1
        ON public.{TRANSACTIONS_TABLE}(transaction_hash);'''
        psql = PostgresSqlConnector()
        psql.create(create_)

        create_ = f'''
        CREATE INDEX IF NOT EXISTS {TRANSACTIONS_TABLE}_unique_idx_2
        ON public.{TRANSACTIONS_TABLE}(order_id);'''
        psql = PostgresSqlConnector()
        psql.create(create_)
