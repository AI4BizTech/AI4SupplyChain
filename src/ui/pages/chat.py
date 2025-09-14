"""
Chat interface page
"""

import streamlit as st
import time
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def render_chat_page():
    """Render the AI chat interface page"""
    st.title("💬 AI Inventory Assistant")
    
    st.markdown("""
    Welcome to your AI-powered inventory assistant! I can help you with:
    
    • 📦 **Inventory Queries**: Check stock levels, find products, analyze inventory
    • 📈 **Demand Forecasting**: Generate forecasts, analyze trends, predict demand
    • ⚙️ **Optimization**: Calculate EOQ, reorder points, safety stock levels
    • 📊 **Reports & Analytics**: Create reports, analyze performance, identify trends
    • 🏢 **Supplier Management**: Find suppliers, analyze performance, manage relationships
    • 📄 **Transaction Processing**: Help with inventory movements and adjustments
    
    Just ask me anything about your inventory management needs!
    """)
    
    try:
        # Initialize the AI agent
        if 'agent' not in st.session_state:
            from src.agent.agent import InventoryAgent
            st.session_state.agent = InventoryAgent()
        
        # Check if agent is available
        if not st.session_state.agent.is_available():
            st.error("🚫 AI Agent Not Available")
            st.warning("The AI agent is not properly configured. Please check your API keys in the configuration.")
            
            with st.expander("🔧 Configuration Help"):
                st.write("""
                To use the AI assistant, you need to configure API keys:
                
                1. **OpenAI API Key** (Primary):
                   - Sign up at https://platform.openai.com/
                   - Generate an API key
                   - Set the OPENAI_API_KEY environment variable
                
                2. **Anthropic API Key** (Fallback):
                   - Sign up at https://console.anthropic.com/
                   - Generate an API key  
                   - Set the ANTHROPIC_API_KEY environment variable
                
                3. **Restart the application** after setting the keys
                """)
            return
        
        # Initialize chat history
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
            # Add welcome message
            welcome_message = {
                "role": "assistant",
                "content": """👋 Hello! I'm your AI inventory assistant. I'm here to help you manage your inventory more effectively.

**What I can help you with:**

🔍 **Quick Examples:**
- "What's my current stock for SKU-123?"
- "Show me products that need reordering"
- "Generate a 7-day forecast for laptops"
- "Calculate the optimal order quantity for Product ABC"
- "Which suppliers have the best performance?"
- "Create an inventory report for electronics"

**Advanced Capabilities:**
- Analyze inventory trends and patterns
- Recommend optimization strategies
- Help with supplier evaluation
- Assist with demand planning
- Generate custom reports and insights

What would you like to know about your inventory?""",
                "timestamp": datetime.now().isoformat()
            }
            st.session_state.chat_history.append(welcome_message)
        
        # Chat interface
        render_chat_interface()
        
        # Sidebar with features and examples
        render_chat_sidebar()
        
    except Exception as e:
        st.error(f"Error initializing chat interface: {e}")
        logger.error(f"Chat interface error: {e}")

def render_chat_interface():
    """Render the main chat interface"""
    
    # Display chat history
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                # Show timestamp for recent messages
                if "timestamp" in message:
                    timestamp = datetime.fromisoformat(message["timestamp"])
                    if (datetime.now() - timestamp).seconds < 300:  # Last 5 minutes
                        st.caption(f"_{timestamp.strftime('%H:%M:%S')}_")
    
    # Chat input
    if prompt := st.chat_input("Ask about your inventory..."):
        # Add user message to history
        user_message = {
            "role": "user", 
            "content": prompt,
            "timestamp": datetime.now().isoformat()
        }
        st.session_state.chat_history.append(user_message)
        
        # Display user message immediately
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Get response from agent
                    response = st.session_state.agent.chat(prompt)
                    
                    # Display response with typing effect (simplified)
                    message_placeholder = st.empty()
                    full_response = ""
                    
                    # Simulate typing effect
                    for chunk in response.split():
                        full_response += chunk + " "
                        message_placeholder.markdown(full_response + "▌")
                        time.sleep(0.02)  # Small delay for typing effect
                    
                    message_placeholder.markdown(full_response)
                    
                    # Add assistant response to history
                    assistant_message = {
                        "role": "assistant",
                        "content": full_response.strip(),
                        "timestamp": datetime.now().isoformat()
                    }
                    st.session_state.chat_history.append(assistant_message)
                    
                except Exception as e:
                    error_message = f"I apologize, but I encountered an error: {str(e)}"
                    st.error(error_message)
                    
                    # Add error to history
                    error_response = {
                        "role": "assistant",
                        "content": error_message,
                        "timestamp": datetime.now().isoformat()
                    }
                    st.session_state.chat_history.append(error_response)

def render_chat_sidebar():
    """Render the chat sidebar with examples and features"""
    
    with st.sidebar:
        st.header("💡 Quick Examples")
        
        # Example categories
        example_categories = {
            "📦 Inventory Queries": [
                "What's my current stock for SKU-123?",
                "Show me all products with low stock",
                "Which items are out of stock?",
                "What's the total value of my inventory?"
            ],
            "📈 Forecasting": [
                "Generate a 7-day forecast for Product ABC",
                "Show me demand trends for electronics",
                "What's the forecast accuracy for my top products?",
                "Analyze seasonal patterns for winter items"
            ],
            "⚙️ Optimization": [
                "Calculate EOQ for Product XYZ",
                "What should be the reorder point for SKU-456?",
                "Show me optimization opportunities",
                "Which products need safety stock adjustment?"
            ],
            "🏢 Suppliers": [
                "Which suppliers have the best performance?",
                "Show me lead times for all suppliers",
                "Find suppliers for electronics category",
                "Analyze supplier delivery performance"
            ],
            "📊 Analytics": [
                "Create an inventory turnover report",
                "Show me ABC analysis results",
                "What are my fastest-moving products?",
                "Generate a monthly inventory summary"
            ]
        }
        
        # Display examples by category
        for category, examples in example_categories.items():
            with st.expander(category):
                for example in examples:
                    if st.button(example, key=f"example_{hash(example)}", use_container_width=True):
                        # Add example to chat
                        st.session_state.chat_history.append({
                            "role": "user",
                            "content": example,
                            "timestamp": datetime.now().isoformat()
                        })
                        st.rerun()
        
        st.markdown("---")
        
        # Chat management
        st.header("🔧 Chat Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()
        
        with col2:
            if st.button("📥 Export Chat", use_container_width=True):
                export_chat_history()
        
        # Chat statistics
        if st.session_state.chat_history:
            st.markdown("---")
            st.header("📊 Chat Stats")
            
            total_messages = len(st.session_state.chat_history)
            user_messages = len([m for m in st.session_state.chat_history if m["role"] == "user"])
            assistant_messages = len([m for m in st.session_state.chat_history if m["role"] == "assistant"])
            
            st.metric("Total Messages", total_messages)
            st.metric("Your Messages", user_messages)
            st.metric("Assistant Messages", assistant_messages)
            
            # Session duration
            if len(st.session_state.chat_history) > 1:
                first_msg = st.session_state.chat_history[0]
                last_msg = st.session_state.chat_history[-1]
                
                if "timestamp" in first_msg and "timestamp" in last_msg:
                    start_time = datetime.fromisoformat(first_msg["timestamp"])
                    end_time = datetime.fromisoformat(last_msg["timestamp"])
                    duration = end_time - start_time
                    
                    if duration.seconds > 0:
                        st.metric("Session Duration", f"{duration.seconds // 60}m {duration.seconds % 60}s")
        
        # Agent capabilities
        st.markdown("---")
        st.header("🤖 Agent Capabilities")
        
        try:
            capabilities = st.session_state.agent.get_capabilities()
            
            if capabilities.get("tools"):
                st.write("**Available Tools:**")
                for tool in capabilities["tools"]:
                    st.write(f"• {tool}")
            
            if capabilities.get("models"):
                st.write("**AI Models:**")
                for model in capabilities["models"]:
                    st.write(f"• {model}")
                    
        except Exception as e:
            st.write("Agent capabilities not available")
        
        # Help section
        st.markdown("---")
        st.header("❓ Need Help?")
        
        with st.expander("How to use the AI Assistant"):
            st.markdown("""
            **Tips for better results:**
            
            1. **Be specific**: Instead of "check inventory", try "show current stock levels for electronics category"
            
            2. **Use product identifiers**: Reference products by SKU, name, or category
            
            3. **Ask follow-up questions**: Build on previous responses for deeper insights
            
            4. **Request specific formats**: Ask for tables, charts, or summaries as needed
            
            5. **Combine requests**: "Show low stock items and calculate reorder quantities"
            
            **Sample conversation flow:**
            1. "What products are running low on stock?"
            2. "Calculate optimal reorder quantities for those items"
            3. "Which suppliers should I contact for reordering?"
            4. "Generate purchase orders for the recommended quantities"
            """)
        
        with st.expander("Troubleshooting"):
            st.markdown("""
            **Common issues:**
            
            • **Agent not responding**: Check API key configuration
            • **Slow responses**: Large queries may take time to process
            • **Incomplete data**: Some features require historical transaction data
            • **Connection errors**: Verify internet connection and API status
            
            **Getting better results:**
            
            • Ensure your inventory data is up to date
            • Use exact SKU numbers when possible
            • Be patient with complex analytical queries
            • Try rephrasing questions if results aren't helpful
            """)

def export_chat_history():
    """Export chat history to a downloadable format"""
    try:
        if not st.session_state.chat_history:
            st.warning("No chat history to export")
            return
        
        # Prepare chat export
        chat_export = []
        for message in st.session_state.chat_history:
            timestamp = message.get("timestamp", datetime.now().isoformat())
            chat_export.append(f"[{timestamp}] {message['role'].upper()}: {message['content']}\n\n")
        
        export_content = "".join(chat_export)
        
        # Create download
        st.download_button(
            label="💾 Download Chat History",
            data=export_content,
            file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )
        
    except Exception as e:
        st.error(f"Error exporting chat history: {e}")

if __name__ == "__main__":
    render_chat_page()
