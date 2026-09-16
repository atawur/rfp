"use client";

import React, { useState, useEffect } from "react";
import { Modal } from "@/components/ui/Modal";
import { Badge } from "@/components/ui/Badge";
import { CategoryBadge } from "@/components/rfp/CategoryBadge";
import { rfpService } from "@/services/rfpService";
import { useToast } from "@/context/ToastContext";
import { RFP } from "@/types";
import {
  Calendar,
  Building,
  DollarSign,
  MapPin,
  Mail,
  Phone,
  User as UserIcon,
  ExternalLink,
  Clock,
  FileCheck,
  Send,
  Sparkles,
  Loader2,
} from "lucide-react";

interface RFPDetailModalProps {
  rfp: RFP | null;
  isOpen: boolean;
  onClose: () => void;
  onUpdated?: (updated: RFP) => void;
}

export const RFPDetailModal: React.FC<RFPDetailModalProps> = ({
  rfp,
  isOpen,
  onClose,
  onUpdated,
}) => {
  const [currentRfp, setCurrentRfp] = useState<RFP | null>(rfp);
  const [classifying, setClassifying] = useState(false);
  const { success, error } = useToast();

  useEffect(() => {
    setCurrentRfp(rfp);
  }, [rfp]);

  if (!rfp || !currentRfp) return null;

  const handleClassify = async () => {
    if (!currentRfp) return;
    setClassifying(true);
    try {
      const updated = await rfpService.classifyRFP(currentRfp.id, true);
      setCurrentRfp(updated);
      onUpdated?.(updated);
      success(`RFP classified as "${updated.primary_category}"!`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Classification failed";
      error(msg);
    } finally {
      setClassifying(false);
    }
  };

  // Calculate days remaining if submission_deadline is present
  let daysRemaining: number | null = null;
  if (currentRfp.submission_deadline) {
    const deadline = new Date(currentRfp.submission_deadline);
    const today = new Date();
    const diffTime = deadline.getTime() - today.getTime();
    daysRemaining = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  }

  // Parse eligibility/requirements if string or json
  const renderList = (data: unknown) => {
    if (!data) return <span style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>None specified</span>;
    if (Array.isArray(data)) {
      return (
        <ul style={{ paddingLeft: "20px", display: "flex", flexDirection: "column", gap: "6px" }}>
          {data.map((item, idx) => (
            <li key={idx} style={{ fontSize: "0.85rem", color: "var(--text-light)" }}>
              {typeof item === "object" ? JSON.stringify(item) : String(item)}
            </li>
          ))}
        </ul>
      );
    }
    if (typeof data === "string") {
      return <p style={{ fontSize: "0.85rem", color: "var(--text-light)", lineHeight: 1.5 }}>{data}</p>;
    }
    return (
      <pre style={{ fontSize: "0.8rem", color: "var(--text-light)", overflowX: "auto" }}>
        {JSON.stringify(data, null, 2)}
      </pre>
    );
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={rfp.title}
      subtitle={`RFP #${rfp.id} • Reference: ${rfp.reference_number || rfp.external_rfp_id || "N/A"}`}
      maxWidth={760}
    >
      <div style={{ display: "flex", flexDirection: "column", gap: "22px" }}>
        {/* Status & Deadline Highlights */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "12px",
            background: "rgba(255, 255, 255, 0.03)",
            padding: "14px 18px",
            borderRadius: "12px",
            border: "1px solid var(--border-subtle)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>Status:</span>
            <Badge status={rfp.status || "NEW"} />
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
            {daysRemaining !== null && (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  fontSize: "0.825rem",
                  fontWeight: 600,
                  color: daysRemaining <= 3 ? "var(--accent-rose)" : "var(--accent-cyan)",
                }}
              >
                <Clock size={16} />
                <span>
                  {daysRemaining > 0
                    ? `${daysRemaining} days remaining`
                    : daysRemaining === 0
                    ? "Due Today"
                    : `${Math.abs(daysRemaining)} days overdue`}
                </span>
              </div>
            )}

            <a
              href={currentRfp.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-secondary btn-sm"
              style={{ display: "flex", alignItems: "center", gap: "6px" }}
            >
              <span>View Source</span>
              <ExternalLink size={14} />
            </a>
          </div>
        </div>

        {/* AI Category Classification Section */}
        <div
          style={{
            background: "rgba(15, 23, 42, 0.6)",
            border: "1px solid rgba(99, 102, 241, 0.25)",
            borderRadius: "12px",
            padding: "16px 18px",
            display: "flex",
            flexDirection: "column",
            gap: "12px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "8px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <Sparkles size={16} color="var(--accent-cyan)" />
              <span style={{ fontSize: "0.85rem", fontWeight: 700, color: "#ffffff", letterSpacing: "0.01em" }}>
                AI Taxonomy & Scope Classification
              </span>
              {currentRfp.classification_status && (
                <span
                  style={{
                    fontSize: "0.68rem",
                    padding: "2px 6px",
                    borderRadius: "4px",
                    background:
                      currentRfp.classification_status === "completed"
                        ? "rgba(16, 185, 129, 0.15)"
                        : "rgba(245, 158, 11, 0.15)",
                    color:
                      currentRfp.classification_status === "completed"
                        ? "#34d399"
                        : "#fbbf24",
                    textTransform: "uppercase",
                    fontWeight: 700,
                  }}
                >
                  {currentRfp.classification_status}
                </span>
              )}
            </div>

            <button
              type="button"
              onClick={handleClassify}
              disabled={classifying}
              className="btn btn-secondary btn-sm"
              style={{ padding: "4px 10px", fontSize: "0.75rem", gap: "6px" }}
            >
              {classifying ? (
                <Loader2 size={13} className="animate-spin" />
              ) : (
                <Sparkles size={13} color="var(--accent-cyan)" />
              )}
              <span>{currentRfp.primary_category ? "Re-run AI Classification" : "Classify with AI"}</span>
            </button>
          </div>

          {currentRfp.primary_category ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "16px", flexWrap: "wrap" }}>
                <div>
                  <span style={{ fontSize: "0.72rem", color: "var(--text-muted)", display: "block", marginBottom: "3px" }}>
                    PRIMARY CATEGORY
                  </span>
                  <CategoryBadge
                    category={currentRfp.primary_category}
                    subCategory={currentRfp.sub_category}
                    confidence={currentRfp.confidence}
                    size="md"
                  />
                </div>

                {currentRfp.procurement_type && (
                  <div>
                    <span style={{ fontSize: "0.72rem", color: "var(--text-muted)", display: "block", marginBottom: "3px" }}>
                      PROCUREMENT TYPE
                    </span>
                    <span
                      style={{
                        fontSize: "0.8rem",
                        fontWeight: 600,
                        padding: "4px 10px",
                        borderRadius: "6px",
                        background: "rgba(255, 255, 255, 0.05)",
                        border: "1px solid var(--border-subtle)",
                        color: "#f8fafc",
                        textTransform: "capitalize",
                        display: "inline-block",
                      }}
                    >
                      {currentRfp.procurement_type.replace(/_/g, " ")}
                    </span>
                  </div>
                )}

                {currentRfp.secondary_categories && currentRfp.secondary_categories.length > 0 && (
                  <div>
                    <span style={{ fontSize: "0.72rem", color: "var(--text-muted)", display: "block", marginBottom: "3px" }}>
                      SECONDARY CATEGORIES
                    </span>
                    <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                      {currentRfp.secondary_categories.map((cat, idx) => (
                        <span
                          key={idx}
                          style={{
                            fontSize: "0.72rem",
                            padding: "3px 8px",
                            borderRadius: "4px",
                            background: "rgba(255, 255, 255, 0.05)",
                            color: "var(--text-secondary)",
                            textTransform: "capitalize",
                          }}
                        >
                          {cat.replace(/_/g, " ")}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {currentRfp.classification_reason && (
                <div
                  style={{
                    fontSize: "0.8rem",
                    color: "var(--text-light)",
                    background: "rgba(255, 255, 255, 0.03)",
                    padding: "8px 12px",
                    borderRadius: "6px",
                    borderLeft: "3px solid var(--accent-cyan)",
                    lineHeight: 1.4,
                  }}
                >
                  <span style={{ fontWeight: 600, color: "var(--accent-cyan)" }}>Objective Justification: </span>
                  {currentRfp.classification_reason}
                </div>
              )}

              {currentRfp.keywords && currentRfp.keywords.length > 0 && (
                <div style={{ display: "flex", alignItems: "center", gap: "6px", flexWrap: "wrap" }}>
                  <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>Keywords:</span>
                  {currentRfp.keywords.map((kw, idx) => (
                    <span
                      key={idx}
                      style={{
                        fontSize: "0.7rem",
                        padding: "1px 6px",
                        borderRadius: "4px",
                        background: "rgba(99, 102, 241, 0.1)",
                        color: "#a5b4fc",
                        border: "1px solid rgba(99, 102, 241, 0.2)",
                      }}
                    >
                      {kw}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
              No AI category assigned yet. Click &quot;Classify with AI&quot; to run automated taxonomy classification.
            </div>
          )}
        </div>

        {/* Metadata Grid */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 180px), 1fr))",
            gap: "16px",
          }}
        >
          {/* Organization */}
          <div
            style={{
              padding: "12px",
              borderRadius: "10px",
              background: "rgba(255, 255, 255, 0.02)",
              border: "1px solid var(--border-subtle)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "var(--text-muted)", fontSize: "0.75rem", marginBottom: "4px" }}>
              <Building size={14} />
              <span>ORGANIZATION</span>
            </div>
            <div style={{ fontSize: "0.9rem", fontWeight: 600, color: "#ffffff" }}>
              {rfp.organization || "Unspecified"}
            </div>
          </div>

          {/* Budget */}
          <div
            style={{
              padding: "12px",
              borderRadius: "10px",
              background: "rgba(255, 255, 255, 0.02)",
              border: "1px solid var(--border-subtle)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "var(--text-muted)", fontSize: "0.75rem", marginBottom: "4px" }}>
              <DollarSign size={14} />
              <span>ESTIMATED BUDGET</span>
            </div>
            <div style={{ fontSize: "0.9rem", fontWeight: 600, color: "var(--accent-emerald)" }}>
              {rfp.estimated_budget
                ? `${rfp.currency || "USD"} ${rfp.estimated_budget.toLocaleString()}`
                : "Not Disclosed"}
            </div>
          </div>

          {/* Deadline */}
          <div
            style={{
              padding: "12px",
              borderRadius: "10px",
              background: "rgba(255, 255, 255, 0.02)",
              border: "1px solid var(--border-subtle)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "var(--text-muted)", fontSize: "0.75rem", marginBottom: "4px" }}>
              <Calendar size={14} />
              <span>SUBMISSION DEADLINE</span>
            </div>
            <div style={{ fontSize: "0.9rem", fontWeight: 600, color: "#ffffff" }}>
              {rfp.submission_deadline || "No deadline posted"}
            </div>
          </div>

          {/* Location */}
          <div
            style={{
              padding: "12px",
              borderRadius: "10px",
              background: "rgba(255, 255, 255, 0.02)",
              border: "1px solid var(--border-subtle)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "var(--text-muted)", fontSize: "0.75rem", marginBottom: "4px" }}>
              <MapPin size={14} />
              <span>LOCATION</span>
            </div>
            <div style={{ fontSize: "0.9rem", fontWeight: 600, color: "#ffffff" }}>
              {rfp.location || "Global / Unspecified"}
            </div>
          </div>

          {/* Crawled Date */}
          <div
            style={{
              padding: "12px",
              borderRadius: "10px",
              background: "rgba(255, 255, 255, 0.02)",
              border: "1px solid var(--border-subtle)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "var(--text-muted)", fontSize: "0.75rem", marginBottom: "4px" }}>
              <Clock size={14} color="var(--accent-cyan)" />
              <span>DATE CRAWLED</span>
            </div>
            <div style={{ fontSize: "0.9rem", fontWeight: 600, color: "#ffffff" }}>
              {rfp.first_seen_at
                ? new Date(rfp.first_seen_at).toLocaleDateString(undefined, {
                    year: "numeric",
                    month: "short",
                    day: "numeric",
                  })
                : rfp.created_at
                ? new Date(rfp.created_at).toLocaleDateString(undefined, {
                    year: "numeric",
                    month: "short",
                    day: "numeric",
                  })
                : "N/A"}
            </div>
          </div>
        </div>

        {/* Description */}
        <div>
          <h4 style={{ fontSize: "0.9rem", fontWeight: 700, color: "#ffffff", marginBottom: "8px" }}>
            Summary & Scope
          </h4>
          <div
            style={{
              padding: "16px",
              borderRadius: "10px",
              background: "rgba(255, 255, 255, 0.02)",
              border: "1px solid var(--border-subtle)",
              fontSize: "0.875rem",
              lineHeight: 1.6,
              color: "var(--text-light)",
            }}
          >
            {rfp.description || "No description extracted for this procurement notice."}
          </div>
        </div>

        {/* Requirements & Eligibility Tabs/Sections */}
        <div className="form-grid-2">
          <div>
            <h4 style={{ fontSize: "0.9rem", fontWeight: 700, color: "#ffffff", marginBottom: "8px", display: "flex", alignItems: "center", gap: "6px" }}>
              <FileCheck size={16} color="var(--accent-cyan)" />
              <span>Key Requirements</span>
            </h4>
            <div
              style={{
                padding: "14px",
                borderRadius: "10px",
                background: "rgba(255, 255, 255, 0.02)",
                border: "1px solid var(--border-subtle)",
                minHeight: "100px",
              }}
            >
              {renderList(rfp.requirements)}
            </div>
          </div>

          <div>
            <h4 style={{ fontSize: "0.9rem", fontWeight: 700, color: "#ffffff", marginBottom: "8px", display: "flex", alignItems: "center", gap: "6px" }}>
              <Send size={16} color="var(--accent-violet)" />
              <span>Eligibility Criteria</span>
            </h4>
            <div
              style={{
                padding: "14px",
                borderRadius: "10px",
                background: "rgba(255, 255, 255, 0.02)",
                border: "1px solid var(--border-subtle)",
                minHeight: "100px",
              }}
            >
              {renderList(rfp.eligibility)}
            </div>
          </div>
        </div>

        {/* Contact Information */}
        <div
          style={{
            padding: "14px 18px",
            borderRadius: "10px",
            background: "rgba(255, 255, 255, 0.02)",
            border: "1px solid var(--border-subtle)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "14px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <UserIcon size={16} color="var(--text-muted)" />
            <span style={{ fontSize: "0.85rem", color: "var(--text-light)" }}>
              {rfp.contact_person || "Contact Person N/A"}
            </span>
          </div>

          {rfp.contact_email && (
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <Mail size={16} color="var(--text-muted)" />
              <a
                href={`mailto:${rfp.contact_email}`}
                style={{ fontSize: "0.85rem", color: "var(--accent-cyan)", textDecoration: "underline" }}
              >
                {rfp.contact_email}
              </a>
            </div>
          )}

          {rfp.contact_phone && (
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <Phone size={16} color="var(--text-muted)" />
              <span style={{ fontSize: "0.85rem", color: "var(--text-light)" }}>
                {rfp.contact_phone}
              </span>
            </div>
          )}
        </div>
      </div>
    </Modal>
  );
};
