"""
Transaction service for inventory movement processing.
"""
from datetime import datetime, timezone
from typing import List, Optional
from sqlmodel import Session, select, and_, desc
from decimal import Decimal

from ..data.models import (
    Transaction, TransactionCreate, TransactionRead,
    TransactionType, Inventory, Product, Location
)
from .inventory_service import InventoryService
from ..config import settings
import logging

logger = logging.getLogger(__name__)


class TransactionService:
    """Service for transaction processing and inventory movements."""
    
    def __init__(self, session: Session):
        self.session = session
        self.inventory_service = InventoryService(session)
    
    def create_transaction(self, transaction_data: TransactionCreate) -> Transaction:
        """Create and process a new transaction."""
        # Validate product and location exist
        product = self.session.get(Product, transaction_data.product_id)
        if not product:
            raise ValueError(f"Product with ID {transaction_data.product_id} not found")
        
        location = self.session.get(Location, transaction_data.location_id)
        if not location:
            raise ValueError(f"Location with ID {transaction_data.location_id} not found")
        
        # Validate transaction based on type
        self._validate_transaction(transaction_data)
        
        # Create transaction record
        transaction = Transaction.model_validate(transaction_data.model_dump())
        transaction.created_at = datetime.now(timezone.utc)
        
        self.session.add(transaction)
        self.session.flush()  # Get the ID but don't commit yet
        
        # Update inventory based on transaction type
        self._process_inventory_update(transaction)
        
        self.session.commit()
        self.session.refresh(transaction)
        
        logger.info(
            f"Processed {transaction.transaction_type} transaction: "
            f"Product {transaction.product_id}, Location {transaction.location_id}, "
            f"Quantity {transaction.quantity}"
        )
        
        return transaction
    
    def create_bulk_transactions(self, transactions_data: List[TransactionCreate]) -> List[Transaction]:
        """Create multiple transactions in a single batch."""
        transactions = []
        
        try:
            for transaction_data in transactions_data:
                transaction = self.create_transaction(transaction_data)
                transactions.append(transaction)
            
            logger.info(f"Processed {len(transactions)} transactions in batch")
            return transactions
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Batch transaction processing failed: {e}")
            raise
    
    def get_transaction(self, transaction_id: int) -> Optional[Transaction]:
        """Get transaction by ID."""
        return self.session.get(Transaction, transaction_id)
    
    def list_transactions(
        self,
        skip: int = 0,
        limit: int = 50,
        product_id: Optional[int] = None,
        location_id: Optional[int] = None,
        transaction_type: Optional[TransactionType] = None,
        reference_number: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Transaction]:
        """List transactions with filtering options."""
        query = select(Transaction)
        
        # Apply filters
        if product_id:
            query = query.where(Transaction.product_id == product_id)
        if location_id:
            query = query.where(Transaction.location_id == location_id)
        if transaction_type:
            query = query.where(Transaction.transaction_type == transaction_type)
        if reference_number:
            query = query.where(Transaction.reference_number == reference_number)
        if start_date:
            query = query.where(Transaction.created_at >= start_date)
        if end_date:
            query = query.where(Transaction.created_at <= end_date)
        
        # Order by most recent first
        query = query.order_by(desc(Transaction.created_at))
        query = query.offset(skip).limit(limit)
        
        return list(self.session.exec(query))
    
    def get_product_transaction_history(
        self, 
        product_id: int,
        limit: int = 100
    ) -> List[Transaction]:
        """Get transaction history for a specific product."""
        query = select(Transaction).where(
            Transaction.product_id == product_id
        ).order_by(desc(Transaction.created_at)).limit(limit)
        
        return list(self.session.exec(query))
    
    def get_location_transaction_history(
        self, 
        location_id: int,
        limit: int = 100
    ) -> List[Transaction]:
        """Get transaction history for a specific location."""
        query = select(Transaction).where(
            Transaction.location_id == location_id
        ).order_by(desc(Transaction.created_at)).limit(limit)
        
        return list(self.session.exec(query))
    
    def process_stock_receipt(
        self,
        product_id: int,
        location_id: int,
        quantity: int,
        reference_number: Optional[str] = None,
        notes: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Transaction:
        """Process stock receipt (IN transaction)."""
        transaction_data = TransactionCreate(
            product_id=product_id,
            location_id=location_id,
            transaction_type=TransactionType.IN,
            quantity=abs(quantity),  # Ensure positive for IN
            reference_number=reference_number,
            notes=notes,
            user_id=user_id
        )
        return self.create_transaction(transaction_data)
    
    def process_stock_shipment(
        self,
        product_id: int,
        location_id: int,
        quantity: int,
        reference_number: Optional[str] = None,
        notes: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Transaction:
        """Process stock shipment (OUT transaction)."""
        transaction_data = TransactionCreate(
            product_id=product_id,
            location_id=location_id,
            transaction_type=TransactionType.OUT,
            quantity=-abs(quantity),  # Ensure negative for OUT
            reference_number=reference_number,
            notes=notes,
            user_id=user_id
        )
        return self.create_transaction(transaction_data)
    
    def process_stock_transfer(
        self,
        product_id: int,
        from_location_id: int,
        to_location_id: int,
        quantity: int,
        reference_number: Optional[str] = None,
        notes: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[Transaction]:
        """Process stock transfer between locations."""
        if from_location_id == to_location_id:
            raise ValueError("Source and destination locations cannot be the same")
        
        # Check available quantity at source location
        available = self.inventory_service.get_available_quantity(product_id, from_location_id)
        if available < quantity:
            raise ValueError(f"Insufficient stock. Available: {available}, Requested: {quantity}")
        
        transactions = []
        
        # OUT transaction from source
        out_transaction = TransactionCreate(
            product_id=product_id,
            location_id=from_location_id,
            transaction_type=TransactionType.TRANSFER,
            quantity=-abs(quantity),
            reference_number=reference_number,
            notes=f"Transfer OUT to Location {to_location_id}" + (f": {notes}" if notes else ""),
            user_id=user_id
        )
        transactions.append(self.create_transaction(out_transaction))
        
        # IN transaction to destination
        in_transaction = TransactionCreate(
            product_id=product_id,
            location_id=to_location_id,
            transaction_type=TransactionType.TRANSFER,
            quantity=abs(quantity),
            reference_number=reference_number,
            notes=f"Transfer IN from Location {from_location_id}" + (f": {notes}" if notes else ""),
            user_id=user_id
        )
        transactions.append(self.create_transaction(in_transaction))
        
        logger.info(f"Processed transfer of {quantity} units from location {from_location_id} to {to_location_id}")
        return transactions
    
    def process_stock_adjustment(
        self,
        product_id: int,
        location_id: int,
        adjustment_quantity: int,
        reason: str,
        user_id: Optional[str] = None
    ) -> Transaction:
        """Process stock adjustment (ADJUSTMENT transaction)."""
        transaction_data = TransactionCreate(
            product_id=product_id,
            location_id=location_id,
            transaction_type=TransactionType.ADJUSTMENT,
            quantity=adjustment_quantity,  # Can be positive or negative
            reference_number=None,
            notes=f"Stock adjustment: {reason}",
            user_id=user_id
        )
        return self.create_transaction(transaction_data)
    
    def get_transaction_summary(
        self,
        product_id: Optional[int] = None,
        location_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """Get transaction summary statistics."""
        query = select(Transaction)
        
        if product_id:
            query = query.where(Transaction.product_id == product_id)
        if location_id:
            query = query.where(Transaction.location_id == location_id)
        if start_date:
            query = query.where(Transaction.created_at >= start_date)
        if end_date:
            query = query.where(Transaction.created_at <= end_date)
        
        transactions = list(self.session.exec(query))
        
        summary = {
            "total_transactions": len(transactions),
            "in_transactions": len([t for t in transactions if t.transaction_type == TransactionType.IN]),
            "out_transactions": len([t for t in transactions if t.transaction_type == TransactionType.OUT]),
            "transfer_transactions": len([t for t in transactions if t.transaction_type == TransactionType.TRANSFER]),
            "adjustment_transactions": len([t for t in transactions if t.transaction_type == TransactionType.ADJUSTMENT]),
            "total_quantity_in": sum(t.quantity for t in transactions if t.quantity > 0),
            "total_quantity_out": abs(sum(t.quantity for t in transactions if t.quantity < 0)),
        }
        
        return summary
    
    # Private helper methods
    
    def _validate_transaction(self, transaction_data: TransactionCreate) -> None:
        """Validate transaction data based on business rules."""
        if transaction_data.quantity == 0:
            raise ValueError("Transaction quantity cannot be zero")
        
        # Validate quantity sign based on transaction type
        if transaction_data.transaction_type == TransactionType.IN and transaction_data.quantity <= 0:
            raise ValueError("IN transactions must have positive quantity")
        
        if transaction_data.transaction_type == TransactionType.OUT and transaction_data.quantity >= 0:
            raise ValueError("OUT transactions must have negative quantity")
        
        # Check available stock for OUT transactions
        if (transaction_data.transaction_type in [TransactionType.OUT, TransactionType.TRANSFER] 
            and transaction_data.quantity < 0):
            available = self.inventory_service.get_available_quantity(
                transaction_data.product_id, 
                transaction_data.location_id
            )
            required = abs(transaction_data.quantity)
            
            if available < required:
                raise ValueError(
                    f"Insufficient stock. Available: {available}, Required: {required}"
                )
    
    def _process_inventory_update(self, transaction: Transaction) -> None:
        """Update inventory levels based on transaction."""
        from ..data.models import InventoryUpdate
        
        # Get current inventory
        inventory = self.inventory_service.get_inventory_by_product_location(
            transaction.product_id, 
            transaction.location_id
        )
        
        if not inventory:
            # Create inventory record if it doesn't exist
            inventory = self.inventory_service.update_inventory(
                transaction.product_id,
                transaction.location_id,
                InventoryUpdate(quantity_on_hand=0, reserved_quantity=0)
            )
        
        # Calculate new quantity
        new_quantity = inventory.quantity_on_hand + transaction.quantity
        
        # Check for negative inventory
        if new_quantity < 0 and not settings.allow_negative_inventory:
            raise ValueError(
                f"Transaction would result in negative inventory: {new_quantity}. "
                f"Current: {inventory.quantity_on_hand}, Transaction: {transaction.quantity}"
            )
        
        # Update inventory
        self.inventory_service.update_inventory(
            transaction.product_id,
            transaction.location_id,
            InventoryUpdate(quantity_on_hand=new_quantity)
        )