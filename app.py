import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from sqlalchemy.orm import sessionmaker, joinedload
from db import query_db, SessionLocal
from models import Participants, Events, TicketTypes, Sales
from sqlalchemy import func

def kpi_banner(attendees, retention, revenue):
    with st.container():
        st.markdown("### KPI Overview")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Attendees", value=attendees)
        with col2:
            st.metric(label="Rentention Percentage", value=(f"{retention/attendees * 100:.2f}%"))
        with col3:
            st.metric(label="Revenue", value=revenue)

def college_cloropleth(colleges_count, returning_colleges_count):
    colleges = []
    counts = []
    for college, count in colleges_count:
        if count>=2:
            colleges.append(college)
            counts.append(count)
    data = pd.DataFrame({
        "City": colleges,
        "Colleges": counts
    })

    colleges_ret = []
    counts_ret = []
    for college, count in returning_colleges_count:
        if count>=2:
            colleges_ret.append(college)
            counts_ret.append(count)

    data_ret = pd.DataFrame({
        "City": colleges_ret,
        "Colleges": counts_ret
    })

    data = data.sort_values(by="Colleges", ascending=False)
    data_ret = data_ret.sort_values(by="Colleges", ascending=False)



    fig = px.bar(data, x = "City", y="Colleges", labels="Total College Attendance")
    fig2 = px.bar(data_ret, x = "City", y="Colleges", labels="Total College Attendance")
    

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig, key="college_chart_total")
    
    with col2:
        st.plotly_chart(fig2, key="college_chart_returning")


st.set_page_config(page_title="Event Sales Dashboard", layout="wide")

st.title("Event Sales Dashboard")



db = SessionLocal()

events = db.query(Events.event_id, Events.event_name, Events.location).all()

event_options = ["ALL"] + [f"{event.event_name} {event.location}" for event in events]

selected_event = st.selectbox("Select Event", event_options)

if selected_event != "ALL":
    selected_event_id = next(event.event_id for event in events if f"{event.event_name} {event.location}" == selected_event)
    selected_event_year = db.query(Events.year).filter(Events.event_id == selected_event_id).scalar()

    participants = db.query(func.sum(Sales.total_paid)) \
                    .join(Events, Sales.event_id == Events.event_id) \
                    .join(Participants, Sales.participant_id == Participants.participant_id) \
                    .filter(Events.event_id == selected_event_id) \
                    .scalar()


    attendees = db.query(func.count(Participants.participant_id)) \
                .join(Sales, Sales.participant_id == Participants.participant_id) \
                .filter(Sales.event_id == selected_event_id) \
                .scalar()


    subquery = db.query(Sales.participant_id) \
        .join(Events, Sales.event_id == Events.event_id) \
        .filter(Events.year < selected_event_year) \
        .distinct().subquery()
    attendees_with_previous_events = db.query(func.count(Participants.participant_id)) \
        .join(Sales, Sales.participant_id == Participants.participant_id) \
        .filter(Sales.event_id == selected_event_id) \
        .filter(Participants.participant_id.in_(subquery)) \
        .scalar()

    college_counts = db.query(Participants.college, func.count(Participants.participant_id)) \
                    .group_by(Participants.college) \
                    .join(Sales, Sales.participant_id == Participants.participant_id) \
                    .filter(Participants.college != "N/A") \
                    .filter(Sales.event_id == selected_event_id) \
                    .all()

    colleges_returning = db.query(Participants.college, func.count(Participants.participant_id)) \
                    .group_by(Participants.college) \
                    .join(Sales, Sales.participant_id == Participants.participant_id) \
                    .filter(Participants.college != "N/A") \
                    .filter(Sales.event_id == selected_event_id) \
                    .filter(Participants.participant_id.in_(subquery)) \
                    .all()
else:
    participants = db.query(func.sum(Sales.total_paid)) \
                    .join(Events, Sales.event_id == Events.event_id) \
                    .join(Participants, Sales.participant_id == Participants.participant_id) \
                    .scalar()


    attendees = db.query(func.count(Participants.participant_id)) \
                .join(Sales, Sales.participant_id == Participants.participant_id) \
                .scalar()


    subquery = db.query(Sales.participant_id) \
        .join(Events, Sales.event_id == Events.event_id) \
        .distinct().subquery()
    attendees_with_previous_events = db.query(func.count(Participants.participant_id)) \
        .join(Sales, Sales.participant_id == Participants.participant_id) \
        .filter(Participants.participant_id.in_(subquery)) \
        .scalar()

    college_counts = db.query(Participants.college, func.count(Participants.participant_id)) \
                    .group_by(Participants.college) \
                    .join(Sales, Sales.participant_id == Participants.participant_id) \
                    .filter(Participants.college != "N/A") \
                    .all()

    colleges_returning = db.query(Participants.college, func.count(Participants.participant_id)) \
                    .group_by(Participants.college) \
                    .join(Sales, Sales.participant_id == Participants.participant_id) \
                    .filter(Participants.college != "N/A") \
                    .filter(Participants.participant_id.in_(subquery)) \
                    .all()

kpi_banner(attendees=attendees, retention=attendees_with_previous_events, revenue=f"${participants:,.2f}")
college_cloropleth(college_counts, colleges_returning)
