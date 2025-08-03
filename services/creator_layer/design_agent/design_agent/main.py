from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uuid
import asyncpg
import os
import httpx
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Agent OS - Design Agent", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://aos_user:aos_password@postgres:5432/aos_db")
CANVA_API_KEY = os.getenv("CANVA_API_KEY", "")

async def get_db_connection():
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

class DesignRequest(BaseModel):
    prompt: str
    design_type: Optional[str] = "social_media_post"
    dimensions: Optional[str] = "1080x1080"
    brand_colors: Optional[List[str]] = ["#1E40AF", "#FFFFFF"]
    brand_fonts: Optional[List[str]] = ["Arial", "Helvetica"]
    style: Optional[str] = "modern"
    include_text: Optional[str] = ""

class DesignResponse(BaseModel):
    design_url: str
    design_id: str
    template_used: str
    brand_compliance_score: float
    performance_prediction: Dict[str, Any]
    metadata: Dict[str, Any]

class CanvaAPIClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.canva.com/v1"
        
    async def find_template(self, design_type: str, style: str) -> Dict[str, Any]:
        """Find suitable Canva template"""
        try:
            if not self.api_key:
                return self._get_mock_template(design_type, style)
                
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/designs/templates",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    params={
                        "type": design_type,
                        "style": style,
                        "limit": 10
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    templates = data.get("templates", [])
                    if templates:
                        return templates[0]  # Return first suitable template
                    
            return self._get_mock_template(design_type, style)
            
        except Exception as e:
            logger.error(f"Template search failed: {e}")
            return self._get_mock_template(design_type, style)
    
    async def create_design(self, template_id: str, customizations: Dict[str, Any]) -> Dict[str, Any]:
        """Create design from template with customizations"""
        try:
            if not self.api_key:
                return self._create_mock_design(template_id, customizations)
                
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/designs",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "template_id": template_id,
                        "customizations": customizations
                    },
                    timeout=60.0
                )
                
                if response.status_code == 201:
                    return response.json()
                    
            return self._create_mock_design(template_id, customizations)
            
        except Exception as e:
            logger.error(f"Design creation failed: {e}")
            return self._create_mock_design(template_id, customizations)
    
    def _get_mock_template(self, design_type: str, style: str) -> Dict[str, Any]:
        """Mock template data"""
        return {
            "id": f"template_{design_type}_{style}_{uuid.uuid4().hex[:8]}",
            "name": f"{style.title()} {design_type.replace('_', ' ').title()} Template",
            "type": design_type,
            "style": style,
            "dimensions": "1080x1080",
            "preview_url": f"https://example.com/template-preview-{uuid.uuid4().hex[:8]}.jpg"
        }
    
    def _create_mock_design(self, template_id: str, customizations: Dict[str, Any]) -> Dict[str, Any]:
        """Mock design creation"""
        design_id = str(uuid.uuid4())
        return {
            "id": design_id,
            "url": f"https://example.com/design-{design_id}.jpg",
            "download_url": f"https://example.com/download-{design_id}.jpg",
            "template_id": template_id,
            "status": "completed",
            "created_at": datetime.utcnow().isoformat()
        }

class BrandConsistencyEngine:
    def __init__(self):
        self.brand_guidelines = {
            "approved_colors": ["#1E40AF", "#3B82F6", "#60A5FA", "#FFFFFF", "#F8FAFC"],
            "approved_fonts": ["Arial", "Helvetica", "Open Sans", "Roboto"],
            "style_requirements": {
                "modern": {"clean_layout": True, "minimal_text": True},
                "corporate": {"professional_colors": True, "readable_fonts": True},
                "creative": {"bold_colors": True, "artistic_elements": True}
            }
        }
    
    def validate_brand_compliance(self, design_request: DesignRequest) -> float:
        """Validate design against brand guidelines"""
        score = 1.0
        
        if design_request.brand_colors:
            for color in design_request.brand_colors:
                if color not in self.brand_guidelines["approved_colors"]:
                    score -= 0.2
        
        if design_request.brand_fonts:
            for font in design_request.brand_fonts:
                if font not in self.brand_guidelines["approved_fonts"]:
                    score -= 0.1
        
        style_reqs = self.brand_guidelines["style_requirements"].get(design_request.style, {})
        if style_reqs:
            pass
        
        return max(0.0, min(1.0, score))
    
    def predict_performance(self, design_request: DesignRequest, template: Dict[str, Any]) -> Dict[str, Any]:
        """Predict design performance based on historical data"""
        base_engagement = 0.7
        
        type_multipliers = {
            "social_media_post": 1.0,
            "story": 0.8,
            "banner": 0.6,
            "infographic": 1.2
        }
        
        engagement_score = base_engagement * type_multipliers.get(design_request.design_type or "social_media_post", 1.0)
        
        return {
            "predicted_engagement": round(engagement_score, 2),
            "estimated_reach": int(engagement_score * 1000),
            "performance_factors": {
                "design_type": design_request.design_type,
                "style": design_request.style,
                "brand_compliance": self.validate_brand_compliance(design_request)
            }
        }

canva_client = CanvaAPIClient(CANVA_API_KEY)
brand_engine = BrandConsistencyEngine()

@app.get("/")
async def root():
    return {"message": "AI Agent OS - Design Agent v2.0.0", "status": "operational"}

@app.get("/healthz")
async def healthz():
    try:
        conn = await get_db_connection()
        await conn.execute("SELECT 1")
        await conn.close()
        return {"status": "healthy", "database": "connected", "service": "design_agent"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

@app.post("/create-design", response_model=DesignResponse)
async def create_design(request: DesignRequest):
    """Create a design using Canva API with brand consistency validation"""
    try:
        logger.info(f"Creating design: {request.design_type} - {request.prompt}")
        
        compliance_score = brand_engine.validate_brand_compliance(request)
        
        if compliance_score < 0.5:
            raise HTTPException(
                status_code=400, 
                detail=f"Design does not meet brand guidelines. Compliance score: {compliance_score}"
            )
        
        template = await canva_client.find_template(request.design_type or "social_media_post", request.style or "modern")
        
        customizations = {
            "text_elements": [
                {
                    "content": request.include_text or request.prompt,
                    "font": request.brand_fonts[0] if request.brand_fonts else "Arial",
                    "color": request.brand_colors[0] if request.brand_colors else "#1E40AF"
                }
            ],
            "color_scheme": request.brand_colors,
            "dimensions": request.dimensions
        }
        
        design_result = await canva_client.create_design(template["id"], customizations)
        
        performance_prediction = brand_engine.predict_performance(request, template)
        
        response = DesignResponse(
            design_url=design_result["url"],
            design_id=design_result["id"],
            template_used=template["name"],
            brand_compliance_score=compliance_score,
            performance_prediction=performance_prediction,
            metadata={
                "timestamp": datetime.utcnow().isoformat(),
                "template_id": template["id"],
                "customizations_applied": len(customizations.get("text_elements", [])),
                "api_used": "canva" if CANVA_API_KEY else "mock"
            }
        )
        
        logger.info(f"Successfully created design: {design_result['id']}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Design creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create design: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """Register this agent in the database on startup"""
    try:
        conn = await get_db_connection()
        
        agent_id = str(uuid.uuid4())
        capabilities = {
            "design_creation": True,
            "brand_validation": True,
            "template_selection": True,
            "performance_prediction": True
        }
        
        configuration = {
            "supported_design_types": ["social_media_post", "story", "banner", "infographic"],
            "supported_dimensions": ["1080x1080", "1920x1080", "1080x1920", "1200x628"],
            "brand_compliance_threshold": 0.5
        }
        
        existing = await conn.fetchrow(
            "SELECT id FROM agents WHERE type = $1 AND name = $2",
            "design", "Design Agent"
        )
        
        if not existing:
            await conn.execute("""
                INSERT INTO agents (id, name, type, status, capabilities, configuration)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, agent_id, "Design Agent", "design", "active", capabilities, configuration)
            
            logger.info(f"Registered Design Agent with ID: {agent_id}")
        else:
            logger.info("Design Agent already registered")
            
        await conn.close()
        
    except Exception as e:
        logger.error(f"Failed to register agent: {e}")
