"""
Table components for the Streamlit UI
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

def display_product_table(products: List[Dict[str, Any]], 
                         show_actions: bool = True,
                         selectable: bool = False) -> Optional[List[str]]:
    """Display a formatted product table with optional actions"""
    
    if not products:
        st.info("No products to display")
        return None
    
    # Convert to DataFrame
    df = pd.DataFrame(products)
    
    # Format columns for better display
    if 'unit_cost' in df.columns:
        df['Unit Cost'] = df['unit_cost'].apply(lambda x: f"${float(x):.2f}")
    
    if 'reorder_point' in df.columns:
        df['Reorder Point'] = df['reorder_point'].astype(str) + ' units'
    
    if 'reorder_quantity' in df.columns:
        df['Reorder Qty'] = df['reorder_quantity'].astype(str) + ' units'
    
    # Select display columns
    display_columns = []
    column_mapping = {
        'sku': 'SKU',
        'name': 'Product Name',
        'category': 'Category',
        'Unit Cost': 'Unit Cost',
        'Reorder Point': 'Reorder Point',
        'Reorder Qty': 'Reorder Qty',
        'supplier_name': 'Supplier'
    }
    
    for col in df.columns:
        if col in column_mapping:
            display_columns.append(col)
    
    # Display table
    if selectable:
        selected_rows = st.dataframe(
            df[display_columns].rename(columns=column_mapping),
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="multi-row"
        )
        return selected_rows.selection.rows if hasattr(selected_rows, 'selection') else []
    else:
        st.dataframe(
            df[display_columns].rename(columns=column_mapping),
            use_container_width=True,
            hide_index=True
        )
        return None

def display_inventory_table(inventory_data: List[Dict[str, Any]], 
                           show_alerts: bool = True) -> None:
    """Display inventory levels table with color coding"""
    
    if not inventory_data:
        st.info("No inventory data to display")
        return
    
    df = pd.DataFrame(inventory_data)
    
    # Add status column
    def get_stock_status(row):
        quantity = row.get('quantity', 0)
        reorder_point = row.get('reorder_point', 0)
        
        if quantity == 0:
            return '🔴 Out of Stock'
        elif quantity <= reorder_point:
            return '🟡 Low Stock'
        else:
            return '🟢 In Stock'
    
    df['Status'] = df.apply(get_stock_status, axis=1)
    
    # Format columns
    if 'quantity' in df.columns:
        df['Current Stock'] = df['quantity'].astype(str) + ' units'
    
    if 'unit_cost' in df.columns and 'quantity' in df.columns:
        df['Total Value'] = (df['unit_cost'] * df['quantity']).apply(lambda x: f"${x:,.2f}")
    
    # Select display columns
    display_cols = ['sku', 'product_name', 'Current Stock', 'Status', 'location']
    if 'Total Value' in df.columns:
        display_cols.append('Total Value')
    
    # Filter available columns
    display_cols = [col for col in display_cols if col in df.columns]
    
    # Apply styling
    def style_status(val):
        if '🔴' in val:
            return 'background-color: #ffebee'
        elif '🟡' in val:
            return 'background-color: #fff3e0'
        elif '🟢' in val:
            return 'background-color: #e8f5e8'
        return ''
    
    styled_df = df[display_cols].style.applymap(style_status, subset=['Status'])
    
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
    
    # Show alerts summary
    if show_alerts:
        out_of_stock = len(df[df['Status'].str.contains('Out of Stock')])
        low_stock = len(df[df['Status'].str.contains('Low Stock')])
        
        if out_of_stock > 0 or low_stock > 0:
            col1, col2 = st.columns(2)
            with col1:
                if out_of_stock > 0:
                    st.error(f"🔴 {out_of_stock} items out of stock")
            with col2:
                if low_stock > 0:
                    st.warning(f"🟡 {low_stock} items low on stock")

def display_supplier_table(suppliers: List[Dict[str, Any]], 
                          show_performance: bool = True) -> None:
    """Display supplier information table"""
    
    if not suppliers:
        st.info("No suppliers to display")
        return
    
    df = pd.DataFrame(suppliers)
    
    # Format columns
    if 'lead_time_days' in df.columns:
        df['Lead Time'] = df['lead_time_days'].astype(str) + ' days'
    
    if 'performance_rating' in df.columns:
        df['Rating'] = df['performance_rating'].apply(
            lambda x: f"{float(x):.1f}/5.0" if pd.notna(x) else "N/A"
        )
    
    if 'minimum_order_qty' in df.columns:
        df['Min Order'] = df['minimum_order_qty'].astype(str) + ' units'
    
    # Select display columns
    display_cols = ['supplier_id', 'name', 'Lead Time', 'payment_terms', 'Min Order']
    if show_performance and 'Rating' in df.columns:
        display_cols.append('Rating')
    
    # Filter available columns
    display_cols = [col for col in display_cols if col in df.columns]
    
    # Column mapping for display
    column_mapping = {
        'supplier_id': 'Supplier ID',
        'name': 'Supplier Name',
        'Lead Time': 'Lead Time',
        'payment_terms': 'Payment Terms',
        'Min Order': 'Min Order Qty',
        'Rating': 'Performance Rating'
    }
    
    st.dataframe(
        df[display_cols].rename(columns=column_mapping),
        use_container_width=True,
        hide_index=True
    )

def display_transaction_table(transactions: List[Dict[str, Any]], 
                             show_details: bool = True) -> None:
    """Display transaction history table"""
    
    if not transactions:
        st.info("No transactions to display")
        return
    
    df = pd.DataFrame(transactions)
    
    # Format timestamp
    if 'timestamp' in df.columns:
        df['Date'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
    
    # Format quantity with direction indicators
    if 'quantity' in df.columns:
        df['Quantity'] = df.apply(lambda row: 
            f"+{row['quantity']} units" if row['quantity'] > 0 
            else f"{row['quantity']} units", axis=1)
    
    # Add transaction type icons
    if 'transaction_type' in df.columns:
        type_icons = {
            'receipt': '📦 Receipt',
            'shipment': '📤 Shipment',
            'adjustment': '⚖️ Adjustment',
            'transfer': '🔄 Transfer',
            'expected_receipt': '⏳ Expected Receipt'
        }
        df['Type'] = df['transaction_type'].map(type_icons).fillna(df['transaction_type'])
    
    # Select display columns
    display_cols = ['Date', 'sku', 'Type', 'Quantity', 'location']
    if show_details:
        if 'reference_document' in df.columns:
            display_cols.append('reference_document')
        if 'user_id' in df.columns:
            display_cols.append('user_id')
    
    # Filter available columns
    display_cols = [col for col in display_cols if col in df.columns]
    
    # Column mapping
    column_mapping = {
        'Date': 'Date & Time',
        'sku': 'SKU',
        'Type': 'Transaction Type',
        'Quantity': 'Quantity',
        'location': 'Location',
        'reference_document': 'Reference',
        'user_id': 'User'
    }
    
    st.dataframe(
        df[display_cols].rename(columns=column_mapping),
        use_container_width=True,
        hide_index=True
    )

def display_forecast_comparison_table(forecasts: List[Dict[str, Any]]) -> None:
    """Display forecast comparison table"""
    
    if not forecasts:
        st.info("No forecast data to display")
        return
    
    df = pd.DataFrame(forecasts)
    
    # Format columns
    if 'total_forecast' in df.columns:
        df['Total Forecast'] = df['total_forecast'].apply(lambda x: f"{x:.1f} units")
    
    if 'daily_average' in df.columns:
        df['Daily Avg'] = df['daily_average'].apply(lambda x: f"{x:.1f} units/day")
    
    if 'forecast_method' in df.columns:
        df['Method'] = df['forecast_method'].str.replace('_', ' ').str.title()
    
    if 'accuracy' in df.columns:
        df['Accuracy'] = df['accuracy'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A")
    
    # Select display columns
    display_cols = ['sku', 'product_name', 'Method', 'Total Forecast', 'Daily Avg']
    if 'Accuracy' in df.columns:
        display_cols.append('Accuracy')
    
    # Filter available columns
    display_cols = [col for col in display_cols if col in df.columns]
    
    st.dataframe(df[display_cols], use_container_width=True, hide_index=True)

def display_optimization_results_table(results: List[Dict[str, Any]]) -> None:
    """Display optimization results table"""
    
    if not results:
        st.info("No optimization results to display")
        return
    
    df = pd.DataFrame(results)
    
    # Format columns
    if 'current_eoq' in df.columns and 'optimal_eoq' in df.columns:
        df['EOQ Change'] = (df['optimal_eoq'] - df['current_eoq']).apply(
            lambda x: f"{x:+.0f} units" if x != 0 else "No change"
        )
    
    if 'potential_savings' in df.columns:
        df['Savings'] = df['potential_savings'].apply(lambda x: f"${x:.2f}")
    
    if 'optimization_status' in df.columns:
        status_icons = {
            'optimal': '✅ Optimal',
            'needs_review': '⚠️ Needs Review',
            'critical': '🔴 Critical'
        }
        df['Status'] = df['optimization_status'].map(status_icons).fillna(df['optimization_status'])
    
    # Select display columns
    display_cols = ['sku', 'product_name', 'EOQ Change', 'Savings', 'Status']
    
    # Filter available columns
    display_cols = [col for col in display_cols if col in df.columns]
    
    # Apply conditional formatting
    def style_status(val):
        if '✅' in str(val):
            return 'background-color: #e8f5e8'
        elif '⚠️' in str(val):
            return 'background-color: #fff3e0'
        elif '🔴' in str(val):
            return 'background-color: #ffebee'
        return ''
    
    styled_df = df[display_cols].style.applymap(style_status, subset=['Status'])
    
    st.dataframe(styled_df, use_container_width=True, hide_index=True)

def display_abc_analysis_table(abc_data: List[Dict[str, Any]]) -> None:
    """Display ABC analysis results table"""
    
    if not abc_data:
        st.info("No ABC analysis data to display")
        return
    
    df = pd.DataFrame(abc_data)
    
    # Sort by annual value
    df = df.sort_values('annual_value', ascending=False)
    
    # Calculate cumulative percentage
    df['cumulative_value'] = df['annual_value'].cumsum()
    total_value = df['annual_value'].sum()
    df['cumulative_percentage'] = (df['cumulative_value'] / total_value) * 100
    
    # Assign ABC categories
    df['abc_category'] = 'C'
    df.loc[df['cumulative_percentage'] <= 80, 'abc_category'] = 'A'
    df.loc[(df['cumulative_percentage'] > 80) & (df['cumulative_percentage'] <= 95), 'abc_category'] = 'B'
    
    # Format columns
    df['Annual Value'] = df['annual_value'].apply(lambda x: f"${x:,.2f}")
    df['Cumulative %'] = df['cumulative_percentage'].apply(lambda x: f"{x:.1f}%")
    df['Category'] = df['abc_category']
    
    # Select display columns
    display_cols = ['sku', 'product_name', 'Category', 'Annual Value', 'Cumulative %']
    
    # Apply category styling
    def style_category(val):
        if val == 'A':
            return 'background-color: #ffebee; font-weight: bold'
        elif val == 'B':
            return 'background-color: #fff3e0'
        elif val == 'C':
            return 'background-color: #e8f5e8'
        return ''
    
    styled_df = df[display_cols].style.applymap(style_category, subset=['Category'])
    
    st.dataframe(styled_df, use_container_width=True, hide_index=True)

def display_performance_metrics_table(metrics: List[Dict[str, Any]], 
                                     metric_type: str = "general") -> None:
    """Display performance metrics table with appropriate formatting"""
    
    if not metrics:
        st.info("No performance metrics to display")
        return
    
    df = pd.DataFrame(metrics)
    
    if metric_type == "supplier":
        # Format supplier-specific metrics
        if 'on_time_delivery_rate' in df.columns:
            df['On-Time Delivery'] = (df['on_time_delivery_rate'] * 100).apply(lambda x: f"{x:.1f}%")
        
        if 'quality_rating' in df.columns:
            df['Quality Rating'] = df['quality_rating'].apply(lambda x: f"{x:.1f}/5.0")
        
        if 'total_value' in df.columns:
            df['Total Value'] = df['total_value'].apply(lambda x: f"${x:,.2f}")
        
        display_cols = ['supplier_name', 'On-Time Delivery', 'Quality Rating', 'Total Value']
    
    elif metric_type == "inventory":
        # Format inventory-specific metrics
        if 'turnover_ratio' in df.columns:
            df['Turnover Ratio'] = df['turnover_ratio'].apply(lambda x: f"{x:.1f}x")
        
        if 'days_of_stock' in df.columns:
            df['Days of Stock'] = df['days_of_stock'].apply(lambda x: f"{x:.0f} days")
        
        display_cols = ['sku', 'product_name', 'Turnover Ratio', 'Days of Stock']
    
    else:
        # General metrics formatting
        display_cols = list(df.columns)
    
    # Filter available columns
    display_cols = [col for col in display_cols if col in df.columns]
    
    st.dataframe(df[display_cols], use_container_width=True, hide_index=True)

def create_editable_table(data: List[Dict[str, Any]], 
                         editable_columns: List[str],
                         key: str = "editable_table") -> pd.DataFrame:
    """Create an editable table using st.data_editor"""
    
    if not data:
        st.info("No data to edit")
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    
    # Configure column types for editing
    column_config = {}
    for col in editable_columns:
        if col in df.columns:
            if df[col].dtype in ['int64', 'float64']:
                column_config[col] = st.column_config.NumberColumn(
                    col,
                    help=f"Edit {col}",
                    min_value=0,
                    step=1 if df[col].dtype == 'int64' else 0.01
                )
            else:
                column_config[col] = st.column_config.TextColumn(
                    col,
                    help=f"Edit {col}"
                )
    
    # Create editable dataframe
    edited_df = st.data_editor(
        df,
        column_config=column_config,
        disabled=[col for col in df.columns if col not in editable_columns],
        use_container_width=True,
        hide_index=True,
        key=key
    )
    
    return edited_df

def display_summary_table(summary_data: Dict[str, Any], 
                         title: str = "Summary") -> None:
    """Display a summary table with key-value pairs"""
    
    st.subheader(title)
    
    # Convert to list of dictionaries for better display
    summary_list = []
    for key, value in summary_data.items():
        # Format key for display
        display_key = key.replace('_', ' ').title()
        
        # Format value based on type
        if isinstance(value, float):
            if 'percentage' in key.lower() or 'rate' in key.lower():
                display_value = f"{value:.1f}%"
            elif 'cost' in key.lower() or 'value' in key.lower():
                display_value = f"${value:,.2f}"
            else:
                display_value = f"{value:.2f}"
        elif isinstance(value, int):
            display_value = f"{value:,}"
        else:
            display_value = str(value)
        
        summary_list.append({
            "Metric": display_key,
            "Value": display_value
        })
    
    df = pd.DataFrame(summary_list)
    st.dataframe(df, use_container_width=True, hide_index=True)

def display_comparison_table(data1: List[Dict[str, Any]], 
                           data2: List[Dict[str, Any]],
                           labels: tuple = ("Current", "Proposed"),
                           key_column: str = "sku") -> None:
    """Display a comparison table between two datasets"""
    
    if not data1 or not data2:
        st.info("Insufficient data for comparison")
        return
    
    df1 = pd.DataFrame(data1)
    df2 = pd.DataFrame(data2)
    
    # Merge dataframes on key column
    comparison_df = df1.merge(df2, on=key_column, suffixes=(f'_{labels[0]}', f'_{labels[1]}'))
    
    # Select comparison columns
    comparison_cols = [key_column]
    
    # Find common columns for comparison
    for col in df1.columns:
        if col != key_column and col in df2.columns:
            comparison_cols.extend([f'{col}_{labels[0]}', f'{col}_{labels[1]}'])
    
    # Filter available columns
    comparison_cols = [col for col in comparison_cols if col in comparison_df.columns]
    
    st.dataframe(
        comparison_df[comparison_cols],
        use_container_width=True,
        hide_index=True
    )

def export_table_to_csv(df: pd.DataFrame, filename: str = None) -> None:
    """Add export functionality to any table"""
    
    if filename is None:
        filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Export to CSV",
        data=csv,
        file_name=filename,
        mime="text/csv",
        use_container_width=True
    )
