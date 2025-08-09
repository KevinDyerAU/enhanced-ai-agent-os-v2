import axios from 'axios';

const API_BASE_URL = 'http://localhost:8033/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface ValidationSession {
  id: string;
  name: string;
  unit_code: string;
  description: string;
  status: string;
  created_at: string;
  training_unit_id?: string;
}

export interface TrainingUnit {
  unit_code: string;
  title: string;
  description: string;
  elements: any[];
  performance_criteria: any[];
  knowledge_evidence: any[];
  foundation_skills: any[];
}

export interface Question {
  id: number;
  session_id: string;
  question_type: string;
  category: string;
  question_text: string;
  difficulty_level: string;
  benchmark_answer: string;
  assessment_guidance: string;
  review_status: string;
  created_at: string;
}

export interface ValidationReport {
  id: string;
  session_id: string;
  report_type: string;
  status: string;
  content: string;
  overall_score: number;
  created_at: string;
}

export interface ValidationResult {
  session_id: string;
  overall_score: number;
  compliance_level: string;
  findings: any[];
  recommendations: string[];
  gaps: any[];
}

export interface AnalyticsData {
  total_sessions: number;
  active_sessions: number;
  total_questions: number;
  approved_questions: number;
  validation_trends: any[];
  gap_analysis: any[];
  system_usage: any[];
}

class TrainingValidationAPI {
  async retrieveTrainingUnit(unitCode: string): Promise<TrainingUnit> {
    const response = await api.post('/training-units/retrieve', {
      unit_code: unitCode
    });
    return response.data.unit;
  }

  async createValidationSession(sessionData: {
    name: string;
    unit_code: string;
    description: string;
  }): Promise<ValidationSession> {
    const response = await api.post('/validation-sessions', sessionData);
    return response.data.session;
  }

  async getValidationSessions(): Promise<ValidationSession[]> {
    const response = await api.get('/validation-sessions');
    return response.data.sessions;
  }

  async getValidationSession(sessionId: string): Promise<ValidationSession> {
    const response = await api.get(`/validation-sessions/${sessionId}`);
    return response.data.session;
  }

  async uploadDocument(sessionId: string, file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post(`/api/v1/validation-sessions/${sessionId}/documents`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async executeValidation(sessionId: string, strictnessLevel: string = 'normal'): Promise<ValidationResult> {
    const response = await api.post(`/validation-sessions/${sessionId}/execute`, {
      strictness_level: strictnessLevel
    });
    return response.data;
  }

  async getValidationResults(sessionId: string): Promise<ValidationResult> {
    const response = await api.get(`/validation-sessions/${sessionId}/results`);
    return response.data;
  }

  async generateQuestions(sessionId: string): Promise<Question[]> {
    const response = await api.post(`/validation-sessions/${sessionId}/generate-questions`, {});
    return response.data.questions;
  }

  async getQuestionsForSession(sessionId: string): Promise<Question[]> {
    const response = await api.get(`/validation-sessions/${sessionId}/questions`);
    return response.data.questions;
  }

  async searchQuestions(query: string, filters?: any): Promise<Question[]> {
    const response = await api.post('/questions/search', {
      query,
      filters
    });
    return response.data.questions;
  }

  async getQuestionsByUnit(unitCode: string): Promise<Question[]> {
    const response = await api.get(`/questions/unit/${unitCode}`);
    return response.data.questions;
  }

  async updateQuestionStatus(questionId: number, status: string): Promise<boolean> {
    const response = await api.put(`/questions/${questionId}/status`, {
      status
    });
    return response.data.success;
  }

  async getQuestionStatistics(): Promise<any> {
    const response = await api.get('/questions/statistics');
    return response.data;
  }

  async exportQuestions(format: string = 'json', filters?: any): Promise<any> {
    const response = await api.post('/questions/export', {
      format,
      filters
    });
    return response.data;
  }

  async generateReport(sessionId: string, format: string = 'markdown'): Promise<ValidationReport> {
    const response = await api.post(`/validation-sessions/${sessionId}/generate-report`, {
      format
    });
    return response.data;
  }

  async getSessionReports(sessionId: string): Promise<ValidationReport[]> {
    const response = await api.get(`/validation-sessions/${sessionId}/reports`);
    return response.data.reports;
  }

  async getReportContent(reportId: string): Promise<string> {
    const response = await api.get(`/reports/${reportId}/content`);
    return response.data.content;
  }

  async getValidationTrends(timeframe: string = '30d'): Promise<any> {
    const response = await api.get(`/analytics/validation-trends?timeframe=${timeframe}`);
    return response.data;
  }

  async getGapAnalysisInsights(): Promise<any> {
    const response = await api.get('/analytics/gap-analysis');
    return response.data;
  }

  async getSystemUsageAnalytics(): Promise<AnalyticsData> {
    const response = await api.get('/analytics/system-usage');
    return response.data;
  }

  async submitValidationReportForReview(sessionId: string): Promise<any> {
    const response = await api.post(`/validation-sessions/${sessionId}/submit-for-review`);
    return response.data;
  }

  async getValidationReportStatus(sessionId: string): Promise<any> {
    const response = await api.get(`/validation-sessions/${sessionId}/report-status`);
    return response.data;
  }

  async getPendingValidationReports(): Promise<any[]> {
    const response = await api.get('/validation-reports/pending');
    return response.data.reports;
  }
}

export const trainingValidationAPI = new TrainingValidationAPI();
export default trainingValidationAPI;
