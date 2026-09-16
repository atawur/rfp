"use client";

import React, { useEffect, useState, useCallback, useRef } from "react";
import { websiteService } from "@/services/websiteService";
import { Website } from "@/types";
import { Badge } from "@/components/ui/Badge";
import { AddWebsiteModal } from "@/components/websites/AddWebsiteModal";
import { EditWebsiteModal } from "@/components/websites/EditWebsiteModal";
import { TestExtractionModal } from "@/components/websites/TestExtractionModal";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import {
  Globe,
  Plus,
  Play,
  Sparkles,
  ExternalLink,
  Clock,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Edit2,
  Users,
  Bell,
} from "lucide-react";

export default function WebsitesPage() {

  const { isAuthenticated } = useAuth();
  const [websites, setWebsites] = useState<Website[]>([]);
  const [loading, setLoading] = useState(true);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [editingWebsite, setEditingWebsite] = useState<Website | null>(null);
  const [isTestModalOpen, setIsTestModalOpen] = useState(false);
  const [testTargetUrl, setTestTargetUrl] = useState("");
  const [crawlingId, setCrawlingId] = useState<number | null>(null);
  const [crawlingAll, setCrawlingAll] = useState(false);
  const [togglingStatusId, setTogglingStatusId] = useState<number | null>(null);
  const [runningWebsiteIds, setRunningWebsiteIds] = useState<number[]>([]);
  const [justFinishedWebsiteIds, setJustFinishedWebsiteIds] = useState<number[]>([]);
  const [justFinishedGlobal, setJustFinishedGlobal] = useState(false);

  const prevRunningRef = useRef<number[]>([]);
  const { success, error } = useToast();

  const fetchWebsites = async () => {
    setLoading(true);
    try {
      const data = await websiteService.getWebsites(0, 100);
      setWebsites(data);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchWebsites();
    }
  }, [isAuthenticated]);

  const checkCrawlStatus = useCallback(async () => {
    try {
      const status = await websiteService.getCrawlStatus();
      const currentRunning = status.running_website_ids || [];
      setRunningWebsiteIds(currentRunning);
      return status;
    } catch {
      return { running_website_ids: [], is_crawling_any: false };
    }
  }, []);

  // Poll active background crawl status periodically
  useEffect(() => {
    if (!isAuthenticated) return;

    // Initial check
    checkCrawlStatus();

    const interval = setInterval(async () => {
      const status = await checkCrawlStatus();
      const currentRunning = status.running_website_ids || [];

      // Detect any websites that were running in the previous check but are now completed
      const newlyFinished = prevRunningRef.current.filter(
        (id) => !currentRunning.includes(id)
      );

      if (newlyFinished.length > 0) {
        setJustFinishedWebsiteIds((prev) =>
          Array.from(new Set([...prev, ...newlyFinished]))
        );
        setTimeout(() => {
          setJustFinishedWebsiteIds((prev) =>
            prev.filter((id) => !newlyFinished.includes(id))
          );
        }, 3000);
        fetchWebsites();
      }

      // Update previous running reference
      prevRunningRef.current = currentRunning;

      // Check if previously tracked single website has completed
      if (crawlingId && !currentRunning.includes(crawlingId)) {
        setCrawlingId(null);
      }

      // Check if global crawl completed (only when all portals have completed)
      if (crawlingAll && !status.is_crawling_any) {
        setCrawlingAll(false);
        setJustFinishedGlobal(true);
        setTimeout(() => setJustFinishedGlobal(false), 3000);
        fetchWebsites();
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [isAuthenticated, crawlingId, crawlingAll, checkCrawlStatus]);

  const handleCrawlSingle = async (website: Website) => {
    setCrawlingId(website.id);
    setRunningWebsiteIds((prev) => Array.from(new Set([...prev, website.id])));
    prevRunningRef.current = Array.from(
      new Set([...prevRunningRef.current, website.id])
    );
    try {
      const res = await websiteService.triggerCrawl(website.id);
      success(res.message || `Crawl initiated for "${website.name}"! Background scraping in progress...`);
      setTimeout(() => checkCrawlStatus(), 800);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Crawl trigger failed";
      error(msg);
      setCrawlingId(null);
      setRunningWebsiteIds((prev) => prev.filter((id) => id !== website.id));
      prevRunningRef.current = prevRunningRef.current.filter((id) => id !== website.id);
    }
  };

  const handleCrawlAll = async () => {
    setCrawlingAll(true);
    const activeIds = websites
      .filter((w) => !w.status || w.status === "active")
      .map((w) => w.id);
    setRunningWebsiteIds((prev) => Array.from(new Set([...prev, ...activeIds])));
    prevRunningRef.current = Array.from(
      new Set([...prevRunningRef.current, ...activeIds])
    );

    try {
      const res = await websiteService.triggerCrawlAll();
      const returnedIds =
        res.website_ids && res.website_ids.length > 0 ? res.website_ids : activeIds;
      setRunningWebsiteIds(returnedIds);
      prevRunningRef.current = returnedIds;
      success(res.message || `Global crawl initiated for ${returnedIds.length} active website(s)!`);
      setTimeout(() => checkCrawlStatus(), 800);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to crawl all sources";
      error(msg);
      setCrawlingAll(false);
      setRunningWebsiteIds([]);
      prevRunningRef.current = [];
    }
  };

  const handleOpenTest = (url: string) => {
    setTestTargetUrl(url);
    setIsTestModalOpen(true);
  };

  const handleQuickToggleStatus = async (website: Website, e: React.MouseEvent) => {
    e.stopPropagation();
    const nextStatus = website.status === "inactive" ? "active" : "inactive";
    setTogglingStatusId(website.id);
    try {
      await websiteService.updateWebsite(website.id, { status: nextStatus });
      setWebsites((prev) =>
        prev.map((w) => (w.id === website.id ? { ...w, status: nextStatus } : w))
      );
      success(`Status for "${website.name}" updated to ${nextStatus}!`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to update status";
      error(msg);
    } finally {
      setTogglingStatusId(null);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
      {/* Header */}
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
            Monitored RFP Sources (Mode B)
          </h1>
          <p style={{ fontSize: "0.9rem", color: "var(--text-secondary)", marginTop: "4px" }}>
            Configure recurring procurement portals for autonomous scheduled scraping and opportunity discovery
          </p>
        </div>

        <div className="header-actions">
          <button
            onClick={() => handleOpenTest("")}
            className="btn btn-secondary"
          >
            <Sparkles size={16} color="var(--accent-cyan)" />
            <span>Test Extraction</span>
          </button>

          {/* Trigger Global Crawl Button with Animated Crawling Feedback */}
          {(() => {
            const isGlobalCrawling = crawlingAll || runningWebsiteIds.length > 0;
            return (
              <button
                onClick={handleCrawlAll}
                disabled={isGlobalCrawling}
                className={`btn ${
                  isGlobalCrawling
                    ? "btn-crawling"
                    : justFinishedGlobal
                    ? "btn-crawl-success"
                    : "btn-primary"
                }`}
                style={{
                  padding: "10px 20px",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "8px",
                  fontWeight: 600,
                }}
                title={
                  isGlobalCrawling
                    ? "Autonomous crawl actively extracting data across portals..."
                    : "Trigger crawler across all registered active procurement portals"
                }
              >
                {isGlobalCrawling ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    <span className="crawling-pulse-dot" />
                    <span>Crawling All Portals...</span>
                  </>
                ) : justFinishedGlobal ? (
                  <>
                    <CheckCircle2 size={16} />
                    <span>Global Crawl Completed!</span>
                  </>
                ) : (
                  <>
                    <Play size={16} />
                    <span>Trigger Global Crawl</span>
                  </>
                )}
              </button>
            );
          })()}

          <button
            onClick={() => setIsAddModalOpen(true)}
            className="btn btn-cyan"
          >
            <Plus size={16} />
            <span>Add RFP Source</span>
          </button>
        </div>
      </div>

      {/* Overview stats pill */}
      <div
        className="glass-card"
        style={{
          padding: "18px 24px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "16px",
          background: "rgba(15, 23, 42, 0.6)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "20px", flexWrap: "wrap" }}>
          <div>
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>TOTAL SOURCES</span>
            <div style={{ fontSize: "1.25rem", fontWeight: 700, color: "#ffffff" }}>
              {websites.length}
            </div>
          </div>
          <div className="hide-on-mobile" style={{ width: "1px", height: "30px", background: "var(--border-subtle)" }} />
          <div>
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>ACTIVE MONITORS</span>
            <div style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--accent-emerald)" }}>
              {websites.filter((w) => !w.status || w.status === "active").length}
            </div>
          </div>
          <div className="hide-on-mobile" style={{ width: "1px", height: "30px", background: "var(--border-subtle)" }} />
          <div>
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>SCHEDULE FREQUENCY</span>
            <div style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--accent-cyan)" }}>
              Daily (APScheduler)
            </div>
          </div>
        </div>

        <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", display: "flex", alignItems: "center", gap: "6px" }}>
          <CheckCircle2 size={16} color="var(--accent-emerald)" />
          <span>Crawler worker automatically manages deduplication & change detection</span>
        </div>
      </div>

      {/* Website Sources Table */}
      {loading ? (
        <div style={{ padding: "64px", textAlign: "center", color: "var(--text-muted)" }}>
          Loading Monitored Websites...
        </div>
      ) : websites.length === 0 ? (
        <div
          className="glass-card"
          style={{
            padding: "60px 24px",
            textAlign: "center",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "14px",
          }}
        >
          <Globe size={48} color="var(--text-muted)" />
          <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#ffffff" }}>
            No Sources Configured Yet
          </h3>
          <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)", maxWidth: "450px" }}>
            Register your first RFP portal or agency website to enable automated scheduled crawling.
          </p>
          <button onClick={() => setIsAddModalOpen(true)} className="btn btn-cyan btn-sm">
            <Plus size={14} />
            <span>Register First Source</span>
          </button>
        </div>
      ) : (
        <div className="glass-card table-container" style={{ padding: "16px" }}>
          <table className="custom-table" style={{ minWidth: "680px" }}>
            <thead>
              <tr>
                <th>Source Name</th>
                <th>Listing Target URL</th>
                <th>Frequency</th>
                <th>Alert Recipients</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {websites.map((site) => (
                <tr key={site.id}>
                  <td>
                    <div style={{ fontWeight: 600, color: "#ffffff", display: "flex", alignItems: "center", gap: "8px" }}>
                      <Globe size={16} color="var(--accent-cyan)" />
                      <span>{site.name}</span>
                    </div>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "2px" }}>
                      Base: {site.base_url}
                    </div>
                  </td>
                  <td style={{ maxWidth: "340px" }}>
                    <div
                      style={{
                        fontSize: "0.85rem",
                        color: "var(--text-light)",
                        whiteSpace: "nowrap",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                      }}
                    >
                      {site.start_url}
                    </div>
                    <a
                      href={site.start_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{
                        fontSize: "0.75rem",
                        color: "var(--accent-cyan)",
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "4px",
                        marginTop: "2px",
                      }}
                    >
                      <span>Visit Site</span>
                      <ExternalLink size={11} />
                    </a>
                  </td>
                  <td>
                    <span
                      style={{
                        fontSize: "0.775rem",
                        background: "rgba(255, 255, 255, 0.05)",
                        padding: "4px 8px",
                        borderRadius: "6px",
                        border: "1px solid var(--border-subtle)",
                        textTransform: "capitalize",
                      }}
                    >
                      {site.crawl_frequency || "Daily"}
                    </span>
                  </td>
                  <td>
                    {site.notify_all_receivers ?? true ? (
                      <span
                        className="badge"
                        style={{
                          background: "rgba(6, 182, 212, 0.1)",
                          color: "var(--accent-cyan)",
                          border: "1px solid rgba(6, 182, 212, 0.25)",
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "5px",
                          fontSize: "0.75rem",
                        }}
                        title="All active notification receivers will receive automated alerts for this source"
                      >
                        <Users size={12} /> All Receivers
                      </span>
                    ) : (site.notification_receivers?.length || 0) > 0 ? (
                      <span
                        className="badge"
                        style={{
                          background: "rgba(99, 102, 241, 0.1)",
                          color: "#a5b4fc",
                          border: "1px solid rgba(99, 102, 241, 0.25)",
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "5px",
                          fontSize: "0.75rem",
                        }}
                        title={`Recipients: ${(site.notification_receivers || []).map((r) => r.name).join(", ")}`}
                      >
                        <Bell size={12} /> {site.notification_receivers?.length} Recipient(s)
                      </span>
                    ) : (
                      <span
                        className="badge"
                        style={{
                          background: "rgba(239, 68, 68, 0.1)",
                          color: "#fca5a5",
                          border: "1px solid rgba(239, 68, 68, 0.25)",
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "5px",
                          fontSize: "0.75rem",
                        }}
                      >
                        None Selected
                      </span>
                    )}
                  </td>

                  <td>
                    <button
                      type="button"
                      onClick={(e) => handleQuickToggleStatus(site, e)}
                      disabled={togglingStatusId === site.id}
                      title={`Click to switch status to ${site.status === "inactive" ? "active" : "inactive"}`}
                      style={{
                        background: "transparent",
                        border: "none",
                        padding: 0,
                        cursor: "pointer",
                        display: "inline-flex",
                        alignItems: "center",
                      }}
                    >
                      {togglingStatusId === site.id ? (
                        <span
                          className="badge badge-needs-review"
                          style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}
                        >
                          <Loader2 size={12} className="animate-spin" /> Updating...
                        </span>
                      ) : (
                        <Badge status={site.status || "active"} />
                      )}
                    </button>
                  </td>
                  <td>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      {/* Run Crawl Button with Animated Crawling Feedback */}
                      {(() => {
                        const isSiteCrawling =
                          crawlingId === site.id ||
                          runningWebsiteIds.includes(site.id) ||
                          (crawlingAll && (!site.status || site.status === "active"));
                        const isJustFinished = justFinishedWebsiteIds.includes(site.id);

                        return (
                          <button
                            onClick={() => handleCrawlSingle(site)}
                            disabled={isSiteCrawling}
                            className={`btn btn-sm ${
                              isSiteCrawling
                                ? "btn-crawling-sm"
                                : isJustFinished
                                ? "btn-crawl-success"
                                : "btn-primary"
                            }`}
                            style={{
                              padding: "6px 14px",
                              fontSize: "0.775rem",
                              display: "inline-flex",
                              alignItems: "center",
                              gap: "6px",
                              fontWeight: 600,
                            }}
                            title={
                              isSiteCrawling
                                ? "Extraction worker actively crawling this site in background..."
                                : "Execute crawler and extraction pipeline for this portal"
                            }
                          >
                            {isSiteCrawling ? (
                              <>
                                <Loader2 size={13} className="animate-spin" />
                                <span className="crawling-pulse-dot" />
                                <span>Crawling...</span>
                              </>
                            ) : isJustFinished ? (
                              <>
                                <CheckCircle2 size={13} />
                                <span>Done!</span>
                              </>
                            ) : (
                              <>
                                <Play size={13} />
                                <span>Run Crawl</span>
                              </>
                            )}
                          </button>
                        );
                      })()}

                      <button
                        onClick={() => handleOpenTest(site.start_url)}
                        className="btn btn-secondary btn-sm"
                        style={{ padding: "6px 10px", fontSize: "0.775rem" }}
                        title="Test Extraction synchronously"
                      >
                        <Sparkles size={13} color="var(--accent-cyan)" />
                        <span>Test</span>
                      </button>

                      <button
                        onClick={() => setEditingWebsite(site)}
                        className="btn btn-secondary btn-sm"
                        style={{ padding: "6px 10px", fontSize: "0.775rem", gap: "5px" }}
                        title="Edit Website Source"
                      >
                        <Edit2 size={13} />
                        <span>Edit</span>
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Add Website Modal */}
      <AddWebsiteModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onCreated={() => fetchWebsites()}
      />

      {/* Edit Website Modal */}
      <EditWebsiteModal
        isOpen={Boolean(editingWebsite)}
        website={editingWebsite}
        onClose={() => setEditingWebsite(null)}
        onUpdated={() => fetchWebsites()}
      />

      {/* Test Extraction Modal */}
      <TestExtractionModal
        isOpen={isTestModalOpen}
        onClose={() => setIsTestModalOpen(false)}
        defaultUrl={testTargetUrl}
      />
    </div>
  );
}
