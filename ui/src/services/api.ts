const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface Task {
  id: string;
  title: string;
  description?: string;
  type: string;
  status: string;
  priority: string;
  assigned_agent_id?: string;
  requester_id: string;
  input_data: Record<string, any>;
  output_data: Record<string, any>;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface Agent {
  id: string;
  name: string;
  type: string;
  status: string;
  capabilities: Record<string, any>;
  configuration: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface CreateTaskRequest {
  title: string;
  description?: string;
  type: string;
  priority?: string;
  requester_id: string;
  input_data?: Record<string, any>;
  metadata?: Record<string, any>;
}

class ApiService {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.statusText}`);
    }

    return response.json();
  }

  async getTasks(status?: string): Promise<Task[]> {
    const params = status ? `?status=${encodeURIComponent(status)}` : '';
    return this.request<Task[]>(`/api/v1/tasks${params}`);
  }

  async getTask(taskId: string): Promise<Task> {
    return this.request<Task>(`/api/v1/tasks/${taskId}`);
  }

  async createTask(task: CreateTaskRequest): Promise<Task> {
    return this.request<Task>('/api/v1/tasks', {
      method: 'POST',
      body: JSON.stringify(task),
    });
  }

  async getAgents(): Promise<Agent[]> {
    return this.request<Agent[]>('/api/v1/agents');
  }

  async healthCheck(): Promise<{ status: string; database: string }> {
    return this.request<{ status: string; database: string }>('/healthz');
  }
}

export const apiService = new ApiService();
