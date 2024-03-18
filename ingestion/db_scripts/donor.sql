CREATE TABLE donor (
  id serial PRIMARY KEY,
  donor_name varchar(500) NOT NULL DEFAULT '',
  purchase_date date,
  denomination integer,
  p_date varchar(50),
  year smallint,
  month smallint,
  date smallint
);

