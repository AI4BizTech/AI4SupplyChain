"""
Data simulation service for testing and development
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

from src.data.database import get_database
from src.data.inventory import Product, Supplier, Location, Inventory, Transaction

logger = logging.getLogger(__name__)

class SimulationService:
    """Service for generating sample data and simulating inventory operations"""
    
    def __init__(self, db=None):
        self.db = db or get_database()
        
        # Sample data templates
        self.sample_categories = [
            "Electronics", "Office Supplies", "Industrial Tools", "Automotive Parts",
            "Medical Supplies", "Food & Beverages", "Clothing", "Furniture",
            "Sporting Goods", "Books & Media"
        ]
        
        self.sample_suppliers = [
            {"name": "Global Tech Supply", "lead_time": 7, "payment_terms": "Net 30"},
            {"name": "Industrial Components Inc", "lead_time": 14, "payment_terms": "Net 45"},
            {"name": "Office Pro Distributors", "lead_time": 5, "payment_terms": "Net 15"},
            {"name": "MedSupply Solutions", "lead_time": 10, "payment_terms": "COD"},
            {"name": "Auto Parts Direct", "lead_time": 3, "payment_terms": "Net 30"},
            {"name": "Food Service Partners", "lead_time": 2, "payment_terms": "Net 7"},
            {"name": "Fashion Forward Wholesale", "lead_time": 21, "payment_terms": "Net 60"},
            {"name": "Sports Equipment Co", "lead_time": 12, "payment_terms": "Net 30"}
        ]
        
        self.sample_locations = [
            {"location_id": "MAIN-WH", "name": "Main Warehouse", "warehouse_type": "main"},
            {"location_id": "STORE-01", "name": "Downtown Store", "warehouse_type": "store"},
            {"location_id": "STORE-02", "name": "Mall Location", "warehouse_type": "store"},
            {"location_id": "DIST-CTR", "name": "Distribution Center", "warehouse_type": "distribution"}
        ]
    
    def generate_suppliers(self, count: int = 8) -> List[Supplier]:
        """Generate sample suppliers"""
        suppliers = []
        
        with self.db.session() as session:
            for i, supplier_template in enumerate(self.sample_suppliers[:count]):
                supplier_id = f"SUP-{str(i+1).zfill(3)}"
                
                # Check if supplier already exists
                existing = session.query(Supplier).filter(Supplier.supplier_id == supplier_id).first()
                if existing:
                    suppliers.append(existing)
                    continue
                
                supplier = Supplier(
                    supplier_id=supplier_id,
                    name=supplier_template["name"],
                    contact_info={
                        "email": f"contact@{supplier_template['name'].lower().replace(' ', '').replace('&', 'and')}.com",
                        "phone": f"+1-555-{random.randint(1000, 9999)}",
                        "address": f"{random.randint(100, 9999)} Business St, City, ST {random.randint(10000, 99999)}",
                        "contact_person": f"Contact Person {i+1}"
                    },
                    lead_time_days=supplier_template["lead_time"],
                    payment_terms=supplier_template["payment_terms"],
                    minimum_order_qty=random.randint(1, 10),
                    performance_rating=round(random.uniform(3.5, 5.0), 2)
                )
                
                session.add(supplier)
                session.flush()
                session.refresh(supplier)
                suppliers.append(supplier)
        
        logger.info(f"Generated {len(suppliers)} suppliers")
        return suppliers
    
    def generate_locations(self, count: int = 4) -> List[Location]:
        """Generate sample locations"""
        locations = []
        
        with self.db.session() as session:
            for i, location_template in enumerate(self.sample_locations[:count]):
                # Check if location already exists
                existing = session.query(Location).filter(
                    Location.location_id == location_template["location_id"]
                ).first()
                if existing:
                    locations.append(existing)
                    continue
                
                location = Location(
                    location_id=location_template["location_id"],
                    name=location_template["name"],
                    address=f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Pine', 'Elm'])} St, City, ST {random.randint(10000, 99999)}",
                    warehouse_type=location_template["warehouse_type"],
                    is_active=1
                )
                
                session.add(location)
                session.flush()
                session.refresh(location)
                locations.append(location)
        
        logger.info(f"Generated {len(locations)} locations")
        return locations
    
    def generate_products(self, count: int = 50, suppliers: Optional[List[Supplier]] = None) -> List[Product]:
        """Generate sample products"""
        if not suppliers:
            suppliers = self.generate_suppliers()
        
        products = []
        
        with self.db.session() as session:
            for i in range(count):
                sku = f"SKU-{str(i+1).zfill(4)}"
                
                # Check if product already exists
                existing = session.query(Product).filter(Product.sku == sku).first()
                if existing:
                    products.append(existing)
                    continue
                
                category = random.choice(self.sample_categories)
                supplier = random.choice(suppliers)
                
                # Generate product name based on category
                product_names = {
                    "Electronics": ["Laptop Computer", "Smartphone", "Tablet", "Monitor", "Keyboard", "Mouse"],
                    "Office Supplies": ["Printer Paper", "Stapler", "Pens", "Notebooks", "Folders", "Binders"],
                    "Industrial Tools": ["Drill", "Wrench Set", "Safety Goggles", "Hammer", "Screwdriver Set"],
                    "Automotive Parts": ["Brake Pads", "Oil Filter", "Spark Plugs", "Air Filter", "Battery"],
                    "Medical Supplies": ["Surgical Gloves", "Bandages", "Thermometer", "Stethoscope", "Syringe"],
                    "Food & Beverages": ["Coffee Beans", "Tea Bags", "Snack Bars", "Bottled Water", "Energy Drinks"],
                    "Clothing": ["T-Shirt", "Jeans", "Jacket", "Shoes", "Hat", "Socks"],
                    "Furniture": ["Office Chair", "Desk", "Filing Cabinet", "Bookshelf", "Table"],
                    "Sporting Goods": ["Basketball", "Tennis Racket", "Running Shoes", "Yoga Mat", "Dumbbells"],
                    "Books & Media": ["Technical Manual", "Fiction Book", "DVD", "Magazine", "Software"]
                }
                
                base_name = random.choice(product_names.get(category, ["Generic Item"]))
                product_name = f"{base_name} - Model {random.randint(100, 999)}"
                
                unit_cost = round(random.uniform(5.0, 500.0), 2)
                
                product = Product(
                    sku=sku,
                    name=product_name,
                    description=f"High-quality {base_name.lower()} suitable for {category.lower()} applications",
                    category=category,
                    unit_cost=unit_cost,
                    supplier_id=supplier.id,
                    reorder_point=random.randint(5, 50),
                    reorder_quantity=random.randint(20, 200),
                    weight=round(random.uniform(0.1, 10.0), 2),
                    dimensions={
                        "length": round(random.uniform(5, 50), 1),
                        "width": round(random.uniform(5, 50), 1),
                        "height": round(random.uniform(5, 30), 1)
                    }
                )
                
                session.add(product)
                session.flush()
                session.refresh(product)
                products.append(product)
        
        logger.info(f"Generated {len(products)} products")
        return products
    
    def generate_initial_inventory(self, products: Optional[List[Product]] = None, 
                                 locations: Optional[List[Location]] = None) -> List[Inventory]:
        """Generate initial inventory levels"""
        if not products:
            products = list(self.db.session().query(Product).all())
        if not locations:
            locations = list(self.db.session().query(Location).all())
        
        inventory_records = []
        
        with self.db.session() as session:
            for product in products:
                for location in locations:
                    # Check if inventory record already exists
                    existing = session.query(Inventory).filter(
                        Inventory.product_id == product.id,
                        Inventory.location_id == location.id
                    ).first()
                    if existing:
                        inventory_records.append(existing)
                        continue
                    
                    # Generate realistic initial stock levels
                    if location.warehouse_type == "main":
                        base_stock = random.randint(50, 200)
                    elif location.warehouse_type == "distribution":
                        base_stock = random.randint(20, 100)
                    else:  # store
                        base_stock = random.randint(5, 50)
                    
                    quantity_on_hand = base_stock
                    reserved_quantity = random.randint(0, min(10, quantity_on_hand // 4))
                    
                    inventory = Inventory(
                        product_id=product.id,
                        location_id=location.id,
                        quantity_on_hand=quantity_on_hand,
                        reserved_quantity=reserved_quantity,
                        available_quantity=quantity_on_hand - reserved_quantity,
                        last_counted=datetime.utcnow() - timedelta(days=random.randint(1, 30))
                    )
                    
                    session.add(inventory)
                    session.flush()
                    session.refresh(inventory)
                    inventory_records.append(inventory)
        
        logger.info(f"Generated {len(inventory_records)} inventory records")
        return inventory_records
    
    def generate_historical_transactions(self, days: int = 90, 
                                       transactions_per_day: int = 20,
                                       products: Optional[List[Product]] = None,
                                       locations: Optional[List[Location]] = None) -> List[Transaction]:
        """Generate historical transaction data"""
        if not products:
            with self.db.session() as session:
                products = session.query(Product).all()
        if not locations:
            with self.db.session() as session:
                locations = session.query(Location).all()
        
        transactions = []
        transaction_types = ["receipt", "shipment", "adjustment"]
        
        with self.db.session() as session:
            for day in range(days):
                transaction_date = datetime.utcnow() - timedelta(days=days - day)
                
                for _ in range(random.randint(transactions_per_day // 2, transactions_per_day * 2)):
                    product = random.choice(products)
                    location = random.choice(locations)
                    transaction_type = random.choice(transaction_types)
                    
                    # Generate realistic quantities based on transaction type
                    if transaction_type == "receipt":
                        quantity = random.randint(10, 100)
                    elif transaction_type == "shipment":
                        quantity = -random.randint(1, 50)  # Negative for outbound
                    else:  # adjustment
                        quantity = random.randint(-20, 20)
                    
                    transaction_id = f"{transaction_type}_{transaction_date.strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}"
                    
                    transaction = Transaction(
                        transaction_id=transaction_id,
                        product_id=product.id,
                        location_id=location.id,
                        transaction_type=transaction_type,
                        quantity=quantity,
                        unit_cost=float(product.unit_cost) if transaction_type == "receipt" else None,
                        reference_document=f"REF-{random.randint(1000, 9999)}" if random.random() > 0.3 else None,
                        timestamp=transaction_date + timedelta(
                            hours=random.randint(8, 17),
                            minutes=random.randint(0, 59)
                        ),
                        user_id=random.choice(["user1", "user2", "system", "admin"]),
                        notes=f"Simulated {transaction_type} transaction" if random.random() > 0.7 else None,
                        processed=1
                    )
                    
                    session.add(transaction)
                    transactions.append(transaction)
        
        logger.info(f"Generated {len(transactions)} historical transactions")
        return transactions
    
    def initialize_sample_database(self, supplier_count: int = 8, product_count: int = 50,
                                 location_count: int = 4, history_days: int = 90) -> Dict[str, Any]:
        """Initialize database with complete sample data"""
        try:
            logger.info("Starting sample database initialization...")
            
            # Generate all sample data
            suppliers = self.generate_suppliers(supplier_count)
            locations = self.generate_locations(location_count)
            products = self.generate_products(product_count, suppliers)
            inventory_records = self.generate_initial_inventory(products, locations)
            transactions = self.generate_historical_transactions(
                history_days, transactions_per_day=20, products=products, locations=locations
            )
            
            return {
                "success": True,
                "summary": {
                    "suppliers": len(suppliers),
                    "locations": len(locations),
                    "products": len(products),
                    "inventory_records": len(inventory_records),
                    "transactions": len(transactions)
                },
                "message": "Sample database initialized successfully"
            }
            
        except Exception as e:
            logger.error(f"Sample database initialization failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def simulate_daily_operations(self, days: int = 7) -> Dict[str, Any]:
        """Simulate daily inventory operations"""
        try:
            with self.db.session() as session:
                products = session.query(Product).all()
                locations = session.query(Location).all()
                
                if not products or not locations:
                    return {"error": "No products or locations found. Initialize sample data first."}
                
                transactions_created = 0
                
                for day in range(days):
                    sim_date = datetime.utcnow() + timedelta(days=day)
                    
                    # Simulate various daily activities
                    daily_transactions = random.randint(10, 30)
                    
                    for _ in range(daily_transactions):
                        product = random.choice(products)
                        location = random.choice(locations)
                        
                        # Weighted transaction types (more shipments than receipts)
                        transaction_type = random.choices(
                            ["receipt", "shipment", "adjustment"],
                            weights=[2, 7, 1]
                        )[0]
                        
                        if transaction_type == "receipt":
                            quantity = random.randint(10, 100)
                        elif transaction_type == "shipment":
                            quantity = -random.randint(1, 20)
                        else:  # adjustment
                            quantity = random.randint(-10, 10)
                        
                        transaction_id = f"SIM_{transaction_type}_{sim_date.strftime('%Y%m%d')}_{uuid.uuid4().hex[:6]}"
                        
                        transaction = Transaction(
                            transaction_id=transaction_id,
                            product_id=product.id,
                            location_id=location.id,
                            transaction_type=transaction_type,
                            quantity=quantity,
                            unit_cost=float(product.unit_cost) if transaction_type == "receipt" else None,
                            reference_document=f"SIM-{random.randint(1000, 9999)}",
                            timestamp=sim_date + timedelta(
                                hours=random.randint(8, 17),
                                minutes=random.randint(0, 59)
                            ),
                            user_id="simulation",
                            notes=f"Simulated daily operation - {transaction_type}",
                            processed=1
                        )
                        
                        session.add(transaction)
                        transactions_created += 1
                        
                        # Update inventory
                        inventory = session.query(Inventory).filter(
                            Inventory.product_id == product.id,
                            Inventory.location_id == location.id
                        ).first()
                        
                        if inventory:
                            inventory.quantity_on_hand += quantity
                            inventory.available_quantity = inventory.quantity_on_hand - inventory.reserved_quantity
                            inventory.last_updated = sim_date
                
                session.commit()
                
                return {
                    "success": True,
                    "days_simulated": days,
                    "transactions_created": transactions_created,
                    "message": f"Successfully simulated {days} days of operations"
                }
                
        except Exception as e:
            logger.error(f"Daily operations simulation failed: {e}")
            return {"error": str(e)}
