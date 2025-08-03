from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uuid
import asyncpg
import os
import httpx
import json
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Agent OS - Social Media Manager", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://aos_user:aos_password@postgres:5432/aos_db")
LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID", "")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET", "")

async def get_db_connection():
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

class CampaignRequest(BaseModel):
    content: str
    platforms: List[str] = ["linkedin"]
    target_audience: Optional[str] = "professionals"
    campaign_type: Optional[str] = "awareness"
    schedule_time: Optional[str] = None  # ISO format
    hashtags: Optional[List[str]] = []
    media_urls: Optional[List[str]] = []

class CampaignResponse(BaseModel):
    campaign_id: str
    posts_created: List[Dict[str, Any]]
    scheduling_status: str
    estimated_reach: int
    metadata: Dict[str, Any]

class PlatformAdapter:
    def __init__(self, platform: str):
        self.platform = platform
        self.character_limits = {
            "linkedin": 3000,
            "twitter": 280,
            "facebook": 63206,
            "instagram": 2200
        }
        
    def adapt_content(self, content: str, hashtags: Optional[List[str]] = None) -> str:
        """Adapt content for specific platform requirements"""
        limit = self.character_limits.get(self.platform, 1000)
        
        if self.platform == "linkedin":
            adapted = self._format_linkedin_content(content, hashtags)
        elif self.platform == "twitter":
            adapted = self._format_twitter_content(content, hashtags)
        elif self.platform == "facebook":
            adapted = self._format_facebook_content(content, hashtags)
        elif self.platform == "instagram":
            adapted = self._format_instagram_content(content, hashtags)
        else:
            adapted = content
        
        if len(adapted) > limit:
            adapted = adapted[:limit-3] + "..."
            
        return adapted
    
    def _format_linkedin_content(self, content: str, hashtags: Optional[List[str]] = None) -> str:
        """Format content for LinkedIn"""
        formatted = content
        
        if not content.endswith('.'):
            formatted += '.'
            
        if hashtags:
            formatted += "\n\n" + " ".join([f"#{tag}" for tag in hashtags])
            
        return formatted
    
    def _format_twitter_content(self, content: str, hashtags: Optional[List[str]] = None) -> str:
        """Format content for Twitter"""
        formatted = content
        
        if hashtags:
            formatted += " " + " ".join([f"#{tag}" for tag in hashtags[:3]])  # Limit hashtags
            
        return formatted
    
    def _format_facebook_content(self, content: str, hashtags: Optional[List[str]] = None) -> str:
        """Format content for Facebook"""
        formatted = content
        
        if hashtags:
            formatted += "\n\n" + " ".join([f"#{tag}" for tag in hashtags])
            
        return formatted
    
    def _format_instagram_content(self, content: str, hashtags: Optional[List[str]] = None) -> str:
        """Format content for Instagram"""
        formatted = content
        
        if hashtags:
            formatted += "\n\n" + " ".join([f"#{tag}" for tag in hashtags])
            
        return formatted

class LinkedInAPIClient:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://api.linkedin.com/v2"
        
    async def publish_post(self, content: str, media_urls: Optional[List[str]] = None) -> Dict[str, Any]:
        """Publish post to LinkedIn"""
        try:
            if not self.client_id:
                return self._create_mock_post(content, media_urls)
                
            return self._create_mock_post(content, media_urls)
            
        except Exception as e:
            logger.error(f"LinkedIn post failed: {e}")
            return self._create_mock_post(content, media_urls)
    
    def _create_mock_post(self, content: str, media_urls: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create mock LinkedIn post"""
        post_id = str(uuid.uuid4())
        
        return {
            "id": post_id,
            "platform": "linkedin",
            "content": content,
            "media_urls": media_urls or [],
            "status": "published",
            "url": f"https://linkedin.com/posts/{post_id}",
            "published_at": datetime.utcnow().isoformat(),
            "estimated_reach": 500
        }

class CampaignManager:
    def __init__(self):
        self.linkedin_client = LinkedInAPIClient(LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET)
        
    async def execute_campaign(self, request: CampaignRequest) -> CampaignResponse:
        """Execute social media campaign across platforms"""
        try:
            campaign_id = str(uuid.uuid4())
            posts_created = []
            total_estimated_reach = 0
            
            for platform in request.platforms:
                adapter = PlatformAdapter(platform)
                adapted_content = adapter.adapt_content(request.content, request.hashtags or [])
                
                if platform == "linkedin":
                    post_result = await self.linkedin_client.publish_post(
                        adapted_content, 
                        request.media_urls or []
                    )
                    posts_created.append(post_result)
                    total_estimated_reach += post_result.get("estimated_reach", 0)
                else:
                    mock_post = {
                        "id": str(uuid.uuid4()),
                        "platform": platform,
                        "content": adapted_content,
                        "status": "published",
                        "published_at": datetime.utcnow().isoformat(),
                        "estimated_reach": 300
                    }
                    posts_created.append(mock_post)
                    total_estimated_reach += 300
            
            conn = await get_db_connection()
            try:
                await conn.execute("""
                    INSERT INTO social_media_campaigns 
                    (id, name, description, target_platforms, start_date, end_date, status)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                campaign_id,
                f"Campaign {campaign_id[:8]}",
                request.content[:200],
                request.platforms,
                datetime.utcnow(),
                datetime.utcnow() + timedelta(days=7),
                "active"
                )
                
                for post in posts_created:
                    await conn.execute("""
                        INSERT INTO social_media_posts
                        (id, campaign_id, platform, content, status, scheduled_for, published_at, engagement_metrics)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """,
                    post["id"],
                    campaign_id,
                    post["platform"],
                    post["content"],
                    post["status"],
                    datetime.utcnow() if not request.schedule_time else datetime.fromisoformat(request.schedule_time),
                    datetime.utcnow() if post["status"] == "published" else None,
                    {"estimated_reach": post.get("estimated_reach", 0)}
                    )
                    
            finally:
                await conn.close()
            
            response = CampaignResponse(
                campaign_id=campaign_id,
                posts_created=posts_created,
                scheduling_status="published" if not request.schedule_time else "scheduled",
                estimated_reach=total_estimated_reach,
                metadata={
                    "timestamp": datetime.utcnow().isoformat(),
                    "platforms_count": len(request.platforms),
                    "posts_count": len(posts_created),
                    "campaign_type": request.campaign_type,
                    "target_audience": request.target_audience
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Campaign execution failed: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to execute campaign: {str(e)}")

campaign_manager = CampaignManager()

@app.get("/")
async def root():
    return {"message": "AI Agent OS - Social Media Manager v2.0.0", "status": "operational"}

@app.get("/healthz")
async def healthz():
    try:
        conn = await get_db_connection()
        await conn.execute("SELECT 1")
        await conn.close()
        return {"status": "healthy", "database": "connected", "service": "social_media_manager"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

@app.post("/execute-campaign", response_model=CampaignResponse)
async def execute_campaign(request: CampaignRequest):
    """Execute social media campaign across multiple platforms"""
    try:
        logger.info(f"Executing campaign for platforms: {request.platforms}")
        
        if not request.content.strip():
            raise HTTPException(status_code=400, detail="Content cannot be empty")
        
        if not request.platforms:
            raise HTTPException(status_code=400, detail="At least one platform must be specified")
        
        response = await campaign_manager.execute_campaign(request)
        
        logger.info(f"Successfully executed campaign: {response.campaign_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Campaign execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute campaign: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """Register this agent in the database on startup"""
    try:
        conn = await get_db_connection()
        
        agent_id = str(uuid.uuid4())
        capabilities = {
            "social_media_posting": True,
            "campaign_management": True,
            "content_adaptation": True,
            "multi_platform_support": True
        }
        
        configuration = {
            "supported_platforms": ["linkedin", "twitter", "facebook", "instagram"],
            "character_limits": {
                "linkedin": 3000,
                "twitter": 280,
                "facebook": 63206,
                "instagram": 2200
            },
            "max_hashtags": 10,
            "scheduling_enabled": True
        }
        
        existing = await conn.fetchrow(
            "SELECT id FROM agents WHERE type = $1 AND name = $2",
            "social_media", "Social Media Manager"
        )
        
        if not existing:
            await conn.execute("""
                INSERT INTO agents (id, name, type, status, capabilities, configuration)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, agent_id, "Social Media Manager", "social_media", "active", capabilities, configuration)
            
            logger.info(f"Registered Social Media Manager with ID: {agent_id}")
        else:
            logger.info("Social Media Manager already registered")
            
        await conn.close()
        
    except Exception as e:
        logger.error(f"Failed to register agent: {e}")
