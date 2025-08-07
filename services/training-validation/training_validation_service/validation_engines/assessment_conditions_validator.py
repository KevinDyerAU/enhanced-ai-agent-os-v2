import logging
from typing import Dict, Any, List
import json
import re
import textstat
from .validation_gap import ValidationGap
from .base_validator import BaseValidator
from models.validation_models import ValidationType, TrainingUnit, ValidationDocument, ValidationResult

logger = logging.getLogger(__name__)

class AssessmentConditionsValidator(BaseValidator):
    """Validates training documents against Assessment Conditions (AC) requirements"""
    
    def __init__(self, strictness_level: str = "normal"):
        super().__init__(strictness_level)
        self.ac_categories = [
            "environment",  # Assessment Environment
            "resources",    # Necessary Resources  
            "supervision",  # Supervision and Observation
            "instructions", # Assessment Instructions (NEW - most critical)
            "interaction",  # Assessor Interaction (NEW)
            "third_party",  # Third-Party Reports
            "timing"        # Time Constraints
        ]
    
    @classmethod
    def get_validation_type(cls) -> ValidationType:
        return ValidationType.ASSESSMENT_CONDITIONS
    
    async def validate(self, training_unit: Dict[str, Any], documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute Assessment Conditions validation"""
        logger.info(f"Starting AC validation for unit {training_unit.get('unit_code')}")
        
        findings = {}
        recommendations = []
        scores = {}
        all_gaps = []
        
        unit_assessment_conditions = training_unit.get("assessment_conditions", [])
        
        for category in self.ac_categories:
            category_result = await self._validate_category(
                category, unit_assessment_conditions, documents
            )
            findings[category] = category_result["findings"]
            scores[category] = category_result["score"]
            recommendations.extend(category_result["recommendations"])
            all_gaps.extend(category_result["gaps"])
        
        overall_score = sum(scores.values()) / len(scores) if scores else 0
        
        return {
            "validation_type": "assessment_conditions",
            "overall_score": round(overall_score, 2),
            "category_scores": scores,
            "findings": findings,
            "recommendations": recommendations,
            "gaps": all_gaps,
            "compliance_level": self._determine_compliance_level(overall_score),
            "strictness_level": self.strictness_level
        }
    
    async def _validate_category(self, category: str, unit_conditions: List[Dict], documents: List[Dict]) -> Dict[str, Any]:
        """Validate a specific AC category"""
        findings = []
        recommendations = []
        gaps = []
        score = 0
        
        relevant_content = self._extract_relevant_content(category, documents)
        
        if category == "environment":
            score, category_findings, category_recommendations, category_gaps = await self._validate_environment(
                unit_conditions, relevant_content
            )
        elif category == "resources":
            score, category_findings, category_recommendations, category_gaps = await self._validate_resources(
                unit_conditions, relevant_content
            )
        elif category == "supervision":
            score, category_findings, category_recommendations, category_gaps = await self._validate_supervision(
                unit_conditions, relevant_content
            )
        elif category == "instructions":
            score, category_findings, category_recommendations, category_gaps = await self._validate_instructions(
                unit_conditions, relevant_content
            )
        elif category == "interaction":
            score, category_findings, category_recommendations, category_gaps = await self._validate_interaction(
                unit_conditions, relevant_content
            )
        elif category == "third_party":
            score, category_findings, category_recommendations, category_gaps = await self._validate_third_party(
                unit_conditions, relevant_content
            )
        elif category == "timing":
            score, category_findings, category_recommendations, category_gaps = await self._validate_timing(
                unit_conditions, relevant_content
            )
        
        findings.extend(category_findings)
        recommendations.extend(category_recommendations)
        gaps.extend(category_gaps)
        
        return {
            "score": score,
            "findings": findings,
            "recommendations": recommendations,
            "gaps": [gap.to_dict() for gap in gaps]
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
            "environment": ["environment", "location", "workplace", "setting", "conditions", "simulated", "realistic"],
            "resources": ["resource", "tool", "equipment", "material", "software", "checklist", "rubric"],
            "supervision": ["supervisor", "assessor", "observer", "qualified", "TAE", "oversight", "monitoring"],
            "instructions": ["instruction", "direction", "guideline", "procedure", "step", "requirement", "task"],
            "interaction": ["interaction", "feedback", "question", "discussion", "briefing", "debrief", "communication"],
            "third_party": ["third party", "witness", "employer", "supervisor report", "external", "workplace supervisor"],
            "timing": ["time", "duration", "schedule", "deadline", "frequency", "minutes", "hours", "timeframe"]
        }
        
        keywords = category_keywords.get(category, [])
        content_lower = content.lower()
        
        return any(keyword in content_lower for keyword in keywords)
    
    async def _validate_environment(self, unit_conditions: List[Dict], content: List[str]) -> tuple:
        """Validate assessment environment with semantic analysis"""
        findings = []
        recommendations = []
        gaps = []
        
        if not content:
            gap = ValidationGap(
                gap_type="Missing Environment",
                description="No assessment environment information found in documents",
                recommendation="Add clear description of assessment environment requirements including workplace/simulated conditions",
                confidence_score=0.95,
                category="environment",
                severity="high"
            )
            gaps.append(gap)
            return 30, findings, recommendations, gaps
        
        combined_content = " ".join(content).lower()
        
        environment_keywords = {
            'workplace': ['workplace', 'work site', 'on-site', 'real workplace', 'actual workplace'],
            'simulated': ['simulated', 'simulation', 'mock', 'practice environment', 'training room'],
            'conditions': ['realistic conditions', 'industry conditions', 'authentic conditions'],
            'safety': ['safety', 'safe environment', 'safety requirements', 'safety equipment']
        }
        
        category_scores = {}
        for category, keywords in environment_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in combined_content)
            category_scores[category] = min(100, matches * 25)
        
        specificity_score = self._assess_environment_specificity(combined_content)
        
        overall_score = (
            sum(category_scores.values()) / len(category_scores) * 0.7 +
            specificity_score * 0.3
        )
        
        if self.strictness_level == "strict":
            overall_score *= 0.8
            if specificity_score < 70:
                gap = ValidationGap(
                    gap_type="Vague Environment Description",
                    description="Assessment environment description lacks specific details required for strict validation",
                    recommendation="Provide specific details about location, equipment, and conditions",
                    confidence_score=0.85,
                    category="environment",
                    severity="medium"
                )
                gaps.append(gap)
        elif self.strictness_level == "lenient":
            overall_score *= 1.2
            overall_score = min(100, overall_score)
        
        findings.append(f"Environment analysis: {dict(category_scores)}")
        
        return round(overall_score, 2), findings, recommendations, gaps
    
    async def _validate_resources(self, unit_conditions: List[Dict], content: List[str]) -> tuple:
        """Validate necessary resources"""
        findings = []
        recommendations = []
        gaps = []
        
        if not content:
            gap = ValidationGap(
                gap_type="Missing Resources",
                description="No necessary resources information found in documents",
                recommendation="List required tools, equipment, materials, and software with specific details",
                confidence_score=0.95,
                category="resources",
                severity="high"
            )
            gaps.append(gap)
            return 35, findings, recommendations, gaps
        
        combined_content = " ".join(content).lower()
        
        resource_categories = {
            'tools': ['tool', 'instrument', 'device'],
            'equipment': ['equipment', 'machine', 'apparatus'],
            'materials': ['material', 'supply', 'component'],
            'software': ['software', 'application', 'program', 'system'],
            'documentation': ['manual', 'guide', 'specification', 'standard']
        }
        
        found_categories = 0
        specificity_issues = []
        
        for category, keywords in resource_categories.items():
            if any(keyword in combined_content for keyword in keywords):
                found_categories += 1
                if any(vague in combined_content for vague in ['access to computer', 'appropriate tools', 'suitable equipment']):
                    specificity_issues.append(category)
        
        base_score = (found_categories / len(resource_categories)) * 100
        
        if specificity_issues and self.strictness_level in ["normal", "strict"]:
            gap = ValidationGap(
                gap_type="Vague Resource Description",
                description=f"Resource descriptions are too vague in categories: {', '.join(specificity_issues)}",
                recommendation="Specify exact models, versions, and quantities of required resources",
                confidence_score=0.80,
                category="resources",
                severity="medium"
            )
            gaps.append(gap)
            base_score *= 0.8
        
        if self.strictness_level == "strict":
            base_score *= 0.85
        elif self.strictness_level == "lenient":
            base_score *= 1.15
            base_score = min(100, base_score)
        
        findings.append(f"Found {found_categories}/{len(resource_categories)} resource categories")
        
        return round(base_score, 2), findings, recommendations, gaps
    
    async def _validate_supervision(self, unit_conditions: List[Dict], content: List[str]) -> tuple:
        """Validate supervision and observation requirements"""
        findings = []
        recommendations = []
        gaps = []
        
        if not content:
            gap = ValidationGap(
                gap_type="Missing Supervision",
                description="No supervision and observation information found in documents",
                recommendation="Define assessor qualifications, roles, and observation requirements",
                confidence_score=0.95,
                category="supervision",
                severity="high"
            )
            gaps.append(gap)
            return 30, findings, recommendations, gaps
        
        combined_content = " ".join(content).lower()
        
        supervision_elements = {
            'assessor_qualifications': ['tae40116', 'tae40110', 'qualified assessor', 'cert iv', 'certificate iv'],
            'observation_requirements': ['observe', 'observation', 'monitor', 'supervise', 'oversee'],
            'roles_responsibilities': ['role', 'responsibility', 'duty', 'accountable'],
            'interaction_level': ['direct supervision', 'indirect supervision', 'remote supervision']
        }
        
        found_elements = 0
        for element, keywords in supervision_elements.items():
            if any(keyword in combined_content for keyword in keywords):
                found_elements += 1
        
        base_score = (found_elements / len(supervision_elements)) * 100
        
        if 'assessor' in combined_content and not any(qual in combined_content for qual in supervision_elements['assessor_qualifications']):
            gap = ValidationGap(
                gap_type="Unspecified Assessor Qualifications",
                description="Assessor mentioned but qualifications not specified",
                recommendation="Specify required assessor qualifications (e.g., TAE40116 or equivalent)",
                confidence_score=0.85,
                category="supervision",
                severity="medium"
            )
            gaps.append(gap)
        
        if self.strictness_level == "strict":
            base_score *= 0.85
        elif self.strictness_level == "lenient":
            base_score *= 1.15
            base_score = min(100, base_score)
        
        findings.append(f"Found {found_elements}/{len(supervision_elements)} supervision elements")
        
        return round(base_score, 2), findings, recommendations, gaps
    
    async def _validate_instructions(self, unit_conditions: List[Dict], content: List[str]) -> tuple:
        """Validate Assessment Instructions with clarity, completeness, and consistency checks"""
        findings = []
        recommendations = []
        gaps = []
        
        if not content:
            gap = ValidationGap(
                gap_type="Missing Instructions",
                description="No assessment instructions found in documents",
                recommendation="Add clear, comprehensive assessment instructions for learners",
                confidence_score=0.95,
                category="instructions",
                severity="high"
            )
            gaps.append(gap)
            return 20, findings, recommendations, gaps
        
        combined_content = " ".join(content)
        
        clarity_score = self._analyze_instruction_clarity(combined_content)
        
        completeness_score = self._analyze_instruction_completeness(combined_content, unit_conditions)
        
        consistency_score = self._analyze_instruction_consistency(content)
        
        if clarity_score < 70:
            gap = ValidationGap(
                gap_type="Unclear Instructions",
                description=f"Assessment instructions have clarity issues (score: {clarity_score}/100). Complex sentences or undefined jargon detected.",
                recommendation="Simplify language, define technical terms, and use clear, direct sentences in assessment instructions.",
                confidence_score=0.85,
                category="instructions",
                severity="medium"
            )
            gaps.append(gap)
        
        if completeness_score < 80:
            gap = ValidationGap(
                gap_type="Incomplete Instructions",
                description=f"Assessment instructions are incomplete (score: {completeness_score}/100). Missing essential elements like submission requirements or assessment criteria.",
                recommendation="Ensure instructions cover all steps, submission requirements, deadlines, and assessment criteria.",
                confidence_score=0.90,
                category="instructions",
                severity="high"
            )
            gaps.append(gap)
        
        if consistency_score < 75:
            gap = ValidationGap(
                gap_type="Inconsistent Instructions",
                description=f"Assessment instructions are inconsistent across documents (score: {consistency_score}/100). Contradictions found between materials.",
                recommendation="Review all assessment materials to ensure consistent instructions and requirements.",
                confidence_score=0.80,
                category="instructions",
                severity="medium"
            )
            gaps.append(gap)
        
        base_score = (clarity_score * 0.4 + completeness_score * 0.4 + consistency_score * 0.2)
        
        if self.strictness_level == "strict":
            base_score *= 0.85  # More stringent
        elif self.strictness_level == "lenient":
            base_score *= 1.15  # More generous
            base_score = min(100, base_score)
        
        findings.append(f"Assessment Instructions Analysis: Clarity={clarity_score}, Completeness={completeness_score}, Consistency={consistency_score}")
        
        if not gaps:
            recommendations.append("Assessment instructions meet quality standards")
        
        return round(base_score, 2), findings, recommendations, gaps
    
    async def _validate_interaction(self, unit_conditions: List[Dict], content: List[str]) -> tuple:
        """Validate assessor interaction requirements"""
        findings = []
        recommendations = []
        gaps = []
        
        if not content:
            gap = ValidationGap(
                gap_type="Missing Interaction",
                description="No assessor interaction information found in documents",
                recommendation="Define how and when assessors will interact with students during assessment",
                confidence_score=0.90,
                category="interaction",
                severity="medium"
            )
            gaps.append(gap)
            return 40, findings, recommendations, gaps
        
        combined_content = " ".join(content).lower()
        
        interaction_elements = {
            'feedback': ['feedback', 'comment', 'response', 'review'],
            'questioning': ['question', 'ask', 'inquiry', 'clarification'],
            'briefing': ['briefing', 'pre-assessment', 'introduction', 'explanation'],
            'debriefing': ['debrief', 'post-assessment', 'discussion', 'reflection']
        }
        
        found_elements = 0
        for element, keywords in interaction_elements.items():
            if any(keyword in combined_content for keyword in keywords):
                found_elements += 1
        
        base_score = (found_elements / len(interaction_elements)) * 100
        
        if self.strictness_level == "strict":
            base_score *= 0.85
        elif self.strictness_level == "lenient":
            base_score *= 1.15
            base_score = min(100, base_score)
        
        findings.append(f"Found {found_elements}/{len(interaction_elements)} interaction elements")
        
        return round(base_score, 2), findings, recommendations, gaps
    
    async def _validate_third_party(self, unit_conditions: List[Dict], content: List[str]) -> tuple:
        """Validate third-party reports requirements"""
        findings = []
        recommendations = []
        gaps = []
        
        combined_content = " ".join(content).lower() if content else ""
        
        third_party_keywords = ['third party', 'workplace supervisor', 'employer', 'witness', 'external']
        has_third_party = any(keyword in combined_content for keyword in third_party_keywords)
        
        if not has_third_party:
            base_score = 75  # Neutral score
            findings.append("No third-party reporting requirements identified")
        else:
            guideline_keywords = ['template', 'form', 'guideline', 'instruction', 'procedure']
            has_guidelines = any(keyword in combined_content for keyword in guideline_keywords)
            
            if not has_guidelines:
                gap = ValidationGap(
                    gap_type="Missing Third-Party Guidelines",
                    description="Third-party evidence mentioned but no templates or guidelines provided",
                    recommendation="Provide templates, forms, or clear guidelines for third-party evidence collection",
                    confidence_score=0.85,
                    category="third_party",
                    severity="medium"
                )
                gaps.append(gap)
                base_score = 50
            else:
                base_score = 85
                findings.append("Third-party reporting guidelines present")
        
        if self.strictness_level == "strict":
            base_score *= 0.9
        elif self.strictness_level == "lenient":
            base_score *= 1.1
            base_score = min(100, base_score)
        
        return round(base_score, 2), findings, recommendations, gaps
    
    async def _validate_timing(self, unit_conditions: List[Dict], content: List[str]) -> tuple:
        """Validate time constraints and timing requirements"""
        findings = []
        recommendations = []
        gaps = []
        
        if not content:
            gap = ValidationGap(
                gap_type="Missing Timing",
                description="No timing or time constraint information found in documents",
                recommendation="Specify assessment timing, duration, and any time constraints",
                confidence_score=0.85,
                category="timing",
                severity="medium"
            )
            gaps.append(gap)
            return 45, findings, recommendations, gaps
        
        combined_content = " ".join(content).lower()
        
        timing_elements = {
            'duration': ['duration', 'time limit', 'minutes', 'hours'],
            'deadlines': ['deadline', 'due date', 'submit by', 'completion date'],
            'scheduling': ['schedule', 'appointment', 'booking', 'time slot'],
            'frequency': ['frequency', 'how often', 'regular', 'periodic']
        }
        
        found_elements = 0
        specific_times = []
        
        for element, keywords in timing_elements.items():
            if any(keyword in combined_content for keyword in keywords):
                found_elements += 1
        
        time_patterns = [r'\d+\s*(?:minutes?|hours?|days?)', r'\d+:\d+', r'\d+\s*(?:am|pm)']
        for pattern in time_patterns:
            matches = re.findall(pattern, combined_content)
            specific_times.extend(matches)
        
        base_score = (found_elements / len(timing_elements)) * 100
        
        if specific_times:
            base_score = min(100, base_score + len(specific_times) * 5)
        
        if any(vague in combined_content for vague in ['reasonable time', 'appropriate duration', 'sufficient time']):
            gap = ValidationGap(
                gap_type="Vague Timing",
                description="Timing requirements are too vague or non-specific",
                recommendation="Provide specific time limits, durations, and deadlines",
                confidence_score=0.75,
                category="timing",
                severity="low"
            )
            gaps.append(gap)
            base_score *= 0.9
        
        if self.strictness_level == "strict":
            base_score *= 0.85
        elif self.strictness_level == "lenient":
            base_score *= 1.15
            base_score = min(100, base_score)
        
        findings.append(f"Found {found_elements}/{len(timing_elements)} timing elements, {len(specific_times)} specific times")
        
        return round(base_score, 2), findings, recommendations, gaps
    
    def _assess_environment_specificity(self, content: str) -> float:
        """Assess how specific the environment description is"""
        specificity_indicators = [
            'specific location', 'address', 'room number', 'building',
            'equipment list', 'software version', 'model number',
            'temperature', 'lighting', 'noise level', 'space requirements'
        ]
        
        matches = sum(1 for indicator in specificity_indicators if indicator in content)
        return min(100, matches * 10)
    
    def _analyze_instruction_clarity(self, content: str) -> float:
        """Analyze clarity of assessment instructions using enhanced NLP"""
        if not content:
            return 0
        
        flesch_score = textstat.flesch_reading_ease(content)
        
        sentences = re.split(r'[.!?]+', content)
        complex_sentences = sum(1 for s in sentences if len(s.split()) > 25)
        complexity_penalty = (complex_sentences / len(sentences)) * 30 if sentences else 0
        
        jargon_words = [
            'assessment', 'criteria', 'evidence', 'portfolio', 'competency',
            'benchmark', 'rubric', 'holistic', 'formative', 'summative',
            'authentic', 'validity', 'reliability', 'moderation'
        ]
        jargon_count = sum(content.lower().count(word) for word in jargon_words)
        
        definition_patterns = [
            r'\bmeans\b', r'\brefers to\b', r'\bdefined as\b', r'\bis when\b',
            r'\binvolves\b', r'\binclude[s]?\b', r'\bfor example\b', r'\bsuch as\b'
        ]
        definitions_count = sum(len(re.findall(pattern, content.lower())) for pattern in definition_patterns)
        
        jargon_penalty = max(0, (jargon_count - definitions_count) * 1.5)
        
        passive_patterns = [r'\bis\s+\w+ed\b', r'\bwas\s+\w+ed\b', r'\bwere\s+\w+ed\b', r'\bbeen\s+\w+ed\b']
        passive_count = sum(len(re.findall(pattern, content.lower())) for pattern in passive_patterns)
        passive_penalty = min(15, passive_count * 2)
        
        unclear_pronouns = ['this', 'that', 'these', 'those', 'it']
        pronoun_count = sum(content.lower().count(pronoun) for pronoun in unclear_pronouns)
        pronoun_penalty = min(10, pronoun_count * 0.5)
        
        clarity_score = max(0, min(100, (flesch_score + 100) / 2 - complexity_penalty - jargon_penalty - passive_penalty - pronoun_penalty))
        
        return clarity_score
    
    def _analyze_instruction_completeness(self, content: str, unit_conditions: List[Dict]) -> float:
        """Analyze completeness of assessment instructions"""
        if not content:
            return 0
        
        content_lower = content.lower()
        
        essential_elements = {
            'submission_requirements': ['submit', 'submission', 'due', 'deadline', 'hand in'],
            'assessment_criteria': ['criteria', 'standard', 'benchmark', 'graded', 'marked'],
            'steps_procedures': ['step', 'procedure', 'process', 'method', 'approach'],
            'time_limits': ['time', 'duration', 'minutes', 'hours', 'deadline'],
            'resources_needed': ['resource', 'material', 'equipment', 'tool', 'access'],
            'format_requirements': ['format', 'structure', 'layout', 'presentation', 'style']
        }
        
        present_elements = 0
        for element, keywords in essential_elements.items():
            if any(keyword in content_lower for keyword in keywords):
                present_elements += 1
        
        completeness_score = (present_elements / len(essential_elements)) * 100
        
        return completeness_score
    
    def _analyze_instruction_consistency(self, content_list: List[str]) -> float:
        """Analyze consistency of instructions across multiple documents"""
        if len(content_list) < 2:
            return 100  # Single document is consistent by default
        
        instruction_elements = []
        for content in content_list:
            elements = self._extract_instruction_elements(content)
            instruction_elements.append(elements)
        
        consistency_issues = 0
        total_comparisons = 0
        
        for i in range(len(instruction_elements)):
            for j in range(i + 1, len(instruction_elements)):
                total_comparisons += 1
                if not self._are_instructions_consistent(instruction_elements[i], instruction_elements[j]):
                    consistency_issues += 1
        
        if total_comparisons == 0:
            return 100
        
        consistency_score = max(0, 100 - (consistency_issues / total_comparisons) * 100)
        return consistency_score
    
    def _extract_instruction_elements(self, content: str) -> Dict[str, List[str]]:
        """Extract key instruction elements from content"""
        content_lower = content.lower()
        
        elements = {
            'deadlines': re.findall(r'due\s+(?:by\s+)?(\w+\s+\d+|\d+\s+\w+)', content_lower),
            'submission_methods': re.findall(r'submit\s+(?:via|through|to)\s+(\w+)', content_lower),
            'time_limits': re.findall(r'(\d+)\s+(?:minutes?|hours?)', content_lower),
            'formats': re.findall(r'format\s+(?:should\s+be|must\s+be)\s+(\w+)', content_lower)
        }
        
        return elements
    
    def _are_instructions_consistent(self, elements1: Dict, elements2: Dict) -> bool:
        """Check if instruction elements are consistent between documents"""
        for key in elements1:
            if key in elements2:
                if elements1[key] and elements2[key]:
                    if set(elements1[key]) != set(elements2[key]):
                        return False
        return True
    
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
