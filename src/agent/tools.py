"""
LangChain tools for inventory operations
"""

from langchain.tools import BaseTool
from typing import Type, Dict, Any, Optional, List
from pydantic import BaseModel, Field
import logging

from src.services.inventory import InventoryService
from src.services.suppliers import SupplierService
from src.services.forecasting import ForecastingService
from src.services.optimization import OptimizationService
from src.services.transactions import TransactionService

logger = logging.getLogger(__name__)

# Input schemas for tools
class InventoryQueryInput(BaseModel):
    """Input schema for inventory queries"""
    sku: str = Field(description="Product SKU to query")
    location_id: Optional[str] = Field(default=None, description="Specific location ID or None for all locations")

class ForecastInput(BaseModel):
    """Input schema for demand forecasting"""
    sku: str = Field(description="Product SKU to forecast")
    horizon_days: int = Field(default=7, description="Forecast horizon in days")
    method: str = Field(default="auto", description="Forecast method: auto, moving_average, exponential_smoothing, trend_analysis")

class OptimizationInput(BaseModel):
    """Input schema for optimization calculations"""
    sku: str = Field(description="Product SKU to optimize")
    calculation_type: str = Field(default="all", description="Type of calculation: eoq, reorder_point, safety_stock, or all")

class SupplierQueryInput(BaseModel):
    """Input schema for supplier queries"""
    supplier_id: Optional[str] = Field(default=None, description="Supplier ID to query, or None for all suppliers")

class LowStockInput(BaseModel):
    """Input schema for low stock queries"""
    location_id: Optional[str] = Field(default=None, description="Location ID to filter by, or None for all locations")

class TransactionHistoryInput(BaseModel):
    """Input schema for transaction history"""
    sku: Optional[str] = Field(default=None, description="Product SKU to filter by")
    limit: int = Field(default=20, description="Maximum number of transactions to return")

class InventoryTools:
    """Collection of inventory management tools for LangChain agent"""
    
    def __init__(self):
        self.inventory_service = InventoryService()
        self.supplier_service = SupplierService()
        self.forecasting_service = ForecastingService()
        self.optimization_service = OptimizationService()
        self.transaction_service = TransactionService()
    
    def get_tools(self) -> List[BaseTool]:
        """Get all available tools"""
        return [
            InventoryQueryTool(self.inventory_service),
            ForecastTool(self.forecasting_service, self.inventory_service),
            OptimizationTool(self.optimization_service, self.inventory_service),
            SupplierQueryTool(self.supplier_service),
            LowStockAlertTool(self.inventory_service),
            TransactionHistoryTool(self.inventory_service),
            InventorySummaryTool(self.inventory_service),
            ReorderRecommendationsTool(self.optimization_service)
        ]

class InventoryQueryTool(BaseTool):
    """Tool for querying current inventory levels"""
    name = "inventory_query"
    description = """
    Query current inventory levels for a specific product across warehouses.
    Use this when users ask about stock levels, availability, or current inventory.
    Returns detailed breakdown by warehouse with reorder recommendations.
    """
    args_schema: Type[BaseModel] = InventoryQueryInput
    
    def __init__(self, inventory_service: InventoryService):
        super().__init__()
        self.inventory_service = inventory_service
    
    def _run(self, sku: str, location_id: Optional[str] = None) -> str:
        """Execute inventory query"""
        try:
            stock_levels = self.inventory_service.get_stock_levels(sku, location_id)
            
            if not stock_levels:
                return f"❌ No inventory found for product {sku}"
            
            # Get product details
            product = self.inventory_service.get_product_by_sku(sku)
            if not product:
                return f"❌ Product {sku} not found"
            
            # Calculate totals
            total_stock = sum(item['quantity_on_hand'] for item in stock_levels)
            total_available = sum(item['available_quantity'] for item in stock_levels)
            total_reserved = sum(item['reserved_quantity'] for item in stock_levels)
            
            # Determine status
            if total_stock <= product.reorder_point:
                status = "🔴 CRITICAL - Below Reorder Point"
                urgency = "URGENT"
            elif total_stock <= product.reorder_point * 1.5:
                status = "🟡 LOW - Monitor Closely"
                urgency = "MEDIUM"
            else:
                status = "🟢 ADEQUATE"
                urgency = "LOW"
            
            # Format location breakdown
            location_breakdown = []
            for item in stock_levels:
                location_breakdown.append(
                    f"  📍 {item['location_name']}: {item['quantity_on_hand']} units "
                    f"({item['available_quantity']} available, {item['reserved_quantity']} reserved)"
                )
            
            response = f"""📦 **Inventory Report for {sku}**
**Product**: {product.name}
**Category**: {product.category}

**Stock Summary**:
• Total Stock: {total_stock} units
• Available: {total_available} units  
• Reserved: {total_reserved} units
• Status: {status}
• Reorder Point: {product.reorder_point} units

**Location Breakdown**:
{chr(10).join(location_breakdown)}

**Recommendation**: {"⚠️ Consider reordering immediately!" if urgency == "URGENT" else "✅ Stock levels are adequate" if urgency == "LOW" else "📊 Monitor closely and prepare for reorder"}
"""
            return response.strip()
            
        except Exception as e:
            logger.error(f"Inventory query error: {e}")
            return f"❌ Error querying inventory: {str(e)}"

class ForecastTool(BaseTool):
    """Tool for generating demand forecasts"""
    name = "demand_forecast"
    description = """
    Generate demand forecast for a specific product over a given time horizon.
    Use this when users ask about future demand, sales predictions, or planning needs.
    Returns forecast with confidence intervals and recommendations.
    """
    args_schema: Type[BaseModel] = ForecastInput
    
    def __init__(self, forecasting_service: ForecastingService, inventory_service: InventoryService):
        super().__init__()
        self.forecasting_service = forecasting_service
        self.inventory_service = inventory_service
    
    def _run(self, sku: str, horizon_days: int = 7, method: str = "auto") -> str:
        """Generate demand forecast"""
        try:
            # Get product
            product = self.inventory_service.get_product_by_sku(sku)
            if not product:
                return f"❌ Product {sku} not found"
            
            # Generate forecast
            forecast = self.forecasting_service.generate_forecast(
                product.id, horizon=horizon_days, method=method
            )
            
            if "error" in forecast:
                return f"❌ Cannot generate forecast: {forecast['error']}"
            
            total_forecast = forecast.get('total_forecast', 0)
            daily_avg = forecast.get('daily_average', 0)
            method_used = forecast.get('forecast_method', 'unknown')
            data_points = forecast.get('data_points', 0)
            
            # Get current stock for comparison
            stock_levels = self.inventory_service.get_stock_levels(sku)
            current_stock = sum(item['quantity_on_hand'] for item in stock_levels) if stock_levels else 0
            
            # Calculate days of stock remaining
            days_of_stock = round(current_stock / max(daily_avg, 0.1), 1) if daily_avg > 0 else float('inf')
            
            # Generate recommendation
            if days_of_stock < horizon_days:
                recommendation = "🔴 URGENT: Current stock insufficient for forecast period"
            elif days_of_stock < horizon_days * 1.5:
                recommendation = "🟡 CAUTION: Stock may run low during forecast period"
            else:
                recommendation = "🟢 ADEQUATE: Current stock should cover forecast period"
            
            response = f"""📈 **Demand Forecast for {sku}**
**Product**: {product.name}

**Forecast Results**:
• Period: Next {horizon_days} days
• Total Predicted Demand: {total_forecast:.1f} units
• Daily Average: {daily_avg:.1f} units/day
• Method Used: {method_used.replace('_', ' ').title()}
• Based on: {data_points} historical data points

**Current Situation**:
• Current Stock: {current_stock} units
• Days of Stock Remaining: {days_of_stock:.1f} days

**Planning Recommendation**: 
{recommendation}
"""
            
            # Add forecast series if available
            if 'forecast_series' in forecast and len(forecast['forecast_series']) <= 14:
                series_str = ", ".join([f"{f:.1f}" for f in forecast['forecast_series'][:7]])
                response += f"\n**Daily Forecast (first 7 days)**: {series_str}"
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Forecast error: {e}")
            return f"❌ Error generating forecast: {str(e)}"

class OptimizationTool(BaseTool):
    """Tool for inventory optimization calculations"""
    name = "inventory_optimization"
    description = """
    Calculate optimal inventory parameters like EOQ, reorder points, and safety stock.
    Use this when users ask about optimization, order quantities, or reorder recommendations.
    """
    args_schema: Type[BaseModel] = OptimizationInput
    
    def __init__(self, optimization_service: OptimizationService, inventory_service: InventoryService):
        super().__init__()
        self.optimization_service = optimization_service
        self.inventory_service = inventory_service
    
    def _run(self, sku: str, calculation_type: str = "all") -> str:
        """Execute optimization calculations"""
        try:
            # Get product
            product = self.inventory_service.get_product_by_sku(sku)
            if not product:
                return f"❌ Product {sku} not found"
            
            if calculation_type == "eoq":
                result = self.optimization_service.calculate_eoq(product.id)
            elif calculation_type == "reorder_point":
                result = self.optimization_service.calculate_reorder_point(product.id)
            elif calculation_type == "safety_stock":
                result = self.optimization_service.calculate_safety_stock(product.id)
            else:  # all
                result = self.optimization_service.optimize_inventory_levels(product.id)
            
            if "error" in result:
                return f"❌ Optimization failed: {result['error']}"
            
            if calculation_type == "all":
                # Comprehensive optimization report
                opt_results = result['optimization_results']
                cost_analysis = result['cost_analysis']
                service_metrics = result['service_metrics']
                
                response = f"""⚙️ **Inventory Optimization for {sku}**
**Product**: {product.name}

**Optimal Parameters**:
• Economic Order Quantity (EOQ): {opt_results['economic_order_quantity']:.0f} units
• Reorder Point: {opt_results['reorder_point']:.0f} units
• Safety Stock: {opt_results['safety_stock']:.0f} units
• Recommended Max Stock: {opt_results['recommended_max_stock']:.0f} units

**Cost Analysis**:
• Annual Ordering Cost: ${cost_analysis['annual_ordering_cost']:.2f}
• Annual Holding Cost: ${cost_analysis['annual_holding_cost']:.2f}
• Total Annual Cost: ${cost_analysis['total_annual_cost']:.2f}

**Service Metrics**:
• Service Level: {service_metrics['service_level']*100:.0f}%
• Lead Time: {service_metrics['lead_time_days']} days
• Orders Per Year: {service_metrics['orders_per_year']:.1f}

**Current vs Optimal**:
• Current Reorder Point: {product.reorder_point} units
• Current Order Quantity: {product.reorder_quantity} units
• Optimization Potential: {"✅ Current settings are close to optimal" if abs(product.reorder_point - opt_results['reorder_point']) < 10 else "📊 Consider updating reorder parameters"}
"""
            else:
                # Single calculation report
                if calculation_type == "eoq":
                    response = f"""📊 **EOQ Analysis for {sku}**
• Optimal Order Quantity: {result['eoq']:.0f} units
• Annual Demand: {result['annual_demand']:.0f} units
• Orders Per Year: {result['number_of_orders_per_year']:.1f}
• Time Between Orders: {result['time_between_orders_days']:.1f} days
• Total Annual Cost: ${result['total_annual_cost']:.2f}
"""
                elif calculation_type == "reorder_point":
                    response = f"""🎯 **Reorder Point Analysis for {sku}**
• Optimal Reorder Point: {result['reorder_point']:.0f} units
• Lead Time Demand: {result['lead_time_demand']:.0f} units
• Safety Stock: {result['safety_stock']:.0f} units
• Service Level: {result['service_level']*100:.0f}%
• Lead Time: {result['lead_time_days']} days
"""
                else:  # safety_stock
                    response = f"""🛡️ **Safety Stock Analysis for {sku}**
• Optimal Safety Stock: {result['safety_stock']:.0f} units
• Service Level: {result['service_level']*100:.0f}%
• Daily Demand: {result['daily_demand']:.1f} units
• Demand Variability: {result['demand_variability']*100:.1f}%
• Annual Holding Cost: ${result['annual_holding_cost']:.2f}
"""
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Optimization error: {e}")
            return f"❌ Error in optimization: {str(e)}"

class SupplierQueryTool(BaseTool):
    """Tool for querying supplier information"""
    name = "supplier_query"
    description = """
    Query supplier information including performance metrics and product listings.
    Use this when users ask about suppliers, vendor information, or supplier performance.
    """
    args_schema: Type[BaseModel] = SupplierQueryInput
    
    def __init__(self, supplier_service: SupplierService):
        super().__init__()
        self.supplier_service = supplier_service
    
    def _run(self, supplier_id: Optional[str] = None) -> str:
        """Execute supplier query"""
        try:
            if supplier_id:
                # Get specific supplier details
                supplier = self.supplier_service.get_supplier_by_id(supplier_id)
                if not supplier:
                    return f"❌ Supplier {supplier_id} not found"
                
                # Get performance metrics
                performance = self.supplier_service.get_supplier_performance(supplier_id)
                products = self.supplier_service.get_supplier_products(supplier_id)
                
                contact_info = supplier.contact_info or {}
                
                response = f"""🏢 **Supplier Details: {supplier.name}**
**ID**: {supplier.supplier_id}

**Contact Information**:
• Email: {contact_info.get('email', 'Not provided')}
• Phone: {contact_info.get('phone', 'Not provided')}
• Contact Person: {contact_info.get('contact_person', 'Not provided')}

**Business Terms**:
• Lead Time: {supplier.lead_time_days} days
• Payment Terms: {supplier.payment_terms or 'Not specified'}
• Minimum Order Qty: {supplier.minimum_order_qty} units
• Performance Rating: {supplier.performance_rating or 'Not rated'}/5.0

**Performance Metrics** (Last 90 days):
• Total Orders: {performance.get('total_orders', 0)}
• Total Value: ${performance.get('total_value', 0):,.2f}
• On-Time Delivery: {performance.get('on_time_delivery_rate', 0)*100:.1f}%

**Products Supplied**: {len(products)} products
"""
                if products:
                    top_products = products[:5]  # Show top 5
                    product_list = "\n".join([f"  • {p['sku']}: {p['name']} (${p['unit_cost']:.2f})" for p in top_products])
                    response += f"\n**Top Products**:\n{product_list}"
                    if len(products) > 5:
                        response += f"\n  ... and {len(products) - 5} more products"
                
            else:
                # Get all suppliers summary
                suppliers = self.supplier_service.get_suppliers_summary()
                
                if not suppliers:
                    return "❌ No suppliers found in the system"
                
                response = f"🏢 **Supplier Summary** ({len(suppliers)} suppliers)\n\n"
                
                for supplier in suppliers[:10]:  # Show top 10
                    response += f"**{supplier['name']}** ({supplier['supplier_id']})\n"
                    response += f"  • Products: {supplier['product_count']} | "
                    response += f"Lead Time: {supplier['lead_time_days']} days | "
                    response += f"Rating: {supplier['performance_rating']:.1f}/5.0\n"
                    response += f"  • Recent Orders: ${supplier['recent_order_value']:,.2f}\n\n"
                
                if len(suppliers) > 10:
                    response += f"... and {len(suppliers) - 10} more suppliers"
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Supplier query error: {e}")
            return f"❌ Error querying suppliers: {str(e)}"

class LowStockAlertTool(BaseTool):
    """Tool for identifying low stock items"""
    name = "low_stock_alerts"
    description = """
    Identify products that are below their reorder points and need attention.
    Use this when users ask about low stock, items to reorder, or stock alerts.
    """
    args_schema: Type[BaseModel] = LowStockInput
    
    def __init__(self, inventory_service: InventoryService):
        super().__init__()
        self.inventory_service = inventory_service
    
    def _run(self, location_id: Optional[str] = None) -> str:
        """Get low stock alerts"""
        try:
            low_stock_items = self.inventory_service.get_low_stock_items(location_id)
            
            if not low_stock_items:
                return "✅ No low stock alerts! All products are above their reorder points."
            
            # Group by urgency
            critical = [item for item in low_stock_items if item['current_stock'] <= item['reorder_point'] * 0.5]
            urgent = [item for item in low_stock_items if item['reorder_point'] * 0.5 < item['current_stock'] <= item['reorder_point']]
            
            response = f"🚨 **Low Stock Alert Report**\n"
            
            if location_id:
                response += f"**Location**: {location_id}\n"
            else:
                response += "**All Locations**\n"
            
            response += f"**Total Items Below Reorder Point**: {len(low_stock_items)}\n\n"
            
            if critical:
                response += f"🔴 **CRITICAL** ({len(critical)} items):\n"
                for item in critical[:5]:  # Show top 5 critical
                    response += f"  • {item['sku']}: {item['current_stock']}/{item['reorder_point']} units "
                    response += f"at {item['location_name']}\n"
                    response += f"    Suggested Order: {item['reorder_quantity']} units\n"
                if len(critical) > 5:
                    response += f"  ... and {len(critical) - 5} more critical items\n"
                response += "\n"
            
            if urgent:
                response += f"🟡 **URGENT** ({len(urgent)} items):\n"
                for item in urgent[:5]:  # Show top 5 urgent
                    response += f"  • {item['sku']}: {item['current_stock']}/{item['reorder_point']} units "
                    response += f"at {item['location_name']}\n"
                if len(urgent) > 5:
                    response += f"  ... and {len(urgent) - 5} more urgent items\n"
            
            response += f"\n**Recommendation**: {'🔥 Immediate action required for critical items!' if critical else '📊 Plan reorders for urgent items soon.'}"
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Low stock alert error: {e}")
            return f"❌ Error getting low stock alerts: {str(e)}"

class TransactionHistoryTool(BaseTool):
    """Tool for querying transaction history"""
    name = "transaction_history"
    description = """
    Query recent transaction history for products or locations.
    Use this when users ask about recent activities, transaction logs, or inventory movements.
    """
    args_schema: Type[BaseModel] = TransactionHistoryInput
    
    def __init__(self, inventory_service: InventoryService):
        super().__init__()
        self.inventory_service = inventory_service
    
    def _run(self, sku: Optional[str] = None, limit: int = 20) -> str:
        """Get transaction history"""
        try:
            # Get product ID if SKU provided
            product_id = None
            if sku:
                product = self.inventory_service.get_product_by_sku(sku)
                if not product:
                    return f"❌ Product {sku} not found"
                product_id = product.id
            
            transactions = self.inventory_service.get_transaction_history(
                product_id=product_id, limit=limit
            )
            
            if not transactions:
                filter_text = f" for {sku}" if sku else ""
                return f"📝 No recent transactions found{filter_text}"
            
            response = f"📝 **Transaction History**"
            if sku:
                response += f" for {sku}"
            response += f" (Last {len(transactions)} transactions)\n\n"
            
            for trans in transactions:
                # Format transaction type with emoji
                type_emoji = {
                    'receipt': '📦',
                    'shipment': '🚚',
                    'adjustment': '⚖️',
                    'expected_receipt': '📋',
                    'transfer': '🔄'
                }.get(trans['transaction_type'], '📄')
                
                response += f"{type_emoji} **{trans['transaction_type'].title()}** - {trans['transaction_id']}\n"
                response += f"  • Product: {trans['sku']} - {trans['product_name']}\n"
                response += f"  • Location: {trans['location_name']}\n"
                response += f"  • Quantity: {trans['quantity']} units\n"
                response += f"  • Date: {trans['timestamp'].strftime('%Y-%m-%d %H:%M')}\n"
                
                if trans['reference_document']:
                    response += f"  • Reference: {trans['reference_document']}\n"
                if trans['notes']:
                    response += f"  • Notes: {trans['notes']}\n"
                response += "\n"
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Transaction history error: {e}")
            return f"❌ Error getting transaction history: {str(e)}"

class InventorySummaryTool(BaseTool):
    """Tool for getting overall inventory summary"""
    name = "inventory_summary"
    description = """
    Get overall inventory summary with key metrics and statistics.
    Use this when users ask for dashboard information, overview, or general inventory status.
    """
    args_schema: Type[BaseModel] = BaseModel
    
    def __init__(self, inventory_service: InventoryService):
        super().__init__()
        self.inventory_service = inventory_service
    
    def _run(self) -> str:
        """Get inventory summary"""
        try:
            summary = self.inventory_service.get_inventory_summary()
            
            response = f"""📊 **Inventory Dashboard Summary**

**Overall Statistics**:
• Total Products: {summary['total_products']:,}
• Total Locations: {summary['total_locations']}
• Total Inventory Value: ${summary['total_inventory_value']:,.2f}

**Activity Metrics**:
• Low Stock Items: {summary['low_stock_items']} ({'🔴 Attention needed!' if summary['low_stock_items'] > 0 else '✅ All good!'})
• Recent Transactions (7 days): {summary['recent_transactions']}

**Status Overview**:
• Inventory Health: {'🟡 Needs attention' if summary['low_stock_items'] > summary['total_products'] * 0.1 else '🟢 Healthy'}
• Activity Level: {'🔥 High' if summary['recent_transactions'] > 50 else '📊 Normal' if summary['recent_transactions'] > 10 else '🔄 Low'}

**Quick Actions**:
• Check low stock alerts for reorder recommendations
• Review recent transactions for unusual patterns  
• Run demand forecasts for planning purposes
"""
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Inventory summary error: {e}")
            return f"❌ Error getting inventory summary: {str(e)}"

class ReorderRecommendationsTool(BaseTool):
    """Tool for getting reorder recommendations"""
    name = "reorder_recommendations"
    description = """
    Get intelligent reorder recommendations based on optimization calculations.
    Use this when users ask about what to order, purchase recommendations, or procurement planning.
    """
    args_schema: Type[BaseModel] = LowStockInput
    
    def __init__(self, optimization_service: OptimizationService):
        super().__init__()
        self.optimization_service = optimization_service
    
    def _run(self, location_id: Optional[str] = None) -> str:
        """Get reorder recommendations"""
        try:
            recommendations = self.optimization_service.get_optimization_recommendations(location_id)
            
            if not recommendations:
                return "✅ No reorder recommendations at this time. All inventory levels are adequate."
            
            # Group by priority
            high_priority = [r for r in recommendations if r['priority'] == 'HIGH']
            medium_priority = [r for r in recommendations if r['priority'] == 'MEDIUM']
            
            response = f"🛒 **Reorder Recommendations**\n"
            
            if location_id:
                response += f"**Location**: {location_id}\n"
            
            response += f"**Total Items**: {len(recommendations)}\n\n"
            
            if high_priority:
                response += f"🔴 **HIGH PRIORITY** ({len(high_priority)} items) - Order immediately:\n"
                for item in high_priority[:10]:  # Show top 10
                    days_stock = item.get('estimated_days_of_stock', 'Unknown')
                    response += f"  • **{item['sku']}** - {item['product_name']}\n"
                    response += f"    Current: {item['current_stock']} | Reorder at: {item['reorder_point']} | "
                    response += f"Order: {item['recommended_order_qty']:.0f} units\n"
                    if days_stock != 'Unknown':
                        response += f"    Days of stock remaining: {days_stock}\n"
                response += "\n"
            
            if medium_priority:
                response += f"🟡 **MEDIUM PRIORITY** ({len(medium_priority)} items) - Plan to order soon:\n"
                for item in medium_priority[:5]:  # Show top 5
                    response += f"  • {item['sku']}: Order {item['recommended_order_qty']:.0f} units "
                    response += f"(Current: {item['current_stock']})\n"
                if len(medium_priority) > 5:
                    response += f"  ... and {len(medium_priority) - 5} more medium priority items\n"
            
            # Calculate total order value (simplified)
            total_items = len([r for r in recommendations if r['priority'] in ['HIGH', 'MEDIUM']])
            response += f"\n**Summary**: {total_items} items need reordering"
            
            if high_priority:
                response += f"\n🚨 **Action Required**: {len(high_priority)} items need immediate ordering to prevent stockouts!"
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Reorder recommendations error: {e}")
            return f"❌ Error getting reorder recommendations: {str(e)}"
