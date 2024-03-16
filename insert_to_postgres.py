import os
import pandas as pd
import numpy as np
import psycopg2

from dotenv import load_dotenv

load_dotenv()

def import_donor_data():
    df = pd.read_csv('.data/donor.csv')
    # TODO: complete the remaining code

def import_party_data():
    df = pd.read_csv('.data/donor.csv')
    # TODO: complete the remaining code

import_donor_data()
import_party_data()

'''

1. Read the data into a pandas dataframe
2. The columns in the file are basically p_date, donor_name, denomination
3. Add purchase_date,year,month,date columns to the dataframe
4. Fill the purchase_date (date format),year,month,date columns

  


# Read the CSV file
df = pd.read_csv('.data/donor.csv')

# Cleanup data
df['birthDate'] = pd.to_datetime(df['birthDate'].astype(str).str.split().str.get(0)).dt.date
df['date'] = pd.to_datetime(df['date'].astype(str).str.split().str.get(0)).dt.date
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

query = """INSERT INTO Billionaires2023 (worldRank, finalWorth, category, personName, age,
    country, city, source, industries, countryOfCitizenship, organization, selfMade, status, gender, 
    birthDate, lastName, firstName, title, date, state, residenceStateRegion, birthYear, birthMonth, 
    birthDay) 
     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
      %s, %s, %s, %s)"""
query = ' '.join(query.split('\n'))


for index, row in df.iterrows():
    values = (row['worldRank'], row['finalWorth'], row['category'], row['personName'], 
                row['age'], row['country'], row['city'], row['source'], 
                row['industries'], row['countryOfCitizenship'], row['organization'], row['selfMade'], 
                row['status'], row['gender'], row['birthDate'], row['lastName'], 
                row['firstName'], row['title'], row['date'], row['state'], 
                row['residenceStateRegion'], row['birthYear'], row['birthMonth'], row['birthDay'])
    cursor.execute(query, values)
    conn.commit()

conn.close()

'''
