"""
Enhanced database configuration with connection pooling and migrations support
"""
import os
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv
import logging

from app.config import settings

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Database configuration with connection pooling
engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,   # Recycle connections after 1 hour
    echo=settings.debug  # Log SQL queries in debug mode
)

# Add connection event listeners for monitoring
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Configure database connection parameters"""
    if 'postgresql' in settings.database_url:
        # PostgreSQL specific configurations
        with dbapi_connection.cursor() as cursor:
            cursor.execute("SET timezone='UTC'")


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class DatabaseManager:
    """Enhanced database session management"""
    
    @staticmethod
    def get_db():
        """Dependency to get database session with proper error handling"""
        db = SessionLocal()
        try:
            yield db
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    @staticmethod
    def create_tables():
        """Create all database tables"""
        Base.metadata.create_all(bind=engine)
    
    @staticmethod
    def drop_tables():
        """Drop all database tables (use with caution)"""
        Base.metadata.drop_all(bind=engine)
    
    @staticmethod
    def check_connection():
        """Check database connectivity"""
        try:
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception as e:
            logging.error(f"Database connection failed: {e}")
            return False


# Global database manager instance
db_manager = DatabaseManager()

# Backwards compatibility
get_db = db_manager.get_db
