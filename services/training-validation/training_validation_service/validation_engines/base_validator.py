from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass
from models.validation_models import TrainingUnit, ValidationDocument, ValidationResult, ValidationType

class BaseValidator(ABC):
    """Base class for all validation engines."""
    
    def __init__(self, strictness_level: str = "normal"):
        """Initialize the validator with a strictness level."""
        self.strictness_level = strictness_level
        self.validation_type = self.get_validation_type()
    
    @classmethod
    @abstractmethod
    def get_validation_type(cls) -> ValidationType:
        """Return the type of validation this engine performs."""
        pass
    
    @abstractmethod
    async def validate(
        self, 
        training_unit: TrainingUnit, 
        documents: List[ValidationDocument]
    ) -> ValidationResult:
        """
        Validate documents against the training unit.
        
        Args:
            training_unit: The training unit to validate against
            documents: List of documents to validate
            
        Returns:
            ValidationResult containing the validation outcome
        """
        pass
    
    def _calculate_score(
        self, 
        matches: int, 
        total_required: int, 
        weights: Dict[str, float] = None
    ) -> float:
        """
        Calculate a normalized score based on matches and required items.
        
        Args:
            matches: Number of successful matches
            total_required: Total number of required items
            weights: Optional weights for different match types
            
        Returns:
            Normalized score between 0 and 1
        """
        if not total_required:
            return 1.0  # Nothing to validate means perfect score
            
        if weights:
            weighted_matches = sum(weight for match, weight in weights.items() if match)
            weighted_total = sum(weights.values())
            return weighted_matches / weighted_total if weighted_total else 1.0
            
        return matches / total_required if total_required > 0 else 1.0
