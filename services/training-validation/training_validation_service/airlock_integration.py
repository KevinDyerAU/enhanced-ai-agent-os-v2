import logging
import httpx
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)

class AirlockIntegration:
    """Integration client for the Airlock System"""
    
    def __init__(self):
        self.airlock_url = os.getenv("AIRLOCK_URL", "http://airlock_system:8007")
    
    async def submit_for_review(self, asset_id: str, reviewer_id: str, priority: str = "normal") -> Dict[str, Any]:
        """Submit a validation report asset for airlock review"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.airlock_url}/request-review",
                    json={
                        "asset_id": asset_id,
                        "reviewer_id": reviewer_id,
                        "priority": priority,
                        "metadata": {
                            "source": "training_validation_service",
                            "asset_type": "validation_report"
                        }
                    },
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Successfully submitted asset {asset_id} for review")
                    return result
                else:
                    logger.error(f"Failed to submit asset for review: {response.status_code}")
                    return {"error": f"HTTP {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"Error submitting asset for review: {e}")
            return {"error": str(e)}
    
    async def get_asset_status(self, asset_id: str) -> Dict[str, Any]:
        """Get the current status of an asset in the airlock system"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.airlock_url}/assets/{asset_id}",
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Failed to get asset status: {response.status_code}")
                    return {"error": f"HTTP {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"Error getting asset status: {e}")
            return {"error": str(e)}
    
    async def get_pending_validation_reports(self) -> Dict[str, Any]:
        """Get all pending validation reports in the airlock system"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.airlock_url}/assets/pending",
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    assets = response.json()
                    validation_reports = [
                        asset for asset in assets 
                        if asset.get("type") == "validation_report"
                    ]
                    return {"validation_reports": validation_reports}
                else:
                    logger.error(f"Failed to get pending assets: {response.status_code}")
                    return {"error": f"HTTP {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"Error getting pending validation reports: {e}")
            return {"error": str(e)}
