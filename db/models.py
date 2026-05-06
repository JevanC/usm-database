from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime, Text, Boolean, Numeric, ForeignKey, UniqueConstraint, Float
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class TicketTypes(Base):
    __tablename__ = 'ticket_types'
    ticket_id = Column(Integer, primary_key=True)
    ticket_type = Column(String(100), nullable=False, unique=True)

    sales = relationship("Sales", back_populates="ticket")

class Colleges(Base):
    __tablename__ = 'colleges'
    college_id = Column(Integer, primary_key=True)
    name = Column(String)
    latitude = Column(Float)  # Double Precision
    longitude = Column(Float)  # Double Precision
    city = Column(String)
    state = Column(String(2))
    zip = Column(String(5))  # Typical zip length
    county = Column(String)
    country = Column(String)

    #participants = relationship("Participants", back_populates="college")

class Participants(Base):
    __tablename__ = 'participants'
    participant_id = Column(Integer, primary_key=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    birth_date = Column(Date)
    home_address = Column(String(100))
    home_city = Column(String(50))
    home_state = Column(String(50))
    home_zip = Column(String(10))
    phone_number = Column(String(20))
    gender = Column(String(20))
    major_or_profession = Column(Text)
    incomplete = Column(Boolean)
    last_updated = Column(DateTime)
    college_id = Column(Integer, ForeignKey('colleges.college_id'))  # ForeignKey linking to colleges table

    
    #colleges = relationship("Colleges", back_populates="participants")

    sales = relationship("Sales", back_populates="participant")

    __table_args__ = (UniqueConstraint('first_name', 'last_name', 'birth_date', name='unique_participant'),)

class Events(Base):
    __tablename__ = 'events'
    event_id = Column(Integer, primary_key=True)
    event_name = Column(String(50), nullable=False)
    year = Column(Integer, nullable=False)
    location = Column(String(50), nullable=False)

    sales = relationship("Sales", back_populates="event")

    __table_args__ = (UniqueConstraint('event_name', 'year', 'location', name='unique_event'),)

class Sales(Base):
    __tablename__ = 'sales'
    sales_id = Column(Integer, primary_key=True)
    order_date = Column(DateTime, nullable=False)
    total_paid = Column(Numeric(10, 2), nullable=False)
    fees_paid = Column(Numeric(10, 2), nullable=False)
    friday_hotel = Column(Boolean, nullable=False, default=False)
    saturday_hotel = Column(Boolean, nullable=False, default=False)
    sunday_hotel = Column(Boolean, nullable=False, default=False)

    event_id = Column(Integer, ForeignKey('events.event_id', ondelete="CASCADE"))
    participant_id = Column(Integer, ForeignKey('participants.participant_id', ondelete="SET NULL", onupdate="CASCADE"))
    ticket_id = Column(Integer, ForeignKey('ticket_types.ticket_id', ondelete='SET NULL', onupdate="CASCADE"))

    event = relationship("Events", back_populates="sales")
    participant = relationship("Participants", back_populates="sales")
    ticket = relationship("TicketTypes", back_populates="sales")
