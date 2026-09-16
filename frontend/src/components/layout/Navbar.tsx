"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { agentConfigService } from "@/services/agentConfigService";
import { AIAgentConfig } from "@/types";
import { apiRequest } from "@/services/apiClient";
import { API_ENDPOINTS } from "@/constants/api";
import { Bot, LogIn, LogOut, User as UserIcon, Sparkles, Menu, X } from "lucide-react";

interface NavbarProps {
  isMobileMenuOpen?: boolean;
  onToggleMobileMenu?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  isMobileMenuOpen = false,
  onToggleMobileMenu,
}) => {
  const { user, logout, isAuthenticated } = useAuth();
  const router = useRouter();
  const [isBackendHealthy, setIsBackendHealthy] = useState<boolean | null>(null);
  const [activeAgent, setActiveAgent] = useState<AIAgentConfig | null>(null);

  useEffect(() => {
    // Check backend health
    const checkHealth = async () => {
      try {
        await apiRequest(API_ENDPOINTS.HEALTH);
        setIsBackendHealthy(true);
      } catch {
        setIsBackendHealthy(false);
      }
    };

    // Check active agent
    const checkActiveAgent = async () => {
      try {
        const agent = await agentConfigService.getActiveConfig();
        setActiveAgent(agent);
      } catch {
        // user may not be logged in or endpoint restricted
      }
    };

    checkHealth();
    if (isAuthenticated) {
      checkActiveAgent();
    }
  }, [isAuthenticated]);

  return (
    <header
      style={{
        height: "64px",
        background: "rgba(10, 15, 29, 0.85)",
        backdropFilter: "blur(16px)",
        WebkitBackdropFilter: "blur(16px)",
        borderBottom: "1px solid var(--border-subtle)",
        position: "sticky",
        top: 0,
        zIndex: 100,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 clamp(10px, 2.5vw, 20px)",
      }}
    >
      {/* Brand & Mobile Hamburger Menu */}
      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        {/* Hamburger Toggle Button (Shown on Tablet & Mobile) */}
        <button
          onClick={onToggleMobileMenu}
          className="show-on-tablet"
          style={{
            display: "none",
            alignItems: "center",
            justifyContent: "center",
            padding: "7px",
            borderRadius: "8px",
            background: "rgba(255, 255, 255, 0.06)",
            border: "1px solid var(--border-subtle)",
            color: "#ffffff",
          }}
          aria-label={isMobileMenuOpen ? "Close menu" : "Open menu"}
        >
          {isMobileMenuOpen ? <X size={18} /> : <Menu size={18} />}
        </button>

        <Link href="/" style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: 8,
              background: "linear-gradient(135deg, #6366f1 0%, #06b6d4 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "0 0 15px rgba(99, 102, 241, 0.4)",
              flexShrink: 0,
            }}
          >
            <Sparkles size={17} color="#ffffff" />
          </div>
          <div style={{ display: "flex", alignItems: "center" }}>
            <span style={{ fontWeight: 800, fontSize: "1rem", letterSpacing: "-0.02em", color: "#ffffff" }}>
              RFP<span style={{ color: "var(--accent-cyan)" }}>INTELLECT</span>
            </span>
            <span
              className="hide-on-mobile"
              style={{
                marginLeft: "8px",
                fontSize: "0.625rem",
                fontWeight: 700,
                background: "rgba(99, 102, 241, 0.2)",
                color: "#a5b4fc",
                padding: "2px 6px",
                borderRadius: 4,
                border: "1px solid rgba(99, 102, 241, 0.3)",
              }}
            >
              AI AGENT
            </span>
          </div>
        </Link>
      </div>

      {/* Middle Status Chips */}
      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
        {/* API Health Pill */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "6px",
            background: "rgba(255, 255, 255, 0.04)",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            padding: "4px 8px",
            borderRadius: "9999px",
            fontSize: "0.725rem",
            color: "var(--text-secondary)",
          }}
        >
          <span
            className={`status-dot ${isBackendHealthy ? "active" : ""}`}
            style={{
              backgroundColor:
                isBackendHealthy === true
                  ? "var(--accent-emerald)"
                  : isBackendHealthy === false
                  ? "var(--accent-rose)"
                  : "var(--accent-amber)",
            }}
          />
          <span className="hide-on-mobile">
            API: {isBackendHealthy === true ? "Online (v1)" : isBackendHealthy === false ? "Offline" : "Checking..."}
          </span>
          <span className="show-on-mobile" style={{ display: "none" }}>
            {isBackendHealthy === true ? "API Online" : "Offline"}
          </span>
        </div>

        {/* Active AI Agent Chip (Hidden on tablet/mobile to prevent congestion) */}
        {activeAgent && (
          <div
            className="hide-on-tablet"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              background: "rgba(99, 102, 241, 0.12)",
              border: "1px solid rgba(99, 102, 241, 0.3)",
              padding: "4px 10px",
              borderRadius: "9999px",
              fontSize: "0.75rem",
              color: "#c7d2fe",
            }}
          >
            <Bot size={14} color="#818cf8" />
            <span>Agent: <strong style={{ color: "#ffffff" }}>{activeAgent.provider.toUpperCase()} ({activeAgent.model_name})</strong></span>
          </div>
        )}
      </div>

      {/* User Actions */}
      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        {isAuthenticated && user ? (
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                background: "rgba(255, 255, 255, 0.05)",
                padding: "4px 8px",
                borderRadius: "8px",
                border: "1px solid var(--border-subtle)",
              }}
            >
              <div
                style={{
                  width: 24,
                  height: 24,
                  borderRadius: "50%",
                  background: "linear-gradient(135deg, #6366f1, #a855f7)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "0.7rem",
                  fontWeight: 700,
                  color: "#ffffff",
                  flexShrink: 0,
                }}
              >
                {user.name ? user.name[0].toUpperCase() : "U"}
              </div>
              <div className="hide-on-mobile" style={{ display: "flex", flexDirection: "column" }}>
                <span
                  style={{
                    fontSize: "0.75rem",
                    fontWeight: 600,
                    color: "#f8fafc",
                    maxWidth: "100px",
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}
                >
                  {user.name}
                </span>
                <span
                  style={{
                    fontSize: "0.65rem",
                    color: "var(--text-muted)",
                    maxWidth: "110px",
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}
                >
                  {user.email}
                </span>
              </div>
            </div>

            <button
              onClick={() => {
                logout();
                router.push("/login");
              }}
              className="btn btn-secondary btn-sm"
              title="Sign Out"
              style={{ padding: "6px 8px" }}
            >
              <LogOut size={15} />
            </button>
          </div>
        ) : (
          <Link href="/login" className="btn btn-primary btn-sm">
            <LogIn size={15} />
            <span>Sign In</span>
          </Link>
        )}
      </div>
    </header>
  );
};
