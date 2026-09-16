import { apiRequest } from "./apiClient";
import { API_ENDPOINTS } from "@/constants/api";
import { Token, User } from "@/types";

export const authService = {
  async login(username: string, password: string): Promise<Token> {
    const body = new URLSearchParams({
      username,
      password,
    }).toString();

    const data = await apiRequest<Token>(API_ENDPOINTS.AUTH.LOGIN, {
      method: "POST",
      body,
      formUrlEncoded: true,
    });

    if (typeof window !== "undefined" && data.access_token) {
      localStorage.setItem("rfp_token", data.access_token);
    }
    return data;
  },

  async getCurrentUser(): Promise<User> {
    return apiRequest<User>(API_ENDPOINTS.USERS.ME, {
      method: "GET",
    });
  },

  logout(): void {
    if (typeof window !== "undefined") {
      localStorage.removeItem("rfp_token");
    }
  },

  getToken(): string | null {
    if (typeof window !== "undefined") {
      return localStorage.getItem("rfp_token");
    }
    return null;
  },

  isAuthenticated(): boolean {
    return !!this.getToken();
  },
};
