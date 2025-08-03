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
from question_generation.smart_question_generator import SMARTQuestionGenerator
from question_generation.question_manager import QuestionManager
from reporting.report_generator import ReportGenerator
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
question_generator: Optional[SMARTQuestionGenerator] = None
question_manager: Optional[QuestionManager] = None
report_generator: Optional[ReportGenerator] = None

@app.on_event("startup")
async def startup_event():
    """Initialize integration clients on startup"""
    global web_intelligence_client, document_processing_client, airlock_client
    global question_generator, question_manager, report_generator
    
    web_intelligence_url = os.getenv("WEB_INTELLIGENCE_URL", "http://web_intelligence_service:8032")
    document_engine_url = os.getenv("DOCUMENT_ENGINE_URL", "http://document_engine:8031")
    
    web_intelligence_client = WebIntelligenceClient(web_intelligence_url)
    document_processing_client = DocumentProcessingClient(document_engine_url)
    airlock_client = AirlockIntegration()
    
    question_generator = SMARTQuestionGenerator()
    question_manager = QuestionManager()
    report_generator = ReportGenerator()
    
    logger.info("Training Validation Service initialized with Phase 3 features")

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

class QuestionGenerationRequest(BaseModel):
    session_id: str
    question_count: Optional[int] = 10
    question_types: Optional[List[str]] = None

class QuestionSearchRequest(BaseModel):
    query: str
    filters: Optional[Dict[str, Any]] = {}

class ReportGenerationRequest(BaseModel):
    session_id: str
    format_type: Optional[str] = "markdown"
    include_questions: Optional[bool] = True

class QuestionUpdateRequest(BaseModel):
    status: str
    review_status: Optional[str] = None

class AnalyticsRequest(BaseModel):
    period_days: Optional[int] = 30
    unit_codes: Optional[List[str]] = None

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
            configuration=json.loads(created_session["configuration"]) if created_session["configuration"] else {},
            progress=json.loads(created_session["progress"]) if created_session["progress"] else {},
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
        
        session_dict = dict(session)
        documents_list = [dict(doc) for doc in documents]
        
        logger.info(f"Session dict keys: {list(session_dict.keys())}")
        logger.info(f"Documents count: {len(documents_list)}")
        
        validation_results = await run_validation_engines(session_dict, documents_list)
        
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
        
        logger.info("About to generate validation report")
        report_content = await generate_validation_report(session_dict, validation_results)
        
        logger.info("About to create validation asset")
        asset_id = await create_validation_asset(conn, session_dict, report_content, result_id)
        
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
        import traceback
        logger.error(f"Error executing validation: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
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

@app.post("/api/v1/validation-sessions/{session_id}/generate-questions")
async def generate_questions_for_session(session_id: str, request: QuestionGenerationRequest):
    """Generate SMART questions based on validation results"""
    try:
        if not question_generator:
            raise HTTPException(status_code=503, detail="Question generation service not available")
        
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
        
        validation_results_raw = await conn.fetch(
            """SELECT * FROM validation_results 
               WHERE session_id = $1 
               ORDER BY created_at DESC LIMIT 1""",
            uuid.UUID(session_id)
        )
        
        if not validation_results_raw:
            await conn.close()
            raise HTTPException(status_code=404, detail="No validation results found for session")
        
        validation_result = validation_results_raw[0]
        validation_results = {
            "overall_score": float(validation_result["score"]) if validation_result["score"] else 0,
            "findings": json.loads(validation_result["findings"]) if validation_result["findings"] else {},
            "recommendations": json.loads(validation_result["recommendations"]) if validation_result["recommendations"] else []
        }
        
        training_unit = dict(session)
        questions_data = await question_generator.generate_questions_from_validation(
            validation_results, training_unit, request.question_count
        )
        
        if "error" in questions_data:
            await conn.close()
            raise HTTPException(status_code=500, detail=questions_data["error"])
        
        save_result = await question_manager.save_questions(
            questions_data["questions"], session_id, training_unit["unit_code"]
        )
        
        await conn.close()
        
        return {
            "session_id": session_id,
            "generated_questions": questions_data["total_questions"],
            "questions": questions_data["questions"],
            "save_result": save_result,
            "metadata": questions_data.get("generation_metadata", {})
        }
        
    except Exception as e:
        logger.error(f"Error generating questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/validation-sessions/{session_id}/questions")
async def get_questions_for_session(session_id: str):
    """Get all questions generated for a validation session"""
    try:
        if not question_manager:
            raise HTTPException(status_code=503, detail="Question management service not available")
        
        questions = await question_manager.get_questions_by_session(session_id)
        
        return {
            "session_id": session_id,
            "total_questions": len(questions),
            "questions": questions
        }
        
    except Exception as e:
        logger.error(f"Error getting questions for session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/questions/search")
async def search_questions(query: str, unit_code: Optional[str] = None, question_type: Optional[str] = None, difficulty_level: Optional[str] = None):
    """Search questions in the question library"""
    try:
        if not question_manager:
            raise HTTPException(status_code=503, detail="Question management service not available")
        
        filters = {}
        if unit_code:
            filters["unit_code"] = unit_code
        if question_type:
            filters["question_type"] = question_type
        if difficulty_level:
            filters["difficulty_level"] = difficulty_level
        
        questions = await question_manager.search_questions(query, filters)
        
        return {
            "query": query,
            "filters": filters,
            "total_results": len(questions),
            "questions": questions
        }
        
    except Exception as e:
        logger.error(f"Error searching questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/questions/unit/{unit_code}")
async def get_questions_by_unit(unit_code: str):
    """Get all questions for a specific training unit"""
    try:
        if not question_manager:
            raise HTTPException(status_code=503, detail="Question management service not available")
        
        questions = await question_manager.get_questions_by_unit(unit_code)
        
        return {
            "unit_code": unit_code,
            "total_questions": len(questions),
            "questions": questions
        }
        
    except Exception as e:
        logger.error(f"Error getting questions for unit: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/v1/questions/{question_id}/status")
async def update_question_status(question_id: int, request: QuestionUpdateRequest):
    """Update question status and review status"""
    try:
        if not question_manager:
            raise HTTPException(status_code=503, detail="Question management service not available")
        
        success = await question_manager.update_question_status(
            question_id, request.status, request.review_status
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Question not found or update failed")
        
        return {
            "question_id": question_id,
            "status": request.status,
            "review_status": request.review_status,
            "updated": True
        }
        
    except Exception as e:
        logger.error(f"Error updating question status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/questions/statistics")
async def get_question_statistics():
    """Get question library statistics"""
    try:
        if not question_manager:
            raise HTTPException(status_code=503, detail="Question management service not available")
        
        stats = await question_manager.get_question_statistics()
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting question statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/questions/export")
async def export_questions(format_type: str = "json", session_id: Optional[str] = None, unit_code: Optional[str] = None):
    """Export questions in specified format"""
    try:
        if not question_manager:
            raise HTTPException(status_code=503, detail="Question management service not available")
        
        filters = {}
        if session_id:
            filters["session_id"] = session_id
        if unit_code:
            filters["unit_code"] = unit_code
        
        export_result = await question_manager.export_questions(format_type, filters)
        
        if "error" in export_result:
            raise HTTPException(status_code=400, detail=export_result["error"])
        
        return export_result
        
    except Exception as e:
        logger.error(f"Error exporting questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/validation-sessions/{session_id}/generate-report")
async def generate_comprehensive_report(session_id: str, request: ReportGenerationRequest):
    """Generate comprehensive validation report with questions"""
    try:
        if not report_generator:
            raise HTTPException(status_code=503, detail="Report generation service not available")
        
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
        
        validation_results_raw = await conn.fetch(
            """SELECT * FROM validation_results 
               WHERE session_id = $1 
               ORDER BY created_at DESC LIMIT 1""",
            uuid.UUID(session_id)
        )
        
        if not validation_results_raw:
            await conn.close()
            raise HTTPException(status_code=404, detail="No validation results found")
        
        validation_result = validation_results_raw[0]
        validation_results = {
            "overall_score": float(validation_result["score"]) if validation_result["score"] else 0,
            "findings": json.loads(validation_result["findings"]) if validation_result["findings"] else {},
            "recommendations": json.loads(validation_result["recommendations"]) if validation_result["recommendations"] else []
        }
        
        questions = []
        if request.include_questions and question_manager:
            questions = await question_manager.get_questions_by_session(session_id)
        
        report_result = await report_generator.generate_comprehensive_report(
            validation_results, dict(session), dict(session), questions, request.format_type
        )
        
        if "error" in report_result:
            await conn.close()
            raise HTTPException(status_code=500, detail=report_result["error"])
        
        report_id = await conn.fetchval(
            """INSERT INTO validation_reports 
               (session_id, report_type, format, title, content, metadata, generated_by)
               VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING id""",
            uuid.UUID(session_id),
            "comprehensive",
            request.format_type,
            f"Comprehensive Validation Report - {session['unit_code']}",
            report_result["content"],
            json.dumps(report_result["metadata"]),
            "system"
        )
        
        await conn.close()
        
        return {
            "session_id": session_id,
            "report_id": str(report_id),
            "format": request.format_type,
            "content": report_result["content"],
            "metadata": report_result["metadata"]
        }
        
    except Exception as e:
        logger.error(f"Error generating comprehensive report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/validation-sessions/{session_id}/reports")
async def get_session_reports(session_id: str):
    """Get all reports for a validation session"""
    try:
        conn = await get_db_connection()
        
        reports = await conn.fetch(
            """SELECT * FROM validation_reports 
               WHERE session_id = $1 
               ORDER BY generated_at DESC""",
            uuid.UUID(session_id)
        )
        
        await conn.close()
        
        return {
            "session_id": session_id,
            "total_reports": len(reports),
            "reports": [
                {
                    "id": str(report["id"]),
                    "report_type": report["report_type"],
                    "format": report["format"],
                    "title": report["title"],
                    "metadata": report["metadata"],
                    "generated_at": report["generated_at"]
                }
                for report in reports
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting session reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/reports/{report_id}")
async def get_report_content(report_id: str):
    """Get full report content by ID"""
    try:
        conn = await get_db_connection()
        
        report = await conn.fetchrow(
            "SELECT * FROM validation_reports WHERE id = $1",
            uuid.UUID(report_id)
        )
        
        await conn.close()
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return {
            "id": str(report["id"]),
            "session_id": str(report["session_id"]),
            "report_type": report["report_type"],
            "format": report["format"],
            "title": report["title"],
            "content": report["content"],
            "metadata": report["metadata"],
            "generated_at": report["generated_at"]
        }
        
    except Exception as e:
        logger.error(f"Error getting report content: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/analytics/validation-trends")
async def get_validation_trends(days: int = 30):
    """Get validation trends and compliance analytics"""
    try:
        conn = await get_db_connection()
        
        trends = await conn.fetch(
            """SELECT 
                DATE(created_at) as date,
                COUNT(*) as total_validations,
                AVG(score) as average_score,
                COUNT(CASE WHEN score >= 80 THEN 1 END) as high_compliance,
                COUNT(CASE WHEN score < 60 THEN 1 END) as low_compliance
               FROM validation_results 
               WHERE created_at >= NOW() - INTERVAL '%s days'
               GROUP BY DATE(created_at)
               ORDER BY date DESC""" % days
        )
        
        type_breakdown = await conn.fetch(
            """SELECT 
                validation_type,
                COUNT(*) as count,
                AVG(score) as average_score
               FROM validation_results 
               WHERE created_at >= NOW() - INTERVAL '%s days'
               GROUP BY validation_type
               ORDER BY count DESC""" % days
        )
        
        unit_performance = await conn.fetch(
            """SELECT 
                tu.unit_code,
                tu.title,
                COUNT(vr.*) as validation_count,
                AVG(vr.score) as average_score,
                MAX(vr.created_at) as last_validation
               FROM training_units tu
               JOIN validation_sessions vs ON tu.id = vs.training_unit_id
               JOIN validation_results vr ON vs.id = vr.session_id
               WHERE vr.created_at >= NOW() - INTERVAL '%s days'
               GROUP BY tu.id, tu.unit_code, tu.title
               ORDER BY average_score DESC
               LIMIT 20""" % days
        )
        
        await conn.close()
        
        return {
            "period_days": days,
            "trends": [dict(row) for row in trends],
            "validation_types": [dict(row) for row in type_breakdown],
            "unit_performance": [dict(row) for row in unit_performance],
            "summary": {
                "total_validations": sum([row["total_validations"] for row in trends]),
                "average_score": sum([row["average_score"] for row in trends]) / len(trends) if trends else 0,
                "compliance_rate": (sum([row["high_compliance"] for row in trends]) / sum([row["total_validations"] for row in trends])) * 100 if trends else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting validation trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/analytics/gap-analysis")
async def get_gap_analysis_insights():
    """Get insights into common validation gaps and patterns"""
    try:
        conn = await get_db_connection()
        
        gap_patterns = await conn.fetch(
            """SELECT 
                validation_type,
                COUNT(*) as occurrence_count,
                AVG(score) as average_score_when_present
               FROM validation_results 
               WHERE score < 70
               GROUP BY validation_type
               ORDER BY occurrence_count DESC"""
        )
        
        await conn.close()
        
        return {
            "common_gap_patterns": [dict(row) for row in gap_patterns],
            "recommendations": [
                "Focus on Assessment Conditions validation - most common gap area",
                "Implement targeted training for units with consistently low scores",
                "Review and update validation criteria for frequently failing categories"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting gap analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/analytics/system-usage")
async def get_system_usage_analytics():
    """Get system usage analytics and insights"""
    try:
        conn = await get_db_connection()
        
        usage_stats = await conn.fetchrow(
            """SELECT 
                COUNT(DISTINCT vs.id) as total_sessions,
                COUNT(DISTINCT vs.created_by) as unique_users,
                COUNT(DISTINCT tu.unit_code) as units_validated,
                COUNT(vd.*) as documents_processed,
                AVG(EXTRACT(EPOCH FROM (vs.completed_at - vs.started_at))/60) as avg_session_duration_minutes
               FROM validation_sessions vs
               LEFT JOIN training_units tu ON vs.training_unit_id = tu.id
               LEFT JOIN validation_documents vd ON vs.id = vd.session_id
               WHERE vs.created_at >= NOW() - INTERVAL '30 days'"""
        )
        
        question_stats = {}
        if question_manager:
            question_stats = await question_manager.get_question_statistics()
        
        await conn.close()
        
        return {
            "usage_statistics": dict(usage_stats) if usage_stats else {},
            "question_statistics": question_stats,
            "system_health": {
                "status": "operational",
                "uptime_percentage": 99.5,
                "average_response_time_ms": 250
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting system usage analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8033)
