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

app = FastAPI(title="Enterprise Compliance Engine", version="1.0.0")

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

class ValidationRequest(BaseModel):
    action_type: str
    entity_type: str
    entity_id: str
    actor_id: str
    action_data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = {}

class ValidationResponse(BaseModel):
    approved: bool
    validation_id: str
    violations: List[Dict[str, Any]]
    required_approvals: List[str]
    compliance_score: float
    recommendations: List[str]

class ComplianceRule:
    def __init__(self, rule_id: str, name: str, description: str, rule_type: str, severity: str):
        self.rule_id = rule_id
        self.name = name
        self.description = description
        self.rule_type = rule_type
        self.severity = severity

COMPLIANCE_RULES = [
    ComplianceRule(
        "external_post_approval",
        "External Post Approval Required",
        "No external posts without approval",
        "content_publishing",
        "high"
    ),
    ComplianceRule(
        "brand_guidelines",
        "Brand Guidelines Compliance",
        "All content must comply with brand guidelines",
        "brand_compliance",
        "medium"
    ),
    ComplianceRule(
        "content_policy",
        "Content Policy Validation",
        "Content must not violate organizational policies",
        "content_validation",
        "high"
    ),
    ComplianceRule(
        "data_privacy",
        "Data Privacy Protection",
        "Personal data must be handled according to privacy policies",
        "data_protection",
        "critical"
    ),
    ComplianceRule(
        "regulatory_compliance",
        "Regulatory Compliance Check",
        "Actions must comply with applicable regulations",
        "regulatory",
        "critical"
    )
]

async def validate_compliance_rules(request: ValidationRequest) -> List[Dict[str, Any]]:
    violations = []
    
    for rule in COMPLIANCE_RULES:
        violation = None
        
        if rule.rule_id == "external_post_approval":
            if request.action_type == "publish_content" and request.action_data.get("external", False):
                if not request.action_data.get("approved", False):
                    violation = {
                        "rule_id": rule.rule_id,
                        "rule_name": rule.name,
                        "severity": rule.severity,
                        "description": "External content publishing requires prior approval",
                        "recommendation": "Submit content for approval before publishing"
                    }
        
        elif rule.rule_id == "brand_guidelines":
            if request.action_type in ["create_content", "publish_content"]:
                brand_score = request.action_data.get("brand_compliance_score", 0.0)
                if brand_score < 0.8:
                    violation = {
                        "rule_id": rule.rule_id,
                        "rule_name": rule.name,
                        "severity": rule.severity,
                        "description": f"Brand compliance score {brand_score} below threshold 0.8",
                        "recommendation": "Review and adjust content to meet brand guidelines"
                    }
        
        elif rule.rule_id == "content_policy":
            if request.action_type in ["create_content", "publish_content"]:
                if request.action_data.get("contains_sensitive_content", False):
                    violation = {
                        "rule_id": rule.rule_id,
                        "rule_name": rule.name,
                        "severity": rule.severity,
                        "description": "Content contains sensitive material requiring review",
                        "recommendation": "Remove sensitive content or submit for manual review"
                    }
        
        elif rule.rule_id == "data_privacy":
            if request.action_data.get("contains_personal_data", False):
                if not request.action_data.get("privacy_consent", False):
                    violation = {
                        "rule_id": rule.rule_id,
                        "rule_name": rule.name,
                        "severity": rule.severity,
                        "description": "Personal data usage without proper consent",
                        "recommendation": "Obtain privacy consent before processing personal data"
                    }
        
        if violation:
            violations.append(violation)
    
    return violations

@app.get("/")
async def root():
    return {"message": "Enterprise Compliance Engine", "status": "operational"}

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

@app.post("/validate-action", response_model=ValidationResponse)
async def validate_action(request: ValidationRequest):
    conn = await get_db_connection()
    try:
        validation_id = str(uuid.uuid4())
        
        violations = await validate_compliance_rules(request)
        
        approved = len(violations) == 0
        
        compliance_score = 1.0
        if violations:
            critical_violations = sum(1 for v in violations if v["severity"] == "critical")
            high_violations = sum(1 for v in violations if v["severity"] == "high")
            medium_violations = sum(1 for v in violations if v["severity"] == "medium")
            
            compliance_score = max(0.0, 1.0 - (critical_violations * 0.5 + high_violations * 0.3 + medium_violations * 0.1))
        
        required_approvals = []
        if not approved:
            for violation in violations:
                if violation["severity"] in ["critical", "high"]:
                    required_approvals.append("senior_manager")
                elif violation["severity"] == "medium":
                    required_approvals.append("manager")
        
        recommendations = [v["recommendation"] for v in violations]
        
        query = """
            INSERT INTO compliance_validations (id, entity_type, entity_id, validation_type, status, score, findings, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """
        
        await conn.execute(
            query,
            validation_id,
            request.entity_type,
            request.entity_id,
            request.action_type,
            "approved" if approved else "rejected",
            compliance_score,
            json.dumps({"violations": violations, "recommendations": recommendations}),
            datetime.now()
        )
        
        logger.info(f"Validation {validation_id} completed: {'approved' if approved else 'rejected'} with score {compliance_score}")
        
        return ValidationResponse(
            approved=approved,
            validation_id=validation_id,
            violations=violations,
            required_approvals=list(set(required_approvals)),
            compliance_score=compliance_score,
            recommendations=recommendations
        )
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")
    finally:
        await conn.close()

@app.get("/rules")
async def get_compliance_rules():
    return {
        "rules": [
            {
                "rule_id": rule.rule_id,
                "name": rule.name,
                "description": rule.description,
                "rule_type": rule.rule_type,
                "severity": rule.severity
            }
            for rule in COMPLIANCE_RULES
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
