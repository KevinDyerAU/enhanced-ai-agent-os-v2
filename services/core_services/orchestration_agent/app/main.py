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
import aiohttp

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

class TaskCompletion(BaseModel):
    result: str
    metadata: Optional[Dict[str, Any]] = {}

@app.post("/api/v1/tasks/{task_id}/complete")
async def complete_task(task_id: str, completion: TaskCompletion):
    """Mark a task as completed with results"""
    conn = await get_db_connection()
    try:
        await conn.execute("""
            UPDATE tasks 
            SET status = 'completed', 
                output_data = $1, 
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $2
        """, json.dumps({"result": completion.result, **completion.metadata}), task_id)
        
        task_row = await conn.fetchrow("""
            SELECT id, title, description, status, output_data, created_at, updated_at
            FROM tasks WHERE id = $1
        """, task_id)
        
        if not task_row:
            raise HTTPException(status_code=404, detail="Task not found")
        
        await store_task_memory(task_row)
        
        await publish_task_completion_event(task_row)
        
        return {
            "success": True,
            "task": dict(task_row),
            "message": "Task completed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await conn.close()

async def store_task_memory(task_row):
    """Store completed task in vector database for future reference"""
    try:
        data_architecture_url = os.getenv("DATA_ARCHITECTURE_URL", "http://data_architecture:8020")
        
        output_data = json.loads(task_row['output_data']) if isinstance(task_row['output_data'], str) else (task_row['output_data'] or {})
        task_summary = f"Task: {task_row['title']}\nDescription: {task_row['description']}\nResult: {output_data.get('result', 'No result')}"
        
        payload = {
            "content": task_summary,
            "metadata": {
                "task_id": task_row['id'],
                "title": task_row['title'],
                "status": task_row['status'],
                "created_at": task_row['created_at'].isoformat() if task_row['created_at'] else None,
                "completed_at": task_row['updated_at'].isoformat() if task_row['updated_at'] else None,
                "type": "completed_task"
            },
            "document_id": f"task_{task_row['id']}"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{data_architecture_url}/knowledge/store",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    logger.info(f"Successfully stored task {task_row['id']} in vector database")
                else:
                    logger.error(f"Failed to store task in vector database: {response.status}")
                    
    except Exception as e:
        logger.error(f"Error storing task memory: {str(e)}")

async def publish_task_completion_event(task_row):
    """Publish task completion event to Kafka"""
    try:
        data_architecture_url = os.getenv("DATA_ARCHITECTURE_URL", "http://data_architecture:8020")
        
        payload = {
            "topic": "task.completed",
            "event_type": "task_completed",
            "data": {
                "task_id": task_row['id'],
                "title": task_row['title'],
                "status": task_row['status'],
                "completed_at": task_row['updated_at'].isoformat() if task_row['updated_at'] else None
            },
            "metadata": {
                "source": "orchestration_agent",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{data_architecture_url}/events/publish",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    logger.info(f"Successfully published task completion event for {task_row['id']}")
                else:
                    logger.error(f"Failed to publish task completion event: {response.status}")
                    
    except Exception as e:
        logger.error(f"Error publishing task completion event: {str(e)}")

async def search_relevant_tasks(query: str, top_k: int = 3):
    """Search for relevant past tasks using vector similarity"""
    try:
        data_architecture_url = os.getenv("DATA_ARCHITECTURE_URL", "http://data_architecture:8020")
        
        payload = {
            "query": query,
            "top_k": top_k,
            "filter_metadata": {"type": "completed_task"}
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{data_architecture_url}/knowledge/search",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("results", [])
                else:
                    logger.error(f"Failed to search tasks: {response.status}")
                    return []
                    
    except Exception as e:
        logger.error(f"Error searching relevant tasks: {str(e)}")
        return []
