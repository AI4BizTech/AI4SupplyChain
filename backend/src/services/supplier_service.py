"""
Supplier service for vendor management operations.
"""
from datetime import datetime, timezone
from typing import List, Optional
from sqlmodel import Session, select, func
from decimal import Decimal

from ..data.models import (
    Supplier, SupplierCreate, SupplierUpdate, SupplierRead,
    Product, Transaction, TransactionType
)
import logging

logger = logging.getLogger(__name__)


class SupplierService:
    """Service for supplier/vendor management."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_supplier(self, supplier_data: SupplierCreate) -> Supplier:
        """Create a new supplier."""
        # Check if supplier name already exists
        existing = self.session.exec(
            select(Supplier).where(Supplier.name == supplier_data.name)
        ).first()
        
        if existing:
            raise ValueError(f"Supplier with name '{supplier_data.name}' already exists")
        
        # Create supplier
        supplier = Supplier.model_validate(supplier_data.model_dump())
        supplier.created_at = datetime.now(timezone.utc)
        supplier.updated_at = datetime.now(timezone.utc)
        
        self.session.add(supplier)
        self.session.commit()
        self.session.refresh(supplier)
        
        logger.info(f"Created supplier: {supplier.name}")
        return supplier
    
    def get_supplier(self, supplier_id: int) -> Optional[Supplier]:
        """Get supplier by ID."""
        return self.session.get(Supplier, supplier_id)
    
    def get_supplier_by_name(self, name: str) -> Optional[Supplier]:
        """Get supplier by name."""
        return self.session.exec(
            select(Supplier).where(Supplier.name == name)
        ).first()
    
    def list_suppliers(
        self,
        skip: int = 0,
        limit: int = 50,
        is_active: Optional[bool] = None,
        min_rating: Optional[float] = None
    ) -> List[Supplier]:
        """List suppliers with optional filtering."""
        query = select(Supplier)
        
        if is_active is not None:
            query = query.where(Supplier.is_active == is_active)
        if min_rating is not None:
            query = query.where(Supplier.performance_rating >= min_rating)
        
        query = query.offset(skip).limit(limit)
        return list(self.session.exec(query))
    
    def update_supplier(self, supplier_id: int, supplier_data: SupplierUpdate) -> Optional[Supplier]:
        """Update supplier."""
        supplier = self.session.get(Supplier, supplier_id)
        if not supplier:
            return None
        
        # Check for name conflicts if name is being updated
        if supplier_data.name and supplier_data.name != supplier.name:
            existing = self.session.exec(
                select(Supplier).where(Supplier.name == supplier_data.name)
            ).first()
            if existing:
                raise ValueError(f"Supplier with name '{supplier_data.name}' already exists")
        
        # Update fields
        update_data = supplier_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(supplier, field, value)
        
        supplier.updated_at = datetime.now(timezone.utc)
        self.session.add(supplier)
        self.session.commit()
        self.session.refresh(supplier)
        
        logger.info(f"Updated supplier: {supplier.name}")
        return supplier
    
    def delete_supplier(self, supplier_id: int) -> bool:
        """Soft delete supplier (deactivate)."""
        supplier = self.session.get(Supplier, supplier_id)
        if not supplier:
            return False
        
        # Check if supplier has active products
        active_products_count = self.session.exec(
            select(func.count(Product.id))
            .where(Product.supplier_id == supplier_id)
            .where(Product.is_active == True)
        ).first()
        
        if active_products_count > 0:
            raise ValueError(
                f"Cannot deactivate supplier with {active_products_count} active products. "
                "Deactivate products first or reassign them to another supplier."
            )
        
        supplier.is_active = False
        supplier.updated_at = datetime.now(timezone.utc)
        self.session.add(supplier)
        self.session.commit()
        
        logger.info(f"Deactivated supplier: {supplier.name}")
        return True

    def delete_supplier_permanently(self, supplier_id: int) -> bool:
        """Hard delete supplier (permanently remove from database)."""
        supplier = self.session.get(Supplier, supplier_id)
        if not supplier:
            return False

        # Check if supplier has any products
        products_count = self.session.exec(
            select(func.count(Product.id)).where(Product.supplier_id == supplier_id)
        ).first()

        if products_count > 0:
            raise ValueError(
                f"Cannot permanently delete supplier {supplier.name}. "
                f"It has {products_count} associated products. "
                "Remove or reassign products first to preserve data integrity."
            )

        # Check if supplier has any transactions through their products
        # This is additional safety even though we check products above
        from .transaction_service import TransactionService
        transaction_service = TransactionService(self.session)

        # Get all products that were ever associated with this supplier
        all_supplier_products = self.session.exec(
            select(Product.id).where(Product.supplier_id == supplier_id)
        ).all()

        if all_supplier_products:
            # Check for any transactions involving these products
            for product_id in all_supplier_products:
                transactions = transaction_service.list_transactions(product_id=product_id)
                if transactions:
                    raise ValueError(
                        f"Cannot permanently delete supplier {supplier.name}. "
                        "It has products with existing transaction history. "
                        "Use deactivate instead to preserve data integrity."
                    )

        name = supplier.name
        self.session.delete(supplier)
        self.session.commit()

        logger.warning(f"Permanently deleted supplier: {name}")
        return True
    
    def get_supplier_products(self, supplier_id: int) -> List[Product]:
        """Get all products from a supplier."""
        return list(self.session.exec(
            select(Product).where(Product.supplier_id == supplier_id)
        ))
    
    def get_supplier_active_products(self, supplier_id: int) -> List[Product]:
        """Get active products from a supplier."""
        return list(self.session.exec(
            select(Product)
            .where(Product.supplier_id == supplier_id)
            .where(Product.is_active == True)
        ))
    
    def calculate_supplier_performance(self, supplier_id: int) -> dict:
        """Calculate supplier performance metrics."""
        supplier = self.get_supplier(supplier_id)
        if not supplier:
            raise ValueError(f"Supplier with ID {supplier_id} not found")
        
        # Get supplier products
        products = self.get_supplier_products(supplier_id)
        product_ids = [p.id for p in products]
        
        if not product_ids:
            return {
                "supplier_id": supplier_id,
                "supplier_name": supplier.name,
                "total_products": 0,
                "active_products": 0,
                "total_receipts": 0,
                "total_quantity_received": 0,
                "avg_lead_time": supplier.lead_time_days,
                "performance_score": 0.0
            }
        
        # Get receipt transactions for supplier products
        receipt_transactions = list(self.session.exec(
            select(Transaction)
            .where(Transaction.product_id.in_(product_ids))
            .where(Transaction.transaction_type == TransactionType.IN)
        ))
        
        # Calculate metrics
        total_receipts = len(receipt_transactions)
        total_quantity_received = sum(t.quantity for t in receipt_transactions if t.quantity > 0)
        active_products_count = len([p for p in products if p.is_active])
        
        # Simple performance score based on activity and lead time
        performance_score = 0.0
        if total_receipts > 0:
            # Score based on activity level and lead time efficiency
            activity_score = min(5.0, total_receipts / 10)  # Max 5 points for activity
            lead_time_score = max(0, 5.0 - (supplier.lead_time_days / 10))  # Better score for shorter lead times
            performance_score = (activity_score + lead_time_score) / 2
        
        return {
            "supplier_id": supplier_id,
            "supplier_name": supplier.name,
            "total_products": len(products),
            "active_products": active_products_count,
            "total_receipts": total_receipts,
            "total_quantity_received": total_quantity_received,
            "avg_lead_time": supplier.lead_time_days,
            "performance_score": round(performance_score, 2)
        }
    
    def update_supplier_performance_rating(self, supplier_id: int) -> Optional[Supplier]:
        """Update supplier's performance rating based on calculated metrics."""
        performance = self.calculate_supplier_performance(supplier_id)
        
        supplier = self.get_supplier(supplier_id)
        if not supplier:
            return None
        
        supplier.performance_rating = performance["performance_score"]
        supplier.updated_at = datetime.now(timezone.utc)
        
        self.session.add(supplier)
        self.session.commit()
        self.session.refresh(supplier)
        
        logger.info(f"Updated performance rating for supplier {supplier.name}: {supplier.performance_rating}")
        return supplier
    
    def get_supplier_statistics(self) -> dict:
        """Get overall supplier statistics."""
        total_suppliers = self.session.exec(select(func.count(Supplier.id))).first()
        active_suppliers = self.session.exec(
            select(func.count(Supplier.id)).where(Supplier.is_active == True)
        ).first()
        
        # Average lead time
        avg_lead_time = self.session.exec(
            select(func.avg(Supplier.lead_time_days)).where(Supplier.is_active == True)
        ).first()
        
        # Average performance rating 
        avg_performance = self.session.exec(
            select(func.avg(Supplier.performance_rating))
            .where(Supplier.is_active == True)
            .where(Supplier.performance_rating.is_not(None))
        ).first()
        
        # Top performing suppliers
        top_suppliers = list(self.session.exec(
            select(Supplier)
            .where(Supplier.is_active == True)
            .where(Supplier.performance_rating.is_not(None))
            .order_by(Supplier.performance_rating.desc())
            .limit(5)
        ))
        
        return {
            "total_suppliers": total_suppliers or 0,
            "active_suppliers": active_suppliers or 0,
            "inactive_suppliers": (total_suppliers or 0) - (active_suppliers or 0),
            "average_lead_time_days": round(avg_lead_time, 1) if avg_lead_time else 0,
            "average_performance_rating": round(avg_performance, 1) if avg_performance else 0,
            "top_suppliers": [
                {
                    "id": s.id,
                    "name": s.name,
                    "performance_rating": s.performance_rating,
                    "lead_time_days": s.lead_time_days
                }
                for s in top_suppliers
            ]
        }
    
    def get_suppliers_needing_review(self) -> List[Supplier]:
        """Get suppliers that might need performance review."""
        # Suppliers with no performance rating or low rating
        return list(self.session.exec(
            select(Supplier)
            .where(Supplier.is_active == True)
            .where(
                (Supplier.performance_rating.is_(None)) |
                (Supplier.performance_rating < 3.0)
            )
        ))
    
    def bulk_update_performance_ratings(self) -> int:
        """Update performance ratings for all active suppliers."""
        active_suppliers = self.list_suppliers(is_active=True)
        updated_count = 0
        
        for supplier in active_suppliers:
            try:
                self.update_supplier_performance_rating(supplier.id)
                updated_count += 1
            except Exception as e:
                logger.warning(f"Failed to update performance rating for supplier {supplier.id}: {e}")
                continue
        
        logger.info(f"Updated performance ratings for {updated_count} suppliers")
        return updated_count