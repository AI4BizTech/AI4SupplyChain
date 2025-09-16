"""
Basic tests for AI4SupplyChain
"""

import pytest
from src.config import validate_config
from src.data.database import Database

def test_config_validation():
    """Test configuration validation"""
    # This should not raise an exception
    result = validate_config()
    assert isinstance(result, bool)

def test_database_creation():
    """Test database creation"""
    db = Database("sqlite:///:memory:")  # In-memory database for testing
    assert db is not None
    
    # Test table creation
    db.create_tables()
    
    # Test session creation
    with db.session() as session:
        assert session is not None

def test_imports():
    """Test that all main modules can be imported"""
    from src.services.inventory import InventoryService
    from src.services.suppliers import SupplierService
    from src.services.forecasting import ForecastingService
    from src.services.optimization import OptimizationService
    from src.services.simulation import SimulationService
    
    # Should not raise import errors
    assert InventoryService is not None
    assert SupplierService is not None
    assert ForecastingService is not None
    assert OptimizationService is not None
    assert SimulationService is not None
