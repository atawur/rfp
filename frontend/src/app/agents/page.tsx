"use client";

import React, { useEffect, useState } from "react";
import { agentConfigService } from "@/services/agentConfigService";
import { AIAgentConfig } from "@/types";
import { AgentConfigModal } from "@/components/agents/AgentConfigModal";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import {
  Bot,
  Plus,
  CheckCircle2,
  Trash2,
  Edit2,
  Key,
  Cpu,
  Sparkles,
  Zap,
  Sliders,
  Loader2,
} from "lucide-react";

export default function AgentsPage() {
  const { isAuthenticated } = useAuth();
  const [configs, setConfigs] = useState<AIAgentConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingConfig, setEditingConfig] = useState<AIAgentConfig | null>(null);
  const [activatingId, setActivatingId] = useState<number | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const { success, error } = useToast();

  const fetchConfigs = async () => {
    setLoading(true);
    try {
      const data = await agentConfigService.getConfigs(0, 100);
      setConfigs(data);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchConfigs();
    }
  }, [isAuthenticated]);

  const handleActivate = async (config: AIAgentConfig) => {
    setActivatingId(config.id);
    try {
      await agentConfigService.activateConfig(config.id);
      success(`"${config.name}" is now the active AI Agent!`);
      await fetchConfigs();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to activate agent";
      error(msg);
    } finally {
      setActivatingId(null);
    }
  };

  const handleDelete = async (config: AIAgentConfig) => {
    if (!window.confirm(`Are you sure you want to delete "${config.name}"?`)) return;

    setDeletingId(config.id);
    try {
      await agentConfigService.deleteConfig(config.id);
      success(`Deleted configuration "${config.name}"`);
      await fetchConfigs();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to delete agent";
      error(msg);
    } finally {
      setDeletingId(null);
    }
  };

  const activeConfig = configs.find((c) => c.is_active);

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
            AI Agent Intelligence Engine
          </h1>
          <p style={{ fontSize: "0.9rem", color: "var(--text-secondary)", marginTop: "4px" }}>
            Manage LLM provider configurations (OpenAI & Gemini), sampling temperatures, and active models
          </p>
        </div>

        <button
          onClick={() => {
            setEditingConfig(null);
            setIsModalOpen(true);
          }}
          className="btn btn-primary"
        >
          <Plus size={16} />
          <span>Register New AI Agent</span>
        </button>
      </div>

      {/* Active Model Spotlight Card */}
      {activeConfig && (
        <div
          className="glass-card animate-fade-in"
          style={{
            padding: "24px 28px",
            background:
              "linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(6, 182, 212, 0.1) 100%)",
            border: "1px solid rgba(99, 102, 241, 0.4)",
            boxShadow: "0 0 35px -5px rgba(99, 102, 241, 0.25)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "20px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "20px", flexWrap: "wrap" }}>
            <div
              style={{
                width: 56,
                height: 56,
                borderRadius: 14,
                background: "linear-gradient(135deg, #6366f1 0%, #06b6d4 100%)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                boxShadow: "0 0 20px rgba(99, 102, 241, 0.5)",
                flexShrink: 0,
              }}
            >
              <Sparkles size={28} color="#ffffff" />
            </div>

            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "4px", flexWrap: "wrap" }}>
                <span
                  style={{
                    fontSize: "0.75rem",
                    fontWeight: 700,
                    textTransform: "uppercase",
                    letterSpacing: "0.08em",
                    color: "var(--accent-cyan)",
                  }}
                >
                  CURRENTLY ACTIVE AGENT
                </span>
                <span className="badge badge-open">In Production</span>
              </div>

              <h2 style={{ fontSize: "1.4rem", fontWeight: 800, color: "#ffffff" }}>
                {activeConfig.name}
              </h2>

              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "16px",
                  marginTop: "6px",
                  fontSize: "0.825rem",
                  color: "var(--text-light)",
                  flexWrap: "wrap",
                }}
              >
                <div>
                  <span style={{ color: "var(--text-muted)" }}>Provider:</span>{" "}
                  <strong style={{ color: "var(--accent-cyan)", textTransform: "uppercase" }}>
                    {activeConfig.provider}
                  </strong>
                </div>
                <div>
                  <span style={{ color: "var(--text-muted)" }}>Model:</span>{" "}
                  <code style={{ background: "rgba(0,0,0,0.3)", padding: "2px 6px", borderRadius: 4, color: "#ffffff" }}>
                    {activeConfig.model_name}
                  </code>
                </div>
                <div>
                  <span style={{ color: "var(--text-muted)" }}>Temperature:</span>{" "}
                  <strong style={{ color: "var(--accent-emerald)", fontFamily: "var(--font-mono)" }}>
                    {activeConfig.temperature}
                  </strong>
                </div>
              </div>
            </div>
          </div>

          <button
            onClick={() => {
              setEditingConfig(activeConfig);
              setIsModalOpen(true);
            }}
            className="btn btn-secondary"
            style={{ padding: "8px 16px" }}
          >
            <Edit2 size={15} />
            <span>Modify Settings</span>
          </button>
        </div>
      )}

      {/* Configurations Grid */}
      {loading ? (
        <div style={{ padding: "64px", textAlign: "center", color: "var(--text-muted)" }}>
          Loading AI agent profiles...
        </div>
      ) : configs.length === 0 ? (
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
          <Bot size={48} color="var(--text-muted)" />
          <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#ffffff" }}>
            No AI Models Configured
          </h3>
          <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)", maxWidth: "450px" }}>
            Configure your OpenAI or Google Gemini API key to activate autonomous tender field extraction.
          </p>
          <button
            onClick={() => {
              setEditingConfig(null);
              setIsModalOpen(true);
            }}
            className="btn btn-cyan btn-sm"
          >
            <Plus size={14} />
            <span>Register First Agent</span>
          </button>
        </div>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(min(100%, 300px), 1fr))",
            gap: "20px",
          }}
        >
          {configs.map((config) => {
            const isCurActive = config.is_active;
            const isGemini = config.provider.toLowerCase().includes("gemini");

            return (
              <div
                key={config.id}
                className="glass-card"
                style={{
                  padding: "24px",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                  minHeight: "240px",
                  borderColor: isCurActive ? "rgba(99, 102, 241, 0.4)" : "var(--border-subtle)",
                }}
              >
                <div>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      marginBottom: "14px",
                    }}
                  >
                    <span
                      style={{
                        padding: "4px 10px",
                        borderRadius: "6px",
                        fontSize: "0.75rem",
                        fontWeight: 700,
                        textTransform: "uppercase",
                        letterSpacing: "0.04em",
                        backgroundColor: isGemini ? "rgba(6, 182, 212, 0.15)" : "rgba(16, 185, 129, 0.15)",
                        color: isGemini ? "#22d3ee" : "#34d399",
                        border: isGemini
                          ? "1px solid rgba(6, 182, 212, 0.3)"
                          : "1px solid rgba(16, 185, 129, 0.3)",
                      }}
                    >
                      {config.provider.toUpperCase()}
                    </span>

                    {isCurActive ? (
                      <span className="badge badge-open" style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                        <CheckCircle2 size={12} />
                        <span>Active</span>
                      </span>
                    ) : (
                      <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                        Standby
                      </span>
                    )}
                  </div>

                  <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#ffffff", marginBottom: "8px" }}>
                    {config.name}
                  </h3>

                  <div style={{ display: "flex", flexDirection: "column", gap: "8px", fontSize: "0.825rem", color: "var(--text-light)" }}>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                      <span style={{ color: "var(--text-muted)" }}>Model Identifier:</span>
                      <strong
                        style={{
                          color: "#ffffff",
                          fontFamily: "var(--font-mono)",
                          maxWidth: "180px",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                        }}
                        title={config.model_name}
                      >
                        {config.model_name}
                      </strong>
                    </div>

                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                      <span style={{ color: "var(--text-muted)" }}>Temperature:</span>
                      <span style={{ color: "var(--accent-cyan)", fontFamily: "var(--font-mono)" }}>
                        {config.temperature}
                      </span>
                    </div>

                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                      <span style={{ color: "var(--text-muted)" }}>API Key:</span>
                      <span style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)", fontSize: "0.75rem" }}>
                        {config.api_key_masked || "••••••••"}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Card Actions */}
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    marginTop: "20px",
                    paddingTop: "14px",
                    borderTop: "1px solid var(--border-subtle)",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <button
                      onClick={() => {
                        setEditingConfig(config);
                        setIsModalOpen(true);
                      }}
                      className="btn btn-secondary btn-sm"
                      style={{ padding: "6px 10px" }}
                      title="Edit Configuration"
                    >
                      <Edit2 size={14} />
                    </button>

                    <button
                      onClick={() => handleDelete(config)}
                      disabled={deletingId === config.id || isCurActive}
                      className="btn btn-danger btn-sm"
                      style={{ padding: "6px 10px" }}
                      title={isCurActive ? "Cannot delete active agent" : "Delete Configuration"}
                    >
                      {deletingId === config.id ? (
                        <Loader2 size={14} className="animate-spin" />
                      ) : (
                        <Trash2 size={14} />
                      )}
                    </button>
                  </div>

                  {!isCurActive && (
                    <button
                      onClick={() => handleActivate(config)}
                      disabled={activatingId === config.id}
                      className="btn btn-primary btn-sm"
                    >
                      {activatingId === config.id ? (
                        <Loader2 size={13} className="animate-spin" />
                      ) : (
                        <Zap size={13} />
                      )}
                      <span>Set as Active</span>
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Modal */}
      <AgentConfigModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSaved={() => fetchConfigs()}
        configToEdit={editingConfig}
      />
    </div>
  );
}
