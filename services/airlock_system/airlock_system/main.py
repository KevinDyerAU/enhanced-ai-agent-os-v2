from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import asyncpg
import os
import uuid
from datetime import datetime
import logging
import httpx
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Airlock System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://aos_user:aos_password@postgres:5432/aos_db")
AUDIT_SERVICE_URL = os.getenv("AUDIT_SERVICE_URL", "http://audit_service:8006")

async def get_db_connection():
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

async def log_audit_event(event_type: str, entity_type: str, entity_id: str, actor_id: str, action: str, details: Dict[str, Any]):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AUDIT_SERVICE_URL}/log-event",
                json={
                    "event_type": event_type,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "actor_type": "user",
                    "actor_id": actor_id,
                    "action": action,
                    "details": details
                }
            )
            if response.status_code == 200:
                logger.info(f"Audit event logged: {action} on {entity_id}")
            else:
                logger.warning(f"Failed to log audit event: {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to log audit event: {e}")

class ReviewRequest(BaseModel):
    asset_id: str
    reviewer_id: str
    priority: str = "normal"
    metadata: Optional[Dict[str, Any]] = {}

class ApprovalRequest(BaseModel):
    reviewer_id: str
    comments: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}

class RejectionRequest(BaseModel):
    reviewer_id: str
    reason: str
    comments: Optional[str] = None
    required_changes: Optional[List[str]] = []
    metadata: Optional[Dict[str, Any]] = {}

class AssetResponse(BaseModel):
    id: str
    title: str
    type: str
    status: str
    content_url: Optional[str]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

class ReviewResponse(BaseModel):
    asset_id: str
    status: str
    message: str
    review_id: str

@app.get("/")
async def root():
    return {"message": "Airlock System", "status": "operational"}

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

@app.post("/request-review", response_model=ReviewResponse)
async def request_review(request: ReviewRequest):
    conn = await get_db_connection()
    try:
        check_query = "SELECT id, status FROM creative_assets WHERE id = $1"
        asset = await conn.fetchrow(check_query, request.asset_id)
        
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        if asset['status'] not in ['draft', 'rejected']:
            raise HTTPException(
                status_code=400, 
                detail=f"Asset cannot be submitted for review from status: {asset['status']}"
            )
        
        review_id = str(uuid.uuid4())
        
        update_query = """
            UPDATE creative_assets 
            SET status = 'pending_review', updated_at = $1 
            WHERE id = $2
        """
        
        await conn.execute(update_query, datetime.now(), request.asset_id)
        
        await log_audit_event(
            event_type="asset_review",
            entity_type="creative_asset",
            entity_id=request.asset_id,
            actor_id=request.reviewer_id,
            action="request_review",
            details={
                "previous_status": asset['status'],
                "new_status": "pending_review",
                "priority": request.priority,
                "metadata": request.metadata
            }
        )
        
        logger.info(f"Asset {request.asset_id} submitted for review by {request.reviewer_id}")
        
        return ReviewResponse(
            asset_id=request.asset_id,
            status="pending_review",
            message="Asset submitted for review successfully",
            review_id=review_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to request review: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to request review: {str(e)}")
    finally:
        await conn.close()

@app.post("/approve/{asset_id}", response_model=ReviewResponse)
async def approve_asset(asset_id: str, request: ApprovalRequest):
    conn = await get_db_connection()
    try:
        check_query = "SELECT id, status FROM creative_assets WHERE id = $1"
        asset = await conn.fetchrow(check_query, asset_id)
        
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        if asset['status'] != 'pending_review':
            raise HTTPException(
                status_code=400, 
                detail=f"Asset cannot be approved from status: {asset['status']}"
            )
        
        update_query = """
            UPDATE creative_assets 
            SET status = 'approved', updated_at = $1 
            WHERE id = $2
        """
        
        await conn.execute(update_query, datetime.now(), asset_id)
        
        await log_audit_event(
            event_type="asset_approval",
            entity_type="creative_asset",
            entity_id=asset_id,
            actor_id=request.reviewer_id,
            action="approve",
            details={
                "previous_status": asset['status'],
                "new_status": "approved",
                "comments": request.comments,
                "metadata": request.metadata
            }
        )
        
        logger.info(f"Asset {asset_id} approved by {request.reviewer_id}")
        
        return ReviewResponse(
            asset_id=asset_id,
            status="approved",
            message="Asset approved successfully",
            review_id=str(uuid.uuid4())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to approve asset: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to approve asset: {str(e)}")
    finally:
        await conn.close()

@app.post("/reject/{asset_id}", response_model=ReviewResponse)
async def reject_asset(asset_id: str, request: RejectionRequest):
    conn = await get_db_connection()
    try:
        check_query = "SELECT id, status FROM creative_assets WHERE id = $1"
        asset = await conn.fetchrow(check_query, asset_id)
        
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        if asset['status'] != 'pending_review':
            raise HTTPException(
                status_code=400, 
                detail=f"Asset cannot be rejected from status: {asset['status']}"
            )
        
        update_query = """
            UPDATE creative_assets 
            SET status = 'rejected', updated_at = $1 
            WHERE id = $2
        """
        
        await conn.execute(update_query, datetime.now(), asset_id)
        
        await log_audit_event(
            event_type="asset_rejection",
            entity_type="creative_asset",
            entity_id=asset_id,
            actor_id=request.reviewer_id,
            action="reject",
            details={
                "previous_status": asset['status'],
                "new_status": "rejected",
                "reason": request.reason,
                "comments": request.comments,
                "required_changes": request.required_changes,
                "metadata": request.metadata
            }
        )
        
        logger.info(f"Asset {asset_id} rejected by {request.reviewer_id}")
        
        return ReviewResponse(
            asset_id=asset_id,
            status="rejected",
            message="Asset rejected",
            review_id=str(uuid.uuid4())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reject asset: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reject asset: {str(e)}")
    finally:
        await conn.close()

@app.get("/assets/pending", response_model=List[AssetResponse])
async def get_pending_assets(limit: int = 50):
    conn = await get_db_connection()
    try:
        query = """
            SELECT id, title, type, status, content_url, metadata, created_at, updated_at
            FROM creative_assets 
            WHERE status = 'pending_review'
            ORDER BY created_at ASC
            LIMIT $1
        """
        
        rows = await conn.fetch(query, limit)
        
        assets = []
        for row in rows:
            assets.append(AssetResponse(
                id=str(row['id']),
                title=row['title'],
                type=row['type'],
                status=row['status'],
                content_url=row['content_url'],
                metadata=json.loads(row['metadata']) if isinstance(row['metadata'], str) else (row['metadata'] or {}),
                created_at=row['created_at'],
                updated_at=row['updated_at']
            ))
        
        return assets
        
    except Exception as e:
        logger.error(f"Failed to get pending assets: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get pending assets: {str(e)}")
    finally:
        await conn.close()

@app.get("/assets/{asset_id}", response_model=AssetResponse)
async def get_asset(asset_id: str):
    conn = await get_db_connection()
    try:
        query = """
            SELECT id, title, type, status, content_url, metadata, created_at, updated_at
            FROM creative_assets 
            WHERE id = $1
        """
        
        row = await conn.fetchrow(query, asset_id)
        
        if not row:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        return AssetResponse(
            id=str(row['id']),
            title=row['title'],
            type=row['type'],
            status=row['status'],
            content_url=row['content_url'],
            metadata=json.loads(row['metadata']) if isinstance(row['metadata'], str) else (row['metadata'] or {}),
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get asset: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get asset: {str(e)}")
    finally:
        await conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)
