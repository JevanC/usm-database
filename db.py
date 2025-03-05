from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database connection
DATABASE_URL = "postgresql://jevanchahal:jbrosQ78@localhost/usm"
engine = create_engine(DATABASE_URL)

# Create session
SessionLocal = sessionmaker(bind=engine)

def query_db(query):
    """Fetch data from the database using raw SQL."""
    with engine.connect() as connection:
        return connection.execute(text(query)).fetchall()
