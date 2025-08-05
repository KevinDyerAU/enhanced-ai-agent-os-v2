# Chat Feedback System with Real-time Communication
# File: /services/airlock_system/airlock_system/chat_feedback_system.py

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timezone
import asyncpg
import json
import uuid
import logging
import asyncio
from enum import Enum
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enhanced Models for Chat and Feedback
class ChatParticipantType(str, Enum):
    HUMAN = "human"
    AGENT = "agent"
    SYSTEM = "system"

class MessageType(str, Enum):
    TEXT = "text"
    FEEDBACK = "feedback"
    SUGGESTION = "suggestion"
    APPROVAL = "approval"
    REJECTION = "rejection"
    SYSTEM = "system"
    TYPING = "typing"
    REACTION = "reaction"

class FeedbackType(str, Enum):
    APPROVAL = "approval"
    REJECTION = "rejection"
    SUGGESTION = "suggestion"
    RATING = "rating"
    COMMENT = "comment"
    IMPROVEMENT = "improvement"

class ChatMessage(BaseModel):
    sender_type: ChatParticipantType
    sender_id: str
    sender_name: Optional[str] = None
    message_type: MessageType = MessageType.TEXT
    content: str
    metadata: Optional[Dict[str, Any]] = {}
    reply_to_message_id: Optional[str] = None
    thread_id: Optional[str] = None

class FeedbackMessage(BaseModel):
    feedback_type: FeedbackType
    feedback_data: Dict[str, Any]
    provided_by: str
    provided_by_name: Optional[str] = None
    target_content_id: Optional[str] = None  # For targeting specific content sections
    severity: Optional[str] = "medium"  # low, medium, high, critical

class TypingIndicator(BaseModel):
    sender_id: str
    sender_name: Optional[str] = None
    is_typing: bool

class MessageReaction(BaseModel):
    message_id: str
    reaction: str  # emoji or reaction type
    user_id: str
    user_name: Optional[str] = None

class WebSocketMessage(BaseModel):
    type: str
    data: Dict[str, Any]
    timestamp: Optional[datetime] = None

class ChatFeedbackManager:
    def __init__(self, database_url: str):
        self.database_url = database_url
        # WebSocket connections: {item_id: {connection_id: websocket}}
        self.connections: Dict[str, Dict[str, WebSocket]] = {}
        # Typing indicators: {item_id: {user_id: timestamp}}
        self.typing_indicators: Dict[str, Dict[str, datetime]] = {}
        # User presence: {item_id: {user_id: {name, last_seen}}}
        self.user_presence: Dict[str, Dict[str, Dict[str, Any]]] = {}
        
    async def get_db_connection(self):
        return await asyncpg.connect(self.database_url)
    
    # WebSocket Connection Management
    async def connect_user(self, websocket: WebSocket, item_id: str, user_id: str, user_name: Optional[str] = None):
        """Connect a user to an airlock item chat"""
        await websocket.accept()
        
        connection_id = str(uuid.uuid4())
        
        if item_id not in self.connections:
            self.connections[item_id] = {}
        
        self.connections[item_id][connection_id] = websocket
        
        # Update user presence
        if item_id not in self.user_presence:
            self.user_presence[item_id] = {}
        
        self.user_presence[item_id][user_id] = {
            "name": user_name or user_id,
            "last_seen": datetime.now(timezone.utc),
            "connection_id": connection_id
        }
        
        # Notify other users of new participant
        await self._broadcast_to_item(item_id, {
            "type": "user_joined",
            "user_id": user_id,
            "user_name": user_name or user_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }, exclude_connection=connection_id)
        
        # Send current participants to new user
        await websocket.send_json({
            "type": "participants_list",
            "participants": [
                {"user_id": uid, "name": data["name"], "last_seen": data["last_seen"].isoformat()}
                for uid, data in self.user_presence.get(item_id, {}).items()
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        logger.info(f"User {user_id} connected to item {item_id}")
        return connection_id
    
    async def disconnect_user(self, item_id: str, connection_id: str, user_id: str):
        """Disconnect a user from an airlock item chat"""
        if item_id in self.connections and connection_id in self.connections[item_id]:
            del self.connections[item_id][connection_id]
            
            if not self.connections[item_id]:
                del self.connections[item_id]
        
        # Update user presence
        if item_id in self.user_presence and user_id in self.user_presence[item_id]:
            user_name = self.user_presence[item_id][user_id].get("name", user_id)
            del self.user_presence[item_id][user_id]
            
            if not self.user_presence[item_id]:
                del self.user_presence[item_id]
            
            # Notify other users
            await self._broadcast_to_item(item_id, {
                "type": "user_left",
                "user_id": user_id,
                "user_name": user_name,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        
        # Clear typing indicator
        if item_id in self.typing_indicators and user_id in self.typing_indicators[item_id]:
            del self.typing_indicators[item_id][user_id]
            await self._broadcast_typing_update(item_id)
        
        logger.info(f"User {user_id} disconnected from item {item_id}")
    
    # Message Handling
    async def add_chat_message(self, item_id: str, message: ChatMessage) -> str:
        """Add a chat message and broadcast to connected users"""
        conn = await self.get_db_connection()
        try:
            # Verify item exists
            item_exists = await conn.fetchval("SELECT EXISTS(SELECT 1 FROM airlock_items WHERE id = $1)", item_id)
            if not item_exists:
                raise HTTPException(status_code=404, detail="Airlock item not found")
            
            # Get or create chat session
            session_id = await self._get_or_create_chat_session(conn, item_id, 
                                                              message.sender_type.value, message.sender_id)
            
            # Add message to database
            message_id = str(uuid.uuid4())
            await conn.execute("""
                INSERT INTO airlock_chat_messages (
                    id, session_id, sender_type, sender_id, message_type, content, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, message_id, session_id, message.sender_type.value, message.sender_id,
                message.message_type.value, message.content, json.dumps(message.metadata))
            
            # Broadcast to connected users
            broadcast_data = {
                "type": "new_message",
                "message_id": message_id,
                "sender_type": message.sender_type.value,
                "sender_id": message.sender_id,
                "sender_name": message.sender_name,
                "message_type": message.message_type.value,
                "content": message.content,
                "metadata": message.metadata,
                "reply_to_message_id": message.reply_to_message_id,
                "thread_id": message.thread_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            await self._broadcast_to_item(item_id, broadcast_data)
            
            # Clear typing indicator for sender
            if item_id in self.typing_indicators and message.sender_id in self.typing_indicators[item_id]:
                del self.typing_indicators[item_id][message.sender_id]
                await self._broadcast_typing_update(item_id)
            
            return message_id
            
        finally:
            await conn.close()
    
    async def add_feedback(self, item_id: str, feedback: FeedbackMessage) -> str:
        """Add feedback and broadcast to connected users"""
        conn = await self.get_db_connection()
        try:
            # Verify item exists
            item_exists = await conn.fetchval("SELECT EXISTS(SELECT 1 FROM airlock_items WHERE id = $1)", item_id)
            if not item_exists:
                raise HTTPException(status_code=404, detail="Airlock item not found")
            
            feedback_id = str(uuid.uuid4())
            await conn.execute("""
                INSERT INTO airlock_feedback (
                    id, airlock_item_id, feedback_type, feedback_data, provided_by
                ) VALUES ($1, $2, $3, $4, $5)
            """, feedback_id, item_id, feedback.feedback_type.value, 
                json.dumps({
                    **feedback.feedback_data,
                    "provided_by_name": feedback.provided_by_name,
                    "target_content_id": feedback.target_content_id,
                    "severity": feedback.severity
                }), feedback.provided_by)
            
            # Add as chat message too
            feedback_message = ChatMessage(
                sender_type=ChatParticipantType.HUMAN,
                sender_id=feedback.provided_by,
                sender_name=feedback.provided_by_name,
                message_type=MessageType.FEEDBACK,
                content=f"Feedback: {feedback.feedback_type.value}",
                metadata={
                    "feedback_id": feedback_id,
                    "feedback_type": feedback.feedback_type.value,
                    "feedback_data": feedback.feedback_data,
                    "severity": feedback.severity,
                    "target_content_id": feedback.target_content_id
                }
            )
            
            await self.add_chat_message(item_id, feedback_message)
            
            # Broadcast feedback notification
            await self._broadcast_to_item(item_id, {
                "type": "new_feedback",
                "feedback_id": feedback_id,
                "feedback_type": feedback.feedback_type.value,
                "provided_by": feedback.provided_by,
                "provided_by_name": feedback.provided_by_name,
                "severity": feedback.severity,
                "target_content_id": feedback.target_content_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            return feedback_id
            
        finally:
            await conn.close()
    
    async def handle_typing_indicator(self, item_id: str, typing: TypingIndicator):
        """Handle typing indicator updates"""
        if item_id not in self.typing_indicators:
            self.typing_indicators[item_id] = {}
        
        if typing.is_typing:
            self.typing_indicators[item_id][typing.sender_id] = datetime.now(timezone.utc)
        else:
            if typing.sender_id in self.typing_indicators[item_id]:
                del self.typing_indicators[item_id][typing.sender_id]
        
        await self._broadcast_typing_update(item_id)
    
    async def handle_message_reaction(self, item_id: str, reaction: MessageReaction):
        """Handle message reactions"""
        conn = await self.get_db_connection()
        try:
            # Store reaction in database (you might want to create a reactions table)
            # For now, we'll just broadcast it
            await self._broadcast_to_item(item_id, {
                "type": "message_reaction",
                "message_id": reaction.message_id,
                "reaction": reaction.reaction,
                "user_id": reaction.user_id,
                "user_name": reaction.user_name,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
        finally:
            await conn.close()
    
    async def get_chat_history(self, item_id: str, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get chat history for an item"""
        conn = await self.get_db_connection()
        try:
            rows = await conn.fetch("""
                SELECT acm.*
                FROM airlock_chat_messages acm
                JOIN airlock_chat_sessions acs ON acm.session_id = acs.id
                WHERE acs.airlock_item_id = $1
                ORDER BY acm.created_at ASC
                LIMIT $2 OFFSET $3
            """, item_id, limit, offset)
            
            return [{
                "id": str(row['id']),
                "sender_type": row['sender_type'],
                "sender_id": row['sender_id'],
                "message_type": row['message_type'],
                "content": row['content'],
                "metadata": json.loads(row['metadata']),
                "created_at": row['created_at'].isoformat()
            } for row in rows]
            
        finally:
            await conn.close()
    
    async def get_feedback_history(self, item_id: str) -> List[Dict]:
        """Get feedback history for an item"""
        conn = await self.get_db_connection()
        try:
            rows = await conn.fetch("""
                SELECT * FROM airlock_feedback 
                WHERE airlock_item_id = $1 
                ORDER BY created_at DESC
            """, item_id)
            
            return [{
                "id": str(row['id']),
                "feedback_type": row['feedback_type'],
                "feedback_data": json.loads(row['feedback_data']),
                "provided_by": row['provided_by'],
                "created_at": row['created_at'].isoformat()
            } for row in rows]
            
        finally:
            await conn.close()
    
    # Broadcasting and Notifications
    async def _broadcast_to_item(self, item_id: str, message: Dict, exclude_connection: Optional[str] = None):
        """Broadcast a message to all connected users for an item"""
        if item_id not in self.connections:
            return
        
        disconnected = []
        for connection_id, websocket in self.connections[item_id].items():
            if exclude_connection and connection_id == exclude_connection:
                continue
                
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send message to connection {connection_id}: {e}")
                disconnected.append(connection_id)
        
        # Remove disconnected websockets
        for conn_id in disconnected:
            if conn_id in self.connections[item_id]:
                del self.connections[item_id][conn_id]
    
    async def _broadcast_typing_update(self, item_id: str):
        """Broadcast typing indicator updates"""
        if item_id not in self.typing_indicators:
            typing_users = []
        else:
            # Clean up old typing indicators (older than 10 seconds)
            current_time = datetime.now(timezone.utc)
            expired_users = [
                user_id for user_id, timestamp in self.typing_indicators[item_id].items()
                if (current_time - timestamp).total_seconds() > 10
            ]
            
            for user_id in expired_users:
                del self.typing_indicators[item_id][user_id]
            
            typing_users = [
                {
                    "user_id": user_id,
                    "user_name": self.user_presence.get(item_id, {}).get(user_id, {}).get("name", user_id)
                }
                for user_id in self.typing_indicators[item_id].keys()
            ]
        
        await self._broadcast_to_item(item_id, {
            "type": "typing_update",
            "typing_users": typing_users,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    # Helper Methods
    async def _get_or_create_chat_session(self, conn, item_id: str, participant_type: str, participant_id: str) -> str:
        """Get or create chat session"""
        row = await conn.fetchrow("""
            SELECT id FROM airlock_chat_sessions 
            WHERE airlock_item_id = $1 AND participant_type = $2 AND participant_id = $3
        """, item_id, participant_type, participant_id)
        
        if row:
            return str(row['id'])
        
        # Create new session
        session_id = str(uuid.uuid4())
        await conn.execute("""
            INSERT INTO airlock_chat_sessions (id, airlock_item_id, participant_type, participant_id)
            VALUES ($1, $2, $3, $4)
        """, session_id, item_id, participant_type, participant_id)
        
        return session_id
    
    # Background Tasks
    async def cleanup_expired_typing_indicators(self):
        """Background task to clean up expired typing indicators"""
        while True:
            try:
                current_time = datetime.now(timezone.utc)
                
                for item_id in list(self.typing_indicators.keys()):
                    expired_users = [
                        user_id for user_id, timestamp in self.typing_indicators[item_id].items()
                        if (current_time - timestamp).total_seconds() > 10
                    ]
                    
                    if expired_users:
                        for user_id in expired_users:
                            del self.typing_indicators[item_id][user_id]
                        
                        await self._broadcast_typing_update(item_id)
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(5)

# FastAPI Integration
app = FastAPI(title="Chat Feedback System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize chat manager
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://aos_user:aos_password@postgres:5432/aos_db")
chat_manager = ChatFeedbackManager(DATABASE_URL)

# Start background tasks
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(chat_manager.cleanup_expired_typing_indicators())

# WebSocket endpoint
@app.websocket("/api/v1/chat/{item_id}/ws")
async def websocket_endpoint(websocket: WebSocket, item_id: str, user_id: str, user_name: Optional[str] = None):
    """WebSocket endpoint for real-time chat and feedback"""
    connection_id = await chat_manager.connect_user(websocket, item_id, user_id, user_name)
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                message_type = message_data.get("type")
                
                if message_type == "ping":
                    await websocket.send_json({
                        "type": "pong", 
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                
                elif message_type == "chat_message":
                    chat_msg = ChatMessage(**message_data["data"])
                    await chat_manager.add_chat_message(item_id, chat_msg)
                
                elif message_type == "feedback":
                    feedback_msg = FeedbackMessage(**message_data["data"])
                    await chat_manager.add_feedback(item_id, feedback_msg)
                
                elif message_type == "typing":
                    typing_indicator = TypingIndicator(**message_data["data"])
                    await chat_manager.handle_typing_indicator(item_id, typing_indicator)
                
                elif message_type == "reaction":
                    reaction = MessageReaction(**message_data["data"])
                    await chat_manager.handle_message_reaction(item_id, reaction)
                
                else:
                    await websocket.send_json({
                        "type": "error", 
                        "message": f"Unknown message type: {message_type}"
                    })
                    
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await websocket.send_json({"type": "error", "message": str(e)})
                
    except WebSocketDisconnect:
        await chat_manager.disconnect_user(item_id, connection_id, user_id)

# REST API endpoints
@app.post("/api/v1/chat/{item_id}/messages")
async def add_message(item_id: str, message: ChatMessage):
    """Add a chat message via REST API"""
    message_id = await chat_manager.add_chat_message(item_id, message)
    return {"message_id": message_id, "status": "added"}

@app.get("/api/v1/chat/{item_id}/messages")
async def get_messages(item_id: str, limit: int = 50, offset: int = 0):
    """Get chat history via REST API"""
    return await chat_manager.get_chat_history(item_id, limit, offset)

@app.post("/api/v1/chat/{item_id}/feedback")
async def add_feedback_rest(item_id: str, feedback: FeedbackMessage):
    """Add feedback via REST API"""
    feedback_id = await chat_manager.add_feedback(item_id, feedback)
    return {"feedback_id": feedback_id, "status": "added"}

@app.get("/api/v1/chat/{item_id}/feedback")
async def get_feedback_rest(item_id: str):
    """Get feedback history via REST API"""
    return await chat_manager.get_feedback_history(item_id)

@app.get("/api/v1/chat/{item_id}/participants")
async def get_participants(item_id: str):
    """Get current participants in a chat"""
    participants = []
    if item_id in chat_manager.user_presence:
        participants = [
            {
                "user_id": user_id,
                "name": data["name"],
                "last_seen": data["last_seen"].isoformat()
            }
            for user_id, data in chat_manager.user_presence[item_id].items()
        ]
    
    return {"participants": participants}

@app.get("/api/v1/chat/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "service": "chat_feedback_system",
        "active_connections": sum(len(conns) for conns in chat_manager.connections.values()),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

