"""
Tests for AI agent system
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.agent.llm_client import LLMClient
from src.agent.tools import InventoryQueryTool, ForecastTool, OptimizationTool
from src.agent.agent import InventoryAgent
from src.agent.memory import ConversationMemory


class TestLLMClient:
    """Test LLM Client"""
    
    def test_client_initialization(self):
        """Test LLM client initialization"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            client = LLMClient(primary_provider='openai')
            assert client.primary_provider == 'openai'
            assert 'openai' in client.available_providers
    
    @patch('openai.OpenAI')
    def test_openai_completion(self, mock_openai):
        """Test OpenAI completion"""
        # Mock OpenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Test response"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            client = LLMClient(primary_provider='openai')
            response = client.generate_response([{"role": "user", "content": "Hello"}])
            
            assert response == "Test response"
            mock_client.chat.completions.create.assert_called_once()
    
    def test_fallback_mechanism(self):
        """Test LLM fallback mechanism"""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            client = LLMClient(primary_provider='openai')  # Primary not available
            
            with patch.object(client, '_call_openai', side_effect=Exception("API Error")):
                with patch.object(client, '_call_anthropic', return_value="Fallback response"):
                    response = client.generate_response([{"role": "user", "content": "Hello"}])
                    assert response == "Fallback response"


class TestConversationMemory:
    """Test Conversation Memory"""
    
    def test_memory_initialization(self):
        """Test memory initialization"""
        memory = ConversationMemory(max_history_length=5)
        assert len(memory.history) == 0
        assert memory.max_history_length == 5
    
    def test_add_message(self):
        """Test adding messages to memory"""
        memory = ConversationMemory()
        memory.add_message("user", "Hello")
        memory.add_message("assistant", "Hi there!")
        
        assert len(memory.history) == 2
        assert memory.history[0]["role"] == "user"
        assert memory.history[0]["content"] == "Hello"
        assert memory.history[1]["role"] == "assistant"
    
    def test_history_length_limit(self):
        """Test history length limiting"""
        memory = ConversationMemory(max_history_length=3)
        
        for i in range(5):
            memory.add_message("user", f"Message {i}")
        
        assert len(memory.history) == 3
        assert memory.history[0]["content"] == "Message 2"  # Oldest messages removed
    
    def test_context_management(self):
        """Test context management"""
        memory = ConversationMemory()
        memory.update_context("current_product", "SKU-123")
        memory.update_context("location", "Warehouse A")
        
        assert memory.get_context("current_product") == "SKU-123"
        assert memory.get_context("location") == "Warehouse A"
        assert memory.get_context("nonexistent", "default") == "default"
    
    def test_clear_operations(self):
        """Test clearing memory and context"""
        memory = ConversationMemory()
        memory.add_message("user", "Hello")
        memory.update_context("test", "value")
        
        memory.clear_history()
        assert len(memory.history) == 0
        
        memory.clear_context()
        assert len(memory.context) == 0


class TestInventoryTools:
    """Test inventory-related tools"""
    
    def test_inventory_query_tool(self, db_session, sample_inventory):
        """Test inventory query tool"""
        mock_service = Mock()
        mock_service.get_product_by_sku.return_value = sample_inventory.product
        mock_service.get_inventory_by_product_location.return_value = sample_inventory
        
        tool = InventoryQueryTool(mock_service)
        result = tool.run(f"stock level for {sample_inventory.product.sku}")
        
        assert "stock" in result.lower() or "inventory" in result.lower()
        mock_service.get_product_by_sku.assert_called()
    
    def test_forecast_tool(self, db_session, sample_product):
        """Test forecasting tool"""
        mock_service = Mock()
        mock_forecast = {
            'forecast': [{'date': '2024-01-01', 'predicted_demand': 15}],
            'method': 'exponential_smoothing'
        }
        mock_service.exponential_smoothing_forecast.return_value = mock_forecast
        
        tool = ForecastTool(mock_service)
        result = tool.run(f"forecast for product {sample_product.id}")
        
        assert "forecast" in result.lower()
        mock_service.exponential_smoothing_forecast.assert_called()
    
    def test_optimization_tool(self, db_session):
        """Test optimization tool"""
        mock_service = Mock()
        mock_eoq = {
            'optimal_order_quantity': 100,
            'total_annual_cost': 500,
            'num_orders_per_year': 10
        }
        mock_service.calculate_eoq.return_value = mock_eoq
        
        tool = OptimizationTool(mock_service)
        result = tool.run("calculate EOQ for annual demand 1000, ordering cost 50, holding cost 5")
        
        assert "100" in result  # Should contain the EOQ result
        mock_service.calculate_eoq.assert_called()


class TestInventoryAgent:
    """Test main inventory agent"""
    
    def test_agent_initialization(self, db_session):
        """Test agent initialization"""
        mock_inventory_service = Mock()
        mock_forecasting_service = Mock()
        mock_optimization_service = Mock()
        
        agent = InventoryAgent(
            mock_inventory_service,
            mock_forecasting_service,
            mock_optimization_service
        )
        
        assert agent.inventory_service == mock_inventory_service
        assert agent.forecasting_service == mock_forecasting_service
        assert agent.optimization_service == mock_optimization_service
        assert len(agent.tools) > 0  # Should have tools loaded
    
    @patch('ai4supplychain.agent.llm_client.LLMClient')
    def test_agent_chat(self, mock_llm_class, db_session):
        """Test agent chat functionality"""
        # Mock LLM client
        mock_llm = Mock()
        mock_llm.generate_response.return_value = "I can help you with inventory management."
        mock_llm_class.return_value = mock_llm
        
        # Mock services
        mock_inventory_service = Mock()
        mock_forecasting_service = Mock()
        mock_optimization_service = Mock()
        
        agent = InventoryAgent(
            mock_inventory_service,
            mock_forecasting_service,
            mock_optimization_service
        )
        
        response = agent.chat("What's my current stock?")
        
        assert isinstance(response, str)
        assert len(response) > 0
        mock_llm.generate_response.assert_called()
    
    def test_agent_capabilities(self, db_session):
        """Test agent capabilities reporting"""
        mock_inventory_service = Mock()
        mock_forecasting_service = Mock()
        mock_optimization_service = Mock()
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = InventoryAgent(
                mock_inventory_service,
                mock_forecasting_service,
                mock_optimization_service
            )
            
            capabilities = agent.get_capabilities()
            
            assert 'agent_available' in capabilities
            assert 'llm_providers' in capabilities
            assert 'tools_available' in capabilities
            assert isinstance(capabilities['llm_providers'], list)
    
    def test_tool_execution(self, db_session):
        """Test tool execution through agent"""
        mock_inventory_service = Mock()
        mock_inventory_service.get_inventory_summary.return_value = {
            'total_products': 10,
            'total_locations': 2,
            'low_stock_items': 3
        }
        
        mock_forecasting_service = Mock()
        mock_optimization_service = Mock()
        
        agent = InventoryAgent(
            mock_inventory_service,
            mock_forecasting_service,
            mock_optimization_service
        )
        
        # Find the inventory tool
        inventory_tool = None
        for tool in agent.tools:
            if hasattr(tool, 'name') and 'inventory' in tool.name.lower():
                inventory_tool = tool
                break
        
        if inventory_tool:
            result = inventory_tool.run("get summary")
            assert "10" in result or "products" in result.lower()
            mock_inventory_service.get_inventory_summary.assert_called()
