"""
Chat/AI agent API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import logging
import json
import asyncio

from src.agent.agent import InventoryAgent
from src.agent.memory import get_conversation_memory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# Pydantic models for API
class ChatMessage(BaseModel):
    message: str = Field(..., description="User message")
    session_id: str = Field(default="default", description="Session ID for conversation continuity")
    user_id: str = Field(default="api", description="User ID")

class ChatResponse(BaseModel):
    response: str
    session_id: str
    message_id: Optional[str] = None
    timestamp: str

class ConversationHistory(BaseModel):
    session_id: str
    messages: List[Dict[str, str]]
    message_count: int

# Global agent instance (in production, you might want to use dependency injection)
_agent_instance: Optional[InventoryAgent] = None

def get_agent() -> InventoryAgent:
    """Get or create the global agent instance"""
    global _agent_instance
    if _agent_instance is None:
        try:
            _agent_instance = InventoryAgent()
            logger.info("Inventory agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize inventory agent: {e}")
            raise HTTPException(status_code=503, detail="AI agent is not available")
    
    return _agent_instance

@router.post("/message", response_model=ChatResponse)
async def send_message(
    chat_request: ChatMessage,
    agent: InventoryAgent = Depends(get_agent)
):
    """Send a message to the AI agent"""
    try:
        # Check if agent is available
        if not agent.is_available():
            raise HTTPException(
                status_code=503, 
                detail="AI agent is not available. Please check API key configuration."
            )
        
        # Get conversation memory for this session
        memory = get_conversation_memory(chat_request.session_id)
        
        # Add user message to memory
        memory.add_user_message(chat_request.message)
        
        # Get response from agent
        response = agent.chat(chat_request.message, chat_request.user_id)
        
        # Add AI response to memory
        memory.add_ai_message(response)
        
        from datetime import datetime
        return ChatResponse(
            response=response,
            session_id=chat_request.session_id,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@router.get("/history/{session_id}", response_model=ConversationHistory)
async def get_conversation_history(session_id: str):
    """Get conversation history for a session"""
    try:
        memory = get_conversation_memory(session_id)
        history = memory.get_conversation_history()
        
        return ConversationHistory(
            session_id=session_id,
            messages=history,
            message_count=len(history)
        )
        
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/history/{session_id}")
async def clear_conversation_history(session_id: str):
    """Clear conversation history for a session"""
    try:
        memory = get_conversation_memory(session_id)
        memory.clear_all()
        
        return {
            "success": True,
            "message": f"Conversation history cleared for session {session_id}",
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"Error clearing conversation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions")
async def get_active_sessions():
    """Get list of active chat sessions"""
    try:
        from src.agent.memory import get_session_memory
        session_memory = get_session_memory()
        active_sessions = session_memory.get_active_sessions()
        
        session_info = []
        for session_id in active_sessions:
            memory = get_conversation_memory(session_id)
            session_info.append({
                "session_id": session_id,
                "message_count": len(memory.get_messages()),
                "summary": memory.get_summary()
            })
        
        return {
            "active_sessions": len(active_sessions),
            "sessions": session_info
        }
        
    except Exception as e:
        logger.error(f"Error getting active sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agent/status")
async def get_agent_status():
    """Get AI agent status and capabilities"""
    try:
        agent = get_agent()
        capabilities = agent.get_capabilities()
        
        return {
            "status": "available" if agent.is_available() else "unavailable",
            "capabilities": capabilities
        }
        
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        return {
            "status": "unavailable",
            "error": str(e),
            "capabilities": {}
        }

@router.get("/agent/tools")
async def get_available_tools():
    """Get list of available AI tools"""
    try:
        agent = get_agent()
        capabilities = agent.get_capabilities()
        
        return {
            "tools": capabilities.get("tools", []),
            "tool_count": capabilities.get("tools_count", 0)
        }
        
    except Exception as e:
        logger.error(f"Error getting available tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.session_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.session_connections[session_id] = websocket

    def disconnect(self, websocket: WebSocket, session_id: str):
        self.active_connections.remove(websocket)
        if session_id in self.session_connections:
            del self.session_connections[session_id]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def send_to_session(self, message: str, session_id: str):
        if session_id in self.session_connections:
            websocket = self.session_connections[session_id]
            await websocket.send_text(message)

manager = ConnectionManager()

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat"""
    await manager.connect(websocket, session_id)
    
    try:
        # Send welcome message
        welcome_msg = {
            "type": "system",
            "message": f"Connected to AI4SupplyChain chat session: {session_id}",
            "session_id": session_id
        }
        await manager.send_personal_message(json.dumps(welcome_msg), websocket)
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                user_message = message_data.get("message", "")
                
                if not user_message.strip():
                    continue
                
                # Get agent and process message
                agent = get_agent()
                
                if not agent.is_available():
                    error_response = {
                        "type": "error",
                        "message": "AI agent is not available. Please check configuration.",
                        "session_id": session_id
                    }
                    await manager.send_personal_message(json.dumps(error_response), websocket)
                    continue
                
                # Get conversation memory
                memory = get_conversation_memory(session_id)
                
                # Add user message to memory
                memory.add_user_message(user_message)
                
                # Send typing indicator
                typing_msg = {
                    "type": "typing",
                    "message": "AI is thinking...",
                    "session_id": session_id
                }
                await manager.send_personal_message(json.dumps(typing_msg), websocket)
                
                # Get AI response
                response = agent.chat(user_message, session_id)
                
                # Add AI response to memory
                memory.add_ai_message(response)
                
                # Send response to client
                response_msg = {
                    "type": "response",
                    "message": response,
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
                await manager.send_personal_message(json.dumps(response_msg), websocket)
                
            except json.JSONDecodeError:
                error_response = {
                    "type": "error",
                    "message": "Invalid message format. Please send JSON.",
                    "session_id": session_id
                }
                await manager.send_personal_message(json.dumps(error_response), websocket)
                
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                error_response = {
                    "type": "error",
                    "message": f"Error processing message: {str(e)}",
                    "session_id": session_id
                }
                await manager.send_personal_message(json.dumps(error_response), websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
        logger.info(f"WebSocket disconnected for session: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        manager.disconnect(websocket, session_id)
