"use client";

import React, { useState } from "react";
import { Navbar } from "./Navbar";
import { Sidebar } from "./Sidebar";
import { ModeAImportModal } from "@/components/rfp/ModeAImportModal";

interface AppShellProps {
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const [isModeAModalOpen, setIsModeAModalOpen] = useState(false);
  const [isMobileNavOpen, setIsMobileNavOpen] = useState(false);

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <Navbar
        isMobileMenuOpen={isMobileNavOpen}
        onToggleMobileMenu={() => setIsMobileNavOpen(!isMobileNavOpen)}
      />

      {/* Backdrop overlay for mobile drawer */}
      {isMobileNavOpen && (
        <div
          className="sidebar-backdrop"
          onClick={() => setIsMobileNavOpen(false)}
          aria-hidden="true"
        />
      )}

      <div style={{ display: "flex", flex: 1, position: "relative" }}>
        <Sidebar
          isOpen={isMobileNavOpen}
          onClose={() => setIsMobileNavOpen(false)}
          onOpenModeAModal={() => setIsModeAModalOpen(true)}
        />

        <main className="app-main-content">
          {children}
        </main>
      </div>

      <ModeAImportModal
        isOpen={isModeAModalOpen}
        onClose={() => setIsModeAModalOpen(false)}
        onSuccess={() => {
          // If on rfps page or home page, can trigger refresh
          if (typeof window !== "undefined") {
            window.dispatchEvent(new CustomEvent("rfp-created"));
          }
        }}
      />
    </div>
  );
};
