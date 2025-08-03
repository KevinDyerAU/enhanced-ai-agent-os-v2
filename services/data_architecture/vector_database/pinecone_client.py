import os
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import aiohttp
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class VectorDocument:
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None

@dataclass
class SearchResult:
    document: VectorDocument
    score: float

class PineconeVectorClient:
    """
    Vector database client for storing and searching task memories using Pinecone.
    Provides semantic search capabilities for AI agents to learn from past experiences.
    """
    
    def __init__(self, api_key: str, environment: str, index_name: str = "task-memory"):
        self.api_key = api_key
        self.environment = environment
        self.index_name = index_name
        self.base_url = f"https://{index_name}-{environment}.svc.{environment}.pinecone.io"
        self.embedding_dimension = 1536  # OpenAI ada-002 embedding dimension
        
    async def _get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI API"""
        try:
            headers = {
                "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "input": text,
                "model": "text-embedding-ada-002"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.openai.com/v1/embeddings",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data["data"][0]["embedding"]
                    else:
                        logger.error(f"OpenAI API error: {response.status}")
                        return np.random.random(self.embedding_dimension).tolist()
                        
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return np.random.random(self.embedding_dimension).tolist()
    
    async def _pinecone_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make authenticated request to Pinecone API"""
        headers = {
            "Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, headers=headers, json=data) as response:
                    if response.status in [200, 201]:
                        return await response.json()
                    else:
                        logger.error(f"Pinecone API error: {response.status} - {await response.text()}")
                        return {"error": f"API error: {response.status}"}
        except Exception as e:
            logger.error(f"Pinecone request error: {str(e)}")
            return {"error": str(e)}
    
    async def store_document(self, document: VectorDocument) -> bool:
        """Store a document with its embedding in the vector database"""
        try:
            if not document.embedding:
                document.embedding = await self._get_embedding(document.content)
            
            vector_data = {
                "vectors": [{
                    "id": document.id,
                    "values": document.embedding,
                    "metadata": {
                        **document.metadata,
                        "content": document.content
                    }
                }]
            }
            
            result = await self._pinecone_request("POST", "/vectors/upsert", vector_data)
            
            if "error" not in result:
                logger.info(f"Successfully stored document {document.id}")
                return True
            else:
                logger.error(f"Failed to store document {document.id}: {result['error']}")
                return False
                
        except Exception as e:
            logger.error(f"Error storing document {document.id}: {str(e)}")
            return False
    
    async def search_similar(self, 
                           query: str, 
                           top_k: int = 5,
                           filter_metadata: Dict = None) -> List[SearchResult]:
        """Search for similar documents using semantic similarity"""
        try:
            query_embedding = await self._get_embedding(query)
            
            search_data = {
                "vector": query_embedding,
                "topK": top_k,
                "includeMetadata": True,
                "includeValues": False
            }
            
            if filter_metadata:
                search_data["filter"] = filter_metadata
            
            result = await self._pinecone_request("POST", "/query", search_data)
            
            if "error" in result:
                logger.error(f"Search error: {result['error']}")
                return []
            
            search_results = []
            for match in result.get("matches", []):
                metadata = match.get("metadata", {})
                content = metadata.pop("content", "")
                
                document = VectorDocument(
                    id=match["id"],
                    content=content,
                    metadata=metadata
                )
                
                search_results.append(SearchResult(
                    document=document,
                    score=match["score"]
                ))
            
            logger.info(f"Found {len(search_results)} similar documents for query")
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return []
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete a document from the vector database"""
        try:
            delete_data = {
                "ids": [document_id]
            }
            
            result = await self._pinecone_request("POST", "/vectors/delete", delete_data)
            
            if "error" not in result:
                logger.info(f"Successfully deleted document {document_id}")
                return True
            else:
                logger.error(f"Failed to delete document {document_id}: {result['error']}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {str(e)}")
            return False
    
    async def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector index"""
        try:
            result = await self._pinecone_request("GET", "/describe_index_stats")
            
            if "error" not in result:
                return result
            else:
                logger.error(f"Failed to get index stats: {result['error']}")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting index stats: {str(e)}")
            return {}
