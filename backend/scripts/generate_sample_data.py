#!/usr/bin/env python3
"""
Generate sample data for AI4SupplyChain inventory system.
"""
import sys
import os
from pathlib import Path

# Add the backend src directory to the path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir / "src"))

from decimal import Decimal
import random
from datetime import datetime, timedelta, timezone
from sqlmodel import Session

from src.data.database import get_session_sync, init_database
from src.data.models import (
    Supplier, Location, Product, Inventory, Transaction, TransactionType
)
from src.services.inventory_service import InventoryService
from src.services.transaction_service import TransactionService
from src.services.supplier_service import SupplierService
from src.services.location_service import LocationService

# Sample data configurations
SUPPLIERS_DATA = [
    {
        "name": "TechGear Suppliers Inc.",
        "contact_person": "John Smith",
        "email": "john@techgear.com",
        "phone": "+1-555-0101",
        "address": "123 Industrial Ave, Tech City, TC 12345",
        "lead_time_days": 5,
        "payment_terms": "Net 30",
        "minimum_order_qty": 10
    },
    {
        "name": "Global Electronics Ltd",
        "contact_person": "Sarah Johnson",
        "email": "sarah@globalelec.com",
        "phone": "+1-555-0102",
        "address": "456 Commerce St, Electronics Park, EP 67890",
        "lead_time_days": 7,
        "payment_terms": "Net 15",
        "minimum_order_qty": 25
    },
    {
        "name": "Precision Components Co",
        "contact_person": "Mike Chen",
        "email": "mike@precision.com",
        "phone": "+1-555-0103",
        "address": "789 Manufacturing Blvd, Component City, CC 11111",
        "lead_time_days": 10,
        "payment_terms": "Net 45",
        "minimum_order_qty": 5
    },
    {
        "name": "Office Solutions Hub",
        "contact_person": "Lisa Brown",
        "email": "lisa@officesol.com",
        "phone": "+1-555-0104",
        "address": "321 Business Park Dr, Office Town, OT 22222",
        "lead_time_days": 3,
        "payment_terms": "Net 30",
        "minimum_order_qty": 50
    }
]

LOCATIONS_DATA = [
    {
        "name": "Main Warehouse",
        "code": "MAIN",
        "address": "100 Storage Way, Warehouse District, WD 33333",
        "warehouse_type": "Distribution Center"
    },
    {
        "name": "Retail Store North",
        "code": "RTL-N",
        "address": "200 Shopping Plaza, North Mall, NM 44444",
        "warehouse_type": "Retail"
    },
    {
        "name": "Retail Store South",
        "code": "RTL-S",
        "address": "300 Market Street, South Center, SC 55555",
        "warehouse_type": "Retail"
    },
    {
        "name": "Overflow Storage",
        "code": "OVFL",
        "address": "400 Overflow Lane, Storage Park, SP 66666",
        "warehouse_type": "Storage"
    }
]

PRODUCTS_DATA = [
    # Electronics Category
    {
        "sku": "LAPTOP-001",
        "name": "Business Laptop Model X1",
        "description": "High-performance business laptop with 16GB RAM",
        "category": "Electronics",
        "unit_cost": Decimal("800.00"),
        "unit_price": Decimal("1200.00"),
        "weight": Decimal("2.5"),
        "dimensions": "35x25x2 cm",
        "reorder_point": 5,
        "reorder_quantity": 20
    },
    {
        "sku": "MOUSE-001",
        "name": "Wireless Optical Mouse",
        "description": "Ergonomic wireless mouse with precision tracking",
        "category": "Electronics",
        "unit_cost": Decimal("25.00"),
        "unit_price": Decimal("45.00"),
        "weight": Decimal("0.15"),
        "dimensions": "12x7x4 cm",
        "reorder_point": 50,
        "reorder_quantity": 100
    },
    {
        "sku": "KEYB-001",
        "name": "Mechanical Keyboard",
        "description": "RGB mechanical keyboard with tactile switches",
        "category": "Electronics",
        "unit_cost": Decimal("75.00"),
        "unit_price": Decimal("120.00"),
        "weight": Decimal("1.2"),
        "dimensions": "45x15x4 cm",
        "reorder_point": 20,
        "reorder_quantity": 50
    },
    # Office Supplies Category
    {
        "sku": "PEN-001",
        "name": "Blue Ink Pens (Pack of 12)",
        "description": "Professional blue ballpoint pens, smooth writing",
        "category": "Office Supplies",
        "unit_cost": Decimal("5.00"),
        "unit_price": Decimal("12.00"),
        "weight": Decimal("0.2"),
        "dimensions": "15x10x2 cm",
        "reorder_point": 100,
        "reorder_quantity": 500
    },
    {
        "sku": "PAPER-001",
        "name": "A4 Copy Paper (Ream)",
        "description": "High-quality A4 copy paper, 80gsm, 500 sheets",
        "category": "Office Supplies",
        "unit_cost": Decimal("8.00"),
        "unit_price": Decimal("15.00"),
        "weight": Decimal("2.5"),
        "dimensions": "30x21x5 cm",
        "reorder_point": 200,
        "reorder_quantity": 1000
    },
    {
        "sku": "FOLDER-001",
        "name": "Manila File Folders (Pack of 25)",
        "description": "Letter-size manila file folders with tabs",
        "category": "Office Supplies",
        "unit_cost": Decimal("12.00"),
        "unit_price": Decimal("20.00"),
        "weight": Decimal("0.8"),
        "dimensions": "32x24x3 cm",
        "reorder_point": 50,
        "reorder_quantity": 200
    },
    # Components Category
    {
        "sku": "SCREW-001",
        "name": "M4 Machine Screws (Pack of 100)",
        "description": "Stainless steel M4x12mm machine screws",
        "category": "Components",
        "unit_cost": Decimal("15.00"),
        "unit_price": Decimal("25.00"),
        "weight": Decimal("0.5"),
        "dimensions": "10x10x2 cm",
        "reorder_point": 25,
        "reorder_quantity": 100
    },
    {
        "sku": "CABLE-001",
        "name": "USB-C Cable 2m",
        "description": "High-speed USB-C cable with data and charging support",
        "category": "Components",
        "unit_cost": Decimal("8.00"),
        "unit_price": Decimal("18.00"),
        "weight": Decimal("0.3"),
        "dimensions": "15x12x3 cm",
        "reorder_point": 30,
        "reorder_quantity": 150
    }
]


def create_sample_suppliers(session: Session) -> list[Supplier]:
    """Create sample suppliers."""
    print("Creating sample suppliers...")
    supplier_service = SupplierService(session)
    suppliers = []
    
    for supplier_data in SUPPLIERS_DATA:
        from src.data.models import SupplierCreate
        supplier = supplier_service.create_supplier(SupplierCreate(**supplier_data))
        suppliers.append(supplier)
        print(f"  ✓ Created supplier: {supplier.name}")
    
    return suppliers


def create_sample_locations(session: Session) -> list[Location]:
    """Create sample locations."""
    print("Creating sample locations...")
    location_service = LocationService(session)
    locations = []
    
    for location_data in LOCATIONS_DATA:
        from src.data.models import LocationCreate
        location = location_service.create_location(LocationCreate(**location_data))
        locations.append(location)
        print(f"  ✓ Created location: {location.name}")
    
    return locations


def create_sample_products(session: Session, suppliers: list[Supplier]) -> list[Product]:
    """Create sample products."""
    print("Creating sample products...")
    inventory_service = InventoryService(session)
    products = []
    
    for i, product_data in enumerate(PRODUCTS_DATA):
        from src.data.models import ProductCreate
        # Assign suppliers round-robin style
        supplier_id = suppliers[i % len(suppliers)].id
        product_data["supplier_id"] = supplier_id
        
        product = inventory_service.create_product(ProductCreate(**product_data))
        products.append(product)
        print(f"  ✓ Created product: {product.sku} - {product.name}")
    
    return products


def create_sample_inventory(session: Session, products: list[Product], locations: list[Location]) -> None:
    """Create sample inventory records with initial stock."""
    print("Creating sample inventory...")
    inventory_service = InventoryService(session)
    
    for product in products:
        for location in locations:
            # Generate random initial stock levels
            base_stock = random.randint(20, 200)
            reserved = random.randint(0, min(10, base_stock // 4))
            
            from src.data.models import InventoryUpdate
            inventory_service.update_inventory(
                product.id,
                location.id,
                InventoryUpdate(
                    quantity_on_hand=base_stock,
                    reserved_quantity=reserved
                )
            )
            print(f"  ✓ Set inventory for {product.sku} at {location.name}: {base_stock} on hand, {reserved} reserved")


def create_sample_transactions(session: Session, products: list[Product], locations: list[Location]) -> None:
    """Create sample transaction history."""
    print("Creating sample transactions...")
    transaction_service = TransactionService(session)
    
    # Generate transactions over the last 30 days
    start_date = datetime.now(timezone.utc) - timedelta(days=30)
    
    transaction_types = [
        TransactionType.IN,
        TransactionType.OUT,
        TransactionType.TRANSFER,
        TransactionType.ADJUSTMENT
    ]
    
    reference_prefixes = {
        TransactionType.IN: "PO",
        TransactionType.OUT: "DO",
        TransactionType.TRANSFER: "TXF",
        TransactionType.ADJUSTMENT: "ADJ"
    }
    
    for day in range(30):
        transaction_date = start_date + timedelta(days=day)
        
        # Generate 3-8 transactions per day
        num_transactions = random.randint(3, 8)
        
        for _ in range(num_transactions):
            product = random.choice(products)
            location = random.choice(locations)
            trans_type = random.choice(transaction_types)
            
            # Generate appropriate quantity based on transaction type
            if trans_type == TransactionType.IN:
                quantity = random.randint(10, 100)
            elif trans_type == TransactionType.OUT:
                quantity = -random.randint(5, 50)
            elif trans_type == TransactionType.TRANSFER:
                quantity = random.randint(5, 30)
                if random.choice([True, False]):
                    quantity = -quantity  # OUT side of transfer
            else:  # ADJUSTMENT
                quantity = random.randint(-20, 20)
            
            # Generate reference number
            ref_num = f"{reference_prefixes[trans_type]}-{random.randint(1000, 9999)}"
            
            try:
                from src.data.models import TransactionCreate
                transaction_data = TransactionCreate(
                    product_id=product.id,
                    location_id=location.id,
                    transaction_type=trans_type,
                    quantity=quantity,
                    reference_number=ref_num,
                    notes=f"Sample {trans_type.value.lower()} transaction",
                    user_id="system"
                )
                
                transaction = transaction_service.create_transaction(transaction_data)
                # Set the created timestamp to our desired date
                transaction.created_at = transaction_date
                session.add(transaction)
                session.commit()
                
                print(f"  ✓ Created {trans_type.value} transaction: {product.sku} @ {location.name}, qty: {quantity}")
                
            except Exception as e:
                # Skip transactions that would cause issues (e.g., insufficient stock)
                print(f"  ! Skipped transaction due to: {str(e)[:50]}...")
                continue


def update_supplier_performance(session: Session, suppliers: list[Supplier]) -> None:
    """Update supplier performance ratings."""
    print("Updating supplier performance ratings...")
    supplier_service = SupplierService(session)
    
    for supplier in suppliers:
        supplier_service.update_supplier_performance_rating(supplier.id)
        updated_supplier = supplier_service.get_supplier(supplier.id)
        print(f"  ✓ Updated {supplier.name}: rating = {updated_supplier.performance_rating}")


def main():
    """Generate all sample data."""
    print("🚀 AI4SupplyChain Sample Data Generator")
    print("=" * 50)
    
    # Initialize database
    print("Initializing database...")
    init_database()
    print("  ✓ Database initialized")
    
    with get_session_sync() as session:
        try:
            # Create sample data in order
            suppliers = create_sample_suppliers(session)
            locations = create_sample_locations(session)
            products = create_sample_products(session, suppliers)
            create_sample_inventory(session, products, locations)
            create_sample_transactions(session, products, locations)
            update_supplier_performance(session, suppliers)
            
            print("\n" + "=" * 50)
            print("✅ Sample data generation completed successfully!")
            print(f"   • {len(suppliers)} suppliers")
            print(f"   • {len(locations)} locations")
            print(f"   • {len(products)} products")
            print(f"   • Inventory records for all product-location combinations")
            print(f"   • ~30 days of transaction history")
            print("\n🎯 Your AI4SupplyChain system is ready for testing!")
            
        except Exception as e:
            print(f"\n❌ Error generating sample data: {e}")
            raise


if __name__ == "__main__":
    main()