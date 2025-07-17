from scripts import agent
import streamlit as st
from google import genai
from google.genai import types
from db.database import query_db
import os
from dotenv import load_dotenv
import os

if "agent" not in st.session_state:
    st.session_state.agent = agent.create_agent()

if "config" not in st.session_state:
    st.session_state.config = {"configurable": {"thread_id": "Base Thread"}}

question = st.text_area("What is your question")
button = st.button("Submit")

if button and question:
    response = st.session_state.agent.invoke(
        {"messages": [{"role": "user", "content": question}]},
        st.session_state.config  
    )

    st.markdown(dict(response['messages'][-1])['content'])