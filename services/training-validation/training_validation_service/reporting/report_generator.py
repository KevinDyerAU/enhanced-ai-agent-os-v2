import logging
from typing import Dict, Any, List, Optional
import json
from datetime import datetime
from jinja2 import Template
import os

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Generates detailed validation reports in various formats"""
    
    def __init__(self):
        self.report_templates = {
            "markdown": self._get_markdown_template(),
            "html": self._get_html_template(),
            "summary": self._get_summary_template()
        }
    
    async def generate_comprehensive_report(
        self, 
        validation_results: Dict[str, Any],
        training_unit: Dict[str, Any],
        session_data: Dict[str, Any],
        questions: Optional[List[Dict[str, Any]]] = None,
        format_type: str = "markdown"
    ) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        logger.info(f"Generating comprehensive report for unit {training_unit.get('unit_code')} in {format_type} format")
        
        try:
            report_data = self._prepare_report_data(
                validation_results, training_unit, session_data, questions
            )
            
            if format_type.lower() == "markdown":
                report_content = self._generate_markdown_report(report_data)
            elif format_type.lower() == "html":
                report_content = self._generate_html_report(report_data)
            elif format_type.lower() == "summary":
                report_content = self._generate_summary_report(report_data)
            else:
                return {"error": f"Unsupported format: {format_type}"}
            
            return {
                "success": True,
                "format": format_type,
                "content": report_content,
                "metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "unit_code": training_unit.get("unit_code"),
                    "session_id": session_data.get("id"),
                    "total_pages": self._estimate_pages(report_content),
                    "word_count": len(report_content.split())
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return {"error": str(e)}
    
    def _prepare_report_data(
        self, 
        validation_results: Dict[str, Any],
        training_unit: Dict[str, Any],
        session_data: Dict[str, Any],
        questions: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Prepare data for report generation"""
        
        overall_score = validation_results.get("overall_score", 0)
        compliance_level = self._determine_compliance_level(overall_score)
        
        engine_results = {}
        total_gaps = 0
        high_priority_gaps = []
        
        for engine_name, results in validation_results.items():
            if isinstance(results, dict) and "overall_score" in results:
                engine_results[engine_name] = results
                
                gaps = results.get("gaps", [])
                total_gaps += len(gaps)
                
                for gap in gaps:
                    if isinstance(gap, dict) and gap.get("severity") == "high":
                        gap["source_engine"] = engine_name
                        high_priority_gaps.append(gap)
        
        questions_summary = {}
        if questions:
            questions_summary = {
                "total_questions": len(questions),
                "by_type": self._group_questions_by_type(questions),
                "by_difficulty": self._group_questions_by_difficulty(questions),
                "by_source": self._group_questions_by_source(questions)
            }
        
        return {
            "unit_info": {
                "code": training_unit.get("unit_code", ""),
                "title": training_unit.get("unit_title", ""),
                "sector": training_unit.get("sector", ""),
                "qualification_level": training_unit.get("qualification_level", ""),
                "elements_count": len(training_unit.get("elements", [])),
                "performance_criteria_count": len(training_unit.get("performance_criteria", [])),
                "knowledge_evidence_count": len(training_unit.get("knowledge_evidence", []))
            },
            "session_info": {
                "id": session_data.get("id", ""),
                "created_at": session_data.get("created_at", ""),
                "status": session_data.get("status", ""),
                "strictness_level": session_data.get("strictness_level", "normal"),
                "documents_count": len(session_data.get("documents", []))
            },
            "validation_summary": {
                "overall_score": overall_score,
                "compliance_level": compliance_level,
                "total_engines": len(engine_results),
                "total_gaps": total_gaps,
                "high_priority_gaps_count": len(high_priority_gaps)
            },
            "engine_results": engine_results,
            "high_priority_gaps": high_priority_gaps,
            "questions_summary": questions_summary,
            "questions": questions or [],
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def _generate_markdown_report(self, report_data: Dict[str, Any]) -> str:
        """Generate markdown format report"""
        template = Template(self.report_templates["markdown"])
        return template.render(**report_data)
    
    def _generate_html_report(self, report_data: Dict[str, Any]) -> str:
        """Generate HTML format report"""
        template = Template(self.report_templates["html"])
        return template.render(**report_data)
    
    def _generate_summary_report(self, report_data: Dict[str, Any]) -> str:
        """Generate summary format report"""
        template = Template(self.report_templates["summary"])
        return template.render(**report_data)
    
    def _determine_compliance_level(self, score: float) -> str:
        """Determine compliance level based on score"""
        if score >= 90:
            return "Excellent"
        elif score >= 80:
            return "Good"
        elif score >= 70:
            return "Satisfactory"
        elif score >= 60:
            return "Needs Improvement"
        else:
            return "Poor"
    
    def _group_questions_by_type(self, questions: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group questions by type"""
        type_counts = {}
        for question in questions:
            q_type = question.get("question_type", "unknown")
            type_counts[q_type] = type_counts.get(q_type, 0) + 1
        return type_counts
    
    def _group_questions_by_difficulty(self, questions: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group questions by difficulty"""
        difficulty_counts = {}
        for question in questions:
            difficulty = question.get("difficulty_level", "unknown")
            difficulty_counts[difficulty] = difficulty_counts.get(difficulty, 0) + 1
        return difficulty_counts
    
    def _group_questions_by_source(self, questions: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group questions by source type"""
        source_counts = {}
        for question in questions:
            source = question.get("source_type", "unknown")
            source_counts[source] = source_counts.get(source, 0) + 1
        return source_counts
    
    def _estimate_pages(self, content: str) -> int:
        """Estimate number of pages for the report"""
        words_per_page = 500  # Approximate
        word_count = len(content.split())
        return max(1, (word_count + words_per_page - 1) // words_per_page)
    
    def _get_markdown_template(self) -> str:
        """Get markdown report template"""
        return """

**Unit:** {{ unit_info.code }} - {{ unit_info.title }}  
**Sector:** {{ unit_info.sector }}  
**Qualification Level:** {{ unit_info.qualification_level }}  
**Generated:** {{ generated_at }}  
**Session ID:** {{ session_info.id }}

---


- **Overall Score:** {{ validation_summary.overall_score }}/100
- **Compliance Level:** {{ validation_summary.compliance_level }}
- **Strictness Level:** {{ session_info.strictness_level }}
- **Total Gaps Identified:** {{ validation_summary.total_gaps }}
- **High Priority Gaps:** {{ validation_summary.high_priority_gaps_count }}

---


- **Elements:** {{ unit_info.elements_count }}
- **Performance Criteria:** {{ unit_info.performance_criteria_count }}
- **Knowledge Evidence Requirements:** {{ unit_info.knowledge_evidence_count }}
- **Documents Analyzed:** {{ session_info.documents_count }}

---


{% for engine_name, results in engine_results.items() %}

- **Score:** {{ results.overall_score }}/100
- **Findings:** {{ results.findings|length if results.findings is mapping else 'N/A' }}
- **Recommendations:** {{ results.recommendations|length }}
- **Gaps:** {{ results.gaps|length }}

{% if results.gaps %}
{% for gap in results.gaps %}
- **{{ gap.gap_type }}** ({{ gap.severity }}): {{ gap.description }}
  - *Recommendation:* {{ gap.recommendation }}
  - *Confidence:* {{ (gap.confidence_score * 100)|round }}%
{% endfor %}
{% endif %}

---
{% endfor %}


{% if high_priority_gaps %}
{% for gap in high_priority_gaps %}

**Description:** {{ gap.description }}

**Recommendation:** {{ gap.recommendation }}

**Confidence Score:** {{ (gap.confidence_score * 100)|round }}%

---
{% endfor %}
{% else %}
No high priority gaps identified.
{% endif %}


{% if questions_summary.total_questions %}
- **Total Questions Generated:** {{ questions_summary.total_questions }}

{% for type, count in questions_summary.by_type.items() %}
- {{ type.replace('_', ' ').title() }}: {{ count }}
{% endfor %}

{% for difficulty, count in questions_summary.by_difficulty.items() %}
- {{ difficulty }}: {{ count }}
{% endfor %}

{% for source, count in questions_summary.by_source.items() %}
- {{ source.replace('_', ' ').title() }}: {{ count }}
{% endfor %}

---


{% for question in questions[:5] %}

**Difficulty:** {{ question.difficulty_level }}  
**Time Allocation:** {{ question.time_allocation }} minutes

**Question:** {{ question.question_text }}

**Benchmark Answer:** {{ question.benchmark_answer }}

**Assessment Guidance:** {{ question.assessment_guidance }}

---
{% endfor %}
{% else %}
No questions were generated for this validation session.
{% endif %}


Based on the validation analysis, the following actions are recommended:

{% for engine_name, results in engine_results.items() %}
{% for recommendation in results.recommendations %}
- {{ recommendation }}
{% endfor %}
{% endfor %}

---

*Report generated by Enhanced AI Agent OS Training Validation System*
"""
    
    def _get_html_template(self) -> str:
        """Get HTML report template"""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>Training Validation Report - {{ unit_info.code }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
        .header { background: #f4f4f4; padding: 20px; border-radius: 5px; }
        .summary { background: #e8f4f8; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .engine-result { border: 1px solid #ddd; margin: 20px 0; padding: 15px; border-radius: 5px; }
        .gap { background: #fff3cd; padding: 10px; margin: 10px 0; border-left: 4px solid #ffc107; }
        .high-priority { background: #f8d7da; border-left-color: #dc3545; }
        .question { background: #f8f9fa; padding: 15px; margin: 15px 0; border-radius: 5px; }
        .score { font-size: 1.2em; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Training Validation Report</h1>
        <p><strong>Unit:</strong> {{ unit_info.code }} - {{ unit_info.title }}</p>
        <p><strong>Sector:</strong> {{ unit_info.sector }}</p>
        <p><strong>Generated:</strong> {{ generated_at }}</p>
    </div>

    <div class="summary">
        <h2>Executive Summary</h2>
        <p class="score">Overall Score: {{ validation_summary.overall_score }}/100 ({{ validation_summary.compliance_level }})</p>
        <p>Strictness Level: {{ session_info.strictness_level }}</p>
        <p>Total Gaps: {{ validation_summary.total_gaps }} ({{ validation_summary.high_priority_gaps_count }} high priority)</p>
    </div>

    <h2>Validation Results</h2>
    {% for engine_name, results in engine_results.items() %}
    <div class="engine-result">
        <h3>{{ engine_name.replace('_', ' ').title() }}</h3>
        <p><strong>Score:</strong> {{ results.overall_score }}/100</p>
        <p><strong>Gaps:</strong> {{ results.gaps|length }}</p>
        
        {% if results.gaps %}
        <h4>Gaps:</h4>
        {% for gap in results.gaps %}
        <div class="gap {% if gap.severity == 'high' %}high-priority{% endif %}">
            <strong>{{ gap.gap_type }}</strong> ({{ gap.severity }})
            <p>{{ gap.description }}</p>
            <p><em>Recommendation: {{ gap.recommendation }}</em></p>
        </div>
        {% endfor %}
        {% endif %}
    </div>
    {% endfor %}

    {% if questions %}
    <h2>Generated Questions ({{ questions|length }})</h2>
    {% for question in questions[:10] %}
    <div class="question">
        <h4>{{ question.question_type.replace('_', ' ').title() }} - {{ question.difficulty_level }}</h4>
        <p><strong>Question:</strong> {{ question.question_text }}</p>
        <p><strong>Time:</strong> {{ question.time_allocation }} minutes</p>
        <p><strong>Assessment Guidance:</strong> {{ question.assessment_guidance }}</p>
    </div>
    {% endfor %}
    {% endif %}

    <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd;">
        <p><em>Report generated by Enhanced AI Agent OS Training Validation System</em></p>
    </footer>
</body>
</html>
"""
    
    def _get_summary_template(self) -> str:
        """Get summary report template"""
        return """
TRAINING VALIDATION SUMMARY REPORT
==================================

Unit: {{ unit_info.code }} - {{ unit_info.title }}
Sector: {{ unit_info.sector }}
Generated: {{ generated_at }}

OVERALL RESULTS
---------------
Score: {{ validation_summary.overall_score }}/100 ({{ validation_summary.compliance_level }})
Strictness: {{ session_info.strictness_level }}
Total Gaps: {{ validation_summary.total_gaps }}
High Priority: {{ validation_summary.high_priority_gaps_count }}

VALIDATION ENGINES
------------------
{% for engine_name, results in engine_results.items() %}
{{ engine_name.replace('_', ' ').title() }}: {{ results.overall_score }}/100 ({{ results.gaps|length }} gaps)
{% endfor %}

HIGH PRIORITY GAPS
------------------
{% for gap in high_priority_gaps %}
- {{ gap.gap_type }}: {{ gap.description }}
{% endfor %}

QUESTIONS GENERATED
-------------------
{% if questions_summary.total_questions %}
Total: {{ questions_summary.total_questions }}
Types: {% for type, count in questions_summary.by_type.items() %}{{ type }}({{ count }}) {% endfor %}
{% else %}
No questions generated
{% endif %}

KEY RECOMMENDATIONS
-------------------
{% for engine_name, results in engine_results.items() %}
{% for recommendation in results.recommendations[:3] %}
- {{ recommendation }}
{% endfor %}
{% endfor %}
"""
