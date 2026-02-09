"""
SkyPulse 2.0 - Database Setup
Handles database connection, session management, and initialization.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
import logging

from config import Config
from models.schemas import Base

logger = logging.getLogger(__name__)

# Create engine
engine = create_engine(
    Config.DATABASE_URL,
    echo=(Config.LOG_LEVEL == "DEBUG"),
    pool_pre_ping=True,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Session = scoped_session(SessionLocal)


def init_db():
    """Initialize database - create all tables"""
    logger.info("Initializing database...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully")


def drop_db():
    """Drop all tables - use with caution!"""
    logger.warning("Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    logger.info("Database dropped")


@contextmanager
def get_db():
    """
    Context manager for database sessions.
    Usage:
        with get_db() as db:
            user = db.query(User).first()
    """
    db = Session()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        db.close()


def get_db_session():
    """
    Get a database session (caller is responsible for closing).
    Usage:
        db = get_db_session()
        try:
            user = db.query(User).first()
            db.commit()
        finally:
            db.close()
    """
    return Session()


if __name__ == "__main__":
    # Allow running as script to initialize database
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        init_db()
        print("✅ Database initialized")
    elif len(sys.argv) > 1 and sys.argv[1] == "drop":
        confirm = input("Are you sure you want to drop all tables? (yes/no): ")
        if confirm.lower() == "yes":
            drop_db()
            print("✅ Database dropped")
    else:
        print("Usage: python -m models.database [init|drop]")
