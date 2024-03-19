import streamlit as st
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import psycopg2 as pg
from llm import *

tables = ["party","donor","party_master"]
host = st.secrets.get("DB_HOST")
database = st.secrets.get("DB_NAME")
username = st.secrets.get("DB_USERNAME")
password = st.secrets.get("DB_PASSWORD")

uri = f"postgresql+psycopg2://{username}:{password}@{host}/{database}"

sqldb = SQLDatabase.from_uri(database_uri=uri, ignore_tables=[])


def generate_response(user_question):
    print("utils.py :: user_question: "+user_question)
    standardised_question = user_question
   
    sql_template = """Based on the table schema below, write a SQL query to answer the user's question:
    {schema}

    Question: {question}
    SQL Query: """
  
    prompt = ChatPromptTemplate.from_template(sql_template)
    model = llm

    sql_chain = (
        RunnablePassthrough.assign(schema=get_schema)
        | prompt
        | model.bind(stop=["\nSQLResult:"])
        | StrOutputParser()
    )

    sqlquery = sql_chain.invoke({"question": standardised_question})
    print("utils.py :: sqlquery: "+sqlquery)

    template = """Based on the question, sql query, and sql response, write a natural language response:
   
    If an exception happens, please say 
    'I am unable to answer your question at this time'

    If the query doesn't get any results, please say 
    'No data found for your question at this time'


    Question: {question}
    SQL Query: {query}
    SQL Response: {response} """
    prompt_response = ChatPromptTemplate.from_template(template)
    final_chain = (
        RunnablePassthrough.assign(schema=get_schema, response=lambda x: run_query(x["query"]))
        | prompt_response
        | model
        | StrOutputParser()
    )

    response = "I am unable to answer your question at this time."
    if (str(sqlquery.upper()).startswith("SELECT")):
        response = final_chain.invoke({"question": standardised_question, "query": sqlquery})
  
    print("utils.py :: response: "+response)
    return response

def get_schema(_):
    return sqldb.get_table_info()


def run_query(query):
    return sqldb.run(query)
