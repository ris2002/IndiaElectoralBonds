CREATE TABLE user_question
(
    id serial PRIMARY KEY,
    user_question varchar(4000) NOT NULL DEFAULT '',
    standardised_question varchar(4000),
    sql_query varchar(2000),
    final_response varchar(8000),
    insert_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)