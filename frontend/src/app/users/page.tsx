"use client";

import React, { useEffect, useState } from "react";
import { userService } from "@/services/userService";
import { User } from "@/types";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import { Badge } from "@/components/ui/Badge";
import { AddUserModal } from "@/components/users/AddUserModal";
import { EditUserModal } from "@/components/users/EditUserModal";
import { UserPlus, Shield, Mail, Edit2, Loader2 } from "lucide-react";

export default function UsersPage() {
  const { user: currentUser, isAuthenticated } = useAuth();
  const { success, error } = useToast();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const data = await userService.getUsers(0, 100);
      setUsers(data);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to load team members";
      error(message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchUsers();
    }
  }, [isAuthenticated]);

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
            Team & Access Control
          </h1>
          <p style={{ fontSize: "0.9rem", color: "var(--text-secondary)", marginTop: "4px" }}>
            Manage platform members, role assignments, email notification delivery, and account profiles
          </p>
        </div>

        <button onClick={() => setIsAddModalOpen(true)} className="btn btn-primary">
          <UserPlus size={16} />
          <span>Add Team Member</span>
        </button>
      </div>

      {/* Current User Card */}
      {currentUser && (
        <div
          className="glass-card"
          style={{
            padding: "20px 24px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "16px",
            background: "rgba(99, 102, 241, 0.06)",
            border: "1px solid rgba(99, 102, 241, 0.2)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "16px", flexWrap: "wrap" }}>
            <div
              style={{
                width: 48,
                height: 48,
                borderRadius: "50%",
                background: "linear-gradient(135deg, #6366f1, #a855f7)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "1.2rem",
                fontWeight: 700,
                color: "#ffffff",
                flexShrink: 0,
              }}
            >
              {currentUser.name ? currentUser.name[0].toUpperCase() : "U"}
            </div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
                <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#ffffff" }}>
                  {currentUser.name}
                </h3>
                <span className="badge badge-open">You (Active Session)</span>
              </div>
              <p style={{ fontSize: "0.825rem", color: "var(--text-muted)", marginTop: "2px" }}>
                {currentUser.email} • Role:{" "}
                <strong style={{ color: "var(--accent-cyan)" }}>
                  {currentUser.role_id === 1 ? "Super Admin" : "Standard Member"}
                </strong>
              </p>
            </div>
          </div>

          <button
            onClick={() => setEditingUser(currentUser)}
            className="btn btn-secondary"
            style={{ fontSize: "0.85rem", padding: "8px 14px", gap: "6px" }}
          >
            <Edit2 size={14} />
            <span>Edit My Profile</span>
          </button>
        </div>
      )}

      {/* Users Directory Table */}
      {loading ? (
        <div style={{ padding: "64px", textAlign: "center", color: "var(--text-muted)" }}>
          Loading team members...
        </div>
      ) : (
        <div className="glass-card table-container" style={{ padding: "16px" }}>
          <table className="custom-table" style={{ minWidth: "640px" }}>
            <thead>
              <tr>
                <th>Member</th>
                <th>Email Address</th>
                <th>Access Role</th>
                <th>Account Status</th>
                <th style={{ textAlign: "right" }}>Actions</th>
              </tr>
            </thead>

            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td>
                    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <div
                        style={{
                          width: 34,
                          height: 34,
                          borderRadius: "50%",
                          background:
                            u.id === currentUser?.id
                              ? "linear-gradient(135deg, #6366f1, #a855f7)"
                              : "rgba(255, 255, 255, 0.08)",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          fontSize: "0.85rem",
                          fontWeight: 700,
                          color: "#f8fafc",
                          border: u.id === currentUser?.id ? "1px solid rgba(255,255,255,0.4)" : "none",
                        }}
                      >
                        {u.name ? u.name[0].toUpperCase() : "U"}
                      </div>
                      <div>
                        <span style={{ fontWeight: 600, color: "#ffffff", display: "flex", alignItems: "center", gap: "6px" }}>
                          {u.name}
                          {u.id === currentUser?.id && (
                            <span style={{ fontSize: "0.65rem", padding: "1px 5px", borderRadius: "4px", background: "rgba(99, 102, 241, 0.25)", color: "#a5b4fc" }}>
                              YOU
                            </span>
                          )}
                        </span>
                      </div>
                    </div>
                  </td>
                  <td>
                    <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "var(--text-light)" }}>
                      <Mail size={14} color="var(--text-muted)" />
                      <span>{u.email}</span>
                    </div>
                  </td>
                  <td>
                    <span
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "6px",
                        fontSize: "0.8rem",
                        fontWeight: 600,
                        color: u.role_id === 1 ? "var(--accent-cyan)" : "var(--text-secondary)",
                      }}
                    >
                      <Shield size={14} />
                      <span>{u.role_id === 1 ? "Super Admin" : "Member"}</span>
                    </span>
                  </td>
                  <td>
                    <Badge status={u.status || "active"} />
                  </td>
                  <td style={{ textAlign: "right" }}>

                    <button
                      onClick={() => setEditingUser(u)}
                      className="btn btn-secondary"
                      style={{
                        padding: "6px 12px",
                        fontSize: "0.8rem",
                        gap: "6px",
                        borderRadius: "var(--radius-sm)",
                      }}
                    >
                      <Edit2 size={13} />
                      <span>Edit</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Add User Modal */}
      <AddUserModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onCreated={() => fetchUsers()}
      />

      {/* Edit User Modal */}
      <EditUserModal
        isOpen={Boolean(editingUser)}
        onClose={() => setEditingUser(null)}
        user={editingUser}
        onUpdated={() => fetchUsers()}
      />
    </div>
  );
}
