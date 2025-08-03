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

app = FastAPI(title="AI Agent OS - Ideation Agent", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://aos_user:aos_password@postgres:5432/aos_db")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

async def get_db_connection():
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

class IdeaGenerationRequest(BaseModel):
    topic: str
    target_audience: Optional[str] = "general"
    content_type: Optional[str] = "blog_post"
    industry: Optional[str] = "technology"
    tone: Optional[str] = "professional"
    count: Optional[int] = 5

class ContentIdea(BaseModel):
    title: str
    description: str
    key_points: List[str]
    target_audience: str
    estimated_engagement: str
    content_type: str
    trending_score: float

class IdeaGenerationResponse(BaseModel):
    ideas: List[ContentIdea]
    market_insights: Dict[str, Any]
    generation_metadata: Dict[str, Any]

class MarketIntelligenceEngine:
    def __init__(self):
        self.trending_topics = [
            "AI and Machine Learning",
            "Sustainable Technology",
            "Remote Work Solutions",
            "Digital Transformation",
            "Cybersecurity",
            "Cloud Computing",
            "Data Analytics",
            "IoT and Smart Devices"
        ]
        
    async def analyze_market_trends(self, topic: str, industry: str) -> Dict[str, Any]:
        """Analyze market trends for the given topic and industry"""
        try:
            market_data = {
                "trending_keywords": [
                    f"{topic} trends",
                    f"{industry} innovation",
                    f"{topic} best practices",
                    f"future of {topic}"
                ],
                "audience_interests": [
                    "How-to guides",
                    "Industry insights",
                    "Case studies",
                    "Expert interviews"
                ],
                "content_performance": {
                    "high_engagement_formats": ["video", "infographic", "interactive"],
                    "optimal_length": "1500-2500 words",
                    "best_posting_times": ["9-11 AM", "2-4 PM"]
                },
                "competitive_landscape": {
                    "content_gaps": [f"{topic} for beginners", f"{topic} case studies"],
                    "trending_angles": [f"Future of {topic}", f"{topic} ROI analysis"]
                }
            }
            
            return market_data
            
        except Exception as e:
            logger.error(f"Market analysis failed: {e}")
            return {"error": "Market analysis unavailable"}

class IdeationEngine:
    def __init__(self, openrouter_api_key: str):
        self.api_key = openrouter_api_key
        self.base_url = "https://openrouter.ai/api/v1"
        
    async def generate_content_ideas(self, request: IdeaGenerationRequest, market_data: Dict[str, Any], past_tasks_context: List[dict] = None) -> List[ContentIdea]:
        """Generate content ideas using OpenRouter LLM"""
        try:
            if not self.api_key:
                return self._generate_mock_ideas(request)
                
            prompt = self._build_ideation_prompt(request, market_data, past_tasks_context)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "anthropic/claude-3-haiku",
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 2000,
                        "temperature": 0.7
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    return self._parse_llm_response(content, request)
                else:
                    logger.error(f"OpenRouter API error: {response.status_code}")
                    return self._generate_mock_ideas(request)
                    
        except Exception as e:
            logger.error(f"LLM idea generation failed: {e}")
            return self._generate_mock_ideas(request)
    
    def _build_ideation_prompt(self, request: IdeaGenerationRequest, market_data: Dict[str, Any], past_tasks_context: List[dict] = None) -> str:
        """Build the prompt for LLM idea generation"""
        context_section = ""
        if past_tasks_context:
            context_section = "\n\nRelevant Past Tasks for Context:\n"
            for i, task in enumerate(past_tasks_context[:3], 1):
                context_section += f"{i}. {task.get('content', '')[:200]}...\n"
            context_section += "\nUse these past experiences to inform your ideas but create new, innovative concepts.\n"
        
        return f"""
        Generate {request.count} creative content ideas for the following requirements:
        
        Topic: {request.topic}
        Target Audience: {request.target_audience}
        Content Type: {request.content_type}
        Industry: {request.industry}
        Tone: {request.tone}
        
        Market Intelligence:
        - Trending Keywords: {', '.join(market_data.get('trending_keywords', []))}
        - Audience Interests: {', '.join(market_data.get('audience_interests', []))}
        - Content Gaps: {', '.join(market_data.get('competitive_landscape', {}).get('content_gaps', []))}
        {context_section}
        
        For each idea, provide:
        1. A compelling title
        2. A detailed description (2-3 sentences)
        3. 3-5 key points to cover
        4. Estimated engagement level (high/medium/low)
        5. Trending score (0.0-1.0)
        
        Format the response as JSON with the following structure:
        {{
            "ideas": [
                {{
                    "title": "...",
                    "description": "...",
                    "key_points": ["...", "...", "..."],
                    "estimated_engagement": "high",
                    "trending_score": 0.8
                }}
            ]
        }}
        """
    
    def _parse_llm_response(self, content: str, request: IdeaGenerationRequest) -> List[ContentIdea]:
        """Parse LLM response into ContentIdea objects"""
        try:
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            json_str = content[start_idx:end_idx]
            
            data = json.loads(json_str)
            ideas = []
            
            for idea_data in data.get("ideas", []):
                idea = ContentIdea(
                    title=idea_data.get("title", "Untitled"),
                    description=idea_data.get("description", "No description"),
                    key_points=idea_data.get("key_points", []),
                    target_audience=request.target_audience,
                    estimated_engagement=idea_data.get("estimated_engagement", "medium"),
                    content_type=request.content_type,
                    trending_score=idea_data.get("trending_score", 0.5)
                )
                ideas.append(idea)
                
            return ideas
            
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return self._generate_mock_ideas(request)
    
    def _generate_mock_ideas(self, request: IdeaGenerationRequest) -> List[ContentIdea]:
        """Generate mock ideas when LLM is unavailable"""
        mock_ideas = [
            ContentIdea(
                title=f"The Ultimate Guide to {request.topic}",
                description=f"A comprehensive guide covering everything you need to know about {request.topic}, from basics to advanced strategies.",
                key_points=[
                    f"Introduction to {request.topic}",
                    "Best practices and methodologies",
                    "Common challenges and solutions",
                    "Future trends and predictions"
                ],
                target_audience=request.target_audience,
                estimated_engagement="high",
                content_type=request.content_type,
                trending_score=0.8
            ),
            ContentIdea(
                title=f"5 Common {request.topic} Mistakes to Avoid",
                description=f"Learn from the most frequent pitfalls in {request.topic} and how to avoid them in your projects.",
                key_points=[
                    "Mistake #1: Poor planning",
                    "Mistake #2: Ignoring best practices",
                    "Mistake #3: Inadequate testing",
                    "How to prevent these issues"
                ],
                target_audience=request.target_audience,
                estimated_engagement="medium",
                content_type=request.content_type,
                trending_score=0.6
            ),
            ContentIdea(
                title=f"Case Study: Successful {request.topic} Implementation",
                description=f"Real-world example of how a company successfully implemented {request.topic} solutions.",
                key_points=[
                    "Company background and challenges",
                    "Solution approach and methodology",
                    "Results and ROI analysis",
                    "Lessons learned and recommendations"
                ],
                target_audience=request.target_audience,
                estimated_engagement="high",
                content_type=request.content_type,
                trending_score=0.7
            )
        ]
        
        return mock_ideas[:request.count]

market_engine = MarketIntelligenceEngine()
ideation_engine = IdeationEngine(OPENROUTER_API_KEY)

@app.get("/")
async def root():
    return {"message": "AI Agent OS - Ideation Agent v2.0.0", "status": "operational"}

@app.get("/healthz")
async def healthz():
    try:
        conn = await get_db_connection()
        await conn.execute("SELECT 1")
        await conn.close()
        return {"status": "healthy", "database": "connected", "service": "ideation_agent"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

@app.post("/generate-ideas", response_model=IdeaGenerationResponse)
async def generate_ideas(request: IdeaGenerationRequest):
    """Generate content ideas based on market intelligence and AI analysis"""
    try:
        logger.info(f"Generating ideas for topic: {request.topic}")
        
        market_data = await market_engine.analyze_market_trends(request.topic, request.industry or "technology")
        
        relevant_tasks = await search_relevant_tasks(
            f"{request.topic} {request.target_audience} {request.content_type}"
        )
        
        ideas = await ideation_engine.generate_content_ideas(request, market_data, relevant_tasks)
        
        response = IdeaGenerationResponse(
            ideas=ideas,
            market_insights=market_data,
            generation_metadata={
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": str(uuid.uuid4()),
                "model_used": "anthropic/claude-3-haiku" if OPENROUTER_API_KEY else "mock",
                "ideas_generated": len(ideas)
            }
        )
        
        logger.info(f"Successfully generated {len(ideas)} ideas")
        return response
        
    except Exception as e:
        logger.error(f"Idea generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate ideas: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """Register this agent in the database on startup"""
    try:
        conn = await get_db_connection()
        
        agent_id = str(uuid.uuid4())
        capabilities = {
            "content_ideation": True,
            "market_analysis": True,
            "trend_identification": True,
            "audience_targeting": True
        }
        
        configuration = {
            "supported_content_types": ["blog_post", "article", "social_media", "video_script"],
            "supported_industries": ["technology", "healthcare", "finance", "education", "retail"],
            "max_ideas_per_request": 10
        }
        
        existing = await conn.fetchrow(
            "SELECT id FROM agents WHERE type = $1 AND name = $2",
            "ideation", "Ideation Agent"
        )
        
        if not existing:
            await conn.execute("""
                INSERT INTO agents (id, name, type, status, capabilities, configuration)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, agent_id, "Ideation Agent", "ideation", "active", capabilities, configuration)
            
            logger.info(f"Registered Ideation Agent with ID: {agent_id}")
        else:
            logger.info("Ideation Agent already registered")
            
        await conn.close()
        
    except Exception as e:
        logger.error(f"Failed to register agent: {e}")

async def search_relevant_tasks(query: str, top_k: int = 3):
    """Search for relevant past tasks using vector similarity"""
    try:
        data_architecture_url = os.getenv("DATA_ARCHITECTURE_URL", "http://data_architecture:8020")
        
        payload = {
            "query": query,
            "top_k": top_k,
            "filter_metadata": {"type": "completed_task"}
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{data_architecture_url}/knowledge/search",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 200:
                result = response.json()
                return result.get("results", [])
            else:
                logger.error(f"Failed to search tasks: {response.status_code}")
                return []
                    
    except Exception as e:
        logger.error(f"Error searching relevant tasks: {str(e)}")
        return []
