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

st.set_page_config(page_title="Event Sales Dashboard", layout="wide")
st.title('📊 Welcome to the USM Events Dashboard')
st.markdown("""
This interactive dashboard helps you explore, manage, and analyze event data with ease.<br>
👉 Use the sidebar to:<br>
<b>View Dashboard:</b> Explore key metrics and visual insights<br>
<b>Add Data:</b> Upload and clean your event CSVs<br>
<b>Talk to AI:</b> Ask questions about your data in natural language<br><br>
Get started by choosing an option from the sidebar!
""", unsafe_allow_html=True)


