"""
Location service for warehouse/storage location management.
"""
from datetime import datetime, timezone
from typing import List, Optional
from sqlmodel import Session, select, func
from decimal import Decimal

from ..data.models import (
    Location, LocationCreate, LocationUpdate, LocationRead,
    Inventory, Product, Transaction
)
import logging

logger = logging.getLogger(__name__)


class LocationService:
    """Service for location/warehouse management."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_location(self, location_data: LocationCreate) -> Location:
        """Create a new location."""
        # Check if location name already exists
        existing = self.session.exec(
            select(Location).where(Location.name == location_data.name)
        ).first()
        
        if existing:
            raise ValueError(f"Location with name '{location_data.name}' already exists")
        
        # Check if code is provided and unique
        if location_data.code:
            existing_code = self.session.exec(
                select(Location).where(Location.code == location_data.code)
            ).first()
            if existing_code:
                raise ValueError(f"Location with code '{location_data.code}' already exists")
        
        # Create location
        location = Location.model_validate(location_data.model_dump())
        location.created_at = datetime.now(timezone.utc)
        location.updated_at = datetime.now(timezone.utc)
        
        self.session.add(location)
        self.session.commit()
        self.session.refresh(location)
        
        logger.info(f"Created location: {location.name}")
        return location
    
    def get_location(self, location_id: int) -> Optional[Location]:
        """Get location by ID."""
        return self.session.get(Location, location_id)
    
    def get_location_by_name(self, name: str) -> Optional[Location]:
        """Get location by name."""
        return self.session.exec(
            select(Location).where(Location.name == name)
        ).first()
    
    def get_location_by_code(self, code: str) -> Optional[Location]:
        """Get location by code."""
        return self.session.exec(
            select(Location).where(Location.code == code)
        ).first()
    
    def list_locations(
        self,
        skip: int = 0,
        limit: int = 50,
        is_active: Optional[bool] = None,
        warehouse_type: Optional[str] = None
    ) -> List[Location]:
        """List locations with optional filtering."""
        query = select(Location)
        
        if is_active is not None:
            query = query.where(Location.is_active == is_active)
        if warehouse_type:
            query = query.where(Location.warehouse_type == warehouse_type)
        
        query = query.offset(skip).limit(limit)
        return list(self.session.exec(query))
    
    def update_location(self, location_id: int, location_data: LocationUpdate) -> Optional[Location]:
        """Update location."""
        location = self.session.get(Location, location_id)
        if not location:
            return None
        
        # Check for name conflicts if name is being updated
        if location_data.name and location_data.name != location.name:
            existing = self.session.exec(
                select(Location).where(Location.name == location_data.name)
            ).first()
            if existing:
                raise ValueError(f"Location with name '{location_data.name}' already exists")
        
        # Check for code conflicts if code is being updated
        if location_data.code and location_data.code != location.code:
            existing_code = self.session.exec(
                select(Location).where(Location.code == location_data.code)
            ).first()
            if existing_code:
                raise ValueError(f"Location with code '{location_data.code}' already exists")
        
        # Update fields
        update_data = location_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(location, field, value)
        
        location.updated_at = datetime.now(timezone.utc)
        self.session.add(location)
        self.session.commit()
        self.session.refresh(location)
        
        logger.info(f"Updated location: {location.name}")
        return location
    
    def delete_location(self, location_id: int) -> bool:
        """Soft delete location (deactivate)."""
        location = self.session.get(Location, location_id)
        if not location:
            return False
        
        # Check if location has inventory
        inventory_count = self.session.exec(
            select(func.count(Inventory.id))
            .where(Inventory.location_id == location_id)
            .where(Inventory.quantity_on_hand > 0)
        ).first()
        
        if inventory_count > 0:
            raise ValueError(
                f"Cannot deactivate location with {inventory_count} inventory records. "
                "Move or adjust inventory first."
            )
        
        location.is_active = False
        location.updated_at = datetime.now(timezone.utc)
        self.session.add(location)
        self.session.commit()
        
        logger.info(f"Deactivated location: {location.name}")
        return True

    def delete_location_permanently(self, location_id: int) -> bool:
        """Hard delete location (permanently remove from database)."""
        location = self.session.get(Location, location_id)
        if not location:
            return False

        # Check if location has any inventory records (including zero quantities)
        inventory_count = self.session.exec(
            select(func.count(Inventory.id)).where(Inventory.location_id == location_id)
        ).first()

        if inventory_count > 0:
            # Check if any have non-zero quantities
            nonzero_inventory_count = self.session.exec(
                select(func.count(Inventory.id))
                .where(Inventory.location_id == location_id)
                .where(Inventory.quantity_on_hand > 0)
            ).first()

            if nonzero_inventory_count > 0:
                raise ValueError(
                    f"Cannot permanently delete location {location.name}. "
                    f"It has {nonzero_inventory_count} inventory records with stock. "
                    "Move or adjust inventory first to preserve data integrity."
                )

        # Check if location has any transactions
        transaction_count = self.session.exec(
            select(func.count(Transaction.id)).where(Transaction.location_id == location_id)
        ).first()

        if transaction_count > 0:
            raise ValueError(
                f"Cannot permanently delete location {location.name}. "
                f"It has {transaction_count} transaction records. "
                "Use deactivate instead to preserve transaction history."
            )

        # If there are only empty inventory records (auto-created), delete them first
        if inventory_count > 0:
            self.session.exec(
                select(Inventory).where(Inventory.location_id == location_id)
            ).all()
            for inv in self.session.exec(
                select(Inventory).where(Inventory.location_id == location_id)
            ).all():
                self.session.delete(inv)

        name = location.name
        self.session.delete(location)
        self.session.commit()

        logger.warning(f"Permanently deleted location: {name}")
        return True
    
    def get_location_inventory(self, location_id: int) -> List[Inventory]:
        """Get all inventory records for a location."""
        return list(self.session.exec(
            select(Inventory)
            .where(Inventory.location_id == location_id)
            .where(Inventory.quantity_on_hand > 0)
        ))
    
    def get_location_inventory_summary(self, location_id: int) -> dict:
        """Get inventory summary for a location."""
        location = self.get_location(location_id)
        if not location:
            raise ValueError(f"Location with ID {location_id} not found")
        
        inventory_records = self.get_location_inventory(location_id)
        
        total_products = len(inventory_records)
        total_quantity = sum(inv.quantity_on_hand for inv in inventory_records)
        total_reserved = sum(inv.reserved_quantity for inv in inventory_records)
        total_available = sum(max(0, inv.quantity_on_hand - inv.reserved_quantity) for inv in inventory_records)
        
        # Calculate total value (need to join with products for unit cost)
        inventory_with_products = list(self.session.exec(
            select(Inventory, Product)
            .where(Inventory.location_id == location_id)
            .where(Inventory.quantity_on_hand > 0)
            .where(Inventory.product_id == Product.id)
        ))
        
        total_value = sum(
            inv.quantity_on_hand * product.unit_cost 
            for inv, product in inventory_with_products
        )
        
        return {
            "location_id": location_id,
            "location_name": location.name,
            "location_code": location.code,
            "total_products": total_products,
            "total_quantity": total_quantity,
            "total_reserved": total_reserved,
            "total_available": total_available,
            "total_value": float(total_value),
            "is_active": location.is_active
        }
    
    def get_location_activity(self, location_id: int, days: int = 30) -> dict:
        """Get recent activity summary for a location."""
        from datetime import timedelta
        
        location = self.get_location(location_id)
        if not location:
            raise ValueError(f"Location with ID {location_id} not found")
        
        # Get transactions from the last N days
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        recent_transactions = list(self.session.exec(
            select(Transaction)
            .where(Transaction.location_id == location_id)
            .where(Transaction.created_at >= cutoff_date)
        ))
        
        # Categorize transactions
        in_transactions = [t for t in recent_transactions if t.quantity > 0]
        out_transactions = [t for t in recent_transactions if t.quantity < 0]
        
        total_in = sum(t.quantity for t in in_transactions)
        total_out = abs(sum(t.quantity for t in out_transactions))
        
        # Prepare transaction type summary
        transaction_types = {}
        for txn in recent_transactions:
            txn_type = txn.transaction_type.value
            if txn_type not in transaction_types:
                transaction_types[txn_type] = 0
            transaction_types[txn_type] += 1
        
        return {
            "location_id": location_id,
            "location_name": location.name,
            "period_days": days,
            "total_transactions": len(recent_transactions),
            "in_transactions": len(in_transactions),
            "out_transactions": len(out_transactions),
            "total_quantity_in": total_in,
            "total_quantity_out": total_out,
            "net_change": total_in - total_out,
            "recent_transactions": [
                {
                    "id": t.id,
                    "transaction_type": t.transaction_type.value,
                    "quantity": t.quantity,
                    "product_id": t.product_id,
                    "created_at": t.created_at,
                    "reference_number": t.reference_number,
                    "user_id": t.user_id
                }
                for t in sorted(recent_transactions, key=lambda x: x.created_at, reverse=True)[:10]
            ],
            "transaction_types": transaction_types
        }
    
    def get_location_statistics(self) -> dict:
        """Get overall location statistics."""
        total_locations = self.session.exec(select(func.count(Location.id))).first()
        active_locations = self.session.exec(
            select(func.count(Location.id)).where(Location.is_active == True)
        ).first()
        
        # Get warehouse types
        warehouse_types = list(self.session.exec(
            select(Location.warehouse_type)
            .where(Location.warehouse_type.is_not(None))
            .distinct()
        ))
        
        # Get locations with most inventory
        locations_with_inventory = list(self.session.exec(
            select(Location.id, Location.name, func.sum(Inventory.quantity_on_hand).label("total_qty"))
            .join(Inventory, Location.id == Inventory.location_id)
            .where(Location.is_active == True)
            .group_by(Location.id, Location.name)
            .order_by(func.sum(Inventory.quantity_on_hand).desc())
            .limit(5)
        ))
        
        return {
            "total_locations": total_locations or 0,
            "active_locations": active_locations or 0,
            "inactive_locations": (total_locations or 0) - (active_locations or 0),
            "warehouse_types": warehouse_types,
            "top_locations_by_inventory": [
                {
                    "id": row[0],
                    "name": row[1], 
                    "total_quantity": row[2]
                }
                for row in locations_with_inventory
            ]
        }
    
    def get_empty_locations(self) -> List[Location]:
        """Get locations with no inventory."""
        return list(self.session.exec(
            select(Location)
            .where(Location.is_active == True)
            .where(~Location.id.in_(
                select(Inventory.location_id)
                .where(Inventory.quantity_on_hand > 0)
                .distinct()
            ))
        ))
    
    def get_locations_with_low_activity(self, days: int = 30, min_transactions: int = 5) -> List[Location]:
        """Get locations with low transaction activity."""
        from datetime import timedelta
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get locations with transaction counts
        locations_with_counts = list(self.session.exec(
            select(Location.id, Location.name, func.count(Transaction.id).label("transaction_count"))
            .outerjoin(Transaction, Location.id == Transaction.location_id)
            .where(Location.is_active == True)
            .where((Transaction.created_at >= cutoff_date) | (Transaction.created_at.is_(None)))
            .group_by(Location.id, Location.name)
            .having(func.count(Transaction.id) < min_transactions)
        ))
        
        # Convert to Location objects
        low_activity_location_ids = [row[0] for row in locations_with_counts]
        return list(self.session.exec(
            select(Location).where(Location.id.in_(low_activity_location_ids))
        ))
    
    def get_warehouse_types(self) -> List[str]:
        """Get list of distinct warehouse types."""
        result = self.session.exec(
            select(Location.warehouse_type)
            .distinct()
            .where(Location.warehouse_type.is_not(None))
        )
        return [wt for wt in result if wt]