"""
Supplier management interface page
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

def render_suppliers_page():
    """Render the supplier management page"""
    st.title("🏢 Supplier Management")
    
    # Sidebar for actions
    with st.sidebar:
        st.header("Supplier Actions")
        action = st.selectbox(
            "Choose Action",
            ["View Suppliers", "Add Supplier", "Edit Supplier", "Performance Analysis", "Import Suppliers"]
        )
    
    try:
        from src.services.suppliers import SupplierService
        from src.services.inventory import InventoryService
        
        supplier_service = SupplierService()
        inventory_service = InventoryService()
        
        if action == "View Suppliers":
            show_suppliers_list(supplier_service)
        elif action == "Add Supplier":
            show_add_supplier_form(supplier_service)
        elif action == "Edit Supplier":
            show_edit_supplier_form(supplier_service)
        elif action == "Performance Analysis":
            show_performance_analysis(supplier_service, inventory_service)
        elif action == "Import Suppliers":
            show_import_suppliers(supplier_service)
            
    except Exception as e:
        st.error(f"Error loading supplier management: {e}")
        st.info("Please ensure the database is initialized and services are available.")

def show_suppliers_list(supplier_service):
    """Show list of all suppliers"""
    st.header("📋 Supplier Directory")
    
    # Filters and search
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_name = st.text_input("Search by Name")
    
    with col2:
        min_rating = st.slider("Minimum Rating", 0.0, 5.0, 0.0, 0.1)
    
    with col3:
        limit = st.number_input("Max Results", min_value=10, max_value=1000, value=100)
    
    try:
        # Get suppliers
        suppliers = supplier_service.list_suppliers(limit=limit)
        
        if search_name:
            suppliers = [s for s in suppliers if search_name.lower() in s.name.lower()]
        
        if min_rating > 0:
            suppliers = [s for s in suppliers if (s.performance_rating or 0) >= min_rating]
        
        if not suppliers:
            st.info("No suppliers found matching the criteria.")
            return
        
        # Convert to DataFrame for display
        suppliers_data = []
        for supplier in suppliers:
            suppliers_data.append({
                "Supplier ID": supplier.supplier_id,
                "Name": supplier.name,
                "Lead Time (days)": supplier.lead_time_days,
                "Payment Terms": supplier.payment_terms or "N/A",
                "Min Order Qty": supplier.minimum_order_qty,
                "Rating": f"{float(supplier.performance_rating or 0):.1f}/5.0",
                "Contact": supplier.contact_info.get('email', 'N/A') if supplier.contact_info else 'N/A'
            })
        
        df = pd.DataFrame(suppliers_data)
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Suppliers", len(suppliers))
        with col2:
            avg_lead_time = sum(s.lead_time_days for s in suppliers) / len(suppliers) if suppliers else 0
            st.metric("Avg Lead Time", f"{avg_lead_time:.1f} days")
        with col3:
            avg_rating = sum(float(s.performance_rating or 0) for s in suppliers) / len(suppliers) if suppliers else 0
            st.metric("Avg Rating", f"{avg_rating:.1f}/5.0")
        with col4:
            active_suppliers = len([s for s in suppliers if s.performance_rating and s.performance_rating > 3.0])
            st.metric("High Performers", f"{active_suppliers} (>3.0)")
        
        # Display suppliers table
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Supplier details expander
        if st.checkbox("Show detailed view"):
            selected_supplier = st.selectbox("Select Supplier for Details", [s.supplier_id for s in suppliers])
            if selected_supplier:
                show_supplier_details(supplier_service, selected_supplier)
                
    except Exception as e:
        st.error(f"Error loading suppliers: {e}")

def show_supplier_details(supplier_service, supplier_id: str):
    """Show detailed information for a specific supplier"""
    try:
        supplier = supplier_service.get_supplier_by_id(supplier_id)
        if not supplier:
            st.error(f"Supplier {supplier_id} not found")
            return
        
        st.subheader(f"🏢 Supplier Details: {supplier.name}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Basic Information**")
            st.write(f"**Supplier ID:** {supplier.supplier_id}")
            st.write(f"**Name:** {supplier.name}")
            st.write(f"**Lead Time:** {supplier.lead_time_days} days")
            st.write(f"**Payment Terms:** {supplier.payment_terms or 'N/A'}")
            st.write(f"**Minimum Order Qty:** {supplier.minimum_order_qty}")
            st.write(f"**Performance Rating:** {float(supplier.performance_rating or 0):.1f}/5.0")
            
        with col2:
            st.write("**Contact Information**")
            if supplier.contact_info:
                contact = supplier.contact_info
                st.write(f"**Email:** {contact.get('email', 'N/A')}")
                st.write(f"**Phone:** {contact.get('phone', 'N/A')}")
                st.write(f"**Address:** {contact.get('address', 'N/A')}")
            else:
                st.write("No contact information available")
        
        # Supplier products
        try:
            products = supplier_service.get_supplier_products(supplier_id)
            if products:
                st.write("**Products Supplied**")
                products_df = pd.DataFrame(products)
                st.dataframe(products_df, use_container_width=True, hide_index=True)
            else:
                st.info("No products assigned to this supplier")
        except Exception as e:
            st.warning(f"Could not load supplier products: {e}")
        
        # Performance metrics
        try:
            performance = supplier_service.get_supplier_performance(supplier_id)
            if performance:
                st.write("**Performance Metrics**")
                perf_col1, perf_col2 = st.columns(2)
                
                with perf_col1:
                    st.metric("On-Time Delivery", f"{performance.get('on_time_delivery_rate', 0)*100:.1f}%")
                    st.metric("Quality Rating", f"{performance.get('quality_rating', 0):.1f}/5.0")
                
                with perf_col2:
                    st.metric("Total Orders", performance.get('total_orders', 0))
                    st.metric("Total Value", f"${performance.get('total_value', 0):,.2f}")
        except Exception as e:
            st.info("Performance data not available")
            
    except Exception as e:
        st.error(f"Error loading supplier details: {e}")

def show_add_supplier_form(supplier_service):
    """Show form to add a new supplier"""
    st.header("➕ Add New Supplier")
    
    with st.form("add_supplier_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            supplier_id = st.text_input("Supplier ID*", help="Unique supplier identifier")
            name = st.text_input("Supplier Name*")
            lead_time_days = st.number_input("Lead Time (days)*", min_value=1, value=7)
            payment_terms = st.text_input("Payment Terms", placeholder="e.g., Net 30")
            minimum_order_qty = st.number_input("Minimum Order Quantity", min_value=1, value=1)
        
        with col2:
            st.write("**Contact Information**")
            email = st.text_input("Email")
            phone = st.text_input("Phone")
            address = st.text_area("Address")
            
            st.write("**Performance**")
            initial_rating = st.slider("Initial Performance Rating", 0.0, 5.0, 3.0, 0.1)
        
        # Additional fields
        st.write("**Additional Information**")
        col3, col4 = st.columns(2)
        
        with col3:
            preferred_supplier = st.checkbox("Preferred Supplier")
            active_supplier = st.checkbox("Active Supplier", value=True)
        
        with col4:
            credit_terms = st.text_input("Credit Terms")
            tax_id = st.text_input("Tax ID")
        
        notes = st.text_area("Notes")
        
        submitted = st.form_submit_button("Add Supplier")
        
        if submitted:
            if not supplier_id or not name:
                st.error("Please fill in all required fields (marked with *)")
                return
            
            try:
                # Check if supplier ID already exists
                existing = supplier_service.get_supplier_by_id(supplier_id)
                if existing:
                    st.error(f"Supplier with ID '{supplier_id}' already exists")
                    return
                
                # Prepare contact info
                contact_info = {}
                if email:
                    contact_info['email'] = email
                if phone:
                    contact_info['phone'] = phone
                if address:
                    contact_info['address'] = address
                if credit_terms:
                    contact_info['credit_terms'] = credit_terms
                if tax_id:
                    contact_info['tax_id'] = tax_id
                
                # Prepare supplier data
                supplier_data = {
                    "supplier_id": supplier_id,
                    "name": name,
                    "contact_info": contact_info if contact_info else None,
                    "lead_time_days": lead_time_days,
                    "payment_terms": payment_terms,
                    "minimum_order_qty": minimum_order_qty,
                    "performance_rating": initial_rating,
                    "preferred": preferred_supplier,
                    "active": active_supplier,
                    "notes": notes
                }
                
                # Create supplier
                new_supplier = supplier_service.create_supplier(supplier_data)
                st.success(f"✅ Supplier '{name}' (ID: {supplier_id}) created successfully!")
                st.balloons()
                
                # Show created supplier details
                with st.expander("View Created Supplier"):
                    st.json({
                        "id": new_supplier.id,
                        "supplier_id": new_supplier.supplier_id,
                        "name": new_supplier.name,
                        "lead_time_days": new_supplier.lead_time_days,
                        "performance_rating": float(new_supplier.performance_rating or 0)
                    })
                
            except Exception as e:
                st.error(f"Error creating supplier: {e}")

def show_edit_supplier_form(supplier_service):
    """Show form to edit an existing supplier"""
    st.header("✏️ Edit Supplier")
    
    # Supplier selection
    try:
        suppliers = supplier_service.list_suppliers(limit=1000)
        if not suppliers:
            st.info("No suppliers available to edit.")
            return
        
        supplier_options = [f"{s.supplier_id} - {s.name}" for s in suppliers]
        selected_supplier = st.selectbox("Select Supplier to Edit", supplier_options)
        
        if not selected_supplier:
            return
        
        supplier_id = selected_supplier.split(" - ")[0]
        supplier = supplier_service.get_supplier_by_id(supplier_id)
        
        if not supplier:
            st.error("Selected supplier not found")
            return
        
        # Edit form
        with st.form("edit_supplier_form"):
            st.write(f"**Editing Supplier: {supplier.name} (ID: {supplier.supplier_id})**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Supplier Name", value=supplier.name)
                lead_time_days = st.number_input("Lead Time (days)", min_value=1, value=supplier.lead_time_days)
                payment_terms = st.text_input("Payment Terms", value=supplier.payment_terms or "")
                minimum_order_qty = st.number_input("Minimum Order Quantity", min_value=1, value=supplier.minimum_order_qty)
            
            with col2:
                st.write("**Contact Information**")
                contact_info = supplier.contact_info or {}
                email = st.text_input("Email", value=contact_info.get('email', ''))
                phone = st.text_input("Phone", value=contact_info.get('phone', ''))
                address = st.text_area("Address", value=contact_info.get('address', ''))
                
                performance_rating = st.slider(
                    "Performance Rating", 
                    0.0, 5.0, 
                    float(supplier.performance_rating or 3.0), 
                    0.1
                )
            
            submitted = st.form_submit_button("Update Supplier")
            
            if submitted:
                try:
                    # Prepare contact info
                    new_contact_info = {}
                    if email:
                        new_contact_info['email'] = email
                    if phone:
                        new_contact_info['phone'] = phone
                    if address:
                        new_contact_info['address'] = address
                    
                    updates = {
                        "name": name,
                        "contact_info": new_contact_info if new_contact_info else None,
                        "lead_time_days": lead_time_days,
                        "payment_terms": payment_terms,
                        "minimum_order_qty": minimum_order_qty,
                        "performance_rating": performance_rating
                    }
                    
                    updated_supplier = supplier_service.update_supplier(supplier.id, updates)
                    if updated_supplier:
                        st.success(f"✅ Supplier '{name}' updated successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to update supplier")
                        
                except Exception as e:
                    st.error(f"Error updating supplier: {e}")
                    
    except Exception as e:
        st.error(f"Error loading edit form: {e}")

def show_performance_analysis(supplier_service, inventory_service):
    """Show supplier performance analysis"""
    st.header("📊 Supplier Performance Analysis")
    
    # Time period selection
    col1, col2 = st.columns(2)
    with col1:
        days = st.selectbox("Analysis Period", [30, 60, 90, 180, 365], index=2)
    with col2:
        min_orders = st.number_input("Minimum Orders for Analysis", min_value=1, value=5)
    
    try:
        suppliers = supplier_service.list_suppliers()
        
        if not suppliers:
            st.info("No suppliers available for analysis.")
            return
        
        # Get performance data for all suppliers
        performance_data = []
        for supplier in suppliers:
            try:
                perf = supplier_service.get_supplier_performance(supplier.supplier_id, days)
                if perf and perf.get('total_orders', 0) >= min_orders:
                    performance_data.append({
                        'Supplier ID': supplier.supplier_id,
                        'Supplier Name': supplier.name,
                        'Rating': float(supplier.performance_rating or 0),
                        'Lead Time': supplier.lead_time_days,
                        'On-Time Delivery': perf.get('on_time_delivery_rate', 0) * 100,
                        'Quality Rating': perf.get('quality_rating', 0),
                        'Total Orders': perf.get('total_orders', 0),
                        'Total Value': perf.get('total_value', 0),
                        'Defect Rate': perf.get('defect_rate', 0) * 100
                    })
            except:
                # If performance data not available, use basic info
                performance_data.append({
                    'Supplier ID': supplier.supplier_id,
                    'Supplier Name': supplier.name,
                    'Rating': float(supplier.performance_rating or 0),
                    'Lead Time': supplier.lead_time_days,
                    'On-Time Delivery': 0,
                    'Quality Rating': 0,
                    'Total Orders': 0,
                    'Total Value': 0,
                    'Defect Rate': 0
                })
        
        if not performance_data:
            st.info(f"No suppliers with at least {min_orders} orders in the last {days} days.")
            return
        
        df = pd.DataFrame(performance_data)
        
        # Performance metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_rating = df['Rating'].mean()
            st.metric("Average Rating", f"{avg_rating:.1f}/5.0")
        
        with col2:
            avg_lead_time = df['Lead Time'].mean()
            st.metric("Average Lead Time", f"{avg_lead_time:.1f} days")
        
        with col3:
            avg_on_time = df['On-Time Delivery'].mean()
            st.metric("Average On-Time Delivery", f"{avg_on_time:.1f}%")
        
        with col4:
            total_value = df['Total Value'].sum()
            st.metric("Total Purchase Value", f"${total_value:,.2f}")
        
        # Performance charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Rating vs On-Time Delivery scatter plot
            fig_scatter = px.scatter(
                df, 
                x='Rating', 
                y='On-Time Delivery',
                size='Total Value',
                hover_data=['Supplier Name', 'Total Orders'],
                title="Rating vs On-Time Delivery",
                labels={'Rating': 'Performance Rating', 'On-Time Delivery': 'On-Time Delivery (%)'}
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
        
        with col2:
            # Lead time distribution
            fig_hist = px.histogram(
                df,
                x='Lead Time',
                title="Lead Time Distribution",
                labels={'Lead Time': 'Lead Time (days)', 'count': 'Number of Suppliers'}
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        
        # Top performers table
        st.subheader("🏆 Top Performing Suppliers")
        
        # Calculate performance score
        df['Performance Score'] = (
            (df['Rating'] / 5.0) * 0.3 +
            (df['On-Time Delivery'] / 100.0) * 0.3 +
            (df['Quality Rating'] / 5.0) * 0.2 +
            ((100 - df['Defect Rate']) / 100.0) * 0.2
        ) * 100
        
        top_performers = df.nlargest(10, 'Performance Score')[
            ['Supplier Name', 'Rating', 'On-Time Delivery', 'Quality Rating', 'Performance Score']
        ]
        
        # Format for display
        top_performers['Rating'] = top_performers['Rating'].apply(lambda x: f"{x:.1f}/5.0")
        top_performers['On-Time Delivery'] = top_performers['On-Time Delivery'].apply(lambda x: f"{x:.1f}%")
        top_performers['Quality Rating'] = top_performers['Quality Rating'].apply(lambda x: f"{x:.1f}/5.0")
        top_performers['Performance Score'] = top_performers['Performance Score'].apply(lambda x: f"{x:.1f}")
        
        st.dataframe(top_performers, use_container_width=True, hide_index=True)
        
        # Full performance table
        st.subheader("📋 Complete Performance Data")
        
        # Format full dataframe for display
        df_display = df.copy()
        df_display['Rating'] = df_display['Rating'].apply(lambda x: f"{x:.1f}/5.0")
        df_display['On-Time Delivery'] = df_display['On-Time Delivery'].apply(lambda x: f"{x:.1f}%")
        df_display['Quality Rating'] = df_display['Quality Rating'].apply(lambda x: f"{x:.1f}/5.0")
        df_display['Total Value'] = df_display['Total Value'].apply(lambda x: f"${x:,.2f}")
        df_display['Defect Rate'] = df_display['Defect Rate'].apply(lambda x: f"{x:.1f}%")
        df_display['Performance Score'] = df_display['Performance Score'].apply(lambda x: f"{x:.1f}")
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        # Export option
        if st.button("📥 Export Performance Data"):
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"supplier_performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
    except Exception as e:
        st.error(f"Error loading performance analysis: {e}")

def show_import_suppliers(supplier_service):
    """Show supplier import functionality"""
    st.header("📥 Import Suppliers")
    
    st.info("Upload a CSV file with supplier data to bulk import suppliers.")
    
    # Show expected format
    with st.expander("📋 Expected CSV Format"):
        st.write("Your CSV file should have the following columns:")
        sample_data = {
            "supplier_id": ["SUP-001", "SUP-002", "SUP-003"],
            "name": ["Supplier A", "Supplier B", "Supplier C"],
            "email": ["contact@suppA.com", "info@suppB.com", "sales@suppC.com"],
            "phone": ["+1-555-0001", "+1-555-0002", "+1-555-0003"],
            "lead_time_days": [7, 14, 5],
            "payment_terms": ["Net 30", "Net 15", "COD"],
            "minimum_order_qty": [100, 50, 25],
            "performance_rating": [4.2, 3.8, 4.5]
        }
        st.dataframe(pd.DataFrame(sample_data))
    
    uploaded_file = st.file_uploader(
        "Choose CSV file",
        type="csv",
        help="Upload a CSV file with supplier data"
    )
    
    if uploaded_file is not None:
        try:
            # Read CSV
            df = pd.read_csv(uploaded_file)
            
            st.write("**Preview of uploaded data:**")
            st.dataframe(df.head())
            
            # Validate required columns
            required_columns = ["supplier_id", "name"]
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.error(f"Missing required columns: {', '.join(missing_columns)}")
                return
            
            # Show import summary
            st.write(f"**Import Summary:**")
            st.write(f"- Total rows: {len(df)}")
            st.write(f"- Columns: {', '.join(df.columns)}")
            
            if st.button("Import Suppliers"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                imported = 0
                errors = []
                
                for index, row in df.iterrows():
                    try:
                        # Check if supplier exists
                        existing = supplier_service.get_supplier_by_id(row['supplier_id'])
                        if existing:
                            errors.append(f"Row {index + 1}: Supplier ID '{row['supplier_id']}' already exists")
                            continue
                        
                        # Prepare contact info
                        contact_info = {}
                        if 'email' in row and pd.notna(row['email']):
                            contact_info['email'] = str(row['email'])
                        if 'phone' in row and pd.notna(row['phone']):
                            contact_info['phone'] = str(row['phone'])
                        if 'address' in row and pd.notna(row['address']):
                            contact_info['address'] = str(row['address'])
                        
                        # Prepare supplier data
                        supplier_data = {
                            "supplier_id": str(row['supplier_id']),
                            "name": str(row['name']),
                            "contact_info": contact_info if contact_info else None,
                            "lead_time_days": int(row.get('lead_time_days', 7)),
                            "payment_terms": str(row.get('payment_terms', '')) if pd.notna(row.get('payment_terms')) else None,
                            "minimum_order_qty": int(row.get('minimum_order_qty', 1)),
                            "performance_rating": float(row.get('performance_rating', 3.0)) if pd.notna(row.get('performance_rating')) else None
                        }
                        
                        # Create supplier
                        supplier_service.create_supplier(supplier_data)
                        imported += 1
                        
                    except Exception as e:
                        errors.append(f"Row {index + 1}: {str(e)}")
                    
                    # Update progress
                    progress = (index + 1) / len(df)
                    progress_bar.progress(progress)
                    status_text.text(f"Processing row {index + 1} of {len(df)}")
                
                # Show results
                st.success(f"✅ Import completed! {imported} suppliers imported successfully.")
                
                if errors:
                    st.error(f"❌ {len(errors)} errors occurred:")
                    for error in errors[:10]:  # Show first 10 errors
                        st.write(f"- {error}")
                    if len(errors) > 10:
                        st.write(f"... and {len(errors) - 10} more errors")
                
        except Exception as e:
            st.error(f"Error processing CSV file: {e}")

if __name__ == "__main__":
    render_suppliers_page()
