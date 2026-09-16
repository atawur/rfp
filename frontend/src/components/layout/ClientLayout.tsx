"use client";

import React, { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { AppShell } from "./AppShell";
import { Sparkles, Loader2 } from "lucide-react";

export const ClientLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const pathname = usePathname();
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();
  const isAuthPage = pathname === "/login";

  useEffect(() => {
    if (isLoading) return;

    if (!isAuthenticated && !isAuthPage) {
      router.replace("/login");
    } else if (isAuthenticated && isAuthPage) {
      router.replace("/");
    }
  }, [isAuthenticated, isLoading, isAuthPage, router]);

  // While checking session on mount
  if (isLoading) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: "16px",
          background: "var(--bg-main)",
        }}
      >
        <div
          style={{
            width: 48,
            height: 48,
            borderRadius: 14,
            background: "linear-gradient(135deg, #6366f1, #06b6d4)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 0 25px rgba(99, 102, 241, 0.5)",
          }}
        >
          <Sparkles size={26} color="#ffffff" />
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "var(--text-secondary)", fontSize: "0.9rem" }}>
          <Loader2 size={16} className="animate-spin" color="var(--accent-cyan)" />
          <span>Verifying authentication session...</span>
        </div>
      </div>
    );
  }

  // If unauthenticated and on a protected page, block rendering until redirect happens
  if (!isAuthenticated && !isAuthPage) {
    return null;
  }

  // If on login page, render without AppShell
  if (isAuthPage) {
    return <>{children}</>;
  }

  // Otherwise render full authenticated app
  return <AppShell>{children}</AppShell>;
};
