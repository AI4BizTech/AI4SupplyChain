"""
Main LangChain agent for inventory management
"""

from typing import List, Dict, Any, Optional
import logging
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from src.agent.llm_client import LLMClient
from src.agent.tools import InventoryTools
from src.config import (
    OPENAI_API_KEY, 
    ANTHROPIC_API_KEY, 
    PRIMARY_LLM_PROVIDER,
    LLM_TEMPERATURE
)

logger = logging.getLogger(__name__)

class InventoryAgent:
    """Main conversational AI agent for inventory management"""
    
    def __init__(self):
        self.llm_client = LLMClient()
        self.tools_provider = InventoryTools()
        self.tools = self.tools_provider.get_tools()
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            return_messages=True,
            k=10  # Keep last 10 exchanges
        )
        
        # Initialize the agent
        self.agent_executor = self._create_agent()
    
    def _create_agent(self) -> Optional[AgentExecutor]:
        """Create the LangChain agent with tools"""
        try:
            # Create LLM instance for LangChain
            if PRIMARY_LLM_PROVIDER == "openai" and OPENAI_API_KEY:
                llm = ChatOpenAI(
                    model="gpt-4o-mini",
                    temperature=LLM_TEMPERATURE,
                    openai_api_key=OPENAI_API_KEY
                )
            elif PRIMARY_LLM_PROVIDER == "anthropic" and ANTHROPIC_API_KEY:
                llm = ChatAnthropic(
                    model="claude-3-5-haiku-20241022",
                    temperature=LLM_TEMPERATURE,
                    anthropic_api_key=ANTHROPIC_API_KEY
                )
            else:
                logger.error("No valid LLM provider configured for agent")
                return None
            
            # Create system prompt
            system_prompt = """You are an AI assistant specializing in inventory management and supply chain operations. 
You have access to a comprehensive inventory management system with the following capabilities:

🔧 **Available Tools**:
- inventory_query: Check current stock levels for any product
- demand_forecast: Generate demand predictions for planning
- inventory_optimization: Calculate optimal order quantities and reorder points
- supplier_query: Get supplier information and performance metrics
- low_stock_alerts: Identify products that need reordering
- transaction_history: Review recent inventory movements
- inventory_summary: Get overall system statistics
- reorder_recommendations: Get intelligent purchase recommendations

📋 **Your Role**:
- Help users understand their inventory status and make data-driven decisions
- Provide clear, actionable recommendations for inventory management
- Explain complex concepts in simple terms
- Always use the available tools to get real-time data rather than making assumptions
- Format responses with emojis and clear structure for better readability

💡 **Best Practices**:
- When users ask about stock levels, always use inventory_query first
- For planning questions, combine forecasting with optimization tools
- Provide context and explanations with your recommendations
- If data is insufficient, explain what additional information would help
- Always include actionable next steps in your responses

🎯 **Communication Style**:
- Be professional but friendly and approachable
- Use bullet points and clear formatting for complex information
- Include relevant emojis to make responses more engaging
- Provide specific numbers and metrics when available
- Always explain the reasoning behind recommendations

Remember: You're helping businesses optimize their inventory operations, which directly impacts their cash flow and customer satisfaction. Provide accurate, helpful, and actionable insights."""

            # Create prompt template
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad")
            ])
            
            # Create agent
            agent = create_openai_functions_agent(
                llm=llm,
                tools=self.tools,
                prompt=prompt
            )
            
            # Create agent executor
            agent_executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                memory=self.memory,
                verbose=False,  # Set to True for debugging
                handle_parsing_errors=True,
                max_iterations=3,
                early_stopping_method="generate"
            )
            
            logger.info("Inventory agent created successfully")
            return agent_executor
            
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            return None
    
    def chat(self, message: str, user_id: Optional[str] = None) -> str:
        """Process a chat message and return response"""
        try:
            if not self.agent_executor:
                # Fallback to direct LLM if agent creation failed
                return self._fallback_chat(message)
            
            # Process message through agent
            response = self.agent_executor.invoke({
                "input": message,
                "chat_history": self.memory.chat_memory.messages
            })
            
            return response.get("output", "I apologize, but I couldn't process your request properly. Please try again.")
            
        except Exception as e:
            logger.error(f"Chat processing error: {e}")
            return f"I encountered an error while processing your request: {str(e)}. Please try rephrasing your question."
    
    def _fallback_chat(self, message: str) -> str:
        """Fallback chat using direct LLM without agent tools"""
        try:
            system_message = """You are an AI assistant for inventory management. 
You don't currently have access to real-time data, but you can provide general guidance about inventory management concepts, best practices, and help users understand what information they might need to gather."""
            
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": message}
            ]
            
            response = self.llm_client.chat(messages)
            
            # Add a note about limited functionality
            response += "\n\n*Note: I'm currently running in limited mode without access to your inventory data. For real-time inventory information, please ensure the system is properly configured.*"
            
            return response
            
        except Exception as e:
            logger.error(f"Fallback chat error: {e}")
            return "I'm having trouble processing your request right now. Please check the system configuration and try again."
    
    def clear_memory(self):
        """Clear conversation memory"""
        self.memory.clear()
        logger.info("Agent memory cleared")
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get formatted conversation history"""
        try:
            history = []
            for message in self.memory.chat_memory.messages:
                if isinstance(message, HumanMessage):
                    history.append({"role": "user", "content": message.content})
                elif isinstance(message, AIMessage):
                    history.append({"role": "assistant", "content": message.content})
            return history
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []
    
    def is_available(self) -> bool:
        """Check if agent is available and properly configured"""
        return self.agent_executor is not None and self.llm_client.is_available()
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get information about agent capabilities"""
        return {
            "agent_available": self.agent_executor is not None,
            "llm_available": self.llm_client.is_available(),
            "llm_providers": self.llm_client.get_available_providers(),
            "primary_provider": PRIMARY_LLM_PROVIDER,
            "tools_count": len(self.tools),
            "tools": [tool.name for tool in self.tools],
            "memory_size": len(self.memory.chat_memory.messages) if self.memory else 0
        }
