"use client";

import React, { useEffect, useState } from "react";
import { rfpService } from "@/services/rfpService";
import { websiteService } from "@/services/websiteService";
import { agentConfigService } from "@/services/agentConfigService";
import { RFP, Website, AIAgentConfig } from "@/types";
import { StatCard } from "@/components/ui/StatCard";
import { Badge } from "@/components/ui/Badge";
import { RFPDetailModal } from "@/components/rfp/RFPDetailModal";
import { ModeAImportModal } from "@/components/rfp/ModeAImportModal";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import {
  FileText,
  Globe,
  Bot,
  AlertTriangle,
  Zap,
  Play,
  ArrowRight,
  ExternalLink,
  Calendar,
  Sparkles,
  Search,
  CheckCircle2,
  Loader2,
} from "lucide-react";
import Link from "next/link";

export default function DashboardPage() {
  const { isAuthenticated } = useAuth();
  const [rfps, setRfps] = useState<RFP[]>([]);
  const [websites, setWebsites] = useState<Website[]>([]);
  const [activeAgent, setActiveAgent] = useState<AIAgentConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedRfp, setSelectedRfp] = useState<RFP | null>(null);
  const [isModeAModalOpen, setIsModeAModalOpen] = useState(false);
  const [triggeringCrawl, setTriggeringCrawl] = useState(false);

  const { success, error } = useToast();

  const loadData = async () => {
    setLoading(true);
    try {
      const [rfpData, websiteData, agentData] = await Promise.allSettled([
        rfpService.getRFPs(0, 50),
        websiteService.getWebsites(0, 50),
        agentConfigService.getActiveConfig(),
      ]);

      if (rfpData.status === "fulfilled") setRfps(rfpData.value);
      if (websiteData.status === "fulfilled") setWebsites(websiteData.value);
      if (agentData.status === "fulfilled") setActiveAgent(agentData.value);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      loadData();
    }

    const handleRfpCreated = () => {
      if (isAuthenticated) loadData();
    };
    window.addEventListener("rfp-created", handleRfpCreated);
    return () => window.removeEventListener("rfp-created", handleRfpCreated);
  }, [isAuthenticated]);

  useEffect(() => {
    if (!isAuthenticated) return;
    const interval = setInterval(async () => {
      try {
        const status = await websiteService.getCrawlStatus();
        if (triggeringCrawl && !status.is_crawling_any) {
          setTriggeringCrawl(false);
          loadData();
        } else if (status.is_crawling_any) {
          setTriggeringCrawl(true);
        }
      } catch {
        // ignore
      }
    }, 2500);
    return () => clearInterval(interval);
  }, [isAuthenticated, triggeringCrawl]);

  const handleCrawlAll = async () => {
    setTriggeringCrawl(true);
    try {
      const res = await websiteService.triggerCrawlAll();
      success(res.message || "Triggered crawl for all active websites!");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to trigger crawl";
      error(message);
      setTriggeringCrawl(false);
    }
  };

  const activeWebsitesCount = websites.filter(
    (w) => !w.status || w.status === "active"
  ).length;

  const reviewNeededCount = rfps.filter(
    (r) => r.status === "NEEDS_REVIEW" || r.status === "EXTRACTION_FAILED"
  ).length;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
      {/* Top Header Banner */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "16px",
        }}
      >
        <div>
          <h1 className="page-title">
            Procurement Intelligence Dashboard
          </h1>
          <p style={{ fontSize: "0.9rem", color: "var(--text-secondary)", marginTop: "4px" }}>
            Autonomous RFP discovery, LLM-powered extraction, and multi-source web monitoring
          </p>
        </div>

        {/* Top Action Buttons */}
        <div className="header-actions">
          <button
            onClick={() => setIsModeAModalOpen(true)}
            className="btn btn-cyan"
            style={{ padding: "10px 18px" }}
          >
            <Zap size={17} />
            <span>Mode A: Ingest URL</span>
          </button>

          <button
            onClick={handleCrawlAll}
            disabled={triggeringCrawl}
            className={`btn ${triggeringCrawl ? "btn-crawling" : "btn-primary"}`}
            style={{ padding: "10px 18px", display: "inline-flex", alignItems: "center", gap: "8px" }}
          >
            {triggeringCrawl ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                <span className="crawling-pulse-dot" />
                <span>Crawling All Portals...</span>
              </>
            ) : (
              <>
                <Play size={16} />
                <span>Trigger Global Crawl</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid-cards-responsive">
        <StatCard
          title="TOTAL OPPORTUNITIES"
          value={loading ? "..." : rfps.length}
          subtitle="Indexed in system database"
          icon={FileText}
          color="indigo"
        />

        <StatCard
          title="ACTIVE SOURCES"
          value={loading ? "..." : activeWebsitesCount}
          subtitle={`${websites.length} total monitored portals`}
          icon={Globe}
          color="cyan"
        />

        <StatCard
          title="ACTIVE AI ENGINE"
          value={
            activeAgent
              ? activeAgent.model_name
              : "Pure OpenAI"
          }
          subtitle={
            activeAgent
              ? `${activeAgent.provider.toUpperCase()} (T: ${activeAgent.temperature})`
              : "Default extraction agent"
          }
          icon={Bot}
          color="emerald"
        />

        <StatCard
          title="NEEDS REVIEW"
          value={loading ? "..." : reviewNeededCount}
          subtitle="Flagged for manual QA"
          icon={AlertTriangle}
          color={reviewNeededCount > 0 ? "amber" : "emerald"}
        />
      </div>

      {/* Active AI Agent Status Banner */}
      <div
        className="glass-card"
        style={{
          padding: "20px 24px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "16px",
          background:
            "linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(6, 182, 212, 0.08) 100%)",
          border: "1px solid rgba(99, 102, 241, 0.25)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "16px", flexWrap: "wrap" }}>
          <div
            style={{
              width: 48,
              height: 48,
              borderRadius: 12,
              background: "linear-gradient(135deg, #6366f1, #06b6d4)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "0 0 20px rgba(99, 102, 241, 0.4)",
              flexShrink: 0,
            }}
          >
            <Sparkles size={24} color="#ffffff" />
          </div>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
              <h3 style={{ fontSize: "1.05rem", fontWeight: 700, color: "#ffffff" }}>
                AI Extraction Layer: {activeAgent?.name || "Active Production Agent"}
              </h3>
              <span className="badge badge-open">Online</span>
            </div>
            <p style={{ fontSize: "0.825rem", color: "var(--text-light)", marginTop: "3px" }}>
              Operating on provider:{" "}
              <strong style={{ color: "#ffffff" }}>
                {activeAgent?.provider.toUpperCase() || "OPENAI"}
              </strong>{" "}
              • Model:{" "}
              <code
                style={{
                  background: "rgba(0,0,0,0.3)",
                  padding: "2px 6px",
                  borderRadius: 4,
                  color: "var(--accent-cyan)",
                }}
              >
                {activeAgent?.model_name || "gpt-4o"}
              </code>{" "}
              • Temperature: {activeAgent?.temperature ?? 0.0}
            </p>
          </div>
        </div>

        <Link href="/agents" className="btn btn-secondary btn-sm">
          <span>Manage Models</span>
          <ArrowRight size={14} />
        </Link>
      </div>

      {/* Main Content Two-Column Grid */}
      <div className="grid-2col-responsive">
        {/* Left Column: Recent RFPs */}
        <div className="glass-card" style={{ padding: "24px" }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginBottom: "18px",
              flexWrap: "wrap",
              gap: "8px",
            }}
          >
            <div>
              <h2 style={{ fontSize: "1.15rem", fontWeight: 700, color: "#ffffff" }}>
                Recent Procurement Opportunities
              </h2>
              <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "2px" }}>
                Latest discovered tenders with extracted budgets & deadlines
              </p>
            </div>
            <Link
              href="/rfps"
              style={{
                fontSize: "0.825rem",
                color: "var(--accent-cyan)",
                display: "flex",
                alignItems: "center",
                gap: "4px",
                fontWeight: 600,
              }}
            >
              <span>View All ({rfps.length})</span>
              <ArrowRight size={14} />
            </Link>
          </div>

          {rfps.length === 0 ? (
            <div
              style={{
                padding: "48px 24px",
                textAlign: "center",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: "12px",
              }}
            >
              <FileText size={40} color="var(--text-muted)" />
              <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
                No RFPs stored yet. Run Mode A ingestion or trigger a crawl!
              </p>
              <button onClick={() => setIsModeAModalOpen(true)} className="btn btn-cyan btn-sm">
                <Zap size={14} />
                <span>Ingest First RFP</span>
              </button>
            </div>
          ) : (
            <div className="table-container">
              <table className="custom-table" style={{ minWidth: "640px" }}>
                <thead>
                  <tr>
                    <th>RFP / Tender Title</th>
                    <th>Organization</th>
                    <th>Deadline</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {rfps.slice(0, 6).map((rfp) => (
                    <tr
                      key={rfp.id}
                      style={{ cursor: "pointer" }}
                      onClick={() => setSelectedRfp(rfp)}
                    >
                      <td style={{ maxWidth: "280px" }}>
                        <div
                          style={{
                            fontWeight: 600,
                            color: "#f8fafc",
                            whiteSpace: "nowrap",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                          }}
                        >
                          {rfp.title}
                        </div>
                        <div
                          style={{
                            fontSize: "0.75rem",
                            color: "var(--text-muted)",
                            fontFamily: "var(--font-mono)",
                          }}
                        >
                          {rfp.reference_number || `ID #${rfp.id}`}
                        </div>
                      </td>
                      <td style={{ fontSize: "0.85rem", color: "var(--text-light)" }}>
                        {rfp.organization || "Unspecified"}
                      </td>
                      <td style={{ fontSize: "0.85rem" }}>
                        {rfp.submission_deadline ? (
                          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                            <Calendar size={14} color="var(--accent-cyan)" />
                            <span>{rfp.submission_deadline}</span>
                          </div>
                        ) : (
                          <span style={{ color: "var(--text-muted)" }}>Open-ended</span>
                        )}
                      </td>
                      <td>
                        <Badge status={rfp.status || "NEW"} />
                      </td>
                      <td>
                        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                          <a
                            href={rfp.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="btn btn-cyan btn-sm"
                            style={{
                              padding: "4px 8px",
                              fontSize: "0.75rem",
                              display: "inline-flex",
                              alignItems: "center",
                              gap: "4px",
                            }}
                            title="Visit Original RFP Website (New Tab)"
                          >
                            <ExternalLink size={12} />
                            <span>Original RFP Webpage</span>
                          </a>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedRfp(rfp);
                            }}
                            className="btn btn-secondary btn-sm"
                            style={{ padding: "4px 8px", fontSize: "0.75rem" }}
                          >
                            Inspect
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Right Column: Monitored Sources Quick View */}
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          <div className="glass-card" style={{ padding: "24px" }}>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                marginBottom: "16px",
              }}
            >
              <div>
                <h3 style={{ fontSize: "1.05rem", fontWeight: 700, color: "#ffffff" }}>
                  Monitored Sources
                </h3>
                <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "2px" }}>
                  Mode B daily scheduled targets
                </p>
              </div>
              <Link
                href="/websites"
                style={{
                  fontSize: "0.75rem",
                  color: "var(--accent-cyan)",
                  fontWeight: 600,
                }}
              >
                Manage
              </Link>
            </div>

            {websites.length === 0 ? (
              <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                No website sources registered.
              </p>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                {websites.slice(0, 4).map((site) => (
                  <div
                    key={site.id}
                    style={{
                      padding: "12px",
                      borderRadius: "10px",
                      background: "rgba(255, 255, 255, 0.02)",
                      border: "1px solid var(--border-subtle)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 600, fontSize: "0.85rem", color: "#ffffff" }}>
                        {site.name}
                      </div>
                      <div
                        style={{
                          fontSize: "0.725rem",
                          color: "var(--text-muted)",
                          maxWidth: "200px",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {site.start_url}
                      </div>
                    </div>
                    <Badge status={site.status || "active"} />
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Mode Explanation Card */}
          <div
            className="glass-card"
            style={{
              padding: "20px",
              background: "rgba(15, 23, 42, 0.8)",
              border: "1px solid rgba(255, 255, 255, 0.08)",
            }}
          >
            <h4
              style={{
                fontSize: "0.85rem",
                fontWeight: 700,
                color: "#ffffff",
                marginBottom: "8px",
                display: "flex",
                alignItems: "center",
                gap: "6px",
              }}
            >
              <CheckCircle2 size={16} color="var(--accent-emerald)" />
              <span>Platform Ingestion Workflow</span>
            </h4>
            <div style={{ fontSize: "0.775rem", color: "var(--text-light)", lineHeight: 1.6 }}>
              <p style={{ marginBottom: "6px" }}>
                • <strong>Mode A</strong>: Point directly to any tender announcement or PDF. AI agent structures the fields synchronously.
              </p>
              <p>
                • <strong>Mode B</strong>: Automated daily crawl scheduler scans active portals, identifies new notices, and enqueues extractions.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Detail Modal */}
      <RFPDetailModal
        rfp={selectedRfp}
        isOpen={!!selectedRfp}
        onClose={() => setSelectedRfp(null)}
      />

      {/* Mode A Modal */}
      <ModeAImportModal
        isOpen={isModeAModalOpen}
        onClose={() => setIsModeAModalOpen(false)}
        onSuccess={() => loadData()}
      />
    </div>
  );
}
