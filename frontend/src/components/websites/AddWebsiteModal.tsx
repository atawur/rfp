"use client";

import React, { useState, useEffect } from "react";
import { Modal } from "@/components/ui/Modal";
import { websiteService } from "@/services/websiteService";
import { notificationReceiverService } from "@/services/notificationReceiverService";
import { useToast } from "@/context/ToastContext";
import { WebsiteCreate, NotificationReceiver } from "@/types";
import { Globe, Plus, Loader2, Bell, Users, CheckSquare, Square } from "lucide-react";

interface AddWebsiteModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export const AddWebsiteModal: React.FC<AddWebsiteModalProps> = ({
  isOpen,
  onClose,
  onCreated,
}) => {
  const [formData, setFormData] = useState<WebsiteCreate>({
    name: "",
    base_url: "",
    start_url: "",
    status: "active",
    crawl_frequency: "daily",
    notify_all_receivers: true,
    receiver_ids: [],
  });

  const [notifyAllReceivers, setNotifyAllReceivers] = useState(true);
  const [selectedReceiverIds, setSelectedReceiverIds] = useState<number[]>([]);
  const [activeReceivers, setActiveReceivers] = useState<NotificationReceiver[]>([]);
  const [loadingReceivers, setLoadingReceivers] = useState(false);
  const [loading, setLoading] = useState(false);
  const { success, error } = useToast();

  useEffect(() => {
    if (isOpen) {
      const loadReceivers = async () => {
        setLoadingReceivers(true);
        try {
          const receivers = await notificationReceiverService.getActiveReceivers();
          setActiveReceivers(receivers);
          // Default to all active receivers if specific selection chosen
          setSelectedReceiverIds(receivers.map((r) => r.id));
        } catch {
          // silently handle
        } finally {
          setLoadingReceivers(false);
        }
      };
      loadReceivers();
    }
  }, [isOpen]);

  const handleToggleReceiver = (id: number) => {
    setSelectedReceiverIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const handleSelectAll = () => {
    setSelectedReceiverIds(activeReceivers.map((r) => r.id));
  };

  const handleClearAll = () => {
    setSelectedReceiverIds([]);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name || !formData.base_url || !formData.start_url) {
      error("Name, Base URL, and Start URL are required.");
      return;
    }

    if (!notifyAllReceivers && selectedReceiverIds.length === 0) {
      error("Please select at least one notification receiver or choose 'All Notification Receivers'.");
      return;
    }

    setLoading(true);
    try {
      await websiteService.createWebsite({
        ...formData,
        notify_all_receivers: notifyAllReceivers,
        receiver_ids: notifyAllReceivers ? [] : selectedReceiverIds,
      });
      success("Monitored website source registered successfully!");
      onCreated();
      onClose();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to register website";
      error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Register Monitored RFP Source"
      subtitle="Configure a recurring website source for Mode B daily crawling and automated discovery"
      maxWidth={600}
    >
      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        <div className="form-group">
          <label className="form-label" htmlFor="website-name">Source Name *</label>
          <input
            id="website-name"
            required
            className="form-control"
            placeholder="e.g. City Bank Procurement Portal"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="website-base-url">Base URL *</label>
          <input
            id="website-base-url"
            type="url"
            required
            className="form-control"
            placeholder="https://www.citybankplc.com"
            value={formData.base_url}
            onChange={(e) => setFormData({ ...formData, base_url: e.target.value })}
          />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="website-start-url">Tenders / RFP Listing URL *</label>
          <input
            id="website-start-url"
            type="url"
            required
            className="form-control"
            placeholder="https://www.citybankplc.com/rfp/request-for-proposal"
            value={formData.start_url}
            onChange={(e) => setFormData({ ...formData, start_url: e.target.value })}
          />
        </div>

        <div className="form-grid-2">
          <div className="form-group">
            <label className="form-label" htmlFor="website-status">Monitoring Status</label>
            <select
              id="website-status"
              className="form-control"
              value={formData.status}
              onChange={(e) => setFormData({ ...formData, status: e.target.value })}
            >
              <option value="active">Active (Daily Crawl)</option>
              <option value="inactive">Inactive (Paused)</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="website-freq">Crawl Frequency</label>
            <select
              id="website-freq"
              className="form-control"
              value={formData.crawl_frequency}
              onChange={(e) => setFormData({ ...formData, crawl_frequency: e.target.value })}
            >
              <option value="daily">Daily</option>
              <option value="hourly">Hourly</option>
              <option value="weekly">Weekly</option>
            </select>
          </div>
        </div>

        {/* Notification Receivers Configuration */}
        <div
          style={{
            background: "rgba(255, 255, 255, 0.03)",
            border: "1px solid var(--border-color)",
            borderRadius: "var(--radius-md)",
            padding: "16px",
            display: "flex",
            flexDirection: "column",
            gap: "12px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Bell size={16} color="var(--accent-cyan)" />
            <span style={{ fontWeight: 700, fontSize: "0.9rem", color: "#ffffff" }}>
              Email Notification Recipients
            </span>
          </div>
          <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", margin: 0 }}>
            Specify which notification receiver contacts receive alerts when new RFPs are discovered on this portal.
          </p>

          <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginTop: "4px" }}>
            {/* Option 1: All Receivers */}
            <label
              style={{
                display: "flex",
                alignItems: "flex-start",
                gap: "10px",
                cursor: "pointer",
                padding: "10px 12px",
                borderRadius: "var(--radius-sm)",
                background: notifyAllReceivers ? "rgba(6, 182, 212, 0.08)" : "transparent",
                border: notifyAllReceivers ? "1px solid rgba(6, 182, 212, 0.3)" : "1px solid transparent",
              }}
            >
              <input
                type="radio"
                name="receiver_selection"
                checked={notifyAllReceivers}
                onChange={() => setNotifyAllReceivers(true)}
                style={{ marginTop: "3px", cursor: "pointer" }}
              />
              <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "#ffffff" }}>
                  All Notification Receivers (Broadcast)
                </span>
                <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                  All current and future active notification receiver contacts will receive alerts for this website.
                </span>
              </div>
            </label>

            {/* Option 2: Specific Receivers */}
            <label
              style={{
                display: "flex",
                alignItems: "flex-start",
                gap: "10px",
                cursor: "pointer",
                padding: "10px 12px",
                borderRadius: "var(--radius-sm)",
                background: !notifyAllReceivers ? "rgba(99, 102, 241, 0.08)" : "transparent",
                border: !notifyAllReceivers ? "1px solid rgba(99, 102, 241, 0.3)" : "1px solid transparent",
              }}
            >
              <input
                type="radio"
                name="receiver_selection"
                checked={!notifyAllReceivers}
                onChange={() => setNotifyAllReceivers(false)}
                style={{ marginTop: "3px", cursor: "pointer" }}
              />
              <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "#ffffff" }}>
                  Select Specific Receivers
                </span>
                <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                  Only selected recipient contacts from the list below will be alerted.
                </span>
              </div>
            </label>
          </div>

          {/* Checklist when specific is selected */}
          {!notifyAllReceivers && (
            <div
              style={{
                marginTop: "8px",
                borderTop: "1px solid var(--border-subtle)",
                paddingTop: "12px",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: "8px",
                }}
              >
                <span style={{ fontSize: "0.775rem", color: "var(--text-muted)", fontWeight: 600 }}>
                  Active Contacts ({selectedReceiverIds.length}/{activeReceivers.length} selected)
                </span>
                <div style={{ display: "flex", gap: "10px" }}>
                  <button
                    type="button"
                    onClick={handleSelectAll}
                    style={{ background: "none", border: "none", color: "var(--accent-cyan)", fontSize: "0.75rem", cursor: "pointer" }}
                  >
                    Select All
                  </button>
                  <span style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>|</span>
                  <button
                    type="button"
                    onClick={handleClearAll}
                    style={{ background: "none", border: "none", color: "var(--text-muted)", fontSize: "0.75rem", cursor: "pointer" }}
                  >
                    Clear
                  </button>
                </div>
              </div>

              {loadingReceivers ? (
                <div style={{ padding: "16px", textAlign: "center", color: "var(--text-muted)", fontSize: "0.8rem" }}>
                  <Loader2 size={14} className="animate-spin" style={{ display: "inline-block", marginRight: "6px" }} />
                  Loading receivers...
                </div>
              ) : activeReceivers.length === 0 ? (
                <div style={{ padding: "16px", textAlign: "center", color: "var(--text-muted)", fontSize: "0.8rem" }}>
                  No active notification receivers found. Please add contacts in the Notification Receivers menu first.
                </div>
              ) : (
                <div
                  style={{
                    maxHeight: "180px",
                    overflowY: "auto",
                    display: "flex",
                    flexDirection: "column",
                    gap: "6px",
                    paddingRight: "4px",
                  }}
                >
                  {activeReceivers.map((rec) => {
                    const isChecked = selectedReceiverIds.includes(rec.id);
                    return (
                      <div
                        key={rec.id}
                        onClick={() => handleToggleReceiver(rec.id)}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "10px",
                          padding: "8px 10px",
                          borderRadius: "6px",
                          background: isChecked ? "rgba(99, 102, 241, 0.12)" : "rgba(255, 255, 255, 0.02)",
                          border: isChecked ? "1px solid rgba(99, 102, 241, 0.35)" : "1px solid var(--border-subtle)",
                          cursor: "pointer",
                        }}
                      >
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => {}} // handled by div
                          style={{ cursor: "pointer" }}
                        />
                        <div style={{ display: "flex", flexDirection: "column", fontSize: "0.825rem" }}>
                          <span style={{ fontWeight: 600, color: "#ffffff" }}>{rec.name}</span>
                          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{rec.email}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </div>

        <div style={{ display: "flex", justifyContent: "flex-end", gap: "12px", marginTop: "12px", flexWrap: "wrap" }}>
          <button type="button" onClick={onClose} className="btn btn-secondary">
            Cancel
          </button>
          <button type="submit" disabled={loading} className="btn btn-primary">
            {loading ? <Loader2 size={16} className="animate-spin" /> : <Plus size={16} />}
            <span>Register Source</span>
          </button>
        </div>
      </form>
    </Modal>
  );
};
