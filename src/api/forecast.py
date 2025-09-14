"""
Demand forecasting API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import logging

from src.services.forecasting import ForecastingService
from src.services.inventory import InventoryService
from src.data.database import get_database

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/forecast", tags=["forecasting"])

# Pydantic models for API
class ForecastRequest(BaseModel):
    sku: str = Field(..., description="Product SKU to forecast")
    horizon_days: int = Field(default=7, ge=1, le=365, description="Forecast horizon in days")
    method: str = Field(default="auto", description="Forecast method: auto, moving_average, exponential_smoothing, trend_analysis")

class ForecastResponse(BaseModel):
    product_id: int
    sku: str
    forecast_method: str
    horizon_days: int
    total_forecast: float
    daily_average: float
    forecast_series: Optional[List[float]] = None
    parameters: Dict[str, Any]
    data_points: int
    confidence_intervals: Optional[Dict[str, float]] = None

class SeasonalAnalysisResponse(BaseModel):
    product_id: int
    sku: str
    seasonal_detected: bool
    day_of_week_pattern: Dict[str, float]
    coefficient_of_variation: float
    data_points: int
    reason: Optional[str] = None

# Dependencies
def get_forecasting_service() -> ForecastingService:
    return ForecastingService(get_database())

def get_inventory_service() -> InventoryService:
    return InventoryService(get_database())

@router.post("/", response_model=ForecastResponse)
async def generate_forecast(
    request: ForecastRequest,
    forecasting_service: ForecastingService = Depends(get_forecasting_service),
    inventory_service: InventoryService = Depends(get_inventory_service)
):
    """Generate demand forecast for a product"""
    try:
        # Get product by SKU
        product = inventory_service.get_product_by_sku(request.sku)
        if not product:
            raise HTTPException(status_code=404, detail=f"Product with SKU '{request.sku}' not found")
        
        # Validate method
        valid_methods = ["auto", "moving_average", "exponential_smoothing", "trend_analysis"]
        if request.method not in valid_methods:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid forecast method. Must be one of: {', '.join(valid_methods)}"
            )
        
        # Generate forecast
        forecast_result = forecasting_service.generate_forecast(
            product_id=product.id,
            horizon=request.horizon_days,
            method=request.method
        )
        
        if "error" in forecast_result:
            raise HTTPException(status_code=400, detail=forecast_result["error"])
        
        # Save forecast result to database
        forecasting_service.save_forecast_result(forecast_result)
        
        return ForecastResponse(
            product_id=forecast_result["product_id"],
            sku=request.sku,
            forecast_method=forecast_result["forecast_method"],
            horizon_days=forecast_result["horizon_days"],
            total_forecast=forecast_result["total_forecast"],
            daily_average=forecast_result["daily_average"],
            forecast_series=forecast_result.get("forecast_series"),
            parameters=forecast_result.get("parameters", {}),
            data_points=forecast_result["data_points"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating forecast: {e}")
        raise HTTPException(status_code=500, detail=f"Forecast generation failed: {str(e)}")

@router.get("/{sku}")
async def get_forecast_by_sku(
    sku: str,
    horizon_days: int = Query(7, ge=1, le=365, description="Forecast horizon in days"),
    method: str = Query("auto", description="Forecast method"),
    forecasting_service: ForecastingService = Depends(get_forecasting_service),
    inventory_service: InventoryService = Depends(get_inventory_service)
):
    """Get forecast for a specific product by SKU"""
    try:
        # Create request and call generate_forecast
        request = ForecastRequest(sku=sku, horizon_days=horizon_days, method=method)
        return await generate_forecast(request, forecasting_service, inventory_service)
        
    except Exception as e:
        logger.error(f"Error getting forecast for SKU {sku}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{sku}/accuracy")
async def get_forecast_accuracy(
    sku: str,
    days: int = Query(30, ge=1, le=365, description="Number of days for accuracy calculation"),
    forecasting_service: ForecastingService = Depends(get_forecasting_service),
    inventory_service: InventoryService = Depends(get_inventory_service)
):
    """Get forecast accuracy metrics for a product"""
    try:
        # Get product by SKU
        product = inventory_service.get_product_by_sku(sku)
        if not product:
            raise HTTPException(status_code=404, detail=f"Product with SKU '{sku}' not found")
        
        # Get accuracy metrics
        accuracy_result = forecasting_service.get_forecast_accuracy(product.id, days)
        
        if "error" in accuracy_result:
            raise HTTPException(status_code=404, detail=accuracy_result["error"])
        
        return {
            "sku": sku,
            **accuracy_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting forecast accuracy for SKU {sku}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{sku}/seasonal")
async def get_seasonal_analysis(
    sku: str,
    forecasting_service: ForecastingService = Depends(get_forecasting_service),
    inventory_service: InventoryService = Depends(get_inventory_service)
):
    """Get seasonal pattern analysis for a product"""
    try:
        # Get product by SKU
        product = inventory_service.get_product_by_sku(sku)
        if not product:
            raise HTTPException(status_code=404, detail=f"Product with SKU '{sku}' not found")
        
        # Get seasonal analysis
        seasonal_result = forecasting_service.get_seasonal_patterns(product.id)
        
        if "error" in seasonal_result:
            raise HTTPException(status_code=400, detail=seasonal_result["error"])
        
        return SeasonalAnalysisResponse(
            product_id=seasonal_result["product_id"],
            sku=sku,
            seasonal_detected=seasonal_result["seasonal_detected"],
            day_of_week_pattern=seasonal_result["day_of_week_pattern"],
            coefficient_of_variation=seasonal_result["coefficient_of_variation"],
            data_points=seasonal_result["data_points"],
            reason=seasonal_result.get("reason")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting seasonal analysis for SKU {sku}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{sku}/historical-demand")
async def get_historical_demand(
    sku: str,
    days: int = Query(90, ge=1, le=365, description="Number of days of historical data"),
    forecasting_service: ForecastingService = Depends(get_forecasting_service),
    inventory_service: InventoryService = Depends(get_inventory_service)
):
    """Get historical demand data for a product"""
    try:
        # Get product by SKU
        product = inventory_service.get_product_by_sku(sku)
        if not product:
            raise HTTPException(status_code=404, detail=f"Product with SKU '{sku}' not found")
        
        # Get historical demand
        demand_df = forecasting_service.get_historical_demand(product.id, days)
        
        if demand_df.empty:
            return {
                "sku": sku,
                "message": "No historical demand data found",
                "data_points": 0,
                "demand_data": []
            }
        
        # Convert to list of dictionaries
        demand_data = []
        for _, row in demand_df.iterrows():
            demand_data.append({
                "date": row['date'].isoformat(),
                "demand": float(row['demand'])
            })
        
        # Calculate summary statistics
        total_demand = demand_df['demand'].sum()
        avg_daily_demand = demand_df['demand'].mean()
        max_demand = demand_df['demand'].max()
        min_demand = demand_df['demand'].min()
        
        return {
            "sku": sku,
            "period_days": days,
            "data_points": len(demand_data),
            "summary": {
                "total_demand": float(total_demand),
                "average_daily_demand": float(avg_daily_demand),
                "max_daily_demand": float(max_demand),
                "min_daily_demand": float(min_demand)
            },
            "demand_data": demand_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting historical demand for SKU {sku}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bulk")
async def generate_bulk_forecasts(
    skus: List[str] = Query(..., description="List of product SKUs"),
    horizon_days: int = Query(7, ge=1, le=365, description="Forecast horizon in days"),
    method: str = Query("auto", description="Forecast method"),
    forecasting_service: ForecastingService = Depends(get_forecasting_service),
    inventory_service: InventoryService = Depends(get_inventory_service)
):
    """Generate forecasts for multiple products"""
    try:
        if len(skus) > 50:
            raise HTTPException(status_code=400, detail="Maximum 50 SKUs allowed per bulk request")
        
        results = []
        errors = []
        
        for sku in skus:
            try:
                # Get product
                product = inventory_service.get_product_by_sku(sku)
                if not product:
                    errors.append(f"Product with SKU '{sku}' not found")
                    continue
                
                # Generate forecast
                forecast_result = forecasting_service.generate_forecast(
                    product_id=product.id,
                    horizon=horizon_days,
                    method=method
                )
                
                if "error" in forecast_result:
                    errors.append(f"SKU {sku}: {forecast_result['error']}")
                    continue
                
                # Save forecast result
                forecasting_service.save_forecast_result(forecast_result)
                
                results.append({
                    "sku": sku,
                    "forecast_method": forecast_result["forecast_method"],
                    "total_forecast": forecast_result["total_forecast"],
                    "daily_average": forecast_result["daily_average"],
                    "data_points": forecast_result["data_points"]
                })
                
            except Exception as e:
                errors.append(f"SKU {sku}: {str(e)}")
        
        return {
            "successful_forecasts": len(results),
            "failed_forecasts": len(errors),
            "results": results,
            "errors": errors if errors else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating bulk forecasts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/methods/available")
async def get_available_methods():
    """Get list of available forecasting methods"""
    return {
        "methods": [
            {
                "method": "auto",
                "description": "Automatically select the best method based on data characteristics",
                "recommended": True
            },
            {
                "method": "moving_average",
                "description": "Simple moving average forecast",
                "min_data_points": 7,
                "best_for": "Stable demand patterns"
            },
            {
                "method": "exponential_smoothing",
                "description": "Exponential smoothing with trend detection",
                "min_data_points": 14,
                "best_for": "Data with trends and seasonality"
            },
            {
                "method": "trend_analysis",
                "description": "Linear trend analysis",
                "min_data_points": 10,
                "best_for": "Data with clear linear trends"
            }
        ]
    }
