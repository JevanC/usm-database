import streamlit as st
from datetime import datetime
import pandas as pd
from scripts.clean_data import clean_data
from scripts.add_new_event import merge_new_data
from db.database import query_db, SessionLocal
import numpy as np

st.title("CSV Uploader")
uploaded = st.file_uploader("Upload your file here", type=["csv"])

def incomplete(df):
    df['Birth Date'] = pd.to_datetime(df['Birth Date'], errors='coerce')
    df['incomplete'] = (df['Birth Date'] == pd.Timestamp("1901-01-01"))
    return df

if uploaded is not None:
    new_event_name = st.text_input(label="What is the event name?")
    st.session_state.new_event_date = st.date_input(label="When is the event date?")
    new_event_location = st.text_input(label="What is the event location?")
    st.session_state.at_door_cost = st.text_input(label="How much does an At The Door Ticket Cost?")
    if st.button("SUBMIT"):
        st.session_state.submitted = True
    if "submitted" in st.session_state:
        uploaded_df = pd.read_csv(uploaded, header=0)
        uploaded_df = uploaded_df.dropna(subset=['First Name'])
        st.session_state.new_event_date = pd.Timestamp(datetime.combine(st.session_state.new_event_date, datetime.min.time()))
        st.write(uploaded_df[uploaded_df['Order Date'].isna()])
        st.success("File Uploaded Successfully")
        new_event_data = clean_data(uploaded_df)
        new_event_data = incomplete(new_event_data)
        new_event_data[['event_name', 'event_year', 'event_location']] = new_event_name, st.session_state.new_event_date.year, new_event_location

        st.write(new_event_data)
else:
    st.info("Please upload a CSV file to proceed.")

if "merge" not in st.session_state:
    st.session_state.merge = False

if st.button("Merge"):
    st.session_state.merge = True

if st.session_state.merge == True:
    with SessionLocal() as session:
        merge_new_data(session, new_event_data, st.session_state.new_event_date)
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()