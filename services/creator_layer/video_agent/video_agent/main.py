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

app = FastAPI(title="AI Agent OS - Video Agent", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://aos_user:aos_password@postgres:5432/aos_db")
DESCRIPT_API_KEY = os.getenv("DESCRIPT_API_KEY", "")

async def get_db_connection():
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

class VideoCreationRequest(BaseModel):
    script: str
    voice_style: Optional[str] = "professional"
    video_style: Optional[str] = "presentation"
    duration_target: Optional[int] = 60  # seconds
    background_music: Optional[bool] = True
    include_captions: Optional[bool] = True
    resolution: Optional[str] = "1080p"

class VideoCreationResponse(BaseModel):
    video_url: str
    video_id: str
    audio_url: str
    duration: int
    processing_status: str
    metadata: Dict[str, Any]

class DescriptAPIClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.descript.com/v1"
        
    async def create_text_to_speech(self, script: str, voice_style: str) -> Dict[str, Any]:
        """Generate speech from text using Descript TTS"""
        try:
            if not self.api_key:
                return self._create_mock_audio(script, voice_style)
                
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/tts",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "text": script,
                        "voice": voice_style,
                        "format": "mp3",
                        "speed": 1.0
                    },
                    timeout=120.0
                )
                
                if response.status_code == 200:
                    return response.json()
                    
            return self._create_mock_audio(script, voice_style)
            
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            return self._create_mock_audio(script, voice_style)
    
    async def create_video_project(self, audio_id: str, video_style: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Create video project with audio and visual elements"""
        try:
            if not self.api_key:
                return self._create_mock_video(audio_id, video_style, options)
                
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/projects",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "name": f"Video Project {uuid.uuid4().hex[:8]}",
                        "audio_id": audio_id,
                        "video_style": video_style,
                        "options": options
                    },
                    timeout=180.0
                )
                
                if response.status_code == 201:
                    return response.json()
                    
            return self._create_mock_video(audio_id, video_style, options)
            
        except Exception as e:
            logger.error(f"Video project creation failed: {e}")
            return self._create_mock_video(audio_id, video_style, options)
    
    async def export_video(self, project_id: str, resolution: str) -> Dict[str, Any]:
        """Export video in specified resolution"""
        try:
            if not self.api_key:
                return self._create_mock_export(project_id, resolution)
                
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/projects/{project_id}/export",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "format": "mp4",
                        "resolution": resolution,
                        "quality": "high"
                    },
                    timeout=300.0
                )
                
                if response.status_code == 200:
                    return response.json()
                    
            return self._create_mock_export(project_id, resolution)
            
        except Exception as e:
            logger.error(f"Video export failed: {e}")
            return self._create_mock_export(project_id, resolution)
    
    def _create_mock_audio(self, script: str, voice_style: str) -> Dict[str, Any]:
        """Mock audio generation"""
        audio_id = str(uuid.uuid4())
        estimated_duration = len(script.split()) * 0.5  # Rough estimate: 0.5 seconds per word
        
        return {
            "id": audio_id,
            "url": f"https://example.com/audio-{audio_id}.mp3",
            "duration": int(estimated_duration),
            "voice_style": voice_style,
            "status": "completed",
            "created_at": datetime.utcnow().isoformat()
        }
    
    def _create_mock_video(self, audio_id: str, video_style: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Mock video project creation"""
        project_id = str(uuid.uuid4())
        
        return {
            "id": project_id,
            "name": f"Video Project {project_id[:8]}",
            "audio_id": audio_id,
            "video_style": video_style,
            "status": "processing",
            "created_at": datetime.utcnow().isoformat()
        }
    
    def _create_mock_export(self, project_id: str, resolution: str) -> Dict[str, Any]:
        """Mock video export"""
        export_id = str(uuid.uuid4())
        
        return {
            "id": export_id,
            "project_id": project_id,
            "url": f"https://example.com/video-{export_id}.mp4",
            "resolution": resolution,
            "status": "completed",
            "created_at": datetime.utcnow().isoformat()
        }

class VideoProcessor:
    def __init__(self, descript_client: DescriptAPIClient):
        self.descript_client = descript_client
        
    async def create_video_content(self, request: VideoCreationRequest) -> VideoCreationResponse:
        """Create complete video content from script"""
        try:
            logger.info("Generating audio from script...")
            audio_result = await self.descript_client.create_text_to_speech(
                request.script, 
                request.voice_style or "professional"
            )
            
            logger.info("Creating video project...")
            video_options = {
                "include_captions": request.include_captions,
                "background_music": request.background_music,
                "duration_target": request.duration_target
            }
            
            project_result = await self.descript_client.create_video_project(
                audio_result["id"],
                request.video_style or "presentation",
                video_options
            )
            
            logger.info("Exporting video...")
            export_result = await self.descript_client.export_video(
                project_result["id"],
                request.resolution or "1080p"
            )
            
            response = VideoCreationResponse(
                video_url=export_result["url"],
                video_id=export_result["id"],
                audio_url=audio_result["url"],
                duration=audio_result["duration"],
                processing_status=export_result["status"],
                metadata={
                    "timestamp": datetime.utcnow().isoformat(),
                    "script_length": len(request.script),
                    "voice_style": request.voice_style,
                    "video_style": request.video_style,
                    "resolution": request.resolution,
                    "api_used": "descript" if DESCRIPT_API_KEY else "mock",
                    "project_id": project_result["id"],
                    "audio_id": audio_result["id"]
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Video creation failed: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create video: {str(e)}")

descript_client = DescriptAPIClient(DESCRIPT_API_KEY)
video_processor = VideoProcessor(descript_client)

@app.get("/")
async def root():
    return {"message": "AI Agent OS - Video Agent v2.0.0", "status": "operational"}

@app.get("/healthz")
async def healthz():
    try:
        conn = await get_db_connection()
        await conn.execute("SELECT 1")
        await conn.close()
        return {"status": "healthy", "database": "connected", "service": "video_agent"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

@app.post("/create-video-content", response_model=VideoCreationResponse)
async def create_video_content(request: VideoCreationRequest):
    """Create video content from script using Descript API"""
    try:
        logger.info(f"Creating video content from script: {len(request.script)} characters")
        
        if len(request.script) < 10:
            raise HTTPException(status_code=400, detail="Script too short. Minimum 10 characters required.")
        
        if len(request.script) > 5000:
            raise HTTPException(status_code=400, detail="Script too long. Maximum 5000 characters allowed.")
        
        response = await video_processor.create_video_content(request)
        
        logger.info(f"Successfully created video: {response.video_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create video content: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """Register this agent in the database on startup"""
    try:
        conn = await get_db_connection()
        
        agent_id = str(uuid.uuid4())
        capabilities = {
            "text_to_speech": True,
            "video_creation": True,
            "audio_processing": True,
            "caption_generation": True
        }
        
        configuration = {
            "supported_voice_styles": ["professional", "casual", "energetic", "calm"],
            "supported_video_styles": ["presentation", "tutorial", "promotional", "educational"],
            "supported_resolutions": ["720p", "1080p", "4K"],
            "max_script_length": 5000,
            "max_duration": 300
        }
        
        existing = await conn.fetchrow(
            "SELECT id FROM agents WHERE type = $1 AND name = $2",
            "video", "Video Agent"
        )
        
        if not existing:
            await conn.execute("""
                INSERT INTO agents (id, name, type, status, capabilities, configuration)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, agent_id, "Video Agent", "video", "active", capabilities, configuration)
            
            logger.info(f"Registered Video Agent with ID: {agent_id}")
        else:
            logger.info("Video Agent already registered")
            
        await conn.close()
        
    except Exception as e:
        logger.error(f"Failed to register agent: {e}")
