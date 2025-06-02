import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from sqlalchemy.orm import sessionmaker, joinedload
from db import query_db, SessionLocal
from models import Participants, Events, TicketTypes, Sales, Colleges
from sqlalchemy import func, and_
from clean_data import clean_data
from thefuzz import fuzz, process
from datetime import datetime
import numpy as np

def kpi_banner(norcal, socal, attendees, retention, revenue):
    with st.container():
        st.markdown("### KPI Overview")
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric(label="Attendees", value=attendees)
        with col2:
            st.metric(label="Rentention Percentage", value=(f"{retention/attendees * 100:.2f}%"))
        with col3:
            st.metric(label="Revenue", value=revenue)
        with col4:
            st.metric(label="Total NorCal Students", value=norcal)
        with col5:
            st.metric(label="Total SoCal Students", value=socal)

def college_cloropleth(colleges_count, returning_colleges_count):
    # Filter out colleges with less than 2 attendees
    filtered_total = [(college, count) for college, count in colleges_count if count >= 2]
    filtered_returning = [(college, count) for college, count in returning_colleges_count if count >= 2]

    total_colleges = len(filtered_total)
    returning_colleges = len(filtered_returning)

    # Convert to DataFrame
    df_total = pd.DataFrame(filtered_total, columns=["College", "Count"]).sort_values(by="Count", ascending=False)
    df_returning = pd.DataFrame(filtered_returning, columns=["College", "Count"]).sort_values(by="Count", ascending=False)

    # Pie Charts
    fig_total = px.pie(df_total, names="College", values="Count", title="Total College Attendance")
    fig_returning = px.pie(df_returning, names="College", values="Count", title="Returning College Attendance")

    # Display in columns
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"### Total Colleges (2+ attendees): {total_colleges}")
        st.plotly_chart(fig_total, use_container_width=True, key="college_chart_total")

    with col2:
        st.markdown(f"### Returning Colleges (2+ attendees): {returning_colleges}")
        st.plotly_chart(fig_returning, use_container_width=True, key="college_chart_returning")
    

def compare_nor_so_cal(selected_name):
        norcal = session.query(Events.event_name, Events.location, Events.year, func.count(Participants.participant_id)) \
            .join(Colleges, Colleges.college_id == Participants.college_id) \
            .join(Sales, Sales.participant_id == Participants.participant_id) \
            .join(Events, Events.event_id == Sales.event_id) \
            .filter(Colleges.state == "CA") \
            .filter(Colleges.latitude >= 37) \
            .filter(Events.event_name == selected_name) \
            .group_by(Events.event_name, Events.year, Events.location)\
            .order_by(Events.year)\
            .all()
        
        socal = session.query(Events.event_name, Events.location, Events.year, func.count(Participants.participant_id)) \
            .join(Colleges, Colleges.college_id == Participants.college_id) \
            .join(Sales, Sales.participant_id == Participants.participant_id) \
            .join(Events, Events.event_id == Sales.event_id) \
            .filter(Colleges.state == "CA") \
            .filter(Colleges.latitude < 37) \
            .filter(Events.event_name == selected_name) \
            .group_by(Events.event_name, Events.year, Events.location)\
            .order_by(Events.year)\
            .all()
        
        
        norcal_df = pd.DataFrame(norcal, columns=['Event', 'Location', 'Year', 'NorCal'])
        socal_df = pd.DataFrame(socal, columns=['Event','Location', 'Year', 'SoCal'])
        df=pd.merge(norcal_df, socal_df, on=['Event','Location', 'Year'], how='outer')

        df['Event'] = df.apply(lambda x : f"{x['Event']} {x['Location']}", axis=1)
        df['Last Year NorCal'] = ((df['NorCal'] - df['NorCal'].shift(1)) / df['NorCal'].shift(1) * 100).round(2)

        df['Last Year SoCal'] = ((df['SoCal'] - df['SoCal'].shift(1)) / df['SoCal'].shift(1) * 100).round(2)

        df['Two Year Ago NorCal'] = ((df['NorCal'] - df['NorCal'].shift(1)) / df['NorCal'].shift(2) * 100).round(2)
        df['Two Year Ago SoCal'] = ((df['SoCal'] - df['SoCal'].shift(1)) / df['SoCal'].shift(2) * 100).round(2)

        df[['Event', 'Year', 'Last Year NorCal', 'Last Year SoCal', 'Two Year Ago NorCal', 'Two Year Ago SoCal']]
        

st.set_page_config(page_title="Event Sales Dashboard", layout="wide")

st.title("Event Sales Dashboard")



session = SessionLocal()

events = session.query(Events.event_id, Events.event_name, Events.location).all()

event_options = ["ALL"] + [f"{event.event_name} {event.location}" for event in events]

selected_event = st.selectbox("Select Event", event_options)

if selected_event != "ALL":
    selected_event_id = next(event.event_id for event in events if f"{event.event_name} {event.location}" == selected_event)
    selected_event_year = session.query(Events.year).filter(Events.event_id == selected_event_id).scalar()

    participants = session.query(func.sum(Sales.total_paid)) \
                    .join(Events, Sales.event_id == Events.event_id) \
                    .join(Participants, Sales.participant_id == Participants.participant_id) \
                    .filter(Events.event_id == selected_event_id) \
                    .scalar()


    attendees = session.query(func.count(Participants.participant_id)) \
                .join(Sales, Sales.participant_id == Participants.participant_id) \
                .filter(Sales.event_id == selected_event_id) \
                .scalar()


    subquery = session.query(Sales.participant_id) \
        .join(Events, Sales.event_id == Events.event_id) \
        .filter(Events.year < selected_event_year) \
        .distinct().subquery()
    attendees_with_previous_events = session.query(func.count(Participants.participant_id)) \
        .join(Sales, Sales.participant_id == Participants.participant_id) \
        .filter(Sales.event_id == selected_event_id) \
        .filter(Participants.participant_id.in_(subquery)) \
        .scalar()

    college_counts = session.query(Colleges.name, func.count(Participants.participant_id)) \
                    .join(Colleges, Colleges.college_id == Participants.college_id) \
                    .join(Sales, Sales.participant_id == Participants.participant_id) \
                    .filter(Participants.college_id != None) \
                    .filter(Sales.event_id == selected_event_id) \
                    .group_by(Colleges.college_id) \
                    .all()

    college_returning_subquery = (
    session.query(Colleges.college_id)
    .join(Participants, Colleges.college_id == Participants.college_id)
    .join(Sales, Sales.participant_id == Participants.participant_id)
    .join(Events, Sales.event_id == Events.event_id)
    .filter(Events.year < selected_event_year)
    .group_by(Colleges.college_id)
    .having(func.count(Participants.participant_id) >= 2)
    .subquery()
)

# Main query: get college names and participant counts for qualifying colleges
    colleges_returning = (
        session.query(Colleges.name, func.count(Participants.participant_id))
        .join(Participants, Colleges.college_id == Participants.college_id)
        .join(Sales, Sales.participant_id == Participants.participant_id)
        .filter(Participants.college_id != None)
        .filter(Sales.event_id == selected_event_id)
        .filter(Colleges.college_id.in_(college_returning_subquery))
        .group_by(Colleges.college_id)
        .all()
    )
    
    norcal = session.query(func.count(Participants.participant_id)) \
        .join(Colleges, Colleges.college_id == Participants.college_id) \
        .join(Sales, Sales.participant_id == Participants.participant_id) \
        .filter(Colleges.state == "CA") \
        .filter(Colleges.latitude >= 37) \
        .filter(Sales.event_id == selected_event_id) \
        .scalar()
    
    socal = session.query(func.count(Participants.participant_id)) \
        .join(Colleges, Colleges.college_id == Participants.college_id) \
        .join(Sales, Sales.participant_id == Participants.participant_id) \
        .filter(Colleges.state == "CA") \
        .filter(Colleges.latitude < 37) \
        .filter(Sales.event_id == selected_event_id) \
        .scalar()
        
    
    
else:
    participants = session.query(func.sum(Sales.total_paid)) \
                    .join(Events, Sales.event_id == Events.event_id) \
                    .join(Participants, Sales.participant_id == Participants.participant_id) \
                    .scalar()


    attendees = session.query(func.count(Participants.participant_id)) \
                .join(Sales, Sales.participant_id == Participants.participant_id) \
                .scalar()


    subquery = session.query(Sales.participant_id) \
        .join(Events, Sales.event_id == Events.event_id) \
        .distinct().subquery()
    attendees_with_previous_events = session.query(func.count(Participants.participant_id)) \
        .join(Sales, Sales.participant_id == Participants.participant_id) \
        .filter(Participants.participant_id.in_(subquery)) \
        .scalar()

    college_counts = session.query(Colleges.name, func.count(Participants.participant_id)) \
                    .join(Colleges, Colleges.college_id == Participants.college_id) \
                    .join(Sales, Sales.participant_id == Participants.participant_id) \
                    .filter(Participants.college_id != None) \
                    .group_by(Colleges.college_id) \
                    .all()

    colleges_returning = session.query(Colleges.name, func.count(Participants.participant_id)) \
                    .join(Colleges, Colleges.college_id == Participants.college_id) \
                    .join(Sales, Sales.participant_id == Participants.participant_id) \
                    .filter(Participants.college_id != None) \
                    .filter(Participants.participant_id.in_(subquery)) \
                    .group_by(Colleges.college_id) \
                    .all()
    
    norcal = session.query(func.count(Participants.participant_id)) \
        .join(Colleges, Colleges.college_id == Participants.college_id) \
        .join(Sales, Sales.participant_id == Participants.participant_id) \
        .filter(Colleges.state == "CA") \
        .filter(Colleges.latitude >= 37) \
        .scalar()
    
    socal = session.query(func.count(Participants.participant_id)) \
        .join(Colleges, Colleges.college_id == Participants.college_id) \
        .join(Sales, Sales.participant_id == Participants.participant_id) \
        .filter(Colleges.state == "CA") \
        .filter(Colleges.latitude < 37) \
        .scalar()

kpi_banner(norcal=norcal, socal=socal, attendees=attendees, retention=attendees_with_previous_events, revenue=f"${participants:,.2f}")
college_cloropleth(college_counts, colleges_returning)
compare_nor_so_cal("Inter-SSA Conference")
def merge_new_data(df, default_event_date):

    df['college_id'] = -1
    for idx, row in df.iterrows():
        st.write(f"We are on row {idx}")
        new_first_name = row['First Name']
        new_last_name = row['Last Name']
        new_birth_date = row['Birth Date']

        existing_participant = session.query(Participants).filter(
            and_(
                Participants.first_name == new_first_name,
                Participants.last_name == new_last_name,
                Participants.birth_date == new_birth_date
            )
        ).first()

        new_college_id = None
        if existing_participant is None:
            college_list = [c[0] for c in session.query(Colleges.name).all()]
            original_college_name = row['What school are you currently attending?']
            excluded_list = ['high school', 'graduate student', 'other', 'n/a']

            if pd.isna(original_college_name) or original_college_name.lower() in excluded_list:
                df.loc[idx, 'college_id'] = None
            else:
                best_match = process.extractOne(original_college_name, college_list, scorer=fuzz.token_sort_ratio)
                if best_match and best_match[1] >= 95:
                    new_college_id = session.query(Colleges.college_id).filter(
                        Colleges.name == best_match[0]
                    ).scalar()
                df.loc[idx, 'college_id'] = new_college_id

            new_participant = Participants(
                first_name = new_first_name,
                last_name = new_last_name,
                birth_date = new_birth_date,
                home_address = row['Home Address 1'],
                home_city = row['Home City'],
                home_state = row['Home State'],
                home_zip = row['Home Zip'],
                phone_number = row['Cell Phone'],
                gender = row['Gender'],
                major_or_profession = row['What is your major/profession?'],
                college = best_match[0] if best_match else None,
                last_updated = (row['Order Date'] if row['Order Date'] and pd.notna(row['Order Date']) else default_event_date),
                college_id = new_college_id
            )
            session.add(new_participant)
            session.commit()
            row_participant_id = new_participant.participant_id
        else:
            row_participant_id = existing_participant.participant_id
            st.write(f"{existing_participant.first_name} Already Exists")
        
        existing_event = session.query(Events).filter(
            and_(
                Events.event_name == row['event_name'],
                Events.location == row['event_location'],
                Events.year == row['event_year']
            )
        ).first()

        if existing_event is None and (row['event_name'], row['event_location'], row['event_year']):
            new_event = Events(
                event_name = row['event_name'],
                location = row['event_location'],
                year = row['event_year']
            )
            session.add(new_event)
            session.commit()
            row_event_id = new_event.event_id
        else:
            row_event_id = existing_event.event_id
            st.write(f"{existing_event.event_name} Already Exists")

        existing_ticket_type = session.query(TicketTypes).filter(
            and_(TicketTypes.ticket_type == row['Ticket Type'])
        ).first()
        
        if existing_ticket_type is None:
            new_ticket_type = TicketTypes(
                ticket_type = row['Ticket Type']
            )
            session.add(new_ticket_type)
            session.commit()
            row_ticket_id = new_ticket_type.ticket_id
        else:
            row_ticket_id = existing_ticket_type.ticket_id
            st.write(f"{existing_ticket_type.ticket_type} Already Exists")
        
        existing_sale = session.query(Sales).filter(
            and_(
                Sales.event_id == row_event_id,
                Sales.participant_id == row_participant_id,
                Sales.ticket_id == row_ticket_id,
                Sales.order_date == (row['Order Date'] if row['Order Date'] and pd.notna(row['Order Date']) else default_event_date)
                 )
        ).first()

        if existing_sale is None:
            new_sale = Sales(
            order_date = (row['Order Date'] if row['Order Date'] and pd.notna(row['Order Date']) else default_event_date),
            total_paid = row['Total Paid'],
            fees_paid = row['Fees Paid'],
            friday_hotel = row['friday_hotel'],
            saturday_hotel = row['saturday_hotel'],
            sunday_hotel = row['sunday_hotel'],
            event_id = row_event_id,
            participant_id = row_participant_id,
            ticket_id = row_ticket_id)
            st.write(f"SALE HAS GONE THROUGH")
            session.add(new_sale)
            session.commit()
        
        
st.title("CSV Uploader")
uploaded = st.file_uploader("Upload your file here", type=["csv"])

if uploaded is not None:
    new_event_name = st.text_input(label="What is the event name?")
    new_event_year = st.text_input(label="What is the event year?")
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
        new_event_data[['event_name', 'event_year', 'event_location']] = new_event_name, new_event_year, new_event_location
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

#if st.button("FLUSH"):
    #for i in st.session_state.new_participants:
        #session.add(i)
    #    st.write(f"New Participant {i}")
    #for i in st.session_state.new_events:
        #session.add(i)
    #    st.write(f"New Event {i.event_name} {i.year} {i.location}")
    #for i in st.session_state.new_tickets:
        #session.add(i)
    #    st.write(f"New Ticket {i}")
    #for i in st.session_state.new_sales:
        #session.add(i)
    #    st.write(f"New Sale {i}")
    #session.flush()