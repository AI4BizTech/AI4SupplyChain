"""
Test configuration and fixtures for AI4SupplyChain
"""
import pytest
import tempfile
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.data.base import Base
from src.data.database import Database
from src.data.inventory import Product, Supplier, Location, Inventory, Transaction


@pytest.fixture(scope="session")
def test_database():
    """Create a temporary test database."""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    
    # Create test database URL
    test_db_url = f"sqlite:///{db_path}"
    
    # Create engine and session
    engine = create_engine(test_db_url, echo=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield SessionLocal
    
    # Cleanup
    os.unlink(db_path)


@pytest.fixture
def db_session(test_database):
    """Create a database session for testing."""
    session = test_database()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def sample_supplier(db_session):
    """Create a sample supplier for testing."""
    supplier = Supplier(
        supplier_id="SUPP001",
        name="Test Supplier Inc",
        contact_info={"email": "test@supplier.com", "phone": "123-456-7890"},
        lead_time_days=5,
        payment_terms="NET30",
        minimum_order_qty=10
    )
    db_session.add(supplier)
    db_session.commit()
    return supplier


@pytest.fixture
def sample_location(db_session):
    """Create a sample location for testing."""
    location = Location(
        location_id="LOC001",
        name="Main Warehouse",
        address="123 Storage St, City, State",
        location_type="warehouse"
    )
    db_session.add(location)
    db_session.commit()
    return location


@pytest.fixture
def sample_product(db_session, sample_supplier):
    """Create a sample product for testing."""
    product = Product(
        sku="TEST-001",
        name="Test Product",
        description="A test product for unit testing",
        category="Electronics",
        unit_cost=50.00,
        supplier_id=sample_supplier.id,
        reorder_point=20,
        reorder_quantity=100
    )
    db_session.add(product)
    db_session.commit()
    return product


@pytest.fixture
def sample_inventory(db_session, sample_product, sample_location):
    """Create sample inventory for testing."""
    inventory = Inventory(
        product_id=sample_product.id,
        location_id=sample_location.id,
        quantity_on_hand=50,
        quantity_reserved=5,
        quantity_available=45
    )
    db_session.add(inventory)
    db_session.commit()
    return inventory


@pytest.fixture
def sample_transaction(db_session, sample_product, sample_location):
    """Create a sample transaction for testing."""
    transaction = Transaction(
        transaction_id="TXN001",
        product_id=sample_product.id,
        location_id=sample_location.id,
        transaction_type="receipt",
        quantity=25,
        reference_document="PO-12345",
        user_id="test_user",
        notes="Test transaction"
    )
    db_session.add(transaction)
    db_session.commit()
    return transaction
