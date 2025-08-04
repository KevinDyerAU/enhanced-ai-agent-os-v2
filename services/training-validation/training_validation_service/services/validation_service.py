from schemas.unit_schema import Unit
from schemas.document_schema import ProcessedElement
from typing import List, Dict, Any

class ValidationService:
    """
    Orchestrates the validation of training documents against official unit requirements.
    """
    def validate_document(self, unit_data: Unit, document_elements: List[ProcessedElement]) -> Dict[str, Any]:
        """
        Runs all validation checks and returns a comprehensive report.
        """
        validation_results = {
            "summary": {},
            "assessment_conditions": self._validate_assessment_conditions(unit_data, document_elements),
            "elements_and_performance_criteria": self._validate_epc(unit_data, document_elements),
            "performance_evidence": self._validate_performance_evidence(unit_data, document_elements),
            "knowledge_evidence": self._validate_knowledge_evidence(unit_data, document_elements),
        }
        
        return validation_results

    def _validate_assessment_conditions(self, unit_data: Unit, doc_elements: List[ProcessedElement]) -> Dict[str, Any]:
        gaps = []
        full_doc_text = " ".join([elem.text for elem in doc_elements]).lower()

        required_text = unit_data.assessment_conditions.description
        if not required_text:
            pass
        elif required_text.lower() not in full_doc_text:
            gaps.append({
                "type": "Missing Assessment Condition",
                "detail": f"The document does not appear to contain the required assessment conditions: '{required_text[:100]}...'",
                "recommendation": "Ensure the specific assessment conditions from training.gov.au are included and addressed in your assessment materials."
            })

        instruction_keywords = ["instructions", "procedure", "what you need to do", "task steps"]
        has_instructions = any(keyword in full_doc_text for keyword in instruction_keywords)
        
        if not has_instructions:
            gaps.append({
                "type": "Missing Assessment Instructions",
                "detail": "The document does not seem to contain a clear section for assessment instructions or procedures.",
                "recommendation": "Add a clear, step-by-step section detailing the instructions for the learner."
            })

        status = "Gaps Found" if gaps else "Passed"
        return {"status": status, "gaps": gaps}

    def _validate_epc(self, unit_data: Unit, doc_elements: List[ProcessedElement]) -> Dict[str, Any]:
        gaps = []
        full_doc_text = " ".join([elem.text for elem in doc_elements]).lower()
        
        for element in unit_data.elements_and_performance_criteria:
            for pc in element.performance_criteria:
                pc_text = pc.lower()
                if pc_text not in full_doc_text:
                    gaps.append({
                        "type": "Missing Performance Criterion",
                        "detail": f"The assessment does not seem to address the performance criterion: '{pc}'",
                        "recommendation": f"Ensure there is an assessment task that requires the student to demonstrate '{pc}'."
                    })

        status = "Gaps Found" if gaps else "Passed"
        return {"status": status, "gaps": gaps, "total_criteria": len(unit_data.elements_and_performance_criteria)}

    def _validate_performance_evidence(self, unit_data: Unit, doc_elements: List[ProcessedElement]) -> Dict[str, Any]:
        gaps = []
        full_doc_text = " ".join([elem.text for elem in doc_elements]).lower()

        for pe in unit_data.performance_evidence:
            pe_text = pe.lower()
            if pe_text not in full_doc_text:
                gaps.append({
                    "type": "Missing Performance Evidence",
                    "detail": f"The assessment tasks do not appear to generate the required performance evidence: '{pe}'",
                    "recommendation": f"Design an assessment task where the student must produce evidence for '{pe}'."
                })

        status = "Gaps Found" if gaps else "Passed"
        return {"status": status, "gaps": gaps}

    def _validate_knowledge_evidence(self, unit_data: Unit, doc_elements: List[ProcessedElement]) -> Dict[str, Any]:
        gaps = []
        full_doc_text = " ".join([elem.text for elem in doc_elements]).lower()

        for ke in unit_data.knowledge_evidence:
            ke_text = ke.lower()
            if ke_text not in full_doc_text:
                gaps.append({
                    "type": "Missing Knowledge Evidence",
                    "detail": f"The document does not appear to cover or assess the required knowledge: '{ke}'",
                    "recommendation": f"Ensure your learner guide contains content on '{ke}' or that there is a knowledge question assessing it."
                })

        status = "Gaps Found" if gaps else "Passed"
        return {"status": status, "gaps": gaps}

validation_service = ValidationService()
