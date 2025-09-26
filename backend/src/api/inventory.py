"""
Inventory management API endpoints.
"""
from fastapi import APIRouter, HTTPException, Query, Path
from typing import List, Optional

from ..data.models import InventoryRead, InventoryUpdate
from .dependencies import (
    InventoryServiceDep, handle_service_error
)

router = APIRouter()


@router.get("/", response_model=List[dict], summary="Get inventory levels")
async def get_inventory(
    product_id: Optional[int] = Query(None, description="Filter by product ID"),
    location_id: Optional[int] = Query(None, description="Filter by location ID"),
    service: InventoryServiceDep = None
):
    """Get inventory levels with optional filtering."""
    try:
        inventory_records = service.get_inventory(
            product_id=product_id,
            location_id=location_id
        )
        
        return [
            {
                "id": inv.id,
                "product_id": inv.product_id,
                "location_id": inv.location_id,
                "quantity_on_hand": inv.quantity_on_hand,
                "reserved_quantity": inv.reserved_quantity,
                "available_quantity": max(0, inv.quantity_on_hand - inv.reserved_quantity),
                "last_updated": inv.last_updated
            }
            for inv in inventory_records
        ]
    except Exception as e:
        raise handle_service_error(e, "inventory retrieval")


@router.get("/location/{location_id}", response_model=List[dict], summary="Get location inventory")
async def get_location_inventory(
    location_id: int = Path(..., description="Location ID"),
    service: InventoryServiceDep = None
):
    """Get all inventory for a specific location."""
    try:
        inventory_records = service.get_inventory(location_id=location_id)
        
        result = []
        for inv in inventory_records:
            product = service.get_product(inv.product_id)
            if product:
                result.append({
                    "id": inv.id,
                    "product_id": inv.product_id,
                    "product_sku": product.sku,
                    "product_name": product.name,
                    "location_id": inv.location_id,
                    "quantity_on_hand": inv.quantity_on_hand,
                    "reserved_quantity": inv.reserved_quantity,
                    "available_quantity": max(0, inv.quantity_on_hand - inv.reserved_quantity),
                    "unit_cost": float(product.unit_cost),
                    "total_value": float(product.unit_cost * inv.quantity_on_hand),
                    "last_updated": inv.last_updated
                })
        
        return result
    except Exception as e:
        raise handle_service_error(e, "location inventory retrieval")


@router.get("/alerts/low-stock", response_model=List[dict], summary="Get low stock alerts")
async def get_low_stock_alerts(service: InventoryServiceDep = None):
    """Get products that need reordering."""
    try:
        low_stock_products = service.get_low_stock_products()
        
        alerts = []
        for product in low_stock_products:
            total_available = service.get_total_available_quantity(product.id)
            inventory_records = service.get_inventory(product_id=product.id)
            
            alerts.append({
                "product_id": product.id,
                "sku": product.sku,
                "name": product.name,
                "category": product.category,
                "reorder_point": product.reorder_point,
                "reorder_quantity": product.reorder_quantity,
                "current_available": total_available,
                "shortage": max(0, product.reorder_point - total_available),
                "supplier_id": product.supplier_id,
                "locations": [
                    {
                        "location_id": inv.location_id,
                        "available": max(0, inv.quantity_on_hand - inv.reserved_quantity)
                    }
                    for inv in inventory_records
                ]
            })
        
        return alerts
    except Exception as e:
        raise handle_service_error(e, "low stock alerts retrieval")


@router.get("/summary", summary="Get inventory summary")
async def get_inventory_summary(service: InventoryServiceDep = None):
    """Get overall inventory summary statistics."""
    try:
        all_inventory = service.get_inventory()
        
        total_products_with_stock = len(set(inv.product_id for inv in all_inventory if inv.quantity_on_hand > 0))
        total_quantity = sum(inv.quantity_on_hand for inv in all_inventory)
        total_reserved = sum(inv.reserved_quantity for inv in all_inventory)
        total_available = sum(max(0, inv.quantity_on_hand - inv.reserved_quantity) for inv in all_inventory)
        
        # Calculate total value (need product costs)
        total_value = 0
        for inv in all_inventory:
            product = service.get_product(inv.product_id)
            if product and inv.quantity_on_hand > 0:
                total_value += float(product.unit_cost * inv.quantity_on_hand)
        
        low_stock_count = len(service.get_low_stock_products())
        
        return {
            "total_products_with_stock": total_products_with_stock,
            "total_quantity_on_hand": total_quantity,
            "total_reserved_quantity": total_reserved,
            "total_available_quantity": total_available,
            "total_inventory_value": total_value,
            "low_stock_products": low_stock_count,
            "inventory_turnover_ratio": None,  # Would need historical data
        }
    except Exception as e:
        raise handle_service_error(e, "inventory summary retrieval")


@router.put("/{product_id}/{location_id}", response_model=dict, summary="Update inventory")
async def update_inventory(
    inventory_data: InventoryUpdate,
    product_id: int = Path(..., description="Product ID"),
    location_id: int = Path(..., description="Location ID"),
    service: InventoryServiceDep = None
):
    """Update inventory quantities for a product at a location."""
    try:
        inventory = service.update_inventory(product_id, location_id, inventory_data)
        if not inventory:
            raise HTTPException(
                status_code=404, 
                detail=f"Inventory not found for product {product_id} at location {location_id}"
            )
        
        return {
            "id": inventory.id,
            "product_id": inventory.product_id,
            "location_id": inventory.location_id,
            "quantity_on_hand": inventory.quantity_on_hand,
            "reserved_quantity": inventory.reserved_quantity,
            "available_quantity": max(0, inventory.quantity_on_hand - inventory.reserved_quantity),
            "last_updated": inventory.last_updated
        }
    except HTTPException:
        raise
    except Exception as e:
        raise handle_service_error(e, "inventory update")


@router.get("/{product_id}/{location_id}", response_model=dict, summary="Get specific inventory")
async def get_specific_inventory(
    product_id: int = Path(..., description="Product ID"),
    location_id: int = Path(..., description="Location ID"),
    service: InventoryServiceDep = None
):
    """Get inventory for a specific product at a specific location."""
    try:
        inventory = service.get_inventory_by_product_location(product_id, location_id)
        if not inventory:
            raise HTTPException(
                status_code=404,
                detail=f"Inventory not found for product {product_id} at location {location_id}"
            )
        
        product = service.get_product(product_id)
        
        return {
            "id": inventory.id,
            "product_id": inventory.product_id,
            "product_sku": product.sku if product else None,
            "product_name": product.name if product else None,
            "location_id": inventory.location_id,
            "quantity_on_hand": inventory.quantity_on_hand,
            "reserved_quantity": inventory.reserved_quantity,
            "available_quantity": max(0, inventory.quantity_on_hand - inventory.reserved_quantity),
            "last_updated": inventory.last_updated
        }
    except HTTPException:
        raise
    except Exception as e:
        raise handle_service_error(e, "specific inventory retrieval")


@router.post("/{product_id}/{location_id}/reserve", summary="Reserve inventory")
async def reserve_inventory(
    quantity: int = Query(..., ge=1, description="Quantity to reserve"),
    product_id: int = Path(..., description="Product ID"),
    location_id: int = Path(..., description="Location ID"),
    service: InventoryServiceDep = None
):
    """Reserve inventory quantity."""
    try:
        success = service.reserve_inventory(product_id, location_id, quantity)
        if not success:
            available = service.get_available_quantity(product_id, location_id)
            raise HTTPException(
                status_code=400,
                detail=f"Cannot reserve {quantity} units. Available: {available}"
            )
        
        return {
            "message": f"Successfully reserved {quantity} units",
            "product_id": product_id,
            "location_id": location_id,
            "reserved_quantity": quantity
        }
    except HTTPException:
        raise
    except Exception as e:
        raise handle_service_error(e, "inventory reservation")


@router.post("/{product_id}/{location_id}/release", summary="Release reservation")
async def release_reservation(
    quantity: int = Query(..., ge=1, description="Quantity to release"),
    product_id: int = Path(..., description="Product ID"),
    location_id: int = Path(..., description="Location ID"),
    service: InventoryServiceDep = None
):
    """Release reserved inventory."""
    try:
        success = service.release_reservation(product_id, location_id, quantity)
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"No inventory reservation found for product {product_id} at location {location_id}"
            )
        
        return {
            "message": f"Successfully released {quantity} reserved units",
            "product_id": product_id,
            "location_id": location_id,
            "released_quantity": quantity
        }
    except HTTPException:
        raise
    except Exception as e:
        raise handle_service_error(e, "reservation release")