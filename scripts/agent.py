import getpass
import os
from db.database import engine
from langchain.chat_models import init_chat_model
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver
import streamlit as st
from langchain_tavily import TavilySearch
from pinecone import Pinecone
from langchain.schema import Document
from langchain.tools import tool
from langchain_text_splitters import RecursiveCharacterTextSplitter
import hashlib

if "PINECONE_API_KEY" in st.secrets:
    os.environ["PINECONE_API_KEY"] = st.secrets["PINECONE_API_KEY"]

pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
index_name = 'usm-agent-memory'
dense_index = pc.Index(index_name)

def init_vector_db():
    if not pc.has_index(index_name):
        pc.create_index_for_model(
            name=index_name,
            cloud='aws', 
            region='us-east-1',
            embed={
            "model":"llama-text-embed-v2",
            "field_map":{"text": "chunk_text"}
        }
        )

@tool
def update_password(password):
    '''
    this tool is used to update the guessed password to check
    if the user has credentials to upsert information. If the user says the password is [blank], call this tool with the given password
    '''
    st.session_state.guessed_password = password


@tool
def upsert_information(text, meta_data):
    '''
    this tool is a way to update your vector data base, you have to submit in a unique ID which is something descripive, the text you want to embed, and then
    a dictionary containing the metadata of that information. ASK THE USER FOR Permission BEFORE UPSERTING ANYTHING. The Parameters are text -> str, meta_data -> dict.
    CALL THIS TOOL WHEN YOU THINK YOU NEED TO ADD STUFF TO MEMORY. INFER WHAT THE ID, TEXT, AND META_DATA SHOULD BE, DONT ASK THE USER DIRECTLY RATHER ASK QUESTIONS TO HELP YOU GET ANSWERS.
    '''
    if st.session_state.guessed_password:
        if  st.session_state.guessed_password != st.secrets['password']:
            return "Failed because user inputted incorrect password"
    else:
        return "Failed because user did not input password"
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)
    texts = text_splitter.split_text(text)
    base_id = hashlib.sha256(text.encode()).hexdigest()[:8]

    records = []
    for idx, value in enumerate(texts):
        record = {"id" : base_id + f"_{idx}", "chunk_text" : value}
        record.update(meta_data)
        records.append(record)
    dense_index.upsert_records("default", records)

@tool
def query_vectordb(question):
    '''
    this tool is used to look up information in your vector db. All you have to submit is a question and it will look and return to you the relevant documents.
    use this tool wheneber you feel like you should
    '''

    results = dense_index.search(
        namespace = "default",
        query={
            "top_k" : 10,
            "inputs": {
                "text":question
            }
        },
        rerank={
        "model": "bge-reranker-v2-m3",
        "top_n": 10,
        "rank_fields": ["chunk_text"]
    }   

    )
    return results


def create_agent():

    os.environ["LANGSMITH_TRACING"] = "true"

    if "LANGSMITH_API_KEY" in st.secrets:
        os.environ["LANGSMITH_API_KEY"] = st.secrets["LANGSMITH_API_KEY"]

    project_name = st.secrets.get("LANGSMITH_PROJECT", "default")
    os.environ["LANGSMITH_PROJECT"] = project_name

    if "GOOGLE_API_KEY" in st.secrets:
        os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]

    model = init_chat_model("gemini-2.5-flash", model_provider="google_genai")
    init_vector_db()
    toolkit = SQLDatabaseToolkit(db=SQLDatabase(engine), llm=model)
    tools = toolkit.get_tools()

    prebuilt_prompt = '''
    You are a personalized AI assistant built for the United Sikh Movement (USM). Your role is to help users retrieve, understand, and build upon USM's collective knowledge — whether stored in a structured SQL database, a semantic memory (VectorDB), or discovered via the internet.

    ========================= CORE OBJECTIVE =========================

    You serve as a memory-augmented assistant to help organize and share knowledge related to USM events, themes, speakers, announcements, and more. Your answers should be clear, relevant, and deeply informed by both data and context.
    You are also a **self-improving assistant** — every time you encounter new information that isn’t already in the structured database, you attempt to store it to your long-term memory (VectorDB) so you can better assist in the future.
    ========================= WORKFLOW OVERVIEW =========================

    1. **START WITH SQL**  
        - Your first step is always to consult the SQL database. It holds structured information like events, years, speakers, themes, etc.
        - Begin by reviewing the list of available tables.
        - Then inspect the schema of the most relevant table(s) before attempting a query.
        - Only query for necessary columns relevant to the question.
        - Unless otherwise specified, limit results to {top_k} rows.
        - Prefer ordering results by a meaningful column (e.g., most recent year).
        - Do not use SELECT *.
        - Never make DML statements (INSERT, UPDATE, DELETE, DROP, etc.).
        - Double-check your query syntax. If a query fails, revise and try again.

    2. **THEN CHECK YOUR VECTORDATABASE**  
        - If the SQL database doesn’t contain the answer, check your VectorDB memory.
        - The VectorDB contains semantically stored facts, history, or context that was learned during prior interactions.
        - Use this memory to inform your answer. Be specific and cite what chunk or idea you're referencing.

    3. **IF THAT STILL FAILS, USE TAVILY TO SEARCH THE WEB**  
        - If the answer is not in SQL or the VectorDB, use Tavily (web search tool) to fetch external information.
        - Summarize and rephrase web results in your own words.
        - Avoid relying on raw search content—only pull what’s relevant and helpful.

    ========================= LEARNING & MEMORY =========================

    4. **WHEN YOU LEARN SOMETHING NEW:**
        - If you gain new knowledge from a user or external source that is not already in your SQL database:
                - Use `upsert_information(id, text, metadata)` to store it in the VectorDB.
                - Create a unique, descriptive `id` (e.g., "2022_theme_paatshahi").
                - Ensure `text` summarizes what was learned (1–3 sentences).
                - Use `metadata` to tag useful context like "event_id", "source", or "topic".
                - You may be returned an error indicating the user has not submitted a password / incorrect password

    ========================= BEHAVIOR GUIDELINES =========================

    - Act as an intelligent, informed assistant on behalf of USM.
    - Keep answers clear and helpful.
    - Be proactive — do not ask the user to tell you what tables exist; inspect them yourself.
    - Always try to answer in a descriptive and thoughtful way, grounded in available data.
    - Try to provide detail to your answer, dont be afraid to give longer answers
    - If something isn't known, say so — and try to learn it.
    - ALWAYS CHECK SQL FIRST, AND ALWAYS CHECK YOUR VECTOR DATABASE, ONLY USE TAVILY IF BOTH SQL AND VECTOR DATABASE FAILS

    =================================================================

    '''.format(
        dialect="SQLite",
        top_k=5,
    )

    basic_search_tool = TavilySearch(
        max_results=5,
            topic="general",
        )
    
    basic_search_tool.description = 'this tool gives acces to tavily to allow the agent to find information not currently in its database. After using this tool you need to consider updating your vector database'
    if "memory" not in st.session_state:
        st.session_state.memory = InMemorySaver()

    memory = InMemorySaver()
    tools.append(basic_search_tool)
    tools.append(upsert_information)
    tools.append(query_vectordb)
    tools.append(update_password)

    agent = create_react_agent(model=model, tools=tools, prompt=prebuilt_prompt, checkpointer=memory)


    return agent