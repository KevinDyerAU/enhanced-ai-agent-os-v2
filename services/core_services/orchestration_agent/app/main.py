from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uuid
import asyncpg
import os
from datetime import datetime
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Agent OS - Orchestration Service", version="2.0.0")

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://aos_user:aos_password@postgres:5432/aos_db")

async def get_db_connection():
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

class TaskRequest(BaseModel):
    title: str
    description: Optional[str] = None
    type: str
    priority: str = "medium"
    requester_id: str
    input_data: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}

class TaskResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    type: str
    status: str
    priority: str
    assigned_agent_id: Optional[str]
    requester_id: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

class AgentResponse(BaseModel):
    id: str
    name: str
    type: str
    status: str
    capabilities: Dict[str, Any]
    configuration: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

@app.get("/")
async def root():
    return {"message": "AI Agent OS - Orchestration Service v2.0.0", "status": "operational"}

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

@app.post("/api/v1/tasks", response_model=TaskResponse)
async def create_task(task_request: TaskRequest):
    conn = await get_db_connection()
    try:
        task_id = str(uuid.uuid4())
        
        query = """
            INSERT INTO tasks (id, title, description, type, status, priority, requester_id, input_data, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING *
        """
        
        row = await conn.fetchrow(
            query,
            task_id,
            task_request.title,
            task_request.description,
            task_request.type,
            "pending",
            task_request.priority,
            task_request.requester_id,
            json.dumps(task_request.input_data),
            json.dumps(task_request.metadata)
        )
        
        logger.info(f"Created task {task_id} of type {task_request.type}")
        
        return TaskResponse(
            id=str(row['id']),
            title=row['title'],
            description=row['description'],
            type=row['type'],
            status=row['status'],
            priority=row['priority'],
            assigned_agent_id=str(row['assigned_agent_id']) if row['assigned_agent_id'] else None,
            requester_id=row['requester_id'],
            input_data=json.loads(row['input_data']) if isinstance(row['input_data'], str) else row['input_data'],
            output_data=json.loads(row['output_data']) if isinstance(row['output_data'], str) else (row['output_data'] or {}),
            metadata=json.loads(row['metadata']) if isinstance(row['metadata'], str) else (row['metadata'] or {}),
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
        
    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")
    finally:
        await conn.close()

@app.get("/api/v1/tasks", response_model=List[TaskResponse])
async def get_tasks(status: Optional[str] = None, limit: int = 50):
    conn = await get_db_connection()
    try:
        if status:
            query = "SELECT * FROM tasks WHERE status = $1 ORDER BY created_at DESC LIMIT $2"
            rows = await conn.fetch(query, status, limit)
        else:
            query = "SELECT * FROM tasks ORDER BY created_at DESC LIMIT $1"
            rows = await conn.fetch(query, limit)
        
        tasks = []
        for row in rows:
            tasks.append(TaskResponse(
                id=str(row['id']),
                title=row['title'],
                description=row['description'],
                type=row['type'],
                status=row['status'],
                priority=row['priority'],
                assigned_agent_id=str(row['assigned_agent_id']) if row['assigned_agent_id'] else None,
                requester_id=row['requester_id'],
                input_data=json.loads(row['input_data']) if isinstance(row['input_data'], str) else row['input_data'],
                output_data=json.loads(row['output_data']) if isinstance(row['output_data'], str) else (row['output_data'] or {}),
                metadata=json.loads(row['metadata']) if isinstance(row['metadata'], str) else (row['metadata'] or {}),
                created_at=row['created_at'],
                updated_at=row['updated_at']
            ))
        
        return tasks
        
    except Exception as e:
        logger.error(f"Failed to get tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get tasks: {str(e)}")
    finally:
        await conn.close()

@app.get("/api/v1/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    conn = await get_db_connection()
    try:
        query = "SELECT * FROM tasks WHERE id = $1"
        row = await conn.fetchrow(query, task_id)
        
        if not row:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return TaskResponse(
            id=str(row['id']),
            title=row['title'],
            description=row['description'],
            type=row['type'],
            status=row['status'],
            priority=row['priority'],
            assigned_agent_id=str(row['assigned_agent_id']) if row['assigned_agent_id'] else None,
            requester_id=row['requester_id'],
            input_data=json.loads(row['input_data']) if isinstance(row['input_data'], str) else row['input_data'],
            output_data=json.loads(row['output_data']) if isinstance(row['output_data'], str) else (row['output_data'] or {}),
            metadata=json.loads(row['metadata']) if isinstance(row['metadata'], str) else (row['metadata'] or {}),
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get task: {str(e)}")
    finally:
        await conn.close()

@app.get("/api/v1/agents", response_model=List[AgentResponse])
async def get_agents():
    conn = await get_db_connection()
    try:
        query = "SELECT * FROM agents ORDER BY created_at DESC"
        rows = await conn.fetch(query)
        
        agents = []
        for row in rows:
            agents.append(AgentResponse(
                id=str(row['id']),
                name=row['name'],
                type=row['type'],
                status=row['status'],
                capabilities=row['capabilities'],
                configuration=row['configuration'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            ))
        
        return agents
        
    except Exception as e:
        logger.error(f"Failed to get agents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agents: {str(e)}")
    finally:
        await conn.close()
