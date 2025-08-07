"""
API package for the Training Validation Service.

This package contains all API routes and endpoints organized by feature.
"""
from fastapi import APIRouter

# Create main API router
api_router = APIRouter(prefix="/api/v1")

# Import and include all route modules here
# This will be populated by the individual route modules
