from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Dict, Any
from ....services.validation_service import ValidationService, validation_service
from ....schemas.unit_schema import Unit
from ....schemas.document_schema import DocumentProcessingResult

router = APIRouter()

@router.post(
    "/validate",
    summary="Run Full Validation",
    description="Validates a processed document against the scraped data of a training unit."
)
async def run_validation(
    unit_data: Unit = Body(..., description="The scraped and parsed data for the training unit."),
    document_data: DocumentProcessingResult = Body(..., description="The processed document content."),
    val_service: ValidationService = Depends(lambda: validation_service)
) -> Dict[str, Any]:
    """
    This endpoint orchestrates the entire validation process.
    """
    try:
        results = val_service.validate_document(
            unit_data=unit_data,
            document_elements=document_data.elements
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during validation: {str(e)}")
