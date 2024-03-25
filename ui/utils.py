from operator import itemgetter
import os
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_openai.chat_models import ChatOpenAI
import psycopg2
from dotenv import load_dotenv, find_dotenv
from decimal import Decimal
import re
import ast

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

tables = ["bond_party","bond_donor"]

host=os.getenv("db-host")
database=os.getenv("db-name")
username=os.getenv("db-username")
password=os.getenv("db-password")

uri = f"postgresql+psycopg2://{username}:{password}@{host}/{database}"

sqldb = SQLDatabase.from_uri(database_uri=uri, include_tables=tables)


def format_indian_currency(amount):
    """
    Formats the given amount as Indian currency (with commas and the ₹ symbol).
    """
    if isinstance(amount, Decimal):
        s = str(amount)
        reg = re.compile('(\d{3})?(\d{2})?(\d{2})?(\d+)?$')
        match = reg.search(s[::-1])
        groups = [group[::-1] for group in match.groups() if group]
        final_amount = ','.join(groups[::-1])
        formatted_amount = "₹" + final_amount
    else:
        # For non-Decimal values, return them as-is
        formatted_amount = amount
    return formatted_amount

def format_response(sql_response):
    """
    Formats the entire SQL response by converting Decimal values to Indian rupees format.
    """
    formatted_response = []
    for row in sql_response:
        formatted_row = [format_indian_currency(value) for value in row]
        formatted_response.append(tuple(formatted_row))
    return formatted_response

#Translate [input_text] to [target_language] 
def translate_text(input_text,target_language):
    prompt = ChatPromptTemplate.from_template(f"""Translate {input_text} to {target_language} """)
    
    output_parser = StrOutputParser()
    model = llm
    chain = prompt | model | output_parser
    translated_text = chain.invoke({"input_text":input_text})
    return translated_text

# Generate response based on selected language
def generate_response_language(user_question, target_language):
    #print("utils.py :: user_question: "+user_question + " target_language: "+target_language)
    standardised_question = user_question
    
    if target_language != 'English':
        #if selected language is other than english, translate text to english to form sql query
        standardised_question = translate_text(user_question, 'English')
    
    sql_template = """Based on the table schema below, write a SQL query to answer the user's question:
    {schema}
    Please note the giver is the bond donor and the receiver is the bond party.
    Please do not use s_no column in the query.
    Do not compare purchaser_name and political_party_name as they do not represent the same entity.
    Use unique_bond_number when you need to join bond_party and bond_donor tables.
    If more than one political_party_name or purchaser_name is selected, use IN operator.
    Check both political_party_name and political_party_code columns when checking for party, use OR condition.
  
    Please just return the SQL query and not the result.
    Use the format\nQuestion:...\nSQLResult:...\n\n"),
    Question: {question}
    SQL Query: """
  
    sql_prompt = ChatPromptTemplate.from_template(sql_template)
    model = llm

    sql_chain = (
        RunnablePassthrough.assign(schema=get_schema)
        | sql_prompt
        | model.bind(stop=["\nSQLResult:"])
        | StrOutputParser()
    )

    sqlquery = sql_chain.invoke({"question": standardised_question})
    sqlquery = sqlquery.strip()
    #print("utils.py :: sqlquery: "+sqlquery)
    
    sqlresponse_template = """Based on the sql query, get sql response:
    SQL Query: {query}
    SQL Response: {response} """
    sqlresponse_prompt = ChatPromptTemplate.from_template(sqlresponse_template)
    sqlresponse_chain = (
        RunnablePassthrough.assign(response=lambda x: run_query(x["query"]))
    )

    response = "I am unable to answer your question at this time."
    
    if (str(sqlquery.upper()).startswith("SELECT")):
        response = sqlresponse_chain.invoke({"query": sqlquery})["response"]
        #print("utils.py :: sql_response (inside): "+str(response))
  
    # If response is not equal to "I am unable to answer your question at this time."
    if response != "I am unable to answer your question at this time.":
    # Convert the SQL response to a list of tuples
        l_response = eval(response)
        formatted_response = format_response(l_response)
        
        final_template = """Based on the question and response, write a natural language response:
    
        Question: {question}
        Response: {sql_response} """
        final_prompt = ChatPromptTemplate.from_template(final_template)
        
        final_chain = (
            final_prompt
            | model
            | StrOutputParser()
        )

        response = final_chain.invoke({"question": standardised_question, "sql_response": formatted_response})
  
    if target_language != 'English':
        response = translate_text(response, target_language)
    store_question(user_question, standardised_question, sqlquery, response)
    return response

def generate_response(user_question):
    #print("utils.py :: user_question: "+user_question)
    standardised_question = user_question
    
    sql_template = """Based on the table schema below, write a SQL query to answer the user's question:
    {schema}
    Please note the giver is the bond donor and the receiver is the bond party.
    Please do not use s_no column in the query.
    Do not compare purchaser_name and political_party_name as they do not represent the same entity.
    Use unique_bond_number when you need to join bond_party and bond_donor tables.
    If more than one political_party_name or purchaser_name is selected, use IN operator.
    Check both political_party_name and political_party_code columns when checking for party, use OR condition.
  
    Please just return the SQL query and not the result.
    Use the format\nQuestion:...\nSQLResult:...\n\n"),
    Question: {question}
    SQL Query: """
  
    sql_prompt = ChatPromptTemplate.from_template(sql_template)
    model = llm

    sql_chain = (
        RunnablePassthrough.assign(schema=get_schema)
        | sql_prompt
        | model.bind(stop=["\nSQLResult:"])
        | StrOutputParser()
    )

    sqlquery = sql_chain.invoke({"question": standardised_question})
    sqlquery = sqlquery.strip()
    #print("utils.py :: sqlquery: "+sqlquery)
    
    sqlresponse_template = """Based on the sql query, get sql response:
    SQL Query: {query}
    SQL Response: {response} """
    sqlresponse_prompt = ChatPromptTemplate.from_template(sqlresponse_template)
    sqlresponse_chain = (
        RunnablePassthrough.assign(response=lambda x: run_query(x["query"]))
    )

    response = "I am unable to answer your question at this time."
    
    if (str(sqlquery.upper()).startswith("SELECT")):
        #print("utils.py :: before running the sql query")
        response = sqlresponse_chain.invoke({"query": sqlquery})["response"]
        #print("utils.py :: sql_response (inside): "+str(response))
        

    #print("utils.py :: sql_response: "+str(response))

    # If response is not equal to "I am unable to answer your question at this time."
    if response != "I am unable to answer your question at this time.":
    # Convert the SQL response to a list of tuples
        l_response = eval(response)
        formatted_response = format_response(l_response)
        
        final_template = """Based on the question and response, write a natural language response:
    
        Question: {question}
        Response: {sql_response} """
        final_prompt = ChatPromptTemplate.from_template(final_template)
        
        final_chain = (
            final_prompt
            | model
            | StrOutputParser()
        )

        response = final_chain.invoke({"question": standardised_question, "sql_response": formatted_response})
  
    store_question(user_question, standardised_question, sqlquery, response)
    return response
    

def get_schema(_):
    return sqldb.get_table_info()


def run_query(query):
    return sqldb.run(query)

def store_question(user_question, 
                    standardised_question, 
                    sqlquery, 
                    response):
 
    conn = psycopg2.connect(host=host, database=database, user=username, password=password)
    conn.autocommit = True
    cursor = conn.cursor()
    query = """INSERT INTO user_question (user_question, standardised_question, sql_query, final_response) VALUES (%s, %s, %s, %s)"""
    values = (user_question, standardised_question, sqlquery, response)
    cursor.execute(query, values)
    conn.commit()

    conn.close()


def generate_response2(user_question):

    sql_template = """Based on the table schema below, write a SQL query to answer the user's question:
    {db_schema}

    Question: {question}
    SQL Query: """

    prompt1 = ChatPromptTemplate.from_template(sql_template)

    chain1 = (
        RunnablePassthrough.assign(db_schema=get_schema)
        | prompt1
        | llm.bind(stop=["\nSQLResult:"])
        | StrOutputParser()
    )


    template = """Based on the question, sql query, and sql response, write a natural language response:

    If an exception happens, please say 
    'I am unable to answer your question at this time'

    If the query doesn't get any results, please say 
    'No data found for your question at this time'


    Question: {question}
    SQL Query: {query}
    SQL Response: {response} """

    prompt2 = ChatPromptTemplate.from_template(template)

    chain2 = (
        RunnablePassthrough.assign(response=lambda x: run_query(x["query"]))
        | prompt2
        | llm
        | StrOutputParser()
    )

    response = "I am unable to answer your question at this time."
    
    chain = {"query": chain1, "question": itemgetter("question")} | chain2

    response = chain.invoke({"question": user_question})


def generate_response1(user_question):


    print("utils.py :: user_question: "+user_question)
    standardised_question = user_question
   
    sql_template = """Based on the table schema below, write a SQL query to answer the user's question:
    {schema}
    Please just return the SQL query and not the result.
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
   
    You are an expert on Indian currency and finance. You have a tendency to ignore a digit or two from the input.
    Please double check that you did not leave any digits from the input and show the numbers in ₹#####,##,##,###.

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
  
   
    store_question(user_question, standardised_question, sqlquery, response)
    return response


def get_donor_options():
    query = "SELECT DISTINCT purchaser_name FROM bond_donor ORDER BY purchaser_name ASC"
    result = sqldb.run(query)
    result = ast.literal_eval(result)
    donor_options = [row[0] for row in result]
    return donor_options


def get_party_options():
    query = "SELECT DISTINCT political_party_name FROM bond_party ORDER BY political_party_name ASC"
    result = sqldb.run(query)  
    result = ast.literal_eval(result)
    names = [item[0] for item in result]
    party_options = names
    return party_options

def get_lang_options():
    lang_list=['English','Telugu', 'Hindi']
    return lang_list