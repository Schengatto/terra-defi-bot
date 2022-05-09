from core.connectors.postgresql_connector import PostgresSqlConnector

POSITIONS_TABLE = "positions"


class PositionsDatabaseHelper:
    def __init__(self):
        self.__init_database()

    def __init_database(self):
        self.__create_positions_table__()

    def __create_positions_table__(self):
        create_ = f'''
        CREATE TABLE IF NOT EXISTS public.{POSITIONS_TABLE}
        (
            id uuid NOT NULL DEFAULT uuid_generate_v4(),
            terra_pair uuid NOT NULL,
            terra_token uuid NOT NULL,
            open_transaction uuid NOT NULL,
            close_transaction uuid,
            stop_loss_price numeric,
            trailing_stop_loss boolean NOT NULL DEFAULT FALSE, 
            take_profit_price numeric,
            created timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT "{POSITIONS_TABLE}_pk" PRIMARY KEY (id),
            CONSTRAINT {POSITIONS_TABLE}_fk_terra_pairs
             foreign key (terra_pair)
             REFERENCES public.terra_pairs (id),
            CONSTRAINT {POSITIONS_TABLE}_fk_terra_tokens
             foreign key (terra_token)
             REFERENCES public.terra_tokens (id),
            CONSTRAINT {POSITIONS_TABLE}_fk_transactions1
             foreign key (open_transaction)
             REFERENCES public.transactions (id),
            CONSTRAINT {POSITIONS_TABLE}_fk_transactions2
             foreign key (close_transaction)
             REFERENCES public.transactions (id)
        );
        '''
        psql = PostgresSqlConnector()
        psql.create(create_)
