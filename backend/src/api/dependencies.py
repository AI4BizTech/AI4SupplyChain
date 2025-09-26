"""
Common dependencies for FastAPI endpoints.
"""
from fastapi import Depends, HTTPException, Query
from sqlmodel import Session
from typing import Optional, Annotated

from ..data.database import get_session
from ..data.base import PaginationParams
from ..services.inventory_service import InventoryService
from ..services.transaction_service import TransactionService
from ..services.supplier_service import SupplierService
from ..services.location_service import LocationService


# Database dependency
def get_db_session():
    """Get database session dependency with proper lifecycle management."""
    session_generator = get_session()
    session = next(session_generator)
    try:
        yield session
    finally:
        try:
            next(session_generator)
        except StopIteration:
            pass  # Expected when generator is exhausted


# Service dependencies
def get_inventory_service(session: Session = Depends(get_db_session)) -> InventoryService:
    """Get inventory service dependency."""
    return InventoryService(session)


def get_transaction_service(session: Session = Depends(get_db_session)) -> TransactionService:
    """Get transaction service dependency."""
    return TransactionService(session)


def get_supplier_service(session: Session = Depends(get_db_session)) -> SupplierService:
    """Get supplier service dependency."""
    return SupplierService(session)


def get_location_service(session: Session = Depends(get_db_session)) -> LocationService:
    """Get location service dependency."""
    return LocationService(session)


# Pagination dependency
def get_pagination_params(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    size: int = Query(50, ge=1, le=1000, description="Page size (max 1000)")
) -> PaginationParams:
    """Get pagination parameters."""
    return PaginationParams(page=page, size=size)


# Common query parameters
def get_skip_limit(pagination: PaginationParams = Depends(get_pagination_params)) -> tuple[int, int]:
    """Convert pagination to skip/limit."""
    skip = (pagination.page - 1) * pagination.size
    return skip, pagination.size


# Validation helpers
def validate_positive_int(value: int, field_name: str) -> int:
    """Validate that an integer is positive."""
    if value <= 0:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must be positive"
        )
    return value


def validate_non_negative_int(value: int, field_name: str) -> int:
    """Validate that an integer is non-negative."""
    if value < 0:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} cannot be negative"
        )
    return value


# Error handling helpers
def handle_service_error(error: Exception, operation: str) -> HTTPException:
    """Convert service errors to appropriate HTTP exceptions."""
    error_msg = str(error)
    
    if "not found" in error_msg.lower():
        return HTTPException(status_code=404, detail=error_msg)
    elif "already exists" in error_msg.lower():
        return HTTPException(status_code=409, detail=error_msg)
    elif "insufficient" in error_msg.lower():
        return HTTPException(status_code=400, detail=error_msg)
    elif "invalid" in error_msg.lower() or "cannot" in error_msg.lower():
        return HTTPException(status_code=400, detail=error_msg)
    else:
        return HTTPException(
            status_code=500,
            detail=f"Error during {operation}: {error_msg}"
        )


# Type aliases for common dependencies
DatabaseSession = Annotated[Session, Depends(get_db_session)]
InventoryServiceDep = Annotated[InventoryService, Depends(get_inventory_service)]
TransactionServiceDep = Annotated[TransactionService, Depends(get_transaction_service)]
SupplierServiceDep = Annotated[SupplierService, Depends(get_supplier_service)]
LocationServiceDep = Annotated[LocationService, Depends(get_location_service)]
PaginationDep = Annotated[PaginationParams, Depends(get_pagination_params)]
SkipLimitDep = Annotated[tuple[int, int], Depends(get_skip_limit)]