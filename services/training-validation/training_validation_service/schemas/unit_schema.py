from pydantic import BaseModel, Field
from typing import List, Optional

class AssessmentConditions(BaseModel):
    """Assessment conditions for a training unit."""
    description: str = Field(..., description="Description of assessment conditions")
    environment: Optional[str] = Field(None, description="Assessment environment requirements")
    resources: Optional[str] = Field(None, description="Required resources for assessment")
    supervision: Optional[str] = Field(None, description="Supervision requirements")
    instructions: Optional[str] = Field(None, description="Assessment instructions")

class ElementPerformanceCriteria(BaseModel):
    """Element with its performance criteria."""
    element_title: str = Field(..., description="Title of the element")
    element_description: str = Field(..., description="Description of the element")
    performance_criteria: List[str] = Field(..., description="List of performance criteria for this element")

class Unit(BaseModel):
    """Training unit data scraped from training.gov.au."""
    unit_code: str = Field(..., description="Unit code (e.g., BSBWHS211)")
    unit_title: str = Field(..., description="Title of the training unit")
    unit_description: str = Field(..., description="Description of the training unit")
    assessment_conditions: AssessmentConditions = Field(..., description="Assessment conditions for the unit")
    elements_and_performance_criteria: List[ElementPerformanceCriteria] = Field(..., description="Elements and their performance criteria")
    performance_evidence: List[str] = Field(..., description="Required performance evidence")
    knowledge_evidence: List[str] = Field(..., description="Required knowledge evidence")
    foundation_skills: Optional[List[str]] = Field(default=[], description="Foundation skills requirements")
    
    class Config:
        from_attributes = True
