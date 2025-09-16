"""
Supplier management API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import logging

from src.services.suppliers import SupplierService
from src.data.database import get_database

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/suppliers", tags=["suppliers"])

# Pydantic models for API
class SupplierCreate(BaseModel):
    supplier_id: str = Field(..., description="Unique supplier identifier")
    name: str = Field(..., description="Supplier name")
    contact_info: Optional[Dict[str, Any]] = Field(default={}, description="Contact information")
    lead_time_days: int = Field(default=7, ge=1, description="Lead time in days")
    payment_terms: Optional[str] = Field(None, description="Payment terms")
    minimum_order_qty: int = Field(default=1, ge=1, description="Minimum order quantity")
    performance_rating: Optional[float] = Field(None, ge=0.0, le=5.0, description="Performance rating")

class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_info: Optional[Dict[str, Any]] = None
    lead_time_days: Optional[int] = Field(None, ge=1)
    payment_terms: Optional[str] = None
    minimum_order_qty: Optional[int] = Field(None, ge=1)
    performance_rating: Optional[float] = Field(None, ge=0.0, le=5.0)

class SupplierResponse(BaseModel):
    id: int
    supplier_id: str
    name: str
    contact_info: Optional[Dict[str, Any]]
    lead_time_days: int
    payment_terms: Optional[str]
    minimum_order_qty: int
    performance_rating: Optional[float]
    created_at: str
    updated_at: str

# Dependency to get supplier service
def get_supplier_service() -> SupplierService:
    return SupplierService(get_database())

@router.post("/", response_model=Dict[str, Any])
async def create_supplier(
    supplier: SupplierCreate,
    service: SupplierService = Depends(get_supplier_service)
):
    """Create a new supplier"""
    try:
        created_supplier = service.create_supplier(supplier.dict())
        return {
            "success": True,
            "supplier": {
                "id": created_supplier.id,
                "supplier_id": created_supplier.supplier_id,
                "name": created_supplier.name,
                "lead_time_days": created_supplier.lead_time_days,
                "performance_rating": float(created_supplier.performance_rating or 0.0)
            }
        }
    except Exception as e:
        logger.error(f"Error creating supplier: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{supplier_id}")
async def get_supplier(
    supplier_id: str,
    service: SupplierService = Depends(get_supplier_service)
):
    """Get supplier by supplier_id"""
    supplier = service.get_supplier_by_id(supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    return {
        "id": supplier.id,
        "supplier_id": supplier.supplier_id,
        "name": supplier.name,
        "contact_info": supplier.contact_info,
        "lead_time_days": supplier.lead_time_days,
        "payment_terms": supplier.payment_terms,
        "minimum_order_qty": supplier.minimum_order_qty,
        "performance_rating": float(supplier.performance_rating or 0.0),
        "created_at": supplier.created_at.isoformat(),
        "updated_at": supplier.updated_at.isoformat()
    }

@router.get("/")
async def list_suppliers(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of suppliers to return"),
    service: SupplierService = Depends(get_supplier_service)
):
    """List all suppliers with summary information"""
    try:
        suppliers_summary = service.get_suppliers_summary()
        
        # Apply limit
        limited_suppliers = suppliers_summary[:limit]
        
        return {
            "suppliers": limited_suppliers,
            "count": len(limited_suppliers),
            "total_available": len(suppliers_summary)
        }
    except Exception as e:
        logger.error(f"Error listing suppliers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{supplier_id}")
async def update_supplier(
    supplier_id: str,
    updates: SupplierUpdate,
    service: SupplierService = Depends(get_supplier_service)
):
    """Update supplier information"""
    try:
        # Get supplier first to get internal ID
        supplier = service.get_supplier_by_id(supplier_id)
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        # Filter out None values
        update_data = {k: v for k, v in updates.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid updates provided")
        
        updated_supplier = service.update_supplier(supplier.id, update_data)
        if not updated_supplier:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        return {
            "success": True,
            "supplier": {
                "id": updated_supplier.id,
                "supplier_id": updated_supplier.supplier_id,
                "name": updated_supplier.name,
                "lead_time_days": updated_supplier.lead_time_days,
                "performance_rating": float(updated_supplier.performance_rating or 0.0),
                "updated_at": updated_supplier.updated_at.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating supplier: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{supplier_id}/products")
async def get_supplier_products(
    supplier_id: str,
    service: SupplierService = Depends(get_supplier_service)
):
    """Get all products from a specific supplier"""
    try:
        products = service.get_supplier_products(supplier_id)
        
        if not products:
            # Check if supplier exists
            supplier = service.get_supplier_by_id(supplier_id)
            if not supplier:
                raise HTTPException(status_code=404, detail="Supplier not found")
        
        return {
            "supplier_id": supplier_id,
            "products": products,
            "count": len(products)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting supplier products: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{supplier_id}/performance")
async def get_supplier_performance(
    supplier_id: str,
    days: int = Query(90, ge=1, le=365, description="Number of days for performance calculation"),
    service: SupplierService = Depends(get_supplier_service)
):
    """Get supplier performance metrics"""
    try:
        performance = service.get_supplier_performance(supplier_id, days)
        
        if not performance:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        return performance
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting supplier performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{supplier_id}/rating")
async def update_supplier_rating(
    supplier_id: str,
    rating: float = Query(..., ge=0.0, le=5.0, description="Performance rating (0.0 to 5.0)"),
    service: SupplierService = Depends(get_supplier_service)
):
    """Update supplier performance rating"""
    try:
        success = service.update_performance_rating(supplier_id, rating)
        
        if not success:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        return {
            "success": True,
            "message": f"Updated rating for supplier {supplier_id} to {rating}",
            "supplier_id": supplier_id,
            "new_rating": rating
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating supplier rating: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{supplier_id}/summary")
async def get_supplier_summary(
    supplier_id: str,
    service: SupplierService = Depends(get_supplier_service)
):
    """Get comprehensive supplier summary including performance and products"""
    try:
        # Get basic supplier info
        supplier = service.get_supplier_by_id(supplier_id)
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        # Get performance metrics
        performance = service.get_supplier_performance(supplier_id)
        
        # Get products
        products = service.get_supplier_products(supplier_id)
        
        return {
            "supplier": {
                "id": supplier.id,
                "supplier_id": supplier.supplier_id,
                "name": supplier.name,
                "contact_info": supplier.contact_info,
                "lead_time_days": supplier.lead_time_days,
                "payment_terms": supplier.payment_terms,
                "minimum_order_qty": supplier.minimum_order_qty,
                "performance_rating": float(supplier.performance_rating or 0.0)
            },
            "performance": performance,
            "products": {
                "items": products,
                "count": len(products)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting supplier summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
