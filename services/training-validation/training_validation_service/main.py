from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncpg
import os
import logging
import uuid
from datetime import datetime
import json
import tempfile
from integrations.web_intelligence_client import WebIntelligenceClient
from integrations.document_processing_client import DocumentProcessingClient
from validation_coordinator import run_validation_engines, generate_validation_report, create_validation_asset
from airlock_integration import AirlockIntegration
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AOS Training Validation Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

web_intelligence_client: Optional[WebIntelligenceClient] = None
document_processing_client: Optional[DocumentProcessingClient] = None
airlock_client: Optional[AirlockIntegration] = None

@app.on_event("startup")
async def startup_event():
    """Initialize integration clients on startup"""
    global web_intelligence_client, document_processing_client, airlock_client
    
    web_intelligence_url = os.getenv("WEB_INTELLIGENCE_URL", "http://web_intelligence_service:8032")
    document_engine_url = os.getenv("DOCUMENT_ENGINE_URL", "http://document_engine:8031")
    
    web_intelligence_client = WebIntelligenceClient(web_intelligence_url)
    document_processing_client = DocumentProcessingClient(document_engine_url)
    airlock_client = AirlockIntegration()
    
    logger.info("Training Validation Service initialized with integrations")

async def get_db_connection():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise HTTPException(status_code=500, detail="Database URL not configured")
    return await asyncpg.connect(database_url)

class TrainingUnitRequest(BaseModel):
    unit_code: str

class ValidationSessionCreate(BaseModel):
    name: str
    description: Optional[str] = None
    training_unit_id: str
    configuration: Optional[Dict[str, Any]] = {}
    created_by: str

class ValidationSessionResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    training_unit_id: str
    status: str
    configuration: Dict[str, Any]
    progress: Dict[str, Any]
    created_by: str
    created_at: datetime
    updated_at: datetime

class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size_bytes: int
    processing_status: str

class ValidationRequest(BaseModel):
    strictness_level: Optional[str] = "normal"
    reviewer_id: Optional[str] = "system"
    submit_for_review: Optional[bool] = True

class AirlockSubmissionRequest(BaseModel):
    asset_id: str
    reviewer_id: str
    priority: Optional[str] = "normal"

@app.get("/")
async def root():
    return {"message": "AOS Training Validation Service", "status": "operational"}

@app.get("/healthz")
async def health_check():
    try:
        conn = await get_db_connection()
        await conn.execute("SELECT 1")
        await conn.close()
        return {"status": "healthy", "service": "training_validation", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.post("/api/v1/training-units/retrieve")
async def retrieve_training_unit(request: TrainingUnitRequest):
    """Retrieve training unit data from training.gov.au via Web Intelligence Service"""
    try:
        conn = await get_db_connection()
        
        existing_unit = await conn.fetchrow(
            "SELECT * FROM training_units WHERE unit_code = $1",
            request.unit_code
        )
        
        if existing_unit:
            await conn.close()
            return {
                "id": str(existing_unit["id"]),
                "unit_code": existing_unit["unit_code"],
                "title": existing_unit["title"],
                "description": existing_unit["description"],
                "cached": True
            }
        
        if web_intelligence_client:
            scraped_data = await web_intelligence_client.scrape_training_unit(request.unit_code)
            if scraped_data:
                unit_id = await conn.fetchval(
                    """INSERT INTO training_units (unit_code, title, description, field, level, points, 
                       elements, performance_criteria, knowledge_evidence, performance_evidence, 
                       foundation_skills, assessment_conditions, raw_data, last_updated_from_source)
                       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, NOW()) RETURNING id""",
                    scraped_data["unit_code"], scraped_data["title"], scraped_data["description"],
                    scraped_data["field"], scraped_data["level"], scraped_data["points"],
                    json.dumps(scraped_data["elements"]), json.dumps(scraped_data["performance_criteria"]),
                    json.dumps(scraped_data["knowledge_evidence"]), json.dumps(scraped_data["performance_evidence"]),
                    json.dumps(scraped_data["foundation_skills"]), json.dumps(scraped_data["assessment_conditions"]),
                    json.dumps(scraped_data["raw_data"])
                )
                
                await conn.close()
                return {
                    "id": str(unit_id),
                    "unit_code": scraped_data["unit_code"],
                    "title": scraped_data["title"],
                    "description": scraped_data["description"],
                    "cached": False
                }
        
        await conn.close()
        raise HTTPException(status_code=404, detail=f"Training unit {request.unit_code} not found")
        
    except Exception as e:
        logger.error(f"Error retrieving training unit: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/validation-sessions", response_model=ValidationSessionResponse)
async def create_validation_session(session: ValidationSessionCreate):
    """Create a new validation session"""
    try:
        conn = await get_db_connection()
        
        session_id = await conn.fetchval(
            """INSERT INTO validation_sessions (name, description, training_unit_id, configuration, created_by)
               VALUES ($1, $2, $3, $4, $5) RETURNING id""",
            session.name,
            session.description,
            uuid.UUID(session.training_unit_id),
            json.dumps(session.configuration),
            session.created_by
        )
        
        created_session = await conn.fetchrow(
            "SELECT * FROM validation_sessions WHERE id = $1",
            session_id
        )
        
        await conn.close()
        
        return ValidationSessionResponse(
            id=str(created_session["id"]),
            name=created_session["name"],
            description=created_session["description"],
            training_unit_id=str(created_session["training_unit_id"]),
            status=created_session["status"],
            configuration=created_session["configuration"] or {},
            progress=created_session["progress"] or {},
            created_by=created_session["created_by"],
            created_at=created_session["created_at"],
            updated_at=created_session["updated_at"]
        )
        
    except Exception as e:
        logger.error(f"Error creating validation session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/validation-sessions")
async def list_validation_sessions(created_by: Optional[str] = None):
    """List validation sessions"""
    try:
        conn = await get_db_connection()
        
        if created_by:
            sessions = await conn.fetch(
                """SELECT vs.*, tu.unit_code, tu.title as unit_title
                   FROM validation_sessions vs
                   JOIN training_units tu ON vs.training_unit_id = tu.id
                   WHERE vs.created_by = $1
                   ORDER BY vs.created_at DESC""",
                created_by
            )
        else:
            sessions = await conn.fetch(
                """SELECT vs.*, tu.unit_code, tu.title as unit_title
                   FROM validation_sessions vs
                   JOIN training_units tu ON vs.training_unit_id = tu.id
                   ORDER BY vs.created_at DESC"""
            )
        
        await conn.close()
        
        return [
            {
                "id": str(session["id"]),
                "name": session["name"],
                "description": session["description"],
                "training_unit_id": str(session["training_unit_id"]),
                "unit_code": session["unit_code"],
                "unit_title": session["unit_title"],
                "status": session["status"],
                "configuration": session["configuration"] or {},
                "progress": session["progress"] or {},
                "created_by": session["created_by"],
                "created_at": session["created_at"],
                "updated_at": session["updated_at"]
            }
            for session in sessions
        ]
        
    except Exception as e:
        logger.error(f"Error listing validation sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/validation-sessions/{session_id}/documents", response_model=DocumentUploadResponse)
async def upload_document(session_id: str, file: UploadFile = File(...)):
    """Upload a document for validation"""
    try:
        conn = await get_db_connection()
        
        session = await conn.fetchrow(
            "SELECT id FROM validation_sessions WHERE id = $1",
            uuid.UUID(session_id)
        )
        
        if not session:
            await conn.close()
            raise HTTPException(status_code=404, detail="Validation session not found")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        processed_data = None
        if document_processing_client:
            processed_data = await document_processing_client.process_document(tmp_path, file.filename)
        
        document_id = await conn.fetchval(
            """INSERT INTO validation_documents 
               (session_id, filename, file_path, file_type, file_size_bytes, 
                content_extracted, metadata, processing_status, uploaded_by)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) RETURNING id""",
            uuid.UUID(session_id),
            file.filename,
            tmp_path,
            file.content_type or "application/octet-stream",
            len(content),
            processed_data.get("text_content") if processed_data else None,
            json.dumps(processed_data.get("metadata", {})) if processed_data else "{}",
            "completed" if processed_data else "failed",
            "system"
        )
        
        os.unlink(tmp_path)
        
        await conn.close()
        
        return DocumentUploadResponse(
            id=str(document_id),
            filename=file.filename,
            file_type=file.content_type or "application/octet-stream",
            file_size_bytes=len(content),
            processing_status="completed" if processed_data else "failed"
        )
        
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/validation-sessions/{session_id}/validate")
async def execute_validation(session_id: str, request: ValidationRequest = ValidationRequest()):
    """Execute validation for a session and create validation report as creative asset for airlock review"""
    try:
        conn = await get_db_connection()
        
        session = await conn.fetchrow(
            """SELECT vs.*, tu.unit_code, tu.title as unit_title, tu.elements, tu.performance_criteria,
                      tu.knowledge_evidence, tu.performance_evidence, tu.foundation_skills, tu.assessment_conditions
               FROM validation_sessions vs
               JOIN training_units tu ON vs.training_unit_id = tu.id
               WHERE vs.id = $1""",
            uuid.UUID(session_id)
        )
        
        if not session:
            await conn.close()
            raise HTTPException(status_code=404, detail="Validation session not found")
        
        await conn.execute(
            """UPDATE validation_sessions 
               SET status = 'in_progress', started_at = NOW(), updated_at = NOW()
               WHERE id = $1""",
            uuid.UUID(session_id)
        )
        
        documents = await conn.fetch(
            "SELECT * FROM validation_documents WHERE session_id = $1",
            uuid.UUID(session_id)
        )
        
        validation_results = await run_validation_engines(session, documents)
        
        result_id = await conn.fetchval(
            """INSERT INTO validation_results 
               (session_id, validation_type, status, score, findings, recommendations, validated_by)
               VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING id""",
            uuid.UUID(session_id),
            "comprehensive",
            "completed",
            validation_results["overall_score"],
            json.dumps(validation_results["findings"]),
            json.dumps(validation_results["recommendations"]),
            "system"
        )
        
        report_content = await generate_validation_report(session, validation_results)
        
        asset_id = await create_validation_asset(conn, session, report_content, result_id)
        
        airlock_response = None
        if request.submit_for_review and airlock_client:
            airlock_response = await airlock_client.submit_for_review(
                str(asset_id), 
                request.reviewer_id,
                "normal"
            )
        
        await conn.execute(
            """UPDATE validation_sessions 
               SET status = 'completed', completed_at = NOW(), updated_at = NOW()
               WHERE id = $1""",
            uuid.UUID(session_id)
        )
        
        await conn.close()
        
        response = {
            "session_id": session_id,
            "status": "completed",
            "result_id": str(result_id),
            "asset_id": str(asset_id),
            "message": "Validation completed successfully. Report created and ready for review.",
            "overall_score": validation_results["overall_score"],
            "findings_summary": validation_results["summary"]
        }
        
        if airlock_response:
            response["airlock_submission"] = airlock_response
        
        return response
        
    except Exception as e:
        logger.error(f"Error executing validation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/validation-sessions/{session_id}/results")
async def get_validation_results(session_id: str):
    """Get validation results for a session"""
    try:
        conn = await get_db_connection()
        
        results = await conn.fetch(
            """SELECT * FROM validation_results 
               WHERE session_id = $1 
               ORDER BY created_at DESC""",
            uuid.UUID(session_id)
        )
        
        await conn.close()
        
        return [
            {
                "id": str(result["id"]),
                "validation_type": result["validation_type"],
                "category": result["category"],
                "status": result["status"],
                "score": float(result["score"]) if result["score"] else None,
                "findings": result["findings"] or {},
                "evidence": result["evidence"] or {},
                "recommendations": result["recommendations"] or {},
                "created_at": result["created_at"]
            }
            for result in results
        ]
        
    except Exception as e:
        logger.error(f"Error getting validation results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/validation-reports/{asset_id}/submit-review")
async def submit_validation_report_for_review(asset_id: str, request: AirlockSubmissionRequest):
    """Submit a validation report for airlock review"""
    try:
        if not airlock_client:
            raise HTTPException(status_code=503, detail="Airlock integration not available")
        
        result = await airlock_client.submit_for_review(
            request.asset_id,
            request.reviewer_id,
            request.priority
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except Exception as e:
        logger.error(f"Error submitting validation report for review: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/validation-reports/{asset_id}/status")
async def get_validation_report_status(asset_id: str):
    """Get the airlock status of a validation report"""
    try:
        if not airlock_client:
            raise HTTPException(status_code=503, detail="Airlock integration not available")
        
        result = await airlock_client.get_asset_status(asset_id)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting validation report status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/validation-reports/pending")
async def get_pending_validation_reports():
    """Get all pending validation reports in the airlock system"""
    try:
        if not airlock_client:
            raise HTTPException(status_code=503, detail="Airlock integration not available")
        
        result = await airlock_client.get_pending_validation_reports()
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting pending validation reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8033)
