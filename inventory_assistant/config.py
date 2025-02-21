# inventory_assistant/config.py
from pathlib import Path
from typing import Dict, Tuple
import logging

# Database Path Configuration
file_path = Path(__file__).resolve()
project_root = file_path.parent.parent
data_path = project_root / "data"

if not data_path.exists():
    data_path.mkdir(parents=True)

DB_PATH = data_path / "inventory.db"

# Logging Configuration
LOG_LEVEL = logging.WARNING  # Main application logging level
SQLALCHEMY_LOG_LEVEL = logging.WARNING  # SQL logging level
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_FILE = data_path / "simulation.log"

# Disable SQL logging noise
logging.getLogger('sqlalchemy.engine').setLevel(SQLALCHEMY_LOG_LEVEL)

# Simulation Configuration
INITIAL_STOCK_RANGES: Dict[str, Tuple[int, int]] = {
    "premium": (20, 50),
    "midrange": (50, 100),
    "budget": (100, 200)
}

PRICE_RANGES: Dict[str, Tuple[float, float]] = {
    "premium": (1500.0, 3000.0),
    "midrange": (800.0, 1499.99),
    "budget": (300.0, 799.99)
}

MIN_STOCK_LEVELS: Dict[str, int] = {
    "premium": 10,
    "midrange": 20,
    "budget": 30
}

# Daily transaction simulation parameters
DAILY_TRANSACTION_RANGES: Dict[str, Tuple[int, int]] = {
    "premium": (1, 5),    # Premium laptops sell less but higher value
    "midrange": (5, 15),  # Medium volume
    "budget": (10, 30)    # Higher volume for budget laptops
}

# Probability of transaction per category per day
TRANSACTION_PROBABILITY: Dict[str, float] = {
    "premium": 0.3,   # 30% chance of transaction
    "midrange": 0.5,  # 50% chance of transaction
    "budget": 0.7     # 70% chance of transaction
}

# Sample laptop models per category
LAPTOP_MODELS: Dict[str, list[Dict[str, str]]] = {
    "premium": [
        {"brand": "APPLE", "model": "MacBook Pro 16"},
        {"brand": "DELL", "model": "XPS 15"},
        {"brand": "LENOVO", "model": "ThinkPad X1 Carbon"}
    ],
    "midrange": [
        {"brand": "DELL", "model": "Latitude 5420"},
        {"brand": "HP", "model": "EliteBook 840"},
        {"brand": "LENOVO", "model": "ThinkPad T14"}
    ],
    "budget": [
        {"brand": "ACER", "model": "Aspire 5"},
        {"brand": "ASUS", "model": "VivoBook 15"},
        {"brand": "LENOVO", "model": "IdeaPad 3"}
    ]
}