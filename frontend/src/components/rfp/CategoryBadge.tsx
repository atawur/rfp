"use client";

import React from "react";
import { Sparkles, Loader2, RefreshCw } from "lucide-react";

interface CategoryBadgeProps {
  category?: string | null;
  subCategory?: string | null;
  procurementType?: string | null;
  confidence?: number | null;
  status?: string | null;
  onClassify?: (e: React.MouseEvent) => void;
  isClassifying?: boolean;
  size?: "sm" | "md" | "lg";
}

const CATEGORY_STYLES: Record<
  string,
  { bg: string; color: string; border: string; label: string }
> = {
  software: {
    bg: "rgba(99, 102, 241, 0.15)",
    color: "#a5b4fc",
    border: "rgba(99, 102, 241, 0.35)",
    label: "Software",
  },
  hardware: {
    bg: "rgba(245, 158, 11, 0.15)",
    color: "#fcd34d",
    border: "rgba(245, 158, 11, 0.35)",
    label: "Hardware",
  },
  it_services: {
    bg: "rgba(6, 182, 212, 0.15)",
    color: "#67e8f9",
    border: "rgba(6, 182, 212, 0.35)",
    label: "IT Services",
  },
  cybersecurity: {
    bg: "rgba(244, 63, 94, 0.15)",
    color: "#fda4af",
    border: "rgba(244, 63, 94, 0.35)",
    label: "Cybersecurity",
  },
  cloud: {
    bg: "rgba(14, 165, 233, 0.15)",
    color: "#7dd3fc",
    border: "rgba(14, 165, 233, 0.35)",
    label: "Cloud",
  },
  telecommunications: {
    bg: "rgba(168, 85, 247, 0.15)",
    color: "#d8b4fe",
    border: "rgba(168, 85, 247, 0.35)",
    label: "Telecom",
  },
  professional_services: {
    bg: "rgba(16, 185, 129, 0.15)",
    color: "#6ee7b7",
    border: "rgba(16, 185, 129, 0.35)",
    label: "Professional Services",
  },
  healthcare: {
    bg: "rgba(20, 184, 166, 0.15)",
    color: "#5eead4",
    border: "rgba(20, 184, 166, 0.35)",
    label: "Healthcare",
  },
  construction: {
    bg: "rgba(234, 179, 8, 0.15)",
    color: "#fde047",
    border: "rgba(234, 179, 8, 0.35)",
    label: "Construction",
  },
  security: {
    bg: "rgba(239, 68, 68, 0.15)",
    color: "#fca5a5",
    border: "rgba(239, 68, 68, 0.35)",
    label: "Security",
  },
  transportation: {
    bg: "rgba(59, 130, 246, 0.15)",
    color: "#93c5fd",
    border: "rgba(59, 130, 246, 0.35)",
    label: "Transportation",
  },
  office_supplies: {
    bg: "rgba(148, 163, 184, 0.15)",
    color: "#e2e8f0",
    border: "rgba(148, 163, 184, 0.35)",
    label: "Office Supplies",
  },
  education: {
    bg: "rgba(132, 204, 22, 0.15)",
    color: "#bef264",
    border: "rgba(132, 204, 22, 0.35)",
    label: "Education",
  },
  other: {
    bg: "rgba(255, 255, 255, 0.08)",
    color: "#cbd5e1",
    border: "rgba(255, 255, 255, 0.18)",
    label: "Other",
  },
};

export const CategoryBadge: React.FC<CategoryBadgeProps> = ({
  category,
  subCategory,
  procurementType,
  confidence,
  status,
  onClassify,
  isClassifying = false,
  size = "sm",
}) => {
  const normCategory = (category || "").toLowerCase().trim();
  const style = CATEGORY_STYLES[normCategory] || {
    bg: "rgba(255, 255, 255, 0.06)",
    color: "var(--text-secondary)",
    border: "var(--border-subtle)",
    label: category ? category.replace(/_/g, " ") : "Unclassified",
  };

  // If unclassified or pending
  if (!category) {
    return (
      <div style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}>
        {status === "failed" ? (
          <span
            style={{
              fontSize: size === "sm" ? "0.72rem" : "0.8rem",
              padding: "2px 8px",
              borderRadius: "6px",
              background: "rgba(239, 68, 68, 0.12)",
              color: "#fca5a5",
              border: "1px solid rgba(239, 68, 68, 0.3)",
              fontWeight: 500,
            }}
          >
            Failed
          </span>
        ) : (
          <span
            style={{
              fontSize: size === "sm" ? "0.72rem" : "0.8rem",
              padding: "2px 8px",
              borderRadius: "6px",
              background: "rgba(255, 255, 255, 0.05)",
              color: "var(--text-muted)",
              border: "1px solid var(--border-subtle)",
              fontWeight: 500,
            }}
          >
            Pending
          </span>
        )}

        {onClassify && (
          <button
            type="button"
            onClick={onClassify}
            disabled={isClassifying}
            className="btn btn-secondary btn-sm"
            style={{
              padding: "2px 6px",
              fontSize: "0.7rem",
              gap: "3px",
              height: "22px",
              borderRadius: "4px",
            }}
            title="Classify with AI"
          >
            {isClassifying ? (
              <Loader2 size={11} className="animate-spin" />
            ) : (
              <Sparkles size={11} color="var(--accent-cyan)" />
            )}
            <span>Classify</span>
          </button>
        )}
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "3px", alignItems: "flex-start" }}>
      <div style={{ display: "inline-flex", alignItems: "center", gap: "6px", flexWrap: "wrap" }}>
        {/* Primary category badge */}
        <span
          style={{
            fontSize: size === "sm" ? "0.75rem" : "0.825rem",
            fontWeight: 700,
            padding: size === "sm" ? "3px 8px" : "4px 10px",
            borderRadius: "6px",
            background: style.bg,
            color: style.color,
            border: `1px solid ${style.border}`,
            display: "inline-flex",
            alignItems: "center",
            gap: "5px",
            letterSpacing: "0.01em",
            textTransform: "capitalize",
          }}
          title={confidence ? `AI Confidence: ${(confidence * 100).toFixed(0)}%` : undefined}
        >
          <span>{style.label}</span>
          {confidence !== undefined && confidence !== null && (
            <span
              style={{
                fontSize: "0.65rem",
                opacity: 0.85,
                background: "rgba(0, 0, 0, 0.25)",
                padding: "0 4px",
                borderRadius: "4px",
              }}
            >
              {(confidence * 100).toFixed(0)}%
            </span>
          )}
        </span>

        {/* Procurement type tag if available */}
        {procurementType && (
          <span
            style={{
              fontSize: "0.68rem",
              fontWeight: 600,
              padding: "1px 6px",
              borderRadius: "4px",
              background: "rgba(255, 255, 255, 0.05)",
              color: "var(--text-muted)",
              border: "1px solid var(--border-subtle)",
              textTransform: "capitalize",
            }}
          >
            {procurementType.replace(/_/g, " ")}
          </span>
        )}

        {/* Quick re-classify button */}
        {onClassify && (
          <button
            type="button"
            onClick={onClassify}
            disabled={isClassifying}
            style={{
              background: "transparent",
              border: "none",
              cursor: "pointer",
              padding: "2px",
              display: "inline-flex",
              alignItems: "center",
              color: "var(--text-muted)",
            }}
            title="Re-classify with AI"
          >
            {isClassifying ? (
              <Loader2 size={11} className="animate-spin" />
            ) : (
              <RefreshCw size={11} />
            )}
          </button>
        )}
      </div>

      {/* Subcategory subtitle */}
      {subCategory && subCategory !== "general" && (
        <span
          style={{
            fontSize: "0.725rem",
            color: "var(--text-secondary)",
            fontFamily: "var(--font-mono)",
            textTransform: "lowercase",
            paddingLeft: "2px",
          }}
        >
          ↳ {subCategory.replace(/_/g, " ")}
        </span>
      )}
    </div>
  );
};
