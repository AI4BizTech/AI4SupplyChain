"""
Conversation memory management for the AI agent
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from langchain.memory import ConversationBufferWindowMemory, ConversationSummaryBufferMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage

from src.data.database import get_database

logger = logging.getLogger(__name__)

class ConversationMemory:
    """Enhanced conversation memory with persistence and context management"""
    
    def __init__(self, user_id: str = "default", max_messages: int = 20):
        self.user_id = user_id
        self.max_messages = max_messages
        self.db = get_database()
        
        # In-memory storage for current session
        self.messages: List[BaseMessage] = []
        self.context: Dict[str, Any] = {}
        
        # Load previous conversation if exists
        self._load_conversation()
    
    def add_message(self, message: BaseMessage):
        """Add a new message to memory"""
        self.messages.append(message)
        
        # Keep only the last max_messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
        
        # Save to persistent storage
        self._save_message(message)
    
    def add_user_message(self, content: str):
        """Add a user message"""
        message = HumanMessage(content=content)
        self.add_message(message)
        return message
    
    def add_ai_message(self, content: str):
        """Add an AI response message"""
        message = AIMessage(content=content)
        self.add_message(message)
        return message
    
    def add_system_message(self, content: str):
        """Add a system message"""
        message = SystemMessage(content=content)
        self.add_message(message)
        return message
    
    def get_messages(self, limit: Optional[int] = None) -> List[BaseMessage]:
        """Get recent messages"""
        if limit:
            return self.messages[-limit:]
        return self.messages
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get conversation history in a simple format"""
        history = []
        for message in self.messages:
            if isinstance(message, HumanMessage):
                history.append({"role": "user", "content": message.content})
            elif isinstance(message, AIMessage):
                history.append({"role": "assistant", "content": message.content})
            elif isinstance(message, SystemMessage):
                history.append({"role": "system", "content": message.content})
        return history
    
    def set_context(self, key: str, value: Any):
        """Set context information"""
        self.context[key] = value
        self._save_context()
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """Get context information"""
        return self.context.get(key, default)
    
    def update_context(self, updates: Dict[str, Any]):
        """Update multiple context values"""
        self.context.update(updates)
        self._save_context()
    
    def clear_context(self):
        """Clear all context"""
        self.context.clear()
        self._save_context()
    
    def clear_messages(self):
        """Clear all messages"""
        self.messages.clear()
        self._clear_persistent_messages()
    
    def clear_all(self):
        """Clear both messages and context"""
        self.clear_messages()
        self.clear_context()
    
    def get_summary(self) -> str:
        """Get a summary of the conversation"""
        if not self.messages:
            return "No conversation history"
        
        message_count = len(self.messages)
        user_messages = len([m for m in self.messages if isinstance(m, HumanMessage)])
        ai_messages = len([m for m in self.messages if isinstance(m, AIMessage)])
        
        # Get recent topics from last few messages
        recent_content = []
        for message in self.messages[-5:]:
            if isinstance(message, (HumanMessage, AIMessage)):
                # Extract key topics (simplified)
                content = message.content.lower()
                if any(keyword in content for keyword in ['inventory', 'stock', 'product']):
                    recent_content.append("inventory management")
                elif any(keyword in content for keyword in ['forecast', 'predict', 'demand']):
                    recent_content.append("demand forecasting")
                elif any(keyword in content for keyword in ['supplier', 'vendor']):
                    recent_content.append("supplier management")
                elif any(keyword in content for keyword in ['eoq', 'reorder', 'optimization']):
                    recent_content.append("inventory optimization")
        
        topics = list(set(recent_content))
        
        summary = f"Conversation with {message_count} messages ({user_messages} user, {ai_messages} assistant)"
        if topics:
            summary += f". Recent topics: {', '.join(topics)}"
        
        return summary
    
    def _load_conversation(self):
        """Load conversation from persistent storage"""
        try:
            # In a real implementation, this would load from database
            # For now, we'll keep it in memory only
            logger.debug(f"Loading conversation for user {self.user_id}")
        except Exception as e:
            logger.error(f"Error loading conversation: {e}")
    
    def _save_message(self, message: BaseMessage):
        """Save a single message to persistent storage"""
        try:
            # In a real implementation, this would save to database
            # For now, we'll keep it in memory only
            logger.debug(f"Saving message for user {self.user_id}")
        except Exception as e:
            logger.error(f"Error saving message: {e}")
    
    def _save_context(self):
        """Save context to persistent storage"""
        try:
            # In a real implementation, this would save to database
            logger.debug(f"Saving context for user {self.user_id}")
        except Exception as e:
            logger.error(f"Error saving context: {e}")
    
    def _clear_persistent_messages(self):
        """Clear messages from persistent storage"""
        try:
            # In a real implementation, this would clear from database
            logger.debug(f"Clearing messages for user {self.user_id}")
        except Exception as e:
            logger.error(f"Error clearing messages: {e}")

class SessionMemory:
    """Session-based memory for temporary context"""
    
    def __init__(self):
        self.sessions: Dict[str, ConversationMemory] = {}
    
    def get_memory(self, session_id: str) -> ConversationMemory:
        """Get or create memory for a session"""
        if session_id not in self.sessions:
            self.sessions[session_id] = ConversationMemory(user_id=session_id)
        return self.sessions[session_id]
    
    def clear_session(self, session_id: str):
        """Clear a specific session"""
        if session_id in self.sessions:
            self.sessions[session_id].clear_all()
            del self.sessions[session_id]
    
    def clear_old_sessions(self, max_age_hours: int = 24):
        """Clear sessions older than specified hours"""
        # In a real implementation, this would check timestamps
        # For now, we'll keep all sessions
        pass
    
    def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs"""
        return list(self.sessions.keys())

# Global session memory instance
_session_memory = SessionMemory()

def get_session_memory() -> SessionMemory:
    """Get the global session memory instance"""
    return _session_memory

def get_conversation_memory(session_id: str = "default") -> ConversationMemory:
    """Get conversation memory for a specific session"""
    return _session_memory.get_memory(session_id)
