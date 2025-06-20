from db.database import query_db, SessionLocal
from db.models import Participants, Events, TicketTypes, Sales, Colleges
from sqlalchemy import and_
import streamlit as st
import pandas as pd
from thefuzz import fuzz, process


def merge_participants(session, keep_id, remove_id):
    session.query(Sales).filter(Sales.participant_id == remove_id).update(
        {Sales.participant_id: keep_id}
    )
    
    participant_to_remove = session.query(Participants).get(remove_id)
    if participant_to_remove:
        session.delete(participant_to_remove)
    
    session.commit()

def merge_new_data(session, df, default_event_date):

    df['college_id'] = -1
    best_match=None
    for idx, row in df.iterrows():
        st.write(f"We are on row {idx}")
        new_first_name = row['First Name'].strip().lower()
        new_last_name = row['Last Name'].strip().lower()
        new_birth_date = row['Birth Date']
        new_birth_date = pd.to_datetime(new_birth_date).date()
        new_phone_number = row['Phone Number']

        candidates = session.query(Participants).filter(
            Participants.first_name == new_first_name,
            Participants.last_name == new_last_name
        ).all()

        def is_valid_match(p):
            
            st.write(p.birth_date)
            phone_matches = new_phone_number and p.phone_number.strip().lower() == new_phone_number
            birth_matches = new_birth_date and p.birth_date == new_birth_date

            birth_conflicts = (
                p.birth_date and new_birth_date and p.birth_date != new_birth_date
            )

            return (phone_matches or birth_matches) and not birth_conflicts

        existing_participant = next((p for p in candidates if is_valid_match(p)), None)
        st.write(existing_participant)
        

        

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
                phone_number = row['Phone Number'],
                gender = row['Gender'],
                major_or_profession = row['Major or Profession'],
                last_updated = (row['Order Date'] if row['Order Date'] and pd.notna(row['Order Date']) else default_event_date),
                college_id = new_college_id,
                incomplete = row['incomplete']
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