"""
Inventory service for product and stock management operations.
"""
from datetime import datetime, timezone
from typing import List, Optional
from sqlmodel import Session, select, and_
from decimal import Decimal

from ..data.models import (
    Product, ProductCreate, ProductUpdate, ProductRead,
    Inventory, InventoryUpdate, InventoryRead,
    Location, Supplier
)
from ..config import settings
import logging

logger = logging.getLogger(__name__)


class InventoryService:
    """Service for inventory and product management."""
    
    def __init__(self, session: Session):
        self.session = session
    
    # Product CRUD operations
    
    def create_product(self, product_data: ProductCreate) -> Product:
        """Create a new product."""
        # Check if SKU already exists
        existing = self.session.exec(
            select(Product).where(Product.sku == product_data.sku)
        ).first()
        
        if existing:
            raise ValueError(f"Product with SKU '{product_data.sku}' already exists")
        
        # Validate supplier if provided
        if product_data.supplier_id:
            supplier = self.session.get(Supplier, product_data.supplier_id)
            if not supplier or not supplier.is_active:
                raise ValueError(f"Invalid or inactive supplier ID: {product_data.supplier_id}")
        
        # Create product
        product = Product.model_validate(product_data.model_dump())
        self.session.add(product)
        self.session.commit()
        self.session.refresh(product)
        
        # Auto-create inventory records if enabled
        if settings.auto_create_inventory_records:
            self._create_initial_inventory_records(product.id)
        
        logger.info(f"Created product: {product.sku} - {product.name}")
        return product
    
    def get_product(self, product_id: int) -> Optional[Product]:
        """Get product by ID."""
        return self.session.get(Product, product_id)
    
    def get_product_by_sku(self, sku: str) -> Optional[Product]:
        """Get product by SKU."""
        return self.session.exec(
            select(Product).where(Product.sku == sku)
        ).first()
    
    def list_products(
        self, 
        skip: int = 0, 
        limit: int = 50,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        supplier_id: Optional[int] = None
    ) -> List[Product]:
        """List products with optional filtering."""
        query = select(Product)
        
        if category:
            query = query.where(Product.category == category)
        if is_active is not None:
            query = query.where(Product.is_active == is_active)
        if supplier_id:
            query = query.where(Product.supplier_id == supplier_id)
        
        query = query.offset(skip).limit(limit)
        return list(self.session.exec(query))
    
    def update_product(self, product_id: int, product_data: ProductUpdate) -> Optional[Product]:
        """Update product."""
        product = self.session.get(Product, product_id)
        if not product:
            return None
        
        # Validate supplier if being updated
        if product_data.supplier_id:
            supplier = self.session.get(Supplier, product_data.supplier_id)
            if not supplier or not supplier.is_active:
                raise ValueError(f"Invalid or inactive supplier ID: {product_data.supplier_id}")
        
        # Update fields
        update_data = product_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)
        
        product.updated_at = datetime.now(timezone.utc)
        self.session.add(product)
        self.session.commit()
        self.session.refresh(product)
        
        logger.info(f"Updated product: {product.sku}")
        return product
    
    def delete_product(self, product_id: int) -> bool:
        """Soft delete product (deactivate)."""
        product = self.session.get(Product, product_id)
        if not product:
            return False

        product.is_active = False
        product.updated_at = datetime.now(timezone.utc)
        self.session.add(product)
        self.session.commit()

        logger.info(f"Deactivated product: {product.sku}")
        return True

    def delete_product_permanently(self, product_id: int) -> bool:
        """Hard delete product (permanently remove from database)."""
        product = self.session.get(Product, product_id)
        if not product:
            return False

        # Check if product has any transactions or inventory records
        from .transaction_service import TransactionService

        transaction_service = TransactionService(self.session)
        has_transactions = len(transaction_service.list_transactions(product_id=product_id)) > 0

        inventory_items = self.session.exec(
            select(Inventory).where(Inventory.product_id == product_id)
        ).all()

        # Check if there are any non-zero inventory quantities
        has_meaningful_inventory = any(
            item.quantity_on_hand > 0 or item.reserved_quantity > 0
            for item in inventory_items
        )

        if has_transactions:
            raise ValueError(
                f"Cannot permanently delete product {product.sku}. "
                "It has existing transaction history. "
                "Use deactivate instead to preserve data integrity."
            )

        if has_meaningful_inventory:
            raise ValueError(
                f"Cannot permanently delete product {product.sku}. "
                "It has existing inventory quantities. "
                "Use deactivate instead to preserve data integrity."
            )

        # Delete empty inventory records first (auto-created records with zero quantities)
        for item in inventory_items:
            self.session.delete(item)

        sku = product.sku
        self.session.delete(product)
        self.session.commit()

        logger.warning(f"Permanently deleted product: {sku}")
        return True
    
    # Inventory operations
    
    def get_inventory(
        self, 
        product_id: Optional[int] = None,
        location_id: Optional[int] = None
    ) -> List[Inventory]:
        """Get inventory records with optional filtering."""
        query = select(Inventory)
        
        if product_id:
            query = query.where(Inventory.product_id == product_id)
        if location_id:
            query = query.where(Inventory.location_id == location_id)
        
        return list(self.session.exec(query))
    
    def get_inventory_by_product_location(
        self, 
        product_id: int, 
        location_id: int
    ) -> Optional[Inventory]:
        """Get specific inventory record."""
        return self.session.exec(
            select(Inventory).where(
                and_(
                    Inventory.product_id == product_id,
                    Inventory.location_id == location_id
                )
            )
        ).first()
    
    def update_inventory(
        self, 
        product_id: int, 
        location_id: int, 
        inventory_data: InventoryUpdate
    ) -> Optional[Inventory]:
        """Update inventory quantities."""
        inventory = self.get_inventory_by_product_location(product_id, location_id)
        
        if not inventory:
            # Create if doesn't exist
            inventory = Inventory(
                product_id=product_id,
                location_id=location_id,
                quantity_on_hand=0,
                reserved_quantity=0
            )
            self.session.add(inventory)
        
        # Update quantities
        update_data = inventory_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                if field == "quantity_on_hand" and value < 0 and not settings.allow_negative_inventory:
                    raise ValueError("Negative inventory not allowed")
                setattr(inventory, field, value)
        
        inventory.last_updated = datetime.now(timezone.utc)
        self.session.add(inventory)
        self.session.commit()
        self.session.refresh(inventory)
        
        logger.info(f"Updated inventory for product {product_id} at location {location_id}")
        return inventory
    
    def get_available_quantity(self, product_id: int, location_id: int) -> int:
        """Get available quantity (on_hand - reserved)."""
        inventory = self.get_inventory_by_product_location(product_id, location_id)
        if not inventory:
            return 0
        return max(0, inventory.quantity_on_hand - inventory.reserved_quantity)
    
    def get_total_available_quantity(self, product_id: int) -> int:
        """Get total available quantity across all locations."""
        inventories = self.get_inventory(product_id=product_id)
        total = 0
        for inv in inventories:
            total += max(0, inv.quantity_on_hand - inv.reserved_quantity)
        return total
    
    def get_low_stock_products(self) -> List[Product]:
        """Get products with stock below reorder point."""
        from sqlmodel import text
        
        query = text("""
        SELECT p.* FROM products p
        JOIN (
            SELECT product_id, SUM(quantity_on_hand - reserved_quantity) as available
            FROM inventory
            GROUP BY product_id
        ) i ON p.id = i.product_id
        WHERE i.available <= p.reorder_point AND p.is_active = 1
        """)
        result = self.session.exec(query)
        return list(result)
    
    def reserve_inventory(
        self, 
        product_id: int, 
        location_id: int, 
        quantity: int
    ) -> bool:
        """Reserve inventory quantity."""
        inventory = self.get_inventory_by_product_location(product_id, location_id)
        if not inventory:
            return False
        
        available = inventory.quantity_on_hand - inventory.reserved_quantity
        if available < quantity:
            return False
        
        inventory.reserved_quantity += quantity
        inventory.last_updated = datetime.now(timezone.utc)
        self.session.add(inventory)
        self.session.commit()
        
        logger.info(f"Reserved {quantity} units of product {product_id} at location {location_id}")
        return True
    
    def release_reservation(
        self, 
        product_id: int, 
        location_id: int, 
        quantity: int
    ) -> bool:
        """Release reserved inventory."""
        inventory = self.get_inventory_by_product_location(product_id, location_id)
        if not inventory:
            return False
        
        inventory.reserved_quantity = max(0, inventory.reserved_quantity - quantity)
        inventory.last_updated = datetime.now(timezone.utc)
        self.session.add(inventory)
        self.session.commit()
        
        logger.info(f"Released {quantity} reserved units of product {product_id} at location {location_id}")
        return True
    
    # Helper methods
    
    def _create_initial_inventory_records(self, product_id: int) -> None:
        """Create initial inventory records for all active locations."""
        locations = self.session.exec(
            select(Location).where(Location.is_active == True)
        ).all()
        
        for location in locations:
            existing = self.get_inventory_by_product_location(product_id, location.id)
            if not existing:
                inventory = Inventory(
                    product_id=product_id,
                    location_id=location.id,
                    quantity_on_hand=0,
                    reserved_quantity=0
                )
                self.session.add(inventory)
        
        self.session.commit()
        logger.info(f"Created initial inventory records for product {product_id}")
    
    def get_product_categories(self) -> List[str]:
        """Get list of distinct product categories."""
        result = self.session.exec(
            select(Product.category).distinct().where(Product.category.is_not(None))
        )
        return [cat for cat in result if cat]