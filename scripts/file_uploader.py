import streamlit as st
from datetime import datetime
import pandas as pd
from clean_data import clean_data
from add_new_event import merge_new_data
st.title("CSV Uploader")
uploaded = st.file_uploader("Upload your file here", type=["csv"])

if uploaded is not None:
    new_event_name = st.text_input(label="What is the event name?")
    st.session_state.new_event_date = st.date_input(label="When is the event date?")
    new_event_location = st.text_input(label="What is the event location?")
    if st.button("SUBMIT"):
        st.session_state.submitted = True
    if "submitted" in st.session_state:
        uploaded_df = pd.read_csv(uploaded, header=2)
        uploaded_df = uploaded_df.dropna(subset=['First Name'])
        st.session_state.new_event_date = pd.Timestamp(datetime.combine(st.session_state.new_event_date, datetime.min.time()))
        st.write(uploaded_df[uploaded_df['Order Date'].isna()])
        st.success("File Uploaded Successfully")
        new_event_data = clean_data(uploaded_df)
        new_event_data[['event_name', 'event_year', 'event_location']] = new_event_name, st.session_state.new_event_date.year, new_event_location
        st.write(new_event_data),
else:
    st.info("Please upload a CSV file to proceed.")

if "merge" not in st.session_state:
    st.session_state.merge = False

if st.button("Merge"):
    st.session_state.merge = True

if st.session_state.merge == True:
    merge_new_data(new_event_data, st.session_state.new_event_date)
    st.session_state.merge = False
    st.rerun()