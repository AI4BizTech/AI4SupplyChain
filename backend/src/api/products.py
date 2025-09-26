"""
Product management API endpoints.
"""
from fastapi import APIRouter, HTTPException, Query, Path
from typing import List, Optional

from ..data.models import (
    Product, ProductCreate, ProductUpdate, ProductRead, 
    ProductWithSupplier
)
from .dependencies import (
    InventoryServiceDep, SkipLimitDep, handle_service_error
)

router = APIRouter()


@router.post("/", response_model=ProductRead, summary="Create product")
async def create_product(
    product_data: ProductCreate,
    service: InventoryServiceDep
):
    """Create a new product."""
    try:
        product = service.create_product(product_data)
        return ProductRead.model_validate(product.model_dump())
    except Exception as e:
        raise handle_service_error(e, "product creation")


@router.get("/", response_model=List[ProductRead], summary="List products")
async def list_products(
    skip_limit: SkipLimitDep,
    category: Optional[str] = Query(None, description="Filter by category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    supplier_id: Optional[int] = Query(None, description="Filter by supplier"),
    service: InventoryServiceDep = None
):
    """List products with optional filtering."""
    try:
        skip, limit = skip_limit
        products = service.list_products(
            skip=skip,
            limit=limit,
            category=category,
            is_active=is_active,
            supplier_id=supplier_id
        )
        return [ProductRead.model_validate(p.model_dump()) for p in products]
    except Exception as e:
        raise handle_service_error(e, "product listing")


@router.get("/categories", response_model=List[str], summary="Get product categories")
async def get_product_categories(service: InventoryServiceDep):
    """Get list of distinct product categories."""
    try:
        return service.get_product_categories()
    except Exception as e:
        raise handle_service_error(e, "categories retrieval")


@router.get("/low-stock", response_model=List[ProductRead], summary="Get low stock products")
async def get_low_stock_products(service: InventoryServiceDep):
    """Get products with stock levels below reorder point."""
    try:
        products = service.get_low_stock_products()
        return [ProductRead.model_validate(p.model_dump()) for p in products]
    except Exception as e:
        raise handle_service_error(e, "low stock products retrieval")


@router.get("/sku/{sku}", response_model=ProductRead, summary="Get product by SKU")
async def get_product_by_sku(
    sku: str = Path(..., description="Product SKU"),
    service: InventoryServiceDep = None
):
    """Get product by SKU."""
    try:
        product = service.get_product_by_sku(sku)
        if not product:
            raise HTTPException(status_code=404, detail=f"Product with SKU '{sku}' not found")
        return ProductRead.model_validate(product.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        raise handle_service_error(e, "product retrieval")


@router.get("/{product_id}", response_model=ProductRead, summary="Get product by ID")
async def get_product(
    product_id: int = Path(..., description="Product ID"),
    service: InventoryServiceDep = None
):
    """Get product by ID."""
    try:
        product = service.get_product(product_id)
        if not product:
            raise HTTPException(status_code=404, detail=f"Product with ID {product_id} not found")
        return ProductRead.model_validate(product.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        raise handle_service_error(e, "product retrieval")


@router.put("/{product_id}", response_model=ProductRead, summary="Update product")
async def update_product(
    product_data: ProductUpdate,
    product_id: int = Path(..., description="Product ID"),
    service: InventoryServiceDep = None
):
    """Update product."""
    try:
        product = service.update_product(product_id, product_data)
        if not product:
            raise HTTPException(status_code=404, detail=f"Product with ID {product_id} not found")
        return ProductRead.model_validate(product.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        raise handle_service_error(e, "product update")


@router.delete("/{product_id}", summary="Delete product")
async def delete_product(
    product_id: int = Path(..., description="Product ID"),
    service: InventoryServiceDep = None
):
    """Deactivate product (soft delete)."""
    try:
        success = service.delete_product(product_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Product with ID {product_id} not found")
        return {"message": "Product deactivated successfully", "product_id": product_id}
    except HTTPException:
        raise
    except Exception as e:
        raise handle_service_error(e, "product deletion")


@router.delete("/{product_id}/permanent", summary="Delete product permanently")
async def delete_product_permanently(
    product_id: int = Path(..., description="Product ID"),
    service: InventoryServiceDep = None
):
    """Permanently delete product (hard delete). Only allowed if no transactions or inventory exist."""
    try:
        success = service.delete_product_permanently(product_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Product with ID {product_id} not found")
        return {"message": "Product permanently deleted", "product_id": product_id}
    except HTTPException:
        raise
    except ValueError as e:
        # Business rule violation (has transactions/inventory)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise handle_service_error(e, "permanent product deletion")


@router.get("/{product_id}/inventory", summary="Get product inventory")
async def get_product_inventory(
    product_id: int = Path(..., description="Product ID"),
    service: InventoryServiceDep = None
):
    """Get inventory levels for a product across all locations."""
    try:
        # First check if product exists
        product = service.get_product(product_id)
        if not product:
            raise HTTPException(status_code=404, detail=f"Product with ID {product_id} not found")
        
        inventory_records = service.get_inventory(product_id=product_id)
        
        total_on_hand = sum(inv.quantity_on_hand for inv in inventory_records)
        total_reserved = sum(inv.reserved_quantity for inv in inventory_records)
        total_available = service.get_total_available_quantity(product_id)
        
        return {
            "product_id": product_id,
            "sku": product.sku,
            "name": product.name,
            "reorder_point": product.reorder_point,
            "reorder_quantity": product.reorder_quantity,
            "total_on_hand": total_on_hand,
            "total_reserved": total_reserved,
            "total_available": total_available,
            "needs_reorder": total_available <= product.reorder_point,
            "locations": [
                {
                    "location_id": inv.location_id,
                    "quantity_on_hand": inv.quantity_on_hand,
                    "reserved_quantity": inv.reserved_quantity,
                    "available_quantity": max(0, inv.quantity_on_hand - inv.reserved_quantity),
                    "last_updated": inv.last_updated
                }
                for inv in inventory_records
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise handle_service_error(e, "product inventory retrieval")