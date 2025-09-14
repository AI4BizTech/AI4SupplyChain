"""
Product master data management page
"""

import streamlit as st
import pandas as pd
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

def render_products_page():
    """Render the product master data management page"""
    st.title("📦 Product Master Data Management")
    
    # Sidebar for actions
    with st.sidebar:
        st.header("Product Actions")
        action = st.selectbox(
            "Choose Action",
            ["View Products", "Add Product", "Edit Product", "Import Products"]
        )
    
    try:
        from src.services.inventory import InventoryService
        from src.services.suppliers import SupplierService
        
        inventory_service = InventoryService()
        supplier_service = SupplierService()
        
        if action == "View Products":
            show_products_list(inventory_service)
        elif action == "Add Product":
            show_add_product_form(inventory_service, supplier_service)
        elif action == "Edit Product":
            show_edit_product_form(inventory_service, supplier_service)
        elif action == "Import Products":
            show_import_products(inventory_service)
            
    except Exception as e:
        st.error(f"Error loading product management: {e}")
        st.info("Please ensure the database is initialized and services are available.")

def show_products_list(inventory_service):
    """Show list of all products"""
    st.header("📋 Product Catalog")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        category_filter = st.selectbox(
            "Filter by Category",
            ["All"] + get_categories(inventory_service)
        )
    
    with col2:
        search_sku = st.text_input("Search by SKU")
    
    with col3:
        limit = st.number_input("Max Results", min_value=10, max_value=1000, value=100)
    
    # Get products
    try:
        category = None if category_filter == "All" else category_filter
        products = inventory_service.list_products(category=category, limit=limit)
        
        if search_sku:
            products = [p for p in products if search_sku.upper() in p.sku.upper()]
        
        if not products:
            st.info("No products found matching the criteria.")
            return
        
        # Convert to DataFrame for display
        products_data = []
        for product in products:
            products_data.append({
                "SKU": product.sku,
                "Name": product.name,
                "Category": product.category,
                "Unit Cost": f"${float(product.unit_cost):.2f}",
                "Reorder Point": product.reorder_point,
                "Reorder Qty": product.reorder_quantity,
                "Supplier ID": product.supplier_id or "N/A"
            })
        
        df = pd.DataFrame(products_data)
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Products", len(products))
        with col2:
            total_value = sum(float(p.unit_cost) * p.reorder_quantity for p in products)
            st.metric("Total Catalog Value", f"${total_value:,.2f}")
        with col3:
            categories = len(set(p.category for p in products))
            st.metric("Categories", categories)
        with col4:
            avg_cost = sum(float(p.unit_cost) for p in products) / len(products) if products else 0
            st.metric("Avg Unit Cost", f"${avg_cost:.2f}")
        
        # Display products table
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Product details expander
        if st.checkbox("Show detailed view"):
            selected_sku = st.selectbox("Select Product for Details", [p.sku for p in products])
            if selected_sku:
                show_product_details(inventory_service, selected_sku)
                
    except Exception as e:
        st.error(f"Error loading products: {e}")

def show_product_details(inventory_service, sku: str):
    """Show detailed information for a specific product"""
    try:
        product = inventory_service.get_product_by_sku(sku)
        if not product:
            st.error(f"Product {sku} not found")
            return
        
        st.subheader(f"📦 Product Details: {product.name}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Basic Information**")
            st.write(f"**SKU:** {product.sku}")
            st.write(f"**Name:** {product.name}")
            st.write(f"**Category:** {product.category}")
            st.write(f"**Description:** {product.description or 'N/A'}")
            
        with col2:
            st.write("**Inventory Settings**")
            st.write(f"**Unit Cost:** ${float(product.unit_cost):.2f}")
            st.write(f"**Reorder Point:** {product.reorder_point} units")
            st.write(f"**Reorder Quantity:** {product.reorder_quantity} units")
            st.write(f"**Weight:** {float(product.weight or 0):.2f} kg")
        
        # Current stock levels
        stock_levels = inventory_service.get_stock_levels(sku)
        if stock_levels:
            st.write("**Current Stock Levels**")
            stock_df = pd.DataFrame(stock_levels)
            st.dataframe(stock_df, use_container_width=True, hide_index=True)
        
        # Recent transactions
        transactions = inventory_service.get_transaction_history(product_id=product.id, limit=10)
        if transactions:
            st.write("**Recent Transactions**")
            trans_df = pd.DataFrame(transactions)
            st.dataframe(trans_df, use_container_width=True, hide_index=True)
            
    except Exception as e:
        st.error(f"Error loading product details: {e}")

def show_add_product_form(inventory_service, supplier_service):
    """Show form to add a new product"""
    st.header("➕ Add New Product")
    
    with st.form("add_product_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            sku = st.text_input("SKU*", help="Unique product identifier")
            name = st.text_input("Product Name*")
            category = st.selectbox(
                "Category*",
                ["Electronics", "Office Supplies", "Industrial Tools", "Automotive Parts",
                 "Medical Supplies", "Food & Beverages", "Clothing", "Furniture",
                 "Sporting Goods", "Books & Media", "Other"]
            )
            description = st.text_area("Description")
        
        with col2:
            unit_cost = st.number_input("Unit Cost ($)*", min_value=0.01, value=1.00, step=0.01)
            reorder_point = st.number_input("Reorder Point", min_value=0, value=10)
            reorder_quantity = st.number_input("Reorder Quantity", min_value=1, value=50)
            weight = st.number_input("Weight (kg)", min_value=0.0, value=0.0, step=0.1)
        
        # Supplier selection
        try:
            suppliers = supplier_service.list_suppliers()
            supplier_options = ["None"] + [f"{s.supplier_id} - {s.name}" for s in suppliers]
            selected_supplier = st.selectbox("Supplier", supplier_options)
            
            supplier_id = None
            if selected_supplier != "None":
                supplier_id = int(selected_supplier.split(" - ")[0].split("-")[0])
        except:
            st.info("No suppliers available. Add suppliers first.")
            supplier_id = None
        
        # Dimensions
        st.write("**Dimensions (optional)**")
        col3, col4, col5 = st.columns(3)
        with col3:
            length = st.number_input("Length (cm)", min_value=0.0, value=0.0)
        with col4:
            width = st.number_input("Width (cm)", min_value=0.0, value=0.0)
        with col5:
            height = st.number_input("Height (cm)", min_value=0.0, value=0.0)
        
        submitted = st.form_submit_button("Add Product")
        
        if submitted:
            if not sku or not name or not category:
                st.error("Please fill in all required fields (marked with *)")
                return
            
            try:
                # Check if SKU already exists
                existing = inventory_service.get_product_by_sku(sku)
                if existing:
                    st.error(f"Product with SKU '{sku}' already exists")
                    return
                
                # Prepare product data
                product_data = {
                    "sku": sku,
                    "name": name,
                    "category": category,
                    "description": description,
                    "unit_cost": unit_cost,
                    "supplier_id": supplier_id,
                    "reorder_point": reorder_point,
                    "reorder_quantity": reorder_quantity,
                    "weight": weight if weight > 0 else None,
                    "dimensions": {
                        "length": length,
                        "width": width,
                        "height": height
                    } if any([length, width, height]) else None
                }
                
                # Create product
                new_product = inventory_service.create_product(product_data)
                st.success(f"✅ Product '{name}' (SKU: {sku}) created successfully!")
                st.balloons()
                
                # Show created product details
                with st.expander("View Created Product"):
                    st.json({
                        "id": new_product.id,
                        "sku": new_product.sku,
                        "name": new_product.name,
                        "category": new_product.category,
                        "unit_cost": float(new_product.unit_cost)
                    })
                
            except Exception as e:
                st.error(f"Error creating product: {e}")

def show_edit_product_form(inventory_service, supplier_service):
    """Show form to edit an existing product"""
    st.header("✏️ Edit Product")
    
    # Product selection
    try:
        products = inventory_service.list_products(limit=1000)
        if not products:
            st.info("No products available to edit.")
            return
        
        product_options = [f"{p.sku} - {p.name}" for p in products]
        selected_product = st.selectbox("Select Product to Edit", product_options)
        
        if not selected_product:
            return
        
        sku = selected_product.split(" - ")[0]
        product = inventory_service.get_product_by_sku(sku)
        
        if not product:
            st.error("Selected product not found")
            return
        
        # Edit form
        with st.form("edit_product_form"):
            st.write(f"**Editing Product: {product.name} (SKU: {product.sku})**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Product Name", value=product.name)
                category = st.selectbox(
                    "Category",
                    ["Electronics", "Office Supplies", "Industrial Tools", "Automotive Parts",
                     "Medical Supplies", "Food & Beverages", "Clothing", "Furniture",
                     "Sporting Goods", "Books & Media", "Other"],
                    index=0 if product.category not in ["Electronics", "Office Supplies", "Industrial Tools", "Automotive Parts",
                                                       "Medical Supplies", "Food & Beverages", "Clothing", "Furniture",
                                                       "Sporting Goods", "Books & Media", "Other"] else 
                    ["Electronics", "Office Supplies", "Industrial Tools", "Automotive Parts",
                     "Medical Supplies", "Food & Beverages", "Clothing", "Furniture",
                     "Sporting Goods", "Books & Media", "Other"].index(product.category)
                )
                description = st.text_area("Description", value=product.description or "")
            
            with col2:
                unit_cost = st.number_input("Unit Cost ($)", min_value=0.01, value=float(product.unit_cost), step=0.01)
                reorder_point = st.number_input("Reorder Point", min_value=0, value=product.reorder_point)
                reorder_quantity = st.number_input("Reorder Quantity", min_value=1, value=product.reorder_quantity)
                weight = st.number_input("Weight (kg)", min_value=0.0, value=float(product.weight or 0), step=0.1)
            
            submitted = st.form_submit_button("Update Product")
            
            if submitted:
                try:
                    updates = {
                        "name": name,
                        "category": category,
                        "description": description,
                        "unit_cost": unit_cost,
                        "reorder_point": reorder_point,
                        "reorder_quantity": reorder_quantity,
                        "weight": weight if weight > 0 else None
                    }
                    
                    updated_product = inventory_service.update_product(product.id, updates)
                    if updated_product:
                        st.success(f"✅ Product '{name}' updated successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to update product")
                        
                except Exception as e:
                    st.error(f"Error updating product: {e}")
                    
    except Exception as e:
        st.error(f"Error loading edit form: {e}")

def show_import_products(inventory_service):
    """Show product import functionality"""
    st.header("📥 Import Products")
    
    st.info("Upload a CSV file with product data to bulk import products.")
    
    # Show expected format
    with st.expander("📋 Expected CSV Format"):
        st.write("Your CSV file should have the following columns:")
        sample_data = {
            "sku": ["SKU-001", "SKU-002", "SKU-003"],
            "name": ["Product 1", "Product 2", "Product 3"],
            "category": ["Electronics", "Office Supplies", "Industrial Tools"],
            "description": ["Description 1", "Description 2", "Description 3"],
            "unit_cost": [25.99, 15.50, 45.00],
            "reorder_point": [10, 20, 5],
            "reorder_quantity": [50, 100, 25],
            "weight": [1.5, 0.5, 3.2]
        }
        st.dataframe(pd.DataFrame(sample_data))
    
    uploaded_file = st.file_uploader(
        "Choose CSV file",
        type="csv",
        help="Upload a CSV file with product data"
    )
    
    if uploaded_file is not None:
        try:
            # Read CSV
            df = pd.read_csv(uploaded_file)
            
            st.write("**Preview of uploaded data:**")
            st.dataframe(df.head())
            
            # Validate required columns
            required_columns = ["sku", "name", "category", "unit_cost"]
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.error(f"Missing required columns: {', '.join(missing_columns)}")
                return
            
            # Show import summary
            st.write(f"**Import Summary:**")
            st.write(f"- Total rows: {len(df)}")
            st.write(f"- Columns: {', '.join(df.columns)}")
            
            if st.button("Import Products"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                imported = 0
                errors = []
                
                for index, row in df.iterrows():
                    try:
                        # Check if product exists
                        existing = inventory_service.get_product_by_sku(row['sku'])
                        if existing:
                            errors.append(f"Row {index + 1}: SKU '{row['sku']}' already exists")
                            continue
                        
                        # Prepare product data
                        product_data = {
                            "sku": str(row['sku']),
                            "name": str(row['name']),
                            "category": str(row['category']),
                            "unit_cost": float(row['unit_cost']),
                            "description": str(row.get('description', '')),
                            "reorder_point": int(row.get('reorder_point', 10)),
                            "reorder_quantity": int(row.get('reorder_quantity', 50)),
                            "weight": float(row.get('weight', 0)) if pd.notna(row.get('weight')) else None
                        }
                        
                        # Create product
                        inventory_service.create_product(product_data)
                        imported += 1
                        
                    except Exception as e:
                        errors.append(f"Row {index + 1}: {str(e)}")
                    
                    # Update progress
                    progress = (index + 1) / len(df)
                    progress_bar.progress(progress)
                    status_text.text(f"Processing row {index + 1} of {len(df)}")
                
                # Show results
                st.success(f"✅ Import completed! {imported} products imported successfully.")
                
                if errors:
                    st.error(f"❌ {len(errors)} errors occurred:")
                    for error in errors[:10]:  # Show first 10 errors
                        st.write(f"- {error}")
                    if len(errors) > 10:
                        st.write(f"... and {len(errors) - 10} more errors")
                
        except Exception as e:
            st.error(f"Error processing CSV file: {e}")

def get_categories(inventory_service) -> list:
    """Get list of unique categories from existing products"""
    try:
        products = inventory_service.list_products(limit=1000)
        categories = list(set(p.category for p in products))
        return sorted(categories)
    except:
        return []

if __name__ == "__main__":
    render_products_page()
