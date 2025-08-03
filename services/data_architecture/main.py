import os
import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime

from vector_database.pinecone_client import PineconeVectorClient, VectorDocument, SearchResult
from streaming.kafka_manager import KafkaEventManager, StreamEvent
from governance.knowledge_graph import KnowledgeGraphManager, Entity, Relationship

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Enhanced AOS Data Architecture Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

vector_client: Optional[PineconeVectorClient] = None
kafka_manager: Optional[KafkaEventManager] = None
knowledge_graph: Optional[KnowledgeGraphManager] = None

class StoreDocumentRequest(BaseModel):
    content: str
    metadata: Dict[str, Any]
    document_id: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    filter_metadata: Optional[Dict[str, Any]] = None

class ComplianceValidationRequest(BaseModel):
    content: str
    content_type: str
    metadata: Dict[str, Any]

class EventPublishRequest(BaseModel):
    topic: str
    event_type: str
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global vector_client, kafka_manager, knowledge_graph
    
    try:
        pinecone_api_key = os.getenv("PINECONE_API_KEY")
        pinecone_environment = os.getenv("PINECONE_ENVIRONMENT", "us-east1-gcp")
        pinecone_index = os.getenv("PINECONE_INDEX_NAME", "task-memory")
        
        if pinecone_api_key:
            vector_client = PineconeVectorClient(
                api_key=pinecone_api_key,
                environment=pinecone_environment,
                index_name=pinecone_index
            )
            logger.info("Pinecone vector client initialized")
        else:
            logger.warning("PINECONE_API_KEY not found, vector search disabled")
        
        kafka_config = {
            'bootstrap_servers': os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092"),
            'topics': [
                {'name': 'task.completed'},
                {'name': 'asset.approved'},
                {'name': 'asset.rejected'},
                {'name': 'agent.activities'},
                {'name': 'system_errors'}
            ]
        }
        
        kafka_manager = KafkaEventManager(kafka_config)
        kafka_manager.start_consuming()
        logger.info("Kafka event manager initialized")
        
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            knowledge_graph = KnowledgeGraphManager(database_url)
            await knowledge_graph.initialize()
            logger.info("Knowledge graph manager initialized")
        else:
            logger.warning("DATABASE_URL not found, knowledge graph disabled")
            
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global kafka_manager, knowledge_graph
    
    if kafka_manager:
        kafka_manager.stop_consuming()
    
    if knowledge_graph:
        await knowledge_graph.close()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "vector_client": vector_client is not None,
            "kafka_manager": kafka_manager is not None,
            "knowledge_graph": knowledge_graph is not None
        }
    }

@app.post("/knowledge/store")
async def store_knowledge(request: StoreDocumentRequest):
    """Store a document in the vector database"""
    if not vector_client:
        raise HTTPException(status_code=503, detail="Vector client not available")
    
    try:
        document_id = request.document_id or f"doc_{datetime.utcnow().timestamp()}"
        
        document = VectorDocument(
            id=document_id,
            content=request.content,
            metadata=request.metadata
        )
        
        success = await vector_client.store_document(document)
        
        if success:
            if kafka_manager:
                event = await kafka_manager.create_event(
                    event_type="knowledge.stored",
                    source_service="data_architecture",
                    data={
                        "document_id": document_id,
                        "content_length": len(request.content),
                        "metadata": request.metadata
                    }
                )
                await kafka_manager.publish_event("agent.activities", event)
            
            return {
                "success": True,
                "document_id": document_id,
                "message": "Document stored successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to store document")
            
    except Exception as e:
        logger.error(f"Error storing knowledge: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/knowledge/search")
async def search_knowledge(request: SearchRequest):
    """Search for similar documents using semantic similarity"""
    if not vector_client:
        raise HTTPException(status_code=503, detail="Vector client not available")
    
    try:
        results = await vector_client.search_similar(
            query=request.query,
            top_k=request.top_k,
            filter_metadata=request.filter_metadata
        )
        
        formatted_results = []
        for result in results:
            formatted_results.append({
                "document_id": result.document.id,
                "content": result.document.content,
                "metadata": result.document.metadata,
                "similarity_score": result.score
            })
        
        if kafka_manager:
            event = await kafka_manager.create_event(
                event_type="knowledge.searched",
                source_service="data_architecture",
                data={
                    "query": request.query,
                    "results_count": len(results),
                    "top_k": request.top_k
                }
            )
            await kafka_manager.publish_event("agent.activities", event)
        
        return {
            "success": True,
            "query": request.query,
            "results": formatted_results,
            "total_results": len(formatted_results)
        }
        
    except Exception as e:
        logger.error(f"Error searching knowledge: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/compliance/validate-processing")
async def validate_compliance(request: ComplianceValidationRequest):
    """Validate content for compliance requirements"""
    try:
        validation_results = {
            "compliant": True,
            "violations": [],
            "recommendations": []
        }
        
        sensitive_patterns = ["password", "api_key", "secret", "token"]
        content_lower = request.content.lower()
        
        for pattern in sensitive_patterns:
            if pattern in content_lower:
                validation_results["violations"].append({
                    "type": "sensitive_information",
                    "pattern": pattern,
                    "severity": "high"
                })
                validation_results["compliant"] = False
        
        if len(request.content) > 10000:
            validation_results["recommendations"].append({
                "type": "content_length",
                "message": "Content is very long, consider summarizing"
            })
        
        if kafka_manager:
            event = await kafka_manager.create_event(
                event_type="compliance.validated",
                source_service="data_architecture",
                data={
                    "content_type": request.content_type,
                    "compliant": validation_results["compliant"],
                    "violations_count": len(validation_results["violations"])
                }
            )
            await kafka_manager.publish_event("agent.activities", event)
        
        return {
            "success": True,
            "validation_results": validation_results
        }
        
    except Exception as e:
        logger.error(f"Error validating compliance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/compliance/report/{framework}")
async def get_compliance_report(framework: str):
    """Get compliance report for a specific framework"""
    try:
        report = {
            "framework": framework,
            "compliance_score": 85.5,
            "last_assessment": datetime.utcnow().isoformat(),
            "areas": {
                "data_protection": {"score": 90, "status": "compliant"},
                "access_control": {"score": 85, "status": "compliant"},
                "audit_logging": {"score": 80, "status": "needs_improvement"}
            },
            "recommendations": [
                "Implement additional access controls for sensitive data",
                "Enhance audit logging for all data operations"
            ]
        }
        
        return {
            "success": True,
            "report": report
        }
        
    except Exception as e:
        logger.error(f"Error generating compliance report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/events/publish")
async def publish_event(request: EventPublishRequest):
    """Publish an event to Kafka"""
    if not kafka_manager:
        raise HTTPException(status_code=503, detail="Kafka manager not available")
    
    try:
        event = await kafka_manager.create_event(
            event_type=request.event_type,
            source_service="data_architecture",
            data=request.data,
            metadata=request.metadata
        )
        
        success = await kafka_manager.publish_event(request.topic, event)
        
        if success:
            return {
                "success": True,
                "event_id": event.event_id,
                "message": f"Event published to topic {request.topic}"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to publish event")
            
    except Exception as e:
        logger.error(f"Error publishing event: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/events/topics")
async def get_topic_info():
    """Get information about Kafka topics"""
    if not kafka_manager:
        raise HTTPException(status_code=503, detail="Kafka manager not available")
    
    return {
        "success": True,
        "topic_info": kafka_manager.get_topic_info()
    }

@app.get("/vector/stats")
async def get_vector_stats():
    """Get vector database statistics"""
    if not vector_client:
        raise HTTPException(status_code=503, detail="Vector client not available")
    
    try:
        stats = await vector_client.get_index_stats()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error getting vector stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8020)
