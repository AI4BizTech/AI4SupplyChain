"""
Database setup and connection management.
"""
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
import sqlite3
from typing import Generator
import logging

from ..config import settings, get_database_url

# Configure logging
logger = logging.getLogger(__name__)

# Create database engine with connection pool configuration
engine_kwargs = {
    "echo": settings.database_echo,
    "pool_size": settings.database_pool_size,
    "max_overflow": settings.database_max_overflow,
    "pool_timeout": settings.database_pool_timeout,
    "pool_recycle": settings.database_pool_recycle,
    "pool_pre_ping": settings.database_pool_pre_ping,
}

# SQLite specific configuration
if "sqlite" in get_database_url():
    engine_kwargs["connect_args"] = {"check_same_thread": False}
    # SQLite doesn't support connection pooling the same way, adjust settings
    engine_kwargs["poolclass"] = None  # Use default SQLite pooling
    engine_kwargs.pop("pool_size", None)
    engine_kwargs.pop("max_overflow", None)
    engine_kwargs.pop("pool_timeout", None)
    logger.info("Using SQLite with simplified connection management")
else:
    logger.info(f"Configuring connection pool: size={settings.database_pool_size}, "
                f"overflow={settings.database_max_overflow}, "
                f"timeout={settings.database_pool_timeout}")

engine = create_engine(get_database_url(), **engine_kwargs)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable foreign key constraints for SQLite."""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def create_db_and_tables() -> None:
    """Create database tables."""
    try:
        SQLModel.metadata.create_all(engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


def get_session() -> Generator[Session, None, None]:
    """Dependency to get database session."""
    with Session(engine) as session:
        try:
            yield session
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()


def get_session_sync() -> Session:
    """Get synchronous database session."""
    return Session(engine)


# Database health check
def check_database_health() -> bool:
    """Check if database is accessible."""
    try:
        with Session(engine) as session:
            session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


def get_connection_pool_status() -> dict:
    """Get current connection pool status."""
    try:
        pool = engine.pool
        return {
            "pool_size": getattr(pool, 'size', lambda: 'N/A')(),
            "checked_in": getattr(pool, 'checkedin', lambda: 'N/A')(),
            "checked_out": getattr(pool, 'checkedout', lambda: 'N/A')(),
            "overflow": getattr(pool, 'overflow', lambda: 'N/A')(),
            "invalid": getattr(pool, 'invalid', lambda: 'N/A')(),
            "status": "SQLite" if "sqlite" in get_database_url() else "PostgreSQL/MySQL"
        }
    except Exception as e:
        logger.error(f"Error getting pool status: {e}")
        return {"error": str(e)}


# Initialize database on import
def init_database() -> None:
    """Initialize database - create tables if they don't exist."""
    try:
        create_db_and_tables()
        if check_database_health():
            logger.info("Database initialized successfully")
        else:
            logger.error("Database initialization failed - health check failed")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise