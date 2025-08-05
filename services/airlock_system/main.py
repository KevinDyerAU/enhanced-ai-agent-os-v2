# Universal Airlock Service - Complete Implementation
# File: /services/airlock_system/airlock_system/universal_airlock_service.py

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone
import asyncpg
import json
import uuid
import logging
from enum import Enum
import os
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic Models
class ContentType(str, Enum):
    TRAINING_VALIDATION = "training_validation"
    CREATIVE_ASSET = "creative_asset"
    IDEATION = "ideation"
    DESIGN = "design"
    CAMPAIGN = "campaign"
    DOCUMENT = "document"
    REPORT = "report"

class AirlockStatus(str, Enum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_CHANGES = "requires_changes"
    IN_REVISION = "in_revision"

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class MessageType(str, Enum):
    TEXT = "text"
    FEEDBACK = "feedback"
    SUGGESTION = "suggestion"
    APPROVAL = "approval"
    REJECTION = "rejection"
    SYSTEM = "system"

class FeedbackType(str, Enum):
    APPROVAL = "approval"
    REJECTION = "rejection"
    SUGGESTION = "suggestion"
    RATING = "rating"
    COMMENT = "comment"

class AirlockItemCreate(BaseModel):
    content_type: ContentType
    source_service: str
    source_id: str
    title: str
    description: Optional[str] = None
    content: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = {}
    priority: Priority = Priority.MEDIUM
    assigned_reviewer_id: Optional[str] = None
    review_deadline: Optional[datetime] = None

class AirlockItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    status: Optional[AirlockStatus] = None
    assigned_reviewer_id: Optional[str] = None
    review_deadline: Optional[datetime] = None

class ChatMessage(BaseModel):
    sender_type: str  # 'human' or 'agent'
    sender_id: str
    message_type: MessageType = MessageType.TEXT
    content: str
    metadata: Optional[Dict[str, Any]] = {}

class FeedbackCreate(BaseModel):
    feedback_type: FeedbackType
    feedback_data: Dict[str, Any]
    provided_by: str

class RevisionCreate(BaseModel):
    content: Dict[str, Any]
    changes_summary: Optional[str] = None
    created_by: str

class AirlockItemResponse(BaseModel):
    id: str
    content_type: str
    source_service: str
    source_id: str
    title: str
    description: Optional[str]
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    status: str
    priority: str
    created_by_agent_id: Optional[str]
    assigned_reviewer_id: Optional[str]
    reviewed_by: Optional[str]
    reviewed_at: Optional[datetime]
    review_deadline: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    revision_count: Optional[int] = 0
    latest_revision: Optional[int] = None

class ChatMessageResponse(BaseModel):
    id: str
    sender_type: str
    sender_id: str
    message_type: str
    content: str
    metadata: Dict[str, Any]
    created_at: datetime

class FeedbackResponse(BaseModel):
    id: str
    feedback_type: str
    feedback_data: Dict[str, Any]
    provided_by: str
    created_at: datetime

class RevisionResponse(BaseModel):
    id: str
    revision_number: int
    content: Dict[str, Any]
    changes_summary: Optional[str]
    created_by: str
    created_at: datetime

class UniversalAirlockService:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.active_connections: Dict[str, List[WebSocket]] = {}
        
    async def get_db_connection(self):
        return await asyncpg.connect(self.database_url)
    
    async def create_airlock_item(self, item: AirlockItemCreate, created_by_agent_id: Optional[str] = None) -> str:
        """Create a new airlock item for review"""
        conn = await self.get_db_connection()
        try:
            # Get or create content type
            content_type_id = await self._get_or_create_content_type(conn, item.content_type)
            
            # Create airlock item
            item_id = str(uuid.uuid4())
            await conn.execute("""
                INSERT INTO airlock_items (
                    id, content_type_id, source_service, source_id, title, description,
                    content, metadata, priority, created_by_agent_id, assigned_reviewer_id,
                    review_deadline
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            """, item_id, content_type_id, item.source_service, item.source_id,
                item.title, item.description, json.dumps(item.content),
                json.dumps(item.metadata), item.priority.value, created_by_agent_id,
                item.assigned_reviewer_id, item.review_deadline)
            
            # Create initial chat session
            await self._create_chat_session(conn, item_id, "agent", "airlock_system")
            
            # Add system message
            await self._add_system_message(conn, item_id, f"Airlock item created for review: {item.title}")
            
            # Log audit event
            await self._log_audit_event(conn, "airlock_item_created", "airlock_item", item_id, 
                                      created_by_agent_id or "system", "create", {
                                          "source_service": item.source_service,
                                          "source_id": item.source_id,
                                          "title": item.title
                                      })
            
            # Notify assigned reviewer if specified
            if item.assigned_reviewer_id:
                await self._notify_reviewer(item_id, item.assigned_reviewer_id, "assigned")
            
            return item_id
            
        finally:
            await conn.close()
    
    async def get_airlock_item(self, item_id: str) -> Optional[AirlockItemResponse]:
        """Get airlock item by ID with revision information"""
        conn = await self.get_db_connection()
        try:
            row = await conn.fetchrow("""
                SELECT ai.*, act.name as content_type_name,
                       (SELECT COUNT(*) FROM airlock_revisions ar WHERE ar.airlock_item_id = ai.id) as revision_count,
                       (SELECT MAX(revision_number) FROM airlock_revisions ar WHERE ar.airlock_item_id = ai.id) as latest_revision
                FROM airlock_items ai
                JOIN airlock_content_types act ON ai.content_type_id = act.id
                WHERE ai.id = $1
            """, item_id)
            
            if not row:
                return None
                
            return AirlockItemResponse(
                id=str(row['id']),
                content_type=row['content_type_name'],
                source_service=row['source_service'],
                source_id=row['source_id'],
                title=row['title'],
                description=row['description'],
                content=json.loads(row['content']),
                metadata=json.loads(row['metadata']),
                status=row['status'],
                priority=row['priority'],
                created_by_agent_id=str(row['created_by_agent_id']) if row['created_by_agent_id'] else None,
                assigned_reviewer_id=row['assigned_reviewer_id'],
                reviewed_by=row['approved_by'] or row['rejected_by'],
                reviewed_at=row['approved_at'] or row['rejected_at'],
                review_deadline=row['review_deadline'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                revision_count=row['revision_count'] or 0,
                latest_revision=row['latest_revision']
            )
            
        finally:
            await conn.close()
    
    async def list_airlock_items(self, status: Optional[str] = None, 
                                assigned_reviewer: Optional[str] = None,
                                source_service: Optional[str] = None,
                                content_type: Optional[str] = None,
                                priority: Optional[str] = None,
                                limit: int = 50, offset: int = 0) -> List[AirlockItemResponse]:
        """List airlock items with optional filters"""
        conn = await self.get_db_connection()
        try:
            query = """
                SELECT ai.*, act.name as content_type_name,
                       (SELECT COUNT(*) FROM airlock_revisions ar WHERE ar.airlock_item_id = ai.id) as revision_count,
                       (SELECT MAX(revision_number) FROM airlock_revisions ar WHERE ar.airlock_item_id = ai.id) as latest_revision
                FROM airlock_items ai
                JOIN airlock_content_types act ON ai.content_type_id = act.id
                WHERE 1=1
            """
            params = []
            param_count = 0
            
            if status:
                param_count += 1
                query += f" AND ai.status = ${param_count}"
                params.append(status)
            
            if assigned_reviewer:
                param_count += 1
                query += f" AND ai.assigned_reviewer_id = ${param_count}"
                params.append(assigned_reviewer)
                
            if source_service:
                param_count += 1
                query += f" AND ai.source_service = ${param_count}"
                params.append(source_service)
                
            if content_type:
                param_count += 1
                query += f" AND act.name = ${param_count}"
                params.append(content_type)
                
            if priority:
                param_count += 1
                query += f" AND ai.priority = ${param_count}"
                params.append(priority)
            
            query += f" ORDER BY ai.created_at DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
            params.extend([limit, offset])
            
            rows = await conn.fetch(query, *params)
            
            return [AirlockItemResponse(
                id=str(row['id']),
                content_type=row['content_type_name'],
                source_service=row['source_service'],
                source_id=row['source_id'],
                title=row['title'],
                description=row['description'],
                content=json.loads(row['content']),
                metadata=json.loads(row['metadata']),
                status=row['status'],
                priority=row['priority'],
                created_by_agent_id=str(row['created_by_agent_id']) if row['created_by_agent_id'] else None,
                assigned_reviewer_id=row['assigned_reviewer_id'],
                reviewed_by=row['approved_by'] or row['rejected_by'],
                reviewed_at=row['approved_at'] or row['rejected_at'],
                review_deadline=row['review_deadline'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                revision_count=row['revision_count'] or 0,
                latest_revision=row['latest_revision']
            ) for row in rows]
            
        finally:
            await conn.close()
    
    async def update_airlock_item(self, item_id: str, update: AirlockItemUpdate, 
                                 updated_by: str) -> bool:
        """Update airlock item"""
        conn = await self.get_db_connection()
        try:
            # Get current item for comparison
            current_item = await conn.fetchrow("SELECT * FROM airlock_items WHERE id = $1", item_id)
            if not current_item:
                return False
            
            # Build dynamic update query
            set_clauses = []
            params = []
            param_count = 0
            changes = {}
            
            if update.title is not None and update.title != current_item['title']:
                param_count += 1
                set_clauses.append(f"title = ${param_count}")
                params.append(update.title)
                changes['title'] = {'from': current_item['title'], 'to': update.title}
            
            if update.description is not None and update.description != current_item['description']:
                param_count += 1
                set_clauses.append(f"description = ${param_count}")
                params.append(update.description)
                changes['description'] = {'from': current_item['description'], 'to': update.description}
                
            if update.content is not None:
                param_count += 1
                set_clauses.append(f"content = ${param_count}")
                params.append(json.dumps(update.content))
                changes['content'] = 'updated'
                
            if update.metadata is not None:
                param_count += 1
                set_clauses.append(f"metadata = ${param_count}")
                params.append(json.dumps(update.metadata))
                changes['metadata'] = 'updated'
                
            if update.status is not None and update.status.value != current_item['status']:
                param_count += 1
                set_clauses.append(f"status = ${param_count}")
                params.append(update.status.value)
                changes['status'] = {'from': current_item['status'], 'to': update.status.value}
                
                if update.status in [AirlockStatus.APPROVED, AirlockStatus.REJECTED]:
                    if update.status == AirlockStatus.APPROVED:
                        param_count += 1
                        set_clauses.append(f"approved_by = ${param_count}")
                        params.append(updated_by)
                        
                        param_count += 1
                        set_clauses.append(f"approved_at = ${param_count}")
                        params.append(datetime.now(timezone.utc))
                    else:  # REJECTED
                        param_count += 1
                        set_clauses.append(f"rejected_by = ${param_count}")
                        params.append(updated_by)
                        
                        param_count += 1
                        set_clauses.append(f"rejected_at = ${param_count}")
                        params.append(datetime.now(timezone.utc))
                    
                    # Add system message for status change
                    status_message = f"Item {update.status.value} by {updated_by}"
                    await self._add_system_message(conn, item_id, status_message)
            
            if update.assigned_reviewer_id is not None and update.assigned_reviewer_id != current_item['assigned_reviewer_id']:
                param_count += 1
                set_clauses.append(f"assigned_reviewer_id = ${param_count}")
                params.append(update.assigned_reviewer_id)
                changes['assigned_reviewer'] = {'from': current_item['assigned_reviewer_id'], 'to': update.assigned_reviewer_id}
                
                # Notify new reviewer
                if update.assigned_reviewer_id:
                    await self._notify_reviewer(item_id, update.assigned_reviewer_id, "assigned")
                
            if update.review_deadline is not None and update.review_deadline != current_item['review_deadline']:
                param_count += 1
                set_clauses.append(f"review_deadline = ${param_count}")
                params.append(update.review_deadline)
                changes['review_deadline'] = {'from': current_item['review_deadline'], 'to': update.review_deadline}
            
            if not set_clauses:
                return False
            
            # Add updated_at
            param_count += 1
            set_clauses.append(f"updated_at = ${param_count}")
            params.append(datetime.now(timezone.utc))
            
            # Add WHERE clause
            param_count += 1
            params.append(item_id)
            
            query = f"""
                UPDATE airlock_items 
                SET {', '.join(set_clauses)}
                WHERE id = ${param_count}
            """
            
            result = await conn.execute(query, *params)
            
            if result == "UPDATE 1":
                # Log audit event
                await self._log_audit_event(conn, "airlock_item_updated", "airlock_item", 
                                          item_id, updated_by, "update", changes)
                
                # Broadcast update to connected clients
                await self._broadcast_to_item(item_id, {
                    "type": "item_updated",
                    "item_id": item_id,
                    "changes": changes,
                    "updated_by": updated_by,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
                return True
            
            return False
            
        finally:
            await conn.close()
    
    async def add_chat_message(self, item_id: str, message: ChatMessage) -> str:
        """Add a chat message to an airlock item"""
        conn = await self.get_db_connection()
        try:
            # Verify item exists
            item_exists = await conn.fetchval("SELECT EXISTS(SELECT 1 FROM airlock_items WHERE id = $1)", item_id)
            if not item_exists:
                raise HTTPException(status_code=404, detail="Airlock item not found")
            
            # Get or create chat session
            session_id = await self._get_or_create_chat_session(conn, item_id, 
                                                              message.sender_type, message.sender_id)
            
            # Add message
            message_id = str(uuid.uuid4())
            await conn.execute("""
                INSERT INTO airlock_chat_messages (
                    id, session_id, sender_type, sender_id, message_type, content, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, message_id, session_id, message.sender_type, message.sender_id,
                message.message_type.value, message.content, json.dumps(message.metadata))
            
            # Notify connected clients
            await self._broadcast_to_item(item_id, {
                "type": "new_message",
                "message_id": message_id,
                "sender_type": message.sender_type,
                "sender_id": message.sender_id,
                "content": message.content,
                "message_type": message.message_type.value,
                "metadata": message.metadata,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            return message_id
            
        finally:
            await conn.close()
    
    async def get_chat_messages(self, item_id: str, limit: int = 50, offset: int = 0) -> List[ChatMessageResponse]:
        """Get chat messages for an airlock item"""
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
            
            return [ChatMessageResponse(
                id=str(row['id']),
                sender_type=row['sender_type'],
                sender_id=row['sender_id'],
                message_type=row['message_type'],
                content=row['content'],
                metadata=json.loads(row['metadata']),
                created_at=row['created_at']
            ) for row in rows]
            
        finally:
            await conn.close()
    
    async def add_feedback(self, item_id: str, feedback: FeedbackCreate) -> str:
        """Add feedback to an airlock item"""
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
                json.dumps(feedback.feedback_data), feedback.provided_by)
            
            # Add system message for feedback
            feedback_message = f"Feedback added by {feedback.provided_by}: {feedback.feedback_type.value}"
            await self._add_system_message(conn, item_id, feedback_message)
            
            # Notify connected clients
            await self._broadcast_to_item(item_id, {
                "type": "new_feedback",
                "feedback_id": feedback_id,
                "feedback_type": feedback.feedback_type.value,
                "provided_by": feedback.provided_by,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            return feedback_id
            
        finally:
            await conn.close()
    
    async def get_feedback(self, item_id: str) -> List[FeedbackResponse]:
        """Get all feedback for an airlock item"""
        conn = await self.get_db_connection()
        try:
            rows = await conn.fetch("""
                SELECT * FROM airlock_feedback 
                WHERE airlock_item_id = $1 
                ORDER BY created_at DESC
            """, item_id)
            
            return [FeedbackResponse(
                id=str(row['id']),
                feedback_type=row['feedback_type'],
                feedback_data=json.loads(row['feedback_data']),
                provided_by=row['provided_by'],
                created_at=row['created_at']
            ) for row in rows]
            
        finally:
            await conn.close()
    
    async def create_revision(self, item_id: str, revision: RevisionCreate) -> str:
        """Create a new revision of an airlock item"""
        conn = await self.get_db_connection()
        try:
            # Get current revision number
            current_revision = await conn.fetchval("""
                SELECT COALESCE(MAX(revision_number), 0) FROM airlock_revisions 
                WHERE airlock_item_id = $1
            """, item_id)
            
            new_revision_number = current_revision + 1
            revision_id = str(uuid.uuid4())
            
            # Create revision
            await conn.execute("""
                INSERT INTO airlock_revisions (
                    id, airlock_item_id, revision_number, content, changes_summary, created_by
                ) VALUES ($1, $2, $3, $4, $5, $6)
            """, revision_id, item_id, new_revision_number, json.dumps(revision.content),
                revision.changes_summary, revision.created_by)
            
            # Update main item with new content and status
            await conn.execute("""
                UPDATE airlock_items 
                SET content = $1, status = $2, updated_at = $3
                WHERE id = $4
            """, json.dumps(revision.content), AirlockStatus.IN_REVISION.value, 
                datetime.now(timezone.utc), item_id)
            
            # Add system message
            revision_message = f"Revision {new_revision_number} created by {revision.created_by}"
            if revision.changes_summary:
                revision_message += f": {revision.changes_summary}"
            await self._add_system_message(conn, item_id, revision_message)
            
            # Notify connected clients
            await self._broadcast_to_item(item_id, {
                "type": "new_revision",
                "revision_id": revision_id,
                "revision_number": new_revision_number,
                "created_by": revision.created_by,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            return revision_id
            
        finally:
            await conn.close()
    
    async def get_revisions(self, item_id: str) -> List[RevisionResponse]:
        """Get all revisions for an airlock item"""
        conn = await self.get_db_connection()
        try:
            rows = await conn.fetch("""
                SELECT * FROM airlock_revisions 
                WHERE airlock_item_id = $1 
                ORDER BY revision_number DESC
            """, item_id)
            
            return [RevisionResponse(
                id=str(row['id']),
                revision_number=row['revision_number'],
                content=json.loads(row['content']),
                changes_summary=row['changes_summary'],
                created_by=row['created_by'],
                created_at=row['created_at']
            ) for row in rows]
            
        finally:
            await conn.close()
    
    async def get_dashboard_stats(self, reviewer_id: Optional[str] = None) -> Dict[str, Any]:
        """Get dashboard statistics"""
        conn = await self.get_db_connection()
        try:
            # Base stats
            stats = {}
            
            # Total items by status
            status_query = "SELECT status, COUNT(*) as count FROM airlock_items"
            status_params = []
            
            if reviewer_id:
                status_query += " WHERE assigned_reviewer_id = $1"
                status_params.append(reviewer_id)
            
            status_query += " GROUP BY status"
            
            status_rows = await conn.fetch(status_query, *status_params)
            stats['by_status'] = {row['status']: row['count'] for row in status_rows}
            
            # Items by priority
            priority_query = "SELECT priority, COUNT(*) as count FROM airlock_items"
            priority_params = []
            
            if reviewer_id:
                priority_query += " WHERE assigned_reviewer_id = $1"
                priority_params.append(reviewer_id)
            
            priority_query += " GROUP BY priority"
            
            priority_rows = await conn.fetch(priority_query, *priority_params)
            stats['by_priority'] = {row['priority']: row['count'] for row in priority_rows}
            
            # Items by content type
            content_type_query = """
                SELECT act.name, COUNT(*) as count 
                FROM airlock_items ai
                JOIN airlock_content_types act ON ai.content_type_id = act.id
            """
            content_type_params = []
            
            if reviewer_id:
                content_type_query += " WHERE ai.assigned_reviewer_id = $1"
                content_type_params.append(reviewer_id)
            
            content_type_query += " GROUP BY act.name"
            
            content_type_rows = await conn.fetch(content_type_query, *content_type_params)
            stats['by_content_type'] = {row['name']: row['count'] for row in content_type_rows}
            
            # Overdue items
            overdue_query = """
                SELECT COUNT(*) as count FROM airlock_items 
                WHERE review_deadline < NOW() AND status = 'pending_review'
            """
            overdue_params = []
            
            if reviewer_id:
                overdue_query += " AND assigned_reviewer_id = $1"
                overdue_params.append(reviewer_id)
            
            overdue_count = await conn.fetchval(overdue_query, *overdue_params)
            stats['overdue_count'] = overdue_count
            
            return stats
            
        finally:
            await conn.close()
    
    # WebSocket connection management
    async def connect_websocket(self, websocket: WebSocket, item_id: str):
        """Connect a WebSocket to an airlock item"""
        await websocket.accept()
        if item_id not in self.active_connections:
            self.active_connections[item_id] = []
        self.active_connections[item_id].append(websocket)
        logger.info(f"WebSocket connected to item {item_id}")
    
    async def disconnect_websocket(self, websocket: WebSocket, item_id: str):
        """Disconnect a WebSocket from an airlock item"""
        if item_id in self.active_connections:
            if websocket in self.active_connections[item_id]:
                self.active_connections[item_id].remove(websocket)
            if not self.active_connections[item_id]:
                del self.active_connections[item_id]
        logger.info(f"WebSocket disconnected from item {item_id}")
    
    async def _broadcast_to_item(self, item_id: str, message: Dict):
        """Broadcast a message to all connected clients for an item"""
        if item_id in self.active_connections:
            disconnected = []
            for websocket in self.active_connections[item_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.warning(f"Failed to send message to websocket: {e}")
                    disconnected.append(websocket)
            
            # Remove disconnected websockets
            for ws in disconnected:
                self.active_connections[item_id].remove(ws)
    
    # Helper methods
    async def _get_or_create_content_type(self, conn, content_type: ContentType) -> int:
        """Get or create content type"""
        row = await conn.fetchrow("""
            SELECT id FROM airlock_content_types WHERE name = $1
        """, content_type.value)
        
        if row:
            return row['id']
        
        # Create new content type
        row = await conn.fetchrow("""
            INSERT INTO airlock_content_types (name, description)
            VALUES ($1, $2) RETURNING id
        """, content_type.value, f"Content type for {content_type.value}")
        
        return row['id']
    
    async def _create_chat_session(self, conn, item_id: str, participant_type: str, participant_id: str) -> str:
        """Create a chat session"""
        session_id = str(uuid.uuid4())
        await conn.execute("""
            INSERT INTO airlock_chat_sessions (id, airlock_item_id, participant_type, participant_id)
            VALUES ($1, $2, $3, $4)
        """, session_id, item_id, participant_type, participant_id)
        return session_id
    
    async def _get_or_create_chat_session(self, conn, item_id: str, participant_type: str, participant_id: str) -> str:
        """Get or create chat session"""
        row = await conn.fetchrow("""
            SELECT id FROM airlock_chat_sessions 
            WHERE airlock_item_id = $1 AND participant_type = $2 AND participant_id = $3
        """, item_id, participant_type, participant_id)
        
        if row:
            return str(row['id'])
        
        return await self._create_chat_session(conn, item_id, participant_type, participant_id)
    
    async def _add_system_message(self, conn, item_id: str, content: str):
        """Add a system message to the chat"""
        session_id = await self._get_or_create_chat_session(conn, item_id, "agent", "airlock_system")
        message_id = str(uuid.uuid4())
        await conn.execute("""
            INSERT INTO airlock_chat_messages (
                id, session_id, sender_type, sender_id, message_type, content, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, message_id, session_id, "agent", "airlock_system", 
            "text", content, json.dumps({}))
    
    async def _notify_reviewer(self, item_id: str, reviewer_id: str, action: str):
        """Notify reviewer of assignment or other actions"""
        # This could be extended to send actual notifications (email, Slack, etc.)
        logger.info(f"Reviewer {reviewer_id} {action} to item {item_id}")
    
    async def _log_audit_event(self, conn, event_type: str, entity_type: str, entity_id: str,
                              actor_id: str, action: str, details: Dict):
        """Log audit event"""
        try:
            await conn.execute("""
                INSERT INTO audit_logs (event_type, entity_type, entity_id, actor_type, actor_id, action, details)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, event_type, entity_type, entity_id, "user", actor_id, action, json.dumps(details))
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")

# FastAPI app
app = FastAPI(title="Universal Airlock System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize service
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://aos_user:aos_password@postgres:5432/aos_db")
airlock_service = UniversalAirlockService(DATABASE_URL)

# API Endpoints
@app.post("/api/v1/airlock/items", response_model=Dict[str, str])
async def create_airlock_item(item: AirlockItemCreate, created_by_agent_id: Optional[str] = None):
    """Create a new airlock item for review"""
    try:
        item_id = await airlock_service.create_airlock_item(item, created_by_agent_id)
        return {"item_id": item_id, "status": "created"}
    except Exception as e:
        logger.error(f"Error creating airlock item: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/airlock/items/{item_id}", response_model=AirlockItemResponse)
async def get_airlock_item(item_id: str):
    """Get airlock item by ID"""
    item = await airlock_service.get_airlock_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Airlock item not found")
    return item

@app.get("/api/v1/airlock/items", response_model=List[AirlockItemResponse])
async def list_airlock_items(
    status: Optional[str] = Query(None, description="Filter by status"),
    assigned_reviewer: Optional[str] = Query(None, description="Filter by assigned reviewer"),
    source_service: Optional[str] = Query(None, description="Filter by source service"),
    content_type: Optional[str] = Query(None, description="Filter by content type"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    limit: int = Query(50, ge=1, le=100, description="Number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip")
):
    """List airlock items with optional filters"""
    return await airlock_service.list_airlock_items(
        status, assigned_reviewer, source_service, content_type, priority, limit, offset
    )

@app.put("/api/v1/airlock/items/{item_id}")
async def update_airlock_item(item_id: str, update: AirlockItemUpdate, updated_by: str = Query(..., description="ID of user making the update")):
    """Update airlock item"""
    success = await airlock_service.update_airlock_item(item_id, update, updated_by)
    if not success:
        raise HTTPException(status_code=404, detail="Airlock item not found or no changes made")
    return {"status": "updated"}

@app.post("/api/v1/airlock/items/{item_id}/messages")
async def add_chat_message(item_id: str, message: ChatMessage):
    """Add a chat message to an airlock item"""
    message_id = await airlock_service.add_chat_message(item_id, message)
    return {"message_id": message_id, "status": "added"}

@app.get("/api/v1/airlock/items/{item_id}/messages", response_model=List[ChatMessageResponse])
async def get_chat_messages(item_id: str, limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0)):
    """Get chat messages for an airlock item"""
    return await airlock_service.get_chat_messages(item_id, limit, offset)

@app.post("/api/v1/airlock/items/{item_id}/feedback")
async def add_feedback(item_id: str, feedback: FeedbackCreate):
    """Add feedback to an airlock item"""
    feedback_id = await airlock_service.add_feedback(item_id, feedback)
    return {"feedback_id": feedback_id, "status": "added"}

@app.get("/api/v1/airlock/items/{item_id}/feedback", response_model=List[FeedbackResponse])
async def get_feedback(item_id: str):
    """Get all feedback for an airlock item"""
    return await airlock_service.get_feedback(item_id)

@app.post("/api/v1/airlock/items/{item_id}/revisions")
async def create_revision(item_id: str, revision: RevisionCreate):
    """Create a new revision of an airlock item"""
    revision_id = await airlock_service.create_revision(item_id, revision)
    return {"revision_id": revision_id, "status": "created"}

@app.get("/api/v1/airlock/items/{item_id}/revisions", response_model=List[RevisionResponse])
async def get_revisions(item_id: str):
    """Get all revisions for an airlock item"""
    return await airlock_service.get_revisions(item_id)

@app.get("/api/v1/airlock/dashboard/stats")
async def get_dashboard_stats(reviewer_id: Optional[str] = Query(None, description="Filter stats by reviewer")):
    """Get dashboard statistics"""
    return await airlock_service.get_dashboard_stats(reviewer_id)

@app.websocket("/api/v1/airlock/items/{item_id}/ws")
async def websocket_endpoint(websocket: WebSocket, item_id: str):
    """WebSocket endpoint for real-time communication"""
    await airlock_service.connect_websocket(websocket, item_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                # Handle different message types
                if message_data.get("type") == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": datetime.now(timezone.utc).isoformat()})
                elif message_data.get("type") == "chat_message":
                    # Process chat message
                    chat_msg = ChatMessage(**message_data["data"])
                    await airlock_service.add_chat_message(item_id, chat_msg)
                else:
                    # Echo back unknown messages
                    await websocket.send_json({"type": "echo", "data": message_data})
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
            except Exception as e:
                await websocket.send_json({"type": "error", "message": str(e)})
    except WebSocketDisconnect:
        await airlock_service.disconnect_websocket(websocket, item_id)

@app.get("/api/v1/airlock/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "universal_airlock", "timestamp": datetime.now(timezone.utc).isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

