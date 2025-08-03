import logging
from typing import Dict, Any, List
import json

logger = logging.getLogger(__name__)

class KnowledgeEvidenceValidator:
    """Validates training documents against Knowledge Evidence (KE) requirements"""
    
    def __init__(self, strictness_level: str = "normal"):
        self.strictness_level = strictness_level
    
    async def validate(self, training_unit: Dict[str, Any], documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute Knowledge Evidence validation"""
        logger.info(f"Starting KE validation for unit {training_unit.get('unit_code')}")
        
        unit_knowledge_evidence = training_unit.get("knowledge_evidence", [])
        
        if not unit_knowledge_evidence:
            return {
                "validation_type": "knowledge_evidence",
                "overall_score": 0,
                "findings": {"error": "No knowledge evidence requirements found in training unit"},
                "recommendations": ["Retrieve complete training unit data with knowledge evidence requirements"],
                "coverage_analysis": {},
                "gaps": ["Complete knowledge evidence requirements missing"]
            }
        
        coverage_analysis = await self._analyze_knowledge_coverage(unit_knowledge_evidence, documents)
        
        gaps = self._identify_knowledge_gaps(unit_knowledge_evidence, coverage_analysis)
        recommendations = self._generate_ke_recommendations(gaps, coverage_analysis)
        
        overall_score = self._calculate_ke_score(coverage_analysis, gaps)
        
        return {
            "validation_type": "knowledge_evidence",
            "overall_score": round(overall_score, 2),
            "findings": {
                "total_requirements": len(unit_knowledge_evidence),
                "covered_requirements": len([k for k, v in coverage_analysis.items() if v["covered"]]),
                "coverage_percentage": round((len([k for k, v in coverage_analysis.items() if v["covered"]]) / len(unit_knowledge_evidence)) * 100, 2) if unit_knowledge_evidence else 0,
                "detailed_analysis": coverage_analysis
            },
            "recommendations": recommendations,
            "coverage_analysis": coverage_analysis,
            "gaps": gaps
        }
    
    async def _analyze_knowledge_coverage(self, knowledge_requirements: List[Dict], documents: List[Dict]) -> Dict[str, Any]:
        """Analyze how well documents cover knowledge requirements"""
        coverage_analysis = {}
        
        for i, requirement in enumerate(knowledge_requirements):
            req_key = f"ke_{i+1}"
            requirement_text = str(requirement) if isinstance(requirement, dict) else requirement
            
            coverage_analysis[req_key] = {
                "requirement": requirement_text,
                "covered": False,
                "coverage_strength": 0,
                "supporting_documents": [],
                "relevant_content": []
            }
            
            for doc in documents:
                content = doc.get("content_extracted", "")
                if content:
                    coverage_score = self._assess_requirement_coverage(requirement_text, content)
                    if coverage_score > 0.3:  # Threshold for considering it covered
                        coverage_analysis[req_key]["covered"] = True
                        coverage_analysis[req_key]["coverage_strength"] = max(
                            coverage_analysis[req_key]["coverage_strength"], coverage_score
                        )
                        coverage_analysis[req_key]["supporting_documents"].append(doc.get("filename", "Unknown"))
                        
                        relevant_snippets = self._extract_relevant_snippets(requirement_text, content)
                        coverage_analysis[req_key]["relevant_content"].extend(relevant_snippets)
        
        return coverage_analysis
    
    def _assess_requirement_coverage(self, requirement: str, content: str) -> float:
        """Assess how well content covers a knowledge requirement"""
        requirement_lower = requirement.lower()
        content_lower = content.lower()
        
        key_terms = self._extract_key_terms(requirement_lower)
        
        matches = 0
        total_terms = len(key_terms)
        
        for term in key_terms:
            if term in content_lower:
                matches += 1
        
        coverage_score = matches / total_terms if total_terms > 0 else 0
        
        if requirement_lower in content_lower:
            coverage_score = min(1.0, coverage_score + 0.3)
        
        return coverage_score
    
    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms from requirement text"""
        common_words = {"the", "and", "or", "of", "to", "in", "for", "with", "by", "from", "a", "an", "is", "are", "be", "have", "has", "will", "can", "may", "must", "should"}
        
        words = text.split()
        key_terms = []
        
        for word in words:
            clean_word = word.strip(".,!?;:")
            if len(clean_word) > 2 and clean_word not in common_words:
                key_terms.append(clean_word)
        
        return key_terms
    
    def _extract_relevant_snippets(self, requirement: str, content: str, max_snippets: int = 3) -> List[str]:
        """Extract relevant content snippets that relate to the requirement"""
        sentences = content.split('.')
        relevant_snippets = []
        
        requirement_terms = set(self._extract_key_terms(requirement.lower()))
        
        for sentence in sentences[:50]:  # Limit to first 50 sentences for performance
            sentence_lower = sentence.lower()
            sentence_terms = set(self._extract_key_terms(sentence_lower))
            
            overlap = len(requirement_terms.intersection(sentence_terms))
            if overlap >= 2:  # At least 2 terms match
                relevant_snippets.append(sentence.strip())
                
                if len(relevant_snippets) >= max_snippets:
                    break
        
        return relevant_snippets
    
    def _identify_knowledge_gaps(self, requirements: List[Dict], coverage_analysis: Dict[str, Any]) -> List[str]:
        """Identify knowledge gaps based on coverage analysis"""
        gaps = []
        
        for req_key, analysis in coverage_analysis.items():
            if not analysis["covered"]:
                gaps.append(f"Knowledge requirement not covered: {analysis['requirement']}")
            elif analysis["coverage_strength"] < 0.6:
                gaps.append(f"Weak coverage for: {analysis['requirement']}")
        
        return gaps
    
    def _generate_ke_recommendations(self, gaps: List[str], coverage_analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on knowledge evidence analysis"""
        recommendations = []
        
        if gaps:
            recommendations.append(f"Address {len(gaps)} knowledge evidence gaps identified")
            
            uncovered_count = len([g for g in gaps if "not covered" in g])
            weak_count = len([g for g in gaps if "Weak coverage" in g])
            
            if uncovered_count > 0:
                recommendations.append(f"Add content to address {uncovered_count} completely uncovered knowledge requirements")
            
            if weak_count > 0:
                recommendations.append(f"Strengthen coverage for {weak_count} weakly covered knowledge requirements")
        
        total_requirements = len(coverage_analysis)
        covered_requirements = len([k for k, v in coverage_analysis.items() if v["covered"]])
        coverage_percentage = (covered_requirements / total_requirements) * 100 if total_requirements > 0 else 0
        
        if coverage_percentage < 70:
            recommendations.append("Overall knowledge evidence coverage is below acceptable threshold (70%)")
        elif coverage_percentage < 90:
            recommendations.append("Consider enhancing knowledge evidence coverage to achieve excellence (90%+)")
        else:
            recommendations.append("Excellent knowledge evidence coverage achieved")
        
        doc_count = len(set([doc for analysis in coverage_analysis.values() for doc in analysis["supporting_documents"]]))
        if doc_count < 2:
            recommendations.append("Consider adding more diverse training materials to improve knowledge coverage")
        
        return recommendations
    
    def _calculate_ke_score(self, coverage_analysis: Dict[str, Any], gaps: List[str]) -> float:
        """Calculate overall Knowledge Evidence score"""
        if not coverage_analysis:
            return 0
        
        total_requirements = len(coverage_analysis)
        covered_requirements = len([k for k, v in coverage_analysis.items() if v["covered"]])
        
        coverage_percentage = (covered_requirements / total_requirements) * 100
        base_score = coverage_percentage * 0.8  # 80% weight for coverage
        
        total_strength = sum([v["coverage_strength"] for v in coverage_analysis.values()])
        avg_strength = total_strength / total_requirements
        strength_bonus = avg_strength * 20  # 20% weight for quality
        
        overall_score = base_score + strength_bonus
        
        if self.strictness_level == "strict":
            overall_score *= 0.9  # More stringent scoring
        elif self.strictness_level == "lenient":
            overall_score *= 1.1  # More generous scoring
            overall_score = min(100, overall_score)  # Cap at 100
        
        return min(100, max(0, overall_score))
