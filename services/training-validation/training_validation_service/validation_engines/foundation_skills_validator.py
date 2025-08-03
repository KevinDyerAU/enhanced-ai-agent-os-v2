import logging
from typing import Dict, Any, List
import json

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
        
        skills_coverage = await self._analyze_foundation_skills_coverage(unit_foundation_skills, documents)
        
        recommendations = self._generate_fs_recommendations(skills_coverage)
        
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
    
    def _generate_fs_recommendations(self, skills_coverage: Dict[str, Any]) -> List[str]:
        """Generate recommendations for Foundation Skills"""
        recommendations = []
        
        weak_categories = []
        missing_categories = []
        
        for category, analysis in skills_coverage.items():
            if analysis["coverage_score"] == 0:
                missing_categories.append(category)
            elif analysis["coverage_score"] < 50:
                weak_categories.append(category)
        
        if missing_categories:
            recommendations.append(f"Add content addressing missing foundation skills: {', '.join(missing_categories)}")
        
        if weak_categories:
            recommendations.append(f"Strengthen coverage of foundation skills: {', '.join(weak_categories)}")
        
        non_integrated = [cat for cat, analysis in skills_coverage.items() if not analysis["assessment_integration"] and analysis["coverage_score"] > 0]
        if non_integrated:
            recommendations.append(f"Integrate assessment of foundation skills: {', '.join(non_integrated)}")
        
        total_categories = len(self.foundation_skills_categories)
        covered_categories = len([k for k, v in skills_coverage.items() if v["coverage_score"] > 30])
        coverage_percentage = (covered_categories / total_categories) * 100
        
        if coverage_percentage < 60:
            recommendations.append("Overall foundation skills coverage is below acceptable threshold")
        elif coverage_percentage >= 90:
            recommendations.append("Excellent foundation skills coverage achieved")
        
        if not recommendations:
            recommendations.append("Foundation skills are adequately addressed in training materials")
        
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
