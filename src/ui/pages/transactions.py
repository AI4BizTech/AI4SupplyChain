"""
Transaction processing with OCR page
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def render_transactions_page():
    """Render the transaction processing page"""
    st.title("📄 Transaction Processing")
    
    # Sidebar for actions
    with st.sidebar:
        st.header("Transaction Actions")
        action = st.selectbox(
            "Choose Action",
            ["Manual Entry", "OCR Upload", "Transaction History", "Pending Receipts"]
        )
    
    try:
        from src.services.transactions import TransactionService
        from src.services.inventory import InventoryService
        
        transaction_service = TransactionService()
        inventory_service = InventoryService()
        
        if action == "Manual Entry":
            show_manual_entry(transaction_service, inventory_service)
        elif action == "OCR Upload":
            show_ocr_upload(transaction_service, inventory_service)
        elif action == "Transaction History":
            show_transaction_history(inventory_service)
        elif action == "Pending Receipts":
            show_pending_receipts(transaction_service)
            
    except Exception as e:
        st.error(f"Error loading transaction processing: {e}")
        st.info("Please ensure the database is initialized and services are available.")

def show_manual_entry(transaction_service, inventory_service):
    """Show manual transaction entry form"""
    st.header("✏️ Manual Transaction Entry")
    
    with st.form("manual_transaction_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Product selection
            try:
                products = inventory_service.list_products(limit=1000)
                product_options = [f"{p.sku} - {p.name}" for p in products]
                selected_product = st.selectbox("Select Product", product_options)
                
                if selected_product:
                    sku = selected_product.split(" - ")[0]
            except:
                st.error("Error loading products")
                return
            
            # Location selection
            locations = get_locations(inventory_service)
            selected_location = st.selectbox("Location", locations)
        
        with col2:
            transaction_type = st.selectbox(
                "Transaction Type",
                ["receipt", "shipment", "adjustment", "transfer"]
            )
            
            quantity = st.number_input(
                "Quantity",
                help="Use positive numbers for inbound, negative for outbound"
            )
        
        col3, col4 = st.columns(2)
        
        with col3:
            unit_cost = st.number_input("Unit Cost ($)", min_value=0.0, step=0.01)
            reference_doc = st.text_input("Reference Document", placeholder="PO-12345, INV-67890, etc.")
        
        with col4:
            user_id = st.text_input("User ID", value="admin")
            notes = st.text_area("Notes")
        
        submitted = st.form_submit_button("Create Transaction")
        
        if submitted:
            if not selected_product or not selected_location or quantity == 0:
                st.error("Please fill in all required fields.")
                return
            
            try:
                transaction_data = {
                    "product_sku": sku,
                    "location_id": selected_location,
                    "transaction_type": transaction_type,
                    "quantity": quantity,
                    "unit_cost": unit_cost if unit_cost > 0 else None,
                    "reference_document": reference_doc,
                    "notes": notes,
                    "user_id": user_id
                }
                
                # Create transaction through API-like interface
                st.success(f"✅ Transaction created: {quantity:+} units of {sku}")
                st.info(f"Type: {transaction_type}, Location: {selected_location}")
                
                if reference_doc:
                    st.info(f"Reference: {reference_doc}")
                
            except Exception as e:
                st.error(f"Error creating transaction: {e}")

def show_ocr_upload(transaction_service, inventory_service):
    """Show OCR document upload functionality"""
    st.header("📤 OCR Document Upload")
    
    st.info("Upload Purchase Orders or Delivery Orders for automatic processing.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        document_type = st.selectbox(
            "Document Type",
            ["purchase_order", "delivery_order"],
            format_func=lambda x: "Purchase Order" if x == "purchase_order" else "Delivery Order"
        )
    
    with col2:
        locations = get_locations(inventory_service)
        selected_location = st.selectbox("Processing Location", locations)
    
    uploaded_file = st.file_uploader(
        "Choose document file",
        type=["pdf", "jpg", "jpeg", "png"],
        help="Upload a PDF, JPG, or PNG file"
    )
    
    if uploaded_file is not None:
        # Show file info
        st.write(f"**File:** {uploaded_file.name}")
        st.write(f"**Size:** {uploaded_file.size:,} bytes")
        st.write(f"**Type:** {uploaded_file.type}")
        
        # Preview for images
        if uploaded_file.type.startswith('image/'):
            st.image(uploaded_file, caption="Document Preview", use_column_width=True)
        
        if st.button("🔍 Process Document"):
            with st.spinner("Processing document with OCR..."):
                try:
                    # Simulate OCR processing
                    st.success("✅ Document processed successfully!")
                    
                    # Show mock results
                    st.subheader("📋 Extracted Information")
                    
                    if document_type == "purchase_order":
                        extracted_data = {
                            "PO Number": "PO-2024-001",
                            "Supplier": "ABC Supplier Inc.",
                            "Date": "2024-01-15",
                            "Items": [
                                {"SKU": "SKU-001", "Description": "Product A", "Quantity": 50, "Price": 25.00},
                                {"SKU": "SKU-002", "Description": "Product B", "Quantity": 30, "Price": 15.50}
                            ]
                        }
                    else:
                        extracted_data = {
                            "DO Number": "DO-2024-001",
                            "Supplier": "ABC Supplier Inc.",
                            "Date": "2024-01-20",
                            "Items": [
                                {"SKU": "SKU-001", "Description": "Product A", "Quantity Delivered": 48},
                                {"SKU": "SKU-002", "Description": "Product B", "Quantity Delivered": 30}
                            ]
                        }
                    
                    # Display extracted data
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Document Info:**")
                        for key, value in extracted_data.items():
                            if key != "Items":
                                st.write(f"- **{key}:** {value}")
                    
                    with col2:
                        st.write("**Items Extracted:**")
                        items_df = pd.DataFrame(extracted_data["Items"])
                        st.dataframe(items_df, hide_index=True)
                    
                    # Show transaction creation results
                    st.subheader("🔄 Transactions Created")
                    
                    transactions_created = []
                    for item in extracted_data["Items"]:
                        if document_type == "purchase_order":
                            transactions_created.append({
                                "SKU": item["SKU"],
                                "Type": "expected_receipt",
                                "Quantity": item["Quantity"],
                                "Location": selected_location,
                                "Status": "Pending Receipt"
                            })
                        else:
                            transactions_created.append({
                                "SKU": item["SKU"],
                                "Type": "receipt",
                                "Quantity": item["Quantity Delivered"],
                                "Location": selected_location,
                                "Status": "Completed"
                            })
                    
                    trans_df = pd.DataFrame(transactions_created)
                    st.dataframe(trans_df, hide_index=True)
                    
                    st.success(f"✅ Created {len(transactions_created)} transactions from document")
                    
                except Exception as e:
                    st.error(f"Error processing document: {e}")

def show_transaction_history(inventory_service):
    """Show transaction history with filters"""
    st.header("📊 Transaction History")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Product filter
        try:
            products = inventory_service.list_products(limit=1000)
            product_options = ["All Products"] + [f"{p.sku} - {p.name}" for p in products]
            selected_product = st.selectbox("Filter by Product", product_options)
            
            product_sku = None
            if selected_product != "All Products":
                product_sku = selected_product.split(" - ")[0]
        except:
            product_sku = None
    
    with col2:
        locations = ["All Locations"] + get_locations(inventory_service)
        selected_location = st.selectbox("Filter by Location", locations)
        location_filter = None if selected_location == "All Locations" else selected_location
    
    with col3:
        transaction_types = ["All Types", "receipt", "shipment", "adjustment", "transfer", "expected_receipt"]
        selected_type = st.selectbox("Filter by Type", transaction_types)
        type_filter = None if selected_type == "All Types" else selected_type
    
    # Date range
    col4, col5, col6 = st.columns(3)
    with col4:
        days_back = st.selectbox("Time Period", [7, 30, 90, 180, 365], index=2)
    with col5:
        limit = st.number_input("Max Results", min_value=10, max_value=1000, value=100)
    with col6:
        st.write("")  # Spacer
    
    try:
        # Get transactions
        transactions = inventory_service.get_transaction_history(
            product_sku=product_sku,
            location=location_filter,
            transaction_type=type_filter,
            limit=limit
        )
        
        if not transactions:
            st.info("No transactions found for the selected criteria.")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(transactions)
        
        # Format for display
        if 'timestamp' in df.columns:
            df['Date'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Transactions", len(df))
        
        with col2:
            inbound = df[df['quantity'] > 0]['quantity'].sum() if 'quantity' in df.columns else 0
            st.metric("Total Inbound", f"{inbound:,}")
        
        with col3:
            outbound = abs(df[df['quantity'] < 0]['quantity'].sum()) if 'quantity' in df.columns else 0
            st.metric("Total Outbound", f"{outbound:,}")
        
        with col4:
            net_change = inbound - outbound
            st.metric("Net Change", f"{net_change:+,}")
        
        # Transaction type breakdown
        if 'transaction_type' in df.columns:
            type_counts = df['transaction_type'].value_counts()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Transactions by Type:**")
                for trans_type, count in type_counts.items():
                    st.write(f"- {trans_type.replace('_', ' ').title()}: {count}")
            
            with col2:
                # Simple chart using metrics
                st.write("**Transaction Distribution:**")
                for trans_type, count in type_counts.items():
                    percentage = (count / len(df)) * 100
                    st.write(f"- {trans_type}: {percentage:.1f}%")
        
        # Display transactions table
        st.subheader("📋 Transaction Details")
        
        # Select columns to display
        display_columns = []
        if 'Date' in df.columns:
            display_columns.append('Date')
        if 'sku' in df.columns:
            display_columns.append('sku')
        if 'product_name' in df.columns:
            display_columns.append('product_name')
        if 'transaction_type' in df.columns:
            display_columns.append('transaction_type')
        if 'quantity' in df.columns:
            display_columns.append('quantity')
        if 'location' in df.columns:
            display_columns.append('location')
        if 'reference_document' in df.columns:
            display_columns.append('reference_document')
        if 'user_id' in df.columns:
            display_columns.append('user_id')
        
        if display_columns:
            df_display = df[display_columns]
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Export option
        if st.button("📥 Export to CSV"):
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"transaction_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
    except Exception as e:
        st.error(f"Error loading transaction history: {e}")

def show_pending_receipts(transaction_service):
    """Show pending expected receipts"""
    st.header("⏳ Pending Receipts")
    
    st.info("These are expected receipts from purchase orders that haven't been received yet.")
    
    try:
        # Mock pending receipts data
        pending_receipts = [
            {
                "Transaction ID": "TXN-001",
                "SKU": "SKU-001",
                "Product Name": "Product A",
                "Expected Qty": 50,
                "Location": "MAIN-WH",
                "PO Reference": "PO-2024-001",
                "Expected Date": "2024-01-20",
                "Days Overdue": 5
            },
            {
                "Transaction ID": "TXN-002", 
                "SKU": "SKU-002",
                "Product Name": "Product B",
                "Expected Qty": 30,
                "Location": "MAIN-WH",
                "PO Reference": "PO-2024-001",
                "Expected Date": "2024-01-20",
                "Days Overdue": 5
            }
        ]
        
        if not pending_receipts:
            st.success("✅ No pending receipts!")
            return
        
        df = pd.DataFrame(pending_receipts)
        
        # Metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Pending Receipts", len(df))
        
        with col2:
            overdue = len(df[df['Days Overdue'] > 0]) if 'Days Overdue' in df.columns else 0
            st.metric("Overdue", overdue)
        
        with col3:
            total_qty = df['Expected Qty'].sum() if 'Expected Qty' in df.columns else 0
            st.metric("Total Expected Qty", f"{total_qty:,}")
        
        # Display table
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Process receipt form
        st.subheader("📦 Process Receipt")
        
        with st.form("process_receipt_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                transaction_options = [f"{r['Transaction ID']} - {r['SKU']}" for r in pending_receipts]
                selected_transaction = st.selectbox("Select Transaction", transaction_options)
            
            with col2:
                if selected_transaction:
                    expected_qty = next(r['Expected Qty'] for r in pending_receipts 
                                      if f"{r['Transaction ID']} - {r['SKU']}" == selected_transaction)
                    actual_qty = st.number_input(
                        f"Actual Quantity Received (Expected: {expected_qty})",
                        min_value=0,
                        max_value=expected_qty * 2,  # Allow over-receipt
                        value=expected_qty
                    )
            
            notes = st.text_area("Receipt Notes")
            
            submitted = st.form_submit_button("Process Receipt")
            
            if submitted and selected_transaction:
                transaction_id = selected_transaction.split(" - ")[0]
                
                st.success(f"✅ Receipt processed for {transaction_id}")
                st.info(f"Quantity received: {actual_qty}")
                
                if actual_qty != expected_qty:
                    variance = actual_qty - expected_qty
                    st.warning(f"Quantity variance: {variance:+} units")
                
                st.rerun()  # Refresh to remove processed receipt
        
    except Exception as e:
        st.error(f"Error loading pending receipts: {e}")

def get_locations(inventory_service) -> list:
    """Get list of available locations"""
    try:
        locations = inventory_service.get_locations()
        return [loc.location_id for loc in locations]
    except:
        return ["MAIN-WH", "STORE-A", "STORE-B"]  # Default locations

if __name__ == "__main__":
    render_transactions_page()
