"""
Supplier data models and relationships
"""

from sqlalchemy import Column, Integer, String, Decimal, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from src.data.base import Base

class SupplierPerformance(Base):
    """Track supplier performance metrics over time"""
    __tablename__ = 'supplier_performance'
    
    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=False)
    evaluation_period_start = Column(DateTime, nullable=False)
    evaluation_period_end = Column(DateTime, nullable=False)
    on_time_delivery_rate = Column(Decimal(5, 4))  # 0.0000 to 1.0000
    quality_rating = Column(Decimal(3, 2))  # 0.00 to 5.00
    cost_competitiveness = Column(Decimal(3, 2))  # 0.00 to 5.00
    communication_rating = Column(Decimal(3, 2))  # 0.00 to 5.00
    overall_score = Column(Decimal(3, 2))  # 0.00 to 5.00
    total_orders = Column(Integer, default=0)
    total_value = Column(Decimal(15, 2))  # Total order value in period
    late_deliveries = Column(Integer, default=0)
    defect_rate = Column(Decimal(5, 4))  # 0.0000 to 1.0000
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    supplier = relationship("Supplier", back_populates="performance_records")

class SupplierContact(Base):
    """Multiple contacts per supplier"""
    __tablename__ = 'supplier_contacts'
    
    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=False)
    contact_type = Column(String(50), nullable=False)  # primary, sales, support, billing
    name = Column(String(200), nullable=False)
    email = Column(String(200))
    phone = Column(String(50))
    title = Column(String(100))
    department = Column(String(100))
    is_primary = Column(Integer, default=0)  # 1 for primary contact
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    supplier = relationship("Supplier", back_populates="contacts")

class SupplierPricing(Base):
    """Track supplier pricing history and agreements"""
    __tablename__ = 'supplier_pricing'
    
    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    price_per_unit = Column(Decimal(10, 4), nullable=False)
    currency = Column(String(3), default='USD')
    minimum_order_quantity = Column(Integer, default=1)
    volume_discounts = Column(JSON)  # [{qty_threshold, discount_rate}]
    effective_date = Column(DateTime, nullable=False)
    expiry_date = Column(DateTime)
    is_active = Column(Integer, default=1)
    contract_reference = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    supplier = relationship("Supplier", back_populates="pricing_records")
    product = relationship("Product")

# Add these relationships to the main Supplier model
# This extends the existing Supplier model from inventory.py
def extend_supplier_model():
    """
    This would extend the Supplier model with additional relationships
    In practice, you'd add these to the main Supplier class in inventory.py
    """
    # Supplier.performance_records = relationship("SupplierPerformance", back_populates="supplier")
    # Supplier.contacts = relationship("SupplierContact", back_populates="supplier")
    # Supplier.pricing_records = relationship("SupplierPricing", back_populates="supplier")
    pass
