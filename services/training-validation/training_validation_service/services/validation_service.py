from typing import List, Dict, Any
from schemas.unit_schema import Unit
from schemas.document_schema import ProcessedElement
from services.llm_service import LLMService, llm_service
from prompts.validation_prompts import (
    ASSESSMENT_CONDITIONS_PROMPT,
    PERFORMANCE_EVIDENCE_PROMPT,
    KNOWLEDGE_EVIDENCE_PROMPT,
    ELEMENTS_PERFORMANCE_CRITERIA_PROMPT,
)

class ValidationService:
    """
    Orchestrates the validation of training documents using LLM-driven analysis
    with prompts from the centralized prompt store.
    """
    def __init__(self, llm_service: LLMService):
        self.llm = llm_service

    def _prepare_context(self, document_elements: List[ProcessedElement], max_tokens: int = 120000) -> str:
        """
        Combines document content into a single string and truncates if necessary
        to fit within the LLM's context window.
        """
        full_doc_text = " ".join([elem.text for elem in document_elements])
        if len(full_doc_text.split()) > max_tokens * 0.75: # A rough token estimation
            return " ".join(full_doc_text.split()[:int(max_tokens * 0.75)])
        return full_doc_text

    def validate_document(self, unit_data: Unit, document_elements: List[ProcessedElement]) -> Dict[str, Any]:
        """
        Runs all validation checks using the LLM and returns a comprehensive report.
        """
        doc_context = self._prepare_context(document_elements)

        pe_list_str = "\n".join([f"- {pe}" for pe in unit_data.performance_evidence])
        pe_prompt = PERFORMANCE_EVIDENCE_PROMPT.format(evidence_list=pe_list_str)
        pe_results = self.llm.get_json_validation(pe_prompt, doc_context)

        ac_results = self.llm.get_json_validation(ASSESSMENT_CONDITIONS_PROMPT, doc_context)

        ke_list_str = "\n".join([f"- {ke}" for ke in unit_data.knowledge_evidence])
        ke_prompt = KNOWLEDGE_EVIDENCE_PROMPT.format(evidence_list=ke_list_str)
        ke_results = self.llm.get_json_validation(ke_prompt, doc_context)

        criteria_list = []
        for element in unit_data.elements_and_performance_criteria:
            for pc in element.performance_criteria:
                criteria_list.append(f"Element: {element.element_title} | Performance Criterion: {pc}")
        criteria_list_str = "\n".join([f"- {criteria}" for criteria in criteria_list])
        epc_prompt = ELEMENTS_PERFORMANCE_CRITERIA_PROMPT.format(criteria_list=criteria_list_str)
        epc_results = self.llm.get_json_validation(epc_prompt, doc_context)

        final_report = {
            "unit_code": unit_data.unit_code,
            "document_name": document_elements[0].metadata.get("file_name", "N/A") if document_elements else "N/A",
            "validation_summary": {
                "performance_evidence": pe_results,
                "assessment_conditions": ac_results,
                "knowledge_evidence": ke_results,
                "elements_and_performance_criteria": epc_results,
            }
        }
        
        return final_report

validation_service = ValidationService(llm_service=llm_service)
