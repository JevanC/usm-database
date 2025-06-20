import pandas as pd
import streamlit as st
from db.models import Participants, Events, TicketTypes, Sales, Colleges
from db.database import query_db, SessionLocal
from add_new_event import merge_participants

def assign_null_people(session):
    null_people_df = pd.DataFrame((session.query(Participants.participant_id, Participants.first_name, Participants.last_name, Participants.birth_date).filter(Participants.birth_date == '1901-01-01').all()))
    confirmed_people_df = pd.DataFrame((session.query(Participants.participant_id, Participants.first_name, Participants.last_name, Participants.birth_date).filter(Participants.birth_date != '1901-01-01').all()))
    selected_change = st.selectbox('Select Unknown Person', ['select'] + list(null_people_df.first_name))
    if selected_change != 'select':
        selected_participant_id = int(null_people_df[null_people_df['first_name'] == selected_change].participant_id)
        st.write(selected_participant_id)
        st.write("Missing Person Information")
        missing_person_event_details = session.query(Events.event_id, Events.event_name, Events.location, Events.year) \
                .join(Sales, Events.event_id == Sales.event_id) \
                .filter(Sales.participant_id == selected_participant_id).all()
        st.write(missing_person_event_details)
        st.write('Potential Matches: ')
        subquery = session.query(Sales.participant_id).filter(Sales.event_id == missing_person_event_details[0].event_id)
        st.write(session.query(Participants.participant_id, Participants.first_name, Participants.last_name, Participants.birth_date) \
                .filter(Participants.first_name == selected_change) \
                .filter(Participants.birth_date != '1901-01-01') \
                .filter(~Participants.participant_id.in_(subquery)).all())

        with st.form("Update Missing People"):
            remove = selected_participant_id
            keep = st.text_input("Who Is This Person? (ID)")
            submitted = st.form_submit_button("Submit")

            if submitted:
                try:
                    remove_id = int(remove)
                    keep_id = int(keep)

                    null_ids = null_people_df["participant_id"].astype(int).tolist()
                    confirmed_ids = confirmed_people_df["participant_id"].astype(int).tolist()

                    if remove_id not in null_ids or keep_id not in confirmed_ids:
                        st.warning("ERROR: One or both participant IDs are invalid. Try again.")
                    else:
                        merge_participants(keep_id=keep_id, remove_id=remove_id)
                        st.success(f"Participant {remove_id} successfully merged into {keep_id}.")
                        st.rerun()
                except ValueError:
                    st.error("Please enter valid integer IDs.")