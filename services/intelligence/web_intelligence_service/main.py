from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict
import os
import logging
from src.firecrawl_client import FirecrawlClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScrapeRequest(BaseModel):
    url: str

app = FastAPI(title="AOS Web Intelligence Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    api_key = os.getenv("FIRECRAWL_API_KEY")
    app.state.firecrawl_client = FirecrawlClient(api_key=api_key)

@app.get("/")
async def root():
    return {"message": "AOS Web Intelligence Service", "status": "operational"}

@app.get("/healthz")
async def health_check():
    return {"status": "healthy", "service": "web_intelligence"}

@app.post("/scrape")
async def scrape_url_endpoint(request: ScrapeRequest) -> Dict:
    client: FirecrawlClient = app.state.firecrawl_client
    result = await client.scrape_url(request.url)
    if result is None:
        raise HTTPException(status_code=500, detail="Failed to scrape the URL.")
    return result
