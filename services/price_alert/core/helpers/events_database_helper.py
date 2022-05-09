from core.connectors.postgresql_connector import PostgresSqlConnector

EVENT_TYPES_TABLE = "event_types"
EVENTS_TABLE = "events"


class EventsDatabaseHelper:
    def __init__(self):
        self.__init_database()

    def __init_database(self):
        self.__create_tables()
        self.__populate_event_types_table()

    def __create_tables(self):
        create_ = f'''
        CREATE TABLE IF NOT EXISTS public.{EVENT_TYPES_TABLE}
        (
            id uuid NOT NULL DEFAULT uuid_generate_v4(),
            name varchar NOT NULL,
            description varchar,
            lock_duration numeric,
            updated timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT "{EVENT_TYPES_TABLE}_pk" PRIMARY KEY (id)
        );'''
        psql = PostgresSqlConnector()
        psql.create(create_)

        create_ = f'''
        CREATE UNIQUE INDEX IF NOT EXISTS {EVENT_TYPES_TABLE}_unique_idx_1
        ON public.{EVENT_TYPES_TABLE}(name);'''
        psql = PostgresSqlConnector()
        psql.create(create_)

        create_ = f'''
        CREATE TABLE IF NOT EXISTS public.{EVENTS_TABLE}
        (
            id uuid NOT NULL DEFAULT uuid_generate_v4(),
            type uuid NOT NULL,
            name varchar NOT NULL,
            symbol varchar NOT NULL,
            message varchar NOT NULL,
            updated timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT "events_pk" PRIMARY KEY (id),
            CONSTRAINT {EVENTS_TABLE}_fk_symbol
             foreign key (type)
             REFERENCES public.{EVENT_TYPES_TABLE} (id)
        );'''
        psql = PostgresSqlConnector()
        psql.create(create_)

    def __populate_event_types_table(self):
        insert_ = f'''
        INSERT INTO public.{EVENT_TYPES_TABLE} (name, description, lock_duration) VALUES ('PRICE_STATISTICS', 'Statistics about the coin price in a specific timeframe', 1140) ON CONFLICT DO NOTHING;
        INSERT INTO public.{EVENT_TYPES_TABLE} (name, description, lock_duration) VALUES ('PRICE_DAILY_PERFORMANCE', '% value of the price performance in the last 24h', 480) ON CONFLICT DO NOTHING;
        INSERT INTO public.{EVENT_TYPES_TABLE} (name, description, lock_duration) VALUES ('PRICE_SUPPORT_LEVEL', 'The price is close a support level', 120) ON CONFLICT DO NOTHING;
        INSERT INTO public.{EVENT_TYPES_TABLE} (name, description, lock_duration) VALUES ('PRICE_RESISTANCE_LEVEL', 'The price is close a resistance level', 120) ON CONFLICT DO NOTHING;
        INSERT INTO public.{EVENT_TYPES_TABLE} (name, description, lock_duration) VALUES ('PRICE_IS_LOW', 'The current price is low', 720) ON CONFLICT DO NOTHING;
        INSERT INTO public.{EVENT_TYPES_TABLE} (name, description, lock_duration) VALUES ('PRICE_IS_HIGH', 'The current price is high', 720) ON CONFLICT DO NOTHING;
        INSERT INTO public.{EVENT_TYPES_TABLE} (name, description, lock_duration) VALUES ('ORDER_PRICE_WARN', 'The current price is high', null) ON CONFLICT DO NOTHING;
        INSERT INTO public.{EVENT_TYPES_TABLE} (name, description, lock_duration) VALUES ('ORDER_TRADE_BUY', 'The current price is high', null) ON CONFLICT DO NOTHING;
        INSERT INTO public.{EVENT_TYPES_TABLE} (name, description, lock_duration) VALUES ('ORDER_TRADE_SELL', 'The current price is high', null) ON CONFLICT DO NOTHING;
        INSERT INTO public.{EVENT_TYPES_TABLE} (name, description, lock_duration) VALUES ('ERROR', 'Application Error', null) ON CONFLICT DO NOTHING;
        '''
        psql = PostgresSqlConnector()
        psql.insert(insert_)
