"""
Transaction management API endpoints.
"""
from fastapi import APIRouter, HTTPException, Query, Path
from typing import List, Optional
from datetime import datetime

from ..data.models import (
    Transaction, TransactionCreate, TransactionRead, TransactionType
)
from .dependencies import (
    TransactionServiceDep, SkipLimitDep, handle_service_error
)

router = APIRouter()


@router.post("/", response_model=TransactionRead, summary="Create transaction")
async def create_transaction(
    transaction_data: TransactionCreate,
    service: TransactionServiceDep
):
    """Create and process a new transaction."""
    try:
        transaction = service.create_transaction(transaction_data)
        return TransactionRead(
            id=transaction.id,
            product_id=transaction.product_id,
            location_id=transaction.location_id,
            transaction_type=transaction.transaction_type,
            quantity=transaction.quantity,
            reference_number=transaction.reference_number,
            notes=transaction.notes,
            user_id=transaction.user_id,
            created_at=transaction.created_at
        )
    except Exception as e:
        raise handle_service_error(e, "transaction creation")


@router.post("/batch", response_model=List[TransactionRead], summary="Create bulk transactions")
async def create_bulk_transactions(
    transactions_data: List[TransactionCreate],
    service: TransactionServiceDep
):
    """Create multiple transactions in a single batch."""
    try:
        transactions = service.create_bulk_transactions(transactions_data)
        return [
            TransactionRead(
                id=t.id,
                product_id=t.product_id,
                location_id=t.location_id,
                transaction_type=t.transaction_type,
                quantity=t.quantity,
                reference_number=t.reference_number,
                notes=t.notes,
                user_id=t.user_id,
                created_at=t.created_at
            ) for t in transactions
        ]
    except Exception as e:
        raise handle_service_error(e, "bulk transaction creation")


@router.get("/", response_model=List[TransactionRead], summary="List transactions")
async def list_transactions(
    skip_limit: SkipLimitDep,
    product_id: Optional[int] = Query(None, description="Filter by product ID"),
    location_id: Optional[int] = Query(None, description="Filter by location ID"),
    transaction_type: Optional[TransactionType] = Query(None, description="Filter by transaction type"),
    reference_number: Optional[str] = Query(None, description="Filter by reference number"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date (ISO format)"),
    service: TransactionServiceDep = None
):
    """List transactions with optional filtering."""
    try:
        skip, limit = skip_limit
        transactions = service.list_transactions(
            skip=skip,
            limit=limit,
            product_id=product_id,
            location_id=location_id,
            transaction_type=transaction_type,
            reference_number=reference_number,
            start_date=start_date,
            end_date=end_date
        )
        return [
            TransactionRead(
                id=t.id,
                product_id=t.product_id,
                location_id=t.location_id,
                transaction_type=t.transaction_type,
                quantity=t.quantity,
                reference_number=t.reference_number,
                notes=t.notes,
                user_id=t.user_id,
                created_at=t.created_at
            ) for t in transactions
        ]
    except Exception as e:
        raise handle_service_error(e, "transaction listing")


@router.get("/summary", summary="Get transaction summary")
async def get_transaction_summary(
    product_id: Optional[int] = Query(None, description="Filter by product ID"),
    location_id: Optional[int] = Query(None, description="Filter by location ID"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    service: TransactionServiceDep = None
):
    """Get transaction summary statistics."""
    try:
        return service.get_transaction_summary(
            product_id=product_id,
            location_id=location_id,
            start_date=start_date,
            end_date=end_date
        )
    except Exception as e:
        raise handle_service_error(e, "transaction summary retrieval")


@router.post("/receipt", response_model=TransactionRead, summary="Process stock receipt")
async def process_stock_receipt(
    product_id: int = Query(..., description="Product ID"),
    location_id: int = Query(..., description="Location ID"),
    quantity: int = Query(..., ge=1, description="Quantity received"),
    reference_number: Optional[str] = Query(None, description="PO or reference number"),
    notes: Optional[str] = Query(None, description="Additional notes"),
    user_id: Optional[str] = Query(None, description="User ID"),
    service: TransactionServiceDep = None
):
    """Process stock receipt (IN transaction)."""
    try:
        transaction = service.process_stock_receipt(
            product_id=product_id,
            location_id=location_id,
            quantity=quantity,
            reference_number=reference_number,
            notes=notes,
            user_id=user_id
        )
        return TransactionRead(
            id=transaction.id,
            product_id=transaction.product_id,
            location_id=transaction.location_id,
            transaction_type=transaction.transaction_type,
            quantity=transaction.quantity,
            reference_number=transaction.reference_number,
            notes=transaction.notes,
            user_id=transaction.user_id,
            created_at=transaction.created_at
        )
    except Exception as e:
        raise handle_service_error(e, "stock receipt processing")


@router.post("/shipment", response_model=TransactionRead, summary="Process stock shipment")
async def process_stock_shipment(
    product_id: int = Query(..., description="Product ID"),
    location_id: int = Query(..., description="Location ID"),
    quantity: int = Query(..., ge=1, description="Quantity shipped"),
    reference_number: Optional[str] = Query(None, description="DO or reference number"),
    notes: Optional[str] = Query(None, description="Additional notes"),
    user_id: Optional[str] = Query(None, description="User ID"),
    service: TransactionServiceDep = None
):
    """Process stock shipment (OUT transaction)."""
    try:
        transaction = service.process_stock_shipment(
            product_id=product_id,
            location_id=location_id,
            quantity=quantity,
            reference_number=reference_number,
            notes=notes,
            user_id=user_id
        )
        return TransactionRead(
            id=transaction.id,
            product_id=transaction.product_id,
            location_id=transaction.location_id,
            transaction_type=transaction.transaction_type,
            quantity=transaction.quantity,
            reference_number=transaction.reference_number,
            notes=transaction.notes,
            user_id=transaction.user_id,
            created_at=transaction.created_at
        )
    except Exception as e:
        raise handle_service_error(e, "stock shipment processing")


@router.post("/transfer", response_model=List[TransactionRead], summary="Process stock transfer")
async def process_stock_transfer(
    product_id: int = Query(..., description="Product ID"),
    from_location_id: int = Query(..., description="Source location ID"),
    to_location_id: int = Query(..., description="Destination location ID"),
    quantity: int = Query(..., ge=1, description="Quantity to transfer"),
    reference_number: Optional[str] = Query(None, description="Transfer reference number"),
    notes: Optional[str] = Query(None, description="Additional notes"),
    user_id: Optional[str] = Query(None, description="User ID"),
    service: TransactionServiceDep = None
):
    """Process stock transfer between locations."""
    try:
        transactions = service.process_stock_transfer(
            product_id=product_id,
            from_location_id=from_location_id,
            to_location_id=to_location_id,
            quantity=quantity,
            reference_number=reference_number,
            notes=notes,
            user_id=user_id
        )
        return [
            TransactionRead(
                id=t.id,
                product_id=t.product_id,
                location_id=t.location_id,
                transaction_type=t.transaction_type,
                quantity=t.quantity,
                reference_number=t.reference_number,
                notes=t.notes,
                user_id=t.user_id,
                created_at=t.created_at
            ) for t in transactions
        ]
    except Exception as e:
        raise handle_service_error(e, "stock transfer processing")


@router.post("/adjustment", response_model=TransactionRead, summary="Process stock adjustment")
async def process_stock_adjustment(
    product_id: int = Query(..., description="Product ID"),
    location_id: int = Query(..., description="Location ID"),
    adjustment_quantity: int = Query(..., description="Adjustment quantity (positive or negative)"),
    reason: str = Query(..., description="Reason for adjustment"),
    user_id: Optional[str] = Query(None, description="User ID"),
    service: TransactionServiceDep = None
):
    """Process stock adjustment (ADJUSTMENT transaction)."""
    try:
        transaction = service.process_stock_adjustment(
            product_id=product_id,
            location_id=location_id,
            adjustment_quantity=adjustment_quantity,
            reason=reason,
            user_id=user_id
        )
        return TransactionRead(
            id=transaction.id,
            product_id=transaction.product_id,
            location_id=transaction.location_id,
            transaction_type=transaction.transaction_type,
            quantity=transaction.quantity,
            reference_number=transaction.reference_number,
            notes=transaction.notes,
            user_id=transaction.user_id,
            created_at=transaction.created_at
        )
    except Exception as e:
        raise handle_service_error(e, "stock adjustment processing")


@router.get("/{transaction_id}", response_model=TransactionRead, summary="Get transaction by ID")
async def get_transaction(
    transaction_id: int = Path(..., description="Transaction ID"),
    service: TransactionServiceDep = None
):
    """Get transaction by ID."""
    try:
        transaction = service.get_transaction(transaction_id)
        if not transaction:
            raise HTTPException(status_code=404, detail=f"Transaction with ID {transaction_id} not found")
        return TransactionRead(
            id=transaction.id,
            product_id=transaction.product_id,
            location_id=transaction.location_id,
            transaction_type=transaction.transaction_type,
            quantity=transaction.quantity,
            reference_number=transaction.reference_number,
            notes=transaction.notes,
            user_id=transaction.user_id,
            created_at=transaction.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise handle_service_error(e, "transaction retrieval")


@router.get("/product/{product_id}/history", response_model=List[TransactionRead], summary="Get product transaction history")
async def get_product_transaction_history(
    product_id: int = Path(..., description="Product ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of transactions to return"),
    service: TransactionServiceDep = None
):
    """Get transaction history for a specific product."""
    try:
        transactions = service.get_product_transaction_history(product_id, limit)
        return [
            TransactionRead(
                id=t.id,
                product_id=t.product_id,
                location_id=t.location_id,
                transaction_type=t.transaction_type,
                quantity=t.quantity,
                reference_number=t.reference_number,
                notes=t.notes,
                user_id=t.user_id,
                created_at=t.created_at
            ) for t in transactions
        ]
    except Exception as e:
        raise handle_service_error(e, "product transaction history retrieval")


@router.get("/location/{location_id}/history", response_model=List[TransactionRead], summary="Get location transaction history")
async def get_location_transaction_history(
    location_id: int = Path(..., description="Location ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of transactions to return"),
    service: TransactionServiceDep = None
):
    """Get transaction history for a specific location."""
    try:
        transactions = service.get_location_transaction_history(location_id, limit)
        return [
            TransactionRead(
                id=t.id,
                product_id=t.product_id,
                location_id=t.location_id,
                transaction_type=t.transaction_type,
                quantity=t.quantity,
                reference_number=t.reference_number,
                notes=t.notes,
                user_id=t.user_id,
                created_at=t.created_at
            ) for t in transactions
        ]
    except Exception as e:
        raise handle_service_error(e, "location transaction history retrieval")