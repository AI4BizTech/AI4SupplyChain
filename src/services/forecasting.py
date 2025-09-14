"""
Demand forecasting service
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy import func
import logging
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.seasonal import seasonal_decompose

from src.data.database import get_database
from src.data.inventory import Product, Transaction
from src.data.forecast import ForecastResult

logger = logging.getLogger(__name__)

class ForecastingService:
    """Service for demand forecasting using various algorithms"""
    
    def __init__(self, db=None):
        self.db = db or get_database()
    
    def get_historical_demand(self, product_id: int, days: int = 90) -> pd.DataFrame:
        """Get historical demand data for a product"""
        with self.db.session() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get outbound transactions (shipments) as demand
            transactions = session.query(
                Transaction.timestamp,
                Transaction.quantity
            ).filter(
                Transaction.product_id == product_id,
                Transaction.transaction_type == 'shipment',
                Transaction.timestamp >= cutoff_date
            ).order_by(Transaction.timestamp).all()
            
            if not transactions:
                return pd.DataFrame(columns=['date', 'demand'])
            
            # Convert to DataFrame
            df = pd.DataFrame([
                {'date': t.timestamp.date(), 'demand': abs(t.quantity)}  # shipments are negative
                for t in transactions
            ])
            
            # Group by date and sum demand
            df = df.groupby('date')['demand'].sum().reset_index()
            df['date'] = pd.to_datetime(df['date'])
            
            return df
    
    def moving_average_forecast(self, product_id: int, horizon: int = 7, window: int = 14) -> Dict[str, Any]:
        """Generate forecast using moving average"""
        try:
            df = self.get_historical_demand(product_id, days=window * 2)
            
            if len(df) < window:
                return {"error": f"Insufficient data. Need at least {window} days of data."}
            
            # Calculate moving average
            df = df.set_index('date').sort_index()
            df['ma'] = df['demand'].rolling(window=window).mean()
            
            # Use last moving average value as forecast
            last_ma = df['ma'].iloc[-1]
            if pd.isna(last_ma):
                last_ma = df['demand'].mean()
            
            total_forecast = last_ma * horizon
            
            return {
                "product_id": product_id,
                "forecast_method": "moving_average",
                "horizon_days": horizon,
                "total_forecast": float(total_forecast),
                "daily_average": float(last_ma),
                "parameters": {"window": window},
                "data_points": len(df)
            }
            
        except Exception as e:
            logger.error(f"Moving average forecast error: {e}")
            return {"error": f"Forecast calculation failed: {str(e)}"}
    
    def exponential_smoothing_forecast(self, product_id: int, horizon: int = 7) -> Dict[str, Any]:
        """Generate forecast using exponential smoothing"""
        try:
            df = self.get_historical_demand(product_id, days=90)
            
            if len(df) < 14:
                return {"error": "Insufficient data. Need at least 14 days of data."}
            
            # Prepare data
            df = df.set_index('date').sort_index()
            demand_series = df['demand'].asfreq('D', fill_value=0)
            
            # Apply exponential smoothing
            if len(demand_series) >= 14:
                try:
                    # Try with trend and seasonal components if enough data
                    if len(demand_series) >= 28:
                        model = ExponentialSmoothing(
                            demand_series,
                            trend='add',
                            seasonal=None,  # Daily data might not have clear seasonality
                            initialization_method='estimated'
                        )
                    else:
                        model = ExponentialSmoothing(
                            demand_series,
                            trend='add',
                            seasonal=None,
                            initialization_method='estimated'
                        )
                    
                    fitted_model = model.fit()
                    forecast = fitted_model.forecast(horizon)
                    
                except Exception:
                    # Fallback to simple exponential smoothing
                    model = ExponentialSmoothing(
                        demand_series,
                        trend=None,
                        seasonal=None,
                        initialization_method='estimated'
                    )
                    fitted_model = model.fit()
                    forecast = fitted_model.forecast(horizon)
            
            else:
                # Very simple exponential smoothing for small datasets
                alpha = 0.3
                forecast_value = demand_series.ewm(alpha=alpha).mean().iloc[-1]
                forecast = [forecast_value] * horizon
            
            total_forecast = sum(forecast)
            daily_average = total_forecast / horizon
            
            return {
                "product_id": product_id,
                "forecast_method": "exponential_smoothing",
                "horizon_days": horizon,
                "total_forecast": float(total_forecast),
                "daily_average": float(daily_average),
                "forecast_series": [float(f) for f in forecast],
                "parameters": {"alpha": 0.3},  # Simplified
                "data_points": len(demand_series)
            }
            
        except Exception as e:
            logger.error(f"Exponential smoothing forecast error: {e}")
            return {"error": f"Forecast calculation failed: {str(e)}"}
    
    def trend_analysis_forecast(self, product_id: int, horizon: int = 7) -> Dict[str, Any]:
        """Generate forecast using trend analysis"""
        try:
            df = self.get_historical_demand(product_id, days=60)
            
            if len(df) < 10:
                return {"error": "Insufficient data for trend analysis. Need at least 10 days of data."}
            
            # Prepare data
            df = df.set_index('date').sort_index()
            df = df.asfreq('D', fill_value=0)
            
            # Calculate trend using linear regression
            x = np.arange(len(df))
            y = df['demand'].values
            
            # Simple linear regression
            n = len(x)
            sum_x = np.sum(x)
            sum_y = np.sum(y)
            sum_xy = np.sum(x * y)
            sum_x2 = np.sum(x * x)
            
            # Calculate slope and intercept
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            intercept = (sum_y - slope * sum_x) / n
            
            # Generate forecast
            forecast_x = np.arange(len(df), len(df) + horizon)
            forecast_values = slope * forecast_x + intercept
            
            # Ensure non-negative forecasts
            forecast_values = np.maximum(forecast_values, 0)
            
            total_forecast = np.sum(forecast_values)
            daily_average = total_forecast / horizon
            
            return {
                "product_id": product_id,
                "forecast_method": "trend_analysis",
                "horizon_days": horizon,
                "total_forecast": float(total_forecast),
                "daily_average": float(daily_average),
                "forecast_series": [float(f) for f in forecast_values],
                "trend_slope": float(slope),
                "parameters": {"slope": float(slope), "intercept": float(intercept)},
                "data_points": len(df)
            }
            
        except Exception as e:
            logger.error(f"Trend analysis forecast error: {e}")
            return {"error": f"Forecast calculation failed: {str(e)}"}
    
    def generate_forecast(self, product_id: int, horizon: int = 7, method: str = "auto") -> Dict[str, Any]:
        """Generate forecast using the specified method or auto-select best method"""
        
        if method == "moving_average":
            return self.moving_average_forecast(product_id, horizon)
        elif method == "exponential_smoothing":
            return self.exponential_smoothing_forecast(product_id, horizon)
        elif method == "trend_analysis":
            return self.trend_analysis_forecast(product_id, horizon)
        elif method == "auto":
            # Auto-select based on data availability and characteristics
            df = self.get_historical_demand(product_id, days=90)
            
            if len(df) < 7:
                return {"error": "Insufficient data for forecasting. Need at least 7 days of historical data."}
            elif len(df) < 14:
                return self.moving_average_forecast(product_id, horizon, window=min(7, len(df)))
            else:
                # Use exponential smoothing for most cases
                result = self.exponential_smoothing_forecast(product_id, horizon)
                if "error" not in result:
                    return result
                else:
                    # Fallback to moving average
                    return self.moving_average_forecast(product_id, horizon)
        else:
            return {"error": f"Unknown forecast method: {method}"}
    
    def save_forecast_result(self, forecast_data: Dict[str, Any]) -> Optional[ForecastResult]:
        """Save forecast result to database"""
        try:
            with self.db.session() as session:
                forecast_result = ForecastResult(
                    product_id=forecast_data["product_id"],
                    forecast_horizon_days=forecast_data["horizon_days"],
                    predicted_demand=forecast_data["total_forecast"],
                    model_used=forecast_data["forecast_method"],
                    model_parameters=forecast_data.get("parameters", {})
                )
                
                session.add(forecast_result)
                session.flush()
                session.refresh(forecast_result)
                return forecast_result
                
        except Exception as e:
            logger.error(f"Error saving forecast result: {e}")
            return None
    
    def get_forecast_accuracy(self, product_id: int, days: int = 30) -> Dict[str, Any]:
        """Calculate forecast accuracy for recent predictions"""
        with self.db.session() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get recent forecasts
            forecasts = session.query(ForecastResult).filter(
                ForecastResult.product_id == product_id,
                ForecastResult.forecast_date >= cutoff_date
            ).all()
            
            if not forecasts:
                return {"error": "No recent forecasts found"}
            
            # For simplicity, return basic metrics
            # In a real implementation, you would compare forecasts with actual demand
            
            avg_forecast = sum(f.predicted_demand for f in forecasts) / len(forecasts)
            
            return {
                "product_id": product_id,
                "forecast_count": len(forecasts),
                "average_forecast": float(avg_forecast),
                "period_days": days,
                "accuracy_note": "Detailed accuracy calculation requires comparison with actual demand data"
            }
    
    def get_seasonal_patterns(self, product_id: int) -> Dict[str, Any]:
        """Analyze seasonal patterns in demand"""
        try:
            df = self.get_historical_demand(product_id, days=365)  # Need at least a year
            
            if len(df) < 30:
                return {"error": "Insufficient data for seasonal analysis. Need at least 30 days."}
            
            # Prepare data
            df = df.set_index('date').sort_index()
            df = df.asfreq('D', fill_value=0)
            
            if len(df) < 30:
                return {"seasonal_detected": False, "reason": "Insufficient continuous data"}
            
            # Simple seasonal analysis - day of week patterns
            df['day_of_week'] = df.index.dayofweek
            day_avg = df.groupby('day_of_week')['demand'].mean()
            
            # Calculate coefficient of variation to detect seasonality
            cv = day_avg.std() / day_avg.mean() if day_avg.mean() > 0 else 0
            
            seasonal_detected = cv > 0.2  # Threshold for seasonal detection
            
            return {
                "product_id": product_id,
                "seasonal_detected": seasonal_detected,
                "day_of_week_pattern": {
                    "Monday": float(day_avg.get(0, 0)),
                    "Tuesday": float(day_avg.get(1, 0)),
                    "Wednesday": float(day_avg.get(2, 0)),
                    "Thursday": float(day_avg.get(3, 0)),
                    "Friday": float(day_avg.get(4, 0)),
                    "Saturday": float(day_avg.get(5, 0)),
                    "Sunday": float(day_avg.get(6, 0))
                },
                "coefficient_of_variation": float(cv),
                "data_points": len(df)
            }
            
        except Exception as e:
            logger.error(f"Seasonal analysis error: {e}")
            return {"error": f"Seasonal analysis failed: {str(e)}"}
