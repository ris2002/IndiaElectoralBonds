CREATE TABLE party (
  id serial PRIMARY KEY,
  party_name varchar(500) NOT NULL DEFAULT '',
  encashment_date date,
  denomination bigint,
  e_date varchar(50),
  year smallint,
  month smallint,
  date smallint
);