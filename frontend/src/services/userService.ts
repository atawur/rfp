import { apiRequest } from "./apiClient";
import { API_ENDPOINTS } from "@/constants/api";
import { User, UserCreate, UserUpdate } from "@/types";

export const userService = {
  async getUsers(skip: number = 0, limit: number = 100): Promise<User[]> {
    return apiRequest<User[]>(API_ENDPOINTS.USERS.BASE, {
      method: "GET",
      params: { skip, limit },
    });
  },

  async createUser(user: UserCreate): Promise<User> {
    return apiRequest<User>(API_ENDPOINTS.USERS.BASE, {
      method: "POST",
      body: JSON.stringify(user),
    });
  },

  async updateUser(id: number, user: UserUpdate): Promise<User> {
    return apiRequest<User>(API_ENDPOINTS.USERS.BY_ID(id), {
      method: "PUT",
      body: JSON.stringify(user),
    });
  },

  async getUserMe(): Promise<User> {
    return apiRequest<User>(API_ENDPOINTS.USERS.ME, {
      method: "GET",
    });
  },
};
