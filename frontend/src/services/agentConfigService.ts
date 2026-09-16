import { apiRequest } from "./apiClient";
import { API_ENDPOINTS } from "@/constants/api";
import {
  AIAgentConfig,
  AIAgentConfigCreate,
  AIAgentConfigUpdate,
} from "@/types";

export const agentConfigService = {
  async getConfigs(skip: number = 0, limit: number = 100): Promise<AIAgentConfig[]> {
    return apiRequest<AIAgentConfig[]>(API_ENDPOINTS.AGENT_CONFIGS.BASE, {
      method: "GET",
      params: { skip, limit },
    });
  },

  async getActiveConfig(): Promise<AIAgentConfig | null> {
    return apiRequest<AIAgentConfig | null>(API_ENDPOINTS.AGENT_CONFIGS.ACTIVE, {
      method: "GET",
    });
  },

  async getConfigById(id: number): Promise<AIAgentConfig> {
    return apiRequest<AIAgentConfig>(API_ENDPOINTS.AGENT_CONFIGS.BY_ID(id), {
      method: "GET",
    });
  },

  async createConfig(config: AIAgentConfigCreate): Promise<AIAgentConfig> {
    return apiRequest<AIAgentConfig>(API_ENDPOINTS.AGENT_CONFIGS.BASE, {
      method: "POST",
      body: JSON.stringify(config),
    });
  },

  async updateConfig(
    id: number,
    config: AIAgentConfigUpdate
  ): Promise<AIAgentConfig> {
    return apiRequest<AIAgentConfig>(API_ENDPOINTS.AGENT_CONFIGS.BY_ID(id), {
      method: "PUT",
      body: JSON.stringify(config),
    });
  },

  async deleteConfig(id: number): Promise<AIAgentConfig> {
    return apiRequest<AIAgentConfig>(API_ENDPOINTS.AGENT_CONFIGS.BY_ID(id), {
      method: "DELETE",
    });
  },

  async activateConfig(id: number): Promise<AIAgentConfig> {
    return apiRequest<AIAgentConfig>(API_ENDPOINTS.AGENT_CONFIGS.ACTIVATE(id), {
      method: "POST",
    });
  },
};
