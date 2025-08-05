from pydantic import BaseModel, Field
from typing import List, Dict, Any
import uuid

class DocumentMetadata(BaseModel):
    """Represents the metadata of an uploaded document."""
    document_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the document.")
    file_name: str = Field(..., description="Original name of the uploaded file.")
    content_type: str = Field(..., description="MIME type of the file.")
    size: int = Field(..., description="Size of the file in bytes.")
    
    class Config:
        from_attributes = True

class ProcessedElement(BaseModel):
    """Represents a single structured element extracted from a document."""
    type: str = Field(..., description="The type of the element (e.g., 'Title', 'NarrativeText', 'ListItem').")
    text: str = Field(..., description="The text content of the element.")
    metadata: Dict[str, Any] = Field(..., description="Source metadata from unstructured, like page number or file source.")

class DocumentProcessingResult(BaseModel):
    """The result of processing a single document."""
    metadata: DocumentMetadata
    elements: List[ProcessedElement] = Field(..., description="A list of structured elements extracted from the document.")
