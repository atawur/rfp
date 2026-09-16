import { apiRequest } from "./apiClient";
import { API_ENDPOINTS } from "@/constants/api";
import { RFP, RFPCreate, RFPImportResponse, PaginatedResponse } from "@/types";

export const rfpService = {
  async getPaginatedRFPs(params: {
    page?: number;
    size?: number;
    website_id?: number | null;
    category?: string;
    sub_category?: string;
    procurement_type?: string;
    status?: string;
    search?: string;
  } = {}): Promise<PaginatedResponse<RFP>> {
    const queryParams: Record<string, string | number> = {
      page: params.page ?? 1,
      size: params.size ?? 20,
    };

    if (params.website_id && params.website_id > 0) {
      queryParams.website_id = params.website_id;
    }
    if (params.category && params.category !== "ALL") {
      queryParams.category = params.category;
    }
    if (params.sub_category) {
      queryParams.sub_category = params.sub_category;
    }
    if (params.procurement_type) {
      queryParams.procurement_type = params.procurement_type;
    }
    if (params.status && params.status !== "ALL") {
      queryParams.status = params.status;
    }
    if (params.search && params.search.trim()) {
      queryParams.search = params.search.trim();
    }

    return apiRequest<PaginatedResponse<RFP>>(API_ENDPOINTS.RFPS.BASE, {
      method: "GET",
      params: queryParams,
    });
  },

  async getRFPs(
    paramsOrSkip?:
      | {
          skip?: number;
          limit?: number;
          page?: number;
          size?: number;
          website_id?: number | null;
          category?: string;
          sub_category?: string;
          procurement_type?: string;
          status?: string;
          search?: string;
        }
      | number,
    limitArg?: number
  ): Promise<RFP[]> {
    let queryParams: Record<string, string | number> = {
      skip: 0,
      limit: 100,
    };

    if (typeof paramsOrSkip === "number") {
      queryParams.skip = paramsOrSkip;
      if (typeof limitArg === "number") {
        queryParams.limit = limitArg;
      }
    } else if (paramsOrSkip) {
      queryParams.skip = paramsOrSkip.skip ?? 0;
      queryParams.limit = paramsOrSkip.limit ?? 100;
      if (paramsOrSkip.page) queryParams.page = paramsOrSkip.page;
      if (paramsOrSkip.size) queryParams.size = paramsOrSkip.size;
      if (paramsOrSkip.website_id && paramsOrSkip.website_id > 0) {
        queryParams.website_id = paramsOrSkip.website_id;
      }
      if (paramsOrSkip.category && paramsOrSkip.category !== "ALL") {
        queryParams.category = paramsOrSkip.category;
      }
      if (paramsOrSkip.sub_category) {
        queryParams.sub_category = paramsOrSkip.sub_category;
      }
      if (paramsOrSkip.procurement_type) {
        queryParams.procurement_type = paramsOrSkip.procurement_type;
      }
      if (paramsOrSkip.status && paramsOrSkip.status !== "ALL") {
        queryParams.status = paramsOrSkip.status;
      }
      if (paramsOrSkip.search && paramsOrSkip.search.trim()) {
        queryParams.search = paramsOrSkip.search.trim();
      }
    }

    const res = await apiRequest<PaginatedResponse<RFP> | RFP[]>(API_ENDPOINTS.RFPS.BASE, {
      method: "GET",
      params: queryParams,
    });

    if (Array.isArray(res)) {
      return res;
    }
    return res?.items || [];
  },

  async getRFPById(id: number): Promise<RFP> {
    return apiRequest<RFP>(API_ENDPOINTS.RFPS.BY_ID(id), {
      method: "GET",
    });
  },

  async createRFP(rfp: RFPCreate): Promise<RFP> {
    return apiRequest<RFP>(API_ENDPOINTS.RFPS.BASE, {
      method: "POST",
      body: JSON.stringify(rfp),
    });
  },

  async importFromUrl(url: string): Promise<RFPImportResponse> {
    return apiRequest<RFPImportResponse>(API_ENDPOINTS.RFPS.IMPORT_URL, {
      method: "POST",
      body: JSON.stringify({ url }),
    });
  },

  async classifyRFP(id: number, force: boolean = false): Promise<RFP> {
    return apiRequest<RFP>(`/api/v1/rfps/${id}/classify?force=${force}`, {
      method: "POST",
    });
  },

  async reprocessClassification(limit: number = 50): Promise<{ processed: number; succeeded: number; failed: number }> {
    return apiRequest<{ processed: number; succeeded: number; failed: number }>(
      `/api/v1/rfps/reprocess-classification?limit=${limit}`,
      {
        method: "POST",
      }
    );
  },
};
