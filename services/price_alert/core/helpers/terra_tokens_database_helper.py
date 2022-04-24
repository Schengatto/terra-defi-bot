import json

import requests
from core.connectors.postgresql_connector import PostgresSqlConnector

TERRA_TOKENS_TABLE = "terra_tokens"
TERRA_PAIRS_TABLE = "terra_pairs"

TERRA_MONEY_CW20_TOKENS = "https://raw.githubusercontent.com/terra-money/assets/master/cw20/tokens.js"
TERRA_MONEY_CW20_PAIRS = "https://raw.githubusercontent.com/terra-money/assets/master/cw20/pairs.js"
TERRA_CW20_TERRA_SWAP_TOKENS = "https://api.terraswap.io/tokens"
TERRA_CW20_TERRA_SWAP_PAIRS = "https://api.terraswap.io/pairs"
TERRA_NATIVE_COINS = ['uaud', 'ucad', 'uchf', 'ucny', 'udkk', 'ueur', 'ugbp', 'uhkd', 'uidr', 'uinr', 'ujpy', 'ukrw',
                      'umnt', 'umyr', 'unok', 'uphp', 'usdr', 'usek', 'usgd', 'uthb', 'utwd', 'uusd', 'uluna']


def fix_element(elem):
    if elem[-1] == ':':
        return '"{}":'.format(elem[:-1])
    else:
        return elem


class TerraTokensDatabaseHelper:
    def __init__(self):
        self._mainnet_tokens, self._testnet_tokens = self.__load_terra_money_tokens()
        self._terra_money_pairs_mainnet, self._terra_money_pairs_testnet = self.__load_terra_money_pairs()
        self._terra_swap_tokens = self.__load_terra_swap_tokens()
        self._supported_tokens = self.__load_supported_tokens()
        self._terra_swap_pairs = self.__load_terra_swap_pairs_mainnet()
        self.__init_database()

    def generate_tokens_db_inserts(self):
        inserts = []
        for model in self._supported_tokens:
            insert = f'''
            INSERT INTO {TERRA_TOKENS_TABLE}(name, symbol, decimal_digits, protocol, icon, mainnet_contract, testnet_contract, is_native)
            VALUES(
                '{model["name"]}',
                '{model["symbol"]}',
                {model['decimal_digits']},
                '{model["protocol"]}',
                '{model["icon"]}',
                '{model["mainnet_contract"]}',
                '{model["testnet_contract"]}',
                {model["is_native"]}
            ) ON CONFLICT DO NOTHING;'''
            inserts.append(insert)
        return inserts

    def generate_pairs_db_inserts(self):
        inserts = []
        for model in self._terra_swap_pairs:
            insert = f'''
            INSERT INTO {TERRA_PAIRS_TABLE}(name, asset1, asset2, mainnet_contract, testnet_contract, protocol)
            VALUES(
                '{model["name"]}',
                (SELECT id FROM {TERRA_TOKENS_TABLE} where mainnet_contract = '{model["asset1"]}'),
                (SELECT id FROM {TERRA_TOKENS_TABLE} where mainnet_contract = '{model["asset2"]}'),
                '{model["mainnet_contract"]}',
                '{model["testnet_contract"]}',
                '{model["protocol"]}'
            ) ON CONFLICT DO NOTHING;'''
            inserts.append(insert)
        return inserts

    def get_native_tokens(self):
        return TERRA_NATIVE_COINS;

    def __load_terra_money_tokens(self):
        terra_coins = requests.get(TERRA_MONEY_CW20_TOKENS)
        postString = "{\n" + terra_coins.text.split("\n", 1)[1]
        x = postString.replace("\'", '"')

        fixed_elem = [fix_element(elem) for elem in x.split()]
        fixed_text = ''.join(fixed_elem)
        fixed_text = fixed_text.replace(",}", '}')
        fixed_text = fixed_text.replace(",]", ']')

        cw20_tokens_json = json.loads(fixed_text)
        return cw20_tokens_json["mainnet"], cw20_tokens_json["testnet"]

    def __load_terra_money_pairs(self):
        terra_coins = requests.get(TERRA_MONEY_CW20_PAIRS)
        postString = "{\n" + terra_coins.text.split("\n", 1)[1]
        x = postString.replace("\'", '"')

        fixed_elem = [fix_element(elem) for elem in x.split()]
        fixed_text = ''.join(fixed_elem)
        fixed_text = fixed_text.replace(",}", '}')
        fixed_text = fixed_text.replace(",]", ']')

        cw20_tokens_json = json.loads(fixed_text)
        mainnet_pairs = []
        for pair in cw20_tokens_json["mainnet"]:
            mainnet_pairs.append(("-".join(cw20_tokens_json["mainnet"][pair]), pair))

        testnet_pairs = []
        for pair in cw20_tokens_json["testnet"]:
            testnet_pairs.append(("-".join(cw20_tokens_json["testnet"][pair]), pair))

        return mainnet_pairs, testnet_pairs

    def __load_terra_swap_tokens(self):
        tokens = requests.get(TERRA_CW20_TERRA_SWAP_TOKENS).json()
        # filter only verified tokens
        result = filter(lambda t: t is not None and 'verified' in t and t['verified'], tokens)
        return list(result)

    def __get_terra_swap_token(self, contract_address: str):
        for terra_swap_token in self._terra_swap_tokens:
            if terra_swap_token['contract_addr'] == contract_address:
                return terra_swap_token
        return None

    def __get_token_testnet_contract(self, symbol: str):
        for testnet_token in self._testnet_tokens:
            if self._testnet_tokens[testnet_token]['symbol'] == symbol:
                return self._testnet_tokens[testnet_token]["token"]
        return None

    def __map_terra_money_info_to_token_model(self, terra_money_info, terra_swap_info):
        testnet_contract = self.__get_token_testnet_contract(terra_money_info['symbol'])
        return {
            "name": terra_money_info['name'] if 'name' in terra_money_info is not None else terra_money_info['symbol'],
            "symbol": terra_money_info['symbol'],
            "protocol": terra_money_info['protocol'] if 'protocol' in terra_money_info is not None else None,
            "decimal_digits": terra_swap_info['decimals'],
            "icon": terra_money_info['icon'] if 'icon' in terra_money_info is not None else None,
            "mainnet_contract": terra_money_info['token'],
            "testnet_contract": testnet_contract,
            "is_native": 'name' in terra_money_info and terra_money_info['name'] in TERRA_NATIVE_COINS
        }

    def __map_terra_swap_info_to_token_model(self, terra_swap_info):
        return {
            "name": terra_swap_info['name'],
            "symbol": terra_swap_info['symbol'],
            "protocol": None,
            "decimal_digits": terra_swap_info['decimals'],
            "icon": terra_swap_info['icon'],
            "mainnet_contract": terra_swap_info['contract_addr'],
            "testnet_contract": None,
            "is_native": terra_swap_info['name'] in TERRA_NATIVE_COINS
        }

    def __load_supported_tokens(self):
        supported_token = []
        for token in self._mainnet_tokens:
            t_info1 = self._mainnet_tokens[token]
            t_info2 = self.__get_terra_swap_token(token)
            if t_info2 is not None and 'decimals' in t_info2:
                supported_token.append(self.__map_terra_money_info_to_token_model(t_info1, t_info2))

        for native in TERRA_NATIVE_COINS:
            t_info2 = self.__get_terra_swap_token(native)
            if t_info2 is not None:
                supported_token.append(self.__map_terra_swap_info_to_token_model(t_info2))
        return supported_token

    def __load_terra_swap_pairs_mainnet(self):
        result = []
        pairs = requests.get(TERRA_CW20_TERRA_SWAP_PAIRS).json()['pairs']
        supported_tokens = list(map(lambda t: t['mainnet_contract'], self._supported_tokens))

        for pair in pairs:
            assets = pair['asset_infos']
            asset1 = assets[0]
            asset2 = assets[1]
            if ('native_token' in asset1 or (
                    'token' in asset1 and asset1['token']['contract_addr'] in supported_tokens)) \
                    and ('native_token' in asset2 or (
                    'token' in asset2 and asset2['token']['contract_addr'] in supported_tokens)):
                a1_c = asset1['native_token']['denom'] if 'native_token' in asset1 else asset1['token']['contract_addr']
                a2_c = asset2['native_token']['denom'] if 'native_token' in asset2 else asset2['token']['contract_addr']
                l1 = list(filter(lambda t: t['mainnet_contract'] == a1_c, self._supported_tokens))
                l2 = list(filter(lambda t: t['mainnet_contract'] == a2_c, self._supported_tokens))
                token1 = l1[0] if len(l1) > 0 else None
                token2 = l2[0] if len(l2) > 0 else None
                if token1 is not None and token2 is not None and 'Delisted' not in token1[
                    'symbol'] and 'Delisted' not in token2['symbol']:
                    # find testnet pair address using terra money pairs
                    pair_sym = list(filter(lambda p: p[1] == pair['contract_addr'], self._terra_money_pairs_mainnet))
                    testnet_contract = list(
                        filter(lambda p: p[0] == pair_sym[0], self._terra_money_pairs_testnet)) if len(
                        pair_sym) != 0 else None
                    pair_name = f"{token1['symbol']}-{token2['symbol']}"
                    pair_model = {
                        "name": pair_name,
                        "asset1": token1['mainnet_contract'],
                        "asset2": token2['mainnet_contract'],
                        "mainnet_contract": pair['contract_addr'],
                        "testnet_contract": testnet_contract,
                        "protocol": "terraswap"
                    }
                    result.append(pair_model)

        return result

    def __init_database(self):
        self.__create_tables()
        self.__populate_terra_tokens_table()
        self.__populate_terra_pairs_table()

    def __create_tables(self):
        create_ = f'''
        CREATE TABLE IF NOT EXISTS public.{TERRA_TOKENS_TABLE}
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
           CONSTRAINT "{TERRA_TOKENS_TABLE}_pk" PRIMARY KEY (id)
        );'''
        psql = PostgresSqlConnector()
        psql.create(create_)

        create_ = f'''
        CREATE UNIQUE INDEX IF NOT EXISTS {TERRA_TOKENS_TABLE}_unique_idx_1
        ON public.{TERRA_TOKENS_TABLE}(name);
        CREATE UNIQUE INDEX IF NOT EXISTS {TERRA_TOKENS_TABLE}_unique_idx_2
        ON public.{TERRA_TOKENS_TABLE}(symbol);
        CREATE UNIQUE INDEX IF NOT EXISTS {TERRA_TOKENS_TABLE}_unique_idx_3
        ON public.{TERRA_TOKENS_TABLE}(mainnet_contract);'''
        psql = PostgresSqlConnector()
        psql.create(create_)

        create_ = f'''
        CREATE TABLE IF NOT EXISTS public.{TERRA_PAIRS_TABLE}
        (
          id uuid NOT NULL DEFAULT uuid_generate_v4(),
          name varchar NOT NULL,
          asset1 uuid NOT NULL,
          asset2 uuid NOT NULL,
          mainnet_contract varchar NOT NULL,
          testnet_contract varchar,
          protocol varchar NOT NULL,
          updated timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
          CONSTRAINT "{TERRA_PAIRS_TABLE}_pk" PRIMARY KEY (id),
          CONSTRAINT {TERRA_PAIRS_TABLE}_fk_asset1
           foreign key (asset1)
           REFERENCES public.{TERRA_TOKENS_TABLE} (id),
          CONSTRAINT {TERRA_PAIRS_TABLE}_fk_asset2
           foreign key (asset2)
           REFERENCES public.{TERRA_TOKENS_TABLE} (id)
        );'''
        psql = PostgresSqlConnector()
        psql.create(create_)

        create_ = f'''
        CREATE UNIQUE INDEX IF NOT EXISTS {TERRA_PAIRS_TABLE}_unique_idx_1
        ON public.{TERRA_PAIRS_TABLE}(asset1, asset2, protocol);'''
        psql = PostgresSqlConnector()
        psql.create(create_)

    def __populate_terra_tokens_table(self):
        insert_ = "\n".join(self.generate_tokens_db_inserts())
        psql = PostgresSqlConnector()
        psql.insert(insert_)

    def __populate_terra_pairs_table(self):
        insert_ = "\n".join(self.generate_pairs_db_inserts())
        psql = PostgresSqlConnector()
        psql.insert(insert_)
