from core.connectors.postgresql_connector import PostgresSqlConnector

TRANSACTIONS_TABLE = "transactions"


class TransactionsDatabaseHelper:
    def __init__(self):
        self.__init_database()

    def __init_database(self):
        self.__create_tables()

    def __create_tables(self):
        create_ = f'''
        CREATE TABLE IF NOT EXISTS public.{TRANSACTIONS_TABLE}
        (
            id uuid NOT NULL DEFAULT uuid_generate_v4(),
            terra_pair uuid NOT NULL,
            offered_token uuid NOT NULL,
            asked_token uuid NOT NULL,
            price numeric NOT NULL,
            amount numeric NOT NULL,
            transaction_hash varchar NOT NULL,
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
             REFERENCES public.terra_tokens (id)
        );
        '''
        psql = PostgresSqlConnector()
        psql.create(create_)

        create_ = f'''
        CREATE UNIQUE INDEX IF NOT EXISTS {TRANSACTIONS_TABLE}_unique_idx_1
        ON public.{TRANSACTIONS_TABLE}(transaction_hash);'''
        psql = PostgresSqlConnector()
        psql.create(create_)
