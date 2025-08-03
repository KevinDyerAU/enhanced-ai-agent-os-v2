import logging
from typing import Dict, Any, List
import json
from .validation_gap import ValidationGap

logger = logging.getLogger(__name__)

class FoundationSkillsValidator:
    """Validates training documents against Foundation Skills (FS) requirements"""
    
    def __init__(self, strictness_level: str = "normal"):
        self.strictness_level = strictness_level
        self.foundation_skills_categories = {
            "literacy": ["reading", "writing", "communication", "language", "vocabulary"],
            "numeracy": ["mathematics", "calculation", "measurement", "data", "statistics"],
            "digital_literacy": ["computer", "technology", "digital", "software", "online"],
            "critical_thinking": ["analysis", "problem solving", "decision making", "evaluation"],
            "teamwork": ["collaboration", "team", "group work", "cooperation"],
            "learning": ["learning", "study", "research", "self-directed"]
        }
    
    async def validate(self, training_unit: Dict[str, Any], documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute Foundation Skills validation"""
        logger.info(f"Starting FS validation for unit {training_unit.get('unit_code')}")
        
        unit_foundation_skills = training_unit.get("foundation_skills", [])
        
        if not unit_foundation_skills:
            return {
                "validation_type": "foundation_skills",
                "overall_score": 0,
                "findings": {"error": "No foundation skills requirements found in training unit"},
                "recommendations": ["Retrieve complete training unit data with foundation skills requirements"],
                "gaps": [],
                "skill_coverage": {}
            }
        
        skills_coverage = await self._analyze_foundation_skills_coverage(unit_foundation_skills, documents)
        
        gaps = self._identify_fs_gaps(skills_coverage, unit_foundation_skills)
        recommendations = self._generate_fs_recommendations(skills_coverage, gaps)
        
        overall_score = self._calculate_fs_score(skills_coverage)
        
        return {
            "validation_type": "foundation_skills",
            "overall_score": round(overall_score, 2),
            "findings": {
                "skills_coverage": skills_coverage,
                "total_categories": len(self.foundation_skills_categories),
                "covered_categories": len([k for k, v in skills_coverage.items() if v["coverage_score"] > 30])
            },
            "recommendations": recommendations,
            "gaps": [gap.to_dict() for gap in gaps],
            "skills_breakdown": skills_coverage
        }
    
    async def _analyze_foundation_skills_coverage(self, unit_skills: List[Dict], documents: List[Dict]) -> Dict[str, Any]:
        """Analyze foundation skills coverage in documents"""
        coverage_analysis = {}
        
        for category, keywords in self.foundation_skills_categories.items():
            coverage_analysis[category] = {
                "coverage_score": 0,
                "keyword_matches": [],
                "supporting_content": [],
                "assessment_integration": False
            }
            
            total_matches = 0
            found_keywords = set()
            supporting_content = []
            
            for doc in documents:
                content = doc.get("content_extracted", "").lower()
                
                for keyword in keywords:
                    matches = content.count(keyword)
                    if matches > 0:
                        total_matches += matches
                        found_keywords.add(keyword)
                        
                        sentences = content.split('.')
                        for sentence in sentences:
                            if keyword in sentence and len(sentence.strip()) > 20:
                                supporting_content.append(sentence.strip()[:200])
                                if len(supporting_content) >= 3:
                                    break
            
            coverage_analysis[category]["keyword_matches"] = list(found_keywords)
            coverage_analysis[category]["supporting_content"] = supporting_content[:3]  # Limit to 3 examples
            
            if total_matches > 0:
                coverage_analysis[category]["coverage_score"] = min(100, total_matches * 15)
            
            assessment_keywords = ["assess", "evaluate", "test", "measure", "demonstrate"]
            for doc in documents:
                content = doc.get("content_extracted", "").lower()
                for keyword in keywords:
                    for assess_keyword in assessment_keywords:
                        if keyword in content and assess_keyword in content:
                            coverage_analysis[category]["assessment_integration"] = True
                            break
        
        return coverage_analysis
    
    def _identify_fs_gaps(self, skills_coverage: Dict[str, Any], unit_foundation_skills: List[Dict]) -> List[ValidationGap]:
        """Identify Foundation Skills gaps"""
        gaps = []
        
        for skill, analysis in skills_coverage.items():
            if analysis["coverage_score"] < 50:
                gap = ValidationGap(
                    gap_type="Poor Foundation Skill Coverage",
                    description=f"{skill.title()} foundation skill has poor coverage (score: {analysis['coverage_score']}/100)",
                    recommendation=f"Integrate {skill} activities throughout training materials and assessments",
                    confidence_score=0.90,
                    category="foundation_skills",
                    severity="high"
                )
                gaps.append(gap)
            elif analysis["coverage_score"] < 70:
                gap = ValidationGap(
                    gap_type="Weak Foundation Skill Integration",
                    description=f"{skill.title()} foundation skill needs stronger integration (score: {analysis['coverage_score']}/100)",
                    recommendation=f"Enhance {skill} integration with more explicit activities and assessment opportunities",
                    confidence_score=0.80,
                    category="foundation_skills",
                    severity="medium"
                )
                gaps.append(gap)
            
            if not analysis["assessment_integration"] and analysis["coverage_score"] > 0:
                gap = ValidationGap(
                    gap_type="Missing Assessment Integration",
                    description=f"{skill.title()} foundation skill is present but not integrated into assessments",
                    recommendation=f"Add explicit {skill} assessment criteria and evaluation methods",
                    confidence_score=0.85,
                    category="foundation_skills",
                    severity="medium"
                )
                gaps.append(gap)
        
        return gaps
    
    def _generate_fs_recommendations(self, skills_coverage: Dict[str, Any], gaps: List[ValidationGap]) -> List[str]:
        """Generate recommendations for Foundation Skills"""
        recommendations = []
        
        # Add gap-based recommendations
        for gap in gaps:
            recommendations.append(gap.recommendation)
        
        if self.strictness_level == "strict":
            for skill, analysis in skills_coverage.items():
                if analysis["coverage_score"] < 85:
                    recommendations.append(f"For strict validation: Strengthen {skill} integration to meet high standards")
        
        if not gaps:
            recommendations.append("Foundation skills are well integrated into training materials")
        
        return recommendations
    
    def _calculate_fs_score(self, skills_coverage: Dict[str, Any]) -> float:
        """Calculate overall Foundation Skills score"""
        if not skills_coverage:
            return 0
        
        total_score = sum([analysis["coverage_score"] for analysis in skills_coverage.values()])
        avg_score = total_score / len(skills_coverage)
        
        integrated_count = len([analysis for analysis in skills_coverage.values() if analysis["assessment_integration"]])
        integration_bonus = (integrated_count / len(skills_coverage)) * 10
        
        covered_categories = len([analysis for analysis in skills_coverage.values() if analysis["coverage_score"] > 30])
        if covered_categories == len(skills_coverage):
            comprehensive_bonus = 10
        else:
            comprehensive_bonus = 0
        
        overall_score = avg_score + integration_bonus + comprehensive_bonus
        
        if self.strictness_level == "strict":
            overall_score *= 0.9
        elif self.strictness_level == "lenient":
            overall_score *= 1.1
            overall_score = min(100, overall_score)
        
        return min(100, max(0, overall_score))
    
    async def _validate_epc_coverage(self, training_unit: Dict[str, Any], documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate Elements and Performance Criteria (EPC) coverage"""
        elements = training_unit.get("elements", [])
        performance_criteria = training_unit.get("performance_criteria", [])
        
        epc_analysis = {
            "elements_covered": 0,
            "performance_criteria_covered": 0,
            "total_elements": len(elements),
            "total_performance_criteria": len(performance_criteria),
            "coverage_gaps": []
        }
        
        combined_content = " ".join([doc.get("content_extracted", "") for doc in documents]).lower()
        
        for i, element in enumerate(elements):
            element_text = str(element).lower() if isinstance(element, dict) else element.lower()
            key_terms = self._extract_element_key_terms(element_text)
            
            if any(term in combined_content for term in key_terms):
                epc_analysis["elements_covered"] += 1
            else:
                epc_analysis["coverage_gaps"].append(f"Element {i+1} not adequately covered")
        
        for i, pc in enumerate(performance_criteria):
            pc_text = str(pc).lower() if isinstance(pc, dict) else pc.lower()
            key_terms = self._extract_element_key_terms(pc_text)
            
            if any(term in combined_content for term in key_terms):
                epc_analysis["performance_criteria_covered"] += 1
            else:
                epc_analysis["coverage_gaps"].append(f"Performance Criteria {i+1} not adequately covered")
        
        return epc_analysis
    
    def _extract_element_key_terms(self, text: str) -> List[str]:
        """Extract key terms from element or performance criteria text"""
        common_words = {"the", "and", "or", "of", "to", "in", "for", "with", "by", "from", "a", "an", "is", "are", "be", "have", "has", "will", "can", "may", "must", "should"}
        
        words = text.split()
        key_terms = []
        
        for word in words:
            clean_word = word.strip(".,!?;:")
            if len(clean_word) > 3 and clean_word not in common_words:
                key_terms.append(clean_word)
        
        return key_terms[:5]  # Return top 5 key terms
