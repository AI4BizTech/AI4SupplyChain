"""
Forecasting data models
"""

from sqlalchemy import Column, Integer, String, Decimal, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from src.data.base import Base

class ForecastResult(Base):
    """Store forecast results and metadata"""
    __tablename__ = 'forecast_results'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    location_id = Column(Integer, ForeignKey('locations.id'))  # NULL for aggregate forecasts
    forecast_date = Column(DateTime, default=datetime.utcnow)
    forecast_horizon_days = Column(Integer, nullable=False)
    predicted_demand = Column(Decimal(10, 2), nullable=False)
    confidence_lower = Column(Decimal(10, 2))
    confidence_upper = Column(Decimal(10, 2))
    model_used = Column(String(50), nullable=False)  # moving_average, exponential_smoothing, etc.
    model_parameters = Column(JSON)  # store model-specific parameters
    accuracy_score = Column(Decimal(5, 4))  # when actual data becomes available
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ForecastResult(product_id={self.product_id}, demand={self.predicted_demand}, model='{self.model_used}')>"

class ForecastAccuracy(Base):
    """Track forecast accuracy over time"""
    __tablename__ = 'forecast_accuracy'
    
    id = Column(Integer, primary_key=True)
    forecast_id = Column(Integer, ForeignKey('forecast_results.id'), nullable=False)
    actual_demand = Column(Decimal(10, 2), nullable=False)
    forecast_error = Column(Decimal(10, 2))  # actual - predicted
    absolute_error = Column(Decimal(10, 2))  # abs(actual - predicted)
    percentage_error = Column(Decimal(10, 4))  # error / actual * 100
    evaluation_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    forecast = relationship("ForecastResult")
    
    def __repr__(self):
        return f"<ForecastAccuracy(forecast_id={self.forecast_id}, error={self.forecast_error})>"
