"""
Supplier management API endpoints.
"""
from fastapi import APIRouter, HTTPException, Query, Path
from typing import List, Optional

from ..data.models import (
    Supplier, SupplierCreate, SupplierUpdate, SupplierRead
)
from .dependencies import (
    SupplierServiceDep, SkipLimitDep, handle_service_error
)

router = APIRouter()


@router.post("/", response_model=SupplierRead, summary="Create supplier")
async def create_supplier(
    supplier_data: SupplierCreate,
    service: SupplierServiceDep
):
    """Create a new supplier."""
    try:
        supplier = service.create_supplier(supplier_data)
        return SupplierRead.model_validate(supplier.model_dump())
    except Exception as e:
        raise handle_service_error(e, "supplier creation")


@router.get("/", response_model=List[SupplierRead], summary="List suppliers")
async def list_suppliers(
    skip_limit: SkipLimitDep,
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="Minimum performance rating"),
    service: SupplierServiceDep = None
):
    """List suppliers with optional filtering."""
    try:
        skip, limit = skip_limit
        suppliers = service.list_suppliers(
            skip=skip,
            limit=limit,
            is_active=is_active,
            min_rating=min_rating
        )
        return [SupplierRead.model_validate(s.model_dump()) for s in suppliers]
    except Exception as e:
        raise handle_service_error(e, "supplier listing")


@router.get("/statistics", summary="Get supplier statistics")
async def get_supplier_statistics(service: SupplierServiceDep):
    """Get overall supplier statistics."""
    try:
        return service.get_supplier_statistics()
    except Exception as e:
        raise handle_service_error(e, "supplier statistics retrieval")


@router.get("/performance/update-all", summary="Update all performance ratings")
async def update_all_performance_ratings(service: SupplierServiceDep):
    """Update performance ratings for all active suppliers."""
    try:
        updated_count = service.bulk_update_performance_ratings()
        return {
            "message": f"Updated performance ratings for {updated_count} suppliers",
            "updated_count": updated_count
        }
    except Exception as e:
        raise handle_service_error(e, "bulk performance rating update")


@router.get("/review-needed", response_model=List[SupplierRead], summary="Get suppliers needing review")
async def get_suppliers_needing_review(service: SupplierServiceDep):
    """Get suppliers that might need performance review."""
    try:
        suppliers = service.get_suppliers_needing_review()
        return [SupplierRead.model_validate(s.model_dump()) for s in suppliers]
    except Exception as e:
        raise handle_service_error(e, "suppliers needing review retrieval")


@router.get("/name/{name}", response_model=SupplierRead, summary="Get supplier by name")
async def get_supplier_by_name(
    name: str = Path(..., description="Supplier name"),
    service: SupplierServiceDep = None
):
    """Get supplier by name."""
    try:
        supplier = service.get_supplier_by_name(name)
        if not supplier:
            raise HTTPException(status_code=404, detail=f"Supplier with name '{name}' not found")
        return SupplierRead.model_validate(supplier.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        raise handle_service_error(e, "supplier retrieval")


@router.get("/{supplier_id}", response_model=SupplierRead, summary="Get supplier by ID")
async def get_supplier(
    supplier_id: int = Path(..., description="Supplier ID"),
    service: SupplierServiceDep = None
):
    """Get supplier by ID."""
    try:
        supplier = service.get_supplier(supplier_id)
        if not supplier:
            raise HTTPException(status_code=404, detail=f"Supplier with ID {supplier_id} not found")
        return SupplierRead.model_validate(supplier.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        raise handle_service_error(e, "supplier retrieval")


@router.put("/{supplier_id}", response_model=SupplierRead, summary="Update supplier")
async def update_supplier(
    supplier_data: SupplierUpdate,
    supplier_id: int = Path(..., description="Supplier ID"),
    service: SupplierServiceDep = None
):
    """Update supplier."""
    try:
        supplier = service.update_supplier(supplier_id, supplier_data)
        if not supplier:
            raise HTTPException(status_code=404, detail=f"Supplier with ID {supplier_id} not found")
        return SupplierRead.model_validate(supplier.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        raise handle_service_error(e, "supplier update")


@router.delete("/{supplier_id}", summary="Delete supplier")
async def delete_supplier(
    supplier_id: int = Path(..., description="Supplier ID"),
    service: SupplierServiceDep = None
):
    """Deactivate supplier (soft delete)."""
    try:
        success = service.delete_supplier(supplier_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Supplier with ID {supplier_id} not found")
        return {"message": "Supplier deactivated successfully", "supplier_id": supplier_id}
    except HTTPException:
        raise
    except Exception as e:
        raise handle_service_error(e, "supplier deletion")


@router.delete("/{supplier_id}/permanent", summary="Delete supplier permanently")
async def delete_supplier_permanently(
    supplier_id: int = Path(..., description="Supplier ID"),
    service: SupplierServiceDep = None
):
    """Permanently delete supplier (hard delete). Only allowed if no products or transactions exist."""
    try:
        success = service.delete_supplier_permanently(supplier_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Supplier with ID {supplier_id} not found")
        return {"message": "Supplier permanently deleted", "supplier_id": supplier_id}
    except HTTPException:
        raise
    except ValueError as e:
        # Business rule violation (has products/transactions)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise handle_service_error(e, "permanent supplier deletion")


@router.get("/{supplier_id}/products", summary="Get supplier products")
async def get_supplier_products(
    supplier_id: int = Path(..., description="Supplier ID"),
    active_only: bool = Query(True, description="Only return active products"),
    service: SupplierServiceDep = None
):
    """Get all products from a supplier."""
    try:
        if active_only:
            products = service.get_supplier_active_products(supplier_id)
        else:
            products = service.get_supplier_products(supplier_id)
        
        from ..data.models import ProductRead
        return [ProductRead.model_validate(p.model_dump()) for p in products]
    except Exception as e:
        raise handle_service_error(e, "supplier products retrieval")


@router.get("/{supplier_id}/performance", summary="Get supplier performance")
async def get_supplier_performance(
    supplier_id: int = Path(..., description="Supplier ID"),
    service: SupplierServiceDep = None
):
    """Get detailed performance metrics for a supplier."""
    try:
        supplier = service.get_supplier(supplier_id)
        if not supplier:
            raise HTTPException(status_code=404, detail=f"Supplier with ID {supplier_id} not found")
        
        performance_metrics = service.calculate_supplier_performance(supplier_id)
        
        # Include supplier's current performance rating
        performance_metrics["performance_rating"] = supplier.performance_rating
        
        return performance_metrics
    except HTTPException:
        raise
    except Exception as e:
        raise handle_service_error(e, "supplier performance calculation")


@router.put("/{supplier_id}/performance", summary="Update supplier performance rating")
async def update_supplier_performance(
    supplier_id: int = Path(..., description="Supplier ID"),
    new_rating: float = Query(..., ge=0.0, le=5.0, description="New performance rating"),
    service: SupplierServiceDep = None
):
    """Update supplier's performance rating."""
    try:
        # Update the supplier's performance rating
        supplier = service.get_supplier(supplier_id)
        if not supplier:
            raise HTTPException(status_code=404, detail=f"Supplier with ID {supplier_id} not found")
        
        # Update the rating
        update_data = SupplierUpdate(performance_rating=new_rating)
        updated_supplier = service.update_supplier(supplier_id, update_data)
        
        return {
            "message": "Performance rating updated successfully",
            "supplier_id": supplier_id,
            "new_rating": updated_supplier.performance_rating
        }
    except HTTPException:
        raise
    except Exception as e:
        raise handle_service_error(e, "supplier performance rating update")