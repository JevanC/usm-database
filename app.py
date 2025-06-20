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
from dotenv import load_dotenv
import os

load_dotenv() 

st.set_page_config(page_title="Event Sales Dashboard", layout="wide")

st.title("Event Sales Dashboard")
st.sidebar.success("Select Dashboard")


