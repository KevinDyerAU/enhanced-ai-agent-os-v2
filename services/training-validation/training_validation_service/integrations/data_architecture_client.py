import httpx
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class DataArchitectureClient:
    """Client for integrating with Data Architecture service for vector store and document context."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        
    async def store_document_context(self, content: str, metadata: Dict[str, Any], document_id: Optional[str] = None) -> Optional[str]:
        """Store current document content in vector store for context retrieval"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/knowledge/store",
                    json={
                        "content": content,
                        "metadata": metadata,
                        "document_id": document_id
                    },
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("document_id")
                else:
                    logger.error(f"Failed to store document context: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error storing document context: {e}")
            return None
    
    async def search_similar_documents(self, query: str, unit_code: Optional[str] = None, top_k: int = 3) -> List[Dict[str, Any]]:
        """Search for similar current documents to provide additional validation context"""
        try:
            filter_metadata = {"content_type": "current_document"}
            if unit_code:
                filter_metadata["unit_code"] = unit_code
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/knowledge/search",
                    json={
                        "query": query,
                        "top_k": top_k,
                        "filter_metadata": filter_metadata
                    },
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("results", [])
                else:
                    logger.error(f"Failed to search similar documents: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error searching similar documents: {e}")
            return []

    async def clear_current_document_context(self, unit_code: str) -> bool:
        """Clear current document context for a specific unit to maintain only current data"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(
                    f"{self.base_url}/knowledge/clear",
                    json={
                        "filter_metadata": {
                            "content_type": "current_document",
                            "unit_code": unit_code
                        }
                    },
                    headers={"Content-Type": "application/json"}
                )
                
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Error clearing document context: {e}")
            return False
