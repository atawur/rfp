"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { rfpService } from "@/services/rfpService";
import { RFP } from "@/types";
import { Badge } from "@/components/ui/Badge";
import { CategoryBadge } from "@/components/rfp/CategoryBadge";
import { useToast } from "@/context/ToastContext";
import {
  ArrowLeft,
  Calendar,
  Building,
  DollarSign,
  MapPin,
  ExternalLink,
  Clock,
  FileCheck,
  Send,
  User,
  Mail,
  Phone,
  Hash,
  ShieldCheck,
  Sparkles,
  Loader2,
} from "lucide-react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";

export default function RFPDetailPage() {
  const { isAuthenticated } = useAuth();
  const { success, error } = useToast();
  const params = useParams();
  const router = useRouter();
  const rfpId = params.id ? Number(params.id) : null;

  const [rfp, setRfp] = useState<RFP | null>(null);
  const [loading, setLoading] = useState(true);
  const [classifying, setClassifying] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleClassify = async () => {
    if (!rfp) return;
    setClassifying(true);
    try {
      const updated = await rfpService.classifyRFP(rfp.id, true);
      setRfp(updated);
      success(`RFP classified as "${updated.primary_category}"!`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Classification failed";
      error(msg);
    } finally {
      setClassifying(false);
    }
  };

  useEffect(() => {
    if (!rfpId || !isAuthenticated) return;

    const fetchDetail = async () => {
      setLoading(true);
      try {
        const data = await rfpService.getRFPById(rfpId);
        setRfp(data);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Failed to load RFP";
        setErrorMsg(msg);
      } finally {
        setLoading(false);
      }
    };

    fetchDetail();
  }, [rfpId]);

  if (loading) {
    return (
      <div style={{ padding: "64px", textAlign: "center", color: "var(--text-muted)" }}>
        Loading RFP Opportunity Details...
      </div>
    );
  }

  if (errorMsg || !rfp) {
    return (
      <div className="glass-card" style={{ padding: "40px", textAlign: "center" }}>
        <h2 style={{ color: "var(--accent-rose)", marginBottom: "8px" }}>RFP Not Found</h2>
        <p style={{ color: "var(--text-secondary)", marginBottom: "20px" }}>
          {errorMsg || "The requested procurement record does not exist or has been removed."}
        </p>
        <Link href="/rfps" className="btn btn-secondary">
          <ArrowLeft size={16} />
          <span>Back to RFPs</span>
        </Link>
      </div>
    );
  }

  // Days remaining calculation
  let daysRemaining: number | null = null;
  if (rfp.submission_deadline) {
    const deadline = new Date(rfp.submission_deadline);
    const today = new Date();
    const diffTime = deadline.getTime() - today.getTime();
    daysRemaining = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  }

  const renderList = (data: unknown) => {
    if (!data) return <span style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>None specified</span>;
    if (Array.isArray(data)) {
      return (
        <ul style={{ paddingLeft: "20px", display: "flex", flexDirection: "column", gap: "8px" }}>
          {data.map((item, idx) => (
            <li key={idx} style={{ fontSize: "0.875rem", color: "var(--text-light)", lineHeight: 1.5 }}>
              {typeof item === "object" ? JSON.stringify(item) : String(item)}
            </li>
          ))}
        </ul>
      );
    }
    if (typeof data === "string") {
      return <p style={{ fontSize: "0.875rem", color: "var(--text-light)", lineHeight: 1.6 }}>{data}</p>;
    }
    return (
      <pre style={{ fontSize: "0.8rem", color: "var(--text-light)", overflowX: "auto" }}>
        {JSON.stringify(data, null, 2)}
      </pre>
    );
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
      {/* Breadcrumb & Navigation */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "12px" }}>
        <Link
          href="/rfps"
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            color: "var(--text-secondary)",
            fontSize: "0.875rem",
            fontWeight: 600,
          }}
        >
          <ArrowLeft size={16} />
          <span>Back to Opportunities</span>
        </Link>

        <a
          href={rfp.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="btn btn-cyan btn-sm"
          style={{ display: "flex", alignItems: "center", gap: "6px" }}
        >
          <span>Original RFP Webpage</span>
          <ExternalLink size={14} />
        </a>
      </div>

      {/* Main RFP Header Card */}
      <div
        className="glass-card"
        style={{
          padding: "clamp(20px, 3.5vw, 32px)",
          display: "flex",
          flexDirection: "column",
          gap: "20px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
          <Badge status={rfp.status || "NEW"} />
          <CategoryBadge
            category={rfp.primary_category}
            subCategory={rfp.sub_category}
            procurementType={rfp.procurement_type}
            confidence={rfp.confidence}
            status={rfp.classification_status}
            isClassifying={classifying}
            onClassify={handleClassify}
            size="md"
          />
          <span style={{ fontSize: "0.8rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
            RFP ID #{rfp.id}
          </span>
          {rfp.reference_number && (
            <span
              style={{
                fontSize: "0.8rem",
                color: "var(--accent-cyan)",
                background: "rgba(6, 182, 212, 0.1)",
                padding: "2px 8px",
                borderRadius: 4,
                border: "1px solid rgba(6, 182, 212, 0.2)",
                fontFamily: "var(--font-mono)",
              }}
            >
              REF: {rfp.reference_number}
            </span>
          )}
        </div>

        <h1
          style={{
            fontSize: "clamp(1.35rem, 3vw, 1.75rem)",
            fontWeight: 800,
            color: "#ffffff",
            lineHeight: 1.3,
          }}
        >
          {rfp.title}
        </h1>

        {/* Quick Highlights Bar */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 180px), 1fr))",
            gap: "16px",
            paddingTop: "16px",
            borderTop: "1px solid var(--border-subtle)",
          }}
        >
          <div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "4px" }}>
              ORGANIZATION
            </div>
            <div style={{ fontWeight: 600, color: "#f8fafc", fontSize: "0.95rem" }}>
              {rfp.organization || "Unspecified"}
            </div>
          </div>

          <div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "4px" }}>
              ESTIMATED BUDGET
            </div>
            <div style={{ fontWeight: 700, color: "var(--accent-emerald)", fontSize: "1.05rem" }}>
              {rfp.estimated_budget
                ? `${rfp.currency || "USD"} ${rfp.estimated_budget.toLocaleString()}`
                : "Not Disclosed"}
            </div>
          </div>

          <div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "4px" }}>
              SUBMISSION DEADLINE
            </div>
            <div style={{ fontWeight: 600, color: "#f8fafc", fontSize: "0.95rem" }}>
              {rfp.submission_deadline || "Open-ended"}
            </div>
          </div>

          <div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "4px" }}>
              DEADLINE STATUS
            </div>
            <div
              style={{
                fontWeight: 600,
                fontSize: "0.95rem",
                color: daysRemaining !== null && daysRemaining <= 3 ? "var(--accent-rose)" : "var(--accent-cyan)",
              }}
            >
              {daysRemaining !== null
                ? daysRemaining > 0
                  ? `${daysRemaining} Days Left`
                  : "Deadline Passed"
                : "N/A"}
            </div>
          </div>

          <div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "4px" }}>
              DATE CRAWLED
            </div>
            <div style={{ fontWeight: 600, color: "#f8fafc", fontSize: "0.95rem" }}>
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
      </div>

      {/* Scope, Requirements, and Details Grid */}
      <div className="grid-2col-responsive">
        {/* Left: Summary & Requirements */}
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          {/* AI Category & Scope Classification Card */}
          <div
            className="glass-card"
            style={{
              padding: "24px",
              border: "1px solid rgba(99, 102, 241, 0.3)",
              background: "rgba(15, 23, 42, 0.6)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px", flexWrap: "wrap", gap: "8px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Sparkles size={18} color="var(--accent-cyan)" />
                <h2 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#ffffff" }}>
                  AI Taxonomy & Objective Classification
                </h2>
              </div>

              <button
                type="button"
                onClick={handleClassify}
                disabled={classifying}
                className="btn btn-secondary btn-sm"
                style={{ fontSize: "0.75rem", gap: "6px" }}
              >
                {classifying ? (
                  <Loader2 size={13} className="animate-spin" />
                ) : (
                  <Sparkles size={13} color="var(--accent-cyan)" />
                )}
                <span>{rfp.primary_category ? "Re-run AI Classification" : "Classify with AI"}</span>
              </button>
            </div>

            {rfp.primary_category ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "16px", flexWrap: "wrap" }}>
                  <div>
                    <span style={{ fontSize: "0.72rem", color: "var(--text-muted)", display: "block", marginBottom: "3px" }}>
                      PRIMARY CATEGORY
                    </span>
                    <CategoryBadge
                      category={rfp.primary_category}
                      subCategory={rfp.sub_category}
                      confidence={rfp.confidence}
                      size="md"
                    />
                  </div>

                  {rfp.procurement_type && (
                    <div>
                      <span style={{ fontSize: "0.72rem", color: "var(--text-muted)", display: "block", marginBottom: "3px" }}>
                        PROCUREMENT NATURE
                      </span>
                      <span
                        style={{
                          fontSize: "0.85rem",
                          fontWeight: 600,
                          padding: "4px 12px",
                          borderRadius: "6px",
                          background: "rgba(255, 255, 255, 0.05)",
                          border: "1px solid var(--border-subtle)",
                          color: "#f8fafc",
                          textTransform: "capitalize",
                          display: "inline-block",
                        }}
                      >
                        {rfp.procurement_type.replace(/_/g, " ")}
                      </span>
                    </div>
                  )}

                  {rfp.secondary_categories && rfp.secondary_categories.length > 0 && (
                    <div>
                      <span style={{ fontSize: "0.72rem", color: "var(--text-muted)", display: "block", marginBottom: "3px" }}>
                        SECONDARY CATEGORIES
                      </span>
                      <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                        {rfp.secondary_categories.map((cat, idx) => (
                          <span
                            key={idx}
                            style={{
                              fontSize: "0.75rem",
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

                {rfp.classification_reason && (
                  <div
                    style={{
                      fontSize: "0.875rem",
                      color: "var(--text-light)",
                      background: "rgba(255, 255, 255, 0.03)",
                      padding: "12px 16px",
                      borderRadius: "8px",
                      borderLeft: "3px solid var(--accent-cyan)",
                      lineHeight: 1.5,
                    }}
                  >
                    <strong style={{ color: "var(--accent-cyan)" }}>Classification Objective: </strong>
                    {rfp.classification_reason}
                  </div>
                )}

                {rfp.keywords && rfp.keywords.length > 0 && (
                  <div style={{ display: "flex", alignItems: "center", gap: "6px", flexWrap: "wrap" }}>
                    <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Keywords:</span>
                    {rfp.keywords.map((kw, idx) => (
                      <span
                        key={idx}
                        style={{
                          fontSize: "0.75rem",
                          padding: "2px 8px",
                          borderRadius: "4px",
                          background: "rgba(99, 102, 241, 0.12)",
                          color: "#a5b4fc",
                          border: "1px solid rgba(99, 102, 241, 0.25)",
                        }}
                      >
                        {kw}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <p style={{ fontSize: "0.875rem", color: "var(--text-muted)" }}>
                This opportunity has not been categorized yet. Click &quot;Classify with AI&quot; above to run automated classification.
              </p>
            )}
          </div>

          {/* Summary */}
          <div className="glass-card" style={{ padding: "24px" }}>
            <h2 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#ffffff", marginBottom: "14px" }}>
              Scope of Work & Overview
            </h2>
            <div
              style={{
                fontSize: "0.9rem",
                lineHeight: 1.7,
                color: "var(--text-light)",
                whiteSpace: "pre-wrap",
              }}
            >
              {rfp.description || "No full description extracted for this procurement notice."}
            </div>
          </div>

          {/* Key Requirements */}
          <div className="glass-card" style={{ padding: "24px" }}>
            <h2
              style={{
                fontSize: "1.1rem",
                fontWeight: 700,
                color: "#ffffff",
                marginBottom: "14px",
                display: "flex",
                alignItems: "center",
                gap: "8px",
              }}
            >
              <FileCheck size={18} color="var(--accent-cyan)" />
              <span>Extracted Requirements & Deliverables</span>
            </h2>
            {renderList(rfp.requirements)}
          </div>

          {/* Eligibility */}
          <div className="glass-card" style={{ padding: "24px" }}>
            <h2
              style={{
                fontSize: "1.1rem",
                fontWeight: 700,
                color: "#ffffff",
                marginBottom: "14px",
                display: "flex",
                alignItems: "center",
                gap: "8px",
              }}
            >
              <Send size={18} color="var(--accent-violet)" />
              <span>Eligibility & Qualification Criteria</span>
            </h2>
            {renderList(rfp.eligibility)}
          </div>
        </div>

        {/* Right: Contact, Ingestion, and System Metadata */}
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          {/* Contact Details */}
          <div className="glass-card" style={{ padding: "24px" }}>
            <h3 style={{ fontSize: "1rem", fontWeight: 700, color: "#ffffff", marginBottom: "16px" }}>
              Inquiries & Contact
            </h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "12px", fontSize: "0.85rem" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <User size={16} color="var(--text-muted)" />
                <span style={{ color: "var(--text-light)" }}>
                  {rfp.contact_person || "Contact Person Unspecified"}
                </span>
              </div>

              {rfp.contact_email && (
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <Mail size={16} color="var(--text-muted)" />
                  <a
                    href={`mailto:${rfp.contact_email}`}
                    style={{ color: "var(--accent-cyan)", textDecoration: "underline" }}
                  >
                    {rfp.contact_email}
                  </a>
                </div>
              )}

              {rfp.contact_phone && (
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <Phone size={16} color="var(--text-muted)" />
                  <span style={{ color: "var(--text-light)" }}>{rfp.contact_phone}</span>
                </div>
              )}

              {rfp.submission_method && (
                <div style={{ marginTop: "8px", paddingTop: "10px", borderTop: "1px solid var(--border-subtle)" }}>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "4px" }}>
                    SUBMISSION METHOD
                  </div>
                  <span style={{ color: "var(--text-light)" }}>{rfp.submission_method}</span>
                </div>
              )}
            </div>
          </div>

          {/* Ingestion & Verification Metadata */}
          <div className="glass-card" style={{ padding: "24px" }}>
            <h3
              style={{
                fontSize: "1rem",
                fontWeight: 700,
                color: "#ffffff",
                marginBottom: "16px",
                display: "flex",
                alignItems: "center",
                gap: "8px",
              }}
            >
              <ShieldCheck size={18} color="var(--accent-emerald)" />
              <span>Ingestion Identity</span>
            </h3>

            <div style={{ display: "flex", flexDirection: "column", gap: "10px", fontSize: "0.775rem" }}>
              <div>
                <span style={{ color: "var(--text-muted)" }}>Date Crawled:</span>{" "}
                <span style={{ color: "var(--text-light)" }}>
                  {rfp.first_seen_at
                    ? new Date(rfp.first_seen_at).toLocaleString()
                    : rfp.created_at
                    ? new Date(rfp.created_at).toLocaleString()
                    : "N/A"}
                </span>
              </div>

              <div>
                <span style={{ color: "var(--text-muted)" }}>Last Checked:</span>{" "}
                <span style={{ color: "var(--text-light)" }}>
                  {rfp.last_seen_at ? new Date(rfp.last_seen_at).toLocaleString() : "N/A"}
                </span>
              </div>

              {rfp.content_hash && (
                <div>
                  <div style={{ color: "var(--text-muted)", marginBottom: "4px" }}>Content Fingerprint:</div>
                  <code
                    style={{
                      background: "rgba(0,0,0,0.4)",
                      padding: "4px 8px",
                      borderRadius: "6px",
                      color: "var(--accent-cyan)",
                      fontFamily: "var(--font-mono)",
                      fontSize: "0.7rem",
                      display: "block",
                      wordBreak: "break-all",
                    }}
                  >
                    {rfp.content_hash}
                  </code>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
