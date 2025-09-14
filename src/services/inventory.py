"""
Inventory management service
"""

from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
import logging
from datetime import datetime, timedelta

from src.data.database import get_database
from src.data.inventory import Product, Supplier, Location, Inventory, Transaction

logger = logging.getLogger(__name__)

class InventoryService:
    """Service for managing inventory operations"""
    
    def __init__(self, db=None):
        self.db = db or get_database()
    
    # Product operations
    def create_product(self, product_data: Dict[str, Any]) -> Product:
        """Create a new product"""
        with self.db.session() as session:
            product = Product(**product_data)
            session.add(product)
            session.flush()
            session.refresh(product)
            return product
    
    def get_product_by_sku(self, sku: str) -> Optional[Product]:
        """Get product by SKU"""
        with self.db.session() as session:
            return session.query(Product).filter(Product.sku == sku).first()
    
    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Get product by ID"""
        with self.db.session() as session:
            return session.query(Product).filter(Product.id == product_id).first()
    
    def list_products(self, category: Optional[str] = None, limit: int = 100) -> List[Product]:
        """List products with optional category filter"""
        with self.db.session() as session:
            query = session.query(Product)
            if category:
                query = query.filter(Product.category == category)
            return query.limit(limit).all()
    
    def update_product(self, product_id: int, updates: Dict[str, Any]) -> Optional[Product]:
        """Update product information"""
        with self.db.session() as session:
            product = session.query(Product).filter(Product.id == product_id).first()
            if product:
                for key, value in updates.items():
                    setattr(product, key, value)
                product.updated_at = datetime.utcnow()
                session.flush()
                session.refresh(product)
            return product
    
    # Location operations
    def create_location(self, location_data: Dict[str, Any]) -> Location:
        """Create a new location"""
        with self.db.session() as session:
            location = Location(**location_data)
            session.add(location)
            session.flush()
            session.refresh(location)
            return location
    
    def get_location_by_id(self, location_id: str) -> Optional[Location]:
        """Get location by location_id"""
        with self.db.session() as session:
            return session.query(Location).filter(Location.location_id == location_id).first()
    
    def list_locations(self) -> List[Location]:
        """List all active locations"""
        with self.db.session() as session:
            return session.query(Location).filter(Location.is_active == 1).all()
    
    # Inventory operations
    def get_stock_levels(self, sku: str, location_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get current stock levels for a product"""
        with self.db.session() as session:
            query = session.query(
                Inventory,
                Product.sku,
                Product.name,
                Location.location_id,
                Location.name.label('location_name')
            ).join(Product).join(Location).filter(Product.sku == sku)
            
            if location_id:
                query = query.filter(Location.location_id == location_id)
            
            results = []
            for inv, sku, product_name, loc_id, loc_name in query.all():
                results.append({
                    'sku': sku,
                    'product_name': product_name,
                    'location_id': loc_id,
                    'location_name': loc_name,
                    'quantity_on_hand': inv.quantity_on_hand,
                    'reserved_quantity': inv.reserved_quantity,
                    'available_quantity': inv.available_quantity,
                    'last_updated': inv.last_updated
                })
            
            return results
    
    def update_stock_level(self, product_id: int, location_id: int, 
                          quantity_change: int, transaction_type: str = "adjustment") -> bool:
        """Update stock level and create transaction record"""
        with self.db.session() as session:
            try:
                # Get or create inventory record
                inventory = session.query(Inventory).filter(
                    and_(Inventory.product_id == product_id, 
                         Inventory.location_id == location_id)
                ).first()
                
                if not inventory:
                    inventory = Inventory(
                        product_id=product_id,
                        location_id=location_id,
                        quantity_on_hand=0,
                        reserved_quantity=0,
                        available_quantity=0
                    )
                    session.add(inventory)
                
                # Update quantities
                inventory.quantity_on_hand += quantity_change
                inventory.available_quantity = inventory.quantity_on_hand - inventory.reserved_quantity
                inventory.last_updated = datetime.utcnow()
                
                # Create transaction record
                transaction = Transaction(
                    transaction_id=f"{transaction_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{product_id}",
                    product_id=product_id,
                    location_id=location_id,
                    transaction_type=transaction_type,
                    quantity=quantity_change,
                    timestamp=datetime.utcnow(),
                    user_id="system"
                )
                session.add(transaction)
                
                session.flush()
                return True
                
            except Exception as e:
                logger.error(f"Error updating stock level: {e}")
                return False
    
    def get_low_stock_items(self, location_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get items that are below reorder point"""
        with self.db.session() as session:
            query = session.query(
                Product,
                Inventory,
                Location.location_id,
                Location.name.label('location_name')
            ).join(Inventory).join(Location).filter(
                Inventory.quantity_on_hand <= Product.reorder_point
            )
            
            if location_id:
                query = query.filter(Location.location_id == location_id)
            
            results = []
            for product, inventory, loc_id, loc_name in query.all():
                results.append({
                    'sku': product.sku,
                    'product_name': product.name,
                    'category': product.category,
                    'location_id': loc_id,
                    'location_name': loc_name,
                    'current_stock': inventory.quantity_on_hand,
                    'reorder_point': product.reorder_point,
                    'reorder_quantity': product.reorder_quantity,
                    'supplier_id': product.supplier_id
                })
            
            return results
    
    def get_inventory_summary(self) -> Dict[str, Any]:
        """Get overall inventory summary statistics"""
        with self.db.session() as session:
            total_products = session.query(Product).count()
            total_locations = session.query(Location).filter(Location.is_active == 1).count()
            
            # Total inventory value (approximate)
            total_value = session.query(
                func.sum(Product.unit_cost * Inventory.quantity_on_hand)
            ).join(Inventory).scalar() or 0
            
            # Low stock items count
            low_stock_count = session.query(Inventory).join(Product).filter(
                Inventory.quantity_on_hand <= Product.reorder_point
            ).count()
            
            # Recent transactions count (last 7 days)
            recent_transactions = session.query(Transaction).filter(
                Transaction.timestamp >= datetime.utcnow() - timedelta(days=7)
            ).count()
            
            return {
                'total_products': total_products,
                'total_locations': total_locations,
                'total_inventory_value': float(total_value),
                'low_stock_items': low_stock_count,
                'recent_transactions': recent_transactions
            }
    
    def get_transaction_history(self, product_id: Optional[int] = None, 
                              location_id: Optional[int] = None,
                              limit: int = 100) -> List[Dict[str, Any]]:
        """Get transaction history with optional filters"""
        with self.db.session() as session:
            query = session.query(
                Transaction,
                Product.sku,
                Product.name.label('product_name'),
                Location.location_id,
                Location.name.label('location_name')
            ).join(Product).join(Location).order_by(desc(Transaction.timestamp))
            
            if product_id:
                query = query.filter(Transaction.product_id == product_id)
            if location_id:
                query = query.filter(Transaction.location_id == location_id)
            
            results = []
            for trans, sku, product_name, loc_id, loc_name in query.limit(limit).all():
                results.append({
                    'transaction_id': trans.transaction_id,
                    'sku': sku,
                    'product_name': product_name,
                    'location_id': loc_id,
                    'location_name': loc_name,
                    'transaction_type': trans.transaction_type,
                    'quantity': trans.quantity,
                    'unit_cost': float(trans.unit_cost) if trans.unit_cost else None,
                    'reference_document': trans.reference_document,
                    'timestamp': trans.timestamp,
                    'user_id': trans.user_id,
                    'notes': trans.notes
                })
            
            return results
