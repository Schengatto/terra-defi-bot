ALTER TABLE price_monitors
ADD COLUMN reliability smallint NOT NULL DEFAULT -1;

ALTER TABLE orders
ADD COLUMN description varchar;

ALTER TABLE transactions
ADD COLUMN created timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE positions
ADD COLUMN trailing_stop_loss boolean NOT NULL DEFAULT FALSE;

ALTER TABLE transactions
ADD COLUMN order_id uuid;