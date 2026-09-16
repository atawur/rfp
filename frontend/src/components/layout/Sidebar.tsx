"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  FileText,
  Globe,
  Bot,
  Users,
  BellRing,
  Zap,
  ExternalLink,
  X,
  Sparkles,
} from "lucide-react";

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
  onOpenModeAModal?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  isOpen = false,
  onClose,
  onOpenModeAModal,
}) => {
  const pathname = usePathname();

  const navItems = [
    { label: "Dashboard", href: "/", icon: LayoutDashboard },
    { label: "RFP Intelligence", href: "/rfps", icon: FileText },
    { label: "Monitored Sources", href: "/websites", icon: Globe },
    { label: "Notification Receivers", href: "/notification-receivers", icon: BellRing },
    { label: "AI Agent Hub", href: "/agents", icon: Bot },
    { label: "Team Members", href: "/users", icon: Users },
  ];


  const handleLinkClick = () => {
    if (onClose) onClose();
  };

  const handleModeAClick = () => {
    if (onClose) onClose();
    if (onOpenModeAModal) onOpenModeAModal();
  };

  return (
    <aside className={`app-sidebar ${isOpen ? "sidebar-open" : ""}`}>
      <div>
        {/* Mobile Header with Brand & Close Button */}
        <div
          className="show-on-tablet"
          style={{
            display: "none",
            alignItems: "center",
            justifyContent: "space-between",
            paddingBottom: "16px",
            marginBottom: "16px",
            borderBottom: "1px solid var(--border-subtle)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div
              style={{
                width: 32,
                height: 32,
                borderRadius: 8,
                background: "linear-gradient(135deg, #6366f1 0%, #06b6d4 100%)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <Sparkles size={16} color="#ffffff" />
            </div>
            <span style={{ fontWeight: 800, fontSize: "1rem", color: "#ffffff" }}>
              RFP<span style={{ color: "var(--accent-cyan)" }}>INTELLECT</span>
            </span>
          </div>

          <button
            onClick={onClose}
            aria-label="Close menu"
            style={{
              padding: "6px",
              borderRadius: "8px",
              background: "rgba(255, 255, 255, 0.06)",
              color: "var(--text-secondary)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Mode A Instant Action Banner */}
        <div style={{ marginBottom: "24px" }}>
          <button
            onClick={handleModeAClick}
            className="btn btn-cyan"
            style={{
              width: "100%",
              padding: "12px 16px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "8px",
              borderRadius: "10px",
              fontWeight: 700,
              fontSize: "0.85rem",
              letterSpacing: "0.02em",
            }}
          >
            <Zap size={18} />
            <span>Mode A: Ingest URL</span>
          </button>
        </div>

        {/* Navigation Items */}
        <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          <span
            style={{
              fontSize: "0.7rem",
              fontWeight: 700,
              textTransform: "uppercase",
              letterSpacing: "0.08em",
              color: "var(--text-muted)",
              padding: "0 12px 6px 12px",
            }}
          >
            Platform Navigation
          </span>

          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive =
              item.href === "/"
                ? pathname === "/"
                : pathname.startsWith(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={handleLinkClick}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "12px",
                  padding: "11px 14px",
                  borderRadius: "10px",
                  fontSize: "0.875rem",
                  fontWeight: isActive ? 700 : 500,
                  color: isActive ? "#ffffff" : "var(--text-secondary)",
                  backgroundColor: isActive
                    ? "rgba(99, 102, 241, 0.15)"
                    : "transparent",
                  border: isActive
                    ? "1px solid rgba(99, 102, 241, 0.3)"
                    : "1px solid transparent",
                  transition: "all 0.15s ease",
                }}
                onMouseEnter={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.04)";
                    e.currentTarget.style.color = "#ffffff";
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.backgroundColor = "transparent";
                    e.currentTarget.style.color = "var(--text-secondary)";
                  }
                }}
              >
                <Icon
                  size={18}
                  style={{
                    color: isActive ? "var(--accent-primary)" : "var(--text-muted)",
                  }}
                />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Footer Info */}
      <div
        style={{
          padding: "16px",
          borderRadius: "12px",
          background: "rgba(255, 255, 255, 0.02)",
          border: "1px solid var(--border-subtle)",
          marginTop: "20px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
          <span style={{ fontSize: "0.8rem", fontWeight: 700, color: "#ffffff" }}>
            Mode A & B Ingestion
          </span>
        </div>
        <p style={{ fontSize: "0.725rem", color: "var(--text-muted)", lineHeight: 1.4 }}>
          Direct AI document extraction & automated daily crawler pipeline.
        </p>
        <div style={{ marginTop: "10px" }}>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            style={{
              fontSize: "0.75rem",
              color: "var(--accent-cyan)",
              display: "flex",
              alignItems: "center",
              gap: "4px",
              fontWeight: 600,
            }}
          >
            <span>Swagger API Docs</span>
            <ExternalLink size={12} />
          </a>
        </div>
      </div>
    </aside>
  );
};
