from dataclasses import dataclass
from typing import Optional

@dataclass
class ValidationGap:
    """Structured gap object for validation findings"""
    gap_type: str  # e.g., "Missing Resource", "Ambiguous Instruction"
    description: str  # Clear explanation of the issue
    recommendation: str  # Actionable suggestion for fixing the issue
    confidence_score: float  # Score indicating system's confidence (0.0-1.0)
    category: str  # AC category this gap belongs to
    severity: str = "medium"  # low, medium, high
    location: Optional[str] = None  # Document/section where gap was found
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "gap_type": self.gap_type,
            "description": self.description,
            "recommendation": self.recommendation,
            "confidence_score": self.confidence_score,
            "category": self.category,
            "severity": self.severity,
            "location": self.location
        }
