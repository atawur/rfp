"use client";

import React, { useState } from "react";
import { Modal } from "@/components/ui/Modal";
import { rfpService } from "@/services/rfpService";
import { useToast } from "@/context/ToastContext";
import { RFPCreate } from "@/types";
import { Plus, Loader2 } from "lucide-react";

interface RFPCreateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export const RFPCreateModal: React.FC<RFPCreateModalProps> = ({
  isOpen,
  onClose,
  onCreated,
}) => {
  const [formData, setFormData] = useState<RFPCreate>({
    title: "",
    organization: "",
    reference_number: "",
    source_url: "",
    estimated_budget: undefined,
    currency: "USD",
    submission_deadline: "",
    location: "",
    description: "",
    status: "OPEN",
  });
  const [loading, setLoading] = useState(false);
  const { success, error } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.title || !formData.source_url) {
      error("Title and Source URL are required.");
      return;
    }

    setLoading(true);
    try {
      await rfpService.createRFP(formData);
      success("RFP opportunity created successfully!");
      onCreated();
      onClose();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to create RFP";
      error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Create RFP Opportunity"
      subtitle="Manually register a procurement record in the platform database"
      maxWidth={680}
    >
      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        <div className="form-group">
          <label className="form-label" htmlFor="rfp-create-title">RFP Title *</label>
          <input
            id="rfp-create-title"
            required
            className="form-control"
            placeholder="e.g. Supply and Implementation of Cloud Infrastructure"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
          />
        </div>

        <div className="form-grid-2">
          <div className="form-group">
            <label className="form-label" htmlFor="rfp-create-org">Issuing Organization</label>
            <input
              id="rfp-create-org"
              className="form-control"
              placeholder="e.g. Ministry of ICT / City Bank"
              value={formData.organization || ""}
              onChange={(e) => setFormData({ ...formData, organization: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="rfp-create-ref">Reference Number</label>
            <input
              id="rfp-create-ref"
              className="form-control"
              placeholder="e.g. RFP-2026-ICT-008"
              value={formData.reference_number || ""}
              onChange={(e) => setFormData({ ...formData, reference_number: e.target.value })}
            />
          </div>
        </div>

        <div className="form-grid-3">
          <div className="form-group">
            <label className="form-label" htmlFor="rfp-create-budget">Estimated Budget</label>
            <input
              id="rfp-create-budget"
              type="number"
              className="form-control"
              placeholder="e.g. 250000"
              value={formData.estimated_budget || ""}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  estimated_budget: e.target.value ? parseFloat(e.target.value) : undefined,
                })
              }
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="rfp-create-currency">Currency</label>
            <input
              id="rfp-create-currency"
              className="form-control"
              placeholder="USD"
              value={formData.currency || "USD"}
              onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="rfp-create-deadline">Deadline</label>
            <input
              id="rfp-create-deadline"
              type="date"
              className="form-control"
              value={formData.submission_deadline || ""}
              onChange={(e) => setFormData({ ...formData, submission_deadline: e.target.value })}
            />
          </div>
        </div>

        <div className="form-grid-2">
          <div className="form-group">
            <label className="form-label" htmlFor="rfp-create-source">Source URL *</label>
            <input
              id="rfp-create-source"
              type="url"
              required
              className="form-control"
              placeholder="https://example.com/rfp-details"
              value={formData.source_url}
              onChange={(e) => setFormData({ ...formData, source_url: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="rfp-create-location">Location</label>
            <input
              id="rfp-create-location"
              className="form-control"
              placeholder="e.g. New York, USA or Remote"
              value={formData.location || ""}
              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
            />
          </div>
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="rfp-create-desc">Description & Scope</label>
          <textarea
            id="rfp-create-desc"
            rows={3}
            className="form-control"
            placeholder="Detailed description of the tender, delivery timeline, and specifications..."
            value={formData.description || ""}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            style={{ resize: "vertical" }}
          />
        </div>

        <div style={{ display: "flex", justifyContent: "flex-end", gap: "12px", marginTop: "8px", flexWrap: "wrap" }}>
          <button type="button" onClick={onClose} className="btn btn-secondary">
            Cancel
          </button>
          <button type="submit" disabled={loading} className="btn btn-primary">
            {loading ? <Loader2 size={16} className="animate-spin" /> : <Plus size={16} />}
            <span>Save RFP</span>
          </button>
        </div>
      </form>
    </Modal>
  );
};
