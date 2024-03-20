import os
import sys
import psycopg2
from dotenv import load_dotenv
from langchain_openai.chat_models import ChatOpenAI

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain.prompts import PromptTemplate

load_dotenv()

llm = ChatOpenAI()


def get_company_details():
  
    class Donor(BaseModel):
        donor_name: str = Field(description="name of the donor")
        donor_type: str = Field(description="type of the donor either individual or organization")
        nature_of_business: str = Field(description="nature of business of the company")
        registration_state: str = Field(description="registration state of the company")
        
    # Get a connection to Postgres
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USERNAME"),
        password=os.getenv("DB_PASSWORD")
    )

    conn.autocommit = True
    cursor = conn.cursor()

    # Get the compamy names from donor_master

    query = """SELECT donor_name FROM donor_master where donor_type is null;"""
    
    # I want to get each donor_name into a variable called donor_name
    cursor.execute(query)
    donor_names = cursor.fetchall()

    total_records = len(donor_names)
    i = 0
    for donor_name in donor_names:
        i += 1
        template = """You are an expert in knowing about companies based in India
                    If the donor is a company, return organization as the donor_type
                    If the donor is a person, return individual as the donor_type
                    Please provide the following in json format for the company {donor_name}:
                    1. The name of the company or individual
                    2. The type of the donor (individual or organization)
                    3. What does the company's nature of business in one sentence. Leave it blank if it is an individual 
                    4. In what state the company got registered. Leave it blank if it is an individual   \n{format_instructions}"""
        
        parser = JsonOutputParser(pydantic_object=Donor)

        prompt = PromptTemplate(
            template=template,
            input_variables=["donor_name"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )
        chain = prompt | llm | parser

        response = chain.invoke({"donor_name": donor_name})
        #print(response)   
        donor_type = response["donor_type"]
        nature_of_business = response["nature_of_business"]
        registration_state = response["registration_state"]

        update_query = """UPDATE donor_master SET donor_type = %s, nature_of_business = %s, registration_state = %s WHERE donor_name = %s;"""
        cursor.execute(update_query, (donor_type, nature_of_business, registration_state, donor_name))
        sys.stdout.write(f"\rProcessing record {i}/{total_records}")
        sys.stdout.flush()
    conn.close()
    print("\nDone")

get_company_details()



