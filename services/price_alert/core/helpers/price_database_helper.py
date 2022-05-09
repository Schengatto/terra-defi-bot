from core.connectors.postgresql_connector import PostgresSqlConnector

PRICE_PROVIDERS = "price_providers"
PRICE_SYMBOLS = "price_symbols"
PRICE_MONITORS = "price_monitors"


class PriceDatabaseHelper:
    def __init__(self):
        self.__init_database()

    def __init_database(self):
        self.__create_tables()
        self.__populate_tables()

    def __create_tables(self):
        create_ = f'''
        CREATE TABLE IF NOT EXISTS public.{PRICE_PROVIDERS}
        (
            id uuid NOT NULL DEFAULT uuid_generate_v4(),
            name varchar NOT NULL,
            active boolean NOT NULL DEFAULT true,
            updated timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT "{PRICE_PROVIDERS}_pk" PRIMARY KEY (id)
        );'''
        psql = PostgresSqlConnector()
        psql.create(create_)

        create_ = f'''
        CREATE UNIQUE INDEX IF NOT EXISTS {PRICE_PROVIDERS}_unique_idx_1
        ON public.{PRICE_PROVIDERS}(name);'''
        psql = PostgresSqlConnector()
        psql.create(create_)

        create_ = f'''
        CREATE TABLE IF NOT EXISTS public.{PRICE_SYMBOLS}
        (
            id uuid NOT NULL DEFAULT uuid_generate_v4(),
            name varchar NOT NULL,
            price_provider uuid NOT NULL,
            terra_pair uuid,
            ask_token uuid,
            active boolean NOT NULL DEFAULT true,
            updated timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT "{PRICE_SYMBOLS}_pk" PRIMARY KEY (id),
            CONSTRAINT {PRICE_SYMBOLS}_fk_provider
             foreign key (price_provider)
             REFERENCES public.{PRICE_PROVIDERS} (id),
            CONSTRAINT {PRICE_SYMBOLS}_fk_terra_pair
             foreign key (terra_pair)
             REFERENCES public.terra_pairs (id),
            CONSTRAINT {PRICE_SYMBOLS}_fk_ask_token
             foreign key (ask_token)
             REFERENCES public.terra_tokens (id)
        );'''
        psql = PostgresSqlConnector()
        psql.create(create_)

        create_ = f'''
        CREATE UNIQUE INDEX IF NOT EXISTS {PRICE_SYMBOLS}_unique_idx_1
        ON public.{PRICE_SYMBOLS}(name, price_provider, terra_pair);'''
        psql = PostgresSqlConnector()
        psql.create(create_)

        create_ = f'''
        CREATE TABLE IF NOT EXISTS public.{PRICE_MONITORS}
        (
            id uuid NOT NULL DEFAULT uuid_generate_v4(),
            price_symbol uuid NOT NULL,
            name varchar NOT NULL,
            active boolean NOT NULL DEFAULT true,
            reliability smallint NOT NULL DEFAULT -1,
            updated timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT "{PRICE_MONITORS}_pk" PRIMARY KEY (id),
            CONSTRAINT {PRICE_MONITORS}_fk_price_symbol
             foreign key (price_symbol)
             REFERENCES public.{PRICE_SYMBOLS} (id)
        );'''
        psql = PostgresSqlConnector()
        psql.create(create_)

        create_ = f'''
        CREATE UNIQUE INDEX IF NOT EXISTS {PRICE_MONITORS}_unique_idx_1
        ON public.{PRICE_MONITORS}(price_symbol);'''
        psql = PostgresSqlConnector()
        psql.create(create_)

    def __populate_tables(self):
        insert_ = f'''
        INSERT INTO public.{PRICE_PROVIDERS}(name, active) VALUES ('binance_spot', true) ON CONFLICT DO NOTHING;
        INSERT INTO public.{PRICE_PROVIDERS}(name, active) VALUES ('coingecko', true) ON CONFLICT DO NOTHING;
        '''
        psql = PostgresSqlConnector()
        psql.insert(insert_)

        insert_ = f'''
        INSERT INTO public.price_symbols(name, price_provider, terra_pair, ask_token)
        VALUES (
         'LUNAUST',
         (select id from public.price_providers where name = 'binance_spot'),
         (select id from public.terra_pairs where name = 'UST-Luna'),
         (select id from public.terra_tokens where symbol = 'Luna')
        ) ON CONFLICT DO NOTHING;

        INSERT INTO public.price_symbols(name, price_provider, terra_pair, ask_token)
        VALUES (
         'LUNAUSDT',
         (select id from public.price_providers where name = 'binance_spot'),
         (select id from public.terra_pairs where name = 'UST-Luna'),
         (select id from public.terra_tokens where symbol = 'Luna')
        ) ON CONFLICT DO NOTHING;

        INSERT INTO public.price_symbols(name, price_provider, terra_pair, ask_token)
        VALUES (
         'ANCUSDT',
         (select id from public.price_providers where name = 'binance_spot'),
         (select id from public.terra_pairs where name = 'ANC-UST'),
         (select id from public.terra_tokens where symbol = 'ANC')
        ) ON CONFLICT DO NOTHING;

        INSERT INTO public.price_symbols(name, price_provider, terra_pair, ask_token)
        VALUES (
         'MIRUSDT',
         (select id from public.price_providers where name = 'binance_spot'),
         (select id from public.terra_pairs where name = 'UST-MIR'),
         (select id from public.terra_tokens where symbol = 'MIR')
        ) ON CONFLICT DO NOTHING;
        '''
        psql = PostgresSqlConnector()
        psql.insert(insert_)

        insert_ = f'''
        INSERT INTO public.price_monitors(price_symbol, name)
        VALUES ((select id from public.price_symbols where name = 'LUNAUST'), 'LUNAUST-binance_spot') ON CONFLICT DO NOTHING;

        INSERT INTO public.price_monitors(price_symbol, name)
        VALUES ((select id from public.price_symbols where name = 'LUNAUSDT'), 'LUNAUSDT-binance_spot') ON CONFLICT DO NOTHING;

        INSERT INTO public.price_monitors(price_symbol, name)
        VALUES ((select id from public.price_symbols where name = 'ANCUSDT'), 'ANCUST-binance_spot') ON CONFLICT DO NOTHING;

        INSERT INTO public.price_monitors(price_symbol, name)
        VALUES ((select id from public.price_symbols where name = 'MIRUSDT'), 'MIRUST-binance_spot') ON CONFLICT DO NOTHING;
        '''
        psql = PostgresSqlConnector()
        psql.insert(insert_)

