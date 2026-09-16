"use client";

import React, { useState, useEffect } from "react";
import { Modal } from "@/components/ui/Modal";
import { notificationReceiverService } from "@/services/notificationReceiverService";
import { useToast } from "@/context/ToastContext";
import { NotificationReceiver } from "@/types";
import { Save, Loader2 } from "lucide-react";

interface EditReceiverModalProps {
  isOpen: boolean;
  onClose: () => void;
  receiver: NotificationReceiver | null;
  onUpdated: () => void;
}

export const EditReceiverModal: React.FC<EditReceiverModalProps> = ({
  isOpen,
  onClose,
  receiver,
  onUpdated,
}) => {
  const [formData, setFormData] = useState<{
    name: string;
    email: string;
    designation: string;
    phone: string;
    status: string;
  }>({
    name: "",
    email: "",
    designation: "",
    phone: "",
    status: "active",
  });
  const [loading, setLoading] = useState(false);
  const { success, error } = useToast();

  useEffect(() => {
    if (receiver) {
      setFormData({
        name: receiver.name || "",
        email: receiver.email || "",
        designation: receiver.designation || "",
        phone: receiver.phone || "",
        status: receiver.status || "active",
      });
    }
  }, [receiver]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!receiver) return;

    if (!formData.name.trim() || !formData.email.trim()) {
      error("Recipient Name and Email Address are required.");
      return;
    }

    setLoading(true);
    try {
      await notificationReceiverService.updateReceiver(receiver.id, {
        name: formData.name.trim(),
        email: formData.email.trim().toLowerCase(),
        designation: formData.designation?.trim() || undefined,
        phone: formData.phone?.trim() || undefined,
        status: formData.status,
      });
      success(`Notification receiver "${formData.name}" updated successfully!`);
      onUpdated();
      onClose();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to update notification receiver";
      error(message);
    } finally {
      setLoading(false);
    }
  };

  if (!receiver) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Edit Notification Receiver"
      subtitle={`Update recipient contact details and alert preferences for ${receiver.name}`}
      maxWidth={520}
    >
      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        <div className="form-group">
          <label className="form-label" htmlFor="edit-receiver-name">Recipient Name *</label>
          <input
            id="edit-receiver-name"
            required
            className="form-control"
            placeholder="e.g. Procurement Team or Atik Rahman"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="edit-receiver-email">Recipient Email Address *</label>
          <input
            id="edit-receiver-email"
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
            <label className="form-label" htmlFor="edit-receiver-designation">Designation (Optional)</label>
            <input
              id="edit-receiver-designation"
              className="form-control"
              placeholder="e.g. Head of Procurement / Lead"
              value={formData.designation}
              onChange={(e) => setFormData({ ...formData, designation: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="edit-receiver-phone">Phone Number (Optional)</label>
            <input
              id="edit-receiver-phone"
              type="tel"
              className="form-control"
              placeholder="e.g. +880 1712-345678"
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
            />
          </div>
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="edit-receiver-status">Notification Status</label>

          <select
            id="edit-receiver-status"
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
            {loading ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
            <span>Save Changes</span>
          </button>
        </div>
      </form>
    </Modal>
  );
};
