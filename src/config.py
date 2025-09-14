"""
Configuration settings for AI4SupplyChain
"""

import os
from pathlib import Path
from typing import Optional

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/inventory.db")
DATABASE_PATH = Path("./data/inventory.db")

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GOOGLE_CLOUD_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# OCR Configuration
OCR_PROVIDER = os.getenv("OCR_PROVIDER", "tesseract")  # tesseract, google, aws
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Application settings
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# LLM Configuration
PRIMARY_LLM_PROVIDER = os.getenv("PRIMARY_LLM_PROVIDER", "openai")  # openai, anthropic
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1000"))

# Business Logic Defaults
DEFAULT_REORDER_POINT = int(os.getenv("DEFAULT_REORDER_POINT", "10"))
DEFAULT_REORDER_QUANTITY = int(os.getenv("DEFAULT_REORDER_QUANTITY", "50"))
DEFAULT_LEAD_TIME_DAYS = int(os.getenv("DEFAULT_LEAD_TIME_DAYS", "7"))

# Data directories
DATA_DIR = Path("./data")
SAMPLE_DATA_DIR = DATA_DIR / "sample_data"
EXPORTS_DIR = DATA_DIR / "exports"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
SAMPLE_DATA_DIR.mkdir(exist_ok=True)
EXPORTS_DIR.mkdir(exist_ok=True)

# Logging configuration
import logging

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

def validate_config() -> bool:
    """Validate essential configuration"""
    if not OPENAI_API_KEY and not ANTHROPIC_API_KEY:
        logger.warning("No LLM API keys configured. AI features will not work.")
        return False
    
    if PRIMARY_LLM_PROVIDER == "openai" and not OPENAI_API_KEY:
        logger.error("OpenAI API key required when PRIMARY_LLM_PROVIDER is 'openai'")
        return False
    
    if PRIMARY_LLM_PROVIDER == "anthropic" and not ANTHROPIC_API_KEY:
        logger.error("Anthropic API key required when PRIMARY_LLM_PROVIDER is 'anthropic'")
        return False
    
    return True
