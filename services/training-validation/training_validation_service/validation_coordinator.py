"""
Validation Coordinator

This module coordinates the execution of multiple validation engines and aggregates their results.
"""
import logging
import json
from typing import Dict, List, Any, Optional, Type, TypeVar
from dataclasses import asdict
import asyncio
from contextlib import asynccontextmanager

from validation_engines.base_validator import BaseValidator
from models.validation_models import (
    ValidationResult, 
    ValidationSummary, 
    TrainingUnit, 
    ValidationDocument,
    ValidationRequest,
    ValidationResponse,
    ValidationType
)

logger = logging.getLogger(__name__)
T = TypeVar('T', bound=BaseValidator)

class ValidationCoordinator:
    """Coordinates the execution of multiple validation engines."""
    
    def __init__(self, validators: Dict[ValidationType, Type[BaseValidator]] = None):
        """Initialize with a dictionary of validator classes."""
        self.validators = validators or {}
    
    def register_validator(self, validator_type: ValidationType, validator_class: Type[BaseValidator]):
        """Register a new validator class."""
        self.validators[validator_type] = validator_class
    
    async def _run_validator(
        self, 
        validator_class: Type[BaseValidator],
        request: ValidationRequest
    ) -> ValidationResult:
        """Run a single validator and handle errors."""
        validator = validator_class(request.strictness_level)
        try:
            return await validator.validate(request.training_unit, request.documents)
        except Exception as e:
            logger.exception(f"Validator {validator_class.__name__} failed")
            return ValidationResult(
                validation_type=validator_class.get_validation_type(),
                overall_score=0,
                details={"error": str(e)},
                error=str(e)
            )
    
    async def run_validation(self, request: ValidationRequest) -> ValidationResponse:
        """
        Run all registered validators in parallel and return aggregated results.
        
        Args:
            request: Validation request containing training unit and documents
            
        Returns:
            ValidationResponse with aggregated results from all validators
        """
        logger.info(f"Starting validation for session {request.session_id}")
        
        # Run all validators in parallel
        tasks = [
            self._run_validator(validator_class, request)
            for validator_class in self.validators.values()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        results_by_type = {
            result.validation_type: result 
            for result in results 
            if isinstance(result, ValidationResult)
        }
        
        # Calculate overall metrics
        scores = [r.overall_score for r in results_by_type.values() if r.error is None]
        overall_score = sum(scores) / len(scores) if scores else 0
        
        # Aggregate recommendations
        all_recommendations = []
        for result in results_by_type.values():
            all_recommendations.extend(result.recommendations)
        
        # Create summary
        summary = ValidationSummary(
            total_validations=len(results_by_type),
            successful_validations=len([r for r in results_by_type.values() if r.error is None]),
            failed_validations=len([r for r in results_by_type.values() if r.error is not None]),
            average_score=round(overall_score, 2)
        )
        
        return ValidationResponse(
            overall_score=round(overall_score, 2),
            findings={k.value: asdict(v) for k, v in results_by_type.items()},
            recommendations=all_recommendations,
            summary=summary,
            strictness_level=request.strictness_level
        )

# Default coordinator instance with standard validators
default_coordinator = ValidationCoordinator()

# Helper function for backward compatibility
async def run_validation_engines(session: Dict[str, Any], documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Legacy function that wraps the new coordinator."""
    from validation_engines import (
        AssessmentConditionsValidator,
        KnowledgeEvidenceValidator,
        PerformanceEvidenceValidator,
        FoundationSkillsValidator
    )
    
    # Configure coordinator with standard validators if not already done
    if not default_coordinator.validators:
        default_coordinator.register_validator(
            ValidationType.ASSESSMENT_CONDITIONS, 
            AssessmentConditionsValidator
        )
        default_coordinator.register_validator(
            ValidationType.KNOWLEDGE_EVIDENCE,
            KnowledgeEvidenceValidator
        )
        default_coordinator.register_validator(
            ValidationType.PERFORMANCE_EVIDENCE,
            PerformanceEvidenceValidator
        )
        default_coordinator.register_validator(
            ValidationType.FOUNDATION_SKILLS,
            FoundationSkillsValidator
        )
    
    # Convert legacy format to new request model
    config = session.get("configuration", {}) if isinstance(session.get("configuration"), dict) else json.loads(session.get("configuration", "{}"))
    
    training_unit = TrainingUnit(
        unit_code=session["unit_code"],
        title=session.get("unit_title", session.get("title", "Unknown")),
        elements=session.get("elements", []),
        performance_criteria=session.get("performance_criteria", []),
        knowledge_evidence=session.get("knowledge_evidence", []),
        performance_evidence=session.get("performance_evidence", []),
        foundation_skills=session.get("foundation_skills", []),
        assessment_conditions=session.get("assessment_conditions", [])
    )
    
    validation_docs = [
        ValidationDocument(
            filename=doc["filename"],
            content_extracted=doc["content_extracted"],
            metadata=doc["metadata"] if isinstance(doc["metadata"], dict) else json.loads(doc["metadata"])
        )
        for doc in documents
    ]
    
    request = ValidationRequest(
        session_id=session["id"],
        training_unit=training_unit,
        documents=validation_docs,
        strictness_level=config.get("strictness_level", "normal")
    )
    
    # Run validation and convert response to legacy format
    response = await default_coordinator.run_validation(request)
    return {
        "overall_score": response.overall_score,
        "findings": response.findings,
        "recommendations": response.recommendations,
        "summary": asdict(response.summary),
        "strictness_level": response.strictness_level
    }

async def generate_validation_report(session: Dict[str, Any], validation_results: Dict[str, Any]) -> str:
    """
    Generate a comprehensive validation report in Markdown format.
    
    Args:
        session: Session information
        validation_results: Results from validation_engines
        
    Returns:
        str: Markdown formatted report
    """
    unit_title = session.get('unit_title', session.get('title', 'Unknown Unit'))
    session_name = session.get('name', 'Unnamed Session')
    unit_code = session.get('unit_code', 'Unknown Code')
    
    report = f"""# Training Validation Report

- **Session Name**: {session_name}
- **Training Unit**: {unit_code} - {unit_title}
- **Validation Date**: {session.get('started_at', 'N/A')}
- **Strictness Level**: {validation_results.get('strictness_level', 'normal')}

- **Overall Score**: {validation_results['overall_score']}/100
- **Total Validations**: {validation_results['summary']['total_validations']}
- **Successful Validations**: {validation_results['summary']['successful_validations']}
- **Failed Validations**: {validation_results['summary']['failed_validations']}


"""
    
    all_gaps = []
    for validation_type, result in validation_results["findings"].items():
        if "gaps" in result:
            gaps = result["gaps"]
            if isinstance(gaps, list):
                for gap in gaps:
                    if isinstance(gap, dict):
                        all_gaps.append(gap)
                    elif hasattr(gap, 'to_dict'):
                        all_gaps.append(gap.to_dict())
                    else:
                        all_gaps.append({
                            "gap_type": "Unknown",
                            "description": str(gap),
                            "recommendation": "Review this finding",
                            "confidence_score": 0.5,
                            "severity": "medium"
                        })
    
    if all_gaps:
        report += f"## Gap Analysis Summary\n"
        report += f"- **Total Gaps Identified**: {len(all_gaps)}\n"
        
        high_gaps = [gap for gap in all_gaps if gap.get("severity") == "high"]
        medium_gaps = [gap for gap in all_gaps if gap.get("severity") == "medium"]
        low_gaps = [gap for gap in all_gaps if gap.get("severity") == "low"]
        
        report += f"- **High Priority**: {len(high_gaps)}\n"
        report += f"- **Medium Priority**: {len(medium_gaps)}\n"
        report += f"- **Low Priority**: {len(low_gaps)}\n\n"
    
    for validation_type, result in validation_results["findings"].items():
        report += f"### {validation_type.replace('_', ' ').title()}\n"
        report += f"- **Score**: {result.get('overall_score', 0)}/100\n"
        
        if "error" in result:
            report += f"- **Status**: Failed - {result['error']}\n"
        else:
            report += f"- **Status**: Completed\n"
            
            if "compliance_level" in result:
                report += f"- **Compliance Level**: {result['compliance_level']}\n"
            
            if "findings" in result and result["findings"]:
                report += f"- **Key Findings**:\n"
                if isinstance(result["findings"], dict):
                    for category, findings in result["findings"].items():
                        if isinstance(findings, list):
                            for finding in findings:
                                report += f"  - {finding}\n"
                elif isinstance(result["findings"], list):
                    for finding in result["findings"]:
                        report += f"  - {finding}\n"
            
            if "gaps" in result and result["gaps"]:
                report += f"- **Identified Gaps** ({len(result['gaps'])}):\n"
                for gap in result["gaps"]:
                    if isinstance(gap, dict):
                        gap_dict = gap
                    elif hasattr(gap, 'to_dict'):
                        gap_dict = gap.to_dict()
                    else:
                        gap_dict = {
                            "gap_type": "Unknown",
                            "description": str(gap),
                            "recommendation": "Review this finding",
                            "confidence_score": 0.5,
                            "severity": "medium"
                        }
                    
                    severity_icon = "🔴" if gap_dict.get("severity") == "high" else "🟡" if gap_dict.get("severity") == "medium" else "🟢"
                    report += f"  {severity_icon} **{gap_dict.get('gap_type', 'Unknown')}** (Confidence: {gap_dict.get('confidence_score', 0):.0%})\n"
                    report += f"    - *Issue*: {gap_dict.get('description', 'No description')}\n"
                    report += f"    - *Action*: {gap_dict.get('recommendation', 'No recommendation')}\n"
            
            if "recommendations" in result and result["recommendations"]:
                report += f"- **Recommendations**:\n"
                for rec in result["recommendations"]:
                    report += f"  - {rec}\n"
        
        report += "\n"
    
    if validation_results["recommendations"]:
        report += "## Overall Recommendations\n"
        for rec in validation_results["recommendations"]:
            report += f"- {rec}\n"
        report += "\n"
    
    high_priority_gaps = []
    for result in validation_results["findings"].values():
        if "gaps" in result:
            for gap in result["gaps"]:
                if isinstance(gap, dict):
                    gap_dict = gap
                elif hasattr(gap, 'to_dict'):
                    gap_dict = gap.to_dict()
                else:
                    gap_dict = {
                        "gap_type": "Unknown",
                        "description": str(gap),
                        "recommendation": "Review this finding",
                        "confidence_score": 0.5,
                        "severity": "medium"
                    }
                
                if gap_dict.get("severity") == "high":
                    high_priority_gaps.append(gap_dict)
    
    if high_priority_gaps:
        report += "## Priority Action Items\n"
        for i, gap in enumerate(high_priority_gaps, 1):
            report += f"{i}. **{gap.get('gap_type', 'Unknown')}**: {gap.get('recommendation', 'No recommendation')}\n"
        report += "\n"
    
    report += "---\n"
    report += "*This report was generated automatically by the AOS Training Validation System with enhanced gap analysis.*\n"
    
    return report

async def create_validation_asset(conn, session: Dict[str, Any], report_content: str, result_id: str) -> Dict[str, str]:
    """
    Create a creative asset for the validation report to go through airlock review.
    
    Args:
        conn: Database connection
        session: Session information
        report_content: Markdown content of the report
        result_id: ID of the validation result
        
    Returns:
        Dict containing asset_id and status
        
    Raises:
        Exception: If there's an error creating the asset
    """
    from datetime import datetime
    import uuid
    
    try:
        # Create asset in database
        asset_id = str(uuid.uuid4())
        created_at = datetime.utcnow()
        
        # Insert into assets table
        await conn.execute(
            """
            INSERT INTO creative_assets (id, name, description, asset_type, status, 
                                      created_by, created_at, updated_at, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            asset_id,
            f"Validation Report - {session.get('unit_code')} - {session.get('name')}",
            f"Validation report for {session.get('unit_code')} - {session.get('unit_title', '')}",
            "validation_report",
            "pending_review",
            session.get('created_by', 'system'),
            created_at,
            created_at,
            json.dumps({
                "session_id": session.get('id'),
                "unit_code": session.get('unit_code'),
                "validation_result_id": result_id,
                "report_type": "validation"
            })
        )
        
        # Insert into validation_reports table
        await conn.execute(
            """
            INSERT INTO validation_reports (id, session_id, report_content, status, 
                                         created_at, updated_at, asset_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            result_id,
            session.get('id'),
            report_content,
            "pending_review",
            created_at,
            created_at,
            asset_id
        )
        
        return {"asset_id": asset_id, "status": "pending_review"}
        
    except Exception as e:
        logger.exception("Failed to create validation asset")
        raise RuntimeError(f"Failed to create validation asset: {str(e)}")
