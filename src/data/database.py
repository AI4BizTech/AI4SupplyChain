"""
Database connection and session management
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
from contextlib import contextmanager
from typing import Optional, Generator
import logging

from src.config import DATABASE_URL
from src.data.base import Base
from src.data.inventory import Product, Supplier, Location, Inventory, Transaction
from src.data.forecast import ForecastResult, ForecastAccuracy

logger = logging.getLogger(__name__)

class Database:
    """Database connection and session management"""
    
    def __init__(self, database_url: str = DATABASE_URL):
        self.database_url = database_url
        self.engine = create_engine(
            database_url,
            echo=False,  # Set to True for SQL debugging
            pool_pre_ping=True,  # Verify connections before use
        )
        
        # Enable foreign key constraints for SQLite
        if "sqlite" in database_url:
            @event.listens_for(Engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
        
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def create_tables(self):
        """Create all database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise
    
    def drop_tables(self):
        """Drop all database tables (use with caution!)"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Error dropping database tables: {e}")
            raise
    
    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """Get a database session with automatic cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def get_session(self) -> Session:
        """Get a database session (remember to close it!)"""
        return self.SessionLocal()

# Global database instance
_database: Optional[Database] = None

def get_database() -> Database:
    """Get or create the global database instance"""
    global _database
    if _database is None:
        _database = Database()
        _database.create_tables()
    return _database

def init_database(database_url: str = DATABASE_URL) -> Database:
    """Initialize database with custom URL"""
    global _database
    _database = Database(database_url)
    _database.create_tables()
    return _database
