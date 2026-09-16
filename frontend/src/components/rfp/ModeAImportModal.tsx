"use client";

import React, { useState } from "react";
import { Modal } from "@/components/ui/Modal";
import { rfpService } from "@/services/rfpService";
import { useToast } from "@/context/ToastContext";
import { RFPProcessResult } from "@/types";
import { Zap, Loader2, CheckCircle2, AlertCircle, ExternalLink, Sparkles } from "lucide-react";
import Link from "next/link";

interface ModeAImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export const ModeAImportModal: React.FC<ModeAImportModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<RFPProcessResult[] | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const { success, error } = useToast();

  const handleImport = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!url || !url.trim()) return;

    setLoading(true);
    setErrorMsg(null);
    setResults(null);

    try {
      const response = await rfpService.importFromUrl(url.trim());
      setResults(response.results);
      success("Mode A Extraction completed successfully!");
      if (onSuccess) onSuccess();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to extract RFP from URL";
      setErrorMsg(message);
      error(message);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setUrl("");
    setResults(null);
    setErrorMsg(null);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Mode A: Direct RFP URL Ingestion"
      subtitle="AI-driven synchronous extraction of procurement opportunities and documents from any direct URL"
      maxWidth={680}
    >
      <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        {/* Info card */}
        <div
          style={{
            background: "rgba(6, 182, 212, 0.08)",
            border: "1px solid rgba(6, 182, 212, 0.2)",
            borderRadius: "10px",
            padding: "14px 16px",
            display: "flex",
            alignItems: "flex-start",
            gap: "12px",
          }}
        >
          <Sparkles size={20} color="#22d3ee" style={{ flexShrink: 0, marginTop: 2 }} />
          <p style={{ fontSize: "0.825rem", color: "#e0f2fe", lineHeight: 1.5 }}>
            Submit an individual RFP page or tender document. The active AI Agent will fetch the content, extract structured data (budget, deadlines, requirements, contacts), validate against schema, and persist to database.
          </p>
        </div>

        {/* Input Form */}
        <form onSubmit={handleImport}>
          <div className="form-group">
            <label className="form-label" htmlFor="rfp-url-input">
              RFP Webpage or Document URL
            </label>
            <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
              <input
                id="rfp-url-input"
                type="url"
                required
                placeholder="https://example.com/procurement/rfp-2026-09"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="form-control"
                disabled={loading}
                style={{ flex: "1 1 240px", minWidth: 0 }}
              />
              <button
                type="submit"
                disabled={loading || !url.trim()}
                className="btn btn-cyan"
                style={{ minWidth: "140px", flex: "1 0 auto" }}
              >
                {loading ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    <span>Extracting...</span>
                  </>
                ) : (
                  <>
                    <Zap size={16} />
                    <span>Extract Now</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Preset Quick Test URL */}
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginTop: "4px", flexWrap: "wrap" }}>
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Sample source:</span>
            <button
              type="button"
              onClick={() => setUrl("https://www.citybankplc.com/rfp/request-for-proposal")}
              style={{
                fontSize: "0.75rem",
                color: "var(--accent-cyan)",
                textDecoration: "underline",
                padding: "2px 4px",
              }}
            >
              City Bank PLC RFPs
            </button>
          </div>
        </form>

        {/* Loading Progress State */}
        {loading && (
          <div
            className="glass-card animate-fade-in"
            style={{
              padding: "20px",
              background: "rgba(15, 23, 42, 0.9)",
              border: "1px solid rgba(6, 182, 212, 0.3)",
              display: "flex",
              flexDirection: "column",
              gap: "12px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <Loader2 size={24} className="animate-spin" color="var(--accent-cyan)" />
              <div>
                <h4 style={{ fontSize: "0.95rem", fontWeight: 700, color: "#ffffff" }}>
                  AI Extraction Pipeline Running
                </h4>
                <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                  Connecting to URL, parsing HTML/documents, and running structured AI extraction...
                </p>
              </div>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginTop: "6px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "0.8rem", color: "#34d399" }}>
                <CheckCircle2 size={14} />
                <span>1. Validated Target URL</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "0.8rem", color: "#38bdf8" }}>
                <Loader2 size={14} className="animate-spin" />
                <span>2. Extracting content & analyzing tender fields with AI</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "0.8rem", color: "var(--text-muted)" }}>
                <span>• 3. Deduplicating and validating schema</span>
              </div>
            </div>
          </div>
        )}

        {/* Error message */}
        {errorMsg && (
          <div
            className="animate-fade-in"
            style={{
              padding: "14px 16px",
              borderRadius: "10px",
              background: "rgba(244, 63, 94, 0.12)",
              border: "1px solid rgba(244, 63, 94, 0.3)",
              display: "flex",
              alignItems: "flex-start",
              gap: "10px",
              color: "#fda4af",
              fontSize: "0.85rem",
            }}
          >
            <AlertCircle size={18} style={{ flexShrink: 0, marginTop: 2 }} />
            <div style={{ flex: 1 }}>
              <strong>Extraction Error:</strong> {errorMsg}
            </div>
          </div>
        )}

        {/* Results State */}
        {results && (
          <div className="animate-fade-in" style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "8px" }}>
              <h4 style={{ fontSize: "0.95rem", fontWeight: 700, color: "#ffffff" }}>
                Extraction Results ({results.length})
              </h4>
              <button onClick={handleReset} className="btn btn-secondary btn-sm">
                Import Another
              </button>
            </div>

            {results.length === 0 ? (
              <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                No RFP items discovered on this page.
              </p>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                {results.map((res, index) => (
                  <div
                    key={index}
                    className="glass-card"
                    style={{
                      padding: "16px",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      gap: "14px",
                      flexWrap: "wrap",
                    }}
                  >
                    <div style={{ flex: 1 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
                        <span
                          className={`badge ${
                            res.status === "inserted"
                              ? "badge-open"
                              : res.status === "updated"
                              ? "badge-updated"
                              : "badge-needs-review"
                          }`}
                        >
                          {res.status}
                        </span>
                        {res.id && (
                          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                            ID #{res.id}
                          </span>
                        )}
                      </div>
                      <h5 style={{ fontSize: "0.9rem", fontWeight: 600, color: "#f8fafc" }}>
                        {res.title || "Untitled RFP"}
                      </h5>
                      {res.reason && (
                        <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "2px" }}>
                          {res.reason}
                        </p>
                      )}
                    </div>

                    {res.id && (
                      <Link
                        href={`/rfps/${res.id}`}
                        onClick={onClose}
                        className="btn btn-secondary btn-sm"
                        style={{ display: "flex", alignItems: "center", gap: "6px" }}
                      >
                        <span>View Details</span>
                        <ExternalLink size={14} />
                      </Link>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </Modal>
  );
};
