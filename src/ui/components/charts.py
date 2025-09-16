"""
Chart components for the Streamlit UI
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

def create_inventory_status_pie_chart(data: Dict[str, int], title: str = "Inventory Status Distribution") -> go.Figure:
    """Create a pie chart for inventory status distribution"""
    
    colors = {
        'In Stock': '#28a745',
        'Low Stock': '#ffc107', 
        'Out of Stock': '#dc3545',
        'Adequate': '#28a745',
        'Critical': '#dc3545',
        'Warning': '#ffc107'
    }
    
    labels = list(data.keys())
    values = list(data.values())
    
    # Map colors to labels
    chart_colors = [colors.get(label, '#6c757d') for label in labels]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker_colors=chart_colors,
        textinfo='label+percent',
        textposition='auto',
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
    )])
    
    fig.update_layout(
        title={
            'text': title,
            'x': 0.5,
            'xanchor': 'center'
        },
        showlegend=True,
        height=400
    )
    
    return fig

def create_category_value_bar_chart(data: List[Dict[str, Any]], title: str = "Inventory Value by Category") -> go.Figure:
    """Create a bar chart showing inventory value by category"""
    
    if not data:
        return go.Figure()
    
    df = pd.DataFrame(data)
    
    fig = px.bar(
        df,
        x='category',
        y='total_value',
        title=title,
        labels={'total_value': 'Total Value ($)', 'category': 'Category'},
        color='total_value',
        color_continuous_scale='Blues'
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=400,
        showlegend=False
    )
    
    # Format y-axis as currency
    fig.update_yaxis(tickformat='$,.0f')
    
    return fig

def create_stock_levels_chart(data: List[Dict[str, Any]], chart_type: str = "bar") -> go.Figure:
    """Create a chart showing stock levels across products"""
    
    if not data:
        return go.Figure()
    
    df = pd.DataFrame(data)
    
    if chart_type == "bar":
        fig = px.bar(
            df,
            x='sku',
            y='quantity',
            title="Current Stock Levels",
            labels={'quantity': 'Stock Quantity', 'sku': 'Product SKU'},
            color='quantity',
            color_continuous_scale='RdYlGn'
        )
        
        # Add reorder point line if available
        if 'reorder_point' in df.columns:
            for i, row in df.iterrows():
                fig.add_hline(
                    y=row['reorder_point'],
                    line_dash="dash",
                    line_color="red",
                    annotation_text=f"Reorder Point: {row['reorder_point']}"
                )
    
    else:  # scatter plot
        fig = px.scatter(
            df,
            x='sku',
            y='quantity',
            size='quantity',
            title="Stock Level Overview",
            labels={'quantity': 'Stock Quantity', 'sku': 'Product SKU'}
        )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=500
    )
    
    return fig

def create_demand_forecast_chart(historical_data: pd.DataFrame, forecast_data: pd.DataFrame, 
                                product_name: str = "Product") -> go.Figure:
    """Create a chart showing historical demand and forecast"""
    
    fig = go.Figure()
    
    # Add historical data
    if not historical_data.empty:
        fig.add_trace(go.Scatter(
            x=historical_data['date'],
            y=historical_data['demand'],
            mode='lines+markers',
            name='Historical Demand',
            line=dict(color='#1f77b4', width=2),
            marker=dict(size=4)
        ))
    
    # Add forecast data
    if not forecast_data.empty:
        fig.add_trace(go.Scatter(
            x=forecast_data['date'],
            y=forecast_data['forecast'],
            mode='lines+markers',
            name='Forecast',
            line=dict(color='#ff7f0e', width=2, dash='dash'),
            marker=dict(size=4)
        ))
        
        # Add confidence intervals if available
        if 'upper_bound' in forecast_data.columns and 'lower_bound' in forecast_data.columns:
            fig.add_trace(go.Scatter(
                x=forecast_data['date'],
                y=forecast_data['upper_bound'],
                mode='lines',
                line=dict(width=0),
                showlegend=False,
                hoverinfo='skip'
            ))
            
            fig.add_trace(go.Scatter(
                x=forecast_data['date'],
                y=forecast_data['lower_bound'],
                mode='lines',
                line=dict(width=0),
                fill='tonexty',
                fillcolor='rgba(255, 127, 14, 0.2)',
                name='Confidence Interval',
                hoverinfo='skip'
            ))
    
    fig.update_layout(
        title=f"Demand Forecast - {product_name}",
        xaxis_title="Date",
        yaxis_title="Demand (units)",
        hovermode='x unified',
        height=500
    )
    
    return fig

def create_supplier_performance_chart(data: List[Dict[str, Any]]) -> go.Figure:
    """Create a scatter plot showing supplier performance metrics"""
    
    if not data:
        return go.Figure()
    
    df = pd.DataFrame(data)
    
    fig = px.scatter(
        df,
        x='on_time_delivery_rate',
        y='quality_rating',
        size='total_orders',
        hover_data=['supplier_name', 'total_value'],
        title="Supplier Performance Analysis",
        labels={
            'on_time_delivery_rate': 'On-Time Delivery Rate (%)',
            'quality_rating': 'Quality Rating (1-5)',
            'total_orders': 'Total Orders'
        }
    )
    
    # Add quadrant lines
    fig.add_hline(y=3.5, line_dash="dot", line_color="gray", opacity=0.5)
    fig.add_vline(x=85, line_dash="dot", line_color="gray", opacity=0.5)
    
    # Add annotations for quadrants
    fig.add_annotation(x=95, y=4.5, text="Star Performers", showarrow=False, font=dict(color="green"))
    fig.add_annotation(x=75, y=4.5, text="Quality Focus", showarrow=False, font=dict(color="orange"))
    fig.add_annotation(x=95, y=2.5, text="Delivery Focus", showarrow=False, font=dict(color="orange"))
    fig.add_annotation(x=75, y=2.5, text="Needs Improvement", showarrow=False, font=dict(color="red"))
    
    fig.update_layout(height=500)
    
    return fig

def create_abc_analysis_chart(data: List[Dict[str, Any]]) -> go.Figure:
    """Create ABC analysis visualization"""
    
    if not data:
        return go.Figure()
    
    df = pd.DataFrame(data)
    
    # Sort by value and calculate cumulative percentage
    df = df.sort_values('annual_value', ascending=False)
    df['cumulative_value'] = df['annual_value'].cumsum()
    total_value = df['annual_value'].sum()
    df['cumulative_percentage'] = (df['cumulative_value'] / total_value) * 100
    
    # Assign ABC categories
    df['abc_category'] = 'C'
    df.loc[df['cumulative_percentage'] <= 80, 'abc_category'] = 'A'
    df.loc[(df['cumulative_percentage'] > 80) & (df['cumulative_percentage'] <= 95), 'abc_category'] = 'B'
    
    # Create the chart
    fig = go.Figure()
    
    # Add bars for individual products
    colors = {'A': '#ff4444', 'B': '#ffaa44', 'C': '#44ff44'}
    
    for category in ['A', 'B', 'C']:
        category_data = df[df['abc_category'] == category]
        fig.add_trace(go.Bar(
            x=category_data.index,
            y=category_data['annual_value'],
            name=f'Category {category}',
            marker_color=colors[category],
            text=category_data['sku'],
            textposition='outside'
        ))
    
    # Add cumulative percentage line
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['cumulative_percentage'],
        mode='lines+markers',
        name='Cumulative %',
        yaxis='y2',
        line=dict(color='black', width=2)
    ))
    
    # Add 80% and 95% lines
    fig.add_hline(y=80, line_dash="dash", line_color="red", yref='y2', 
                  annotation_text="80% (A-B boundary)")
    fig.add_hline(y=95, line_dash="dash", line_color="orange", yref='y2',
                  annotation_text="95% (B-C boundary)")
    
    fig.update_layout(
        title="ABC Analysis - Product Value Distribution",
        xaxis_title="Products (ranked by value)",
        yaxis_title="Annual Value ($)",
        yaxis2=dict(
            title="Cumulative Percentage (%)",
            overlaying='y',
            side='right',
            range=[0, 100]
        ),
        height=500
    )
    
    return fig

def create_transaction_timeline_chart(data: List[Dict[str, Any]], days: int = 30) -> go.Figure:
    """Create a timeline chart showing transaction volumes"""
    
    if not data:
        return go.Figure()
    
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['timestamp']).dt.date
    
    # Group by date and transaction type
    daily_transactions = df.groupby(['date', 'transaction_type']).size().reset_index(name='count')
    
    fig = go.Figure()
    
    transaction_types = daily_transactions['transaction_type'].unique()
    colors = px.colors.qualitative.Set1
    
    for i, trans_type in enumerate(transaction_types):
        type_data = daily_transactions[daily_transactions['transaction_type'] == trans_type]
        
        fig.add_trace(go.Scatter(
            x=type_data['date'],
            y=type_data['count'],
            mode='lines+markers',
            name=trans_type.replace('_', ' ').title(),
            line=dict(color=colors[i % len(colors)])
        ))
    
    fig.update_layout(
        title=f"Transaction Volume - Last {days} Days",
        xaxis_title="Date",
        yaxis_title="Number of Transactions",
        hovermode='x unified',
        height=400
    )
    
    return fig

def create_eoq_sensitivity_chart(eoq: float, annual_demand: float, ordering_cost: float, holding_cost: float) -> go.Figure:
    """Create EOQ sensitivity analysis chart"""
    
    # Generate quantity range around EOQ
    quantities = np.arange(max(1, int(eoq * 0.3)), int(eoq * 2), max(1, int(eoq * 0.05)))
    
    total_costs = []
    ordering_costs = []
    holding_costs = []
    
    for qty in quantities:
        orders_per_year = annual_demand / qty
        ord_cost = orders_per_year * ordering_cost
        hold_cost = (qty / 2) * holding_cost
        total_cost = ord_cost + hold_cost
        
        total_costs.append(total_cost)
        ordering_costs.append(ord_cost)
        holding_costs.append(hold_cost)
    
    fig = go.Figure()
    
    # Add cost curves
    fig.add_trace(go.Scatter(
        x=quantities,
        y=total_costs,
        mode='lines',
        name='Total Cost',
        line=dict(color='red', width=3)
    ))
    
    fig.add_trace(go.Scatter(
        x=quantities,
        y=ordering_costs,
        mode='lines',
        name='Ordering Cost',
        line=dict(color='blue', dash='dash')
    ))
    
    fig.add_trace(go.Scatter(
        x=quantities,
        y=holding_costs,
        mode='lines',
        name='Holding Cost',
        line=dict(color='green', dash='dash')
    ))
    
    # Mark optimal point
    fig.add_vline(
        x=eoq,
        line_dash="dot",
        line_color="red",
        annotation_text=f"EOQ = {eoq:.0f}"
    )
    
    fig.update_layout(
        title="EOQ Cost Sensitivity Analysis",
        xaxis_title="Order Quantity (units)",
        yaxis_title="Annual Cost ($)",
        hovermode='x unified',
        height=400
    )
    
    return fig

def create_stock_turnover_chart(data: List[Dict[str, Any]]) -> go.Figure:
    """Create inventory turnover chart"""
    
    if not data:
        return go.Figure()
    
    df = pd.DataFrame(data)
    
    fig = px.bar(
        df,
        x='sku',
        y='turnover_ratio',
        title="Inventory Turnover by Product",
        labels={'turnover_ratio': 'Turnover Ratio', 'sku': 'Product SKU'},
        color='turnover_ratio',
        color_continuous_scale='RdYlGn'
    )
    
    # Add industry benchmark line
    fig.add_hline(
        y=6,  # Example benchmark
        line_dash="dash",
        line_color="blue",
        annotation_text="Industry Benchmark (6x)"
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=400
    )
    
    return fig

def display_metric_card(title: str, value: str, delta: Optional[str] = None, 
                       delta_color: str = "normal") -> None:
    """Display a metric card with optional delta"""
    
    st.metric(
        label=title,
        value=value,
        delta=delta,
        delta_color=delta_color
    )

def display_kpi_dashboard(metrics: Dict[str, Any]) -> None:
    """Display a KPI dashboard with multiple metrics"""
    
    # Determine number of columns based on metrics count
    num_metrics = len(metrics)
    cols = st.columns(min(num_metrics, 4))
    
    for i, (key, metric) in enumerate(metrics.items()):
        with cols[i % 4]:
            if isinstance(metric, dict):
                display_metric_card(
                    title=metric.get('title', key),
                    value=metric.get('value', '0'),
                    delta=metric.get('delta'),
                    delta_color=metric.get('delta_color', 'normal')
                )
            else:
                display_metric_card(title=key, value=str(metric))

def create_heatmap_chart(data: pd.DataFrame, title: str = "Heatmap") -> go.Figure:
    """Create a heatmap chart"""
    
    fig = go.Figure(data=go.Heatmap(
        z=data.values,
        x=data.columns,
        y=data.index,
        colorscale='RdYlBu_r',
        hoverongaps=False
    ))
    
    fig.update_layout(
        title=title,
        height=400
    )
    
    return fig

def create_gauge_chart(value: float, title: str, max_value: float = 100, 
                      thresholds: Dict[str, float] = None) -> go.Figure:
    """Create a gauge chart for KPI visualization"""
    
    if thresholds is None:
        thresholds = {'red': 30, 'yellow': 70, 'green': 100}
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title},
        gauge={
            'axis': {'range': [None, max_value]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, thresholds['red']], 'color': "lightgray"},
                {'range': [thresholds['red'], thresholds['yellow']], 'color': "yellow"},
                {'range': [thresholds['yellow'], max_value], 'color': "green"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': value
            }
        }
    ))
    
    fig.update_layout(height=300)
    
    return fig
