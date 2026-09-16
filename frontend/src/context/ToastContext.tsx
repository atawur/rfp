"use client";

import React, { createContext, useContext, useState, useCallback } from "react";
import { CheckCircle2, AlertCircle, Info, AlertTriangle, X } from "lucide-react";

export type ToastType = "success" | "error" | "info" | "warning";

interface Toast {
  id: string;
  message: string;
  type: ToastType;
}

interface ToastContextType {
  showToast: (message: string, type?: ToastType) => void;
  success: (message: string) => void;
  error: (message: string) => void;
  info: (message: string) => void;
  warning: (message: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const showToast = useCallback(
    (message: string, type: ToastType = "info") => {
      const id = Math.random().toString(36).substring(2, 9);
      setToasts((prev) => [...prev, { id, message, type }]);

      setTimeout(() => {
        removeToast(id);
      }, 4500);
    },
    [removeToast]
  );

  const success = useCallback((msg: string) => showToast(msg, "success"), [showToast]);
  const error = useCallback((msg: string) => showToast(msg, "error"), [showToast]);
  const info = useCallback((msg: string) => showToast(msg, "info"), [showToast]);
  const warning = useCallback((msg: string) => showToast(msg, "warning"), [showToast]);

  return (
    <ToastContext.Provider value={{ showToast, success, error, info, warning }}>
      {children}
      <div
        style={{
          position: "fixed",
          bottom: 24,
          right: 24,
          zIndex: 9999,
          display: "flex",
          flexDirection: "column",
          gap: 10,
          pointerEvents: "none",
        }}
      >
        {toasts.map((toast) => {
          let bg = "rgba(15, 23, 42, 0.95)";
          let border = "rgba(255, 255, 255, 0.1)";
          let text = "#f8fafc";
          let IconComponent = Info;

          if (toast.type === "success") {
            border = "rgba(16, 185, 129, 0.4)";
            IconComponent = CheckCircle2;
            text = "#34d399";
          } else if (toast.type === "error") {
            border = "rgba(244, 63, 94, 0.4)";
            IconComponent = AlertCircle;
            text = "#fb7185";
          } else if (toast.type === "warning") {
            border = "rgba(245, 158, 11, 0.4)";
            IconComponent = AlertTriangle;
            text = "#fbbf24";
          } else {
            border = "rgba(6, 182, 212, 0.4)";
            IconComponent = Info;
            text = "#38bdf8";
          }

          return (
            <div
              key={toast.id}
              className="animate-fade-in"
              style={{
                pointerEvents: "auto",
                minWidth: 280,
                maxWidth: 420,
                padding: "12px 16px",
                background: bg,
                backdropFilter: "blur(16px)",
                border: `1px solid ${border}`,
                borderRadius: 12,
                boxShadow: "0 10px 30px -5px rgba(0,0,0,0.7)",
                display: "flex",
                alignItems: "center",
                gap: 12,
                color: "#f8fafc",
                fontSize: "0.875rem",
              }}
            >
              <IconComponent size={20} style={{ color: text, flexShrink: 0 }} />
              <div style={{ flex: 1, lineHeight: 1.4 }}>{toast.message}</div>
              <button
                onClick={() => removeToast(toast.id)}
                style={{
                  color: "var(--text-muted)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  padding: 4,
                  borderRadius: 4,
                }}
              >
                <X size={16} />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
}
