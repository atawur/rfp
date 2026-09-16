export interface User {
  id: number;
  name: string;
  email: string;
  status?: string;
  role_id?: number | null;
  notification_receive?: boolean;
}

export interface UserCreate {
  name: string;
  email: string;
  password: string;
  status?: string;
  role_id?: number | null;
  notification_receive?: boolean;
}

export interface UserUpdate {
  name?: string;
  email?: string;
  password?: string;
  status?: string;
  role_id?: number | null;
  notification_receive?: boolean;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface Website {
  id: number;
  name: string;
  base_url: string;
  start_url: string;
  status?: string;
  crawl_frequency?: string;
  config?: Record<string, unknown> | null;
  notify_all_receivers?: boolean;
  notification_receivers?: NotificationReceiver[];
  created_at: string;
  updated_at?: string | null;
}

export interface WebsiteCreate {
  name: string;
  base_url: string;
  start_url: string;
  status?: string;
  crawl_frequency?: string;
  config?: Record<string, unknown> | null;
  notify_all_receivers?: boolean;
  receiver_ids?: number[];
}

export interface WebsiteUpdate {
  name?: string;
  base_url?: string;
  start_url?: string;
  status?: string;
  crawl_frequency?: string;
  config?: Record<string, unknown> | null;
  notify_all_receivers?: boolean;
  receiver_ids?: number[];
}

export interface NotificationReceiver {
  id: number;
  name: string;
  email: string;
  designation?: string;
  phone?: string;
  status: string; // "active" | "inactive"
  created_at?: string;
  updated_at?: string | null;
}

export interface NotificationReceiverCreate {
  name: string;
  email: string;
  designation?: string;
  phone?: string;
  status?: string;
}

export interface NotificationReceiverUpdate {
  name?: string;
  email?: string;
  designation?: string;
  phone?: string;
  status?: string;
}



export interface RFP {
  id: number;
  title: string;
  external_rfp_id?: string | null;
  reference_number?: string | null;
  organization?: string | null;
  description?: string | null;
  published_date?: string | null;
  submission_deadline?: string | null;
  estimated_budget?: number | null;
  currency?: string | null;
  location?: string | null;
  eligibility?: string[] | string | Record<string, unknown> | null;
  requirements?: string[] | string | Record<string, unknown> | null;
  submission_method?: string | null;
  contact_person?: string | null;
  contact_email?: string | null;
  contact_phone?: string | null;
  source_url: string;
  status?: string;
  website_id?: number | null;
  website_name?: string | null;
  content_hash?: string | null;
  first_seen_at?: string;
  last_seen_at?: string;
  created_at?: string;
  updated_at?: string | null;

  // AI Classification Fields
  primary_category?: string | null;
  sub_category?: string | null;
  procurement_type?: string | null;
  confidence?: number | null;
  keywords?: string[] | null;
  secondary_categories?: string[] | null;
  classification_reason?: string | null;
  classified_at?: string | null;
  classification_model?: string | null;
  classification_status?: string | null;
  classification_attempts?: number | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface RFPCreate {
  title: string;
  external_rfp_id?: string | null;
  reference_number?: string | null;
  organization?: string | null;
  description?: string | null;
  published_date?: string | null;
  submission_deadline?: string | null;
  estimated_budget?: number | null;
  currency?: string | null;
  location?: string | null;
  eligibility?: string[] | string | Record<string, unknown> | null;
  requirements?: string[] | string | Record<string, unknown> | null;
  submission_method?: string | null;
  contact_person?: string | null;
  contact_email?: string | null;
  contact_phone?: string | null;
  source_url: string;
  status?: string;
  website_id?: number | null;
}

export interface RFPProcessResult {
  status: string;
  title?: string | null;
  reason?: string | null;
  id?: number | null;
}

export interface RFPImportResponse {
  message: string;
  results: RFPProcessResult[];
}

export interface AIAgentConfig {
  id: number;
  name: string;
  provider: "openai" | "gemini" | string;
  model_name: string;
  temperature: number;
  extra_params?: Record<string, unknown> | null;
  api_key: string;
  api_key_masked?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string | null;
}

export interface AIAgentConfigCreate {
  name: string;
  provider: string;
  model_name: string;
  api_key: string;
  is_active?: boolean;
  temperature?: number;
  extra_params?: Record<string, unknown> | null;
}

export interface AIAgentConfigUpdate {
  name?: string;
  provider?: string;
  model_name?: string;
  api_key?: string;
  is_active?: boolean;
  temperature?: number;
  extra_params?: Record<string, unknown> | null;
}

export interface HealthResponse {
  status: string;
  project: string;
}

export interface CrawlResponse {
  message: string;
  job_id?: string;
  website_ids?: number[];
  crawl_run_id?: number;
  website_id?: number;
}

export interface TestExtractionResponse {
  message: string;
  results: Record<string, unknown>[];
}
