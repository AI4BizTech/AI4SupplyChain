# inventory_assistant/models/lap.py
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from enum import Enum

class LaptopBrand(str, Enum):
    DELL = "Dell"
    HP = "HP"
    LENOVO = "Lenovo"
    APPLE = "Apple"
    ASUS = "Asus"
    ACER = "Acer"

class LaptopCategory(str, Enum):
    PREMIUM = "premium"
    MIDRANGE = "midrange"
    BUDGET = "budget"

class Warehouse(str, Enum):
    A = "A"
    B = "B"
    C = "C"

class Laptop(SQLModel, table=True):
    model_id: str = Field(primary_key=True)
    brand: LaptopBrand
    model_name: str
    category: LaptopCategory
    unit_price: float
    min_stock: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    warehouse_stocks: list["WarehouseStock"] = Relationship(back_populates="laptop")
    transactions: list["Transaction"] = Relationship(back_populates="laptop")

class WarehouseStock(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    model_id: str = Field(foreign_key="laptop.model_id")
    warehouse_id: Warehouse
    quantity: int
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship
    laptop: Laptop = Relationship(back_populates="warehouse_stocks")

class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    transaction_id: str = Field(unique=True)
    date: datetime = Field(default_factory=datetime.utcnow)
    model_id: str = Field(foreign_key="laptop.model_id")
    quantity: int
    warehouse_id: Warehouse
    type: str = "PURCHASE"  # For future expansion: SALE, TRANSFER, etc.
    
    # Relationship
    laptop: Laptop = Relationship(back_populates="transactions")