# Ideation Service Integration with Universal Airlock
# File: /services/ideation/ideation/airlock_integration.py

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import httpx
from pydantic import BaseModel
from enum import Enum

logger = logging.getLogger(__name__)

class CreativeContentType(str, Enum):
    CAMPAIGN_CONCEPT = "campaign_concept"
    CREATIVE_ASSET = "creative_asset"
    BRAND_STRATEGY = "brand_strategy"
    CONTENT_PLAN = "content_plan"
    DESIGN_BRIEF = "design_brief"
    MARKETING_COPY = "marketing_copy"

class IdeationAirlockIntegration:
    """Integration layer between Ideation Service and Universal Airlock"""
    
    def __init__(self, airlock_base_url: str = "http://airlock_system:8000"):
        self.airlock_base_url = airlock_base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def submit_creative_for_review(self,
                                       creative_content: Dict[str, Any],
                                       content_type: CreativeContentType,
                                       project_data: Dict[str, Any],
                                       created_by_agent_id: str = "ideation_agent",
                                       assigned_reviewer_id: Optional[str] = None,
                                       priority: str = "medium") -> str:
        """Submit creative content to airlock for review"""
        
        try:
            # Prepare airlock item data
            airlock_item = {
                "content_type": "creative_asset",
                "source_service": "ideation",
                "source_id": project_data.get("project_id", "unknown"),
                "title": f"{content_type.value.replace('_', ' ').title()} - {project_data.get('project_name', 'Creative Project')}",
                "description": f"Creative content for {project_data.get('project_name', 'project')}: {creative_content.get('description', 'No description')}",
                "content": {
                    "creative_content": creative_content,
                    "project_data": project_data,
                    "content_type": content_type.value,
                    "creation_timestamp": datetime.now(timezone.utc).isoformat(),
                    "creative_score": creative_content.get("creative_score", 0),
                    "brand_alignment": creative_content.get("brand_alignment", 0),
                    "target_audience_fit": creative_content.get("target_audience_fit", 0)
                },
                "metadata": {
                    "project_id": project_data.get("project_id"),
                    "project_name": project_data.get("project_name"),
                    "content_type": content_type.value,
                    "brand": project_data.get("brand", "Unknown"),
                    "target_audience": project_data.get("target_audience", []),
                    "campaign_objectives": project_data.get("objectives", []),
                    "creative_elements": list(creative_content.get("elements", {}).keys()),
                    "estimated_budget": project_data.get("budget", 0),
                    "timeline": project_data.get("timeline", {}),
                    "channels": project_data.get("channels", [])
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
                    f"Creative content submitted for review: {content_type.value.replace('_', ' ').title()}. "
                    f"Project: {project_data.get('project_name', 'Unknown')}. "
                    f"Creative Score: {creative_content.get('creative_score', 0)}%."
                )
                
                # Add creative brief summary
                await self._add_creative_summary(airlock_item_id, creative_content, project_data)
                
                logger.info(f"Successfully submitted creative content to airlock: {airlock_item_id}")
                return airlock_item_id
            else:
                logger.error(f"Failed to submit to airlock: {response.status_code} - {response.text}")
                raise Exception(f"Airlock submission failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error submitting creative content to airlock: {e}")
            raise
    
    async def submit_campaign_strategy_for_review(self,
                                                strategy_data: Dict[str, Any],
                                                campaign_data: Dict[str, Any],
                                                created_by_agent_id: str = "strategy_agent",
                                                assigned_reviewer_id: Optional[str] = None) -> str:
        """Submit campaign strategy to airlock for review"""
        
        try:
            airlock_item = {
                "content_type": "campaign",
                "source_service": "ideation",
                "source_id": campaign_data.get("campaign_id", "unknown"),
                "title": f"Campaign Strategy - {campaign_data.get('campaign_name', 'New Campaign')}",
                "description": f"Comprehensive campaign strategy for {campaign_data.get('brand', 'brand')}",
                "content": {
                    "strategy_data": strategy_data,
                    "campaign_data": campaign_data,
                    "creation_timestamp": datetime.now(timezone.utc).isoformat(),
                    "strategy_score": strategy_data.get("strategy_score", 0),
                    "market_fit": strategy_data.get("market_fit", 0),
                    "roi_projection": strategy_data.get("roi_projection", 0)
                },
                "metadata": {
                    "campaign_id": campaign_data.get("campaign_id"),
                    "campaign_name": campaign_data.get("campaign_name"),
                    "brand": campaign_data.get("brand"),
                    "budget": campaign_data.get("budget", 0),
                    "duration": campaign_data.get("duration", "Unknown"),
                    "target_markets": campaign_data.get("target_markets", []),
                    "key_messages": strategy_data.get("key_messages", []),
                    "success_metrics": strategy_data.get("success_metrics", []),
                    "risk_factors": strategy_data.get("risk_factors", [])
                },
                "priority": "high",  # Campaign strategies are typically high priority
                "assigned_reviewer_id": assigned_reviewer_id
            }
            
            response = await self.client.post(
                f"{self.airlock_base_url}/api/v1/airlock/items",
                json=airlock_item,
                params={"created_by_agent_id": created_by_agent_id}
            )
            
            if response.status_code == 200:
                result = response.json()
                airlock_item_id = result["item_id"]
                
                await self._add_system_message(
                    airlock_item_id,
                    f"Campaign strategy submitted for review. "
                    f"Projected ROI: {strategy_data.get('roi_projection', 0)}%. "
                    f"Budget: ${campaign_data.get('budget', 0):,}."
                )
                
                await self._add_strategy_summary(airlock_item_id, strategy_data, campaign_data)
                
                logger.info(f"Successfully submitted campaign strategy to airlock: {airlock_item_id}")
                return airlock_item_id
            else:
                logger.error(f"Failed to submit strategy to airlock: {response.status_code} - {response.text}")
                raise Exception(f"Airlock submission failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error submitting campaign strategy to airlock: {e}")
            raise
    
    async def handle_creative_feedback(self,
                                     airlock_item_id: str,
                                     feedback_data: Dict[str, Any],
                                     original_content: Dict[str, Any]) -> Dict[str, Any]:
        """Handle feedback and create revised creative content"""
        
        try:
            # Analyze feedback for creative improvements
            improvements_needed = self._analyze_creative_feedback(feedback_data)
            
            if improvements_needed:
                # Generate revised creative content
                revised_content = await self._revise_creative_content(
                    original_content, feedback_data, improvements_needed
                )
                
                # Submit revision to airlock
                changes_summary = self._generate_creative_changes_summary(feedback_data, improvements_needed)
                revision_id = await self.create_revision(
                    airlock_item_id=airlock_item_id,
                    updated_content=revised_content,
                    changes_summary=changes_summary,
                    created_by="ideation_agent"
                )
                
                return {
                    "revision_created": True,
                    "revision_id": revision_id,
                    "revised_content": revised_content,
                    "improvements_made": improvements_needed
                }
            else:
                return {
                    "revision_created": False,
                    "message": "No significant improvements needed based on feedback"
                }
                
        except Exception as e:
            logger.error(f"Error handling creative feedback: {e}")
            return {
                "revision_created": False,
                "error": str(e)
            }
    
    async def create_revision(self,
                            airlock_item_id: str,
                            updated_content: Dict[str, Any],
                            changes_summary: str,
                            created_by: str) -> str:
        """Create a new revision of creative content"""
        
        try:
            revision_data = {
                "content": {
                    "revised_content": updated_content,
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
                
                await self._add_system_message(
                    airlock_item_id,
                    f"Creative revision created by {created_by}: {changes_summary}"
                )
                
                logger.info(f"Successfully created creative revision {revision_id} for airlock item {airlock_item_id}")
                return revision_id
            else:
                logger.error(f"Failed to create revision: {response.status_code} - {response.text}")
                raise Exception(f"Revision creation failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error creating revision: {e}")
            raise
    
    async def _add_system_message(self, airlock_item_id: str, content: str):
        """Add a system message to the airlock item"""
        
        try:
            message_data = {
                "sender_type": "system",
                "sender_id": "ideation_system",
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
    
    async def _add_creative_summary(self, airlock_item_id: str, creative_content: Dict[str, Any], project_data: Dict[str, Any]):
        """Add a detailed creative summary message"""
        
        try:
            elements = creative_content.get("elements", {})
            
            summary = f"""Creative Brief Summary:
• Project: {project_data.get('project_name', 'Unknown')}
• Brand: {project_data.get('brand', 'Unknown')}
• Creative Score: {creative_content.get('creative_score', 0)}%
• Brand Alignment: {creative_content.get('brand_alignment', 0)}%
• Target Audience Fit: {creative_content.get('target_audience_fit', 0)}%

Creative Elements:"""
            
            for element_type, element_data in elements.items():
                summary += f"\n• {element_type.replace('_', ' ').title()}: {element_data.get('description', 'No description')}"
            
            if project_data.get("objectives"):
                summary += f"\n\nCampaign Objectives:"
                for obj in project_data["objectives"][:3]:
                    summary += f"\n• {obj}"
            
            await self._add_system_message(airlock_item_id, summary)
            
        except Exception as e:
            logger.warning(f"Failed to add creative summary: {e}")
    
    async def _add_strategy_summary(self, airlock_item_id: str, strategy_data: Dict[str, Any], campaign_data: Dict[str, Any]):
        """Add a detailed strategy summary message"""
        
        try:
            summary = f"""Campaign Strategy Summary:
• Campaign: {campaign_data.get('campaign_name', 'Unknown')}
• Budget: ${campaign_data.get('budget', 0):,}
• Duration: {campaign_data.get('duration', 'Unknown')}
• Projected ROI: {strategy_data.get('roi_projection', 0)}%
• Market Fit Score: {strategy_data.get('market_fit', 0)}%

Key Messages:"""
            
            for message in strategy_data.get("key_messages", [])[:3]:
                summary += f"\n• {message}"
            
            if strategy_data.get("success_metrics"):
                summary += f"\n\nSuccess Metrics:"
                for metric in strategy_data["success_metrics"][:3]:
                    summary += f"\n• {metric}"
            
            if strategy_data.get("risk_factors"):
                summary += f"\n\nRisk Factors:"
                for risk in strategy_data["risk_factors"][:3]:
                    summary += f"\n• {risk}"
            
            await self._add_system_message(airlock_item_id, summary)
            
        except Exception as e:
            logger.warning(f"Failed to add strategy summary: {e}")
    
    def _analyze_creative_feedback(self, feedback_data: Dict[str, Any]) -> List[str]:
        """Analyze feedback to determine what improvements are needed"""
        
        improvements = []
        feedback_type = feedback_data.get("feedback_type", "")
        feedback_content = feedback_data.get("feedback_data", {})
        
        if feedback_type == "suggestion":
            suggestion = feedback_content.get("suggestion", "")
            if "brand" in suggestion.lower():
                improvements.append("brand_alignment")
            if "audience" in suggestion.lower() or "target" in suggestion.lower():
                improvements.append("target_audience_fit")
            if "creative" in suggestion.lower() or "design" in suggestion.lower():
                improvements.append("creative_elements")
            if "message" in suggestion.lower() or "copy" in suggestion.lower():
                improvements.append("messaging")
        
        elif feedback_type == "rejection":
            # For rejections, assume comprehensive improvements needed
            improvements.extend(["brand_alignment", "creative_elements", "messaging"])
        
        return improvements
    
    async def _revise_creative_content(self,
                                     original_content: Dict[str, Any],
                                     feedback_data: Dict[str, Any],
                                     improvements_needed: List[str]) -> Dict[str, Any]:
        """Create revised creative content based on feedback"""
        
        revised_content = original_content.copy()
        revised_content["revision_timestamp"] = datetime.now(timezone.utc).isoformat()
        revised_content["revision_based_on_feedback"] = feedback_data
        
        # Apply improvements based on feedback
        for improvement in improvements_needed:
            if improvement == "brand_alignment":
                revised_content["brand_alignment"] = min(100, original_content.get("brand_alignment", 0) + 15)
            elif improvement == "target_audience_fit":
                revised_content["target_audience_fit"] = min(100, original_content.get("target_audience_fit", 0) + 10)
            elif improvement == "creative_elements":
                revised_content["creative_score"] = min(100, original_content.get("creative_score", 0) + 12)
        
        # Update overall creative score
        scores = [
            revised_content.get("brand_alignment", 0),
            revised_content.get("target_audience_fit", 0),
            revised_content.get("creative_score", 0)
        ]
        revised_content["overall_score"] = sum(scores) / len(scores)
        
        return revised_content
    
    def _generate_creative_changes_summary(self, feedback_data: Dict[str, Any], improvements_made: List[str]) -> str:
        """Generate a summary of creative changes made"""
        
        feedback_type = feedback_data.get("feedback_type", "unknown")
        
        if feedback_type == "suggestion":
            suggestion = feedback_data.get("feedback_data", {}).get("suggestion", "")
            return f"Incorporated creative suggestion: {suggestion}. Improved: {', '.join(improvements_made)}"
        elif feedback_type == "rejection":
            return f"Addressed rejection feedback with comprehensive creative improvements: {', '.join(improvements_made)}"
        else:
            return f"Made creative improvements based on reviewer feedback: {', '.join(improvements_made)}"
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# Enhanced Ideation Service with Airlock Integration
class EnhancedIdeationService:
    """Enhanced ideation service that integrates with the universal airlock"""
    
    def __init__(self, airlock_integration: IdeationAirlockIntegration):
        self.airlock = airlock_integration
        self.creative_cache = {}
    
    async def generate_and_submit_creative(self,
                                         project_brief: Dict[str, Any],
                                         content_type: CreativeContentType,
                                         assigned_reviewer_id: Optional[str] = None,
                                         auto_submit: bool = True) -> Dict[str, Any]:
        """Generate creative content and optionally submit to airlock for review"""
        
        # Generate the creative content (this would call your existing generation logic)
        creative_content = await self._generate_creative_content(project_brief, content_type)
        
        # Determine if automatic submission is appropriate
        should_submit = auto_submit and self._should_submit_for_review(creative_content)
        
        airlock_item_id = None
        if should_submit:
            try:
                # Determine priority based on project data
                priority = self._determine_priority(project_brief, creative_content)
                
                # Submit to airlock
                airlock_item_id = await self.airlock.submit_creative_for_review(
                    creative_content=creative_content,
                    content_type=content_type,
                    project_data=project_brief,
                    assigned_reviewer_id=assigned_reviewer_id,
                    priority=priority
                )
                
                # Cache the creative content for potential revisions
                self.creative_cache[airlock_item_id] = {
                    "creative_content": creative_content,
                    "project_brief": project_brief,
                    "content_type": content_type
                }
                
                # Update creative content with airlock information
                creative_content["airlock_item_id"] = airlock_item_id
                creative_content["submitted_for_review"] = True
                creative_content["review_status"] = "pending_review"
                
            except Exception as e:
                logger.error(f"Failed to submit creative for review: {e}")
                creative_content["airlock_submission_error"] = str(e)
                creative_content["submitted_for_review"] = False
        
        return creative_content
    
    async def generate_and_submit_campaign_strategy(self,
                                                  campaign_brief: Dict[str, Any],
                                                  assigned_reviewer_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate campaign strategy and submit to airlock for review"""
        
        # Generate the campaign strategy
        strategy_data = await self._generate_campaign_strategy(campaign_brief)
        
        try:
            # Submit to airlock
            airlock_item_id = await self.airlock.submit_campaign_strategy_for_review(
                strategy_data=strategy_data,
                campaign_data=campaign_brief,
                assigned_reviewer_id=assigned_reviewer_id
            )
            
            # Cache the strategy for potential revisions
            self.creative_cache[airlock_item_id] = {
                "strategy_data": strategy_data,
                "campaign_brief": campaign_brief,
                "content_type": "campaign_strategy"
            }
            
            strategy_data["airlock_item_id"] = airlock_item_id
            strategy_data["submitted_for_review"] = True
            strategy_data["review_status"] = "pending_review"
            
        except Exception as e:
            logger.error(f"Failed to submit strategy for review: {e}")
            strategy_data["airlock_submission_error"] = str(e)
            strategy_data["submitted_for_review"] = False
        
        return strategy_data
    
    async def _generate_creative_content(self, project_brief: Dict[str, Any], content_type: CreativeContentType) -> Dict[str, Any]:
        """Generate creative content based on project brief (placeholder for your existing logic)"""
        
        # This is where you'd call your existing creative generation logic
        # For now, returning a mock result
        return {
            "content_type": content_type.value,
            "creative_score": 88,
            "brand_alignment": 92,
            "target_audience_fit": 85,
            "elements": {
                "headline": {
                    "text": "Innovative Solutions for Tomorrow",
                    "description": "Primary headline for the campaign"
                },
                "visual_concept": {
                    "description": "Modern, clean design with bold typography",
                    "color_palette": ["#FF6B35", "#004E89", "#FFFFFF"]
                },
                "call_to_action": {
                    "text": "Discover More",
                    "placement": "Bottom right"
                }
            },
            "description": f"Creative {content_type.value} for {project_brief.get('project_name', 'project')}",
            "estimated_production_cost": 15000,
            "timeline": "2 weeks"
        }
    
    async def _generate_campaign_strategy(self, campaign_brief: Dict[str, Any]) -> Dict[str, Any]:
        """Generate campaign strategy based on brief (placeholder for your existing logic)"""
        
        return {
            "strategy_score": 91,
            "market_fit": 87,
            "roi_projection": 245,
            "key_messages": [
                "Innovation drives success",
                "Quality you can trust",
                "Solutions for the future"
            ],
            "target_segments": [
                "Tech-savvy professionals",
                "Early adopters",
                "Decision makers"
            ],
            "channel_strategy": {
                "digital": 60,
                "traditional": 25,
                "social": 15
            },
            "success_metrics": [
                "Brand awareness increase: 25%",
                "Lead generation: 1000+ qualified leads",
                "Conversion rate: 3.5%"
            ],
            "risk_factors": [
                "Market saturation",
                "Competitive response",
                "Economic downturn"
            ],
            "timeline": {
                "planning": "2 weeks",
                "execution": "8 weeks",
                "evaluation": "2 weeks"
            }
        }
    
    def _should_submit_for_review(self, creative_content: Dict[str, Any]) -> bool:
        """Determine if creative content should be submitted for human review"""
        
        creative_score = creative_content.get("creative_score", 0)
        brand_alignment = creative_content.get("brand_alignment", 0)
        
        # Submit for review if:
        # - Creative score is below 85% (needs human verification)
        # - Brand alignment is below 90%
        # - High-value projects (always need review)
        
        if creative_score < 85 or brand_alignment < 90:
            return True
        
        # Always submit high-value creative work for review
        estimated_cost = creative_content.get("estimated_production_cost", 0)
        if estimated_cost > 10000:
            return True
        
        return False
    
    def _determine_priority(self, project_brief: Dict[str, Any], creative_content: Dict[str, Any]) -> str:
        """Determine priority level based on project and creative data"""
        
        budget = project_brief.get("budget", 0)
        timeline = project_brief.get("timeline", {})
        creative_score = creative_content.get("creative_score", 0)
        
        # High priority for large budgets or tight timelines
        if budget > 100000:
            return "urgent"
        elif budget > 50000 or creative_score < 75:
            return "high"
        elif budget > 20000:
            return "medium"
        else:
            return "low"


# FastAPI endpoints for the enhanced ideation service
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Enhanced Ideation Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
airlock_integration = IdeationAirlockIntegration()
ideation_service = EnhancedIdeationService(airlock_integration)

@app.post("/api/v1/ideation/generate-creative")
async def generate_creative(
    project_brief: Dict[str, Any],
    content_type: CreativeContentType,
    assigned_reviewer_id: Optional[str] = None,
    auto_submit: bool = True
):
    """Generate creative content and optionally submit for review"""
    
    try:
        result = await ideation_service.generate_and_submit_creative(
            project_brief=project_brief,
            content_type=content_type,
            assigned_reviewer_id=assigned_reviewer_id,
            auto_submit=auto_submit
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in generate_creative: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/ideation/generate-campaign-strategy")
async def generate_campaign_strategy(
    campaign_brief: Dict[str, Any],
    assigned_reviewer_id: Optional[str] = None
):
    """Generate campaign strategy and submit for review"""
    
    try:
        result = await ideation_service.generate_and_submit_campaign_strategy(
            campaign_brief=campaign_brief,
            assigned_reviewer_id=assigned_reviewer_id
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in generate_campaign_strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/ideation/handle-feedback/{airlock_item_id}")
async def handle_creative_feedback(airlock_item_id: str, feedback_data: Dict[str, Any]):
    """Handle feedback from reviewers and create creative revisions if needed"""
    
    try:
        # Get cached creative content
        cached_data = ideation_service.creative_cache.get(airlock_item_id)
        if not cached_data:
            raise HTTPException(status_code=404, detail="Creative content not found in cache")
        
        result = await airlock_integration.handle_creative_feedback(
            airlock_item_id=airlock_item_id,
            feedback_data=feedback_data,
            original_content=cached_data
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error handling creative feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    await airlock_integration.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)

