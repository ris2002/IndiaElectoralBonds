CREATE TABLE party_master (
  id serial PRIMARY KEY,
  party_code varchar(10) NOT NULL DEFAULT '',
  party_name varchar(500) NOT NULL DEFAULT ''
);