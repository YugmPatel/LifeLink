/**
 * API Service for EDFlow AI Dashboard
 * Handles all HTTP requests to the FastAPI backend
 */

import {
  DashboardMetrics,
  PatientCase,
  ActivityEntry,
  ChatMessage,
  AgentStatus,
  SimulationResponse,
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8080";

class ApiError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public response?: any
  ) {
    super(message);
    this.name = "ApiError";
  }
}

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    const defaultOptions: RequestInit = {
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    };

    const config = { ...defaultOptions, ...options };

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new ApiError(
          errorData.message ||
            `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          errorData
        );
      }

      return await response.json();
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }

      // Network or other errors
      throw new ApiError(
        `Network error: ${
          error instanceof Error ? error.message : "Unknown error"
        }`,
        0
      );
    }
  }

  // Dashboard endpoints
  async getDashboardMetrics(): Promise<DashboardMetrics> {
    const data = await this.request<DashboardMetrics>("/api/dashboard/metrics");
    return {
      ...data,
      lastUpdated: new Date(data.lastUpdated),
    };
  }

  async getDashboardStatus(): Promise<any> {
    return this.request("/api/dashboard/status");
  }

  // Cases endpoints
  async getActiveCases(filters?: {
    status?: string;
    type?: string;
    priority?: number;
    limit?: number;
  }): Promise<PatientCase[]> {
    const params = new URLSearchParams();

    if (filters?.status) params.append("status", filters.status);
    if (filters?.type) params.append("case_type", filters.type);
    if (filters?.priority)
      params.append("priority", filters.priority.toString());
    if (filters?.limit) params.append("limit", filters.limit.toString());

    const queryString = params.toString();
    const endpoint = `/api/cases${queryString ? `?${queryString}` : ""}`;

    const cases = await this.request<PatientCase[]>(endpoint);
    return cases.map((patientCase) => ({
      ...patientCase,
      timestamp: new Date(patientCase.timestamp),
    }));
  }

  async getCaseDetails(caseId: string): Promise<PatientCase> {
    const data = await this.request<PatientCase>(`/api/cases/${caseId}`);
    return {
      ...data,
      timestamp: new Date(data.timestamp),
    };
  }

  async updateCaseStatus(caseId: string, status: string): Promise<any> {
    return this.request(`/api/cases/${caseId}/status?new_status=${status}`, {
      method: "PUT",
    });
  }

  async dischargeCase(caseId: string): Promise<any> {
    return this.request(`/api/cases/${caseId}`, {
      method: "DELETE",
    });
  }

  async getCaseTimeline(caseId: string): Promise<any> {
    return this.request(`/api/cases/${caseId}/timeline`);
  }

  async getCaseStatistics(): Promise<any> {
    return this.request("/api/cases/statistics/summary");
  }

  // Activity endpoints
  async getRecentActivity(filters?: {
    type?: string;
    limit?: number;
  }): Promise<ActivityEntry[]> {
    const params = new URLSearchParams();

    if (filters?.type) params.append("activity_type", filters.type);
    if (filters?.limit) params.append("limit", filters.limit.toString());

    const queryString = params.toString();
    const endpoint = `/api/dashboard/activity${
      queryString ? `?${queryString}` : ""
    }`;

    const activities = await this.request<ActivityEntry[]>(endpoint);
    return activities.map((activity) => ({
      ...activity,
      timestamp: new Date(activity.timestamp),
    }));
  }

  // Agent endpoints
  async getAgentsStatus(): Promise<AgentStatus[]> {
    const agents = await this.request<AgentStatus[]>("/api/agents/status");
    return agents.map((agent) => ({
      ...agent,
      lastSeen: new Date(agent.lastSeen),
    }));
  }

  async getAgentMessages(filters?: {
    agentType?: string;
    limit?: number;
  }): Promise<ChatMessage[]> {
    const params = new URLSearchParams();

    if (filters?.agentType) params.append("agent_type", filters.agentType);
    if (filters?.limit) params.append("limit", filters.limit.toString());

    const queryString = params.toString();
    const endpoint = `/api/agents/messages${
      queryString ? `?${queryString}` : ""
    }`;

    const messages = await this.request<ChatMessage[]>(endpoint);
    return messages.map((message) => ({
      ...message,
      timestamp: new Date(message.timestamp),
    }));
  }

  async getAgentsHealth(): Promise<any> {
    return this.request("/api/agents/health");
  }

  async getSpecificAgentStatus(agentType: string): Promise<AgentStatus> {
    const agent = await this.request<AgentStatus>(
      `/api/agents/${agentType}/status`
    );
    return {
      ...agent,
      lastSeen: new Date(agent.lastSeen),
    };
  }

  async restartAgent(agentType: string): Promise<any> {
    return this.request(`/api/agents/${agentType}/restart`, {
      method: "POST",
    });
  }

  async getCommunicationStats(): Promise<any> {
    return this.request("/api/agents/communication/stats");
  }

  // Simulation endpoints
  async simulateSTEMI(): Promise<SimulationResponse> {
    const data = await this.request<SimulationResponse>(
      "/api/simulation/stemi",
      {
        method: "POST",
      }
    );
    return {
      ...data,
      timestamp: new Date(data.timestamp),
    };
  }

  async simulateStroke(): Promise<SimulationResponse> {
    const data = await this.request<SimulationResponse>(
      "/api/simulation/stroke",
      {
        method: "POST",
      }
    );
    return {
      ...data,
      timestamp: new Date(data.timestamp),
    };
  }

  async simulateTrauma(): Promise<SimulationResponse> {
    const data = await this.request<SimulationResponse>(
      "/api/simulation/trauma",
      {
        method: "POST",
      }
    );
    return {
      ...data,
      timestamp: new Date(data.timestamp),
    };
  }

  async simulateCustomCase(
    caseType: string,
    patientData?: any
  ): Promise<SimulationResponse> {
    const data = await this.request<SimulationResponse>(
      "/api/simulation/custom",
      {
        method: "POST",
        body: JSON.stringify({
          case_type: caseType,
          patient_data: patientData,
        }),
      }
    );
    return {
      ...data,
      timestamp: new Date(data.timestamp),
    };
  }

  async getSimulationStatus(): Promise<any> {
    return this.request("/api/simulation/status");
  }

  // Health check
  async healthCheck(): Promise<any> {
    return this.request("/health");
  }

  // Utility methods
  isHealthy(): Promise<boolean> {
    return this.healthCheck()
      .then(() => true)
      .catch(() => false);
  }

  async testConnection(): Promise<boolean> {
    try {
      await this.healthCheck();
      return true;
    } catch {
      return false;
    }
  }
}

// Create singleton instance
export const apiService = new ApiService();

// Export individual methods for convenience
export const api = {
  // Dashboard
  getDashboardMetrics: () => apiService.getDashboardMetrics(),
  getDashboardStatus: () => apiService.getDashboardStatus(),

  // Cases
  getActiveCases: (filters?: Parameters<typeof apiService.getActiveCases>[0]) =>
    apiService.getActiveCases(filters),
  getCaseDetails: (caseId: string) => apiService.getCaseDetails(caseId),
  updateCaseStatus: (caseId: string, status: string) =>
    apiService.updateCaseStatus(caseId, status),
  dischargeCase: (caseId: string) => apiService.dischargeCase(caseId),
  getCaseTimeline: (caseId: string) => apiService.getCaseTimeline(caseId),
  getCaseStatistics: () => apiService.getCaseStatistics(),

  // Activity
  getRecentActivity: (
    filters?: Parameters<typeof apiService.getRecentActivity>[0]
  ) => apiService.getRecentActivity(filters),

  // Agents
  getAgentsStatus: () => apiService.getAgentsStatus(),
  getAgentMessages: (
    filters?: Parameters<typeof apiService.getAgentMessages>[0]
  ) => apiService.getAgentMessages(filters),
  getAgentsHealth: () => apiService.getAgentsHealth(),
  getSpecificAgentStatus: (agentType: string) =>
    apiService.getSpecificAgentStatus(agentType),
  restartAgent: (agentType: string) => apiService.restartAgent(agentType),
  getCommunicationStats: () => apiService.getCommunicationStats(),

  // Simulations
  simulateSTEMI: () => apiService.simulateSTEMI(),
  simulateStroke: () => apiService.simulateStroke(),
  simulateTrauma: () => apiService.simulateTrauma(),
  simulateCustomCase: (caseType: string, patientData?: any) =>
    apiService.simulateCustomCase(caseType, patientData),
  getSimulationStatus: () => apiService.getSimulationStatus(),

  // Health
  healthCheck: () => apiService.healthCheck(),
  isHealthy: () => apiService.isHealthy(),
  testConnection: () => apiService.testConnection(),
};

export default apiService;
export { ApiError };
