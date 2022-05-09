CREATE TABLE IF NOT EXISTS public.terra_tokens
(
    id uuid NOT NULL DEFAULT uuid_generate_v4(),
    name varchar NOT NULL,
    symbol varchar NOT NULL,
    decimal_digits numeric NOT NULL,
    protocol varchar,
    icon varchar,
    mainnet_contract varchar NOT NULL,
    testnet_contract varchar,
    is_native boolean NOT NULL,
    updated timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "terra_tokens_pk" PRIMARY KEY (id)
);

CREATE UNIQUE INDEX IF NOT EXISTS terra_tokens_unique_idx_1
ON public.terra_tokens(name);
CREATE UNIQUE INDEX IF NOT EXISTS terra_tokens_unique_idx_2
ON public.terra_tokens(symbol);
CREATE UNIQUE INDEX IF NOT EXISTS terra_tokens_unique_idx_3
ON public.terra_tokens(mainnet_contract);
CREATE UNIQUE INDEX IF NOT EXISTS terra_tokens_unique_idx_4
ON public.{TERRA_TOKENS_TABLE}(mainnet_contract,testnet_contract);


CREATE TABLE IF NOT EXISTS public.terra_pairs
(
   id uuid NOT NULL DEFAULT uuid_generate_v4(),
   name varchar NOT NULL,
   asset1 uuid NOT NULL,
   asset2 uuid NOT NULL,
   mainnet_contract varchar NOT NULL,
   testnet_contract varchar,
   protocol varchar NOT NULL,
   updated timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
   CONSTRAINT "terra_pairs_pk" PRIMARY KEY (id),
   CONSTRAINT terra_pairs_fk_asset1
    foreign key (asset1)
    REFERENCES public.terra_tokens (id),
   CONSTRAINT terra_pairs_fk_asset2
    foreign key (asset2)
    REFERENCES public.terra_tokens (id)
);

CREATE UNIQUE INDEX IF NOT EXISTS terra_pairs_unique_idx_1
ON public.terra_pairs(asset1, asset2, protocol);
CREATE UNIQUE INDEX IF NOT EXISTS terra_pairs_unique_idx_2
ON public.terra_pairs(mainnet_contract);
CREATE UNIQUE INDEX IF NOT EXISTS terra_pairs_unique_idx_3
ON public.terra_pairs(mainnet_contract, testnet_contract);
                    
                    
CREATE TABLE IF NOT EXISTS public.price_providers
(
    id uuid NOT NULL DEFAULT uuid_generate_v4(),
    name varchar NOT NULL,
	active boolean NOT NULL DEFAULT true,
	updated timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "price_providers_pk" PRIMARY KEY (id)
);

CREATE UNIQUE INDEX IF NOT EXISTS price_providers_unique_idx_1
ON public.price_providers(name);


CREATE TABLE IF NOT EXISTS public.price_symbols
(
    id uuid NOT NULL DEFAULT uuid_generate_v4(),
    name varchar NOT NULL,
	price_provider uuid NOT NULL,
	terra_pair uuid,
	ask_token uuid,
	active boolean NOT NULL DEFAULT true,
	updated timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "price_symbols_pk" PRIMARY KEY (id),
    CONSTRAINT price_symbols_fk_provider
     foreign key (price_provider)
     REFERENCES public.price_providers (id),
    CONSTRAINT price_symbols_fk_terra_pair
     foreign key (terra_pair)
     REFERENCES public.terra_pairs (id),
    CONSTRAINT price_symbols_fk_ask_token
     foreign key (ask_token)
     REFERENCES public.terra_tokens (id)
);

CREATE UNIQUE INDEX IF NOT EXISTS price_symbols_unique_idx_1
ON public.price_symbols(name, price_provider, terra_pair);


CREATE TABLE IF NOT EXISTS public.price_monitors
(
    id uuid NOT NULL DEFAULT uuid_generate_v4(),
    price_symbol uuid NOT NULL,
    name varchar NOT NULL,
	active boolean NOT NULL DEFAULT true,
	reliability smallint NOT NULL DEFAULT -1,
	updated timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "price_monitors_pk" PRIMARY KEY (id),
    CONSTRAINT price_monitors_fk_price_symbol
     foreign key (price_symbol)
     REFERENCES public.price_symbols (id)
);

CREATE UNIQUE INDEX IF NOT EXISTS price_monitors_unique_idx_1
ON public.price_monitors(price_symbol);


CREATE TABLE IF NOT EXISTS public.orders
(
    id uuid NOT NULL DEFAULT uuid_generate_v4(),
    terra_pair uuid NOT NULL,
    terra_token uuid NOT NULL,
	type varchar NOT NULL,
	price numeric NOT NULL,
	amount numeric,
	retries smallint DEFAULT 0,
	status varchar NOT NULL,
	description varchar,
	updated timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "orders_pk" PRIMARY KEY (id),
    CONSTRAINT orders_fk_terra_pair
     foreign key (terra_pair)
     REFERENCES public.terra_pairs (id),
    CONSTRAINT orders_fk_terra_tokens
     foreign key (terra_token)
     REFERENCES public.terra_tokens (id)
);


CREATE TABLE IF NOT EXISTS public.event_types
(
    id uuid NOT NULL DEFAULT uuid_generate_v4(),
	name varchar NOT NULL,
	description varchar,
	lock_duration numeric,
	updated timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "event_types_pk" PRIMARY KEY (id)
);

CREATE UNIQUE INDEX IF NOT EXISTS event_types_unique_idx_1
ON public.event_types(name);


CREATE TABLE IF NOT EXISTS public.events
        (
            id uuid NOT NULL DEFAULT uuid_generate_v4(),
            type uuid NOT NULL,
            name varchar NOT NULL,
            symbol varchar NOT NULL,
            message varchar NOT NULL,
            updated timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT "events_pk" PRIMARY KEY (id),
            CONSTRAINT events_fk_symbol
             foreign key (type)
             REFERENCES public.event_types (id)
        );


CREATE TABLE IF NOT EXISTS public.transactions
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
    CONSTRAINT "transactions_pk" PRIMARY KEY (id),
    CONSTRAINT transactions_fk_terra_pair
     foreign key (terra_pair)
     REFERENCES public.terra_pairs (id),
    CONSTRAINT transactions_fk_terra_tokens1
     foreign key (offered_token)
     REFERENCES public.terra_tokens (id),
    CONSTRAINT transactions_fk_terra_tokens2
     foreign key (asked_token)
     REFERENCES public.terra_tokens (id),
    CONSTRAINT transactions_fk_orders
     foreign key (order_id)
     REFERENCES public.orders (id)
);

CREATE UNIQUE INDEX IF NOT EXISTS transactions_unique_idx_1
ON public.transactions(transaction_hash);

CREATE INDEX IF NOT EXISTS transactions_unique_idx_2
ON public.transactions(order_id);


CREATE TABLE IF NOT EXISTS public.positions
(
    id uuid NOT NULL DEFAULT uuid_generate_v4(),
	terra_pair uuid NOT NULL,
    terra_token uuid NOT NULL,
	open_transaction uuid NOT NULL,
	close_transaction uuid,
	stop_loss_price numeric,
	trailing_stop_loss boolean NOT NULL default FALSE,
	take_profit_price numeric,
	created timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
	updated timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "positions_pk" PRIMARY KEY (id),
    CONSTRAINT positions_fk_terra_pairs
     foreign key (terra_pair)
     REFERENCES public.terra_pairs (id),
    CONSTRAINT positions_fk_terra_tokens
     foreign key (terra_token)
     REFERENCES public.terra_tokens (id),
    CONSTRAINT positions_fk_transactions1
     foreign key (open_transaction)
     REFERENCES public.transactions (id)
    CONSTRAINT positions_fk_transactions2
     foreign key (close_transaction)
     REFERENCES public.transactions (id)
);


