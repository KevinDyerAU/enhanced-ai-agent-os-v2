from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum, auto

class ValidationType(str, Enum):
    ASSESSMENT_CONDITIONS = "assessment_conditions"
    KNOWLEDGE_EVIDENCE = "knowledge_evidence"
    PERFORMANCE_EVIDENCE = "performance_evidence"
    FOUNDATION_SKILLS = "foundation_skills"

class ValidationStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ValidationResult:
    validation_type: ValidationType
    overall_score: float
    details: Dict[str, Any]
    recommendations: List[str] = field(default_factory=list)
    error: Optional[str] = None

@dataclass
class ValidationSummary:
    total_validations: int
    successful_validations: int
    failed_validations: int
    average_score: float

@dataclass
class TrainingUnit:
    unit_code: str
    title: str
    elements: List[Dict[str, Any]]
    performance_criteria: List[Dict[str, Any]]
    knowledge_evidence: List[Dict[str, Any]]
    performance_evidence: List[Dict[str, Any]]
    foundation_skills: List[Dict[str, Any]]
    assessment_conditions: List[Dict[str, Any]]

@dataclass
class ValidationDocument:
    filename: str
    content_extracted: str
    metadata: Dict[str, Any]

@dataclass
class ValidationRequest:
    session_id: str
    training_unit: TrainingUnit
    documents: List[ValidationDocument]
    strictness_level: str = "normal"

@dataclass
class ValidationResponse:
    overall_score: float
    findings: Dict[str, ValidationResult]
    recommendations: List[str]
    summary: ValidationSummary
    strictness_level: str
