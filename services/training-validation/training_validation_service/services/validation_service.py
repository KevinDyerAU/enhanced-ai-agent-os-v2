import asyncio
import logging
from typing import List, Dict, Any, Optional
from schemas.unit_schema import Unit
from schemas.document_schema import ProcessedElement
from services.llm_service import LLMService, llm_service
from integrations.data_architecture_client import DataArchitectureClient
from prompts.validation_prompts import (
    ASSESSMENT_CONDITIONS_PROMPT,
    PERFORMANCE_EVIDENCE_PROMPT,
    KNOWLEDGE_EVIDENCE_PROMPT,
    FOUNDATION_SKILLS_PROMPT,
    EPC_PROMPT
)
import os

logger = logging.getLogger(__name__)

class ValidationService:
    """
    Orchestrates the complete validation of training documents using concurrent
    LLM-driven analysis with prompts from the centralized prompt store.
    Enhanced with vector store context for improved accuracy.
    """
    def __init__(self, llm_service: LLMService, data_architecture_client: Optional[DataArchitectureClient] = None):
        self.llm = llm_service
        self.data_client = data_architecture_client or DataArchitectureClient(
            os.getenv("DATA_ARCHITECTURE_URL", "http://data_architecture:8020")
        )

    def _prepare_context(self, document_elements: List[ProcessedElement], max_tokens: int = 120000) -> str:
        """
        Combines document content into a single string and truncates if necessary.
        """
        full_doc_text = " ".join([elem.text for elem in document_elements])
        if len(full_doc_text) > max_tokens * 4:
            full_doc_text = full_doc_text[:max_tokens * 4]
        return full_doc_text

    async def _get_additional_context(self, unit_data: Unit, document_elements: List[ProcessedElement]) -> str:
        """
        Retrieve additional context from vector store for current documents only.
        """
        try:
            doc_content = self._prepare_context(document_elements)
            document_id = await self.data_client.store_document_context(
                content=doc_content,
                metadata={
                    "content_type": "current_document",
                    "unit_code": unit_data.unit_code,
                    "document_name": document_elements[0].metadata.get("file_name", "N/A") if document_elements else "N/A"
                }
            )
            
            similar_docs = await self.data_client.search_similar_documents(
                query=f"{unit_data.unit_code} {unit_data.unit_title}",
                unit_code=unit_data.unit_code,
                top_k=2
            )
            
            context_parts = []
            if similar_docs:
                context_parts.append("Similar Current Documents:")
                for doc in similar_docs[:2]:
                    context_parts.append(f"- {doc.get('content', '')[:200]}...")
            
            return "\n".join(context_parts) if context_parts else ""
            
        except Exception as e:
            logger.error(f"Error retrieving additional context: {e}")
            return ""

    async def validate_document_fully(self, unit_data: Unit, document_elements: List[ProcessedElement]) -> Dict[str, Any]:
        """
        Runs all validation checks CONCURRENTLY using asyncio and returns a comprehensive report.
        Enhanced with additional context from vector store for current documents.
        """
        doc_context = self._prepare_context(document_elements)
        additional_context = await self._get_additional_context(unit_data, document_elements)

        
        ac_prompt = ASSESSMENT_CONDITIONS_PROMPT

        pe_list_str = "\n".join([f"- {pe}" for pe in unit_data.performance_evidence])
        pe_prompt = PERFORMANCE_EVIDENCE_PROMPT.format(evidence_list=pe_list_str)

        ke_list_str = "\n".join([f"- {ke}" for ke in unit_data.knowledge_evidence])
        ke_prompt = KNOWLEDGE_EVIDENCE_PROMPT.format(evidence_list=ke_list_str)

        fs_list_str = "\n".join([f"- {fs.skill}: {fs.description}" for fs in unit_data.foundation_skills])
        fs_prompt = FOUNDATION_SKILLS_PROMPT.format(evidence_list=fs_list_str)

        epc_list_items = []
        for element in unit_data.elements_and_performance_criteria:
            epc_list_items.append(f"Element: {element.element_description}")
            for pc in element.performance_criteria:
                epc_list_items.append(f"  - PC: {pc}")
        epc_list_str = "\n".join(epc_list_items)
        epc_prompt = EPC_PROMPT.format(evidence_list=epc_list_str)

        context_with_additional = doc_context
        if additional_context:
            context_with_additional = f"{doc_context}\n\nAdditional Context:\n{additional_context}"

        tasks = [
            self.llm.get_json_validation(ac_prompt, context_with_additional),
            self.llm.get_json_validation(pe_prompt, context_with_additional),
            self.llm.get_json_validation(ke_prompt, context_with_additional),
            self.llm.get_json_validation(fs_prompt, context_with_additional),
            self.llm.get_json_validation(epc_prompt, context_with_additional)
        ]
        
        results = await asyncio.gather(*tasks)
        
        ac_results, pe_results, ke_results, fs_results, epc_results = results

        final_report = {
            "unit_code": unit_data.unit_code,
            "document_name": document_elements[0].metadata.get("file_name", "N/A") if document_elements else "N/A",
            "validation_report": {
                "assessment_conditions": ac_results,
                "performance_evidence": pe_results,
                "knowledge_evidence": ke_results,
                "foundation_skills": fs_results,
                "elements_and_performance_criteria": epc_results,
            }
        }
        
        return final_report

    def validate_document(self, unit_data: Unit, document_elements: List[ProcessedElement]) -> Dict[str, Any]:
        """
        Synchronous wrapper for backward compatibility with existing endpoint.
        """
        return asyncio.run(self.validate_document_fully(unit_data, document_elements))

validation_service = ValidationService(llm_service=llm_service)
