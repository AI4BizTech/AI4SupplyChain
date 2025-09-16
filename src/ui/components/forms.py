"""
Form components for the Streamlit UI
"""

import streamlit as st
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, date
import json

def create_product_form(product_data: Optional[Dict[str, Any]] = None, 
                       form_key: str = "product_form") -> Optional[Dict[str, Any]]:
    """Create a product input form"""
    
    is_edit = product_data is not None
    
    with st.form(form_key):
        st.subheader("➕ Add New Product" if not is_edit else f"✏️ Edit Product")
        
        col1, col2 = st.columns(2)
        
        with col1:
            sku = st.text_input(
                "SKU*", 
                value=product_data.get('sku', '') if is_edit else '',
                disabled=is_edit,  # SKU shouldn't be editable
                help="Unique product identifier"
            )
            
            name = st.text_input(
                "Product Name*",
                value=product_data.get('name', '') if is_edit else '',
                help="Full product name"
            )
            
            category = st.selectbox(
                "Category*",
                options=[
                    "Electronics", "Office Supplies", "Industrial Tools", 
                    "Automotive Parts", "Medical Supplies", "Food & Beverages",
                    "Clothing", "Furniture", "Sporting Goods", "Books & Media", "Other"
                ],
                index=0 if not is_edit else (
                    ["Electronics", "Office Supplies", "Industrial Tools", 
                     "Automotive Parts", "Medical Supplies", "Food & Beverages",
                     "Clothing", "Furniture", "Sporting Goods", "Books & Media", "Other"]
                    .index(product_data.get('category', 'Other')) 
                    if product_data.get('category') in [
                        "Electronics", "Office Supplies", "Industrial Tools", 
                        "Automotive Parts", "Medical Supplies", "Food & Beverages",
                        "Clothing", "Furniture", "Sporting Goods", "Books & Media", "Other"
                    ] else 0
                )
            )
            
            description = st.text_area(
                "Description",
                value=product_data.get('description', '') if is_edit else '',
                help="Product description"
            )
        
        with col2:
            unit_cost = st.number_input(
                "Unit Cost ($)*",
                min_value=0.01,
                value=float(product_data.get('unit_cost', 1.0)) if is_edit else 1.0,
                step=0.01,
                help="Cost per unit"
            )
            
            reorder_point = st.number_input(
                "Reorder Point",
                min_value=0,
                value=int(product_data.get('reorder_point', 10)) if is_edit else 10,
                help="Minimum stock level before reordering"
            )
            
            reorder_quantity = st.number_input(
                "Reorder Quantity",
                min_value=1,
                value=int(product_data.get('reorder_quantity', 50)) if is_edit else 50,
                help="Quantity to order when restocking"
            )
            
            weight = st.number_input(
                "Weight (kg)",
                min_value=0.0,
                value=float(product_data.get('weight', 0.0)) if is_edit and product_data.get('weight') else 0.0,
                step=0.1,
                help="Product weight in kilograms"
            )
        
        # Additional fields
        with st.expander("📏 Additional Information"):
            col3, col4, col5 = st.columns(3)
            
            with col3:
                length = st.number_input(
                    "Length (cm)",
                    min_value=0.0,
                    value=0.0,
                    help="Product length"
                )
            
            with col4:
                width = st.number_input(
                    "Width (cm)",
                    min_value=0.0,
                    value=0.0,
                    help="Product width"
                )
            
            with col5:
                height = st.number_input(
                    "Height (cm)",
                    min_value=0.0,
                    value=0.0,
                    help="Product height"
                )
            
            barcode = st.text_input("Barcode/UPC", help="Product barcode or UPC")
            tags = st.text_input("Tags", help="Comma-separated tags for categorization")
        
        submitted = st.form_submit_button(
            "Update Product" if is_edit else "Create Product",
            use_container_width=True
        )
        
        if submitted:
            if not sku or not name or not category:
                st.error("Please fill in all required fields (marked with *)")
                return None
            
            # Prepare form data
            form_data = {
                "sku": sku,
                "name": name,
                "category": category,
                "description": description,
                "unit_cost": unit_cost,
                "reorder_point": reorder_point,
                "reorder_quantity": reorder_quantity,
                "weight": weight if weight > 0 else None,
                "dimensions": {
                    "length": length,
                    "width": width,
                    "height": height
                } if any([length, width, height]) else None,
                "barcode": barcode if barcode else None,
                "tags": [tag.strip() for tag in tags.split(",")] if tags else None
            }
            
            return form_data
    
    return None

def create_supplier_form(supplier_data: Optional[Dict[str, Any]] = None,
                        form_key: str = "supplier_form") -> Optional[Dict[str, Any]]:
    """Create a supplier input form"""
    
    is_edit = supplier_data is not None
    
    with st.form(form_key):
        st.subheader("➕ Add New Supplier" if not is_edit else f"✏️ Edit Supplier")
        
        col1, col2 = st.columns(2)
        
        with col1:
            supplier_id = st.text_input(
                "Supplier ID*",
                value=supplier_data.get('supplier_id', '') if is_edit else '',
                disabled=is_edit,  # Supplier ID shouldn't be editable
                help="Unique supplier identifier"
            )
            
            name = st.text_input(
                "Supplier Name*",
                value=supplier_data.get('name', '') if is_edit else '',
                help="Full supplier name"
            )
            
            lead_time_days = st.number_input(
                "Lead Time (days)*",
                min_value=1,
                value=int(supplier_data.get('lead_time_days', 7)) if is_edit else 7,
                help="Average lead time in days"
            )
            
            payment_terms = st.text_input(
                "Payment Terms",
                value=supplier_data.get('payment_terms', '') if is_edit else '',
                placeholder="e.g., Net 30, COD, 2/10 Net 30",
                help="Payment terms and conditions"
            )
            
            minimum_order_qty = st.number_input(
                "Minimum Order Quantity",
                min_value=1,
                value=int(supplier_data.get('minimum_order_qty', 1)) if is_edit else 1,
                help="Minimum order quantity"
            )
        
        with col2:
            st.write("**Contact Information**")
            
            contact_info = supplier_data.get('contact_info', {}) if is_edit else {}
            
            email = st.text_input(
                "Email",
                value=contact_info.get('email', '') if contact_info else '',
                help="Primary contact email"
            )
            
            phone = st.text_input(
                "Phone",
                value=contact_info.get('phone', '') if contact_info else '',
                help="Primary contact phone"
            )
            
            address = st.text_area(
                "Address",
                value=contact_info.get('address', '') if contact_info else '',
                help="Supplier address"
            )
            
            website = st.text_input(
                "Website",
                value=contact_info.get('website', '') if contact_info else '',
                placeholder="https://example.com",
                help="Supplier website"
            )
        
        # Performance and additional info
        with st.expander("📊 Performance & Additional Info"):
            col3, col4 = st.columns(2)
            
            with col3:
                performance_rating = st.slider(
                    "Initial Performance Rating",
                    min_value=1.0,
                    max_value=5.0,
                    value=float(supplier_data.get('performance_rating', 3.0)) if is_edit else 3.0,
                    step=0.1,
                    help="Performance rating (1-5)"
                )
                
                preferred = st.checkbox(
                    "Preferred Supplier",
                    value=supplier_data.get('preferred', False) if is_edit else False
                )
                
                active = st.checkbox(
                    "Active Supplier",
                    value=supplier_data.get('active', True) if is_edit else True
                )
            
            with col4:
                tax_id = st.text_input(
                    "Tax ID",
                    value=contact_info.get('tax_id', '') if contact_info else '',
                    help="Supplier tax identification number"
                )
                
                credit_limit = st.number_input(
                    "Credit Limit ($)",
                    min_value=0.0,
                    value=float(supplier_data.get('credit_limit', 0.0)) if is_edit and supplier_data.get('credit_limit') else 0.0,
                    step=100.0,
                    help="Credit limit for this supplier"
                )
                
                currency = st.selectbox(
                    "Currency",
                    options=["USD", "EUR", "GBP", "CAD", "JPY", "AUD"],
                    index=0,
                    help="Default currency for transactions"
                )
        
        notes = st.text_area(
            "Notes",
            value=supplier_data.get('notes', '') if is_edit else '',
            help="Additional notes about the supplier"
        )
        
        submitted = st.form_submit_button(
            "Update Supplier" if is_edit else "Create Supplier",
            use_container_width=True
        )
        
        if submitted:
            if not supplier_id or not name:
                st.error("Please fill in all required fields (marked with *)")
                return None
            
            # Prepare contact info
            contact_data = {}
            if email:
                contact_data['email'] = email
            if phone:
                contact_data['phone'] = phone
            if address:
                contact_data['address'] = address
            if website:
                contact_data['website'] = website
            if tax_id:
                contact_data['tax_id'] = tax_id
            
            # Prepare form data
            form_data = {
                "supplier_id": supplier_id,
                "name": name,
                "contact_info": contact_data if contact_data else None,
                "lead_time_days": lead_time_days,
                "payment_terms": payment_terms if payment_terms else None,
                "minimum_order_qty": minimum_order_qty,
                "performance_rating": performance_rating,
                "preferred": preferred,
                "active": active,
                "credit_limit": credit_limit if credit_limit > 0 else None,
                "currency": currency,
                "notes": notes if notes else None
            }
            
            return form_data
    
    return None

def create_transaction_form(form_key: str = "transaction_form") -> Optional[Dict[str, Any]]:
    """Create a transaction input form"""
    
    with st.form(form_key):
        st.subheader("➕ Create Transaction")
        
        col1, col2 = st.columns(2)
        
        with col1:
            product_sku = st.text_input(
                "Product SKU*",
                help="Enter the product SKU"
            )
            
            location_id = st.selectbox(
                "Location*",
                options=["MAIN-WH", "STORE-A", "STORE-B", "DIST-CENTER"],
                help="Select transaction location"
            )
            
            transaction_type = st.selectbox(
                "Transaction Type*",
                options=["receipt", "shipment", "adjustment", "transfer"],
                format_func=lambda x: {
                    "receipt": "📦 Receipt (Inbound)",
                    "shipment": "📤 Shipment (Outbound)",
                    "adjustment": "⚖️ Adjustment",
                    "transfer": "🔄 Transfer"
                }[x],
                help="Type of inventory transaction"
            )
        
        with col2:
            quantity = st.number_input(
                "Quantity*",
                value=0,
                help="Positive for inbound, negative for outbound"
            )
            
            unit_cost = st.number_input(
                "Unit Cost ($)",
                min_value=0.0,
                value=0.0,
                step=0.01,
                help="Cost per unit for this transaction"
            )
            
            reference_document = st.text_input(
                "Reference Document",
                placeholder="PO-12345, INV-67890, etc.",
                help="Reference document number"
            )
        
        user_id = st.text_input(
            "User ID",
            value="admin",
            help="User performing the transaction"
        )
        
        notes = st.text_area(
            "Notes",
            help="Additional notes about this transaction"
        )
        
        submitted = st.form_submit_button("Create Transaction", use_container_width=True)
        
        if submitted:
            if not product_sku or not location_id or quantity == 0:
                st.error("Please fill in all required fields and enter a non-zero quantity")
                return None
            
            form_data = {
                "product_sku": product_sku,
                "location_id": location_id,
                "transaction_type": transaction_type,
                "quantity": quantity,
                "unit_cost": unit_cost if unit_cost > 0 else None,
                "reference_document": reference_document if reference_document else None,
                "user_id": user_id,
                "notes": notes if notes else None
            }
            
            return form_data
    
    return None

def create_forecast_form(form_key: str = "forecast_form") -> Optional[Dict[str, Any]]:
    """Create a demand forecast input form"""
    
    with st.form(form_key):
        st.subheader("🔮 Generate Forecast")
        
        col1, col2 = st.columns(2)
        
        with col1:
            product_sku = st.text_input(
                "Product SKU*",
                help="Enter the product SKU to forecast"
            )
            
            horizon_days = st.number_input(
                "Forecast Horizon (days)*",
                min_value=1,
                max_value=365,
                value=30,
                help="Number of days to forecast"
            )
        
        with col2:
            method = st.selectbox(
                "Forecasting Method",
                options=["auto", "moving_average", "exponential_smoothing", "trend_analysis"],
                format_func=lambda x: {
                    "auto": "🤖 Auto (Best Method)",
                    "moving_average": "📊 Moving Average",
                    "exponential_smoothing": "📈 Exponential Smoothing",
                    "trend_analysis": "📉 Trend Analysis"
                }[x],
                help="Choose forecasting method"
            )
            
            confidence_level = st.slider(
                "Confidence Level (%)",
                min_value=80,
                max_value=99,
                value=95,
                help="Confidence level for forecast intervals"
            )
        
        include_seasonality = st.checkbox(
            "Include Seasonality Analysis",
            value=True,
            help="Analyze seasonal patterns in the data"
        )
        
        submitted = st.form_submit_button("Generate Forecast", use_container_width=True)
        
        if submitted:
            if not product_sku:
                st.error("Please enter a product SKU")
                return None
            
            form_data = {
                "product_sku": product_sku,
                "horizon_days": horizon_days,
                "method": method,
                "confidence_level": confidence_level / 100,
                "include_seasonality": include_seasonality
            }
            
            return form_data
    
    return None

def create_optimization_form(form_key: str = "optimization_form") -> Optional[Dict[str, Any]]:
    """Create an optimization parameters form"""
    
    with st.form(form_key):
        st.subheader("⚙️ Optimization Parameters")
        
        optimization_type = st.selectbox(
            "Optimization Type",
            options=["eoq", "reorder_point", "safety_stock"],
            format_func=lambda x: {
                "eoq": "📊 Economic Order Quantity (EOQ)",
                "reorder_point": "🎯 Reorder Point",
                "safety_stock": "🛡️ Safety Stock"
            }[x]
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            product_sku = st.text_input(
                "Product SKU*",
                help="Enter product SKU for optimization"
            )
            
            if optimization_type in ["eoq", "reorder_point"]:
                annual_demand = st.number_input(
                    "Annual Demand (units)",
                    min_value=1,
                    value=1000,
                    help="Expected annual demand"
                )
            
            if optimization_type == "eoq":
                ordering_cost = st.number_input(
                    "Ordering Cost ($/order)",
                    min_value=0.01,
                    value=50.0,
                    step=0.01,
                    help="Cost to place one order"
                )
        
        with col2:
            if optimization_type in ["reorder_point", "safety_stock"]:
                service_level = st.slider(
                    "Service Level (%)",
                    min_value=80,
                    max_value=99,
                    value=95,
                    help="Desired service level"
                )
                
                lead_time_days = st.number_input(
                    "Lead Time (days)",
                    min_value=1,
                    value=7,
                    help="Supplier lead time"
                )
            
            if optimization_type == "eoq":
                carrying_cost_rate = st.slider(
                    "Carrying Cost Rate (%/year)",
                    min_value=1.0,
                    max_value=50.0,
                    value=20.0,
                    step=0.5,
                    help="Annual carrying cost as % of unit cost"
                )
        
        # Advanced parameters
        with st.expander("🔧 Advanced Parameters"):
            if optimization_type in ["reorder_point", "safety_stock"]:
                demand_variability = st.slider(
                    "Demand Variability (CV)",
                    min_value=0.1,
                    max_value=2.0,
                    value=0.3,
                    step=0.1,
                    help="Coefficient of variation for demand"
                )
                
                lead_time_variability = st.number_input(
                    "Lead Time Variability (days)",
                    min_value=0,
                    value=1,
                    help="Standard deviation of lead time"
                )
        
        submitted = st.form_submit_button("Calculate Optimization", use_container_width=True)
        
        if submitted:
            if not product_sku:
                st.error("Please enter a product SKU")
                return None
            
            form_data = {
                "product_sku": product_sku,
                "optimization_type": optimization_type
            }
            
            if optimization_type == "eoq":
                form_data.update({
                    "annual_demand": annual_demand,
                    "ordering_cost": ordering_cost,
                    "carrying_cost_rate": carrying_cost_rate / 100
                })
            elif optimization_type in ["reorder_point", "safety_stock"]:
                form_data.update({
                    "service_level": service_level / 100,
                    "lead_time_days": lead_time_days,
                    "demand_variability": demand_variability,
                    "lead_time_variability": lead_time_variability
                })
                if optimization_type == "reorder_point":
                    form_data["annual_demand"] = annual_demand
            
            return form_data
    
    return None

def create_filter_form(filter_options: Dict[str, List[str]], 
                      form_key: str = "filter_form") -> Optional[Dict[str, Any]]:
    """Create a generic filter form"""
    
    with st.form(form_key):
        st.subheader("🔍 Filters")
        
        filters = {}
        
        # Create filter inputs based on options
        num_cols = min(len(filter_options), 3)
        cols = st.columns(num_cols)
        
        for i, (filter_name, options) in enumerate(filter_options.items()):
            with cols[i % num_cols]:
                display_name = filter_name.replace('_', ' ').title()
                
                if isinstance(options, list):
                    # Dropdown filter
                    selected = st.selectbox(
                        display_name,
                        options=["All"] + options,
                        key=f"filter_{filter_name}"
                    )
                    filters[filter_name] = None if selected == "All" else selected
                
                elif isinstance(options, dict):
                    # Range filter
                    if 'min' in options and 'max' in options:
                        min_val, max_val = st.slider(
                            display_name,
                            min_value=options['min'],
                            max_value=options['max'],
                            value=(options['min'], options['max']),
                            key=f"filter_{filter_name}"
                        )
                        filters[filter_name] = {'min': min_val, 'max': max_val}
        
        # Date range filter
        if 'date_range' in filter_options:
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input(
                    "Start Date",
                    value=datetime.now().date() - timedelta(days=30),
                    key="filter_start_date"
                )
            with col2:
                end_date = st.date_input(
                    "End Date",
                    value=datetime.now().date(),
                    key="filter_end_date"
                )
            filters['date_range'] = {'start': start_date, 'end': end_date}
        
        # Search filter
        search_term = st.text_input(
            "Search",
            placeholder="Enter search term...",
            key="filter_search"
        )
        if search_term:
            filters['search'] = search_term
        
        submitted = st.form_submit_button("Apply Filters", use_container_width=True)
        
        if submitted:
            return filters
    
    return None

def create_bulk_action_form(actions: List[str], 
                          form_key: str = "bulk_action_form") -> Optional[Dict[str, Any]]:
    """Create a bulk action form"""
    
    with st.form(form_key):
        st.subheader("⚡ Bulk Actions")
        
        action = st.selectbox(
            "Select Action",
            options=actions,
            help="Choose action to apply to selected items"
        )
        
        # Action-specific parameters
        parameters = {}
        
        if "update" in action.lower():
            st.write("**Update Parameters:**")
            col1, col2 = st.columns(2)
            
            with col1:
                field_to_update = st.selectbox(
                    "Field to Update",
                    options=["category", "reorder_point", "reorder_quantity", "supplier"]
                )
            
            with col2:
                new_value = st.text_input("New Value")
            
            parameters = {"field": field_to_update, "value": new_value}
        
        elif "delete" in action.lower():
            confirm_delete = st.checkbox(
                "I confirm I want to delete the selected items",
                help="This action cannot be undone"
            )
            parameters = {"confirmed": confirm_delete}
        
        elif "export" in action.lower():
            export_format = st.selectbox(
                "Export Format",
                options=["CSV", "Excel", "JSON"]
            )
            parameters = {"format": export_format}
        
        submitted = st.form_submit_button(
            f"Execute {action}",
            use_container_width=True,
            type="primary" if "delete" not in action.lower() else "secondary"
        )
        
        if submitted:
            if "delete" in action.lower() and not parameters.get("confirmed"):
                st.error("Please confirm the deletion action")
                return None
            
            return {
                "action": action,
                "parameters": parameters
            }
    
    return None
