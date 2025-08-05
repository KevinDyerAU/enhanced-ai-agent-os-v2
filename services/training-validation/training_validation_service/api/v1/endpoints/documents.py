from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from ....schemas.document_schema import DocumentProcessingResult, DocumentMetadata
from ....services.document_service import DocumentService, document_service

router = APIRouter()

@router.post(
    "/upload",
    response_model=DocumentProcessingResult,
    summary="Upload and Process a Document",
    description="Uploads a single document (PDF, DOCX, etc.) and processes it to extract structured text elements."
)
async def upload_document(
    file: UploadFile = File(..., description="The document file to be processed."),
    doc_service: DocumentService = Depends(lambda: document_service)
):
    """
    Handles the file upload, creates metadata, and invokes the document
    processing service.
    """
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file was uploaded."
        )

    document_metadata = DocumentMetadata(
        file_name=file.filename,
        content_type=file.content_type,
        size=file.size
    )

    try:
        processed_elements = await doc_service.process_document(file)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}"
        )

    return DocumentProcessingResult(
        metadata=document_metadata,
        elements=processed_elements
    )
