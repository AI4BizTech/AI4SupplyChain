"""
Tests for FastAPI endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from src.api.main import app
from src.data.inventory import Product, Supplier, Transaction


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    return Mock()


class TestInventoryAPI:
    """Test inventory API endpoints"""
    
    def test_get_inventory_summary(self, client):
        """Test getting inventory summary"""
        with patch('ai4supplychain.api.inventory.get_database') as mock_db:
            mock_session = Mock()
            mock_db.return_value = mock_session
            
            with patch('ai4supplychain.services.inventory.InventoryService') as mock_service_class:
                mock_service = Mock()
                mock_service.get_inventory_summary.return_value = {
                    'total_products': 5,
                    'total_locations': 2,
                    'total_inventory_value': 10000.0,
                    'low_stock_items': 1
                }
                mock_service_class.return_value = mock_service
                
                response = client.get("/api/inventory/summary")
                
                assert response.status_code == 200
                data = response.json()
                assert data['total_products'] == 5
                assert data['total_locations'] == 2
    
    def test_get_low_stock_products(self, client):
        """Test getting low stock products"""
        with patch('ai4supplychain.api.inventory.get_database') as mock_db:
            mock_session = Mock()
            mock_db.return_value = mock_session
            
            with patch('ai4supplychain.services.inventory.InventoryService') as mock_service_class:
                mock_service = Mock()
                mock_product = Mock()
                mock_product.sku = "LOW-STOCK-001"
                mock_product.name = "Low Stock Product"
                mock_service.get_low_stock_products.return_value = [mock_product]
                mock_service_class.return_value = mock_service
                
                response = client.get("/api/inventory/low-stock")
                
                assert response.status_code == 200
                data = response.json()
                assert len(data) == 1


class TestSuppliersAPI:
    """Test suppliers API endpoints"""
    
    def test_create_supplier(self, client):
        """Test creating a supplier"""
        supplier_data = {
            "supplier_id": "SUPP001",
            "name": "Test Supplier",
            "contact_info": {"email": "test@supplier.com"},
            "lead_time_days": 5,
            "payment_terms": "NET30",
            "minimum_order_qty": 10
        }
        
        with patch('ai4supplychain.api.suppliers.get_database') as mock_db:
            mock_session = Mock()
            mock_db.return_value = mock_session
            
            with patch('ai4supplychain.services.suppliers.SupplierService') as mock_service_class:
                mock_service = Mock()
                mock_supplier = Mock()
                mock_supplier.id = 1
                mock_supplier.supplier_id = "SUPP001"
                mock_supplier.name = "Test Supplier"
                mock_service.create_supplier.return_value = mock_supplier
                mock_service_class.return_value = mock_service
                
                response = client.post("/api/suppliers/", json=supplier_data)
                
                assert response.status_code == 201
    
    def test_get_all_suppliers(self, client):
        """Test getting all suppliers"""
        with patch('ai4supplychain.api.suppliers.get_database') as mock_db:
            mock_session = Mock()
            mock_db.return_value = mock_session
            
            with patch('ai4supplychain.services.suppliers.SupplierService') as mock_service_class:
                mock_service = Mock()
                mock_suppliers = [Mock(id=1, name="Supplier 1"), Mock(id=2, name="Supplier 2")]
                mock_service.get_all_suppliers.return_value = mock_suppliers
                mock_service_class.return_value = mock_service
                
                response = client.get("/api/suppliers/")
                
                assert response.status_code == 200
                data = response.json()
                assert len(data) == 2


class TestTransactionsAPI:
    """Test transactions API endpoints"""
    
    def test_create_transaction(self, client):
        """Test creating a transaction"""
        transaction_data = {
            "transaction_id": "TXN001",
            "product_id": 1,
            "location_id": 1,
            "transaction_type": "receipt",
            "quantity": 50,
            "reference_document": "PO-12345",
            "user_id": "test_user",
            "notes": "Test transaction"
        }
        
        with patch('ai4supplychain.api.transactions.get_database') as mock_db:
            mock_session = Mock()
            mock_db.return_value = mock_session
            
            with patch('ai4supplychain.services.transactions.TransactionService') as mock_service_class:
                mock_service = Mock()
                mock_transaction = Mock()
                mock_transaction.id = 1
                mock_transaction.transaction_id = "TXN001"
                mock_service.create_transaction.return_value = mock_transaction
                mock_service_class.return_value = mock_service
                
                response = client.post("/api/transactions/", json=transaction_data)
                
                assert response.status_code == 201
    
    def test_upload_document_for_ocr(self, client):
        """Test uploading document for OCR processing"""
        # Create a mock file
        test_file_content = b"fake pdf content"
        
        with patch('ai4supplychain.api.transactions.get_database') as mock_db:
            mock_session = Mock()
            mock_db.return_value = mock_session
            
            with patch('ai4supplychain.services.transactions.TransactionService') as mock_service_class:
                mock_service = Mock()
                mock_result = {
                    "success": True,
                    "transactions_created": 2,
                    "ocr_data": {"extracted_text": "PO Number: 12345"},
                    "transactions": []
                }
                mock_service.process_uploaded_document.return_value = mock_result
                mock_service_class.return_value = mock_service
                
                response = client.post(
                    "/api/transactions/upload-document/",
                    files={"file": ("test.pdf", test_file_content, "application/pdf")},
                    data={"document_type": "purchase_order", "location_id": 1}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] == True
                assert data["transactions_created"] == 2


class TestForecastAPI:
    """Test forecast API endpoints"""
    
    def test_generate_forecast(self, client):
        """Test generating a forecast"""
        with patch('ai4supplychain.api.forecast.get_database') as mock_db:
            mock_session = Mock()
            mock_db.return_value = mock_session
            
            with patch('ai4supplychain.services.forecasting.ForecastingService') as mock_service_class:
                mock_service = Mock()
                mock_forecast = {
                    'forecast': [
                        {'date': '2024-01-01', 'predicted_demand': 15},
                        {'date': '2024-01-02', 'predicted_demand': 18}
                    ],
                    'method': 'exponential_smoothing',
                    'accuracy_metrics': {'mape': 5.2}
                }
                mock_service.exponential_smoothing_forecast.return_value = mock_forecast
                mock_service_class.return_value = mock_service
                
                response = client.post("/api/forecasts/1?horizon=7&method=exponential_smoothing")
                
                assert response.status_code == 200
                data = response.json()
                assert data['product_id'] == 1
                assert data['method'] == 'exponential_smoothing'
                assert 'forecast_data' in data
    
    def test_get_forecast_history(self, client):
        """Test getting forecast history"""
        with patch('ai4supplychain.api.forecast.get_database') as mock_db:
            mock_session = Mock()
            mock_db.return_value = mock_session
            
            with patch('ai4supplychain.services.forecasting.ForecastingService') as mock_service_class:
                mock_service = Mock()
                mock_history = [
                    {'forecast_id': 1, 'created_at': '2024-01-01', 'method': 'moving_average'},
                    {'forecast_id': 2, 'created_at': '2024-01-02', 'method': 'exponential_smoothing'}
                ]
                mock_service.get_forecast_history.return_value = mock_history
                mock_service_class.return_value = mock_service
                
                response = client.get("/api/forecasts/1")
                
                assert response.status_code == 200
                data = response.json()
                assert len(data) == 2


class TestChatAPI:
    """Test chat API endpoints"""
    
    def test_websocket_connection(self, client):
        """Test WebSocket connection for chat"""
        with patch('ai4supplychain.api.chat.get_database') as mock_db:
            mock_session = Mock()
            mock_db.return_value = mock_session
            
            with patch('ai4supplychain.agent.agent.InventoryAgent') as mock_agent_class:
                mock_agent = Mock()
                mock_agent.chat.return_value = "Hello! I'm your inventory assistant."
                mock_agent_class.return_value = mock_agent
                
                # Test WebSocket connection
                with client.websocket_connect("/api/ws/chat/test_client") as websocket:
                    # Should receive welcome message
                    welcome_data = websocket.receive_text()
                    assert "Hello" in welcome_data or "assistant" in welcome_data
                    
                    # Send a message
                    websocket.send_text("What's my inventory?")
                    
                    # Should receive typing indicator and response
                    typing_data = websocket.receive_text()
                    response_data = websocket.receive_text()
                    
                    assert "inventory assistant" in response_data


class TestAPIErrorHandling:
    """Test API error handling"""
    
    def test_404_error(self, client):
        """Test 404 error handling"""
        response = client.get("/api/nonexistent-endpoint")
        assert response.status_code == 404
    
    def test_validation_error(self, client):
        """Test validation error handling"""
        # Send invalid data to create supplier
        invalid_data = {
            "name": "",  # Empty name should cause validation error
            "lead_time_days": -1  # Negative lead time should be invalid
        }
        
        with patch('ai4supplychain.api.suppliers.get_database') as mock_db:
            mock_session = Mock()
            mock_db.return_value = mock_session
            
            response = client.post("/api/suppliers/", json=invalid_data)
            # Should return 422 for validation error or 400 for bad request
            assert response.status_code in [400, 422]
    
    def test_internal_server_error_handling(self, client):
        """Test internal server error handling"""
        with patch('ai4supplychain.api.inventory.get_database') as mock_db:
            mock_db.side_effect = Exception("Database connection failed")
            
            response = client.get("/api/inventory/summary")
            assert response.status_code == 500
