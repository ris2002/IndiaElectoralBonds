CREATE TABLE donor_master (
  id serial PRIMARY KEY,
  donor_name varchar(500) NOT NULL DEFAULT '',
  donor_type varchar(50),
  registration_state varchar(50),
  nature_of_business varchar(5000) 
);

INSERT INTO donor_master (donor_name)
SELECT DISTINCT donor_name
FROM donor;