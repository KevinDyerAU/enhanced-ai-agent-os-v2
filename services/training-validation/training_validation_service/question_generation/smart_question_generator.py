import logging
from typing import Dict, Any, List, Optional
import json
from openai import OpenAI
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class SMARTQuestionGenerator:
    """Generates SMART questions based on validation findings and training unit requirements"""
    
    def __init__(self):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )
        self.default_model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o")
        self.question_types = [
            "open_ended",
            "multiple_choice", 
            "scenario_based",
            "practical_demonstration",
            "case_study",
            "problem_solving"
        ]
    
    async def generate_questions_from_validation(
        self, 
        validation_results: Dict[str, Any], 
        training_unit: Dict[str, Any],
        question_count: int = 10
    ) -> Dict[str, Any]:
        """Generate SMART questions based on validation results and training unit"""
        logger.info(f"Generating {question_count} SMART questions for unit {training_unit.get('unit_code')}")
        
        try:
            unit_context = self._extract_unit_context(training_unit)
            validation_gaps = self._extract_validation_gaps(validation_results)
            performance_criteria = training_unit.get("performance_criteria", [])
            knowledge_evidence = training_unit.get("knowledge_evidence", [])
            
            questions = []
            
            pc_questions = await self._generate_performance_criteria_questions(
                performance_criteria, unit_context, question_count // 3
            )
            questions.extend(pc_questions)
            
            ke_questions = await self._generate_knowledge_evidence_questions(
                knowledge_evidence, unit_context, question_count // 3
            )
            questions.extend(ke_questions)
            
            gap_questions = await self._generate_gap_based_questions(
                validation_gaps, unit_context, question_count // 3
            )
            questions.extend(gap_questions)
            
            questions = questions[:question_count]
            
            return {
                "unit_code": training_unit.get("unit_code"),
                "generated_at": datetime.utcnow().isoformat(),
                "total_questions": len(questions),
                "questions": questions,
                "generation_metadata": {
                    "performance_criteria_count": len(performance_criteria),
                    "knowledge_evidence_count": len(knowledge_evidence),
                    "validation_gaps_count": len(validation_gaps),
                    "unit_context": unit_context
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating questions: {str(e)}")
            return {
                "error": f"Failed to generate questions: {str(e)}",
                "questions": [],
                "total_questions": 0
            }
    
    def _extract_unit_context(self, training_unit: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant context from training unit for question generation"""
        return {
            "unit_code": training_unit.get("unit_code", ""),
            "unit_title": training_unit.get("unit_title", ""),
            "sector": training_unit.get("sector", ""),
            "qualification_level": training_unit.get("qualification_level", ""),
            "application": training_unit.get("application", ""),
            "elements_count": len(training_unit.get("elements", [])),
            "performance_criteria_count": len(training_unit.get("performance_criteria", [])),
            "knowledge_evidence_count": len(training_unit.get("knowledge_evidence", []))
        }
    
    def _extract_validation_gaps(self, validation_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract validation gaps from all validation engines"""
        all_gaps = []
        
        for engine_name, engine_results in validation_results.items():
            if isinstance(engine_results, dict) and "gaps" in engine_results:
                gaps = engine_results["gaps"]
                if isinstance(gaps, list):
                    for gap in gaps:
                        if isinstance(gap, dict):
                            gap["source_engine"] = engine_name
                            all_gaps.append(gap)
        
        return all_gaps
    
    async def _generate_performance_criteria_questions(
        self, 
        performance_criteria: List[Dict], 
        unit_context: Dict[str, Any], 
        count: int
    ) -> List[Dict[str, Any]]:
        """Generate questions based on performance criteria"""
        if not performance_criteria or count <= 0:
            return []
        
        try:
            prompt = self._build_performance_criteria_prompt(performance_criteria, unit_context, count)
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert training assessment designer specializing in creating SMART questions for vocational education."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            questions_text = response.choices[0].message.content
            questions = self._parse_generated_questions(questions_text, "performance_criteria")
            
            return questions[:count]
            
        except Exception as e:
            logger.error(f"Error generating performance criteria questions: {str(e)}")
            return []
    
    async def _generate_knowledge_evidence_questions(
        self, 
        knowledge_evidence: List[Dict], 
        unit_context: Dict[str, Any], 
        count: int
    ) -> List[Dict[str, Any]]:
        """Generate questions based on knowledge evidence requirements"""
        if not knowledge_evidence or count <= 0:
            return []
        
        try:
            prompt = self._build_knowledge_evidence_prompt(knowledge_evidence, unit_context, count)
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert training assessment designer specializing in knowledge-based questions for vocational education."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            questions_text = response.choices[0].message.content
            questions = self._parse_generated_questions(questions_text, "knowledge_evidence")
            
            return questions[:count]
            
        except Exception as e:
            logger.error(f"Error generating knowledge evidence questions: {str(e)}")
            return []
    
    async def _generate_gap_based_questions(
        self, 
        validation_gaps: List[Dict], 
        unit_context: Dict[str, Any], 
        count: int
    ) -> List[Dict[str, Any]]:
        """Generate questions to address validation gaps"""
        if not validation_gaps or count <= 0:
            return []
        
        try:
            prompt = self._build_gap_based_prompt(validation_gaps, unit_context, count)
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert training assessment designer specializing in addressing training material gaps through targeted questions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            questions_text = response.choices[0].message.content
            questions = self._parse_generated_questions(questions_text, "gap_based")
            
            return questions[:count]
            
        except Exception as e:
            logger.error(f"Error generating gap-based questions: {str(e)}")
            return []
    
    def _build_performance_criteria_prompt(
        self, 
        performance_criteria: List[Dict], 
        unit_context: Dict[str, Any], 
        count: int
    ) -> str:
        """Build prompt for performance criteria questions"""
        criteria_text = "\n".join([f"- {str(pc)}" for pc in performance_criteria[:5]])  # Limit to first 5
        
        return f"""
Create {count} SMART assessment questions for the training unit "{unit_context['unit_code']} - {unit_context['unit_title']}" 
in the {unit_context['sector']} sector.

Performance Criteria to address:
{criteria_text}

Requirements:
1. Questions must be SMART (Specific, Measurable, Achievable, Relevant, Time-bound)
2. Include a mix of question types: open-ended, multiple-choice, scenario-based
3. Each question should directly assess one or more performance criteria
4. Provide benchmark answers and assessment guidance
5. Include difficulty level (Beginner, Intermediate, Advanced)

Format each question as JSON with these fields:
- question_id: unique identifier
- question_type: type of question
- question_text: the actual question
- difficulty_level: Beginner/Intermediate/Advanced
- performance_criteria_addressed: list of criteria this question addresses
- benchmark_answer: expected answer or key points
- assessment_guidance: how to evaluate the response
- time_allocation: suggested time in minutes

Return only valid JSON array of questions.
"""
    
    def _build_knowledge_evidence_prompt(
        self, 
        knowledge_evidence: List[Dict], 
        unit_context: Dict[str, Any], 
        count: int
    ) -> str:
        """Build prompt for knowledge evidence questions"""
        ke_text = "\n".join([f"- {str(ke)}" for ke in knowledge_evidence[:5]])  # Limit to first 5
        
        return f"""
Create {count} knowledge-based assessment questions for the training unit "{unit_context['unit_code']} - {unit_context['unit_title']}" 
in the {unit_context['sector']} sector.

Knowledge Evidence requirements:
{ke_text}

Requirements:
1. Questions must test theoretical understanding and knowledge application
2. Include various formats: multiple-choice, short answer, case studies
3. Each question should assess specific knowledge evidence requirements
4. Provide detailed benchmark answers
5. Include assessment rubrics

Format each question as JSON with these fields:
- question_id: unique identifier
- question_type: type of question
- question_text: the actual question
- difficulty_level: Beginner/Intermediate/Advanced
- knowledge_evidence_addressed: list of KE requirements this question addresses
- benchmark_answer: expected answer or key points
- assessment_guidance: how to evaluate the response
- time_allocation: suggested time in minutes

Return only valid JSON array of questions.
"""
    
    def _build_gap_based_prompt(
        self, 
        validation_gaps: List[Dict], 
        unit_context: Dict[str, Any], 
        count: int
    ) -> str:
        """Build prompt for gap-based questions"""
        gaps_text = "\n".join([f"- {gap.get('description', '')} (Type: {gap.get('gap_type', '')})" 
                              for gap in validation_gaps[:5]])  # Limit to first 5
        
        return f"""
Create {count} targeted assessment questions to address identified gaps in training materials for unit 
"{unit_context['unit_code']} - {unit_context['unit_title']}" in the {unit_context['sector']} sector.

Identified Gaps:
{gaps_text}

Requirements:
1. Questions should specifically address the identified gaps
2. Help learners demonstrate competency in areas where materials are weak
3. Include practical scenarios and real-world applications
4. Provide comprehensive assessment guidance
5. Focus on closing the identified gaps

Format each question as JSON with these fields:
- question_id: unique identifier
- question_type: type of question
- question_text: the actual question
- difficulty_level: Beginner/Intermediate/Advanced
- gaps_addressed: list of gap types this question addresses
- benchmark_answer: expected answer or key points
- assessment_guidance: how to evaluate the response
- time_allocation: suggested time in minutes

Return only valid JSON array of questions.
"""
    
    def _parse_generated_questions(self, questions_text: str, source_type: str) -> List[Dict[str, Any]]:
        """Parse generated questions from OpenAI response"""
        try:
            questions_text = questions_text.strip()
            
            if questions_text.startswith("```json"):
                questions_text = questions_text[7:]
            if questions_text.startswith("```"):
                questions_text = questions_text[3:]
            if questions_text.endswith("```"):
                questions_text = questions_text[:-3]
            
            questions_data = json.loads(questions_text)
            
            if isinstance(questions_data, dict):
                questions_data = [questions_data]
            
            for i, question in enumerate(questions_data):
                question["source_type"] = source_type
                question["generated_at"] = datetime.utcnow().isoformat()
                if "question_id" not in question:
                    question["question_id"] = f"{source_type}_{i+1}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            return questions_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse generated questions JSON: {str(e)}")
            return self._create_fallback_questions(questions_text, source_type)
        except Exception as e:
            logger.error(f"Error parsing generated questions: {str(e)}")
            return []
    
    def _create_fallback_questions(self, text: str, source_type: str) -> List[Dict[str, Any]]:
        """Create fallback questions when JSON parsing fails"""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        questions = []
        
        for i, line in enumerate(lines[:5]):  # Limit to 5 fallback questions
            if len(line) > 20:  # Only use substantial lines
                question = {
                    "question_id": f"fallback_{source_type}_{i+1}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    "question_type": "open_ended",
                    "question_text": line,
                    "difficulty_level": "Intermediate",
                    "source_type": source_type,
                    "benchmark_answer": "Answer should demonstrate understanding of the topic.",
                    "assessment_guidance": "Evaluate based on accuracy, completeness, and practical application.",
                    "time_allocation": 10,
                    "generated_at": datetime.utcnow().isoformat(),
                    "fallback_generation": True
                }
                questions.append(question)
        
        return questions
