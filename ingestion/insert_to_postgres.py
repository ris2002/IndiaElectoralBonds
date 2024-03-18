import os
import pandas as pd
import numpy as np
import psycopg2

from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def import_donor_data():
  
    df = pd.read_csv('./data/donors.csv')

    # Cleanup data
    df['purchase_date'] = pd.to_datetime(df['p_date'].astype(str).str.split().str.get(0)).dt.date
    df['year'] = df['purchase_date'].astype(str).apply(lambda date_string: (datetime.strptime(date_string, '%Y-%m-%d').year))
    df['month'] = df['purchase_date'].astype(str).apply(lambda date_string: (datetime.strptime(date_string, '%Y-%m-%d').month))
    df['date'] = df['purchase_date'].astype(str).apply(lambda date_string: (datetime.strptime(date_string, '%Y-%m-%d').day))
    df['denomination'] = df['denomination'].astype(int)
    df = df.replace({np.nan: None})

    # Get a connection to Postgres
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USERNAME"),
        password=os.getenv("DB_PASSWORD")
    )

    conn.autocommit = True
    cursor = conn.cursor()

    query = """INSERT INTO donor (p_date, donor_name, denomination, purchase_date, year, month, date) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)"""
    query = ' '.join(query.split('\n'))

    for index, row in df.iterrows():
        values = (row['p_date'], row['donor_name'], row['denomination'], row['purchase_date'], row['year'], row['month'], row['date'])
        cursor.execute(query, values)
        conn.commit()

    conn.close()


def import_party_data():
    df = pd.read_csv('./data/parties.csv')

    # Cleanup data
    df['encashment_date'] = pd.to_datetime(df['e_date'].astype(str).str.split().str.get(0)).dt.date
    df['year'] = df['encashment_date'].astype(str).apply(lambda date_string: (datetime.strptime(date_string, '%Y-%m-%d').year))
    df['month'] = df['encashment_date'].astype(str).apply(lambda date_string: (datetime.strptime(date_string, '%Y-%m-%d').month))
    df['date'] = df['encashment_date'].astype(str).apply(lambda date_string: (datetime.strptime(date_string, '%Y-%m-%d').day))
    df['denomination'] = df['denomination'].astype(int)
    df = df.replace({np.nan: None})

    # Get a connection to Postgres
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USERNAME"),
        password=os.getenv("DB_PASSWORD")
    )

    conn.autocommit = True
    cursor = conn.cursor()

    query = """INSERT INTO party (e_date, party_name, denomination, encashment_date, year, month, date) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)"""
    query = ' '.join(query.split('\n'))

    for index, row in df.iterrows():
        values = (row['e_date'], row['party_name'], row['denomination'], row['encashment_date'], row['year'], row['month'], row['date'])
        cursor.execute(query, values)
        conn.commit()

    conn.close()


import_donor_data()
import_party_data()


