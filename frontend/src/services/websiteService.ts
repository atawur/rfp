import { apiRequest } from "./apiClient";
import { API_ENDPOINTS } from "@/constants/api";
import {
  CrawlResponse,
  TestExtractionResponse,
  Website,
  WebsiteCreate,
  WebsiteUpdate,
} from "@/types";

export const websiteService = {
  async getWebsites(skip: number = 0, limit: number = 100): Promise<Website[]> {
    return apiRequest<Website[]>(API_ENDPOINTS.WEBSITES.BASE, {
      method: "GET",
      params: { skip, limit },
    });
  },

  async getWebsiteById(id: number): Promise<Website> {
    return apiRequest<Website>(API_ENDPOINTS.WEBSITES.BY_ID(id), {
      method: "GET",
    });
  },

  async createWebsite(website: WebsiteCreate): Promise<Website> {
    return apiRequest<Website>(API_ENDPOINTS.WEBSITES.BASE, {
      method: "POST",
      body: JSON.stringify(website),
    });
  },

  async updateWebsite(id: number, website: WebsiteUpdate): Promise<Website> {
    return apiRequest<Website>(API_ENDPOINTS.WEBSITES.BY_ID(id), {
      method: "PUT",
      body: JSON.stringify(website),
    });
  },

  async triggerCrawl(websiteId: number): Promise<CrawlResponse> {
    return apiRequest<CrawlResponse>(API_ENDPOINTS.WEBSITES.CRAWL(websiteId), {
      method: "POST",
    });
  },

  async triggerCrawlAll(): Promise<CrawlResponse> {
    return apiRequest<CrawlResponse>(API_ENDPOINTS.WEBSITES.CRAWL_ALL, {
      method: "POST",
    });
  },

  async testExtraction(url: string): Promise<TestExtractionResponse> {
    return apiRequest<TestExtractionResponse>(
      API_ENDPOINTS.WEBSITES.TEST_EXTRACTION,
      {
        method: "POST",
        body: JSON.stringify({ url }),
      }
    );
  },

  async getCrawlStatus(): Promise<{ running_website_ids: number[]; is_crawling_any: boolean }> {
    return apiRequest<{ running_website_ids: number[]; is_crawling_any: boolean }>(
      "/api/v1/websites/crawl-status",
      {
        method: "GET",
      }
    );
  },
};
