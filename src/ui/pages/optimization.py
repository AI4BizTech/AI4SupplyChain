"""
Optimization tools page
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def render_optimization_page():
    """Render the inventory optimization page"""
    st.title("⚙️ Inventory Optimization")
    
    # Sidebar for actions
    with st.sidebar:
        st.header("Optimization Tools")
        action = st.selectbox(
            "Choose Tool",
            ["EOQ Calculator", "Reorder Point", "Safety Stock", "ABC Analysis", "Optimization Dashboard"]
        )
    
    try:
        from src.services.optimization import OptimizationService
        from src.services.inventory import InventoryService
        from src.services.forecasting import ForecastingService
        
        optimization_service = OptimizationService()
        inventory_service = InventoryService()
        forecasting_service = ForecastingService()
        
        if action == "EOQ Calculator":
            show_eoq_calculator(optimization_service, inventory_service)
        elif action == "Reorder Point":
            show_reorder_point_calculator(optimization_service, inventory_service, forecasting_service)
        elif action == "Safety Stock":
            show_safety_stock_calculator(optimization_service, inventory_service, forecasting_service)
        elif action == "ABC Analysis":
            show_abc_analysis(optimization_service, inventory_service)
        elif action == "Optimization Dashboard":
            show_optimization_dashboard(optimization_service, inventory_service)
            
    except Exception as e:
        st.error(f"Error loading inventory optimization: {e}")
        st.info("Please ensure the database is initialized and services are available.")

def show_eoq_calculator(optimization_service, inventory_service):
    """Show Economic Order Quantity calculator"""
    st.header("📊 Economic Order Quantity (EOQ) Calculator")
    
    st.info("Calculate the optimal order quantity to minimize total inventory costs.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Product selection
        try:
            products = inventory_service.list_products(limit=1000)
            product_options = ["Manual Input"] + [f"{p.sku} - {p.name}" for p in products]
            selected_product = st.selectbox("Select Product", product_options)
            
            if selected_product != "Manual Input":
                sku = selected_product.split(" - ")[0]
                product = inventory_service.get_product_by_sku(sku)
                
                # Pre-fill with product data
                default_unit_cost = float(product.unit_cost) if product else 10.0
                st.info(f"Using data for product: {product.name if product else 'Unknown'}")
            else:
                default_unit_cost = 10.0
                product = None
                sku = None
        except:
            st.error("Error loading products")
            return
    
    with col2:
        st.write("**EOQ Formula:**")
        st.latex(r"EOQ = \sqrt{\frac{2 \times D \times S}{H}}")
        st.write("Where:")
        st.write("- D = Annual demand")
        st.write("- S = Ordering cost per order")
        st.write("- H = Holding cost per unit per year")
    
    # EOQ Parameters
    st.subheader("📋 EOQ Parameters")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        annual_demand = st.number_input(
            "Annual Demand (units/year)",
            min_value=1,
            value=1000,
            help="Total expected demand for one year"
        )
    
    with col2:
        ordering_cost = st.number_input(
            "Ordering Cost ($/order)",
            min_value=0.01,
            value=50.0,
            step=0.01,
            help="Cost to place one order (admin, shipping, etc.)"
        )
    
    with col3:
        unit_cost = st.number_input(
            "Unit Cost ($/unit)",
            min_value=0.01,
            value=default_unit_cost,
            step=0.01,
            help="Cost per unit of the product"
        )
    
    col4, col5, col6 = st.columns(3)
    
    with col4:
        carrying_cost_rate = st.slider(
            "Carrying Cost Rate (%/year)",
            min_value=1.0,
            max_value=50.0,
            value=20.0,
            step=0.5,
            help="Annual carrying cost as % of unit cost"
        ) / 100
    
    with col5:
        holding_cost = unit_cost * carrying_cost_rate
        st.metric("Holding Cost", f"${holding_cost:.2f}/unit/year")
    
    with col6:
        st.write("")  # Spacer
    
    if st.button("🔍 Calculate EOQ"):
        try:
            # Calculate EOQ
            eoq_result = optimization_service.calculate_eoq(
                annual_demand=annual_demand,
                ordering_cost=ordering_cost,
                holding_cost=holding_cost
            )
            
            if "error" in eoq_result:
                st.error(f"EOQ calculation failed: {eoq_result['error']}")
                return
            
            st.success("✅ EOQ calculated successfully!")
            
            # Display results
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Optimal Order Quantity", f"{eoq_result['eoq']:.0f} units")
            
            with col2:
                st.metric("Orders per Year", f"{eoq_result['orders_per_year']:.1f}")
            
            with col3:
                st.metric("Order Frequency", f"{365/eoq_result['orders_per_year']:.0f} days")
            
            with col4:
                st.metric("Total Annual Cost", f"${eoq_result['total_cost']:.2f}")
            
            # Cost breakdown
            st.subheader("💰 Cost Breakdown")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Annual Ordering Cost", f"${eoq_result['ordering_cost']:.2f}")
            
            with col2:
                st.metric("Annual Holding Cost", f"${eoq_result['holding_cost']:.2f}")
            
            with col3:
                st.metric("Annual Product Cost", f"${annual_demand * unit_cost:,.2f}")
            
            # EOQ Sensitivity Analysis
            st.subheader("📊 Sensitivity Analysis")
            
            # Create sensitivity chart
            quantities = np.arange(int(eoq_result['eoq'] * 0.5), int(eoq_result['eoq'] * 1.5), 10)
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
                x=eoq_result['eoq'],
                line_dash="dot",
                line_color="red",
                annotation_text=f"EOQ = {eoq_result['eoq']:.0f}"
            )
            
            fig.update_layout(
                title="EOQ Cost Analysis",
                xaxis_title="Order Quantity (units)",
                yaxis_title="Annual Cost ($)",
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Recommendations
            st.subheader("💡 Recommendations")
            
            current_order_qty = product.reorder_quantity if product else None
            
            if current_order_qty:
                savings = calculate_cost_savings(
                    current_order_qty, eoq_result['eoq'],
                    annual_demand, ordering_cost, holding_cost
                )
                
                if savings > 0:
                    st.success(f"💰 Potential annual savings: ${savings:.2f}")
                    st.info(f"📈 Current order quantity: {current_order_qty} units")
                    st.info(f"🎯 Recommended order quantity: {eoq_result['eoq']:.0f} units")
                else:
                    st.info("✅ Current order quantity is near optimal")
            
            # Update product recommendation
            if product and st.button("📝 Update Product with EOQ"):
                try:
                    updates = {"reorder_quantity": int(eoq_result['eoq'])}
                    inventory_service.update_product(product.id, updates)
                    st.success(f"✅ Updated {sku} reorder quantity to {eoq_result['eoq']:.0f} units")
                except Exception as e:
                    st.error(f"Error updating product: {e}")
            
        except Exception as e:
            st.error(f"Error calculating EOQ: {e}")

def show_reorder_point_calculator(optimization_service, inventory_service, forecasting_service):
    """Show reorder point calculator"""
    st.header("🎯 Reorder Point Calculator")
    
    st.info("Calculate the optimal reorder point to minimize stockouts while controlling inventory costs.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Product selection
        try:
            products = inventory_service.list_products(limit=1000)
            product_options = ["Manual Input"] + [f"{p.sku} - {p.name}" for p in products]
            selected_product = st.selectbox("Select Product", product_options)
            
            if selected_product != "Manual Input":
                sku = selected_product.split(" - ")[0]
                product = inventory_service.get_product_by_sku(sku)
            else:
                product = None
                sku = None
        except:
            st.error("Error loading products")
            return
    
    with col2:
        st.write("**Reorder Point Formula:**")
        st.latex(r"ROP = (D \times L) + SS")
        st.write("Where:")
        st.write("- D = Average daily demand")
        st.write("- L = Lead time (days)")
        st.write("- SS = Safety stock")
    
    # Parameters
    st.subheader("📋 Reorder Point Parameters")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Try to get demand from forecast
        avg_daily_demand = 10.0
        if product:
            try:
                forecast = forecasting_service.generate_forecast(product.id, horizon=7)
                if "daily_average" in forecast:
                    avg_daily_demand = forecast["daily_average"]
            except:
                pass
        
        avg_daily_demand = st.number_input(
            "Average Daily Demand (units/day)",
            min_value=0.1,
            value=avg_daily_demand,
            step=0.1,
            help="Average units sold per day"
        )
    
    with col2:
        # Get lead time from supplier if available
        lead_time = 7
        if product and product.supplier_id:
            try:
                # This would get supplier lead time
                lead_time = 7  # Default for now
            except:
                pass
        
        lead_time = st.number_input(
            "Lead Time (days)",
            min_value=1,
            value=lead_time,
            help="Time from order placement to receipt"
        )
    
    with col3:
        service_level = st.slider(
            "Service Level (%)",
            min_value=50,
            max_value=99,
            value=95,
            help="Desired stockout protection level"
        )
    
    col4, col5 = st.columns(2)
    
    with col4:
        demand_variability = st.slider(
            "Demand Variability (CV)",
            min_value=0.1,
            max_value=2.0,
            value=0.3,
            step=0.1,
            help="Coefficient of variation for demand"
        )
    
    with col5:
        lead_time_variability = st.slider(
            "Lead Time Variability (days)",
            min_value=0,
            max_value=lead_time,
            value=1,
            help="Standard deviation of lead time"
        )
    
    if st.button("🔍 Calculate Reorder Point"):
        try:
            # Calculate reorder point
            rop_result = optimization_service.calculate_reorder_point(
                avg_daily_demand=avg_daily_demand,
                lead_time_days=lead_time,
                service_level=service_level / 100,
                demand_std=avg_daily_demand * demand_variability,
                lead_time_std=lead_time_variability
            )
            
            if "error" in rop_result:
                st.error(f"Reorder point calculation failed: {rop_result['error']}")
                return
            
            st.success("✅ Reorder point calculated successfully!")
            
            # Display results
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Reorder Point", f"{rop_result['reorder_point']:.0f} units")
            
            with col2:
                st.metric("Safety Stock", f"{rop_result['safety_stock']:.0f} units")
            
            with col3:
                st.metric("Lead Time Demand", f"{rop_result['lead_time_demand']:.0f} units")
            
            with col4:
                expected_stockouts = (1 - service_level / 100) * 100
                st.metric("Expected Stockout Risk", f"{expected_stockouts:.1f}%")
            
            # Reorder point breakdown
            st.subheader("📊 Breakdown Analysis")
            
            # Create breakdown chart
            breakdown_data = {
                'Component': ['Lead Time Demand', 'Safety Stock'],
                'Quantity': [rop_result['lead_time_demand'], rop_result['safety_stock']]
            }
            
            fig = px.bar(
                breakdown_data,
                x='Component',
                y='Quantity',
                title="Reorder Point Components",
                color='Component',
                color_discrete_map={
                    'Lead Time Demand': '#1f77b4',
                    'Safety Stock': '#ff7f0e'
                }
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Service level analysis
            st.subheader("📈 Service Level Impact")
            
            service_levels = range(80, 100, 2)
            reorder_points = []
            safety_stocks = []
            
            for sl in service_levels:
                temp_result = optimization_service.calculate_reorder_point(
                    avg_daily_demand=avg_daily_demand,
                    lead_time_days=lead_time,
                    service_level=sl / 100,
                    demand_std=avg_daily_demand * demand_variability,
                    lead_time_std=lead_time_variability
                )
                reorder_points.append(temp_result.get('reorder_point', 0))
                safety_stocks.append(temp_result.get('safety_stock', 0))
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=service_levels,
                y=reorder_points,
                mode='lines+markers',
                name='Reorder Point',
                line=dict(color='blue')
            ))
            
            fig.add_trace(go.Scatter(
                x=service_levels,
                y=safety_stocks,
                mode='lines+markers',
                name='Safety Stock',
                line=dict(color='orange')
            ))
            
            fig.update_layout(
                title="Service Level vs Inventory Requirements",
                xaxis_title="Service Level (%)",
                yaxis_title="Inventory (units)",
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Current vs recommended
            if product:
                current_rop = product.reorder_point
                st.subheader("💡 Comparison with Current Settings")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Current Reorder Point", f"{current_rop} units")
                
                with col2:
                    st.metric("Recommended Reorder Point", f"{rop_result['reorder_point']:.0f} units")
                
                difference = rop_result['reorder_point'] - current_rop
                if abs(difference) > 5:
                    if difference > 0:
                        st.warning(f"⚠️ Consider increasing reorder point by {difference:.0f} units")
                    else:
                        st.info(f"💡 Consider decreasing reorder point by {abs(difference):.0f} units")
                else:
                    st.success("✅ Current reorder point is near optimal")
                
                # Update product
                if st.button("📝 Update Product with Calculated Reorder Point"):
                    try:
                        updates = {"reorder_point": int(rop_result['reorder_point'])}
                        inventory_service.update_product(product.id, updates)
                        st.success(f"✅ Updated {sku} reorder point to {rop_result['reorder_point']:.0f} units")
                    except Exception as e:
                        st.error(f"Error updating product: {e}")
            
        except Exception as e:
            st.error(f"Error calculating reorder point: {e}")

def show_safety_stock_calculator(optimization_service, inventory_service, forecasting_service):
    """Show safety stock calculator"""
    st.header("🛡️ Safety Stock Calculator")
    
    st.info("Calculate optimal safety stock levels to protect against demand and supply variability.")
    
    # This would be similar to reorder point calculator but focused on safety stock
    # For brevity, showing a simplified version
    
    col1, col2 = st.columns(2)
    
    with col1:
        avg_demand = st.number_input("Average Daily Demand", min_value=1.0, value=10.0)
        demand_std = st.number_input("Demand Standard Deviation", min_value=0.1, value=3.0)
    
    with col2:
        lead_time = st.number_input("Lead Time (days)", min_value=1, value=7)
        service_level = st.slider("Service Level (%)", 80, 99, 95)
    
    if st.button("Calculate Safety Stock"):
        try:
            # Simplified safety stock calculation
            z_score = {90: 1.28, 95: 1.65, 99: 2.33}.get(service_level, 1.65)
            safety_stock = z_score * demand_std * np.sqrt(lead_time)
            
            st.success(f"✅ Recommended Safety Stock: {safety_stock:.0f} units")
            
            # Show impact of different service levels
            service_levels = [80, 85, 90, 95, 99]
            z_scores = [0.84, 1.04, 1.28, 1.65, 2.33]
            safety_stocks = [z * demand_std * np.sqrt(lead_time) for z in z_scores]
            
            chart_data = pd.DataFrame({
                'Service Level': service_levels,
                'Safety Stock': safety_stocks
            })
            
            fig = px.bar(
                chart_data,
                x='Service Level',
                y='Safety Stock',
                title="Safety Stock vs Service Level"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error calculating safety stock: {e}")

def show_abc_analysis(optimization_service, inventory_service):
    """Show ABC analysis"""
    st.header("📊 ABC Analysis")
    
    st.info("Classify products by their contribution to total inventory value.")
    
    if st.button("🔍 Perform ABC Analysis"):
        try:
            # Mock ABC analysis data
            products_data = []
            
            try:
                products = inventory_service.list_products(limit=1000)
                for product in products:
                    # Get stock levels
                    stock_levels = inventory_service.get_stock_levels(product.sku)
                    total_stock = sum(item['quantity'] for item in stock_levels) if stock_levels else 0
                    
                    annual_usage = total_stock * 12  # Mock annual usage
                    unit_cost = float(product.unit_cost)
                    annual_value = annual_usage * unit_cost
                    
                    products_data.append({
                        'SKU': product.sku,
                        'Product Name': product.name,
                        'Annual Usage': annual_usage,
                        'Unit Cost': unit_cost,
                        'Annual Value': annual_value
                    })
            except:
                # Fallback mock data
                products_data = [
                    {'SKU': 'SKU-001', 'Product Name': 'Product A', 'Annual Usage': 1000, 'Unit Cost': 50.0, 'Annual Value': 50000},
                    {'SKU': 'SKU-002', 'Product Name': 'Product B', 'Annual Usage': 800, 'Unit Cost': 30.0, 'Annual Value': 24000},
                    {'SKU': 'SKU-003', 'Product Name': 'Product C', 'Annual Usage': 500, 'Unit Cost': 20.0, 'Annual Value': 10000},
                ]
            
            if not products_data:
                st.info("No product data available for ABC analysis")
                return
            
            df = pd.DataFrame(products_data)
            
            # Sort by annual value
            df = df.sort_values('Annual Value', ascending=False).reset_index(drop=True)
            
            # Calculate cumulative percentage
            df['Cumulative Value'] = df['Annual Value'].cumsum()
            total_value = df['Annual Value'].sum()
            df['Cumulative %'] = (df['Cumulative Value'] / total_value) * 100
            
            # Assign ABC categories
            df['ABC Category'] = 'C'
            df.loc[df['Cumulative %'] <= 80, 'ABC Category'] = 'A'
            df.loc[(df['Cumulative %'] > 80) & (df['Cumulative %'] <= 95), 'ABC Category'] = 'B'
            
            # Display results
            st.success("✅ ABC Analysis completed!")
            
            # Category summary
            category_summary = df.groupby('ABC Category').agg({
                'SKU': 'count',
                'Annual Value': 'sum'
            }).reset_index()
            category_summary['Value %'] = (category_summary['Annual Value'] / total_value) * 100
            category_summary.columns = ['Category', 'Product Count', 'Total Value', 'Value %']
            
            st.subheader("📊 Category Summary")
            st.dataframe(category_summary, hide_index=True)
            
            # ABC Chart
            fig = px.bar(
                category_summary,
                x='Category',
                y='Value %',
                title="ABC Analysis - Value Distribution",
                color='Category',
                color_discrete_map={'A': '#ff4444', 'B': '#ffaa44', 'C': '#44ff44'}
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Detailed results
            st.subheader("📋 Detailed Results")
            
            # Format for display
            df_display = df.copy()
            df_display['Unit Cost'] = df_display['Unit Cost'].apply(lambda x: f"${x:.2f}")
            df_display['Annual Value'] = df_display['Annual Value'].apply(lambda x: f"${x:,.2f}")
            df_display['Cumulative %'] = df_display['Cumulative %'].apply(lambda x: f"{x:.1f}%")
            
            st.dataframe(df_display, hide_index=True)
            
            # Recommendations
            st.subheader("💡 ABC Management Recommendations")
            
            a_count = len(df[df['ABC Category'] == 'A'])
            b_count = len(df[df['ABC Category'] == 'B'])
            c_count = len(df[df['ABC Category'] == 'C'])
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write("**Category A (High Value)**")
                st.write(f"• {a_count} products (~80% of value)")
                st.write("• Tight inventory control")
                st.write("• Frequent reviews")
                st.write("• Accurate forecasting")
                st.write("• Close supplier relationships")
            
            with col2:
                st.write("**Category B (Medium Value)**")
                st.write(f"• {b_count} products (~15% of value)")
                st.write("• Moderate control")
                st.write("• Monthly reviews")
                st.write("• Standard forecasting")
                st.write("• Balanced approach")
            
            with col3:
                st.write("**Category C (Low Value)**")
                st.write(f"• {c_count} products (~5% of value)")
                st.write("• Simple control systems")
                st.write("• Quarterly reviews")
                st.write("• Basic forecasting")
                st.write("• Focus on automation")
            
        except Exception as e:
            st.error(f"Error performing ABC analysis: {e}")

def show_optimization_dashboard(optimization_service, inventory_service):
    """Show optimization dashboard with multiple metrics"""
    st.header("🎯 Optimization Dashboard")
    
    st.info("Overview of optimization opportunities across your inventory.")
    
    try:
        # Mock optimization data
        products = inventory_service.list_products(limit=100)
        
        if not products:
            st.info("No products available for optimization analysis")
            return
        
        optimization_data = []
        
        for product in products:
            try:
                # Mock calculations
                current_eoq = product.reorder_quantity
                current_rop = product.reorder_point
                
                # Simplified optimal calculations
                optimal_eoq = max(50, int(current_eoq * (0.8 + 0.4 * np.random.random())))
                optimal_rop = max(10, int(current_rop * (0.9 + 0.2 * np.random.random())))
                
                eoq_savings = abs(optimal_eoq - current_eoq) * float(product.unit_cost) * 0.1
                rop_impact = "Optimal" if abs(optimal_rop - current_rop) < 5 else "Needs Review"
                
                optimization_data.append({
                    'SKU': product.sku,
                    'Product Name': product.name,
                    'Current EOQ': current_eoq,
                    'Optimal EOQ': optimal_eoq,
                    'Current ROP': current_rop,
                    'Optimal ROP': optimal_rop,
                    'Potential Savings': eoq_savings,
                    'Status': rop_impact
                })
            except:
                continue
        
        if not optimization_data:
            st.info("No optimization data available")
            return
        
        df = pd.DataFrame(optimization_data)
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_products = len(df)
            st.metric("Products Analyzed", total_products)
        
        with col2:
            needs_review = len(df[df['Status'] == 'Needs Review'])
            st.metric("Needs Optimization", needs_review)
        
        with col3:
            total_savings = df['Potential Savings'].sum()
            st.metric("Potential Savings", f"${total_savings:,.2f}")
        
        with col4:
            optimization_rate = ((total_products - needs_review) / total_products) * 100
            st.metric("Optimization Rate", f"{optimization_rate:.1f}%")
        
        # Top optimization opportunities
        st.subheader("🎯 Top Optimization Opportunities")
        
        top_opportunities = df.nlargest(10, 'Potential Savings')[
            ['SKU', 'Product Name', 'Current EOQ', 'Optimal EOQ', 'Potential Savings']
        ]
        
        # Format for display
        top_opportunities['Potential Savings'] = top_opportunities['Potential Savings'].apply(lambda x: f"${x:.2f}")
        
        st.dataframe(top_opportunities, hide_index=True)
        
        # Optimization status chart
        status_counts = df['Status'].value_counts()
        
        fig = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="Optimization Status Distribution",
            color_discrete_map={'Optimal': '#28a745', 'Needs Review': '#ffc107'}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Savings potential chart
        if len(df) > 0:
            fig = px.histogram(
                df,
                x='Potential Savings',
                title="Distribution of Potential Savings",
                nbins=20
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Action items
        st.subheader("📋 Recommended Actions")
        
        high_impact = df[df['Potential Savings'] > 100].nlargest(5, 'Potential Savings')
        
        if not high_impact.empty:
            st.write("**High Impact Optimizations:**")
            for _, row in high_impact.iterrows():
                st.write(f"• **{row['SKU']}**: Adjust EOQ from {row['Current EOQ']} to {row['Optimal EOQ']} units (Save ${row['Potential Savings']:.2f})")
        
        if needs_review > 0:
            st.write(f"**{needs_review} products need reorder point review**")
        
        # Export optimization report
        if st.button("📥 Export Optimization Report"):
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"optimization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
    except Exception as e:
        st.error(f"Error loading optimization dashboard: {e}")

def calculate_cost_savings(current_qty, optimal_qty, annual_demand, ordering_cost, holding_cost):
    """Calculate potential cost savings from EOQ optimization"""
    try:
        # Current total cost
        current_orders_per_year = annual_demand / current_qty
        current_ordering_cost = current_orders_per_year * ordering_cost
        current_holding_cost = (current_qty / 2) * holding_cost
        current_total_cost = current_ordering_cost + current_holding_cost
        
        # Optimal total cost
        optimal_orders_per_year = annual_demand / optimal_qty
        optimal_ordering_cost = optimal_orders_per_year * ordering_cost
        optimal_holding_cost = (optimal_qty / 2) * holding_cost
        optimal_total_cost = optimal_ordering_cost + optimal_holding_cost
        
        return current_total_cost - optimal_total_cost
    except:
        return 0

if __name__ == "__main__":
    render_optimization_page()
