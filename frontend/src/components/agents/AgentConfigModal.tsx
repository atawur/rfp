"use client";

import React, { useState } from "react";
import { Modal } from "@/components/ui/Modal";
import { agentConfigService } from "@/services/agentConfigService";
import { useToast } from "@/context/ToastContext";
import { AIAgentConfig, AIAgentConfigCreate } from "@/types";
import { Bot, Key, Eye, EyeOff, Loader2 } from "lucide-react";

interface AgentConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSaved: () => void;
  configToEdit?: AIAgentConfig | null;
}

export const AgentConfigModal: React.FC<AgentConfigModalProps> = ({
  isOpen,
  onClose,
  onSaved,
  configToEdit,
}) => {
  const isEditing = !!configToEdit;
  const [name, setName] = useState(configToEdit?.name || "");
  const [provider, setProvider] = useState<string>(configToEdit?.provider || "openai");
  const [modelName, setModelName] = useState(configToEdit?.model_name || "gpt-4o");
  const [apiKey, setApiKey] = useState(configToEdit?.api_key || "");
  const [temperature, setTemperature] = useState<number>(configToEdit?.temperature ?? 0.0);
  const [isActive, setIsActive] = useState<boolean>(configToEdit?.is_active ?? false);
  const [showApiKey, setShowApiKey] = useState(false);
  const [loading, setLoading] = useState(false);

  const { success, error } = useToast();

  const handleProviderChange = (newProvider: string) => {
    setProvider(newProvider);
    if (newProvider === "openai") {
      setModelName("gpt-4o");
    } else if (newProvider === "gemini") {
      setModelName("gemini-2.5-flash");
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !modelName || (!isEditing && !apiKey)) {
      error("Name, model, and API key are required.");
      return;
    }

    setLoading(true);
    try {
      if (isEditing && configToEdit) {
        await agentConfigService.updateConfig(configToEdit.id, {
          name,
          provider,
          model_name: modelName,
          temperature,
          is_active: isActive,
          ...(apiKey ? { api_key: apiKey } : {}),
        });
        success("AI Agent configuration updated!");
      } else {
        await agentConfigService.createConfig({
          name,
          provider,
          model_name: modelName,
          api_key: apiKey,
          temperature,
          is_active: isActive,
        });
        success("New AI Agent configuration registered!");
      }
      onSaved();
      onClose();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to save configuration";
      error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEditing ? "Edit AI Agent Model" : "Register New AI Agent Model"}
      subtitle="Configure an LLM provider and secret key for RFP analysis, schema mapping, and document OCR"
      maxWidth={600}
    >
      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        <div className="form-group">
          <label className="form-label" htmlFor="agent-name">Configuration Name *</label>
          <input
            id="agent-name"
            required
            className="form-control"
            placeholder="e.g. OpenAI GPT-4o Production"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </div>

        <div className="form-grid-2">
          <div className="form-group">
            <label className="form-label" htmlFor="agent-provider">Provider</label>
            <select
              id="agent-provider"
              className="form-control"
              value={provider}
              onChange={(e) => handleProviderChange(e.target.value)}
            >
              <option value="openai">OpenAI</option>
              <option value="gemini">Google Gemini</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="agent-model">Model Name</label>
            <select
              id="agent-model"
              className="form-control"
              value={modelName}
              onChange={(e) => setModelName(e.target.value)}
            >
              {provider === "openai" ? (
                <>
                  <option value="gpt-4o">gpt-4o (Recommended)</option>
                  <option value="gpt-4o-mini">gpt-4o-mini</option>
                  <option value="gpt-4-turbo">gpt-4-turbo</option>
                </>
              ) : (
                <>
                  <option value="gemini-2.5-flash">gemini-2.5-flash (Fast & Accurate)</option>
                  <option value="gemini-1.5-pro">gemini-1.5-pro (Deep Reasoning)</option>
                  <option value="gemini-1.5-flash">gemini-1.5-flash</option>
                </>
              )}
            </select>
          </div>
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="agent-key">
            {isEditing ? "Update API Key (Leave blank to keep current key)" : "Secret API Key *"}
          </label>
          <div style={{ position: "relative" }}>
            <input
              id="agent-key"
              type={showApiKey ? "text" : "password"}
              required={!isEditing}
              className="form-control"
              placeholder={isEditing ? "••••••••••••••••" : "sk-proj-... / AIzaSy..."}
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              style={{ paddingRight: "40px" }}
            />
            <button
              type="button"
              onClick={() => setShowApiKey(!showApiKey)}
              style={{
                position: "absolute",
                right: "12px",
                top: "50%",
                transform: "translateY(-50%)",
                color: "var(--text-muted)",
              }}
            >
              {showApiKey ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
        </div>

        {/* Temperature slider */}
        <div className="form-group">
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
            <label className="form-label" htmlFor="agent-temp">Sampling Temperature</label>
            <span style={{ fontSize: "0.8rem", color: "var(--accent-cyan)", fontFamily: "var(--font-mono)" }}>
              {temperature.toFixed(2)}
            </span>
          </div>
          <input
            id="agent-temp"
            type="range"
            min={0.0}
            max={1.0}
            step={0.05}
            value={temperature}
            onChange={(e) => setTemperature(parseFloat(e.target.value))}
            style={{ width: "100%", accentColor: "var(--accent-primary)" }}
          />
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.7rem", color: "var(--text-muted)", marginTop: "2px" }}>
            <span>0.0 (Strict / Deterministic)</span>
            <span>1.0 (Creative)</span>
          </div>
        </div>

        {/* Set as Active Checkbox */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginTop: "4px" }}>
          <input
            type="checkbox"
            id="is_active_checkbox"
            checked={isActive}
            onChange={(e) => setIsActive(e.target.checked)}
            style={{ width: 16, height: 16, accentColor: "var(--accent-emerald)" }}
          />
          <label htmlFor="is_active_checkbox" style={{ fontSize: "0.85rem", color: "var(--text-light)", cursor: "pointer" }}>
            Activate this AI Agent immediately (will become default for all extractions)
          </label>
        </div>

        <div style={{ display: "flex", justifyContent: "flex-end", gap: "12px", marginTop: "12px", flexWrap: "wrap" }}>
          <button type="button" onClick={onClose} className="btn btn-secondary">
            Cancel
          </button>
          <button type="submit" disabled={loading} className="btn btn-primary">
            {loading ? <Loader2 size={16} className="animate-spin" /> : <Bot size={16} />}
            <span>{isEditing ? "Save Changes" : "Create Configuration"}</span>
          </button>
        </div>
      </form>
    </Modal>
  );
};
