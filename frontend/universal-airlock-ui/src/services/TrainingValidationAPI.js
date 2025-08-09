import axios from 'axios';

const API_BASE_URL = 'http://localhost:8033/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

class TrainingValidationAPI {
  async uploadDocument(sessionId, file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post(`/validation-sessions/${sessionId}/documents`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  // Add other methods as needed
  async retrieveTrainingUnit(unitCode) {
    const response = await api.post('/training-units/retrieve', {
      unit_code: unitCode
    });
    return response.data.unit;
  }

  async createValidationSession(sessionData) {
    console.log('Creating validation session with data:', JSON.stringify(sessionData, null, 2));
    try {
      const response = await api.post('/validation-sessions', sessionData);
      console.log('Validation session created successfully:', response.data);
      return response.data.session;
    } catch (error) {
      console.error('Error creating validation session:', {
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        config: {
          url: error.config?.url,
          method: error.config?.method,
          data: error.config?.data
        }
      });
      throw error;
    }
  }

  async getValidationSessions() {
    const response = await api.get('/validation-sessions');
    return response.data.sessions;
  }

  async getValidationSession(sessionId) {
    const response = await api.get(`/validation-sessions/${sessionId}`);
    return response.data.session;
  }

  async executeValidation(sessionId, strictnessLevel = 'normal') {
    const response = await api.post(`/validation-sessions/${sessionId}/execute`, {
      strictness_level: strictnessLevel
    });
    return response.data;
  }

  async getValidationResults(sessionId) {
    const response = await api.get(`/validation-sessions/${sessionId}/results`);
    return response.data;
  }
}

export const trainingValidationAPI = new TrainingValidationAPI();
export default trainingValidationAPI;
