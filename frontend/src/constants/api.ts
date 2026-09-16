export const API_ENDPOINTS = {
  HEALTH: "/health",
  AUTH: {
    LOGIN: "/api/v1/auth/login/access-token",
  },
  USERS: {
    BASE: "/api/v1/users/",
    BY_ID: (id: number | string) => `/api/v1/users/${id}`,
    ME: "/api/v1/users/me",
  },
  WEBSITES: {
    BASE: "/api/v1/websites/",
    BY_ID: (id: number | string) => `/api/v1/websites/${id}`,
    CRAWL: (id: number | string) => `/api/v1/websites/${id}/crawl`,
    CRAWL_ALL: "/api/v1/websites/crawl-all",
    TEST_EXTRACTION: "/api/v1/websites/test-extraction",
  },
  RFPS: {
    BASE: "/api/v1/rfps/",
    BY_ID: (id: number | string) => `/api/v1/rfps/${id}`,
    IMPORT_URL: "/api/v1/rfps/import-url",
  },
  AGENT_CONFIGS: {
    BASE: "/api/v1/agent-configs/",
    ACTIVE: "/api/v1/agent-configs/active",
    BY_ID: (id: number | string) => `/api/v1/agent-configs/${id}`,
    ACTIVATE: (id: number | string) => `/api/v1/agent-configs/${id}/activate`,
  },
  NOTIFICATION_RECEIVERS: {
    BASE: "/api/v1/notification-receivers/",
    BY_ID: (id: number | string) => `/api/v1/notification-receivers/${id}`,
  },
} as const;

