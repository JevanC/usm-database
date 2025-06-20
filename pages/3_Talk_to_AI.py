from scripts import agent
import streamlit as st
from google import genai
from google.genai import types
from db.database import query_db
import os
from dotenv import load_dotenv
import os

load_dotenv() 

genai_api = os.getenv("genai_api")
client = genai.Client(api_key=genai_api)


question = st.text_input("Your Question")
response = agent.automatic_query(client, question)
st.markdown(response)


# query_database = {
#     "name": "query_db",
#     "description": (
#         "Sends a query to a postgres database with the following tables and schemas:\n"
#         "Table Sales:\n"
#         "-sales_id = Column(Integer, primary_key=True)\n"
#         "-order_date = Column(DateTime, nullable=False)\n"
#         "-total_paid = Column(Numeric(10, 2), nullable=False)\n"
#         "-fees_paid = Column(Numeric(10, 2), nullable=False)\n"
#         "-friday_hotel = Column(Boolean, nullable=False, default=False)\n"
#         "-saturday_hotel = Column(Boolean, nullable=False, default=False)\n"
#         "-sunday_hotel = Column(Boolean, nullable=False, default=False)\n"
#         "-event_id = Column(Integer, ForeignKey('events.event_id', ondelete='CASCADE'))\n"
#         "-participant_id = Column(Integer, ForeignKey('participants.participant_id', ondelete='SET NULL', onupdate='CASCADE'))\n"
#         "-ticket_id = Column(Integer, ForeignKey('ticket_types.ticket_id', ondelete='SET NULL', onupdate='CASCADE'))\n"
#         "Table Events:\n"
#         "-event_id = Column(Integer, primary_key=True)\n"
#         "-event_name = Column(String(50), nullable=False)\n"
#         "-year = Column(Integer, nullable=False)\n"
#         "-location = Column(String(50), nullable=False)\n"
#         "Table Participants:\n"
#         "-participant_id = Column(Integer, primary_key=True)\n"
#         "-first_name = Column(String(50), nullable=False)\n"
#         "-last_name = Column(String(50), nullable=False)\n"
#         "-birth_date = Column(Date) if unknown it is set to '1901-01-01'\n" # Emphasize '1901-01-01' as a string/date literal
#         "-home_address = Column(String(100))\n"
#         "-home_city = Column(String(50))\n"
#         "-home_state = Column(String(50))\n"
#         "-home_zip = Column(String(10))\n"
#         "-phone_number = Column(String(20))\n"
#         "-gender = Column(String(20))\n"
#         "-major_or_profession = Column(Text)\n"
#         "-college = Column(Text)\n"
#         "-last_updated = Column(DateTime)\n"
#         "-college_id = Column(Integer, ForeignKey('colleges.college_id'))\n"
#         "Table Colleges:\n"
#         "-college_id = Column(Integer, primary_key=True)\n"
#         "-name = Column(String)\n"
#         "-latitude = Column(Float)\n"
#         "-longitude = Column(Float)\n"
#         "-city = Column(String)\n"
#         "-state = Column(String(2))\n"
#         "-zip = Column(String(5))\n"
#         "-county = Column(String)\n"
#         "-country = Column(String)\n"
#         "Table TicketTypes:\n"
#         "-ticket_id = Column(Integer, primary_key=True)\n"
#         "-ticket_type = Column(String(100), nullable=False, unique=True)\n"
#         "IMPORTANT: When identifying duplicate Participants, a unique participant is defined by the combination of first_name, last_name, and birth_date. However, if the birth_date is '1901-01-01', it should NOT be considered for uniqueness, meaning participants with '1901-01-01' birthdates should be excluded from this uniqueness check. "
#         "For potential repeats, identify participants who share the same first_name and last_name, but their birth_date is *not* '1901-01-01', and there are multiple such entries." # Refined instruction
#     ),
#     "parameters": {
#         "type": "object",
#         "properties": {
#             "query": {
#                 "type": "string",
#                 "description": "A SQL query that gets sent to a database",
#             },
#         },
#         "required": ["query"],
#     },
# }

# tools = types.Tool(function_declarations=[query_database])
# config = types.GenerateContentConfig(tools=[tools])

# response = client.models.generate_content(
#     model="gemini-2.0-flash",
#     contents="Find me every student who repeated twice when they shouldnt have because of missing data",
#     config=config,
# )

# if response.candidates[0].content.parts[0].function_call:
#     function_call = response.candidates[0].content.parts[0].function_call
#     st.write(f"Function to call: {function_call.name}")
#     st.write(f"Arguments: {function_call.args}")
# else:
#     st.write("No function call found in the response.")
#     st.write(response.text)
