"""
Main Streamlit dashboard entry point
"""

import streamlit as st
import logging
from datetime import datetime
import pandas as pd

# Page imports
from src.ui.pages.products import render_products_page
from src.ui.pages.inventory import render_inventory_page
from src.ui.pages.suppliers import render_suppliers_page
from src.ui.pages.transactions import render_transactions_page
from src.ui.pages.forecasting import render_forecasting_page
from src.ui.pages.optimization import render_optimization_page
from src.ui.pages.chat import render_chat_page

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="AI4SupplyChain Dashboard",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Main Streamlit application"""
    
    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #1f77b4;
    }
    .sidebar-info {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .nav-button {
        width: 100%;
        margin: 0.25rem 0;
        text-align: left;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Main header
    st.markdown("""
    <div class="main-header">
        <h1>🚀 AI4SupplyChain Dashboard</h1>
        <p>Intelligent Inventory Management & Demand Planning</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("### 📋 Navigation")
        
        # System status
        st.markdown('<div class="sidebar-info">', unsafe_allow_html=True)
        st.write("**🎯 System Status**")
        st.success("✅ Online")
        st.info(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Main navigation
        page_options = {
            "🏠 Dashboard": "dashboard",
            "📦 Products": "products", 
            "📊 Inventory": "inventory",
            "🏢 Suppliers": "suppliers",
            "📄 Transactions": "transactions",
            "📈 Forecasting": "forecasting",
            "⚙️ Optimization": "optimization",
            "💬 AI Assistant": "chat"
        }
        
        # Use session state to track current page
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'dashboard'
        
        # Navigation buttons
        for page_name, page_key in page_options.items():
            if st.button(page_name, key=f"nav_{page_key}", use_container_width=True):
                st.session_state.current_page = page_key
                st.rerun()
        
        # Quick stats
        st.markdown("---")
        st.markdown("### 📊 Quick Stats")
        try:
            # Mock quick stats - in real app, these would come from services
            st.metric("Products", "1,234", "12 new")
            st.metric("Low Stock", "23", "-5")
            st.metric("Orders", "156", "+8")
        except Exception as e:
            st.warning("Stats unavailable")
    
    # Main content area based on selected page
    current_page = st.session_state.current_page
    
    try:
        if current_page == "dashboard":
            show_dashboard_overview()
        elif current_page == "products":
            render_products_page()
        elif current_page == "inventory":
            render_inventory_page()
        elif current_page == "suppliers":
            render_suppliers_page()
        elif current_page == "transactions":
            render_transactions_page()
        elif current_page == "forecasting":
            render_forecasting_page()
        elif current_page == "optimization":
            render_optimization_page()
        elif current_page == "chat":
            render_chat_page()
        else:
            show_dashboard_overview()
    except Exception as e:
        st.error(f"Error loading page: {e}")
        logger.error(f"Page loading error: {e}")
        st.info("Please check the system configuration and try again.")

def show_dashboard_overview():
    """Display the main dashboard overview"""
    
    st.header("📊 Dashboard Overview")
    
    try:
        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric(
                label="📦 Total Products",
                value="1,234",
                delta="12 new this month"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric(
                label="💰 Inventory Value", 
                value="$2.4M",
                delta="5.2% vs last month"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric(
                label="⚠️ Low Stock Items",
                value="23",
                delta="-5 from yesterday",
                delta_color="inverse"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col4:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric(
                label="🔄 Avg Turnover",
                value="6.8x",
                delta="0.3x improvement"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Charts section
        st.subheader("📈 Analytics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Mock inventory trend chart
            st.subheader("📊 Inventory Trends")
            chart_data = pd.DataFrame({
                'Date': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                'Value': [2100000, 2200000, 2300000, 2250000, 2400000, 2380000]
            })
            st.line_chart(chart_data.set_index('Date'))
        
        with col2:
            # Mock category breakdown
            st.subheader("🏷️ Category Breakdown")
            category_data = pd.DataFrame({
                'Category': ['Electronics', 'Office Supplies', 'Industrial Tools', 'Automotive Parts', 'Other'],
                'Value': [35, 25, 20, 15, 5]
            })
            st.bar_chart(category_data.set_index('Category'))
        
        # Recent activity
        st.subheader("📋 Recent Activity")
        
        recent_activities = [
            "📦 Received 500 units of SKU-12345",
            "⚠️ Low stock alert for Product ABC",
            "📈 Forecast generated for Electronics category",
            "🏢 New supplier XYZ Corp added",
            "🔄 Inventory transfer completed: MAIN-WH → STORE-A"
        ]
        
        for activity in recent_activities:
            st.write(f"• {activity}")
        
        # Quick actions
        st.subheader("⚡ Quick Actions")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("➕ Add Product", use_container_width=True):
                st.session_state.current_page = 'products'
                st.rerun()
        
        with col2:
            if st.button("📈 Generate Forecast", use_container_width=True):
                st.session_state.current_page = 'forecasting'
                st.rerun()
        
        with col3:
            if st.button("🔍 Check Stock Alerts", use_container_width=True):
                st.session_state.current_page = 'inventory'
                st.rerun()
        
        with col4:
            if st.button("💬 Ask AI Assistant", use_container_width=True):
                st.session_state.current_page = 'chat'
                st.rerun()
        
        # System information
        with st.expander("🔧 System Information"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**System Status:**")
                st.success("✅ Database Connected")
                st.success("✅ Services Running")
                st.info("📊 Sample Data Mode")
            
            with col2:
                st.write("**Quick Setup:**")
                st.write("1. Configure API keys in environment")
                st.write("2. Initialize database with sample data")
                st.write("3. Start using the AI assistant")
                
                if st.button("🚀 Initialize Sample Data"):
                    with st.spinner("Initializing sample data..."):
                        try:
                            from src.services.simulation import SimulationService
                            sim = SimulationService()
                            result = sim.initialize_sample_database()
                            if result.get('success'):
                                st.success("✅ Sample data initialized!")
                            else:
                                st.error(f"❌ Error: {result.get('error')}")
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
    
    except Exception as e:
        st.error(f"Error loading dashboard: {e}")
        logger.error(f"Dashboard error: {e}")
        
        # Fallback minimal dashboard
        st.info("Loading minimal dashboard...")
        st.write("Welcome to AI4SupplyChain!")
        st.write("Use the sidebar to navigate to different sections.")
        
        # Show setup instructions
        st.subheader("🚀 Getting Started")
        st.markdown("""
        To get started with AI4SupplyChain:
        
        1. **Initialize Sample Data**:
        ```python
        from src.services.simulation import SimulationService
        sim = SimulationService()
        result = sim.initialize_sample_database()
        print(result)
        ```
        
        2. **Configure API Keys** in your `.env` file:
        - OPENAI_API_KEY or ANTHROPIC_API_KEY
        
        3. **Refresh this page** to see your data
        """)

if __name__ == "__main__":
    main()