import asyncio
import regex as re
from google import genai
from google.genai import types
from db.database import query_db



async def ask_llm(client, query):
        
    prompt_to_query = """
        You are a PostgreSQL SQL expert. Convert the following English question into a valid SQL SELECT query. If it is not clear what you are being
        asked, assume that the user is trying to get an answer related to the sales that this organization has had

        CRITICAL FORMATTING RULES:
        - Return ONLY the raw SQL query
        - NO markdown formatting, NO ```sql or ``` blocks
        - NO explanations, NO comments, NO extra text
        - Start directly with SELECT, WITH, or other SQL keywords

        POSTGRESQL-SPECIFIC FUNCTIONS:
        - Use STRING_AGG(column, delimiter) instead of GROUP_CONCAT()
        - Use STRING_AGG(column, ', ') for comma-separated lists
        - Use EXTRACT() for date parts
        - Use COALESCE() for handling NULL values
        - Use ILIKE for case-insensitive pattern matching

        Schema:
        1. ticket_types:
        - ticket_id INTEGER PRIMARY KEY
        - ticket_type VARCHAR(100) NOT NULL UNIQUE

        2. colleges:
        - college_id INTEGER PRIMARY KEY
        - name VARCHAR, latitude FLOAT, longitude FLOAT
        - city VARCHAR, state CHAR(2), zip CHAR(5)
        - county VARCHAR, country VARCHAR

        3. participants:
        - participant_id INTEGER PRIMARY KEY
        - first_name VARCHAR(50) NOT NULL, last_name VARCHAR(50) NOT NULL
        - birth_date DATE NOT NULL, home_address VARCHAR(100)
        - home_city VARCHAR(50), home_state VARCHAR(50), home_zip VARCHAR(10)
        - phone_number VARCHAR(20), gender VARCHAR(20)
        - major_or_profession TEXT, college TEXT
        - last_updated DATETIME
        - college_id INTEGER REFERENCES colleges(college_id)
        - incomplete BOOLEAN

        4. events:
        - event_id INTEGER PRIMARY KEY
        - event_name VARCHAR(50) NOT NULL, year INTEGER NOT NULL
        - location VARCHAR(50) NOT NULL

        5. sales:
        - sales_id INTEGER PRIMARY KEY, order_date DATETIME NOT NULL
        - total_paid NUMERIC(10,2) NOT NULL, fees_paid NUMERIC(10,2) NOT NULL
        - friday_hotel BOOLEAN DEFAULT FALSE, saturday_hotel BOOLEAN DEFAULT FALSE
        - sunday_hotel BOOLEAN DEFAULT FALSE
        - event_id INTEGER REFERENCES events(event_id)
        - participant_id INTEGER REFERENCES participants(participant_id)
        - ticket_id INTEGER REFERENCES ticket_types(ticket_id)

        IMPORTANT: Use lowercase table names (participants, events, sales, etc.)

        English Question:
        """
    
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        config=types.GenerateContentConfig(
            system_instruction=prompt_to_query 
        ),
        contents=[query]
    )
    sql_text = re.sub(r'^```(?:sql)?\s*\n?', '', response.text, flags=re.IGNORECASE | re.MULTILINE)
    sql_text = re.sub(r'\n?```$', '', sql_text)
    
    sql_text = sql_text.strip()
    query_results = query_db(sql_text)

    return query_results

async def translate_sql_results(client, question, answer):
    query_to_english = """    You are a chatbot meant to answer questions users have about the dataset. You are an expert in translating data queries to the user. Based on the user's query and its results, provide a clear and 
    concise explanation of what the results mean. YOURE OUTPUT CANNOT HAVE ``` OR "SQL" ANYWHERE, Explain how the query was most likely found
    If it is not clear what you are being asked, assume that the user is trying to get an answer related to the sales that this organization has had
    Make sure your response is normal english, no fonts, and correct spacing. MAKE SURE THE RESULT IS HIGHLIGHTED, IF THERE IS NO RESULT EXPLAIN WHY.
    WHEN IT COMES TO UNIVERSITY NAMES AND MAJORS, USE THE COMMON NAMES AND COMBINE (CS TO COMPUTER SCIENCE; UNIVERSITY OF CALIFORNIA SAN DIEGO TO UC SAN DIEGO)
"""
    question_str = str(question) if question else "No question provided"
    if answer is None or (hasattr(answer, 'empty') and answer.empty):
        answer_str = "No results returned from the query."
    else:
        try:
            answer_str = answer.to_string(index=False, max_rows=100)
            
            if len(answer) > 100:
                answer_str += f"\n\n[Showing first 100 rows of {len(answer)} total rows]"
                
        except Exception as e:
            answer_str = str(answer)
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        config=types.GenerateContentConfig(
            system_instruction=query_to_english  # Removed .format()
        ),
        contents=[question_str, answer_str]
    )
    
    return response.text

def automatic_query(client, question):
    
    answer_sql = asyncio.run(ask_llm(client, question))
    if answer_sql is not None:
        answer_translated = asyncio.run(translate_sql_results(client, question, answer_sql))
        return answer_translated
        