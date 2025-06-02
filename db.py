from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database connection
DATABASE_URL = "postgresql://neondb_owner:npg_Ppu9aLySJsX1@ep-round-king-a6yht3lu-pooler.us-west-2.aws.neon.tech/neondb?sslmode=require"
engine = create_engine(DATABASE_URL)

# Create session
SessionLocal = sessionmaker(bind=engine)

def query_db(query):
    """Fetch data from the database using raw SQL."""
    with engine.connect() as connection:
        return connection.execute(text(query)).fetchall()
