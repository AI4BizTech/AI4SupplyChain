"""
Inventory data models
"""

from sqlalchemy import Column, Integer, String, Decimal, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from src.data.base import Base

class Product(Base):
    """Product master data model"""
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    sku = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(100), nullable=False, index=True)
    unit_cost = Column(Decimal(10, 2), nullable=False)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'))
    reorder_point = Column(Integer, default=10)
    reorder_quantity = Column(Integer, default=50)
    weight = Column(Decimal(10, 3))  # in kg
    dimensions = Column(JSON)  # {length, width, height}
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    supplier = relationship("Supplier", back_populates="products")
    inventory_records = relationship("Inventory", back_populates="product")
    transactions = relationship("Transaction", back_populates="product")

    def __repr__(self):
        return f"<Product(sku='{self.sku}', name='{self.name}')>"

class Supplier(Base):
    """Supplier master data model"""
    __tablename__ = 'suppliers'
    
    id = Column(Integer, primary_key=True)
    supplier_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    contact_info = Column(JSON)  # {email, phone, address, contact_person}
    lead_time_days = Column(Integer, default=7)
    payment_terms = Column(String(100))  # Net 30, COD, etc.
    minimum_order_qty = Column(Integer, default=1)
    performance_rating = Column(Decimal(3, 2))  # 0.00 to 5.00
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    products = relationship("Product", back_populates="supplier")

    def __repr__(self):
        return f"<Supplier(id='{self.supplier_id}', name='{self.name}')>"

class Location(Base):
    """Location/warehouse model"""
    __tablename__ = 'locations'
    
    id = Column(Integer, primary_key=True)
    location_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    address = Column(Text)
    warehouse_type = Column(String(50))  # main, store, distribution, virtual
    is_active = Column(Integer, default=1)  # 1 = active, 0 = inactive
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    inventory_records = relationship("Inventory", back_populates="location")
    transactions = relationship("Transaction", back_populates="location")

    def __repr__(self):
        return f"<Location(id='{self.location_id}', name='{self.name}')>"

class Inventory(Base):
    """Current inventory levels by product and location"""
    __tablename__ = 'inventory'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    location_id = Column(Integer, ForeignKey('locations.id'), nullable=False)
    quantity_on_hand = Column(Integer, default=0)
    reserved_quantity = Column(Integer, default=0)  # allocated but not shipped
    available_quantity = Column(Integer, default=0)  # on_hand - reserved
    last_counted = Column(DateTime)  # last physical count
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    product = relationship("Product", back_populates="inventory_records")
    location = relationship("Location", back_populates="inventory_records")

    def __repr__(self):
        return f"<Inventory(product_id={self.product_id}, location_id={self.location_id}, qty={self.quantity_on_hand})>"

class Transaction(Base):
    """All inventory movement transactions"""
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    transaction_id = Column(String(50), unique=True, nullable=False, index=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    location_id = Column(Integer, ForeignKey('locations.id'), nullable=False)
    transaction_type = Column(String(20), nullable=False, index=True)  # receipt, shipment, adjustment, transfer, expected_receipt
    quantity = Column(Integer, nullable=False)  # positive for inbound, negative for outbound
    unit_cost = Column(Decimal(10, 2))  # cost per unit for this transaction
    reference_document = Column(String(200))  # PO number, invoice, DO number, etc.
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    user_id = Column(String(100))
    notes = Column(Text)
    processed = Column(Integer, default=1)  # 1 = processed, 0 = pending
    
    # Relationships
    product = relationship("Product", back_populates="transactions")
    location = relationship("Location", back_populates="transactions")

    def __repr__(self):
        return f"<Transaction(id='{self.transaction_id}', type='{self.transaction_type}', qty={self.quantity})>"
