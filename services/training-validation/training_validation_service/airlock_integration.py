# Training Validation Service Integration with Universal Airlock
# File: /services/training_validation/training_validation/airlock_integration.py

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class AirlockIntegration:
    """Integration layer between Training Validation Service and Universal Airlock"""
    
    def __init__(self, airlock_base_url: str = "http://airlock_system:8000"):
        self.airlock_base_url = airlock_base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def submit_validation_for_review(self, 
                                         validation_results: Dict[str, Any],
                                         unit_data: Dict[str, Any],
                                         document_content: Dict[str, Any],
                                         created_by_agent_id: str = "training_validation_agent",
                                         assigned_reviewer_id: Optional[str] = None,
                                         priority: str = "medium") -> str:
        """Submit validation results to airlock for human review"""
        
        try:
            # Prepare airlock item data
            airlock_item = {
                "content_type": "training_validation",
                "source_service": "training_validation",
                "source_id": unit_data.get("unit_code", "unknown"),
                "title": f"Training Validation Report - {unit_data.get('unit_code', 'Unknown Unit')}",
                "description": f"Comprehensive validation report for {unit_data.get('unit_title', 'training unit')}",
                "content": {
                    "validation_results": validation_results,
                    "unit_data": unit_data,
                    "document_content": document_content,
                    "validation_timestamp": datetime.now(timezone.utc).isoformat(),
                    "overall_score": validation_results.get("overall_score", 0),
                    "status": validation_results.get("status", "unknown")
                },
                "metadata": {
                    "unit_code": unit_data.get("unit_code"),
                    "unit_title": unit_data.get("unit_title"),
                    "validation_engine_version": "1.0.0",
                    "document_pages": document_content.get("total_pages", 0),
                    "validation_categories": list(validation_results.get("validations", {}).keys()),
                    "generated_questions_count": len(validation_results.get("generated_questions", [])),
                    "compliance_percentage": validation_results.get("document_analysis", {}).get("compliance_percentage", 0)
                },
                "priority": priority,
                "assigned_reviewer_id": assigned_reviewer_id
            }
            
            # Submit to airlock
            response = await self.client.post(
                f"{self.airlock_base_url}/api/v1/airlock/items",
                json=airlock_item,
                params={"created_by_agent_id": created_by_agent_id}
            )
            
            if response.status_code == 200:
                result = response.json()
                airlock_item_id = result["item_id"]
                
                # Add initial system message
                await self._add_system_message(
                    airlock_item_id,
                    f"Training validation completed for {unit_data.get('unit_code', 'Unknown Unit')}. "
                    f"Overall score: {validation_results.get('overall_score', 0)}%. "
                    f"Status: {validation_results.get('status', 'unknown')}."
                )
                
                # Add detailed validation summary
                await self._add_validation_summary(airlock_item_id, validation_results)
                
                logger.info(f"Successfully submitted validation to airlock: {airlock_item_id}")
                return airlock_item_id
            else:
                logger.error(f"Failed to submit to airlock: {response.status_code} - {response.text}")
                raise Exception(f"Airlock submission failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error submitting validation to airlock: {e}")
            raise
    
    async def update_validation_status(self, 
                                     airlock_item_id: str,
                                     new_status: str,
                                     updated_by: str,
                                     feedback: Optional[str] = None) -> bool:
        """Update the status of a validation in the airlock"""
        
        try:
            update_data = {
                "status": new_status
            }
            
            response = await self.client.put(
                f"{self.airlock_base_url}/api/v1/airlock/items/{airlock_item_id}",
                json=update_data,
                params={"updated_by": updated_by}
            )
            
            if response.status_code == 200:
                # Add feedback message if provided
                if feedback:
                    await self._add_feedback_message(airlock_item_id, feedback, updated_by)
                
                logger.info(f"Successfully updated airlock item {airlock_item_id} status to {new_status}")
                return True
            else:
                logger.error(f"Failed to update airlock item: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating airlock item: {e}")
            return False
    
    async def create_revision(self,
                            airlock_item_id: str,
                            updated_validation_results: Dict[str, Any],
                            changes_summary: str,
                            created_by: str) -> str:
        """Create a new revision of the validation results"""
        
        try:
            revision_data = {
                "content": {
                    "validation_results": updated_validation_results,
                    "revision_timestamp": datetime.now(timezone.utc).isoformat()
                },
                "changes_summary": changes_summary,
                "created_by": created_by
            }
            
            response = await self.client.post(
                f"{self.airlock_base_url}/api/v1/airlock/items/{airlock_item_id}/revisions",
                json=revision_data
            )
            
            if response.status_code == 200:
                result = response.json()
                revision_id = result["revision_id"]
                
                # Add system message about revision
                await self._add_system_message(
                    airlock_item_id,
                    f"New revision created by {created_by}: {changes_summary}"
                )
                
                logger.info(f"Successfully created revision {revision_id} for airlock item {airlock_item_id}")
                return revision_id
            else:
                logger.error(f"Failed to create revision: {response.status_code} - {response.text}")
                raise Exception(f"Revision creation failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error creating revision: {e}")
            raise
    
    async def get_feedback_for_validation(self, airlock_item_id: str) -> List[Dict[str, Any]]:
        """Get all feedback for a validation"""
        
        try:
            response = await self.client.get(
                f"{self.airlock_base_url}/api/v1/airlock/items/{airlock_item_id}/feedback"
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get feedback: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting feedback: {e}")
            return []
    
    async def _add_system_message(self, airlock_item_id: str, content: str):
        """Add a system message to the airlock item"""
        
        try:
            message_data = {
                "sender_type": "system",
                "sender_id": "training_validation_system",
                "message_type": "system",
                "content": content,
                "metadata": {}
            }
            
            await self.client.post(
                f"{self.airlock_base_url}/api/v1/airlock/items/{airlock_item_id}/messages",
                json=message_data
            )
            
        except Exception as e:
            logger.warning(f"Failed to add system message: {e}")
    
    async def _add_feedback_message(self, airlock_item_id: str, feedback: str, provided_by: str):
        """Add a feedback message to the airlock item"""
        
        try:
            feedback_data = {
                "feedback_type": "comment",
                "feedback_data": {"comment": feedback},
                "provided_by": provided_by
            }
            
            await self.client.post(
                f"{self.airlock_base_url}/api/v1/airlock/items/{airlock_item_id}/feedback",
                json=feedback_data
            )
            
        except Exception as e:
            logger.warning(f"Failed to add feedback message: {e}")
    
    async def _add_validation_summary(self, airlock_item_id: str, validation_results: Dict[str, Any]):
        """Add a detailed validation summary message"""
        
        try:
            # Create summary of validation results
            validations = validation_results.get("validations", {})
            passed_count = sum(1 for v in validations.values() if v.get("status") == "passed")
            failed_count = sum(1 for v in validations.values() if v.get("status") == "failed")
            warning_count = sum(1 for v in validations.values() if v.get("status") == "warning")
            
            summary = f"""Validation Summary:
• Overall Score: {validation_results.get('overall_score', 0)}%
• Validations Passed: {passed_count}
• Validations Failed: {failed_count}
• Validations with Warnings: {warning_count}
• Generated Questions: {len(validation_results.get('generated_questions', []))}

Key Areas Requiring Attention:"""
            
            # Add specific gaps and recommendations
            for category, validation in validations.items():
                if validation.get("gaps"):
                    summary += f"\n\n{category.replace('_', ' ').title()}:"
                    for gap in validation["gaps"][:3]:  # Limit to first 3 gaps
                        summary += f"\n• {gap}"
            
            await self._add_system_message(airlock_item_id, summary)
            
        except Exception as e:
            logger.warning(f"Failed to add validation summary: {e}")
    
    async def submit_for_review(self, asset_id: str, reviewer_id: str, priority: str = "normal") -> Dict[str, Any]:
        """Submit an asset for review in the airlock system"""
        try:
            review_data = {
                "asset_id": asset_id,
                "reviewer_id": reviewer_id,
                "priority": priority,
                "submitted_at": datetime.now(timezone.utc).isoformat()
            }
            
            response = await self.client.post(
                f"{self.airlock_base_url}/api/v1/airlock/submit-for-review",
                json=review_data
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Successfully submitted asset {asset_id} for review")
                return {"success": True, "review_id": result.get("review_id")}
            else:
                logger.error(f"Failed to submit for review: {response.status_code} - {response.text}")
                return {"success": False, "error": f"Submission failed: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error submitting for review: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_asset_status(self, asset_id: str) -> Dict[str, Any]:
        """Get the status of an asset in the airlock system"""
        try:
            response = await self.client.get(
                f"{self.airlock_base_url}/api/v1/airlock/assets/{asset_id}/status"
            )
            
            if response.status_code == 200:
                result = response.json()
                return {"success": True, "status": result}
            else:
                logger.error(f"Failed to get asset status: {response.status_code} - {response.text}")
                return {"success": False, "error": f"Status retrieval failed: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error getting asset status: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_pending_validation_reports(self) -> Dict[str, Any]:
        """Get all pending validation reports from the airlock system"""
        try:
            response = await self.client.get(
                f"{self.airlock_base_url}/api/v1/airlock/pending-reports",
                params={"content_type": "training_validation"}
            )
            
            if response.status_code == 200:
                result = response.json()
                return {"success": True, "reports": result.get("reports", [])}
            else:
                logger.error(f"Failed to get pending reports: {response.status_code} - {response.text}")
                return {"success": False, "error": f"Reports retrieval failed: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error getting pending reports: {e}")
            return {"success": False, "error": str(e)}

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# Enhanced Training Validation Service with Airlock Integration
class EnhancedValidationService:
    """Enhanced validation service that integrates with the universal airlock"""
    
    def __init__(self, airlock_integration: AirlockIntegration):
        self.airlock = airlock_integration
        self.validation_cache = {}
    
    async def validate_and_submit_for_review(self,
                                           unit_data: Dict[str, Any],
                                           document_content: Dict[str, Any],
                                           assigned_reviewer_id: Optional[str] = None,
                                           auto_submit: bool = True) -> Dict[str, Any]:
        """Perform validation and optionally submit to airlock for review"""
        
        # Perform the actual validation (this would call your existing validation logic)
        validation_results = await self._perform_validation(unit_data, document_content)
        
        # Determine if automatic submission is appropriate
        should_submit = auto_submit and self._should_submit_for_review(validation_results)
        
        airlock_item_id = None
        if should_submit:
            try:
                # Determine priority based on validation results
                priority = self._determine_priority(validation_results)
                
                # Submit to airlock
                airlock_item_id = await self.airlock.submit_validation_for_review(
                    validation_results=validation_results,
                    unit_data=unit_data,
                    document_content=document_content,
                    assigned_reviewer_id=assigned_reviewer_id,
                    priority=priority
                )
                
                # Update validation results with airlock information
                validation_results["airlock_item_id"] = airlock_item_id
                validation_results["submitted_for_review"] = True
                validation_results["review_status"] = "pending_review"
                
            except Exception as e:
                logger.error(f"Failed to submit validation for review: {e}")
                validation_results["airlock_submission_error"] = str(e)
                validation_results["submitted_for_review"] = False
        
        return validation_results
    
    async def handle_feedback_and_revise(self,
                                       airlock_item_id: str,
                                       feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle feedback from reviewers and create revised validation if needed"""
        
        try:
            # Get the original validation data
            # (In a real implementation, you'd retrieve this from your database)
            original_validation = self.validation_cache.get(airlock_item_id)
            if not original_validation:
                raise Exception("Original validation data not found")
            
            # Analyze feedback and determine if revision is needed
            revision_needed = self._analyze_feedback_for_revision(feedback_data)
            
            if revision_needed:
                # Create revised validation based on feedback
                revised_validation = await self._create_revised_validation(
                    original_validation, feedback_data
                )
                
                # Submit revision to airlock
                changes_summary = self._generate_changes_summary(feedback_data)
                revision_id = await self.airlock.create_revision(
                    airlock_item_id=airlock_item_id,
                    updated_validation_results=revised_validation,
                    changes_summary=changes_summary,
                    created_by="training_validation_agent"
                )
                
                return {
                    "revision_created": True,
                    "revision_id": revision_id,
                    "revised_validation": revised_validation
                }
            else:
                return {
                    "revision_created": False,
                    "message": "No revision needed based on feedback"
                }
                
        except Exception as e:
            logger.error(f"Error handling feedback and revision: {e}")
            return {
                "revision_created": False,
                "error": str(e)
            }
    
    async def _perform_validation(self, unit_data: Dict[str, Any], document_content: Dict[str, Any]) -> Dict[str, Any]:
        """Perform the actual validation logic (placeholder for your existing validation)"""
        
        # This is where you'd call your existing validation logic
        # For now, returning a mock result
        return {
            "overall_score": 85,
            "status": "requires_changes",
            "validations": {
                "assessment_conditions": {
                    "status": "passed",
                    "score": 90,
                    "gaps": [],
                    "recommendations": ["Consider adding more specific workplace scenarios"]
                },
                "elements_performance_criteria": {
                    "status": "failed",
                    "score": 70,
                    "gaps": [
                        "Element 1.2 - Performance criteria not fully addressed",
                        "Element 2.1 - Missing specific assessment methods"
                    ],
                    "recommendations": [
                        "Add detailed assessment methods for each performance criteria",
                        "Ensure all elements are explicitly covered"
                    ]
                }
            },
            "generated_questions": [],
            "document_analysis": {
                "total_pages": 45,
                "compliance_percentage": 85
            }
        }
    
    def _should_submit_for_review(self, validation_results: Dict[str, Any]) -> bool:
        """Determine if validation should be submitted for human review"""
        
        overall_score = validation_results.get("overall_score", 0)
        status = validation_results.get("status", "unknown")
        
        # Submit for review if:
        # - Score is below 90% (needs human verification)
        # - Status indicates issues
        # - There are failed validations
        
        if overall_score < 90:
            return True
        
        if status in ["failed", "requires_changes"]:
            return True
        
        validations = validation_results.get("validations", {})
        if any(v.get("status") == "failed" for v in validations.values()):
            return True
        
        return False
    
    def _determine_priority(self, validation_results: Dict[str, Any]) -> str:
        """Determine priority level based on validation results"""
        
        overall_score = validation_results.get("overall_score", 0)
        
        if overall_score < 60:
            return "urgent"
        elif overall_score < 75:
            return "high"
        elif overall_score < 85:
            return "medium"
        else:
            return "low"
    
    def _analyze_feedback_for_revision(self, feedback_data: Dict[str, Any]) -> bool:
        """Analyze feedback to determine if a revision is needed"""
        
        feedback_type = feedback_data.get("feedback_type", "")
        
        # Revision needed for suggestions, rejections, or change requests
        return feedback_type in ["suggestion", "rejection", "improvement"]
    
    async def _create_revised_validation(self, 
                                       original_validation: Dict[str, Any],
                                       feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a revised validation based on feedback"""
        
        # This is where you'd implement logic to revise the validation
        # based on the specific feedback received
        
        revised_validation = original_validation.copy()
        revised_validation["revision_timestamp"] = datetime.now(timezone.utc).isoformat()
        revised_validation["revision_based_on_feedback"] = feedback_data
        
        # Apply specific improvements based on feedback
        # (This would be more sophisticated in a real implementation)
        
        return revised_validation
    
    def _generate_changes_summary(self, feedback_data: Dict[str, Any]) -> str:
        """Generate a summary of changes made based on feedback"""
        
        feedback_type = feedback_data.get("feedback_type", "unknown")
        
        if feedback_type == "suggestion":
            return f"Incorporated suggestion: {feedback_data.get('feedback_data', {}).get('suggestion', 'Improvements made')}"
        elif feedback_type == "rejection":
            return "Addressed rejection feedback and made necessary corrections"
        else:
            return "Made improvements based on reviewer feedback"


# FastAPI endpoints for the enhanced validation service
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Enhanced Training Validation Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
airlock_integration = AirlockIntegration()
validation_service = EnhancedValidationService(airlock_integration)

@app.post("/api/v1/validation/validate-and-submit")
async def validate_and_submit(
    unit_data: Dict[str, Any],
    document_content: Dict[str, Any],
    assigned_reviewer_id: Optional[str] = None,
    auto_submit: bool = True
):
    """Validate training unit and optionally submit for review"""
    
    try:
        result = await validation_service.validate_and_submit_for_review(
            unit_data=unit_data,
            document_content=document_content,
            assigned_reviewer_id=assigned_reviewer_id,
            auto_submit=auto_submit
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in validate_and_submit: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/validation/handle-feedback/{airlock_item_id}")
async def handle_feedback(airlock_item_id: str, feedback_data: Dict[str, Any]):
    """Handle feedback from reviewers and create revisions if needed"""
    
    try:
        result = await validation_service.handle_feedback_and_revise(
            airlock_item_id=airlock_item_id,
            feedback_data=feedback_data
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error handling feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/validation/feedback/{airlock_item_id}")
async def get_validation_feedback(airlock_item_id: str):
    """Get all feedback for a validation"""
    
    try:
        feedback = await airlock_integration.get_feedback_for_validation(airlock_item_id)
        return {"feedback": feedback}
        
    except Exception as e:
        logger.error(f"Error getting feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    await airlock_integration.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

