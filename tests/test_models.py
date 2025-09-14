"""
Tests for data models
"""
import pytest
from datetime import datetime
from src.data.inventory import Product, Supplier, Location, Inventory, Transaction


class TestSupplier:
    """Test Supplier model"""
    
    def test_supplier_creation(self, db_session):
        """Test creating a supplier"""
        supplier = Supplier(
            supplier_id="TEST001",
            name="Test Supplier",
            contact_info={"email": "test@example.com"},
            lead_time_days=7,
            payment_terms="NET30"
        )
        db_session.add(supplier)
        db_session.commit()
        
        assert supplier.id is not None
        assert supplier.supplier_id == "TEST001"
        assert supplier.name == "Test Supplier"
        assert supplier.lead_time_days == 7
        assert supplier.performance_score == 100  # Default value
    
    def test_supplier_relationships(self, sample_supplier, sample_product):
        """Test supplier-product relationships"""
        assert len(sample_supplier.products) == 1
        assert sample_supplier.products[0] == sample_product


class TestProduct:
    """Test Product model"""
    
    def test_product_creation(self, db_session, sample_supplier):
        """Test creating a product"""
        product = Product(
            sku="TEST-SKU-001",
            name="Test Product",
            description="Test Description",
            category="Test Category",
            unit_cost=25.50,
            supplier_id=sample_supplier.id,
            reorder_point=10,
            reorder_quantity=50
        )
        db_session.add(product)
        db_session.commit()
        
        assert product.id is not None
        assert product.sku == "TEST-SKU-001"
        assert product.unit_cost == 25.50
        assert product.supplier_id == sample_supplier.id
    
    def test_product_supplier_relationship(self, sample_product, sample_supplier):
        """Test product-supplier relationship"""
        assert sample_product.supplier == sample_supplier


class TestLocation:
    """Test Location model"""
    
    def test_location_creation(self, db_session):
        """Test creating a location"""
        location = Location(
            location_id="STORE001",
            name="Test Store",
            address="123 Test St",
            location_type="store"
        )
        db_session.add(location)
        db_session.commit()
        
        assert location.id is not None
        assert location.location_id == "STORE001"
        assert location.location_type == "store"


class TestInventory:
    """Test Inventory model"""
    
    def test_inventory_creation(self, sample_inventory):
        """Test inventory creation and relationships"""
        assert sample_inventory.quantity_on_hand == 50
        assert sample_inventory.quantity_reserved == 5
        assert sample_inventory.quantity_available == 45
        assert sample_inventory.product is not None
        assert sample_inventory.location is not None
    
    def test_inventory_calculations(self, sample_inventory):
        """Test inventory quantity calculations"""
        # Test that available = on_hand - reserved
        expected_available = sample_inventory.quantity_on_hand - sample_inventory.quantity_reserved
        assert sample_inventory.quantity_available == expected_available


class TestTransaction:
    """Test Transaction model"""
    
    def test_transaction_creation(self, sample_transaction):
        """Test transaction creation"""
        assert sample_transaction.transaction_id == "TXN001"
        assert sample_transaction.transaction_type == "receipt"
        assert sample_transaction.quantity == 25
        assert sample_transaction.user_id == "test_user"
        assert sample_transaction.created_at is not None
    
    def test_transaction_relationships(self, sample_transaction, sample_product, sample_location):
        """Test transaction relationships"""
        assert sample_transaction.product == sample_product
        assert sample_transaction.location == sample_location
    
    def test_transaction_types(self, db_session, sample_product, sample_location):
        """Test different transaction types"""
        transaction_types = ["receipt", "shipment", "adjustment", "transfer"]
        
        for i, txn_type in enumerate(transaction_types):
            transaction = Transaction(
                transaction_id=f"TXN{i+100}",
                product_id=sample_product.id,
                location_id=sample_location.id,
                transaction_type=txn_type,
                quantity=10,
                user_id="test_user"
            )
            db_session.add(transaction)
        
        db_session.commit()
        
        # Verify all transactions were created
        transactions = db_session.query(Transaction).filter(
            Transaction.transaction_id.like("TXN1%")
        ).all()
        assert len(transactions) == 4
        
        # Verify transaction types
        found_types = {t.transaction_type for t in transactions}
        assert found_types == set(transaction_types)
