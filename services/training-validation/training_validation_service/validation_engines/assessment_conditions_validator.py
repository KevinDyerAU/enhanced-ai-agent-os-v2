import logging
from typing import Dict, Any, List
import json

logger = logging.getLogger(__name__)

class AssessmentConditionsValidator:
    """Validates training documents against Assessment Conditions (AC) requirements"""
    
    def __init__(self, strictness_level: str = "normal"):
        self.strictness_level = strictness_level
        self.ac_categories = [
            "assessment_environment",
            "assessment_methods", 
            "assessment_tools",
            "assessment_timing",
            "assessment_evidence",
            "assessment_criteria",
            "assessment_support"
        ]
    
    async def validate(self, training_unit: Dict[str, Any], documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute Assessment Conditions validation"""
        logger.info(f"Starting AC validation for unit {training_unit.get('unit_code')}")
        
        findings = {}
        recommendations = []
        scores = {}
        
        unit_assessment_conditions = training_unit.get("assessment_conditions", [])
        
        for category in self.ac_categories:
            category_result = await self._validate_category(
                category, unit_assessment_conditions, documents
            )
            findings[category] = category_result["findings"]
            scores[category] = category_result["score"]
            recommendations.extend(category_result["recommendations"])
        
        overall_score = sum(scores.values()) / len(scores) if scores else 0
        
        return {
            "validation_type": "assessment_conditions",
            "overall_score": round(overall_score, 2),
            "category_scores": scores,
            "findings": findings,
            "recommendations": recommendations,
            "compliance_level": self._determine_compliance_level(overall_score)
        }
    
    async def _validate_category(self, category: str, unit_conditions: List[Dict], documents: List[Dict]) -> Dict[str, Any]:
        """Validate a specific AC category"""
        findings = []
        recommendations = []
        score = 0
        
        relevant_content = self._extract_relevant_content(category, documents)
        
        if category == "assessment_environment":
            score, category_findings, category_recommendations = await self._validate_environment(
                unit_conditions, relevant_content
            )
        elif category == "assessment_methods":
            score, category_findings, category_recommendations = await self._validate_methods(
                unit_conditions, relevant_content
            )
        elif category == "assessment_tools":
            score, category_findings, category_recommendations = await self._validate_tools(
                unit_conditions, relevant_content
            )
        elif category == "assessment_timing":
            score, category_findings, category_recommendations = await self._validate_timing(
                unit_conditions, relevant_content
            )
        elif category == "assessment_evidence":
            score, category_findings, category_recommendations = await self._validate_evidence(
                unit_conditions, relevant_content
            )
        elif category == "assessment_criteria":
            score, category_findings, category_recommendations = await self._validate_criteria(
                unit_conditions, relevant_content
            )
        elif category == "assessment_support":
            score, category_findings, category_recommendations = await self._validate_support(
                unit_conditions, relevant_content
            )
        
        findings.extend(category_findings)
        recommendations.extend(category_recommendations)
        
        return {
            "score": score,
            "findings": findings,
            "recommendations": recommendations
        }
    
    def _extract_relevant_content(self, category: str, documents: List[Dict]) -> List[str]:
        """Extract content relevant to the AC category from documents"""
        relevant_content = []
        
        for doc in documents:
            content = doc.get("content_extracted", "")
            if content and self._is_content_relevant(category, content):
                relevant_content.append(content)
        
        return relevant_content
    
    def _is_content_relevant(self, category: str, content: str) -> bool:
        """Check if content is relevant to the AC category"""
        category_keywords = {
            "assessment_environment": ["environment", "location", "workplace", "setting", "conditions"],
            "assessment_methods": ["method", "approach", "technique", "observation", "demonstration"],
            "assessment_tools": ["tool", "equipment", "resource", "checklist", "rubric"],
            "assessment_timing": ["time", "duration", "schedule", "deadline", "frequency"],
            "assessment_evidence": ["evidence", "portfolio", "documentation", "record"],
            "assessment_criteria": ["criteria", "standard", "benchmark", "requirement"],
            "assessment_support": ["support", "assistance", "guidance", "help", "accommodation"]
        }
        
        keywords = category_keywords.get(category, [])
        content_lower = content.lower()
        
        return any(keyword in content_lower for keyword in keywords)
    
    async def _validate_environment(self, unit_conditions: List[Dict], content: List[str]) -> tuple:
        """Validate assessment environment requirements"""
        score = 70  # Base score
        findings = []
        recommendations = []
        
        if not content:
            findings.append("No assessment environment information found in documents")
            recommendations.append("Add clear description of assessment environment requirements")
            score = 30
        else:
            findings.append("Assessment environment information present")
            if self.strictness_level == "strict":
                score = 85
        
        return score, findings, recommendations
    
    async def _validate_methods(self, unit_conditions: List[Dict], content: List[str]) -> tuple:
        """Validate assessment methods"""
        score = 75
        findings = []
        recommendations = []
        
        if not content:
            findings.append("Assessment methods not clearly specified")
            recommendations.append("Define specific assessment methods and approaches")
            score = 40
        else:
            findings.append("Assessment methods documented")
            if self.strictness_level == "strict":
                score = 90
        
        return score, findings, recommendations
    
    async def _validate_tools(self, unit_conditions: List[Dict], content: List[str]) -> tuple:
        """Validate assessment tools and resources"""
        score = 80
        findings = []
        recommendations = []
        
        if not content:
            findings.append("Assessment tools and resources not specified")
            recommendations.append("List required assessment tools and resources")
            score = 35
        else:
            findings.append("Assessment tools documented")
        
        return score, findings, recommendations
    
    async def _validate_timing(self, unit_conditions: List[Dict], content: List[str]) -> tuple:
        """Validate assessment timing requirements"""
        score = 65
        findings = []
        recommendations = []
        
        findings.append("Assessment timing requirements reviewed")
        if not content:
            recommendations.append("Specify assessment timing and duration requirements")
            score = 45
        
        return score, findings, recommendations
    
    async def _validate_evidence(self, unit_conditions: List[Dict], content: List[str]) -> tuple:
        """Validate evidence collection requirements"""
        score = 85
        findings = []
        recommendations = []
        
        findings.append("Evidence collection requirements assessed")
        if not content:
            recommendations.append("Define evidence collection and documentation requirements")
            score = 50
        
        return score, findings, recommendations
    
    async def _validate_criteria(self, unit_conditions: List[Dict], content: List[str]) -> tuple:
        """Validate assessment criteria"""
        score = 90
        findings = []
        recommendations = []
        
        findings.append("Assessment criteria reviewed")
        if not content:
            recommendations.append("Establish clear assessment criteria and standards")
            score = 40
        
        return score, findings, recommendations
    
    async def _validate_support(self, unit_conditions: List[Dict], content: List[str]) -> tuple:
        """Validate assessment support requirements"""
        score = 75
        findings = []
        recommendations = []
        
        findings.append("Assessment support requirements evaluated")
        if not content:
            recommendations.append("Define assessment support and accommodation options")
            score = 55
        
        return score, findings, recommendations
    
    def _determine_compliance_level(self, score: float) -> str:
        """Determine compliance level based on overall score"""
        if score >= 90:
            return "excellent"
        elif score >= 80:
            return "good"
        elif score >= 70:
            return "satisfactory"
        elif score >= 60:
            return "needs_improvement"
        else:
            return "inadequate"
