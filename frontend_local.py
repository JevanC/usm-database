import streamlit as st
import pandas as pd
from db import query_db

st.set_page_config(page_title="Event Sales Dashboard", layout="wide")

st.title("Event Sales Dashboard")

# Fetch sales data
sales_data = pd.DataFrame(query_db("SELECT * FROM sales"))

# Display Data
st.subheader("Sales Data")
st.dataframe(sales_data)

# Filter by Event
event_names = [row[0] for row in query_db("SELECT DISTINCT event_name FROM events")]
selected_event = st.selectbox("Select Event", ["All"] + event_names)

if selected_event != "All":
    sales_data = pd.DataFrame(query_db(f"SELECT * FROM sales WHERE event_id IN (SELECT event_id FROM events WHERE event_name = '{selected_event}')"))

st.subheader("Filtered Sales Data")
st.dataframe(sales_data)

# Metrics
st.metric("Total Revenue", f"${sales_data['total_paid'].sum():,.2f}")
st.metric("Total Fees Collected", f"${sales_data['fees_paid'].sum():,.2f}")

# Chart Example
st.subheader("Revenue by Event")
chart_data = pd.DataFrame(query_db("SELECT e.event_name, SUM(s.total_paid) as revenue FROM sales s JOIN events e ON s.event_id = e.event_id GROUP BY e.event_name"))
st.bar_chart(chart_data.set_index("event_name"))

# Run the app with: `streamlit run app.py`
