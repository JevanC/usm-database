from sqlalchemy.orm import sessionmaker, joinedload
from db.database import query_db, SessionLocal
from db.models import Participants, Events, TicketTypes, Sales, Colleges
from sqlalchemy import func

def get_norcal_yoy(session, selected_name):
    return session.query(Events.event_name, Events.location, Events.year, func.count(Participants.participant_id)) \
            .join(Colleges, Colleges.college_id == Participants.college_id) \
            .join(Sales, Sales.participant_id == Participants.participant_id) \
            .join(Events, Events.event_id == Sales.event_id) \
            .filter(Colleges.state == "CA") \
            .filter(Colleges.latitude >= 37) \
            .filter(Events.event_name == selected_name) \
            .group_by(Events.event_name, Events.year, Events.location)\
            .order_by(Events.year)\
            .all()

def get_scocal_yoy(session, selected_name):
        return session.query(Events.event_name, Events.location, Events.year, func.count(Participants.participant_id)) \
            .join(Colleges, Colleges.college_id == Participants.college_id) \
            .join(Sales, Sales.participant_id == Participants.participant_id) \
            .join(Events, Events.event_id == Sales.event_id) \
            .filter(Colleges.state == "CA") \
            .filter(Colleges.latitude < 37) \
            .filter(Events.event_name == selected_name) \
            .group_by(Events.event_name, Events.year, Events.location)\
            .order_by(Events.year)\
            .all()

def get_events(session):
     return session.query(Events.event_id, Events.event_name, Events.location).all()

def get_event_id(session, events, selected_event):
    return next(event.event_id for event in events if f"{event.event_name} {event.location}" == selected_event)

def get_event_year(session, selected_event_id):
    return int(session.query(Events.year).filter(Events.event_id == selected_event_id).scalar())

def get_total_revenue(session, selected_event_id):
    if selected_event_id is not None:
        return float(session.query(func.sum(Sales.total_paid)) \
                        .join(Events, Sales.event_id == Events.event_id) \
                        .join(Participants, Sales.participant_id == Participants.participant_id) \
                        .filter(Events.event_id == selected_event_id) \
                        .scalar())
    else:
        return float(session.query(func.sum(Sales.total_paid)) \
                        .join(Events, Sales.event_id == Events.event_id) \
                        .join(Participants, Sales.participant_id == Participants.participant_id) \
                        .scalar())

def get_attendees(session, selected_event_id):
    if selected_event_id is not None:
        return int(session.query(func.count(Participants.participant_id)) \
                .join(Sales, Sales.participant_id == Participants.participant_id) \
                .filter(Sales.event_id == selected_event_id) \
                .scalar())
    else:
        return int(session.query(func.count(Participants.participant_id)) \
                .join(Sales, Sales.participant_id == Participants.participant_id) \
                .scalar())

def past_pariticpant_ids(session, selected_event_year):
    if selected_event_year is not None:
        return session.query(Sales.participant_id) \
        .join(Events, Sales.event_id == Events.event_id) \
        .filter(Events.year < selected_event_year) \
        .distinct().subquery()

def get_returning_participants(session, selected_event_id):
    if selected_event_id is not None:
        selected_event_year = get_event_year(session, selected_event_id)
        subquery = past_pariticpant_ids(session=session, selected_event_year=selected_event_year)
        return int(session.query(func.count(Participants.participant_id)) \
            .join(Sales, Sales.participant_id == Participants.participant_id) \
            .filter(Sales.event_id == selected_event_id) \
            .filter(Participants.participant_id.in_(subquery)) \
            .scalar())
    
def get_colleges_counts(session, selected_event_id):
    if selected_event_id is not None:
        return session.query(Colleges.name, func.count(Participants.participant_id)) \
                    .join(Colleges, Colleges.college_id == Participants.college_id) \
                    .join(Sales, Sales.participant_id == Participants.participant_id) \
                    .filter(Participants.college_id != None) \
                    .filter(Sales.event_id == selected_event_id) \
                    .group_by(Colleges.college_id) \
                    .all()
    else:
        return session.query(Colleges.name, func.count(Participants.participant_id)) \
                    .join(Colleges, Colleges.college_id == Participants.college_id) \
                    .join(Sales, Sales.participant_id == Participants.participant_id) \
                    .filter(Participants.college_id != None) \
                    .group_by(Colleges.college_id) \
                    .all()

def past_colleges(session, selected_event_id):
    if selected_event_id is not None:
        selected_event_year = get_event_year(session, selected_event_id=selected_event_id)
        return ( session.query(Colleges.college_id)
            .join(Participants, Colleges.college_id == Participants.college_id)
            .join(Sales, Sales.participant_id == Participants.participant_id)
            .join(Events, Sales.event_id == Events.event_id)
            .filter(Events.year < selected_event_year)
            .group_by(Colleges.college_id)
            .having(func.count(Participants.participant_id) >= 1)
            .subquery()
        )
    else:
        return None

def get_returning_colleges(session, selected_event_id):
    if selected_event_id is not None:
        college_returning_subquery = past_colleges(session=session, selected_event_id=selected_event_id)
        return (
            session.query(Colleges.name, func.count(Participants.participant_id))
            .join(Participants, Colleges.college_id == Participants.college_id)
            .join(Sales, Sales.participant_id == Participants.participant_id)
            .filter(Participants.college_id != None)
            .filter(Sales.event_id == selected_event_id)
            .filter(Colleges.college_id.in_(college_returning_subquery))
            .group_by(Colleges.college_id)
            .all()
        )
    
    
def get_norcal(session, selected_event_id):
    if selected_event_id is not None:
        return int(session.query(func.count(Participants.participant_id)) \
            .join(Colleges, Colleges.college_id == Participants.college_id) \
            .join(Sales, Sales.participant_id == Participants.participant_id) \
            .filter(Colleges.state == "CA") \
            .filter(Colleges.latitude >= 37) \
            .filter(Sales.event_id == selected_event_id) \
            .scalar())
    else:
        return int(session.query(func.count(Participants.participant_id)) \
            .join(Colleges, Colleges.college_id == Participants.college_id) \
            .join(Sales, Sales.participant_id == Participants.participant_id) \
            .filter(Colleges.state == "CA") \
            .filter(Colleges.latitude >= 37) \
            .scalar())

def get_socal(session, selected_event_id):
    if selected_event_id is not None:
        return int(session.query(func.count(Participants.participant_id)) \
            .join(Colleges, Colleges.college_id == Participants.college_id) \
            .join(Sales, Sales.participant_id == Participants.participant_id) \
            .filter(Colleges.state == "CA") \
            .filter(Colleges.latitude < 37) \
            .filter(Sales.event_id == selected_event_id) \
            .scalar())
    else:
        return int(session.query(func.count(Participants.participant_id)) \
            .join(Colleges, Colleges.college_id == Participants.college_id) \
            .join(Sales, Sales.participant_id == Participants.participant_id) \
            .filter(Colleges.state == "CA") \
            .filter(Colleges.latitude < 37) \
            .scalar())