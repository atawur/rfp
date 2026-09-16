const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(message: string, status: number, data?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined>;
  formUrlEncoded?: boolean;
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { params, formUrlEncoded, headers: customHeaders, ...restOptions } = options;

  let url = `${API_BASE_URL}${endpoint}`;

  if (params) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value));
      }
    });
    const queryString = searchParams.toString();
    if (queryString) {
      url += (url.includes("?") ? "&" : "?") + queryString;
    }
  }

  const headers = new Headers(customHeaders || {});

  // Add auth token if present in localStorage in browser
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("rfp_token");
    if (token && !headers.has("Authorization")) {
      headers.set("Authorization", `Bearer ${token}`);
    }
  }

  if (formUrlEncoded) {
    headers.set("Content-Type", "application/x-www-form-urlencoded");
  } else if (!headers.has("Content-Type") && restOptions.body && typeof restOptions.body === "string") {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(url, {
    headers,
    ...restOptions,
  });

  if (!response.ok) {
    let errorDetail = `Request failed with status ${response.status}`;
    let errorData: unknown = null;

    try {
      errorData = await response.json();
      if (errorData && typeof errorData === "object") {
        const anyError = errorData as Record<string, unknown>;
        if (typeof anyError.detail === "string") {
          errorDetail = anyError.detail;
        } else if (Array.isArray(anyError.detail)) {
          errorDetail = anyError.detail.map((e: { msg?: string }) => e.msg || JSON.stringify(e)).join(", ");
        } else if (typeof anyError.message === "string") {
          errorDetail = anyError.message;
        }
      }
    } catch {
      // response was not JSON, fallback to statusText
      errorDetail = response.statusText || errorDetail;
    }

    // Auto clear expired token if 401
    if (response.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("rfp_token");
    }

    throw new ApiError(errorDetail, response.status, errorData);
  }

  // Check if response has content before parsing JSON
  const text = await response.text();
  return text ? JSON.parse(text) : ({} as T);
}
