from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import URL
import os
from dotenv import load_dotenv

load_dotenv()

# Check if DATABASE_URL is set in the environment (e.g., on deployment platforms)
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # If a full URL is provided via env var, use it directly
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
else:
    # Build the URL programmatically so special characters in the password
    # are handled correctly by SQLAlchemy (no manual percent-encoding needed)
    db_url = URL.create(
        drivername="postgresql",
        username=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "A8!m.7%,ySTQ%Cq"),
        host=os.getenv("DB_HOST", "db.qafqqzdbmtziehxscjld.supabase.co"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME", "postgres"),
    )
    engine = create_engine(db_url, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
