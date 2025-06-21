import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from scripts import static_query
from scripts.clean_data import clean_data
from thefuzz import fuzz, process
from datetime import datetime
from db.database import query_db, SessionLocal
from visulizations.kpi_banner import kpi_banner
from visulizations.colleges_pie_charts import pie_charts
from dotenv import load_dotenv
import os



st.set_page_config(page_title="Event Sales Dashboard", layout="wide")

st.title("Event Sales Dashboard")


with SessionLocal() as session:
    events = static_query.get_events(session)
    event_options = ["ALL"] + [f"{event.event_name} {event.location}" for event in events]
    selected_event = st.selectbox(label="Select Event", options=event_options)
    selected_event_id = None
    selected_event_year = None
    if selected_event != "ALL":
        selected_event_id = static_query.get_event_id(session, selected_event=selected_event, events=events)
        selected_event_year = static_query.get_event_year(session, selected_event_id=selected_event_id)
    norcal = static_query.get_norcal(session=session, selected_event_id=selected_event_id)
    socal = static_query.get_socal(session=session, selected_event_id=selected_event_id)
    attendees = static_query.get_attendees(session=session, selected_event_id=selected_event_id)
    retention = static_query.get_returning_participants(session=session, selected_event_id=selected_event_id)
    revenue = static_query.get_total_revenue(session=session, selected_event_id=selected_event_id)
    college_counts = static_query.get_colleges_counts(session=session, selected_event_id=selected_event_id)
    returning_colleges = static_query.get_returning_colleges(session=session, selected_event_id=selected_event_id)

kpi_banner(norcal, socal, attendees, retention, revenue)
pie_charts(college_counts, returning_colleges)


