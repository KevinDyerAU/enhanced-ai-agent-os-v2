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

export interface ComplianceValidation {
  approved: boolean;
  validation_id: string;
  violations: Array<{
    rule_id: string;
    rule_name: string;
    severity: string;
    description: string;
    recommendation: string;
  }>;
  required_approvals: string[];
  compliance_score: number;
  recommendations: string[];
}

export interface AuditLog {
  id: string;
  event_type: string;
  entity_type: string;
  entity_id: string;
  actor_type: string;
  actor_id: string;
  action: string;
  details: Record<string, any>;
  timestamp: string;
  session_id?: string;
}

export interface CreativeAsset {
  id: string;
  title: string;
  type: string;
  status: string;
  content_url?: string;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export class ApiService {
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

  async validateAction(request: {
    action_type: string;
    entity_type: string;
    entity_id: string;
    actor_id: string;
    action_data: Record<string, any>;
    metadata?: Record<string, any>;
  }): Promise<ComplianceValidation> {
    const response = await fetch('http://localhost:8005/validate-action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request)
    });
    if (!response.ok) {
      throw new Error('Validation failed');
    }
    return response.json();
  }

  async logEvent(request: {
    event_type: string;
    entity_type: string;
    entity_id: string;
    actor_type: string;
    actor_id: string;
    action: string;
    details: Record<string, any>;
    metadata?: Record<string, any>;
  }): Promise<AuditLog> {
    const response = await fetch('http://localhost:8006/log-event', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request)
    });
    if (!response.ok) {
      throw new Error('Audit logging failed');
    }
    return response.json();
  }

  async queryAuditLogs(request: {
    entity_type?: string;
    entity_id?: string;
    actor_id?: string;
    event_type?: string;
    action?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
  }): Promise<AuditLog[]> {
    const response = await fetch('http://localhost:8006/query-logs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request)
    });
    if (!response.ok) {
      throw new Error('Audit query failed');
    }
    return response.json();
  }

  async requestReview(request: {
    asset_id: string;
    reviewer_id: string;
    priority?: string;
    metadata?: Record<string, any>;
  }): Promise<{ asset_id: string; status: string; message: string; review_id: string }> {
    const response = await fetch('http://localhost:8007/request-review', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request)
    });
    if (!response.ok) {
      throw new Error('Review request failed');
    }
    return response.json();
  }

  async approveAsset(assetId: string, request: {
    reviewer_id: string;
    comments?: string;
    metadata?: Record<string, any>;
  }): Promise<{ asset_id: string; status: string; message: string; review_id: string }> {
    const response = await fetch(`http://localhost:8007/approve/${assetId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request)
    });
    if (!response.ok) {
      throw new Error('Asset approval failed');
    }
    return response.json();
  }

  async rejectAsset(assetId: string, request: {
    reviewer_id: string;
    reason: string;
    comments?: string;
    required_changes?: string[];
    metadata?: Record<string, any>;
  }): Promise<{ asset_id: string; status: string; message: string; review_id: string }> {
    const response = await fetch(`http://localhost:8007/reject/${assetId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request)
    });
    if (!response.ok) {
      throw new Error('Asset rejection failed');
    }
    return response.json();
  }

  async getPendingAssets(limit: number = 50): Promise<CreativeAsset[]> {
    const response = await fetch(`http://localhost:8007/assets/pending?limit=${limit}`);
    if (!response.ok) {
      throw new Error('Failed to fetch pending assets');
    }
    return response.json();
  }

  async getAsset(assetId: string): Promise<CreativeAsset> {
    const response = await fetch(`http://localhost:8007/assets/${assetId}`);
    if (!response.ok) {
      throw new Error('Failed to fetch asset');
    }
    return response.json();
  }
}


export const apiService = new ApiService();
