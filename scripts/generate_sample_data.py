#!/usr/bin/env python3
"""
Generate sample data for AI4SupplyChain development and testing
"""
import csv
import random
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any


class SampleDataGenerator:
    """Generate realistic sample data for the supply chain system"""
    
    def __init__(self):
        self.suppliers = []
        self.locations = []
        self.products = []
        self.transactions = []
        
        # Sample data templates
        self.supplier_names = [
            "TechSupply Corp", "Global Electronics Ltd", "Industrial Parts Inc",
            "Quality Components Co", "Reliable Suppliers LLC", "Prime Manufacturing",
            "Advanced Materials Group", "Precision Tools Ltd", "Smart Solutions Inc",
            "Innovation Supply Chain"
        ]
        
        self.product_categories = [
            "Electronics", "Tools", "Office Supplies", "Industrial Equipment",
            "Safety Equipment", "Maintenance Supplies", "IT Hardware", "Furniture"
        ]
        
        self.location_types = ["warehouse", "store", "distribution_center", "factory"]
        
        self.cities = [
            "New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
            "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose"
        ]
    
    def generate_suppliers(self, count: int = 10) -> List[Dict[str, Any]]:
        """Generate sample supplier data"""
        suppliers = []
        
        for i in range(count):
            supplier = {
                "supplier_id": f"SUPP{i+1:03d}",
                "name": random.choice(self.supplier_names),
                "contact_info": {
                    "email": f"contact@supplier{i+1}.com",
                    "phone": f"({random.randint(200,999)}) {random.randint(200,999)}-{random.randint(1000,9999)}",
                    "address": f"{random.randint(100,9999)} Business Ave, {random.choice(self.cities)}, State {random.randint(10000,99999)}"
                },
                "lead_time_days": random.randint(3, 21),
                "payment_terms": random.choice(["NET15", "NET30", "NET45", "COD", "2/10 NET30"]),
                "minimum_order_qty": random.randint(1, 100),
                "performance_score": random.randint(75, 100),
                "created_at": datetime.now().isoformat()
            }
            suppliers.append(supplier)
        
        self.suppliers = suppliers
        return suppliers
    
    def generate_locations(self, count: int = 8) -> List[Dict[str, Any]]:
        """Generate sample location data"""
        locations = []
        
        for i in range(count):
            location = {
                "location_id": f"LOC{i+1:03d}",
                "name": f"{random.choice(['Main', 'North', 'South', 'East', 'West', 'Central'])} {random.choice(['Warehouse', 'Store', 'Distribution Center', 'Facility'])}",
                "address": f"{random.randint(100,9999)} {random.choice(['Industrial', 'Commerce', 'Business', 'Main'])} St, {random.choice(self.cities)}, State {random.randint(10000,99999)}",
                "location_type": random.choice(self.location_types),
                "capacity": random.randint(1000, 50000),
                "created_at": datetime.now().isoformat()
            }
            locations.append(location)
        
        self.locations = locations
        return locations
    
    def generate_products(self, count: int = 50) -> List[Dict[str, Any]]:
        """Generate sample product data"""
        products = []
        
        product_prefixes = ["PRO", "SKU", "ITEM", "PART"]
        
        for i in range(count):
            supplier_id = random.randint(1, len(self.suppliers)) if self.suppliers else 1
            category = random.choice(self.product_categories)
            
            product = {
                "sku": f"{random.choice(product_prefixes)}-{i+1:04d}",
                "name": f"{category} Item {i+1}",
                "description": f"High-quality {category.lower()} product for professional use. Model {i+1} with advanced features.",
                "category": category,
                "unit_cost": round(random.uniform(5.0, 500.0), 2),
                "supplier_id": supplier_id,
                "reorder_point": random.randint(10, 100),
                "reorder_quantity": random.randint(50, 500),
                "weight": round(random.uniform(0.1, 50.0), 2),
                "dimensions": {
                    "length": round(random.uniform(1, 100), 1),
                    "width": round(random.uniform(1, 50), 1),
                    "height": round(random.uniform(1, 30), 1)
                },
                "created_at": datetime.now().isoformat()
            }
            products.append(product)
        
        self.products = products
        return products
    
    def generate_transactions(self, count: int = 200) -> List[Dict[str, Any]]:
        """Generate sample transaction data"""
        transactions = []
        transaction_types = ["receipt", "shipment", "adjustment", "transfer"]
        
        for i in range(count):
            product_id = random.randint(1, len(self.products)) if self.products else 1
            location_id = random.randint(1, len(self.locations)) if self.locations else 1
            transaction_type = random.choice(transaction_types)
            
            # Generate transaction date within last 90 days
            days_ago = random.randint(0, 90)
            transaction_date = datetime.now() - timedelta(days=days_ago)
            
            # Adjust quantity based on transaction type
            if transaction_type == "receipt":
                quantity = random.randint(10, 200)
            elif transaction_type == "shipment":
                quantity = -random.randint(1, 100)  # Negative for shipments
            elif transaction_type == "adjustment":
                quantity = random.randint(-50, 50)
            else:  # transfer
                quantity = random.randint(5, 100)
            
            transaction = {
                "transaction_id": f"TXN{i+1:06d}",
                "product_id": product_id,
                "location_id": location_id,
                "transaction_type": transaction_type,
                "quantity": quantity,
                "reference_document": f"{transaction_type.upper()}-{random.randint(10000,99999)}",
                "user_id": random.choice(["admin", "warehouse_user", "manager", "operator"]),
                "notes": f"Auto-generated {transaction_type} transaction for testing",
                "created_at": transaction_date.isoformat()
            }
            transactions.append(transaction)
        
        self.transactions = transactions
        return transactions
    
    def generate_inventory_levels(self) -> List[Dict[str, Any]]:
        """Generate initial inventory levels for all product-location combinations"""
        inventory = []
        
        # Create inventory for subset of products at each location
        for location in self.locations:
            # Each location has 60-80% of products
            num_products = int(len(self.products) * random.uniform(0.6, 0.8))
            selected_products = random.sample(self.products, num_products)
            
            for product in selected_products:
                quantity_on_hand = random.randint(0, 500)
                quantity_reserved = min(quantity_on_hand, random.randint(0, 50))
                quantity_available = quantity_on_hand - quantity_reserved
                
                inventory_record = {
                    "product_id": self.products.index(product) + 1,
                    "location_id": self.locations.index(location) + 1,
                    "quantity_on_hand": quantity_on_hand,
                    "quantity_reserved": quantity_reserved,
                    "quantity_available": quantity_available,
                    "last_updated": datetime.now().isoformat()
                }
                inventory.append(inventory_record)
        
        return inventory
    
    def save_to_csv(self, data: List[Dict[str, Any]], filename: str, directory: str = "storage/sample_data"):
        """Save data to CSV file"""
        Path(directory).mkdir(parents=True, exist_ok=True)
        filepath = Path(directory) / filename
        
        if not data:
            print(f"⚠️ No data to save for {filename}")
            return
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=data[0].keys())
            writer.writeheader()
            
            for row in data:
                # Convert complex fields to JSON strings
                clean_row = {}
                for key, value in row.items():
                    if isinstance(value, (dict, list)):
                        clean_row[key] = json.dumps(value)
                    else:
                        clean_row[key] = value
                writer.writerow(clean_row)
        
        print(f"✅ Saved {len(data)} records to {filepath}")
    
    def generate_all_sample_data(self, 
                                suppliers_count: int = 10,
                                locations_count: int = 8,
                                products_count: int = 50,
                                transactions_count: int = 200):
        """Generate all sample data and save to CSV files"""
        print("🎲 Generating sample data for AI4SupplyChain...")
        
        # Generate data in dependency order
        print("📊 Generating suppliers...")
        suppliers = self.generate_suppliers(suppliers_count)
        self.save_to_csv(suppliers, "suppliers.csv")
        
        print("📍 Generating locations...")
        locations = self.generate_locations(locations_count)
        self.save_to_csv(locations, "locations.csv")
        
        print("📦 Generating products...")
        products = self.generate_products(products_count)
        self.save_to_csv(products, "products.csv")
        
        print("📋 Generating transactions...")
        transactions = self.generate_transactions(transactions_count)
        self.save_to_csv(transactions, "transactions.csv")
        
        print("📊 Generating inventory levels...")
        inventory = self.generate_inventory_levels()
        self.save_to_csv(inventory, "inventory.csv")
        
        # Generate summary
        summary = {
            "suppliers_generated": len(suppliers),
            "locations_generated": len(locations),
            "products_generated": len(products),
            "transactions_generated": len(transactions),
            "inventory_records_generated": len(inventory),
            "generated_at": datetime.now().isoformat()
        }
        
        print("\n📈 Sample Data Generation Summary:")
        for key, value in summary.items():
            if key != "generated_at":
                print(f"   {key.replace('_', ' ').title()}: {value}")
        
        return summary


def main():
    """Main function to generate sample data"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate sample data for AI4SupplyChain")
    parser.add_argument("--suppliers", type=int, default=10, help="Number of suppliers to generate")
    parser.add_argument("--locations", type=int, default=8, help="Number of locations to generate")
    parser.add_argument("--products", type=int, default=50, help="Number of products to generate")
    parser.add_argument("--transactions", type=int, default=200, help="Number of transactions to generate")
    parser.add_argument("--output-dir", default="storage/sample_data", help="Output directory for CSV files")
    
    args = parser.parse_args()
    
    generator = SampleDataGenerator()
    summary = generator.generate_all_sample_data(
        suppliers_count=args.suppliers,
        locations_count=args.locations,
        products_count=args.products,
        transactions_count=args.transactions
    )
    
    print(f"\n🎉 Sample data generation complete!")
    print(f"📁 Files saved to: {args.output_dir}")


if __name__ == "__main__":
    main()
