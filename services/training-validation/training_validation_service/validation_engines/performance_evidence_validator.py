import logging
from typing import Dict, Any, List
import json
from .validation_gap import ValidationGap

logger = logging.getLogger(__name__)

class PerformanceEvidenceValidator:
    """Validates training documents against Performance Evidence (PE) requirements"""
    
    def __init__(self, strictness_level: str = "normal"):
        self.strictness_level = strictness_level
    
    async def validate(self, training_unit: Dict[str, Any], documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute Performance Evidence validation"""
        logger.info(f"Starting PE validation for unit {training_unit.get('unit_code')}")
        
        unit_performance_evidence = training_unit.get("performance_evidence", [])
        
        if not unit_performance_evidence:
            return {
                "validation_type": "performance_evidence",
                "overall_score": 0,
                "findings": {"error": "No performance evidence requirements found in training unit"},
                "recommendations": ["Retrieve complete training unit data with performance evidence requirements"],
                "gaps": [],
                "assessment_methods": {},
                "evidence_collection": {}
            }
        
        assessment_methods = await self._analyze_assessment_methods(unit_performance_evidence, documents)
        
        evidence_collection = await self._analyze_evidence_collection(unit_performance_evidence, documents)
        
        gaps = self._identify_pe_gaps(assessment_methods, evidence_collection)
        recommendations = self._generate_pe_recommendations(assessment_methods, evidence_collection, gaps)
        
        overall_score = self._calculate_pe_score(assessment_methods, evidence_collection)
        
        return {
            "validation_type": "performance_evidence",
            "overall_score": round(overall_score, 2),
            "findings": {
                "assessment_methods_analysis": assessment_methods,
                "evidence_collection_analysis": evidence_collection,
                "performance_criteria_alignment": await self._analyze_performance_criteria_alignment(unit_performance_evidence, documents)
            },
            "recommendations": recommendations,
            "gaps": [gap.to_dict() for gap in gaps],
            "assessment_methods": assessment_methods,
            "evidence_collection": evidence_collection
        }
    
    async def _analyze_assessment_methods(self, performance_requirements: List[Dict], documents: List[Dict]) -> Dict[str, Any]:
        """Analyze assessment methods specified in documents"""
        methods_analysis = {
            "identified_methods": [],
            "method_clarity": 0,
            "method_appropriateness": 0,
            "method_coverage": 0
        }
        
        assessment_methods = [
            "observation", "demonstration", "portfolio", "project", "case study",
            "simulation", "role play", "presentation", "interview", "practical assessment"
        ]
        
        identified_methods = set()
        method_mentions = 0
        
        for doc in documents:
            content = doc.get("content_extracted", "").lower()
            
            for method in assessment_methods:
                if method in content:
                    identified_methods.add(method)
                    method_mentions += content.count(method)
        
        methods_analysis["identified_methods"] = list(identified_methods)
        
        if method_mentions > 0:
            methods_analysis["method_clarity"] = min(100, method_mentions * 15)
        
        if len(identified_methods) >= 3:
            methods_analysis["method_appropriateness"] = 90
        elif len(identified_methods) >= 2:
            methods_analysis["method_appropriateness"] = 75
        elif len(identified_methods) >= 1:
            methods_analysis["method_appropriateness"] = 60
        else:
            methods_analysis["method_appropriateness"] = 30
        
        if len(performance_requirements) > 0:
            coverage_ratio = len(identified_methods) / len(performance_requirements)
            methods_analysis["method_coverage"] = min(100, coverage_ratio * 100)
        
        return methods_analysis
    
    async def _analyze_evidence_collection(self, performance_requirements: List[Dict], documents: List[Dict]) -> Dict[str, Any]:
        """Analyze evidence collection procedures"""
        evidence_analysis = {
            "collection_procedures": [],
            "documentation_requirements": [],
            "evidence_types": [],
            "collection_clarity": 0,
            "storage_procedures": 0
        }
        
        collection_keywords = [
            "evidence", "documentation", "record", "portfolio", "collect", "gather",
            "submit", "store", "maintain", "organize", "file"
        ]
        
        evidence_types = [
            "written work", "practical demonstration", "video recording", "photographs",
            "witness testimony", "supervisor feedback", "self-assessment", "peer review"
        ]
        
        found_procedures = set()
        found_evidence_types = set()
        collection_mentions = 0
        
        for doc in documents:
            content = doc.get("content_extracted", "").lower()
            
            for keyword in collection_keywords:
                if keyword in content:
                    collection_mentions += content.count(keyword)
                    found_procedures.add(keyword)
            
            for evidence_type in evidence_types:
                if evidence_type in content:
                    found_evidence_types.add(evidence_type)
        
        evidence_analysis["collection_procedures"] = list(found_procedures)
        evidence_analysis["evidence_types"] = list(found_evidence_types)
        
        if collection_mentions > 0:
            evidence_analysis["collection_clarity"] = min(100, collection_mentions * 10)
        
        storage_keywords = ["store", "maintain", "organize", "file", "archive", "database"]
        storage_mentions = sum([doc.get("content_extracted", "").lower().count(keyword) for doc in documents for keyword in storage_keywords])
        
        if storage_mentions > 0:
            evidence_analysis["storage_procedures"] = min(100, storage_mentions * 20)
        
        return evidence_analysis
    
    async def _analyze_performance_criteria_alignment(self, performance_requirements: List[Dict], documents: List[Dict]) -> Dict[str, Any]:
        """Analyze alignment between performance criteria and evidence requirements"""
        alignment_analysis = {
            "criteria_coverage": 0,
            "evidence_alignment": 0,
            "assessment_validity": 0
        }
        
        
        total_content_length = sum([len(doc.get("content_extracted", "")) for doc in documents])
        
        if total_content_length > 5000:
            alignment_analysis["criteria_coverage"] = 85
            alignment_analysis["evidence_alignment"] = 80
            alignment_analysis["assessment_validity"] = 75
        elif total_content_length > 2000:
            alignment_analysis["criteria_coverage"] = 70
            alignment_analysis["evidence_alignment"] = 65
            alignment_analysis["assessment_validity"] = 60
        else:
            alignment_analysis["criteria_coverage"] = 50
            alignment_analysis["evidence_alignment"] = 45
            alignment_analysis["assessment_validity"] = 40
        
        return alignment_analysis
    
    def _identify_pe_gaps(self, assessment_methods: Dict[str, Any], evidence_collection: Dict[str, Any]) -> List[ValidationGap]:
        """Identify Performance Evidence gaps"""
        gaps = []
        
        if len(assessment_methods["identified_methods"]) < 2:
            gap = ValidationGap(
                gap_type="Insufficient Assessment Methods",
                description=f"Only {len(assessment_methods['identified_methods'])} assessment method(s) identified. Multiple methods needed for comprehensive evaluation.",
                recommendation="Include at least 2-3 different assessment methods (e.g., observation, demonstration, portfolio)",
                confidence_score=0.90,
                category="performance_evidence",
                severity="high"
            )
            gaps.append(gap)
        
        if assessment_methods["method_clarity"] < 70:
            gap = ValidationGap(
                gap_type="Unclear Assessment Methods",
                description=f"Assessment method descriptions lack clarity (score: {assessment_methods['method_clarity']}/100)",
                recommendation="Provide detailed, step-by-step descriptions of how each assessment method will be conducted",
                confidence_score=0.85,
                category="performance_evidence",
                severity="medium"
            )
            gaps.append(gap)
        
        if len(evidence_collection["evidence_types"]) < 3:
            gap = ValidationGap(
                gap_type="Limited Evidence Types",
                description=f"Only {len(evidence_collection['evidence_types'])} evidence type(s) specified. Diverse evidence needed.",
                recommendation="Specify multiple evidence types (written work, practical demonstration, video recording, etc.)",
                confidence_score=0.80,
                category="performance_evidence",
                severity="medium"
            )
            gaps.append(gap)
        
        if evidence_collection["storage_procedures"] < 60:
            gap = ValidationGap(
                gap_type="Missing Storage Procedures",
                description="Evidence storage and maintenance procedures not clearly defined",
                recommendation="Define clear procedures for storing, organizing, and maintaining collected evidence",
                confidence_score=0.85,
                category="performance_evidence",
                severity="medium"
            )
            gaps.append(gap)
        
        return gaps
    
    def _generate_pe_recommendations(self, assessment_methods: Dict[str, Any], evidence_collection: Dict[str, Any], gaps: List[ValidationGap]) -> List[str]:
        """Generate recommendations for Performance Evidence"""
        recommendations = []
        
        # Add gap-based recommendations
        for gap in gaps:
            recommendations.append(gap.recommendation)
        
        if self.strictness_level == "strict":
            if assessment_methods["method_appropriateness"] < 90:
                recommendations.append("For strict validation: Ensure all assessment methods directly align with industry standards")
            if evidence_collection["collection_clarity"] < 80:
                recommendations.append("For strict validation: Provide explicit, unambiguous evidence collection procedures")
        
        if not recommendations:
            recommendations.append("Performance evidence requirements meet validation standards")
        
        return recommendations
    
    def _calculate_pe_score(self, assessment_methods: Dict[str, Any], evidence_collection: Dict[str, Any]) -> float:
        """Calculate overall Performance Evidence score"""
        method_score = (
            assessment_methods["method_clarity"] * 0.3 +
            assessment_methods["method_appropriateness"] * 0.4 +
            assessment_methods["method_coverage"] * 0.3
        )
        
        evidence_score = (
            evidence_collection["collection_clarity"] * 0.5 +
            evidence_collection["storage_procedures"] * 0.3 +
            (len(evidence_collection["evidence_types"]) * 10) * 0.2  # Diversity bonus
        )
        
        overall_score = method_score * 0.6 + evidence_score * 0.4
        
        if self.strictness_level == "strict":
            overall_score *= 0.85
        elif self.strictness_level == "lenient":
            overall_score *= 1.15
            overall_score = min(100, overall_score)
        
        return min(100, max(0, overall_score))
