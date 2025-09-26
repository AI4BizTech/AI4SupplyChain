"""
Location management API endpoints.
"""
from fastapi import APIRouter, HTTPException, Query, Path
from typing import List, Optional

from ..data.models import (
    Location, LocationCreate, LocationUpdate, LocationRead
)
from .dependencies import (
    LocationServiceDep, SkipLimitDep, handle_service_error
)

router = APIRouter()


@router.post("/", response_model=LocationRead, summary="Create location")
async def create_location(
    location_data: LocationCreate,
    service: LocationServiceDep
):
    """Create a new location."""
    try:
        location = service.create_location(location_data)
        return LocationRead.model_validate(location.model_dump())
    except Exception as e:
        raise handle_service_error(e, "location creation")


@router.get("/", response_model=List[LocationRead], summary="List locations")
async def list_locations(
    skip_limit: SkipLimitDep,
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    warehouse_type: Optional[str] = Query(None, description="Filter by warehouse type"),
    service: LocationServiceDep = None
):
    """List locations with optional filtering."""
    try:
        skip, limit = skip_limit
        locations = service.list_locations(
            skip=skip,
            limit=limit,
            is_active=is_active,
            warehouse_type=warehouse_type
        )
        return [LocationRead.model_validate(l.model_dump()) for l in locations]
    except Exception as e:
        raise handle_service_error(e, "location listing")


@router.get("/statistics", summary="Get location statistics")
async def get_location_statistics(service: LocationServiceDep):
    """Get overall location statistics."""
    try:
        return service.get_location_statistics()
    except Exception as e:
        raise handle_service_error(e, "location statistics retrieval")


@router.get("/warehouse-types", response_model=List[str], summary="Get warehouse types")
async def get_warehouse_types(service: LocationServiceDep):
    """Get list of distinct warehouse types."""
    try:
        return service.get_warehouse_types()
    except Exception as e:
        raise handle_service_error(e, "warehouse types retrieval")


@router.get("/empty", response_model=List[LocationRead], summary="Get empty locations")
async def get_empty_locations(service: LocationServiceDep):
    """Get locations with no inventory."""
    try:
        locations = service.get_empty_locations()
        return [LocationRead.model_validate(l.model_dump()) for l in locations]
    except Exception as e:
        raise handle_service_error(e, "empty locations retrieval")


@router.get("/low-activity", response_model=List[LocationRead], summary="Get low activity locations")
async def get_low_activity_locations(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    min_transactions: int = Query(5, ge=0, description="Minimum transaction threshold"),
    service: LocationServiceDep = None
):
    """Get locations with low transaction activity."""
    try:
        locations = service.get_locations_with_low_activity(days, min_transactions)
        return [LocationRead.model_validate(l.model_dump()) for l in locations]
    except Exception as e:
        raise handle_service_error(e, "low activity locations retrieval")


@router.get("/name/{name}", response_model=LocationRead, summary="Get location by name")
async def get_location_by_name(
    name: str = Path(..., description="Location name"),
    service: LocationServiceDep = None
):
    """Get location by name."""
    try:
        location = service.get_location_by_name(name)
        if not location:
            raise HTTPException(status_code=404, detail=f"Location with name '{name}' not found")
        return LocationRead.model_validate(location.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        raise handle_service_error(e, "location retrieval")


@router.get("/code/{code}", response_model=LocationRead, summary="Get location by code")
async def get_location_by_code(
    code: str = Path(..., description="Location code"),
    service: LocationServiceDep = None
):
    """Get location by code."""
    try:
        location = service.get_location_by_code(code)
        if not location:
            raise HTTPException(status_code=404, detail=f"Location with code '{code}' not found")
        return LocationRead.model_validate(location.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        raise handle_service_error(e, "location retrieval")


@router.get("/{location_id}", response_model=LocationRead, summary="Get location by ID")
async def get_location(
    location_id: int = Path(..., description="Location ID"),
    service: LocationServiceDep = None
):
    """Get location by ID."""
    try:
        location = service.get_location(location_id)
        if not location:
            raise HTTPException(status_code=404, detail=f"Location with ID {location_id} not found")
        return LocationRead.model_validate(location.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        raise handle_service_error(e, "location retrieval")


@router.put("/{location_id}", response_model=LocationRead, summary="Update location")
async def update_location(
    location_data: LocationUpdate,
    location_id: int = Path(..., description="Location ID"),
    service: LocationServiceDep = None
):
    """Update location."""
    try:
        location = service.update_location(location_id, location_data)
        if not location:
            raise HTTPException(status_code=404, detail=f"Location with ID {location_id} not found")
        return LocationRead.model_validate(location.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        raise handle_service_error(e, "location update")


@router.delete("/{location_id}", summary="Delete location")
async def delete_location(
    location_id: int = Path(..., description="Location ID"),
    service: LocationServiceDep = None
):
    """Deactivate location (soft delete)."""
    try:
        success = service.delete_location(location_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Location with ID {location_id} not found")
        return {"message": "Location deactivated successfully", "location_id": location_id}
    except HTTPException:
        raise
    except Exception as e:
        raise handle_service_error(e, "location deletion")


@router.delete("/{location_id}/permanent", summary="Delete location permanently")
async def delete_location_permanently(
    location_id: int = Path(..., description="Location ID"),
    service: LocationServiceDep = None
):
    """Permanently delete location (hard delete). Only allowed if no inventory or transactions exist."""
    try:
        success = service.delete_location_permanently(location_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Location with ID {location_id} not found")
        return {"message": "Location permanently deleted", "location_id": location_id}
    except HTTPException:
        raise
    except ValueError as e:
        # Business rule violation (has inventory/transactions)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise handle_service_error(e, "permanent location deletion")


@router.get("/{location_id}/inventory", summary="Get location inventory summary")
async def get_location_inventory_summary(
    location_id: int = Path(..., description="Location ID"),
    service: LocationServiceDep = None
):
    """Get inventory summary for a location."""
    try:
        return service.get_location_inventory_summary(location_id)
    except Exception as e:
        raise handle_service_error(e, "location inventory summary retrieval")


@router.get("/{location_id}/activity", summary="Get location activity")
async def get_location_activity(
    location_id: int = Path(..., description="Location ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    service: LocationServiceDep = None
):
    """Get recent activity summary for a location."""
    try:
        return service.get_location_activity(location_id, days)
    except Exception as e:
        raise handle_service_error(e, "location activity retrieval")