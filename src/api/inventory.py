"""
Inventory management API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import logging

from src.services.inventory import InventoryService
from src.data.database import get_database

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inventory", tags=["inventory"])

# Pydantic models for API
class ProductCreate(BaseModel):
    sku: str = Field(..., description="Product SKU")
    name: str = Field(..., description="Product name")
    description: Optional[str] = None
    category: str = Field(..., description="Product category")
    unit_cost: float = Field(..., gt=0, description="Unit cost")
    supplier_id: Optional[int] = None
    reorder_point: int = Field(default=10, ge=0)
    reorder_quantity: int = Field(default=50, ge=1)
    weight: Optional[float] = Field(None, ge=0)
    dimensions: Optional[Dict[str, float]] = None

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    unit_cost: Optional[float] = Field(None, gt=0)
    supplier_id: Optional[int] = None
    reorder_point: Optional[int] = Field(None, ge=0)
    reorder_quantity: Optional[int] = Field(None, ge=1)
    weight: Optional[float] = Field(None, ge=0)
    dimensions: Optional[Dict[str, float]] = None

class LocationCreate(BaseModel):
    location_id: str = Field(..., description="Location ID")
    name: str = Field(..., description="Location name")
    address: Optional[str] = None
    warehouse_type: str = Field(default="store", description="Warehouse type")

class StockUpdate(BaseModel):
    quantity_change: int = Field(..., description="Quantity change (positive or negative)")
    transaction_type: str = Field(default="adjustment", description="Transaction type")

# Dependency to get inventory service
def get_inventory_service() -> InventoryService:
    return InventoryService(get_database())

@router.post("/products", response_model=Dict[str, Any])
async def create_product(
    product: ProductCreate,
    service: InventoryService = Depends(get_inventory_service)
):
    """Create a new product"""
    try:
        created_product = service.create_product(product.dict())
        return {
            "success": True,
            "product": {
                "id": created_product.id,
                "sku": created_product.sku,
                "name": created_product.name,
                "category": created_product.category,
                "unit_cost": float(created_product.unit_cost)
            }
        }
    except Exception as e:
        logger.error(f"Error creating product: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/products/{sku}")
async def get_product(
    sku: str,
    service: InventoryService = Depends(get_inventory_service)
):
    """Get product by SKU"""
    product = service.get_product_by_sku(sku)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {
        "id": product.id,
        "sku": product.sku,
        "name": product.name,
        "description": product.description,
        "category": product.category,
        "unit_cost": float(product.unit_cost),
        "supplier_id": product.supplier_id,
        "reorder_point": product.reorder_point,
        "reorder_quantity": product.reorder_quantity,
        "weight": float(product.weight) if product.weight else None,
        "dimensions": product.dimensions,
        "created_at": product.created_at.isoformat(),
        "updated_at": product.updated_at.isoformat()
    }

@router.get("/products")
async def list_products(
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of products to return"),
    service: InventoryService = Depends(get_inventory_service)
):
    """List products with optional filtering"""
    try:
        products = service.list_products(category=category, limit=limit)
        return {
            "products": [
                {
                    "id": p.id,
                    "sku": p.sku,
                    "name": p.name,
                    "category": p.category,
                    "unit_cost": float(p.unit_cost),
                    "reorder_point": p.reorder_point,
                    "reorder_quantity": p.reorder_quantity
                }
                for p in products
            ],
            "count": len(products)
        }
    except Exception as e:
        logger.error(f"Error listing products: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/products/{product_id}")
async def update_product(
    product_id: int,
    updates: ProductUpdate,
    service: InventoryService = Depends(get_inventory_service)
):
    """Update product information"""
    try:
        # Filter out None values
        update_data = {k: v for k, v in updates.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid updates provided")
        
        updated_product = service.update_product(product_id, update_data)
        if not updated_product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return {
            "success": True,
            "product": {
                "id": updated_product.id,
                "sku": updated_product.sku,
                "name": updated_product.name,
                "category": updated_product.category,
                "unit_cost": float(updated_product.unit_cost),
                "updated_at": updated_product.updated_at.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating product: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/locations", response_model=Dict[str, Any])
async def create_location(
    location: LocationCreate,
    service: InventoryService = Depends(get_inventory_service)
):
    """Create a new location"""
    try:
        created_location = service.create_location(location.dict())
        return {
            "success": True,
            "location": {
                "id": created_location.id,
                "location_id": created_location.location_id,
                "name": created_location.name,
                "warehouse_type": created_location.warehouse_type
            }
        }
    except Exception as e:
        logger.error(f"Error creating location: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/locations")
async def list_locations(
    service: InventoryService = Depends(get_inventory_service)
):
    """List all active locations"""
    try:
        locations = service.list_locations()
        return {
            "locations": [
                {
                    "id": loc.id,
                    "location_id": loc.location_id,
                    "name": loc.name,
                    "address": loc.address,
                    "warehouse_type": loc.warehouse_type
                }
                for loc in locations
            ],
            "count": len(locations)
        }
    except Exception as e:
        logger.error(f"Error listing locations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stock/{sku}")
async def get_stock_levels(
    sku: str,
    location_id: Optional[str] = Query(None, description="Filter by location ID"),
    service: InventoryService = Depends(get_inventory_service)
):
    """Get current stock levels for a product"""
    try:
        stock_levels = service.get_stock_levels(sku, location_id)
        
        if not stock_levels:
            raise HTTPException(status_code=404, detail="No stock records found for this product")
        
        return {
            "sku": sku,
            "stock_levels": stock_levels,
            "total_stock": sum(item['quantity_on_hand'] for item in stock_levels),
            "total_available": sum(item['available_quantity'] for item in stock_levels),
            "total_reserved": sum(item['reserved_quantity'] for item in stock_levels)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stock levels: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/stock/{sku}")
async def update_stock_level(
    sku: str,
    location_id: str = Query(..., description="Location ID"),
    stock_update: StockUpdate = ...,
    service: InventoryService = Depends(get_inventory_service)
):
    """Update stock level for a product at a location"""
    try:
        # Get product and location
        product = service.get_product_by_sku(sku)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        location = service.get_location_by_id(location_id)
        if not location:
            raise HTTPException(status_code=404, detail="Location not found")
        
        # Update stock
        success = service.update_stock_level(
            product.id,
            location.id,
            stock_update.quantity_change,
            stock_update.transaction_type
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update stock level")
        
        # Return updated stock levels
        updated_levels = service.get_stock_levels(sku, location_id)
        
        return {
            "success": True,
            "message": f"Stock updated for {sku} at {location_id}",
            "stock_levels": updated_levels
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating stock level: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts/low-stock")
async def get_low_stock_alerts(
    location_id: Optional[str] = Query(None, description="Filter by location ID"),
    service: InventoryService = Depends(get_inventory_service)
):
    """Get items that are below their reorder points"""
    try:
        low_stock_items = service.get_low_stock_items(location_id)
        
        return {
            "low_stock_items": low_stock_items,
            "count": len(low_stock_items),
            "critical_count": len([item for item in low_stock_items 
                                 if item['current_stock'] <= item['reorder_point'] * 0.5])
        }
    except Exception as e:
        logger.error(f"Error getting low stock alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary")
async def get_inventory_summary(
    service: InventoryService = Depends(get_inventory_service)
):
    """Get overall inventory summary statistics"""
    try:
        summary = service.get_inventory_summary()
        return summary
    except Exception as e:
        logger.error(f"Error getting inventory summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/transactions")
async def get_transaction_history(
    sku: Optional[str] = Query(None, description="Filter by product SKU"),
    location_id: Optional[str] = Query(None, description="Filter by location ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of transactions"),
    service: InventoryService = Depends(get_inventory_service)
):
    """Get transaction history with optional filters"""
    try:
        # Convert location_id to internal ID if provided
        location_pk = None
        if location_id:
            location = service.get_location_by_id(location_id)
            if location:
                location_pk = location.id
        
        # Convert SKU to product ID if provided
        product_pk = None
        if sku:
            product = service.get_product_by_sku(sku)
            if product:
                product_pk = product.id
        
        transactions = service.get_transaction_history(
            product_id=product_pk,
            location_id=location_pk,
            limit=limit
        )
        
        return {
            "transactions": transactions,
            "count": len(transactions)
        }
    except Exception as e:
        logger.error(f"Error getting transaction history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
