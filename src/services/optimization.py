"""
Inventory optimization service
"""

import math
import numpy as np
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
import logging

from src.data.database import get_database
from src.data.inventory import Product, Supplier, Inventory
from src.services.forecasting import ForecastingService

logger = logging.getLogger(__name__)

class OptimizationService:
    """Service for inventory optimization calculations"""
    
    def __init__(self, db=None):
        self.db = db or get_database()
        self.forecasting_service = ForecastingService(db)
    
    def calculate_eoq(self, product_id: int, annual_demand: Optional[float] = None,
                     ordering_cost: float = 50.0, holding_cost_rate: float = 0.25) -> Dict[str, Any]:
        """
        Calculate Economic Order Quantity (EOQ)
        
        Args:
            product_id: Product ID
            annual_demand: Annual demand (if None, will estimate from historical data)
            ordering_cost: Cost per order (default $50)
            holding_cost_rate: Annual holding cost as percentage of item cost (default 25%)
        """
        try:
            with self.db.session() as session:
                product = session.query(Product).filter(Product.id == product_id).first()
                if not product:
                    return {"error": "Product not found"}
                
                # Estimate annual demand if not provided
                if annual_demand is None:
                    # Get 90-day forecast and extrapolate
                    forecast_result = self.forecasting_service.generate_forecast(product_id, horizon=90)
                    if "error" in forecast_result:
                        return {"error": f"Cannot estimate demand: {forecast_result['error']}"}
                    
                    # Extrapolate to annual demand
                    annual_demand = (forecast_result["total_forecast"] / 90) * 365
                
                if annual_demand <= 0:
                    return {"error": "Annual demand must be positive"}
                
                # Calculate holding cost per unit per year
                unit_cost = float(product.unit_cost)
                holding_cost_per_unit = unit_cost * holding_cost_rate
                
                # EOQ formula: sqrt((2 * D * S) / H)
                # Where D = annual demand, S = ordering cost, H = holding cost per unit
                eoq = math.sqrt((2 * annual_demand * ordering_cost) / holding_cost_per_unit)
                
                # Calculate related metrics
                number_of_orders = annual_demand / eoq
                time_between_orders = 365 / number_of_orders
                total_annual_cost = (annual_demand / eoq) * ordering_cost + (eoq / 2) * holding_cost_per_unit
                
                return {
                    "product_id": product_id,
                    "sku": product.sku,
                    "eoq": round(eoq, 2),
                    "annual_demand": round(annual_demand, 2),
                    "number_of_orders_per_year": round(number_of_orders, 2),
                    "time_between_orders_days": round(time_between_orders, 1),
                    "total_annual_cost": round(total_annual_cost, 2),
                    "parameters": {
                        "ordering_cost": ordering_cost,
                        "holding_cost_rate": holding_cost_rate,
                        "unit_cost": unit_cost,
                        "holding_cost_per_unit": round(holding_cost_per_unit, 2)
                    }
                }
                
        except Exception as e:
            logger.error(f"EOQ calculation error: {e}")
            return {"error": f"EOQ calculation failed: {str(e)}"}
    
    def calculate_reorder_point(self, product_id: int, service_level: float = 0.95) -> Dict[str, Any]:
        """
        Calculate reorder point with safety stock
        
        Args:
            product_id: Product ID
            service_level: Desired service level (default 95%)
        """
        try:
            with self.db.session() as session:
                product = session.query(Product).filter(Product.id == product_id).first()
                if not product:
                    return {"error": "Product not found"}
                
                # Get supplier lead time
                supplier = None
                lead_time_days = 7  # Default
                if product.supplier_id:
                    supplier = session.query(Supplier).filter(Supplier.id == product.supplier_id).first()
                    if supplier:
                        lead_time_days = supplier.lead_time_days
                
                # Estimate daily demand
                forecast_result = self.forecasting_service.generate_forecast(product_id, horizon=30)
                if "error" in forecast_result:
                    return {"error": f"Cannot estimate demand: {forecast_result['error']}"}
                
                daily_demand = forecast_result["daily_average"]
                
                if daily_demand <= 0:
                    return {"error": "Daily demand must be positive"}
                
                # Calculate demand during lead time
                lead_time_demand = daily_demand * lead_time_days
                
                # Simplified safety stock calculation
                # In practice, this would use demand variability and lead time variability
                # For now, using a simple percentage of lead time demand
                demand_variability_factor = 0.3  # Assume 30% coefficient of variation
                
                # Z-score for service level (approximate)
                z_scores = {0.90: 1.28, 0.95: 1.65, 0.99: 2.33}
                z_score = z_scores.get(service_level, 1.65)
                
                # Safety stock = z_score * sqrt(lead_time) * daily_demand_std
                # Simplified: safety_stock = z_score * lead_time_demand * variability_factor
                safety_stock = z_score * lead_time_demand * demand_variability_factor
                
                reorder_point = lead_time_demand + safety_stock
                
                return {
                    "product_id": product_id,
                    "sku": product.sku,
                    "reorder_point": round(reorder_point, 2),
                    "lead_time_demand": round(lead_time_demand, 2),
                    "safety_stock": round(safety_stock, 2),
                    "daily_demand": round(daily_demand, 2),
                    "lead_time_days": lead_time_days,
                    "service_level": service_level,
                    "supplier_name": supplier.name if supplier else "Unknown",
                    "parameters": {
                        "z_score": z_score,
                        "demand_variability_factor": demand_variability_factor
                    }
                }
                
        except Exception as e:
            logger.error(f"Reorder point calculation error: {e}")
            return {"error": f"Reorder point calculation failed: {str(e)}"}
    
    def calculate_safety_stock(self, product_id: int, service_level: float = 0.95,
                              demand_variability: Optional[float] = None) -> Dict[str, Any]:
        """
        Calculate optimal safety stock level
        
        Args:
            product_id: Product ID
            service_level: Desired service level (default 95%)
            demand_variability: Coefficient of variation for demand (if None, will estimate)
        """
        try:
            with self.db.session() as session:
                product = session.query(Product).filter(Product.id == product_id).first()
                if not product:
                    return {"error": "Product not found"}
                
                # Get lead time
                lead_time_days = 7
                if product.supplier_id:
                    supplier = session.query(Supplier).filter(Supplier.id == product.supplier_id).first()
                    if supplier:
                        lead_time_days = supplier.lead_time_days
                
                # Get demand forecast
                forecast_result = self.forecasting_service.generate_forecast(product_id, horizon=30)
                if "error" in forecast_result:
                    return {"error": f"Cannot estimate demand: {forecast_result['error']}"}
                
                daily_demand = forecast_result["daily_average"]
                
                # Estimate demand variability if not provided
                if demand_variability is None:
                    # Get historical data to calculate variability
                    historical_df = self.forecasting_service.get_historical_demand(product_id, days=60)
                    if len(historical_df) > 7:
                        daily_demands = historical_df.set_index('date').resample('D')['demand'].sum().fillna(0)
                        if daily_demands.mean() > 0:
                            demand_variability = daily_demands.std() / daily_demands.mean()
                        else:
                            demand_variability = 0.3  # Default assumption
                    else:
                        demand_variability = 0.3  # Default assumption
                
                # Z-score for service level
                z_scores = {0.90: 1.28, 0.95: 1.65, 0.99: 2.33}
                z_score = z_scores.get(service_level, 1.65)
                
                # Safety stock calculation
                # SS = z * sqrt(lead_time) * daily_demand * coefficient_of_variation
                safety_stock = z_score * math.sqrt(lead_time_days) * daily_demand * demand_variability
                
                # Calculate holding cost of safety stock
                holding_cost_rate = 0.25  # 25% annual holding cost
                annual_holding_cost = safety_stock * float(product.unit_cost) * holding_cost_rate
                
                return {
                    "product_id": product_id,
                    "sku": product.sku,
                    "safety_stock": round(safety_stock, 2),
                    "service_level": service_level,
                    "daily_demand": round(daily_demand, 2),
                    "demand_variability": round(demand_variability, 3),
                    "lead_time_days": lead_time_days,
                    "annual_holding_cost": round(annual_holding_cost, 2),
                    "parameters": {
                        "z_score": z_score,
                        "holding_cost_rate": holding_cost_rate
                    }
                }
                
        except Exception as e:
            logger.error(f"Safety stock calculation error: {e}")
            return {"error": f"Safety stock calculation failed: {str(e)}"}
    
    def optimize_inventory_levels(self, product_id: int) -> Dict[str, Any]:
        """
        Comprehensive inventory optimization for a product
        """
        try:
            # Calculate all optimization metrics
            eoq_result = self.calculate_eoq(product_id)
            reorder_result = self.calculate_reorder_point(product_id)
            safety_stock_result = self.calculate_safety_stock(product_id)
            
            if any("error" in result for result in [eoq_result, reorder_result, safety_stock_result]):
                errors = [r.get("error") for r in [eoq_result, reorder_result, safety_stock_result] if "error" in r]
                return {"error": f"Optimization failed: {'; '.join(errors)}"}
            
            # Combine results
            return {
                "product_id": product_id,
                "sku": eoq_result["sku"],
                "optimization_results": {
                    "economic_order_quantity": eoq_result["eoq"],
                    "reorder_point": reorder_result["reorder_point"],
                    "safety_stock": safety_stock_result["safety_stock"],
                    "recommended_max_stock": eoq_result["eoq"] + safety_stock_result["safety_stock"]
                },
                "cost_analysis": {
                    "annual_ordering_cost": eoq_result["total_annual_cost"],
                    "annual_holding_cost": safety_stock_result["annual_holding_cost"],
                    "total_annual_cost": eoq_result["total_annual_cost"] + safety_stock_result["annual_holding_cost"]
                },
                "service_metrics": {
                    "service_level": reorder_result["service_level"],
                    "lead_time_days": reorder_result["lead_time_days"],
                    "orders_per_year": eoq_result["number_of_orders_per_year"]
                }
            }
            
        except Exception as e:
            logger.error(f"Inventory optimization error: {e}")
            return {"error": f"Inventory optimization failed: {str(e)}"}
    
    def scenario_analysis(self, product_id: int, scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform what-if analysis with different scenarios
        
        Args:
            product_id: Product ID
            scenarios: List of scenario parameters to test
        """
        try:
            results = []
            
            for i, scenario in enumerate(scenarios):
                scenario_name = scenario.get("name", f"Scenario {i+1}")
                
                # Calculate EOQ with scenario parameters
                eoq_result = self.calculate_eoq(
                    product_id,
                    annual_demand=scenario.get("annual_demand"),
                    ordering_cost=scenario.get("ordering_cost", 50.0),
                    holding_cost_rate=scenario.get("holding_cost_rate", 0.25)
                )
                
                # Calculate reorder point with scenario parameters
                reorder_result = self.calculate_reorder_point(
                    product_id,
                    service_level=scenario.get("service_level", 0.95)
                )
                
                if "error" in eoq_result or "error" in reorder_result:
                    continue
                
                results.append({
                    "scenario_name": scenario_name,
                    "parameters": scenario,
                    "eoq": eoq_result["eoq"],
                    "reorder_point": reorder_result["reorder_point"],
                    "total_annual_cost": eoq_result["total_annual_cost"],
                    "orders_per_year": eoq_result["number_of_orders_per_year"]
                })
            
            return {
                "product_id": product_id,
                "scenarios": results,
                "comparison_metrics": ["eoq", "reorder_point", "total_annual_cost", "orders_per_year"]
            }
            
        except Exception as e:
            logger.error(f"Scenario analysis error: {e}")
            return {"error": f"Scenario analysis failed: {str(e)}"}
    
    def get_optimization_recommendations(self, location_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get optimization recommendations for products"""
        try:
            with self.db.session() as session:
                query = session.query(Product, Inventory).join(Inventory)
                
                if location_id:
                    from src.data.inventory import Location
                    location = session.query(Location).filter(Location.location_id == location_id).first()
                    if location:
                        query = query.filter(Inventory.location_id == location.id)
                
                results = []
                for product, inventory in query.all():
                    # Quick optimization check
                    current_stock = inventory.quantity_on_hand
                    reorder_point = product.reorder_point
                    
                    # Get EOQ recommendation
                    eoq_result = self.calculate_eoq(product.id)
                    
                    if "error" not in eoq_result:
                        recommended_order_qty = eoq_result["eoq"]
                        
                        # Determine recommendation type
                        if current_stock <= reorder_point:
                            recommendation = "REORDER_NOW"
                            priority = "HIGH"
                        elif current_stock <= reorder_point * 1.5:
                            recommendation = "MONITOR_CLOSELY"
                            priority = "MEDIUM"
                        else:
                            recommendation = "ADEQUATE_STOCK"
                            priority = "LOW"
                        
                        results.append({
                            "sku": product.sku,
                            "product_name": product.name,
                            "current_stock": current_stock,
                            "reorder_point": reorder_point,
                            "recommended_order_qty": round(recommended_order_qty, 0),
                            "recommendation": recommendation,
                            "priority": priority,
                            "estimated_days_of_stock": round(current_stock / max(eoq_result.get("daily_demand", 1), 0.1), 1) if "daily_demand" in eoq_result else None
                        })
                
                # Sort by priority
                priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
                results.sort(key=lambda x: priority_order.get(x["priority"], 3))
                
                return results
                
        except Exception as e:
            logger.error(f"Optimization recommendations error: {e}")
            return []
