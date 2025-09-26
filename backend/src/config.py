"""
Centralized configuration for AI4SupplyChain backend system.
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Database Configuration
    database_url: str = "sqlite:///./data/inventory.db"
    database_echo: bool = False  # Set to True for SQL query logging

    # Database Connection Pool Configuration
    database_pool_size: int = 20  # Base connection pool size
    database_max_overflow: int = 30  # Additional connections when pool is full
    database_pool_timeout: int = 30  # Timeout for getting connection from pool
    database_pool_recycle: int = 3600  # Recycle connections after 1 hour
    database_pool_pre_ping: bool = True  # Validate connections before use
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    api_title: str = "AI4SupplyChain Inventory API"
    api_version: str = "1.0.0"
    api_description: str = "AI-powered dynamic inventory and demand planning system"
    
    # File Storage Configuration
    data_directory: Path = Path("./data")
    uploads_directory: Path = Path("./data/uploads")
    exports_directory: Path = Path("./data/exports")
    logs_directory: Path = Path("./data/logs")
    sample_data_directory: Path = Path("./data/sample_data")
    
    # Security Configuration
    secret_key: str = "your-secret-key-change-in-production"
    access_token_expire_minutes: int = 30
    
    # Pagination Configuration
    default_page_size: int = 50
    max_page_size: int = 1000
    
    # Business Rules Configuration
    allow_negative_inventory: bool = False
    auto_create_inventory_records: bool = True
    default_reorder_point: int = 10
    default_reorder_quantity: int = 50
    
    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = "../.env"  # Look for .env in project root
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()


def ensure_directories() -> None:
    """Ensure all required directories exist."""
    directories = [
        settings.data_directory,
        settings.uploads_directory,
        settings.exports_directory,
        settings.logs_directory,
        settings.sample_data_directory,
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def get_database_url() -> str:
    """Get the database URL with proper path resolution."""
    if settings.database_url.startswith("sqlite:///"):
        # Ensure the database directory exists
        db_path = Path(settings.database_url.replace("sqlite:///", ""))
        db_path.parent.mkdir(parents=True, exist_ok=True)
    
    return settings.database_url


# Development helper functions
def is_development() -> bool:
    """Check if running in development mode."""
    return settings.api_reload


def is_testing() -> bool:
    """Check if running in test mode."""
    return "pytest" in os.environ.get("_", "")


# Initialize directories on import
ensure_directories()