import logging
from typing import Dict, Any, List
import json
from validation_engines.assessment_conditions_validator import AssessmentConditionsValidator
from validation_engines.knowledge_evidence_validator import KnowledgeEvidenceValidator
from validation_engines.performance_evidence_validator import PerformanceEvidenceValidator
from validation_engines.foundation_skills_validator import FoundationSkillsValidator

logger = logging.getLogger(__name__)

async def run_validation_engines(session: Dict[str, Any], documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Coordinate execution of all validation engines"""
    logger.info(f"Starting validation for session {session['id']}")
    
    config = session.get("configuration", {}) if isinstance(session.get("configuration"), dict) else json.loads(session.get("configuration", "{}"))
    strictness_level = config.get("strictness_level", "normal")
    
    training_unit = {
        "unit_code": session["unit_code"],
        "title": session.get("unit_title", session.get("title", "Unknown")),
        "elements": json.loads(session["elements"]) if isinstance(session["elements"], str) else session.get("elements", []),
        "performance_criteria": json.loads(session["performance_criteria"]) if isinstance(session["performance_criteria"], str) else session.get("performance_criteria", []),
        "knowledge_evidence": json.loads(session["knowledge_evidence"]) if isinstance(session["knowledge_evidence"], str) else session.get("knowledge_evidence", []),
        "performance_evidence": json.loads(session["performance_evidence"]) if isinstance(session["performance_evidence"], str) else session.get("performance_evidence", []),
        "foundation_skills": json.loads(session["foundation_skills"]) if isinstance(session["foundation_skills"], str) else session.get("foundation_skills", []),
        "assessment_conditions": json.loads(session["assessment_conditions"]) if isinstance(session["assessment_conditions"], str) else session.get("assessment_conditions", [])
    }
    
    document_list = []
    for doc in documents:
        document_list.append({
            "filename": doc["filename"],
            "content_extracted": doc["content_extracted"],
            "metadata": json.loads(doc["metadata"]) if isinstance(doc["metadata"], str) else doc["metadata"]
        })
    
    ac_validator = AssessmentConditionsValidator(strictness_level)
    ke_validator = KnowledgeEvidenceValidator(strictness_level)
    pe_validator = PerformanceEvidenceValidator(strictness_level)
    fs_validator = FoundationSkillsValidator(strictness_level)
    
    results = {}
    
    try:
        results["assessment_conditions"] = await ac_validator.validate(training_unit, document_list)
        logger.info("Assessment Conditions validation completed")
    except Exception as e:
        logger.error(f"Assessment Conditions validation failed: {e}")
        results["assessment_conditions"] = {"validation_type": "assessment_conditions", "overall_score": 0, "error": str(e)}
    
    try:
        results["knowledge_evidence"] = await ke_validator.validate(training_unit, document_list)
        logger.info("Knowledge Evidence validation completed")
    except Exception as e:
        logger.error(f"Knowledge Evidence validation failed: {e}")
        results["knowledge_evidence"] = {"validation_type": "knowledge_evidence", "overall_score": 0, "error": str(e)}
    
    try:
        results["performance_evidence"] = await pe_validator.validate(training_unit, document_list)
        logger.info("Performance Evidence validation completed")
    except Exception as e:
        logger.error(f"Performance Evidence validation failed: {e}")
        results["performance_evidence"] = {"validation_type": "performance_evidence", "overall_score": 0, "error": str(e)}
    
    try:
        results["foundation_skills"] = await fs_validator.validate(training_unit, document_list)
        logger.info("Foundation Skills validation completed")
    except Exception as e:
        logger.error(f"Foundation Skills validation failed: {e}")
        results["foundation_skills"] = {"validation_type": "foundation_skills", "overall_score": 0, "error": str(e)}
    
    scores = [result.get("overall_score", 0) for result in results.values()]
    overall_score = sum(scores) / len(scores) if scores else 0
    
    all_recommendations = []
    for result in results.values():
        if "recommendations" in result:
            all_recommendations.extend(result["recommendations"])
    
    summary = {
        "total_validations": len(results),
        "successful_validations": len([r for r in results.values() if "error" not in r]),
        "failed_validations": len([r for r in results.values() if "error" in r]),
        "average_score": round(overall_score, 2)
    }
    
    return {
        "overall_score": round(overall_score, 2),
        "findings": results,
        "recommendations": all_recommendations,
        "summary": summary,
        "strictness_level": strictness_level
    }

async def generate_validation_report(session: Dict[str, Any], validation_results: Dict[str, Any]) -> str:
    """Generate a comprehensive validation report in Markdown format"""
    
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

async def create_validation_asset(conn, session: Dict[str, Any], report_content: str, result_id: str) -> str:
    """Create a creative asset for the validation report to go through airlock review"""
    
    unit_code = session.get('unit_code', 'Unknown Code')
    session_name = session.get('name', 'Unnamed Session')
    session_id = session.get('id', 'unknown')
    
    asset_id = await conn.fetchval(
        """INSERT INTO creative_assets 
           (title, description, type, asset_type, content_url, metadata, status, created_by_agent_id)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING id""",
        f"Training Validation Report - {unit_code}",
        f"Comprehensive validation report for {session_name} ({unit_code})",
        "validation_report",
        "validation_report",
        f"/validation/reports/{result_id}",
        json.dumps({
            "session_id": str(session_id),
            "result_id": str(result_id),
            "unit_code": unit_code,
            "report_content": report_content,
            "validation_type": "comprehensive",
            "generated_by": "training_validation_service"
        }),
        "draft",
        None
    )
    
    return asset_id
