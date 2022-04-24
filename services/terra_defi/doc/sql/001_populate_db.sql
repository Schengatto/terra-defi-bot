INSERT INTO public.event_types (name, description, lock_duration) VALUES ('PRICE_STATISTICS', 'Statistics about the coin price in a specific timeframe', 1140) ON CONFLICT DO NOTHING;
INSERT INTO public.event_types (name, description, lock_duration) VALUES ('PRICE_DAILY_PERFORMANCE', '% value of the price performance in the last 24h', 480) ON CONFLICT DO NOTHING;
INSERT INTO public.event_types (name, description, lock_duration) VALUES ('PRICE_SUPPORT_LEVEL', 'The price is close a support level', 120) ON CONFLICT DO NOTHING;
INSERT INTO public.event_types (name, description, lock_duration) VALUES ('PRICE_RESISTANCE_LEVEL', 'The price is close a resistance level', 120) ON CONFLICT DO NOTHING;
INSERT INTO public.event_types (name, description, lock_duration) VALUES ('PRICE_IS_LOW', 'The current price is low', 720) ON CONFLICT DO NOTHING;
INSERT INTO public.event_types (name, description, lock_duration) VALUES ('PRICE_IS_HIGH', 'The current price is high', 720) ON CONFLICT DO NOTHING;
INSERT INTO public.event_types (name, description, lock_duration) VALUES ('ORDER_PRICE_WARN', 'The current price is high', null) ON CONFLICT DO NOTHING;
INSERT INTO public.event_types (name, description, lock_duration) VALUES ('ORDER_TRADE_BUY', 'The current price is high', null) ON CONFLICT DO NOTHING;
INSERT INTO public.event_types (name, description, lock_duration) VALUES ('ORDER_TRADE_SELL', 'The current price is high', null) ON CONFLICT DO NOTHING;
INSERT INTO public.event_types (name, description, lock_duration) VALUES ('ERROR', 'Application Error', null) ON CONFLICT DO NOTHING;

INSERT INTO public.price_providers(name, active) VALUES ('binance_spot', true) ON CONFLICT DO NOTHING;
INSERT INTO public.price_providers(name, active) VALUES ('coingecko', true) ON CONFLICT DO NOTHING;

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

INSERT INTO public.price_symbols(name, price_provider, terra_pair, ask_token)
VALUES(
 'mad-meerkat-optimizer',
 (select id from public.price_providers where name = 'coingecko'),
 null,
 null
) ON CONFLICT DO NOTHING;

INSERT INTO public.price_symbols(name, price_provider, terra_pair, ask_token)
VALUES(
 'crypto-com-chain',
 (select id from public.price_providers where name = 'coingecko'),
 null,
 null
) ON CONFLICT DO NOTHING;

INSERT INTO public.price_symbols(name, price_provider, terra_pair, ask_token)
VALUES(
 'lunaverse',
 (select id from public.price_providers where name = 'coingecko'),
 (select id from public.terra_pairs where name = 'LUV-UST'),
 (select id from public.terra_tokens where symbol = 'LUV')
) ON CONFLICT DO NOTHING;

INSERT INTO public.price_symbols(name, price_provider, terra_pair, ask_token)
VALUES(
 'terra-world-token',
 (select id from public.price_providers where name = 'coingecko'),
 (select id from public.terra_pairs where name = 'TWD-UST'),
 (select id from public.terra_tokens where symbol = 'TWD')
) ON CONFLICT DO NOTHING;

INSERT INTO public.price_symbols(name, price_provider, terra_pair, ask_token)
VALUES(
 'mars-protocol',
 (select id from public.price_providers where name = 'coingecko'),
 (select id from public.terra_pairs where name = 'MARS-UST'),
 (select id from public.terra_tokens where symbol = 'MARS')
) ON CONFLICT DO NOTHING;

INSERT INTO public.price_symbols(name, price_provider, terra_pair, ask_token)
VALUES(
 'kujira',
 (select id from public.price_providers where name = 'coingecko'),
 (select id from public.terra_pairs where name = 'KUJI-UST'),
 (select id from public.terra_tokens where symbol = 'KUJI')
) ON CONFLICT DO NOTHING;

INSERT INTO public.price_symbols(name, price_provider, terra_pair, ask_token)
VALUES(
 'astroport',
 (select id from public.price_providers where name = 'coingecko'),
 (select id from public.terra_pairs where name = 'ASTRO-UST'),
 (select id from public.terra_tokens where symbol = 'ASTRO')
) ON CONFLICT DO NOTHING;

INSERT INTO public.price_monitors(price_symbol, name)
VALUES ((select id from public.price_symbols where name = 'astroport'), 'astroport-coingecko') ON CONFLICT DO NOTHING;

INSERT INTO public.price_monitors(price_symbol, name)
VALUES ((select id from public.price_symbols where name = 'kujira'), 'kujira-protocol-coingecko') ON CONFLICT DO NOTHING;

INSERT INTO public.price_monitors(price_symbol, name)
VALUES ((select id from public.price_symbols where name = 'mars-protocol'), 'mars-protocol-coingecko') ON CONFLICT DO NOTHING;

INSERT INTO public.price_monitors(price_symbol, name)
VALUES ((select id from public.price_symbols where name = 'terra-world-token'), 'terra-world-token-coingecko') ON CONFLICT DO NOTHING;

INSERT INTO public.price_monitors(price_symbol, name)
VALUES ((select id from public.price_symbols where name = 'lunaverse'), 'lunaverse-coingecko') ON CONFLICT DO NOTHING;

INSERT INTO public.price_monitors(price_symbol, name)
VALUES ((select id from public.price_symbols where name = 'crypto-com-chain'), 'crypto-com-chain-coingecko') ON CONFLICT DO NOTHING;

INSERT INTO public.price_monitors(price_symbol, name)
VALUES ((select id from public.price_symbols where name = 'mad-meerkat-optimizer'), 'mad-meerkat-optimizer-coingecko') ON CONFLICT DO NOTHING;

INSERT INTO public.price_monitors(price_symbol, name)
VALUES ((select id from public.price_symbols where name = 'LUNAUST'), 'LUNAUST-binance_spot') ON CONFLICT DO NOTHING;

INSERT INTO public.price_monitors(price_symbol, name)
VALUES ((select id from public.price_symbols where name = 'LUNAUSDT'), 'LUNAUSDT-binance_spot') ON CONFLICT DO NOTHING;

INSERT INTO public.price_monitors(price_symbol, name)
VALUES ((select id from public.price_symbols where name = 'ANCUSDT'), 'ANCUST-binance_spot') ON CONFLICT DO NOTHING;

INSERT INTO public.price_monitors(price_symbol, name)
VALUES ((select id from public.price_symbols where name = 'MIRUSDT'), 'MIRUST-binance_spot') ON CONFLICT DO NOTHING;


--INSERT INTO public.price_symbols(name, price_provider, terra_pair, ask_token)
--VALUES(
-- 'robohero',
-- (select id from public.price_providers where name = 'coingecko'),
-- (select id from public.terra_pairs where name = 'ROBO-UST'),
-- (select id from public.terra_tokens where symbol = 'ROBO')
--) ON CONFLICT DO NOTHING;

-- INSERT INTO public.price_monitors(price_symbol, name)
-- VALUES ((select id from public.price_symbols where name = 'robohero'), 'robohero-coingecko') ON CONFLICT DO NOTHING;