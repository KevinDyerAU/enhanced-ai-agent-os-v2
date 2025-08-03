import logging
from typing import Dict, Any, List, Optional
import json
import asyncpg
from datetime import datetime
import os
import uuid

logger = logging.getLogger(__name__)

class QuestionManager:
    """Manages question library with organizing, categorizing, and searching capabilities"""
    
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/aos_db")
    
    async def save_questions(
        self, 
        questions: List[Dict[str, Any]], 
        session_id: str,
        unit_code: str
    ) -> Dict[str, Any]:
        """Save generated questions to the database"""
        logger.info(f"Saving {len(questions)} questions for unit {unit_code}")
        
        try:
            conn = await asyncpg.connect(self.db_url)
            
            saved_questions = []
            for question in questions:
                question_id = await conn.fetchval("""
                    INSERT INTO generated_questions (
                        session_id, training_unit_id, question_type, category, question_text,
                        difficulty_level, benchmark_answer, assessment_guidance,
                        metadata, created_at
                    ) VALUES ($1, (SELECT training_unit_id FROM validation_sessions WHERE id = $1), $2, $3, $4, $5, $6, $7, $8, $9)
                    RETURNING id
                """, 
                    uuid.UUID(session_id),
                    question.get("question_type", "open_ended"),
                    question.get("category", "knowledge_evidence"),
                    question.get("question_text", ""),
                    question.get("difficulty_level", "medium"),
                    question.get("benchmark_answer", ""),
                    question.get("assessment_guidance", ""),
                    json.dumps(question),
                    datetime.utcnow()
                )
                
                question["id"] = question_id
                saved_questions.append(question)
            
            await conn.close()
            
            return {
                "success": True,
                "saved_count": len(saved_questions),
                "questions": saved_questions
            }
            
        except Exception as e:
            logger.error(f"Error saving questions: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "saved_count": 0
            }
    
    async def get_questions_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieve questions by validation session"""
        try:
            conn = await asyncpg.connect(self.db_url)
            
            rows = await conn.fetch("""
                SELECT id, session_id, training_unit_id, question_type, category, question_text,
                       difficulty_level, benchmark_answer, assessment_guidance,
                       metadata, created_at, review_status
                FROM generated_questions 
                WHERE session_id = $1
                ORDER BY created_at DESC
            """, uuid.UUID(session_id))
            
            await conn.close()
            
            questions = []
            for row in rows:
                question = dict(row)
                if question["metadata"]:
                    try:
                        metadata = json.loads(question["metadata"])
                        question.update(metadata)
                    except json.JSONDecodeError:
                        pass
                questions.append(question)
            
            return questions
            
        except Exception as e:
            logger.error(f"Error retrieving questions for session {session_id}: {str(e)}")
            return []
    
    async def get_questions_by_unit(self, unit_code: str) -> List[Dict[str, Any]]:
        """Retrieve questions by unit code"""
        try:
            conn = await asyncpg.connect(self.db_url)
            
            rows = await conn.fetch("""
                SELECT gq.id, gq.session_id, gq.training_unit_id, gq.question_type, gq.category, gq.question_text,
                       gq.difficulty_level, gq.benchmark_answer, gq.assessment_guidance,
                       gq.metadata, gq.created_at, gq.review_status
                FROM generated_questions gq
                JOIN training_units tu ON gq.training_unit_id = tu.id
                WHERE tu.unit_code = $1
                ORDER BY gq.created_at DESC
            """, unit_code)
            
            await conn.close()
            
            questions = []
            for row in rows:
                question = dict(row)
                if question["metadata"]:
                    try:
                        metadata = json.loads(question["metadata"])
                        question.update(metadata)
                    except json.JSONDecodeError:
                        pass
                questions.append(question)
            
            return questions
            
        except Exception as e:
            logger.error(f"Error retrieving questions for unit {unit_code}: {str(e)}")
            return []
    
    async def search_questions(
        self, 
        query: str, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search questions with filters"""
        try:
            conn = await asyncpg.connect(self.db_url)
            
            where_conditions = ["question_text ILIKE $1"]
            params = [f"%{query}%"]
            param_count = 1
            
            if filters:
                if filters.get("unit_code"):
                    param_count += 1
                    where_conditions.append(f"tu.unit_code = ${param_count}")
                    params.append(filters["unit_code"])
                
                if filters.get("question_type"):
                    param_count += 1
                    where_conditions.append(f"gq.question_type = ${param_count}")
                    params.append(filters["question_type"])
                
                if filters.get("difficulty_level"):
                    param_count += 1
                    where_conditions.append(f"gq.difficulty_level = ${param_count}")
                    params.append(filters["difficulty_level"])
                
                if filters.get("category"):
                    param_count += 1
                    where_conditions.append(f"gq.category = ${param_count}")
                    params.append(filters["category"])
            
            query_sql = f"""
                SELECT gq.id, gq.session_id, gq.training_unit_id, gq.question_type, gq.category, gq.question_text,
                       gq.difficulty_level, gq.benchmark_answer, gq.assessment_guidance,
                       gq.metadata, gq.created_at, gq.review_status, tu.unit_code
                FROM generated_questions gq
                LEFT JOIN training_units tu ON gq.training_unit_id = tu.id
                WHERE {' AND '.join(where_conditions)}
                ORDER BY gq.created_at DESC
                LIMIT 50
            """
            
            rows = await conn.fetch(query_sql, *params)
            await conn.close()
            
            questions = []
            for row in rows:
                question = dict(row)
                if question["metadata"]:
                    try:
                        metadata = json.loads(question["metadata"])
                        question.update(metadata)
                    except json.JSONDecodeError:
                        pass
                questions.append(question)
            
            return questions
            
        except Exception as e:
            logger.error(f"Error searching questions: {str(e)}")
            return []
    
    async def update_question_status(
        self, 
        question_id: int, 
        status: str, 
        review_status: Optional[str] = None
    ) -> bool:
        """Update question status and review status"""
        try:
            conn = await asyncpg.connect(self.db_url)
            
            if review_status:
                await conn.execute("""
                    UPDATE generated_questions 
                    SET review_status = $1, reviewed_at = $2
                    WHERE id = $3
                """, review_status, datetime.utcnow(), question_id)
            else:
                await conn.execute("""
                    UPDATE generated_questions 
                    SET review_status = $1, reviewed_at = $2
                    WHERE id = $3
                """, status, datetime.utcnow(), question_id)
            
            await conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error updating question status: {str(e)}")
            return False
    
    async def get_question_statistics(self) -> Dict[str, Any]:
        """Get question library statistics"""
        try:
            conn = await asyncpg.connect(self.db_url)
            
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_questions,
                    COUNT(DISTINCT training_unit_id) as unique_units,
                    COUNT(DISTINCT session_id) as unique_sessions,
                    COUNT(CASE WHEN review_status = 'approved' THEN 1 END) as approved_questions,
                    COUNT(CASE WHEN review_status = 'pending' THEN 1 END) as pending_questions,
                    COUNT(CASE WHEN review_status = 'rejected' THEN 1 END) as rejected_questions
                FROM generated_questions
            """)
            
            type_stats = await conn.fetch("""
                SELECT question_type, COUNT(*) as count
                FROM generated_questions
                GROUP BY question_type
                ORDER BY count DESC
            """)
            
            difficulty_stats = await conn.fetch("""
                SELECT difficulty_level, COUNT(*) as count
                FROM generated_questions
                GROUP BY difficulty_level
                ORDER BY count DESC
            """)
            
            await conn.close()
            
            return {
                "total_statistics": dict(stats),
                "question_types": [dict(row) for row in type_stats],
                "difficulty_levels": [dict(row) for row in difficulty_stats]
            }
            
        except Exception as e:
            logger.error(f"Error getting question statistics: {str(e)}")
            return {}
    
    async def export_questions(
        self, 
        format_type: str = "json",
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Export questions in specified format"""
        try:
            if filters:
                if filters.get("session_id"):
                    questions = await self.get_questions_by_session(filters["session_id"])
                elif filters.get("unit_code"):
                    questions = await self.get_questions_by_unit(filters["unit_code"])
                else:
                    questions = await self.search_questions("", filters)
            else:
                questions = await self.search_questions("")
            
            if format_type.lower() == "json":
                return {
                    "format": "json",
                    "data": questions,
                    "count": len(questions)
                }
            elif format_type.lower() == "csv":
                csv_data = self._convert_to_csv(questions)
                return {
                    "format": "csv",
                    "data": csv_data,
                    "count": len(questions)
                }
            else:
                return {
                    "error": f"Unsupported format: {format_type}",
                    "supported_formats": ["json", "csv"]
                }
                
        except Exception as e:
            logger.error(f"Error exporting questions: {str(e)}")
            return {"error": str(e)}
    
    def _convert_to_csv(self, questions: List[Dict[str, Any]]) -> str:
        """Convert questions to CSV format"""
        if not questions:
            return ""
        
        headers = [
            "id", "session_id", "question_type", "category", "question_text", 
            "difficulty_level", "benchmark_answer", "assessment_guidance",
            "review_status", "created_at"
        ]
        
        csv_lines = [",".join(headers)]
        
        for question in questions:
            row = []
            for header in headers:
                value = str(question.get(header, "")).replace('"', '""')  # Escape quotes
                if "," in value or '"' in value or "\n" in value:
                    value = f'"{value}"'  # Quote if contains special chars
                row.append(value)
            csv_lines.append(",".join(row))
        
        return "\n".join(csv_lines)
