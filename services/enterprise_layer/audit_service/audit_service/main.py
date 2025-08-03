from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import asyncpg
import os
import uuid
from datetime import datetime
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Enterprise Audit Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://aos_user:aos_password@postgres:5432/aos_db")

async def get_db_connection():
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

class AuditLogRequest(BaseModel):
    event_type: str
    entity_type: str
    entity_id: str
    actor_type: str
    actor_id: str
    action: str
    details: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = {}

class AuditLogResponse(BaseModel):
    id: str
    event_type: str
    entity_type: str
    entity_id: str
    actor_type: str
    actor_id: str
    action: str
    details: Dict[str, Any]
    timestamp: datetime
    session_id: Optional[str]

class AuditQueryRequest(BaseModel):
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    actor_id: Optional[str] = None
    event_type: Optional[str] = None
    action: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 100

@app.get("/")
async def root():
    return {"message": "Enterprise Audit Service", "status": "operational"}

@app.get("/healthz")
async def healthz():
    try:
        conn = await get_db_connection()
        await conn.execute("SELECT 1")
        await conn.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

@app.post("/log-event", response_model=AuditLogResponse)
async def log_event(request: AuditLogRequest):
    conn = await get_db_connection()
    try:
        audit_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        session_id = request.metadata.get("session_id") if request.metadata else None
        
        query = """
            INSERT INTO audit_logs (id, event_type, entity_type, entity_id, actor_type, actor_id, action, details, timestamp, session_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING *
        """
        
        row = await conn.fetchrow(
            query,
            audit_id,
            request.event_type,
            request.entity_type,
            request.entity_id,
            request.actor_type,
            request.actor_id,
            request.action,
            json.dumps(request.details),
            timestamp,
            session_id
        )
        
        logger.info(f"Audit log {audit_id} created: {request.event_type} - {request.action} by {request.actor_id}")
        
        return AuditLogResponse(
            id=str(row['id']),
            event_type=row['event_type'],
            entity_type=row['entity_type'],
            entity_id=str(row['entity_id']),
            actor_type=row['actor_type'],
            actor_id=row['actor_id'],
            action=row['action'],
            details=json.loads(row['details']) if isinstance(row['details'], str) else row['details'],
            timestamp=row['timestamp'],
            session_id=row['session_id']
        )
        
    except Exception as e:
        logger.error(f"Failed to log event: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to log event: {str(e)}")
    finally:
        await conn.close()

@app.post("/query-logs", response_model=List[AuditLogResponse])
async def query_audit_logs(request: AuditQueryRequest):
    conn = await get_db_connection()
    try:
        conditions = []
        params = []
        param_count = 0
        
        if request.entity_type:
            param_count += 1
            conditions.append(f"entity_type = ${param_count}")
            params.append(request.entity_type)
        
        if request.entity_id:
            param_count += 1
            conditions.append(f"entity_id = ${param_count}")
            params.append(request.entity_id)
        
        if request.actor_id:
            param_count += 1
            conditions.append(f"actor_id = ${param_count}")
            params.append(request.actor_id)
        
        if request.event_type:
            param_count += 1
            conditions.append(f"event_type = ${param_count}")
            params.append(request.event_type)
        
        if request.action:
            param_count += 1
            conditions.append(f"action = ${param_count}")
            params.append(request.action)
        
        if request.start_date:
            param_count += 1
            conditions.append(f"timestamp >= ${param_count}")
            params.append(request.start_date)
        
        if request.end_date:
            param_count += 1
            conditions.append(f"timestamp <= ${param_count}")
            params.append(request.end_date)
        
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        
        param_count += 1
        query = f"SELECT * FROM audit_logs{where_clause} ORDER BY timestamp DESC LIMIT ${param_count}"
        params.append(request.limit)
        
        rows = await conn.fetch(query, *params)
        
        audit_logs = []
        for row in rows:
            audit_logs.append(AuditLogResponse(
                id=str(row['id']),
                event_type=row['event_type'],
                entity_type=row['entity_type'],
                entity_id=str(row['entity_id']),
                actor_type=row['actor_type'],
                actor_id=row['actor_id'],
                action=row['action'],
                details=json.loads(row['details']) if isinstance(row['details'], str) else row['details'],
                timestamp=row['timestamp'],
                session_id=row['session_id']
            ))
        
        return audit_logs
        
    except Exception as e:
        logger.error(f"Failed to query audit logs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to query audit logs: {str(e)}")
    finally:
        await conn.close()

@app.get("/stats")
async def get_audit_stats():
    conn = await get_db_connection()
    try:
        stats_query = """
            SELECT 
                COUNT(*) as total_events,
                COUNT(DISTINCT entity_id) as unique_entities,
                COUNT(DISTINCT actor_id) as unique_actors,
                event_type,
                COUNT(*) as event_count
            FROM audit_logs 
            WHERE timestamp >= NOW() - INTERVAL '24 hours'
            GROUP BY event_type
            ORDER BY event_count DESC
        """
        
        rows = await conn.fetch(stats_query)
        
        total_query = "SELECT COUNT(*) as total FROM audit_logs WHERE timestamp >= NOW() - INTERVAL '24 hours'"
        total_row = await conn.fetchrow(total_query)
        
        event_types = []
        for row in rows:
            event_types.append({
                "event_type": row['event_type'],
                "count": row['event_count']
            })
        
        return {
            "last_24_hours": {
                "total_events": total_row['total'],
                "event_types": event_types
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get audit stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get audit stats: {str(e)}")
    finally:
        await conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
