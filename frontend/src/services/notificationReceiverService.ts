import { apiRequest } from "./apiClient";
import { API_ENDPOINTS } from "@/constants/api";
import {
  NotificationReceiver,
  NotificationReceiverCreate,
  NotificationReceiverUpdate,
} from "@/types";

export const notificationReceiverService = {
  async getReceivers(
    skip: number = 0,
    limit: number = 100,
    statusFilter?: string
  ): Promise<NotificationReceiver[]> {
    const params: Record<string, string | number> = { skip, limit };
    if (statusFilter) {
      params.status_filter = statusFilter;
    }
    return apiRequest<NotificationReceiver[]>(
      API_ENDPOINTS.NOTIFICATION_RECEIVERS.BASE,
      {
        method: "GET",
        params,
      }
    );
  },

  async getActiveReceivers(): Promise<NotificationReceiver[]> {
    return this.getReceivers(0, 200, "active");
  },

  async createReceiver(
    receiver: NotificationReceiverCreate
  ): Promise<NotificationReceiver> {
    return apiRequest<NotificationReceiver>(
      API_ENDPOINTS.NOTIFICATION_RECEIVERS.BASE,
      {
        method: "POST",
        body: JSON.stringify(receiver),
      }
    );
  },

  async updateReceiver(
    id: number,
    receiver: NotificationReceiverUpdate
  ): Promise<NotificationReceiver> {
    return apiRequest<NotificationReceiver>(
      API_ENDPOINTS.NOTIFICATION_RECEIVERS.BY_ID(id),
      {
        method: "PUT",
        body: JSON.stringify(receiver),
      }
    );
  },

  async deleteReceiver(id: number): Promise<{ message: string }> {
    return apiRequest<{ message: string }>(
      API_ENDPOINTS.NOTIFICATION_RECEIVERS.BY_ID(id),
      {
        method: "DELETE",
      }
    );
  },
};
