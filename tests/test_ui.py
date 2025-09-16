"""
Tests for UI components
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import streamlit as st
from src.ui.components.charts import render_forecast_chart, render_abc_chart
from src.ui.components.tables import render_product_table, render_supplier_table, render_transaction_table
from src.ui.components.forms import render_product_form, render_supplier_form, render_transaction_form
import pandas as pd


class TestChartComponents:
    """Test chart rendering components"""
    
    @patch('streamlit.plotly_chart')
    @patch('plotly.express.line')
    def test_render_forecast_chart(self, mock_line, mock_plotly_chart):
        """Test forecast chart rendering"""
        forecast_data = {
            "forecast": [
                {"date": "2024-01-01", "predicted_demand": 15},
                {"date": "2024-01-02", "predicted_demand": 18},
                {"date": "2024-01-03", "predicted_demand": 20}
            ]
        }
        
        # Mock plotly figure
        mock_fig = Mock()
        mock_line.return_value = mock_fig
        
        with patch('streamlit.subheader'):
            render_forecast_chart(forecast_data)
            
            # Verify plotly line chart was called
            mock_line.assert_called_once()
            # Verify streamlit plotly_chart was called
            mock_plotly_chart.assert_called_once_with(mock_fig, use_container_width=True)
    
    @patch('streamlit.warning')
    def test_render_forecast_chart_no_data(self, mock_warning):
        """Test forecast chart with no data"""
        forecast_data = {}
        
        with patch('streamlit.subheader'):
            render_forecast_chart(forecast_data)
            
            mock_warning.assert_called_once_with("No forecast data available to render chart.")
    
    @patch('streamlit.plotly_chart')
    @patch('plotly.express.bar')
    def test_render_abc_chart(self, mock_bar, mock_plotly_chart):
        """Test ABC analysis chart rendering"""
        abc_data = pd.DataFrame([
            {"product_name": "Product A", "cumulative_percentage": 60, "category": "Electronics", "abc_category": "A", "total_value": 10000},
            {"product_name": "Product B", "cumulative_percentage": 80, "category": "Tools", "abc_category": "B", "total_value": 5000},
            {"product_name": "Product C", "cumulative_percentage": 100, "category": "Office", "abc_category": "C", "total_value": 1000}
        ])
        
        mock_fig = Mock()
        mock_bar.return_value = mock_fig
        
        with patch('streamlit.subheader'):
            render_abc_chart(abc_data)
            
            mock_bar.assert_called_once()
            mock_plotly_chart.assert_called_once_with(mock_fig, use_container_width=True)
    
    @patch('streamlit.warning')
    def test_render_abc_chart_empty_data(self, mock_warning):
        """Test ABC chart with empty data"""
        abc_data = pd.DataFrame()
        
        with patch('streamlit.subheader'):
            render_abc_chart(abc_data)
            
            mock_warning.assert_called_once_with("No data for ABC analysis chart.")


class TestTableComponents:
    """Test table rendering components"""
    
    @patch('streamlit.dataframe')
    def test_render_product_table(self, mock_dataframe):
        """Test product table rendering"""
        mock_products = [
            Mock(to_dict=lambda: {"sku": "PROD-001", "name": "Product 1", "category": "Electronics"}),
            Mock(to_dict=lambda: {"sku": "PROD-002", "name": "Product 2", "category": "Tools"})
        ]
        
        render_product_table(mock_products)
        
        mock_dataframe.assert_called_once()
        # Verify DataFrame was created with product data
        call_args = mock_dataframe.call_args[0][0]
        assert len(call_args) == 2
    
    @patch('streamlit.dataframe')
    def test_render_supplier_table(self, mock_dataframe):
        """Test supplier table rendering"""
        mock_suppliers = [
            Mock(to_dict=lambda: {"supplier_id": "SUPP-001", "name": "Supplier 1", "lead_time_days": 5}),
            Mock(to_dict=lambda: {"supplier_id": "SUPP-002", "name": "Supplier 2", "lead_time_days": 7})
        ]
        
        render_supplier_table(mock_suppliers)
        
        mock_dataframe.assert_called_once()
        call_args = mock_dataframe.call_args[0][0]
        assert len(call_args) == 2
    
    @patch('streamlit.dataframe')
    def test_render_transaction_table(self, mock_dataframe):
        """Test transaction table rendering"""
        mock_transactions = [
            Mock(to_dict=lambda: {"transaction_id": "TXN-001", "transaction_type": "receipt", "quantity": 50}),
            Mock(to_dict=lambda: {"transaction_id": "TXN-002", "transaction_type": "shipment", "quantity": 25})
        ]
        
        render_transaction_table(mock_transactions)
        
        mock_dataframe.assert_called_once()
        call_args = mock_dataframe.call_args[0][0]
        assert len(call_args) == 2


class TestFormComponents:
    """Test form rendering components"""
    
    @patch('streamlit.form_submit_button')
    @patch('streamlit.number_input')
    @patch('streamlit.text_input')
    @patch('streamlit.text_area')
    @patch('streamlit.form')
    @patch('streamlit.hidden_input')
    def test_render_product_form_new(self, mock_hidden, mock_form, mock_text_area, 
                                   mock_text_input, mock_number_input, mock_submit):
        """Test rendering product form for new product"""
        # Mock form context manager
        mock_form.return_value.__enter__ = Mock()
        mock_form.return_value.__exit__ = Mock()
        
        # Mock form inputs
        mock_text_input.side_effect = ["SKU-001", "Test Product", "Electronics"]
        mock_text_area.return_value = "Test description"
        mock_number_input.side_effect = [25.50, 1, 10, 50]
        mock_submit.return_value = True
        mock_hidden.return_value = None
        
        with patch('streamlit.form'):
            result = render_product_form()
            
            # Verify form was created
            assert mock_text_input.call_count >= 3  # SKU, name, category
            assert mock_text_area.called  # Description
            assert mock_number_input.call_count >= 4  # Cost, supplier_id, reorder_point, reorder_quantity
    
    @patch('streamlit.form_submit_button')
    @patch('streamlit.number_input')
    @patch('streamlit.text_input')
    @patch('streamlit.text_area')
    @patch('streamlit.form')
    @patch('streamlit.hidden_input')
    def test_render_supplier_form_new(self, mock_hidden, mock_form, mock_text_area,
                                    mock_text_input, mock_number_input, mock_submit):
        """Test rendering supplier form for new supplier"""
        mock_form.return_value.__enter__ = Mock()
        mock_form.return_value.__exit__ = Mock()
        
        mock_text_input.side_effect = ["SUPP-001", "Test Supplier", "NET30"]
        mock_text_area.return_value = '{"email": "test@supplier.com"}'
        mock_number_input.side_effect = [7, 1]
        mock_submit.return_value = True
        mock_hidden.return_value = None
        
        with patch('streamlit.form'):
            result = render_supplier_form()
            
            assert mock_text_input.call_count >= 3
            assert mock_text_area.called
            assert mock_number_input.call_count >= 2
    
    @patch('streamlit.form_submit_button')
    @patch('streamlit.selectbox')
    @patch('streamlit.number_input')
    @patch('streamlit.text_input')
    @patch('streamlit.text_area')
    @patch('streamlit.form')
    @patch('streamlit.hidden_input')
    def test_render_transaction_form_new(self, mock_hidden, mock_form, mock_text_area,
                                       mock_text_input, mock_number_input, 
                                       mock_selectbox, mock_submit):
        """Test rendering transaction form for new transaction"""
        mock_form.return_value.__enter__ = Mock()
        mock_form.return_value.__exit__ = Mock()
        
        mock_number_input.side_effect = [1, 1, 50]  # product_id, location_id, quantity
        mock_selectbox.return_value = "receipt"
        mock_text_input.side_effect = ["PO-12345", "test_user"]
        mock_text_area.return_value = "Test notes"
        mock_submit.return_value = True
        mock_hidden.return_value = None
        
        with patch('streamlit.form'):
            result = render_transaction_form()
            
            assert mock_number_input.call_count >= 3
            assert mock_selectbox.called
            assert mock_text_input.call_count >= 2
            assert mock_text_area.called


class TestUIIntegration:
    """Test UI integration scenarios"""
    
    @patch('ai4supplychain.services.inventory.InventoryService')
    def test_dashboard_with_data(self, mock_service_class):
        """Test dashboard rendering with data"""
        mock_service = Mock()
        mock_service.get_inventory_summary.return_value = {
            'total_products': 10,
            'total_locations': 3,
            'total_inventory_value': 25000.0,
            'low_stock_items': 2,
            'recent_transactions': 15
        }
        mock_service_class.return_value = mock_service
        
        with patch('streamlit.header'), \
             patch('streamlit.columns') as mock_columns, \
             patch('streamlit.metric') as mock_metric, \
             patch('streamlit.subheader'), \
             patch('streamlit.info'):
            
            # Mock columns
            mock_col = Mock()
            mock_columns.return_value = [mock_col, mock_col, mock_col, mock_col]
            
            from src.ui.pages.dashboard import render_dashboard_page
            render_dashboard_page()
            
            # Verify metrics were displayed
            assert mock_metric.call_count == 4  # Should display 4 metrics
    
    @patch('ai4supplychain.services.inventory.InventoryService')
    def test_dashboard_without_data(self, mock_service_class):
        """Test dashboard rendering without data (error case)"""
        mock_service_class.side_effect = Exception("Database not initialized")
        
        with patch('streamlit.header'), \
             patch('streamlit.warning') as mock_warning, \
             patch('streamlit.subheader'), \
             patch('streamlit.markdown'), \
             patch('streamlit.code'):
            
            from src.ui.pages.dashboard import render_dashboard_page
            render_dashboard_page()
            
            # Verify warning was shown
            mock_warning.assert_called_once()
    
    def test_navigation_structure(self):
        """Test main navigation structure"""
        with patch('streamlit.set_page_config'), \
             patch('streamlit.title'), \
             patch('streamlit.subheader'), \
             patch('streamlit.sidebar.title'), \
             patch('streamlit.sidebar.selectbox') as mock_selectbox:
            
            # Mock page selection
            mock_selectbox.return_value = "🏠 Dashboard"
            
            with patch('src.ui.pages.dashboard.render_dashboard_page') as mock_dashboard:
                from src.ui.main import main
                main()
                
                # Verify dashboard page was called
                mock_dashboard.assert_called_once()
    
    @patch('ai4supplychain.agent.agent.InventoryAgent')
    def test_chat_interface(self, mock_agent_class):
        """Test chat interface functionality"""
        mock_agent = Mock()
        mock_agent.chat.return_value = "I can help you with inventory management!"
        mock_agent_class.return_value = mock_agent
        
        with patch('streamlit.title'), \
             patch('streamlit.markdown'), \
             patch('streamlit.session_state', {'agent': mock_agent, 'chat_history': []}), \
             patch('streamlit.chat_message'), \
             patch('streamlit.chat_input') as mock_input, \
             patch('streamlit.spinner'):
            
            mock_input.return_value = "What's my stock level?"
            
            from src.ui.pages.chat import render_chat_page
            render_chat_page()
            
            # Verify agent was called if input was provided
            if mock_input.return_value:
                mock_agent.chat.assert_called_with("What's my stock level?")
