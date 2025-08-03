from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import tempfile
import os
import logging
from src.document_parser import DocumentParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AOS Document Processing Engine", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

parser = DocumentParser()

@app.get("/")
async def root():
    return {"message": "AOS Document Processing Engine", "status": "operational"}

@app.get("/healthz")
async def health_check():
    return {"status": "healthy", "service": "document_engine"}

@app.post("/parse")
async def parse_document_endpoint(file: UploadFile = File(...)):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
        
        parsed_data = await parser.parse_document(tmp_path)
        
        os.unlink(tmp_path)
        
        if parsed_data:
            return parsed_data
        raise HTTPException(status_code=400, detail="Failed to parse document.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
