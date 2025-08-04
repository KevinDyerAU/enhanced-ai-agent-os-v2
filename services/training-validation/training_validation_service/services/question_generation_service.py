import asyncio
import logging
from typing import List, Dict, Any, Optional
from schemas.unit_schema import Unit
from schemas.document_schema import ProcessedElement
from services.llm_service import LLMService, llm_service
from integrations.data_architecture_client import DataArchitectureClient
import os

logger = logging.getLogger(__name__)

class QuestionGenerationService:
    """
    Dedicated service for generating assessment questions based on validation gaps.
    Enhanced with contextual information from vector store for current documents.
    """
    def __init__(self, llm_service: LLMService, data_architecture_client: Optional[DataArchitectureClient] = None):
        self.llm = llm_service
        self.data_client = data_architecture_client or DataArchitectureClient(
            os.getenv("DATA_ARCHITECTURE_URL", "http://data_architecture:8020")
        )

    async def _get_question_context(self, unit_data: Unit, gap_type: str) -> str:
        """
        Retrieve contextual information for better question generation from current documents.
        """
        try:
            query = f"{unit_data.unit_code} {gap_type} assessment questions examples"
            
            similar_questions = await self.data_client.search_similar_documents(
                query=query,
                unit_code=unit_data.unit_code,
                top_k=2
            )
            
            if similar_questions:
                context_parts = ["Similar Assessment Examples:"]
                for doc in similar_questions[:2]:
                    context_parts.append(f"- {doc.get('content', '')[:150]}...")
                return "\n".join(context_parts)
            
            return ""
            
        except Exception as e:
            logger.error(f"Error retrieving question context: {e}")
            return ""

    async def generate_questions_for_gaps(self, unit_data: Unit, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate assessment questions for identified validation gaps.
        Enhanced with additional context from vector store.
        """
        question_generation_tasks = []
        
        if "performance_evidence" in validation_results:
            pe_gaps = [item for item in validation_results["performance_evidence"].get("performance_evidence_validation", []) 
                      if item.get("status") != "Met"]
            if pe_gaps:
                question_generation_tasks.append(
                    self._generate_performance_questions(pe_gaps, unit_data)
                )

        if "knowledge_evidence" in validation_results:
            ke_gaps = [item for item in validation_results["knowledge_evidence"].get("knowledge_evidence_validation", [])
                      if item.get("status") != "Met"]
            if ke_gaps:
                question_generation_tasks.append(
                    self._generate_knowledge_questions(ke_gaps, unit_data)
                )

        if "foundation_skills" in validation_results:
            fs_gaps = [item for item in validation_results["foundation_skills"].get("foundation_skills_validation", [])
                      if item.get("status") != "Met"]
            if fs_gaps:
                question_generation_tasks.append(
                    self._generate_foundation_skills_questions(fs_gaps, unit_data)
                )

        if "elements_and_performance_criteria" in validation_results:
            epc_gaps = [item for item in validation_results["elements_and_performance_criteria"].get("epc_validation", [])
                       if item.get("status") != "Met"]
            if epc_gaps:
                question_generation_tasks.append(
                    self._generate_epc_questions(epc_gaps, unit_data)
                )

        if question_generation_tasks:
            generated_questions = await asyncio.gather(*question_generation_tasks)
            return {
                "unit_code": unit_data.unit_code,
                "generated_questions": {
                    "performance_evidence": generated_questions[0] if len(generated_questions) > 0 else [],
                    "knowledge_evidence": generated_questions[1] if len(generated_questions) > 1 else [],
                    "foundation_skills": generated_questions[2] if len(generated_questions) > 2 else [],
                    "elements_and_performance_criteria": generated_questions[3] if len(generated_questions) > 3 else []
                }
            }
        
        return {"unit_code": unit_data.unit_code, "generated_questions": {}}

    async def _generate_performance_questions(self, gaps: List[Dict], unit_data: Unit) -> List[Dict]:
        """Generate practical assessment tasks for performance evidence gaps."""
        context = await self._get_question_context(unit_data, "performance evidence")
        
        prompt = f"""
        Generate practical assessment tasks for the following Performance Evidence gaps:
        {gaps}
        
        For each gap, create:
        1. A SMART practical task
        2. A multiple choice question
        3. Benchmark answers for both
        
        Return JSON with structured questions.
        """
        return await self.llm.get_json_validation(prompt, context)

    async def _generate_knowledge_questions(self, gaps: List[Dict], unit_data: Unit) -> List[Dict]:
        """Generate knowledge assessment questions for knowledge evidence gaps."""
        context = await self._get_question_context(unit_data, "knowledge evidence")
        
        prompt = f"""
        Generate knowledge assessment questions for the following Knowledge Evidence gaps:
        {gaps}
        
        For each gap, create:
        1. An open-ended knowledge question
        2. A multiple choice question
        3. Benchmark answers for both
        
        Return JSON with structured questions.
        """
        return await self.llm.get_json_validation(prompt, context)

    async def _generate_foundation_skills_questions(self, gaps: List[Dict], unit_data: Unit) -> List[Dict]:
        """Generate foundation skills assessment tasks."""
        context = await self._get_question_context(unit_data, "foundation skills")
        
        prompt = f"""
        Generate foundation skills assessment tasks for the following gaps:
        {gaps}
        
        For each gap, create practical tasks that integrate the foundation skill naturally.
        
        Return JSON with structured tasks.
        """
        return await self.llm.get_json_validation(prompt, context)

    async def _generate_epc_questions(self, gaps: List[Dict], unit_data: Unit) -> List[Dict]:
        """Generate assessment tasks for Elements and Performance Criteria gaps."""
        context = await self._get_question_context(unit_data, "elements and performance criteria")
        
        prompt = f"""
        Generate assessment tasks for the following Elements and Performance Criteria gaps:
        {gaps}
        
        For each gap, create practical assessment tasks that directly measure the performance criterion.
        
        Return JSON with structured tasks.
        """
        return await self.llm.get_json_validation(prompt, context)

question_generation_service = QuestionGenerationService(llm_service=llm_service)
