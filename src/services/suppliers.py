"""
Supplier management service
"""

from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import logging
from datetime import datetime, timedelta

from src.data.database import get_database
from src.data.inventory import Supplier, Product, Transaction

logger = logging.getLogger(__name__)

class SupplierService:
    """Service for managing supplier operations"""
    
    def __init__(self, db=None):
        self.db = db or get_database()
    
    def create_supplier(self, supplier_data: Dict[str, Any]) -> Supplier:
        """Create a new supplier"""
        with self.db.session() as session:
            supplier = Supplier(**supplier_data)
            session.add(supplier)
            session.flush()
            session.refresh(supplier)
            return supplier
    
    def get_supplier_by_id(self, supplier_id: str) -> Optional[Supplier]:
        """Get supplier by supplier_id"""
        with self.db.session() as session:
            return session.query(Supplier).filter(Supplier.supplier_id == supplier_id).first()
    
    def get_supplier_by_pk(self, pk: int) -> Optional[Supplier]:
        """Get supplier by primary key"""
        with self.db.session() as session:
            return session.query(Supplier).filter(Supplier.id == pk).first()
    
    def list_suppliers(self, limit: int = 100) -> List[Supplier]:
        """List all suppliers"""
        with self.db.session() as session:
            return session.query(Supplier).limit(limit).all()
    
    def update_supplier(self, supplier_pk: int, updates: Dict[str, Any]) -> Optional[Supplier]:
        """Update supplier information"""
        with self.db.session() as session:
            supplier = session.query(Supplier).filter(Supplier.id == supplier_pk).first()
            if supplier:
                for key, value in updates.items():
                    setattr(supplier, key, value)
                supplier.updated_at = datetime.utcnow()
                session.flush()
                session.refresh(supplier)
            return supplier
    
    def get_supplier_products(self, supplier_id: str) -> List[Dict[str, Any]]:
        """Get all products from a specific supplier"""
        with self.db.session() as session:
            supplier = session.query(Supplier).filter(Supplier.supplier_id == supplier_id).first()
            if not supplier:
                return []
            
            products = session.query(Product).filter(Product.supplier_id == supplier.id).all()
            
            result = []
            for product in products:
                result.append({
                    'sku': product.sku,
                    'name': product.name,
                    'category': product.category,
                    'unit_cost': float(product.unit_cost),
                    'reorder_point': product.reorder_point,
                    'reorder_quantity': product.reorder_quantity
                })
            
            return result
    
    def get_supplier_performance(self, supplier_id: str, days: int = 90) -> Dict[str, Any]:
        """Calculate supplier performance metrics"""
        with self.db.session() as session:
            supplier = session.query(Supplier).filter(Supplier.supplier_id == supplier_id).first()
            if not supplier:
                return {}
            
            # Get products from this supplier
            product_ids = session.query(Product.id).filter(Product.supplier_id == supplier.id).all()
            product_ids = [pid[0] for pid in product_ids]
            
            if not product_ids:
                return {
                    'supplier_id': supplier_id,
                    'supplier_name': supplier.name,
                    'total_orders': 0,
                    'total_value': 0.0,
                    'average_lead_time': supplier.lead_time_days,
                    'on_time_delivery_rate': 0.0,
                    'performance_rating': float(supplier.performance_rating or 0.0)
                }
            
            # Get recent transactions (receipts) for performance calculation
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            recent_receipts = session.query(Transaction).filter(
                Transaction.product_id.in_(product_ids),
                Transaction.transaction_type == 'receipt',
                Transaction.timestamp >= cutoff_date
            ).all()
            
            total_orders = len(recent_receipts)
            total_value = sum(
                float(t.unit_cost * t.quantity) if t.unit_cost else 0 
                for t in recent_receipts
            )
            
            # Calculate average lead time (simplified - would need PO dates for accuracy)
            avg_lead_time = supplier.lead_time_days
            
            # Simplified on-time delivery rate (would need more sophisticated tracking)
            on_time_rate = 0.85 if total_orders > 0 else 0.0  # Placeholder
            
            return {
                'supplier_id': supplier_id,
                'supplier_name': supplier.name,
                'total_orders': total_orders,
                'total_value': total_value,
                'average_lead_time': avg_lead_time,
                'on_time_delivery_rate': on_time_rate,
                'performance_rating': float(supplier.performance_rating or 0.0),
                'contact_info': supplier.contact_info,
                'payment_terms': supplier.payment_terms,
                'minimum_order_qty': supplier.minimum_order_qty
            }
    
    def get_suppliers_summary(self) -> List[Dict[str, Any]]:
        """Get summary of all suppliers with basic metrics"""
        with self.db.session() as session:
            suppliers = session.query(Supplier).all()
            
            results = []
            for supplier in suppliers:
                # Count products for this supplier
                product_count = session.query(Product).filter(Product.supplier_id == supplier.id).count()
                
                # Get recent transaction value (last 30 days)
                cutoff_date = datetime.utcnow() - timedelta(days=30)
                product_ids = session.query(Product.id).filter(Product.supplier_id == supplier.id).all()
                product_ids = [pid[0] for pid in product_ids]
                
                recent_value = 0.0
                if product_ids:
                    recent_transactions = session.query(func.sum(Transaction.quantity * Transaction.unit_cost)).filter(
                        Transaction.product_id.in_(product_ids),
                        Transaction.transaction_type == 'receipt',
                        Transaction.timestamp >= cutoff_date,
                        Transaction.unit_cost.isnot(None)
                    ).scalar()
                    recent_value = float(recent_transactions or 0.0)
                
                results.append({
                    'supplier_id': supplier.supplier_id,
                    'name': supplier.name,
                    'product_count': product_count,
                    'lead_time_days': supplier.lead_time_days,
                    'performance_rating': float(supplier.performance_rating or 0.0),
                    'recent_order_value': recent_value,
                    'payment_terms': supplier.payment_terms,
                    'contact_info': supplier.contact_info
                })
            
            return results
    
    def update_performance_rating(self, supplier_id: str, rating: float) -> bool:
        """Update supplier performance rating (0.0 to 5.0)"""
        if not (0.0 <= rating <= 5.0):
            return False
        
        with self.db.session() as session:
            supplier = session.query(Supplier).filter(Supplier.supplier_id == supplier_id).first()
            if supplier:
                supplier.performance_rating = rating
                supplier.updated_at = datetime.utcnow()
                session.flush()
                return True
            return False
