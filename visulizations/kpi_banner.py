import streamlit as st
def kpi_banner(norcal, socal, attendees, retention, revenue):
    with st.container():
        st.markdown("### KPI Overview")
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric(label="Attendees", value=attendees)
        with col2:
            st.metric(label="Rentention Percentage", value=(f"{retention/attendees * 100:.2f}%" if retention is not None else "N/A"))
        with col3:
            st.metric(label="Revenue", value=revenue)
        with col4:
            st.metric(label="Total NorCal Students", value=norcal)
        with col5:
            st.metric(label="Total SoCal Students", value=socal)