"""
Sessions API endpoints for managing validation sessions.

This module provides RESTful endpoints for creating, retrieving, and listing
validation sessions used in the training validation service.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import constr, validator

# Import models and services
from models.validation_models import ValidationSession, ValidationSessionCreate, ValidationStatus
from services.session_service import SessionService
from services.exceptions import (
    SessionNotFoundError,
    InvalidSessionDataError,
    SessionCreationError
)

router = APIRouter(prefix="/sessions", tags=["Validation Sessions"])

# Constants
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Custom validators
def validate_session_id(session_id: str) -> str:
    """Validate session ID format."""
    try:
        UUID(session_id, version=4)
        return session_id
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID format. Must be a valid UUID v4."
        ) from e

def validate_status(status: Optional[str]) -> Optional[str]:
    """Validate status parameter."""
    if status and status not in ValidationStatus.__members__:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(ValidationStatus.__members__.keys())}"
        )
    return status

@router.post(
    "/",
    response_model=ValidationSession,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new validation session",
    response_description="The created validation session"
)
async def create_validation_session(
    session_data: ValidationSessionCreate,
    session_service: SessionService = Depends()
) -> ValidationSession:
    """
    Create a new validation session with the provided configuration.

    This endpoint initializes a new validation session with the specified
    parameters and returns the session details.

    Args:
        session_data: Configuration data for the new validation session
        session_service: Injected session service dependency

    Returns:
        ValidationSession: The newly created validation session

    Raises:
        HTTPException: 400 if input data is invalid
        HTTPException: 500 if there's an error creating the session
    """
    try:
        return await session_service.create_session(session_data)
    except InvalidSessionDataError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e
    except SessionCreationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create validation session"
        ) from e

@router.get(
    "/",
    response_model=List[ValidationSession],
    summary="List validation sessions",
    response_description="List of validation sessions matching the criteria"
)
async def list_validation_sessions(
    created_by: Optional[str] = Query(
        None,
        description="Filter sessions by creator's user ID"
    ),
    status: Optional[str] = Query(
        None,
        description=f"Filter sessions by status. Options: {', '.join(ValidationStatus.__members__.keys())}",
        regex=f"^({'|'.join(ValidationStatus.__members__.keys())})?$"
    ),
    page: int = Query(1, ge=1, description="Page number for pagination"),
    page_size: int = Query(
        DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
        description=f"Number of items per page (max: {MAX_PAGE_SIZE})"
    ),
    session_service: SessionService = Depends()
) -> List[ValidationSession]:
    """
    Retrieve a paginated list of validation sessions with optional filtering.

    This endpoint supports filtering by creator and status, and provides
    pagination controls for large result sets.

    Args:
        created_by: Filter sessions by the user who created them
        status: Filter sessions by status
        page: Page number for pagination (1-based)
        page_size: Number of items per page
        session_service: Injected session service dependency

    Returns:
        List[ValidationSession]: List of validation sessions matching the criteria
    """
    try:
        # Convert 1-based page to 0-based offset
        offset = (page - 1) * page_size
        return await session_service.list_sessions(
            created_by=created_by,
            status=status,
            limit=page_size,
            offset=offset
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sessions"
        ) from e

@router.get(
    "/{session_id}",
    response_model=ValidationSession,
    summary="Get session by ID",
    response_description="The requested validation session",
    responses={
        404: {"description": "Session not found"}
    }
)
async def get_validation_session(
    session_id: str = Depends(validate_session_id),
    session_service: SessionService = Depends()
) -> ValidationSession:
    """
    Retrieve a specific validation session by its unique identifier.

    Args:
        session_id: The unique identifier of the session to retrieve
        session_service: Injected session service dependency

    Returns:
        ValidationSession: The requested validation session

    Raises:
        HTTPException: 404 if no session exists with the given ID
    """
    try:
        session = await session_service.get_session(session_id)
        if not session:
            raise SessionNotFoundError(session_id)
        return session
    except SessionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve session"
        ) from e
