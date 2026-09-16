"use client";

import React, { useState } from "react";
import { Modal } from "@/components/ui/Modal";
import { notificationReceiverService } from "@/services/notificationReceiverService";
import { useToast } from "@/context/ToastContext";
import { NotificationReceiverCreate } from "@/types";
import { UserCheck, Loader2 } from "lucide-react";

interface AddReceiverModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export const AddReceiverModal: React.FC<AddReceiverModalProps> = ({
  isOpen,
  onClose,
  onCreated,
}) => {
  const [formData, setFormData] = useState<NotificationReceiverCreate>({
    name: "",
    email: "",
    designation: "",
    phone: "",
    status: "active",
  });
  const [loading, setLoading] = useState(false);
  const { success, error } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim() || !formData.email.trim()) {
      error("Recipient Name and Email Address are required.");
      return;
    }

    setLoading(true);
    try {
      await notificationReceiverService.createReceiver({
        name: formData.name.trim(),
        email: formData.email.trim().toLowerCase(),
        designation: formData.designation?.trim() || undefined,
        phone: formData.phone?.trim() || undefined,
        status: formData.status || "active",
      });
      success(`Notification receiver "${formData.name}" added successfully!`);
      setFormData({ name: "", email: "", designation: "", phone: "", status: "active" });
      onCreated();
      onClose();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to add notification receiver";
      error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Add Notification Receiver"
      subtitle="Register an email recipient to receive automated alerts when RFPs are discovered"
      maxWidth={520}
    >
      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        <div className="form-group">
          <label className="form-label" htmlFor="receiver-name">Recipient Name *</label>
          <input
            id="receiver-name"
            required
            className="form-control"
            placeholder="e.g. Procurement Team or Atik Rahman"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="receiver-email">Recipient Email Address *</label>
          <input
            id="receiver-email"
            type="email"
            required
            className="form-control"
            placeholder="e.g. tenders@company.com"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          />
        </div>

        <div className="form-grid-2">
          <div className="form-group">
            <label className="form-label" htmlFor="receiver-designation">Designation (Optional)</label>
            <input
              id="receiver-designation"
              className="form-control"
              placeholder="e.g. Head of Procurement / Lead"
              value={formData.designation || ""}
              onChange={(e) => setFormData({ ...formData, designation: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="receiver-phone">Phone Number (Optional)</label>
            <input
              id="receiver-phone"
              type="tel"
              className="form-control"
              placeholder="e.g. +880 1712-345678"
              value={formData.phone || ""}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
            />
          </div>
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="receiver-status">Notification Status</label>

          <select
            id="receiver-status"
            className="form-control"
            value={formData.status}
            onChange={(e) => setFormData({ ...formData, status: e.target.value })}
          >
            <option value="active">Active (Receives Email Alerts)</option>
            <option value="inactive">Inactive (Paused / Muted)</option>
          </select>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "4px", display: "block" }}>
            Only active receivers are eligible to receive automated RFP discovery emails.
          </span>
        </div>

        <div style={{ display: "flex", justifyContent: "flex-end", gap: "12px", marginTop: "12px", flexWrap: "wrap" }}>
          <button type="button" onClick={onClose} className="btn btn-secondary">
            Cancel
          </button>
          <button type="submit" disabled={loading} className="btn btn-primary">
            {loading ? <Loader2 size={16} className="animate-spin" /> : <UserCheck size={16} />}
            <span>Add Receiver</span>
          </button>
        </div>
      </form>
    </Modal>
  );
};
