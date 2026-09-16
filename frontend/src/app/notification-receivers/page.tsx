"use client";

import React, { useEffect, useState, useMemo } from "react";
import { notificationReceiverService } from "@/services/notificationReceiverService";
import { NotificationReceiver } from "@/types";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import { Badge } from "@/components/ui/Badge";
import { AddReceiverModal } from "@/components/receivers/AddReceiverModal";
import { EditReceiverModal } from "@/components/receivers/EditReceiverModal";
import {
  Bell,
  BellOff,
  UserPlus,
  Mail,
  Edit2,
  Trash2,
  Loader2,
  Search,
  CheckCircle2,
  XCircle,
  Users,
  Phone,
  Briefcase,
} from "lucide-react";


export default function NotificationReceiversPage() {
  const { isAuthenticated } = useAuth();
  const { success, error } = useToast();
  const [receivers, setReceivers] = useState<NotificationReceiver[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [editingReceiver, setEditingReceiver] = useState<NotificationReceiver | null>(null);
  const [togglingId, setTogglingId] = useState<number | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const fetchReceivers = async () => {
    setLoading(true);
    try {
      const data = await notificationReceiverService.getReceivers(0, 100);
      setReceivers(data);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to load notification receivers";
      error(message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchReceivers();
    }
  }, [isAuthenticated]);

  const handleQuickToggleStatus = async (receiver: NotificationReceiver, e: React.MouseEvent) => {
    e.stopPropagation();
    setTogglingId(receiver.id);
    const nextStatus = receiver.status === "active" ? "inactive" : "active";
    try {
      await notificationReceiverService.updateReceiver(receiver.id, {
        status: nextStatus,
      });
      setReceivers((prev) =>
        prev.map((r) => (r.id === receiver.id ? { ...r, status: nextStatus } : r))
      );
      success(
        nextStatus === "active"
          ? `Activated alerts for ${receiver.name}`
          : `Paused alerts for ${receiver.name}`
      );
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to update receiver status";
      error(message);
    } finally {
      setTogglingId(null);
    }
  };

  const handleDeleteReceiver = async (receiver: NotificationReceiver) => {
    if (!window.confirm(`Are you sure you want to remove "${receiver.name}" (${receiver.email}) from notification receivers?`)) {
      return;
    }
    setDeletingId(receiver.id);
    try {
      await notificationReceiverService.deleteReceiver(receiver.id);
      setReceivers((prev) => prev.filter((r) => r.id !== receiver.id));
      success(`Removed notification receiver "${receiver.name}"`);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to delete receiver";
      error(message);
    } finally {
      setDeletingId(null);
    }
  };

  const filteredReceivers = useMemo(() => {
    if (!searchQuery.trim()) return receivers;
    const q = searchQuery.toLowerCase();
    return receivers.filter(
      (r) =>
        r.name.toLowerCase().includes(q) ||
        r.email.toLowerCase().includes(q) ||
        (r.designation && r.designation.toLowerCase().includes(q)) ||
        (r.phone && r.phone.toLowerCase().includes(q))
    );
  }, [receivers, searchQuery]);


  const activeCount = receivers.filter((r) => r.status === "active").length;
  const inactiveCount = receivers.length - activeCount;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          flexWrap: "wrap",
          gap: "16px",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "4px" }}>
            <h1 style={{ fontSize: "1.75rem", fontWeight: 800, color: "#ffffff", letterSpacing: "-0.5px" }}>
              Notification Receivers
            </h1>
            <span
              style={{
                fontSize: "0.75rem",
                padding: "3px 8px",
                borderRadius: "12px",
                background: "rgba(6, 182, 212, 0.15)",
                color: "var(--accent-cyan)",
                border: "1px solid rgba(6, 182, 212, 0.3)",
                fontWeight: 600,
              }}
            >
              {receivers.length} Total
            </span>
          </div>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", maxWidth: "680px" }}>
            Manage email contacts who receive automated procurement and RFP alerts. Configure each website in Monitored Sources to notify all active receivers or specific selected recipients.
          </p>
        </div>

        <button
          onClick={() => setIsAddModalOpen(true)}
          className="btn btn-primary"
          style={{ display: "inline-flex", alignItems: "center", gap: "8px" }}
        >
          <UserPlus size={16} />
          <span>Add Receiver</span>
        </button>
      </div>

      {/* Metrics Row */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: "16px",
        }}
      >
        <div className="glass-card" style={{ padding: "18px 20px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "8px" }}>
            <span style={{ fontSize: "0.825rem", color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.5px" }}>
              Total Receivers
            </span>
            <Users size={18} color="var(--accent-cyan)" />
          </div>
          <div style={{ fontSize: "1.65rem", fontWeight: 800, color: "#ffffff" }}>
            {loading ? "..." : receivers.length}
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "4px" }}>
            Configured notification recipients
          </div>
        </div>

        <div className="glass-card" style={{ padding: "18px 20px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "8px" }}>
            <span style={{ fontSize: "0.825rem", color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.5px" }}>
              Active Alerts
            </span>
            <CheckCircle2 size={18} color="#10b981" />
          </div>
          <div style={{ fontSize: "1.65rem", fontWeight: 800, color: "#10b981" }}>
            {loading ? "..." : activeCount}
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "4px" }}>
            Currently receiving automated email alerts
          </div>
        </div>

        <div className="glass-card" style={{ padding: "18px 20px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "8px" }}>
            <span style={{ fontSize: "0.825rem", color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.5px" }}>
              Paused / Muted
            </span>
            <XCircle size={18} color="var(--text-muted)" />
          </div>
          <div style={{ fontSize: "1.65rem", fontWeight: 800, color: "var(--text-muted)" }}>
            {loading ? "..." : inactiveCount}
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "4px" }}>
            Alerts temporarily disabled
          </div>
        </div>
      </div>

      {/* Filter and Search */}
      <div
        className="glass-card"
        style={{
          padding: "12px 18px",
          display: "flex",
          alignItems: "center",
          gap: "12px",
        }}
      >
        <Search size={16} color="var(--text-muted)" />
        <input
          type="text"
          placeholder="Filter receivers by name or email address..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{
            background: "transparent",
            border: "none",
            outline: "none",
            color: "#ffffff",
            fontSize: "0.9rem",
            width: "100%",
          }}
        />
        {searchQuery && (
          <button
            onClick={() => setSearchQuery("")}
            style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer", fontSize: "0.8rem" }}
          >
            Clear
          </button>
        )}
      </div>

      {/* Receivers Table */}
      {loading ? (
        <div style={{ padding: "64px", textAlign: "center", color: "var(--text-muted)" }}>
          <Loader2 size={24} className="animate-spin" style={{ margin: "0 auto 8px" }} />
          Loading notification receivers...
        </div>
      ) : filteredReceivers.length === 0 ? (
        <div
          className="glass-card"
          style={{
            padding: "56px 24px",
            textAlign: "center",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "12px",
          }}
        >
          <div
            style={{
              width: 48,
              height: 48,
              borderRadius: "50%",
              background: "rgba(6, 182, 212, 0.1)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "var(--accent-cyan)",
            }}
          >
            <Bell size={24} />
          </div>
          <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#ffffff" }}>
            {searchQuery ? "No matching receivers found" : "No Notification Receivers Added"}
          </h3>
          <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)", maxWidth: "440px" }}>
            {searchQuery
              ? "Try adjusting your search filter or clear the query."
              : "Register recipient contacts who should receive automated emails whenever new RFPs or tenders matching monitored portals are discovered."}
          </p>
          {!searchQuery && (
            <button
              onClick={() => setIsAddModalOpen(true)}
              className="btn btn-primary btn-sm"
              style={{ marginTop: "8px" }}
            >
              <UserPlus size={14} />
              <span>Add First Receiver</span>
            </button>
          )}
        </div>
      ) : (
        <div className="glass-card table-container" style={{ padding: "16px" }}>
          <table className="custom-table" style={{ minWidth: "640px" }}>
            <thead>
              <tr>
                <th>Recipient Contact</th>
                <th>Email Address</th>
                <th>Phone Number</th>
                <th>Notification Status</th>
                <th style={{ textAlign: "right" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredReceivers.map((receiver) => (
                <tr key={receiver.id}>
                  <td>
                    <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                      <div
                        style={{
                          width: 36,
                          height: 36,
                          borderRadius: "50%",
                          background:
                            receiver.status === "active"
                              ? "linear-gradient(135deg, #06b6d4, #3b82f6)"
                              : "rgba(255, 255, 255, 0.08)",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          fontSize: "0.85rem",
                          fontWeight: 700,
                          color: "#f8fafc",
                          flexShrink: 0,
                        }}
                      >
                        {receiver.name ? receiver.name[0].toUpperCase() : "R"}
                      </div>
                      <div>
                        <div style={{ fontWeight: 600, color: "#ffffff", fontSize: "0.925rem" }}>
                          {receiver.name}
                        </div>
                        {receiver.designation ? (
                          <div style={{ display: "inline-flex", alignItems: "center", gap: "5px", color: "var(--accent-cyan)", fontSize: "0.775rem", marginTop: "2px" }}>
                            <Briefcase size={12} />
                            <span>{receiver.designation}</span>
                          </div>
                        ) : (
                          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>No designation specified</span>
                        )}
                      </div>
                    </div>
                  </td>
                  <td>
                    <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "var(--text-light)", fontSize: "0.85rem" }}>
                      <Mail size={13} color="var(--text-muted)" />
                      <span>{receiver.email}</span>
                    </div>
                  </td>
                  <td>
                    {receiver.phone ? (
                      <div style={{ display: "inline-flex", alignItems: "center", gap: "6px", color: "var(--text-light)", fontSize: "0.85rem" }}>
                        <Phone size={13} color="var(--accent-cyan)" />
                        <span>{receiver.phone}</span>
                      </div>
                    ) : (
                      <span style={{ color: "var(--text-muted)", fontSize: "0.825rem" }}>—</span>
                    )}
                  </td>
                  <td>
                    <button
                      type="button"
                      onClick={(e) => handleQuickToggleStatus(receiver, e)}
                      disabled={togglingId === receiver.id}
                      title="Click to toggle alert status"
                      style={{
                        background: "none",
                        border: "none",
                        padding: 0,
                        cursor: "pointer",
                      }}
                    >


                      {togglingId === receiver.id ? (
                        <span
                          className="badge"
                          style={{
                            background: "rgba(255, 255, 255, 0.05)",
                            color: "var(--text-muted)",
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "6px",
                          }}
                        >
                          <Loader2 size={12} className="animate-spin" /> Updating...
                        </span>
                      ) : receiver.status === "active" ? (
                        <span
                          className="badge badge-open"
                          style={{
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "6px",
                            cursor: "pointer",
                          }}
                        >
                          <Bell size={12} /> Active (Alerts Enabled)
                        </span>
                      ) : (
                        <span
                          className="badge badge-closed"
                          style={{
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "6px",
                            cursor: "pointer",
                            background: "rgba(255, 255, 255, 0.05)",
                            color: "var(--text-muted)",
                            borderColor: "var(--border-color)",
                          }}
                        >
                          <BellOff size={12} /> Inactive (Muted)
                        </span>
                      )}
                    </button>
                  </td>
                  <td style={{ textAlign: "right" }}>
                    <div style={{ display: "inline-flex", gap: "6px" }}>
                      <button
                        onClick={() => setEditingReceiver(receiver)}
                        className="btn btn-secondary"
                        style={{ padding: "6px 10px", fontSize: "0.8rem" }}
                        title="Edit recipient"
                      >
                        <Edit2 size={13} />
                      </button>
                      <button
                        onClick={() => handleDeleteReceiver(receiver)}
                        disabled={deletingId === receiver.id}
                        className="btn btn-secondary"
                        style={{
                          padding: "6px 10px",
                          fontSize: "0.8rem",
                          color: "#ef4444",
                          borderColor: "rgba(239, 68, 68, 0.2)",
                        }}
                        title="Delete recipient"
                      >
                        {deletingId === receiver.id ? (
                          <Loader2 size={13} className="animate-spin" />
                        ) : (
                          <Trash2 size={13} />
                        )}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Modals */}
      <AddReceiverModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onCreated={fetchReceivers}
      />

      <EditReceiverModal
        isOpen={Boolean(editingReceiver)}
        onClose={() => setEditingReceiver(null)}
        receiver={editingReceiver}
        onUpdated={fetchReceivers}
      />
    </div>
  );
}
