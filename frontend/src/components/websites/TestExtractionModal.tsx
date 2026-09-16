"use client";

import React, { useState } from "react";
import { Modal } from "@/components/ui/Modal";
import { websiteService } from "@/services/websiteService";
import { useToast } from "@/context/ToastContext";
import { Sparkles, Loader2, Code2, CheckCircle2 } from "lucide-react";

interface TestExtractionModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultUrl?: string;
}

export const TestExtractionModal: React.FC<TestExtractionModalProps> = ({
  isOpen,
  onClose,
  defaultUrl = "",
}) => {
  const [url, setUrl] = useState(defaultUrl);
  const [loading, setLoading] = useState(false);
  const [rawResult, setRawResult] = useState<unknown | null>(null);
  const { success, error } = useToast();

  const handleTest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url || !url.trim()) return;

    setLoading(true);
    setRawResult(null);

    try {
      const res = await websiteService.testExtraction(url.trim());
      setRawResult(res);
      success("Extraction test executed successfully!");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Test extraction failed";
      error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="AI Extraction Playground & Tester"
      subtitle="Synchronously test AI parsing on any target URL without mutating live data"
      maxWidth={720}
    >
      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        <form onSubmit={handleTest}>
          <div className="form-group">
            <label className="form-label" htmlFor="test-url">Test Webpage or Document URL</label>
            <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
              <input
                id="test-url"
                type="url"
                required
                className="form-control"
                placeholder="https://example.com/rfp-page"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                disabled={loading}
                style={{ flex: "1 1 220px", minWidth: 0 }}
              />
              <button
                type="submit"
                disabled={loading || !url.trim()}
                className="btn btn-primary"
                style={{ minWidth: "130px", flex: "1 0 auto" }}
              >
                {loading ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
                <span>Run Test</span>
              </button>
            </div>
          </div>
        </form>

        {loading && (
          <div
            className="glass-card animate-fade-in"
            style={{
              padding: "24px",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              gap: "12px",
              textAlign: "center",
            }}
          >
            <Loader2 size={32} className="animate-spin" color="var(--accent-primary)" />
            <div style={{ fontWeight: 600, color: "#ffffff" }}>Fetching and parsing page...</div>
            <p style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
              The active AI model is analyzing unstructured text, evaluating RFP fields, and computing confidence.
            </p>
          </div>
        )}

        {rawResult !== null && (
          <div className="animate-fade-in" style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "6px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "#34d399", fontSize: "0.85rem", fontWeight: 600 }}>
                <CheckCircle2 size={16} />
                <span>AI Pipeline Response</span>
              </div>
              <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                JSON Payload
              </span>
            </div>

            <pre
              style={{
                background: "rgba(10, 15, 29, 0.95)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "10px",
                padding: "16px",
                fontSize: "0.8rem",
                color: "#93c5fd",
                maxHeight: "360px",
                overflowY: "auto",
                overflowX: "auto",
                fontFamily: "var(--font-mono)",
                lineHeight: 1.5,
              }}
            >
              {JSON.stringify(rawResult, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </Modal>
  );
};
