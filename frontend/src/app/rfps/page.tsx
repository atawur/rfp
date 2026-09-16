"use client";

import React, { useEffect, useState, useCallback } from "react";
import { rfpService } from "@/services/rfpService";
import { websiteService } from "@/services/websiteService";
import { RFP, Website } from "@/types";
import { Badge } from "@/components/ui/Badge";
import { CategoryBadge } from "@/components/rfp/CategoryBadge";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import { RFPDetailModal } from "@/components/rfp/RFPDetailModal";
import { ModeAImportModal } from "@/components/rfp/ModeAImportModal";
import { RFPCreateModal } from "@/components/rfp/RFPCreateModal";
import {
  Search,
  Zap,
  Plus,
  Calendar,
  Building,
  DollarSign,
  ExternalLink,
  Filter,
  Layers,
  Table as TableIcon,
  LayoutGrid,
  FileText,
  Sparkles,
  Loader2,
  Tag,
  RotateCcw,
  Clock,
  Globe,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
} from "lucide-react";

import Link from "next/link";

export default function RFPsPage() {
  const { isAuthenticated } = useAuth();
  const { success, error } = useToast();
  const [rfps, setRfps] = useState<RFP[]>([]);
  const [websites, setWebsites] = useState<Website[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedSearchQuery, setDebouncedSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [categoryFilter, setCategoryFilter] = useState("ALL");
  const [websiteFilter, setWebsiteFilter] = useState<string>("ALL");
  const [viewMode, setViewMode] = useState<"table" | "grid">("table");
  const [classifyingRfpId, setClassifyingRfpId] = useState<number | null>(null);
  const [reprocessing, setReprocessing] = useState(false);

  // Pagination states
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(20);
  const [total, setTotal] = useState<number>(0);
  const [totalPages, setTotalPages] = useState<number>(1);

  const [selectedRfp, setSelectedRfp] = useState<RFP | null>(null);
  const [isModeAModalOpen, setIsModeAModalOpen] = useState(false);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  // Fetch websites for filter dropdown
  useEffect(() => {
    if (isAuthenticated) {
      websiteService
        .getWebsites(0, 100)
        .then((data) => setWebsites(data))
        .catch(() => {});
    }
  }, [isAuthenticated]);

  // Debounce search query to prevent flooding server requests
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchQuery(searchQuery);
      setPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const fetchRFPs = useCallback(async () => {
    setLoading(true);
    try {
      const data = await rfpService.getPaginatedRFPs({
        page,
        size: pageSize,
        website_id: websiteFilter !== "ALL" ? Number(websiteFilter) : undefined,
        category: categoryFilter !== "ALL" ? categoryFilter : undefined,
        status: statusFilter !== "ALL" ? statusFilter : undefined,
        search: debouncedSearchQuery,
      });
      setRfps(data.items);
      setTotal(data.total);
      setTotalPages(data.pages);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, websiteFilter, categoryFilter, statusFilter, debouncedSearchQuery]);

  useEffect(() => {
    if (isAuthenticated) {
      fetchRFPs();
    }
  }, [isAuthenticated, fetchRFPs]);

  const handleClassifySingle = async (rfpId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    setClassifyingRfpId(rfpId);
    try {
      const updated = await rfpService.classifyRFP(rfpId, true);
      setRfps((prev) => prev.map((r) => (r.id === rfpId ? updated : r)));
      if (selectedRfp?.id === rfpId) {
        setSelectedRfp(updated);
      }
      success(`RFP #${rfpId} classified as "${updated.primary_category}" (${updated.sub_category || "general"})!`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Classification failed";
      error(msg);
    } finally {
      setClassifyingRfpId(null);
    }
  };

  const handleReprocessAll = async () => {
    setReprocessing(true);
    try {
      const res = await rfpService.reprocessClassification(50);
      success(`AI Classification completed: ${res.succeeded} classified, ${res.failed} failed out of ${res.processed} opportunities.`);
      await fetchRFPs();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Reprocessing failed";
      error(msg);
    } finally {
      setReprocessing(false);
    }
  };

  const CATEGORIES = [
    { value: "ALL", label: "All Categories" },
    { value: "software", label: "Software" },
    { value: "hardware", label: "Hardware" },
    { value: "it_services", label: "IT Services" },
    { value: "cybersecurity", label: "Cybersecurity" },
    { value: "cloud", label: "Cloud" },
    { value: "telecommunications", label: "Telecommunications" },
    { value: "professional_services", label: "Professional Services" },
    { value: "healthcare", label: "Healthcare" },
    { value: "construction", label: "Construction" },
    { value: "security", label: "Security" },
    { value: "transportation", label: "Transportation" },
    { value: "office_supplies", label: "Office Supplies" },
    { value: "education", label: "Education" },
    { value: "other", label: "Other" },
    { value: "UNCLASSIFIED", label: "Unclassified / Pending" },
  ];

  const hasActiveFilters =
    categoryFilter !== "ALL" ||
    statusFilter !== "ALL" ||
    websiteFilter !== "ALL" ||
    searchQuery.trim() !== "";

  const handleResetFilters = () => {
    setSearchQuery("");
    setDebouncedSearchQuery("");
    setCategoryFilter("ALL");
    setStatusFilter("ALL");
    setWebsiteFilter("ALL");
    setPage(1);
  };

  const getPageNumbers = (current: number, total: number) => {
    if (total <= 7) {
      return Array.from({ length: total }, (_, i) => i + 1);
    }
    if (current <= 4) {
      return [1, 2, 3, 4, 5, "...", total];
    }
    if (current >= total - 3) {
      return [1, "...", total - 4, total - 3, total - 2, total - 1, total];
    }
    return [1, "...", current - 1, current, current + 1, "...", total];
  };

  const statuses = ["ALL", "NEW", "OPEN", "NEEDS_REVIEW", "UPDATED", "CLOSED"];

  const formatCrawledDate = (dateStr?: string | null) => {
    if (!dateStr) return { date: "—", time: "" };
    try {
      const d = new Date(dateStr);
      if (isNaN(d.getTime())) return { date: dateStr, time: "" };
      return {
        date: d.toLocaleDateString(undefined, {
          year: "numeric",
          month: "short",
          day: "numeric",
        }),
        time: d.toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
      };
    } catch {
      return { date: dateStr, time: "" };
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* Page Header */}
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
            RFP Intelligence Explorer
          </h1>
          <p style={{ fontSize: "0.9rem", color: "var(--text-secondary)", marginTop: "4px" }}>
            Search, filter, and inspect structured tender opportunities extracted across all sources
          </p>
        </div>

        <div className="header-actions">
          <button
            onClick={handleReprocessAll}
            disabled={reprocessing}
            className="btn btn-secondary"
            title="Automatically run AI classification on all pending or unclassified RFPs"
          >
            {reprocessing ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <Sparkles size={16} color="var(--accent-cyan)" />
            )}
            <span>Classify Pending RFPs</span>
          </button>
          <button onClick={() => setIsModeAModalOpen(true)} className="btn btn-cyan">
            <Zap size={16} />
            <span>Mode A: Ingest URL</span>
          </button>
          <button onClick={() => setIsCreateModalOpen(true)} className="btn btn-primary">
            <Plus size={16} />
            <span>Manual Create</span>
          </button>
        </div>
      </div>

      {/* Filter and Search Controls Bar */}
      <div
        className="glass-card"
        style={{
          padding: "16px 20px",
          display: "flex",
          flexDirection: "column",
          gap: "14px",
        }}
      >
        {/* Tier 1: Search, Category Dropdown, and View Mode Toggle */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "12px",
          }}
        >
          {/* Search input */}
          <div style={{ position: "relative", flex: "1 1 280px", minWidth: "220px" }}>
            <Search
              size={18}
              style={{
                position: "absolute",
                left: 14,
                top: "50%",
                transform: "translateY(-50%)",
                color: "var(--text-muted)",
              }}
            />
            <input
              type="text"
              placeholder="Search title, category, subcategory, organization..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="form-control"
              style={{ paddingLeft: "42px", paddingRight: loading ? "40px" : "14px" }}
            />
            {loading && (
              <Loader2
                size={16}
                className="animate-spin"
                style={{
                  position: "absolute",
                  right: 14,
                  top: "50%",
                  transform: "translateY(-50%)",
                  color: "var(--accent-cyan)",
                }}
              />
            )}
          </div>

          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              flexWrap: "wrap",
            }}
          >
            {/* Website Filter Dropdown */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                background: "rgba(255, 255, 255, 0.05)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "8px",
                padding: "2px 10px",
              }}
            >
              <Globe size={14} color="var(--accent-cyan)" />
              <select
                value={websiteFilter}
                onChange={(e) => {
                  setWebsiteFilter(e.target.value);
                  setPage(1);
                }}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "#f8fafc",
                  fontSize: "0.8rem",
                  fontWeight: 600,
                  outline: "none",
                  cursor: "pointer",
                  padding: "6px 0",
                  maxWidth: "180px",
                }}
              >
                <option value="ALL" style={{ background: "#0f172a", color: "#ffffff" }}>
                  All Websites ({websites.length})
                </option>
                {websites.map((w) => (
                  <option key={w.id} value={w.id} style={{ background: "#0f172a", color: "#ffffff" }}>
                    {w.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Category Filter Dropdown */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                background: "rgba(255, 255, 255, 0.05)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "8px",
                padding: "2px 10px",
              }}
            >
              <Tag size={14} color="var(--accent-cyan)" />
              <select
                value={categoryFilter}
                onChange={(e) => {
                  setCategoryFilter(e.target.value);
                  setPage(1);
                }}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "#f8fafc",
                  fontSize: "0.8rem",
                  fontWeight: 600,
                  outline: "none",
                  cursor: "pointer",
                  padding: "6px 0",
                  maxWidth: "180px",
                }}
              >
                {CATEGORIES.map((cat) => (
                  <option key={cat.value} value={cat.value} style={{ background: "#0f172a", color: "#ffffff" }}>
                    {cat.label}
                  </option>
                ))}
              </select>
            </div>

            {/* View mode toggle */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                background: "rgba(255, 255, 255, 0.05)",
                padding: "3px",
                borderRadius: "8px",
                border: "1px solid var(--border-subtle)",
              }}
            >
              <button
                onClick={() => setViewMode("table")}
                style={{
                  padding: "6px 10px",
                  borderRadius: "6px",
                  display: "flex",
                  alignItems: "center",
                  gap: "4px",
                  fontSize: "0.75rem",
                  fontWeight: 600,
                  backgroundColor: viewMode === "table" ? "rgba(255, 255, 255, 0.12)" : "transparent",
                  color: viewMode === "table" ? "#ffffff" : "var(--text-muted)",
                }}
              >
                <TableIcon size={14} />
                <span>Table</span>
              </button>
              <button
                onClick={() => setViewMode("grid")}
                style={{
                  padding: "6px 10px",
                  borderRadius: "6px",
                  display: "flex",
                  alignItems: "center",
                  gap: "4px",
                  fontSize: "0.75rem",
                  fontWeight: 600,
                  backgroundColor: viewMode === "grid" ? "rgba(255, 255, 255, 0.12)" : "transparent",
                  color: viewMode === "grid" ? "#ffffff" : "var(--text-muted)",
                }}
              >
                <LayoutGrid size={14} />
                <span>Grid</span>
              </button>
            </div>
          </div>
        </div>

        {/* Tier 2: Status Filter Pills and Reset Button */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "10px",
            borderTop: "1px solid rgba(255, 255, 255, 0.05)",
            paddingTop: "12px",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              minWidth: 0,
              flex: "1 1 auto",
              overflow: "hidden",
            }}
          >
            <span
              style={{
                fontSize: "0.7rem",
                fontWeight: 700,
                textTransform: "uppercase",
                letterSpacing: "0.06em",
                color: "var(--text-muted)",
                whiteSpace: "nowrap",
                flexShrink: 0,
              }}
            >
              Status:
            </span>
            <div className="status-pills-container" style={{ padding: "2px 0" }}>
              {statuses.map((status) => {
                const isSelected = statusFilter === status;
                return (
                  <button
                    key={status}
                    onClick={() => {
                      setStatusFilter(status);
                      setPage(1);
                    }}
                    style={{
                      padding: "5px 12px",
                      borderRadius: "9999px",
                      fontSize: "0.72rem",
                      fontWeight: 600,
                      whiteSpace: "nowrap",
                      flexShrink: 0,
                      transition: "all 0.15s ease",
                      backgroundColor: isSelected ? "var(--accent-primary)" : "rgba(255, 255, 255, 0.05)",
                      color: isSelected ? "#ffffff" : "var(--text-secondary)",
                      border: isSelected ? "1px solid var(--accent-primary)" : "1px solid var(--border-subtle)",
                    }}
                  >
                    {status}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Reset Filter Button if active */}
          {hasActiveFilters && (
            <button
              onClick={handleResetFilters}
              className="btn btn-secondary btn-sm"
              style={{
                fontSize: "0.72rem",
                padding: "5px 10px",
                display: "flex",
                alignItems: "center",
                gap: "5px",
                flexShrink: 0,
              }}
              title="Reset all search and category filters"
            >
              <RotateCcw size={12} />
              <span>Reset</span>
            </button>
          )}
        </div>
      </div>

      {/* RFPs Render View */}
      {loading && rfps.length === 0 ? (
        <div
          style={{
            padding: "64px",
            textAlign: "center",
            color: "var(--text-muted)",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "12px",
          }}
        >
          <Loader2 size={24} className="animate-spin" color="var(--accent-cyan)" />
          <span>Searching & loading opportunities from database...</span>
        </div>
      ) : rfps.length === 0 ? (
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
          <FileText size={48} color="var(--text-muted)" />
          <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#ffffff" }}>
            No Matching RFPs Found
          </h3>
          <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)", maxWidth: "450px" }}>
            No opportunities matched your search criteria. Try modifying your search or reset filters.
          </p>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            {hasActiveFilters && (
              <button onClick={handleResetFilters} className="btn btn-secondary btn-sm">
                <RotateCcw size={14} />
                <span>Reset Filters</span>
              </button>
            )}
            <button onClick={() => setIsModeAModalOpen(true)} className="btn btn-cyan btn-sm">
              <Zap size={14} />
              <span>Ingest RFP from URL</span>
            </button>
          </div>
        </div>
      ) : viewMode === "table" ? (
        <div
          className="glass-card table-container"
          style={{
            padding: "16px",
            opacity: loading ? 0.6 : 1,
            transition: "opacity 0.2s ease",
          }}
        >
          <table className="custom-table" style={{ minWidth: "920px" }}>
            <thead>
              <tr>
                <th>RFP Title & Reference</th>
                <th>Category & Scope</th>
                <th>Source Portal</th>
                <th>Organization</th>
                <th>Budget</th>
                <th>Deadline</th>
                <th>Date Crawled</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {rfps.map((rfp) => {
                const crawled = formatCrawledDate(rfp.first_seen_at || rfp.created_at);
                return (
                  <tr
                    key={rfp.id}
                    style={{ cursor: "pointer" }}
                    onClick={() => setSelectedRfp(rfp)}
                  >
                    <td style={{ maxWidth: "300px" }}>
                      <div style={{ fontWeight: 600, color: "#ffffff", marginBottom: "3px" }}>
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
                    <td style={{ minWidth: "160px" }}>
                      <CategoryBadge
                        category={rfp.primary_category}
                        subCategory={rfp.sub_category}
                        procurementType={rfp.procurement_type}
                        confidence={rfp.confidence}
                        status={rfp.classification_status}
                        isClassifying={classifyingRfpId === rfp.id}
                        onClassify={(e) => handleClassifySingle(rfp.id, e)}
                      />
                    </td>
                    <td>
                      <div
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "5px",
                          padding: "3px 8px",
                          borderRadius: "6px",
                          background: "rgba(34, 211, 238, 0.08)",
                          border: "1px solid rgba(34, 211, 238, 0.2)",
                          fontSize: "0.75rem",
                          color: "var(--accent-cyan)",
                          fontWeight: 600,
                          maxWidth: "150px",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                        }}
                        title={rfp.website_name || "Direct Source"}
                      >
                        <Globe size={12} style={{ flexShrink: 0 }} />
                        <span style={{ overflow: "hidden", textOverflow: "ellipsis" }}>
                          {rfp.website_name || "Direct Source"}
                        </span>
                      </div>
                    </td>
                    <td>
                      <div style={{ fontSize: "0.85rem", color: "var(--text-light)" }}>
                        {rfp.organization || "Unspecified"}
                      </div>
                      {rfp.location && (
                        <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                          {rfp.location}
                        </div>
                      )}
                    </td>
                    <td>
                      <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--accent-emerald)" }}>
                        {rfp.estimated_budget
                          ? `${rfp.currency || "USD"} ${rfp.estimated_budget.toLocaleString()}`
                          : "—"}
                      </span>
                    </td>
                    <td>
                      {rfp.submission_deadline ? (
                        <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.85rem", color: "#f8fafc" }}>
                          <Calendar size={14} color="var(--accent-cyan)" />
                          <span>{rfp.submission_deadline}</span>
                        </div>
                      ) : (
                        <span style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>Open-ended</span>
                      )}
                    </td>
                    <td>
                      {crawled.time ? (
                        <div>
                          <div
                            style={{
                              display: "flex",
                              alignItems: "center",
                              gap: "6px",
                              fontSize: "0.825rem",
                              color: "#f8fafc",
                            }}
                          >
                            <Clock size={13} color="var(--accent-cyan)" />
                            <span>{crawled.date}</span>
                          </div>
                          <div
                            style={{
                              fontSize: "0.72rem",
                              color: "var(--text-muted)",
                              paddingLeft: "19px",
                            }}
                          >
                            {crawled.time}
                          </div>
                        </div>
                      ) : (
                        <span style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>—</span>
                      )}
                    </td>
                    <td>
                      <Badge status={rfp.status || "NEW"} />
                    </td>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedRfp(rfp);
                          }}
                          className="btn btn-secondary btn-sm"
                          style={{ fontSize: "0.72rem", padding: "4px 8px" }}
                        >
                          Preview
                        </button>
                        <Link
                          href={`/rfps/${rfp.id}`}
                          onClick={(e) => e.stopPropagation()}
                          className="btn btn-cyan btn-sm"
                          style={{
                            fontSize: "0.72rem",
                            padding: "4px 8px",
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "4px",
                          }}
                          title="Full Details"
                        >
                          <FileText size={12} />
                          <span>Details</span>
                        </Link>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        /* Grid View */
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(min(100%, 300px), 1fr))",
            gap: "20px",
            opacity: loading ? 0.6 : 1,
            transition: "opacity 0.2s ease",
          }}
        >
          {rfps.map((rfp) => (
            <div
              key={rfp.id}
              className="glass-card"
              style={{
                padding: "20px",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
                minHeight: "220px",
                cursor: "pointer",
              }}
              onClick={() => setSelectedRfp(rfp)}
            >
              <div>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    marginBottom: "12px",
                    gap: "8px",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
                    <Badge status={rfp.status || "NEW"} />
                    {rfp.website_name && (
                      <span
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "4px",
                          fontSize: "0.72rem",
                          padding: "2px 8px",
                          borderRadius: "6px",
                          background: "rgba(34, 211, 238, 0.08)",
                          border: "1px solid rgba(34, 211, 238, 0.2)",
                          color: "var(--accent-cyan)",
                          fontWeight: 600,
                        }}
                      >
                        <Globe size={11} />
                        {rfp.website_name}
                      </span>
                    )}
                    <CategoryBadge
                      category={rfp.primary_category}
                      subCategory={rfp.sub_category}
                      procurementType={rfp.procurement_type}
                      confidence={rfp.confidence}
                      status={rfp.classification_status}
                      isClassifying={classifyingRfpId === rfp.id}
                      onClassify={(e) => handleClassifySingle(rfp.id, e)}
                      size="sm"
                    />
                  </div>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                    #{rfp.id}
                  </span>
                </div>

                <h3
                  style={{
                    fontSize: "1rem",
                    fontWeight: 700,
                    color: "#ffffff",
                    lineHeight: 1.4,
                    marginBottom: "10px",
                    display: "-webkit-box",
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: "vertical",
                    overflow: "hidden",
                  }}
                >
                  {rfp.title}
                </h3>

                <div style={{ display: "flex", flexDirection: "column", gap: "6px", fontSize: "0.8rem", color: "var(--text-light)" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                    <Building size={14} color="var(--text-muted)" />
                    <span>{rfp.organization || "Organization Unspecified"}</span>
                  </div>

                  {rfp.submission_deadline && (
                    <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                      <Calendar size={14} color="var(--accent-cyan)" />
                      <span>Due: {rfp.submission_deadline}</span>
                    </div>
                  )}

                  {rfp.estimated_budget && (
                    <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                      <DollarSign size={14} color="var(--accent-emerald)" />
                      <span style={{ color: "var(--accent-emerald)", fontWeight: 600 }}>
                        {rfp.currency || "USD"} {rfp.estimated_budget.toLocaleString()}
                      </span>
                    </div>
                  )}

                  {(rfp.first_seen_at || rfp.created_at) && (
                    <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                      <Clock size={13} color="var(--accent-cyan)" />
                      <span style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
                        Crawled: {formatCrawledDate(rfp.first_seen_at || rfp.created_at).date}
                      </span>
                    </div>
                  )}
                </div>
              </div>

              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  marginTop: "16px",
                  paddingTop: "12px",
                  borderTop: "1px solid var(--border-subtle)",
                  flexWrap: "wrap",
                  gap: "8px",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "6px", flexWrap: "wrap" }}>
                  <a
                    href={rfp.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={(e) => e.stopPropagation()}
                    className="btn btn-cyan btn-sm"
                    style={{
                      fontSize: "0.72rem",
                      padding: "4px 8px",
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "4px",
                      fontWeight: 600,
                      whiteSpace: "nowrap",
                    }}
                    title="Visit Original RFP Website (Opens in new tab)"
                  >
                    <ExternalLink size={12} />
                    <span>Source</span>
                  </a>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedRfp(rfp);
                    }}
                    className="btn btn-secondary btn-sm"
                    style={{ fontSize: "0.72rem", padding: "4px 8px", whiteSpace: "nowrap" }}
                  >
                    Preview
                  </button>
                </div>
                <Link
                  href={`/rfps/${rfp.id}`}
                  onClick={(e) => e.stopPropagation()}
                  className="btn btn-secondary btn-sm"
                  style={{
                    fontSize: "0.72rem",
                    padding: "4px 8px",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "4px",
                    fontWeight: 600,
                    whiteSpace: "nowrap",
                    color: "var(--accent-cyan)",
                  }}
                  title="View full tender opportunity details"
                >
                  <span>Details</span>
                  <FileText size={12} />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination Controls Bar */}
      {total > 0 && (
        <div
          className="glass-card"
          style={{
            padding: "14px 20px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "14px",
            marginTop: "4px",
          }}
        >
          {/* Summary / Range */}
          <div style={{ fontSize: "0.825rem", color: "var(--text-secondary)" }}>
            Showing{" "}
            <span style={{ fontWeight: 600, color: "#ffffff" }}>
              {Math.min((page - 1) * pageSize + 1, total)}
            </span>{" "}
            to{" "}
            <span style={{ fontWeight: 600, color: "#ffffff" }}>
              {Math.min(page * pageSize, total)}
            </span>{" "}
            of{" "}
            <span style={{ fontWeight: 600, color: "var(--accent-cyan)" }}>
              {total}
            </span>{" "}
            opportunities
          </div>

          {/* Page Size & Page Navigation */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "14px",
              flexWrap: "wrap",
            }}
          >
            {/* Page Size Picker */}
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
                Per page:
              </span>
              <select
                value={pageSize}
                onChange={(e) => {
                  setPageSize(Number(e.target.value));
                  setPage(1);
                }}
                style={{
                  background: "rgba(255, 255, 255, 0.06)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "6px",
                  color: "#ffffff",
                  fontSize: "0.78rem",
                  fontWeight: 600,
                  padding: "4px 8px",
                  outline: "none",
                  cursor: "pointer",
                }}
              >
                {[10, 20, 50, 100].map((sz) => (
                  <option key={sz} value={sz} style={{ background: "#0f172a", color: "#ffffff" }}>
                    {sz}
                  </option>
                ))}
              </select>
            </div>

            {/* Navigation Buttons */}
            <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
              <button
                onClick={() => setPage(1)}
                disabled={page <= 1 || loading}
                className="btn btn-secondary btn-sm"
                style={{ padding: "5px 8px", opacity: page <= 1 ? 0.4 : 1 }}
                title="First Page"
              >
                <ChevronsLeft size={14} />
              </button>
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1 || loading}
                className="btn btn-secondary btn-sm"
                style={{ padding: "5px 8px", opacity: page <= 1 ? 0.4 : 1 }}
                title="Previous Page"
              >
                <ChevronLeft size={14} />
              </button>

              {getPageNumbers(page, totalPages).map((p, idx) => {
                if (p === "...") {
                  return (
                    <span
                      key={`ellipsis-${idx}`}
                      style={{
                        padding: "0 6px",
                        color: "var(--text-muted)",
                        fontSize: "0.8rem",
                      }}
                    >
                      ...
                    </span>
                  );
                }
                const isCurrent = p === page;
                return (
                  <button
                    key={`page-${p}`}
                    onClick={() => setPage(Number(p))}
                    disabled={loading}
                    style={{
                      minWidth: "30px",
                      height: "30px",
                      padding: "0 8px",
                      borderRadius: "6px",
                      fontSize: "0.78rem",
                      fontWeight: 600,
                      backgroundColor: isCurrent ? "var(--accent-primary)" : "rgba(255, 255, 255, 0.05)",
                      color: isCurrent ? "#ffffff" : "var(--text-secondary)",
                      border: isCurrent ? "1px solid var(--accent-primary)" : "1px solid var(--border-subtle)",
                      cursor: "pointer",
                      transition: "all 0.15s ease",
                    }}
                  >
                    {p}
                  </button>
                );
              })}

              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages || loading}
                className="btn btn-secondary btn-sm"
                style={{ padding: "5px 8px", opacity: page >= totalPages ? 0.4 : 1 }}
                title="Next Page"
              >
                <ChevronRight size={14} />
              </button>
              <button
                onClick={() => setPage(totalPages)}
                disabled={page >= totalPages || loading}
                className="btn btn-secondary btn-sm"
                style={{ padding: "5px 8px", opacity: page >= totalPages ? 0.4 : 1 }}
                title="Last Page"
              >
                <ChevronsRight size={14} />
              </button>
            </div>
          </div>
        </div>
      )}

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
        onSuccess={() => fetchRFPs()}
      />

      {/* Manual Create Modal */}
      <RFPCreateModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onCreated={() => fetchRFPs()}
      />
    </div>
  );
}
