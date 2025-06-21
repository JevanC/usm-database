from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import pandas as pd
import numpy as np
from thefuzz import process
from dotenv import load_dotenv
import streamlit as st
import os

load_dotenv() 

DATABASE_URL = st.secrets["DATABASE_URL"]
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def query_db(query):
    with engine.connect() as connection:
        return pd.read_sql(text(query), connection)

# Get list of college names for fuzzy matching
with engine.connect() as conn:
    colleges_name = list(pd.read_sql(text("SELECT name FROM colleges"), conn)["name"])

# Replace college name with college_id
def replace_college_name(original_name):
    excluded_list = ['high school', 'graduate student', 'other']
    if original_name == "N/A" or pd.isna(original_name) or original_name.lower() in excluded_list:
        return None
    best_match = process.extractOne(original_name, colleges_name)
    if best_match[1] < 95:
        return None
    with engine.connect() as conn:
        result = pd.read_sql(
            text("SELECT college_id FROM colleges WHERE name = :name"),
            conn,
            params={"name": best_match[0]}
        )
    return result['college_id'].iloc[0] if not result.empty else None

# Load participant data
with engine.connect() as conn:
    participants_df = pd.read_sql(text("SELECT * FROM participants;"), conn)


# Update database
with engine.begin() as conn:  # Use .begin() to enable transactions
    for _, row in participants_df.iterrows():
        if pd.isna(row['college_id']):
            continue
        conn.execute(
            text("UPDATE participants SET college_id = :college_id WHERE participant_id = :id"),
            {"college_id": int(row['college_id']), "id": int(row['participant_id'])}
        )
