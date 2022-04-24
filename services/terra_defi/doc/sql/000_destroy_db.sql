DROP TABLE IF EXISTS events;
DROP TABLE IF EXISTS event_types;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS price_monitors;
DROP TABLE IF EXISTS price_symbols;
DROP TABLE IF EXISTS price_providers;
DROP TABLE IF EXISTS terra_pairs;
DROP TABLE IF EXISTS terra_tokens;

DROP DATABASE IF EXISTS terra_defi;


CREATE DATABASE terra_defi
    WITH
    OWNER = terra_defi_db_user
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.utf8'
    LC_CTYPE = 'en_US.utf8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" SCHEMA public;

Do
$do$
BEGIN
  IF NOT EXISTS (SELECT * FROM pg_user WHERE username = 'terra_defi_db_user')then
      CREATE USER terra_defi_db_user WITH ENCRYPTED PASSWORD '???';
      GRANT ALL PRIVILEGES ON DATABASE terra_defi TO terra_defi_db_user;
   END IF;
end
$do$