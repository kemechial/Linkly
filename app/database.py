from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Change this to your actual DB in production (for now, use SQLite)
DATABASE_URL = "sqlite:///./linkly.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}  # Only needed for SQLite
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()