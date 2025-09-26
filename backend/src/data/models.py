"""
SQLModel database models for inventory management system.
"""
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship


class TransactionType(str, Enum):
    """Types of inventory transactions."""
    IN = "IN"                    # Stock received/added
    OUT = "OUT"                  # Stock shipped/removed
    TRANSFER = "TRANSFER"        # Stock moved between locations
    ADJUSTMENT = "ADJUSTMENT"    # Manual inventory adjustment


# Database Models (table=True)

class Supplier(SQLModel, table=True):
    """Supplier/vendor master data."""
    __tablename__ = "suppliers"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=200, index=True, description="Supplier company name")
    contact_person: Optional[str] = Field(max_length=200, description="Primary contact name")
    email: Optional[str] = Field(max_length=200, description="Contact email")
    phone: Optional[str] = Field(max_length=50, description="Contact phone number")
    address: Optional[str] = Field(description="Supplier address")
    
    # Business terms
    lead_time_days: int = Field(default=7, ge=0, description="Average lead time in days")
    payment_terms: Optional[str] = Field(max_length=100, description="Payment terms (e.g., Net 30)")
    minimum_order_qty: int = Field(default=1, ge=1, description="Minimum order quantity")
    
    # Status and tracking
    is_active: bool = Field(default=True, description="Is supplier active")
    performance_rating: Optional[float] = Field(default=None, ge=0, le=5, description="Performance rating 0-5")
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    products: List["Product"] = Relationship(back_populates="supplier")


class Location(SQLModel, table=True):
    """Storage locations/warehouses."""
    __tablename__ = "locations"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=200, index=True, description="Location name")
    code: Optional[str] = Field(max_length=20, unique=True, description="Location code/abbreviation")
    address: Optional[str] = Field(description="Physical address")
    warehouse_type: Optional[str] = Field(max_length=100, description="Type of warehouse")
    
    # Status
    is_active: bool = Field(default=True, description="Is location active")
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    inventory_records: List["Inventory"] = Relationship(back_populates="location")
    transactions: List["Transaction"] = Relationship(back_populates="location")


class Product(SQLModel, table=True):
    """Product master data."""
    __tablename__ = "products"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    sku: str = Field(max_length=100, unique=True, index=True, description="Stock Keeping Unit")
    name: str = Field(max_length=200, index=True, description="Product name")
    description: Optional[str] = Field(description="Product description")
    category: Optional[str] = Field(max_length=100, index=True, description="Product category")
    
    # Pricing
    unit_cost: Decimal = Field(decimal_places=2, ge=0, description="Cost per unit")
    unit_price: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0, description="Selling price per unit")
    
    # Physical attributes
    weight: Optional[Decimal] = Field(default=None, decimal_places=3, ge=0, description="Weight per unit")
    dimensions: Optional[str] = Field(max_length=100, description="Dimensions (LxWxH)")
    
    # Inventory management
    reorder_point: int = Field(default=10, ge=0, description="Reorder point quantity")
    reorder_quantity: int = Field(default=50, ge=1, description="Reorder quantity")
    
    # Supplier relationship
    supplier_id: Optional[int] = Field(default=None, foreign_key="suppliers.id")
    supplier: Optional[Supplier] = Relationship(back_populates="products")
    
    # Status
    is_active: bool = Field(default=True, description="Is product active")
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    inventory_records: List["Inventory"] = Relationship(back_populates="product")
    transactions: List["Transaction"] = Relationship(back_populates="product")


class Inventory(SQLModel, table=True):
    """Current inventory levels by product and location."""
    __tablename__ = "inventory"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Composite key components
    product_id: int = Field(foreign_key="products.id", index=True)
    location_id: int = Field(foreign_key="locations.id", index=True)
    
    # Quantities
    quantity_on_hand: int = Field(ge=0, description="Available quantity")
    reserved_quantity: int = Field(default=0, ge=0, description="Reserved/allocated quantity")
    
    # Tracking
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    product: Product = Relationship(back_populates="inventory_records")
    location: Location = Relationship(back_populates="inventory_records")
    
    # Ensure unique product-location combination
    __table_args__ = {"sqlite_autoincrement": True}


class Transaction(SQLModel, table=True):
    """Inventory transaction history."""
    __tablename__ = "transactions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Transaction details
    product_id: int = Field(foreign_key="products.id", index=True)
    location_id: int = Field(foreign_key="locations.id", index=True)
    transaction_type: TransactionType = Field(index=True, description="Type of transaction")
    quantity: int = Field(description="Quantity moved (positive for IN, negative for OUT)")
    
    # References and documentation
    reference_number: Optional[str] = Field(max_length=100, description="PO, DO, or other reference")
    notes: Optional[str] = Field(description="Transaction notes")
    
    # Audit trail
    user_id: Optional[str] = Field(max_length=100, description="User who performed transaction")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    
    # Relationships
    product: Product = Relationship(back_populates="transactions")
    location: Location = Relationship(back_populates="transactions")


# API Response Models (not tables)

class ProductRead(SQLModel):
    """Product data for API responses."""
    id: int
    sku: str
    name: str
    description: Optional[str]
    category: Optional[str]
    unit_cost: Decimal
    unit_price: Optional[Decimal]
    weight: Optional[Decimal]
    dimensions: Optional[str]
    reorder_point: int
    reorder_quantity: int
    supplier_id: Optional[int]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProductCreate(SQLModel):
    """Product data for creation."""
    sku: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    unit_cost: Decimal
    unit_price: Optional[Decimal] = None
    weight: Optional[Decimal] = None
    dimensions: Optional[str] = None
    reorder_point: int = 10
    reorder_quantity: int = 50
    supplier_id: Optional[int] = None


class ProductUpdate(SQLModel):
    """Product data for updates."""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    unit_cost: Optional[Decimal] = None
    unit_price: Optional[Decimal] = None
    weight: Optional[Decimal] = None
    dimensions: Optional[str] = None
    reorder_point: Optional[int] = None
    reorder_quantity: Optional[int] = None
    supplier_id: Optional[int] = None
    is_active: Optional[bool] = None


class SupplierRead(SQLModel):
    """Supplier data for API responses."""
    id: int
    name: str
    contact_person: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    lead_time_days: int
    payment_terms: Optional[str]
    minimum_order_qty: int
    is_active: bool
    performance_rating: Optional[float]
    created_at: datetime
    updated_at: datetime


class SupplierCreate(SQLModel):
    """Supplier data for creation."""
    name: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    lead_time_days: int = 7
    payment_terms: Optional[str] = None
    minimum_order_qty: int = 1
    performance_rating: Optional[float] = None


class SupplierUpdate(SQLModel):
    """Supplier data for updates."""
    name: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    lead_time_days: Optional[int] = None
    payment_terms: Optional[str] = None
    minimum_order_qty: Optional[int] = None
    is_active: Optional[bool] = None
    performance_rating: Optional[float] = None


class LocationRead(SQLModel):
    """Location data for API responses."""
    id: int
    name: str
    code: Optional[str]
    address: Optional[str]
    warehouse_type: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class LocationCreate(SQLModel):
    """Location data for creation."""
    name: str
    code: Optional[str] = None
    address: Optional[str] = None
    warehouse_type: Optional[str] = None


class LocationUpdate(SQLModel):
    """Location data for updates."""
    name: Optional[str] = None
    code: Optional[str] = None
    address: Optional[str] = None
    warehouse_type: Optional[str] = None
    is_active: Optional[bool] = None


class InventoryRead(SQLModel):
    """Inventory data for API responses."""
    id: int
    product_id: int
    location_id: int
    quantity_on_hand: int
    reserved_quantity: int
    available_quantity: int  # Calculated field
    last_updated: datetime


class InventoryUpdate(SQLModel):
    """Inventory data for updates."""
    quantity_on_hand: Optional[int] = None
    reserved_quantity: Optional[int] = None


class TransactionRead(SQLModel):
    """Transaction data for API responses."""
    id: int
    product_id: int
    location_id: int
    transaction_type: TransactionType
    quantity: int
    reference_number: Optional[str]
    notes: Optional[str]
    user_id: Optional[str]
    created_at: datetime


class TransactionCreate(SQLModel):
    """Transaction data for creation."""
    product_id: int
    location_id: int
    transaction_type: TransactionType
    quantity: int
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    user_id: Optional[str] = None


# Detailed response models with relationships
class ProductWithSupplier(ProductRead):
    """Product with supplier details."""
    supplier: Optional[SupplierRead] = None


class InventoryWithDetails(InventoryRead):
    """Inventory with product and location details."""
    product: ProductRead
    location: LocationRead


class TransactionWithDetails(TransactionRead):
    """Transaction with product and location details."""
    product: ProductRead
    location: LocationRead