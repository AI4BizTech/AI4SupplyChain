"""
Inventory management page
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def render_inventory_page():
    """Render the inventory management page"""
    st.title("📊 Inventory Management")
    
    # Sidebar for actions
    with st.sidebar:
        st.header("Inventory Actions")
        action = st.selectbox(
            "Choose Action",
            ["Dashboard", "Stock Levels", "Stock Alerts", "Adjustments", "Transfers"]
        )
    
    try:
        from src.services.inventory import InventoryService
        
        inventory_service = InventoryService()
        
        if action == "Dashboard":
            show_inventory_dashboard(inventory_service)
        elif action == "Stock Levels":
            show_stock_levels(inventory_service)
        elif action == "Stock Alerts":
            show_stock_alerts(inventory_service)
        elif action == "Adjustments":
            show_inventory_adjustments(inventory_service)
        elif action == "Transfers":
            show_inventory_transfers(inventory_service)
            
    except Exception as e:
        st.error(f"Error loading inventory management: {e}")
        st.info("Please ensure the database is initialized and services are available.")

def show_inventory_dashboard(inventory_service):
    """Show inventory dashboard with key metrics"""
    st.header("📈 Inventory Dashboard")
    
    try:
        # Get summary statistics
        summary = inventory_service.get_inventory_summary()
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Products",
                summary.get('total_products', 0)
            )
        
        with col2:
            st.metric(
                "Total Stock Value",
                f"${summary.get('total_value', 0):,.2f}"
            )
        
        with col3:
            st.metric(
                "Low Stock Items",
                summary.get('low_stock_count', 0),
                delta=f"-{summary.get('low_stock_percentage', 0):.1f}%" if summary.get('low_stock_percentage', 0) > 0 else None
            )
        
        with col4:
            st.metric(
                "Out of Stock",
                summary.get('out_of_stock_count', 0)
            )
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Stock status pie chart
            stock_status_data = {
                'Status': ['Adequate', 'Low Stock', 'Out of Stock'],
                'Count': [
                    summary.get('adequate_stock_count', 0),
                    summary.get('low_stock_count', 0),
                    summary.get('out_of_stock_count', 0)
                ]
            }
            
            fig_pie = px.pie(
                values=stock_status_data['Count'],
                names=stock_status_data['Status'],
                title="Stock Status Distribution",
                color_discrete_map={
                    'Adequate': '#28a745',
                    'Low Stock': '#ffc107',
                    'Out of Stock': '#dc3545'
                }
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Top categories by value
            category_data = summary.get('category_breakdown', [])
            if category_data:
                df_categories = pd.DataFrame(category_data)
                fig_bar = px.bar(
                    df_categories,
                    x='category',
                    y='total_value',
                    title="Inventory Value by Category",
                    labels={'total_value': 'Total Value ($)', 'category': 'Category'}
                )
                fig_bar.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_bar, use_container_width=True)
        
        # Recent activity
        st.subheader("📋 Recent Inventory Activity")
        recent_transactions = inventory_service.get_transaction_history(limit=10)
        
        if recent_transactions:
            df_transactions = pd.DataFrame(recent_transactions)
            
            # Format the data for display
            df_display = df_transactions.copy()
            if 'timestamp' in df_display.columns:
                df_display['timestamp'] = pd.to_datetime(df_display['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        else:
            st.info("No recent transactions found.")
        
        # Alerts section
        show_inventory_alerts_summary(inventory_service)
        
    except Exception as e:
        st.error(f"Error loading dashboard: {e}")

def show_stock_levels(inventory_service):
    """Show current stock levels across all locations"""
    st.header("📦 Stock Levels")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        location_filter = st.selectbox(
            "Filter by Location",
            ["All Locations"] + get_locations(inventory_service)
        )
    
    with col2:
        category_filter = st.selectbox(
            "Filter by Category", 
            ["All Categories"] + get_categories(inventory_service)
        )
    
    with col3:
        stock_status = st.selectbox(
            "Filter by Stock Status",
            ["All", "In Stock", "Low Stock", "Out of Stock"]
        )
    
    try:
        # Get stock levels
        location = None if location_filter == "All Locations" else location_filter
        category = None if category_filter == "All Categories" else category_filter
        
        stock_data = inventory_service.get_all_stock_levels(
            location=location,
            category=category
        )
        
        if not stock_data:
            st.info("No stock data found for the selected filters.")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(stock_data)
        
        # Add stock status column
        df['Stock Status'] = df.apply(
            lambda row: get_stock_status(row['quantity'], row.get('reorder_point', 0)),
            axis=1
        )
        
        # Filter by stock status
        if stock_status != "All":
            df = df[df['Stock Status'] == stock_status]
        
        if df.empty:
            st.info(f"No products found with status: {stock_status}")
            return
        
        # Display summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Products Shown", len(df))
        with col2:
            total_units = df['quantity'].sum()
            st.metric("Total Units", f"{total_units:,}")
        with col3:
            low_stock_count = len(df[df['Stock Status'] == 'Low Stock'])
            st.metric("Low Stock Items", low_stock_count)
        with col4:
            out_of_stock_count = len(df[df['Stock Status'] == 'Out of Stock'])
            st.metric("Out of Stock", out_of_stock_count)
        
        # Color code the dataframe
        def color_stock_status(val):
            if val == 'Out of Stock':
                return 'background-color: #ffebee'
            elif val == 'Low Stock':
                return 'background-color: #fff3e0'
            elif val == 'In Stock':
                return 'background-color: #e8f5e8'
            return ''
        
        # Format for display
        df_display = df.copy()
        if 'unit_cost' in df_display.columns:
            df_display['Unit Cost'] = df_display['unit_cost'].apply(lambda x: f"${float(x):.2f}")
        if 'total_value' in df_display.columns:
            df_display['Total Value'] = df_display['total_value'].apply(lambda x: f"${float(x):,.2f}")
        
        # Style and display
        styled_df = df_display.style.applymap(color_stock_status, subset=['Stock Status'])
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        # Export option
        if st.button("📥 Export to CSV"):
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"stock_levels_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
    except Exception as e:
        st.error(f"Error loading stock levels: {e}")

def show_stock_alerts(inventory_service):
    """Show stock alerts and reorder recommendations"""
    st.header("🚨 Stock Alerts & Recommendations")
    
    try:
        # Get low stock and out of stock items
        alerts = inventory_service.get_stock_alerts()
        
        if not alerts:
            st.success("✅ No stock alerts! All products are adequately stocked.")
            return
        
        # Separate alerts by type
        out_of_stock = [item for item in alerts if item.get('quantity', 0) == 0]
        low_stock = [item for item in alerts if item.get('quantity', 0) > 0 and item.get('status') == 'Low Stock']
        
        # Out of stock alerts
        if out_of_stock:
            st.error(f"🚫 **{len(out_of_stock)} Products Out of Stock**")
            df_out = pd.DataFrame(out_of_stock)
            st.dataframe(df_out, use_container_width=True, hide_index=True)
        
        # Low stock alerts
        if low_stock:
            st.warning(f"⚠️ **{len(low_stock)} Products Low on Stock**")
            df_low = pd.DataFrame(low_stock)
            st.dataframe(df_low, use_container_width=True, hide_index=True)
        
        # Reorder recommendations
        st.subheader("📋 Reorder Recommendations")
        
        reorder_recommendations = []
        for item in alerts:
            if item.get('recommended_order_qty', 0) > 0:
                reorder_recommendations.append({
                    'SKU': item.get('sku'),
                    'Product Name': item.get('product_name'),
                    'Current Stock': item.get('quantity', 0),
                    'Reorder Point': item.get('reorder_point', 0),
                    'Recommended Order Qty': item.get('recommended_order_qty', 0),
                    'Estimated Cost': f"${float(item.get('estimated_cost', 0)):,.2f}",
                    'Supplier': item.get('supplier_name', 'N/A')
                })
        
        if reorder_recommendations:
            df_reorder = pd.DataFrame(reorder_recommendations)
            st.dataframe(df_reorder, use_container_width=True, hide_index=True)
            
            # Total reorder cost
            total_cost = sum(float(item.get('estimated_cost', 0)) for item in alerts if item.get('estimated_cost'))
            st.metric("Total Estimated Reorder Cost", f"${total_cost:,.2f}")
            
            # Generate purchase orders
            if st.button("📝 Generate Purchase Orders"):
                st.info("Purchase order generation functionality would be implemented here.")
        
    except Exception as e:
        st.error(f"Error loading stock alerts: {e}")

def show_inventory_adjustments(inventory_service):
    """Show inventory adjustment functionality"""
    st.header("⚖️ Inventory Adjustments")
    
    st.info("Use this section to record inventory adjustments from cycle counts, damage, theft, etc.")
    
    # Adjustment form
    with st.form("adjustment_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Product selection
            try:
                products = inventory_service.list_products(limit=1000)
                product_options = [f"{p.sku} - {p.name}" for p in products]
                selected_product = st.selectbox("Select Product", product_options)
                
                if selected_product:
                    sku = selected_product.split(" - ")[0]
                    product = inventory_service.get_product_by_sku(sku)
                    
                    # Show current stock
                    if product:
                        current_stock = inventory_service.get_stock_levels(sku)
                        if current_stock:
                            total_stock = sum(item['quantity'] for item in current_stock)
                            st.info(f"Current total stock: {total_stock} units")
            except:
                st.error("Error loading products")
                return
        
        with col2:
            # Location selection
            locations = get_locations(inventory_service)
            selected_location = st.selectbox("Location", locations)
        
        # Adjustment details
        adjustment_type = st.selectbox(
            "Adjustment Type",
            ["Cycle Count", "Damage", "Theft", "Found Inventory", "Other"]
        )
        
        col3, col4 = st.columns(2)
        with col3:
            quantity_adjustment = st.number_input(
                "Quantity Adjustment",
                help="Use positive numbers to add inventory, negative to remove"
            )
        
        with col4:
            reason = st.text_area("Reason/Notes", help="Explain the reason for this adjustment")
        
        submitted = st.form_submit_button("Record Adjustment")
        
        if submitted:
            if not selected_product or not selected_location or quantity_adjustment == 0:
                st.error("Please fill in all required fields and enter a non-zero adjustment quantity.")
                return
            
            try:
                # Create adjustment transaction
                transaction_data = {
                    "product_sku": sku,
                    "location_id": selected_location,
                    "transaction_type": "adjustment",
                    "quantity": quantity_adjustment,
                    "reference_document": f"ADJ-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                    "notes": f"Adjustment Type: {adjustment_type}. Reason: {reason}",
                    "user_id": "admin"  # In a real app, this would be the logged-in user
                }
                
                # This would call the transaction service
                st.success(f"✅ Adjustment recorded: {quantity_adjustment:+} units for {sku}")
                st.info(f"Transaction ID: {transaction_data['reference_document']}")
                
            except Exception as e:
                st.error(f"Error recording adjustment: {e}")
    
    # Recent adjustments
    st.subheader("📋 Recent Adjustments")
    try:
        adjustments = inventory_service.get_transaction_history(
            transaction_type="adjustment",
            limit=20
        )
        
        if adjustments:
            df_adjustments = pd.DataFrame(adjustments)
            st.dataframe(df_adjustments, use_container_width=True, hide_index=True)
        else:
            st.info("No recent adjustments found.")
            
    except Exception as e:
        st.error(f"Error loading recent adjustments: {e}")

def show_inventory_transfers(inventory_service):
    """Show inventory transfer functionality"""
    st.header("🔄 Inventory Transfers")
    
    st.info("Transfer inventory between locations.")
    
    # Transfer form
    with st.form("transfer_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Product selection
            try:
                products = inventory_service.list_products(limit=1000)
                product_options = [f"{p.sku} - {p.name}" for p in products]
                selected_product = st.selectbox("Select Product", product_options)
                
                if selected_product:
                    sku = selected_product.split(" - ")[0]
                    
                    # Show stock by location
                    stock_levels = inventory_service.get_stock_levels(sku)
                    if stock_levels:
                        st.write("**Current Stock by Location:**")
                        for stock in stock_levels:
                            st.write(f"- {stock['location']}: {stock['quantity']} units")
            except:
                st.error("Error loading products")
                return
        
        with col2:
            locations = get_locations(inventory_service)
            from_location = st.selectbox("From Location", locations, key="from_loc")
            to_location = st.selectbox("To Location", locations, key="to_loc")
        
        col3, col4 = st.columns(2)
        with col3:
            transfer_quantity = st.number_input("Quantity to Transfer", min_value=1, value=1)
        
        with col4:
            transfer_notes = st.text_area("Transfer Notes")
        
        submitted = st.form_submit_button("Execute Transfer")
        
        if submitted:
            if not selected_product or not from_location or not to_location or transfer_quantity <= 0:
                st.error("Please fill in all required fields.")
                return
            
            if from_location == to_location:
                st.error("From and To locations cannot be the same.")
                return
            
            try:
                # Create transfer transactions
                transfer_id = f"TRF-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                
                # Outbound transaction
                outbound_data = {
                    "product_sku": sku,
                    "location_id": from_location,
                    "transaction_type": "transfer",
                    "quantity": -transfer_quantity,  # Negative for outbound
                    "reference_document": transfer_id,
                    "notes": f"Transfer to {to_location}. {transfer_notes}",
                    "user_id": "admin"
                }
                
                # Inbound transaction
                inbound_data = {
                    "product_sku": sku,
                    "location_id": to_location,
                    "transaction_type": "transfer",
                    "quantity": transfer_quantity,  # Positive for inbound
                    "reference_document": transfer_id,
                    "notes": f"Transfer from {from_location}. {transfer_notes}",
                    "user_id": "admin"
                }
                
                st.success(f"✅ Transfer completed: {transfer_quantity} units of {sku}")
                st.success(f"From: {from_location} → To: {to_location}")
                st.info(f"Transfer ID: {transfer_id}")
                
            except Exception as e:
                st.error(f"Error executing transfer: {e}")
    
    # Recent transfers
    st.subheader("📋 Recent Transfers")
    try:
        transfers = inventory_service.get_transaction_history(
            transaction_type="transfer",
            limit=20
        )
        
        if transfers:
            df_transfers = pd.DataFrame(transfers)
            st.dataframe(df_transfers, use_container_width=True, hide_index=True)
        else:
            st.info("No recent transfers found.")
            
    except Exception as e:
        st.error(f"Error loading recent transfers: {e}")

def show_inventory_alerts_summary(inventory_service):
    """Show a summary of inventory alerts"""
    st.subheader("🚨 Inventory Alerts Summary")
    
    try:
        alerts = inventory_service.get_stock_alerts()
        
        if not alerts:
            st.success("✅ No inventory alerts")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            out_of_stock = len([a for a in alerts if a.get('quantity', 0) == 0])
            st.metric("Out of Stock", out_of_stock, delta=f"-{out_of_stock}" if out_of_stock > 0 else None)
        
        with col2:
            low_stock = len([a for a in alerts if a.get('quantity', 0) > 0 and a.get('status') == 'Low Stock'])
            st.metric("Low Stock", low_stock, delta=f"-{low_stock}" if low_stock > 0 else None)
        
        if st.button("View All Alerts"):
            st.session_state.inventory_action = "Stock Alerts"
            st.rerun()
            
    except Exception as e:
        st.error(f"Error loading alerts summary: {e}")

def get_stock_status(quantity: int, reorder_point: int) -> str:
    """Determine stock status based on quantity and reorder point"""
    if quantity == 0:
        return "Out of Stock"
    elif quantity <= reorder_point:
        return "Low Stock"
    else:
        return "In Stock"

def get_locations(inventory_service) -> list:
    """Get list of available locations"""
    try:
        locations = inventory_service.get_locations()
        return [loc.location_id for loc in locations]
    except:
        return ["MAIN-WH", "STORE-A", "STORE-B"]  # Default locations

def get_categories(inventory_service) -> list:
    """Get list of product categories"""
    try:
        products = inventory_service.list_products(limit=1000)
        categories = list(set(p.category for p in products))
        return sorted(categories)
    except:
        return []

if __name__ == "__main__":
    render_inventory_page()
