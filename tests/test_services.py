"""
Tests for business logic services
"""
import pytest
from unittest.mock import Mock, patch
from src.services.inventory import InventoryService
from src.services.suppliers import SupplierService
from src.services.forecasting import ForecastingService
from src.services.optimization import OptimizationService
from src.services.simulation import SimulationService


class TestInventoryService:
    """Test InventoryService"""
    
    def test_get_inventory_summary(self, db_session):
        """Test getting inventory summary"""
        service = InventoryService(db_session)
        summary = service.get_inventory_summary()
        
        assert isinstance(summary, dict)
        assert 'total_products' in summary
        assert 'total_locations' in summary
        assert 'total_inventory_value' in summary
        assert 'low_stock_items' in summary
    
    def test_get_low_stock_products(self, db_session, sample_inventory):
        """Test getting low stock products"""
        service = InventoryService(db_session)
        
        # Set inventory below reorder point
        sample_inventory.quantity_on_hand = 5
        sample_inventory.product.reorder_point = 20
        db_session.commit()
        
        low_stock = service.get_low_stock_products()
        assert len(low_stock) >= 1
        assert any(item.id == sample_inventory.product.id for item in low_stock)
    
    def test_update_stock_levels(self, db_session, sample_inventory):
        """Test updating stock levels"""
        service = InventoryService(db_session)
        original_quantity = sample_inventory.quantity_on_hand
        
        # Update stock
        service.update_stock_levels(
            sample_inventory.product.id, 
            sample_inventory.location.id, 
            75
        )
        
        db_session.refresh(sample_inventory)
        assert sample_inventory.quantity_on_hand == 75
        assert sample_inventory.quantity_on_hand != original_quantity


class TestSupplierService:
    """Test SupplierService"""
    
    def test_get_all_suppliers(self, db_session, sample_supplier):
        """Test getting all suppliers"""
        service = SupplierService(db_session)
        suppliers = service.get_all_suppliers()
        
        assert len(suppliers) >= 1
        assert any(s.id == sample_supplier.id for s in suppliers)
    
    def test_create_supplier(self, db_session):
        """Test creating a new supplier"""
        service = SupplierService(db_session)
        
        supplier_data = {
            'supplier_id': 'NEW001',
            'name': 'New Supplier',
            'contact_info': {'email': 'new@supplier.com'},
            'lead_time_days': 10,
            'payment_terms': 'NET45'
        }
        
        new_supplier = service.create_supplier(supplier_data)
        assert new_supplier.supplier_id == 'NEW001'
        assert new_supplier.name == 'New Supplier'
        assert new_supplier.lead_time_days == 10
    
    def test_update_performance_score(self, db_session, sample_supplier):
        """Test updating supplier performance score"""
        service = SupplierService(db_session)
        original_score = sample_supplier.performance_score
        
        service.update_performance_score(sample_supplier.id, 85)
        
        db_session.refresh(sample_supplier)
        assert sample_supplier.performance_score == 85
        assert sample_supplier.performance_score != original_score


class TestForecastingService:
    """Test ForecastingService"""
    
    def test_simple_moving_average_forecast(self, db_session, sample_product):
        """Test simple moving average forecast"""
        service = ForecastingService(db_session)
        
        # Mock historical data (would normally come from transactions)
        with patch.object(service, '_get_historical_demand') as mock_demand:
            mock_demand.return_value = [10, 12, 8, 15, 20, 18, 14]
            
            forecast = service.simple_moving_average_forecast(sample_product.id, 7)
            
            assert 'forecast' in forecast
            assert 'method' in forecast
            assert forecast['method'] == 'simple_moving_average'
            assert len(forecast['forecast']) == 7
    
    def test_exponential_smoothing_forecast(self, db_session, sample_product):
        """Test exponential smoothing forecast"""
        service = ForecastingService(db_session)
        
        with patch.object(service, '_get_historical_demand') as mock_demand:
            mock_demand.return_value = [10, 12, 8, 15, 20, 18, 14, 16, 22, 19]
            
            forecast = service.exponential_smoothing_forecast(sample_product.id, 5)
            
            assert 'forecast' in forecast
            assert 'method' in forecast
            assert forecast['method'] == 'exponential_smoothing'
            assert len(forecast['forecast']) == 5


class TestOptimizationService:
    """Test OptimizationService"""
    
    def test_calculate_eoq(self, db_session):
        """Test Economic Order Quantity calculation"""
        service = OptimizationService(db_session)
        
        result = service.calculate_eoq(
            annual_demand=1000,
            ordering_cost=50,
            holding_cost=5
        )
        
        assert 'optimal_order_quantity' in result
        assert 'total_annual_cost' in result
        assert 'num_orders_per_year' in result
        assert result['optimal_order_quantity'] > 0
    
    def test_calculate_reorder_point(self, db_session):
        """Test reorder point calculation"""
        service = OptimizationService(db_session)
        
        result = service.calculate_reorder_point(
            daily_demand_avg=10,
            daily_demand_stddev=2,
            lead_time_days=7,
            service_level=0.95
        )
        
        assert 'reorder_point' in result
        assert 'safety_stock' in result
        assert result['reorder_point'] > 0
        assert result['safety_stock'] >= 0
    
    def test_calculate_safety_stock(self, db_session):
        """Test safety stock calculation"""
        service = OptimizationService(db_session)
        
        safety_stock = service.calculate_safety_stock(
            daily_demand_stddev=3,
            lead_time_days=5,
            service_level=0.95
        )
        
        assert safety_stock > 0
        assert isinstance(safety_stock, (int, float))
    
    def test_perform_abc_analysis(self, db_session, sample_product, sample_inventory):
        """Test ABC analysis"""
        service = OptimizationService(db_session)
        
        # Mock additional products for meaningful ABC analysis
        with patch.object(service, '_get_products_with_value') as mock_products:
            mock_products.return_value = [
                {'product_name': 'Product A', 'total_value': 10000, 'category': 'Electronics'},
                {'product_name': 'Product B', 'total_value': 5000, 'category': 'Tools'},
                {'product_name': 'Product C', 'total_value': 1000, 'category': 'Office'},
            ]
            
            result = service.perform_abc_analysis()
            
            assert len(result) == 3
            assert all('abc_category' in item for item in result)
            assert all('cumulative_percentage' in item for item in result)


class TestSimulationService:
    """Test SimulationService"""
    
    def test_initialize_sample_database(self, db_session):
        """Test sample database initialization"""
        service = SimulationService(db_session)
        
        result = service.initialize_sample_database()
        
        assert 'success' in result
        if result['success']:
            assert 'summary' in result
            summary = result['summary']
            assert 'suppliers_created' in summary
            assert 'products_created' in summary
            assert 'locations_created' in summary
    
    def test_generate_sample_transactions(self, db_session, sample_product, sample_location):
        """Test generating sample transactions"""
        service = SimulationService(db_session)
        
        transactions = service.generate_sample_transactions(
            num_transactions=5,
            products=[sample_product],
            locations=[sample_location]
        )
        
        assert len(transactions) == 5
        assert all(t.product_id == sample_product.id for t in transactions)
        assert all(t.location_id == sample_location.id for t in transactions)
    
    def test_simulate_demand_patterns(self, db_session):
        """Test demand pattern simulation"""
        service = SimulationService(db_session)
        
        demand_data = service.simulate_demand_patterns(
            num_days=30,
            base_demand=100,
            seasonality_factor=0.2,
            noise_factor=0.1
        )
        
        assert len(demand_data) == 30
        assert all('date' in day and 'demand' in day for day in demand_data)
        assert all(day['demand'] > 0 for day in demand_data)
