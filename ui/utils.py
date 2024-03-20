import os
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_openai.chat_models import ChatOpenAI
import psycopg2
from dotenv import load_dotenv, find_dotenv

if find_dotenv():
    load_dotenv(find_dotenv())

openai_api_key = os.getenv("openai-api-key")
openai_model = os.getenv("openai-model")


os.environ["OPENAI_API_KEY"] = openai_api_key

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("langchain-api-key")    
os.environ["LANGCHAIN_PROJECT"] = os.getenv("langchain-project")

llm = ChatOpenAI(
    openai_api_key=openai_api_key,
    model=openai_model,
    temperature=0
)

tables = ["party","donor","party_master","donor_master"]

host=os.getenv("db-host")
database=os.getenv("db-name")
username=os.getenv("db-username")
password=os.getenv("db-password")

uri = f"postgresql+psycopg2://{username}:{password}@{host}/{database}"

sqldb = SQLDatabase.from_uri(database_uri=uri, include_tables=tables)


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
