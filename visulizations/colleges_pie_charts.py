import streamlit as st
import plotly.express as px
import pandas as pd

def pie_charts(college_counts, returning_colleges, ticket_types):    
    df_total = pd.DataFrame(college_counts, columns=["College", "Count"]).sort_values(by="Count", ascending=False)
    df_returning = pd.DataFrame(returning_colleges, columns=["College", "Count"]).sort_values(by="Count", ascending=False)
    df_tickets = pd.DataFrame(ticket_types, columns=["Ticket Type", "Sales"]).sort_values(by="Sales", ascending=False)

    fig_total = px.pie(df_total, names="College", values="Count", title="Total College Attendance")
    fig_returning = px.pie(df_returning, names="College", values="Count", title="Returning College Attendance")
    fig_tickets = px.pie(df_tickets, names="Ticket Type", values="Sales", title="Sales by Ticket Types")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"### Total Colleges: {len(college_counts)}")
        st.plotly_chart(fig_total, use_container_width=True, key="college_chart_total")

    with col2:
        st.markdown(f"### Returning Colleges: {len(returning_colleges) if returning_colleges is not None else 'N/A'}")
        st.plotly_chart(fig_returning, use_container_width=True, key="college_chart_returning")
    
    st.markdown(f'### Total Ticket Types')
    st.plotly_chart(fig_tickets, use_container_width=True, key="ticket_type_sales")